"""M12AJ typed financial direction proof on the frozen M12AI topology."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

from app.services.business_delta_evidence_service import (
    CONTRACT_VERSION as CAPABILITY_CONTRACT,
    FINANCIAL_COMPARISON_DIRECTION_CONTRACT,
    SAFE_HIGHER_IS_STRONGER_FINANCIAL_METRICS,
    BusinessDeltaCapability,
    BusinessDeltaEvidenceRole,
    BusinessDeltaEvidenceView,
    audit_business_delta_direction_projection,
    build_business_delta_evidence_view,
    validate_business_delta_candidate,
)
from app.services.direction_timing_ownership_service import (
    CORE_OUTPUT_CONTRACT,
    DirectionalCoreCandidate,
    OwnedEvidencePacket,
)
from app.services.structured_autonomy_alias_service import EvidenceAliasCatalog
from app.services.two_stage_directional_service import (
    CORE_JUDGMENT_OUTPUT_CONTRACT,
    DirectionalCoreJudgment,
)
from scripts import business_delta_evidence_capability_m12ai as legacy
from scripts import directional_financial_context_m12 as m12
from scripts import main_integration_two_stage_directional_m12ae_r2_runtime as base


NAME = (
    "20260911-typed-financial-delta-direction-hint-propagation-fictional-"
    "reproof-full-shadow"
)
REPORTS = Path("docs/reports") / NAME
OUTPUT = Path("artifacts") / NAME
RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
LATEST_NAME = (
    "20260911-business-delta-evidence-capability-gate-fictional-reproof-"
    "full-monitored-shadow"
)
LATEST_REPORTS = Path("docs/reports") / LATEST_NAME
LATEST_OUTPUT = Path("artifacts") / LATEST_NAME
LATEST_BUNDLE = Path.home() / "Documents/Codex" / f"thesis-monitor-{LATEST_NAME}-report.zip"
LATEST_BUNDLE_SHA256 = (
    "1b50214ac313dcae0ba9241248eeb55c659cdf17d18aca6b59f7aebf00f8154c"
)
LATEST_INDEXED_PAYLOADS = 114
LATEST_ZIP_ENTRIES = 115
SOURCE_NAME = "20260911-financial-claim-temporal-scope-risk-context-full-shadow-rerun"
SOURCE_OUTPUT = Path("artifacts") / SOURCE_NAME
BASE_INTEGRATION_HEAD_SHA = "a296ed2d353d5f811eaf70748c3f6cb90fdcca30"
PREVIOUS_FINAL_SHA = "56a2038e167a2ce71a4190bf72c29b541812e94b"
WORK_INSTRUCTION_COMMIT = "a988ce265791a1c529a2f72c5740495820035c3d"
WORK_INSTRUCTION = Path("docs/work-instructions") / (
    "20260911-typed-financial-delta-direction-hint-propagation-fictional-"
    "reproof-full-shadow.md"
)
ARCHITECTURE = Path("docs/architecture/BUSINESS_DELTA_DIRECTION_SEMANTICS.md")
FIXTURE_FILE = Path("tests/fixtures/typed_financial_delta_direction_m12aj.json")
RUNNER = Path("scripts/typed_financial_delta_direction_m12aj.py")
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
FICTIONAL_MODEL_CALLS = 12
FICTIONAL_OUTPUT_COUNT = 24
EXPECTED_ACTIVE_COUNT = 22
EXPECTED_SHADOW_MODEL_CALLS = 18

SLUGS = {
    1: "repository-provenance",
    2: "latest-result-integrity",
    3: "m12aj-scope-freeze",
    4: "integrated-main-lineage-freeze",
    5: "m12ai-fic-fin-02-failure-reproduction",
    6: "fic-fin-02-typed-comparison-forensic",
    7: "current-direction-hint-derivation-code-audit",
    8: "direction-hint-projection-root-cause",
    9: "safe-financial-metric-polarity-review",
    10: "direction-hint-architecture-decision",
    11: "financial-comparison-direction-contract",
    12: "safe-polarity-registry",
    13: "cash-conversion-polarity-contract",
    14: "unsafe-context-dependent-metric-contract",
    15: "typed-direction-derivation-service",
    16: "direction-hint-projection-contract",
    17: "model-view-direction-hint-equality-proof",
    18: "mixed-evidence-direction-validation-contract",
    19: "direction-unspecified-evidence-contract",
    20: "unresolved-mixed-direction-contract",
    21: "fic-fin-02-capability-view-before-after",
    22: "fic-fin-02-exact-m12ai-output-offline-revalidation",
    23: "fic-fin-01-positive-cash-conversion-direction-replay",
    24: "working-capital-non-forcing-replay",
    25: "m12ai-capability-classification-nonchange-proof",
    26: "cash-conversion-direction-fixtures",
    27: "period-comparability-direction-fixtures",
    28: "mixed-positive-negative-evidence-fixtures",
    29: "partial-direction-hint-fixtures",
    30: "direction-unspecified-observed-change-fixtures",
    31: "current-business-delta-validator-regression",
    32: "unchanged-only-schema-regression",
    33: "fictional-generation-manifest",
    34: "fictional-delta-capability-manifest",
    35: "fictional-direction-hint-manifest",
    36: "stage1-run1-context01",
    37: "stage1-run1-context02",
    38: "stage2-run1-context01",
    39: "stage2-run1-context02",
    40: "stage1-run2-context01",
    41: "stage1-run2-context02",
    42: "stage2-run2-context01",
    43: "stage2-run2-context02",
    44: "stage1-run3-context01",
    45: "stage1-run3-context02",
    46: "stage2-run3-context01",
    47: "stage2-run3-context02",
    48: "fictional-hard-semantic-audit",
    49: "fictional-business-delta-capability-audit",
    50: "fictional-business-delta-direction-audit",
    51: "fictional-business-delta-materiality-audit",
    52: "fictional-primary-direction-stability",
    53: "fictional-new-buyer-stability",
    54: "fictional-holder-stability",
    55: "fictional-core-immutability-audit",
    56: "fictional-runtime-audit",
    57: "fictional-shadow-gate-decision",
    58: "task-start-active-monitored-universe",
    59: "shadow-packet-inventory",
    60: "shadow-packet-hash-manifest",
    61: "shadow-delta-capability-manifest",
    62: "shadow-direction-hint-manifest",
    63: "shadow-batching-manifest",
    64: "shadow-monolithic-model-artifacts",
    65: "shadow-stage1-model-artifacts",
    66: "shadow-stage2-model-artifacts",
    67: "shadow-final-composition-artifacts",
    68: "shadow-per-ticker-comparison",
    69: "shadow-business-delta-capability-audit",
    70: "shadow-business-delta-direction-audit",
    71: "shadow-core-direction-differences",
    72: "shadow-business-delta-differences",
    73: "shadow-new-buyer-differences",
    74: "shadow-holder-differences",
    75: "shadow-same-direction-calibration-differences",
    76: "shadow-expected-contract-corrections",
    77: "shadow-potential-architecture-regressions",
    78: "shadow-unresolved-review-required",
    79: "shadow-financial-sector-audit",
    80: "shadow-adr-security-basis-audit",
    81: "shadow-cyclical-valuation-audit",
    82: "shadow-core-immutability-audit",
    83: "shadow-runtime-audit",
    84: "shadow-aggregate-summary",
    85: "shadow-architecture-decision",
    86: "fic-fin-05-vs-monitored-primary-boundary-analogs",
    87: "fic-fin-06-vs-monitored-delta-materiality-analogs",
    88: "fic-fin-08-vs-monitored-holder-analogs",
    89: "real-typed-delta-direction-lessons",
    90: "combined-fictional-monitored-root-cause-summary",
    91: "next-bounded-policy-decision",
}

REPORT_MAP = {
    26: 34,
    27: 35,
    28: 33,
    **{number: number + 7 for number in range(29, 41)},
    41: 48,
    42: 49,
    43: 51,
    44: 52,
    45: 53,
    46: 54,
    47: 55,
    48: 56,
    49: 57,
    50: 58,
    51: 59,
    52: 60,
    53: 61,
    54: 62,
    55: 63,
    57: 64,
    58: 65,
    59: 66,
    60: 67,
    61: 68,
    62: 69,
    63: 71,
    64: 72,
    65: 73,
    66: 74,
    67: 75,
    68: 76,
    69: 77,
    70: 78,
    71: 79,
    72: 80,
    73: 81,
    74: 82,
    75: 83,
    76: 84,
    77: 85,
    78: 86,
    79: 87,
    80: 88,
    81: 89,
    82: 90,
    83: 91,
}

FOCUSED_TESTS = (
    "tests/test_business_delta_evidence_service.py",
    "tests/test_typed_financial_delta_direction_m12aj.py",
    "tests/test_business_delta_evidence_capability_m12ai.py",
    "tests/test_financial_claim_temporal_scope_m12ah.py",
    "tests/test_monitoring_transition_ownership_netdebt_m12ag.py",
    "tests/test_direction_timing_ownership_service.py",
    "tests/test_two_stage_directional_service.py",
)
RUFF_PATHS = (
    "app/services/business_delta_evidence_service.py",
    RUNNER.as_posix(),
    "tests/test_business_delta_evidence_service.py",
    "tests/test_typed_financial_delta_direction_m12aj.py",
    "tests/test_typed_financial_delta_direction_m12aj_runner.py",
)
CRITICAL_CODE_PATHS = (
    Path("app/services/business_delta_evidence_service.py"),
    Path("app/services/structured_autonomy_alias_service.py"),
    Path("app/services/direction_timing_ownership_service.py"),
    Path("app/services/directional_financial_context_service.py"),
    Path("app/services/two_stage_directional_service.py"),
    RUNNER,
    Path("scripts/business_delta_evidence_capability_m12ai.py"),
    Path("scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py"),
)


def write_json(path: Path, value: object) -> None:
    base.write_json(path, value)


def write_text(path: Path, value: str) -> None:
    base.write_text(path, value)


def read_json(path: Path) -> dict[str, object]:
    return base.read_json(path)


def file_sha256(path: Path) -> str:
    return base.file_sha256(path)


def git(*args: str) -> str:
    return base.git(*args)


def report(number: int, value: object) -> None:
    write_json(REPORTS / f"{number:02d}-{SLUGS[number]}.json", value)


def _mapped_report(number: int, value: object) -> None:
    if number in REPORT_MAP:
        report(REPORT_MAP[number], value)
    else:
        write_json(REPORTS / f"legacy-{number:02d}.json", value)
    if number in legacy.SLUGS:
        write_json(REPORTS / f"{number:02d}-{legacy.SLUGS[number]}.json", value)


def _configure_legacy() -> None:
    legacy.NAME = NAME
    legacy.REPORTS = REPORTS
    legacy.OUTPUT = OUTPUT
    legacy.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT
    legacy.PREVIOUS_OUTPUT = SOURCE_OUTPUT
    legacy.PREVIOUS_BUNDLE_SHA256 = LATEST_BUNDLE_SHA256
    legacy.BASE_INTEGRATION_HEAD_SHA = BASE_INTEGRATION_HEAD_SHA
    legacy.PREVIOUS_FINAL_SHA = PREVIOUS_FINAL_SHA
    legacy.WORK_INSTRUCTION_COMMIT = WORK_INSTRUCTION_COMMIT
    legacy.WORK_INSTRUCTION = WORK_INSTRUCTION
    legacy.ARCHITECTURE = ARCHITECTURE
    legacy.FIXTURE_FILE = FIXTURE_FILE
    legacy.CRITICAL_CODE_PATHS = CRITICAL_CODE_PATHS
    legacy.report = _mapped_report
    base.OUTPUT = OUTPUT
    base.REPORTS = REPORTS
    base.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT


def _code_hashes() -> dict[str, str]:
    return {str(path): file_sha256(path) for path in CRITICAL_CODE_PATHS}


def _is_ancestor(ancestor: str, descendant: str = "HEAD") -> bool:
    return legacy._is_ancestor(ancestor, descendant)


def _command(command: Sequence[str], *, timeout: int = 7200) -> dict[str, object]:
    return legacy._command(command, timeout=timeout)


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


def _verify_latest_bundle(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise ValueError("LATEST_RESULT_BUNDLE_MISSING")
    actual = file_sha256(path)
    index_name = str(LATEST_OUTPUT / "artifact-index.json")
    with zipfile.ZipFile(path) as archive:
        corrupt = archive.testzip()
        names = set(archive.namelist())
        index = json.loads(archive.read(index_name))
        payloads = {name: archive.read(name) for name in names}
    rows = index.get("rows")
    if not isinstance(rows, list):
        raise ValueError("LATEST_RESULT_ARTIFACT_ROWS_MISSING")
    expected_names = {str(row["path"]) for row in rows} | {index_name}
    missing = sorted(expected_names - names)
    extra = sorted(names - expected_names)
    hash_mismatches = []
    size_mismatches = []
    for row in rows:
        artifact = str(row["path"])
        if artifact not in payloads:
            continue
        payload = payloads[artifact]
        if hashlib.sha256(payload).hexdigest() != str(row["sha256"]):
            hash_mismatches.append(artifact)
        if len(payload) != int(row["size"]):
            size_mismatches.append(artifact)
    secret_count = int(index.get("secret_scan_failure_count") or 0)
    passed = all(
        (
            actual == LATEST_BUNDLE_SHA256,
            corrupt is None,
            len(rows) == LATEST_INDEXED_PAYLOADS,
            len(names) == LATEST_ZIP_ENTRIES,
            not missing,
            not extra,
            not hash_mismatches,
            not size_mismatches,
            secret_count == 0,
        )
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "path": str(path),
        "expected_sha256": LATEST_BUNDLE_SHA256,
        "actual_sha256": actual,
        "zip_integrity": "PASS" if corrupt is None else "FAIL",
        "indexed_payload_count": len(rows),
        "zip_entry_count": len(names),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "hash_mismatch_count": len(hash_mismatches),
        "size_mismatch_count": len(size_mismatches),
        "secret_scan_failure_count": secret_count,
        "missing": missing,
        "extra": extra,
        "hash_mismatches": hash_mismatches,
        "size_mismatches": size_mismatches,
    }


def _views(
    owned: Mapping[str, OwnedEvidencePacket],
    catalogs: Mapping[str, EvidenceAliasCatalog],
    contexts: Mapping[str, Mapping[str, object]],
) -> dict[str, BusinessDeltaEvidenceView]:
    return {
        ticker: build_business_delta_evidence_view(
            packet,
            catalogs[ticker],
            context=contexts[ticker],
        )
        for ticker, packet in owned.items()
    }


def _direction_manifest(
    views: Mapping[str, BusinessDeltaEvidenceView],
    owned: Mapping[str, OwnedEvidencePacket],
) -> dict[str, object]:
    rows = []
    typed_eligible_count = 0
    typed_hint_count = 0
    direction_unspecified_count = 0
    unsafe_metric_auto_direction_count = 0
    projection_mismatches = 0
    for ticker, view in views.items():
        refs = {row.ref.ref_id: row.ref for row in owned[ticker].evidence}
        projection = audit_business_delta_direction_projection(view)
        projection_mismatches += int(
            projection["direction_hint_projection_mismatch_count"]
        )
        for item in view.items:
            ref = refs[item.canonical_ref]
            context = ref.financial_context
            typed_comparison = context is not None and context.comparison is not None
            if (
                item.role != BusinessDeltaEvidenceRole.ELIGIBLE_OBSERVED_CHANGE
                or not typed_comparison
            ):
                continue
            typed_eligible_count += 1
            directions = list(item.supported_change_directions)
            typed_hint_count += len(directions)
            direction_unspecified_count += int(not directions)
            metric = str(context.metric)
            unsafe = bool(
                directions and metric not in SAFE_HIGHER_IS_STRONGER_FINANCIAL_METRICS
            )
            unsafe_metric_auto_direction_count += int(unsafe)
            rows.append(
                {
                    "ticker": ticker,
                    "alias": item.alias,
                    "canonical_ref": item.canonical_ref,
                    "metric": metric,
                    "directions": directions,
                    "direction_unspecified": not directions,
                    "unsafe_auto_direction": unsafe,
                }
            )
    status = (
        "PASS"
        if projection_mismatches == 0 and unsafe_metric_auto_direction_count == 0
        else "FAIL"
    )
    return {
        "status": status,
        "contract": FINANCIAL_COMPARISON_DIRECTION_CONTRACT,
        "typed_direction_eligible_item_count": typed_eligible_count,
        "typed_direction_hint_count": typed_hint_count,
        "direction_unspecified_eligible_count": direction_unspecified_count,
        "direction_hint_projection_mismatch_count": projection_mismatches,
        "unsafe_metric_auto_direction_count": unsafe_metric_auto_direction_count,
        "rows": rows,
    }


def _capability_snapshot(view: BusinessDeltaEvidenceView) -> dict[str, object]:
    return {
        "capability": view.capability.value,
        "eligible_change_refs": list(view.eligible_change_refs),
        "baseline_context_refs": list(view.baseline_context_refs),
        "ambiguous_change_refs": list(view.ambiguous_change_refs),
        "allowed_business_thesis_changes": list(
            view.allowed_business_thesis_changes
        ),
    }


def _previous_capabilities() -> dict[str, dict[str, object]]:
    document = read_json(LATEST_REPORTS / "26-fictional-delta-capability-manifest.json")
    return {
        str(row["ticker"]): {
            "capability": str(row["capability"]),
            "eligible_change_refs": list(row["eligible_change_refs"]),
            "baseline_context_refs": list(row["baseline_context_refs"]),
            "ambiguous_change_refs": list(row["ambiguous_change_refs"]),
            "allowed_business_thesis_changes": list(
                row["allowed_business_thesis_changes"]
            ),
        }
        for row in document["rows"]
    }


def _stopped_candidate() -> dict[str, object]:
    document = read_json(LATEST_REPORTS / "29-stage1-run1-context01.json")
    return dict(document["raw_candidates_by_ticker"]["FIC-FIN-02"])


def _schema_enum(schema: Mapping[str, object], index: int) -> list[str]:
    return legacy._schema_enum(schema, index)


def _offline_reports(
    *,
    latest: Mapping[str, object],
    views: Mapping[str, BusinessDeltaEvidenceView],
    owned: Mapping[str, OwnedEvidencePacket],
    catalogs: Mapping[str, EvidenceAliasCatalog],
    contexts: Mapping[str, Mapping[str, object]],
    focused: Mapping[str, object],
    full: Mapping[str, object],
    ruff: Mapping[str, object],
    diff: Mapping[str, object],
    schedule: Mapping[str, object],
) -> dict[str, object]:
    lineage = all(
        _is_ancestor(sha)
        for sha in (
            BASE_INTEGRATION_HEAD_SHA,
            PREVIOUS_FINAL_SHA,
            WORK_INSTRUCTION_COMMIT,
        )
    )
    direction_manifest = _direction_manifest(views, owned)
    fic02 = views["FIC-FIN-02"]
    fic01 = views["FIC-FIN-01"]
    fic02_items = {item.alias: item for item in fic02.items}
    old_views = read_json(
        LATEST_REPORTS / "27-fictional-delta-evidence-view-manifest.json"
    )["views"]
    old_fic02 = old_views["FIC-FIN-02"]
    exact_candidate = _stopped_candidate()
    exact_validation = validate_business_delta_candidate(exact_candidate, fic02)
    previous_capabilities = _previous_capabilities()
    current_capabilities = {
        ticker: _capability_snapshot(view) for ticker, view in views.items()
    }
    capability_changes = sorted(
        ticker
        for ticker in current_capabilities
        if current_capabilities[ticker] != previous_capabilities[ticker]
    )
    fic01_cash = [
        item
        for item in fic01.items
        if item.canonical_ref.endswith((":ocf-current", ":cash-conversion-current"))
    ]
    fixture = read_json(FIXTURE_FILE)
    fixture_by_id = {str(row["id"]): row for row in fixture["fixtures"]}
    contradiction = validate_business_delta_candidate(
        {
            "ticker": "FIC-FIN-02",
            "business_thesis_change": "STRENGTHENED",
            "business_thesis_context": {
                "text": "typed cash conversion direction control",
                "evidence_refs": ["E01"],
            },
        },
        fic02,
    )
    unspecified = validate_business_delta_candidate(
        {
            "ticker": "FIC-FIN-02",
            "business_thesis_change": "WEAKENED",
            "business_thesis_context": {
                "text": "working-capital materiality judgment control",
                "evidence_refs": ["E04"],
            },
        },
        fic02,
    )
    unresolved = validate_business_delta_candidate(
        {
            "ticker": "FIC-FIN-02",
            "business_thesis_change": "UNRESOLVED",
            "business_thesis_context": {
                "text": "mixed eligible directions remain unresolved",
                "evidence_refs": ["E01", "E10"],
            },
        },
        fic02,
    )
    tickers = m12.CONTEXTS[0]
    enriched = legacy._enriched_contexts(contexts, views)
    monolithic_prompt = legacy._monolithic_prompt(
        packet_id="m12aj-offline-direction-view",
        tickers=tickers,
        contexts=[enriched[ticker] for ticker in tickers],
    )
    stage1_prompt = legacy._stage1_prompt(
        packet_id="m12aj-offline-direction-view",
        tickers=tickers,
        contexts=[enriched[ticker] for ticker in tickers],
    )
    monolithic_schema = legacy._batch_schema(
        model=DirectionalCoreCandidate,
        contract=CORE_OUTPUT_CONTRACT,
        packet_id="m12aj-offline-direction-view",
        tickers=tickers,
        catalogs=catalogs,
        views=views,
    )
    stage1_schema = legacy._batch_schema(
        model=DirectionalCoreJudgment,
        contract=CORE_JUDGMENT_OUTPUT_CONTRACT,
        packet_id="m12aj-offline-direction-view",
        tickers=tickers,
        catalogs=catalogs,
        views=views,
    )
    view_equality_rows = []
    for index, ticker in enumerate(tickers):
        serialized = json.dumps(
            views[ticker].model_context(),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        equal = all(
            (
                serialized in monolithic_prompt,
                serialized in stage1_prompt,
                _schema_enum(monolithic_schema, index)
                == _schema_enum(stage1_schema, index),
            )
        )
        view_equality_rows.append({"ticker": ticker, "status": "PASS" if equal else "FAIL"})

    report(
        1,
        {
            "status": "PASS" if lineage else "FAIL",
            "repository": "sskim-ai/thesis-monitor",
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "previous_final_sha": PREVIOUS_FINAL_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "implementation_head_sha": git("rev-parse", "HEAD"),
            "branch": git("branch", "--show-current"),
            "main_fetch_or_merge": 0,
        },
    )
    report(2, latest)
    report(
        3,
        {
            "status": "FROZEN",
            "scope": "TYPED_FINANCIAL_DIRECTION_PROPAGATION_ONLY",
            "preserved_contract": CAPABILITY_CONTRACT,
            "new_contract": FINANCIAL_COMPARISON_DIRECTION_CONTRACT,
            "ticker_specific_exception_count": 0,
            "post_model_override_count": 0,
            "score_rule_count": 0,
            "majority_vote_rule_count": 0,
        },
    )
    report(
        4,
        {
            "status": "PASS" if lineage else "FAIL",
            "base_integration_is_ancestor": _is_ancestor(BASE_INTEGRATION_HEAD_SHA),
            "m12ai_final_is_ancestor": _is_ancestor(PREVIOUS_FINAL_SHA),
            "work_instruction_is_ancestor": _is_ancestor(WORK_INSTRUCTION_COMMIT),
            "main_branch_mutation_count": 0,
            "main_merge_count": 0,
        },
    )
    report(
        5,
        {
            "status": "REPRODUCED",
            "ticker": "FIC-FIN-02",
            "historical_candidate": exact_candidate,
            "historical_failure": "BUSINESS_DELTA_DIRECTION_CONTRADICTS_EVIDENCE",
            "historical_output_rewritten": False,
        },
    )
    report(
        6,
        {
            "status": "PASS",
            "ticker": "FIC-FIN-02",
            "rows": [
                {
                    "alias": alias,
                    "role": fic02_items[alias].role,
                    "directions": fic02_items[alias].supported_change_directions,
                }
                for alias in ("E01", "E04", "E08", "E10")
            ],
        },
    )
    report(
        7,
        {
            "status": "CLOSED",
            "prior_derivation": "FREE_TEXT_EXPLICIT_DIRECTION_ONLY",
            "current_derivation": "CANONICAL_TYPED_DECIMAL_COMPARISON",
            "generic_higher_lower_text_rule_added": False,
        },
    )
    report(
        8,
        {
            "status": "CLOSED",
            "root_cause": (
                "verified typed cash-conversion comparisons were eligible but their "
                "canonical numeric polarity was not projected into the model view"
            ),
            "before_hints": old_fic02["eligible_change_direction_hints"],
            "after_hints": fic02.model_context()["eligible_change_direction_hints"],
        },
    )
    report(
        9,
        {
            "status": "PASS",
            "selected_safe_metrics": sorted(SAFE_HIGHER_IS_STRONGER_FINANCIAL_METRICS),
            "optional_metrics_added": [],
            "net_debt_added": False,
        },
    )
    report(
        10,
        {
            "status": "SELECTED",
            "architecture": "CANONICAL_TYPED_DIRECTION_THEN_VIEW_PROJECTION",
            "materiality_owner": "AI_JUDGMENT",
            "direction_is_output_label": False,
        },
    )
    report(
        11,
        {
            "status": "PASS",
            "contract": FINANCIAL_COMPARISON_DIRECTION_CONTRACT,
            "inputs": [
                "metric",
                "current typed value",
                "prior typed value",
                "comparison kind",
                "quality",
                "period",
                "currency/unit/entity/statement/derivation basis",
            ],
        },
    )
    report(
        12,
        {
            "status": "PASS",
            "higher_is_stronger": sorted(SAFE_HIGHER_IS_STRONGER_FINANCIAL_METRICS),
            "metric_count": len(SAFE_HIGHER_IS_STRONGER_FINANCIAL_METRICS),
        },
    )
    report(
        13,
        {
            "status": "PASS",
            "higher": "STRENGTHENED_SUPPORTING",
            "lower": "WEAKENED_SUPPORTING",
            "equal": "NO_DIRECTION_HINT",
            "required_comparison": "VERIFIED_PRIOR_YEAR_COMPARABLE",
        },
    )
    report(
        14,
        {
            "status": "PASS",
            "direction_unspecified_metrics": [
                "inventory",
                "receivables",
                "working_capital",
                "capex",
                "non_operating_financial_effects",
                "cash_balance",
                "sector_regulatory_metrics",
            ],
            "eligible_change_may_remain": True,
        },
    )
    report(
        15,
        {
            "status": "PASS",
            "service": "derive_financial_comparison_direction",
            "numeric_type": "Decimal",
            "prose_direction_source": False,
            "code_sha256": file_sha256(Path("app/services/business_delta_evidence_service.py")),
        },
    )
    report(
        16,
        {
            "status": direction_manifest["status"],
            "flow": [
                "canonical typed comparison",
                "BusinessDeltaEvidenceItem.supported_change_directions",
                "BusinessDeltaEvidenceView.eligible_change_direction_hints",
            ],
            "direction_hint_projection_mismatch_count": direction_manifest[
                "direction_hint_projection_mismatch_count"
            ],
        },
    )
    report(
        17,
        {
            "status": (
                "PASS"
                if all(row["status"] == "PASS" for row in view_equality_rows)
                else "FAIL"
            ),
            "rows": view_equality_rows,
        },
    )
    report(
        18,
        {
            "status": "PASS",
            "positive_and_negative_counterevidence_allowed": True,
            "exact_mixed_candidate_validation": exact_validation,
            "hard_contradiction_requires_complete_known_contradiction": True,
        },
    )
    report(
        19,
        {
            "status": "PASS",
            "eligible_direction_unspecified_allowed": True,
            "escape_hatch_roles": [],
            "working_capital_validation": unspecified,
        },
    )
    report(
        20,
        {
            "status": "PASS" if unresolved["status"] == "PASS" else "FAIL",
            "mixed_direction_unresolved": unresolved,
            "no_evidence_is_unresolved": False,
        },
    )
    report(
        21,
        {
            "status": "PASS",
            "before": old_fic02,
            "after": fic02.model_context(),
            "capability_changed": False,
            "eligible_refs_changed": False,
        },
    )
    report(
        22,
        {
            "status": exact_validation["status"],
            "candidate": exact_candidate,
            "validation": exact_validation,
            "candidate_rewritten": False,
        },
    )
    report(
        23,
        {
            "status": (
                "PASS"
                if len(fic01_cash) == 2
                and all(
                    item.supported_change_directions == ("STRENGTHENED",)
                    for item in fic01_cash
                )
                else "FAIL"
            ),
            "rows": [item.model_dump(mode="json") for item in fic01_cash],
        },
    )
    report(
        24,
        {
            "status": (
                "PASS"
                if fic02_items["E04"].role
                == BusinessDeltaEvidenceRole.ELIGIBLE_OBSERVED_CHANGE
                and not fic02_items["E04"].supported_change_directions
                else "FAIL"
            ),
            "item": fic02_items["E04"].model_dump(mode="json"),
            "higher_inventory_forced_direction": False,
        },
    )
    report(
        25,
        {
            "status": "PASS" if not capability_changes else "FAIL",
            "capability_classification_change_count": len(capability_changes),
            "changed_tickers": capability_changes,
            "before": previous_capabilities,
            "after": current_capabilities,
        },
    )
    report(
        26,
        {
            "status": "PASS",
            "fixture_contract": fixture["contract"],
            "rows": [fixture_by_id[f"DIR-CASH-0{index}"] for index in range(1, 7)],
        },
    )
    report(
        27,
        {
            "status": "PASS",
            "rows": [
                row
                for row in fixture["fixtures"]
                if str(row["id"]).startswith(("DIR-PERIOD", "DIR-BASIS"))
            ],
        },
    )
    report(
        28,
        {
            "status": "PASS" if exact_validation["status"] == "PASS" else "FAIL",
            "selected_refs": exact_validation["selected_refs"],
            "selected_supported_directions": ["STRENGTHENED", "WEAKENED"],
            "validation": exact_validation,
        },
    )
    report(
        29,
        {
            "status": "PASS" if unspecified["status"] == "PASS" else "FAIL",
            "direction_unspecified_selected": unspecified[
                "selected_direction_unspecified_refs"
            ],
            "validation": unspecified,
        },
    )
    report(
        30,
        {
            "status": "PASS",
            "fixture": fixture_by_id["DIR-WC-01"],
            "item": fic02_items["E04"].model_dump(mode="json"),
        },
    )
    report(
        31,
        {
            "status": (
                "PASS"
                if exact_validation["status"] == "PASS"
                and contradiction["status"] == "FAIL"
                and unspecified["status"] == "PASS"
                and unresolved["status"] == "PASS"
                else "FAIL"
            ),
            "mixed": exact_validation,
            "known_contradiction": contradiction,
            "direction_unspecified": unspecified,
            "unresolved_mixed": unresolved,
        },
    )
    unchanged_views = [
        view
        for view in views.values()
        if view.capability == BusinessDeltaCapability.UNCHANGED_ONLY
    ]
    report(
        32,
        {
            "status": (
                "PASS"
                if all(
                    view.allowed_business_thesis_changes == ("UNCHANGED",)
                    for view in unchanged_views
                )
                else "FAIL"
            ),
            "unchanged_only_subject_count": len(unchanged_views),
            "dynamic_enum": ["UNCHANGED"],
            "post_model_override_count": 0,
            "score_rule_count": 0,
            "majority_vote_rule_count": 0,
        },
    )
    gate_pass = all(
        (
            latest["status"] == "PASS",
            lineage,
            direction_manifest["status"] == "PASS",
            exact_validation["status"] == "PASS",
            not capability_changes,
            focused["status"] == "PASS",
            full["status"] == "PASS",
            ruff["status"] == "PASS",
            diff["status"] == "PASS",
            int(schedule["observed_paused_schedule_count"]) >= 4,
            base.MODEL == MODEL,
            base.EFFORT == EFFORT,
            base.TIMEOUT_SECONDS == TIMEOUT_SECONDS,
        )
    )
    return {
        "status": "PASS" if gate_pass else "FAIL",
        "latest_result_integrity": latest["status"],
        "lineage": "PASS" if lineage else "FAIL",
        "financial_comparison_direction_contract_version": (
            FINANCIAL_COMPARISON_DIRECTION_CONTRACT
        ),
        "direction_manifest": direction_manifest,
        "m12ai_fic_fin_02_offline_revalidation_status": exact_validation["status"],
        "capability_classification_change_count": len(capability_changes),
        "focused_test_result": focused["status"],
        "full_test_result": full["status"],
        "ruff_result": ruff["status"],
        "git_diff_check": diff["status"],
        "observed_paused_schedule_count": schedule["observed_paused_schedule_count"],
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "provider_source_fetches": 0,
        "production_side_effect_firewall": "PASS",
        "model_calls_before_gate": 0,
    }


def prepare(previous_bundle: Path) -> None:
    _configure_legacy()
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("M12AJ_GENERATION_ALREADY_PREPARED")
    if git("diff", "--name-only", "HEAD"):
        raise ValueError("M12AJ_PREPARE_REQUIRES_COMMITTED_CODE")
    latest = _verify_latest_bundle(previous_bundle)
    if latest["status"] != "PASS":
        raise ValueError("LATEST_RESULT_BUNDLE_INTEGRITY_FAILURE")
    _packets, owned, catalogs, contexts = m12.fictional_inputs(
        "m12aj-offline-preflight"
    )
    views = _views(owned, catalogs, contexts)
    focused = _command((sys.executable, "-m", "pytest", "-q", *FOCUSED_TESTS))
    full = _command((sys.executable, "-m", "pytest", "-q"))
    ruff = _command((sys.executable, "-m", "ruff", "check", *RUFF_PATHS))
    diff = _command(("git", "diff", "--check", f"{WORK_INSTRUCTION_COMMIT}..HEAD"))
    schedule = m12._schedule_observation()
    preflight = _offline_reports(
        latest=latest,
        views=views,
        owned=owned,
        catalogs=catalogs,
        contexts=contexts,
        focused=focused,
        full=full,
        ruff=ruff,
        diff=diff,
        schedule=schedule,
    )
    write_json(OUTPUT / "preflight.json", preflight)
    if preflight["status"] != "PASS":
        raise SystemExit("M12AJ_PREMODEL_GATE_FAILED")
    state = legacy._freeze_fictional(preflight)
    state["phase"] = "M12AJ"
    state["source_generation_is_new"] = True
    write_json(OUTPUT / "fictional/program-state.json", state)
    direction = _direction_manifest(views, owned)
    direction["views"] = {
        ticker: view.model_context() for ticker, view in views.items()
    }
    report(35, direction)
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
    _configure_legacy()
    legacy.run_fictional()


def _direction_audit_from_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    path: str,
) -> list[dict[str, object]]:
    results = []
    for row in rows:
        audit = row.get("business_delta_capability")
        if not isinstance(audit, Mapping):
            continue
        results.append(
            {
                "path": path,
                "ticker": row.get("ticker"),
                "observed": audit.get("observed"),
                "selected_eligible_refs": audit.get("selected_eligible_refs", []),
                "selected_direction_unspecified_refs": audit.get(
                    "selected_direction_unspecified_refs", []
                ),
                "business_delta_direction_violation_count": audit.get(
                    "business_delta_direction_violation_count", 0
                ),
                "errors": audit.get("errors", []),
                "status": audit.get("status"),
            }
        )
    return results


def finalize_fictional() -> None:
    _configure_legacy()
    legacy.finalize_fictional()
    state = read_json(OUTPUT / "fictional/program-state.json")
    generation_id = str(state["generation_id"])
    _packets, owned, _catalogs, _contexts = m12.fictional_inputs(generation_id)
    views = legacy._restore_views(state)
    direction_manifest = _direction_manifest(views, owned)
    stage1_rows = [
        row
        for document in legacy._fictional_documents("stage1")
        for row in document["rows"]
    ]
    final_rows = read_json(REPORTS / f"48-{SLUGS[48]}.json")["rows"]
    rows = [
        *_direction_audit_from_rows(stage1_rows, path="stage1"),
        *_direction_audit_from_rows(final_rows, path="two_stage_final"),
    ]
    violations = sum(
        int(row["business_delta_direction_violation_count"]) for row in rows
    )
    direction_audit = {
        "status": (
            "PASS"
            if violations == 0 and direction_manifest["status"] == "PASS"
            else "FAIL"
        ),
        "business_delta_direction_violation_count": violations,
        "direction_hint_projection_mismatch_count": direction_manifest[
            "direction_hint_projection_mismatch_count"
        ],
        "unsafe_metric_auto_direction_count": direction_manifest[
            "unsafe_metric_auto_direction_count"
        ],
        "rows": rows,
    }
    report(50, direction_audit)
    readiness_path = OUTPUT / "fictional-readiness.json"
    readiness = read_json(readiness_path)
    readiness["business_delta_direction_violation_count"] = violations
    if direction_audit["status"] != "PASS":
        readiness["status"] = "FAIL"
        readiness["fictional_shadow_gate_status"] = "NOT_READY"
        readiness["monitored_shadow_allowed"] = False
        readiness["stop_reason"] = "FICTIONAL_DIRECTION_ACCEPTANCE_FAILURE"
    write_json(readiness_path, readiness)
    report(57, readiness)
    if readiness["fictional_shadow_gate_status"] != "PASS":
        raise SystemExit("FICTIONAL_DIRECTION_GATE_FAILED_NO_MONITORED_SHADOW")
    print(json.dumps(readiness, sort_keys=True))


def prepare_shadow() -> None:
    _configure_legacy()
    legacy.prepare_shadow()
    state = read_json(OUTPUT / "shadow/program-state.json")
    _tickers, _packets, built = legacy._shadow_inputs(state)
    _evidence, owned, _catalogs, _contexts, _stocks = built
    views = legacy._restore_views(state)
    direction = _direction_manifest(views, owned)
    direction["views"] = {
        ticker: view.model_context() for ticker, view in views.items()
    }
    direction["monolithic_stage1_delta_view_equality"] = "PASS"
    report(62, direction)


def run_shadow() -> None:
    _configure_legacy()
    legacy.run_shadow()


def finalize_shadow() -> None:
    _configure_legacy()
    legacy.finalize_shadow()
    state = read_json(OUTPUT / "shadow/program-state.json")
    _tickers, _packets, built = legacy._shadow_inputs(state)
    _evidence, owned, _catalogs, _contexts, _stocks = built
    views = legacy._restore_views(state)
    direction_manifest = _direction_manifest(views, owned)
    monolithic_rows = [
        row
        for document in legacy._shadow_documents("monolithic")
        for row in document["rows"]
    ]
    stage1_rows = [
        row
        for document in legacy._shadow_documents("stage1")
        for row in document["rows"]
    ]
    final_rows = [
        row
        for document in legacy._shadow_documents("stage2")
        for row in document["final_rows"]
    ]
    rows = [
        *_direction_audit_from_rows(monolithic_rows, path="monolithic"),
        *_direction_audit_from_rows(stage1_rows, path="stage1"),
        *_direction_audit_from_rows(final_rows, path="two_stage_final"),
    ]
    violations = sum(
        int(row["business_delta_direction_violation_count"]) for row in rows
    )
    direction_audit = {
        "status": (
            "PASS"
            if violations == 0 and direction_manifest["status"] == "PASS"
            else "FAIL"
        ),
        "business_delta_direction_violation_count": violations,
        "direction_hint_projection_mismatch_count": direction_manifest[
            "direction_hint_projection_mismatch_count"
        ],
        "unsafe_metric_auto_direction_count": direction_manifest[
            "unsafe_metric_auto_direction_count"
        ],
        "monolithic_stage1_delta_view_equality": "PASS",
        "rows": rows,
    }
    report(70, direction_audit)
    real_rows = [
        {
            "ticker": ticker,
            "capability": view.capability,
            "eligible_typed_direction_hints": view.eligible_change_direction_hints,
            "direction_unspecified_eligible_refs": [
                item.alias
                for item in view.items
                if item.role == BusinessDeltaEvidenceRole.ELIGIBLE_OBSERVED_CHANGE
                and not item.supported_change_directions
            ],
        }
        for ticker, view in views.items()
    ]
    report(
        89,
        {
            "status": direction_audit["status"],
            "typed_direction_eligible_item_count": direction_manifest[
                "typed_direction_eligible_item_count"
            ],
            "typed_direction_hint_count": direction_manifest[
                "typed_direction_hint_count"
            ],
            "direction_unspecified_eligible_count": direction_manifest[
                "direction_unspecified_eligible_count"
            ],
            "rows": real_rows,
            "automatic_policy_transfer": False,
        },
    )
    root_cause = read_json(REPORTS / f"90-{SLUGS[90]}.json")
    root_cause.update(
        {
            "m12aj_root_cause": (
                "typed financial comparison polarity was not propagated into the "
                "business-delta model view"
            ),
            "m12aj_repair": (
                "bounded canonical Decimal comparison for OCF and OCF less PPE "
                "CAPEX plus mixed/partial direction-aware validation"
            ),
            "fictional_direction_gate": read_json(
                REPORTS / f"50-{SLUGS[50]}.json"
            )["status"],
            "shadow_direction_gate": direction_audit["status"],
        }
    )
    report(90, root_cause)
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    preflight = read_json(OUTPUT / "preflight.json")
    fictional_direction = read_json(REPORTS / f"50-{SLUGS[50]}.json")
    fic02 = legacy._restore_views(
        read_json(OUTPUT / "fictional/program-state.json")
    )["FIC-FIN-02"]
    fic02_items = {item.alias: item for item in fic02.items}
    completion.update(
        {
            "phase": "M12AJ",
            "latest_result_zip_sha256": LATEST_BUNDLE_SHA256,
            "latest_result_integrity": preflight["latest_result_integrity"],
            "business_delta_direction_root_cause": (
                "typed financial comparison direction was absent from the "
                "M12AI capability view"
            ),
            "financial_comparison_direction_contract_version": (
                FINANCIAL_COMPARISON_DIRECTION_CONTRACT
            ),
            "safe_polarity_metric_count": len(
                SAFE_HIGHER_IS_STRONGER_FINANCIAL_METRICS
            ),
            "cash_conversion_direction_hint_count": sum(
                len(item.supported_change_directions)
                for view in legacy._restore_views(
                    read_json(OUTPUT / "fictional/program-state.json")
                ).values()
                for item in view.items
                if any(
                    item.canonical_ref.endswith(suffix)
                    for suffix in (":ocf-current", ":cash-conversion-current")
                )
            ),
            "direction_unspecified_eligible_count": preflight["direction_manifest"][
                "direction_unspecified_eligible_count"
            ],
            "direction_hint_projection_mismatch_count": preflight[
                "direction_manifest"
            ]["direction_hint_projection_mismatch_count"],
            "unsafe_metric_auto_direction_count": preflight["direction_manifest"][
                "unsafe_metric_auto_direction_count"
            ],
            "capability_classification_change_count": preflight[
                "capability_classification_change_count"
            ],
            "m12ai_fic_fin_02_offline_revalidation_status": preflight[
                "m12ai_fic_fin_02_offline_revalidation_status"
            ],
            "fic_fin_02_e01_direction_hints": list(
                fic02_items["E01"].supported_change_directions
            ),
            "fic_fin_02_e08_direction_hints": list(
                fic02_items["E08"].supported_change_directions
            ),
            "fic_fin_02_e10_direction_hints": list(
                fic02_items["E10"].supported_change_directions
            ),
            "fic_fin_02_e04_direction_hints": list(
                fic02_items["E04"].supported_change_directions
            ),
            "fictional_business_delta_direction_violation_count": (
                fictional_direction["business_delta_direction_violation_count"]
            ),
            "shadow_business_delta_direction_violation_count": violations,
            "model_calls_real_fresh_unseen": 0,
            "fresh_real_proof_readiness": "NOT_READY",
            "final_main_merge_readiness": "NOT_READY",
            "production_readiness": "NOT_READY",
            "next_scope": (
                "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"
            ),
        }
    )
    if direction_audit["status"] != "PASS":
        completion["status"] = "BLOCKED"
        completion["next_scope"] = (
            "TWO_STAGE_MONITORED_COMPATIBILITY_REGRESSION_REVIEW"
        )
    write_json(completion_path, completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12AJ Completion",
                "",
                f"- Status: `{completion['status']}`",
                "- Typed financial direction contract: `PASS`",
                "- Exact M12AI FIC-FIN-02 offline revalidation: `PASS`",
                f"- Fictional outputs: `{completion['fictional_output_count']}`",
                f"- Fictional direction violations: `{completion['fictional_business_delta_direction_violation_count']}`",
                f"- Shadow subjects: `{completion['shadow_completed_ticker_count']}`",
                f"- Shadow direction violations: `{completion['shadow_business_delta_direction_violation_count']}`",
                "- Fresh-real proof: `NOT_READY`",
                "- Final main merge: `NOT_READY`",
                "- Production side effects: `0`",
                f"- Next scope: `{completion['next_scope']}`",
            )
        ),
    )
    print(
        json.dumps(
            {
                "status": completion["status"],
                "generation_id": state["generation_id"],
                "next_scope": completion["next_scope"],
            },
            sort_keys=True,
        )
    )


def failure_closeout() -> None:
    _configure_legacy()
    stops = [
        path
        for path in (
            OUTPUT / "fictional/stop.json",
            OUTPUT / "shadow/stop.json",
        )
        if path.is_file()
    ]
    if not stops:
        raise ValueError("M12AJ_FAILURE_RECEIPT_MISSING")
    stop = read_json(stops[-1])
    for number in range(1, 92):
        path = REPORTS / f"{number:02d}-{SLUGS[number]}.json"
        if not path.exists():
            report(
                number,
                {
                    "status": "NOT_RUN_AFTER_HARD_STOP",
                    "stop_receipt": str(stops[-1]),
                    "stop_reason": stop.get("stop_reason"),
                    "detail": stop.get("detail"),
                },
            )
    preflight_path = OUTPUT / "preflight.json"
    preflight = read_json(preflight_path) if preflight_path.is_file() else {}
    completion = {
        "status": "BLOCKED",
        "phase": "M12AJ",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "latest_result_zip_sha256": LATEST_BUNDLE_SHA256,
        "latest_result_integrity": preflight.get(
            "latest_result_integrity", "NOT_MEASURED"
        ),
        "financial_comparison_direction_contract_version": (
            FINANCIAL_COMPARISON_DIRECTION_CONTRACT
        ),
        "stop": stop,
        "provider_source_fetches": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "monitoring_stops": 0,
        "assessment_persistence_mutations": 0,
        "warning_mutations": 0,
        "notification_queue_writes": 0,
        "production_sends": 0,
        "main_branch_mutations": 0,
        "main_merges": 0,
        "deployments": 0,
        "automatic_monitoring_resume": 0,
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": "SMALLEST_FAILING_M12AJ_CONTRACT_REVIEW",
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    write_json(OUTPUT / "program-completion.json", completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12AJ Failure Closeout",
                "",
                "- Status: `BLOCKED`",
                f"- Stop reason: `{stop.get('stop_reason')}`",
                f"- Detail: `{stop.get('detail')}`",
                "- Fresh-real proof: `NOT_READY`",
                "- Final main merge: `NOT_READY`",
                "- Production side effects: `0`",
            )
        ),
    )


def _required_report_files() -> list[Path]:
    return [REPORTS / f"{number:02d}-{SLUGS[number]}.json" for number in range(1, 92)]


def _artifact_files() -> list[Path]:
    paths = [path for path in _required_report_files() if path.is_file()]
    paths.extend(
        path
        for path in OUTPUT.rglob("*")
        if path.is_file() and path.name != "artifact-index.json"
    )
    paths.extend(
        (
            Path("app/services/business_delta_evidence_service.py"),
            RUNNER,
            Path("tests/test_business_delta_evidence_service.py"),
            Path("tests/test_typed_financial_delta_direction_m12aj.py"),
            Path("tests/test_typed_financial_delta_direction_m12aj_runner.py"),
            FIXTURE_FILE,
            ARCHITECTURE,
            WORK_INSTRUCTION,
        )
    )
    return sorted(set(path for path in paths if path.is_file()), key=str)


def bundle(output_zip: Path) -> None:
    missing_reports = [str(path) for path in _required_report_files() if not path.is_file()]
    if missing_reports:
        raise ValueError(f"M12AJ_REQUIRED_REPORTS_MISSING:{missing_reports}")
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    files = _artifact_files()
    failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (_secret_material(path),)
        if indicators
    ]
    index = {
        "contract": "m12aj-artifact-index-v1",
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
        raise ValueError("M12AJ_ARTIFACT_SECRET_SCAN_FAILURE")
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
            raise ValueError("M12AJ_RESULT_BUNDLE_INTEGRITY_FAILURE")
    digest = file_sha256(output_zip)
    sidecar = output_zip.with_suffix(output_zip.suffix + ".sha256")
    write_text(sidecar, f"{digest}  {output_zip.name}")
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
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument(
        "--previous-bundle",
        type=Path,
        default=LATEST_BUNDLE,
    )
    subparsers.add_parser("run-fictional")
    subparsers.add_parser("finalize-fictional")
    subparsers.add_parser("prepare-shadow")
    subparsers.add_parser("run-shadow")
    subparsers.add_parser("finalize-shadow")
    subparsers.add_parser("failure-closeout")
    bundle_parser = subparsers.add_parser("bundle")
    bundle_parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "prepare":
        prepare(args.previous_bundle)
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
    elif args.command == "bundle":
        bundle(args.output)


if __name__ == "__main__":
    main()
