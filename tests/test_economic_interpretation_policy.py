"""Source/property rules, never ticker conclusions or real corporate receipts."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.services.economic_interpretation_policy import (
    BackendComparisonInputs, BackendReportedComparison, ComparisonInput,
    ReportedComparisonInput, ReportedStatementInput, governing_abstention_policy,
    qualify_cash_flow_comparison, qualify_reported_comparison, reject_unauthorized_abstention,
)
from app.services.unified_snapshot_contract import digest
from scripts import directional_financial_context_m12 as m12
from app.services.sec_financial_snapshot_service import _companyfacts_snapshots
from tests.test_external_api_accuracy import _companyfact_entry, _companyfacts_payload


def cash(identity="UNSEEN_US_POLICY", value="180", metric="operating_cash_flow"):
    prior, current = m12._financial_pair(
        identity, metric, metric, current_value=value, prior_value="110",
        period_type=m12.FinancialPeriodType.YTD,
        current_start="2026-01-01", current_end="2026-06-30",
        prior_start="2025-01-01", prior_end="2025-06-30",
        comparison_kind=m12.FinancialComparisonKind.PRIOR_YEAR_COMPARABLE,
    )
    prior = prior.model_copy(update={"value": Decimal("110")})
    current = current.model_copy(update={"value": Decimal(value)})
    value = ComparisonInput(security_id=identity, generation_id="fixture-run",
        source_generation_id="fixture-source", owner_ref="SYNTHETIC_STATEMENT_OWNER",
        source_artifact_sha256=("a" * 64,), facts=(prior, current))
    return value, current.ref_id


def qualify(value, selected_ref, **changes):
    owned = BackendComparisonInputs(value, expected_input_sha256=digest(value.model_dump(mode="json")))
    args = dict(inputs=owned, current_ref=selected_ref, security_id=value.security_id,
                generation_id=value.generation_id, source_generation_id=value.source_generation_id)
    args.update(changes)
    return qualify_cash_flow_comparison(**args)


@pytest.mark.parametrize("identity", ["UNSEEN_US_POLICY", "UNSEEN_KR_POLICY", "UNSEEN_ADS_POLICY"])
@pytest.mark.parametrize("amount,direction", [("180", ("STRENGTHENED",)), ("90", ("WEAKENED",)), ("110", ())])
def test_same_rule_with_financial_permutation(identity, amount, direction):
    result = qualify(*cash(identity, amount))
    assert result.comparison_qualified
    assert result.observed_direction == direction
    assert result.permitted_core_roles == ()
    assert result.permitted_native_direction_axes == ()
    assert result.core_role_state == "POLICY_RULE_NOT_AUTHORIZED"
    assert not result.accepted_economic_candidate


def test_revenue_is_not_cash_flow_polarity_and_missing_model_is_not_global():
    result = qualify(*cash(metric="revenue"))
    assert result.reason == "METRIC_POLARITY_CONTEXT_DEPENDENT"
    assert not result.comparison_qualified
    assert qualify(*cash()).comparison_qualified


@pytest.mark.parametrize("field", ["security_id", "generation_id", "source_generation_id", "current_ref"])
def test_wrong_identity_generation_or_membership(field):
    with pytest.raises(ValueError, match="MISMATCH"):
        qualify(*cash(), **{field: "wrong"})


def test_independent_input_anchor_and_backend_capability_required():
    value, ref = cash()
    with pytest.raises(ValueError, match="ANCHOR_REQUIRED"):
        BackendComparisonInputs(value, expected_input_sha256="b" * 64)
    with pytest.raises(ValueError, match="BACKEND_OWNED"):
        qualify_cash_flow_comparison(inputs=value.model_dump(), current_ref=ref,
            security_id=value.security_id, generation_id=value.generation_id,
            source_generation_id=value.source_generation_id)


def test_prose_cannot_substitute_for_structured_value():
    value, _ = cash()
    prior, current = value.facts
    changed = current.model_copy(update={"value": None, "statement": '{"value":180}'})
    value = value.model_copy(update={"facts": (prior, changed)})
    with pytest.raises(ValueError, match="NO_PROSE_FALLBACK"):
        BackendComparisonInputs(value, expected_input_sha256=digest(value.model_dump(mode="json")))


def test_noncomparable_period_or_quality_has_no_hint():
    value, ref = cash()
    prior, current = value.facts
    context = prior.financial_context.model_copy(update={"currency": "KRW"})
    unsafe = value.model_copy(update={"facts": (prior.model_copy(update={"financial_context": context}), current)})
    result = qualify(unsafe, ref)
    assert not result.comparison_qualified
    assert result.observed_direction == ()


def reported(identity):
    current = dict(_companyfact_entry(30, fp="Q2", start="2026-04-01", end="2026-06-30", filed="2026-08-01"),
                   accn="0000001234-26-000001")
    prior = dict(current, start="2025-04-01", end="2025-06-30", val=-20)
    payload = _companyfacts_payload("us-gaap", {
        "Revenues": [dict(r, val=100) for r in (current, prior)],
        "RevenueFromContractWithCustomerExcludingAssessedTax": [dict(r, val=10) for r in (current, prior)],
        "OperatingIncomeLoss": [current, prior],
    })
    payload["cik"] = 1234
    prior, current = sorted(_companyfacts_snapshots(payload, identity), key=lambda r: r.financial_period_end)
    rows = [ReportedStatementInput(**{field: getattr(row, field) for field in ReportedStatementInput.model_fields})
            for row in (current, prior)]
    capsule = ReportedComparisonInput(security_id=identity, ticker=identity,
        generation_id="fixture-run", source_generation_id="fixture-source",
        owner_ref="SYNTHETIC_SEC_COMPARISON_OWNER", source_artifact_sha256=("a" * 64,),
        cutoff=date(2026, 9, 22), formal=rows[0], comparison=rows[1])
    return capsule


def evaluate_reported(capsule, **changes):
    owned = BackendReportedComparison(capsule, expected_input_sha256=digest(capsule.model_dump(mode="json")))
    args = dict(inputs=owned, security_id=capsule.security_id, generation_id=capsule.generation_id,
                source_generation_id=capsule.source_generation_id)
    args.update(changes)
    return qualify_reported_comparison(**args)


@pytest.mark.parametrize("identity", ["UNSEEN_US_REPORTED", "UNSEEN_KR_REPORTED", "UNSEEN_ADS_REPORTED"])
def test_field_qualification_is_local_not_revenue_to_profit_upgrade(identity):
    receipt, results = evaluate_reported(reported(identity))
    assert receipt["status"] == "PASS"
    assert len(results) == 1
    assert receipt["comparative_observations"][0]["metric"] == "operating_income"
    assert results[0].observed_direction == ("higher",)
    assert results[0].permitted_core_roles == ()
    assert receipt["fields"]["current.revenue"]["state"] == "denied"


@pytest.mark.parametrize("field", ["security_id", "generation_id", "source_generation_id"])
def test_reported_request_binding(field):
    with pytest.raises(ValueError, match="MISMATCH"):
        evaluate_reported(reported("UNSEEN_REPORTED"), **{field: "another"})


def test_source_mutation_and_unknown_field_rejected():
    capsule = reported("UNSEEN_REPORTED")
    altered = capsule.model_copy(update={"formal": capsule.formal.model_copy(update={"operating_income": 777.0})})
    with pytest.raises(ValueError, match="ANCHOR_REQUIRED"):
        BackendReportedComparison(altered, expected_input_sha256=digest(capsule.model_dump(mode="json")))
    receipt, results = evaluate_reported(altered)
    assert receipt["status"] == "FAIL"
    assert results == ()
    raw = capsule.model_dump(mode="json")
    raw["desired_Core_conclusion"] = "BUY"
    with pytest.raises(ValidationError):
        ReportedComparisonInput.model_validate(raw)


def test_abstention_has_definite_policy_gap_not_hold_or_wait():
    result = governing_abstention_policy()
    assert result.status == "POLICY_AUTHORITY_GAP"
    assert not result.accepted_abstention
    assert result.permitted_substitutions == ()
    for value in ("HOLD", "WAIT", "ABSTAIN", {"outcome_type": "ABSTAIN", "optional_history_missing": True}):
        with pytest.raises(ValueError, match="POLICY_AUTHORITY_GAP"):
            reject_unauthorized_abstention(value)


def test_prior_only_comparison_ref_cannot_omit_current_support():
    value, ref = cash()
    prior, current = value.facts
    comparison = current.financial_context.comparison.model_copy(update={"input_source_refs": (prior.source_ref,)})
    context = current.financial_context.model_copy(update={"comparison": comparison})
    value = value.model_copy(update={"facts": (prior, current.model_copy(update={"financial_context": context}))})
    result = qualify(value, ref)
    assert result.comparison_qualified
    assert set(result.required_supporting_refs) == {current.source_ref, prior.source_ref}
