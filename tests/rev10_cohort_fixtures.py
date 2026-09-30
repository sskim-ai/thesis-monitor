"""One fictional generation, with every raw response built in its own clock."""
import asyncio
from datetime import date, datetime, timedelta, timezone
import json

import httpx
from pydantic import TypeAdapter

from app.models.security import SecurityMaster
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_stock_acquisition import StockPlan, make_reads, UNIVERSE, ROLES
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_source_composition import SourceRole, SourceInput, A
from tests.rev8_source_fixtures import fresh_inputs, POLICY
from tests.rev10_source_fixtures import wire_clock, event_inputs
from tests.test_unified_real_aggregate_owners import aggregate, binding

START = datetime(2026, 9, 23, 8, 10, tzinfo=timezone.utc)
RUN = 'rev10-common-synthetic'
CUTOFF = START + timedelta(minutes=1)
QUERY = START + timedelta(seconds=10)
POLICY_ALL = UnifiedSourcePolicy(POLICY.allowed_providers | {
    'google_news_rss', 'finnhub', 'ohlcv_analyst', 'kiwoom_rest', 'fred', 'eia', 'ecos', 'krx_night_futures'})


def plan_and_securities():
    identities, securities = {}, {m: [] for m in UNIVERSE}
    for market, tickers in UNIVERSE.items():
        for t in tickers:
            foreign = t in {'TSM', 'WRD', 'SKHY'}
            s = SecurityMaster(ticker=t, company_name='Synthetic ' + t,
                canonical_company_id='synthetic-issuer-' + t, canonical_security_id='security-' + t,
                exchange='NASDAQ' if market == 'us' else 'KRX', country='US' if market == 'us' else 'KR',
                cik='1234' if market == 'us' else None, corp_code='00123456' if market == 'kr' else None,
                issuer_type='foreign_private_issuer' if foreign else 'domestic_us' if market == 'us' else 'domestic_kr',
                security_type='common_stock', identity_provider='sec_edgar' if market == 'us' else 'opendart',
                identity_quality='verified', updated_at=START)
            if t == 'SKHY':
                s = s.model_copy(update={'issuer_type': 'adr', 'security_type': 'ads'})
            if t in {'IBM', 'MU'}:
                # Fictional SEC evidence below is consumed by the real identity owner.
                s = s.model_copy(update={'identity_provider': 'sec_official_identity'})
            securities[market].append(s.model_dump(mode='json'))
            identities[t] = s.model_dump(mode='json')
    universe = {m: {'eligible_subjects': list(ts)} for m, ts in UNIVERSE.items()}
    plan = StockPlan(run_id=RUN, acquisition_id='synthetic-stock', frozen_at=START,
        instruction_sha='1' * 40, implementation_sha='2' * 40, universe_sha256=digest(universe),
        owner_files={'app/providers/kiwoom.py': '3' * 64}, owner_head='4' * 40, settings_sha256='5' * 64,
        request_environment_sha256='6' * 64, reads=make_reads(universe, identities, at=START,
            counts={m: {r: 300 for r in ROLES} for m in UNIVERSE}))
    return plan, securities


def stocks(root):
    plan, securities = plan_and_securities()
    inputs = {}
    window = dict(run_id=RUN, collection_started_at=START.isoformat(),
                  source_query_cutoff=QUERY.isoformat(),
                  business_availability_cutoff=CUTOFF.isoformat())
    for market, tickers in UNIVERSE.items():
        for t in tickers:
            with wire_clock(START + timedelta(seconds=4)):
                inputs[t] = fresh_inputs(root / t, t, plan=plan, cohort_securities=securities[market],
                    policy=POLICY_ALL, current_only=t in {'RXRX', 'WULF'}, conflict=t == 'CPNG',
                    denied_quality=t == '047810', insurance=t == '003690', empty_financial=t == 'SKHY')
            inputs[t]['source_window'] = window
    for t, persisted in [('CORZ', False), ('WULF', True)]:
        event_inputs(root / (t + '-event'), inputs=inputs[t], persisted=persisted)
    from app.services.fresh_financial_stock_owner import fresh_stock_baseline
    from app.services.bounded_financial_stock_owner import assemble
    from app.services.official_security_identity_service import OfficialSecurityIdentityEvidence
    source = inputs['000660']
    source_owner = dict(baseline=fresh_stock_baseline(source['technical_inputs']),
        local_seed=source['technical_inputs']['local_seed'], **source['financial_inputs'])
    official = OfficialSecurityIdentityEvidence(ticker='SKHY', issuer_name='Synthetic issuer',
        security_title='American Depositary Shares', security_type='ads', issuer_type='adr', exchange='NASDAQ',
        source_url='https://www.sec.gov/Archives/edgar/data/1234/000000123426000001/prospectus.htm',
        source_form='424(b)(4)', filing_accession='0000001234-26-000001', as_of_date='2026-06-01',
        source_reference='SYNTHETIC fixture, NOT LIVE', cik='1234', ordinary_share_identifier='000660').to_payload()
    inputs['SKHY']['financial_inputs']['issuer_business'] = dict(source_inputs=source_owner,
        official_identity=official, official_identity_sha256=digest(official), source_result_sha256=digest(assemble(**source_owner)))
    for t, negative in [('IBM', False), ('MU', True)]:
        from tests.rev28_native_fixtures import native_input
        i = inputs[t]
        i['valuation_inputs'] = native_input(i['financial_inputs']['plan']['security'], start=START,
            run=RUN, policy=POLICY_ALL, negative=negative)
    return inputs


def markets(root):
    from app.macro.providers.base import MacroProviderResult
    from app.macro.providers.market import MARKET_SYMBOLS, OhlcvMarketProvider
    from app.services.unified_source_observer import OhlcvRead, OhlcvReceiptObserver
    from app.services.unified_aggregate_owners import us_market_aggregate_owner, kiwoom_aggregate_owner
    from app.services.unified_kiwoom_observer import KiwoomReceiptObserver
    from app.services.kiwoom_kr_market_context_service import KiwoomKrMarketContextService, kiwoom_market_reads
    from app.providers.kiwoom_rest_client import KiwoomRestClient
    from tests.test_kiwoom_rest_market_context import _handler
    output = {}
    at = QUERY
    for market in ('us', 'kr'):
        path, attempt = root / market, RUN + ':' + market
        session = date(2026, 9, 22 if market == 'us' else 23)
        if market == 'us':
            reads = tuple(OhlcvRead(role='us_market_prices:' + symbol, symbol=symbol, market='us',
                provider='ohlcv_analyst', period='daily', adjusted=True, session_date=session, max_requests=1,
                params=dict(symbol=symbol, market='US', periods='daily', count=2,
                            include_indicators='false', indicator_limit=0, adjusted='true')) for symbol in MARKET_SYMBOLS)
            observer = OhlcvReceiptObserver(root=path, run_id=RUN, attempt_id=attempt, reads=reads, policy=POLICY_ALL)
            def reply(request):
                return httpx.Response(200, json=dict(resolved_symbol={'code': request.url.params['symbol']},
                    meta=dict(provider='ohlcv_analyst', adjusted=True), periods={'daily': [
                        dict(date=session.isoformat(), close=100), dict(date='2026-09-21', close=99)]}))
            provider = OhlcvMarketProvider(httpx.MockTransport(reply), source_observer=observer)
            with wire_clock(at):
                value = TypeAdapter(MacroProviderResult).dump_python(asyncio.run(provider.collect(at)), mode='json')
            role = SourceRole(key='us_market_prices', owner='us_market', market=market, symbol='*',
                provider='ohlcv_analyst', basis='adjusted_close', session=session.isoformat(), acquisition_class=A, mandatory=True)
            owner = us_market_aggregate_owner(role=role, source_url=provider.settings.ohlcv_base_url.rstrip('/') + '/ohlcv', policy=POLICY_ALL)
        else:
            observer = KiwoomReceiptObserver(root=path, run_id=RUN, attempt_id=attempt, session_date=session,
                reads=kiwoom_market_reads(session_date=session, max_pages=5, max_requests_per_page=1), policy=POLICY_ALL)
            base = _handler([])
            def reply(request):
                if request.headers.get('api-id') == 'ka20009':
                    code = json.loads(request.content)['inds_cd']
                    from tests.test_kiwoom_rest_market_context import _current
                    row = _current(code)
                    return httpx.Response(200, json=dict(return_code=0, inds_cur_prc_daly_rept=[dict(
                        dt_n=session.strftime('%Y%m%d'), cur_prc_n=row['cur_prc'], flu_rt_n=row['flu_rt'])]))
                return base.handle_request(request)
            client = KiwoomRestClient(app_key='fixture', secret_key='fixture', source_observer=observer,
                transport=httpx.MockTransport(reply), max_retries=0, request_interval_seconds=0)
            service = KiwoomKrMarketContextService(client, max_pages=5)
            with wire_clock(at):
                asyncio.run(service.collect(session_date=session, observed_at=at))
            value = json.loads((path / 'normalization.json').read_bytes())['roles']['kr_local_indices_sectors_breadth']['value']
            role = SourceRole(key='kr_local_indices_sectors_breadth', owner='kiwoom_pages', market=market,
                symbol='*', provider='kiwoom_rest', basis='query_time', session=session.isoformat(), acquisition_class=A, mandatory=True)
            owner = kiwoom_aggregate_owner(role=role, observed_at=at, max_pages=5, max_requests_per_page=1, policy=POLICY_ALL)
        receipt = aggregate(path, role, value, at)
        durable_json(path / 'aggregate.json', receipt.model_dump(mode='json'))
        item = SourceInput(role=role.key, run_id=RUN, attempt_id=attempt, acquisition_class=A,
            requested_at=at, received_at=at, artifact=receipt.artifact, artifact_sha256=receipt.artifact_sha256,
            receipt_artifact='aggregate.json', receipt_sha256=binding(path, 'aggregate.json')['sha256'])
        output[market] = dict(native_aggregate=dict(item=item, role=role, root=path, run_id=RUN,
            start=START, cutoff=CUTOFF, attempt_id=attempt, policy=POLICY_ALL, owners={role.owner: owner}))
    return output


def night(root):
    from app.jobs.probe_krx_night_futures import fetch_live_probe, KRX_FUTURES_DAILY_URL
    from app.macro.providers.krx import materialize_night_probe
    from app.macro.providers.base import MacroProviderResult
    from tests.test_krx_night_futures_probe import _row
    bodies, hashes, receipts = {}, {}, []
    at = QUERY
    def reply(request):
        day = datetime.strptime(request.url.params['basDd'], '%Y%m%d').date()
        rows = []
        if day < at.date():
            for session, close in [('정규', '100'), ('야간', '101')]:
                row = _row('KOSPI 200 선물', session, 'A016C000', '코스피200 F 202612' + (' 야간' if session == '야간' else ''),
                           close, day.strftime('%Y%m%d'), '1' if session == '야간' else None)
                row.update(TDD_OPNPRC='100', TDD_HGPRC='102', TDD_LWPRC='99')
                rows.append(row)
        name = day.isoformat() + '.json'
        body = encoded({'OutBlock_1': rows})
        bodies[name], hashes[name] = body, sha256_bytes(body)
        receipts.append(dict(run_id=RUN, acquisition_id='night-once', provider='krx_night_futures',
            outcome='HTTP_RESPONSE', http_status=200, artifact=name, artifact_sha256=hashes[name],
            requested_at=START.isoformat(), received_at=at.isoformat(),
            request=dict(method='GET', route=KRX_FUTURES_DAILY_URL, params=dict(request.url.params))))
        return httpx.Response(200, content=body)
    probe = asyncio.run(fetch_live_probe(run_date=at.date(), observation_time=at, api_key='fixture',
                                       transport=httpx.MockTransport(reply), max_lookback_days=7))
    probe.live_source = True
    value = TypeAdapter(MacroProviderResult).dump_python(materialize_night_probe(probe, history_directory=root), mode='json')
    return dict(receipts=receipts, bodies=bodies, body_hashes=hashes, observed_at=at, run_id=RUN,
        acquisition_id='night-once', expected_value_sha256=digest(value), policy=POLICY_ALL,
        run_started_at=START, acquisition_cutoff=CUTOFF)
