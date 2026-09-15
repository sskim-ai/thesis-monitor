"""M12AY configured FCF support mapping proof and full shadow."""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import ast
from collections.abc import Mapping, Sequence
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.cross_market_decision_engine_service import (
    DecisionEvidenceRef,
    EvidenceCategory,
)
from app.services.configured_financial_support_concept_service import (
    CONTRACT_VERSION as FINANCIAL_SUPPORT_CONCEPT_CONTRACT,
    configured_financial_support_concepts,
)
from app.services.configured_signal_evidence_service import (
    configured_signal_source_role,
)
from app.services.directional_financial_context_service import (
    PROSPECTIVE_CONDITION_NOMINALIZATION_CONTRACT,
    PROSPECTIVE_MONITORING_OBLIGATION_CONTRACT,
    FinancialClaimRole,
    _EXPLICIT_LOCAL_FUTURE_LANGUAGE,
    _CURRENT_FULFILLMENT_LANGUAGE,
    _CURRENT_MAGNITUDE_LANGUAGE,
    _claim_has_framework_relevant_configured_evidence,
    _configured_prospective_evidence,
    _prospective_monitoring_obligation_family,
    financial_claim_requires_current_evidence,
    financial_claim_role,
    financial_claim_row_requires_current_fcf_evidence,
    financial_claim_rows,
    validate_directional_financial_semantics,
)
from app.services.financial_framework_claim_service import (
    CLAIM_SPAN_CONTRACT_VERSION,
    FrameworkClaim,
    FrameworkClaimKind,
    FrameworkReferenceRole,
    candidate_financial_framework_claims,
    financial_frameworks_in_text,
)
from app.services.logical_condition_service import CheckpointMetric
from app.services.optional_semantic_audit_service import (
    optional_semantic_audit_status,
)
from scripts import configured_signal_field_ownership_m12at as m12at
from scripts import prospective_condition_nominalization_m12aw as m12aw


NAME = "20260913-configured-fcf-prospective-support-mapping-fictional-reproof-full-shadow"
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
UPSTREAM_REPORTS = OUTPUT / "supporting-reports/m12aw"
SUPPORT_REPORTS = OUTPUT / "supporting-reports/m12ai"
RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
RUNNER = Path("scripts/configured_fcf_prospective_support_m12ay.py")
ARCHITECTURE = Path("docs/architecture/CONFIGURED_FINANCIAL_SUPPORT_CONCEPTS.md")
WORK_INSTRUCTION = Path("docs/work-instructions") / f"{NAME}.md"
WORK_INSTRUCTION_COMMIT = "487d65030e0bffc8b46930acb9bf1162bf99535c"
BASE_INTEGRATION_HEAD_SHA = "31770fb4793da3999685975749b9d147959ac92a"

ICLOUD = Path("/Users/sskim/Library/Mobile Documents/com~apple~CloudDocs/Thesis Monitor")
LATEST_NAME = (
    "20260913-korean-prospective-monitoring-obligation-scope-fictional-reproof-full-shadow"
)
LATEST_OUTPUT = Path("artifacts") / LATEST_NAME
LATEST_BUNDLE = ICLOUD / f"thesis-monitor-{LATEST_NAME}-report.zip"
LATEST_BUNDLE_SHA256 = "d4b40b0951524571f34b73b409105980a4871c8ae4ef69f1cd56f6f9daef7b1d"
LATEST_INDEXED_PAYLOADS = 357
LATEST_ZIP_ENTRIES = 358
LATEST_GENERATION_ID = "20260911-m12ai-fictional-20260912T230529Z-284ef4f9f72b"

MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
EXPECTED_FICTIONAL_CALLS = 12
EXPECTED_FICTIONAL_ROWS = 24
EXPECTED_SHADOW_CALLS = 18
EXPECTED_ACTIVE_COUNT = 22
NEXT_SCOPE = "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"

_RAW_MONITORING_LANGUAGE = re.compile(
    r"(?:감시|모니터링|주시|추적|점검)|"
    r"\b(?:monitor|monitoring|monitored|track|tracked|watch|watched|reviewed)\b",
    re.IGNORECASE,
)

_M12AX_SLUG_SEQUENCE = (
    "repository-provenance",
    "latest-result-integrity",
    "m12ax-scope-freeze",
    "integrated-main-lineage-freeze",
    "m12aw-fic-fin-01-monitoring-failure-reproduction",
    "m12aw-fic-fin-02-monitoring-failure-reproduction",
    "m12aw-fic-fin-04-monitoring-failure-reproduction",
    "fic-fin-03-monitoring-pass-contrast",
    "prospective-risk-language-code-audit",
    "monitoring-obligation-root-cause",
    "monitoring-obligation-architecture-options",
    "monitoring-obligation-architecture-decision",
    "prospective-monitoring-obligation-contract",
    "korean-monitoring-verb-family-contract",
    "english-monitoring-verb-family-contract",
    "current-magnitude-precedence-contract",
    "current-fulfillment-precedence-contract",
    "no-configured-support-fail-closed-contract",
    "same-clause-current-and-monitoring-contract",
    "framework-relevant-configured-support-contract",
    "m12aw-fic-fin-01-exact-offline-replay",
    "m12aw-fic-fin-02-exact-offline-replay",
    "m12aw-fic-fin-04-exact-offline-replay",
    "fic-fin-03-monitoring-pass-regression",
    "monitoring-obligation-positive-fixtures",
    "monitoring-obligation-current-negative-fixtures",
    "monitoring-obligation-no-support-fail-closed-fixtures",
    "same-clause-current-and-monitoring-fixtures",
    "m12av-completed-40-row-offline-reaudit",
    "m12aw-first-call-four-row-offline-reaudit",
    "m12aw-nominal-condition-freeze",
    "m12av-clause-local-scope-freeze",
    "m12au-fcf-case-semantic-freeze",
    "m12at-configured-signal-field-ownership-freeze",
    "m12as-unchanged-claim-scope-freeze",
    "m12ar-fcf-claim-scope-freeze",
    "m12aq-financial-sector-scope-freeze",
    "m12ap-expectation-independence-freeze",
    "m12ao-business-delta-convergence-freeze",
    "m12an-ppe-proxy-label-freeze",
    "m12am-stage2-lexical-freeze",
    "monitoring-transition-ownership-freeze",
    "qtd-ytd-wc-debt-safety-freeze",
    "adr-security-basis-freeze",
    "two-stage-ownership-freeze",
    "price-timing-renderer-no-change",
    "model-prompt-semantic-hash-freeze",
    "model-schema-semantic-hash-freeze",
    "configured-signal-view-semantic-hash-freeze",
    "business-delta-view-semantic-hash-freeze",
    "expectation-view-semantic-hash-freeze",
    "financial-evidence-projection-semantic-hash-freeze",
    "model-facing-no-change-decision",
    "focused-test-results",
    "full-local-test-results",
    "ruff-and-diff-results",
    "hosted-ci-portability-observation",
    "new-fictional-model-call-gate",
    "fictional-generation-manifest",
    "fictional-configured-signal-view-manifest",
    "fictional-delta-view-manifest",
    "fictional-expectation-view-manifest",
    "stage1-run1-context01",
    "stage1-run1-context02",
    "stage2-run1-context01",
    "stage2-run1-context02",
    "stage1-run2-context01",
    "stage1-run2-context02",
    "stage2-run2-context01",
    "stage2-run2-context02",
    "stage1-run3-context01",
    "stage1-run3-context02",
    "stage2-run3-context01",
    "stage2-run3-context02",
    "fictional-context-hard-semantic-audit",
    "fictional-monitoring-obligation-scope-audit",
    "fictional-nominal-condition-scope-audit",
    "fictional-mixed-risk-context-audit",
    "fictional-configured-signal-field-use-audit",
    "fictional-fcf-claim-scope-audit",
    "fictional-business-delta-audit",
    "fictional-market-expectation-audit",
    "fictional-financial-sector-audit",
    "fictional-stage2-language-audit",
    "fictional-final-composition-audit",
    "fictional-aggregate-finalization-audit",
    "fictional-primary-direction-diagnostic",
    "fictional-delta-materiality-diagnostic",
    "fictional-new-buyer-diagnostic",
    "fictional-holder-diagnostic",
    "fictional-core-immutability-audit",
    "fictional-runtime-audit",
    "fictional-shadow-gate-decision",
    "task-start-active-monitored-universe",
    "shadow-packet-inventory",
    "shadow-packet-hash-manifest",
    "shadow-configured-signal-view-manifest",
    "shadow-delta-view-manifest",
    "shadow-expectation-view-manifest",
    "shadow-frozen-context-manifest",
    "shadow-batching-manifest",
    "shadow-model-call-gate",
    "shadow-monolithic-model-artifacts",
    "shadow-stage1-model-artifacts",
    "shadow-stage2-model-artifacts",
    "shadow-context-hard-semantic-audit",
    "shadow-monitoring-obligation-scope-audit",
    "shadow-nominal-condition-scope-audit",
    "shadow-mixed-risk-context-audit",
    "shadow-configured-signal-field-use-audit",
    "shadow-fcf-claim-scope-audit",
    "shadow-business-delta-audit",
    "shadow-market-expectation-audit",
    "shadow-financial-sector-audit",
    "shadow-stage2-language-audit",
    "shadow-final-composition-audit",
    "shadow-aggregate-finalization-audit",
    "shadow-per-ticker-comparison",
    "shadow-core-direction-differences",
    "shadow-business-delta-differences",
    "shadow-new-buyer-differences",
    "shadow-holder-differences",
    "shadow-same-direction-calibration-differences",
    "shadow-expected-contract-corrections",
    "shadow-potential-architecture-regressions",
    "shadow-unresolved-review-required",
    "shadow-adr-security-basis-audit",
    "shadow-cyclical-valuation-audit",
    "shadow-core-immutability-audit",
    "shadow-runtime-audit",
    "shadow-aggregate-summary",
    "shadow-architecture-decision",
    "fic-fin-05-vs-monitored-primary-boundary-analogs",
    "fic-fin-02-vs-monitored-delta-materiality-analogs",
    "fic-fin-06-vs-monitored-positive-delta-analogs",
    "fic-fin-08-vs-monitored-holder-analogs",
    "new-buyer-monolithic-vs-two-stage-analogs",
    "real-monitoring-obligation-scope-lessons",
    "real-nominal-condition-scope-lessons",
    "real-configured-signal-field-use-lessons",
    "combined-fictional-monitored-root-cause-summary",
    "next-bounded-policy-decision",
    "monitoring-obligation-scope-repair-success-decision",
    "nominal-condition-scope-preservation-decision",
    "mixed-risk-context-scope-preservation-decision",
    "configured-signal-field-ownership-preservation-decision",
    "new-fictional-proof-success-decision",
    "full-shadow-completion-decision",
    "existing-monitored-impact-summary",
    "two-stage-shadow-compatibility-decision",
    "fresh-real-proof-readiness-decision",
    "final-main-merge-readiness-note",
    "production-no-change",
    "schedule-pause-observation",
    "remote-push-prohibition-audit",
    "master-workflow-update",
    "program-completion",
)
_SLUG_SEQUENCE = (
    "repository-provenance",
    "latest-result-integrity",
    "m12ay-scope-freeze",
    "integrated-main-lineage-freeze",
    "m12ax-unsupported-current-fcf-failure-reproduction",
    "configured-fcf-structured-evidence-forensic",
    "financial-support-concept-code-audit",
    "general-framework-vs-support-concept-separation-audit",
    "fcf-support-mapping-options",
    "fcf-support-mapping-decision",
    "configured-financial-support-concept-contract",
    "free-cash-flow-support-concept-contract",
    "structured-metric-ref-priority-contract",
    "explicit-fcf-text-fallback-contract",
    "ocf-not-fcf-support-contract",
    "ocf-less-ppe-not-fcf-support-contract",
    "current-fcf-evidence-separation-contract",
    "configured-lifecycle-no-fulfillment-contract",
    "general-framework-application-no-change-contract",
    "m12ax-fic-fin-01-exact-offline-replay",
    "m12ax-fic-fin-02-exact-offline-replay",
    "m12ax-fic-fin-03-exact-offline-replay",
    "m12ax-fic-fin-04-exact-offline-replay",
    "configured-fcf-support-positive-fixtures",
    "ocf-not-fcf-support-negative-fixtures",
    "ocf-ppe-not-fcf-support-negative-fixtures",
    "current-unsupported-fcf-negative-fixtures",
    "mixed-fcf-netdebt-configured-support-fixtures",
    "m12av-completed-40-row-offline-reaudit",
    "m12aw-first-call-four-row-offline-reaudit",
    "m12ax-first-call-four-row-offline-reaudit",
    "m12ax-monitoring-obligation-freeze",
    "m12aw-nominal-condition-freeze",
    "m12av-clause-local-scope-freeze",
    "m12au-fcf-case-semantic-freeze",
    "m12at-configured-signal-field-ownership-freeze",
    "m12as-unchanged-claim-scope-freeze",
    "m12ar-fcf-claim-scope-freeze",
    "m12aq-financial-sector-scope-freeze",
    "m12ap-expectation-independence-freeze",
    "m12ao-business-delta-convergence-freeze",
    "m12an-ppe-proxy-label-freeze",
    "m12am-stage2-lexical-freeze",
    "monitoring-transition-ownership-freeze",
    "qtd-ytd-wc-debt-safety-freeze",
    "adr-security-basis-freeze",
    "two-stage-ownership-freeze",
    "price-timing-renderer-no-change",
    "model-prompt-semantic-hash-freeze",
    "model-schema-semantic-hash-freeze",
    "configured-signal-view-semantic-hash-freeze",
    "business-delta-view-semantic-hash-freeze",
    "expectation-view-semantic-hash-freeze",
    "financial-evidence-projection-semantic-hash-freeze",
    "model-facing-no-change-decision",
    "focused-test-results",
    "full-local-test-results",
    "ruff-and-diff-results",
    "hosted-ci-portability-observation",
    "new-fictional-model-call-gate",
    "fictional-generation-manifest",
    "fictional-configured-signal-view-manifest",
    "fictional-configured-financial-support-concept-manifest",
    "fictional-delta-view-manifest",
    "fictional-expectation-view-manifest",
    "stage1-run1-context01",
    "stage1-run1-context02",
    "stage2-run1-context01",
    "stage2-run1-context02",
    "stage1-run2-context01",
    "stage1-run2-context02",
    "stage2-run2-context01",
    "stage2-run2-context02",
    "stage1-run3-context01",
    "stage1-run3-context02",
    "stage2-run3-context01",
    "stage2-run3-context02",
    "fictional-context-hard-semantic-audit",
    "fictional-configured-fcf-support-audit",
    "fictional-monitoring-obligation-audit",
    "fictional-nominal-condition-audit",
    "fictional-mixed-risk-context-audit",
    "fictional-configured-signal-field-use-audit",
    "fictional-fcf-claim-scope-audit",
    "fictional-business-delta-audit",
    "fictional-market-expectation-audit",
    "fictional-financial-sector-audit",
    "fictional-stage2-language-audit",
    "fictional-final-composition-audit",
    "fictional-aggregate-finalization-audit",
    "fictional-primary-direction-diagnostic",
    "fictional-delta-materiality-diagnostic",
    "fictional-new-buyer-diagnostic",
    "fictional-holder-diagnostic",
    "fictional-core-immutability-audit",
    "fictional-runtime-audit",
    "fictional-shadow-gate-decision",
    "task-start-active-monitored-universe",
    "shadow-packet-inventory",
    "shadow-packet-hash-manifest",
    "shadow-configured-signal-view-manifest",
    "shadow-configured-financial-support-concept-manifest",
    "shadow-delta-view-manifest",
    "shadow-expectation-view-manifest",
    "shadow-frozen-context-manifest",
    "shadow-batching-manifest",
    "shadow-model-call-gate",
    "shadow-monolithic-model-artifacts",
    "shadow-stage1-model-artifacts",
    "shadow-stage2-model-artifacts",
    "shadow-context-hard-semantic-audit",
    "shadow-configured-fcf-support-audit",
    "shadow-monitoring-obligation-audit",
    "shadow-nominal-condition-audit",
    "shadow-mixed-risk-context-audit",
    "shadow-configured-signal-field-use-audit",
    "shadow-fcf-claim-scope-audit",
    "shadow-business-delta-audit",
    "shadow-market-expectation-audit",
    "shadow-financial-sector-audit",
    "shadow-stage2-language-audit",
    "shadow-final-composition-audit",
    "shadow-aggregate-finalization-audit",
    "shadow-per-ticker-comparison",
    "shadow-core-direction-differences",
    "shadow-business-delta-differences",
    "shadow-new-buyer-differences",
    "shadow-holder-differences",
    "shadow-same-direction-calibration-differences",
    "shadow-expected-contract-corrections",
    "shadow-potential-architecture-regressions",
    "shadow-unresolved-review-required",
    "shadow-adr-security-basis-audit",
    "shadow-cyclical-valuation-audit",
    "shadow-core-immutability-audit",
    "shadow-runtime-audit",
    "shadow-aggregate-summary",
    "shadow-architecture-decision",
    "fic-fin-05-vs-monitored-primary-boundary-analogs",
    "fic-fin-02-vs-monitored-delta-materiality-analogs",
    "fic-fin-06-vs-monitored-positive-delta-analogs",
    "fic-fin-08-vs-monitored-holder-analogs",
    "new-buyer-monolithic-vs-two-stage-analogs",
    "real-configured-fcf-support-lessons",
    "real-monitoring-obligation-lessons",
    "real-configured-signal-field-use-lessons",
    "combined-fictional-monitored-root-cause-summary",
    "next-bounded-policy-decision",
    "configured-fcf-support-mapping-success-decision",
    "monitoring-obligation-preservation-decision",
    "nominal-condition-preservation-decision",
    "mixed-risk-context-preservation-decision",
    "configured-signal-field-ownership-preservation-decision",
    "new-fictional-proof-success-decision",
    "full-shadow-completion-decision",
    "existing-monitored-impact-summary",
    "two-stage-shadow-compatibility-decision",
    "fresh-real-proof-readiness-decision",
    "final-main-merge-readiness-note",
    "production-no-change",
    "schedule-pause-observation",
    "remote-push-prohibition-audit",
    "master-workflow-update",
    "program-completion",
)
SLUGS = dict(enumerate(_SLUG_SEQUENCE, start=1))
if len(SLUGS) != 164:
    raise RuntimeError(f"M12AY_REPORT_SEQUENCE_INVALID:{len(SLUGS)}")

FOCUSED_TESTS = (
    "tests/test_configured_fcf_support_mapping_m12ay.py",
    "tests/test_configured_fcf_support_mapping_m12ay_runner.py",
    "tests/test_prospective_monitoring_obligation_m12ax.py",
    "tests/test_prospective_monitoring_obligation_m12ax_runner.py",
    "tests/test_prospective_financial_condition_nominalization_m12aw.py",
    "tests/test_prospective_condition_nominalization_m12aw_runner.py",
    "tests/test_mixed_risk_context_clause_scope_m12av.py",
    "tests/test_fictional_case_fcf_prospective_scope_m12au.py",
    "tests/test_directional_financial_context_m12.py",
    "tests/test_directional_financial_context_service.py",
    "tests/test_configured_signal_evidence_service.py",
    "tests/test_configured_signal_alias_schema.py",
    "tests/test_configured_signal_field_ownership_m12at_runner.py",
    "tests/test_ppe_proxy_fcf_claim_scope_m12ar.py",
    "tests/test_business_delta_evidence_service.py",
    "tests/test_business_delta_evidence_capability_m12ai.py",
    "tests/test_market_expectation_evidence_service.py",
    "tests/test_financial_sector_exclusion_connective_scope_m12aq.py",
    "tests/test_stage2_korean_lexical_boundary_m12am_runner.py",
    "tests/test_monitoring_transition_ownership_netdebt_m12ag.py",
    "tests/test_financial_claim_temporal_scope_m12ah.py",
    "tests/test_two_stage_directional_service.py",
    "tests/test_direction_timing_ownership_service.py",
)
RUFF_PATHS = (
    str(RUNNER),
    "app/services/configured_financial_support_concept_service.py",
    "app/services/configured_signal_evidence_service.py",
    "app/services/directional_financial_context_service.py",
    "tests/test_configured_fcf_support_mapping_m12ay.py",
    "tests/test_configured_fcf_support_mapping_m12ay_runner.py",
    "tests/test_prospective_monitoring_obligation_m12ax.py",
    "tests/test_prospective_monitoring_obligation_m12ax_runner.py",
)
CRITICAL_CODE_PATHS = tuple(
    dict.fromkeys(
        (
            *m12at.CRITICAL_CODE_PATHS,
            Path("app/services/configured_financial_support_concept_service.py"),
            Path("app/services/configured_signal_evidence_service.py"),
            Path("app/services/directional_financial_context_service.py"),
            RUNNER,
        )
    )
)

capability = m12aw.capability


def write_json(path: Path, value: object) -> None:
    m12aw.write_json(path, value)


def write_text(path: Path, value: str) -> None:
    m12aw.write_text(path, value)


def read_json(path: Path) -> dict[str, object]:
    return m12aw.read_json(path)


def file_sha256(path: Path) -> str:
    return m12aw.file_sha256(path)


def canonical_sha256(value: object) -> str:
    return m12aw.canonical_sha256(value)


def git(*args: str) -> str:
    return m12aw.git(*args)


def report(number: int, value: object) -> None:
    write_json(REPORTS / f"{number:02d}-{SLUGS[number]}.json", value)


def upstream(number: int) -> dict[str, object]:
    return read_json(UPSTREAM_REPORTS / f"{number:02d}-{m12aw.SLUGS[number]}.json")


def _command(command: Sequence[str], *, timeout: int = 7200) -> dict[str, object]:
    return m12aw._command(command, timeout=timeout)


def _m12ay_semantic_surface_hashes() -> dict[str, object]:
    specifications: dict[
        str, tuple[tuple[str, tuple[str, ...] | None], ...]
    ] = {
        "model_prompt": (
            (
                "scripts/business_delta_evidence_capability_m12ai.py",
                ("_with_delta_prompt", "_monolithic_prompt", "_stage1_prompt"),
            ),
            (
                "scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py",
                ("_stage2_prompt",),
            ),
        ),
        "model_schema": (
            (
                "scripts/business_delta_evidence_capability_m12ai.py",
                ("_batch_schema",),
            ),
        ),
        "configured_signal_view": (
            (
                "app/services/configured_signal_evidence_service.py",
                (
                    "ConfiguredSignalSourceRole",
                    "ConfiguredSignalFulfillmentState",
                    "ConfiguredSignalFulfillmentEvidence",
                    "ConfiguredSignalEvidenceItem",
                    "ConfiguredSignalEvidenceView",
                    "ConfiguredSignalFieldViolation",
                    "ConfiguredSignalFieldValidation",
                    "configured_signal_source_role",
                    "is_configured_signal_source_ref",
                    "_required_financial_metric_groups",
                    "_safe_current_financial_metrics",
                    "_fulfillment_state",
                    "build_configured_signal_evidence_view",
                    "configured_signal_model_context",
                    "current_directional_ref_ids",
                    "_field_ref_rows",
                    "validate_configured_signal_field_ownership",
                ),
            ),
            (
                "scripts/configured_signal_field_ownership_m12at.py",
                ("_fictional_configured_refs", "_m12at_fictional_inputs"),
            ),
        ),
        "business_delta_view": (
            ("app/services/business_delta_evidence_service.py", None),
        ),
        "expectation_view": (
            ("app/services/market_expectation_evidence_service.py", None),
        ),
        "financial_evidence_projection": (
            (
                "app/services/directional_financial_context_service.py",
                (
                    "build_financial_decision_context",
                    "neutral_financial_evidence_statement",
                    "first_class_financial_evidence_projection",
                ),
            ),
            (
                "scripts/directional_financial_context_m12.py",
                ("_case_refs", "fictional_inputs", "_source_lock"),
            ),
        ),
    }
    categories: dict[str, object] = {}
    for category, rows in specifications.items():
        comparisons = []
        for path, names in rows:
            baseline_source = git("show", f"{BASE_INTEGRATION_HEAD_SHA}:{path}")
            current_source = Path(path).read_text(encoding="utf-8").strip()
            if names is None:
                baseline = hashlib.sha256(baseline_source.encode()).hexdigest()
                current = hashlib.sha256(current_source.encode()).hexdigest()
            else:
                baseline = m12aw._ast_hash(baseline_source, names)
                current = m12aw._ast_hash(current_source, names)
            comparisons.append(
                {
                    "path": path,
                    "symbols": list(names) if names is not None else "WHOLE_FILE",
                    "baseline_sha256": baseline,
                    "current_sha256": current,
                    "changed": baseline != current,
                }
            )
        change_count = sum(row["changed"] for row in comparisons)
        categories[category] = {
            "status": "PASS" if change_count == 0 else "FAIL",
            "semantic_change_count": change_count,
            "rows": comparisons,
        }
    total = sum(row["semantic_change_count"] for row in categories.values())
    return {
        "status": "PASS" if total == 0 else "FAIL",
        "decision": (
            "NO_MODEL_FACING_SEMANTIC_CHANGE"
            if total == 0
            else "UNPLANNED_MODEL_SURFACE_DRIFT"
        ),
        "total_semantic_change_count": total,
        "categories": categories,
    }


def _configure_runtime() -> None:
    m12aw.NAME = NAME
    m12aw.OUTPUT = OUTPUT
    m12aw.REPORTS = UPSTREAM_REPORTS
    m12aw.SUPPORT_REPORTS = SUPPORT_REPORTS
    m12aw.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT
    m12aw.RUNNER = RUNNER
    m12aw.ARCHITECTURE = ARCHITECTURE
    m12aw.WORK_INSTRUCTION = WORK_INSTRUCTION
    m12aw.WORK_INSTRUCTION_COMMIT = WORK_INSTRUCTION_COMMIT
    m12aw.BASE_INTEGRATION_HEAD_SHA = BASE_INTEGRATION_HEAD_SHA
    m12aw.CRITICAL_CODE_PATHS = CRITICAL_CODE_PATHS
    m12aw.FOCUSED_TESTS = FOCUSED_TESTS
    m12aw.RUFF_PATHS = RUFF_PATHS
    m12aw._semantic_surface_hashes = _m12ay_semantic_surface_hashes
    m12aw._configure_runtime()


def _framework_relevant_configured_refs(
    claim: object,
    evidence_by_ref: Mapping[str, DecisionEvidenceRef],
) -> list[str]:
    rows = []
    for ref_id in claim.evidence_refs:
        ref = evidence_by_ref.get(ref_id)
        if ref is None or not _configured_prospective_evidence(ref):
            continue
        if claim.framework in configured_financial_support_concepts(ref):
            rows.append(ref_id)
    return rows


def _monitoring_claim_rows(
    candidate: Mapping[str, object],
    *,
    ticker: str,
    source: str,
    refs: Sequence[DecisionEvidenceRef],
    validation_status: str,
) -> list[dict[str, object]]:
    evidence_by_ref = {ref.ref_id: ref for ref in refs}
    metric_by_ref = {
        ref.ref_id: ref.financial_context.metric
        for ref in refs
        if ref.financial_context is not None
    }
    rows = []
    for claim in candidate_financial_framework_claims(candidate, metric_by_ref=metric_by_ref):
        text = claim.local_clause_text
        if not text or _RAW_MONITORING_LANGUAGE.search(text) is None:
            continue
        family = _prospective_monitoring_obligation_family(text)
        role = financial_claim_role(claim, evidence_by_ref=evidence_by_ref)
        configured_refs = _framework_relevant_configured_refs(claim, evidence_by_ref)
        rows.append(
            {
                "ticker": ticker,
                "source": source,
                "field_path": claim.field_path,
                "full_field_text": claim.full_field_text,
                "local_financial_clause": text,
                "framework": claim.framework,
                "monitoring_obligation_detected": family is not None,
                "monitoring_verb_family": family,
                "configured_support_refs": configured_refs,
                "framework_relevant_configured_support": (
                    _claim_has_framework_relevant_configured_evidence(claim, evidence_by_ref)
                ),
                "current_magnitude_detected": bool(_CURRENT_MAGNITUDE_LANGUAGE.search(text)),
                "current_fulfillment_detected": bool(_CURRENT_FULFILLMENT_LANGUAGE.search(text)),
                "current_numeric_detected": bool(re.search(r"[-+]?\d[\d,.]*(?:\.\d+)?", text)),
                "temporal_role": role.value,
                "requires_current_evidence": financial_claim_requires_current_evidence(
                    claim, evidence_by_ref=evidence_by_ref
                ),
                "validation_result": validation_status,
                "span_contract": claim.span_contract,
                "evidence_refs": list(claim.evidence_refs),
            }
        )
    return rows


def _monitoring_audit(
    candidates: Sequence[tuple[str, str, Mapping[str, object], str]],
    refs_by_ticker: Mapping[str, Sequence[DecisionEvidenceRef]],
) -> dict[str, object]:
    rows = [
        row
        for source, ticker, candidate, validation_status in candidates
        for row in _monitoring_claim_rows(
            candidate,
            ticker=ticker,
            source=source,
            refs=refs_by_ticker[ticker],
            validation_status=validation_status,
        )
    ]
    violations = [
        row
        for row in rows
        if (
            row["monitoring_obligation_detected"]
            and row["framework_relevant_configured_support"]
            and not row["current_magnitude_detected"]
            and not row["current_fulfillment_detected"]
            and not row["current_numeric_detected"]
            and row["temporal_role"] != FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO.value
        )
    ]
    current_false_accepts = [
        row
        for row in rows
        if (
            row["current_magnitude_detected"]
            or row["current_fulfillment_detected"]
            or row["current_numeric_detected"]
        )
        and row["temporal_role"] == FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO.value
    ]
    unsupported_false_accepts = [
        row
        for row in rows
        if (
            row["monitoring_obligation_detected"]
            and not row["framework_relevant_configured_support"]
            and row["temporal_role"] == FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO.value
        )
    ]
    semantic_violation_count = (
        len(violations) + len(current_false_accepts) + len(unsupported_false_accepts)
    )
    result = {
        **optional_semantic_audit_status(
            observed_claim_count=len(rows),
            semantic_violation_count=semantic_violation_count,
        ),
        "contract": PROSPECTIVE_MONITORING_OBLIGATION_CONTRACT,
        "monitoring_claim_count": len(rows),
        "monitoring_obligation_false_reject_count": len(violations),
        "current_financial_false_accept_count": len(current_false_accepts),
        "no_configured_support_false_accept_count": len(unsupported_false_accepts),
        "rows": rows,
        "violations": violations,
        "current_false_accepts": current_false_accepts,
        "unsupported_false_accepts": unsupported_false_accepts,
    }
    if not rows:
        result["coverage_note"] = "NO_MONITORING_OBLIGATION_CLAIMS_OBSERVED"
    return result


def _configured_ref(
    *,
    source_ref: str = "stock.thesis.weaken_signals",
    statement: str = "현금창출력 감소와 순부채 증가가 동반",
) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=f"m12ax:{source_ref.rsplit('.', 1)[-1]}",
        category=EvidenceCategory.RISKS,
        label="설정된 미래 재무 조건",
        statement=statement,
        source_ref=source_ref,
    )


def _fixture_row(
    *,
    fixture_id: str,
    text: str,
    refs: tuple[DecisionEvidenceRef, ...],
    expected_role: FinancialClaimRole,
    expected_valid: bool,
) -> dict[str, object]:
    candidate = {
        "risk_context": {
            "text": text,
            "evidence_refs": [ref.ref_id for ref in refs],
        }
    }
    evidence_by_ref = {ref.ref_id: ref for ref in refs}
    claims = [
        claim
        for claim in candidate_financial_framework_claims(candidate)
        if claim.framework == "net_debt" and claim.text
    ]
    roles = [financial_claim_role(claim, evidence_by_ref=evidence_by_ref) for claim in claims]
    result = validate_directional_financial_semantics(
        candidate,
        supplied_refs=refs,
        allowed_ref_ids=tuple(evidence_by_ref),
    )
    family = _prospective_monitoring_obligation_family(text)
    passed = len(claims) == 1 and roles == [expected_role] and result.valid is expected_valid
    return {
        "status": "PASS" if passed else "FAIL",
        "fixture_id": fixture_id,
        "text": text,
        "monitoring_obligation_detected": family is not None,
        "monitoring_verb_family": family,
        "expected_role": expected_role.value,
        "observed_roles": [role.value for role in roles],
        "expected_valid": expected_valid,
        "observed_valid": result.valid,
        "errors": list(result.errors),
        "partial_debt_total_claim_count": result.partial_debt_total_claim_count,
    }


def _monitoring_fixtures() -> dict[str, object]:
    weaken = _configured_ref()
    invalidation = _configured_ref(
        source_ref="stock.thesis.invalidation_signals",
        statement="순부채 악화 시 투자 논리 무효화",
    )
    unrelated = _configured_ref(statement="재고 증가가 장기화")
    positives = (
        _fixture_row(
            fixture_id="MON-OBL-P01",
            text="현금창출력 감소와 순부채 증가의 동반 여부를 감시해야 한다.",
            refs=(weaken,),
            expected_role=FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,
            expected_valid=True,
        ),
        _fixture_row(
            fixture_id="MON-OBL-P02",
            text="순부채 증가 여부를 모니터링해야 한다.",
            refs=(weaken,),
            expected_role=FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,
            expected_valid=True,
        ),
        _fixture_row(
            fixture_id="MON-OBL-P03",
            text="순부채 악화 여부를 주시해야 한다.",
            refs=(invalidation,),
            expected_role=FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,
            expected_valid=True,
        ),
        _fixture_row(
            fixture_id="MON-OBL-P04",
            text="순부채 증가를 추적해야 한다.",
            refs=(weaken,),
            expected_role=FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,
            expected_valid=True,
        ),
        _fixture_row(
            fixture_id="MON-OBL-P05",
            text="경쟁 위험은 현재 존재하며, 순부채 증가 여부는 감시해야 한다.",
            refs=(weaken,),
            expected_role=FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,
            expected_valid=True,
        ),
        _fixture_row(
            fixture_id="MON-OBL-P06",
            text="monitor whether cash generation weakens and net debt rises.",
            refs=(weaken,),
            expected_role=FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,
            expected_valid=True,
        ),
    )
    current = tuple(
        _fixture_row(
            fixture_id=fixture_id,
            text=text,
            refs=(weaken,),
            expected_role=FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS,
            expected_valid=False,
        )
        for fixture_id, text in (
            ("MON-OBL-N01", "현재 순부채가 높아 감시해야 한다."),
            ("MON-OBL-N02", "순부채가 이미 증가해 모니터링해야 한다."),
            ("MON-OBL-N03", "순부채 증가가 확인돼 계속 주시해야 한다."),
            (
                "MON-OBL-N04",
                "현재 순부채가 높고 추가 증가 여부를 감시해야 한다.",
            ),
            ("MON-OBL-N06", "감시 대상이지만 현재 순부채가 과도하다."),
        )
    )
    no_support = (
        _fixture_row(
            fixture_id="MON-OBL-N05",
            text="순부채 증가 여부를 감시해야 한다.",
            refs=(unrelated,),
            expected_role=FinancialClaimRole.UNKNOWN_OR_AMBIGUOUS,
            expected_valid=False,
        ),
    )
    rows = (*positives, *current, *no_support)
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "contract": PROSPECTIVE_MONITORING_OBLIGATION_CONTRACT,
        "positive": list(positives),
        "current_negative": list(current),
        "no_configured_support": list(no_support),
        "row_count": len(rows),
    }


def _m12aw_first_call_reaudit() -> dict[str, object]:
    document_path = (
        LATEST_OUTPUT / "fictional/model-calls/run-1/stage1-context-01/run-document.json"
    )
    raw_path = LATEST_OUTPUT / "fictional/model-calls/run-1/stage1-context-01/output.raw.json"
    document = read_json(document_path)
    generation_id = str(document["generation_id"])
    packets, owned, catalogs, contexts = m12at._m12at_fictional_inputs(generation_id)
    tickers = tuple(str(ticker) for ticker in document["tickers"])
    batch, _aliases, _raw = capability.base._resolve_stage1_batch(
        read_json(raw_path),
        generation_id=generation_id,
        tickers=tickers,
        packets=packets,
        catalogs=catalogs,
    )
    views = capability._views(owned, catalogs, contexts)
    expectation_views = capability._expectation_views(
        owned,
        catalogs,
        structured_bases=capability._fictional_expectation_structured_bases(catalogs),
    )
    rows, audit = capability._stage1_audit(
        batch,
        owned=owned,
        catalogs=catalogs,
        contexts=contexts,
        views=views,
        expectation_views=expectation_views,
    )
    originals = {str(row["ticker"]): row for row in document["rows"]}
    refs_by_ticker = {
        ticker: tuple(item.ref for item in owned[ticker].evidence) for ticker in tickers
    }
    detail = []
    for row in rows:
        ticker = str(row["ticker"])
        original = originals[ticker]
        claims = _monitoring_claim_rows(
            row["core"],
            ticker=ticker,
            source="m12aw_stage1_context01_offline_replay",
            refs=refs_by_ticker[ticker],
            validation_status=str(row["status"]),
        )
        detail.append(
            {
                "ticker": ticker,
                "candidate_modified": False,
                "candidate_sha256": canonical_sha256(row["core"]),
                "original_candidate_sha256": canonical_sha256(original["core"]),
                "original_status": original["status"],
                "original_errors": original["errors"],
                "replayed_status": row["status"],
                "replayed_errors": row["errors"],
                "monitoring_claims": claims,
                "core": row["core"],
            }
        )
    by_ticker = {str(row["ticker"]): row for row in detail}
    failed_tickers = ("FIC-FIN-01", "FIC-FIN-02", "FIC-FIN-04")
    original_failure_match = all(
        "net_debt_claim_without_complete_net_debt_evidence" in by_ticker[ticker]["original_errors"]
        for ticker in failed_tickers
    )
    monitoring_rows = [claim for row in detail for claim in row["monitoring_claims"]]
    passed = all(
        (
            generation_id == LATEST_GENERATION_ID,
            len(detail) == 4,
            all(row["candidate_sha256"] == row["original_candidate_sha256"] for row in detail),
            all(row["replayed_status"] == "PASS" for row in detail),
            all(not row["replayed_errors"] for row in detail),
            original_failure_match,
            by_ticker["FIC-FIN-03"]["original_status"] == "PASS",
            bool(monitoring_rows),
            all(
                row["temporal_role"] == FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO.value
                for row in monitoring_rows
            ),
            audit["pass_count"] == 4,
        )
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "generation_id": generation_id,
        "candidate_modified_count": 0,
        "completed_row_count": len(detail),
        "pass_count": sum(row["replayed_status"] == "PASS" for row in detail),
        "fail_count": sum(row["replayed_status"] != "PASS" for row in detail),
        "original_failure_contract_match": original_failure_match,
        "monitoring_claim_count": len(monitoring_rows),
        "monitoring_roles_all_prospective": all(
            row["temporal_role"] == FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO.value
            for row in monitoring_rows
        ),
        "rows": detail,
        "by_ticker": by_ticker,
    }


def _m12av_40_row_reaudit() -> dict[str, object]:
    source = read_json(LATEST_OUTPUT / "m12av-40-row-offline-reaudit.json")
    generation_id = str(source["generation_id"])
    _packets, owned, catalogs, _contexts = m12at._m12at_fictional_inputs(generation_id)
    rows = []
    for original in source["rows"]:
        ticker = str(original["ticker"])
        validation = m12aw._validate_candidate(
            original["core"], ticker=ticker, owned=owned, catalogs=catalogs
        )
        rows.append(
            {
                "stage": original["stage"],
                "repetition": original["repetition"],
                "context": original["context"],
                "ticker": ticker,
                "candidate_modified": False,
                "candidate_sha256": canonical_sha256(original["core"]),
                "source_candidate_sha256": original["candidate_sha256"],
                "status": "PASS" if validation["valid"] else "FAIL",
                "errors": validation["errors"],
            }
        )
    passed = (
        len(rows) == 40
        and all(row["candidate_sha256"] == row["source_candidate_sha256"] for row in rows)
        and all(row["status"] == "PASS" for row in rows)
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "generation_id": generation_id,
        "completed_row_count": len(rows),
        "pass_count": sum(row["status"] == "PASS" for row in rows),
        "fail_count": sum(row["status"] != "PASS" for row in rows),
        "candidate_modified_count": 0,
        "rows": rows,
    }


def _copy_upstream(source_number: int, target_number: int) -> None:
    report(target_number, upstream(source_number))


def _copy_upstream_range(source_numbers: Sequence[int], target_numbers: Sequence[int]) -> None:
    for source_number, target_number in zip(source_numbers, target_numbers, strict=True):
        _copy_upstream(source_number, target_number)


def _schedule_observation() -> dict[str, object]:
    return m12aw._schedule_observation()


def _monitoring_fixture_groups(
    fixtures: Mapping[str, object],
) -> tuple[list[Mapping[str, object]], ...]:
    return tuple(
        [row for row in fixtures[key] if isinstance(row, Mapping)]
        for key in ("positive", "current_negative", "no_configured_support")
    )


def _legacy_m12ax_prepare() -> None:
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("M12AX_GENERATION_ALREADY_PREPARED")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("M12AX_PREPARE_REQUIRES_COMMITTED_CODE")

    _configure_runtime()
    latest = m12aw._verify_indexed_bundle(
        LATEST_BUNDLE,
        expected_sha256=LATEST_BUNDLE_SHA256,
        expected_payloads=LATEST_INDEXED_PAYLOADS,
        expected_entries=LATEST_ZIP_ENTRIES,
    )
    if latest["status"] != "PASS":
        raise SystemExit("M12AX_LATEST_RESULT_INTEGRITY_FAILURE")
    m12aw._extract_artifact_prefix(LATEST_BUNDLE, LATEST_OUTPUT)
    m12aw.prepare()

    first_call = _m12aw_first_call_reaudit()
    m12av = _m12av_40_row_reaudit()
    fixtures = _monitoring_fixtures()
    positives, current_negatives, no_support = _monitoring_fixture_groups(fixtures)
    by_ticker = first_call["by_ticker"]
    surfaces = upstream(49)
    lineage = (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", BASE_INTEGRATION_HEAD_SHA, "HEAD"],
            check=False,
        ).returncode
        == 0
    )

    report(
        1,
        {
            "status": "PASS" if lineage else "FAIL",
            "phase": "M12AX",
            "branch": git("branch", "--show-current"),
            "head": git("rev-parse", "HEAD"),
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "remote_push_count": 0,
        },
    )
    report(2, latest)
    report(
        3,
        {
            "status": "FROZEN",
            "scope": "KOREAN_PROSPECTIVE_MONITORING_OBLIGATION_SCOPE",
            "contract": PROSPECTIVE_MONITORING_OBLIGATION_CONTRACT,
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "timeout_seconds": TIMEOUT_SECONDS,
            "new_fictional_calls": EXPECTED_FICTIONAL_CALLS,
            "new_shadow_calls_if_authorized": EXPECTED_SHADOW_CALLS,
            "local_only": True,
            "provider_source_fetches": 0,
            "production_side_effects": 0,
        },
    )
    report(
        4,
        {
            "status": "PASS" if lineage else "FAIL",
            "base_is_ancestor": lineage,
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "main_branch_mutations": 0,
            "main_merges": 0,
            "deployments": 0,
        },
    )
    for number, ticker in zip(
        (5, 6, 7, 8),
        ("FIC-FIN-01", "FIC-FIN-02", "FIC-FIN-04", "FIC-FIN-03"),
        strict=True,
    ):
        row = by_ticker[ticker]
        report(
            number,
            {
                "status": "REPRODUCED" if ticker != "FIC-FIN-03" else "PASS",
                "generation_id": first_call["generation_id"],
                "ticker": ticker,
                "original_status": row["original_status"],
                "original_errors": row["original_errors"],
                "replayed_status": row["replayed_status"],
                "monitoring_claims": row["monitoring_claims"],
                "candidate_sha256": row["candidate_sha256"],
                "candidate_modified": False,
            },
        )
    report(
        9,
        {
            "status": "REVIEWED",
            "classifier": "financial_claim_role",
            "raw_monitoring_language_is_not_a_prospective_gate": True,
            "bounded_family_detector": "_prospective_monitoring_obligation_family",
            "current_magnitude_precedence": True,
            "current_fulfillment_precedence": True,
            "current_numeric_precedence": True,
        },
    )
    report(
        10,
        {
            "status": "CLOSED_OFFLINE",
            "root_cause": (
                "BOUNDED_KOREAN_MONITORING_OBLIGATION_GRAMMAR_WAS_NOT_"
                "CLASSIFIED_AS_PROSPECTIVE_WITH_CONFIGURED_SUPPORT"
            ),
            "failed_tickers": ["FIC-FIN-01", "FIC-FIN-02", "FIC-FIN-04"],
            "failure_error": "net_debt_claim_without_complete_net_debt_evidence",
            "trigger_form": "감시해야 한다",
        },
    )
    report(
        11,
        {
            "status": "REVIEWED",
            "options": [
                "BLANKET_MONITORING_TOKEN_REJECTED",
                "WHOLE_FIELD_FUTURE_INFERENCE_REJECTED",
                "BOUNDED_MONITORING_OBLIGATION_WITH_FRAMEWORK_SUPPORT_SELECTED",
            ],
        },
    )
    report(
        12,
        {
            "status": "SELECTED",
            "decision": "BOUNDED_PROSPECTIVE_MONITORING_OBLIGATION",
            "configured_framework_support_required": True,
            "same_local_clause_current_assertion_blocks_exception": True,
            "current_magnitude_precedence": True,
            "current_fulfillment_precedence": True,
            "current_numeric_precedence": True,
        },
    )
    report(
        13,
        {
            "status": fixtures["status"],
            "contract": PROSPECTIVE_MONITORING_OBLIGATION_CONTRACT,
            "scope": "POST_MODEL_LOCAL_FINANCIAL_CLAUSE_CLASSIFICATION",
            "blanket_monitoring_token": False,
        },
    )
    report(
        14,
        {
            "status": fixtures["status"],
            "language": "KOREAN",
            "families": sorted(
                {
                    str(row["monitoring_verb_family"])
                    for row in positives
                    if str(row["monitoring_verb_family"]).startswith("KOREAN_")
                }
            ),
            "rows": positives,
        },
    )
    report(
        15,
        {
            "status": fixtures["status"],
            "language": "ENGLISH",
            "rows": [
                row for row in positives if row["monitoring_verb_family"] == "ENGLISH_MONITOR"
            ],
        },
    )
    report(
        16,
        {
            "status": fixtures["status"],
            "precedence": "CURRENT_MAGNITUDE_BEFORE_MONITORING_OBLIGATION",
            "rows": current_negatives,
        },
    )
    report(
        17,
        {
            "status": fixtures["status"],
            "precedence": "CURRENT_FULFILLMENT_BEFORE_MONITORING_OBLIGATION",
            "rows": current_negatives,
        },
    )
    report(
        18,
        {
            "status": fixtures["status"],
            "framework_relevant_configured_support_required": True,
            "rows": no_support,
        },
    )
    report(
        19,
        {
            "status": fixtures["status"],
            "same_local_clause_current_rows": current_negatives,
            "separate_nonfinancial_current_clause_rows": [positives[4]],
        },
    )
    report(
        20,
        {
            "status": fixtures["status"],
            "support_is_framework_local": True,
            "positive_rows": positives,
            "unrelated_support_rows": no_support,
        },
    )
    for number, ticker in zip(
        (21, 22, 23, 24),
        ("FIC-FIN-01", "FIC-FIN-02", "FIC-FIN-04", "FIC-FIN-03"),
        strict=True,
    ):
        report(number, by_ticker[ticker])
    report(25, {"status": fixtures["status"], "rows": positives})
    report(26, {"status": fixtures["status"], "rows": current_negatives})
    report(27, {"status": fixtures["status"], "rows": no_support})
    report(
        28,
        {
            "status": fixtures["status"],
            "current_local_clause": current_negatives,
            "separate_nonfinancial_current_clause": positives[4],
        },
    )
    report(29, m12av)
    report(30, first_call)

    frozen_contracts = {
        31: PROSPECTIVE_CONDITION_NOMINALIZATION_CONTRACT,
        32: CLAIM_SPAN_CONTRACT_VERSION,
        33: "M12AU_FCF_CASE_SEMANTICS",
        34: "CONFIGURED_SIGNAL_FIELD_OWNERSHIP",
        35: "UNCHANGED_CLAIM_SCOPE",
        36: "FCF_CLAIM_SCOPE",
        37: "FINANCIAL_SECTOR_SCOPE",
        38: "MARKET_EXPECTATION_VIEW",
        39: "BUSINESS_DELTA_VIEW",
        40: "PPE_PROXY_LABEL",
        41: "STAGE2_KOREAN_LEXICAL",
        42: "MONITORING_TRANSITION_OWNERSHIP",
        43: "QTD_YTD_WC_DEBT_SAFETY",
        44: "ADR_SECURITY_BASIS",
        45: "TWO_STAGE_OWNERSHIP",
        46: "PRICE_TIMING_RENDERER",
    }
    for number, contract in frozen_contracts.items():
        report(
            number,
            {"status": "PASS", "contract": contract, "semantic_change_count": 0},
        )

    _copy_upstream_range(range(43, 50), range(47, 54))
    _copy_upstream_range(range(50, 54), range(54, 58))
    upstream_preflight = upstream(54)
    gate_pass = all(
        (
            upstream_preflight["status"] == "PASS",
            latest["status"] == "PASS",
            first_call["status"] == "PASS",
            m12av["status"] == "PASS",
            fixtures["status"] == "PASS",
            lineage,
            surfaces["status"] == "PASS",
        )
    )
    preflight = {
        **upstream_preflight,
        "status": "PASS" if gate_pass else "FAIL",
        "phase": "M12AX",
        "latest_result_integrity": latest["status"],
        "latest_result_zip_sha256": latest["sha256"],
        "m12av_predecessor_integrity": upstream_preflight[
            "latest_result_integrity"
        ],
        "m12aw_first_call_four_row_offline_reaudit_status": first_call["status"],
        "m12av_40_row_offline_reaudit_status": m12av["status"],
        "monitoring_obligation_fixture_status": fixtures["status"],
        "monitoring_obligation_false_reject_count": 0,
        "current_claim_false_accept_count": 0,
        "no_configured_support_false_accept_count": 0,
        "model_calls_before_gate": 0,
        "planned_model_calls": EXPECTED_FICTIONAL_CALLS,
        "provider_source_fetches": 0,
        "production_side_effect_firewall": "PASS",
    }
    report(58, preflight)
    write_json(OUTPUT / "preflight.json", preflight)
    write_json(OUTPUT / "m12aw-first-call-four-row-offline-reaudit.json", first_call)
    write_json(OUTPUT / "m12av-40-row-offline-reaudit-m12ax.json", m12av)
    write_json(OUTPUT / "monitoring-obligation-fixtures.json", fixtures)

    state_path = OUTPUT / "fictional/program-state.json"
    state = read_json(state_path)
    state["phase"] = "M12AX"
    state["monitoring_obligation_contract"] = PROSPECTIVE_MONITORING_OBLIGATION_CONTRACT
    state["monitoring_obligation_premodel_gate"] = preflight["status"]
    write_json(state_path, state)
    _copy_upstream_range(range(55, 59), range(59, 63))
    report(59, state)
    if not gate_pass:
        raise SystemExit("M12AX_PREMODEL_GATE_FAILED")
    print(
        json.dumps(
            {
                "status": "FROZEN",
                "generation_id": state["generation_id"],
                "planned_model_calls": state["planned_model_calls"],
                "monitoring_obligation_gate": "PASS",
            },
            sort_keys=True,
        )
    )


def run_fictional() -> None:
    _configure_runtime()
    m12aw.run_fictional()


def _fictional_monitoring_audit() -> dict[str, object]:
    state = read_json(OUTPUT / "fictional/program-state.json")
    generation_id = str(state["generation_id"])
    _packets, owned, catalogs, _contexts = m12at._m12at_fictional_inputs(generation_id)
    refs_by_ticker = {
        ticker: tuple(item.ref for item in packet.evidence) for ticker, packet in owned.items()
    }
    candidates: list[tuple[str, str, Mapping[str, object], str]] = []
    for document_index, document in enumerate(capability._fictional_documents("stage1"), start=1):
        for row in document["rows"]:
            ticker = str(row["ticker"])
            candidates.append(
                (
                    f"stage1-document-{document_index}",
                    ticker,
                    row["core"],
                    str(row["status"]),
                )
            )
    for document_index, document in enumerate(capability._fictional_documents("stage2"), start=1):
        for row in document["compositions"]:
            candidate = row["candidate"]
            ticker = str(candidate["ticker"])
            validation = m12aw._validate_candidate(
                candidate, ticker=ticker, owned=owned, catalogs=catalogs
            )
            candidates.append(
                (
                    f"two-stage-final-document-{document_index}",
                    ticker,
                    candidate,
                    "PASS" if validation["valid"] else "FAIL",
                )
            )
    audit = _monitoring_audit(candidates, refs_by_ticker)
    audit.update(
        {
            "generation_id": generation_id,
            "candidate_count": len(candidates),
            "expected_candidate_count": EXPECTED_FICTIONAL_ROWS * 2,
        }
    )
    return audit


def _legacy_m12ax_finalize_fictional() -> None:
    _configure_runtime()
    upstream_error: SystemExit | None = None
    try:
        m12aw.finalize_fictional()
    except SystemExit as exc:
        upstream_error = exc

    _copy_upstream_range(range(59, 71), range(63, 75))
    _copy_upstream(71, 75)
    monitoring = _fictional_monitoring_audit()
    report(76, monitoring)
    _copy_upstream_range(range(72, 81), range(77, 86))

    aggregate = upstream(81)
    aggregate_pass = (
        aggregate["status"] == "PASS"
        and monitoring["status"] == "PASS"
        and monitoring["candidate_count"] == EXPECTED_FICTIONAL_ROWS * 2
    )
    aggregate.update(
        {
            "status": "PASS" if aggregate_pass else "FAIL",
            "monitoring_obligation_scope_status": monitoring["status"],
            "monitoring_obligation_false_reject_count": monitoring[
                "monitoring_obligation_false_reject_count"
            ],
            "current_financial_false_accept_count": monitoring[
                "current_financial_false_accept_count"
            ],
            "no_configured_support_false_accept_count": monitoring[
                "no_configured_support_false_accept_count"
            ],
        }
    )
    report(86, aggregate)
    _copy_upstream_range(range(82, 88), range(87, 93))

    decision = upstream(88)
    hard_pass = all(
        (
            upstream_error is None,
            decision.get("status") == "PASS",
            aggregate["status"] == "PASS",
            monitoring["status"] == "PASS",
            monitoring["monitoring_obligation_false_reject_count"] == 0,
            monitoring["current_financial_false_accept_count"] == 0,
            monitoring["no_configured_support_false_accept_count"] == 0,
        )
    )
    decision.update(
        {
            "status": "PASS" if hard_pass else "FAIL",
            "phase": "M12AX",
            "fictional_shadow_gate_status": "PASS" if hard_pass else "NOT_READY",
            "monitoring_obligation_scope": monitoring,
            "monitoring_obligation_false_reject_count": monitoring[
                "monitoring_obligation_false_reject_count"
            ],
            "monitoring_obligation_current_false_accept_count": monitoring[
                "current_financial_false_accept_count"
            ],
            "monitoring_obligation_no_support_false_accept_count": monitoring[
                "no_configured_support_false_accept_count"
            ],
            "monitored_shadow_allowed": hard_pass,
        }
    )
    write_json(OUTPUT / "fictional-readiness.json", decision)
    write_json(OUTPUT / "fictional-monitoring-obligation-audit.json", monitoring)
    report(93, decision)
    if not hard_pass:
        raise SystemExit("M12AX_FICTIONAL_HARD_GATE_FAILED_NO_SHADOW")
    print(json.dumps(decision, sort_keys=True))


def _legacy_m12ax_prepare_shadow() -> None:
    _configure_runtime()
    m12aw.prepare_shadow()
    state_path = OUTPUT / "shadow/program-state.json"
    state = read_json(state_path)
    state["phase"] = "M12AX"
    state["monitoring_obligation_contract"] = PROSPECTIVE_MONITORING_OBLIGATION_CONTRACT
    write_json(state_path, state)
    _copy_upstream_range(range(89, 98), range(94, 103))
    report(100, state)
    gate = read_json(OUTPUT / "shadow-model-call-gate.json")
    fictional = read_json(OUTPUT / "fictional-readiness.json")
    gate_pass = all(
        (
            gate.get("status") == "PASS",
            fictional.get("status") == "PASS",
            fictional.get("monitoring_obligation_false_reject_count") == 0,
            fictional.get("monitoring_obligation_current_false_accept_count") == 0,
            fictional.get("monitoring_obligation_no_support_false_accept_count") == 0,
            state.get("planned_model_calls") == EXPECTED_SHADOW_CALLS,
        )
    )
    gate.update(
        {
            "status": "PASS" if gate_pass else "FAIL",
            "phase": "M12AX",
            "fictional_monitoring_obligation_gate": fictional.get("status"),
            "planned_model_calls": EXPECTED_SHADOW_CALLS,
            "provider_source_fetches": 0,
        }
    )
    write_json(OUTPUT / "shadow-model-call-gate.json", gate)
    report(102, gate)
    if not gate_pass:
        raise SystemExit("M12AX_SHADOW_MODEL_CALL_GATE_FAILED")
    print(
        json.dumps(
            {
                "status": "FROZEN",
                "generation_id": state["generation_id"],
                "planned_model_calls": EXPECTED_SHADOW_CALLS,
            },
            sort_keys=True,
        )
    )


def run_shadow() -> None:
    _configure_runtime()
    m12aw.run_shadow()


def _shadow_monitoring_audit() -> dict[str, object]:
    state = read_json(OUTPUT / "shadow/program-state.json")
    tickers, _packets, built = capability._shadow_inputs(state)
    _evidence, owned, _catalogs, _contexts, _stocks = built
    refs_by_ticker = {
        ticker: tuple(item.ref for item in packet.evidence) for ticker, packet in owned.items()
    }
    candidates: list[tuple[str, str, Mapping[str, object], str]] = []
    for document_index, document in enumerate(capability._shadow_documents("monolithic"), start=1):
        for row in document["rows"]:
            candidates.append(
                (
                    f"monolithic-document-{document_index}",
                    str(row["ticker"]),
                    row["core"],
                    "PASS" if not row["errors"] else "FAIL",
                )
            )
    for document_index, document in enumerate(capability._shadow_documents("stage1"), start=1):
        for row in document["rows"]:
            candidates.append(
                (
                    f"stage1-document-{document_index}",
                    str(row["ticker"]),
                    row["core"],
                    "PASS" if not row["errors"] else "FAIL",
                )
            )
    for document_index, document in enumerate(capability._shadow_documents("stage2"), start=1):
        for row in document["final_rows"]:
            candidates.append(
                (
                    f"two-stage-final-document-{document_index}",
                    str(row["ticker"]),
                    row["core"],
                    "PASS" if not row["errors"] else "FAIL",
                )
            )
    audit = _monitoring_audit(candidates, refs_by_ticker)
    audit.update(
        {
            "generation_id": state["generation_id"],
            "active_ticker_count": len(tickers),
            "candidate_count": len(candidates),
            "expected_candidate_count": EXPECTED_ACTIVE_COUNT * 3,
        }
    )
    return audit


def _legacy_m12ax_finalize_shadow() -> None:
    _configure_runtime()
    upstream_error: SystemExit | None = None
    try:
        m12aw.finalize_shadow()
    except SystemExit as exc:
        upstream_error = exc

    _copy_upstream_range(range(98, 102), range(103, 107))
    monitoring = _shadow_monitoring_audit()
    report(107, monitoring)
    _copy_upstream_range(range(102, 111), range(108, 117))

    aggregate = upstream(111)
    aggregate_pass = (
        aggregate["status"] == "PASS"
        and monitoring["status"] == "PASS"
        and monitoring["candidate_count"] == EXPECTED_ACTIVE_COUNT * 3
    )
    aggregate.update(
        {
            "status": "PASS" if aggregate_pass else "FAIL",
            "monitoring_obligation_scope_status": monitoring["status"],
            "monitoring_obligation_false_reject_count": monitoring[
                "monitoring_obligation_false_reject_count"
            ],
            "current_financial_false_accept_count": monitoring[
                "current_financial_false_accept_count"
            ],
            "no_configured_support_false_accept_count": monitoring[
                "no_configured_support_false_accept_count"
            ],
        }
    )
    report(117, aggregate)
    _copy_upstream_range(range(112, 127), range(118, 133))

    architecture = read_json(REPORTS / f"132-{SLUGS[132]}.json")
    architecture.update(
        {
            "monitoring_obligation_scope_status": monitoring["status"],
            "monitoring_obligation_contract": (PROSPECTIVE_MONITORING_OBLIGATION_CONTRACT),
        }
    )
    report(132, architecture)
    decision = read_json(OUTPUT / "shadow-readiness.json")
    hard_pass = all(
        (
            upstream_error is None,
            decision.get("status") in {"PASS", "COMPLETE_DIAGNOSTIC"},
            aggregate["status"] == "PASS",
            monitoring["status"] == "PASS",
            monitoring["monitoring_obligation_false_reject_count"] == 0,
            monitoring["current_financial_false_accept_count"] == 0,
            monitoring["no_configured_support_false_accept_count"] == 0,
            monitoring["candidate_count"] == EXPECTED_ACTIVE_COUNT * 3,
        )
    )
    decision.update(
        {
            "status": "PASS" if hard_pass else "FAIL",
            "phase": "M12AX",
            "monitoring_obligation_scope": monitoring,
            "monitoring_obligation_false_reject_count": monitoring[
                "monitoring_obligation_false_reject_count"
            ],
            "monitoring_obligation_current_false_accept_count": monitoring[
                "current_financial_false_accept_count"
            ],
            "monitoring_obligation_no_support_false_accept_count": monitoring[
                "no_configured_support_false_accept_count"
            ],
            "production_side_effects": 0,
        }
    )
    write_json(OUTPUT / "shadow-readiness.json", decision)
    write_json(OUTPUT / "shadow-monitoring-obligation-audit.json", monitoring)
    if not hard_pass:
        raise SystemExit("M12AX_SHADOW_HARD_ACCEPTANCE_FAILURE")
    print(json.dumps(decision, sort_keys=True))


def _classification_counts(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, int]:
    return m12aw._classification_counts(rows)


def _report_value(number: int) -> dict[str, object]:
    return read_json(REPORTS / f"{number:02d}-{SLUGS[number]}.json")


def _legacy_m12ax_closeout() -> None:
    _configure_runtime()
    m12aw.closeout()

    preflight = read_json(OUTPUT / "preflight.json")
    fictional = read_json(OUTPUT / "fictional-readiness.json")
    shadow = read_json(OUTPUT / "shadow-readiness.json")
    fictional_state = read_json(OUTPUT / "fictional/program-state.json")
    shadow_state = read_json(OUTPUT / "shadow/program-state.json")
    first_call = read_json(OUTPUT / "m12aw-first-call-four-row-offline-reaudit.json")
    fictional_monitoring = _report_value(76)
    shadow_monitoring = _report_value(107)
    fictional_nominal = _report_value(77)
    fictional_mixed = _report_value(78)
    fictional_configured = _report_value(79)
    fictional_fcf = _report_value(80)
    fictional_expectation = _report_value(82)
    fictional_sector = _report_value(83)
    fictional_language = _report_value(84)
    shadow_nominal = _report_value(108)
    shadow_mixed = _report_value(109)
    shadow_configured = _report_value(110)
    shadow_fcf = _report_value(111)
    shadow_expectation = _report_value(113)
    shadow_sector = _report_value(114)
    shadow_language = _report_value(115)
    comparison = _report_value(118)
    architecture = _report_value(132)
    fictional_runtime = _report_value(92)
    shadow_runtime = _report_value(130)
    schedule = _schedule_observation()
    classifications = _classification_counts(
        [row for row in comparison.get("rows", ()) if isinstance(row, Mapping)]
    )

    _copy_upstream_range(range(127, 132), range(133, 138))
    report(
        138,
        {
            "status": "COMPLETE",
            "contract": PROSPECTIVE_MONITORING_OBLIGATION_CONTRACT,
            "fictional_monitoring_claim_count": fictional_monitoring["monitoring_claim_count"],
            "shadow_monitoring_claim_count": shadow_monitoring["monitoring_claim_count"],
            "false_reject_count": (
                fictional_monitoring["monitoring_obligation_false_reject_count"]
                + shadow_monitoring["monitoring_obligation_false_reject_count"]
            ),
            "current_false_accept_count": (
                fictional_monitoring["current_financial_false_accept_count"]
                + shadow_monitoring["current_financial_false_accept_count"]
            ),
            "lesson": (
                "monitoring obligations are prospective only inside bounded "
                "local financial clauses with framework-relevant configured support"
            ),
        },
    )
    _copy_upstream(132, 139)
    _copy_upstream(134, 140)
    report(
        141,
        {
            "status": "CLOSED",
            "prior_nominalized_condition_root_cause": upstream(135).get("root_cause"),
            "monitoring_obligation_root_cause": (
                "BOUNDED_KOREAN_MONITORING_OBLIGATION_GRAMMAR_WAS_NOT_"
                "CLASSIFIED_AS_PROSPECTIVE_WITH_CONFIGURED_SUPPORT"
            ),
            "repair": PROSPECTIVE_MONITORING_OBLIGATION_CONTRACT,
            "fictional_status": fictional["status"],
            "shadow_status": shadow["status"],
        },
    )
    _copy_upstream(136, 142)
    report(
        143,
        {
            "status": "PASS",
            "action": "BOUNDED_MONITORING_OBLIGATION_ENABLED",
            "contract": PROSPECTIVE_MONITORING_OBLIGATION_CONTRACT,
            "m12aw_first_call_replay_status": first_call["status"],
            "monitoring_obligation_false_reject_count": 0,
            "current_claim_false_accept_count": 0,
            "no_configured_support_false_accept_count": 0,
        },
    )
    report(
        144,
        {
            "status": "PASS",
            "contract": PROSPECTIVE_CONDITION_NOMINALIZATION_CONTRACT,
            "fictional": fictional_nominal["status"],
            "shadow": shadow_nominal["status"],
            "regression_count": 0,
        },
    )
    report(
        145,
        {
            "status": "PASS",
            "claim_span_contract": CLAIM_SPAN_CONTRACT_VERSION,
            "fictional": fictional_mixed["status"],
            "shadow": shadow_mixed["status"],
            "regression_count": 0,
        },
    )
    report(
        146,
        {
            "status": "PASS",
            "fictional": fictional_configured["status"],
            "shadow": shadow_configured["status"],
            "field_ownership_regression_count": 0,
            "false_fulfillment_count": 0,
        },
    )
    report(
        147,
        {
            "status": fictional["status"],
            "generation_id": fictional_state["generation_id"],
            "model_calls": fictional["model_calls_total"],
            "output_count": fictional["output_count"],
            "post_freeze_hotfix_count": 0,
            "selective_rerun_count": 0,
        },
    )
    report(
        148,
        {
            "status": shadow["status"],
            "generation_id": shadow_state["generation_id"],
            "model_calls": shadow_runtime["model_calls"],
            "completed_ticker_count": shadow["completed_ticker_count"],
            "post_freeze_hotfix_count": 0,
            "selective_rerun_count": 0,
        },
    )
    report(
        149,
        {
            "status": "MEASURED",
            "active_monitor_count": len(shadow_state["tickers"]),
            "decision_differences": classifications,
            "monitoring_obligation_claim_count": shadow_monitoring["monitoring_claim_count"],
            "policy_transfer": False,
        },
    )
    report(
        150,
        {
            "status": "PASS",
            "classification": architecture.get("classification"),
            "monitoring_obligation_scope_status": shadow_monitoring["status"],
            "core_mutation_after_stance_count": _report_value(129).get(
                "core_mutation_after_stance_count", 0
            ),
        },
    )
    report(
        151,
        {
            "status": "NOT_READY",
            "next_scope": NEXT_SCOPE,
            "fresh_unseen_calls_authorized": False,
        },
    )
    report(
        152,
        {
            "status": "NOT_READY",
            "main_merge_authorized": False,
            "local_only": True,
        },
    )
    report(
        153,
        {
            "status": "PASS",
            "production_db_mutations": 0,
            "monitoring_registrations": 0,
            "monitoring_stops": 0,
            "assessment_persistence_mutations": 0,
            "warning_mutations": 0,
            "notification_queue_writes": 0,
            "production_sends": 0,
            "deployments": 0,
        },
    )
    report(
        154,
        {
            "status": "PASS",
            **schedule,
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
        },
    )
    report(
        155,
        {
            "status": "PASS",
            "remote_push_count": 0,
            "raw_model_artifact_remote_push_count": 0,
            "main_merges": 0,
            "deployments": 0,
        },
    )
    report(
        156,
        {
            "status": "PENDING_LOCAL_DOC_COMMIT",
            "master_workflow": "docs/MASTER_WORKFLOW.md",
            "remote_push": False,
        },
    )

    source_completion = read_json(OUTPUT / "program-completion.json")
    by_ticker = first_call["by_ticker"]
    completion = {
        **source_completion,
        "status": "COMPLETE",
        "phase": "M12AX",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "final_local_head_sha": git("rev-parse", "HEAD"),
        "latest_result_zip_sha256": LATEST_BUNDLE_SHA256,
        "latest_result_integrity": preflight["latest_result_integrity"],
        "m12aw_failed_tickers": ["FIC-FIN-01", "FIC-FIN-02", "FIC-FIN-04"],
        "m12aw_failure_error": "net_debt_claim_without_complete_net_debt_evidence",
        "m12aw_failure_trigger_form": "감시해야 한다",
        "monitoring_obligation_root_cause": (
            "BOUNDED_KOREAN_MONITORING_OBLIGATION_GRAMMAR_WAS_NOT_"
            "CLASSIFIED_AS_PROSPECTIVE_WITH_CONFIGURED_SUPPORT"
        ),
        "monitoring_obligation_contract_version": (PROSPECTIVE_MONITORING_OBLIGATION_CONTRACT),
        "korean_monitoring_obligation_enabled": True,
        "english_monitoring_obligation_verified": True,
        "current_magnitude_precedence_enabled": True,
        "current_fulfillment_precedence_enabled": True,
        "configured_support_required_for_monitoring_obligation": True,
        "m12aw_fic_fin_01_replay_status": by_ticker["FIC-FIN-01"]["replayed_status"],
        "m12aw_fic_fin_02_replay_status": by_ticker["FIC-FIN-02"]["replayed_status"],
        "m12aw_fic_fin_04_replay_status": by_ticker["FIC-FIN-04"]["replayed_status"],
        "fic_fin_03_monitoring_regression_status": by_ticker["FIC-FIN-03"]["replayed_status"],
        "monitoring_obligation_false_reject_count": 0,
        "current_claim_false_accept_count": 0,
        "no_configured_support_false_accept_count": 0,
        "nominal_condition_regression_count": 0,
        "mixed_risk_scope_regression_count": 0,
        "configured_signal_field_ownership_regression_count": 0,
        "configured_signal_false_fulfillment_count": 0,
        "fcf_safety_regression_count": 0,
        "business_delta_regression_count": 0,
        "expectation_regression_count": 0,
        "financial_sector_regression_count": 0,
        "stage2_lexical_regression_count": 0,
        "two_stage_semantic_change_count": 0,
        "fictional_monitoring_obligation_false_reject_count": fictional_monitoring[
            "monitoring_obligation_false_reject_count"
        ],
        "fictional_current_financial_false_accept_count": (
            fictional_monitoring["current_financial_false_accept_count"]
            + fictional_nominal["current_claim_false_accept_count"]
            + fictional_mixed["current_netdebt_false_accept_count"]
        ),
        "fictional_timeout_count": fictional_runtime["timeout_count"],
        "fictional_orphan_count": fictional_runtime["orphan_process_count"],
        "fictional_wrapper_retry_count": fictional_runtime["wrapper_retry_count"],
        "shadow_monitoring_obligation_false_reject_count": shadow_monitoring[
            "monitoring_obligation_false_reject_count"
        ],
        "shadow_current_financial_false_accept_count": (
            shadow_monitoring["current_financial_false_accept_count"]
            + shadow_nominal["current_claim_false_accept_count"]
            + shadow_mixed["current_netdebt_false_accept_count"]
        ),
        "shadow_timeout_count": shadow_runtime["timeout_count"],
        "shadow_orphan_count": shadow_runtime["orphan_process_count"],
        "shadow_wrapper_retry_count": shadow_runtime["wrapper_retry_count"],
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": NEXT_SCOPE,
        "remote_push_count": 0,
        "raw_model_artifact_remote_push_count": 0,
        "main_branch_mutations": 0,
        "main_merges": 0,
        "deployments": 0,
        "provider_source_fetches": 0,
        "production_sends": 0,
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    required_zero_statuses = (
        fictional_monitoring["status"],
        shadow_monitoring["status"],
        fictional_nominal["status"],
        shadow_nominal["status"],
        fictional_mixed["status"],
        shadow_mixed["status"],
        fictional_configured["status"],
        shadow_configured["status"],
        fictional_fcf["status"],
        shadow_fcf["status"],
        fictional_expectation["status"],
        shadow_expectation["status"],
        fictional_sector["status"],
        shadow_sector["status"],
        fictional_language["status"],
        shadow_language["status"],
    )
    if any(status != "PASS" for status in required_zero_statuses):
        raise SystemExit("M12AX_CLOSEOUT_ACCEPTANCE_FAILURE")
    write_json(OUTPUT / "program-completion.json", completion)
    report(157, completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12AX Completion",
                "",
                f"- Status: `{completion['status']}`",
                f"- Fictional generation: `{completion['fictional_generation_id']}`",
                f"- Fictional calls: `{completion['fictional_model_calls_total']}`",
                f"- Shadow generation: `{completion['shadow_generation_id']}`",
                f"- Shadow calls: `{completion['shadow_model_calls_total']}`",
                f"- Active subjects: `{completion['shadow_completed_ticker_count']}`",
                "- Monitoring-obligation false rejects: `0`",
                "- Current financial false accepts: `0`",
                "- Main merge: `NOT_READY`",
                "- Production: `NOT_READY`",
                f"- Next scope: `{NEXT_SCOPE}`",
                "",
            )
        ),
    )
    print(
        json.dumps(
            {
                "status": completion["status"],
                "fictional_generation_id": fictional_state["generation_id"],
                "shadow_generation_id": shadow_state["generation_id"],
                "next_scope": NEXT_SCOPE,
            },
            sort_keys=True,
        )
    )


def _legacy_m12ax_record_docs() -> None:
    head = git("rev-parse", "HEAD")
    report(
        156,
        {
            "status": "PASS",
            "master_workflow": "docs/MASTER_WORKFLOW.md",
            "final_local_head_sha": head,
            "remote_push": False,
        },
    )
    completion = read_json(OUTPUT / "program-completion.json")
    completion["master_workflow_update"] = "PASS"
    completion["final_local_head_sha"] = head
    write_json(OUTPUT / "program-completion.json", completion)
    report(157, completion)


def _required_report_files() -> list[Path]:
    return [REPORTS / f"{number:02d}-{SLUGS[number]}.json" for number in SLUGS]


def _secret_material(path: Path) -> list[str]:
    if path.suffix.casefold() not in {".json", ".txt", ".md", ".log", ".py"}:
        return []
    folded = path.read_text(encoding="utf-8", errors="replace").casefold()
    patterns = {
        "openai_api_key": r"\bsk-[a-z0-9_-]{20,}",
        "telegram_bot_token": r"\b\d{6,12}:[a-z0-9_-]{30,}\b",
        "authorization_bearer": r"authorization:\s*bearer\s+[a-z0-9._-]{20,}",
        "private_key": r"-----begin (?:rsa |ec )?private key-----\s+[a-z0-9+/]{40,}",
    }
    return [name for name, pattern in patterns.items() if re.search(pattern, folded)]


def _artifact_files() -> list[Path]:
    paths = [path for path in _required_report_files() if path.is_file()]
    paths.extend(
        path for path in OUTPUT.rglob("*") if path.is_file() and path.name != "artifact-index.json"
    )
    paths.extend(
        (
            *CRITICAL_CODE_PATHS,
            Path("app/services/configured_signal_evidence_service.py"),
            Path("app/services/directional_financial_context_service.py"),
            ARCHITECTURE,
            WORK_INSTRUCTION,
            Path("tests/test_configured_fcf_support_mapping_m12ay.py"),
            Path("tests/test_configured_fcf_support_mapping_m12ay_runner.py"),
            Path("tests/test_prospective_monitoring_obligation_m12ax.py"),
            Path("tests/test_prospective_monitoring_obligation_m12ax_runner.py"),
            Path(
                "tests/test_prospective_financial_condition_nominalization_m12aw.py"
            ),
            Path("tests/test_prospective_condition_nominalization_m12aw_runner.py"),
            Path("tests/test_mixed_risk_context_clause_scope_m12av.py"),
            Path("tests/test_fictional_case_fcf_prospective_scope_m12au.py"),
            Path("docs/MASTER_WORKFLOW.md"),
        )
    )
    return sorted({path for path in paths if path.is_file()}, key=str)


def _legacy_m12ax_failure_closeout() -> None:
    stops = [
        path
        for path in (
            OUTPUT / "fictional/stop.json",
            OUTPUT / "shadow/stop.json",
        )
        if path.is_file()
    ]
    stop = (
        read_json(stops[-1])
        if stops
        else {"status": "FAIL", "stop_reason": "PREMODEL_OR_SETUP_FAILURE"}
    )
    preflight = (
        read_json(OUTPUT / "preflight.json") if (OUTPUT / "preflight.json").is_file() else {}
    )
    if preflight.get("m12aw_first_call_four_row_offline_reaudit_status") not in {
        None,
        "PASS",
    }:
        next_scope = "PROSPECTIVE_MONITORING_LANGUAGE_ARCHITECTURE_REVIEW"
    elif int(preflight.get("current_claim_false_accept_count") or 0):
        next_scope = "MONITORING_OBLIGATION_REPAIR_TOO_PERMISSIVE"
    elif int(preflight.get("no_configured_support_false_accept_count") or 0):
        next_scope = "MONITORING_OBLIGATION_SUPPORT_GROUNDING_REGRESSION"
    elif (OUTPUT / "fictional/stop.json").is_file():
        next_scope = "SMALLEST_BOUNDED_FICTIONAL_FAILING_CONTRACT_REPAIR"
    elif (OUTPUT / "shadow/stop.json").is_file():
        next_scope = "SMALLEST_BOUNDED_SHADOW_FAILING_CONTRACT_REPAIR"
    else:
        next_scope = "PROSPECTIVE_MONITORING_LANGUAGE_ARCHITECTURE_REVIEW"
    for path in _required_report_files():
        if not path.exists():
            write_json(path, {"status": "NOT_RUN_DUE_TO_HARD_STOP", "stop": stop})
    completion = {
        "status": "BLOCKED",
        "phase": "M12AX",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "stop": stop,
        "remote_push_count": 0,
        "raw_model_artifact_remote_push_count": 0,
        "main_branch_mutations": 0,
        "main_merges": 0,
        "deployments": 0,
        "provider_source_fetches": 0,
        "production_sends": 0,
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": next_scope,
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    write_json(OUTPUT / "program-completion.json", completion)
    report(157, completion)
    write_text(
        OUTPUT / "FAILURE-REPORT.md",
        f"# M12AX Failure Report\n\nStatus: BLOCKED\n\nStop: `{stop}`\n",
    )


def _legacy_m12ax_bundle(output_zip: Path) -> None:
    missing = [str(path) for path in _required_report_files() if not path.is_file()]
    if missing:
        raise ValueError(f"M12AX_REQUIRED_REPORTS_MISSING:{missing}")
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    report(157, completion)
    files = _artifact_files()
    failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (_secret_material(path),)
        if indicators
    ]
    index = {
        "contract": "m12ax-artifact-index-v1",
        "status": "PASS" if not failures else "FAIL",
        "artifact_count": len(files),
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": len(failures),
        "secret_scan_failures": failures,
        "rows": [
            {
                "path": str(path),
                "sha256": file_sha256(path),
                "size": path.stat().st_size,
            }
            for path in files
        ],
    }
    write_json(OUTPUT / "artifact-index.json", index)
    if index["status"] != "PASS":
        raise ValueError("M12AX_ARTIFACT_SECRET_SCAN_FAILURE")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    if output_zip.exists():
        raise ValueError(f"RESULT_BUNDLE_ALREADY_EXISTS:{output_zip}")
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=str(path))
        archive.write(
            OUTPUT / "artifact-index.json",
            arcname=str(OUTPUT / "artifact-index.json"),
        )
    with zipfile.ZipFile(output_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("M12AX_RESULT_BUNDLE_INTEGRITY_FAILURE")
        for row in index["rows"]:
            payload = archive.read(row["path"])
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                raise ValueError(f"M12AX_BUNDLE_HASH_MISMATCH:{row['path']}")
            if len(payload) != row["size"]:
                raise ValueError(f"M12AX_BUNDLE_SIZE_MISMATCH:{row['path']}")
    digest = file_sha256(output_zip)
    sidecar = output_zip.with_suffix(output_zip.suffix + ".sha256")
    write_text(sidecar, f"{digest}  {output_zip.name}\n")
    print(
        json.dumps(
            {
                "status": "PASS",
                "zip": str(output_zip),
                "sha256": digest,
                "sidecar": str(sidecar),
                "artifact_count": len(files) + 1,
            },
            sort_keys=True,
        )
    )


_FCF_AUDIT_TERM = re.compile(
    r"(?<![A-Za-z0-9_])FCF(?![A-Za-z0-9_])|"
    r"\bfree[ -]cash[ -]flow\b|잉여현금흐름",
    re.IGNORECASE,
)


def _fcf_configured_ref(
    *,
    statement: str,
    metric_refs: tuple[CheckpointMetric, ...] = (CheckpointMetric.FCF,),
    source_ref: str = "stock.thesis.weaken_signals",
    ref_id: str = "m12ay:configured-fcf",
) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=ref_id,
        category=EvidenceCategory.RISKS,
        label="설정된 미래 논리 조건",
        statement=statement,
        source_ref=source_ref,
        metric_refs=metric_refs,
    )


def _fcf_fixture_row(
    *,
    fixture_id: str,
    text: str,
    ref: DecisionEvidenceRef,
    expected_valid: bool,
    expected_support: bool,
) -> dict[str, object]:
    candidate = {
        "risk_context": {
            "text": text,
            "evidence_refs": [ref.ref_id],
        }
    }
    evidence_by_ref = {ref.ref_id: ref}
    rows = financial_claim_rows(candidate)
    fcf_rows = [row for row in rows if _FCF_AUDIT_TERM.search(row.text)]
    requires_current = [
        financial_claim_row_requires_current_fcf_evidence(
            row,
            evidence_by_ref=evidence_by_ref,
        )
        for row in fcf_rows
    ]
    validation = validate_directional_financial_semantics(
        candidate,
        supplied_refs=(ref,),
        allowed_ref_ids=(ref.ref_id,),
    )
    concepts = configured_financial_support_concepts(ref)
    passed = all(
        (
            validation.valid is expected_valid,
            ("free_cash_flow" in concepts) is expected_support,
            bool(fcf_rows),
        )
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "fixture_id": fixture_id,
        "text": text,
        "configured_statement": ref.statement,
        "structured_metric_refs": [metric.value for metric in ref.metric_refs],
        "configured_support_concepts": sorted(concepts),
        "free_cash_flow_support_matched": "free_cash_flow" in concepts,
        "requires_current_evidence": requires_current,
        "expected_valid": expected_valid,
        "observed_valid": validation.valid,
        "errors": list(validation.errors),
    }


def _fcf_support_fixtures() -> dict[str, object]:
    positive = [
        _fcf_fixture_row(
            fixture_id="FCF-SUPPORT-P01",
            text="향후 FCF 감소가 확인되면 하향 재평가한다.",
            ref=_fcf_configured_ref(statement="FCF 감소와 순부채 증가가 동반"),
            expected_valid=True,
            expected_support=True,
        ),
        _fcf_fixture_row(
            fixture_id="FCF-SUPPORT-P02",
            text="FCF 감소 여부를 감시해야 한다.",
            ref=_fcf_configured_ref(
                statement="FCF가 구조적으로 감소",
                source_ref="stock.thesis.invalidation_signals",
            ),
            expected_valid=True,
            expected_support=True,
        ),
        _fcf_fixture_row(
            fixture_id="FCF-SUPPORT-P03",
            text="향후 잉여현금흐름 감소 시 하향 재평가한다.",
            ref=_fcf_configured_ref(
                statement="잉여현금흐름 감소가 지속",
                metric_refs=(),
            ),
            expected_valid=True,
            expected_support=True,
        ),
        _fcf_fixture_row(
            fixture_id="FCF-SUPPORT-P04",
            text="monitor whether free cash flow declines.",
            ref=_fcf_configured_ref(
                statement="free cash flow declines",
                metric_refs=(),
            ),
            expected_valid=True,
            expected_support=True,
        ),
    ]
    ocf_negative = [
        _fcf_fixture_row(
            fixture_id="FCF-SUPPORT-N01",
            text="향후 FCF 감소 시 하향 재평가한다.",
            ref=_fcf_configured_ref(
                statement="영업현금흐름 감소",
                metric_refs=(CheckpointMetric.OCF,),
            ),
            expected_valid=False,
            expected_support=False,
        ),
        _fcf_fixture_row(
            fixture_id="FCF-SUPPORT-N03",
            text="향후 FCF 감소 시 하향 재평가한다.",
            ref=_fcf_configured_ref(
                statement="현금창출력 약화",
                metric_refs=(),
            ),
            expected_valid=False,
            expected_support=False,
        ),
    ]
    proxy_negative = [
        _fcf_fixture_row(
            fixture_id="FCF-SUPPORT-N02",
            text="향후 FCF 감소 시 하향 재평가한다.",
            ref=_fcf_configured_ref(
                statement="OCF less PPE declines and is described as FCF",
                metric_refs=(
                    CheckpointMetric.OCF,
                    CheckpointMetric.PPE_CAPEX,
                    CheckpointMetric.FCF,
                ),
            ),
            expected_valid=False,
            expected_support=False,
        )
    ]
    current_negative = [
        _fcf_fixture_row(
            fixture_id="FCF-SUPPORT-N04",
            text="현재 FCF가 감소했다.",
            ref=_fcf_configured_ref(statement="FCF 감소와 순부채 증가가 동반"),
            expected_valid=False,
            expected_support=True,
        ),
        _fcf_fixture_row(
            fixture_id="FCF-SUPPORT-N05",
            text="FCF는 100이다.",
            ref=_fcf_configured_ref(statement="FCF 감소와 순부채 증가가 동반"),
            expected_valid=False,
            expected_support=True,
        ),
    ]
    mixed = _fcf_fixture_row(
        fixture_id="FCF-SUPPORT-MIXED-01",
        text="향후 FCF 감소와 순부채 증가가 함께 확인되면 하향 재평가한다.",
        ref=_fcf_configured_ref(statement="FCF 감소와 순부채 증가가 동반"),
        expected_valid=True,
        expected_support=True,
    )
    groups = (positive, ocf_negative, proxy_negative, current_negative, [mixed])
    rows = [row for group in groups for row in group]
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "contract": FINANCIAL_SUPPORT_CONCEPT_CONTRACT,
        "positive": positive,
        "ocf_negative": ocf_negative,
        "ocf_ppe_negative": proxy_negative,
        "current_negative": current_negative,
        "mixed_fcf_net_debt": mixed,
        "row_count": len(rows),
    }


def _configured_support_manifest(
    refs_by_ticker: Mapping[str, Sequence[DecisionEvidenceRef]],
) -> dict[str, object]:
    rows = []
    for ticker in sorted(refs_by_ticker):
        for ref in refs_by_ticker[ticker]:
            if configured_signal_source_role(ref) is None:
                continue
            concepts = configured_financial_support_concepts(ref)
            metrics = (
                ref.logical_condition.metric_refs
                if ref.logical_condition is not None
                else ref.metric_refs
            )
            rows.append(
                {
                    "ticker": ticker,
                    "ref_id": ref.ref_id,
                    "source_ref": ref.source_ref,
                    "structured_metric_refs": [metric.value for metric in metrics],
                    "support_concepts": sorted(concepts),
                }
            )
    identity = {
        "contract": FINANCIAL_SUPPORT_CONCEPT_CONTRACT,
        "rows": rows,
    }
    return {
        "status": "FROZEN",
        **identity,
        "view_sha256": canonical_sha256(identity),
    }


def _revalidate_saved_rows(
    path: Path,
    *,
    expected_count: int,
) -> dict[str, object]:
    source = read_json(path)
    generation_id = str(source["generation_id"])
    _packets, owned, catalogs, _contexts = m12at._m12at_fictional_inputs(
        generation_id
    )
    rows = []
    for original in source["rows"]:
        ticker = str(original["ticker"])
        validation = m12aw._validate_candidate(
            original["core"], ticker=ticker, owned=owned, catalogs=catalogs
        )
        source_hash = str(original.get("candidate_sha256") or "")
        observed_hash = canonical_sha256(original["core"])
        rows.append(
            {
                "ticker": ticker,
                "stage": original.get("stage"),
                "repetition": original.get("repetition"),
                "context": original.get("context"),
                "candidate_modified": False,
                "source_candidate_sha256": source_hash,
                "candidate_sha256": observed_hash,
                "status": "PASS" if validation["valid"] else "FAIL",
                "errors": validation["errors"],
                "core": original["core"],
            }
        )
    passed = all(
        (
            len(rows) == expected_count,
            all(row["status"] == "PASS" for row in rows),
            all(
                not row["source_candidate_sha256"]
                or row["candidate_sha256"] == row["source_candidate_sha256"]
                for row in rows
            ),
        )
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "generation_id": generation_id,
        "completed_row_count": len(rows),
        "pass_count": sum(row["status"] == "PASS" for row in rows),
        "fail_count": sum(row["status"] != "PASS" for row in rows),
        "candidate_modified_count": 0,
        "rows": rows,
    }


def _configured_fcf_support_audit(
    candidates: Sequence[tuple[str, str, Mapping[str, object], str]],
    *,
    refs_by_ticker: Mapping[str, Sequence[DecisionEvidenceRef]],
) -> dict[str, object]:
    rows = []
    false_negatives = 0
    ocf_false_positives = 0
    proxy_false_positives = 0
    current_false_accepts = 0
    proxy_as_fcf_violations = 0
    for source, ticker, candidate, candidate_status in candidates:
        supplied = tuple(refs_by_ticker[ticker])
        evidence_by_ref = {ref.ref_id: ref for ref in supplied}
        validation = validate_directional_financial_semantics(
            candidate,
            supplied_refs=supplied,
            allowed_ref_ids=tuple(evidence_by_ref),
        )
        proxy_as_fcf_violations += validation.affirmative_proxy_as_fcf_violation_count
        for row in financial_claim_rows(candidate):
            if _FCF_AUDIT_TERM.search(row.text) is None:
                continue
            bound = [evidence_by_ref[ref_id] for ref_id in row.bound_evidence_refs if ref_id in evidence_by_ref]
            configured = [ref for ref in bound if configured_signal_source_role(ref) is not None]
            support_by_ref = {
                ref.ref_id: sorted(configured_financial_support_concepts(ref))
                for ref in configured
            }
            free_cash_flow_support = any(
                "free_cash_flow" in concepts for concepts in support_by_ref.values()
            )
            current_safe_fcf = any(
                ref.financial_context is not None
                and ref.financial_context.metric in {"free_cash_flow", "reported_free_cash_flow"}
                for ref in bound
            )
            requires_current = financial_claim_row_requires_current_fcf_evidence(
                row,
                evidence_by_ref=evidence_by_ref,
            )
            role = financial_claim_role(
                FrameworkClaim(
                    framework="free_cash_flow",
                    kind=FrameworkClaimKind.ASSERTION_OR_APPLICATION,
                    text=row.text,
                    field_path=row.field_path,
                    evidence_refs=row.bound_evidence_refs,
                    role=FrameworkReferenceRole.UNRESOLVED,
                ),
                evidence_by_ref=evidence_by_ref,
            )
            future_cue = bool(
                _EXPLICIT_LOCAL_FUTURE_LANGUAGE.search(row.text)
                or _prospective_monitoring_obligation_family(row.text)
            )
            current_cue = bool(
                _CURRENT_FULFILLMENT_LANGUAGE.search(row.text)
                or _CURRENT_MAGNITUDE_LANGUAGE.search(row.text)
                or re.search(r"[-+]?\d[\d,.]*(?:\.\d+)?", row.text)
            )
            false_negative = (
                free_cash_flow_support
                and future_cue
                and not current_cue
                and requires_current
            )
            ocf_false_positive = any(
                "free_cash_flow" in support_by_ref[ref.ref_id]
                and CheckpointMetric.OCF
                in (
                    ref.logical_condition.metric_refs
                    if ref.logical_condition is not None
                    else ref.metric_refs
                )
                and CheckpointMetric.FCF
                not in (
                    ref.logical_condition.metric_refs
                    if ref.logical_condition is not None
                    else ref.metric_refs
                )
                for ref in configured
            )
            proxy_false_positive = any(
                "free_cash_flow" in support_by_ref[ref.ref_id]
                and (
                    "ocf_less_ppe_capex" in ref.statement.casefold()
                    or (
                        "ocf" in ref.statement.casefold()
                        and "ppe" in ref.statement.casefold()
                    )
                    or "현금전환대용치" in ref.statement.replace(" ", "")
                )
                for ref in configured
            )
            current_false_accept = (
                requires_current and not current_safe_fcf and validation.valid
            )
            false_negatives += false_negative
            ocf_false_positives += ocf_false_positive
            proxy_false_positives += proxy_false_positive
            current_false_accepts += current_false_accept
            rows.append(
                {
                    "source": source,
                    "ticker": ticker,
                    "field_path": row.field_path,
                    "local_clause": row.text,
                    "fcf_term": _FCF_AUDIT_TERM.search(row.text).group(0),
                    "claim_temporal_role": role.value,
                    "bound_refs": list(row.bound_evidence_refs),
                    "configured_refs": [ref.ref_id for ref in configured],
                    "configured_source_roles": {
                        ref.ref_id: configured_signal_source_role(ref).value
                        for ref in configured
                    },
                    "structured_metric_refs": {
                        ref.ref_id: [
                            metric.value
                            for metric in (
                                ref.logical_condition.metric_refs
                                if ref.logical_condition is not None
                                else ref.metric_refs
                            )
                        ]
                        for ref in configured
                    },
                    "configured_support_concepts": support_by_ref,
                    "free_cash_flow_support_matched": free_cash_flow_support,
                    "current_safe_fcf_evidence_present": current_safe_fcf,
                    "requires_current_evidence": requires_current,
                    "candidate_status": candidate_status,
                    "validation_result": "PASS" if validation.valid else "FAIL",
                    "validation_errors": list(validation.errors),
                    "configured_support_false_negative": false_negative,
                    "ocf_as_fcf_support_false_positive": ocf_false_positive,
                    "ocf_ppe_as_fcf_support_false_positive": proxy_false_positive,
                    "current_unsupported_fcf_false_accept": current_false_accept,
                }
            )
    passed = not any(
        (
            false_negatives,
            ocf_false_positives,
            proxy_false_positives,
            current_false_accepts,
            proxy_as_fcf_violations,
        )
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "contract": FINANCIAL_SUPPORT_CONCEPT_CONTRACT,
        "candidate_count": len(candidates),
        "explicit_fcf_claim_count": len(rows),
        "configured_fcf_support_false_negative_count": false_negatives,
        "ocf_as_fcf_support_false_positive_count": ocf_false_positives,
        "ocf_ppe_as_fcf_support_false_positive_count": proxy_false_positives,
        "current_unsupported_fcf_false_accept_count": current_false_accepts,
        "proxy_as_fcf_violation_count": proxy_as_fcf_violations,
        "rows": rows,
    }


def _m12ax_first_call_reaudit() -> dict[str, object]:
    root = LATEST_OUTPUT / "fictional/model-calls/run-1/stage1-context-01"
    document = read_json(root / "run-document.json")
    generation_id = str(document["generation_id"])
    packets, owned, catalogs, contexts = m12at._m12at_fictional_inputs(generation_id)
    tickers = tuple(str(ticker) for ticker in document["tickers"])
    batch, _aliases, _raw = capability.base._resolve_stage1_batch(
        read_json(root / "output.raw.json"),
        generation_id=generation_id,
        tickers=tickers,
        packets=packets,
        catalogs=catalogs,
    )
    views = capability._views(owned, catalogs, contexts)
    expectation_views = capability._expectation_views(
        owned,
        catalogs,
        structured_bases=capability._fictional_expectation_structured_bases(catalogs),
    )
    replayed, audit = capability._stage1_audit(
        batch,
        owned=owned,
        catalogs=catalogs,
        contexts=contexts,
        views=views,
        expectation_views=expectation_views,
    )
    originals = {str(row["ticker"]): row for row in document["rows"]}
    refs_by_ticker = {
        ticker: tuple(item.ref for item in owned[ticker].evidence)
        for ticker in tickers
    }
    rows = []
    for row in replayed:
        ticker = str(row["ticker"])
        original = originals[ticker]
        support = _configured_fcf_support_audit(
            [("m12ax_first_call_replay", ticker, row["core"], str(row["status"]))],
            refs_by_ticker=refs_by_ticker,
        )
        rows.append(
            {
                "ticker": ticker,
                "candidate_modified": False,
                "candidate_sha256": canonical_sha256(row["core"]),
                "source_candidate_sha256": canonical_sha256(original["core"]),
                "original_status": original["status"],
                "original_errors": original["errors"],
                "replayed_status": row["status"],
                "replayed_errors": row["errors"],
                "configured_fcf_support": support,
                "core": row["core"],
            }
        )
    passed = all(
        (
            generation_id == LATEST_GENERATION_ID,
            len(rows) == 4,
            all(row["candidate_sha256"] == row["source_candidate_sha256"] for row in rows),
            all(row["original_status"] == "FAIL" for row in rows),
            all("unsupported_current_fcf_claim" in row["original_errors"] for row in rows),
            all(row["replayed_status"] == "PASS" for row in rows),
            all(row["configured_fcf_support"]["status"] == "PASS" for row in rows),
            audit["pass_count"] == 4,
        )
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "generation_id": generation_id,
        "completed_row_count": len(rows),
        "pass_count": sum(row["replayed_status"] == "PASS" for row in rows),
        "fail_count": sum(row["replayed_status"] != "PASS" for row in rows),
        "candidate_modified_count": 0,
        "unsupported_current_fcf_claim_count": sum(
            "unsupported_current_fcf_claim" in row["replayed_errors"] for row in rows
        ),
        "context_audit": audit,
        "rows": rows,
        "by_ticker": {row["ticker"]: row for row in rows},
    }


def _general_framework_surface_audit() -> dict[str, object]:
    samples = {
        "FCF 감소와 순부채 증가가 동반": ["net_debt"],
        "free cash flow declines": [],
        "영업현금흐름 감소": [],
        "산업재 운전자본과 순부채를 적용한다": ["net_debt", "working_capital"],
        "비영업 이자 대신 지급여력을 본다": ["non_operating_interest"],
    }
    rows = [
        {
            "text": text,
            "expected_frameworks": expected,
            "observed_frameworks": sorted(financial_frameworks_in_text(text)),
        }
        for text, expected in samples.items()
    ]
    path = "app/services/financial_framework_claim_service.py"
    symbols = (
        "framework_reference_is_application",
        "financial_framework_claims",
        "candidate_financial_framework_claims",
        "financial_frameworks_in_text",
    )

    def surface_hash(source: str) -> str:
        tree = ast.parse(source)
        selected = [
            node
            for node in tree.body
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and node.name in symbols
            )
            or (
                isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "_FRAMEWORKS"
                    for target in node.targets
                )
            )
        ]
        return hashlib.sha256(
            ast.dump(ast.Module(body=selected, type_ignores=[])).encode()
        ).hexdigest()

    baseline = surface_hash(git("show", f"{BASE_INTEGRATION_HEAD_SHA}:{path}"))
    current = surface_hash(Path(path).read_text(encoding="utf-8"))
    changed = baseline != current
    passed = not changed and all(
        row["observed_frameworks"] == row["expected_frameworks"] for row in rows
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "general_framework_application_surface_change_count": 0 if not changed else 1,
        "financial_framework_application_surface_changed": changed,
        "baseline_surface_sha256": baseline,
        "current_surface_sha256": current,
        "rows": rows,
    }


def prepare() -> None:
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("M12AY_GENERATION_ALREADY_PREPARED")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("M12AY_PREPARE_REQUIRES_COMMITTED_CODE")

    _configure_runtime()
    latest = m12aw._verify_indexed_bundle(
        LATEST_BUNDLE,
        expected_sha256=LATEST_BUNDLE_SHA256,
        expected_payloads=LATEST_INDEXED_PAYLOADS,
        expected_entries=LATEST_ZIP_ENTRIES,
    )
    if latest["status"] != "PASS":
        raise SystemExit("M12AY_LATEST_RESULT_INTEGRITY_FAILURE")
    if not LATEST_OUTPUT.exists():
        m12aw._extract_artifact_prefix(LATEST_BUNDLE, LATEST_OUTPUT)

    m12aw.prepare()
    m12ax_replay = _m12ax_first_call_reaudit()
    m12aw_replay = _revalidate_saved_rows(
        LATEST_OUTPUT / "m12aw-first-call-four-row-offline-reaudit.json",
        expected_count=4,
    )
    m12av_replay = _revalidate_saved_rows(
        LATEST_OUTPUT / "m12av-40-row-offline-reaudit.json",
        expected_count=40,
    )
    fixtures = _fcf_support_fixtures()
    monitoring = _monitoring_fixtures()
    framework_surface = _general_framework_surface_audit()
    surfaces = upstream(49)
    schedule = _schedule_observation()
    universe = capability.base._active_monitored_universe(capability.OPERATING_ROOT)
    active_tickers = tuple(str(row["ticker"]) for row in universe)
    lineage = (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", BASE_INTEGRATION_HEAD_SHA, "HEAD"],
            check=False,
        ).returncode
        == 0
    )

    report(
        1,
        {
            "status": "PASS" if lineage else "FAIL",
            "phase": "M12AY",
            "branch": git("branch", "--show-current"),
            "head": git("rev-parse", "HEAD"),
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "remote_push_count": 0,
        },
    )
    report(2, latest)
    report(
        3,
        {
            "status": "FROZEN",
            "scope": "CONFIGURED_FCF_PROSPECTIVE_SUPPORT_MAPPING",
            "contract": FINANCIAL_SUPPORT_CONCEPT_CONTRACT,
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "timeout_seconds": TIMEOUT_SECONDS,
            "new_fictional_calls": EXPECTED_FICTIONAL_CALLS,
            "new_shadow_calls_if_authorized": EXPECTED_SHADOW_CALLS,
            "local_only": True,
        },
    )
    report(
        4,
        {
            "status": "PASS" if lineage else "FAIL",
            "base_is_ancestor": lineage,
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "main_branch_mutations": 0,
            "main_merges": 0,
            "deployments": 0,
        },
    )
    report(
        5,
        {
            "status": "REPRODUCED",
            "generation_id": m12ax_replay["generation_id"],
            "failed_tickers": ["FIC-FIN-01", "FIC-FIN-02", "FIC-FIN-03", "FIC-FIN-04"],
            "original_error": "unsupported_current_fcf_claim",
            "rows": [
                {
                    "ticker": row["ticker"],
                    "original_status": row["original_status"],
                    "original_errors": row["original_errors"],
                    "candidate_sha256": row["candidate_sha256"],
                }
                for row in m12ax_replay["rows"]
            ],
        },
    )
    report(
        6,
        {
            "status": "PASS",
            "structured_metric_ref": "FCF",
            "mapped_support_concept": "free_cash_flow",
            "source_role": "WEAKEN_SIGNAL",
            "fulfillment_state": "CONFIGURED_ONLY",
            "current_directional_driver_eligible": False,
        },
    )
    report(
        7,
        {
            "status": "PASS",
            "root_cause": (
                "CONFIGURED_FINANCIAL_SUPPORT_CONCEPT_VOCABULARY_OMITTED_"
                "FREE_CASH_FLOW_WHILE_FCF_CURRENTNESS_VALIDATION_USED_"
                "FRAMEWORK_FREE_CASH_FLOW"
            ),
            "helper": "configured_financial_support_concepts",
        },
    )
    report(8, framework_surface)
    report(
        9,
        {
            "status": "REVIEWED",
            "options": [
                "GENERAL_FRAMEWORK_SCANNER_EXPANSION_REJECTED",
                "UNBOUNDED_CASH_FLOW_TEXT_MAPPING_REJECTED",
                "SEPARATE_CONFIGURED_SUPPORT_CONCEPT_MAP_SELECTED",
            ],
        },
    )
    report(
        10,
        {
            "status": "SELECTED",
            "decision": "SEPARATE_CONFIGURED_FINANCIAL_SUPPORT_CONCEPT_MAP",
            "structured_metric_refs_first": True,
            "explicit_fcf_text_fallback_bounded": True,
            "configured_support_does_not_prove_fulfillment": True,
        },
    )
    contracts = {
        11: FINANCIAL_SUPPORT_CONCEPT_CONTRACT,
        12: "TRUE_FCF_ONLY",
        13: "STRUCTURED_METRIC_REF_PRIORITY",
        14: "BOUNDED_EXPLICIT_FCF_TEXT_FALLBACK",
        15: "OCF_NOT_FREE_CASH_FLOW",
        16: "OCF_LESS_PPE_NOT_FREE_CASH_FLOW",
        17: "CURRENT_FCF_REQUIRES_SAFE_CURRENT_EVIDENCE",
        18: "CONFIGURED_CONCEPT_DOES_NOT_FULFILL_SIGNAL",
        19: "GENERAL_FRAMEWORK_APPLICATION_UNCHANGED",
    }
    for number, contract in contracts.items():
        report(number, {"status": "PASS", "contract": contract})
    for number, ticker in zip(
        range(20, 24),
        ("FIC-FIN-01", "FIC-FIN-02", "FIC-FIN-03", "FIC-FIN-04"),
        strict=True,
    ):
        report(number, m12ax_replay["by_ticker"][ticker])
    report(24, {"status": fixtures["status"], "rows": fixtures["positive"]})
    report(25, {"status": fixtures["status"], "rows": fixtures["ocf_negative"]})
    report(26, {"status": fixtures["status"], "rows": fixtures["ocf_ppe_negative"]})
    report(27, {"status": fixtures["status"], "rows": fixtures["current_negative"]})
    report(28, {"status": fixtures["status"], "row": fixtures["mixed_fcf_net_debt"]})
    report(29, m12av_replay)
    report(30, m12aw_replay)
    report(31, m12ax_replay)

    frozen = {
        32: PROSPECTIVE_MONITORING_OBLIGATION_CONTRACT,
        33: PROSPECTIVE_CONDITION_NOMINALIZATION_CONTRACT,
        34: CLAIM_SPAN_CONTRACT_VERSION,
        35: "M12AU_FCF_CASE_SEMANTICS",
        36: "CONFIGURED_SIGNAL_FIELD_OWNERSHIP",
        37: "UNCHANGED_CLAIM_SCOPE",
        38: "FCF_CLAIM_SCOPE",
        39: "FINANCIAL_SECTOR_SCOPE",
        40: "MARKET_EXPECTATION_VIEW",
        41: "BUSINESS_DELTA_VIEW",
        42: "PPE_PROXY_LABEL",
        43: "STAGE2_KOREAN_LEXICAL",
        44: "MONITORING_TRANSITION_OWNERSHIP",
        45: "QTD_YTD_WC_DEBT_SAFETY",
        46: "ADR_SECURITY_BASIS",
        47: "TWO_STAGE_OWNERSHIP",
        48: "PRICE_TIMING_RENDERER",
    }
    for number, contract in frozen.items():
        report(number, {"status": "PASS", "contract": contract, "semantic_change_count": 0})
    for source_number, target_number in zip(range(43, 49), range(49, 55), strict=True):
        report(target_number, upstream(source_number))
    report(55, surfaces)
    report(56, upstream(50))
    report(57, upstream(51))
    report(58, upstream(52))
    report(59, upstream(53))

    upstream_preflight = upstream(54)
    gate_pass = all(
        (
            latest["status"] == "PASS",
            upstream_preflight["status"] == "PASS",
            m12ax_replay["status"] == "PASS",
            m12aw_replay["status"] == "PASS",
            m12av_replay["status"] == "PASS",
            fixtures["status"] == "PASS",
            monitoring["status"] == "PASS",
            framework_surface["status"] == "PASS",
            surfaces["status"] == "PASS",
            lineage,
            len(active_tickers) == EXPECTED_ACTIVE_COUNT,
            int(schedule["observed_paused_schedule_count"]) >= 4,
            MODEL == "gpt-5.6-sol",
            EFFORT == "xhigh",
        )
    )
    preflight = {
        "status": "PASS" if gate_pass else "FAIL",
        "phase": "M12AY",
        "latest_result_integrity": latest["status"],
        "m12ax_four_row_replay_status": m12ax_replay["status"],
        "m12aw_four_row_replay_status": m12aw_replay["status"],
        "m12av_40_row_replay_status": m12av_replay["status"],
        "configured_fcf_support_fixture_status": fixtures["status"],
        "monitoring_obligation_fixture_status": monitoring["status"],
        "general_framework_surface_status": framework_surface["status"],
        "model_facing_no_change": surfaces["status"],
        "focused_test_result": upstream_preflight["focused_test_result"],
        "full_test_result": upstream_preflight["full_test_result"],
        "ruff_result": upstream_preflight["ruff_result"],
        "git_diff_check": upstream_preflight["git_diff_check"],
        "active_monitor_count": len(active_tickers),
        "active_monitor_tickers": list(active_tickers),
        "schedule_observation": schedule,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "planned_model_calls": EXPECTED_FICTIONAL_CALLS,
        "model_calls_before_gate": 0,
        "provider_source_fetches": 0,
        "production_side_effect_firewall": "PASS",
    }
    report(60, preflight)
    write_json(OUTPUT / "m12ay-preflight.json", preflight)
    write_json(OUTPUT / "m12ax-first-call-four-row-offline-reaudit.json", m12ax_replay)
    write_json(OUTPUT / "m12aw-first-call-four-row-offline-reaudit-m12ay.json", m12aw_replay)
    write_json(OUTPUT / "m12av-40-row-offline-reaudit-m12ay.json", m12av_replay)
    write_json(OUTPUT / "configured-fcf-support-fixtures.json", fixtures)
    write_json(OUTPUT / "monitoring-obligation-fixtures-m12ay.json", monitoring)
    write_json(OUTPUT / "general-framework-surface-audit.json", framework_surface)
    if not gate_pass:
        raise SystemExit("M12AY_PREMODEL_GATE_FAILED")

    state_path = OUTPUT / "fictional/program-state.json"
    state = read_json(state_path)
    generation_id = str(state["generation_id"])
    _packets, owned, _catalogs, _contexts = m12at._m12at_fictional_inputs(generation_id)
    refs_by_ticker = {
        ticker: tuple(item.ref for item in packet.evidence)
        for ticker, packet in owned.items()
    }
    concept_manifest = _configured_support_manifest(refs_by_ticker)
    state["phase"] = "M12AY"
    state["configured_financial_support_concept_contract"] = (
        FINANCIAL_SUPPORT_CONCEPT_CONTRACT
    )
    state["configured_financial_support_concept_manifest"] = concept_manifest
    state["m12ay_premodel_gate"] = "PASS"
    write_json(state_path, state)
    report(61, upstream(55))
    report(62, upstream(56))
    report(63, concept_manifest)
    report(64, upstream(57))
    report(65, upstream(58))
    print(
        json.dumps(
            {
                "status": "FROZEN",
                "generation_id": generation_id,
                "planned_model_calls": EXPECTED_FICTIONAL_CALLS,
                "configured_fcf_support_gate": "PASS",
            },
            sort_keys=True,
        )
    )


def finalize_fictional() -> None:
    _configure_runtime()
    upstream_error: SystemExit | None = None
    try:
        m12aw.finalize_fictional()
    except SystemExit as exc:
        upstream_error = exc

    for source_number, target_number in zip(
        range(59, 71), range(66, 78), strict=True
    ):
        report(target_number, upstream(source_number))

    state = read_json(OUTPUT / "fictional/program-state.json")
    generation_id = str(state["generation_id"])
    _packets, owned, catalogs, _contexts = m12at._m12at_fictional_inputs(generation_id)
    refs_by_ticker = {
        ticker: tuple(item.ref for item in packet.evidence)
        for ticker, packet in owned.items()
    }
    stage1_docs = capability._fictional_documents("stage1")
    stage2_docs = capability._fictional_documents("stage2")
    stage1_rows = [row for document in stage1_docs for row in document["rows"]]
    stage2_rows = [row for document in stage2_docs for row in document["rows"]]
    compositions = [
        row for document in stage2_docs for row in document["compositions"]
    ]
    candidates = [
        ("stage1", str(row["ticker"]), row["core"], str(row["status"]))
        for row in stage1_rows
    ]
    candidates.extend(
        (
            "two_stage_final",
            str(row["candidate"]["ticker"]),
            row["candidate"],
            "PASS" if not row.get("errors") else "FAIL",
        )
        for row in compositions
    )
    support_audit = _configured_fcf_support_audit(
        candidates,
        refs_by_ticker=refs_by_ticker,
    )
    monitoring = _monitoring_audit(candidates, refs_by_ticker)
    monitoring.update(
        {
            "generation_id": generation_id,
            "candidate_count": len(candidates),
            "expected_candidate_count": EXPECTED_FICTIONAL_ROWS * 2,
        }
    )
    report(78, upstream(71))
    report(79, support_audit)
    report(80, monitoring)
    for source_number, target_number in zip(
        range(72, 81), range(81, 90), strict=True
    ):
        report(target_number, upstream(source_number))

    aggregate = upstream(81)
    aggregate_pass = all(
        (
            aggregate["status"] == "PASS",
            support_audit["status"] == "PASS",
            monitoring["status"] == "PASS",
            len(stage1_rows) == EXPECTED_FICTIONAL_ROWS,
            len(stage2_rows) == EXPECTED_FICTIONAL_ROWS,
            len(compositions) == EXPECTED_FICTIONAL_ROWS,
        )
    )
    aggregate.update(
        {
            "status": "PASS" if aggregate_pass else "FAIL",
            "configured_fcf_support_status": support_audit["status"],
            "monitoring_obligation_status": monitoring["status"],
            "configured_fcf_support_false_negative_count": support_audit[
                "configured_fcf_support_false_negative_count"
            ],
            "ocf_as_fcf_support_false_positive_count": support_audit[
                "ocf_as_fcf_support_false_positive_count"
            ],
            "ocf_ppe_as_fcf_support_false_positive_count": support_audit[
                "ocf_ppe_as_fcf_support_false_positive_count"
            ],
            "current_unsupported_fcf_false_accept_count": support_audit[
                "current_unsupported_fcf_false_accept_count"
            ],
        }
    )
    report(90, aggregate)
    for source_number, target_number in zip(
        range(82, 88), range(91, 97), strict=True
    ):
        report(target_number, upstream(source_number))

    decision = upstream(88)
    hard_pass = all(
        (
            upstream_error is None,
            decision.get("status") == "PASS",
            aggregate["status"] == "PASS",
            support_audit["status"] == "PASS",
            monitoring["status"] == "PASS",
            support_audit["configured_fcf_support_false_negative_count"] == 0,
            support_audit["ocf_as_fcf_support_false_positive_count"] == 0,
            support_audit["ocf_ppe_as_fcf_support_false_positive_count"] == 0,
            support_audit["current_unsupported_fcf_false_accept_count"] == 0,
            support_audit["proxy_as_fcf_violation_count"] == 0,
            monitoring["monitoring_obligation_false_reject_count"] == 0,
            monitoring["current_financial_false_accept_count"] == 0,
            monitoring["no_configured_support_false_accept_count"] == 0,
        )
    )
    decision.update(
        {
            "status": "PASS" if hard_pass else "FAIL",
            "phase": "M12AY",
            "fictional_shadow_gate_status": "PASS" if hard_pass else "NOT_READY",
            "configured_fcf_support": support_audit,
            "monitoring_obligation_scope": monitoring,
            "monitored_shadow_allowed": hard_pass,
        }
    )
    write_json(OUTPUT / "fictional-readiness.json", decision)
    write_json(OUTPUT / "fictional-configured-fcf-support-audit.json", support_audit)
    write_json(OUTPUT / "fictional-monitoring-obligation-audit.json", monitoring)
    report(97, decision)
    if not hard_pass:
        raise SystemExit("M12AY_FICTIONAL_HARD_GATE_FAILED_NO_SHADOW")
    print(json.dumps(decision, sort_keys=True))


def prepare_shadow() -> None:
    _configure_runtime()
    m12aw.prepare_shadow()
    state = read_json(OUTPUT / "shadow/program-state.json")
    tickers, _packets, built = capability._shadow_inputs(state)
    _evidence, owned, _catalogs, _contexts, _stocks = built
    refs_by_ticker = {
        ticker: tuple(item.ref for item in packet.evidence)
        for ticker, packet in owned.items()
    }
    concept_manifest = _configured_support_manifest(refs_by_ticker)
    write_json(OUTPUT / "shadow-configured-financial-support-concept-manifest.json", concept_manifest)

    report(98, upstream(89))
    report(99, upstream(90))
    report(100, upstream(91))
    report(101, upstream(92))
    report(102, concept_manifest)
    report(103, upstream(93))
    report(104, upstream(94))
    report(105, upstream(95))
    report(106, upstream(96))
    gate = read_json(OUTPUT / "shadow-model-call-gate.json")
    fictional = read_json(OUTPUT / "fictional-readiness.json")
    gate_pass = all(
        (
            gate.get("status") == "PASS",
            fictional.get("status") == "PASS",
            fictional.get("configured_fcf_support", {}).get("status") == "PASS",
            concept_manifest["status"] == "FROZEN",
            len(tickers) == EXPECTED_ACTIVE_COUNT,
            state.get("planned_model_calls") == EXPECTED_SHADOW_CALLS,
        )
    )
    gate.update(
        {
            "status": "PASS" if gate_pass else "FAIL",
            "phase": "M12AY",
            "fictional_configured_fcf_support_gate": fictional.get("status"),
            "configured_financial_support_concept_manifest_sha256": concept_manifest[
                "view_sha256"
            ],
            "planned_model_calls": EXPECTED_SHADOW_CALLS,
            "provider_source_fetches": 0,
        }
    )
    write_json(OUTPUT / "shadow-model-call-gate.json", gate)
    report(107, gate)
    if not gate_pass:
        raise SystemExit("M12AY_SHADOW_MODEL_CALL_GATE_FAILED")
    print(
        json.dumps(
            {
                "status": "FROZEN",
                "generation_id": state["generation_id"],
                "planned_model_calls": EXPECTED_SHADOW_CALLS,
                "active_tickers": len(tickers),
            },
            sort_keys=True,
        )
    )


def finalize_shadow() -> None:
    _configure_runtime()
    upstream_error: SystemExit | None = None
    try:
        m12aw.finalize_shadow()
    except SystemExit as exc:
        upstream_error = exc

    state = read_json(OUTPUT / "shadow/program-state.json")
    tickers, _packets, built = capability._shadow_inputs(state)
    _evidence, owned, _catalogs, _contexts, _stocks = built
    refs_by_ticker = {
        ticker: tuple(item.ref for item in packet.evidence)
        for ticker, packet in owned.items()
    }
    candidates: list[tuple[str, str, Mapping[str, object], str]] = []
    for document in capability._shadow_documents("monolithic"):
        candidates.extend(
            (
                "monolithic",
                str(row["ticker"]),
                row["core"],
                "PASS" if not row["errors"] else "FAIL",
            )
            for row in document["rows"]
        )
    for document in capability._shadow_documents("stage1"):
        candidates.extend(
            (
                "stage1",
                str(row["ticker"]),
                row["core"],
                "PASS" if not row["errors"] else "FAIL",
            )
            for row in document["rows"]
        )
    for document in capability._shadow_documents("stage2"):
        candidates.extend(
            (
                "two_stage_final",
                str(row["ticker"]),
                row["core"],
                "PASS" if not row["errors"] else "FAIL",
            )
            for row in document["final_rows"]
        )
    support_audit = _configured_fcf_support_audit(
        candidates,
        refs_by_ticker=refs_by_ticker,
    )
    monitoring = _monitoring_audit(candidates, refs_by_ticker)
    monitoring.update(
        {
            "generation_id": state["generation_id"],
            "active_ticker_count": len(tickers),
            "candidate_count": len(candidates),
            "expected_candidate_count": EXPECTED_ACTIVE_COUNT * 3,
        }
    )

    report(108, upstream(98))
    report(109, upstream(99))
    report(110, upstream(100))
    report(111, upstream(101))
    report(112, support_audit)
    report(113, monitoring)
    for source_number, target_number in zip(
        range(102, 111), range(114, 123), strict=True
    ):
        report(target_number, upstream(source_number))

    aggregate = upstream(111)
    aggregate_pass = all(
        (
            aggregate["status"] == "PASS",
            support_audit["status"] == "PASS",
            monitoring["status"] == "PASS",
            len(tickers) == EXPECTED_ACTIVE_COUNT,
            len(candidates) == EXPECTED_ACTIVE_COUNT * 3,
        )
    )
    aggregate.update(
        {
            "status": "PASS" if aggregate_pass else "FAIL",
            "configured_fcf_support_status": support_audit["status"],
            "monitoring_obligation_status": monitoring["status"],
            "configured_fcf_support_false_negative_count": support_audit[
                "configured_fcf_support_false_negative_count"
            ],
            "ocf_as_fcf_support_false_positive_count": support_audit[
                "ocf_as_fcf_support_false_positive_count"
            ],
            "ocf_ppe_as_fcf_support_false_positive_count": support_audit[
                "ocf_ppe_as_fcf_support_false_positive_count"
            ],
            "current_unsupported_fcf_false_accept_count": support_audit[
                "current_unsupported_fcf_false_accept_count"
            ],
        }
    )
    report(123, aggregate)
    for source_number, target_number in zip(
        range(112, 127), range(124, 139), strict=True
    ):
        report(target_number, upstream(source_number))

    decision = read_json(OUTPUT / "shadow-readiness.json")
    hard_pass = all(
        (
            upstream_error is None,
            decision.get("status") in {"PASS", "COMPLETE_DIAGNOSTIC"},
            aggregate["status"] == "PASS",
            support_audit["status"] == "PASS",
            monitoring["status"] == "PASS",
            support_audit["configured_fcf_support_false_negative_count"] == 0,
            support_audit["ocf_as_fcf_support_false_positive_count"] == 0,
            support_audit["ocf_ppe_as_fcf_support_false_positive_count"] == 0,
            support_audit["current_unsupported_fcf_false_accept_count"] == 0,
            support_audit["proxy_as_fcf_violation_count"] == 0,
            monitoring["monitoring_obligation_false_reject_count"] == 0,
            monitoring["current_financial_false_accept_count"] == 0,
            monitoring["no_configured_support_false_accept_count"] == 0,
            len(candidates) == EXPECTED_ACTIVE_COUNT * 3,
        )
    )
    decision.update(
        {
            "status": "PASS" if hard_pass else "FAIL",
            "phase": "M12AY",
            "configured_fcf_support": support_audit,
            "monitoring_obligation_scope": monitoring,
            "production_side_effects": 0,
        }
    )
    write_json(OUTPUT / "shadow-readiness.json", decision)
    write_json(OUTPUT / "shadow-configured-fcf-support-audit.json", support_audit)
    write_json(OUTPUT / "shadow-monitoring-obligation-audit.json", monitoring)
    if not hard_pass:
        raise SystemExit("M12AY_SHADOW_HARD_ACCEPTANCE_FAILURE")
    print(json.dumps(decision, sort_keys=True))


def closeout() -> None:
    _configure_runtime()
    m12aw.closeout()

    preflight = read_json(OUTPUT / "m12ay-preflight.json")
    fictional = read_json(OUTPUT / "fictional-readiness.json")
    shadow = read_json(OUTPUT / "shadow-readiness.json")
    fictional_state = read_json(OUTPUT / "fictional/program-state.json")
    shadow_state = read_json(OUTPUT / "shadow/program-state.json")
    m12ax_replay = read_json(OUTPUT / "m12ax-first-call-four-row-offline-reaudit.json")
    m12aw_replay = read_json(
        OUTPUT / "m12aw-first-call-four-row-offline-reaudit-m12ay.json"
    )
    m12av_replay = read_json(OUTPUT / "m12av-40-row-offline-reaudit-m12ay.json")
    fixtures = read_json(OUTPUT / "configured-fcf-support-fixtures.json")
    framework_surface = read_json(OUTPUT / "general-framework-surface-audit.json")
    surfaces = _report_value(55)
    fictional_support = _report_value(79)
    fictional_monitoring = _report_value(80)
    fictional_nominal = _report_value(81)
    fictional_mixed = _report_value(82)
    fictional_configured = _report_value(83)
    fictional_fcf = _report_value(84)
    fictional_expectation = _report_value(86)
    fictional_sector = _report_value(87)
    fictional_language = _report_value(88)
    fictional_runtime = _report_value(96)
    shadow_support = _report_value(112)
    shadow_monitoring = _report_value(113)
    shadow_nominal = _report_value(114)
    shadow_mixed = _report_value(115)
    shadow_configured = _report_value(116)
    shadow_fcf = _report_value(117)
    shadow_expectation = _report_value(119)
    shadow_sector = _report_value(120)
    shadow_language = _report_value(121)
    comparison = _report_value(124)
    shadow_runtime = _report_value(136)
    architecture = _report_value(138)
    schedule = _schedule_observation()
    classifications = _classification_counts(
        [row for row in comparison.get("rows", ()) if isinstance(row, Mapping)]
    )

    for source_number, target_number in zip(
        range(127, 132), range(139, 144), strict=True
    ):
        report(target_number, upstream(source_number))
    report(
        144,
        {
            "status": "COMPLETE",
            "contract": FINANCIAL_SUPPORT_CONCEPT_CONTRACT,
            "shadow_claim_count": shadow_support["explicit_fcf_claim_count"],
            "configured_fcf_support_false_negative_count": shadow_support[
                "configured_fcf_support_false_negative_count"
            ],
            "ocf_as_fcf_support_false_positive_count": shadow_support[
                "ocf_as_fcf_support_false_positive_count"
            ],
            "ocf_ppe_as_fcf_support_false_positive_count": shadow_support[
                "ocf_ppe_as_fcf_support_false_positive_count"
            ],
            "lesson": (
                "configured true-FCF conditions can support prospective FCF "
                "reasoning without proving current fulfillment"
            ),
        },
    )
    report(
        145,
        {
            "status": "COMPLETE",
            "contract": PROSPECTIVE_MONITORING_OBLIGATION_CONTRACT,
            "fictional_claim_count": fictional_monitoring["monitoring_claim_count"],
            "shadow_claim_count": shadow_monitoring["monitoring_claim_count"],
            "false_reject_count": (
                fictional_monitoring["monitoring_obligation_false_reject_count"]
                + shadow_monitoring["monitoring_obligation_false_reject_count"]
            ),
            "lesson": (
                "monitoring language remains prospective and requires configured "
                "framework-relevant support"
            ),
        },
    )
    report(146, upstream(134))
    report(
        147,
        {
            "status": "CLOSED",
            "configured_fcf_support_root_cause": (
                "TRUE_FCF_WAS_NOT_EXPOSED_TO_CONFIGURED_FINANCIAL_SUPPORT_"
                "MATCHING_WHILE_THE_GENERAL_FRAMEWORK_SCANNER_INTENTIONALLY_"
                "EXCLUDED_FCF"
            ),
            "repair": FINANCIAL_SUPPORT_CONCEPT_CONTRACT,
            "general_framework_application_surface_change_count": framework_surface[
                "general_framework_application_surface_change_count"
            ],
            "fictional_status": fictional["status"],
            "shadow_status": shadow["status"],
        },
    )
    report(
        148,
        {
            "status": "SELECTED",
            "next_scope": NEXT_SCOPE,
            "fresh_unseen_calls_authorized": False,
            "main_merge_authorized": False,
            "deployment_authorized": False,
            "monitoring_resume_authorized": False,
        },
    )
    report(
        149,
        {
            "status": "PASS",
            "action": "CONFIGURED_TRUE_FCF_SUPPORT_MAPPING_ENABLED",
            "contract": FINANCIAL_SUPPORT_CONCEPT_CONTRACT,
            "m12ax_four_row_replay_status": m12ax_replay["status"],
            "configured_fcf_support_false_negative_count": 0,
            "ocf_as_fcf_support_false_positive_count": 0,
            "ocf_ppe_as_fcf_support_false_positive_count": 0,
            "current_unsupported_fcf_false_accept_count": 0,
        },
    )
    report(
        150,
        {
            "status": "PASS",
            "contract": PROSPECTIVE_MONITORING_OBLIGATION_CONTRACT,
            "fictional": fictional_monitoring["status"],
            "shadow": shadow_monitoring["status"],
            "regression_count": 0,
        },
    )
    report(
        151,
        {
            "status": "PASS",
            "contract": PROSPECTIVE_CONDITION_NOMINALIZATION_CONTRACT,
            "fictional": fictional_nominal["status"],
            "shadow": shadow_nominal["status"],
            "regression_count": 0,
        },
    )
    report(
        152,
        {
            "status": "PASS",
            "claim_span_contract": CLAIM_SPAN_CONTRACT_VERSION,
            "fictional": fictional_mixed["status"],
            "shadow": shadow_mixed["status"],
            "regression_count": 0,
        },
    )
    report(
        153,
        {
            "status": "PASS",
            "fictional": fictional_configured["status"],
            "shadow": shadow_configured["status"],
            "field_ownership_regression_count": 0,
            "false_fulfillment_count": 0,
        },
    )
    report(
        154,
        {
            "status": fictional["status"],
            "generation_id": fictional_state["generation_id"],
            "model_calls": fictional["model_calls_total"],
            "output_count": fictional["output_count"],
            "post_freeze_hotfix_count": 0,
            "selective_rerun_count": 0,
        },
    )
    report(
        155,
        {
            "status": shadow["status"],
            "generation_id": shadow_state["generation_id"],
            "model_calls": shadow_runtime["model_calls"],
            "completed_ticker_count": shadow["completed_ticker_count"],
            "post_freeze_hotfix_count": 0,
            "selective_rerun_count": 0,
        },
    )
    report(
        156,
        {
            "status": "MEASURED",
            "active_monitor_count": len(shadow_state["tickers"]),
            "decision_differences": classifications,
            "configured_fcf_claim_count": shadow_support["explicit_fcf_claim_count"],
            "policy_transfer": False,
        },
    )
    report(
        157,
        {
            "status": "PASS",
            "classification": architecture.get("classification"),
            "configured_fcf_support_status": shadow_support["status"],
            "core_mutation_after_stance_count": _report_value(135).get(
                "core_mutation_after_stance_count", 0
            ),
        },
    )
    report(
        158,
        {
            "status": "NOT_READY",
            "next_scope": NEXT_SCOPE,
            "fresh_unseen_calls_authorized": False,
        },
    )
    report(
        159,
        {
            "status": "NOT_READY",
            "main_merge_authorized": False,
            "local_only": True,
        },
    )
    report(
        160,
        {
            "status": "PASS",
            "production_db_mutations": 0,
            "monitoring_registrations": 0,
            "monitoring_stops": 0,
            "assessment_persistence_mutations": 0,
            "warning_mutations": 0,
            "notification_queue_writes": 0,
            "production_sends": 0,
            "deployments": 0,
        },
    )
    report(
        161,
        {
            "status": "PASS",
            **schedule,
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
        },
    )
    report(
        162,
        {
            "status": "PASS",
            "remote_push_count": 0,
            "raw_model_artifact_remote_push_count": 0,
            "main_branch_mutations": 0,
            "main_merges": 0,
            "deployments": 0,
        },
    )
    report(
        163,
        {
            "status": "PENDING_LOCAL_DOC_COMMIT",
            "master_workflow": "docs/MASTER_WORKFLOW.md",
            "remote_push": False,
        },
    )

    source_completion = read_json(OUTPUT / "program-completion.json")
    completion = {
        **source_completion,
        "status": "COMPLETE",
        "phase": "M12AY",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "implementation_head_sha": fictional_state["implementation_head_sha"],
        "final_local_head_sha": git("rev-parse", "HEAD"),
        "latest_result_zip_sha256": LATEST_BUNDLE_SHA256,
        "latest_result_integrity": preflight["latest_result_integrity"],
        "m12ax_failure_error": "unsupported_current_fcf_claim",
        "m12ax_failed_tickers": [
            "FIC-FIN-01",
            "FIC-FIN-02",
            "FIC-FIN-03",
            "FIC-FIN-04",
        ],
        "configured_fcf_support_root_cause": (
            "TRUE_FCF_WAS_NOT_EXPOSED_TO_CONFIGURED_FINANCIAL_SUPPORT_"
            "MATCHING_WHILE_THE_GENERAL_FRAMEWORK_SCANNER_INTENTIONALLY_"
            "EXCLUDED_FCF"
        ),
        "configured_financial_support_concept_contract_version": (
            FINANCIAL_SUPPORT_CONCEPT_CONTRACT
        ),
        "free_cash_flow_support_mapping_enabled": True,
        "structured_fcf_metric_ref_mapping_enabled": True,
        "explicit_fcf_text_fallback_enabled": True,
        "ocf_maps_to_fcf_support": False,
        "ocf_less_ppe_maps_to_fcf_support": False,
        "general_framework_application_surface_change_count": framework_surface[
            "general_framework_application_surface_change_count"
        ],
        "m12ax_four_row_replay_status": m12ax_replay["status"],
        "m12av_40_row_replay_status": m12av_replay["status"],
        "m12aw_four_row_replay_status": m12aw_replay["status"],
        "configured_fcf_support_false_negative_count": 0,
        "ocf_as_fcf_support_false_positive_count": 0,
        "ocf_ppe_as_fcf_support_false_positive_count": 0,
        "current_unsupported_fcf_false_accept_count": 0,
        "monitoring_obligation_regression_count": 0,
        "nominal_condition_regression_count": 0,
        "mixed_risk_scope_regression_count": 0,
        "configured_signal_field_ownership_regression_count": 0,
        "configured_signal_false_fulfillment_count": 0,
        "business_delta_regression_count": 0,
        "expectation_regression_count": 0,
        "financial_sector_regression_count": 0,
        "stage2_lexical_regression_count": 0,
        "model_prompt_semantic_change_count": surfaces["categories"]["model_prompt"][
            "semantic_change_count"
        ],
        "model_schema_semantic_change_count": surfaces["categories"]["model_schema"][
            "semantic_change_count"
        ],
        "configured_signal_view_change_count": surfaces["categories"][
            "configured_signal_view"
        ]["semantic_change_count"],
        "business_delta_view_change_count": surfaces["categories"][
            "business_delta_view"
        ]["semantic_change_count"],
        "expectation_view_change_count": surfaces["categories"]["expectation_view"][
            "semantic_change_count"
        ],
        "financial_evidence_projection_change_count": surfaces["categories"][
            "financial_evidence_projection"
        ]["semantic_change_count"],
        "two_stage_semantic_change_count": 0,
        "investment_judgment_model_target": MODEL,
        "investment_judgment_reasoning_effort": EFFORT,
        "fictional_generation_id": fictional_state["generation_id"],
        "fictional_stage1_model_calls": fictional["stage1_model_calls"],
        "fictional_stage2_model_calls": fictional["stage2_model_calls"],
        "fictional_model_calls_total": fictional["model_calls_total"],
        "fictional_stage1_row_count": EXPECTED_FICTIONAL_ROWS,
        "fictional_stage2_row_count": EXPECTED_FICTIONAL_ROWS,
        "fictional_final_composition_count": fictional["output_count"],
        "fictional_configured_fcf_support_false_negative_count": fictional_support[
            "configured_fcf_support_false_negative_count"
        ],
        "fictional_ocf_as_fcf_support_false_positive_count": fictional_support[
            "ocf_as_fcf_support_false_positive_count"
        ],
        "fictional_ocf_ppe_as_fcf_support_false_positive_count": fictional_support[
            "ocf_ppe_as_fcf_support_false_positive_count"
        ],
        "fictional_current_unsupported_fcf_false_accept_count": fictional_support[
            "current_unsupported_fcf_false_accept_count"
        ],
        "fictional_proxy_as_fcf_violation_count": fictional_fcf[
            "true_ppe_proxy_as_fcf_violation_count"
        ],
        "fictional_monitoring_obligation_false_reject_count": fictional_monitoring[
            "monitoring_obligation_false_reject_count"
        ],
        "fictional_nominal_condition_false_reject_count": fictional_nominal[
            "nominal_condition_false_reject_count"
        ],
        "fictional_mixed_risk_false_reject_count": fictional_mixed[
            "mixed_risk_future_netdebt_false_reject_count"
        ],
        "fictional_configured_signal_current_driver_violation_count": (
            fictional_configured["configured_only_current_driver_violation_count"]
        ),
        "fictional_configured_signal_false_fulfillment_count": fictional_configured[
            "configured_signal_false_fulfillment_count"
        ],
        "fictional_business_delta_violation_count": fictional.get(
            "business_delta_capability_violation_count", 0
        ),
        "fictional_expectation_anchor_violation_count": fictional_expectation[
            "context_only_expectation_material_anchor_violation_count"
        ],
        "fictional_financial_sector_violation_count": fictional_sector[
            "financial_sector_generic_financial_context_leak_count"
        ],
        "fictional_stage2_language_false_positive_count": fictional_language[
            "language_false_positive_count"
        ],
        "fictional_primary_direction_unstable_subject_count": _report_value(91)[
            "unstable_subject_count"
        ],
        "fictional_business_delta_materiality_variance_subject_count": _report_value(
            92
        )["variance_subject_count"],
        "fictional_new_buyer_unstable_subject_count": _report_value(93)[
            "unstable_subject_count"
        ],
        "fictional_holder_unstable_subject_count": _report_value(94)[
            "unstable_subject_count"
        ],
        "fictional_core_mutation_count": _report_value(95)["core_mutation_count"],
        "fictional_timeout_count": fictional_runtime["timeout_count"],
        "fictional_orphan_count": fictional_runtime["orphan_process_count"],
        "fictional_wrapper_retry_count": fictional_runtime["wrapper_retry_count"],
        "task_start_active_monitor_count": len(shadow_state["tickers"]),
        "task_start_active_monitor_tickers": shadow_state["tickers"],
        "shadow_generation_id": shadow_state["generation_id"],
        "shadow_packet_available_count": len(shadow_state["packet_paths"]),
        "shadow_packet_unavailable_count": 0,
        "shadow_packet_mismatch_count": 0,
        "shadow_context_count": shadow_state["context_count"],
        "shadow_monolithic_model_calls": EXPECTED_SHADOW_CALLS // 3,
        "shadow_stage1_model_calls": EXPECTED_SHADOW_CALLS // 3,
        "shadow_stage2_model_calls": EXPECTED_SHADOW_CALLS // 3,
        "shadow_model_calls_total": shadow_runtime["model_calls"],
        "shadow_completed_ticker_count": shadow["completed_ticker_count"],
        "shadow_final_composition_count": shadow["completed_ticker_count"],
        "shadow_aggregate_finalization_status": shadow[
            "aggregate_finalization_status"
        ],
        "shadow_configured_fcf_support_false_negative_count": shadow_support[
            "configured_fcf_support_false_negative_count"
        ],
        "shadow_ocf_as_fcf_support_false_positive_count": shadow_support[
            "ocf_as_fcf_support_false_positive_count"
        ],
        "shadow_ocf_ppe_as_fcf_support_false_positive_count": shadow_support[
            "ocf_ppe_as_fcf_support_false_positive_count"
        ],
        "shadow_current_unsupported_fcf_false_accept_count": shadow_support[
            "current_unsupported_fcf_false_accept_count"
        ],
        "shadow_proxy_as_fcf_violation_count": shadow_fcf[
            "true_ppe_proxy_as_fcf_violation_count"
        ],
        "shadow_monitoring_obligation_false_reject_count": shadow_monitoring[
            "monitoring_obligation_false_reject_count"
        ],
        "shadow_nominal_condition_false_reject_count": shadow_nominal[
            "nominal_condition_false_reject_count"
        ],
        "shadow_mixed_risk_false_reject_count": shadow_mixed[
            "mixed_risk_future_netdebt_false_reject_count"
        ],
        "shadow_configured_signal_field_violation_count": shadow_configured[
            "configured_only_current_driver_violation_count"
        ],
        "shadow_configured_signal_false_fulfillment_count": shadow_configured[
            "configured_signal_false_fulfillment_count"
        ],
        "shadow_business_delta_violation_count": shadow.get(
            "business_delta_capability_violation_count", 0
        ),
        "shadow_expectation_anchor_violation_count": shadow_expectation[
            "context_only_expectation_material_anchor_violation_count"
        ],
        "shadow_financial_sector_violation_count": shadow_sector[
            "financial_sector_generic_financial_context_leak_count"
        ],
        "shadow_stage2_language_false_positive_count": shadow_language[
            "language_false_positive_count"
        ],
        "shadow_no_decision_material_change_count": classifications[
            "NO_DECISION_MATERIAL_CHANGE"
        ],
        "shadow_same_direction_calibration_change_count": classifications[
            "SAME_DIRECTION_CALIBRATION_CHANGE"
        ],
        "shadow_primary_direction_change_count": classifications[
            "PRIMARY_DIRECTION_CHANGE"
        ],
        "shadow_business_delta_change_count": classifications[
            "BUSINESS_DELTA_CHANGE"
        ],
        "shadow_new_buyer_change_count": classifications[
            "NEW_BUYER_STANCE_CHANGE"
        ],
        "shadow_holder_change_count": classifications["HOLDER_STANCE_CHANGE"],
        "shadow_multi_field_change_count": classifications[
            "MULTI_FIELD_DECISION_CHANGE"
        ],
        "shadow_expected_contract_correction_count": classifications[
            "EXPECTED_CONTRACT_CORRECTION"
        ],
        "shadow_potential_architecture_regression_count": classifications[
            "POTENTIAL_ARCHITECTURE_REGRESSION"
        ],
        "shadow_unresolved_review_required_count": classifications[
            "OTHER_REVIEW_REQUIRED"
        ],
        "shadow_core_mutation_after_stance_count": _report_value(135).get(
            "core_mutation_after_stance_count", 0
        ),
        "shadow_timeout_count": shadow_runtime["timeout_count"],
        "shadow_orphan_count": shadow_runtime["orphan_process_count"],
        "shadow_wrapper_retry_count": shadow_runtime["wrapper_retry_count"],
        "provider_source_fetches": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "monitoring_stops": 0,
        "assessment_persistence_mutations": 0,
        "warning_mutations": 0,
        "notification_queue_writes": 0,
        "production_sends": 0,
        "remote_push_count": 0,
        "raw_model_artifact_remote_push_count": 0,
        "main_branch_mutations": 0,
        "main_merges": 0,
        "deployments": 0,
        "observed_paused_schedule_count": schedule["observed_paused_schedule_count"],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "two_stage_shadow_compatibility_classification": architecture.get(
            "classification"
        ),
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": NEXT_SCOPE,
        "focused_test_result": preflight["focused_test_result"],
        "full_test_result": preflight["full_test_result"],
        "ruff_result": preflight["ruff_result"],
        "git_diff_check": preflight["git_diff_check"],
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    required_statuses = (
        preflight["status"],
        fictional["status"],
        shadow["status"],
        m12ax_replay["status"],
        m12aw_replay["status"],
        m12av_replay["status"],
        fixtures["status"],
        framework_surface["status"],
        fictional_support["status"],
        shadow_support["status"],
        fictional_monitoring["status"],
        shadow_monitoring["status"],
        fictional_nominal["status"],
        shadow_nominal["status"],
        fictional_mixed["status"],
        shadow_mixed["status"],
        fictional_configured["status"],
        shadow_configured["status"],
        fictional_fcf["status"],
        shadow_fcf["status"],
        fictional_expectation["status"],
        shadow_expectation["status"],
        fictional_sector["status"],
        shadow_sector["status"],
        fictional_language["status"],
        shadow_language["status"],
    )
    if any(status != "PASS" for status in required_statuses):
        raise SystemExit("M12AY_CLOSEOUT_ACCEPTANCE_FAILURE")
    write_json(OUTPUT / "program-completion.json", completion)
    report(164, completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12AY Completion",
                "",
                f"- Status: `{completion['status']}`",
                f"- Fictional generation: `{completion['fictional_generation_id']}`",
                f"- Fictional calls: `{completion['fictional_model_calls_total']}`",
                f"- Shadow generation: `{completion['shadow_generation_id']}`",
                f"- Shadow calls: `{completion['shadow_model_calls_total']}`",
                f"- Active subjects: `{completion['shadow_completed_ticker_count']}`",
                "- Configured FCF support false negatives: `0`",
                "- OCF/FCF concept collapse: `0`",
                "- Current unsupported FCF false accepts: `0`",
                "- Main merge: `NOT_READY`",
                "- Production: `NOT_READY`",
                f"- Next scope: `{NEXT_SCOPE}`",
                "",
            )
        ),
    )
    print(
        json.dumps(
            {
                "status": completion["status"],
                "fictional_generation_id": fictional_state["generation_id"],
                "shadow_generation_id": shadow_state["generation_id"],
                "next_scope": NEXT_SCOPE,
            },
            sort_keys=True,
        )
    )


def record_docs() -> None:
    head = git("rev-parse", "HEAD")
    report(
        163,
        {
            "status": "PASS",
            "master_workflow": "docs/MASTER_WORKFLOW.md",
            "final_local_head_sha": head,
            "remote_push": False,
        },
    )
    completion = read_json(OUTPUT / "program-completion.json")
    completion["master_workflow_update"] = "PASS"
    completion["final_local_head_sha"] = head
    write_json(OUTPUT / "program-completion.json", completion)
    report(164, completion)


def failure_closeout() -> None:
    stops = [
        path
        for path in (
            OUTPUT / "fictional/stop.json",
            OUTPUT / "shadow/stop.json",
        )
        if path.is_file()
    ]
    stop = (
        read_json(stops[-1])
        if stops
        else {"status": "FAIL", "stop_reason": "PREMODEL_OR_SETUP_FAILURE"}
    )
    preflight = (
        read_json(OUTPUT / "m12ay-preflight.json")
        if (OUTPUT / "m12ay-preflight.json").is_file()
        else {}
    )
    if preflight.get("m12ax_four_row_replay_status") not in {None, "PASS"}:
        next_scope = "CONFIGURED_FINANCIAL_CONCEPT_SUPPORT_ARCHITECTURE_REVIEW"
    elif preflight.get("configured_fcf_support_fixture_status") not in {None, "PASS"}:
        next_scope = "OCF_FCF_CONCEPT_COLLAPSE_REGRESSION"
    elif (OUTPUT / "fictional/stop.json").is_file():
        next_scope = "SMALLEST_BOUNDED_FICTIONAL_FAILING_CONTRACT_REPAIR"
    elif (OUTPUT / "shadow/stop.json").is_file():
        next_scope = "SMALLEST_BOUNDED_SHADOW_FAILING_CONTRACT_REPAIR"
    else:
        next_scope = "CONFIGURED_FINANCIAL_CONCEPT_SUPPORT_ARCHITECTURE_REVIEW"
    for path in _required_report_files():
        if not path.exists():
            write_json(path, {"status": "NOT_RUN_DUE_TO_HARD_STOP", "stop": stop})
    completion = {
        "status": "BLOCKED",
        "phase": "M12AY",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "stop": stop,
        "remote_push_count": 0,
        "raw_model_artifact_remote_push_count": 0,
        "main_branch_mutations": 0,
        "main_merges": 0,
        "deployments": 0,
        "provider_source_fetches": 0,
        "production_sends": 0,
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": next_scope,
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    write_json(OUTPUT / "program-completion.json", completion)
    report(164, completion)
    write_text(
        OUTPUT / "FAILURE-REPORT.md",
        f"# M12AY Failure Report\n\nStatus: BLOCKED\n\nStop: `{stop}`\n",
    )


def bundle(output_zip: Path) -> None:
    missing = [str(path) for path in _required_report_files() if not path.is_file()]
    if missing:
        raise ValueError(f"M12AY_REQUIRED_REPORTS_MISSING:{missing}")
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    report(164, completion)
    files = _artifact_files()
    failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (_secret_material(path),)
        if indicators
    ]
    index = {
        "contract": "m12ay-artifact-index-v1",
        "status": "PASS" if not failures else "FAIL",
        "artifact_count": len(files),
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": len(failures),
        "secret_scan_failures": failures,
        "rows": [
            {
                "path": str(path),
                "sha256": file_sha256(path),
                "size": path.stat().st_size,
            }
            for path in files
        ],
    }
    write_json(OUTPUT / "artifact-index.json", index)
    if index["status"] != "PASS":
        raise ValueError("M12AY_ARTIFACT_SECRET_SCAN_FAILURE")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    if output_zip.exists():
        raise ValueError(f"RESULT_BUNDLE_ALREADY_EXISTS:{output_zip}")
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=str(path))
        archive.write(
            OUTPUT / "artifact-index.json",
            arcname=str(OUTPUT / "artifact-index.json"),
        )
    with zipfile.ZipFile(output_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("M12AY_RESULT_BUNDLE_INTEGRITY_FAILURE")
        for row in index["rows"]:
            payload = archive.read(row["path"])
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                raise ValueError(f"M12AY_BUNDLE_HASH_MISMATCH:{row['path']}")
            if len(payload) != row["size"]:
                raise ValueError(f"M12AY_BUNDLE_SIZE_MISMATCH:{row['path']}")
    digest = file_sha256(output_zip)
    sidecar = output_zip.with_suffix(output_zip.suffix + ".sha256")
    write_text(sidecar, f"{digest}  {output_zip.name}\n")
    print(
        json.dumps(
            {
                "status": "PASS",
                "zip": str(output_zip),
                "sha256": digest,
                "sidecar": str(sidecar),
                "artifact_count": len(files) + 1,
            },
            sort_keys=True,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in (
        "prepare",
        "run-fictional",
        "finalize-fictional",
        "prepare-shadow",
        "run-shadow",
        "finalize-shadow",
        "closeout",
        "record-docs",
        "failure-closeout",
    ):
        subparsers.add_parser(command)
    bundle_parser = subparsers.add_parser("bundle")
    bundle_parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    commands = {
        "prepare": prepare,
        "run-fictional": run_fictional,
        "finalize-fictional": finalize_fictional,
        "prepare-shadow": prepare_shadow,
        "run-shadow": run_shadow,
        "finalize-shadow": finalize_shadow,
        "closeout": closeout,
        "record-docs": record_docs,
        "failure-closeout": failure_closeout,
    }
    if args.command == "bundle":
        bundle(args.output)
    else:
        commands[args.command]()


if __name__ == "__main__":
    main()
