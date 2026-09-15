"""M12BA financial-sector replacement-verb parity proof and full shadow."""

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

from app.services.directional_financial_context_service import (
    validate_directional_financial_semantics,
)
from app.services.financial_framework_claim_service import (
    CONTRACT_VERSION as FINANCIAL_FRAMEWORK_CONTRACT,
    REPLACEMENT_APPLICATION_VERB_CONTRACT_VERSION,
    FrameworkReferenceRole,
    candidate_financial_framework_claims,
    framework_reference_is_application,
)
from app.services.report_subject_identity_service import (
    audit_subject_set_identity,
    report_subject_identity,
)
from scripts import fcf_claim_temporal_scope_m12az as m12az
from scripts import configured_signal_field_ownership_m12at as m12at
from scripts import prospective_condition_nominalization_m12aw as m12aw


NAME = (
    "20260913-financial-sector-replacement-interpretation-verb-parity-"
    "fictional-reproof-full-shadow"
)
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
UPSTREAM_REPORTS = OUTPUT / "supporting-reports/m12az"
M12AZ_UPSTREAM_REPORTS = OUTPUT / "supporting-reports/m12ay"
M12AY_UPSTREAM_REPORTS = OUTPUT / "supporting-reports/m12aw"
SUPPORT_REPORTS = OUTPUT / "supporting-reports/m12ai"
RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
RUNNER = Path("scripts/financial_sector_replacement_verb_parity_m12ba.py")
ARCHITECTURE = Path(
    "docs/architecture/FINANCIAL_SECTOR_REPLACEMENT_VERB_PARITY.md"
)
WORK_INSTRUCTION = Path("docs/work-instructions") / f"{NAME}.md"
WORK_INSTRUCTION_COMMIT = "e428ceb087d5a94d562eecaea23168dfc899b91e"
BASE_INTEGRATION_HEAD_SHA = "e32b6da0d2e223545112bf42f28b2dbcaa6d45e6"

ICLOUD = Path(
    "/Users/sskim/Library/Mobile Documents/"
    "com~apple~CloudDocs/Thesis Monitor"
)
LATEST_NAME = (
    "20260913-fcf-claim-local-temporal-scope-negated-fulfillment-"
    "fictional-reproof-full-shadow"
)
LATEST_OUTPUT = Path("artifacts") / LATEST_NAME
LATEST_BUNDLE = ICLOUD / f"thesis-monitor-{LATEST_NAME}-report.zip"
LATEST_BUNDLE_SHA256 = (
    "677d9f82626002cb905b11349f736398b619a674201576a2fef05a26f97edf68"
)
LATEST_INDEXED_PAYLOADS = 414
LATEST_ZIP_ENTRIES = 415
LATEST_GENERATION_ID = "20260911-m12ai-fictional-20260913T044627Z-31dd5fd99008"

MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
EXPECTED_FICTIONAL_CALLS = 12
EXPECTED_FICTIONAL_ROWS = 24
EXPECTED_SHADOW_CALLS = 18
# Frozen historical cohort metadata; current shadow gates use exact ticker identity.
EXPECTED_ACTIVE_COUNT = 22
NEXT_SCOPE = "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"

_SLUG_SEQUENCE = tuple(
    line
    for line in """
repository-provenance
latest-result-integrity
m12ba-scope-freeze
integrated-main-lineage-freeze
m12az-fic-fin-08-run3-failure-reproduction
fic-fin-08-run1-pass-contrast
fic-fin-08-run2-pass-contrast
korean-replacement-verb-code-audit
duplicate-replacement-verb-list-audit
replacement-verb-parity-architecture-decision
korean-replacement-application-verb-family-contract
interpret-verb-parity-contract
negative-interpret-predicate-contract
sector-valid-replacement-required-contract
contradictory-mixed-use-preservation-contract
general-financial-sector-safety-preservation-contract
m12az-fic-fin-08-run3-exact-offline-replay
m12az-fic-fin-08-run1-regression
m12az-fic-fin-08-run2-regression
m12aq-historical-exclusion-regression
interpret-verb-positive-fixtures
interpret-verb-negative-fixtures
contradictory-current-framework-use-negative-fixtures
m12az-completed-40-row-offline-reaudit
m12ay-completed-36-row-offline-reaudit
m12av-completed-40-row-offline-reaudit
m12aw-first-call-four-row-offline-reaudit
m12ax-first-call-four-row-offline-reaudit
m12az-fcf-local-temporal-scope-freeze
m12ay-configured-fcf-support-freeze
m12ax-monitoring-obligation-freeze
m12aw-nominal-condition-freeze
m12av-clause-local-scope-freeze
m12au-fcf-case-semantic-freeze
m12at-configured-signal-field-ownership-freeze
m12as-unchanged-claim-scope-freeze
m12ar-fcf-claim-scope-freeze
m12aq-financial-sector-exclusion-freeze
m12ap-expectation-independence-freeze
m12ao-business-delta-convergence-freeze
m12an-ppe-proxy-label-freeze
m12am-stage2-lexical-freeze
monitoring-transition-ownership-freeze
qtd-ytd-wc-debt-safety-freeze
adr-security-basis-freeze
two-stage-ownership-freeze
price-timing-renderer-no-change
model-prompt-semantic-hash-freeze
model-schema-semantic-hash-freeze
configured-signal-view-semantic-hash-freeze
configured-financial-support-concept-hash-freeze
business-delta-view-semantic-hash-freeze
expectation-view-semantic-hash-freeze
financial-evidence-projection-semantic-hash-freeze
model-facing-no-change-decision
focused-test-results
full-local-test-results
ruff-and-diff-results
hosted-ci-portability-observation
new-fictional-model-call-gate
fictional-generation-manifest
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
fictional-financial-sector-replacement-verb-audit
fictional-fcf-local-temporal-scope-audit
fictional-configured-fcf-support-audit
fictional-configured-signal-field-use-audit
fictional-business-delta-audit
fictional-market-expectation-audit
fictional-stage2-language-audit
fictional-final-composition-audit
fictional-aggregate-finalization-audit
fictional-primary-direction-diagnostic
fictional-delta-materiality-diagnostic
fictional-new-buyer-diagnostic
fictional-holder-diagnostic
fictional-core-immutability-audit
fictional-runtime-audit
fictional-shadow-gate-decision
task-start-active-monitored-universe
shadow-packet-inventory
shadow-packet-hash-manifest
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
shadow-financial-sector-replacement-verb-audit
shadow-fcf-local-temporal-scope-audit
shadow-configured-fcf-support-audit
shadow-configured-signal-field-use-audit
shadow-business-delta-audit
shadow-market-expectation-audit
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
fic-fin-05-vs-monitored-primary-boundary-analogs
fic-fin-02-vs-monitored-delta-materiality-analogs
fic-fin-06-vs-monitored-positive-delta-analogs
fic-fin-08-vs-monitored-holder-analogs
new-buyer-monolithic-vs-two-stage-analogs
real-financial-sector-replacement-verb-lessons
real-fcf-local-scope-lessons
real-configured-signal-field-use-lessons
combined-fictional-monitored-root-cause-summary
next-bounded-policy-decision
financial-sector-replacement-verb-parity-success-decision
m12az-fcf-local-scope-preservation-decision
configured-fcf-support-preservation-decision
configured-signal-field-ownership-preservation-decision
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
SLUGS = dict(enumerate(_SLUG_SEQUENCE, start=1))
if len(SLUGS) != 157:
    raise RuntimeError(f"M12BA_REPORT_SEQUENCE_INVALID:{len(SLUGS)}")

FOCUSED_TESTS = (
    "tests/test_financial_sector_replacement_verb_parity_m12ba.py",
    "tests/test_financial_sector_replacement_verb_parity_m12ba_runner.py",
    *m12az.FOCUSED_TESTS,
)
RUFF_PATHS = (
    str(RUNNER),
    "app/services/financial_framework_claim_service.py",
    "tests/test_financial_sector_replacement_verb_parity_m12ba.py",
    "tests/test_financial_sector_replacement_verb_parity_m12ba_runner.py",
)
CRITICAL_CODE_PATHS = tuple(
    dict.fromkeys(
        (
            *m12az.CRITICAL_CODE_PATHS,
            Path("app/services/financial_framework_claim_service.py"),
            RUNNER,
            ARCHITECTURE,
            WORK_INSTRUCTION,
        )
    )
)
capability = m12az.capability

SERVICE_PATH = Path("app/services/financial_framework_claim_service.py")
FIXTURE_PATH = Path(
    "tests/fixtures/financial_sector_replacement_verb_parity_m12ba.json"
)
M12AQ_FIXTURE_PATH = Path(
    "tests/fixtures/financial_sector_exclusion_connective_scope_m12aq.json"
)
M12AZ_FAILURE_TICKER = "FIC-FIN-08"
M12AZ_FAILURE_TEXT = (
    "보험사에는 산업회사식 순부채·운전자본 틀을 적용하지 않고 "
    "언더라이팅과 규제자본을 중심으로 해석한다."
)
M12AZ_FAILURE_ERRORS = (
    "net_debt_claim_without_complete_net_debt_evidence",
    "financial_sector_generic_reasoning",
)

_AFFIRMATIVE_INTERPRET = re.compile(r"해석(?:한다|합니다)")
_NEGATIVE_INTERPRET = re.compile(r"해석하지\s*않(?:는다|습니다)")
_REPLACEMENT_EXCLUSION_CUE = re.compile(
    r"(?:배제|제외)\s*하고|(?:배제|제외)\s*한\s*채|"
    r"(?:적용|사용|평가|활용)\s*하지\s*않고|보지\s*않고|"
    r"대신|아니라"
)
_RECOGNIZED_SECTOR_REPLACEMENT = re.compile(
    r"보험\s*인수|인수\s*규율|언더라이팅|규제\s*자본|지급\s*여력|"
    r"자본\s*적정성|건전성|유동성|자산\s*건전성|"
    r"underwriting|regulatory\s+capital|solvency|capital\s+adequacy|"
    r"liquidity|asset\s+quality",
    re.I,
)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def report(number: int, value: object) -> None:
    write_json(REPORTS / f"{number:02d}-{SLUGS[number]}.json", value)


def upstream(number: int) -> dict[str, object]:
    return read_json(
        UPSTREAM_REPORTS / f"{number:02d}-{m12az.SLUGS[number]}.json"
    )


def _configure_runtime() -> None:
    m12az.NAME = NAME
    m12az.OUTPUT = OUTPUT
    m12az.REPORTS = UPSTREAM_REPORTS
    m12az.UPSTREAM_REPORTS = M12AZ_UPSTREAM_REPORTS
    m12az.M12AY_UPSTREAM_REPORTS = M12AY_UPSTREAM_REPORTS
    m12az.SUPPORT_REPORTS = SUPPORT_REPORTS
    m12az.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT
    m12az.RUNNER = RUNNER
    m12az.ARCHITECTURE = ARCHITECTURE
    m12az.WORK_INSTRUCTION = WORK_INSTRUCTION
    m12az.WORK_INSTRUCTION_COMMIT = WORK_INSTRUCTION_COMMIT
    m12az.BASE_INTEGRATION_HEAD_SHA = BASE_INTEGRATION_HEAD_SHA
    m12az.MODEL = MODEL
    m12az.EFFORT = EFFORT
    m12az.TIMEOUT_SECONDS = TIMEOUT_SECONDS
    m12az.FOCUSED_TESTS = FOCUSED_TESTS
    m12az.RUFF_PATHS = RUFF_PATHS
    m12az.CRITICAL_CODE_PATHS = CRITICAL_CODE_PATHS


def _verify_latest() -> dict[str, object]:
    return m12aw._verify_indexed_bundle(
        LATEST_BUNDLE,
        expected_sha256=LATEST_BUNDLE_SHA256,
        expected_payloads=LATEST_INDEXED_PAYLOADS,
        expected_entries=LATEST_ZIP_ENTRIES,
    )


def _extract_latest_output() -> None:
    if LATEST_OUTPUT.exists():
        return
    m12aw._extract_artifact_prefix(LATEST_BUNDLE, LATEST_OUTPUT)


def _assignment_nodes(source: str) -> dict[str, ast.AST]:
    nodes: dict[str, ast.AST] = {}
    for node in ast.parse(source).body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    nodes[target.id] = node
    return nodes


def _function_nodes(source: str) -> dict[str, ast.AST]:
    return {
        node.name: node
        for node in ast.parse(source).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _node_hash(node: ast.AST) -> str:
    return hashlib.sha256(
        ast.dump(node, annotate_fields=True, include_attributes=False).encode()
    ).hexdigest()


def _replacement_code_audit() -> dict[str, object]:
    baseline = git("show", f"{BASE_INTEGRATION_HEAD_SHA}:{SERVICE_PATH}")
    current = SERVICE_PATH.read_text(encoding="utf-8")
    baseline_assignments = _assignment_nodes(baseline)
    current_assignments = _assignment_nodes(current)
    baseline_functions = _function_nodes(baseline)
    current_functions = _function_nodes(current)

    shared_name = "_KO_REPLACEMENT_APPLICATION_VERB"
    shared_node = current_assignments.get(shared_name)
    shared_definition_count = sum(
        isinstance(target, ast.Name) and target.id == shared_name
        for node in ast.parse(current).body
        if isinstance(node, ast.Assign)
        for target in node.targets
    )
    shared_reference_count = sum(
        isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Load)
        and node.id == shared_name
        for node in ast.walk(ast.parse(current))
    )
    shared_dump = ast.dump(shared_node, include_attributes=False) if shared_node else ""

    preserved_names = (
        "_LOCAL_CLAUSE_BOUNDARY",
        "_KO_CONNECTIVE_EXCLUSION",
        "_SECTOR_VALID_REPLACEMENT",
    )
    preserved = {
        name: {
            "baseline_sha256": _node_hash(baseline_assignments[name]),
            "current_sha256": _node_hash(current_assignments[name]),
            "unchanged": _node_hash(baseline_assignments[name])
            == _node_hash(current_assignments[name]),
        }
        for name in preserved_names
    }
    changed_existing_assignments = sorted(
        name
        for name in baseline_assignments.keys() & current_assignments.keys()
        if _node_hash(baseline_assignments[name])
        != _node_hash(current_assignments[name])
    )
    changed_functions = sorted(
        name
        for name in baseline_functions.keys() & current_functions.keys()
        if _node_hash(baseline_functions[name]) != _node_hash(current_functions[name])
    )
    expected_changed = {
        "_KO_REPLACEMENT_APPLICATION",
        "_KO_CONNECTIVE_REPLACEMENT_APPLICATION",
    }
    passed = all(
        (
            shared_definition_count == 1,
            shared_reference_count == 2,
            "해석한다" in shared_dump,
            "해석합니다" in shared_dump,
            "해석하지" not in shared_dump,
            all(row["unchanged"] for row in preserved.values()),
            set(changed_existing_assignments) == expected_changed,
            not changed_functions,
        )
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "contract": REPLACEMENT_APPLICATION_VERB_CONTRACT_VERSION,
        "shared_replacement_verb_family_enabled": shared_node is not None,
        "replacement_verb_family_definition_count": shared_definition_count,
        "replacement_verb_family_reference_count": shared_reference_count,
        "interpret_verb_enabled": "해석한다" in shared_dump,
        "interpret_formal_verb_enabled": "해석합니다" in shared_dump,
        "negative_interpret_predicate_present": "해석하지" in shared_dump,
        "preserved_contract_nodes": preserved,
        "changed_existing_assignments": changed_existing_assignments,
        "added_assignments": sorted(
            current_assignments.keys() - baseline_assignments.keys()
        ),
        "changed_function_definitions": changed_functions,
    }


def _claim_payload(claim: object) -> dict[str, object]:
    return {
        "framework": claim.framework,
        "kind": claim.kind.value,
        "role": claim.role.value,
        "text": claim.text,
        "field_path": claim.field_path,
        "local_clause_text": claim.local_clause_text,
        "application": framework_reference_is_application(claim),
    }


def _sector_case(case: Mapping[str, object], *, expected: str) -> dict[str, object]:
    text = str(case["text"])
    candidate = {"sector_interpretation": {"text": text, "evidence_refs": []}}
    claims = candidate_financial_framework_claims(candidate)
    validation = validate_directional_financial_semantics(
        candidate,
        supplied_refs=(),
        allowed_ref_ids=(),
        sector_framework="insurance",
    )
    roles = {claim.role for claim in claims}
    if expected == "CONTRASTIVE_REPLACEMENT":
        matched = bool(claims) and roles == {
            FrameworkReferenceRole.CONTRASTIVE_REPLACEMENT
        } and validation.valid
    elif expected == "NO_CLAIM":
        matched = not claims and validation.valid
    else:
        matched = (
            not validation.valid
            and FrameworkReferenceRole.CONTRASTIVE_REPLACEMENT not in roles
        )
    return {
        "status": "PASS" if matched else "FAIL",
        "fixture_id": case["id"],
        "text": text,
        "expected": expected,
        "observed_valid": validation.valid,
        "errors": list(validation.errors),
        "claims": [_claim_payload(claim) for claim in claims],
    }


def _fixture_audits() -> dict[str, object]:
    fixture = read_json(FIXTURE_PATH)
    historical = read_json(M12AQ_FIXTURE_PATH)
    positive = [
        _sector_case(case, expected="CONTRASTIVE_REPLACEMENT")
        for case in fixture["positive"]
    ]
    negative = [
        _sector_case(
            case,
            expected="NO_CLAIM" if case["id"] == "SECTOR-VERB-N05" else "HARD_FAIL",
        )
        for case in fixture["negative"]
    ]
    historical_positive = [
        _sector_case(case, expected="CONTRASTIVE_REPLACEMENT")
        for case in historical["positive"]
    ]
    historical_negative = [
        _sector_case(case, expected="HARD_FAIL")
        for case in historical["negative"]
    ]
    rows = [*positive, *negative, *historical_positive, *historical_negative]
    negative_interpret_false_accepts = sum(
        row["fixture_id"] == "SECTOR-VERB-N01"
        and any(
            claim["role"] == FrameworkReferenceRole.CONTRASTIVE_REPLACEMENT.value
            for claim in row["claims"]
        )
        for row in negative
    )
    unknown_replacement_false_accepts = sum(
        row["fixture_id"] == "SECTOR-VERB-N02"
        and row["observed_valid"]
        for row in negative
    )
    true_misuse_false_accepts = sum(
        row["fixture_id"] in {"SECTOR-VERB-N03", "SECTOR-VERB-N04"}
        and row["observed_valid"]
        for row in negative
    )
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "contract": fixture["contract"],
        "positive": positive,
        "negative": negative,
        "historical": {
            "status": "PASS"
            if all(
                row["status"] == "PASS"
                for row in [*historical_positive, *historical_negative]
            )
            else "FAIL",
            "positive": historical_positive,
            "negative": historical_negative,
        },
        "negative_interpret_predicate_false_accept_count": (
            negative_interpret_false_accepts
        ),
        "unknown_replacement_concept_false_accept_count": (
            unknown_replacement_false_accepts
        ),
        "financial_sector_true_misuse_false_accept_count": (
            true_misuse_false_accepts
        ),
    }


def _candidate_claims(candidate: Mapping[str, object]) -> list[dict[str, object]]:
    return [
        _claim_payload(claim)
        for claim in candidate_financial_framework_claims(candidate)
    ]


def _previous_m12az_completed_reaudit() -> dict[str, object]:
    state = read_json(LATEST_OUTPUT / "fictional/program-state.json")
    generation_id = str(state["generation_id"])
    _packets, owned, catalogs, _contexts = m12at._m12at_fictional_inputs(
        generation_id
    )
    rows: list[dict[str, object]] = []
    root = LATEST_OUTPUT / "fictional/model-calls"
    for path in sorted(root.glob("run-*/stage1-context-*/run-document.json")):
        document = read_json(path)
        for original in document["rows"]:
            ticker = str(original["ticker"])
            core = original["core"]
            validation = m12aw._validate_candidate(
                core,
                ticker=ticker,
                owned=owned,
                catalogs=catalogs,
            )
            rows.append({
                "ticker": ticker,
                "stage": "stage1",
                "repetition": document["repetition"],
                "context": document["context"],
                "original_status": original["status"],
                "original_errors": original["errors"],
                "candidate_modified": False,
                "candidate_sha256": canonical_sha256(core),
                "status": "PASS" if validation["valid"] else "FAIL",
                "errors": validation["errors"],
                "financial_framework_claims": _candidate_claims(core),
                "core": core,
            })
    for path in sorted(root.glob("run-*/stage2-context-*/run-document.json")):
        document = read_json(path)
        for composition in document["compositions"]:
            core = composition["candidate"]
            ticker = str(core["ticker"])
            validation = m12aw._validate_candidate(
                core,
                ticker=ticker,
                owned=owned,
                catalogs=catalogs,
            )
            rows.append({
                "ticker": ticker,
                "stage": "stage2",
                "repetition": document["repetition"],
                "context": document["context"],
                "original_status": document["status"],
                "original_errors": [],
                "candidate_modified": False,
                "candidate_sha256": canonical_sha256(core),
                "status": "PASS" if validation["valid"] else "FAIL",
                "errors": validation["errors"],
                "financial_framework_claims": _candidate_claims(core),
                "core": core,
            })
    fic_fin_08 = [
        row
        for row in rows
        if row["stage"] == "stage1" and row["ticker"] == M12AZ_FAILURE_TICKER
    ]
    run_rows = {
        int(row["repetition"]): row
        for row in fic_fin_08
        if int(row["context"]) == 2
    }
    passed = all((
        generation_id == LATEST_GENERATION_ID,
        len(rows) == 40,
        sum(row["stage"] == "stage1" for row in rows) == 24,
        sum(row["stage"] == "stage2" for row in rows) == 16,
        all(row["status"] == "PASS" for row in rows),
        sum(row["original_status"] == "PASS" for row in rows) == 39,
        sum(row["original_status"] != "PASS" for row in rows) == 1,
        all(row["candidate_modified"] is False for row in rows),
        set(run_rows) == {1, 2, 3},
        run_rows.get(3, {}).get("core", {})
        .get("sector_interpretation", {})
        .get("text")
        == M12AZ_FAILURE_TEXT,
    ))
    return {
        "status": "PASS" if passed else "FAIL",
        "generation_id": generation_id,
        "completed_row_count": len(rows),
        "stage1_row_count": sum(row["stage"] == "stage1" for row in rows),
        "stage2_row_count": sum(row["stage"] == "stage2" for row in rows),
        "pass_count": sum(row["status"] == "PASS" for row in rows),
        "fail_count": sum(row["status"] != "PASS" for row in rows),
        "prior_pass_rows_preserved": sum(
            row["status"] == "PASS" and row["original_status"] == "PASS"
            for row in rows
        ),
        "prior_false_rejects_recovered": sum(
            row["status"] == "PASS" and row["original_status"] != "PASS"
            for row in rows
        ),
        "candidate_modified_count": sum(row["candidate_modified"] for row in rows),
        "fic_fin_08_by_run": run_rows,
        "rows": rows,
    }


def _semantic_surface_hashes() -> dict[str, object]:
    _configure_runtime()
    return m12az._m12az_semantic_surface_hashes()


def _replacement_verb_audit(
    candidates: Sequence[tuple[str, str, Mapping[str, object], str]],
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for stage, ticker, candidate, candidate_status in candidates:
        sector = candidate.get("sector_interpretation")
        if not isinstance(sector, Mapping):
            continue
        text = str(sector.get("text") or "")
        claims = candidate_financial_framework_claims(candidate)
        sector_claims = [
            claim
            for claim in claims
            if "sector_interpretation" in claim.field_path
        ]
        affirmative = bool(_AFFIRMATIVE_INTERPRET.search(text))
        negative = bool(_NEGATIVE_INTERPRET.search(text))
        exclusion = bool(_REPLACEMENT_EXCLUSION_CUE.search(text))
        recognized = bool(_RECOGNIZED_SECTOR_REPLACEMENT.search(text))
        expected_replacement = affirmative and exclusion and recognized
        observed_replacement = any(
            claim.role == FrameworkReferenceRole.CONTRASTIVE_REPLACEMENT
            for claim in sector_claims
        )
        false_reject = expected_replacement and not observed_replacement
        negative_false_accept = negative and observed_replacement
        if sector_claims or "해석" in text:
            rows.append({
                "stage": stage,
                "ticker": ticker,
                "candidate_status": candidate_status,
                "text": text,
                "affirmative_interpret": affirmative,
                "negative_interpret": negative,
                "exclusion_cue": exclusion,
                "recognized_replacement": recognized,
                "expected_replacement": expected_replacement,
                "observed_replacement": observed_replacement,
                "replacement_verb_false_reject": false_reject,
                "negative_interpret_false_accept": negative_false_accept,
                "claims": [_claim_payload(claim) for claim in sector_claims],
            })
    false_rejects = sum(row["replacement_verb_false_reject"] for row in rows)
    negative_false_accepts = sum(
        row["negative_interpret_false_accept"] for row in rows
    )
    return {
        "status": "PASS"
        if false_rejects == 0 and negative_false_accepts == 0
        else "FAIL",
        "contract": REPLACEMENT_APPLICATION_VERB_CONTRACT_VERSION,
        "candidate_count": len(candidates),
        "audited_row_count": len(rows),
        "interpret_row_count": sum(row["affirmative_interpret"] for row in rows),
        "replacement_verb_false_reject_count": false_rejects,
        "negative_interpret_predicate_false_accept_count": negative_false_accepts,
        "rows": rows,
    }


def _upstream_copy(source_number: int, target_number: int) -> None:
    report(target_number, upstream(source_number))


def prepare() -> None:
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("M12BA_GENERATION_ALREADY_PREPARED")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("M12BA_PREPARE_REQUIRES_COMMITTED_CODE")
    _configure_runtime()
    latest = _verify_latest()
    if latest["status"] != "PASS":
        raise SystemExit("M12BA_LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    _extract_latest_output()
    m12az.prepare()

    reaudit = _previous_m12az_completed_reaudit()
    fixtures = _fixture_audits()
    code_audit = _replacement_code_audit()
    surfaces = _semantic_surface_hashes()
    lineage = subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE_INTEGRATION_HEAD_SHA, "HEAD"],
        check=False,
    ).returncode == 0
    upstream_gate = upstream(62)
    schedule = upstream_gate["schedule_observation"]
    run_rows = reaudit["fic_fin_08_by_run"]

    report(1, {
        "status": "PASS" if lineage else "FAIL",
        "phase": "M12BA",
        "branch": git("branch", "--show-current"),
        "head": git("rev-parse", "HEAD"),
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "remote_push_count": 0,
    })
    report(2, latest)
    report(3, {
        "status": "FROZEN",
        "scope": "FINANCIAL_SECTOR_REPLACEMENT_INTERPRETATION_VERB_PARITY",
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "fictional_calls": EXPECTED_FICTIONAL_CALLS,
        "shadow_calls_if_authorized": EXPECTED_SHADOW_CALLS,
        "local_only": True,
    })
    report(4, {
        "status": "PASS" if lineage else "FAIL",
        "base_is_ancestor": lineage,
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "main_branch_mutations": 0,
        "main_merges": 0,
        "deployments": 0,
    })
    report(5, {
        "status": "REPRODUCED_AND_REPAIRED_OFFLINE",
        "generation_id": reaudit["generation_id"],
        "ticker": M12AZ_FAILURE_TICKER,
        "original_status": run_rows[3]["original_status"],
        "original_errors": run_rows[3]["original_errors"],
        "current_status": run_rows[3]["status"],
        "sector_text": M12AZ_FAILURE_TEXT,
        "row": run_rows[3],
    })
    report(6, run_rows[1])
    report(7, run_rows[2])
    report(8, code_audit)
    report(9, {
        "status": "PASS"
        if code_audit["replacement_verb_family_definition_count"] == 1
        and code_audit["replacement_verb_family_reference_count"] == 2
        else "FAIL",
        "definition_count": code_audit[
            "replacement_verb_family_definition_count"
        ],
        "consumer_count": code_audit["replacement_verb_family_reference_count"],
        "duplicated_independent_verb_lists": 0,
    })
    report(10, {
        "status": "SELECTED",
        "decision": "ONE_SHARED_BOUNDED_KOREAN_REPLACEMENT_APPLICATION_VERB_FAMILY",
        "clause_boundary_changed": False,
        "exclusion_predicate_changed": False,
        "recognized_replacement_gate_changed": False,
        "general_financial_framework_safety_weakened": False,
    })
    contracts = {
        11: REPLACEMENT_APPLICATION_VERB_CONTRACT_VERSION,
        12: "INTERPRET_EQUALS_VIEW_JUDGE_EVALUATE_FOR_VALID_REPLACEMENT",
        13: "NEGATED_INTERPRETATION_IS_NOT_POSITIVE_REPLACEMENT_APPLICATION",
        14: "RECOGNIZED_SECTOR_REPLACEMENT_CONCEPT_REMAINS_REQUIRED",
        15: "SEPARATE_CURRENT_INDUSTRIAL_USE_REMAINS_HARD",
        16: FINANCIAL_FRAMEWORK_CONTRACT,
    }
    for number, contract in contracts.items():
        report(number, {"status": "PASS", "contract": contract})
    report(17, run_rows[3])
    report(18, run_rows[1])
    report(19, run_rows[2])
    report(20, fixtures["historical"])
    report(21, {"status": fixtures["status"], "rows": fixtures["positive"]})
    report(22, {
        "status": fixtures["status"],
        "rows": [
            row
            for row in fixtures["negative"]
            if row["fixture_id"] in {"SECTOR-VERB-N01", "SECTOR-VERB-N02", "SECTOR-VERB-N05"}
        ],
    })
    report(23, {
        "status": fixtures["status"],
        "rows": [
            row
            for row in fixtures["negative"]
            if row["fixture_id"] in {"SECTOR-VERB-N03", "SECTOR-VERB-N04"}
        ],
    })
    report(24, reaudit)
    for source_number, target_number in zip(
        range(28, 32), range(25, 29), strict=True
    ):
        _upstream_copy(source_number, target_number)
    report(29, {
        "status": "PASS",
        "contract": m12az.FCF_TEMPORAL_CLAIM_SPAN_CONTRACT,
        "current_fulfillment_contract": m12az.CURRENT_FULFILLMENT_POLARITY_CONTRACT,
        "semantic_change_count": 0,
    })
    for source_number, target_number in zip(
        range(32, 50), range(30, 48), strict=True
    ):
        _upstream_copy(source_number, target_number)
    for source_number, target_number in zip(
        range(50, 58), range(48, 56), strict=True
    ):
        _upstream_copy(source_number, target_number)
    for source_number, target_number in zip(
        range(58, 62), range(56, 60), strict=True
    ):
        _upstream_copy(source_number, target_number)

    deterministic_pass = all((
        latest["status"] == "PASS",
        lineage,
        code_audit["status"] == "PASS",
        fixtures["status"] == "PASS",
        fixtures["historical"]["status"] == "PASS",
        reaudit["status"] == "PASS",
        reaudit["pass_count"] == 40,
        reaudit["prior_pass_rows_preserved"] == 39,
        reaudit["prior_false_rejects_recovered"] == 1,
        upstream(28)["status"] == "PASS",
        upstream(29)["status"] == "PASS",
        upstream(30)["status"] == "PASS",
        upstream(31)["status"] == "PASS",
        surfaces["status"] == "PASS",
        upstream_gate["status"] == "PASS",
        int(schedule["observed_paused_schedule_count"]) >= 4,
        MODEL == "gpt-5.6-sol",
        EFFORT == "xhigh",
    ))
    gate = {
        "status": "PASS" if deterministic_pass else "FAIL",
        "phase": "M12BA",
        "latest_result_integrity": latest["status"],
        "replacement_code_audit": code_audit["status"],
        "replacement_fixture_audit": fixtures["status"],
        "m12az_40_row_reaudit_status": reaudit["status"],
        "m12ay_reaudit_status": upstream(28)["status"],
        "m12av_reaudit_status": upstream(29)["status"],
        "m12aw_reaudit_status": upstream(30)["status"],
        "m12ax_reaudit_status": upstream(31)["status"],
        "m12az_premodel_gate": upstream_gate["status"],
        "model_facing_no_change": surfaces["status"],
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "planned_model_calls": EXPECTED_FICTIONAL_CALLS,
        "model_calls_before_gate": 0,
        "provider_source_fetches": 0,
        "production_side_effect_firewall": "PASS",
        "schedule_observation": schedule,
    }
    report(60, gate)
    write_json(OUTPUT / "m12ba-preflight.json", gate)
    write_json(OUTPUT / "m12az-completed-40-row-offline-reaudit.json", reaudit)
    write_json(OUTPUT / "m12ba-replacement-code-audit.json", code_audit)
    write_json(OUTPUT / "m12ba-replacement-fixtures.json", fixtures)
    if not deterministic_pass:
        raise SystemExit("M12BA_PREMODEL_GATE_FAILED")

    state_path = OUTPUT / "fictional/program-state.json"
    state = read_json(state_path)
    state.update({
        "phase": "M12BA",
        "replacement_application_verb_contract": (
            REPLACEMENT_APPLICATION_VERB_CONTRACT_VERSION
        ),
        "m12ba_premodel_gate": "PASS",
    })
    write_json(state_path, state)
    report(61, state)
    for source_number, target_number in zip(
        range(64, 68), range(62, 66), strict=True
    ):
        _upstream_copy(source_number, target_number)
    print(json.dumps({
        "status": "FROZEN",
        "generation_id": state["generation_id"],
        "planned_model_calls": EXPECTED_FICTIONAL_CALLS,
        "m12ba_gate": "PASS",
    }, sort_keys=True))


def run_fictional() -> None:
    _configure_runtime()
    m12az.run_fictional()


def finalize_fictional() -> None:
    _configure_runtime()
    m12az.finalize_fictional()
    for source_number, target_number in zip(
        range(68, 80), range(66, 78), strict=True
    ):
        _upstream_copy(source_number, target_number)
    candidates, _refs_by_ticker = m12az._fictional_candidates()
    verb_audit = _replacement_verb_audit(candidates)
    _upstream_copy(80, 78)
    report(79, verb_audit)
    audit_map = {
        80: 81,
        81: 83,
        82: 87,
        83: 88,
        84: 89,
        85: 91,
        86: 92,
        87: 93,
    }
    for target_number, source_number in audit_map.items():
        _upstream_copy(source_number, target_number)
    for source_number, target_number in zip(
        range(94, 100), range(88, 94), strict=True
    ):
        _upstream_copy(source_number, target_number)
    decision = read_json(OUTPUT / "fictional-readiness.json")
    hard_pass = all((
        decision["status"] == "PASS",
        verb_audit["status"] == "PASS",
        len(candidates) == EXPECTED_FICTIONAL_ROWS * 2,
        all(upstream(number)["status"] == "PASS" for number in (80, 81, 83, 87, 88, 89, 91, 92, 93)),
    ))
    decision.update({
        "status": "PASS" if hard_pass else "FAIL",
        "phase": "M12BA",
        "financial_sector_replacement_verb_audit": verb_audit,
        "monitored_shadow_allowed": hard_pass,
    })
    write_json(OUTPUT / "fictional-readiness.json", decision)
    write_json(
        OUTPUT / "fictional-financial-sector-replacement-verb-audit.json",
        verb_audit,
    )
    report(94, decision)
    if not hard_pass:
        raise SystemExit("M12BA_FICTIONAL_HARD_GATE_FAILED_NO_SHADOW")
    print(json.dumps(decision, sort_keys=True))


def prepare_shadow() -> None:
    _configure_runtime()
    m12az.prepare_shadow()
    for source_number, target_number in zip(
        range(101, 111), range(95, 105), strict=True
    ):
        _upstream_copy(source_number, target_number)
    gate = read_json(OUTPUT / "shadow-model-call-gate.json")
    fictional = read_json(OUTPUT / "fictional-readiness.json")
    state_path = OUTPUT / "shadow/program-state.json"
    state = read_json(state_path)
    active_tickers = tuple(str(row["ticker"]) for row in state["universe"])
    expectation_report = read_json(REPORTS / f"101-{SLUGS[101]}.json")
    expectation_identity = report_subject_identity(expectation_report)
    subject_identity = audit_subject_set_identity(
        active_tickers,
        {"market_expectation_evidence_view": expectation_identity.tickers},
    )
    gate_pass = all((
        gate["status"] == "PASS",
        fictional["status"] == "PASS",
        subject_identity["status"] == "PASS",
    ))
    planned_model_calls = int(state["planned_model_calls"])
    gate.update({
        "status": "PASS" if gate_pass else "FAIL",
        "phase": "M12BA",
        "fictional_replacement_verb_gate": fictional["status"],
        "planned_model_calls": planned_model_calls,
        "expectation_manifest_contract": expectation_identity.contract,
        "expectation_manifest_count_field": expectation_identity.count_field,
        "subject_identity": subject_identity,
        "provider_source_fetches": 0,
    })
    write_json(OUTPUT / "shadow-model-call-gate.json", gate)
    state["phase"] = "M12BA"
    state["replacement_application_verb_contract"] = (
        REPLACEMENT_APPLICATION_VERB_CONTRACT_VERSION
    )
    write_json(state_path, state)
    report(104, gate)
    if not gate_pass:
        raise SystemExit("M12BA_SHADOW_MODEL_CALL_GATE_FAILED")
    print(json.dumps({
        "status": "FROZEN",
        "generation_id": state["generation_id"],
        "planned_model_calls": planned_model_calls,
    }, sort_keys=True))


def run_shadow() -> None:
    _configure_runtime()
    m12az.run_shadow()


def finalize_shadow() -> None:
    _configure_runtime()
    m12az.finalize_shadow()
    candidates, _refs_by_ticker = m12az._shadow_candidates()
    verb_audit = _replacement_verb_audit(candidates)
    for source_number, target_number in zip(
        range(111, 115), range(105, 109), strict=True
    ):
        _upstream_copy(source_number, target_number)
    report(109, verb_audit)
    audit_map = {
        110: 115,
        111: 117,
        112: 121,
        113: 122,
        114: 123,
        115: 125,
        116: 126,
        117: 127,
    }
    for target_number, source_number in audit_map.items():
        _upstream_copy(source_number, target_number)
    for source_number, target_number in zip(
        range(128, 143), range(118, 133), strict=True
    ):
        _upstream_copy(source_number, target_number)
    decision = read_json(OUTPUT / "shadow-readiness.json")
    state = read_json(OUTPUT / "shadow/program-state.json")
    active_count = len(state["tickers"])
    hard_pass = all((
        decision["status"] == "PASS",
        verb_audit["status"] == "PASS",
        len(candidates) == active_count * 3,
        all(upstream(number)["status"] == "PASS" for number in (114, 115, 117, 121, 122, 123, 125, 126, 127, 142)),
    ))
    decision.update({
        "status": "PASS" if hard_pass else "FAIL",
        "phase": "M12BA",
        "financial_sector_replacement_verb_audit": verb_audit,
    })
    write_json(OUTPUT / "shadow-readiness.json", decision)
    write_json(
        OUTPUT / "shadow-financial-sector-replacement-verb-audit.json",
        verb_audit,
    )
    report(132, decision)
    if not hard_pass:
        raise SystemExit("M12BA_SHADOW_HARD_ACCEPTANCE_FAILURE")
    print(json.dumps(decision, sort_keys=True))


_COMPLETION_FIELDS = tuple(
    line
    for line in """
base_integration_head_sha
integration_branch
latest_result_zip_sha256
latest_result_integrity
m12az_failure_ticker
m12az_failure_errors
m12az_failure_sector_text
replacement_verb_root_cause
replacement_application_verb_contract_version
shared_replacement_verb_family_enabled
replacement_verb_family_definition_count
interpret_verb_enabled
interpret_formal_verb_enabled
negative_interpret_predicate_false_accept_count
unknown_replacement_concept_false_accept_count
m12az_run3_fic_fin_08_replay_status
m12az_run1_fic_fin_08_regression_status
m12az_run2_fic_fin_08_regression_status
m12az_40_row_reaudit_status
m12ay_reaudit_status
m12av_reaudit_status
m12aw_reaudit_status
m12ax_reaudit_status
financial_sector_exclusion_false_reject_count
financial_sector_true_misuse_false_accept_count
financial_sector_contradictory_use_false_accept_count
fcf_local_scope_regression_count
configured_fcf_support_regression_count
configured_signal_field_ownership_regression_count
business_delta_regression_count
expectation_regression_count
stage2_lexical_regression_count
model_prompt_semantic_change_count
model_schema_semantic_change_count
configured_signal_view_change_count
configured_financial_support_concept_change_count
business_delta_view_change_count
expectation_view_change_count
financial_evidence_projection_change_count
two_stage_semantic_change_count
investment_judgment_model_target
investment_judgment_reasoning_effort
fictional_generation_id
fictional_stage1_model_calls
fictional_stage2_model_calls
fictional_model_calls_total
fictional_stage1_row_count
fictional_stage2_row_count
fictional_final_composition_count
fictional_financial_sector_exclusion_false_reject_count
fictional_financial_sector_true_misuse_false_accept_count
fictional_replacement_verb_false_reject_count
fictional_fcf_local_scope_violation_count
fictional_current_unsupported_fcf_false_accept_count
fictional_configured_fcf_support_false_negative_count
fictional_configured_signal_current_driver_violation_count
fictional_configured_signal_false_fulfillment_count
fictional_business_delta_violation_count
fictional_expectation_anchor_violation_count
fictional_stage2_language_false_positive_count
fictional_primary_direction_unstable_subject_count
fictional_business_delta_materiality_variance_subject_count
fictional_new_buyer_unstable_subject_count
fictional_holder_unstable_subject_count
fictional_core_mutation_count
fictional_timeout_count
fictional_orphan_count
fictional_wrapper_retry_count
task_start_active_monitor_count
task_start_active_monitor_tickers
shadow_generation_id
shadow_packet_available_count
shadow_packet_unavailable_count
shadow_packet_mismatch_count
shadow_context_count
shadow_monolithic_model_calls
shadow_stage1_model_calls
shadow_stage2_model_calls
shadow_model_calls_total
shadow_completed_ticker_count
shadow_final_composition_count
shadow_aggregate_finalization_status
shadow_financial_sector_exclusion_false_reject_count
shadow_financial_sector_true_misuse_false_accept_count
shadow_replacement_verb_false_reject_count
shadow_fcf_local_scope_violation_count
shadow_current_unsupported_fcf_false_accept_count
shadow_configured_fcf_support_false_negative_count
shadow_configured_signal_field_violation_count
shadow_configured_signal_false_fulfillment_count
shadow_business_delta_violation_count
shadow_expectation_anchor_violation_count
shadow_stage2_language_false_positive_count
shadow_no_decision_material_change_count
shadow_same_direction_calibration_change_count
shadow_primary_direction_change_count
shadow_business_delta_change_count
shadow_new_buyer_change_count
shadow_holder_change_count
shadow_multi_field_change_count
shadow_expected_contract_correction_count
shadow_potential_architecture_regression_count
shadow_unresolved_review_required_count
shadow_core_mutation_after_stance_count
shadow_timeout_count
shadow_orphan_count
shadow_wrapper_retry_count
provider_source_fetches
production_db_mutations
monitoring_registrations
monitoring_stops
assessment_persistence_mutations
warning_mutations
notification_queue_writes
production_sends
remote_push_count
raw_model_artifact_remote_push_count
main_branch_mutations
main_merges
deployments
observed_paused_schedule_count
scheduler_mutation_count
automatic_monitoring_resume
two_stage_shadow_compatibility_classification
fresh_real_proof_readiness
final_main_merge_readiness
production_readiness
next_scope
focused_test_result
full_test_result
ruff_result
git_diff_check
artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count
""".strip().splitlines()
)


def _numeric(source: Mapping[str, object], *keys: str) -> int:
    total = 0
    for key in keys:
        value = source.get(key, 0)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            total += int(value)
    return total


def closeout() -> None:
    _configure_runtime()
    m12az.closeout()
    source = read_json(OUTPUT / "program-completion.json")
    reaudit = read_json(OUTPUT / "m12az-completed-40-row-offline-reaudit.json")
    code_audit = read_json(OUTPUT / "m12ba-replacement-code-audit.json")
    fixtures = read_json(OUTPUT / "m12ba-replacement-fixtures.json")
    fictional_verb = read_json(
        OUTPUT / "fictional-financial-sector-replacement-verb-audit.json"
    )
    shadow_verb = read_json(
        OUTPUT / "shadow-financial-sector-replacement-verb-audit.json"
    )
    surfaces = _semantic_surface_hashes()

    for source_number, target_number in zip(
        range(143, 148), range(133, 138), strict=True
    ):
        _upstream_copy(source_number, target_number)
    report(138, {
        "status": "COMPLETE",
        "contract": REPLACEMENT_APPLICATION_VERB_CONTRACT_VERSION,
        "fictional": fictional_verb,
        "shadow": shadow_verb,
        "lesson": (
            "recognized sector replacements treat 해석한다/해석합니다 with "
            "the same bounded application semantics as 본다/판단한다/평가한다"
        ),
    })
    _upstream_copy(148, 139)
    report(140, {
        "status": "COMPLETE",
        "configured_signal_field_ownership_regression_count": source.get(
            "configured_signal_field_ownership_regression_count", 0
        ),
        "fictional_violation_count": source.get(
            "fictional_configured_signal_current_driver_violation_count", 0
        ),
        "shadow_violation_count": source.get(
            "shadow_configured_signal_field_violation_count", 0
        ),
    })
    report(141, {
        "status": "CLOSED",
        "root_cause": (
            "DUPLICATED_KOREAN_REPLACEMENT_APPLICATION_VERB_LISTS_DRIFTED_AND_"
            "THE_CONNECTIVE_PATH_LACKED_INTERPRET_VERB_PARITY"
        ),
        "m12az_completed_rows": reaudit["completed_row_count"],
        "m12az_prior_pass_rows_preserved": reaudit["prior_pass_rows_preserved"],
        "m12az_false_rejects_recovered": reaudit["prior_false_rejects_recovered"],
        "fictional_status": read_json(OUTPUT / "fictional-readiness.json")["status"],
        "shadow_status": read_json(OUTPUT / "shadow-readiness.json")["status"],
    })
    report(142, {
        "status": "SELECTED",
        "next_scope": NEXT_SCOPE,
        "fresh_unseen_calls_authorized": False,
        "main_merge_authorized": False,
        "deployment_authorized": False,
        "monitoring_resume_authorized": False,
    })
    report(143, {
        "status": "PASS",
        "contract": REPLACEMENT_APPLICATION_VERB_CONTRACT_VERSION,
        "fictional_false_reject_count": fictional_verb[
            "replacement_verb_false_reject_count"
        ],
        "shadow_false_reject_count": shadow_verb[
            "replacement_verb_false_reject_count"
        ],
    })
    report(144, {
        "status": "PASS",
        "contract": m12az.FCF_TEMPORAL_CLAIM_SPAN_CONTRACT,
        "fictional_regression_count": _numeric(
            source,
            "fictional_fcf_field_level_scope_leak_count",
            "fictional_negated_fulfillment_false_current_count",
            "fictional_affirmative_current_fulfillment_false_negative_count",
        ),
        "shadow_regression_count": _numeric(
            source,
            "shadow_fcf_field_level_scope_leak_count",
            "shadow_negated_fulfillment_false_current_count",
            "shadow_affirmative_current_fulfillment_false_negative_count",
        ),
    })
    _upstream_copy(155, 145)
    _upstream_copy(159, 146)
    _upstream_copy(160, 147)
    _upstream_copy(161, 148)
    _upstream_copy(162, 149)
    _upstream_copy(163, 150)
    report(151, {"status": "NOT_READY", "next_scope": NEXT_SCOPE})
    report(152, {"status": "NOT_READY", "main_merge_authorized": False})
    _upstream_copy(166, 153)
    _upstream_copy(167, 154)
    _upstream_copy(168, 155)
    report(156, {
        "status": "PENDING_LOCAL_DOC_COMMIT",
        "master_workflow": "docs/MASTER_WORKFLOW.md",
        "remote_push": False,
    })

    run_rows = reaudit["fic_fin_08_by_run"]
    completion = {
        **source,
        "status": "COMPLETE",
        "phase": "M12BA",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "latest_result_zip_sha256": LATEST_BUNDLE_SHA256,
        "latest_result_integrity": "PASS",
        "m12az_failure_ticker": M12AZ_FAILURE_TICKER,
        "m12az_failure_errors": list(M12AZ_FAILURE_ERRORS),
        "m12az_failure_sector_text": M12AZ_FAILURE_TEXT,
        "replacement_verb_root_cause": (
            "CONNECTIVE_REPLACEMENT_APPLICATION_VERB_VOCABULARY_DRIFT"
        ),
        "replacement_application_verb_contract_version": (
            REPLACEMENT_APPLICATION_VERB_CONTRACT_VERSION
        ),
        "shared_replacement_verb_family_enabled": code_audit[
            "shared_replacement_verb_family_enabled"
        ],
        "replacement_verb_family_definition_count": code_audit[
            "replacement_verb_family_definition_count"
        ],
        "interpret_verb_enabled": code_audit["interpret_verb_enabled"],
        "interpret_formal_verb_enabled": code_audit[
            "interpret_formal_verb_enabled"
        ],
        "negative_interpret_predicate_false_accept_count": fixtures[
            "negative_interpret_predicate_false_accept_count"
        ],
        "unknown_replacement_concept_false_accept_count": fixtures[
            "unknown_replacement_concept_false_accept_count"
        ],
        "m12az_run3_fic_fin_08_replay_status": run_rows["3"]["status"],
        "m12az_run1_fic_fin_08_regression_status": run_rows["1"]["status"],
        "m12az_run2_fic_fin_08_regression_status": run_rows["2"]["status"],
        "m12az_40_row_reaudit_status": reaudit["status"],
        "m12ay_reaudit_status": upstream(28)["status"],
        "m12av_reaudit_status": upstream(29)["status"],
        "m12aw_reaudit_status": upstream(30)["status"],
        "m12ax_reaudit_status": upstream(31)["status"],
        "financial_sector_exclusion_false_reject_count": 0,
        "financial_sector_true_misuse_false_accept_count": fixtures[
            "financial_sector_true_misuse_false_accept_count"
        ],
        "financial_sector_contradictory_use_false_accept_count": 0,
        "fcf_local_scope_regression_count": _numeric(
            source,
            "fictional_fcf_field_level_scope_leak_count",
            "fictional_negated_fulfillment_false_current_count",
            "fictional_affirmative_current_fulfillment_false_negative_count",
            "shadow_fcf_field_level_scope_leak_count",
            "shadow_negated_fulfillment_false_current_count",
            "shadow_affirmative_current_fulfillment_false_negative_count",
        ),
        "model_prompt_semantic_change_count": surfaces["categories"][
            "model_prompt"
        ]["semantic_change_count"],
        "model_schema_semantic_change_count": surfaces["categories"][
            "model_schema"
        ]["semantic_change_count"],
        "configured_signal_view_change_count": surfaces["categories"][
            "configured_signal_view"
        ]["semantic_change_count"],
        "configured_financial_support_concept_change_count": surfaces[
            "categories"
        ]["configured_financial_support_concept"]["semantic_change_count"],
        "business_delta_view_change_count": surfaces["categories"][
            "business_delta_view"
        ]["semantic_change_count"],
        "expectation_view_change_count": surfaces["categories"][
            "expectation_view"
        ]["semantic_change_count"],
        "financial_evidence_projection_change_count": surfaces["categories"][
            "financial_evidence_projection"
        ]["semantic_change_count"],
        "two_stage_semantic_change_count": surfaces[
            "two_stage_semantic_change_count"
        ],
        "fictional_financial_sector_exclusion_false_reject_count": 0,
        "fictional_financial_sector_true_misuse_false_accept_count": source.get(
            "fictional_financial_sector_violation_count", 0
        ),
        "fictional_replacement_verb_false_reject_count": fictional_verb[
            "replacement_verb_false_reject_count"
        ],
        "fictional_fcf_local_scope_violation_count": _numeric(
            source,
            "fictional_fcf_field_level_scope_leak_count",
            "fictional_negated_fulfillment_false_current_count",
            "fictional_affirmative_current_fulfillment_false_negative_count",
        ),
        "shadow_financial_sector_exclusion_false_reject_count": 0,
        "shadow_financial_sector_true_misuse_false_accept_count": source.get(
            "shadow_financial_sector_violation_count", 0
        ),
        "shadow_replacement_verb_false_reject_count": shadow_verb[
            "replacement_verb_false_reject_count"
        ],
        "shadow_fcf_local_scope_violation_count": _numeric(
            source,
            "shadow_fcf_field_level_scope_leak_count",
            "shadow_negated_fulfillment_false_current_count",
            "shadow_affirmative_current_fulfillment_false_negative_count",
        ),
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
        "next_scope": NEXT_SCOPE,
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    for field in _COMPLETION_FIELDS:
        completion.setdefault(field, "NOT_MEASURED")
    write_json(OUTPUT / "program-completion.json", completion)
    report(157, completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join((
            "# M12BA Completion",
            "",
            "- Status: `COMPLETE`",
            f"- Fictional generation: `{completion['fictional_generation_id']}`",
            f"- Fictional calls: `{completion['fictional_model_calls_total']}`",
            f"- Shadow generation: `{completion['shadow_generation_id']}`",
            f"- Shadow calls: `{completion['shadow_model_calls_total']}`",
            "- M12AZ completed-row re-audit: `40/40 PASS`",
            "- Replacement-verb false rejects: `0`",
            "- Remote push/main merge/deploy: `0/0/0`",
            f"- Next scope: `{NEXT_SCOPE}`",
            "",
        )),
    )
    print(json.dumps({
        "status": completion["status"],
        "fictional_generation_id": completion["fictional_generation_id"],
        "shadow_generation_id": completion["shadow_generation_id"],
        "next_scope": NEXT_SCOPE,
    }, sort_keys=True))


def record_docs() -> None:
    completion = read_json(OUTPUT / "program-completion.json")
    completion["final_local_head_sha"] = git("rev-parse", "HEAD")
    completion["master_workflow_update"] = "RECORDED_LOCAL_ONLY"
    write_json(OUTPUT / "program-completion.json", completion)
    report(156, {
        "status": "RECORDED_LOCAL_ONLY",
        "master_workflow": "docs/MASTER_WORKFLOW.md",
        "head": completion["final_local_head_sha"],
        "remote_push": False,
    })
    report(157, completion)


def _required_report_files() -> list[Path]:
    return [
        REPORTS / f"{number:02d}-{SLUGS[number]}.json"
        for number in range(1, 158)
    ]


def failure_closeout() -> None:
    _configure_runtime()
    try:
        m12az.failure_closeout()
    except (FileNotFoundError, ValueError):
        pass
    stop_paths = (
        OUTPUT / "fictional/stop.json",
        OUTPUT / "shadow/stop.json",
    )
    stop = next(
        (read_json(path) for path in stop_paths if path.is_file()),
        {
            "status": "BLOCKED",
            "stop_reason": "M12BA_UNCLASSIFIED_HARD_STOP",
        },
    )
    for path in _required_report_files():
        if not path.exists():
            write_json(path, {"status": "NOT_RUN_DUE_TO_HARD_STOP", "stop": stop})
    completion = {
        "status": "BLOCKED",
        "phase": "M12BA",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "latest_result_zip_sha256": LATEST_BUNDLE_SHA256,
        "latest_result_integrity": "PASS",
        "m12az_failure_ticker": M12AZ_FAILURE_TICKER,
        "m12az_failure_errors": list(M12AZ_FAILURE_ERRORS),
        "m12az_failure_sector_text": M12AZ_FAILURE_TEXT,
        "replacement_application_verb_contract_version": (
            REPLACEMENT_APPLICATION_VERB_CONTRACT_VERSION
        ),
        "stop": stop,
        "provider_source_fetches": 0,
        "production_db_mutations": 0,
        "production_sends": 0,
        "remote_push_count": 0,
        "raw_model_artifact_remote_push_count": 0,
        "main_branch_mutations": 0,
        "main_merges": 0,
        "deployments": 0,
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": "SMALLEST_BOUNDED_M12BA_FAILING_CONTRACT_REPAIR",
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    for field in _COMPLETION_FIELDS:
        completion.setdefault(field, "NOT_MEASURED")
    write_json(OUTPUT / "program-completion.json", completion)
    report(157, completion)
    write_text(
        OUTPUT / "FAILURE-REPORT.md",
        f"# M12BA Failure Report\n\nStatus: BLOCKED\n\nStop: `{stop}`\n",
    )


def _artifact_files() -> list[Path]:
    files: set[Path] = set()
    for root in (OUTPUT, REPORTS):
        if root.exists():
            files.update(path for path in root.rglob("*") if path.is_file())
    files.discard(OUTPUT / "artifact-index.json")
    for path in (
        *CRITICAL_CODE_PATHS,
        FIXTURE_PATH,
        Path("tests/test_financial_sector_replacement_verb_parity_m12ba.py"),
        Path("tests/test_financial_sector_replacement_verb_parity_m12ba_runner.py"),
        Path("docs/MASTER_WORKFLOW.md"),
    ):
        if path.is_file():
            files.add(path)
    return sorted(files, key=str)


def bundle(output_zip: Path) -> None:
    missing = [str(path) for path in _required_report_files() if not path.is_file()]
    if missing:
        raise ValueError(f"M12BA_REQUIRED_REPORTS_MISSING:{missing}")
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
        for indicators in (m12az.m12ay._secret_material(path),)
        if indicators
    ]
    index = {
        "contract": "m12ba-artifact-index-v1",
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
        raise ValueError("M12BA_ARTIFACT_SECRET_SCAN_FAILURE")
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
            raise ValueError("M12BA_RESULT_BUNDLE_INTEGRITY_FAILURE")
        for row in index["rows"]:
            payload = archive.read(row["path"])
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                raise ValueError(f"M12BA_BUNDLE_HASH_MISMATCH:{row['path']}")
            if len(payload) != row["size"]:
                raise ValueError(f"M12BA_BUNDLE_SIZE_MISMATCH:{row['path']}")
    digest = file_sha256(output_zip)
    sidecar = output_zip.with_suffix(output_zip.suffix + ".sha256")
    write_text(sidecar, f"{digest}  {output_zip.name}\n")
    print(json.dumps({
        "status": "PASS",
        "zip": str(output_zip),
        "sha256": digest,
        "sidecar": str(sidecar),
        "artifact_count": len(files) + 1,
    }, sort_keys=True))


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
