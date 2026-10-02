import asyncio
from copy import deepcopy
from datetime import date, datetime
import json
from types import SimpleNamespace

import httpx
import pytest

from app.macro.providers.ecos import EcosProvider
from app.providers.news import GoogleNewsRSSProvider, NaverNewsProvider, serialize_news_request
from app.services.eligible_completed_session_bars import eligible_completed_roles
from app.services.kiwoom_kr_market_context_service import KiwoomKrMarketContextService
from app.services.macro_source_time import source_period
from app.services.price_structure_wave_fibonacci_v3_service import _calendar_for_range
from app.services.unified_event_acquisition import EventReceiptTransport
from app.services.unified_live_source_transport import SourceSafetyStop
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_stock_anomaly_scope import materialize_source_components
from app.services.unified_stock_owner import _technical

AT = "2026-09-29T00:29:11+00:00"
TARGET = date(2026, 9, 28)


def roles():
    _, cal = _calendar_for_range("KR", start=date(2025, 1, 1), end=date(2026, 9, 30))
    rows = [dict(date=str(s.date()), open=10, high=12, low=9, close=11, volume=100)
            for s in cal.sessions_in_range("2025-01-02", "2026-09-29")]
    return {k: deepcopy(rows) for k in ("adjusted_daily", "adjusted_weekly",
                                      "adjusted_monthly", "unadjusted_weekly_valuation")}


def select(raw, **kw):
    return eligible_completed_roles(raw, ticker="FIXTURE", market="kr", cutoff=TARGET,
                                    observed_at=AT, **kw)


def test_completed_selection_precedes_calculation_and_preserves_raw():
    raw = roles()
    before = deepcopy(raw)
    selected, receipt = select(raw)
    assert raw == before
    assert selected["adjusted_daily"][-1]["date"] == str(TARGET)
    assert receipt["roles"]["adjusted_daily"]["excluded_rows"] == [
        dict(date="2026-09-29", reason="OUT_OF_SCOPE_CURRENT_OR_FUTURE_SESSION")]
    for tf in ("weekly", "monthly"):
        assert selected["adjusted_" + tf][-1]["bar_state"] == "PARTIAL"
        assert receipt["roles"]["adjusted_" + tf]["derived_periods"][0]["input_dates"][-1] == str(TARGET)


@pytest.mark.parametrize("change", ["target_missing", "target_relabel", "basis", "duplicate"])
def test_completed_bar_negatives(change):
    raw = roles()
    if change == "target_missing":
        raw["adjusted_daily"] = [r for r in raw["adjusted_daily"] if r["date"] != str(TARGET)]
    elif change == "target_relabel":
        raw["adjusted_daily"][-1]["date"] = str(TARGET)
    elif change == "duplicate":
        raw["adjusted_daily"].append(raw["adjusted_daily"][-1])
    with pytest.raises(ValueError):
        select(raw, **({"adjustment_basis": "unadjusted"} if change == "basis" else {}))


@pytest.mark.parametrize("cycle,expected,granularity", [
    ("20260928", "2026-09-28", "daily"), ("202609", "2026-09-01", "monthly"),
    ("2026Q3", "2026-07-01", "quarterly"), ("2026", "2026-01-01", "annual")])
def test_source_period(cycle, expected, granularity):
    parsed, precision = source_period(cycle)
    assert (str(parsed), precision) == (expected, granularity)


@pytest.mark.parametrize("cycle", ["", "2026Q0", "2026Q5", "202613", "20260230", "20269", "today"])
def test_bad_source_cycle(cycle):
    with pytest.raises(ValueError):
        source_period(cycle)


def test_ecos_source_cycle_not_query_time():
    at = datetime.fromisoformat(AT)
    rows = [dict(KEYSTAT_NAME="원/달러 환율(종가)", CLASS_NAME="환율", DATA_VALUE="1365.1",
                 CYCLE="20260928", UNIT_NAME="원"),
            dict(KEYSTAT_NAME="M2(광의통화, 평잔)", DATA_VALUE="123", CYCLE="202607")]
    p = EcosProvider(httpx.MockTransport(lambda r: httpx.Response(200, json={"KeyStatisticList": {"row": rows}})),
                     clock=lambda: at)
    p.settings = SimpleNamespace(ecos_api_key="fixture", macro_provider_timeout_seconds=1)
    result = asyncio.run(p.collect(at))
    fx = next(r for r in result.observations if r.series_code == "USDKRW")
    assert str(fx.observed_at.date()) == "2026-09-28"
    assert fx.raw_payload["raw_cycle"] == "20260928"
    assert fx.raw_payload["publication_context"]["display_eligible"]
    assert {r.series_code for r in result.observations} == {"USDKRW", "KR_M2"}


@pytest.mark.parametrize("alias", ['Quoted "name"', "Comma, Inc.", "A B", "A&B", "A+B", "한글 회사"])
def test_google_single_wire_serializer(alias):
    url = GoogleNewsRSSProvider.request_url("FIXTURE", 7, search_aliases=[alias])
    provider = httpx.Request("GET", url)
    descriptor = serialize_news_request("GET", str(provider.url.copy_with(query=None)),
                                        list(provider.url.params.multi_items()))
    assert str(provider.url) == str(descriptor.url)


def test_naver_explicit_settings_ignore_ambient(monkeypatch):
    monkeypatch.setattr("app.providers.news.get_settings", lambda: SimpleNamespace(naver_client_id="", naver_client_secret=""))
    calls = []
    def send(r):
        calls.append(r)
        return httpx.Response(200, json={"items": []})
    settings = SimpleNamespace(naver_client_id="fixture-id", naver_client_secret="fixture-secret")
    p = NaverNewsProvider(settings=settings, transport=httpx.MockTransport(send))
    assert asyncio.run(p.fetch_events("FIXTURE", 7)) == []
    assert len(calls) == 1 and calls[0].headers["X-Naver-Client-Id"] == "fixture-id"


def test_pre_dispatch_denial_preserves_original(tmp_path):
    def deny(_):
        raise SourceSafetyStop("native_request_not_unique_sealed_slot")
    t = EventReceiptTransport(root=tmp_path / "event", run_id="generation", acquisition_id="read",
        provider="google_news_rss", policy=UnifiedSourcePolicy(frozenset({"google_news_rss"})),
        max_requests=1, inner=httpx.MockTransport(deny))
    with pytest.raises(SourceSafetyStop, match="native_request_not_unique"):
        asyncio.run(t.handle_async_request(httpx.Request("GET", GoogleNewsRSSProvider.request_url("FIXTURE", 7))))
    receipt = json.loads((t.root / "pre-dispatch-terminal.json").read_bytes())
    assert receipt["http_attempts"] == 0 and receipt["response_receipt"] == "NOT_CREATED"
    assert not list(t.root.glob("*.response.json"))
    assert receipt["denial_code"] == "native_request_not_unique_sealed_slot"


def test_current_and_completed_market_roles():
    history = {"inds_cur_prc_daly_rept": [
        dict(dt_n="20260929", cur_prc_n="9999", flu_rt_n="10"),
        dict(dt_n="20260928", cur_prc_n="6889.74", flu_rt_n="-2.7")]}
    row = KiwoomKrMarketContextService._completed_history_row(history=history,
        session_date=TARGET, observed_at=datetime.fromisoformat(AT))
    assert row["dt_n"] == "20260928" and row["cur_prc_n"] == "6889.74"
    with pytest.raises(ValueError):
        KiwoomKrMarketContextService._completed_history_row(history={"inds_cur_prc_daly_rept": []},
            session_date=TARGET, observed_at=datetime.fromisoformat(AT))


def test_completed_receipt_mutation_blocks_replay():
    raw = roles()
    args = dict(ticker="FIXTURE", market="kr", cutoff=TARGET, observed_at=AT)
    components = materialize_source_components(**args, roles=raw, completed_session=True)
    components["completed_session_bar_set"]["eligible_bar_set_sha256"] = digest("other")
    with pytest.raises(ValueError, match="completed_bar_set"):
        _technical(components, raw, **args)


def news_transport(tmp_path, market, inner, **kwargs):
    from app.models.security import SecurityMaster
    from app.services.unified_stock_event_input import make_read, PlannedNewsTransport
    s = SecurityMaster(id=1, ticker="FIXTURE", company_name="Fixture & Company",
        canonical_company_id="company:fixture", canonical_security_id="security:fixture")
    record = s.model_dump(mode="json")
    read = make_read(security=record, market=market, run_id="fresh",
        lookback_days=7, security_records=[record])
    return PlannedNewsTransport(read=read, root=tmp_path / "event", inner=inner,
        policy=UnifiedSourcePolicy(frozenset({read.provider})), **kwargs)


@pytest.mark.parametrize("mutation", ["order", "encoding", "added", "missing", "query", "host"])
def test_exact_news_wire_denies_before_dispatch(tmp_path, mutation):
    calls = []
    t = news_transport(tmp_path, "us", httpx.MockTransport(lambda r: calls.append(r)))
    spec = t.read.request
    req = serialize_news_request(spec["method"], spec["route"], spec["params"])
    url = str(req.url)
    if mutation == "order":
        url = str(serialize_news_request("GET", spec["route"], list(reversed(spec["params"]))).url)
    elif mutation == "encoding":
        url = url.replace("+", "%20")
    elif mutation == "added":
        url += "&extra=1"
    elif mutation == "missing":
        url = url.split("&ceid=")[0]
    elif mutation == "query":
        url = url.replace("company", "other")
    else:
        url = url.replace("news.google.com", "example.invalid")
    with pytest.raises(ValueError):
        asyncio.run(t.handle_async_request(httpx.Request("GET", url)))
    assert calls == [] and t.pre_dispatch_terminal["http_attempts"] == 0


@pytest.mark.parametrize("mode", ["missing", "mismatch"])
def test_naver_settings_binding_denies_without_exposure(tmp_path, mode):
    calls = []
    t = news_transport(tmp_path, "kr", httpx.MockTransport(lambda r: calls.append(r)),
                       settings_identity=digest(["right-id", "right-secret"]))
    settings = SimpleNamespace(naver_client_id="" if mode == "missing" else "wrong-id",
                               naver_client_secret="" if mode == "missing" else "wrong-secret")
    p = NaverNewsProvider(settings=settings, transport=t)
    with pytest.raises(ValueError):
        asyncio.run(p.fetch_events("FIXTURE", 7, search_aliases=list(t.read.aliases)))
    assert calls == [] and t.pre_dispatch_terminal
    assert all(b"wrong-secret" not in f.read_bytes() for f in t.root.iterdir() if f.is_file())


def test_kr_completed_consumer_allows_only_owned_history_without_breadth():
    from tests.test_r2b_r5_market_adapter import fixture, project
    packet, seed, graph = fixture("kr")
    source = graph["markets"]["kr"]
    value = dict(indices=[dict(symbol=m, label=m, close=100, return_pct=-1,
        source_ref=f"kiwoom:ka20009:{m}:2026-09-23") for m in ("KOSPI", "KOSDAQ")],
        sectors=[], breadth=None, breadth_by_scope=[])
    source["component"].update(value=value, value_sha256=digest(value))
    seed["attempt_hashes"]["kr"] = digest(source)
    graph["run_seed_sha256"] = digest(seed)
    packet.update(market_sources=deepcopy(source), run_seed_sha256=digest(seed),
                  authority_graph_sha256=digest(graph))
    result = project((packet, seed, graph))
    assert result["context"]["parity_status"] == "PASS"


def test_typed_absent_night_has_three_unavailable_horizons():
    from app.services.market_display_plan import build_display_plan
    source = dict(session=dict(latest_completed_regular_session_date="2026-09-28",
        assessment_date="2026-09-29", market="us"), fact_catalog=[], numeric_registry=[])
    result = build_display_plan(source, market="us", assessment_date="2026-09-29", eligible_refs=[])
    night = next(i for i in result.items if i.block_id == "night")
    assert night.status == "UNAVAILABLE" and night.text.count("자료 부족") == 3
    assert not night.fact_ids and not night.bindings
