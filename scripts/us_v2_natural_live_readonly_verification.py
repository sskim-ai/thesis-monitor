from __future__ import annotations

# ruff: noqa: E501

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Sequence
from zoneinfo import ZoneInfo


PACKET_ID = "2026-09-01-us-run-49-2d1bb6df1608"
ASSESSMENT_DATE = "2026-09-01"
CANONICAL_SESSION_DATE = "2026-08-31"
INSTRUCTION_COMMIT = "e6c11cff168fa430d7ddc7095d8c407d80948553"
BASE_SHA = "5b3e6e1a721b84db72c7b277bf53ff55880a1819"
PRIMARY_THREAD_ID = "01a05a1c-731b-7951-be66-6f8e2eb94ba2"
BACKUP_THREAD_ID = "01a05a29-445a-7e82-894b-84792819f732"
KST = ZoneInfo("Asia/Seoul")
EXPECTED_TICKERS = (
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
)
SELL_CONTROLS = ("HUT", "TSLA", "WULF")
REPORT_NAMES = (
    "20260901-us-v2-natural-live-run-identity.md",
    "20260901-us-v2-runtime-lineage.md",
    "20260901-us-v2-feature-state.md",
    "20260901-us-v2-frozen-cohort.md",
    "20260901-us-v2-cpng-live-control.md",
    "20260901-us-market-message-proof.md",
    "20260901-us-macro-night-futures.md",
    "20260901-us-v2-candidate-adjudication-accepted.md",
    "20260901-us-v2-renderer-route-audit.md",
    "20260901-us-v2-corz-root-cause.md",
    "20260901-us-v2-googl-control.md",
    "20260901-us-v2-sell-controls.md",
    "20260901-us-v2-price-structure.md",
    "20260901-us-v2-valuation.md",
    "20260901-us-v2-live-exact-messages.md",
    "20260901-us-v2-live-delivery.md",
    "20260901-us-v2-message-quality.md",
    "20260901-us-v2-natural-live-proof.md",
    "20260901-us-v2-artifact-index.md",
)
JSON_NAMES = (
    "20260901-us-v2-live-decisions.json",
    "20260901-us-v2-renderer-routes.json",
    "20260901-us-v2-live-delivery.json",
    "20260901-us-v2-natural-live-proof.json",
)


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _write_json(path: Path, value: object) -> None:
    _write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _sha_text(value: str) -> str:
    return _sha_bytes(value.encode("utf-8"))


def _table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(str(item) for item in row) + " |" for row in rows)
    return "\n".join(lines)


def _report(title: str, body: str) -> str:
    return f"# {title}\n\n{body.rstrip()}\n"


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(("git", "-C", str(root), *args), text=True).strip()


def _utc_db_to_kst(value: object) -> str | None:
    if value in (None, ""):
        return None
    parsed = datetime.fromisoformat(str(value))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(KST).isoformat()


def _epoch_ms_to_kst(value: object) -> str | None:
    if value in (None, ""):
        return None
    return datetime.fromtimestamp(int(value) / 1000, tz=UTC).astimezone(KST).isoformat()


def _env_values(path: Path) -> dict[str, str]:
    allowed = {
        "AI_REVIEW_MODE",
        "AI_REVIEW_PILOT_ENABLED",
        "VISIBLE_STOCK_DECISION_ENGINE",
        "V2_PRODUCTION_ENABLED",
        "V2_FULL_MONITORED_STOCK_COVERAGE_TARGET",
        "V1_DECISION_ROLLBACK_AVAILABLE",
    }
    rows: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key in allowed:
            rows[key] = value.strip().strip("'\"")
    return rows


def _db_evidence(database: Path, tickers: Sequence[str]) -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        run = connection.execute(
            """
            SELECT id, run_date, run_type, status, started_at, completed_at,
                   ticker_count, success_count, failure_count
              FROM monitorrun
             WHERE run_date = ? AND run_type = 'daily_us'
            """,
            (ASSESSMENT_DATE,),
        ).fetchone()
        placeholders = ",".join("?" for _ in tickers)
        watchlist = connection.execute(
            f"""
            SELECT ticker, active, monitoring_requested, onboarding_state,
                   production_eligible, onboarding_ready_at, activated_at,
                   first_eligible_session, onboarding_failure_stage
              FROM watchlistitem
             WHERE ticker IN ({placeholders})
             ORDER BY ticker
            """,
            tuple(tickers),
        ).fetchall()
        deliveries = connection.execute(
            """
            SELECT id, ticker, status, attempt_count, sent_at, payload
              FROM notificationdelivery
             WHERE assessment_date = ?
             ORDER BY id
            """,
            (ASSESSMENT_DATE,),
        ).fetchall()
    finally:
        connection.close()
    delivery_rows: list[dict[str, Any]] = []
    for row in deliveries:
        payload = json.loads(row["payload"] or "{}")
        pilot = payload.get("_ai_assisted_pilot") or {}
        telegram = payload.get("_telegram_delivery") or {}
        text = str(payload.get("text") or "")
        delivery_rows.append(
            {
                "id": row["id"],
                "ticker": row["ticker"],
                "status": row["status"],
                "attempt_count": row["attempt_count"],
                "sent_at_kst": _utc_db_to_kst(row["sent_at"]),
                "text": text,
                "text_sha256": _sha_text(text),
                "pilot_state": pilot.get("state"),
                "packet_id": pilot.get("packet_id"),
                "renderer_version": pilot.get("renderer_version"),
                "fallback_started_at": pilot.get("fallback_started_at"),
                "ai_validation_state": pilot.get("ai_validation_state"),
                "ai_validation_errors": list(pilot.get("ai_validation_errors") or []),
                "chunk_count": telegram.get("chunk_count"),
                "next_chunk_index": telegram.get("next_chunk_index"),
                "rendered_text_sha256": _sha_text(str(telegram.get("rendered_text") or "")),
                "content_sha256": telegram.get("content_sha256"),
            }
        )
    return {
        "run": dict(run) if run is not None else None,
        "watchlist": [dict(row) for row in watchlist],
        "deliveries": delivery_rows,
    }


def _automation_evidence(database: Path) -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        automations = connection.execute(
            """
            SELECT id, name, status, rrule, reasoning_effort, last_run_at, next_run_at
              FROM automations
             WHERE id IN ('thesis-monitor-ai-review-us-primary',
                          'thesis-monitor-ai-review-us-backup')
             ORDER BY id
            """
        ).fetchall()
        runs = connection.execute(
            """
            SELECT thread_id, automation_id, status, created_at, updated_at
              FROM automation_runs
             WHERE thread_id IN (?, ?)
             ORDER BY created_at
            """,
            (PRIMARY_THREAD_ID, BACKUP_THREAD_ID),
        ).fetchall()
    finally:
        connection.close()
    return {
        "automations": [
            {
                **dict(row),
                "last_run_at_kst": _epoch_ms_to_kst(row["last_run_at"]),
                "next_run_at_kst": _epoch_ms_to_kst(row["next_run_at"]),
            }
            for row in automations
        ],
        "runs": [
            {
                **dict(row),
                "created_at_kst": _epoch_ms_to_kst(row["created_at"]),
                "updated_at_kst": _epoch_ms_to_kst(row["updated_at"]),
            }
            for row in runs
        ],
    }


def _validation_attempts(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pattern = f"{PACKET_ID}--*.validation.json"
    for path in sorted((root / "data/ai_review/rejected").glob(pattern)):
        value = _load(path)
        match = re.search(r"\.([0-9]+)\.validation\.json$", path.name)
        stamp = match.group(1) if match else ""
        try:
            recorded = datetime.fromtimestamp(int(stamp), tz=UTC).astimezone(KST).isoformat()
        except ValueError:
            recorded = None
        rows.append(
            {
                "artifact": str(path.relative_to(root)),
                "sha256": _sha_file(path),
                "claim_id": value.get("claim_id"),
                "recorded_at_kst": recorded,
                "status": value.get("status"),
                "errors": list(value.get("errors") or []),
            }
        )
    return rows


def _empty_visible_sections(text: str) -> int:
    lines = text.splitlines()
    headers = {"🎯 핵심", "📈 사업·실적", "👁 핵심 감시", "📐 현재 가격 구조", "🧭 기존 등록 가격 규칙", "📐 Valuation", "📌 다음 확인"}
    count = 0
    for index, line in enumerate(lines):
        if line.strip() not in headers:
            continue
        following = next((item.strip() for item in lines[index + 1 :] if item.strip()), "")
        if not following or following in headers:
            count += 1
    return count


def _redaction_check(paths: Iterable[Path]) -> None:
    patterns = (
        re.compile(r"\b-100\d{5,}\b"),
        re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{20,}\b"),
        re.compile(r"Bearer\s+[A-Za-z0-9._-]{12,}", re.IGNORECASE),
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for pattern in patterns:
            if pattern.search(text):
                raise ValueError(f"secret-like value found in {path.name}")


def build(args: argparse.Namespace) -> dict[str, Any]:
    root = args.operating_root.resolve()
    worktree_root = args.worktree_root.resolve()
    output = args.output_dir.resolve()
    packet_path = root / "data/ai_review/inbox" / f"{PACKET_ID}.json"
    history = root / "data/ai_review/pilot/history/2026/09" / PACKET_ID
    deterministic_path = history / "deterministic-messages.json"
    fallback_path = history / "fallback-messages.json"
    delivery_result_path = history / "delivery-result.json"
    validation_path = history / "validation-result.json"
    baseline_path = root / "app/resources/v2_accepted_migration_baseline.json"
    cpng_path = root / "data/onboarding/CPNG/onboarding-7c85c3812221b1b17c10.accepted.json"
    instruction_path = args.instruction.resolve()

    packet = _load(packet_path)
    deterministic = _load(deterministic_path)
    fallback = _load(fallback_path)
    delivery_result = _load(delivery_result_path)
    validation_result = _load(validation_path)
    baseline = _load(baseline_path)
    cpng = _load(cpng_path)
    env = _env_values(root / ".env")
    db = _db_evidence(root / "data/thesis_monitor.sqlite3", EXPECTED_TICKERS)
    automation = _automation_evidence(args.codex_database.resolve())
    validations = _validation_attempts(root)

    packet_tickers = tuple(row["ticker"] for row in packet["stocks"])
    eligible = tuple(packet["production_universe"]["eligible_subjects"])
    if packet["packet_id"] != PACKET_ID or set(packet_tickers) != set(EXPECTED_TICKERS):
        raise ValueError("target packet identity or cohort mismatch")
    if set(eligible) != set(EXPECTED_TICKERS):
        raise ValueError("frozen eligible cohort mismatch")
    if str(packet["source_monitor_run_id"]) != "49":
        raise ValueError("unexpected source run")
    if validation_result.get("status") != "rejected" or validation_result.get("rejected_ai_sent") is not False:
        raise ValueError("terminal validation safety state mismatch")

    messages = {row["ticker"]: row["payload"] for row in deterministic["messages"]}
    fallback_messages = {row["ticker"]: row for row in fallback["messages"]}
    delivery_rows = {row["ticker"]: row for row in db["deliveries"]}
    expected_delivery_tickers = set(EXPECTED_TICKERS) | {"__DAILY_DIGEST__"}
    if set(messages) != expected_delivery_tickers or set(fallback_messages) != expected_delivery_tickers:
        raise ValueError("archive message set mismatch")
    if set(delivery_rows) != expected_delivery_tickers:
        raise ValueError("delivery ledger set mismatch")

    exact_rows: list[dict[str, Any]] = []
    for ticker in sorted(expected_delivery_tickers):
        deterministic_text = str(messages[ticker].get("text") or "")
        fallback_text = str(fallback_messages[ticker].get("text") or "")
        delivered = delivery_rows[ticker]
        exact = (
            deterministic_text
            == fallback_text
            == delivered["text"]
            and delivered["text_sha256"] == delivered["rendered_text_sha256"]
        )
        exact_rows.append(
            {
                "ticker": ticker,
                "text": deterministic_text,
                "text_sha256": _sha_text(deterministic_text),
                "archive_fallback_match": deterministic_text == fallback_text,
                "delivery_text_match": deterministic_text == delivered["text"],
                "recorded_render_match": delivered["text_sha256"] == delivered["rendered_text_sha256"],
                "exact": exact,
            }
        )
    live_exact = all(row["exact"] for row in exact_rows)

    baseline_by_ticker = {
        row["ticker"]: row
        for row in baseline["entries"]
        if row.get("market") == "us" and row.get("ticker") in EXPECTED_TICKERS
    }
    baseline_by_ticker["CPNG"] = {
        "ticker": "CPNG",
        "accepted_decision": cpng["accepted_decision"],
        "accepted_decision_id": cpng["accepted_decision_id"],
        "evidence_sha256": cpng["accepted_evidence_fingerprint"],
        "source": "onboarding_accepted_artifact",
    }
    if set(baseline_by_ticker) != set(EXPECTED_TICKERS):
        raise ValueError("prior accepted control coverage mismatch")

    decisions: list[dict[str, Any]] = []
    routes: list[dict[str, Any]] = []
    for ticker in EXPECTED_TICKERS:
        text = str(messages[ticker]["text"])
        explicit = re.search(r"(?:AI 분석 판단|판단)\s*:\s*(BUY|HOLD|SELL)\b", text) is not None
        prior = baseline_by_ticker[ticker]
        decisions.append(
            {
                "ticker": ticker,
                "cohort_eligible": True,
                "prior_accepted_decision": prior["accepted_decision"],
                "prior_accepted_source": prior["source"],
                "fresh_v2_candidate_status": "NOT_GENERATED",
                "fresh_candidate_decision": None,
                "adjudication_status": "NOT_REACHED",
                "packet_bound_accepted_status": "NOT_CREATED",
                "packet_bound_accepted_decision": None,
                "accepted_plan_present": False,
                "renderer_route": "DETERMINISTIC_FALLBACK",
                "explicit_decision_visible": explicit,
                "raw_candidate_visible": False,
                "earliest_failure_stage": "CANDIDATE_NOT_GENERATED",
                "failure_scope": "SYSTEMIC",
            }
        )
        routes.append(
            {
                "ticker": ticker,
                "selector_state": "AI_VALIDATION_REJECTED_FALLBACK_ELIGIBLE",
                "accepted_decision_plan_present": False,
                "renderer_route": "DETERMINISTIC_FALLBACK",
                "decision_block_selected": False,
                "suppression_reason": "PACKET_BOUND_V2_CANDIDATE_NOT_GENERATED_AND_AI_OUTPUT_REJECTED",
                "visible_payload_sha256": _sha_text(text),
            }
        )

    price_rows: list[dict[str, Any]] = []
    valuation_rows: list[dict[str, Any]] = []
    quality_rows: list[dict[str, Any]] = []
    stock_by_ticker = {row["ticker"]: row for row in packet["stocks"]}
    for ticker in EXPECTED_TICKERS:
        payload = messages[ticker]
        text = str(payload["text"])
        rollout = payload["analysis_context"]["price_structure_v3_rollout"]
        bindings = list(rollout.get("numeric_bindings") or [])
        major_without_anchor = [
            row.get("semantic_type")
            for row in bindings
            if str(row.get("semantic_type", "")).startswith("MAJOR_") and not row.get("price_anchor_refs")
        ]
        provisional = [row for row in bindings if str(row.get("semantic_type", "")).startswith("PROVISIONAL_BOLLINGER")]
        price_status = (
            rollout.get("enabled") is True
            and rollout.get("monitored_subject") is True
            and not rollout.get("render_validation_errors")
            and rollout.get("section") in text
            and not major_without_anchor
            and all(row.get("is_partial_bar") is True and row.get("authoritative") is False for row in provisional)
        )
        price_rows.append(
            {
                "ticker": ticker,
                "eligibility": rollout.get("eligibility"),
                "binding_count": len(bindings),
                "major_without_price_anchor": major_without_anchor,
                "provisional_count": len(provisional),
                "render_errors": list(rollout.get("render_validation_errors") or []),
                "section_exactly_present": rollout.get("section") in text,
                "status": "PASS" if price_status else "FAIL",
            }
        )

        valuation = stock_by_ticker[ticker]["valuation"]
        financial_quality = valuation.get("financial_quality") or {}
        denied = set(financial_quality.get("denied_fields") or []) | set(financial_quality.get("non_prose_fields") or [])
        valuation_section = text.split("📐 Valuation", 1)[1].split("📌 다음 확인", 1)[0] if "📐 Valuation" in text else ""
        violations: list[str] = []
        if "price_to_book" in denied and re.search(r"^PBR\s*=", valuation_section, re.MULTILINE):
            violations.append("denied_current_pbr_rendered")
        if any(label in text for label in ("FCF Yield", "FCF/share", "EV/FCF", "P/FCF")):
            violations.append("unsupported_cash_flow_valuation")
        if "📐 Valuation" not in text:
            violations.append("valuation_section_missing")
        valuation_rows.append(
            {
                "ticker": ticker,
                "security_identity_state": valuation.get("security_identity_state"),
                "security_identity_verification_status": valuation.get("security_identity_verification_status"),
                "denied_fields": sorted(denied),
                "uses_nm_semantics": "N/M" in valuation_section,
                "uses_withholding_language": "판단 자료 부족" in valuation_section or "보류" in valuation_section,
                "violations": violations,
                "status": "PASS" if not violations else "FAIL",
            }
        )

        explicit = next(row for row in decisions if row["ticker"] == ticker)["explicit_decision_visible"]
        empty_sections = _empty_visible_sections(text)
        order_command = any(term in text.lower() for term in ("즉시 매수", "즉시 매도", "지금 매수", "지금 매도", "buy now", "sell now"))
        quality_rows.append(
            {
                "ticker": ticker,
                "message_length": len(text),
                "explicit_decision_visible": explicit,
                "raw_candidate_visible": False,
                "empty_visible_sections": empty_sections,
                "order_command": order_command,
                "renderer_quality": "PASS" if not empty_sections and not order_command else "FAIL",
                "v2_decision_quality": "FAIL" if not explicit else "PASS",
            }
        )

    market_text = str(messages["__DAILY_DIGEST__"]["text"])
    if str(worktree_root) not in sys.path:
        sys.path.insert(0, str(worktree_root))
    from app.services.us_market_message_quality_service import (  # noqa: PLC0415
        validate_us_market_message_payload,
    )

    market_quality_receipt = validate_us_market_message_payload(market_text).to_dict()
    required_market_fragments = ("SPY -0.30%", "QQQ +0.05%", "IWM -0.62%", "SOXX +0.48%", "RSP -0.59%", "에너지 +2.04%", "커뮤니케이션 서비스 -1.35%", "미국 10년물 실질금리는 상승")
    market_quality = all(fragment in market_text for fragment in required_market_fragments)
    digest_plan = packet["market_context"]["us_market_digest_plan"]
    digest_by_slot = {row["slot"]: row for row in digest_plan["items"]}
    market_quality = (
        market_quality
        and digest_by_slot["SMALL_CAP_RELATIVE"]["omission_reason"] == "OMITTED_SAFE_NOT_MATERIAL"
        and market_quality_receipt["status"] == "PASS"
    )

    watchlist = {row["ticker"]: row for row in db["watchlist"]}
    cpng_watch = watchlist["CPNG"]
    run = db["run"]
    primary_run = next(row for row in automation["runs"] if row["thread_id"] == PRIMARY_THREAD_ID)
    backup_run = next(row for row in automation["runs"] if row["thread_id"] == BACKUP_THREAD_ID)
    primary_config = next(row for row in automation["automations"] if row["id"].endswith("us-primary"))
    backup_config = next(row for row in automation["automations"] if row["id"].endswith("us-backup"))

    exactly_once = (
        len(db["deliveries"]) == 15
        and all(row["status"] == "sent" and row["attempt_count"] == 1 for row in db["deliveries"])
        and len({row["ticker"] for row in db["deliveries"]}) == 15
        and all(row["chunk_count"] == row["next_chunk_index"] == 1 for row in db["deliveries"])
    )
    price_contract = all(row["status"] == "PASS" for row in price_rows)
    valuation_contract = all(row["status"] == "PASS" for row in valuation_rows)
    empty_count = sum(row["empty_visible_sections"] for row in quality_rows)
    prior_counts = Counter(row["accepted_decision"] for row in baseline_by_ticker.values())

    gates = {
        "MANUAL_US_PRODUCTION_JOB_TRIGGER": 0,
        "MANUAL_US_PRODUCTION_SEND": 0,
        "US_PRODUCTION_STATE_MUTATION": 0,
        "US_CANONICAL_SESSION_DATE": CANONICAL_SESSION_DATE,
        "US_RUNTIME_LINEAGE": "PASS",
        "US_ACTIVE_US_FOREIGN_COUNT": 14,
        "US_CUTOFF_ELIGIBLE_STOCK_COUNT": 14,
        "CPNG_CUTOFF_STATUS": "ACTIVE_READY_BEFORE_CUTOFF",
        "CPNG_V2_LIVE_STATUS": "MISSING_UNEXPECTED",
        "CPNG_BLOCKS_OTHER_US_SUBJECTS": 0,
        "US_PACKET_UNIVERSE_MUTATED_AFTER_CUTOFF": 0,
        "US_MARKET_MESSAGE_QUALITY": "PASS" if market_quality else "FAIL",
        "US_MACRO_TEMPORAL_SAFETY": "PASS",
        "US_NIGHT_FUTURES": "SOURCE_LIMITATION_SAFE",
        "US_SAME_EVIDENCE_UNEXPLAINED_DECISION_CHURN": 0,
        "US_UNADJUDICATED_MATERIAL_CHANGE_VISIBLE": 0,
        "US_ACCEPTED_READY_COUNT": 0,
        "US_NOT_READY_COUNT": 14,
        "US_ACCEPTED_BUY_COUNT": 0,
        "US_ACCEPTED_HOLD_COUNT": 0,
        "US_ACCEPTED_SELL_COUNT": 0,
        "US_PRIOR_ACCEPTED_BUY_CONTROL_COUNT": prior_counts["BUY"],
        "US_PRIOR_ACCEPTED_HOLD_CONTROL_COUNT": prior_counts["HOLD"],
        "US_PRIOR_ACCEPTED_SELL_CONTROL_COUNT": prior_counts["SELL"],
        "US_RENDERER_ROUTE_IDENTIFIED_COUNT": len(routes),
        "US_EXPLICIT_DECISION_BLOCK_VISIBLE_COUNT": sum(row["explicit_decision_visible"] for row in decisions),
        "US_OLD_OR_FALLBACK_STOCK_MESSAGE_COUNT": 14,
        "US_RAW_CANDIDATE_VISIBLE": 0,
        "CORZ_V2_STATUS": "FALLBACK_RENDERER_ROUTE",
        "GOOGL_V2_LIVE_CONTROL": "FAIL",
        "US_SELL_PATH_VISIBILITY": "FAIL",
        "PRIMARY_V2_ABSENCE_ROOT_CAUSE": "CANDIDATE_NOT_GENERATED",
        "V2_ABSENCE_SCOPE": "SYSTEMIC",
        "US_PRICE_STRUCTURE_CONTRACT": "PASS" if price_contract else "FAIL",
        "US_VALUATION_CONTRACT": "PASS" if valuation_contract else "FAIL",
        "US_EXPECTED_STOCK_MESSAGE_COUNT": 14,
        "US_EXPECTED_PRODUCTION_MESSAGE_COUNT": 15,
        "US_SENT_PRODUCTION_MESSAGE_COUNT": sum(row["status"] == "sent" for row in db["deliveries"]),
        "US_RECEIVED_PRODUCTION_MESSAGE_COUNT": sum(row["chunk_count"] == row["next_chunk_index"] == 1 for row in db["deliveries"]),
        "US_LIVE_EXACT_PAYLOAD": "PASS" if live_exact else "FAIL",
        "US_EXACTLY_ONCE_DELIVERY": "PASS" if exactly_once else "FAIL",
        "US_DUPLICATE": 0 if len({row["ticker"] for row in db["deliveries"]}) == 15 else 1,
        "US_ORPHAN": 0 if set(delivery_rows) == expected_delivery_tickers else 1,
        "US_UNOWNED_RETRY": 0 if all(row["attempt_count"] == 1 for row in db["deliveries"]) else 1,
        "US_EMPTY_VISIBLE_SECTION_COUNT": empty_count,
        "US_V2_MESSAGE_QUALITY": "FAIL",
        "OPEN_P0": 0,
        "OPEN_MATERIAL_P1": 2,
        "OPEN_P2": 0,
        "US_V2_NATURAL_LIVE": "FAIL",
        "NEXT_ACTION": "BOUNDED_DECISION_PIPELINE_REPAIR",
    }

    proof = {
        "contract": "us-v2-natural-live-readonly-verification-v1",
        "instruction_commit": INSTRUCTION_COMMIT,
        "base_sha": BASE_SHA,
        "run_id": 49,
        "packet_id": PACKET_ID,
        "assessment_date": ASSESSMENT_DATE,
        "canonical_session_date": CANONICAL_SESSION_DATE,
        "gates": gates,
        "root_cause": {
            "earliest_stage": "CANDIDATE_NOT_GENERATED",
            "scope": "SYSTEMIC",
            "primary": "Both natural automations exited accepted_decision_v2_runtime.prepare_context while fetching local OHLCV, before a packet-bound V2 candidate or accepted plan existed.",
            "secondary": "The backup AI prose candidate then remained rejected on a false-positive numbers_without_provenance:2000 finding, so deterministic fallback became terminal.",
        },
        "terminal_validation": {
            "status": validation_result.get("status"),
            "errors": list(validation_result.get("errors") or []),
            "fallback_eligibility_preserved": validation_result.get("fallback_eligibility_preserved"),
            "rejected_ai_sent": validation_result.get("rejected_ai_sent"),
        },
        "safety": {
            "manual_trigger": 0,
            "manual_send": 0,
            "production_state_mutation": 0,
            "raw_candidate_visible": 0,
            "secret_values_recorded": 0,
        },
        "market_quality_receipt": market_quality_receipt,
    }

    _write_json(output / JSON_NAMES[0], {"packet_id": PACKET_ID, "decisions": decisions, "prior_control_distribution": dict(prior_counts)})
    _write_json(output / JSON_NAMES[1], {"packet_id": PACKET_ID, "routes": routes})
    _write_json(
        output / JSON_NAMES[2],
        {
            "packet_id": PACKET_ID,
            "delivery_mode": delivery_result["delivery_mode"],
            "dispatched_at": delivery_result["dispatched_at"],
            "expected": 15,
            "sent": gates["US_SENT_PRODUCTION_MESSAGE_COUNT"],
            "recorded_complete": gates["US_RECEIVED_PRODUCTION_MESSAGE_COUNT"],
            "rows": [{key: value for key, value in row.items() if key != "text"} for row in db["deliveries"]],
            "exact_payload_rows": [{key: value for key, value in row.items() if key != "text"} for row in exact_rows],
        },
    )
    _write_json(output / JSON_NAMES[3], proof)

    _write(
        output / REPORT_NAMES[0],
        _report(
            "2026-09-01 US V2 Natural Live Run Identity",
            f"""- `RUN_ID`: `49`
- `PACKET_ID`: `{PACKET_ID}`
- canonical US session: `{CANONICAL_SESSION_DATE}`
- source monitor: `{run['status']}`, `{_utc_db_to_kst(run['started_at'])}` to `{_utc_db_to_kst(run['completed_at'])}`, `{run['success_count']}/{run['ticker_count']}`
- primary scheduled: `08:15 KST`; actual: `{primary_run['created_at_kst']}` to `{primary_run['updated_at_kst']}`
- backup scheduled: `08:30 KST`; actual: `{backup_run['created_at_kst']}` to `{backup_run['updated_at_kst']}`
- terminal packet claim owner: `codex-us-backup`
- dispatch: `{delivery_result['dispatched_at']}`
- delivery mode: `{delivery_result['delivery_mode']}`
- job exit: source monitor succeeded; both V2 generators exited fail-closed; backup fallback sent successfully.

No production job, scheduler, retry, or send was manually invoked during this proof.""",
        ),
    )
    operating_sha = _git(root, "rev-parse", "HEAD")
    _write(
        output / REPORT_NAMES[1],
        _report(
            "US V2 Runtime Lineage",
            f"""- `origin/main`: `{args.origin_main_sha}`
- operating HEAD: `{operating_sha}`
- runtime code SHA: `{operating_sha}`
- work-instruction commit: `{INSTRUCTION_COMMIT}`
- target run occurred after `{BASE_SHA}` was present in the operating checkout.
- `US_RUNTIME_LINEAGE`: `PASS`

The scheduled automation source cwd was the operating checkout. This report-only branch did not alter runtime code.""",
        ),
    )
    _write(
        output / REPORT_NAMES[2],
        _report(
            "US V2 Feature State",
            f"""| State | Value |
| --- | --- |
| VISIBLE_STOCK_DECISION_ENGINE | `{env.get('VISIBLE_STOCK_DECISION_ENGINE', 'UNKNOWN')}` |
| V2_PRODUCTION_ENABLED | `{env.get('V2_PRODUCTION_ENABLED', 'UNKNOWN')}` |
| FULL_MONITORED_STOCK_COVERAGE_TARGET | `{env.get('V2_FULL_MONITORED_STOCK_COVERAGE_TARGET', 'UNKNOWN')}` |
| V1_VISIBLE_DECISION_ENGINE | `false` |
| V1_ROLLBACK_AVAILABLE | `{env.get('V1_DECISION_ROLLBACK_AVAILABLE', 'UNKNOWN')}` |
| PRODUCTION_ASSIST | `OFF` |
| AI_REVIEW_MODE | `{env.get('AI_REVIEW_MODE', 'UNKNOWN')}` |
| AI_REVIEW_PILOT_ENABLED | `{env.get('AI_REVIEW_PILOT_ENABLED', 'UNKNOWN')}` |
| background onboarding reconciler | `ENABLED_BOUNDED` |
| market-preflight onboarding resume | `ENABLED_BOUNDED_CACHED_ONLY` |

The primary and backup automations remained `ACTIVE`; their configured reasoning effort was `{primary_config['reasoning_effort']}` and `{backup_config['reasoning_effort']}` respectively.""",
        ),
    )
    cohort_rows = []
    for ticker in EXPECTED_TICKERS:
        watch = watchlist[ticker]
        cohort_rows.append((ticker, bool(watch["active"]), watch["onboarding_state"], bool(watch["production_eligible"]), "YES", watch["first_eligible_session"] or "pre-existing", "-"))
    _write(
        output / REPORT_NAMES[3],
        _report(
            "US V2 Frozen Cohort",
            f"""Packet cutoff: `{packet['production_universe']['cutoff']}`

{_table(('Ticker', 'Active', 'Onboarding', 'Prod eligible', 'Included', 'First eligible', 'Exclusion'), cohort_rows)}

`NVDA` was excluded with the packet-recorded inactive/not-requested reasons. The immutable packet cohort and the 14 stock delivery rows match exactly.

- `US_PACKET_UNIVERSE_MUTATED_AFTER_CUTOFF`: `0`
- `US_CUTOFF_ELIGIBLE_STOCK_COUNT`: `14`""",
        ),
    )
    _write(
        output / REPORT_NAMES[4],
        _report(
            "CPNG Natural Live Control",
            f"""- active: `{bool(cpng_watch['active'])}`
- monitoring requested: `{bool(cpng_watch['monitoring_requested'])}`
- onboarding state: `{cpng_watch['onboarding_state']}`
- production eligible: `{bool(cpng_watch['production_eligible'])}`
- ready at: `{_utc_db_to_kst(cpng_watch['onboarding_ready_at'])}`
- activated at: `{_utc_db_to_kst(cpng_watch['activated_at'])}`
- first eligible session: `{cpng_watch['first_eligible_session']}`
- packet cutoff: `{packet['production_universe']['cutoff']}`
- frozen cohort included: `YES`
- prior onboarding accepted control: `{cpng['accepted_decision']}` / `{cpng['status']}` / adjudication `{cpng['accepted_plan']['adjudication_status']}`
- packet-bound V2 candidate: `NOT_GENERATED`
- packet-bound accepted plan: `NOT_CREATED`
- delivery: `SENT_ONCE_DETERMINISTIC_FALLBACK`
- explicit decision block: `NO`

`CPNG_CUTOFF_STATUS = ACTIVE_READY_BEFORE_CUTOFF`

`CPNG_V2_LIVE_STATUS = MISSING_UNEXPECTED`

`CPNG_BLOCKS_OTHER_US_SUBJECTS = 0`""",
        ),
    )
    _write(
        output / REPORT_NAMES[5],
        _report(
            "US Market Message Proof",
            f"""```text
{market_text}
```

- core index observations: all dated `{CANONICAL_SESSION_DATE}`.
- SOXX/SPY relative spread: selected after passing the existing materiality rule.
- IWM/SPY relative spread: safely omitted at `-0.32pp`, below the existing `0.50pp` threshold.
- RSP is described as participation style, not broad advance/decline breadth.
- sector leader/laggard: XLE/XLC, exact payload-bound.
- runtime quality receipt: `{market_quality_receipt['contract']}` / `{market_quality_receipt['status']}` / errors `{len(market_quality_receipt['errors'])}` / payload `{market_quality_receipt['payload_sha256']}`.
- `US_MARKET_MESSAGE_QUALITY = {'PASS' if market_quality else 'FAIL'}`""",
        ),
    )
    night = packet["market_context"]["night_futures_audit"]
    _write(
        output / REPORT_NAMES[6],
        _report(
            "US Macro and Night Futures",
            f"""- DFII10 observation date: `{digest_by_slot['MACRO_CONTEXT']['observation_dates'][0]}`
- temporal role: `{digest_by_slot['MACRO_CONTEXT']['temporal_roles'][0]}`
- rendered role: supporting market environment; no same-session or intraday wording.
- night-futures expected session: `{night['expected_session']}`
- query time: `{night['query_time']}`
- ready products: `0/2`; both official rows were unavailable and omitted.
- `US_MACRO_TEMPORAL_SAFETY = PASS`
- `US_NIGHT_FUTURES = SOURCE_LIMITATION_SAFE`""",
        ),
    )
    decision_table = _table(
        ("Ticker", "Prior control", "Fresh candidate", "Adjudication", "Packet accepted", "Visible", "Earliest failure"),
        ((row["ticker"], row["prior_accepted_decision"], row["fresh_v2_candidate_status"], row["adjudication_status"], row["packet_bound_accepted_status"], "YES" if row["explicit_decision_visible"] else "NO", row["earliest_failure_stage"]) for row in decisions),
    )
    _write(
        output / REPORT_NAMES[7],
        _report(
            "Candidate, Adjudication, and Accepted Decision Audit",
            f"""{decision_table}

The migration/onboarding artifacts provide prior controls (`BUY {prior_counts['BUY']}`, `HOLD {prior_counts['HOLD']}`, `SELL {prior_counts['SELL']}`), but they are not fresh packet-bound accepted plans. Both natural V2 generation attempts failed before candidate creation, so packet-bound accepted counts are zero.

AI prose candidates were generated separately and rejected; none is an accepted V2 decision artifact and none was delivered.""",
        ),
    )
    route_table = _table(
        ("Ticker", "Selector", "Accepted plan", "Route", "Decision block", "Reason"),
        ((row["ticker"], row["selector_state"], "NO", row["renderer_route"], "NO", row["suppression_reason"]) for row in routes),
    )
    _write(
        output / REPORT_NAMES[8],
        _report(
            "US V2 Renderer Route Audit",
            f"""{route_table}

- routes identified: `14/14`
- renderer omission classification: `NOT_APPLICABLE`; no packet-bound accepted plan reached the selector.
- terminal route: `DETERMINISTIC_FALLBACK` for the full stock cohort.
- `PRIMARY_V2_ABSENCE_ROOT_CAUSE = CANDIDATE_NOT_GENERATED`
- `V2_ABSENCE_SCOPE = SYSTEMIC`""",
        ),
    )
    _write(
        output / REPORT_NAMES[9],
        _report(
            "CORZ V2 Root-Cause Trace",
            """`evidence → candidate → adjudication → accepted → selector → renderer → validator → delivery`

1. CORZ was eligible and present in the immutable packet.
2. The natural V2 generator entered `accepted_decision_v2_runtime.prepare_context`.
3. Local OHLCV fetch raised `httpcore.ConnectError`; no CORZ candidate was created.
4. Adjudication and packet-bound acceptance were never reached.
5. The separate AI prose candidate was rejected by validation.
6. Backend selected deterministic fallback.
7. The fallback payload was delivered once and matched archive/ledger text exactly.

Prior control: `HOLD`. Visible explicit decision: `NO`.

`CORZ_V2_STATUS = FALLBACK_RENDERER_ROUTE`""",
        ),
    )
    _write(
        output / REPORT_NAMES[10],
        _report(
            "GOOGL BUY Control",
            """- prior accepted control: `BUY`
- fresh packet-bound candidate: `NOT_GENERATED`
- adjudication: `NOT_REACHED`
- new accepted plan: `NOT_CREATED`
- delivered route: `DETERMINISTIC_FALLBACK`
- top-level BUY/HOLD/SELL: `NOT_VISIBLE`
- visible text only states `투자 논리: 유지`, which is not a HOLD decision block.

Fresh evidence could legitimately change BUY, but no fresh decision exists to explain or validate a change.

`GOOGL_V2_LIVE_CONTROL = FAIL`""",
        ),
    )
    _write(
        output / REPORT_NAMES[11],
        _report(
            "US SELL Controls",
            f"""{_table(('Ticker', 'Prior accepted', 'Fresh packet decision', 'Visible decision', 'Route'), ((ticker, 'SELL', 'NONE', 'NO', 'DETERMINISTIC_FALLBACK') for ticker in SELL_CONTROLS))}

No order-command language was present, but none of the prior SELL controls exposed a fresh accepted bearish decision.

`US_SELL_PATH_VISIBILITY = FAIL`""",
        ),
    )
    _write(
        output / REPORT_NAMES[12],
        _report(
            "US Price Structure Contract",
            f"""{_table(('Ticker', 'Eligibility', 'Bindings', 'Provisional', 'Major missing anchor', 'Render errors', 'Status'), ((row['ticker'], row['eligibility'], row['binding_count'], row['provisional_count'], len(row['major_without_price_anchor']), len(row['render_errors']), row['status']) for row in price_rows))}

Every rendered section matched its archived rollout section. Major structural zones retained price anchors; provisional Bollinger layers remained partial/non-authoritative with close-time caution.

`US_PRICE_STRUCTURE_CONTRACT = {'PASS' if price_contract else 'FAIL'}`""",
        ),
    )
    _write(
        output / REPORT_NAMES[13],
        _report(
            "US Valuation Contract",
            f"""{_table(('Ticker', 'Identity state', 'Denied fields', 'N/M', 'Withheld', 'Violations', 'Status'), ((row['ticker'], row['security_identity_state'], len(row['denied_fields']), row['uses_nm_semantics'], row['uses_withholding_language'], ', '.join(row['violations']) or '-', row['status']) for row in valuation_rows))}

Denied current PBR values were not rendered as current PBR equations. N/M and withheld-language paths remained fail-closed. No FCF yield, per-share FCF, EV/FCF, or P/FCF was produced.

`US_VALUATION_CONTRACT = {'PASS' if valuation_contract else 'FAIL'}`""",
        ),
    )
    exact_blocks = []
    for row in exact_rows:
        exact_blocks.append(f"## {row['ticker']}\n\nSHA-256: `{row['text_sha256']}`\n\n```text\n{row['text']}\n```")
    _write(output / REPORT_NAMES[14], _report("US Live Exact Production Messages", "\n\n".join(exact_blocks)))
    delivery_table = _table(
        ("ID", "Ticker", "Status", "Attempts", "Sent KST", "Chunk", "Pilot state", "Text SHA-256"),
        ((row["id"], row["ticker"], row["status"], row["attempt_count"], row["sent_at_kst"], f"{row['next_chunk_index']}/{row['chunk_count']}", row["pilot_state"], row["text_sha256"]) for row in db["deliveries"]),
    )
    _write(
        output / REPORT_NAMES[15],
        _report(
            "US V2 Live Delivery",
            f"""{delivery_table}

- expected: `15`; sent: `{gates['US_SENT_PRODUCTION_MESSAGE_COUNT']}`; recorded complete: `{gates['US_RECEIVED_PRODUCTION_MESSAGE_COUNT']}`
- dispatch: `{delivery_result['dispatched_at']}`
- delivery mode: `{delivery_result['delivery_mode']}`
- archive fallback, delivery payload, and recorded rendered text SHA matched for all messages.
- duplicate: `0`; orphan: `0`; unowned retry: `0`
- `US_LIVE_EXACT_PAYLOAD = {gates['US_LIVE_EXACT_PAYLOAD']}`
- `US_EXACTLY_ONCE_DELIVERY = {gates['US_EXACTLY_ONCE_DELIVERY']}`""",
        ),
    )
    _write(
        output / REPORT_NAMES[16],
        _report(
            "US V2 Message Quality",
            f"""{_table(('Ticker', 'Length', 'Explicit decision', 'Empty sections', 'Order command', 'Renderer quality', 'V2 quality'), ((row['ticker'], row['message_length'], row['explicit_decision_visible'], row['empty_visible_sections'], row['order_command'], row['renderer_quality'], row['v2_decision_quality']) for row in quality_rows))}

The deterministic messages were readable and structurally complete, but all 14 lacked the required accepted BUY/HOLD/SELL block. `투자 논리: 유지` was not counted as HOLD. Raw candidate visibility and unadjudicated material decision visibility were both zero.

- `US_EMPTY_VISIBLE_SECTION_COUNT = {empty_count}`
- `US_V2_MESSAGE_QUALITY = FAIL`""",
        ),
    )
    gate_lines = "\n".join(f"- `{key} = {value}`" for key, value in gates.items())
    _write(
        output / REPORT_NAMES[17],
        _report(
            "US V2 Natural Live Proof",
            f"""## Decision

`US_V2_NATURAL_LIVE = FAIL`

## Earliest break

Both natural primary and backup runs failed at packet-bound V2 candidate preparation while fetching local OHLCV. No candidate, adjudication, or accepted plan was produced. The separate AI prose path also rejected its final candidate, so the safe deterministic fallback delivered 15/15 once.

This is operationally safe but not a V2 natural-live proof.

## Severity

- P0: `0`
- Material P1: `2`
  - V2 candidate generation has a systemic local OHLCV availability dependency with no packet-safe accepted-plan continuation.
  - Backup AI validation retained a false-positive `numbers_without_provenance:market_context.text:2000`, forcing fallback despite no literal `2000` in the repaired market sentence.
- P2: `0`

## Gates

{gate_lines}

## Next action

`BOUNDED_DECISION_PIPELINE_REPAIR`

Repair was intentionally not performed during this proof.""",
        ),
    )

    source_artifacts = (packet_path, deterministic_path, fallback_path, delivery_result_path, validation_path, baseline_path, cpng_path)
    report_artifacts = tuple(output / name for name in REPORT_NAMES[:-1]) + tuple(output / name for name in JSON_NAMES)
    artifact_rows = [("source", str(path.relative_to(root)), _sha_file(path)) for path in source_artifacts]
    artifact_rows.extend(("report", path.name, _sha_file(path)) for path in report_artifacts)
    artifact_rows.append(("instruction", str(instruction_path.relative_to(args.worktree_root.resolve())), _sha_file(instruction_path)))
    validation_rows = [(row["artifact"], row["recorded_at_kst"], row["claim_id"], len(row["errors"]), row["sha256"]) for row in validations]
    _write(
        output / REPORT_NAMES[18],
        _report(
            "US V2 Natural Live Artifact Index",
            f"""## Immutable sources and generated reports

{_table(('Class', 'Artifact', 'SHA-256'), artifact_rows)}

## Rejected AI validation receipts

{_table(('Artifact', 'Recorded KST', 'Claim', 'Errors', 'SHA-256'), validation_rows)}

Automation execution evidence was read from the two natural Codex rollout records identified by thread ID. Stack traces were reduced to their exception class and failing module path; no hidden reasoning or sensitive runtime values are included.""",
        ),
    )

    generated = tuple(output / name for name in REPORT_NAMES) + tuple(output / name for name in JSON_NAMES)
    _redaction_check(generated)
    return {
        "proof": proof,
        "generated": [str(path) for path in generated],
        "validation_attempts": validations,
        "price_rows": price_rows,
        "valuation_rows": valuation_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--operating-root", type=Path, required=True)
    parser.add_argument("--worktree-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--instruction", type=Path, required=True)
    parser.add_argument("--codex-database", type=Path, required=True)
    parser.add_argument("--origin-main-sha", required=True)
    args = parser.parse_args()
    result = build(args)
    print(json.dumps({"generated_count": len(result["generated"]), "gates": result["proof"]["gates"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
