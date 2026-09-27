import asyncio
from copy import deepcopy
from datetime import datetime, timezone

import httpx
import pytest

from app.services.bounded_financial_acquisition import (
    AcquisitionDenied, BoundedReader, DOMESTIC, FOREIGN, DART, SystemicStop,
    collect, exhibit_selection, make_plan, retryable, sec_selection,
)
from app.services.bounded_financial_projection import field_record, paired
from app.services.bounded_financial_projection import project


def plan(market='us', foreign=False):
    return make_plan({'ticker': 'FIXTURE', 'canonical_company_id': 'issuer', 'canonical_security_id': 'security',
        'identity_provider': 'local', 'cik': '123', 'corp_code': '00123456',
        'issuer_type': 'foreign_private_issuer' if foreign else 'domestic_us'},
        market=market, cutoff=datetime(2026, 9, 27, tzinfo=timezone.utc), run_id='fixture')


def filing(form='20-F', ordinal=1, year=2026):
    return {'form': form, 'accessionNumber': f'0000000123-26-{ordinal:06d}',
        'primaryDocument': 'primary.htm', 'filingDate': f'{year}-08-01',
        'reportDate': f'{year}-06-30', 'role': 'current'}


def submission(filings):
    keys = ['form', 'accessionNumber', 'primaryDocument', 'filingDate', 'reportDate']
    return {'cik': '123', 'filings': {'recent': {k: [r[k] for r in filings] for k in keys}, 'files': []}}


@pytest.mark.parametrize('count', [0, 3, 9, 99])
def test_exhibit_budget_is_not_selection_truncation(count):
    p, f = plan(foreign=True), filing()
    index = {'directory': {'item': [{'name': f'ex99-{i}.htm'} for i in range(count)]}}
    if count > 2:
        with pytest.raises(AcquisitionDenied, match='SEC_DOCUMENT_BOUND_EXHAUSTED'):
            exhibit_selection(index, '', p, f)
    else:
        assert exhibit_selection(index, '', p, f) == []


@pytest.mark.parametrize('count', [1, 3, 9, 99, 129])
@pytest.mark.parametrize('foreign', [True, False])
def test_discovery_caps_deterministic(count, foreign):
    p = plan(foreign=foreign)
    forms = ['6-K', '20-F'] if foreign else ['10-Q', '10-K']
    payload = submission([filing(forms[i % 2], i+1) for i in range(count)])
    if count > p['limits']['candidates']:
        with pytest.raises(AcquisitionDenied, match='SEC_DISCOVERY_BOUND_EXHAUSTED'):
            sec_selection(payload, p)
    else:
        first = sec_selection(payload, p)
        reverse = deepcopy(payload)
        for values in reverse['filings']['recent'].values():
            values.reverse()
        assert first == sec_selection(reverse, p)
        assert len(first) <= p['limits']['current'] + p['limits']['prior']


@pytest.mark.parametrize('total', [1, 3, 9, 99])
def test_dart_page_count_enforced_before_next_request(tmp_path, total):
    calls = []
    def respond(request):
        calls.append(request)
        return httpx.Response(200, json={'status':'000','total_page':total,'list':[]})
    reader = BoundedReader(plan('kr'), tmp_path, api_key='test', transport=httpx.MockTransport(respond))
    if total > 2:
        with pytest.raises(AcquisitionDenied, match='OPENDART_DISCOVERY_BOUND_EXHAUSTED'):
            asyncio.run(collect(reader))
    else:
        assert not asyncio.run(collect(reader))['selected_filings']
    assert len(calls) == 1


def test_two_page_dart_plan_and_no_hidden_requests(tmp_path):
    calls = []
    def respond(request):
        calls.append(request)
        return httpx.Response(200, json={'status':'000','total_page':2,'list':[]})
    reader = BoundedReader(plan('kr'), tmp_path, api_key='test', transport=httpx.MockTransport(respond))
    asyncio.run(collect(reader))
    assert len(calls) == reader.logical == reader.attempts == 2


@pytest.mark.parametrize('kind', ['identity', 'filing', 'period', 'basis', 'unit', 'lineage', 'schema', 'quality'])
def test_semantic_errors_never_retried(kind):
    assert not retryable(exc=ValueError(kind))


def test_retry_byte_identity_and_receipts(tmp_path, monkeypatch):
    calls = []
    async def no_sleep(_):
        pass
    monkeypatch.setattr('app.services.bounded_financial_acquisition.asyncio.sleep', no_sleep)
    def respond(request):
        calls.append(str(request.url))
        return httpx.Response(503 if len(calls) < 3 else 200, json={'cik':123})
    p = plan()
    reader = BoundedReader(p, tmp_path, transport=httpx.MockTransport(respond))
    asyncio.run(reader.read('discovery', 'https://data.sec.gov/submissions/CIK0000000123.json'))
    assert reader.logical == 1 and reader.attempts == 3 and len(set(calls)) == 1
    assert len({r['request_sha256'] for r in reader.receipts}) == 1
    assert [r['retry'] for r in reader.receipts] == [False, True, True]


def test_retries_stop_at_three(tmp_path, monkeypatch):
    async def no_sleep(_):
        pass
    monkeypatch.setattr('app.services.bounded_financial_acquisition.asyncio.sleep', no_sleep)
    reader = BoundedReader(plan(), tmp_path, transport=httpx.MockTransport(lambda r: httpx.Response(503)))
    with pytest.raises(AcquisitionDenied):
        asyncio.run(reader.read('discovery', 'https://data.sec.gov/submissions/CIK0000000123.json'))
    assert reader.attempts == 3


def test_unselected_document_and_outside_provider_denied(tmp_path):
    reader = BoundedReader(plan(), tmp_path)
    with pytest.raises(SystemicStop):
        asyncio.run(reader.read('document', 'https://evil.test/a'))
    with pytest.raises(SystemicStop, match='frozen_selection'):
        asyncio.run(reader.read('document', 'https://www.sec.gov/Archives/edgar/data/123/000000012326000001/main.htm', filing=filing()))
    assert reader.logical == reader.attempts == 0


def observation(year=2026, **overrides):
    lineage = {'source_document_id': 'document', 'source_document_type':'10-Q',
        'filing_date':f'{year}-08-01', 'occurrence_id':f'row-{year}', 'semantic':'us-gaap:Revenues',
        'period_start':f'{year}-04-01', 'period_end':f'{year}-06-30', 'period_role':'SINGLE_QUARTER',
        'statement_basis':'entity_wide', 'currency':'USD', 'unit':'USD', 'unit_scale':1, **overrides}
    return field_record(plan(), metric='revenue', value=100, lineage=lineage, quality=[], raw_sha='a'*64, role='current')


def test_absolute_context_not_direction_and_compatible_pair():
    row = observation()
    assert row['context_eligible'] and not row['direction_eligible']
    assert paired(row, observation(2025))


@pytest.mark.parametrize('key,value', [('period_role','CUMULATIVE_YTD'),('statement_basis','separate'),
    ('currency','KRW'),('unit','million USD'),('unit_scale',1000000),('semantic','us-gaap:ProfitLoss'),
    ('formal_state','PROVISIONAL'),('canonical_company_id','another'),('canonical_security_id','other'),
    ('period_start','2025-01-01'),('context_eligible',False)])
def test_comparison_fail_closed(key, value):
    prior = observation(2025)
    prior[key] = value
    assert not paired(observation(), prior)


def test_missing_lineage_and_tainted_field_do_not_taint_clean_sibling():
    good = observation()
    bad = observation(occurrence_id=None)
    assert good['context_eligible'] and not bad['context_eligible']
    assert not paired(good, bad)


def test_caps_and_retained_controls():
    assert [x.maximum_logical for x in (DOMESTIC, FOREIGN, DART)] == [4,18,6]
    security = {**plan()['security'], 'ticker':'SNDK'}
    with pytest.raises(AcquisitionDenied):
        make_plan(security, market='us', cutoff=datetime.now(timezone.utc), run_id='x')


def test_secret_echo_fails_closed_without_archiving(tmp_path):
    reader = BoundedReader(plan('kr'), tmp_path, api_key='do-not-archive',
        transport=httpx.MockTransport(lambda r: httpx.Response(200, text='do-not-archive')))
    with pytest.raises(SystemicStop, match='secret_echo'):
        asyncio.run(collect(reader))
    assert reader.receipts[0]['failure_class'] == 'SYSTEMIC_STOP'
    assert not list(tmp_path.glob('*.body'))
    assert all(b'do-not-archive' not in p.read_bytes() for p in tmp_path.iterdir())


def sec_fixture(tmp_path, *, ticker='FIXTURE', cik='123', only_current=False, conflict=False, security=None):
    from test_external_api_accuracy import _companyfact_entry, _companyfacts_payload
    p = plan()
    p['ticker'] = ticker
    p['issuer'] = cik.zfill(10)
    p['security'].update(ticker=ticker,cik=cik)
    if security:
        p['security']=security
    from app.services.unified_snapshot_contract import digest
    p['identity_sha256']=digest(p['security'])
    f = filing('10-Q')
    f['accessionNumber'] = f'{int(cik):010d}-26-000001'
    current = {**_companyfact_entry(30, fp='Q2', start='2026-04-01', end='2026-06-30', filed='2026-08-01'),
               'accn':f['accessionNumber']}
    rows = [current] if only_current else [current,dict(current,start='2025-04-01',end='2025-06-30',val=-20)]
    concepts = {'Revenues':[dict(r,val=100) for r in rows], 'OperatingIncomeLoss':rows}
    if conflict:
        concepts['RevenueFromContractWithCustomerExcludingAssessedTax']=[dict(r,val=10) for r in rows]
    payload = _companyfacts_payload('us-gaap', concepts)
    payload['cik'] = int(cik)
    def respond(request):
        if '/submissions/' in str(request.url):
            response = submission([f])
            response['cik'] = int(cik)
            return httpx.Response(200,json=response)
        if '/companyfacts/' in str(request.url):
            return httpx.Response(200,json=payload)
        return httpx.Response(200,text='<html>Official primary document fixture</html>')
    reader = BoundedReader(p,tmp_path,transport=httpx.MockTransport(respond))
    acquisition = asyncio.run(collect(reader))
    return p, acquisition, reader.receipts


@pytest.mark.parametrize('current_only', [True,False])
@pytest.mark.parametrize('conflict', [True,False])
def test_sec_raw_to_existing_quality_direction_owner(tmp_path,current_only,conflict):
    p,a,r = sec_fixture(tmp_path,only_current=current_only,conflict=conflict)
    result = project(p,a,tmp_path,r)
    assert result == project(p,a,tmp_path,r)
    assert result['context_eligible']
    assert result['direction_eligible'] == (not current_only)
    if conflict:
        assert all(c['metric']=='operating_income' for b in result['quality_bundles'] for c in b['quality']['comparative_observations'])
    with pytest.raises(ValueError,match='raw_receipt_hash_mismatch'):
        (tmp_path / a['companyfacts_artifact']).write_text('{}')
        project(p,a,tmp_path,r)


def test_dart_exact_occurrence_anomaly_and_clean_sibling(tmp_path):
    p = plan('kr')
    discovery = {'status':'000','total_page':1,'list':[{'corp_code':p['issuer'],'corp_name':'Fixture',
        'report_nm':'반기보고서 (2026.06)','rcept_no':'20260814000001','rcept_dt':'20260814'}]}
    rows=[]
    for i,(metric,account,label,value,prior) in enumerate([
        ('revenue','ifrs-full_Revenue','매출액',100,80),
        ('operating_income','dart_OperatingIncomeLoss','영업이익',76,30),
        ('net_income','ifrs-full_ProfitLoss','당기순이익',120,20)]):
        rows.append({'corp_code':p['issuer'],'rcept_no':'20260814000001','bsns_year':'2026','reprt_code':'11012',
            'fs_div':'CFS','sj_div':'CIS','account_id':account,'account_nm':label,'account_detail':'-',
            'ord':str(i+1),'currency':'KRW','thstrm_amount':str(value),'frmtrm_q_amount':str(prior)})
    def respond(request):
        if request.url.path.endswith('list.json'):
            return httpx.Response(200,json=discovery)
        return httpx.Response(200,json={'status':'000','list':rows if request.url.params['fs_div']=='CFS' else []})
    reader=BoundedReader(p,tmp_path,api_key='test',transport=httpx.MockTransport(respond))
    acquisition=asyncio.run(collect(reader))
    result=project(p,acquisition,tmp_path,reader.receipts)
    fields={r['metric']:r for r in result['fields']}
    assert fields['revenue']['context_eligible']
    assert not fields['operating_income']['context_eligible']
    assert not fields['net_income']['context_eligible']
    assert result['direction_eligible']
    assert [r['metric'] for r in result['quality_bundles'][0]['quality']['comparative_observations']]==['revenue']
    assert reader.attempts==3


def test_actual_stock_materializer_comparative_binding(tmp_path):
    from test_unified_stock_owner import source
    from app.services.unified_stock_owner import assemble_stock
    from app.services.bounded_financial_stock_owner import assemble, validate
    inputs=source.__wrapped__()
    baseline=assemble_stock(**inputs)
    local=inputs['local_seed']
    security=next(r['record'] for c in local['roles'].values() for r in c['records'] if r['table']=='securitymaster')
    p,a,r=sec_fixture(tmp_path,ticker='CORZ',cik='1234',security=security)
    args=dict(baseline=baseline,plan=p,acquisition=a,directory=tmp_path,receipts=r,local_seed=local)
    result=assemble(**args)
    assert result['status']=='PASS', result['mandatory_missing']
    assert len(result['comparative_fact_refs'])==2
    assert validate(result,**args)
    result['packet']['stocks'][0]['fact_catalog'][-1]['fields']['current_value']=9999
    with pytest.raises(ValueError,match='replay_mismatch'):
        validate(result,**args)


def test_shadow_numeric_binding_does_not_change_default_registry():
    from app.services.numeric_semantic_registry import build_numeric_registry
    from app.services.bounded_financial_stock_owner import comparison_numeric_semantic
    fact={'fact_id':'comparison','fact_type':'earnings_comparison','fields':{
        'metric':'revenue','currency':'USD','current_value':100,'prior_comparable_value':80,'delta':20,'growth_pct':25}}
    original=build_numeric_registry([fact])
    assert not any(r['registered'] for r in original)
    shadow=build_numeric_registry([fact],semantic_resolver=comparison_numeric_semantic)
    assert all(r['registered'] and not r['prose_allowed'] for r in shadow)
    assert build_numeric_registry([fact])==original
    fact['fields']['unowned_number']=999
    shadow=build_numeric_registry([fact],semantic_resolver=comparison_numeric_semantic)
    assert not shadow[-1]['registered']
