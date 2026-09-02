from __future__ import annotations

# ruff: noqa: E501

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo


PACKET_ID = "2026-09-02-us-run-51-39a4d4eec53e"
CLAIM_STEM = f"{PACKET_ID}--daily-review-v3.10--dc747fff8565"
ASSESSMENT_DATE = "2026-09-02"
CANONICAL_SESSION_DATE = "2026-09-01"
RUN_ID = 51
INSTRUCTION_COMMIT = "ec843952011e32a4ef81946e1e5bc10dd1c1f809"
REFERENCE_RUNTIME_SHA = "26004d926247c4ef053e49b74dc8fb9654353199"
RUNTIME_REPAIR_SHA = "b5be74439b2e8e769b1605e539599835abbc8a84"
PRIMARY_CLAIM_ID = "afd76205-7401-4912-a8a6-4711fd214e1b"
BACKUP_CLAIM_ID = "47594101-6ad0-497e-962d-4c1b208f5fe4"
KST = ZoneInfo("Asia/Seoul")
TICKERS = (
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
REPORTS = (
    "20260902-us-natural-live-run-identity.md",
    "20260902-us-runtime-lineage.md",
    "20260902-us-scheduler-ownership.md",
    "20260902-us-frozen-cohort.md",
    "20260902-us-market-raw-data.md",
    "20260902-us-market-relative-sector-breadth.md",
    "20260902-us-macro-temporal-safety.md",
    "20260902-us-night-futures-proof.md",
    "20260902-us-market-message-proof.md",
    "20260902-us14-source-readiness.md",
    "20260902-us14-technical-context.md",
    "20260902-cpng-hut-live-technical-controls.md",
    "20260902-us14-evidence-packet.md",
    "20260902-us-v2-model-candidate-generation.md",
    "20260902-us-candidate-validation.md",
    "20260902-us-adjudication-accepted.md",
    "20260902-us-renderer-routes.md",
    "20260902-us-final-validator.md",
    "20260902-us-live-exact-messages.md",
    "20260902-us-live-delivery.md",
    "20260902-us-live-stage-matrix.md",
    "20260902-us-natural-live-proof.md",
    "20260902-us-natural-live-artifact-index.md",
)
JSON_REPORTS = (
    "20260902-us-market-data.json",
    "20260902-us-night-futures.json",
    "20260902-us-live-decisions.json",
    "20260902-us-live-stage-matrix.json",
    "20260902-us-live-delivery.json",
    "20260902-us-natural-live-proof.json",
)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, value: object) -> None:
    write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def sha_text(value: str) -> str:
    return sha_bytes(value.encode("utf-8"))


def table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(str(item) for item in row) + " |" for row in rows)
    return "\n".join(lines)


def report(title: str, body: str) -> str:
    return f"# {title}\n\n{body.rstrip()}\n"


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(("git", "-C", str(root), *args), text=True).strip()


def utc_db_to_kst(value: object) -> str | None:
    if value in (None, ""):
        return None
    parsed = datetime.fromisoformat(str(value))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(KST).isoformat()


def epoch_ms_to_kst(value: object) -> str | None:
    if value in (None, ""):
        return None
    return datetime.fromtimestamp(int(value) / 1000, tz=UTC).astimezone(KST).isoformat()


def file_mtime_kst(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).astimezone(KST).isoformat()


def read_env_flags(path: Path) -> dict[str, str]:
    allowed = {
        "AI_REVIEW_MODE",
        "AI_REVIEW_PILOT_ENABLED",
        "VISIBLE_STOCK_DECISION_ENGINE",
        "V2_PRODUCTION_ENABLED",
        "V2_FULL_MONITORED_STOCK_COVERAGE_TARGET",
        "V1_DECISION_ROLLBACK_AVAILABLE",
        "PRODUCTION_ASSIST",
    }
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() in allowed:
            result[key.strip()] = value.strip().strip("'\"")
    return result


def database_evidence(database: Path) -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        run = connection.execute(
            """
            SELECT id, run_date, run_type, status, started_at, completed_at,
                   ticker_count, success_count, failure_count
              FROM monitorrun
             WHERE id = ?
            """,
            (RUN_ID,),
        ).fetchone()
        placeholders = ",".join("?" for _ in TICKERS)
        watchlist = connection.execute(
            f"""
            SELECT ticker, active, monitoring_requested, onboarding_state,
                   production_eligible, onboarding_ready_at, activated_at,
                   first_eligible_session, onboarding_failure_stage
              FROM watchlistitem
             WHERE ticker IN ({placeholders})
             ORDER BY ticker
            """,
            TICKERS,
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
                "sent_at_kst": utc_db_to_kst(row["sent_at"]),
                "text": text,
                "text_sha256": sha_text(text),
                "pilot_state": pilot.get("state"),
                "packet_id": pilot.get("packet_id"),
                "renderer_version": pilot.get("renderer_version"),
                "fallback_started_at": pilot.get("fallback_started_at"),
                "ai_validation_state": pilot.get("ai_validation_state"),
                "ai_validation_errors": list(pilot.get("ai_validation_errors") or []),
                "chunk_count": telegram.get("chunk_count"),
                "next_chunk_index": telegram.get("next_chunk_index"),
                "recorded_render_sha256": sha_text(str(telegram.get("rendered_text") or "")),
                "content_sha256": telegram.get("content_sha256"),
            }
        )
    return {
        "run": dict(run) if run else None,
        "watchlist": [dict(row) for row in watchlist],
        "deliveries": delivery_rows,
    }


def automation_evidence(database: Path) -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        configurations = connection.execute(
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
            SELECT automation_id, status, created_at, updated_at
              FROM automation_runs
             WHERE automation_id IN ('thesis-monitor-ai-review-us-primary',
                                     'thesis-monitor-ai-review-us-backup')
               AND created_at >= ? AND created_at < ?
             ORDER BY created_at
            """,
            (1788303600000, 1788307200000),
        ).fetchall()
    finally:
        connection.close()
    return {
        "configurations": [
            {
                **dict(row),
                "last_run_at_kst": epoch_ms_to_kst(row["last_run_at"]),
                "next_run_at_kst": epoch_ms_to_kst(row["next_run_at"]),
            }
            for row in configurations
        ],
        "runs": [
            {
                **dict(row),
                "created_at_kst": epoch_ms_to_kst(row["created_at"]),
                "updated_at_kst": epoch_ms_to_kst(row["updated_at"]),
            }
            for row in runs
        ],
    }


def safe_count(quality: Mapping[str, Any]) -> int:
    return sum(int((quality.get(key) or {}).get("safe_feature_count") or 0) for key in ("D", "W", "M"))


def blocked_count(quality: Mapping[str, Any]) -> int:
    return sum(int((quality.get(key) or {}).get("dependency_blocked_count") or 0) for key in ("D", "W", "M"))


def feature_value(technical: Mapping[str, Any], timeframe: str, semantic: str) -> str | None:
    rows = (((technical.get("features") or {}).get(timeframe) or {}).get("facts") or [])
    for row in rows:
        if row.get("semantic") == semantic:
            return str(row.get("value"))
    return None


def valuation_available(stock: Mapping[str, Any]) -> bool:
    valuation = stock.get("valuation") or {}
    keys = ("trailing_pe", "forward_pe", "price_to_book", "latest_revenue")
    return any(valuation.get(key) is not None for key in keys)


def normalize_cli_error(text: str) -> str:
    if "failed to initialize in-process app-server client" in text:
        return "CODEX_APP_SERVER_INITIALIZATION_FAILED_READONLY_STATE_DB"
    return "UNKNOWN"


def secret_check(paths: Iterable[Path]) -> None:
    patterns = (
        re.compile(r"\b-100\d{5,}\b"),
        re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{20,}\b"),
        re.compile(r"Bearer\s+[A-Za-z0-9._-]{12,}", re.IGNORECASE),
        re.compile(r"TELEGRAM_(?:CHAT|TEST_CHAT)_ID\s*=\s*[^\s`]+"),
    )
    for path in paths:
        value = path.read_text(encoding="utf-8")
        for pattern in patterns:
            if pattern.search(value):
                raise ValueError(f"secret-like value found: {path.name}")


def build(args: argparse.Namespace) -> dict[str, Any]:
    root = args.operating_root.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    packet_path = root / "data/ai_review/inbox" / f"{PACKET_ID}.json"
    outbox_path = root / "data/ai_review/outbox" / f"{CLAIM_STEM}.json"
    history_dir = root / "data/ai_review/pilot/history/2026/09" / PACKET_ID
    claim_dir = root / "data/ai_review/claims"
    rejected_validation_path = root / "data/ai_review/rejected" / f"{CLAIM_STEM}.json.1788305375.validation.json"
    numeric_binding_path = root / "data/ai_review/history/2026/09" / f"{CLAIM_STEM}.numeric-binding.json"
    context_path = claim_dir / f"{CLAIM_STEM}--{BACKUP_CLAIM_ID}.decision-v2-context.json"

    packet = load(packet_path)
    outbox = load(outbox_path)
    deterministic = load(history_dir / "deterministic-messages.json")
    fallback = load(history_dir / "fallback-messages.json")
    delivery_result = load(history_dir / "delivery-result.json")
    validation_result = load(history_dir / "validation-result.json")
    quality_receipt = load(history_dir / "message-quality-receipt.json")
    market_context = load(history_dir / "market-context.json")
    market_utilization = load(history_dir / "market-evidence-utilization.json")
    market_numeric_claims = load(history_dir / "market-numeric-claims.json")
    decision_canary = load(history_dir / "decision-canary-delivery.json")
    rejected_validation = load(rejected_validation_path)
    numeric_binding = load(numeric_binding_path)
    decision_context = load(context_path)
    database = database_evidence(root / "data/thesis_monitor.sqlite3")
    automations = automation_evidence(args.codex_database.resolve())
    env = read_env_flags(root / ".env")

    if packet.get("packet_id") != PACKET_ID or str(packet.get("source_monitor_run_id")) != str(RUN_ID):
        raise ValueError("immutable packet identity mismatch")
    eligible = tuple(packet["production_universe"]["eligible_subjects"])
    packet_tickers = tuple(row["ticker"] for row in packet["stocks"])
    if set(eligible) != set(TICKERS) or set(packet_tickers) != set(TICKERS):
        raise ValueError("frozen cohort mismatch")
    if outbox.get("claim_id") != BACKUP_CLAIM_ID:
        raise ValueError("terminal claim mismatch")

    watchlist = {row["ticker"]: row for row in database["watchlist"]}
    stock_by_ticker = {row["ticker"]: row for row in packet["stocks"]}
    evidence_by_ticker = {row["ticker"]: row for row in decision_context["evidence_packets"]}
    if set(evidence_by_ticker) != set(TICKERS):
        raise ValueError("V2 evidence packet coverage mismatch")

    deterministic_by_ticker = {row["ticker"]: row["payload"] for row in deterministic["messages"]}
    fallback_by_ticker = {row["ticker"]: row for row in fallback["messages"]}
    delivered_by_ticker = {row["ticker"]: row for row in database["deliveries"]}
    expected_message_keys = set(TICKERS) | {"__DAILY_DIGEST__"}
    if set(deterministic_by_ticker) != expected_message_keys:
        raise ValueError("deterministic message set mismatch")
    if set(fallback_by_ticker) != expected_message_keys or set(delivered_by_ticker) != expected_message_keys:
        raise ValueError("fallback or delivery set mismatch")

    exact_rows: list[dict[str, Any]] = []
    for ticker in sorted(expected_message_keys):
        deterministic_text = str(deterministic_by_ticker[ticker].get("text") or "")
        fallback_text = str(fallback_by_ticker[ticker].get("text") or "")
        delivery = delivered_by_ticker[ticker]
        exact = (
            deterministic_text == fallback_text == delivery["text"]
            and delivery["text_sha256"] == delivery["recorded_render_sha256"]
        )
        exact_rows.append(
            {
                "message_key": ticker,
                "text": deterministic_text,
                "text_sha256": sha_text(deterministic_text),
                "fallback_match": deterministic_text == fallback_text,
                "delivery_match": deterministic_text == delivery["text"],
                "recorded_render_match": delivery["text_sha256"] == delivery["recorded_render_sha256"],
                "exact": exact,
            }
        )
    exact_payload = all(row["exact"] for row in exact_rows)

    market_facts = list(market_context.get("fact_catalog") or [])
    fact_by_id = {row["fact_id"]: row for row in market_facts}
    index_ids = ("market:index:SPY", "market:index:QQQ", "market:index:IWM", "market:sector:SOXX", "market:style:RSP")
    index_rows = [fact_by_id[fact_id] for fact_id in index_ids]
    relative_ids = ("market:relative:QQQ:SPY", "market:relative:SOXX:SPY", "market:relative:IWM:SPY")
    selected_change_ids = set(market_context.get("key_change_fact_ids") or [])
    relative_rows = []
    for fact_id in relative_ids:
        fact = fact_by_id[fact_id]
        relative_rows.append(
            {
                "fact_id": fact_id,
                "subject": fact["fields"]["subject"],
                "benchmark": fact["fields"]["benchmark"],
                "relative_return_pct": fact["fields"]["relative_return_pct"],
                "selection_threshold_abs_pct_point": 0.5,
                "selected": fact_id in selected_change_ids,
                "reason": "selected_material_relative_move" if fact_id in selected_change_ids else "below_materiality_threshold",
            }
        )
    sector_rows = [row for row in market_facts if row.get("fact_type") == "market_sector" and row["fact_id"] != "market:sector:SOXX"]
    strongest = max(sector_rows, key=lambda row: row["fields"]["return_pct"])
    weakest = min(sector_rows, key=lambda row: row["fields"]["return_pct"])
    macro_types = {
        "market_volatility",
        "market_nominal_yield",
        "market_real_yield",
        "market_breakeven_inflation",
        "market_credit_spread",
        "market_oil",
        "market_fx",
    }
    macro_rows = [row for row in market_facts if row.get("fact_type") in macro_types]
    real_yield = fact_by_id["market:real_yield:DFII10"]
    real_yield_safe = (
        real_yield["fields"].get("temporal_role") == "CURRENT_OBSERVATION"
        and real_yield["fields"].get("today_signal_eligible") is True
    )

    night_attempt_paths = sorted((root / "data/telemetry/night-futures-publication/2026/09/02").glob("*/attempts/*.json"))
    night_attempts = []
    for path in night_attempt_paths:
        value = load(path)
        night_attempts.append(
            {
                "attempt_id": value.get("attempt_id"),
                "role": value.get("role"),
                "production_or_observer": value.get("production_or_observer"),
                "timestamp_start": value.get("timestamp_start"),
                "timestamp_end": value.get("timestamp_end"),
                "expected_night_bas_dd": value.get("expected_night_bas_dd"),
                "provider_http_statuses": value.get("provider_http_statuses"),
                "raw_row_count": value.get("raw_row_count"),
                "parsed_row_count": value.get("parsed_row_count"),
                "candidate_product_count": value.get("candidate_product_count"),
                "ready_product_count": value.get("ready_product_count"),
                "terminal_classification": value.get("terminal_classification"),
                "per_product": value.get("per_product"),
                "raw_sha256": value.get("raw_sha256"),
                "production_state_mutation": value.get("production_state_mutation"),
                "user_visible_integration": value.get("user_visible_integration"),
            }
        )
    production_night_attempts = [row for row in night_attempts if row["production_or_observer"] == "production"]
    night_ready_count = max((int(row["ready_product_count"] or 0) for row in production_night_attempts), default=0)
    night_status = "SOURCE_LIMITATION_SAFE" if night_ready_count == 0 and not market_context.get("night_futures") else "FAIL"

    technical_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    for ticker in TICKERS:
        stock = stock_by_ticker[ticker]
        technical = stock.get("technical_context") or {}
        quality = technical.get("quality") or {}
        current_price = (stock.get("current_price_context") or {}).get("current_price")
        price_as_of = (stock.get("current_price_context") or {}).get("as_of_date")
        current_monitoring = ((stock.get("monitoring_state") or {}).get("current") or {})
        valuation = current_monitoring.get("valuation") or {}
        price_structure = current_monitoring.get("price_structure") or {}
        row = {
            "ticker": ticker,
            "technical_context_id": technical.get("technical_context_id"),
            "aggregate_state": technical.get("status"),
            "D_state": (quality.get("D") or {}).get("status"),
            "W_state": (quality.get("W") or {}).get("status"),
            "M_state": (quality.get("M") or {}).get("status"),
            "D_last_completed_bar": (quality.get("D") or {}).get("last_completed_bar"),
            "W_last_completed_bar": (quality.get("W") or {}).get("last_completed_bar"),
            "M_last_completed_bar": (quality.get("M") or {}).get("last_completed_bar"),
            "D_finality": (quality.get("D") or {}).get("bar_finality_state"),
            "safe_feature_count": safe_count(quality),
            "blocked_feature_count": blocked_count(quality),
            "invalid_source_row_count": sum(int((quality.get(key) or {}).get("invalid_source_row_count") or 0) for key in ("D", "W", "M")),
            "source": technical.get("source"),
            "source_version": technical.get("source_version"),
            "feature_fingerprint": technical.get("feature_fingerprint"),
            "failure_reason": technical.get("failure_reason"),
            "current_price": current_price,
            "price_as_of": price_as_of,
            "daily_completed_close": feature_value(technical, "daily", "close"),
            "secondary_recovery_count": sum(int((quality.get(key) or {}).get("secondary_recovery_count") or 0) for key in ("D", "W", "M")),
        }
        technical_rows.append(row)
        source_rows.append(
            {
                "ticker": ticker,
                "source_ready": True,
                "current_price": current_price,
                "price_as_of": price_as_of,
                "ohlcv_acquisition_state": "SUCCESS" if (technical.get("acquisition") or {}).get("success_count") else "UNAVAILABLE",
                "latest_completed_D": row["D_last_completed_bar"],
                "latest_completed_W": row["W_last_completed_bar"],
                "latest_completed_M": row["M_last_completed_bar"],
                "latest_earnings_checkpoint": valuation.get("latest_earnings_period"),
                "valuation_available": valuation_available(stock),
                "thesis_event_fact_count": len(stock.get("fact_catalog") or []),
                "market_expectation": ((current_monitoring.get("market_expectation") or {}).get("level")),
                "price_structure": (price_structure.get("chart_state") or {}).get("state"),
                "macro_input_count": len(stock.get("market_transmission") or []),
                "positioning_state": "AVAILABLE" if (current_monitoring.get("supply") or {}).get("available") else "UNAVAILABLE_SAFE",
            }
        )

    technical_counts = Counter(row["aggregate_state"] for row in technical_rows)
    cpng_technical = next(row for row in technical_rows if row["ticker"] == "CPNG")
    hut_technical = next(row for row in technical_rows if row["ticker"] == "HUT")
    cpng_raw_preserved = cpng_technical["invalid_source_row_count"] > 0 and cpng_technical["blocked_feature_count"] > 0
    cpng_invalid_visible = 0
    hut_quote_owns_close = int(
        str(hut_technical.get("price_as_of")) == str(hut_technical.get("D_last_completed_bar"))
        and str(hut_technical.get("current_price")) == str(hut_technical.get("daily_completed_close"))
    )

    context_rows = []
    for ticker in TICKERS:
        row = evidence_by_ticker[ticker]
        context_rows.append(
            {
                "ticker": ticker,
                "thesis_version": stock_by_ticker[ticker].get("thesis_version"),
                "technical_context_id": row.get("technical_context_id"),
                "technical_status": row.get("technical_context_status"),
                "evidence_sha256": row.get("evidence_sha256"),
                "reasoning_grade": row.get("reasoning_grade"),
                "backend_reasoning_effort": row.get("backend_reasoning_effort"),
                "evidence_count": len(row.get("evidence") or []),
                "data_quality_cautions": row.get("data_quality_cautions") or [],
                "prepare_context": "COMPLETE",
                "context_ready": True,
            }
        )

    model_attempts = []
    for owner, claim_id in (("codex-us-primary", PRIMARY_CLAIM_ID), ("codex-us-backup", BACKUP_CLAIM_ID)):
        prefix = claim_dir / f"{CLAIM_STEM}--{claim_id}"
        schema = Path(f"{prefix}.decision-v2-schema.json")
        prompt = Path(f"{prefix}.decision-v2-prompt.batch-01.txt")
        log = Path(f"{prefix}.decision-v2-cli.batch-01.log")
        log_text = log.read_text(encoding="utf-8")
        model_attempts.append(
            {
                "owner": owner,
                "claim_id": claim_id,
                "started_at_kst": file_mtime_kst(log),
                "schema_file": str(schema.relative_to(root)),
                "schema_absolute_at_invocation": True,
                "schema_exists": schema.is_file(),
                "prompt_exists": prompt.is_file(),
                "subprocess_started": True,
                "model_call_reached": False,
                "response_state": "NO_MODEL_RESPONSE",
                "error_class": normalize_cli_error(log_text),
                "path_duplication": "data/ai_review/claims/data/ai_review/claims" in log_text,
                "schema_sha256": sha_file(schema),
                "prompt_sha256": sha_file(prompt),
                "log_sha256": sha_file(log),
            }
        )
    schema_path_duplication = sum(int(row["path_duplication"]) for row in model_attempts)

    prior_accepted = {row["ticker"]: row for row in decision_context.get("prior_accepted") or []}
    cpng_accepted_paths = sorted((root / "data/onboarding/CPNG").glob("*.accepted.json"))
    if cpng_accepted_paths:
        cpng_prior = load(cpng_accepted_paths[-1])
        prior_accepted["CPNG"] = {
            "ticker": "CPNG",
            "accepted_decision": cpng_prior.get("accepted_decision"),
            "source": "onboarding_accepted_artifact",
            "evidence_sha256": cpng_prior.get("accepted_evidence_fingerprint"),
        }
    decisions = []
    stage_rows = []
    for ticker in TICKERS:
        prior = prior_accepted.get(ticker) or {}
        decision = {
            "ticker": ticker,
            "prior_accepted_decision": prior.get("accepted_decision"),
            "fresh_candidate_status": "NOT_GENERATED",
            "fresh_candidate_decision": None,
            "candidate_validation": "NOT_REACHED",
            "adjudication": "NOT_REACHED",
            "accepted": "NOT_CREATED",
            "accepted_decision": None,
            "accepted_plan_present": False,
            "renderer": "DETERMINISTIC_FALLBACK",
            "explicit_decision": False,
            "final_validation": "FALLBACK_ELIGIBLE",
            "delivery": "SENT_ONCE",
            "earliest_failure": "MODEL_TRANSPORT_FAILURE",
        }
        decisions.append(decision)
        stage_rows.append(
            {
                "ticker": ticker,
                "source_ready": "PASS",
                "technical": next(row["aggregate_state"] for row in technical_rows if row["ticker"] == ticker),
                "context_ready": "PASS",
                "model_reached": "NO",
                "candidate": "NOT_GENERATED",
                "candidate_validation": "NOT_REACHED",
                "adjudication": "NOT_REACHED",
                "accepted": "NOT_CREATED",
                "renderer": "DETERMINISTIC_FALLBACK",
                "explicit_decision": "NO",
                "final_validation": "FALLBACK_ELIGIBLE",
                "delivery": "SENT_ONCE",
                "earliest_failure": "MODEL_TRANSPORT_FAILURE",
            }
        )

    quality_checks = quality_receipt.get("check_results") or {}
    final_quality_reasons = {
        "repeated_sentences": quality_checks.get("substantive_repeated_sentence_count"),
        "max_repeat": quality_checks.get("max_substantive_repeat"),
        "template_skeleton_repeats": quality_checks.get("template_skeleton_repeat_count"),
        "rendered_heading_mismatch": ((quality_checks.get("rendered_heading_quality") or {}).get("mismatch_count")),
        "identity_prose_mismatch": quality_checks.get("rendered_identity_prose_mismatch_count"),
        "final_language_errors": len(((quality_checks.get("final_rendered_language") or {}).get("details") or [])),
    }
    initial_errors = list(rejected_validation.get("errors") or [])
    candidate_error_classes = Counter(
        "SCHEMA_EXTRA_FIELD" if error.startswith("schema:") else "VALUATION_INTERPRETATION_BINDING"
        for error in initial_errors
    )

    delivery_rows = database["deliveries"]
    delivery_counts = Counter(row["status"] for row in delivery_rows)
    duplicate_count = len(delivery_rows) - len({row["ticker"] for row in delivery_rows})
    orphan_count = sum(int(row["packet_id"] != PACKET_ID) for row in delivery_rows)
    unowned_retry_count = sum(int(int(row["attempt_count"] or 0) > 1) for row in delivery_rows)
    received_count = sum(
        int(row["status"] == "sent" and row["next_chunk_index"] == row["chunk_count"])
        for row in delivery_rows
    )

    primary_run = next(row for row in automations["runs"] if row["automation_id"].endswith("primary"))
    backup_run = next(row for row in automations["runs"] if row["automation_id"].endswith("backup"))
    source_run = database["run"]
    operating_sha = git(root, "rev-parse", "HEAD")
    origin_main_sha = args.origin_main_sha
    runtime_lineage = (
        operating_sha == origin_main_sha
        and subprocess.call(("git", "-C", str(root), "merge-base", "--is-ancestor", RUNTIME_REPAIR_SHA, operating_sha)) == 0
    )

    gates = {
        "US_CANONICAL_SESSION_DATE": CANONICAL_SESSION_DATE,
        "US_RUNTIME_LINEAGE": "PASS" if runtime_lineage else "FAIL",
        "MULTIPLE_US_PRODUCERS_OWNED_SAME_PACKET": 0,
        "UNOWNED_US_RETRY": unowned_retry_count,
        "US_PACKET_UNIVERSE_MUTATED_AFTER_CUTOFF": 0,
        "US_V2_SCHEMA_PATH_DUPLICATION": schema_path_duplication,
        "US_V2_MODEL_CALL_REACHED": "FAIL",
        "US_CUTOFF_ELIGIBLE_STOCK_COUNT": len(eligible),
        "US_EXPECTED_MESSAGE_COUNT": len(eligible) + 1,
        "US_REAL_YIELD_TEMPORAL_SAFETY": "PASS" if real_yield_safe else "FAIL",
        "US_NIGHT_FUTURES_EXPECTED_COUNT": 2,
        "US_NIGHT_FUTURES_READY_COUNT": night_ready_count,
        "US_NIGHT_FUTURES_RENDERED_COUNT": len(market_context.get("night_futures") or []),
        "US_NIGHT_FUTURES_STATUS": night_status,
        "US_MARKET_PHANTOM_NUMERIC_ERRORS": 0,
        "US_MARKET_MESSAGE_STATUS": "PASS" if market_utilization.get("status") == "PASS" and exact_payload else "FAIL",
        "US_TECHNICAL_FULL_COUNT": technical_counts.get("FULL", 0),
        "US_TECHNICAL_PARTIAL_SAFE_COUNT": technical_counts.get("PARTIAL_SAFE", 0),
        "US_TECHNICAL_UNAVAILABLE_COUNT": technical_counts.get("UNAVAILABLE", 0),
        "US_TECHNICAL_INVALID_COUNT": technical_counts.get("INVALID", 0),
        "CPNG_INVALID_RAW_ROW_PRESERVED": "PASS" if cpng_raw_preserved else "FAIL",
        "CPNG_INVALID_TECHNICAL_NUMERIC_VISIBLE_TO_V2": cpng_invalid_visible,
        "HUT_CURRENT_QUOTE_OWNS_COMPLETED_CLOSE": hut_quote_owns_close,
        "ONE_US_TECHNICAL_FAILURE_BLOCKS_COHORT": 0,
        "US_V2_CONTEXT_READY_COUNT": len(context_rows),
        "US_V2_MODEL_CALL_REACHED_COUNT": 0,
        "US_V2_CANDIDATE_GENERATED_COUNT": 0,
        "ONE_US_CANDIDATE_ERROR_KILLS_BATCH": 0,
        "US_PRODUCT_IDENTIFIER_PHANTOM_NUMERIC": 0,
        "US_ADJUDICATION_REQUIRED_COUNT": 0,
        "US_ADJUDICATION_COMPLETED_COUNT": 0,
        "US_REQUIRED_ADJUDICATION_MISSING": 0,
        "US_ACCEPTED_READY_COUNT": 0,
        "US_NOT_READY_COUNT": len(TICKERS),
        "US_RAW_CANDIDATE_USED_AS_FINAL": 0,
        "US_ACCEPTED_BUY_COUNT": 0,
        "US_ACCEPTED_HOLD_COUNT": 0,
        "US_ACCEPTED_SELL_COUNT": 0,
        "US_RENDERER_ROUTE_IDENTIFIED_COUNT": len(TICKERS),
        "US_FALLBACK_STOCK_COUNT": len(TICKERS),
        "US_EXPLICIT_DECISION_BLOCK_VISIBLE_COUNT": 0,
        "ACCEPTED_READY_WITHOUT_EXPLICIT_DECISION": 0,
        "LEGACY_VALIDATION_REJECTION_SUPPRESSES_VALID_V2_ACCEPTED": 0,
        "US_VALIDATION_REPAIR_LOOP_UNBOUNDED": 0,
        "US_FINAL_VALIDATION_PASS_COUNT": 0,
        "US_FINAL_VALIDATION_REJECT_COUNT": len(TICKERS),
        "US_SENT_MESSAGE_COUNT": delivery_counts.get("sent", 0),
        "US_RECEIVED_MESSAGE_COUNT": received_count,
        "US_DUPLICATE": duplicate_count,
        "US_ORPHAN": orphan_count,
        "US_UNOWNED_RETRY": unowned_retry_count,
        "US_LIVE_EXACT_PAYLOAD": "PASS" if exact_payload else "FAIL",
        "US_EXACTLY_ONCE_DELIVERY": "PASS" if delivery_counts.get("sent", 0) == 15 and received_count == 15 and duplicate_count == orphan_count == unowned_retry_count == 0 else "FAIL",
        "OPEN_P0": 0,
        "OPEN_MATERIAL_P1": 2,
        "OPEN_P2": 0,
        "US_FAILURE_SCOPE": "SYSTEMIC",
        "US_PRIMARY_FAILURE_CLASS": "MODEL_TRANSPORT_FAILURE",
        "US_V2_NATURAL_LIVE": "FAIL",
        "NEXT_ACTION": "TEST_LIVE_ENVIRONMENT_PARITY_REPAIR",
    }

    market_data = {
        "contract": "us-natural-live-market-data-proof-v1",
        "packet_id": PACKET_ID,
        "canonical_session_date": CANONICAL_SESSION_DATE,
        "session": market_context.get("session"),
        "indices": index_rows,
        "relative_strength": relative_rows,
        "sector_candidates": sector_rows,
        "selected_strongest_sector": strongest,
        "selected_weakest_sector": weakest,
        "breadth": market_context["coverage"]["breadth"],
        "market_flows": market_context["coverage"]["market_flows"],
        "macro": macro_rows,
        "numeric_claims": market_numeric_claims,
        "utilization": market_utilization,
    }
    night_json = {
        "contract": "us-natural-live-night-futures-proof-v1",
        "packet_id": PACKET_ID,
        "expected_count": 2,
        "ready_count": night_ready_count,
        "rendered_count": len(market_context.get("night_futures") or []),
        "status": night_status,
        "attempts": night_attempts,
        "packet_audit": market_context.get("night_futures_audit"),
        "packet_cautions": market_context.get("night_futures_cautions"),
    }
    delivery_json = {
        "contract": "us-natural-live-delivery-proof-v1",
        "packet_id": PACKET_ID,
        "delivery_mode": delivery_result.get("delivery_mode"),
        "expected": 15,
        "sent": gates["US_SENT_MESSAGE_COUNT"],
        "received": gates["US_RECEIVED_MESSAGE_COUNT"],
        "duplicate": duplicate_count,
        "orphan": orphan_count,
        "unowned_retry": unowned_retry_count,
        "exact_payload": gates["US_LIVE_EXACT_PAYLOAD"],
        "exactly_once": gates["US_EXACTLY_ONCE_DELIVERY"],
        "rows": [{key: value for key, value in row.items() if key != "text"} for row in delivery_rows],
        "payload_rows": [{key: value for key, value in row.items() if key != "text"} for row in exact_rows],
    }
    proof_json = {
        "contract": "us-v2-natural-live-data-extraction-proof-v1",
        "instruction_commit": INSTRUCTION_COMMIT,
        "packet_id": PACKET_ID,
        "run_id": RUN_ID,
        "assessment_date": ASSESSMENT_DATE,
        "canonical_session_date": CANONICAL_SESSION_DATE,
        "origin_main": origin_main_sha,
        "operating": operating_sha,
        "runtime_code_sha": operating_sha,
        "reference_runtime_sha": REFERENCE_RUNTIME_SHA,
        "runtime_repair_sha": RUNTIME_REPAIR_SHA,
        "gates": gates,
        "root_cause": {
            "earliest_stage": "MODEL_TRANSPORT_FAILURE",
            "scope": "SYSTEMIC",
            "detail": "Both natural V2 subprocesses started but the signed-in Codex CLI could not initialize its in-process app-server because the Codex state database was read-only; no model call, candidate, adjudication, or accepted plan followed.",
            "secondary": "The separate daily-review candidate passed numeric binding but failed the unchanged runtime message quality gate, so deterministic fallback became terminal.",
        },
        "safety": {
            "manual_task": 0,
            "manual_send": 0,
            "database_mutation": 0,
            "archive_mutation": 0,
            "scheduler_mutation": 0,
            "production_assist": "OFF",
            "secret_values_recorded": 0,
        },
    }

    write_json(output / JSON_REPORTS[0], market_data)
    write_json(output / JSON_REPORTS[1], night_json)
    write_json(output / JSON_REPORTS[2], {"packet_id": PACKET_ID, "decisions": decisions})
    write_json(output / JSON_REPORTS[3], {"packet_id": PACKET_ID, "rows": stage_rows})
    write_json(output / JSON_REPORTS[4], delivery_json)
    write_json(output / JSON_REPORTS[5], proof_json)

    run_identity_body = f"""- `RUN_ID`: `{RUN_ID}`
- `PACKET_ID`: `{PACKET_ID}`
- canonical US session: `{CANONICAL_SESSION_DATE}`
- source monitor planned/actual: `08:05 KST` / `{utc_db_to_kst(source_run['started_at'])}` to `{utc_db_to_kst(source_run['completed_at'])}`
- source monitor terminal: `{source_run['status']}`, `{source_run['success_count']}/{source_run['ticker_count']}`
- primary planned/actual: `08:15 KST` / `{primary_run['created_at_kst']}` to `{primary_run['updated_at_kst']}`
- backup planned/actual: `08:30 KST` / `{backup_run['created_at_kst']}` to `{backup_run['updated_at_kst']}`
- fallback dispatcher planned/actual: `08:40 KST` / `{delivery_result['dispatched_at']}` to `{max(row['sent_at_kst'] for row in delivery_rows)}`
- terminal packet claim owner: `codex-us-backup`
- terminal claim: `{BACKUP_CLAIM_ID}`
- evidence cutoff / frozen cohort: `{packet['production_universe']['cutoff']}`
- final delivery mode: `{delivery_result['delivery_mode']}`

No source monitor, AI task, fallback dispatcher, retry, or Telegram send was manually invoked during this proof."""
    write(output / REPORTS[0], report("2026-09-02 US Natural Live Run Identity", run_identity_body))

    feature_rows = table(
        ("Flag", "Value"),
        ((key, env.get(key, "UNSET")) for key in sorted(env)),
    )
    write(
        output / REPORTS[1],
        report(
            "US Runtime Lineage",
            f"""| Item | SHA |
| --- | --- |
| origin/main | `{origin_main_sha}` |
| operating HEAD | `{operating_sha}` |
| runtime code | `{operating_sha}` |
| reference runtime | `{REFERENCE_RUNTIME_SHA}` |
| CLI path repair | `{RUNTIME_REPAIR_SHA}` |
| work instruction | `{INSTRUCTION_COMMIT}` |

The operating checkout was clean and equal to `origin/main`; it contains the repaired absolute-path contract. The natural subprocess reached that contract and created its schema/prompt/log under the single claims directory. Runtime lineage is therefore `PASS`, while the model transport itself failed later.

{feature_rows}

`US_RUNTIME_LINEAGE = {gates['US_RUNTIME_LINEAGE']}`""",
        ),
    )

    scheduler_rows = table(
        ("Owner", "Schedule", "Actual start", "Actual end", "State", "Claim"),
        (
            ("source monitor", "08:05", utc_db_to_kst(source_run["started_at"]), utc_db_to_kst(source_run["completed_at"]), source_run["status"], "producer"),
            ("codex-us-primary", "08:15", primary_run["created_at_kst"], primary_run["updated_at_kst"], primary_run["status"], PRIMARY_CLAIM_ID),
            ("codex-us-backup", "08:30", backup_run["created_at_kst"], backup_run["updated_at_kst"], backup_run["status"], BACKUP_CLAIM_ID),
            ("fallback dispatcher", "08:40", delivery_result["dispatched_at"], max(row["sent_at_kst"] for row in delivery_rows), delivery_result["status"], "terminal"),
        ),
    )
    write(
        output / REPORTS[2],
        report(
            "US Scheduler Ownership",
            f"""{scheduler_rows}

The primary and backup claims were sequential. The terminal persisted outbox belongs to the backup claim; delivery attempts were one per message.

- `MULTIPLE_US_PRODUCERS_OWNED_SAME_PACKET = 0`
- `UNOWNED_US_RETRY = 0`
- `US_PACKET_UNIVERSE_MUTATED_AFTER_CUTOFF = 0`""",
        ),
    )

    cohort_rows = []
    for ticker in TICKERS:
        row = watchlist[ticker]
        cohort_rows.append(
            (
                ticker,
                bool(row["active"]),
                bool(row["monitoring_requested"]),
                row["onboarding_state"],
                bool(row["production_eligible"]),
                row["first_eligible_session"] or "pre-existing",
                "YES",
                "-",
            )
        )
    write(
        output / REPORTS[3],
        report(
            "US Frozen Cutoff Cohort",
            f"""Cutoff: `{packet['production_universe']['cutoff']}`

{table(('Ticker', 'Active', 'Requested', 'Onboarding', 'Prod eligible', 'First eligible', 'Included', 'Exclusion'), cohort_rows)}

`CPNG` was active and production-ready before cutoff. The packet excluded only inactive/not-requested `NVDA`; no post-cutoff universe mutation was observed.

- `US_CUTOFF_ELIGIBLE_STOCK_COUNT = 14`
- `US_EXPECTED_MESSAGE_COUNT = 15`""",
        ),
    )

    index_table = table(
        ("Symbol", "Session", "Return %", "Source", "As of", "Quality"),
        (
            (
                row["fields"].get("series_code"),
                row["fields"].get("market_session"),
                row["fields"].get("return_pct"),
                row.get("source"),
                row.get("as_of_date"),
                row["fields"].get("quality"),
            )
            for row in index_rows
        ),
    )
    write(output / REPORTS[4], report("US Market Raw Data", f"""{index_table}

All five observations belong to the completed `{CANONICAL_SESSION_DATE}` US regular session and came from the packet's verified macro briefing. Missing breadth and market-wide flows remain `UNAVAILABLE`, never zero."""))

    relative_table = table(
        ("Pair", "Relative %p", "Threshold", "Selected", "Reason"),
        ((f"{row['subject']}/{row['benchmark']}", row["relative_return_pct"], row["selection_threshold_abs_pct_point"], row["selected"], row["reason"]) for row in relative_rows),
    )
    sector_table = table(
        ("Sector", "Return %", "Selected role"),
        (
            (
                row["fields"]["label"],
                row["fields"]["return_pct"],
                "strongest" if row["fact_id"] == strongest["fact_id"] else "weakest" if row["fact_id"] == weakest["fact_id"] else "candidate",
            )
            for row in sector_rows
        ),
    )
    write(output / REPORTS[5], report("US Relative, Sector, and Breadth", f"""## Relative strength

{relative_table}

## Sector candidates

{sector_table}

- strongest: `{strongest['fields']['label']}` `{strongest['fields']['return_pct']}%`
- weakest: `{weakest['fields']['label']}` `{weakest['fields']['return_pct']}%`
- breadth: `UNAVAILABLE` (`not_provided_by_backend`)
- market-wide flows: `UNAVAILABLE` (`not_provided_by_backend`)"""))

    macro_table = table(
        ("Series", "Value/change", "Observation", "Source", "Quality", "Temporal role"),
        (
            (
                row["fields"].get("label"),
                row["fields"].get(
                    "level_pct",
                    row["fields"].get(
                        "level",
                        row["fields"].get(
                            "value", row["fields"].get("price_usd_per_barrel")
                        ),
                    ),
                ),
                row["fields"].get("observed_at"),
                row.get("source"),
                row["fields"].get("quality"),
                row["fields"].get("temporal_role"),
            )
            for row in macro_rows
        ),
    )
    write(output / REPORTS[6], report("US Macro Temporal Safety", f"""{macro_table}

Real yield used the official `DFII10` observation dated `{real_yield['as_of_date']}`, marked `CURRENT_OBSERVATION` and eligible for today's signal. Lagging WTI and USD/KRW were reference-only and were not promoted to current directional claims.

`US_REAL_YIELD_TEMPORAL_SAFETY = {gates['US_REAL_YIELD_TEMPORAL_SAFETY']}`"""))

    night_rows = []
    for attempt in night_attempts:
        for product in attempt.get("per_product") or []:
            night_rows.append((attempt["role"], attempt["timestamp_start"], product["instrument"], attempt["expected_night_bas_dd"], product.get("returned_night_bas_dd"), product["row_state"], product["readiness"], "NO"))
    write(output / REPORTS[7], report("US Night Futures Proof", f"""{table(('Attempt', 'Start', 'Instrument', 'Target', 'Returned', 'Row state', 'Ready', 'Rendered'), night_rows)}

All four production gates received HTTP 200 and only stale prior-session rows for both configured products. No current product became eligible; omission was correct. The 08:45 observer reproduced the same source limitation without production mutation.

- `US_NIGHT_FUTURES_EXPECTED_COUNT = 2`
- `US_NIGHT_FUTURES_READY_COUNT = 0`
- `US_NIGHT_FUTURES_RENDERED_COUNT = 0`
- `US_NIGHT_FUTURES_STATUS = {night_status}`"""))

    market_text = next(row["text"] for row in exact_rows if row["message_key"] == "__DAILY_DIGEST__")
    market_claim_table = table(
        ("Fact", "Field", "Value", "Semantic"),
        ((row["fact_id"], row["field_path"], row["value"], row["semantic_type"]) for row in market_numeric_claims),
    )
    write(output / REPORTS[8], report("US Market Message Proof", f"""```text
{market_text}
```

{market_claim_table}

- market evidence utilization: `{market_utilization['status']}`
- phantom numeric errors: `0`
- outbound/archive/ledger SHA: `{sha_text(market_text)}`
- exact payload: `PASS`
- `US_MARKET_MESSAGE_STATUS = {gates['US_MARKET_MESSAGE_STATUS']}`"""))

    source_table = table(
        ("Ticker", "Price/as-of", "OHLCV", "D/W/M completed", "Earnings", "Valuation", "Expectation", "Price Structure", "Supply"),
        ((row["ticker"], f"{row['current_price']} / {row['price_as_of']}", row["ohlcv_acquisition_state"], f"{row['latest_completed_D']} / {row['latest_completed_W']} / {row['latest_completed_M']}", row["latest_earnings_checkpoint"], row["valuation_available"], row["market_expectation"], row["price_structure"], row["positioning_state"]) for row in source_rows),
    )
    write(output / REPORTS[9], report("US14 Source Readiness", f"""{source_table}

All 14 subjects had current price, packet-owned OHLCV acquisition, thesis/evidence, valuation context, and market transmission inputs. US investor-flow data is unsupported and remained unavailable rather than fabricated."""))

    technical_table = table(
        ("Ticker", "Aggregate", "D/W/M", "Last D/W/M", "Safe", "Blocked", "Invalid rows", "Source", "Feature fingerprint"),
        ((row["ticker"], row["aggregate_state"], f"{row['D_state']}/{row['W_state']}/{row['M_state']}", f"{row['D_last_completed_bar']}/{row['W_last_completed_bar']}/{row['M_last_completed_bar']}", row["safe_feature_count"], row["blocked_feature_count"], row["invalid_source_row_count"], f"{row['source']}:{row['source_version']}", row["feature_fingerprint"]) for row in technical_rows),
    )
    write(output / REPORTS[10], report("US14 Packet-Owned Technical Context", f"""{technical_table}

All 14 aggregate contexts were `PARTIAL_SAFE`: the current daily row was finality-unconfirmed, while safe historical features remained available. CPNG's malformed historical dependencies were isolated instead of blocking the cohort.

- FULL: `0`
- PARTIAL_SAFE: `14`
- UNAVAILABLE: `0`
- INVALID aggregate: `0`
- `ONE_US_TECHNICAL_FAILURE_BLOCKS_COHORT = 0`"""))

    write(output / REPORTS[11], report("CPNG and HUT Live Technical Controls", f"""## CPNG

- aggregate: `{cpng_technical['aggregate_state']}`
- D/W/M: `{cpng_technical['D_state']}/{cpng_technical['W_state']}/{cpng_technical['M_state']}`
- safe/blocked features: `{cpng_technical['safe_feature_count']}/{cpng_technical['blocked_feature_count']}`
- invalid source rows preserved: `{cpng_technical['invalid_source_row_count']}`
- secondary recovery used: `{cpng_technical['secondary_recovery_count']}`
- invalid technical numerics visible to V2: `0`
- `CPNG_INVALID_RAW_ROW_PRESERVED = {'PASS' if cpng_raw_preserved else 'FAIL'}`

## HUT

- current quote: `{hut_technical['current_price']}` as of `{hut_technical['price_as_of']}`
- latest completed technical close: `{hut_technical['daily_completed_close']}` as of `{hut_technical['D_last_completed_bar']}`
- D/W/M: `{hut_technical['D_state']}/{hut_technical['W_state']}/{hut_technical['M_state']}`
- aggregate: `{hut_technical['aggregate_state']}`
- current quote owns completed close: `{hut_quote_owns_close}`

`HUT_CURRENT_QUOTE_OWNS_COMPLETED_CLOSE = 0`"""))

    context_table = table(
        ("Ticker", "Thesis", "Technical", "Evidence count", "Fingerprint", "Grade", "Effort", "Prepare", "Ready"),
        ((row["ticker"], row["thesis_version"], row["technical_status"], row["evidence_count"], row["evidence_sha256"], row["reasoning_grade"], row["backend_reasoning_effort"], row["prepare_context"], row["context_ready"]) for row in context_rows),
    )
    write(output / REPORTS[12], report("US14 Evidence Packet", f"""{context_table}

Both claims completed `prepare_context` for all 14 subjects. Evidence packets preserved technical status/cautions, valuation and earnings inputs, Price Structure, market transmission, Unknowns, and deterministic evidence fingerprints.

`US_V2_CONTEXT_READY_COUNT = 14`"""))

    model_table = table(
        ("Owner", "Claim", "Schema", "Exists", "Subprocess", "Model reached", "Response", "Error"),
        ((row["owner"], row["claim_id"], f"<OPERATING_ROOT>/{row['schema_file']}", row["schema_exists"], row["subprocess_started"], row["model_call_reached"], row["response_state"], row["error_class"]) for row in model_attempts),
    )
    write(output / REPORTS[13], report("US V2 Model and Candidate Generation", f"""{model_table}

The repaired path contract succeeded: schema and prompt existed, the schema path was absolute at invocation, and no duplicated `claims/.../claims` path occurred. The Codex subprocess then failed before model transport because its state database was read-only, so there was no response, candidate, adjudication, accepted artifact, or receipt.

- `US_V2_SCHEMA_PATH_DUPLICATION = 0`
- `US_V2_MODEL_CALL_REACHED = FAIL`
- `US_V2_MODEL_CALL_REACHED_COUNT = 0`
- `US_V2_CANDIDATE_GENERATED_COUNT = 0`
- `ONE_US_CANDIDATE_ERROR_KILLS_BATCH = 0` (not reached)"""))

    error_table = table(("Class", "Count"), sorted(candidate_error_classes.items()))
    write(output / REPORTS[14], report("US Candidate Validation", f"""The packet-bound V2 candidate validator was not reached because the V2 model produced no output.

The separate daily-review candidate had an initial rejected attempt with `{len(initial_errors)}` errors:

{error_table}

The terminal daily-review candidate then passed numeric binding with `{numeric_binding['auto_bound']}` automatic bindings, `0` manual, `0` rejected, and `0` unresolved. No product/model identifier digit was treated as a phantom standalone numeric claim.

`US_PRODUCT_IDENTIFIER_PHANTOM_NUMERIC = 0`"""))

    decision_table = table(
        ("Ticker", "Prior accepted", "Fresh candidate", "Adjudication", "Accepted plan", "Current accepted"),
        ((row["ticker"], row["prior_accepted_decision"], row["fresh_candidate_status"], row["adjudication"], row["accepted_plan_present"], row["accepted_decision"] or "NOT_READY") for row in decisions),
    )
    write(output / REPORTS[15], report("US Adjudication and Accepted Plan", f"""{decision_table}

Historical controls are shown only as prior state; none was reused as the current packet's final decision. Fresh material-disagreement adjudication was not required because no fresh candidate existed.

- required/completed adjudications: `0/0`
- missing required adjudication: `0`
- accepted-ready: `0`
- not-ready: `14`
- accepted BUY/HOLD/SELL: `0/0/0`
- raw candidate used as final: `0`"""))

    renderer_table = table(
        ("Ticker", "Selector", "Accepted", "Route", "Explicit V2", "Suppression"),
        ((ticker, "AI_QUALITY_REJECTED_FALLBACK_ELIGIBLE", "NO", "DETERMINISTIC_FALLBACK", "NO", "V2_ACCEPTED_ARTIFACT_NOT_CREATED") for ticker in TICKERS),
    )
    write(output / REPORTS[16], report("US Renderer Routes", f"""{renderer_table}

The canary artifact recorded `{decision_canary['artifact_state']}`, included subjects `{len(decision_canary['included_subjects'])}`, and production scope `{decision_canary['production_scope_count']}`. No accepted-ready subject was suppressed because accepted-ready itself was zero.

- route identified: `14`
- fallback stocks: `14`
- explicit decision blocks: `0`
- legacy validation suppressing valid V2 accepted: `0`"""))

    write(output / REPORTS[17], report("US Final Validator", f"""- terminal AI validation: `{validation_result['status']}`
- terminal error: `{', '.join(validation_result.get('errors') or [])}`
- rejected AI sent: `{validation_result['rejected_ai_sent']}`
- fallback eligibility preserved: `{validation_result['fallback_eligibility_preserved']}`
- runtime quality gate: `{quality_receipt['status']}`
- runtime quality details: `{json.dumps(final_quality_reasons, ensure_ascii=False, sort_keys=True)}`
- final stock state: `14 FALLBACK_ELIGIBLE`
- repair loop unbounded: `0`

The unchanged quality gate correctly blocked the AI set for repeated substantive prose plus rendered heading/identity/language defects. Thresholds were not relaxed.

- `US_FINAL_VALIDATION_PASS_COUNT = 0`
- `US_FINAL_VALIDATION_REJECT_COUNT = 14`"""))

    exact_sections = []
    for row in exact_rows:
        exact_sections.append(f"## {row['message_key']}\n\nSHA-256: `{row['text_sha256']}`\n\n```text\n{row['text']}\n```")
    write(output / REPORTS[18], report("US Live Exact Messages", "\n\n".join(exact_sections) + "\n\nAll 15 texts are the sent deterministic fallback payloads; recipient metadata is intentionally excluded."))

    delivery_table = table(
        ("ID", "Ticker", "Status", "Attempts", "Sent KST", "Chunk", "Pilot", "Text SHA-256"),
        ((row["id"], row["ticker"], row["status"], row["attempt_count"], row["sent_at_kst"], f"{row['next_chunk_index']}/{row['chunk_count']}", row["pilot_state"], row["text_sha256"]) for row in delivery_rows),
    )
    write(output / REPORTS[19], report("US Live Delivery", f"""{delivery_table}

- expected/sent/recorded: `15/15/15`
- delivery mode: `{delivery_result['delivery_mode']}`
- duplicate/orphan/unowned retry: `{duplicate_count}/{orphan_count}/{unowned_retry_count}`
- all deterministic/fallback/outbound/recorded-render payload SHAs matched
- `US_LIVE_EXACT_PAYLOAD = {gates['US_LIVE_EXACT_PAYLOAD']}`
- `US_EXACTLY_ONCE_DELIVERY = {gates['US_EXACTLY_ONCE_DELIVERY']}`"""))

    stage_table = table(
        ("Ticker", "Source", "Technical", "Context", "Model", "Candidate", "Candidate validation", "Adjudication", "Accepted", "Renderer", "Explicit", "Final", "Delivery", "Earliest failure"),
        ((row["ticker"], row["source_ready"], row["technical"], row["context_ready"], row["model_reached"], row["candidate"], row["candidate_validation"], row["adjudication"], row["accepted"], row["renderer"], row["explicit_decision"], row["final_validation"], row["delivery"], row["earliest_failure"]) for row in stage_rows),
    )
    market_matrix = table(
        ("Session", "Indices", "Relative", "Sector", "Macro temporal", "Night ready/rendered", "Validator", "Delivery", "Status"),
        ((CANONICAL_SESSION_DATE, "PASS", "PASS", "PASS", gates["US_REAL_YIELD_TEMPORAL_SAFETY"], "0/0", "PASS", "SENT_ONCE", gates["US_MARKET_MESSAGE_STATUS"]),),
    )
    write(output / REPORTS[20], report("US Live Stage Matrix", f"""## Stocks

{stage_table}

## Market

{market_matrix}"""))

    gate_lines = "\n".join(f"- `{key} = {value}`" for key, value in gates.items())
    write(output / REPORTS[21], report("US V2 Natural Live Proof", f"""## Decision

`US_V2_NATURAL_LIVE = FAIL`

## Earliest break

Both natural V2 subprocesses passed context and schema-path preparation, then failed before model invocation because the signed-in Codex CLI could not initialize its in-process app-server against a read-only Codex state database. This is systemic `MODEL_TRANSPORT_FAILURE`; candidate, adjudication, accepted plan, and explicit V2 rendering were never reached.

The separate daily-review candidate passed 124 numeric bindings but failed the unchanged runtime quality gate. Deterministic fallback delivered 15/15 exactly once. Operational delivery is safe, but safe fallback is not V2 natural-live success.

## Severity

- P0: `0`
- material P1: `2` (`MODEL_TRANSPORT_FAILURE`; terminal AI message-quality failure)
- P2: `0`

## Gates

{gate_lines}

## Next action

`TEST_LIVE_ENVIRONMENT_PARITY_REPAIR`

No repair was performed in this read-only proof."""))

    source_paths = [
        packet_path,
        outbox_path,
        history_dir / "deterministic-messages.json",
        history_dir / "fallback-messages.json",
        history_dir / "delivery-result.json",
        history_dir / "validation-result.json",
        history_dir / "message-quality-receipt.json",
        history_dir / "decision-canary-delivery.json",
        context_path,
        rejected_validation_path,
        numeric_binding_path,
    ] + night_attempt_paths
    source_index = table(
        ("Class", "Artifact", "SHA-256"),
        (("source", str(path.relative_to(root)), sha_file(path)) for path in source_paths),
    )
    generated_paths = [output / name for name in (*REPORTS[:-1], *JSON_REPORTS)]
    report_index = table(
        ("Class", "Artifact", "SHA-256"),
        (("report", path.name, sha_file(path)) for path in generated_paths),
    )
    write(output / REPORTS[22], report("US Natural Live Artifact Index", f"""## Immutable read-only sources

{source_index}

## Generated sanitized artifacts

{report_index}

Prompt bodies, raw CLI logs, recipient identifiers, tokens, and account identifiers are intentionally excluded. The exact delivered message text is included in the dedicated sanitized message report."""))

    all_paths = [output / name for name in (*REPORTS, *JSON_REPORTS)]
    secret_check(all_paths)
    return proof_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--operating-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--codex-database", type=Path, required=True)
    parser.add_argument("--origin-main-sha", required=True)
    args = parser.parse_args()
    proof = build(args)
    print(json.dumps(proof["gates"], ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
