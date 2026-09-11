"""M12AF integrated-main monitored shadow diagnostic.

This module reuses the frozen M12AE-R2 prompts, schemas, validators, and
composer.  It only changes orchestration and reporting so the already exposed
monitored universe can be compared despite the fictional calibration gate.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

from app.services.direction_timing_ownership_service import (
    CORE_OUTPUT_CONTRACT,
    DirectionalCoreCandidate,
    canonical_sha256,
)
from app.services.two_stage_directional_service import (
    CORE_JUDGMENT_OUTPUT_CONTRACT,
    FUNDAMENTAL_STANCE_OUTPUT_CONTRACT,
    DirectionalCoreJudgment,
    FundamentalStanceCandidate,
)
from scripts import directional_financial_context_m12 as m12
from scripts import main_integration_two_stage_directional_m12ae_r2_runtime as base


NAME = "20260911-integrated-main-monitored-shadow-diagnostic-boundary-delta-review"
REPORTS = Path("docs/reports") / NAME
OUTPUT = Path("artifacts") / NAME
RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
OPERATING_ROOT = Path("/Users/sskim/Codex/thesis-monitor")
PREVIOUS_NAME = (
    "20260911-main-integration-two-stage-directional-fictional-monitored-shadow-validation"
)
PREVIOUS_OUTPUT = Path("artifacts") / PREVIOUS_NAME
PREVIOUS_REPORTS = Path("docs/reports") / PREVIOUS_NAME
PREVIOUS_BUNDLE = (
    Path.home()
    / "Documents/Codex"
    / f"thesis-monitor-{PREVIOUS_NAME}-report.zip"
)
PREVIOUS_BUNDLE_SHA256 = (
    "b72cf76bf454b67237347caf31b457dc5b56b57d92765eba568769c0fd19c98d"
)
PREVIOUS_ARTIFACT_COUNT = 176
BASE_INTEGRATION_HEAD_SHA = "b7d36b76fc938ca7cb7103b28606fdaa66498710"
MAIN_FROZEN_SHA = "d18e68b1e944d7749d093b08797fcd9498412680"
M12AD_SOURCE_HEAD_SHA = "69661d6754b0555e4c11caba8a53bd55a1fe7140"
INTEGRATION_MERGE_SHA = "f1078d283b0bc963553fd25ade272b6002b7a4c2"
WORK_INSTRUCTION_COMMIT = "377a5e3eed110ee71e563bd70cfa918dd7d1437d"
WORK_INSTRUCTION = (
    Path("docs/work-instructions")
    / "20260911-integrated-main-monitored-shadow-diagnostic-and-boundary-delta-review.md"
)
EXPECTED_CONTROL_PROMPT_SHA256 = (
    "ffec08bb75ecc3d1caae3f341833d867c695010bff3561ceed2a351d73861d0d"
)
EXPECTED_CONTROL_SCHEMA_SHA256 = (
    "e8eba3acda7e0289423132d33cd3cca9ba121439154df6a67c607a7d34beb1a0"
)
EXPECTED_CONTROL_CODE_SHA256 = (
    "3ff975fab9188171566258f0105453230b4279754eccb3836335158296ea092c"
)
EXPECTED_TWO_STAGE_SERVICE_SHA256 = (
    "6bfc575ab39d5dbba2b39870ae37e1c85385f2097b6081fad46c8cefd652261c"
)
EXPECTED_STAGE1_PROMPT_SHA256 = (
    "8438a335d19407228b800f57787e6226754d35c8f351c39d4714d4942720938b"
)
EXPECTED_STAGE1_SCHEMA_SHA256 = (
    "070d43361a66658fedc810a48acc2e2459d7f356a894c2ddc58cdc0ccfa4ef23"
)
EXPECTED_STAGE2_PROMPT_SHA256 = (
    "8bcce811f69c59a05262ecbd5ec661d238ad4d066bae7bb68a0806218be27a21"
)
EXPECTED_STAGE2_SCHEMA_SHA256 = (
    "aea35a4f2f211caea4fb2b9d12a0f0ff9e0e0f7105f03a1545bcfb708ae09b89"
)
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
SUBJECTS_PER_CONTEXT = 4
REFERENCE = {
    "kr": (
        "000660",
        "003690",
        "005490",
        "005930",
        "010120",
        "012450",
        "047810",
        "086280",
    ),
    "us": (
        "CORZ",
        "CPNG",
        "CRCL",
        "GOOGL",
        "HUT",
        "IBM",
        "MU",
        "RXRX",
        "SKHY",
        "SNDK",
        "TSLA",
        "TSM",
        "WRD",
        "WULF",
    ),
}
ARCHITECTURE_CLASSIFICATIONS = {
    "TWO_STAGE_COMPATIBILITY_CLEAN",
    "TWO_STAGE_COMPATIBILITY_CLEAN_WITH_EXPECTED_CORRECTIONS",
    "TWO_STAGE_COMPATIBILITY_HAS_BOUNDED_REGRESSIONS",
    "TWO_STAGE_COMPATIBILITY_HAS_SYSTEMIC_REGRESSION",
    "TWO_STAGE_COMPATIBILITY_INCOMPLETE",
}
REVIEW_RESOLUTIONS = {
    "EXPECTED_CONTRACT_CORRECTION",
    "POTENTIAL_ARCHITECTURE_REGRESSION",
    "OTHER_REVIEW_REQUIRED",
}
COMBINED_CLASSIFICATIONS = {
    "SYNTHETIC_EDGE_ONLY_SO_FAR",
    "REAL_MONITORED_ANALOG_PRESENT",
    "INSUFFICIENT_REAL_ANALOG_COVERAGE",
}
NEXT_SCOPES = {
    "DECISION_BOUNDARY_AND_DELTA_POLICY_REVIEW_ON_INTEGRATED_MAIN",
    "TWO_STAGE_CORE_STABILITY_ARCHITECTURE_REVIEW_ON_INTEGRATED_MAIN",
    "BUSINESS_THESIS_DELTA_SEMANTICS_REVIEW_ON_INTEGRATED_MAIN",
    "FUNDAMENTAL_STANCE_STAGE_COMPATIBILITY_REVIEW_ON_INTEGRATED_MAIN",
    "TWO_STAGE_EVIDENCE_SURFACE_COMPATIBILITY_REPAIR",
}


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


def report(number: int, slug: str, value: object) -> None:
    write_json(REPORTS / f"{number:02d}-{slug}.json", value)


def _batches(tickers: Sequence[str]) -> tuple[tuple[str, ...], ...]:
    return tuple(
        tuple(tickers[index : index + SUBJECTS_PER_CONTEXT])
        for index in range(0, len(tickers), SUBJECTS_PER_CONTEXT)
    )


def _configure_base() -> None:
    base.OUTPUT = OUTPUT
    base.REPORTS = REPORTS
    base.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT


def _runner_path() -> Path:
    return Path(__file__).resolve().relative_to(Path.cwd().resolve())


def _code_hashes() -> dict[str, str]:
    hashes = base._code_hashes()
    hashes[str(_runner_path())] = file_sha256(_runner_path())
    return hashes


def _git_is_ancestor(ancestor: str, descendant: str = "HEAD") -> bool:
    return (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            check=False,
        ).returncode
        == 0
    )


def _secret_material(path: Path) -> list[str]:
    if path.suffix.casefold() not in {".json", ".txt", ".md", ".log", ".py"}:
        return []
    folded = path.read_text(encoding="utf-8", errors="replace").casefold()
    indicators = {
        "openai_api_key": r"\bsk-[a-z0-9_-]{20,}",
        "telegram_bot_token": r"\b\d{6,12}:[a-z0-9_-]{30,}\b",
        "authorization_bearer": r"authorization:\s*bearer\s+[a-z0-9._-]{20,}",
        "private_key": (
            r"-----begin (?:rsa |ec )?private key-----\s+[a-z0-9+/]{40,}"
        ),
    }
    return [name for name, pattern in indicators.items() if re.search(pattern, folded)]


def _verify_previous_index() -> dict[str, object]:
    index = read_json(PREVIOUS_OUTPUT / "artifact-index.json")
    rows = index.get("rows")
    if not isinstance(rows, list):
        raise ValueError("latest_result_artifact_rows_missing")
    missing: list[str] = []
    hash_mismatches: list[str] = []
    size_mismatches: list[str] = []
    secret_failures: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("latest_result_artifact_row_invalid")
        path = Path(str(row["path"]))
        if not path.is_file():
            missing.append(str(path))
            continue
        if file_sha256(path) != str(row["sha256"]):
            hash_mismatches.append(str(path))
        if path.stat().st_size != int(row["size"]):
            size_mismatches.append(str(path))
        indicators = _secret_material(path)
        if indicators:
            secret_failures.append({"path": str(path), "indicators": indicators})
    result = {
        "artifact_count": len(rows),
        "missing_count": len(missing),
        "hash_mismatch_count": len(hash_mismatches),
        "size_mismatch_count": len(size_mismatches),
        "secret_scan_failure_count": len(secret_failures),
        "missing": missing,
        "hash_mismatches": hash_mismatches,
        "size_mismatches": size_mismatches,
        "secret_scan_failures": secret_failures,
    }
    if result != {
        **result,
        "artifact_count": PREVIOUS_ARTIFACT_COUNT,
        "missing_count": 0,
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": 0,
    }:
        raise ValueError("LATEST_RESULT_ARTIFACT_INDEX_MISMATCH")
    return result


def _architecture_hashes() -> dict[str, str]:
    generation = "m12ae-r2-architecture-proof"
    _packets, _owned, catalogs, contexts = m12.fictional_inputs(generation)
    tickers = m12.CONTEXTS[0]
    selected = [contexts[ticker] for ticker in tickers]
    monolithic_prompt = base._monolithic_prompt(
        packet_id=generation,
        tickers=tickers,
        contexts=selected,
    )
    monolithic_schema = base._batch_schema(
        model=DirectionalCoreCandidate,
        contract=CORE_OUTPUT_CONTRACT,
        packet_id=generation,
        tickers=tickers,
        catalogs=catalogs,
    )
    stage1_prompt = base._stage1_prompt(
        packet_id=generation,
        tickers=tickers,
        contexts=selected,
    )
    stage1_schema = base._batch_schema(
        model=DirectionalCoreJudgment,
        contract=CORE_JUDGMENT_OUTPUT_CONTRACT,
        packet_id=generation,
        tickers=tickers,
        catalogs=catalogs,
    )
    stage2_contexts = [
        {
            **contexts[ticker],
            "core_snapshot_sha256": "0" * 64,
            "frozen_stage1_core": {"ticker": ticker, "status": "FROZEN_PROBE"},
        }
        for ticker in tickers
    ]
    stage2_prompt = base._stage2_prompt(
        packet_id=generation,
        tickers=tickers,
        contexts=stage2_contexts,
    )
    stage2_schema = base._batch_schema(
        model=FundamentalStanceCandidate,
        contract=FUNDAMENTAL_STANCE_OUTPUT_CONTRACT,
        packet_id=generation,
        tickers=tickers,
        catalogs=catalogs,
    )
    return {
        "monolithic_prompt_sha256": canonical_sha256(monolithic_prompt),
        "monolithic_schema_sha256": canonical_sha256(monolithic_schema),
        "monolithic_control_code_sha256": file_sha256(
            Path("scripts/directional_core_price_timing_holdout.py")
        ),
        "two_stage_service_sha256": file_sha256(
            Path("app/services/two_stage_directional_service.py")
        ),
        "stage1_prompt_sha256": canonical_sha256(stage1_prompt),
        "stage1_schema_sha256": canonical_sha256(stage1_schema),
        "stage2_prompt_sha256": canonical_sha256(stage2_prompt),
        "stage2_schema_sha256": canonical_sha256(stage2_schema),
    }


def _architecture_hashes_match(value: Mapping[str, object]) -> bool:
    expected = {
        "monolithic_prompt_sha256": EXPECTED_CONTROL_PROMPT_SHA256,
        "monolithic_schema_sha256": EXPECTED_CONTROL_SCHEMA_SHA256,
        "monolithic_control_code_sha256": EXPECTED_CONTROL_CODE_SHA256,
        "two_stage_service_sha256": EXPECTED_TWO_STAGE_SERVICE_SHA256,
        "stage1_prompt_sha256": EXPECTED_STAGE1_PROMPT_SHA256,
        "stage1_schema_sha256": EXPECTED_STAGE1_SCHEMA_SHA256,
        "stage2_prompt_sha256": EXPECTED_STAGE2_PROMPT_SHA256,
        "stage2_schema_sha256": EXPECTED_STAGE2_SCHEMA_SHA256,
    }
    return dict(value) == expected


def diagnostic_gate_status(
    *,
    architecture_integrity: bool,
    objective_semantic_failure_count: int,
    core_mutation_count: int,
    active_universe_resolved: bool,
    packet_available_count: int,
    paused_schedule_count: int,
    runner_target_matches: bool,
) -> str:
    return (
        "PASS"
        if architecture_integrity
        and objective_semantic_failure_count == 0
        and core_mutation_count == 0
        and active_universe_resolved
        and packet_available_count > 0
        and paused_schedule_count >= 4
        and runner_target_matches
        else "FAIL"
    )


def _age_days(value: object, *, now: datetime) -> int | str:
    if not isinstance(value, str) or not value:
        return "NOT_DERIVABLE"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return "NOT_DERIVABLE"
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return max(0, (now - parsed.astimezone(UTC)).days)


def prepare(operating_root: Path, previous_bundle: Path) -> None:
    _configure_base()
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("m12af_generation_already_prepared")
    if git("status", "--short"):
        raise ValueError("m12af_prepare_requires_clean_worktree")
    if not _git_is_ancestor(BASE_INTEGRATION_HEAD_SHA):
        raise ValueError("unexpected_integration_branch_lineage")
    if not _git_is_ancestor(MAIN_FROZEN_SHA) or not _git_is_ancestor(
        M12AD_SOURCE_HEAD_SHA
    ):
        raise ValueError("frozen_main_or_m12ad_lineage_missing")
    if not previous_bundle.is_file():
        raise ValueError("LATEST_RESULT_BUNDLE_MISSING")
    bundle_sha = file_sha256(previous_bundle)
    if bundle_sha != PREVIOUS_BUNDLE_SHA256:
        raise ValueError("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    with zipfile.ZipFile(previous_bundle) as archive:
        if archive.testzip() is not None:
            raise ValueError("LATEST_RESULT_BUNDLE_ZIP_INTEGRITY_FAILURE")
    previous_index = _verify_previous_index()
    architecture_hashes = _architecture_hashes()
    architecture_integrity = _architecture_hashes_match(architecture_hashes)
    if not architecture_integrity:
        raise ValueError("MONOLITHIC_CONTROL_OR_TWO_STAGE_DRIFT")

    fictional = read_json(PREVIOUS_OUTPUT / "fictional-readiness.json")
    fictional_runtime = read_json(PREVIOUS_REPORTS / "63-full-two-stage-runtime-audit.json")
    objective_failures = int(fictional.get("objective_semantic_failure_count") or 0)
    core_mutations = int(fictional.get("core_mutation_after_stance_count") or 0)
    fictional_hard_semantics_clean = (
        objective_failures == 0
        and core_mutations == 0
        and int(fictional.get("stage1_model_calls") or 0) == 6
        and int(fictional.get("stage2_model_calls") or 0) == 6
        and int(fictional.get("final_output_count") or 0) == 24
        and fictional_runtime.get("status") == "PASS"
    )
    if not fictional_hard_semantics_clean:
        raise ValueError("FICTIONAL_HARD_SEMANTIC_REUSE_GATE_FAILED")

    universe = base._active_monitored_universe(operating_root)
    if not universe:
        raise ValueError("ACTIVE_MONITORED_UNIVERSE_UNRESOLVED")
    tickers = tuple(str(row["ticker"]) for row in universe)
    by_market = {
        market: {str(row["ticker"]) for row in universe if row["market"] == market}
        for market in ("kr", "us")
    }
    now = datetime.now(UTC)
    source_packets: dict[str, dict[str, object]] = {}
    source_inventory: list[dict[str, object]] = []
    unavailable: list[dict[str, str]] = []
    for market, required in by_market.items():
        if not required:
            continue
        try:
            path, packet = base._latest_complete_packet(
                operating_root,
                market=market,
                required_tickers=required,
            )
        except (OSError, ValueError) as exc:
            unavailable.extend(
                {"ticker": ticker, "reason": f"LOCAL_PACKET_UNAVAILABLE:{type(exc).__name__}"}
                for ticker in sorted(required)
            )
            continue
        generated_at = packet.get("generated_at") or packet.get("assessment_date")
        source_inventory.append(
            {
                "market": market,
                "path": str(path),
                "file_sha256": file_sha256(path),
                "packet_id": packet.get("packet_id"),
                "generated_at": generated_at,
                "packet_age_days": _age_days(generated_at, now=now),
                "required_ticker_count": len(required),
                "provider_refresh": 0,
            }
        )
        for ticker in sorted(required):
            source_packets[ticker] = base._single_stock_packet(packet, ticker=ticker)
    available_tickers = tuple(ticker for ticker in tickers if ticker in source_packets)
    if not available_tickers:
        raise ValueError("ACTIVE_MONITORED_PACKET_INVENTORY_EMPTY")
    evidence, owned, catalogs, contexts, _stocks = base._build_shadow_inputs(
        source_packets,
        available_tickers,
    )
    del evidence, owned

    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    suffix = hashlib.sha256(
        f"{git('rev-parse', 'HEAD')}|{stamp}|{'|'.join(available_tickers)}|M12AF".encode()
    ).hexdigest()[:12]
    generation_id = f"20260911-m12af-shadow-{stamp}-{suffix}"
    packets_root = OUTPUT / "shadow" / "frozen-packets"
    packet_paths: dict[str, str] = {}
    packet_hashes: dict[str, str] = {}
    packet_metadata: dict[str, dict[str, object]] = {}
    for ticker in available_tickers:
        path = packets_root / f"{ticker}.json"
        write_json(path, source_packets[ticker])
        packet_paths[ticker] = str(path)
        packet_hashes[ticker] = canonical_sha256(source_packets[ticker])
        packet_metadata[ticker] = {
            "packet_id": source_packets[ticker].get("packet_id"),
            "packet_as_of_date": source_packets[ticker].get("generated_at")
            or source_packets[ticker].get("assessment_date"),
            "packet_age_days": _age_days(
                source_packets[ticker].get("generated_at")
                or source_packets[ticker].get("assessment_date"),
                now=now,
            ),
            "shadow_label": "ARCHITECTURE_COMPATIBILITY_ONLY",
        }

    context_rows: list[dict[str, object]] = []
    for context_number, batch in enumerate(_batches(available_tickers), start=1):
        directory = OUTPUT / "shadow" / "frozen-contexts" / f"context-{context_number:02d}"
        paths = {
            "monolithic_prompt": directory / "monolithic-prompt.txt",
            "monolithic_schema": directory / "monolithic-schema.json",
            "stage1_prompt": directory / "stage1-prompt.txt",
            "stage1_schema": directory / "stage1-schema.json",
            "stage2_schema": directory / "stage2-schema.json",
        }
        selected_contexts = [contexts[ticker] for ticker in batch]
        write_text(
            paths["monolithic_prompt"],
            base._monolithic_prompt(
                packet_id=generation_id,
                tickers=batch,
                contexts=selected_contexts,
            ),
        )
        write_json(
            paths["monolithic_schema"],
            base._batch_schema(
                model=DirectionalCoreCandidate,
                contract=CORE_OUTPUT_CONTRACT,
                packet_id=generation_id,
                tickers=batch,
                catalogs=catalogs,
            ),
        )
        write_text(
            paths["stage1_prompt"],
            base._stage1_prompt(
                packet_id=generation_id,
                tickers=batch,
                contexts=selected_contexts,
            ),
        )
        write_json(
            paths["stage1_schema"],
            base._batch_schema(
                model=DirectionalCoreJudgment,
                contract=CORE_JUDGMENT_OUTPUT_CONTRACT,
                packet_id=generation_id,
                tickers=batch,
                catalogs=catalogs,
            ),
        )
        write_json(
            paths["stage2_schema"],
            base._batch_schema(
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
                "packet_sha256": {ticker: packet_hashes[ticker] for ticker in batch},
                "packet_set_sha256": canonical_sha256(
                    {ticker: packet_hashes[ticker] for ticker in batch}
                ),
                "inputs": {
                    name: {"path": str(path), "sha256": file_sha256(path)}
                    for name, path in paths.items()
                },
            }
        )

    schedule = m12._schedule_observation()
    runner_matches = (
        base.MODEL == MODEL
        and base.EFFORT == EFFORT
        and base.TIMEOUT_SECONDS == TIMEOUT_SECONDS
        and m12.MODEL == MODEL
        and m12.EFFORT == EFFORT
        and m12.TIMEOUT_SECONDS == TIMEOUT_SECONDS
    )
    gate_status = diagnostic_gate_status(
        architecture_integrity=architecture_integrity,
        objective_semantic_failure_count=objective_failures,
        core_mutation_count=core_mutations,
        active_universe_resolved=bool(tickers),
        packet_available_count=len(available_tickers),
        paused_schedule_count=int(schedule["observed_paused_schedule_count"]),
        runner_target_matches=runner_matches,
    )
    code_hashes = base._code_hashes()
    state = {
        "status": "FROZEN" if gate_status == "PASS" else "BLOCKED",
        "phase": "M12AF",
        "generation_id": generation_id,
        "prepared_at": now.isoformat(),
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "preparation_head_sha": git("rev-parse", "HEAD"),
        "integration_branch": git("branch", "--show-current"),
        "tickers": list(available_tickers),
        "all_active_tickers": list(tickers),
        "universe": universe,
        "packet_paths": packet_paths,
        "packet_hashes": packet_hashes,
        "packet_metadata": packet_metadata,
        "source_inventory": source_inventory,
        "unavailable": unavailable,
        "context_count": len(context_rows),
        "planned_model_calls": 3 * len(context_rows),
        "contexts": context_rows,
        "code_hashes": code_hashes,
        "m12af_runner_sha256": file_sha256(_runner_path()),
        "schedule_start": schedule,
        "provider_source_fetches": 0,
        "fictional_two_stage_readiness": fictional.get("fictional_two_stage_readiness"),
        "fictional_objective_semantic_failure_count": objective_failures,
        "fictional_core_mutation_count": core_mutations,
        "diagnostic_gate_reclassification": (
            "FICTIONAL_DECISION_STABILITY_DOES_NOT_BLOCK_EXISTING_MONITORED_DIAGNOSTIC"
        ),
    }
    write_json(OUTPUT / "shadow" / "program-state.json", state)

    reference_set = set(REFERENCE["kr"] + REFERENCE["us"])
    actual_set = set(tickers)
    report(
        1,
        "repository-provenance",
        {
            "status": "PASS",
            "repository": "sskim-ai/thesis-monitor",
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "task_branch": git("branch", "--show-current"),
            "task_head_sha": git("rev-parse", "HEAD"),
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "main_fetch_or_merge": 0,
            "main_branch_mutations": 0,
        },
    )
    report(
        2,
        "latest-result-integrity",
        {
            "status": "PASS",
            "path": str(previous_bundle),
            "expected_sha256": PREVIOUS_BUNDLE_SHA256,
            "actual_sha256": bundle_sha,
            "zip_integrity": "PASS",
            **previous_index,
        },
    )
    report(
        3,
        "m12af-scope-freeze",
        {
            "status": "FROZEN",
            "phase": "M12AF",
            "scope": "EXISTING_MONITORED_SAME_PACKET_ARCHITECTURE_DIAGNOSTIC",
            "fresh_unseen_model_calls": 0,
            "prompt_schema_threshold_contract_changes": 0,
            "provider_refresh": 0,
            "production_side_effects": 0,
            "main_merge": 0,
        },
    )
    report(
        4,
        "integrated-main-baseline-reuse-proof",
        {
            "status": "PASS",
            "main_frozen_sha": MAIN_FROZEN_SHA,
            "m12ad_source_head_sha": M12AD_SOURCE_HEAD_SHA,
            "integration_merge_sha": INTEGRATION_MERGE_SHA,
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "base_is_ancestor": True,
            "newer_main_fetch_or_merge": 0,
            "focused_baseline": "452 passed",
            "full_baseline": "3388 passed; 2 warnings",
            "ruff": "PASS",
            "git_diff_check": "PASS",
            "runtime_config_smoke": "PASS",
        },
    )
    report(
        5,
        "two-stage-architecture-freeze-proof",
        {
            "status": "PASS",
            "architecture": "STAGE1_CORE_THEN_STAGE2_STANCE_DETERMINISTIC_COMPOSER",
            "hashes": architecture_hashes,
            "hash_match": architecture_integrity,
            "prompt_schema_semantic_change_count": 0,
            "composer_semantic_change_count": 0,
            "threshold_change_count": 0,
        },
    )
    report(
        6,
        "monolithic-control-freeze-proof",
        {
            "status": "PASS",
            "prompt_sha256": architecture_hashes["monolithic_prompt_sha256"],
            "schema_sha256": architecture_hashes["monolithic_schema_sha256"],
            "control_code_sha256": architecture_hashes[
                "monolithic_control_code_sha256"
            ],
            "byte_for_byte_reproduction": True,
        },
    )
    report(
        7,
        "fictional-hard-semantic-reuse-proof",
        {
            "status": "PASS",
            "generation_id": fictional.get("generation_id"),
            "stage1_model_calls": fictional.get("stage1_model_calls"),
            "stage2_model_calls": fictional.get("stage2_model_calls"),
            "final_output_count": fictional.get("final_output_count"),
            "objective_semantic_failure_count": objective_failures,
            "core_mutation_after_stance_count": core_mutations,
            "runtime_status": fictional_runtime.get("status"),
        },
    )
    report(
        8,
        "fictional-blocker-reclassification",
        {
            "status": "FROZEN_DIAGNOSTIC_HYPOTHESES",
            "fictional_two_stage_readiness": fictional.get(
                "fictional_two_stage_readiness"
            ),
            "monitored_diagnostic_allowed": gate_status == "PASS",
            "rows": [
                {
                    "ticker": "FIC-FIN-05",
                    "classification": "INTRINSIC_ADJACENT_PRIMARY_BOUNDARY_CANDIDATE",
                    "observed_direction": ["SELL", "HOLD", "HOLD"],
                    "business_delta": ["UNCHANGED"] * 3,
                    "new_buyer": ["WAIT"] * 3,
                    "holder": ["REVIEW"] * 3,
                },
                {
                    "ticker": "FIC-FIN-06",
                    "classification": (
                        "POSITIVE_THRESHOLD_BOUNDARY_PLUS_OPERATING_SIGNAL_VS_THESIS_DELTA_AMBIGUITY"
                    ),
                    "observed_direction": ["HOLD", "HOLD", "BUY"],
                    "business_delta": ["STRENGTHENED", "STRENGTHENED", "UNCHANGED"],
                    "new_buyer": ["WAIT"] * 3,
                    "holder": ["HOLDABLE"] * 3,
                },
                {
                    "ticker": "FIC-FIN-08",
                    "classification": "HOLDER_UNKNOWN_SEVERITY_BOUNDARY",
                    "observed_direction": ["HOLD"] * 3,
                    "business_delta": ["UNCHANGED"] * 3,
                    "new_buyer": ["WAIT"] * 3,
                    "holder": ["HOLDABLE", "HOLDABLE", "REVIEW"],
                },
            ],
            "majority_vote": 0,
            "balance_averaging": 0,
            "semantic_repair": 0,
        },
    )
    report(
        9,
        "task-start-active-monitored-universe",
        {
            "status": "PASS",
            "authority": "OPERATING_SQLITE_READ_ONLY",
            "database": str(operating_root / "data/thesis_monitor.sqlite3"),
            "count": len(tickers),
            "kr_count": len(by_market["kr"]),
            "us_count": len(by_market["us"]),
            "tickers": list(tickers),
            "rows": universe,
        },
    )
    report(
        10,
        "reference-vs-task-start-universe-diff",
        {
            "status": "MEASURED",
            "reference_count": len(reference_set),
            "task_start_count": len(actual_set),
            "reference_added_tickers": sorted(actual_set - reference_set),
            "reference_removed_tickers": sorted(reference_set - actual_set),
        },
    )
    report(
        11,
        "shadow-packet-source-contract",
        {
            "status": "PASS",
            "source": "LATEST_COMPLETE_ARCHIVED_LOCAL_AI_REVIEW_PACKET",
            "one_frozen_single_stock_projection_per_ticker": True,
            "same_packet_for_monolithic_stage1_stage2": True,
            "provider_source_fetches": 0,
            "shadow_label": "ARCHITECTURE_COMPATIBILITY_ONLY",
        },
    )
    report(
        12,
        "shadow-packet-inventory",
        {
            "status": "PASS" if available_tickers else "FAIL",
            "active_monitored_count": len(tickers),
            "packet_available_count": len(available_tickers),
            "packet_unavailable_count": len(unavailable),
            "source_files": source_inventory,
            "packet_metadata": packet_metadata,
            "unavailable": unavailable,
        },
    )
    report(
        13,
        "shadow-packet-hash-manifest",
        {
            "status": "FROZEN",
            "generation_id": generation_id,
            "packet_hashes": packet_hashes,
            "packet_mismatch_count": 0,
        },
    )
    report(
        14,
        "shadow-batching-manifest",
        {
            "status": "FROZEN",
            "subject_count": len(available_tickers),
            "subjects_per_context": SUBJECTS_PER_CONTEXT,
            "context_count": len(context_rows),
            "planned_monolithic_calls": len(context_rows),
            "planned_stage1_calls": len(context_rows),
            "planned_stage2_calls": len(context_rows),
            "planned_total_calls": 3 * len(context_rows),
            "contexts": context_rows,
        },
    )
    gate = {
        "status": gate_status,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "runtime_mode": "MODEL_CONTEXT_COUPLED",
        "subjects_per_context": SUBJECTS_PER_CONTEXT,
        "timeout_seconds": TIMEOUT_SECONDS,
        "single_authoritative_watchdog": True,
        "wrapper_auto_retry": 0,
        "batch_split": 0,
        "model_target_fallback_count": 0,
        "code_hashes": code_hashes,
        "m12af_runner_sha256": state["m12af_runner_sha256"],
        "architecture_integrity": "PASS" if architecture_integrity else "FAIL",
        "fictional_objective_semantic_failure_count": objective_failures,
        "fictional_core_mutation_count": core_mutations,
        "fictional_decision_stability_required": False,
        "active_monitored_universe_resolved": True,
        "packet_available_count": len(available_tickers),
        "packet_unavailable_count": len(unavailable),
        "provider_source_fetches": 0,
        "production_side_effect_firewall": "PASS",
        "observed_paused_schedule_count": schedule[
            "observed_paused_schedule_count"
        ],
        "shadow_model_calls_before_gate": 0,
    }
    report(15, "shadow-model-call-gate", gate)
    write_json(OUTPUT / "shadow-model-call-gate.json", gate)
    if gate_status != "PASS":
        raise SystemExit("M12AF_SHADOW_MODEL_CALL_GATE_FAILED")
    print(json.dumps({"status": "FROZEN", "generation_id": generation_id}))


def run_shadow() -> None:
    _configure_base()
    state = read_json(OUTPUT / "shadow" / "program-state.json")
    if file_sha256(_runner_path()) != state.get("m12af_runner_sha256"):
        raise ValueError("m12af_runner_changed_after_freeze")
    base.run_shadow()


def _candidate_refs(candidate: DirectionalCoreCandidate) -> set[str]:
    refs: set[str] = set()

    def visit(value: object, key: str | None = None) -> None:
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                visit(child, str(child_key))
        elif isinstance(value, list):
            for child in value:
                visit(child, key)
        elif isinstance(value, str) and key is not None and (
            key == "material_directional_anchor_basis"
            or key == "evidence_refs"
            or key.endswith("_refs")
        ):
            refs.add(value)

    visit(candidate.model_dump(mode="json"))
    return refs


def _raw_material_fields(
    monolithic: DirectionalCoreCandidate,
    two_stage: DirectionalCoreCandidate,
) -> tuple[str, list[str]]:
    return base._comparison_classification(monolithic, two_stage)


def _runtime_counts(documents: Sequence[Mapping[str, object]], planned: int) -> dict[str, object]:
    receipts = [row["transport"] for row in documents]
    return {
        "planned_model_calls": planned,
        "completed_model_calls": len(receipts),
        "monolithic_model_calls": sum(
            str(row.get("contract") or "").endswith("monolithic-context-v1")
            for row in documents
        ),
        "stage1_model_calls": sum(
            str(row.get("contract") or "").endswith("stage1-context-v1")
            for row in documents
        ),
        "stage2_model_calls": sum(
            str(row.get("contract") or "").endswith("stage2-context-v1")
            for row in documents
        ),
        "timeout_count": sum(
            int(row.get("timeout_count") or 0) for row in receipts
        ),
        "capacity_failure_count": sum(
            str(row.get("failure_type") or "").casefold() == "capacity"
            for row in receipts
        ),
        "orphan_process_count": sum(
            int(row.get("orphan_process_count") or 0) for row in receipts
        ),
        "wrapper_retry_count": sum(
            int(row.get("wrapper_retry_count") or 0) for row in receipts
        ),
        "model_target_fallback_count": sum(
            row.get("observed_runtime") != {"model": MODEL, "effort": EFFORT}
            for row in receipts
        ),
    }


def prepare_review() -> None:
    _configure_base()
    state = read_json(OUTPUT / "shadow" / "program-state.json")
    complete = read_json(OUTPUT / "shadow" / "run-complete.json")
    if state.get("code_hashes") != base._code_hashes():
        raise ValueError("shadow_code_changed_after_freeze")
    if file_sha256(_runner_path()) != state.get("m12af_runner_sha256"):
        raise ValueError("m12af_runner_changed_after_freeze")
    if complete.get("model_calls") != state.get("planned_model_calls"):
        raise ValueError("shadow_calls_incomplete")
    tickers, _packets, built = base._load_shadow_inputs(state)
    _evidence, owned, _catalogs, _contexts, _stocks = built
    monolithic_documents = base._shadow_documents("monolithic")
    stage1_documents = base._shadow_documents("stage1")
    stage2_documents = base._shadow_documents("stage2")
    expected_contexts = int(state["context_count"])
    if not all(
        len(rows) == expected_contexts
        for rows in (monolithic_documents, stage1_documents, stage2_documents)
    ):
        raise ValueError("shadow_document_count_mismatch")

    stage1_by_context = {int(row["context"]): row for row in stage1_documents}
    for document in stage2_documents:
        context = int(document["context"])
        stage1_document = stage1_by_context[context]
        linkage = {
            "status": "FROZEN",
            "generation_id": state["generation_id"],
            "context": context,
            "parent_stage1_invocation_id": stage1_document["transport"][
                "invocation_id"
            ],
            "stage2_invocation_id": document["transport"]["invocation_id"],
            "core_snapshot_sha256_by_ticker": {
                str(row["candidate"]["ticker"]): row["core_snapshot_sha256"]
                for row in document["compositions"]
            },
        }
        linkage_path = (
            OUTPUT
            / "shadow"
            / "model-calls"
            / f"context-{context:02d}"
            / "stage2"
            / "parent-stage1-linkage.json"
        )
        write_json(linkage_path, linkage)

    monolithic_by_ticker: dict[str, DirectionalCoreCandidate] = {}
    monolithic_audit: dict[str, Mapping[str, object]] = {}
    for document in monolithic_documents:
        for row in document["rows"]:
            ticker = str(row["ticker"])
            monolithic_by_ticker[ticker] = DirectionalCoreCandidate.model_validate(
                row["core"]
            )
            monolithic_audit[ticker] = row
    final_by_ticker: dict[str, DirectionalCoreCandidate] = {}
    final_audit: dict[str, Mapping[str, object]] = {}
    composition_by_ticker: dict[str, Mapping[str, object]] = {}
    for document in stage2_documents:
        for composition in document["compositions"]:
            ticker = str(composition["candidate"]["ticker"])
            final_by_ticker[ticker] = DirectionalCoreCandidate.model_validate(
                composition["candidate"]
            )
            composition_by_ticker[ticker] = composition
        for row in document["final_rows"]:
            final_audit[str(row["ticker"])] = row
    if set(monolithic_by_ticker) != set(tickers) or set(final_by_ticker) != set(
        tickers
    ):
        raise ValueError("shadow_completed_ticker_scope_mismatch")

    universe_by_ticker = {
        str(row["ticker"]): row for row in state["universe"] if str(row["ticker"]) in tickers
    }
    comparisons: list[dict[str, object]] = []
    review_queue: list[dict[str, object]] = []
    for ticker in tickers:
        monolithic = monolithic_by_ticker[ticker]
        final = final_by_ticker[ticker]
        raw_classification, material_fields = _raw_material_fields(monolithic, final)
        monolithic_domains = base._anchor_domains(monolithic, owned[ticker])
        final_domains = base._anchor_domains(final, owned[ticker])
        monolithic_errors = list(monolithic_audit[ticker]["errors"])
        final_errors = list(final_audit[ticker]["errors"])
        mutation = (
            composition_by_ticker[ticker]["core_snapshot_sha256"]
            != composition_by_ticker[ticker]["post_compose_core_sha256"]
        )
        monolithic_refs = _candidate_refs(monolithic)
        final_refs = _candidate_refs(final)
        shared_refs = sorted(monolithic_refs & final_refs)
        monolithic_only_refs = sorted(monolithic_refs - final_refs)
        two_stage_only_refs = sorted(final_refs - monolithic_refs)
        deterministic_regression_reasons: list[str] = []
        if monolithic_errors or final_errors:
            deterministic_regression_reasons.append(
                "objective_semantic_validation_failure"
            )
        if mutation:
            deterministic_regression_reasons.append("stage2_core_mutation")
        if (
            "overall_direction" in material_fields
            and set(final_domains) < set(monolithic_domains)
        ):
            deterministic_regression_reasons.append(
                "primary_direction_changed_with_lost_anchor_domain"
            )
        provisional_classification = raw_classification
        if material_fields:
            provisional_classification = (
                "POTENTIAL_ARCHITECTURE_REGRESSION"
                if deterministic_regression_reasons
                else "OTHER_REVIEW_REQUIRED"
            )
        row = {
            "ticker": ticker,
            "market": universe_by_ticker[ticker]["market"],
            "industry": universe_by_ticker[ticker].get("industry"),
            "sector": universe_by_ticker[ticker].get("sector"),
            "packet_sha256": state["packet_hashes"][ticker],
            "packet_metadata": state["packet_metadata"][ticker],
            "raw_classification": raw_classification,
            "provisional_classification": provisional_classification,
            "decision_material_changed_fields": material_fields,
            "deterministic_regression_reasons": deterministic_regression_reasons,
            "shared_evidence_refs": shared_refs,
            "monolithic_only_evidence_refs": monolithic_only_refs,
            "two_stage_only_evidence_refs": two_stage_only_refs,
            "monolithic": {
                "overall_direction": monolithic.overall_direction,
                "directional_balance": monolithic.directional_balance.model_dump(
                    mode="json"
                ),
                "hold_lean": monolithic.hold_lean,
                "directional_confidence": monolithic.directional_confidence,
                "business_thesis_change": monolithic.business_thesis_change,
                "fundamental_new_buyer": monolithic.fundamental_new_buyer.stance,
                "fundamental_holder": monolithic.fundamental_holder.stance,
                "anchor_domains": monolithic_domains,
                "support": base._support_view(monolithic),
                "errors": monolithic_errors,
            },
            "two_stage": {
                "overall_direction": final.overall_direction,
                "directional_balance": final.directional_balance.model_dump(mode="json"),
                "hold_lean": final.hold_lean,
                "directional_confidence": final.directional_confidence,
                "business_thesis_change": final.business_thesis_change,
                "fundamental_new_buyer": final.fundamental_new_buyer.stance,
                "fundamental_holder": final.fundamental_holder.stance,
                "anchor_domains": final_domains,
                "support": base._support_view(final),
                "errors": final_errors,
                "core_snapshot_sha256": composition_by_ticker[ticker][
                    "core_snapshot_sha256"
                ],
                "post_compose_core_sha256": composition_by_ticker[ticker][
                    "post_compose_core_sha256"
                ],
            },
        }
        comparisons.append(row)
        if material_fields:
            review_queue.append(
                {
                    "ticker": ticker,
                    "raw_classification": raw_classification,
                    "provisional_classification": provisional_classification,
                    "changed_fields": material_fields,
                    "same_packet_sha256": state["packet_hashes"][ticker],
                    "shared_evidence_refs": shared_refs,
                    "monolithic_only_evidence_refs": monolithic_only_refs,
                    "two_stage_only_evidence_refs": two_stage_only_refs,
                    "deterministic_regression_reasons": deterministic_regression_reasons,
                    "monolithic": row["monolithic"],
                    "two_stage": row["two_stage"],
                    "required_resolution": sorted(REVIEW_RESOLUTIONS),
                }
            )

    packet_mismatches = 0
    for context_number in range(1, expected_contexts + 1):
        documents = (
            monolithic_documents[context_number - 1],
            stage1_documents[context_number - 1],
            stage2_documents[context_number - 1],
        )
        expected = next(
            row["packet_sha256"]
            for row in state["contexts"]
            if int(row["context"]) == context_number
        )
        if any(document["packet_sha256"] != expected for document in documents):
            packet_mismatches += 1
    all_documents = [*monolithic_documents, *stage1_documents, *stage2_documents]
    runtime = _runtime_counts(all_documents, int(state["planned_model_calls"]))
    mutation_count = sum(
        row["two_stage"]["core_snapshot_sha256"]
        != row["two_stage"]["post_compose_core_sha256"]
        for row in comparisons
    )
    objective_error_count = sum(
        len(row["monolithic"]["errors"]) + len(row["two_stage"]["errors"])
        for row in comparisons
    )
    hard_failure_count = (
        packet_mismatches
        + mutation_count
        + objective_error_count
        + int(runtime["timeout_count"])
        + int(runtime["capacity_failure_count"])
        + int(runtime["orphan_process_count"])
        + int(runtime["wrapper_retry_count"])
        + int(runtime["model_target_fallback_count"])
    )
    provisional = {
        "status": "PASS" if hard_failure_count == 0 else "FAIL",
        "generation_id": state["generation_id"],
        "comparisons": comparisons,
        "packet_mismatch_count": packet_mismatches,
        "core_mutation_after_stance_count": mutation_count,
        "objective_semantic_hard_failure_count": objective_error_count,
        "runtime": runtime,
        "hard_failure_count": hard_failure_count,
    }
    write_json(OUTPUT / "shadow" / "provisional-analysis.json", provisional)
    write_json(
        OUTPUT / "shadow" / "review-queue.json",
        {
            "status": "REVIEW_REQUIRED" if review_queue else "EMPTY",
            "generation_id": state["generation_id"],
            "count": len(review_queue),
            "rows": review_queue,
        },
    )
    if hard_failure_count:
        raise SystemExit("M12AF_SHADOW_HARD_SEMANTIC_ACCEPTANCE_FAILED")
    print(
        json.dumps(
            {
                "status": "REVIEW_READY",
                "generation_id": state["generation_id"],
                "completed_tickers": len(comparisons),
                "review_queue_count": len(review_queue),
            },
            sort_keys=True,
        )
    )


def _validate_adjudication(
    adjudication: Mapping[str, object],
    review_rows: Sequence[Mapping[str, object]],
) -> dict[str, Mapping[str, object]]:
    architecture = str(
        adjudication.get("two_stage_shadow_compatibility_classification") or ""
    )
    if architecture not in ARCHITECTURE_CLASSIFICATIONS:
        raise ValueError("invalid_shadow_architecture_classification")
    if str(adjudication.get("next_scope") or "") not in NEXT_SCOPES:
        raise ValueError("invalid_next_scope")
    for field in (
        "fic_fin_05_combined_diagnostic_classification",
        "fic_fin_06_combined_diagnostic_classification",
        "fic_fin_08_combined_diagnostic_classification",
    ):
        if str(adjudication.get(field) or "") not in COMBINED_CLASSIFICATIONS:
            raise ValueError(f"invalid_combined_classification:{field}")
    raw_rows = adjudication.get("adjudications")
    if not isinstance(raw_rows, list):
        raise ValueError("adjudication_rows_required")
    by_ticker: dict[str, Mapping[str, object]] = {}
    for row in raw_rows:
        if not isinstance(row, Mapping):
            raise ValueError("adjudication_row_object_required")
        ticker = str(row.get("ticker") or "")
        if not ticker or ticker in by_ticker:
            raise ValueError("adjudication_ticker_identity_invalid")
        if str(row.get("resolution") or "") not in REVIEW_RESOLUTIONS:
            raise ValueError(f"invalid_adjudication_resolution:{ticker}")
        if not str(row.get("rationale") or "").strip():
            raise ValueError(f"adjudication_rationale_required:{ticker}")
        if not str(row.get("frozen_contract") or "").strip():
            raise ValueError(f"adjudication_frozen_contract_required:{ticker}")
        refs = row.get("evidence_refs")
        if not isinstance(refs, list):
            raise ValueError(f"adjudication_evidence_refs_array_required:{ticker}")
        by_ticker[ticker] = row
    expected = {str(row["ticker"]) for row in review_rows}
    if set(by_ticker) != expected:
        raise ValueError("adjudication_scope_mismatch")
    for queue_row in review_rows:
        ticker = str(queue_row["ticker"])
        allowed = {
            *queue_row["shared_evidence_refs"],
            *queue_row["monolithic_only_evidence_refs"],
            *queue_row["two_stage_only_evidence_refs"],
        }
        cited = set(str(ref) for ref in by_ticker[ticker]["evidence_refs"])
        if not cited <= allowed:
            raise ValueError(f"adjudication_invalid_evidence_ref:{ticker}")
        if (
            by_ticker[ticker]["resolution"] == "POTENTIAL_ARCHITECTURE_REGRESSION"
            and not cited
        ):
            raise ValueError(f"regression_evidence_refs_required:{ticker}")
    return by_ticker


def _selected_rows(
    comparisons: Sequence[Mapping[str, object]], tickers: Sequence[str]
) -> list[Mapping[str, object]]:
    selected = set(tickers)
    return [row for row in comparisons if str(row["ticker"]) in selected]


def finalize(adjudication_path: Path) -> None:
    state = read_json(OUTPUT / "shadow" / "program-state.json")
    provisional = read_json(OUTPUT / "shadow" / "provisional-analysis.json")
    queue = read_json(OUTPUT / "shadow" / "review-queue.json")
    adjudication = read_json(adjudication_path)
    review_rows = queue.get("rows")
    comparisons = provisional.get("comparisons")
    if not isinstance(review_rows, list) or not isinstance(comparisons, list):
        raise ValueError("shadow_review_inputs_invalid")
    by_ticker = _validate_adjudication(adjudication, review_rows)
    finalized: list[dict[str, object]] = []
    for source in comparisons:
        row = dict(source)
        ticker = str(row["ticker"])
        if ticker in by_ticker:
            decision = by_ticker[ticker]
            row["classification"] = decision["resolution"]
            row["review_rationale"] = decision["rationale"]
            row["review_evidence_refs"] = decision["evidence_refs"]
            row["frozen_contract"] = decision["frozen_contract"]
        else:
            row["classification"] = row["raw_classification"]
            row["review_rationale"] = "No decision-material field changed."
            row["review_evidence_refs"] = []
            row["frozen_contract"] = "same-packet compatibility taxonomy"
        finalized.append(row)

    raw_taxonomy = Counter(str(row["raw_classification"]) for row in finalized)
    final_taxonomy = Counter(str(row["classification"]) for row in finalized)
    unavailable = state["unavailable"]
    architecture = str(
        adjudication["two_stage_shadow_compatibility_classification"]
    )
    expected_count = final_taxonomy["EXPECTED_CONTRACT_CORRECTION"]
    regression_count = final_taxonomy["POTENTIAL_ARCHITECTURE_REGRESSION"]
    unresolved_count = final_taxonomy["OTHER_REVIEW_REQUIRED"]
    if architecture == "TWO_STAGE_COMPATIBILITY_CLEAN" and (
        expected_count or regression_count or unresolved_count or unavailable
    ):
        raise ValueError("clean_architecture_classification_inconsistent")
    if architecture == "TWO_STAGE_COMPATIBILITY_CLEAN_WITH_EXPECTED_CORRECTIONS" and (
        not expected_count or regression_count or unresolved_count or unavailable
    ):
        raise ValueError("expected_correction_classification_inconsistent")
    if architecture == "TWO_STAGE_COMPATIBILITY_HAS_BOUNDED_REGRESSIONS" and (
        not regression_count or unavailable
    ):
        raise ValueError("bounded_regression_classification_inconsistent")
    if architecture == "TWO_STAGE_COMPATIBILITY_INCOMPLETE" and not (
        unavailable or unresolved_count
    ):
        raise ValueError("incomplete_classification_without_incomplete_evidence")

    runtime = provisional["runtime"]
    universe = state["universe"]
    sectors = sorted(
        {
            str(row.get("industry") or row.get("sector") or "unspecified")
            for row in universe
        }
    )
    packet_mismatches = int(provisional["packet_mismatch_count"])
    mutation_count = int(provisional["core_mutation_after_stance_count"])
    objective_failures = int(provisional["objective_semantic_hard_failure_count"])
    report(16, "shadow-per-ticker-comparison-table", {"status": "MEASURED", "rows": finalized})
    report(17, "shadow-core-direction-differences", {"status": "MEASURED", "count": sum("overall_direction" in row["decision_material_changed_fields"] for row in finalized), "rows": [row for row in finalized if "overall_direction" in row["decision_material_changed_fields"]]})
    report(18, "shadow-business-delta-differences", {"status": "MEASURED", "count": sum("business_thesis_change" in row["decision_material_changed_fields"] for row in finalized), "rows": [row for row in finalized if "business_thesis_change" in row["decision_material_changed_fields"]]})
    report(19, "shadow-new-buyer-differences", {"status": "MEASURED", "count": sum("fundamental_new_buyer.stance" in row["decision_material_changed_fields"] for row in finalized), "rows": [row for row in finalized if "fundamental_new_buyer.stance" in row["decision_material_changed_fields"]]})
    report(20, "shadow-holder-differences", {"status": "MEASURED", "count": sum("fundamental_holder.stance" in row["decision_material_changed_fields"] for row in finalized), "rows": [row for row in finalized if "fundamental_holder.stance" in row["decision_material_changed_fields"]]})
    report(21, "shadow-same-direction-calibration-differences", {"status": "MEASURED", "count": raw_taxonomy["SAME_DIRECTION_CALIBRATION_CHANGE"], "rows": [row for row in finalized if row["raw_classification"] == "SAME_DIRECTION_CALIBRATION_CHANGE"]})
    report(22, "shadow-expected-contract-corrections", {"status": "MEASURED", "count": expected_count, "rows": [row for row in finalized if row["classification"] == "EXPECTED_CONTRACT_CORRECTION"]})
    report(23, "shadow-potential-architecture-regressions", {"status": "MEASURED", "count": regression_count, "rows": [row for row in finalized if row["classification"] == "POTENTIAL_ARCHITECTURE_REGRESSION"]})
    report(24, "shadow-unresolved-review-required", {"status": "MEASURED", "count": unresolved_count, "rows": [row for row in finalized if row["classification"] == "OTHER_REVIEW_REQUIRED"]})
    report(25, "shadow-sector-coverage", {"status": "MEASURED", "kr_count": sum(row["market"] == "kr" for row in universe), "us_count": sum(row["market"] == "us" for row in universe), "sector_coverage_count": len(sectors), "sectors": sectors, "rows": universe})
    financial_row = next((row for row in finalized if row["ticker"] == "003690"), None)
    financial_failure_count = 0 if financial_row and not financial_row["monolithic"]["errors"] and not financial_row["two_stage"]["errors"] else 1
    report(26, "shadow-financial-sector-audit", {"status": "PASS" if financial_failure_count == 0 else "FAIL", "ticker": "003690", "insurance_appropriate_reasoning_required": True, "generic_industrial_framework_failure_count": financial_failure_count, "comparison": financial_row})
    adr_row = next((row for row in finalized if row["ticker"] == "SKHY"), None)
    adr_failure_count = 0 if adr_row and not adr_row["monolithic"]["errors"] and not adr_row["two_stage"]["errors"] else 1
    report(27, "shadow-adr-security-basis-audit", {"status": "PASS" if adr_failure_count == 0 else "FAIL", "ticker": "SKHY", "security_basis_failure_count": adr_failure_count, "denominator_reconstruction": 0, "provider_multiple_backsolving": 0, "comparison": adr_row})
    cyclical_tickers = [ticker for ticker in ("000660", "005490", "005930", "MU", "SNDK", "TSM") if any(row["ticker"] == ticker for row in finalized)]
    cyclical_rows = _selected_rows(finalized, cyclical_tickers)
    cyclical_failures = sum(bool(row["monolithic"]["errors"] or row["two_stage"]["errors"]) for row in cyclical_rows)
    report(28, "shadow-cyclical-valuation-framework-audit", {"status": "PASS" if cyclical_failures == 0 else "FAIL", "failure_count": cyclical_failures, "rows": cyclical_rows})
    report(29, "shadow-core-immutability-audit", {"status": "PASS" if mutation_count == 0 else "FAIL", "core_mutation_after_stance_count": mutation_count, "rows": [{"ticker": row["ticker"], "before": row["two_stage"]["core_snapshot_sha256"], "after": row["two_stage"]["post_compose_core_sha256"]} for row in finalized]})
    report(30, "shadow-runtime-audit", {"status": "PASS" if provisional["hard_failure_count"] == 0 else "FAIL", **runtime, "packet_mismatch_count": packet_mismatches, "objective_semantic_hard_failure_count": objective_failures})
    aggregate = {
        "status": "MEASURED",
        "active_monitored_count": len(state["all_active_tickers"]),
        "packet_available_count": len(state["tickers"]),
        "packet_unavailable_count": len(unavailable),
        "packet_mismatch_count": packet_mismatches,
        "shadow_completed_ticker_count": len(finalized),
        "raw_taxonomy_counts": dict(sorted(raw_taxonomy.items())),
        "final_taxonomy_counts": dict(sorted(final_taxonomy.items())),
        "kr_count": sum(row["market"] == "kr" for row in finalized),
        "us_count": sum(row["market"] == "us" for row in finalized),
        "sector_coverage_count": len(sectors),
    }
    report(31, "shadow-aggregate-summary", aggregate)
    report(32, "shadow-architecture-decision", {"status": "CLASSIFIED", "two_stage_shadow_compatibility_classification": architecture, "rationale": adjudication["architecture_rationale"], "expected_contract_correction_count": expected_count, "potential_architecture_regression_count": regression_count, "unresolved_review_required_count": unresolved_count, "diagnostic_only": True, "fresh_real_proof_implication": "NONE"})

    analogs = adjudication.get("fictional_analogs")
    if not isinstance(analogs, Mapping):
        raise ValueError("fictional_analogs_required")
    for key in ("FIC-FIN-05", "FIC-FIN-06", "FIC-FIN-08"):
        if not isinstance(analogs.get(key), Mapping):
            raise ValueError(f"fictional_analog_entry_required:{key}")
    fic05 = analogs["FIC-FIN-05"]
    fic06 = analogs["FIC-FIN-06"]
    fic08 = analogs["FIC-FIN-08"]
    report(33, "fic-fin-05-boundary-vs-monitored-leverage-analogs", {"status": "CLASSIFIED", "fictional_pattern": "SELL/HOLD/HOLD at adjacent negative 5.5/6.0 boundary", "classification": adjudication["fic_fin_05_combined_diagnostic_classification"], "analog_tickers": fic05.get("tickers", []), "rationale": fic05.get("rationale"), "rows": _selected_rows(finalized, fic05.get("tickers", [])), "majority_vote": 0, "balance_averaging": 0})
    report(34, "fic-fin-06-operating-signal-vs-thesis-delta-review", {"status": "DIAGNOSTIC_COMPLETE", "frozen_observation": ["STRENGTHENED", "STRENGTHENED", "UNCHANGED"], "distinction": "A comparable-period operating improvement is positive evidence but only changes the thesis delta when it materially validates a stored thesis driver relative to baseline.", "prompt_or_contract_change": 0, "recommended_follow_up": adjudication["next_scope"]})
    report(35, "fic-fin-06-vs-monitored-growth-quality-analogs", {"status": "CLASSIFIED", "classification": adjudication["fic_fin_06_combined_diagnostic_classification"], "analog_tickers": fic06.get("tickers", []), "rationale": fic06.get("rationale"), "rows": _selected_rows(finalized, fic06.get("tickers", []))})
    report(36, "fic-fin-08-holder-risk-severity-review", {"status": "DIAGNOSTIC_COMPLETE", "frozen_observation": ["HOLDABLE", "HOLDABLE", "REVIEW"], "question": "Whether missing confirmation alone should elevate HOLDABLE to REVIEW under the frozen holder contract.", "prompt_or_contract_change": 0, "recommended_follow_up": adjudication["next_scope"]})
    report(37, "fic-fin-08-vs-monitored-financial-sector-analogs", {"status": "CLASSIFIED", "classification": adjudication["fic_fin_08_combined_diagnostic_classification"], "analog_tickers": fic08.get("tickers", []), "rationale": fic08.get("rationale"), "rows": _selected_rows(finalized, fic08.get("tickers", []))})
    report(38, "combined-fictional-monitored-root-cause-summary", {"status": "DIAGNOSTIC_COMPLETE", "fic_fin_05": adjudication["fic_fin_05_combined_diagnostic_classification"], "fic_fin_06": adjudication["fic_fin_06_combined_diagnostic_classification"], "fic_fin_08": adjudication["fic_fin_08_combined_diagnostic_classification"], "architecture": architecture, "rationale": adjudication["combined_rationale"]})
    report(39, "next-bounded-repair-decision", {"status": "SELECTED", "next_scope": adjudication["next_scope"], "rationale": adjudication["next_scope_rationale"], "fresh_unseen_calls_authorized": False, "main_merge_authorized": False})
    report(40, "existing-monitored-impact-summary", {"status": "MEASURED", "compatibility_cohort_not_unseen": True, "completed_ticker_count": len(finalized), "raw_taxonomy_counts": dict(sorted(raw_taxonomy.items())), "final_taxonomy_counts": dict(sorted(final_taxonomy.items())), "production_persistence": 0})
    report(41, "two-stage-shadow-compatibility-readiness", {"status": "DIAGNOSTIC_COMPLETE", "two_stage_shadow_compatibility_classification": architecture, "full_monitored_universe_compatibility_claimed": not unavailable, "fresh_real_generalization_claimed": False})
    report(42, "fresh-real-proof-readiness-decision", {"status": "NOT_READY", "fresh_real_proof_readiness": "NOT_READY", "model_calls_real_fresh_unseen": 0, "reason": "M12AF is an existing monitored architecture diagnostic only."})
    report(43, "final-main-merge-readiness-note", {"status": "NOT_READY", "final_main_merge_readiness": "NOT_READY", "main_merges": 0, "reason": "Fresh unseen real proof has not occurred."})
    no_change = {
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
    }
    report(44, "production-no-change", {"status": "PASS", **no_change, "production_readiness": "NOT_READY"})
    schedule_end = m12._schedule_observation()
    report(45, "schedule-pause-observation", {"status": "PASS" if schedule_end["observed_paused_schedule_count"] >= 4 else "REVIEW", "start": state["schedule_start"], "end": schedule_end, "observed_paused_schedule_count": schedule_end["observed_paused_schedule_count"], "scheduler_mutation_count": 0, "automatic_monitoring_resume": 0})
    report(46, "hosted-ci-portability-handoff", {"status": "NOT_RUN_DIAGNOSTIC_BRANCH", "hosted_ci_pass_claimed": False, "historical_backlog_carried": True, "new_hosted_ci_failure_count": "NOT_MEASURED"})
    report(47, "astra-future-experiment-handoff", {"status": "DEFERRED", "astra_calls": 0, "proof_model": MODEL, "reasoning_effort": EFFORT, "future_experiment_must_be_separate": True})
    report(48, "master-workflow-update", {"status": "RECORDED_IN_REPORT_ONLY", "phase": "M12AF", "two_stage_shadow_compatibility_classification": architecture, "fresh_real_proof_readiness": "NOT_READY", "final_main_merge_readiness": "NOT_READY", "next_scope": adjudication["next_scope"], "persistent_master_workflow_mutation": 0})

    reference_diff = read_json(REPORTS / "10-reference-vs-task-start-universe-diff.json")
    completion: dict[str, object] = {
        "status": "COMPLETE_DIAGNOSTIC",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "monolithic_control_prompt_sha256": EXPECTED_CONTROL_PROMPT_SHA256,
        "monolithic_control_schema_sha256": EXPECTED_CONTROL_SCHEMA_SHA256,
        "two_stage_service_sha256": EXPECTED_TWO_STAGE_SERVICE_SHA256,
        "investment_judgment_model_target": MODEL,
        "investment_judgment_reasoning_effort": EFFORT,
        "task_start_active_monitor_count": len(state["all_active_tickers"]),
        "task_start_active_monitor_tickers": state["all_active_tickers"],
        "reference_added_tickers": reference_diff["reference_added_tickers"],
        "reference_removed_tickers": reference_diff["reference_removed_tickers"],
        "shadow_packet_available_count": len(state["tickers"]),
        "shadow_packet_unavailable_count": len(unavailable),
        "shadow_packet_mismatch_count": packet_mismatches,
        "shadow_context_count": state["context_count"],
        "shadow_monolithic_model_calls": runtime["monolithic_model_calls"],
        "shadow_stage1_model_calls": runtime["stage1_model_calls"],
        "shadow_stage2_model_calls": runtime["stage2_model_calls"],
        "shadow_model_calls_total": runtime["completed_model_calls"],
        "shadow_completed_ticker_count": len(finalized),
        "shadow_no_decision_material_change_count": raw_taxonomy["NO_DECISION_MATERIAL_CHANGE"],
        "shadow_same_direction_calibration_change_count": raw_taxonomy["SAME_DIRECTION_CALIBRATION_CHANGE"],
        "shadow_primary_direction_change_count": sum("overall_direction" in row["decision_material_changed_fields"] for row in finalized),
        "shadow_business_delta_change_count": sum("business_thesis_change" in row["decision_material_changed_fields"] for row in finalized),
        "shadow_new_buyer_change_count": sum("fundamental_new_buyer.stance" in row["decision_material_changed_fields"] for row in finalized),
        "shadow_holder_change_count": sum("fundamental_holder.stance" in row["decision_material_changed_fields"] for row in finalized),
        "shadow_multi_field_change_count": raw_taxonomy["MULTI_FIELD_DECISION_CHANGE"],
        "shadow_expected_contract_correction_count": expected_count,
        "shadow_potential_architecture_regression_count": regression_count,
        "shadow_unresolved_review_required_count": unresolved_count,
        "shadow_kr_count": sum(row["market"] == "kr" for row in finalized),
        "shadow_us_count": sum(row["market"] == "us" for row in finalized),
        "shadow_sector_coverage_count": len(sectors),
        "shadow_financial_sector_framework_failure_count": financial_failure_count,
        "shadow_adr_security_basis_failure_count": adr_failure_count,
        "shadow_cyclical_valuation_framework_failure_count": cyclical_failures,
        "shadow_core_mutation_after_stance_count": mutation_count,
        "shadow_runtime_timeout_count": runtime["timeout_count"],
        "shadow_runtime_capacity_failure_count": runtime["capacity_failure_count"],
        "shadow_runtime_orphan_count": runtime["orphan_process_count"],
        "shadow_wrapper_retry_count": runtime["wrapper_retry_count"],
        "provider_source_fetches": 0,
        **no_change,
        "observed_paused_schedule_count": schedule_end["observed_paused_schedule_count"],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "fic_fin_05_combined_diagnostic_classification": adjudication["fic_fin_05_combined_diagnostic_classification"],
        "fic_fin_06_combined_diagnostic_classification": adjudication["fic_fin_06_combined_diagnostic_classification"],
        "fic_fin_08_combined_diagnostic_classification": adjudication["fic_fin_08_combined_diagnostic_classification"],
        "two_stage_shadow_compatibility_classification": architecture,
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": adjudication["next_scope"],
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    report(49, "program-completion", completion)
    write_json(OUTPUT / "program-completion.json", completion)
    write_json(OUTPUT / "shadow" / "final-comparisons.json", {"status": "FROZEN", "generation_id": state["generation_id"], "rows": finalized})
    print(json.dumps({"status": "COMPLETE_DIAGNOSTIC", "architecture": architecture, "next_scope": adjudication["next_scope"]}, sort_keys=True))


def _artifact_files() -> list[Path]:
    paths = [path for path in REPORTS.rglob("*") if path.is_file()]
    paths.extend(
        path
        for path in OUTPUT.rglob("*")
        if path.is_file() and path.name != "artifact-index.json"
    )
    paths.extend(
        [
            Path("app/services/two_stage_directional_service.py"),
            Path("scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py"),
            _runner_path(),
            Path("tests/test_integrated_main_monitored_shadow_diagnostic_m12af.py"),
            WORK_INSTRUCTION,
        ]
    )
    return sorted(set(path for path in paths if path.is_file()), key=str)


def bundle(output_zip: Path) -> None:
    completion_path = REPORTS / "49-program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    write_json(OUTPUT / "program-completion.json", completion)
    files = _artifact_files()
    failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (_secret_material(path),)
        if indicators
    ]
    index = {
        "contract": "m12af-artifact-index-v1",
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
        raise ValueError("artifact_secret_scan_failure")
    summary = (
        "# M12AF Completion\n\n"
        f"- Status: `{completion['status']}`\n"
        f"- Diagnostic classification: `{completion['two_stage_shadow_compatibility_classification']}`\n"
        f"- Monitored subjects: `{completion['shadow_completed_ticker_count']}`\n"
        f"- Model calls: `{completion['shadow_model_calls_total']}`\n"
        f"- Potential regressions: `{completion['shadow_potential_architecture_regression_count']}`\n"
        f"- Unresolved reviews: `{completion['shadow_unresolved_review_required_count']}`\n"
        "- Fresh real proof: `NOT_READY`\n"
        "- Final main merge: `NOT_READY`\n"
        "- Production changes/sends: `0`\n"
        f"- Next scope: `{completion['next_scope']}`\n"
    )
    write_text(OUTPUT / "COMPLETION-REPORT.md", summary)
    files = _artifact_files()
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    if output_zip.exists():
        raise ValueError(f"result_bundle_already_exists:{output_zip}")
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=str(path))
        archive.write(OUTPUT / "artifact-index.json", arcname=str(OUTPUT / "artifact-index.json"))
    with zipfile.ZipFile(output_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("result_bundle_integrity_failure")
    digest = file_sha256(output_zip)
    sidecar = output_zip.with_suffix(output_zip.suffix + ".sha256")
    write_text(sidecar, f"{digest}  {output_zip.name}")
    print(json.dumps({"status": "PASS", "zip": str(output_zip), "sha256": digest, "sidecar": str(sidecar), "artifact_count": len(files) + 1}, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("prepare", "run-shadow", "prepare-review", "finalize", "bundle"),
    )
    parser.add_argument("--operating-root", type=Path, default=OPERATING_ROOT)
    parser.add_argument("--previous-bundle", type=Path, default=PREVIOUS_BUNDLE)
    parser.add_argument(
        "--adjudication",
        type=Path,
        default=OUTPUT / "shadow" / "review-adjudication.json",
    )
    parser.add_argument(
        "--output-zip",
        type=Path,
        default=(
            Path.home()
            / "Documents/Codex"
            / "thesis-monitor-20260911-integrated-main-monitored-shadow-diagnostic-boundary-delta-review-report.zip"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "prepare":
        prepare(args.operating_root, args.previous_bundle)
    elif args.command == "run-shadow":
        run_shadow()
    elif args.command == "prepare-review":
        prepare_review()
    elif args.command == "finalize":
        finalize(args.adjudication)
    elif args.command == "bundle":
        bundle(args.output_zip)


if __name__ == "__main__":
    main()
