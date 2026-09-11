from __future__ import annotations

from scripts import integrated_main_monitored_shadow_failure_closeout_m12af as closeout
from scripts import integrated_main_monitored_shadow_diagnostic_m12af as m12af


def test_fictional_decision_instability_does_not_block_diagnostic_gate() -> None:
    assert (
        m12af.diagnostic_gate_status(
            architecture_integrity=True,
            objective_semantic_failure_count=0,
            core_mutation_count=0,
            active_universe_resolved=True,
            packet_available_count=22,
            paused_schedule_count=4,
            runner_target_matches=True,
        )
        == "PASS"
    )


def test_objective_semantic_failure_blocks_diagnostic_gate() -> None:
    assert (
        m12af.diagnostic_gate_status(
            architecture_integrity=True,
            objective_semantic_failure_count=1,
            core_mutation_count=0,
            active_universe_resolved=True,
            packet_available_count=22,
            paused_schedule_count=4,
            runner_target_matches=True,
        )
        == "FAIL"
    )


def test_core_mutation_blocks_diagnostic_gate() -> None:
    assert (
        m12af.diagnostic_gate_status(
            architecture_integrity=True,
            objective_semantic_failure_count=0,
            core_mutation_count=1,
            active_universe_resolved=True,
            packet_available_count=22,
            paused_schedule_count=4,
            runner_target_matches=True,
        )
        == "FAIL"
    )


def test_runner_target_or_schedule_mismatch_blocks_gate() -> None:
    assert (
        m12af.diagnostic_gate_status(
            architecture_integrity=True,
            objective_semantic_failure_count=0,
            core_mutation_count=0,
            active_universe_resolved=True,
            packet_available_count=22,
            paused_schedule_count=3,
            runner_target_matches=False,
        )
        == "FAIL"
    )


def test_frozen_prompt_schema_and_service_hashes_reproduce() -> None:
    assert m12af._architecture_hashes_match(m12af._architecture_hashes())


def test_batching_is_dynamic_and_capped_at_four() -> None:
    batches = m12af._batches(tuple(f"T{index}" for index in range(22)))
    assert len(batches) == 6
    assert all(1 <= len(batch) <= 4 for batch in batches)
    assert sum(map(len, batches)) == 22


def test_review_resolution_sets_are_frozen() -> None:
    assert m12af.REVIEW_RESOLUTIONS == {
        "EXPECTED_CONTRACT_CORRECTION",
        "POTENTIAL_ARCHITECTURE_REGRESSION",
        "OTHER_REVIEW_REQUIRED",
    }
    assert "TWO_STAGE_COMPATIBILITY_HAS_BOUNDED_REGRESSIONS" in (
        m12af.ARCHITECTURE_CLASSIFICATIONS
    )


def test_fresh_real_and_production_are_not_next_scope_options() -> None:
    assert all("FRESH_REAL" not in scope for scope in m12af.NEXT_SCOPES)
    assert all("PRODUCTION" not in scope for scope in m12af.NEXT_SCOPES)


def test_failure_closeout_keeps_partial_rows_distinct_from_comparisons() -> None:
    rows = closeout._partial_rows(
        {
            "rows": [
                {
                    "ticker": "TEST",
                    "status": "FAIL",
                    "errors": ["OBJECTIVE_ERROR"],
                    "core": {
                        "overall_direction": "HOLD",
                        "business_thesis_change": "UNCHANGED",
                        "fundamental_new_buyer": {"stance": "WAIT"},
                        "fundamental_holder": {"stance": "HOLDABLE"},
                    },
                    "business_delta": {"status": "PASS"},
                    "financial_semantics": {"valid": False},
                }
            ]
        }
    )

    assert rows == [
        {
            "ticker": "TEST",
            "status": "FAIL",
            "errors": ["OBJECTIVE_ERROR"],
            "overall_direction": "HOLD",
            "business_thesis_change": "UNCHANGED",
            "new_buyer_stance": "WAIT",
            "holder_stance": "HOLDABLE",
            "business_delta": {"status": "PASS"},
            "financial_semantics": {"valid": False},
        }
    ]
