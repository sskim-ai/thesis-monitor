"""Synthetic source-authority tests; never real company or model approval."""
from datetime import date
import hashlib
import json

import pytest
from pydantic import ValidationError

from app.services.economic_interpretation_policy import ReportedComparisonInput, ReportedStatementInput
from app.services.reported_fact_owner import (
    BackendReportedFactOwner, FactUseGrant, RegisteredIssuerBinding, ReportedFact,
)
from app.services.sec_business_field_quality_service import sha
from app.services.sec_financial_snapshot_service import _companyfacts_snapshots
from app.services.unified_snapshot_contract import digest
from tests.test_external_api_accuracy import _companyfact_entry, _companyfacts_payload


def owner_fixture(identity="UNSEEN_US_FACT", *, market="US", security_type="common_stock", current_amount=30,
                  conflicting_revenue=False):
    current = dict(_companyfact_entry(current_amount, fp="Q2", start="2026-04-01", end="2026-06-30",
                                     filed="2026-08-01"), accn="0000001234-26-000001")
    previous = dict(current, start="2025-04-01", end="2025-06-30", val=20)
    raw = _companyfacts_payload("us-gaap", {
        "RevenueFromContractWithCustomerExcludingAssessedTax": [dict(r, val=r["val"]*10) for r in (current,previous)],
        "OperatingIncomeLoss": [current, previous]})
    if conflicting_revenue:
        values = raw["facts"]["us-gaap"]["RevenueFromContractWithCustomerExcludingAssessedTax"]["units"]["USD"]
        values.append(dict(values[0], val=values[0]["val"]+1))
    raw["cik"] = 1234
    prior, formal = sorted(_companyfacts_snapshots(raw, identity), key=lambda row:row.financial_period_end)
    statements = [ReportedStatementInput(**{k:getattr(row,k) for k in ReportedStatementInput.model_fields})
                  for row in (formal, prior)]
    comparison = ReportedComparisonInput(security_id=identity, ticker=identity, generation_id="fixture-execution",
        source_generation_id="fixture-source", owner_ref="SYNTHETIC_STATEMENT_OWNER",
        source_artifact_sha256=(sha(raw),), cutoff=date(2026,9,1), formal=statements[0], comparison=statements[1])
    discovery = dict(cik="0000001234", tickers=[identity], exchanges=["TEST"], filings=dict(recent=dict(
        accessionNumber=[current["accn"]], form=[current["form"]], filingDate=[current["filed"]])))
    registered = dict(roles=dict(security_identity=dict(records=[dict(record=dict(canonical_security_id=identity,
        ticker=identity, cik="0000001234", security_type=security_type, exchange="TEST", country=market))])))
    artifacts = {k:json.dumps(v).encode() for k,v in dict(companyfacts=raw, discovery=discovery, registration=registered).items()}
    for name in ("companyfacts", "discovery"):
        artifacts[name+"_receipt"] = json.dumps(dict(status="PASS", raw_sha256=hashlib.sha256(artifacts[name]).hexdigest(),
            generation_id="fixture-source", logical_request_id=f"financial:{identity}:{name}", role=f"financial:{identity}")).encode()
    anchors = {k:hashlib.sha256(v).hexdigest() for k,v in artifacts.items()}
    registration = RegisteredIssuerBinding(security_id=identity, ticker=identity, issuer_id="0000001234",
        market=market, exchange="TEST", security_type=security_type, registration_owner_ref="SYNTHETIC_REGISTRATION",
        registration_artifact_sha256=anchors["registration"], source_generation_id="fixture-source",
        execution_generation_id="fixture-execution", cutoff=comparison.cutoff)
    args = dict(registration=registration, artifacts=artifacts, trusted_artifact_sha256=anchors, comparison=comparison)
    return BackendReportedFactOwner(**args), args


def resolved(owner, admission, **change):
    args = dict(axis="DISPLAY", security_id=admission.fact.security_id,
                execution_generation_id=admission.fact.execution_generation_id,
                source_generation_id=admission.fact.source_generation_id)
    return owner.resolve(admission, **(args|change))


@pytest.mark.parametrize("identity,market,kind", [("UNSEEN_US_FACT","US","common_stock"),
    ("UNSEEN_KR_FACT","KR","common_stock"), ("UNSEEN_ADS_FACT","US","depositary_receipt")])
@pytest.mark.parametrize("amount,direction", [(30,"UP"),(10,"DOWN"),(20,"FLAT")])
def test_identity_and_evidence_permutation(identity, market, kind, amount, direction):
    owner, _ = owner_fixture(identity, market=market, security_type=kind, current_amount=amount)
    admitted = [owner.admit(f) for f in owner.facts]
    results = []
    for field in ("revenue", "operating_income"):
        pair = sorted((a for a in admitted if a.fact.field==field), key=lambda a:a.fact.period_end, reverse=True)
        result = owner.compare(*pair)
        assert result.factual_direction == direction
        assert result.permitted_core_roles == ()
        assert result.confidence_ceiling is None
        assert result.materiality == "MATERIALITY_POLICY_AUTHORITY_GAP"
        assert owner.verify_interpretation(result) == result
        results.append(result)
    assert len(results)==2
    assert all(resolved(owner,a)==a.fact for a in admitted)


@pytest.mark.parametrize("field,value", [("security_id","other"),("ticker","other"),("issuer_id","9999"),
    ("filing_accession","0000001234-26-000009"),("period_end",date(2026,6,29)),
    ("source_generation_id","other"),("execution_generation_id","other"),("currency","EUR"),
    ("occurrence_ordinal",99),("value",987.654321),("raw_source_sha256","a"*64)])
def test_correct_other_values_do_not_authorize_changed_fact(field,value):
    owner, _ = owner_fixture()
    changed = owner.facts[0].model_copy(update={field:value})
    with pytest.raises(ValueError, match="UNADMITTED_FACT_CAPSULE"):
        owner.admit(changed)


def test_caller_hash_and_forged_grant_not_independent_admission():
    owner, _ = owner_fixture()
    admission = owner.admit(owner.facts[0])
    forged = admission.model_copy(update={"admission_id":"a"*64,
        "admission_sha256":digest(admission.fact.model_dump(mode="json"))})
    with pytest.raises(ValueError, match="UNISSUED_OR_CHANGED"):
        resolved(owner, forged)
    grants = tuple(FactUseGrant(axis=g.axis,state="ALLOWED",policy_ref="SYNTHETIC_FORGED") for g in admission.grants)
    with pytest.raises(ValueError, match="UNISSUED_OR_CHANGED"):
        resolved(owner, admission.model_copy(update={"grants":grants}), axis="CORE_DIRECTION")
    other, _ = owner_fixture()
    with pytest.raises(ValueError, match="UNISSUED_OR_CHANGED"):
        resolved(other, admission)


@pytest.mark.parametrize("axis", ["CORE_CONTEXT","CORE_DIRECTION","OVERALL_DIRECTION","HOLDER_CONTEXT",
    "HOLDER_DIRECTION","NEWBUYER_CONTEXT","NEWBUYER_DIRECTION","UNKNOWN"])
def test_missing_or_different_consumer_grant_is_not_allowed(axis):
    owner, _ = owner_fixture()
    admission = owner.admit(owner.facts[0])
    with pytest.raises(ValueError, match="FACT_USE_GRANT_MISSING"):
        resolved(owner, admission, axis=axis)


@pytest.mark.parametrize("field", ["security_id","execution_generation_id","source_generation_id"])
def test_request_binding(field):
    owner, _ = owner_fixture()
    admission = owner.admit(owner.facts[0])
    with pytest.raises(ValueError, match="FACT_REQUEST_IDENTITY_MISMATCH"):
        resolved(owner, admission, **{field:"other"})


def test_independent_source_anchor_before_any_admission():
    _, args = owner_fixture()
    artifacts = dict(args["artifacts"], companyfacts=b'{"cik":1234}')
    with pytest.raises(ValueError, match="INDEPENDENT_SOURCE_ANCHOR_MISMATCH"):
        BackendReportedFactOwner(**(args|dict(artifacts=artifacts)))


def test_rehashed_projected_quality_is_not_an_independent_owner_receipt():
    _, args = owner_fixture()
    comparison = args["comparison"]
    fields = json.loads(comparison.formal.raw_financial_fields)
    for field in fields:
        if field.get("field") == "sec_business_quality":
            receipt = field["field_quality"]
            receipt["caller_approved"] = True
            receipt["receipt_sha256"] = sha({k:v for k,v in receipt.items() if k != "receipt_sha256"})
    forged = comparison.model_copy(update={"formal": comparison.formal.model_copy(
        update={"raw_financial_fields":json.dumps(fields)})})
    with pytest.raises(ValueError, match="INDEPENDENT_STATEMENT_PROJECTION_MISMATCH"):
        BackendReportedFactOwner(**(args|dict(comparison=forged)))


def test_whole_raw_conflict_not_hidden_by_rehash_and_independent_metric_survives():
    owner, args = owner_fixture(conflicting_revenue=True)
    assert {f.field for f in owner.facts} == {"operating_income"}
    assert owner.compare(*(owner.admit(f) for f in owner.facts)).factual_direction == "UP"
    comparison = args["comparison"]
    fields = json.loads(comparison.formal.raw_financial_fields)
    for field in fields:
        if field.get("field") == "sec_business_quality":
            receipt = field["field_quality"]
            receipt["errors"] = []
            receipt["receipt_sha256"] = sha({k:v for k,v in receipt.items() if k != "receipt_sha256"})
    forged = comparison.model_copy(update={"formal":comparison.formal.model_copy(update={
        "raw_financial_fields":json.dumps(fields), "financial_hard_errors":"[]"})})
    with pytest.raises(ValueError, match="INDEPENDENT_STATEMENT_PROJECTION_MISMATCH"):
        BackendReportedFactOwner(**(args|dict(comparison=forged)))


def test_concept_field_relabel_is_not_owner_qualification():
    _, args = owner_fixture()
    comparison = args["comparison"]
    fields = json.loads(comparison.formal.raw_financial_fields)
    for field in fields:
        if field.get("field") == "revenue":
            field["concept"] = "OperatingIncomeLoss"
    forged = comparison.model_copy(update={"formal":comparison.formal.model_copy(
        update={"raw_financial_fields":json.dumps(fields)})})
    with pytest.raises(ValueError, match="INDEPENDENT_STATEMENT_PROJECTION_MISMATCH"):
        BackendReportedFactOwner(**(args|dict(comparison=forged)))


@pytest.mark.parametrize("field,value", [("issuer_id","9999"),("security_id","other"),
    ("source_generation_id","other"),("execution_generation_id","other")])
def test_independent_owner_identity_generation_rejection(field,value):
    _, args = owner_fixture()
    with pytest.raises(ValueError):
        BackendReportedFactOwner(**(args|dict(registration=args["registration"].model_copy(update={field:value}))))


def test_closed_basis_extra_fields_and_changed_policy_result():
    owner, _ = owner_fixture()
    fact = owner.facts[0]
    for extra in ({"statement_basis":"caller_basis"},{"UNADMITTED_PROBE_RATIO":987.654321},{"value":True}):
        with pytest.raises(ValidationError):
            ReportedFact.model_validate(fact.model_dump(mode="json")|extra)
    admitted = [owner.admit(f) for f in owner.facts if f.field=="revenue"]
    result = owner.compare(*admitted)
    with pytest.raises(ValueError, match="UNISSUED_OR_CHANGED_INTERPRETATION"):
        owner.verify_interpretation(result.model_copy(update={"delta":999.0}))
    with pytest.raises(ValueError, match="EXACT_COMPARISON_MEMBERSHIP"):
        owner.compare(admitted[1], admitted[0])
