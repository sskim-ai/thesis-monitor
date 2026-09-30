from copy import deepcopy
from datetime import timedelta
import asyncio
import json
from types import SimpleNamespace

import httpx
import pytest
from scripts.websocket_timeout_runtime_review_first_a_closeout import validate_json_schema

from app.services.provider_native_valuation_acquisition import (
    routing_markets,
    collect_native,
    replay_native,
)
from app.services.provider_native_valuation_snapshot import derive_provider_snapshots
from app.services.provider_valuation_calibration_context import (
    calibration_context,
    with_axis_refs,
    validate_calibration_output,
    require_direction_isolation,
    ValuationCalibrationContext,
)
from app.services.sealed_source_transport import SealedSourceTransport
from app.services.sealed_fresh_dispatch import SealedDispatcher
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_policy import UnifiedSourcePolicy
from tests.test_r9_rev11_full_plan import compiled
from tests.test_r9_rev11_sealed_dispatch import CONFIG, ROOT
from tests.rev28_native_fixtures import security, native_input


def native_plan():
    _, old, _ = compiled()
    return compiled(
        config_identities={**old["config_identities"], "finnhub": CONFIG},
        valuation_market_types={
            t: "0" for t, s in old["identities"].items() if s["country"] == "KR"
        },
    )


def test_exact_roster_plan_and_readonly_endpoints():
    _, args, out = native_plan()
    slots = [d for d in out["plan"].descriptors if d.role_id.startswith("valuation:")]
    assert len(slots) == 5 + 8 + 28
    assert len(out["valuation_slots"]) == 22
    assert all(not d.mandatory and d.transient_retry_max == 0 for d in slots)
    assert all("alphavantage" not in d.provider for d in slots)
    assert {d.endpoint_operation for d in slots} == {"ka10099", "ka10001", "metric", "profile2"}
    assert out["plan"].admission(
        rev10_receipt=ROOT,
        owners=out["owners"],
        config_identities=args["config_identities"],
        credential_presence={p: True for p in args["config_identities"]},
    )["live_dispatch_allowed"]


def test_market_routing_uses_registry_or_exact_listing_not_ticker_guess():
    sec = security("005930")
    sec["exchange"] = "KRX"
    with pytest.raises(ValueError, match="routing_authority_missing"):
        routing_markets({"005930": sec}, listing_rows=[])
    rows = [dict(code="005930", marketCode="0")]
    assert routing_markets({"005930": sec}, listing_rows=rows) == {"005930": "0"}
    sec["exchange"] = "KOSDAQ"
    with pytest.raises(ValueError, match="routing_conflict"):
        routing_markets({"005930": sec}, listing_rows=rows)
    assert routing_markets({"005930": sec}, listing_rows=[]) == {"005930": "10"}


def test_native_sealed_dispatch_to_owner_replay(tmp_path):
    stock, args, out = native_plan()
    plan = out["plan"]
    requests = []
    identities = args["identities"]

    def responder(request):
        requests.append(request)
        api = request.headers.get("api-id")
        if request.url.path == "/oauth2/token":
            return httpx.Response(
                200,
                json=dict(
                    token="fictional-token",
                    token_type="Bearer",
                    expires_dt="20990101000000",
                    return_code=0,
                ),
            )
        if api == "ka10099":
            return httpx.Response(
                200,
                json=dict(
                    return_code=0,
                    list=[
                        dict(code=t, name=s["company_name"], marketCode="0", marketName="KOSPI")
                        for t, s in identities.items()
                        if s["country"] == "KR"
                    ],
                ),
            )
        if api == "ka10001":
            ticker = json.loads(request.content)["stk_cd"]
            return httpx.Response(
                200,
                json=dict(
                    return_code=0,
                    stk_cd=ticker,
                    stk_nm=identities[ticker]["company_name"],
                    per="18",
                    pbr="2",
                ),
            )
        ticker = request.url.params["symbol"]
        if request.url.path.endswith("/profile2"):
            return httpx.Response(
                200,
                json=dict(
                    ticker=ticker,
                    country="US",
                    currency="USD",
                    exchange=identities[ticker]["exchange"],
                ),
            )
        return httpx.Response(200, json=dict(symbol=ticker, metric=dict(peTTM=18, pbQuarterly=2)))

    run = SealedDispatcher(
        plan=plan,
        root=tmp_path / "dispatch",
        rev10_receipt=ROOT,
        owners=out["owners"],
        config_identities=args["config_identities"],
        credential_presence={p: True for p in args["config_identities"]},
        secrets=("fictional-key", "fictional-secret", "fictional-finnhub"),
    )
    sealed = SealedSourceTransport(
        run, httpx.MockTransport(responder), providers={d.provider for d in plan.descriptors}
    )
    frozen = dict(
        generation_id=stock.run_id,
        frozen_at=stock.frozen_at.isoformat(),
        plan=plan.model_dump(mode="json"),
        valuation_slots=out["valuation_slots"],
        valuation_official_identities={},
    )
    settings = SimpleNamespace(
        kiwoom_app_key="fictional-key",
        kiwoom_secret_key="fictional-secret",
        kiwoom_rest_base_url="https://api.kiwoom.com",
        kiwoom_rest_request_interval_seconds=0,
        finnhub_api_key="fictional-finnhub",
    )
    asyncio.run(collect_native(frozen=frozen, settings=settings, sealed=sealed))
    assert len(requests) == 1 + 1 + 8 + 28
    cutoff = max(v["finished_at"] for v in run.results.values())
    outcome = dict(completed_at=cutoff, logical_results=run.results)
    policy = UnifiedSourcePolicy(frozenset({"kiwoom_rest", "finnhub"}))
    for ticker, sec in identities.items():
        inputs = replay_native(
            root=tmp_path, frozen=frozen, outcome=outcome, security=sec, policy=policy
        )
        rows = derive_provider_snapshots(inputs, security=sec, run_id=stock.run_id)
        if sec["country"] == "KR":
            assert [r.value for r in rows] == [18, 2]
        else:
            assert all(r.value is None for r in rows)  # no authoritative SEC fixture granted
        assert inputs == replay_native(
            root=tmp_path, frozen=frozen, outcome=outcome, security=sec, policy=policy
        )
    changed = deepcopy(identities["005930"])
    changed["canonical_security_id"] = "wrong"
    with pytest.raises(ValueError, match="security_drift"):
        replay_native(
            root=tmp_path, frozen=frozen, outcome=outcome, security=changed, policy=policy
        )
    d = next(d for d in plan.descriptors if d.logical_request_id == "valuation:basic:005930")
    (tmp_path / "dispatch" / d.raw_path).write_bytes(b"{}")
    with pytest.raises(ValueError, match="hash_mismatch"):
        replay_native(
            root=tmp_path,
            frozen=frozen,
            outcome=outcome,
            security=identities["005930"],
            policy=policy,
        )


@pytest.fixture
def valuation(tmp_path):
    from tests.rev10_cohort_fixtures import plan_and_securities, POLICY_ALL, START, RUN
    from tests.rev8_source_fixtures import fresh_inputs
    from tests.rev10_source_fixtures import wire_clock
    from app.services.fresh_financial_stock_owner import assemble_fresh_stock

    plan, securities = plan_and_securities()
    with wire_clock(START + timedelta(seconds=4)):
        inputs = fresh_inputs(
            tmp_path, "IBM", plan=plan, cohort_securities=securities["us"], policy=POLICY_ALL
        )
    plain = assemble_fresh_stock(**inputs)
    inputs["valuation_inputs"] = native_input(
        inputs["financial_inputs"]["plan"]["security"], start=START, run=RUN, policy=POLICY_ALL
    )
    native = assemble_fresh_stock(**inputs)
    assert native["evidence_packet"] == plain["evidence_packet"]
    return native["valuation_view"], plain["valuation_view"]


def test_b_context_qualified_and_unavailable_triplets(valuation):
    current, unavailable = map(calibration_context, valuation)
    assert len(current["facts"]) == 2 and unavailable["facts"] == {}
    assert len(current["metric_states"]) == 3
    assert current == calibration_context(valuation[0])
    assert all(r["metric_asof"] is None for r in current["metric_states"])
    assert not current["overall_direction_use"]
    assert current["metric_states"][2]["value"] is None
    changed = deepcopy(current)
    changed["metric_states"][2]["value"] = 12
    changed["context_sha256"] = digest({k: v for k, v in changed.items() if k != "context_sha256"})
    with pytest.raises(ValueError, match="unavailable_value_leak"):
        ValuationCalibrationContext.model_validate(changed)


def test_context_schema_axis_refs_never_expand_direction(valuation):
    from scripts.m12ds_r2_schemas import obj, refs

    context = calibration_context(valuation[0])
    schema = obj(
        dict(
            overall=obj({"supporting_refs": refs(["business"])}),
            holder_axis={"anyOf": [obj({"holder_reason": {"type": "string"}})]},
            new_buyer_axis={"anyOf": [obj({"new_buyer_reason": {"type": "string"}})]},
        )
    )
    bound = with_axis_refs(schema, context)
    assert bound["properties"]["overall"] == schema["properties"]["overall"]
    ref = next(iter(context["facts"]))
    row = dict(
        overall=dict(supporting_refs=["business"]),
        holder_axis=dict(holder_reason="intact", holder_valuation_refs=[ref]),
        new_buyer_axis=dict(new_buyer_reason="context", new_buyer_valuation_refs=[ref]),
    )
    assert not validate_json_schema(row, bound)
    row["overall"]["supporting_refs"] = [ref]
    assert validate_json_schema(row, bound)


@pytest.mark.parametrize("stage", ["core", "pass-a"])
def test_direction_input_cannot_contain_native_refs_or_block(stage, valuation):
    context = calibration_context(valuation[0])
    for value in [
        dict(valuation_context=context),
        {"claims": [{"evidence_refs": list(context["facts"])}]},
    ]:
        with pytest.raises(ValueError, match="valuation_directional"):
            require_direction_isolation(value)


def test_b_output_requires_axis_owned_refs_and_disallows_overall(valuation):
    ctx = calibration_context(valuation[0])
    ref = next(iter(ctx["facts"]))
    row = dict(
        overall=dict(overall_reason="Observed business", supporting_refs=["business"]),
        holder_axis=dict(
            holder_reason="PER snapshot caution",
            holder_valuation_refs=[ref],
            holder_reason_evidence_refs=["business"],
        ),
        new_buyer_axis=dict(
            new_buyer_reason="PBR snapshot context",
            new_buyer_valuation_refs=[
                next(r["fact_ref"] for r in ctx["metric_states"] if r["metric"] == "PBR")
            ],
            new_buyer_risk_refs=[],
        ),
    )
    assert validate_calibration_output(row, ctx)["status"] == "PASS"
    for field in ["supporting_refs", "contradicting_refs", "confidence_caution_refs"]:
        bad = deepcopy(row)
        bad["overall"][field] = [ref]
        with pytest.raises(ValueError, match="directional_ref_leak"):
            validate_calibration_output(bad, ctx)
    bad = deepcopy(row)
    bad["overall"]["overall_reason"] = "PER implies BUY"
    with pytest.raises(ValueError, match="overall_reason_scope"):
        validate_calibration_output(bad, ctx)
    bad = deepcopy(row)
    bad["new_buyer_axis"]["new_buyer_valuation_refs"] = ["current-valuation:other:PER"]
    with pytest.raises(ValueError, match="axis_ref_not_owned"):
        validate_calibration_output(bad, ctx)


@pytest.mark.parametrize("index", [0, 1])
def test_real_controller_capture_checks_exact_b_context_and_direction_isolation(
    tmp_path, monkeypatch, valuation, index
):
    from scripts.r9_rev11_models import FreshExecution, CaptureOwner
    from scripts.m12ds_r2_schemas import decision_schema
    from app.services.unified_snapshot_contract import encoded

    sources = tmp_path / "sources"
    sources.mkdir()
    (sources / "r9-rev11-final-provider-plan.json").write_bytes(
        encoded(dict(generation_id="fixture", provider_native_valuation=True))
    )
    proof = FreshExecution(tmp_path / "models", sources)
    proof.fresh_stocks = {"IBM": {"valuation_view": valuation[index]}}
    proof.prepared = {"IBM": {"mode": "EVIDENCE_BASED"}}
    expected = proof.valuation_context("IBM")
    cap = {
        k: []
        for k in (
            "positive",
            "negative",
            "confidence",
            "quality",
            "condition",
            "holder_risk",
            "holder_reduce",
        )
    }
    cap.update(holder_support=["business"], risk_triggers={})
    original = decision_schema(cap, dict(fundamental_valid=False, compensating_discount=False), {})
    bound = with_axis_refs(original, expected)
    assert original["properties"]["overall"] == bound["properties"]["overall"]
    assert [
        b["properties"]["new_buyer"]["enum"] for b in bound["properties"]["new_buyer_axis"]["anyOf"]
    ] == [["WAIT"]]
    captured = []

    def capture(self, stage, spec, context, schema, prompt):
        captured.append((stage, context, schema))
        return {"captured": True}

    monkeypatch.setattr(CaptureOwner, "capture", capture)
    spec = dict(market="us", batch=1, subjects=["IBM"])
    ctx = {"IBM": {"valuation_context": expected}}
    assert proof.capture("pass-b", spec, ctx, bound, "fixture") == {"captured": True}
    receipt = json.loads((proof.sealed / "valuation-visibility/us-1.json").read_bytes())
    assert receipt["contexts"]["IBM"] == expected
    with pytest.raises(ValueError, match="visibility_drift"):
        proof.capture("pass-b", spec, {"IBM": {}}, bound, "fixture")
    for stage in ("core", "pass-a"):
        with pytest.raises(ValueError, match="directional_input_leak"):
            proof.capture(stage, spec, ctx, {}, "fixture")
    assert len(captured) == 1


def test_unavailable_fper_caution_needs_no_other_metric_ref(valuation):
    context = calibration_context(valuation[0])
    row = dict(
        overall=dict(overall_reason="Business evidence only"),
        holder_axis=dict(holder_reason="fPER unavailable", holder_valuation_refs=[]),
        new_buyer_axis=dict(new_buyer_reason="fPER unavailable", new_buyer_valuation_refs=[]),
    )
    assert validate_calibration_output(row, context)["status"] == "PASS"
    per_ref = next(r["fact_ref"] for r in context["metric_states"] if r["metric"] == "PER")
    pbr_ref = next(r["fact_ref"] for r in context["metric_states"] if r["metric"] == "PBR")
    row["new_buyer_axis"].update(
        new_buyer_reason="PER snapshot", new_buyer_valuation_refs=[pbr_ref]
    )
    with pytest.raises(ValueError, match="reason_requires_axis_ref"):
        validate_calibration_output(row, context)
    row["new_buyer_axis"]["new_buyer_valuation_refs"] = [per_ref]
    assert validate_calibration_output(row, context)["status"] == "PASS"
