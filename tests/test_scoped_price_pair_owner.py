"""Synthetic byte replay only; these tests never qualify a real source pair.

The pinned public specification is unchanged. project_state, the original current
owner, its wire parser, calendar and OHLC integrity owner all run normally.
No private native-owner archive, credentials, transport or production DB is used.
"""
from copy import deepcopy
from datetime import timedelta

import pytest

from app.services import scoped_price_pair_owner as pair
from app.services.scoped_source_plan import compile_scoped_source_plan
from app.services.sealed_fresh_dispatch import ProviderPlan
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_run_artifacts import sha256_bytes
from tests.completed_price_fixtures import official_spec
from tests.test_scoped_source_plan import arguments, fixture_catalog


@pytest.fixture
def captured(tmp_path):
    catalog, subject, _ = fixture_catalog(tmp_path, ticker="MU")
    settings = arguments(catalog, subject)
    scoped = compile_scoped_source_plan(**settings)
    security = catalog.record(scoped.identities[0], at=settings["at"])
    requirement = next(r for r in scoped.price_pairs if r.symbol == subject.ticker)
    provider = ProviderPlan(**scoped.request_plan.model_dump(), rev10_receipt_sha256="a" * 64)
    slot = next(d for d in provider.descriptors if d.logical_request_id == requirement.descriptor_id)
    documents = official_spec()
    blobs = {"documentation": documents}
    binding = dict(generation_id=provider.generation_id, logical_request_id=slot.logical_request_id,
        descriptor_sha256=slot.descriptor_sha256, request_sha256=slot.request_semantic_sha256,
        plan_sha256=provider.plan_sha256, role=slot.consumer_role,
        resolved_request_sha256=sha256_bytes(slot.request_json.encode()), parent_receipts={})
    start = provider.frozen_at + timedelta(seconds=1)
    attempt = dict(binding, attempt=1, started_at=start.isoformat(),
        finished_at=(start + timedelta(seconds=1)).isoformat(), status=200, artifact="response")
    final = dict(binding, status="PASS", attempts=[attempt])
    source = dict(provider_plan=provider.model_dump(mode="json"),
        documentation=dict(path="documentation", sha256=sha256_bytes(documents)))
    body = dict(return_code=0, result_list=[
        dict(dt=requirement.target.strftime("%Y%m%d"), open_pric="100", high_pric="110", low_pric="90", cur_prc="105"),
        dict(dt=requirement.prior.strftime("%Y%m%d"), open_pric="98", high_pric="105", low_pric="90", cur_prc="100"),
    ])
    args = dict(scoped_plan=scoped, role=requirement.role, source=source, security=security,
        artifact_reader=lambda path, sha: blobs[path], expected_scoped_plan_sha256=scoped.plan_sha256,
        expected_owner_hashes=pair.owner_hashes(), expected_source_sha256=None)
    case = dict(args=args, blobs=blobs, body=body, final=final, requirement=requirement)
    reseal(case)
    return case


def reseal(case):
    """Seal synthetic producer bytes, never a replacement for real receipts."""
    args, blobs, final = case["args"], case["blobs"], case["final"]
    blobs["response"] = encoded(case["body"])
    raw_sha = sha256_bytes(blobs["response"])
    final["attempts"][-1]["raw_sha256"] = raw_sha
    final["raw_sha256"] = raw_sha
    final["receipt_sha256"] = digest({k: v for k, v in final.items() if k != "receipt_sha256"})
    blobs["final"] = encoded(final)
    args["source"]["final"] = dict(path="final", sha256=sha256_bytes(blobs["final"]))
    args["expected_source_sha256"] = digest(args["source"])


def test_real_original_call_path_no_retiming_or_grants(captured, monkeypatch):
    args = captured["args"]
    before = deepcopy(args["source"])
    raw_before = deepcopy(captured["blobs"])
    calls = []
    original_state, original_close = pair.completed_price_state.project_state, pair.close.project

    def state_spy(**kwargs):
        calls.append("project_state")
        context = kwargs["plan"]
        assert context.contract == "scoped-price-replay-context-v1"
        assert context.frozen_at == args["scoped_plan"].request_plan.frozen_at
        assert context.reads == args["scoped_plan"].stock_reads
        assert not hasattr(context, "universe")
        return original_state(**kwargs)

    def close_spy(**kwargs):
        calls.append("original_current_owner")
        return original_close(**kwargs)

    monkeypatch.setattr(pair.completed_price_state, "project_state", state_spy)
    monkeypatch.setattr(pair.close, "project", close_spy)
    result = pair.reprove_price_pair(**args)
    assert calls == ["project_state", "original_current_owner"]
    assert result.status == "PAIR_REPROVED"
    assert [r.role for r in result.observations] == ["PRIOR", "CURRENT"]
    assert [r.close for r in result.observations] == [100, 105]
    assert len({r.raw_sha256 for r in result.observations}) == 1
    assert result.requirement.basis == "REGULAR_STOCK_CLOSE"
    assert result.current_state.numeric_owner.adjustment_basis == "regular_close"
    assert result.current_state.numeric_owner.technical_compatibility["status"] == "UNPROVEN"
    assert result.source_use_grant == "NOT_ISSUED" and result.native_source_use == "NOT_ADMITTED"
    assert not result.current_identity_authority and not result.technical_injection_allowed
    assert not result.requirement.available
    assert args["source"] == before and captured["blobs"] == raw_before
    assert pair.validate_price_pair(result.model_dump(mode="json"), **args) == result


@pytest.mark.parametrize("mutation,reason", [
    ("missing", "EXACT_PRIOR_ROW_MISSING"),
    ("nonadjacent", "EXACT_PRIOR_ROW_MISSING"),
    ("duplicate", "DUPLICATE_PRIOR_ROW"),
    ("conflict", "DUPLICATE_PRIOR_ROW"),
    ("field_missing", "PRIOR_ROW_FIELDS_MISSING"),
    ("numeric_negative", "PRIOR_PRICE_WIRE_INVALID"),
    ("nan", "PRIOR_PRICE_WIRE_INVALID"),
    ("infinity", "PRIOR_PRICE_WIRE_INVALID"),
    ("zero", "PRIOR_PRICE_WIRE_INVALID"),
    ("invalid_ohlc", "PRIOR_OHLC_INTEGRITY_FAILED"),
])
def test_prior_failures_never_fabricate_pair(captured, mutation, reason):
    rows = captured["body"]["result_list"]
    prior = rows[1]
    if mutation == "missing":
        rows.pop()
    elif mutation == "nonadjacent":
        prior["dt"] = (captured["requirement"].prior - timedelta(days=1)).strftime("%Y%m%d")
    elif mutation in {"duplicate", "conflict"}:
        rows.append(dict(prior, cur_prc="101" if mutation == "conflict" else prior["cur_prc"]))
    elif mutation == "field_missing":
        prior.pop("open_pric")
    else:
        prior["cur_prc"] = {"numeric_negative": -100, "nan": "NaN", "infinity": "Infinity",
                            "zero": "0", "invalid_ohlc": "999"}[mutation]
    reseal(captured)
    result = pair.reprove_price_pair(**captured["args"])
    assert result.status == "OWNER_UNQUALIFIED" and result.reason_code == reason
    assert result.current_state.state == "AVAILABLE" and not result.observations


def test_original_sign_parser_is_used_for_prior(captured, monkeypatch):
    captured["body"]["result_list"][1]["cur_prc"] = "-100"
    reseal(captured)
    original, seen = pair.close._wire_price, []

    def spy(value):
        seen.append(value)
        return original(value)

    monkeypatch.setattr(pair.close, "_wire_price", spy)
    result = pair.reprove_price_pair(**captured["args"])
    assert result.status == "PAIR_REPROVED" and result.observations[0].close == 100
    assert "-100" in seen and len(seen) == 8


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "integrity", "shape"])
def test_current_owner_denial_remains_denial(captured, mutation):
    rows = captured["body"]["result_list"]
    if mutation == "missing":
        rows.pop(0)
    elif mutation == "duplicate":
        rows.append(dict(rows[0]))
    elif mutation == "shape":
        rows.append(None)
    else:
        rows[0]["cur_prc"] = "999"
    reseal(captured)
    result = pair.reprove_price_pair(**captured["args"])
    assert result.status == "OWNER_UNQUALIFIED"
    assert result.current_state.state.startswith("DENIED_") and not result.observations


@pytest.mark.parametrize("mutation", ["http", "provider", "format"])
def test_failed_source_is_not_numeric_evidence(captured, mutation):
    if mutation == "http":
        captured["final"]["status"] = "FAILED"
        captured["final"]["attempts"][0]["status"] = 503
    elif mutation == "provider":
        captured["body"]["return_code"] = 1
    else:
        captured["body"] = []
    reseal(captured)
    result = pair.reprove_price_pair(**captured["args"])
    assert result.status == "SOURCE_UNAVAILABLE" and not result.observations


def test_absent_capture_is_explicit(captured):
    args = dict(captured["args"], source=None, expected_source_sha256=None)
    result = pair.reprove_price_pair(**args)
    assert result.reason_code == "CAPTURED_SOURCE_INPUT_MISSING"
    assert result.current_state is None and not result.observations


@pytest.mark.parametrize("kind", ["INDEX", "ETF_PROXY", "KR_STOCK"])
def test_unsupported_adapters_do_not_read_source(captured, tmp_path, kind):
    args = dict(captured["args"], source=None, expected_source_sha256=None)
    plan = args["scoped_plan"]
    if kind == "KR_STOCK":
        catalog, subject, _ = fixture_catalog(tmp_path, ticker="005930", market="kr")
        plan = compile_scoped_source_plan(**arguments(catalog, subject))
        req = next(r for r in plan.price_pairs if r.symbol == "005930")
    else:
        req = next(r for r in plan.price_pairs if r.instrument_kind == kind)

    def forbidden(*unused):
        raise AssertionError("unsupported adapter read source")

    result = pair.reprove_price_pair(**dict(args, scoped_plan=plan, role=req.role,
        expected_scoped_plan_sha256=plan.plan_sha256, artifact_reader=forbidden))
    assert result.status == "UNSUPPORTED_ADAPTER" and result.current_state is None
    assert not result.observations and result.source_use_grant == "NOT_ISSUED"


@pytest.mark.parametrize("anchor", ["expected_scoped_plan_sha256", "expected_source_sha256"])
def test_independent_input_anchor_required(captured, anchor):
    with pytest.raises(ValueError, match="anchor_mismatch"):
        pair.reprove_price_pair(**dict(captured["args"], **{anchor: "0" * 64}))


@pytest.mark.parametrize("name", ["app/services/completed_price_state.py",
    "app/services/ohlcv_provider_integrity_service.py", "app/services/scoped_price_pair_owner.py"])
def test_owner_only_drift_rejected(captured, name):
    owners = dict(captured["args"]["expected_owner_hashes"], **{name: "0" * 64})
    with pytest.raises(ValueError, match="owner_drift"):
        pair.reprove_price_pair(**dict(captured["args"], expected_owner_hashes=owners))


def test_raw_hash_drift_rejected(captured):
    captured["blobs"]["response"] += b" "
    with pytest.raises(ValueError, match="artifact_drift"):
        pair.reprove_price_pair(**captured["args"])


@pytest.mark.parametrize("field,value", [("ticker", "OTHER"), ("canonical_security_id", "other"),
    ("exchange", "NYSE"), ("cik", "0000009999"), ("security_type", "ETF")])
def test_security_not_caller_relabelled(captured, field, value):
    security = dict(captured["args"]["security"], **{field: value})
    with pytest.raises(ValueError, match="security_record_mismatch"):
        pair.reprove_price_pair(**dict(captured["args"], security=security))


@pytest.mark.parametrize("field,value", [("cik", "0000009999"), ("cik", None),
    ("security_type", "ETF"), ("security_type", "ADS"), ("security_type", "preferred_stock"),
    ("security_type", None), ("issuer_type", "foreign_private_issuer"),
    ("canonical_company_id", "another-company")])
def test_security_fields_must_match_binding_even_with_new_record_hash(captured, field, value):
    args = captured["args"]
    security = dict(args["security"], **{field: value})
    data = args["scoped_plan"].model_dump(mode="json")
    data["identities"][0]["record_sha256"] = digest(security)
    plan = pair.R22ScopedSourcePlanV1.model_validate(data)
    with pytest.raises(ValueError, match="security_record_mismatch"):
        pair.reprove_price_pair(**dict(args, security=security, scoped_plan=plan,
            expected_scoped_plan_sha256=plan.plan_sha256))


@pytest.mark.parametrize("currency", ["KRW", "EUR", None, ""])
def test_wrong_explicit_currency_rejected(captured, currency):
    security = dict(captured["args"]["security"], currency=currency)
    with pytest.raises(ValueError, match="security_currency_mismatch"):
        pair.reprove_price_pair(**dict(captured["args"], security=security))


@pytest.mark.parametrize("explicit", [False, True])
def test_catalog_currency_may_be_absent_or_correctly_explicit(captured, explicit):
    security = dict(captured["args"]["security"])
    assert "currency" not in security
    if explicit:
        security["currency"] = "USD"
    result = pair.reprove_price_pair(**dict(captured["args"], security=security))
    assert result.status == "PAIR_REPROVED" and result.requirement.currency == "USD"
    assert result.source_use_grant == "NOT_ISSUED"


def test_positive_replay_uses_unchanged_public_spec_pin(captured):
    expected = "42a7b3912c9d9588c83bdc2db7779c8d2e038703a2b5562e54ef46ae905cba79"
    assert pair.close.OFFICIAL_SPEC_SHA256 == expected
    assert sha256_bytes(captured["blobs"]["documentation"]) == expected
    result = pair.reprove_price_pair(**captured["args"])
    assert result.status == "PAIR_REPROVED"
    assert result.current_state.numeric_owner.documentation_sha256 == expected


def test_provider_plan_scope_cannot_be_truncated(captured):
    args = captured["args"]
    args["source"]["provider_plan"]["descriptors"] = [
        d for d in args["source"]["provider_plan"]["descriptors"] if d["endpoint_operation"] == "usa20590"]
    args["expected_source_sha256"] = digest(args["source"])
    with pytest.raises(ValueError, match="provider_plan_mismatch"):
        pair.reprove_price_pair(**args)


def test_final_generation_mismatch_rejected_even_when_rehashed(captured):
    captured["final"]["generation_id"] = "another-generation"
    reseal(captured)
    with pytest.raises(ValueError, match="attempt_contract_gap"):
        pair.reprove_price_pair(**captured["args"])


def test_request_clock_is_not_retimed_for_prior(captured):
    attempt = captured["final"]["attempts"][0]
    shifted = captured["args"]["scoped_plan"].request_plan.frozen_at + timedelta(days=3)
    attempt.update(started_at=shifted.isoformat(), finished_at=(shifted + timedelta(seconds=1)).isoformat())
    reseal(captured)
    result = pair.reprove_price_pair(**captured["args"])
    assert result.status == "OWNER_UNQUALIFIED"
    assert result.current_state.state == "DENIED_SECURITY_OR_SESSION_BINDING"
    assert not result.observations


def test_separately_captured_prior_is_not_considered(captured):
    captured["body"]["result_list"].pop()
    captured["blobs"]["unreferenced-prior"] = encoded(dict(cur_prc="100", dt="20261015"))
    reseal(captured)
    result = pair.reprove_price_pair(**captured["args"])
    assert result.reason_code == "EXACT_PRIOR_ROW_MISSING"


def test_receipt_rehash_is_not_replay_authority(captured):
    receipt = pair.reprove_price_pair(**captured["args"]).model_dump(mode="json")
    receipt["observations"][0]["close"] = 101.0
    receipt["receipt_sha256"] = digest({k: v for k, v in receipt.items() if k != "receipt_sha256"})
    with pytest.raises(ValueError, match="replay_mismatch"):
        pair.validate_price_pair(receipt, **captured["args"])


@pytest.mark.parametrize("field,value", [("source_use_grant", "ALLOWED"),
    ("current_identity_authority", True), ("native_source_use", "ADMITTED"),
    ("technical_injection_allowed", True)])
def test_no_self_minted_permission(captured, field, value):
    receipt = pair.reprove_price_pair(**captured["args"]).model_dump(mode="json")
    receipt[field] = value
    receipt["receipt_sha256"] = digest({k: v for k, v in receipt.items() if k != "receipt_sha256"})
    with pytest.raises(ValueError):
        pair.validate_price_pair(receipt, **captured["args"])


def test_bounded_cached_reader(captured, monkeypatch):
    calls = []
    def reader(path, sha):
        calls.append(path)
        return captured["blobs"][path]
    result = pair.reprove_price_pair(**dict(captured["args"], artifact_reader=reader))
    assert result.status == "PAIR_REPROVED" and len(calls) == len(set(calls)) == 3
    monkeypatch.setattr(pair, "MAX_REPLAY_BYTES", 1)
    with pytest.raises(ValueError, match="replay_byte_bound"):
        pair.reprove_price_pair(**captured["args"])


def test_boundary_exception_is_not_converted_to_source_denial(captured):
    def forbidden(*unused):
        raise PermissionError("synthetic boundary stop")
    with pytest.raises(PermissionError):
        pair.reprove_price_pair(**dict(captured["args"], artifact_reader=forbidden))
