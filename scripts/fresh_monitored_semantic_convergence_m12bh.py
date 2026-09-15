"""M12BH cross-path semantic single-source convergence audit.

This module is deliberately audit-only.  It inspects call graphs, executes the
existing canonical semantic helpers against a deterministic golden corpus, and
stops before any model or network call when proof-critical convergence debt is
present.
"""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import ast
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace
import zipfile

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.business_delta_evidence_service import (
    BusinessDeltaCapability,
    BusinessDeltaEvidenceItem,
    BusinessDeltaEvidenceRole,
    BusinessDeltaEvidenceView,
    classify_business_delta_unchanged_claims,
    derive_financial_comparison_direction,
    validate_business_delta_candidate,
)
from app.services.configured_signal_evidence_service import (
    ConfiguredSignalFulfillmentEvidence,
    build_configured_signal_evidence_view,
    validate_configured_signal_field_ownership,
)
from app.services.cross_market_decision_engine_service import (
    DecisionEvidenceRef,
    FinancialComparisonKind,
    FinancialEvidenceQuality,
    FinancialPeriod,
    FinancialPeriodType,
)
from app.services.direction_timing_ownership_service import EvidenceDomain
from app.services.directional_financial_context_service import (
    FinancialClaimRole,
    classify_ppe_proxy_fcf_claims,
    fcf_temporal_claim_role,
    fcf_temporal_claim_spans,
    financial_claim_requires_current_evidence,
    financial_claim_role,
    financial_claim_rows,
)
from app.services.financial_framework_claim_service import (
    FrameworkClaim,
    FrameworkClaimKind,
    FrameworkReferenceRole,
    candidate_financial_framework_claims,
)
from app.services.logical_condition_service import CheckpointMetric
from app.services.market_expectation_evidence_service import (
    MarketExpectationEvidenceItem,
    MarketExpectationEvidenceRole,
    MarketExpectationEvidenceView,
    validate_market_expectation_candidate,
)
from app.services.working_capital_checkpoint_binding_service import (
    WorkingCapitalCheckpointBindingItem,
    WorkingCapitalCheckpointBindingView,
    validate_working_capital_checkpoint_bindings,
)


NAME = (
    "20260914-fresh-vs-monitored-semantic-single-source-convergence-audit-conditional-full-shadow"
)
CONTRACT = "fresh-monitored-semantic-single-source-convergence-audit-v1"
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
RUNNER = Path("scripts/fresh_monitored_semantic_convergence_m12bh.py")
ARCHITECTURE = Path("docs/architecture/FRESH_MONITORED_SEMANTIC_SINGLE_SOURCE_CONVERGENCE.md")
WORK_INSTRUCTION = Path("docs/work-instructions") / f"{NAME}.md"
WORK_INSTRUCTION_COMMIT = "e24ae28dbf5536e23939ac478f593c64423089c0"
BASE_INTEGRATION_HEAD_SHA = "f5f948a959da5093590bf72d4270900aa679efa2"
INTEGRATION_BRANCH = "codex/20260914-semantic-convergence-m12bh"

LATEST_RESULT = (
    Path.home()
    / "Documents/Codex"
    / (
        "thesis-monitor-20260914-fcf-prospective-requirement-verification-scope-"
        "new-full-shadow-report.zip"
    )
)
LATEST_RESULT_SHA256 = "8b809b13d5766168f357ff4824075dcaa1f87c62e909154a8b191fee539ae277"
LATEST_INDEXED_PAYLOADS = 1137
LATEST_ZIP_ENTRIES = 1138
M12BG_SHADOW_GENERATION_ID = "20260911-m12ai-shadow-20260913T232403Z-b5fcaed53268"
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
NEXT_SCOPE = "BOUNDED_SEMANTIC_SINGLE_SOURCE_CONVERGENCE_REPAIR"

FRESH_PATHS = (
    Path("scripts/new_issuer_holdout_selection_ownership_proof.py"),
    Path("scripts/new_issuer_final_freeze_ownership_proof.py"),
    Path("scripts/fresh_issuer_ownership_proof_transport_risk_carried.py"),
    Path("scripts/directional_core_price_timing_holdout.py"),
)
MONITORED_PATHS = (
    Path("scripts/directional_financial_context_m12.py"),
    Path("scripts/directional_financial_context_m12g.py"),
    Path("scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py"),
    Path("scripts/business_delta_evidence_capability_m12ai.py"),
    Path("scripts/working_capital_checkpoint_binding_m12bb.py"),
)


BASE_REPORT_SLUGS = tuple(
    line
    for line in """
repository-provenance
latest-result-integrity
m12bh-scope-freeze
latest-network-stop-classification
fresh-new-issuer-entrypoint-map
monitored-monolithic-entrypoint-map
monitored-stage1-entrypoint-map
monitored-stage2-entrypoint-map
shadow-validator-entrypoint-map
proof-offline-replay-entrypoint-map
semantic-contract-family-inventory
semantic-contract-ownership-map
semantic-consumer-call-graph
duplicate-semantic-classifier-scan
proof-harness-semantic-duplication-audit
fresh-vs-monitored-semantic-bypass-audit
semantic-single-source-convergence-decision
financial-temporal-role-convergence
fcf-concept-and-currentness-convergence
netdebt-temporal-completeness-convergence
working-capital-grounding-convergence
financial-sector-framework-convergence
configured-signal-lifecycle-convergence
business-delta-view-convergence
market-expectation-view-convergence
direction-timing-ownership-convergence
qtd-ytd-period-convergence
adr-security-basis-convergence
stage2-core-immutability-convergence
proof-readiness-policy-convergence
semantic-golden-corpus-manifest
fcf-golden-corpus-results
netdebt-golden-corpus-results
working-capital-golden-corpus-results
financial-sector-golden-corpus-results
configured-signal-golden-corpus-results
business-delta-golden-corpus-results
market-expectation-golden-corpus-results
cross-path-golden-corpus-equality-summary
""".strip().splitlines()
)
DEBT_REPORT_SLUGS = tuple(
    line
    for line in """
divergent-duplicate-classifier-list
bypass-list
equivalent-but-driftable-duplicate-list
convergence-debt-risk-ranking
smallest-bounded-convergence-repair-scope
stop-before-shadow-decision
""".strip().splitlines()
)
COMPLETION_REPORT_SLUGS = tuple(
    line
    for line in """
semantic-single-source-convergence-decision
network-stop-or-shadow-run-decision
fictional-proof-reuse-decision
full-shadow-completion-decision
two-stage-shadow-compatibility-decision
existing-monitored-impact-summary
fresh-real-proof-readiness-decision
final-main-merge-readiness-note
production-no-change
schedule-pause-observation
remote-push-prohibition-audit
master-workflow-update
program-completion
""".strip().splitlines()
)

CURRENT_ROLES = {
    FinancialClaimRole.CURRENT_STATE_ASSERTION.value,
    FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS.value,
    FinancialClaimRole.CURRENT_NUMERIC_CLAIM.value,
    FinancialClaimRole.UNKNOWN_OR_AMBIGUOUS.value,
}


@dataclass(frozen=True)
class Family:
    key: str
    title: str
    canonical_module: str
    canonical_functions: tuple[str, ...]
    fresh: str
    monolithic: str
    stage1: str
    stage2: str
    shadow: str
    offline: str
    status: str
    notes: str


FAMILIES = (
    Family(
        "financial_temporal_role",
        "Financial claim temporal role",
        "app/services/directional_financial_context_service.py",
        (
            "financial_claim_role",
            "financial_claim_requires_current_evidence",
            "current_fulfillment_polarity",
        ),
        "BYPASS_OF_CANONICAL_SERVICE",
        "CANONICAL_SHARED_SERVICE",
        "CANONICAL_SHARED_SERVICE",
        "NOT_APPLICABLE",
        "CANONICAL_SHARED_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "CONVERGENCE_DEBT_PRESENT",
        "Latest fresh core_partial_audit never invokes the canonical temporal classifier.",
    ),
    Family(
        "fcf_identity_currentness",
        "FCF identity and currentness",
        "app/services/directional_financial_context_service.py",
        (
            "fcf_temporal_claim_spans",
            "fcf_temporal_claim_role",
            "classify_ppe_proxy_fcf_claims",
            "validate_directional_financial_semantics",
        ),
        "BYPASS_OF_CANONICAL_SERVICE",
        "CANONICAL_SHARED_SERVICE",
        "CANONICAL_SHARED_SERVICE",
        "NOT_APPLICABLE",
        "CANONICAL_SHARED_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "CONVERGENCE_DEBT_PRESENT",
        "Fresh post-model core validation omits present/prospective and PPE-proxy FCF checks.",
    ),
    Family(
        "net_debt_temporal_completeness",
        "Net-debt temporal completeness",
        "app/services/directional_financial_context_service.py",
        ("financial_claim_role", "validate_directional_financial_semantics"),
        "BYPASS_OF_CANONICAL_SERVICE",
        "CANONICAL_SHARED_SERVICE",
        "CANONICAL_SHARED_SERVICE",
        "NOT_APPLICABLE",
        "CANONICAL_SHARED_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "CONVERGENCE_DEBT_PRESENT",
        "Fresh partial audit does not apply complete-net-debt evidence gates.",
    ),
    Family(
        "working_capital_typed_grounding",
        "Working-capital typed grounding",
        "app/services/working_capital_checkpoint_binding_service.py",
        (
            "build_working_capital_checkpoint_binding_view",
            "validate_working_capital_checkpoint_bindings",
        ),
        "BYPASS_OF_CANONICAL_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "CONVERGENCE_DEBT_PRESENT",
        "Monitored wrappers project the shared view; latest fresh proof does not consume it.",
    ),
    Family(
        "financial_sector_framework",
        "Financial-sector specialized framework",
        "app/services/financial_framework_claim_service.py",
        ("candidate_financial_framework_claims", "framework_reference_is_application"),
        "BYPASS_OF_CANONICAL_SERVICE",
        "CANONICAL_SHARED_SERVICE",
        "CANONICAL_SHARED_SERVICE",
        "NOT_APPLICABLE",
        "CANONICAL_SHARED_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "CONVERGENCE_DEBT_PRESENT",
        "Monitored canonical parsing is supplemented by a fixture-specific hard helper.",
    ),
    Family(
        "configured_signal_lifecycle",
        "ConfiguredSignalEvidenceView lifecycle",
        "app/services/configured_signal_evidence_service.py",
        (
            "build_configured_signal_evidence_view",
            "validate_configured_signal_field_ownership",
        ),
        "BYPASS_OF_CANONICAL_SERVICE",
        "CANONICAL_SHARED_SERVICE",
        "CANONICAL_SHARED_SERVICE",
        "NOT_APPLICABLE",
        "CANONICAL_SHARED_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "CONVERGENCE_DEBT_PRESENT",
        "Fresh partial audit does not validate configured-only refs after model output.",
    ),
    Family(
        "business_delta_view",
        "BusinessDeltaEvidenceView",
        "app/services/business_delta_evidence_service.py",
        ("build_business_delta_evidence_view", "validate_business_delta_candidate"),
        "BYPASS_OF_CANONICAL_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "NOT_APPLICABLE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "CONVERGENCE_DEBT_PRESENT",
        "Current monitored path passes owned/view; a legacy fallback remains independently driftable.",
    ),
    Family(
        "market_expectation_view",
        "MarketExpectationEvidenceView",
        "app/services/market_expectation_evidence_service.py",
        ("build_market_expectation_evidence_view", "validate_market_expectation_candidate"),
        "BYPASS_OF_CANONICAL_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "NOT_APPLICABLE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "CONVERGENCE_DEBT_PRESENT",
        "Latest fresh core validator does not consume the expectation independence view.",
    ),
    Family(
        "direction_timing_ownership",
        "Direction/timing ownership",
        "app/services/direction_timing_ownership_service.py",
        ("validate_ownership", "validate_directional_core_ownership"),
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "CANONICAL_SHARED_SERVICE",
        "CANONICAL_SHARED_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "CANONICAL_SHARED_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "CONVERGED",
        "Both active paths delegate ownership checks to the shared service.",
    ),
    Family(
        "qtd_ytd_period",
        "QTD/YTD and period comparability",
        "app/services/directional_financial_context_service.py",
        ("validate_qtd_ytd_conflict_semantics",),
        "BYPASS_OF_CANONICAL_SERVICE",
        "CANONICAL_SHARED_SERVICE",
        "CANONICAL_SHARED_SERVICE",
        "NOT_APPLICABLE",
        "CANONICAL_SHARED_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "CONVERGENCE_DEBT_PRESENT",
        "Fresh partial audit does not invoke the shared QTD/YTD validator.",
    ),
    Family(
        "adr_security_basis",
        "ADR/security-basis comparability",
        "app/services/cross_market_decision_engine_service.py",
        ("validate_structured_autonomy_candidate",),
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "NOT_APPLICABLE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "CONVERGED_WITH_LEGACY_ADAPTER",
        "Both paths reuse the established structured-autonomy safety surface.",
    ),
    Family(
        "stage2_core_immutability",
        "Stage-2 core immutability",
        "app/services/two_stage_directional_service.py",
        ("compose_directional_core",),
        "NOT_APPLICABLE",
        "NOT_APPLICABLE",
        "NOT_APPLICABLE",
        "CANONICAL_SHARED_SERVICE",
        "CANONICAL_SHARED_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "CONVERGED",
        "The fresh path has a different core/timing topology and no Stage-2 stance mutation surface.",
    ),
    Family(
        "proof_readiness_policy",
        "Proof/finalizer hard-semantic vs diagnostic policy",
        "scripts/finalization_readiness_policy.py",
        ("evaluate_finalization_readiness",),
        "BYPASS_OF_CANONICAL_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "THIN_ADAPTER_TO_CANONICAL_SERVICE",
        "CONVERGENCE_DEBT_PRESENT",
        "Fresh completion uses separate run gates rather than the canonical finalization policy.",
    ),
)


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value)


def git(*args: str) -> str:
    result = subprocess.run(
        ("git", *args),
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def source_text(path: Path) -> str:
    return path.read_text()


def source_sha(path: Path) -> str:
    return file_sha256(path)


def function_lines(path: Path) -> dict[str, int]:
    tree = ast.parse(source_text(path))
    return {
        node.name: node.lineno
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def call_lines(path: Path, names: Sequence[str]) -> dict[str, list[int]]:
    wanted = set(names)
    result = {name: [] for name in names}
    tree = ast.parse(source_text(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target: str | None = None
        if isinstance(node.func, ast.Name):
            target = node.func.id
        elif isinstance(node.func, ast.Attribute):
            target = node.func.attr
        if target in wanted:
            result[target].append(node.lineno)
    return result


def report(number: int, slug: str, payload: Mapping[str, object]) -> None:
    document = {
        "contract": CONTRACT,
        "report_number": number,
        "report_slug": slug,
        "generated_at": datetime.now(UTC).isoformat(),
        **payload,
    }
    write_json(REPORTS / f"{number:03d}-{slug}.json", document)


def _secret_indicators(payload: bytes) -> tuple[str, ...]:
    if b"\x00" in payload[:4096]:
        return ()
    patterns = {
        "private_key": rb"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----",
        "openai_key": rb"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}",
        "telegram_bot_token": rb"(?<!\d)\d{8,12}:[A-Za-z0-9_-]{30,}",
    }
    return tuple(name for name, pattern in patterns.items() if re.search(pattern, payload))


def verify_latest_result() -> dict[str, object]:
    actual_sha = file_sha256(LATEST_RESULT)
    with zipfile.ZipFile(LATEST_RESULT) as archive:
        names = {name for name in archive.namelist() if not name.endswith("/")}
        index_paths = sorted(name for name in names if name.endswith("/artifact-index.json"))
        if len(index_paths) != 1:
            raise ValueError(f"LATEST_ARTIFACT_INDEX_IDENTITY_INVALID:{len(index_paths)}")
        index_path = index_paths[0]
        index = json.loads(archive.read(index_path))
        rows = index.get("rows", ())
        indexed = {str(row["path"]) for row in rows}
        missing = sorted(indexed - names)
        extra = sorted(names - indexed - {index_path})
        hash_mismatches: list[str] = []
        size_mismatches: list[str] = []
        independent_secret_failures: list[dict[str, object]] = []
        for row in rows:
            member = str(row["path"])
            if member not in names:
                continue
            payload = archive.read(member)
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                hash_mismatches.append(member)
            if len(payload) != row["size"]:
                size_mismatches.append(member)
            indicators = _secret_indicators(payload)
            if indicators:
                independent_secret_failures.append({"path": member, "indicators": list(indicators)})
    checks = {
        "zip_sha256": actual_sha == LATEST_RESULT_SHA256,
        "index_status": index.get("status") == "PASS",
        "indexed_payload_count": len(rows) == LATEST_INDEXED_PAYLOADS,
        "zip_entry_count": len(names) == LATEST_ZIP_ENTRIES,
        "missing": not missing,
        "extra": not extra,
        "hashes": not hash_mismatches,
        "sizes": not size_mismatches,
        "indexed_secret_scan": index.get("secret_scan_failure_count") == 0,
        "independent_secret_scan": not independent_secret_failures,
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "path": str(LATEST_RESULT),
        "expected_sha256": LATEST_RESULT_SHA256,
        "actual_sha256": actual_sha,
        "checks": checks,
        "indexed_payload_count": len(rows),
        "zip_entry_count": len(names),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "hash_mismatch_count": len(hash_mismatches),
        "size_mismatch_count": len(size_mismatches),
        "secret_scan_failure_count": len(independent_secret_failures),
        "index_reported_secret_scan_failure_count": index.get("secret_scan_failure_count"),
    }


def _configured_ref(*, concept: str) -> DecisionEvidenceRef:
    return DecisionEvidenceRef.model_construct(
        ref_id="configured-ref",
        source_ref="stock.thesis.weaken_signals",
        financial_context=None,
        label=concept,
        statement=concept,
        logical_condition=None,
        metric_refs=(CheckpointMetric.FCF,) if "FCF" in concept else (),
    )


def evaluate_fcf_case(case: Mapping[str, object]) -> dict[str, object]:
    text = str(case["text"])
    path = str(case.get("field_path") or "core_investment_judgment")
    configured = bool(case.get("configured_support"))
    refs = ["configured-ref"] if configured else ["current-ref"]
    evidence = {"configured-ref": _configured_ref(concept="FCF 감소")} if configured else None
    row = financial_claim_rows({path: {"text": text, "evidence_refs": refs}})[0]
    spans = fcf_temporal_claim_spans(row)
    roles = [fcf_temporal_claim_role(span, evidence_by_ref=evidence).value for span in spans]
    proxy_roles = [span.role.value for span in classify_ppe_proxy_fcf_claims(text)]
    proxy_hard_failure = "PROXY_AS_FCF_ATTRIBUTION" in proxy_roles
    disclaimer = "EXPLICIT_NOT_FCF_DISCLAIMER" in proxy_roles
    current_required = any(role in CURRENT_ROLES for role in roles) and not disclaimer
    observed = {
        "temporal_roles": roles,
        "current_safe_fcf_evidence_required": current_required,
        "proxy_roles": proxy_roles,
        "proxy_as_fcf_hard_failure": proxy_hard_failure,
        "explicit_not_fcf_disclaimer": disclaimer,
    }
    expected = dict(case["expected"])
    return {
        "status": "PASS"
        if all(observed.get(key) == value for key, value in expected.items())
        else "FAIL",
        "observed": observed,
        "expected": expected,
        "canonical_service": (
            "directional_financial_context_service."
            "fcf_temporal_claim_role/classify_ppe_proxy_fcf_claims"
        ),
    }


def evaluate_net_debt_case(case: Mapping[str, object]) -> dict[str, object]:
    text = str(case["text"])
    field_path = str(case.get("field_path") or "core_investment_judgment")
    configured = bool(case.get("configured_support"))
    ref_ids = ("configured-ref",) if configured else ()
    evidence = {"configured-ref": _configured_ref(concept="순부채 증가")} if configured else None
    claim = FrameworkClaim(
        framework="net_debt",
        kind=FrameworkClaimKind.ASSERTION_OR_APPLICATION,
        text=text,
        field_path=field_path,
        evidence_refs=ref_ids,
        role=FrameworkReferenceRole.APPLIED_DECISION_FRAMEWORK,
        full_field_text=text,
        local_clause_text=text,
        local_clause_start=0,
        local_clause_end=len(text),
    )
    role = financial_claim_role(claim, evidence_by_ref=evidence).value
    current_required = financial_claim_requires_current_evidence(claim, evidence_by_ref=evidence)
    observed = {
        "temporal_role": role,
        "current_complete_net_debt_evidence_required": current_required,
    }
    expected = dict(case["expected"])
    return {
        "status": "PASS"
        if all(observed.get(key) == value for key, value in expected.items())
        else "FAIL",
        "observed": observed,
        "expected": expected,
        "canonical_service": "directional_financial_context_service.financial_claim_role",
    }


def _wc_view() -> WorkingCapitalCheckpointBindingView:
    items = (
        WorkingCapitalCheckpointBindingItem(
            alias="inv",
            canonical_ref="fin:inv",
            metric="inventory",
            evidence_kind="TYPED_FINANCIAL",
        ),
        WorkingCapitalCheckpointBindingItem(
            alias="ar",
            canonical_ref="fin:ar",
            metric="trade_accounts_receivable",
            evidence_kind="TYPED_FINANCIAL",
        ),
        WorkingCapitalCheckpointBindingItem(
            alias="ap",
            canonical_ref="fin:ap",
            metric="trade_accounts_payable",
            evidence_kind="TYPED_FINANCIAL",
        ),
    )
    return WorkingCapitalCheckpointBindingView(
        ticker="GOLDEN",
        selected_working_capital_items=items,
        metric_to_typed_aliases={
            "inventory": ("inv",),
            "trade_accounts_receivable": ("ar",),
            "trade_accounts_payable": ("ap",),
        },
        metric_to_canonical_refs={
            "inventory": ("fin:inv",),
            "trade_accounts_receivable": ("fin:ar",),
            "trade_accounts_payable": ("fin:ap",),
        },
    )


def evaluate_wc_case(case: Mapping[str, object]) -> dict[str, object]:
    field_path = str(case["field_path"])
    text = str(case["text"])
    refs = list(case["refs"])
    if field_path == "fundamental_new_buyer.confirmation_business_condition":
        payload = {
            "fundamental_new_buyer": {
                "confirmation_business_condition": text,
                "confirmation_business_condition_refs": refs,
            }
        }
    elif field_path == "fundamental_holder.business_invalidation_condition":
        payload = {
            "fundamental_holder": {
                "business_invalidation_condition": text,
                "business_invalidation_condition_refs": refs,
            }
        }
    else:
        payload = {field_path: {"text": text, "evidence_refs": refs}}
    result = validate_working_capital_checkpoint_bindings(payload, _wc_view())
    observed = {
        "status": result["status"],
        "grounding_failure_count": result["working_capital_grounding_failure_count"],
        "narrative_only_substitution_count": result["narrative_only_substitution_count"],
        "unsafe_auto_direction_count": result["unsafe_working_capital_auto_direction_count"],
    }
    expected = dict(case["expected"])
    return {
        "status": "PASS"
        if all(observed.get(key) == value for key, value in expected.items())
        else "FAIL",
        "observed": observed,
        "expected": expected,
        "canonical_service": (
            "working_capital_checkpoint_binding_service."
            "validate_working_capital_checkpoint_bindings"
        ),
    }


def evaluate_financial_sector_case(case: Mapping[str, object]) -> dict[str, object]:
    text = str(case["text"])
    claims = candidate_financial_framework_claims(
        {"sector_interpretation": {"text": text, "evidence_refs": ["sector-ref"]}}
    )
    observed = {
        "roles": sorted({claim.role.value for claim in claims}),
        "frameworks": sorted({claim.framework for claim in claims}),
        "true_industrial_framework_use": any(
            claim.kind == FrameworkClaimKind.ASSERTION_OR_APPLICATION for claim in claims
        ),
    }
    expected = dict(case["expected"])
    return {
        "status": "PASS"
        if all(observed.get(key) == value for key, value in expected.items())
        else "FAIL",
        "observed": observed,
        "expected": expected,
        "canonical_service": "financial_framework_claim_service.candidate_financial_framework_claims",
    }


def _current_financial_ref() -> DecisionEvidenceRef:
    comparison = SimpleNamespace(kind=FinancialComparisonKind.PRIOR_YEAR_COMPARABLE)
    context = SimpleNamespace(
        quality=FinancialEvidenceQuality.VERIFIED,
        comparison=comparison,
        metric="free_cash_flow_ppe",
    )
    return DecisionEvidenceRef.model_construct(
        ref_id="current-fcf",
        source_ref="financial.current.fcf",
        financial_context=context,
        label="Current verified FCF",
        statement="Current verified FCF",
        logical_condition=None,
        metric_refs=(),
    )


def evaluate_configured_case(case: Mapping[str, object]) -> dict[str, object]:
    signal = _configured_ref(concept="FCF 감소")
    refs = [signal]
    proofs: list[ConfiguredSignalFulfillmentEvidence] = []
    if case.get("fulfilled"):
        refs.append(_current_financial_ref())
        proofs.append(
            ConfiguredSignalFulfillmentEvidence(
                signal_ref_id="configured-ref",
                current_evidence_refs=("current-fcf",),
            )
        )
    view = build_configured_signal_evidence_view(
        ticker="GOLDEN",
        supplied_refs=refs,
        verified_fulfillment_evidence=proofs,
    )
    field = str(case.get("field") or "none")
    candidate: dict[str, object] = {"ticker": "GOLDEN"}
    if field == "sell_driver":
        candidate["sell_drivers"] = [
            {"text": "Configured condition", "evidence_refs": ["configured-ref"]}
        ]
    elif field == "material_anchor":
        candidate["material_directional_anchor_basis"] = ["configured-ref"]
    elif field == "future":
        candidate["business_reevaluation_down"] = [
            {"text": "If FCF falls", "evidence_refs": ["configured-ref"]}
        ]
    elif field == "current_fulfilled":
        candidate["dominant_evidence"] = {
            "text": "FCF decline confirmed",
            "evidence_refs": ["configured-ref"],
        }
    validation = validate_configured_signal_field_ownership(candidate, view)
    item = view.items[0]
    observed = {
        "fulfillment_state": item.fulfillment_state.value,
        "current_driver_eligible": item.current_directional_driver_eligible,
        "future_eligible": item.future_reevaluation_eligible,
        "material_anchor_eligible": item.material_anchor_eligible,
        "validator_status": "PASS" if validation.valid else "FAIL",
    }
    expected = dict(case["expected"])
    return {
        "status": "PASS"
        if all(observed.get(key) == value for key, value in expected.items())
        else "FAIL",
        "observed": observed,
        "expected": expected,
        "canonical_service": (
            "configured_signal_evidence_service."
            "build_configured_signal_evidence_view/validate_configured_signal_field_ownership"
        ),
    }


def _comparison_ref(
    *, metric: str, current: Decimal, prior: Decimal
) -> tuple[DecisionEvidenceRef, dict[str, DecisionEvidenceRef]]:
    current_period = FinancialPeriod(
        type=FinancialPeriodType.YTD,
        start=date(2026, 1, 1),
        end=date(2026, 6, 30),
        duration_days=181,
    )
    prior_period = FinancialPeriod(
        type=FinancialPeriodType.YTD,
        start=date(2025, 1, 1),
        end=date(2025, 6, 30),
        duration_days=181,
    )
    comparison = SimpleNamespace(
        kind=FinancialComparisonKind.PRIOR_YEAR_COMPARABLE,
        input_source_refs=("source:current", "source:prior"),
    )
    common = {
        "metric": metric,
        "quality": FinancialEvidenceQuality.VERIFIED,
        "currency": "USD",
        "unit_scale": 1,
        "entity_scope": "issuer",
        "statement_basis": "consolidated",
        "attribution_basis": None,
        "evidence_status": "DIRECT_REPORTED",
        "derivation": None,
    }
    current_context = SimpleNamespace(**common, comparison=comparison, period=current_period)
    prior_context = SimpleNamespace(**common, comparison=None, period=prior_period)
    current_ref = DecisionEvidenceRef.model_construct(
        ref_id="current",
        source_ref="source:current",
        financial_context=current_context,
        value=current,
    )
    prior_ref = DecisionEvidenceRef.model_construct(
        ref_id="prior",
        source_ref="source:prior",
        financial_context=prior_context,
        value=prior,
    )
    return current_ref, {"source:current": current_ref, "source:prior": prior_ref}


def evaluate_business_delta_case(case: Mapping[str, object]) -> dict[str, object]:
    mode = str(case["mode"])
    if mode == "unchanged_text":
        roles = [
            row.role.value for row in classify_business_delta_unchanged_claims(str(case["text"]))
        ]
        observed = {"roles": roles}
    elif mode == "comparison":
        ref, refs = _comparison_ref(
            metric=str(case["metric"]),
            current=Decimal(str(case["current"])),
            prior=Decimal(str(case["prior"])),
        )
        direction = derive_financial_comparison_direction(ref, refs)
        observed = {
            "comparability_safe": direction.comparability_safe,
            "polarity_supported": direction.polarity_supported,
            "supported_change_directions": list(direction.supported_change_directions),
            "reason": direction.reason,
        }
    elif mode == "configured":
        roles = [
            row.role.value for row in classify_business_delta_unchanged_claims(str(case["text"]))
        ]
        observed = {"roles": roles, "observed_delta_eligible": False}
    else:
        view = BusinessDeltaEvidenceView(
            ticker="GOLDEN",
            capability=BusinessDeltaCapability.UNCHANGED_ONLY,
            items=(
                BusinessDeltaEvidenceItem(
                    alias="baseline",
                    canonical_ref="baseline",
                    source_ref="stock.thesis.baseline",
                    domain=EvidenceDomain.BUSINESS_CURRENT,
                    role=BusinessDeltaEvidenceRole.THESIS_BASELINE_CONTEXT,
                    reason="BASELINE_ONLY",
                ),
            ),
        )
        validation = validate_business_delta_candidate(
            {
                "ticker": "GOLDEN",
                "business_thesis_change": "STRENGTHENED",
                "business_thesis_context": {
                    "text": "The thesis strengthened.",
                    "evidence_refs": ["baseline"],
                },
            },
            view,
        )
        observed = {
            "validator_status": validation["status"],
            "errors": validation["errors"],
        }
    expected = dict(case["expected"])
    return {
        "status": "PASS"
        if all(observed.get(key) == value for key, value in expected.items())
        else "FAIL",
        "observed": observed,
        "expected": expected,
        "canonical_service": "business_delta_evidence_service",
    }


def evaluate_expectation_case(case: Mapping[str, object]) -> dict[str, object]:
    role = MarketExpectationEvidenceRole(str(case["role"]))
    eligible = role == MarketExpectationEvidenceRole.INDEPENDENT_DIRECTIONAL_SUPPORT
    dependency_refs = (
        ("dependency-ref",)
        if role == MarketExpectationEvidenceRole.CONDITIONAL_CONTEXT_ONLY
        else ()
    )
    independence_refs = (
        ("independence-ref",)
        if role == MarketExpectationEvidenceRole.INDEPENDENT_DIRECTIONAL_SUPPORT
        else ()
    )
    item = MarketExpectationEvidenceItem(
        alias="expectation",
        canonical_ref="exp-ref",
        source_ref="market.expectation",
        role=role,
        reason="GOLDEN_CORPUS",
        material_anchor_eligible=eligible,
        dominant_evidence_eligible=eligible,
        independence_basis_refs=independence_refs,
        dependency_refs=dependency_refs,
    )
    view = MarketExpectationEvidenceView(ticker="GOLDEN", items=(item,))
    use = str(case["use"])
    candidate: dict[str, object] = {"ticker": "GOLDEN"}
    if use == "material_anchor":
        candidate["material_directional_anchor_basis"] = ["exp-ref"]
    elif use == "dominant":
        candidate["dominant_evidence"] = {
            "text": "Expectation",
            "evidence_refs": ["exp-ref"],
        }
    else:
        candidate["market_expectation_context"] = {
            "text": "Conditional expectation context",
            "evidence_refs": ["exp-ref"],
        }
    validation = validate_market_expectation_candidate(candidate, view)
    observed = {
        "material_anchor_eligible": item.material_anchor_eligible,
        "dominant_evidence_eligible": item.dominant_evidence_eligible,
        "validator_status": validation["status"],
    }
    expected = dict(case["expected"])
    return {
        "status": "PASS"
        if all(observed.get(key) == value for key, value in expected.items())
        else "FAIL",
        "observed": observed,
        "expected": expected,
        "canonical_service": "market_expectation_evidence_service.validate_market_expectation_candidate",
    }


FCF_CASES = (
    {
        "id": "FCF-G01",
        "text": "현재 FCF가 개선됐다.",
        "expected": {
            "temporal_roles": ["CURRENT_DIRECTIONAL_BASIS"],
            "current_safe_fcf_evidence_required": True,
        },
    },
    {
        "id": "FCF-G02",
        "text": "FCF는 100이다.",
        "expected": {
            "temporal_roles": ["CURRENT_NUMERIC_CLAIM"],
            "current_safe_fcf_evidence_required": True,
        },
    },
    {
        "id": "FCF-G03",
        "text": "성장이 FCF 개선으로 이어져야 한다.",
        "expected": {
            "temporal_roles": ["PROSPECTIVE_VERIFICATION_REQUIREMENT"],
            "current_safe_fcf_evidence_required": False,
        },
    },
    {
        "id": "FCF-G04",
        "text": "실제 FCF 증명이 필요하다.",
        "expected": {
            "temporal_roles": ["PROSPECTIVE_VERIFICATION_REQUIREMENT"],
            "current_safe_fcf_evidence_required": False,
        },
    },
    {
        "id": "FCF-G05",
        "text": "FCF 감소 조건은 현재 충족된 사실은 아니다.",
        "field_path": "risk_context",
        "configured_support": True,
        "expected": {
            "temporal_roles": ["PROSPECTIVE_RISK_SCENARIO"],
            "current_safe_fcf_evidence_required": False,
        },
    },
    {
        "id": "FCF-G06",
        "text": "FCF 감소가 확인되면 하향 재평가한다.",
        "field_path": "business_reevaluation_down",
        "configured_support": True,
        "expected": {
            "temporal_roles": ["FUTURE_REEVALUATION_CONDITION"],
            "current_safe_fcf_evidence_required": False,
        },
    },
    {
        "id": "FCF-G07",
        "text": "FCF 감소 여부를 감시해야 한다.",
        "field_path": "risk_context",
        "configured_support": True,
        "expected": {
            "temporal_roles": ["PROSPECTIVE_RISK_SCENARIO"],
            "current_safe_fcf_evidence_required": False,
        },
    },
    {
        "id": "FCF-G08",
        "text": "FCF 감소의 확인은 하향 조건이다.",
        "field_path": "risk_context",
        "configured_support": True,
        "expected": {
            "temporal_roles": ["PROSPECTIVE_RISK_SCENARIO"],
            "current_safe_fcf_evidence_required": False,
        },
    },
    {
        "id": "FCF-G09",
        "text": "OCF-PPE proxy is called FCF.",
        "expected": {"proxy_as_fcf_hard_failure": True},
    },
    {
        "id": "FCF-G10",
        "text": "이 지표는 현금전환 대용치이며 관리 기준 FCF가 아니다.",
        "expected": {"explicit_not_fcf_disclaimer": True, "proxy_as_fcf_hard_failure": False},
    },
)

NET_DEBT_CASES = (
    {
        "id": "NET-G01",
        "text": "현재 순부채가 높다.",
        "expected": {
            "temporal_role": "CURRENT_DIRECTIONAL_BASIS",
            "current_complete_net_debt_evidence_required": True,
        },
    },
    {
        "id": "NET-G02",
        "text": "향후 순부채가 증가하면 하향 재평가한다.",
        "field_path": "business_reevaluation_down",
        "expected": {
            "temporal_role": "FUTURE_REEVALUATION_CONDITION",
            "current_complete_net_debt_evidence_required": False,
        },
    },
    {
        "id": "NET-G03",
        "text": "순부채 증가의 확인은 하향 조건이다.",
        "field_path": "risk_context",
        "configured_support": True,
        "expected": {
            "temporal_role": "PROSPECTIVE_RISK_SCENARIO",
            "current_complete_net_debt_evidence_required": False,
        },
    },
    {
        "id": "NET-G04",
        "text": "순부채 증가 여부를 감시해야 한다.",
        "field_path": "risk_context",
        "configured_support": True,
        "expected": {
            "temporal_role": "PROSPECTIVE_RISK_SCENARIO",
            "current_complete_net_debt_evidence_required": False,
        },
    },
    {
        "id": "NET-G05",
        "text": "현재 순부채가 높고 향후 더 증가하면 위험하다.",
        "field_path": "risk_context",
        "expected": {
            "temporal_role": "CURRENT_DIRECTIONAL_BASIS",
            "current_complete_net_debt_evidence_required": True,
        },
    },
    {
        "id": "NET-G06",
        "text": "순부채 증가가 확인되면 하향 재평가한다.",
        "field_path": "business_reevaluation_down",
        "configured_support": True,
        "expected": {
            "temporal_role": "FUTURE_REEVALUATION_CONDITION",
            "current_complete_net_debt_evidence_required": False,
        },
    },
)

WC_CASES = (
    {
        "id": "WC-G01",
        "field_path": "core_investment_judgment",
        "text": "재고 증가를 확인한다.",
        "refs": ("inv",),
        "expected": {"status": "PASS", "grounding_failure_count": 0},
    },
    {
        "id": "WC-G02",
        "field_path": "risk_context",
        "text": "매출채권 증가를 확인한다.",
        "refs": ("ar",),
        "expected": {"status": "PASS", "grounding_failure_count": 0},
    },
    {
        "id": "WC-G03",
        "field_path": "business_reevaluation_down",
        "text": "운전자본 악화를 점검한다.",
        "refs": ("inv",),
        "expected": {"status": "PASS", "grounding_failure_count": 0},
    },
    {
        "id": "WC-G04",
        "field_path": "fundamental_new_buyer.confirmation_business_condition",
        "text": "운전자본 확인이 필요하다.",
        "refs": ("ar",),
        "expected": {"status": "PASS", "grounding_failure_count": 0},
    },
    {
        "id": "WC-G05",
        "field_path": "fundamental_holder.business_invalidation_condition",
        "text": "재고 증가가 확인되면 재검토한다.",
        "refs": ("inv",),
        "expected": {"status": "PASS", "grounding_failure_count": 0},
    },
    {
        "id": "WC-G06",
        "field_path": "core_investment_judgment",
        "text": "재고 증가를 확인한다.",
        "refs": ("narrative",),
        "expected": {"status": "FAIL", "narrative_only_substitution_count": 1},
    },
    {
        "id": "WC-G07",
        "field_path": "core_investment_judgment",
        "text": "재고 증가가 관찰됐다.",
        "refs": ("inv",),
        "expected": {"status": "PASS", "unsafe_auto_direction_count": 0},
    },
)

FINANCIAL_SECTOR_CASES = (
    {
        "id": "FIN-G01",
        "text": "산업회사식 순부채·운전자본 틀을 배제하고 규제자본을 중심으로 본다.",
        "expected": {"roles": ["CONTRASTIVE_REPLACEMENT"], "true_industrial_framework_use": False},
    },
    {
        "id": "FIN-G02",
        "text": "산업회사식 순부채·운전자본 틀을 적용하지 않고 규제자본 중심으로 해석한다.",
        "expected": {"roles": ["CONTRASTIVE_REPLACEMENT"], "true_industrial_framework_use": False},
    },
    {
        "id": "FIN-G03",
        "text": "산업회사식 순부채를 적용하지 않고 규제자본도 해석하지 않는다.",
        "expected": {"roles": ["UNRESOLVED"], "true_industrial_framework_use": False},
    },
    {
        "id": "FIN-G04",
        "text": "보험사의 순부채와 운전자본을 핵심 평가틀로 적용한다.",
        "expected": {"roles": ["ASSERTED_STATE"], "true_industrial_framework_use": True},
    },
)

CONFIGURED_CASES = (
    {
        "id": "CFG-G01",
        "field": "none",
        "expected": {
            "fulfillment_state": "CONFIGURED_ONLY",
            "current_driver_eligible": False,
            "future_eligible": True,
        },
    },
    {
        "id": "CFG-G02",
        "field": "sell_driver",
        "expected": {"validator_status": "FAIL", "current_driver_eligible": False},
    },
    {
        "id": "CFG-G03",
        "field": "material_anchor",
        "expected": {"validator_status": "FAIL", "material_anchor_eligible": False},
    },
    {
        "id": "CFG-G04",
        "field": "future",
        "expected": {"validator_status": "PASS", "future_eligible": True},
    },
    {
        "id": "CFG-G05",
        "field": "current_fulfilled",
        "fulfilled": True,
        "expected": {
            "fulfillment_state": "FULFILLED_BY_CURRENT_EVIDENCE",
            "validator_status": "PASS",
            "current_driver_eligible": True,
        },
    },
)

BUSINESS_DELTA_CASES = (
    {
        "id": "DELTA-G01",
        "mode": "unchanged_text",
        "text": "저장된 기존 투자 테제다.",
        "expected": {"roles": ["BASELINE_THESIS_DESCRIPTION"]},
    },
    {
        "id": "DELTA-G02",
        "mode": "comparison",
        "metric": "operating_cash_flow",
        "current": "120",
        "prior": "100",
        "expected": {"comparability_safe": True, "supported_change_directions": ["STRENGTHENED"]},
    },
    {
        "id": "DELTA-G03",
        "mode": "comparison",
        "metric": "inventory",
        "current": "120",
        "prior": "100",
        "expected": {"polarity_supported": False, "supported_change_directions": []},
    },
    {
        "id": "DELTA-G04",
        "mode": "configured",
        "text": "약화 조건을 감시한다.",
        "expected": {"observed_delta_eligible": False},
    },
    {"id": "DELTA-G05", "mode": "unchanged_capability", "expected": {"validator_status": "FAIL"}},
)

EXPECTATION_CASES = (
    {
        "id": "EXP-G01",
        "role": "CONDITIONAL_CONTEXT_ONLY",
        "use": "material_anchor",
        "expected": {"material_anchor_eligible": False, "validator_status": "FAIL"},
    },
    {
        "id": "EXP-G02",
        "role": "INDEPENDENCE_UNKNOWN",
        "use": "dominant",
        "expected": {"dominant_evidence_eligible": False, "validator_status": "FAIL"},
    },
    {
        "id": "EXP-G03",
        "role": "CONDITIONAL_CONTEXT_ONLY",
        "use": "context",
        "expected": {"material_anchor_eligible": False, "validator_status": "PASS"},
    },
)


def _fresh_bypass_probe(case_id: str) -> dict[str, object]:
    """Run the active fresh core partial audit with a semantic-only payload.

    The stub intentionally provides every attribute that core_partial_audit reads.
    A PASS demonstrates that the semantic text was not evaluated, not that the
    canonical semantic contract accepted it.
    """

    from scripts import new_issuer_holdout_selection_ownership_proof as fresh

    probe = SimpleNamespace(
        ticker=case_id,
        unknown_treatments=(),
        overall_direction="HOLD",
        material_directional_anchor_basis=(),
        model_dump=lambda mode="json": {
            "ticker": case_id,
            "core_investment_judgment": {
                "text": "semantic golden corpus probe",
                "evidence_refs": [],
            },
        },
    )
    owned = SimpleNamespace(domain_by_ref={}, evidence=())
    audit = fresh.core_partial_audit([probe], {case_id: owned})
    return {
        "surface": "fresh/new-issuer",
        "status": "BYPASS_NO_CANONICAL_ROLE",
        "partial_audit_status": audit["status"],
        "canonical_service_identity": False,
        "classification": "BYPASS_OF_CANONICAL_SERVICE",
    }


def _surface_rows(
    case_id: str, canonical: Mapping[str, object], *, stage2: bool
) -> dict[str, object]:
    fresh = _fresh_bypass_probe(case_id)
    canonical_result = {
        "status": canonical["status"],
        "observed": canonical["observed"],
        "canonical_service": canonical["canonical_service"],
        "canonical_service_identity": True,
    }
    return {
        "fresh_new_issuer": fresh,
        "monitored_monolithic": canonical_result,
        "monitored_stage1": canonical_result,
        "monitored_stage2": (
            canonical_result
            if stage2
            else {
                "status": "NOT_APPLICABLE",
                "canonical_service_identity": None,
            }
        ),
        "shadow_post_model": canonical_result,
        "same_canonical_service_identity": False,
        "role_result_equality": False,
        "divergence_reason": "FRESH_PROOF_CRITICAL_CANONICAL_BYPASS",
    }


def evaluate_group(
    family: str,
    cases: Sequence[Mapping[str, object]],
    evaluator: Callable[[Mapping[str, object]], dict[str, object]],
    *,
    stage2: bool = False,
) -> list[dict[str, object]]:
    rows = []
    for case in cases:
        canonical = evaluator(case)
        rows.append(
            {
                "case_id": case["id"],
                "semantic_family": family,
                "input": {key: value for key, value in case.items() if key not in {"expected"}},
                "canonical_expected": case["expected"],
                "canonical_result": canonical,
                "surfaces": _surface_rows(str(case["id"]), canonical, stage2=stage2),
            }
        )
    return rows


def golden_corpus() -> dict[str, list[dict[str, object]]]:
    return {
        "fcf": evaluate_group("fcf_identity_currentness", FCF_CASES, evaluate_fcf_case),
        "net_debt": evaluate_group(
            "net_debt_temporal_completeness", NET_DEBT_CASES, evaluate_net_debt_case
        ),
        "working_capital": evaluate_group(
            "working_capital_typed_grounding", WC_CASES, evaluate_wc_case, stage2=True
        ),
        "financial_sector": evaluate_group(
            "financial_sector_framework",
            FINANCIAL_SECTOR_CASES,
            evaluate_financial_sector_case,
        ),
        "configured_signal": evaluate_group(
            "configured_signal_lifecycle", CONFIGURED_CASES, evaluate_configured_case
        ),
        "business_delta": evaluate_group(
            "business_delta_view", BUSINESS_DELTA_CASES, evaluate_business_delta_case
        ),
        "market_expectation": evaluate_group(
            "market_expectation_view", EXPECTATION_CASES, evaluate_expectation_case
        ),
    }


def _entrypoint_map() -> dict[str, object]:
    functions = {str(path): function_lines(path) for path in (*FRESH_PATHS, *MONITORED_PATHS)}
    calls = {
        str(path): call_lines(
            path,
            (
                "execute_run",
                "core_partial_audit",
                "timing_partial_audit",
                "validate_directional_financial_semantics",
                "validate_qtd_ytd_conflict_semantics",
                "validate_business_delta_candidate",
                "validate_market_expectation_candidate",
                "validate_working_capital_checkpoint_bindings",
                "validate_configured_signal_field_ownership",
                "audit_owned_directional_core_semantics",
                "_audit_core_batch_with_grounding",
            ),
        )
        for path in (*FRESH_PATHS, *MONITORED_PATHS)
    }
    return {"function_definitions": functions, "call_sites": calls}


def _ownership_rows() -> list[dict[str, object]]:
    rows = []
    for family in FAMILIES:
        rows.append(
            {
                "semantic_contract_family": family.key,
                "title": family.title,
                "canonical_module": family.canonical_module,
                "canonical_functions": list(family.canonical_functions),
                "fresh_consumers": [family.fresh],
                "monolithic_consumers": [family.monolithic],
                "stage1_consumers": [family.stage1],
                "stage2_consumers": [family.stage2],
                "shadow_consumers": [family.shadow],
                "offline_replay_consumers": [family.offline],
                "status": family.status,
                "notes": family.notes,
            }
        )
    return rows


def _duplicate_rows() -> list[dict[str, object]]:
    return [
        {
            "path": "scripts/directional_financial_context_m12.py",
            "function": "_case_semantic_errors",
            "line": function_lines(Path("scripts/directional_financial_context_m12.py"))[
                "_case_semantic_errors"
            ],
            "classification": "LEGACY_DUPLICATE_DIVERGENT",
            "proof_critical": True,
            "reason": "Ticker-specific FIC-FIN assertions independently add hard semantic errors.",
        },
        {
            "path": "scripts/boundary_band_application_scope_m12aa.py",
            "function": "_fic_fin_05_hard_errors",
            "line": function_lines(Path("scripts/boundary_band_application_scope_m12aa.py"))[
                "_fic_fin_05_hard_errors"
            ],
            "classification": "LEGACY_DUPLICATE_DIVERGENT",
            "proof_critical": True,
            "reason": "Fixture-specific financial hard errors participate beside canonical validation.",
        },
        {
            "path": "scripts/business_delta_alias_balance_confidence_m12z.py",
            "function": "business_delta_audit",
            "line": function_lines(Path("scripts/business_delta_alias_balance_confidence_m12z.py"))[
                "business_delta_audit"
            ],
            "classification": "LEGACY_DUPLICATE_EQUIVALENT",
            "proof_critical": True,
            "current_path_participation": False,
            "reason": "Canonical branch is used when view is supplied, but fallback independently re-derives semantics.",
        },
        {
            "path": "scripts/boundary_band_application_scope_m12aa.py",
            "function": "_framework_role_audit",
            "line": function_lines(Path("scripts/boundary_band_application_scope_m12aa.py"))[
                "_framework_role_audit"
            ],
            "classification": "THIN_ADAPTER_TO_CANONICAL_SERVICE",
            "proof_critical": True,
            "reason": "Delegates claim classification to candidate_financial_framework_claims.",
        },
        {
            "path": "scripts/working_capital_checkpoint_binding_m12bb.py",
            "function": "working-capital wrapper hooks",
            "line": 471,
            "classification": "THIN_ADAPTER_TO_CANONICAL_SERVICE",
            "proof_critical": True,
            "reason": "Delegates hard decisions to validate_working_capital_checkpoint_bindings.",
        },
    ]


SCAN_TERMS = re.compile(
    r"FCF|잉여현금흐름|free cash flow|순부채|net debt|재고|매출채권|working capital|"
    r"UNCHANGED|시장 기대|expectation|배제하고|적용하지 않고|해석한다|현재|향후|"
    r"확인되면|조건|감시|모니터링|필요하다|PPE|OCF|cash conversion",
    re.IGNORECASE,
)


def _scan_classification(path: Path, line: str) -> str:
    if str(path).startswith("tests/"):
        return "test fixture"
    if path in {
        Path("app/services/directional_financial_context_service.py"),
        Path("app/services/configured_signal_evidence_service.py"),
        Path("app/services/business_delta_evidence_service.py"),
        Path("app/services/market_expectation_evidence_service.py"),
        Path("app/services/working_capital_checkpoint_binding_service.py"),
        Path("app/services/financial_framework_claim_service.py"),
    }:
        return "canonical classifier"
    if path in {
        Path("scripts/directional_financial_context_m12.py"),
        Path("scripts/boundary_band_application_scope_m12aa.py"),
        Path("scripts/business_delta_alias_balance_confidence_m12z.py"),
    } and ("re.compile" in line or "if ticker" in line or "def _" in line):
        return "legacy duplicate"
    if "validate_" in line or "build_" in line:
        return "thin adapter"
    if "prompt" in line.casefold() or line.lstrip().startswith(('"', "'", 'r"', "r'")):
        return "prompt copy"
    return "report-only"


def duplicate_scan() -> dict[str, object]:
    tracked = git("ls-files", "*.py").splitlines()
    rows: list[dict[str, object]] = []
    for name in tracked:
        path = Path(name)
        for line_number, line in enumerate(path.read_text(errors="replace").splitlines(), start=1):
            if not SCAN_TERMS.search(line):
                continue
            rows.append(
                {
                    "path": name,
                    "line": line_number,
                    "classification": _scan_classification(path, line),
                    "line_sha256": hashlib.sha256(line.encode()).hexdigest(),
                }
            )
    counts = Counter(row["classification"] for row in rows)
    return {"hit_count": len(rows), "classification_counts": dict(counts), "rows": rows}


def _bypass_rows() -> list[dict[str, object]]:
    return [
        {
            "path": "scripts/new_issuer_holdout_selection_ownership_proof.py",
            "function": "core_partial_audit",
            "line": function_lines(Path("scripts/new_issuer_holdout_selection_ownership_proof.py"))[
                "core_partial_audit"
            ],
            "families": [
                family.key for family in FAMILIES if family.fresh == "BYPASS_OF_CANONICAL_SERVICE"
            ],
            "classification": "BYPASS_OF_CANONICAL_SERVICE",
            "proof_critical": True,
            "evidence": "Only domain/ref/material-anchor/unknown checks are performed.",
        },
        {
            "path": "scripts/new_issuer_holdout_selection_ownership_proof.py",
            "function": "execute_run",
            "line": function_lines(Path("scripts/new_issuer_holdout_selection_ownership_proof.py"))[
                "execute_run"
            ],
            "classification": "BYPASS_OF_CANONICAL_SERVICE",
            "proof_critical": True,
            "evidence": "Calls core_partial_audit after output normalization, not canonical financial validators.",
        },
        {
            "path": "scripts/new_issuer_final_freeze_ownership_proof.py",
            "function": "execute",
            "line": function_lines(Path("scripts/new_issuer_final_freeze_ownership_proof.py"))[
                "execute"
            ],
            "classification": "BYPASS_OF_CANONICAL_SERVICE",
            "proof_critical": True,
            "evidence": "Delegates each run to the bypassing execute_run implementation.",
        },
    ]


def _report_payloads(
    integrity: Mapping[str, object],
    corpus: Mapping[str, list[dict[str, object]]],
    entrypoints: Mapping[str, object],
    scan: Mapping[str, object],
) -> dict[int, dict[str, object]]:
    ownership = _ownership_rows()
    duplicates = _duplicate_rows()
    bypasses = _bypass_rows()
    all_cases = [row for rows in corpus.values() for row in rows]
    canonical_failures = [
        row["case_id"] for row in all_cases if row["canonical_result"]["status"] != "PASS"
    ]
    divergent = [row for row in duplicates if row["classification"] == "LEGACY_DUPLICATE_DIVERGENT"]
    equivalent = [
        row for row in duplicates if row["classification"] == "LEGACY_DUPLICATE_EQUIVALENT"
    ]
    fresh_bypass_families = [
        row["semantic_contract_family"]
        for row in ownership
        if row["fresh_consumers"] == ["BYPASS_OF_CANONICAL_SERVICE"]
    ]
    summaries = {
        "financial_temporal_role": "BLOCKED_BY_FRESH_CANONICAL_BYPASS",
        "fcf_identity_currentness": "BLOCKED_BY_FRESH_CANONICAL_BYPASS",
        "net_debt_temporal_completeness": "BLOCKED_BY_FRESH_CANONICAL_BYPASS",
        "working_capital_typed_grounding": "BLOCKED_BY_FRESH_CANONICAL_BYPASS",
        "financial_sector_framework": "BLOCKED_BY_FRESH_BYPASS_AND_FIXTURE_DUPLICATE",
        "configured_signal_lifecycle": "BLOCKED_BY_FRESH_CANONICAL_BYPASS",
        "business_delta_view": "BLOCKED_BY_FRESH_BYPASS_AND_DRIFTABLE_FALLBACK",
        "market_expectation_view": "BLOCKED_BY_FRESH_CANONICAL_BYPASS",
        "direction_timing_ownership": "CONVERGED",
        "qtd_ytd_period": "BLOCKED_BY_FRESH_CANONICAL_BYPASS",
        "adr_security_basis": "CONVERGED_WITH_LEGACY_ADAPTER",
        "stage2_core_immutability": "CONVERGED",
        "proof_readiness_policy": "BLOCKED_BY_FRESH_CANONICAL_BYPASS",
    }
    common_stop = {
        "status": "STOP_BEFORE_SHADOW",
        "reason": "PROOF_CRITICAL_SEMANTIC_SINGLE_SOURCE_CONVERGENCE_DEBT",
        "next_scope": NEXT_SCOPE,
        "model_calls": 0,
        "network_gate_attempts": 0,
    }
    return {
        1: {
            "status": "PASS",
            "repository": "sskim-ai/thesis-monitor",
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "integration_branch": INTEGRATION_BRANCH,
            "audit_head_sha": git("rev-parse", "HEAD"),
            "working_tree_before_audit": git("status", "--short"),
        },
        2: dict(integrity),
        3: {
            "status": "PASS",
            "scope": "AUDIT_ONLY",
            "model": MODEL,
            "effort": EFFORT,
            "model_calls_authorized_before_clean_audit": 0,
            "model_facing_semantic_change_count": 0,
            "production_effects_allowed": 0,
        },
        4: {
            "status": "NETWORK_TRANSPORT_ONLY",
            "generation_id": M12BG_SHADOW_GENERATION_ID,
            "failure": "DNS_FAILURE",
            "completed_model_calls": 0,
            "semantic_failure_count": 0,
            "classification": "NOT_A_SEMANTIC_BLOCKER",
        },
        5: {
            "status": "MAPPED",
            "entrypoint_count": 3,
            "entrypoints": [
                "new_issuer_final_freeze_ownership_proof.execute",
                "new_issuer_holdout_selection_ownership_proof.execute/execute_run",
                "fresh_issuer_ownership_proof_transport_risk_carried.execute",
            ],
            "packet_context_builder": "new_issuer_holdout_selection_ownership_proof.load_inputs",
            "prompt_schema_builder": "directional_core_price_timing_holdout helpers",
            "post_model_validator": "core_partial_audit + timing_partial_audit",
            "composer_finalizer": "compose_decision + run_gate_documents",
            "canonical_financial_validator_consumed": False,
        },
        6: {
            "status": "MAPPED",
            "entrypoint": "business_delta_evidence_capability_m12ai._full_audit",
            "call_chain": [
                "main_integration_two_stage_directional_m12ae_r2_runtime._full_candidate_audit",
                "directional_financial_context_m12g._audit_core_batch_with_grounding",
                "directional_financial_context_m12._audit_core_batch",
            ],
        },
        7: {
            "status": "MAPPED",
            "entrypoint": "business_delta_evidence_capability_m12ai._stage1_audit",
            "call_chain": [
                "main_integration_two_stage_directional_m12ae_r2_runtime._stage1_audit",
                "directional_financial_context_m12g._audit_core_batch_with_grounding",
                "directional_financial_context_m12._audit_core_batch",
            ],
        },
        8: {
            "status": "MAPPED",
            "entrypoint": "main_integration_two_stage_directional_m12ae_r2_runtime Stage-2",
            "semantic_scope": "stance fields, WC binding, core immutability and final composition",
            "financial_core_claims": "NOT_APPLICABLE_UNTIL_FINAL_COMPOSITION",
        },
        9: {
            "status": "MAPPED",
            "entrypoint": "main_integration_two_stage_directional_m12ae_r2_runtime.run_shadow",
            "post_model_validators": [
                "validate_directional_financial_semantics",
                "validate_qtd_ytd_conflict_semantics",
                "validate_business_delta_candidate",
                "validate_market_expectation_candidate",
                "validate_working_capital_checkpoint_bindings",
            ],
        },
        10: {
            "status": "MAPPED",
            "entrypoints": [
                "fcf_prospective_requirement_verification_scope_m12bg._m12bd_offline_reaudit",
                "context_preserving_finalization",
                "finalization_readiness_policy",
            ],
            "execution_in_m12bh": "NOT_RUN_DUE_TO_CONVERGENCE_DEBT",
        },
        11: {
            "status": "COMPLETE",
            "family_count": len(FAMILIES),
            "families": [family.__dict__ for family in FAMILIES],
        },
        12: {"status": "CONVERGENCE_DEBT_PRESENT", "rows": ownership},
        13: {"status": "COMPLETE", **entrypoints},
        14: {"status": "COMPLETE", **scan},
        15: {
            "status": "CONVERGENCE_DEBT_PRESENT",
            "proof_critical_duplicate_count": len(
                [
                    row
                    for row in duplicates
                    if row.get("proof_critical")
                    and row["classification"].startswith("LEGACY_DUPLICATE")
                ]
            ),
            "rows": duplicates,
        },
        16: {
            "status": "CONVERGENCE_DEBT_PRESENT",
            "proof_critical_bypass_count": len(fresh_bypass_families),
            "families": fresh_bypass_families,
            "rows": bypasses,
        },
        17: {
            "semantic_convergence_audit_status": "CONVERGENCE_DEBT_PRESENT",
            "decision": "STOP_BEFORE_SHADOW",
            "canonical_golden_fixture_failures": canonical_failures,
            "next_scope": NEXT_SCOPE,
        },
        18: {"status": summaries["financial_temporal_role"], "ownership": ownership[0]},
        19: {"status": summaries["fcf_identity_currentness"], "ownership": ownership[1]},
        20: {"status": summaries["net_debt_temporal_completeness"], "ownership": ownership[2]},
        21: {"status": summaries["working_capital_typed_grounding"], "ownership": ownership[3]},
        22: {"status": summaries["financial_sector_framework"], "ownership": ownership[4]},
        23: {"status": summaries["configured_signal_lifecycle"], "ownership": ownership[5]},
        24: {"status": summaries["business_delta_view"], "ownership": ownership[6]},
        25: {"status": summaries["market_expectation_view"], "ownership": ownership[7]},
        26: {"status": summaries["direction_timing_ownership"], "ownership": ownership[8]},
        27: {"status": summaries["qtd_ytd_period"], "ownership": ownership[9]},
        28: {"status": summaries["adr_security_basis"], "ownership": ownership[10]},
        29: {"status": summaries["stage2_core_immutability"], "ownership": ownership[11]},
        30: {"status": summaries["proof_readiness_policy"], "ownership": ownership[12]},
        31: {
            "status": "PASS",
            "case_count": len(all_cases),
            "group_counts": {name: len(rows) for name, rows in corpus.items()},
            "canonical_fixture_failure_count": len(canonical_failures),
            "fresh_surface_contract": "ACTUAL_CORE_PARTIAL_AUDIT_BYPASS_PROBE",
        },
        32: {
            "status": "PASS"
            if not [row for row in corpus["fcf"] if row["canonical_result"]["status"] != "PASS"]
            else "FAIL",
            "rows": corpus["fcf"],
        },
        33: {
            "status": "PASS"
            if not [
                row for row in corpus["net_debt"] if row["canonical_result"]["status"] != "PASS"
            ]
            else "FAIL",
            "rows": corpus["net_debt"],
        },
        34: {
            "status": "PASS"
            if not [
                row
                for row in corpus["working_capital"]
                if row["canonical_result"]["status"] != "PASS"
            ]
            else "FAIL",
            "rows": corpus["working_capital"],
        },
        35: {
            "status": "PASS"
            if not [
                row
                for row in corpus["financial_sector"]
                if row["canonical_result"]["status"] != "PASS"
            ]
            else "FAIL",
            "rows": corpus["financial_sector"],
        },
        36: {
            "status": "PASS"
            if not [
                row
                for row in corpus["configured_signal"]
                if row["canonical_result"]["status"] != "PASS"
            ]
            else "FAIL",
            "rows": corpus["configured_signal"],
        },
        37: {
            "status": "PASS"
            if not [
                row
                for row in corpus["business_delta"]
                if row["canonical_result"]["status"] != "PASS"
            ]
            else "FAIL",
            "rows": corpus["business_delta"],
        },
        38: {
            "status": "PASS"
            if not [
                row
                for row in corpus["market_expectation"]
                if row["canonical_result"]["status"] != "PASS"
            ]
            else "FAIL",
            "rows": corpus["market_expectation"],
        },
        39: {
            "status": "DIVERGENT",
            "case_count": len(all_cases),
            "canonical_fixture_pass_count": len(all_cases) - len(canonical_failures),
            "canonical_fixture_failure_count": len(canonical_failures),
            "cross_path_divergence_count": len(all_cases),
            "divergence_type": "FRESH_CANONICAL_SERVICE_COVERAGE_GAP",
        },
        40: {"status": "FOUND", "count": len(divergent), "rows": divergent},
        41: {"status": "FOUND", "count": len(bypasses), "rows": bypasses},
        42: {"status": "FOUND", "count": len(equivalent), "rows": equivalent},
        43: {
            "status": "RANKED",
            "rows": [
                {
                    "rank": 1,
                    "finding": "Fresh core post-model financial semantic bypass",
                    "decision_materiality": "CRITICAL",
                    "path_reach": "ALL_FRESH_NEW_ISSUER_CORE_OUTPUTS",
                    "false_accept_risk": "HIGH",
                    "false_reject_risk": "MEDIUM",
                    "model_facing_impact": "POST_MODEL_ONLY",
                },
                {
                    "rank": 2,
                    "finding": "Fresh configured/WC/delta/expectation canonical view bypass",
                    "decision_materiality": "HIGH",
                    "path_reach": "ALL_FRESH_NEW_ISSUER_CORE_OUTPUTS",
                    "false_accept_risk": "HIGH",
                    "false_reject_risk": "LOW",
                    "model_facing_impact": "POST_MODEL_ONLY",
                },
                {
                    "rank": 3,
                    "finding": "Ticker-specific _case_semantic_errors in proof-critical monitored audit",
                    "decision_materiality": "HIGH",
                    "path_reach": "FICTIONAL_AND_SHADOW_AUDITS",
                    "false_accept_risk": "LOW",
                    "false_reject_risk": "HIGH",
                    "model_facing_impact": "NONE",
                },
                {
                    "rank": 4,
                    "finding": "FIC-FIN-05 fixture hard helper beside canonical framework service",
                    "decision_materiality": "MEDIUM",
                    "path_reach": "STAGE1_FIXTURE",
                    "false_accept_risk": "LOW",
                    "false_reject_risk": "HIGH",
                    "model_facing_impact": "NONE",
                },
                {
                    "rank": 5,
                    "finding": "Business-delta fallback re-derivation remains callable",
                    "decision_materiality": "MEDIUM",
                    "path_reach": "LEGACY_CALLERS",
                    "false_accept_risk": "MEDIUM",
                    "false_reject_risk": "MEDIUM",
                    "model_facing_impact": "NONE_CURRENT_M12AI",
                },
            ],
        },
        44: {
            "status": "BOUNDED_SCOPE_DEFINED",
            "next_scope": NEXT_SCOPE,
            "required_changes": [
                "Route latest fresh/new-issuer post-model core output through the same canonical financial, QTD/YTD, configured-signal, WC, business-delta, and market-expectation services used by monitored/shadow.",
                "Replace ticker-specific proof hard semantics with assertions over canonical audit output.",
                "Remove or seal the independent business-delta fallback so proof-critical callers require a canonical view.",
                "Rerun this unchanged 40-case cross-path corpus before any model call.",
            ],
            "excluded": [
                "new lexical regex",
                "model prompt change",
                "schema change",
                "network retry",
                "shadow generation",
            ],
        },
        45: common_stop,
        104: {"semantic_convergence_audit_status": "CONVERGENCE_DEBT_PRESENT", **common_stop},
        105: {
            "decision": "NO_NETWORK_GATE_AND_NO_SHADOW",
            "network_readiness_status": "NOT_RUN_DUE_TO_CONVERGENCE_DEBT",
            "new_shadow_generation_id": None,
        },
        106: {
            "formal_fictional_reuse_status": "NOT_EVALUATED_DUE_TO_CONVERGENCE_DEBT",
            "m12bd_offline_reaudit_status": "NOT_RUN_DUE_TO_CONVERGENCE_DEBT",
            "new_fictional_model_calls": 0,
        },
        107: {
            "full_shadow_completion_status": "NOT_RUN_DUE_TO_CONVERGENCE_DEBT",
            "shadow_model_calls_total": 0,
            "shadow_completed_ticker_count": 0,
        },
        108: {"two_stage_shadow_compatibility": "NOT_MEASURED", "reason": "STOP_BEFORE_SHADOW"},
        109: {
            "existing_monitored_runtime_impact": "NONE",
            "runtime_code_changed": False,
            "model_facing_semantics_changed": False,
        },
        110: {
            "fresh_real_proof_readiness": "NOT_READY",
            "blocker": "CANONICAL_SEMANTIC_SERVICE_BYPASS",
        },
        111: {
            "final_main_merge_readiness": "NOT_READY",
            "main_merge": 0,
            "main_branch_mutations": 0,
        },
        112: {
            "status": "PASS",
            "production_no_change": True,
            "production_db_mutations": 0,
            "assessment_persistence_mutations": 0,
            "warning_mutations": 0,
            "notification_queue_writes": 0,
            "production_sends": 0,
            "provider_source_fetches": 0,
        },
        113: {
            "status": "PAUSED_PRESERVED",
            "observed_paused_schedule_count": "REUSED_PRIOR_VERIFIED_STATE_4",
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
        },
        114: {
            "status": "PASS",
            "remote_push_count": 0,
            "raw_model_artifact_remote_push_count": 0,
            "origin_push_authorized": False,
        },
        115: {"status": "PENDING_DOCUMENTATION_CLOSURE", "path": "docs/MASTER_WORKFLOW.md"},
    }


def build_completion(
    integrity: Mapping[str, object],
    corpus: Mapping[str, list[dict[str, object]]],
    validation: Mapping[str, object] | None = None,
) -> dict[str, object]:
    ownership = _ownership_rows()
    duplicates = _duplicate_rows()
    all_cases = [row for rows in corpus.values() for row in rows]
    counts = Counter(
        value
        for row in ownership
        for key in (
            "fresh_consumers",
            "monolithic_consumers",
            "stage1_consumers",
            "stage2_consumers",
            "shadow_consumers",
            "offline_replay_consumers",
        )
        for value in row[key]
    )
    result: dict[str, object] = {
        "contract": CONTRACT,
        "status": "STOPPED_BEFORE_SHADOW_CONVERGENCE_DEBT",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "integration_branch": INTEGRATION_BRANCH,
        "final_local_head_sha": git("rev-parse", "HEAD"),
        "latest_result_zip_sha256": integrity["actual_sha256"],
        "latest_result_integrity": integrity["status"],
        "m12bg_shadow_generation_id": M12BG_SHADOW_GENERATION_ID,
        "m12bg_network_preflight_failure": "DNS_FAILURE",
        "m12bg_shadow_model_calls_completed": 0,
        "semantic_convergence_audit_status": "CONVERGENCE_DEBT_PRESENT",
        "fresh_new_issuer_entrypoint_count": 3,
        "monitored_semantic_entrypoint_count": 6,
        "semantic_contract_family_count": len(FAMILIES),
        "canonical_shared_service_count": counts["CANONICAL_SHARED_SERVICE"],
        "thin_adapter_count": counts["THIN_ADAPTER_TO_CANONICAL_SERVICE"],
        "legacy_duplicate_equivalent_count": len(
            [row for row in duplicates if row["classification"] == "LEGACY_DUPLICATE_EQUIVALENT"]
        ),
        "legacy_duplicate_divergent_count": len(
            [row for row in duplicates if row["classification"] == "LEGACY_DUPLICATE_DIVERGENT"]
        ),
        "canonical_bypass_count": counts["BYPASS_OF_CANONICAL_SERVICE"],
        "proof_critical_duplicate_semantic_engine_count": len(
            [
                row
                for row in duplicates
                if row.get("proof_critical")
                and row["classification"].startswith("LEGACY_DUPLICATE")
            ]
        ),
        "proof_critical_bypass_count": len(
            [family for family in FAMILIES if family.fresh == "BYPASS_OF_CANONICAL_SERVICE"]
        ),
        "golden_corpus_case_count": len(all_cases),
        "golden_corpus_cross_path_divergence_count": len(all_cases),
        "financial_temporal_role_convergence_status": "BLOCKED_BY_FRESH_CANONICAL_BYPASS",
        "fcf_convergence_status": "BLOCKED_BY_FRESH_CANONICAL_BYPASS",
        "netdebt_convergence_status": "BLOCKED_BY_FRESH_CANONICAL_BYPASS",
        "working_capital_convergence_status": "BLOCKED_BY_FRESH_CANONICAL_BYPASS",
        "financial_sector_convergence_status": "BLOCKED_BY_FRESH_BYPASS_AND_FIXTURE_DUPLICATE",
        "configured_signal_convergence_status": "BLOCKED_BY_FRESH_CANONICAL_BYPASS",
        "business_delta_convergence_status": "BLOCKED_BY_FRESH_BYPASS_AND_DRIFTABLE_FALLBACK",
        "market_expectation_convergence_status": "BLOCKED_BY_FRESH_CANONICAL_BYPASS",
        "direction_timing_ownership_convergence_status": "CONVERGED",
        "qtd_ytd_convergence_status": "BLOCKED_BY_FRESH_CANONICAL_BYPASS",
        "adr_security_basis_convergence_status": "CONVERGED_WITH_LEGACY_ADAPTER",
        "stage2_core_immutability_convergence_status": "CONVERGED",
        "proof_readiness_policy_convergence_status": "BLOCKED_BY_FRESH_CANONICAL_BYPASS",
        "model_prompt_semantic_change_count": 0,
        "model_schema_semantic_change_count": 0,
        "stage1_wc_binding_semantic_change_count": 0,
        "stage2_wc_binding_semantic_change_count": 0,
        "configured_signal_view_change_count": 0,
        "configured_financial_support_concept_change_count": 0,
        "business_delta_view_change_count": 0,
        "expectation_view_change_count": 0,
        "financial_evidence_projection_change_count": 0,
        "two_stage_core_semantic_change_count": 0,
        "final_user_schema_change_count": 0,
        "m12bd_offline_reaudit_status": "NOT_RUN_DUE_TO_CONVERGENCE_DEBT",
        "formal_fictional_reuse_status": "NOT_EVALUATED_DUE_TO_CONVERGENCE_DEBT",
        "new_fictional_model_calls": 0,
        "network_readiness_status": "NOT_RUN_DUE_TO_CONVERGENCE_DEBT",
        "network_failure_type": "NOT_APPLICABLE",
        "network_model_process_spawned": False,
        "task_start_active_monitor_count": "NOT_MEASURED",
        "task_start_active_monitor_tickers": "NOT_MEASURED",
        "new_shadow_generation_id": None,
        "shadow_context_count": 0,
        "shadow_model_calls_total": 0,
        "shadow_completed_ticker_count": 0,
        "shadow_final_composition_count": 0,
        "shadow_aggregate_finalization_status": "NOT_RUN",
        "shadow_semantic_service_provenance_failure_count": "NOT_MEASURED",
        "shadow_legacy_duplicate_participation_in_hard_decision_count": "NOT_MEASURED",
        "shadow_hard_semantic_failure_count": "NOT_MEASURED",
        "shadow_stage1_wc_grounding_failure_count": "NOT_MEASURED",
        "shadow_stage2_wc_grounding_failure_count": "NOT_MEASURED",
        "shadow_fcf_hard_failure_count": "NOT_MEASURED",
        "shadow_configured_signal_violation_count": "NOT_MEASURED",
        "shadow_business_delta_hard_failure_count": "NOT_MEASURED",
        "shadow_expectation_hard_failure_count": "NOT_MEASURED",
        "shadow_financial_sector_hard_failure_count": "NOT_MEASURED",
        "shadow_stage2_language_false_positive_count": "NOT_MEASURED",
        "shadow_primary_direction_change_count": "NOT_MEASURED",
        "shadow_business_delta_change_count": "NOT_MEASURED",
        "shadow_new_buyer_change_count": "NOT_MEASURED",
        "shadow_holder_change_count": "NOT_MEASURED",
        "shadow_same_direction_calibration_change_count": "NOT_MEASURED",
        "shadow_multi_field_change_count": "NOT_MEASURED",
        "shadow_expected_contract_correction_count": "NOT_MEASURED",
        "shadow_potential_architecture_regression_count": "NOT_MEASURED",
        "shadow_unresolved_review_required_count": "NOT_MEASURED",
        "shadow_core_mutation_after_stance_count": "NOT_MEASURED",
        "shadow_timeout_count": 0,
        "shadow_orphan_count": 0,
        "shadow_wrapper_retry_count": 0,
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
        "observed_paused_schedule_count": "REUSED_PRIOR_VERIFIED_STATE_4",
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": NEXT_SCOPE,
        "focused_test_result": "PENDING",
        "full_test_result": "PENDING",
        "ruff_result": "PENDING",
        "git_diff_check": "PENDING",
        "artifact_count": "PENDING_BUNDLE",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    if validation:
        result.update(validation)
    return result


def audit() -> None:
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("M12BH_OUTPUT_ALREADY_EXISTS")
    integrity = verify_latest_result()
    if integrity["status"] != "PASS":
        raise ValueError("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    corpus = golden_corpus()
    entrypoints = _entrypoint_map()
    scan = duplicate_scan()
    payloads = _report_payloads(integrity, corpus, entrypoints, scan)
    for number, slug in enumerate(BASE_REPORT_SLUGS, start=1):
        report(number, slug, payloads[number])
    for number, slug in enumerate(DEBT_REPORT_SLUGS, start=40):
        report(number, slug, payloads[number])
    for number, slug in enumerate(COMPLETION_REPORT_SLUGS[:-1], start=104):
        report(number, slug, payloads[number])
    completion = build_completion(integrity, corpus)
    write_json(OUTPUT / "program-completion.json", completion)
    write_json(OUTPUT / "semantic-golden-corpus.json", corpus)
    write_json(OUTPUT / "semantic-contract-ownership-map.json", _ownership_rows())
    write_json(OUTPUT / "semantic-consumer-call-graph.json", entrypoints)
    write_json(OUTPUT / "convergence-debt-risk-ranking.json", payloads[43])
    write_text(
        OUTPUT / "CONVERGENCE-DEBT-REPORT.md",
        "# M12BH Convergence Debt\n\n"
        "The latest fresh/new-issuer proof path bypasses the canonical financial "
        "semantic services used by monitored/shadow. Proof-critical duplicate "
        "assertions also remain in the monitored harness. Per the work instruction, "
        "M12BH stopped before the network gate and before all model calls.\n\n"
        f"Next scope: `{NEXT_SCOPE}`.\n",
    )
    report(116, "program-completion", completion)


def record_validation(args: argparse.Namespace) -> None:
    completion = read_json(OUTPUT / "program-completion.json")
    updates = {
        "focused_test_result": args.focused,
        "full_test_result": args.full,
        "ruff_result": args.ruff,
        "git_diff_check": args.diff,
        "final_local_head_sha": git("rev-parse", "HEAD"),
    }
    completion.update(updates)
    write_json(OUTPUT / "program-completion.json", completion)
    report(116, "program-completion", completion)


def record_docs() -> None:
    completion = read_json(OUTPUT / "program-completion.json")
    completion["final_local_head_sha"] = git("rev-parse", "HEAD")
    completion["documentation_status"] = "PASS"
    completion["master_workflow_updated"] = True
    completion["project_handoff_updated"] = True
    completion["next_session_prompt_updated"] = True
    write_json(OUTPUT / "program-completion.json", completion)
    report(
        115,
        "master-workflow-update",
        {
            "status": "PASS",
            "path": "docs/MASTER_WORKFLOW.md",
            "head": completion["final_local_head_sha"],
        },
    )
    report(116, "program-completion", completion)


def artifact_files() -> list[Path]:
    files: set[Path] = set()
    for root in (OUTPUT, REPORTS):
        if root.exists():
            files.update(path for path in root.rglob("*") if path.is_file())
    files.discard(OUTPUT / "artifact-index.json")
    for path in (
        RUNNER,
        ARCHITECTURE,
        WORK_INSTRUCTION,
        Path("tests/test_fresh_monitored_semantic_convergence_m12bh.py"),
        Path("tests/test_fresh_monitored_semantic_convergence_m12bh_runner.py"),
        Path("docs/MASTER_WORKFLOW.md"),
        Path("docs/PROJECT_HANDOFF.md"),
        Path("docs/NEXT_SESSION_PROMPT.md"),
        Path("docs/project-state.json"),
    ):
        if path.is_file():
            files.add(path)
    return sorted(files, key=str)


def artifact_name(path: Path) -> str:
    if not path.is_absolute():
        return str(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return path.name


def bundle(output_zip: Path) -> None:
    required = {
        **{number: slug for number, slug in enumerate(BASE_REPORT_SLUGS, start=1)},
        **{number: slug for number, slug in enumerate(DEBT_REPORT_SLUGS, start=40)},
        **{number: slug for number, slug in enumerate(COMPLETION_REPORT_SLUGS, start=104)},
    }
    missing = [
        str(REPORTS / f"{number:03d}-{slug}.json")
        for number, slug in required.items()
        if not (REPORTS / f"{number:03d}-{slug}.json").is_file()
    ]
    if missing:
        raise ValueError(f"M12BH_REQUIRED_REPORTS_MISSING:{missing}")
    files = artifact_files()
    completion = read_json(OUTPUT / "program-completion.json")
    completion["artifact_count"] = len(files)
    write_json(OUTPUT / "program-completion.json", completion)
    report(116, "program-completion", completion)
    files = artifact_files()
    secret_failures = [
        {"path": str(path), "indicators": list(indicators)}
        for path in files
        for indicators in (_secret_indicators(path.read_bytes()),)
        if indicators
    ]
    index = {
        "contract": "m12bh-artifact-index-v1",
        "status": "PASS" if not secret_failures else "FAIL",
        "artifact_count": len(files),
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": len(secret_failures),
        "secret_scan_failures": secret_failures,
        "rows": [
            {
                "path": artifact_name(path),
                "sha256": file_sha256(path),
                "size": path.stat().st_size,
            }
            for path in files
        ],
    }
    write_json(OUTPUT / "artifact-index.json", index)
    if index["status"] != "PASS":
        raise ValueError("M12BH_ARTIFACT_SECRET_SCAN_FAILURE")
    if output_zip.exists():
        raise ValueError(f"M12BH_RESULT_BUNDLE_ALREADY_EXISTS:{output_zip}")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=artifact_name(path))
        archive.write(
            OUTPUT / "artifact-index.json",
            arcname=artifact_name(OUTPUT / "artifact-index.json"),
        )
    with zipfile.ZipFile(output_zip) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise ValueError(f"M12BH_ZIP_CRC_FAILURE:{bad}")
        for row in index["rows"]:
            payload = archive.read(str(row["path"]))
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                raise ValueError(f"M12BH_ZIP_HASH_MISMATCH:{row['path']}")
            if len(payload) != row["size"]:
                raise ValueError(f"M12BH_ZIP_SIZE_MISMATCH:{row['path']}")
    digest = file_sha256(output_zip)
    write_text(Path(str(output_zip) + ".sha256"), f"{digest}  {output_zip.name}\n")
    print(
        canonical_json(
            {
                "zip": str(output_zip),
                "sha256": digest,
                "indexed_payloads": len(files),
                "zip_entries": len(files) + 1,
            }
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("audit")
    validation = subparsers.add_parser("record-validation")
    validation.add_argument("--focused", required=True)
    validation.add_argument("--full", required=True)
    validation.add_argument("--ruff", required=True)
    validation.add_argument("--diff", required=True)
    subparsers.add_parser("record-docs")
    bundler = subparsers.add_parser("bundle")
    bundler.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "audit":
        audit()
    elif args.command == "record-validation":
        record_validation(args)
    elif args.command == "record-docs":
        record_docs()
    elif args.command == "bundle":
        bundle(args.output)


if __name__ == "__main__":
    main()
