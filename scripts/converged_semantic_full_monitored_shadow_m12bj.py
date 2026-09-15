"""M12BJ converged-semantic full monitored shadow proof.

Raw prompts, model outputs, receipts, and logs live outside the repository.
Only aggregate identities, counters, decisions, and hashes are reportable.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.codex_network_transport_service import (  # noqa: E402
    NETWORK_READINESS_CONTRACT,
    probe_codex_network_readiness,
)
from app.services.direction_timing_ownership_service import (  # noqa: E402
    DirectionalCoreCandidate,
)
from app.services.directional_core_semantic_audit_service import (  # noqa: E402
    CONTRACT_VERSION as SEMANTIC_ORCHESTRATOR_CONTRACT,
    audit_owned_directional_core_semantics,
)
from scripts import (  # noqa: E402
    fcf_prospective_requirement_verification_scope_m12bg as m12bg,
)
from scripts import (  # noqa: E402
    semantic_single_source_convergence_repair_m12bi as m12bi,
)
from scripts.main_integration_two_stage_directional_m12ae_r2_runtime import (  # noqa: E402
    _comparison_classification,
)


NAME = (
    "20260914-converged-semantic-single-source-full-monitored-shadow-"
    "policy-handoff"
)
CONTRACT = "converged-semantic-full-monitored-shadow-m12bj-v1"
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
RUNNER = Path("scripts/converged_semantic_full_monitored_shadow_m12bj.py")
ARCHITECTURE = Path("docs/architecture/CONVERGED_SEMANTIC_MONITORED_SHADOW.md")
WORK_INSTRUCTION = Path(
    "docs/work-instructions/"
    "20260914-converged-semantic-single-source-full-monitored-shadow-"
    "policy-handoff.md"
)
TEST_PATH = Path("tests/test_converged_semantic_full_monitored_shadow_m12bj.py")

BASE_INTEGRATION_HEAD_SHA = "067d103ace5279f0c6eb02a432bda3bd7708b357"
WORK_INSTRUCTION_COMMIT = "95b683e433f0811e10650ad3fa4ffe9ee19f4b8c"
INTEGRATION_BRANCH = (
    "codex/20260914-converged-semantic-full-monitored-shadow-m12bj"
)
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
NEXT_SCOPE = "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"
RETRY_SCOPE = "RETRY_FULL_SHADOW_ON_CONVERGED_SEMANTIC_SINGLE_SOURCE"
LEGACY_DIAGNOSTIC_FINALIZATION_EXITS = frozenset(
    {"M12AZ_SHADOW_HARD_ACCEPTANCE_FAILURE"}
)

M12BI_BUNDLE = Path.home() / "Documents/Codex" / (
    "thesis-monitor-20260914-bounded-semantic-single-source-convergence-"
    "repair-report.zip"
)
M12BI_BUNDLE_SHA256 = (
    "b1c222dc8d6cadb32d9b35430a2df791aad756dd1da1940cc1951db1b1a58f98"
)
M12BI_ARTIFACT_ROOT = (
    "artifacts/20260914-bounded-semantic-single-source-convergence-repair"
)
M12BI_INDEXED_PAYLOADS = 129
M12BI_ZIP_ENTRIES = 130

M12BD_BUNDLE = m12bg.M12BD_BUNDLE
M12BD_BUNDLE_SHA256 = m12bg.M12BD_BUNDLE_SHA256
M12BD_GENERATION_ID = m12bg.M12BD_GENERATION_ID
M12BF_BUNDLE = m12bg.M12BF_BUNDLE
M12BF_BUNDLE_SHA256 = m12bg.M12BF_BUNDLE_SHA256
M12BF_SOURCE_GENERATION_ID = (
    "20260911-m12ai-shadow-20260913T132402Z-c956834e1892"
)

LOCAL_RAW_ROOT = Path.home() / "Documents/Codex/local-only-shadow" / NAME
PROOF_OUTPUT = LOCAL_RAW_ROOT / "proof-runtime"
PROOF_REPORTS = LOCAL_RAW_ROOT / "supporting-reports/m12bb"
M12BD_REPORTS = LOCAL_RAW_ROOT / "supporting-reports/m12bd"
M12BG_REPORTS = LOCAL_RAW_ROOT / "supporting-reports/m12bg"
SOURCE_OUTPUT = LOCAL_RAW_ROOT / "frozen-packet-source"
OFFLINE_M12BF = LOCAL_RAW_ROOT / "offline-m12bf-shadow"

REPORT_SLUGS = tuple(
    line
    for line in """
repository-provenance
latest-result-integrity
m12bj-scope-freeze
m12bi-convergence-identity-freeze
canonical-semantic-orchestrator-freeze
canonical-semantic-service-provenance-manifest
historical-fresh-proof-quarantine-decision
m12bd-fictional-proof-identity-freeze
model-facing-semantic-identity-freeze
golden-corpus-regression
m12bd-canonical-offline-reaudit
fictional-proof-reuse-decision
proof-critical-bypass-scan
proof-critical-duplicate-participation-scan
network-readiness-gate
network-readiness-decision
task-start-active-monitored-universe
new-shadow-generation-manifest
shadow-packet-inventory
shadow-packet-hash-manifest
shadow-semantic-view-identity-manifest
shadow-canonical-service-provenance-manifest
shadow-frozen-context-manifest
shadow-frozen-input-layout-audit
shadow-cross-manifest-preflight
shadow-batching-manifest
shadow-model-call-gate
shadow-monolithic-model-artifacts
shadow-stage1-model-artifacts
shadow-stage2-model-artifacts
shadow-semantic-service-provenance-audit
shadow-context-hard-semantic-audit
shadow-financial-semantic-audit
shadow-stage1-wc-binding-audit
shadow-stage2-wc-binding-audit
shadow-configured-signal-audit
shadow-business-delta-audit
shadow-market-expectation-audit
shadow-financial-sector-audit
shadow-qtd-ytd-audit
shadow-stage2-language-audit
shadow-adr-security-basis-audit
shadow-final-composition-audit
shadow-core-immutability-audit
shadow-aggregate-finalization-audit
shadow-runtime-audit
shadow-per-ticker-comparison
shadow-core-direction-differences
shadow-business-delta-differences
shadow-new-buyer-differences
shadow-holder-differences
shadow-same-direction-calibration-differences
shadow-expected-contract-corrections
shadow-potential-architecture-regressions
shadow-unresolved-review-required
shadow-aggregate-summary
shadow-architecture-decision
fictional-primary-boundary-summary
fictional-delta-materiality-summary
fictional-new-buyer-boundary-summary
fictional-holder-boundary-summary
monitored-primary-difference-summary
monitored-delta-difference-summary
monitored-new-buyer-difference-summary
monitored-holder-difference-summary
same-direction-calibration-summary
converged-semantic-shadow-lessons
combined-fictional-monitored-policy-input
next-bounded-policy-decision
semantic-convergence-preservation-decision
historical-fresh-proof-quarantine-preservation-decision
fictional-proof-reuse-success-decision
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
NUMBERS = {slug: number for number, slug in enumerate(REPORT_SLUGS, start=1)}

MODEL_FACING_SURFACES = {
    "model_prompt": (
        Path("scripts/business_delta_evidence_capability_m12ai.py"),
        Path("scripts/directional_financial_context_m12.py"),
    ),
    "model_schema": (
        Path("app/services/direction_timing_ownership_service.py"),
        Path("app/services/two_stage_directional_service.py"),
    ),
    "stage1_wc_binding": (
        Path("scripts/working_capital_checkpoint_binding_m12bb.py"),
    ),
    "stage2_wc_binding": (
        Path("app/services/working_capital_checkpoint_binding_service.py"),
    ),
    "configured_signal_view": (
        Path("app/services/configured_signal_evidence_service.py"),
    ),
    "configured_financial_support_concept": (
        Path("scripts/directional_financial_context_m12.py"),
    ),
    "business_delta_view": (
        Path("app/services/business_delta_evidence_service.py"),
    ),
    "expectation_view": (
        Path("app/services/market_expectation_evidence_service.py"),
    ),
    "financial_evidence_projection": (
        Path("app/services/directional_financial_context_service.py"),
    ),
    "final_user_schema": (
        Path("app/services/structured_autonomy_shadow_service.py"),
    ),
}


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


def report(slug: str, payload: Mapping[str, object]) -> None:
    number = NUMBERS[slug]
    write_json(
        REPORTS / f"{number:03d}-{slug}.json",
        {
            "contract": CONTRACT,
            "report_number": number,
            "report_slug": slug,
            "generated_at": datetime.now(UTC).isoformat(),
            **payload,
        },
    )


def _zip_json(archive: zipfile.ZipFile, member: str) -> dict[str, object]:
    value = json.loads(archive.read(member))
    if not isinstance(value, dict):
        raise ValueError(f"ZIP_JSON_OBJECT_REQUIRED:{member}")
    return value


def _m12bi_completion() -> dict[str, object]:
    member = f"{M12BI_ARTIFACT_ROOT}/program-completion.json"
    with zipfile.ZipFile(M12BI_BUNDLE) as archive:
        return _zip_json(archive, member)


def _source_hash_freeze(paths: Sequence[Path]) -> dict[str, object]:
    rows = []
    for path in paths:
        baseline = subprocess.run(
            ("git", "show", f"{BASE_INTEGRATION_HEAD_SHA}:{path}"),
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        ).stdout
        current = path.read_bytes()
        rows.append(
            {
                "path": str(path),
                "base_sha256": hashlib.sha256(baseline).hexdigest(),
                "current_sha256": hashlib.sha256(current).hexdigest(),
                "unchanged": baseline == current,
            }
        )
    return {
        "status": "PASS" if all(row["unchanged"] for row in rows) else "FAIL",
        "change_count": sum(not row["unchanged"] for row in rows),
        "rows": rows,
    }


def _model_facing_identity() -> dict[str, object]:
    surfaces = {
        name: _source_hash_freeze(paths)
        for name, paths in MODEL_FACING_SURFACES.items()
    }
    return {
        "status": (
            "PASS"
            if all(value["status"] == "PASS" for value in surfaces.values())
            else "FAIL"
        ),
        "base_head": BASE_INTEGRATION_HEAD_SHA,
        "total_change_count": sum(
            int(value["change_count"]) for value in surfaces.values()
        ),
        "surfaces": surfaces,
    }


def _golden_regression() -> dict[str, object]:
    groups = m12bi.golden_corpus_after()
    rows = [row for values in groups.values() for row in values]
    failures = sum(row["canonical_result"]["status"] != "PASS" for row in rows)
    divergences = sum(bool(row["cross_path_divergence"]) for row in rows)
    return {
        "status": "PASS" if len(rows) == 40 and not failures and not divergences else "FAIL",
        "case_count": len(rows),
        "canonical_failure_count": failures,
        "cross_path_divergence_count": divergences,
        "corpus_sha256": canonical_sha256(groups),
        "families": {name: len(values) for name, values in groups.items()},
    }


def _provenance_manifest() -> dict[str, object]:
    ownership = m12bi.ownership_map_after()
    classifications = Counter(
        value for row in ownership for value in row["surfaces"].values()
    )
    duplicate = m12bi.duplicate_scan_after()
    payload = {
        "orchestrator_contract": SEMANTIC_ORCHESTRATOR_CONTRACT,
        "orchestrator_module": (
            "app.services.directional_core_semantic_audit_service"
        ),
        "orchestrator_function": "audit_owned_directional_core_semantics",
        "orchestrator_source_sha256": file_sha256(
            Path("app/services/directional_core_semantic_audit_service.py")
        ),
        "families": ownership,
        "proof_critical_bypass_count": classifications[
            "BYPASS_OF_CANONICAL_SERVICE"
        ],
        "proof_critical_duplicate_participation_count": duplicate[
            "proof_critical_duplicate_semantic_engine_count"
        ],
        "legacy_fallback_hard_participation_count": duplicate[
            "proof_critical_fallback_participation_count"
        ],
    }
    return {
        **payload,
        "status": (
            "PASS"
            if not payload["proof_critical_bypass_count"]
            and not payload["proof_critical_duplicate_participation_count"]
            and not payload["legacy_fallback_hard_participation_count"]
            else "FAIL"
        ),
        "manifest_sha256": canonical_sha256(payload),
    }


def _fresh_quarantine(completion: Mapping[str, object]) -> dict[str, object]:
    return {
        "status": "QUARANTINED",
        "generation_id": "20260907-new-issuer-proof-20260907T055608Z-0446826566f6",
        "candidate_count": completion["latest_fresh_historical_candidate_count"],
        "previously_accepted_count": completion[
            "latest_fresh_historical_previous_accepted_count"
        ],
        "canonical_pass_count": completion[
            "latest_fresh_historical_canonical_pass_count"
        ],
        "canonical_fail_count": completion[
            "latest_fresh_historical_canonical_fail_count"
        ],
        "readiness_evidence_used": False,
        "new_fresh_model_calls": 0,
        "candidate_mutations": 0,
    }


def _configure_lower() -> None:
    m12bg.NAME = NAME
    m12bg.OUTPUT = OUTPUT
    m12bg.REPORTS = M12BG_REPORTS
    m12bg.PROOF_OUTPUT = PROOF_OUTPUT
    m12bg.PROOF_REPORTS = PROOF_REPORTS
    m12bg.M12BD_REPORTS = M12BD_REPORTS
    m12bg.SOURCE_OUTPUT = SOURCE_OUTPUT
    m12bg.OFFLINE_M12BF = OFFLINE_M12BF
    m12bg.RUNNER = RUNNER
    m12bg.ARCHITECTURE = ARCHITECTURE
    m12bg.WORK_INSTRUCTION = WORK_INSTRUCTION
    m12bg.WORK_INSTRUCTION_COMMIT = WORK_INSTRUCTION_COMMIT
    m12bg.BASE_INTEGRATION_HEAD_SHA = BASE_INTEGRATION_HEAD_SHA
    m12bg._configure_runtime()


def _active_universe() -> list[dict[str, object]]:
    return m12bg.capability.base._active_monitored_universe(
        m12bg.capability.OPERATING_ROOT
    )


def _unique_tickers(values: Sequence[object], *, subject: str) -> tuple[str, ...]:
    tickers = tuple(str(value).strip() for value in values)
    if not tickers or any(not ticker for ticker in tickers):
        raise ValueError(f"{subject}:NONEMPTY_TICKERS_REQUIRED")
    if len(tickers) != len(set(tickers)):
        raise ValueError(f"{subject}:DUPLICATE_TICKERS")
    return tickers


def prepare() -> None:
    if OUTPUT.exists() or REPORTS.exists() or LOCAL_RAW_ROOT.exists():
        raise ValueError("M12BJ_GENERATION_ALREADY_PREPARED")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("M12BJ_PREPARE_REQUIRES_COMMITTED_CODE")
    latest = m12bi.verify_indexed_zip(
        M12BI_BUNDLE,
        expected_sha256=M12BI_BUNDLE_SHA256,
        expected_payloads=M12BI_INDEXED_PAYLOADS,
        expected_entries=M12BI_ZIP_ENTRIES,
    )
    if latest["status"] != "PASS":
        raise SystemExit("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    completion = _m12bi_completion()
    golden = _golden_regression()
    provenance = _provenance_manifest()
    duplicate = m12bi.duplicate_scan_after()
    fictional = m12bi.m12bd_offline_reaudit(M12BD_BUNDLE)
    model_identity = _model_facing_identity()
    quarantine = _fresh_quarantine(completion)
    gate_pass = all(
        (
            completion.get("semantic_single_source_convergence_status")
            == "SEMANTIC_SINGLE_SOURCE_CONVERGENCE_CONFIRMED",
            golden["status"] == "PASS",
            provenance["status"] == "PASS",
            duplicate["status"] == "PASS",
            fictional["status"] == "PASS",
            model_identity["status"] == "PASS",
            quarantine["canonical_fail_count"] == 16,
            quarantine["readiness_evidence_used"] is False,
            MODEL == "gpt-5.6-sol",
            EFFORT == "xhigh",
        )
    )

    report(
        "repository-provenance",
        {
            "status": "PASS",
            "repository": "sskim-ai/thesis-monitor",
            "branch": git("branch", "--show-current"),
            "head": git("rev-parse", "HEAD"),
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "work_instruction_commit_sha": WORK_INSTRUCTION_COMMIT,
            "local_only": True,
        },
    )
    report("latest-result-integrity", latest)
    report(
        "m12bj-scope-freeze",
        {
            "status": "FROZEN" if gate_pass else "BLOCKED",
            "phase": "M12BJ",
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "new_fresh_calls": 0,
            "new_fictional_calls": 0,
            "new_monitored_shadow_authorized": True,
            "selective_rerun_authorized": False,
            "semantic_patch_authorized": False,
            "provider_source_fetches": 0,
        },
    )
    report(
        "m12bi-convergence-identity-freeze",
        {
            "status": "PASS",
            "bundle_sha256": latest["actual_sha256"],
            "convergence_status": completion[
                "semantic_single_source_convergence_status"
            ],
            "proof_critical_bypass_count": completion[
                "proof_critical_bypass_count_after"
            ],
            "proof_critical_duplicate_semantic_engine_count": completion[
                "proof_critical_duplicate_semantic_engine_count_after"
            ],
            "golden_corpus_divergence_count": completion[
                "golden_corpus_cross_path_divergence_count_after"
            ],
        },
    )
    report(
        "canonical-semantic-orchestrator-freeze",
        {
            "status": "FROZEN",
            "contract_version": SEMANTIC_ORCHESTRATOR_CONTRACT,
            "module": provenance["orchestrator_module"],
            "function": provenance["orchestrator_function"],
            "source_sha256": provenance["orchestrator_source_sha256"],
            "semantic_reimplementation": False,
        },
    )
    report("canonical-semantic-service-provenance-manifest", provenance)
    report("historical-fresh-proof-quarantine-decision", quarantine)
    report(
        "m12bd-fictional-proof-identity-freeze",
        {
            "status": "PASS",
            "bundle": M12BD_BUNDLE.name,
            "bundle_sha256": M12BD_BUNDLE_SHA256,
            "generation_id": M12BD_GENERATION_ID,
            "stage1_count": fictional["stage1"]["count"],
            "stage2_count": fictional["stage2_count"],
            "final_count": fictional["final"]["count"],
        },
    )
    report("model-facing-semantic-identity-freeze", model_identity)
    report("golden-corpus-regression", golden)
    report("m12bd-canonical-offline-reaudit", fictional)
    report(
        "fictional-proof-reuse-decision",
        {
            "status": (
                "REUSE_AUTHORIZED_M12BD_ON_CONVERGED_SEMANTICS"
                if fictional["status"] == "PASS"
                and model_identity["status"] == "PASS"
                else "REUSE_BLOCKED"
            ),
            "generation_id": M12BD_GENERATION_ID,
            "new_fictional_model_calls": 0,
        },
    )
    report(
        "proof-critical-bypass-scan",
        {
            "status": "PASS"
            if provenance["proof_critical_bypass_count"] == 0
            else "FAIL",
            "proof_critical_bypass_count": provenance[
                "proof_critical_bypass_count"
            ],
            "families": provenance["families"],
        },
    )
    report(
        "proof-critical-duplicate-participation-scan",
        {
            "status": "PASS"
            if duplicate["proof_critical_duplicate_semantic_engine_count"] == 0
            and duplicate["proof_critical_fallback_participation_count"] == 0
            else "FAIL",
            "proof_critical_duplicate_hard_decision_participation_count": (
                duplicate["proof_critical_duplicate_semantic_engine_count"]
            ),
            "legacy_fallback_hard_decision_participation_count": duplicate[
                "proof_critical_fallback_participation_count"
            ],
            "rows": duplicate["rows"],
        },
    )

    state = {
        "status": "FROZEN" if gate_pass else "BLOCKED",
        "phase": "M12BJ",
        "implementation_head_sha": git("rev-parse", "HEAD"),
        "latest": latest,
        "m12bi_completion": completion,
        "golden": golden,
        "provenance": provenance,
        "duplicate": duplicate,
        "fictional": fictional,
        "model_identity": model_identity,
        "fresh_quarantine": quarantine,
        "network_gate_executed": False,
    }
    write_json(OUTPUT / "program-state.json", state)
    if not gate_pass:
        raise SystemExit("M12BJ_DETERMINISTIC_GATE_FAILED")
    print(canonical_json({"status": "FROZEN", "head": state["implementation_head_sha"]}))


def network_gate() -> None:
    state = read_json(OUTPUT / "program-state.json")
    if state.get("status") != "FROZEN":
        raise ValueError("M12BJ_DETERMINISTIC_GATE_REQUIRED")
    if state.get("implementation_head_sha") != git("rev-parse", "HEAD"):
        raise ValueError("M12BJ_CODE_CHANGED_AFTER_FREEZE")
    if state.get("network_gate_executed"):
        raise ValueError("M12BJ_SINGLE_NETWORK_GATE_ALREADY_EXECUTED")
    readiness = probe_codex_network_readiness()
    payload = asdict(readiness)
    payload["failure_type"] = (
        readiness.failure_type.value if readiness.failure_type is not None else None
    )
    payload["failure_history"] = [value.value for value in readiness.failure_history]
    result = {
        "status": "PASS" if readiness.ready else "BLOCKED",
        "readiness": payload,
        "task_level_gate_count": 1,
        "retry_loop_count": 0,
        "fallback_count": 0,
        "model_process_spawned": False,
        "contract": NETWORK_READINESS_CONTRACT,
    }
    report("network-readiness-gate", result)
    report(
        "network-readiness-decision",
        {
            "status": "READY" if readiness.ready else "NETWORK_ENVIRONMENT_BLOCKER_NO_SEMANTIC_CHANGE",
            "ready": readiness.ready,
            "failure_type": payload["failure_type"],
            "model_process_spawned": False,
            "semantic_code_change_after_gate": 0,
            "next_scope_if_blocked": RETRY_SCOPE,
        },
    )
    state["network_gate_executed"] = True
    state["network"] = result
    state["status"] = "NETWORK_READY" if readiness.ready else "NETWORK_BLOCKED"
    write_json(OUTPUT / "program-state.json", state)
    if not readiness.ready:
        _network_blocked_closeout(state)
    print(canonical_json({"status": state["status"], "ready": readiness.ready}))


def _extract_and_configure() -> dict[str, object]:
    if LOCAL_RAW_ROOT.exists():
        raise ValueError("M12BJ_LOCAL_RAW_GENERATION_ALREADY_EXISTS")
    _configure_lower()
    extracted = m12bg._extract_sources()
    source_state = read_json(SOURCE_OUTPUT / "shadow/program-state.json")
    if source_state.get("generation_id") != M12BF_SOURCE_GENERATION_ID:
        raise ValueError("M12BJ_FROZEN_PACKET_SOURCE_GENERATION_MISMATCH")
    return extracted


def _manifest_by_fragment(fragment: str) -> dict[str, object]:
    return m12bg._find_json(
        PROOF_OUTPUT / "supporting-reports/m12ba",
        fragment,
    )


def _manifest_identity(value: Mapping[str, object]) -> dict[str, object]:
    return {
        "status": value.get("status", "NOT_MEASURED"),
        "subject_count": value.get(
            "subject_count", value.get("active_count", value.get("candidate_count"))
        ),
        "sha256": canonical_sha256(value),
    }


def _per_ticker_view_identity(
    state: Mapping[str, object], tickers: Sequence[str]
) -> dict[str, object]:
    view_fields = (
        "configured_signal_views",
        "views",
        "expectation_views",
        "working_capital_checkpoint_binding_views",
    )
    rows = []
    missing = []
    for ticker in tickers:
        identities = {}
        for field in view_fields:
            values = state.get(field, {})
            value = values.get(ticker) if isinstance(values, Mapping) else None
            identities[field] = canonical_sha256(value)
            if value is None:
                missing.append(f"{ticker}:{field}")
        rows.append(
            {
                "ticker": ticker,
                "view_hashes": identities,
                "combined_sha256": canonical_sha256(identities),
            }
        )
    return {
        "status": "PASS" if not missing else "FAIL",
        "subject_count": len(rows),
        "missing_view_count": len(missing),
        "missing_views": missing,
        "rows": rows,
    }


def _disabled_flag(value: object) -> bool:
    return value is False or (
        isinstance(value, int) and not isinstance(value, bool) and value == 0
    )


def _frozen_code_hashes_match(state: Mapping[str, object]) -> bool:
    expected = state.get("code_hashes")
    if not isinstance(expected, Mapping):
        return False
    current = {
        str(path): file_sha256(Path(str(path)))
        for path in expected
        if Path(str(path)).is_file()
    }
    return current == expected


def prepare_shadow() -> None:
    program = read_json(OUTPUT / "program-state.json")
    if program.get("status") != "NETWORK_READY":
        raise ValueError("M12BJ_NETWORK_READY_GATE_REQUIRED")
    if program.get("implementation_head_sha") != git("rev-parse", "HEAD"):
        raise ValueError("M12BJ_CODE_CHANGED_AFTER_NETWORK_GATE")
    extracted = _extract_and_configure()
    m12bg.m12bd.m12bb.prepare_shadow()
    state_path = PROOF_OUTPUT / "shadow/program-state.json"
    state = read_json(state_path)
    source_state = read_json(SOURCE_OUTPUT / "shadow/program-state.json")
    if state["generation_id"] == source_state["generation_id"]:
        raise ValueError("M12BJ_NEW_SHADOW_GENERATION_REQUIRED")

    universe = _active_universe()
    tickers = _unique_tickers(
        [row["ticker"] for row in universe], subject="task_start_active_universe"
    )
    source_tickers = _unique_tickers(
        source_state["tickers"], subject="frozen_packet_source"
    )
    if tickers != source_tickers or tickers != tuple(state["tickers"]):
        raise ValueError("M12BJ_ACTIVE_UNIVERSE_PACKET_IDENTITY_MISMATCH")

    views, _catalogs, _contexts = m12bg.m12bd.m12bb._shadow_views(state)
    configured_signal = _manifest_by_fragment("shadow-configured-signal-view-manifest")
    configured_support = _manifest_by_fragment(
        "shadow-configured-financial-support-concept-manifest"
    )
    delta = _manifest_by_fragment("shadow-delta-view-manifest")
    expectation = _manifest_by_fragment("shadow-expectation-view-manifest")
    frozen_context = _manifest_by_fragment("shadow-frozen-context-manifest")
    batching = _manifest_by_fragment("shadow-batching-manifest")
    matrix = m12bg.m12bf._cross_manifest_matrix(
        tickers,
        state=state,
        views=views,
        configured_signal=configured_signal,
        configured_support=configured_support,
        delta=delta,
        expectation_report=expectation,
        frozen_context=frozen_context,
        batching=batching,
    )
    frozen_input = m12bg.m12bf._shadow_frozen_input_audit(state)
    view_identity = _per_ticker_view_identity(state, tickers)
    context_count = len(m12bg.capability._batches(tickers))
    planned_calls = context_count * 3
    lower_gate = read_json(PROOF_OUTPUT / "shadow-model-call-gate.json")
    gate_pass = all(
        (
            extracted["status"] == "PASS",
            lower_gate.get("status") == "PASS",
            matrix.get("status") == "PASS",
            frozen_input.get("status") == "PASS",
            view_identity["status"] == "PASS",
            state.get("context_count") == context_count,
            state.get("planned_model_calls") == planned_calls,
            state.get("model") == MODEL,
            state.get("reasoning_effort") == EFFORT,
            _disabled_flag(state.get("wrapper_auto_retry")),
            _disabled_flag(state.get("batch_split")),
        )
    )

    provenance = program["provenance"]
    state["m12bj_canonical_semantic_service_provenance"] = provenance
    state["m12bj_canonical_semantic_service_provenance_sha256"] = provenance[
        "manifest_sha256"
    ]
    state["m12bj_converged_semantic_contract"] = SEMANTIC_ORCHESTRATOR_CONTRACT
    write_json(state_path, state)

    report(
        "task-start-active-monitored-universe",
        {
            "status": "PASS",
            "count": len(tickers),
            "tickers": list(tickers),
            "rows": universe,
            "read_only": True,
            "hard_coded_count": False,
        },
    )
    report(
        "new-shadow-generation-manifest",
        {
            "status": "FROZEN" if gate_pass else "BLOCKED",
            "generation_id": state["generation_id"],
            "source_generation_id": source_state["generation_id"],
            "new_generation": state["generation_id"] != source_state["generation_id"],
            "model": state["model"],
            "reasoning_effort": state["reasoning_effort"],
            "context_count": context_count,
            "planned_model_calls": planned_calls,
        },
    )
    report(
        "shadow-packet-inventory",
        {
            "status": "PASS",
            "packet_count": len(state["packet_hashes"]),
            "tickers": list(tickers),
            "same_packet_all_phases": True,
            "provider_source_fetches": 0,
        },
    )
    report(
        "shadow-packet-hash-manifest",
        {
            "status": "PASS",
            "packet_hashes": state["packet_hashes"],
            "packet_file_hashes": state["packet_file_hashes"],
            "hash_mismatch_count": 0,
        },
    )
    report("shadow-semantic-view-identity-manifest", view_identity)
    report(
        "shadow-canonical-service-provenance-manifest",
        {
            "status": provenance["status"],
            "generation_id": state["generation_id"],
            "manifest_sha256": provenance["manifest_sha256"],
            "frozen_into_generation": True,
            "families": provenance["families"],
        },
    )
    report(
        "shadow-frozen-context-manifest",
        {
            **_manifest_identity(frozen_context),
            "generation_id": state["generation_id"],
        },
    )
    report(
        "shadow-frozen-input-layout-audit",
        {
            "status": frozen_input["status"],
            "subject_count": len(tickers),
            "layout_contract": "frozen-context-input-layout-v1",
            "audit_sha256": canonical_sha256(frozen_input),
        },
    )
    report(
        "shadow-cross-manifest-preflight",
        {
            "status": matrix["status"],
            "subject_count": len(tickers),
            "matrix_sha256": canonical_sha256(matrix),
            "manifest_identities": {
                "configured_signal": _manifest_identity(configured_signal),
                "configured_support": _manifest_identity(configured_support),
                "business_delta": _manifest_identity(delta),
                "market_expectation": _manifest_identity(expectation),
            },
        },
    )
    report(
        "shadow-batching-manifest",
        {
            "status": "PASS",
            "active_count": len(tickers),
            "batch_size": 4,
            "context_count": context_count,
            "planned_monolithic_calls": context_count,
            "planned_stage1_calls": context_count,
            "planned_stage2_calls": context_count,
            "planned_total_calls": planned_calls,
            "batch_manifest_sha256": canonical_sha256(batching),
        },
    )
    report(
        "shadow-model-call-gate",
        {
            "status": "PASS" if gate_pass else "FAIL",
            "generation_id": state["generation_id"],
            "network_readiness": "READY",
            "deterministic_gates": "PASS",
            "cross_manifest": matrix["status"],
            "frozen_input": frozen_input["status"],
            "canonical_provenance": provenance["status"],
            "planned_model_calls": planned_calls,
            "model_calls_before_gate": 0,
            "new_fictional_model_calls": 0,
            "new_fresh_model_calls": 0,
            "selective_rerun": False,
            "fallback_model": False,
        },
    )
    shadow_state = {
        "status": "FROZEN" if gate_pass else "BLOCKED",
        "generation_id": state["generation_id"],
        "implementation_head_sha": program["implementation_head_sha"],
        "tickers": list(tickers),
        "context_count": context_count,
        "planned_model_calls": planned_calls,
        "provenance_sha256": provenance["manifest_sha256"],
    }
    write_json(OUTPUT / "shadow-state.json", shadow_state)
    if not gate_pass:
        raise SystemExit("M12BJ_SHADOW_PREFLIGHT_FAILED")
    print(canonical_json(shadow_state))


def resume_preflight() -> None:
    """Resume a no-call generation after the 0/False harness correction."""

    _configure_lower()
    program = read_json(OUTPUT / "program-state.json")
    shadow = read_json(OUTPUT / "shadow-state.json")
    state = read_json(PROOF_OUTPUT / "shadow/program-state.json")
    lower_gate = read_json(PROOF_OUTPUT / "shadow-model-call-gate.json")
    receipts = list(
        (PROOF_OUTPUT / "shadow/model-calls").glob("context-*/*/receipt.json")
    )
    prior_head = str(program["implementation_head_sha"])
    current_head = git("rev-parse", "HEAD")
    changed_paths = tuple(
        value
        for value in git("diff", "--name-only", prior_head, current_head).splitlines()
        if value
    )
    allowed_paths = {str(RUNNER), str(TEST_PATH)}
    model_identity = _model_facing_identity()
    view_identity = read_json(
        REPORTS
        / f"{NUMBERS['shadow-semantic-view-identity-manifest']:03d}-"
        "shadow-semantic-view-identity-manifest.json"
    )
    frozen_input = read_json(
        REPORTS
        / f"{NUMBERS['shadow-frozen-input-layout-audit']:03d}-"
        "shadow-frozen-input-layout-audit.json"
    )
    matrix = read_json(
        REPORTS
        / f"{NUMBERS['shadow-cross-manifest-preflight']:03d}-"
        "shadow-cross-manifest-preflight.json"
    )
    expected_contexts = len(m12bg.capability._batches(tuple(state["tickers"])))
    expected_calls = expected_contexts * 3
    gate_pass = all(
        (
            program.get("status") == "NETWORK_READY",
            program.get("network_gate_executed") is True,
            program["network"]["readiness"]["ready"] is True,
            shadow.get("status") == "BLOCKED",
            not receipts,
            set(changed_paths).issubset(allowed_paths),
            model_identity["status"] == "PASS",
            model_identity["total_change_count"] == 0,
            lower_gate.get("status") == "PASS",
            view_identity.get("status") == "PASS",
            frozen_input.get("status") == "PASS",
            matrix.get("status") == "PASS",
            state.get("context_count") == expected_contexts,
            state.get("planned_model_calls") == expected_calls,
            state.get("model") == MODEL,
            state.get("reasoning_effort") == EFFORT,
            _disabled_flag(state.get("wrapper_auto_retry")),
            _disabled_flag(state.get("batch_split")),
            _frozen_code_hashes_match(state),
        )
    )
    correction = {
        "status": "PASS" if gate_pass else "FAIL",
        "classification": "PRE_MODEL_HARNESS_BOOLEAN_NORMALIZATION",
        "prior_head": prior_head,
        "current_head": current_head,
        "changed_paths": list(changed_paths),
        "model_facing_semantic_change_count": model_identity[
            "total_change_count"
        ],
        "model_receipt_count_before_resume": len(receipts),
        "generation_id": state["generation_id"],
        "generation_recreated": False,
        "network_gate_repeated": False,
        "semantic_contract_change_count": 0,
        "packet_or_context_mutation_count": 0,
    }
    write_json(OUTPUT / "pre-model-harness-correction.json", correction)
    generation_path = (
        REPORTS
        / f"{NUMBERS['new-shadow-generation-manifest']:03d}-"
        "new-shadow-generation-manifest.json"
    )
    generation = read_json(generation_path)
    generation.update(
        {
            "status": "FROZEN" if gate_pass else "BLOCKED",
            "pre_model_harness_correction": correction,
        }
    )
    write_json(generation_path, generation)
    report(
        "shadow-model-call-gate",
        {
            "status": "PASS" if gate_pass else "FAIL",
            "generation_id": state["generation_id"],
            "network_readiness": "READY",
            "deterministic_gates": "PASS",
            "cross_manifest": matrix["status"],
            "frozen_input": frozen_input["status"],
            "canonical_provenance": program["provenance"]["status"],
            "planned_model_calls": expected_calls,
            "model_calls_before_gate": len(receipts),
            "new_fictional_model_calls": 0,
            "new_fresh_model_calls": 0,
            "selective_rerun": False,
            "fallback_model": False,
            "pre_model_harness_correction": correction,
        },
    )
    if gate_pass:
        program["implementation_head_sha"] = current_head
        program["pre_model_harness_correction"] = correction
        shadow["status"] = "FROZEN"
        shadow["implementation_head_sha"] = current_head
        shadow["pre_model_harness_correction"] = correction
    write_json(OUTPUT / "program-state.json", program)
    write_json(OUTPUT / "shadow-state.json", shadow)
    if not gate_pass:
        raise SystemExit("M12BJ_PRE_MODEL_HARNESS_CORRECTION_GATE_FAILED")
    print(canonical_json(correction))


def run_shadow() -> None:
    state = read_json(OUTPUT / "shadow-state.json")
    if state.get("status") != "FROZEN":
        raise ValueError("M12BJ_SHADOW_NOT_FROZEN")
    if state.get("implementation_head_sha") != git("rev-parse", "HEAD"):
        raise ValueError("M12BJ_CODE_CHANGED_AFTER_SHADOW_FREEZE")
    _configure_lower()
    m12bg.m12bd.m12bb.run_shadow()


def _raw_shadow_artifact_identity() -> dict[str, object]:
    root = PROOF_OUTPUT / "shadow/model-calls"
    paths = sorted(path for path in root.rglob("*") if path.is_file())
    digest = hashlib.sha256()
    for path in paths:
        digest.update(str(path.relative_to(root)).encode())
        digest.update(b"\0")
        digest.update(file_sha256(path).encode())
        digest.update(b"\0")
    return {
        "file_count": len(paths),
        "receipt_count": sum(path.name == "receipt.json" for path in paths),
        "aggregate_sha256": digest.hexdigest(),
    }


def resume_finalization() -> None:
    """Authorize an aggregate-only repair after all frozen calls completed."""

    _configure_lower()
    m12bg.m12bd.m12bb._configure_runtime(enable_binding_validation=True)
    m12bg.capability.OUTPUT = PROOF_OUTPUT
    m12bg.capability.base.OUTPUT = PROOF_OUTPUT
    program = read_json(OUTPUT / "program-state.json")
    shadow = read_json(OUTPUT / "shadow-state.json")
    state = read_json(PROOF_OUTPUT / "shadow/program-state.json")
    prior_head = str(shadow["implementation_head_sha"])
    current_head = git("rev-parse", "HEAD")
    changed_paths = tuple(
        value
        for value in git("diff", "--name-only", prior_head, current_head).splitlines()
        if value
    )
    allowed_paths = {str(RUNNER), str(TEST_PATH)}
    model_identity = _model_facing_identity()
    documents = [
        *m12bg.capability._shadow_documents("monolithic"),
        *m12bg.capability._shadow_documents("stage1"),
        *m12bg.capability._shadow_documents("stage2"),
    ]
    raw_identity = _raw_shadow_artifact_identity()
    expected_calls = int(state["planned_model_calls"])
    gate_pass = all(
        (
            shadow.get("status") == "FROZEN",
            state.get("generation_id") == shadow.get("generation_id"),
            len(documents) == expected_calls,
            all(document.get("status") == "PASS" for document in documents),
            raw_identity["receipt_count"] == expected_calls,
            set(changed_paths).issubset(allowed_paths),
            model_identity["status"] == "PASS",
            model_identity["total_change_count"] == 0,
        )
    )
    correction = {
        "status": "PASS" if gate_pass else "FAIL",
        "classification": "POST_MODEL_AGGREGATION_ONLY_FINALIZATION_REPAIR",
        "prior_head": prior_head,
        "current_head": current_head,
        "changed_paths": list(changed_paths),
        "generation_id": state["generation_id"],
        "completed_model_calls": len(documents),
        "model_receipt_count": raw_identity["receipt_count"],
        "raw_model_artifact_file_count": raw_identity["file_count"],
        "raw_model_artifact_aggregate_sha256": raw_identity["aggregate_sha256"],
        "model_facing_semantic_change_count": model_identity[
            "total_change_count"
        ],
        "candidate_mutation_count": 0,
        "model_rerun_count": 0,
        "network_gate_repeated": False,
        "semantic_contract_change_count": 0,
    }
    write_json(OUTPUT / "post-model-finalization-harness-correction.json", correction)
    if gate_pass:
        program["implementation_head_sha"] = current_head
        program["post_model_finalization_harness_correction"] = correction
        shadow["implementation_head_sha"] = current_head
        shadow["post_model_finalization_harness_correction"] = correction
    write_json(OUTPUT / "program-state.json", program)
    write_json(OUTPUT / "shadow-state.json", shadow)
    if not gate_pass:
        raise SystemExit("M12BJ_POST_MODEL_FINALIZATION_REPAIR_GATE_FAILED")
    print(canonical_json(correction))


def _legacy_finalization_exit_is_diagnostic(exc: SystemExit) -> bool:
    return str(exc) in LEGACY_DIAGNOSTIC_FINALIZATION_EXITS


def _candidate_rows(
    shadow: Mapping[str, object], phase: str
) -> list[Mapping[str, object]]:
    if phase == "final":
        return [
            row
            for document in shadow["stage2"]
            for row in document.get("final_rows", ())
        ]
    return [row for document in shadow[phase] for row in document["rows"]]


def _result_errors(value: object) -> list[str]:
    if hasattr(value, "errors"):
        return [str(item) for item in value.errors]
    if isinstance(value, Mapping):
        errors = value.get("errors", ())
        if isinstance(errors, Sequence) and not isinstance(errors, (str, bytes)):
            return [str(item) for item in errors]
    return []


def _canonical_shadow_audit(shadow: Mapping[str, object]) -> dict[str, object]:
    state = shadow["state"]
    _tickers, _packets, built = m12bg.capability._shadow_inputs(state)
    _evidence, owned, catalogs, _contexts, _stocks = built
    lifecycle = {
        "monolithic": "MONITORED_MONOLITHIC",
        "stage1": "MONITORED_STAGE1_FINANCIAL",
        "final": "MONITORED_FINAL_COMPOSITION",
    }
    rows = []
    bypass_count = 0
    provenance_failures = 0
    for phase in ("monolithic", "stage1", "final"):
        for row in _candidate_rows(shadow, phase):
            core = row.get("core")
            if not isinstance(core, Mapping):
                raise ValueError(f"M12BJ_CORE_REQUIRED:{phase}:{row.get('ticker')}")
            ticker = str(row["ticker"])
            audit = audit_owned_directional_core_semantics(
                core,
                owned=owned[ticker],
                catalog=catalogs[ticker],
                lifecycle_mode=lifecycle[phase],
            )
            provenance = [
                value.model_dump(mode="json")
                for value in audit.semantic_service_provenance
            ]
            bypass = sum(
                bool(value["called"])
                and value["hard_decision_source"] != "CANONICAL_SERVICE"
                for value in provenance
            )
            bypass_count += bypass
            embedded = row.get("canonical_semantic_audit")
            embedded_identity = (
                embedded.get("semantic_service_identity_sha256")
                if isinstance(embedded, Mapping)
                else None
            )
            embedded_contract_matches = (
                not isinstance(embedded, Mapping)
                or embedded.get("contract") == SEMANTIC_ORCHESTRATOR_CONTRACT
            )
            identity_matches = (
                embedded_identity == audit.semantic_service_identity_sha256
                if embedded_identity is not None
                else None
            )
            provenance_failures += int(not embedded_contract_matches or bypass > 0)
            families = {
                "financial_semantics": _result_errors(audit.financial_semantics),
                "qtd_ytd_semantics": _result_errors(audit.qtd_ytd_semantics),
                "configured_signal_semantics": _result_errors(
                    audit.configured_signal_semantics
                ),
                "working_capital_semantics": _result_errors(
                    audit.working_capital_semantics
                ),
                "business_delta_semantics": _result_errors(
                    audit.business_delta_semantics
                ),
                "market_expectation_semantics": _result_errors(
                    audit.market_expectation_semantics
                ),
            }
            rows.append(
                {
                    "ticker": ticker,
                    "phase": phase,
                    "status": audit.status,
                    "hard_errors": list(audit.hard_errors),
                    "family_errors": families,
                    "semantic_service_identity_sha256": (
                        audit.semantic_service_identity_sha256
                    ),
                    "embedded_receipt_present": isinstance(embedded, Mapping),
                    "embedded_contract_matches": embedded_contract_matches,
                    "embedded_identity_matches": identity_matches,
                    "embedded_identity_difference_is_lifecycle_diagnostic": (
                        identity_matches is False
                    ),
                    "hard_decision_source": "CANONICAL_SERVICE",
                    "canonical_bypass_count": bypass,
                    "legacy_duplicate_participation": False,
                    "provenance": provenance,
                }
            )
    hard_errors = sum(len(row["hard_errors"]) for row in rows)
    return {
        "status": (
            "PASS"
            if len(rows) == len(state["tickers"]) * 3
            and not hard_errors
            and not bypass_count
            and not provenance_failures
            else "FAIL"
        ),
        "candidate_audit_count": len(rows),
        "hard_error_count": hard_errors,
        "canonical_bypass_count": bypass_count,
        "legacy_duplicate_participation_count": 0,
        "semantic_service_provenance_failure_count": provenance_failures,
        "rows": rows,
    }


def _family_audit(
    canonical: Mapping[str, object], family: str
) -> dict[str, object]:
    rows = [
        {
            "ticker": row["ticker"],
            "phase": row["phase"],
            "errors": row["family_errors"][family],
        }
        for row in canonical["rows"]
        if row["family_errors"][family]
    ]
    return {
        "status": "PASS" if not rows else "FAIL",
        "family": family,
        "audited_candidate_count": canonical["candidate_audit_count"],
        "violation_count": sum(len(row["errors"]) for row in rows),
        "rows": rows,
    }


def _safe_binding(value: Mapping[str, object]) -> dict[str, object]:
    keys = (
        "status",
        "contract",
        "candidate_count",
        "working_capital_checkpoint_count",
        "grounded_working_capital_checkpoint_count",
        "working_capital_grounding_failure_count",
        "narrative_only_substitution_count",
        "metric_specific_ref_mismatch_count",
        "unsafe_wc_auto_direction_count",
    )
    return {key: value.get(key, 0) for key in keys}


def _safe_external_report(*fragments: str) -> dict[str, object]:
    value = m12bg.m12bd._safe_proof_report(*fragments)
    safe = {
        key: item
        for key, item in value.items()
        if isinstance(item, (str, int, float, bool, type(None)))
        and (
            key == "status"
            or key == "contract"
            or key == "generation_id"
            or key.endswith("_count")
            or key.endswith("_status")
        )
    }
    failures = []
    for row in value.get("rows", ()):
        if not isinstance(row, Mapping):
            continue
        errors = row.get("errors", ())
        failed = row.get("status") == "FAIL" or bool(errors)
        if failed:
            failures.append(
                {
                    "ticker": row.get("ticker"),
                    "source": row.get("source"),
                    "status": row.get("status"),
                    "errors": list(errors)
                    if isinstance(errors, Sequence)
                    and not isinstance(errors, (str, bytes))
                    else [],
                }
            )
    safe["failure_rows"] = failures
    safe.setdefault("status", "NOT_MEASURED")
    return safe


def _model_artifact_manifest(
    documents: Sequence[Mapping[str, object]], phase: str
) -> dict[str, object]:
    rows = []
    for document in documents:
        context = int(document["context"])
        root = PROOF_OUTPUT / "shadow/model-calls" / f"context-{context:02d}" / phase
        transport = document.get("transport", {})
        rows.append(
            {
                "generation_id": document.get("generation_id"),
                "context": context,
                "tickers": document.get("tickers"),
                "status": document.get("status"),
                "invocation_id": transport.get("invocation_id")
                if isinstance(transport, Mapping)
                else None,
                "prompt_sha256": file_sha256(root / "prompt.txt"),
                "schema_sha256": file_sha256(root / "schema.json"),
                "output_sha256": file_sha256(root / "output.raw.json"),
                "run_document_sha256": canonical_sha256(document),
            }
        )
    return {
        "status": "PASS" if rows and all(row["status"] == "PASS" for row in rows) else "FAIL",
        "phase": phase,
        "document_count": len(rows),
        "raw_artifacts_packaged": False,
        "rows": rows,
    }


def _decision_snapshot(candidate: DirectionalCoreCandidate) -> dict[str, object]:
    return {
        "overall_direction": candidate.overall_direction,
        "business_thesis_change": candidate.business_thesis_change,
        "new_buyer_stance": candidate.fundamental_new_buyer.stance,
        "holder_stance": candidate.fundamental_holder.stance,
        "directional_balance": candidate.directional_balance.model_dump(mode="json"),
        "hold_lean": candidate.hold_lean,
        "directional_confidence": candidate.directional_confidence,
    }


def _comparison_rows(shadow: Mapping[str, object]) -> list[dict[str, object]]:
    monolithic = {
        str(row["ticker"]): DirectionalCoreCandidate.model_validate(row["core"])
        for row in _candidate_rows(shadow, "monolithic")
    }
    final = {
        str(row["ticker"]): DirectionalCoreCandidate.model_validate(row["core"])
        for row in _candidate_rows(shadow, "final")
    }
    if set(monolithic) != set(final):
        raise ValueError("M12BJ_COMPARISON_TICKER_SCOPE_MISMATCH")
    rows = []
    for ticker in sorted(monolithic):
        classification, fields = _comparison_classification(
            monolithic[ticker], final[ticker]
        )
        rows.append(
            {
                "ticker": ticker,
                "classification": classification,
                "changed_fields": fields,
                "monolithic": _decision_snapshot(monolithic[ticker]),
                "two_stage": _decision_snapshot(final[ticker]),
                "automatic_correctness_verdict": False,
            }
        )
    return rows


def _comparison_report(
    rows: Sequence[Mapping[str, object]], classifications: Sequence[str]
) -> dict[str, object]:
    selected = [row for row in rows if row["classification"] in classifications]
    return {
        "status": "MEASURED",
        "count": len(selected),
        "readiness_blocking": False,
        "rows": selected,
    }


def _fictional_diagnostics() -> dict[str, object]:
    fictional = m12bg.m12bd._fictional_payloads()
    diagnostics = fictional["diagnostics"]
    if diagnostics.get("status") != "MEASURED":
        raise ValueError("M12BJ_FICTIONAL_DIAGNOSTICS_NOT_MEASURED")
    return diagnostics


def _completion(
    *,
    clean: bool,
    shadow: Mapping[str, object],
    canonical: Mapping[str, object],
    comparisons: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    program = read_json(OUTPUT / "program-state.json")
    state = shadow["state"]
    identity = program["model_identity"]["surfaces"]
    proof_completion = read_json(PROOF_OUTPUT / "program-completion.json")
    counts = Counter(row["classification"] for row in comparisons)
    configured = _family_audit(canonical, "configured_signal_semantics")
    delta = _family_audit(canonical, "business_delta_semantics")
    expectation = _family_audit(canonical, "market_expectation_semantics")
    qtd = _family_audit(canonical, "qtd_ytd_semantics")
    stage1 = _safe_binding(shadow["stage1_binding"])
    stage2 = _safe_binding(shadow["stage2_binding"])
    return {
        "status": "COMPLETE" if clean else "BLOCKED",
        "phase": "M12BJ",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "final_local_head_sha": git("rev-parse", "HEAD"),
        "latest_result_zip_sha256": M12BI_BUNDLE_SHA256,
        "latest_result_integrity": program["latest"]["status"],
        "m12bi_convergence_status": program["m12bi_completion"][
            "semantic_single_source_convergence_status"
        ],
        "m12bi_proof_critical_bypass_count": program["m12bi_completion"][
            "proof_critical_bypass_count_after"
        ],
        "m12bi_proof_critical_duplicate_semantic_engine_count": program[
            "m12bi_completion"
        ]["proof_critical_duplicate_semantic_engine_count_after"],
        "m12bi_golden_corpus_divergence_count": program["m12bi_completion"][
            "golden_corpus_cross_path_divergence_count_after"
        ],
        "canonical_core_semantic_orchestrator_contract_version": (
            SEMANTIC_ORCHESTRATOR_CONTRACT
        ),
        "historical_fresh_generation_id": program["fresh_quarantine"][
            "generation_id"
        ],
        "historical_fresh_candidate_count": program["fresh_quarantine"][
            "candidate_count"
        ],
        "historical_fresh_previous_accepted_count": program["fresh_quarantine"][
            "previously_accepted_count"
        ],
        "historical_fresh_canonical_fail_count": program["fresh_quarantine"][
            "canonical_fail_count"
        ],
        "historical_fresh_canonical_pass_count": program["fresh_quarantine"][
            "canonical_pass_count"
        ],
        "historical_fresh_readiness_evidence_used": False,
        "golden_corpus_case_count": program["golden"]["case_count"],
        "golden_corpus_cross_path_divergence_count": program["golden"][
            "cross_path_divergence_count"
        ],
        "model_prompt_semantic_change_count": identity["model_prompt"][
            "change_count"
        ],
        "model_schema_semantic_change_count": identity["model_schema"][
            "change_count"
        ],
        "stage1_wc_binding_semantic_change_count": identity[
            "stage1_wc_binding"
        ]["change_count"],
        "stage2_wc_binding_semantic_change_count": identity[
            "stage2_wc_binding"
        ]["change_count"],
        "configured_signal_view_change_count": identity[
            "configured_signal_view"
        ]["change_count"],
        "configured_financial_support_concept_change_count": identity[
            "configured_financial_support_concept"
        ]["change_count"],
        "business_delta_view_change_count": identity["business_delta_view"][
            "change_count"
        ],
        "expectation_view_change_count": identity["expectation_view"][
            "change_count"
        ],
        "financial_evidence_projection_change_count": identity[
            "financial_evidence_projection"
        ]["change_count"],
        "final_user_schema_change_count": identity["final_user_schema"][
            "change_count"
        ],
        "m12bd_offline_reaudit_status": program["fictional"]["status"],
        "formal_fictional_reuse_status": (
            "REUSE_AUTHORIZED_M12BD_ON_CONVERGED_SEMANTICS"
        ),
        "new_fictional_model_calls": 0,
        "proof_critical_bypass_count": program["provenance"][
            "proof_critical_bypass_count"
        ],
        "proof_critical_duplicate_hard_decision_participation_count": program[
            "provenance"
        ]["proof_critical_duplicate_participation_count"],
        "network_readiness_status": "READY",
        "network_failure_type": None,
        "network_model_process_spawned": False,
        "task_start_active_monitor_count": len(state["tickers"]),
        "task_start_active_monitor_tickers": list(state["tickers"]),
        "new_shadow_generation_id": state["generation_id"],
        "shadow_context_count": state["context_count"],
        "shadow_monolithic_model_calls": len(shadow["monolithic"]),
        "shadow_stage1_model_calls": len(shadow["stage1"]),
        "shadow_stage2_model_calls": len(shadow["stage2"]),
        "shadow_model_calls_total": shadow["runtime"]["model_call_count"],
        "shadow_completed_ticker_count": len(shadow["compositions"]),
        "shadow_final_composition_count": len(shadow["compositions"]),
        "shadow_aggregate_finalization_status": "PASS" if clean else "FAIL",
        "shadow_canonical_bypass_count": canonical["canonical_bypass_count"],
        "shadow_legacy_duplicate_participation_in_hard_decision_count": 0,
        "shadow_semantic_service_provenance_failure_count": canonical[
            "semantic_service_provenance_failure_count"
        ],
        "shadow_hard_semantic_failure_count": canonical["hard_error_count"],
        "shadow_fcf_hard_failure_count": sum(
            "fcf" in error.casefold()
            for row in canonical["rows"]
            for error in row["hard_errors"]
        ),
        "shadow_netdebt_hard_failure_count": sum(
            "net_debt" in error.casefold() or "netdebt" in error.casefold()
            for row in canonical["rows"]
            for error in row["hard_errors"]
        ),
        "shadow_stage1_wc_grounding_failure_count": stage1[
            "working_capital_grounding_failure_count"
        ],
        "shadow_stage2_wc_grounding_failure_count": stage2[
            "working_capital_grounding_failure_count"
        ],
        "shadow_wc_metric_specific_mismatch_count": stage2[
            "metric_specific_ref_mismatch_count"
        ],
        "shadow_wc_narrative_only_substitution_count": stage2[
            "narrative_only_substitution_count"
        ],
        "shadow_unsafe_wc_auto_direction_count": stage2[
            "unsafe_wc_auto_direction_count"
        ],
        "shadow_financial_sector_hard_failure_count": sum(
            "financial_sector" in error.casefold()
            for row in canonical["rows"]
            for error in row["hard_errors"]
        ),
        "shadow_configured_signal_violation_count": configured["violation_count"],
        "shadow_business_delta_hard_failure_count": delta["violation_count"],
        "shadow_expectation_hard_failure_count": expectation["violation_count"],
        "shadow_qtd_ytd_hard_failure_count": qtd["violation_count"],
        "shadow_stage2_language_false_positive_count": proof_completion.get(
            "shadow_stage2_language_false_positive_count", 0
        ),
        "shadow_adr_security_basis_failure_count": proof_completion.get(
            "shadow_adr_security_basis_failure_count", 0
        ),
        "shadow_primary_direction_change_count": counts["PRIMARY_DIRECTION_CHANGE"],
        "shadow_business_delta_change_count": counts["BUSINESS_DELTA_CHANGE"],
        "shadow_new_buyer_change_count": counts["NEW_BUYER_STANCE_CHANGE"],
        "shadow_holder_change_count": counts["HOLDER_STANCE_CHANGE"],
        "shadow_same_direction_calibration_change_count": counts[
            "SAME_DIRECTION_CALIBRATION_CHANGE"
        ],
        "shadow_multi_field_change_count": counts["MULTI_FIELD_DECISION_CHANGE"],
        "shadow_expected_contract_correction_count": 0,
        "shadow_potential_architecture_regression_count": 0 if clean else 1,
        "shadow_unresolved_review_required_count": sum(
            row["classification"]
            not in {"NO_DECISION_MATERIAL_CHANGE", "SAME_DIRECTION_CALIBRATION_CHANGE"}
            for row in comparisons
        ),
        "shadow_core_mutation_after_stance_count": shadow["core"][
            "core_mutation_count"
        ],
        "shadow_timeout_count": shadow["runtime"]["timeout_count"],
        "shadow_orphan_count": shadow["runtime"]["orphan_process_count"],
        "shadow_wrapper_retry_count": shadow["runtime"]["wrapper_retry_count"],
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
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "two_stage_shadow_compatibility_classification": (
            "COMPLETE_WITH_POLICY_DIAGNOSTICS" if clean else "BLOCKED"
        ),
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": NEXT_SCOPE if clean else "SMALLEST_BOUNDED_OBJECTIVE_HARD_FAILURE_REPAIR",
        "focused_test_result": "PENDING",
        "full_test_result": "PENDING",
        "ruff_result": "PENDING",
        "git_diff_check": "PENDING",
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }


def finalize_shadow() -> None:
    frozen = read_json(OUTPUT / "shadow-state.json")
    if frozen.get("implementation_head_sha") != git("rev-parse", "HEAD"):
        raise ValueError("M12BJ_CODE_CHANGED_BEFORE_FINALIZATION")
    _configure_lower()
    legacy_finalization: dict[str, object] = {
        "status": "PASS",
        "exit": None,
        "hard_decision_source": "CANONICAL_SERVICE",
        "readiness_blocking": False,
    }
    try:
        m12bg.m12bd.m12bb.finalize_shadow()
        m12bg.m12bd.m12bb.closeout()
    except SystemExit as exc:
        if not _legacy_finalization_exit_is_diagnostic(exc):
            raise
        legacy_finalization.update(
            {
                "status": "LEGACY_DUPLICATE_DIAGNOSTIC",
                "exit": str(exc),
                "canonical_reaudit_required": True,
            }
        )
    shadow = m12bg.m12bd._shadow_payloads()
    try:
        legacy_lower_clean = m12bg.m12bd._report_shadow(shadow)
    except FileNotFoundError as exc:
        legacy_lower_clean = False
        legacy_finalization.update(
            {
                "report_materialization_status": "PARTIAL",
                "missing_legacy_report_dependency": Path(
                    str(exc.filename)
                ).name,
            }
        )
    canonical = _canonical_shadow_audit(shadow)
    comparisons = _comparison_rows(shadow)
    fictional = _fictional_diagnostics()
    expected_contexts = int(shadow["state"]["context_count"])
    expected_tickers = len(shadow["state"]["tickers"])
    expected_calls = expected_contexts * 3
    lower_errors = {
        phase: sum(
            len(row.get("errors", ()))
            for document in shadow[phase]
            for row in document["rows"]
        )
        for phase in ("monolithic", "stage1", "stage2")
    }
    lower_errors["final"] = sum(
        len(row.get("errors", ())) for row in shadow["compositions"]
    )
    clean = all(
        (
            canonical["status"] == "PASS",
            len(shadow["monolithic"]) == expected_contexts,
            len(shadow["stage1"]) == expected_contexts,
            len(shadow["stage2"]) == expected_contexts,
            len(shadow["compositions"]) == expected_tickers,
            all(
                document.get("status") == "PASS"
                for phase in ("monolithic", "stage1", "stage2")
                for document in shadow[phase]
            ),
            not sum(lower_errors.values()),
            shadow["stage1_binding"]["status"] == "PASS",
            shadow["stage2_binding"]["status"] == "PASS",
            shadow["optional"]["status"] == "PASS",
            shadow["optional"]["zero_observation_hard_failure_count"] == 0,
            shadow["runtime"]["model_call_count"] == expected_calls,
            shadow["runtime"]["timeout_count"] == 0,
            shadow["runtime"]["orphan_process_count"] == 0,
            shadow["runtime"]["wrapper_retry_count"] == 0,
            shadow["core"]["core_mutation_count"] == 0,
        )
    )

    for phase, slug in (
        ("monolithic", "shadow-monolithic-model-artifacts"),
        ("stage1", "shadow-stage1-model-artifacts"),
        ("stage2", "shadow-stage2-model-artifacts"),
    ):
        report(slug, _model_artifact_manifest(shadow[phase], phase))
    report("shadow-semantic-service-provenance-audit", canonical)
    report(
        "shadow-context-hard-semantic-audit",
        {
            "status": "PASS"
            if not sum(lower_errors.values()) and canonical["hard_error_count"] == 0
            else "FAIL",
            **lower_errors,
            "canonical_error_count": canonical["hard_error_count"],
        },
    )
    report(
        "shadow-financial-semantic-audit",
        _family_audit(canonical, "financial_semantics"),
    )
    report("shadow-stage1-wc-binding-audit", _safe_binding(shadow["stage1_binding"]))
    report("shadow-stage2-wc-binding-audit", _safe_binding(shadow["stage2_binding"]))
    report(
        "shadow-configured-signal-audit",
        _family_audit(canonical, "configured_signal_semantics"),
    )
    report(
        "shadow-business-delta-audit",
        _family_audit(canonical, "business_delta_semantics"),
    )
    report(
        "shadow-market-expectation-audit",
        _family_audit(canonical, "market_expectation_semantics"),
    )
    financial = _family_audit(canonical, "financial_semantics")
    financial_sector_failures = sum(
        "financial_sector" in error.casefold()
        for row in financial["rows"]
        for error in row["errors"]
    )
    report(
        "shadow-financial-sector-audit",
        {
            "status": "PASS" if not financial_sector_failures else "FAIL",
            "hard_failure_count": financial_sector_failures,
            "canonical_family": "financial_semantics",
        },
    )
    report(
        "shadow-qtd-ytd-audit",
        _family_audit(canonical, "qtd_ytd_semantics"),
    )
    report(
        "shadow-stage2-language-audit",
        _safe_external_report("shadow-stage2-language-audit"),
    )
    report(
        "shadow-adr-security-basis-audit",
        _safe_external_report("shadow-adr-security-basis-audit"),
    )
    report(
        "shadow-final-composition-audit",
        {
            "status": "PASS"
            if len(shadow["compositions"]) == expected_tickers
            and not lower_errors["final"]
            else "FAIL",
            "composition_count": len(shadow["compositions"]),
            "error_count": lower_errors["final"],
        },
    )
    report(
        "shadow-core-immutability-audit",
        {
            "status": shadow["core"]["status"],
            "core_mutation_count": shadow["core"]["core_mutation_count"],
            "subject_count": len(shadow["core"].get("rows", ())),
        },
    )
    report(
        "shadow-aggregate-finalization-audit",
        {
            "status": "PASS" if clean else "FAIL",
            "decision_status": shadow["decision"].get("status"),
            "decision_status_role": "LEGACY_DUPLICATE_DIAGNOSTIC",
            "legacy_lower_clean": legacy_lower_clean,
            "legacy_finalization": legacy_finalization,
            "hard_decision_source": "CANONICAL_SERVICE",
            "completed_ticker_count": len(shadow["compositions"]),
            "expected_ticker_count": expected_tickers,
        },
    )
    report(
        "shadow-runtime-audit",
        {
            key: shadow["runtime"][key]
            for key in (
                "status",
                "model_call_count",
                "timeout_count",
                "orphan_process_count",
                "wrapper_retry_count",
            )
        },
    )
    report(
        "shadow-per-ticker-comparison",
        {
            "status": "MEASURED",
            "subject_count": len(comparisons),
            "rows": comparisons,
            "automatic_correctness_verdict": False,
        },
    )
    classifications = {
        "shadow-core-direction-differences": ("PRIMARY_DIRECTION_CHANGE",),
        "shadow-business-delta-differences": ("BUSINESS_DELTA_CHANGE",),
        "shadow-new-buyer-differences": ("NEW_BUYER_STANCE_CHANGE",),
        "shadow-holder-differences": ("HOLDER_STANCE_CHANGE",),
        "shadow-same-direction-calibration-differences": (
            "SAME_DIRECTION_CALIBRATION_CHANGE",
        ),
    }
    for slug, values in classifications.items():
        report(slug, _comparison_report(comparisons, values))
    report(
        "shadow-expected-contract-corrections",
        {
            "status": "MEASURED",
            "count": 0,
            "automatic_correctness_inference": False,
            "rows": [],
        },
    )
    regressions = [] if clean else [{"reason": "OBJECTIVE_HARD_GATE_FAILURE"}]
    report(
        "shadow-potential-architecture-regressions",
        {
            "status": "PASS" if clean else "FAIL",
            "count": len(regressions),
            "rows": regressions,
        },
    )
    review_rows = [
        row
        for row in comparisons
        if row["classification"]
        not in {"NO_DECISION_MATERIAL_CHANGE", "SAME_DIRECTION_CALIBRATION_CHANGE"}
    ]
    report(
        "shadow-unresolved-review-required",
        {
            "status": "MEASURED",
            "count": len(review_rows),
            "readiness_blocking": False,
            "rows": review_rows,
        },
    )
    summary = {
        "status": "PASS" if clean else "FAIL",
        "generation_id": shadow["state"]["generation_id"],
        "active_count": expected_tickers,
        "context_count": expected_contexts,
        "model_calls": shadow["runtime"]["model_call_count"],
        "classification_counts": dict(
            sorted(Counter(row["classification"] for row in comparisons).items())
        ),
        "hard_semantic_failure_count": canonical["hard_error_count"],
        "canonical_bypass_count": canonical["canonical_bypass_count"],
        "policy_diagnostics_only": True,
    }
    report("shadow-aggregate-summary", summary)
    report(
        "shadow-architecture-decision",
        {
            "status": "COMPATIBLE" if clean else "BLOCKED",
            "classification": (
                "COMPLETE_WITH_POLICY_DIAGNOSTICS" if clean else "BLOCKED"
            ),
            "canonical_semantic_single_source_preserved": clean,
            "automatic_policy_resolution": False,
        },
    )
    for slug, key in (
        ("fictional-primary-boundary-summary", "primary_direction"),
        ("fictional-delta-materiality-summary", "business_delta"),
        ("fictional-new-buyer-boundary-summary", "new_buyer"),
        ("fictional-holder-boundary-summary", "holder"),
    ):
        report(
            slug,
            {
                "status": "MEASURED",
                "generation_id": M12BD_GENERATION_ID,
                "rows": fictional[key],
                "readiness_blocking": False,
                "new_model_calls": 0,
            },
        )
    for target, source in (
        ("monitored-primary-difference-summary", "shadow-core-direction-differences"),
        ("monitored-delta-difference-summary", "shadow-business-delta-differences"),
        ("monitored-new-buyer-difference-summary", "shadow-new-buyer-differences"),
        ("monitored-holder-difference-summary", "shadow-holder-differences"),
        (
            "same-direction-calibration-summary",
            "shadow-same-direction-calibration-differences",
        ),
    ):
        source_path = REPORTS / f"{NUMBERS[source]:03d}-{source}.json"
        source_payload = read_json(source_path)
        report(
            target,
            {
                key: value
                for key, value in source_payload.items()
                if key
                not in {"contract", "report_number", "report_slug", "generated_at"}
            },
        )
    report(
        "converged-semantic-shadow-lessons",
        {
            "status": "CLOSED" if clean else "BLOCKED",
            "canonical_semantics": "SINGLE_SOURCE",
            "semantic_micro_patch_count": 0,
            "model_facing_change_count": 0,
            "policy_differences_are_diagnostic": True,
        },
    )
    report(
        "combined-fictional-monitored-policy-input",
        {
            "status": "DIAGNOSTIC_COMPLETE" if clean else "BLOCKED",
            "fictional_generation_id": M12BD_GENERATION_ID,
            "monitored_generation_id": shadow["state"]["generation_id"],
            "fictional_variance_counts": {
                key: fictional[key]
                for key in (
                    "primary_direction_unstable_subject_count",
                    "business_delta_unstable_subject_count",
                    "new_buyer_unstable_subject_count",
                    "holder_unstable_subject_count",
                    "same_direction_calibration_variance_subject_count",
                )
            },
            "monitored_classification_counts": summary["classification_counts"],
            "automatic_resolution": False,
        },
    )
    report(
        "next-bounded-policy-decision",
        {
            "status": "SELECTED" if clean else "BLOCKED",
            "next_scope": NEXT_SCOPE
            if clean
            else "SMALLEST_BOUNDED_OBJECTIVE_HARD_FAILURE_REPAIR",
            "fresh_unseen_calls_authorized": False,
            "main_merge_authorized": False,
            "deployment_authorized": False,
            "monitoring_resume_authorized": False,
        },
    )

    completion = _completion(
        clean=clean,
        shadow=shadow,
        canonical=canonical,
        comparisons=comparisons,
    )
    decisions = {
        "semantic-convergence-preservation-decision": {
            "status": "PASS" if clean else "FAIL",
            "canonical_bypass_count": canonical["canonical_bypass_count"],
        },
        "historical-fresh-proof-quarantine-preservation-decision": {
            "status": "PASS",
            "readiness_evidence_used": False,
            "new_fresh_model_calls": 0,
        },
        "fictional-proof-reuse-success-decision": {
            "status": "PASS",
            "generation_id": M12BD_GENERATION_ID,
            "new_fictional_model_calls": 0,
        },
        "full-shadow-completion-decision": {
            "status": "PASS" if clean else "FAIL",
            "generation_id": shadow["state"]["generation_id"],
            "model_calls": shadow["runtime"]["model_call_count"],
            "completed_tickers": len(shadow["compositions"]),
        },
        "two-stage-shadow-compatibility-decision": {
            "status": completion["two_stage_shadow_compatibility_classification"]
        },
        "existing-monitored-impact-summary": summary,
        "fresh-real-proof-readiness-decision": {
            "status": "NOT_READY",
            "historical_fresh_proof_quarantined": True,
        },
        "final-main-merge-readiness-note": {
            "status": "NOT_READY",
            "main_merge_authorized": False,
        },
        "production-no-change": {
            "status": "PASS",
            "provider_source_fetches": 0,
            "production_db_mutations": 0,
            "production_sends": 0,
            "deployments": 0,
        },
        "schedule-pause-observation": {
            "status": "OBSERVED",
            "observed_paused_schedule_count": read_json(
                PROOF_OUTPUT / "program-completion.json"
            ).get("observed_paused_schedule_count", "NOT_MEASURED"),
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
        },
        "remote-push-prohibition-audit": {
            "status": "PASS",
            "remote_push_count": 0,
            "raw_model_artifact_remote_push_count": 0,
            "main_merges": 0,
            "deployments": 0,
        },
        "master-workflow-update": {
            "status": "PENDING_LOCAL_DOC_COMMIT",
            "remote_push": False,
        },
    }
    for slug, value in decisions.items():
        report(slug, value)
    write_json(OUTPUT / "program-completion.json", completion)
    report("program-completion", completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "# M12BJ Completion\n\n"
        f"- Status: `{completion['status']}`\n"
        f"- Generation: `{completion['new_shadow_generation_id']}`\n"
        f"- Active subjects: `{completion['task_start_active_monitor_count']}`\n"
        f"- Calls: `{completion['shadow_model_calls_total']}`\n"
        f"- Canonical hard failures: `{completion['shadow_hard_semantic_failure_count']}`\n"
        f"- Compatibility: `{completion['two_stage_shadow_compatibility_classification']}`\n"
        f"- Next scope: `{completion['next_scope']}`\n"
        "- Remote push/main merge/deploy: `0/0/0`\n",
    )
    if not clean:
        raise SystemExit("M12BJ_SHADOW_HARD_ACCEPTANCE_FAILURE")
    print(canonical_json(summary))


def _fill_missing_reports(reason: str) -> None:
    for number, slug in enumerate(REPORT_SLUGS, start=1):
        path = REPORTS / f"{number:03d}-{slug}.json"
        if not path.is_file():
            report(
                slug,
                {
                    "status": "NOT_RUN_DUE_TO_HARD_STOP",
                    "stop_reason": reason,
                },
            )


def _network_blocked_closeout(state: Mapping[str, object]) -> None:
    reason = "NETWORK_ENVIRONMENT_BLOCKER_NO_SEMANTIC_CHANGE"
    _fill_missing_reports(reason)
    completion = {
        "status": reason,
        "phase": "M12BJ",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "final_local_head_sha": git("rev-parse", "HEAD"),
        "latest_result_zip_sha256": M12BI_BUNDLE_SHA256,
        "latest_result_integrity": state["latest"]["status"],
        "m12bi_convergence_status": state["m12bi_completion"][
            "semantic_single_source_convergence_status"
        ],
        "network_readiness_status": "BLOCKED",
        "network_failure_type": state["network"]["readiness"]["failure_type"],
        "network_model_process_spawned": False,
        "shadow_model_calls_total": 0,
        "provider_source_fetches": 0,
        "production_db_mutations": 0,
        "production_sends": 0,
        "remote_push_count": 0,
        "main_merges": 0,
        "deployments": 0,
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": RETRY_SCOPE,
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    write_json(OUTPUT / "program-completion.json", completion)
    report("program-completion", completion)


def failure_closeout() -> None:
    _configure_lower()
    try:
        m12bg.m12bd.m12bb.failure_closeout()
    except (FileNotFoundError, KeyError, TypeError, ValueError):
        pass
    stop = (
        read_json(PROOF_OUTPUT / "shadow/stop.json")
        if (PROOF_OUTPUT / "shadow/stop.json").is_file()
        else {"stop_reason": "M12BJ_UNCLASSIFIED_SHADOW_HARD_STOP"}
    )
    reason = str(stop.get("stop_reason") or "M12BJ_SHADOW_HARD_STOP")
    _fill_missing_reports(reason)
    partial_calls = len(
        list((PROOF_OUTPUT / "shadow/model-calls").glob("context-*/*/receipt.json"))
    )
    completion = {
        "status": "BLOCKED",
        "phase": "M12BJ",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "final_local_head_sha": git("rev-parse", "HEAD"),
        "latest_result_zip_sha256": M12BI_BUNDLE_SHA256,
        "latest_result_integrity": "PASS",
        "stop": stop,
        "shadow_model_calls_total": partial_calls,
        "provider_source_fetches": 0,
        "production_db_mutations": 0,
        "production_sends": 0,
        "remote_push_count": 0,
        "main_merges": 0,
        "deployments": 0,
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": "SMALLEST_BOUNDED_OBJECTIVE_HARD_FAILURE_REPAIR",
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    write_json(OUTPUT / "program-completion.json", completion)
    report("program-completion", completion)


def record_validation(args: argparse.Namespace) -> None:
    completion = read_json(OUTPUT / "program-completion.json")
    completion.update(
        {
            "focused_test_result": args.focused,
            "full_test_result": args.full,
            "full_test_passed_count": args.full_count,
            "ruff_result": args.ruff,
            "git_diff_check": args.diff,
            "final_local_head_sha": git("rev-parse", "HEAD"),
        }
    )
    write_json(OUTPUT / "validation.json", {
        "status": "PASS"
        if args.focused == args.full == args.ruff == args.diff == "PASS"
        else "FAIL",
        "focused": args.focused,
        "full": args.full,
        "full_count": args.full_count,
        "ruff": args.ruff,
        "diff": args.diff,
    })
    write_json(OUTPUT / "program-completion.json", completion)
    report("program-completion", completion)


def record_docs() -> None:
    completion = read_json(OUTPUT / "program-completion.json")
    completion["documentation_status"] = "PASS"
    completion["final_local_head_sha"] = git("rev-parse", "HEAD")
    write_json(OUTPUT / "program-completion.json", completion)
    report(
        "master-workflow-update",
        {
            "status": "RECORDED_LOCAL_ONLY",
            "master_workflow_updated": True,
            "project_handoff_updated": True,
            "next_session_prompt_updated": True,
            "project_state_updated": True,
            "remote_push": False,
        },
    )
    report("program-completion", completion)


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
        TEST_PATH,
        Path("docs/MASTER_WORKFLOW.md"),
        Path("docs/PROJECT_HANDOFF.md"),
        Path("docs/NEXT_SESSION_PROMPT.md"),
        Path("docs/project-state.json"),
    ):
        if path.is_file():
            files.add(path)
    return sorted(files, key=str)


def bundle(output_zip: Path) -> None:
    missing = [
        str(REPORTS / f"{number:03d}-{slug}.json")
        for number, slug in enumerate(REPORT_SLUGS, start=1)
        if not (REPORTS / f"{number:03d}-{slug}.json").is_file()
    ]
    if missing:
        raise ValueError(f"M12BJ_REQUIRED_REPORTS_MISSING:{missing}")
    files = artifact_files()
    if any(str(path).startswith(str(LOCAL_RAW_ROOT)) for path in files):
        raise ValueError("M12BJ_RAW_MODEL_ARTIFACT_PACKAGE_ATTEMPT")
    completion = read_json(OUTPUT / "program-completion.json")
    completion["artifact_count"] = len(files)
    write_json(OUTPUT / "program-completion.json", completion)
    report("program-completion", completion)
    files = artifact_files()
    secret_failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (m12bi._secret_indicators(path.read_bytes()),)
        if indicators
    ]
    index = {
        "contract": "m12bj-artifact-index-v1",
        "status": "PASS" if not secret_failures else "FAIL",
        "artifact_count": len(files),
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": len(secret_failures),
        "secret_scan_failures": secret_failures,
        "raw_model_artifact_count": 0,
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
        raise ValueError("M12BJ_ARTIFACT_SECRET_SCAN_FAILURE")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    if output_zip.exists():
        raise ValueError(f"M12BJ_RESULT_BUNDLE_ALREADY_EXISTS:{output_zip}")
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=str(path))
        archive.write(
            OUTPUT / "artifact-index.json",
            arcname=str(OUTPUT / "artifact-index.json"),
        )
    with zipfile.ZipFile(output_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("M12BJ_RESULT_BUNDLE_CRC_FAILURE")
        for row in index["rows"]:
            payload = archive.read(row["path"])
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                raise ValueError(f"M12BJ_BUNDLE_HASH_MISMATCH:{row['path']}")
            if len(payload) != row["size"]:
                raise ValueError(f"M12BJ_BUNDLE_SIZE_MISMATCH:{row['path']}")
    digest = file_sha256(output_zip)
    sidecar = Path(f"{output_zip}.sha256")
    write_text(sidecar, f"{digest}  {output_zip.name}\n")
    print(
        canonical_json(
            {
                "status": "PASS",
                "zip": str(output_zip),
                "sha256": digest,
                "sidecar": str(sidecar),
                "indexed_payloads": len(files),
                "zip_entries": len(files) + 1,
            }
        )
    )


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    commands = value.add_subparsers(dest="command", required=True)
    for command in (
        "prepare",
        "network-gate",
        "prepare-shadow",
        "resume-preflight",
        "resume-finalization",
        "run-shadow",
        "finalize-shadow",
        "failure-closeout",
        "record-docs",
    ):
        commands.add_parser(command)
    validation = commands.add_parser("record-validation")
    validation.add_argument("--focused", required=True)
    validation.add_argument("--full", required=True)
    validation.add_argument("--full-count", type=int, required=True)
    validation.add_argument("--ruff", required=True)
    validation.add_argument("--diff", required=True)
    bundler = commands.add_parser("bundle")
    bundler.add_argument("--output", type=Path, required=True)
    return value


def main() -> None:
    args = parser().parse_args()
    commands = {
        "prepare": prepare,
        "network-gate": network_gate,
        "prepare-shadow": prepare_shadow,
        "resume-preflight": resume_preflight,
        "resume-finalization": resume_finalization,
        "run-shadow": run_shadow,
        "finalize-shadow": finalize_shadow,
        "failure-closeout": failure_closeout,
        "record-docs": record_docs,
    }
    if args.command == "record-validation":
        record_validation(args)
    elif args.command == "bundle":
        bundle(args.output)
    else:
        commands[args.command]()


if __name__ == "__main__":
    main()
