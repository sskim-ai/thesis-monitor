import asyncio
import base64
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json

import httpx
import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.models.security import SecurityMaster
from app.providers.news import GoogleNewsRSSProvider, NaverNewsProvider
from app.services.unified_event_acquisition import EventAcquisition
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_stock_event_input import (
    BoundNewsInput, NewsRead, PlannedNewsTransport, make_read, replay_news,
)
from app.services.unified_stock_owner import assemble_stock, validate_assembled
from test_unified_stock_owner import source as source_fixture, freeze_hashes


@pytest.fixture
def source():
    return source_fixture.__wrapped__()


def wire(tmp_path, source, *, title="Fixture awarded large order supply contract signed", future=False,
         summary="Fixture supply contract signed", market='us', http_status=200):
    security = next(r['record'] for r in source['financial']['projection']['records'] if r['table'] == 'securitymaster')
    target = SecurityMaster.model_validate(security)
    records = [target.model_dump(mode='json')]
    provider = GoogleNewsRSSProvider if market == 'us' else NaverNewsProvider
    policy = UnifiedSourcePolicy(source['policy'].allowed_providers | {provider.name})
    read = make_read(security=security, market=market, run_id='synthetic-one-shot', lookback_days=3, security_records=records)
    at = datetime.now(timezone.utc) + (timedelta(hours=1) if future else -timedelta(minutes=1))
    body = f'<rss><channel><item><title>{title}</title><link>https://example.test/order</link><pubDate>{at.strftime("%a, %d %b %Y %H:%M:%S GMT")}</pubDate><description>{summary}</description><source>Fixture News</source></item></channel></rss>'.encode()
    if market == 'kr':
        body = json.dumps({'items': [{'title': title, 'originallink': 'https://example.test/order',
            'pubDate': at.strftime('%a, %d %b %Y %H:%M:%S GMT'), 'description': summary}]}).encode()
    transport = PlannedNewsTransport(read=read, root=tmp_path / 'wire', policy=policy,
        inner=httpx.MockTransport(lambda r: httpx.Response(http_status, content=body)))
    engine = create_engine('sqlite://')
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(target)
        session.commit()
        owner = EventAcquisition(transport, cutoff=datetime.now(timezone.utc), max_attempts=1)
        asyncio.run(owner.collect(session, provider(), target, lookback_days=3, aliases=list(read.aliases)))
    engine.dispose()
    def enc(p):
        return base64.b64encode(p.read_bytes()).decode()
    value = BoundNewsInput(read=read, security_records=tuple(records),
        response_receipt_b64=enc(transport.root / 'read-0001.response.json'),
        normalization_b64=enc(transport.root / 'normalization.json'),
        raw_response_b64=enc(transport.root / 'read-0001.body'))
    return value, datetime.now(timezone.utc), policy, records[0]


def bind(source, value, cutoff, policy):
    source.update(event_source=value, business_cutoff=cutoff, policy=policy)
    freeze_hashes(source)
    source['expected_hashes'].update(events=digest(value.model_dump(mode='json')), business_cutoff=digest(cutoff.isoformat()))


def test_news_raw_replay_and_distinct_price_time(tmp_path, source):
    value, cutoff, policy, security = wire(tmp_path, source)
    bound = replay_news(value, security=security, business_cutoff=cutoff, policy=policy)
    assert len(bound['evidence']) == 1
    bind(source, value, cutoff, policy)
    result = assemble_stock(**source)
    assert result['status'] == 'PASS'
    assert result['packet']['source_time_domains']['price_source_frozen_at'] != cutoff.isoformat()
    assert result['packet']['stocks'][0]['technical_context']['as_of'] == source['plan'].frozen_at.isoformat()
    assert any(r.get('source_kind') == 'BUSINESS_EVENT' for r in result['observed_business_union'])
    assert validate_assembled(result, expected_result_sha256=digest(result))


@pytest.mark.parametrize('mode', ['body', 'query', 'normalized', 'identity', 'cutoff'])
def test_bound_news_fail_closed(tmp_path, source, mode):
    value, cutoff, policy, security = wire(tmp_path, source)
    data = value.model_dump(mode='json')
    if mode == 'body':
        data['raw_response_b64'] = base64.b64encode(b'not-original').decode()
    elif mode == 'query':
        data['read']['aliases'] = ['broader query']
    elif mode == 'normalized':
        norm = json.loads(base64.b64decode(data['normalization_b64']))
        norm['normalized'][0]['title'] = 'different title'
        norm['normalized_sha256'] = digest(norm['normalized'])
        data['normalization_b64'] = base64.b64encode(json.dumps(norm).encode()).decode()
    elif mode == 'identity':
        security = dict(security, ticker='OTHER')
    else:
        cutoff = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        replay_news(BoundNewsInput.model_validate(data), security=security, business_cutoff=cutoff, policy=policy)


def test_same_day_future_publication_not_promoted(tmp_path, source):
    value, cutoff, policy, security = wire(tmp_path, source, future=True)
    result = replay_news(value, security=security, business_cutoff=cutoff, policy=policy)
    assert result['evidence'] == []


def test_irrelevant_news_is_not_business_evidence(tmp_path, source):
    value, cutoff, policy, security = wire(tmp_path, source, title='Other company awarded a supply contract',
                                          summary='Other corporation signed a contract')
    data = value.model_dump(mode='json')
    # Source title belongs to another issuer; use raw replay's actual identity verdict.
    result = replay_news(BoundNewsInput.model_validate(data), security=security, business_cutoff=cutoff, policy=policy)
    assert result['candidates'][0]['relevance']['accepted'] is False
    assert result['evidence'] == []


def test_identity_match_without_business_relevance_is_denied(tmp_path, source):
    value, cutoff, policy, security = wire(tmp_path, source, title='Fixture conference', summary='Fixture meeting')
    result = replay_news(value, security=security, business_cutoff=cutoff, policy=policy)
    assert result['evidence'] == []
    assert result['selected'][0]['reason'] == 'business_relevance_failure'


def test_one_request_transport_rejects_repeat(tmp_path, source):
    value, _, policy, _ = wire(tmp_path, source)
    data = value.read.model_dump(mode='json')
    data['max_requests'] = 2
    with pytest.raises(ValueError):
        NewsRead.model_validate(data)
    read = value.read
    calls = []
    owner = PlannedNewsTransport(read=read, root=tmp_path / 'another', policy=policy,
        inner=httpx.MockTransport(lambda r: (calls.append(r), httpx.Response(200, json={}))[1]))
    async def run():
        request = httpx.Request('GET', read.request['route'], params=read.request['params'])
        await owner.handle_async_request(request)
        with pytest.raises(ValueError, match='budget'):
            await owner.handle_async_request(request)
        await owner.close_owner()
    asyncio.run(run())
    assert len(calls) == 1


def test_union_and_event_fact_mutation_rejected(tmp_path, source):
    value, cutoff, policy, _ = wire(tmp_path, source)
    bind(source, value, cutoff, policy)
    result = assemble_stock(**source)
    wrong = deepcopy(result)
    wrong['observed_business_cardinality'] += 1
    with pytest.raises(ValueError, match='union'):
        validate_assembled(wrong, expected_result_sha256=digest(wrong))


def test_financial_tuple_denial_survives_qualified_event(tmp_path, source, monkeypatch):
    import app.services.unified_stock_owner as owner
    value, cutoff, policy, _ = wire(tmp_path, source)
    bind(source, value, cutoff, policy)
    def denied(*args, **kwargs):
        raise ValueError('financial_selected_tuple_mismatch')
    monkeypatch.setattr(owner, '_financial', denied)
    result = assemble_stock(**source)
    assert result['status'] == 'PASS'
    assert result['financial_state']['status'] == 'DENIED'
    assert result['financial_state']['denials'] == ['financial_selected_tuple_mismatch']
    assert result['packet']['stocks'][0]['valuation'] == {}
    assert all(r.get('source_kind') == 'BUSINESS_EVENT' for r in result['observed_business_union'])
    assert validate_assembled(result, expected_result_sha256=digest(result))


def test_event_cannot_hide_financial_binding_tamper(tmp_path, source, monkeypatch):
    import app.services.unified_stock_owner as owner
    value, cutoff, policy, _ = wire(tmp_path, source)
    bind(source, value, cutoff, policy)
    def denied(*args, **kwargs):
        raise ValueError('financial_record_binding_mismatch')
    monkeypatch.setattr(owner, '_financial', denied)
    with pytest.raises(ValueError, match='financial_record_binding_mismatch'):
        assemble_stock(**source)


def test_naver_byte_replay_uses_existing_parser(tmp_path, source, monkeypatch):
    from app.config import get_settings
    monkeypatch.setattr(get_settings(), 'naver_client_id', 'synthetic-client')
    monkeypatch.setattr(get_settings(), 'naver_client_secret', 'synthetic-secret')
    value, cutoff, policy, security = wire(tmp_path, source, market='kr')
    result = replay_news(value, security=security, business_cutoff=cutoff, policy=policy)
    assert len(result['evidence']) == 1
    assert result == replay_news(value, security=security, business_cutoff=cutoff, policy=policy)


def test_http_denial_does_not_create_business_evidence(tmp_path, source):
    value, cutoff, policy, security = wire(tmp_path, source, http_status=403)
    result = replay_news(value, security=security, business_cutoff=cutoff, policy=policy)
    assert result['denial'] == 'event_owner_error:HTTP_403'
    assert not result['evidence']


def test_exact_twenty_plan_has_no_retained_subjects_duplicates_or_retries(source):
    from scripts.unified_event_union_proof import require_twenty, RETAINED
    from app.services.unified_stock_acquisition import UNIVERSE
    template = next(r['record'] for r in source['financial']['projection']['records'] if r['table'] == 'securitymaster')
    reads = []
    for market, tickers in UNIVERSE.items():
        for ticker in tickers:
            if ticker in RETAINED:
                continue
            security = SecurityMaster.model_validate(dict(template, ticker=ticker)).model_dump(mode='json')
            reads.append(make_read(security=security, market=market, run_id='plan-fixture', lookback_days=3,
                                   security_records=[security]))
    require_twenty(reads)
    assert [r.market for r in reads].count('us') == 14
    assert [r.market for r in reads].count('kr') == 6
    for field, value in [('retries', 1), ('redirects', True), ('max_attempts', 2)]:
        data = reads[0].model_dump(mode='json')
        data[field] = value
        with pytest.raises(ValueError):
            NewsRead.model_validate(data)
    with pytest.raises(ValueError):
        require_twenty(reads[:-1] + [reads[0]])
    with pytest.raises(ValueError):
        require_twenty(reads[:-1])
