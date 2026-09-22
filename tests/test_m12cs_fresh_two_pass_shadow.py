from __future__ import annotations

from scripts.m12cs_fresh_two_pass_shadow import (
    _classify_m12cs_failure,
    _contract_key,
    _test_count,
    _validation_rule_ids,
    compare_frozen_draft_hashes,
    pass_a_output_leak_scan,
)


def _row(*, prompt: str = "p", schema: str = "s", context: str = "c") -> dict[str, object]:
    return {
        "stage": "pass-a",
        "market": "us",
        "batch": 1,
        "subjects": ["AAA"],
        "prompt_sha256": prompt,
        "schema_sha256": schema,
        "context_sha256": context,
        "scan": {"status": "PASS"},
        "status": "PASS",
    }


def test_contract_key_is_stage_market_batch() -> None:
    assert _contract_key(_row()) == ("pass-a", "us", 1)


def test_frozen_draft_hash_comparison_requires_sixteen_rows() -> None:
    result = compare_frozen_draft_hashes({"rows": [_row()]}, {"rows": [_row()]})
    assert result["actual_count"] == 1
    assert result["mismatch_count"] == 0
    assert result["status"] == "FAIL"


def test_frozen_draft_hash_comparison_detects_each_hash_class() -> None:
    result = compare_frozen_draft_hashes(
        {"rows": [_row(prompt="actual")]},
        {"rows": [_row(prompt="expected")]},
    )
    assert result["rows"][0]["hash_matches"] == {
        "schema_sha256": True,
        "prompt_sha256": False,
        "context_sha256": True,
    }
    assert result["mismatch_count"] == 1


def test_pass_a_output_leak_scan_accepts_business_only_text() -> None:
    result = pass_a_output_leak_scan(
        {
            "classifications": {
                "AAA": {"archetype_rationale": "사업 경쟁력과 현금창출 구조를 근거로 분류합니다."}
            }
        }
    )
    assert result["status"] == "PASS"
    assert result["hit_count"] == 0


def test_pass_a_output_leak_scan_rejects_price_and_tactical_language() -> None:
    result = pass_a_output_leak_scan(
        {
            "classifications": {
                "AAA": {"archetype_rationale": "현재가와 기술적 진입가를 함께 봅니다."}
            }
        }
    )
    assert result["status"] == "FAIL"
    assert {row["token"] for row in result["hits"]} >= {"현재가", "기술적", "진입가"}


def test_test_count_reads_passed_and_skipped() -> None:
    assert _test_count("4378 passed, 63 skipped in 1.0s") == (4378, 63)


def test_test_count_handles_missing_counts() -> None:
    assert _test_count("collection failed") == (0, 0)


def test_pass_b_raw_semantic_failure_has_stable_category() -> None:
    category = _classify_m12cs_failure(
        RuntimeError("pass_b_raw_semantic_validation_failed"),
        None,
        execution_stage="PASS_B_RAW_SEMANTIC_VALIDATION",
    )

    assert category == "PASS_B_RAW_SEMANTIC_VALIDATION_FAILED"


def test_pass_b_materialized_failure_has_stable_category() -> None:
    category = _classify_m12cs_failure(
        RuntimeError("pass_b_final_semantic_validation_failed"),
        None,
        execution_stage="PASS_B_FINAL_SEMANTIC_VALIDATION",
    )

    assert category == "PASS_B_FINAL_SEMANTIC_VALIDATION_FAILED"


def test_validation_rule_ids_preserve_primary_semantic_cause() -> None:
    assert _validation_rule_ids(
        {
            "errors": [
                "CORZ:PB_BALANCE_SUM",
                "CPNG:PB_BALANCE_SUM",
                "CRCL:PB_BALANCE_SUM",
            ]
        }
    ) == ["PB_BALANCE_SUM"]
