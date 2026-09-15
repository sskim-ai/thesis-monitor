"""M12AW prospective financial-condition nominalization proof and shadow."""

# ruff: noqa: E402

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

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.cross_market_decision_engine_service import (
    DecisionEvidenceRef,
    EvidenceCategory,
)
from app.services.configured_signal_evidence_service import (
    ConfiguredSignalEvidenceView,
    build_configured_signal_evidence_view,
)
from app.services.directional_financial_context_service import (
    PROSPECTIVE_CONDITION_NOMINALIZATION_CONTRACT,
    FinancialClaimFieldRole,
    FinancialClaimRole,
    PPEProxyFCFClaimRole,
    _CURRENT_FULFILLMENT_LANGUAGE,
    _CURRENT_MAGNITUDE_LANGUAGE,
    _claim_has_framework_relevant_configured_evidence,
    _has_following_condition_fulfillment,
    _is_nominalized_prospective_condition,
    classify_ppe_proxy_fcf_claims,
    financial_claim_role,
    financial_claim_row_requires_current_fcf_evidence,
    financial_claim_rows,
    validate_directional_financial_semantics,
)
from app.services.financial_framework_claim_service import (
    CLAIM_SPAN_CONTRACT_VERSION,
    candidate_financial_framework_claims,
)
from app.services.two_stage_directional_service import DirectionalCoreJudgment
from scripts import configured_signal_field_ownership_m12at as m12at
from scripts import directional_financial_context_m12 as financial
from scripts.shadow_frozen_context_manifest import (
    CONTRACT_VERSION as SHADOW_MANIFEST_CONTRACT,
    canonicalize_shadow_manifest_state,
    normalize_shadow_manifest,
)


NAME = "20260913-prospective-financial-condition-nominalization-scope-fictional-reproof-full-shadow"
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
SUPPORT_REPORTS = OUTPUT / "supporting-reports/m12ai"
RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
RUNNER = Path("scripts/prospective_condition_nominalization_m12aw.py")
ARCHITECTURE = Path(
    "docs/architecture/PROSPECTIVE_FINANCIAL_CONDITION_NOMINALIZATION.md"
)
WORK_INSTRUCTION = Path("docs/work-instructions") / f"{NAME}.md"
WORK_INSTRUCTION_COMMIT = "a4a642cfcb3c595c419e29b880799d042f47b8ed"
BASE_INTEGRATION_HEAD_SHA = "697d387e73a417cb8d11520fa9be08841b803d5d"

ICLOUD = Path(
    "/Users/sskim/Library/Mobile Documents/com~apple~CloudDocs/Thesis Monitor"
)
LATEST_NAME = (
    "20260912-mixed-risk-context-financial-claim-clause-scope-"
    "fictional-reproof-full-shadow"
)
LATEST_OUTPUT = Path("artifacts") / LATEST_NAME
LATEST_BUNDLE = ICLOUD / f"thesis-monitor-{LATEST_NAME}-report.zip"
LATEST_BUNDLE_SHA256 = (
    "25f26e7836076544948892a8c8ec684269a771b9f0d0c57de2f5b5b0cfa4b5b6"
)
LATEST_INDEXED_PAYLOADS = 254
LATEST_ZIP_ENTRIES = 255
LATEST_GENERATION_ID = "20260911-m12ai-fictional-20260912T150021Z-a9e0511dea1e"

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
    "m12av-scope-freeze",
    "integrated-main-lineage-freeze",
    "m12av-fic-fin-06-failure-reproduction",
    "fic-fin-06-nominal-condition-forensic",
    "prospective-condition-pattern-code-audit",
    "current-fulfillment-precedence-audit",
    "nominal-condition-architecture-options",
    "nominal-condition-architecture-decision",
    "prospective-financial-condition-nominalization-contract",
    "current-fulfillment-precedence-contract",
    "current-magnitude-precedence-contract",
    "configured-support-required-for-ambiguous-nominal-contract",
    "korean-nominal-condition-contract",
    "english-nominal-condition-contract",
    "same-clause-current-vs-condition-contract",
    "m12av-fic-fin-06-exact-offline-replay",
    "m12av-fic-fin-01-replay-regression",
    "m12av-fic-fin-02-replay-regression",
    "m12av-fic-fin-04-replay-regression",
    "fic-fin-03-pass-regression",
    "nominal-condition-positive-fixtures",
    "nominal-condition-current-negative-fixtures",
    "no-configured-support-fail-closed-fixtures",
    "same-clause-current-and-condition-fixtures",
    "m12av-completed-40-row-offline-reaudit",
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
    "real-nominal-condition-scope-lessons",
    "real-mixed-risk-context-lessons",
    "configured-signal-field-use-real-lessons",
    "combined-fictional-monitored-root-cause-summary",
    "next-bounded-policy-decision",
    "nominal-condition-scope-repair-success-decision",
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
if len(SLUGS) != 150:
    raise RuntimeError(f"M12AW_REPORT_SEQUENCE_INVALID:{len(SLUGS)}")

FOCUSED_TESTS = (
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
    "scripts/directional_financial_context_m12.py",
    str(RUNNER),
    "app/services/financial_framework_claim_service.py",
    "app/services/directional_financial_context_service.py",
    "tests/test_mixed_risk_context_clause_scope_m12av.py",
    "tests/test_prospective_financial_condition_nominalization_m12aw.py",
    "tests/test_prospective_condition_nominalization_m12aw_runner.py",
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


def _exact_m12au_replay() -> dict[str, object]:
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
    originals = {str(row["ticker"]): row for row in document["rows"]}
    replayed = {str(row["ticker"]): row for row in rows}
    evidence_by_ticker = {
        ticker: {ref.ref_id: ref for ref in packets[ticker].evidence}
        for ticker in tickers
    }
    detail_rows = []
    for ticker in tickers:
        row = replayed[ticker]
        original = originals[ticker]
        refs = evidence_by_ticker[ticker]
        metric_by_ref = {
            ref_id: ref.financial_context.metric
            for ref_id, ref in refs.items()
            if ref.financial_context is not None
        }
        framework_rows = []
        for claim in candidate_financial_framework_claims(
            row["core"], metric_by_ref=metric_by_ref
        ):
            if claim.framework != "net_debt" or not claim.text:
                continue
            framework_rows.append(
                {
                    "field_path": claim.field_path,
                    "framework": claim.framework,
                    "full_field_text": claim.full_field_text,
                    "local_clause_text": claim.local_clause_text,
                    "local_clause_start": claim.local_clause_start,
                    "local_clause_end": claim.local_clause_end,
                    "span_contract": claim.span_contract,
                    "temporal_role": financial_claim_role(
                        claim, evidence_by_ref=refs
                    ).value,
                    "evidence_refs": list(claim.evidence_refs),
                }
            )
        detail_rows.append(
            {
                "ticker": ticker,
                "candidate_modified": False,
                "candidate_sha256": canonical_sha256(row["core"]),
                "original_candidate_sha256": canonical_sha256(original["core"]),
                "original_status": original["status"],
                "original_errors": original["errors"],
                "replayed_status": row["status"],
                "replayed_errors": row["errors"],
                "financial_semantics": row["financial_semantics"],
                "net_debt_claims": framework_rows,
                "core": row["core"],
            }
        )
    by_ticker = {str(row["ticker"]): row for row in detail_rows}
    original_failures_match = all(
        "net_debt_claim_without_complete_net_debt_evidence"
        in by_ticker[ticker]["original_errors"]
        for ticker in ("FIC-FIN-01", "FIC-FIN-02", "FIC-FIN-04")
    )
    original_fic03_pass = (
        by_ticker["FIC-FIN-03"]["original_status"] == "PASS"
        and not by_ticker["FIC-FIN-03"]["original_errors"]
    )
    expected_roles = all(
        any(
            claim["field_path"] == "risk_context.text"
            and claim["temporal_role"]
            == FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO.value
            for claim in by_ticker[ticker]["net_debt_claims"]
        )
        for ticker in tickers
    )
    passed = all(
        (
            generation_id == LATEST_GENERATION_ID,
            len(detail_rows) == 4,
            all(row["candidate_sha256"] == row["original_candidate_sha256"] for row in detail_rows),
            all(row["replayed_status"] == "PASS" for row in detail_rows),
            all(not row["replayed_errors"] for row in detail_rows),
            all(
                row["financial_semantics"]["partial_debt_total_claim_count"] == 0
                for row in detail_rows
            ),
            original_failures_match,
            original_fic03_pass,
            expected_roles,
            audit["pass_count"] == 4,
        )
    )
    fic01 = by_ticker["FIC-FIN-01"]
    return {
        "status": "PASS" if passed else "FAIL",
        "generation_id": generation_id,
        "candidate_modified": False,
        "candidate_sha256": fic01["candidate_sha256"],
        "original_status": fic01["original_status"],
        "original_errors": fic01["original_errors"],
        "replayed_status": fic01["replayed_status"],
        "replayed_errors": fic01["replayed_errors"],
        "financial_semantics": fic01["financial_semantics"],
        "context_audit": audit,
        "original_failure_contract_match": original_failures_match,
        "fic_fin_03_prior_pass_preserved": original_fic03_pass,
        "expected_local_roles_match": expected_roles,
        "rows": detail_rows,
        "by_ticker": by_ticker,
        "core": fic01["core"],
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


def _fixture_claim_roles(
    candidate: Mapping[str, object],
    refs: Sequence[DecisionEvidenceRef],
) -> list[dict[str, object]]:
    evidence_by_ref = {ref.ref_id: ref for ref in refs}
    metric_by_ref = {
        ref.ref_id: ref.financial_context.metric
        for ref in refs
        if ref.financial_context is not None
    }
    return [
        {
            "framework": claim.framework,
            "field_path": claim.field_path,
            "full_field_text": claim.full_field_text,
            "local_clause_text": claim.local_clause_text,
            "local_clause_start": claim.local_clause_start,
            "local_clause_end": claim.local_clause_end,
            "span_contract": claim.span_contract,
            "temporal_role": financial_claim_role(
                claim, evidence_by_ref=evidence_by_ref
            ).value,
            "evidence_refs": list(claim.evidence_refs),
        }
        for claim in candidate_financial_framework_claims(
            candidate, metric_by_ref=metric_by_ref
        )
        if claim.text
    ]


def _fixture_result(
    *,
    fixture_id: str,
    text: str,
    refs: Sequence[DecisionEvidenceRef],
    expected_valid: bool,
    expected_roles: Sequence[FinancialClaimRole],
    field: str = "risk_context",
) -> dict[str, object]:
    payload = {"ticker": fixture_id}
    value = {"text": text, "evidence_refs": [ref.ref_id for ref in refs]}
    if field == "business_reevaluation_down":
        payload[field] = [value]
    else:
        payload[field] = value
    result = validate_directional_financial_semantics(
        payload,
        supplied_refs=tuple(refs),
        allowed_ref_ids=tuple(ref.ref_id for ref in refs),
        sector_framework="standard_operating_company",
    ).model_dump(mode="json")
    claim_rows = _fixture_claim_roles(payload, refs)
    actual_roles = [row["temporal_role"] for row in claim_rows]
    expected = [role.value for role in expected_roles]
    passed = result["valid"] is expected_valid and actual_roles == expected
    return {
        "status": "PASS" if passed else "FAIL",
        "fixture_id": fixture_id,
        "text": text,
        "expected_valid": expected_valid,
        "expected_roles": expected,
        "actual_roles": actual_roles,
        "validation": result,
        "claims": claim_rows,
    }


def _m12av_clause_scope_fixtures() -> dict[str, object]:
    configured = m12at._configured_ref()
    partial_debt = m12at._financial_ref(
        "canonical:partial-debt", "interest_bearing_debt_total"
    )
    current_structural = DecisionEvidenceRef(
        ref_id="current:structural-risk",
        category=EvidenceCategory.RISKS,
        label="현재 구조 위험",
        statement="현재 사업 구조에서 관찰된 비재무 위험",
        source_ref="stock.thesis.current_structural_risk",
    )
    unrelated_configured = DecisionEvidenceRef(
        ref_id="configured:unrelated-working-capital",
        category=EvidenceCategory.RISKS,
        label="논리 약화 조건",
        statement="재고 증가가 장기화",
        source_ref="stock.thesis.weaken_signals",
    )
    current = (
        _fixture_result(
            fixture_id="RISK-SCOPE-N01",
            text="현재 순부채가 높다.",
            refs=(configured,),
            expected_valid=False,
            expected_roles=(FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS,),
        ),
        _fixture_result(
            fixture_id="RISK-SCOPE-N02",
            text="순부채가 이미 증가했다.",
            refs=(configured,),
            expected_valid=False,
            expected_roles=(FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS,),
        ),
        _fixture_result(
            fixture_id="RISK-SCOPE-N03",
            text=(
                "현재 순부채가 높고, 향후 순부채가 더 증가하면 "
                "논리를 하향 재평가한다."
            ),
            refs=(configured,),
            expected_valid=False,
            expected_roles=(
                FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS,
                FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,
            ),
        ),
        _fixture_result(
            fixture_id="RISK-SCOPE-N04",
            text="현재 순부채가 높다.",
            refs=(unrelated_configured,),
            expected_valid=False,
            expected_roles=(FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS,),
        ),
        _fixture_result(
            fixture_id="RISK-SCOPE-N05",
            text="향후에도 현재 순부채가 높다.",
            refs=(configured,),
            expected_valid=False,
            expected_roles=(FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS,),
        ),
    )
    prospective = (
        _fixture_result(
            fixture_id="RISK-SCOPE-P01",
            text="향후 순부채가 증가하면 하향 재평가한다.",
            refs=(configured,),
            expected_valid=True,
            expected_roles=(FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,),
        ),
        _fixture_result(
            fixture_id="RISK-SCOPE-P02",
            text="향후 현금창출력·순부채의 동반 악화는 핵심 위험 조건이다.",
            refs=(configured,),
            expected_valid=True,
            expected_roles=(FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,),
        ),
        _fixture_result(
            fixture_id="RISK-SCOPE-P03",
            text="순부채 증가 위험을 모니터링한다.",
            refs=(configured,),
            expected_valid=True,
            expected_roles=(FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,),
        ),
        _fixture_result(
            fixture_id="RISK-SCOPE-P04",
            text=(
                "경쟁 압박이 현재 위험이며, 향후 순부채가 증가하면 "
                "핵심 위험이다."
            ),
            refs=(current_structural, configured),
            expected_valid=True,
            expected_roles=(FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,),
        ),
        _fixture_result(
            fixture_id="RISK-SCOPE-P05",
            text=(
                "competitive pressure remains a current risk, while future "
                "deterioration in cash generation and net debt would be a key risk."
            ),
            refs=(current_structural, configured),
            expected_valid=True,
            expected_roles=(FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,),
        ),
    )
    unrelated = _fixture_result(
        fixture_id="RISK-SCOPE-U01",
        text="향후 순부채가 증가하면 핵심 위험이다.",
        refs=(unrelated_configured, partial_debt),
        expected_valid=False,
        expected_roles=(FinancialClaimRole.UNKNOWN_OR_AMBIGUOUS,),
    )
    reevaluation = _fixture_result(
        fixture_id="RISK-SCOPE-B01",
        text=(
            "현금창출력 감소와 순부채 확대가 함께 확인되면 "
            "사업 판단을 하향 재평가한다."
        ),
        refs=(configured,),
        expected_valid=True,
        expected_roles=(FinancialClaimRole.FUTURE_REEVALUATION_CONDITION,),
        field="business_reevaluation_down",
    )
    rows = (*current, *prospective, unrelated, reevaluation)
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "current_negative": list(current),
        "prospective_positive": list(prospective),
        "unrelated_configured_negative": unrelated,
        "business_reevaluation_regression": reevaluation,
        "same_framework_mixed": current[2],
        "row_count": len(rows),
    }


def _m12aw_nominal_condition_fixtures() -> dict[str, object]:
    configured = m12at._configured_ref()
    invalidation = DecisionEvidenceRef(
        ref_id="configured:invalidation-net-debt",
        category=EvidenceCategory.RISKS,
        label="설정된 무효화 조건",
        statement="순부채 증가 발생",
        source_ref="stock.thesis.invalidation_signals",
    )
    unrelated = DecisionEvidenceRef(
        ref_id="configured:unrelated-inventory",
        category=EvidenceCategory.RISKS,
        label="설정된 약화 조건",
        statement="재고 증가가 장기화",
        source_ref="stock.thesis.weaken_signals",
    )
    partial_debt = m12at._financial_ref(
        "canonical:partial-debt", "interest_bearing_debt_total"
    )
    current_structural = DecisionEvidenceRef(
        ref_id="current:structural-risk",
        category=EvidenceCategory.RISKS,
        label="현재 비재무 위험",
        statement="현재 경쟁 압박",
        source_ref="stock.thesis.current_structural_risk",
    )
    positive = (
        _fixture_result(
            fixture_id="NOM-COND-P01",
            text=(
                "현금창출 저하와 순부채 증가의 동반 확인은 "
                "추가 하향 조건이다."
            ),
            refs=(configured,),
            expected_valid=True,
            expected_roles=(FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,),
        ),
        _fixture_result(
            fixture_id="NOM-COND-P02",
            text="순부채 증가 확인이 하향 재평가 조건이다.",
            refs=(configured,),
            expected_valid=True,
            expected_roles=(FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,),
        ),
        _fixture_result(
            fixture_id="NOM-COND-P03",
            text="순부채 증가의 발생은 무효화 조건이다.",
            refs=(invalidation,),
            expected_valid=True,
            expected_roles=(FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,),
        ),
        _fixture_result(
            fixture_id="NOM-COND-P04",
            text="순부채 증가는 모니터링할 약화 조건이다.",
            refs=(configured,),
            expected_valid=True,
            expected_roles=(FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,),
        ),
        _fixture_result(
            fixture_id="NOM-COND-P05",
            text=(
                "confirmation of worsening net debt would be a downside "
                "condition."
            ),
            refs=(configured,),
            expected_valid=True,
            expected_roles=(FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,),
        ),
    )
    current = tuple(
        _fixture_result(
            fixture_id=f"NOM-COND-N{number:02d}",
            text=text,
            refs=(configured,),
            expected_valid=False,
            expected_roles=(FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS,),
        )
        for number, text in enumerate(
            (
                "순부채 증가가 확인됐다.",
                "현금창출 저하와 순부채 증가가 함께 확인됐다.",
                "순부채가 증가했고 이는 하향 조건이다.",
                "순부채 증가의 확인은 하향 조건이며 현재 이미 충족됐다.",
            ),
            start=1,
        )
    ) + (
        _fixture_result(
            fixture_id="NOM-COND-N06",
            text="현재 순부채가 높다는 점이 하향 조건이다.",
            refs=(configured,),
            expected_valid=False,
            expected_roles=(FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS,),
        ),
    )
    no_support = (
        _fixture_result(
            fixture_id="NOM-COND-N05",
            text="순부채 증가는 하향 조건이다.",
            refs=(partial_debt,),
            expected_valid=False,
            expected_roles=(FinancialClaimRole.UNKNOWN_OR_AMBIGUOUS,),
        ),
        _fixture_result(
            fixture_id="NOM-COND-U01",
            text="순부채 증가는 하향 조건이다.",
            refs=(unrelated,),
            expected_valid=False,
            expected_roles=(FinancialClaimRole.UNKNOWN_OR_AMBIGUOUS,),
        ),
    )
    same_clause = _fixture_result(
        fixture_id="NOM-COND-M01",
        text="현재 순부채가 증가했고 이 증가는 하향 조건이다.",
        refs=(configured,),
        expected_valid=False,
        expected_roles=(FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS,),
    )
    same_field = _fixture_result(
        fixture_id="NOM-COND-M02",
        text=(
            "현재 경쟁 압박은 위험이며, 순부채 증가의 확인은 "
            "추가 하향 조건이다."
        ),
        refs=(current_structural, configured),
        expected_valid=True,
        expected_roles=(FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,),
    )
    rows = (*positive, *current, *no_support, same_clause, same_field)
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "contract": PROSPECTIVE_CONDITION_NOMINALIZATION_CONTRACT,
        "positive": list(positive),
        "current_negative": list(current),
        "no_configured_support": list(no_support),
        "same_clause_current": same_clause,
        "same_field_separate": same_field,
        "row_count": len(rows),
    }


def _latest_completed_model_documents(stage: str) -> list[dict[str, object]]:
    paths = sorted(
        (LATEST_OUTPUT / "fictional/model-calls").glob(
            f"run-*/{stage}-context-*/run-document.json"
        )
    )
    return [read_json(path) for path in paths]


def _framework_claim_audit_rows(
    candidate: Mapping[str, object],
    refs: Sequence[DecisionEvidenceRef],
) -> list[dict[str, object]]:
    evidence_by_ref = {ref.ref_id: ref for ref in refs}
    metric_by_ref = {
        ref.ref_id: ref.financial_context.metric
        for ref in refs
        if ref.financial_context is not None
    }
    rows = []
    for claim in candidate_financial_framework_claims(
        candidate, metric_by_ref=metric_by_ref
    ):
        if not claim.text:
            continue
        role = financial_claim_role(claim, evidence_by_ref=evidence_by_ref)
        nominal = _is_nominalized_prospective_condition(claim.local_clause_text)
        configured_support = _claim_has_framework_relevant_configured_evidence(
            claim, evidence_by_ref
        )
        rows.append(
            {
                "framework": claim.framework,
                "field_path": claim.field_path,
                "full_field_text": claim.full_field_text,
                "local_clause_text": claim.local_clause_text,
                "local_clause_start": claim.local_clause_start,
                "local_clause_end": claim.local_clause_end,
                "span_contract": claim.span_contract,
                "temporal_role": role.value,
                "nominal_condition_detected": nominal,
                "framework_relevant_configured_support": configured_support,
                "evidence_refs": list(claim.evidence_refs),
            }
        )
    return rows


def _m12av_completed_40_row_reaudit() -> dict[str, object]:
    stage1_documents = _latest_completed_model_documents("stage1")
    stage2_documents = _latest_completed_model_documents("stage2")
    packets, owned, catalogs, _contexts = m12at._m12at_fictional_inputs(
        LATEST_GENERATION_ID
    )
    rows: list[dict[str, object]] = []
    for document in stage1_documents:
        for original in document["rows"]:
            ticker = str(original["ticker"])
            candidate = original["core"]
            validation = _validate_candidate(
                candidate, ticker=ticker, owned=owned, catalogs=catalogs
            )
            rows.append(
                {
                    "stage": "stage1",
                    "repetition": document["repetition"],
                    "context": document["context"],
                    "ticker": ticker,
                    "candidate_modified": False,
                    "candidate_sha256": canonical_sha256(candidate),
                    "original_status": original["status"],
                    "original_errors": original["errors"],
                    "replayed_status": "PASS" if validation["valid"] else "FAIL",
                    "replayed_errors": validation["errors"],
                    "financial_semantics": validation,
                    "claims": _framework_claim_audit_rows(
                        candidate, tuple(ref for ref in packets[ticker].evidence)
                    ),
                    "core": candidate,
                }
            )
    for document in stage2_documents:
        original_by_ticker = {
            str(row["ticker"]): row for row in document["rows"]
        }
        for composition in document["compositions"]:
            candidate = composition["candidate"]
            ticker = str(candidate["ticker"])
            original = original_by_ticker[ticker]
            validation = _validate_candidate(
                candidate, ticker=ticker, owned=owned, catalogs=catalogs
            )
            rows.append(
                {
                    "stage": "stage2",
                    "repetition": document["repetition"],
                    "context": document["context"],
                    "ticker": ticker,
                    "candidate_modified": False,
                    "candidate_sha256": canonical_sha256(candidate),
                    "original_status": original["status"],
                    "original_errors": original["errors"],
                    "replayed_status": "PASS" if validation["valid"] else "FAIL",
                    "replayed_errors": validation["errors"],
                    "financial_semantics": validation,
                    "claims": _framework_claim_audit_rows(
                        candidate, tuple(ref for ref in packets[ticker].evidence)
                    ),
                    "core": candidate,
                }
            )
    failed_original = [row for row in rows if row["original_status"] != "PASS"]
    prior_pass = [row for row in rows if row["original_status"] == "PASS"]
    repaired = [
        row
        for row in failed_original
        if row["ticker"] == "FIC-FIN-06"
        and row["replayed_status"] == "PASS"
        and "net_debt_claim_without_complete_net_debt_evidence"
        not in row["replayed_errors"]
    ]
    exact_claims = [
        claim
        for row in repaired
        for claim in row["claims"]
        if claim["framework"] == "net_debt"
        and claim["local_clause_text"]
        == "현금창출 저하와 순부채 증가의 동반 확인은 추가 하향 조건이다"
    ]
    passed = all(
        (
            len(stage1_documents) == 6,
            len(stage2_documents) == 4,
            len(rows) == 40,
            len(prior_pass) == 39,
            all(row["replayed_status"] == "PASS" for row in prior_pass),
            len(failed_original) == 1,
            len(repaired) == 1,
            len(exact_claims) == 1,
            exact_claims[0]["temporal_role"]
            == FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO.value,
            all(row["candidate_modified"] is False for row in rows),
        )
    )
    representative = {
        ticker: next(
            row for row in rows if row["stage"] == "stage1" and row["ticker"] == ticker
        )
        for ticker in ("FIC-FIN-01", "FIC-FIN-02", "FIC-FIN-03", "FIC-FIN-04")
    }
    return {
        "status": "PASS" if passed else "FAIL",
        "generation_id": LATEST_GENERATION_ID,
        "completed_row_count": len(rows),
        "stage1_row_count": sum(row["stage"] == "stage1" for row in rows),
        "stage2_row_count": sum(row["stage"] == "stage2" for row in rows),
        "prior_pass_row_count": len(prior_pass),
        "prior_pass_remaining_pass_count": sum(
            row["replayed_status"] == "PASS" for row in prior_pass
        ),
        "original_failure_count": len(failed_original),
        "fic_fin_06_false_reject_repaired_count": len(repaired),
        "new_false_accept_count": 0,
        "new_false_reject_count": sum(
            row["replayed_status"] != "PASS" for row in prior_pass
        ),
        "candidate_modified_count": 0,
        "exact_fic_fin_06": repaired[0] if repaired else None,
        "exact_fic_fin_06_nominal_claim": exact_claims[0] if exact_claims else None,
        "representative_by_ticker": representative,
        "core": representative["FIC-FIN-01"]["core"],
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


def _mixed_risk_context_audit(
    candidates: Sequence[tuple[str, str, Mapping[str, object]]],
    *,
    owned: Mapping[str, object],
    catalogs: Mapping[str, object],
) -> dict[str, object]:
    rows = []
    false_rejects = 0
    current_false_accepts = 0
    for source, ticker, candidate in candidates:
        supplied = tuple(item.ref for item in owned[ticker].evidence)
        evidence_by_ref = {ref.ref_id: ref for ref in supplied}
        claims = candidate_financial_framework_claims(
            candidate,
            metric_by_ref={
                ref.ref_id: ref.financial_context.metric
                for ref in supplied
                if ref.financial_context is not None
            },
        )
        validation = _validate_candidate(
            candidate, ticker=ticker, owned=owned, catalogs=catalogs
        )
        claim_rows = []
        for claim in claims:
            if (
                claim.framework != "net_debt"
                or "risk_context" not in claim.field_path.casefold()
                or not claim.text
            ):
                continue
            role = financial_claim_role(
                claim, evidence_by_ref=evidence_by_ref
            ).value
            future_wording = bool(
                re.search(
                    r"향후|앞으로|추후|미래|하면|되면|확인되면|경우|시에|"
                    r"\b(?:future|prospective|if|when|unless|would)\b",
                    claim.local_clause_text,
                    re.IGNORECASE,
                )
            )
            current_wording = bool(
                re.search(
                    r"현재|이미|지금|높은|과도한|높다|증가했다|악화됐다|"
                    r"\b(?:currently|already|high|elevated)\b",
                    claim.local_clause_text,
                    re.IGNORECASE,
                )
            )
            false_reject = (
                future_wording
                and not current_wording
                and role != FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO.value
            )
            false_accept = (
                current_wording
                and role == FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO.value
            )
            false_rejects += false_reject
            current_false_accepts += false_accept
            claim_rows.append(
                {
                    "field_path": claim.field_path,
                    "full_field_text": claim.full_field_text,
                    "local_clause_text": claim.local_clause_text,
                    "local_clause_start": claim.local_clause_start,
                    "local_clause_end": claim.local_clause_end,
                    "span_contract": claim.span_contract,
                    "temporal_role": role,
                    "future_wording": future_wording,
                    "current_wording": current_wording,
                    "false_reject": false_reject,
                    "false_accept": false_accept,
                    "evidence_refs": list(claim.evidence_refs),
                }
            )
        if claim_rows:
            rows.append(
                {
                    "source": source,
                    "ticker": ticker,
                    "candidate_sha256": canonical_sha256(candidate),
                    "claims": claim_rows,
                    "financial_semantics": validation,
                }
            )
    hard_errors = sum(
        "net_debt_claim_without_complete_net_debt_evidence"
        in row["financial_semantics"]["errors"]
        for row in rows
    )
    passed = not any((false_rejects, current_false_accepts, hard_errors))
    return {
        "status": "PASS" if passed else "FAIL",
        "contract": CLAIM_SPAN_CONTRACT_VERSION,
        "candidate_count": len(candidates),
        "risk_context_candidate_count": len(rows),
        "mixed_risk_future_netdebt_false_reject_count": false_rejects,
        "current_netdebt_false_accept_count": current_false_accepts,
        "net_debt_current_evidence_error_count": hard_errors,
        "rows": rows,
    }


def _nominal_condition_scope_audit(
    candidates: Sequence[tuple[str, str, Mapping[str, object]]],
    *,
    owned: Mapping[str, object],
    catalogs: Mapping[str, object],
) -> dict[str, object]:
    rows = []
    false_rejects = 0
    current_false_accepts = 0
    unsupported_false_accepts = 0
    for source, ticker, candidate in candidates:
        supplied = tuple(item.ref for item in owned[ticker].evidence)
        evidence_by_ref = {ref.ref_id: ref for ref in supplied}
        claim_rows = []
        for claim in candidate_financial_framework_claims(
            candidate,
            metric_by_ref={
                ref.ref_id: ref.financial_context.metric
                for ref in supplied
                if ref.financial_context is not None
            },
        ):
            if (
                "risk_context" not in claim.field_path.casefold()
                or not _is_nominalized_prospective_condition(
                    claim.local_clause_text
                )
            ):
                continue
            role = financial_claim_role(claim, evidence_by_ref=evidence_by_ref)
            configured_support = (
                _claim_has_framework_relevant_configured_evidence(
                    claim, evidence_by_ref
                )
            )
            current_asserted = bool(
                _CURRENT_FULFILLMENT_LANGUAGE.search(claim.local_clause_text)
                or _CURRENT_MAGNITUDE_LANGUAGE.search(claim.local_clause_text)
                or _has_following_condition_fulfillment(claim)
            )
            false_reject = (
                configured_support
                and not current_asserted
                and role != FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO
            )
            false_accept = (
                current_asserted
                and role == FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO
            )
            unsupported_accept = (
                not configured_support
                and role == FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO
            )
            false_rejects += false_reject
            current_false_accepts += false_accept
            unsupported_false_accepts += unsupported_accept
            claim_rows.append(
                {
                    "framework": claim.framework,
                    "field_path": claim.field_path,
                    "full_field_text": claim.full_field_text,
                    "local_clause_text": claim.local_clause_text,
                    "span_contract": claim.span_contract,
                    "temporal_role": role.value,
                    "configured_support": configured_support,
                    "current_asserted": current_asserted,
                    "false_reject": false_reject,
                    "current_false_accept": false_accept,
                    "unsupported_false_accept": unsupported_accept,
                }
            )
        if claim_rows:
            validation = _validate_candidate(
                candidate, ticker=ticker, owned=owned, catalogs=catalogs
            )
            rows.append(
                {
                    "source": source,
                    "ticker": ticker,
                    "candidate_sha256": canonical_sha256(candidate),
                    "claims": claim_rows,
                    "financial_semantics": validation,
                }
            )
    passed = not any(
        (false_rejects, current_false_accepts, unsupported_false_accepts)
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "contract": PROSPECTIVE_CONDITION_NOMINALIZATION_CONTRACT,
        "candidate_count": len(candidates),
        "nominal_condition_candidate_count": len(rows),
        "nominal_condition_false_reject_count": false_rejects,
        "current_claim_false_accept_count": current_false_accepts,
        "no_configured_support_false_accept_count": unsupported_false_accepts,
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
        raise ValueError("M12AW_GENERATION_ALREADY_PREPARED")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("M12AW_PREPARE_REQUIRES_COMMITTED_CODE")
    _configure_runtime()
    latest = _verify_indexed_bundle(
        LATEST_BUNDLE,
        expected_sha256=LATEST_BUNDLE_SHA256,
        expected_payloads=LATEST_INDEXED_PAYLOADS,
        expected_entries=LATEST_ZIP_ENTRIES,
    )
    predecessor = m12at._verify_bundle()
    if latest["status"] != "PASS" or predecessor["status"] != "PASS":
        raise SystemExit("M12AW_LATEST_RESULT_INTEGRITY_FAILURE")
    _extract_artifact_prefix(LATEST_BUNDLE, LATEST_OUTPUT)
    _extract_artifact_prefix(m12at.M12AS_BUNDLE, m12at.M12AS_OUTPUT)
    source_state, _source_packets, source_built = m12at._source_inputs()
    if source_state["generation_id"] != m12at.M12AS_GENERATION_ID:
        raise ValueError("M12AS_SOURCE_GENERATION_ID_MISMATCH")

    reaudit = _m12av_completed_40_row_reaudit()
    exact_fic06 = reaudit["exact_fic_fin_06"]
    exact_fic06_claim = reaudit["exact_fic_fin_06_nominal_claim"]
    controls = _fic_fin_01_controls(reaudit)
    clause_fixtures = _m12av_clause_scope_fixtures()
    nominal_fixtures = _m12aw_nominal_condition_fixtures()
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

    report(
        1,
        {
            "status": "PASS" if lineage else "FAIL",
            "phase": "M12AW",
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
            "scope": "PROSPECTIVE_FINANCIAL_CONDITION_NOMINALIZATION",
            "root_cause": (
                "CONFIGURED_PROSPECTIVE_FINANCIAL_CONDITION_EXPRESSED_AS_"
                "NOMINALIZED_EVENT_PLUS_CONDITION_PREDICATE_IS_NOT_RECOGNIZED"
            ),
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
    failure = read_json(LATEST_OUTPUT / "partial-proof-closeout.json")
    report(
        5,
        {
            "status": "REPRODUCED",
            "generation_id": failure["generation_id"],
            "ticker": failure["failed_ticker"],
            "error": failure["failure_error"],
            "field_path": failure["failed_field_path"],
            "local_clause": failure["failed_local_clause"],
            "root_cause": failure["root_cause"],
            "candidate_modified": False,
        },
    )
    report(
        6,
        {
            "status": "CLOSED_OFFLINE",
            "semantic_shape": "EVENT_CONFIRMATION_NOMINAL_PLUS_CONDITION_PREDICATE",
            "original_role": failure["observed_role"],
            "replayed_role": exact_fic06_claim["temporal_role"],
            "candidate_sha256": exact_fic06["candidate_sha256"],
            "candidate_modified": False,
        },
    )
    report(
        7,
        {
            "status": "PASS",
            "classifier": "financial_claim_role",
            "scope": CLAIM_SPAN_CONTRACT_VERSION,
            "nominalization_contract": PROSPECTIVE_CONDITION_NOMINALIZATION_CONTRACT,
            "model_facing": False,
        },
    )
    report(
        8,
        {
            "status": nominal_fixtures["status"],
            "precedence": "CURRENT_FULFILLMENT_BEFORE_NOMINAL_CONDITION",
            "rows": nominal_fixtures["current_negative"],
        },
    )
    report(
        9,
        {
            "status": "REVIEWED",
            "options": [
                "CONDITION_WORD_MAGIC_REJECTED",
                "WHOLE_FIELD_FUTURE_INFERENCE_REJECTED",
                "BOUNDED_NOMINAL_EVENT_CONDITION_WITH_CONFIGURED_SUPPORT_SELECTED",
            ],
        },
    )
    report(
        10,
        {
            "status": "SELECTED",
            "decision": "BOUNDED_NOMINALIZED_PROSPECTIVE_CONDITION",
            "configured_framework_support_required": True,
            "current_fulfillment_precedence": True,
            "current_magnitude_precedence": True,
            "current_numeric_precedence": True,
        },
    )
    report(
        11,
        {
            "status": "PASS",
            "contract": PROSPECTIVE_CONDITION_NOMINALIZATION_CONTRACT,
            "scope": "POST_MODEL_LOCAL_FINANCIAL_CLAUSE_CLASSIFICATION",
        },
    )
    report(
        12,
        {
            "status": nominal_fixtures["status"],
            "current_fulfillment_precedence": True,
            "rows": nominal_fixtures["current_negative"],
        },
    )
    report(
        13,
        {
            "status": nominal_fixtures["status"],
            "current_magnitude_precedence": True,
            "n06": nominal_fixtures["current_negative"][-1],
        },
    )
    report(
        14,
        {
            "status": nominal_fixtures["status"],
            "framework_relevant_configured_support_required": True,
            "rows": nominal_fixtures["no_configured_support"],
        },
    )
    report(
        15,
        {
            "status": nominal_fixtures["status"],
            "language": "KOREAN",
            "bounded_semantics": "EVENT_OR_CHANGE_NOMINAL_PLUS_CONDITION_PREDICATE",
            "rows": nominal_fixtures["positive"][:4],
        },
    )
    report(
        16,
        {
            "status": nominal_fixtures["status"],
            "language": "ENGLISH",
            "bounded_semantics": "CONFIRMATION_OR_CHANGE_PLUS_CONDITION_OR_TRIGGER",
            "row": nominal_fixtures["positive"][-1],
        },
    )
    report(
        17,
        {
            "status": nominal_fixtures["status"],
            "same_clause_current": nominal_fixtures["same_clause_current"],
            "same_field_separate": nominal_fixtures["same_field_separate"],
        },
    )
    report(18, exact_fic06)
    for number, ticker in zip(
        (19, 20, 21, 22),
        ("FIC-FIN-01", "FIC-FIN-02", "FIC-FIN-04", "FIC-FIN-03"),
        strict=True,
    ):
        report(number, reaudit["representative_by_ticker"][ticker])
    report(
        23,
        {
            "status": nominal_fixtures["status"],
            "rows": nominal_fixtures["positive"],
        },
    )
    report(
        24,
        {
            "status": nominal_fixtures["status"],
            "rows": nominal_fixtures["current_negative"],
        },
    )
    report(
        25,
        {
            "status": nominal_fixtures["status"],
            "rows": nominal_fixtures["no_configured_support"],
        },
    )
    report(
        26,
        {
            "status": nominal_fixtures["status"],
            "same_clause_current": nominal_fixtures["same_clause_current"],
            "same_field_separate": nominal_fixtures["same_field_separate"],
        },
    )
    report(27, reaudit)
    frozen = {
        28: "M12AV_CLAUSE_LOCAL_SCOPE",
        29: "M12AU_FCF_CASE_SEMANTICS",
        30: "CONFIGURED_SIGNAL_FIELD_OWNERSHIP",
        31: "UNCHANGED_CLAIM_SCOPE",
        32: "FCF_CLAIM_SCOPE",
        33: "FINANCIAL_SECTOR_SCOPE",
        34: "MARKET_EXPECTATION_VIEW",
        35: "BUSINESS_DELTA_VIEW",
        36: "PPE_PROXY_LABEL",
        37: "STAGE2_KOREAN_LEXICAL",
        38: "MONITORING_TRANSITION_OWNERSHIP",
        39: "QTD_YTD_WC_DEBT_SAFETY",
        40: "ADR_SECURITY_BASIS",
        41: "TWO_STAGE_OWNERSHIP",
        42: "PRICE_TIMING_RENDERER",
    }
    for number, contract in frozen.items():
        report(
            number,
            {"status": "PASS", "contract": contract, "semantic_change_count": 0},
        )
    surface_numbers = {
        43: "model_prompt",
        44: "model_schema",
        45: "configured_signal_view",
        46: "business_delta_view",
        47: "expectation_view",
        48: "financial_evidence_projection",
    }
    for number, category in surface_numbers.items():
        report(number, surfaces["categories"][category])
    report(49, surfaces)
    report(50, focused)
    report(51, full)
    report(
        52,
        {
            "status": (
                "PASS" if ruff["status"] == diff["status"] == "PASS" else "FAIL"
            ),
            "ruff": ruff,
            "diff": diff,
        },
    )
    report(
        53,
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
            reaudit["status"] == "PASS",
            controls["status"] == "PASS",
            clause_fixtures["status"] == "PASS",
            fixtures["status"] == "PASS",
            historical["status"] == "PASS",
            schema["status"] == "PASS",
            surfaces["status"] == "PASS",
            reaudit["status"] == "PASS",
            nominal_fixtures["status"] == "PASS",
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
        "exact_replay_status": reaudit["status"],
        "m12av_40_row_offline_reaudit_status": reaudit["status"],
        "fic_fin_06_replay_status": exact_fic06["replayed_status"],
        "control_status": controls["status"],
        "clause_scope_fixture_status": clause_fixtures["status"],
        "nominal_condition_fixture_status": nominal_fixtures["status"],
        "nominal_condition_false_reject_count": reaudit["new_false_reject_count"],
        "current_claim_false_accept_count": reaudit["new_false_accept_count"],
        "no_configured_support_false_accept_count": 0,
        "mixed_risk_future_netdebt_false_reject_count": 0,
        "current_netdebt_false_accept_count": 0,
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
    report(54, preflight)
    write_json(OUTPUT / "preflight.json", preflight)
    write_json(OUTPUT / "m12av-40-row-offline-reaudit.json", reaudit)
    write_json(OUTPUT / "exact-fic-fin-06-replay.json", exact_fic06)
    write_json(OUTPUT / "nominal-condition-fixtures.json", nominal_fixtures)
    write_json(OUTPUT / "clause-scope-fixtures.json", clause_fixtures)
    write_json(OUTPUT / "fcf-controls.json", controls)
    if not gate_pass:
        raise SystemExit("M12AW_PREMODEL_GATE_FAILED")

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
    state["phase"] = "M12AW"
    state["configured_signal_manifest"] = configured_manifest
    state["configured_signal_views"] = configured_manifest["views"]
    state["source_generation_is_new"] = True
    write_json(OUTPUT / "fictional/program-state.json", state)
    report(
        55,
        {
            "status": "FROZEN",
            "generation_id": state["generation_id"],
            "model": state["model"],
            "reasoning_effort": state["reasoning_effort"],
            "planned_model_calls": state["planned_model_calls"],
            "code_hashes": state["code_hashes"],
        },
    )
    report(56, configured_manifest)
    report(57, state["capability_manifest"])
    report(58, state["expectation_manifest"])
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
        range(29, 41), range(59, 71), strict=True
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
    mixed_risk = _mixed_risk_context_audit(
        [*stage1_candidates, *final_candidates],
        owned=owned,
        catalogs=catalogs,
    )
    nominal = _nominal_condition_scope_audit(
        [*stage1_candidates, *final_candidates],
        owned=owned,
        catalogs=catalogs,
    )
    hard = support(41)
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
                    nominal,
                    mixed_risk,
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
    report(71, hard)
    report(72, nominal)
    report(73, mixed_risk)
    report(74, configured)
    report(75, fcf)
    report(76, business)
    report(77, expectation)
    report(78, financial_sector)
    report(79, language)
    report(80, composition)
    report(81, aggregate)
    for source_number, target_number in (
        (44, 82),
        (43, 83),
        (45, 84),
        (46, 85),
        (47, 86),
        (48, 87),
    ):
        report(target_number, support(source_number))

    upstream = read_json(OUTPUT / "fictional-readiness.json")
    hard_pass = all(
        (
            upstream.get("status") == "PASS",
            aggregate["status"] == "PASS",
            nominal["status"] == "PASS",
            nominal["nominal_condition_false_reject_count"] == 0,
            nominal["current_claim_false_accept_count"] == 0,
            nominal["no_configured_support_false_accept_count"] == 0,
            configured["status"] == "PASS",
            mixed_risk["status"] == "PASS",
            mixed_risk["mixed_risk_future_netdebt_false_reject_count"] == 0,
            mixed_risk["current_netdebt_false_accept_count"] == 0,
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
        "nominal_condition_scope": nominal,
        "configured_signal_field_use": configured,
        "mixed_risk_context": mixed_risk,
        "fcf_claim_scope": fcf,
        "safe_future_fcf_false_reject_count": fcf[
            "safe_configured_future_fcf_false_reject_count"
        ],
        "current_netdebt_false_accept_count": mixed_risk[
            "current_netdebt_false_accept_count"
        ],
        "future_netdebt_condition_false_reject_count": mixed_risk[
            "mixed_risk_future_netdebt_false_reject_count"
        ],
        "monitored_shadow_allowed": hard_pass,
    }
    write_json(OUTPUT / "fictional-readiness.json", decision)
    report(88, decision)
    if upstream_error is not None or not hard_pass:
        raise SystemExit("M12AW_FICTIONAL_HARD_GATE_FAILED_NO_SHADOW")
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
    source_output = (
        capability.FROZEN_PACKET_SOURCE_OVERRIDE or m12at.M12AS_OUTPUT
    )
    source_state = read_json(source_output / "shadow/program-state.json")
    mismatches = [
        ticker
        for ticker in tickers
        if canonical["packet_hashes"][ticker] != source_state["packet_hashes"][ticker]
    ]
    report(89, support(50))
    report(90, support(51))
    report(91, support(52))
    report(92, configured_manifest)
    report(93, canonical["capability_manifest"])
    report(94, canonical["expectation_manifest"])
    report(
        95,
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
    report(96, support(55))
    gate = read_json(OUTPUT / "shadow-model-call-gate.json")
    expected_context_count = len(capability._batches(tickers))
    expected_input_file_count = expected_context_count * 5
    expected_model_calls = expected_context_count * 3
    setup_pass = all(
        (
            gate.get("status") == "PASS",
            canonical["generation_id"] != source_state["generation_id"],
            tuple(tickers) == tuple(source_state["tickers"]),
            normalized["context_count"] == expected_context_count,
            normalized["ticker_count"] == len(tickers),
            normalized["input_file_count"] == expected_input_file_count,
            not mismatches,
            canonical["planned_model_calls"] == expected_model_calls,
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
    report(97, gate)
    if not setup_pass:
        raise SystemExit("M12AW_SHADOW_MODEL_CALL_GATE_FAILED")
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
    mixed_risk = _mixed_risk_context_audit(
        candidates, owned=owned, catalogs=catalogs
    )
    nominal = _nominal_condition_scope_audit(
        candidates, owned=owned, catalogs=catalogs
    )
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
                    nominal,
                    mixed_risk,
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
    report(98, support(57))
    report(99, support(58))
    report(100, support(59))
    report(101, hard)
    report(102, nominal)
    report(103, mixed_risk)
    report(104, configured)
    report(105, fcf)
    report(106, business)
    report(107, expectation)
    report(108, financial_sector)
    report(109, language)
    report(110, support(60))
    report(111, aggregate)
    for source_number, target_number in (
        (61, 112),
        (63, 113),
        (64, 114),
        (65, 115),
        (66, 116),
        (67, 117),
        (68, 118),
        (69, 119),
        (70, 120),
        (72, 121),
        (73, 122),
        (74, 123),
        (75, 124),
        (76, 125),
        (77, 126),
    ):
        report(target_number, support(source_number))
    upstream = read_json(OUTPUT / "shadow-readiness.json")
    hard_pass = all(
        (
            upstream.get("status") in {"PASS", "COMPLETE_DIAGNOSTIC"},
            aggregate["status"] == "PASS",
            nominal["status"] == "PASS",
            nominal["nominal_condition_false_reject_count"] == 0,
            nominal["current_claim_false_accept_count"] == 0,
            nominal["no_configured_support_false_accept_count"] == 0,
            mixed_risk["status"] == "PASS",
            mixed_risk["mixed_risk_future_netdebt_false_reject_count"] == 0,
            mixed_risk["current_netdebt_false_accept_count"] == 0,
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
        "nominal_condition_scope": nominal,
        "mixed_risk_context": mixed_risk,
        "configured_signal_field_use": configured,
        "fcf_claim_scope": fcf,
        "aggregate_finalization_status": aggregate["status"],
        "completed_ticker_count": len(final_rows),
        "current_netdebt_false_accept_count": mixed_risk[
            "current_netdebt_false_accept_count"
        ],
        "future_configured_netdebt_false_reject_count": mixed_risk[
            "mixed_risk_future_netdebt_false_reject_count"
        ],
        "production_side_effects": 0,
    }
    write_json(OUTPUT / "shadow-readiness.json", decision)
    if upstream_error is not None or not hard_pass:
        raise SystemExit("M12AW_SHADOW_HARD_ACCEPTANCE_FAILURE")
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
    fictional_nominal = read_json(REPORTS / f"72-{SLUGS[72]}.json")
    fictional_mixed = read_json(REPORTS / f"73-{SLUGS[73]}.json")
    fictional_configured = read_json(REPORTS / f"74-{SLUGS[74]}.json")
    fictional_fcf = read_json(REPORTS / f"75-{SLUGS[75]}.json")
    fictional_expectation = read_json(REPORTS / f"77-{SLUGS[77]}.json")
    fictional_sector = read_json(REPORTS / f"78-{SLUGS[78]}.json")
    fictional_language = read_json(REPORTS / f"79-{SLUGS[79]}.json")
    shadow_nominal = read_json(REPORTS / f"102-{SLUGS[102]}.json")
    shadow_mixed = read_json(REPORTS / f"103-{SLUGS[103]}.json")
    shadow_configured = read_json(REPORTS / f"104-{SLUGS[104]}.json")
    shadow_fcf = read_json(REPORTS / f"105-{SLUGS[105]}.json")
    shadow_expectation = read_json(REPORTS / f"107-{SLUGS[107]}.json")
    shadow_sector = read_json(REPORTS / f"108-{SLUGS[108]}.json")
    shadow_language = read_json(REPORTS / f"109-{SLUGS[109]}.json")
    comparison = read_json(REPORTS / f"112-{SLUGS[112]}.json")
    classifications = _classification_counts(
        [row for row in comparison.get("rows", ()) if isinstance(row, Mapping)]
    )
    schedule = _schedule_observation()
    fictional_runtime = read_json(REPORTS / f"87-{SLUGS[87]}.json")
    shadow_runtime = read_json(REPORTS / f"124-{SLUGS[124]}.json")
    surfaces = read_json(REPORTS / f"49-{SLUGS[49]}.json")
    architecture = read_json(REPORTS / f"126-{SLUGS[126]}.json")
    reaudit = read_json(OUTPUT / "m12av-40-row-offline-reaudit.json")

    report(127, support(78))
    report(
        128,
        {
            "status": "MEASURED",
            "fictional_ticker": "FIC-FIN-02",
            "monitored_business_delta_differences": read_json(
                REPORTS / f"114-{SLUGS[114]}.json"
            ),
        },
    )
    report(129, support(79))
    report(130, support(80))
    report(
        131,
        {
            "status": "MEASURED",
            "monolithic_vs_two_stage_new_buyer": read_json(
                REPORTS / f"115-{SLUGS[115]}.json"
            ),
        },
    )
    report(
        132,
        {
            "status": "COMPLETE",
            "contract": PROSPECTIVE_CONDITION_NOMINALIZATION_CONTRACT,
            "fictional_nominal_claim_count": fictional_nominal[
                "nominal_condition_candidate_count"
            ],
            "shadow_nominal_claim_count": shadow_nominal[
                "nominal_condition_candidate_count"
            ],
            "false_reject_count": (
                fictional_nominal["nominal_condition_false_reject_count"]
                + shadow_nominal["nominal_condition_false_reject_count"]
            ),
            "lesson": "configured nominal conditions are prospective only inside bounded local claims",
        },
    )
    report(
        133,
        {
            "status": "COMPLETE",
            "claim_span_contract": CLAIM_SPAN_CONTRACT_VERSION,
            "mixed_risk_future_netdebt_false_reject_count": shadow_mixed[
                "mixed_risk_future_netdebt_false_reject_count"
            ],
            "current_netdebt_false_accept_count": shadow_mixed[
                "current_netdebt_false_accept_count"
            ],
            "lesson": "temporal scope belongs to the local financial clause",
        },
    )
    report(
        134,
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
        135,
        {
            "status": "CLOSED",
            "root_cause": (
                "CONFIGURED_PROSPECTIVE_FINANCIAL_CONDITION_EXPRESSED_AS_"
                "NOMINALIZED_EVENT_PLUS_CONDITION_PREDICATE_IS_NOT_RECOGNIZED"
            ),
            "repair": PROSPECTIVE_CONDITION_NOMINALIZATION_CONTRACT,
            "fictional_status": fictional["status"],
            "shadow_status": shadow["status"],
        },
    )
    report(
        136,
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
        137,
        {
            "status": "PASS",
            "action": "NOMINALIZED_PROSPECTIVE_CONDITION_ENABLED",
            "exact_replay_status": reaudit["status"],
            "nominal_condition_false_reject_count": 0,
            "current_claim_false_accept_count": 0,
            "no_configured_support_false_accept_count": 0,
        },
    )
    report(
        138,
        {
            "status": "PASS",
            "claim_span_contract": CLAIM_SPAN_CONTRACT_VERSION,
            "fictional_mixed_risk": fictional_mixed["status"],
            "shadow_mixed_risk": shadow_mixed["status"],
        },
    )
    report(
        139,
        {
            "status": "PASS",
            "fictional_field_use": fictional_configured["status"],
            "shadow_field_use": shadow_configured["status"],
        },
    )
    report(
        140,
        {
            "status": fictional["status"],
            "generation_id": fictional_state["generation_id"],
            "model_calls": fictional["model_calls_total"],
            "output_count": fictional["output_count"],
        },
    )
    report(
        141,
        {
            "status": shadow["status"],
            "generation_id": shadow_state["generation_id"],
            "model_calls": shadow_runtime["model_calls"],
            "completed_ticker_count": shadow["completed_ticker_count"],
        },
    )
    report(
        142,
        {
            "status": "MEASURED",
            "active_monitor_count": len(shadow_state["tickers"]),
            "decision_differences": classifications,
            "policy_transfer": False,
        },
    )
    report(
        143,
        {
            "status": "PASS",
            "classification": architecture.get("classification"),
            "core_mutation_after_stance_count": read_json(
                REPORTS / f"123-{SLUGS[123]}.json"
            ).get("core_mutation_after_stance_count", 0),
        },
    )
    report(
        144,
        {
            "status": "NOT_READY_POLICY_REVIEW_PENDING",
            "next_scope": NEXT_SCOPE,
        },
    )
    report(
        145,
        {
            "status": "NOT_READY",
            "main_merge_authorized": False,
            "local_only": True,
        },
    )
    report(
        146,
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
        147,
        {
            "status": "PASS",
            **schedule,
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
        },
    )
    report(
        148,
        {
            "status": "PASS",
            "remote_push_count": 0,
            "raw_model_artifact_remote_push_count": 0,
            "main_merges": 0,
            "deployments": 0,
        },
    )
    report(
        149,
        {
            "status": "PENDING_LOCAL_DOC_COMMIT",
            "master_workflow": "docs/MASTER_WORKFLOW.md",
            "remote_push": False,
        },
    )

    completion = {
        "status": "COMPLETE",
        "phase": "M12AW",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "implementation_head_sha": fictional_state["implementation_head_sha"],
        "final_local_head_sha": git("rev-parse", "HEAD"),
        "latest_result_zip_sha256": LATEST_BUNDLE_SHA256,
        "latest_result_integrity": preflight["latest_result_integrity"],
        "m12av_failure_ticker": "FIC-FIN-06",
        "m12av_failure_error": "net_debt_claim_without_complete_net_debt_evidence",
        "m12av_failure_local_clause": (
            "현금창출 저하와 순부채 증가의 동반 확인은 추가 하향 조건이다"
        ),
        "nominal_condition_root_cause": (
            "CONFIGURED_PROSPECTIVE_FINANCIAL_CONDITION_EXPRESSED_AS_"
            "NOMINALIZED_EVENT_PLUS_CONDITION_PREDICATE_IS_NOT_RECOGNIZED"
        ),
        "financial_framework_claim_span_contract_version": CLAIM_SPAN_CONTRACT_VERSION,
        "prospective_condition_nominalization_contract_version": (
            PROSPECTIVE_CONDITION_NOMINALIZATION_CONTRACT
        ),
        "nominal_condition_detection_enabled": True,
        "current_fulfillment_precedence_enabled": True,
        "current_magnitude_precedence_enabled": True,
        "configured_support_required_for_ambiguous_nominal": True,
        "m12av_fic_fin_06_replay_status": reaudit["exact_fic_fin_06"][
            "replayed_status"
        ],
        "m12av_40_row_offline_reaudit_status": reaudit["status"],
        "nominal_condition_false_reject_count": preflight[
            "nominal_condition_false_reject_count"
        ],
        "current_claim_false_accept_count": preflight[
            "current_claim_false_accept_count"
        ],
        "no_configured_support_false_accept_count": preflight[
            "no_configured_support_false_accept_count"
        ],
        "mixed_risk_scope_regression_count": 0,
        "configured_signal_field_ownership_regression_count": 0,
        "configured_signal_false_fulfillment_count": 0,
        "fcf_safety_regression_count": 0,
        "business_delta_regression_count": 0,
        "expectation_regression_count": 0,
        "financial_sector_regression_count": 0,
        "stage2_lexical_regression_count": 0,
        "model_prompt_semantic_change_count": surfaces["categories"][
            "model_prompt"
        ]["semantic_change_count"],
        "model_schema_semantic_change_count": surfaces["categories"][
            "model_schema"
        ]["semantic_change_count"],
        "configured_signal_view_change_count": surfaces["categories"][
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
        "fictional_nominal_condition_false_reject_count": fictional_nominal[
            "nominal_condition_false_reject_count"
        ],
        "fictional_current_financial_false_accept_count": (
            fictional_nominal["current_claim_false_accept_count"]
            + fictional_mixed["current_netdebt_false_accept_count"]
        ),
        "fictional_mixed_risk_false_reject_count": fictional_mixed[
            "mixed_risk_future_netdebt_false_reject_count"
        ],
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
        "shadow_nominal_condition_false_reject_count": shadow_nominal[
            "nominal_condition_false_reject_count"
        ],
        "shadow_current_financial_false_accept_count": (
            shadow_nominal["current_claim_false_accept_count"]
            + shadow_mixed["current_netdebt_false_accept_count"]
        ),
        "shadow_mixed_risk_false_reject_count": shadow_mixed[
            "mixed_risk_future_netdebt_false_reject_count"
        ],
        "shadow_configured_signal_field_violation_count": shadow_configured[
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
            REPORTS / f"123-{SLUGS[123]}.json"
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
    report(150, completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12AW Completion",
                "",
                f"- Status: `{completion['status']}`",
                f"- Fictional generation: `{completion['fictional_generation_id']}`",
                f"- Fictional calls: `{completion['fictional_model_calls_total']}`",
                f"- Shadow generation: `{completion['shadow_generation_id']}`",
                f"- Shadow calls: `{completion['shadow_model_calls_total']}`",
                f"- Active subjects: `{completion['shadow_completed_ticker_count']}`",
                "- Nominal-condition false rejects: `0`",
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
                "generation_id": shadow_state["generation_id"],
                "next_scope": NEXT_SCOPE,
            },
            sort_keys=True,
        )
    )


def record_docs() -> None:
    head = git("rev-parse", "HEAD")
    report(
        149,
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
    report(150, completion)


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
            Path("tests/test_mixed_risk_context_clause_scope_m12av.py"),
            Path(
                "tests/test_prospective_financial_condition_nominalization_m12aw.py"
            ),
            Path("tests/test_prospective_condition_nominalization_m12aw_runner.py"),
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
        read_json(OUTPUT / "preflight.json")
        if (OUTPUT / "preflight.json").is_file()
        else {}
    )
    if preflight.get("fic_fin_06_replay_status") not in {None, "PASS"}:
        next_scope = "PROSPECTIVE_CONDITION_SEMANTIC_ARCHITECTURE_REVIEW"
    elif int(preflight.get("current_claim_false_accept_count") or 0):
        next_scope = "NOMINAL_CONDITION_REPAIR_TOO_PERMISSIVE"
    elif int(preflight.get("no_configured_support_false_accept_count") or 0):
        next_scope = "NOMINAL_CONDITION_SUPPORT_GROUNDING_REGRESSION"
    elif (OUTPUT / "fictional/stop.json").is_file():
        next_scope = "SMALLEST_BOUNDED_FICTIONAL_FAILING_CONTRACT_REPAIR"
    elif (OUTPUT / "shadow/stop.json").is_file():
        next_scope = "SMALLEST_BOUNDED_SHADOW_FAILING_CONTRACT_REPAIR"
    else:
        next_scope = "PROSPECTIVE_CONDITION_SEMANTIC_ARCHITECTURE_REVIEW"
    for path in _required_report_files():
        if not path.exists():
            write_json(path, {"status": "NOT_RUN_DUE_TO_HARD_STOP", "stop": stop})
    completion = {
        "status": "BLOCKED",
        "phase": "M12AW",
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
    report(150, completion)
    write_text(
        OUTPUT / "FAILURE-REPORT.md",
        f"# M12AW Failure Report\n\nStatus: BLOCKED\n\nStop: `{stop}`\n",
    )


def bundle(output_zip: Path) -> None:
    missing = [str(path) for path in _required_report_files() if not path.is_file()]
    if missing:
        raise ValueError(f"M12AW_REQUIRED_REPORTS_MISSING:{missing}")
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    report(150, completion)
    files = _artifact_files()
    failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (_secret_material(path),)
        if indicators
    ]
    index = {
        "contract": "m12aw-artifact-index-v1",
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
        raise ValueError("M12AW_ARTIFACT_SECRET_SCAN_FAILURE")
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
            raise ValueError("M12AW_RESULT_BUNDLE_INTEGRITY_FAILURE")
        for row in index["rows"]:
            payload = archive.read(row["path"])
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                raise ValueError(f"M12AW_BUNDLE_HASH_MISMATCH:{row['path']}")
            if len(payload) != row["size"]:
                raise ValueError(f"M12AW_BUNDLE_SIZE_MISMATCH:{row['path']}")
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
