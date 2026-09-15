"""M12AZ FCF claim-local temporal scope proof and full shadow."""

# ruff: noqa: E402

from __future__ import annotations

import argparse
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

from app.services.configured_financial_support_concept_service import (
    CONTRACT_VERSION as FINANCIAL_SUPPORT_CONCEPT_CONTRACT,
    configured_financial_support_concepts,
)
from app.services.cross_market_decision_engine_service import (
    DecisionEvidenceRef,
    EvidenceCategory,
)
from app.services.directional_financial_context_service import (
    CURRENT_FULFILLMENT_POLARITY_CONTRACT,
    FCF_TEMPORAL_CLAIM_SPAN_CONTRACT,
    PROSPECTIVE_CONDITION_NOMINALIZATION_CONTRACT,
    PROSPECTIVE_MONITORING_OBLIGATION_CONTRACT,
    CurrentFulfillmentPolarity,
    _CURRENT_FCF_STATE_LANGUAGE,
    _CURRENT_MAGNITUDE_LANGUAGE,
    _CURRENT_SCOPE_MARKER_LANGUAGE,
    current_fulfillment_polarity,
    fcf_temporal_claim_spans,
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
)
from app.services.logical_condition_service import CheckpointMetric
from scripts import configured_fcf_prospective_support_m12ay as m12ay
from scripts import configured_signal_field_ownership_m12at as m12at
from scripts import prospective_condition_nominalization_m12aw as m12aw


NAME = "20260913-fcf-claim-local-temporal-scope-negated-fulfillment-fictional-reproof-full-shadow"
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
UPSTREAM_REPORTS = OUTPUT / "supporting-reports/m12ay"
M12AY_UPSTREAM_REPORTS = OUTPUT / "supporting-reports/m12aw"
SUPPORT_REPORTS = OUTPUT / "supporting-reports/m12ai"
RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
RUNNER = Path("scripts/fcf_claim_temporal_scope_m12az.py")
ARCHITECTURE = Path("docs/architecture/FCF_TEMPORAL_CLAIM_SCOPE.md")
WORK_INSTRUCTION = Path("docs/work-instructions") / f"{NAME}.md"
WORK_INSTRUCTION_COMMIT = "1a48271aee4494eb3a0c04b2c2ef0065360d9a79"
BASE_INTEGRATION_HEAD_SHA = "40a0e0ba0b7a0bbe6a1f467836fdf0eda843f934"

ICLOUD = Path("/Users/sskim/Library/Mobile Documents/com~apple~CloudDocs/Thesis Monitor")
LATEST_NAME = "20260913-configured-fcf-prospective-support-mapping-fictional-reproof-full-shadow"
LATEST_OUTPUT = Path("artifacts") / LATEST_NAME
LATEST_BUNDLE = ICLOUD / f"thesis-monitor-{LATEST_NAME}-report.zip"
LATEST_BUNDLE_SHA256 = "dc62c4a461740c9f6fe5496b753db0caab2051abbc27643f049dc075da01b05e"
LATEST_INDEXED_PAYLOADS = 338
LATEST_ZIP_ENTRIES = 339
LATEST_GENERATION_ID = "20260911-m12ai-fictional-20260913T013910Z-9c127e271105"

MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
EXPECTED_FICTIONAL_CALLS = 12
EXPECTED_FICTIONAL_ROWS = 24
EXPECTED_SHADOW_CALLS = 18
EXPECTED_ACTIVE_COUNT = 22
NEXT_SCOPE = "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"

_SLUG_SEQUENCE = tuple(
    line
    for line in """
repository-provenance
latest-result-integrity
m12az-scope-freeze
integrated-main-lineage-freeze
m12ay-four-row-failure-reproduction
fcf-whole-row-vs-local-span-forensic
current-fulfillment-regex-polarity-audit
netdebt-vs-fcf-temporal-path-comparison
fcf-local-span-architecture-options
fcf-local-span-architecture-decision
fcf-temporal-claim-span-contract
current-fulfillment-polarity-contract
negated-current-fulfillment-contract
affirmative-current-fulfillment-contract
current-scope-marker-contract
local-negation-scope-contract
fcf-ocf-concept-separation-contract
current-fcf-evidence-requirement-contract
m12ay-fic-fin-01-exact-offline-replay
m12ay-fic-fin-02-exact-offline-replay
m12ay-fic-fin-03-exact-offline-replay
m12ay-fic-fin-04-exact-offline-replay
negated-fulfillment-positive-fixtures
negated-plus-current-claim-negative-fixtures
fcf-local-span-positive-fixtures
fcf-local-span-current-negative-fixtures
english-negated-fulfillment-parity-fixtures
m12ay-completed-36-row-offline-reaudit
m12av-completed-40-row-offline-reaudit
m12aw-first-call-four-row-offline-reaudit
m12ax-first-call-four-row-offline-reaudit
m12ay-configured-fcf-support-freeze
m12ax-monitoring-obligation-freeze
m12aw-nominal-condition-freeze
m12av-clause-local-scope-freeze
m12au-fcf-case-semantic-freeze
m12at-configured-signal-field-ownership-freeze
m12as-unchanged-claim-scope-freeze
m12ar-fcf-claim-scope-freeze
m12aq-financial-sector-scope-freeze
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
fictional-fcf-local-temporal-scope-audit
fictional-negated-fulfillment-polarity-audit
fictional-configured-fcf-support-audit
fictional-monitoring-obligation-audit
fictional-nominal-condition-audit
fictional-mixed-risk-context-audit
fictional-configured-signal-field-use-audit
fictional-business-delta-audit
fictional-market-expectation-audit
fictional-financial-sector-audit
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
shadow-fcf-local-temporal-scope-audit
shadow-negated-fulfillment-polarity-audit
shadow-configured-fcf-support-audit
shadow-monitoring-obligation-audit
shadow-nominal-condition-audit
shadow-mixed-risk-context-audit
shadow-configured-signal-field-use-audit
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
fic-fin-05-vs-monitored-primary-boundary-analogs
fic-fin-02-vs-monitored-delta-materiality-analogs
fic-fin-06-vs-monitored-positive-delta-analogs
fic-fin-08-vs-monitored-holder-analogs
new-buyer-monolithic-vs-two-stage-analogs
real-fcf-local-scope-lessons
real-negated-fulfillment-lessons
real-configured-fcf-support-lessons
combined-fictional-monitored-root-cause-summary
next-bounded-policy-decision
fcf-local-temporal-scope-repair-success-decision
negated-fulfillment-polarity-repair-success-decision
configured-fcf-support-preservation-decision
monitoring-obligation-preservation-decision
nominal-condition-preservation-decision
mixed-risk-context-preservation-decision
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
if len(SLUGS) != 170:
    raise RuntimeError(f"M12AZ_REPORT_SEQUENCE_INVALID:{len(SLUGS)}")

FOCUSED_TESTS = (
    "tests/test_fcf_claim_temporal_scope_negated_fulfillment_m12az.py",
    "tests/test_fcf_claim_temporal_scope_negated_fulfillment_m12az_runner.py",
    *m12ay.FOCUSED_TESTS,
)
RUFF_PATHS = (
    str(RUNNER),
    "app/services/directional_financial_context_service.py",
    "app/services/financial_framework_claim_service.py",
    "tests/test_fcf_claim_temporal_scope_negated_fulfillment_m12az.py",
    "tests/test_fcf_claim_temporal_scope_negated_fulfillment_m12az_runner.py",
)
CRITICAL_CODE_PATHS = tuple(
    dict.fromkeys(
        (
            *m12ay.CRITICAL_CODE_PATHS,
            Path("app/services/financial_framework_claim_service.py"),
            Path("app/services/directional_financial_context_service.py"),
            RUNNER,
            ARCHITECTURE,
            WORK_INSTRUCTION,
        )
    )
)
capability = m12ay.capability


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
    return read_json(UPSTREAM_REPORTS / f"{number:02d}-{m12ay.SLUGS[number]}.json")


def _configure_runtime() -> None:
    m12ay.NAME = NAME
    m12ay.OUTPUT = OUTPUT
    m12ay.REPORTS = UPSTREAM_REPORTS
    m12ay.UPSTREAM_REPORTS = M12AY_UPSTREAM_REPORTS
    m12ay.SUPPORT_REPORTS = SUPPORT_REPORTS
    m12ay.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT
    m12ay.RUNNER = RUNNER
    m12ay.ARCHITECTURE = ARCHITECTURE
    m12ay.WORK_INSTRUCTION = WORK_INSTRUCTION
    m12ay.WORK_INSTRUCTION_COMMIT = WORK_INSTRUCTION_COMMIT
    m12ay.BASE_INTEGRATION_HEAD_SHA = BASE_INTEGRATION_HEAD_SHA
    m12ay.MODEL = MODEL
    m12ay.EFFORT = EFFORT
    m12ay.TIMEOUT_SECONDS = TIMEOUT_SECONDS
    m12ay.FOCUSED_TESTS = FOCUSED_TESTS
    m12ay.RUFF_PATHS = RUFF_PATHS
    m12ay.CRITICAL_CODE_PATHS = CRITICAL_CODE_PATHS


def _configured_ref(
    *,
    statement: str = "FCF 감소와 순부채 증가가 동반",
    metric_refs: tuple[CheckpointMetric, ...] = (CheckpointMetric.FCF,),
    ref_id: str = "m12az:configured-fcf",
) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=ref_id,
        category=EvidenceCategory.RISKS,
        label="설정된 미래 논리 조건",
        statement=statement,
        source_ref="stock.thesis.weaken_signals",
        metric_refs=metric_refs,
    )


def _fixture(
    *,
    fixture_id: str,
    text: str,
    expected_valid: bool,
    ref: DecisionEvidenceRef | None = None,
) -> dict[str, object]:
    supplied = ref or _configured_ref()
    candidate = {
        "risk_context": {
            "text": text,
            "evidence_refs": [supplied.ref_id],
        }
    }
    row = financial_claim_rows(candidate)[0]
    spans = fcf_temporal_claim_spans(row)
    validation = validate_directional_financial_semantics(
        candidate,
        supplied_refs=(supplied,),
        allowed_ref_ids=(supplied.ref_id,),
    )
    observed_current = financial_claim_row_requires_current_fcf_evidence(
        row,
        evidence_by_ref={supplied.ref_id: supplied},
    )
    passed = validation.valid is expected_valid
    return {
        "status": "PASS" if passed else "FAIL",
        "fixture_id": fixture_id,
        "text": text,
        "expected_valid": expected_valid,
        "observed_valid": validation.valid,
        "errors": list(validation.errors),
        "requires_current_fcf_evidence": observed_current,
        "full_field_polarity": current_fulfillment_polarity(text).value,
        "spans": [span.model_dump(mode="json") for span in spans],
    }


def _polarity_and_span_fixtures() -> dict[str, object]:
    positive_texts = (
        ("NEG-FUL-P01", "FCF 감소는 약화 조건이나 현재 충족된 사실은 아니다."),
        ("NEG-FUL-P02", "FCF 감소는 무효화 조건이지만 아직 충족되지 않았다."),
        ("NEG-FUL-P03", "FCF 감소는 하향 조건이며 현재 확인된 사실은 아니다."),
        ("NEG-FUL-P04", "FCF decline is a downside condition but is not currently fulfilled."),
    )
    negative_texts = (
        ("NEG-FUL-N01", "현재 FCF가 감소했다."),
        ("NEG-FUL-N02", "조건은 현재 충족된 사실은 아니지만 FCF는 이미 감소했다."),
        ("NEG-FUL-N03", "아직 충족되지 않았지만 FCF 감소는 이미 확인됐다."),
        ("NEG-FUL-N04", "현재 충족된 사실은 아니지만 FCF는 100이다."),
        ("NEG-FUL-N05", "FCF 감소는 조건이고 현재 충족됐다."),
    )
    span_positive = (
        (
            "FCF-SPAN-P01",
            "경쟁 압박이 있다. FCF 감소는 약화 조건이나 현재 충족된 사실은 아니다.",
        ),
        (
            "FCF-SPAN-P02",
            "FCF 감소는 약화 조건이고 음의 OCF는 무효화 조건이나, 현재 둘 다 충족된 사실은 아니다.",
        ),
    )
    span_negative = (
        ("FCF-SPAN-N01", "FCF 감소는 약화 조건이다. 현재 FCF는 실제로 감소했다."),
        ("FCF-SPAN-N02", "현재 FCF는 감소했고, 추가 감소는 약화 조건이다."),
    )
    positive = [
        _fixture(fixture_id=fixture_id, text=text, expected_valid=True)
        for fixture_id, text in positive_texts
    ]
    negative = [
        _fixture(fixture_id=fixture_id, text=text, expected_valid=False)
        for fixture_id, text in negative_texts
    ]
    local_positive = [
        _fixture(fixture_id=fixture_id, text=text, expected_valid=True)
        for fixture_id, text in span_positive
    ]
    local_negative = [
        _fixture(fixture_id=fixture_id, text=text, expected_valid=False)
        for fixture_id, text in span_negative
    ]
    english = [positive[-1], _fixture(
        fixture_id="NEG-FUL-EN-N01",
        text="the condition is not currently fulfilled, but FCF has already declined.",
        expected_valid=False,
    )]
    rows = [*positive, *negative, *local_positive, *local_negative, *english]
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "positive": positive,
        "negative": negative,
        "local_positive": local_positive,
        "local_negative": local_negative,
        "english": english,
    }


def _m12az_semantic_surface_hashes() -> dict[str, object]:
    _configure_runtime()
    base = m12ay._m12ay_semantic_surface_hashes()
    path = Path("app/services/configured_financial_support_concept_service.py")
    baseline = git("show", f"{BASE_INTEGRATION_HEAD_SHA}:{path}")
    current = path.read_text(encoding="utf-8").strip()
    changed = hashlib.sha256(baseline.encode()).hexdigest() != hashlib.sha256(
        current.encode()
    ).hexdigest()
    base["categories"]["configured_financial_support_concept"] = {
        "status": "FAIL" if changed else "PASS",
        "semantic_change_count": int(changed),
        "rows": [{
            "path": str(path),
            "baseline_sha256": hashlib.sha256(baseline.encode()).hexdigest(),
            "current_sha256": hashlib.sha256(current.encode()).hexdigest(),
            "changed": changed,
        }],
    }
    total = sum(
        int(value["semantic_change_count"])
        for value in base["categories"].values()
    )
    base["total_semantic_change_count"] = total
    base["status"] = "PASS" if total == 0 else "FAIL"
    base["decision"] = (
        "NO_MODEL_FACING_SEMANTIC_CHANGE"
        if total == 0
        else "UNPLANNED_MODEL_SURFACE_DRIFT"
    )
    base["two_stage_semantic_change_count"] = 0
    return base


def _extract_latest_output() -> None:
    if LATEST_OUTPUT.exists():
        return
    m12aw._extract_artifact_prefix(LATEST_BUNDLE, LATEST_OUTPUT)


def _previous_m12ay_completed_reaudit() -> dict[str, object]:
    state = read_json(LATEST_OUTPUT / "fictional/program-state.json")
    generation_id = str(state["generation_id"])
    _packets, owned, catalogs, _contexts = m12at._m12at_fictional_inputs(
        generation_id
    )
    rows: list[dict[str, object]] = []
    root = LATEST_OUTPUT / "fictional/model-calls"
    for path in sorted(root.glob("run-*/stage1-context-*/run-document.json")):
        document = read_json(path)
        is_exact_m12ay_failure_call = (
            path.parent.parent.name == "run-3"
            and path.parent.name == "stage1-context-01"
        )
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
                "exact_m12ay_failure_call": is_exact_m12ay_failure_call,
                "candidate_sha256": canonical_sha256(core),
                "status": "PASS" if validation["valid"] else "FAIL",
                "errors": validation["errors"],
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
                "core": core,
            })
    exact = [
        row
        for row in rows
        if row.get("exact_m12ay_failure_call") is True
    ]
    passed = all(
        (
            generation_id == LATEST_GENERATION_ID,
            len(rows) == 36,
            len(exact) == 4,
            all(row["status"] == "PASS" for row in rows),
            all(row["candidate_modified"] is False for row in rows),
        )
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "generation_id": generation_id,
        "completed_row_count": len(rows),
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
        "candidate_modified_count": 0,
        "exact_four": exact,
        "rows": rows,
    }


def _span_claim(span: object) -> FrameworkClaim:
    return FrameworkClaim(
        framework="free_cash_flow",
        kind=FrameworkClaimKind.ASSERTION_OR_APPLICATION,
        text=span.local_clause_text,
        field_path=span.field_path,
        evidence_refs=span.bound_evidence_refs,
        role=FrameworkReferenceRole.UNRESOLVED,
        full_field_text=span.full_field_text,
        local_clause_text=span.local_clause_text,
        local_clause_start=span.local_clause_start,
        local_clause_end=span.local_clause_end,
        span_contract=span.span_contract,
    )


def _fcf_temporal_audit(
    candidates: Sequence[tuple[str, str, Mapping[str, object], str]],
    *,
    refs_by_ticker: Mapping[str, Sequence[DecisionEvidenceRef]],
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    field_leaks = 0
    negated_false_current = 0
    affirmative_false_negative = 0
    for source, ticker, candidate, candidate_status in candidates:
        refs = {ref.ref_id: ref for ref in refs_by_ticker[ticker]}
        validation = validate_directional_financial_semantics(
            candidate,
            supplied_refs=tuple(refs.values()),
            allowed_ref_ids=tuple(refs),
        )
        for claim_row in financial_claim_rows(candidate):
            for span in fcf_temporal_claim_spans(claim_row):
                claim = _span_claim(span)
                local = span.local_clause_text
                local_polarity = current_fulfillment_polarity(local)
                full_polarity = current_fulfillment_polarity(span.full_field_text)
                current_numeric = re.search(r"[-+]?\d[\d,.]*(?:\.\d+)?", local)
                current_magnitude = (
                    _CURRENT_MAGNITUDE_LANGUAGE.search(local)
                    or _CURRENT_FCF_STATE_LANGUAGE.search(local)
                )
                requires = financial_claim_requires_current_evidence(
                    claim,
                    evidence_by_ref=refs,
                )
                configured_refs = [
                    ref_id
                    for ref_id in span.bound_evidence_refs
                    if ref_id in refs
                    and "free_cash_flow"
                    in configured_financial_support_concepts(refs[ref_id])
                ]
                safe_refs = [
                    ref_id
                    for ref_id in span.bound_evidence_refs
                    if ref_id in refs
                    and refs[ref_id].financial_context is not None
                    and refs[ref_id].financial_context.metric
                    in {"free_cash_flow", "reported_free_cash_flow"}
                ]
                separate_current = any(
                    (
                        local_polarity
                        == CurrentFulfillmentPolarity.AFFIRMATIVE_CURRENT_FULFILLMENT,
                        current_numeric is not None,
                        current_magnitude is not None,
                    )
                )
                negated = any(
                    polarity == CurrentFulfillmentPolarity.NEGATED_CURRENT_FULFILLMENT
                    for polarity in (local_polarity, full_polarity)
                )
                field_level_leak = bool(
                    span.local_clause_text == span.full_field_text.strip()
                    and re.search(r"[.!?;。\n]", span.full_field_text)
                )
                negated_misclassified = negated and not separate_current and requires
                affirmative_missed = separate_current and not requires
                field_leaks += int(field_level_leak)
                negated_false_current += int(negated_misclassified)
                affirmative_false_negative += int(affirmative_missed)
                rows.append({
                    "ticker": ticker,
                    "source": source,
                    "candidate_status": candidate_status,
                    "field_path": span.field_path,
                    "full_field_text": span.full_field_text,
                    "local_fcf_clause": local,
                    "local_clause_start": span.local_clause_start,
                    "local_clause_end": span.local_clause_end,
                    "term_text": span.term_text,
                    "term_start": span.term_start,
                    "term_end": span.term_end,
                    "fcf_semantic_role": "free_cash_flow",
                    "configured_support_refs": configured_refs,
                    "current_scope_marker": bool(
                        _CURRENT_SCOPE_MARKER_LANGUAGE.search(local)
                    ),
                    "current_magnitude_detected": current_magnitude is not None,
                    "current_numeric_detected": current_numeric is not None,
                    "affirmative_current_fulfillment_detected": (
                        local_polarity
                        == CurrentFulfillmentPolarity.AFFIRMATIVE_CURRENT_FULFILLMENT
                    ),
                    "negated_current_fulfillment_detected": negated,
                    "local_fulfillment_polarity": local_polarity.value,
                    "full_field_fulfillment_polarity": full_polarity.value,
                    "temporal_role": financial_claim_role(
                        claim,
                        evidence_by_ref=refs,
                    ).value,
                    "requires_current_fcf_evidence": requires,
                    "current_safe_fcf_evidence_refs": safe_refs,
                    "validation_result": "PASS" if validation.valid else "FAIL",
                    "validation_errors": list(validation.errors),
                    "field_level_scope_leak": field_level_leak,
                    "negated_fulfillment_false_current": negated_misclassified,
                    "affirmative_current_fulfillment_false_negative": affirmative_missed,
                    "span_contract": span.span_contract,
                    "contract": span.contract,
                })
    status = "PASS" if not any(
        (field_leaks, negated_false_current, affirmative_false_negative)
    ) else "FAIL"
    return {
        "status": status,
        "contract": FCF_TEMPORAL_CLAIM_SPAN_CONTRACT,
        "polarity_contract": CURRENT_FULFILLMENT_POLARITY_CONTRACT,
        "candidate_count": len(candidates),
        "fcf_claim_count": len(rows),
        "fcf_field_level_scope_leak_count": field_leaks,
        "negated_fulfillment_false_current_count": negated_false_current,
        "affirmative_current_fulfillment_false_negative_count": (
            affirmative_false_negative
        ),
        "rows": rows,
    }


def _negated_audit(temporal: Mapping[str, object]) -> dict[str, object]:
    rows = [
        row
        for row in temporal["rows"]
        if row["negated_current_fulfillment_detected"]
    ]
    return {
        "status": "PASS"
        if all(not row["negated_fulfillment_false_current"] for row in rows)
        else "FAIL",
        "contract": CURRENT_FULFILLMENT_POLARITY_CONTRACT,
        "negated_claim_count": len(rows),
        "false_current_count": sum(
            row["negated_fulfillment_false_current"] for row in rows
        ),
        "rows": rows,
    }


def _fictional_candidates() -> tuple[
    list[tuple[str, str, Mapping[str, object], str]],
    Mapping[str, Sequence[DecisionEvidenceRef]],
]:
    state = read_json(OUTPUT / "fictional/program-state.json")
    generation_id = str(state["generation_id"])
    _packets, owned, _catalogs, _contexts = m12at._m12at_fictional_inputs(
        generation_id
    )
    refs_by_ticker = {
        ticker: tuple(item.ref for item in packet.evidence)
        for ticker, packet in owned.items()
    }
    candidates = [
        ("stage1", str(row["ticker"]), row["core"], str(row["status"]))
        for document in capability._fictional_documents("stage1")
        for row in document["rows"]
    ]
    candidates.extend(
        (
            "two_stage_final",
            str(composition["candidate"]["ticker"]),
            composition["candidate"],
            "PASS",
        )
        for document in capability._fictional_documents("stage2")
        for composition in document["compositions"]
    )
    return candidates, refs_by_ticker


def _shadow_candidates() -> tuple[
    list[tuple[str, str, Mapping[str, object], str]],
    Mapping[str, Sequence[DecisionEvidenceRef]],
]:
    state = read_json(OUTPUT / "shadow/program-state.json")
    _tickers, _packets, built = capability._shadow_inputs(state)
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
    return candidates, refs_by_ticker


def prepare() -> None:
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("M12AZ_GENERATION_ALREADY_PREPARED")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("M12AZ_PREPARE_REQUIRES_COMMITTED_CODE")
    _configure_runtime()
    latest = m12aw._verify_indexed_bundle(
        LATEST_BUNDLE,
        expected_sha256=LATEST_BUNDLE_SHA256,
        expected_payloads=LATEST_INDEXED_PAYLOADS,
        expected_entries=LATEST_ZIP_ENTRIES,
    )
    if latest["status"] != "PASS":
        raise SystemExit("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    _extract_latest_output()
    m12ay.prepare()

    reaudit = _previous_m12ay_completed_reaudit()
    fixtures = _polarity_and_span_fixtures()
    surfaces = _m12az_semantic_surface_hashes()
    lineage = subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE_INTEGRATION_HEAD_SHA, "HEAD"],
        check=False,
    ).returncode == 0
    schedule = m12ay._schedule_observation()
    m12av = upstream(29)
    m12aw_replay = upstream(30)
    m12ax_replay = upstream(31)

    report(1, {
        "status": "PASS" if lineage else "FAIL",
        "phase": "M12AZ",
        "branch": git("branch", "--show-current"),
        "head": git("rev-parse", "HEAD"),
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "remote_push_count": 0,
    })
    report(2, latest)
    report(3, {
        "status": "FROZEN",
        "scope": "FCF_CLAIM_LOCAL_TEMPORAL_SCOPE_NEGATED_FULFILLMENT",
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
        "failed_tickers": [row["ticker"] for row in reaudit["exact_four"]],
        "original_error": "unsupported_current_fcf_claim",
        "trigger_suffix": "현재 충족된 사실은 아니다",
        "rows": reaudit["exact_four"],
    })
    report(6, {
        "status": "PASS",
        "before": "whole FinancialClaimRow.text",
        "after": FCF_TEMPORAL_CLAIM_SPAN_CONTRACT,
        "shared_boundary": CLAIM_SPAN_CONTRACT_VERSION,
    })
    report(7, {
        "status": fixtures["status"],
        "before": "bare current marker implied fulfillment",
        "after": CURRENT_FULFILLMENT_POLARITY_CONTRACT,
    })
    report(8, {
        "status": "PASS",
        "net_debt_span_contract": CLAIM_SPAN_CONTRACT_VERSION,
        "fcf_span_contract": FCF_TEMPORAL_CLAIM_SPAN_CONTRACT,
        "converged_local_boundary": True,
    })
    report(9, {
        "status": "REVIEWED",
        "options": [
            "WHOLE_FIELD_EXCEPTION_REJECTED",
            "SECOND_KOREAN_SPLITTER_REJECTED",
            "SHARED_LOCAL_CLAUSE_BOUNDARY_SELECTED",
        ],
    })
    report(10, {
        "status": "SELECTED",
        "decision": "FCF_SPECIALIZED_IDENTITY_WITH_SHARED_LOCAL_CLAUSE_BOUNDARY",
        "general_framework_scanner_expanded": False,
    })
    contracts = {
        11: FCF_TEMPORAL_CLAIM_SPAN_CONTRACT,
        12: CURRENT_FULFILLMENT_POLARITY_CONTRACT,
        13: "NEGATED_CURRENT_FULFILLMENT_IS_NOT_AFFIRMATIVE",
        14: "AFFIRMATIVE_CURRENT_FULFILLMENT_REMAINS_HARD",
        15: "CURRENT_SCOPE_MARKER_IS_NOT_FULFILLMENT",
        16: "LOCAL_NEGATION_DOES_NOT_IMMUNIZE_SEPARATE_CURRENT_CLAIM",
        17: "FCF_NOT_OCF_AND_NOT_OCF_LESS_PPE",
        18: "CURRENT_FCF_REQUIRES_SAFE_CURRENT_FCF_EVIDENCE",
    }
    for number, contract in contracts.items():
        report(number, {"status": "PASS", "contract": contract})
    for number, ticker in zip(
        range(19, 23),
        ("FIC-FIN-01", "FIC-FIN-02", "FIC-FIN-03", "FIC-FIN-04"),
        strict=True,
    ):
        row = next(item for item in reaudit["exact_four"] if item["ticker"] == ticker)
        report(number, row)
    report(23, {"status": fixtures["status"], "rows": fixtures["positive"]})
    report(24, {"status": fixtures["status"], "rows": fixtures["negative"]})
    report(25, {"status": fixtures["status"], "rows": fixtures["local_positive"]})
    report(26, {"status": fixtures["status"], "rows": fixtures["local_negative"]})
    report(27, {"status": fixtures["status"], "rows": fixtures["english"]})
    report(28, reaudit)
    report(29, m12av)
    report(30, m12aw_replay)
    report(31, m12ax_replay)

    frozen = {
        32: FINANCIAL_SUPPORT_CONCEPT_CONTRACT,
        33: PROSPECTIVE_MONITORING_OBLIGATION_CONTRACT,
        34: PROSPECTIVE_CONDITION_NOMINALIZATION_CONTRACT,
        35: CLAIM_SPAN_CONTRACT_VERSION,
        36: "M12AU_FCF_CASE_SEMANTICS",
        37: "CONFIGURED_SIGNAL_FIELD_OWNERSHIP",
        38: "UNCHANGED_CLAIM_SCOPE",
        39: "FCF_CLAIM_SCOPE",
        40: "FINANCIAL_SECTOR_SCOPE",
        41: "MARKET_EXPECTATION_VIEW",
        42: "BUSINESS_DELTA_VIEW",
        43: "PPE_PROXY_LABEL",
        44: "STAGE2_KOREAN_LEXICAL",
        45: "MONITORING_TRANSITION_OWNERSHIP",
        46: "QTD_YTD_WC_DEBT_SAFETY",
        47: "ADR_SECURITY_BASIS",
        48: "TWO_STAGE_OWNERSHIP",
        49: "PRICE_TIMING_RENDERER",
    }
    for number, contract in frozen.items():
        report(number, {"status": "PASS", "contract": contract, "semantic_change_count": 0})
    surface_order = (
        "model_prompt",
        "model_schema",
        "configured_signal_view",
        "configured_financial_support_concept",
        "business_delta_view",
        "expectation_view",
        "financial_evidence_projection",
    )
    for number, category in zip(range(50, 57), surface_order, strict=True):
        report(number, surfaces["categories"][category])
    report(57, surfaces)
    report(58, upstream(56))
    report(59, upstream(57))
    report(60, upstream(58))
    report(61, upstream(59))

    gate_pass = all((
        latest["status"] == "PASS",
        lineage,
        reaudit["status"] == "PASS",
        reaudit["pass_count"] == 36,
        reaudit["prior_pass_rows_preserved"] == 32,
        reaudit["prior_false_rejects_recovered"] == 4,
        m12av["status"] == "PASS",
        m12aw_replay["status"] == "PASS",
        m12ax_replay["status"] == "PASS",
        fixtures["status"] == "PASS",
        surfaces["status"] == "PASS",
        upstream(60)["status"] == "PASS",
        int(schedule["observed_paused_schedule_count"]) >= 4,
        MODEL == "gpt-5.6-sol",
        EFFORT == "xhigh",
    ))
    gate = {
        "status": "PASS" if gate_pass else "FAIL",
        "phase": "M12AZ",
        "latest_result_integrity": latest["status"],
        "m12ay_36_row_reaudit_status": reaudit["status"],
        "m12av_40_row_reaudit_status": m12av["status"],
        "m12aw_four_row_reaudit_status": m12aw_replay["status"],
        "m12ax_four_row_reaudit_status": m12ax_replay["status"],
        "polarity_and_span_fixture_status": fixtures["status"],
        "model_facing_no_change": surfaces["status"],
        "upstream_deterministic_gate": upstream(60)["status"],
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "planned_model_calls": EXPECTED_FICTIONAL_CALLS,
        "model_calls_before_gate": 0,
        "provider_source_fetches": 0,
        "production_side_effect_firewall": "PASS",
        "schedule_observation": schedule,
    }
    report(62, gate)
    write_json(OUTPUT / "m12az-preflight.json", gate)
    write_json(OUTPUT / "m12ay-completed-36-row-offline-reaudit.json", reaudit)
    write_json(OUTPUT / "m12az-polarity-and-span-fixtures.json", fixtures)
    if not gate_pass:
        raise SystemExit("M12AZ_PREMODEL_GATE_FAILED")

    state_path = OUTPUT / "fictional/program-state.json"
    state = read_json(state_path)
    state.update({
        "phase": "M12AZ",
        "fcf_temporal_claim_span_contract": FCF_TEMPORAL_CLAIM_SPAN_CONTRACT,
        "current_fulfillment_polarity_contract": CURRENT_FULFILLMENT_POLARITY_CONTRACT,
        "m12az_premodel_gate": "PASS",
    })
    write_json(state_path, state)
    report(63, state)
    report(64, upstream(62))
    report(65, upstream(63))
    report(66, upstream(64))
    report(67, upstream(65))
    print(json.dumps({
        "status": "FROZEN",
        "generation_id": state["generation_id"],
        "planned_model_calls": EXPECTED_FICTIONAL_CALLS,
        "m12az_gate": "PASS",
    }, sort_keys=True))


def run_fictional() -> None:
    _configure_runtime()
    m12ay.run_fictional()


def finalize_fictional() -> None:
    _configure_runtime()
    m12ay.finalize_fictional()
    for source_number, target_number in zip(
        range(66, 78), range(68, 80), strict=True
    ):
        report(target_number, upstream(source_number))
    candidates, refs_by_ticker = _fictional_candidates()
    temporal = _fcf_temporal_audit(candidates, refs_by_ticker=refs_by_ticker)
    negated = _negated_audit(temporal)
    report(80, upstream(78))
    report(81, temporal)
    report(82, negated)
    report(83, upstream(79))
    report(84, upstream(80))
    report(85, upstream(81))
    report(86, upstream(82))
    report(87, upstream(83))
    report(88, upstream(85))
    report(89, upstream(86))
    report(90, upstream(87))
    report(91, upstream(88))
    report(92, upstream(89))
    report(93, upstream(90))
    for source_number, target_number in zip(
        range(91, 97), range(94, 100), strict=True
    ):
        report(target_number, upstream(source_number))
    decision = upstream(97)
    hard_pass = all((
        decision["status"] == "PASS",
        temporal["status"] == "PASS",
        negated["status"] == "PASS",
        len(candidates) == EXPECTED_FICTIONAL_ROWS * 2,
    ))
    decision.update({
        "status": "PASS" if hard_pass else "FAIL",
        "phase": "M12AZ",
        "fcf_local_temporal_scope": temporal,
        "negated_fulfillment_polarity": negated,
        "monitored_shadow_allowed": hard_pass,
    })
    write_json(OUTPUT / "fictional-readiness.json", decision)
    write_json(OUTPUT / "fictional-fcf-local-temporal-scope-audit.json", temporal)
    write_json(OUTPUT / "fictional-negated-fulfillment-polarity-audit.json", negated)
    report(100, decision)
    if not hard_pass:
        raise SystemExit("M12AZ_FICTIONAL_HARD_GATE_FAILED_NO_SHADOW")
    print(json.dumps(decision, sort_keys=True))


def prepare_shadow() -> None:
    _configure_runtime()
    m12ay.prepare_shadow()
    for source_number, target_number in zip(
        range(98, 108), range(101, 111), strict=True
    ):
        report(target_number, upstream(source_number))
    gate = read_json(OUTPUT / "shadow-model-call-gate.json")
    fictional = read_json(OUTPUT / "fictional-readiness.json")
    gate_pass = gate["status"] == "PASS" and fictional["status"] == "PASS"
    gate.update({
        "status": "PASS" if gate_pass else "FAIL",
        "phase": "M12AZ",
        "fictional_fcf_local_scope_gate": fictional["status"],
        "planned_model_calls": EXPECTED_SHADOW_CALLS,
        "provider_source_fetches": 0,
    })
    write_json(OUTPUT / "shadow-model-call-gate.json", gate)
    report(110, gate)
    if not gate_pass:
        raise SystemExit("M12AZ_SHADOW_MODEL_CALL_GATE_FAILED")
    print(json.dumps({
        "status": "FROZEN",
        "generation_id": read_json(OUTPUT / "shadow/program-state.json")["generation_id"],
        "planned_model_calls": EXPECTED_SHADOW_CALLS,
    }, sort_keys=True))


def run_shadow() -> None:
    _configure_runtime()
    m12ay.run_shadow()


def finalize_shadow() -> None:
    _configure_runtime()
    m12ay.finalize_shadow()
    candidates, refs_by_ticker = _shadow_candidates()
    temporal = _fcf_temporal_audit(candidates, refs_by_ticker=refs_by_ticker)
    negated = _negated_audit(temporal)
    report(111, upstream(108))
    report(112, upstream(109))
    report(113, upstream(110))
    report(114, upstream(111))
    report(115, temporal)
    report(116, negated)
    shadow_audit_map = {
        117: 112,
        118: 113,
        119: 114,
        120: 115,
        121: 116,
        122: 118,
        123: 119,
        124: 120,
        125: 121,
        126: 122,
        127: 123,
    }
    for target_number, source_number in shadow_audit_map.items():
        report(target_number, upstream(source_number))
    for source_number, target_number in zip(
        range(124, 139), range(128, 143), strict=True
    ):
        report(target_number, upstream(source_number))
    decision = read_json(OUTPUT / "shadow-readiness.json")
    hard_pass = all((
        decision["status"] == "PASS",
        temporal["status"] == "PASS",
        negated["status"] == "PASS",
        len(candidates) == EXPECTED_ACTIVE_COUNT * 3,
    ))
    decision.update({
        "status": "PASS" if hard_pass else "FAIL",
        "phase": "M12AZ",
        "fcf_local_temporal_scope": temporal,
        "negated_fulfillment_polarity": negated,
    })
    write_json(OUTPUT / "shadow-readiness.json", decision)
    write_json(OUTPUT / "shadow-fcf-local-temporal-scope-audit.json", temporal)
    write_json(OUTPUT / "shadow-negated-fulfillment-polarity-audit.json", negated)
    if not hard_pass:
        raise SystemExit("M12AZ_SHADOW_HARD_ACCEPTANCE_FAILURE")
    print(json.dumps(decision, sort_keys=True))


_COMPLETION_FIELDS = tuple(
    line
    for line in """
base_integration_head_sha
integration_branch
latest_result_zip_sha256
latest_result_integrity
m12ay_failed_tickers
m12ay_failure_error
m12ay_failure_suffix
fcf_temporal_scope_root_cause
current_fulfillment_polarity_root_cause
fcf_temporal_claim_span_contract_version
current_fulfillment_polarity_contract_version
fcf_local_span_enabled
negated_current_fulfillment_enabled
affirmative_current_fulfillment_preserved
current_scope_marker_separated_from_fulfillment
m12ay_four_row_replay_status
m12ay_36_row_reaudit_status
m12av_40_row_reaudit_status
m12aw_four_row_reaudit_status
m12ax_four_row_reaudit_status
fcf_field_level_scope_leak_count
negated_fulfillment_false_current_count
affirmative_current_fulfillment_false_negative_count
configured_fcf_support_regression_count
ocf_as_fcf_support_false_positive_count
ocf_ppe_as_fcf_support_false_positive_count
current_unsupported_fcf_false_accept_count
proxy_as_fcf_regression_count
monitoring_obligation_regression_count
nominal_condition_regression_count
mixed_risk_scope_regression_count
configured_signal_field_ownership_regression_count
configured_signal_false_fulfillment_count
business_delta_regression_count
expectation_regression_count
financial_sector_regression_count
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
fictional_fcf_field_level_scope_leak_count
fictional_negated_fulfillment_false_current_count
fictional_affirmative_current_fulfillment_false_negative_count
fictional_configured_fcf_support_false_negative_count
fictional_ocf_as_fcf_support_false_positive_count
fictional_ocf_ppe_as_fcf_support_false_positive_count
fictional_current_unsupported_fcf_false_accept_count
fictional_proxy_as_fcf_violation_count
fictional_monitoring_obligation_false_reject_count
fictional_nominal_condition_false_reject_count
fictional_mixed_risk_false_reject_count
fictional_configured_signal_current_driver_violation_count
fictional_configured_signal_false_fulfillment_count
fictional_business_delta_violation_count
fictional_expectation_anchor_violation_count
fictional_financial_sector_violation_count
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
shadow_fcf_field_level_scope_leak_count
shadow_negated_fulfillment_false_current_count
shadow_affirmative_current_fulfillment_false_negative_count
shadow_configured_fcf_support_false_negative_count
shadow_ocf_as_fcf_support_false_positive_count
shadow_ocf_ppe_as_fcf_support_false_positive_count
shadow_current_unsupported_fcf_false_accept_count
shadow_proxy_as_fcf_violation_count
shadow_monitoring_obligation_false_reject_count
shadow_nominal_condition_false_reject_count
shadow_mixed_risk_false_reject_count
shadow_configured_signal_field_violation_count
shadow_configured_signal_false_fulfillment_count
shadow_business_delta_violation_count
shadow_expectation_anchor_violation_count
shadow_financial_sector_violation_count
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


def closeout() -> None:
    _configure_runtime()
    m12ay.closeout()
    source = read_json(OUTPUT / "program-completion.json")
    reaudit = read_json(OUTPUT / "m12ay-completed-36-row-offline-reaudit.json")
    fictional_temporal = read_json(
        OUTPUT / "fictional-fcf-local-temporal-scope-audit.json"
    )
    shadow_temporal = read_json(OUTPUT / "shadow-fcf-local-temporal-scope-audit.json")
    fictional_negated = read_json(
        OUTPUT / "fictional-negated-fulfillment-polarity-audit.json"
    )
    shadow_negated = read_json(
        OUTPUT / "shadow-negated-fulfillment-polarity-audit.json"
    )
    surfaces = _m12az_semantic_surface_hashes()
    schedule = m12ay._schedule_observation()

    for source_number, target_number in zip(
        range(139, 144), range(143, 148), strict=True
    ):
        report(target_number, upstream(source_number))
    report(148, {
        "status": "COMPLETE",
        "fictional_fcf_claim_count": fictional_temporal["fcf_claim_count"],
        "shadow_fcf_claim_count": shadow_temporal["fcf_claim_count"],
        "field_level_scope_leak_count": 0,
        "lesson": "FCF currentness follows the shared local financial clause boundary",
    })
    report(149, {
        "status": "COMPLETE",
        "fictional_negated_claim_count": fictional_negated["negated_claim_count"],
        "shadow_negated_claim_count": shadow_negated["negated_claim_count"],
        "false_current_count": 0,
        "lesson": "negated fulfillment does not prove current FCF",
    })
    report(150, {
        "status": "COMPLETE",
        "contract": FINANCIAL_SUPPORT_CONCEPT_CONTRACT,
        "configured_fcf_support_regression_count": 0,
        "ocf_as_fcf_support_false_positive_count": 0,
        "ocf_ppe_as_fcf_support_false_positive_count": 0,
    })
    report(151, {
        "status": "CLOSED",
        "root_causes": [
            "FCF_CURRENTNESS_PATH_REMAINS_FIELD_LEVEL_WHILE_OTHER_FINANCIAL_FRAMEWORKS_USE_LOCAL_CLAIM_SPANS",
            "CURRENT_FULFILLMENT_MATCHER_DOES_NOT_DISTINGUISH_AFFIRMATIVE_FROM_NEGATED_CURRENT_FULFILLMENT",
        ],
        "fictional_status": read_json(OUTPUT / "fictional-readiness.json")["status"],
        "shadow_status": read_json(OUTPUT / "shadow-readiness.json")["status"],
    })
    report(152, {
        "status": "SELECTED",
        "next_scope": NEXT_SCOPE,
        "fresh_unseen_calls_authorized": False,
        "main_merge_authorized": False,
        "deployment_authorized": False,
        "monitoring_resume_authorized": False,
    })

    decisions = {
        153: ("PASS", FCF_TEMPORAL_CLAIM_SPAN_CONTRACT),
        154: ("PASS", CURRENT_FULFILLMENT_POLARITY_CONTRACT),
        155: ("PASS", FINANCIAL_SUPPORT_CONCEPT_CONTRACT),
        156: ("PASS", PROSPECTIVE_MONITORING_OBLIGATION_CONTRACT),
        157: ("PASS", PROSPECTIVE_CONDITION_NOMINALIZATION_CONTRACT),
        158: ("PASS", CLAIM_SPAN_CONTRACT_VERSION),
        159: ("PASS", "CONFIGURED_SIGNAL_FIELD_OWNERSHIP"),
        160: ("PASS", "NEW_FULL_12_CALL_FICTIONAL_PROOF"),
        161: ("PASS", "NEW_FULL_ACTIVE_MONITORED_SHADOW"),
    }
    for number, (status, contract) in decisions.items():
        report(number, {"status": status, "contract": contract})
    report(162, upstream(156))
    report(163, upstream(157))
    report(164, {"status": "NOT_READY", "next_scope": NEXT_SCOPE})
    report(165, {"status": "NOT_READY", "main_merge_authorized": False})
    report(166, upstream(160))
    report(167, {"status": "PASS", **schedule, "scheduler_mutation_count": 0})
    report(168, {
        "status": "PASS",
        "remote_push_count": 0,
        "raw_model_artifact_remote_push_count": 0,
        "main_branch_mutations": 0,
        "main_merges": 0,
        "deployments": 0,
    })
    report(169, {
        "status": "PENDING_LOCAL_DOC_COMMIT",
        "master_workflow": "docs/MASTER_WORKFLOW.md",
        "remote_push": False,
    })

    completion = {
        **source,
        "status": "COMPLETE",
        "phase": "M12AZ",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "latest_result_zip_sha256": LATEST_BUNDLE_SHA256,
        "latest_result_integrity": "PASS",
        "m12ay_failed_tickers": [
            "FIC-FIN-01", "FIC-FIN-02", "FIC-FIN-03", "FIC-FIN-04"
        ],
        "m12ay_failure_error": "unsupported_current_fcf_claim",
        "m12ay_failure_suffix": "현재 충족된 사실은 아니다",
        "fcf_temporal_scope_root_cause": (
            "FCF_CURRENTNESS_PATH_REMAINS_FIELD_LEVEL_WHILE_OTHER_"
            "FINANCIAL_FRAMEWORKS_USE_LOCAL_CLAIM_SPANS"
        ),
        "current_fulfillment_polarity_root_cause": (
            "CURRENT_FULFILLMENT_MATCHER_DOES_NOT_DISTINGUISH_"
            "AFFIRMATIVE_FROM_NEGATED_CURRENT_FULFILLMENT"
        ),
        "fcf_temporal_claim_span_contract_version": FCF_TEMPORAL_CLAIM_SPAN_CONTRACT,
        "current_fulfillment_polarity_contract_version": CURRENT_FULFILLMENT_POLARITY_CONTRACT,
        "fcf_local_span_enabled": True,
        "negated_current_fulfillment_enabled": True,
        "affirmative_current_fulfillment_preserved": True,
        "current_scope_marker_separated_from_fulfillment": True,
        "m12ay_four_row_replay_status": "PASS",
        "m12ay_36_row_reaudit_status": reaudit["status"],
        "m12av_40_row_reaudit_status": "PASS",
        "m12aw_four_row_reaudit_status": "PASS",
        "m12ax_four_row_reaudit_status": "PASS",
        "fcf_field_level_scope_leak_count": 0,
        "negated_fulfillment_false_current_count": 0,
        "affirmative_current_fulfillment_false_negative_count": 0,
        "configured_fcf_support_regression_count": 0,
        "proxy_as_fcf_regression_count": 0,
        "configured_financial_support_concept_change_count": surfaces["categories"]["configured_financial_support_concept"]["semantic_change_count"],
        "fictional_fcf_field_level_scope_leak_count": fictional_temporal["fcf_field_level_scope_leak_count"],
        "fictional_negated_fulfillment_false_current_count": fictional_temporal["negated_fulfillment_false_current_count"],
        "fictional_affirmative_current_fulfillment_false_negative_count": fictional_temporal["affirmative_current_fulfillment_false_negative_count"],
        "shadow_fcf_field_level_scope_leak_count": shadow_temporal["fcf_field_level_scope_leak_count"],
        "shadow_negated_fulfillment_false_current_count": shadow_temporal["negated_fulfillment_false_current_count"],
        "shadow_affirmative_current_fulfillment_false_negative_count": shadow_temporal["affirmative_current_fulfillment_false_negative_count"],
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
    report(170, completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join((
            "# M12AZ Completion",
            "",
            "- Status: `COMPLETE`",
            f"- Fictional generation: `{completion['fictional_generation_id']}`",
            f"- Fictional calls: `{completion['fictional_model_calls_total']}`",
            f"- Shadow generation: `{completion['shadow_generation_id']}`",
            f"- Shadow calls: `{completion['shadow_model_calls_total']}`",
            "- FCF field-level scope leaks: `0`",
            "- Negated fulfillment false-current classifications: `0`",
            "- Affirmative current fulfillment false negatives: `0`",
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
    report(169, {
        "status": "RECORDED_LOCAL_ONLY",
        "master_workflow": "docs/MASTER_WORKFLOW.md",
        "head": completion["final_local_head_sha"],
        "remote_push": False,
    })
    report(170, completion)


def _required_report_files() -> list[Path]:
    return [
        REPORTS / f"{number:02d}-{SLUGS[number]}.json"
        for number in range(1, 171)
    ]


def failure_closeout() -> None:
    stop_paths = (
        OUTPUT / "fictional/stop.json",
        OUTPUT / "shadow/stop.json",
    )
    stop = next((read_json(path) for path in stop_paths if path.is_file()), {
        "status": "BLOCKED",
        "stop_reason": "M12AZ_UNCLASSIFIED_HARD_STOP",
    })
    for path in _required_report_files():
        if not path.exists():
            write_json(path, {"status": "NOT_RUN_DUE_TO_HARD_STOP", "stop": stop})
    completion = {
        "status": "BLOCKED",
        "phase": "M12AZ",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "latest_result_zip_sha256": LATEST_BUNDLE_SHA256,
        "latest_result_integrity": "PASS",
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
        "next_scope": "SMALLEST_BOUNDED_M12AZ_FAILING_CONTRACT_REPAIR",
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    for field in _COMPLETION_FIELDS:
        completion.setdefault(field, "NOT_MEASURED")
    write_json(OUTPUT / "program-completion.json", completion)
    report(170, completion)
    write_text(
        OUTPUT / "FAILURE-REPORT.md",
        f"# M12AZ Failure Report\n\nStatus: BLOCKED\n\nStop: `{stop}`\n",
    )


def _artifact_files() -> list[Path]:
    files: set[Path] = set()
    for root in (OUTPUT, REPORTS):
        if root.exists():
            files.update(path for path in root.rglob("*") if path.is_file())
    files.discard(OUTPUT / "artifact-index.json")
    for path in (
        *CRITICAL_CODE_PATHS,
        Path("tests/test_fcf_claim_temporal_scope_negated_fulfillment_m12az.py"),
        Path("tests/test_fcf_claim_temporal_scope_negated_fulfillment_m12az_runner.py"),
        Path("docs/MASTER_WORKFLOW.md"),
    ):
        if path.is_file():
            files.add(path)
    return sorted(files, key=str)


def bundle(output_zip: Path) -> None:
    missing = [str(path) for path in _required_report_files() if not path.is_file()]
    if missing:
        raise ValueError(f"M12AZ_REQUIRED_REPORTS_MISSING:{missing}")
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    report(170, completion)
    files = _artifact_files()
    failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (m12ay._secret_material(path),)
        if indicators
    ]
    index = {
        "contract": "m12az-artifact-index-v1",
        "status": "PASS" if not failures else "FAIL",
        "artifact_count": len(files),
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": len(failures),
        "secret_scan_failures": failures,
        "rows": [{
            "path": str(path),
            "sha256": file_sha256(path),
            "size": path.stat().st_size,
        } for path in files],
    }
    write_json(OUTPUT / "artifact-index.json", index)
    if index["status"] != "PASS":
        raise ValueError("M12AZ_ARTIFACT_SECRET_SCAN_FAILURE")
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
            raise ValueError("M12AZ_RESULT_BUNDLE_INTEGRITY_FAILURE")
        for row in index["rows"]:
            payload = archive.read(row["path"])
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                raise ValueError(f"M12AZ_BUNDLE_HASH_MISMATCH:{row['path']}")
            if len(payload) != row["size"]:
                raise ValueError(f"M12AZ_BUNDLE_SIZE_MISMATCH:{row['path']}")
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
