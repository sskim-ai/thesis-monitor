from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.financial_framework_claim_service import FrameworkClaimKind
from scripts import sol_leverage_target_delta_m12y as y


def test_root_causes_and_targets_were_frozen_before_implementation():
    root = y.read(y.ROOT)
    assert root["status"] == "FROZEN_BEFORE_IMPLEMENTATION"
    assert (
        root["contrastive_exclusion"]["root_cause"]
        == "CONTRASTIVE_REPLACEMENT_EXCLUSION_NOT_RECOGNIZED"
    )
    assert (
        root["leverage_target"]["root_cause"]
        == "EXACT_FIXTURE_TARGET_OVERCONSTRAINED_EXPECT_6_0"
    )
    assert root["leverage_target"]["selected_branch"] == "A_FIXTURE_TARGET_CORRECTION_ONLY"
    assert (
        root["business_delta"]["root_cause"]
        == "ABSOLUTE_NEGATIVE_STATE_MISREAD_AS_WEAKENING_DELTA"
    )
    assert root["business_delta"]["frozen_target"] == "UNCHANGED"


def test_required_artifact_names_are_complete_and_unique():
    assert set(y.SLUGS) == set(range(1, 87))
    assert len(set(y.SLUGS.values())) == 86


@pytest.mark.parametrize("text", y.read(y.FIXTURES)["exclusion_positive"])
def test_contrastive_replacement_is_explicit_exclusion(text):
    claims = y.financial_framework_claims(text)
    assert claims
    assert all(claim.kind == FrameworkClaimKind.EXPLICIT_EXCLUSION for claim in claims)
    assert y._validate_framework_text(text).valid


@pytest.mark.parametrize("text", y.read(y.FIXTURES)["exclusion_negative"])
def test_contradictory_conditional_and_ambiguous_contrasts_fail(text):
    claims = y.financial_framework_claims(text)
    assert claims
    assert any(claim.kind != FrameworkClaimKind.EXPLICIT_EXCLUSION for claim in claims)
    assert not y._validate_framework_text(text).valid


def test_contrastive_exclusion_does_not_immunize_another_field():
    candidate = {
        "sector_interpretation": {
            "text": "순부채 대신 규제자본을 본다.",
            "evidence_refs": [],
        },
        "risk_context": {
            "text": "운전자본 악화가 핵심 투자 리스크다.",
            "evidence_refs": [],
        },
    }
    result = y.validate_directional_financial_semantics(
        candidate,
        supplied_refs=(),
        allowed_ref_ids=(),
        sector_framework="bank_or_insurer",
    )
    assert not result.valid
    assert "financial_sector_generic_reasoning" in result.errors


def test_fic_fin_08_exact_m12x_output_now_passes_offline():
    replay = y.exact_fic_fin_08_replay()
    assert replay["status"] == "PASS", replay
    assert replay["after_errors"] == []
    assert replay["source_output_unchanged"]


def test_leverage_target_and_no_score_contract_are_generic():
    audit = y.leverage_fixture_audit()
    assert audit["status"] == "PASS"
    assert audit["fixed_score_rule_count"] == 0
    assert audit["evidence_count_bucket_rule_count"] == 0
    first = audit["rows"][0]
    assert (first["expected_direction"], first["expected_buy"], first["expected_sell"]) == (
        "SELL",
        4.0,
        6.0,
    )


def test_business_delta_fixtures_separate_absolute_state_from_change():
    audit = y.delta_fixture_audit()
    assert audit["status"] == "PASS"
    rows = {row["id"]: row for row in audit["rows"]}
    assert rows["DELTA-01"]["expected"] == "UNCHANGED"
    assert rows["DELTA-02"]["expected"] == "WEAKENED"
    assert rows["DELTA-03"]["expected"] == "UNCHANGED"
    assert rows["DELTA-04"]["expected"] == "STRENGTHENED"


def _candidate(change: str, refs: list[str], ticker: str = "GENERIC"):
    return {
        "ticker": ticker,
        "business_thesis_change": change,
        "business_thesis_context": {"text": "bounded", "evidence_refs": refs},
    }


def _context(*statements: str):
    return {
        "evidence": [
            {"alias": f"E{index:02d}", "statement": statement}
            for index, statement in enumerate(statements, start=1)
        ]
    }


def test_business_delta_audit_rejects_absolute_state_as_weakening():
    result = y.business_delta_audit(
        _candidate("WEAKENED", ["E01"]),
        _context("A high complete debt balance and thin cash buffer reduce resilience."),
    )
    assert result["status"] == "FAIL"
    assert result["unsupported_absolute_state_to_delta"]


def test_business_delta_audit_accepts_explicit_change_and_ignores_conditional():
    weakened = y.business_delta_audit(
        _candidate("WEAKENED", ["E01"]),
        _context("High debt worsened materially versus the supplied prior baseline."),
    )
    strengthened = y.business_delta_audit(
        _candidate("STRENGTHENED", ["E01"]),
        _context("Operating and cash conversion improved versus the prior comparable period."),
    )
    conditional = y.business_delta_audit(
        _candidate("WEAKENED", ["E01"]),
        _context("Refinancing stress could weaken resilience."),
    )
    assert weakened["status"] == strengthened["status"] == "PASS"
    assert conditional["status"] == "FAIL"


def test_fic_fin_05_exact_delta_target_is_unchanged():
    context = y.read(y.M12X_OUTPUT / "contexts/FIC-FIN-05.json")
    old = y._m12x_rows()["FIC-FIN-05"]
    assert y.business_delta_audit(old, context)["status"] == "FAIL"
    corrected = {**old, "business_thesis_change": "UNCHANGED"}
    assert y.business_delta_audit(corrected, context)["status"] == "PASS"


def test_target_calibration_uses_frozen_m12y_targets():
    for ticker, buy in y.TARGET_BUYS.items():
        row = {"ticker": ticker, "core": {"directional_balance": {"buy": buy}}}
        assert y.calibration_audit(row)["status"] == "PASS"
        row["core"]["directional_balance"]["buy"] = buy + 0.5
        assert y.calibration_audit(row)["status"] == "FAIL"


def test_only_one_business_delta_prompt_clarification_was_added():
    after = Path("scripts/directional_core_price_timing_holdout.py").read_text()
    marker = "business_thesis_change is a change assessment, not an absolute quality label."
    assert not y.read(y.ROOT)["business_delta"][
        "existing_prompt_explicitly_separates_absolute_state_from_change"
    ]
    assert y._base_hash("scripts/directional_core_price_timing_holdout.py") == (
        y.BASE_FILE_SHA256["scripts/directional_core_price_timing_holdout.py"]
    )
    assert after.count(marker) == 1
    assert y._freeze_paths(("app/services/directional_balance_service.py",))["status"] == "PASS"


def test_base_hash_has_shallow_checkout_fallback(monkeypatch):
    path = "scripts/directional_core_price_timing_holdout.py"

    def unavailable(_path):
        raise y.subprocess.CalledProcessError(128, ["git", "show"])

    monkeypatch.setattr(y, "_base_bytes", unavailable)
    assert y._base_hash(path) == y.BASE_FILE_SHA256[path]


def test_runtime_and_frozen_threshold_contracts_remain_unchanged():
    root = y.read(y.ROOT)
    assert (root["runtime"]["model"], root["runtime"]["effort"]) == (
        "gpt-5.6-sol",
        "xhigh",
    )
    assert root["runtime"]["timeout_seconds"] == 1800
    assert root["runtime"]["subjects_per_context"] == 4
    assert root["runtime"]["wrapper_retry_count"] == 0
    assert root["semantic_freeze"]["directional_threshold"] == 6.0
    assert root["semantic_freeze"]["directional_increment"] == 0.5
    assert root["semantic_freeze"]["fixed_score_rule_count"] == 0


def test_source_contexts_remain_identical_to_m12x():
    _packets, _owned, _catalogs, contexts = y.m12.fictional_inputs("m12y-source-test")
    for ticker in y.m12.TICKERS:
        previous = json.loads(
            (y.M12X_OUTPUT / "contexts" / f"{ticker}.json").read_text()
        )
        current = contexts[ticker]
        previous["assessment_date"] = current["assessment_date"]
        assert current == previous


def test_canary_rejects_failed_phase_a(tmp_path, monkeypatch):
    monkeypatch.setattr(y, "OUTPUT", tmp_path)
    y.write(tmp_path / "phase-a-receipt.json", {"status": "FAIL"})
    with pytest.raises(ValueError, match="m12y_phase_a_not_passed"):
        y.run()
