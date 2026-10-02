from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import json

import httpx
import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.config import get_settings
from app.models.event import Event
from app.models.security import SecurityMaster
from app.providers.filings import OpenDARTProvider, SecEdgarProvider
from app.providers.news import GoogleNewsRSSProvider, NaverNewsProvider
from app.services.collection_service import CollectionService
from app.services.unified_event_acquisition import CachedEventRead, EventAcquisition, EventReceiptTransport
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_policy import UnifiedSourcePolicy


@pytest.fixture
def session():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(SecurityMaster(ticker="ACME", company_name="Acme Corporation",
            canonical_company_id="cik:1234", canonical_security_id="NASDAQ:ACME",
            identity_provider="sec_edgar", cik="1234", corp_code="00123456"))
        session.commit()
        yield session
    engine.dispose()


def acquisition(root, provider, handler=None, *, cache=(), cutoff=None, attempts=1, budget=4):
    transport = EventReceiptTransport(root=root, run_id="synthetic-events",
        acquisition_id="once", provider=provider,
        policy=UnifiedSourcePolicy(frozenset({provider, "sec_edgar"})),
        max_requests=budget, inner=httpx.MockTransport(handler) if handler else None, cache=cache)
    return EventAcquisition(transport, cutoff=cutoff or datetime.now(timezone.utc), max_attempts=attempts)


def collect(session, owner, provider):
    target = session.exec(select(SecurityMaster)).one()
    before = target.model_dump(mode="json")
    rows = asyncio.run(owner.collect(session, provider, target, lookback_days=5,
                                    aliases=["Acme Corporation"]))
    assert target.model_dump(mode="json") == before
    assert not session.new and not session.dirty and not session.deleted
    assert not session.exec(select(Event)).all()
    return rows


def rss(date=None):
    date = date or datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    return (f'<rss><channel><item><title>Acme Corporation revenue update</title>'
            f'<link>https://example.test/acme</link><pubDate>{date}</pubDate>'
            '<description>Acme Corporation published results.</description>'
            '<source>Fixture News</source></item></channel></rss>').encode()


def test_google_wire_and_exact_cache_preserve_publication_and_no_mutation(tmp_path, session):
    owner = acquisition(tmp_path / "wire", "google_news_rss", lambda _: httpx.Response(200, content=rss()))
    assert len(collect(session, owner, GoogleNewsRSSProvider())) == 1
    root = owner.transport.root
    norm = json.loads((root / "normalization.json").read_bytes())
    assert norm["normalized_sha256"] == digest(norm["normalized"])
    path = root / "read-0001.response.json"
    original = json.loads(path.read_bytes())
    cache = (CachedEventRead(root, path.name, hashlib.sha256(path.read_bytes()).hexdigest()),)
    replay = acquisition(tmp_path / "cache", "google_news_rss", cache=cache)
    assert len(collect(session, replay, GoogleNewsRSSProvider())) == 1
    current = json.loads((replay.transport.root / path.name).read_bytes())
    assert current["outcome"] == "CACHE_SOURCE_OPEN"
    assert current["original_received_at"] == original["received_at"]
    assert json.loads((replay.transport.root / "normalization.json").read_bytes())["normalized"] == norm["normalized"]


@pytest.mark.parametrize("published", ["invalid", "Mon, 01 Jan 2040 00:00:00 GMT",
                                      "Tue, 01 Jan 2019 00:00:00 GMT"])
def test_publication_not_inferred_or_outside_window(tmp_path, session, published):
    owner = acquisition(tmp_path / "wire", "google_news_rss",
                        lambda _: httpx.Response(200, content=rss(published)))
    assert collect(session, owner, GoogleNewsRSSProvider()) == []
    assert json.loads((owner.transport.root / "normalization.json").read_bytes())["denial"]


def test_failure_then_bounded_retry_has_both_receipts(tmp_path, session):
    calls = []
    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            raise httpx.ConnectError("not exported", request=request)
        return httpx.Response(200, content=rss())
    owner = acquisition(tmp_path / "wire", "google_news_rss", handler, attempts=2)
    assert len(collect(session, owner, GoogleNewsRSSProvider())) == 1
    norm = json.loads((owner.transport.root / "normalization.json").read_bytes())
    assert len(norm["children"]) == 2
    assert len(norm["attempts"]) == 2
    assert "not exported" not in "".join(p.read_text() for p in owner.transport.root.iterdir())
    assert json.loads((owner.transport.root / "read-0001.response.json").read_bytes())["outcome"] == "TRANSPORT_ERROR"


@pytest.mark.parametrize("mode", ["provider", "raw", "future"])
def test_cache_prohibited_tampered_future_fail_closed(tmp_path, session, mode):
    owner = acquisition(tmp_path / "wire", "google_news_rss", lambda _: httpx.Response(200, content=rss()))
    collect(session, owner, GoogleNewsRSSProvider())
    root = owner.transport.root
    path = root / "read-0001.response.json"
    receipt = json.loads(path.read_bytes())
    if mode == "provider":
        receipt["provider"] = "alpha_vantage"
    elif mode == "raw":
        (root / receipt["artifact"]).write_bytes(b"changed")
    else:
        receipt["received_at"] = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    path.write_text(json.dumps(receipt))
    cached = (CachedEventRead(root, path.name, hashlib.sha256(path.read_bytes()).hexdigest()),)
    replay = acquisition(tmp_path / "cache", "google_news_rss", cache=cached)
    assert collect(session, replay, GoogleNewsRSSProvider()) == []
    assert json.loads((replay.transport.root / "normalization.json").read_bytes())["denial"]
    assert json.loads((replay.transport.root / "read-0001.response.json").read_bytes())["outcome"] == "CACHE_DENIED"


def test_sec_bound_issuer_and_nested_owner_receipt(tmp_path, session, monkeypatch):
    monkeypatch.setattr(get_settings(), "sec_user_agent", "fixture operator")
    payload = {"cik": 1234, "name": "Acme Corporation", "filings": {"recent": {
        "form": ["10-Q"], "filingDate": [datetime.now(timezone.utc).date().isoformat()],
        "accessionNumber": ["0000001234-26-000001"], "primaryDocument": ["acme.htm"]}}}
    owner = acquisition(tmp_path / "sec", "sec_edgar", lambda _: httpx.Response(200, json=payload))
    assert len(collect(session, owner, SecEdgarProvider())) == 1
    assert owner.transport.ordinal == 1
    payload["cik"] = 9876
    wrong = acquisition(tmp_path / "wrong", "sec_edgar", lambda _: httpx.Response(200, json=payload))
    assert collect(session, wrong, SecEdgarProvider()) == []


def test_naver_receipts_exclude_credentials(tmp_path, session, monkeypatch):
    monkeypatch.setattr(get_settings(), "naver_client_id", "fixture-id")
    monkeypatch.setattr(get_settings(), "naver_client_secret", "fixture-secret")
    def handler(request):
        assert request.headers["X-Naver-Client-Secret"] == "fixture-secret"
        return httpx.Response(200, json={"items": []})
    owner = acquisition(tmp_path / "naver", "naver_news", handler)
    assert collect(session, owner, NaverNewsProvider()) == []
    assert "fixture-secret" not in "".join(p.read_text() for p in owner.transport.root.iterdir())


def test_opendart_no_unobserved_corp_code_lookup(tmp_path, session, monkeypatch):
    monkeypatch.setattr(get_settings(), "opendart_api_key", "fixture-dart-secret")
    def handler(request):
        assert request.url.params["corp_code"] == "00123456"
        assert request.url.path == "/api/list.json"
        return httpx.Response(200, json={"status": "013", "list": []})
    owner = acquisition(tmp_path / "dart", "opendart", handler)
    assert collect(session, owner, OpenDARTProvider()) == []
    assert owner.transport.ordinal == 1
    assert "fixture-dart-secret" not in "".join(p.read_text() for p in owner.transport.root.iterdir())


def test_opendart_nested_statement_reads_all_have_receipts(tmp_path, session, monkeypatch):
    monkeypatch.setattr(get_settings(), "opendart_api_key", "fixture-dart-secret")
    calls = []
    def handler(request):
        calls.append(request.url.path)
        if request.url.path == "/api/list.json":
            return httpx.Response(200, json={"status": "000", "list": [{
                "rcept_no": datetime.now(timezone.utc).strftime("%Y%m%d") + "000001",
                "rcept_dt": datetime.now(timezone.utc).strftime("%Y%m%d"),
                "report_nm": "\ubc18\uae30\ubcf4\uace0\uc11c", "corp_name": "Acme Corporation",
                "corp_code": "00123456", "stock_code": "ACME"}]})
        return httpx.Response(200, json={"status": "013", "list": []})
    owner = acquisition(tmp_path / "dart", "opendart", handler, budget=20)
    assert len(collect(session, owner, OpenDARTProvider())) == 1
    assert "/api/fnlttSinglAcntAll.json" in calls and len(calls) > 2
    norm = json.loads((owner.transport.root / "normalization.json").read_bytes())
    assert len(norm["children"]) == len(calls)
    assert "fixture-dart-secret" not in "".join(p.read_text() for p in owner.transport.root.iterdir())


def test_collection_qualified_detached_path_not_blanket_denied(tmp_path, session):
    owner = acquisition(tmp_path / "google", "google_news_rss", lambda _: httpx.Response(200, content=rss()))
    service = CollectionService(source_policy=owner.transport.policy,
                                event_acquisitions={"google_news_rss": owner})
    service.providers = [GoogleNewsRSSProvider()]
    assert len(asyncio.run(service.collect_events(session, "ACME", 5))) == 1
    assert not session.dirty and not session.new and not session.exec(select(Event)).all()


@pytest.mark.parametrize("provider", ["alpha_vantage", "mock", "undeclared"])
def test_prohibited_provider_before_transport(tmp_path, provider):
    with pytest.raises(ValueError):
        acquisition(tmp_path / "no-call", provider, lambda _: pytest.fail("unexpected call"))


def test_unqualified_event_history_api_still_denied(session):
    service = CollectionService(source_policy=UnifiedSourcePolicy(frozenset({"sec_edgar"})))
    with pytest.raises(ValueError, match="cache_not_source_qualified"):
        asyncio.run(service.get_thesis_events(session, "ACME", 5, auto_backfill=True))
