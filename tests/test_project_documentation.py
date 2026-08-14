import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = (
    ROOT / "docs" / "PROJECT_HANDOFF.md",
    ROOT / "docs" / "NEXT_SESSION_PROMPT.md",
    ROOT / "docs" / "project-state.json",
    ROOT / "docs" / "architecture" / "AI_ASSISTED_MONITORING.md",
    ROOT / "docs" / "architecture" / "OHLCV_STRUCTURE_ENGINE.md",
    ROOT / "docs" / "architecture" / "MARKET_INTELLIGENCE.md",
    ROOT / "docs" / "architecture" / "MONITORING_STATE_LIFECYCLE.md",
    ROOT / "docs" / "architecture" / "PEER_VALUATION.md",
    ROOT / "docs" / "operations" / "AI_ASSISTED_PILOT.md",
    ROOT / "docs" / "knowledge" / "README.md",
)
INVESTMENT_SHA = "559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18"
CHART_SHA = "beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_persistent_handoff_artifacts_and_state_are_current() -> None:
    assert all(path.exists() for path in DOCUMENTS)
    state = json.loads((ROOT / "docs" / "project-state.json").read_text())

    assert state["repository"] == "sskim-ai/thesis-monitor"
    assert state["branch"] == "main"
    assert state["current_commit"] == "HEAD"
    assert state["current_commit_resolution"] == "git rev-parse HEAD"
    assert state["ai_review_mode"] == "shadow"
    assert state["ai_policy_version"] == "daily-review-v3.8"
    assert state["output_schema_version"] == 4
    assert state["ohlcv_structure_version"] == "ohlcv-structure-v2"
    assert state["pilot_version"] == "ai-assisted-pilot-v3"
    assert state["pilot_counts_at_activation"] == {"kr": 0, "us": 0}
    assert state["pilot_current_successful_sessions"] == {"kr": 1, "us": 0}
    assert state["monitoring_state_version"] == "monitoring-state-v1"
    assert state["single_delivery"] is True
    assert state["deterministic_fallback"] is True
    assert state["production_assist"] is False
    assert state["public_action_version"] == "0.4.5"
    assert state["public_action_operation_ids"] == "20/20"


def test_knowledge_checksums_and_runtime_parity_are_documented() -> None:
    investment_paths = (
        ROOT / "docs" / "knowledge" / "investment-thesis-analysis-monitoring-knowledge-v3.md",
        ROOT
        / ".agents"
        / "skills"
        / "thesis-monitor-daily-review"
        / "references"
        / "investment-thesis-analysis-monitoring-knowledge.md",
        ROOT / "docs" / "custom_gpt_knowledge_ko.md",
    )
    chart_paths = (
        ROOT / "docs" / "knowledge" / "stock-chart-value-analysis-knowledge-v1.md",
        ROOT
        / ".agents"
        / "skills"
        / "thesis-monitor-daily-review"
        / "references"
        / "stock-chart-value-analysis-knowledge-v1.md",
    )

    assert {_sha256(path) for path in investment_paths} == {INVESTMENT_SHA}
    assert {_sha256(path) for path in chart_paths} == {CHART_SHA}
    state = (ROOT / "docs" / "project-state.json").read_text()
    guide = (ROOT / "docs" / "knowledge" / "README.md").read_text()
    assert INVESTMENT_SHA in state and INVESTMENT_SHA in guide
    assert CHART_SHA in state and CHART_SHA in guide


def test_architecture_guides_record_decisions_and_readme_navigation() -> None:
    decision_docs = (
        ROOT / "docs" / "architecture" / "AI_ASSISTED_MONITORING.md",
        ROOT / "docs" / "architecture" / "OHLCV_STRUCTURE_ENGINE.md",
        ROOT / "docs" / "architecture" / "MARKET_INTELLIGENCE.md",
        ROOT / "docs" / "architecture" / "MONITORING_STATE_LIFECYCLE.md",
        ROOT / "docs" / "architecture" / "PEER_VALUATION.md",
        ROOT / "docs" / "operations" / "AI_ASSISTED_PILOT.md",
        ROOT / "docs" / "knowledge" / "README.md",
    )
    for path in decision_docs:
        text = path.read_text()
        assert "## Problem" in text
        assert "## Decision" in text
        assert "## Why" in text
        assert "## Rejected Alternative" in text
        assert "## Safety Constraint" in text

    readme = (ROOT / "README.md").read_text()
    for relative in (
        "docs/PROJECT_HANDOFF.md",
        "docs/architecture/AI_ASSISTED_MONITORING.md",
        "docs/architecture/OHLCV_STRUCTURE_ENGINE.md",
        "docs/architecture/MARKET_INTELLIGENCE.md",
        "docs/architecture/MONITORING_STATE_LIFECYCLE.md",
        "docs/architecture/PEER_VALUATION.md",
        "docs/operations/AI_ASSISTED_PILOT.md",
        "docs/knowledge/README.md",
        "docs/NEXT_SESSION_PROMPT.md",
        "docs/project-state.json",
    ):
        assert relative in readme


def test_documentation_relative_links_resolve_and_contains_no_secrets() -> None:
    markdown_paths = [path for path in DOCUMENTS if path.suffix == ".md"]
    markdown_paths.extend([ROOT / "README.md", ROOT / "docs" / "ai_review_project_handoff.md"])
    secret_assignment = re.compile(
        r"(?i)(?:api[_-]?key|token|secret|password|chat[_-]?id)"
        r"[ \t]*[:=][ \t]*['\"]?[A-Za-z0-9_\-]{12,}"
    )

    for path in markdown_paths:
        text = path.read_text()
        assert "/Users/" not in text
        assert "/home/" not in text
        assert secret_assignment.search(text) is None
        for raw_target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            target = raw_target.split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            assert (path.parent / target).resolve().exists(), (path, target)
