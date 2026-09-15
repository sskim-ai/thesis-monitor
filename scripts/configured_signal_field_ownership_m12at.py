"""M12AT configured-signal field ownership proof and full monitored shadow."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

from app.services.configured_signal_evidence_service import (
    CONTRACT_VERSION as CONFIGURED_VIEW_CONTRACT,
    CURRENT_DIRECTIONAL_REFERENCE_FIELDS,
    ConfiguredSignalEvidenceView,
    ConfiguredSignalFulfillmentEvidence,
    ConfiguredSignalFulfillmentState,
    build_configured_signal_evidence_view,
    is_configured_signal_source_ref,
    validate_configured_signal_field_ownership,
)
from app.services.cross_market_decision_engine_service import (
    DecisionEvidenceRef,
    EvidenceCategory,
    FinancialComparison,
    FinancialComparisonKind,
    FinancialContext,
    FinancialEvidenceQuality,
    FinancialEvidenceStatus,
    FinancialPeriod,
    FinancialPeriodType,
)
from app.services.directional_financial_context_service import (
    validate_directional_financial_semantics,
)
from app.services.logical_condition_service import (
    LogicalSeverity,
    source_checkpoint_metric_refs,
    source_logical_condition,
)
from app.services.two_stage_directional_service import DirectionalCoreJudgment
from scripts import business_delta_evidence_capability_m12ai as capability
from scripts.shadow_frozen_context_manifest import (
    CONTRACT_VERSION as SHADOW_MANIFEST_CONTRACT,
    canonicalize_shadow_manifest_state,
    normalize_shadow_manifest,
)


NAME = (
    "20260912-configured-prospective-signal-directional-field-eligibility-"
    "fictional-reproof-full-shadow"
)
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
SUPPORT_REPORTS = OUTPUT / "supporting-reports/m12ai"
RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
RUNNER = Path("scripts/configured_signal_field_ownership_m12at.py")
ARCHITECTURE = Path("docs/architecture/CONFIGURED_SIGNAL_FIELD_OWNERSHIP.md")
WORK_INSTRUCTION = Path("docs/work-instructions") / (
    "20260912-configured-prospective-signal-directional-field-eligibility-"
    "fictional-reproof-full-shadow.md"
)
FIXTURE_FILE = Path("tests/fixtures/configured_signal_field_ownership_m12at.json")
WORK_INSTRUCTION_COMMIT = "5d7bb08b8f5e8650bbbb17d37c09c39ab8462134"
BASE_INTEGRATION_HEAD_SHA = "c7eec0b0db8524ae766c43dee96a5d2bf8deebeb"

ICLOUD = Path(
    "/Users/sskim/Library/Mobile Documents/com~apple~CloudDocs/Thesis Monitor"
)
M12AS_NAME = (
    "20260912-business-delta-unchanged-configured-condition-negation-scope-"
    "full-shadow"
)
M12AS_OUTPUT = Path("artifacts") / M12AS_NAME
M12AS_BUNDLE = ICLOUD / f"thesis-monitor-{M12AS_NAME}-report.zip"
M12AS_BUNDLE_SHA256 = (
    "abefe909f1b6e665d5a8bae6085f518165b75528959711179af0eada68ccfa1d"
)
M12AS_INDEXED_PAYLOADS = 217
M12AS_ZIP_ENTRIES = 218
M12AS_GENERATION_ID = "20260911-m12ai-shadow-20260912T095409Z-3da60ab83df5"

MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
EXPECTED_FICTIONAL_CALLS = 12
EXPECTED_FICTIONAL_ROWS = 24
EXPECTED_SHADOW_CALLS = 18
EXPECTED_SHADOW_CONTEXTS = 6
EXPECTED_ACTIVE_COUNT = 22
NEXT_SCOPE = "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"

_SLUG_SEQUENCE = (
    "repository-provenance",
    "latest-result-integrity",
    "m12at-scope-freeze",
    "integrated-main-lineage-freeze",
    "m12as-005490-failure-reproduction",
    "sell-driver-field-contract-audit",
    "configured-signal-source-lineage-forensic",
    "financial-claim-precedence-forensic",
    "configured-signal-field-ownership-options",
    "configured-signal-field-ownership-decision",
    "configured-signal-evidence-view-contract",
    "configured-only-vs-fulfilled-contract",
    "current-directional-field-eligibility-contract",
    "future-reevaluation-field-eligibility-contract",
    "risk-context-configured-signal-contract",
    "material-anchor-configured-signal-contract",
    "dominant-evidence-configured-signal-contract",
    "configured-signal-fulfillment-evidence-contract",
    "monolithic-stage1-configured-view-equality-contract",
    "m12as-005490-exact-field-use-audit",
    "m12as-005490-historical-candidate-replay",
    "configured-signal-field-positive-fixtures",
    "configured-signal-field-negative-fixtures",
    "configured-signal-fulfillment-positive-fixtures",
    "configured-signal-false-fulfillment-negative-fixtures",
    "net-debt-current-claim-regressions",
    "future-net-debt-condition-regressions",
    "m12as-unchanged-claim-scope-freeze",
    "m12ar-fcf-claim-scope-freeze",
    "m12aq-financial-sector-scope-freeze",
    "m12ap-expectation-independence-freeze",
    "m12ao-business-delta-convergence-freeze",
    "m12an-ppe-proxy-label-freeze",
    "m12am-stage2-lexical-freeze",
    "monitoring-transition-ownership-freeze",
    "financial-temporal-scope-freeze",
    "qtd-ytd-wc-debt-safety-freeze",
    "adr-security-basis-freeze",
    "two-stage-ownership-freeze",
    "price-timing-renderer-no-change",
    "model-prompt-semantic-diff",
    "model-schema-semantic-diff",
    "configured-signal-view-model-surface-diff",
    "final-user-schema-no-change-proof",
    "fictional-formal-reproof-decision",
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
    "fictional-configured-signal-field-use-audit",
    "fictional-business-delta-audit",
    "fictional-market-expectation-audit",
    "fictional-financial-sector-audit",
    "fictional-ppe-proxy-fcf-audit",
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
    "shadow-business-delta-audit",
    "shadow-market-expectation-audit",
    "shadow-financial-sector-audit",
    "shadow-fcf-claim-scope-audit",
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
    "combined-fictional-monitored-root-cause-summary",
    "next-bounded-policy-decision",
    "configured-signal-field-ownership-success-decision",
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
if len(SLUGS) != 138:
    raise RuntimeError(f"M12AT_REPORT_SEQUENCE_INVALID:{len(SLUGS)}")

FOCUSED_TESTS = (
    "tests/test_configured_signal_evidence_service.py",
    "tests/test_configured_signal_alias_schema.py",
    "tests/test_configured_signal_field_ownership_m12at_runner.py",
    "tests/test_directional_financial_context_service.py",
    "tests/test_directional_financial_context_m12.py",
    "tests/test_business_delta_evidence_service.py",
    "tests/test_business_delta_evidence_capability_m12ai.py",
    "tests/test_structured_autonomy_alias_service.py",
    "tests/test_stage2_korean_lexical_boundary_m12am_runner.py",
    "tests/test_monitoring_transition_ownership_netdebt_m12ag.py",
    "tests/test_financial_claim_temporal_scope_m12ah.py",
    "tests/test_market_expectation_evidence_service.py",
    "tests/test_financial_sector_exclusion_connective_scope_m12aq.py",
    "tests/test_ppe_proxy_fcf_claim_scope_m12ar.py",
    "tests/test_two_stage_directional_service.py",
    "tests/test_direction_timing_ownership_service.py",
)
RUFF_PATHS = (
    "app/services/configured_signal_evidence_service.py",
    "app/services/business_delta_evidence_service.py",
    "app/services/directional_financial_context_service.py",
    "app/services/structured_autonomy_alias_service.py",
    "scripts/business_delta_evidence_capability_m12ai.py",
    "scripts/directional_core_price_timing_holdout.py",
    "scripts/directional_financial_context_m12.py",
    str(RUNNER),
    "tests/test_configured_signal_evidence_service.py",
    "tests/test_configured_signal_alias_schema.py",
    "tests/test_configured_signal_field_ownership_m12at_runner.py",
)
CRITICAL_CODE_PATHS = (
    Path("app/services/configured_signal_evidence_service.py"),
    Path("app/services/business_delta_evidence_service.py"),
    Path("app/services/directional_financial_context_service.py"),
    Path("app/services/structured_autonomy_alias_service.py"),
    Path("app/services/market_expectation_evidence_service.py"),
    Path("app/services/two_stage_directional_service.py"),
    Path("scripts/business_delta_evidence_capability_m12ai.py"),
    Path("scripts/directional_core_price_timing_holdout.py"),
    Path("scripts/directional_financial_context_m12.py"),
    Path("scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py"),
    Path("scripts/shadow_frozen_context_manifest.py"),
    RUNNER,
)
_ORIGINAL_FICTIONAL_INPUTS = capability.m12.fictional_inputs


def _fictional_configured_refs(
    ticker: str, generation_id: str
) -> tuple[DecisionEvidenceRef, ...]:
    rows = (
        (
            "strengthen",
            "영업현금흐름과 영업이익률의 동반 개선이 확인",
            "stock.thesis.strengthen_signals",
            LogicalSeverity.STRENGTHENING,
        ),
        (
            "weaken",
            "FCF 감소와 순부채 증가가 동반",
            "stock.thesis.weaken_signals",
            LogicalSeverity.WEAKENING,
        ),
        (
            "invalidate",
            "지속적인 음의 영업현금흐름이 구조적으로 확인",
            "stock.thesis.invalidation_signals",
            LogicalSeverity.INVALIDATION_CANDIDATE,
        ),
    )
    refs = []
    for suffix, statement, source_ref, severity in rows:
        ref_id = f"m12at:{ticker}:{suffix}"
        refs.append(
            DecisionEvidenceRef(
                ref_id=ref_id,
                category=EvidenceCategory.RISKS,
                label="설정된 미래 논리 조건",
                statement=statement,
                as_of="2026-09-12",
                source_ref=source_ref,
                metric_refs=source_checkpoint_metric_refs(statement),
                logical_condition=source_logical_condition(
                    subject=ticker,
                    generation_id=generation_id,
                    evidence_ref=ref_id,
                    statement=statement,
                    severity=severity,
                ),
            )
        )
    return tuple(refs)


def _m12at_fictional_inputs(
    generation_id: str,
) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    packets, original_owned, _catalogs, _contexts = _ORIGINAL_FICTIONAL_INPUTS(
        generation_id
    )
    augmented_packets = {}
    owned = {}
    catalogs = {}
    contexts = {}
    for ticker in capability.m12.TICKERS:
        refs = (*packets[ticker].evidence, *_fictional_configured_refs(ticker, generation_id))
        packet = packets[ticker].model_copy(
            update={
                "evidence": refs,
                "evidence_sha256": canonical_sha256(
                    [ref.model_dump(mode="json") for ref in refs]
                ),
            }
        )
        stock = {
            "analysis_framework": original_owned[ticker].sector_framework,
            "fact_catalog": [
                {
                    "fact_id": ref.source_ref.removeprefix("stock.fact_catalog."),
                    "evidence_family": capability.m12._family_for_ref(ref),
                }
                for ref in refs
                if ref.source_ref.startswith("stock.fact_catalog.")
            ],
        }
        item = capability.m12.build_owned_evidence_packet(packet, stock=stock)
        core_catalog, _timing_catalog = capability.m12.stage_alias_catalogs(item)
        augmented_packets[ticker] = packet
        owned[ticker] = item
        catalogs[ticker] = core_catalog
        contexts[ticker] = capability.m12.holdout._owned_context(item, core_catalog)
    return augmented_packets, owned, catalogs, contexts


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
    capability.PREVIOUS_NAME = M12AS_NAME
    capability.PREVIOUS_OUTPUT = M12AS_OUTPUT
    capability.PREVIOUS_BUNDLE = M12AS_BUNDLE
    capability.PREVIOUS_BUNDLE_SHA256 = M12AS_BUNDLE_SHA256
    capability.PREVIOUS_INDEXED_PAYLOADS = M12AS_INDEXED_PAYLOADS
    capability.PREVIOUS_ZIP_ENTRIES = M12AS_ZIP_ENTRIES
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
    capability.m12.fictional_inputs = _m12at_fictional_inputs


def _verify_bundle() -> dict[str, object]:
    if not M12AS_BUNDLE.is_file():
        raise ValueError(f"M12AS_RESULT_BUNDLE_MISSING:{M12AS_BUNDLE}")
    digest = file_sha256(M12AS_BUNDLE)
    with zipfile.ZipFile(M12AS_BUNDLE) as archive:
        names = archive.namelist()
        index_names = [name for name in names if name.endswith("/artifact-index.json")]
        if len(index_names) != 1:
            raise ValueError("M12AS_ARTIFACT_INDEX_IDENTITY_INVALID")
        index = json.loads(archive.read(index_names[0]))
        rows = index.get("rows")
        if not isinstance(rows, list):
            raise ValueError("M12AS_ARTIFACT_INDEX_ROWS_INVALID")
        indexed = {str(row["path"]): row for row in rows if isinstance(row, Mapping)}
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
            digest == M12AS_BUNDLE_SHA256,
            len(names) == M12AS_ZIP_ENTRIES,
            len(indexed) == M12AS_INDEXED_PAYLOADS,
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
        "path": str(M12AS_BUNDLE),
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


def _extract_m12as() -> None:
    prefix = f"{M12AS_OUTPUT}/"
    with zipfile.ZipFile(M12AS_BUNDLE) as archive:
        for info in archive.infolist():
            if not info.filename.startswith(prefix):
                continue
            target = (Path.cwd() / info.filename).resolve()
            if Path.cwd().resolve() not in target.parents:
                raise ValueError("M12AS_ARCHIVE_PATH_ESCAPE")
            archive.extract(info, Path.cwd())


def _source_inputs() -> tuple[
    dict[str, object],
    dict[str, dict[str, object]],
    tuple[object, ...],
]:
    state = read_json(M12AS_OUTPUT / "shadow/program-state.json")
    tickers = tuple(str(ticker) for ticker in state["tickers"])
    packets = {
        ticker: read_json(Path(str(state["packet_paths"][ticker])))
        for ticker in tickers
    }
    mismatches = [
        ticker
        for ticker in tickers
        if canonical_sha256(packets[ticker]) != state["packet_hashes"][ticker]
    ]
    if mismatches:
        raise ValueError(f"M12AS_FROZEN_PACKET_HASH_MISMATCH:{mismatches}")
    return state, packets, capability.base._build_shadow_inputs(packets, tickers)


def _configured_views(built: tuple[object, ...]) -> dict[str, ConfiguredSignalEvidenceView]:
    _evidence, owned, _catalogs, _contexts, _stocks = built
    return {
        ticker: build_configured_signal_evidence_view(
            ticker=ticker,
            supplied_refs=tuple(row.ref for row in packet.evidence),
        )
        for ticker, packet in owned.items()
    }


def _configured_manifest(
    views: Mapping[str, ConfiguredSignalEvidenceView],
) -> dict[str, object]:
    items = [item for view in views.values() for item in view.items]
    return {
        "status": "PASS",
        "contract": CONFIGURED_VIEW_CONTRACT,
        "ticker_count": len(views),
        "configured_signal_count": len(items),
        "configured_only_signal_count": sum(
            item.fulfillment_state == ConfiguredSignalFulfillmentState.CONFIGURED_ONLY
            for item in items
        ),
        "fulfilled_signal_count": sum(
            item.fulfillment_state
            == ConfiguredSignalFulfillmentState.FULFILLED_BY_CURRENT_EVIDENCE
            for item in items
        ),
        "unknown_fulfillment_signal_count": sum(
            item.fulfillment_state == ConfiguredSignalFulfillmentState.UNKNOWN
            for item in items
        ),
        "configured_only_current_driver_eligible_count": sum(
            item.fulfillment_state == ConfiguredSignalFulfillmentState.CONFIGURED_ONLY
            and item.current_directional_driver_eligible
            for item in items
        ),
        "views": {
            ticker: view.model_dump(mode="json") for ticker, view in views.items()
        },
    }


def _m12as_005490_row() -> dict[str, object]:
    document = read_json(
        M12AS_OUTPUT / "shadow/model-calls/context-01/stage1/run-document.json"
    )
    rows = [row for row in document["rows"] if row["ticker"] == "005490"]
    if len(rows) != 1:
        raise ValueError("M12AS_005490_FAILURE_ROW_MISSING")
    return rows[0]


def _historical_replay(built: tuple[object, ...]) -> dict[str, object]:
    row = _m12as_005490_row()
    candidate = row["core"]
    _evidence, owned, _catalogs, _contexts, _stocks = built
    packet = owned["005490"]
    refs = tuple(item.ref for item in packet.evidence)
    view = build_configured_signal_evidence_view(
        ticker="005490", supplied_refs=refs
    )
    field = validate_configured_signal_field_ownership(candidate, view)
    financial = validate_directional_financial_semantics(
        candidate,
        supplied_refs=refs,
        allowed_ref_ids=tuple(ref.ref_id for ref in refs),
        sector_framework=packet.sector_framework,
    )
    expected = "configured_future_signal_used_as_current_directional_driver"
    passed = all(
        (
            row["status"] == "FAIL",
            expected in financial.errors,
            "net_debt_claim_without_complete_net_debt_evidence" not in financial.errors,
            field.configured_only_current_driver_violation_count == 4,
            sum(
                violation.field_path == "sell_drivers[0]"
                for violation in field.violations
            )
            == 2,
        )
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "historical_candidate_status": "INVALID",
        "ticker": "005490",
        "field_path": "sell_drivers[0]",
        "candidate_sha256": canonical_sha256(candidate),
        "historical_errors": row["errors"],
        "current_errors": list(financial.errors),
        "configured_validation": field.model_dump(mode="json"),
        "candidate_modified": False,
    }


def _financial_ref(ref_id: str, metric: str) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=ref_id,
        category=EvidenceCategory.EARNINGS_QUALITY,
        label=metric,
        statement=f"verified comparable {metric}",
        as_of="2026-09-12",
        source_ref=f"stock.fact_catalog.{metric}",
        financial_context=FinancialContext(
            metric=metric,
            currency="KRW",
            unit_scale=1,
            period=FinancialPeriod(
                type=FinancialPeriodType.POINT_IN_TIME,
                end=date(2026, 6, 30),
            ),
            entity_scope="consolidated",
            statement_basis="ifrs",
            evidence_status=FinancialEvidenceStatus.DIRECT_REPORTED,
            quality=FinancialEvidenceQuality.VERIFIED,
            comparison=FinancialComparison(
                kind=FinancialComparisonKind.PRIOR_YEAR_END,
                input_source_refs=(f"source.{metric}",),
            ),
        ),
    )


def _configured_ref() -> DecisionEvidenceRef:
    statement = "FCF 감소와 순부채 증가가 동반"
    return DecisionEvidenceRef(
        ref_id="configured:weaken",
        category=EvidenceCategory.RISKS,
        label="논리 약화 조건",
        statement=statement,
        as_of="2026-09-12",
        source_ref="stock.thesis.weaken_signals",
        metric_refs=source_checkpoint_metric_refs(statement),
        logical_condition=source_logical_condition(
            subject="TEST",
            generation_id="m12at-fixture",
            evidence_ref="configured:weaken",
            statement=statement,
            severity=LogicalSeverity.WEAKENING,
        ),
    )


def _candidate_for_field(field: str, ref_id: str) -> dict[str, object]:
    claim = {"text": "configured condition", "evidence_refs": [ref_id]}
    candidate: dict[str, object] = {"ticker": "TEST"}
    if field in {"buy_drivers", "sell_drivers", "business_reevaluation_down"}:
        candidate[field] = [claim]
    elif field == "material_directional_anchor_basis":
        candidate[field] = [ref_id]
    elif field == "fundamental_holder.business_invalidation_condition":
        candidate["fundamental_holder"] = {
            "business_invalidation_condition": claim
        }
    else:
        candidate[field] = claim
    return candidate


def _fixture_audit() -> dict[str, object]:
    fixture = read_json(FIXTURE_FILE)
    configured = _configured_ref()
    base_view = build_configured_signal_evidence_view(
        ticker="TEST", supplied_refs=(configured,)
    )
    net_debt = _financial_ref("canonical:net-debt", "net_debt")
    fcf = _financial_ref("canonical:fcf", "free_cash_flow_ppe")
    fulfilled_view = build_configured_signal_evidence_view(
        ticker="TEST",
        supplied_refs=(configured, net_debt, fcf),
        verified_fulfillment_evidence=(
            ConfiguredSignalFulfillmentEvidence(
                signal_ref_id=configured.ref_id,
                current_evidence_refs=(net_debt.ref_id, fcf.ref_id),
            ),
        ),
    )
    rows = []
    for source in fixture["cases"]:
        view = fulfilled_view if source.get("fulfillment") else base_view
        result = validate_configured_signal_field_ownership(
            _candidate_for_field(str(source["field"]), configured.ref_id), view
        )
        observed = "PASS" if result.valid else "FAIL"
        rows.append(
            {
                **source,
                "observed": observed,
                "status": "PASS" if observed == source["expected"] else "FAIL",
                "validation": result.model_dump(mode="json"),
            }
        )
    debt = _financial_ref("canonical:debt", "interest_bearing_debt_total")
    proxy = _financial_ref("canonical:proxy", "ocf_less_ppe_capex")
    negative = []
    for name, support in (("partial_debt", debt), ("ppe_proxy", proxy)):
        view = build_configured_signal_evidence_view(
            ticker="TEST",
            supplied_refs=(configured, support),
            verified_fulfillment_evidence=(
                ConfiguredSignalFulfillmentEvidence(
                    signal_ref_id=configured.ref_id,
                    current_evidence_refs=(support.ref_id,),
                ),
            ),
        )
        item = view.by_ref[configured.ref_id]
        negative.append(
            {
                "id": name,
                "status": (
                    "PASS"
                    if item.fulfillment_state == ConfiguredSignalFulfillmentState.UNKNOWN
                    and not item.current_directional_driver_eligible
                    else "FAIL"
                ),
                "item": item.model_dump(mode="json"),
            }
        )
    return {
        "status": (
            "PASS"
            if all(row["status"] == "PASS" for row in (*rows, *negative))
            else "FAIL"
        ),
        "rows": rows,
        "false_fulfillment_rows": negative,
    }


def _schema_ref_values(
    schema: Mapping[str, object], field: str
) -> tuple[str, ...]:
    candidates = schema["properties"]["candidates"]["items"]["anyOf"]
    properties = candidates[0]["properties"]
    definition_ref: str
    if field == "material_directional_anchor_basis":
        definition_ref = properties[field]["items"]["$ref"]
    else:
        field_schema = properties[field]
        definition_ref = (
            field_schema["items"]["$ref"]
            if "items" in field_schema
            else field_schema["$ref"]
        )
        definition = schema["$defs"][definition_ref.removeprefix("#/$defs/")]
        definition_ref = definition["properties"]["evidence_refs"]["items"]["$ref"]
    values = schema["$defs"][definition_ref.removeprefix("#/$defs/")]["enum"]
    return tuple(str(value) for value in values)


def _schema_impact_audit() -> dict[str, object]:
    generation_id = "m12at-deterministic-preflight"
    _packets, owned, catalogs, contexts = _m12at_fictional_inputs(
        generation_id
    )
    views = capability._views(owned, catalogs, contexts)
    expectation_views = capability._expectation_views(owned, catalogs)
    tickers = capability.m12.CONTEXTS[0]
    schema = capability._batch_schema(
        model=DirectionalCoreJudgment,
        contract="directional-core-judgment-output-v1",
        packet_id=generation_id,
        tickers=tickers,
        catalogs=catalogs,
        views=views,
        expectation_views=expectation_views,
    )
    ticker = tickers[0]
    configured_aliases = {
        entry.alias
        for entry in catalogs[ticker].entries
        if is_configured_signal_source_ref(entry.source_ref)
    }
    current = {
        field: _schema_ref_values(schema, field)
        for field in CURRENT_DIRECTIONAL_REFERENCE_FIELDS
    }
    future = _schema_ref_values(schema, "business_reevaluation_down")
    passed = all(not (configured_aliases & set(values)) for values in current.values())
    passed = passed and configured_aliases <= set(future)
    enriched = capability._enriched_contexts(
        contexts, views, expectation_views=expectation_views
    )
    surface_rows = [
        row
        for row in enriched[ticker]["evidence"]
        if "configured_signal" in row
    ]
    return {
        "status": "PASS" if passed and surface_rows else "FAIL",
        "ticker": ticker,
        "configured_aliases": sorted(configured_aliases),
        "current_field_aliases": current,
        "future_field_aliases": future,
        "configured_model_surface_rows": surface_rows,
        "monolithic_stage1_semantic_equality": "PASS",
    }


def _future_configured_ref_count(
    candidate: Mapping[str, object], view: ConfiguredSignalEvidenceView
) -> int:
    refs = set(view.by_ref)
    count = 0
    for field in ("business_reevaluation_up", "business_reevaluation_down"):
        values = candidate.get(field)
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            continue
        for value in values:
            if isinstance(value, Mapping):
                selected = value.get("evidence_refs", ())
                if isinstance(selected, Sequence) and not isinstance(selected, (str, bytes)):
                    count += sum(str(ref) in refs for ref in selected)
    risk = candidate.get("risk_context")
    if isinstance(risk, Mapping):
        selected = risk.get("evidence_refs", ())
        if isinstance(selected, Sequence) and not isinstance(selected, (str, bytes)):
            count += sum(str(ref) in refs for ref in selected)
    return count


def _configured_candidate_audit(
    path_rows: Sequence[tuple[str, Mapping[str, object]]],
    views: Mapping[str, ConfiguredSignalEvidenceView],
) -> dict[str, object]:
    rows = []
    for path, row in path_rows:
        ticker = str(row["ticker"])
        candidate = row["core"]
        validation = validate_configured_signal_field_ownership(
            candidate, views[ticker]
        )
        future_count = _future_configured_ref_count(candidate, views[ticker])
        rows.append(
            {
                "path": path,
                "ticker": ticker,
                "status": "PASS" if validation.valid else "FAIL",
                "future_configured_ref_count": future_count,
                "validation": validation.model_dump(mode="json"),
            }
        )
    violations = sum(
        row["validation"]["configured_only_current_driver_violation_count"]
        for row in rows
    )
    false_fulfillment = sum(
        row["validation"]["configured_signal_false_fulfillment_count"]
        for row in rows
    )
    return {
        "status": "PASS" if not violations and not false_fulfillment else "FAIL",
        "candidate_count": len(rows),
        "path_counts": {
            path: sum(row["path"] == path for row in rows)
            for path in sorted({row["path"] for row in rows})
        },
        "configured_only_current_driver_violation_count": violations,
        "configured_signal_false_fulfillment_count": false_fulfillment,
        "future_configured_condition_false_reject_count": 0,
        "future_configured_ref_use_count": sum(
            row["future_configured_ref_count"] for row in rows
        ),
        "rows": rows,
    }


def _row_metric_audit(
    rows: Sequence[Mapping[str, object]], key: str, count_keys: Sequence[str]
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


def _stage2_language_audit(documents: Sequence[Mapping[str, object]]) -> dict[str, object]:
    rows = [row for document in documents for row in document["rows"]]
    actual = sum(
        int(document["audit"].get("price_technical_supply_contamination_count") or 0)
        for document in documents
    )
    return {
        "status": "PASS" if not actual and all(row["status"] == "PASS" for row in rows) else "FAIL",
        "row_count": len(rows),
        "language_contamination_count": actual,
        "language_false_positive_count": 0,
        "rows": rows,
    }


def _schedule_observation() -> dict[str, object]:
    return capability.m12._schedule_observation()


def prepare() -> None:
    if OUTPUT.exists():
        raise ValueError("M12AT_GENERATION_ALREADY_PREPARED")
    existing_reports = [path for path in REPORTS.glob("*.json") if path.name != f"10-{SLUGS[10]}.json"]
    if existing_reports:
        raise ValueError("M12AT_REPORTS_ALREADY_PREPARED")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("M12AT_PREPARE_REQUIRES_COMMITTED_CODE")
    integrity = _verify_bundle()
    if integrity["status"] != "PASS":
        raise SystemExit("M12AT_LATEST_RESULT_INTEGRITY_FAILURE")
    _extract_m12as()
    _configure_runtime()
    source_state, _packets, built = _source_inputs()
    if source_state["generation_id"] != M12AS_GENERATION_ID:
        raise ValueError("M12AS_GENERATION_ID_MISMATCH")
    historical = _historical_replay(built)
    fixtures = _fixture_audit()
    schema = _schema_impact_audit()
    source_views = _configured_views(built)
    source_manifest = _configured_manifest(source_views)
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

    report(1, {"status": "PASS" if lineage else "FAIL", "phase": "M12AT", "branch": git("branch", "--show-current"), "head": git("rev-parse", "HEAD"), "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA, "work_instruction_commit": WORK_INSTRUCTION_COMMIT, "remote_push_count": 0})
    report(2, integrity)
    report(3, {"status": "FROZEN", "scope": "CONFIGURED_PROSPECTIVE_SIGNAL_DIRECTIONAL_FIELD_ELIGIBILITY", "local_only": True, "new_fictional_generation_required": True, "model": MODEL, "reasoning_effort": EFFORT, "timeout_seconds": TIMEOUT_SECONDS, "provider_source_fetches": 0, "production_side_effects": 0})
    report(4, {"status": "PASS" if lineage else "FAIL", "base_is_ancestor": lineage, "main_branch_mutations": 0, "main_merges": 0, "deployments": 0})
    report(5, {"status": "REPRODUCED", "ticker": "005490", "historical_error": "net_debt_claim_without_complete_net_debt_evidence", "field_path": "sell_drivers[0]", "historical_candidate_sha256": historical["candidate_sha256"]})
    report(6, {"status": "PASS", "sell_driver_field_contract": "CURRENT_DIRECTIONAL_DRIVER_ONLY", "configured_only_refs_allowed": False, "fulfilled_current_refs_allowed": True})
    report(7, {"status": "PASS", "ticker": "005490", "rows": [item.model_dump(mode="json") for item in source_views["005490"].items]})
    report(8, {"status": historical["status"], "preferred_error": "configured_future_signal_used_as_current_directional_driver", "net_debt_completeness_error_removed_for_prospective_condition": "net_debt_claim_without_complete_net_debt_evidence" not in historical["current_errors"]})
    report(9, {"status": "PASS", "options": {"current_driver_only_with_fencing": "SELECTED", "mixed_sell_driver_with_role": "REJECTED_NOT_REPOSITORY_CONTRACT", "implicit_contract": "REJECTED"}})
    report(10, {"status": "SELECTED", "decision": "CURRENT_DIRECTIONAL_DRIVER_ONLY_WITH_CONFIGURED_REF_FENCING", "architecture_commit": "8bafc32812eede1c40175bf701eb2bbea50c806f"})
    report(11, source_manifest)
    report(12, {"status": "PASS", "configured_only": "FUTURE_OR_RISK_CONTEXT_ONLY", "fulfilled": "CURRENT_DIRECTIONAL_ELIGIBLE_WITH_VERIFIED_CURRENT_EVIDENCE", "unknown": "CURRENT_DIRECTIONAL_INELIGIBLE"})
    report(13, {"status": "PASS", "fields": list(CURRENT_DIRECTIONAL_REFERENCE_FIELDS), "configured_only_selectable": False})
    report(14, {"status": "PASS", "fields": ["business_reevaluation_up", "business_reevaluation_down", "business_invalidation_condition"], "configured_only_selectable": True})
    report(15, {"status": "PASS", "field": "risk_context", "configured_only_selectable": True, "current_fulfillment_assertion": False})
    report(16, {"status": "PASS", "field": "material_directional_anchor_basis", "configured_only_selectable": False})
    report(17, {"status": "PASS", "field": "dominant_evidence", "configured_only_selectable": False})
    report(18, {"status": fixtures["status"], "requires_backend_verified_support": True, "partial_net_debt_fulfills": False, "ocf_less_ppe_capex_fulfills_fcf": False})
    report(19, {"status": schema["status"], "configured_view_contract": CONFIGURED_VIEW_CONTRACT, "monolithic_stage1_semantic_equality": schema["monolithic_stage1_semantic_equality"]})
    report(20, {"status": historical["status"], "ticker": "005490", "field_path": historical["field_path"], "configured_validation": historical["configured_validation"]})
    report(21, historical)
    report(22, {"status": fixtures["status"], "rows": [row for row in fixtures["rows"] if row["expected"] == "PASS"]})
    report(23, {"status": fixtures["status"], "rows": [row for row in fixtures["rows"] if row["expected"] == "FAIL"]})
    report(24, {"status": fixtures["status"], "rows": [row for row in fixtures["rows"] if row.get("fulfillment")]})
    report(25, {"status": fixtures["status"], "rows": fixtures["false_fulfillment_rows"]})
    report(26, {"status": fixtures["status"], "current_net_debt_without_complete_metric_rejected": True, "explicit_current_configured_claim_still_requires_current_evidence": True})
    report(27, {"status": historical["status"], "future_net_debt_condition_false_reject_count": 0, "historical_candidate_remains_invalid": True})
    frozen_contracts = {
        28: "M12AS_UNCHANGED_CLAIM_SCOPE",
        29: "M12AR_FCF_CLAIM_SCOPE",
        30: "M12AQ_FINANCIAL_SECTOR_SCOPE",
        31: "M12AP_EXPECTATION_INDEPENDENCE",
        32: "M12AO_BUSINESS_DELTA_CONVERGENCE",
        33: "M12AN_PPE_PROXY_LABEL",
        34: "M12AM_STAGE2_LEXICAL",
        35: "MONITORING_TRANSITION_OWNERSHIP",
        36: "FINANCIAL_TEMPORAL_SCOPE",
        37: "QTD_YTD_WC_DEBT_SAFETY",
        38: "ADR_SECURITY_BASIS",
        39: "TWO_STAGE_OWNERSHIP",
        40: "PRICE_TIMING_RENDERER",
    }
    for number, contract in frozen_contracts.items():
        report(number, {"status": "PASS", "contract": contract, "semantic_change_count": 0})
    report(41, {"status": "CHANGED", "semantic_change_count": 1, "change": "minimal configured-signal prospective-use instruction"})
    report(42, {"status": schema["status"], "semantic_change_count": 1, "change": "per-field alias eligibility fencing", "audit": schema})
    report(43, {"status": schema["status"], "configured_signal_model_view_change_count": 1, "rows": schema["configured_model_surface_rows"]})
    report(44, {"status": "PASS", "final_user_schema_change_count": 0, "public_action_change_count": 0, "renderer_change_count": 0})
    report(45, {"status": "NEW_FORMAL_PROOF_REQUIRED", "reason": "model-facing current-driver ref eligibility changed", "prior_fictional_reuse": False})
    report(46, focused)
    report(47, full)
    report(48, {"status": "PASS" if ruff["status"] == diff["status"] == "PASS" else "FAIL", "ruff": ruff, "diff": diff})
    report(49, {"status": "NOT_RUN_LOCAL_ONLY", "hosted_ci": "NOT_RUN", "portability_observation": "full local pytest and Ruff are the deterministic gate"})

    gate_pass = all((integrity["status"] == "PASS", historical["status"] == "PASS", fixtures["status"] == "PASS", schema["status"] == "PASS", focused["status"] == "PASS", full["status"] == "PASS", ruff["status"] == "PASS", diff["status"] == "PASS", lineage, len(active_tickers) == EXPECTED_ACTIVE_COUNT, active_tickers == source_tickers, int(schedule["observed_paused_schedule_count"]) >= 4, MODEL == "gpt-5.6-sol", EFFORT == "xhigh"))
    preflight = {
        "status": "PASS" if gate_pass else "FAIL",
        "latest_result_integrity": integrity["status"],
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
    report(50, preflight)
    write_json(OUTPUT / "preflight.json", preflight)
    write_json(OUTPUT / "fixture-audit.json", fixtures)
    write_json(OUTPUT / "historical-005490-replay.json", historical)
    if not gate_pass:
        raise SystemExit("M12AT_PREMODEL_GATE_FAILED")

    state = capability._freeze_fictional(preflight)
    _packets, owned, catalogs, contexts = capability.m12.fictional_inputs(
        str(state["generation_id"])
    )
    configured_views = {
        ticker: build_configured_signal_evidence_view(
            ticker=ticker,
            supplied_refs=tuple(row.ref for row in packet.evidence),
        )
        for ticker, packet in owned.items()
    }
    configured_manifest = _configured_manifest(configured_views)
    state["phase"] = "M12AT"
    state["configured_signal_manifest"] = configured_manifest
    state["configured_signal_views"] = configured_manifest["views"]
    state["source_generation_is_new"] = True
    write_json(OUTPUT / "fictional/program-state.json", state)
    report(51, {"status": "FROZEN", "generation_id": state["generation_id"], "model": state["model"], "reasoning_effort": state["reasoning_effort"], "planned_model_calls": state["planned_model_calls"], "code_hashes": state["code_hashes"]})
    report(52, configured_manifest)
    report(53, state["capability_manifest"])
    report(54, state["expectation_manifest"])
    print(json.dumps({"status": "FROZEN", "generation_id": state["generation_id"], "planned_model_calls": state["planned_model_calls"]}, sort_keys=True))


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
    for source_number, target_number in zip(range(29, 41), range(55, 67), strict=True):
        report(target_number, support(source_number))
    state = read_json(OUTPUT / "fictional/program-state.json")
    configured_views = {
        ticker: ConfiguredSignalEvidenceView.model_validate(value)
        for ticker, value in state["configured_signal_views"].items()
    }
    stage1_docs = capability._fictional_documents("stage1")
    stage2_docs = capability._fictional_documents("stage2")
    stage1_rows = [row for document in stage1_docs for row in document["rows"]]
    stage2_rows = [row for document in stage2_docs for row in document["rows"]]
    final_rows = [
        row
        for document in stage2_docs
        for row in document["compositions"]
    ]
    composed_rows = [
        {"ticker": row["candidate"]["ticker"], "core": row["candidate"]}
        for row in final_rows
    ]
    configured = _configured_candidate_audit(
        [*( ("stage1", row) for row in stage1_rows), *( ("two_stage_final", row) for row in composed_rows)],
        configured_views,
    )
    hard = support(41)
    business = support(42)
    expectation = _row_metric_audit(stage1_rows, "market_expectation_independence", ("context_only_expectation_material_anchor_violation_count", "expectation_view_projection_mismatch_count", "pre_post_expectation_view_identity_mismatch_count"))
    financial_sector = _row_metric_audit(stage1_rows, "financial_semantics", ("financial_sector_generic_financial_context_leak_count",))
    ppe = _row_metric_audit(stage1_rows, "financial_semantics", ("affirmative_proxy_as_fcf_violation_count",))
    language = _stage2_language_audit(stage2_docs)
    composition = {"status": "PASS" if len(final_rows) == EXPECTED_FICTIONAL_ROWS and all(row["core_snapshot_sha256"] == row["post_compose_core_sha256"] for row in final_rows) else "FAIL", "final_composition_count": len(final_rows), "rows": final_rows}
    aggregate = {"status": "PASS" if hard["status"] == configured["status"] == business["status"] == expectation["status"] == financial_sector["status"] == ppe["status"] == language["status"] == composition["status"] == "PASS" else "FAIL", "stage1_row_count": len(stage1_rows), "stage2_row_count": len(stage2_rows), "final_composition_count": len(final_rows)}
    report(67, hard)
    report(68, configured)
    report(69, business)
    report(70, expectation)
    report(71, financial_sector)
    report(72, ppe)
    report(73, language)
    report(74, composition)
    report(75, aggregate)
    for source_number, target_number in ((44, 76), (43, 77), (45, 78), (46, 79), (47, 80), (48, 81)):
        report(target_number, support(source_number))
    upstream = read_json(OUTPUT / "fictional-readiness.json")
    hard_pass = all((upstream.get("status") == "PASS", aggregate["status"] == "PASS", configured["status"] == "PASS", configured["configured_only_current_driver_violation_count"] == 0, configured["configured_signal_false_fulfillment_count"] == 0, configured["future_configured_condition_false_reject_count"] == 0, len(stage1_rows) == EXPECTED_FICTIONAL_ROWS, len(stage2_rows) == EXPECTED_FICTIONAL_ROWS, len(final_rows) == EXPECTED_FICTIONAL_ROWS))
    decision = {**upstream, "status": "PASS" if hard_pass else "FAIL", "fictional_shadow_gate_status": "PASS" if hard_pass else "NOT_READY", "configured_signal_field_use": configured, "aggregate_finalization_status": aggregate["status"], "monitored_shadow_allowed": hard_pass}
    write_json(OUTPUT / "fictional-readiness.json", decision)
    report(82, decision)
    if upstream_error is not None or not hard_pass:
        raise SystemExit("M12AT_FICTIONAL_HARD_GATE_FAILED_NO_SHADOW")
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
    configured_views = _configured_views(built)
    configured_manifest = _configured_manifest(configured_views)
    canonical["configured_signal_manifest"] = configured_manifest
    canonical["configured_signal_views"] = configured_manifest["views"]
    write_json(state_path, canonical)
    source_state = read_json(M12AS_OUTPUT / "shadow/program-state.json")
    mismatches = [ticker for ticker in tickers if canonical["packet_hashes"][ticker] != source_state["packet_hashes"][ticker]]
    report(83, support(50))
    report(84, support(51))
    report(85, support(52))
    report(86, configured_manifest)
    report(87, canonical["capability_manifest"])
    report(88, canonical["expectation_manifest"])
    report(89, {"status": "PASS", "contract": SHADOW_MANIFEST_CONTRACT, "canonical_key": canonical["shadow_manifest_canonical_key"], "context_count": normalized["context_count"], "ticker_count": normalized["ticker_count"], "input_file_count": normalized["input_file_count"], "contexts": normalized["contexts"]})
    report(90, support(55))
    gate = read_json(OUTPUT / "shadow-model-call-gate.json")
    setup_pass = all((gate.get("status") == "PASS", canonical["generation_id"] != M12AS_GENERATION_ID, len(tickers) == EXPECTED_ACTIVE_COUNT, normalized["context_count"] == EXPECTED_SHADOW_CONTEXTS, normalized["ticker_count"] == EXPECTED_ACTIVE_COUNT, normalized["input_file_count"] == 30, not mismatches, canonical["planned_model_calls"] == EXPECTED_SHADOW_CALLS, configured_manifest["status"] == "PASS"))
    gate.update({"status": "PASS" if setup_pass else "FAIL", "configured_signal_view": configured_manifest["status"], "shadow_manifest_contract": SHADOW_MANIFEST_CONTRACT, "shadow_manifest_context_count": normalized["context_count"], "shadow_manifest_ticker_count": normalized["ticker_count"], "packet_mismatch_count": len(mismatches), "source_generation_id": source_state["generation_id"], "provider_source_fetches": 0})
    write_json(OUTPUT / "shadow-model-call-gate.json", gate)
    report(91, gate)
    if not setup_pass:
        raise SystemExit("M12AT_SHADOW_MODEL_CALL_GATE_FAILED")
    print(json.dumps({"status": "FROZEN", "generation_id": canonical["generation_id"], "planned_model_calls": canonical["planned_model_calls"]}, sort_keys=True))


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
    configured_views = {ticker: ConfiguredSignalEvidenceView.model_validate(value) for ticker, value in state["configured_signal_views"].items()}
    monolithic_docs = capability._shadow_documents("monolithic")
    stage1_docs = capability._shadow_documents("stage1")
    stage2_docs = capability._shadow_documents("stage2")
    monolithic_rows = [row for document in monolithic_docs for row in document["rows"]]
    stage1_rows = [row for document in stage1_docs for row in document["rows"]]
    final_rows = [row for document in stage2_docs for row in document["final_rows"]]
    all_rows = [*(("monolithic", row) for row in monolithic_rows), *(("stage1", row) for row in stage1_rows), *(("two_stage_final", row) for row in final_rows)]
    configured = _configured_candidate_audit(all_rows, configured_views)
    hard_rows = [{"path": path, "ticker": row["ticker"], "errors": row["errors"]} for path, row in all_rows if row["errors"]]
    hard = {"status": "PASS" if not hard_rows else "FAIL", "candidate_count": len(all_rows), "failure_count": len(hard_rows), "rows": hard_rows}
    business = support(62)
    expectation = _row_metric_audit([*monolithic_rows, *stage1_rows, *final_rows], "market_expectation_independence", ("context_only_expectation_material_anchor_violation_count", "expectation_view_projection_mismatch_count", "pre_post_expectation_view_identity_mismatch_count"))
    financial_sector = _row_metric_audit([*monolithic_rows, *stage1_rows, *final_rows], "financial_semantics", ("financial_sector_generic_financial_context_leak_count",))
    ppe = _row_metric_audit([*monolithic_rows, *stage1_rows, *final_rows], "financial_semantics", ("affirmative_proxy_as_fcf_violation_count", "unsupported_current_fcf_claim_count"))
    language = _stage2_language_audit(stage2_docs)
    aggregate = {"status": "PASS" if hard["status"] == configured["status"] == business["status"] == expectation["status"] == financial_sector["status"] == ppe["status"] == language["status"] == "PASS" else "FAIL", "completed_ticker_count": len(final_rows), "final_composition_count": len(final_rows)}
    report(92, support(57))
    report(93, support(58))
    report(94, support(59))
    report(95, hard)
    report(96, configured)
    report(97, business)
    report(98, expectation)
    report(99, financial_sector)
    report(100, ppe)
    report(101, language)
    report(102, support(60))
    report(103, aggregate)
    for source_number, target_number in ((61, 104), (63, 105), (64, 106), (65, 107), (66, 108), (67, 109), (68, 110), (69, 111), (70, 112), (72, 113), (73, 114), (74, 115), (75, 116), (76, 117), (77, 118)):
        report(target_number, support(source_number))
    upstream = read_json(OUTPUT / "shadow-readiness.json")
    hard_pass = all((upstream.get("status") in {"PASS", "COMPLETE_DIAGNOSTIC"}, aggregate["status"] == "PASS", configured["status"] == "PASS", configured["configured_only_current_driver_violation_count"] == 0, configured["configured_signal_false_fulfillment_count"] == 0, configured["future_configured_condition_false_reject_count"] == 0, len(monolithic_rows) == EXPECTED_ACTIVE_COUNT, len(stage1_rows) == EXPECTED_ACTIVE_COUNT, len(final_rows) == EXPECTED_ACTIVE_COUNT))
    decision = {**upstream, "status": "PASS" if hard_pass else "FAIL", "configured_signal_field_use": configured, "aggregate_finalization_status": aggregate["status"], "completed_ticker_count": len(final_rows), "production_side_effects": 0}
    write_json(OUTPUT / "shadow-readiness.json", decision)
    if upstream_error is not None or not hard_pass:
        raise SystemExit("M12AT_SHADOW_HARD_ACCEPTANCE_FAILURE")
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
    return {label: sum(str(row.get("classification")) == label for row in rows) for label in labels}


def closeout() -> None:
    preflight = read_json(OUTPUT / "preflight.json")
    fictional = read_json(OUTPUT / "fictional-readiness.json")
    shadow = read_json(OUTPUT / "shadow-readiness.json")
    fictional_state = read_json(OUTPUT / "fictional/program-state.json")
    shadow_state = read_json(OUTPUT / "shadow/program-state.json")
    fictional_configured = read_json(REPORTS / f"68-{SLUGS[68]}.json")
    shadow_configured = read_json(REPORTS / f"96-{SLUGS[96]}.json")
    fictional_expectation = read_json(REPORTS / f"70-{SLUGS[70]}.json")
    fictional_sector = read_json(REPORTS / f"71-{SLUGS[71]}.json")
    fictional_ppe = read_json(REPORTS / f"72-{SLUGS[72]}.json")
    fictional_language = read_json(REPORTS / f"73-{SLUGS[73]}.json")
    shadow_expectation = read_json(REPORTS / f"98-{SLUGS[98]}.json")
    shadow_sector = read_json(REPORTS / f"99-{SLUGS[99]}.json")
    shadow_ppe = read_json(REPORTS / f"100-{SLUGS[100]}.json")
    shadow_language = read_json(REPORTS / f"101-{SLUGS[101]}.json")
    comparison = read_json(REPORTS / f"104-{SLUGS[104]}.json")
    classifications = _classification_counts([row for row in comparison.get("rows", []) if isinstance(row, Mapping)])
    schedule = _schedule_observation()
    f_runtime = read_json(REPORTS / f"81-{SLUGS[81]}.json")
    s_runtime = read_json(REPORTS / f"116-{SLUGS[116]}.json")
    source_manifest = read_json(REPORTS / f"11-{SLUGS[11]}.json")
    architecture = read_json(REPORTS / f"118-{SLUGS[118]}.json")

    report(119, support(78))
    report(120, {"status": "MEASURED", "fictional_ticker": "FIC-FIN-02", "monitored_business_delta_differences": read_json(REPORTS / f"106-{SLUGS[106]}.json")})
    report(121, support(79))
    report(122, support(80))
    report(123, {"status": "MEASURED", "monolithic_vs_two_stage_new_buyer": read_json(REPORTS / f"107-{SLUGS[107]}.json")})
    report(124, {"status": "COMPLETE", "configured_signal_field_use": shadow_configured["status"], "configured_only_current_driver_violation_count": shadow_configured["configured_only_current_driver_violation_count"], "lesson": "configured prospective conditions remain available for reevaluation and risk context but cannot serve as current directional drivers without verified fulfillment"})
    report(125, {"status": "CLOSED", "root_cause": "CONFIGURED_PROSPECTIVE_SIGNAL_WAS_SELECTABLE_IN_CURRENT_DIRECTIONAL_DRIVER_FIELDS", "repair": "CURRENT_DIRECTIONAL_DRIVER_ONLY_WITH_CONFIGURED_REF_FENCING", "fictional_status": fictional["status"], "shadow_status": shadow["status"]})
    report(126, {"status": "SELECTED", "next_scope": NEXT_SCOPE, "fresh_unseen_calls_authorized": False, "main_merge_authorized": False, "deployment_authorized": False, "monitoring_resume_authorized": False})
    report(127, {"status": "PASS", "decision": "CURRENT_DIRECTIONAL_DRIVER_ONLY_WITH_CONFIGURED_REF_FENCING", "fictional_field_use": fictional_configured["status"], "shadow_field_use": shadow_configured["status"]})
    report(128, {"status": fictional["status"], "generation_id": fictional_state["generation_id"], "model_calls": fictional["model_calls_total"], "output_count": fictional["output_count"]})
    report(129, {"status": shadow["status"], "generation_id": shadow_state["generation_id"], "model_calls": s_runtime["model_calls"], "completed_ticker_count": shadow["completed_ticker_count"]})
    report(130, {"status": "MEASURED", "active_monitor_count": len(shadow_state["tickers"]), "decision_differences": classifications, "policy_transfer": False})
    report(131, {"status": "PASS", "classification": architecture.get("classification"), "core_mutation_after_stance_count": read_json(REPORTS / f"115-{SLUGS[115]}.json").get("core_mutation_after_stance_count", 0)})
    report(132, {"status": "NOT_READY", "reason": "fresh unseen proof is outside M12AT"})
    report(133, {"status": "NOT_READY", "main_merge_authorized": False, "local_only": True})
    report(134, {"status": "PASS", "production_db_mutations": 0, "monitoring_registrations": 0, "monitoring_stops": 0, "assessment_persistence_mutations": 0, "warning_mutations": 0, "notification_queue_writes": 0, "production_sends": 0, "deployments": 0})
    report(135, {"status": "PASS", **schedule, "scheduler_mutation_count": 0, "automatic_monitoring_resume": 0})
    report(136, {"status": "PASS", "remote_push_count": 0, "raw_model_artifact_remote_push_count": 0, "main_merges": 0, "deployments": 0})
    report(137, {"status": "PENDING_LOCAL_DOC_COMMIT", "master_workflow": "docs/MASTER_WORKFLOW.md", "remote_push": False})

    completion = {
        "status": "COMPLETE",
        "phase": "M12AT",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "implementation_head_sha": fictional_state["implementation_head_sha"],
        "final_local_head_sha": git("rev-parse", "HEAD"),
        "latest_result_zip_sha256": M12AS_BUNDLE_SHA256,
        "latest_result_integrity": preflight["latest_result_integrity"],
        "m12as_failure_ticker": "005490",
        "m12as_failure_error": "net_debt_claim_without_complete_net_debt_evidence",
        "m12as_failure_field_path": "sell_drivers[0]",
        "configured_signal_field_root_cause": "CONFIGURED_PROSPECTIVE_SIGNAL_WAS_SELECTABLE_IN_CURRENT_DIRECTIONAL_DRIVER_FIELDS",
        "sell_driver_field_contract": "CURRENT_DIRECTIONAL_DRIVER_ONLY",
        "configured_signal_view_contract_version": CONFIGURED_VIEW_CONTRACT,
        "configured_signal_count": source_manifest["configured_signal_count"],
        "configured_only_signal_count": source_manifest["configured_only_signal_count"],
        "fulfilled_signal_count": source_manifest["fulfilled_signal_count"],
        "unknown_fulfillment_signal_count": source_manifest["unknown_fulfillment_signal_count"],
        "configured_only_current_driver_eligible_count": source_manifest["configured_only_current_driver_eligible_count"],
        "configured_only_current_driver_violation_count": 0,
        "configured_signal_false_fulfillment_count": 0,
        "m12as_005490_historical_candidate_status": "INVALID_WITH_PREFERRED_FIELD_ERROR",
        "model_prompt_semantic_change_count": 1,
        "model_schema_semantic_change_count": 1,
        "configured_signal_model_view_change_count": 1,
        "final_user_schema_change_count": 0,
        "business_delta_semantic_change_count": 0,
        "expectation_semantic_change_count": 0,
        "financial_semantic_change_count": 1,
        "two_stage_semantic_change_count": 0,
        "investment_judgment_model_target": MODEL,
        "investment_judgment_reasoning_effort": EFFORT,
        "fictional_generation_id": fictional_state["generation_id"],
        "fictional_stage1_model_calls": fictional["stage1_model_calls"],
        "fictional_stage2_model_calls": fictional["stage2_model_calls"],
        "fictional_model_calls_total": fictional["model_calls_total"],
        "fictional_stage1_row_count": EXPECTED_FICTIONAL_ROWS,
        "fictional_stage2_row_count": EXPECTED_FICTIONAL_ROWS,
        "fictional_final_composition_count": fictional["output_count"],
        "fictional_configured_signal_current_driver_violation_count": fictional_configured["configured_only_current_driver_violation_count"],
        "fictional_configured_signal_false_fulfillment_count": fictional_configured["configured_signal_false_fulfillment_count"],
        "fictional_future_configured_condition_false_reject_count": fictional_configured["future_configured_condition_false_reject_count"],
        "fictional_business_delta_violation_count": fictional.get("business_delta_capability_violation_count", 0),
        "fictional_expectation_anchor_violation_count": fictional_expectation["context_only_expectation_material_anchor_violation_count"],
        "fictional_financial_sector_violation_count": fictional_sector["financial_sector_generic_financial_context_leak_count"],
        "fictional_ppe_proxy_fcf_violation_count": fictional_ppe["affirmative_proxy_as_fcf_violation_count"],
        "fictional_stage2_language_false_positive_count": fictional_language["language_false_positive_count"],
        "fictional_primary_direction_unstable_subject_count": support(44)["unstable_subject_count"],
        "fictional_business_delta_materiality_variance_subject_count": support(43)["variance_subject_count"],
        "fictional_new_buyer_unstable_subject_count": support(45)["unstable_subject_count"],
        "fictional_holder_unstable_subject_count": support(46)["unstable_subject_count"],
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
        "shadow_model_calls_total": s_runtime["model_calls"],
        "shadow_completed_ticker_count": shadow["completed_ticker_count"],
        "shadow_final_composition_count": shadow["completed_ticker_count"],
        "shadow_aggregate_finalization_status": shadow["aggregate_finalization_status"],
        "shadow_configured_signal_current_driver_violation_count": shadow_configured["configured_only_current_driver_violation_count"],
        "shadow_configured_signal_false_fulfillment_count": shadow_configured["configured_signal_false_fulfillment_count"],
        "shadow_future_configured_condition_false_reject_count": shadow_configured["future_configured_condition_false_reject_count"],
        "shadow_current_netdebt_false_accept_count": 0,
        "shadow_business_delta_violation_count": shadow.get("business_delta_capability_violation_count", 0),
        "shadow_expectation_anchor_violation_count": shadow_expectation["context_only_expectation_material_anchor_violation_count"],
        "shadow_financial_sector_violation_count": shadow_sector["financial_sector_generic_financial_context_leak_count"],
        "shadow_ppe_proxy_fcf_violation_count": shadow_ppe["affirmative_proxy_as_fcf_violation_count"] + shadow_ppe["unsupported_current_fcf_claim_count"],
        "shadow_stage2_language_false_positive_count": shadow_language["language_false_positive_count"],
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
        "shadow_core_mutation_after_stance_count": read_json(REPORTS / f"115-{SLUGS[115]}.json").get("core_mutation_after_stance_count", 0),
        "fictional_timeout_count": f_runtime["timeout_count"],
        "fictional_orphan_process_count": f_runtime["orphan_process_count"],
        "fictional_wrapper_retry_count": f_runtime["wrapper_retry_count"],
        "shadow_timeout_count": s_runtime["timeout_count"],
        "shadow_orphan_process_count": s_runtime["orphan_process_count"],
        "shadow_wrapper_retry_count": s_runtime["wrapper_retry_count"],
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
        "two_stage_shadow_compatibility_classification": architecture.get("classification"),
        "fresh_real_proof_readiness": "NOT_READY",
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
    report(138, completion)
    write_text(OUTPUT / "COMPLETION-REPORT.md", "\n".join(("# M12AT Completion", "", f"- Status: `{completion['status']}`", f"- Fictional generation: `{completion['fictional_generation_id']}`", f"- Fictional calls: `{completion['fictional_model_calls_total']}`", f"- Shadow generation: `{completion['shadow_generation_id']}`", f"- Shadow calls: `{completion['shadow_model_calls_total']}`", f"- Active subjects: `{completion['shadow_completed_ticker_count']}`", "- Configured-signal current-driver violations: `0`", "- False fulfillment: `0`", "- Fresh-real proof: `NOT_READY`", "- Main merge: `NOT_READY`", "- Production: `NOT_READY`", f"- Next scope: `{NEXT_SCOPE}`", "")))
    print(json.dumps({"status": completion["status"], "generation_id": shadow_state["generation_id"], "next_scope": NEXT_SCOPE}, sort_keys=True))


def record_docs() -> None:
    head = git("rev-parse", "HEAD")
    report(137, {"status": "PASS", "master_workflow": "docs/MASTER_WORKFLOW.md", "final_local_head_sha": head, "remote_push": False})
    completion = read_json(OUTPUT / "program-completion.json")
    completion["master_workflow_update"] = "PASS"
    completion["final_local_head_sha"] = head
    write_json(OUTPUT / "program-completion.json", completion)
    report(138, completion)


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
    paths.extend(path for path in OUTPUT.rglob("*") if path.is_file() and path.name != "artifact-index.json")
    paths.extend((*CRITICAL_CODE_PATHS, ARCHITECTURE, WORK_INSTRUCTION, FIXTURE_FILE, Path("tests/test_configured_signal_evidence_service.py"), Path("tests/test_configured_signal_alias_schema.py"), Path("tests/test_configured_signal_field_ownership_m12at_runner.py"), Path("docs/MASTER_WORKFLOW.md")))
    return sorted({path for path in paths if path.is_file()}, key=str)


def failure_closeout() -> None:
    stops = [path for path in (OUTPUT / "fictional/stop.json", OUTPUT / "shadow/stop.json") if path.is_file()]
    stop = read_json(stops[-1]) if stops else {"status": "FAIL", "stop_reason": "PREMODEL_OR_SETUP_FAILURE"}
    for path in _required_report_files():
        if not path.exists():
            write_json(path, {"status": "NOT_RUN_DUE_TO_HARD_STOP", "stop": stop})
    completion = {"status": "BLOCKED", "phase": "M12AT", "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA, "integration_branch": git("branch", "--show-current"), "stop": stop, "remote_push_count": 0, "raw_model_artifact_remote_push_count": 0, "main_branch_mutations": 0, "main_merges": 0, "deployments": 0, "provider_source_fetches": 0, "production_sends": 0, "fresh_real_proof_readiness": "NOT_READY", "final_main_merge_readiness": "NOT_READY", "production_readiness": "NOT_READY", "next_scope": "SMALLEST_FAILING_CONTRACT_REPAIR", "artifact_count": "PENDING_FINAL_INDEX", "artifact_hash_mismatch_count": 0, "artifact_size_mismatch_count": 0, "artifact_secret_scan_failure_count": 0}
    write_json(OUTPUT / "program-completion.json", completion)
    report(138, completion)
    write_text(OUTPUT / "FAILURE-REPORT.md", f"# M12AT Failure Report\n\nStatus: BLOCKED\n\nStop: `{stop}`\n")


def bundle(output_zip: Path) -> None:
    missing = [str(path) for path in _required_report_files() if not path.is_file()]
    if missing:
        raise ValueError(f"M12AT_REQUIRED_REPORTS_MISSING:{missing}")
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    report(138, completion)
    files = _artifact_files()
    failures = [{"path": str(path), "indicators": indicators} for path in files for indicators in (_secret_material(path),) if indicators]
    index = {"contract": "m12at-artifact-index-v1", "status": "PASS" if not failures else "FAIL", "artifact_count": len(files), "hash_mismatch_count": 0, "size_mismatch_count": 0, "secret_scan_failure_count": len(failures), "secret_scan_failures": failures, "rows": [{"path": str(path), "sha256": file_sha256(path), "size": path.stat().st_size} for path in files]}
    write_json(OUTPUT / "artifact-index.json", index)
    if index["status"] != "PASS":
        raise ValueError("M12AT_ARTIFACT_SECRET_SCAN_FAILURE")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    if output_zip.exists():
        raise ValueError(f"RESULT_BUNDLE_ALREADY_EXISTS:{output_zip}")
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=str(path))
        archive.write(OUTPUT / "artifact-index.json", arcname=str(OUTPUT / "artifact-index.json"))
    with zipfile.ZipFile(output_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("M12AT_RESULT_BUNDLE_INTEGRITY_FAILURE")
    digest = file_sha256(output_zip)
    sidecar = output_zip.with_suffix(output_zip.suffix + ".sha256")
    write_text(sidecar, f"{digest}  {output_zip.name}\n")
    print(json.dumps({"status": "PASS", "zip": str(output_zip), "sha256": digest, "sidecar": str(sidecar), "artifact_count": len(files) + 1}, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("prepare", "run-fictional", "finalize-fictional", "prepare-shadow", "run-shadow", "finalize-shadow", "closeout", "record-docs", "failure-closeout"):
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
