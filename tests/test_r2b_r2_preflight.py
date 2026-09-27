from copy import deepcopy

import pytest

from scripts import r2b_r2_preflight as p


def context(present):
    ref = "canonical:financial_quality:2026-06-30"
    return dict(ticker="FICTIONAL", eligible_claim_refs=["claim:fictional"], premium_eligible_claim_refs=[],
        accepted_fundamental_claims=[], eligible_non_price_evidence=[dict(ref_id=ref,
            label="financial_quality", statement=dict(state="caution_usable", source_period="2026-06-30"))]
            if present else [],
        data_quality_catalog=dict(evidence_refs=[ref] if present else [],
                                  positive_quality_refs=[], material_disclosure_failure_refs=[]))


@pytest.mark.parametrize("present", [True, False])
def test_actual_a_materializer_detects_gap_that_schema_misses(present):
    ctx = context(present)
    schema = p.owner.future_pass_a_batch_schema(subjects=["FICTIONAL"], subject_contexts={"FICTIONAL": ctx})
    assert p.schema_check(schema)["dialect"]["status"] == "PASS"
    _, receipt = p.materialization_probe("FICTIONAL", schema, ctx)
    assert receipt["status"] == ("PASS" if present else "FAIL")
    assert receipt["synthetic_only"] and not receipt["actual_model_output"]
    if not present:
        assert receipt["legacy_semantic"]["errors"] == ["FICTIONAL:data_quality_effect_missing_reason_or_ref"]


def full_receipt():
    rows = [dict(ticker=t, status="PASS", decision_mode="EVIDENCE_BASED", Core="PASS", A="PASS", B="PASS",
                 NewBuyer="PASS", Holder="PASS", a_materialization=dict(status="PASS"))
            for tickers in p.io.UNIVERSE.values() for t in tickers]
    return dict(status="PASS", ready=22, rows=rows)


@pytest.mark.parametrize("broken", ["missing", "duplicate", "blocked", "materialization", "old_schema_only"])
def test_no_partial_or_schema_only_dispatch(broken):
    receipt = full_receipt()
    if broken == "missing":
        receipt["rows"].pop()
    elif broken == "duplicate":
        receipt["rows"][-1] = deepcopy(receipt["rows"][0])
    elif broken == "blocked":
        receipt["rows"][0]["A"] = "BLOCKED"
    elif broken == "materialization":
        receipt["rows"][0]["a_materialization"]["status"] = "FAIL"
    else:
        receipt["rows"][0].pop("a_materialization")
    with pytest.raises(ValueError):
        p.require_whole_ready(receipt)


def test_full_preflight_still_requires_separate_request_freeze():
    receipt = p.require_whole_ready(full_receipt())
    assert receipt["status"] == "READY_FOR_REQUEST_FREEZE"
    assert not receipt["actual_model_dispatch_authorized"]


def test_read_audit_allows_exact_neutral_receipt_only(tmp_path):
    path = tmp_path / "INDEPENDENT_FREEZE_RECEIPT.json"
    audit = p.SourceReadAudit([path], [tmp_path])
    audit("open", (str(path), "r", 0))
    with pytest.raises(PermissionError, match="assessment_content_forbidden"):
        audit("open", (str(tmp_path / "INDEPENDENT_BLIND_ASSESSMENT.json"), "r", 0))
    with pytest.raises(PermissionError, match="outside_allowlist"):
        audit("open", (str(tmp_path / "not-allowlisted.json"), "r", 0))
    assert audit.receipt()["reads"] == {str(path): 1}
    assert not audit.receipt()["independent_assessment_content_read"]
