from copy import deepcopy
import json

import pytest

from app.services.provider_native_valuation_snapshot import (
    derive_provider_snapshots,
    ProviderNativeValuationSnapshot,
)
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_run_artifacts import sha256_bytes
from tests.rev28_native_fixtures import native_input, security


def alter(part, fn):
    body = json.loads(part["raw"])
    fn(body)
    part["raw"] = encoded(body)
    part["receipt"]["source_sha256"] = sha256_bytes(part["raw"])


def derive(sec, inputs):
    return derive_provider_snapshots(inputs, security=sec, run_id="fictional-snapshot")


@pytest.mark.parametrize("ticker", ["IBM", "005930"])
def test_atomic_positive_without_denominator_reconstruction(ticker):
    sec = security(ticker)
    inputs = native_input(sec)
    rows = derive(sec, inputs)
    assert [r.value for r in rows] == [12.3, 1.5]
    for row in rows:
        assert row.state == "QUALIFIED_PROVIDER_LATEST_SNAPSHOT"
        assert row.metric_asof is row.underlying_denominator_period is None
        assert row.retrieval_timestamp.isoformat() == inputs["receipt"]["received_at"]
        assert (
            row.display_eligible
            and row.new_buyer_valuation_context_eligible
            and row.holder_valuation_context_eligible
        )
        assert not row.overall_direction_use and not row.same_session_recomputation
        assert "PROVIDER_METRIC_ASOF_NOT_EXPLICIT" in row.caveats
        assert ProviderNativeValuationSnapshot.model_validate(row.model_dump(mode="json")) == row
    if ticker.isdigit():
        assert "PROVIDER_UPDATE_CADENCE_WEEKLY_OR_EARNINGS_SEASON" in rows[0].caveats


def test_kr_exchange_native_market_name_and_same_code():
    sec = security('012450')
    inputs = native_input(sec)
    page = inputs['identity_inputs']['list_pages'][0]
    alter(page, lambda b: b['list'][0].update(marketName='거래소'))
    assert all(r.display_eligible for r in derive(sec, inputs))
    alter(page, lambda b: b['list'][0].update(marketCode='10'))
    assert all(not r.display_eligible for r in derive(sec, inputs))


@pytest.mark.parametrize("ticker", ["IBM", "005930"])
@pytest.mark.parametrize("value", [None, "", "  ", 0, "0", -1, True, "oops", "NaN", "Infinity"])
def test_sentinel_is_not_cheap_or_nm_and_other_metric_independent(ticker, value):
    sec = security(ticker)
    inputs = native_input(sec)
    alter(
        inputs,
        lambda b: (b if ticker.isdigit() else b["metric"]).update(
            {("per" if ticker.isdigit() else "peTTM"): value}
        ),
    )
    per, pbr = derive(sec, inputs)
    assert per.value is None and per.state.startswith("UNAVAILABLE_")
    assert pbr.display_eligible


@pytest.mark.parametrize(
    "case",
    ["wrong_code", "preferred", "wrong_market", "wrong_name", "missing", "duplicate", "old_list"],
)
def test_kr_identity_negatives(case):
    sec = security("005930")
    inputs = native_input(sec)
    page = inputs["identity_inputs"]["list_pages"][0]
    if case == "old_list":
        page["receipt"]["run_id"] = "old"
        with pytest.raises(ValueError, match="receipt_mismatch"):
            derive(sec, inputs)
        return
    if case in {"wrong_code", "preferred"}:
        alter(
            inputs if case == "wrong_code" else page,
            lambda b: (
                b.update(stk_cd="005935")
                if case == "wrong_code"
                else b["list"][0].update(code="005935")
            ),
        )
    elif case == "missing":
        alter(page, lambda b: b.update(list=[]))
    elif case == "duplicate":
        alter(page, lambda b: b["list"].append(deepcopy(b["list"][0])))
    else:
        alter(
            page,
            lambda b: b["list"][0].update(
                **({"marketCode": "10"} if case == "wrong_market" else {"name": "Different"})
            ),
        )
    assert all(r.state == "UNAVAILABLE_SECURITY_IDENTITY" for r in derive(sec, inputs))


@pytest.mark.parametrize(
    "case",
    [
        "ticker",
        "exchange",
        "currency",
        "metric_symbol",
        "official_hash",
        "official_exchange",
    ],
)
def test_us_identity_negatives(case):
    sec = security()
    inputs = native_input(sec)
    identity = inputs["identity_inputs"]
    if case in {"ticker", "exchange", "currency"}:
        alter(identity["profile"], lambda b: b.update({case: "OTHER"}))
    elif case == "metric_symbol":
        alter(inputs, lambda b: b.update(symbol="OTHER"))
    elif case == "official_hash":
        identity["official_identity_sha256"] = "0" * 64
    elif case == "official_exchange":
        identity["official_identity"]["evidence"]["exchange"] = "NASDAQ"
        identity["official_identity_sha256"] = digest(identity["official_identity"])
    assert all(r.state == "UNAVAILABLE_SECURITY_IDENTITY" for r in derive(sec, inputs))


@pytest.mark.parametrize("case", ["old_run", "old_time", "cache", "hash", "route", "identity_hash"])
def test_acquisition_fail_closed(case):
    sec = security()
    inputs = native_input(sec)
    if case == "old_time":
        inputs["receipt"]["received_at"] = "2025-01-01T00:00:00+00:00"
    elif case == "old_run":
        inputs["receipt"]["run_id"] = "old"
    elif case == "cache":
        inputs["receipt"]["cache_reused"] = True
    elif case == "hash":
        inputs["raw"] = b"{}"
    elif case == "identity_hash":
        inputs["receipt"]["security_sha256"] = "0" * 64
    else:
        inputs["receipt"]["request"]["route"] += "-wrong"
    with pytest.raises(ValueError, match="native_snapshot_source"):
        derive(sec, inputs)


@pytest.mark.parametrize(
    "field,value",
    [
        ("metricAsOf", "2000-01-01"),
        ("metricAsOf", "2099-01-01"),
        ("isStale", True),
        ("asOfDate", "broken"),
    ],
)
def test_conflicting_currentness_not_replaced_by_retrieval(field, value):
    sec = security()
    inputs = native_input(sec)
    alter(inputs, lambda b: b.update({field: value}))
    assert all(r.state == "UNAVAILABLE_CURRENTNESS" for r in derive(sec, inputs))


def test_adr_and_forward_do_not_inherit_permissions():
    sec = security("TSM")
    sec.update(security_type="ads", issuer_type="adr")
    inputs = native_input(sec)
    alter(inputs, lambda b: b.update(symbol="2330.TW"))
    alter(
        inputs["identity_inputs"]["profile"], lambda b: b.update(ticker="2330.TW", currency="TWD")
    )
    assert all(r.state == "UNAVAILABLE_ADR_CONVERSION" for r in derive(sec, inputs))
    assert all(r.metric in {"PER", "PBR"} for r in derive(sec, inputs))


@pytest.mark.parametrize(
    "field,value", [("value", 999), ("overall_direction_use", True), ("metric_asof", "2026-09-30")]
)
def test_receipt_forgery(field, value):
    sec = security()
    row = derive(sec, native_input(sec))[0].model_dump(mode="json")
    row[field] = value
    with pytest.raises(ValueError):
        ProviderNativeValuationSnapshot.model_validate(row)


def test_production_stock_owner_display_and_direction_separation(tmp_path):
    from tests.rev10_cohort_fixtures import plan_and_securities, POLICY_ALL, START, RUN
    from tests.rev8_source_fixtures import fresh_inputs
    from tests.rev10_source_fixtures import wire_clock
    from datetime import timedelta
    from app.services.fresh_financial_stock_owner import assemble_fresh_stock
    from app.services.current_fresh_valuation import (
        CurrentValuationView,
        valuation_numeric_bindings,
    )
    from app.services.detailed_stock_message_service import _valuation_rows

    plan, securities = plan_and_securities()
    with wire_clock(START + timedelta(seconds=4)):
        inputs = fresh_inputs(
            tmp_path, "IBM", plan=plan, cohort_securities=securities["us"], policy=POLICY_ALL
        )
    without = assemble_fresh_stock(**inputs)
    inputs["valuation_inputs"] = native_input(
        inputs["financial_inputs"]["plan"]["security"], start=START, run=RUN, policy=POLICY_ALL
    )
    with_snapshot = assemble_fresh_stock(**inputs)
    view = CurrentValuationView.model_validate(with_snapshot["valuation_view"])
    assert [m.status for m in view.metrics] == ["QUALIFIED", "QUALIFIED", "QUALIFIED"]
    assert view.security_basis_receipt.status == "UNAVAILABLE_SECURITY_BASIS"
    assert all(not m.entry_use_eligible for m in view.metrics)
    assert set(valuation_numeric_bindings(view)) == {"PER", "PBR", "FORWARD_PE"}
    assert [e for e in without["evidence_packet"]["evidence"]] == with_snapshot["evidence_packet"][
        "evidence"
    ]
    lines = [r.text for r in _valuation_rows(view)]
    assert "Finnhub TTM snapshot" in lines[0] and "Finnhub quarterly snapshot" in lines[1]
    assert "fPER(FY1)" in lines[2] and "FY1 제품 정책 기준" in lines[2]
    assert all(m.publication_date is None for m in view.metrics)
    forged = view.model_dump(mode="json")
    forged["security_id"] = "different"
    with pytest.raises(ValueError, match="binding_mismatch"):
        CurrentValuationView.model_validate(forged)
