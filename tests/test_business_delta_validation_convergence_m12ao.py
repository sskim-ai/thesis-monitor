from __future__ import annotations

import inspect

from app.services.business_delta_evidence_service import (
    BusinessDeltaCapability,
    BusinessDeltaEvidenceRole,
    build_business_delta_evidence_view,
    business_delta_evidence_view_sha256,
)
from scripts import business_delta_alias_balance_confidence_m12z as legacy
from scripts import business_delta_validation_convergence_m12ao as runner
from scripts import directional_financial_context_m12 as fixtures


def _inputs():
    _packets, owned, catalogs, contexts = fixtures.fictional_inputs(
        "m12ao-deterministic"
    )
    views = {
        ticker: build_business_delta_evidence_view(
            owned[ticker], catalogs[ticker], context=contexts[ticker]
        )
        for ticker in fixtures.TICKERS
    }
    return owned, catalogs, contexts, views


def _candidate(ticker: str, change: str, refs: list[str], text: str = "근거 판단"):
    return {
        "ticker": ticker,
        "business_thesis_change": change,
        "business_thesis_context": {"evidence_refs": refs, "text": text},
    }


def _audit(ticker: str, change: str, refs: list[str], text: str = "근거 판단"):
    owned, catalogs, contexts, views = _inputs()
    return legacy.business_delta_audit(
        _candidate(ticker, change, refs, text),
        contexts[ticker],
        catalogs[ticker],
        owned=owned[ticker],
        view=views[ticker],
    )


def test_delta_conv_01_inventory_direction_remains_unspecified() -> None:
    result = _audit("FIC-FIN-06", "UNRESOLVED", ["E04"])
    assert result["status"] == "PASS", result
    assert result["linked_evidence"][0]["direction_semantics"] == (
        "DIRECTION_UNSPECIFIED"
    )
    assert result["linked_evidence"][0]["supported_change_directions"] == []


def test_delta_conv_02_receivables_direction_remains_unspecified() -> None:
    result = _audit("FIC-FIN-06", "UNRESOLVED", ["E03"])
    assert result["status"] == "PASS", result
    assert result["linked_evidence"][0]["direction_semantics"] == (
        "DIRECTION_UNSPECIFIED"
    )


def test_delta_conv_03_stored_thesis_is_baseline_only() -> None:
    result = _audit("FIC-FIN-06", "STRENGTHENED", ["E06"])
    assert result["status"] == "FAIL"
    assert result["linked_evidence"][0]["canonical_delta_role"] == (
        "BASELINE_CONTEXT"
    )
    assert result["linked_evidence"][0]["delta_evidence_eligible"] is False


def test_delta_conv_04_ocf_lower_comparable_is_weakened() -> None:
    result = _audit("FIC-FIN-02", "WEAKENED", ["E08"])
    assert result["status"] == "PASS", result
    assert result["linked_evidence"][0]["supported_change_directions"] == [
        "WEAKENED"
    ]


def test_delta_conv_05_explicit_operating_improvement_is_strengthened() -> None:
    result = _audit("FIC-FIN-06", "STRENGTHENED", ["E09"])
    assert result["status"] == "PASS", result
    assert result["linked_evidence"][0]["supported_change_directions"] == [
        "STRENGTHENED"
    ]


def test_delta_conv_06_unchanged_only_rejects_changed_state() -> None:
    result = _audit("FIC-FIN-05", "STRENGTHENED", ["E05", "E06", "E09"])
    assert result["status"] == "FAIL"
    assert "BUSINESS_DELTA_CAPABILITY_VALUE_VIOLATION" in result["errors"]


def test_delta_conv_07_known_positive_plus_unspecified_can_be_unresolved() -> None:
    result = _audit("FIC-FIN-06", "UNRESOLVED", ["E03", "E04", "E06", "E09"])
    assert result["status"] == "PASS", result
    assert result["supported_change_directions"] == ["STRENGTHENED"]
    assert len(result["direction_unspecified_eligible_refs"]) == 2
    assert result["unsupported_absolute_state_to_delta_count"] == 0


def test_delta_conv_08_all_known_positive_rejects_weakened() -> None:
    result = _audit("FIC-FIN-01", "WEAKENED", ["E04", "E08", "E09"])
    assert result["status"] == "FAIL"
    assert "BUSINESS_DELTA_DIRECTION_CONTRADICTS_EVIDENCE" in result["errors"]


def test_exact_fic_fin_06_roles_and_view_identity_converge() -> None:
    owned, catalogs, contexts, views = _inputs()
    view = views["FIC-FIN-06"]
    items = {item.alias: item for item in view.items}
    assert view.capability == BusinessDeltaCapability.AI_JUDGMENT
    assert items["E03"].role == BusinessDeltaEvidenceRole.ELIGIBLE_OBSERVED_CHANGE
    assert items["E04"].role == BusinessDeltaEvidenceRole.ELIGIBLE_OBSERVED_CHANGE
    assert items["E03"].supported_change_directions == ()
    assert items["E04"].supported_change_directions == ()
    assert items["E06"].role == BusinessDeltaEvidenceRole.THESIS_BASELINE_CONTEXT
    assert items["E09"].supported_change_directions == ("STRENGTHENED",)

    candidate = _candidate(
        "FIC-FIN-06",
        "UNRESOLVED",
        [item.canonical_ref for item in (items["E03"], items["E04"], items["E06"], items["E09"])],
        "영업 성장은 강화 신호지만 재고와 매출채권의 동반 증가는 그 질을 "
        "모호하게 해 논지 변화가 아직 해소되지 않았다.",
    )
    result = legacy.business_delta_audit(
        candidate,
        contexts["FIC-FIN-06"],
        catalogs["FIC-FIN-06"],
        owned=owned["FIC-FIN-06"],
        view=view,
    )
    expected_hash = business_delta_evidence_view_sha256(view)
    assert result["status"] == "PASS", result
    assert result["pre_model_delta_view_sha256"] == expected_hash
    assert result["post_model_validator_delta_view_sha256"] == expected_hash
    assert result["pre_post_delta_view_identity_mismatch_count"] == 0
    assert result["business_delta_semantic_projection_mismatch_count"] == 0
    assert result["legacy_raw_text_direction_rederivation_count"] == 0
    assert result["legacy_raw_text_eligibility_rederivation_count"] == 0


def test_fic_fin_02_mixed_evidence_allows_weakened_or_unresolved() -> None:
    refs = ["E01", "E04", "E08", "E10"]
    assert _audit("FIC-FIN-02", "WEAKENED", refs)["status"] == "PASS"
    assert _audit("FIC-FIN-02", "UNRESOLVED", refs)["status"] == "PASS"


def test_model_facing_business_delta_view_contract_is_unchanged() -> None:
    _owned, _catalogs, _contexts, views = _inputs()
    context = views["FIC-FIN-06"].model_context()
    assert context["contract"] == "business-delta-evidence-view-v1"
    assert "direction_unspecified_eligible_refs" not in context
    assert "post_model_validator_contract" not in context


def test_m12ao_runner_freezes_required_local_only_contract() -> None:
    assert len(runner.SLUGS) == 125
    assert len(set(runner.SLUGS.values())) == 125
    assert len(runner._required_report_files()) == 125
    assert (runner.MODEL, runner.EFFORT, runner.TIMEOUT_SECONDS) == (
        "gpt-5.6-sol",
        "xhigh",
        1800,
    )
    assert runner.EXPECTED_FICTIONAL_CALLS == 12
    assert runner.EXPECTED_FICTIONAL_ROWS == 24
    assert runner.EXPECTED_SHADOW_CALLS == 18
    assert runner.ICLOUD.name == "Thesis Monitor"


def test_m12ao_completion_includes_required_shadow_safety_counts() -> None:
    source = inspect.getsource(runner.closeout)
    for field in (
        "shadow_financial_sector_framework_failure_count",
        "shadow_adr_security_basis_failure_count",
        "shadow_cyclical_valuation_framework_failure_count",
        "shadow_core_mutation_after_stance_count",
    ):
        assert field in source
