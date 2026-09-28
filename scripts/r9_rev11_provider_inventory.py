"""Offline exact-descriptor inventory. Never dispatch a partially sealed plan."""
from datetime import datetime
from pathlib import Path

import httpx

from app.macro.providers.market import MARKET_SYMBOLS
from app.services.bounded_financial_acquisition import make_plan
from app.services.fresh_source_run_contract import acquisition_plan, MAX_KR_REQUEST_PAGES
from app.services.sealed_fresh_dispatch import FreshRequestDescriptor, ProviderPlan, wire_identity, kr_request_budget
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest, encoded


def inventory(*, stock, identities, config_identities, credential_presence, configured_kr_pages, rev10_receipt, code_sha):
    """Current static identities only; no prior filing list or cursor carry-in."""
    root = Path(__file__).resolve().parents[1]
    candidate = acquisition_plan(stock, identities, kr_max_pages=MAX_KR_REQUEST_PAGES)
    descriptors, coverage, page_proof = [], [], []
    owners = {}
    def add(key, provider, role, market, subject, operation, req, owner, target, mandatory=True,
            group=None, page=1, max_pages=1, retries=2):
        owner_sha = sha256_bytes((root / owner).read_bytes())
        owners[owner] = owner_sha
        desc = FreshRequestDescriptor(generation_id=stock.run_id, logical_request_id=key,
            provider=provider, source_family=role.split(':')[0], role_id=role, market=market,
            subject=subject, endpoint_operation=operation, request_json=wire_identity(req, ('PLAN_CREDENTIAL',)),
            target_period=target, mandatory=mandatory, group_id=group or key, page_ordinal=page,
            max_pages=max_pages, document_ordinal=1, max_documents=1, timeout_seconds=600,
            transient_retry_max=retries, raw_path=f'raw/{key}/source.body', normalizer=owner,
            consumer_role=role, owner_sha256=owner_sha, config_identity_sha256=config_identities[provider])
        descriptors.append(desc)
        return desc.logical_request_id
    def row(role, status, ids, reason, mandatory=True):
        coverage.append(dict(role=role, status=status, descriptor_ids=ids, reason=reason, mandatory=mandatory))
    for r in stock.reads:
        role = 'stock:' + r.entry_id
        body = dict(stk_cd=r.subject, upd_stkpc_tp=str(int(r.adjusted)))
        body.update(dict(stex_tp=r.exchange, strt_dt='', exrt_appl_tp='0') if r.market == 'us' else dict(base_dt=r.query_date))
        key = add(r.entry_id + ':page1', 'kiwoom', role, r.market, r.subject, r.api_id,
            httpx.Request('POST', 'https://api.kiwoom.com' + r.route, json=body,
                headers={'api-id': r.api_id, 'cont-yn': 'N', 'next-key': '', 'authorization': 'Bearer PLAN_CREDENTIAL'}),
            'app/services/unified_stock_owner.py', r.latest_completed_session)
        row(role, 'RESPONSE_DEPENDENT_REQUESTS_UNSEALED', [key],
            'Pages 2..max_pages require response next-key; freezing page1 does not qualify the whole consumer.')
        if r.market == 'kr':
            page_proof.append(dict(role=role, owner_finite_envelope=r.max_pages,
                consumer_rows=r.count, **kr_request_budget(global_cap=configured_kr_pages,
                    row_count=r.count, verified_minimum_rows_per_page=None, consumer_complete=True)))
    # Recent filings and companyfacts are addressable before collection; selected
    # filing URLs and linked exhibit names are not functions of the static CIK.
    for ticker, p in candidate['financial_plans'].items():
        role = 'financial:' + ticker
        ids = []
        if p['market'] == 'us':
            for stage, url in (
                ('discovery', f'https://data.sec.gov/submissions/CIK{p["issuer"]}.json'),
                ('companyfacts', f'https://data.sec.gov/api/xbrl/companyfacts/CIK{p["issuer"]}.json')):
                ids.append(add(ticker + ':' + stage, 'sec_edgar', role, 'us', ticker, stage,
                    httpx.Request('GET', url, headers={'User-Agent': 'PLAN_CREDENTIAL'}),
                    'app/services/bounded_financial_projection.py', p['cutoff'][:10]))
            reason = 'Selected accession/primaryDocument and optional exhibits come from fresh submission/index/document responses.'
        else:
            for page in range(1, p['limits']['discovery'] + 1):
                params = dict(crtfc_key='PLAN_CREDENTIAL', corp_code=p['issuer'], bgn_de=p['begin'].replace('-', ''),
                    end_de=p['cutoff'][:10].replace('-', ''), pblntf_ty='A', last_reprt_at='N', page_count=100, page_no=page)
                ids.append(add(ticker + ':discovery:' + str(page), 'opendart', role, 'kr', ticker, 'list',
                    httpx.Request('GET', 'https://opendart.fss.or.kr/api/list.json', params=params),
                    'app/services/bounded_financial_projection.py', p['cutoff'][:10],
                    group=ticker + ':discovery', page=page, max_pages=p['limits']['discovery']))
            reason = 'Current/prior business year and report code are selected from fresh list; enumerating all possibilities exceeds existing selected-filing caps.'
        row(role, 'RESPONSE_DEPENDENT_REQUESTS_UNSEALED', ids, reason)
    for r in candidate['kr_market_reads']:
        role = 'kr_market:' + r['key']
        key = add(r['key'], 'kiwoom', role, 'kr', r['key'].split(':')[0], r['api_id'],
            httpx.Request('POST', 'https://api.kiwoom.com' +
                ('/api/dostk/mrkcond' if r['api_id'] == 'ka10066' else '/api/dostk/sect'), json=r['body'],
                headers={'api-id': r['api_id'], 'cont-yn': 'N', 'next-key': '', 'authorization': 'Bearer PLAN_CREDENTIAL'}),
            'app/services/kiwoom_kr_market_context_service.py',
            next(x.latest_completed_session for x in stock.reads if x.market == 'kr'), mandatory=r['mandatory'])
        paginated = r['api_id'] == 'ka10066'
        row(role, 'RESPONSE_DEPENDENT_REQUESTS_UNSEALED' if paginated else 'EXACT_DESCRIPTOR', [key],
            'Complete-market row count/page size and next-key unknown.' if paginated else 'Existing single-response owner.', r['mandatory'])
        page_proof.append(dict(role=role, **kr_request_budget(global_cap=configured_kr_pages, row_count=None,
            verified_minimum_rows_per_page=None, consumer_complete=True, single_response=not paginated)))
    for symbol in MARKET_SYMBOLS:
        row('us_market:' + symbol, 'RESPONSE_DEPENDENT_REQUESTS_UNSEALED', [],
            'Native market owner resolves exchange from usa10099 responses; exact chart stex_tp is not in the market registry.')
    macro = candidate['macro_queries']
    for series in macro['fred']['series']:
        role = 'fred:' + series
        req = httpx.Request('GET', 'https://api.stlouisfed.org/fred/series/observations', params=dict(
            series_id=series, api_key='PLAN_CREDENTIAL', file_type='json', sort_order='desc', limit=5,
            observation_end=macro['fred']['observation_end']))
        key = add(role, 'fred', role, 'global', series, 'observations', req,
            'app/macro/providers/fred.py', macro['fred']['observation_end'])
        row(role, 'EXACT_DESCRIPTOR', [key], 'Current configured FRED registry, no series expansion.')
    for series in macro['eia']['series']:
        role = 'eia:' + series
        key = add(role, 'eia', role, 'global', series, 'seriesid',
            httpx.Request('GET', 'https://api.eia.gov/v2/seriesid/' + series,
                         params={'api_key': 'PLAN_CREDENTIAL', 'length': 1}),
            'app/macro/providers/eia.py', stock.frozen_at.date().isoformat())
        row(role, 'EXACT_DESCRIPTOR', [key], 'Current configured EIA registry.')
    key = add('ecos:KeyStatisticList', 'ecos', 'ecos:USDKRW', 'kr', 'USDKRW', 'KeyStatisticList',
        httpx.Request('GET', 'https://ecos.bok.or.kr/api/KeyStatisticList/PLAN_CREDENTIAL/json/kr/1/100'),
        'app/macro/providers/ecos.py', stock.frozen_at.date().isoformat())
    row('ecos:USDKRW', 'EXACT_DESCRIPTOR', [key], 'Source-owned TIME/currentness still must pass after actual collection.')
    for day in candidate['night_query_dates']:
        role = 'night:KOSPI200:' + day
        key = add(role, 'krx_night_futures', role, 'kr', 'KOSPI200', 'fut_bydd_trd',
            httpx.Request('GET', 'https://data-dbg.krx.co.kr/svc/apis/drv/fut_bydd_trd',
                params={'basDd': day.replace('-', '')}, headers={'AUTH_KEY': 'PLAN_CREDENTIAL'}),
            'app/macro/providers/krx.py', day)
        row(role, 'EXACT_DESCRIPTOR', [key], 'Existing finite current-month plus prior-boundary window; KOSPI200 only.')
    for ticker in identities:
        row('events:' + ticker, 'NOT_COMPILED', [],
            'Event role classification and query/eligibility binding must be frozen; not silently EVENT_NOT_REQUIRED.', False)
        row('valuation:' + ticker, 'NOT_COMPILED', [],
            'Existing optional native owner/current-security qualification has not been connected to this plan.', False)
    row('kiwoom:credential_exchange', 'NOT_COMPILED', [],
        'An explicit secret-free auth receipt owner is required; source-body dispatcher must not serialize token responses.')
    row('whole_graph:fresh_receipt_collector', 'NOT_COMPILED', [],
        'SealedDispatcher receipt chain exists; no all-role receipt-to-current-whole-graph adapter registered.')
    unresolved = [r['role'] for r in coverage if r['status'] != 'EXACT_DESCRIPTOR']
    plan = ProviderPlan(generation_id=stock.run_id, code_sha=code_sha,
        policy_schema_sha256=digest({'candidate': candidate['plan_sha256'], 'descriptor': FreshRequestDescriptor.model_json_schema()}),
        rev10_receipt_sha256=sha256_bytes(encoded(rev10_receipt) + b'\n'), frozen_at=stock.frozen_at,
        descriptors=tuple(descriptors), mandatory_roles=tuple(r['role'] for r in coverage if r['mandatory']),
        unresolved_roles=tuple(unresolved))
    admission = plan.admission(rev10_receipt=rev10_receipt, owners=owners, config_identities=config_identities,
                              credential_presence=credential_presence)
    return dict(diagnostic_plan=plan.model_dump(mode='json'), admission=admission,
        descriptor_inventory=[dict(d.model_dump(mode='json'), descriptor_sha256=d.descriptor_sha256,
            request_semantic_sha256=d.request_semantic_sha256, max_transport_attempts=d.max_transport_attempts) for d in descriptors],
        role_coverage=coverage, kr_page_proof=page_proof,
        legacy_candidate_envelope=candidate['budgets'], final_provider_plan_issued=False)


def sec_response_dependency_probe():
    """Same static issuer/plan admits two source responses with different URLs."""
    from app.services.bounded_financial_acquisition import sec_selection, sec_base
    security = dict(ticker='FIXTURE', canonical_company_id='issuer', canonical_security_id='security',
        identity_provider='local', cik='123', issuer_type='domestic_us')
    p = make_plan(security, market='us', cutoff=datetime.fromisoformat('2026-09-28T00:00:00+00:00'), run_id='probe')
    urls = []
    for ordinal in (1, 2):
        row = dict(form=['10-Q'], accessionNumber=[f'0000000123-26-{ordinal:06d}'],
            primaryDocument=[f'quarter-{ordinal}.htm'], filingDate=['2026-08-01'], reportDate=['2026-06-30'])
        selected = sec_selection({'cik': '123', 'filings': {'recent': row, 'files': []}}, p)
        urls.append(sec_base(p, selected[0]) + selected[0]['primaryDocument'])
    return dict(same_static_plan_sha256=digest(p), possible_document_urls=urls,
        different_exact_request=urls[0] != urls[1], fixture_only=True, network_calls=0,
        conclusion='Exact child requests require fresh discovery or an explicitly authorized response-bound descriptor contract.')
