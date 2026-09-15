from __future__ import annotations

from pathlib import Path

from scripts import stage2_korean_lexical_boundary_m12am as runner


def test_m12am_report_contract_has_exactly_89_numbered_artifacts() -> None:
    assert len(runner._SLUG_SEQUENCE) == 89
    assert runner.SLUGS[1] == "repository-provenance"
    assert runner.SLUGS[49] == "shadow-stage2-language-contamination-audit"
    assert runner.SLUGS[89] == "program-completion"
    assert set(runner.SLUGS) == set(range(1, 90))


def test_legacy_shadow_reports_map_to_m12am_analysis_contract() -> None:
    assert runner.LEGACY_REPORT_MAP == {
        50: 41,
        51: 42,
        52: 43,
        53: 44,
        55: 47,
        60: 50,
        61: 52,
        62: 53,
        63: 55,
        64: 56,
        65: 57,
        66: 58,
        67: 59,
        68: 60,
        69: 61,
        70: 62,
        71: 63,
        72: 64,
        73: 65,
        74: 66,
        75: 67,
        76: 68,
        77: 69,
    }


def test_authoritative_m12al_identity_is_frozen() -> None:
    assert runner.M12AL_BUNDLE_SHA256 == (
        "7409289d73f6ecd4e9b2fbac7fb3d2ec937f9bbe931a4d11584022e31fe09535"
    )
    assert runner.M12AL_INDEXED_PAYLOADS == 190
    assert runner.M12AL_ZIP_ENTRIES == 191
    assert runner.M12AL_SHADOW_GENERATION_ID == (
        "20260911-m12ai-shadow-20260911T083524Z-8740a0bb34ed"
    )


def test_m12al_stop_and_exact_stage2_replay_are_reproduced() -> None:
    stop = runner._m12al_stop_reproduction()
    replay = runner._m12al_stage2_reaudit()

    assert stop["status"] == "REPRODUCED"
    assert stop["completed_model_calls"] == 6
    assert replay["status"] == "PASS"
    assert replay["exact_047810"]["status"] == "PASS"
    assert replay["exact_047810"]["timing_or_supply_refs"] == []
    assert replay["exact_047810"]["matched_contamination_spans"] == []
    assert replay["contexts"]["context-01"]["pass_count"] == 4
    assert replay["contexts"]["context-02"]["pass_count"] == 4


def test_m12al_partial_shadow_remains_diagnostic_only() -> None:
    result = runner._m12al_partial_diagnostics()

    assert result["status"] == "INCOMPLETE_DIAGNOSTIC_ONLY"
    assert result["ticker_count"] == 8
    assert result["formal_comparison_eligible"] is False


def test_fictional_stage2_reaudit_reuses_all_24_rows_without_calls() -> None:
    result = runner._fictional_stage2_language_reaudit()

    assert result["status"] == "PASS"
    assert result["row_count"] == 24
    assert result["failure_count"] == 0
    assert result["model_calls"] == 0


def test_lexicon_and_semantic_scope_are_bounded() -> None:
    lexicon = runner._lexicon_audit()
    semantic = runner._semantic_hash_audit(
        allowed_successor_paths=(
            Path("app/services/business_delta_evidence_service.py"),
            Path("app/services/directional_financial_context_service.py"),
            Path("app/services/structured_autonomy_alias_service.py"),
            Path("scripts/directional_financial_context_m12.py"),
        )
    )

    assert lexicon["status"] == "PASS"
    assert lexicon["forbidden_lexeme_count"] == 10
    assert lexicon["substring_rule_count_before"] == 10
    assert lexicon["substring_rule_count_after"] == 0
    assert semantic["status"] == "FAIL"
    assert semantic["legacy_model_facing_function_mismatches"] == [
        "_batch_schema",
        "_enriched_contexts",
        "_full_audit",
        "_stage1_audit",
    ]
    assert not {
        "_monolithic_prompt",
        "_stage1_prompt",
        "_views",
    }.intersection(semantic["legacy_model_facing_function_mismatches"])
    assert semantic["model_schema_semantic_change_count"] == 0
    assert semantic["business_delta_semantic_change_count"] == 0
    assert semantic["financial_semantic_change_count"] == 0
    assert semantic["two_stage_semantic_change_count"] == 0
    assert semantic["stage2_language_matcher_change_count"] == 1


def test_new_shadow_runtime_contract_is_fixed() -> None:
    assert runner.MODEL == "gpt-5.6-sol"
    assert runner.EFFORT == "xhigh"
    assert runner.TIMEOUT_SECONDS == 1800
    assert runner.EXPECTED_ACTIVE_COUNT == 22
    assert runner.EXPECTED_CONTEXTS == 6
    assert runner.EXPECTED_MODEL_CALLS == 18
