"""Offline-only synthetic forwardPE contract tests; no provider transport."""

from copy import deepcopy
import json

import pytest

from app.services import provider_native_valuation_snapshot as native
from app.services.current_fresh_valuation import CurrentMultiple
from app.services.provider_valuation_calibration_context import (
    ValuationCalibrationContext,
    calibration_context,
    validate_calibration_output,
)
from app.services.unified_snapshot_contract import digest
from tests.rev28_native_fixtures import native_input, security
from tests.test_r9_rev28_native_snapshot import alter as alter_in_place
from tests import test_r9_rev29_valuation_integration as rev29


@pytest.fixture
def valuation(tmp_path):
    return rev29.valuation.__wrapped__(tmp_path)


def derive(inputs=None, sec=None):
    sec = sec or security()
    return native.derive_forward_snapshot(
        inputs or native_input(sec), security=sec, run_id="fictional-snapshot"
    )


def alter(inputs, fn):
    result = deepcopy(inputs)
    alter_in_place(result, fn)
    return result


def rehash(row, field):
    return {**row, field: digest({k: v for k, v in row.items() if k != field})}


def test_atomic_forward_and_old_owners_unchanged():
    sec = security()
    inputs = native_input(sec)
    old = [
        r.model_dump(mode="json")
        for r in native.derive_provider_snapshots(inputs, security=sec, run_id="fictional-snapshot")
    ]
    snapshot = derive(inputs)
    assert snapshot.value == 7
    assert snapshot.state == native.FORWARD_QUALIFIED
    assert snapshot.forward_horizon_state == "PROVIDER_FORWARD_HORIZON_UNSPECIFIED"
    assert snapshot.provider_horizon is snapshot.estimate_basis is None
    assert snapshot.display_label == "Finnhub Forward P/E"
    assert not snapshot.overall_direction_use
    assert not snapshot.core_visibility and not snapshot.pass_a_visibility
    assert snapshot.underlying_denominator_period is None
    assert snapshot.metric_asof is None
    assert "EPS" not in type(snapshot).model_fields
    assert [
        r.model_dump(mode="json")
        for r in native.derive_provider_snapshots(inputs, security=sec, run_id="fictional-snapshot")
    ] == old
    # forwardPE is independently owned even if trailing EPS/PER are not usable.
    altered = alter(inputs, lambda b: b["metric"].update(peTTM=-1, epsTTM=-999999))
    assert derive(altered).value == 7


@pytest.mark.parametrize("value", [None, "", "  "])
def test_missing_forward_is_typed(value):
    row = derive(alter(native_input(security()), lambda b: b["metric"].update(forwardPE=value)))
    assert row.state == "UNAVAILABLE_FORWARD_PE" and row.value is None
    assert not row.display_eligible


@pytest.mark.parametrize("value", [0, -3, "NaN", "Infinity", "bad", True, "1e9999"])
def test_invalid_forward_is_not_positive_authority(value):
    row = derive(alter(native_input(security()), lambda b: b["metric"].update(forwardPE=value)))
    assert row.state == "INVALID_FORWARD_PE" and row.value is None


def test_no_alternate_field_or_implied_eps_fallback():
    inputs = alter(native_input(security()), lambda b: b["metric"].pop("forwardPE"))
    body = json.loads(inputs["raw"])
    assert body["metric"]["peTTM"] > 0
    assert derive(inputs).state == "UNAVAILABLE_FORWARD_PE"
    with pytest.raises(ValueError, match="forward_pe_requires_atomic_provider_owner"):
        CurrentMultiple(
            metric="FORWARD_PE",
            status="UNAVAILABLE",
            denial_reason="missing",
            numerator=10,
            source_method="fictional",
            input_hashes=("a" * 64,),
        )


@pytest.mark.parametrize("home", [False, True])
def test_adr_never_transfers_home_ratio(home):
    sec = security()
    sec.update(issuer_type="adr", security_type="ads")
    inputs = native_input(sec)
    if home:
        inputs = alter(inputs, lambda b: b.update(symbol="HOME.TW"))
    row = derive(inputs, sec)
    assert row.state == (
        "UNAVAILABLE_ADR_FORWARD_VALUATION_CONVERSION"
        if home
        else "UNAVAILABLE_ADR_FORWARD_VALUATION_IDENTITY"
    )
    assert row.value is None and not row.display_eligible


@pytest.mark.parametrize(
    "field,value", [("symbol", "WRONG"), ("currency", "TWD"), ("shareClass", "wrong")]
)
def test_security_metadata_mismatch(field, value):
    row = derive(alter(native_input(security()), lambda b: b.update({field: value})))
    assert row.state == "IDENTITY_MISMATCH" and row.value is None


def test_stale_and_receipt_tamper_fail_closed():
    inputs = native_input(security())
    assert (
        derive(alter(inputs, lambda b: b.update(isStale=True))).state == "SOURCE_RESPONSE_INVALID"
    )
    bad = deepcopy(inputs)
    bad["raw"] += b" "
    with pytest.raises(ValueError, match="receipt_mismatch"):
        derive(bad)
    bad = deepcopy(inputs)
    bad["receipt"]["received_at"] = "2099-01-01T00:00:00+00:00"
    with pytest.raises(ValueError, match="time_mismatch"):
        derive(bad)


def test_caller_cannot_promote_user_assertion_to_fy1():
    row = derive().model_dump(mode="json")
    row.update(
        forward_horizon_state="PROVIDER_FORWARD_HORIZON_FY1",
        provider_horizon="NEXT_FISCAL_YEAR",
        estimate_basis="ANALYST_ESTIMATES",
        state=native.FORWARD_FY1_QUALIFIED,
        provider_definition={"source": "user assertion"},
    )
    with pytest.raises(ValueError, match="official_definition_required"):
        native.ProviderNativeForwardValuationSnapshot.model_validate(rehash(row, "snapshot_sha256"))


def test_fy1_mapping_only_under_pinned_definition_synthetic(monkeypatch, tmp_path):
    # This fixture is not live official documentation evidence.
    proof = dict(
        source_url="https://finnhub.io/fictional-test-definition",
        sha256="a" * 64,
        field="metric.forwardPE",
        definition="synthetic FY1 analyst-estimate definition",
    )
    monkeypatch.setattr(native, "FINNHUB_FORWARD_FY1_PROVENANCE", proof)
    row = derive()
    assert row.state == native.FORWARD_FY1_QUALIFIED
    assert row.forward_horizon_state == "PROVIDER_FORWARD_HORIZON_FY1"
    assert row.provider_horizon == "NEXT_FISCAL_YEAR"
    assert row.estimate_basis == "ANALYST_ESTIMATES"
    assert row.provider_definition == proof and row.display_label == "fPER(FY1)"
    assert row.underlying_denominator_period is None
    assert not row.overall_direction_use and not row.same_session_recomputation
    from app.services.current_fresh_valuation import CurrentValuationView
    from app.services.detailed_stock_message_service import _valuation_rows

    view = CurrentValuationView.model_validate(rev29.valuation.__wrapped__(tmp_path)[0])
    assert 'fPER(FY1)' in _valuation_rows(view)[2].text
    context = calibration_context(view)
    assert context['metric_states'][2]['state'] == native.FORWARD_FY1_QUALIFIED
    assert context['metric_states'][2]['provider_definition'] == proof


def test_binding_renderer_and_axis_ownership(valuation):
    from app.services.current_fresh_valuation import (
        CurrentValuationView,
        valuation_numeric_bindings,
    )
    from app.services.detailed_stock_message_service import _valuation_rows

    view = CurrentValuationView.model_validate(valuation[0])
    bound = valuation_numeric_bindings(view)["FORWARD_PE"]
    assert bound["fact"]["fields"] == {"forward_pe": 7}
    assert bound["fact"]["provider_snapshot"]["provider_field"] == "forwardPE"
    line = _valuation_rows(view)[2].text
    assert "Finnhub Forward P/E" in line and "7" in line and "fPER(FY1)" not in line
    context = calibration_context(view)
    ref = context["metric_states"][2]["fact_ref"]
    output = dict(
        overall=dict(overall_reason="business evidence"),
        holder_axis=dict(holder_reason="Forward P/E snapshot context", holder_valuation_refs=[ref]),
        new_buyer_axis=dict(
            new_buyer_reason="Forward P/E snapshot context", new_buyer_valuation_refs=[ref]
        ),
    )
    assert validate_calibration_output(output, context)["status"] == "PASS"
    output["holder_axis"]["holder_valuation_refs"] = []
    with pytest.raises(ValueError, match="requires_axis_ref"):
        validate_calibration_output(output, context)
    output["overall"]["overall_reason"] = "Forward P/E implies business improvement"
    with pytest.raises(ValueError, match="overall_reason_scope"):
        validate_calibration_output(output, context)


@pytest.mark.parametrize(
    "field,value",
    [
        ("display_label", "fPER(FY1)"),
        ("provider_horizon", "NEXT_FISCAL_YEAR"),
        ("estimate_basis", "ANALYST_ESTIMATES"),
    ],
)
def test_context_metadata_forgery_rejected(valuation, field, value):
    context = calibration_context(valuation[0])
    context["metric_states"][2][field] = value
    with pytest.raises(ValueError, match="horizon_label_unowned"):
        ValuationCalibrationContext.model_validate(rehash(context, "context_sha256"))


def test_context_qualification_state_must_match_atomic_owner(valuation):
    context = calibration_context(valuation[0])
    context['metric_states'][2]['state'] = native.FORWARD_FY1_QUALIFIED
    with pytest.raises(ValueError, match='forward_owner_binding'):
        ValuationCalibrationContext.model_validate(rehash(context, 'context_sha256'))
