"""Current configured finite provider slots, frozen before acquisition."""
from pathlib import Path

import httpx

from app.macro.providers.market import MARKET_SYMBOLS
from app.jobs.probe_krx_night_futures import USER_AGENT as NIGHT_USER_AGENT
from app.services.fresh_source_run_contract import acquisition_plan, MAX_KR_REQUEST_PAGES
from app.services.sealed_chart_slots import chart_slots
from app.services.sealed_financial_slots import financial_slots
from app.services.sealed_fresh_dispatch import FreshRequestDescriptor, ProviderPlan, wire_identity
from app.services.sealed_response_binding import ResponseBinding, binding_owner_hash
from app.services.unified_kiwoom_observer import KiwoomRead
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest, encoded

ROOT = Path(__file__).resolve().parents[1]


def compile_plan(*, stock, identities, news_reads, config_identities, rev10_receipt,
                 configured_kr_pages, kr_post_acquisition_completeness_approved, exact_financial_owner=False,
                 valuation_market_types=None):
    if kr_post_acquisition_completeness_approved is not True:
        raise ValueError('explicit_kr_post_acquisition_completeness_approval_required')
    if configured_kr_pages < 1:
        raise ValueError('kr_configured_page_cap_invalid')
    local_kr_cap = min(configured_kr_pages, MAX_KR_REQUEST_PAGES)
    candidate = acquisition_plan(stock, identities, kr_max_pages=local_kr_cap, exact_financial_owner=exact_financial_owner)
    descriptors, owners, roles, page_proof = [], {}, {}, []
    def add(key, provider, role, market, subject, operation, request, *, mandatory=True,
            binding=None, pages=1, retries=2):
        owner = 'app/services/sealed_source_transport.py'
        owner_hash = sha256_bytes((ROOT / owner).read_bytes())
        d = FreshRequestDescriptor(generation_id=stock.run_id, logical_request_id=key,
            provider=provider, source_family=role.split(':')[0], role_id=role, market=market, subject=subject,
            endpoint_operation=operation, request_json=wire_identity(request, ('PLAN_CREDENTIAL',)),
            target_period=next((r.latest_completed_session for r in stock.reads if r.market == market), stock.frozen_at.date().isoformat()),
            mandatory=mandatory, group_id=key, page_ordinal=1, max_pages=pages, document_ordinal=1, max_documents=1,
            timeout_seconds=600, transient_retry_max=retries, raw_path=f'raw/{key}/source.body', normalizer=owner,
            consumer_role=role, owner_sha256=owner_hash, config_identity_sha256=config_identities[provider], response_binding=binding)
        slots = chart_slots(d, maximum_pages=pages) if pages > 1 else (d,)
        descriptors.extend(slots)
        owners[owner] = owner_hash
        roles[role] = dict(mandatory=mandatory, descriptor_ids=[s.logical_request_id for s in slots])
        return d.logical_request_id
    def kiwoom(key, role, market, subject, api, route, body, *, pages=1, mandatory=True, binding=None, retries=2):
        return add(key, 'kiwoom', role, market, subject, api, httpx.Request('POST', 'https://api.kiwoom.com' + route,
            json=body, headers={'Content-Type': 'application/json;charset=UTF-8', 'api-id': api,
                'authorization': 'Bearer PLAN_CREDENTIAL', 'cont-yn': 'N', 'next-key': ''}),
            mandatory=mandatory, pages=pages, binding=binding, retries=retries)
    add('kiwoom:auth', 'kiwoom', 'kiwoom:credential_exchange', 'global', 'run', 'credential_exchange',
        httpx.Request('POST', 'https://api.kiwoom.com/oauth2/token',
            headers={'Content-Type': 'application/json;charset=UTF-8'},
            json={'grant_type': 'client_credentials', 'appkey': 'PLAN_CREDENTIAL', 'secretkey': 'PLAN_CREDENTIAL'}))
    for r in stock.reads:
        body = dict(stk_cd=r.subject, upd_stkpc_tp=str(int(r.adjusted)))
        body.update(dict(stex_tp=r.exchange, strt_dt='', exrt_appl_tp='0') if r.market == 'us' else dict(base_dt=r.query_date))
        if r.market == 'kr' and r.max_pages > local_kr_cap:
            raise ValueError('R2B_R9_REV11_KR_PAGE_BUDGET_INSUFFICIENT:' + r.entry_id)
        role = 'stock:' + r.entry_id
        kiwoom(r.entry_id + ':page1', role, r.market, r.subject, r.api_id, r.route, body, pages=r.max_pages)
        if r.market == 'kr':
            page_proof.append(dict(role=role, configured_cap=configured_kr_pages, accepted_bound=MAX_KR_REQUEST_PAGES,
                request_local_cap=r.max_pages, consumer_rows=r.count, policy='EXISTING_OWNER_CAP_POST_ACQUISITION_COMPLETENESS',
                cap_exhaustion='SOURCE_PARTIAL', global_setting_changed=False))
    discovery = []
    for exchange in ('ND', 'NY', 'NA'):
        discovery.append(kiwoom('us_market:discovery:' + exchange, 'us_market:exchange_discovery', 'us', '*',
            'usa10099', '/api/us/stkinfo', {'stex_tp': exchange}))
    for symbol in MARKET_SYMBOLS:
        policy = dict(rule='native_exact_symbol_in_exchange_list', symbol=symbol,
                      exchange_order=['ND', 'NY', 'NA'], row_keys=['list', 'result_list', 'output', 'data'])
        binding = ResponseBinding(kind='KIWOOM_US_EXCHANGE', parents=tuple(discovery),
            policy_json=encoded(policy).decode(), policy_sha256=digest(policy))
        kiwoom('us_market:' + symbol, 'us_market:' + symbol, 'us', symbol, 'usa06012', '/api/us/chart',
            dict(stex_tp='ND', stk_cd=symbol, strt_dt='', upd_stkpc_tp='1', exrt_appl_tp='0'), pages=2, binding=binding)
    for r in candidate['kr_market_reads']:
        kiwoom('kr_market:' + r['key'], 'kr_market:' + r['key'], 'kr', r['key'].split(':')[0], r['api_id'], KiwoomRead.model_validate(r).endpoint,
                r['body'], pages=r['max_pages'], mandatory=r['mandatory'])
        page_proof.append(dict(role='kr_market:' + r['key'], configured_cap=configured_kr_pages,
            accepted_bound=MAX_KR_REQUEST_PAGES, request_local_cap=r['max_pages'],
            policy='EXISTING_OWNER_CAP_POST_ACQUISITION_COMPLETENESS', cap_exhaustion='SOURCE_PARTIAL', global_setting_changed=False))
    for t, p in candidate['financial_plans'].items():
        owner = 'app/services/sealed_financial_reader.py'
        owners[owner] = sha256_bytes((ROOT / owner).read_bytes())
        rows = financial_slots(p, owner=owner, owner_sha256=owners[owner], config_sha256=config_identities[p['provider']])
        descriptors.extend(rows)
        roles['financial:' + t] = dict(mandatory=True, descriptor_ids=[d.logical_request_id for d in rows])
    for series in candidate['macro_queries']['fred']['series']:
        add('fred:' + series, 'fred', 'fred:' + series, 'global', series, 'observations',
            httpx.Request('GET', 'https://api.stlouisfed.org/fred/series/observations', params=dict(series_id=series,
                api_key='PLAN_CREDENTIAL', file_type='json', sort_order='desc', limit=5,
                observation_end=candidate['macro_queries']['fred']['observation_end'])))
    for series in candidate['macro_queries']['eia']['series']:
        add('eia:' + series, 'eia', 'eia:' + series, 'global', series, 'seriesid',
            httpx.Request('GET', 'https://api.eia.gov/v2/seriesid/' + series, params={'api_key': 'PLAN_CREDENTIAL', 'length': 1}))
    add('ecos:USDKRW', 'ecos', 'ecos:USDKRW', 'kr', 'USDKRW', 'KeyStatisticList',
        httpx.Request('GET', 'https://ecos.bok.or.kr/api/KeyStatisticList/PLAN_CREDENTIAL/json/kr/1/100'))
    for day in candidate['night_query_dates']:
        key = 'night:KOSPI200:' + day
        add(key, 'krx_night_futures', key, 'kr', 'KOSPI200', 'fut_bydd_trd',
            httpx.Request('GET', 'https://data-dbg.krx.co.kr/svc/apis/drv/fut_bydd_trd',
                params={'basDd': day.replace('-', '')}, headers={'AUTH_KEY': 'PLAN_CREDENTIAL', 'User-Agent': NIGHT_USER_AGENT}))
    if {r.subject for r in news_reads} != set(identities):
        raise ValueError('event_classification_exact_all22_required')
    for r in news_reads:
        req = r.request
        headers = ({'X-Naver-Client-Id': 'PLAN_CREDENTIAL', 'X-Naver-Client-Secret': 'PLAN_CREDENTIAL'}
                   if r.market == 'kr' else {})
        from app.providers.news import serialize_news_request
        add('events:' + r.subject, r.provider, 'events:' + r.subject, r.market, r.subject, 'news',
            serialize_news_request(req['method'], req['route'], req['params'], headers=headers), mandatory=False, retries=0)
        roles['events:' + r.subject]['classification'] = 'EVENT_OPTIONAL_PLANNED'
    valuation_slots = {}
    if valuation_market_types is not None:
        from app.services.provider_native_valuation_acquisition import add_slots
        valuation_slots = add_slots(identities=identities, market_types=valuation_market_types, add=add, kiwoom=kiwoom)
    plan = ProviderPlan(generation_id=stock.run_id, code_sha=stock.implementation_sha,
        policy_schema_sha256=digest({'descriptor': FreshRequestDescriptor.model_json_schema(),
            'acquisition': candidate['plan_sha256'], 'kr_completeness_approval': True}),
        rev10_receipt_sha256=sha256_bytes(encoded(rev10_receipt) + b'\n'), frozen_at=stock.frozen_at,
        descriptors=tuple(descriptors), mandatory_roles=tuple(k for k, v in roles.items() if v['mandatory']),
        binding_owner_sha256=binding_owner_hash())
    for role, row in roles.items():
        row['descriptor_ids'] = [d.logical_request_id for d in descriptors if d.consumer_role == role]
    return dict(plan=plan, candidate=candidate, owners=owners, role_coverage=roles, kr_page_proof=page_proof,
        optional_valuation={t: {'native_metric': ('PLANNED_NATIVE_SNAPSHOT_OPTIONAL_VALUE' if valuation_slots else 'OPTIONAL_UNAVAILABLE_NO_PLANNED_NATIVE_READ'),
            'financial_price_inputs': 'CURRENT_GENERATION_ONLY', 'no_new_provider': True} for t in identities},
        valuation_slots=valuation_slots, news_reads=[r.model_dump(mode='json') for r in news_reads],
        acquisition_fragment_not_source_qualification=True)
