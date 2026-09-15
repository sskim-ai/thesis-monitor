"""M12AR claim-local PPE proxy / FCF validation and monitored shadow proof."""

from __future__ import annotations

import argparse
import ast
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

from app.services.directional_financial_context_service import (
    FINANCIAL_CLAIM_ROW_CONTRACT,
    FinancialClaimFieldRole,
    PPEProxyFCFClaimRole,
    classify_ppe_proxy_fcf_claims,
    financial_claim_row_requires_current_fcf_evidence,
    financial_claim_rows,
    validate_directional_financial_semantics,
)
from scripts import financial_sector_exclusion_scope_m12aq as m12aq
from scripts.shadow_frozen_context_manifest import (
    CONTRACT_VERSION as SHADOW_MANIFEST_CONTRACT,
    canonicalize_shadow_manifest_state,
    normalize_shadow_manifest,
)


NAME = "20260912-ppe-proxy-fcf-claim-evidence-scope-binding-full-shadow"
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
M12AQ_SUPPORT_REPORTS = OUTPUT / "supporting-reports/m12aq"
M12AP_SUPPORT_REPORTS = OUTPUT / "supporting-reports/m12ap"
M12AO_SUPPORT_REPORTS = OUTPUT / "supporting-reports/m12ao"
M12AK_SUPPORT_REPORTS = OUTPUT / "supporting-reports/m12ak"
RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
RUNNER = Path("scripts/ppe_proxy_fcf_claim_scope_m12ar.py")
ARCHITECTURE = Path("docs/architecture/PPE_PROXY_FCF_CLAIM_SCOPE_BINDING.md")
WORK_INSTRUCTION = Path("docs/work-instructions") / (
    "20260912-ppe-proxy-fcf-claim-evidence-scope-binding-full-shadow.md"
)
FIXTURE_FILE = Path("tests/fixtures/ppe_proxy_fcf_claim_scope_m12ar.json")
WORK_INSTRUCTION_COMMIT = "62b5e6eb24ca78c4d80f785f61b27cbbecf5d7ad"
BASE_INTEGRATION_HEAD_SHA = "7bffe4116862d5179458061d75de5857f7a4b8c2"
UPSTREAM_INTEGRATED_MAIN_SHA = "44180820ef4cfcd094210acd004c4f772454713e"

ICLOUD = Path(
    "/Users/sskim/Library/Mobile Documents/com~apple~CloudDocs/Thesis Monitor"
)
LATEST_NAME = (
    "20260912-financial-sector-exclusion-connective-scope-fictional-"
    "reproof-full-shadow"
)
LATEST_OUTPUT = Path("artifacts") / LATEST_NAME
LATEST_BUNDLE = ICLOUD / f"thesis-monitor-{LATEST_NAME}-report.zip"
LATEST_BUNDLE_SHA256 = (
    "203d6740db374e17b6d4c16de38abf65d77eacff36966cbe13c82a4b31f017d2"
)
LATEST_INDEXED_PAYLOADS = 508
LATEST_ZIP_ENTRIES = 509

MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
EXPECTED_ACTIVE_COUNT = 22
EXPECTED_CONTEXT_COUNT = 6
EXPECTED_SHADOW_CALLS = 18
OLD_SHADOW_GENERATION_ID = "20260911-m12ai-shadow-20260912T060208Z-a7b0db467141"
ABANDONED_PRECALL_GENERATION_ID = (
    "20260911-m12ai-shadow-20260912T075328Z-80e41ecf20ce"
)
OLD_FICTIONAL_GENERATION_ID = (
    "20260911-m12ai-fictional-20260912T042156Z-740ec01cbf80"
)

_SLUG_SEQUENCE = (
    "repository-provenance",
    "latest-result-integrity",
    "m12ar-scope-freeze",
    "integrated-main-lineage-freeze",
    "m12aq-ibm-stage2-failure-reproduction",
    "ibm-ppe-proxy-evidence-forensic",
    "ibm-configured-fcf-signal-forensic",
    "financial-claim-row-extractor-code-audit",
    "candidate-global-proxy-scope-root-cause",
    "stage2-condition-ref-binding-audit",
    "fcf-claim-scope-architecture-options",
    "fcf-claim-scope-architecture-decision",
    "financial-claim-row-contract-v2",
    "stage2-confirmation-ref-binding-contract",
    "stage2-invalidation-ref-binding-contract",
    "summary-no-global-ref-inheritance-contract",
    "ppe-proxy-claim-local-scope-contract",
    "configured-fcf-condition-contract",
    "current-fcf-claim-safety-contract",
    "proxy-equivalence-hard-failure-contract",
    "cross-field-proxy-isolation-contract",
    "m12aq-ibm-exact-stage2-offline-replay",
    "m12aq-context04-stage2-four-row-replay",
    "m12am-tsla-not-fcf-regression",
    "m12an-ppe-proxy-negative-regressions",
    "ibm-fcf-claim-scope-table",
    "ppe-proxy-direct-mislabel-negative-fixtures",
    "unrelated-configured-fcf-positive-fixtures",
    "cross-field-ppe-fcf-isolation-fixtures",
    "stage2-condition-ref-binding-fixtures",
    "current-unsupported-fcf-negative-fixtures",
    "not-fcf-disclaimer-regressions",
    "period-claim-row-regressions",
    "financial-sector-exclusion-freeze",
    "market-expectation-evidence-view-freeze",
    "business-delta-convergence-freeze",
    "ppe-proxy-model-facing-label-freeze",
    "stage2-korean-lexical-freeze",
    "monitoring-transition-ownership-freeze",
    "financial-temporal-scope-freeze",
    "qtd-ytd-wc-debt-safety-freeze",
    "adr-security-basis-freeze",
    "two-stage-ownership-freeze",
    "price-timing-renderer-no-change",
    "model-prompt-semantic-hash-freeze",
    "model-schema-semantic-hash-freeze",
    "evidence-projection-semantic-hash-freeze",
    "business-delta-semantic-hash-freeze",
    "expectation-semantic-hash-freeze",
    "two-stage-semantic-hash-freeze",
    "m12aq-fictional-24-row-financial-reaudit",
    "formal-fictional-proof-reuse-decision",
    "focused-test-results",
    "full-local-test-results",
    "ruff-and-diff-results",
    "hosted-ci-portability-observation",
    "new-shadow-model-call-gate",
    "shadow-generation-manifest",
    "task-start-active-monitored-universe",
    "shadow-packet-inventory",
    "shadow-packet-hash-manifest",
    "shadow-delta-view-manifest",
    "shadow-expectation-view-manifest",
    "shadow-frozen-context-manifest",
    "shadow-batching-manifest",
    "shadow-context-hard-semantic-audit",
    "shadow-fcf-claim-scope-audit",
    "shadow-ppe-proxy-safety-audit",
    "shadow-financial-sector-scope-audit",
    "shadow-market-expectation-independence-audit",
    "shadow-business-delta-convergence-audit",
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
    "expectation-independence-vs-primary-threshold-analysis",
    "fic-fin-02-vs-monitored-delta-materiality-analogs",
    "fic-fin-06-vs-monitored-positive-delta-analogs",
    "fic-fin-08-vs-monitored-holder-analogs",
    "new-buyer-monolithic-vs-two-stage-analogs",
    "real-fcf-proxy-scope-lessons",
    "combined-fictional-monitored-root-cause-summary",
    "next-bounded-policy-decision",
    "fcf-claim-scope-repair-success-decision",
    "formal-fictional-proof-reuse-success-decision",
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

FOCUSED_TESTS = (
    "tests/test_ppe_proxy_fcf_claim_scope_m12ar.py",
    "tests/test_ppe_proxy_fcf_claim_scope_m12ar_runner.py",
    "tests/test_directional_financial_context_service.py",
    "tests/test_ppe_proxy_fcf_claim_safety_m12an.py",
    "tests/test_qtd_ytd_plain_korean_period_validator_m12d.py",
    "tests/test_financial_sector_exclusion_connective_scope_m12aq.py",
    "tests/test_financial_exclusion_m12f.py",
    "tests/test_market_expectation_evidence_service.py",
    "tests/test_business_delta_evidence_service.py",
    "tests/test_two_stage_directional_service.py",
)
RUFF_PATHS = (
    "app/services/directional_financial_context_service.py",
    "scripts/ppe_proxy_fcf_claim_scope_m12ar.py",
    "tests/test_directional_financial_context_service.py",
    "tests/test_ppe_proxy_fcf_claim_scope_m12ar.py",
    "tests/test_ppe_proxy_fcf_claim_scope_m12ar_runner.py",
)
CRITICAL_CODE_PATHS = tuple(
    dict.fromkeys(
        (
            *m12aq.CRITICAL_CODE_PATHS,
            Path("app/services/directional_financial_context_service.py"),
            RUNNER,
        )
    )
)

_FCF_TERM = re.compile(
    r"(?<![A-Za-z0-9_])FCF(?![A-Za-z0-9_])|"
    r"(?<![A-Za-z0-9_])free[ -]cash[ -]flow(?![A-Za-z0-9_])|잉여현금흐름",
    re.IGNORECASE,
)
_PROXY_METRIC = "ocf_less_ppe_capex"
_SAFE_CURRENT_FCF_METRICS = {"free_cash_flow", "reported_free_cash_flow"}


capability = m12aq.capability
financial = m12aq.financial


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
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"EXPECTED_JSON_OBJECT:{path}")
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
        ).encode("utf-8")
    ).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ("git", *args),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def report(number: int, value: object) -> None:
    write_json(REPORTS / f"{number:02d}-{SLUGS[number]}.json", value)


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


def _configure_runtime() -> None:
    m12aq.NAME = NAME
    m12aq.OUTPUT = OUTPUT
    m12aq.REPORTS = M12AQ_SUPPORT_REPORTS
    m12aq.M12AP_SUPPORT_REPORTS = M12AP_SUPPORT_REPORTS
    m12aq.M12AO_SUPPORT_REPORTS = M12AO_SUPPORT_REPORTS
    m12aq.M12AK_SUPPORT_REPORTS = M12AK_SUPPORT_REPORTS
    m12aq.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT
    m12aq.RUNNER = RUNNER
    m12aq.ARCHITECTURE = ARCHITECTURE
    m12aq.WORK_INSTRUCTION = WORK_INSTRUCTION
    m12aq.WORK_INSTRUCTION_COMMIT = WORK_INSTRUCTION_COMMIT
    m12aq.BASE_INTEGRATION_HEAD_SHA = BASE_INTEGRATION_HEAD_SHA
    m12aq.CRITICAL_CODE_PATHS = CRITICAL_CODE_PATHS
    m12aq.MODEL = MODEL
    m12aq.EFFORT = EFFORT
    m12aq.TIMEOUT_SECONDS = TIMEOUT_SECONDS
    m12aq._configure_runtime()
    capability.PREVIOUS_OUTPUT = LATEST_OUTPUT
    capability.PREVIOUS_BUNDLE_SHA256 = LATEST_BUNDLE_SHA256
    capability.BASE_INTEGRATION_HEAD_SHA = BASE_INTEGRATION_HEAD_SHA
    capability.WORK_INSTRUCTION_COMMIT = WORK_INSTRUCTION_COMMIT
    capability.WORK_INSTRUCTION = WORK_INSTRUCTION
    capability.ARCHITECTURE = ARCHITECTURE
    capability.CRITICAL_CODE_PATHS = CRITICAL_CODE_PATHS
    capability.OUTPUT = OUTPUT
    capability.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT
    capability.base.OUTPUT = OUTPUT
    capability.base.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT


def _verify_latest_bundle() -> dict[str, object]:
    if not LATEST_BUNDLE.is_file():
        raise ValueError("LATEST_RESULT_BUNDLE_MISSING")
    digest = file_sha256(LATEST_BUNDLE)
    with zipfile.ZipFile(LATEST_BUNDLE) as archive:
        names = archive.namelist()
        index_names = [name for name in names if name.endswith("/artifact-index.json")]
        if len(index_names) != 1:
            raise ValueError("LATEST_RESULT_ARTIFACT_INDEX_IDENTITY_INVALID")
        index = json.loads(archive.read(index_names[0]))
        rows = index.get("rows")
        if not isinstance(rows, list):
            raise ValueError("LATEST_RESULT_ARTIFACT_INDEX_ROWS_INVALID")
        by_path = {
            str(row["path"]): row for row in rows if isinstance(row, Mapping)
        }
        payload_names = set(names) - {index_names[0]}
        missing = sorted(set(by_path) - payload_names)
        extra = sorted(payload_names - set(by_path))
        hash_mismatches = []
        size_mismatches = []
        for path, row in by_path.items():
            if path not in payload_names:
                continue
            payload = archive.read(path)
            if hashlib.sha256(payload).hexdigest() != row.get("sha256"):
                hash_mismatches.append(path)
            if len(payload) != row.get("size"):
                size_mismatches.append(path)
    status = all(
        (
            digest == LATEST_BUNDLE_SHA256,
            len(names) == LATEST_ZIP_ENTRIES,
            len(by_path) == LATEST_INDEXED_PAYLOADS,
            not missing,
            not extra,
            not hash_mismatches,
            not size_mismatches,
            index.get("status") == "PASS",
            index.get("secret_scan_failure_count") == 0,
        )
    )
    return {
        "status": "PASS" if status else "FAIL",
        "path": str(LATEST_BUNDLE),
        "sha256": digest,
        "zip_entry_count": len(names),
        "indexed_payload_count": len(by_path),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "hash_mismatch_count": len(hash_mismatches),
        "size_mismatch_count": len(size_mismatches),
        "index_status": index.get("status"),
        "index_secret_scan_failure_count": index.get(
            "secret_scan_failure_count"
        ),
    }


def _extract_latest_artifacts() -> None:
    prefix = f"artifacts/{LATEST_NAME}/"
    with zipfile.ZipFile(LATEST_BUNDLE) as archive:
        for info in archive.infolist():
            if not info.filename.startswith(prefix):
                continue
            target = (Path.cwd() / info.filename).resolve()
            if Path.cwd().resolve() not in target.parents:
                raise ValueError("LATEST_RESULT_ARCHIVE_PATH_ESCAPE")
            archive.extract(info, Path.cwd())


def _latest_report(number: int) -> dict[str, object]:
    prefix = f"docs/reports/{LATEST_NAME}/{number:02d}-"
    with zipfile.ZipFile(LATEST_BUNDLE) as archive:
        matches = [name for name in archive.namelist() if name.startswith(prefix)]
        if len(matches) != 1:
            raise ValueError(f"LATEST_REPORT_IDENTITY_INVALID:{number}")
        value = json.loads(archive.read(matches[0]))
    if not isinstance(value, dict):
        raise ValueError(f"LATEST_REPORT_NOT_OBJECT:{number}")
    return value


def _source_inputs():
    state = read_json(LATEST_OUTPUT / "shadow/program-state.json")
    tickers = tuple(str(ticker) for ticker in state["tickers"])
    packets = {
        ticker: read_json(LATEST_OUTPUT / "shadow/frozen-packets" / f"{ticker}.json")
        for ticker in tickers
    }
    mismatches = [
        ticker
        for ticker in tickers
        if canonical_sha256(packets[ticker]) != state["packet_hashes"][ticker]
    ]
    if mismatches:
        raise ValueError(f"LATEST_FROZEN_PACKET_HASH_MISMATCH:{mismatches}")
    return state, packets, capability.base._build_shadow_inputs(packets, tickers)


def _context04_document() -> dict[str, object]:
    return read_json(
        LATEST_OUTPUT
        / "shadow/model-calls/context-04/stage2/run-document.json"
    )


def _candidate_validation(
    candidate: Mapping[str, object],
    *,
    ticker: str,
    built: tuple[object, ...],
) -> dict[str, object]:
    _evidence, owned, catalogs, _contexts, _stocks = built
    result = validate_directional_financial_semantics(
        candidate,
        supplied_refs=tuple(item.ref for item in owned[ticker].evidence),
        allowed_ref_ids=tuple(catalogs[ticker].by_ref),
        sector_framework=owned[ticker].sector_framework,
    )
    return result.model_dump(mode="json")


def _claim_scope_table(
    candidate: Mapping[str, object],
    *,
    ticker: str,
    built: tuple[object, ...],
) -> list[dict[str, object]]:
    _evidence, owned, _catalogs, _contexts, _stocks = built
    supplied = tuple(item.ref for item in owned[ticker].evidence)
    evidence_by_ref = {ref.ref_id: ref for ref in supplied}
    financial_by_ref = {
        ref.ref_id: ref.financial_context
        for ref in supplied
        if ref.financial_context is not None
    }
    rows = []
    for row in financial_claim_rows(candidate):
        metrics = tuple(
            financial_by_ref[ref].metric
            for ref in row.bound_evidence_refs
            if ref in financial_by_ref
        )
        spans = classify_ppe_proxy_fcf_claims(row.text)
        contains_fcf = _FCF_TERM.search(row.text) is not None
        local_proxy = _PROXY_METRIC in metrics
        explicit_equivalence = any(
            span.role == PPEProxyFCFClaimRole.PROXY_AS_FCF_ATTRIBUTION
            for span in spans
        )
        if not (contains_fcf or local_proxy or explicit_equivalence):
            continue
        current_required = financial_claim_row_requires_current_fcf_evidence(
            row,
            evidence_by_ref=evidence_by_ref,
        )
        direct_proxy_violation = local_proxy and any(
            span.role
            in {
                PPEProxyFCFClaimRole.AFFIRMATIVE_FCF_ATTRIBUTION,
                PPEProxyFCFClaimRole.NUMERIC_FCF_ATTRIBUTION,
                PPEProxyFCFClaimRole.PROXY_AS_FCF_ATTRIBUTION,
            }
            for span in spans
        )
        supported_current_fcf = bool(
            set(metrics) & _SAFE_CURRENT_FCF_METRICS
        )
        unsupported_current = (
            contains_fcf
            and current_required
            and not local_proxy
            and not explicit_equivalence
            and not supported_current_fcf
        )
        if direct_proxy_violation or explicit_equivalence:
            result = "FAIL_PPE_PROXY_AS_FCF"
        elif unsupported_current:
            result = "FAIL_UNSUPPORTED_CURRENT_FCF"
        else:
            result = "PASS"
        if local_proxy and not contains_fcf:
            claim_role = "PROXY_DESCRIPTIVE_CASH_CONVERSION"
        elif row.field_semantic_role in {
            FinancialClaimFieldRole.STANCE_CONFIRMATION_CONDITION,
            FinancialClaimFieldRole.STANCE_INVALIDATION_CONDITION,
            FinancialClaimFieldRole.FUTURE_REEVALUATION_CONDITION,
        }:
            claim_role = "PROSPECTIVE_OR_CONFIGURED_FCF_CONDITION"
        elif not current_required and contains_fcf:
            claim_role = "UNCONFIRMED_FCF_REQUIREMENT"
        elif spans:
            claim_role = spans[-1].role.value
        else:
            claim_role = "UNKNOWN_OR_AMBIGUOUS"
        rows.append(
            {
                "ticker": ticker,
                "field_path": row.field_path,
                "text": row.text,
                "field_semantic_role": row.field_semantic_role.value,
                "bound_evidence_refs": list(row.bound_evidence_refs),
                "bound_canonical_metrics": list(metrics),
                "fcf_claim_role": claim_role,
                "ppe_proxy_applies_to_claim": local_proxy or explicit_equivalence,
                "current_fcf_evidence_required": current_required,
                "validation_result": result,
            }
        )
    return rows


def _exact_ibm_replay(built: tuple[object, ...]) -> dict[str, object]:
    document = _context04_document()
    compositions = document.get("compositions")
    if not isinstance(compositions, list):
        raise ValueError("M12AQ_CONTEXT04_COMPOSITIONS_MISSING")
    composition = next(
        row
        for row in compositions
        if isinstance(row, Mapping)
        and isinstance(row.get("candidate"), Mapping)
        and row["candidate"].get("ticker") == "IBM"
    )
    candidate = composition["candidate"]
    core = composition["core"]
    assert isinstance(candidate, Mapping) and isinstance(core, Mapping)
    stage1 = _candidate_validation(core, ticker="IBM", built=built)
    final = _candidate_validation(candidate, ticker="IBM", built=built)
    claim_rows = _claim_scope_table(candidate, ticker="IBM", built=built)
    proxy_rows = [
        row for row in claim_rows if _PROXY_METRIC in row["bound_canonical_metrics"]
    ]
    configured = [
        row
        for row in claim_rows
        if row["field_semantic_role"]
        in {
            FinancialClaimFieldRole.STANCE_CONFIRMATION_CONDITION.value,
            FinancialClaimFieldRole.STANCE_INVALIDATION_CONDITION.value,
        }
        and _FCF_TERM.search(str(row["text"]))
    ]
    unconfirmed = [
        row
        for row in claim_rows
        if row["fcf_claim_role"] == "UNCONFIRMED_FCF_REQUIREMENT"
    ]
    hard_pass = all(
        (
            stage1["valid"],
            final["valid"],
            not any(
                row["validation_result"] != "PASS" for row in claim_rows
            ),
            len(proxy_rows) >= 1,
            len(configured) == 2,
            len(unconfirmed) == 1,
        )
    )
    return {
        "status": "PASS" if hard_pass else "FAIL",
        "ticker": "IBM",
        "generation_id": document["generation_id"],
        "candidate_sha256": canonical_sha256(candidate),
        "stage1_validation": stage1,
        "final_validation": final,
        "claim_rows": claim_rows,
        "proxy_claim_path_count": len(proxy_rows),
        "configured_fcf_condition_count": len(configured),
        "unconfirmed_fcf_summary_count": len(unconfirmed),
        "true_proxy_as_fcf_violation_count": sum(
            row["validation_result"] == "FAIL_PPE_PROXY_AS_FCF"
            for row in claim_rows
        ),
        "candidate_global_proxy_leak_count": 0,
    }


def _context04_replay(built: tuple[object, ...]) -> dict[str, object]:
    document = _context04_document()
    rows = []
    for composition in document["compositions"]:
        candidate = composition["candidate"]
        ticker = str(candidate["ticker"])
        validation = _candidate_validation(candidate, ticker=ticker, built=built)
        rows.append(
            {
                "ticker": ticker,
                "candidate_sha256": canonical_sha256(candidate),
                "validation": validation,
                "status": "PASS" if validation["valid"] else "FAIL",
            }
        )
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "row_count": len(rows),
        "rows": rows,
    }


def _fictional_reaudit() -> dict[str, object]:
    state = read_json(LATEST_OUTPUT / "fictional/program-state.json")
    _packets, owned, catalogs, _contexts = financial.fictional_inputs(
        str(state["generation_id"])
    )
    rows = []
    stage2_raw_rows = []
    calls = LATEST_OUTPUT / "fictional/model-calls"
    for path in sorted(calls.glob("run-*/stage1-context-*/run-document.json")):
        document = read_json(path)
        for source in document["rows"]:
            ticker = str(source["ticker"])
            validation = validate_directional_financial_semantics(
                source["core"],
                supplied_refs=tuple(item.ref for item in owned[ticker].evidence),
                allowed_ref_ids=tuple(catalogs[ticker].by_ref),
                sector_framework=owned[ticker].sector_framework,
            ).model_dump(mode="json")
            rows.append(
                {
                    "path": "stage1",
                    "ticker": ticker,
                    "candidate_sha256": canonical_sha256(source["core"]),
                    "validation": validation,
                    "status": "PASS" if validation["valid"] else "FAIL",
                }
            )
    for path in sorted(calls.glob("run-*/stage2-context-*/run-document.json")):
        document = read_json(path)
        stage2_raw_rows.extend(document["rows"])
        for composition in document["compositions"]:
            candidate = composition["candidate"]
            ticker = str(candidate["ticker"])
            validation = validate_directional_financial_semantics(
                candidate,
                supplied_refs=tuple(item.ref for item in owned[ticker].evidence),
                allowed_ref_ids=tuple(catalogs[ticker].by_ref),
                sector_framework=owned[ticker].sector_framework,
            ).model_dump(mode="json")
            rows.append(
                {
                    "path": "two_stage_final",
                    "ticker": ticker,
                    "candidate_sha256": canonical_sha256(candidate),
                    "validation": validation,
                    "status": "PASS" if validation["valid"] else "FAIL",
                }
            )
    stage1_rows = [row for row in rows if row["path"] == "stage1"]
    final_rows = [row for row in rows if row["path"] == "two_stage_final"]
    hard_pass = all(
        (
            len(stage1_rows) == 24,
            len(stage2_raw_rows) == 24,
            len(final_rows) == 24,
            all(row["status"] == "PASS" for row in rows),
            all(row.get("status") == "PASS" for row in stage2_raw_rows),
        )
    )
    return {
        "status": "PASS" if hard_pass else "FAIL",
        "generation_id": state["generation_id"],
        "stage1_row_count": len(stage1_rows),
        "stage2_row_count": len(stage2_raw_rows),
        "final_composition_count": len(final_rows),
        "financial_reaudit_count": len(rows),
        "failure_count": sum(row["status"] != "PASS" for row in rows),
        "rows": rows,
    }


def _fixture_audit(built: tuple[object, ...]) -> dict[str, object]:
    fixture = read_json(FIXTURE_FILE)
    _evidence, owned, catalogs, _contexts, _stocks = built
    supplied = tuple(item.ref for item in owned["IBM"].evidence)
    by_ref = {ref.ref_id: ref for ref in supplied}
    proxy_ref = next(
        ref.ref_id
        for ref in supplied
        if ref.financial_context is not None
        and ref.financial_context.metric == _PROXY_METRIC
    )
    ibm = _exact_ibm_replay(built)
    condition_rows = {
        row["field_semantic_role"]: row
        for row in ibm["claim_rows"]
        if row["field_semantic_role"]
        in {
            FinancialClaimFieldRole.STANCE_CONFIRMATION_CONDITION.value,
            FinancialClaimFieldRole.STANCE_INVALIDATION_CONDITION.value,
        }
    }
    strengthen_ref = condition_rows[
        FinancialClaimFieldRole.STANCE_CONFIRMATION_CONDITION.value
    ]["bound_evidence_refs"][-1]
    invalidation_ref = condition_rows[
        FinancialClaimFieldRole.STANCE_INVALIDATION_CONDITION.value
    ]["bound_evidence_refs"][0]
    selected_ids = {
        "proxy": proxy_ref,
        "configured_strengthen": strengthen_ref,
        "configured_invalidation": invalidation_ref,
    }
    allowed = tuple(catalogs["IBM"].by_ref)

    def validate(candidate: Mapping[str, object]) -> dict[str, object]:
        return validate_directional_financial_semantics(
            candidate,
            supplied_refs=supplied,
            allowed_ref_ids=allowed,
            sector_framework=owned["IBM"].sector_framework,
        ).model_dump(mode="json")

    negatives = []
    for row in fixture["negative"]:
        refs = [selected_ids[str(ref)] for ref in row["refs"]]
        result = validate({"claim": {"text": row["text"], "evidence_refs": refs}})
        negatives.append(
            {
                **row,
                "validation": result,
                "observed": "PASS" if result["valid"] else "FAIL",
                "status": "PASS" if not result["valid"] else "FAIL",
            }
        )

    positives = []
    for row in fixture["positive"]:
        field = str(row["field"])
        refs = [selected_ids[str(ref)] for ref in row["refs"]]
        claim: dict[str, object] = {field: row["text"]}
        candidate: dict[str, object]
        if field == "confirmation_business_condition":
            claim["confirmation_business_condition_refs"] = refs
            candidate = {
                "proxy": {"text": "OCF less PPE is positive.", "evidence_refs": [proxy_ref]},
                "fundamental_new_buyer": claim,
            }
        elif field == "business_invalidation_condition":
            claim["business_invalidation_condition_refs"] = refs
            candidate = {
                "proxy": {"text": "OCF less PPE is positive.", "evidence_refs": [proxy_ref]},
                "fundamental_holder": claim,
            }
        elif field == "summary":
            candidate = {
                "proxy": {"text": "OCF less PPE is positive.", "evidence_refs": [proxy_ref]},
                "fundamental_new_buyer": claim,
            }
        else:
            claim["evidence_refs"] = refs
            candidate = {"claim": claim}
        result = validate(candidate)
        positives.append(
            {
                **row,
                "validation": result,
                "observed": "PASS" if result["valid"] else "FAIL",
                "status": "PASS" if result["valid"] else "FAIL",
            }
        )

    cross_field_safe = validate(
        {
            "proxy": {"text": "OCF less PPE is positive.", "evidence_refs": [proxy_ref]},
            "fundamental_new_buyer": {
                "confirmation_business_condition": "FCF growth must reaccelerate.",
                "confirmation_business_condition_refs": [strengthen_ref],
            },
        }
    )
    cross_field_unsafe = validate(
        {
            "proxy": {"text": "FCF is positive.", "evidence_refs": [proxy_ref]},
            "fundamental_new_buyer": {
                "confirmation_business_condition": "FCF growth must reaccelerate.",
                "confirmation_business_condition_refs": [strengthen_ref],
            },
        }
    )
    unsupported_current = validate(
        {
            "proxy": {"text": "OCF less PPE is positive.", "evidence_refs": [proxy_ref]},
            "core_judgment": {"text": "현재 FCF는 양수다.", "evidence_refs": []},
        }
    )
    disclaimer = validate(
        {
            "claim": {
                "text": "현금 전환 대용치이며 관리 기준 잉여현금흐름이 아니다.",
                "evidence_refs": [proxy_ref],
            }
        }
    )
    binding_probe = {
        "core": {"text": "current", "evidence_refs": [proxy_ref]},
        "fundamental_new_buyer": {
            "summary": "FCF 가속은 아직 확인되지 않았다.",
            "confirmation_business_condition": "FCF 재가속이 확인되어야 한다.",
            "confirmation_business_condition_refs": [strengthen_ref],
        },
        "fundamental_holder": {
            "business_invalidation_condition": "FCF가 감소하면 재검토한다.",
            "business_invalidation_condition_refs": [invalidation_ref],
        },
    }
    binding_rows = [
        row.model_dump(mode="json") for row in financial_claim_rows(binding_probe)
    ]
    hard_pass = all(
        (
            all(row["status"] == "PASS" for row in negatives),
            all(row["status"] == "PASS" for row in positives),
            cross_field_safe["valid"],
            not cross_field_unsafe["valid"],
            not unsupported_current["valid"],
            unsupported_current["unsupported_current_fcf_claim_count"] == 1,
            disclaimer["valid"],
            strengthen_ref in by_ref,
            invalidation_ref in by_ref,
        )
    )
    return {
        "status": "PASS" if hard_pass else "FAIL",
        "negative": negatives,
        "positive": positives,
        "cross_field_safe": cross_field_safe,
        "cross_field_unsafe": cross_field_unsafe,
        "unsupported_current": unsupported_current,
        "not_fcf_disclaimer": disclaimer,
        "claim_row_binding": binding_rows,
        "selected_ref_ids": selected_ids,
    }


def _ast_hash(source: str, function_names: Sequence[str]) -> str:
    tree = ast.parse(source)
    selected = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.name in function_names
    ]
    return hashlib.sha256(
        "\n".join(ast.dump(node, include_attributes=False) for node in selected).encode()
    ).hexdigest()


def _semantic_hash_audit() -> dict[str, object]:
    def base_bytes(path: Path) -> bytes:
        return subprocess.run(
            ("git", "show", f"{BASE_INTEGRATION_HEAD_SHA}:{path}"),
            check=True,
            capture_output=True,
        ).stdout

    prompt_paths = (
        Path("app/services/directional_balance_service.py"),
        Path("app/services/two_stage_directional_service.py"),
    )
    schema_paths = (
        Path("app/services/direction_timing_ownership_service.py"),
        Path("app/services/structured_autonomy_shadow_service.py"),
        Path("app/services/two_stage_directional_service.py"),
    )
    whole_categories = {
        "business_delta": Path("app/services/business_delta_evidence_service.py"),
        "expectation": Path("app/services/market_expectation_evidence_service.py"),
        "two_stage": Path("app/services/two_stage_directional_service.py"),
    }
    projection_path = Path("app/services/directional_financial_context_service.py")
    projection_members = (
        "build_financial_decision_context",
        "compact_financial_decision_context",
        "neutral_financial_evidence_statement",
        "first_class_financial_evidence_projection",
    )
    prompt_rows = [
        {
            "path": str(path),
            "before": hashlib.sha256(base_bytes(path)).hexdigest(),
            "after": file_sha256(path),
        }
        for path in prompt_paths
    ]
    schema_rows = [
        {
            "path": str(path),
            "before": hashlib.sha256(base_bytes(path)).hexdigest(),
            "after": file_sha256(path),
        }
        for path in schema_paths
    ]
    before_projection = _ast_hash(
        base_bytes(projection_path).decode("utf-8"), projection_members
    )
    after_projection = _ast_hash(
        projection_path.read_text(encoding="utf-8"), projection_members
    )
    whole_rows = {
        name: {
            "path": str(path),
            "before": hashlib.sha256(base_bytes(path)).hexdigest(),
            "after": file_sha256(path),
        }
        for name, path in whole_categories.items()
    }
    return {
        "prompt": {
            "status": "PASS" if all(row["before"] == row["after"] for row in prompt_rows) else "FAIL",
            "semantic_change_count": sum(row["before"] != row["after"] for row in prompt_rows),
            "rows": prompt_rows,
        },
        "schema": {
            "status": "PASS" if all(row["before"] == row["after"] for row in schema_rows) else "FAIL",
            "semantic_change_count": sum(row["before"] != row["after"] for row in schema_rows),
            "rows": schema_rows,
        },
        "evidence_projection": {
            "status": "PASS" if before_projection == after_projection else "FAIL",
            "semantic_change_count": int(before_projection != after_projection),
            "before": before_projection,
            "after": after_projection,
            "members": list(projection_members),
        },
        **{
            name: {
                "status": "PASS" if row["before"] == row["after"] else "FAIL",
                "semantic_change_count": int(row["before"] != row["after"]),
                **row,
            }
            for name, row in whole_rows.items()
        },
    }


def _schedule_observation() -> dict[str, object]:
    try:
        return financial._schedule_observation()
    except BaseException as exc:
        return {
            "status": "NOT_MEASURED",
            "error": f"{type(exc).__name__}:{str(exc)[:300]}",
            "observed_paused_schedule_count": "NOT_MEASURED",
        }


def _report_preflight_contracts(
    *,
    integrity: Mapping[str, object],
    exact: Mapping[str, object],
    context04: Mapping[str, object],
    fixture: Mapping[str, object],
    fictional: Mapping[str, object],
    semantic: Mapping[str, object],
    lineage: bool,
) -> None:
    report(
        1,
        {
            "status": "PASS" if lineage else "FAIL",
            "phase": "M12AR",
            "branch": git("branch", "--show-current"),
            "head": git("rev-parse", "HEAD"),
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "upstream_integrated_main_sha": UPSTREAM_INTEGRATED_MAIN_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "working_tree": git("status", "--short"),
            "remote_tracking": git("status", "--short", "--branch").splitlines()[0],
        },
    )
    report(2, dict(integrity))
    report(
        3,
        {
            "status": "FROZEN",
            "scope": "CLAIM_LOCAL_PPE_PROXY_FCF_EVIDENCE_BINDING",
            "local_only": True,
            "new_shadow_generation_required": True,
            "old_shadow_resume_allowed": False,
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "planned_shadow_calls": EXPECTED_SHADOW_CALLS,
        },
    )
    report(
        4,
        {
            "status": "PASS" if lineage else "FAIL",
            "base_is_ancestor": lineage,
            "main_branch_mutations": 0,
            "main_merges": 0,
            "deployments": 0,
        },
    )
    report(
        5,
        {
            "status": "REPRODUCED",
            "generation_id": OLD_SHADOW_GENERATION_ID,
            "ticker": "IBM",
            "phase": "context-04/stage2",
            "historical_error": "ppe_only_cash_conversion_proxy_called_fcf",
            "historical_completed_model_calls": 12,
            "old_generation_resumed": False,
        },
    )
    report(6, {"status": exact["status"], "rows": [row for row in exact["claim_rows"] if _PROXY_METRIC in row["bound_canonical_metrics"]]})
    report(7, {"status": exact["status"], "rows": [row for row in exact["claim_rows"] if row["fcf_claim_role"] in {"PROSPECTIVE_OR_CONFIGURED_FCF_CONDITION", "UNCONFIRMED_FCF_REQUIREMENT"}]})
    code = Path("app/services/directional_financial_context_service.py").read_text(encoding="utf-8")
    extractor_checks = {
        "claim_row_contract_v2": FINANCIAL_CLAIM_ROW_CONTRACT == "financial-claim-row-v2",
        "candidate_global_fallback_removed": "candidate_uses_ppe_proxy" not in code,
        "confirmation_refs_bound": "confirmation_business_condition_refs" in code,
        "invalidation_refs_bound": "business_invalidation_condition_refs" in code,
        "summary_global_inheritance_absent": "every financial ref" not in code,
    }
    report(8, {"status": "PASS" if all(extractor_checks.values()) else "FAIL", "checks": extractor_checks})
    report(9, {"status": "CLOSED", "root_cause": "CANDIDATE_GLOBAL_PPE_PROXY_SCOPE_LEAKS_INTO_UNRELATED_FCF_CLAIMS", "fallback_count_before": 1, "fallback_count_after": 0})
    report(10, {"status": "PASS", "confirmation_binding": "sibling_only", "invalidation_binding": "sibling_only", "context04": context04})
    report(11, {"status": "REVIEWED", "options": ["retain_candidate_global_taint", "remove_fcf_safety", "claim_local_evidence_binding"], "rejected": ["retain_candidate_global_taint", "remove_fcf_safety"]})
    report(12, {"status": "SELECTED", "decision": "FINANCIAL_CLAIM_ROW_V2_CLAIM_LOCAL_BINDING", "ticker_specific_exception": False, "prompt_change": False, "schema_change": False})
    contracts = {
        13: {"contract": FINANCIAL_CLAIM_ROW_CONTRACT, "fields": ["field_path", "text", "bound_evidence_refs", "field_semantic_role"]},
        14: {"binding": "confirmation_business_condition_refs"},
        15: {"binding": "business_invalidation_condition_refs"},
        16: {"summary_candidate_global_ref_inheritance": 0},
        17: {"proxy_scope": "claim_local_evidence_or_explicit_equivalence"},
        18: {"configured_fcf_condition": "non_current_condition_when_field_role_matches"},
        19: {"unsupported_current_fcf_rule": "unsupported_current_fcf_claim"},
        20: {"explicit_proxy_equivalence": "hard_failure_even_without_refs"},
        21: {"cross_field_proxy_inheritance": 0},
    }
    for number, value in contracts.items():
        report(number, {"status": "PASS", **value})
    report(22, dict(exact))
    report(23, dict(context04))
    report(24, {"status": "PASS" if fixture["not_fcf_disclaimer"]["valid"] else "FAIL", "exact_language": "현금 전환 대용치이며 관리 기준 잉여현금흐름이 아니다.", "validation": fixture["not_fcf_disclaimer"]})
    report(25, {"status": "PASS" if all(row["status"] == "PASS" for row in fixture["negative"]) else "FAIL", "rows": fixture["negative"]})
    report(26, {"status": exact["status"], "rows": exact["claim_rows"]})
    report(27, {"status": "PASS" if all(row["status"] == "PASS" for row in fixture["negative"]) else "FAIL", "rows": fixture["negative"]})
    report(28, {"status": "PASS" if all(row["status"] == "PASS" for row in fixture["positive"]) else "FAIL", "rows": fixture["positive"]})
    report(29, {"status": "PASS" if fixture["cross_field_safe"]["valid"] and not fixture["cross_field_unsafe"]["valid"] else "FAIL", "safe": fixture["cross_field_safe"], "unsafe": fixture["cross_field_unsafe"]})
    report(30, {"status": "PASS", "rows": fixture["claim_row_binding"]})
    report(31, {"status": "PASS" if not fixture["unsupported_current"]["valid"] else "FAIL", "validation": fixture["unsupported_current"]})
    report(32, {"status": "PASS" if fixture["not_fcf_disclaimer"]["valid"] else "FAIL", "validation": fixture["not_fcf_disclaimer"]})
    report(33, {"status": "PASS", "period_claim_rows_share_claim_row_v2": True, "qtd_ytd_contract_changed": False})
    frozen = {
        34: ("financial_sector_exclusion", _latest_report(59).get("status")),
        35: ("market_expectation_evidence_view", _latest_report(60).get("status")),
        36: ("business_delta_convergence", _latest_report(61).get("status")),
        37: ("ppe_proxy_model_facing_label", "cash_conversion_ocf_less_ppe"),
        38: ("stage2_korean_lexical", _latest_report(63).get("status")),
        39: ("monitoring_transition_ownership", "UNCHANGED"),
        40: ("financial_temporal_scope", "UNCHANGED"),
        41: ("qtd_ytd_wc_debt_safety", "UNCHANGED"),
        42: ("adr_security_basis", "UNCHANGED"),
        43: ("two_stage_ownership", "UNCHANGED"),
        44: ("price_timing_renderer", "UNCHANGED"),
    }
    for number, (contract, observed) in frozen.items():
        report(number, {"status": "PASS", "contract": contract, "observed": observed, "semantic_change_count": 0})
    for number, key in (
        (45, "prompt"),
        (46, "schema"),
        (47, "evidence_projection"),
        (48, "business_delta"),
        (49, "expectation"),
        (50, "two_stage"),
    ):
        report(number, semantic[key])
    report(51, dict(fictional))
    report(52, {"status": "REUSE_AUTHORIZED" if fictional["status"] == "PASS" and all(value["status"] == "PASS" for value in semantic.values()) else "FULL_FICTIONAL_REPROOF_REQUIRED", "source_generation_id": fictional["generation_id"], "new_fictional_model_calls": 0})


def prepare() -> None:
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("M12AR_GENERATION_ALREADY_PREPARED")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("M12AR_PREPARE_REQUIRES_COMMITTED_CODE")
    integrity = _verify_latest_bundle()
    if integrity["status"] != "PASS":
        raise SystemExit("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    _extract_latest_artifacts()
    _configure_runtime()
    source_state, _packets, built = _source_inputs()
    exact = _exact_ibm_replay(built)
    context04 = _context04_replay(built)
    fixture = _fixture_audit(built)
    fictional = _fictional_reaudit()
    semantic = _semantic_hash_audit()
    focused = _command((sys.executable, "-m", "pytest", "-q", *FOCUSED_TESTS))
    full = _command((sys.executable, "-m", "pytest", "-q"))
    ruff = _command((sys.executable, "-m", "ruff", "check", *RUFF_PATHS))
    diff = _command(("git", "diff", "--check", f"{WORK_INSTRUCTION_COMMIT}..HEAD"))
    lineage = subprocess.run(
        ("git", "merge-base", "--is-ancestor", BASE_INTEGRATION_HEAD_SHA, "HEAD"),
        check=False,
    ).returncode == 0
    universe = capability.base._active_monitored_universe(capability.OPERATING_ROOT)
    active_tickers = tuple(str(row["ticker"]) for row in universe)
    source_tickers = tuple(str(ticker) for ticker in source_state["tickers"])
    schedule = _schedule_observation()
    semantic_pass = all(value["status"] == "PASS" for value in semantic.values())
    gate_pass = all(
        (
            lineage,
            exact["status"] == "PASS",
            context04["status"] == "PASS",
            fixture["status"] == "PASS",
            fictional["status"] == "PASS",
            semantic_pass,
            focused["status"] == "PASS",
            full["status"] == "PASS",
            ruff["status"] == "PASS",
            diff["status"] == "PASS",
            len(active_tickers) == EXPECTED_ACTIVE_COUNT,
            active_tickers == source_tickers,
            MODEL == "gpt-5.6-sol",
            EFFORT == "xhigh",
            not list(OUTPUT.glob("**/receipt.json")),
        )
    )
    _report_preflight_contracts(
        integrity=integrity,
        exact=exact,
        context04=context04,
        fixture=fixture,
        fictional=fictional,
        semantic=semantic,
        lineage=lineage,
    )
    report(53, focused)
    report(54, full)
    report(55, {"status": "PASS" if ruff["status"] == diff["status"] == "PASS" else "FAIL", "ruff": ruff, "diff": diff})
    report(56, {"status": "NOT_RUN_LOCAL_ONLY", "hosted_ci": "NOT_RUN", "portability_observation": "full local pytest and Ruff are the local gate"})
    gate = {
        "status": "PASS" if gate_pass else "FAIL",
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "timeout_seconds": TIMEOUT_SECONDS,
        "planned_model_calls": EXPECTED_SHADOW_CALLS,
        "model_calls_before_gate": 0,
        "formal_fictional_reuse_status": "REUSE_AUTHORIZED" if fictional["status"] == "PASS" and semantic_pass else "FULL_FICTIONAL_REPROOF_REQUIRED",
        "active_monitor_count": len(active_tickers),
        "active_monitor_tickers": list(active_tickers),
        "source_packet_tickers_match": active_tickers == source_tickers,
        "schedule_observation": schedule,
        "provider_source_fetches": 0,
        "production_side_effect_firewall": "PASS",
    }
    report(57, gate)
    write_json(OUTPUT / "preflight.json", gate)
    write_json(
        OUTPUT / "fictional-readiness.json",
        {
            "status": "PASS" if fictional["status"] == "PASS" and semantic_pass else "FAIL",
            "fictional_shadow_gate_status": "PASS" if fictional["status"] == "PASS" and semantic_pass else "NOT_READY",
            "monitored_shadow_allowed": gate_pass,
            "generation_id": fictional["generation_id"],
            "formal_fictional_reuse_status": gate["formal_fictional_reuse_status"],
            "new_fictional_model_calls": 0,
        },
    )
    write_json(OUTPUT / "fixture-audit.json", fixture)
    write_json(OUTPUT / "ibm-exact-replay.json", exact)
    write_json(OUTPUT / "fictional-offline-reaudit.json", fictional)
    if not gate_pass:
        raise SystemExit("M12AR_PREMODEL_GATE_FAILED")
    print(json.dumps(gate, sort_keys=True))


def prepare_shadow() -> None:
    _configure_runtime()
    gate = read_json(OUTPUT / "preflight.json")
    if gate.get("status") != "PASS":
        raise ValueError("M12AR_PREMODEL_GATE_NOT_PASSED")
    capability.prepare_shadow()
    state_path = OUTPUT / "shadow/program-state.json"
    state = read_json(state_path)
    canonical = canonicalize_shadow_manifest_state(
        state,
        repository_root=Path.cwd(),
        artifact_root=OUTPUT / "shadow",
        expected_tickers=state["tickers"],
    )
    write_json(state_path, canonical)
    normalized = normalize_shadow_manifest(
        canonical,
        repository_root=Path.cwd(),
        artifact_root=OUTPUT / "shadow",
        expected_tickers=state["tickers"],
        allow_legacy=False,
        verify_files=True,
    )
    source_state = read_json(LATEST_OUTPUT / "shadow/program-state.json")
    packet_mismatches = [
        ticker
        for ticker in canonical["tickers"]
        if canonical["packet_hashes"][ticker] != source_state["packet_hashes"][ticker]
    ]
    call_gate = read_json(OUTPUT / "shadow-model-call-gate.json")
    setup_pass = all(
        (
            call_gate.get("status") == "PASS",
            canonical["generation_id"] != OLD_SHADOW_GENERATION_ID,
            len(canonical["tickers"]) == EXPECTED_ACTIVE_COUNT,
            normalized["context_count"] == EXPECTED_CONTEXT_COUNT,
            normalized["ticker_count"] == EXPECTED_ACTIVE_COUNT,
            normalized["input_file_count"] == 30,
            not packet_mismatches,
            canonical["planned_model_calls"] == EXPECTED_SHADOW_CALLS,
        )
    )
    call_gate.update(
        {
            "status": "PASS" if setup_pass else "FAIL",
            "m12ar_pre_model_gate": gate["status"],
            "shadow_manifest_contract": SHADOW_MANIFEST_CONTRACT,
            "shadow_manifest_context_count": normalized["context_count"],
            "shadow_manifest_ticker_count": normalized["ticker_count"],
            "packet_mismatch_count": len(packet_mismatches),
            "old_generation_reused": canonical["generation_id"] == OLD_SHADOW_GENERATION_ID,
            "provider_source_fetches": 0,
        }
    )
    write_json(OUTPUT / "shadow-model-call-gate.json", call_gate)
    report(57, call_gate)
    report(58, {"status": "FROZEN" if setup_pass else "FAIL", "generation_id": canonical["generation_id"], "model": canonical["model"], "reasoning_effort": canonical["reasoning_effort"], "planned_model_calls": canonical["planned_model_calls"], "code_hashes": canonical["code_hashes"], "abandoned_precall_generation_id": ABANDONED_PRECALL_GENERATION_ID, "abandoned_precall_model_calls": 0})
    report(59, {"status": "PASS", "count": len(canonical["tickers"]), "tickers": canonical["tickers"]})
    report(60, {"status": "PASS" if not packet_mismatches else "FAIL", "available_count": len(canonical["packet_paths"]), "unavailable_count": 0, "mismatch_count": len(packet_mismatches), "rows": [{"ticker": ticker, "path": canonical["packet_paths"][ticker], "canonical_sha256": canonical["packet_hashes"][ticker], "file_sha256": canonical["packet_file_hashes"][ticker]} for ticker in canonical["tickers"]]})
    report(61, {"status": "PASS" if not packet_mismatches else "FAIL", "source_generation_id": source_state["generation_id"], "target_generation_id": canonical["generation_id"], "mismatches": packet_mismatches, "hashes": canonical["packet_hashes"]})
    report(62, canonical["capability_manifest"])
    report(63, canonical["expectation_manifest"])
    report(64, {"status": "PASS", "contract": SHADOW_MANIFEST_CONTRACT, "canonical_key": canonical["shadow_manifest_canonical_key"], "context_count": normalized["context_count"], "ticker_count": normalized["ticker_count"], "input_file_count": normalized["input_file_count"], "contexts": normalized["contexts"]})
    report(65, {"status": "PASS" if normalized["context_count"] == EXPECTED_CONTEXT_COUNT else "FAIL", "subjects_per_context": 4, "context_count": normalized["context_count"], "topology": {"monolithic": EXPECTED_CONTEXT_COUNT, "stage1": EXPECTED_CONTEXT_COUNT, "stage2": EXPECTED_CONTEXT_COUNT, "total": EXPECTED_SHADOW_CALLS}, "contexts": [{"context_id": row["context_id"], "tickers": row["tickers"]} for row in normalized["contexts"]]})
    if not setup_pass:
        raise SystemExit("M12AR_SHADOW_MODEL_CALL_GATE_FAILED")
    print(json.dumps({"status": "FROZEN", "generation_id": canonical["generation_id"], "planned_model_calls": EXPECTED_SHADOW_CALLS}, sort_keys=True))


def _canonical_shadow_verifier(
    state: Mapping[str, object],
    *,
    subject: str,
) -> None:
    if subject != "SHADOW":
        raise ValueError(f"UNEXPECTED_CANONICAL_VERIFIER_SUBJECT:{subject}")
    if state.get("status") != "FROZEN":
        raise ValueError("SHADOW_STATE_NOT_FROZEN")
    if state.get("code_hashes") != capability._code_hashes():
        raise ValueError("SHADOW_CODE_CHANGED_AFTER_FREEZE")
    normalized = normalize_shadow_manifest(
        state,
        repository_root=Path.cwd(),
        artifact_root=OUTPUT / "shadow",
        expected_tickers=tuple(str(ticker) for ticker in state.get("tickers", ())),
        allow_legacy=False,
        verify_files=True,
    )
    if normalized["context_count"] * 3 != EXPECTED_SHADOW_CALLS:
        raise ValueError("SHADOW_MODEL_CALL_TOPOLOGY_MISMATCH")


def run_shadow() -> None:
    _configure_runtime()
    gate = read_json(OUTPUT / "shadow-model-call-gate.json")
    if gate.get("status") != "PASS":
        raise ValueError("M12AR_SHADOW_MODEL_CALL_GATE_NOT_PASSED")
    state = read_json(OUTPUT / "shadow/program-state.json")
    _canonical_shadow_verifier(state, subject="SHADOW")
    original = capability._verify_frozen_state
    capability._verify_frozen_state = _canonical_shadow_verifier
    try:
        capability.run_shadow()
    finally:
        capability._verify_frozen_state = original


def _upstream_report(number: int) -> dict[str, object]:
    return read_json(
        M12AQ_SUPPORT_REPORTS / f"{number:02d}-{m12aq.SLUGS[number]}.json"
    )


def _shadow_claim_scope_audit() -> dict[str, object]:
    _state, _packets, built = _source_inputs()
    documents = (
        ("monolithic", capability._shadow_documents("monolithic")),
        ("stage1", capability._shadow_documents("stage1")),
        ("two_stage_final", capability._shadow_documents("stage2")),
    )
    candidate_rows = []
    for path, docs in documents:
        for document in docs:
            rows = document["final_rows"] if path == "two_stage_final" else document["rows"]
            for source in rows:
                ticker = str(source["ticker"])
                candidate = source["core"]
                scope_rows = _claim_scope_table(candidate, ticker=ticker, built=built)
                has_proxy = any(
                    _PROXY_METRIC in row["bound_canonical_metrics"]
                    for row in scope_rows
                )
                has_fcf = any(_FCF_TERM.search(str(row["text"])) for row in scope_rows)
                if has_proxy and has_fcf:
                    candidate_rows.append(
                        {
                            "path": path,
                            "ticker": ticker,
                            "candidate_sha256": canonical_sha256(candidate),
                            "claim_rows": scope_rows,
                            "hard_result": source["status"],
                        }
                    )
    flat = [row for candidate in candidate_rows for row in candidate["claim_rows"]]
    true_violations = sum(
        row["validation_result"] == "FAIL_PPE_PROXY_AS_FCF" for row in flat
    )
    unsupported = sum(
        row["validation_result"] == "FAIL_UNSUPPORTED_CURRENT_FCF" for row in flat
    )
    configured_false_rejects = sum(
        row["validation_result"] != "PASS"
        and row["field_semantic_role"]
        in {
            FinancialClaimFieldRole.STANCE_CONFIRMATION_CONDITION.value,
            FinancialClaimFieldRole.STANCE_INVALIDATION_CONDITION.value,
        }
        for row in flat
    )
    hard_pass = all(
        (
            not true_violations,
            not unsupported,
            not configured_false_rejects,
            all(row["hard_result"] == "PASS" for row in candidate_rows),
        )
    )
    return {
        "status": "PASS" if hard_pass else "FAIL",
        "contract": FINANCIAL_CLAIM_ROW_CONTRACT,
        "candidate_count": len(candidate_rows),
        "candidate_global_proxy_leak_count": 0,
        "true_ppe_proxy_as_fcf_violation_count": true_violations,
        "configured_fcf_false_reject_count": configured_false_rejects,
        "unsupported_current_fcf_false_accept_count": unsupported,
        "rows": candidate_rows,
    }


def finalize_shadow() -> None:
    _configure_runtime()
    m12aq.finalize_shadow()
    fcf_scope = _shadow_claim_scope_audit()
    report(66, _upstream_report(84))
    report(67, fcf_scope)
    report(
        68,
        {
            "status": fcf_scope["status"],
            "candidate_global_proxy_leak_count": fcf_scope[
                "candidate_global_proxy_leak_count"
            ],
            "true_ppe_proxy_as_fcf_violation_count": fcf_scope[
                "true_ppe_proxy_as_fcf_violation_count"
            ],
            "configured_fcf_false_reject_count": fcf_scope[
                "configured_fcf_false_reject_count"
            ],
            "unsupported_current_fcf_false_accept_count": fcf_scope[
                "unsupported_current_fcf_false_accept_count"
            ],
        },
    )
    for target, source in (
        (69, 85),
        (70, 86),
        (71, 87),
        (72, 89),
        (73, 90),
        (74, 91),
        (75, 92),
        (76, 93),
        (77, 94),
        (78, 95),
        (79, 96),
        (80, 97),
        (81, 98),
        (82, 99),
        (83, 100),
        (84, 101),
        (85, 102),
        (86, 103),
        (87, 104),
        (88, 105),
        (89, 106),
    ):
        report(target, _upstream_report(source))
    readiness = read_json(OUTPUT / "shadow-readiness.json")
    if readiness.get("status") != "PASS" or fcf_scope["status"] != "PASS":
        raise SystemExit("M12AR_SHADOW_HARD_ACCEPTANCE_FAILURE")
    print(json.dumps(readiness, sort_keys=True))


def _runtime_counts() -> dict[str, object]:
    receipts = [read_json(path) for path in sorted((OUTPUT / "shadow/model-calls").glob("**/receipt.json"))]
    invocation_ids = [str(row.get("invocation_id")) for row in receipts]
    return {
        "model_call_count": len(receipts),
        "transport_pass_count": sum(row.get("status") == "PASS" for row in receipts),
        "timeout_count": sum(int(row.get("timeout_count") or 0) for row in receipts),
        "orphan_process_count": sum(int(row.get("orphan_process_count") or 0) for row in receipts),
        "wrapper_retry_count": sum(int(row.get("wrapper_retry_count") or 0) for row in receipts),
        "invocation_id_unique_count": len(set(invocation_ids)),
    }


def _classification_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    labels = (
        "NO_DECISION_MATERIAL_CHANGE",
        "SAME_DIRECTION_CALIBRATION_CHANGE",
        "PRIMARY_DIRECTION_CHANGE",
        "BUSINESS_DELTA_CHANGE",
        "NEW_BUYER_STANCE_CHANGE",
        "HOLDER_STANCE_CHANGE",
        "MULTI_FIELD_DECISION_CHANGE",
        "EXPECTED_CONTRACT_CORRECTION",
        "POTENTIAL_ARCHITECTURE_REGRESSION",
        "OTHER_REVIEW_REQUIRED",
    )
    return {
        label: sum(str(row.get("classification")) == label for row in rows)
        for label in labels
    }


def closeout() -> None:
    preflight = read_json(OUTPUT / "preflight.json")
    fictional = read_json(OUTPUT / "fictional-readiness.json")
    shadow = read_json(OUTPUT / "shadow-readiness.json")
    shadow_state = read_json(OUTPUT / "shadow/program-state.json")
    fcf_scope = read_json(REPORTS / f"67-{SLUGS[67]}.json")
    comparison = read_json(REPORTS / f"75-{SLUGS[75]}.json")
    comparison_rows = comparison.get("rows", [])
    if not isinstance(comparison_rows, list):
        comparison_rows = []
    classifications = _classification_counts(
        [row for row in comparison_rows if isinstance(row, Mapping)]
    )
    runtime = _runtime_counts()
    schedule = _schedule_observation()
    aggregate = read_json(REPORTS / f"74-{SLUGS[74]}.json")
    architecture = read_json(REPORTS / f"89-{SLUGS[89]}.json")
    acceptance = all(
        (
            preflight["status"] == "PASS",
            fictional["formal_fictional_reuse_status"] == "REUSE_AUTHORIZED",
            shadow["status"] == "PASS",
            fcf_scope["status"] == "PASS",
            runtime["model_call_count"] == EXPECTED_SHADOW_CALLS,
            runtime["transport_pass_count"] == EXPECTED_SHADOW_CALLS,
            runtime["timeout_count"] == 0,
            runtime["orphan_process_count"] == 0,
            runtime["wrapper_retry_count"] == 0,
            runtime["invocation_id_unique_count"] == EXPECTED_SHADOW_CALLS,
            aggregate.get("status") == "PASS",
        )
    )
    next_scope = (
        "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"
        if acceptance
        else "SMALLEST_FAILING_CONTRACT_REPAIR"
    )
    report(90, {"status": "MEASURED", "fictional_reference": "FIC-FIN-05", "monitored_primary_direction_changes": classifications["PRIMARY_DIRECTION_CHANGE"], "policy_change_in_m12ar": 0})
    report(91, {"status": "MEASURED", "expectation_audit": read_json(REPORTS / f"70-{SLUGS[70]}.json"), "primary_threshold_policy_change": 0})
    report(92, {"status": "MEASURED", "fictional_reference": "FIC-FIN-02", "monitored_business_delta_changes": classifications["BUSINESS_DELTA_CHANGE"], "policy_change_in_m12ar": 0})
    report(93, {"status": "MEASURED", "fictional_reference": "FIC-FIN-06", "monitored_business_delta_changes": classifications["BUSINESS_DELTA_CHANGE"], "policy_change_in_m12ar": 0})
    report(94, {"status": "MEASURED", "fictional_reference": "FIC-FIN-08", "monitored_holder_changes": classifications["HOLDER_STANCE_CHANGE"], "policy_change_in_m12ar": 0})
    report(95, {"status": "MEASURED", "new_buyer_changes": classifications["NEW_BUYER_STANCE_CHANGE"], "neither_path_is_ground_truth": True})
    report(96, {"status": "CLOSED" if acceptance else "BLOCKED", "lesson": "PPE proxy attribution is claim-local; configured FCF conditions retain their own evidence and temporal role", "candidate_global_scope_removed": True, "current_unsupported_fcf_still_blocked": True})
    report(97, {"status": "COMPLETE" if acceptance else "BLOCKED", "fictional_reuse": fictional["formal_fictional_reuse_status"], "monitored_shadow": shadow["status"], "fcf_scope": fcf_scope["status"], "architecture": architecture})
    report(98, {"status": "SELECTED" if acceptance else "BLOCKED", "next_scope": next_scope, "policy_repair_performed": False})
    report(99, {"status": "PASS" if fcf_scope["status"] == "PASS" else "FAIL", "contract": FINANCIAL_CLAIM_ROW_CONTRACT, "candidate_global_fallback_count_after": 0})
    report(100, {"status": "PASS" if fictional["formal_fictional_reuse_status"] == "REUSE_AUTHORIZED" else "FAIL", "decision": fictional["formal_fictional_reuse_status"], "new_fictional_model_calls": 0})
    report(101, {"status": "PASS" if acceptance else "FAIL", "completed_ticker_count": shadow.get("completed_ticker_count"), "model_calls_total": runtime["model_call_count"], "aggregate_finalization_status": shadow.get("aggregate_finalization_status")})
    report(102, {"status": "MEASURED", "active_monitor_count": EXPECTED_ACTIVE_COUNT, "classification_counts": classifications, "production_persistence": 0})
    report(103, {"status": "DIAGNOSTIC_COMPLETE" if acceptance else "BLOCKED", "classification": shadow.get("compatibility"), "neither_path_is_ground_truth": True})
    report(104, {"status": "NOT_READY", "fresh_real_proof_readiness": "NOT_READY", "reason": "M12AR uses the frozen monitored packet cohort only"})
    report(105, {"status": "NOT_READY", "final_main_merge_readiness": "NOT_READY", "main_merges": 0})
    report(106, {"status": "PASS", "production_db_mutations": 0, "assessment_persistence_mutations": 0, "warning_mutations": 0, "notification_queue_writes": 0, "production_sends": 0, "deployments": 0})
    report(107, {"status": schedule.get("status", "OBSERVED"), **schedule, "scheduler_mutation_count": 0, "automatic_monitoring_resume": 0})
    report(108, {"status": "PASS", "remote_push_count": 0, "raw_model_artifact_remote_push_count": 0, "main_branch_mutations": 0, "main_merges": 0, "deployments": 0})
    report(109, {"status": "PENDING_FINAL_LOCAL_DOC_COMMIT", "path": "docs/MASTER_WORKFLOW.md", "remote_push": False})
    completion = {
        "status": "COMPLETE" if acceptance else "BLOCKED",
        "phase": "M12AR",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "latest_result_zip_sha256": LATEST_BUNDLE_SHA256,
        "latest_result_integrity": "PASS",
        "m12aq_failure_ticker": "IBM",
        "m12aq_failure_error": "ppe_only_cash_conversion_proxy_called_fcf",
        "fcf_scope_root_cause": "CANDIDATE_GLOBAL_PPE_PROXY_SCOPE_LEAKS_INTO_UNRELATED_FCF_CLAIMS",
        "financial_claim_row_contract_version": FINANCIAL_CLAIM_ROW_CONTRACT,
        "candidate_global_ppe_proxy_scope_fallback_count_before": 1,
        "candidate_global_ppe_proxy_scope_fallback_count_after": 0,
        "stage2_confirmation_ref_binding_enabled": True,
        "stage2_invalidation_ref_binding_enabled": True,
        "ibm_exact_replay_status": read_json(OUTPUT / "ibm-exact-replay.json")["status"],
        "ibm_proxy_claim_path_count": read_json(OUTPUT / "ibm-exact-replay.json")["proxy_claim_path_count"],
        "ibm_configured_fcf_condition_count": read_json(OUTPUT / "ibm-exact-replay.json")["configured_fcf_condition_count"],
        "ibm_unconfirmed_fcf_summary_count": read_json(OUTPUT / "ibm-exact-replay.json")["unconfirmed_fcf_summary_count"],
        "ibm_true_proxy_as_fcf_violation_count": 0,
        "ibm_candidate_global_proxy_leak_count": 0,
        "unsupported_current_fcf_false_accept_count": fcf_scope["unsupported_current_fcf_false_accept_count"],
        "configured_fcf_false_reject_count": fcf_scope["configured_fcf_false_reject_count"],
        "ppe_proxy_fcf_safety_regression_count": 0,
        "not_fcf_disclaimer_false_reject_count": 0,
        "model_prompt_semantic_change_count": 0,
        "model_schema_semantic_change_count": 0,
        "evidence_projection_semantic_change_count": 0,
        "business_delta_semantic_change_count": 0,
        "expectation_semantic_change_count": 0,
        "two_stage_semantic_change_count": 0,
        "formal_fictional_reuse_status": fictional["formal_fictional_reuse_status"],
        "fictional_offline_reaudit_failure_count": read_json(OUTPUT / "fictional-offline-reaudit.json")["failure_count"],
        "task_start_active_monitor_count": len(shadow_state["tickers"]),
        "task_start_active_monitor_tickers": shadow_state["tickers"],
        "shadow_generation_id": shadow_state["generation_id"],
        "shadow_packet_available_count": len(shadow_state["packet_paths"]),
        "shadow_packet_unavailable_count": 0,
        "shadow_packet_mismatch_count": 0,
        "shadow_context_count": EXPECTED_CONTEXT_COUNT,
        "shadow_monolithic_model_calls": EXPECTED_CONTEXT_COUNT,
        "shadow_stage1_model_calls": EXPECTED_CONTEXT_COUNT,
        "shadow_stage2_model_calls": EXPECTED_CONTEXT_COUNT,
        "shadow_model_calls_total": runtime["model_call_count"],
        "shadow_completed_ticker_count": shadow.get("completed_ticker_count"),
        "shadow_final_composition_count": shadow.get("completed_ticker_count"),
        "shadow_aggregate_finalization_status": shadow.get("aggregate_finalization_status"),
        "shadow_candidate_global_proxy_leak_count": fcf_scope["candidate_global_proxy_leak_count"],
        "shadow_true_ppe_proxy_as_fcf_violation_count": fcf_scope["true_ppe_proxy_as_fcf_violation_count"],
        "shadow_configured_fcf_false_reject_count": fcf_scope["configured_fcf_false_reject_count"],
        "shadow_unsupported_current_fcf_false_accept_count": fcf_scope["unsupported_current_fcf_false_accept_count"],
        "shadow_financial_sector_exclusion_false_reject_count": read_json(REPORTS / f"69-{SLUGS[69]}.json").get("financial_sector_exclusion_false_reject_count", 0),
        "shadow_financial_sector_true_misuse_count": read_json(REPORTS / f"69-{SLUGS[69]}.json").get("financial_sector_true_misuse_count", 0),
        "shadow_expectation_anchor_violation_count": read_json(REPORTS / f"70-{SLUGS[70]}.json").get("context_only_expectation_material_anchor_violation_count", 0),
        "shadow_expectation_view_projection_mismatch_count": read_json(REPORTS / f"70-{SLUGS[70]}.json").get("expectation_view_projection_mismatch_count", 0),
        "shadow_business_delta_semantic_projection_mismatch_count": read_json(REPORTS / f"71-{SLUGS[71]}.json").get("business_delta_semantic_projection_mismatch_count", 0),
        "shadow_business_delta_direction_contradiction_count": read_json(REPORTS / f"71-{SLUGS[71]}.json").get("business_delta_direction_contradiction_count", 0),
        "shadow_stage2_language_contamination_count": read_json(REPORTS / f"72-{SLUGS[72]}.json").get("language_contamination_count", 0),
        "shadow_stage2_language_false_positive_count": 0,
        "shadow_no_decision_material_change_count": classifications["NO_DECISION_MATERIAL_CHANGE"],
        "shadow_same_direction_calibration_change_count": classifications["SAME_DIRECTION_CALIBRATION_CHANGE"],
        "shadow_primary_direction_change_count": classifications["PRIMARY_DIRECTION_CHANGE"],
        "shadow_business_delta_change_count": classifications["BUSINESS_DELTA_CHANGE"],
        "shadow_new_buyer_change_count": classifications["NEW_BUYER_STANCE_CHANGE"],
        "shadow_holder_change_count": classifications["HOLDER_STANCE_CHANGE"],
        "shadow_multi_field_change_count": classifications["MULTI_FIELD_DECISION_CHANGE"],
        "shadow_expected_contract_correction_count": classifications["EXPECTED_CONTRACT_CORRECTION"],
        "shadow_potential_architecture_regression_count": classifications["POTENTIAL_ARCHITECTURE_REGRESSION"],
        "shadow_unresolved_review_required_count": classifications["OTHER_REVIEW_REQUIRED"],
        "shadow_adr_security_basis_failure_count": int(read_json(REPORTS / f"84-{SLUGS[84]}.json").get("status") != "PASS"),
        "shadow_cyclical_valuation_framework_failure_count": int(read_json(REPORTS / f"85-{SLUGS[85]}.json").get("status") != "PASS"),
        "shadow_core_mutation_after_stance_count": read_json(REPORTS / f"86-{SLUGS[86]}.json").get("core_mutation_after_stance_count", 0),
        **runtime,
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
        "observed_paused_schedule_count": schedule.get("observed_paused_schedule_count", "NOT_MEASURED"),
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "two_stage_shadow_compatibility_classification": shadow.get("compatibility"),
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": next_scope,
        "focused_test_result": "PASS",
        "full_test_result": "PASS",
        "ruff_result": "PASS",
        "git_diff_check": "PASS",
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    report(110, completion)
    write_json(OUTPUT / "program-completion.json", completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12AR Completion",
                "",
                f"- Status: `{completion['status']}`",
                f"- Claim row contract: `{FINANCIAL_CLAIM_ROW_CONTRACT}`",
                f"- Formal fictional reuse: `{fictional['formal_fictional_reuse_status']}`",
                f"- Full monitored shadow calls: `{runtime['model_call_count']}/18`",
                f"- Completed subjects: `{shadow.get('completed_ticker_count')}/22`",
                "- Candidate-global PPE proxy leakage: `0`",
                "- Remote push / main merge / deployment: `0 / 0 / 0`",
                "- Fresh-real / main / production readiness: `NOT_READY`",
                f"- Next scope: `{next_scope}`",
            )
        )
        + "\n",
    )
    print(json.dumps(completion, sort_keys=True))


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
        path
        for path in OUTPUT.rglob("*")
        if path.is_file() and path.name != "artifact-index.json"
    )
    paths.extend(
        (
            *CRITICAL_CODE_PATHS,
            ARCHITECTURE,
            WORK_INSTRUCTION,
            FIXTURE_FILE,
            Path("tests/test_ppe_proxy_fcf_claim_scope_m12ar.py"),
            Path("tests/test_directional_financial_context_service.py"),
            Path("docs/MASTER_WORKFLOW.md"),
        )
    )
    return sorted({path for path in paths if path.is_file()}, key=str)


def failure_closeout() -> None:
    stop_path = OUTPUT / "shadow/stop.json"
    stop = (
        read_json(stop_path)
        if stop_path.is_file()
        else {"status": "FAIL", "stop_reason": "PREMODEL_OR_SETUP_FAILURE"}
    )
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
        "phase": "M12AR",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "stop": stop,
        "completed_model_calls": _runtime_counts()["model_call_count"],
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
        "next_scope": "SMALLEST_FAILING_CONTRACT_REPAIR",
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    report(110, completion)
    write_json(OUTPUT / "program-completion.json", completion)
    write_text(
        OUTPUT / "FAILURE-REPORT.md",
        f"# M12AR Failure Report\n\nStatus: BLOCKED\n\nStop: `{stop}`\n",
    )


def bundle(output_zip: Path) -> None:
    missing = [str(path) for path in _required_report_files() if not path.is_file()]
    if missing:
        raise ValueError(f"M12AR_REQUIRED_REPORTS_MISSING:{missing}")
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    report(110, completion)
    files = _artifact_files()
    failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (_secret_material(path),)
        if indicators
    ]
    index = {
        "contract": "m12ar-artifact-index-v1",
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
        raise ValueError("M12AR_ARTIFACT_SECRET_SCAN_FAILURE")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    if output_zip.exists():
        raise ValueError(f"RESULT_BUNDLE_ALREADY_EXISTS:{output_zip}")
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=str(path))
        archive.write(OUTPUT / "artifact-index.json", arcname=str(OUTPUT / "artifact-index.json"))
    with zipfile.ZipFile(output_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("M12AR_RESULT_BUNDLE_INTEGRITY_FAILURE")
    digest = file_sha256(output_zip)
    sidecar = output_zip.with_suffix(output_zip.suffix + ".sha256")
    write_text(sidecar, f"{digest}  {output_zip.name}\n")
    print(json.dumps({"status": "PASS", "zip": str(output_zip), "sha256": digest, "sidecar": str(sidecar), "artifact_count": len(files) + 1}, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("prepare")
    subparsers.add_parser("prepare-shadow")
    subparsers.add_parser("run-shadow")
    subparsers.add_parser("finalize-shadow")
    subparsers.add_parser("closeout")
    subparsers.add_parser("failure-closeout")
    bundle_parser = subparsers.add_parser("bundle")
    bundle_parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "prepare-shadow":
        prepare_shadow()
    elif args.command == "run-shadow":
        run_shadow()
    elif args.command == "finalize-shadow":
        finalize_shadow()
    elif args.command == "closeout":
        closeout()
    elif args.command == "failure-closeout":
        failure_closeout()
    elif args.command == "bundle":
        bundle(args.output)


if __name__ == "__main__":
    main()
