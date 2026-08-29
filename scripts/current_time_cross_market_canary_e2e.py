from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sqlite3
import sys
from collections.abc import Mapping
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import exchange_calendars as exchange_calendar
import httpx
from sqlalchemy import text as sql_text
from sqlmodel import Session

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from app.database import engine  # noqa: E402
from app.jobs.probe_krx_night_futures import fetch_live_probe  # noqa: E402
from app.providers.nasdaq_trader_breadth_provider import (  # noqa: E402
    NasdaqTraderBreadthProvider,
)
from app.services.cross_market_decision_engine_service import (  # noqa: E402
    DecisionCandidate,
    DecisionEvidencePacket,
)
from app.services.decision_canary_service import (  # noqa: E402
    insert_decision_canary_block,
    polarity_claim_errors,
)
from app.services.kr_market_digest_quality_service import (  # noqa: E402
    is_kr_sector_return_row,
)
from app.services.ticker_analysis_snapshot_service import (  # noqa: E402
    TickerAnalysisSnapshotService,
)
from scripts.kr_final_preenable_test_delivery import (  # noqa: E402
    deliver_test_messages,
)
from scripts.kr_market_preenable_evidence import (  # noqa: E402
    audit_test_sink,
    load_env_values,
)


CONTRACT = "current-time-cross-market-canary-message-e2e-v1"
NAMESPACE = "CURRENT_TIME_CROSS_MARKET_CANARY_MESSAGE_E2E_TEST_ONLY"
KST = ZoneInfo("Asia/Seoul")
SUBJECTS = {"kr": ("003690", "000660"), "us": ("GOOGL", "RXRX")}
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
MESSAGE_KEYS = (
    "KR_MARKET",
    "US_MARKET",
    "003690",
    "000660",
    "GOOGL",
    "RXRX",
)


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _session(calendar_name: str, current_date: date) -> tuple[date, date]:
    calendar = exchange_calendar.get_calendar(calendar_name)
    completed = calendar.date_to_session(current_date, direction="previous")
    return completed.date(), calendar.next_session(completed).date()


async def _fetch_market_bar(
    client: httpx.AsyncClient,
    *,
    symbol: str,
) -> dict[str, object]:
    last_error: Exception | None = None
    payload: dict[str, object] | None = None
    attempts = 0
    for attempts in range(1, 4):
        try:
            response = await client.get(
                "/ohlcv",
                params={
                    "symbol": symbol,
                    "market": "US",
                    "periods": "daily",
                    "count": 2,
                    "include_indicators": "false",
                    "indicator_limit": 0,
                    "adjusted": "true",
                },
            )
            response.raise_for_status()
            value = response.json()
            if not isinstance(value, dict):
                raise ValueError(f"market_payload_invalid:{symbol}")
            payload = value
            break
        except (httpx.HTTPError, ValueError) as exc:
            last_error = exc
            if attempts < 3:
                await asyncio.sleep(float(attempts))
    if payload is None:
        assert last_error is not None
        raise last_error
    bars = payload.get("periods", {}).get("daily", [])
    if not isinstance(bars, list) or len(bars) < 2:
        raise ValueError(f"market_bar_incomplete:{symbol}")
    previous, latest = bars[-2], bars[-1]
    previous_close = float(previous["close"])
    close = float(latest["close"])
    if previous_close == 0:
        raise ValueError(f"market_previous_close_zero:{symbol}")
    return {
        "symbol": symbol,
        "session_date": str(latest["date"])[:10],
        "close": close,
        "previous_close": previous_close,
        "return_pct": round((close / previous_close - 1.0) * 100.0, 4),
        "source": "local_ohlcv_api",
        "attempts": attempts,
        "source_payload_sha256": _sha256_text(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        ),
    }


async def _ticker_snapshots() -> dict[str, object]:
    service = TickerAnalysisSnapshotService()
    rows: dict[str, object] = {}
    with Session(engine) as session:
        session.exec(sql_text("PRAGMA query_only = ON"))
        for ticker in (*SUBJECTS["kr"], *SUBJECTS["us"]):
            snapshot = None
            last_error: Exception | None = None
            attempts = 0
            for attempts in range(1, 4):
                try:
                    snapshot = await service.fetch(session, ticker)
                    break
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                    if attempts < 3:
                        await asyncio.sleep(float(attempts))
            if snapshot is None:
                assert last_error is not None
                rows[ticker] = {
                    "status": "PROVIDER_ERROR",
                    "error_class": type(last_error).__name__,
                    "error_message": str(last_error)[:240],
                    "attempts": attempts,
                }
            else:
                rows[ticker] = {
                    "status": "PASS",
                    "attempts": attempts,
                    "snapshot": snapshot.model_dump(mode="json"),
                }
    return rows


def _notification_texts(
    database: Path,
    *,
    kr_assessment_date: str,
    us_assessment_date: str,
) -> dict[str, dict[str, object]]:
    requested = {
        "KR_MARKET": (kr_assessment_date, "__DAILY_DIGEST_KR__"),
        "US_MARKET": (us_assessment_date, "__DAILY_DIGEST__"),
        "003690": (kr_assessment_date, "003690"),
        "000660": (kr_assessment_date, "000660"),
        "GOOGL": (us_assessment_date, "GOOGL"),
        "RXRX": (us_assessment_date, "RXRX"),
    }
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    try:
        rows: dict[str, dict[str, object]] = {}
        for key, (assessment_date, ticker) in requested.items():
            row = connection.execute(
                """
                SELECT status, payload
                  FROM notificationdelivery
                 WHERE assessment_date = ? AND ticker = ?
                """,
                (assessment_date, ticker),
            ).fetchone()
            if row is None:
                raise ValueError(f"base_message_missing:{key}")
            payload = json.loads(row[1] or "{}")
            message = str(payload.get("text") or "")
            if not message:
                raise ValueError(f"base_message_text_missing:{key}")
            rows[key] = {
                "assessment_date": assessment_date,
                "ticker": ticker,
                "delivery_status": row[0],
                "text": message,
                "text_sha256": _sha256_text(message),
            }
    finally:
        connection.close()
    return rows


def _canonical_store_audit(database: Path) -> dict[str, object]:
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows: list[dict[str, object]] = []
        for ticker in (*SUBJECTS["kr"], *SUBJECTS["us"]):
            watchlist = connection.execute(
                """
                SELECT company_name, exchange, active, latest_status,
                       latest_assessment_date
                  FROM watchlistitem
                 WHERE ticker = ?
                """,
                (ticker,),
            ).fetchone()
            thesis = connection.execute(
                """
                SELECT version, status, time_horizon, created_at
                  FROM investmentthesis
                 WHERE ticker = ?
                 ORDER BY version DESC LIMIT 1
                """,
                (ticker,),
            ).fetchone()
            assessment = connection.execute(
                """
                SELECT assessment_date, status, business_thesis_change,
                       valuation_change, earnings_estimate_impact, created_at
                  FROM thesisassessment
                 WHERE ticker = ?
                 ORDER BY assessment_date DESC, id DESC LIMIT 1
                """,
                (ticker,),
            ).fetchone()
            financial = connection.execute(
                """
                SELECT COUNT(*) AS row_count, MAX(reported_date) AS latest_reported_date,
                       MAX(created_at) AS latest_ingested_at
                  FROM financialsnapshot
                 WHERE ticker = ?
                """,
                (ticker,),
            ).fetchone()
            rows.append(
                {
                    "ticker": ticker,
                    "watchlist": dict(watchlist) if watchlist is not None else None,
                    "thesis": dict(thesis) if thesis is not None else None,
                    "latest_assessment": (
                        dict(assessment) if assessment is not None else None
                    ),
                    "financial_store": (
                        dict(financial) if financial is not None else None
                    ),
                    "status": (
                        "PASS"
                        if all(
                            item is not None
                            for item in (watchlist, thesis, assessment, financial)
                        )
                        else "PARTIAL_SAFE"
                    ),
                }
            )
    finally:
        connection.close()
    return {
        "contract": "current-canonical-store-read-only-audit-v1",
        "status": (
            "PASS" if all(row["status"] == "PASS" for row in rows) else "PARTIAL_SAFE"
        ),
        "database_query_only": True,
        "rows": rows,
    }


def _signed_percent(value: object) -> str:
    return f"{float(value):+.2f}%"


def _krw_amount(value: object) -> str:
    amount = float(value)
    sign = "+" if amount > 0 else "-" if amount < 0 else ""
    absolute = abs(amount)
    if absolute >= 1_000_000_000_000:
        return f"{sign}{absolute / 1_000_000_000_000:.2f}조원"
    return f"{sign}{absolute / 100_000_000:,.0f}억원"


def _fresh_kosdaq_size_rows(kr_market: Mapping[str, object]) -> list[dict[str, object]]:
    archive_path = Path(str(kr_market.get("archive_path") or ""))
    archive = _read_json(archive_path)
    if not isinstance(archive, Mapping):
        raise ValueError("kr_market_archive_invalid")
    names = ("KOSDAQ 100", "KOSDAQ MID 300", "KOSDAQ SMALL")
    matches: list[dict[str, object]] = []
    for response in archive.get("responses") or ():
        if not isinstance(response, Mapping) or response.get("api_id") != "ka20003":
            continue
        payload = response.get("payload")
        if not isinstance(payload, Mapping):
            continue
        for row in payload.get("all_inds_idex") or ():
            if not isinstance(row, Mapping) or str(row.get("stk_nm") or "") not in names:
                continue
            matches.append(
                {
                    "sector": str(row["stk_nm"]),
                    "return_pct": float(str(row.get("flu_rt") or "0")),
                }
            )
    order = {name: index for index, name in enumerate(names)}
    matches.sort(key=lambda row: order[str(row["sector"])])
    if len(matches) != 3:
        raise ValueError("kr_kosdaq_size_rows_incomplete")
    return matches


def _fresh_sector_rows(kr_market: Mapping[str, object]) -> list[dict[str, object]]:
    archive = _read_json(Path(str(kr_market.get("archive_path") or "")))
    if not isinstance(archive, Mapping):
        raise ValueError("kr_market_archive_invalid")
    excluded = {
        "종합(KOSPI)",
        "종합(KOSDAQ)",
        "대형주",
        "중형주",
        "소형주",
        "KOSDAQ 100",
        "KOSDAQ MID 300",
        "KOSDAQ SMALL",
        "변동성지수",
    }
    result: list[dict[str, object]] = []
    for response in archive.get("responses") or ():
        if not isinstance(response, Mapping) or response.get("api_id") != "ka20003":
            continue
        request = response.get("request")
        payload = response.get("payload")
        if not isinstance(request, Mapping) or not isinstance(payload, Mapping):
            continue
        market = {"001": "KOSPI", "101": "KOSDAQ"}.get(
            str(request.get("inds_cd") or "")
        )
        if market is None:
            continue
        for row in payload.get("all_inds_idex") or ():
            if not isinstance(row, Mapping):
                continue
            sector = str(row.get("stk_nm") or "")
            if (
                not sector
                or sector in excluded
                or not is_kr_sector_return_row(market_scope=market, name=sector)
            ):
                continue
            result.append(
                {
                    "market_scope": market,
                    "sector": sector,
                    "return_pct": float(str(row.get("flu_rt") or "0")),
                }
            )
    return result


def _render_current_kr_market(kr_market: Mapping[str, object]) -> str:
    indices = {
        str(row.get("symbol") or ""): row
        for row in kr_market.get("indices") or ()
        if isinstance(row, Mapping)
    }
    breadth = {
        str(row.get("scope") or ""): row.get("breadth")
        for row in kr_market.get("breadth_by_scope") or ()
        if isinstance(row, Mapping) and isinstance(row.get("breadth"), Mapping)
    }
    flows = {
        (str(row.get("market") or ""), str(row.get("actor") or "")): row
        for row in kr_market.get("market_flows") or ()
        if isinstance(row, Mapping)
    }
    kpi_size = [
        row
        for row in kr_market.get("size_context") or ()
        if isinstance(row, Mapping)
    ]
    kpi_size.sort(key=lambda row: {"대형주": 0, "중형주": 1, "소형주": 2}.get(str(row.get("sector")), 9))
    kosdaq_size = _fresh_kosdaq_size_rows(kr_market)
    sectors = _fresh_sector_rows(kr_market)
    top = sorted(sectors, key=lambda row: (-float(row["return_pct"]), str(row["sector"])))
    bottom = sorted(sectors, key=lambda row: (float(row["return_pct"]), str(row["sector"])))

    def sector_line(rows: list[Mapping[str, object]], market: str) -> str:
        selected = [row for row in rows if row.get("market_scope") == market][:3]
        if len(selected) != 3:
            raise ValueError(f"kr_sector_top3_incomplete:{market}")
        return " · ".join(
            f"{str(row['sector']).replace('/', '·')} {_signed_percent(row['return_pct'])}"
            for row in selected
        )

    def flow_line(market: str) -> str:
        return " · ".join(
            f"{label} {_krw_amount(flows[(market, actor)]['net_buy_amount'])}"
            for actor, label in (
                ("foreign", "외국인"),
                ("institution", "기관"),
                ("retail", "개인"),
            )
        )

    def breadth_line(market: str) -> str:
        row = breadth[market]
        assert isinstance(row, Mapping)
        return (
            f"상승 {int(row['advance_count']):,} · 하락 {int(row['decline_count']):,} · "
            f"보합 {int(row['unchanged_count']):,} · A/D {float(row['ad_ratio']):.2f}"
        )

    session = str(kr_market["session_date"])
    return "\n".join(
        (
            f"🇰🇷 한국시장 마감 · {session}",
            "",
            "📈 주요 지수",
            f"• KOSPI {float(indices['KOSPI']['close']):,.2f} · {_signed_percent(indices['KOSPI']['return_pct'])}",
            f"• KOSDAQ {float(indices['KOSDAQ']['close']):,.2f} · {_signed_percent(indices['KOSDAQ']['return_pct'])}",
            "",
            "🔎 시장 내부",
            f"• KOSPI: {breadth_line('KOSPI')}",
            f"• KOSDAQ: {breadth_line('KOSDAQ')}",
            "",
            "💰 투자자 수급",
            f"• KOSPI: {flow_line('KOSPI')}",
            f"• KOSDAQ: {flow_line('KOSDAQ')}",
            "",
            "📊 규모/스타일",
            "• KOSPI: "
            + " · ".join(
                f"{str(row['sector']).removesuffix('주')} {_signed_percent(row['return_pct'])}"
                for row in kpi_size
            ),
            "• KOSDAQ: "
            + " · ".join(
                f"{str(row['sector']).replace('KOSDAQ ', '')} {_signed_percent(row['return_pct'])}"
                for row in kosdaq_size
            ),
            "",
            "🏭 업종 강세 TOP3",
            f"• KOSPI: {sector_line(top, 'KOSPI')}",
            f"• KOSDAQ: {sector_line(top, 'KOSDAQ')}",
            "",
            "📉 업종 약세 TOP3",
            f"• KOSPI: {sector_line(bottom, 'KOSPI')}",
            f"• KOSDAQ: {sector_line(bottom, 'KOSDAQ')}",
            "",
            "📌 다음 확인",
            "• 다음 정규장에서 지수 방향과 종목 breadth의 괴리가 해소되는지 확인합니다.",
            "• 외국인·기관의 동반 순매도가 이어지는지 확인합니다.",
        )
    )


async def _collect(args: argparse.Namespace) -> None:
    execution_time = datetime.now(KST)
    latest_kr, next_kr = _session("XKRX", execution_time.date())
    latest_us, _next_us = _session("XNYS", execution_time.date())
    kr_market = _read_json(args.kr_market)
    if not isinstance(kr_market, Mapping):
        raise ValueError("kr_market_evidence_invalid")
    if str(kr_market.get("session_date") or "") != latest_kr.isoformat():
        raise ValueError("kr_market_session_mismatch")

    settings = get_settings()
    api_key = settings.action_api_key or settings.ohlcv_api_key or ""
    if not api_key:
        raise ValueError("ohlcv_api_key_missing")
    symbols = (*INDEX_SYMBOLS, *SECTOR_SYMBOLS)
    async with httpx.AsyncClient(
        base_url=settings.ohlcv_base_url.rstrip("/"),
        headers={"X-API-Key": api_key},
        timeout=settings.ohlcv_timeout_seconds,
    ) as client:
        gathered = await asyncio.gather(
            *(_fetch_market_bar(client, symbol=symbol) for symbol in symbols),
            return_exceptions=True,
        )
    us_rows: list[dict[str, object]] = []
    us_errors: list[dict[str, str]] = []
    for symbol, result in zip(symbols, gathered, strict=True):
        if isinstance(result, Exception):
            us_errors.append({"symbol": symbol, "error_class": type(result).__name__})
        else:
            us_rows.append(result)
    if any(row["session_date"] != latest_us.isoformat() for row in us_rows):
        raise ValueError("us_market_session_mismatch")

    breadth_result, breadth_payload = await NasdaqTraderBreadthProvider().collect(
        session_date=latest_us,
        retrieved_at=execution_time,
    )
    night = await fetch_live_probe()
    snapshots = await _ticker_snapshots()
    kr_packet = _read_json(args.kr_packet)
    us_packet = _read_json(args.us_packet)
    if not isinstance(kr_packet, Mapping) or not isinstance(us_packet, Mapping):
        raise ValueError("source_packet_invalid")
    messages = _notification_texts(
        args.database,
        kr_assessment_date=str(kr_packet.get("assessment_date") or "")[:10],
        us_assessment_date=str(us_packet.get("assessment_date") or "")[:10],
    )
    archived_kr_text = str(messages["KR_MARKET"]["text"])
    fresh_kr_text = _render_current_kr_market(kr_market)
    messages["KR_MARKET"] = {
        **messages["KR_MARKET"],
        "text": fresh_kr_text,
        "text_sha256": _sha256_text(fresh_kr_text),
        "render_basis": "fresh_kiwoom_current_completed_session",
        "archived_text_sha256": _sha256_text(archived_kr_text),
    }
    _write_json(
        args.output,
        {
            "contract": CONTRACT,
            "status": "PASS" if not us_errors else "PARTIAL_SAFE",
            "execution_time_kst": execution_time.isoformat(),
            "session_resolution": {
                "latest_completed_kr_session": latest_kr.isoformat(),
                "latest_completed_us_session": latest_us.isoformat(),
                "next_kr_regular_session": next_kr.isoformat(),
                "status": "PASS",
            },
            "canary_subjects": SUBJECTS,
            "kr_market": {
                "status": "PASS",
                "source_path": str(args.kr_market),
                "source_sha256": _sha256_file(args.kr_market),
                "evidence": kr_market,
            },
            "us_market": {
                "status": "PASS" if not us_errors else "PARTIAL_SAFE",
                "retrieved_at": execution_time.isoformat(),
                "request_count": len(symbols),
                "success_count": len(us_rows),
                "failure_count": len(us_errors),
                "rows": us_rows,
                "errors": us_errors,
                "nasdaq_breadth": breadth_result.model_dump(mode="json"),
                "nasdaq_source_payload_sha256": _sha256_bytes(breadth_payload),
            },
            "night_futures": night.compact_summary(),
            "ticker_snapshots": snapshots,
            "source_packets": {
                "kr": {
                    "path": str(args.kr_packet),
                    "sha256": _sha256_file(args.kr_packet),
                    "packet_id": kr_packet.get("packet_id"),
                },
                "us": {
                    "path": str(args.us_packet),
                    "sha256": _sha256_file(args.us_packet),
                    "packet_id": us_packet.get("packet_id"),
                },
            },
            "base_messages": messages,
            "safety": {
                "database_query_only": True,
                "production_recipient_send": 0,
                "production_delivery_intent": 0,
                "scheduler_mutation": 0,
                "natural_canary_counter_mutation": 0,
            },
        },
    )
    print(
        json.dumps(
            {
                "status": "PASS" if not us_errors else "PARTIAL_SAFE",
                "latest_kr": latest_kr.isoformat(),
                "latest_us": latest_us.isoformat(),
                "us_market_success": len(us_rows),
                "us_market_failure": len(us_errors),
                "snapshot_success": sum(
                    row.get("status") == "PASS"
                    for row in snapshots.values()
                    if isinstance(row, Mapping)
                ),
            },
            sort_keys=True,
        )
    )


def _market_quality(key: str, message: str) -> list[str]:
    if key == "KR_MARKET":
        required = (
            "🇰🇷 한국시장 마감",
            "📈 주요 지수",
            "🔎 시장 내부",
            "💰 투자자 수급",
            "📊 규모/스타일",
            "🏭 업종 강세 TOP3",
            "📉 업종 약세 TOP3",
        )
        forbidden = ("가격 구조", "Price Structure")
    else:
        required = ("🇺🇸 미국시장 마감", "SPY", "QQQ", "IWM", "SOXX", "RSP", "🔎 시장 내부")
        forbidden = ("가격 구조", "Price Structure")
    errors = [f"missing:{token}" for token in required if token not in message]
    errors.extend(f"forbidden:{token}" for token in forbidden if token in message)
    return errors


def _stock_quality(message: str, decision: str) -> list[str]:
    required = (
        f"AI 종합 판단: {decision}",
        "추론등급: 매우 높음",
        "판단 확신도:",
        "단기 타이밍:",
        "✅ BUY 쪽 근거:",
        "⚠️ SELL 쪽 근거:",
        "🔼 상향 조건:",
        "🔽 하향 조건:",
    )
    errors = [f"missing:{token}" for token in required if token not in message]
    forbidden = ("시장가 매수", "시장가 매도", "전량 매도", "지금 사세요", "지금 파세요", "비중")
    errors.extend(f"order_language:{token}" for token in forbidden if token in message)
    return errors


def _build_test(args: argparse.Namespace) -> None:
    collection = _read_json(args.collection)
    decisions = _read_json(args.decisions)
    if not isinstance(collection, Mapping) or not isinstance(decisions, Mapping):
        raise ValueError("build_inputs_invalid")
    base_messages = collection.get("base_messages")
    if not isinstance(base_messages, Mapping):
        raise ValueError("base_messages_missing")
    decision_rows = {
        str(row.get("ticker") or ""): row
        for row in decisions.get("rows") or ()
        if isinstance(row, Mapping)
    }
    if set(decision_rows) != {*SUBJECTS["kr"], *SUBJECTS["us"]}:
        raise ValueError("decision_subjects_mismatch")

    messages: list[dict[str, object]] = []
    quality: list[dict[str, object]] = []
    for key in ("KR_MARKET", "US_MARKET"):
        base = base_messages.get(key)
        if not isinstance(base, Mapping):
            raise ValueError(f"market_base_missing:{key}")
        if key == "KR_MARKET":
            kr_context = collection.get("kr_market")
            if not isinstance(kr_context, Mapping) or not isinstance(
                kr_context.get("evidence"), Mapping
            ):
                raise ValueError("fresh_kr_market_evidence_missing")
            message = _render_current_kr_market(kr_context["evidence"])
        else:
            message = str(base.get("text") or "")
        errors = _market_quality(key, message)
        if errors:
            raise ValueError(f"market_message_quality:{key}:" + ",".join(errors))
        messages.append(
            {
                "ticker": key,
                "route": "CURRENT_PRODUCTION_EQUIVALENT_TEST_ONLY",
                "logical_identity": f"{NAMESPACE}:{collection['execution_time_kst']}:{key}",
                "text": message,
            }
        )
        quality.append(
            {
                "ticker": key,
                "status": "PASS",
                "character_count": len(message),
                "payload_sha256": _sha256_text(message),
            }
        )

    for ticker in (*SUBJECTS["kr"], *SUBJECTS["us"]):
        base = base_messages.get(ticker)
        row = decision_rows[ticker]
        block = row.get("block")
        if not isinstance(base, Mapping) or not isinstance(block, Mapping):
            raise ValueError(f"stock_message_input_missing:{ticker}")
        packet = DecisionEvidencePacket.model_validate(row["evidence_packet"])
        candidate = DecisionCandidate.model_validate(row["candidate"])
        polarity_errors = polarity_claim_errors(
            packet,
            buy_case_evidence=candidate.buy_case_evidence,
            sell_case_evidence=candidate.sell_case_evidence,
            neutral_context_evidence=candidate.neutral_context_evidence,
        )
        if polarity_errors:
            raise ValueError(f"polarity_invalid:{ticker}:" + ",".join(polarity_errors))
        message = insert_decision_canary_block(str(base.get("text") or ""), str(block["text"]))
        errors = _stock_quality(message, candidate.decision)
        if len(message) > 3500:
            errors.append("message_too_long")
        if errors:
            raise ValueError(f"stock_message_quality:{ticker}:" + ",".join(errors))
        messages.append(
            {
                "ticker": ticker,
                "route": "CURRENT_PRODUCTION_EQUIVALENT_TEST_ONLY",
                "logical_identity": f"{NAMESPACE}:{collection['execution_time_kst']}:{ticker}",
                "text": message,
            }
        )
        quality.append(
            {
                "ticker": ticker,
                "decision": candidate.decision,
                "status": "PASS",
                "character_count": len(message),
                "payload_sha256": _sha256_text(message),
                "buy_claim_count": len(candidate.buy_case_evidence),
                "sell_claim_count": len(candidate.sell_case_evidence),
            }
        )
    if tuple(str(row["ticker"]) for row in messages) != MESSAGE_KEYS:
        raise ValueError("test_message_order_invalid")
    identities = [str(row["logical_identity"]) for row in messages]
    if len(identities) != len(set(identities)):
        raise ValueError("test_message_identity_duplicate")
    _write_json(
        args.output,
        {
            "contract": CONTRACT,
            "status": "PASS",
            "namespace": NAMESPACE,
            "message_count": 6,
            "production_recipient_send_count": 0,
            "production_delivery_intent_count": 0,
            "messages": messages,
            "quality": quality,
        },
    )
    print(json.dumps({"status": "PASS", "messages": 6}, sort_keys=True))


def _received_quality(message: str) -> Mapping[str, object]:
    if message.startswith("🇰🇷"):
        errors = _market_quality("KR_MARKET", message)
    elif message.startswith("🇺🇸"):
        errors = _market_quality("US_MARKET", message)
    else:
        errors = _stock_quality(message, next((item for item in ("BUY", "HOLD", "SELL") if f"AI 종합 판단: {item}" in message), ""))
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


async def _send_test(args: argparse.Namespace) -> None:
    payload = _read_json(args.messages)
    if not isinstance(payload, Mapping) or payload.get("status") != "PASS":
        raise ValueError("test_messages_not_ready")
    messages = [row for row in payload.get("messages") or () if isinstance(row, Mapping)]
    if len(messages) != 6:
        raise ValueError("test_message_count_not_six")
    env = load_env_values(args.env_file)
    sink = audit_test_sink(env)
    if sink.get("available") is not True:
        raise ValueError(f"test_sink_unavailable:{sink.get('reason')}")
    selected_key = str(sink.get("selected_test_key_name") or "")
    receipt = await deliver_test_messages(
        messages,
        token=env.get("TELEGRAM_BOT_TOKEN") or "",
        test_chat_id=env.get(selected_key) or "",
        production_chat_id=env.get("TELEGRAM_CHAT_ID") or "",
        test_sink_alias=str(sink["test_sink_alias"]),
        production_sink_alias=str(sink["production_sink_alias"]),
        receipt_path=args.receipt,
        contract="current-time-cross-market-canary-test-sink-v1",
        namespace=NAMESPACE,
        received_payload_validator=_received_quality,
    )
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "sent": receipt["sent_message_count"],
                "exact": receipt["exact_payload_match"],
                "production_recipient_send": receipt["production_recipient_send_count"],
            },
            sort_keys=True,
        )
    )


def _audit_store(args: argparse.Namespace) -> None:
    value = _canonical_store_audit(args.database)
    _write_json(args.output, value)
    print(
        json.dumps(
            {"status": value["status"], "subjects": len(value["rows"])},
            sort_keys=True,
        )
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    collect = sub.add_parser("collect")
    collect.add_argument("--kr-market", type=Path, required=True)
    collect.add_argument("--kr-packet", type=Path, required=True)
    collect.add_argument("--us-packet", type=Path, required=True)
    collect.add_argument("--database", type=Path, required=True)
    collect.add_argument("--output", type=Path, required=True)
    build = sub.add_parser("build-test")
    build.add_argument("--collection", type=Path, required=True)
    build.add_argument("--decisions", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    send = sub.add_parser("send-test")
    send.add_argument("--env-file", type=Path, required=True)
    send.add_argument("--messages", type=Path, required=True)
    send.add_argument("--receipt", type=Path, required=True)
    store = sub.add_parser("audit-store")
    store.add_argument("--database", type=Path, required=True)
    store.add_argument("--output", type=Path, required=True)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "collect":
        asyncio.run(_collect(args))
    elif args.command == "build-test":
        _build_test(args)
    elif args.command == "send-test":
        asyncio.run(_send_test(args))
    else:
        _audit_store(args)


if __name__ == "__main__":
    main()
