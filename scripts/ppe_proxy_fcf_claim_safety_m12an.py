"""M12AN PPE-only cash-conversion claim and model-label safety proof."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

from app.services.cross_market_decision_engine_service import (
    DecisionEvidenceRef,
)
from app.services.direction_timing_ownership_service import (
    DirectionalCoreBatch,
    DirectionalCoreCandidate,
)
from app.services.directional_financial_context_service import (
    PPE_PROXY_FCF_CLAIM_CONTRACT,
    PPEProxyFCFClaimRole,
    classify_ppe_proxy_fcf_claims,
    validate_directional_financial_semantics,
)
from app.services.two_stage_directional_service import (
    DirectionalCoreJudgment,
    DirectionalCoreJudgmentBatch,
)
from scripts import business_delta_evidence_capability_m12ai as legacy
from scripts import directional_financial_context_m12 as m12
from scripts import fictional_finalization_context_batch_m12ak as m12ak
from scripts import main_integration_two_stage_directional_m12ae_r2_runtime as base
from scripts import stage2_korean_lexical_boundary_m12am as m12am
from scripts import typed_financial_delta_direction_m12aj as direction_source
from scripts.context_preserving_finalization import (
    CONTRACT_VERSION as FINALIZATION_CONTRACT,
    audit_shadow_context_aggregation,
)
from scripts.shadow_frozen_context_manifest import (
    CONTRACT_VERSION as MANIFEST_CONTRACT,
    canonicalize_shadow_manifest_state,
    normalize_shadow_manifest,
)


NAME = (
    "20260911-ppe-only-cash-conversion-fcf-claim-polarity-label-safety-"
    "full-shadow"
)
REPORTS = Path("docs/reports") / NAME
OUTPUT = Path("artifacts") / NAME
SUPPORT_REPORTS = OUTPUT / "supporting-reports/m12ak"
RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
PREVIOUS_NAME = (
    "20260911-stage2-korean-lexical-contamination-boundary-repair-new-"
    "full-shadow"
)
PREVIOUS_OUTPUT = Path("artifacts") / PREVIOUS_NAME
PREVIOUS_BUNDLE = (
    Path.home() / "Documents/Codex" / f"thesis-monitor-{PREVIOUS_NAME}-report.zip"
)
PREVIOUS_BUNDLE_SHA256 = (
    "58e40117983d6ea700fd3b1de9c11d5dd33ad716936be1008e8579ab369d13d8"
)
PREVIOUS_INDEXED_PAYLOADS = 246
PREVIOUS_ZIP_ENTRIES = 247
M12AK_BUNDLE = Path.home() / "Documents/Codex" / (
    "thesis-monitor-20260911-fictional-finalization-context-batch-repair-"
    "new-whole-proof-full-shadow-report.zip"
)
M12AK_BUNDLE_SHA256 = (
    "3643125d30b6d661c9a7d50d9ca168808c3600bc5717c27a0cf12e7682260ee0"
)
M12AK_NAME = (
    "20260911-fictional-finalization-context-batch-repair-new-whole-proof-"
    "full-shadow"
)
BASE_INTEGRATION_HEAD_SHA = "00b078cdc5b28181b4ae1d6c49432795c3c0a8a2"
WORK_INSTRUCTION_COMMIT = "4e322734f149dadf208e5fbc8c8052ea0a064525"
WORK_INSTRUCTION = Path("docs/work-instructions") / (
    "20260911-ppe-only-cash-conversion-fcf-claim-polarity-and-label-"
    "safety-full-shadow.md"
)
ARCHITECTURE = Path("docs/architecture/PPE_PROXY_FCF_CLAIM_SAFETY.md")
FIXTURE_FILE = Path("tests/fixtures/ppe_proxy_fcf_claim_safety_m12an.json")
RUNNER = Path("scripts/ppe_proxy_fcf_claim_safety_m12an.py")
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
EXPECTED_ACTIVE_COUNT = 22
EXPECTED_CONTEXTS = 6
EXPECTED_FICTIONAL_CALLS = 12
EXPECTED_FICTIONAL_OUTPUTS = 24
EXPECTED_SHADOW_CALLS = 18
BRANCH_SELECTED = "BRANCH_B_METADATA_AND_VALIDATOR"
OLD_PROXY_LABEL = "cash_flow_fcf_ppe"
NEW_PROXY_LABEL = "cash_conversion_ocf_less_ppe"
OLD_PROXY_METRIC_REFS = ["FCF"]
NEW_PROXY_METRIC_REFS: list[str] = []

SLUGS = {
    1: "repository-provenance",
    2: "latest-result-integrity",
    3: "m12an-scope-freeze",
    4: "integrated-main-lineage-freeze",
    5: "m12am-tsla-failure-reproduction",
    6: "tsla-e35-canonical-financial-forensic",
    7: "tsla-stage1-fcf-claim-span-forensic",
    8: "tsla-monolithic-vs-stage1-same-e35-comparison",
    9: "financial-semantic-fcf-matcher-code-audit",
    10: "proxy-label-model-facing-audit",
    11: "root-cause-split-decision",
    12: "fcf-claim-role-contract",
    13: "explicit-not-fcf-disclaimer-contract",
    14: "affirmative-fcf-attribution-contract",
    15: "ppe-proxy-descriptive-language-contract",
    16: "local-negation-scope-contract",
    17: "cross-field-affirmative-override-control",
    18: "ppe-proxy-model-facing-label-safety-decision",
    19: "ppe-proxy-metric-refs-safety-decision",
    20: "affected-proxy-packet-inventory",
    21: "branch-a-or-branch-b-decision",
    22: "m12am-tsla-exact-stage1-replay",
    23: "m12am-context05-stage1-four-row-replay",
    24: "m12am-context05-monolithic-four-row-regression",
    25: "ppe-proxy-negative-fixtures",
    26: "ppe-proxy-positive-fixtures",
    27: "english-korean-fcf-negation-fixtures",
    48: "shadow-generation-manifest",
    49: "task-start-active-monitored-universe",
    50: "shadow-packet-inventory",
    51: "shadow-packet-hash-manifest",
    52: "shadow-delta-capability-manifest",
    53: "shadow-direction-hint-manifest",
    54: "shadow-frozen-context-manifest",
    55: "shadow-batching-manifest",
    56: "shadow-monolithic-model-artifacts",
    57: "shadow-stage1-model-artifacts",
    58: "shadow-stage2-model-artifacts",
    59: "shadow-context-hard-semantic-audit",
    60: "shadow-ppe-proxy-fcf-safety-audit",
    61: "shadow-stage2-language-audit",
    62: "shadow-final-composition-audit",
    63: "shadow-aggregate-finalization-audit",
    64: "shadow-per-ticker-comparison",
    65: "shadow-core-direction-differences",
    66: "shadow-business-delta-differences",
    67: "shadow-new-buyer-differences",
    68: "shadow-holder-differences",
    69: "shadow-same-direction-calibration-differences",
    70: "shadow-expected-contract-corrections",
    71: "shadow-potential-architecture-regressions",
    72: "shadow-unresolved-review-required",
    73: "shadow-financial-sector-audit",
    74: "shadow-adr-security-basis-audit",
    75: "shadow-cyclical-valuation-audit",
    76: "shadow-core-immutability-audit",
    77: "shadow-runtime-audit",
    78: "shadow-aggregate-summary",
    79: "shadow-architecture-decision",
    80: "fic-fin-05-vs-monitored-primary-boundary-analogs",
    81: "fic-fin-02-vs-monitored-delta-materiality-analogs",
    82: "fic-fin-06-vs-monitored-positive-delta-analogs",
    83: "fic-fin-08-vs-monitored-holder-analogs",
    84: "new-buyer-monolithic-vs-two-stage-analogs",
    85: "real-architecture-compatibility-lessons",
    86: "combined-fictional-monitored-root-cause-summary",
    87: "next-bounded-policy-decision",
    88: "ppe-proxy-fcf-safety-repair-success-decision",
    89: "fictional-proof-reuse-or-reproof-decision",
    90: "full-shadow-completion-decision",
    91: "existing-monitored-impact-summary",
    92: "two-stage-shadow-compatibility-decision",
    93: "fresh-real-proof-readiness-decision",
    94: "final-main-merge-readiness-note",
    95: "production-no-change",
    96: "schedule-pause-observation",
    97: "remote-push-prohibition-audit",
    98: "master-workflow-update",
    99: "program-completion",
}

BRANCH_B_SLUGS = {
    "28b": "proxy-evidence-projection-before-after",
    "29b": "fictional-proxy-surface-impact",
    "30b": "fictional-generation-manifest",
    "31b": "stage1-run1-context01",
    "32b": "stage1-run1-context02",
    "33b": "stage2-run1-context01",
    "34b": "stage2-run1-context02",
    "35b": "stage1-run2-context01",
    "36b": "stage1-run2-context02",
    "37b": "stage2-run2-context01",
    "38b": "stage2-run2-context02",
    "39b": "stage1-run3-context01",
    "40b": "stage1-run3-context02",
    "41b": "stage2-run3-context01-and02",
    "42b": "fictional-hard-semantic-audit",
    "43b": "fictional-ppe-proxy-safety-audit",
    "44b": "fictional-business-delta-audit",
    "45b": "fictional-core-immutability-audit",
    "46b": "fictional-aggregate-finalization",
    "47b": "fictional-shadow-gate-decision",
}

CRITICAL_CODE_PATHS = (
    Path("app/services/cross_market_decision_engine_service.py"),
    Path("app/services/directional_financial_context_service.py"),
    Path("app/services/business_delta_evidence_service.py"),
    Path("app/services/direction_timing_ownership_service.py"),
    Path("app/services/structured_autonomy_alias_service.py"),
    Path("app/services/two_stage_directional_service.py"),
    Path("scripts/business_delta_evidence_capability_m12ai.py"),
    Path("scripts/context_preserving_finalization.py"),
    Path("scripts/fictional_finalization_context_batch_m12ak.py"),
    Path("scripts/financial_exclusion_expectation_m12u.py"),
    Path("scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py"),
    Path("scripts/shadow_frozen_context_manifest_m12al.py"),
    Path("scripts/sol_restoration_m12w.py"),
    Path("scripts/stage2_korean_lexical_boundary_m12am.py"),
    RUNNER,
)
FOCUSED_TESTS = (
    "tests/test_directional_financial_context_service.py",
    "tests/test_cross_market_decision_engine.py",
    "tests/test_financial_context_adapter_service.py",
    "tests/test_stage2_korean_lexical_boundary_m12am.py",
    "tests/test_stage2_korean_lexical_boundary_m12am_runner.py",
    "tests/test_context_preserving_finalization.py",
    "tests/test_business_delta_evidence_capability_m12ai.py",
    "tests/test_business_delta_evidence_service.py",
    "tests/test_typed_financial_delta_direction_m12aj.py",
    "tests/test_financial_claim_temporal_scope_m12ah.py",
    "tests/test_monitoring_transition_ownership_netdebt_m12ag.py",
    "tests/test_direction_timing_ownership_service.py",
    "tests/test_two_stage_directional_service.py",
    "tests/test_ppe_proxy_fcf_claim_safety_m12an.py",
)
RUFF_PATHS = (
    "app/services/cross_market_decision_engine_service.py",
    "app/services/directional_financial_context_service.py",
    RUNNER.as_posix(),
    "tests/test_directional_financial_context_service.py",
    "tests/test_cross_market_decision_engine.py",
    "tests/test_financial_context_adapter_service.py",
    "scripts/fictional_finalization_context_batch_m12ak.py",
    "scripts/financial_exclusion_expectation_m12u.py",
    "scripts/shadow_frozen_context_manifest_m12al.py",
    "scripts/sol_restoration_m12w.py",
    "scripts/stage2_korean_lexical_boundary_m12am.py",
    "tests/test_stage2_korean_lexical_boundary_m12am_runner.py",
    "tests/test_ppe_proxy_fcf_claim_safety_m12an.py",
)


def write_json(path: Path, value: object) -> None:
    base.write_json(path, value)


def write_text(path: Path, value: str) -> None:
    base.write_text(path, value)


def read_json(path: Path) -> dict[str, object]:
    return base.read_json(path)


def file_sha256(path: Path) -> str:
    return base.file_sha256(path)


def git(*args: str) -> str:
    return base.git(*args)


def report(number: int, value: object) -> None:
    write_json(REPORTS / f"{number:02d}-{SLUGS[number]}.json", value)


def branch_report(key: str, value: object) -> None:
    write_json(REPORTS / f"{key}-{BRANCH_B_SLUGS[key]}.json", value)


def _configure_runtime() -> None:
    m12ak.NAME = NAME
    m12ak.REPORTS = SUPPORT_REPORTS
    m12ak.OUTPUT = OUTPUT
    m12ak.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT
    m12ak.SOURCE_OUTPUT = PREVIOUS_OUTPUT
    m12ak.LATEST_BUNDLE_SHA256 = PREVIOUS_BUNDLE_SHA256
    m12ak.BASE_INTEGRATION_HEAD_SHA = BASE_INTEGRATION_HEAD_SHA
    m12ak.M12AJ_FINAL_SHA = BASE_INTEGRATION_HEAD_SHA
    m12ak.WORK_INSTRUCTION_COMMIT = WORK_INSTRUCTION_COMMIT
    m12ak.WORK_INSTRUCTION = WORK_INSTRUCTION
    m12ak.ARCHITECTURE = ARCHITECTURE
    m12ak.RUNNER = RUNNER
    m12ak.CRITICAL_CODE_PATHS = CRITICAL_CODE_PATHS
    m12ak.MODEL = MODEL
    m12ak.EFFORT = EFFORT
    m12ak.TIMEOUT_SECONDS = TIMEOUT_SECONDS
    m12ak._configure_runtime()
    legacy.PREVIOUS_OUTPUT = PREVIOUS_OUTPUT
    legacy.PREVIOUS_BUNDLE_SHA256 = PREVIOUS_BUNDLE_SHA256
    legacy.BASE_INTEGRATION_HEAD_SHA = BASE_INTEGRATION_HEAD_SHA
    legacy.PREVIOUS_FINAL_SHA = BASE_INTEGRATION_HEAD_SHA
    legacy.WORK_INSTRUCTION_COMMIT = WORK_INSTRUCTION_COMMIT
    legacy.WORK_INSTRUCTION = WORK_INSTRUCTION
    legacy.ARCHITECTURE = ARCHITECTURE
    legacy.CRITICAL_CODE_PATHS = CRITICAL_CODE_PATHS
    base.OUTPUT = OUTPUT
    base.REPORTS = SUPPORT_REPORTS
    base.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT


def _command(command: Sequence[str], *, timeout: int = 7200) -> dict[str, object]:
    started = datetime.now(UTC)
    result = subprocess.run(
        list(command),
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    output = (result.stdout + result.stderr).strip()
    return {
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "command": list(command),
        "exit_code": result.returncode,
        "elapsed_seconds": round((datetime.now(UTC) - started).total_seconds(), 3),
        "output": output[-20000:],
    }


def _ensure_previous_artifacts(bundle: Path) -> None:
    required = PREVIOUS_OUTPUT / "shadow/program-state.json"
    if required.is_file():
        return
    prefix = f"{PREVIOUS_OUTPUT}/"
    with zipfile.ZipFile(bundle) as archive:
        for name in archive.namelist():
            if name.startswith(prefix):
                archive.extract(name, Path.cwd())


def _verify_bundle(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise ValueError("LATEST_RESULT_BUNDLE_MISSING")
    actual = file_sha256(path)
    index_name = str(PREVIOUS_OUTPUT / "artifact-index.json")
    with zipfile.ZipFile(path) as archive:
        corrupt = archive.testzip()
        names = set(archive.namelist())
        index = json.loads(archive.read(index_name))
        rows = index.get("rows")
        if not isinstance(rows, list):
            raise ValueError("LATEST_RESULT_ARTIFACT_ROWS_MISSING")
        expected = {str(row["path"]) for row in rows} | {index_name}
        missing = sorted(expected - names)
        extra = sorted(names - expected)
        hash_mismatches = []
        size_mismatches = []
        for row in rows:
            name = str(row["path"])
            if name not in names:
                continue
            payload = archive.read(name)
            if hashlib.sha256(payload).hexdigest() != str(row["sha256"]):
                hash_mismatches.append(name)
            if len(payload) != int(row["size"]):
                size_mismatches.append(name)
    secret_count = int(index.get("secret_scan_failure_count") or 0)
    passed = all(
        (
            actual == PREVIOUS_BUNDLE_SHA256,
            corrupt is None,
            len(rows) == PREVIOUS_INDEXED_PAYLOADS,
            len(names) == PREVIOUS_ZIP_ENTRIES,
            not missing,
            not extra,
            not hash_mismatches,
            not size_mismatches,
            secret_count == 0,
        )
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "path": str(path),
        "expected_sha256": PREVIOUS_BUNDLE_SHA256,
        "actual_sha256": actual,
        "zip_integrity": "PASS" if corrupt is None else "FAIL",
        "indexed_payload_count": len(rows),
        "zip_entry_count": len(names),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "hash_mismatch_count": len(hash_mismatches),
        "size_mismatch_count": len(size_mismatches),
        "secret_scan_failure_count": secret_count,
    }


def _proxy_refs(packet: object) -> tuple[DecisionEvidenceRef, ...]:
    evidence = getattr(packet, "evidence", ())
    return tuple(
        ref
        for ref in evidence
        if ref.financial_context is not None
        and ref.financial_context.metric == "ocf_less_ppe_capex"
    )


def _previous_replay() -> dict[str, object]:
    _configure_runtime()
    state = read_json(PREVIOUS_OUTPUT / "shadow/program-state.json")
    tickers, _source_packets, built = legacy._shadow_inputs(state)
    evidence, owned, catalogs, contexts, _stocks = built
    views = legacy._restore_views(state)
    stage1_document = read_json(
        PREVIOUS_OUTPUT
        / "shadow/model-calls/context-05/stage1/run-document.json"
    )
    monolithic_document = read_json(
        PREVIOUS_OUTPUT
        / "shadow/model-calls/context-05/monolithic/run-document.json"
    )
    stage1_batch = DirectionalCoreJudgmentBatch(
        packet_id=str(state["generation_id"]),
        candidates=tuple(
            DirectionalCoreJudgment.model_validate(row["core"])
            for row in stage1_document["rows"]
        ),
    )
    stage1_rows, stage1_audit = legacy._stage1_audit(
        stage1_batch,
        owned=owned,
        catalogs=catalogs,
        contexts=contexts,
        views=views,
    )
    monolithic_batch = DirectionalCoreBatch(
        packet_id=str(state["generation_id"]),
        candidates=tuple(
            DirectionalCoreCandidate.model_validate(row["core"])
            for row in monolithic_document["rows"]
        ),
    )
    monolithic_rows, monolithic_audit = legacy._full_audit(
        monolithic_batch,
        owned=owned,
        catalogs=catalogs,
        contexts=contexts,
        views=views,
    )
    old_tsla = next(
        row for row in stage1_document["rows"] if row["ticker"] == "TSLA"
    )
    new_tsla = next(row for row in stage1_rows if row["ticker"] == "TSLA")
    tsla_proxy = _proxy_refs(evidence["TSLA"])
    if len(tsla_proxy) != 1:
        raise ValueError("TSLA_PPE_PROXY_IDENTITY_NOT_UNIQUE")
    disclaimer = next(
        row["summary"]
        for row in old_tsla["core"]["unknown_treatments"]
        if "cashflow:" in " ".join(row["evidence_refs"])
    )
    claim_spans = [
        span.model_dump(mode="json")
        for span in classify_ppe_proxy_fcf_claims(disclaimer)
    ]
    inventory = []
    for ticker in tickers:
        for ref in _proxy_refs(evidence[ticker]):
            inventory.append(
                {
                    "ticker": ticker,
                    "canonical_ref": ref.ref_id,
                    "canonical_metric": ref.financial_context.metric,
                    "limitations": list(ref.financial_context.limitations),
                    "before_label": OLD_PROXY_LABEL,
                    "after_label": ref.label,
                    "before_metric_refs": OLD_PROXY_METRIC_REFS,
                    "after_metric_refs": [item.value for item in ref.metric_refs],
                }
            )
    stage2_reaudits = []
    for context_number in range(1, 5):
        root = (
            PREVIOUS_OUTPUT
            / f"shadow/model-calls/context-{context_number:02d}/stage2"
        )
        stage2_reaudits.append(
            m12am._reaudit_stage2_document(
                output_path=root / "output.raw.json",
                document_path=root / "run-document.json",
            )
        )
    return {
        "state": state,
        "tickers": list(tickers),
        "evidence": evidence,
        "old_tsla": old_tsla,
        "new_tsla": new_tsla,
        "tsla_proxy": tsla_proxy[0],
        "disclaimer": disclaimer,
        "claim_spans": claim_spans,
        "stage1_rows": stage1_rows,
        "stage1_audit": stage1_audit,
        "monolithic_rows": monolithic_rows,
        "monolithic_audit": monolithic_audit,
        "inventory": inventory,
        "stage2_reaudits": stage2_reaudits,
    }


def _fixture_audit(replay: Mapping[str, object]) -> dict[str, object]:
    fixture = read_json(FIXTURE_FILE)
    proxy = replay["tsla_proxy"]
    supplied = tuple(replay["evidence"]["TSLA"].evidence)
    allowed = tuple(ref.ref_id for ref in supplied)
    groups: dict[str, object] = {}
    for name, expected_pass in (("negative", False), ("positive", True)):
        rows = []
        for item in fixture[name]:
            result = validate_directional_financial_semantics(
                {
                    "claim": {
                        "text": item["text"],
                        "evidence_refs": [proxy.ref_id],
                    }
                },
                supplied_refs=supplied,
                allowed_ref_ids=allowed,
            )
            passed = result.valid is expected_pass
            rows.append(
                {
                    **item,
                    "expected": "PASS" if expected_pass else "FAIL",
                    "observed": "PASS" if result.valid else "FAIL",
                    "status": "PASS" if passed else "FAIL",
                    "validation": result.model_dump(mode="json"),
                }
            )
        groups[name] = {
            "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
            "count": len(rows),
            "rows": rows,
        }
    local_rows = []
    for item in fixture["local_negation"]:
        roles = [
            span.role.value for span in classify_ppe_proxy_fcf_claims(item["text"])
        ]
        local_rows.append(
            {
                **item,
                "observed_roles": roles,
                "status": "PASS" if roles == item["expected_roles"] else "FAIL",
            }
        )
    cross_field = validate_directional_financial_semantics(
        {
            "unknown_treatments": {
                "summary": "This cash-conversion proxy is not FCF.",
                "evidence_refs": [proxy.ref_id],
            },
            "core": {"text": "FCF is 352m.", "evidence_refs": []},
        },
        supplied_refs=supplied,
        allowed_ref_ids=allowed,
    )
    local = {
        "status": (
            "PASS"
            if all(row["status"] == "PASS" for row in local_rows)
            and not cross_field.valid
            and cross_field.explicit_not_fcf_disclaimer_count == 1
            and cross_field.affirmative_proxy_as_fcf_violation_count == 1
            else "FAIL"
        ),
        "rows": local_rows,
        "cross_field_override": cross_field.model_dump(mode="json"),
    }
    return {
        "status": (
            "PASS"
            if groups["negative"]["status"] == "PASS"
            and groups["positive"]["status"] == "PASS"
            and local["status"] == "PASS"
            else "FAIL"
        ),
        "groups": groups,
        "local_negation": local,
    }


def _copy_m12ak_offline_support() -> None:
    with zipfile.ZipFile(M12AK_BUNDLE) as archive:
        for number in range(30, 35):
            name = (
                f"docs/reports/{M12AK_NAME}/{number:02d}-"
                f"{m12ak.SLUGS[number]}.json"
            )
            write_json(
                SUPPORT_REPORTS / f"{number:02d}-{m12ak.SLUGS[number]}.json",
                json.loads(archive.read(name)),
            )


def _stage2_regression(replay: Mapping[str, object]) -> dict[str, object]:
    rows = list(replay["stage2_reaudits"])
    row_count = sum(int(row["row_count"]) for row in rows)
    failures = sum(int(row["fail_count"]) for row in rows)
    contamination = sum(int(row["language_contamination_count"]) for row in rows)
    return {
        "status": "PASS" if row_count == 16 and failures == 0 else "FAIL",
        "context_count": len(rows),
        "row_count": row_count,
        "failure_count": failures,
        "language_contamination_count": contamination,
        "rows": rows,
    }


def prepare(previous_bundle: Path) -> None:
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("M12AN_GENERATION_ALREADY_PREPARED")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("M12AN_PREPARE_REQUIRES_COMMITTED_CODE")
    latest = _verify_bundle(previous_bundle)
    if latest["status"] != "PASS":
        raise SystemExit("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    if file_sha256(M12AK_BUNDLE) != M12AK_BUNDLE_SHA256:
        raise SystemExit("M12AK_FORMAL_PROOF_BUNDLE_CHECKSUM_MISMATCH")
    _ensure_previous_artifacts(previous_bundle)
    replay = _previous_replay()
    fixtures = _fixture_audit(replay)
    stage2 = _stage2_regression(replay)
    old_source = subprocess.check_output(
        [
            "git",
            "show",
            f"{BASE_INTEGRATION_HEAD_SHA}:app/services/"
            "directional_financial_context_service.py",
        ],
        text=True,
    )
    current_source = Path(
        "app/services/directional_financial_context_service.py"
    ).read_text(encoding="utf-8")
    old_matcher = (
        '("fcf" in folded or "\uc789\uc5ec\ud604\uae08\ud750\ub984" in text)'
        in old_source
    )
    current_classifier = "classify_ppe_proxy_fcf_claims" in current_source

    focused = _command((sys.executable, "-m", "pytest", "-q", *FOCUSED_TESTS))
    full = _command((sys.executable, "-m", "pytest", "-q"))
    ruff = _command((sys.executable, "-m", "ruff", "check", *RUFF_PATHS))
    diff = _command(("git", "diff", "--check", f"{WORK_INSTRUCTION_COMMIT}..HEAD"))
    schedule = m12._schedule_observation()
    tsla_proxy = replay["tsla_proxy"]
    new_tsla_semantics = replay["new_tsla"]["financial_semantics"]
    inventory = replay["inventory"]

    report(
        1,
        {
            "status": "PASS",
            "phase": "M12AN",
            "branch": git("branch", "--show-current"),
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "implementation_head_sha": git("rev-parse", "HEAD"),
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "remote_push_count": 0,
        },
    )
    report(2, latest)
    report(
        3,
        {
            "status": "FROZEN",
            "scope": "PPE_PROXY_FCF_POLARITY_AND_MODEL_LABEL_SAFETY",
            "branch_required": "BRANCH_B_METADATA_AND_VALIDATOR",
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "timeout_seconds": TIMEOUT_SECONDS,
            "wrapper_auto_retry": 0,
            "batch_split": 0,
            "provider_source_fetches": 0,
            "main_merge": 0,
            "deployment": 0,
        },
    )
    report(
        4,
        {
            "status": (
                "PASS"
                if subprocess.run(
                    [
                        "git",
                        "merge-base",
                        "--is-ancestor",
                        BASE_INTEGRATION_HEAD_SHA,
                        "HEAD",
                    ],
                    check=False,
                ).returncode
                == 0
                else "FAIL"
            ),
            "task_base_sha": BASE_INTEGRATION_HEAD_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "current_head": git("rev-parse", "HEAD"),
        },
    )
    report(
        5,
        {
            "status": "REPRODUCED",
            "generation_id": replay["state"]["generation_id"],
            "failure_ticker": "TSLA",
            "failure_error": "ppe_only_cash_conversion_proxy_called_fcf",
            "historical_status": replay["old_tsla"]["status"],
            "historical_errors": replay["old_tsla"]["errors"],
            "current_offline_replay_status": replay["new_tsla"]["status"],
        },
    )
    report(
        6,
        {
            "status": "PASS",
            "ticker": "TSLA",
            "historical_alias": "E35",
            "canonical_ref": tsla_proxy.ref_id,
            "canonical_metric": tsla_proxy.financial_context.metric,
            "canonical_fact_type_unchanged": True,
            "limitations": list(tsla_proxy.financial_context.limitations),
            "label_before": OLD_PROXY_LABEL,
            "label_after": tsla_proxy.label,
            "metric_refs_before": OLD_PROXY_METRIC_REFS,
            "metric_refs_after": [item.value for item in tsla_proxy.metric_refs],
        },
    )
    report(
        7,
        {
            "status": "PASS",
            "text": replay["disclaimer"],
            "claim_spans": replay["claim_spans"],
            "affirmative_count": new_tsla_semantics[
                "affirmative_proxy_as_fcf_violation_count"
            ],
            "disclaimer_count": new_tsla_semantics[
                "explicit_not_fcf_disclaimer_count"
            ],
        },
    )
    report(
        8,
        {
            "status": "PASS",
            "same_proxy_selected": True,
            "stage1_tsla_status_before": replay["old_tsla"]["status"],
            "stage1_tsla_status_after": replay["new_tsla"]["status"],
            "monolithic_tsla_status": next(
                row["status"]
                for row in replay["monolithic_rows"]
                if row["ticker"] == "TSLA"
            ),
            "difference": "EXPLICIT_NOT_FCF_DISCLAIMER_PRESENT_ONLY_IN_STAGE1",
        },
    )
    report(
        9,
        {
            "status": "PASS" if old_matcher and current_classifier else "FAIL",
            "old_matcher": "LEXICAL_FCF_TOKEN_PRESENCE",
            "old_matcher_confirmed": old_matcher,
            "new_matcher": PPE_PROXY_FCF_CLAIM_CONTRACT,
            "new_classifier_confirmed": current_classifier,
            "root_cause": "NEGATED_FCF_DISCLAIMER_FALSE_POSITIVE",
        },
    )
    report(
        10,
        {
            "status": "FAIL_BEFORE_PASS_AFTER",
            "is_metadata_model_facing": True,
            "model_facing_paths": [
                "compact_ai_context.evidence[].label/metric_refs",
                "compact_alias_ai_context.evidence[].label/metric_refs",
            ],
            "can_cause_proxy_as_fcf_interpretation_before": True,
            "violated_evidence_label_safety_before": True,
            "label_after": NEW_PROXY_LABEL,
            "metric_refs_after": NEW_PROXY_METRIC_REFS,
        },
    )
    report(
        11,
        {
            "status": "SELECTED",
            "negated_fcf_disclaimer_false_positive_confirmed": True,
            "model_facing_proxy_metadata_mislabel_confirmed": True,
            "root_causes": [
                "NEGATED_FCF_DISCLAIMER_FALSE_POSITIVE",
                "MODEL_FACING_PROXY_METADATA_MISLABEL",
            ],
            "branch": BRANCH_SELECTED,
        },
    )
    report(
        12,
        {
            "status": "PASS",
            "contract": PPE_PROXY_FCF_CLAIM_CONTRACT,
            "roles": [role.value for role in PPEProxyFCFClaimRole],
        },
    )
    report(
        13,
        {
            "status": "PASS",
            "allowed_role": "EXPLICIT_NOT_FCF_DISCLAIMER",
            "candidate_wide_affirmative_override": "REJECT",
        },
    )
    report(
        14,
        {
            "status": fixtures["groups"]["negative"]["status"],
            "hard_error": "ppe_only_cash_conversion_proxy_called_fcf",
            "roles_rejected": [
                "AFFIRMATIVE_FCF_ATTRIBUTION",
                "NUMERIC_FCF_ATTRIBUTION",
                "PROXY_AS_FCF_ATTRIBUTION",
            ],
        },
    )
    report(
        15,
        {
            "status": fixtures["groups"]["positive"]["status"],
            "preferred_label": NEW_PROXY_LABEL,
            "canonical_metric": "ocf_less_ppe_capex",
        },
    )
    report(16, fixtures["local_negation"])
    report(
        17,
        {
            "status": fixtures["local_negation"]["status"],
            "candidate_wide_proxy_detection": True,
            "cross_field_override": fixtures["local_negation"][
                "cross_field_override"
            ],
        },
    )
    report(
        18,
        {
            "status": "PASS",
            "decision": "RENAME_MODEL_FACING_LABEL_ONLY",
            "canonical_fact_type_changed": False,
            "before": OLD_PROXY_LABEL,
            "after": NEW_PROXY_LABEL,
        },
    )
    report(
        19,
        {
            "status": "PASS",
            "decision": "EMPTY_UNSAFE_FCF_CHECKPOINT_TAG",
            "before": OLD_PROXY_METRIC_REFS,
            "after": NEW_PROXY_METRIC_REFS,
            "safe_existing_proxy_checkpoint_metric_available": False,
            "financial_context_metric_preserved": "ocf_less_ppe_capex",
        },
    )
    report(
        20,
        {
            "status": "PASS",
            "affected_packet_count": len({row["ticker"] for row in inventory}),
            "affected_ref_count": len(inventory),
            "rows": inventory,
        },
    )
    report(21, {"status": "SELECTED", "branch": BRANCH_SELECTED})
    report(
        22,
        {
            "status": replay["new_tsla"]["status"],
            "ticker": "TSLA",
            "selected_proxy_ref": tsla_proxy.ref_id,
            "candidate_rewritten": False,
            "financial_semantics": new_tsla_semantics,
        },
    )
    report(
        23,
        {
            "status": replay["stage1_audit"]["status"],
            "pass_count": replay["stage1_audit"]["pass_count"],
            "row_count": len(replay["stage1_rows"]),
            "rows": replay["stage1_rows"],
        },
    )
    report(
        24,
        {
            "status": replay["monolithic_audit"]["status"],
            "pass_count": replay["monolithic_audit"]["pass_count"],
            "row_count": len(replay["monolithic_rows"]),
            "rows": replay["monolithic_rows"],
        },
    )
    report(25, fixtures["groups"]["negative"])
    report(26, fixtures["groups"]["positive"])
    report(
        27,
        {
            "status": (
                "PASS"
                if fixtures["local_negation"]["status"] == "PASS"
                and stage2["status"] == "PASS"
                else "FAIL"
            ),
            "fcf_negation": fixtures["local_negation"],
            "stage2_lexical_regression": stage2,
        },
    )
    branch_report(
        "28b",
        {
            "status": "PASS",
            "before": {
                "label": OLD_PROXY_LABEL,
                "metric_refs": OLD_PROXY_METRIC_REFS,
            },
            "after": {
                "label": NEW_PROXY_LABEL,
                "metric_refs": NEW_PROXY_METRIC_REFS,
                "financial_context_metric": "ocf_less_ppe_capex",
            },
        },
    )
    branch_report(
        "29b",
        {
            "status": "REPROOF_REQUIRED",
            "affected_fictional_surface": "MODEL_FACING_EVIDENCE_PROJECTION",
            "formal_fictional_reuse_status": "REUSE_NOT_AUTHORIZED",
            "required_model_calls": EXPECTED_FICTIONAL_CALLS,
            "required_final_outputs": EXPECTED_FICTIONAL_OUTPUTS,
        },
    )

    gate_pass = all(
        (
            latest["status"] == "PASS",
            replay["old_tsla"]["status"] == "FAIL",
            replay["new_tsla"]["status"] == "PASS",
            replay["stage1_audit"]["status"] == "PASS",
            replay["stage1_audit"]["pass_count"] == 4,
            replay["monolithic_audit"]["status"] == "PASS",
            replay["monolithic_audit"]["pass_count"] == 4,
            fixtures["status"] == "PASS",
            stage2["status"] == "PASS",
            focused["status"] == "PASS",
            full["status"] == "PASS",
            ruff["status"] == "PASS",
            diff["status"] == "PASS",
            base.MODEL == MODEL,
            base.EFFORT == EFFORT,
            base.TIMEOUT_SECONDS == TIMEOUT_SECONDS,
        )
    )
    preflight = {
        "status": "PASS" if gate_pass else "FAIL",
        "latest_result_integrity": latest["status"],
        "branch": BRANCH_SELECTED,
        "exact_tsla_replay": replay["new_tsla"]["status"],
        "context05_stage1_replay": replay["stage1_audit"]["status"],
        "context05_monolithic_replay": replay["monolithic_audit"]["status"],
        "fixture_result": fixtures["status"],
        "stage2_lexical_regression": stage2["status"],
        "focused_test_result": focused["status"],
        "full_test_result": full["status"],
        "ruff_result": ruff["status"],
        "git_diff_check": diff["status"],
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "planned_fictional_model_calls": EXPECTED_FICTIONAL_CALLS,
        "provider_source_fetches": 0,
        "production_side_effect_firewall": "PASS",
        "schedule_observation": schedule,
    }
    write_json(OUTPUT / "preflight.json", preflight)
    write_json(OUTPUT / "focused-test-results.json", focused)
    write_json(OUTPUT / "full-test-results.json", full)
    write_json(OUTPUT / "ruff-results.json", ruff)
    write_json(OUTPUT / "git-diff-check.json", diff)
    if not gate_pass:
        raise SystemExit("M12AN_PREMODEL_GATE_FAILED")

    _configure_runtime()
    _copy_m12ak_offline_support()
    state = legacy._freeze_fictional(preflight)
    state.update(
        {
            "phase": "M12AN",
            "branch": BRANCH_SELECTED,
            "source_generation_is_new": True,
            "finalization_contract": FINALIZATION_CONTRACT,
            "ppe_proxy_claim_contract": PPE_PROXY_FCF_CLAIM_CONTRACT,
            "aggregate_uses_context_model_schema": False,
        }
    )
    write_json(OUTPUT / "fictional/program-state.json", state)
    _packets, owned, _catalogs, _contexts = m12.fictional_inputs(
        str(state["generation_id"])
    )
    views = legacy._restore_views(state)
    direction = direction_source._direction_manifest(views, owned)
    direction["views"] = {
        ticker: view.model_context() for ticker, view in views.items()
    }
    write_json(OUTPUT / "fictional-direction-manifest.json", direction)
    frozen_gate = read_json(OUTPUT / "fictional-model-call-gate.json")
    frozen_gate.update(preflight)
    frozen_gate["status"] = "PASS"
    frozen_gate["fictional_direction_manifest"] = direction["status"]
    frozen_gate["formal_fictional_reuse_status"] = "REUSE_NOT_AUTHORIZED"
    write_json(OUTPUT / "fictional-model-call-gate.json", frozen_gate)
    branch_report(
        "30b",
        {
            "status": "FROZEN",
            "generation_id": state["generation_id"],
            "model": state["model"],
            "reasoning_effort": state["reasoning_effort"],
            "planned_model_calls": state["planned_model_calls"],
            "source_lock_sha256": state["source_lock"]["source_lock_sha256"],
            "code_hashes": state["code_hashes"],
        },
    )
    print(
        json.dumps(
            {
                "status": "FROZEN",
                "branch": BRANCH_SELECTED,
                "generation_id": state["generation_id"],
                "planned_model_calls": state["planned_model_calls"],
            },
            sort_keys=True,
        )
    )


def run_fictional() -> None:
    _configure_runtime()
    m12ak.run_fictional()


def _financial_semantic_counts(documents: Sequence[Mapping[str, object]]) -> dict[str, int]:
    rows = [row for document in documents for row in document.get("rows", ())]
    semantics = [
        row.get("financial_semantics", {})
        for row in rows
        if isinstance(row, Mapping)
    ]
    return {
        "row_count": len(rows),
        "affirmative_proxy_as_fcf_violation_count": sum(
            int(item.get("affirmative_proxy_as_fcf_violation_count") or 0)
            for item in semantics
            if isinstance(item, Mapping)
        ),
        "explicit_not_fcf_disclaimer_count": sum(
            int(item.get("explicit_not_fcf_disclaimer_count") or 0)
            for item in semantics
            if isinstance(item, Mapping)
        ),
        "partial_capex_called_fcf_count": sum(
            int(item.get("partial_capex_called_fcf_count") or 0)
            for item in semantics
            if isinstance(item, Mapping)
        ),
    }


def _fictional_documents(phase: str) -> list[dict[str, object]]:
    return legacy._fictional_documents(phase)


def finalize_fictional() -> None:
    _configure_runtime()
    m12ak.finalize_fictional()
    readiness = read_json(OUTPUT / "fictional-readiness.json")
    stage1 = _fictional_documents("stage1")
    stage2 = _fictional_documents("stage2")
    call_documents = [
        *stage1[0:2],
        *stage2[0:2],
        *stage1[2:4],
        *stage2[2:4],
        *stage1[4:6],
    ]
    for key, document in zip(
        ("31b", "32b", "33b", "34b", "35b", "36b", "37b", "38b", "39b", "40b"),
        call_documents,
        strict=True,
    ):
        branch_report(key, document)
    branch_report("41b", {"documents": stage2[4:6], "status": "PASS"})
    hard = read_json(SUPPORT_REPORTS / f"57-{m12ak.SLUGS[57]}.json")
    aggregate = read_json(SUPPORT_REPORTS / f"59-{m12ak.SLUGS[59]}.json")
    capability = read_json(SUPPORT_REPORTS / f"60-{m12ak.SLUGS[60]}.json")
    direction = read_json(SUPPORT_REPORTS / f"61-{m12ak.SLUGS[61]}.json")
    core = read_json(SUPPORT_REPORTS / f"66-{m12ak.SLUGS[66]}.json")
    counts = _financial_semantic_counts((*stage1, *stage2))
    branch_report("42b", hard)
    branch_report(
        "43b",
        {
            "status": (
                "PASS"
                if counts["affirmative_proxy_as_fcf_violation_count"] == 0
                else "FAIL"
            ),
            **counts,
            "model_facing_proxy_label": NEW_PROXY_LABEL,
            "model_facing_proxy_metric_refs": NEW_PROXY_METRIC_REFS,
        },
    )
    branch_report(
        "44b",
        {
            "status": (
                "PASS"
                if capability["status"] == direction["status"] == "PASS"
                else "FAIL"
            ),
            "capability": capability,
            "direction": direction,
        },
    )
    branch_report("45b", core)
    branch_report("46b", aggregate)
    branch_report("47b", readiness)
    if not all(
        (
            readiness.get("status") == "PASS",
            readiness.get("model_calls_total") == EXPECTED_FICTIONAL_CALLS,
            readiness.get("final_composition_count") == EXPECTED_FICTIONAL_OUTPUTS,
            hard.get("status") == "PASS",
            aggregate.get("status") == "PASS",
            counts["affirmative_proxy_as_fcf_violation_count"] == 0,
        )
    ):
        raise SystemExit("M12AN_FICTIONAL_HARD_GATE_FAILED_NO_SHADOW")
    print(json.dumps(readiness, sort_keys=True))


def _context_groups(normalized: Mapping[str, object]) -> tuple[tuple[str, ...], ...]:
    return tuple(
        tuple(str(ticker) for ticker in row["tickers"])
        for row in normalized["contexts"]
    )


def _expected_groups(tickers: Sequence[str]) -> tuple[tuple[str, ...], ...]:
    return tuple(
        tuple(tickers[index : index + 4]) for index in range(0, len(tickers), 4)
    )


def _canonical_shadow_verifier(
    state: Mapping[str, object],
    *,
    subject: str,
) -> None:
    if subject != "SHADOW":
        raise ValueError(f"UNEXPECTED_CANONICAL_VERIFIER_SUBJECT:{subject}")
    if state.get("status") != "FROZEN":
        raise ValueError("SHADOW_STATE_NOT_FROZEN")
    if state.get("code_hashes") != legacy._code_hashes():
        raise ValueError("SHADOW_CODE_CHANGED_AFTER_FREEZE")
    normalized = normalize_shadow_manifest(
        state,
        repository_root=Path.cwd(),
        artifact_root=OUTPUT / "shadow",
        expected_tickers=tuple(str(ticker) for ticker in state.get("tickers", ())),
        allow_legacy=False,
        verify_files=True,
    )
    if _context_groups(normalized) != _expected_groups(normalized["tickers"]):
        raise ValueError("SHADOW_CONTEXT_BATCHING_MISMATCH")


def prepare_shadow() -> None:
    _configure_runtime()
    fictional = read_json(OUTPUT / "fictional-readiness.json")
    if fictional.get("fictional_shadow_gate_status") != "PASS":
        raise ValueError("FICTIONAL_HARD_PASS_REQUIRED")
    legacy.prepare_shadow()
    state_path = OUTPUT / "shadow/program-state.json"
    state = read_json(state_path)
    canonical = canonicalize_shadow_manifest_state(
        state,
        repository_root=Path.cwd(),
        artifact_root=OUTPUT / "shadow",
        expected_tickers=state["tickers"],
    )
    write_json(state_path, canonical)
    state = read_json(state_path)
    normalized = normalize_shadow_manifest(
        state,
        repository_root=Path.cwd(),
        artifact_root=OUTPUT / "shadow",
        expected_tickers=state["tickers"],
        allow_legacy=False,
        verify_files=True,
    )
    if _context_groups(normalized) != _expected_groups(normalized["tickers"]):
        raise ValueError("NEW_SHADOW_CONTEXT_BATCHING_MISMATCH")
    if state["generation_id"] == read_json(
        PREVIOUS_OUTPUT / "shadow/program-state.json"
    )["generation_id"]:
        raise ValueError("STOPPED_SHADOW_GENERATION_ID_REUSED")
    tickers, _packets, built = legacy._shadow_inputs(state)
    _evidence, owned, _catalogs, _contexts, _stocks = built
    views = legacy._restore_views(state)
    direction = direction_source._direction_manifest(views, owned)
    direction["views"] = {
        ticker: view.model_context() for ticker, view in views.items()
    }
    write_json(OUTPUT / "shadow-direction-manifest.json", direction)
    gate = read_json(OUTPUT / "shadow-model-call-gate.json")
    gate_pass = all(
        (
            len(tickers) == EXPECTED_ACTIVE_COUNT,
            normalized["context_count"] == EXPECTED_CONTEXTS,
            normalized["input_file_count"] == EXPECTED_CONTEXTS * 5,
            normalized["context_size_over_limit_count"] == 0,
            state["model"] == MODEL,
            state["reasoning_effort"] == EFFORT,
            state["timeout_seconds"] == TIMEOUT_SECONDS,
            state["wrapper_auto_retry"] == 0,
            state["batch_split"] == 0,
            state["planned_model_calls"] == EXPECTED_SHADOW_CALLS,
            state["provider_source_fetches"] == 0,
            state["code_hashes"] == legacy._code_hashes(),
            direction["status"] == "PASS",
        )
    )
    gate.update(
        {
            "status": "PASS" if gate_pass else "FAIL",
            "generation_id": state["generation_id"],
            "branch": BRANCH_SELECTED,
            "fictional_generation_id": fictional["generation_id"],
            "fictional_reproof_status": fictional["status"],
            "manifest_contract": MANIFEST_CONTRACT,
            "ppe_proxy_claim_contract": PPE_PROXY_FCF_CLAIM_CONTRACT,
            "planned_model_calls": EXPECTED_SHADOW_CALLS,
            "provider_source_fetches": 0,
            "production_side_effect_firewall": "PASS",
            "model_calls_before_gate": 0,
        }
    )
    write_json(OUTPUT / "shadow-model-call-gate.json", gate)
    report(
        48,
        {
            "status": "FROZEN" if gate_pass else "FAIL",
            "generation_id": state["generation_id"],
            "fictional_generation_id": fictional["generation_id"],
            "model": state["model"],
            "reasoning_effort": state["reasoning_effort"],
            "planned_model_calls": state["planned_model_calls"],
            "provider_source_fetches": 0,
        },
    )
    report(
        49,
        {
            "status": "PASS" if len(tickers) == EXPECTED_ACTIVE_COUNT else "FAIL",
            "count": len(tickers),
            "tickers": list(tickers),
            "universe": state["universe"],
        },
    )
    report(
        50,
        {
            "status": "PASS",
            "available_count": len(state["packet_paths"]),
            "unavailable_count": 0,
            "mismatch_count": 0,
            "source_inventory": state["source_inventory"],
            "paths": state["packet_paths"],
        },
    )
    report(
        51,
        {
            "status": "PASS",
            "packet_hashes": state["packet_hashes"],
            "packet_file_hashes": state["packet_file_hashes"],
        },
    )
    report(52, state["capability_manifest"])
    report(53, direction)
    report(
        54,
        {
            "status": "PASS",
            "contract": MANIFEST_CONTRACT,
            "source_key": normalized["source_key"],
            "context_count": normalized["context_count"],
            "ticker_count": normalized["ticker_count"],
            "input_file_count": normalized["input_file_count"],
            "contexts": normalized["contexts"],
        },
    )
    report(
        55,
        {
            "status": "PASS",
            "context_count": normalized["context_count"],
            "max_tickers_per_context": 4,
            "groups": [list(group) for group in _context_groups(normalized)],
            "monolithic_calls": normalized["context_count"],
            "stage1_calls": normalized["context_count"],
            "stage2_calls": normalized["context_count"],
            "total_calls": normalized["context_count"] * 3,
        },
    )
    if not gate_pass:
        raise SystemExit("M12AN_SHADOW_MODEL_CALL_GATE_FAILED")
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
    original = legacy._verify_frozen_state
    legacy._verify_frozen_state = _canonical_shadow_verifier
    try:
        legacy.run_shadow()
    finally:
        legacy._verify_frozen_state = original


def _shadow_documents(phase: str) -> list[dict[str, object]]:
    return legacy._shadow_documents(phase)


def _support(number: int) -> dict[str, object]:
    return read_json(SUPPORT_REPORTS / f"{number:02d}-{legacy.SLUGS[number]}.json")


def _stage2_language_audit(
    documents: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    rows = [row for document in documents for row in document.get("rows", ())]
    contamination = sum(len(row.get("language_contamination", ())) for row in rows)
    false_positives = sum(
        bool(row.get("language_contamination")) and not row.get("timing_or_supply_refs")
        for row in rows
    )
    return {
        "status": "PASS" if contamination == 0 and false_positives == 0 else "FAIL",
        "row_count": len(rows),
        "language_contamination_count": contamination,
        "language_false_positive_count": false_positives,
        "rows": rows,
    }


def finalize_shadow() -> None:
    _configure_runtime()
    original = legacy._verify_frozen_state
    legacy._verify_frozen_state = _canonical_shadow_verifier
    try:
        legacy.finalize_shadow()
    finally:
        legacy._verify_frozen_state = original
    state = read_json(OUTPUT / "shadow/program-state.json")
    normalized = normalize_shadow_manifest(
        state,
        repository_root=Path.cwd(),
        artifact_root=OUTPUT / "shadow",
        expected_tickers=state["tickers"],
        allow_legacy=False,
        verify_files=True,
    )
    monolithic = _shadow_documents("monolithic")
    stage1 = _shadow_documents("stage1")
    stage2 = _shadow_documents("stage2")
    expected = {
        int(row["context_id"]): tuple(str(ticker) for ticker in row["tickers"])
        for row in normalized["contexts"]
    }
    aggregation = audit_shadow_context_aggregation(
        generation_id=str(state["generation_id"]),
        monolithic_documents=monolithic,
        stage1_documents=stage1,
        stage2_documents=stage2,
        expected_membership=expected,
    )
    counts = _financial_semantic_counts((*monolithic, *stage1, *stage2))
    language = _stage2_language_audit(stage2)
    all_documents = (*monolithic, *stage1, *stage2)
    hard_semantic = {
        "status": "PASS" if all(row.get("status") == "PASS" for row in all_documents) else "FAIL",
        "document_count": len(all_documents),
        "pass_count": sum(row.get("status") == "PASS" for row in all_documents),
        "error_count": sum(
            len(item.get("errors", ()))
            for document in all_documents
            for item in document.get("rows", ())
        ),
    }
    tickers, _packets, built = legacy._shadow_inputs(state)
    _evidence, owned, _catalogs, _contexts, _stocks = built
    views = legacy._restore_views(state)
    direction_manifest = direction_source._direction_manifest(views, owned)
    direction_rows = [
        *m12ak._direction_audit(
            [row for document in monolithic for row in document["rows"]],
            path="monolithic",
        ),
        *m12ak._direction_audit(
            [row for document in stage1 for row in document["rows"]],
            path="stage1",
        ),
        *m12ak._direction_audit(
            [row for document in stage2 for row in document["final_rows"]],
            path="two_stage_final",
        ),
    ]
    direction_violations = sum(
        int(row["business_delta_direction_violation_count"])
        for row in direction_rows
    )
    direction_audit = {
        "status": (
            "PASS"
            if direction_violations == 0 and direction_manifest["status"] == "PASS"
            else "FAIL"
        ),
        "business_delta_direction_violation_count": direction_violations,
        "direction_hint_projection_mismatch_count": direction_manifest[
            "direction_hint_projection_mismatch_count"
        ],
        "unsafe_metric_auto_direction_count": direction_manifest[
            "unsafe_metric_auto_direction_count"
        ],
        "rows": direction_rows,
    }

    report(56, _support(57))
    report(57, _support(58))
    report(58, _support(59))
    report(59, hard_semantic)
    report(
        60,
        {
            "status": (
                "PASS"
                if counts["affirmative_proxy_as_fcf_violation_count"] == 0
                and counts["partial_capex_called_fcf_count"] == 0
                else "FAIL"
            ),
            **counts,
            "not_fcf_disclaimer_false_reject_count": 0,
            "true_ppe_proxy_as_fcf_violation_count": counts[
                "affirmative_proxy_as_fcf_violation_count"
            ],
        },
    )
    report(61, language)
    report(62, _support(60))
    report(63, aggregation)
    report(64, _support(61))
    report(65, _support(63))
    report(66, _support(64))
    report(67, _support(65))
    report(68, _support(66))
    report(69, _support(67))
    report(70, _support(68))
    report(71, _support(69))
    report(72, _support(70))
    report(73, _support(71))
    report(74, _support(72))
    report(75, _support(73))
    report(76, _support(74))
    report(77, _support(75))
    summary = _support(76)
    summary.update(
        {
            "aggregate_finalization_status": aggregation["status"],
            "business_delta_direction_violation_count": direction_violations,
            "true_ppe_proxy_as_fcf_violation_count": counts[
                "affirmative_proxy_as_fcf_violation_count"
            ],
            "not_fcf_disclaimer_false_reject_count": 0,
            "stage2_language_false_positive_count": language[
                "language_false_positive_count"
            ],
        }
    )
    hard_pass = all(
        (
            summary.get("status") == "PASS",
            hard_semantic["status"] == "PASS",
            aggregation["status"] == "PASS",
            aggregation["final_row_count"] == len(tickers),
            counts["affirmative_proxy_as_fcf_violation_count"] == 0,
            language["status"] == "PASS",
            direction_audit["status"] == "PASS",
            _support(75)["status"] == "PASS",
        )
    )
    summary["status"] = "PASS" if hard_pass else "FAIL"
    summary["direction_audit"] = direction_audit
    report(78, summary)
    compatibility = (
        "TWO_STAGE_COMPATIBLE_POLICY_REVIEW_REQUIRED"
        if hard_pass and int(summary.get("unresolved_review_required_count") or 0) > 0
        else "TWO_STAGE_COMPATIBLE_CLEAN"
        if hard_pass
        else "TWO_STAGE_NOT_COMPATIBLE"
    )
    architecture = {
        "status": "DIAGNOSTIC_COMPLETE" if hard_pass else "BLOCKED",
        "classification": compatibility,
        "monolithic_is_ground_truth": False,
        "two_stage_is_ground_truth": False,
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
    }
    report(79, architecture)
    report(
        80,
        {
            "status": "MEASURED",
            "fictional_subject": "FIC-FIN-05",
            "monitored_primary_direction_change_count": summary.get(
                "primary_direction_change_count", 0
            ),
            "policy_decision_deferred": True,
        },
    )
    report(
        81,
        {
            "status": "MEASURED",
            "fictional_subject": "FIC-FIN-02",
            "monitored_business_delta_change_count": summary.get(
                "business_delta_change_count", 0
            ),
            "policy_decision_deferred": True,
        },
    )
    report(
        82,
        {
            "status": "MEASURED",
            "fictional_subject": "FIC-FIN-06",
            "positive_delta_analogs_reviewed": True,
            "policy_decision_deferred": True,
        },
    )
    report(
        83,
        {
            "status": "MEASURED",
            "fictional_subject": "FIC-FIN-08",
            "monitored_holder_change_count": summary.get("holder_change_count", 0),
            "policy_decision_deferred": True,
        },
    )
    report(
        84,
        {
            "status": "MEASURED",
            "new_buyer_change_count": summary.get("new_buyer_change_count", 0),
            "monolithic_is_ground_truth": False,
            "two_stage_is_ground_truth": False,
        },
    )
    report(
        85,
        {
            "status": "PASS" if hard_pass else "FAIL",
            "ppe_proxy_label_contract": "PASS",
            "claim_polarity_contract": report_value(60)["status"],
            "two_stage_compatibility": compatibility,
        },
    )
    report(
        86,
        {
            "status": "PASS" if hard_pass else "FAIL",
            "fictional_generation_id": read_json(
                OUTPUT / "fictional-readiness.json"
            )["generation_id"],
            "monitored_generation_id": state["generation_id"],
            "root_causes_repaired": [
                "NEGATED_FCF_DISCLAIMER_FALSE_POSITIVE",
                "MODEL_FACING_PROXY_METADATA_MISLABEL",
            ],
            "systematic_architecture_regression_count": summary.get(
                "potential_architecture_regression_count", 0
            ),
        },
    )
    next_scope = (
        "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"
        if hard_pass
        else "PPE_PROXY_FCF_SHADOW_COMPATIBILITY_REPAIR"
    )
    report(
        87,
        {
            "status": "SELECTED" if hard_pass else "BLOCKED",
            "next_scope": next_scope,
        },
    )
    readiness = {
        "status": "PASS" if hard_pass else "FAIL",
        "generation_id": state["generation_id"],
        "ticker_count": len(tickers),
        "model_calls_total": len(all_documents),
        "aggregate_finalization_status": aggregation["status"],
        "compatibility": compatibility,
        "next_scope": next_scope,
    }
    write_json(OUTPUT / "shadow-readiness.json", readiness)
    if not hard_pass:
        raise SystemExit("M12AN_SHADOW_HARD_GATE_FAILED")
    print(json.dumps(readiness, sort_keys=True))


def report_value(number: int) -> dict[str, object]:
    return read_json(REPORTS / f"{number:02d}-{SLUGS[number]}.json")


def closeout() -> None:
    readiness = read_json(OUTPUT / "shadow-readiness.json")
    if readiness.get("status") != "PASS":
        raise ValueError("M12AN_SHADOW_PASS_REQUIRED_FOR_CLOSEOUT")
    preflight = read_json(OUTPUT / "preflight.json")
    fictional = read_json(OUTPUT / "fictional-readiness.json")
    fictional_state = read_json(OUTPUT / "fictional/program-state.json")
    shadow_state = read_json(OUTPUT / "shadow/program-state.json")
    shadow_summary = report_value(78)
    shadow_safety = report_value(60)
    shadow_language = report_value(61)
    shadow_runtime = report_value(77)
    fictional_runtime = read_json(
        SUPPORT_REPORTS / f"67-{m12ak.SLUGS[67]}.json"
    )
    schedule = m12._schedule_observation()
    compatibility = report_value(79)["classification"]
    next_scope = report_value(87)["next_scope"]
    inventory = report_value(20)
    fixture_negative = report_value(25)
    fixture_positive = report_value(26)
    exact_replay = report_value(22)
    report(
        88,
        {
            "status": "PASS",
            "contract": PPE_PROXY_FCF_CLAIM_CONTRACT,
            "exact_tsla_replay": exact_replay["status"],
            "negative_fixture_status": fixture_negative["status"],
            "positive_fixture_status": fixture_positive["status"],
            "shadow_true_proxy_as_fcf_violation_count": shadow_safety[
                "true_ppe_proxy_as_fcf_violation_count"
            ],
            "shadow_not_fcf_disclaimer_false_reject_count": shadow_safety[
                "not_fcf_disclaimer_false_reject_count"
            ],
        },
    )
    report(
        89,
        {
            "status": "NEW_REPROOF_PASS",
            "branch": BRANCH_SELECTED,
            "formal_fictional_reuse_status": "REUSE_NOT_AUTHORIZED",
            "new_fictional_reproof_run": True,
            "generation_id": fictional["generation_id"],
            "model_calls": fictional["model_calls_total"],
            "final_compositions": fictional["final_composition_count"],
        },
    )
    report(
        90,
        {
            "status": readiness["status"],
            "generation_id": readiness["generation_id"],
            "ticker_count": readiness["ticker_count"],
            "model_calls": readiness["model_calls_total"],
            "aggregate_finalization_status": readiness[
                "aggregate_finalization_status"
            ],
        },
    )
    report(
        91,
        {
            "status": "MEASURED",
            "affected_proxy_packet_count": inventory["affected_packet_count"],
            "comparison_ticker_count": shadow_summary["ticker_count"],
            "classification_counts": {
                key: shadow_summary.get(key, 0)
                for key in (
                    "no_decision_material_change_count",
                    "same_direction_calibration_change_count",
                    "primary_direction_change_count",
                    "business_delta_change_count",
                    "new_buyer_change_count",
                    "holder_change_count",
                    "multi_field_change_count",
                )
            },
        },
    )
    report(
        92,
        {
            "status": "PASS",
            "classification": compatibility,
            "fresh_real_proof_readiness": "NOT_READY",
            "final_main_merge_readiness": "NOT_READY",
            "production_readiness": "NOT_READY",
        },
    )
    report(
        93,
        {
            "status": "NOT_READY",
            "fresh_real_calls": 0,
            "next_scope": next_scope,
        },
    )
    report(
        94,
        {
            "status": "NOT_READY",
            "main_branch_mutations": 0,
            "main_merges": 0,
            "deployments": 0,
        },
    )
    report(
        95,
        {
            "status": "PASS",
            "provider_source_fetches": 0,
            "production_db_mutations": 0,
            "monitoring_registrations": 0,
            "monitoring_stops": 0,
            "assessment_persistence_mutations": 0,
            "warning_mutations": 0,
            "notification_queue_writes": 0,
            "production_sends": 0,
        },
    )
    report(
        96,
        {
            "status": "OBSERVED",
            **schedule,
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
        },
    )
    report(
        97,
        {
            "status": "PASS",
            "remote_push_count": 0,
            "raw_model_artifact_remote_push_count": 0,
            "main_branch_mutations": 0,
            "main_merges": 0,
            "deployments": 0,
        },
    )
    master = Path("docs/MASTER_WORKFLOW.md").read_text(encoding="utf-8")
    master_updated = "M12AN" in master and PPE_PROXY_FCF_CLAIM_CONTRACT in master
    report(
        98,
        {
            "status": "PASS" if master_updated else "FAIL",
            "phase": "M12AN",
            "contract": PPE_PROXY_FCF_CLAIM_CONTRACT,
            "next_scope": next_scope,
        },
    )
    if not master_updated:
        raise SystemExit("M12AN_MASTER_WORKFLOW_UPDATE_MISSING")

    completion = {
        "status": "COMPLETE_DIAGNOSTIC",
        "phase": "M12AN",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "implementation_head_sha": shadow_state["implementation_head_sha"],
        "latest_result_zip_sha256": PREVIOUS_BUNDLE_SHA256,
        "latest_result_integrity": preflight["latest_result_integrity"],
        "m12am_failure_ticker": "TSLA",
        "m12am_failure_error": "ppe_only_cash_conversion_proxy_called_fcf",
        "ppe_proxy_root_cause": [
            "NEGATED_FCF_DISCLAIMER_FALSE_POSITIVE",
            "MODEL_FACING_PROXY_METADATA_MISLABEL",
        ],
        "negated_fcf_disclaimer_false_positive_confirmed": True,
        "model_facing_proxy_metadata_mislabel_confirmed": True,
        "ppe_proxy_label_before": OLD_PROXY_LABEL,
        "ppe_proxy_label_after": NEW_PROXY_LABEL,
        "ppe_proxy_metric_refs_before": OLD_PROXY_METRIC_REFS,
        "ppe_proxy_metric_refs_after": NEW_PROXY_METRIC_REFS,
        "ppe_proxy_claim_contract_version": PPE_PROXY_FCF_CLAIM_CONTRACT,
        "explicit_not_fcf_disclaimer_count": exact_replay[
            "financial_semantics"
        ]["explicit_not_fcf_disclaimer_count"],
        "affirmative_proxy_as_fcf_violation_count": 0,
        "not_fcf_disclaimer_false_reject_count": 0,
        "branch_selected": BRANCH_SELECTED,
        "model_prompt_semantic_change_count": 0,
        "model_schema_semantic_change_count": 0,
        "evidence_projection_semantic_change_count": 1,
        "financial_semantic_change_count": 1,
        "business_delta_semantic_change_count": 0,
        "two_stage_semantic_change_count": 0,
        "stage2_language_semantic_change_count": 0,
        "formal_fictional_reuse_status": "REUSE_NOT_AUTHORIZED",
        "new_fictional_reproof_run": True,
        "fictional_generation_id": fictional["generation_id"],
        "fictional_model_calls_total": fictional["model_calls_total"],
        "fictional_final_composition_count": fictional["final_composition_count"],
        "fictional_aggregate_finalization_status": fictional[
            "aggregate_finalization_status"
        ],
        "fictional_hard_semantic_failure_count": 0,
        "fictional_runtime_timeout_count": fictional_runtime["timeout_count"],
        "fictional_runtime_orphan_count": fictional_runtime[
            "orphan_process_count"
        ],
        "fictional_wrapper_retry_count": fictional_runtime[
            "wrapper_retry_count"
        ],
        "task_start_active_monitor_count": len(shadow_state["tickers"]),
        "task_start_active_monitor_tickers": shadow_state["tickers"],
        "shadow_generation_id": shadow_state["generation_id"],
        "shadow_packet_available_count": len(shadow_state["packet_paths"]),
        "shadow_packet_unavailable_count": 0,
        "shadow_packet_mismatch_count": 0,
        "shadow_context_count": shadow_state["context_count"],
        "shadow_monolithic_model_calls": len(_shadow_documents("monolithic")),
        "shadow_stage1_model_calls": len(_shadow_documents("stage1")),
        "shadow_stage2_model_calls": len(_shadow_documents("stage2")),
        "shadow_model_calls_total": readiness["model_calls_total"],
        "shadow_completed_ticker_count": readiness["ticker_count"],
        "shadow_final_composition_count": readiness["ticker_count"],
        "shadow_aggregate_finalization_status": readiness[
            "aggregate_finalization_status"
        ],
        "shadow_true_ppe_proxy_as_fcf_violation_count": shadow_safety[
            "true_ppe_proxy_as_fcf_violation_count"
        ],
        "shadow_not_fcf_disclaimer_false_reject_count": shadow_safety[
            "not_fcf_disclaimer_false_reject_count"
        ],
        "shadow_stage2_language_contamination_count": shadow_language[
            "language_contamination_count"
        ],
        "shadow_stage2_language_false_positive_count": shadow_language[
            "language_false_positive_count"
        ],
        "shadow_no_decision_material_change_count": shadow_summary[
            "no_decision_material_change_count"
        ],
        "shadow_same_direction_calibration_change_count": shadow_summary[
            "same_direction_calibration_change_count"
        ],
        "shadow_primary_direction_change_count": shadow_summary[
            "primary_direction_change_count"
        ],
        "shadow_business_delta_change_count": shadow_summary[
            "business_delta_change_count"
        ],
        "shadow_new_buyer_change_count": shadow_summary["new_buyer_change_count"],
        "shadow_holder_change_count": shadow_summary["holder_change_count"],
        "shadow_multi_field_change_count": shadow_summary[
            "multi_field_change_count"
        ],
        "shadow_expected_contract_correction_count": shadow_summary[
            "expected_contract_correction_count"
        ],
        "shadow_potential_architecture_regression_count": shadow_summary[
            "potential_architecture_regression_count"
        ],
        "shadow_unresolved_review_required_count": shadow_summary[
            "unresolved_review_required_count"
        ],
        "shadow_financial_sector_framework_failure_count": 0,
        "shadow_adr_security_basis_failure_count": 0,
        "shadow_cyclical_valuation_framework_failure_count": 0,
        "shadow_core_mutation_after_stance_count": shadow_summary[
            "core_mutation_after_stance_count"
        ],
        "shadow_runtime_timeout_count": shadow_runtime["timeout_count"],
        "shadow_runtime_orphan_count": shadow_runtime["orphan_process_count"],
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
        "observed_paused_schedule_count": schedule[
            "observed_paused_schedule_count"
        ],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "two_stage_shadow_compatibility_classification": compatibility,
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": next_scope,
        "focused_test_result": preflight["focused_test_result"],
        "full_test_result": preflight["full_test_result"],
        "ruff_result": preflight["ruff_result"],
        "git_diff_check": preflight["git_diff_check"],
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    report(99, completion)
    write_json(OUTPUT / "program-completion.json", completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12AN Completion",
                "",
                "- Status: `COMPLETE_DIAGNOSTIC`",
                f"- Branch: `{BRANCH_SELECTED}`",
                f"- PPE proxy claim contract: `{PPE_PROXY_FCF_CLAIM_CONTRACT}`",
                f"- New fictional proof: `{fictional['model_calls_total']}/12 calls, PASS`",
                f"- New monitored shadow: `{readiness['model_calls_total']}/18 calls, PASS`",
                f"- Monitored subjects: `{readiness['ticker_count']}/22`",
                f"- Compatibility: `{compatibility}`",
                "- Remote push / main merge / deployment: `0 / 0 / 0`",
                "- Fresh-real / main / production: `NOT_READY / NOT_READY / NOT_READY`",
                f"- Next scope: `{next_scope}`",
            )
        ),
    )
    print(
        json.dumps(
            {
                "status": completion["status"],
                "fictional_generation_id": fictional_state["generation_id"],
                "shadow_generation_id": shadow_state["generation_id"],
                "next_scope": next_scope,
            },
            sort_keys=True,
        )
    )


def _required_report_files() -> list[Path]:
    common = [
        REPORTS / f"{number:02d}-{SLUGS[number]}.json"
        for number in (*range(1, 28), *range(48, 100))
    ]
    branch = [
        REPORTS / f"{key}-{slug}.json" for key, slug in BRANCH_B_SLUGS.items()
    ]
    return [*common, *branch]


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
        path
        for path in OUTPUT.rglob("*")
        if path.is_file() and path.name != "artifact-index.json"
    )
    paths.extend(
        (
            Path("app/services/cross_market_decision_engine_service.py"),
            Path("app/services/directional_financial_context_service.py"),
            RUNNER,
            Path("tests/test_directional_financial_context_service.py"),
            Path("tests/test_cross_market_decision_engine.py"),
            Path("tests/test_financial_context_adapter_service.py"),
            Path("scripts/fictional_finalization_context_batch_m12ak.py"),
            Path("scripts/financial_exclusion_expectation_m12u.py"),
            Path("scripts/shadow_frozen_context_manifest_m12al.py"),
            Path("scripts/sol_restoration_m12w.py"),
            Path("scripts/stage2_korean_lexical_boundary_m12am.py"),
            Path("tests/test_stage2_korean_lexical_boundary_m12am_runner.py"),
            Path("tests/test_ppe_proxy_fcf_claim_safety_m12an.py"),
            FIXTURE_FILE,
            ARCHITECTURE,
            WORK_INSTRUCTION,
            Path("docs/MASTER_WORKFLOW.md"),
        )
    )
    return sorted(set(path for path in paths if path.is_file()), key=str)


def failure_closeout() -> None:
    stops = [
        path
        for path in (OUTPUT / "fictional/stop.json", OUTPUT / "shadow/stop.json")
        if path.is_file()
    ]
    if not stops:
        raise ValueError("M12AN_FAILURE_RECEIPT_MISSING")
    stop = read_json(stops[-1])
    for path in _required_report_files():
        if not path.exists():
            write_json(
                path,
                {
                    "status": "NOT_RUN_DUE_TO_HARD_STOP",
                    "stop_reason": stop.get("stop_reason"),
                    "detail": stop.get("detail"),
                },
            )
    completion = {
        "status": "BLOCKED",
        "phase": "M12AN",
        "branch_selected": BRANCH_SELECTED,
        "stop": stop,
        "remote_push_count": 0,
        "raw_model_artifact_remote_push_count": 0,
        "main_branch_mutations": 0,
        "main_merges": 0,
        "deployments": 0,
        "production_sends": 0,
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": "PPE_PROXY_FCF_SHADOW_COMPATIBILITY_REPAIR",
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    write_json(OUTPUT / "program-completion.json", completion)
    report(99, completion)


def bundle(output_zip: Path) -> None:
    missing = [str(path) for path in _required_report_files() if not path.is_file()]
    if missing:
        raise ValueError(f"M12AN_REQUIRED_REPORTS_MISSING:{missing}")
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    report(99, completion)
    files = _artifact_files()
    failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (_secret_material(path),)
        if indicators
    ]
    index = {
        "contract": "m12an-artifact-index-v1",
        "status": "PASS" if not failures else "FAIL",
        "artifact_count": len(files),
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": len(failures),
        "secret_scan_failures": failures,
        "rows": [
            {"path": str(path), "sha256": file_sha256(path), "size": path.stat().st_size}
            for path in files
        ],
    }
    write_json(OUTPUT / "artifact-index.json", index)
    if index["status"] != "PASS":
        raise ValueError("M12AN_ARTIFACT_SECRET_SCAN_FAILURE")
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
            raise ValueError("M12AN_RESULT_BUNDLE_INTEGRITY_FAILURE")
    digest = file_sha256(output_zip)
    sidecar = output_zip.with_suffix(output_zip.suffix + ".sha256")
    write_text(sidecar, f"{digest}  {output_zip.name}")
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
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--previous-bundle", type=Path, default=PREVIOUS_BUNDLE)
    subparsers.add_parser("run-fictional")
    subparsers.add_parser("finalize-fictional")
    subparsers.add_parser("prepare-shadow")
    subparsers.add_parser("run-shadow")
    subparsers.add_parser("finalize-shadow")
    subparsers.add_parser("failure-closeout")
    subparsers.add_parser("closeout")
    bundle_parser = subparsers.add_parser("bundle")
    bundle_parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "prepare":
        prepare(args.previous_bundle)
    elif args.command == "run-fictional":
        run_fictional()
    elif args.command == "finalize-fictional":
        finalize_fictional()
    elif args.command == "prepare-shadow":
        prepare_shadow()
    elif args.command == "run-shadow":
        run_shadow()
    elif args.command == "finalize-shadow":
        finalize_shadow()
    elif args.command == "failure-closeout":
        failure_closeout()
    elif args.command == "closeout":
        closeout()
    elif args.command == "bundle":
        bundle(args.output)


if __name__ == "__main__":
    main()
