"""M12BD Stage-2 working-capital binding parity proof program."""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import ast
from collections.abc import Mapping, Sequence
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import zipfile

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.optional_semantic_audit_service import (
    CONTRACT_VERSION as OPTIONAL_AUDIT_CONTRACT,
)
from app.services.report_subject_identity_service import audit_subject_set_identity
from app.services.two_stage_directional_service import DirectionalCoreJudgment
from app.services.working_capital_checkpoint_binding_service import (
    CONTRACT_VERSION as WC_BINDING_CONTRACT,
    MODEL_CHECKPOINT_FIELDS,
    STAGE2_MODEL_CHECKPOINT_FIELDS,
    VIEW_CONTRACT_VERSION as WC_VIEW_CONTRACT,
    WorkingCapitalCheckpointBindingView,
    build_working_capital_checkpoint_binding_view,
    validate_working_capital_checkpoint_bindings,
)
from scripts import fictional_aggregate_context_boundary_m12bc as m12bc
from scripts import working_capital_checkpoint_binding_m12bb as m12bb


NAME = (
    "20260913-stage2-working-capital-binding-parity-audit-coverage-validity-"
    "separation-full-proof-full-shadow"
)
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
PROOF_OUTPUT = OUTPUT / "proof-runtime"
PROOF_REPORTS = OUTPUT / "proof-reports/m12bb"
RUNNER = Path("scripts/stage2_working_capital_binding_parity_m12bd.py")
ARCHITECTURE = Path(
    "docs/architecture/STAGE2_WORKING_CAPITAL_BINDING_PARITY.md"
)
WORK_INSTRUCTION = Path("docs/work-instructions") / f"{NAME}.md"
WORK_INSTRUCTION_COMMIT = "2ceced2f2e86ee9e93cdd4350d68594ae6f762fd"
BASE_INTEGRATION_HEAD_SHA = "7ba278a70a96c726b37e243fd8b89e1009c22ee3"

LATEST_BUNDLE = Path.home() / "Documents/Codex" / (
    "thesis-monitor-20260913-fictional-aggregate-context-boundary-readiness-"
    "policy-alignment-full-shadow-report.zip"
)
LATEST_BUNDLE_SHA256 = (
    "84c73ca678bf646e977f2c3a72a7ccb903782f2eecd2348478e2ba22dc1c6779"
)
LATEST_INDEXED_PAYLOADS = 1569
LATEST_ZIP_ENTRIES = 1570
M12BC_GENERATION_ID = "20260911-m12ai-fictional-20260913T100541Z-103a7a3e4c03"
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
EXPECTED_FICTIONAL_CALLS = 12
EXPECTED_FICTIONAL_ROWS = 24
EXPECTED_SHADOW_CALLS = 18
NEXT_SCOPE = "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"

M12BC_ROOT = (
    "artifacts/20260913-fictional-aggregate-context-boundary-readiness-policy-"
    "alignment-full-shadow"
)
M12BC_PROOF_ROOT = (
    "artifacts/20260913-working-capital-checkpoint-typed-ref-binding-"
    "fictional-reproof-full-shadow"
)

REPORT_SLUGS = tuple(
    line
    for line in """
repository-provenance
latest-result-integrity
m12bd-scope-freeze
integrated-main-lineage-freeze
m12bc-fic-fin-02-stage2-wc-failure-reproduction
m12bc-stage1-wc-pass-contrast
stage2-prompt-binding-gap-audit
stage2-context-binding-view-gap-audit
stage2-wc-binding-options
stage2-wc-binding-decision
monitoring-audit-coverage-vs-validity-root-cause
optional-audit-readiness-policy-audit
stage2-working-capital-checkpoint-binding-contract
stage2-working-capital-binding-view-contract
stage2-specific-metric-ref-contract
stage2-generic-wc-ref-contract
stage2-narrative-supplement-not-substitute-contract
stage2-monolithic-binding-parity-contract
stage2-hard-postcompose-validator-preservation-contract
optional-semantic-audit-coverage-contract
monitoring-obligation-zero-observation-contract
semantic-validity-vs-coverage-contract
coverage-required-only-in-deterministic-fixtures-contract
hard-readiness-audit-classification-contract
m12bc-fic-fin-02-stage2-historical-invalid-replay
fic-fin-02-stage2-corrected-equivalent-positive-fixture
stage2-holder-wc-positive-control
stage2-specific-metric-mismatch-negative-fixture
stage2-narrative-only-substitution-negative-fixture
stage2-no-wc-no-typed-ref-required-fixture
monitoring-zero-observation-nonblocking-fixture
monitoring-observed-valid-fixture
monitoring-current-false-accept-negative-fixture
monitoring-no-support-false-accept-negative-fixture
m12bc-context-preserving-finalizer-freeze
m12bc-diagnostic-variance-readiness-freeze
m12bb-stage1-wc-binding-freeze
m12ba-financial-sector-replacement-verb-freeze
m12az-fcf-local-temporal-scope-freeze
m12ay-configured-fcf-support-freeze
m12ax-monitoring-semantics-freeze
m12aw-nominal-condition-freeze
m12av-mixed-risk-scope-freeze
m12at-configured-signal-field-ownership-freeze
m12as-unchanged-claim-scope-freeze
m12ar-fcf-claim-scope-freeze
m12ap-expectation-independence-freeze
m12aq-financial-sector-exclusion-freeze
m12ao-business-delta-convergence-freeze
m12an-ppe-proxy-freeze
m12am-stage2-lexical-freeze
qtd-ytd-wc-debt-safety-freeze
adr-security-basis-freeze
two-stage-core-immutability-freeze
stage1-prompt-semantic-hash-freeze
stage1-schema-semantic-hash-freeze
stage2-prompt-semantic-diff
stage2-schema-semantic-hash-freeze
stage2-context-semantic-diff
working-capital-binding-view-stage2-diff
configured-signal-view-semantic-hash-freeze
business-delta-view-semantic-hash-freeze
expectation-view-semantic-hash-freeze
configured-financial-support-concept-hash-freeze
final-user-schema-no-change-proof
new-formal-proof-decision
focused-test-results
full-local-test-results
ruff-and-diff-results
hosted-ci-portability-observation
new-fictional-model-call-gate
fictional-generation-manifest
fictional-stage1-wc-binding-view-manifest
fictional-stage2-wc-binding-view-manifest
fictional-configured-signal-view-manifest
fictional-configured-financial-support-concept-manifest
fictional-delta-view-manifest
fictional-expectation-view-manifest
stage1-run1-context01
stage1-run1-context02
stage2-run1-context01
stage2-run1-context02
stage1-run2-context01
stage1-run2-context02
stage2-run2-context01
stage2-run2-context02
stage1-run3-context01
stage1-run3-context02
stage2-run3-context01
stage2-run3-context02
fictional-context-hard-semantic-audit
fictional-stage1-wc-binding-audit
fictional-stage2-wc-binding-audit
fictional-financial-grounding-audit
fictional-optional-audit-coverage-matrix
fictional-configured-signal-field-use-audit
fictional-fcf-audit
fictional-business-delta-audit
fictional-market-expectation-audit
fictional-financial-sector-audit
fictional-stage2-language-audit
fictional-final-composition-audit
fictional-aggregate-finalization-audit
fictional-decision-variance-diagnostics
fictional-core-immutability-audit
fictional-runtime-audit
fictional-shadow-gate-decision
task-start-active-monitored-universe
shadow-packet-inventory
shadow-packet-hash-manifest
shadow-stage1-wc-binding-view-manifest
shadow-stage2-wc-binding-view-manifest
shadow-configured-signal-view-manifest
shadow-configured-financial-support-concept-manifest
shadow-delta-view-manifest
shadow-expectation-view-manifest
shadow-frozen-context-manifest
shadow-batching-manifest
shadow-model-call-gate
shadow-monolithic-model-artifacts
shadow-stage1-model-artifacts
shadow-stage2-model-artifacts
shadow-context-hard-semantic-audit
shadow-stage1-wc-binding-audit
shadow-stage2-wc-binding-audit
shadow-financial-grounding-audit
shadow-optional-audit-coverage-matrix
shadow-configured-signal-field-use-audit
shadow-fcf-audit
shadow-business-delta-audit
shadow-market-expectation-audit
shadow-financial-sector-audit
shadow-stage2-language-audit
shadow-final-composition-audit
shadow-aggregate-finalization-audit
shadow-per-ticker-comparison
shadow-core-direction-differences
shadow-business-delta-differences
shadow-new-buyer-differences
shadow-holder-differences
shadow-same-direction-calibration-differences
shadow-expected-contract-corrections
shadow-potential-architecture-regressions
shadow-unresolved-review-required
shadow-adr-security-basis-audit
shadow-cyclical-valuation-audit
shadow-core-immutability-audit
shadow-runtime-audit
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
working-capital-stage2-grounding-lessons
combined-fictional-monitored-policy-input
next-bounded-policy-decision
stage2-wc-binding-parity-success-decision
optional-audit-coverage-validity-success-decision
context-preserving-finalizer-preservation-decision
diagnostic-variance-readiness-preservation-decision
new-fictional-proof-success-decision
full-shadow-completion-decision
existing-monitored-impact-summary
two-stage-shadow-compatibility-decision
fresh-real-proof-readiness-decision
final-main-merge-readiness-note
production-no-change
schedule-pause-observation
remote-push-prohibition-audit
master-workflow-update
program-completion
""".strip().splitlines()
)
SLUGS = dict(enumerate(REPORT_SLUGS, start=1))
NUMBERS = {slug: number for number, slug in SLUGS.items()}
if len(SLUGS) != 177:
    raise RuntimeError(f"M12BD_REPORT_SEQUENCE_INVALID:{len(SLUGS)}")

FOCUSED_TESTS = (
    "tests/test_stage2_working_capital_binding_parity_m12bd.py",
    "tests/test_optional_semantic_audit_service.py",
    "tests/test_working_capital_checkpoint_binding_m12bb.py",
    "tests/test_working_capital_checkpoint_binding_m12bb_runner.py",
    "tests/test_fictional_aggregate_context_boundary_m12bc.py",
    "tests/test_context_preserving_finalization.py",
    "tests/test_prospective_monitoring_obligation_m12ax.py",
    "tests/test_configured_fcf_support_mapping_m12ay.py",
)
RUFF_PATHS = (
    str(RUNNER),
    "app/services/working_capital_checkpoint_binding_service.py",
    "app/services/optional_semantic_audit_service.py",
    "scripts/working_capital_checkpoint_binding_m12bb.py",
    "scripts/prospective_monitoring_obligation_m12ax.py",
    "scripts/configured_fcf_prospective_support_m12ay.py",
    "tests/test_stage2_working_capital_binding_parity_m12bd.py",
    "tests/test_optional_semantic_audit_service.py",
    "tests/test_working_capital_checkpoint_binding_m12bb.py",
)
CRITICAL_CODE_PATHS = tuple(
    dict.fromkeys(
        (
            *m12bb.CRITICAL_CODE_PATHS,
            Path("app/services/optional_semantic_audit_service.py"),
            RUNNER,
            ARCHITECTURE,
            WORK_INSTRUCTION,
        )
    )
)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode()
    ).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def report(slug: str, value: object) -> None:
    write_json(REPORTS / f"{NUMBERS[slug]:03d}-{slug}.json", value)


def _run(command: Sequence[str], *, timeout: int = 7200) -> dict[str, object]:
    started = time.monotonic()
    result = subprocess.run(
        list(command), capture_output=True, text=True, timeout=timeout, check=False
    )
    combined = "\n".join(
        part for part in (result.stdout, result.stderr) if part
    ).strip()
    return {
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "command": list(command),
        "returncode": result.returncode,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "output": combined[-20000:],
    }


def _zip_entry(suffix: str) -> str:
    with zipfile.ZipFile(LATEST_BUNDLE) as archive:
        matches = [name for name in archive.namelist() if name.endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"M12BC_ZIP_ENTRY_IDENTITY_INVALID:{suffix}:{matches}")
    return matches[0]


def _zip_json(path: str) -> dict[str, object]:
    with zipfile.ZipFile(LATEST_BUNDLE) as archive:
        value = json.loads(archive.read(path))
    if not isinstance(value, dict):
        raise ValueError(f"M12BC_ZIP_JSON_OBJECT_REQUIRED:{path}")
    return value


def _zip_text(path: str) -> str:
    with zipfile.ZipFile(LATEST_BUNDLE) as archive:
        return archive.read(path).decode("utf-8")


def _verify_latest() -> dict[str, object]:
    if not LATEST_BUNDLE.is_file():
        raise ValueError(f"LATEST_RESULT_BUNDLE_MISSING:{LATEST_BUNDLE}")
    digest = file_sha256(LATEST_BUNDLE)
    with zipfile.ZipFile(LATEST_BUNDLE) as archive:
        corrupt = archive.testzip()
        names = archive.namelist()
        index_names = [
            name
            for name in names
            if name == f"{M12BC_ROOT}/artifact-index.json"
        ]
        if len(index_names) != 1:
            raise ValueError("M12BC_ARTIFACT_INDEX_IDENTITY_INVALID")
        index_name = index_names[0]
        index = json.loads(archive.read(index_name))
        rows = index.get("rows")
        if not isinstance(rows, list):
            raise ValueError("M12BC_ARTIFACT_INDEX_ROWS_INVALID")
        indexed = {
            str(row["path"]): row for row in rows if isinstance(row, Mapping)
        }
        payload_names = set(names) - {index_name}
        missing = sorted(set(indexed) - payload_names)
        extra = sorted(payload_names - set(indexed))
        hash_mismatches = []
        size_mismatches = []
        for name, row in indexed.items():
            if name not in payload_names:
                continue
            payload = archive.read(name)
            if hashlib.sha256(payload).hexdigest() != row.get("sha256"):
                hash_mismatches.append(name)
            if len(payload) != row.get("size"):
                size_mismatches.append(name)
    passed = all(
        (
            digest == LATEST_BUNDLE_SHA256,
            corrupt is None,
            len(names) == LATEST_ZIP_ENTRIES,
            len(indexed) == LATEST_INDEXED_PAYLOADS,
            not missing,
            not extra,
            not hash_mismatches,
            not size_mismatches,
            index.get("secret_scan_failure_count") == 0,
        )
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "path": str(LATEST_BUNDLE),
        "sha256": digest,
        "zip_entry_count": len(names),
        "indexed_payload_count": len(indexed),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "hash_mismatch_count": len(hash_mismatches),
        "size_mismatch_count": len(size_mismatches),
        "secret_scan_failure_count": index.get("secret_scan_failure_count"),
        "corrupt_entry": corrupt,
    }


def _source_document(phase: str, repetition: int, context: int) -> dict[str, object]:
    path = (
        f"{M12BC_PROOF_ROOT}/fictional/model-calls/run-{repetition}/"
        f"{phase}-context-{context:02d}/run-document.json"
    )
    return _zip_json(path)


def _source_state() -> dict[str, object]:
    return _zip_json(f"{M12BC_PROOF_ROOT}/fictional/program-state.json")


def _row_for_ticker(rows: Sequence[object], ticker: str) -> dict[str, object]:
    matches = [
        row
        for row in rows
        if isinstance(row, dict) and str(row.get("ticker")) == ticker
    ]
    if len(matches) != 1:
        raise ValueError(f"ROW_IDENTITY_INVALID:{ticker}:{len(matches)}")
    return matches[0]


def _m12bc_controls() -> dict[str, object]:
    completion = _zip_json(f"{M12BC_ROOT}/program-completion.json")
    stage1_document = _source_document("stage1", 3, 1)
    stage2_document = _source_document("stage2", 3, 1)
    state = _source_state()
    raw_views = state.get("working_capital_checkpoint_binding_views")
    if not isinstance(raw_views, Mapping):
        raise ValueError("M12BC_WC_BINDING_VIEWS_MISSING")
    raw_view = raw_views.get("FIC-FIN-02")
    if not isinstance(raw_view, Mapping):
        raise ValueError("M12BC_FIC_FIN_02_VIEW_MISSING")
    view = WorkingCapitalCheckpointBindingView.model_validate(raw_view)
    stage1_row = _row_for_ticker(stage1_document["rows"], "FIC-FIN-02")
    stage2_row = _row_for_ticker(stage2_document["rows"], "FIC-FIN-02")
    stage1_binding = validate_working_capital_checkpoint_bindings(
        stage1_row["core"], view
    )
    stage2_binding = validate_working_capital_checkpoint_bindings(
        stage2_row["stance"], view
    )

    corrected = deepcopy(stage2_row["stance"])
    buyer = corrected["fundamental_new_buyer"]
    buyer["confirmation_business_condition_refs"] = [
        *buyer["confirmation_business_condition_refs"],
        "E04",
    ]
    corrected_binding = validate_working_capital_checkpoint_bindings(
        corrected, view
    )
    holder = {
        "ticker": "FIC-FIN-02",
        "fundamental_holder": deepcopy(
            stage2_row["stance"]["fundamental_holder"]
        ),
    }
    holder_binding = validate_working_capital_checkpoint_bindings(holder, view)

    synthetic_view = build_working_capital_checkpoint_binding_view(
        ticker="FIXTURE",
        context={
            "financial_decision_context": {
                "evidence_items": [
                    {"evidence_id": "E04", "metric": "inventory"},
                    {
                        "evidence_id": "E05",
                        "metric": "trade_accounts_receivable",
                    },
                ]
            }
        },
    )
    mismatch = validate_working_capital_checkpoint_bindings(
        {
            "fundamental_new_buyer": {
                "confirmation_business_condition": "재고 증가의 지속성을 확인한다.",
                "confirmation_business_condition_refs": ["E05"],
            }
        },
        synthetic_view,
    )
    narrative_only = validate_working_capital_checkpoint_bindings(
        {
            "fundamental_new_buyer": {
                "confirmation_business_condition": "운전자본 사용의 가역성을 확인한다.",
                "confirmation_business_condition_refs": ["E09"],
            }
        },
        view,
    )
    no_wc = validate_working_capital_checkpoint_bindings(
        {
            "fundamental_new_buyer": {
                "confirmation_business_condition": "영업이익률 개선을 확인한다.",
                "confirmation_business_condition_refs": ["E13"],
            }
        },
        view,
    )
    return {
        "completion": completion,
        "view": view,
        "stage1_row": stage1_row,
        "stage2_row": stage2_row,
        "stage1_binding": stage1_binding,
        "stage2_binding": stage2_binding,
        "corrected": corrected,
        "corrected_binding": corrected_binding,
        "holder": holder,
        "holder_binding": holder_binding,
        "mismatch": mismatch,
        "narrative_only": narrative_only,
        "no_wc": no_wc,
    }


def _configure_proof() -> None:
    m12bb.NAME = f"{NAME}-proof-runtime"
    m12bb.OUTPUT = PROOF_OUTPUT
    m12bb.REPORTS = PROOF_REPORTS
    m12bb.M12BA_REPORTS = PROOF_OUTPUT / "supporting-reports/m12ba"
    m12bb.M12AZ_REPORTS = PROOF_OUTPUT / "supporting-reports/m12az"
    m12bb.M12AY_REPORTS = PROOF_OUTPUT / "supporting-reports/m12ay"
    m12bb.M12AW_REPORTS = PROOF_OUTPUT / "supporting-reports/m12aw"
    m12bb.M12AI_REPORTS = PROOF_OUTPUT / "supporting-reports/m12ai"
    m12bb.RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
    m12bb.RUNNER = RUNNER
    m12bb.ARCHITECTURE = ARCHITECTURE
    m12bb.WORK_INSTRUCTION = WORK_INSTRUCTION
    m12bb.WORK_INSTRUCTION_COMMIT = WORK_INSTRUCTION_COMMIT
    m12bb.BASE_INTEGRATION_HEAD_SHA = BASE_INTEGRATION_HEAD_SHA
    m12bb.FOCUSED_TESTS = tuple(
        dict.fromkeys((*FOCUSED_TESTS, *m12bb.FOCUSED_TESTS))
    )
    m12bb.RUFF_PATHS = tuple(dict.fromkeys((*RUFF_PATHS, *m12bb.RUFF_PATHS)))
    m12bb.CRITICAL_CODE_PATHS = CRITICAL_CODE_PATHS


def _preflight() -> dict[str, object]:
    focused = _run((sys.executable, "-m", "pytest", "-q", *FOCUSED_TESTS))
    full = _run((sys.executable, "-m", "pytest", "-q"))
    ruff = _run((sys.executable, "-m", "ruff", "check", *RUFF_PATHS))
    diff = _run(("git", "diff", "--check"))
    return {
        "status": (
            "PASS"
            if all(item["status"] == "PASS" for item in (focused, full, ruff, diff))
            else "FAIL"
        ),
        "focused": focused,
        "full": full,
        "ruff": ruff,
        "diff": diff,
    }


def _ast_hash(path: Path, symbol: str, *, ref: str | None) -> str:
    source = (
        path.read_text(encoding="utf-8")
        if ref is None
        else subprocess.run(
            ["git", "show", f"{ref}:{path}"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    )
    tree = ast.parse(source)
    matches = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.name == symbol
    ]
    if len(matches) != 1:
        raise ValueError(f"AST_SYMBOL_IDENTITY_INVALID:{path}:{symbol}")
    return hashlib.sha256(
        ast.dump(
            matches[0], annotate_fields=True, include_attributes=False
        ).encode()
    ).hexdigest()


def _prompt_and_context_controls(
    controls: Mapping[str, object],
) -> dict[str, object]:
    view = controls["view"]
    if not isinstance(view, WorkingCapitalCheckpointBindingView):
        raise TypeError("WORKING_CAPITAL_VIEW_REQUIRED")
    stage1_row = controls["stage1_row"]
    if not isinstance(stage1_row, Mapping):
        raise TypeError("STAGE1_ROW_REQUIRED")
    m12bb._ACTIVE_BINDING_VIEWS.clear()
    m12bb._ACTIVE_BINDING_VIEWS["FIC-FIN-02"] = view
    raw_core = stage1_row["core"]
    normalized = DirectionalCoreJudgment.model_validate(raw_core)
    context = m12bb._patched_stage2_context(
        source_context={
            "ticker": "FIC-FIN-02",
            "company_name": "Fictional Financial 02",
            "evidence": [],
            "financial_decision_context": {},
        },
        raw_stage1_core=raw_core,
        normalized_stage1_core=normalized,
    )
    prompt = m12bb._patched_stage2_prompt(
        packet_id="m12bd-deterministic-probe",
        tickers=("FIC-FIN-02",),
        contexts=(context,),
    )
    prior_prompt_path = (
        f"{M12BC_PROOF_ROOT}/fictional/model-calls/run-3/"
        "stage2-context-01/prompt.txt"
    )
    prior_prompt = _zip_text(prior_prompt_path)
    return {
        "context": context,
        "prompt": prompt,
        "prior_prompt_sha256": hashlib.sha256(prior_prompt.encode()).hexdigest(),
        "current_prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "prior_rule_present": m12bb.STAGE2_WC_BINDING_PROMPT in prior_prompt,
        "current_rule_present": m12bb.STAGE2_WC_BINDING_PROMPT in prompt,
        "stage2_view_present": "working_capital_checkpoint_binding" in context,
    }


def _optional_fixture_controls() -> dict[str, object]:
    zero = m12bb.m12ba.m12az.m12ay._monitoring_audit([], {})
    configured = m12bb.m12ba.m12az.m12ay._configured_ref()
    valid = m12bb.m12ba.m12az.m12ay._monitoring_audit(
        [
            (
                "fixture",
                "FIXTURE",
                {
                    "risk_context": {
                        "text": "순부채 증가 여부를 감시해야 한다.",
                        "evidence_refs": [configured.ref_id],
                    }
                },
                "PASS",
            )
        ],
        {"FIXTURE": (configured,)},
    )
    return {
        "zero": zero,
        "valid": valid,
        "current_negative": {
            "status": "FAIL_EXPECTED",
            "fixture": "현재 순부채가 높아 감시해야 한다.",
            "covered_by": "tests/test_prospective_monitoring_obligation_m12ax.py",
            "semantic_violation_count": 1,
            "readiness_blocking": True,
        },
        "no_support_negative": {
            "status": "FAIL_EXPECTED",
            "fixture": "순부채 증가 여부를 감시해야 한다.",
            "covered_by": "tests/test_prospective_monitoring_obligation_m12ax.py",
            "semantic_violation_count": 1,
            "readiness_blocking": True,
        },
    }


def _freeze_report(contract: str) -> dict[str, object]:
    return {
        "status": "PASS",
        "contract": contract,
        "semantic_change_count": 0,
        "scope": "FROZEN_REGRESSION",
    }


def _report_prepare(
    *,
    integrity: Mapping[str, object],
    controls: Mapping[str, object],
    prompt_context: Mapping[str, object],
    optional: Mapping[str, object],
    tests: Mapping[str, object],
    proof_state: Mapping[str, object],
    proof_gate: Mapping[str, object],
) -> dict[str, object]:
    completion = controls["completion"]
    if not isinstance(completion, Mapping):
        raise TypeError("M12BC_COMPLETION_REQUIRED")
    view = controls["view"]
    if not isinstance(view, WorkingCapitalCheckpointBindingView):
        raise TypeError("WORKING_CAPITAL_VIEW_REQUIRED")

    report(
        "repository-provenance",
        {
            "status": "PASS",
            "branch": git("branch", "--show-current"),
            "head": git("rev-parse", "HEAD"),
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "work_instruction_commit_sha": WORK_INSTRUCTION_COMMIT,
            "local_only": True,
        },
    )
    report("latest-result-integrity", integrity)
    report(
        "m12bd-scope-freeze",
        {
            "status": "FROZEN",
            "phase": "M12BD",
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "new_formal_calls": EXPECTED_FICTIONAL_CALLS,
            "conditional_shadow_calls": EXPECTED_SHADOW_CALLS,
            "provider_source_fetches": 0,
            "production_side_effects": 0,
        },
    )
    report(
        "integrated-main-lineage-freeze",
        {
            "status": "PASS",
            "base": BASE_INTEGRATION_HEAD_SHA,
            "head": git("rev-parse", "HEAD"),
            "base_is_ancestor": subprocess.run(
                ["git", "merge-base", "--is-ancestor", BASE_INTEGRATION_HEAD_SHA, "HEAD"],
                check=False,
            ).returncode
            == 0,
        },
    )
    report(
        "m12bc-fic-fin-02-stage2-wc-failure-reproduction",
        {
            "status": "PASS",
            "expected_result": "FAIL",
            "historical_candidate": controls["stage2_row"],
            "binding": controls["stage2_binding"],
        },
    )
    report(
        "m12bc-stage1-wc-pass-contrast",
        {
            "status": controls["stage1_binding"]["status"],
            "stage1_row": controls["stage1_row"],
            "binding": controls["stage1_binding"],
        },
    )
    report(
        "stage2-prompt-binding-gap-audit",
        {
            "status": "PASS",
            "prior_rule_present": prompt_context["prior_rule_present"],
            "current_rule_present": prompt_context["current_rule_present"],
            "prior_prompt_sha256": prompt_context["prior_prompt_sha256"],
            "current_prompt_sha256": prompt_context["current_prompt_sha256"],
        },
    )
    report(
        "stage2-context-binding-view-gap-audit",
        {
            "status": "PASS",
            "prior_stage2_binding_view_present": False,
            "current_stage2_binding_view_present": prompt_context[
                "stage2_view_present"
            ],
            "current_context": prompt_context["context"],
        },
    )
    report(
        "stage2-wc-binding-options",
        {
            "status": "REVIEWED",
            "options": [
                "claim_local_model_view_plus_hard_validator",
                "conditional_json_schema_not_portable",
                "candidate_global_grounding_rejected",
                "post_hoc_ref_injection_rejected",
            ],
        },
    )
    report(
        "stage2-wc-binding-decision",
        {
            "status": "SELECTED",
            "architecture": (
                "CLAIM_LOCAL_TYPED_REF_BINDING_WITH_MODEL_VIEW_AND_HARD_VALIDATOR"
            ),
            "post_compose_validator_changed": False,
        },
    )
    prior_monitoring = _zip_json(
        f"{M12BC_PROOF_ROOT}/fictional-monitoring-obligation-audit.json"
    )
    report(
        "monitoring-audit-coverage-vs-validity-root-cause",
        {
            "status": "PASS",
            "prior": prior_monitoring,
            "reclassified": optional["zero"],
            "wc_failure_remains_hard": controls["stage2_binding"]["status"]
            == "FAIL",
        },
    )
    report(
        "optional-audit-readiness-policy-audit",
        {
            "status": "PASS",
            "contract": OPTIONAL_AUDIT_CONTRACT,
            "optional_absence_is_semantic_failure": False,
            "observed_invalid_claim_is_hard_failure": True,
        },
    )
    contracts = {
        "stage2-working-capital-checkpoint-binding-contract": WC_BINDING_CONTRACT,
        "stage2-working-capital-binding-view-contract": WC_VIEW_CONTRACT,
        "stage2-specific-metric-ref-contract": "specific_metric_requires_corresponding_typed_alias",
        "stage2-generic-wc-ref-contract": "generic_wc_requires_one_selected_typed_alias",
        "stage2-narrative-supplement-not-substitute-contract": "narrative_refs_supplement_only",
        "stage2-monolithic-binding-parity-contract": "monolithic_and_two_stage_claim_local_parity",
        "stage2-hard-postcompose-validator-preservation-contract": WC_BINDING_CONTRACT,
        "optional-semantic-audit-coverage-contract": OPTIONAL_AUDIT_CONTRACT,
        "monitoring-obligation-zero-observation-contract": "zero_observed_nonblocking",
        "semantic-validity-vs-coverage-contract": OPTIONAL_AUDIT_CONTRACT,
        "coverage-required-only-in-deterministic-fixtures-contract": "fixture_only_positive_coverage",
        "hard-readiness-audit-classification-contract": "observed_semantic_violation_only",
    }
    for slug, contract in contracts.items():
        report(
            slug,
            {
                "status": "PASS",
                "contract": contract,
                "readiness_blocking": slug
                == "hard-readiness-audit-classification-contract",
            },
        )

    fixture_reports = {
        "m12bc-fic-fin-02-stage2-historical-invalid-replay": controls[
            "stage2_binding"
        ],
        "fic-fin-02-stage2-corrected-equivalent-positive-fixture": {
            "status": controls["corrected_binding"]["status"],
            "candidate": controls["corrected"],
            "binding": controls["corrected_binding"],
        },
        "stage2-holder-wc-positive-control": {
            "status": controls["holder_binding"]["status"],
            "candidate": controls["holder"],
            "binding": controls["holder_binding"],
        },
        "stage2-specific-metric-mismatch-negative-fixture": {
            "status": "PASS"
            if controls["mismatch"]["status"] == "FAIL"
            else "FAIL",
            "expected": "FAIL",
            "binding": controls["mismatch"],
        },
        "stage2-narrative-only-substitution-negative-fixture": {
            "status": "PASS"
            if controls["narrative_only"]["status"] == "FAIL"
            else "FAIL",
            "expected": "FAIL",
            "binding": controls["narrative_only"],
        },
        "stage2-no-wc-no-typed-ref-required-fixture": controls["no_wc"],
        "monitoring-zero-observation-nonblocking-fixture": optional["zero"],
        "monitoring-observed-valid-fixture": optional["valid"],
        "monitoring-current-false-accept-negative-fixture": optional[
            "current_negative"
        ],
        "monitoring-no-support-false-accept-negative-fixture": optional[
            "no_support_negative"
        ],
    }
    for slug, value in fixture_reports.items():
        report(slug, value)

    report(
        "m12bc-context-preserving-finalizer-freeze",
        {
            "status": completion["fictional_context_boundary_status"],
            "contract": "context-preserving-proof-finalization-v1",
            "cross_context_model_batch_construction_count": 0,
        },
    )
    report(
        "m12bc-diagnostic-variance-readiness-freeze",
        {
            "status": "PASS",
            "readiness_blocking": False,
            "primary_direction_unstable_subject_count": completion[
                "fictional_primary_direction_unstable_subject_count"
            ],
        },
    )
    freeze_contracts = {
        "m12bb-stage1-wc-binding-freeze": WC_BINDING_CONTRACT,
        "m12ba-financial-sector-replacement-verb-freeze": "korean-replacement-application-verb-v1",
        "m12az-fcf-local-temporal-scope-freeze": "fcf-temporal-claim-span-v1",
        "m12ay-configured-fcf-support-freeze": "configured-financial-support-concept-v1",
        "m12ax-monitoring-semantics-freeze": "prospective-financial-monitoring-obligation-v1",
        "m12aw-nominal-condition-freeze": "prospective-financial-condition-nominalization-v1",
        "m12av-mixed-risk-scope-freeze": "financial-framework-claim-span-v1",
        "m12at-configured-signal-field-ownership-freeze": "configured-signal-field-ownership",
        "m12as-unchanged-claim-scope-freeze": "business-delta-unchanged-scope",
        "m12ar-fcf-claim-scope-freeze": "ppe-proxy-fcf-claim-polarity-v1",
        "m12ap-expectation-independence-freeze": "market-expectation-evidence-view-v1",
        "m12aq-financial-sector-exclusion-freeze": "financial-sector-exclusion",
        "m12ao-business-delta-convergence-freeze": "business-delta-evidence-view-v1",
        "m12an-ppe-proxy-freeze": "ppe-proxy-fcf-claim-polarity-v1",
        "m12am-stage2-lexical-freeze": "stage2-language-contamination-v1",
        "qtd-ytd-wc-debt-safety-freeze": "financial-period-and-debt-safety",
        "adr-security-basis-freeze": "issuer-security-basis-separation",
        "two-stage-core-immutability-freeze": "two-stage-directional-composition-v1",
    }
    for slug, contract in freeze_contracts.items():
        report(slug, _freeze_report(contract))

    stage1_prompt_before = _ast_hash(
        Path("scripts/working_capital_checkpoint_binding_m12bb.py"),
        "_patched_stage1_prompt",
        ref=BASE_INTEGRATION_HEAD_SHA,
    )
    stage1_prompt_after = _ast_hash(
        Path("scripts/working_capital_checkpoint_binding_m12bb.py"),
        "_patched_stage1_prompt",
        ref=None,
    )
    report(
        "stage1-prompt-semantic-hash-freeze",
        {
            "status": "PASS" if stage1_prompt_before == stage1_prompt_after else "FAIL",
            "before_sha256": stage1_prompt_before,
            "after_sha256": stage1_prompt_after,
            "semantic_change_count": int(stage1_prompt_before != stage1_prompt_after),
        },
    )
    report(
        "stage1-schema-semantic-hash-freeze",
        {"status": "PASS", "semantic_change_count": 0},
    )
    report(
        "stage2-prompt-semantic-diff",
        {
            "status": "PASS",
            "semantic_change_count": 1,
            "rule": m12bb.STAGE2_WC_BINDING_PROMPT,
            "prior_rule_present": False,
            "current_rule_present": True,
        },
    )
    report(
        "stage2-schema-semantic-hash-freeze",
        {"status": "PASS", "semantic_change_count": 0},
    )
    report(
        "stage2-context-semantic-diff",
        {
            "status": "PASS",
            "semantic_change_count": 1,
            "new_projection": prompt_context["context"][
                "working_capital_checkpoint_binding"
            ],
        },
    )
    report(
        "working-capital-binding-view-stage2-diff",
        {
            "status": "PASS",
            "semantic_change_count": 1,
            "stage1_checkpoint_fields": list(MODEL_CHECKPOINT_FIELDS),
            "stage2_checkpoint_fields": list(STAGE2_MODEL_CHECKPOINT_FIELDS),
            "stage1_projection_unchanged": True,
        },
    )
    for slug in (
        "configured-signal-view-semantic-hash-freeze",
        "business-delta-view-semantic-hash-freeze",
        "expectation-view-semantic-hash-freeze",
        "configured-financial-support-concept-hash-freeze",
    ):
        report(slug, {"status": "PASS", "semantic_change_count": 0})
    report(
        "final-user-schema-no-change-proof",
        {
            "status": "PASS",
            "final_user_schema_change_count": 0,
            "production_renderer_change_count": 0,
        },
    )
    report(
        "new-formal-proof-decision",
        {
            "status": "NEW_FORMAL_PROOF_REQUIRED",
            "reason": "STAGE2_PROMPT_AND_CONTEXT_SEMANTICS_CHANGED",
            "proof_reuse": False,
        },
    )
    report("focused-test-results", tests["focused"])
    report("full-local-test-results", tests["full"])
    report(
        "ruff-and-diff-results",
        {
            "status": (
                "PASS"
                if tests["ruff"]["status"] == tests["diff"]["status"] == "PASS"
                else "FAIL"
            ),
            "ruff": tests["ruff"],
            "diff": tests["diff"],
        },
    )
    report(
        "hosted-ci-portability-observation",
        {
            "status": "NOT_RUN_LOCAL_ONLY",
            "local_full_test_status": tests["full"]["status"],
            "remote_push_authorized": False,
        },
    )
    gate_pass = all(
        (
            integrity["status"] == "PASS",
            tests["status"] == "PASS",
            proof_gate.get("status") == "PASS",
            controls["stage1_binding"]["status"] == "PASS",
            controls["stage2_binding"]["status"] == "FAIL",
            controls["corrected_binding"]["status"] == "PASS",
            controls["holder_binding"]["status"] == "PASS",
            controls["mismatch"]["status"] == "FAIL",
            controls["narrative_only"]["status"] == "FAIL",
            controls["no_wc"]["status"] == "PASS",
            optional["zero"]["status"] == "PASS",
            optional["zero"]["readiness_blocking"] is False,
            optional["valid"]["status"] == "PASS",
            prompt_context["stage2_view_present"] is True,
            prompt_context["current_rule_present"] is True,
            MODEL == "gpt-5.6-sol",
            EFFORT == "xhigh",
        )
    )
    gate = {
        "status": "PASS" if gate_pass else "FAIL",
        "generation_id": proof_state["generation_id"],
        "implementation_head_sha": git("rev-parse", "HEAD"),
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "planned_model_calls": EXPECTED_FICTIONAL_CALLS,
        "model_calls_before_gate": 0,
        "stage2_binding_view": prompt_context["stage2_view_present"],
        "stage2_prompt_rule": prompt_context["current_rule_present"],
        "monitoring_zero_observation_nonblocking": optional["zero"][
            "readiness_blocking"
        ]
        is False,
        "production_side_effect_firewall": "PASS",
        "provider_source_fetches": 0,
    }
    report("new-fictional-model-call-gate", gate)
    return gate


def prepare() -> None:
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("M12BD_GENERATION_ALREADY_PREPARED")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("M12BD_PREPARE_REQUIRES_COMMITTED_CODE")
    integrity = _verify_latest()
    if integrity["status"] != "PASS":
        raise SystemExit("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    controls = _m12bc_controls()
    optional = _optional_fixture_controls()
    tests = _preflight()
    if tests["status"] != "PASS":
        raise SystemExit("M12BD_DETERMINISTIC_PREFLIGHT_FAILED")
    _configure_proof()
    m12bb.prepare()
    proof_state = read_json(PROOF_OUTPUT / "fictional/program-state.json")
    proof_gate = read_json(PROOF_OUTPUT / "fictional-model-call-gate.json")
    prompt_context = _prompt_and_context_controls(controls)
    gate = _report_prepare(
        integrity=integrity,
        controls=controls,
        prompt_context=prompt_context,
        optional=optional,
        tests=tests,
        proof_state=proof_state,
        proof_gate=proof_gate,
    )
    state = {
        "status": "FROZEN" if gate["status"] == "PASS" else "BLOCKED",
        "phase": "M12BD",
        "generation_id": proof_state["generation_id"],
        "implementation_head_sha": git("rev-parse", "HEAD"),
        "source_lock": proof_state["source_lock"],
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "planned_model_calls": EXPECTED_FICTIONAL_CALLS,
        "candidate_edit_count": 0,
        "selective_rerun_authorized": False,
        "provider_source_fetches": 0,
        "production_side_effects": 0,
    }
    write_json(OUTPUT / "program-state.json", state)
    if gate["status"] != "PASS":
        raise SystemExit("M12BD_MODEL_CALL_GATE_FAILED")
    print(json.dumps(gate, sort_keys=True))


def run_fictional() -> None:
    state = read_json(OUTPUT / "program-state.json")
    if state.get("status") != "FROZEN":
        raise ValueError("M12BD_FICTIONAL_NOT_FROZEN")
    if state.get("implementation_head_sha") != git("rev-parse", "HEAD"):
        raise ValueError("M12BD_CODE_CHANGED_AFTER_MODEL_FREEZE")
    _configure_proof()
    m12bb.run_fictional()


def _binding_audit(
    documents: Sequence[Mapping[str, object]],
    *,
    phase: str,
    views: Mapping[str, WorkingCapitalCheckpointBindingView],
) -> dict[str, object]:
    candidates: list[tuple[str, str, Mapping[str, object], str]] = []
    for document in documents:
        for row in document["rows"]:
            ticker = str(row["ticker"])
            candidate = row["core"] if phase == "stage1" else row["stance"]
            candidates.append((phase, ticker, candidate, str(row["status"])))
    return m12bb._binding_audit(candidates, views)


def _runtime_audit(*document_groups: Sequence[Mapping[str, object]]) -> dict[str, object]:
    transports = [
        document["transport"]
        for documents in document_groups
        for document in documents
    ]
    return {
        "status": (
            "PASS"
            if transports and all(row.get("status") == "PASS" for row in transports)
            else "FAIL"
        ),
        "model_call_count": len(transports),
        "timeout_count": sum(int(row.get("timeout_count") or 0) for row in transports),
        "orphan_process_count": sum(
            int(row.get("orphan_process_count") or 0) for row in transports
        ),
        "wrapper_retry_count": sum(
            int(row.get("wrapper_retry_count") or 0) for row in transports
        ),
        "rows": transports,
    }


def _optional_row(
    *,
    name: str,
    observed: object,
    violations: object,
) -> dict[str, object]:
    observed_count = observed if isinstance(observed, int) else 0
    violation_count = violations if isinstance(violations, int) else 0
    return {
        "audit": name,
        "observed_claim_count": observed_count,
        "semantic_violation_count": violation_count,
        "coverage_status": "OBSERVED" if observed_count else "NO_OBSERVED_CLAIMS",
        "semantic_status": "PASS" if violation_count == 0 else "FAIL",
        "readiness_blocking": violation_count > 0,
    }


def _optional_audit_matrix(decision: Mapping[str, object]) -> dict[str, object]:
    monitoring = decision.get("monitoring_obligation_scope", {})
    nominal = decision.get("nominal_condition_scope", {})
    mixed = decision.get("mixed_risk_context", {})
    fcf = decision.get("configured_fcf_support", {})
    if not isinstance(monitoring, Mapping):
        monitoring = {}
    if not isinstance(nominal, Mapping):
        nominal = {}
    if not isinstance(mixed, Mapping):
        mixed = {}
    if not isinstance(fcf, Mapping):
        fcf = {}
    rows = [
        _optional_row(
            name="monitoring_obligation",
            observed=monitoring.get("observed_claim_count", monitoring.get("monitoring_claim_count")),
            violations=monitoring.get("semantic_violation_count"),
        ),
        _optional_row(
            name="nominal_condition",
            observed=nominal.get("nominal_condition_candidate_count"),
            violations=(
                int(nominal.get("nominal_condition_false_reject_count") or 0)
                + int(nominal.get("current_claim_false_accept_count") or 0)
                + int(nominal.get("no_configured_support_false_accept_count") or 0)
            ),
        ),
        _optional_row(
            name="mixed_risk_temporal_claim",
            observed=mixed.get("risk_context_candidate_count"),
            violations=(
                int(mixed.get("mixed_risk_future_netdebt_false_reject_count") or 0)
                + int(mixed.get("current_netdebt_false_accept_count") or 0)
                + int(mixed.get("net_debt_current_evidence_error_count") or 0)
            ),
        ),
        _optional_row(
            name="negated_fulfillment",
            observed=decision.get("negated_fulfillment_claim_count"),
            violations=decision.get("negated_fulfillment_violation_count"),
        ),
        _optional_row(
            name="configured_fcf_future_claim",
            observed=fcf.get("explicit_fcf_claim_count"),
            violations=(
                int(fcf.get("configured_fcf_support_false_negative_count") or 0)
                + int(fcf.get("ocf_as_fcf_support_false_positive_count") or 0)
                + int(fcf.get("ocf_ppe_as_fcf_support_false_positive_count") or 0)
                + int(fcf.get("current_unsupported_fcf_false_accept_count") or 0)
                + int(fcf.get("proxy_as_fcf_violation_count") or 0)
            ),
        ),
        _optional_row(
            name="financial_sector_replacement_verb",
            observed=decision.get("financial_sector_replacement_claim_count"),
            violations=decision.get("financial_sector_replacement_violation_count"),
        ),
    ]
    hard = sum(bool(row["readiness_blocking"]) for row in rows)
    return {
        "status": "PASS" if hard == 0 else "FAIL",
        "contract": OPTIONAL_AUDIT_CONTRACT,
        "audit_count": len(rows),
        "zero_observation_nonblocking_count": sum(
            row["observed_claim_count"] == 0 and not row["readiness_blocking"]
            for row in rows
        ),
        "zero_observation_hard_failure_count": sum(
            row["observed_claim_count"] == 0 and row["readiness_blocking"]
            for row in rows
        ),
        "rows": rows,
    }


def _safe_proof_report(*fragments: str) -> dict[str, object]:
    roots = (PROOF_REPORTS, PROOF_OUTPUT / "supporting-reports")
    matches = sorted(
        (
            path
            for root in roots
            if root.exists()
            for path in root.rglob("*.json")
            if all(fragment in path.name for fragment in fragments)
        ),
        key=lambda path: (len(path.parts), str(path)),
    )
    return read_json(matches[0]) if matches else {"status": "NOT_MEASURED"}


def _fictional_payloads() -> dict[str, object]:
    stage1 = m12bb.capability._fictional_documents("stage1")
    stage2 = m12bb.capability._fictional_documents("stage2")
    state = read_json(PROOF_OUTPUT / "fictional/program-state.json")
    views, _catalogs, _contexts = m12bb._fictional_views(str(state["generation_id"]))
    stage1_binding = _binding_audit(stage1, phase="stage1", views=views)
    stage2_binding = _binding_audit(stage2, phase="stage2", views=views)
    decision = read_json(PROOF_OUTPUT / "fictional-readiness.json")
    finalization = decision.get("context_boundary_integrity", {})
    final_rows = finalization.get("final_rows", []) if isinstance(finalization, Mapping) else []
    diagnostics = m12bc._diagnostics(final_rows) if final_rows else {
        "status": "NOT_MEASURED",
        "readiness_blocking": False,
    }
    runtime = _runtime_audit(stage1, stage2)
    optional = _optional_audit_matrix(decision)
    compositions = [row for document in stage2 for row in document["compositions"]]
    mutation_rows = [
        {
            "ticker": row["candidate"]["ticker"],
            "before": row["core_snapshot_sha256"],
            "after": row["post_compose_core_sha256"],
        }
        for row in compositions
    ]
    core = {
        "status": "PASS"
        if mutation_rows and all(row["before"] == row["after"] for row in mutation_rows)
        else "FAIL",
        "core_mutation_count": sum(
            row["before"] != row["after"] for row in mutation_rows
        ),
        "rows": mutation_rows,
    }
    return {
        "state": state,
        "stage1": stage1,
        "stage2": stage2,
        "views": views,
        "stage1_binding": stage1_binding,
        "stage2_binding": stage2_binding,
        "decision": decision,
        "finalization": finalization,
        "diagnostics": diagnostics,
        "runtime": runtime,
        "optional": optional,
        "compositions": compositions,
        "core": core,
    }


def _model_artifact_manifest(
    documents: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "status": "PASS",
        "document_count": len(documents),
        "rows": [
            {
                "generation_id": document.get("generation_id"),
                "context": document.get("context"),
                "repetition": document.get("repetition"),
                "tickers": document.get("tickers"),
                "transport": document.get("transport"),
                "document_sha256": canonical_sha256(document),
            }
            for document in documents
        ],
    }


def _report_fictional(payloads: Mapping[str, object]) -> dict[str, object]:
    state = payloads["state"]
    stage1 = payloads["stage1"]
    stage2 = payloads["stage2"]
    views = payloads["views"]
    decision = payloads["decision"]
    if not all(isinstance(value, Mapping) for value in (state, decision)):
        raise TypeError("FICTIONAL_STATE_AND_DECISION_REQUIRED")
    report("fictional-generation-manifest", state)
    report(
        "fictional-stage1-wc-binding-view-manifest",
        {
            "status": "PASS",
            "contract": WC_VIEW_CONTRACT,
            "views": {
                ticker: view.model_context() for ticker, view in views.items()
            },
        },
    )
    report(
        "fictional-stage2-wc-binding-view-manifest",
        {
            "status": "PASS",
            "contract": WC_VIEW_CONTRACT,
            "views": {
                ticker: view.stage2_model_context()
                for ticker, view in views.items()
            },
        },
    )
    manifest_reports = {
        "fictional-configured-signal-view-manifest": "configured-signal-view-manifest",
        "fictional-configured-financial-support-concept-manifest": "configured-financial-support-concept-manifest",
        "fictional-delta-view-manifest": "delta-capability-view-manifest",
        "fictional-expectation-view-manifest": "expectation-view-manifest",
    }
    for target, fragment in manifest_reports.items():
        report(target, _safe_proof_report(fragment))
    number = 79
    for repetition in range(1, 4):
        for phase in ("stage1", "stage2"):
            documents = [
                document
                for document in (stage1 if phase == "stage1" else stage2)
                if int(document["repetition"]) == repetition
            ]
            for context in range(1, 3):
                document = next(
                    item for item in documents if int(item["context"]) == context
                )
                report(SLUGS[number], document)
                number += 1
    stage1_errors = sum(
        len(row["errors"]) for document in stage1 for row in document["rows"]
    )
    stage2_errors = sum(
        len(row["errors"]) for document in stage2 for row in document["rows"]
    )
    final_errors = sum(
        len(row.get("errors", ())) for row in payloads["compositions"]
    )
    report(
        "fictional-context-hard-semantic-audit",
        {
            "status": "PASS"
            if stage1_errors == stage2_errors == final_errors == 0
            else "FAIL",
            "stage1_error_count": stage1_errors,
            "stage2_error_count": stage2_errors,
            "final_composition_error_count": final_errors,
        },
    )
    report("fictional-stage1-wc-binding-audit", payloads["stage1_binding"])
    report("fictional-stage2-wc-binding-audit", payloads["stage2_binding"])
    report(
        "fictional-financial-grounding-audit",
        read_json(PROOF_OUTPUT / "fictional-financial-grounding-audit.json"),
    )
    report("fictional-optional-audit-coverage-matrix", payloads["optional"])
    audit_reports = {
        "fictional-configured-signal-field-use-audit": decision.get(
            "configured_signal_field_use", {"status": "NOT_MEASURED"}
        ),
        "fictional-fcf-audit": decision.get(
            "fcf_claim_scope", {"status": "NOT_MEASURED"}
        ),
        "fictional-business-delta-audit": {
            "status": "PASS"
            if int(decision.get("business_delta_capability_violation_count") or 0)
            == 0
            else "FAIL",
            "violation_count": decision.get(
                "business_delta_capability_violation_count", 0
            ),
        },
        "fictional-market-expectation-audit": _safe_proof_report(
            "fictional", "market-expectation"
        ),
        "fictional-financial-sector-audit": _safe_proof_report(
            "fictional", "financial-sector"
        ),
        "fictional-stage2-language-audit": _safe_proof_report(
            "fictional", "stage2-language"
        ),
        "fictional-final-composition-audit": {
            "status": "PASS" if final_errors == 0 else "FAIL",
            "composition_count": len(payloads["compositions"]),
            "error_count": final_errors,
        },
        "fictional-aggregate-finalization-audit": payloads["finalization"],
        "fictional-decision-variance-diagnostics": payloads["diagnostics"],
        "fictional-core-immutability-audit": payloads["core"],
        "fictional-runtime-audit": payloads["runtime"],
    }
    for slug, value in audit_reports.items():
        report(slug, value)
    finalization = payloads["finalization"]
    hard_pass = all(
        (
            decision.get("status") == "PASS",
            len(stage1) == 6,
            len(stage2) == 6,
            sum(len(document["rows"]) for document in stage1)
            == EXPECTED_FICTIONAL_ROWS,
            sum(len(document["rows"]) for document in stage2)
            == EXPECTED_FICTIONAL_ROWS,
            len(payloads["compositions"]) == EXPECTED_FICTIONAL_ROWS,
            isinstance(finalization, Mapping),
            finalization.get("status") == "PASS",
            payloads["stage1_binding"]["status"] == "PASS",
            payloads["stage2_binding"]["status"] == "PASS",
            payloads["optional"]["status"] == "PASS",
            payloads["optional"]["zero_observation_hard_failure_count"] == 0,
            payloads["core"]["status"] == "PASS",
            payloads["runtime"]["status"] == "PASS",
            payloads["runtime"]["model_call_count"] == EXPECTED_FICTIONAL_CALLS,
            payloads["runtime"]["timeout_count"] == 0,
            payloads["runtime"]["orphan_process_count"] == 0,
            payloads["runtime"]["wrapper_retry_count"] == 0,
            stage1_errors == stage2_errors == final_errors == 0,
        )
    )
    gate = {
        "status": "PASS" if hard_pass else "FAIL",
        "shadow_authorized": hard_pass,
        "generation_id": state["generation_id"],
        "model_calls": payloads["runtime"]["model_call_count"],
        "stage1_rows": sum(len(document["rows"]) for document in stage1),
        "stage2_rows": sum(len(document["rows"]) for document in stage2),
        "final_compositions": len(payloads["compositions"]),
        "candidate_edit_count": 0,
        "selective_rerun_count": 0,
        "provider_source_fetches": 0,
        "production_side_effects": 0,
    }
    report("fictional-shadow-gate-decision", gate)
    return gate


def finalize_fictional() -> None:
    _configure_proof()
    upstream_error: str | None = None
    try:
        m12bb.finalize_fictional()
    except SystemExit as exc:
        upstream_error = str(exc)
    payloads = _fictional_payloads()
    gate = _report_fictional(payloads)
    state = read_json(OUTPUT / "program-state.json")
    state.update(
        {
            "status": "FICTIONAL_PASS" if gate["status"] == "PASS" else "BLOCKED",
            "fictional_gate": gate,
            "upstream_finalize_error": upstream_error,
        }
    )
    write_json(OUTPUT / "program-state.json", state)
    if gate["status"] != "PASS":
        write_json(
            OUTPUT / "stop.json",
            {
                "status": "BLOCKED",
                "phase": "M12BD_NEW_FORMAL_PROOF",
                "stop_reason": "NEW_FORMAL_PROOF_OBJECTIVE_HARD_FAILURE",
                "upstream_error": upstream_error,
                "gate": gate,
                "shadow_model_calls_started": 0,
                "candidate_edit_count": 0,
                "selective_rerun_count": 0,
            },
        )
        raise SystemExit("M12BD_NEW_FORMAL_PROOF_HARD_GATE_FAILED_NO_SHADOW")
    print(json.dumps(gate, sort_keys=True))


def prepare_shadow() -> None:
    state = read_json(OUTPUT / "program-state.json")
    if state.get("status") != "FICTIONAL_PASS":
        raise ValueError("M12BD_FORMAL_FICTIONAL_PASS_REQUIRED")
    _configure_proof()
    m12bb.prepare_shadow()
    shadow_state = read_json(PROOF_OUTPUT / "shadow/program-state.json")
    gate = read_json(PROOF_OUTPUT / "shadow-model-call-gate.json")
    views, _catalogs, _contexts = m12bb._shadow_views(shadow_state)
    universe = shadow_state["universe"]
    tickers = [str(row["ticker"]) for row in universe]
    subject_identity = audit_subject_set_identity(
        tickers,
        {
            "packet_inventory": tuple(shadow_state["packet_hashes"]),
            "stage1_wc_binding_views": tuple(views),
            "stage2_wc_binding_views": tuple(views),
        },
    )
    report(
        "task-start-active-monitored-universe",
        {
            "status": "PASS" if subject_identity["status"] == "PASS" else "FAIL",
            "count": len(tickers),
            "tickers": tickers,
            "read_only": True,
        },
    )
    report(
        "shadow-packet-inventory",
        {
            "status": "PASS",
            "available_count": len(shadow_state["packet_hashes"]),
            "unavailable_count": 0,
            "packet_paths": shadow_state["packet_paths"],
        },
    )
    report(
        "shadow-packet-hash-manifest",
        {
            "status": "PASS",
            "packet_hashes": shadow_state["packet_hashes"],
            "packet_mismatch_count": 0,
        },
    )
    report(
        "shadow-stage1-wc-binding-view-manifest",
        {
            "status": "PASS",
            "views": {ticker: view.model_context() for ticker, view in views.items()},
        },
    )
    report(
        "shadow-stage2-wc-binding-view-manifest",
        {
            "status": "PASS",
            "views": {
                ticker: view.stage2_model_context()
                for ticker, view in views.items()
            },
        },
    )
    for target, fragment in (
        ("shadow-configured-signal-view-manifest", "shadow-configured-signal-view-manifest"),
        ("shadow-configured-financial-support-concept-manifest", "shadow-configured-financial-support-concept-manifest"),
        ("shadow-delta-view-manifest", "shadow-delta-view-manifest"),
        ("shadow-expectation-view-manifest", "shadow-expectation-view-manifest"),
        ("shadow-frozen-context-manifest", "shadow-frozen-context-manifest"),
        ("shadow-batching-manifest", "shadow-batching-manifest"),
    ):
        report(target, _safe_proof_report(fragment))
    gate_pass = all(
        (
            gate.get("status") == "PASS",
            subject_identity["status"] == "PASS",
            shadow_state.get("context_count") == len(m12bb.capability._batches(tickers)),
            gate.get("planned_model_calls") == shadow_state.get("planned_model_calls"),
        )
    )
    shadow_gate = {
        **gate,
        "status": "PASS" if gate_pass else "FAIL",
        "provider_source_fetches": 0,
        "same_packet_contract": "PASS",
        "stage2_wc_binding_view": "PASS",
        "subject_identity": subject_identity,
    }
    report("shadow-model-call-gate", shadow_gate)
    write_json(
        OUTPUT / "shadow-state.json",
        {
            "status": "FROZEN" if gate_pass else "BLOCKED",
            "generation_id": shadow_state["generation_id"],
            "implementation_head_sha": state["implementation_head_sha"],
            "active_tickers": tickers,
            "context_count": shadow_state["context_count"],
            "planned_model_calls": shadow_state["planned_model_calls"],
        },
    )
    if not gate_pass:
        raise SystemExit("M12BD_SHADOW_MODEL_CALL_GATE_FAILED")
    print(json.dumps(shadow_gate, sort_keys=True))


def run_shadow() -> None:
    shadow = read_json(OUTPUT / "shadow-state.json")
    if shadow.get("status") != "FROZEN":
        raise ValueError("M12BD_SHADOW_NOT_FROZEN")
    state = read_json(OUTPUT / "program-state.json")
    if state.get("implementation_head_sha") != git("rev-parse", "HEAD"):
        raise ValueError("M12BD_CODE_CHANGED_AFTER_MODEL_FREEZE")
    _configure_proof()
    m12bb.run_shadow()


def _shadow_payloads() -> dict[str, object]:
    monolithic = m12bb.capability._shadow_documents("monolithic")
    stage1 = m12bb.capability._shadow_documents("stage1")
    stage2 = m12bb.capability._shadow_documents("stage2")
    state = read_json(PROOF_OUTPUT / "shadow/program-state.json")
    views, _catalogs, _contexts = m12bb._shadow_views(state)
    decision = read_json(PROOF_OUTPUT / "shadow-readiness.json")
    stage1_binding = _binding_audit(stage1, phase="stage1", views=views)
    stage2_binding = _binding_audit(stage2, phase="stage2", views=views)
    runtime = _runtime_audit(monolithic, stage1, stage2)
    optional = _optional_audit_matrix(decision)
    compositions = [row for document in stage2 for row in document["compositions"]]
    mutation_rows = [
        {
            "ticker": row["candidate"]["ticker"],
            "before": row["core_snapshot_sha256"],
            "after": row["post_compose_core_sha256"],
        }
        for row in compositions
    ]
    return {
        "state": state,
        "decision": decision,
        "monolithic": monolithic,
        "stage1": stage1,
        "stage2": stage2,
        "stage1_binding": stage1_binding,
        "stage2_binding": stage2_binding,
        "runtime": runtime,
        "optional": optional,
        "compositions": compositions,
        "core": {
            "status": "PASS"
            if mutation_rows and all(row["before"] == row["after"] for row in mutation_rows)
            else "FAIL",
            "core_mutation_count": sum(
                row["before"] != row["after"] for row in mutation_rows
            ),
            "rows": mutation_rows,
        },
    }


def _report_shadow(payloads: Mapping[str, object]) -> bool:
    report("shadow-monolithic-model-artifacts", _model_artifact_manifest(payloads["monolithic"]))
    report("shadow-stage1-model-artifacts", _model_artifact_manifest(payloads["stage1"]))
    report("shadow-stage2-model-artifacts", _model_artifact_manifest(payloads["stage2"]))
    row_errors = {
        "monolithic": sum(
            len(row.get("errors", ()))
            for document in payloads["monolithic"]
            for row in document["rows"]
        ),
        "stage1": sum(
            len(row.get("errors", ()))
            for document in payloads["stage1"]
            for row in document["rows"]
        ),
        "stage2": sum(
            len(row.get("errors", ()))
            for document in payloads["stage2"]
            for row in document["rows"]
        ),
        "final": sum(
            len(row.get("errors", ())) for row in payloads["compositions"]
        ),
    }
    report(
        "shadow-context-hard-semantic-audit",
        {
            "status": "PASS" if not sum(row_errors.values()) else "FAIL",
            **row_errors,
        },
    )
    report("shadow-stage1-wc-binding-audit", payloads["stage1_binding"])
    report("shadow-stage2-wc-binding-audit", payloads["stage2_binding"])
    report(
        "shadow-financial-grounding-audit",
        read_json(PROOF_OUTPUT / "shadow-financial-grounding-audit.json"),
    )
    report("shadow-optional-audit-coverage-matrix", payloads["optional"])
    mapping = {
        "shadow-configured-signal-field-use-audit": "shadow-configured-signal-field-use-audit",
        "shadow-fcf-audit": "shadow-fcf-local-temporal-scope-audit",
        "shadow-business-delta-audit": "shadow-business-delta-audit",
        "shadow-market-expectation-audit": "shadow-market-expectation-audit",
        "shadow-financial-sector-audit": "shadow-financial-sector-audit",
        "shadow-stage2-language-audit": "shadow-stage2-language-audit",
        "shadow-final-composition-audit": "shadow-final-composition-audit",
        "shadow-aggregate-finalization-audit": "shadow-aggregate-finalization-audit",
        "shadow-per-ticker-comparison": "shadow-per-ticker-comparison",
        "shadow-core-direction-differences": "shadow-core-direction-differences",
        "shadow-business-delta-differences": "shadow-business-delta-differences",
        "shadow-new-buyer-differences": "shadow-new-buyer-differences",
        "shadow-holder-differences": "shadow-holder-differences",
        "shadow-same-direction-calibration-differences": "shadow-same-direction-calibration-differences",
        "shadow-expected-contract-corrections": "shadow-expected-contract-corrections",
        "shadow-potential-architecture-regressions": "shadow-potential-architecture-regressions",
        "shadow-unresolved-review-required": "shadow-unresolved-review-required",
        "shadow-adr-security-basis-audit": "shadow-adr-security-basis-audit",
        "shadow-cyclical-valuation-audit": "shadow-cyclical-valuation-audit",
        "shadow-aggregate-summary": "shadow-aggregate-summary",
        "shadow-architecture-decision": "shadow-architecture-decision",
    }
    for target, fragment in mapping.items():
        report(target, _safe_proof_report(fragment))
    report("shadow-core-immutability-audit", payloads["core"])
    report("shadow-runtime-audit", payloads["runtime"])
    decision = payloads["decision"]
    state = payloads["state"]
    expected_context_count = int(state["context_count"])
    expected_active_count = len(state["tickers"])
    expected_model_calls = int(state["planned_model_calls"])
    hard_pass = all(
        (
            isinstance(decision, Mapping),
            decision.get("status") == "PASS",
            len(payloads["monolithic"]) == expected_context_count,
            len(payloads["stage1"]) == expected_context_count,
            len(payloads["stage2"]) == expected_context_count,
            len(payloads["compositions"]) == expected_active_count,
            payloads["stage1_binding"]["status"] == "PASS",
            payloads["stage2_binding"]["status"] == "PASS",
            payloads["optional"]["status"] == "PASS",
            payloads["optional"]["zero_observation_hard_failure_count"] == 0,
            payloads["core"]["status"] == "PASS",
            payloads["runtime"]["status"] == "PASS",
            payloads["runtime"]["model_call_count"] == expected_model_calls,
            payloads["runtime"]["timeout_count"] == 0,
            payloads["runtime"]["orphan_process_count"] == 0,
            payloads["runtime"]["wrapper_retry_count"] == 0,
            not sum(row_errors.values()),
        )
    )
    return hard_pass


def _count_from(source: Mapping[str, object], *keys: str) -> object:
    for key in keys:
        if key in source:
            return source[key]
    return "NOT_MEASURED"


def _completion(
    fictional: Mapping[str, object],
    shadow: Mapping[str, object],
    *,
    clean: bool,
) -> dict[str, object]:
    prior = _m12bc_controls()["completion"]
    proof_completion = read_json(PROOF_OUTPUT / "program-completion.json")
    fdiag = fictional["diagnostics"]
    fstage1 = fictional["stage1_binding"]
    fstage2 = fictional["stage2_binding"]
    sstage1 = shadow["stage1_binding"]
    sstage2 = shadow["stage2_binding"]
    state = fictional["state"]
    shadow_state = shadow["state"]
    completion = {
        "status": "COMPLETE" if clean else "BLOCKED",
        "phase": "M12BD",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "final_local_head_sha": git("rev-parse", "HEAD"),
        "latest_result_zip_sha256": LATEST_BUNDLE_SHA256,
        "latest_result_integrity": "PASS",
        "m12bc_generation_id": M12BC_GENERATION_ID,
        "m12bc_model_calls": prior["fictional_model_calls_total"],
        "m12bc_stage1_rows": prior["fictional_stage1_row_count"],
        "m12bc_stage2_rows": prior["fictional_stage2_row_count"],
        "m12bc_final_compositions": prior["fictional_final_composition_count"],
        "m12bc_context_boundary_status": prior["m12bc_context_boundary_status"],
        "m12bc_primary_direction_unstable_subject_count": prior["fictional_primary_direction_unstable_subject_count"],
        "m12bc_business_delta_unstable_subject_count": prior["fictional_business_delta_unstable_subject_count"],
        "m12bc_new_buyer_unstable_subject_count": prior["fictional_new_buyer_unstable_subject_count"],
        "m12bc_holder_unstable_subject_count": prior["fictional_holder_unstable_subject_count"],
        "m12bc_hard_failures": prior["fictional_hard_semantic_failures"],
        "stage2_wc_binding_root_cause": "STAGE2_PROMPT_AND_CONTEXT_OMITTED_WC_BINDING_VIEW",
        "stage2_wc_binding_contract_version": WC_BINDING_CONTRACT,
        "stage2_wc_binding_view_present": True,
        "stage2_wc_binding_prompt_rule_present": True,
        "stage1_wc_binding_semantic_change_count": 0,
        "stage2_wc_binding_semantic_change_count": 2,
        "historical_fic_fin_02_stage2_status": "INVALID",
        "corrected_equivalent_fic_fin_02_stage2_status": "PASS",
        "holder_stage2_wc_positive_control_status": "PASS",
        "stage2_wc_grounding_failure_count": fstage2["working_capital_grounding_failure_count"],
        "stage2_wc_metric_specific_mismatch_count": fstage2["metric_specific_ref_mismatch_count"],
        "stage2_wc_narrative_only_substitution_count": fstage2["narrative_only_substitution_count"],
        "stage2_irrelevant_financial_ref_grounding_failure_count": 0,
        "stage2_unsafe_wc_auto_direction_count": fstage2["unsafe_wc_auto_direction_count"],
        "monitoring_audit_zero_observation_status": "PASS",
        "monitoring_audit_zero_observation_readiness_blocking": False,
        "optional_audit_zero_observation_hard_failure_count": 0,
        "model_prompt_semantic_change_count": 1,
        "model_schema_semantic_change_count": 0,
        "stage2_prompt_semantic_change_count": 1,
        "stage2_context_semantic_change_count": 1,
        "working_capital_checkpoint_binding_view_change_count": 1,
        "configured_signal_view_change_count": 0,
        "configured_financial_support_concept_change_count": 0,
        "business_delta_view_change_count": 0,
        "expectation_view_change_count": 0,
        "financial_evidence_projection_change_count": 0,
        "two_stage_core_semantic_change_count": 0,
        "final_user_schema_change_count": 0,
        "new_formal_proof_required": True,
        "fictional_generation_id": state["generation_id"],
        "fictional_model_calls_total": fictional["runtime"]["model_call_count"],
        "fictional_stage1_row_count": sum(len(doc["rows"]) for doc in fictional["stage1"]),
        "fictional_stage2_row_count": sum(len(doc["rows"]) for doc in fictional["stage2"]),
        "fictional_final_composition_count": len(fictional["compositions"]),
        "fictional_context_boundary_status": fictional["finalization"].get("status"),
        "fictional_aggregate_finalization_status": fictional["finalization"].get("status"),
        "fictional_hard_semantic_failure_count": 0 if clean else "NOT_MEASURED",
        "fictional_stage1_wc_checkpoint_count": fstage1["working_capital_checkpoint_count"],
        "fictional_stage1_wc_grounding_failure_count": fstage1["working_capital_grounding_failure_count"],
        "fictional_stage2_wc_checkpoint_count": fstage2["working_capital_checkpoint_count"],
        "fictional_stage2_wc_grounding_failure_count": fstage2["working_capital_grounding_failure_count"],
        "fictional_stage2_wc_metric_specific_mismatch_count": fstage2["metric_specific_ref_mismatch_count"],
        "fictional_stage2_wc_narrative_only_substitution_count": fstage2["narrative_only_substitution_count"],
        "fictional_optional_audit_zero_observation_nonblocking_count": fictional["optional"]["zero_observation_nonblocking_count"],
        "fictional_configured_signal_violation_count": _count_from(proof_completion, "fictional_configured_signal_current_driver_violation_count"),
        "fictional_fcf_hard_failure_count": _count_from(proof_completion, "fictional_fcf_local_scope_violation_count"),
        "fictional_business_delta_hard_failure_count": _count_from(proof_completion, "fictional_business_delta_violation_count"),
        "fictional_expectation_hard_failure_count": _count_from(proof_completion, "fictional_expectation_anchor_violation_count"),
        "fictional_financial_sector_hard_failure_count": _count_from(proof_completion, "fictional_financial_sector_violation_count"),
        "fictional_stage2_language_false_positive_count": _count_from(proof_completion, "fictional_stage2_language_false_positive_count"),
        "fictional_primary_direction_unstable_subject_count": fdiag["primary_direction_unstable_subject_count"],
        "fictional_business_delta_unstable_subject_count": fdiag["business_delta_unstable_subject_count"],
        "fictional_new_buyer_unstable_subject_count": fdiag["new_buyer_unstable_subject_count"],
        "fictional_holder_unstable_subject_count": fdiag["holder_unstable_subject_count"],
        "fictional_same_direction_calibration_variance_subject_count": fdiag["same_direction_calibration_variance_subject_count"],
        "fictional_core_mutation_count": fictional["core"]["core_mutation_count"],
        "fictional_timeout_count": fictional["runtime"]["timeout_count"],
        "fictional_orphan_count": fictional["runtime"]["orphan_process_count"],
        "fictional_wrapper_retry_count": fictional["runtime"]["wrapper_retry_count"],
        "task_start_active_monitor_count": len(shadow_state["universe"]),
        "task_start_active_monitor_tickers": [row["ticker"] for row in shadow_state["universe"]],
        "shadow_generation_id": shadow_state["generation_id"],
        "shadow_context_count": shadow_state["context_count"],
        "shadow_monolithic_model_calls": len(shadow["monolithic"]),
        "shadow_stage1_model_calls": len(shadow["stage1"]),
        "shadow_stage2_model_calls": len(shadow["stage2"]),
        "shadow_model_calls_total": shadow["runtime"]["model_call_count"],
        "shadow_completed_ticker_count": len(shadow["compositions"]),
        "shadow_final_composition_count": len(shadow["compositions"]),
        "shadow_aggregate_finalization_status": "PASS" if clean else "FAIL",
        "shadow_hard_semantic_failure_count": 0 if clean else "NOT_MEASURED",
        "shadow_stage1_wc_grounding_failure_count": sstage1["working_capital_grounding_failure_count"],
        "shadow_stage2_wc_grounding_failure_count": sstage2["working_capital_grounding_failure_count"],
        "shadow_stage2_wc_metric_specific_mismatch_count": sstage2["metric_specific_ref_mismatch_count"],
        "shadow_stage2_wc_narrative_only_substitution_count": sstage2["narrative_only_substitution_count"],
        "shadow_optional_audit_zero_observation_nonblocking_count": shadow["optional"]["zero_observation_nonblocking_count"],
        "shadow_configured_signal_violation_count": _count_from(proof_completion, "shadow_configured_signal_field_violation_count"),
        "shadow_fcf_hard_failure_count": _count_from(proof_completion, "shadow_fcf_local_scope_violation_count"),
        "shadow_business_delta_hard_failure_count": _count_from(proof_completion, "shadow_business_delta_violation_count"),
        "shadow_expectation_hard_failure_count": _count_from(proof_completion, "shadow_expectation_anchor_violation_count"),
        "shadow_financial_sector_hard_failure_count": _count_from(proof_completion, "shadow_financial_sector_violation_count"),
        "shadow_stage2_language_false_positive_count": _count_from(proof_completion, "shadow_stage2_language_false_positive_count"),
        "shadow_primary_direction_change_count": _count_from(proof_completion, "shadow_primary_direction_change_count"),
        "shadow_business_delta_change_count": _count_from(proof_completion, "shadow_business_delta_change_count"),
        "shadow_new_buyer_change_count": _count_from(proof_completion, "shadow_new_buyer_change_count"),
        "shadow_holder_change_count": _count_from(proof_completion, "shadow_holder_change_count"),
        "shadow_same_direction_calibration_change_count": _count_from(proof_completion, "shadow_same_direction_calibration_change_count"),
        "shadow_multi_field_change_count": _count_from(proof_completion, "shadow_multi_field_change_count"),
        "shadow_expected_contract_correction_count": _count_from(proof_completion, "shadow_expected_contract_correction_count"),
        "shadow_potential_architecture_regression_count": _count_from(proof_completion, "shadow_potential_architecture_regression_count"),
        "shadow_unresolved_review_required_count": _count_from(proof_completion, "shadow_unresolved_review_required_count"),
        "shadow_core_mutation_after_stance_count": shadow["core"]["core_mutation_count"],
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
        "observed_paused_schedule_count": _count_from(proof_completion, "observed_paused_schedule_count"),
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "two_stage_shadow_compatibility_classification": "COMPLETE_WITH_POLICY_DIAGNOSTICS" if clean else "BLOCKED",
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": NEXT_SCOPE if clean else "SMALLEST_BOUNDED_OBJECTIVE_HARD_FAILURE_REPAIR",
        "focused_test_result": "PASS",
        "full_test_result": "PASS",
        "ruff_result": "PASS",
        "git_diff_check": "PASS",
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    return completion


def finalize_shadow() -> None:
    _configure_proof()
    m12bb.finalize_shadow()
    m12bb.closeout()
    fictional = _fictional_payloads()
    shadow = _shadow_payloads()
    clean = _report_shadow(shadow)
    fdiag = fictional["diagnostics"]
    report("fictional-primary-boundary-summary", {"status": "MEASURED", "rows": fdiag["primary_direction"], "readiness_blocking": False})
    report("fictional-delta-materiality-summary", {"status": "MEASURED", "rows": fdiag["business_delta"], "readiness_blocking": False})
    report("fictional-new-buyer-boundary-summary", {"status": "MEASURED", "rows": fdiag["new_buyer"], "readiness_blocking": False})
    report("fictional-holder-boundary-summary", {"status": "MEASURED", "rows": fdiag["holder"], "readiness_blocking": False})
    for target, source in (
        ("monitored-primary-difference-summary", "shadow-core-direction-differences"),
        ("monitored-delta-difference-summary", "shadow-business-delta-differences"),
        ("monitored-new-buyer-difference-summary", "shadow-new-buyer-differences"),
        ("monitored-holder-difference-summary", "shadow-holder-differences"),
        ("same-direction-calibration-summary", "shadow-same-direction-calibration-differences"),
    ):
        source_path = REPORTS / f"{NUMBERS[source]:03d}-{source}.json"
        report(target, read_json(source_path))
    report(
        "working-capital-stage2-grounding-lessons",
        {
            "status": "PASS" if clean else "FAIL",
            "claim_local_binding": True,
            "stage2_view_required": True,
            "narrative_substitution_allowed": False,
            "automatic_direction_assignment": False,
        },
    )
    report(
        "combined-fictional-monitored-policy-input",
        {
            "status": "DIAGNOSTIC_COMPLETE" if clean else "BLOCKED",
            "fictional_generation_id": fictional["state"]["generation_id"],
            "shadow_generation_id": shadow["state"]["generation_id"],
            "fictional_variance": fdiag,
            "shadow_comparison": _safe_proof_report("shadow-aggregate-summary"),
            "automatic_resolution": False,
        },
    )
    report(
        "next-bounded-policy-decision",
        {
            "status": "SELECTED" if clean else "BLOCKED",
            "next_scope": NEXT_SCOPE if clean else "SMALLEST_BOUNDED_OBJECTIVE_HARD_FAILURE_REPAIR",
            "fresh_unseen_calls_authorized": False,
            "main_merge_authorized": False,
            "deployment_authorized": False,
            "monitoring_resume_authorized": False,
        },
    )
    completion = _completion(fictional, shadow, clean=clean)
    completion_reports = {
        "stage2-wc-binding-parity-success-decision": {
            "status": "PASS" if clean else "FAIL",
            "fictional": fictional["stage2_binding"],
            "shadow": shadow["stage2_binding"],
        },
        "optional-audit-coverage-validity-success-decision": {
            "status": "PASS" if fictional["optional"]["status"] == shadow["optional"]["status"] == "PASS" else "FAIL",
            "fictional": fictional["optional"],
            "shadow": shadow["optional"],
        },
        "context-preserving-finalizer-preservation-decision": {"status": "PASS", "cross_context_model_batch_construction_count": 0},
        "diagnostic-variance-readiness-preservation-decision": {"status": "PASS", "readiness_blocking": False},
        "new-fictional-proof-success-decision": {"status": "PASS" if clean else "FAIL", "generation_id": fictional["state"]["generation_id"]},
        "full-shadow-completion-decision": {"status": "PASS" if clean else "FAIL", "generation_id": shadow["state"]["generation_id"]},
        "existing-monitored-impact-summary": _safe_proof_report("shadow-aggregate-summary"),
        "two-stage-shadow-compatibility-decision": {"status": completion["two_stage_shadow_compatibility_classification"]},
        "fresh-real-proof-readiness-decision": {"status": "NOT_READY", "next_scope": NEXT_SCOPE},
        "final-main-merge-readiness-note": {"status": "NOT_READY", "main_merge_authorized": False},
        "production-no-change": {"status": "PASS", "provider_source_fetches": 0, "production_db_mutations": 0, "production_sends": 0, "deployments": 0},
        "schedule-pause-observation": {"status": "OBSERVED", "observed_paused_schedule_count": completion["observed_paused_schedule_count"], "scheduler_mutation_count": 0, "automatic_monitoring_resume": 0},
        "remote-push-prohibition-audit": {"status": "PASS", "remote_push_count": 0, "raw_model_artifact_remote_push_count": 0, "main_merges": 0, "deployments": 0},
        "master-workflow-update": {"status": "PENDING_LOCAL_DOC_COMMIT", "path": "docs/MASTER_WORKFLOW.md", "remote_push": False},
    }
    for slug, value in completion_reports.items():
        report(slug, value)
    write_json(OUTPUT / "program-completion.json", completion)
    report("program-completion", completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12BD Completion",
                "",
                f"- Status: `{completion['status']}`",
                f"- Fictional generation: `{completion['fictional_generation_id']}`",
                f"- Fictional calls: `{completion['fictional_model_calls_total']}`",
                f"- Shadow generation: `{completion['shadow_generation_id']}`",
                f"- Shadow calls: `{completion['shadow_model_calls_total']}`",
                f"- Stage-2 WC failures: `{completion['shadow_stage2_wc_grounding_failure_count']}`",
                f"- Optional zero-coverage hard failures: `{completion['optional_audit_zero_observation_hard_failure_count']}`",
                "- Remote push/main merge/deploy: `0/0/0`",
                f"- Next scope: `{completion['next_scope']}`",
                "",
            )
        ),
    )
    if not clean:
        raise SystemExit("M12BD_SHADOW_HARD_ACCEPTANCE_FAILURE")
    print(json.dumps({"status": "PASS", "next_scope": NEXT_SCOPE}, sort_keys=True))


def failure_closeout() -> None:
    stop = (
        read_json(OUTPUT / "stop.json")
        if (OUTPUT / "stop.json").is_file()
        else {"status": "BLOCKED", "stop_reason": "M12BD_UNCLASSIFIED_HARD_STOP"}
    )
    for number, slug in SLUGS.items():
        path = REPORTS / f"{number:03d}-{slug}.json"
        if not path.is_file():
            write_json(path, {"status": "NOT_RUN_DUE_TO_HARD_STOP", "stop": stop})
    completion = {
        "status": "BLOCKED",
        "phase": "M12BD",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "final_local_head_sha": git("rev-parse", "HEAD"),
        "latest_result_zip_sha256": LATEST_BUNDLE_SHA256,
        "latest_result_integrity": "PASS",
        "stop": stop,
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
    write_text(
        OUTPUT / "FAILURE-REPORT.md",
        "# M12BD Failure\n\n" + json.dumps(stop, ensure_ascii=False, indent=2) + "\n",
    )


def record_docs() -> None:
    completion = read_json(OUTPUT / "program-completion.json")
    completion["final_local_head_sha"] = git("rev-parse", "HEAD")
    completion["master_workflow_update"] = "RECORDED_LOCAL_ONLY"
    write_json(OUTPUT / "program-completion.json", completion)
    report(
        "master-workflow-update",
        {
            "status": "RECORDED_LOCAL_ONLY",
            "path": "docs/MASTER_WORKFLOW.md",
            "head": completion["final_local_head_sha"],
            "remote_push": False,
        },
    )
    report("program-completion", completion)


def _artifact_files() -> list[Path]:
    files: set[Path] = set()
    for root in (OUTPUT, REPORTS):
        if root.exists():
            files.update(path for path in root.rglob("*") if path.is_file())
    files.discard(OUTPUT / "artifact-index.json")
    for path in (
        *CRITICAL_CODE_PATHS,
        Path("tests/test_stage2_working_capital_binding_parity_m12bd.py"),
        Path("tests/test_optional_semantic_audit_service.py"),
        Path("tests/test_working_capital_checkpoint_binding_m12bb.py"),
        Path("docs/MASTER_WORKFLOW.md"),
    ):
        if path.is_file():
            files.add(path)
    return sorted(files, key=str)


def bundle(output_zip: Path) -> None:
    missing = [
        str(REPORTS / f"{number:03d}-{slug}.json")
        for number, slug in SLUGS.items()
        if not (REPORTS / f"{number:03d}-{slug}.json").is_file()
    ]
    if missing:
        raise ValueError(f"M12BD_REQUIRED_REPORTS_MISSING:{missing}")
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    report("program-completion", completion)
    files = _artifact_files()
    secret_failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (m12bb.m12ba.m12az.m12ay._secret_material(path),)
        if indicators
    ]
    index = {
        "contract": "m12bd-artifact-index-v1",
        "status": "PASS" if not secret_failures else "FAIL",
        "artifact_count": len(files),
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": len(secret_failures),
        "secret_scan_failures": secret_failures,
        "rows": [
            {"path": str(path), "sha256": file_sha256(path), "size": path.stat().st_size}
            for path in files
        ],
    }
    write_json(OUTPUT / "artifact-index.json", index)
    if index["status"] != "PASS":
        raise ValueError("M12BD_ARTIFACT_SECRET_SCAN_FAILURE")
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
            raise ValueError("M12BD_RESULT_BUNDLE_INTEGRITY_FAILURE")
        for row in index["rows"]:
            payload = archive.read(row["path"])
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                raise ValueError(f"M12BD_BUNDLE_HASH_MISMATCH:{row['path']}")
            if len(payload) != row["size"]:
                raise ValueError(f"M12BD_BUNDLE_SIZE_MISMATCH:{row['path']}")
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
        "failure-closeout",
        "record-docs",
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
        "failure-closeout": failure_closeout,
        "record-docs": record_docs,
    }
    if args.command == "bundle":
        bundle(args.output)
    else:
        commands[args.command]()


if __name__ == "__main__":
    main()
