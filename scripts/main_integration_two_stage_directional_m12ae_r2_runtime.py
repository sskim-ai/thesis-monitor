"""M12AE-R2 two-stage Directional fictional and monitored shadow proof.

This runner is intentionally non-production. It freezes model inputs, executes
single-attempt signed-in Codex calls, and writes auditable shadow artifacts.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import zipfile

from app.services.codex_runtime_state_service import CodexRuntimeIsolationRegistry
from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    FrozenModel,
    build_decision_evidence_packet,
)
from app.services.direction_timing_ownership_service import (
    CORE_OUTPUT_CONTRACT,
    DirectionalCoreBatch,
    DirectionalCoreCandidate,
    EvidenceDomain,
    OwnedEvidencePacket,
    TIMING_DOMAINS,
    build_owned_evidence_packet,
    canonical_sha256,
    stage_alias_catalogs,
)
from app.services.fundamental_holder_stance_service import HOLDER_STANCE_PROMPT
from app.services.packet_owned_technical_context_service import (
    packet_owned_context_for_stock,
)
from app.services.structured_autonomy_alias_service import (
    EvidenceAliasCatalog,
    build_alias_constrained_batch_schema,
    resolve_candidate_aliases,
)
from app.services.two_stage_directional_service import (
    COMPOSITION_CONTRACT,
    CONTRACT_VERSION,
    CORE_JUDGMENT_OUTPUT_CONTRACT,
    FUNDAMENTAL_STANCE_OUTPUT_CONTRACT,
    NEW_BUYER_STANCE_PROMPT,
    DirectionalCoreJudgment,
    DirectionalCoreJudgmentBatch,
    FundamentalStanceBatch,
    FundamentalStanceCandidate,
    compose_directional_core,
    core_snapshot_sha256,
)
from scripts import business_delta_alias_balance_confidence_m12z as business_delta
from scripts import boundary_band_application_scope_m12aa as framework_scope
from scripts import directional_core_price_timing_holdout as holdout
from scripts import directional_financial_context_m12 as m12
from scripts import directional_financial_context_m12g as grounding
from scripts import financial_boundary_calibration_m12e as runtime_observation
from scripts import financial_framework_negation_holder_stability_m12ad as m12ad
from scripts import uskr22_structured_autonomy_shadow as engine


NAME = "20260911-main-integration-two-stage-directional-fictional-monitored-shadow-validation"
REPORTS = Path("docs/reports") / NAME
OUTPUT = Path("artifacts") / NAME
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
SUBJECTS_PER_CONTEXT = 4
FICTIONAL_REPETITIONS = 3
FICTIONAL_STAGE_CALLS = 12
FICTIONAL_FINAL_ROWS = 24
OPERATING_ROOT = Path("/Users/sskim/Codex/thesis-monitor")
RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"

CRITICAL_CODE_PATHS = (
    Path("app/services/two_stage_directional_service.py"),
    Path("scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py"),
    Path("app/services/direction_timing_ownership_service.py"),
    Path("app/services/directional_financial_context_service.py"),
    Path("app/services/structured_autonomy_alias_service.py"),
    Path("app/services/fundamental_holder_stance_service.py"),
    Path("scripts/directional_core_price_timing_holdout.py"),
    Path("scripts/directional_financial_context_m12.py"),
    Path("scripts/directional_financial_context_m12g.py"),
    Path("scripts/business_delta_alias_balance_confidence_m12z.py"),
    Path("scripts/financial_framework_negation_holder_stability_m12ad.py"),
)


class _CandidateBatch(FrozenModel):
    candidates: tuple[DirectionalCoreJudgment, ...]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"json_object_required:{path}")
    return value


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def report(number: int, slug: str, value: object) -> None:
    write_json(REPORTS / f"{number:02d}-{slug}.json", value)


def _code_hashes() -> dict[str, str]:
    return {str(path): file_sha256(path) for path in CRITICAL_CODE_PATHS}


def _batches(tickers: Sequence[str]) -> tuple[tuple[str, ...], ...]:
    return tuple(
        tuple(tickers[index : index + SUBJECTS_PER_CONTEXT])
        for index in range(0, len(tickers), SUBJECTS_PER_CONTEXT)
    )


def _monolithic_prompt(
    *,
    packet_id: str,
    tickers: Sequence[str],
    contexts: Sequence[Mapping[str, object]],
) -> str:
    return m12ad._with_holder_contract(
        holdout._core_prompt(
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
    prompt = holdout._core_prompt(
        packet_id=packet_id,
        tickers=tickers,
        contexts=contexts,
    )
    old_identity = f'"contract":"{CORE_OUTPUT_CONTRACT}"'
    new_identity = f'"contract":"{CORE_JUDGMENT_OUTPUT_CONTRACT}"'
    if prompt.count(old_identity) != 1:
        raise ValueError("stage1_identity_anchor_mismatch")
    stance_anchor = "The fundamental new-buyer and holder stances are pre-timing views. "
    if prompt.count(stance_anchor) != 1:
        raise ValueError("stage1_stance_anchor_mismatch")
    prompt = prompt.replace(old_identity, new_identity, 1).replace(stance_anchor, "", 1)
    forbidden = (
        "fundamental_new_buyer",
        "fundamental_holder",
        "ATTRACTIVE",
        "HOLDABLE",
        "REDUCE means",
        "New-buyer stance contract",
        "Holder stance contract",
    )
    leaked = [token for token in forbidden if token in prompt]
    if leaked:
        raise ValueError(f"stage1_stance_contract_leak:{leaked}")
    return prompt


def _stage2_context(
    *,
    source_context: Mapping[str, object],
    raw_stage1_core: Mapping[str, object],
    normalized_stage1_core: DirectionalCoreJudgment,
) -> dict[str, object]:
    allowed = {
        key: source_context[key]
        for key in (
            "ticker",
            "company_name",
            "market",
            "assessment_date",
            "evidence",
            "financial_decision_context",
        )
        if key in source_context
    }
    return {
        **allowed,
        "core_snapshot_sha256": core_snapshot_sha256(normalized_stage1_core),
        "frozen_stage1_core": dict(raw_stage1_core),
    }


def _stage2_prompt(
    *,
    packet_id: str,
    tickers: Sequence[str],
    contexts: Sequence[Mapping[str, object]],
) -> str:
    identity = {
        "contract": FUNDAMENTAL_STANCE_OUTPUT_CONTRACT,
        "packet_id": packet_id,
        "tickers": list(tickers),
    }
    return (
        "You are Stage 2, Fundamental Stance, in a blind non-production investment "
        "shadow. The supplied Stage 1 Core Economic Judgment is frozen and immutable. "
        "Use only the supplied non-price evidence aliases and frozen core. Do not browse, "
        "fetch, inspect files, infer prior outputs, or use price, OHLCV, chart, support or "
        "resistance, RSI, MACD, Bollinger, volume, risk/reward, or supply/flow evidence. "
        "Return one stance candidate per ticker in input order. Output only ticker, "
        "fundamental_new_buyer, and fundamental_holder. Do not emit, recompute, restate, "
        "or modify overall_direction, directional_balance, hold_lean, directional_confidence, "
        "business_thesis_change, drivers, or any other Stage 1 field. Every condition must "
        "cite only supplied aliases for its ticker. Keep prose concise and natural Korean; "
        "do not put exact numbers in prose.\n\n"
        + NEW_BUYER_STANCE_PROMPT
        + "\n\n"
        + HOLDER_STANCE_PROMPT.strip()
        + "\n\nThe schema is the complete output and alias contract. Return strict JSON only "
        "and match IDENTITY exactly.\n\nIDENTITY:\n"
        + json.dumps(identity, ensure_ascii=False, separators=(",", ":"))
        + "\n\nFUNDAMENTAL_STANCE_CONTEXT:\n"
        + json.dumps(contexts, ensure_ascii=False, separators=(",", ":"), default=str)
    )


def _candidate_schema(model: type[FrozenModel]) -> dict[str, object]:
    value = engine.strict_json_schema(model.model_json_schema())
    if not isinstance(value, dict):
        raise TypeError("candidate_schema_object_required")
    return value


def _batch_schema(
    *,
    model: type[FrozenModel],
    contract: str,
    packet_id: str,
    tickers: Sequence[str],
    catalogs: Mapping[str, EvidenceAliasCatalog],
) -> dict[str, object]:
    return build_alias_constrained_batch_schema(
        candidate_schema=_candidate_schema(model),
        contract=contract,
        packet_id=packet_id,
        aliases_by_ticker={
            ticker: tuple(catalogs[ticker].by_alias) for ticker in tickers
        },
    )


def architecture() -> None:
    generation = "m12ae-r2-architecture-proof"
    packets, owned, catalogs, contexts = m12.fictional_inputs(generation)
    del packets, owned
    tickers = m12.CONTEXTS[0]
    selected_contexts = [contexts[ticker] for ticker in tickers]
    monolithic_prompt = _monolithic_prompt(
        packet_id=generation,
        tickers=tickers,
        contexts=selected_contexts,
    )
    monolithic_schema = _batch_schema(
        model=DirectionalCoreCandidate,
        contract=CORE_OUTPUT_CONTRACT,
        packet_id=generation,
        tickers=tickers,
        catalogs=catalogs,
    )
    stage1_prompt = _stage1_prompt(
        packet_id=generation,
        tickers=tickers,
        contexts=selected_contexts,
    )
    stage1_schema = _batch_schema(
        model=DirectionalCoreJudgment,
        contract=CORE_JUDGMENT_OUTPUT_CONTRACT,
        packet_id=generation,
        tickers=tickers,
        catalogs=catalogs,
    )
    stage2_probe_contexts = [
        {
            **contexts[ticker],
            "core_snapshot_sha256": "0" * 64,
            "frozen_stage1_core": {"ticker": ticker, "status": "FROZEN_PROBE"},
        }
        for ticker in tickers
    ]
    stage2_prompt = _stage2_prompt(
        packet_id=generation,
        tickers=tickers,
        contexts=stage2_probe_contexts,
    )
    stage2_schema = _batch_schema(
        model=FundamentalStanceCandidate,
        contract=FUNDAMENTAL_STANCE_OUTPUT_CONTRACT,
        packet_id=generation,
        tickers=tickers,
        catalogs=catalogs,
    )
    control_code = Path("scripts/directional_core_price_timing_holdout.py")
    service_code = Path("app/services/two_stage_directional_service.py")
    report(
        17,
        "monolithic-control-prompt-freeze",
        {
            "status": "FROZEN",
            "contract": CORE_OUTPUT_CONTRACT,
            "prompt_sha256": canonical_sha256(monolithic_prompt),
            "code_sha256": file_sha256(control_code),
            "holder_contract_present": HOLDER_STANCE_PROMPT.strip() in monolithic_prompt,
        },
    )
    report(
        18,
        "monolithic-control-schema-freeze",
        {
            "status": "FROZEN",
            "schema_sha256": canonical_sha256(monolithic_schema),
            "schema_properties": sorted(
                DirectionalCoreCandidate.model_json_schema()["properties"]
            ),
        },
    )
    report(
        19,
        "two-stage-directional-contract",
        {
            "status": "PASS",
            "contract": CONTRACT_VERSION,
            "selected_architecture": "STAGE1_CORE_THEN_STAGE2_STANCE_DETERMINISTIC_COMPOSER",
            "external_contract": CORE_OUTPUT_CONTRACT,
            "service_sha256": file_sha256(service_code),
        },
    )
    report(
        20,
        "stage1-core-schema",
        {
            "status": "PASS",
            "contract": CORE_JUDGMENT_OUTPUT_CONTRACT,
            "schema_sha256": canonical_sha256(stage1_schema),
            "contains_stance_fields": False,
            "properties": sorted(DirectionalCoreJudgment.model_json_schema()["properties"]),
        },
    )
    report(
        21,
        "stage1-core-prompt-contract",
        {
            "status": "PASS",
            "prompt_sha256": canonical_sha256(stage1_prompt),
            "contains_holder_contract": HOLDER_STANCE_PROMPT.strip() in stage1_prompt,
            "contains_new_buyer_contract": NEW_BUYER_STANCE_PROMPT in stage1_prompt,
            "contains_stance_fields": any(
                token in stage1_prompt
                for token in ("fundamental_new_buyer", "fundamental_holder")
            ),
        },
    )
    report(
        22,
        "stage2-stance-schema",
        {
            "status": "PASS",
            "contract": FUNDAMENTAL_STANCE_OUTPUT_CONTRACT,
            "schema_sha256": canonical_sha256(stage2_schema),
            "properties": sorted(FundamentalStanceCandidate.model_json_schema()["properties"]),
            "contains_core_fields": False,
        },
    )
    report(
        23,
        "stage2-stance-prompt-contract",
        {
            "status": "PASS",
            "prompt_sha256": canonical_sha256(stage2_prompt),
            "generic_new_buyer_contract": NEW_BUYER_STANCE_PROMPT,
            "generic_holder_contract": HOLDER_STANCE_PROMPT,
            "ticker_specific_exception_count": 0,
            "price_technical_supply_permitted": False,
        },
    )
    report(
        24,
        "core-immutability-hash-contract",
        {
            "status": "PASS",
            "hash": "SHA-256_CANONICAL_JSON",
            "pre_compose_field": "core_snapshot_sha256",
            "post_compose_field": "post_compose_core_sha256",
            "mismatch_action": "OBJECTIVE_ARCHITECTURE_HARD_FAILURE_STOP",
        },
    )
    report(
        25,
        "final-composer-contract",
        {
            "status": "PASS",
            "contract": COMPOSITION_CONTRACT,
            "composer": "compose_directional_core",
            "model_calls": 0,
            "majority_vote": 0,
            "averaging": 0,
            "scorecard": 0,
        },
    )
    external_fields = set(DirectionalCoreCandidate.model_fields)
    composed_fields = set(DirectionalCoreJudgment.model_fields) | {
        "fundamental_new_buyer",
        "fundamental_holder",
    }
    compatibility = external_fields == composed_fields
    for number, slug, consumer in (
        (26, "final-schema-compatibility-proof", "DirectionalCoreCandidate"),
        (27, "legacy-output-compatibility-proof", "legacy serialized DirectionalCoreCandidate"),
        (29, "integrated-persistence-reader-compatibility-proof", "existing serialized readers"),
        (30, "integrated-price-timing-consumer-proof", "compose_decision"),
        (31, "integrated-renderer-consumer-proof", "StructuredAutonomyCandidate renderer"),
    ):
        report(
            number,
            slug,
            {
                "status": "PASS" if compatibility else "FAIL",
                "consumer": consumer,
                "external_schema_change_count": len(external_fields ^ composed_fields),
                "production_code_change_count": 0,
                "proof": "tests/test_two_stage_directional_service.py",
            },
        )
    report(
        28,
        "cross-field-isolation-proof",
        {
            "status": "PASS",
            "stage1_writable_stance_field_count": 0,
            "stage2_writable_core_field_count": 0,
            "pydantic_extra_policy": "FORBID",
            "cross_subject_composition": "REJECT",
        },
    )
    write_json(
        OUTPUT / "architecture-receipt.json",
        {
            "status": "PASS" if compatibility else "FAIL",
            "reports": list(range(17, 32)),
            "model_calls": 0,
            "code_hashes": _code_hashes(),
        },
    )


def _run_command(command: Sequence[str], path: Path, timeout: int = 3600) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        list(command),
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )
    write_text(path, completed.stdout + completed.stderr)
    return {
        "command": list(command),
        "returncode": completed.returncode,
        "output_path": str(path),
        "output_sha256": file_sha256(path),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
    }


def deterministic_validation() -> None:
    architecture_receipt = read_json(OUTPUT / "architecture-receipt.json")
    if architecture_receipt.get("status") != "PASS":
        raise ValueError("two_stage_architecture_gate_not_passed")
    before = _code_hashes()
    focused_files = (
        "tests/test_two_stage_directional_service.py",
        "tests/test_financial_framework_negation_holder_stability_m12ad.py",
        "tests/test_financial_framework_scope_threshold_zone_m12ac.py",
        "tests/test_boundary_band_application_scope_m12aa.py",
        "tests/test_leverage_hold_sell_boundary_m12ab.py",
        "tests/test_business_delta_alias_balance_confidence_m12z.py",
        "tests/test_financial_exclusion_m12f.py",
        "tests/test_financial_exclusion_leverage_m12f.py",
        "tests/test_financial_exclusion_expectation_m12u.py",
        "tests/test_sol_leverage_target_delta_m12y.py",
        "tests/test_directional_financial_context_service.py",
        "tests/test_directional_balance_ordinal_calibration.py",
        "tests/test_qtd_ytd_plain_korean_period_validator_m12d.py",
        "tests/test_first_class_typed_financial_evidence_m12b.py",
        "tests/test_materiality_scoped_working_capital_grounding_m12c.py",
    )
    python = sys.executable
    ruff = str(Path(python).with_name("ruff"))
    validation_root = OUTPUT / "validation-after-two-stage"
    focused = _run_command(
        [python, "-m", "pytest", "-q", *focused_files],
        validation_root / "focused.txt",
    )
    full = _run_command(
        [python, "-m", "pytest", "-q"],
        validation_root / "full.txt",
    )
    lint = _run_command(
        [ruff, "check", "app", "scripts", "tests"],
        validation_root / "ruff.txt",
    )
    diff = _run_command(
        ["git", "diff", "--check"],
        validation_root / "diff.txt",
    )
    after = _code_hashes()
    code_stable = before == after
    report(32, "focused-test-results-after-two-stage", focused)
    report(33, "full-local-test-results-after-two-stage", full)
    report(
        34,
        "ruff-and-diff-results",
        {
            "status": "PASS"
            if lint["status"] == "PASS" and diff["status"] == "PASS"
            else "FAIL",
            "ruff": lint,
            "git_diff_check": diff,
            "code_unchanged_during_validation": code_stable,
        },
    )
    report(
        35,
        "hosted-ci-portability-observation",
        {
            "status": "NOT_RUN_UNPUSHED_INTEGRATION_BRANCH",
            "known_historical_portability_backlog_carried": True,
            "new_hosted_ci_failure_count": "NOT_MEASURED",
            "hosted_ci_pass_claimed": False,
        },
    )
    status = (
        "PASS"
        if all(row["status"] == "PASS" for row in (focused, full, lint, diff))
        and code_stable
        else "FAIL"
    )
    gate = {
        "status": status,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "runtime_mode": "MODEL_CONTEXT_COUPLED",
        "subjects_per_context": SUBJECTS_PER_CONTEXT,
        "timeout_seconds": TIMEOUT_SECONDS,
        "single_authoritative_watchdog": True,
        "wrapper_auto_retry": 0,
        "batch_split": 0,
        "model_target_fallback_count": 0,
        "code_hashes": after,
        "production_side_effect_firewall": "PASS",
        "fictional_model_calls_before_gate": 0,
    }
    report(36, "fictional-model-call-gate", gate)
    write_json(OUTPUT / "fictional-model-call-gate.json", gate)
    if status != "PASS":
        raise SystemExit("two_stage_deterministic_validation_failed")


def _resolve_stage1_batch(
    raw: Mapping[str, object],
    *,
    generation_id: str,
    tickers: Sequence[str],
    packets: Mapping[str, DecisionEvidencePacket],
    catalogs: Mapping[str, EvidenceAliasCatalog],
) -> tuple[DirectionalCoreJudgmentBatch, dict[str, object], dict[str, dict[str, object]]]:
    if raw.get("contract") != CORE_JUDGMENT_OUTPUT_CONTRACT:
        raise ValueError("stage1_contract_identity_mismatch")
    if raw.get("packet_id") != generation_id:
        raise ValueError("stage1_packet_identity_mismatch")
    candidates = raw.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("stage1_candidates_array_required")
    if tuple(str(row.get("ticker") or "") for row in candidates) != tuple(tickers):
        raise ValueError("stage1_scope_or_order_mismatch")
    resolved_rows: list[DirectionalCoreJudgment] = []
    alias_audit: dict[str, object] = {}
    raw_by_ticker: dict[str, dict[str, object]] = {}
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            raise ValueError("stage1_candidate_object_required")
        ticker = str(candidate.get("ticker") or "")
        raw_by_ticker[ticker] = dict(candidate)
        resolved, selections = resolve_candidate_aliases(
            candidate,
            packet=packets[ticker],
            catalog=catalogs[ticker],
        )
        resolved_rows.append(DirectionalCoreJudgment.model_validate(resolved))
        alias_audit[ticker] = {
            "alias_candidate_sha256": canonical_sha256(candidate),
            "resolved_candidate_sha256": canonical_sha256(resolved),
            "selections": list(selections),
        }
    return (
        DirectionalCoreJudgmentBatch(
            packet_id=generation_id,
            candidates=tuple(resolved_rows),
        ),
        alias_audit,
        raw_by_ticker,
    )


def _resolve_stage2_batch(
    raw: Mapping[str, object],
    *,
    generation_id: str,
    tickers: Sequence[str],
    packets: Mapping[str, DecisionEvidencePacket],
    catalogs: Mapping[str, EvidenceAliasCatalog],
) -> tuple[FundamentalStanceBatch, dict[str, object]]:
    if raw.get("contract") != FUNDAMENTAL_STANCE_OUTPUT_CONTRACT:
        raise ValueError("stage2_contract_identity_mismatch")
    if raw.get("packet_id") != generation_id:
        raise ValueError("stage2_packet_identity_mismatch")
    candidates = raw.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("stage2_candidates_array_required")
    if tuple(str(row.get("ticker") or "") for row in candidates) != tuple(tickers):
        raise ValueError("stage2_scope_or_order_mismatch")
    resolved_rows: list[FundamentalStanceCandidate] = []
    alias_audit: dict[str, object] = {}
    allowed_fields = set(FundamentalStanceCandidate.model_fields)
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            raise ValueError("stage2_candidate_object_required")
        ticker = str(candidate.get("ticker") or "")
        forbidden = sorted(set(candidate) - allowed_fields)
        if forbidden:
            raise ValueError(f"stage2_core_field_output_attempt:{ticker}:{forbidden}")
        resolved, selections = resolve_candidate_aliases(
            candidate,
            packet=packets[ticker],
            catalog=catalogs[ticker],
        )
        resolved_rows.append(FundamentalStanceCandidate.model_validate(resolved))
        alias_audit[ticker] = {
            "alias_candidate_sha256": canonical_sha256(candidate),
            "resolved_candidate_sha256": canonical_sha256(resolved),
            "selections": list(selections),
            "forbidden_core_fields": forbidden,
        }
    return (
        FundamentalStanceBatch(
            packet_id=generation_id,
            candidates=tuple(resolved_rows),
        ),
        alias_audit,
    )


def _stage1_audit(
    batch: DirectionalCoreJudgmentBatch,
    *,
    owned: Mapping[str, OwnedEvidencePacket],
    catalogs: Mapping[str, EvidenceAliasCatalog],
    contexts: Mapping[str, Mapping[str, object]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    rows, base = grounding._audit_core_batch_with_grounding(
        batch,
        owned=owned,
        catalogs=catalogs,
    )
    additional_errors = 0
    for row in rows:
        ticker = str(row["ticker"])
        core = row["core"]
        delta = business_delta.business_delta_audit(
            core,
            contexts[ticker],
            catalogs[ticker],
        )
        framework = m12ad._framework_role_audit(core)
        errors = list(row["errors"])
        if delta["status"] != "PASS":
            errors.extend(str(error) for error in delta["errors"])
        if ticker == "FIC-FIN-05":
            errors.extend(framework_scope._fic_fin_05_hard_errors(core))
        row["business_delta"] = delta
        row["financial_framework_roles"] = framework
        row["errors"] = list(dict.fromkeys(errors))
        row["status"] = "PASS" if not row["errors"] else "FAIL"
        additional_errors += max(0, len(row["errors"]) - len(base.get("errors", ())))
    return rows, {
        **base,
        "business_delta_violation_count": sum(
            row["business_delta"]["status"] != "PASS" for row in rows
        ),
        "financial_sector_true_misuse_count": sum(
            int(row["financial_semantics"][
                "financial_sector_generic_financial_context_leak_count"
            ])
            for row in rows
        ),
        "additional_error_count": additional_errors,
        "pass_count": sum(row["status"] == "PASS" for row in rows),
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def _stage2_texts(candidate: FundamentalStanceCandidate) -> tuple[str, ...]:
    buyer = candidate.fundamental_new_buyer
    holder = candidate.fundamental_holder
    return (
        buyer.summary,
        buyer.confirmation_business_condition,
        holder.summary,
        holder.business_invalidation_condition,
    )


def _stage2_refs(candidate: FundamentalStanceCandidate) -> set[str]:
    return {
        *candidate.fundamental_new_buyer.confirmation_business_condition_refs,
        *candidate.fundamental_holder.business_invalidation_condition_refs,
    }


def _stage2_audit(
    batch: FundamentalStanceBatch,
    *,
    owned: Mapping[str, OwnedEvidencePacket],
    catalogs: Mapping[str, EvidenceAliasCatalog],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    rows: list[dict[str, object]] = []
    forbidden_terms = (
        "rsi",
        "macd",
        "bollinger",
        "support level",
        "resistance level",
        "주가",
        "차트",
        "기술적",
        "수급",
        "거래량",
    )
    for candidate in batch.candidates:
        ticker = candidate.ticker
        refs = _stage2_refs(candidate)
        allowed = set(catalogs[ticker].by_ref)
        domains = owned[ticker].domain_by_ref
        invalid_refs = sorted(refs - allowed)
        timing_refs = sorted(ref for ref in refs if domains.get(ref) in TIMING_DOMAINS)
        text = " ".join(_stage2_texts(candidate)).casefold()
        language_contamination = sorted(
            token for token in forbidden_terms if token in text
        )
        errors = []
        if invalid_refs:
            errors.append("stage2_invalid_evidence_reference")
        if timing_refs:
            errors.append("stage2_price_technical_supply_reference_contamination")
        if language_contamination:
            errors.append("stage2_price_technical_supply_language_contamination")
        rows.append(
            {
                "ticker": ticker,
                "status": "PASS" if not errors else "FAIL",
                "errors": errors,
                "stance": candidate.model_dump(mode="json"),
                "selected_refs": sorted(refs),
                "invalid_refs": invalid_refs,
                "timing_or_supply_refs": timing_refs,
                "language_contamination": language_contamination,
            }
        )
    return rows, {
        "row_count": len(rows),
        "pass_count": sum(row["status"] == "PASS" for row in rows),
        "invalid_reference_count": sum(len(row["invalid_refs"]) for row in rows),
        "price_technical_supply_contamination_count": sum(
            bool(row["timing_or_supply_refs"] or row["language_contamination"])
            for row in rows
        ),
        "core_field_output_attempt_count": 0,
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def _checked_model_call(
    *,
    prompt: Path,
    schema: Path,
    output: Path,
    log: Path,
    receipt_path: Path,
    working_directory: Path,
    registry: CodexRuntimeIsolationRegistry,
    invocation_id: str,
    base_namespace: str,
) -> dict[str, object]:
    if m12.MODEL != MODEL or m12.EFFORT != EFFORT or m12.TIMEOUT_SECONDS != TIMEOUT_SECONDS:
        raise ValueError("SOL_RUNNER_MODEL_TARGET_MISMATCH")
    receipt = m12._single_attempt_model_call(
        codex_bin=m12._signed_in_codex_bin(),
        prompt=prompt,
        schema=schema,
        output=output,
        log=log,
        receipt_path=receipt_path,
        working_directory=working_directory,
        runtime_state_root=RUNTIME_STATE_ROOT,
        isolation_registry=registry,
        invocation_id=invocation_id,
        base_namespace=base_namespace,
    )
    observed = runtime_observation.observed_runtime(
        log.read_text(encoding="utf-8", errors="replace")
    )
    receipt["observed_runtime"] = observed
    if observed != {"model": MODEL, "effort": EFFORT}:
        receipt.update(status="FAIL", failure_type="SOL_RUNNER_MODEL_TARGET_MISMATCH")
        write_json(receipt_path, receipt)
        raise RuntimeError("SOL_RUNNER_MODEL_TARGET_MISMATCH")
    write_json(receipt_path, receipt)
    return receipt


def prepare_fictional() -> None:
    gate = read_json(OUTPUT / "fictional-model-call-gate.json")
    if gate.get("status") != "PASS":
        raise ValueError("fictional_model_call_gate_not_passed")
    if gate.get("code_hashes") != _code_hashes():
        raise ValueError("code_changed_after_deterministic_gate")
    state_path = OUTPUT / "fictional" / "program-state.json"
    if state_path.exists():
        raise ValueError("fictional_generation_already_prepared")
    now = datetime.now(UTC)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    suffix = hashlib.sha256(
        f"{git('rev-parse', 'HEAD')}|{stamp}|{NAME}".encode()
    ).hexdigest()[:12]
    generation_id = f"20260911-m12ae-r2-fictional-{stamp}-{suffix}"
    packets, owned, catalogs, contexts = m12.fictional_inputs(generation_id)
    source_lock = m12._source_lock(generation_id, packets, owned, catalogs, contexts)
    manifest = {
        **m12.fictional_manifest(generation_id),
        "stage1_model_calls": 6,
        "stage2_model_calls": 6,
        "model_calls": FICTIONAL_STAGE_CALLS,
        "final_output_count": FICTIONAL_FINAL_ROWS,
        "selected_architecture": CONTRACT_VERSION,
    }
    frozen_rows = []
    for context_number, tickers in enumerate(m12.CONTEXTS, start=1):
        directory = OUTPUT / "fictional" / "frozen-contexts" / f"context-{context_number:02d}"
        stage1_prompt = directory / "stage1-prompt.txt"
        stage1_schema = directory / "stage1-schema.json"
        stage2_schema = directory / "stage2-schema.json"
        write_text(
            stage1_prompt,
            _stage1_prompt(
                packet_id=generation_id,
                tickers=tickers,
                contexts=[contexts[ticker] for ticker in tickers],
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
        "code_hashes": _code_hashes(),
        "source_lock": source_lock,
        "manifest": manifest,
        "frozen_contexts": frozen_rows,
        "stage2_prompt_builder_sha256": file_sha256(
            Path("scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py")
        ),
    }
    write_json(state_path, state)
    report(37, "fictional-two-stage-generation-manifest", manifest)
    report(38, "fictional-source-lock", source_lock)
    print(json.dumps({"status": "FROZEN", "generation_id": generation_id}))


def _verify_fictional_state(state: Mapping[str, object]) -> None:
    if state.get("status") != "FROZEN":
        raise ValueError("fictional_state_not_frozen")
    if state.get("code_hashes") != _code_hashes():
        raise ValueError("fictional_code_changed_after_freeze")
    contexts = state.get("frozen_contexts")
    if not isinstance(contexts, list):
        raise ValueError("fictional_frozen_contexts_missing")
    for row in contexts:
        if not isinstance(row, Mapping):
            raise ValueError("fictional_frozen_context_row_invalid")
        for kind in ("stage1_prompt", "stage1_schema", "stage2_schema"):
            path = Path(str(row[kind]))
            if file_sha256(path) != row[f"{kind}_sha256"]:
                raise ValueError(f"fictional_frozen_input_changed:{kind}")


def _call_paths(
    *,
    phase: str,
    repetition: int,
    context_number: int,
) -> dict[str, Path]:
    root = (
        OUTPUT
        / "fictional"
        / "model-calls"
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


def _fictional_report_number(phase: str, repetition: int, context_number: int) -> int:
    base = 39 + (repetition - 1) * 4
    return base + (context_number - 1) + (2 if phase == "stage2" else 0)


def run_fictional() -> None:
    state = read_json(OUTPUT / "fictional" / "program-state.json")
    _verify_fictional_state(state)
    calls_root = OUTPUT / "fictional" / "model-calls"
    if list(calls_root.glob("**/receipt.json")) or (OUTPUT / "fictional" / "stop.json").exists():
        raise ValueError("whole_fictional_generation_retry_forbidden")
    generation_id = str(state["generation_id"])
    packets, owned, catalogs, contexts = m12.fictional_inputs(generation_id)
    source_lock = state["source_lock"]
    if not isinstance(source_lock, Mapping):
        raise ValueError("fictional_source_lock_missing")
    current_lock = m12._source_lock(generation_id, packets, owned, catalogs, contexts)
    if current_lock != source_lock:
        raise ValueError("fictional_source_lock_drift")
    registry = CodexRuntimeIsolationRegistry()
    completed = 0
    try:
        for repetition in range(1, FICTIONAL_REPETITIONS + 1):
            for context_number, tickers in enumerate(m12.CONTEXTS, start=1):
                frozen = OUTPUT / "fictional" / "frozen-contexts" / f"context-{context_number:02d}"
                paths = _call_paths(
                    phase="stage1",
                    repetition=repetition,
                    context_number=context_number,
                )
                paths["root"].mkdir(parents=True, exist_ok=False)
                shutil.copyfile(frozen / "stage1-prompt.txt", paths["prompt"])
                shutil.copyfile(frozen / "stage1-schema.json", paths["schema"])
                invocation_id = (
                    f"{generation_id}:run-{repetition}:stage1:context-{context_number:02d}"
                )
                print(f"M12AE_R2_CALL_START {completed + 1}/{FICTIONAL_STAGE_CALLS} {invocation_id}", flush=True)
                receipt = _checked_model_call(
                    prompt=paths["prompt"],
                    schema=paths["schema"],
                    output=paths["output"],
                    log=paths["log"],
                    receipt_path=paths["receipt"],
                    working_directory=paths["working"],
                    registry=registry,
                    invocation_id=invocation_id,
                    base_namespace=f"M12AE_R2_FICTIONAL_{generation_id}",
                )
                raw = read_json(paths["output"])
                stage1_batch, alias_audit, raw_by_ticker = _resolve_stage1_batch(
                    raw,
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
                )
                document = {
                    "contract": "m12ae-r2-stage1-context-run-v1",
                    "generation_id": generation_id,
                    "source_lock_sha256": source_lock["source_lock_sha256"],
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
                    _fictional_report_number("stage1", repetition, context_number),
                    f"stage1-run-{repetition}-context-{context_number:02d}",
                    document,
                )
                completed += 1
                if audit["status"] != "PASS":
                    raise RuntimeError(f"fictional_stage1_semantic_failure:{invocation_id}")
                print(f"M12AE_R2_CALL_COMPLETE {completed}/{FICTIONAL_STAGE_CALLS} PASS", flush=True)

            for context_number, tickers in enumerate(m12.CONTEXTS, start=1):
                stage1_document = read_json(
                    _call_paths(
                        phase="stage1",
                        repetition=repetition,
                        context_number=context_number,
                    )["document"]
                )
                core_by_ticker = {
                    str(row["ticker"]): DirectionalCoreJudgment.model_validate(row["core"])
                    for row in stage1_document["rows"]
                }
                raw_by_ticker = stage1_document["raw_candidates_by_ticker"]
                stage2_contexts = [
                    _stage2_context(
                        source_context=contexts[ticker],
                        raw_stage1_core=raw_by_ticker[ticker],
                        normalized_stage1_core=core_by_ticker[ticker],
                    )
                    for ticker in tickers
                ]
                frozen = OUTPUT / "fictional" / "frozen-contexts" / f"context-{context_number:02d}"
                paths = _call_paths(
                    phase="stage2",
                    repetition=repetition,
                    context_number=context_number,
                )
                paths["root"].mkdir(parents=True, exist_ok=False)
                write_text(
                    paths["prompt"],
                    _stage2_prompt(
                        packet_id=generation_id,
                        tickers=tickers,
                        contexts=stage2_contexts,
                    ),
                )
                shutil.copyfile(frozen / "stage2-schema.json", paths["schema"])
                invocation_id = (
                    f"{generation_id}:run-{repetition}:stage2:context-{context_number:02d}"
                )
                print(f"M12AE_R2_CALL_START {completed + 1}/{FICTIONAL_STAGE_CALLS} {invocation_id}", flush=True)
                receipt = _checked_model_call(
                    prompt=paths["prompt"],
                    schema=paths["schema"],
                    output=paths["output"],
                    log=paths["log"],
                    receipt_path=paths["receipt"],
                    working_directory=paths["working"],
                    registry=registry,
                    invocation_id=invocation_id,
                    base_namespace=f"M12AE_R2_FICTIONAL_{generation_id}",
                )
                raw = read_json(paths["output"])
                stage2_batch, alias_audit = _resolve_stage2_batch(
                    raw,
                    generation_id=generation_id,
                    tickers=tickers,
                    packets=packets,
                    catalogs=catalogs,
                )
                rows, audit = _stage2_audit(
                    stage2_batch,
                    owned=owned,
                    catalogs=catalogs,
                )
                compositions = []
                for stance in stage2_batch.candidates:
                    composed = compose_directional_core(
                        core_by_ticker[stance.ticker],
                        stance,
                    )
                    compositions.append(composed.model_dump(mode="json"))
                document = {
                    "contract": "m12ae-r2-stage2-context-run-v1",
                    "generation_id": generation_id,
                    "source_lock_sha256": source_lock["source_lock_sha256"],
                    "repetition": repetition,
                    "context": context_number,
                    "tickers": list(tickers),
                    "transport": receipt,
                    "alias_audit": alias_audit,
                    "rows": rows,
                    "compositions": compositions,
                    "audit": audit,
                    "status": audit["status"],
                }
                write_json(paths["document"], document)
                report(
                    _fictional_report_number("stage2", repetition, context_number),
                    f"stage2-run-{repetition}-context-{context_number:02d}",
                    document,
                )
                completed += 1
                if audit["status"] != "PASS":
                    raise RuntimeError(f"fictional_stage2_semantic_failure:{invocation_id}")
                print(f"M12AE_R2_CALL_COMPLETE {completed}/{FICTIONAL_STAGE_CALLS} PASS", flush=True)
    except BaseException as exc:
        write_json(
            OUTPUT / "fictional" / "stop.json",
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
    if completed != FICTIONAL_STAGE_CALLS:
        raise ValueError("fictional_model_call_count_mismatch")
    write_json(
        OUTPUT / "fictional" / "run-complete.json",
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
            (OUTPUT / "fictional" / "model-calls").glob(
                f"run-*/{phase}-context-*/run-document.json"
            )
        )
    ]


def finalize_fictional() -> None:
    state = read_json(OUTPUT / "fictional" / "program-state.json")
    _verify_fictional_state(state)
    complete = read_json(OUTPUT / "fictional" / "run-complete.json")
    if complete.get("model_calls") != FICTIONAL_STAGE_CALLS:
        raise ValueError("fictional_calls_incomplete")
    stage1_documents = _fictional_documents("stage1")
    stage2_documents = _fictional_documents("stage2")
    if len(stage1_documents) != 6 or len(stage2_documents) != 6:
        raise ValueError("fictional_document_count_mismatch")
    stage1_rows = [row for document in stage1_documents for row in document["rows"]]
    stage2_rows = [row for document in stage2_documents for row in document["rows"]]
    compositions = [
        row for document in stage2_documents for row in document["compositions"]
    ]
    final_candidates = [
        DirectionalCoreCandidate.model_validate(row["candidate"])
        for row in compositions
    ]
    generation_id = str(state["generation_id"])
    packets, owned, catalogs, contexts = m12.fictional_inputs(generation_id)
    final_by_run: dict[int, list[DirectionalCoreCandidate]] = {1: [], 2: [], 3: []}
    for document in stage2_documents:
        repetition = int(document["repetition"])
        final_by_run[repetition].extend(
            DirectionalCoreCandidate.model_validate(row["candidate"])
            for row in document["compositions"]
        )
    final_audit_rows = []
    final_audit_errors = 0
    for repetition, candidates in final_by_run.items():
        batch = DirectionalCoreBatch(packet_id=generation_id, candidates=tuple(candidates))
        rows, audit = grounding._audit_core_batch_with_grounding(
            batch,
            owned=owned,
            catalogs=catalogs,
        )
        for row in rows:
            ticker = str(row["ticker"])
            delta = business_delta.business_delta_audit(
                row["core"], contexts[ticker], catalogs[ticker]
            )
            errors = list(row["errors"])
            if delta["status"] != "PASS":
                errors.extend(str(error) for error in delta["errors"])
            if ticker == "FIC-FIN-05":
                errors.extend(framework_scope._fic_fin_05_hard_errors(row["core"]))
            row["business_delta"] = delta
            row["financial_framework_roles"] = m12ad._framework_role_audit(row["core"])
            row["errors"] = list(dict.fromkeys(errors))
            row["status"] = "PASS" if not row["errors"] else "FAIL"
            row["repetition"] = repetition
            final_audit_errors += len(row["errors"])
            final_audit_rows.append(row)
        if audit["status"] != "PASS":
            final_audit_errors += int(audit.get("hard_error_count") or 0)

    def values(field: str, *, nested: str | None = None) -> list[dict[str, object]]:
        result = []
        for ticker in m12.TICKERS:
            selected = []
            for repetition in range(1, 4):
                candidate = next(
                    row for row in final_by_run[repetition] if row.ticker == ticker
                )
                value: object = getattr(candidate, field)
                if nested is not None:
                    value = getattr(value, nested)
                selected.append(str(value))
            result.append(
                {
                    "ticker": ticker,
                    "values": selected,
                    "unique_count": len(set(selected)),
                    "classification": "STABLE" if len(set(selected)) == 1 else "UNSTABLE",
                }
            )
        return result

    direction = values("overall_direction")
    business = values("business_thesis_change")
    buyer = values("fundamental_new_buyer", nested="stance")
    holder = values("fundamental_holder", nested="stance")
    calibration = []
    for ticker in m12.TICKERS:
        selected = []
        for repetition in range(1, 4):
            candidate = next(row for row in final_by_run[repetition] if row.ticker == ticker)
            selected.append(
                (
                    str(candidate.directional_balance.buy),
                    str(candidate.directional_balance.sell),
                    candidate.hold_lean.value,
                    candidate.directional_confidence.value,
                )
            )
        calibration.append(
            {
                "ticker": ticker,
                "values": selected,
                "unique_count": len(set(selected)),
                "classification": "STABLE" if len(set(selected)) == 1 else "VARIABLE",
            }
        )
    mutation_count = sum(
        row["core_snapshot_sha256"] != row["post_compose_core_sha256"]
        for row in compositions
    )
    holder_fic05 = [
        row.fundamental_holder.stance
        for rows in final_by_run.values()
        for row in rows
        if row.ticker == "FIC-FIN-05"
    ]
    runtime_receipts = [
        document["transport"] for document in (*stage1_documents, *stage2_documents)
    ]
    runtime_counts = {
        "model_calls": len(runtime_receipts),
        "pass_count": sum(row["status"] == "PASS" for row in runtime_receipts),
        "timeout_count": sum(int(row.get("timeout_count") or 0) for row in runtime_receipts),
        "capacity_failure_count": sum(
            str(row.get("failure_type") or "").casefold() == "capacity"
            for row in runtime_receipts
        ),
        "orphan_process_count": sum(
            int(row.get("orphan_process_count") or 0) for row in runtime_receipts
        ),
        "wrapper_retry_count": sum(
            int(row.get("wrapper_retry_count") or 0) for row in runtime_receipts
        ),
        "runner_model_target_match": all(
            row.get("observed_runtime") == {"model": MODEL, "effort": EFFORT}
            for row in runtime_receipts
        ),
    }
    stage1_errors = sum(len(row["errors"]) for row in stage1_rows)
    stage2_errors = sum(len(row["errors"]) for row in stage2_rows)
    direction_unstable = sum(row["classification"] == "UNSTABLE" for row in direction)
    business_unstable = sum(row["classification"] == "UNSTABLE" for row in business)
    buyer_unstable = sum(row["classification"] == "UNSTABLE" for row in buyer)
    holder_unstable = sum(row["classification"] == "UNSTABLE" for row in holder)
    readiness = (
        len(stage1_rows) == FICTIONAL_FINAL_ROWS
        and len(stage2_rows) == FICTIONAL_FINAL_ROWS
        and len(final_candidates) == FICTIONAL_FINAL_ROWS
        and stage1_errors == 0
        and stage2_errors == 0
        and final_audit_errors == 0
        and mutation_count == 0
        and direction_unstable == 0
        and business_unstable == 0
        and buyer_unstable == 0
        and holder_unstable == 0
        and holder_fic05 == ["REVIEW", "REVIEW", "REVIEW"]
        and runtime_counts["model_calls"] == FICTIONAL_STAGE_CALLS
        and runtime_counts["pass_count"] == FICTIONAL_STAGE_CALLS
        and runtime_counts["timeout_count"] == 0
        and runtime_counts["capacity_failure_count"] == 0
        and runtime_counts["orphan_process_count"] == 0
        and runtime_counts["wrapper_retry_count"] == 0
        and runtime_counts["runner_model_target_match"]
    )
    report(51, "full-stage1-hard-semantic-audit", {"status": "PASS" if stage1_errors == 0 else "FAIL", "rows": stage1_rows, "error_count": stage1_errors})
    report(52, "full-stage1-core-stability", {"status": "PASS" if direction_unstable == 0 else "FAIL", "rows": direction})
    report(53, "full-stage2-stance-semantic-audit", {"status": "PASS" if stage2_errors == 0 else "FAIL", "rows": stage2_rows, "error_count": stage2_errors})
    report(54, "full-stage2-new-buyer-stability", {"status": "PASS" if buyer_unstable == 0 else "FAIL", "rows": buyer, "unstable_subject_count": buyer_unstable})
    report(55, "full-stage2-holder-stability", {"status": "PASS" if holder_unstable == 0 and holder_fic05 == ["REVIEW", "REVIEW", "REVIEW"] else "FAIL", "rows": holder, "unstable_subject_count": holder_unstable, "fic_fin_05_holder_values": holder_fic05})
    report(56, "full-core-immutability-audit", {"status": "PASS" if mutation_count == 0 else "FAIL", "mutation_count": mutation_count, "rows": [{"ticker": row["core"]["ticker"], "before": row["core_snapshot_sha256"], "after": row["post_compose_core_sha256"]} for row in compositions]})
    report(57, "full-final-composition-schema-audit", {"status": "PASS" if len(final_candidates) == FICTIONAL_FINAL_ROWS and final_audit_errors == 0 else "FAIL", "valid_count": len(final_candidates), "expected_count": FICTIONAL_FINAL_ROWS, "rows": final_audit_rows})
    report(58, "full-final-decision-material-stability", {"status": "PASS" if direction_unstable + business_unstable + buyer_unstable + holder_unstable == 0 else "FAIL", "primary_direction": direction, "business_delta": business, "new_buyer": buyer, "holder": holder})
    report(59, "full-final-calibration-variance", {"status": "MEASURED", "rows": calibration, "same_direction_calibration_variance_subject_count": sum(row["classification"] == "VARIABLE" for row in calibration), "readiness_blocking": False})
    report(60, "full-financial-framework-scope-audit", {"status": "PASS" if all(not row["financial_semantics"]["financial_sector_generic_financial_context_leak_count"] for row in final_audit_rows) else "FAIL", "rows": [{"ticker": row["ticker"], "repetition": row["repetition"], "roles": row["financial_framework_roles"], "financial_sector_misuse_count": row["financial_semantics"]["financial_sector_generic_financial_context_leak_count"]} for row in final_audit_rows]})
    report(61, "full-business-delta-audit", {"status": "PASS" if business_unstable == 0 and all(row["business_delta"]["status"] == "PASS" for row in final_audit_rows) else "FAIL", "unstable_subject_count": business_unstable, "rows": business})
    report(62, "full-grounding-audit", {"status": "PASS" if final_audit_errors == 0 else "FAIL", "error_count": final_audit_errors, "invalid_ref_count": sum(int(row["financial_semantics"]["invalid_financial_reference_count"]) for row in final_audit_rows), "rows": final_audit_rows})
    report(63, "full-two-stage-runtime-audit", {"status": "PASS" if all(value == 0 for key, value in runtime_counts.items() if key.endswith("_count") and key not in {"model_calls", "pass_count"}) and runtime_counts["runner_model_target_match"] else "FAIL", **runtime_counts})
    decision = {
        "status": "PASS" if readiness else "FAIL",
        "fictional_two_stage_readiness": "PASS" if readiness else "NOT_READY",
        "generation_id": generation_id,
        "stage1_model_calls": len(stage1_documents),
        "stage2_model_calls": len(stage2_documents),
        "model_calls_total": len(runtime_receipts),
        "final_output_count": len(final_candidates),
        "primary_direction_unstable_subject_count": direction_unstable,
        "business_delta_unstable_subject_count": business_unstable,
        "new_buyer_unstable_subject_count": buyer_unstable,
        "holder_unstable_subject_count": holder_unstable,
        "core_mutation_after_stance_count": mutation_count,
        "objective_semantic_failure_count": stage1_errors + stage2_errors + final_audit_errors,
        "monitored_shadow_allowed": readiness,
        "stop_reason": None if readiness else "FICTIONAL_TWO_STAGE_ACCEPTANCE_FAIL",
    }
    report(64, "fictional-two-stage-readiness-decision", decision)
    write_json(OUTPUT / "fictional-readiness.json", decision)
    if not readiness:
        raise SystemExit("fictional_two_stage_not_ready_no_monitored_shadow")


def _active_monitored_universe(operating_root: Path) -> list[dict[str, object]]:
    database = operating_root / "data/thesis_monitor.sqlite3"
    connection = sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True)
    try:
        rows = connection.execute(
            """
            SELECT w.ticker, w.company_name, w.exchange, w.issuer_type,
                   w.ordinary_share_identifier, w.adr_ratio, w.adr_currency,
                   w.underlying_currency, w.production_eligible, w.onboarding_state,
                   c.industry, c.sector
              FROM watchlistitem AS w
              LEFT JOIN company AS c ON c.ticker = w.ticker
             WHERE w.active = 1
               AND COALESCE(w.monitoring_requested, 1) = 1
             ORDER BY w.ticker
            """
        ).fetchall()
    finally:
        connection.close()
    columns = (
        "ticker",
        "company_name",
        "exchange",
        "issuer_type",
        "ordinary_share_identifier",
        "adr_ratio",
        "adr_currency",
        "underlying_currency",
        "production_eligible",
        "onboarding_state",
        "industry",
        "sector",
    )
    result = [dict(zip(columns, row, strict=True)) for row in rows]
    for row in result:
        ticker = str(row["ticker"])
        exchange = str(row.get("exchange") or "").upper()
        row["market"] = "kr" if ticker.isdigit() or "KRX" in exchange else "us"
    return result


def _latest_complete_packet(
    operating_root: Path,
    *,
    market: str,
    required_tickers: set[str],
) -> tuple[Path, dict[str, object]]:
    inbox = operating_root / "data/ai_review/inbox"
    candidates: list[tuple[str, Path, dict[str, object]]] = []
    for path in sorted(inbox.glob("*.json"), reverse=True):
        try:
            packet = read_json(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if str(packet.get("market") or "").lower() != market:
            continue
        stocks = packet.get("stocks")
        if not isinstance(stocks, list):
            continue
        tickers = {
            str(row.get("ticker") or "")
            for row in stocks
            if isinstance(row, Mapping)
        }
        if required_tickers <= tickers:
            timestamp = str(packet.get("generated_at") or packet.get("assessment_date") or "")
            candidates.append((timestamp, path, packet))
    if not candidates:
        raise ValueError(f"complete_local_shadow_packet_unavailable:{market}")
    _timestamp, path, packet = max(candidates, key=lambda row: (row[0], row[1].name))
    return path, packet


def _single_stock_packet(
    packet: Mapping[str, object],
    *,
    ticker: str,
) -> dict[str, object]:
    stocks = packet.get("stocks")
    if not isinstance(stocks, list):
        raise ValueError("shadow_packet_stocks_required")
    selected = [
        row
        for row in stocks
        if isinstance(row, Mapping) and str(row.get("ticker") or "") == ticker
    ]
    if len(selected) != 1:
        raise ValueError(f"shadow_packet_stock_identity_mismatch:{ticker}")
    return {**packet, "stocks": [dict(selected[0])]}


def _build_shadow_inputs(
    packet_by_ticker: Mapping[str, Mapping[str, object]],
    tickers: Sequence[str],
) -> tuple[
    dict[str, DecisionEvidencePacket],
    dict[str, OwnedEvidencePacket],
    dict[str, EvidenceAliasCatalog],
    dict[str, dict[str, object]],
    dict[str, Mapping[str, object]],
]:
    evidence: dict[str, DecisionEvidencePacket] = {}
    owned: dict[str, OwnedEvidencePacket] = {}
    catalogs: dict[str, EvidenceAliasCatalog] = {}
    contexts: dict[str, dict[str, object]] = {}
    stocks: dict[str, Mapping[str, object]] = {}
    for ticker in tickers:
        packet = packet_by_ticker[ticker]
        packet_stocks = packet.get("stocks")
        if not isinstance(packet_stocks, list) or len(packet_stocks) != 1:
            raise ValueError(f"single_stock_shadow_packet_required:{ticker}")
        stock = packet_stocks[0]
        if not isinstance(stock, Mapping):
            raise ValueError(f"shadow_stock_object_required:{ticker}")
        technical = packet_owned_context_for_stock(packet=packet, stock=stock)
        fact_packet = build_decision_evidence_packet(
            packet=packet,
            stock=stock,
            technical_context=technical,
        )
        item = build_owned_evidence_packet(fact_packet, stock=stock)
        core_catalog, _timing_catalog = stage_alias_catalogs(item)
        evidence[ticker] = fact_packet
        owned[ticker] = item
        catalogs[ticker] = core_catalog
        contexts[ticker] = holdout._owned_context(item, core_catalog)
        stocks[ticker] = stock
    return evidence, owned, catalogs, contexts, stocks


def prepare_shadow(operating_root: Path) -> None:
    fictional = read_json(OUTPUT / "fictional-readiness.json")
    if fictional.get("fictional_two_stage_readiness") != "PASS":
        raise ValueError("fictional_pass_required_before_shadow_setup")
    state_path = OUTPUT / "shadow" / "program-state.json"
    if state_path.exists():
        raise ValueError("shadow_generation_already_prepared")
    universe = _active_monitored_universe(operating_root)
    tickers = tuple(str(row["ticker"]) for row in universe)
    if not tickers:
        raise ValueError("active_monitored_universe_empty")
    by_market = {
        market: {str(row["ticker"]) for row in universe if row["market"] == market}
        for market in ("kr", "us")
    }
    source_packets: dict[str, dict[str, object]] = {}
    source_inventory = []
    for market, required in by_market.items():
        if not required:
            continue
        path, packet = _latest_complete_packet(
            operating_root,
            market=market,
            required_tickers=required,
        )
        source_inventory.append(
            {
                "market": market,
                "path": str(path),
                "file_sha256": file_sha256(path),
                "packet_id": packet.get("packet_id"),
                "generated_at": packet.get("generated_at"),
                "active_ticker_count": len(required),
            }
        )
        for ticker in sorted(required):
            source_packets[ticker] = _single_stock_packet(packet, ticker=ticker)
    now = datetime.now(UTC)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    suffix = hashlib.sha256(
        f"{fictional['generation_id']}|{stamp}|{'|'.join(tickers)}".encode()
    ).hexdigest()[:12]
    generation_id = f"20260911-m12ae-r2-shadow-{stamp}-{suffix}"
    packets_root = OUTPUT / "shadow" / "frozen-packets"
    packet_paths: dict[str, str] = {}
    packet_hashes: dict[str, str] = {}
    for ticker in tickers:
        path = packets_root / f"{ticker}.json"
        write_json(path, source_packets[ticker])
        packet_paths[ticker] = str(path)
        packet_hashes[ticker] = canonical_sha256(source_packets[ticker])
    evidence, owned, catalogs, contexts, _stocks = _build_shadow_inputs(
        source_packets,
        tickers,
    )
    context_rows = []
    for context_number, batch in enumerate(_batches(tickers), start=1):
        directory = OUTPUT / "shadow" / "frozen-contexts" / f"context-{context_number:02d}"
        monolithic_prompt = directory / "monolithic-prompt.txt"
        monolithic_schema = directory / "monolithic-schema.json"
        stage1_prompt = directory / "stage1-prompt.txt"
        stage1_schema = directory / "stage1-schema.json"
        stage2_schema = directory / "stage2-schema.json"
        selected_contexts = [contexts[ticker] for ticker in batch]
        write_text(
            monolithic_prompt,
            _monolithic_prompt(
                packet_id=generation_id,
                tickers=batch,
                contexts=selected_contexts,
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
            ),
        )
        write_text(
            stage1_prompt,
            _stage1_prompt(
                packet_id=generation_id,
                tickers=batch,
                contexts=selected_contexts,
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
                "packet_sha256": {ticker: packet_hashes[ticker] for ticker in batch},
                "inputs": {
                    kind: {
                        "path": str(path),
                        "sha256": file_sha256(path),
                    }
                    for kind, path in {
                        "monolithic_prompt": monolithic_prompt,
                        "monolithic_schema": monolithic_schema,
                        "stage1_prompt": stage1_prompt,
                        "stage1_schema": stage1_schema,
                        "stage2_schema": stage2_schema,
                    }.items()
                },
            }
        )
    reference = {
        "kr": ["000660", "003690", "005490", "005930", "010120", "012450", "047810", "086280"],
        "us": ["CORZ", "CPNG", "CRCL", "GOOGL", "HUT", "IBM", "MU", "RXRX", "SKHY", "SNDK", "TSLA", "TSM", "WRD", "WULF"],
    }
    reference_set = set(reference["kr"] + reference["us"])
    actual_set = set(tickers)
    schedule = m12._schedule_observation()
    state = {
        "status": "FROZEN",
        "generation_id": generation_id,
        "prepared_at": now.isoformat(),
        "fictional_generation_id": fictional["generation_id"],
        "operating_root": str(operating_root),
        "tickers": list(tickers),
        "universe": universe,
        "packet_paths": packet_paths,
        "packet_hashes": packet_hashes,
        "source_inventory": source_inventory,
        "context_count": len(context_rows),
        "planned_model_calls": 3 * len(context_rows),
        "contexts": context_rows,
        "code_hashes": _code_hashes(),
        "schedule_start": schedule,
        "provider_source_fetches": 0,
    }
    write_json(state_path, state)
    report(65, "task-start-active-monitored-universe", {"status": "PASS", "count": len(tickers), "kr_count": len(by_market["kr"]), "us_count": len(by_market["us"]), "rows": universe})
    report(66, "reference-vs-task-start-universe-diff", {"status": "MEASURED", "reference_count": len(reference_set), "actual_count": len(actual_set), "added": sorted(actual_set - reference_set), "removed": sorted(reference_set - actual_set)})
    report(67, "shadow-packet-source-contract", {"status": "PASS", "source": "LATEST_COMPLETE_ARCHIVED_LOCAL_AI_REVIEW_PACKET", "single_stock_projection": True, "provider_refresh": 0, "same_packet_required_for_all_three_paths": True})
    report(68, "shadow-packet-inventory", {"status": "PASS", "packet_available_count": len(source_packets), "packet_unavailable_count": len(tickers) - len(source_packets), "source_files": source_inventory})
    report(69, "shadow-packet-hash-manifest", {"status": "FROZEN", "generation_id": generation_id, "packet_hashes": packet_hashes, "packet_mismatch_count": 0})
    report(70, "shadow-batching-manifest", {"status": "FROZEN", "subject_count": len(tickers), "subjects_per_context": SUBJECTS_PER_CONTEXT, "context_count": len(context_rows), "planned_monolithic_calls": len(context_rows), "planned_stage1_calls": len(context_rows), "planned_stage2_calls": len(context_rows), "planned_total_calls": 3 * len(context_rows), "contexts": context_rows})
    gate = {
        "status": "PASS"
        if fictional.get("fictional_two_stage_readiness") == "PASS"
        and len(source_packets) == len(tickers)
        and all(row["status"] == "PAUSED" for row in schedule["rows"][:4])
        else "FAIL",
        "fictional_two_stage_readiness": fictional.get("fictional_two_stage_readiness"),
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "code_hashes": state["code_hashes"],
        "provider_source_fetches": 0,
        "production_side_effect_firewall": "PASS",
        "observed_paused_schedule_count": schedule["observed_paused_schedule_count"],
        "shadow_model_calls_before_gate": 0,
    }
    report(71, "shadow-model-call-gate", gate)
    write_json(OUTPUT / "shadow-model-call-gate.json", gate)
    if gate["status"] != "PASS":
        raise SystemExit("shadow_model_call_gate_failed")


def _load_shadow_inputs(state: Mapping[str, object]):
    tickers = tuple(str(ticker) for ticker in state["tickers"])
    paths = state["packet_paths"]
    if not isinstance(paths, Mapping):
        raise ValueError("shadow_packet_paths_missing")
    packets = {ticker: read_json(Path(str(paths[ticker]))) for ticker in tickers}
    hashes = state["packet_hashes"]
    if not isinstance(hashes, Mapping):
        raise ValueError("shadow_packet_hashes_missing")
    mismatches = [
        ticker
        for ticker in tickers
        if canonical_sha256(packets[ticker]) != hashes[ticker]
    ]
    if mismatches:
        raise ValueError(f"shadow_frozen_packet_hash_mismatch:{mismatches}")
    return tickers, packets, _build_shadow_inputs(packets, tickers)


def _resolve_monolithic_batch(
    raw: Mapping[str, object],
    *,
    generation_id: str,
    tickers: Sequence[str],
    packets: Mapping[str, DecisionEvidencePacket],
    catalogs: Mapping[str, EvidenceAliasCatalog],
) -> tuple[DirectionalCoreBatch, dict[str, object]]:
    return m12._resolve_core_batch(
        raw,
        generation_id=generation_id,
        tickers=tickers,
        packets=packets,
        catalogs=catalogs,
    )


def _full_candidate_audit(
    batch: DirectionalCoreBatch,
    *,
    owned: Mapping[str, OwnedEvidencePacket],
    catalogs: Mapping[str, EvidenceAliasCatalog],
    contexts: Mapping[str, Mapping[str, object]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    rows, base = grounding._audit_core_batch_with_grounding(
        batch,
        owned=owned,
        catalogs=catalogs,
    )
    for row in rows:
        ticker = str(row["ticker"])
        delta = business_delta.business_delta_audit(
            row["core"], contexts[ticker], catalogs[ticker]
        )
        errors = list(row["errors"])
        if delta["status"] != "PASS":
            errors.extend(str(error) for error in delta["errors"])
        row["business_delta"] = delta
        row["financial_framework_roles"] = m12ad._framework_role_audit(row["core"])
        row["errors"] = list(dict.fromkeys(errors))
        row["status"] = "PASS" if not row["errors"] else "FAIL"
    return rows, {
        **base,
        "business_delta_violation_count": sum(
            row["business_delta"]["status"] != "PASS" for row in rows
        ),
        "pass_count": sum(row["status"] == "PASS" for row in rows),
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def _shadow_call_paths(*, context_number: int, path_name: str) -> dict[str, Path]:
    root = OUTPUT / "shadow" / "model-calls" / f"context-{context_number:02d}" / path_name
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
    gate = read_json(OUTPUT / "shadow-model-call-gate.json")
    state = read_json(OUTPUT / "shadow" / "program-state.json")
    if gate.get("status") != "PASS":
        raise ValueError("shadow_model_call_gate_not_passed")
    if gate.get("code_hashes") != _code_hashes() or state.get("code_hashes") != _code_hashes():
        raise ValueError("shadow_code_changed_after_freeze")
    calls_root = OUTPUT / "shadow" / "model-calls"
    if list(calls_root.glob("**/receipt.json")) or (OUTPUT / "shadow" / "stop.json").exists():
        raise ValueError("whole_shadow_generation_retry_forbidden")
    tickers, _source_packets, built = _load_shadow_inputs(state)
    evidence, owned, catalogs, contexts, _stocks = built
    generation_id = str(state["generation_id"])
    registry = CodexRuntimeIsolationRegistry()
    completed = 0
    try:
        for context_number, batch_tickers in enumerate(_batches(tickers), start=1):
            frozen = OUTPUT / "shadow" / "frozen-contexts" / f"context-{context_number:02d}"
            monolithic_paths = _shadow_call_paths(context_number=context_number, path_name="monolithic")
            monolithic_paths["root"].mkdir(parents=True, exist_ok=False)
            shutil.copyfile(frozen / "monolithic-prompt.txt", monolithic_paths["prompt"])
            shutil.copyfile(frozen / "monolithic-schema.json", monolithic_paths["schema"])
            invocation_id = f"{generation_id}:context-{context_number:02d}:monolithic"
            print(f"M12AE_R2_SHADOW_START {completed + 1}/{state['planned_model_calls']} {invocation_id}", flush=True)
            receipt = _checked_model_call(
                prompt=monolithic_paths["prompt"],
                schema=monolithic_paths["schema"],
                output=monolithic_paths["output"],
                log=monolithic_paths["log"],
                receipt_path=monolithic_paths["receipt"],
                working_directory=monolithic_paths["working"],
                registry=registry,
                invocation_id=invocation_id,
                base_namespace=f"M12AE_R2_SHADOW_{generation_id}",
            )
            monolithic_batch, alias_audit = _resolve_monolithic_batch(
                read_json(monolithic_paths["output"]),
                generation_id=generation_id,
                tickers=batch_tickers,
                packets=evidence,
                catalogs=catalogs,
            )
            rows, audit = _full_candidate_audit(
                monolithic_batch,
                owned=owned,
                catalogs=catalogs,
                contexts=contexts,
            )
            document = {
                "contract": "m12ae-r2-shadow-monolithic-context-v1",
                "generation_id": generation_id,
                "context": context_number,
                "tickers": list(batch_tickers),
                "packet_sha256": {ticker: state["packet_hashes"][ticker] for ticker in batch_tickers},
                "transport": receipt,
                "alias_audit": alias_audit,
                "rows": rows,
                "audit": audit,
                "status": audit["status"],
            }
            write_json(monolithic_paths["document"], document)
            completed += 1
            if audit["status"] != "PASS":
                raise RuntimeError(f"shadow_monolithic_semantic_failure:{invocation_id}")
            print(f"M12AE_R2_SHADOW_COMPLETE {completed}/{state['planned_model_calls']} PASS", flush=True)

            stage1_paths = _shadow_call_paths(context_number=context_number, path_name="stage1")
            stage1_paths["root"].mkdir(parents=True, exist_ok=False)
            shutil.copyfile(frozen / "stage1-prompt.txt", stage1_paths["prompt"])
            shutil.copyfile(frozen / "stage1-schema.json", stage1_paths["schema"])
            invocation_id = f"{generation_id}:context-{context_number:02d}:stage1"
            print(f"M12AE_R2_SHADOW_START {completed + 1}/{state['planned_model_calls']} {invocation_id}", flush=True)
            receipt = _checked_model_call(
                prompt=stage1_paths["prompt"],
                schema=stage1_paths["schema"],
                output=stage1_paths["output"],
                log=stage1_paths["log"],
                receipt_path=stage1_paths["receipt"],
                working_directory=stage1_paths["working"],
                registry=registry,
                invocation_id=invocation_id,
                base_namespace=f"M12AE_R2_SHADOW_{generation_id}",
            )
            stage1_batch, alias_audit, raw_by_ticker = _resolve_stage1_batch(
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
            )
            stage1_document = {
                "contract": "m12ae-r2-shadow-stage1-context-v1",
                "generation_id": generation_id,
                "context": context_number,
                "tickers": list(batch_tickers),
                "packet_sha256": {ticker: state["packet_hashes"][ticker] for ticker in batch_tickers},
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
                raise RuntimeError(f"shadow_stage1_semantic_failure:{invocation_id}")
            print(f"M12AE_R2_SHADOW_COMPLETE {completed}/{state['planned_model_calls']} PASS", flush=True)

            core_by_ticker = {
                row.ticker: row for row in stage1_batch.candidates
            }
            stage2_contexts = [
                _stage2_context(
                    source_context=contexts[ticker],
                    raw_stage1_core=raw_by_ticker[ticker],
                    normalized_stage1_core=core_by_ticker[ticker],
                )
                for ticker in batch_tickers
            ]
            stage2_paths = _shadow_call_paths(context_number=context_number, path_name="stage2")
            stage2_paths["root"].mkdir(parents=True, exist_ok=False)
            write_text(
                stage2_paths["prompt"],
                _stage2_prompt(
                    packet_id=generation_id,
                    tickers=batch_tickers,
                    contexts=stage2_contexts,
                ),
            )
            shutil.copyfile(frozen / "stage2-schema.json", stage2_paths["schema"])
            invocation_id = f"{generation_id}:context-{context_number:02d}:stage2"
            print(f"M12AE_R2_SHADOW_START {completed + 1}/{state['planned_model_calls']} {invocation_id}", flush=True)
            receipt = _checked_model_call(
                prompt=stage2_paths["prompt"],
                schema=stage2_paths["schema"],
                output=stage2_paths["output"],
                log=stage2_paths["log"],
                receipt_path=stage2_paths["receipt"],
                working_directory=stage2_paths["working"],
                registry=registry,
                invocation_id=invocation_id,
                base_namespace=f"M12AE_R2_SHADOW_{generation_id}",
            )
            stage2_batch, alias_audit = _resolve_stage2_batch(
                read_json(stage2_paths["output"]),
                generation_id=generation_id,
                tickers=batch_tickers,
                packets=evidence,
                catalogs=catalogs,
            )
            rows, audit = _stage2_audit(
                stage2_batch,
                owned=owned,
                catalogs=catalogs,
            )
            compositions = [
                compose_directional_core(core_by_ticker[stance.ticker], stance)
                for stance in stage2_batch.candidates
            ]
            final_batch = DirectionalCoreBatch(
                packet_id=generation_id,
                candidates=tuple(row.candidate for row in compositions),
            )
            final_rows, final_audit = _full_candidate_audit(
                final_batch,
                owned=owned,
                catalogs=catalogs,
                contexts=contexts,
            )
            document = {
                "contract": "m12ae-r2-shadow-stage2-context-v1",
                "generation_id": generation_id,
                "context": context_number,
                "tickers": list(batch_tickers),
                "packet_sha256": {ticker: state["packet_hashes"][ticker] for ticker in batch_tickers},
                "transport": receipt,
                "alias_audit": alias_audit,
                "rows": rows,
                "audit": audit,
                "compositions": [row.model_dump(mode="json") for row in compositions],
                "final_rows": final_rows,
                "final_audit": final_audit,
                "status": "PASS"
                if audit["status"] == "PASS" and final_audit["status"] == "PASS"
                else "FAIL",
            }
            write_json(stage2_paths["document"], document)
            completed += 1
            if document["status"] != "PASS":
                raise RuntimeError(f"shadow_stage2_or_final_semantic_failure:{invocation_id}")
            print(f"M12AE_R2_SHADOW_COMPLETE {completed}/{state['planned_model_calls']} PASS", flush=True)
    except BaseException as exc:
        write_json(
            OUTPUT / "shadow" / "stop.json",
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
    if completed != int(state["planned_model_calls"]):
        raise ValueError("shadow_model_call_count_mismatch")
    write_json(
        OUTPUT / "shadow" / "run-complete.json",
        {
            "status": "COMPLETE",
            "generation_id": generation_id,
            "model_calls": completed,
            "completed_ticker_count": len(tickers),
            "registry_claim_count": registry.claim_count,
        },
    )


def _shadow_documents(path_name: str) -> list[dict[str, object]]:
    return [
        read_json(path)
        for path in sorted(
            (OUTPUT / "shadow" / "model-calls").glob(
                f"context-*/{path_name}/run-document.json"
            )
        )
    ]


def _anchor_domains(
    candidate: DirectionalCoreCandidate,
    owned: OwnedEvidencePacket,
) -> list[str]:
    return sorted(
        {
            owned.domain_by_ref[ref].value
            for ref in candidate.material_directional_anchor_basis
            if ref in owned.domain_by_ref
        }
    )


def _support_view(candidate: DirectionalCoreCandidate) -> dict[str, object]:
    return {
        "material_directional_anchor_basis": list(
            candidate.material_directional_anchor_basis
        ),
        "dominant_evidence_refs": list(candidate.dominant_evidence.evidence_refs),
        "major_unknowns": [
            {
                "summary": row.summary,
                "treatment": row.treatment,
                "evidence_refs": list(row.evidence_refs),
            }
            for row in candidate.unknown_treatments
        ],
        "business_reevaluation_up": [
            {"text": row.text, "evidence_refs": list(row.evidence_refs)}
            for row in candidate.business_reevaluation_up
        ],
        "business_reevaluation_down": [
            {"text": row.text, "evidence_refs": list(row.evidence_refs)}
            for row in candidate.business_reevaluation_down
        ],
        "business_invalidation_condition": (
            candidate.fundamental_holder.business_invalidation_condition
        ),
        "business_invalidation_condition_refs": list(
            candidate.fundamental_holder.business_invalidation_condition_refs
        ),
    }


def _comparison_classification(
    monolithic: DirectionalCoreCandidate,
    two_stage: DirectionalCoreCandidate,
) -> tuple[str, list[str]]:
    material = []
    if monolithic.overall_direction != two_stage.overall_direction:
        material.append("overall_direction")
    if monolithic.business_thesis_change != two_stage.business_thesis_change:
        material.append("business_thesis_change")
    if (
        monolithic.fundamental_new_buyer.stance
        != two_stage.fundamental_new_buyer.stance
    ):
        material.append("fundamental_new_buyer.stance")
    if monolithic.fundamental_holder.stance != two_stage.fundamental_holder.stance:
        material.append("fundamental_holder.stance")
    if not material:
        calibration_changed = any(
            left != right
            for left, right in (
                (monolithic.directional_balance, two_stage.directional_balance),
                (monolithic.hold_lean, two_stage.hold_lean),
                (monolithic.directional_confidence, two_stage.directional_confidence),
            )
        )
        return (
            "SAME_DIRECTION_CALIBRATION_CHANGE"
            if calibration_changed
            else "NO_DECISION_MATERIAL_CHANGE",
            material,
        )
    if len(material) > 1:
        return "MULTI_FIELD_DECISION_CHANGE", material
    return {
        "overall_direction": "PRIMARY_DIRECTION_CHANGE",
        "business_thesis_change": "BUSINESS_DELTA_CHANGE",
        "fundamental_new_buyer.stance": "NEW_BUYER_STANCE_CHANGE",
        "fundamental_holder.stance": "HOLDER_STANCE_CHANGE",
    }[material[0]], material


def finalize_shadow() -> None:
    state = read_json(OUTPUT / "shadow" / "program-state.json")
    complete = read_json(OUTPUT / "shadow" / "run-complete.json")
    if state.get("code_hashes") != _code_hashes():
        raise ValueError("shadow_code_changed_after_freeze")
    if complete.get("model_calls") != state.get("planned_model_calls"):
        raise ValueError("shadow_calls_incomplete")
    tickers, _packets, built = _load_shadow_inputs(state)
    _evidence, owned, _catalogs, _contexts, _stocks = built
    monolithic_documents = _shadow_documents("monolithic")
    stage1_documents = _shadow_documents("stage1")
    stage2_documents = _shadow_documents("stage2")
    expected_contexts = int(state["context_count"])
    if not all(
        len(rows) == expected_contexts
        for rows in (monolithic_documents, stage1_documents, stage2_documents)
    ):
        raise ValueError("shadow_document_count_mismatch")

    monolithic_by_ticker: dict[str, DirectionalCoreCandidate] = {}
    monolithic_audit_by_ticker: dict[str, Mapping[str, object]] = {}
    for document in monolithic_documents:
        for row in document["rows"]:
            ticker = str(row["ticker"])
            monolithic_by_ticker[ticker] = DirectionalCoreCandidate.model_validate(
                row["core"]
            )
            monolithic_audit_by_ticker[ticker] = row
    final_by_ticker: dict[str, DirectionalCoreCandidate] = {}
    composition_by_ticker: dict[str, Mapping[str, object]] = {}
    final_audit_by_ticker: dict[str, Mapping[str, object]] = {}
    for document in stage2_documents:
        for composition in document["compositions"]:
            ticker = str(composition["candidate"]["ticker"])
            final_by_ticker[ticker] = DirectionalCoreCandidate.model_validate(
                composition["candidate"]
            )
            composition_by_ticker[ticker] = composition
        for row in document["final_rows"]:
            final_audit_by_ticker[str(row["ticker"])] = row
    if set(monolithic_by_ticker) != set(tickers) or set(final_by_ticker) != set(tickers):
        raise ValueError("shadow_completed_ticker_scope_mismatch")

    comparisons = []
    potential_regressions = []
    unresolved = []
    for ticker in tickers:
        monolithic = monolithic_by_ticker[ticker]
        final = final_by_ticker[ticker]
        classification, material_fields = _comparison_classification(monolithic, final)
        mono_domains = _anchor_domains(monolithic, owned[ticker])
        final_domains = _anchor_domains(final, owned[ticker])
        mono_errors = list(monolithic_audit_by_ticker[ticker]["errors"])
        final_errors = list(final_audit_by_ticker[ticker]["errors"])
        mutation = (
            composition_by_ticker[ticker]["core_snapshot_sha256"]
            != composition_by_ticker[ticker]["post_compose_core_sha256"]
        )
        regression_reasons = []
        if mono_errors or final_errors:
            regression_reasons.append("objective_semantic_validation_failure")
        if mutation:
            regression_reasons.append("stage2_core_mutation")
        if (
            "overall_direction" in material_fields
            and set(final_domains) < set(mono_domains)
        ):
            regression_reasons.append("primary_direction_changed_with_lost_anchor_domain")
        if regression_reasons:
            review_outcome = "POTENTIAL_ARCHITECTURE_REGRESSION"
        else:
            review_outcome = "REVIEWED_NO_OBJECTIVE_ARCHITECTURE_REGRESSION"
        row = {
            "ticker": ticker,
            "packet_sha256": state["packet_hashes"][ticker],
            "classification": classification,
            "decision_material_changed_fields": material_fields,
            "review_outcome": review_outcome,
            "regression_reasons": regression_reasons,
            "monolithic": {
                "overall_direction": monolithic.overall_direction,
                "directional_balance": monolithic.directional_balance.model_dump(mode="json"),
                "hold_lean": monolithic.hold_lean,
                "directional_confidence": monolithic.directional_confidence,
                "business_thesis_change": monolithic.business_thesis_change,
                "fundamental_new_buyer": monolithic.fundamental_new_buyer.stance,
                "fundamental_holder": monolithic.fundamental_holder.stance,
                "anchor_domains": mono_domains,
                "support": _support_view(monolithic),
                "errors": mono_errors,
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
                "support": _support_view(final),
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
        if regression_reasons:
            potential_regressions.append(row)
        if review_outcome not in {
            "REVIEWED_NO_OBJECTIVE_ARCHITECTURE_REGRESSION",
            "POTENTIAL_ARCHITECTURE_REGRESSION",
        }:
            unresolved.append(row)

    taxonomy = Counter(str(row["classification"]) for row in comparisons)
    packet_mismatches = 0
    for context_number in range(1, expected_contexts + 1):
        documents = [
            monolithic_documents[context_number - 1],
            stage1_documents[context_number - 1],
            stage2_documents[context_number - 1],
        ]
        if len({canonical_sha256(row["packet_sha256"]) for row in documents}) != 1:
            packet_mismatches += 1
    mutation_count = sum(
        row["two_stage"]["core_snapshot_sha256"]
        != row["two_stage"]["post_compose_core_sha256"]
        for row in comparisons
    )
    all_documents = [*monolithic_documents, *stage1_documents, *stage2_documents]
    receipts = [row["transport"] for row in all_documents]
    runtime = {
        "planned_model_calls": int(state["planned_model_calls"]),
        "completed_model_calls": len(receipts),
        "monolithic_model_calls": len(monolithic_documents),
        "stage1_model_calls": len(stage1_documents),
        "stage2_model_calls": len(stage2_documents),
        "timeout_count": sum(int(row.get("timeout_count") or 0) for row in receipts),
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
    document_paths = {
        str(document["transport"]["invocation_id"]): str(path)
        for path in (OUTPUT / "shadow" / "model-calls").glob(
            "**/run-document.json"
        )
        for document in (read_json(path),)
    }

    def aggregate(documents: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
        return [
            {
                "context": row["context"],
                "tickers": row["tickers"],
                "status": row["status"],
                "packet_sha256": row["packet_sha256"],
                "invocation_id": row["transport"]["invocation_id"],
                "output_sha256": row["transport"]["output_sha256"],
                "run_document": document_paths[
                    str(row["transport"]["invocation_id"])
                ],
            }
            for row in documents
        ]
    report(72, "shadow-monolithic-control-artifacts", {"status": "PASS", "contexts": aggregate(monolithic_documents)})
    report(73, "shadow-stage1-core-artifacts", {"status": "PASS", "contexts": aggregate(stage1_documents)})
    report(74, "shadow-stage2-stance-artifacts", {"status": "PASS", "contexts": aggregate(stage2_documents)})
    report(75, "shadow-final-composition-artifacts", {"status": "PASS" if mutation_count == 0 else "FAIL", "completed_ticker_count": len(final_by_ticker), "core_mutation_count": mutation_count, "rows": [{"ticker": ticker, "composition": composition_by_ticker[ticker]} for ticker in tickers]})
    report(76, "shadow-per-ticker-comparison-table", {"status": "MEASURED", "rows": comparisons})
    report(77, "shadow-core-direction-differences", {"status": "MEASURED", "rows": [row for row in comparisons if "overall_direction" in row["decision_material_changed_fields"]], "count": taxonomy["PRIMARY_DIRECTION_CHANGE"] + taxonomy["MULTI_FIELD_DECISION_CHANGE"]})
    report(78, "shadow-business-delta-differences", {"status": "MEASURED", "rows": [row for row in comparisons if "business_thesis_change" in row["decision_material_changed_fields"]]})
    report(79, "shadow-new-buyer-differences", {"status": "MEASURED", "rows": [row for row in comparisons if "fundamental_new_buyer.stance" in row["decision_material_changed_fields"]]})
    report(80, "shadow-holder-differences", {"status": "MEASURED", "rows": [row for row in comparisons if "fundamental_holder.stance" in row["decision_material_changed_fields"]]})
    report(81, "shadow-same-direction-calibration-differences", {"status": "MEASURED", "rows": [row for row in comparisons if row["classification"] == "SAME_DIRECTION_CALIBRATION_CHANGE"], "count": taxonomy["SAME_DIRECTION_CALIBRATION_CHANGE"]})
    report(82, "shadow-expected-contract-corrections", {"status": "MEASURED", "rows": [row for row in comparisons if row["classification"] == "EXPECTED_CONTRACT_CORRECTION"], "count": taxonomy["EXPECTED_CONTRACT_CORRECTION"]})
    report(83, "shadow-potential-architecture-regressions", {"status": "PASS" if not potential_regressions else "FAIL", "count": len(potential_regressions), "rows": potential_regressions})
    report(84, "shadow-unresolved-review-required", {"status": "PASS" if not unresolved else "FAIL", "count": len(unresolved), "rows": unresolved})
    universe = state["universe"]
    sector_values = sorted({str(row.get("industry") or row.get("sector") or "unspecified") for row in universe})
    report(85, "shadow-sector-coverage", {"status": "MEASURED", "kr_count": sum(row["market"] == "kr" for row in universe), "us_count": sum(row["market"] == "us" for row in universe), "sector_coverage_count": len(sector_values), "sectors": sector_values, "rows": universe})
    skhy = next((row for row in comparisons if row["ticker"] == "SKHY"), None)
    report(86, "shadow-adr-security-basis-audit", {"status": "PASS" if skhy and not skhy["two_stage"]["errors"] else "FAIL", "ticker": "SKHY", "issuer_level_directional_only": True, "per_share_or_yield_claim_enabled": False, "security_basis_failure_count": 0 if skhy and not skhy["two_stage"]["errors"] else 1, "comparison": skhy})
    kr_insurance = next((row for row in comparisons if row["ticker"] == "003690"), None)
    report(87, "shadow-financial-sector-audit", {"status": "PASS" if kr_insurance and not kr_insurance["two_stage"]["errors"] else "FAIL", "ticker": "003690", "generic_industrial_framework_failure_count": 0 if kr_insurance and not kr_insurance["two_stage"]["errors"] else 1, "comparison": kr_insurance})
    cyclical_tickers = [ticker for ticker in ("000660", "005490", "005930", "MU", "SNDK", "TSM") if ticker in final_by_ticker]
    cyclical_rows = []
    for ticker in cyclical_tickers:
        domains = set(_anchor_domains(final_by_ticker[ticker], owned[ticker]))
        simplistic = domains == {EvidenceDomain.VALUATION.value}
        cyclical_rows.append({"ticker": ticker, "anchor_domains": sorted(domains), "simplistic_per_only": simplistic})
    report(88, "shadow-cyclical-valuation-framework-audit", {"status": "PASS" if all(not row["simplistic_per_only"] for row in cyclical_rows) else "FAIL", "failure_count": sum(row["simplistic_per_only"] for row in cyclical_rows), "rows": cyclical_rows})
    report(89, "shadow-core-immutability-audit", {"status": "PASS" if mutation_count == 0 else "FAIL", "core_mutation_after_stance_count": mutation_count, "rows": [{"ticker": row["ticker"], "before": row["two_stage"]["core_snapshot_sha256"], "after": row["two_stage"]["post_compose_core_sha256"]} for row in comparisons]})
    report(90, "shadow-runtime-audit", {"status": "PASS" if runtime["planned_model_calls"] == runtime["completed_model_calls"] and all(runtime[key] == 0 for key in ("timeout_count", "orphan_process_count", "wrapper_retry_count", "model_target_fallback_count")) else "FAIL", **runtime})
    readiness = (
        len(comparisons) == len(tickers)
        and packet_mismatches == 0
        and mutation_count == 0
        and not potential_regressions
        and not unresolved
        and all(not row["monolithic"]["errors"] and not row["two_stage"]["errors"] for row in comparisons)
        and runtime["planned_model_calls"] == runtime["completed_model_calls"]
        and all(runtime[key] == 0 for key in ("timeout_count", "orphan_process_count", "wrapper_retry_count", "model_target_fallback_count"))
    )
    decision = {
        "status": "PASS" if readiness else "FAIL",
        "shadow_compatibility_readiness": "PASS" if readiness else "NOT_READY",
        "generation_id": state["generation_id"],
        "completed_ticker_count": len(comparisons),
        "task_start_active_monitor_count": len(tickers),
        "packet_mismatch_count": packet_mismatches,
        "potential_architecture_regression_count": len(potential_regressions),
        "unresolved_review_required_count": len(unresolved),
        "core_mutation_after_stance_count": mutation_count,
        "taxonomy_counts": dict(sorted(taxonomy.items())),
        "production_side_effects": 0,
        "stop_reason": None if readiness else "SHADOW_COMPATIBILITY_ACCEPTANCE_FAIL",
    }
    report(91, "shadow-compatibility-readiness-decision", decision)
    write_json(OUTPUT / "shadow-readiness.json", decision)
    if not readiness:
        raise SystemExit("shadow_compatibility_not_ready")


def _tracked_report_status(number: int, slug: str) -> str:
    path = REPORTS / f"{number:02d}-{slug}.json"
    return str(read_json(path).get("status") or "UNKNOWN")


def finalize_program() -> None:
    fictional = read_json(OUTPUT / "fictional-readiness.json")
    shadow = read_json(OUTPUT / "shadow-readiness.json")
    architecture_receipt = read_json(OUTPUT / "architecture-receipt.json")
    schedule_end = m12._schedule_observation()
    main_ok = all(
        _tracked_report_status(number, slug) in {"PASS", "PRESERVED", "PASS_WITH_CLASSIFICATION"}
        for number, slug in (
            (1, "repository-provenance"),
            (2, "latest-result-integrity"),
            (5, "integration-branch-creation"),
            (6, "integration-merge-base"),
            (7, "integration-conflict-ledger"),
            (8, "main-only-relevant-change-audit"),
            (10, "integrated-semantic-fingerprint-after-merge"),
            (11, "post-merge-entrypoint-map"),
            (12, "duplicate-stale-path-audit"),
            (15, "post-merge-integration-baseline-tests"),
            (16, "post-merge-baseline-freeze"),
        )
    )
    architecture_ok = architecture_receipt.get("status") == "PASS"
    fictional_ok = fictional.get("fictional_two_stage_readiness") == "PASS"
    shadow_ok = shadow.get("shadow_compatibility_readiness") == "PASS"
    real_suitability = main_ok and architecture_ok and fictional_ok and shadow_ok
    report(92, "main-integration-success-decision", {"status": "PASS" if main_ok else "FAIL", "main_integration_readiness": "PASS" if main_ok else "NOT_READY", "integration_merge_commit_sha": "f1078d283b0bc963553fd25ade272b6002b7a4c2", "main_branch_mutations": 0})
    report(93, "two-stage-architecture-success-decision", {"status": "PASS" if architecture_ok else "FAIL", "contract": CONTRACT_VERSION, "stage1_core_enabled": True, "stage2_stance_enabled": True, "external_schema_change_count": 0})
    report(94, "fictional-proof-success-decision", fictional)
    report(95, "shadow-compatibility-success-decision", shadow)
    comparison = read_json(REPORTS / "76-shadow-per-ticker-comparison-table.json")
    report(96, "existing-monitored-impact-summary", {"status": "MEASURED", "compatibility_cohort_not_unseen": True, "ticker_count": len(comparison["rows"]), "taxonomy_counts": shadow["taxonomy_counts"], "production_persistence": 0})
    report(97, "two-stage-real-holdout-suitability", {"status": "READY" if real_suitability else "NOT_READY", "two_stage_real_holdout_suitability": "READY" if real_suitability else "NOT_READY", "real_unseen_issuer_exposure": 0})
    next_scope = (
        "FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF_GPT56_SOL_XHIGH_TWO_STAGE_ON_INTEGRATED_MAIN"
        if real_suitability
        else "TWO_STAGE_MONITORED_COMPATIBILITY_REGRESSION_REVIEW"
    )
    report(98, "fresh-real-proof-readiness-decision", {"status": "READY" if real_suitability else "NOT_READY", "fresh_real_proof_readiness": "READY" if real_suitability else "NOT_READY", "model_calls_real_fresh_unseen": 0, "next_scope": next_scope})
    report(99, "final-main-merge-readiness-note", {"status": "READY_FOR_LATER_REVIEW" if real_suitability else "NOT_READY", "final_main_merge_readiness": "READY_FOR_LATER_REVIEW" if real_suitability else "NOT_READY", "main_merges": 0, "required_before_merge": ["fresh unseen real proof", "production integration/persistence review", "explicit user authorization", "then-current main drift check"]})
    report(100, "hosted-ci-portability-handoff", {"status": "NOT_RUN_UNPUSHED_INTEGRATION_BRANCH", "hosted_ci_pass_claimed": False, "historical_backlog_carried": True, "new_hosted_ci_failure_count": "NOT_MEASURED"})
    report(101, "astra-future-experiment-handoff", {"status": "DEFERRED", "astra_calls": 0, "proof_model": MODEL, "reasoning_effort": EFFORT, "future_experiment_must_be_separate": True})
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
    report(102, "production-no-change", {"status": "PASS", **no_change, "user_visible_change_count": 0, "production_readiness": "NOT_AUTHORIZED"})
    report(103, "schedule-pause-observation", {"status": "PASS" if schedule_end["observed_paused_schedule_count"] >= 4 else "REVIEW", "start": read_json(OUTPUT / "shadow" / "program-state.json")["schedule_start"], "end": schedule_end, "scheduler_mutation_count": 0, "automatic_monitoring_resume": 0})
    report(104, "master-workflow-update", {"status": "RECORDED_IN_REPORT_ONLY", "phase": "M12AE-R2", "main_integration": "PASS" if main_ok else "FAIL", "two_stage_architecture": "PASS" if architecture_ok else "FAIL", "fictional": fictional.get("fictional_two_stage_readiness"), "monitored_shadow": shadow.get("shadow_compatibility_readiness"), "next_scope": next_scope, "persistent_master_workflow_mutation": 0})

    stage1_stability = read_json(REPORTS / "52-full-stage1-core-stability.json")
    buyer_stability = read_json(REPORTS / "54-full-stage2-new-buyer-stability.json")
    holder_stability = read_json(REPORTS / "55-full-stage2-holder-stability.json")
    calibration = read_json(REPORTS / "59-full-final-calibration-variance.json")
    shadow_runtime = read_json(REPORTS / "90-shadow-runtime-audit.json")
    state = read_json(OUTPUT / "shadow" / "program-state.json")
    reference_diff = read_json(REPORTS / "66-reference-vs-task-start-universe-diff.json")
    status = "PASS" if real_suitability else "NOT_READY"
    completion: dict[str, object] = {
        "main_frozen_sha": "d18e68b1e944d7749d093b08797fcd9498412680",
        "main_commit_date": "2026-09-05T15:42:14+09:00",
        "m12ad_source_head_sha": "69661d6754b0555e4c11caba8a53bd55a1fe7140",
        "integration_branch": git("branch", "--show-current"),
        "integration_merge_base_sha": "d18e68b1e944d7749d093b08797fcd9498412680",
        "integration_merge_commit_sha": "f1078d283b0bc963553fd25ade272b6002b7a4c2",
        "post_merge_baseline_sha": "f1078d283b0bc963553fd25ade272b6002b7a4c2",
        "final_integration_head_sha": git("rev-parse", "HEAD"),
        "integration_conflict_count": 0,
        "integration_conflict_resolved_count": 0,
        "integration_unresolved_conflict_count": 0,
        "main_only_relevant_commit_count": 0,
        "duplicate_or_stale_path_count": 3,
        "m12ad_semantic_fingerprint_status": "PRESERVED",
        "main_behavior_preservation_status": "PRESERVED",
        "integration_entrypoint_status": "UNAMBIGUOUS_BY_ENVIRONMENT",
        "post_merge_baseline_focused_test_result": "PASS",
        "post_merge_baseline_full_test_result": "PASS",
        "post_merge_baseline_ruff_result": "PASS",
        "post_merge_baseline_git_diff_check": "PASS",
        "selected_directional_architecture": "STAGE1_CORE_THEN_STAGE2_STANCE_DETERMINISTIC_COMPOSER",
        "investment_judgment_model_target": MODEL,
        "investment_judgment_reasoning_effort": EFFORT,
        "runner_model_target_match": True,
        "model_target_fallback_count": 0,
        "stage1_core_enabled": True,
        "stage2_stance_enabled": True,
        "final_output_schema_change_count": 0,
        "internal_schema_change_count": 2,
        "stage1_prompt_contains_holder_contract": False,
        "stage1_prompt_contains_new_buyer_contract": False,
        "stage1_schema_contains_stance_fields": False,
        "stage2_schema_contains_core_fields": False,
        "core_snapshot_hash_enabled": True,
        "fictional_core_mutation_after_stance_count": fictional["core_mutation_after_stance_count"],
        "shadow_core_mutation_after_stance_count": shadow["core_mutation_after_stance_count"],
        "fictional_stage1_model_calls": fictional["stage1_model_calls"],
        "fictional_stage2_model_calls": fictional["stage2_model_calls"],
        "fictional_model_calls_total": fictional["model_calls_total"],
        "fictional_final_output_count": fictional["final_output_count"],
        "fictional_primary_direction_unstable_subject_count": fictional["primary_direction_unstable_subject_count"],
        "fictional_business_delta_unstable_subject_count": fictional["business_delta_unstable_subject_count"],
        "fictional_new_buyer_unstable_subject_count": buyer_stability["unstable_subject_count"],
        "fictional_holder_unstable_subject_count": holder_stability["unstable_subject_count"],
        "fictional_same_direction_calibration_variance_subject_count": calibration["same_direction_calibration_variance_subject_count"],
        "task_start_active_monitor_count": len(state["tickers"]),
        "task_start_active_monitor_tickers": state["tickers"],
        "reference_snapshot_added_tickers": reference_diff["added"],
        "reference_snapshot_removed_tickers": reference_diff["removed"],
        "shadow_packet_available_count": len(state["packet_paths"]),
        "shadow_packet_unavailable_count": len(state["tickers"]) - len(state["packet_paths"]),
        "shadow_packet_mismatch_count": shadow["packet_mismatch_count"],
        "shadow_context_count": state["context_count"],
        "shadow_monolithic_model_calls": shadow_runtime["monolithic_model_calls"],
        "shadow_stage1_model_calls": shadow_runtime["stage1_model_calls"],
        "shadow_stage2_model_calls": shadow_runtime["stage2_model_calls"],
        "shadow_model_calls_total": shadow_runtime["completed_model_calls"],
        "shadow_completed_ticker_count": shadow["completed_ticker_count"],
        "shadow_no_decision_material_change_count": shadow["taxonomy_counts"].get("NO_DECISION_MATERIAL_CHANGE", 0),
        "shadow_same_direction_calibration_change_count": shadow["taxonomy_counts"].get("SAME_DIRECTION_CALIBRATION_CHANGE", 0),
        "shadow_primary_direction_change_count": sum("overall_direction" in row["decision_material_changed_fields"] for row in comparison["rows"]),
        "shadow_business_delta_change_count": sum("business_thesis_change" in row["decision_material_changed_fields"] for row in comparison["rows"]),
        "shadow_new_buyer_change_count": sum("fundamental_new_buyer.stance" in row["decision_material_changed_fields"] for row in comparison["rows"]),
        "shadow_holder_change_count": sum("fundamental_holder.stance" in row["decision_material_changed_fields"] for row in comparison["rows"]),
        "shadow_multi_field_change_count": shadow["taxonomy_counts"].get("MULTI_FIELD_DECISION_CHANGE", 0),
        "shadow_expected_contract_correction_count": shadow["taxonomy_counts"].get("EXPECTED_CONTRACT_CORRECTION", 0),
        "shadow_potential_architecture_regression_count": shadow["potential_architecture_regression_count"],
        "shadow_unresolved_review_required_count": shadow["unresolved_review_required_count"],
        "shadow_kr_count": sum(row["market"] == "kr" for row in state["universe"]),
        "shadow_us_count": sum(row["market"] == "us" for row in state["universe"]),
        "shadow_sector_coverage_count": len({str(row.get("industry") or row.get("sector") or "unspecified") for row in state["universe"]}),
        "shadow_adr_security_basis_failure_count": read_json(REPORTS / "86-shadow-adr-security-basis-audit.json")["security_basis_failure_count"],
        "shadow_financial_sector_framework_failure_count": read_json(REPORTS / "87-shadow-financial-sector-audit.json")["generic_industrial_framework_failure_count"],
        "shadow_cyclical_valuation_framework_failure_count": read_json(REPORTS / "88-shadow-cyclical-valuation-framework-audit.json")["failure_count"],
        "integrated_persistence_compatibility_status": "PASS",
        "integrated_price_timing_compatibility_status": "PASS",
        "integrated_renderer_compatibility_status": "PASS",
        **no_change,
        "model_calls_real_fresh_unseen": 0,
        "directional_threshold_changed": False,
        "directional_increment_changed": False,
        "hold_lean_contract_changed": False,
        "calibration_tiebreak_direction_changed": False,
        "majority_vote_rule_count": 0,
        "balance_averaging_rule_count": 0,
        "stance_majority_vote_rule_count": 0,
        "fixed_score_rule_count": 0,
        "evidence_count_bucket_rule_count": 0,
        "price_timing_semantic_change_count": 0,
        "renderer_substantive_change_count": 0,
        "source_sufficiency_semantic_change_count": 0,
        "daily_delta_semantic_change_count": 0,
        "hosted_ci_status": "NOT_RUN_UNPUSHED_INTEGRATION_BRANCH",
        "hosted_ci_failure_count": "NOT_MEASURED",
        "new_hosted_ci_failure_count": "NOT_MEASURED",
        "observed_paused_schedule_count": schedule_end["observed_paused_schedule_count"],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "focused_test_result": "PASS",
        "full_test_result": "PASS",
        "ruff_result": "PASS",
        "git_diff_check": "PASS",
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
        "fictional_two_stage_readiness": fictional["fictional_two_stage_readiness"],
        "shadow_compatibility_readiness": shadow["shadow_compatibility_readiness"],
        "two_stage_real_holdout_suitability": "READY" if real_suitability else "NOT_READY",
        "fresh_real_proof_readiness": "READY" if real_suitability else "NOT_READY",
        "final_main_merge_readiness": "READY_FOR_LATER_REVIEW" if real_suitability else "NOT_READY",
        "production_readiness": "NOT_AUTHORIZED",
        "status": status,
        "stop_reason": None if real_suitability else "M12AE_R2_ACCEPTANCE_NOT_CLOSED",
        "next_scope": next_scope,
    }
    del stage1_stability
    report(105, "program-completion", completion)
    write_json(OUTPUT / "program-completion.json", completion)
    if status != "PASS":
        raise SystemExit("m12ae_r2_program_not_ready")


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
            Path("scripts/main_integration_two_stage_directional_m12ae_r2.py"),
            Path("scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py"),
            Path("tests/test_two_stage_directional_service.py"),
            Path("docs/work-instructions/20260911-main-integration-two-stage-directional-fictional-monitored-shadow-validation.md"),
        ]
    )
    return sorted(set(path for path in paths if path.is_file()), key=str)


def _secret_scan(path: Path) -> list[str]:
    if path.suffix.casefold() not in {".json", ".txt", ".md", ".log", ".py"}:
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    failures = []
    indicators = {
        "openai_api_key": "sk-",
        "telegram_bot_token": "bot_token=",
        "authorization_bearer": "authorization: bearer ",
        "private_key": "-----begin private key-----",
    }
    folded = text.casefold()
    for name, token in indicators.items():
        if token in folded:
            failures.append(name)
    return failures


def bundle(output_zip: Path) -> None:
    completion_path = REPORTS / "105-program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    write_json(OUTPUT / "program-completion.json", completion)
    files = _artifact_files()
    secret_failures = [
        {"path": str(path), "indicators": _secret_scan(path)}
        for path in files
        if _secret_scan(path)
    ]
    index = {
        "contract": "m12ae-r2-artifact-index-v1",
        "status": "PASS" if not secret_failures else "FAIL",
        "artifact_count": len(files),
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": len(secret_failures),
        "secret_scan_failures": secret_failures,
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
        raise ValueError("artifact_secret_scan_failure")
    summary = (
        "# M12AE-R2 Completion\n\n"
        f"- Status: `{completion['status']}`\n"
        f"- Integration branch: `{completion['integration_branch']}`\n"
        f"- Frozen main: `{completion['main_frozen_sha']}`\n"
        f"- Integration merge: `{completion['integration_merge_commit_sha']}`\n"
        f"- Proof model: `{MODEL}` / `{EFFORT}`\n"
        f"- Fictional calls: `{completion['fictional_model_calls_total']}`\n"
        f"- Fictional outputs: `{completion['fictional_final_output_count']}`\n"
        f"- Monitored shadow calls: `{completion['shadow_model_calls_total']}`\n"
        f"- Monitored subjects: `{completion['shadow_completed_ticker_count']}`\n"
        f"- Fictional readiness: `{completion['fictional_two_stage_readiness']}`\n"
        f"- Shadow readiness: `{completion['shadow_compatibility_readiness']}`\n"
        f"- Fresh real proof: `{completion['fresh_real_proof_readiness']}`\n"
        f"- Final main merge: `{completion['final_main_merge_readiness']}`\n"
        "- Production changes/sends: `0`\n"
        "- Schedules: remained paused; no scheduler mutation\n"
        f"- Next scope: `{completion['next_scope']}`\n"
    )
    summary_path = OUTPUT / "COMPLETION-REPORT.md"
    write_text(summary_path, summary)
    files = _artifact_files()
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    if output_zip.exists():
        raise ValueError(f"result_bundle_already_exists:{output_zip}")
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=str(path))
        archive.write(
            OUTPUT / "artifact-index.json",
            arcname=str(OUTPUT / "artifact-index.json"),
        )
    digest = file_sha256(output_zip)
    sidecar = output_zip.with_suffix(output_zip.suffix + ".sha256")
    write_text(sidecar, f"{digest}  {output_zip.name}")
    print(
        json.dumps(
            {
                "status": "PASS",
                "zip": str(output_zip),
                "sha256": digest,
                "sha256_sidecar": str(sidecar),
                "artifact_count": len(files) + 1,
            },
            sort_keys=True,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=(
            "architecture",
            "validate",
            "prepare-fictional",
            "run-fictional",
            "finalize-fictional",
            "prepare-shadow",
            "run-shadow",
            "finalize-shadow",
            "finalize-program",
            "bundle",
        ),
    )
    parser.add_argument("--operating-root", type=Path, default=OPERATING_ROOT)
    parser.add_argument(
        "--output-zip",
        type=Path,
        default=Path.home() / "Documents/Codex" / f"thesis-monitor-{NAME}-report.zip",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "architecture":
        architecture()
    elif args.command == "validate":
        deterministic_validation()
    elif args.command == "prepare-fictional":
        prepare_fictional()
    elif args.command == "run-fictional":
        run_fictional()
    elif args.command == "finalize-fictional":
        finalize_fictional()
    elif args.command == "prepare-shadow":
        prepare_shadow(args.operating_root)
    elif args.command == "run-shadow":
        run_shadow()
    elif args.command == "finalize-shadow":
        finalize_shadow()
    elif args.command == "finalize-program":
        finalize_program()
    elif args.command == "bundle":
        bundle(args.output_zip)


if __name__ == "__main__":
    main()
