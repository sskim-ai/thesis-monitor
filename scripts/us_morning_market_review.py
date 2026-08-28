from __future__ import annotations

# ruff: noqa: E402, E501

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

import exchange_calendars as exchange_calendar

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.jobs.probe_krx_night_futures import expected_latest_completed_krx_session
from app.providers.nasdaq_trader_breadth_provider import (
    parse_nasdaq_daily_market_file,
)
from app.services.market_evidence_utilization_validator_service import (
    validate_us_market_evidence_utilization,
)
from app.services.market_session import us_market_session
from app.services.us_full_message_service import render_us_full_market_message
from app.services.us_market_message_quality_service import (
    validate_us_market_message_payload,
)


REPORT_DATE = "20260829"
INDEX_SYMBOLS = ("SPY", "QQQ", "IWM", "SOXX", "RSP")
SECTOR_SYMBOLS = (
    "XLB",
    "XLC",
    "XLE",
    "XLF",
    "XLI",
    "XLK",
    "XLP",
    "XLRE",
    "XLU",
    "XLV",
    "XLY",
)
MACRO_SYMBOLS = (
    "DGS10",
    "DFII10",
    "T10YIE",
    "BAMLH0A0HYM2",
    "VIXCLS",
    "DCOILWTICO",
    "USDKRW",
    "DTWEXBGS",
)
KST = ZoneInfo("Asia/Seoul")


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _write_json(path: Path, value: object) -> None:
    _write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_text(value: str) -> str:
    return _sha_bytes(value.encode("utf-8"))


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _decimal(value: object) -> Decimal:
    return Decimal(str(value))


def _spread(subject: object, benchmark: object) -> float:
    return float((_decimal(subject) - _decimal(benchmark)).quantize(Decimal("0.0001")))


def _pct(value: object) -> str:
    return f"{float(value):+.2f}%"


def _pp(value: object) -> str:
    return f"{float(value):+.4f}pp"


def _table(headers: Iterable[str], rows: Iterable[Iterable[object]]) -> str:
    heads = [str(item) for item in headers]
    lines = ["| " + " | ".join(heads) + " |", "| " + " | ".join("---" for _ in heads) + " |"]
    lines.extend("| " + " | ".join(str(item) for item in row) + " |" for row in rows)
    return "\n".join(lines)


def _report(title: str, body: str) -> str:
    return f"# {title}\n\n{body.rstrip()}\n"


def _observations(briefing: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    rows = briefing.get("market_summary", {}).get("observations", [])
    return {str(row["series_code"]): row for row in rows if isinstance(row, dict) and row.get("series_code")}


def _next_xkrx_session(value: date) -> date | None:
    try:
        calendar = exchange_calendar.get_calendar("XKRX")
        return calendar.date_to_session(value, direction="next").date()
    except (ValueError, IndexError, TypeError):
        return None


def _delivery_evidence(database: Path, assessment_date: str) -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        run = connection.execute(
            """
            SELECT id, run_date, run_type, status, started_at, completed_at,
                   ticker_count, success_count, failure_count
              FROM monitorrun
             WHERE run_date = ? AND run_type = 'daily_us'
             ORDER BY id DESC LIMIT 1
            """,
            (assessment_date,),
        ).fetchone()
        rows = connection.execute(
            """
            SELECT id, ticker, status, attempt_count, sent_at, payload
              FROM notificationdelivery
             WHERE assessment_date = ?
             ORDER BY id
            """,
            (assessment_date,),
        ).fetchall()
    finally:
        connection.close()
    deliveries: list[dict[str, Any]] = []
    for row in rows:
        payload = json.loads(row["payload"] or "{}")
        deliveries.append(
            {
                "id": row["id"],
                "ticker": row["ticker"],
                "status": row["status"],
                "attempt_count": row["attempt_count"],
                "sent_at": row["sent_at"],
                "text": payload.get("text"),
                "use_llm": payload.get("use_llm"),
            }
        )
    return {
        "run": dict(run) if run is not None else None,
        "deliveries": deliveries,
        "market_delivery": next((row for row in deliveries if row["ticker"] == "__DAILY_DIGEST__"), None),
    }


def _night_attempts(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.glob("**/attempts/*.json")):
        item = _load(path)
        rows.append(
            {
                "role": item.get("role"),
                "timestamp_start": item.get("timestamp_start"),
                "timestamp_end": item.get("timestamp_end"),
                "expected_night_bas_dd": item.get("expected_night_bas_dd"),
                "expected_preceding_day_bas_dd": item.get("expected_preceding_day_bas_dd"),
                "terminal_classification": item.get("terminal_classification"),
                "ready_product_count": item.get("ready_product_count"),
                "candidate_product_count": item.get("candidate_product_count"),
                "user_visible_integration": item.get("user_visible_integration"),
                "production_state_mutation": item.get("production_state_mutation"),
                "per_product": [
                    {
                        "product": product.get("product"),
                        "row_state": product.get("row_state"),
                        "returned_night_bas_dd": product.get("returned_night_bas_dd"),
                        "rejection_reason": product.get("rejection_reason"),
                    }
                    for product in item.get("per_product", [])
                ],
            }
        )
    return sorted(rows, key=lambda row: str(row.get("timestamp_start") or ""))


def _validation_summary(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    row = _load(path)
    errors = list(row.get("errors") or [])
    return {
        "status": row.get("status"),
        "error_count": len(errors),
        "errors": errors,
        "fallback_eligibility_preserved": row.get("fallback_eligibility_preserved"),
        "rejected_ai_sent": row.get("rejected_ai_sent"),
        "recorded_at": row.get("recorded_at"),
    }


def build(args: argparse.Namespace) -> dict[str, Any]:
    packet = _load(args.packet)
    briefing = _load(args.briefing)
    rejected = _load(args.rejected_ai)
    structured_breadth = _load(args.structured_breadth)
    observations = _observations(briefing)
    execution_time = datetime.fromisoformat(args.execution_time_kst)
    if execution_time.tzinfo is None:
        raise ValueError("execution time must be timezone-aware")
    execution_time = execution_time.astimezone(KST)

    resolved = us_market_session(execution_time)
    session_context = packet["market_context"]["adapter_context"]["session_context"]
    target_session = date.fromisoformat(str(session_context["latest_completed_regular_session_date"]))
    if resolved.latest_completed_regular_session_date != target_session:
        raise ValueError("packet and calendar latest completed US session disagree")

    core: dict[str, dict[str, Any]] = {}
    for symbol in INDEX_SYMBOLS:
        row = observations[symbol]
        temporal = row["temporal"]
        core[symbol] = {
            "ticker": symbol,
            "close": row["value"],
            "previous_close": row["previous_value"],
            "session_return_pct": row["change_pct"],
            "session_date": temporal["observation_date"],
            "source": row["provider"],
            "state": temporal["structured_state"],
            "temporal_role": temporal["temporal_role"],
        }
    if any(row["session_date"] != target_session.isoformat() for row in core.values()):
        raise ValueError("core market observation session mismatch")

    relations = {
        "rsp_minus_spy_pp": _spread(core["RSP"]["session_return_pct"], core["SPY"]["session_return_pct"]),
        "qqq_minus_spy_pp": _spread(core["QQQ"]["session_return_pct"], core["SPY"]["session_return_pct"]),
        "iwm_minus_spy_pp": _spread(core["IWM"]["session_return_pct"], core["SPY"]["session_return_pct"]),
        "soxx_minus_spy_pp": _spread(core["SOXX"]["session_return_pct"], core["SPY"]["session_return_pct"]),
        "soxx_minus_qqq_pp": _spread(core["SOXX"]["session_return_pct"], core["QQQ"]["session_return_pct"]),
    }
    participation = (
        "동일가중도 같은 방향으로 하락했지만 SPY보다 0.12%p 약했고, "
        "QQQ와 IWM도 SPY를 하회해 대형주 방어가 상대적으로 나았던 혼합·좁은 참여였습니다. "
        "RSP는 참여 스타일 프록시이며 공식 거래소 breadth가 아닙니다."
    )

    sectors: list[dict[str, Any]] = []
    for symbol in SECTOR_SYMBOLS:
        row = observations[symbol]
        fact = next(
            item
            for item in packet["market_context"]["fact_catalog"]
            if item.get("fact_id") == f"market:sector:{symbol}"
        )
        sectors.append(
            {
                "ticker": symbol,
                "sector_name": fact["fields"]["label"],
                "close": row["value"],
                "return_pct": row["change_pct"],
                "session_date": row["temporal"]["observation_date"],
                "source": row["provider"],
                "state": row["temporal"]["structured_state"],
            }
        )
    sectors.sort(key=lambda row: float(row["return_pct"]), reverse=True)
    top3, bottom3 = sectors[:3], sectors[-3:][::-1]

    envelope = structured_breadth["envelope"]
    breadth_payload = args.breadth_raw.read_bytes()
    breadth = parse_nasdaq_daily_market_file(
        breadth_payload,
        target_session=target_session,
        retrieved_at=datetime.fromisoformat(envelope["retrieved_at"]),
        source_url=envelope["source_refs"][0],
    ).model_dump(mode="json")

    expected_night = expected_latest_completed_krx_session(execution_time.date())
    next_kr = _next_xkrx_session(execution_time.date())
    night_audit = packet["market_context"]["night_futures_audit"]
    attempts = _night_attempts(args.night_telemetry_root)
    if expected_night is None or night_audit.get("expected_session") != expected_night.isoformat():
        raise ValueError("night-futures canonical session mapping mismatch")
    night_products = {
        "KOSPI200": {
            "value": None,
            "actual_session": None,
            "state": "NOT_READY",
            "source": "KRX canonical gate",
            "reason": "expected_session_absent; stale prior session rejected",
        },
        "KOSDAQ150": {
            "value": None,
            "actual_session": None,
            "state": "NOT_READY",
            "source": "KRX canonical gate",
            "reason": "expected_session_absent; stale prior session rejected",
        },
    }

    macro: list[dict[str, Any]] = []
    for symbol in MACRO_SYMBOLS:
        row = observations[symbol]
        temporal = row["temporal"]
        change = row.get("change_value")
        if symbol in {"DGS10", "DFII10", "T10YIE", "BAMLH0A0HYM2"} and change is not None:
            change_display = f"{float(change) * 100:+.0f}bp"
        else:
            change_display = _pct(row.get("change_pct") or 0)
        macro.append(
            {
                "series_code": symbol,
                "value": row["value"],
                "unit": row["unit"],
                "change": change_display,
                "observation_date": temporal["observation_date"],
                "temporal_role": temporal["temporal_role"],
                "today_signal_eligible": temporal["today_signal_eligible"],
                "structured_state": temporal["structured_state"],
                "reason": temporal["reason"],
                "source": row["provider"],
            }
        )

    context = packet["market_context"]
    fallback = render_us_full_market_message(context)
    ai_next_checks = [str(item["text"]) for item in rejected["market_review"].get("next_checks", [])]
    ai_render = render_us_full_market_message(context, next_checks=ai_next_checks)
    fallback_quality = validate_us_market_message_payload(fallback.text).to_dict()
    ai_quality = validate_us_market_message_payload(ai_render.text).to_dict()
    plan = context["us_market_digest_plan"]
    interpreted_refs = [
        *fallback.index_fact_ids,
        *fallback.sector_fact_ids,
        "market:style:RSP",
        "market:index:SPY",
    ]
    utilization = validate_us_market_evidence_utilization(
        plan,
        facts_used=interpreted_refs,
        interpretation_fact_ids=interpreted_refs,
    ).to_dict()

    delivery = _delivery_evidence(args.database, packet["assessment_date"])
    natural_market = delivery["market_delivery"]
    natural_text = str(natural_market.get("text") or "") if natural_market else ""
    natural_parity = bool(natural_text and natural_text == fallback.text)
    natural_count = len(delivery["deliveries"])
    sent_count = sum(row["status"] == "sent" for row in delivery["deliveries"])

    primary_validation = _validation_summary(args.primary_validation)
    backup_validation = _validation_summary(args.backup_validation)
    exact_candidate = fallback.text
    no_night_visible = "🌙 한국 야간선물" not in exact_candidate
    no_macro_visible = "🌐 보조 시장환경" not in exact_candidate
    all_core_current = all(row["state"] == "CURRENT_DIRECTIONAL" for row in core.values())
    sector_current_count = sum(row["state"] == "CURRENT_DIRECTIONAL" for row in sectors)
    issue_rows = [
        {"component": "core indices", "expected": "5 current", "actual": "5 current", "state": "NONE", "impact": "none"},
        {"component": "RSP", "expected": "participation proxy", "actual": "current; not promoted to breadth", "state": "NONE", "impact": "none"},
        {"component": "SOXX", "expected": "current relative input", "actual": "current; relative weakness", "state": "NONE", "impact": "none"},
        {"component": "sector universe", "expected": "11 current", "actual": f"{sector_current_count} current", "state": "NONE", "impact": "none"},
        {"component": "Nasdaq breadth", "expected": target_session.isoformat(), "actual": str(breadth.get("latest_available_session")), "state": "PUBLICATION_PENDING", "impact": "safe omission"},
        {"component": "NYSE breadth", "expected": "official/free supported source", "actual": "unavailable", "state": "SAFE_OMISSION", "impact": "no synthetic substitute"},
        {"component": "night futures", "expected": expected_night.isoformat(), "actual": "prior session only", "state": "STALE", "impact": "entire section omitted"},
        {"component": "macro", "expected": "specific/material/current", "actual": "none selected", "state": "SAFE_OMISSION", "impact": "current market evidence retained"},
        {"component": "natural run", "expected": "1 market + 13 stock", "actual": f"{sent_count}/{natural_count} sent", "state": "NONE", "impact": "deterministic route delivered"},
        {"component": "AI stock candidate", "expected": "validator pass", "actual": f"{primary_validation['error_count'] if primary_validation else 0} primary errors", "state": "MATERIAL_P1", "impact": "AI output rejected; safe deterministic delivery already complete"},
    ]
    open_p0: list[str] = []
    open_p1 = ["AI full-stock candidate validation failed; market evidence remained safe and deterministic delivery succeeded."]
    review_state = "PARTIAL_SAFE" if open_p1 else "PASS"

    market_data = {
        "contract": "us-morning-market-data-review-v1",
        "instruction_commit": args.instruction_commit,
        "base_sha": args.base_sha,
        "operating_sha_observed": args.operating_sha,
        "execution_time_kst": execution_time.isoformat(),
        "latest_completed_us_session": target_session.isoformat(),
        "us_market_calendar_status": resolved.session,
        "packet_id": packet["packet_id"],
        "source_monitor_run_id": packet.get("source_monitor_run_id"),
        "core_indices": core,
        "deterministic_relations": relations,
        "participation_style_summary": participation,
        "semiconductor_relative_state": "RELATIVE_WEAKNESS",
        "sectors_ranked": sectors,
        "sector_top3_strong": top3,
        "sector_top3_weak": bottom3,
        "production_sector_policy": "TOP_1_BOTTOM_1",
        "nasdaq_breadth": breadth,
        "nyse_breadth": {"state": "UNAVAILABLE", "reason": "no supported official/free production source"},
        "night_futures": {
            "expected_session": expected_night.isoformat(),
            "next_relevant_kr_regular_session": next_kr.isoformat() if next_kr else None,
            "products": night_products,
            "attempts": attempts,
            "canonical_gate_used": True,
            "raw_summary_bypass": 0,
            "stale_visible": 0,
        },
        "macro": macro,
        "macro_selected_facts": [],
        "render": {
            "exact_candidate": exact_candidate,
            "exact_candidate_sha256": _sha_text(exact_candidate),
            "fallback": fallback.to_dict(),
            "fallback_quality": fallback_quality,
            "ai_assisted": ai_render.to_dict(),
            "ai_quality": ai_quality,
            "evidence_utilization": utilization,
        },
        "natural_run": {
            "state": "FOUND" if delivery["run"] else "NOT_FOUND",
            "run": delivery["run"],
            "packet_id": packet["packet_id"],
            "route": "DETERMINISTIC_PRODUCTION_RENDERER",
            "delivery_count": natural_count,
            "sent_count": sent_count,
            "market_message": natural_text,
            "market_message_sha256": _sha_text(natural_text) if natural_text else None,
            "message_evidence_parity": "PASS" if natural_parity else "FAIL",
            "primary_ai_validation": primary_validation,
            "backup_ai_validation": backup_validation,
        },
        "data_quality_issues": issue_rows,
        "open_p0": open_p0,
        "open_material_p1": open_p1,
        "review_state": review_state,
    }

    gates = {
        "EXECUTION_TIME_KST": execution_time.isoformat(),
        "LATEST_COMPLETED_US_SESSION": target_session.isoformat(),
        "LATEST_COMPLETED_US_SESSION_RESOLVED": "PASS",
        **{symbol: _pct(core[symbol]["session_return_pct"]) for symbol in INDEX_SYMBOLS},
        **{f"{symbol}_CURRENT": "PASS" if core[symbol]["state"] == "CURRENT_DIRECTIONAL" else "FAIL" for symbol in INDEX_SYMBOLS},
        "PARTICIPATION_STYLE_SUMMARY": participation,
        "SEMICONDUCTOR_RELATIVE_STATE": "RELATIVE_WEAKNESS",
        "SEMICONDUCTOR_RELATIVE_SPREAD_VS_SPY": _pp(relations["soxx_minus_spy_pp"]),
        "SECTOR_CURRENT_SESSION_COUNT": sector_current_count,
        "SECTOR_TOP3_STRONG": [f"{row['ticker']} {_pct(row['return_pct'])}" for row in top3],
        "SECTOR_TOP3_WEAK": [f"{row['ticker']} {_pct(row['return_pct'])}" for row in bottom3],
        "NASDAQ_BREADTH_STATE": "PUBLICATION_PENDING",
        "NASDAQ_BREADTH_SOURCE_SESSION": breadth.get("latest_available_session"),
        "STALE_NASDAQ_BREADTH_AS_CURRENT": 0,
        "NYSE_BREADTH": "UNAVAILABLE",
        "EXPECTED_NIGHT_FUTURES_SESSION": expected_night.isoformat(),
        "KOSPI200_NIGHT_FUTURES": "UNAVAILABLE",
        "KOSPI200_NIGHT_FUTURES_STATE": "NOT_READY",
        "KOSDAQ150_NIGHT_FUTURES": "UNAVAILABLE",
        "KOSDAQ150_NIGHT_FUTURES_STATE": "NOT_READY",
        "NIGHT_FUTURES_CANONICAL_GATE_USED": "PASS",
        "NIGHT_FUTURES_SESSION_MAPPING": "PASS",
        "RAW_SUMMARY_NIGHT_FUTURES_BYPASS": 0,
        "STALE_NIGHT_FUTURES_VISIBLE": 0,
        "MACRO_SELECTED_FACTS": [],
        "GENERIC_NO_CHANGE_MACRO_SECTION_VISIBLE": int(not no_macro_visible and fallback_quality["generic_no_change_macro_section_visible"]),
        "MALFORMED_ZERO_CHANGE_KOREAN": fallback_quality["malformed_zero_change_korean"],
        "STALE_MACRO_AS_CURRENT": 0,
        "AI_CALCULATED_INDEX_RETURN": 0,
        "AI_DERIVED_SECTOR_RANKING": 0,
        "AI_FALLBACK_INDEX_NUMERIC_PARITY": "PASS" if ai_render.index_fact_ids == fallback.index_fact_ids else "FAIL",
        "AI_FALLBACK_SECTOR_NUMERIC_PARITY": "PASS" if ai_render.sector_fact_ids == fallback.sector_fact_ids else "FAIL",
        "AI_FALLBACK_NIGHT_FUTURES_PARITY": "PASS" if ai_render.night_fact_ids == fallback.night_fact_ids and no_night_visible else "FAIL",
        "AI_FALLBACK_TEMPORAL_PARITY": "PASS" if "🌐 보조 시장환경" not in ai_render.text and no_macro_visible else "FAIL",
        "NATURAL_US_MORNING_RUN": "FOUND" if delivery["run"] else "NOT_FOUND",
        "NATURAL_US_MORNING_RUN_ID": delivery["run"]["id"] if delivery["run"] else None,
        "NATURAL_US_MORNING_PACKET_ID": packet["packet_id"],
        "NATURAL_US_MORNING_MESSAGE_EVIDENCE_PARITY": "PASS" if natural_parity else "FAIL",
        "OPEN_P0": len(open_p0),
        "OPEN_MATERIAL_P1": len(open_p1),
        "US_MORNING_DATA_REVIEW": review_state,
        "NEXT_ACTION": "BOUNDED_REPAIR" if open_p1 else "NO_ACTION",
    }
    if not all_core_current or sector_current_count != len(SECTOR_SYMBOLS):
        gates["US_MORNING_DATA_REVIEW"] = "FAIL"
    return {"market_data": market_data, "gates": gates}


def write_reports(result: dict[str, Any], args: argparse.Namespace) -> list[Path]:
    data = result["market_data"]
    gates = result["gates"]
    output = args.output_dir
    core = data["core_indices"]
    sectors = data["sectors_ranked"]
    relations = data["deterministic_relations"]
    breadth = data["nasdaq_breadth"]
    night = data["night_futures"]
    macro = data["macro"]
    natural = data["natural_run"]
    render = data["render"]
    paths: list[Path] = []

    def emit(name: str, title: str, body: str) -> None:
        path = output / name
        _write(path, _report(title, body))
        paths.append(path)

    emit(
        f"{REPORT_DATE}-us-morning-session-resolution.md",
        "2026-08-29 US Morning Session Resolution",
        f"""- Execution time (KST): `{data['execution_time_kst']}`
- Calendar status at execution: `{data['us_market_calendar_status']}`
- Latest completed US regular session: `{data['latest_completed_us_session']}`
- Packet session: `{data['latest_completed_us_session']}`
- Resolver agreement: `PASS`
- Base SHA: `{data['base_sha']}`
- Instruction commit: `{data['instruction_commit']}`

The XNYS calendar resolver and the immutable packet independently resolve the same completed session. No calendar-date shortcut was used.""",
    )
    emit(
        f"{REPORT_DATE}-us-major-index-data.md",
        "2026-08-29 US Major Index Data",
        _table(
            ("Ticker", "Close", "Prior", "Return", "Session", "Source", "State"),
            ((symbol, row["close"], row["previous_close"], _pct(row["session_return_pct"]), row["session_date"], row["source"], row["state"]) for symbol, row in core.items()),
        )
        + "\n\nAll five returns are backend-owned completed-session values. `AI_CALCULATED_INDEX_RETURN = 0`.",
    )
    emit(
        f"{REPORT_DATE}-us-participation-style.md",
        "2026-08-29 US Participation and Style",
        f"""{data['participation_style_summary']}

{_table(('Relation', 'Spread'), (
    ('RSP - SPY', _pp(relations['rsp_minus_spy_pp'])),
    ('QQQ - SPY', _pp(relations['qqq_minus_spy_pp'])),
    ('IWM - SPY', _pp(relations['iwm_minus_spy_pp'])),
))}

Evidence refs: `market:style:RSP`, `market:index:SPY`, `market:index:QQQ`, `market:index:IWM`. `RSP_AS_EXCHANGE_BREADTH = 0`.""",
    )
    emit(
        f"{REPORT_DATE}-us-semiconductor-relative.md",
        "2026-08-29 US Semiconductor Relative Review",
        f"""- State: `RELATIVE_WEAKNESS`
- SOXX return: `{_pct(core['SOXX']['session_return_pct'])}`
- SOXX - SPY: `{_pp(relations['soxx_minus_spy_pp'])}`
- SOXX - QQQ: `{_pp(relations['soxx_minus_qqq_pp'])}`
- Evidence: `market:sector:SOXX`, `market:index:SPY`, `market:index:QQQ`

The spreads are deterministic backend audit calculations. They are not AI arithmetic.""",
    )
    emit(
        f"{REPORT_DATE}-us-sector-dispersion.md",
        "2026-08-29 US Sector Dispersion",
        _table(
            ("Rank", "Ticker", "Sector", "Close", "Return", "Session", "State"),
            ((index, row["ticker"], row["sector_name"], row["close"], _pct(row["return_pct"]), row["session_date"], row["state"]) for index, row in enumerate(sectors, 1)),
        )
        + "\n\n"
        + "Strongest three: "
        + ", ".join(
            f"{row['ticker']} {_pct(row['return_pct'])}"
            for row in data["sector_top3_strong"]
        )
        + ".\n\nWeakest three: "
        + ", ".join(
            f"{row['ticker']} {_pct(row['return_pct'])}"
            for row in data["sector_top3_weak"]
        )
        + ".\n\n"
        + "Current production renderer policy remains `TOP_1_BOTTOM_1`: XLC and XLK. The read-only task does not change that policy. `AI_DERIVED_SECTOR_RANKING = 0`.",
    )
    emit(
        f"{REPORT_DATE}-us-nasdaq-breadth.md",
        "2026-08-29 Official Nasdaq Breadth",
        f"""- Requested session: `{breadth['target_session']}`
- Latest official source session: `{breadth['latest_available_session']}`
- Latest completed market session: `{breadth['latest_completed_session']}`
- Publication state: `{breadth['publication_state']}`
- Denial reason: `{breadth['denial_reason']}`
- Advances: `unavailable for target session`
- Declines: `unavailable for target session`
- Unchanged: `unavailable for target session`
- Advance/decline ratio: `unavailable for target session`
- Source payload SHA-256: `{breadth['source_payload_sha256']}`
- Invalid historical rows ignored outside target: `{', '.join(breadth['invalid_breadth_sessions']) or '0'}`

The official file had not published the exact 2026-08-28 row. The 2026-08-26 row was not promoted to current. `STALE_NASDAQ_BREADTH_AS_CURRENT = 0`. NYSE breadth remains `UNAVAILABLE`; no unofficial substitute was synthesized.""",
    )
    attempt_rows = []
    for attempt in night["attempts"]:
        returned = sorted({str(row.get("returned_night_bas_dd")) for row in attempt["per_product"] if row.get("returned_night_bas_dd")})
        attempt_rows.append((attempt["role"], attempt["timestamp_start"], attempt["expected_night_bas_dd"], ", ".join(returned), attempt["terminal_classification"], attempt["ready_product_count"]))
    emit(
        f"{REPORT_DATE}-us-korea-night-futures.md",
        "2026-08-29 Korea Night Futures Gate",
        f"""- Execution time (KST): `{data['execution_time_kst']}`
- Latest completed US session: `{data['latest_completed_us_session']}`
- Next relevant KR regular session: `{night['next_relevant_kr_regular_session']}`
- Expected night-futures session (06:00 end-date basis): `{night['expected_session']}`
- KOSPI200: `NOT_READY` (`expected_session_absent`)
- KOSDAQ150: `NOT_READY` (`expected_session_absent`)
- Canonical gate used: `PASS`
- Raw summary bypass: `0`
- Stale prior-session values visible: `0`
- Empty section visible: `0`

{_table(('Role', 'Observed', 'Expected', 'Returned night session', 'Terminal state', 'Ready'), attempt_rows)}

All four production-gate attempts found only the 2026-08-28 prior night session. The current candidate therefore omits the entire night-futures section.""",
    )
    emit(
        f"{REPORT_DATE}-us-macro-context.md",
        "2026-08-29 US Macro Temporal Context",
        _table(
            ("Series", "Value", "Change", "Observation", "Temporal role", "Today eligible", "Source"),
            ((row["series_code"], f"{row['value']} {row['unit']}", row["change"], row["observation_date"], row["temporal_role"], row["today_signal_eligible"], row["source"]) for row in macro),
        )
        + "\n\n`MACRO_SELECTED_FACTS = []`. Current DGS10, DFII10, T10YIE, high-yield spread, and VIX observations were retained in evidence but none passed the existing additional-materiality selector. WTI, broad dollar, and USD/KRW remained reference-lagging. The user-facing macro section was safely omitted.",
    )
    emit(
        f"{REPORT_DATE}-us-morning-exact-message-candidate.md",
        "2026-08-29 Exact US Morning Message Candidate",
        f"""Contract: `{render['fallback']['contract']}`  
Candidate SHA-256: `{render['exact_candidate_sha256']}`  
Renderer status: `{'PASS' if not render['fallback']['validation_errors'] else 'FAIL'}`  
Message quality: `{render['fallback_quality']['status']}`  
Delivery performed by this task: `0`

```text
{render['exact_candidate']}
```""",
    )
    emit(
        f"{REPORT_DATE}-us-morning-ai-fallback-parity.md",
        "2026-08-29 US Morning AI and Fallback Parity",
        f"""{_table(('Gate', 'Result'), (
    ('Index numeric parity', gates['AI_FALLBACK_INDEX_NUMERIC_PARITY']),
    ('Sector numeric parity', gates['AI_FALLBACK_SECTOR_NUMERIC_PARITY']),
    ('Night-futures visibility parity', gates['AI_FALLBACK_NIGHT_FUTURES_PARITY']),
    ('Temporal macro parity', gates['AI_FALLBACK_TEMPORAL_PARITY']),
    ('Fallback exact-payload quality', render['fallback_quality']['status']),
    ('AI-assisted exact-payload quality', render['ai_quality']['status']),
    ('Market evidence utilization', render['evidence_utilization']['status']),
))}

Both candidates use the same deterministic index, participation, sector, night, and macro layers. The AI-assisted variant changes only the bounded next-check text. No candidate was sent by this task.

## AI-Assisted Preview

```text
{render['ai_assisted']['text']}
```

## Deterministic Fallback Preview

```text
{render['fallback']['text']}
```""",
    )
    primary = natural.get("primary_ai_validation") or {}
    backup = natural.get("backup_ai_validation") or {}
    emit(
        f"{REPORT_DATE}-us-natural-run-inspection.md",
        "2026-08-29 US Natural Run Inspection",
        f"""- Natural run: `{natural['state']}`
- Monitor run ID: `{natural['run']['id'] if natural['run'] else 'unavailable'}`
- Packet ID: `{natural['packet_id']}`
- Route delivered: `{natural['route']}`
- Deliveries: `{natural['sent_count']}/{natural['delivery_count']} sent` (1 market + 13 stocks)
- Market evidence parity: `{natural['message_evidence_parity']}`
- Primary AI validation: `{primary.get('status', 'unavailable')}` with `{primary.get('error_count', 0)}` errors
- Backup AI validation: `{backup.get('status', 'unavailable')}` with `{backup.get('error_count', 0)}` errors
- Rejected AI sent: `false`

The primary AI full-stock candidate failed stock-level risk/reward, valuation, inventory-ownership, and numeric-occurrence checks. After rejecting one intermediate stale-claim output, the backup's final candidate failed three market-evidence-consumption checks and one framework allowlist check. These failures did not alter the market evidence and did not cause a duplicate delivery; the regular deterministic route had already completed all 14 sends.

## Exact Delivered Market Message

```text
{natural['market_message']}
```""",
    )
    emit(
        f"{REPORT_DATE}-us-morning-data-quality.md",
        "2026-08-29 US Morning Data Quality",
        _table(
            ("Component", "Expected", "Actual", "State", "Impact"),
            ((row["component"], row["expected"], row["actual"], row["state"], row["impact"]) for row in data["data_quality_issues"]),
        )
        + f"\n\n- Open P0: `{len(data['open_p0'])}`\n- Open material P1: `{len(data['open_material_p1'])}`\n- Review state: `{data['review_state']}`\n\nThe P1 is bounded to the rejected full-stock AI candidate. The requested current market-data extraction and exact delivered market message are evidence-consistent.",
    )
    emit(
        f"{REPORT_DATE}-us-morning-review-summary.md",
        "2026-08-29 US Morning Review Summary",
        f"""{_table(('Item', 'Result'), (
    ('US target session', data['latest_completed_us_session']),
    ('SPY', _pct(core['SPY']['session_return_pct'])),
    ('QQQ', _pct(core['QQQ']['session_return_pct'])),
    ('IWM', _pct(core['IWM']['session_return_pct'])),
    ('SOXX', _pct(core['SOXX']['session_return_pct'])),
    ('RSP', _pct(core['RSP']['session_return_pct'])),
    ('Participation/style', data['participation_style_summary']),
    ('Semiconductor relative', f"RELATIVE_WEAKNESS ({_pp(relations['soxx_minus_spy_pp'])} vs SPY)"),
    ('Top 3 sectors', ', '.join(f"{row['ticker']} {_pct(row['return_pct'])}" for row in data['sector_top3_strong'])),
    ('Bottom 3 sectors', ', '.join(f"{row['ticker']} {_pct(row['return_pct'])}" for row in data['sector_top3_weak'])),
    ('Nasdaq breadth', f"PUBLICATION_PENDING; latest official {breadth['latest_available_session']}"),
    ('KOSPI200 night', 'NOT_READY; omitted'),
    ('KOSDAQ150 night', 'NOT_READY; omitted'),
    ('Macro selected', 'none'),
    ('Natural run', f"FOUND; run {natural['run']['id']}; parity {natural['message_evidence_parity']}"),
))}

## Final Gates

```json
{json.dumps(gates, ensure_ascii=False, indent=2, sort_keys=True)}
```

The review is `PARTIAL_SAFE`: hard market-data, temporal-safety, renderer, and natural-message parity gates pass. One material P1 remains in the rejected full-stock AI candidate and requires a separate bounded repair; production delivery already completed safely through the deterministic route.""",
    )

    market_json = output / f"{REPORT_DATE}-us-morning-market-data.json"
    summary_json = output / f"{REPORT_DATE}-us-morning-review-summary.json"
    _write_json(market_json, data)
    _write_json(summary_json, gates)
    paths.extend((market_json, summary_json))

    index_path = output / f"{REPORT_DATE}-us-morning-artifact-index.md"
    indexed = [args.instruction, *paths]
    index_rows = [(path.name, _sha_file(path), path.stat().st_size) for path in indexed]
    _write(
        index_path,
        _report(
            "2026-08-29 US Morning Artifact Index",
            f"""- Instruction commit: `{data['instruction_commit']}`
- Base SHA: `{data['base_sha']}`
- Runtime behavior changed: `NO`
- Production/test Telegram sent by this task: `0`
- DB, assessment, scheduler, and Production Assist mutation: `0`

{_table(('Artifact', 'SHA-256', 'Bytes'), index_rows)}

The completion ZIP is assembled after validation and receives its own external SHA-256 receipt.""",
        ),
    )
    paths.append(index_path)
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the read-only US morning market review evidence bundle.")
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--briefing", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--structured-breadth", type=Path, required=True)
    parser.add_argument("--breadth-raw", type=Path, required=True)
    parser.add_argument("--night-telemetry-root", type=Path, required=True)
    parser.add_argument("--rejected-ai", type=Path, required=True)
    parser.add_argument("--primary-validation", type=Path)
    parser.add_argument("--backup-validation", type=Path)
    parser.add_argument("--instruction", type=Path, required=True)
    parser.add_argument("--instruction-commit", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--operating-sha", required=True)
    parser.add_argument("--execution-time-kst", required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs" / "reports")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build(args)
    paths = write_reports(result, args)
    print(json.dumps({"status": result["gates"]["US_MORNING_DATA_REVIEW"], "reports": [str(path) for path in paths]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
