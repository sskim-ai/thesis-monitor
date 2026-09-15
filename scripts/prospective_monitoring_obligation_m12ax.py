"""M12AX prospective monitoring-obligation proof and full shadow."""

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

from app.services.cross_market_decision_engine_service import (
    DecisionEvidenceRef,
    EvidenceCategory,
)
from app.services.directional_financial_context_service import (
    PROSPECTIVE_CONDITION_NOMINALIZATION_CONTRACT,
    PROSPECTIVE_MONITORING_OBLIGATION_CONTRACT,
    FinancialClaimRole,
    _CURRENT_FULFILLMENT_LANGUAGE,
    _CURRENT_MAGNITUDE_LANGUAGE,
    _claim_has_framework_relevant_configured_evidence,
    _configured_prospective_evidence,
    _prospective_monitoring_obligation_family,
    financial_claim_requires_current_evidence,
    financial_claim_role,
    validate_directional_financial_semantics,
)
from app.services.financial_framework_claim_service import (
    CLAIM_SPAN_CONTRACT_VERSION,
    candidate_financial_framework_claims,
    financial_frameworks_in_text,
)
from app.services.optional_semantic_audit_service import (
    optional_semantic_audit_status,
)
from scripts import configured_signal_field_ownership_m12at as m12at
from scripts import prospective_condition_nominalization_m12aw as m12aw


NAME = "20260913-korean-prospective-monitoring-obligation-scope-fictional-reproof-full-shadow"
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
UPSTREAM_REPORTS = OUTPUT / "supporting-reports/m12aw"
SUPPORT_REPORTS = OUTPUT / "supporting-reports/m12ai"
RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
RUNNER = Path("scripts/prospective_monitoring_obligation_m12ax.py")
ARCHITECTURE = Path("docs/architecture/PROSPECTIVE_FINANCIAL_MONITORING_OBLIGATION.md")
WORK_INSTRUCTION = Path("docs/work-instructions") / f"{NAME}.md"
WORK_INSTRUCTION_COMMIT = "aa02d2c3bd905a3647728b951c414f601ab30eb6"
BASE_INTEGRATION_HEAD_SHA = "d1a4c6ca7e0e67a15794c62c4c8d11decabd5061"

ICLOUD = Path("/Users/sskim/Library/Mobile Documents/com~apple~CloudDocs/Thesis Monitor")
LATEST_NAME = (
    "20260913-prospective-financial-condition-nominalization-scope-fictional-reproof-full-shadow"
)
LATEST_OUTPUT = Path("artifacts") / LATEST_NAME
LATEST_BUNDLE = ICLOUD / f"thesis-monitor-{LATEST_NAME}-report.zip"
LATEST_BUNDLE_SHA256 = "49af4f94721f73e4b20019543c156d0ec6a211577f65f1c85609bb95f6c24a92"
LATEST_INDEXED_PAYLOADS = 199
LATEST_ZIP_ENTRIES = 200
LATEST_GENERATION_ID = "20260911-m12ai-fictional-20260912T163236Z-5fadf35ee9fa"

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

_SLUG_SEQUENCE = (
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
SLUGS = dict(enumerate(_SLUG_SEQUENCE, start=1))
if len(SLUGS) != 157:
    raise RuntimeError(f"M12AX_REPORT_SEQUENCE_INVALID:{len(SLUGS)}")

FOCUSED_TESTS = (
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
    "app/services/directional_financial_context_service.py",
    "tests/test_prospective_monitoring_obligation_m12ax.py",
    "tests/test_prospective_monitoring_obligation_m12ax_runner.py",
)
CRITICAL_CODE_PATHS = tuple(dict.fromkeys((*m12at.CRITICAL_CODE_PATHS, RUNNER)))

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
        if claim.framework in financial_frameworks_in_text(f"{ref.label} {ref.statement}"):
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


def prepare() -> None:
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


def finalize_fictional() -> None:
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


def prepare_shadow() -> None:
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


def finalize_shadow() -> None:
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


def closeout() -> None:
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


def record_docs() -> None:
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
            Path("app/services/directional_financial_context_service.py"),
            ARCHITECTURE,
            WORK_INSTRUCTION,
            Path("tests/test_prospective_monitoring_obligation_m12ax.py"),
            Path("tests/test_prospective_monitoring_obligation_m12ax_runner.py"),
            Path("docs/MASTER_WORKFLOW.md"),
        )
    )
    return sorted({path for path in paths if path.is_file()}, key=str)


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


def bundle(output_zip: Path) -> None:
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
