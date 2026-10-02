from copy import deepcopy

import pytest

from app.services.cross_market_decision_engine_service import _compact
from scripts import financial_direction_eligibility as g
from scripts import m12ds_r3_policy as p
from scripts import r2b_r2_contract as c


def fixture(*, metric="operating_income", value=20, prior=None):
    ref = "canonical:earnings:fictional"
    fields = {metric: {"value": value}}
    if prior is not None:
        basis = dict(period_type="QTD", currency="USD", unit="currency", entity_scope="issuer", statement_basis="CFS")
        fields = dict(metric=metric, current_value=value, prior_comparable_value=prior,
                      comparison_type="YOY", current_period=dict(start="2026-04-01", end="2026-06-30", **basis),
                      prior_period=dict(start="2025-04-01", end="2025-06-30", **basis))
    row = dict(ref_id=ref, category="earnings", source_ref="stock.fact_catalog.earnings:fictional",
               statement=_compact(fields), as_of="2026-06-30")
    record = dict(ref_id=ref, fact_kind="earnings", authority_state="RESOLVED",
                  allowed_uses=["CONTEXT", "BUSINESS_CONTEXT", "OVERALL_DIRECTION", "HOLDER_STANCE", "ENTRY"],
                  prohibited_uses=[], denial_reasons=[])
    bound = {ref: dict(fields=fields, fact_sha256=p.canonical_sha256(fields))}
    return row, record, bound


@pytest.mark.parametrize("metric", ["revenue", "operating_income", "net_income", "operating_cash_flow"])
@pytest.mark.parametrize("value", [20, 0, -20])
def test_absolute_amount_is_context_not_direction(metric, value):
    row, record, fields = fixture(metric=metric, value=value)
    original = deepcopy((row, record, fields))
    after = g.narrow_financial_authority(record, row, fields[row["ref_id"]])
    assert not set(after["allowed_uses"]) & g.DIRECTION_USES
    assert g.DIRECTION_USES <= set(after["prohibited_uses"])
    assert {"CONTEXT", "BUSINESS_CONTEXT"} <= set(after["allowed_uses"])
    assert after["financial_direction_eligibility"]["direction_eligible"] is False
    assert not p.observations([row], {"authority_records": [record]}, fields)
    assert (row, record, fields) == original


@pytest.mark.parametrize("value,expected", [(20, p.Effect.POSITIVE), (-20, p.Effect.DETERIORATION)])
def test_compatible_comparison_preserved(value, expected):
    row, record, fields = fixture(value=value, prior=5)
    assert g.narrow_financial_authority(record, row, fields[row["ref_id"]]) == record
    obs = p.observations([row], {"authority_records": [record]}, fields)
    assert len(obs) == 1 and next(iter(obs.values()))["effect"] == expected


@pytest.mark.parametrize("change", ["period_type", "currency", "statement_basis", "entity_scope", "unit", "duration", "denied"])
def test_incompatible_or_denied_comparison_is_not_directional(change):
    row, record, fields = fixture(prior=5)
    scope = fields[row["ref_id"]]["fields"]
    if change == "denied":
        record["prohibited_uses"] = ["OVERALL_DIRECTION"]
    elif change == "duration":
        scope["prior_period"]["start"] = "2025-04-02"
    else:
        scope["prior_period"][change] = "different"
    row["statement"] = _compact(scope)
    assert not p.observations([row], {"authority_records": [record]}, fields)


@pytest.mark.parametrize("polarity", ["BULLISH", "BEARISH", "NEUTRAL"])
def test_atomic_polarity_uses_typed_eligibility_not_claim_wording(polarity):
    row, record, fields = fixture()
    atomic = [dict(parent_source_refs=[row["ref_id"]], claim=dict(
        polarity=polarity, text="Revenue presence alone does not establish growth."))]
    args = (atomic, [row], {"authority_records": [record]}, fields)
    if polarity == "NEUTRAL":
        g.validate_atomic_direction(*args)
    else:
        with pytest.raises(ValueError, match="without_eligible_observed_source"):
            g.validate_atomic_direction(*args)
        atomic[0]["claim"]["text"] = "A wholly different language or wording."
        with pytest.raises(ValueError, match="without_eligible_observed_source"):
            g.validate_atomic_direction(*args)


def test_mixed_refs_with_valid_comparative_owner_apply_existing_policy():
    absolute, ra, fa = fixture()
    comparison, rc, fc = fixture(prior=5)
    old = comparison["ref_id"]
    comparison["ref_id"] = rc["ref_id"] = "canonical:earnings_comparison:fictional"
    fc[comparison["ref_id"]] = fc.pop(old)
    atomic = [dict(parent_source_refs=[absolute["ref_id"], comparison["ref_id"]],
                   claim=dict(polarity="BULLISH", text="Source-owned comparison."))]
    g.validate_atomic_direction(atomic, [absolute, comparison], {"authority_records": [ra, rc]}, {**fa, **fc})
    rc["prohibited_uses"] = ["OVERALL_DIRECTION"]
    with pytest.raises(ValueError, match="without_eligible_observed_source"):
        g.validate_atomic_direction(atomic, [absolute, comparison], {"authority_records": [ra, rc]}, {**fa, **fc})


def test_source_denials_only_narrow_and_add_comparative_recovery_without_fake_values():
    row, record, fields = fixture()
    record["allowed_uses"] = ["CONTEXT"]
    after = g.narrow_financial_authority(record, row, fields[row["ref_id"]])
    assert after["allowed_uses"] == ["CONTEXT"]
    recovery = c.limitation_catalog(dict(ticker="FICTIONAL", financial_state=dict(denials=[])),
                                   {"authority_records": [after]})
    assert len(recovery) == 1
    assert next(iter(recovery.values()))["source_ref"] == row["ref_id"]


def test_neutral_context_claim_preserves_numeric_source():
    row, record, fields = fixture()
    raw = {"claims": [dict(effect="CONFIDENCE_ONLY", text="Current amount is context only.",
                            evidence_refs=[row["ref_id"]], observation_ids=[], materiality="CONTEXT_ONLY")]}
    core = p.materialize_core("FICTIONAL", raw, [row], {"authority_records": [record]}, fields)
    assert core["atomic_claims"][0]["claim"]["polarity"] == "NEUTRAL"
    assert core["observations"] == {}
