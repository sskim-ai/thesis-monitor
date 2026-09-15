from __future__ import annotations

from copy import deepcopy

from scripts import real_cohort_policy_validation_m12bk_r2 as runner


def _view(
    direction: str,
    buy: float,
    sell: float,
    *,
    new_buyer: str = "WAIT",
    holder: str = "HOLDABLE",
) -> dict[str, object]:
    return {
        "overall_direction": direction,
        "directional_balance": {"buy": buy, "sell": sell},
        "directional_confidence": "MEDIUM",
        "business_thesis_change": "UNCHANGED",
        "new_buyer_stance": new_buyer,
        "holder_stance": holder,
        "evidence_refs": {
            "material_anchor_refs": ["canonical:valuation:current"],
            "core_judgment_refs": ["canonical:valuation:current"],
            "dominant_evidence_refs": ["canonical:valuation:current"],
            "risk_refs": [],
            "unknown_refs": [],
            "new_buyer_confirmation_refs": ["decision-evidence:confirm"],
            "holder_invalidation_refs": ["decision-evidence:invalidate"],
        },
        "canonical_semantic_status": "PASS",
        "price_technical_ref_count": 0,
        "supply_ref_count": 0,
        "stage2_timing_or_supply_ref_count": 0,
    }


def test_report_contract_is_complete_and_unique() -> None:
    assert len(runner.REPORT_SLUGS) == 34
    assert len(set(runner.REPORT_SLUGS)) == 34
    assert runner.NUMBERS["repository-provenance"] == 1
    assert runner.NUMBERS["program-completion"] == 34


def test_adjacent_primary_policy_tolerates_only_clean_same_stance_boundary() -> None:
    paths = {
        "monolithic": _view("HOLD", 5.5, 4.5),
        "two_stage": _view("BUY", 6.0, 4.0),
    }
    assert runner.classify_primary_boundary(
        paths, evidence_universe_preserved=True
    ) == "POLICY_TOLERATED_ADJACENT_PRIMARY_BOUNDARY"

    paths["two_stage"]["holder_stance"] = "REVIEW"
    assert runner.classify_primary_boundary(
        paths, evidence_universe_preserved=True
    ) == "PRIMARY_BOUNDARY_POLICY_EXCEPTION"


def test_adjacent_primary_policy_fails_closed_on_semantic_or_source_loss() -> None:
    paths = {
        "monolithic": _view("HOLD", 4.5, 5.5),
        "two_stage": _view("SELL", 4.0, 6.0),
    }
    assert runner.classify_primary_boundary(
        paths, evidence_universe_preserved=False
    ) == "PRIMARY_BOUNDARY_POLICY_EXCEPTION"
    paths["two_stage"]["canonical_semantic_status"] = "FAIL"
    assert runner.classify_primary_boundary(
        paths, evidence_universe_preserved=True
    ) == "PRIMARY_BOUNDARY_POLICY_EXCEPTION"


def test_holder_policy_requires_current_material_ref_and_forbids_timing_source() -> None:
    paths = {
        "monolithic": _view("HOLD", 4.5, 5.5, holder="HOLDABLE"),
        "two_stage": _view("HOLD", 4.5, 5.5, holder="REVIEW"),
    }
    assert runner.classify_holder_boundary(
        paths, current_material_refs=("canonical:valuation:current",)
    ) == "POLICY_TOLERATED_HOLDER_BOUNDARY"

    invalid = deepcopy(paths)
    invalid["two_stage"]["stage2_timing_or_supply_ref_count"] = 1
    assert runner.classify_holder_boundary(
        invalid, current_material_refs=("canonical:valuation:current",)
    ) == "HOLDER_POLICY_EXCEPTION"
    assert runner.classify_holder_boundary(
        paths, current_material_refs=("canonical:missing",)
    ) == "HOLDER_POLICY_EXCEPTION"


def test_coupled_entry_policy_requires_independent_confirmation_contract() -> None:
    paths = {
        "monolithic": _view("BUY", 6.0, 4.0, new_buyer="ATTRACTIVE"),
        "two_stage": _view("HOLD", 5.5, 4.5, new_buyer="WAIT"),
    }
    assert runner.classify_coupled_entry_boundary(
        paths, independent_analogue=True
    ) == "POLICY_TOLERATED_COUPLED_ENTRY_BOUNDARY"
    assert runner.classify_coupled_entry_boundary(
        paths, independent_analogue=False
    ) == "NEW_BUYER_POLICY_EXCEPTION"


def test_calibration_policy_tolerates_only_small_same_decision_variance() -> None:
    paths = {
        "monolithic": _view("HOLD", 5.0, 5.0),
        "two_stage": _view("HOLD", 5.5, 4.5),
    }
    assert runner.classify_calibration(paths) == "POLICY_TOLERATED_CALIBRATION_VARIANCE"
    paths["two_stage"]["directional_balance"] = {"buy": 6.0, "sell": 4.0}
    assert runner.classify_calibration(paths) == "CALIBRATION_POLICY_EXCEPTION"


def test_artifact_inventory_excludes_raw_model_material() -> None:
    paths = {str(path) for path in runner.artifact_files()}
    assert not any("model-calls" in path for path in paths)
    assert not any(path.endswith("prompt.txt") for path in paths)
    assert not any(path.endswith("output.raw.json") for path in paths)
    assert not any(path.endswith("transport.log") for path in paths)


def test_reference_family_preserves_financial_evidence_boundaries() -> None:
    assert runner._ref_family("canonical:valuation:current") == "canonical_valuation"
    assert runner._ref_family("canonical:cashflow:abc") == "canonical_cashflow_derived"
    assert (
        runner._ref_family("canonical:cashflow-reported:abc")
        == "canonical_cashflow_reported"
    )
    assert runner._ref_family("decision-evidence:abc") == "packet_decision_evidence"
