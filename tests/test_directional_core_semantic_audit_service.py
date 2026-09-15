from __future__ import annotations

from app.services.direction_timing_ownership_service import stage_alias_catalogs
from app.services.directional_core_semantic_audit_service import (
    CONTRACT_VERSION,
    SemanticApplicability,
    audit_owned_directional_core_semantics,
)
from scripts import boundary_band_application_scope_m12aa as boundary
from scripts import business_delta_alias_balance_confidence_m12z as delta
from scripts import configured_signal_field_ownership_m12at as configured
from scripts import directional_financial_context_m12 as monitored
from scripts import new_issuer_holdout_selection_ownership_proof as fresh
from scripts import synthetic_canary_fixture_repair_ownership_resume as synthetic


def test_owned_adapter_runs_every_applicable_canonical_service() -> None:
    owned = synthetic.fictional_owned("SYNTHETIC_NEW_HOLDOUT", market="us")
    candidate = synthetic.fixture_core(owned)
    catalog, _timing = stage_alias_catalogs(owned)

    audit = audit_owned_directional_core_semantics(
        candidate,
        owned=owned,
        catalog=catalog,
        lifecycle_mode="INITIAL_ANALYSIS",
    )

    assert audit.contract == CONTRACT_VERSION
    assert audit.status == "PASS"
    assert not audit.hard_errors
    assert set(audit.applicability.values()) <= {
        SemanticApplicability.APPLICABLE,
        SemanticApplicability.APPLICABLE_WITH_EMPTY_VIEW,
    }
    assert all(row.called for row in audit.semantic_service_provenance)


def test_canonical_financial_failure_is_a_shared_hard_error() -> None:
    _packets, owned, catalogs, _contexts = configured._m12at_fictional_inputs(
        "m12bi-test"
    )
    candidate = {
        "ticker": "FIC-FIN-01",
        "buy_drivers": [
            {
                "text": "현재 FCF가 증가했다.",
                "evidence_refs": [
                    "canonical:fictional:FIC-FIN-01:ocf-current"
                ],
            }
        ],
    }

    audit = audit_owned_directional_core_semantics(
        candidate,
        owned=owned["FIC-FIN-01"],
        catalog=catalogs["FIC-FIN-01"],
        lifecycle_mode="MONITORED_STAGE1_FINANCIAL",
        include_working_capital=False,
        include_business_delta=False,
        include_market_expectation=False,
    )

    assert audit.status == "FAIL"
    assert audit.hard_errors == ("unsupported_current_fcf_claim",)


def test_fresh_proof_critical_audit_requires_and_records_canonical_catalog() -> None:
    owned = synthetic.fictional_owned("SYNTHETIC_NEW_HOLDOUT", market="us")
    candidate = synthetic.fixture_core(owned)
    catalog, _timing = stage_alias_catalogs(owned)

    missing = fresh.core_partial_audit(
        (candidate,),
        {candidate.ticker: owned},
        proof_critical=True,
    )
    accepted = fresh.core_partial_audit(
        (candidate,),
        {candidate.ticker: owned},
        catalogs={candidate.ticker: catalog},
        proof_critical=True,
    )

    assert missing["status"] == "FAIL"
    assert missing["rows"][0]["errors"] == [
        "fresh_canonical_semantic_catalog_required"
    ]
    assert accepted["status"] == "PASS"
    assert accepted["canonical_semantic_audit_consumed"] is True
    canonical = accepted["rows"][0]["canonical_semantic_audit"]
    assert canonical["contract"] == CONTRACT_VERSION
    assert canonical["applicability"]["business_delta_semantics"] == (
        SemanticApplicability.APPLICABLE
    )
    business_delta_provenance = next(
        row
        for row in canonical["semantic_service_provenance"]
        if row["family"] == "business_delta_semantics"
    )
    assert business_delta_provenance["called"] is True
    assert business_delta_provenance["hard_decision_source"] == "CANONICAL_SERVICE"


def test_fresh_initial_analysis_business_delta_remains_decision_active() -> None:
    owned = synthetic.fictional_owned("SYNTHETIC_NEW_HOLDOUT", market="us")
    candidate = synthetic.fixture_core(owned).model_copy(
        update={"business_thesis_change": "UNRESOLVED"}
    )
    catalog, _timing = stage_alias_catalogs(owned)

    result = fresh.core_partial_audit(
        (candidate,),
        {candidate.ticker: owned},
        catalogs={candidate.ticker: catalog},
        proof_critical=True,
    )

    assert result["status"] == "FAIL"
    assert "BUSINESS_DELTA_CAPABILITY_VALUE_VIOLATION" in result["rows"][0][
        "errors"
    ]
    assert "BUSINESS_DELTA_UNRESOLVED_WITHOUT_ELIGIBLE_AMBIGUITY" in result[
        "rows"
    ][0]["errors"]


def test_proof_critical_business_delta_fallback_is_sealed() -> None:
    result = delta.business_delta_audit(
        {
            "ticker": "FIC-FIN-01",
            "business_thesis_change": "UNCHANGED",
            "business_thesis_context": {"evidence_refs": ["E01"]},
        },
        {"ticker": "FIC-FIN-01", "evidence": []},
        {"ticker": "FIC-FIN-01", "entries": []},
        proof_critical=True,
    )

    assert result["status"] == "FAIL"
    assert result["errors"] == ["CANONICAL_BUSINESS_DELTA_VIEW_REQUIRED"]
    assert result["proof_critical_fallback_participation"] is False


def test_fixture_specific_duplicate_hard_semantics_are_retired() -> None:
    assert monitored._case_semantic_errors(
        "FIC-FIN-05",
        object(),
        selected_financial_refs=set(),
    ) == ()
    assert boundary._fic_fin_05_hard_errors(
        {"ticker": "FIC-FIN-05", "overall_direction": "BUY"}
    ) == []
