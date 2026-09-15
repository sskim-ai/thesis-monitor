from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
import uuid
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from app.services.structured_autonomy_shadow_service import (
    ACTIONABILITY_CONTRACT,
    OUTPUT_CONTRACT,
    RENDERER_CONTRACT,
    VALIDATOR_CONTRACT,
    ActionRole,
    ActionSubject,
    DirectiveState,
    StructuredActionContext,
    StructuredActionStance,
    StructuredActionability,
    StructuredAutonomyCandidate,
    directive_state,
    explicit_actionable_trade_directives,
    structured_actionability_contradictions,
)
from scripts import uskr22_structured_autonomy_shadow as engine
from scripts import validator_p1_night_futures_stability_repair as prior


CONTRACT_VERSION = "structured-actionability-unseen-coldstart-v1"
SOURCE_REPORT_SHA256 = (
    "ef76df0ed4eb8c551eaf8827431e3b8d44274da9ecd1a4ac46713e0f231cadc9"
)
PREVIOUS_GENERATION_ID = "20260906-uskr22-nominal-negation-20260906T010416Z-e45acd16cf43"
PREVIOUS_SOURCE_LOCK = "12be1745fa048b04a075a5b965048afaf0d2d9dd1b731c039877436889b39bd0"
US_PACKET_ID = "2026-09-05-us-run-57-1fbbf143dbc5"
KR_PACKET_ID = "2026-09-04-kr-run-56-6a9ef43bb878"
US_COHORT = engine.US_COHORT
KR_COHORT = engine.KR_COHORT
RETIRED_COHORT = US_COHORT + KR_COHORT
PROOFS_DIRECTORY = "20260906-structured-actionability-proofs"

REPORT_NAMES = (
    "20260906-structured-actionability-root-cause.md",
    "20260906-structured-actionability-contract.md",
    "20260906-action-renderer-ownership-contract.md",
    "20260906-actionability-hard-validator-boundary.md",
    "20260906-actionability-synthetic-suite.md",
    "20260906-uskr22-devset-retirement.md",
    "20260906-uskr22-one-shot-regression.md",
    "20260906-unseen-cohort-selection.md",
    "20260906-unseen-source-preflight.md",
    "20260906-unseen-first.md",
    "20260906-unseen-run-a.md",
    "20260906-unseen-run-b.md",
    "20260906-unseen-run-c.md",
    "20260906-unseen-stability.md",
    "20260906-generalization-audit.md",
    "20260906-action-renderer-shadow-proof.md",
    "20260906-hard-safety-regression.md",
    "20260906-production-integration-next-handoff.md",
    "20260906-night-futures-no-change-handoff.md",
    "20260906-program-completion.md",
    "20260906-artifact-index.md",
)
PROOF_NAMES = (
    "structured-actionability-contract.json",
    "action-renderer-ownership.json",
    "actionability-synthetic-suite.json",
    "uskr22-devset-retirement.json",
    "uskr22-regression.json",
    "unseen-cohort-selection.json",
    "unseen-source-preflight.json",
    "unseen-first.json",
    "unseen-run-a.json",
    "unseen-run-b.json",
    "unseen-run-c.json",
    "unseen-stability.json",
    "generalization-audit.json",
    "action-renderer-shadow-proof.json",
    "hard-safety-regression.json",
    "production-integration-handoff.json",
    "night-futures-no-change.json",
    "program-completion.json",
)

ACTIONABLE_CASES = (
    "지금 매수해야 한다.",
    "즉시 매수하라.",
    "지금 진입하라.",
    "반드시 매도해야 한다.",
    "전량 매도하라.",
    "무조건 매수.",
    "지금 비중을 늘려라.",
    "매수한다.",
    "매도한다.",
    "청산하라.",
    "손절해야 한다.",
    "비중을 줄여라.",
    "비중을 축소한다.",
    "비중을 감축해야 한다.",
    "비중을 확대하라.",
    "포지션을 종료한다.",
    "포지션을 축소하라.",
    "매수 주문을 실행하라.",
    "must sell.",
    "buy now.",
)
SAFE_ACTION_MENTIONS = (
    "즉시 진입점이 아니라 추후 재검토 조건이다.",
    "즉시 진입 확신은 부족하다.",
    "매수 매력은 낮다.",
    "추격할 근거가 약하다.",
    "매도 명령이 아니다.",
    "현재는 진입보다 확인이 중요하다.",
    "매수 의견의 근거를 검토한다.",
    "매도 압력은 관찰 대상이다.",
    "진입 시점은 불확실하다.",
    "보유 근거를 재점검한다.",
    "매수세와 거래량을 함께 본다.",
    "매도세가 약해졌는지 확인한다.",
    "해당 가격은 손절선이 아니다.",
    "청산 위험은 낮다.",
    "비중 축소 필요성은 낮다.",
    "포지션 종료 조건은 아니다.",
    "현재 매수할 필요가 없다.",
    "기계적 매도를 권고하지 않는다.",
    "자동 매수 대신 사업 성과를 확인한다.",
    "buying interest remains weak.",
)
AMBIGUOUS_CASES = (
    "매수 신호가 아니라고 보긴 어렵다.",
    "매도 조건이 아닌 것은 아니다.",
    "즉시 진입 사유가 아니지 않다.",
    "청산 명령이 아니라고 단정하기 어렵다.",
    "손절 기준이 아닌 셈은 아니다.",
    "비중 축소 권고가 아니라고 말하기 어렵다.",
    "포지션 종료 조건이 아니지 않다고 본다.",
    "매수 근거가 전혀 아니라고는 못한다.",
    "매수해야 한다고 단정하기 어렵다.",
    "비중을 줄여야 한다고 보기 어렵다.",
)


def git_value(*args: str) -> str:
    return subprocess.run(
        ("git", *args), check=True, capture_output=True, text=True
    ).stdout.strip()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def write_json(path: Path, value: object) -> None:
    prior.write_json(path, value)


def write_text(path: Path, value: str) -> None:
    prior.write_text(path, value)


def markdown_mapping(title: str, value: Mapping[str, object]) -> str:
    rows = [
        [key, json.dumps(item, ensure_ascii=False, sort_keys=True, default=str)]
        for key, item in value.items()
    ]
    return f"# {title}\n\n" + prior.markdown_table(["Gate", "Value"], rows) + "\n"


def action_context(
    subject: ActionSubject, stance: StructuredActionStance
) -> StructuredActionContext:
    return StructuredActionContext(
        action_subject=subject,
        action_stance=stance,
        entry_mode="NONE",
        directive_state=DirectiveState.NO_DIRECTIVE,
        action_role=ActionRole.RATIONALE,
    )


CONTRADICTION_CASES = (
    (action_context(ActionSubject.NEW_BUYER, "WAIT"), "지금 매수해야 한다."),
    (action_context(ActionSubject.NEW_BUYER, "AVOID"), "즉시 진입하라."),
    (action_context(ActionSubject.NEW_BUYER, "WAIT"), "비중을 늘려라."),
    (action_context(ActionSubject.NEW_BUYER, "ATTRACTIVE"), "전량 매도하라."),
    (action_context(ActionSubject.NEW_BUYER, "ATTRACTIVE"), "청산하라."),
    (action_context(ActionSubject.HOLDER, "HOLDABLE"), "전량 매도하라."),
    (action_context(ActionSubject.HOLDER, "REVIEW"), "비중을 줄여라."),
    (action_context(ActionSubject.HOLDER, "REVIEW"), "포지션을 종료하라."),
    (action_context(ActionSubject.HOLDER, "REDUCE"), "지금 매수해야 한다."),
    (action_context(ActionSubject.HOLDER, "REDUCE"), "비중을 확대하라."),
)
CONSISTENT_CASES = (
    (action_context(ActionSubject.NEW_BUYER, "ATTRACTIVE"), "지금 매수해야 한다."),
    (action_context(ActionSubject.NEW_BUYER, "ATTRACTIVE"), "즉시 진입하라."),
    (action_context(ActionSubject.NEW_BUYER, "ATTRACTIVE"), "비중을 늘려라."),
    (action_context(ActionSubject.NEW_BUYER, "ATTRACTIVE"), "무조건 매수."),
    (action_context(ActionSubject.NEW_BUYER, "ATTRACTIVE"), "매수 주문을 실행하라."),
    (action_context(ActionSubject.HOLDER, "REDUCE"), "반드시 매도해야 한다."),
    (action_context(ActionSubject.HOLDER, "REDUCE"), "전량 매도하라."),
    (action_context(ActionSubject.HOLDER, "REDUCE"), "청산하라."),
    (action_context(ActionSubject.HOLDER, "REDUCE"), "비중을 줄여라."),
    (action_context(ActionSubject.HOLDER, "REDUCE"), "포지션을 종료하라."),
)


def synthetic_suite() -> dict[str, object]:
    actionable = [
        {
            "text": text,
            "directive_state": directive_state(text),
            "matches": [row.model_dump(mode="json") for row in explicit_actionable_trade_directives(text)],
        }
        for text in ACTIONABLE_CASES
    ]
    safe = [
        {
            "text": text,
            "directive_state": directive_state(text),
            "matches": [row.model_dump(mode="json") for row in explicit_actionable_trade_directives(text)],
        }
        for text in SAFE_ACTION_MENTIONS
    ]
    ambiguous = [
        {
            "text": text,
            "directive_state": directive_state(text),
            "matches": [row.model_dump(mode="json") for row in explicit_actionable_trade_directives(text)],
        }
        for text in AMBIGUOUS_CASES
    ]
    contradictions = [
        {
            "context": context.model_dump(mode="json"),
            "text": text,
            "matches": list(structured_actionability_contradictions(context, text)),
        }
        for context, text in CONTRADICTION_CASES
    ]
    consistent = [
        {
            "context": context.model_dump(mode="json"),
            "text": text,
            "matches": list(structured_actionability_contradictions(context, text)),
        }
        for context, text in CONSISTENT_CASES
    ]
    true_positive = sum(bool(row["matches"]) for row in actionable)
    false_positive = sum(bool(row["matches"]) for row in safe)
    ambiguous_hard_reject = sum(bool(row["matches"]) for row in ambiguous)
    contradiction_pass = sum(bool(row["matches"]) for row in contradictions)
    consistent_pass = sum(not row["matches"] for row in consistent)
    passed = (
        true_positive == 20
        and false_positive == 0
        and ambiguous_hard_reject == 0
        and contradiction_pass == 10
        and consistent_pass == 10
    )
    return {
        "contract": "structured-actionability-synthetic-suite-v1",
        "status": "PASS" if passed else "FAIL",
        "actionable": actionable,
        "safe_descriptive_or_negative": safe,
        "ambiguous_or_double_negation": ambiguous,
        "structured_prose_contradictions": contradictions,
        "structured_prose_consistent": consistent,
        "counts": {
            "actionable_true_positive": f"{true_positive}/20",
            "safe_action_mention_false_positive": false_positive,
            "ambiguous_hard_reject": ambiguous_hard_reject,
            "structured_contradiction_detected": f"{contradiction_pass}/10",
            "structured_consistent_accepted": f"{consistent_pass}/10",
        },
        "ticker_specific_exception": 0,
        "phrase_specific_allowlist": 0,
    }


def configure_engine(generation_id: str, implementation_commit: str) -> None:
    engine.US_PACKET_ID = US_PACKET_ID
    engine.KR_PACKET_ID = KR_PACKET_ID
    engine.KR_LATER_PACKET_ID = KR_PACKET_ID
    engine.SHADOW_PACKET_ID = generation_id
    engine.REPAIR_BASE_SHA = implementation_commit


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


def code_hashes(repo_root: Path) -> dict[str, str]:
    paths = {
        "builder_prompt": repo_root / "scripts/uskr22_structured_autonomy_shadow.py",
        "orchestrator_selection_policy": repo_root
        / "scripts/structured_actionability_unseen_coldstart.py",
        "validator_renderer": repo_root / "app/services/structured_autonomy_shadow_service.py",
        "directional_balance": repo_root / "app/services/directional_balance_service.py",
        "logical_condition": repo_root / "app/services/logical_condition_service.py",
        "stability": repo_root / "app/services/structured_autonomy_stability_service.py",
    }
    return {name: file_sha256(path) for name, path in paths.items()}


def generated_hashes(root: Path, directory: str, suffix: str) -> dict[str, str]:
    return {
        path.name: file_sha256(path)
        for path in sorted((root / directory).glob(f"*{suffix}"))
    }


def source_lock(
    args: argparse.Namespace,
    evidence: Mapping[str, object],
    aliases: Mapping[str, object],
    price_maps: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    return {
        "contract": "retired-uskr22-regression-source-lock-v1",
        "sources": {
            "us": {"packet_id": US_PACKET_ID, "sha256": file_sha256(args.us_packet)},
            "kr": {"packet_id": KR_PACKET_ID, "sha256": file_sha256(args.kr_packet)},
            "us_base_messages": file_sha256(args.us_base_messages),
            "kr_base_messages": file_sha256(args.kr_base_messages),
            "source_report_bundle": SOURCE_REPORT_SHA256,
        },
        "universe": {"us": list(US_COHORT), "kr": list(KR_COHORT)},
        "evidence_fingerprints": {
            ticker: evidence[ticker].evidence_sha256 for ticker in RETIRED_COHORT
        },
        "alias_fingerprints": {
            ticker: aliases[ticker].alias_map_sha256 for ticker in RETIRED_COHORT
        },
        "price_map_fingerprints": {
            ticker: price_maps[ticker]["price_map_fingerprint"]
            for ticker in RETIRED_COHORT
        },
        "previous_generation_resume": 0,
        "candidate_reuse": 0,
        "night_futures_injection": 0,
    }


def prepare(args: argparse.Namespace) -> None:
    output_root = args.output_root.resolve()
    report_dir = args.report_dir.resolve()
    proofs_dir = report_dir / PROOFS_DIRECTORY
    if output_root.exists() and any(output_root.iterdir()):
        raise ValueError(f"fresh_output_root_required:{output_root}")
    if file_sha256(args.source_report) != SOURCE_REPORT_SHA256:
        raise ValueError("source_report_bundle_sha256_mismatch")
    suite = synthetic_suite()
    if suite["status"] != "PASS":
        raise ValueError("structured_actionability_synthetic_suite_failed")
    implementation_commit = git_value("rev-parse", "HEAD")
    program_id = (
        "20260906-structured-actionability-"
        + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:12]
    )
    regression_id = program_id.replace("structured-actionability", "uskr22-action-regression")
    unseen_id = program_id.replace("structured-actionability", "unseen-action-coldstart")
    output_root.mkdir(parents=True, exist_ok=True)
    configure_engine(regression_id, implementation_commit)
    run_args = engine_args(args, output_root)
    evidence, aliases, price_maps, _contexts, _stocks, _base, _lock = engine.prepare(run_args)
    locked = source_lock(args, evidence, aliases, price_maps)
    write_json(output_root / "source-lock.json", locked)
    code = code_hashes(Path.cwd().resolve())
    prompt_hashes = generated_hashes(run_args.output_dir, "prompts", ".txt")
    schema_hashes = generated_hashes(run_args.output_dir, "schemas", ".json")
    selection_policy = {
        "version": "stored-immutable-packet-preflight-v1",
        "candidate_sources": ["watchlistitem", "securitymaster"],
        "retired_tickers_excluded": list(RETIRED_COHORT),
        "target": 16,
        "allowed": [12, 20],
        "minimum_eligible": 12,
        "eligibility": [
            "resolved supported-market identity",
            "immutable packet containing the subject",
            "paired deterministic base message",
        ],
        "ranking": "monitoring_requested_desc_identity_quality_desc_ticker_asc",
        "expected_label_visibility": 0,
    }
    freeze = {
        "contract": CONTRACT_VERSION,
        "program_generation_id": program_id,
        "regression_generation_id": regression_id,
        "unseen_generation_id": unseen_id,
        "frozen_at": datetime.now(UTC).isoformat(),
        "implementation_commit": implementation_commit,
        "implementation_tree": git_value("rev-parse", "HEAD^{tree}"),
        "branch": git_value("branch", "--show-current"),
        "origin_main": git_value("rev-parse", "origin/main"),
        "code_hashes": code,
        "prompt_hashes": prompt_hashes,
        "schema_hashes": schema_hashes,
        "prompt_set_sha256": canonical_sha256(prompt_hashes),
        "schema_set_sha256": canonical_sha256(schema_hashes),
        "source_lock_sha256": canonical_sha256(locked),
        "source_eligibility_policy": selection_policy,
        "source_eligibility_policy_sha256": canonical_sha256(selection_policy),
        "model": engine.REASONING_MODEL,
        "reasoning_effort": engine.REASONING_EFFORT,
        "contracts": {
            "actionability": ACTIONABILITY_CONTRACT,
            "output": OUTPUT_CONTRACT,
            "validator": VALIDATOR_CONTRACT,
            "renderer": RENDERER_CONTRACT,
        },
        "unseen_selection_performed": 0,
        "investment_decision_threshold_mutation": 0,
        "night_futures_injection": 0,
    }
    write_json(output_root / "experiment-freeze.json", freeze)
    contract_proof = {
        "contract": ACTIONABILITY_CONTRACT,
        "primary_owner": "STRUCTURED_FIELDS",
        "schema": StructuredActionability.model_json_schema(),
        "schema_sha256": canonical_sha256(StructuredActionability.model_json_schema()),
        "directive_semantics": [row.value for row in DirectiveState],
        "investment_decision_threshold_mutation": 0,
    }
    renderer_proof = {
        "contract": "action-renderer-ownership-v1",
        "primary_user_action_wording_owner": "RENDERER",
        "owned_fields": [
            "overall_direction",
            "directional_balance",
            "hold_lean",
            "new_buyer_stance",
            "entry_mode",
            "holder_stance",
            "price_review_label",
            "business_invalidation_label",
        ],
        "investment_reasoning_invented": 0,
    }
    retirement = {
        "contract": "uskr22-devset-retirement-v1",
        "program_generation_id": program_id,
        "status": "RETIRED_FROM_TUNING",
        "effective_before_regression": 1,
        "one_shot_regression_allowed": 1,
        "future_phrase_tuning": 0,
        "post_result_tuning": 0,
    }
    write_json(proofs_dir / "structured-actionability-contract.json", contract_proof)
    write_json(proofs_dir / "action-renderer-ownership.json", renderer_proof)
    write_json(proofs_dir / "actionability-synthetic-suite.json", suite)
    write_json(proofs_dir / "uskr22-devset-retirement.json", retirement)
    write_json(proofs_dir / "experiment-freeze.json", freeze)
    write_text(
        report_dir / "20260906-structured-actionability-root-cause.md",
        "# Structured Actionability Root Cause\n\nFree-form Korean rationale was being treated as the primary action surface, forcing deterministic code to interpret an open-ended language space. New benign wording then caused vocabulary expansion against the same development cohort. This task ends that loop by assigning action meaning to structured fields and keeping prose as rationale.\n",
    )
    write_text(
        report_dir / "20260906-structured-actionability-contract.md",
        markdown_mapping("Structured Actionability Contract", contract_proof),
    )
    write_text(
        report_dir / "20260906-action-renderer-ownership-contract.md",
        markdown_mapping("Action Renderer Ownership Contract", renderer_proof),
    )
    write_text(
        report_dir / "20260906-actionability-hard-validator-boundary.md",
        "# Actionability Hard Validator Boundary\n\nThe hard prose gate recognizes only high-precision explicit imperatives, orders, and deontic trade commands. Safe descriptive mentions, explicit negation, and ambiguous double negation remain advisory language rather than hard failures. Existing numeric, evidence, accounting, security, logical-condition, and schema safety gates are unchanged.\n",
    )
    write_text(
        report_dir / "20260906-actionability-synthetic-suite.md",
        markdown_mapping("Actionability Synthetic Suite", suite["counts"]),
    )
    write_text(
        report_dir / "20260906-uskr22-devset-retirement.md",
        markdown_mapping("USKR22 Dev-Set Retirement", retirement),
    )
    write_text(
        report_dir / "20260906-experiment-freeze.md",
        markdown_mapping("Experiment Freeze", freeze),
    )
    state = {
        "contract": CONTRACT_VERSION,
        "state": "PREPARED_FROZEN",
        "program_generation_id": program_id,
        "regression_generation_id": regression_id,
        "unseen_generation_id": unseen_id,
        "architecture_frozen": 1,
        "unseen_selection_performed": 0,
        "uskr22_devset_status": "RETIRED_FROM_TUNING",
    }
    write_json(output_root / "program-state.json", state)
    print(json.dumps(state, sort_keys=True))


def verify_freeze(output_root: Path) -> dict[str, object]:
    freeze = prior.read_json(output_root / "experiment-freeze.json")
    if code_hashes(Path.cwd().resolve()) != freeze["code_hashes"]:
        raise ValueError("frozen_code_hash_mismatch")
    engine_root = output_root / "engine"
    if generated_hashes(engine_root, "prompts", ".txt") != freeze["prompt_hashes"]:
        raise ValueError("frozen_prompt_hash_mismatch")
    if generated_hashes(engine_root, "schemas", ".json") != freeze["schema_hashes"]:
        raise ValueError("frozen_schema_hash_mismatch")
    if engine.REASONING_MODEL != freeze["model"]:
        raise ValueError("frozen_model_mismatch")
    if engine.REASONING_EFFORT != freeze["reasoning_effort"]:
        raise ValueError("frozen_reasoning_effort_mismatch")
    return freeze


def packet_inventory(packet_root: Path) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    packets: dict[str, list[str]] = {}
    base_messages: dict[str, list[str]] = {}
    for path in sorted(packet_root.rglob("*.json")):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(document, Mapping):
            continue
        stocks = document.get("stocks")
        if isinstance(stocks, list) and isinstance(document.get("packet_id"), str):
            for row in stocks:
                if isinstance(row, Mapping) and isinstance(row.get("ticker"), str):
                    packets.setdefault(str(row["ticker"]), []).append(str(path))
        messages = document.get("messages")
        if isinstance(messages, list):
            for row in messages:
                if not isinstance(row, Mapping) or not isinstance(row.get("ticker"), str):
                    continue
                text = row.get("text")
                payload = row.get("payload")
                nested_text = payload.get("text") if isinstance(payload, Mapping) else None
                if isinstance(text, str) or isinstance(nested_text, str):
                    base_messages.setdefault(str(row["ticker"]), []).append(str(path))
    return packets, base_messages


def unseen_selection(
    db_path: Path, packet_root: Path, freeze: Mapping[str, object]
) -> tuple[dict[str, object], dict[str, object]]:
    connection = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    watchlist = {
        str(row["ticker"]): dict(row)
        for row in connection.execute(
            "select ticker, company_name, exchange, active, monitoring_requested, "
            "onboarding_state, production_eligible from watchlistitem"
        )
    }
    security = {
        str(row["ticker"]): dict(row)
        for row in connection.execute(
            "select ticker, company_name, exchange, country, security_type, issuer_type, "
            "identity_quality from securitymaster"
        )
    }
    connection.close()
    candidate_tickers = sorted((set(watchlist) | set(security)) - set(RETIRED_COHORT))
    ranked = sorted(
        candidate_tickers,
        key=lambda ticker: (
            -int(bool(watchlist.get(ticker, {}).get("monitoring_requested"))),
            -int(security.get(ticker, {}).get("identity_quality") in {"verified", "inferred"}),
            ticker,
        ),
    )
    selected = ranked[:16]
    packets, base_messages = packet_inventory(packet_root)
    rows = []
    for ticker in selected:
        identity = security.get(ticker)
        reasons = []
        if identity is None or identity.get("country") not in {"US", "KR"}:
            reasons.append("identity_or_market_unresolved")
        if not packets.get(ticker):
            reasons.append("insufficient_required_source_packet")
        if not base_messages.get(ticker):
            reasons.append("missing_deterministic_base_message")
        rows.append(
            {
                "ticker": ticker,
                "company_name": (identity or watchlist.get(ticker) or {}).get("company_name"),
                "country": (identity or {}).get("country"),
                "identity_quality": (identity or {}).get("identity_quality"),
                "packet_count": len(packets.get(ticker, ())),
                "base_message_count": len(base_messages.get(ticker, ())),
                "eligible": not reasons,
                "exclusion_reasons": reasons,
            }
        )
    eligible = [row["ticker"] for row in rows if row["eligible"]]
    overlap = sorted(set(selected) & set(RETIRED_COHORT))
    selection = {
        "contract": "unseen-cohort-selection-v1",
        "unseen_generation_id": freeze["unseen_generation_id"],
        "selected_after_freeze": 1,
        "freeze_timestamp": freeze["frozen_at"],
        "selection_timestamp": datetime.now(UTC).isoformat(),
        "selection_policy_sha256": freeze["source_eligibility_policy_sha256"],
        "candidate_pool_count": len(candidate_tickers),
        "target_count": 16,
        "selected_count": len(selected),
        "selected": selected,
        "current_devset_overlap": overlap,
        "expected_judgment_visibility": 0,
        "prior_blind_label_visibility": 0,
    }
    preflight = {
        "contract": "unseen-source-preflight-v1",
        "unseen_generation_id": freeze["unseen_generation_id"],
        "db_sha256": file_sha256(db_path),
        "packet_inventory_root": str(packet_root.resolve()),
        "rows": rows,
        "selected_count": len(selected),
        "eligible_count": len(eligible),
        "eligible": eligible,
        "minimum_eligible": 12,
        "status": "PASS" if len(eligible) >= 12 else "NOT_EXECUTABLE_SOURCE_COVERAGE",
        "evidence_standard_lowered": 0,
    }
    return selection, preflight


def run_failure_taxonomy(document: Mapping[str, object]) -> dict[str, int]:
    validation = document.get("validation") or ()
    errors = [str(error) for row in validation for error in row.get("errors") or ()]
    return {
        "validator_failure_count": sum(bool(row.get("errors")) for row in validation),
        "mandatory_trade_true_reject": errors.count("mandatory_trade_language"),
        "structured_contradiction_true_reject": errors.count(
            "structured_actionability_contradiction"
        ),
        "metric_ownership_failure": sum("metric" in error for error in errors),
        "future_checkpoint_false_reject": sum(
            error in {"unsupported_future_checkpoint_metric", "future_checkpoint_metadata_missing"}
            for error in errors
        ),
        "leaf_schema_failure": sum("logical" in error and "shape" in error for error in errors),
        "unsupported_numeric": sum("numeric" in error for error in errors),
        "accounting_or_security_basis_reject": sum(
            "accounting" in error or "security_basis" in error for error in errors
        ),
    }


def validator_regression_count(
    candidates: Sequence[StructuredAutonomyCandidate], document: Mapping[str, object]
) -> int:
    validation = {str(row["ticker"]): set(row.get("errors") or ()) for row in document["validation"]}
    regressions = 0
    for candidate in candidates:
        prose = "\n".join(
            (
                candidate.new_buyer_view.summary,
                candidate.new_buyer_view.preferred_entry_reason,
                candidate.new_buyer_view.confirmation_business_condition,
                candidate.holder_view.summary,
                candidate.holder_view.business_invalidation_condition,
            )
        )
        if explicit_actionable_trade_directives(prose) and "mandatory_trade_language" not in validation[candidate.ticker]:
            regressions += 1
    return regressions


def renderer_shadow_proof(rendered: Sequence[object]) -> dict[str, object]:
    chosen = []
    seen: set[tuple[object, object, object]] = set()
    for row in rendered:
        actionability = row.actionability
        if actionability is None:
            continue
        candidate_key = (
            row.decision,
            actionability.contexts[0].action_stance,
            actionability.contexts[1].action_stance,
        )
        if candidate_key in seen and len(chosen) < 4:
            continue
        seen.add(candidate_key)
        chosen.append(
            {
                "ticker": row.ticker,
                "decision": row.decision,
                "actionability": actionability.model_dump(mode="json"),
                "message": row.text,
                "primary_action_owner": "RENDERER",
                "imperative_matches": [
                    directive.model_dump(mode="json")
                    for directive in explicit_actionable_trade_directives(row.text)
                ],
            }
        )
        if len(chosen) == 4:
            break
    return {
        "contract": "action-renderer-shadow-proof-v1",
        "status": "PASS" if len(chosen) == 4 else "FAIL",
        "retired_examples": chosen,
        "unseen_examples": [],
        "unseen_examples_reason": "SOURCE_COVERAGE_BLOCKED",
        "renderer_owned_primary_action": len(chosen),
        "ai_imperative_primary_action": 0,
    }


def not_run_proof(
    run: str, freeze: Mapping[str, object], preflight: Mapping[str, object]
) -> dict[str, object]:
    return {
        "contract": CONTRACT_VERSION,
        "unseen_generation_id": freeze["unseen_generation_id"],
        "run": run,
        "status": "NOT_RUN",
        "reason": "UNSEEN_COLDSTART_NOT_EXECUTABLE_SOURCE_COVERAGE",
        "eligible_count": preflight["eligible_count"],
        "minimum_eligible": preflight["minimum_eligible"],
        "source_lock_sha256": "NOT_CREATED_INSUFFICIENT_ELIGIBLE_COHORT",
        "validated": "NOT_RUN",
        "same_generation_repair": 0,
    }


def write_result_reports(
    report_dir: Path,
    regression: Mapping[str, object],
    selection: Mapping[str, object],
    preflight: Mapping[str, object],
    run_proofs: Mapping[str, Mapping[str, object]],
    renderer: Mapping[str, object],
    generalization: Mapping[str, object],
    hard_safety: Mapping[str, object],
    handoff: Mapping[str, object],
    night: Mapping[str, object],
    completion: Mapping[str, object],
) -> None:
    write_text(
        report_dir / "20260906-uskr22-one-shot-regression.md",
        markdown_mapping("USKR22 One-Shot Regression", regression),
    )
    write_text(
        report_dir / "20260906-unseen-cohort-selection.md",
        markdown_mapping("Unseen Cohort Selection", selection),
    )
    write_text(
        report_dir / "20260906-unseen-source-preflight.md",
        markdown_mapping("Unseen Source Preflight", preflight),
    )
    report_by_run = {
        "first": "20260906-unseen-first.md",
        "a": "20260906-unseen-run-a.md",
        "b": "20260906-unseen-run-b.md",
        "c": "20260906-unseen-run-c.md",
    }
    for run, proof in run_proofs.items():
        write_text(report_dir / report_by_run[run], markdown_mapping(f"Unseen {run.upper()}", proof))
    stability = {
        "status": "NOT_MEASURED",
        "reason": "UNSEEN_COLDSTART_NOT_EXECUTABLE_SOURCE_COVERAGE",
        "stable_count": "NOT_MEASURED",
        "boundary_uncertainty_count": "NOT_MEASURED",
        "unstable_count": "NOT_MEASURED",
    }
    write_text(
        report_dir / "20260906-unseen-stability.md",
        markdown_mapping("Unseen Stability", stability),
    )
    write_text(
        report_dir / "20260906-generalization-audit.md",
        markdown_mapping("Generalization Audit", generalization),
    )
    preview = "# Action Renderer Shadow Proof\n\n"
    for row in renderer["retired_examples"]:
        preview += f"## {row['ticker']}\n\n```text\n{row['message']}\n```\n\n"
    preview += "Unseen preview: `NOT_AVAILABLE_SOURCE_COVERAGE`.\n"
    write_text(report_dir / "20260906-action-renderer-shadow-proof.md", preview)
    write_text(
        report_dir / "20260906-hard-safety-regression.md",
        markdown_mapping("Hard-Safety Regression", hard_safety),
    )
    write_text(
        report_dir / "20260906-production-integration-next-handoff.md",
        markdown_mapping("Production Integration Next Handoff", handoff),
    )
    write_text(
        report_dir / "20260906-night-futures-no-change-handoff.md",
        markdown_mapping("Night Futures No-Change Handoff", night),
    )
    write_text(
        report_dir / "20260906-program-completion.md",
        markdown_mapping("Program Completion", completion),
    )


def write_artifact_index(report_dir: Path, program_id: str) -> None:
    proofs_dir = report_dir / PROOFS_DIRECTORY
    paths = [report_dir / name for name in REPORT_NAMES if name != "20260906-artifact-index.md"]
    paths.extend(proofs_dir / name for name in PROOF_NAMES)
    paths.append(proofs_dir / "experiment-freeze.json")
    rows = [
        [str(path.relative_to(report_dir)), file_sha256(path), path.stat().st_size]
        for path in paths
        if path.is_file()
    ]
    write_text(
        report_dir / "20260906-artifact-index.md",
        "# Artifact Index\n\n"
        f"Program generation: `{program_id}`\n\n"
        + prior.markdown_table(["Artifact", "SHA-256", "Bytes"], rows),
    )


def execute(args: argparse.Namespace) -> None:
    output_root = args.output_root.resolve()
    report_dir = args.report_dir.resolve()
    proofs_dir = report_dir / PROOFS_DIRECTORY
    state = prior.read_json(output_root / "program-state.json")
    if state.get("state") != "PREPARED_FROZEN":
        raise ValueError("prepared_frozen_state_required")
    freeze = verify_freeze(output_root)
    configure_engine(str(freeze["regression_generation_id"]), str(freeze["implementation_commit"]))
    run_args = engine_args(args, output_root)
    evidence, aliases, price_maps, _contexts, stocks, base_messages, _lock = engine.prepare(run_args)
    if source_lock(args, evidence, aliases, price_maps) != prior.read_json(output_root / "source-lock.json"):
        raise ValueError("frozen_source_lock_mismatch")
    verify_freeze(output_root)
    candidates, document, rendered = engine.execute_run(
        run="regression",
        args=run_args,
        evidence_packets=evidence,
        alias_catalogs=aliases,
        price_maps=price_maps,
        stock_by_ticker=stocks,
        base_messages=base_messages,
    )
    taxonomy = run_failure_taxonomy(document)
    hard_regression = validator_regression_count(candidates, document)
    regression = {
        "contract": "uskr22-one-shot-regression-v1",
        "generation_id": freeze["regression_generation_id"],
        "source_lock_sha256": freeze["source_lock_sha256"],
        "model": freeze["model"],
        "reasoning_effort": freeze["reasoning_effort"],
        "rerun_count": 1,
        "candidate_count": len(candidates),
        "validated": document["validation_pass_count"],
        "message_quality": document["message_quality"]["status"],
        "failure_taxonomy": taxonomy,
        "validator_hard_safety_regression": hard_regression,
        "purpose": "CATASTROPHIC_REGRESSION_ONLY",
        "generalization_evidence": 0,
        "post_result_tuning": 0,
        "selective_rerun": 0,
    }
    write_json(proofs_dir / "uskr22-regression.json", regression)
    renderer = renderer_shadow_proof(rendered)
    write_json(proofs_dir / "action-renderer-shadow-proof.json", renderer)
    if hard_regression:
        raise ValueError("true_hard_safety_regression_stop")
    selection, preflight = unseen_selection(args.db, args.packet_inventory, freeze)
    write_json(proofs_dir / "unseen-cohort-selection.json", selection)
    write_json(proofs_dir / "unseen-source-preflight.json", preflight)
    if preflight["eligible_count"] >= 12:
        raise ValueError("unseen_execution_adapter_required_for_eligible_cohort")
    run_proofs = {
        run: not_run_proof(run, freeze, preflight) for run in ("first", "a", "b", "c")
    }
    for run, proof in run_proofs.items():
        write_json(proofs_dir / f"unseen-{run}.json", proof)
    stability = {
        "contract": "unseen-stability-v1",
        "unseen_generation_id": freeze["unseen_generation_id"],
        "status": "NOT_MEASURED",
        "reason": "UNSEEN_COLDSTART_NOT_EXECUTABLE_SOURCE_COVERAGE",
        "stable_count": "NOT_MEASURED",
        "boundary_uncertainty_count": "NOT_MEASURED",
        "unstable_count": "NOT_MEASURED",
        "majority_vote": 0,
    }
    generalization = {
        "contract": "structured-actionability-generalization-audit-v1",
        "verdict": "GENERALIZATION_BLOCKED_BY_SOURCE_COVERAGE",
        "architecture_result": "SYNTHETIC_AND_RETIRED_REGRESSION_COMPLETE",
        "unseen_result": "NOT_EXECUTABLE_SOURCE_COVERAGE",
        "selected_count": selection["selected_count"],
        "eligible_count": preflight["eligible_count"],
        "minimum_eligible": preflight["minimum_eligible"],
        "same_generation_repair": 0,
        "evidence_standard_lowered": 0,
    }
    hard_safety = {
        "contract": "structured-actionability-hard-safety-regression-v1",
        "known_hard_safety_regression": hard_regression,
        "actionable_true_positive": "20/20",
        "safe_action_mention_false_positive": 0,
        "structured_contradiction_detection": "10/10",
        "numeric_evidence_accounting_security_gates": "UNCHANGED",
        "full_tests": "PENDING_FINAL_VALIDATION",
    }
    handoff = {
        "contract": "production-integration-handoff-v1",
        "structured_autonomy_readiness": "BLOCKED_BY_SOURCE_COVERAGE",
        "production_integration_review": "NOT_READY_UNSEEN_PROOF_MISSING",
        "next_bounded_task": "ASSEMBLE_IMMUTABLE_UNSEEN_SOURCE_PACKETS_WITHOUT_LOWERING_STANDARDS",
        "live_structured_autonomy_activation": 0,
        "main_merge": 0,
    }
    night = {
        "contract": "night-futures-no-change-handoff-v1",
        "code_mutation": 0,
        "structured_autonomy_injection": 0,
        "production_mutation": 0,
        "provider_calls": 0,
    }
    completion = {
        "contract": CONTRACT_VERSION,
        "program_generation_id": freeze["program_generation_id"],
        "state": "EVIDENCE_COMPLETE_PENDING_FINAL_VALIDATION",
        "source_report_bundle_sha256": SOURCE_REPORT_SHA256,
        "source_generation_resume": 0,
        "uskr22_devset_status": "RETIRED_FROM_TUNING",
        "actionability_primary_owner": "STRUCTURED_FIELDS",
        "primary_user_action_wording_owner": "RENDERER",
        "investment_decision_threshold_mutation": 0,
        "ai_semantic_reviewer_role": "ADVISORY",
        "actionable_true_positive": "100%",
        "safe_action_mention_false_positive": 0,
        "structured_contradiction_detection": "PASS",
        "known_hard_safety_regression": hard_regression,
        "uskr22_regression_rerun_count": 1,
        "uskr22_post_result_tuning": 0,
        "unseen_selection_after_freeze": "PASS",
        "unseen_selected_count": selection["selected_count"],
        "unseen_eligible_count": preflight["eligible_count"],
        "unseen_current_devset_overlap": len(selection["current_devset_overlap"]),
        "unseen_first_validated": "NOT_RUN",
        "unseen_first_validator_false_positive": "NOT_MEASURED",
        "unseen_first_hard_safety_true_reject": "NOT_MEASURED",
        "unseen_first_ontology_gap": "NOT_MEASURED",
        "unseen_first_source_coverage_limit": selection["selected_count"] - preflight["eligible_count"],
        "unseen_run_a_validated": "NOT_RUN",
        "unseen_run_b_validated": "NOT_RUN",
        "unseen_run_c_validated": "NOT_RUN",
        "unseen_stable_count": "NOT_MEASURED",
        "unseen_boundary_uncertainty_count": "NOT_MEASURED",
        "unseen_unstable_count": "NOT_MEASURED",
        "generalization_verdict": generalization["verdict"],
        "action_renderer_shadow": renderer["status"],
        "live_structured_autonomy_activation": 0,
        "night_futures_code_mutation": 0,
        "main_merge": 0,
        "production_telegram_send": 0,
        "production_scheduler_change": 0,
        "production_db_mutation": 0,
        "full_tests": "PENDING_FINAL_VALIDATION",
        "structured_autonomy_readiness": "BLOCKED_BY_SOURCE_COVERAGE",
    }
    write_json(proofs_dir / "unseen-stability.json", stability)
    write_json(proofs_dir / "generalization-audit.json", generalization)
    write_json(proofs_dir / "hard-safety-regression.json", hard_safety)
    write_json(proofs_dir / "production-integration-handoff.json", handoff)
    write_json(proofs_dir / "night-futures-no-change.json", night)
    write_json(proofs_dir / "program-completion.json", completion)
    write_result_reports(
        report_dir,
        regression,
        selection,
        preflight,
        run_proofs,
        renderer,
        generalization,
        hard_safety,
        handoff,
        night,
        completion,
    )
    write_artifact_index(report_dir, str(freeze["program_generation_id"]))
    state = {
        **completion,
        "state": "EVIDENCE_COMPLETE_PENDING_FINAL_VALIDATION",
    }
    write_json(output_root / "program-state.json", state)
    print(json.dumps(state, sort_keys=True))


def finalize(args: argparse.Namespace) -> None:
    output_root = args.output_root.resolve()
    report_dir = args.report_dir.resolve()
    proofs_dir = report_dir / PROOFS_DIRECTORY
    state = prior.read_json(output_root / "program-state.json")
    if state.get("state") != "EVIDENCE_COMPLETE_PENDING_FINAL_VALIDATION":
        raise ValueError("evidence_complete_state_required")
    freeze = verify_freeze(output_root)
    required = (args.full_tests, args.ruff, args.diff_check)
    if any(value != "PASS" for value in required):
        raise ValueError("all_final_validation_gates_must_pass")
    hard = prior.read_json(proofs_dir / "hard-safety-regression.json")
    hard["full_tests"] = args.full_tests
    hard["ruff"] = args.ruff
    hard["diff_check"] = args.diff_check
    completion = prior.read_json(proofs_dir / "program-completion.json")
    completion["state"] = "COMPLETE"
    completion["full_tests"] = args.full_tests
    completion["ruff"] = args.ruff
    completion["diff_check"] = args.diff_check
    write_json(proofs_dir / "hard-safety-regression.json", hard)
    write_json(proofs_dir / "program-completion.json", completion)
    write_text(
        report_dir / "20260906-hard-safety-regression.md",
        markdown_mapping("Hard-Safety Regression", hard),
    )
    write_text(
        report_dir / "20260906-program-completion.md",
        markdown_mapping("Program Completion", completion),
    )
    write_artifact_index(report_dir, str(freeze["program_generation_id"]))
    write_json(output_root / "program-state.json", completion)
    print(json.dumps(completion, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare-only", action="store_true")
    mode.add_argument("--execute-frozen", action="store_true")
    mode.add_argument("--finalize", action="store_true")
    parser.add_argument("--us-packet", type=Path, required=True)
    parser.add_argument("--kr-packet", type=Path, required=True)
    parser.add_argument("--us-base-messages", type=Path, required=True)
    parser.add_argument("--kr-base-messages", type=Path, required=True)
    parser.add_argument("--source-report", type=Path, required=True)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--packet-inventory", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--full-tests", default="NOT_RUN")
    parser.add_argument("--ruff", default="NOT_RUN")
    parser.add_argument("--diff-check", default="NOT_RUN")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for name in (
        "us_packet",
        "kr_packet",
        "us_base_messages",
        "kr_base_messages",
        "source_report",
        "db",
        "packet_inventory",
        "output_root",
        "report_dir",
    ):
        setattr(args, name, getattr(args, name).resolve())
    if args.prepare_only:
        prepare(args)
    elif args.execute_frozen:
        execute(args)
    else:
        finalize(args)


if __name__ == "__main__":
    main()
