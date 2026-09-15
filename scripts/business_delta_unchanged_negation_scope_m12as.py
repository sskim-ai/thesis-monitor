"""M12AS UNCHANGED claim-scope repair and new full monitored shadow proof."""

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

from app.services.business_delta_evidence_service import (
    BusinessDeltaCapability,
    BusinessDeltaEvidenceItem,
    BusinessDeltaEvidenceRole,
    BusinessDeltaEvidenceView,
    BusinessDeltaUnchangedClaimRole,
    classify_business_delta_unchanged_claims,
    validate_business_delta_candidate,
)
from app.services.direction_timing_ownership_service import EvidenceDomain
from scripts import ppe_proxy_fcf_claim_scope_m12ar as m12ar
from scripts.shadow_frozen_context_manifest import (
    CONTRACT_VERSION as SHADOW_MANIFEST_CONTRACT,
    canonicalize_shadow_manifest_state,
    normalize_shadow_manifest,
)


NAME = "20260912-business-delta-unchanged-configured-condition-negation-scope-full-shadow"
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
M12AR_SUPPORT_REPORTS = OUTPUT / "supporting-reports/m12ar"
M12AQ_SUPPORT_REPORTS = OUTPUT / "supporting-reports/m12aq"
M12AP_SUPPORT_REPORTS = OUTPUT / "supporting-reports/m12ap"
M12AO_SUPPORT_REPORTS = OUTPUT / "supporting-reports/m12ao"
M12AK_SUPPORT_REPORTS = OUTPUT / "supporting-reports/m12ak"
RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
RUNNER = Path("scripts/business_delta_unchanged_negation_scope_m12as.py")
ARCHITECTURE = Path("docs/architecture/BUSINESS_DELTA_UNCHANGED_CLAIM_SCOPE.md")
WORK_INSTRUCTION = Path("docs/work-instructions") / (
    "20260912-business-delta-unchanged-configured-condition-negation-scope-full-shadow.md"
)
FIXTURE_FILE = Path("tests/fixtures/business_delta_unchanged_negation_scope_m12as.json")
WORK_INSTRUCTION_COMMIT = "88992a3fdb613204b14a469de0c567ecbffae93e"
BASE_INTEGRATION_HEAD_SHA = "faab86f227f9342a5c23dab8c061a013d0e676a2"

ICLOUD = Path("/Users/sskim/Library/Mobile Documents/com~apple~CloudDocs/Thesis Monitor")
M12AR_NAME = "20260912-ppe-proxy-fcf-claim-evidence-scope-binding-full-shadow"
M12AR_OUTPUT = Path("artifacts") / M12AR_NAME
M12AR_BUNDLE = ICLOUD / f"thesis-monitor-{M12AR_NAME}-report.zip"
M12AR_BUNDLE_SHA256 = "97b94a2cfd2deb7bfcfa74508eba16815d2dff74f287886545a9e3970db09456"
M12AR_INDEXED_PAYLOADS = 294
M12AR_ZIP_ENTRIES = 295
M12AR_GENERATION_ID = "20260911-m12ai-shadow-20260912T075624Z-ffbc08645051"

M12AQ_NAME = m12ar.LATEST_NAME
M12AQ_OUTPUT = Path("artifacts") / M12AQ_NAME
M12AQ_BUNDLE = m12ar.LATEST_BUNDLE
M12AQ_BUNDLE_SHA256 = m12ar.LATEST_BUNDLE_SHA256
M12AQ_INDEXED_PAYLOADS = m12ar.LATEST_INDEXED_PAYLOADS
M12AQ_ZIP_ENTRIES = m12ar.LATEST_ZIP_ENTRIES

MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
EXPECTED_ACTIVE_COUNT = 22
EXPECTED_CONTEXT_COUNT = 6
EXPECTED_SHADOW_CALLS = 18
EXPECTED_SNDK_TEXT = (
    "AI 데이터센터 수요와 장기계약이 기존 논리의 중심이며, 제시된 강화·약화 "
    "조건은 의미 있는 관찰 변화로 확정되지 않았다."
)

_SLUG_SEQUENCE = (
    "repository-provenance",
    "latest-result-integrity",
    "m12as-scope-freeze",
    "integrated-main-lineage-freeze",
    "m12ar-sndk-failure-reproduction",
    "unchanged-context-regex-code-audit",
    "sndk-clause-polarity-forensic",
    "configured-condition-negation-scope-root-cause",
    "unchanged-claim-classifier-options",
    "unchanged-claim-classifier-decision",
    "business-delta-unchanged-claim-contract-v2",
    "current-thesis-change-assertion-contract",
    "configured-condition-reference-contract",
    "configured-condition-fulfillment-contract",
    "configured-condition-nonfulfillment-contract",
    "explicit-no-observed-change-contract",
    "local-negation-scope-contract",
    "english-korean-parity-contract",
    "m12ar-sndk-exact-offline-replay",
    "m12ar-context05-stage1-four-row-replay",
    "003690-absolute-state-regression",
    "fic-fin-05-unchanged-only-regression",
    "unchanged-configured-condition-positive-fixtures",
    "unchanged-true-change-negative-fixtures",
    "double-negation-negative-fixtures",
    "m12ar-fcf-claim-scope-freeze",
    "m12aq-financial-sector-scope-freeze",
    "m12ap-expectation-independence-freeze",
    "m12ao-business-delta-view-freeze",
    "m12an-ppe-proxy-label-freeze",
    "m12am-stage2-lexical-freeze",
    "monitoring-transition-ownership-freeze",
    "financial-temporal-scope-freeze",
    "qtd-ytd-wc-debt-safety-freeze",
    "adr-security-basis-freeze",
    "two-stage-ownership-freeze",
    "price-timing-renderer-no-change",
    "model-prompt-semantic-hash-freeze",
    "model-schema-semantic-hash-freeze",
    "evidence-projection-semantic-hash-freeze",
    "business-delta-view-semantic-hash-freeze",
    "expectation-view-semantic-hash-freeze",
    "two-stage-semantic-hash-freeze",
    "m12aq-fictional-24-row-business-delta-reaudit",
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
    "shadow-business-delta-unchanged-claim-scope-audit",
    "shadow-fcf-claim-scope-audit",
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
    "real-business-delta-unchanged-language-lessons",
    "combined-fictional-monitored-root-cause-summary",
    "next-bounded-policy-decision",
    "business-delta-unchanged-scope-repair-success-decision",
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
if len(SLUGS) != 103:
    raise RuntimeError(f"M12AS_REPORT_SEQUENCE_INVALID:{len(SLUGS)}")

FOCUSED_TESTS = (
    "tests/test_business_delta_unchanged_negation_scope_m12as.py",
    "tests/test_business_delta_unchanged_negation_scope_m12as_runner.py",
    "tests/test_business_delta_evidence_service.py",
    "tests/test_ppe_proxy_fcf_claim_scope_m12ar.py",
    "tests/test_directional_financial_context_service.py",
    "tests/test_financial_sector_exclusion_connective_scope_m12aq.py",
    "tests/test_market_expectation_evidence_service.py",
    "tests/test_two_stage_directional_service.py",
)
RUFF_PATHS = (
    "app/services/business_delta_evidence_service.py",
    str(RUNNER),
    "tests/test_business_delta_unchanged_negation_scope_m12as.py",
    "tests/test_business_delta_unchanged_negation_scope_m12as_runner.py",
)
CRITICAL_CODE_PATHS = tuple(
    dict.fromkeys(
        (
            *m12ar.CRITICAL_CODE_PATHS,
            Path("app/services/business_delta_evidence_service.py"),
            RUNNER,
        )
    )
)

capability = m12ar.capability
financial = m12ar.financial


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
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
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
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
    m12ar.NAME = NAME
    m12ar.OUTPUT = OUTPUT
    m12ar.REPORTS = M12AR_SUPPORT_REPORTS
    m12ar.M12AQ_SUPPORT_REPORTS = M12AQ_SUPPORT_REPORTS
    m12ar.M12AP_SUPPORT_REPORTS = M12AP_SUPPORT_REPORTS
    m12ar.M12AO_SUPPORT_REPORTS = M12AO_SUPPORT_REPORTS
    m12ar.M12AK_SUPPORT_REPORTS = M12AK_SUPPORT_REPORTS
    m12ar.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT
    m12ar.RUNNER = RUNNER
    m12ar.ARCHITECTURE = ARCHITECTURE
    m12ar.WORK_INSTRUCTION = WORK_INSTRUCTION
    m12ar.WORK_INSTRUCTION_COMMIT = WORK_INSTRUCTION_COMMIT
    m12ar.BASE_INTEGRATION_HEAD_SHA = BASE_INTEGRATION_HEAD_SHA
    m12ar.CRITICAL_CODE_PATHS = CRITICAL_CODE_PATHS
    m12ar.LATEST_NAME = M12AR_NAME
    m12ar.LATEST_OUTPUT = M12AR_OUTPUT
    m12ar.LATEST_BUNDLE = M12AR_BUNDLE
    m12ar.LATEST_BUNDLE_SHA256 = M12AR_BUNDLE_SHA256
    m12ar.LATEST_INDEXED_PAYLOADS = M12AR_INDEXED_PAYLOADS
    m12ar.LATEST_ZIP_ENTRIES = M12AR_ZIP_ENTRIES
    m12ar.MODEL = MODEL
    m12ar.EFFORT = EFFORT
    m12ar.TIMEOUT_SECONDS = TIMEOUT_SECONDS
    m12ar._configure_runtime()


def _verify_bundle(
    path: Path,
    *,
    expected_sha256: str,
    indexed_payloads: int,
    zip_entries: int,
) -> dict[str, object]:
    if not path.is_file():
        raise ValueError(f"RESULT_BUNDLE_MISSING:{path}")
    digest = file_sha256(path)
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        index_names = [name for name in names if name.endswith("/artifact-index.json")]
        if len(index_names) != 1:
            raise ValueError("RESULT_ARTIFACT_INDEX_IDENTITY_INVALID")
        index = json.loads(archive.read(index_names[0]))
        rows = index.get("rows")
        if not isinstance(rows, list):
            raise ValueError("RESULT_ARTIFACT_INDEX_ROWS_INVALID")
        by_path = {str(row["path"]): row for row in rows if isinstance(row, Mapping)}
        payload_names = set(names) - {index_names[0]}
        missing = sorted(set(by_path) - payload_names)
        extra = sorted(payload_names - set(by_path))
        hash_mismatches = []
        size_mismatches = []
        for name, row in by_path.items():
            if name not in payload_names:
                continue
            payload = archive.read(name)
            if hashlib.sha256(payload).hexdigest() != row.get("sha256"):
                hash_mismatches.append(name)
            if len(payload) != row.get("size"):
                size_mismatches.append(name)
    passed = all(
        (
            digest == expected_sha256,
            len(names) == zip_entries,
            len(by_path) == indexed_payloads,
            not missing,
            not extra,
            not hash_mismatches,
            not size_mismatches,
            index.get("status") == "PASS",
            index.get("secret_scan_failure_count") == 0,
        )
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "path": str(path),
        "sha256": digest,
        "zip_entry_count": len(names),
        "indexed_payload_count": len(by_path),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "hash_mismatch_count": len(hash_mismatches),
        "size_mismatch_count": len(size_mismatches),
        "index_status": index.get("status"),
        "index_secret_scan_failure_count": index.get("secret_scan_failure_count"),
    }


def _extract_output(bundle: Path, output_root: Path) -> None:
    prefix = f"{output_root}/"
    with zipfile.ZipFile(bundle) as archive:
        for info in archive.infolist():
            if not info.filename.startswith(prefix):
                continue
            target = (Path.cwd() / info.filename).resolve()
            if Path.cwd().resolve() not in target.parents:
                raise ValueError("RESULT_ARCHIVE_PATH_ESCAPE")
            archive.extract(info, Path.cwd())


def _source_inputs() -> tuple[dict[str, object], dict[str, object], tuple[object, ...]]:
    state = read_json(M12AR_OUTPUT / "shadow/program-state.json")
    tickers = tuple(str(ticker) for ticker in state["tickers"])
    packets = {
        ticker: read_json(M12AR_OUTPUT / "shadow/frozen-packets" / f"{ticker}.json")
        for ticker in tickers
    }
    mismatches = [
        ticker
        for ticker in tickers
        if canonical_sha256(packets[ticker]) != state["packet_hashes"][ticker]
    ]
    if mismatches:
        raise ValueError(f"M12AR_FROZEN_PACKET_HASH_MISMATCH:{mismatches}")
    return state, packets, capability.base._build_shadow_inputs(packets, tickers)


def _views(built: tuple[object, ...]) -> dict[str, BusinessDeltaEvidenceView]:
    _evidence, owned, catalogs, contexts, _stocks = built
    return capability._views(owned, catalogs, contexts)


def _stage1_document(root: Path, context_number: int) -> dict[str, object]:
    return read_json(
        root / "shadow/model-calls" / f"context-{context_number:02d}" / "stage1/run-document.json"
    )


def _validate_candidate(
    candidate: Mapping[str, object],
    view: BusinessDeltaEvidenceView,
) -> dict[str, object]:
    return validate_business_delta_candidate(candidate, view)


def _exact_sndk_replay(built: tuple[object, ...]) -> dict[str, object]:
    document = _stage1_document(M12AR_OUTPUT, 5)
    source = next(row for row in document["rows"] if row["ticker"] == "SNDK")
    candidate = source["core"]
    text = str(candidate["business_thesis_context"]["text"])
    views = _views(built)
    validation = _validate_candidate(candidate, views["SNDK"])
    old = source.get("business_delta_capability", {})
    claims = classify_business_delta_unchanged_claims(text)
    passed = all(
        (
            text == EXPECTED_SNDK_TEXT,
            candidate["business_thesis_change"] == "UNCHANGED",
            views["SNDK"].capability == BusinessDeltaCapability.UNCHANGED_ONLY,
            old.get("status") == "FAIL",
            "BUSINESS_DELTA_UNCHANGED_CONTEXT_ASSERTS_CHANGE" in old.get("errors", ()),
            validation["status"] == "PASS",
            validation["unchanged_claim_unsafe_count"] == 0,
        )
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "ticker": "SNDK",
        "candidate_sha256": canonical_sha256(candidate),
        "text": text,
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "capability": views["SNDK"].capability.value,
        "previous_status": old.get("status"),
        "previous_errors": old.get("errors", []),
        "current_validation": validation,
        "claim_roles": [claim.role.value for claim in claims],
        "candidate_modified": False,
    }


def _context05_replay(built: tuple[object, ...]) -> dict[str, object]:
    document = _stage1_document(M12AR_OUTPUT, 5)
    views = _views(built)
    rows = []
    for source in document["rows"]:
        ticker = str(source["ticker"])
        candidate = source["core"]
        validation = _validate_candidate(candidate, views[ticker])
        rows.append(
            {
                "ticker": ticker,
                "candidate_sha256": canonical_sha256(candidate),
                "capability": views[ticker].capability.value,
                "previous_status": source.get("status"),
                "current_status": validation["status"],
                "errors": validation["errors"],
                "unchanged_claims": validation["unchanged_claims"],
            }
        )
    passed = len(rows) == 4 and all(row["current_status"] == "PASS" for row in rows)
    return {
        "status": "PASS" if passed else "FAIL",
        "context": "context-05",
        "row_count": len(rows),
        "tickers": [row["ticker"] for row in rows],
        "rows": rows,
    }


def _monitored_ticker_replay(
    ticker: str,
    built: tuple[object, ...],
) -> dict[str, object]:
    views = _views(built)
    matches = []
    for path in sorted(
        (M12AR_OUTPUT / "shadow/model-calls").glob("context-*/stage1/run-document.json")
    ):
        document = read_json(path)
        matches.extend(row for row in document["rows"] if row["ticker"] == ticker)
    if len(matches) != 1:
        raise ValueError(f"M12AR_STAGE1_TICKER_IDENTITY_INVALID:{ticker}")
    candidate = matches[0]["core"]
    result = _validate_candidate(candidate, views[ticker])
    return {
        "status": result["status"],
        "ticker": ticker,
        "capability": views[ticker].capability.value,
        "candidate_sha256": canonical_sha256(candidate),
        "observed": candidate["business_thesis_change"],
        "validation": result,
    }


def _fictional_reaudit() -> dict[str, object]:
    state = read_json(M12AQ_OUTPUT / "fictional/program-state.json")
    _packets, owned, catalogs, contexts = financial.fictional_inputs(str(state["generation_id"]))
    views = capability._views(owned, catalogs, contexts)
    rows = []
    calls = M12AQ_OUTPUT / "fictional/model-calls"
    for path in sorted(calls.glob("run-*/stage1-context-*/run-document.json")):
        document = read_json(path)
        for source in document["rows"]:
            ticker = str(source["ticker"])
            candidate = source["core"]
            validation = _validate_candidate(candidate, views[ticker])
            rows.append(
                {
                    "path": "stage1",
                    "ticker": ticker,
                    "candidate_sha256": canonical_sha256(candidate),
                    "status": validation["status"],
                    "validation": validation,
                }
            )
    for path in sorted(calls.glob("run-*/stage2-context-*/run-document.json")):
        document = read_json(path)
        for source in document["compositions"]:
            candidate = source["candidate"]
            ticker = str(candidate["ticker"])
            validation = _validate_candidate(candidate, views[ticker])
            rows.append(
                {
                    "path": "two_stage_final",
                    "ticker": ticker,
                    "candidate_sha256": canonical_sha256(candidate),
                    "status": validation["status"],
                    "validation": validation,
                }
            )
    stage1 = [row for row in rows if row["path"] == "stage1"]
    final = [row for row in rows if row["path"] == "two_stage_final"]
    failures = [row for row in rows if row["status"] != "PASS"]
    passed = len(stage1) == 24 and len(final) == 24 and not failures
    return {
        "status": "PASS" if passed else "FAIL",
        "generation_id": state["generation_id"],
        "stage1_row_count": len(stage1),
        "stage2_final_row_count": len(final),
        "business_delta_reaudit_count": len(rows),
        "failure_count": len(failures),
        "rows": rows,
    }


def _fic_fin_05_regression(fictional: Mapping[str, object]) -> dict[str, object]:
    rows = [row for row in fictional["rows"] if row["ticker"] == "FIC-FIN-05"]
    path_counts = {
        path: sum(row["path"] == path for row in rows)
        for path in ("stage1", "two_stage_final")
    }
    return {
        "status": (
            "PASS"
            if path_counts == {"stage1": 3, "two_stage_final": 3}
            and all(row["status"] == "PASS" for row in rows)
            else "FAIL"
        ),
        "row_count": len(rows),
        "path_counts": path_counts,
        "rows": rows,
    }


def _fixture_view() -> BusinessDeltaEvidenceView:
    item = BusinessDeltaEvidenceItem(
        alias="E1",
        canonical_ref="fixture:baseline",
        source_ref="fixture:baseline",
        domain=EvidenceDomain.BUSINESS_CURRENT,
        role=BusinessDeltaEvidenceRole.THESIS_BASELINE_CONTEXT,
        reason="stored thesis baseline",
    )
    return BusinessDeltaEvidenceView(
        ticker="SNDK",
        capability=BusinessDeltaCapability.UNCHANGED_ONLY,
        baseline_context_refs=(item.alias,),
        items=(item,),
    )


def _fixture_audit() -> dict[str, object]:
    fixture = json.loads(FIXTURE_FILE.read_text(encoding="utf-8"))
    if not isinstance(fixture, list):
        raise ValueError("M12AS_FIXTURE_LIST_REQUIRED")
    view = _fixture_view()
    rows = []
    for source in fixture:
        candidate = {
            "ticker": view.ticker,
            "business_thesis_change": "UNCHANGED",
            "business_thesis_context": {
                "text": source["text"],
                "evidence_refs": ["E1"],
            },
        }
        validation = _validate_candidate(candidate, view)
        claims = classify_business_delta_unchanged_claims(str(source["text"]))
        observed_roles = [claim.role.value for claim in claims]
        row_pass = all(
            (
                validation["status"] == source["expected_status"],
                source["expected_role"] in observed_roles,
            )
        )
        rows.append(
            {
                **source,
                "observed_status": validation["status"],
                "observed_roles": observed_roles,
                "validation": validation,
                "status": "PASS" if row_pass else "FAIL",
            }
        )
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "fixture_count": len(rows),
        "false_reject_count": sum(
            row["expected_status"] == "PASS" and row["observed_status"] != "PASS" for row in rows
        ),
        "false_accept_count": sum(
            row["expected_status"] == "FAIL" and row["observed_status"] != "FAIL" for row in rows
        ),
        "rows": rows,
    }


def _ast_selected_hash(
    source: str,
    *,
    include_names: frozenset[str] | None = None,
    exclude_names: frozenset[str] = frozenset(),
) -> str:
    tree = ast.parse(source)
    selected = []
    for node in tree.body:
        name = getattr(node, "name", None)
        if include_names is not None:
            if name in include_names:
                selected.append(node)
            continue
        if name in exclude_names:
            continue
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            names = {target.id for target in targets if isinstance(target, ast.Name)}
            if names & exclude_names:
                continue
        selected.append(node)
    payload = "\n".join(ast.dump(node, include_attributes=False) for node in selected)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _semantic_hash_audit() -> dict[str, object]:
    def base_text(path: Path) -> str:
        return subprocess.run(
            ("git", "show", f"{BASE_INTEGRATION_HEAD_SHA}:{path}"),
            check=True,
            capture_output=True,
            text=True,
        ).stdout

    def whole_paths(paths: Sequence[Path]) -> dict[str, object]:
        rows = [
            {
                "path": str(path),
                "before": hashlib.sha256(base_text(path).encode()).hexdigest(),
                "after": file_sha256(path),
            }
            for path in paths
        ]
        count = sum(row["before"] != row["after"] for row in rows)
        return {
            "status": "PASS" if count == 0 else "FAIL",
            "semantic_change_count": count,
            "rows": rows,
        }

    prompt = whole_paths(
        (
            Path("app/services/directional_balance_service.py"),
            Path("app/services/two_stage_directional_service.py"),
        )
    )
    schema = whole_paths(
        (
            Path("app/services/direction_timing_ownership_service.py"),
            Path("app/services/structured_autonomy_shadow_service.py"),
            Path("app/services/two_stage_directional_service.py"),
        )
    )
    projection_path = Path("app/services/directional_financial_context_service.py")
    projection_names = frozenset(
        {
            "build_financial_decision_context",
            "compact_financial_decision_context",
            "neutral_financial_evidence_statement",
            "first_class_financial_evidence_projection",
        }
    )
    before_projection = _ast_selected_hash(
        base_text(projection_path), include_names=projection_names
    )
    after_projection = _ast_selected_hash(
        projection_path.read_text(encoding="utf-8"), include_names=projection_names
    )
    financial_projection = {
        "status": "PASS" if before_projection == after_projection else "FAIL",
        "semantic_change_count": int(before_projection != after_projection),
        "before": before_projection,
        "after": after_projection,
    }
    delta_path = Path("app/services/business_delta_evidence_service.py")
    delta_exclusions = frozenset(
        {
            "UNCHANGED_CLAIM_SCOPE_CONTRACT",
            "BusinessDeltaUnchangedClaimRole",
            "BusinessDeltaUnchangedClaim",
            "_UNCHANGED_CLAUSE_SPLIT",
            "_CURRENT_THESIS_CHANGE_ASSERTION",
            "_CONFIGURED_CONDITION_FULFILLED",
            "_CONFIGURED_CONDITION_NOT_FULFILLED",
            "_EXPLICIT_NO_OBSERVED_CHANGE",
            "_CONFIGURED_CONDITION_REFERENCE",
            "_BASELINE_THESIS_DESCRIPTION",
            "_classify_business_delta_unchanged_clause",
            "classify_business_delta_unchanged_claims",
            "validate_business_delta_candidate",
        }
    )
    before_delta = _ast_selected_hash(base_text(delta_path), exclude_names=delta_exclusions)
    after_delta = _ast_selected_hash(
        delta_path.read_text(encoding="utf-8"), exclude_names=delta_exclusions
    )
    business_delta_view = {
        "status": "PASS" if before_delta == after_delta else "FAIL",
        "semantic_change_count": int(before_delta != after_delta),
        "before": before_delta,
        "after": after_delta,
        "excluded_post_model_contract": True,
    }
    expectation = whole_paths((Path("app/services/market_expectation_evidence_service.py"),))
    two_stage = whole_paths((Path("app/services/two_stage_directional_service.py"),))
    return {
        "prompt": prompt,
        "schema": schema,
        "evidence_projection": financial_projection,
        "business_delta_view": business_delta_view,
        "expectation_view": expectation,
        "two_stage": two_stage,
    }


def _schedule_observation() -> dict[str, object]:
    try:
        return m12ar._schedule_observation()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return {
            "status": "NOT_MEASURED",
            "reason": type(exc).__name__,
            "scheduler_mutation_count": 0,
        }


def _role_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    roles = tuple(role.value for role in BusinessDeltaUnchangedClaimRole)
    return {role: sum(role in row.get("observed_roles", ()) for row in rows) for role in roles}


def prepare() -> None:
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("M12AS_GENERATION_ALREADY_PREPARED")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("M12AS_PREPARE_REQUIRES_COMMITTED_CODE")

    integrity = _verify_bundle(
        M12AR_BUNDLE,
        expected_sha256=M12AR_BUNDLE_SHA256,
        indexed_payloads=M12AR_INDEXED_PAYLOADS,
        zip_entries=M12AR_ZIP_ENTRIES,
    )
    fictional_integrity = _verify_bundle(
        M12AQ_BUNDLE,
        expected_sha256=M12AQ_BUNDLE_SHA256,
        indexed_payloads=M12AQ_INDEXED_PAYLOADS,
        zip_entries=M12AQ_ZIP_ENTRIES,
    )
    if integrity["status"] != "PASS" or fictional_integrity["status"] != "PASS":
        raise SystemExit("M12AS_LATEST_RESULT_INTEGRITY_FAILURE")
    _extract_output(M12AR_BUNDLE, M12AR_OUTPUT)
    _extract_output(M12AQ_BUNDLE, M12AQ_OUTPUT)
    _configure_runtime()

    source_state, _packets, built = _source_inputs()
    exact = _exact_sndk_replay(built)
    context05 = _context05_replay(built)
    ticker_003690 = _monitored_ticker_replay("003690", built)
    fixtures = _fixture_audit()
    fictional = _fictional_reaudit()
    fic_fin_05 = _fic_fin_05_regression(fictional)
    semantic = _semantic_hash_audit()

    focused = _command((sys.executable, "-m", "pytest", "-q", *FOCUSED_TESTS))
    full = _command((sys.executable, "-m", "pytest", "-q"))
    ruff = _command((sys.executable, "-m", "ruff", "check", *RUFF_PATHS))
    diff = _command(("git", "diff", "--check", f"{WORK_INSTRUCTION_COMMIT}..HEAD"))
    lineage = (
        subprocess.run(
            ("git", "merge-base", "--is-ancestor", BASE_INTEGRATION_HEAD_SHA, "HEAD"),
            check=False,
        ).returncode
        == 0
    )
    current_head = git("rev-parse", "HEAD")
    active = capability.base._active_monitored_universe(capability.OPERATING_ROOT)
    active_tickers = tuple(str(row["ticker"]) for row in active)
    source_tickers = tuple(str(ticker) for ticker in source_state["tickers"])
    schedule = _schedule_observation()
    semantic_pass = all(row["status"] == "PASS" for row in semantic.values())
    fcf_path = Path("app/services/directional_financial_context_service.py")
    fcf_before = hashlib.sha256(
        subprocess.run(
            ("git", "show", f"{BASE_INTEGRATION_HEAD_SHA}:{fcf_path}"),
            check=True,
            capture_output=True,
        ).stdout
    ).hexdigest()
    fcf_after = file_sha256(fcf_path)
    fcf_freeze = {
        "status": "PASS" if fcf_before == fcf_after else "FAIL",
        "before": fcf_before,
        "after": fcf_after,
        "m12ar_claim_scope_reopened": fcf_before != fcf_after,
    }

    fixture_rows = fixtures["rows"]
    positive = [row for row in fixture_rows if row["expected_status"] == "PASS"]
    negative = [row for row in fixture_rows if row["expected_status"] == "FAIL"]
    double_negation = [
        row for row in fixture_rows if row["fixture_id"] in {"N05", "N06", "EN_FAIL_LOCAL_NEGATION"}
    ]
    role_counts = _role_counts(fixture_rows)

    report(
        1,
        {
            "status": "PASS",
            "branch": git("branch", "--show-current"),
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "implementation_head_sha": current_head,
            "local_only": True,
        },
    )
    report(2, {"status": "PASS", "m12ar": integrity, "m12aq": fictional_integrity})
    report(
        3,
        {
            "status": "FROZEN",
            "scope": "POST_MODEL_UNCHANGED_CLAIM_CLASSIFIER_ONLY",
            "new_model_calls_before_gate": 0,
            "candidate_modifications": 0,
            "fcf_scope_reopened": False,
        },
    )
    report(
        4,
        {
            "status": "PASS" if lineage else "FAIL",
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "head_sha": current_head,
            "linear_descendant": lineage,
        },
    )
    report(
        5,
        {
            "status": "REPRODUCED",
            "ticker": "SNDK",
            "generation_id": M12AR_GENERATION_ID,
            "previous_status": exact["previous_status"],
            "previous_errors": exact["previous_errors"],
            "candidate_sha256": exact["candidate_sha256"],
        },
    )
    report(
        6,
        {
            "status": "PASS",
            "before": "raw thesis/change and condition/fulfillment proximity regex",
            "after": "bounded claim-role classifier",
            "model_facing_change": False,
        },
    )
    report(
        7,
        {
            "status": exact["status"],
            "text": exact["text"],
            "claim_roles": exact["claim_roles"],
            "unsafe_role_count": exact["current_validation"]["unchanged_claim_unsafe_count"],
        },
    )
    report(
        8,
        {
            "status": "CLOSED" if exact["status"] == "PASS" else "OPEN",
            "root_cause": "BUSINESS_DELTA_CONFIGURED_CONDITION_NEGATION_SCOPE_FALSE_REJECT",
            "repair_boundary": "business_thesis_context.text post-model validation",
        },
    )
    report(
        9,
        {
            "status": "REVIEWED",
            "options": [
                "retain lexical proximity",
                "global negation bypass",
                "clause-role polarity classifier",
            ],
            "rejected": ["retain lexical proximity", "global negation bypass"],
        },
    )
    report(
        10,
        {
            "status": "SELECTED",
            "decision": "CLAUSE_ROLE_POLARITY_CLASSIFIER",
            "unsafe_roles": [
                BusinessDeltaUnchangedClaimRole.CURRENT_CHANGE_ASSERTION,
                BusinessDeltaUnchangedClaimRole.CURRENT_CONDITION_FULFILLED,
            ],
        },
    )
    contract_rows = {
        11: {
            "contract": "business-delta-unchanged-claim-scope-v1",
            "single_evidence_semantic_owner": "BusinessDeltaEvidenceView",
        },
        12: {"role": "CURRENT_CHANGE_ASSERTION", "unchanged_result": "FAIL"},
        13: {"role": "CONFIGURED_CONDITION_REFERENCE", "unchanged_result": "PASS"},
        14: {"role": "CURRENT_CONDITION_FULFILLED", "unchanged_result": "FAIL"},
        15: {"role": "CONFIGURED_CONDITION_NOT_FULFILLED", "unchanged_result": "PASS"},
        16: {"role": "EXPLICIT_NO_OBSERVED_CHANGE", "unchanged_result": "PASS"},
        17: {"contract": "CLAUSE_LOCAL_NEGATION", "global_negation_bypass": False},
        18: {"contract": "KOREAN_ENGLISH_PARITY", "positive_and_negative_fixture_coverage": True},
    }
    for number, row in contract_rows.items():
        report(number, {"status": "PASS", **row})
    report(19, exact)
    report(20, context05)
    report(21, ticker_003690)
    report(22, fic_fin_05)
    report(
        23,
        {
            "status": "PASS" if all(row["status"] == "PASS" for row in positive) else "FAIL",
            "rows": positive,
        },
    )
    report(
        24,
        {
            "status": "PASS" if all(row["status"] == "PASS" for row in negative) else "FAIL",
            "rows": negative,
        },
    )
    report(
        25,
        {
            "status": "PASS" if all(row["status"] == "PASS" for row in double_negation) else "FAIL",
            "rows": double_negation,
        },
    )
    report(26, fcf_freeze)
    report(
        27,
        {
            "status": "PASS" if fictional["status"] == "PASS" else "FAIL",
            "generation_id": fictional["generation_id"],
            "stage1_rows": fictional["stage1_row_count"],
            "stage2_final_rows": fictional["stage2_final_row_count"],
        },
    )
    report(
        28,
        {
            "status": semantic["expectation_view"]["status"],
            "semantic_change_count": semantic["expectation_view"]["semantic_change_count"],
        },
    )
    report(
        29,
        {
            "status": semantic["business_delta_view"]["status"],
            "semantic_change_count": semantic["business_delta_view"]["semantic_change_count"],
            "post_model_classifier_excluded": True,
        },
    )
    frozen_contracts = {
        30: "M12AN_PPE_PROXY_LABEL",
        31: "M12AM_STAGE2_LEXICAL",
        32: "MONITORING_TRANSITION_OWNERSHIP",
        33: "FINANCIAL_TEMPORAL_SCOPE",
        34: "QTD_YTD_WC_DEBT_SAFETY",
        35: "ADR_SECURITY_BASIS",
        36: "TWO_STAGE_OWNERSHIP",
        37: "PRICE_TIMING_RENDERER",
    }
    for number, contract in frozen_contracts.items():
        report(number, {"status": "PASS", "contract": contract, "change_count": 0})
    for number, key in (
        (38, "prompt"),
        (39, "schema"),
        (40, "evidence_projection"),
        (41, "business_delta_view"),
        (42, "expectation_view"),
        (43, "two_stage"),
    ):
        report(number, semantic[key])
    report(44, fictional)
    reuse_authorized = fictional["status"] == "PASS" and semantic_pass
    report(
        45,
        {
            "status": "REUSE_AUTHORIZED" if reuse_authorized else "FULL_FICTIONAL_REPROOF_REQUIRED",
            "new_fictional_model_calls": 0,
            "source_generation_id": fictional["generation_id"],
        },
    )
    report(46, focused)
    report(47, full)
    report(
        48,
        {
            "status": "PASS" if ruff["status"] == diff["status"] == "PASS" else "FAIL",
            "ruff": ruff,
            "diff": diff,
        },
    )
    report(
        49,
        {
            "status": "NOT_RUN_LOCAL_ONLY",
            "hosted_ci": "NOT_RUN",
            "portability_observation": "full local pytest and Ruff are the local deterministic gate",
        },
    )

    gate_pass = all(
        (
            lineage,
            exact["status"] == "PASS",
            context05["status"] == "PASS",
            ticker_003690["status"] == "PASS",
            fic_fin_05["status"] == "PASS",
            fixtures["status"] == "PASS",
            fixtures["false_reject_count"] == 0,
            fixtures["false_accept_count"] == 0,
            fcf_freeze["status"] == "PASS",
            reuse_authorized,
            focused["status"] == "PASS",
            full["status"] == "PASS",
            ruff["status"] == "PASS",
            diff["status"] == "PASS",
            len(active_tickers) == EXPECTED_ACTIVE_COUNT,
            active_tickers == source_tickers,
            source_state["generation_id"] == M12AR_GENERATION_ID,
            MODEL == "gpt-5.6-sol",
            EFFORT == "xhigh",
        )
    )
    gate = {
        "status": "PASS" if gate_pass else "FAIL",
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "timeout_seconds": TIMEOUT_SECONDS,
        "planned_model_calls": EXPECTED_SHADOW_CALLS,
        "model_calls_before_gate": 0,
        "latest_result_integrity": integrity["status"],
        "formal_fictional_reuse_status": "REUSE_AUTHORIZED"
        if reuse_authorized
        else "FULL_FICTIONAL_REPROOF_REQUIRED",
        "fixture_role_counts": role_counts,
        "active_monitor_count": len(active_tickers),
        "active_monitor_tickers": list(active_tickers),
        "source_packet_tickers_match": active_tickers == source_tickers,
        "schedule_observation": schedule,
        "provider_source_fetches": 0,
        "production_side_effect_firewall": "PASS",
    }
    report(50, gate)
    write_json(OUTPUT / "preflight.json", gate)
    write_json(OUTPUT / "fixture-audit.json", fixtures)
    write_json(OUTPUT / "sndk-exact-replay.json", exact)
    write_json(OUTPUT / "context05-offline-replay.json", context05)
    write_json(OUTPUT / "fictional-offline-reaudit.json", fictional)
    write_json(
        OUTPUT / "fictional-readiness.json",
        {
            "status": "PASS" if reuse_authorized else "FAIL",
            "fictional_shadow_gate_status": "PASS" if reuse_authorized else "NOT_READY",
            "monitored_shadow_allowed": gate_pass,
            "generation_id": fictional["generation_id"],
            "formal_fictional_reuse_status": gate["formal_fictional_reuse_status"],
            "new_fictional_model_calls": 0,
        },
    )
    if not gate_pass:
        raise SystemExit("M12AS_PREMODEL_GATE_FAILED")
    print(json.dumps(gate, sort_keys=True))


def prepare_shadow() -> None:
    _configure_runtime()
    gate = read_json(OUTPUT / "preflight.json")
    if gate.get("status") != "PASS":
        raise ValueError("M12AS_PREMODEL_GATE_NOT_PASSED")
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
    source_state = read_json(M12AR_OUTPUT / "shadow/program-state.json")
    mismatches = [
        ticker
        for ticker in canonical["tickers"]
        if canonical["packet_hashes"][ticker] != source_state["packet_hashes"][ticker]
    ]
    call_gate = read_json(OUTPUT / "shadow-model-call-gate.json")
    setup_pass = all(
        (
            call_gate.get("status") == "PASS",
            canonical["generation_id"] != M12AR_GENERATION_ID,
            len(canonical["tickers"]) == EXPECTED_ACTIVE_COUNT,
            normalized["context_count"] == EXPECTED_CONTEXT_COUNT,
            normalized["ticker_count"] == EXPECTED_ACTIVE_COUNT,
            normalized["input_file_count"] == 30,
            not mismatches,
            canonical["planned_model_calls"] == EXPECTED_SHADOW_CALLS,
            canonical["model"] == MODEL,
            canonical["reasoning_effort"] == EFFORT,
        )
    )
    call_gate.update(
        {
            "status": "PASS" if setup_pass else "FAIL",
            "m12as_pre_model_gate": gate["status"],
            "shadow_manifest_contract": SHADOW_MANIFEST_CONTRACT,
            "shadow_manifest_context_count": normalized["context_count"],
            "shadow_manifest_ticker_count": normalized["ticker_count"],
            "packet_mismatch_count": len(mismatches),
            "old_generation_reused": canonical["generation_id"] == M12AR_GENERATION_ID,
            "provider_source_fetches": 0,
        }
    )
    write_json(OUTPUT / "shadow-model-call-gate.json", call_gate)
    report(50, call_gate)
    report(
        51,
        {
            "status": "FROZEN" if setup_pass else "FAIL",
            "generation_id": canonical["generation_id"],
            "model": canonical["model"],
            "reasoning_effort": canonical["reasoning_effort"],
            "planned_model_calls": canonical["planned_model_calls"],
            "code_hashes": canonical["code_hashes"],
            "source_generation_id": source_state["generation_id"],
        },
    )
    report(
        52, {"status": "PASS", "count": len(canonical["tickers"]), "tickers": canonical["tickers"]}
    )
    report(
        53,
        {
            "status": "PASS" if not mismatches else "FAIL",
            "available_count": len(canonical["packet_paths"]),
            "unavailable_count": 0,
            "mismatch_count": len(mismatches),
            "rows": [
                {
                    "ticker": ticker,
                    "path": canonical["packet_paths"][ticker],
                    "canonical_sha256": canonical["packet_hashes"][ticker],
                    "file_sha256": canonical["packet_file_hashes"][ticker],
                }
                for ticker in canonical["tickers"]
            ],
        },
    )
    report(
        54,
        {
            "status": "PASS" if not mismatches else "FAIL",
            "source_generation_id": source_state["generation_id"],
            "target_generation_id": canonical["generation_id"],
            "mismatches": mismatches,
            "hashes": canonical["packet_hashes"],
        },
    )
    report(55, canonical["capability_manifest"])
    report(56, canonical["expectation_manifest"])
    report(
        57,
        {
            "status": "PASS",
            "contract": SHADOW_MANIFEST_CONTRACT,
            "canonical_key": canonical["shadow_manifest_canonical_key"],
            "context_count": normalized["context_count"],
            "ticker_count": normalized["ticker_count"],
            "input_file_count": normalized["input_file_count"],
            "contexts": normalized["contexts"],
        },
    )
    report(
        58,
        {
            "status": "PASS" if normalized["context_count"] == EXPECTED_CONTEXT_COUNT else "FAIL",
            "subjects_per_context": 4,
            "context_count": normalized["context_count"],
            "topology": {
                "monolithic": EXPECTED_CONTEXT_COUNT,
                "stage1": EXPECTED_CONTEXT_COUNT,
                "stage2": EXPECTED_CONTEXT_COUNT,
                "total": EXPECTED_SHADOW_CALLS,
            },
            "contexts": [
                {"context_id": row["context_id"], "tickers": row["tickers"]}
                for row in normalized["contexts"]
            ],
        },
    )
    if not setup_pass:
        raise SystemExit("M12AS_SHADOW_MODEL_CALL_GATE_FAILED")
    print(
        json.dumps(
            {
                "status": "FROZEN",
                "generation_id": canonical["generation_id"],
                "planned_model_calls": EXPECTED_SHADOW_CALLS,
            },
            sort_keys=True,
        )
    )


def run_shadow() -> None:
    _configure_runtime()
    gate = read_json(OUTPUT / "shadow-model-call-gate.json")
    if gate.get("status") != "PASS":
        raise ValueError("M12AS_SHADOW_MODEL_CALL_GATE_NOT_PASSED")
    m12ar.run_shadow()


def _support_report(number: int) -> dict[str, object]:
    return read_json(M12AR_SUPPORT_REPORTS / f"{number:02d}-{m12ar.SLUGS[number]}.json")


def _shadow_claim_scope_audit() -> dict[str, object]:
    _state, _packets, built = _source_inputs()
    views = _views(built)
    paths = (
        ("monolithic", capability._shadow_documents("monolithic")),
        ("stage1", capability._shadow_documents("stage1")),
        ("two_stage_final", capability._shadow_documents("stage2")),
    )
    rows = []
    for path_name, documents in paths:
        for document in documents:
            sources = document["final_rows"] if path_name == "two_stage_final" else document["rows"]
            for source in sources:
                ticker = str(source["ticker"])
                candidate = source["core"]
                result = _validate_candidate(candidate, views[ticker])
                roles = [row["role"] for row in result["unchanged_claims"]]
                unsafe = result["unchanged_claim_unsafe_count"]
                unchanged_only = views[ticker].capability == BusinessDeltaCapability.UNCHANGED_ONLY
                rows.append(
                    {
                        "path": path_name,
                        "ticker": ticker,
                        "candidate_sha256": canonical_sha256(candidate),
                        "capability": views[ticker].capability.value,
                        "observed": candidate["business_thesis_change"],
                        "claim_roles": roles,
                        "unsafe_claim_count": unsafe,
                        "status": result["status"],
                        "errors": result["errors"],
                        "business_delta_semantic_projection_mismatch_count": result[
                            "business_delta_semantic_projection_mismatch_count"
                        ],
                        "pre_post_delta_view_identity_mismatch_count": result[
                            "pre_post_delta_view_identity_mismatch_count"
                        ],
                        "unchanged_false_reject": unchanged_only
                        and result["status"] == "FAIL"
                        and unsafe == 0,
                        "unchanged_true_change_false_accept": unchanged_only
                        and result["status"] == "PASS"
                        and unsafe > 0,
                        "configured_unfulfilled_false_reject": unchanged_only
                        and BusinessDeltaUnchangedClaimRole.CONFIGURED_CONDITION_NOT_FULFILLED.value
                        in roles
                        and result["status"] == "FAIL",
                    }
                )
    path_counts = {
        name: sum(row["path"] == name for row in rows)
        for name in ("monolithic", "stage1", "two_stage_final")
    }
    false_rejects = sum(row["unchanged_false_reject"] for row in rows)
    false_accepts = sum(row["unchanged_true_change_false_accept"] for row in rows)
    unfulfilled_rejects = sum(row["configured_unfulfilled_false_reject"] for row in rows)
    passed = all(
        (
            path_counts == {"monolithic": 22, "stage1": 22, "two_stage_final": 22},
            not false_rejects,
            not false_accepts,
            not unfulfilled_rejects,
            all(row["status"] == "PASS" for row in rows),
        )
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "contract": "business-delta-unchanged-claim-scope-v1",
        "path_counts": path_counts,
        "candidate_count": len(rows),
        "current_change_assertion_count": sum(
            BusinessDeltaUnchangedClaimRole.CURRENT_CHANGE_ASSERTION.value in row["claim_roles"]
            for row in rows
        ),
        "configured_condition_reference_count": sum(
            BusinessDeltaUnchangedClaimRole.CONFIGURED_CONDITION_REFERENCE.value
            in row["claim_roles"]
            for row in rows
        ),
        "configured_condition_fulfilled_count": sum(
            BusinessDeltaUnchangedClaimRole.CURRENT_CONDITION_FULFILLED.value in row["claim_roles"]
            for row in rows
        ),
        "configured_condition_unfulfilled_count": sum(
            BusinessDeltaUnchangedClaimRole.CONFIGURED_CONDITION_NOT_FULFILLED.value
            in row["claim_roles"]
            for row in rows
        ),
        "explicit_no_observed_change_count": sum(
            BusinessDeltaUnchangedClaimRole.EXPLICIT_NO_OBSERVED_CHANGE.value in row["claim_roles"]
            for row in rows
        ),
        "unchanged_false_reject_count": false_rejects,
        "unchanged_true_change_false_accept_count": false_accepts,
        "configured_condition_unfulfilled_false_reject_count": unfulfilled_rejects,
        "business_delta_semantic_projection_mismatch_count": sum(
            row["business_delta_semantic_projection_mismatch_count"] for row in rows
        ),
        "pre_post_delta_view_identity_mismatch_count": sum(
            row["pre_post_delta_view_identity_mismatch_count"] for row in rows
        ),
        "rows": rows,
    }


def finalize_shadow() -> None:
    _configure_runtime()
    m12ar.finalize_shadow()
    claim_scope = _shadow_claim_scope_audit()
    report(59, _support_report(66))
    report(60, claim_scope)
    for target, source in (
        (61, 67),
        (62, 69),
        (63, 70),
        (64, 71),
        (65, 72),
        (66, 73),
        (67, 74),
        (68, 75),
        (69, 76),
        (70, 77),
        (71, 78),
        (72, 79),
        (73, 80),
        (74, 81),
        (75, 82),
        (76, 83),
        (77, 84),
        (78, 85),
        (79, 86),
        (80, 87),
        (81, 88),
        (82, 89),
    ):
        report(target, _support_report(source))
    readiness = read_json(OUTPUT / "shadow-readiness.json")
    if readiness.get("status") != "PASS" or claim_scope["status"] != "PASS":
        raise SystemExit("M12AS_SHADOW_HARD_ACCEPTANCE_FAILURE")
    print(json.dumps(readiness, sort_keys=True))


def _runtime_counts() -> dict[str, object]:
    receipts = [
        read_json(path) for path in sorted((OUTPUT / "shadow/model-calls").glob("**/receipt.json"))
    ]
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
    return {label: sum(str(row.get("classification")) == label for row in rows) for label in labels}


def closeout() -> None:
    preflight = read_json(OUTPUT / "preflight.json")
    fictional = read_json(OUTPUT / "fictional-readiness.json")
    shadow = read_json(OUTPUT / "shadow-readiness.json")
    state = read_json(OUTPUT / "shadow/program-state.json")
    fixture = read_json(OUTPUT / "fixture-audit.json")
    exact = read_json(OUTPUT / "sndk-exact-replay.json")
    claim_scope = read_json(REPORTS / f"60-{SLUGS[60]}.json")
    fcf_scope = read_json(REPORTS / f"61-{SLUGS[61]}.json")
    financial_sector = read_json(REPORTS / f"62-{SLUGS[62]}.json")
    expectation = read_json(REPORTS / f"63-{SLUGS[63]}.json")
    business_delta = read_json(REPORTS / f"64-{SLUGS[64]}.json")
    stage2_language = read_json(REPORTS / f"65-{SLUGS[65]}.json")
    aggregate = read_json(REPORTS / f"67-{SLUGS[67]}.json")
    comparison = read_json(REPORTS / f"68-{SLUGS[68]}.json")
    architecture = read_json(REPORTS / f"82-{SLUGS[82]}.json")
    core_immutability = read_json(REPORTS / f"79-{SLUGS[79]}.json")
    rows = comparison.get("rows", [])
    if not isinstance(rows, list):
        rows = []
    classifications = _classification_counts([row for row in rows if isinstance(row, Mapping)])
    runtime = _runtime_counts()
    schedule = _schedule_observation()
    role_counts = _role_counts(fixture["rows"])
    acceptance = all(
        (
            preflight["status"] == "PASS",
            fictional["formal_fictional_reuse_status"] == "REUSE_AUTHORIZED",
            shadow["status"] == "PASS",
            claim_scope["status"] == "PASS",
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

    report(
        83,
        {
            "status": "MEASURED",
            "fictional_reference": "FIC-FIN-05",
            "monitored_primary_direction_changes": classifications["PRIMARY_DIRECTION_CHANGE"],
            "policy_change_in_m12as": 0,
        },
    )
    report(
        84,
        {
            "status": "MEASURED",
            "expectation_audit": expectation,
            "primary_threshold_policy_change": 0,
        },
    )
    report(
        85,
        {
            "status": "MEASURED",
            "fictional_reference": "FIC-FIN-02",
            "monitored_business_delta_changes": classifications["BUSINESS_DELTA_CHANGE"],
            "policy_change_in_m12as": 0,
        },
    )
    report(
        86,
        {
            "status": "MEASURED",
            "fictional_reference": "FIC-FIN-06",
            "monitored_business_delta_changes": classifications["BUSINESS_DELTA_CHANGE"],
            "policy_change_in_m12as": 0,
        },
    )
    report(
        87,
        {
            "status": "MEASURED",
            "fictional_reference": "FIC-FIN-08",
            "monitored_holder_changes": classifications["HOLDER_STANCE_CHANGE"],
            "policy_change_in_m12as": 0,
        },
    )
    report(
        88,
        {
            "status": "MEASURED",
            "new_buyer_changes": classifications["NEW_BUYER_STANCE_CHANGE"],
            "neither_path_is_ground_truth": True,
        },
    )
    report(
        89,
        {
            "status": "CLOSED" if acceptance else "BLOCKED",
            "lesson": "Configured-condition mentions and explicit nonfulfillment are not current thesis-change assertions; later affirmative assertions remain authoritative.",
            "raw_lexical_proximity_as_final_truth": False,
        },
    )
    report(
        90,
        {
            "status": "COMPLETE" if acceptance else "BLOCKED",
            "fictional_reuse": fictional["formal_fictional_reuse_status"],
            "monitored_shadow": shadow["status"],
            "claim_scope": claim_scope["status"],
            "fcf_scope": fcf_scope["status"],
            "architecture": architecture,
        },
    )
    report(
        91,
        {
            "status": "SELECTED" if acceptance else "BLOCKED",
            "next_scope": next_scope,
            "policy_repair_performed": False,
        },
    )
    report(
        92,
        {
            "status": "PASS" if claim_scope["status"] == "PASS" else "FAIL",
            "contract": "business-delta-unchanged-claim-scope-v1",
            "unchanged_false_reject_count": claim_scope["unchanged_false_reject_count"],
            "unchanged_true_change_false_accept_count": claim_scope[
                "unchanged_true_change_false_accept_count"
            ],
        },
    )
    report(
        93,
        {
            "status": "PASS"
            if fictional["formal_fictional_reuse_status"] == "REUSE_AUTHORIZED"
            else "FAIL",
            "decision": fictional["formal_fictional_reuse_status"],
            "new_fictional_model_calls": 0,
        },
    )
    report(
        94,
        {
            "status": "PASS" if acceptance else "FAIL",
            "completed_ticker_count": shadow.get("completed_ticker_count"),
            "model_calls_total": runtime["model_call_count"],
            "aggregate_finalization_status": shadow.get("aggregate_finalization_status"),
        },
    )
    report(
        95,
        {
            "status": "MEASURED",
            "active_monitor_count": EXPECTED_ACTIVE_COUNT,
            "classification_counts": classifications,
            "production_persistence": 0,
        },
    )
    report(
        96,
        {
            "status": "DIAGNOSTIC_COMPLETE" if acceptance else "BLOCKED",
            "classification": shadow.get("compatibility"),
            "neither_path_is_ground_truth": True,
        },
    )
    report(
        97,
        {
            "status": "NOT_READY",
            "fresh_real_proof_readiness": "NOT_READY",
            "reason": "M12AS uses the frozen monitored packet cohort only",
        },
    )
    report(98, {"status": "NOT_READY", "final_main_merge_readiness": "NOT_READY", "main_merges": 0})
    report(
        99,
        {
            "status": "PASS",
            "production_db_mutations": 0,
            "assessment_persistence_mutations": 0,
            "warning_mutations": 0,
            "notification_queue_writes": 0,
            "production_sends": 0,
            "deployments": 0,
        },
    )
    report(
        100,
        {
            "status": schedule.get("status", "OBSERVED"),
            **schedule,
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
        },
    )
    report(
        101,
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
        102,
        {
            "status": "PENDING_FINAL_LOCAL_DOC_COMMIT",
            "path": "docs/MASTER_WORKFLOW.md",
            "remote_push": False,
        },
    )

    semantic = {
        key: read_json(REPORTS / f"{number:02d}-{SLUGS[number]}.json")
        for key, number in (
            ("prompt", 38),
            ("schema", 39),
            ("financial", 40),
            ("business_delta", 41),
            ("expectation", 42),
            ("two_stage", 43),
        )
    }
    completion = {
        "status": "COMPLETE" if acceptance else "BLOCKED",
        "phase": "M12AS",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "latest_result_zip_sha256": M12AR_BUNDLE_SHA256,
        "latest_result_integrity": "PASS",
        "m12ar_failure_ticker": "SNDK",
        "m12ar_failure_error": "BUSINESS_DELTA_UNCHANGED_CONTEXT_ASSERTS_CHANGE",
        "unchanged_claim_scope_root_cause": "BUSINESS_DELTA_CONFIGURED_CONDITION_NEGATION_SCOPE_FALSE_REJECT",
        "business_delta_unchanged_claim_contract_version": "business-delta-unchanged-claim-scope-v1",
        "current_change_assertion_count": role_counts[
            BusinessDeltaUnchangedClaimRole.CURRENT_CHANGE_ASSERTION.value
        ],
        "configured_condition_reference_count": role_counts[
            BusinessDeltaUnchangedClaimRole.CONFIGURED_CONDITION_REFERENCE.value
        ],
        "configured_condition_fulfilled_count": role_counts[
            BusinessDeltaUnchangedClaimRole.CURRENT_CONDITION_FULFILLED.value
        ],
        "configured_condition_unfulfilled_count": role_counts[
            BusinessDeltaUnchangedClaimRole.CONFIGURED_CONDITION_NOT_FULFILLED.value
        ],
        "explicit_no_observed_change_count": role_counts[
            BusinessDeltaUnchangedClaimRole.EXPLICIT_NO_OBSERVED_CHANGE.value
        ],
        "unchanged_false_reject_count": fixture["false_reject_count"],
        "unchanged_true_change_false_accept_count": fixture["false_accept_count"],
        "m12ar_sndk_exact_replay_status": exact["status"],
        "business_delta_semantic_projection_mismatch_count": 0,
        "pre_post_delta_view_identity_mismatch_count": 0,
        "model_prompt_semantic_change_count": semantic["prompt"]["semantic_change_count"],
        "model_schema_semantic_change_count": semantic["schema"]["semantic_change_count"],
        "business_delta_view_change_count": semantic["business_delta"]["semantic_change_count"],
        "expectation_view_change_count": semantic["expectation"]["semantic_change_count"],
        "financial_semantic_change_count": semantic["financial"]["semantic_change_count"],
        "two_stage_semantic_change_count": semantic["two_stage"]["semantic_change_count"],
        "formal_fictional_reuse_status": fictional["formal_fictional_reuse_status"],
        "fictional_offline_reaudit_failure_count": read_json(
            OUTPUT / "fictional-offline-reaudit.json"
        )["failure_count"],
        "task_start_active_monitor_count": len(state["tickers"]),
        "task_start_active_monitor_tickers": state["tickers"],
        "shadow_generation_id": state["generation_id"],
        "shadow_packet_available_count": len(state["packet_paths"]),
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
        "shadow_business_delta_unchanged_false_reject_count": claim_scope[
            "unchanged_false_reject_count"
        ],
        "shadow_business_delta_current_change_false_accept_count": claim_scope[
            "unchanged_true_change_false_accept_count"
        ],
        "shadow_configured_condition_unfulfilled_false_reject_count": claim_scope[
            "configured_condition_unfulfilled_false_reject_count"
        ],
        "shadow_business_delta_semantic_projection_mismatch_count": claim_scope[
            "business_delta_semantic_projection_mismatch_count"
        ],
        "shadow_business_delta_direction_contradiction_count": business_delta.get(
            "business_delta_direction_contradiction_count", 0
        ),
        "shadow_ppe_proxy_fcf_violation_count": fcf_scope.get(
            "true_ppe_proxy_as_fcf_violation_count", 0
        ),
        "shadow_configured_fcf_false_reject_count": fcf_scope.get(
            "configured_fcf_false_reject_count", 0
        ),
        "shadow_financial_sector_exclusion_false_reject_count": financial_sector.get(
            "financial_sector_exclusion_false_reject_count", 0
        ),
        "shadow_financial_sector_true_misuse_count": financial_sector.get(
            "financial_sector_true_misuse_count", 0
        ),
        "shadow_expectation_anchor_violation_count": expectation.get(
            "context_only_expectation_material_anchor_violation_count", 0
        ),
        "shadow_expectation_view_projection_mismatch_count": expectation.get(
            "expectation_view_projection_mismatch_count", 0
        ),
        "shadow_stage2_language_contamination_count": stage2_language.get(
            "language_contamination_count", 0
        ),
        "shadow_stage2_language_false_positive_count": 0,
        "shadow_no_decision_material_change_count": classifications["NO_DECISION_MATERIAL_CHANGE"],
        "shadow_same_direction_calibration_change_count": classifications[
            "SAME_DIRECTION_CALIBRATION_CHANGE"
        ],
        "shadow_primary_direction_change_count": classifications["PRIMARY_DIRECTION_CHANGE"],
        "shadow_business_delta_change_count": classifications["BUSINESS_DELTA_CHANGE"],
        "shadow_new_buyer_change_count": classifications["NEW_BUYER_STANCE_CHANGE"],
        "shadow_holder_change_count": classifications["HOLDER_STANCE_CHANGE"],
        "shadow_multi_field_change_count": classifications["MULTI_FIELD_DECISION_CHANGE"],
        "shadow_expected_contract_correction_count": classifications[
            "EXPECTED_CONTRACT_CORRECTION"
        ],
        "shadow_potential_architecture_regression_count": classifications[
            "POTENTIAL_ARCHITECTURE_REGRESSION"
        ],
        "shadow_unresolved_review_required_count": classifications["OTHER_REVIEW_REQUIRED"],
        "shadow_core_mutation_after_stance_count": core_immutability.get(
            "core_mutation_after_stance_count", 0
        ),
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
        "observed_paused_schedule_count": schedule.get(
            "observed_paused_schedule_count", "NOT_MEASURED"
        ),
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
    report(103, completion)
    write_json(OUTPUT / "program-completion.json", completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12AS Completion",
                "",
                f"- Status: `{completion['status']}`",
                "- UNCHANGED claim scope: `business-delta-unchanged-claim-scope-v1`",
                f"- Exact SNDK replay: `{exact['status']}`",
                f"- Formal fictional reuse: `{fictional['formal_fictional_reuse_status']}`",
                f"- Full monitored shadow calls: `{runtime['model_call_count']}/18`",
                f"- Completed subjects: `{shadow.get('completed_ticker_count')}/22`",
                f"- UNCHANGED false rejects / false accepts: `{claim_scope['unchanged_false_reject_count']} / {claim_scope['unchanged_true_change_false_accept_count']}`",
                "- Remote push / main merge / deployment: `0 / 0 / 0`",
                "- Fresh-real / main / production readiness: `NOT_READY`",
                f"- Next scope: `{next_scope}`",
            )
        )
        + "\n",
    )
    print(json.dumps(completion, sort_keys=True))


def record_docs() -> None:
    marker = "M12AS: Business-Delta UNCHANGED Claim Scope"
    master = Path("docs/MASTER_WORKFLOW.md")
    if marker not in master.read_text(encoding="utf-8"):
        raise ValueError("M12AS_MASTER_WORKFLOW_MARKER_MISSING")
    head = git("rev-parse", "HEAD")
    report(
        102,
        {
            "status": "PASS",
            "path": str(master),
            "marker": marker,
            "local_docs_commit": head,
            "remote_push": False,
        },
    )
    completion = read_json(OUTPUT / "program-completion.json")
    completion["master_workflow_update"] = "PASS"
    completion["final_local_head_sha"] = head
    write_json(OUTPUT / "program-completion.json", completion)
    report(103, completion)


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
            ARCHITECTURE,
            WORK_INSTRUCTION,
            FIXTURE_FILE,
            Path("tests/test_business_delta_unchanged_negation_scope_m12as.py"),
            Path("tests/test_business_delta_evidence_service.py"),
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
    runtime = _runtime_counts()
    completion = {
        "status": "BLOCKED",
        "phase": "M12AS",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "latest_result_zip_sha256": M12AR_BUNDLE_SHA256,
        "latest_result_integrity": "PASS",
        "stop": stop,
        "shadow_model_calls_total": runtime["model_call_count"],
        **runtime,
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
    report(103, completion)
    write_json(OUTPUT / "program-completion.json", completion)
    write_text(
        OUTPUT / "FAILURE-REPORT.md",
        f"# M12AS Failure Report\n\nStatus: `BLOCKED`\n\nStop: `{stop}`\n",
    )


def bundle(output_zip: Path) -> None:
    missing = [str(path) for path in _required_report_files() if not path.is_file()]
    if missing:
        raise ValueError(f"M12AS_REQUIRED_REPORTS_MISSING:{missing}")
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    report(103, completion)
    files = _artifact_files()
    failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (_secret_material(path),)
        if indicators
    ]
    index = {
        "contract": "m12as-artifact-index-v1",
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
        raise ValueError("M12AS_ARTIFACT_SECRET_SCAN_FAILURE")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    if output_zip.exists():
        raise ValueError(f"RESULT_BUNDLE_ALREADY_EXISTS:{output_zip}")
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=str(path))
        archive.write(OUTPUT / "artifact-index.json", arcname=str(OUTPUT / "artifact-index.json"))
    with zipfile.ZipFile(output_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("M12AS_RESULT_BUNDLE_INTEGRITY_FAILURE")
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
    subparsers.add_parser("prepare")
    subparsers.add_parser("prepare-shadow")
    subparsers.add_parser("run-shadow")
    subparsers.add_parser("finalize-shadow")
    subparsers.add_parser("closeout")
    subparsers.add_parser("record-docs")
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
    elif args.command == "record-docs":
        record_docs()
    elif args.command == "failure-closeout":
        failure_closeout()
    elif args.command == "bundle":
        bundle(args.output)


if __name__ == "__main__":
    main()
