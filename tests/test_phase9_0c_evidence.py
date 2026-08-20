import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = (
    ROOT / "docs" / "reports" / "20260820-phase9-0c-shadow-context.json"
)


def _evidence() -> dict:
    return json.loads(EVIDENCE.read_text())


def test_phase9_0c_archive_evidence_closes_shadow_contract() -> None:
    evidence = _evidence()

    assert evidence["contract"] == "cash-flow-shadow-consumption-v1"
    assert evidence["counts"] == {
        "capex_consumed": 9,
        "consumption_eligible": 12,
        "contexts_with_comparison": 9,
        "fcf_consumed": 9,
        "freshness": {
            "BLOCKED": 7,
            "CURRENT_FORMAL": 10,
            "FORMAL_ALIGNMENT_UNAVAILABLE": 0,
            "FORMAL_LAGGING_PROVISIONAL": 2,
            "NOT_APPLICABLE": 1,
            "STALE_FORMAL": 0,
        },
        "ocf_consumed": 10,
        "safe_comparisons": 25,
        "shadow_used": 10,
        "subjects": 20,
        "suppressed_comparisons": 11,
        "usage_modes": {"FULL_FCF_CONTEXT": 9, "OCF_ONLY_CONTEXT": 1},
    }
    assert evidence["human_quality"]["DEGRADED"] == 0
    assert evidence["point_in_time"]["future_fact_violations"] == 0
    assert evidence["semantic_validation"]["error_count"] == 0
    assert evidence["numeric_binding"]["automatic"] == 10
    assert evidence["numeric_binding"]["manual"] == 0
    assert evidence["numeric_binding"]["rejected"] == 0
    assert evidence["numeric_binding"]["unresolved"] == 0
    assert set(evidence["mutations"].values()) == {0}


def test_phase9_0c_quality_and_negative_controls_pass() -> None:
    evidence = _evidence()

    for name in ("run28_before", "run28_after", "run29_after"):
        result = evidence["quality"][name]
        assert result["hard_checks_passed"] is True
        assert result["final_language_passed"] is True
        assert result["substantive_repeated_sentence_count"] == 0
        assert result["template_skeleton_repeat_count"] == 0
    assert evidence["quality"]["run28_receipt_status"] == "passed"
    assert evidence["quality"]["run29_receipt_status"] == "passed"
    assert set(evidence["negative_controls"].values()) == {0}
    assert evidence["unknown_resolution"] == {
        "before": 17,
        "resolved": 8,
        "still_valid": 8,
        "suppressed_not_applicable": 1,
    }
    assert ".;" not in json.dumps(
        evidence["run28_shadow_candidate"], ensure_ascii=False
    )


def test_phase9_0c_selective_boundaries_remain_fail_closed() -> None:
    evidence = _evidence()
    audits = {row["ticker"]: row for row in evidence["ticker_audit"]}

    assert len(audits) == 20
    assert audits["HUT"]["context"]["usage_mode"] == "OCF_ONLY_CONTEXT"
    for ticker in ("TSM", "WRD"):
        context = audits[ticker]["context"]
        assert context["usage_mode"] == "LATEST_FORMAL_CONTEXT_ONLY"
        assert context["shadow_used"] is False
        assert context["freshness_state"] == "FORMAL_LAGGING_PROVISIONAL"
    korean_re = audits["003690"]["context"]
    assert korean_re["usage_mode"] == "NOT_APPLICABLE"
    assert korean_re["shadow_used"] is False
    for ticker in ("000660", "005930", "005490", "010120", "012450", "086280"):
        assert audits[ticker]["context"]["freshness_state"] == "BLOCKED"
        assert audits[ticker]["shadow_reasoning"] is None


def test_phase9_0c_readiness_is_explicit_without_user_exposure() -> None:
    evidence = _evidence()
    readiness = evidence["readiness"]

    assert readiness["p0_open"] == []
    assert readiness["p1_open"] == []
    assert readiness["phase_9_0d_ready"] is True
    assert readiness["phase_9_0d_scope"] == (
        "SELECTIVE_CASH_FLOW_RUNTIME_SHADOW_CANARY"
    )
    assert readiness["cash_flow_user_visible"] is False
    assert readiness["production_assist"] is False
