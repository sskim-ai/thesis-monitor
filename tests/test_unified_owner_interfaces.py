from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
import hashlib
import json

import httpx
import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings
from app.macro.providers.finnhub import FinnhubEarningsProvider
from app.macro.providers.market import MARKET_SYMBOLS, OhlcvMarketProvider
from app.models.event import Event
from app.models.financial import FinancialSnapshot
from app.models.security import SecurityMaster
from app.models.thesis import InvestmentThesis
from app.models.watchlist import WatchlistItem
from app.providers.kiwoom_rest_client import KiwoomRestClient, KiwoomRestError
from app.providers.nasdaq_trader_breadth_provider import NasdaqTraderBreadthProvider
from app.services.collection_service import CollectionService
from app.services.financial_freshness_service import (
    FinancialFreshnessService, evaluate_financial_freshness_records,
)
from app.services.kiwoom_kr_market_context_service import (
    KiwoomKrMarketContextService, kiwoom_market_reads,
)
from app.services.unified_kiwoom_observer import KiwoomReceiptObserver
from app.services.unified_persisted_projection import project_financial_freshness, project_local_seed
from app.services.unified_run_acquisition import RunAcquisitionObserver, RunRead
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_observer import OhlcvRead, OhlcvReceiptObserver
from app.services.unified_source_policy import UnifiedSourcePolicy
from test_kiwoom_rest_market_context import _handler, SESSION_DATE, OBSERVED_AT


US_SESSION = date(2026, 8, 25)
US_CUTOFF = datetime(2026, 8, 26, 0, 0, tzinfo=timezone.utc)


def market_observer(root, *, attempt="A", symbols=None):
    reads = tuple(OhlcvRead(role=f"us_market_prices:{symbol}", symbol=symbol,
        market="us", provider="ohlcv_analyst", period="daily", adjusted=True,
        session_date=US_SESSION, max_requests=1, params={"symbol": symbol, "market": "US",
            "periods": "daily", "count": 2, "include_indicators": "false",
            "indicator_limit": 0, "adjusted": "true"}) for symbol in (symbols or MARKET_SYMBOLS))
    return OhlcvReceiptObserver(root=root, run_id="synthetic-run", attempt_id=attempt,
        reads=reads, policy=UnifiedSourcePolicy(frozenset({"ohlcv_analyst"})))


def market_transport(calls, *, corrupt=None):
    def handler(request):
        symbol = request.url.params["symbol"]
        calls.append(symbol)
        payload = {"resolved_symbol": {"code": symbol},
                   "meta": {"provider": "ohlcv_analyst", "adjusted": True},
                   "periods": {"daily": [{"date": US_SESSION.isoformat(), "close": 100}]}}
        if symbol == "SPY" and corrupt:
            corrupt(payload)
        return httpx.Response(200, json=payload)
    return httpx.MockTransport(handler)


def test_us_whole_set_receipts_and_no_attempt_reuse(tmp_path):
    for attempt in ("A", "B", "C"):
        root = tmp_path / attempt
        observer = market_observer(root, attempt=attempt)
        calls = []
        provider = OhlcvMarketProvider(market_transport(calls), source_observer=observer)
        result = asyncio.run(provider.collect(US_CUTOFF))
        assert len(result.observations) == len(MARKET_SYMBOLS) == len(calls)
        assert len(list(root.glob("*.response.json"))) == len(calls)
        for path in root.glob("*.normalization.json"):
            normalized = json.loads(path.read_bytes())
            assert normalized["attempt_id"] == attempt
            assert digest(normalized["normalized"]) == normalized["normalized_sha256"]
            response = json.loads(path.with_name(path.name.replace("normalization", "response")).read_bytes())
            assert hashlib.sha256((root / response["artifact"]).read_bytes()).hexdigest() == response["artifact_sha256"]
            assert digest(response) == normalized["response_receipt_sha256"]
        with pytest.raises(ValueError, match="whole_fresh_market"):
            asyncio.run(provider.collect(US_CUTOFF))
    with pytest.raises(ValueError, match="new_source_attempt"):
        market_observer(tmp_path / "A")


@pytest.mark.parametrize("corrupt", [
    lambda p: p["resolved_symbol"].update(code="WRONG"),
    lambda p: p["meta"].update(adjusted=False),
    lambda p: p["meta"].update(upstream_provider="alpha_vantage"),
    lambda p: p["periods"]["daily"][0].update(date="2026-08-24"),
    lambda p: p["periods"]["daily"][0].update(date="2026-08-27"),
])
def test_us_bad_identity_session_basis_cannot_become_observation(tmp_path, corrupt):
    observer = market_observer(tmp_path / "A")
    result = asyncio.run(OhlcvMarketProvider(market_transport([], corrupt=corrupt),
                                            source_observer=observer).collect(US_CUTOFF))
    assert "SPY" not in {o.series_code for o in result.observations}
    assert len(result.warnings) == 1
    assert len(list(observer.root.glob("*.normalization.json"))) == len(MARKET_SYMBOLS) - 1


def test_us_partial_plan_no_dispatch(tmp_path):
    calls = []
    provider = OhlcvMarketProvider(market_transport(calls),
                                  source_observer=market_observer(tmp_path / "A", symbols=["SPY"]))
    with pytest.raises(ValueError, match="whole_fresh_market"):
        asyncio.run(provider.collect(US_CUTOFF))
    assert calls == []


def kr_service(root, *, transport=None, pages=5, retries=0):
    observer = KiwoomReceiptObserver(root=root, run_id="synthetic-kr", attempt_id=root.name,
        session_date=SESSION_DATE, reads=kiwoom_market_reads(session_date=SESSION_DATE,
            max_pages=pages, max_requests_per_page=retries + 1),
        policy=UnifiedSourcePolicy(frozenset({"kiwoom_rest"})))
    client = KiwoomRestClient(app_key="synthetic-app", secret_key="synthetic-secret",
        source_observer=observer, transport=transport or _handler([]), max_retries=retries,
        request_interval_seconds=0)
    return KiwoomKrMarketContextService(client, max_pages=pages), observer


def test_kr_data_pages_not_oauth_and_page_set_normalization(tmp_path):
    service, observer = kr_service(tmp_path / "A")
    collection = asyncio.run(service.collect(session_date=SESSION_DATE, observed_at=OBSERVED_AT))
    receipt = json.loads((observer.root / "normalization.json").read_bytes())
    assert receipt["mandatory_complete"]
    assert receipt["page_sets_sha256"] == digest(receipt["page_sets"])
    assert len(list(observer.root.glob("*.response.json"))) == 12
    assert len(receipt["page_sets"]["KOSPI:ka10066"]) == 2
    assert all(v["status"] == "AVAILABLE" for v in receipt["roles"].values())
    assert receipt["owner_audit"] == collection.audit.model_dump(mode="json")
    for file in observer.root.iterdir():
        content = file.read_text()
        assert "test-access-token" not in content
        assert "synthetic-secret" not in content
        assert "synthetic-app" not in content
        assert "/oauth2" not in content
        assert "authorization" not in content
    with pytest.raises(ValueError, match="new_whole_attempt"):
        asyncio.run(service.collect(session_date=SESSION_DATE, observed_at=OBSERVED_AT))


def test_kr_retry_receipt_and_optional_incomplete_page_denial(tmp_path):
    original = _handler([])
    calls = []
    def handler(request):
        if request.url.path != "/oauth2/token":
            calls.append(request.headers["api-id"])
            if len(calls) == 1:
                return httpx.Response(429, headers={"Retry-After": "0"})
        return original.handle_request(request)
    service, observer = kr_service(tmp_path / "A", transport=httpx.MockTransport(handler), pages=1, retries=1)
    asyncio.run(service.collect(session_date=SESSION_DATE, observed_at=OBSERVED_AT))
    receipt = json.loads((observer.root / "normalization.json").read_bytes())
    assert receipt["mandatory_complete"]
    flow = receipt["roles"]["kr_market_investor_flows"]
    assert flow == {"status": "OPTIONAL_UNAVAILABLE", "value": None, "value_sha256": None}
    assert len(list(observer.root.glob("*.response.json"))) == 11
    assert json.loads((observer.root / "read-0001.response.json").read_bytes())["http_status"] == 429


@pytest.mark.parametrize("api_id,mandatory", [("ka20003", True), ("ka10051", False)])
def test_kr_missing_read_retains_failure_and_no_invented_values(tmp_path, api_id, mandatory):
    original = _handler([])
    def handler(request):
        if request.headers.get("api-id") == api_id:
            raise httpx.ConnectError("sensitive endpoint text", request=request)
        return original.handle_request(request)
    service, observer = kr_service(tmp_path / "A", transport=httpx.MockTransport(handler))
    if mandatory:
        with pytest.raises(KiwoomRestError):
            asyncio.run(service.collect(session_date=SESSION_DATE, observed_at=OBSERVED_AT))
    else:
        asyncio.run(service.collect(session_date=SESSION_DATE, observed_at=OBSERVED_AT))
    receipt = json.loads((observer.root / "normalization.json").read_bytes())
    assert receipt["mandatory_complete"] is not mandatory
    assert receipt["roles"]["kr_market_investor_flows"]["value"] is None
    assert "sensitive endpoint text" not in "".join(f.read_text() for f in observer.root.iterdir())


def test_kr_cross_attempt_page_and_cursor_rejected_before_call(tmp_path):
    _service, a = kr_service(tmp_path / "A")
    _service, b = kr_service(tmp_path / "B")
    a.begin(SESSION_DATE, OBSERVED_AT)
    b.begin(SESSION_DATE, OBSERVED_AT)
    read = a.reads[0]
    async def capture():
        async with httpx.AsyncClient(base_url="https://api.kiwoom.test", transport=_handler([])) as client:
            return await a.post(client, endpoint=read.endpoint, api_id=read.api_id,
                body=read.body, headers={"api-id": read.api_id}, continuation=False, next_key="")
    response = asyncio.run(capture())
    with pytest.raises(ValueError, match="foreign_or_consumed"):
        b.accept_page(response, continuation=False, next_key="")
    with pytest.raises(ValueError, match="page_chain"):
        b.preflight(read.endpoint, read.api_id, read.body, True, "from-another-attempt")


def run_observer(root, *, provider, role, route, params):
    return RunAcquisitionObserver(root=root, run_id="synthetic-run", acquisition_id="acquisition-1",
        provider=provider, role=role, reads=(RunRead(key="data", route=route, params=params,
            max_requests=1),), policy=UnifiedSourcePolicy(frozenset({provider})))


def test_calendar_run_identity_source_time_and_secret_exclusion(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "finnhub_api_key", "synthetic-calendar-secret")
    observer = run_observer(tmp_path / "calendar", provider="finnhub_earnings", role="earnings_calendar",
        route="/api/v1/calendar/earnings", params={"from": "2026-08-25", "to": "2026-08-28"})
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json={"earningsCalendar": [
        {"symbol": "MSFT", "date": "2026-08-27", "quarter": 2, "epsActual": None, "epsEstimate": 3}]}))
    provider = FinnhubEarningsProvider(transport, source_observer=observer)
    result = asyncio.run(provider.collect(US_CUTOFF))
    assert result.events[0].event_status == "scheduled"
    path = observer.root / "normalization.json"
    frozen = path.read_bytes()
    receipt = json.loads(frozen)
    assert receipt["acquisition_id"] == "acquisition-1"
    assert "attempt_id" not in receipt
    assert receipt["normalized"]["events"][0]["scheduled_at"].startswith("2026-08-27")
    for _ in range(3):
        with pytest.raises(ValueError, match="reuse_mismatch"):
            asyncio.run(provider.collect(US_CUTOFF + timedelta(minutes=5)))
        assert path.read_bytes() == frozen
    assert "synthetic-calendar-secret" not in "".join(f.read_text() for f in observer.root.iterdir())


@pytest.mark.parametrize("failure", ["transport", "http", "not_configured"])
def test_optional_calendar_failure_is_run_bound(tmp_path, monkeypatch, failure):
    monkeypatch.setattr(get_settings(), "finnhub_api_key", "" if failure == "not_configured" else "fixture")
    observer = run_observer(tmp_path / "calendar", provider="finnhub_earnings", role="earnings_calendar",
        route="/api/v1/calendar/earnings", params={"from": "2026-08-25", "to": "2026-08-28"})
    def handler(r):
        if failure == "transport":
            raise httpx.ReadTimeout("do not serialize", request=r)
        return httpx.Response(503)
    result = asyncio.run(FinnhubEarningsProvider(httpx.MockTransport(handler), source_observer=observer).collect(US_CUTOFF))
    assert result.events == []
    receipt = json.loads((observer.root / "normalization.json").read_bytes())
    assert receipt["status"] == "UNAVAILABLE"
    assert receipt["acquisition_id"] == "acquisition-1"
    assert len(receipt["reads"]) == (0 if failure == "not_configured" else 1)


def test_breadth_owner_receipt_raw_and_temporal_binding(tmp_path):
    observer = run_observer(tmp_path / "breadth", provider="nasdaq_trader", role="us_exchange_breadth",
        route="/dynamic/dailyfiles/daily2026.csv", params={})
    payload = b"Date,Advances,Declines,Unchanged\n08/25/2026 00:00:00,100,80,20\n"
    result, raw = asyncio.run(NasdaqTraderBreadthProvider(source_observer=observer,
        transport=httpx.MockTransport(lambda r: httpx.Response(200, content=payload))).collect(
            session_date=US_SESSION, retrieved_at=US_CUTOFF))
    receipt = json.loads((observer.root / "normalization.json").read_bytes())
    assert raw == payload
    assert receipt["normalized"] == result.model_dump(mode="json")
    assert result.observation.session_date == US_SESSION
    assert result.source_payload_sha256 == hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize("period,filing,as_of", [
    (date(2026, 6, 30), date(2026, 8, 1), date(2026, 8, 26)),
    (date(2026, 9, 30), date(2026, 8, 1), date(2026, 8, 26)),
    (date(2025, 6, 30), date(2025, 8, 1), date(2026, 8, 26)),
])
def test_financial_readonly_and_mutation_path_share_semantics(period, filing, as_of):
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        row = FinancialSnapshot(ticker="FIX", period="FY", provider="sec_edgar",
            financial_period_end=period, filing_date=filing, reported_date=filing)
        session.add(row)
        session.commit()
        session.refresh(row)
        before = deepcopy(row.model_dump())
        decision, _events, copies = evaluate_financial_freshness_records([], [row], as_of=as_of)
        assert row.model_dump() == before
        assert not session.dirty
        legacy = FinancialFreshnessService().assess(session, "FIX", as_of=as_of)
        assert decision == legacy
        assert row.model_dump() == copies[0].model_dump()


def test_financial_projection_readonly_exact_versions_and_future_exclusion():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        rows = [FinancialSnapshot(ticker="FIX", period="Q2", provider=provider,
            financial_period_end=date(2026, 6, 30), filing_date=filing) for provider, filing in (
                ("sec_edgar", date(2026, 8, 1)), ("alpha_vantage", date(2026, 8, 1)),
                ("sec_edgar", date(2026, 9, 1)))]
        session.add_all(rows)
        session.commit()
        for row in rows:
            session.refresh(row)
        before = [r.model_dump() for r in rows]
        result = project_financial_freshness(session, ticker="FIX", cutoff=US_CUTOFF,
            policy=UnifiedSourcePolicy(frozenset({"sec_edgar"})))
        assert len(result["records"]) == 1
        assert result["version"] == digest(result["records"])
        assert result["source_receipt"] is None
        assert result["production_seed_qualified"] is False
        assert [r.model_dump() for r in rows] == before
        assert not session.dirty and not session.new
        rows[0].revenue = 200
        with pytest.raises(ValueError, match="clean_read_session"):
            project_financial_freshness(session, ticker="FIX", cutoff=US_CUTOFF,
                policy=UnifiedSourcePolicy(frozenset({"sec_edgar"})))


def test_local_seed_uses_current_owner_eligibility_without_ensure():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(WatchlistItem(ticker="FIX", company_name="Fixture", exchange="NASDAQ",
            created_at=US_CUTOFF, activated_at=US_CUTOFF))
        session.add(SecurityMaster(ticker="FIX", company_name="Fixture", canonical_company_id="issuer:fix",
            canonical_security_id="security:fix", exchange="NASDAQ", country="US",
            issuer_type="domestic_us", identity_provider="local", updated_at=US_CUTOFF))
        session.add(InvestmentThesis(ticker="FIX", version=1, core_thesis="Fixture thesis", created_at=US_CUTOFF))
        session.commit()
        policy = UnifiedSourcePolicy(frozenset({"canonical_local", "local"}))
        result = project_local_seed(session, market="us", session_key="2026-08-25", cutoff=US_CUTOFF, policy=policy)
        assert result["universe"]["eligible_subjects"] == ["FIX"]
        assert all(v["eligible"] for v in result["roles"].values())
        assert all(v["version"] == digest(v["records"]) for v in result["roles"].values())
        assert not session.new and not session.dirty and not session.deleted
        assert "thesisassessment" not in json.dumps(result)
        assert "latest_status" not in json.dumps(result)


@pytest.mark.parametrize("provider", ["alpha_vantage", "massive", "mock", "undeclared", "sec_edgar"])
def test_collection_nested_paths_closed_before_db_or_live(provider):
    class ForbiddenSession:
        def __getattr__(self, name):
            raise AssertionError("DB must not be reached")
    class Provider:
        name = provider
        async def fetch_events(self, *args, **kwargs):
            raise AssertionError("network must not be reached")
    service = CollectionService(source_policy=UnifiedSourcePolicy(frozenset({"sec_edgar"})))
    with pytest.raises(ValueError):
        asyncio.run(service._fetch_provider_events(ForbiddenSession(), Provider(), "FIX", 7, [], "domestic_us"))
    with pytest.raises(ValueError, match="wire_owner_not_qualified"):
        asyncio.run(service.collect_events(ForbiddenSession(), "FIX", 7))
    with pytest.raises(ValueError, match="versioned_owner"):
        asyncio.run(service.get_company_profile(ForbiddenSession(), "FIX"))
    result = asyncio.run(service.get_earnings_checkpoints(ForbiddenSession(), "FIX"))
    assert result.provider_status == "unavailable"


def test_freshness_event_changes_are_proposals_only():
    event = Event(ticker="FIX", company_name="Fixture", event_type="financial_report",
        date=date(2026, 8, 25), provider="sec_edgar", source="official fixture",
        title="Quarterly filing", url="https://example.test",
        reporting_period_end=date(2026, 6, 30), financial_refresh_required=True)
    before = event.model_dump()
    evaluate_financial_freshness_records([event], [], as_of=date(2026, 8, 26))
    assert event.model_dump() == before


@pytest.mark.parametrize("unavailable", [False, True])
def test_night_run_acquisition_data_reads_and_product_denial(tmp_path, monkeypatch, unavailable):
    from app.jobs.probe_krx_night_futures import KRX_FUTURES_DAILY_URL
    from app.macro.providers.krx import KrxNightFuturesProvider
    from test_krx_night_futures_probe import _row
    monkeypatch.setattr(get_settings(), "krx_open_api_key", "synthetic-krx-secret")
    root = tmp_path / "night"
    as_of = datetime(2026, 8, 25, 23, 10, tzinfo=timezone.utc)
    days = [date(2026, 8, 26) - timedelta(days=n) for n in range(7)]
    observer = RunAcquisitionObserver(root=root, run_id="synthetic-run", acquisition_id="night-once",
        provider="krx_night_futures", role="night_and_publication_context",
        reads=tuple(RunRead(key=d.isoformat(), route=KRX_FUTURES_DAILY_URL,
                           params={"basDd": d.strftime("%Y%m%d")}, max_requests=1) for d in days),
        policy=UnifiedSourcePolicy(frozenset({"krx_night_futures"})))
    def handler(request):
        day = request.url.params["basDd"]
        if unavailable:
            return httpx.Response(200, json={"OutBlock_1": []})
        rows = []
        for product, code, name in (
            ("KOSPI 200 \uc120\ubb3c", "A0169000", "\ucf54\uc2a4\ud53c200 F 202609"),
            ("KOSDAQ 150 \uc120\ubb3c", "A0669000", "\ucf54\uc2a4\ub2e5150 F 202609"),
        ):
            if day == "20260826":
                rows.append(_row(product, "\uc57c\uac04", code, name, "101", day, "+1"))
            elif day == "20260825":
                rows.append(_row(product, "\uc815\uaddc", code, name, "100", day))
        return httpx.Response(200, json={"OutBlock_1": rows})
    provider = KrxNightFuturesProvider(source_observer=observer,
        transport=httpx.MockTransport(handler), history_directory=tmp_path / "private-history")
    result = asyncio.run(provider.collect(as_of))
    receipt = json.loads((root / "normalization.json").read_bytes())
    assert receipt["status"] == ("UNAVAILABLE" if unavailable else "OWNER_NORMALIZED")
    assert len(result.observations) == (0 if unavailable else 1)
    assert len(receipt["reads"]) == (7 if unavailable else 2)
    assert "synthetic-krx-secret" not in "".join(f.read_text() for f in root.iterdir())
    assert all(row["receipt"]["acquisition_id"] == "night-once" for row in receipt["reads"])
    frozen = (root / "normalization.json").read_bytes()
    with pytest.raises(ValueError, match="reuse_mismatch"):
        asyncio.run(provider.collect(as_of + timedelta(minutes=5)))
    assert (root / "normalization.json").read_bytes() == frozen


def test_readonly_valuation_does_not_sync_dividend_or_taint_rows(tmp_path, monkeypatch):
    from app.services.valuation_snapshot_service import ValuationSnapshotService
    from app.models.financial import DividendHistory
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    service = ValuationSnapshotService(source_policy=UnifiedSourcePolicy(frozenset({"sec_edgar"})))
    def forbidden(*args, **kwargs):
        raise AssertionError("No mutation owner invocation")
    monkeypatch.setattr(service.dividend_service, "sync_financial_snapshots", forbidden)
    monkeypatch.setattr(service.dividend_service, "sync_capital_returns", forbidden)
    with Session(engine) as session:
        row = FinancialSnapshot(ticker="FIX", period="FY", provider="alpha_vantage",
                                financial_period_end=date(2026, 9, 30), filing_date=date(2026, 8, 1))
        session.add(row)
        session.add(DividendHistory(ticker="FIX", fiscal_year=2025, provider="alpha_vantage",
                                   source="synthetic", dividend_per_share=100))
        session.commit()
        session.refresh(row)
        before = row.model_dump()
        assert service._financial_rows(session, "FIX") == []
        assert row.model_dump() == before and not session.dirty
        from app.schemas.thesis import PriceContext
        result = asyncio.run(service.fetch("FIX", "NASDAQ", PriceContext(),
                                           as_of=US_CUTOFF, session=session))
        assert result.estimate_provider != "alpha_vantage"
        assert not session.new and not session.dirty


def test_night_unified_cannot_silently_use_shared_history(tmp_path):
    from app.macro.providers.krx import KrxNightFuturesProvider
    observer = run_observer(tmp_path / "night", provider="krx_night_futures",
        role="night_and_publication_context", route="https://data-dbg.krx.co.kr/data", params={})
    with pytest.raises(ValueError, match="history_directory_required"):
        KrxNightFuturesProvider(source_observer=observer)
    with pytest.raises(ValueError, match="new_private_history"):
        KrxNightFuturesProvider(source_observer=observer, history_directory=tmp_path)


def test_disabled_breadth_has_explicit_run_denial(tmp_path, monkeypatch):
    from app.services.us_exchange_breadth_service import collect_and_persist_us_exchange_breadth
    monkeypatch.setattr(get_settings(), "nasdaq_us_exchange_breadth_enabled", False)
    observer = run_observer(tmp_path / "breadth", provider="nasdaq_trader", role="us_exchange_breadth",
        route="/dynamic/dailyfiles/daily2026.csv", params={})
    result = asyncio.run(collect_and_persist_us_exchange_breadth(session_date=US_SESSION,
        observed_at=US_CUTOFF, source_observer=observer))
    assert result["status"] == "NOT_ENABLED"
    receipt = json.loads((observer.root / "normalization.json").read_bytes())
    assert receipt["denial"] == "NOT_ENABLED" and receipt["reads"] == []
