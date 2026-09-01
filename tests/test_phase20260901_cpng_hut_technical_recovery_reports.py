from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "reports"
ARCHITECTURE = ROOT / "docs" / "architecture"


def test_required_technical_recovery_architecture_and_reports_exist() -> None:
    architecture = (
        "OHLCV_COMPLETED_BAR_FINALITY.md",
        "OHLCV_QUOTE_VS_CANDLE_SEMANTICS.md",
        "TECHNICAL_FEATURE_DEPENDENCY_REGISTRY.md",
        "FEATURE_SCOPED_TECHNICAL_VALIDITY.md",
        "OHLCV_SECONDARY_SOURCE_RECOVERY.md",
        "PACKET_OWNED_TECHNICAL_CONTEXT.md",
    )
    reports = (
        "20260901-hut-provider-field-semantics.md",
        "20260901-hut-completed-bar-finality.md",
        "20260901-hut-automatic-recovery.md",
        "20260901-cpng-feature-dependency-map.md",
        "20260901-cpng-feature-scoped-validity.md",
        "20260901-recursive-indicator-dependency-audit.md",
        "20260901-secondary-ohlcv-source-audit.md",
        "20260901-secondary-row-recovery-controls.md",
        "20260901-cpng-hut-technical-context-v2.md",
        "20260901-cpng-hut-run49-replay.md",
        "20260901-current-us-technical-recovery-regression.md",
        "20260901-kr-technical-recovery-regression.md",
        "20260901-technical-recovery-test-sink.md",
        "20260901-technical-recovery-message-quality.md",
        "20260901-technical-recovery-main-merge.md",
        "20260901-technical-recovery-live-guard.md",
        "20260901-technical-recovery-artifact-index.md",
    )

    assert all((ARCHITECTURE / name).is_file() for name in architecture)
    assert all((REPORTS / name).is_file() for name in reports)


def test_technical_recovery_machine_readable_safety_gates() -> None:
    hut = json.loads((REPORTS / "20260901-hut-finality.json").read_text())
    cpng = json.loads((REPORTS / "20260901-cpng-feature-validity.json").read_text())
    secondary = json.loads((REPORTS / "20260901-secondary-recovery.json").read_text())
    readiness = json.loads(
        (REPORTS / "20260901-technical-recovery-readiness.json").read_text()
    )

    assert hut["current_quote_silently_owns_completed_close"] == 0
    assert hut["ticker_specific_patch"] == 0
    assert cpng["aggregate"] == "PARTIAL_SAFE"
    assert cpng["safe_feature_count"] > 0
    assert cpng["blocked_feature_count"] > 0
    assert cpng["invalid_row_dropped_inside_dependency"] == 0
    assert secondary["status"] == "NO_APPROVED_SOURCE"
    assert secondary["unapproved_source_used"] == 0
    assert readiness["run49_counts"]["PARTIAL_SAFE"] == 14
    assert readiness["kr_counts"]["FULL"] == 8
    assert readiness["invalid_feature_numeric_visible_to_v2"] == 0
    assert readiness["full_pytest"] == "2033 PASS"
    assert readiness["test_sink_initial_sent"] == 20
    assert readiness["test_sink_continuation_sent"] == 2
    assert readiness["test_sink_duplicate_count"] == 0
    assert readiness["test_sink_orphan_count"] == 0
