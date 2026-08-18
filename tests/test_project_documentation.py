import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = (
    ROOT / "docs" / "MASTER_WORKFLOW.md",
    ROOT / "docs" / "PROJECT_HANDOFF.md",
    ROOT / "docs" / "NEXT_SESSION_PROMPT.md",
    ROOT / "docs" / "project-state.json",
    ROOT / "docs" / "architecture" / "AI_ASSISTED_MONITORING.md",
    ROOT / "docs" / "architecture" / "OHLCV_STRUCTURE_ENGINE.md",
    ROOT / "docs" / "architecture" / "MARKET_INTELLIGENCE.md",
    ROOT / "docs" / "architecture" / "NUMERIC_PROVENANCE.md",
    ROOT / "docs" / "architecture" / "MONITORING_STATE_LIFECYCLE.md",
    ROOT / "docs" / "architecture" / "PEER_VALUATION.md",
    ROOT / "docs" / "architecture" / "PEER_SECTOR_VALUATION.md",
    ROOT / "docs" / "architecture" / "NATURAL_LIVE_MESSAGE_HARDENING.md",
    ROOT / "docs" / "architecture" / "KRX_MARKET_BREADTH.md",
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
    assert state["branch"] == "codex/phase-8-3-peer-sector-valuation"
    assert (
        state["experimental_branch"]
        == "codex/phase-8-3-peer-sector-valuation"
    )
    assert (
        state["current_phase"]
        == "phase_8_3_peer_sector_valuation_strong_partial_experimental_validation"
    )
    assert (
        state["last_completed_phase"]
        == "phase_8_3_peer_sector_valuation_experimental_validation"
    )
    assert (
        state["next_default_phase"]
        == "natural_proof_krx_observation_and_peer_provider_capability_review"
    )
    assert state["deployed_code_commit"] == (
        "b3ad1ea82bdbd3fe003831d449b0dcaa7c6a2da2"
    )
    assert state["main_code_commit"] == "e925ee05eabcc1e89c74dfb1ec0d2dabbb01729d"
    assert state["operating_code_commit"] == (
        "e925ee05eabcc1e89c74dfb1ec0d2dabbb01729d"
    )
    assert (
        state["persistent_gaps"]["current_price_rr_packet_numeric_path"]
        == "LIVE_PATH_PASS"
    )
    assert state["persistent_gaps"]["natural_live_validation"] == "PARTIAL"
    assert state["persistent_gaps"]["krx_open_api"] == (
        "APPROVED_HISTORICAL_PASS_UNIVERSE_CLOSED_PUBLICATION_TIMING_UNDER_OBSERVATION_EXPERIMENTAL_NOT_DEPLOYED"
    )
    krx = state["phase_8_2a_1_krx_universe_and_readiness"]
    assert krx["universe_contract"] == "CLOSED"
    assert krx["denominator_before_after"] == [2532, 2532]
    assert krx["readiness_contract"] == "krx-publication-readiness-v1"
    assert krx["current_session_readiness"] == "PARTIAL"
    assert krx["current_session_observation"]["current_snapshot_promotable"] is False
    assert krx["main_merged"] is False
    assert krx["operating_deployed"] is False
    publication = state["phase_8_2a_2_krx_publication_timing"]
    assert publication["telemetry_contract"] == "krx-publication-telemetry-v1"
    assert publication["provider_role_contract"] == "krx-time-slot-provider-role-v1"
    assert publication["current_session_readiness"] == "PARTIAL"
    assert publication["immediate_observation"]["core_endpoint_rows"] == [0, 0, 0, 0]
    assert publication["immediate_observation"]["first_complete_at"] is None
    assert publication["provider_roles"] == {
        "same_day_close_1605": "NOT_YET_PROVEN",
        "next_morning_0805": "NOT_YET_PROVEN",
        "t_plus_1_reconciliation": "NOT_YET_PROVEN",
        "historical": "SUPPORTED",
    }
    assert publication["main_merged"] is False
    assert publication["operating_deployed"] is False
    workflow = state["master_workflow_v3"]
    assert workflow["status"] == "synchronized_and_phase_8_3_validated"
    assert workflow["priority_rule"] == "OPERATING_BLOCKER_BEFORE_NEW_FEATURE"
    assert workflow["development_lane"]["phase"] == "8.3"
    assert workflow["development_lane"]["operating_deployment"] is False
    peer = state["phase_8_3_peer_sector_valuation"]
    assert peer["status"] == "STRONG_PARTIAL"
    assert peer["contract"] == "peer-sector-valuation-v1"
    assert peer["peer_group_version"] == "verified-profile-peers-v2"
    assert peer["assessment_count"] == 20
    assert peer["market_counts"] == {"kr": 7, "us": 13}
    assert peer["user_visible_peer_state_count"] == 0
    assert peer["numeric_provenance"] == "PASS"
    assert peer["main_merged"] is False
    assert peer["operating_deployed"] is False
    assert (
        state["persistent_gaps"]["fallback_price_lifecycle"]
        == "CLOSED_RETROSPECTIVE_AND_OPERATING_CODE_PROMOTED"
    )
    assert state["current_commit"] == "HEAD"
    assert state["current_commit_resolution"] == "git rev-parse HEAD"
    assert state["ai_review_mode"] == "shadow"
    assert state["ai_policy_version"] == "daily-review-v3.10"
    assert state["output_schema_version"] == 4
    assert state["security_identity_version"] == "security-identity-v2"
    assert state["financial_quality_version"] == "financial-quality-taint-v2"
    assert state["ohlcv_structure_version"] == "ohlcv-structure-v2"
    assert state["pilot_version"] == "ai-assisted-pilot-v3"
    assert state["pilot_counts_at_activation"] == {"kr": 0, "us": 0}
    assert state["pilot_current_successful_sessions"] == {"kr": 3, "us": 3}
    assert state["monitoring_state_version"] == "monitoring-state-v1"
    task_state = state["scheduled_task_contract_verification"]
    assert task_state["status"] == "passed"
    assert task_state["expected_target_count"] == 4
    assert task_state["visible_target_count"] == 4
    assert task_state["active_target_count"] == 4
    assert task_state["required_policy_version"] == "daily-review-v3.10"
    assert task_state["times_kst"] == ["08:15", "08:30", "16:15", "16:55"]
    assert task_state["manual_executions_during_promotion"] == 0
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
        ROOT / "docs" / "architecture" / "NUMERIC_PROVENANCE.md",
        ROOT / "docs" / "architecture" / "MONITORING_STATE_LIFECYCLE.md",
        ROOT / "docs" / "architecture" / "PEER_VALUATION.md",
        ROOT / "docs" / "architecture" / "PEER_SECTOR_VALUATION.md",
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
        "docs/architecture/NUMERIC_PROVENANCE.md",
        "docs/architecture/MONITORING_STATE_LIFECYCLE.md",
        "docs/architecture/PEER_VALUATION.md",
        "docs/architecture/PEER_SECTOR_VALUATION.md",
        "docs/operations/AI_ASSISTED_PILOT.md",
        "docs/operations/SCHEDULED_TASK_CONTRACTS.md",
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
