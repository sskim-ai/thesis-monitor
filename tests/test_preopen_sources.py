import asyncio
from datetime import date, datetime, timedelta
from email.utils import format_datetime
from types import SimpleNamespace

import httpx

from app.config import Settings
from app.services import preopen_base, preopen_sources as sources


US_AT = datetime.fromisoformat('2026-11-30T08:30:00-05:00')
KR_AT = datetime.fromisoformat('2026-11-30T07:30:00+09:00')
OPEN = date.fromisoformat('2026-11-30')


def owned(ticker, *, provider, at, previous=(), cik=None, corp_code=None):
    watermark = dict(status='CHECKED', requested_at=at.isoformat(),
                     received_at=(at + timedelta(seconds=1)).isoformat(), ids=list(previous))
    return dict(ticker=ticker, preopen=dict(
        security=dict(ticker=ticker, canonical_security_id=f'sec:{ticker}',
                      canonical_company_id=f'corp:{ticker}', company_name=f'{ticker} Industries',
                      cik=cik, corp_code=corp_code),
        event_watermarks={provider: watermark}))


def execute(market, *, at, rows=(), handler=None, run_roots=None, window=timedelta(minutes=5), base_cutoff=None,
            **settings):
    return asyncio.run(sources.collect_preopen_sources(market, opening_session=OPEN, rows=rows,
        cutoff=at + window, run_roots=run_roots or {}, base_cutoff=base_cutoff, settings=Settings(_env_file=None,
        ohlcv_base_url=settings.pop('ohlcv_base_url', ''), **settings),
        enable_network=handler is not None, clock=lambda: at,
        transport=httpx.MockTransport(handler) if handler is not None else None))


def coverage(result, *, ticker, provider):
    return next(row for row in result['coverage']
                if row.get('ticker') == ticker and row['provider'] == provider)


def test_sec_uses_acceptance_timestamp_document_scope_and_amendment():
    older = '0000123456-26-000001'
    amendment = '0000123456-26-000002'
    routine = '0000123456-26-000003'
    future = '0000123456-26-000004'
    calls = []
    original = US_AT - timedelta(days=3)
    row = owned('ACME', provider='sec_edgar', at=original, previous=(older,), cik='123456')
    row['preopen']['event_watermarks']['google_news_rss'] = (
        row['preopen']['event_watermarks']['sec_edgar'].copy())
    row['preopen']['event_watermarks']['google_news_rss']['ids'] = []

    def send(request):
        calls.append(request)
        if request.url.host == 'news.google.com':
            return httpx.Response(200, text='<rss><channel></channel></rss>')
        assert request.url.path == '/submissions/CIK0000123456.json'
        assert request.headers['User-Agent'] == 'integration fixture'
        return httpx.Response(200, json=dict(cik='123456', filings=dict(files=[], recent=dict(
            form=['10-Q', '8-K/A', '8-K', '8-K'],
            accessionNumber=[older, amendment, routine, future],
            primaryDocument=['original.htm', 'amend.htm', 'routine.htm', 'future.htm'],
            filingDate=['2026-11-27', '2026-11-30', '2026-11-30', '2026-11-30'],
            acceptanceDateTime=['2026-11-27T14:30:03Z', '2026-11-30T12:00:00Z',
                                '2026-11-30T12:10:00Z', '2026-11-30T14:00:00Z'],
            items=['', '2.02, 9.01', '7.01', '4.02']))))

    result = execute('us', at=US_AT, rows=[row], handler=send, sec_user_agent='integration fixture')
    assert len(calls) == 2 and result['requests'] == {'google_news_rss': 1, 'sec_edgar': 1}
    corrected, ordinary = result['events']['ACME']
    assert corrected['id'] == amendment and corrected['material'] and corrected['revision']
    assert corrected['incremental'] == 'CONFIRMED'
    assert corrected['published_at'] == '2026-11-30T12:00:00+00:00'
    assert ordinary['id'] == routine and not ordinary['material']
    filing_scope = coverage(result, ticker='ACME', provider='sec_edgar')
    assert filing_scope['material_change'] and filing_scope['status'] == 'PARTIAL'
    assert coverage(result, ticker='ACME', provider='google_news_rss')['status'] == 'NO_SIGNIFICANT_CHANGE'


def test_dart_date_only_revisions_retain_uncertainty_and_429_stops_provider():
    seen = []
    rows = [owned(ticker, provider='opendart', at=KR_AT - timedelta(days=3), corp_code=corp)
            for ticker, corp in [('005001', '00005001'), ('005002', '00005002'), ('005003', '00005003')]]

    def send(request):
        seen.append(request.url.params['corp_code'])
        if request.url.params['corp_code'] == '00005002':
            return httpx.Response(429, text='private response body')
        return httpx.Response(200, json=dict(status='000', total_page=2, list=[
            dict(corp_code='00005001', rcept_dt='20261127', rcept_no='20261127000002',
                 report_nm='[기재정정] 단일판매 공급계약'),
            dict(corp_code='00005001', rcept_dt='20261128', rcept_no='20261128000003',
                 report_nm='[기재정정] 단일판매 공급계약'),
        ]))

    result = execute('kr', at=KR_AT, rows=rows, handler=send, opendart_api_key='test secret')
    assert seen == ['00005001', '00005002']
    same_day, later_day = result['events']['005001']
    assert same_day['incremental'] == 'UNCONFIRMED' and same_day['timestamp_uncertain']
    assert later_day['incremental'] == 'CONFIRMED' and later_day['published_at'] is None
    assert later_day['material'] and later_day['revision']
    assert coverage(result, ticker='005001', provider='opendart')['status'] == 'PARTIAL'
    assert coverage(result, ticker='005002', provider='opendart')['reason'] == 'HTTP_429'
    assert coverage(result, ticker='005003', provider='opendart')['reason'] == 'RATE_LIMITED'
    assert 'test secret' not in str(result) and 'private response body' not in str(result)


def test_dart_date_only_material_filing_is_reviewable_without_timed_confirmation():
    row = owned('005001', provider='opendart', at=KR_AT - timedelta(days=3), corp_code='00005001')

    def send(_request):
        return httpx.Response(200, json=dict(status='000', total_page=1, list=[
            dict(corp_code='00005001', rcept_dt='20261130', rcept_no='20261130000002',
                 report_nm='[기재정정] 단일판매 공급계약'),
        ]))

    result = execute('kr', at=KR_AT, rows=[row], handler=send, opendart_api_key='fixture')
    event, = result['events']['005001']
    assert event['official'] and event['revision'] and event['material']
    assert event['incremental'] == 'CONFIRMED' and event['timestamp_uncertain']
    filing_scope = coverage(result, ticker='005001', provider='opendart')
    assert filing_scope['status'] == 'HEADLINE_REVIEW'
    assert not filing_scope['material_change']


def test_naver_separates_relevant_headline_from_issuer_facts_and_ambiguous_timestamps():
    row = owned('005001', provider='naver_news', at=KR_AT - timedelta(days=3))
    row['preopen']['security']['company_name'] = 'Acme Industries'

    def send(request):
        assert request.url.params['sort'] == 'date' and request.headers['X-Naver-Client-Id'] == 'client'
        return httpx.Response(200, json=dict(total=3, items=[
            dict(title='Acme Industries awarded large order supply contract signed',
                 description='Acme Industries supply contract signed',
                 originallink='https://example.test/contract', pubDate=format_datetime(KR_AT - timedelta(hours=1))),
            dict(title='Acme Industries awarded major order', description='Acme Industries awarded a major order',
                 originallink='https://example.test/ambiguous', pubDate='unavailable'),
            dict(title='Other Industries announced equity offering', description='Acme Industries comparisons',
                 originallink='https://example.test/other', pubDate=format_datetime(KR_AT - timedelta(hours=2))),
        ]))

    result = execute('kr', at=KR_AT, rows=[row], handler=send,
                     naver_client_id='client', naver_client_secret='secret')
    headline, = result['events']['005001']
    assert headline['url'].endswith('/contract') and headline['incremental'] == 'CONFIRMED'
    assert not headline['official'] and not headline['material']
    assert coverage(result, ticker='005001', provider='naver_news')['status'] == 'PARTIAL'


def test_missing_provider_watermark_excludes_old_reports_and_leaves_newness_unconfirmed():
    row = owned('ACME', provider='sec_edgar', at=US_AT - timedelta(days=3), cik='123456')
    row['preopen']['event_watermarks'].clear()

    def send(request):
        if request.url.host == 'news.google.com':
            return httpx.Response(200, text='<rss><channel></channel></rss>')
        return httpx.Response(200, json=dict(cik='123456', filings=dict(files=[], recent=dict(
            form=['10-Q', '8-K'], accessionNumber=['0000123456-26-000001', '0000123456-26-000002'],
            primaryDocument=['old.htm', 'update.htm'], filingDate=['2026-11-27', '2026-11-30'],
            acceptanceDateTime=['2026-11-27T14:00:00Z', '2026-11-30T12:00:00Z'], items=['', '2.02']))))

    result = execute('us', at=US_AT, rows=[row], handler=send, sec_user_agent='fixture',
                     base_cutoff=datetime.fromisoformat('2026-11-27T15:00:00Z'))
    update, = result['events']['ACME']
    assert update['id'] == '0000123456-26-000002' and update['incremental'] == 'UNCONFIRMED'
    assert coverage(result, ticker='ACME', provider='sec_edgar')['status'] == 'PARTIAL'


def test_deadline_preserves_completed_sources_and_prevents_new_requests(monkeypatch):
    monkeypatch.setattr(sources, 'is_exchange_session_date', lambda *_: True)
    at = US_AT
    rows = [owned(ticker, provider='google_news_rss', at=at - timedelta(days=1), cik='123456')
            for ticker in ('ACME', 'BETA', 'ZETA')]
    seen = []

    async def send(request):
        seen.append(str(request.url))
        if 'BETA' in str(request.url):
            await asyncio.sleep(30)
        return httpx.Response(200, text='<rss><channel></channel></rss>')

    result = execute('us', at=at, rows=rows, handler=send, window=timedelta(seconds=0.08))
    assert len(seen) == 2
    assert coverage(result, ticker='ACME', provider='google_news_rss')['status'] == 'NO_SIGNIFICANT_CHANGE'
    assert coverage(result, ticker='BETA', provider='google_news_rss')['status'] == 'TIMEOUT'
    assert coverage(result, ticker='ZETA', provider='google_news_rss')['status'] == 'TIMEOUT'


def test_kr_uses_exact_saved_etf_and_only_eligible_completed_others(monkeypatch, tmp_path):
    us_path = tmp_path / 'us'
    kr_path = tmp_path / 'kr'
    captures = []
    reads = []

    def read_preopen_base(root, market, day, *, allow_reference):
        assert not allow_reference
        reads.append((root, market, day.isoformat()))
        return SimpleNamespace(is_current=market == 'us', cutoff=None, completed_at=None, messages=[dict(preopen_market=[
            dict(series='SPY', provider='kiwoom', observed_date='2026-11-27', value=100,
                 unit='USD', change_pct=1.0, source_ref='original')
        ])])

    def send(request):
        series = request.url.params['symbol']
        captures.append(series)
        latest = '2026-11-26' if series == 'IWM' else '2026-11-27'
        assert request.url.path == '/ohlcv' and request.url.params['count'] == '2'
        return httpx.Response(200, json=dict(
            resolved_symbol={'code': series}, meta={'provider': 'ohlcv_analyst', 'adjusted': True},
            periods={'daily': [dict(date='2026-11-25', close=100.0), dict(date=latest, close=101.0)]}))

    monkeypatch.setattr(preopen_base, 'read_preopen_base', read_preopen_base)
    run_roots = {'us': us_path, 'kr': kr_path}
    result = execute('kr', at=KR_AT, handler=send, run_roots=run_roots,
                     ohlcv_base_url='https://ohlcv.test')
    assert captures == ['QQQ', 'IWM', 'RSP', 'SOXX']
    assert reads == [(us_path, 'us', '2026-11-27'), (kr_path, 'kr', '2026-11-27')]
    observed = {row['series']: row for row in result['market']}
    assert set(observed) == {'SPY', 'QQQ', 'RSP', 'SOXX'}
    assert observed['SPY']['source_ref'] == 'original'
    assert observed['SOXX']['observed_date'] == '2026-11-27'
    offline = execute('kr', at=KR_AT, run_roots=run_roots)
    assert offline['market'] == [observed['SPY']] and offline['requests'] == {}


def test_kr_excludes_unfinished_etf_prices_and_disallowed_lineage():
    def send(request):
        series = request.url.params['symbol']
        prior = dict(date='2026-11-25', close=100.0)
        latest = dict(date='2026-11-27', close=101.0)
        meta = dict(provider='ohlcv_analyst', adjusted=True, upstream_provider='kiwoom')
        if series == 'QQQ':
            latest['bar_state'] = 'PARTIAL'
        elif series == 'IWM':
            prior['complete'] = False
        elif series == 'RSP':
            latest['completion_state'] = 'UNCONFIRMED'
        elif series == 'SOXX':
            meta['upstream_provider'] = 'alpha_vantage'
        return httpx.Response(200, json=dict(meta=meta, resolved_symbol={'code': series},
            periods={'daily': [prior, latest]}))

    result = execute('kr', at=KR_AT, handler=send, ohlcv_base_url='https://ohlcv.test')
    observation, = result['market']
    assert observation['series'] == 'SPY' and observation['value'] == 101.0
    assert result['requests'] == {'ohlcv_analyst': 5}
    states = {r['series']: r['status'] for r in result['coverage'] if r['provider'] == 'ohlcv_analyst'}
    assert states == {'SPY': 'OBSERVED', 'QQQ': 'UNAVAILABLE', 'IWM': 'UNAVAILABLE',
                      'RSP': 'UNAVAILABLE', 'SOXX': 'UNAVAILABLE'}


def test_market_producer_keeps_only_registry_bound_values():
    from app.services.market_display_plan import DisplayBinding, DisplayItem

    item = DisplayItem(block_id='style', display_order=0, label='동일가중', text='text ignored',
        status='AVAILABLE', format_id='display', bindings=(DisplayBinding(fact_id='fund',
        field_path='fields.return_pct', value=1.0, unit='pct', registry_row_sha256='registry',
        fact_sha256='fact'),))
    accepted = SimpleNamespace(market='us', items=[item])
    retained = sources.saved_market_rows(accepted, dict(fact_catalog=[dict(fact_id='fund',
        as_of_date='2026-11-27', fields=dict(series_code='RSP', value=993, provider='kiwoom'))]))
    assert retained[0]['value'] is None and retained[0]['change_pct'] == 1.0
