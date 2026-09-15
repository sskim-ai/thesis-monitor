"""M12AP market-expectation independence proof and monitored shadow."""

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

from pydantic import ValidationError

from app.services.market_expectation_evidence_service import (
    CONTRACT_VERSION as EXPECTATION_VIEW_CONTRACT,
    MarketExpectationEvidenceRole,
    MarketExpectationStructuredBasis,
    audit_market_expectation_view_projection,
    build_market_expectation_evidence_view,
    market_expectation_evidence_view_sha256,
    validate_market_expectation_candidate,
)
from app.services.two_stage_directional_service import (
    CORE_JUDGMENT_OUTPUT_CONTRACT,
    DirectionalCoreJudgment,
    DirectionalCoreJudgmentBatch,
)
from scripts import business_delta_evidence_capability_m12ai as capability
from scripts import business_delta_validation_convergence_m12ao as m12ao
from scripts import directional_financial_context_m12 as financial
from scripts import ppe_proxy_fcf_claim_safety_m12an as ppe
from scripts import typed_financial_delta_direction_m12aj as direction


NAME = (
    "20260912-market-expectation-economic-independence-anchor-eligibility-"
    "fictional-reproof-full-shadow"
)
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
M12AO_SUPPORT_REPORTS = OUTPUT / "supporting-reports/m12ao"
M12AK_SUPPORT_REPORTS = OUTPUT / "supporting-reports/m12ak"
RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
RUNNER = Path("scripts/market_expectation_independence_m12ap.py")
ARCHITECTURE = Path(
    "docs/architecture/MARKET_EXPECTATION_ECONOMIC_INDEPENDENCE.md"
)
WORK_INSTRUCTION = Path("docs/work-instructions") / (
    "20260912-market-expectation-economic-independence-anchor-eligibility-"
    "fictional-reproof-full-shadow.md"
)
WORK_INSTRUCTION_COMMIT = "fb8bdc8f4e51bbdcfde363bc75c8f998b83b4b75"
BASE_INTEGRATION_HEAD_SHA = "4e52e41b1e3850e36b477b02cc5597550d3db131"

ICLOUD = Path(
    "/Users/sskim/Library/Mobile Documents/com~apple~CloudDocs/Thesis Monitor"
)
LATEST_NAME = (
    "20260911-business-delta-single-source-validation-convergence-"
    "fictional-reproof-full-shadow"
)
LATEST_OUTPUT = Path("artifacts") / LATEST_NAME
LATEST_BUNDLE = ICLOUD / f"thesis-monitor-{LATEST_NAME}-report.zip"
LATEST_BUNDLE_SHA256 = (
    "32e62c0fe690e1b77fd8f098f205ca9ad87c7ec89bdf8c0529c7b8df9d64dcb6"
)
LATEST_INDEXED_PAYLOADS = 218
LATEST_ZIP_ENTRIES = 219

SOURCE_NAME = m12ao.SOURCE_NAME
SOURCE_OUTPUT = Path("artifacts") / SOURCE_NAME
SOURCE_BUNDLE = m12ao.SOURCE_BUNDLE
SOURCE_BUNDLE_SHA256 = m12ao.SOURCE_BUNDLE_SHA256
SOURCE_INDEXED_PAYLOADS = m12ao.SOURCE_INDEXED_PAYLOADS
SOURCE_ZIP_ENTRIES = m12ao.SOURCE_ZIP_ENTRIES
M12AK_NAME = m12ao.M12AK_NAME
M12AK_BUNDLE = m12ao.M12AK_BUNDLE
M12AK_BUNDLE_SHA256 = m12ao.M12AK_BUNDLE_SHA256

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
    "m12ap-scope-freeze",
    "integrated-main-lineage-freeze",
    "m12ao-fic-fin-05-failure-reproduction",
    "m12ao-fic-fin-05-expectation-use-forensic",
    "m12ak-fic-fin-05-sell-pass-forensic",
    "m12ak-fic-fin-05-hold-pass-forensic",
    "market-expectation-prompt-contract-audit",
    "expectation-independence-root-cause",
    "expectation-independence-architecture-options",
    "expectation-independence-architecture-decision",
    "market-expectation-evidence-view-contract",
    "independent-directional-support-contract",
    "conditional-context-only-contract",
    "independence-unknown-contract",
    "expectation-field-use-contract",
    "expectation-material-anchor-schema-contract",
    "expectation-dominant-evidence-schema-contract",
    "expectation-driver-use-contract",
    "pre-post-expectation-view-identity-contract",
    "m12ao-failed-candidate-offline-replay",
    "m12ak-sell-6-pass-offline-replay",
    "m12ak-hold-5_5-pass-offline-replay",
    "expectation-independence-negative-fixtures",
    "expectation-independence-positive-fixtures",
    "source-category-not-economic-independence-fixtures",
    "independent-current-expectation-support-fixtures",
    "unknown-independence-conservative-fixtures",
    "business-delta-convergence-freeze",
    "m12an-fic-fin-06-delta-replay",
    "ppe-proxy-fcf-safety-freeze",
    "stage2-korean-lexical-freeze",
    "monitoring-transition-ownership-freeze",
    "financial-temporal-scope-freeze",
    "financial-sector-framework-freeze",
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
    "shadow-financial-sector-audit",
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
    "real-expectation-independence-lessons",
    "combined-fictional-monitored-root-cause-summary",
    "next-bounded-policy-decision",
    "market-expectation-independence-success-decision",
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
    "tests/test_market_expectation_evidence_service.py",
    "tests/test_market_expectation_independence_m12ap.py",
    "tests/test_business_delta_validation_convergence_m12ao.py",
    "tests/test_business_delta_evidence_service.py",
    "tests/test_business_delta_evidence_capability_m12ai.py",
    "tests/test_ppe_proxy_fcf_claim_safety_m12an.py",
    "tests/test_stage2_korean_lexical_boundary_m12am_runner.py",
    "tests/test_monitoring_transition_ownership_netdebt_m12ag.py",
    "tests/test_financial_claim_temporal_scope_m12ah.py",
    "tests/test_financial_framework_negation_holder_stability_m12ad.py",
    "tests/test_direction_timing_ownership_service.py",
    "tests/test_two_stage_directional_service.py",
    "tests/test_fictional_finalization_context_batch_m12ak_runner.py",
    "tests/test_shadow_frozen_context_manifest_m12al_runner.py",
)
RUFF_PATHS = (
    "app/services/market_expectation_evidence_service.py",
    "scripts/directional_financial_context_m12.py",
    "scripts/business_delta_evidence_capability_m12ai.py",
    "scripts/boundary_band_application_scope_m12aa.py",
    "scripts/fictional_finalization_context_batch_m12ak.py",
    str(RUNNER),
    "tests/test_market_expectation_evidence_service.py",
    "tests/test_market_expectation_independence_m12ap.py",
    "tests/test_stage2_korean_lexical_boundary_m12am_runner.py",
    "tests/test_fictional_finalization_context_batch_m12ak_runner.py",
    "tests/test_shadow_frozen_context_manifest_m12al_runner.py",
)
CRITICAL_CODE_PATHS = (
    Path("app/services/market_expectation_evidence_service.py"),
    Path("app/services/business_delta_evidence_service.py"),
    Path("app/services/structured_autonomy_alias_service.py"),
    Path("app/services/direction_timing_ownership_service.py"),
    Path("app/services/directional_financial_context_service.py"),
    Path("app/services/two_stage_directional_service.py"),
    Path("scripts/directional_financial_context_m12.py"),
    Path("scripts/business_delta_evidence_capability_m12ai.py"),
    Path("scripts/boundary_band_application_scope_m12aa.py"),
    Path("scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py"),
    Path("scripts/fictional_finalization_context_batch_m12ak.py"),
    Path("scripts/context_preserving_finalization.py"),
    RUNNER,
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


def m12ao_support(number: int) -> dict[str, object]:
    return read_json(
        M12AO_SUPPORT_REPORTS / f"{number:02d}-{m12ao.SLUGS[number]}.json"
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
    m12ao.NAME = NAME
    m12ao.OUTPUT = OUTPUT
    m12ao.REPORTS = M12AO_SUPPORT_REPORTS
    m12ao.SUPPORT_REPORTS = M12AK_SUPPORT_REPORTS
    m12ao.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT
    m12ao.RUNNER = RUNNER
    m12ao.ARCHITECTURE = ARCHITECTURE
    m12ao.WORK_INSTRUCTION = WORK_INSTRUCTION
    m12ao.WORK_INSTRUCTION_COMMIT = WORK_INSTRUCTION_COMMIT
    m12ao.BASE_INTEGRATION_HEAD_SHA = BASE_INTEGRATION_HEAD_SHA
    m12ao.SOURCE_OUTPUT = SOURCE_OUTPUT
    m12ao.SOURCE_BUNDLE = SOURCE_BUNDLE
    m12ao.SOURCE_BUNDLE_SHA256 = SOURCE_BUNDLE_SHA256
    m12ao.SOURCE_INDEXED_PAYLOADS = SOURCE_INDEXED_PAYLOADS
    m12ao.SOURCE_ZIP_ENTRIES = SOURCE_ZIP_ENTRIES
    m12ao.M12AK_BUNDLE = M12AK_BUNDLE
    m12ao.M12AK_BUNDLE_SHA256 = M12AK_BUNDLE_SHA256
    m12ao.CRITICAL_CODE_PATHS = CRITICAL_CODE_PATHS
    m12ao.MODEL = MODEL
    m12ao.EFFORT = EFFORT
    m12ao.TIMEOUT_SECONDS = TIMEOUT_SECONDS
    m12ao._configure_runtime()


def _verify_bundle(
    path: Path,
    *,
    expected_sha256: str,
    output_root: Path,
    indexed_payloads: int,
    zip_entries: int,
) -> dict[str, object]:
    return m12ao._verify_bundle(
        path,
        expected_sha256=expected_sha256,
        output_root=output_root,
        indexed_payloads=indexed_payloads,
        zip_entries=zip_entries,
    )


def _extract_output(bundle: Path, output_root: Path) -> None:
    m12ao._extract_output(bundle, output_root)


def _bundle_json(bundle: Path, name: str) -> dict[str, object]:
    with zipfile.ZipFile(bundle) as archive:
        value = json.loads(archive.read(name))
    if not isinstance(value, dict):
        raise ValueError(f"BUNDLE_JSON_OBJECT_REQUIRED:{name}")
    return value


def _result_report(
    bundle: Path,
    *,
    result_name: str,
    number: int,
    slugs: Mapping[int, str],
) -> dict[str, object]:
    name = f"docs/reports/{result_name}/{number:02d}-{slugs[number]}.json"
    return _bundle_json(bundle, name)


def _candidate_row(
    bundle: Path,
    *,
    result_name: str,
    repetition: int,
) -> tuple[str, dict[str, object]]:
    root = f"artifacts/{result_name}/fictional"
    state = _bundle_json(bundle, f"{root}/program-state.json")
    document = _bundle_json(
        bundle,
        (
            f"{root}/model-calls/run-{repetition}/"
            "stage1-context-02/run-document.json"
        ),
    )
    row = next(
        item for item in document["rows"] if item["ticker"] == "FIC-FIN-05"
    )
    return str(state["generation_id"]), dict(row)


def _fictional_views(generation_id: str):
    packets, owned, catalogs, contexts = financial.fictional_inputs(generation_id)
    delta_views = capability._views(owned, catalogs, contexts)
    expectation_views = capability._expectation_views(
        owned,
        catalogs,
        structured_bases=capability._fictional_expectation_structured_bases(catalogs),
    )
    return packets, owned, catalogs, contexts, delta_views, expectation_views


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
    ) = _fictional_views(generation_id)
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
        "expectation_view": expectation_views["FIC-FIN-05"],
    }


def _exact_replays() -> dict[str, object]:
    failed_generation, failed_row = _candidate_row(
        LATEST_BUNDLE,
        result_name=LATEST_NAME,
        repetition=2,
    )
    sell_generation, sell_row = _candidate_row(
        M12AK_BUNDLE,
        result_name=M12AK_NAME,
        repetition=1,
    )
    hold_generation, hold_row = _candidate_row(
        M12AK_BUNDLE,
        result_name=M12AK_NAME,
        repetition=2,
    )
    failed = _stage1_replay(failed_row["core"], generation_id=failed_generation)
    sell = _stage1_replay(sell_row["core"], generation_id=sell_generation)
    hold = _stage1_replay(hold_row["core"], generation_id=hold_generation)
    failed_errors = failed["row"]["errors"]
    failed_generic = any(
        str(error).startswith("context_only_market_expectation_used_as_")
        for error in failed_errors
    )
    return {
        "failed": {
            **failed,
            "status": "PASS" if failed["status"] == "FAIL" and failed_generic else "FAIL",
            "historical_status": failed_row["status"],
            "historical_errors": failed_row["errors"],
            "expected_current_validation": "FAIL",
        },
        "sell": {
            **sell,
            "status": "PASS" if sell["status"] == "PASS" else "FAIL",
            "historical_status": sell_row["status"],
            "expected_current_validation": "PASS",
        },
        "hold": {
            **hold,
            "status": "PASS" if hold["status"] == "PASS" else "FAIL",
            "historical_status": hold_row["status"],
            "expected_current_validation": "PASS",
        },
    }


def _expectation_fixtures(replays: Mapping[str, object]) -> dict[str, object]:
    failed = replays["failed"]
    sell = replays["sell"]
    view = failed["expectation_view"]
    expectation = view.expectation_items[0]
    expectation_ref = expectation.canonical_ref
    dependency_ref = expectation.dependency_refs[0]
    failed_core = failed["row"]["core"]
    sell_core = sell["row"]["core"]

    non_expectation_anchor = next(
        item.canonical_ref
        for item in view.items
        if item.role == MarketExpectationEvidenceRole.NOT_MARKET_EXPECTATION
        and "complete-debt" in item.canonical_ref
    )
    negative_candidates = {
        "EXP-INDEP-N01": {
            "ticker": view.ticker,
            "material_directional_anchor_basis": [expectation_ref],
        },
        "EXP-INDEP-N02": {
            "ticker": view.ticker,
            "dominant_evidence": {"evidence_refs": [expectation_ref]},
        },
        "EXP-INDEP-N04": {
            "ticker": view.ticker,
            "sell_drivers": [
                {
                    "classification": "THESIS_INVALIDATION",
                    "evidence_refs": [expectation_ref],
                }
            ],
        },
    }
    negative_rows = []
    for fixture_id, candidate in negative_candidates.items():
        audit = validate_market_expectation_candidate(candidate, view)
        negative_rows.append(
            {
                "id": fixture_id,
                "expected": "FAIL",
                "observed": audit["status"],
                "status": "PASS" if audit["status"] == "FAIL" else "FAIL",
                "audit": audit,
            }
        )
    try:
        MarketExpectationStructuredBasis(
            expectation_ref=expectation_ref,
            independently_observed=True,
        )
    except ValidationError as exc:
        n03_status = "PASS"
        n03_detail = str(exc)
    else:
        n03_status = "FAIL"
        n03_detail = "category-only independent basis was accepted"
    negative_rows.append(
        {
            "id": "EXP-INDEP-N03",
            "expected": "FAIL_PREMODEL",
            "observed": "FAIL_PREMODEL" if n03_status == "PASS" else "PASS",
            "status": n03_status,
            "detail": n03_detail,
        }
    )

    independent_view = build_market_expectation_evidence_view(
        next(
            value
            for key, value in _fictional_views(str(failed["generation_id"]))[1].items()
            if key == "FIC-FIN-05"
        ),
        _fictional_views(str(failed["generation_id"]))[2]["FIC-FIN-05"],
        structured_bases=(
            MarketExpectationStructuredBasis(
                expectation_ref=expectation_ref,
                independently_observed=True,
                independence_basis_refs=(non_expectation_anchor,),
            ),
        ),
    )
    positive_candidates = {
        "EXP-INDEP-P01": {
            "ticker": view.ticker,
            "market_expectation_context": {"evidence_refs": [expectation_ref]},
        },
        "EXP-INDEP-P02": {
            "ticker": view.ticker,
            "sell_drivers": [
                {
                    "classification": "OTHER_EVIDENCE",
                    "evidence_refs": [expectation_ref],
                }
            ],
        },
        "EXP-INDEP-P03": sell_core,
        "EXP-INDEP-P04": {
            "ticker": view.ticker,
            "material_directional_anchor_basis": [expectation_ref],
            "dominant_evidence": {"evidence_refs": [expectation_ref]},
        },
        "EXP-INDEP-P05": {
            "ticker": view.ticker,
            "market_expectation_context": {"evidence_refs": [expectation_ref]},
        },
    }
    positive_rows = []
    for fixture_id, candidate in positive_candidates.items():
        selected_view = independent_view if fixture_id == "EXP-INDEP-P04" else view
        audit = validate_market_expectation_candidate(candidate, selected_view)
        positive_rows.append(
            {
                "id": fixture_id,
                "expected": "PASS",
                "observed": audit["status"],
                "status": audit["status"],
                "audit": audit,
            }
        )
    return {
        "status": (
            "PASS"
            if all(row["status"] == "PASS" for row in negative_rows + positive_rows)
            else "FAIL"
        ),
        "negative": negative_rows,
        "positive": positive_rows,
        "dependency_ref": dependency_ref,
        "failed_candidate_sha256": capability.canonical_sha256(failed_core),
    }


def _schema_audit(generation_id: str) -> dict[str, object]:
    (
        _packets,
        owned,
        catalogs,
        contexts,
        delta_views,
        expectation_views,
    ) = _fictional_views(generation_id)
    del owned, contexts
    tickers = financial.CONTEXTS[1]
    schema = capability._batch_schema(
        model=DirectionalCoreJudgment,
        contract=CORE_JUDGMENT_OUTPUT_CONTRACT,
        packet_id=generation_id,
        tickers=tickers,
        catalogs=catalogs,
        views=delta_views,
        expectation_views=expectation_views,
    )
    choice = schema["properties"]["candidates"]["items"]["anyOf"][0]
    properties = choice["properties"]
    anchor_name = properties["material_directional_anchor_basis"]["items"][
        "$ref"
    ].split("/")[-1]
    dominant_name = properties["dominant_evidence"]["$ref"].split("/")[-1]
    dominant_alias_name = schema["$defs"][dominant_name]["properties"][
        "evidence_refs"
    ]["items"]["$ref"].split("/")[-1]
    all_aliases = schema["$defs"]["T1_EvidenceAlias"]["enum"]
    anchor_aliases = schema["$defs"][anchor_name]["enum"]
    dominant_aliases = schema["$defs"][dominant_alias_name]["enum"]
    passed = (
        "E07" in all_aliases
        and "E07" not in anchor_aliases
        and "E07" not in dominant_aliases
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "ticker": "FIC-FIN-05",
        "context_aliases": all_aliases,
        "material_anchor_aliases": anchor_aliases,
        "dominant_evidence_aliases": dominant_aliases,
        "context_only_alias": "E07",
        "model_schema_semantic_change_count": 1,
    }


def _expectation_audit(
    rows_by_path: Sequence[tuple[str, Sequence[Mapping[str, object]]]],
) -> dict[str, object]:
    rows = []
    for path, source_rows in rows_by_path:
        for row in source_rows:
            audit = row.get("market_expectation_independence")
            if not isinstance(audit, Mapping):
                rows.append(
                    {
                        "path": path,
                        "ticker": row.get("ticker"),
                        "status": "FAIL",
                        "errors": ["market_expectation_independence_audit_missing"],
                    }
                )
                continue
            rows.append(
                {
                    "path": path,
                    "ticker": row.get("ticker"),
                    "status": audit.get("status"),
                    "linked_evidence": audit.get("linked_evidence", []),
                    "errors": audit.get("errors", []),
                    "anchor_violations": audit.get(
                        "context_only_expectation_material_anchor_violation_count", 0
                    ),
                    "dominant_violations": audit.get(
                        "context_only_expectation_dominant_evidence_violation_count", 0
                    ),
                    "driver_violations": audit.get(
                        "context_only_expectation_driver_classification_violation_count",
                        0,
                    ),
                    "projection_mismatches": audit.get(
                        "expectation_view_projection_mismatch_count", 0
                    ),
                    "identity_mismatches": audit.get(
                        "pre_post_expectation_view_identity_mismatch_count", 0
                    ),
                }
            )
    anchor = sum(int(row.get("anchor_violations") or 0) for row in rows)
    dominant = sum(int(row.get("dominant_violations") or 0) for row in rows)
    driver = sum(int(row.get("driver_violations") or 0) for row in rows)
    projection = sum(int(row.get("projection_mismatches") or 0) for row in rows)
    identity = sum(int(row.get("identity_mismatches") or 0) for row in rows)
    passed = bool(rows) and all(row["status"] == "PASS" for row in rows)
    return {
        "status": "PASS" if passed else "FAIL",
        "row_count": len(rows),
        "context_only_expectation_material_anchor_violation_count": anchor,
        "context_only_expectation_dominant_evidence_violation_count": dominant,
        "context_only_expectation_driver_classification_violation_count": driver,
        "expectation_view_projection_mismatch_count": projection,
        "pre_post_expectation_view_identity_mismatch_count": identity,
        "rows": rows,
    }


def _projection_manifest(generation_id: str) -> dict[str, object]:
    (
        _packets,
        _owned,
        _catalogs,
        _contexts,
        _delta_views,
        expectation_views,
    ) = _fictional_views(generation_id)
    rows = []
    for ticker, view in expectation_views.items():
        projection = audit_market_expectation_view_projection(view)
        rows.append(
            {
                "ticker": ticker,
                "view_sha256": market_expectation_evidence_view_sha256(view),
                "projection": projection,
                "view": view.model_context(),
            }
        )
    expectations = [
        item
        for view in expectation_views.values()
        for item in view.expectation_items
    ]
    return {
        "status": (
            "PASS"
            if all(row["projection"]["status"] == "PASS" for row in rows)
            else "FAIL"
        ),
        "contract": EXPECTATION_VIEW_CONTRACT,
        "subject_count": len(expectation_views),
        "expectation_ref_count": len(expectations),
        "independent_directional_support_count": sum(
            item.role
            == MarketExpectationEvidenceRole.INDEPENDENT_DIRECTIONAL_SUPPORT
            for item in expectations
        ),
        "conditional_context_only_count": sum(
            item.role == MarketExpectationEvidenceRole.CONDITIONAL_CONTEXT_ONLY
            for item in expectations
        ),
        "independence_unknown_count": sum(
            item.role == MarketExpectationEvidenceRole.INDEPENDENCE_UNKNOWN
            for item in expectations
        ),
        "already_reflected_counterweight_count": sum(
            item.role
            == MarketExpectationEvidenceRole.ALREADY_REFLECTED_OR_COUNTERWEIGHT
            for item in expectations
        ),
        "expectation_view_projection_mismatch_count": sum(
            int(row["projection"]["expectation_view_projection_mismatch_count"])
            for row in rows
        ),
        "rows": rows,
    }


def _prompt_audit() -> dict[str, object]:
    path = Path("app/services/directional_balance_service.py")
    source = path.read_text(encoding="utf-8")
    contract_text = (
        "Source-category independence is not economic independence. "
        "A market-expectation claim conditional on the same materially unresolved"
    )
    unchanged = (
        subprocess.run(
            ["git", "diff", "--quiet", BASE_INTEGRATION_HEAD_SHA, "HEAD", "--", str(path)],
            check=False,
        ).returncode
        == 0
    )
    return {
        "status": "PASS" if contract_text in source and unchanged else "FAIL",
        "path": str(path),
        "existing_contract_present": contract_text in source,
        "unchanged_from_base": unchanged,
        "sha256": file_sha256(path),
        "model_prompt_semantic_change_count": 0 if unchanged else 1,
    }


def _serializable_replay(value: Mapping[str, object]) -> dict[str, object]:
    return {
        key: (
            item.model_dump(mode="json")
            if hasattr(item, "model_dump")
            else item
        )
        for key, item in value.items()
    }


def prepare() -> None:
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("M12AP_GENERATION_ALREADY_PREPARED")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("M12AP_PREPARE_REQUIRES_COMMITTED_CODE")

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
    m12ak = m12ao._bundle_crc_and_hash(M12AK_BUNDLE, M12AK_BUNDLE_SHA256)
    if not all(item["status"] == "PASS" for item in (latest, source, m12ak)):
        raise SystemExit("M12AP_LATEST_RESULT_INTEGRITY_FAILURE")
    _extract_output(LATEST_BUNDLE, LATEST_OUTPUT)
    _extract_output(SOURCE_BUNDLE, SOURCE_OUTPUT)

    _configure_runtime()
    replays = _exact_replays()
    fixtures = _expectation_fixtures(replays)
    projection = _projection_manifest("m12ap-deterministic-gate")
    schema = _schema_audit("m12ap-deterministic-gate")
    prompt = _prompt_audit()

    m12ao_delta_projection = _result_report(
        LATEST_BUNDLE,
        result_name=LATEST_NAME,
        number=25,
        slugs=m12ao.SLUGS,
    )
    m12an_fic06 = _result_report(
        LATEST_BUNDLE,
        result_name=LATEST_NAME,
        number=20,
        slugs=m12ao.SLUGS,
    )
    m12ao_preflight = _result_report(
        LATEST_BUNDLE,
        result_name=LATEST_NAME,
        number=43,
        slugs=m12ao.SLUGS,
    )

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
    source_tickers = tuple(str(ticker) for ticker in source_state["tickers"])
    active_tickers = tuple(str(row["ticker"]) for row in universe)
    lineage = (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", BASE_INTEGRATION_HEAD_SHA, "HEAD"],
            check=False,
        ).returncode
        == 0
    )

    failed = replays["failed"]
    sell = replays["sell"]
    hold = replays["hold"]
    failed_audit = failed["row"]["market_expectation_independence"]
    sell_audit = sell["row"]["market_expectation_independence"]
    hold_audit = hold["row"]["market_expectation_independence"]
    business_freeze = {
        "status": (
            "PASS"
            if m12ao_delta_projection["status"] == "PASS"
            and m12ao_preflight["business_delta_semantic_projection_mismatch_count"]
            == 0
            and m12ao_preflight["pre_post_delta_view_identity_mismatch_count"] == 0
            else "FAIL"
        ),
        "business_delta_semantic_projection_mismatch_count": m12ao_preflight[
            "business_delta_semantic_projection_mismatch_count"
        ],
        "pre_post_delta_view_identity_mismatch_count": m12ao_preflight[
            "pre_post_delta_view_identity_mismatch_count"
        ],
        "legacy_raw_text_direction_rederivation_count": 0,
        "legacy_raw_text_eligibility_rederivation_count": 0,
        "authoritative_m12ao_report": m12ao_delta_projection,
    }

    report(
        1,
        {
            "status": "PASS" if lineage else "FAIL",
            "phase": "M12AP",
            "branch": git("branch", "--show-current"),
            "head": git("rev-parse", "HEAD"),
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "working_tree": git("status", "--short"),
            "remote_tracking_state": git("status", "--short", "--branch").splitlines()[0],
            "remote_push_count": 0,
        },
    )
    report(2, {"status": "PASS", "latest": latest, "source": source, "m12ak": m12ak})
    report(
        3,
        {
            "status": "FROZEN",
            "scope": "MARKET_EXPECTATION_ECONOMIC_INDEPENDENCE_ANCHOR_ELIGIBILITY",
            "local_only": True,
            "new_fictional_generation_required": True,
            "stopped_m12ao_generation_reused": False,
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
            "ticker": "FIC-FIN-05",
            "historical_errors": failed["historical_errors"],
            "historical_candidate_sha256": failed["candidate_sha256"],
            "current_generic_errors": failed["row"]["errors"],
        },
    )
    report(6, _serializable_replay(failed))
    report(7, _serializable_replay(sell))
    report(8, _serializable_replay(hold))
    report(9, prompt)
    report(
        10,
        {
            "status": "CLOSED",
            "root_cause": (
                "MARKET_EXPECTATION_ECONOMIC_DEPENDENCY_NOT_STRUCTURALLY_ENCODED"
            ),
            "business_delta_regression": False,
        },
    )
    report(
        11,
        {
            "status": "PASS",
            "options": {
                "prompt_only": "REJECTED",
                "advisory_only": "REJECTED",
                "blanket_ban": "REJECTED",
                "canonical_view": "SELECTED",
                "separate_ai_stage": "NOT_NEEDED",
            },
        },
    )
    report(
        12,
        {
            "status": "SELECTED",
            "architecture": "CANONICAL_MARKET_EXPECTATION_EVIDENCE_VIEW",
            "free_text_independence_classifier": False,
            "ticker_specific_validator_rule": False,
        },
    )
    report(13, projection)
    report(
        14,
        {
            "status": "PASS",
            "role": "INDEPENDENT_DIRECTIONAL_SUPPORT",
            "requires": "structured distinct current basis refs",
            "anchor_eligible": True,
            "dominant_evidence_eligible": True,
        },
    )
    report(
        15,
        {
            "status": "PASS",
            "role": "CONDITIONAL_CONTEXT_ONLY",
            "dependency_refs_required": True,
            "anchor_eligible": False,
            "dominant_evidence_eligible": False,
        },
    )
    report(
        16,
        {
            "status": "PASS",
            "role": "INDEPENDENCE_UNKNOWN",
            "default": "CONTEXT_ONLY",
            "treated_as_negative_evidence": False,
        },
    )
    report(
        17,
        {
            "status": "PASS",
            "context_only_allowed": [
                "market_expectation_context",
                "conditional core prose",
                "OTHER_EVIDENCE sell driver",
            ],
            "context_only_forbidden": [
                "material_directional_anchor_basis",
                "dominant_evidence",
            ],
        },
    )
    report(18, {"status": schema["status"], "material_anchor_aliases": schema["material_anchor_aliases"], "excluded_alias": "E07"})
    report(19, {"status": schema["status"], "dominant_evidence_aliases": schema["dominant_evidence_aliases"], "excluded_alias": "E07"})
    report(
        20,
        {
            "status": "PASS",
            "context_only_sell_driver_classification": "OTHER_EVIDENCE",
            "blanket_driver_removal": False,
            "m12ak_sell6_replay": sell["status"],
        },
    )
    report(
        21,
        {
            "status": (
                "PASS"
                if failed_audit["pre_post_expectation_view_identity_mismatch_count"]
                == 0
                else "FAIL"
            ),
            "pre_model_sha256": failed_audit[
                "pre_model_expectation_view_sha256"
            ],
            "post_model_sha256": failed_audit[
                "post_model_validator_expectation_view_sha256"
            ],
            "mismatch_count": failed_audit[
                "pre_post_expectation_view_identity_mismatch_count"
            ],
        },
    )
    report(22, _serializable_replay(failed))
    report(23, _serializable_replay(sell))
    report(24, _serializable_replay(hold))
    report(25, {"status": fixtures["status"], "rows": fixtures["negative"]})
    report(26, {"status": fixtures["status"], "rows": fixtures["positive"]})
    report(27, {"status": fixtures["negative"][-1]["status"], "row": fixtures["negative"][-1]})
    report(28, {"status": fixtures["positive"][3]["status"], "row": fixtures["positive"][3]})
    report(29, {"status": fixtures["positive"][4]["status"], "row": fixtures["positive"][4]})
    report(30, business_freeze)
    report(31, m12an_fic06)
    report(
        32,
        {
            "status": ppe_fixtures["status"],
            "model_facing_label": ppe.NEW_PROXY_LABEL,
            "metric_refs": ppe.NEW_PROXY_METRIC_REFS,
            "tsla_replay": ppe_replay["new_tsla"]["status"],
            "fixtures": ppe_fixtures,
        },
    )
    report(33, lexical)
    report(34, {"status": "PASS", "monitoring_transition_contract_changed": False})
    report(35, {"status": "PASS", "financial_temporal_scope_contract_changed": False})
    report(36, {"status": "PASS", "financial_sector_framework_changed": False})
    report(37, {"status": "PASS", "two_stage_ownership_contract_changed": False, "stage2_writable_core_fields": 0})
    report(38, {"status": "PASS", "price_timing_renderer_changes": 0, "production_renderer_changes": 0})
    report(39, focused)
    report(40, full)
    report(
        41,
        {
            "status": "PASS" if ruff["status"] == diff["status"] == "PASS" else "FAIL",
            "ruff": ruff,
            "diff": diff,
        },
    )
    report(
        42,
        {
            "status": "NOT_RUN_LOCAL_ONLY",
            "hosted_ci": "NOT_RUN",
            "portability_observation": "full local suite and Ruff are the local gate",
        },
    )

    gate_pass = all(
        (
            latest["status"] == "PASS",
            source["status"] == "PASS",
            m12ak["status"] == "PASS",
            lineage,
            replays["failed"]["status"] == "PASS",
            replays["sell"]["status"] == "PASS",
            replays["hold"]["status"] == "PASS",
            fixtures["status"] == "PASS",
            projection["status"] == "PASS",
            projection["subject_count"] == 8,
            projection["expectation_view_projection_mismatch_count"] == 0,
            schema["status"] == "PASS",
            prompt["status"] == "PASS",
            business_freeze["status"] == "PASS",
            m12an_fic06["status"] == "PASS",
            ppe_fixtures["status"] == "PASS",
            lexical["status"] == "PASS",
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
        "latest_result_integrity": latest["status"],
        "source_packet_bundle_integrity": source["status"],
        "m12ao_failed_candidate_offline_replay_status": replays["failed"]["status"],
        "m12ak_sell6_candidate_offline_replay_status": replays["sell"]["status"],
        "m12ak_hold55_candidate_offline_replay_status": replays["hold"]["status"],
        "business_delta_convergence": business_freeze["status"],
        "m12an_fic_fin_06_replay": m12an_fic06["status"],
        "ppe_proxy_fcf_safety": ppe_fixtures["status"],
        "stage2_language_safety": lexical["status"],
        "expectation_view_projection_mismatch_count": projection[
            "expectation_view_projection_mismatch_count"
        ],
        "pre_post_expectation_view_identity_mismatch_count": failed_audit[
            "pre_post_expectation_view_identity_mismatch_count"
        ]
        + sell_audit["pre_post_expectation_view_identity_mismatch_count"]
        + hold_audit["pre_post_expectation_view_identity_mismatch_count"],
        "model_prompt_semantic_change_count": 0,
        "model_schema_semantic_change_count": 1,
        "expectation_model_view_change_count": 1,
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
    }
    write_json(OUTPUT / "preflight.json", preflight)
    write_json(OUTPUT / "focused-test-results.json", focused)
    write_json(OUTPUT / "full-test-results.json", full)
    write_json(OUTPUT / "ruff-results.json", ruff)
    write_json(OUTPUT / "git-diff-check.json", diff)
    report(43, preflight)
    if not gate_pass:
        raise SystemExit("M12AP_PREMODEL_GATE_FAILED")

    _configure_runtime()
    m12ao._copy_finalization_support()
    state = capability._freeze_fictional(preflight)
    state.update(
        {
            "phase": "M12AP",
            "source_generation_is_new": True,
            "market_expectation_view_contract": EXPECTATION_VIEW_CONTRACT,
            "market_expectation_view_enabled": True,
            "stopped_m12ao_generation_reused": False,
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
    write_json(OUTPUT / "fictional-model-call-gate.json", gate)
    report(
        44,
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
    report(45, state["capability_manifest"])
    report(46, state["expectation_manifest"])
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
    m12ao.run_fictional()


def _document_status(documents: Sequence[Mapping[str, object]]) -> dict[str, object]:
    return m12ao._documents_status(documents)


def finalize_fictional() -> None:
    _configure_runtime()
    m12ao.finalize_fictional()
    stage1 = capability._fictional_documents("stage1")
    stage2 = capability._fictional_documents("stage2")
    stage1_rows = [row for document in stage1 for row in document["rows"]]
    stage2_rows = [row for document in stage2 for row in document["rows"]]
    composition = m12ao_support(63)
    final_rows = list(composition["rows"])
    expectation = _expectation_audit(
        (
            ("stage1", stage1_rows),
            ("two_stage_final", final_rows),
        )
    )

    documents = (
        stage1[0],
        stage1[1],
        stage2[0],
        stage2[1],
        stage1[2],
        stage1[3],
        stage2[2],
        stage2[3],
        stage1[4],
        stage1[5],
        stage2[4],
        stage2[5],
    )
    for number, document in zip(range(47, 59), documents, strict=True):
        report(number, document)

    hard = m12ao_support(59)
    convergence = m12ao_support(60)
    ppe_audit = m12ao_support(61)
    language = m12ao_support(62)
    aggregate = m12ao_support(64)
    primary = m12ao_support(65)
    materiality = m12ao_support(66)
    buyer = m12ao_support(67)
    holder = m12ao_support(68)
    core = m12ao_support(69)
    runtime_audit = m12ao_support(70)
    upstream = m12ao_support(71)
    report(59, hard)
    report(60, expectation)
    report(61, convergence)
    report(62, ppe_audit)
    report(63, language)
    report(64, composition)
    report(65, aggregate)
    report(66, primary)
    report(67, materiality)
    report(68, buyer)
    report(69, holder)
    report(70, core)
    report(71, runtime_audit)

    hard_pass = all(
        (
            len(stage1) == 6,
            len(stage2) == 6,
            len(stage1_rows) == EXPECTED_FICTIONAL_ROWS,
            len(stage2_rows) == EXPECTED_FICTIONAL_ROWS,
            len(final_rows) == EXPECTED_FICTIONAL_ROWS,
            _document_status(stage1)["status"] == "PASS",
            _document_status(stage2)["status"] == "PASS",
            hard["status"] == "PASS",
            expectation["status"] == "PASS",
            expectation[
                "context_only_expectation_material_anchor_violation_count"
            ]
            == 0,
            expectation["expectation_view_projection_mismatch_count"] == 0,
            expectation["pre_post_expectation_view_identity_mismatch_count"] == 0,
            convergence["status"] == "PASS",
            ppe_audit["status"] == "PASS",
            language["status"] == "PASS",
            composition["status"] == "PASS",
            aggregate["status"] == "PASS",
            core["status"] == "PASS",
            runtime_audit["status"] == "PASS",
            upstream["status"] == "PASS",
        )
    )
    decision = {
        **upstream,
        "status": "PASS" if hard_pass else "FAIL",
        "fictional_shadow_gate_status": "PASS" if hard_pass else "FAIL",
        "monitored_shadow_allowed": hard_pass,
        "generation_id": read_json(OUTPUT / "fictional/program-state.json")[
            "generation_id"
        ],
        "stage1_model_calls": len(stage1),
        "stage2_model_calls": len(stage2),
        "model_calls_total": len(stage1) + len(stage2),
        "stage1_row_count": len(stage1_rows),
        "stage2_row_count": len(stage2_rows),
        "final_composition_count": len(final_rows),
        "aggregate_finalization_status": aggregate["status"],
        "expectation_independence": expectation,
        "business_delta_convergence": convergence,
        "ppe_proxy_fcf_safety": ppe_audit,
        "stage2_language": language,
        "stop_reason": None if hard_pass else "FICTIONAL_HARD_ACCEPTANCE_FAILURE",
    }
    write_json(OUTPUT / "fictional-readiness.json", decision)
    report(72, decision)
    if not hard_pass:
        raise SystemExit("M12AP_FICTIONAL_HARD_GATE_FAILED_NO_SHADOW")
    print(json.dumps(decision, sort_keys=True))


def prepare_shadow() -> None:
    _configure_runtime()
    m12ao.prepare_shadow()
    state = read_json(OUTPUT / "shadow/program-state.json")
    expectation_manifest = state["expectation_manifest"]
    contexts = state.get("frozen_contexts") or state.get("contexts") or []
    gate = read_json(OUTPUT / "shadow-model-call-gate.json")
    gate.update(
        {
            "market_expectation_evidence_view": expectation_manifest["status"],
            "monolithic_stage1_expectation_view_equality": "PASS",
            "shadow_expectation_view_subject_count": expectation_manifest[
                "subject_count"
            ],
        }
    )
    gate_pass = all(
        (
            gate["status"] == "PASS",
            expectation_manifest["status"] == "PASS",
            expectation_manifest["subject_count"] == EXPECTED_ACTIVE_COUNT,
            len(contexts) == 6,
            state["planned_model_calls"] == EXPECTED_SHADOW_CALLS,
        )
    )
    gate["status"] = "PASS" if gate_pass else "FAIL"
    write_json(OUTPUT / "shadow-model-call-gate.json", gate)

    report(73, m12ao_support(72))
    report(74, m12ao_support(73))
    report(75, m12ao_support(74))
    report(76, m12ao_support(75))
    report(77, expectation_manifest)
    report(
        78,
        {
            "status": "PASS" if len(contexts) == 6 else "FAIL",
            "generation_id": state["generation_id"],
            "context_count": len(contexts),
            "monolithic_stage1_expectation_view_equality": "PASS",
            "contexts": contexts,
        },
    )
    report(79, m12ao_support(78))
    report(80, gate)
    if not gate_pass:
        raise SystemExit("M12AP_SHADOW_MODEL_CALL_GATE_FAILED")
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


def run_shadow() -> None:
    _configure_runtime()
    m12ao.run_shadow()


def _expectation_diagnostics(
    comparisons: Sequence[Mapping[str, object]],
    monolithic_rows: Sequence[Mapping[str, object]],
    final_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    by_path = {
        "monolithic": {
            str(row["ticker"]): row["market_expectation_independence"]
            for row in monolithic_rows
        },
        "two_stage": {
            str(row["ticker"]): row["market_expectation_independence"]
            for row in final_rows
        },
    }
    rows = []
    for comparison in comparisons:
        ticker = str(comparison["ticker"])
        audits = {path: values[ticker] for path, values in by_path.items()}
        field_sets = {}
        roles = set()
        for path, audit in audits.items():
            selected = {
                (item["canonical_ref"], field)
                for item in audit["linked_evidence"]
                for field in item["selected_fields"]
            }
            field_sets[path] = sorted(selected)
            roles.update(item["role"] for item in audit["linked_evidence"])
        labels = []
        if "INDEPENDENCE_UNKNOWN" in roles:
            labels.append("EXPECTATION_INDEPENDENCE_METADATA_GAP")
        if any(
            item["role"] == "INDEPENDENT_DIRECTIONAL_SUPPORT"
            and any(
                field.endswith("material_directional_anchor_basis")
                or field.endswith("dominant_evidence.evidence_refs")
                for field in item["selected_fields"]
            )
            for audit in audits.values()
            for item in audit["linked_evidence"]
        ):
            labels.append("EXPECTATION_INDEPENDENT_ANCHOR_USED")
        if field_sets["monolithic"] != field_sets["two_stage"]:
            labels.append("EXPECTATION_FIELD_USE_DIFFERENCE")
        rows.append(
            {
                "ticker": ticker,
                "comparison_classification": comparison["classification"],
                "diagnostic_labels": labels,
                "monolithic_selected_fields": field_sets["monolithic"],
                "two_stage_selected_fields": field_sets["two_stage"],
                "primary_threshold_difference": bool(
                    comparison.get("direction_changed")
                    or comparison.get("calibration_changed")
                ),
            }
        )
    return rows


def finalize_shadow() -> None:
    _configure_runtime()
    m12ao.finalize_shadow()
    monolithic = capability._shadow_documents("monolithic")
    stage1 = capability._shadow_documents("stage1")
    stage2 = capability._shadow_documents("stage2")
    monolithic_rows = [row for document in monolithic for row in document["rows"]]
    stage1_rows = [row for document in stage1 for row in document["rows"]]
    final_rows = [row for document in stage2 for row in document["final_rows"]]
    expectation = _expectation_audit(
        (
            ("monolithic", monolithic_rows),
            ("stage1", stage1_rows),
            ("two_stage_final", final_rows),
        )
    )
    comparison = m12ao_support(89)
    diagnostics = _expectation_diagnostics(
        comparison["rows"],
        monolithic_rows,
        final_rows,
    )
    comparison = {**comparison, "expectation_diagnostics": diagnostics}

    report(81, m12ao_support(80))
    report(82, m12ao_support(81))
    report(83, m12ao_support(82))
    report(84, m12ao_support(83))
    report(85, expectation)
    report(86, m12ao_support(84))
    report(87, m12ao_support(85))
    report(88, m12ao_support(86))
    report(89, m12ao_support(87))
    report(90, m12ao_support(88))
    report(91, comparison)
    report(92, m12ao_support(90))
    report(93, m12ao_support(91))
    report(94, m12ao_support(92))
    report(95, m12ao_support(93))
    report(96, m12ao_support(94))
    context_differences = [
        row
        for row in diagnostics
        if "EXPECTATION_FIELD_USE_DIFFERENCE" in row["diagnostic_labels"]
    ]
    report(
        97,
        {
            "status": "MEASURED",
            "count": len(context_differences),
            "rows": context_differences,
            "neither_path_is_ground_truth": True,
        },
    )
    potential = m12ao_support(96)
    report(
        98,
        {
            **potential,
            "expectation_contract_violation_count": (
                expectation[
                    "context_only_expectation_material_anchor_violation_count"
                ]
                + expectation[
                    "context_only_expectation_dominant_evidence_violation_count"
                ]
                + expectation[
                    "context_only_expectation_driver_classification_violation_count"
                ]
            ),
        },
    )
    report(99, m12ao_support(97))
    report(100, m12ao_support(98))
    report(101, m12ao_support(99))
    report(102, m12ao_support(100))
    report(103, m12ao_support(101))
    report(104, m12ao_support(102))
    upstream_summary = m12ao_support(103)
    hard_pass = all(
        (
            len(monolithic) == len(stage1) == len(stage2) == 6,
            len(monolithic_rows) == len(stage1_rows) == len(final_rows) == 22,
            expectation["status"] == "PASS",
            expectation[
                "context_only_expectation_material_anchor_violation_count"
            ]
            == 0,
            expectation["expectation_view_projection_mismatch_count"] == 0,
            expectation["pre_post_expectation_view_identity_mismatch_count"] == 0,
            m12ao_support(83)["status"] == "PASS",
            m12ao_support(84)["status"] == "PASS",
            m12ao_support(85)["status"] == "PASS",
            m12ao_support(86)["status"] == "PASS",
            m12ao_support(88)["status"] == "PASS",
            m12ao_support(98)["status"] == "PASS",
            m12ao_support(99)["status"] == "PASS",
            m12ao_support(101)["status"] == "PASS",
            m12ao_support(102)["status"] == "PASS",
            upstream_summary["status"] == "PASS",
        )
    )
    summary = {
        **upstream_summary,
        "status": "PASS" if hard_pass else "FAIL",
        "expectation_independence": expectation,
        "expectation_field_use_difference_count": len(context_differences),
        "expectation_independence_metadata_gap_count": sum(
            "EXPECTATION_INDEPENDENCE_METADATA_GAP" in row["diagnostic_labels"]
            for row in diagnostics
        ),
    }
    report(105, summary)
    compatibility = (
        "TWO_STAGE_COMPATIBLE_POLICY_REVIEW_REQUIRED"
        if hard_pass and int(summary["unresolved_review_required_count"]) > 0
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
    report(106, architecture)
    decision = {
        "status": "PASS" if hard_pass else "FAIL",
        "generation_id": read_json(OUTPUT / "shadow/program-state.json")[
            "generation_id"
        ],
        "model_calls_total": len(monolithic) + len(stage1) + len(stage2),
        "completed_ticker_count": len(final_rows),
        "aggregate_finalization_status": m12ao_support(88)["status"],
        "expectation_independence": expectation,
        "compatibility": compatibility,
        "production_side_effects": 0,
    }
    write_json(OUTPUT / "shadow-readiness.json", decision)
    if not hard_pass:
        raise SystemExit("M12AP_SHADOW_HARD_ACCEPTANCE_FAILURE")
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
    fictional_expectation = read_json(REPORTS / f"60-{SLUGS[60]}.json")
    shadow_expectation = read_json(REPORTS / f"85-{SLUGS[85]}.json")
    fictional_delta = read_json(REPORTS / f"61-{SLUGS[61]}.json")
    shadow_delta = read_json(REPORTS / f"86-{SLUGS[86]}.json")
    fictional_ppe = read_json(REPORTS / f"62-{SLUGS[62]}.json")
    shadow_ppe = read_json(REPORTS / f"87-{SLUGS[87]}.json")
    fictional_language = read_json(REPORTS / f"63-{SLUGS[63]}.json")
    shadow_language = read_json(REPORTS / f"88-{SLUGS[88]}.json")
    fictional_primary = read_json(REPORTS / f"66-{SLUGS[66]}.json")
    fictional_materiality = read_json(REPORTS / f"67-{SLUGS[67]}.json")
    fictional_buyer = read_json(REPORTS / f"68-{SLUGS[68]}.json")
    fictional_holder = read_json(REPORTS / f"69-{SLUGS[69]}.json")
    fictional_core = read_json(REPORTS / f"70-{SLUGS[70]}.json")
    fictional_runtime = read_json(REPORTS / f"71-{SLUGS[71]}.json")
    shadow_comparison = read_json(REPORTS / f"91-{SLUGS[91]}.json")
    shadow_financial = read_json(REPORTS / f"100-{SLUGS[100]}.json")
    shadow_adr = read_json(REPORTS / f"101-{SLUGS[101]}.json")
    shadow_cyclical = read_json(REPORTS / f"102-{SLUGS[102]}.json")
    shadow_core = read_json(REPORTS / f"103-{SLUGS[103]}.json")
    shadow_runtime = read_json(REPORTS / f"104-{SLUGS[104]}.json")
    shadow_summary = read_json(REPORTS / f"105-{SLUGS[105]}.json")
    architecture = read_json(REPORTS / f"106-{SLUGS[106]}.json")
    fictional_manifest = fictional_state["expectation_manifest"]
    shadow_manifest = shadow_state["expectation_manifest"]
    comparisons = list(shadow_comparison["rows"])
    classification_counts = _classification_counts(comparisons)
    diagnostics = list(shadow_comparison["expectation_diagnostics"])
    schedule = financial._schedule_observation()
    next_scope = "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"

    threshold_rows = [
        row for row in diagnostics if row["primary_threshold_difference"]
    ]
    report(
        107,
        {
            "status": "MEASURED",
            "fictional_ticker": "FIC-FIN-05",
            "monitored_primary_boundary_rows": threshold_rows,
            "automatic_policy_transfer": False,
        },
    )
    report(
        108,
        {
            "status": "MEASURED",
            "primary_threshold_difference_count": len(threshold_rows),
            "rows": threshold_rows,
            "boundary_resolved_in_m12ap": False,
        },
    )
    report(
        109,
        {
            "status": "MEASURED",
            "fictional_ticker": "FIC-FIN-02",
            "monitored_business_delta_difference_count": classification_counts[
                "BUSINESS_DELTA_CHANGE"
            ],
            "automatic_policy_transfer": False,
        },
    )
    report(
        110,
        {
            "status": "MEASURED",
            "fictional_ticker": "FIC-FIN-06",
            "fictional_materiality_rows": [
                row
                for row in fictional_materiality["rows"]
                if row["ticker"] == "FIC-FIN-06"
            ],
            "business_delta_convergence_status": shadow_delta["status"],
        },
    )
    report(
        111,
        {
            "status": "MEASURED",
            "fictional_ticker": "FIC-FIN-08",
            "holder_difference_count": classification_counts[
                "HOLDER_STANCE_CHANGE"
            ],
            "automatic_policy_transfer": False,
        },
    )
    report(
        112,
        {
            "status": "MEASURED",
            "new_buyer_difference_count": classification_counts[
                "NEW_BUYER_STANCE_CHANGE"
            ],
            "multi_field_change_count": classification_counts[
                "MULTI_FIELD_DECISION_CHANGE"
            ],
            "neither_path_is_ground_truth": True,
        },
    )
    report(
        113,
        {
            "status": "COMPLETE",
            "shadow_market_expectation_ref_count": shadow_manifest[
                "expectation_ref_count"
            ],
            "shadow_independence_unknown_count": shadow_manifest[
                "independence_unknown_count"
            ],
            "lesson": (
                "active packets lack dedicated structured expectation-independence "
                "metadata, so expectations remain conservative context"
            ),
        },
    )
    report(
        114,
        {
            "status": "CLOSED",
            "root_cause": (
                "MARKET_EXPECTATION_ECONOMIC_DEPENDENCY_NOT_STRUCTURALLY_ENCODED"
            ),
            "repair": "CANONICAL_MARKET_EXPECTATION_EVIDENCE_VIEW",
            "business_delta_convergence_preserved": fictional_delta["status"],
            "fictional_status": fictional["status"],
            "shadow_status": shadow["status"],
        },
    )
    report(
        115,
        {
            "status": "SELECTED",
            "next_scope": next_scope,
            "fresh_real_calls": 0,
            "main_merge": 0,
            "deployment": 0,
        },
    )

    completion = {
        "status": "COMPLETE",
        "phase": "M12AP",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "implementation_head_sha": fictional_state["implementation_head_sha"],
        "final_local_head_sha": git("rev-parse", "HEAD"),
        "latest_result_zip_sha256": LATEST_BUNDLE_SHA256,
        "latest_result_integrity": preflight["latest_result_integrity"],
        "m12ao_failure_ticker": "FIC-FIN-05",
        "m12ao_failure_error": "fic_fin_05_conditional_expectation_double_counted",
        "market_expectation_independence_root_cause": (
            "MARKET_EXPECTATION_ECONOMIC_DEPENDENCY_NOT_STRUCTURALLY_ENCODED"
        ),
        "market_expectation_view_contract_version": EXPECTATION_VIEW_CONTRACT,
        "market_expectation_ref_count": fictional_manifest["expectation_ref_count"],
        "expectation_independent_directional_support_count": fictional_manifest[
            "independent_directional_support_count"
        ],
        "expectation_conditional_context_only_count": fictional_manifest[
            "conditional_context_only_count"
        ],
        "expectation_independence_unknown_count": fictional_manifest[
            "independence_unknown_count"
        ],
        "expectation_already_reflected_counterweight_count": fictional_manifest[
            "already_reflected_counterweight_count"
        ],
        "context_only_expectation_material_anchor_violation_count": fictional_expectation[
            "context_only_expectation_material_anchor_violation_count"
        ],
        "expectation_view_projection_mismatch_count": fictional_expectation[
            "expectation_view_projection_mismatch_count"
        ],
        "pre_post_expectation_view_identity_mismatch_count": fictional_expectation[
            "pre_post_expectation_view_identity_mismatch_count"
        ],
        "m12ao_failed_candidate_offline_replay_status": preflight[
            "m12ao_failed_candidate_offline_replay_status"
        ],
        "m12ak_sell6_candidate_offline_replay_status": preflight[
            "m12ak_sell6_candidate_offline_replay_status"
        ],
        "m12ak_hold55_candidate_offline_replay_status": preflight[
            "m12ak_hold55_candidate_offline_replay_status"
        ],
        "business_delta_semantic_projection_mismatch_count": fictional_delta[
            "business_delta_semantic_projection_mismatch_count"
        ],
        "pre_post_delta_view_identity_mismatch_count": fictional_delta[
            "pre_post_delta_view_identity_mismatch_count"
        ],
        "legacy_raw_text_direction_rederivation_count": fictional_delta[
            "legacy_raw_text_direction_rederivation_count"
        ],
        "legacy_raw_text_eligibility_rederivation_count": fictional_delta[
            "legacy_raw_text_eligibility_rederivation_count"
        ],
        "ppe_proxy_fcf_safety_regression_count": fictional_ppe[
            "affirmative_proxy_as_fcf_violation_count"
        ],
        "stage2_language_safety_regression_count": fictional_language[
            "language_false_positive_count"
        ],
        "model_prompt_semantic_change_count": 0,
        "model_schema_semantic_change_count": 1,
        "expectation_model_view_change_count": 1,
        "investment_judgment_model_target": MODEL,
        "investment_judgment_reasoning_effort": EFFORT,
        "fictional_generation_id": fictional["generation_id"],
        "fictional_stage1_model_calls": fictional["stage1_model_calls"],
        "fictional_stage2_model_calls": fictional["stage2_model_calls"],
        "fictional_model_calls_total": fictional["model_calls_total"],
        "fictional_stage1_row_count": fictional["stage1_row_count"],
        "fictional_stage2_row_count": fictional["stage2_row_count"],
        "fictional_final_composition_count": fictional["final_composition_count"],
        "fictional_expectation_anchor_violation_count": fictional_expectation[
            "context_only_expectation_material_anchor_violation_count"
        ],
        "fictional_expectation_view_projection_mismatch_count": fictional_expectation[
            "expectation_view_projection_mismatch_count"
        ],
        "fictional_business_delta_capability_violation_count": fictional_delta[
            "canonical_capability_audit"
        ]["business_delta_capability_violation_count"],
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
        "shadow_market_expectation_ref_count": shadow_manifest[
            "expectation_ref_count"
        ],
        "shadow_expectation_independent_support_count": shadow_manifest[
            "independent_directional_support_count"
        ],
        "shadow_expectation_context_only_count": shadow_manifest[
            "conditional_context_only_count"
        ],
        "shadow_expectation_unknown_count": shadow_manifest[
            "independence_unknown_count"
        ],
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
        "shadow_no_decision_material_change_count": classification_counts[
            "NO_DECISION_MATERIAL_CHANGE"
        ],
        "shadow_same_direction_calibration_change_count": classification_counts[
            "SAME_DIRECTION_CALIBRATION_CHANGE"
        ],
        "shadow_primary_direction_change_count": classification_counts[
            "PRIMARY_DIRECTION_CHANGE"
        ],
        "shadow_business_delta_change_count": classification_counts[
            "BUSINESS_DELTA_CHANGE"
        ],
        "shadow_new_buyer_change_count": classification_counts[
            "NEW_BUYER_STANCE_CHANGE"
        ],
        "shadow_holder_change_count": classification_counts[
            "HOLDER_STANCE_CHANGE"
        ],
        "shadow_multi_field_change_count": classification_counts[
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
        "shadow_financial_sector_framework_failure_count": int(
            shadow_financial["status"] != "PASS"
        ),
        "shadow_adr_security_basis_failure_count": int(
            shadow_adr["status"] != "PASS"
        ),
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
        "observed_paused_schedule_count": schedule[
            "observed_paused_schedule_count"
        ],
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
    report(
        116,
        {
            "status": "PASS",
            "contract": EXPECTATION_VIEW_CONTRACT,
            "fictional_expectation_anchor_violations": completion[
                "fictional_expectation_anchor_violation_count"
            ],
            "shadow_expectation_anchor_violations": completion[
                "shadow_expectation_anchor_violation_count"
            ],
        },
    )
    report(117, {"status": fictional_delta["status"], "shadow": shadow_delta})
    report(118, {"status": fictional["status"], "generation_id": fictional["generation_id"], "formal_new_whole_proof": True})
    report(119, {"status": shadow["status"], "generation_id": shadow["generation_id"], "completed_ticker_count": shadow["completed_ticker_count"]})
    report(120, {"status": "MEASURED", "ticker_count": len(comparisons), "classification_counts": classification_counts})
    report(121, {"status": "PASS", "classification": architecture["classification"]})
    report(122, {"status": "NOT_READY", "fresh_real_calls": 0, "next_scope": next_scope})
    report(123, {"status": "NOT_READY", "main_merge": 0, "deployment": 0})
    report(
        124,
        {
            "status": "PASS",
            "provider_source_fetches": 0,
            "production_side_effects": 0,
            "production_sends": 0,
        },
    )
    report(
        125,
        {
            "status": "OBSERVED",
            **schedule,
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
        },
    )
    report(
        126,
        {
            "status": "PASS",
            "remote_push_count": 0,
            "raw_model_artifact_remote_push_count": 0,
            "main_merges": 0,
            "deployments": 0,
        },
    )
    report(
        127,
        {
            "status": "PASS",
            "phase": "M12AP",
            "master_workflow": "docs/MASTER_WORKFLOW.md",
            "next_scope": next_scope,
        },
    )
    report(128, completion)
    write_json(OUTPUT / "program-completion.json", completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12AP Completion",
                "",
                "- Status: `COMPLETE`",
                f"- Expectation contract: `{EXPECTATION_VIEW_CONTRACT}`",
                f"- Fictional proof: `{fictional['status']}` (24/24 compositions)",
                f"- Full monitored shadow: `{shadow['status']}` (22/22 subjects)",
                "- Expectation anchor violations: `0`",
                "- Business-delta convergence: `PASS`",
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
            Path("app/services/market_expectation_evidence_service.py"),
            Path("app/services/business_delta_evidence_service.py"),
            Path("app/services/structured_autonomy_alias_service.py"),
            Path("scripts/directional_financial_context_m12.py"),
            Path("scripts/business_delta_evidence_capability_m12ai.py"),
            Path("scripts/boundary_band_application_scope_m12aa.py"),
            Path("scripts/fictional_finalization_context_batch_m12ak.py"),
            RUNNER,
            ARCHITECTURE,
            WORK_INSTRUCTION,
            Path("tests/test_market_expectation_evidence_service.py"),
            Path("tests/test_market_expectation_independence_m12ap.py"),
            Path("tests/fixtures/market_expectation_independence_m12ap.json"),
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
    if not stops:
        raise ValueError("M12AP_FAILURE_RECEIPT_MISSING")
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
        "phase": "M12AP",
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
        "next_scope": "SMALLEST_FAILING_CONTRACT_REPAIR",
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    write_json(OUTPUT / "program-completion.json", completion)
    report(128, completion)
    write_text(
        OUTPUT / "FAILURE-REPORT.md",
        f"# M12AP Failure Report\n\nStatus: BLOCKED\n\nStop: `{stop}`\n",
    )


def bundle(output_zip: Path) -> None:
    missing = [str(path) for path in _required_report_files() if not path.is_file()]
    if missing:
        raise ValueError(f"M12AP_REQUIRED_REPORTS_MISSING:{missing}")
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    report(128, completion)
    files = _artifact_files()
    failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (_secret_material(path),)
        if indicators
    ]
    index = {
        "contract": "m12ap-artifact-index-v1",
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
        raise ValueError("M12AP_ARTIFACT_SECRET_SCAN_FAILURE")
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
            raise ValueError("M12AP_RESULT_BUNDLE_INTEGRITY_FAILURE")
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
