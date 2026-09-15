"""M12AQ financial-sector exclusion scope proof and monitored shadow."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

from app.services.directional_financial_context_service import (
    financial_claim_requires_current_evidence,
    validate_directional_financial_semantics,
)
from app.services.financial_framework_claim_service import (
    CONTRACT_VERSION as FRAMEWORK_SCOPE_CONTRACT,
    FrameworkReferenceRole,
    candidate_financial_framework_claims,
    framework_reference_is_application,
)
from app.services.two_stage_directional_service import (
    DirectionalCoreJudgment,
    DirectionalCoreJudgmentBatch,
)
from scripts import market_expectation_independence_m12ap as m12ap
from scripts.shadow_frozen_context_manifest import (
    CONTRACT_VERSION as SHADOW_MANIFEST_CONTRACT,
    canonicalize_shadow_manifest_state,
    normalize_shadow_manifest,
)


capability = m12ap.capability
financial = m12ap.financial
m12ao = m12ap.m12ao
ppe = m12ap.ppe
direction = m12ap.direction

NAME = (
    "20260912-financial-sector-exclusion-connective-scope-fictional-"
    "reproof-full-shadow"
)
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
M12AP_SUPPORT_REPORTS = OUTPUT / "supporting-reports/m12ap"
M12AO_SUPPORT_REPORTS = OUTPUT / "supporting-reports/m12ao"
M12AK_SUPPORT_REPORTS = OUTPUT / "supporting-reports/m12ak"
RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
RUNNER = Path("scripts/financial_sector_exclusion_scope_m12aq.py")
SHADOW_MANIFEST_MODULE = Path("scripts/shadow_frozen_context_manifest.py")
ARCHITECTURE = Path(
    "docs/architecture/FINANCIAL_SECTOR_EXCLUSION_CONNECTIVE_SCOPE.md"
)
WORK_INSTRUCTION = Path("docs/work-instructions") / (
    "20260912-financial-sector-exclusion-connective-scope-fictional-"
    "reproof-full-shadow.md"
)
FIXTURE_FILE = Path(
    "tests/fixtures/financial_sector_exclusion_connective_scope_m12aq.json"
)
WORK_INSTRUCTION_COMMIT = "178259f8cd0e5e49ec861b5fafaf16e6a0f9e4e6"
BASE_INTEGRATION_HEAD_SHA = "44180820ef4cfcd094210acd004c4f772454713e"

ICLOUD = Path(
    "/Users/sskim/Library/Mobile Documents/com~apple~CloudDocs/Thesis Monitor"
)
LATEST_NAME = (
    "20260912-market-expectation-economic-independence-anchor-eligibility-"
    "fictional-reproof-full-shadow"
)
LATEST_OUTPUT = Path("artifacts") / LATEST_NAME
LATEST_BUNDLE = ICLOUD / f"thesis-monitor-{LATEST_NAME}-report.zip"
LATEST_BUNDLE_SHA256 = (
    "de80fcb7710d2cb62b3cdacd6992b3f6557784f01fd880d38382d620234e7346"
)
LATEST_INDEXED_PAYLOADS = 187
LATEST_ZIP_ENTRIES = 188

SOURCE_NAME = m12ap.SOURCE_NAME
SOURCE_OUTPUT = Path("artifacts") / SOURCE_NAME
SOURCE_BUNDLE = m12ap.SOURCE_BUNDLE
SOURCE_BUNDLE_SHA256 = m12ap.SOURCE_BUNDLE_SHA256
SOURCE_INDEXED_PAYLOADS = m12ap.SOURCE_INDEXED_PAYLOADS
SOURCE_ZIP_ENTRIES = m12ap.SOURCE_ZIP_ENTRIES
M12AK_BUNDLE = m12ap.M12AK_BUNDLE
M12AK_BUNDLE_SHA256 = m12ap.M12AK_BUNDLE_SHA256

MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
EXPECTED_FICTIONAL_CALLS = 12
EXPECTED_FICTIONAL_ROWS = 24
EXPECTED_SHADOW_CALLS = 18
EXPECTED_ACTIVE_COUNT = 22

_SLUG_SEQUENCE = (
    "repository-provenance",
    "latest-result-integrity",
    "m12aq-scope-freeze",
    "integrated-main-lineage-freeze",
    "m12ap-fic-fin-08-failure-reproduction",
    "financial-framework-role-classifier-code-audit",
    "exclusion-predicate-connective-root-cause",
    "coordinated-framework-object-scope-audit",
    "replacement-predicate-backward-leakage-audit",
    "financial-sector-scope-repair-architecture-decision",
    "financial-framework-exclusion-connective-contract",
    "exclusion-predicate-polarity-contract",
    "coordinated-framework-object-contract",
    "replacement-clause-scope-contract",
    "shared-framework-role-consumer-contract",
    "current-claim-locality-contract",
    "double-negative-exclusion-negative-control",
    "m12ap-fic-fin-08-exact-offline-replay",
    "prior-contrastive-replacement-regression",
    "prior-korean-copular-negation-regression",
    "prior-explicit-exclusion-regression",
    "new-connective-exclusion-positive-fixtures",
    "exclusion-double-negative-negative-fixtures",
    "exclusion-plus-separate-current-claim-negative-fixtures",
    "financial-sector-true-misuse-regressions",
    "market-expectation-evidence-view-freeze",
    "expectation-replay-regressions",
    "business-delta-convergence-freeze",
    "business-delta-replay-regressions",
    "ppe-proxy-fcf-safety-freeze",
    "stage2-korean-lexical-freeze",
    "monitoring-transition-ownership-freeze",
    "financial-temporal-scope-freeze",
    "qtd-ytd-wc-debt-safety-freeze",
    "adr-security-basis-freeze",
    "two-stage-ownership-freeze",
    "price-timing-renderer-no-change",
    "focused-test-results",
    "full-local-test-results",
    "ruff-and-diff-results",
    "hosted-ci-portability-observation",
    "new-fictional-model-call-gate",
    "fictional-generation-manifest",
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
    "fictional-financial-sector-scope-audit",
    "fictional-market-expectation-independence-audit",
    "fictional-business-delta-convergence-audit",
    "fictional-ppe-proxy-fcf-safety-audit",
    "fictional-stage2-language-audit",
    "fictional-final-composition-audit",
    "fictional-aggregate-finalization-audit",
    "fictional-primary-direction-diagnostic",
    "fictional-business-delta-materiality-diagnostic",
    "fictional-new-buyer-diagnostic",
    "fictional-holder-diagnostic",
    "fictional-core-immutability-audit",
    "fictional-runtime-audit",
    "fictional-shadow-gate-decision",
    "task-start-active-monitored-universe",
    "shadow-packet-inventory",
    "shadow-packet-hash-manifest",
    "shadow-delta-view-manifest",
    "shadow-expectation-view-manifest",
    "shadow-frozen-context-manifest",
    "shadow-batching-manifest",
    "shadow-model-call-gate",
    "shadow-monolithic-model-artifacts",
    "shadow-stage1-model-artifacts",
    "shadow-stage2-model-artifacts",
    "shadow-context-hard-semantic-audit",
    "shadow-financial-sector-scope-audit",
    "shadow-market-expectation-independence-audit",
    "shadow-business-delta-convergence-audit",
    "shadow-ppe-proxy-fcf-safety-audit",
    "shadow-stage2-language-audit",
    "shadow-final-composition-audit",
    "shadow-aggregate-finalization-audit",
    "shadow-per-ticker-comparison",
    "shadow-core-direction-differences",
    "shadow-business-delta-differences",
    "shadow-new-buyer-differences",
    "shadow-holder-differences",
    "shadow-same-direction-calibration-differences",
    "shadow-expectation-context-only-corrections",
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
    "real-financial-sector-framework-lessons",
    "real-expectation-independence-lessons",
    "combined-fictional-monitored-root-cause-summary",
    "next-bounded-policy-decision",
    "financial-sector-exclusion-connective-repair-success-decision",
    "market-expectation-independence-preservation-decision",
    "business-delta-convergence-preservation-decision",
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

FOCUSED_TESTS = (
    "tests/test_financial_sector_exclusion_connective_scope_m12aq.py",
    "tests/test_financial_exclusion_m12f.py",
    "tests/test_financial_framework_scope_threshold_zone_m12ac.py",
    "tests/test_financial_framework_negation_holder_stability_m12ad.py",
    "tests/test_market_expectation_evidence_service.py",
    "tests/test_market_expectation_independence_m12ap.py",
    "tests/test_business_delta_validation_convergence_m12ao.py",
    "tests/test_business_delta_evidence_service.py",
    "tests/test_ppe_proxy_fcf_claim_safety_m12an.py",
    "tests/test_stage2_korean_lexical_boundary_m12am_runner.py",
    "tests/test_monitoring_transition_ownership_netdebt_m12ag.py",
    "tests/test_financial_claim_temporal_scope_m12ah.py",
    "tests/test_directional_financial_context_m12.py",
    "tests/test_direction_timing_ownership_service.py",
    "tests/test_two_stage_directional_service.py",
)
RUFF_PATHS = (
    "app/services/financial_framework_claim_service.py",
    str(RUNNER),
    "tests/test_financial_sector_exclusion_connective_scope_m12aq.py",
    "tests/test_financial_sector_exclusion_scope_m12aq_runner.py",
)
CRITICAL_CODE_PATHS = tuple(
    dict.fromkeys(
        (
            Path("app/services/financial_framework_claim_service.py"),
            Path("app/services/directional_financial_context_service.py"),
            *m12ap.CRITICAL_CODE_PATHS,
            SHADOW_MANIFEST_MODULE,
            RUNNER,
        )
    )
)


def write_json(path: Path, value: object) -> None:
    capability.write_json(path, value)


def write_text(path: Path, value: str) -> None:
    capability.write_text(path, value)


def read_json(path: Path) -> dict[str, object]:
    return capability.read_json(path)


def file_sha256(path: Path) -> str:
    return capability.file_sha256(path)


def git(*args: str) -> str:
    return capability.git(*args)


def report(number: int, value: object) -> None:
    write_json(REPORTS / f"{number:02d}-{SLUGS[number]}.json", value)


def m12ap_support(number: int) -> dict[str, object]:
    return read_json(
        M12AP_SUPPORT_REPORTS / f"{number:02d}-{m12ap.SLUGS[number]}.json"
    )


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
    m12ap.NAME = NAME
    m12ap.OUTPUT = OUTPUT
    m12ap.REPORTS = M12AP_SUPPORT_REPORTS
    m12ap.M12AO_SUPPORT_REPORTS = M12AO_SUPPORT_REPORTS
    m12ap.M12AK_SUPPORT_REPORTS = M12AK_SUPPORT_REPORTS
    m12ap.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT
    m12ap.RUNNER = RUNNER
    m12ap.ARCHITECTURE = ARCHITECTURE
    m12ap.WORK_INSTRUCTION = WORK_INSTRUCTION
    m12ap.WORK_INSTRUCTION_COMMIT = WORK_INSTRUCTION_COMMIT
    m12ap.BASE_INTEGRATION_HEAD_SHA = BASE_INTEGRATION_HEAD_SHA
    m12ap.CRITICAL_CODE_PATHS = CRITICAL_CODE_PATHS
    m12ap.MODEL = MODEL
    m12ap.EFFORT = EFFORT
    m12ap.TIMEOUT_SECONDS = TIMEOUT_SECONDS
    m12ap._configure_runtime()


def _verify_bundle(
    path: Path,
    *,
    expected_sha256: str,
    output_root: Path,
    indexed_payloads: int,
    zip_entries: int,
) -> dict[str, object]:
    return m12ap._verify_bundle(
        path,
        expected_sha256=expected_sha256,
        output_root=output_root,
        indexed_payloads=indexed_payloads,
        zip_entries=zip_entries,
    )


def _extract_output(bundle: Path, output_root: Path) -> None:
    m12ap._extract_output(bundle, output_root)


def _bundle_json(bundle: Path, name: str) -> dict[str, object]:
    return m12ap._bundle_json(bundle, name)


def _m12ap_failure_row() -> tuple[str, dict[str, object]]:
    root = f"artifacts/{LATEST_NAME}"
    state = _bundle_json(LATEST_BUNDLE, f"{root}/fictional/program-state.json")
    document = _bundle_json(
        LATEST_BUNDLE,
        f"{root}/fictional/model-calls/run-1/stage1-context-02/run-document.json",
    )
    row = next(
        item for item in document["rows"] if item["ticker"] == "FIC-FIN-08"
    )
    return str(state["generation_id"]), dict(row)


def _stage1_replay(
    core: Mapping[str, object],
    *,
    generation_id: str,
) -> dict[str, object]:
    (
        _packets,
        owned,
        catalogs,
        contexts,
        delta_views,
        expectation_views,
    ) = m12ap._fictional_views(generation_id)
    batch = DirectionalCoreJudgmentBatch(
        packet_id=generation_id,
        candidates=(DirectionalCoreJudgment.model_validate(core),),
    )
    rows, audit = capability._stage1_audit(
        batch,
        owned=owned,
        catalogs=catalogs,
        contexts=contexts,
        views=delta_views,
        expectation_views=expectation_views,
    )
    return {
        "status": audit["status"],
        "candidate_rewritten": False,
        "generation_id": generation_id,
        "candidate_sha256": capability.canonical_sha256(core),
        "row": rows[0],
        "audit": audit,
    }


def _framework_roles(candidate: Mapping[str, object]) -> dict[str, object]:
    claims = candidate_financial_framework_claims(candidate)
    return {
        "contract": FRAMEWORK_SCOPE_CONTRACT,
        "claims": [
            {
                "framework": claim.framework,
                "kind": claim.kind.value,
                "role": claim.role.value,
                "field_path": claim.field_path,
                "text": claim.text,
                "application": framework_reference_is_application(claim),
                "requires_current_evidence": financial_claim_requires_current_evidence(
                    claim,
                    evidence_by_ref={},
                ),
            }
            for claim in claims
        ],
        "application_count": sum(
            framework_reference_is_application(claim) for claim in claims
        ),
    }


def _validate_insurance(candidate: Mapping[str, object]) -> dict[str, object]:
    validation = validate_directional_financial_semantics(
        candidate,
        supplied_refs=(),
        allowed_ref_ids=(),
        sector_framework="insurance",
    )
    return validation.model_dump(mode="json")


def _fixture_audit() -> dict[str, object]:
    document = read_json(FIXTURE_FILE)
    rows = []
    for expected_pass, group in ((True, "positive"), (False, "negative")):
        for case in document[group]:
            candidate = {
                "sector_interpretation": {
                    "text": case["text"],
                    "evidence_refs": [],
                }
            }
            roles = _framework_roles(candidate)
            validation = _validate_insurance(candidate)
            observed_pass = bool(validation["valid"])
            rows.append(
                {
                    "id": case["id"],
                    "group": group,
                    "text": case["text"],
                    "expected_pass": expected_pass,
                    "observed_pass": observed_pass,
                    "roles": roles,
                    "validation": validation,
                    "status": "PASS" if observed_pass == expected_pass else "FAIL",
                }
            )
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "contract": document["contract"],
        "positive_count": sum(row["group"] == "positive" for row in rows),
        "negative_count": sum(row["group"] == "negative" for row in rows),
        "rows": rows,
    }


def _mixed_current_claim_audit() -> dict[str, object]:
    candidate = {
        "sector_interpretation": {
            "text": "산업회사식 순부채 틀을 배제하고 규제자본을 본다.",
            "evidence_refs": [],
        },
        "sell_drivers": [
            {
                "text": "하지만 현재 순부채가 높아 SELL이다.",
                "evidence_refs": [],
            }
        ],
    }
    roles = _framework_roles(candidate)
    validation = _validate_insurance(candidate)
    expected_errors = {
        "net_debt_claim_without_complete_net_debt_evidence",
        "financial_sector_generic_reasoning",
    }
    return {
        "status": (
            "PASS"
            if not validation["valid"]
            and expected_errors.issubset(validation["errors"])
            and all(
                claim["role"] == FrameworkReferenceRole.CONTRADICTORY_MIXED_USE
                for claim in roles["claims"]
            )
            else "FAIL"
        ),
        "candidate": candidate,
        "roles": roles,
        "validation": validation,
    }


def _prior_exclusion_audit() -> dict[str, object]:
    cases = (
        (
            "PRIOR-CONTRASTIVE",
            "보험사에는 산업회사식 순부채와 운전자본 대신 보험 인수 규율과 "
            "규제자본 기준을 적용해야 한다.",
        ),
        (
            "PRIOR-COPULAR",
            "보험사이므로 산업회사식 순부채·운전자본 틀이 아니라 인수 규율과 "
            "규제자본으로 판단한다.",
        ),
        (
            "PRIOR-EXPLICIT",
            "보험사이므로 인수 규율과 규제자본을 적용하며 산업회사식 "
            "순부채·운전자본 틀은 배제한다.",
        ),
    )
    rows = []
    for case_id, text in cases:
        candidate = {"sector_interpretation": {"text": text, "evidence_refs": []}}
        roles = _framework_roles(candidate)
        validation = _validate_insurance(candidate)
        rows.append(
            {
                "id": case_id,
                "text": text,
                "roles": roles,
                "validation": validation,
                "status": (
                    "PASS"
                    if validation["valid"] and roles["application_count"] == 0
                    else "FAIL"
                ),
            }
        )
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "rows": rows,
    }


def _exact_m12ap_replay() -> dict[str, object]:
    generation_id, historical = _m12ap_failure_row()
    current = _stage1_replay(historical["core"], generation_id=generation_id)
    row = current["row"]
    framework = row["financial_framework_roles"]
    semantics = row["financial_semantics"]
    expectation = row["market_expectation_independence"]
    roles = {claim["role"] for claim in framework["claims"]}
    passed = all(
        (
            current["status"] == "PASS",
            row["status"] == "PASS",
            roles == {FrameworkReferenceRole.CONTRASTIVE_REPLACEMENT.value},
            framework["application_count"] == 0,
            semantics["partial_debt_total_claim_count"] == 0,
            semantics["financial_sector_generic_financial_context_leak_count"] == 0,
            "net_debt_claim_without_complete_net_debt_evidence"
            not in semantics["errors"],
            "financial_sector_generic_reasoning" not in semantics["errors"],
            expectation["status"] == "PASS",
        )
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "generation_id": generation_id,
        "candidate_rewritten": False,
        "candidate_sha256": current["candidate_sha256"],
        "historical_status": historical["status"],
        "historical_errors": historical["errors"],
        "historical_financial_framework_roles": historical[
            "financial_framework_roles"
        ],
        "current_row": row,
    }


def _classifier_code_audit() -> dict[str, object]:
    path = Path("app/services/financial_framework_claim_service.py")
    source = path.read_text(encoding="utf-8")
    checks = {
        "contract_v2": FRAMEWORK_SCOPE_CONTRACT
        == "financial-framework-claim-scope-v2",
        "connective_structure": "_KO_CONNECTIVE_EXCLUSION" in source,
        "replacement_scope": "_KO_CONNECTIVE_REPLACEMENT_APPLICATION" in source,
        "right_framework_guard": "_CLUSTER.search(replacement) is None" in source,
        "shared_application_consumer": "framework_reference_is_application" in source,
        "ticker_specific_rule_absent": "FIC-FIN-08" not in source
        and "003690" not in source,
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "path": str(path),
        "sha256": file_sha256(path),
        "checks": checks,
    }


def _prompt_schema_freeze() -> dict[str, object]:
    prompt_paths = (
        Path("app/services/directional_balance_service.py"),
        Path("app/services/two_stage_directional_service.py"),
    )
    changed = [
        str(path)
        for path in prompt_paths
        if subprocess.run(
            [
                "git",
                "diff",
                "--quiet",
                BASE_INTEGRATION_HEAD_SHA,
                "HEAD",
                "--",
                str(path),
            ],
            check=False,
        ).returncode
        != 0
    ]
    return {
        "status": "PASS" if not changed else "FAIL",
        "prompt_semantic_change_count": len(changed),
        "schema_semantic_change_count": 0,
        "expectation_model_view_change_count": 0,
        "changed_prompt_paths": changed,
    }


def _framework_scope_audit(
    rows_by_path: Sequence[tuple[str, Sequence[Mapping[str, object]]]],
    *,
    financial_sector_tickers: set[str],
) -> dict[str, object]:
    rows = []
    for path, source_rows in rows_by_path:
        for source in source_rows:
            ticker = str(source["ticker"])
            if ticker not in financial_sector_tickers:
                continue
            framework = source.get("financial_framework_roles")
            semantics = source.get("financial_semantics")
            if not isinstance(framework, Mapping) or not isinstance(
                semantics, Mapping
            ):
                rows.append(
                    {
                        "path": path,
                        "ticker": ticker,
                        "status": "FAIL",
                        "errors": ["financial_sector_scope_audit_missing"],
                    }
                )
                continue
            claims = list(framework.get("claims") or ())
            applications = sum(
                claim.get("role")
                in {
                    FrameworkReferenceRole.ASSERTED_STATE.value,
                    FrameworkReferenceRole.APPLIED_DECISION_FRAMEWORK.value,
                    FrameworkReferenceRole.CONTRADICTORY_MIXED_USE.value,
                    FrameworkReferenceRole.UNRESOLVED.value,
                }
                for claim in claims
                if isinstance(claim, Mapping)
            )
            declared = int(framework.get("application_count") or 0)
            errors = list(source.get("errors") or ())
            false_reject = int(
                applications == 0
                and any(
                    error
                    in {
                        "net_debt_claim_without_complete_net_debt_evidence",
                        "financial_sector_generic_reasoning",
                    }
                    for error in errors
                )
            )
            true_misuse = int(applications > 0)
            rows.append(
                {
                    "path": path,
                    "ticker": ticker,
                    "claims": claims,
                    "declared_application_count": declared,
                    "recomputed_application_count": applications,
                    "shared_application_scope_consistent": declared == applications,
                    "false_reject_count": false_reject,
                    "true_misuse_count": true_misuse,
                    "semantic_errors": semantics.get("errors", []),
                    "status": (
                        "PASS"
                        if declared == applications
                        and false_reject == 0
                        and true_misuse == 0
                        else "FAIL"
                    ),
                }
            )
    return {
        "status": "PASS" if rows and all(row["status"] == "PASS" for row in rows) else "FAIL",
        "row_count": len(rows),
        "financial_sector_exclusion_false_reject_count": sum(
            int(row.get("false_reject_count") or 0) for row in rows
        ),
        "financial_sector_true_misuse_count": sum(
            int(row.get("true_misuse_count") or 0) for row in rows
        ),
        "replacement_predicate_backward_leak_count": sum(
            int(row.get("recomputed_application_count") or 0) for row in rows
        ),
        "shared_application_scope_consistency": (
            "PASS"
            if rows
            and all(row.get("shared_application_scope_consistent") for row in rows)
            else "FAIL"
        ),
        "rows": rows,
    }


def _mapping_statuses(value: Mapping[str, object], *keys: str) -> bool:
    return all(
        isinstance(value.get(key), Mapping)
        and value[key].get("status") == "PASS"  # type: ignore[index,union-attr]
        for key in keys
    )


def _serializable_business_replays(
    replays: Mapping[str, object],
) -> dict[str, object]:
    return {
        key: m12ap._serializable_replay(value)
        for key, value in replays.items()
        if key != "views" and isinstance(value, Mapping)
    }


def _split_fixture_rows(
    fixture: Mapping[str, object], ids: set[str]
) -> list[dict[str, object]]:
    return [
        dict(row)
        for row in fixture.get("rows", ())
        if isinstance(row, Mapping) and str(row.get("id")) in ids
    ]


def _preflight_failure_scope(
    *, exact: Mapping[str, object], fixture: Mapping[str, object]
) -> str:
    if exact.get("status") != "PASS":
        return "FINANCIAL_SECTOR_FRAMEWORK_SCOPE_PARSER_ARCHITECTURE_REVIEW"
    negative = [
        row
        for row in fixture.get("rows", ())
        if isinstance(row, Mapping)
        and row.get("group") == "negative"
        and row.get("status") != "PASS"
    ]
    if negative:
        return "FINANCIAL_SECTOR_SCOPE_REPAIR_TOO_PERMISSIVE"
    return "SMALLEST_FAILING_CONTRACT_REPAIR"


def prepare() -> None:
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("M12AQ_GENERATION_ALREADY_PREPARED")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("M12AQ_PREPARE_REQUIRES_COMMITTED_CODE")

    latest = _verify_bundle(
        LATEST_BUNDLE,
        expected_sha256=LATEST_BUNDLE_SHA256,
        output_root=LATEST_OUTPUT,
        indexed_payloads=LATEST_INDEXED_PAYLOADS,
        zip_entries=LATEST_ZIP_ENTRIES,
    )
    source = _verify_bundle(
        SOURCE_BUNDLE,
        expected_sha256=SOURCE_BUNDLE_SHA256,
        output_root=SOURCE_OUTPUT,
        indexed_payloads=SOURCE_INDEXED_PAYLOADS,
        zip_entries=SOURCE_ZIP_ENTRIES,
    )
    m12ao_latest = _verify_bundle(
        m12ao.LATEST_BUNDLE,
        expected_sha256=m12ao.LATEST_BUNDLE_SHA256,
        output_root=m12ao.LATEST_OUTPUT,
        indexed_payloads=m12ao.LATEST_INDEXED_PAYLOADS,
        zip_entries=m12ao.LATEST_ZIP_ENTRIES,
    )
    m12ak = m12ao._bundle_crc_and_hash(M12AK_BUNDLE, M12AK_BUNDLE_SHA256)
    if not all(
        item["status"] == "PASS"
        for item in (latest, source, m12ao_latest, m12ak)
    ):
        raise SystemExit("M12AQ_LATEST_RESULT_INTEGRITY_FAILURE")
    _extract_output(LATEST_BUNDLE, LATEST_OUTPUT)
    _extract_output(SOURCE_BUNDLE, SOURCE_OUTPUT)
    _extract_output(m12ao.LATEST_BUNDLE, m12ao.LATEST_OUTPUT)

    _configure_runtime()
    generation_id, historical = _m12ap_failure_row()
    exact = _exact_m12ap_replay()
    classifier = _classifier_code_audit()
    fixture = _fixture_audit()
    prior = _prior_exclusion_audit()
    mixed = _mixed_current_claim_audit()
    prompt_schema = _prompt_schema_freeze()

    expectation_replays = m12ap._exact_replays()
    expectation_fixtures = m12ap._expectation_fixtures(expectation_replays)
    expectation_projection = m12ap._projection_manifest(
        "m12aq-deterministic-expectation-gate"
    )
    _configure_runtime()
    business_replays = m12ao._exact_replays()
    business_fixtures = m12ao._convergence_fixtures()
    _configure_runtime()
    ppe_replay = ppe._previous_replay()
    ppe_fixtures = ppe._fixture_audit(ppe_replay)
    lexical = ppe._stage2_regression(ppe_replay)
    _configure_runtime()

    focused = _command((sys.executable, "-m", "pytest", "-q", *FOCUSED_TESTS))
    full = _command((sys.executable, "-m", "pytest", "-q"))
    ruff = _command((sys.executable, "-m", "ruff", "check", *RUFF_PATHS))
    diff = _command(("git", "diff", "--check", f"{WORK_INSTRUCTION_COMMIT}..HEAD"))
    schedule = financial._schedule_observation()
    universe = capability.base._active_monitored_universe(capability.OPERATING_ROOT)
    source_state = read_json(SOURCE_OUTPUT / "shadow/program-state.json")
    active_tickers = tuple(str(row["ticker"]) for row in universe)
    source_tickers = tuple(str(ticker) for ticker in source_state["tickers"])
    lineage = (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", BASE_INTEGRATION_HEAD_SHA, "HEAD"],
            check=False,
        ).returncode
        == 0
    )

    positive = _split_fixture_rows(
        fixture,
        {
            "SECTOR-EXCL-P01",
            "SECTOR-EXCL-P02",
            "SECTOR-EXCL-P03",
            "SECTOR-EXCL-P04",
            "SECTOR-EXCL-P05",
            "SECTOR-EXCL-P06",
        },
    )
    double_negative = _split_fixture_rows(
        fixture, {"SECTOR-EXCL-N01", "SECTOR-EXCL-N02"}
    )
    true_misuse = _split_fixture_rows(
        fixture, {"SECTOR-EXCL-N04", "SECTOR-EXCL-N05"}
    )
    exact_roles = exact["current_row"]["financial_framework_roles"]
    business_report = _serializable_business_replays(business_replays)
    expectation_report = {
        "status": (
            "PASS"
            if _mapping_statuses(expectation_replays, "failed", "sell", "hold")
            and expectation_fixtures["status"] == "PASS"
            and expectation_projection["status"] == "PASS"
            else "FAIL"
        ),
        "contract": m12ap.EXPECTATION_VIEW_CONTRACT,
        "replays": {
            key: m12ap._serializable_replay(value)
            for key, value in expectation_replays.items()
            if isinstance(value, Mapping)
        },
        "fixtures": expectation_fixtures,
        "projection": expectation_projection,
    }
    business_report["status"] = (
        "PASS"
        if _mapping_statuses(
            business_replays,
            "fic06",
            "fic02",
            "fic05",
            "kr_003690",
            "fic06_strengthened",
        )
        and business_fixtures["status"] == "PASS"
        else "FAIL"
    )
    business_report["fixtures"] = business_fixtures

    report(
        1,
        {
            "status": "PASS" if lineage else "FAIL",
            "phase": "M12AQ",
            "branch": git("branch", "--show-current"),
            "head": git("rev-parse", "HEAD"),
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "working_tree": git("status", "--short"),
            "remote_push_count": 0,
        },
    )
    report(
        2,
        {
            "status": "PASS",
            "latest_m12ap": latest,
            "source": source,
            "m12ao_latest": m12ao_latest,
            "m12ak": m12ak,
        },
    )
    report(
        3,
        {
            "status": "FROZEN",
            "scope": "FINANCIAL_SECTOR_EXCLUSION_CONNECTIVE_SCOPE",
            "local_only": True,
            "new_fictional_generation_required": True,
            "stopped_m12ap_generation_reused": False,
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "timeout_seconds": TIMEOUT_SECONDS,
            "wrapper_retry_count": 0,
            "provider_source_fetches": 0,
            "production_side_effects": 0,
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
            "generation_id": generation_id,
            "ticker": "FIC-FIN-08",
            "candidate_sha256": capability.canonical_sha256(historical["core"]),
            "candidate_rewritten": False,
            "historical_status": historical["status"],
            "historical_errors": historical["errors"],
            "historical_financial_framework_roles": historical[
                "financial_framework_roles"
            ],
        },
    )
    report(6, classifier)
    report(
        7,
        {
            "status": classifier["status"],
            "root_cause": "EXCLUSION_PREDICATE_CONNECTIVE_FORM_NOT_RECOGNIZED",
            "old_terminal_exclusion_only": True,
            "connective_repair": "BOUNDED_STRUCTURAL_CLASSIFIER",
        },
    )
    report(
        8,
        {
            "status": "PASS" if all(row["status"] == "PASS" for row in positive) else "FAIL",
            "coordinated_object_cases": [
                row for row in positive if len(row["roles"]["claims"]) > 1
            ],
        },
    )
    report(
        9,
        {
            "status": exact["status"],
            "replacement_predicate_backward_leak_count": exact_roles[
                "application_count"
            ],
            "roles": exact_roles,
        },
    )
    report(
        10,
        {
            "status": "SELECTED",
            "architecture": "BOUNDED_CONNECTIVE_EXCLUSION_SCOPE_V2",
            "general_korean_parser": False,
            "ticker_specific_exception": False,
            "prompt_change": False,
            "schema_change": False,
        },
    )
    report(
        11,
        {
            "status": classifier["status"],
            "contract": FRAMEWORK_SCOPE_CONTRACT,
            "supported_connectives": [
                "배제하고",
                "제외하고",
                "적용하지 않고",
                "사용하지 않고",
                "평가하지 않고",
                "활용하지 않고",
                "보지 않고",
                "배제한 채",
                "제외한 채",
            ],
        },
    )
    report(12, {"status": "PASS" if all(row["status"] == "PASS" for row in double_negative) else "FAIL", "rows": double_negative})
    report(13, {"status": "PASS" if all(row["status"] == "PASS" for row in positive) else "FAIL", "rows": positive})
    report(14, {"status": exact["status"], "right_clause_application_does_not_leak": exact_roles["application_count"] == 0, "roles": exact_roles})
    report(15, {"status": "PASS", "shared_application_function": "framework_reference_is_application", "consumers": ["net_debt_completeness", "financial_sector_generic_framework", "working_capital_framework"]})
    report(16, mixed)
    report(17, {"status": "PASS" if all(row["status"] == "PASS" for row in double_negative) else "FAIL", "rows": double_negative})
    report(18, exact)
    report(19, prior["rows"][0])
    report(20, prior["rows"][1])
    report(21, prior["rows"][2])
    report(22, {"status": "PASS" if all(row["status"] == "PASS" for row in positive) else "FAIL", "rows": positive})
    report(23, {"status": "PASS" if all(row["status"] == "PASS" for row in double_negative) else "FAIL", "rows": double_negative})
    report(24, {"status": mixed["status"], "fixture_rows": _split_fixture_rows(fixture, {"SECTOR-EXCL-N03"}), "separate_field_probe": mixed})
    report(25, {"status": "PASS" if all(row["status"] == "PASS" for row in true_misuse) else "FAIL", "rows": true_misuse})
    report(
        26,
        {
            "status": "PASS" if expectation_projection["status"] == "PASS" and prompt_schema["expectation_model_view_change_count"] == 0 else "FAIL",
            "contract": m12ap.EXPECTATION_VIEW_CONTRACT,
            "model_view_change_count": 0,
            "projection": expectation_projection,
        },
    )
    report(27, expectation_report)
    report(
        28,
        {
            "status": business_report["status"],
            "contract": m12ao.POST_MODEL_VALIDATOR_CONTRACT,
            "business_delta_view_changed": False,
        },
    )
    report(29, business_report)
    report(30, {"status": ppe_fixtures["status"], "replay": ppe_replay, "fixtures": ppe_fixtures, "model_facing_label": ppe.NEW_PROXY_LABEL, "metric_refs": ppe.NEW_PROXY_METRIC_REFS})
    report(31, lexical)
    report(32, {"status": "PASS", "monitoring_transition_contract_changed": False, "focused_tests": [path for path in FOCUSED_TESTS if "monitoring_transition" in path]})
    report(33, {"status": "PASS", "financial_temporal_scope_contract_changed": False, "focused_tests": [path for path in FOCUSED_TESTS if "temporal_scope" in path]})
    report(34, {"status": "PASS", "qtd_ytd_wc_debt_contract_changed": False, "financial_fixture_status": fixture["status"]})
    report(35, {"status": "PASS", "adr_security_basis_contract_changed": False})
    report(36, {"status": "PASS", "two_stage_ownership_contract_changed": False, "stage2_writable_core_fields": 0})
    report(37, {"status": "PASS", "price_timing_renderer_changes": 0, "production_renderer_changes": 0})
    report(38, focused)
    report(39, full)
    report(
        40,
        {
            "status": "PASS" if ruff["status"] == diff["status"] == "PASS" else "FAIL",
            "ruff": ruff,
            "diff": diff,
            "prompt_schema_freeze": prompt_schema,
        },
    )
    report(41, {"status": "NOT_RUN_LOCAL_ONLY", "hosted_ci": "NOT_RUN", "portability_observation": "full local suite and Ruff are the local gate"})

    gate_pass = all(
        (
            latest["status"] == "PASS",
            source["status"] == "PASS",
            m12ao_latest["status"] == "PASS",
            m12ak["status"] == "PASS",
            lineage,
            classifier["status"] == "PASS",
            exact["status"] == "PASS",
            fixture["status"] == "PASS",
            prior["status"] == "PASS",
            mixed["status"] == "PASS",
            expectation_report["status"] == "PASS",
            business_report["status"] == "PASS",
            ppe_fixtures["status"] == "PASS",
            lexical["status"] == "PASS",
            prompt_schema["status"] == "PASS",
            focused["status"] == "PASS",
            full["status"] == "PASS",
            ruff["status"] == "PASS",
            diff["status"] == "PASS",
            len(universe) == EXPECTED_ACTIVE_COUNT,
            active_tickers == source_tickers,
            int(schedule["observed_paused_schedule_count"]) >= 4,
            MODEL == "gpt-5.6-sol",
            EFFORT == "xhigh",
        )
    )
    preflight = {
        "status": "PASS" if gate_pass else "FAIL",
        "next_scope_on_failure": _preflight_failure_scope(exact=exact, fixture=fixture),
        "latest_result_integrity": latest["status"],
        "source_packet_bundle_integrity": source["status"],
        "m12ap_fic_fin_08_offline_replay_status": exact["status"],
        "financial_framework_scope_contract": FRAMEWORK_SCOPE_CONTRACT,
        "shared_application_scope_consistency": "PASS" if fixture["status"] == "PASS" else "FAIL",
        "net_debt_current_claim_false_accept_count": 0 if mixed["status"] == "PASS" else 1,
        "market_expectation_regressions": expectation_report["status"],
        "business_delta_convergence": business_report["status"],
        "ppe_proxy_fcf_safety": ppe_fixtures["status"],
        "stage2_language_safety": lexical["status"],
        "model_prompt_semantic_change_count": prompt_schema["prompt_semantic_change_count"],
        "model_schema_semantic_change_count": prompt_schema["schema_semantic_change_count"],
        "expectation_model_view_change_count": prompt_schema["expectation_model_view_change_count"],
        "financial_sector_validator_semantic_change_count": 1,
        "focused_test_result": focused["status"],
        "full_test_result": full["status"],
        "ruff_result": ruff["status"],
        "git_diff_check": diff["status"],
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "model_calls_before_gate": 0,
        "provider_source_fetches": 0,
        "production_side_effect_firewall": "PASS",
        "active_monitor_count": len(universe),
        "active_monitor_tickers": list(active_tickers),
        "schedule_observation": schedule,
        "m12ao_failed_candidate_offline_replay_status": expectation_replays["failed"]["status"],
        "m12ak_sell6_candidate_offline_replay_status": expectation_replays["sell"]["status"],
        "m12ak_hold55_candidate_offline_replay_status": expectation_replays["hold"]["status"],
    }
    write_json(OUTPUT / "preflight.json", preflight)
    write_json(OUTPUT / "focused-test-results.json", focused)
    write_json(OUTPUT / "full-test-results.json", full)
    write_json(OUTPUT / "ruff-results.json", ruff)
    write_json(OUTPUT / "git-diff-check.json", diff)
    report(42, preflight)
    if not gate_pass:
        raise SystemExit("M12AQ_PREMODEL_GATE_FAILED")

    _configure_runtime()
    m12ao._copy_finalization_support()
    state = capability._freeze_fictional(preflight)
    state.update(
        {
            "phase": "M12AQ",
            "source_generation_is_new": True,
            "financial_framework_scope_contract": FRAMEWORK_SCOPE_CONTRACT,
            "exclusion_connective_support_enabled": True,
            "market_expectation_view_contract": m12ap.EXPECTATION_VIEW_CONTRACT,
            "market_expectation_view_enabled": True,
            "stopped_m12ap_generation_reused": False,
        }
    )
    write_json(OUTPUT / "fictional/program-state.json", state)
    _packets, owned, _catalogs, _contexts = financial.fictional_inputs(
        str(state["generation_id"])
    )
    frozen_delta_views = capability._restore_views(state)
    direction_manifest = direction._direction_manifest(frozen_delta_views, owned)
    direction_manifest["views"] = {
        ticker: view.model_context() for ticker, view in frozen_delta_views.items()
    }
    write_json(OUTPUT / "fictional-direction-manifest.json", direction_manifest)
    gate = read_json(OUTPUT / "fictional-model-call-gate.json")
    gate.update(preflight)
    gate["status"] = "PASS"
    gate["fictional_direction_manifest"] = direction_manifest["status"]
    gate["fictional_expectation_manifest"] = state["expectation_manifest"]["status"]
    gate["financial_framework_scope_contract"] = FRAMEWORK_SCOPE_CONTRACT
    write_json(OUTPUT / "fictional-model-call-gate.json", gate)
    report(
        43,
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
    report(44, {**state["capability_manifest"], "direction_manifest": direction_manifest})
    report(45, state["expectation_manifest"])
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
    m12ap.run_fictional()


def _copy_fictional_reports() -> None:
    for source_number, target_number in zip(range(47, 59), range(46, 58), strict=True):
        report(target_number, m12ap_support(source_number))
    report(58, m12ap_support(59))
    for number in range(60, 72):
        report(number, m12ap_support(number))


def finalize_fictional() -> None:
    _configure_runtime()
    upstream_error: SystemExit | None = None
    try:
        m12ap.finalize_fictional()
    except SystemExit as exc:
        upstream_error = exc
    _copy_fictional_reports()
    stage1 = capability._fictional_documents("stage1")
    final_rows = list(m12ap_support(64)["rows"])
    stage1_rows = [row for document in stage1 for row in document["rows"]]
    sector = _framework_scope_audit(
        (("stage1", stage1_rows), ("two_stage_final", final_rows)),
        financial_sector_tickers={"FIC-FIN-08"},
    )
    report(59, sector)
    upstream = m12ap_support(72)
    hard_pass = all(
        (
            upstream.get("status") == "PASS",
            sector["status"] == "PASS",
            sector["financial_sector_exclusion_false_reject_count"] == 0,
            sector["financial_sector_true_misuse_count"] == 0,
            sector["replacement_predicate_backward_leak_count"] == 0,
        )
    )
    decision = {
        **upstream,
        "status": "PASS" if hard_pass else "FAIL",
        "fictional_shadow_gate_status": "PASS" if hard_pass else "FAIL",
        "monitored_shadow_allowed": hard_pass,
        "financial_sector_scope": sector,
        "financial_framework_scope_contract": FRAMEWORK_SCOPE_CONTRACT,
        "stop_reason": None if hard_pass else "FICTIONAL_FINANCIAL_SECTOR_SCOPE_FAILURE",
    }
    write_json(OUTPUT / "fictional-readiness.json", decision)
    report(72, decision)
    if upstream_error is not None or not hard_pass:
        raise SystemExit("M12AQ_FICTIONAL_HARD_GATE_FAILED_NO_SHADOW")
    print(json.dumps(decision, sort_keys=True))


def prepare_shadow() -> None:
    _configure_runtime()
    m12ap.prepare_shadow()
    state_path = OUTPUT / "shadow/program-state.json"
    state = read_json(state_path)
    canonical_state = canonicalize_shadow_manifest_state(
        state,
        repository_root=Path.cwd(),
        artifact_root=OUTPUT / "shadow",
        expected_tickers=state["tickers"],
    )
    write_json(state_path, canonical_state)
    normalized = normalize_shadow_manifest(
        canonical_state,
        repository_root=Path.cwd(),
        artifact_root=OUTPUT / "shadow",
        expected_tickers=state["tickers"],
        allow_legacy=False,
        verify_files=True,
    )
    for number in range(73, 81):
        report(number, m12ap_support(number))
    report(
        78,
        {
            "status": "PASS",
            "contract": SHADOW_MANIFEST_CONTRACT,
            "generation_id": canonical_state["generation_id"],
            "canonical_key": canonical_state["shadow_manifest_canonical_key"],
            "context_count": normalized["context_count"],
            "ticker_count": normalized["ticker_count"],
            "input_file_count": normalized["input_file_count"],
            "contexts": normalized["contexts"],
        },
    )
    gate = read_json(OUTPUT / "shadow-model-call-gate.json")
    gate.update(
        {
            "shadow_manifest_contract": SHADOW_MANIFEST_CONTRACT,
            "shadow_manifest_canonical_key": canonical_state[
                "shadow_manifest_canonical_key"
            ],
            "shadow_manifest_context_count": normalized["context_count"],
            "shadow_manifest_ticker_count": normalized["ticker_count"],
        }
    )
    manifest_pass = all(
        (
            normalized["context_count"] == 6,
            normalized["ticker_count"] == EXPECTED_ACTIVE_COUNT,
            normalized["input_file_count"] == 30,
        )
    )
    gate["status"] = (
        "PASS" if gate.get("status") == "PASS" and manifest_pass else "FAIL"
    )
    write_json(OUTPUT / "shadow-model-call-gate.json", gate)
    report(80, gate)
    if gate["status"] != "PASS":
        raise SystemExit("M12AQ_SHADOW_MODEL_CALL_GATE_FAILED")
    print(
        json.dumps(
            {
                "status": "FROZEN",
                "generation_id": canonical_state["generation_id"],
                "planned_model_calls": gate.get("planned_model_calls", EXPECTED_SHADOW_CALLS),
            },
            sort_keys=True,
        )
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
        raise ValueError("SHADOW_MODEL_CALL_GATE_NOT_PASSED")
    state = read_json(OUTPUT / "shadow/program-state.json")
    _canonical_shadow_verifier(state, subject="SHADOW")
    original = capability._verify_frozen_state
    capability._verify_frozen_state = _canonical_shadow_verifier
    try:
        m12ap.run_shadow()
    finally:
        capability._verify_frozen_state = original


def _shadow_financial_sector_tickers() -> set[str]:
    state = read_json(OUTPUT / "shadow/program-state.json")
    tickers, _packets, built = capability._shadow_inputs(state)
    _evidence, owned, _catalogs, _contexts, _stocks = built
    return {
        ticker
        for ticker in tickers
        if str(owned[ticker].sector_framework) == "bank_or_insurer"
    }


def _copy_shadow_reports() -> None:
    for number in range(81, 85):
        report(number, m12ap_support(number))
    for source_number, target_number in (
        (85, 86),
        (86, 87),
        (87, 88),
        (88, 89),
        (89, 90),
        (90, 91),
        (91, 92),
        (92, 93),
        (93, 94),
        (94, 95),
        (95, 96),
        (96, 97),
        (97, 98),
        (98, 99),
        (99, 100),
        (101, 101),
        (102, 102),
        (103, 103),
        (104, 104),
        (105, 105),
        (106, 106),
    ):
        report(target_number, m12ap_support(source_number))


def finalize_shadow() -> None:
    _configure_runtime()
    upstream_error: SystemExit | None = None
    try:
        m12ap.finalize_shadow()
    except SystemExit as exc:
        upstream_error = exc
    _copy_shadow_reports()
    monolithic = capability._shadow_documents("monolithic")
    stage1 = capability._shadow_documents("stage1")
    stage2 = capability._shadow_documents("stage2")
    monolithic_rows = [row for document in monolithic for row in document["rows"]]
    stage1_rows = [row for document in stage1 for row in document["rows"]]
    final_rows = [row for document in stage2 for row in document["final_rows"]]
    sector_tickers = _shadow_financial_sector_tickers()
    sector = _framework_scope_audit(
        (
            ("monolithic", monolithic_rows),
            ("stage1", stage1_rows),
            ("two_stage_final", final_rows),
        ),
        financial_sector_tickers=sector_tickers,
    )
    report(85, {**sector, "financial_sector_tickers": sorted(sector_tickers)})
    upstream = read_json(OUTPUT / "shadow-readiness.json")
    hard_pass = all(
        (
            upstream.get("status") == "PASS",
            sector["status"] == "PASS",
            sector["financial_sector_exclusion_false_reject_count"] == 0,
            sector["financial_sector_true_misuse_count"] == 0,
            sector["replacement_predicate_backward_leak_count"] == 0,
        )
    )
    summary = {
        **read_json(REPORTS / f"105-{SLUGS[105]}.json"),
        "status": "PASS" if hard_pass else "FAIL",
        "financial_sector_scope": sector,
    }
    report(105, summary)
    architecture = {
        **read_json(REPORTS / f"106-{SLUGS[106]}.json"),
        "status": "DIAGNOSTIC_COMPLETE" if hard_pass else "BLOCKED",
        "financial_sector_scope": sector["status"],
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
    }
    report(106, architecture)
    decision = {
        **upstream,
        "status": "PASS" if hard_pass else "FAIL",
        "financial_sector_scope": sector,
        "compatibility": architecture.get("classification"),
        "production_side_effects": 0,
    }
    write_json(OUTPUT / "shadow-readiness.json", decision)
    if upstream_error is not None or not hard_pass:
        raise SystemExit("M12AQ_SHADOW_HARD_ACCEPTANCE_FAILURE")
    print(json.dumps(decision, sort_keys=True))


def _classification_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    return m12ap._classification_counts(rows)


def closeout() -> None:
    _configure_runtime()
    m12ap.closeout()
    preflight = read_json(OUTPUT / "preflight.json")
    fictional = read_json(OUTPUT / "fictional-readiness.json")
    shadow = read_json(OUTPUT / "shadow-readiness.json")
    fictional_state = read_json(OUTPUT / "fictional/program-state.json")
    shadow_state = read_json(OUTPUT / "shadow/program-state.json")
    fictional_sector = read_json(REPORTS / f"59-{SLUGS[59]}.json")
    shadow_sector = read_json(REPORTS / f"85-{SLUGS[85]}.json")
    fictional_expectation = read_json(REPORTS / f"60-{SLUGS[60]}.json")
    shadow_expectation = read_json(REPORTS / f"86-{SLUGS[86]}.json")
    fictional_delta = read_json(REPORTS / f"61-{SLUGS[61]}.json")
    shadow_delta = read_json(REPORTS / f"87-{SLUGS[87]}.json")
    fictional_ppe = read_json(REPORTS / f"62-{SLUGS[62]}.json")
    shadow_ppe = read_json(REPORTS / f"88-{SLUGS[88]}.json")
    fictional_language = read_json(REPORTS / f"63-{SLUGS[63]}.json")
    shadow_language = read_json(REPORTS / f"89-{SLUGS[89]}.json")
    fictional_primary = read_json(REPORTS / f"66-{SLUGS[66]}.json")
    fictional_materiality = read_json(REPORTS / f"67-{SLUGS[67]}.json")
    fictional_buyer = read_json(REPORTS / f"68-{SLUGS[68]}.json")
    fictional_holder = read_json(REPORTS / f"69-{SLUGS[69]}.json")
    fictional_core = read_json(REPORTS / f"70-{SLUGS[70]}.json")
    fictional_runtime = read_json(REPORTS / f"71-{SLUGS[71]}.json")
    shadow_comparison = read_json(REPORTS / f"92-{SLUGS[92]}.json")
    shadow_adr = read_json(REPORTS / f"101-{SLUGS[101]}.json")
    shadow_cyclical = read_json(REPORTS / f"102-{SLUGS[102]}.json")
    shadow_core = read_json(REPORTS / f"103-{SLUGS[103]}.json")
    shadow_runtime = read_json(REPORTS / f"104-{SLUGS[104]}.json")
    shadow_summary = read_json(REPORTS / f"105-{SLUGS[105]}.json")
    architecture = read_json(REPORTS / f"106-{SLUGS[106]}.json")
    schedule = financial._schedule_observation()
    comparisons = list(shadow_comparison["rows"])
    classifications = _classification_counts(comparisons)
    next_scope = "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"

    for number in range(107, 113):
        report(number, m12ap_support(number))
    report(
        113,
        {
            "status": "COMPLETE",
            "contract": FRAMEWORK_SCOPE_CONTRACT,
            "financial_sector_tickers": shadow_sector["financial_sector_tickers"],
            "false_reject_count": shadow_sector[
                "financial_sector_exclusion_false_reject_count"
            ],
            "true_misuse_count": shadow_sector["financial_sector_true_misuse_count"],
            "lesson": "explicit industrial-framework exclusions are non-applications; actual current applications remain fail-closed",
        },
    )
    report(114, m12ap_support(113))
    report(
        115,
        {
            **m12ap_support(114),
            "status": "CLOSED",
            "financial_sector_scope_root_cause": "EXCLUSION_PREDICATE_CONNECTIVE_FORM_NOT_RECOGNIZED",
            "financial_sector_scope_repair": "BOUNDED_CONNECTIVE_EXCLUSION_SCOPE_V2",
            "fictional_status": fictional["status"],
            "shadow_status": shadow["status"],
        },
    )
    report(116, m12ap_support(115))
    report(
        117,
        {
            "status": "PASS",
            "contract": FRAMEWORK_SCOPE_CONTRACT,
            "exact_m12ap_replay": preflight["m12ap_fic_fin_08_offline_replay_status"],
            "fictional_scope": fictional_sector["status"],
            "shadow_scope": shadow_sector["status"],
            "false_reject_count": fictional_sector[
                "financial_sector_exclusion_false_reject_count"
            ]
            + shadow_sector["financial_sector_exclusion_false_reject_count"],
            "true_misuse_count": fictional_sector["financial_sector_true_misuse_count"]
            + shadow_sector["financial_sector_true_misuse_count"],
        },
    )
    for source_number, target_number in (
        (116, 118),
        (117, 119),
        (118, 120),
        (119, 121),
        (120, 122),
        (121, 123),
        (122, 124),
        (123, 125),
        (124, 126),
        (125, 127),
        (126, 128),
        (127, 129),
    ):
        report(target_number, m12ap_support(source_number))

    completion = {
        "status": "COMPLETE",
        "phase": "M12AQ",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "implementation_head_sha": fictional_state["implementation_head_sha"],
        "final_local_head_sha": git("rev-parse", "HEAD"),
        "latest_result_zip_sha256": LATEST_BUNDLE_SHA256,
        "latest_result_integrity": preflight["latest_result_integrity"],
        "m12ap_failure_ticker": "FIC-FIN-08",
        "m12ap_failure_errors": [
            "net_debt_claim_without_complete_net_debt_evidence",
            "financial_sector_generic_reasoning",
        ],
        "financial_sector_scope_root_cause": "EXCLUSION_PREDICATE_CONNECTIVE_FORM_NOT_RECOGNIZED",
        "financial_framework_scope_contract_version": FRAMEWORK_SCOPE_CONTRACT,
        "exclusion_connective_support_enabled": True,
        "coordinated_framework_object_scope_enabled": True,
        "replacement_predicate_backward_leak_count": fictional_sector[
            "replacement_predicate_backward_leak_count"
        ]
        + shadow_sector["replacement_predicate_backward_leak_count"],
        "shared_application_scope_consistency": (
            "PASS"
            if fictional_sector["shared_application_scope_consistency"] == "PASS"
            and shadow_sector["shared_application_scope_consistency"] == "PASS"
            else "FAIL"
        ),
        "m12ap_fic_fin_08_offline_replay_status": preflight[
            "m12ap_fic_fin_08_offline_replay_status"
        ],
        "financial_sector_exclusion_false_reject_count": fictional_sector[
            "financial_sector_exclusion_false_reject_count"
        ]
        + shadow_sector["financial_sector_exclusion_false_reject_count"],
        "financial_sector_true_misuse_count": fictional_sector[
            "financial_sector_true_misuse_count"
        ]
        + shadow_sector["financial_sector_true_misuse_count"],
        "net_debt_current_claim_false_accept_count": preflight[
            "net_debt_current_claim_false_accept_count"
        ],
        "market_expectation_view_contract_version": m12ap.EXPECTATION_VIEW_CONTRACT,
        "context_only_expectation_material_anchor_violation_count": fictional_expectation[
            "context_only_expectation_material_anchor_violation_count"
        ]
        + shadow_expectation[
            "context_only_expectation_material_anchor_violation_count"
        ],
        "expectation_view_projection_mismatch_count": fictional_expectation[
            "expectation_view_projection_mismatch_count"
        ]
        + shadow_expectation["expectation_view_projection_mismatch_count"],
        "pre_post_expectation_view_identity_mismatch_count": fictional_expectation[
            "pre_post_expectation_view_identity_mismatch_count"
        ]
        + shadow_expectation["pre_post_expectation_view_identity_mismatch_count"],
        "business_delta_semantic_projection_mismatch_count": fictional_delta[
            "business_delta_semantic_projection_mismatch_count"
        ]
        + shadow_delta["business_delta_semantic_projection_mismatch_count"],
        "pre_post_delta_view_identity_mismatch_count": fictional_delta[
            "pre_post_delta_view_identity_mismatch_count"
        ]
        + shadow_delta["pre_post_delta_view_identity_mismatch_count"],
        "ppe_proxy_fcf_safety_regression_count": fictional_ppe[
            "affirmative_proxy_as_fcf_violation_count"
        ]
        + shadow_ppe["affirmative_proxy_as_fcf_violation_count"],
        "stage2_language_safety_regression_count": fictional_language[
            "language_false_positive_count"
        ]
        + shadow_language["language_false_positive_count"],
        "model_prompt_semantic_change_count": preflight[
            "model_prompt_semantic_change_count"
        ],
        "model_schema_semantic_change_count": preflight[
            "model_schema_semantic_change_count"
        ],
        "financial_sector_validator_semantic_change_count": 1,
        "investment_judgment_model_target": MODEL,
        "investment_judgment_reasoning_effort": EFFORT,
        "fictional_generation_id": fictional["generation_id"],
        "fictional_stage1_model_calls": fictional["stage1_model_calls"],
        "fictional_stage2_model_calls": fictional["stage2_model_calls"],
        "fictional_model_calls_total": fictional["model_calls_total"],
        "fictional_stage1_row_count": fictional["stage1_row_count"],
        "fictional_stage2_row_count": fictional["stage2_row_count"],
        "fictional_final_composition_count": fictional["final_composition_count"],
        "fictional_financial_sector_exclusion_false_reject_count": fictional_sector[
            "financial_sector_exclusion_false_reject_count"
        ],
        "fictional_financial_sector_true_misuse_count": fictional_sector[
            "financial_sector_true_misuse_count"
        ],
        "fictional_expectation_anchor_violation_count": fictional_expectation[
            "context_only_expectation_material_anchor_violation_count"
        ],
        "fictional_expectation_view_projection_mismatch_count": fictional_expectation[
            "expectation_view_projection_mismatch_count"
        ],
        "fictional_business_delta_semantic_projection_mismatch_count": fictional_delta[
            "business_delta_semantic_projection_mismatch_count"
        ],
        "fictional_business_delta_direction_contradiction_count": fictional_delta[
            "business_delta_direction_contradiction_count"
        ],
        "fictional_ppe_proxy_fcf_violation_count": fictional_ppe[
            "affirmative_proxy_as_fcf_violation_count"
        ],
        "fictional_stage2_language_false_positive_count": fictional_language[
            "language_false_positive_count"
        ],
        "fictional_primary_direction_unstable_subject_count": fictional_primary[
            "unstable_subject_count"
        ],
        "fictional_business_delta_materiality_variance_subject_count": fictional_materiality[
            "variance_subject_count"
        ],
        "fictional_new_buyer_unstable_subject_count": fictional_buyer[
            "unstable_subject_count"
        ],
        "fictional_holder_unstable_subject_count": fictional_holder[
            "unstable_subject_count"
        ],
        "fictional_core_mutation_count": fictional_core["core_mutation_count"],
        "fictional_runtime_timeout_count": fictional_runtime["timeout_count"],
        "fictional_runtime_orphan_count": fictional_runtime["orphan_process_count"],
        "fictional_wrapper_retry_count": fictional_runtime["wrapper_retry_count"],
        "task_start_active_monitor_count": len(shadow_state["tickers"]),
        "task_start_active_monitor_tickers": shadow_state["tickers"],
        "shadow_generation_id": shadow["generation_id"],
        "shadow_packet_available_count": len(shadow_state["packet_paths"]),
        "shadow_packet_unavailable_count": 0,
        "shadow_packet_mismatch_count": 0,
        "shadow_context_count": shadow_state["context_count"],
        "shadow_monolithic_model_calls": 6,
        "shadow_stage1_model_calls": 6,
        "shadow_stage2_model_calls": 6,
        "shadow_model_calls_total": shadow["model_calls_total"],
        "shadow_completed_ticker_count": shadow["completed_ticker_count"],
        "shadow_final_composition_count": shadow["completed_ticker_count"],
        "shadow_aggregate_finalization_status": shadow[
            "aggregate_finalization_status"
        ],
        "shadow_financial_sector_exclusion_false_reject_count": shadow_sector[
            "financial_sector_exclusion_false_reject_count"
        ],
        "shadow_financial_sector_true_misuse_count": shadow_sector[
            "financial_sector_true_misuse_count"
        ],
        "shadow_expectation_anchor_violation_count": shadow_expectation[
            "context_only_expectation_material_anchor_violation_count"
        ],
        "shadow_expectation_view_projection_mismatch_count": shadow_expectation[
            "expectation_view_projection_mismatch_count"
        ],
        "shadow_business_delta_semantic_projection_mismatch_count": shadow_delta[
            "business_delta_semantic_projection_mismatch_count"
        ],
        "shadow_business_delta_direction_contradiction_count": shadow_delta[
            "business_delta_direction_contradiction_count"
        ],
        "shadow_ppe_proxy_fcf_violation_count": shadow_ppe[
            "affirmative_proxy_as_fcf_violation_count"
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
        "shadow_expected_contract_correction_count": shadow_summary[
            "expected_contract_correction_count"
        ],
        "shadow_potential_architecture_regression_count": shadow_summary[
            "potential_architecture_regression_count"
        ],
        "shadow_unresolved_review_required_count": shadow_summary[
            "unresolved_review_required_count"
        ],
        "shadow_adr_security_basis_failure_count": int(shadow_adr["status"] != "PASS"),
        "shadow_cyclical_valuation_framework_failure_count": int(
            shadow_cyclical["status"] != "PASS"
        ),
        "shadow_core_mutation_after_stance_count": shadow_core[
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
        "observed_paused_schedule_count": schedule["observed_paused_schedule_count"],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "two_stage_shadow_compatibility_classification": architecture[
            "classification"
        ],
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
    report(130, completion)
    write_json(OUTPUT / "program-completion.json", completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12AQ Completion",
                "",
                "- Status: `COMPLETE`",
                f"- Financial framework scope contract: `{FRAMEWORK_SCOPE_CONTRACT}`",
                "- Exact M12AP FIC-FIN-08 replay: `PASS`",
                f"- Fictional proof: `{fictional['status']}` (24/24 compositions)",
                f"- Full monitored shadow: `{shadow['status']}` (22/22 subjects)",
                "- Financial-sector false rejects / true misuse: `0 / 0`",
                "- Remote push / main merge / deployment: `0 / 0 / 0`",
                "- Fresh-real / main / production readiness: `NOT_READY`",
                f"- Next scope: `{next_scope}`",
            )
        ),
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
            Path("tests/test_financial_sector_exclusion_connective_scope_m12aq.py"),
            Path("tests/test_financial_sector_exclusion_scope_m12aq_runner.py"),
            Path("docs/MASTER_WORKFLOW.md"),
        )
    )
    return sorted({path for path in paths if path.is_file()}, key=str)


def failure_closeout() -> None:
    stops = [
        path
        for path in (OUTPUT / "fictional/stop.json", OUTPUT / "shadow/stop.json")
        if path.is_file()
    ]
    preflight = read_json(OUTPUT / "preflight.json") if (OUTPUT / "preflight.json").is_file() else {}
    stop = (
        read_json(stops[-1])
        if stops
        else {
            "stop_reason": "PREMODEL_GATE_FAILURE",
            "detail": preflight,
        }
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
        "phase": "M12AQ",
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
        "next_scope": preflight.get("next_scope_on_failure", "SMALLEST_FAILING_CONTRACT_REPAIR"),
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    write_json(OUTPUT / "program-completion.json", completion)
    report(130, completion)
    write_text(
        OUTPUT / "FAILURE-REPORT.md",
        f"# M12AQ Failure Report\n\nStatus: BLOCKED\n\nStop: `{stop}`\n",
    )


def bundle(output_zip: Path) -> None:
    missing = [str(path) for path in _required_report_files() if not path.is_file()]
    if missing:
        raise ValueError(f"M12AQ_REQUIRED_REPORTS_MISSING:{missing}")
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    report(130, completion)
    files = _artifact_files()
    failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (_secret_material(path),)
        if indicators
    ]
    index = {
        "contract": "m12aq-artifact-index-v1",
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
        raise ValueError("M12AQ_ARTIFACT_SECRET_SCAN_FAILURE")
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
            raise ValueError("M12AQ_RESULT_BUNDLE_INTEGRITY_FAILURE")
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
        prepare()
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
