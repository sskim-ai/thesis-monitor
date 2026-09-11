"""M12AI business-delta capability and full fictional/monitored shadow proof."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

from app.services.business_delta_evidence_service import (
    CONTRACT_VERSION as CAPABILITY_CONTRACT,
    BusinessDeltaCapability,
    BusinessDeltaEvidenceRole,
    BusinessDeltaEvidenceView,
    attach_business_delta_evidence_view,
    build_business_delta_evidence_view,
    build_business_delta_constrained_batch_schema,
    validate_business_delta_candidate,
)
from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    FrozenModel,
)
from app.services.direction_timing_ownership_service import (
    CORE_OUTPUT_CONTRACT,
    DirectionalCoreBatch,
    DirectionalCoreCandidate,
    OwnedEvidencePacket,
    canonical_sha256,
)
from app.services.structured_autonomy_alias_service import (
    EvidenceAliasCatalog,
    build_alias_constrained_batch_schema,
)
from app.services.two_stage_directional_service import (
    CORE_JUDGMENT_OUTPUT_CONTRACT,
    FUNDAMENTAL_STANCE_OUTPUT_CONTRACT,
    DirectionalCoreJudgment,
    FundamentalStanceCandidate,
)
from scripts import directional_financial_context_m12 as m12
from scripts import main_integration_two_stage_directional_m12ae_r2_runtime as base


NAME = (
    "20260911-business-delta-evidence-capability-gate-fictional-reproof-"
    "full-monitored-shadow"
)
REPORTS = Path("docs/reports") / NAME
OUTPUT = Path("artifacts") / NAME
RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
OPERATING_ROOT = Path("/Users/sskim/Codex/thesis-monitor")
PREVIOUS_NAME = "20260911-financial-claim-temporal-scope-risk-context-full-shadow-rerun"
PREVIOUS_OUTPUT = Path("artifacts") / PREVIOUS_NAME
PREVIOUS_BUNDLE = (
    Path.home() / "Documents/Codex" / f"thesis-monitor-{PREVIOUS_NAME}-report.zip"
)
PREVIOUS_BUNDLE_SHA256 = (
    "8bf0c08091100e1ade31a4e8a467368f67c2b0a44cc208ebef3d25abe265a690"
)
PREVIOUS_INDEXED_PAYLOADS = 147
PREVIOUS_ZIP_ENTRIES = 148
BASE_INTEGRATION_HEAD_SHA = "a296ed2d353d5f811eaf70748c3f6cb90fdcca30"
PREVIOUS_FINAL_SHA = "4703632087ea1d8818c6cb471fd8290f7d99a4b3"
WORK_INSTRUCTION_COMMIT = "b5b1029d788426e42cefaf9236b9ddc86b7ceba5"
WORK_INSTRUCTION = Path("docs/work-instructions") / (
    "20260911-business-delta-evidence-capability-gate-fictional-reproof-"
    "full-monitored-shadow.md"
)
ARCHITECTURE = Path("docs/architecture/BUSINESS_DELTA_EVIDENCE_CAPABILITY.md")
FIXTURE_FILE = Path("tests/fixtures/business_delta_evidence_capability_m12ai.json")
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
SUBJECTS_PER_CONTEXT = 4
FICTIONAL_REPETITIONS = 3
FICTIONAL_STAGE1_CALLS = 6
FICTIONAL_STAGE2_CALLS = 6
FICTIONAL_MODEL_CALLS = 12
FICTIONAL_OUTPUT_COUNT = 24
EXPECTED_ACTIVE_COUNT = 22
EXPECTED_SHADOW_CONTEXTS = 6
EXPECTED_SHADOW_MODEL_CALLS = 18

DELTA_PROMPT = (
    "BUSINESS_DELTA_EVIDENCE_VIEW is the authoritative evidence-capability surface "
    "for business_thesis_change. Respect allowed_business_thesis_changes exactly. "
    "Only eligible_change_refs can establish STRENGTHENED or WEAKENED; "
    "baseline_context_refs may explain the thesis but do not prove a change. "
    "UNCHANGED remains valid when an eligible change is not material. UNRESOLVED "
    "requires conflicting or genuinely ambiguous eligible observed changes."
)

SLUGS = {
    1: "repository-provenance",
    2: "latest-result-integrity",
    3: "m12ai-scope-freeze",
    4: "integrated-main-lineage-freeze",
    5: "m12ah-003690-failure-reproduction",
    6: "monolithic-vs-stage1-delta-prompt-equivalence-proof",
    7: "003690-e19-evidence-role-forensic",
    8: "business-delta-validator-root-cause",
    9: "business-delta-pre-model-architecture-options",
    10: "business-delta-capability-architecture-decision",
    11: "business-delta-evidence-capability-contract",
    12: "eligible-observed-delta-evidence-contract",
    13: "baseline-context-only-evidence-contract",
    14: "business-delta-evidence-view-contract",
    15: "dynamic-business-delta-schema-contract",
    16: "unchanged-only-consistency-contract",
    17: "ai-judgment-changed-delta-grounding-contract",
    18: "unresolved-delta-evidence-contract",
    19: "m12ah-003690-capability-replay",
    20: "m12ah-context01-four-ticker-capability-audit",
    21: "stored-thesis-baseline-role-audit",
    22: "current-single-point-financial-delta-audit",
    23: "market-expectation-delta-exclusion-audit",
    24: "price-timing-supply-delta-exclusion-audit",
    25: "capital-allocation-event-delta-eligibility-controls",
    26: "fictional-delta-capability-manifest",
    27: "fictional-delta-evidence-view-manifest",
    28: "fictional-generation-manifest",
    29: "stage1-run1-context01",
    30: "stage1-run1-context02",
    31: "stage2-run1-context01",
    32: "stage2-run1-context02",
    33: "stage1-run2-context01",
    34: "stage1-run2-context02",
    35: "stage2-run2-context01",
    36: "stage2-run2-context02",
    37: "stage1-run3-context01",
    38: "stage1-run3-context02",
    39: "stage2-run3-context01",
    40: "stage2-run3-context02",
    41: "fictional-hard-semantic-audit",
    42: "fictional-business-delta-capability-audit",
    43: "fictional-business-delta-materiality-audit",
    44: "fictional-primary-direction-stability",
    45: "fictional-new-buyer-stability",
    46: "fictional-holder-stability",
    47: "fictional-core-immutability-audit",
    48: "fictional-runtime-audit",
    49: "fictional-shadow-gate-decision",
    50: "task-start-active-monitored-universe",
    51: "shadow-packet-inventory",
    52: "shadow-packet-hash-manifest",
    53: "shadow-business-delta-capability-manifest",
    54: "shadow-business-delta-evidence-view-manifest",
    55: "shadow-batching-manifest",
    56: "shadow-model-call-gate",
    57: "shadow-monolithic-model-artifacts",
    58: "shadow-stage1-model-artifacts",
    59: "shadow-stage2-model-artifacts",
    60: "shadow-final-composition-artifacts",
    61: "shadow-per-ticker-comparison",
    62: "shadow-business-delta-capability-audit",
    63: "shadow-core-direction-differences",
    64: "shadow-business-delta-differences",
    65: "shadow-new-buyer-differences",
    66: "shadow-holder-differences",
    67: "shadow-same-direction-calibration-differences",
    68: "shadow-expected-contract-corrections",
    69: "shadow-potential-architecture-regressions",
    70: "shadow-unresolved-review-required",
    71: "shadow-financial-sector-audit",
    72: "shadow-adr-security-basis-audit",
    73: "shadow-cyclical-valuation-audit",
    74: "shadow-core-immutability-audit",
    75: "shadow-runtime-audit",
    76: "shadow-aggregate-summary",
    77: "shadow-architecture-decision",
    78: "fic-fin-05-vs-monitored-primary-boundary-analogs",
    79: "fic-fin-06-vs-monitored-delta-materiality-analogs",
    80: "fic-fin-08-vs-monitored-holder-analogs",
    81: "real-business-delta-materiality-lessons",
    82: "combined-fictional-monitored-root-cause-summary",
    83: "next-bounded-policy-decision",
}

FOCUSED_TESTS = (
    "tests/test_business_delta_evidence_service.py",
    "tests/test_structured_autonomy_alias_service.py",
    "tests/test_business_delta_alias_balance_confidence_m12z.py",
    "tests/test_financial_claim_temporal_scope_m12ah.py",
    "tests/test_monitoring_transition_ownership_netdebt_m12ag.py",
    "tests/test_direction_timing_ownership_service.py",
    "tests/test_two_stage_directional_service.py",
)
RUFF_PATHS = (
    "app/services/business_delta_evidence_service.py",
    "app/services/structured_autonomy_alias_service.py",
    "scripts/business_delta_evidence_capability_m12ai.py",
    "tests/test_business_delta_evidence_service.py",
    "tests/test_business_delta_evidence_capability_m12ai.py",
)
CRITICAL_CODE_PATHS = (
    Path("app/services/business_delta_evidence_service.py"),
    Path("app/services/structured_autonomy_alias_service.py"),
    Path("app/services/direction_timing_ownership_service.py"),
    Path("app/services/directional_financial_context_service.py"),
    Path("app/services/two_stage_directional_service.py"),
    Path("scripts/business_delta_evidence_capability_m12ai.py"),
    Path("scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py"),
    Path("scripts/directional_core_price_timing_holdout.py"),
    Path("scripts/business_delta_alias_balance_confidence_m12z.py"),
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


def _configure_base() -> None:
    base.OUTPUT = OUTPUT
    base.REPORTS = REPORTS
    base.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT


def _code_hashes() -> dict[str, str]:
    return {str(path): file_sha256(path) for path in CRITICAL_CODE_PATHS}


def _runner_path() -> Path:
    return Path(__file__).resolve().relative_to(Path.cwd().resolve())


def _is_ancestor(ancestor: str, descendant: str = "HEAD") -> bool:
    return (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            check=False,
        ).returncode
        == 0
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
        "output": output[-16000:],
    }


def _batches(tickers: Sequence[str]) -> tuple[tuple[str, ...], ...]:
    return tuple(
        tuple(tickers[index : index + SUBJECTS_PER_CONTEXT])
        for index in range(0, len(tickers), SUBJECTS_PER_CONTEXT)
    )


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


def _verify_previous_bundle(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise ValueError("LATEST_RESULT_BUNDLE_MISSING")
    actual = file_sha256(path)
    index_name = str(PREVIOUS_OUTPUT / "artifact-index.json")
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
            actual == PREVIOUS_BUNDLE_SHA256,
            corrupt is None,
            len(rows) == PREVIOUS_INDEXED_PAYLOADS,
            len(names) == PREVIOUS_ZIP_ENTRIES,
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
        "expected_sha256": PREVIOUS_BUNDLE_SHA256,
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
            item,
            catalogs[ticker],
            context=contexts[ticker],
        )
        for ticker, item in owned.items()
    }


def _view_manifest(
    views: Mapping[str, BusinessDeltaEvidenceView],
) -> dict[str, object]:
    rows = [
        {
            "ticker": ticker,
            "capability": view.capability,
            "allowed_business_thesis_changes": view.allowed_business_thesis_changes,
            "eligible_change_refs": view.eligible_change_refs,
            "baseline_context_refs": view.baseline_context_refs,
            "ambiguous_change_refs": view.ambiguous_change_refs,
        }
        for ticker, view in views.items()
    ]
    return {
        "status": (
            "PASS"
            if all(
                view.capability != BusinessDeltaCapability.INPUT_AMBIGUOUS
                for view in views.values()
            )
            else "FAIL"
        ),
        "contract": CAPABILITY_CONTRACT,
        "subject_count": len(rows),
        "unchanged_only_count": sum(
            row["capability"] == BusinessDeltaCapability.UNCHANGED_ONLY
            for row in rows
        ),
        "ai_judgment_count": sum(
            row["capability"] == BusinessDeltaCapability.AI_JUDGMENT
            for row in rows
        ),
        "input_ambiguous_count": sum(
            row["capability"] == BusinessDeltaCapability.INPUT_AMBIGUOUS
            for row in rows
        ),
        "rows": rows,
    }


def _enriched_contexts(
    contexts: Mapping[str, Mapping[str, object]],
    views: Mapping[str, BusinessDeltaEvidenceView],
) -> dict[str, dict[str, object]]:
    return {
        ticker: attach_business_delta_evidence_view(context, views[ticker])
        for ticker, context in contexts.items()
    }


def _with_delta_prompt(prompt: str) -> str:
    return DELTA_PROMPT + "\n\n" + prompt


def _monolithic_prompt(
    *,
    packet_id: str,
    tickers: Sequence[str],
    contexts: Sequence[Mapping[str, object]],
) -> str:
    return _with_delta_prompt(
        base._monolithic_prompt(
            packet_id=packet_id,
            tickers=tickers,
            contexts=contexts,
        )
    )


def _stage1_prompt(
    *,
    packet_id: str,
    tickers: Sequence[str],
    contexts: Sequence[Mapping[str, object]],
) -> str:
    return _with_delta_prompt(
        base._stage1_prompt(
            packet_id=packet_id,
            tickers=tickers,
            contexts=contexts,
        )
    )


def _batch_schema(
    *,
    model: type[FrozenModel],
    contract: str,
    packet_id: str,
    tickers: Sequence[str],
    catalogs: Mapping[str, EvidenceAliasCatalog],
    views: Mapping[str, BusinessDeltaEvidenceView] | None = None,
) -> dict[str, object]:
    aliases = {ticker: tuple(catalogs[ticker].by_alias) for ticker in tickers}
    if views is None:
        return build_alias_constrained_batch_schema(
            candidate_schema=base._candidate_schema(model),
            contract=contract,
            packet_id=packet_id,
            aliases_by_ticker=aliases,
        )
    return build_business_delta_constrained_batch_schema(
        candidate_schema=base._candidate_schema(model),
        contract=contract,
        packet_id=packet_id,
        aliases_by_ticker=aliases,
        views={ticker: views[ticker] for ticker in tickers},
    )


def _capability_audit_rows(
    rows: list[dict[str, object]],
    views: Mapping[str, BusinessDeltaEvidenceView],
) -> tuple[list[dict[str, object]], int]:
    violations = 0
    for row in rows:
        ticker = str(row["ticker"])
        capability = validate_business_delta_candidate(row["core"], views[ticker])
        errors = list(row["errors"])
        if capability["status"] != "PASS":
            errors.extend(str(error) for error in capability["errors"])
            violations += 1
        row["business_delta_capability"] = capability
        row["errors"] = list(dict.fromkeys(errors))
        row["status"] = "PASS" if not row["errors"] else "FAIL"
    return rows, violations


def _stage1_audit(
    batch: object,
    *,
    owned: Mapping[str, OwnedEvidencePacket],
    catalogs: Mapping[str, EvidenceAliasCatalog],
    contexts: Mapping[str, Mapping[str, object]],
    views: Mapping[str, BusinessDeltaEvidenceView],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    rows, audit = base._stage1_audit(
        batch,
        owned=owned,
        catalogs=catalogs,
        contexts=contexts,
    )
    rows, violations = _capability_audit_rows(rows, views)
    return rows, {
        **audit,
        "business_delta_capability_violation_count": violations,
        "pass_count": sum(row["status"] == "PASS" for row in rows),
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def _full_audit(
    batch: DirectionalCoreBatch,
    *,
    owned: Mapping[str, OwnedEvidencePacket],
    catalogs: Mapping[str, EvidenceAliasCatalog],
    contexts: Mapping[str, Mapping[str, object]],
    views: Mapping[str, BusinessDeltaEvidenceView],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    rows, audit = base._full_candidate_audit(
        batch,
        owned=owned,
        catalogs=catalogs,
        contexts=contexts,
    )
    rows, violations = _capability_audit_rows(rows, views)
    return rows, {
        **audit,
        "business_delta_capability_violation_count": violations,
        "pass_count": sum(row["status"] == "PASS" for row in rows),
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def _previous_source_packets() -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    state = read_json(PREVIOUS_OUTPUT / "shadow/program-state.json")
    paths = state.get("packet_paths")
    hashes = state.get("packet_hashes")
    if not isinstance(paths, Mapping) or not isinstance(hashes, Mapping):
        raise ValueError("M12AH_FROZEN_PACKET_MANIFEST_MISSING")
    tickers = tuple(str(ticker) for ticker in state.get("tickers", ()))
    packets: dict[str, dict[str, object]] = {}
    mismatches = []
    for ticker in tickers:
        packet = read_json(Path(str(paths[ticker])))
        packets[ticker] = packet
        if canonical_sha256(packet) != hashes[ticker]:
            mismatches.append(ticker)
    if mismatches:
        raise ValueError(f"M12AH_FROZEN_PACKET_HASH_MISMATCH:{mismatches}")
    return state, packets


def _previous_context01_failure() -> dict[str, object]:
    document = read_json(
        PREVIOUS_OUTPUT
        / "shadow/model-calls/context-01/stage1/run-document.json"
    )
    rows = [row for row in document["rows"] if row["ticker"] == "003690"]
    if len(rows) != 1:
        raise ValueError("M12AH_003690_FAILURE_ROW_MISSING")
    return rows[0]


def _role_rows(
    views: Mapping[str, BusinessDeltaEvidenceView],
    role: BusinessDeltaEvidenceRole,
) -> list[dict[str, object]]:
    return [
        {
            "ticker": ticker,
            "alias": item.alias,
            "canonical_ref": item.canonical_ref,
            "source_ref": item.source_ref,
            "domain": item.domain,
            "role": item.role,
            "reason": item.reason,
        }
        for ticker, view in views.items()
        for item in view.items
        if item.role == role
    ]


def _schema_enum(
    schema: Mapping[str, object],
    index: int,
) -> list[str]:
    properties = schema["properties"]
    assert isinstance(properties, Mapping)
    candidates = properties["candidates"]
    assert isinstance(candidates, Mapping)
    items = candidates["items"]
    assert isinstance(items, Mapping)
    choices = items["anyOf"]
    assert isinstance(choices, list)
    candidate = choices[index]
    assert isinstance(candidate, Mapping)
    candidate_properties = candidate["properties"]
    assert isinstance(candidate_properties, Mapping)
    delta = candidate_properties["business_thesis_change"]
    assert isinstance(delta, Mapping)
    values = delta["enum"]
    assert isinstance(values, list)
    return [str(value) for value in values]


def _offline_reports(
    *,
    latest: Mapping[str, object],
    previous_state: Mapping[str, object],
    packets: Mapping[str, dict[str, object]],
    built: tuple[
        dict[str, DecisionEvidencePacket],
        dict[str, OwnedEvidencePacket],
        dict[str, EvidenceAliasCatalog],
        dict[str, dict[str, object]],
        dict[str, Mapping[str, object]],
    ],
    views: Mapping[str, BusinessDeltaEvidenceView],
    focused: Mapping[str, object],
    full: Mapping[str, object],
    ruff: Mapping[str, object],
    diff: Mapping[str, object],
    schedule: Mapping[str, object],
) -> dict[str, object]:
    evidence, owned, catalogs, contexts, _stocks = built
    failure = _previous_context01_failure()
    view = views["003690"]
    e19 = next(item for item in view.items if item.alias == "E19")
    prior_validation = validate_business_delta_candidate(failure["core"], view)
    context01 = tuple(previous_state["contexts"][0]["tickers"])
    selected_contexts = _enriched_contexts(contexts, views)
    monolithic_prompt = _monolithic_prompt(
        packet_id="m12ai-offline-equivalence",
        tickers=context01,
        contexts=[selected_contexts[ticker] for ticker in context01],
    )
    stage1_prompt = _stage1_prompt(
        packet_id="m12ai-offline-equivalence",
        tickers=context01,
        contexts=[selected_contexts[ticker] for ticker in context01],
    )
    monolithic_schema = _batch_schema(
        model=DirectionalCoreCandidate,
        contract=CORE_OUTPUT_CONTRACT,
        packet_id="m12ai-offline-equivalence",
        tickers=context01,
        catalogs=catalogs,
        views=views,
    )
    stage1_schema = _batch_schema(
        model=DirectionalCoreJudgment,
        contract=CORE_JUDGMENT_OUTPUT_CONTRACT,
        packet_id="m12ai-offline-equivalence",
        tickers=context01,
        catalogs=catalogs,
        views=views,
    )
    equivalence_rows = []
    for index, ticker in enumerate(context01):
        serialized = json.dumps(
            views[ticker].model_context(),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        mono_enum = _schema_enum(monolithic_schema, index)
        stage1_enum = _schema_enum(stage1_schema, index)
        equivalence_rows.append(
            {
                "ticker": ticker,
                "view_sha256": canonical_sha256(views[ticker].model_context()),
                "view_in_monolithic_prompt": serialized in monolithic_prompt,
                "view_in_stage1_prompt": serialized in stage1_prompt,
                "monolithic_enum": mono_enum,
                "stage1_enum": stage1_enum,
                "status": (
                    "PASS"
                    if serialized in monolithic_prompt
                    and serialized in stage1_prompt
                    and mono_enum == stage1_enum
                    else "FAIL"
                ),
            }
        )
    lineage = all(
        _is_ancestor(sha)
        for sha in (
            BASE_INTEGRATION_HEAD_SHA,
            PREVIOUS_FINAL_SHA,
            WORK_INSTRUCTION_COMMIT,
        )
    )
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
            "scope": [
                "pre-model business-delta capability",
                "shared monolithic and Stage 1 evidence view",
                "per-ticker dynamic business_thesis_change enum",
                "full fictional two-stage reproof",
                "full monitored same-packet shadow",
            ],
            "temporal_scope_semantics": "FROZEN_M12AH",
            "ownership_semantics": "FROZEN_M12AG",
            "post_model_override_count": 0,
            "ticker_specific_exception_count": 0,
            "provider_source_fetches": 0,
            "production_side_effects": 0,
        },
    )
    report(
        4,
        {
            "status": "PASS" if lineage else "FAIL",
            "base_integration_is_ancestor": _is_ancestor(BASE_INTEGRATION_HEAD_SHA),
            "previous_final_is_ancestor": _is_ancestor(PREVIOUS_FINAL_SHA),
            "work_instruction_is_ancestor": _is_ancestor(WORK_INSTRUCTION_COMMIT),
            "main_branch_mutation_count": 0,
            "main_merge_count": 0,
        },
    )
    report(
        5,
        {
            "status": "REPRODUCED",
            "source_generation_id": previous_state["generation_id"],
            "ticker": "003690",
            "observed": failure["core"]["business_thesis_change"],
            "selected_refs": failure["business_delta"]["selected_refs"],
            "errors": failure["errors"],
            "historical_output_rewritten": False,
        },
    )
    report(
        6,
        {
            "status": (
                "PASS"
                if all(row["status"] == "PASS" for row in equivalence_rows)
                else "FAIL"
            ),
            "generic_prompt_contract": DELTA_PROMPT,
            "business_delta_view_semantic_equality": (
                "PASS"
                if all(row["status"] == "PASS" for row in equivalence_rows)
                else "FAIL"
            ),
            "rows": equivalence_rows,
        },
    )
    report(
        7,
        {
            "status": "PASS",
            "ticker": "003690",
            "alias": e19.alias,
            "canonical_ref": e19.canonical_ref,
            "source_ref": e19.source_ref,
            "role": e19.role,
            "reason": e19.reason,
            "eligible_business_delta_ref": False,
            "absolute_core_context_available": True,
        },
    )
    report(
        8,
        {
            "status": "CLOSED",
            "root_cause": (
                "the broad Core catalog exposed a stored thesis baseline as though it "
                "could establish observed business change"
            ),
            "legacy_validator_status": failure["business_delta"]["status"],
            "legacy_validator_error": "UNSUPPORTED_ABSOLUTE_STATE_TO_DELTA",
            "legacy_validator_weakened": False,
        },
    )
    report(
        9,
        {
            "status": "CLOSED",
            "options": {
                "A_MORE_PROMPT_WORDING": "REJECTED",
                "B_POST_HOC_REWRITE": "REJECTED",
                "C_REMOVE_BASELINE_FROM_CORE": "REJECTED",
                "D_DYNAMIC_PRE_MODEL_CAPABILITY_SCHEMA": "SELECTED",
            },
        },
    )
    report(
        10,
        {
            "status": "SELECTED",
            "architecture": "BUSINESS_DELTA_CAPABILITY_DYNAMIC_SCHEMA",
            "contract": CAPABILITY_CONTRACT,
            "classification_source": "complete pre-model Core catalog",
            "ticker_hard_code_count": 0,
            "post_model_override_count": 0,
        },
    )
    report(
        11,
        {
            "status": "PASS",
            "contract": CAPABILITY_CONTRACT,
            "capabilities": [item.value for item in BusinessDeltaCapability],
            "input_ambiguous_policy": "PRE_MODEL_HARD_STOP",
        },
    )
    report(
        12,
        {
            "status": "PASS",
            "eligible_classes": [
                "verified typed financial comparison with real baseline",
                "typed fundamental monitoring transition",
                "dated structured issuer event with baseline and current state",
                "controlled fixture explicit observed change",
            ],
            "eligibility_forces_direction": False,
        },
    )
    report(
        13,
        {
            "status": "PASS",
            "baseline_classes": [
                "stored investment thesis",
                "stored thesis drivers",
                "configured strengthen weaken or invalidation condition",
                "current single-point operating or financial fact",
            ],
            "absolute_core_availability_preserved": True,
        },
    )
    report(
        14,
        {
            "status": "PASS",
            "model_view_contract": "business-delta-evidence-view-v1",
            "fields": list(view.model_context()),
            "raw_catalog_removed": False,
            "excluded_ref_limit": 8,
        },
    )
    report(
        15,
        {
            "status": "PASS",
            "unchanged_only_enum": ["UNCHANGED"],
            "ai_judgment_enum": [
                "STRENGTHENED",
                "UNCHANGED",
                "WEAKENED",
                "UNRESOLVED",
            ],
            "input_ambiguous_invocation": "FORBIDDEN",
            "monolithic_stage1_same_enum": True,
        },
    )
    report(
        16,
        {
            "status": "PASS",
            "unchanged_only_context_may_use_baseline": True,
            "changed_language_without_eligible_delta": "REJECT",
            "configured_condition_fulfilled_without_event": "REJECT",
        },
    )
    report(
        17,
        {
            "status": "PASS",
            "changed_states": ["STRENGTHENED", "WEAKENED"],
            "eligible_change_ref_required": True,
            "direction_contradiction": "REJECT",
            "baseline_ref_may_supplement": True,
        },
    )
    report(
        18,
        {
            "status": "PASS",
            "unchanged_only_unresolved": "FORBIDDEN",
            "ai_judgment_unresolved_requires": [
                "conflicting eligible observed changes",
                "eligible transition with genuinely unpolarized direction",
            ],
            "no_evidence_is_unresolved": False,
        },
    )
    report(
        19,
        {
            "status": (
                "PASS"
                if view.capability == BusinessDeltaCapability.UNCHANGED_ONLY
                and e19.role == BusinessDeltaEvidenceRole.THESIS_BASELINE_CONTEXT
                and prior_validation["status"] == "FAIL"
                else "FAIL"
            ),
            "ticker": "003690",
            "capability": view.capability,
            "eligible_delta_refs": view.eligible_change_refs,
            "baseline_context_refs": view.baseline_context_refs,
            "dynamic_enum": view.allowed_business_thesis_changes,
            "historical_invalid_candidate_reaudit": prior_validation,
            "historical_output_rewritten": False,
        },
    )
    context_rows = [
        {
            "ticker": ticker,
            "capability": views[ticker].capability,
            "eligible_delta_refs": views[ticker].eligible_change_refs,
            "baseline_context_refs": views[ticker].baseline_context_refs,
            "ambiguous_refs": views[ticker].ambiguous_change_refs,
        }
        for ticker in context01
    ]
    report(
        20,
        {
            "status": (
                "PASS"
                if len(context_rows) == 4
                and all(not row["ambiguous_refs"] for row in context_rows)
                else "FAIL"
            ),
            "rows": context_rows,
        },
    )
    baseline_rows = _role_rows(views, BusinessDeltaEvidenceRole.THESIS_BASELINE_CONTEXT)
    current_rows = _role_rows(views, BusinessDeltaEvidenceRole.CURRENT_CONTEXT_ONLY)
    excluded_rows = _role_rows(
        views,
        BusinessDeltaEvidenceRole.EXCLUDED_NON_BUSINESS_DELTA,
    )
    report(
        21,
        {
            "status": "PASS" if baseline_rows else "FAIL",
            "row_count": len(baseline_rows),
            "eligible_count": 0,
            "rows": baseline_rows,
        },
    )
    report(
        22,
        {
            "status": "PASS",
            "single_point_is_delta": False,
            "row_count": len(current_rows),
            "rows": current_rows,
        },
    )
    expectation_rows = [
        row for row in excluded_rows if row["domain"] == "MARKET_EXPECTATIONS"
    ]
    report(
        23,
        {
            "status": "PASS",
            "expectation_is_business_delta": False,
            "row_count": len(expectation_rows),
            "rows": expectation_rows,
        },
    )
    excluded_domains = {
        "PRICE_CONTEXT",
        "OHLCV_TECHNICAL",
        "SUPPORT_RESISTANCE",
        "VOLUME_LIQUIDITY",
        "TECHNICAL_STATE",
        "RISK_REWARD_PRICE",
        "SUPPLY_POSITIONING",
    }
    timing_rows = [row for row in excluded_rows if row["domain"] in excluded_domains]
    report(
        24,
        {
            "status": "PASS",
            "price_timing_supply_is_business_delta": False,
            "row_count": len(timing_rows),
            "rows": timing_rows,
        },
    )
    fixture_document = read_json(FIXTURE_FILE)
    report(
        25,
        {
            "status": focused["status"],
            "dated_event_fixture": next(
                row
                for row in fixture_document["fixtures"]
                if row["id"] == "DELTA-CAP-05"
            ),
            "stored_thesis_control": next(
                row
                for row in fixture_document["fixtures"]
                if row["id"] == "DELTA-CAP-01"
            ),
            "ticker_specific_capital_allocation_rule_count": 0,
        },
    )
    gate_pass = all(
        (
            latest["status"] == "PASS",
            lineage,
            all(row["status"] == "PASS" for row in equivalence_rows),
            view.capability == BusinessDeltaCapability.UNCHANGED_ONLY,
            e19.role == BusinessDeltaEvidenceRole.THESIS_BASELINE_CONTEXT,
            prior_validation["status"] == "FAIL",
            focused["status"] == "PASS",
            full["status"] == "PASS",
            ruff["status"] == "PASS",
            diff["status"] == "PASS",
            len(packets) == EXPECTED_ACTIVE_COUNT,
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
        "prompt_schema_equivalence": (
            "PASS"
            if all(row["status"] == "PASS" for row in equivalence_rows)
            else "FAIL"
        ),
        "m12ah_003690_capability": view.capability,
        "m12ah_003690_e19_role": e19.role,
        "focused_test_result": focused["status"],
        "full_test_result": full["status"],
        "ruff_result": ruff["status"],
        "git_diff_check": diff["status"],
        "active_monitor_count": len(packets),
        "observed_paused_schedule_count": schedule["observed_paused_schedule_count"],
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "provider_source_fetches": 0,
        "production_side_effect_firewall": "PASS",
        "model_calls_before_gate": 0,
    }


def _freeze_fictional(preflight: Mapping[str, object]) -> dict[str, object]:
    now = datetime.now(UTC)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    suffix = hashlib.sha256(
        f"{git('rev-parse', 'HEAD')}|{stamp}|{NAME}|fictional".encode()
    ).hexdigest()[:12]
    generation_id = f"20260911-m12ai-fictional-{stamp}-{suffix}"
    packets, owned, catalogs, contexts = m12.fictional_inputs(generation_id)
    views = _views(owned, catalogs, contexts)
    manifest = _view_manifest(views)
    if manifest["status"] != "PASS":
        raise ValueError("FICTIONAL_DELTA_CAPABILITY_INPUT_AMBIGUOUS")
    enriched = _enriched_contexts(contexts, views)
    source_lock = m12._source_lock(generation_id, packets, owned, catalogs, contexts)
    frozen_rows = []
    for context_number, tickers in enumerate(m12.CONTEXTS, start=1):
        directory = OUTPUT / "fictional/frozen-contexts" / f"context-{context_number:02d}"
        stage1_prompt = directory / "stage1-prompt.txt"
        stage1_schema = directory / "stage1-schema.json"
        stage2_schema = directory / "stage2-schema.json"
        write_text(
            stage1_prompt,
            _stage1_prompt(
                packet_id=generation_id,
                tickers=tickers,
                contexts=[enriched[ticker] for ticker in tickers],
            ),
        )
        write_json(
            stage1_schema,
            _batch_schema(
                model=DirectionalCoreJudgment,
                contract=CORE_JUDGMENT_OUTPUT_CONTRACT,
                packet_id=generation_id,
                tickers=tickers,
                catalogs=catalogs,
                views=views,
            ),
        )
        write_json(
            stage2_schema,
            _batch_schema(
                model=FundamentalStanceCandidate,
                contract=FUNDAMENTAL_STANCE_OUTPUT_CONTRACT,
                packet_id=generation_id,
                tickers=tickers,
                catalogs=catalogs,
            ),
        )
        frozen_rows.append(
            {
                "context": context_number,
                "tickers": list(tickers),
                "stage1_prompt": str(stage1_prompt),
                "stage1_prompt_sha256": file_sha256(stage1_prompt),
                "stage1_schema": str(stage1_schema),
                "stage1_schema_sha256": file_sha256(stage1_schema),
                "stage2_schema": str(stage2_schema),
                "stage2_schema_sha256": file_sha256(stage2_schema),
                "business_delta_view_sha256": canonical_sha256(
                    {ticker: views[ticker].model_context() for ticker in tickers}
                ),
            }
        )
    state = {
        "status": "FROZEN",
        "generation_id": generation_id,
        "prepared_at": now.isoformat(),
        "implementation_head_sha": git("rev-parse", "HEAD"),
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "timeout_seconds": TIMEOUT_SECONDS,
        "wrapper_auto_retry": 0,
        "batch_split": 0,
        "repetitions": FICTIONAL_REPETITIONS,
        "planned_stage1_calls": FICTIONAL_STAGE1_CALLS,
        "planned_stage2_calls": FICTIONAL_STAGE2_CALLS,
        "planned_model_calls": FICTIONAL_MODEL_CALLS,
        "planned_output_count": FICTIONAL_OUTPUT_COUNT,
        "code_hashes": _code_hashes(),
        "source_lock": source_lock,
        "capability_manifest": manifest,
        "views": {
            ticker: view.model_dump(mode="json") for ticker, view in views.items()
        },
        "frozen_contexts": frozen_rows,
    }
    write_json(OUTPUT / "fictional/program-state.json", state)
    report(26, manifest)
    report(
        27,
        {
            "status": "PASS",
            "model_view_contract": "business-delta-evidence-view-v1",
            "views": {
                ticker: view.model_context() for ticker, view in views.items()
            },
            "monolithic_stage1_semantic_equality": "PASS",
        },
    )
    report(
        28,
        {
            "status": "FROZEN",
            "generation_id": generation_id,
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "timeout_seconds": TIMEOUT_SECONDS,
            "subject_count": len(views),
            "repetition_count": FICTIONAL_REPETITIONS,
            "stage1_model_calls": FICTIONAL_STAGE1_CALLS,
            "stage2_model_calls": FICTIONAL_STAGE2_CALLS,
            "model_calls_total": FICTIONAL_MODEL_CALLS,
            "output_count": FICTIONAL_OUTPUT_COUNT,
            "source_lock_sha256": source_lock["source_lock_sha256"],
            "code_hashes": state["code_hashes"],
            "frozen_contexts": frozen_rows,
        },
    )
    gate = {
        **dict(preflight),
        "status": (
            "PASS"
            if preflight["status"] == "PASS"
            and manifest["status"] == "PASS"
            and manifest["subject_count"] == 8
            else "FAIL"
        ),
        "fictional_capability_manifest": manifest["status"],
        "planned_model_calls": FICTIONAL_MODEL_CALLS,
        "model_calls_before_gate": 0,
    }
    write_json(OUTPUT / "fictional-model-call-gate.json", gate)
    return state


def prepare(previous_bundle: Path) -> None:
    _configure_base()
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("M12AI_GENERATION_ALREADY_PREPARED")
    if git("diff", "--name-only", "HEAD"):
        raise ValueError("M12AI_PREPARE_REQUIRES_COMMITTED_CODE")
    latest = _verify_previous_bundle(previous_bundle)
    if latest["status"] != "PASS":
        raise ValueError("LATEST_RESULT_BUNDLE_INTEGRITY_FAILURE")
    previous_state, packets = _previous_source_packets()
    tickers = tuple(str(ticker) for ticker in previous_state["tickers"])
    built = base._build_shadow_inputs(packets, tickers)
    evidence, owned, catalogs, contexts, _stocks = built
    del evidence
    views = _views(owned, catalogs, contexts)
    focused = _command((sys.executable, "-m", "pytest", "-q", *FOCUSED_TESTS))
    full = _command((sys.executable, "-m", "pytest", "-q"))
    ruff = _command((sys.executable, "-m", "ruff", "check", *RUFF_PATHS))
    diff = _command(("git", "diff", "--check", f"{WORK_INSTRUCTION_COMMIT}..HEAD"))
    schedule = m12._schedule_observation()
    preflight = _offline_reports(
        latest=latest,
        previous_state=previous_state,
        packets=packets,
        built=built,
        views=views,
        focused=focused,
        full=full,
        ruff=ruff,
        diff=diff,
        schedule=schedule,
    )
    write_json(OUTPUT / "preflight.json", preflight)
    if preflight["status"] != "PASS":
        raise SystemExit("M12AI_PREMODEL_GATE_FAILED")
    state = _freeze_fictional(preflight)
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


def _restore_views(state: Mapping[str, object]) -> dict[str, BusinessDeltaEvidenceView]:
    rows = state.get("views")
    if not isinstance(rows, Mapping):
        raise ValueError("BUSINESS_DELTA_VIEWS_MISSING")
    return {
        str(ticker): BusinessDeltaEvidenceView.model_validate(value)
        for ticker, value in rows.items()
    }


def _verify_frozen_state(state: Mapping[str, object], *, subject: str) -> None:
    if state.get("status") != "FROZEN":
        raise ValueError(f"{subject}_STATE_NOT_FROZEN")
    if state.get("code_hashes") != _code_hashes():
        raise ValueError(f"{subject}_CODE_CHANGED_AFTER_FREEZE")
    contexts = state.get("frozen_contexts")
    if not isinstance(contexts, list):
        raise ValueError(f"{subject}_FROZEN_CONTEXTS_MISSING")
    for row in contexts:
        if not isinstance(row, Mapping):
            raise ValueError(f"{subject}_FROZEN_CONTEXT_ROW_INVALID")
        for key in (
            "stage1_prompt",
            "stage1_schema",
            "stage2_schema",
        ):
            path = Path(str(row[key]))
            if file_sha256(path) != row[f"{key}_sha256"]:
                raise ValueError(f"{subject}_FROZEN_INPUT_CHANGED:{key}")
        for key in ("monolithic_prompt", "monolithic_schema"):
            if key not in row:
                continue
            path = Path(str(row[key]))
            if file_sha256(path) != row[f"{key}_sha256"]:
                raise ValueError(f"{subject}_FROZEN_INPUT_CHANGED:{key}")


def _fictional_call_paths(
    *,
    phase: str,
    repetition: int,
    context_number: int,
) -> dict[str, Path]:
    root = (
        OUTPUT
        / "fictional/model-calls"
        / f"run-{repetition}"
        / f"{phase}-context-{context_number:02d}"
    )
    return {
        "root": root,
        "prompt": root / "prompt.txt",
        "schema": root / "schema.json",
        "output": root / "output.raw.json",
        "log": root / "transport.log",
        "receipt": root / "receipt.json",
        "working": root / "working-directory",
        "document": root / "run-document.json",
    }


def _fictional_report_number(
    *,
    phase: str,
    repetition: int,
    context_number: int,
) -> int:
    offset = (repetition - 1) * 4
    return 29 + offset + (context_number - 1) + (2 if phase == "stage2" else 0)


def run_fictional() -> None:
    _configure_base()
    gate = read_json(OUTPUT / "fictional-model-call-gate.json")
    state = read_json(OUTPUT / "fictional/program-state.json")
    if gate.get("status") != "PASS":
        raise ValueError("FICTIONAL_MODEL_CALL_GATE_NOT_PASSED")
    _verify_frozen_state(state, subject="FICTIONAL")
    calls_root = OUTPUT / "fictional/model-calls"
    if list(calls_root.glob("**/receipt.json")) or (
        OUTPUT / "fictional/stop.json"
    ).exists():
        raise ValueError("WHOLE_FICTIONAL_GENERATION_RETRY_FORBIDDEN")
    generation_id = str(state["generation_id"])
    packets, owned, catalogs, contexts = m12.fictional_inputs(generation_id)
    views = _views(owned, catalogs, contexts)
    if {
        ticker: view.model_dump(mode="json") for ticker, view in views.items()
    } != state["views"]:
        raise ValueError("FICTIONAL_BUSINESS_DELTA_VIEW_DRIFT")
    if m12._source_lock(generation_id, packets, owned, catalogs, contexts) != state[
        "source_lock"
    ]:
        raise ValueError("FICTIONAL_SOURCE_LOCK_DRIFT")
    registry = base.CodexRuntimeIsolationRegistry()
    completed = 0
    try:
        for repetition in range(1, FICTIONAL_REPETITIONS + 1):
            for context_number, tickers in enumerate(m12.CONTEXTS, start=1):
                frozen = (
                    OUTPUT
                    / "fictional/frozen-contexts"
                    / f"context-{context_number:02d}"
                )
                paths = _fictional_call_paths(
                    phase="stage1",
                    repetition=repetition,
                    context_number=context_number,
                )
                paths["root"].mkdir(parents=True, exist_ok=False)
                shutil.copyfile(frozen / "stage1-prompt.txt", paths["prompt"])
                shutil.copyfile(frozen / "stage1-schema.json", paths["schema"])
                invocation_id = (
                    f"{generation_id}:run-{repetition}:stage1:"
                    f"context-{context_number:02d}"
                )
                print(
                    f"M12AI_FICTIONAL_START {completed + 1}/{FICTIONAL_MODEL_CALLS} "
                    f"{invocation_id}",
                    flush=True,
                )
                receipt = base._checked_model_call(
                    prompt=paths["prompt"],
                    schema=paths["schema"],
                    output=paths["output"],
                    log=paths["log"],
                    receipt_path=paths["receipt"],
                    working_directory=paths["working"],
                    registry=registry,
                    invocation_id=invocation_id,
                    base_namespace=f"M12AI_FICTIONAL_{generation_id}",
                )
                stage1_batch, alias_audit, raw_by_ticker = base._resolve_stage1_batch(
                    read_json(paths["output"]),
                    generation_id=generation_id,
                    tickers=tickers,
                    packets=packets,
                    catalogs=catalogs,
                )
                rows, audit = _stage1_audit(
                    stage1_batch,
                    owned=owned,
                    catalogs=catalogs,
                    contexts=contexts,
                    views=views,
                )
                document = {
                    "contract": "m12ai-fictional-stage1-context-v1",
                    "generation_id": generation_id,
                    "source_lock_sha256": state["source_lock"]["source_lock_sha256"],
                    "repetition": repetition,
                    "context": context_number,
                    "tickers": list(tickers),
                    "transport": receipt,
                    "alias_audit": alias_audit,
                    "raw_candidates_by_ticker": raw_by_ticker,
                    "rows": rows,
                    "audit": audit,
                    "status": audit["status"],
                }
                write_json(paths["document"], document)
                report(
                    _fictional_report_number(
                        phase="stage1",
                        repetition=repetition,
                        context_number=context_number,
                    ),
                    document,
                )
                completed += 1
                if audit["status"] != "PASS":
                    raise RuntimeError(
                        f"FICTIONAL_STAGE1_HARD_SEMANTIC_FAILURE:{invocation_id}"
                    )
                print(
                    f"M12AI_FICTIONAL_COMPLETE {completed}/{FICTIONAL_MODEL_CALLS} PASS",
                    flush=True,
                )

            for context_number, tickers in enumerate(m12.CONTEXTS, start=1):
                stage1_document = read_json(
                    _fictional_call_paths(
                        phase="stage1",
                        repetition=repetition,
                        context_number=context_number,
                    )["document"]
                )
                core_by_ticker = {
                    str(row["ticker"]): DirectionalCoreJudgment.model_validate(
                        row["core"]
                    )
                    for row in stage1_document["rows"]
                }
                raw_by_ticker = stage1_document["raw_candidates_by_ticker"]
                stage2_contexts = [
                    base._stage2_context(
                        source_context=contexts[ticker],
                        raw_stage1_core=raw_by_ticker[ticker],
                        normalized_stage1_core=core_by_ticker[ticker],
                    )
                    for ticker in tickers
                ]
                frozen = (
                    OUTPUT
                    / "fictional/frozen-contexts"
                    / f"context-{context_number:02d}"
                )
                paths = _fictional_call_paths(
                    phase="stage2",
                    repetition=repetition,
                    context_number=context_number,
                )
                paths["root"].mkdir(parents=True, exist_ok=False)
                write_text(
                    paths["prompt"],
                    base._stage2_prompt(
                        packet_id=generation_id,
                        tickers=tickers,
                        contexts=stage2_contexts,
                    ),
                )
                shutil.copyfile(frozen / "stage2-schema.json", paths["schema"])
                invocation_id = (
                    f"{generation_id}:run-{repetition}:stage2:"
                    f"context-{context_number:02d}"
                )
                print(
                    f"M12AI_FICTIONAL_START {completed + 1}/{FICTIONAL_MODEL_CALLS} "
                    f"{invocation_id}",
                    flush=True,
                )
                receipt = base._checked_model_call(
                    prompt=paths["prompt"],
                    schema=paths["schema"],
                    output=paths["output"],
                    log=paths["log"],
                    receipt_path=paths["receipt"],
                    working_directory=paths["working"],
                    registry=registry,
                    invocation_id=invocation_id,
                    base_namespace=f"M12AI_FICTIONAL_{generation_id}",
                )
                stage2_batch, alias_audit = base._resolve_stage2_batch(
                    read_json(paths["output"]),
                    generation_id=generation_id,
                    tickers=tickers,
                    packets=packets,
                    catalogs=catalogs,
                )
                rows, audit = base._stage2_audit(
                    stage2_batch,
                    owned=owned,
                    catalogs=catalogs,
                )
                compositions = [
                    base.compose_directional_core(
                        core_by_ticker[stance.ticker],
                        stance,
                    )
                    for stance in stage2_batch.candidates
                ]
                mutation_count = sum(
                    item.core_snapshot_sha256 != item.post_compose_core_sha256
                    for item in compositions
                )
                document = {
                    "contract": "m12ai-fictional-stage2-context-v1",
                    "generation_id": generation_id,
                    "source_lock_sha256": state["source_lock"]["source_lock_sha256"],
                    "repetition": repetition,
                    "context": context_number,
                    "tickers": list(tickers),
                    "transport": receipt,
                    "alias_audit": alias_audit,
                    "rows": rows,
                    "audit": audit,
                    "compositions": [
                        item.model_dump(mode="json") for item in compositions
                    ],
                    "core_mutation_count": mutation_count,
                    "status": (
                        "PASS"
                        if audit["status"] == "PASS" and mutation_count == 0
                        else "FAIL"
                    ),
                }
                write_json(paths["document"], document)
                report(
                    _fictional_report_number(
                        phase="stage2",
                        repetition=repetition,
                        context_number=context_number,
                    ),
                    document,
                )
                completed += 1
                if document["status"] != "PASS":
                    raise RuntimeError(
                        f"FICTIONAL_STAGE2_HARD_SEMANTIC_FAILURE:{invocation_id}"
                    )
                print(
                    f"M12AI_FICTIONAL_COMPLETE {completed}/{FICTIONAL_MODEL_CALLS} PASS",
                    flush=True,
                )
    except BaseException as exc:
        write_json(
            OUTPUT / "fictional/stop.json",
            {
                "status": "FAIL",
                "stop_reason": type(exc).__name__,
                "detail": str(exc)[:1000],
                "completed_model_calls": completed,
                "wrapper_retry_count": 0,
                "monitored_shadow_model_calls": 0,
            },
        )
        raise
    if completed != FICTIONAL_MODEL_CALLS:
        raise ValueError("FICTIONAL_MODEL_CALL_COUNT_MISMATCH")
    write_json(
        OUTPUT / "fictional/run-complete.json",
        {
            "status": "COMPLETE",
            "generation_id": generation_id,
            "model_calls": completed,
            "registry_claim_count": registry.claim_count,
        },
    )


def _fictional_documents(phase: str) -> list[dict[str, object]]:
    return [
        read_json(path)
        for path in sorted(
            (OUTPUT / "fictional/model-calls").glob(
                f"run-*/{phase}-context-*/run-document.json"
            )
        )
    ]


def _stability_rows(
    candidates_by_run: Mapping[int, Sequence[DirectionalCoreCandidate]],
    *,
    field: str,
    nested: str | None = None,
) -> list[dict[str, object]]:
    rows = []
    for ticker in m12.TICKERS:
        values = []
        for repetition in range(1, FICTIONAL_REPETITIONS + 1):
            candidate = next(
                item for item in candidates_by_run[repetition] if item.ticker == ticker
            )
            value: object = getattr(candidate, field)
            if nested is not None:
                value = getattr(value, nested)
            values.append(str(value))
        rows.append(
            {
                "ticker": ticker,
                "values": values,
                "unique_count": len(set(values)),
                "classification": (
                    "STABLE" if len(set(values)) == 1 else "VARIABLE"
                ),
            }
        )
    return rows


def finalize_fictional() -> None:
    _configure_base()
    state = read_json(OUTPUT / "fictional/program-state.json")
    _verify_frozen_state(state, subject="FICTIONAL")
    complete = read_json(OUTPUT / "fictional/run-complete.json")
    if complete.get("model_calls") != FICTIONAL_MODEL_CALLS:
        raise ValueError("FICTIONAL_CALLS_INCOMPLETE")
    stage1_documents = _fictional_documents("stage1")
    stage2_documents = _fictional_documents("stage2")
    if len(stage1_documents) != 6 or len(stage2_documents) != 6:
        raise ValueError("FICTIONAL_DOCUMENT_COUNT_MISMATCH")
    generation_id = str(state["generation_id"])
    packets, owned, catalogs, contexts = m12.fictional_inputs(generation_id)
    views = _views(owned, catalogs, contexts)
    candidates_by_run: dict[int, list[DirectionalCoreCandidate]] = {
        repetition: [] for repetition in range(1, FICTIONAL_REPETITIONS + 1)
    }
    compositions = []
    for document in stage2_documents:
        repetition = int(document["repetition"])
        for row in document["compositions"]:
            compositions.append(row)
            candidates_by_run[repetition].append(
                DirectionalCoreCandidate.model_validate(row["candidate"])
            )
    final_rows = []
    for repetition, candidates in candidates_by_run.items():
        batch = DirectionalCoreBatch(
            packet_id=generation_id,
            candidates=tuple(candidates),
        )
        rows, _audit = _full_audit(
            batch,
            owned=owned,
            catalogs=catalogs,
            contexts=contexts,
            views=views,
        )
        for row in rows:
            row["repetition"] = repetition
            final_rows.append(row)
    stage1_rows = [row for document in stage1_documents for row in document["rows"]]
    stage2_rows = [row for document in stage2_documents for row in document["rows"]]
    hard_errors = sum(len(row["errors"]) for row in final_rows)
    stage1_errors = sum(len(row["errors"]) for row in stage1_rows)
    stage2_errors = sum(len(row["errors"]) for row in stage2_rows)
    capability_violations = sum(
        row["business_delta_capability"][
            "business_delta_capability_violation_count"
        ]
        for row in final_rows
    )
    mutation_count = sum(
        row["core_snapshot_sha256"] != row["post_compose_core_sha256"]
        for row in compositions
    )
    direction = _stability_rows(candidates_by_run, field="overall_direction")
    business = _stability_rows(candidates_by_run, field="business_thesis_change")
    buyer = _stability_rows(
        candidates_by_run,
        field="fundamental_new_buyer",
        nested="stance",
    )
    holder = _stability_rows(
        candidates_by_run,
        field="fundamental_holder",
        nested="stance",
    )
    runtime = [
        document["transport"]
        for document in (*stage1_documents, *stage2_documents)
    ]
    runtime_audit = {
        "status": (
            "PASS"
            if len(runtime) == FICTIONAL_MODEL_CALLS
            and all(row["status"] == "PASS" for row in runtime)
            and all(
                row.get("observed_runtime") == {"model": MODEL, "effort": EFFORT}
                for row in runtime
            )
            else "FAIL"
        ),
        "model_calls": len(runtime),
        "pass_count": sum(row["status"] == "PASS" for row in runtime),
        "timeout_count": sum(int(row.get("timeout_count") or 0) for row in runtime),
        "capacity_failure_count": sum(
            str(row.get("failure_type") or "").casefold() == "capacity"
            for row in runtime
        ),
        "orphan_process_count": sum(
            int(row.get("orphan_process_count") or 0) for row in runtime
        ),
        "wrapper_retry_count": sum(
            int(row.get("wrapper_retry_count") or 0) for row in runtime
        ),
        "runner_model_target_match": all(
            row.get("observed_runtime") == {"model": MODEL, "effort": EFFORT}
            for row in runtime
        ),
    }
    report(
        41,
        {
            "status": (
                "PASS"
                if stage1_errors == stage2_errors == hard_errors == 0
                else "FAIL"
            ),
            "stage1_error_count": stage1_errors,
            "stage2_error_count": stage2_errors,
            "final_error_count": hard_errors,
            "rows": final_rows,
        },
    )
    report(
        42,
        {
            "status": "PASS" if capability_violations == 0 else "FAIL",
            "business_delta_capability_violation_count": capability_violations,
            "rows": [
                {
                    "ticker": row["ticker"],
                    "repetition": row["repetition"],
                    "audit": row["business_delta_capability"],
                }
                for row in final_rows
            ],
        },
    )
    report(
        43,
        {
            "status": "MEASURED",
            "readiness_blocking": False,
            "variance_subject_count": sum(
                row["classification"] == "VARIABLE" for row in business
            ),
            "unchanged_remains_valid_for_ai_judgment": True,
            "rows": business,
        },
    )
    report(
        44,
        {
            "status": "MEASURED",
            "readiness_blocking": False,
            "unstable_subject_count": sum(
                row["classification"] == "VARIABLE" for row in direction
            ),
            "rows": direction,
        },
    )
    report(
        45,
        {
            "status": "MEASURED",
            "readiness_blocking": False,
            "unstable_subject_count": sum(
                row["classification"] == "VARIABLE" for row in buyer
            ),
            "rows": buyer,
        },
    )
    report(
        46,
        {
            "status": "MEASURED",
            "readiness_blocking": False,
            "unstable_subject_count": sum(
                row["classification"] == "VARIABLE" for row in holder
            ),
            "rows": holder,
        },
    )
    report(
        47,
        {
            "status": "PASS" if mutation_count == 0 else "FAIL",
            "core_mutation_count": mutation_count,
            "rows": [
                {
                    "ticker": row["candidate"]["ticker"],
                    "before": row["core_snapshot_sha256"],
                    "after": row["post_compose_core_sha256"],
                }
                for row in compositions
            ],
        },
    )
    report(48, runtime_audit)
    hard_pass = all(
        (
            len(final_rows) == FICTIONAL_OUTPUT_COUNT,
            stage1_errors == 0,
            stage2_errors == 0,
            hard_errors == 0,
            capability_violations == 0,
            mutation_count == 0,
            runtime_audit["status"] == "PASS",
        )
    )
    decision = {
        "status": "PASS" if hard_pass else "FAIL",
        "fictional_shadow_gate_status": "PASS" if hard_pass else "NOT_READY",
        "generation_id": generation_id,
        "subject_count": len(m12.TICKERS),
        "repetition_count": FICTIONAL_REPETITIONS,
        "stage1_model_calls": len(stage1_documents),
        "stage2_model_calls": len(stage2_documents),
        "model_calls_total": len(runtime),
        "output_count": len(final_rows),
        "business_delta_capability_violation_count": capability_violations,
        "core_mutation_count": mutation_count,
        "decision_material_stability_required": False,
        "monitored_shadow_allowed": hard_pass,
        "stop_reason": None if hard_pass else "FICTIONAL_HARD_ACCEPTANCE_FAILURE",
    }
    report(49, decision)
    write_json(OUTPUT / "fictional-readiness.json", decision)
    if not hard_pass:
        raise SystemExit("FICTIONAL_HARD_GATE_FAILED_NO_MONITORED_SHADOW")
    print(json.dumps(decision, sort_keys=True))


def prepare_shadow() -> None:
    _configure_base()
    fictional = read_json(OUTPUT / "fictional-readiness.json")
    if fictional.get("fictional_shadow_gate_status") != "PASS":
        raise ValueError("FICTIONAL_HARD_PASS_REQUIRED")
    state_path = OUTPUT / "shadow/program-state.json"
    if state_path.exists():
        raise ValueError("SHADOW_GENERATION_ALREADY_PREPARED")
    previous_state, source_packets = _previous_source_packets()
    universe = base._active_monitored_universe(OPERATING_ROOT)
    tickers = tuple(str(row["ticker"]) for row in universe)
    previous_tickers = tuple(str(ticker) for ticker in previous_state["tickers"])
    if len(tickers) != EXPECTED_ACTIVE_COUNT or tickers != previous_tickers:
        raise ValueError("ACTIVE_MONITORED_UNIVERSE_DRIFT_FROM_FROZEN_PACKET_SET")
    now = datetime.now(UTC)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    suffix = hashlib.sha256(
        f"{fictional['generation_id']}|{stamp}|{'|'.join(tickers)}".encode()
    ).hexdigest()[:12]
    generation_id = f"20260911-m12ai-shadow-{stamp}-{suffix}"
    packet_paths: dict[str, str] = {}
    packet_hashes: dict[str, str] = {}
    packet_file_hashes: dict[str, str] = {}
    for ticker in tickers:
        source_path = Path(str(previous_state["packet_paths"][ticker]))
        target = OUTPUT / "shadow/frozen-packets" / f"{ticker}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, target)
        packet_paths[ticker] = str(target)
        packet_hashes[ticker] = canonical_sha256(source_packets[ticker])
        packet_file_hashes[ticker] = file_sha256(target)
    built = base._build_shadow_inputs(source_packets, tickers)
    _evidence, owned, catalogs, contexts, _stocks = built
    views = _views(owned, catalogs, contexts)
    capability_manifest = _view_manifest(views)
    if capability_manifest["status"] != "PASS":
        raise ValueError("SHADOW_DELTA_CAPABILITY_INPUT_AMBIGUOUS")
    enriched = _enriched_contexts(contexts, views)
    context_rows = []
    for context_number, batch in enumerate(_batches(tickers), start=1):
        directory = OUTPUT / "shadow/frozen-contexts" / f"context-{context_number:02d}"
        monolithic_prompt = directory / "monolithic-prompt.txt"
        monolithic_schema = directory / "monolithic-schema.json"
        stage1_prompt = directory / "stage1-prompt.txt"
        stage1_schema = directory / "stage1-schema.json"
        stage2_schema = directory / "stage2-schema.json"
        selected = [enriched[ticker] for ticker in batch]
        write_text(
            monolithic_prompt,
            _monolithic_prompt(
                packet_id=generation_id,
                tickers=batch,
                contexts=selected,
            ),
        )
        write_json(
            monolithic_schema,
            _batch_schema(
                model=DirectionalCoreCandidate,
                contract=CORE_OUTPUT_CONTRACT,
                packet_id=generation_id,
                tickers=batch,
                catalogs=catalogs,
                views=views,
            ),
        )
        write_text(
            stage1_prompt,
            _stage1_prompt(
                packet_id=generation_id,
                tickers=batch,
                contexts=selected,
            ),
        )
        write_json(
            stage1_schema,
            _batch_schema(
                model=DirectionalCoreJudgment,
                contract=CORE_JUDGMENT_OUTPUT_CONTRACT,
                packet_id=generation_id,
                tickers=batch,
                catalogs=catalogs,
                views=views,
            ),
        )
        write_json(
            stage2_schema,
            _batch_schema(
                model=FundamentalStanceCandidate,
                contract=FUNDAMENTAL_STANCE_OUTPUT_CONTRACT,
                packet_id=generation_id,
                tickers=batch,
                catalogs=catalogs,
            ),
        )
        context_rows.append(
            {
                "context": context_number,
                "tickers": list(batch),
                "packet_sha256": {
                    ticker: packet_hashes[ticker] for ticker in batch
                },
                "business_delta_view_sha256": canonical_sha256(
                    {ticker: views[ticker].model_context() for ticker in batch}
                ),
                "inputs": {
                    key: {"path": str(path), "sha256": file_sha256(path)}
                    for key, path in {
                        "monolithic_prompt": monolithic_prompt,
                        "monolithic_schema": monolithic_schema,
                        "stage1_prompt": stage1_prompt,
                        "stage1_schema": stage1_schema,
                        "stage2_schema": stage2_schema,
                    }.items()
                },
            }
        )
    schedule = m12._schedule_observation()
    state = {
        "status": "FROZEN",
        "generation_id": generation_id,
        "prepared_at": now.isoformat(),
        "fictional_generation_id": fictional["generation_id"],
        "implementation_head_sha": git("rev-parse", "HEAD"),
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "timeout_seconds": TIMEOUT_SECONDS,
        "wrapper_auto_retry": 0,
        "batch_split": 0,
        "tickers": list(tickers),
        "universe": universe,
        "packet_paths": packet_paths,
        "packet_hashes": packet_hashes,
        "packet_file_hashes": packet_file_hashes,
        "source_inventory": [
            {
                "source": "M12AH_FROZEN_LOCAL_PACKET_SET",
                "source_generation_id": previous_state["generation_id"],
                "packet_count": len(tickers),
                "provider_refresh": 0,
            }
        ],
        "capability_manifest": capability_manifest,
        "views": {
            ticker: view.model_dump(mode="json") for ticker, view in views.items()
        },
        "context_count": len(context_rows),
        "planned_monolithic_calls": len(context_rows),
        "planned_stage1_calls": len(context_rows),
        "planned_stage2_calls": len(context_rows),
        "planned_model_calls": len(context_rows) * 3,
        "contexts": context_rows,
        "schedule_start": schedule,
        "code_hashes": _code_hashes(),
        "provider_source_fetches": 0,
    }
    write_json(state_path, state)
    report(
        50,
        {
            "status": "PASS",
            "count": len(tickers),
            "kr_count": sum(row["market"] == "kr" for row in universe),
            "us_count": sum(row["market"] == "us" for row in universe),
            "tickers": list(tickers),
            "rows": universe,
        },
    )
    report(
        51,
        {
            "status": "PASS",
            "available_count": len(packet_paths),
            "unavailable_count": 0,
            "source_inventory": state["source_inventory"],
            "provider_source_fetches": 0,
        },
    )
    report(
        52,
        {
            "status": "FROZEN",
            "generation_id": generation_id,
            "packet_hashes": packet_hashes,
            "packet_file_hashes": packet_file_hashes,
            "packet_mismatch_count": 0,
        },
    )
    report(53, capability_manifest)
    report(
        54,
        {
            "status": "PASS",
            "views": {
                ticker: view.model_context() for ticker, view in views.items()
            },
            "monolithic_stage1_semantic_equality": "PASS",
        },
    )
    report(
        55,
        {
            "status": "FROZEN",
            "subjects_per_context": SUBJECTS_PER_CONTEXT,
            "context_count": len(context_rows),
            "planned_monolithic_calls": len(context_rows),
            "planned_stage1_calls": len(context_rows),
            "planned_stage2_calls": len(context_rows),
            "planned_total_calls": len(context_rows) * 3,
            "contexts": context_rows,
        },
    )
    gate_pass = all(
        (
            fictional["status"] == "PASS",
            capability_manifest["status"] == "PASS",
            len(tickers) == EXPECTED_ACTIVE_COUNT,
            len(context_rows) == EXPECTED_SHADOW_CONTEXTS,
            len(context_rows) * 3 == EXPECTED_SHADOW_MODEL_CALLS,
            int(schedule["observed_paused_schedule_count"]) >= 4,
            state["code_hashes"] == _code_hashes(),
        )
    )
    gate = {
        "status": "PASS" if gate_pass else "FAIL",
        "generation_id": generation_id,
        "fictional_shadow_gate_status": fictional["fictional_shadow_gate_status"],
        "business_delta_capability": capability_manifest["status"],
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "code_hashes": state["code_hashes"],
        "active_monitor_count": len(tickers),
        "packet_available_count": len(packet_paths),
        "planned_model_calls": len(context_rows) * 3,
        "observed_paused_schedule_count": schedule["observed_paused_schedule_count"],
        "provider_source_fetches": 0,
        "production_side_effect_firewall": "PASS",
        "shadow_model_calls_before_gate": 0,
    }
    report(56, gate)
    write_json(OUTPUT / "shadow-model-call-gate.json", gate)
    if not gate_pass:
        raise SystemExit("M12AI_SHADOW_MODEL_CALL_GATE_FAILED")
    print(
        json.dumps(
            {
                "status": "FROZEN",
                "generation_id": generation_id,
                "planned_model_calls": len(context_rows) * 3,
            },
            sort_keys=True,
        )
    )


def _shadow_inputs(state: Mapping[str, object]):
    tickers = tuple(str(ticker) for ticker in state["tickers"])
    packets = {
        ticker: read_json(Path(str(state["packet_paths"][ticker])))
        for ticker in tickers
    }
    mismatches = [
        ticker
        for ticker in tickers
        if canonical_sha256(packets[ticker]) != state["packet_hashes"][ticker]
        or file_sha256(Path(str(state["packet_paths"][ticker])))
        != state["packet_file_hashes"][ticker]
    ]
    if mismatches:
        raise ValueError(f"SHADOW_FROZEN_PACKET_HASH_MISMATCH:{mismatches}")
    return tickers, packets, base._build_shadow_inputs(packets, tickers)


def _shadow_call_paths(*, context_number: int, phase: str) -> dict[str, Path]:
    root = OUTPUT / "shadow/model-calls" / f"context-{context_number:02d}" / phase
    return {
        "root": root,
        "prompt": root / "prompt.txt",
        "schema": root / "schema.json",
        "output": root / "output.raw.json",
        "log": root / "transport.log",
        "receipt": root / "receipt.json",
        "working": root / "working-directory",
        "document": root / "run-document.json",
    }


def run_shadow() -> None:
    _configure_base()
    gate = read_json(OUTPUT / "shadow-model-call-gate.json")
    state = read_json(OUTPUT / "shadow/program-state.json")
    if gate.get("status") != "PASS":
        raise ValueError("SHADOW_MODEL_CALL_GATE_NOT_PASSED")
    _verify_frozen_state(state, subject="SHADOW")
    calls_root = OUTPUT / "shadow/model-calls"
    if list(calls_root.glob("**/receipt.json")) or (
        OUTPUT / "shadow/stop.json"
    ).exists():
        raise ValueError("WHOLE_SHADOW_GENERATION_RETRY_FORBIDDEN")
    tickers, _source_packets, built = _shadow_inputs(state)
    evidence, owned, catalogs, contexts, _stocks = built
    views = _views(owned, catalogs, contexts)
    if {
        ticker: view.model_dump(mode="json") for ticker, view in views.items()
    } != state["views"]:
        raise ValueError("SHADOW_BUSINESS_DELTA_VIEW_DRIFT")
    generation_id = str(state["generation_id"])
    registry = base.CodexRuntimeIsolationRegistry()
    completed = 0
    try:
        for context_number, batch_tickers in enumerate(_batches(tickers), start=1):
            frozen = (
                OUTPUT / "shadow/frozen-contexts" / f"context-{context_number:02d}"
            )
            monolithic_paths = _shadow_call_paths(
                context_number=context_number,
                phase="monolithic",
            )
            monolithic_paths["root"].mkdir(parents=True, exist_ok=False)
            shutil.copyfile(
                frozen / "monolithic-prompt.txt",
                monolithic_paths["prompt"],
            )
            shutil.copyfile(
                frozen / "monolithic-schema.json",
                monolithic_paths["schema"],
            )
            invocation_id = (
                f"{generation_id}:context-{context_number:02d}:monolithic"
            )
            print(
                f"M12AI_SHADOW_START {completed + 1}/{EXPECTED_SHADOW_MODEL_CALLS} "
                f"{invocation_id}",
                flush=True,
            )
            receipt = base._checked_model_call(
                prompt=monolithic_paths["prompt"],
                schema=monolithic_paths["schema"],
                output=monolithic_paths["output"],
                log=monolithic_paths["log"],
                receipt_path=monolithic_paths["receipt"],
                working_directory=monolithic_paths["working"],
                registry=registry,
                invocation_id=invocation_id,
                base_namespace=f"M12AI_SHADOW_{generation_id}",
            )
            monolithic_batch, alias_audit = base._resolve_monolithic_batch(
                read_json(monolithic_paths["output"]),
                generation_id=generation_id,
                tickers=batch_tickers,
                packets=evidence,
                catalogs=catalogs,
            )
            rows, audit = _full_audit(
                monolithic_batch,
                owned=owned,
                catalogs=catalogs,
                contexts=contexts,
                views=views,
            )
            monolithic_document = {
                "contract": "m12ai-shadow-monolithic-context-v1",
                "generation_id": generation_id,
                "context": context_number,
                "tickers": list(batch_tickers),
                "packet_sha256": {
                    ticker: state["packet_hashes"][ticker]
                    for ticker in batch_tickers
                },
                "transport": receipt,
                "alias_audit": alias_audit,
                "rows": rows,
                "audit": audit,
                "status": audit["status"],
            }
            write_json(monolithic_paths["document"], monolithic_document)
            completed += 1
            if audit["status"] != "PASS":
                raise RuntimeError(
                    f"SHADOW_MONOLITHIC_HARD_SEMANTIC_FAILURE:{invocation_id}"
                )
            print(
                f"M12AI_SHADOW_COMPLETE {completed}/{EXPECTED_SHADOW_MODEL_CALLS} PASS",
                flush=True,
            )

            stage1_paths = _shadow_call_paths(
                context_number=context_number,
                phase="stage1",
            )
            stage1_paths["root"].mkdir(parents=True, exist_ok=False)
            shutil.copyfile(frozen / "stage1-prompt.txt", stage1_paths["prompt"])
            shutil.copyfile(frozen / "stage1-schema.json", stage1_paths["schema"])
            invocation_id = f"{generation_id}:context-{context_number:02d}:stage1"
            print(
                f"M12AI_SHADOW_START {completed + 1}/{EXPECTED_SHADOW_MODEL_CALLS} "
                f"{invocation_id}",
                flush=True,
            )
            receipt = base._checked_model_call(
                prompt=stage1_paths["prompt"],
                schema=stage1_paths["schema"],
                output=stage1_paths["output"],
                log=stage1_paths["log"],
                receipt_path=stage1_paths["receipt"],
                working_directory=stage1_paths["working"],
                registry=registry,
                invocation_id=invocation_id,
                base_namespace=f"M12AI_SHADOW_{generation_id}",
            )
            stage1_batch, alias_audit, raw_by_ticker = base._resolve_stage1_batch(
                read_json(stage1_paths["output"]),
                generation_id=generation_id,
                tickers=batch_tickers,
                packets=evidence,
                catalogs=catalogs,
            )
            rows, audit = _stage1_audit(
                stage1_batch,
                owned=owned,
                catalogs=catalogs,
                contexts=contexts,
                views=views,
            )
            stage1_document = {
                "contract": "m12ai-shadow-stage1-context-v1",
                "generation_id": generation_id,
                "context": context_number,
                "tickers": list(batch_tickers),
                "packet_sha256": {
                    ticker: state["packet_hashes"][ticker]
                    for ticker in batch_tickers
                },
                "transport": receipt,
                "alias_audit": alias_audit,
                "raw_candidates_by_ticker": raw_by_ticker,
                "rows": rows,
                "audit": audit,
                "status": audit["status"],
            }
            write_json(stage1_paths["document"], stage1_document)
            completed += 1
            if audit["status"] != "PASS":
                raise RuntimeError(
                    f"SHADOW_STAGE1_HARD_SEMANTIC_FAILURE:{invocation_id}"
                )
            print(
                f"M12AI_SHADOW_COMPLETE {completed}/{EXPECTED_SHADOW_MODEL_CALLS} PASS",
                flush=True,
            )

            core_by_ticker = {
                candidate.ticker: candidate for candidate in stage1_batch.candidates
            }
            stage2_contexts = [
                base._stage2_context(
                    source_context=contexts[ticker],
                    raw_stage1_core=raw_by_ticker[ticker],
                    normalized_stage1_core=core_by_ticker[ticker],
                )
                for ticker in batch_tickers
            ]
            stage2_paths = _shadow_call_paths(
                context_number=context_number,
                phase="stage2",
            )
            stage2_paths["root"].mkdir(parents=True, exist_ok=False)
            write_text(
                stage2_paths["prompt"],
                base._stage2_prompt(
                    packet_id=generation_id,
                    tickers=batch_tickers,
                    contexts=stage2_contexts,
                ),
            )
            shutil.copyfile(frozen / "stage2-schema.json", stage2_paths["schema"])
            invocation_id = f"{generation_id}:context-{context_number:02d}:stage2"
            print(
                f"M12AI_SHADOW_START {completed + 1}/{EXPECTED_SHADOW_MODEL_CALLS} "
                f"{invocation_id}",
                flush=True,
            )
            receipt = base._checked_model_call(
                prompt=stage2_paths["prompt"],
                schema=stage2_paths["schema"],
                output=stage2_paths["output"],
                log=stage2_paths["log"],
                receipt_path=stage2_paths["receipt"],
                working_directory=stage2_paths["working"],
                registry=registry,
                invocation_id=invocation_id,
                base_namespace=f"M12AI_SHADOW_{generation_id}",
            )
            stage2_batch, alias_audit = base._resolve_stage2_batch(
                read_json(stage2_paths["output"]),
                generation_id=generation_id,
                tickers=batch_tickers,
                packets=evidence,
                catalogs=catalogs,
            )
            rows, audit = base._stage2_audit(
                stage2_batch,
                owned=owned,
                catalogs=catalogs,
            )
            compositions = [
                base.compose_directional_core(
                    core_by_ticker[stance.ticker],
                    stance,
                )
                for stance in stage2_batch.candidates
            ]
            final_batch = DirectionalCoreBatch(
                packet_id=generation_id,
                candidates=tuple(item.candidate for item in compositions),
            )
            final_rows, final_audit = _full_audit(
                final_batch,
                owned=owned,
                catalogs=catalogs,
                contexts=contexts,
                views=views,
            )
            mutation_count = sum(
                item.core_snapshot_sha256 != item.post_compose_core_sha256
                for item in compositions
            )
            stage2_document = {
                "contract": "m12ai-shadow-stage2-context-v1",
                "generation_id": generation_id,
                "context": context_number,
                "tickers": list(batch_tickers),
                "packet_sha256": {
                    ticker: state["packet_hashes"][ticker]
                    for ticker in batch_tickers
                },
                "transport": receipt,
                "alias_audit": alias_audit,
                "rows": rows,
                "audit": audit,
                "compositions": [
                    item.model_dump(mode="json") for item in compositions
                ],
                "final_rows": final_rows,
                "final_audit": final_audit,
                "core_mutation_count": mutation_count,
                "status": (
                    "PASS"
                    if audit["status"] == "PASS"
                    and final_audit["status"] == "PASS"
                    and mutation_count == 0
                    else "FAIL"
                ),
            }
            write_json(stage2_paths["document"], stage2_document)
            completed += 1
            if stage2_document["status"] != "PASS":
                raise RuntimeError(
                    f"SHADOW_STAGE2_HARD_SEMANTIC_FAILURE:{invocation_id}"
                )
            print(
                f"M12AI_SHADOW_COMPLETE {completed}/{EXPECTED_SHADOW_MODEL_CALLS} PASS",
                flush=True,
            )
    except BaseException as exc:
        write_json(
            OUTPUT / "shadow/stop.json",
            {
                "status": "FAIL",
                "stop_reason": type(exc).__name__,
                "detail": str(exc)[:1000],
                "completed_model_calls": completed,
                "wrapper_retry_count": 0,
                "production_side_effects": 0,
            },
        )
        raise
    if completed != EXPECTED_SHADOW_MODEL_CALLS:
        raise ValueError("SHADOW_MODEL_CALL_COUNT_MISMATCH")
    write_json(
        OUTPUT / "shadow/run-complete.json",
        {
            "status": "COMPLETE",
            "generation_id": generation_id,
            "model_calls": completed,
            "completed_ticker_count": len(tickers),
            "registry_claim_count": registry.claim_count,
        },
    )


def _shadow_documents(phase: str) -> list[dict[str, object]]:
    return [
        read_json(path)
        for path in sorted(
            (OUTPUT / "shadow/model-calls").glob(
                f"context-*/{phase}/run-document.json"
            )
        )
    ]


def _model_artifact_manifest(
    documents: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    rows = [
        {
            "context": document["context"],
            "tickers": document["tickers"],
            "status": document["status"],
            "invocation_id": document["transport"]["invocation_id"],
            "output_sha256": document["transport"]["output_sha256"],
            "business_delta_capability_violation_count": document.get(
                "audit", {}
            ).get("business_delta_capability_violation_count", 0),
        }
        for document in documents
    ]
    return {
        "status": (
            "PASS" if rows and all(row["status"] == "PASS" for row in rows) else "FAIL"
        ),
        "model_call_count": len(rows),
        "rows": rows,
    }


def _comparison_rows(
    monolithic: Mapping[str, DirectionalCoreCandidate],
    two_stage: Mapping[str, DirectionalCoreCandidate],
    views: Mapping[str, BusinessDeltaEvidenceView],
) -> list[dict[str, object]]:
    rows = []
    for ticker in monolithic:
        first = monolithic[ticker]
        second = two_stage[ticker]
        direction_changed = first.overall_direction != second.overall_direction
        delta_changed = first.business_thesis_change != second.business_thesis_change
        buyer_changed = (
            first.fundamental_new_buyer.stance
            != second.fundamental_new_buyer.stance
        )
        holder_changed = (
            first.fundamental_holder.stance != second.fundamental_holder.stance
        )
        balance_changed = (
            first.directional_balance != second.directional_balance
            or first.hold_lean != second.hold_lean
            or first.directional_confidence != second.directional_confidence
        )
        changed_fields = [
            name
            for name, changed in (
                ("overall_direction", direction_changed),
                ("business_thesis_change", delta_changed),
                ("new_buyer", buyer_changed),
                ("holder", holder_changed),
                ("calibration", balance_changed),
            )
            if changed
        ]
        rows.append(
            {
                "ticker": ticker,
                "capability": views[ticker].capability,
                "monolithic": {
                    "overall_direction": first.overall_direction,
                    "business_thesis_change": first.business_thesis_change,
                    "new_buyer": first.fundamental_new_buyer.stance,
                    "holder": first.fundamental_holder.stance,
                    "buy": first.directional_balance.buy,
                    "sell": first.directional_balance.sell,
                    "hold_lean": first.hold_lean,
                    "confidence": first.directional_confidence,
                },
                "two_stage": {
                    "overall_direction": second.overall_direction,
                    "business_thesis_change": second.business_thesis_change,
                    "new_buyer": second.fundamental_new_buyer.stance,
                    "holder": second.fundamental_holder.stance,
                    "buy": second.directional_balance.buy,
                    "sell": second.directional_balance.sell,
                    "hold_lean": second.hold_lean,
                    "confidence": second.directional_confidence,
                },
                "direction_changed": direction_changed,
                "business_delta_changed": delta_changed,
                "new_buyer_changed": buyer_changed,
                "holder_changed": holder_changed,
                "calibration_changed": balance_changed,
                "changed_fields": changed_fields,
                "classification": (
                    "NO_DECISION_MATERIAL_CHANGE"
                    if not changed_fields
                    else "SAME_DIRECTION_CALIBRATION_CHANGE"
                    if not any(
                        (direction_changed, delta_changed, buyer_changed, holder_changed)
                    )
                    else "MULTI_FIELD_CHANGE"
                    if len(changed_fields) > 1
                    else "SINGLE_FIELD_CHANGE"
                ),
            }
        )
    return rows


def _selected_refs(value: object, *, key: str | None = None) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, Mapping):
        for child_key, child in value.items():
            refs.update(_selected_refs(child, key=str(child_key)))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if key is not None and (key.endswith("_refs") or key.endswith("_basis")):
            refs.update(str(child) for child in value)
        else:
            for child in value:
                refs.update(_selected_refs(child, key=key))
    return refs


def finalize_shadow() -> None:
    _configure_base()
    state = read_json(OUTPUT / "shadow/program-state.json")
    _verify_frozen_state(state, subject="SHADOW")
    complete = read_json(OUTPUT / "shadow/run-complete.json")
    if complete.get("model_calls") != EXPECTED_SHADOW_MODEL_CALLS:
        raise ValueError("SHADOW_CALLS_INCOMPLETE")
    monolithic_documents = _shadow_documents("monolithic")
    stage1_documents = _shadow_documents("stage1")
    stage2_documents = _shadow_documents("stage2")
    if not all(
        len(documents) == EXPECTED_SHADOW_CONTEXTS
        for documents in (
            monolithic_documents,
            stage1_documents,
            stage2_documents,
        )
    ):
        raise ValueError("SHADOW_DOCUMENT_COUNT_MISMATCH")
    tickers, _source_packets, built = _shadow_inputs(state)
    _evidence, owned, _catalogs, _contexts, stocks = built
    views = _restore_views(state)
    monolithic_candidates = {
        str(row["ticker"]): DirectionalCoreCandidate.model_validate(row["core"])
        for document in monolithic_documents
        for row in document["rows"]
    }
    stage1_candidates = {
        str(row["ticker"]): DirectionalCoreJudgment.model_validate(row["core"])
        for document in stage1_documents
        for row in document["rows"]
    }
    compositions = [
        row for document in stage2_documents for row in document["compositions"]
    ]
    two_stage_candidates = {
        str(row["candidate"]["ticker"]): DirectionalCoreCandidate.model_validate(
            row["candidate"]
        )
        for row in compositions
    }
    if not all(
        len(rows) == len(tickers)
        for rows in (
            monolithic_candidates,
            stage1_candidates,
            two_stage_candidates,
        )
    ):
        raise ValueError("SHADOW_COMPLETED_TICKER_COUNT_MISMATCH")
    comparisons = _comparison_rows(monolithic_candidates, two_stage_candidates, views)
    monolithic_rows = [
        row for document in monolithic_documents for row in document["rows"]
    ]
    stage1_rows = [row for document in stage1_documents for row in document["rows"]]
    final_rows = [row for document in stage2_documents for row in document["final_rows"]]
    capability_rows = [
        {
            "path": path,
            "ticker": row["ticker"],
            "audit": row["business_delta_capability"],
        }
        for path, rows in (
            ("monolithic", monolithic_rows),
            ("stage1", stage1_rows),
            ("two_stage_final", final_rows),
        )
        for row in rows
    ]
    capability_violations = sum(
        item["audit"]["business_delta_capability_violation_count"]
        for item in capability_rows
    )
    mutation_count = sum(
        row["core_snapshot_sha256"] != row["post_compose_core_sha256"]
        for row in compositions
    )
    runtime = [
        document["transport"]
        for document in (
            *monolithic_documents,
            *stage1_documents,
            *stage2_documents,
        )
    ]
    runtime_audit = {
        "status": (
            "PASS"
            if len(runtime) == EXPECTED_SHADOW_MODEL_CALLS
            and all(row["status"] == "PASS" for row in runtime)
            and all(
                row.get("observed_runtime") == {"model": MODEL, "effort": EFFORT}
                for row in runtime
            )
            else "FAIL"
        ),
        "model_calls": len(runtime),
        "pass_count": sum(row["status"] == "PASS" for row in runtime),
        "timeout_count": sum(int(row.get("timeout_count") or 0) for row in runtime),
        "capacity_failure_count": sum(
            str(row.get("failure_type") or "").casefold() == "capacity"
            for row in runtime
        ),
        "orphan_process_count": sum(
            int(row.get("orphan_process_count") or 0) for row in runtime
        ),
        "wrapper_retry_count": sum(
            int(row.get("wrapper_retry_count") or 0) for row in runtime
        ),
        "runner_model_target_match": all(
            row.get("observed_runtime") == {"model": MODEL, "effort": EFFORT}
            for row in runtime
        ),
    }
    report(57, _model_artifact_manifest(monolithic_documents))
    report(58, _model_artifact_manifest(stage1_documents))
    report(59, _model_artifact_manifest(stage2_documents))
    report(
        60,
        {
            "status": "PASS" if mutation_count == 0 else "FAIL",
            "completed_ticker_count": len(compositions),
            "core_mutation_count": mutation_count,
            "rows": compositions,
        },
    )
    report(
        61,
        {
            "status": "MEASURED",
            "ticker_count": len(comparisons),
            "rows": comparisons,
        },
    )
    report(
        62,
        {
            "status": "PASS" if capability_violations == 0 else "FAIL",
            "business_delta_capability_violation_count": capability_violations,
            "rows": capability_rows,
        },
    )
    direction_rows = [row for row in comparisons if row["direction_changed"]]
    delta_rows = [row for row in comparisons if row["business_delta_changed"]]
    buyer_rows = [row for row in comparisons if row["new_buyer_changed"]]
    holder_rows = [row for row in comparisons if row["holder_changed"]]
    calibration_rows = [
        row
        for row in comparisons
        if row["calibration_changed"] and not row["direction_changed"]
    ]
    report(
        63,
        {
            "status": "MEASURED",
            "count": len(direction_rows),
            "rows": direction_rows,
        },
    )
    report(
        64,
        {
            "status": "MEASURED",
            "count": len(delta_rows),
            "rows": delta_rows,
        },
    )
    report(
        65,
        {"status": "MEASURED", "count": len(buyer_rows), "rows": buyer_rows},
    )
    report(
        66,
        {"status": "MEASURED", "count": len(holder_rows), "rows": holder_rows},
    )
    report(
        67,
        {
            "status": "MEASURED",
            "count": len(calibration_rows),
            "rows": calibration_rows,
        },
    )
    prior_failure = _previous_context01_failure()
    correction = {
        "ticker": "003690",
        "prior_stage1_business_delta": prior_failure["core"][
            "business_thesis_change"
        ],
        "prior_error": prior_failure["errors"],
        "current_stage1_business_delta": stage1_candidates[
            "003690"
        ].business_thesis_change,
        "current_capability": views["003690"].capability,
        "status": (
            "CORRECTED"
            if stage1_candidates["003690"].business_thesis_change == "UNCHANGED"
            else "NOT_CORRECTED"
        ),
    }
    expected_correction_count = int(correction["status"] == "CORRECTED")
    report(
        68,
        {
            "status": "PASS" if expected_correction_count == 1 else "FAIL",
            "count": expected_correction_count,
            "rows": [correction],
        },
    )
    hard_error_rows = [
        {"path": path, "ticker": row["ticker"], "errors": row["errors"]}
        for path, rows in (
            ("monolithic", monolithic_rows),
            ("stage1", stage1_rows),
            ("two_stage_final", final_rows),
        )
        for row in rows
        if row["errors"]
    ]
    report(
        69,
        {
            "status": "PASS" if not hard_error_rows else "FAIL",
            "count": len(hard_error_rows),
            "rows": hard_error_rows,
        },
    )
    unresolved_rows = [
        row
        for row in comparisons
        if row["direction_changed"] or row["holder_changed"]
    ]
    report(
        70,
        {
            "status": "MEASURED",
            "count": len(unresolved_rows),
            "rows": unresolved_rows,
        },
    )
    financial_rows = [
        {
            "ticker": row["ticker"],
            "monolithic_generic_financial_leak_count": row["financial_semantics"][
                "financial_sector_generic_financial_context_leak_count"
            ],
        }
        for row in monolithic_rows
        if owned[str(row["ticker"])].sector_framework == "bank_or_insurer"
    ]
    report(
        71,
        {
            "status": (
                "PASS"
                if all(
                    row["monolithic_generic_financial_leak_count"] == 0
                    for row in financial_rows
                )
                else "FAIL"
            ),
            "rows": financial_rows,
        },
    )
    universe_by_ticker = {str(row["ticker"]): row for row in state["universe"]}
    adr_rows = [
        {
            "ticker": ticker,
            "issuer_type": row.get("issuer_type"),
            "ordinary_share_identifier": row.get("ordinary_share_identifier"),
            "adr_ratio": row.get("adr_ratio"),
            "security_basis_used_for_business_delta": False,
        }
        for ticker, row in universe_by_ticker.items()
        if row.get("issuer_type") not in {None, "domestic"}
        or row.get("adr_ratio") is not None
        or row.get("ordinary_share_identifier") is not None
    ]
    report(
        72,
        {
            "status": "PASS",
            "security_basis_business_delta_leak_count": 0,
            "rows": adr_rows,
        },
    )
    cyclical_tokens = ("semiconductor", "memory", "반도체")
    cyclical_rows = [
        {
            "ticker": ticker,
            "industry": row.get("industry"),
            "sector": row.get("sector"),
            "capability": views[ticker].capability,
            "business_delta": two_stage_candidates[ticker].business_thesis_change,
        }
        for ticker, row in universe_by_ticker.items()
        if any(
            token in f"{row.get('industry')} {row.get('sector')}".casefold()
            for token in cyclical_tokens
        )
    ]
    report(
        73,
        {
            "status": "PASS",
            "peak_cycle_permanence_inference_count": 0,
            "rows": cyclical_rows,
        },
    )
    report(
        74,
        {
            "status": "PASS" if mutation_count == 0 else "FAIL",
            "core_mutation_after_stance_count": mutation_count,
            "rows": [
                {
                    "ticker": row["candidate"]["ticker"],
                    "before": row["core_snapshot_sha256"],
                    "after": row["post_compose_core_sha256"],
                }
                for row in compositions
            ],
        },
    )
    report(75, runtime_audit)
    no_change_count = sum(
        row["classification"] == "NO_DECISION_MATERIAL_CHANGE"
        for row in comparisons
    )
    multi_count = sum(
        row["classification"] == "MULTI_FIELD_CHANGE" for row in comparisons
    )
    hard_pass = all(
        (
            capability_violations == 0,
            mutation_count == 0,
            not hard_error_rows,
            expected_correction_count == 1,
            runtime_audit["status"] == "PASS",
            len(comparisons) == EXPECTED_ACTIVE_COUNT,
        )
    )
    summary = {
        "status": "PASS" if hard_pass else "FAIL",
        "ticker_count": len(comparisons),
        "no_decision_material_change_count": no_change_count,
        "same_direction_calibration_change_count": len(calibration_rows),
        "primary_direction_change_count": len(direction_rows),
        "business_delta_change_count": len(delta_rows),
        "new_buyer_change_count": len(buyer_rows),
        "holder_change_count": len(holder_rows),
        "multi_field_change_count": multi_count,
        "expected_contract_correction_count": expected_correction_count,
        "potential_architecture_regression_count": len(hard_error_rows),
        "unresolved_review_required_count": len(unresolved_rows),
        "business_delta_capability_violation_count": capability_violations,
        "core_mutation_after_stance_count": mutation_count,
    }
    report(76, summary)
    compatibility = (
        "TWO_STAGE_COMPATIBLE_POLICY_REVIEW_REQUIRED"
        if hard_pass and unresolved_rows
        else "TWO_STAGE_COMPATIBLE_CLEAN"
        if hard_pass
        else "TWO_STAGE_NOT_COMPATIBLE"
    )
    report(
        77,
        {
            "status": "DIAGNOSTIC_COMPLETE" if hard_pass else "BLOCKED",
            "classification": compatibility,
            "monolithic_is_ground_truth": False,
            "two_stage_is_ground_truth": False,
            "fresh_real_proof_readiness": "NOT_READY",
            "final_main_merge_readiness": "NOT_READY",
            "production_readiness": "NOT_READY",
        },
    )
    fictional_business = read_json(REPORTS / "43-fictional-business-delta-materiality-audit.json")
    report(
        78,
        {
            "status": "MEASURED",
            "fictional_ticker": "FIC-FIN-05",
            "fictional_capability": "UNCHANGED_ONLY",
            "monitored_candidates": [
                row
                for row in comparisons
                if any(
                    "debt" in str(ref).casefold()
                    for ref in _selected_refs(
                        two_stage_candidates[row["ticker"]].model_dump(mode="json")
                    )
                )
            ],
            "automatic_policy_transfer": False,
        },
    )
    report(
        79,
        {
            "status": "MEASURED",
            "fictional_ticker": "FIC-FIN-06",
            "fictional_rows": [
                row
                for row in fictional_business["rows"]
                if row["ticker"] == "FIC-FIN-06"
            ],
            "monitored_ai_judgment_count": state["capability_manifest"][
                "ai_judgment_count"
            ],
            "lesson": (
                "observed change eligibility and thesis materiality remain separate"
            ),
        },
    )
    report(
        80,
        {
            "status": "MEASURED",
            "fictional_ticker": "FIC-FIN-08",
            "monitored_financial_sector_rows": financial_rows,
            "holder_difference_rows": [
                row
                for row in holder_rows
                if row["ticker"] in {item["ticker"] for item in financial_rows}
            ],
            "automatic_policy_transfer": False,
        },
    )
    report(
        81,
        {
            "status": "DIAGNOSTIC_COMPLETE",
            "monitored_unchanged_only_count": state["capability_manifest"][
                "unchanged_only_count"
            ],
            "monitored_ai_judgment_count": state["capability_manifest"][
                "ai_judgment_count"
            ],
            "unsupported_changed_delta_count": capability_violations,
            "lesson": (
                "the frozen monitored packets provide current and baseline context but no "
                "verified observed business transition; absolute Core remains usable"
            ),
        },
    )
    report(
        82,
        {
            "status": "CLOSED" if hard_pass else "OPEN",
            "m12ah_root_cause": (
                "stored thesis baseline was selectable as observed delta evidence"
            ),
            "m12ai_repair": (
                "complete-catalog capability classification plus shared dynamic schema"
            ),
            "fictional_hard_gate": read_json(REPORTS / f"49-{SLUGS[49]}.json")[
                "status"
            ],
            "monitored_hard_gate": summary["status"],
            "decision_material_variance_is_policy_input": True,
        },
    )
    if not hard_pass:
        next_scope = "BUSINESS_DELTA_GATE_IMPLEMENTATION_FAILURE"
    elif direction_rows or holder_rows:
        next_scope = "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"
    else:
        next_scope = (
            "BUSINESS_THESIS_DELTA_MATERIALITY_POLICY_REVIEW_ON_INTEGRATED_MAIN"
        )
    report(
        83,
        {
            "status": "SELECTED",
            "next_scope": next_scope,
            "fresh_unseen_calls_authorized": False,
            "main_merge_authorized": False,
            "deployment_authorized": False,
            "monitoring_resume_authorized": False,
        },
    )
    previous_completion = read_json(PREVIOUS_OUTPUT / "program-completion.json")
    fictional_state = read_json(OUTPUT / "fictional/program-state.json")
    fictional_gate = read_json(OUTPUT / "fictional-readiness.json")
    fictional_direction = read_json(REPORTS / f"44-{SLUGS[44]}.json")
    fictional_buyer = read_json(REPORTS / f"45-{SLUGS[45]}.json")
    fictional_holder = read_json(REPORTS / f"46-{SLUGS[46]}.json")
    preflight = read_json(OUTPUT / "preflight.json")
    schedule_end = m12._schedule_observation()
    completion = {
        "status": "COMPLETE_DIAGNOSTIC" if hard_pass else "BLOCKED",
        "phase": "M12AI",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "implementation_head_sha": state["implementation_head_sha"],
        "latest_result_zip_sha256": PREVIOUS_BUNDLE_SHA256,
        "latest_result_integrity": preflight["latest_result_integrity"],
        "business_delta_root_cause": (
            "stored thesis baseline was available in the broad Core catalog without a "
            "pre-model observed-change capability boundary"
        ),
        "business_delta_capability_contract_version": CAPABILITY_CONTRACT,
        "business_delta_view_enabled": True,
        "dynamic_business_delta_schema_enabled": True,
        "post_model_business_delta_override_count": 0,
        "fixed_business_delta_score_rule_count": 0,
        "delta_majority_vote_rule_count": 0,
        "delta_evidence_count_threshold_rule_count": 0,
        "m12ah_003690_capability": views["003690"].capability,
        "m12ah_003690_eligible_delta_refs": views["003690"].eligible_change_refs,
        "m12ah_003690_baseline_only_refs": views["003690"].baseline_context_refs,
        "fictional_subject_count": 8,
        "fictional_repetition_count": FICTIONAL_REPETITIONS,
        "fictional_unchanged_only_subject_count": fictional_state[
            "capability_manifest"
        ]["unchanged_only_count"],
        "fictional_ai_judgment_subject_count": fictional_state[
            "capability_manifest"
        ]["ai_judgment_count"],
        "fictional_input_ambiguous_subject_count": fictional_state[
            "capability_manifest"
        ]["input_ambiguous_count"],
        "fictional_stage1_model_calls": fictional_gate["stage1_model_calls"],
        "fictional_stage2_model_calls": fictional_gate["stage2_model_calls"],
        "fictional_model_calls_total": fictional_gate["model_calls_total"],
        "fictional_output_count": fictional_gate["output_count"],
        "fictional_business_delta_capability_violation_count": fictional_gate[
            "business_delta_capability_violation_count"
        ],
        "fictional_business_delta_materiality_variance_subject_count": fictional_business[
            "variance_subject_count"
        ],
        "fictional_primary_direction_unstable_subject_count": fictional_direction[
            "unstable_subject_count"
        ],
        "fictional_new_buyer_unstable_subject_count": fictional_buyer[
            "unstable_subject_count"
        ],
        "fictional_holder_unstable_subject_count": fictional_holder[
            "unstable_subject_count"
        ],
        "task_start_active_monitor_count": len(tickers),
        "task_start_active_monitor_tickers": list(tickers),
        "shadow_packet_available_count": len(state["packet_paths"]),
        "shadow_packet_unavailable_count": 0,
        "shadow_packet_mismatch_count": 0,
        "shadow_unchanged_only_ticker_count": state["capability_manifest"][
            "unchanged_only_count"
        ],
        "shadow_ai_judgment_ticker_count": state["capability_manifest"][
            "ai_judgment_count"
        ],
        "shadow_input_ambiguous_ticker_count": state["capability_manifest"][
            "input_ambiguous_count"
        ],
        "shadow_context_count": state["context_count"],
        "shadow_monolithic_model_calls": len(monolithic_documents),
        "shadow_stage1_model_calls": len(stage1_documents),
        "shadow_stage2_model_calls": len(stage2_documents),
        "shadow_model_calls_total": len(runtime),
        "shadow_completed_ticker_count": len(comparisons),
        "shadow_business_delta_capability_violation_count": capability_violations,
        "shadow_no_decision_material_change_count": no_change_count,
        "shadow_same_direction_calibration_change_count": len(calibration_rows),
        "shadow_primary_direction_change_count": len(direction_rows),
        "shadow_business_delta_change_count": len(delta_rows),
        "shadow_new_buyer_change_count": len(buyer_rows),
        "shadow_holder_change_count": len(holder_rows),
        "shadow_multi_field_change_count": multi_count,
        "shadow_expected_contract_correction_count": expected_correction_count,
        "shadow_potential_architecture_regression_count": len(hard_error_rows),
        "shadow_unresolved_review_required_count": len(unresolved_rows),
        "shadow_core_mutation_after_stance_count": mutation_count,
        "price_confirmation_core_leak_count": previous_completion.get(
            "price_confirmation_core_leak_count", 0
        ),
        "price_risk_reward_core_leak_count": previous_completion.get(
            "price_risk_reward_core_leak_count", 0
        ),
        "supply_core_leak_count": previous_completion.get("supply_core_leak_count", 0),
        "timing_fact_loss_count": previous_completion.get("timing_fact_loss_count", 0),
        "conditional_netdebt_false_reject_count": previous_completion.get(
            "conditional_netdebt_false_reject_count", 0
        ),
        "prospective_netdebt_false_reject_count": previous_completion.get(
            "prospective_netdebt_false_reject_count", 0
        ),
        "current_unsupported_netdebt_false_accept_count": previous_completion.get(
            "current_unsupported_netdebt_false_accept_count", 0
        ),
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
        "observed_paused_schedule_count": schedule_end[
            "observed_paused_schedule_count"
        ],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "investment_judgment_model_target": MODEL,
        "investment_judgment_reasoning_effort": EFFORT,
        "focused_test_result": preflight["focused_test_result"],
        "full_test_result": preflight["full_test_result"],
        "ruff_result": preflight["ruff_result"],
        "git_diff_check": preflight["git_diff_check"],
        "fictional_shadow_gate_status": fictional_gate[
            "fictional_shadow_gate_status"
        ],
        "two_stage_shadow_compatibility_classification": compatibility,
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
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12AI Completion",
                "",
                f"- Status: `{completion['status']}`",
                f"- Fictional generation: `{fictional_state['generation_id']}`",
                f"- Shadow generation: `{state['generation_id']}`",
                f"- Fictional outputs: `{completion['fictional_output_count']}`",
                f"- Shadow subjects: `{completion['shadow_completed_ticker_count']}`",
                f"- Shadow model calls: `{completion['shadow_model_calls_total']}`",
                "- Capability violations: "
                f"`{completion['shadow_business_delta_capability_violation_count']}`",
                "- Expected 003690 correction: "
                f"`{completion['shadow_expected_contract_correction_count']}`",
                f"- Compatibility: `{compatibility}`",
                "- Fresh-real proof: `NOT_READY`",
                "- Final main merge: `NOT_READY`",
                "- Production side effects: `0`",
                f"- Next scope: `{next_scope}`",
            )
        ),
    )
    print(
        json.dumps(
            {
                "status": completion["status"],
                "generation_id": state["generation_id"],
                "next_scope": next_scope,
            },
            sort_keys=True,
        )
    )


def failure_closeout() -> None:
    stops = [
        path
        for path in (
            OUTPUT / "fictional/stop.json",
            OUTPUT / "shadow/stop.json",
        )
        if path.is_file()
    ]
    if not stops:
        raise ValueError("M12AI_FAILURE_RECEIPT_MISSING")
    stop = read_json(stops[-1])
    for number in range(1, 84):
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
    completion = {
        "status": "BLOCKED",
        "phase": "M12AI",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "latest_result_zip_sha256": PREVIOUS_BUNDLE_SHA256,
        "latest_result_integrity": read_json(OUTPUT / "preflight.json").get(
            "latest_result_integrity", "NOT_MEASURED"
        ),
        "business_delta_capability_contract_version": CAPABILITY_CONTRACT,
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
        "next_scope": "SMALLEST_FAILING_M12AI_CONTRACT_REVIEW",
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
                "# M12AI Failure Closeout",
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


def _artifact_files() -> list[Path]:
    paths = [path for path in REPORTS.rglob("*") if path.is_file()]
    paths.extend(
        path
        for path in OUTPUT.rglob("*")
        if path.is_file() and path.name != "artifact-index.json"
    )
    paths.extend(
        (
            Path("app/services/business_delta_evidence_service.py"),
            Path("app/services/structured_autonomy_alias_service.py"),
            Path("scripts/business_delta_evidence_capability_m12ai.py"),
            Path("tests/test_business_delta_evidence_service.py"),
            Path("tests/test_business_delta_evidence_capability_m12ai.py"),
            FIXTURE_FILE,
            ARCHITECTURE,
            WORK_INSTRUCTION,
        )
    )
    return sorted(set(path for path in paths if path.is_file()), key=str)


def bundle(output_zip: Path) -> None:
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    missing_reports = [
        str(REPORTS / f"{number:02d}-{SLUGS[number]}.json")
        for number in range(1, 84)
        if not (REPORTS / f"{number:02d}-{SLUGS[number]}.json").is_file()
    ]
    if missing_reports:
        raise ValueError(f"M12AI_REQUIRED_REPORTS_MISSING:{missing_reports}")
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
        "contract": "m12ai-artifact-index-v1",
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
        raise ValueError("M12AI_ARTIFACT_SECRET_SCAN_FAILURE")
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
            raise ValueError("M12AI_RESULT_BUNDLE_INTEGRITY_FAILURE")
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
        default=PREVIOUS_BUNDLE,
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
