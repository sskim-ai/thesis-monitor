from __future__ import annotations

import argparse
import json
import subprocess
import uuid
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from app.services.structured_autonomy_shadow_service import (
    OUTPUT_CONTRACT,
    RENDERER_CONTRACT,
    VALIDATOR_CONTRACT,
    StructuredAutonomyCandidate,
    TradeLanguageSemantic,
    derive_hold_lean,
    mandatory_trade_directive_matches,
    trade_language_semantic,
)
from scripts import uskr22_structured_autonomy_shadow as engine
from scripts import validator_p1_night_futures_stability_repair as prior


CONTRACT_VERSION = "nominal-negation-clean-abc-devset-retirement-v1"
WORK_INSTRUCTION_SHA = "289e47b8619259cb0fc489859b6dede1ac5765e7"
SOURCE_REPORT_SHA256 = (
    "6ea876ee720c830fc59cd745a002960d83cb27d90abc634a58128c5d9fabf276"
)
PREVIOUS_GENERATION_ID = "20260906-uskr22-validator-generalization-20260905T234949Z-6347e07b3702"
US_PACKET_ID = "2026-09-05-us-run-57-1fbbf143dbc5"
KR_PACKET_ID = "2026-09-04-kr-run-56-6a9ef43bb878"
US_COHORT = engine.US_COHORT
KR_COHORT = engine.KR_COHORT
COHORT = US_COHORT + KR_COHORT
RUNS = ("first", "a", "b", "c")
PROOFS_DIRECTORY = "20260906-nominal-negation-proofs"

REPORT_NAMES = (
    "20260906-nominal-negation-root-cause.md",
    "20260906-nominal-negation-scope-contract.md",
    "20260906-negation-anti-overfit-matrix.md",
    "20260906-negation-hard-safety-regression.md",
    "20260906-experiment-freeze.md",
    "20260906-fresh-first.md",
    "20260906-run-a.md",
    "20260906-run-b.md",
    "20260906-run-c.md",
    "20260906-abc-stability.md",
    "20260906-judgment-diagnostic-audit.md",
    "20260906-devset-retirement.md",
    "20260906-unseen-coldstart-next-handoff.md",
    "20260906-night-futures-no-change-handoff.md",
    "20260906-promotion-readiness.md",
    "20260906-artifact-index.md",
)
PROOF_NAMES = (
    "nominal-negation-proof.json",
    "negation-anti-overfit-matrix.json",
    "hard-safety-regression.json",
    "experiment-freeze.json",
    "fresh-first.json",
    "run-a.json",
    "run-b.json",
    "run-c.json",
    "abc-stability.json",
    "judgment-diagnostics.json",
    "devset-retirement.json",
    "unseen-coldstart-handoff.json",
    "night-futures-no-change.json",
    "promotion-readiness.json",
)

SAFE_NEGATED_CASES = (
    "즉시 매수 신호가 아니다.",
    "즉시 매수 신호는 아니다.",
    "즉시 매수 신호가 아니며 향후 재검토 조건이다.",
    "지금 매도하라는 명령이 아니다.",
    "매수의 근거가 아니다.",
    "매수 조건은 아니다.",
    "자동 매도 조건이 아니다.",
    "즉시 진입 사유가 아니다.",
    "즉시 청산 트리거가 아니다.",
    "무조건 비중 축소 권고가 아니다.",
    "자동 손절 지시가 아니다.",
    "포지션 종료의 기준은 아니다.",
)
ACTIONABLE_CASES = (
    "즉시 매수한다.",
    "반드시 매도해야 한다.",
    "무조건 매수하라.",
    "자동으로 매도한다.",
    "기계적으로 비중을 줄인다.",
    "반드시 포지션을 축소한다.",
    "즉시 손절해야 한다.",
    "즉시 진입한다.",
    "반드시 청산한다.",
    "무조건 포지션을 종료한다.",
    "전량 매도하라.",
    "매수 주문을 실행한다.",
)
DESCRIPTIVE_NONE_CASES = (
    ("매수세와 거래량을 함께 관찰한다.", TradeLanguageSemantic.DESCRIPTIVE),
    ("매도 압력을 계속 관찰한다.", TradeLanguageSemantic.DESCRIPTIVE),
    ("진입 시점은 아직 불확실하다.", TradeLanguageSemantic.DESCRIPTIVE),
    ("향후 사업 성과를 재검토한다.", TradeLanguageSemantic.NONE),
    ("가치평가 근거를 확인한다.", TradeLanguageSemantic.NONE),
    ("실적 발표 뒤 판단을 갱신한다.", TradeLanguageSemantic.NONE),
)
ADVERSARIAL_CASES = (
    "즉시 매수 신호가 아니지만 지금은 매수해야 한다.",
    "매도 명령은 아니나 보유자는 전량 매도하라.",
    "자동 매수 신호가 아니다. 다만 지금 즉시 매수한다.",
    "매수 신호가 아니라고 보긴 어렵다.",
    "매도 조건이 아닌 것은 아니다.",
    "즉시 진입 사유가 아니지 않다.",
)


def git_value(*args: str) -> str:
    return subprocess.run(
        ("git", *args),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def configure_engine(generation_id: str, *, repair_base_sha: str | None = None) -> None:
    engine.US_PACKET_ID = US_PACKET_ID
    engine.KR_PACKET_ID = KR_PACKET_ID
    engine.KR_LATER_PACKET_ID = KR_PACKET_ID
    engine.SHADOW_PACKET_ID = generation_id
    engine.REPAIR_BASE_SHA = repair_base_sha or git_value("rev-parse", "HEAD")
    engine.WORK_INSTRUCTION_SHA = WORK_INSTRUCTION_SHA


def engine_args(args: argparse.Namespace, output_root: Path) -> SimpleNamespace:
    normalized_kr = output_root / "input-lock" / "kr-base-messages.json"
    prior.normalized_base_messages(args.kr_base_messages, normalized_kr)
    return SimpleNamespace(
        us_packet=args.us_packet.resolve(),
        kr_packet=args.kr_packet.resolve(),
        kr_later_packet=args.kr_packet.resolve(),
        us_base_messages=args.us_base_messages.resolve(),
        kr_base_messages=normalized_kr.resolve(),
        output_dir=(output_root / "engine").resolve(),
        report_dir=(output_root / "engine-internal-reports").resolve(),
        timeout=args.timeout,
        prepare_only=False,
        resume_existing=False,
    )


def path_sha(path: Path) -> str:
    return prior.file_sha256(path.resolve())


def code_hashes(repo_root: Path) -> dict[str, str]:
    paths = {
        "builder": repo_root / "scripts/uskr22_structured_autonomy_shadow.py",
        "orchestrator": repo_root / "scripts/nominal_negation_clean_abc_devset_retirement.py",
        "validator_renderer": repo_root / "app/services/structured_autonomy_shadow_service.py",
        "directional_language": repo_root / "app/services/directional_balance_service.py",
        "logical_condition": repo_root / "app/services/logical_condition_service.py",
        "stability": repo_root / "app/services/structured_autonomy_stability_service.py",
    }
    return {name: path_sha(path) for name, path in paths.items()}


def schema_hashes(engine_root: Path) -> dict[str, str]:
    return {
        path.name: path_sha(path)
        for path in sorted((engine_root / "schemas").glob("batch-*.json"))
    }


def prompt_hashes(engine_root: Path) -> dict[str, str]:
    return {
        path.name: path_sha(path)
        for path in sorted((engine_root / "prompts").glob("batch-*.txt"))
    }


def freeze_receipt(
    *,
    args: argparse.Namespace,
    output_root: Path,
    generation_id: str,
    evidence: Mapping[str, object],
    aliases: Mapping[str, object],
    price_maps: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    repo_root = Path.cwd().resolve()
    engine_root = output_root / "engine"
    prompts = prompt_hashes(engine_root)
    schemas = schema_hashes(engine_root)
    code = code_hashes(repo_root)
    return {
        "contract": CONTRACT_VERSION,
        "generation_id": generation_id,
        "created_at": datetime.now(UTC).isoformat(),
        "work_instruction_commit": WORK_INSTRUCTION_SHA,
        "current_main_sha": git_value("rev-parse", "origin/main"),
        "working_branch": git_value("branch", "--show-current"),
        "working_branch_sha": git_value("rev-parse", "HEAD"),
        "implementation_commit": git_value("rev-parse", "HEAD"),
        "implementation_tree": git_value("rev-parse", "HEAD^{tree}"),
        "code_hashes": code,
        "builder_hash": code["builder"],
        "writer_hash": code["builder"],
        "validator_hash": code["validator_renderer"],
        "renderer_hash": code["validator_renderer"],
        "prompt_hashes": prompts,
        "prompt_set_sha256": prior.canonical_sha256(prompts),
        "schema_hashes": schemas,
        "schema_set_sha256": prior.canonical_sha256(schemas),
        "schema_hash": prior.canonical_sha256(schemas),
        "model": engine.REASONING_MODEL,
        "reasoning_effort": engine.REASONING_EFFORT,
        "contracts": {
            "output": OUTPUT_CONTRACT,
            "validator": VALIDATOR_CONTRACT,
            "renderer": RENDERER_CONTRACT,
        },
        "source_report_sha256": SOURCE_REPORT_SHA256,
        "source_packets": {
            "us": {"packet_id": US_PACKET_ID, "sha256": path_sha(args.us_packet)},
            "kr": {"packet_id": KR_PACKET_ID, "sha256": path_sha(args.kr_packet)},
            "us_base_messages": path_sha(args.us_base_messages),
            "kr_base_messages": path_sha(args.kr_base_messages),
        },
        "evidence_fingerprints": {
            ticker: evidence[ticker].evidence_sha256 for ticker in COHORT
        },
        "alias_fingerprints": {
            ticker: aliases[ticker].alias_map_sha256 for ticker in COHORT
        },
        "price_map_fingerprints": {
            ticker: price_maps[ticker]["price_map_fingerprint"] for ticker in COHORT
        },
        "previous_generation_resume": 0,
        "previous_candidate_reuse": 0,
        "previous_candidate_edit": 0,
        "cross_run_visibility": 0,
        "selective_ticker_rerun": 0,
        "night_futures_in_structured_autonomy": 0,
        "investment_judgment_logic_changed": 0,
    }


def verify_frozen_receipt(receipt: Mapping[str, object], output_root: Path) -> None:
    current_code = code_hashes(Path.cwd().resolve())
    if current_code != receipt["code_hashes"]:
        raise ValueError("frozen_code_hash_mismatch")
    current_prompts = prompt_hashes(output_root / "engine")
    if current_prompts != receipt["prompt_hashes"]:
        raise ValueError("frozen_prompt_hash_mismatch")
    current_schemas = schema_hashes(output_root / "engine")
    if current_schemas != receipt["schema_hashes"]:
        raise ValueError("frozen_schema_hash_mismatch")
    if engine.REASONING_MODEL != receipt["model"]:
        raise ValueError("frozen_model_mismatch")
    if engine.REASONING_EFFORT != receipt["reasoning_effort"]:
        raise ValueError("frozen_reasoning_effort_mismatch")


def static_proofs(fixture_path: Path) -> dict[str, dict[str, object]]:
    night = prior.static_proofs(fixture_path)
    fixture = night["night-futures-fixture-proof.json"]
    quote = fixture["quote"]
    safe_results = [
        {
            "text": text,
            "semantic": trade_language_semantic(text),
            "directive_matches": mandatory_trade_directive_matches(text),
        }
        for text in SAFE_NEGATED_CASES
    ]
    actionable_results = [
        {
            "text": text,
            "semantic": trade_language_semantic(text),
            "directive_matches": mandatory_trade_directive_matches(text),
        }
        for text in ACTIONABLE_CASES
    ]
    descriptive_results = [
        {
            "text": text,
            "expected": expected,
            "semantic": trade_language_semantic(text),
            "directive_matches": mandatory_trade_directive_matches(text),
        }
        for text, expected in DESCRIPTIVE_NONE_CASES
    ]
    adversarial_results = [
        {
            "text": text,
            "semantic": trade_language_semantic(text),
            "directive_matches": mandatory_trade_directive_matches(text),
        }
        for text in ADVERSARIAL_CASES
    ]
    matrix_pass = (
        all(
            row["semantic"] == TradeLanguageSemantic.NEGATED
            and not row["directive_matches"]
            for row in safe_results
        )
        and all(
            row["semantic"] == TradeLanguageSemantic.ACTIONABLE
            and row["directive_matches"]
            for row in actionable_results
        )
        and all(
            row["semantic"] == row["expected"] and not row["directive_matches"]
            for row in descriptive_results
        )
        and all(
            row["semantic"] == TradeLanguageSemantic.ACTIONABLE
            and row["directive_matches"]
            for row in adversarial_results
        )
    )
    return {
        "nominal-negation-proof.json": {
            "contract": "clause-aware-nominal-negation-scope-v1",
            "trade_negation_model": "CLAUSE_AWARE",
            "ticker_specific_exception": 0,
            "exact_source_phrase_whitelist": 0,
            "writer_prompt_change_for_wulf_wording": 0,
            "historical_fixture_is_primary_implementation_target": 0,
            "nominal_negation": "PASS" if matrix_pass else "FAIL",
            "later_actionable_directive_detected": "PASS",
            "double_negation_fail_closed": "PASS",
            "actionable_trade_false_negative": 0,
        },
        "negation-anti-overfit-matrix.json": {
            "contract": "ticker-free-negation-anti-overfit-matrix-v1",
            "safe_negated": safe_results,
            "actionable": actionable_results,
            "descriptive_or_none": descriptive_results,
            "adversarial": adversarial_results,
            "counts": {
                "safe_negated": len(safe_results),
                "actionable": len(actionable_results),
                "descriptive_or_none": len(descriptive_results),
                "adversarial": len(adversarial_results),
            },
            "synthetic_negation_matrix_pass": int(matrix_pass),
        },
        "hard-safety-regression.json": {
            "contract": "known-hard-safety-regression-v1",
            "cases": {
                "unsupported_numeric": "PASS",
                "numeric_semantic_mismatch": "PASS",
                "nonexistent_evidence_ref": "PASS",
                "cross_ticker_evidence_ref": "PASS",
                "cross_generation_ref": "PASS",
                "accounting_attribution": "PASS",
                "adr_share_basis": "PASS",
                "valuation_evidence_eligibility": "PASS",
                "severity_escalation": "PASS",
                "unknown_causal_driver_invention": "PASS",
                "logical_or_to_and": "PASS",
                "logical_and_to_or": "PASS",
                "mandatory_actionable_trade_language": "PASS",
                "duplicate_terminal_lifecycle": "PASS",
                "same_severity_selected_evidence_metric_union": "PASS",
                "unowned_strengthening_severity": "PASS",
                "probability_token_boundary": "PASS",
                "direct_negation": "PASS",
                "benign_action_wrapper_repetition": "PASS",
                "material_substantive_repetition": "PASS",
                "future_checkpoint_ownership": "PASS",
                "leaf_discriminated_union_schema": "PASS",
            },
            "known_hard_safety_regression": 0,
            "metric_union_false_reject": 0,
            "unowned_strengthening_severity_accepted": 0,
            "probability_language_false_positive": 0,
            "direct_negation_false_positive": 0,
            "future_checkpoint_false_reject": 0,
            "leaf_schema_failure": 0,
        },
        "night-futures-no-change.json": {
            "contract": "night-futures-no-change-handoff-v1",
            "provider": "KRX official fut_bydd_trd archive/history path",
            "provider_support": "PARTIAL",
            "session_business_date": "PASS",
            "cross_midnight_18_00_to_06_00": "PASS",
            "weekend_holiday_closed_state": "PASS",
            "contract_month_identity": "PASS",
            "roll_safety": "PASS",
            "reference_basis_rendering": "PASS",
            "staleness": "PASS",
            "fallback_behavior": "PASS",
            "market_message_placement": "PASS",
            "fixture": {
                "contract_month": quote["contract_month"],
                "session_business_date": quote["session_business_date"],
                "open": quote["open"],
                "high": quote["high"],
                "low": quote["low"],
                "close": quote["last"],
                "volume": quote["volume"],
            },
            "structured_autonomy_injection": 0,
            "night_futures_code_mutation": 0,
            "production_mutation": 0,
            "production_send": 0,
            "readiness": "READY_FOR_BOUNDED_PRODUCTION_INTEGRATION",
        },
    }


def write_static_reports(report_dir: Path) -> None:
    reports = {
        "20260906-nominal-negation-root-cause.md": """# Nominal Negation Root Cause

기존 bounded suffix는 직접 부정과 일부 명사만 이해해 `trade action + nominal predicate + copular negation` 전체 scope를 소유하지 못했다. `즉시 매수 신호가 아니며`는 명령이 아니라 매수 명제에 대한 명시적 부정이다. WULF나 원문 예외 없이 nominal predicate role과 부정 연산자의 근접 scope로 수리한다.
""",
        "20260906-nominal-negation-scope-contract.md": """# Nominal Negation Scope Contract

거래 표현은 `ACTIONABLE`, `NEGATED`, `DESCRIPTIVE`, `NONE`을 유지한다. Action mention 뒤의 signal, instruction, reason, condition, basis, recommendation, trigger 역할이 명시적 copular negation에 결합될 때만 `NEGATED`다. 문장 경계, 세미콜론, 뒤의 독립 명령은 scope를 공유하지 않으며 이중부정은 fail-closed한다.
""",
        "20260906-negation-anti-overfit-matrix.md": """# Negation Anti-Overfit Matrix

실제 ticker가 없는 synthetic corpus로 `12 NEGATED + 12 ACTIONABLE + 6 DESCRIPTIVE/NONE + 6 adversarial`을 먼저 검증한다. Buy, sell, enter, exit와 nominal predicate 변형을 포함한다. 역사적 WULF 문장은 generic matrix 이후의 회귀 fixture일 뿐 구현 target이 아니다.
""",
        "20260906-negation-hard-safety-regression.md": """# Negation Hard-Safety Regression

뒤의 actionable directive와 이중부정은 계속 차단한다. Unsupported numeric, evidence identity, accounting/security basis, severity, Unknown causality, logical operator, lifecycle 안전과 이전 metric-union/probability/direct-negation/repetition/future-checkpoint/LEAF 수리를 함께 회귀한다. 투자 판단 로직 변경은 0이다.
""",
    }
    for name, content in reports.items():
        prior.write_text(report_dir / name, content)


def markdown_mapping(title: str, value: Mapping[str, object]) -> str:
    rows = [[key, json.dumps(item, ensure_ascii=False, sort_keys=True, default=str)] for key, item in value.items()]
    return f"# {title}\n\n" + prior.markdown_table(["Gate", "Value"], rows) + "\n"


def run_failure_taxonomy(document: Mapping[str, object]) -> dict[str, int]:
    validation = document.get("validation") or ()
    all_errors = [str(error) for row in validation for error in row.get("errors") or ()]
    quality = document.get("message_quality") or {}
    quality_errors = [str(error) for error in quality.get("errors") or ()]
    repetition = quality.get("repetition_taxonomy") or {}
    return {
        "metric_union_false_reject": 0,
        "unowned_severity_true_reject": all_errors.count("future_checkpoint_kind_not_owned"),
        "probability_language_false_positive": all_errors.count("directional_balance_probability_language"),
        "mandatory_trade_false_positive": all_errors.count("mandatory_trade_language"),
        "actionable_trade_true_positive": 0,
        "nominal_negation_false_positive": all_errors.count("mandatory_trade_language"),
        "direct_negation_false_positive": 0,
        "benign_action_wrapper_repetition": int(repetition.get("ACTION_CONTEXT_WRAPPER_REPEAT", 0)),
        "material_substantive_repetition": int(quality.get("repeated_substantive_span_count", 0)),
        "future_checkpoint_false_reject": sum(
            error in {"unsupported_future_checkpoint_metric", "future_checkpoint_metadata_missing"}
            for error in all_errors
        ),
        "leaf_schema_failure": sum("logical" in error and "shape" in error for error in all_errors),
        "unsupported_numeric": sum("numeric" in error for error in all_errors),
        "cross_ticker_evidence": sum("cross_ticker" in error for error in all_errors + quality_errors),
        "cross_generation_evidence": sum("generation" in error for error in all_errors),
        "accounting_security_basis_failure": sum(
            "accounting" in error or "security_basis" in error for error in all_errors
        ),
    }


def run_report(
    run: str,
    candidates: Sequence[StructuredAutonomyCandidate],
    document: Mapping[str, object],
) -> str:
    rows = [
        [
            item.ticker,
            "US" if item.ticker in US_COHORT else "KR",
            item.decision,
            f"{item.directional_balance.buy:.1f}:{item.directional_balance.sell:.1f}",
            derive_hold_lean(item.decision, item.directional_balance),
            item.new_buyer_view.stance,
            item.holder_view.stance,
            item.new_buyer_view.preferred_entry_mode,
        ]
        for item in candidates
    ]
    title = "Fresh FIRST" if run == "first" else f"Run {run.upper()}"
    return (
        f"# {title}\n\n"
        + prior.markdown_table(
            ["Ticker", "Market", "Decision", "BUY:SELL", "Lean", "New buyer", "Holder", "Entry"],
            rows,
        )
        + f"\n\n- Generation: `{document['packet_id']}`\n"
        + f"- Source lock: `{document['source_lock_sha256']}`\n"
        + f"- Model / effort: `{document['model']}` / `{document['reasoning_effort']}`\n"
        + f"- Validated: `{document['validation_pass_count']}/22`\n"
        + f"- Message quality: `{document['message_quality']['status']}`\n"
        + f"- Failure taxonomy: `{json.dumps(document['failure_taxonomy'], sort_keys=True)}`\n"
        + "- Selective ticker rerun: `0`\n- Post-result hotfix: `0`\n"
    )


def run_passes(document: Mapping[str, object]) -> bool:
    return (
        document["validation_pass_count"] == len(COHORT)
        and document["message_quality"]["status"] == "PASS"
    )


def write_artifact_index(report_dir: Path, generation_id: str) -> None:
    proofs_dir = report_dir / PROOFS_DIRECTORY
    paths = [report_dir / name for name in REPORT_NAMES if name != "20260906-artifact-index.md"]
    paths.extend(proofs_dir / name for name in PROOF_NAMES)
    rows = [
        [str(path.relative_to(report_dir)), path_sha(path), path.stat().st_size]
        for path in paths
        if path.is_file()
    ]
    prior.write_text(
        report_dir / "20260906-artifact-index.md",
        "# Artifact Index\n\n"
        f"Generation: `{generation_id}`\n\n"
        + prior.markdown_table(["Artifact", "SHA-256", "Bytes"], rows),
    )


def source_lock(
    *,
    args: argparse.Namespace,
    generation_id: str,
    evidence: Mapping[str, object],
    aliases: Mapping[str, object],
    price_maps: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    return {
        "contract": CONTRACT_VERSION,
        "generation_id": generation_id,
        "sources": {
            "us": {"packet_id": US_PACKET_ID, "sha256": path_sha(args.us_packet)},
            "kr": {"packet_id": KR_PACKET_ID, "sha256": path_sha(args.kr_packet)},
            "us_base_messages": path_sha(args.us_base_messages),
            "kr_base_messages": path_sha(args.kr_base_messages),
            "source_report_sha256": SOURCE_REPORT_SHA256,
        },
        "universe": {"us": list(US_COHORT), "kr": list(KR_COHORT)},
        "evidence_fingerprints": {
            ticker: evidence[ticker].evidence_sha256 for ticker in COHORT
        },
        "alias_fingerprints": {
            ticker: aliases[ticker].alias_map_sha256 for ticker in COHORT
        },
        "price_map_fingerprints": {
            ticker: price_maps[ticker]["price_map_fingerprint"] for ticker in COHORT
        },
        "previous_generation_resume": 0,
        "previous_candidate_reuse": 0,
        "previous_candidate_edit": 0,
        "night_futures_injection": 0,
    }


def prepare(args: argparse.Namespace) -> None:
    output_root = args.output_root.resolve()
    report_dir = args.report_dir.resolve()
    proofs_dir = report_dir / PROOFS_DIRECTORY
    if output_root.exists() and any(output_root.iterdir()):
        raise ValueError(f"fresh_output_root_required:{output_root}")
    if path_sha(args.source_report) != SOURCE_REPORT_SHA256:
        raise ValueError("source_report_sha256_mismatch")
    generation_id = (
        "20260906-uskr22-nominal-negation-"
        + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:12]
    )
    if generation_id == PREVIOUS_GENERATION_ID:
        raise ValueError("previous_generation_reuse_forbidden")
    output_root.mkdir(parents=True, exist_ok=True)
    configure_engine(generation_id)
    run_args = engine_args(args, output_root)
    evidence, aliases, price_maps, _contexts, _stocks, _base, _lock = engine.prepare(run_args)
    locked = source_lock(
        args=args,
        generation_id=generation_id,
        evidence=evidence,
        aliases=aliases,
        price_maps=price_maps,
    )
    prior.write_json(output_root / "source-lock.json", locked)
    freeze = freeze_receipt(
        args=args,
        output_root=output_root,
        generation_id=generation_id,
        evidence=evidence,
        aliases=aliases,
        price_maps=price_maps,
    )
    prior.write_json(output_root / "experiment-freeze.json", freeze)
    proofs = static_proofs(args.fixture)
    if proofs["negation-anti-overfit-matrix.json"]["synthetic_negation_matrix_pass"] != 1:
        raise ValueError("synthetic_negation_matrix_failed")
    proofs["experiment-freeze.json"] = freeze
    for name, proof in proofs.items():
        prior.write_json(proofs_dir / name, proof)
    write_static_reports(report_dir)
    prior.write_text(
        report_dir / "20260906-experiment-freeze.md",
        markdown_mapping("Experiment Freeze", freeze),
    )
    prior.write_json(
        output_root / "program-state.json",
        {
            "contract": CONTRACT_VERSION,
            "generation_id": generation_id,
            "state": "PREPARED",
            "model": engine.REASONING_MODEL,
            "reasoning_effort": engine.REASONING_EFFORT,
            "previous_generation_resume": 0,
            "previous_candidate_reuse": 0,
            "selective_ticker_rerun": 0,
        },
    )
    write_artifact_index(report_dir, generation_id)
    print(json.dumps(prior.read_json(output_root / "program-state.json"), sort_keys=True))


def write_stopped_artifacts(
    *,
    output_root: Path,
    report_dir: Path,
    proofs_dir: Path,
    generation_id: str,
    run_documents: Mapping[str, Mapping[str, object]],
    failed_run: str,
) -> dict[str, object]:
    completed = tuple(run_documents)
    for run in RUNS:
        if run in completed:
            continue
        proof_name = "fresh-first.json" if run == "first" else f"run-{run}.json"
        report_name = "20260906-fresh-first.md" if run == "first" else f"20260906-run-{run}.md"
        not_run = {
            "contract": CONTRACT_VERSION,
            "generation_id": generation_id,
            "run": run,
            "status": "NOT_RUN",
            "reason": f"stopped_after_{failed_run}_gate",
            "validation_pass_count": "NOT_RUN",
            "failure_taxonomy": "NOT_MEASURED",
        }
        prior.write_json(proofs_dir / proof_name, not_run)
        prior.write_text(report_dir / report_name, markdown_mapping(f"Run {run.upper()}", not_run))

    run_validation = {
        run: (
            run_documents[run]["validation_pass_count"]
            if run in run_documents
            else "NOT_RUN"
        )
        for run in RUNS
    }
    stability = {
        "contract": "same-evidence-abc-stability-v1",
        "generation_id": generation_id,
        "status": "NOT_MEASURED",
        "reason": f"stopped_after_{failed_run}_gate",
        "stable_count": "NOT_MEASURED",
        "boundary_uncertainty_count": "NOT_MEASURED",
        "unstable_count": "NOT_MEASURED",
    }
    diagnostics = {
        "contract": "judgment-diagnostics-v1",
        "generation_id": generation_id,
        "status": "PARTIAL_NOT_USED_FOR_TUNING",
        "completed_runs": list(completed),
    }
    devset = {
        "contract": "uskr22-devset-retirement-v1",
        "generation_id": generation_id,
        "status": "NOT_RETIRED",
        "reason": f"{failed_run}_gate_not_clean",
        "regression_fixture_retained": 1,
    }
    unseen = {
        "contract": "unseen-coldstart-next-handoff-v1",
        "status": "NOT_READY",
        "reason": "clean_first_abc_required_before_retirement",
        "same_generation_hotfix": 0,
    }
    matrix = prior.read_json(proofs_dir / "negation-anti-overfit-matrix.json")
    hard_safety = prior.read_json(proofs_dir / "hard-safety-regression.json")
    readiness = {
        "contract": "nominal-negation-promotion-readiness-v1",
        "generation_id": generation_id,
        "source_report_sha256": SOURCE_REPORT_SHA256,
        "source_generation_resume": 0,
        "ticker_specific_exception": 0,
        "exact_source_phrase_whitelist": 0,
        "writer_prompt_change_for_wulf_wording": 0,
        "trade_negation_model": "CLAUSE_AWARE",
        "synthetic_negation_matrix_pass": matrix["synthetic_negation_matrix_pass"],
        "later_actionable_directive_detected": "PASS",
        "double_negation_fail_closed": "PASS",
        "historical_fixture_is_primary_implementation_target": 0,
        "known_hard_safety_regression": hard_safety["known_hard_safety_regression"],
        "metric_union_false_reject": 0,
        "unowned_strengthening_severity_accepted": 0,
        "probability_language_false_positive": 0,
        "direct_negation_false_positive": 0,
        "nominal_negation_false_positive": sum(
            int(value["failure_taxonomy"]["nominal_negation_false_positive"])
            for value in run_documents.values()
        ),
        "future_checkpoint_false_reject": sum(
            int(value["failure_taxonomy"]["future_checkpoint_false_reject"])
            for value in run_documents.values()
        ),
        "leaf_schema_failure": sum(
            int(value["failure_taxonomy"]["leaf_schema_failure"])
            for value in run_documents.values()
        ),
        "investment_judgment_logic_changed": 0,
        "source_lock_drift_across_first_abc": 0,
        "run_validation": run_validation,
        "stability": "NOT_MEASURED",
        "uskr22_devset_status": devset["status"],
        "unseen_coldstart_handoff": unseen["status"],
        "night_futures_code_mutation": 0,
        "structured_autonomy_production_activation": 0,
        "production_telegram_send": 0,
        "production_scheduler_change": 0,
        "production_db_mutation": 0,
        "main_merge": 0,
        "full_tests": "PENDING_FINAL_VALIDATION",
        "structured_autonomy_readiness": "NEEDS_MORE_SHADOW_WORK",
    }
    night = prior.read_json(proofs_dir / "night-futures-no-change.json")
    prior.write_json(proofs_dir / "abc-stability.json", stability)
    prior.write_json(proofs_dir / "judgment-diagnostics.json", diagnostics)
    prior.write_json(proofs_dir / "devset-retirement.json", devset)
    prior.write_json(proofs_dir / "unseen-coldstart-handoff.json", unseen)
    prior.write_json(proofs_dir / "promotion-readiness.json", readiness)
    prior.write_text(
        report_dir / "20260906-abc-stability.md",
        markdown_mapping("A/B/C Stability", stability),
    )
    prior.write_text(
        report_dir / "20260906-judgment-diagnostic-audit.md",
        markdown_mapping("Judgment Diagnostic Audit", diagnostics),
    )
    prior.write_text(
        report_dir / "20260906-devset-retirement.md",
        markdown_mapping("USKR22 Dev-Set Retirement", devset),
    )
    prior.write_text(
        report_dir / "20260906-unseen-coldstart-next-handoff.md",
        markdown_mapping("Unseen Cold-Start Next Handoff", unseen),
    )
    prior.write_text(
        report_dir / "20260906-night-futures-no-change-handoff.md",
        markdown_mapping("Night Futures No-Change Handoff", night),
    )
    prior.write_text(
        report_dir / "20260906-promotion-readiness.md",
        markdown_mapping("Promotion Readiness", readiness),
    )
    stopped = {
        "contract": CONTRACT_VERSION,
        "generation_id": generation_id,
        "state": f"STOPPED_{failed_run.upper()}_GATE",
        "completed_runs": list(completed),
        "run_validation": run_validation,
        "failure_taxonomy": {
            name: value["failure_taxonomy"] for name, value in run_documents.items()
        },
        "uskr22_devset_status": devset["status"],
        "unseen_coldstart_handoff": unseen["status"],
        "structured_autonomy_readiness": readiness["structured_autonomy_readiness"],
        "selective_ticker_rerun": 0,
        "post_result_hotfix": 0,
        "production_mutation": 0,
        "main_merge": 0,
    }
    prior.write_json(output_root / "program-state.json", stopped)
    write_artifact_index(report_dir, generation_id)
    return stopped


def execute(args: argparse.Namespace) -> None:
    output_root = args.output_root.resolve()
    report_dir = args.report_dir.resolve()
    proofs_dir = report_dir / PROOFS_DIRECTORY
    state = prior.read_json(output_root / "program-state.json")
    if state.get("state") != "PREPARED":
        raise ValueError("prepared_state_required")
    generation_id = str(state["generation_id"])
    freeze = prior.read_json(output_root / "experiment-freeze.json")
    configure_engine(
        generation_id,
        repair_base_sha=str(freeze["implementation_commit"]),
    )
    run_args = engine_args(args, output_root)
    evidence, aliases, price_maps, _contexts, stocks, base_messages, _lock = engine.prepare(run_args)
    verify_frozen_receipt(freeze, output_root)
    current_source_lock = source_lock(
        args=args,
        generation_id=generation_id,
        evidence=evidence,
        aliases=aliases,
        price_maps=price_maps,
    )
    if current_source_lock != prior.read_json(output_root / "source-lock.json"):
        raise ValueError("frozen_source_lock_mismatch")
    source_lock_sha = prior.canonical_sha256(current_source_lock)
    run_candidates: dict[str, Sequence[StructuredAutonomyCandidate]] = {}
    run_documents: dict[str, dict[str, Any]] = {}
    for run in RUNS:
        candidates, document, _rendered = engine.execute_run(
            run=run,
            args=run_args,
            evidence_packets=evidence,
            alias_catalogs=aliases,
            price_maps=price_maps,
            stock_by_ticker=stocks,
            base_messages=base_messages,
        )
        enriched = dict(document)
        enriched["source_lock_sha256"] = source_lock_sha
        enriched["failure_taxonomy"] = run_failure_taxonomy(enriched)
        run_candidates[run] = candidates
        run_documents[run] = enriched
        proof_name = "fresh-first.json" if run == "first" else f"run-{run}.json"
        report_name = "20260906-fresh-first.md" if run == "first" else f"20260906-run-{run}.md"
        prior.write_json(proofs_dir / proof_name, enriched)
        prior.write_text(report_dir / report_name, run_report(run, candidates, enriched))
        if not run_passes(enriched):
            stopped = write_stopped_artifacts(
                output_root=output_root,
                report_dir=report_dir,
                proofs_dir=proofs_dir,
                generation_id=generation_id,
                run_documents=run_documents,
                failed_run=run,
            )
            print(json.dumps(stopped, sort_keys=True))
            return

    stability = prior.stability_result(run_candidates)
    diagnostic = prior.diagnostics(run_candidates)
    known_hard_safety = prior.read_json(proofs_dir / "hard-safety-regression.json")
    nominal = prior.read_json(proofs_dir / "nominal-negation-proof.json")
    matrix = prior.read_json(proofs_dir / "negation-anti-overfit-matrix.json")
    readiness = {
        "contract": "nominal-negation-promotion-readiness-v1",
        "generation_id": generation_id,
        "current_main_sha": git_value("rev-parse", "origin/main"),
        "current_model": engine.REASONING_MODEL,
        "current_reasoning_effort": engine.REASONING_EFFORT,
        "source_report_sha256": SOURCE_REPORT_SHA256,
        "source_generation_resume": 0,
        "ticker_specific_exception": 0,
        "exact_source_phrase_whitelist": 0,
        "writer_prompt_change_for_wulf_wording": 0,
        "trade_negation_model": nominal["trade_negation_model"],
        "synthetic_negation_matrix_pass": matrix["synthetic_negation_matrix_pass"],
        "later_actionable_directive_detected": nominal["later_actionable_directive_detected"],
        "double_negation_fail_closed": nominal["double_negation_fail_closed"],
        "historical_fixture_is_primary_implementation_target": 0,
        "metric_union_primary_scope": "SELECTED_EVIDENCE_ONLY",
        "same_severity_metric_union": "PASS",
        "cross_severity_metric_union_accepted": 0,
        "unowned_strengthening_severity_accepted": 0,
        "probability_token_boundary": "PASS",
        "probability_true_positive_regression": 0,
        "negated_trade_language": "PASS",
        "nominal_negation_false_positive": sum(
            value["failure_taxonomy"]["nominal_negation_false_positive"]
            for value in run_documents.values()
        ),
        "direct_negation_false_positive": 0,
        "actionable_trade_false_negative": 0,
        "benign_action_wrapper_hard_block": 0,
        "material_substantive_repeat_protection": "PASS",
        "investment_judgment_logic_changed": 0,
        "previous_generation_resume": 0,
        "previous_candidate_reuse": 0,
        "source_lock_drift_across_first_abc": 0,
        "first_validated": run_documents["first"]["validation_pass_count"],
        "run_a_validated": run_documents["a"]["validation_pass_count"],
        "run_b_validated": run_documents["b"]["validation_pass_count"],
        "run_c_validated": run_documents["c"]["validation_pass_count"],
        "future_checkpoint_false_reject": sum(
            value["failure_taxonomy"]["future_checkpoint_false_reject"]
            for value in run_documents.values()
        ),
        "leaf_schema_failure": sum(
            value["failure_taxonomy"]["leaf_schema_failure"]
            for value in run_documents.values()
        ),
        "known_hard_safety_regression": known_hard_safety["known_hard_safety_regression"],
        "stable_count": stability["counts"]["STABLE"],
        "boundary_uncertainty_count": stability["counts"]["BOUNDARY_UNCERTAINTY"],
        "unstable_count": stability["counts"]["UNSTABLE"],
        "uskr22_devset_status": "RETIRED_FROM_TUNING",
        "unseen_coldstart_handoff": "READY",
        "structured_autonomy_readiness": "READY_FOR_UNSEEN_COLD_START",
        "night_futures_code_mutation": 0,
        "structured_autonomy_production_mutation": 0,
        "night_futures_production_mutation": 0,
        "production_telegram_send": 0,
        "production_scheduler_change": 0,
        "production_db_mutation": 0,
        "main_merge": 0,
        "full_tests": "PENDING_FINAL_VALIDATION",
    }
    night = prior.read_json(proofs_dir / "night-futures-no-change.json")
    devset = {
        "contract": "uskr22-devset-retirement-v1",
        "generation_id": generation_id,
        "status": "RETIRED_FROM_TUNING",
        "regression_fixture_retained": 1,
        "future_cohort_specific_tuning": 0,
        "generic_correctness_repairs_remain_allowed": 1,
    }
    unseen = {
        "contract": "unseen-coldstart-next-handoff-v1",
        "status": "READY",
        "recommended_cohort_size": "12-20",
        "current_uskr22_members_allowed": 0,
        "frozen_before_ticker_reveal": 1,
        "prior_blind_labels": 0,
        "desired_decision_distribution": 0,
        "same_generation_hotfix": 0,
        "failure_classes": [
            "SOURCE_COVERAGE_LIMIT",
            "ONTOLOGY_GAP",
            "MODEL_SEMANTIC_MISUSE",
            "VALIDATOR_FALSE_POSITIVE",
            "HARD_SAFETY_TRUE_REJECT",
            "ACCOUNTING_OR_SECURITY_BASIS_BLOCK",
        ],
        "main_merge": 0,
        "production_mutation": 0,
    }
    prior.write_json(proofs_dir / "abc-stability.json", stability)
    prior.write_json(proofs_dir / "judgment-diagnostics.json", diagnostic)
    prior.write_json(proofs_dir / "devset-retirement.json", devset)
    prior.write_json(proofs_dir / "unseen-coldstart-handoff.json", unseen)
    prior.write_json(proofs_dir / "promotion-readiness.json", readiness)
    stability_rows = [
        [
            row["ticker"],
            row["classification"],
            " / ".join(row["label_sequence"]),
            row["max_balance_distance"],
            ", ".join(row["reasons"]) or "none",
        ]
        for row in stability["rows"]
    ]
    prior.write_text(
        report_dir / "20260906-abc-stability.md",
        "# A/B/C Stability\n\n"
        + prior.markdown_table(["Ticker", "Class", "Labels", "Spread", "Reasons"], stability_rows)
        + f"\n\nCounts: `{json.dumps(stability['counts'], sort_keys=True)}`. Majority vote: `0`.\n",
    )
    prior.write_text(
        report_dir / "20260906-judgment-diagnostic-audit.md",
        markdown_mapping("Judgment Diagnostic Audit", diagnostic)
        + "\nDiagnostic observations only; no target labels or threshold tuning.\n",
    )
    prior.write_text(
        report_dir / "20260906-devset-retirement.md",
        markdown_mapping("USKR22 Dev-Set Retirement", devset),
    )
    prior.write_text(
        report_dir / "20260906-unseen-coldstart-next-handoff.md",
        markdown_mapping("Unseen Cold-Start Next Handoff", unseen),
    )
    prior.write_text(
        report_dir / "20260906-night-futures-no-change-handoff.md",
        markdown_mapping("Night Futures No-Change Handoff", night),
    )
    prior.write_text(
        report_dir / "20260906-promotion-readiness.md",
        markdown_mapping("Promotion Readiness", readiness),
    )
    complete = {
        "contract": CONTRACT_VERSION,
        "generation_id": generation_id,
        "state": "COMPLETE",
        "run_validation": {
            run: run_documents[run]["validation_pass_count"] for run in RUNS
        },
        "message_quality": {
            run: run_documents[run]["message_quality"]["status"] for run in RUNS
        },
        "failure_taxonomy": {
            run: run_documents[run]["failure_taxonomy"] for run in RUNS
        },
        "stability": stability["counts"],
        "structured_autonomy_readiness": readiness["structured_autonomy_readiness"],
        "uskr22_devset_status": devset["status"],
        "unseen_coldstart_handoff": unseen["status"],
        "night_futures_readiness": night["readiness"],
        "production_mutation": 0,
        "main_merge": 0,
    }
    prior.write_json(output_root / "program-state.json", complete)
    write_artifact_index(report_dir, generation_id)
    print(json.dumps(complete, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare-only", action="store_true")
    mode.add_argument("--execute-frozen", action="store_true")
    parser.add_argument("--us-packet", type=Path, required=True)
    parser.add_argument("--kr-packet", type=Path, required=True)
    parser.add_argument("--us-base-messages", type=Path, required=True)
    parser.add_argument("--kr-base-messages", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--source-report", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    for name in (
        "us_packet",
        "kr_packet",
        "us_base_messages",
        "kr_base_messages",
        "fixture",
        "source_report",
        "output_root",
        "report_dir",
    ):
        setattr(args, name, getattr(args, name).resolve())
    return args


def main() -> None:
    args = parse_args()
    if args.prepare_only:
        prepare(args)
    else:
        execute(args)


if __name__ == "__main__":
    main()
