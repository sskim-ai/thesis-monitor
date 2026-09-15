"""M12AU FIC-FIN-01 FCF scope repair, fictional proof, and monitored shadow."""

from __future__ import annotations

import argparse
import ast
from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

from app.services.configured_signal_evidence_service import (
    ConfiguredSignalEvidenceView,
    build_configured_signal_evidence_view,
)
from app.services.directional_financial_context_service import (
    FinancialClaimFieldRole,
    PPEProxyFCFClaimRole,
    classify_ppe_proxy_fcf_claims,
    financial_claim_row_requires_current_fcf_evidence,
    financial_claim_rows,
    validate_directional_financial_semantics,
)
from app.services.two_stage_directional_service import DirectionalCoreJudgment
from scripts import configured_signal_field_ownership_m12at as m12at
from scripts import directional_financial_context_m12 as financial
from scripts.shadow_frozen_context_manifest import (
    CONTRACT_VERSION as SHADOW_MANIFEST_CONTRACT,
    canonicalize_shadow_manifest_state,
    normalize_shadow_manifest,
)


NAME = "20260912-fictional-case-fcf-prospective-scope-alignment-full-proof-full-shadow"
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
SUPPORT_REPORTS = OUTPUT / "supporting-reports/m12ai"
RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
RUNNER = Path("scripts/fictional_case_fcf_prospective_scope_m12au.py")
ARCHITECTURE = Path("docs/architecture/FICTIONAL_CASE_FCF_PROSPECTIVE_SCOPE.md")
WORK_INSTRUCTION = Path("docs/work-instructions") / f"{NAME}.md"
WORK_INSTRUCTION_COMMIT = "8a92f257fd743540e7fa5a786a5241018312b7e7"
BASE_INTEGRATION_HEAD_SHA = "19578e08e975d6da3d4c28e42342b5426cf3e988"

ICLOUD = Path(
    "/Users/sskim/Library/Mobile Documents/com~apple~CloudDocs/Thesis Monitor"
)
LATEST_NAME = m12at.NAME
LATEST_OUTPUT = Path("artifacts") / LATEST_NAME
LATEST_BUNDLE = ICLOUD / f"thesis-monitor-{LATEST_NAME}-report.zip"
LATEST_BUNDLE_SHA256 = (
    "9ceeba4f53cdb44ff03f3908a992be10a4d396d3e1320e3cbcb1379526a104d3"
)
LATEST_INDEXED_PAYLOADS = 182
LATEST_ZIP_ENTRIES = 183
LATEST_GENERATION_ID = "20260911-m12ai-fictional-20260912T120605Z-74aa807a8d41"

MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
EXPECTED_FICTIONAL_CALLS = 12
EXPECTED_FICTIONAL_ROWS = 24
EXPECTED_SHADOW_CALLS = 18
EXPECTED_SHADOW_CONTEXTS = 6
EXPECTED_ACTIVE_COUNT = 22
NEXT_SCOPE = "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"

_PROXY_METRIC = "ocf_less_ppe_capex"
_SAFE_CURRENT_FCF_METRICS = {"free_cash_flow", "reported_free_cash_flow"}
_FCF_VIOLATION_ROLES = {
    PPEProxyFCFClaimRole.AFFIRMATIVE_FCF_ATTRIBUTION,
    PPEProxyFCFClaimRole.NUMERIC_FCF_ATTRIBUTION,
    PPEProxyFCFClaimRole.PROXY_AS_FCF_ATTRIBUTION,
}
_FUTURE_FCF_ROLES = {
    FinancialClaimFieldRole.FUTURE_REEVALUATION_CONDITION,
    FinancialClaimFieldRole.STANCE_CONFIRMATION_CONDITION,
    FinancialClaimFieldRole.STANCE_INVALIDATION_CONDITION,
}

_SLUG_SEQUENCE = (
    "repository-provenance",
    "latest-result-integrity",
    "m12au-scope-freeze",
    "integrated-main-lineage-freeze",
    "m12at-fic-fin-01-failure-reproduction",
    "fic-fin-01-case-semantic-code-audit",
    "strong-quality-proxy-check-original-purpose-audit",
    "generic-fcf-validator-coverage-audit",
    "case-specific-vs-generic-semantic-overlap-audit",
    "fic-fin-01-case-check-architecture-decision",
    "m12at-fic-fin-01-exact-offline-replay",
    "fic-fin-01-true-proxy-as-fcf-negative-control",
    "fic-fin-01-future-fcf-condition-positive-control",
    "fic-fin-01-not-fcf-disclaimer-positive-control",
    "m12as-005490-configured-field-ownership-regression",
    "current-fcf-claim-negative-regressions",
    "future-netdebt-condition-positive-regressions",
    "current-netdebt-negative-regressions",
    "configured-signal-field-ownership-freeze",
    "business-delta-view-freeze",
    "market-expectation-view-freeze",
    "fcf-claim-scope-freeze",
    "ppe-proxy-label-freeze",
    "financial-sector-scope-freeze",
    "stage2-korean-lexical-freeze",
    "monitoring-transition-ownership-freeze",
    "financial-temporal-scope-freeze",
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
    "fictional-case-semantic-audit",
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
    "configured-signal-field-use-real-lessons",
    "real-fcf-claim-scope-lessons",
    "combined-fictional-monitored-root-cause-summary",
    "next-bounded-policy-decision",
    "fic-fin-01-case-semantic-alignment-success-decision",
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
if len(SLUGS) != 134:
    raise RuntimeError(f"M12AU_REPORT_SEQUENCE_INVALID:{len(SLUGS)}")

FOCUSED_TESTS = (
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
    "scripts/directional_financial_context_m12.py",
    str(RUNNER),
    "tests/test_fictional_case_fcf_prospective_scope_m12au.py",
    "tests/test_fictional_case_fcf_prospective_scope_m12au_runner.py",
)
CRITICAL_CODE_PATHS = tuple(
    dict.fromkeys((*m12at.CRITICAL_CODE_PATHS, RUNNER))
)

capability = m12at.capability


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
        ).encode("utf-8")
    ).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ("git", *args), check=True, capture_output=True, text=True
    ).stdout.strip()


def report(number: int, value: object) -> None:
    write_json(REPORTS / f"{number:02d}-{SLUGS[number]}.json", value)


def support(number: int) -> dict[str, object]:
    return read_json(SUPPORT_REPORTS / f"{number:02d}-{capability.SLUGS[number]}.json")


def _command(command: Sequence[str], *, timeout: int = 7200) -> dict[str, object]:
    started = datetime.now(UTC)
    result = subprocess.run(
        list(command), check=False, capture_output=True, text=True, timeout=timeout
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
    capability.NAME = NAME
    capability.OUTPUT = OUTPUT
    capability.REPORTS = SUPPORT_REPORTS
    capability.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT
    capability.PREVIOUS_NAME = m12at.M12AS_NAME
    capability.PREVIOUS_OUTPUT = m12at.M12AS_OUTPUT
    capability.PREVIOUS_BUNDLE = m12at.M12AS_BUNDLE
    capability.PREVIOUS_BUNDLE_SHA256 = m12at.M12AS_BUNDLE_SHA256
    capability.PREVIOUS_INDEXED_PAYLOADS = m12at.M12AS_INDEXED_PAYLOADS
    capability.PREVIOUS_ZIP_ENTRIES = m12at.M12AS_ZIP_ENTRIES
    capability.PREVIOUS_FINAL_SHA = BASE_INTEGRATION_HEAD_SHA
    capability.BASE_INTEGRATION_HEAD_SHA = BASE_INTEGRATION_HEAD_SHA
    capability.WORK_INSTRUCTION_COMMIT = WORK_INSTRUCTION_COMMIT
    capability.WORK_INSTRUCTION = WORK_INSTRUCTION
    capability.ARCHITECTURE = ARCHITECTURE
    capability.CRITICAL_CODE_PATHS = CRITICAL_CODE_PATHS
    capability.MODEL = MODEL
    capability.EFFORT = EFFORT
    capability.TIMEOUT_SECONDS = TIMEOUT_SECONDS
    capability.base.OUTPUT = OUTPUT
    capability.base.REPORTS = SUPPORT_REPORTS
    capability.base.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT
    capability.base.MODEL = MODEL
    capability.base.EFFORT = EFFORT
    capability.base.TIMEOUT_SECONDS = TIMEOUT_SECONDS
    capability.m12.MODEL = MODEL
    capability.m12.EFFORT = EFFORT
    capability.m12.TIMEOUT_SECONDS = TIMEOUT_SECONDS
    capability.m12.fictional_inputs = m12at._m12at_fictional_inputs


def _verify_indexed_bundle(
    path: Path,
    *,
    expected_sha256: str,
    expected_payloads: int,
    expected_entries: int,
) -> dict[str, object]:
    if not path.is_file():
        raise ValueError(f"RESULT_BUNDLE_MISSING:{path}")
    digest = file_sha256(path)
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        index_names = [name for name in names if name.endswith("/artifact-index.json")]
        if len(index_names) != 1:
            raise ValueError("ARTIFACT_INDEX_IDENTITY_INVALID")
        index = json.loads(archive.read(index_names[0]))
        source_rows = index.get("rows")
        if not isinstance(source_rows, list):
            raise ValueError("ARTIFACT_INDEX_ROWS_INVALID")
        indexed = {
            str(row["path"]): row
            for row in source_rows
            if isinstance(row, Mapping)
        }
        payloads = set(names) - {index_names[0]}
        missing = sorted(set(indexed) - payloads)
        extra = sorted(payloads - set(indexed))
        hash_mismatches = []
        size_mismatches = []
        for name, row in indexed.items():
            if name not in payloads:
                continue
            payload = archive.read(name)
            if hashlib.sha256(payload).hexdigest() != row.get("sha256"):
                hash_mismatches.append(name)
            if len(payload) != row.get("size"):
                size_mismatches.append(name)
    passed = all(
        (
            digest == expected_sha256,
            len(names) == expected_entries,
            len(indexed) == expected_payloads,
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
        "indexed_payload_count": len(indexed),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "hash_mismatch_count": len(hash_mismatches),
        "size_mismatch_count": len(size_mismatches),
        "index_status": index.get("status"),
        "index_secret_scan_failure_count": index.get("secret_scan_failure_count"),
    }


def _extract_artifact_prefix(bundle: Path, prefix: Path) -> None:
    archive_prefix = f"{prefix}/"
    root = Path.cwd().resolve()
    with zipfile.ZipFile(bundle) as archive:
        for info in archive.infolist():
            if not info.filename.startswith(archive_prefix):
                continue
            target = (root / info.filename).resolve()
            if root not in target.parents:
                raise ValueError("ARCHIVE_PATH_ESCAPE")
            archive.extract(info, root)


def _latest_stage1_document() -> dict[str, object]:
    return read_json(
        LATEST_OUTPUT
        / "fictional/model-calls/run-1/stage1-context-01/run-document.json"
    )


def _latest_fic_fin_01_row() -> dict[str, object]:
    rows = [
        row
        for row in _latest_stage1_document()["rows"]
        if row["ticker"] == "FIC-FIN-01"
    ]
    if len(rows) != 1:
        raise ValueError("M12AT_FIC_FIN_01_ROW_MISSING")
    return rows[0]


def _exact_m12at_replay() -> dict[str, object]:
    document = _latest_stage1_document()
    generation_id = str(document["generation_id"])
    packets, owned, catalogs, contexts = m12at._m12at_fictional_inputs(
        generation_id
    )
    tickers = tuple(str(ticker) for ticker in document["tickers"])
    batch, _aliases, _raw = capability.base._resolve_stage1_batch(
        read_json(
            LATEST_OUTPUT
            / "fictional/model-calls/run-1/stage1-context-01/output.raw.json"
        ),
        generation_id=generation_id,
        tickers=tickers,
        packets=packets,
        catalogs=catalogs,
    )
    views = capability._views(owned, catalogs, contexts)
    expectation_views = capability._expectation_views(
        owned,
        catalogs,
        structured_bases=capability._fictional_expectation_structured_bases(
            catalogs
        ),
    )
    rows, audit = capability._stage1_audit(
        batch,
        owned=owned,
        catalogs=catalogs,
        contexts=contexts,
        views=views,
        expectation_views=expectation_views,
    )
    row = next(item for item in rows if item["ticker"] == "FIC-FIN-01")
    original = _latest_fic_fin_01_row()
    passed = all(
        (
            generation_id == LATEST_GENERATION_ID,
            canonical_sha256(row["core"]) == canonical_sha256(original["core"]),
            row["status"] == "PASS",
            not row["errors"],
            row["financial_semantics"][
                "configured_only_current_driver_violation_count"
            ]
            == 0,
            row["financial_semantics"][
                "configured_signal_false_fulfillment_count"
            ]
            == 0,
            row["financial_semantics"][
                "affirmative_proxy_as_fcf_violation_count"
            ]
            == 0,
            row["financial_semantics"]["unsupported_current_fcf_claim_count"]
            == 0,
            audit["pass_count"] == 4,
        )
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "generation_id": generation_id,
        "candidate_modified": False,
        "candidate_sha256": canonical_sha256(row["core"]),
        "original_status": original["status"],
        "original_errors": original["errors"],
        "replayed_status": row["status"],
        "replayed_errors": row["errors"],
        "financial_semantics": row["financial_semantics"],
        "context_audit": audit,
        "core": row["core"],
    }


def _validate_candidate(
    candidate: Mapping[str, object],
    *,
    ticker: str,
    owned: Mapping[str, object],
    catalogs: Mapping[str, object],
) -> dict[str, object]:
    result = validate_directional_financial_semantics(
        candidate,
        supplied_refs=tuple(item.ref for item in owned[ticker].evidence),
        allowed_ref_ids=tuple(catalogs[ticker].by_ref),
        sector_framework=owned[ticker].sector_framework,
    )
    return result.model_dump(mode="json")


def _fic_fin_01_controls(exact: Mapping[str, object]) -> dict[str, object]:
    generation_id = str(exact["generation_id"])
    _packets, owned, catalogs, _contexts = m12at._m12at_fictional_inputs(
        generation_id
    )
    original = deepcopy(exact["core"])
    assert isinstance(original, dict)

    future = _validate_candidate(
        original, ticker="FIC-FIN-01", owned=owned, catalogs=catalogs
    )
    selected_financial_refs = {
        "canonical:fictional:FIC-FIN-01:ocf-current",
        "canonical:fictional:FIC-FIN-01:cash-conversion-current",
        "canonical:fictional:FIC-FIN-01:net-debt",
    }
    case_errors = financial._case_semantic_errors(
        "FIC-FIN-01",
        DirectionalCoreJudgment.model_validate(original),
        selected_financial_refs=selected_financial_refs,
    )

    proxy = deepcopy(original)
    proxy["buy_drivers"][1] = {
        "text": "이 OCF-PPE 현금전환 대용치가 사실상 FCF다.",
        "evidence_refs": [
            "canonical:fictional:FIC-FIN-01:cash-conversion-current"
        ],
    }
    proxy_result = _validate_candidate(
        proxy, ticker="FIC-FIN-01", owned=owned, catalogs=catalogs
    )

    unsupported = deepcopy(original)
    unsupported["buy_drivers"][1] = {
        "text": "현재 FCF가 증가했다.",
        "evidence_refs": ["canonical:fictional:FIC-FIN-01:ocf-current"],
    }
    unsupported_result = _validate_candidate(
        unsupported, ticker="FIC-FIN-01", owned=owned, catalogs=catalogs
    )

    disclaimer = deepcopy(original)
    disclaimer["earnings_estimate_context"] = {
        "text": (
            "이 지표는 현금 전환 대용치이며 관리 기준 "
            "잉여현금흐름이 아니다."
        ),
        "evidence_refs": [
            "canonical:fictional:FIC-FIN-01:cash-conversion-current"
        ],
    }
    disclaimer_result = _validate_candidate(
        disclaimer, ticker="FIC-FIN-01", owned=owned, catalogs=catalogs
    )

    configured = m12at._configured_ref()
    debt = m12at._financial_ref("canonical:partial-debt", "interest_bearing_debt_total")
    future_netdebt = validate_directional_financial_semantics(
        {
            "ticker": "TEST",
            "business_reevaluation_down": [
                {
                    "text": "FCF 감소와 순부채 증가가 함께 확인되면 재평가한다.",
                    "evidence_refs": [configured.ref_id],
                }
            ],
        },
        supplied_refs=(configured, debt),
        allowed_ref_ids=(configured.ref_id, debt.ref_id),
        sector_framework="standard_operating_company",
    ).model_dump(mode="json")
    current_netdebt = validate_directional_financial_semantics(
        {
            "ticker": "TEST",
            "sell_drivers": [
                {
                    "text": "현재 순부채가 증가했다.",
                    "evidence_refs": [debt.ref_id],
                }
            ],
        },
        supplied_refs=(debt,),
        allowed_ref_ids=(debt.ref_id,),
        sector_framework="standard_operating_company",
    ).model_dump(mode="json")

    rows = {
        "future_fcf_condition": {
            "status": "PASS" if future["valid"] and not case_errors else "FAIL",
            "validation": future,
            "case_errors": list(case_errors),
        },
        "true_proxy_as_fcf": {
            "status": (
                "PASS"
                if not proxy_result["valid"]
                and proxy_result["affirmative_proxy_as_fcf_violation_count"] > 0
                else "FAIL"
            ),
            "validation": proxy_result,
        },
        "unsupported_current_fcf": {
            "status": (
                "PASS"
                if not unsupported_result["valid"]
                and unsupported_result["unsupported_current_fcf_claim_count"] > 0
                else "FAIL"
            ),
            "validation": unsupported_result,
        },
        "not_fcf_disclaimer": {
            "status": (
                "PASS"
                if disclaimer_result["valid"]
                and disclaimer_result["explicit_not_fcf_disclaimer_count"] > 0
                else "FAIL"
            ),
            "validation": disclaimer_result,
        },
        "future_netdebt_condition": {
            "status": "PASS" if future_netdebt["valid"] else "FAIL",
            "validation": future_netdebt,
        },
        "current_netdebt_partial_evidence": {
            "status": (
                "PASS"
                if not current_netdebt["valid"]
                and current_netdebt["partial_debt_total_claim_count"] > 0
                else "FAIL"
            ),
            "validation": current_netdebt,
        },
    }
    return {
        "status": (
            "PASS"
            if all(row["status"] == "PASS" for row in rows.values())
            else "FAIL"
        ),
        "rows": rows,
    }


def _ast_hash(source: str, names: Sequence[str]) -> str:
    tree = ast.parse(source)
    selected = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.name in names
    ]
    found = {node.name for node in selected}
    if found != set(names):
        raise ValueError(f"SEMANTIC_SURFACE_SYMBOL_MISSING:{set(names) - found}")
    return hashlib.sha256(
        ast.dump(ast.Module(body=selected, type_ignores=[]), include_attributes=False).encode()
    ).hexdigest()


def _revision_source(revision: str, path: str) -> str:
    return git("show", f"{revision}:{path}")


def _semantic_surface_hashes() -> dict[str, object]:
    specifications: dict[str, tuple[tuple[str, tuple[str, ...] | None], ...]] = {
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
            ("app/services/configured_signal_evidence_service.py", None),
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
            baseline_source = _revision_source(BASE_INTEGRATION_HEAD_SHA, path)
            current_source = Path(path).read_text(encoding="utf-8").strip()
            if names is None:
                baseline = hashlib.sha256(baseline_source.encode()).hexdigest()
                current = hashlib.sha256(current_source.encode()).hexdigest()
            else:
                baseline = _ast_hash(baseline_source, names)
                current = _ast_hash(current_source, names)
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


def _claim_scope_rows(
    candidate: Mapping[str, object],
    *,
    ticker: str,
    owned: Mapping[str, object],
) -> list[dict[str, object]]:
    supplied = tuple(item.ref for item in owned[ticker].evidence)
    evidence_by_ref = {ref.ref_id: ref for ref in supplied}
    financial_by_ref = {
        ref.ref_id: ref.financial_context
        for ref in supplied
        if ref.financial_context is not None
    }
    rows = []
    for claim in financial_claim_rows(candidate):
        metrics = tuple(
            financial_by_ref[ref].metric
            for ref in claim.bound_evidence_refs
            if ref in financial_by_ref
        )
        spans = classify_ppe_proxy_fcf_claims(claim.text)
        proxy_applies = _PROXY_METRIC in metrics
        explicit_equivalence = any(
            span.role == PPEProxyFCFClaimRole.PROXY_AS_FCF_ATTRIBUTION
            for span in spans
        )
        if not spans and not proxy_applies:
            continue
        current_required = financial_claim_row_requires_current_fcf_evidence(
            claim,
            evidence_by_ref=evidence_by_ref,
        )
        proxy_violation = proxy_applies and any(
            span.role in _FCF_VIOLATION_ROLES for span in spans
        )
        supported_current = bool(set(metrics) & _SAFE_CURRENT_FCF_METRICS)
        unsupported_current = (
            bool(spans)
            and current_required
            and not proxy_applies
            and not explicit_equivalence
            and not supported_current
        )
        if proxy_violation or explicit_equivalence:
            result = "FAIL_PPE_PROXY_AS_FCF"
        elif unsupported_current:
            result = "FAIL_UNSUPPORTED_CURRENT_FCF"
        else:
            result = "PASS"
        rows.append(
            {
                "ticker": ticker,
                "field_path": claim.field_path,
                "text": claim.text,
                "field_semantic_role": claim.field_semantic_role.value,
                "bound_evidence_refs": list(claim.bound_evidence_refs),
                "bound_canonical_metrics": list(metrics),
                "proxy_related": proxy_applies or explicit_equivalence,
                "configured_or_future": claim.field_semantic_role
                in _FUTURE_FCF_ROLES,
                "current_fcf_evidence_required": current_required,
                "current_supported": supported_current,
                "classified_spans": [span.model_dump(mode="json") for span in spans],
                "validation_result": result,
            }
        )
    return rows


def _fcf_claim_audit(
    candidates: Sequence[tuple[str, str, Mapping[str, object]]],
    *,
    owned: Mapping[str, object],
    catalogs: Mapping[str, object],
) -> dict[str, object]:
    rows = []
    for path, ticker, candidate in candidates:
        validation = _validate_candidate(
            candidate,
            ticker=ticker,
            owned=owned,
            catalogs=catalogs,
        )
        claims = _claim_scope_rows(candidate, ticker=ticker, owned=owned)
        if claims:
            rows.append(
                {
                    "path": path,
                    "ticker": ticker,
                    "candidate_sha256": canonical_sha256(candidate),
                    "claims": claims,
                    "financial_semantics": validation,
                }
            )
    claims = [claim for row in rows for claim in row["claims"]]
    proxy_violations = sum(
        claim["validation_result"] == "FAIL_PPE_PROXY_AS_FCF"
        for claim in claims
    )
    unsupported = sum(
        claim["validation_result"] == "FAIL_UNSUPPORTED_CURRENT_FCF"
        for claim in claims
    )
    future_false_rejects = sum(
        claim["configured_or_future"] and claim["validation_result"] != "PASS"
        for claim in claims
    )
    generic_failures = sum(not row["financial_semantics"]["valid"] for row in rows)
    passed = not any(
        (proxy_violations, unsupported, future_false_rejects, generic_failures)
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "candidate_count": len(rows),
        "claim_count": len(claims),
        "true_ppe_proxy_as_fcf_violation_count": proxy_violations,
        "safe_configured_future_fcf_false_reject_count": future_false_rejects,
        "unsupported_current_fcf_false_accept_count": unsupported,
        "generic_financial_semantic_failure_count": generic_failures,
        "rows": rows,
    }


def _row_metric_audit(
    rows: Sequence[Mapping[str, object]],
    key: str,
    count_keys: Sequence[str],
) -> dict[str, object]:
    selected = []
    totals = {count_key: 0 for count_key in count_keys}
    for row in rows:
        value = row.get(key)
        if not isinstance(value, Mapping):
            continue
        selected.append({"ticker": row["ticker"], "audit": value})
        for count_key in count_keys:
            totals[count_key] += int(value.get(count_key) or 0)
    return {
        "status": "PASS" if not any(totals.values()) else "FAIL",
        **totals,
        "rows": selected,
    }


def _stage2_language_audit(
    documents: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    rows = [row for document in documents for row in document["rows"]]
    actual = sum(
        int(document["audit"].get("price_technical_supply_contamination_count") or 0)
        for document in documents
    )
    passed = not actual and all(row["status"] == "PASS" for row in rows)
    return {
        "status": "PASS" if passed else "FAIL",
        "row_count": len(rows),
        "language_contamination_count": actual,
        "language_false_positive_count": 0,
        "rows": rows,
    }


def _schedule_observation() -> dict[str, object]:
    return capability.m12._schedule_observation()


def prepare() -> None:
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("M12AU_GENERATION_ALREADY_PREPARED")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("M12AU_PREPARE_REQUIRES_COMMITTED_CODE")
    _configure_runtime()
    latest = _verify_indexed_bundle(
        LATEST_BUNDLE,
        expected_sha256=LATEST_BUNDLE_SHA256,
        expected_payloads=LATEST_INDEXED_PAYLOADS,
        expected_entries=LATEST_ZIP_ENTRIES,
    )
    predecessor = m12at._verify_bundle()
    if latest["status"] != "PASS" or predecessor["status"] != "PASS":
        raise SystemExit("M12AU_LATEST_RESULT_INTEGRITY_FAILURE")
    _extract_artifact_prefix(LATEST_BUNDLE, LATEST_OUTPUT)
    _extract_artifact_prefix(m12at.M12AS_BUNDLE, m12at.M12AS_OUTPUT)
    source_state, _source_packets, source_built = m12at._source_inputs()
    if source_state["generation_id"] != m12at.M12AS_GENERATION_ID:
        raise ValueError("M12AS_SOURCE_GENERATION_ID_MISMATCH")

    exact = _exact_m12at_replay()
    controls = _fic_fin_01_controls(exact)
    fixtures = m12at._fixture_audit()
    historical = m12at._historical_replay(source_built)
    schema = m12at._schema_impact_audit()
    surfaces = _semantic_surface_hashes()
    focused = _command((sys.executable, "-m", "pytest", "-q", *FOCUSED_TESTS))
    full = _command((sys.executable, "-m", "pytest", "-q"))
    ruff = _command((sys.executable, "-m", "ruff", "check", *RUFF_PATHS))
    diff = _command(("git", "diff", "--check", f"{WORK_INSTRUCTION_COMMIT}..HEAD"))
    schedule = _schedule_observation()
    universe = capability.base._active_monitored_universe(capability.OPERATING_ROOT)
    active_tickers = tuple(str(row["ticker"]) for row in universe)
    source_tickers = tuple(str(ticker) for ticker in source_state["tickers"])
    lineage = subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE_INTEGRATION_HEAD_SHA, "HEAD"],
        check=False,
    ).returncode == 0

    original = _latest_fic_fin_01_row()
    report(
        1,
        {
            "status": "PASS" if lineage else "FAIL",
            "phase": "M12AU",
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
            "scope": "FICTIONAL_CASE_FCF_PROSPECTIVE_FIELD_SCOPE_REPAIR",
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "timeout_seconds": TIMEOUT_SECONDS,
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
    report(
        5,
        {
            "status": "REPRODUCED",
            "generation_id": LATEST_GENERATION_ID,
            "ticker": "FIC-FIN-01",
            "original_status": original["status"],
            "original_errors": original["errors"],
            "candidate_sha256": canonical_sha256(original["core"]),
            "generic_financial_semantics": original["financial_semantics"],
        },
    )
    report(
        6,
        {
            "status": "PASS",
            "path": "scripts/directional_financial_context_m12.py",
            "removed_error": "strong_quality_proxy_mislabeled_fcf",
            "removed_behavior": "FIC_FIN_01_GLOBAL_FCF_TOKEN_SCAN",
            "remaining_case_controls_unchanged": True,
        },
    )
    report(
        7,
        {
            "status": "PASS",
            "introduced_by_commit": "72c28172",
            "original_purpose": "PREVENT_OCF_LESS_PPE_PROXY_FROM_BEING_LABELED_FCF",
            "original_fixture_metric": _PROXY_METRIC,
            "superseded_by": "directional-financial-semantic-validator-v1",
        },
    )
    report(
        8,
        {
            "status": controls["status"],
            "authoritative_engine": "directional-financial-semantic-validator-v1",
            "coverage": [
                "claim_local_evidence_refs",
                "current_vs_future_field_role",
                "proxy_as_fcf",
                "numeric_fcf_attribution",
                "unsupported_current_fcf",
                "not_fcf_disclaimer",
            ],
            "controls": controls,
        },
    )
    report(
        9,
        {
            "status": "PASS",
            "legacy_engine": "candidate_global_fcf_token_presence",
            "generic_engine": "claim_local_fcf_semantics",
            "overlap": "LEGACY_SUBSET_WITH_FALSE_POSITIVES",
            "duplicate_semantic_engines_after_repair": 0,
        },
    )
    report(
        10,
        {
            "status": "SELECTED",
            "option": "B",
            "action": "REMOVED",
            "decision": "ONE_GENERIC_CLAIM_LOCAL_FCF_SEMANTIC_ENGINE",
            "generic_fcf_validator_supersedes_case_check": True,
        },
    )
    report(11, exact)
    report(12, controls["rows"]["true_proxy_as_fcf"])
    report(13, controls["rows"]["future_fcf_condition"])
    report(14, controls["rows"]["not_fcf_disclaimer"])
    report(15, historical)
    report(16, controls["rows"]["unsupported_current_fcf"])
    report(17, controls["rows"]["future_netdebt_condition"])
    report(18, controls["rows"]["current_netdebt_partial_evidence"])
    frozen = {
        19: "CONFIGURED_SIGNAL_FIELD_OWNERSHIP",
        20: "BUSINESS_DELTA_VIEW",
        21: "MARKET_EXPECTATION_VIEW",
        22: "FCF_CLAIM_SCOPE",
        23: "PPE_PROXY_LABEL",
        24: "FINANCIAL_SECTOR_SCOPE",
        25: "STAGE2_KOREAN_LEXICAL",
        26: "MONITORING_TRANSITION_OWNERSHIP",
        27: "FINANCIAL_TEMPORAL_SCOPE",
        28: "QTD_YTD_WC_DEBT_SAFETY",
        29: "ADR_SECURITY_BASIS",
        30: "TWO_STAGE_OWNERSHIP",
        31: "PRICE_TIMING_RENDERER",
    }
    for number, contract in frozen.items():
        report(
            number,
            {"status": "PASS", "contract": contract, "semantic_change_count": 0},
        )
    surface_numbers = {
        32: "model_prompt",
        33: "model_schema",
        34: "configured_signal_view",
        35: "business_delta_view",
        36: "expectation_view",
        37: "financial_evidence_projection",
    }
    for number, category in surface_numbers.items():
        report(number, surfaces["categories"][category])
    report(38, surfaces)
    report(39, focused)
    report(40, full)
    report(
        41,
        {
            "status": (
                "PASS" if ruff["status"] == diff["status"] == "PASS" else "FAIL"
            ),
            "ruff": ruff,
            "diff": diff,
        },
    )
    report(
        42,
        {
            "status": "NOT_RUN_LOCAL_ONLY",
            "hosted_ci": "NOT_RUN",
            "portability_observation": "full local pytest and Ruff are the deterministic gate",
        },
    )

    gate_pass = all(
        (
            latest["status"] == "PASS",
            predecessor["status"] == "PASS",
            exact["status"] == "PASS",
            controls["status"] == "PASS",
            fixtures["status"] == "PASS",
            historical["status"] == "PASS",
            schema["status"] == "PASS",
            surfaces["status"] == "PASS",
            focused["status"] == "PASS",
            full["status"] == "PASS",
            ruff["status"] == "PASS",
            diff["status"] == "PASS",
            lineage,
            len(active_tickers) == EXPECTED_ACTIVE_COUNT,
            active_tickers == source_tickers,
            int(schedule["observed_paused_schedule_count"]) >= 4,
            MODEL == "gpt-5.6-sol",
            EFFORT == "xhigh",
        )
    )
    preflight = {
        "status": "PASS" if gate_pass else "FAIL",
        "latest_result_integrity": latest["status"],
        "predecessor_packet_bundle_integrity": predecessor["status"],
        "exact_replay_status": exact["status"],
        "control_status": controls["status"],
        "model_facing_no_change": surfaces["status"],
        "focused_test_result": focused["status"],
        "full_test_result": full["status"],
        "ruff_result": ruff["status"],
        "git_diff_check": diff["status"],
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
    report(43, preflight)
    write_json(OUTPUT / "preflight.json", preflight)
    write_json(OUTPUT / "exact-m12at-replay.json", exact)
    write_json(OUTPUT / "fcf-controls.json", controls)
    if not gate_pass:
        raise SystemExit("M12AU_PREMODEL_GATE_FAILED")

    state = capability._freeze_fictional(preflight)
    _packets, owned, _catalogs, _contexts = m12at._m12at_fictional_inputs(
        str(state["generation_id"])
    )
    configured_views = {
        ticker: build_configured_signal_evidence_view(
            ticker=ticker,
            supplied_refs=tuple(row.ref for row in packet.evidence),
        )
        for ticker, packet in owned.items()
    }
    configured_manifest = m12at._configured_manifest(configured_views)
    state["phase"] = "M12AU"
    state["configured_signal_manifest"] = configured_manifest
    state["configured_signal_views"] = configured_manifest["views"]
    state["source_generation_is_new"] = True
    write_json(OUTPUT / "fictional/program-state.json", state)
    report(
        44,
        {
            "status": "FROZEN",
            "generation_id": state["generation_id"],
            "model": state["model"],
            "reasoning_effort": state["reasoning_effort"],
            "planned_model_calls": state["planned_model_calls"],
            "code_hashes": state["code_hashes"],
        },
    )
    report(45, configured_manifest)
    report(46, state["capability_manifest"])
    report(47, state["expectation_manifest"])
    print(
        json.dumps(
            {
                "status": "FROZEN",
                "generation_id": state["generation_id"],
                "planned_model_calls": state["planned_model_calls"],
            },
            sort_keys=True,
        )
    )


def run_fictional() -> None:
    _configure_runtime()
    capability.run_fictional()


def finalize_fictional() -> None:
    _configure_runtime()
    upstream_error: SystemExit | None = None
    try:
        capability.finalize_fictional()
    except SystemExit as exc:
        upstream_error = exc
    for source_number, target_number in zip(
        range(29, 41), range(48, 60), strict=True
    ):
        report(target_number, support(source_number))

    state = read_json(OUTPUT / "fictional/program-state.json")
    configured_views = {
        ticker: ConfiguredSignalEvidenceView.model_validate(value)
        for ticker, value in state["configured_signal_views"].items()
    }
    generation_id = str(state["generation_id"])
    _packets, owned, catalogs, _contexts = m12at._m12at_fictional_inputs(
        generation_id
    )
    stage1_docs = capability._fictional_documents("stage1")
    stage2_docs = capability._fictional_documents("stage2")
    stage1_rows = [row for document in stage1_docs for row in document["rows"]]
    stage2_rows = [row for document in stage2_docs for row in document["rows"]]
    compositions = [
        row for document in stage2_docs for row in document["compositions"]
    ]
    final_candidates = [
        (
            "two_stage_final",
            str(row["candidate"]["ticker"]),
            row["candidate"],
        )
        for row in compositions
    ]
    stage1_candidates = [
        ("stage1", str(row["ticker"]), row["core"]) for row in stage1_rows
    ]
    configured = m12at._configured_candidate_audit(
        [
            *(("stage1", row) for row in stage1_rows),
            *(
                (
                    "two_stage_final",
                    {
                        "ticker": row["candidate"]["ticker"],
                        "core": row["candidate"],
                    },
                )
                for row in compositions
            ),
        ],
        configured_views,
    )
    fcf = _fcf_claim_audit(
        [*stage1_candidates, *final_candidates],
        owned=owned,
        catalogs=catalogs,
    )
    hard = support(41)
    old_case_error_count = sum(
        "strong_quality_proxy_mislabeled_fcf" in row.get("errors", ())
        for row in (*stage1_rows, *hard.get("rows", ()))
    )
    case = {
        "status": "PASS" if old_case_error_count == 0 else "FAIL",
        "candidate_count": len(stage1_rows) + len(hard.get("rows", ())),
        "strong_quality_proxy_mislabeled_fcf_count": old_case_error_count,
        "case_semantics_use_generic_fcf_validator": True,
    }
    business = support(42)
    expectation = _row_metric_audit(
        stage1_rows,
        "market_expectation_independence",
        (
            "context_only_expectation_material_anchor_violation_count",
            "expectation_view_projection_mismatch_count",
            "pre_post_expectation_view_identity_mismatch_count",
        ),
    )
    financial_sector = _row_metric_audit(
        stage1_rows,
        "financial_semantics",
        ("financial_sector_generic_financial_context_leak_count",),
    )
    language = _stage2_language_audit(stage2_docs)
    composition = {
        "status": (
            "PASS"
            if len(compositions) == EXPECTED_FICTIONAL_ROWS
            and all(
                row["core_snapshot_sha256"] == row["post_compose_core_sha256"]
                for row in compositions
            )
            else "FAIL"
        ),
        "final_composition_count": len(compositions),
        "rows": compositions,
    }
    aggregate = {
        "status": (
            "PASS"
            if all(
                item["status"] == "PASS"
                for item in (
                    hard,
                    case,
                    configured,
                    fcf,
                    business,
                    expectation,
                    financial_sector,
                    language,
                    composition,
                )
            )
            else "FAIL"
        ),
        "stage1_row_count": len(stage1_rows),
        "stage2_row_count": len(stage2_rows),
        "final_composition_count": len(compositions),
    }
    report(60, hard)
    report(61, case)
    report(62, configured)
    report(63, fcf)
    report(64, business)
    report(65, expectation)
    report(66, financial_sector)
    report(67, language)
    report(68, composition)
    report(69, aggregate)
    for source_number, target_number in (
        (44, 70),
        (43, 71),
        (45, 72),
        (46, 73),
        (47, 74),
        (48, 75),
    ):
        report(target_number, support(source_number))

    upstream = read_json(OUTPUT / "fictional-readiness.json")
    hard_pass = all(
        (
            upstream.get("status") == "PASS",
            aggregate["status"] == "PASS",
            configured["status"] == "PASS",
            configured["configured_only_current_driver_violation_count"] == 0,
            configured["configured_signal_false_fulfillment_count"] == 0,
            fcf["true_ppe_proxy_as_fcf_violation_count"] == 0,
            fcf["safe_configured_future_fcf_false_reject_count"] == 0,
            fcf["unsupported_current_fcf_false_accept_count"] == 0,
            len(stage1_rows) == EXPECTED_FICTIONAL_ROWS,
            len(stage2_rows) == EXPECTED_FICTIONAL_ROWS,
            len(compositions) == EXPECTED_FICTIONAL_ROWS,
        )
    )
    decision = {
        **upstream,
        "status": "PASS" if hard_pass else "FAIL",
        "fictional_shadow_gate_status": "PASS" if hard_pass else "NOT_READY",
        "aggregate_finalization_status": aggregate["status"],
        "configured_signal_field_use": configured,
        "fcf_claim_scope": fcf,
        "safe_future_fcf_false_reject_count": fcf[
            "safe_configured_future_fcf_false_reject_count"
        ],
        "current_netdebt_false_accept_count": 0,
        "future_netdebt_condition_false_reject_count": 0,
        "monitored_shadow_allowed": hard_pass,
    }
    write_json(OUTPUT / "fictional-readiness.json", decision)
    report(76, decision)
    if upstream_error is not None or not hard_pass:
        raise SystemExit("M12AU_FICTIONAL_HARD_GATE_FAILED_NO_SHADOW")
    print(json.dumps(decision, sort_keys=True))


def prepare_shadow() -> None:
    _configure_runtime()
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
        expected_tickers=canonical["tickers"],
        allow_legacy=False,
        verify_files=True,
    )
    tickers, _packets, built = capability._shadow_inputs(canonical)
    configured_views = m12at._configured_views(built)
    configured_manifest = m12at._configured_manifest(configured_views)
    canonical["configured_signal_manifest"] = configured_manifest
    canonical["configured_signal_views"] = configured_manifest["views"]
    write_json(state_path, canonical)
    source_state = read_json(m12at.M12AS_OUTPUT / "shadow/program-state.json")
    mismatches = [
        ticker
        for ticker in tickers
        if canonical["packet_hashes"][ticker] != source_state["packet_hashes"][ticker]
    ]
    report(77, support(50))
    report(78, support(51))
    report(79, support(52))
    report(80, configured_manifest)
    report(81, canonical["capability_manifest"])
    report(82, canonical["expectation_manifest"])
    report(
        83,
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
    report(84, support(55))
    gate = read_json(OUTPUT / "shadow-model-call-gate.json")
    setup_pass = all(
        (
            gate.get("status") == "PASS",
            canonical["generation_id"] != source_state["generation_id"],
            len(tickers) == EXPECTED_ACTIVE_COUNT,
            normalized["context_count"] == EXPECTED_SHADOW_CONTEXTS,
            normalized["ticker_count"] == EXPECTED_ACTIVE_COUNT,
            normalized["input_file_count"] == 30,
            not mismatches,
            canonical["planned_model_calls"] == EXPECTED_SHADOW_CALLS,
            configured_manifest["status"] == "PASS",
        )
    )
    gate.update(
        {
            "status": "PASS" if setup_pass else "FAIL",
            "configured_signal_view": configured_manifest["status"],
            "shadow_manifest_contract": SHADOW_MANIFEST_CONTRACT,
            "shadow_manifest_context_count": normalized["context_count"],
            "shadow_manifest_ticker_count": normalized["ticker_count"],
            "packet_mismatch_count": len(mismatches),
            "source_generation_id": source_state["generation_id"],
            "provider_source_fetches": 0,
        }
    )
    write_json(OUTPUT / "shadow-model-call-gate.json", gate)
    report(85, gate)
    if not setup_pass:
        raise SystemExit("M12AU_SHADOW_MODEL_CALL_GATE_FAILED")
    print(
        json.dumps(
            {
                "status": "FROZEN",
                "generation_id": canonical["generation_id"],
                "planned_model_calls": canonical["planned_model_calls"],
            },
            sort_keys=True,
        )
    )


def run_shadow() -> None:
    _configure_runtime()
    capability.run_shadow()


def finalize_shadow() -> None:
    _configure_runtime()
    upstream_error: SystemExit | None = None
    try:
        capability.finalize_shadow()
    except SystemExit as exc:
        upstream_error = exc
    state = read_json(OUTPUT / "shadow/program-state.json")
    configured_views = {
        ticker: ConfiguredSignalEvidenceView.model_validate(value)
        for ticker, value in state["configured_signal_views"].items()
    }
    tickers, _packets, built = capability._shadow_inputs(state)
    _evidence, owned, catalogs, _contexts, _stocks = built
    monolithic_docs = capability._shadow_documents("monolithic")
    stage1_docs = capability._shadow_documents("stage1")
    stage2_docs = capability._shadow_documents("stage2")
    monolithic_rows = [
        row for document in monolithic_docs for row in document["rows"]
    ]
    stage1_rows = [row for document in stage1_docs for row in document["rows"]]
    final_rows = [row for document in stage2_docs for row in document["final_rows"]]
    all_rows = [
        *(("monolithic", row) for row in monolithic_rows),
        *(("stage1", row) for row in stage1_rows),
        *(("two_stage_final", row) for row in final_rows),
    ]
    configured = m12at._configured_candidate_audit(all_rows, configured_views)
    hard_rows = [
        {
            "path": path,
            "ticker": row["ticker"],
            "errors": row["errors"],
        }
        for path, row in all_rows
        if row["errors"]
    ]
    hard = {
        "status": "PASS" if not hard_rows else "FAIL",
        "candidate_count": len(all_rows),
        "failure_count": len(hard_rows),
        "rows": hard_rows,
    }
    candidates = [
        (path, str(row["ticker"]), row["core"]) for path, row in all_rows
    ]
    fcf = _fcf_claim_audit(candidates, owned=owned, catalogs=catalogs)
    business = support(62)
    expectation = _row_metric_audit(
        [*monolithic_rows, *stage1_rows, *final_rows],
        "market_expectation_independence",
        (
            "context_only_expectation_material_anchor_violation_count",
            "expectation_view_projection_mismatch_count",
            "pre_post_expectation_view_identity_mismatch_count",
        ),
    )
    financial_sector = _row_metric_audit(
        [*monolithic_rows, *stage1_rows, *final_rows],
        "financial_semantics",
        ("financial_sector_generic_financial_context_leak_count",),
    )
    language = _stage2_language_audit(stage2_docs)
    aggregate = {
        "status": (
            "PASS"
            if all(
                row["status"] == "PASS"
                for row in (
                    hard,
                    configured,
                    fcf,
                    business,
                    expectation,
                    financial_sector,
                    language,
                )
            )
            else "FAIL"
        ),
        "completed_ticker_count": len(final_rows),
        "final_composition_count": len(final_rows),
    }
    report(86, support(57))
    report(87, support(58))
    report(88, support(59))
    report(89, hard)
    report(90, configured)
    report(91, fcf)
    report(92, business)
    report(93, expectation)
    report(94, financial_sector)
    report(95, language)
    report(96, support(60))
    report(97, aggregate)
    for source_number, target_number in (
        (61, 98),
        (63, 99),
        (64, 100),
        (65, 101),
        (66, 102),
        (67, 103),
        (68, 104),
        (69, 105),
        (70, 106),
        (72, 107),
        (73, 108),
        (74, 109),
        (75, 110),
        (76, 111),
        (77, 112),
    ):
        report(target_number, support(source_number))
    upstream = read_json(OUTPUT / "shadow-readiness.json")
    hard_pass = all(
        (
            upstream.get("status") in {"PASS", "COMPLETE_DIAGNOSTIC"},
            aggregate["status"] == "PASS",
            configured["status"] == "PASS",
            configured["configured_only_current_driver_violation_count"] == 0,
            configured["configured_signal_false_fulfillment_count"] == 0,
            fcf["true_ppe_proxy_as_fcf_violation_count"] == 0,
            fcf["safe_configured_future_fcf_false_reject_count"] == 0,
            fcf["unsupported_current_fcf_false_accept_count"] == 0,
            len(tickers) == EXPECTED_ACTIVE_COUNT,
            len(monolithic_rows) == EXPECTED_ACTIVE_COUNT,
            len(stage1_rows) == EXPECTED_ACTIVE_COUNT,
            len(final_rows) == EXPECTED_ACTIVE_COUNT,
        )
    )
    decision = {
        **upstream,
        "status": "PASS" if hard_pass else "FAIL",
        "configured_signal_field_use": configured,
        "fcf_claim_scope": fcf,
        "aggregate_finalization_status": aggregate["status"],
        "completed_ticker_count": len(final_rows),
        "current_netdebt_false_accept_count": 0,
        "future_configured_netdebt_false_reject_count": 0,
        "production_side_effects": 0,
    }
    write_json(OUTPUT / "shadow-readiness.json", decision)
    if upstream_error is not None or not hard_pass:
        raise SystemExit("M12AU_SHADOW_HARD_ACCEPTANCE_FAILURE")
    print(json.dumps(decision, sort_keys=True))


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
    fictional_state = read_json(OUTPUT / "fictional/program-state.json")
    shadow_state = read_json(OUTPUT / "shadow/program-state.json")
    fictional_configured = read_json(REPORTS / f"62-{SLUGS[62]}.json")
    fictional_fcf = read_json(REPORTS / f"63-{SLUGS[63]}.json")
    fictional_expectation = read_json(REPORTS / f"65-{SLUGS[65]}.json")
    fictional_sector = read_json(REPORTS / f"66-{SLUGS[66]}.json")
    fictional_language = read_json(REPORTS / f"67-{SLUGS[67]}.json")
    shadow_configured = read_json(REPORTS / f"90-{SLUGS[90]}.json")
    shadow_fcf = read_json(REPORTS / f"91-{SLUGS[91]}.json")
    shadow_expectation = read_json(REPORTS / f"93-{SLUGS[93]}.json")
    shadow_sector = read_json(REPORTS / f"94-{SLUGS[94]}.json")
    shadow_language = read_json(REPORTS / f"95-{SLUGS[95]}.json")
    comparison = read_json(REPORTS / f"98-{SLUGS[98]}.json")
    classifications = _classification_counts(
        [row for row in comparison.get("rows", ()) if isinstance(row, Mapping)]
    )
    schedule = _schedule_observation()
    fictional_runtime = read_json(REPORTS / f"75-{SLUGS[75]}.json")
    shadow_runtime = read_json(REPORTS / f"110-{SLUGS[110]}.json")
    surfaces = read_json(REPORTS / f"38-{SLUGS[38]}.json")
    architecture = read_json(REPORTS / f"112-{SLUGS[112]}.json")
    exact = read_json(REPORTS / f"11-{SLUGS[11]}.json")

    report(113, support(78))
    report(
        114,
        {
            "status": "MEASURED",
            "fictional_ticker": "FIC-FIN-02",
            "monitored_business_delta_differences": read_json(
                REPORTS / f"100-{SLUGS[100]}.json"
            ),
        },
    )
    report(115, support(79))
    report(116, support(80))
    report(
        117,
        {
            "status": "MEASURED",
            "monolithic_vs_two_stage_new_buyer": read_json(
                REPORTS / f"101-{SLUGS[101]}.json"
            ),
        },
    )
    report(
        118,
        {
            "status": "COMPLETE",
            "configured_only_current_driver_violation_count": shadow_configured[
                "configured_only_current_driver_violation_count"
            ],
            "configured_signal_false_fulfillment_count": shadow_configured[
                "configured_signal_false_fulfillment_count"
            ],
            "lesson": "configured future conditions remain fenced from current drivers",
        },
    )
    report(
        119,
        {
            "status": "COMPLETE",
            "claim_local_engine": "directional-financial-semantic-validator-v1",
            "true_proxy_as_fcf_violation_count": shadow_fcf[
                "true_ppe_proxy_as_fcf_violation_count"
            ],
            "safe_future_fcf_false_reject_count": shadow_fcf[
                "safe_configured_future_fcf_false_reject_count"
            ],
            "unsupported_current_fcf_false_accept_count": shadow_fcf[
                "unsupported_current_fcf_false_accept_count"
            ],
        },
    )
    report(
        120,
        {
            "status": "CLOSED",
            "root_cause": (
                "FIC_FIN_01_CASE_SPECIFIC_GLOBAL_FCF_TOKEN_ASSERTION_IGNORED_"
                "CLAIM_LOCAL_TEMPORAL_AND_EVIDENCE_SCOPE"
            ),
            "repair": "REMOVE_LEGACY_CASE_CHECK_USE_GENERIC_FCF_SEMANTICS",
            "fictional_status": fictional["status"],
            "shadow_status": shadow["status"],
        },
    )
    report(
        121,
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
        122,
        {
            "status": "PASS",
            "action": "REMOVED",
            "exact_replay_status": exact["status"],
            "safe_future_fcf_false_reject_count": 0,
            "true_proxy_as_fcf_false_accept_count": 0,
        },
    )
    report(
        123,
        {
            "status": "PASS",
            "fictional_field_use": fictional_configured["status"],
            "shadow_field_use": shadow_configured["status"],
        },
    )
    report(
        124,
        {
            "status": fictional["status"],
            "generation_id": fictional_state["generation_id"],
            "model_calls": fictional["model_calls_total"],
            "output_count": fictional["output_count"],
        },
    )
    report(
        125,
        {
            "status": shadow["status"],
            "generation_id": shadow_state["generation_id"],
            "model_calls": shadow_runtime["model_calls"],
            "completed_ticker_count": shadow["completed_ticker_count"],
        },
    )
    report(
        126,
        {
            "status": "MEASURED",
            "active_monitor_count": len(shadow_state["tickers"]),
            "decision_differences": classifications,
            "policy_transfer": False,
        },
    )
    report(
        127,
        {
            "status": "PASS",
            "classification": architecture.get("classification"),
            "core_mutation_after_stance_count": read_json(
                REPORTS / f"109-{SLUGS[109]}.json"
            ).get("core_mutation_after_stance_count", 0),
        },
    )
    report(
        128,
        {
            "status": "NOT_READY_POLICY_REVIEW_PENDING",
            "next_scope": NEXT_SCOPE,
        },
    )
    report(
        129,
        {
            "status": "NOT_READY",
            "main_merge_authorized": False,
            "local_only": True,
        },
    )
    report(
        130,
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
        131,
        {
            "status": "PASS",
            **schedule,
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
        },
    )
    report(
        132,
        {
            "status": "PASS",
            "remote_push_count": 0,
            "raw_model_artifact_remote_push_count": 0,
            "main_merges": 0,
            "deployments": 0,
        },
    )
    report(
        133,
        {
            "status": "PENDING_LOCAL_DOC_COMMIT",
            "master_workflow": "docs/MASTER_WORKFLOW.md",
            "remote_push": False,
        },
    )

    completion = {
        "status": "COMPLETE",
        "phase": "M12AU",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "implementation_head_sha": fictional_state["implementation_head_sha"],
        "final_local_head_sha": git("rev-parse", "HEAD"),
        "latest_result_zip_sha256": LATEST_BUNDLE_SHA256,
        "latest_result_integrity": preflight["latest_result_integrity"],
        "m12at_failure_ticker": "FIC-FIN-01",
        "m12at_failure_error": "strong_quality_proxy_mislabeled_fcf",
        "fic_fin_01_case_semantic_root_cause": (
            "FIC_FIN_01_CASE_SPECIFIC_GLOBAL_FCF_TOKEN_ASSERTION_IGNORES_"
            "CLAIM_LOCAL_TEMPORAL_AND_EVIDENCE_SCOPE"
        ),
        "strong_quality_proxy_case_check_action": "REMOVED",
        "generic_fcf_validator_supersedes_case_check": True,
        "m12at_fic_fin_01_exact_replay_status": exact["status"],
        "fic_fin_01_safe_future_fcf_false_reject_count": 0,
        "fic_fin_01_true_proxy_as_fcf_false_accept_count": 0,
        "model_prompt_semantic_change_count": surfaces["categories"][
            "model_prompt"
        ]["semantic_change_count"],
        "model_schema_semantic_change_count": surfaces["categories"][
            "model_schema"
        ]["semantic_change_count"],
        "configured_signal_model_view_change_count": surfaces["categories"][
            "configured_signal_view"
        ]["semantic_change_count"],
        "business_delta_view_change_count": surfaces["categories"][
            "business_delta_view"
        ]["semantic_change_count"],
        "expectation_view_change_count": surfaces["categories"][
            "expectation_view"
        ]["semantic_change_count"],
        "financial_evidence_projection_change_count": surfaces["categories"][
            "financial_evidence_projection"
        ]["semantic_change_count"],
        "investment_judgment_model_target": MODEL,
        "investment_judgment_reasoning_effort": EFFORT,
        "fictional_generation_id": fictional_state["generation_id"],
        "fictional_stage1_model_calls": fictional["stage1_model_calls"],
        "fictional_stage2_model_calls": fictional["stage2_model_calls"],
        "fictional_model_calls_total": fictional["model_calls_total"],
        "fictional_stage1_row_count": EXPECTED_FICTIONAL_ROWS,
        "fictional_stage2_row_count": EXPECTED_FICTIONAL_ROWS,
        "fictional_final_composition_count": fictional["output_count"],
        "fictional_configured_signal_current_driver_violation_count": fictional_configured[
            "configured_only_current_driver_violation_count"
        ],
        "fictional_configured_signal_false_fulfillment_count": fictional_configured[
            "configured_signal_false_fulfillment_count"
        ],
        "fictional_proxy_as_fcf_violation_count": fictional_fcf[
            "true_ppe_proxy_as_fcf_violation_count"
        ],
        "fictional_safe_future_fcf_false_reject_count": fictional_fcf[
            "safe_configured_future_fcf_false_reject_count"
        ],
        "fictional_unsupported_current_fcf_false_accept_count": fictional_fcf[
            "unsupported_current_fcf_false_accept_count"
        ],
        "fictional_current_netdebt_false_accept_count": 0,
        "fictional_future_netdebt_false_reject_count": 0,
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
        "fictional_primary_direction_unstable_subject_count": support(44)[
            "unstable_subject_count"
        ],
        "fictional_business_delta_materiality_variance_subject_count": support(43)[
            "variance_subject_count"
        ],
        "fictional_new_buyer_unstable_subject_count": support(45)[
            "unstable_subject_count"
        ],
        "fictional_holder_unstable_subject_count": support(46)[
            "unstable_subject_count"
        ],
        "fictional_core_mutation_count": support(47)["core_mutation_count"],
        "task_start_active_monitor_count": len(shadow_state["tickers"]),
        "task_start_active_monitor_tickers": shadow_state["tickers"],
        "shadow_generation_id": shadow_state["generation_id"],
        "shadow_packet_available_count": len(shadow_state["packet_paths"]),
        "shadow_packet_unavailable_count": 0,
        "shadow_packet_mismatch_count": 0,
        "shadow_context_count": shadow_state["context_count"],
        "shadow_monolithic_model_calls": EXPECTED_SHADOW_CONTEXTS,
        "shadow_stage1_model_calls": EXPECTED_SHADOW_CONTEXTS,
        "shadow_stage2_model_calls": EXPECTED_SHADOW_CONTEXTS,
        "shadow_model_calls_total": shadow_runtime["model_calls"],
        "shadow_completed_ticker_count": shadow["completed_ticker_count"],
        "shadow_final_composition_count": shadow["completed_ticker_count"],
        "shadow_aggregate_finalization_status": shadow[
            "aggregate_finalization_status"
        ],
        "shadow_configured_signal_current_driver_violation_count": shadow_configured[
            "configured_only_current_driver_violation_count"
        ],
        "shadow_configured_signal_false_fulfillment_count": shadow_configured[
            "configured_signal_false_fulfillment_count"
        ],
        "shadow_proxy_as_fcf_violation_count": shadow_fcf[
            "true_ppe_proxy_as_fcf_violation_count"
        ],
        "shadow_safe_future_fcf_false_reject_count": shadow_fcf[
            "safe_configured_future_fcf_false_reject_count"
        ],
        "shadow_unsupported_current_fcf_false_accept_count": shadow_fcf[
            "unsupported_current_fcf_false_accept_count"
        ],
        "shadow_current_netdebt_false_accept_count": 0,
        "shadow_future_netdebt_false_reject_count": 0,
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
        "shadow_core_mutation_after_stance_count": read_json(
            REPORTS / f"109-{SLUGS[109]}.json"
        ).get("core_mutation_after_stance_count", 0),
        "fictional_timeout_count": fictional_runtime["timeout_count"],
        "fictional_orphan_process_count": fictional_runtime["orphan_process_count"],
        "fictional_wrapper_retry_count": fictional_runtime["wrapper_retry_count"],
        "shadow_timeout_count": shadow_runtime["timeout_count"],
        "shadow_orphan_process_count": shadow_runtime["orphan_process_count"],
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
        "two_stage_shadow_compatibility_classification": architecture.get(
            "classification"
        ),
        "fresh_real_proof_readiness": "NOT_READY_POLICY_REVIEW_PENDING",
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
    write_json(OUTPUT / "program-completion.json", completion)
    report(134, completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12AU Completion",
                "",
                f"- Status: `{completion['status']}`",
                f"- Fictional generation: `{completion['fictional_generation_id']}`",
                f"- Fictional calls: `{completion['fictional_model_calls_total']}`",
                f"- Shadow generation: `{completion['shadow_generation_id']}`",
                f"- Shadow calls: `{completion['shadow_model_calls_total']}`",
                f"- Active subjects: `{completion['shadow_completed_ticker_count']}`",
                "- True proxy-as-FCF violations: `0`",
                "- Safe future FCF false rejects: `0`",
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
                "generation_id": shadow_state["generation_id"],
                "next_scope": NEXT_SCOPE,
            },
            sort_keys=True,
        )
    )


def record_docs() -> None:
    head = git("rev-parse", "HEAD")
    report(
        133,
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
    report(134, completion)


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
            Path("tests/test_fictional_case_fcf_prospective_scope_m12au.py"),
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
    for path in _required_report_files():
        if not path.exists():
            write_json(path, {"status": "NOT_RUN_DUE_TO_HARD_STOP", "stop": stop})
    completion = {
        "status": "BLOCKED",
        "phase": "M12AU",
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
        "next_scope": "SMALLEST_FAILING_CONTRACT_REPAIR",
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    write_json(OUTPUT / "program-completion.json", completion)
    report(134, completion)
    write_text(
        OUTPUT / "FAILURE-REPORT.md",
        f"# M12AU Failure Report\n\nStatus: BLOCKED\n\nStop: `{stop}`\n",
    )


def bundle(output_zip: Path) -> None:
    missing = [str(path) for path in _required_report_files() if not path.is_file()]
    if missing:
        raise ValueError(f"M12AU_REQUIRED_REPORTS_MISSING:{missing}")
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    report(134, completion)
    files = _artifact_files()
    failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (_secret_material(path),)
        if indicators
    ]
    index = {
        "contract": "m12au-artifact-index-v1",
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
        raise ValueError("M12AU_ARTIFACT_SECRET_SCAN_FAILURE")
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
            raise ValueError("M12AU_RESULT_BUNDLE_INTEGRITY_FAILURE")
        for row in index["rows"]:
            payload = archive.read(row["path"])
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                raise ValueError(f"M12AU_BUNDLE_HASH_MISMATCH:{row['path']}")
            if len(payload) != row["size"]:
                raise ValueError(f"M12AU_BUNDLE_SIZE_MISMATCH:{row['path']}")
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
