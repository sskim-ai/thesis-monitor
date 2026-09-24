"""One-shot, read-only KR holiday source audit. No models or delivery entry point."""
from __future__ import annotations

import argparse
import asyncio
from contextlib import ExitStack
from dataclasses import asdict
from datetime import date, datetime
from hashlib import sha256
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

import httpx


KST = ZoneInfo("Asia/Seoul")


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, default=str)
        stream.write("\n")


def calendar_receipt(at):
    import exchange_calendars
    from app.services.market_session import korea_market_session
    from app.services.xkrx_role_target_service import resolve_xkrx_role_target

    cal = exchange_calendars.get_calendar("XKRX")
    # Direct membership is mandatory; out-of-range errors cannot use weekday fallback.
    active = bool(cal.is_session(at.date()))
    prior = cal.date_to_session(at.date(), direction="previous")
    following = cal.date_to_session(at.date(), direction="next")
    state = korea_market_session(at)
    return dict(
        observed_at=at, source="exchange_calendars:XKRX", version=exchange_calendars.__version__,
        calendar_first=cal.first_session, calendar_last=cal.last_session,
        active_session=active, latest_completed_session=state.latest_completed_regular_session_date,
        previous_session=prior.date(), next_session=following.date(),
        previous_open=cal.session_open(prior), previous_close=cal.session_close(prior),
        next_open=cal.session_open(following), next_close=cal.session_close(following),
        state=asdict(state), producer_target=asdict(resolve_xkrx_role_target(at, "kr_daily_production")),
        weekday_fallback_used=False,
    )


async def suppression_receipt(at, tickers):
    from app.jobs import monitor_daily

    session = Mock()
    names = (
        "_analysis_decision", "market_preflight_onboarding_resume",
        "run_kr_close_market_briefing", "run_daily_monitor", "run_macro_monitor",
        "collect_and_persist_kiwoom_market_context", "try_write_ai_review_packet",
        "queue_daily_monitor_notifications", "hold_ai_assisted_pilot_session",
    )
    with ExitStack() as stack:
        guards = {name: stack.enter_context(patch.object(monitor_daily, name,
                  side_effect=AssertionError("holiday gate bypass: " + name))) for name in names}
        output = await monitor_daily._run_market_job(session, at.date(), "kr", as_of=at)
        assert output["analysis_action"] == output["delivery_action"] == "safe_noop"
        assert output["skip_reason"] == "no_valid_role_target"
        counts = {name: guard.call_count for name, guard in guards.items()}
    assert not session.mock_calls and not any(counts.values())
    return dict(
        output=output, downstream_boundary_counts=counts, persistence_calls=len(session.mock_calls),
        KR_MARKET=dict(eligible=False, reason=output["skip_reason"]),
        stocks=[dict(ticker=t, eligible=False, reason=output["skip_reason"]) for t in tickers],
        model_calls=0, Market=0, Core=0, A=0, B=0, rendered_messages=0,
        delivery_intent=0, send_calls=0,
        proof_scope="real producer entry point, tripwires at first downstream boundaries; no packet generated",
    )


class ReadOnlyTransport(httpx.AsyncBaseTransport):
    def __init__(self, root):
        self.root = root
        self.delegate = httpx.AsyncHTTPTransport(retries=0)
        self.rows = []
        self.auth_calls = 0

    async def handle_async_request(self, request):
        path = request.url.path
        auth = request.method == "POST" and path == "/oauth2/token"
        quote = (request.method == "POST" and path == "/api/dostk/stkinfo"
                 and request.headers.get("api-id") == "ka10001")
        chart = request.method == "GET" and path == "/ohlcv"
        if not (auth or quote or chart):
            raise ValueError("read_only_source_allowlist_violation")
        if auth or quote:
            if str(request.url.copy_with(path="", query=None)) != "https://api.kiwoom.com":
                raise ValueError("official_kiwoom_host_required")
        if auth:
            self.auth_calls += 1
            return await self.delegate.handle_async_request(request)
        params = dict(request.url.params) if chart else json.loads(request.content)
        row = dict(path=path, parameters=params, api_id=request.headers.get("api-id"),
                   started_at=datetime.now(KST).isoformat())
        self.rows.append(row)
        try:
            response = await self.delegate.handle_async_request(request)
            raw = await response.aread()
            row.update(http_status=response.status_code, raw_response_sha256=sha256(raw).hexdigest(),
                       raw_body=raw.decode("utf-8"))
            return response
        except httpx.HTTPError as exc:
            row["error_type"] = type(exc).__name__
            raise
        finally:
            row["received_at"] = datetime.now(KST).isoformat()
            put(self.root / f"response-{len(self.rows):03}.json", row)

    async def aclose(self):
        await self.delegate.aclose()


async def collect_sources(root, at, tickers):
    from app.config import get_settings
    from app.providers.kiwoom_rest_client import KiwoomRestClient, KiwoomRestError
    from app.services.ohlcv_client import OhlcvClient
    from app.services.current_price_context_service import select_current_price_context

    settings = get_settings()
    rows = []
    quote_transport = ReadOnlyTransport(root / "raw/quote")
    quotes = KiwoomRestClient(transport=quote_transport, max_retries=0, timeout_seconds=10)
    for ticker in tickers:
        quote, quote_error = None, None
        try:
            response = await quotes.request(endpoint="/api/dostk/stkinfo", api_id="ka10001", body={"stk_cd": ticker})
            quote = response.payload
        except (KiwoomRestError, httpx.HTTPError, ValueError) as exc:
            quote_error = type(exc).__name__
        transport = ReadOnlyTransport(root / "raw" / ticker)
        client = OhlcvClient(transport=transport)
        # Same source/parser/context owner, bounded transport, no persistence session.
        context = await client.fetch_price_context(ticker, as_of=at, session=None)
        data = context.model_dump(mode="json")
        put(root / "normalized" / f"{ticker}.json", data)
        daily_responses = [r for r in transport.rows if r["parameters"].get("periods") == "daily"]
        bars, metadata = [], None
        for response in daily_responses:
            if response.get("http_status") != 200:
                continue
            payload = json.loads(response["raw_body"])
            bars = payload.get("periods", {}).get("daily", [])
            metadata = payload.get("meta")
        latest = max(bars, key=lambda b: str(b.get("date")), default=None)
        dates = [str(b.get("date"))[:10] for b in bars]
        row = dict(
            ticker=ticker, quote_error=quote_error,
            quote_current_price_raw=quote.get("cur_prc") if quote else None,
            quote_source_temporal_fields={k: v for k, v in (quote or {}).items()
                if k in {"dt", "date", "tm", "time", "base_dt", "trde_dt", "business_date"}},
            quote_source_time_verified=False,
            quote_normalization="NON_INTRADAY_CLOSED_SESSION_UNDATED_QUOTE_DIAGNOSTIC_ONLY",
            raw_daily_latest=latest, raw_daily_metadata=metadata,
            raw_daily_row_count=len(bars), raw_holiday_bar_count=dates.count(at.date().isoformat()),
            raw_future_bar_count=sum(d > at.date().isoformat() for d in dates),
            normalized_holiday_bar_count=sum(p.date == at.date() for p in context.daily_history),
            normalized_decision=data["decision"], normalized_chart_basis=context.chart.price_basis,
            normalized_current_price=select_current_price_context(data),
            source_http_count=len(transport.rows), normalized_warnings=context.warnings,
            message_eligible=False,
        )
        row["source_basis_pass"] = bool(
            latest and context.available and dates and not row["raw_holiday_bar_count"]
            and not row["raw_future_bar_count"] and not row["normalized_holiday_bar_count"]
            and context.decision.market_session == "closed"
            and context.decision.price_basis == "close" and context.chart.price_basis == "adjusted_close"
            and str(latest.get("date"))[:10] == context.decision.price_as_of
            == context.decision.latest_completed_regular_session_date
            and isinstance(metadata, dict) and metadata.get("adjusted") is True
        )
        rows.append(row)
        put(root / "symbols" / f"{ticker}.json", row)
        print(json.dumps(dict(ticker=ticker, source_basis_pass=row["source_basis_pass"],
                              quote_available=bool(quote), latest_date=latest.get("date") if latest else None)), flush=True)
        await asyncio.sleep(0.6)
    await quote_transport.aclose()
    put(root / "source-table.json", dict(rows=rows, quote_stats=asdict(quotes.stats),
        auth_calls=quote_transport.auth_calls, gateway_calls=sum(r["source_http_count"] for r in rows),
        provider_scope="existing OHLCV gateway and official Kiwoom ka10001; no accounts/orders",
        provider_cache_policy="existing provider policy; no force-refresh or synthetic bar",
        monitor_retry_attempts=settings.monitor_retry_attempts, source_count=len(rows)))
    return all(row["source_basis_pass"] for row in rows)


async def run(args):
    from sqlmodel import Session, create_engine
    from app.services.onboarding_readiness_service import production_universe_snapshot
    from app.services.market_context_adapter_service import market_context_adapter

    at = datetime.now(KST)
    if at.date() != args.date:
        raise ValueError("actual_holiday_date_required")
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    cal = calendar_receipt(at)
    put(root / "calendar.json", cal)
    if cal["active_session"] or cal["latest_completed_session"] >= at.date():
        raise ValueError("authoritative_closed_session_required")
    database = args.database.resolve()
    engine = create_engine(f"sqlite:///file:{database}?mode=ro&uri=true")
    with Session(engine) as session:
        snapshot = production_universe_snapshot(session, "kr", cutoff=at, session_key="daily_kr")
        tickers = sorted(item.ticker for item in snapshot.eligible_items)
        put(root / "universe.json", dict(source="production_universe_snapshot", database_mode="ro",
            snapshot=snapshot.to_dict(), tickers=tickers, count=len(tickers)))
    engine.dispose()
    if not tickers or len(tickers) != len(set(tickers)):
        raise ValueError("canonical_universe_incomplete")
    put(root / "suppression.json", await suppression_receipt(at, tickers))
    market = market_context_adapter("KR").normalize(
        assessment_date=cal["latest_completed_session"], as_of=at, cutoff=at, fact_catalog=[],
        provider_publication_state="UNAVAILABLE",
    )
    put(root / "market-session-context.json", dict(normalized=market.model_dump(mode="json"),
        scope="isolated session-only adapter proof; holiday producer skips before collecting market values",
        message_eligible=False, model_invoked=False))
    passed = await collect_sources(root, at, tickers) if args.collect else None
    put(root / "result.json", dict(source_basis_pass=passed, calendar_pass=True, suppression_pass=True,
        count=len(tickers), model_calls=0, rendered_messages=0, send_calls=0,
        production_db_writes=0, scheduler_changes=0, collection_executed=args.collect))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", type=date.fromisoformat, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--collect", action="store_true")
    args = parser.parse_args()
    os.environ.update(THESIS_MONITOR_ENV_FILE=str(args.env_file), DATABASE_URL="sqlite:///:memory:",
        DATA_DIR=str(args.output / "isolated-data"), ENABLE_LIVE_PROVIDERS="false",
        NOTIFICATION_DRY_RUN="true", TELEGRAM_BOT_TOKEN="", TELEGRAM_CHAT_ID="", TELEGRAM_TEST_CHAT_ID="",
        PERSISTENCE_V2_WRITER_ENABLED="false", PERSISTENCE_V2_OUTBOX_DELIVERY_ENABLED="false",
        MONITOR_RETRY_ATTEMPTS="1", OHLCV_TIMEOUT_SECONDS="20")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
