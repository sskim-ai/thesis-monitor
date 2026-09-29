import asyncio
from copy import deepcopy
from datetime import date, datetime, timezone
import json

import httpx
import pytest

from app.services.bounded_financial_acquisition import make_plan, collect, BoundedReader, sec_selection, sec_base
from app.services.bounded_financial_projection import project
from app.services.issuer_fiscal_week_policy import extract_policy, annual_comparability, WARNING
from app.services.sec_primary_inline_financial import extract, errors, merge_occurrences
from app.services.sec_foreign_comparison_service import current_projection, parse_document
from app.services.sec_financial_source_completeness import completeness, UNAVAILABLE
from app.services.sec_fpi_financial_purpose import classify_document
from app.services.sealed_financial_slots import financial_slots
from app.services.unified_snapshot_contract import digest
from test_bounded_financial_acquisition import filing, submission

CALENDAR = '''The Company's fiscal year ends on the Friday nearest to June 30 and typically consists of 52 weeks.
Approximately every five to six years, we report a 53-week fiscal year to align the fiscal year with the foregoing policy.
Fiscal year 2026 was comprised of 53 weeks and ended on July 3, 2026.
Fiscal years 2025 and 2024, which ended on June 27, 2025 and June 28, 2024, respectively, were each comprised of 52 weeks.'''


def fiscal_tuple(start='2025-06-28', end='2026-07-03'):
    return dict(issuer='123', metric='revenue', semantic='us-gaap:Revenues', statement_basis='entity_wide',
        currency='USD', unit='USD', unit_scale=1, formal_state='FORMAL', period_role='ANNUAL',
        source_document_id=filing('10-K')['accessionNumber'], period_start=start, period_end=end)


def test_issuer_declared_fiscal_week_policy_and_normal_52_52():
    p = extract_policy(CALENDAR.encode(), issuer='123', filing=filing('10-K'))
    b = fiscal_tuple('2024-06-29', '2025-06-27')
    result = annual_comparability(fiscal_tuple(), b, p)
    assert result['quality_reason_codes'] == [WARNING]
    assert result['current_weeks'] == 53 and result['prior_weeks'] == 52 and result['value_adjustment'] is None
    normal = annual_comparability(b, fiscal_tuple('2023-07-01', '2024-06-28'), p)
    assert normal and not normal['quality_reason_codes']


@pytest.mark.parametrize('change', [
    {'currency': 'KRW'}, {'statement_basis': 'separate'}, {'issuer': '456'},
    {'period_role': 'SINGLE_QUARTER'}, {'period_start': '2025-06-21'},
    {'period_end': '2027-07-03'}, {'formal_state': 'PROVISIONAL'},
    {'unit_scale': 1000},
])
def test_fiscal_week_strict_negative(change):
    p = extract_policy(CALENDAR.encode(), issuer='123', filing=filing('10-K'))
    assert annual_comparability({**fiscal_tuple(), **change}, fiscal_tuple('2024-06-29', '2025-06-27'), p) is None


def test_date_difference_never_proves_policy():
    p = extract_policy(b'Fiscal year 2026 was comprised of 53 weeks and ended on July 3, 2026.', issuer='123', filing=filing('10-K'))
    assert annual_comparability(fiscal_tuple(), fiscal_tuple('2024-06-29', '2025-06-27'), p) is None
    assert annual_comparability(fiscal_tuple(), fiscal_tuple('2024-06-29', '2025-06-27'), None) is None


def plan():
    return make_plan(dict(ticker='SYNTHETIC', canonical_company_id='issuer', canonical_security_id='security',
        identity_provider='local', cik='123', issuer_type='foreign_private_issuer'), market='us',
        cutoff=datetime(2026, 9, 29, tzinfo=timezone.utc), run_id='synthetic', exact_financial_owner=True)


def inline_html(*, dimension='', unit='TWD', start='2025-01-01', end='2025-12-31', extra='', value='120', scale='3', sign='', concept='Revenue'):
    return f'''<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL" xmlns:xbrli="http://www.xbrl.org/2003/instance"
    xmlns:ifrs-full="https://xbrl.ifrs.org/taxonomy/2025-03-27/ifrs-full" xmlns:iso4217="http://www.xbrl.org/2003/iso4217"
    xmlns:ixt="http://www.xbrl.org/inlineXBRL/transformation/2020-02-12" xmlns:xbrldi="http://xbrl.org/2006/xbrldi">
    <h1>Consolidated Statements of Income</h1><ix:resources>
    <xbrli:context id="a"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0000000123</xbrli:identifier>{dimension}</xbrli:entity>
    <xbrli:period><xbrli:startDate>{start}</xbrli:startDate><xbrli:endDate>{end}</xbrli:endDate></xbrli:period></xbrli:context>
    <xbrli:context id="b"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0000000123</xbrli:identifier></xbrli:entity>
    <xbrli:period><xbrli:startDate>2024-01-01</xbrli:startDate><xbrli:endDate>2024-12-31</xbrli:endDate></xbrli:period></xbrli:context>
    <xbrli:unit id="u"><xbrli:measure>iso4217:{unit}</xbrli:measure></xbrli:unit></ix:resources>
    <ix:nonFraction id="first" name="ifrs-full:{concept}" contextRef="a" unitRef="u" scale="{scale}" sign="{sign}" format="ixt:num-dot-decimal">{value}</ix:nonFraction>
    <ix:nonFraction id="prior" name="ifrs-full:{concept}" contextRef="b" unitRef="u" scale="3" format="ixt:num-dot-decimal">100</ix:nonFraction>
    {extra}</html>'''


def extracted(html):
    p, f = plan(), {**filing('20-F'), 'reportDate': '2025-12-31'}
    return extract(html.encode(), issuer_cik='123', filing=f, source_url=sec_base(p, f) + f['primaryDocument'])


def test_exact_inline_annual_leap_year_unit_and_negative_value():
    x = extracted(inline_html(sign='-'))
    assert not x['denials'] and len(x['occurrences']) == 2
    assert x['occurrences'][0]['value'] == -120000
    assert all(not errors(o, date(2026, 9, 29)) for o in x['occurrences'])
    assert current_projection(x['occurrences'], required_role='annual', inline_currency_pair=True)['revenue'] == -120000


@pytest.mark.parametrize('kw,reason', [
    ({'dimension': '<xbrli:segment><xbrldi:explicitMember dimension="x:a">x:b</xbrldi:explicitMember></xbrli:segment>'}, 'INLINE_DIMENSIONED_CONTEXT'),
    ({'unit': 'shares'}, 'INLINE_CURRENCY_UNRESOLVED'),
    ({'start': '2025-01-02'}, 'INLINE_PERIOD_ROLE_UNRESOLVED'),
    ({'scale': '1.2'}, 'INLINE_PARSE_ERROR'),
    ({'value': '1,00'}, 'INLINE_NUMERIC_LITERAL_UNSUPPORTED'),
])
def test_inline_exact_context_negatives(kw, reason):
    result = extracted(inline_html(**kw))
    assert reason in {d['reason'] for d in result['denials']}
    assert not any(o['period_end'] == '2025-12-31' for o in result['occurrences'])


def test_inline_custom_concept_not_fuzzy_mapped():
    assert not extracted(inline_html(concept='MyRevenue'))['occurrences']


@pytest.mark.parametrize('value,expected', [('120', 2), ('121', 3)])
def test_duplicate_presentation_and_conflict_not_value_ranked(value, expected):
    extra = f'<ix:nonFraction id="copy" name="ifrs-full:Revenue" contextRef="a" unitRef="u" scale="3">{value}</ix:nonFraction>'
    x = extracted(inline_html(extra=extra))
    assert len(x['occurrences']) == expected
    if value == '121':
        assert current_projection(x['occurrences'], required_role='annual') is None


def test_note_column_cannot_override_inline_and_exact_conflict_denies():
    from test_residual_financial_semantics import html_statement
    f = filing('20-F')
    url = sec_base(plan(), f) + f['primaryDocument']
    table = parse_document(html_statement('2025-01-01 to 2025-12-31','2024-01-01 to 2024-12-31'),
        issuer_cik='123', accession=f['accessionNumber'], document_type=f['form'], filing_date=f['filingDate'],
        source_url=url, raw_payload=b'table')
    rows, conflicts = merge_occurrences(extracted(inline_html())['occurrences'], table, date(2026,9,29))
    assert conflicts and rows


def test_finite_candidate_inventory_and_sealed_slot_parity():
    p = plan()
    annual = {**filing('20-F', 99), 'reportDate': '2025-12-31'}
    quarter = {**filing('6-K', 1), 'primaryDocument': 'issuer-fsx20260814x6k.htm'}
    other = [{**filing('6-K', i+2), 'reportDate': f'2026-09-{i+1:02d}', 'filingDate': f'2026-09-{i+1:02d}'} for i in range(10)]
    selected = sec_selection(submission([annual, quarter, *other]), p)
    assert quarter['accessionNumber'] in {f['accessionNumber'] for f in selected}
    assert len(selected) <= 3
    assert p['maximum_logical_requests'] == 14
    slots = financial_slots(p, owner='owner', owner_sha256='a'*64, config_sha256='b'*64)
    assert len(slots) == 14
    fake = classify_document(b'Unknown', url=sec_base(p, quarter)+quarter['primaryDocument'], filing=quarter, plan=p)
    assert fake['purpose'] == 'UNKNOWN_PURPOSE' and not fake['financial_authority']


def test_full_mock_fpi_acquisition_primary_inline_projection(tmp_path):
    p = plan()
    p['cutoff'] = '2026-04-01T00:00:00+00:00'
    f = {**filing('20-F'), 'reportDate': '2025-12-31', 'filingDate': '2026-03-15'}
    def respond(request):
        if '/submissions/' in str(request.url):
            return httpx.Response(200, json=submission([f]))
        if '/companyfacts/' in str(request.url):
            return httpx.Response(200, json={'cik':123})
        if str(request.url).endswith('index.json'):
            assert (tmp_path/'fpi-current-financial-candidate-plan.json').exists()
            return httpx.Response(200, json={'directory':{'item':[]}})
        return httpx.Response(200, text=inline_html())
    reader = BoundedReader(p, tmp_path, transport=httpx.MockTransport(respond))
    acquisition = asyncio.run(collect(reader))
    first = project(p, acquisition, tmp_path, reader.receipts, field_semantics=True)
    assert first == project(p, acquisition, tmp_path, reader.receipts, field_semantics=True)
    assert first['comparisons'] and first['comparisons'][0]['current']['lineage']['amount'] == 120000
    assert first['comparisons'][0]['comparison']['lineage']['amount'] == 100000
    assert first['fpi_purpose']['selection']['status'] == 'PASS'
    modified = deepcopy(acquisition)
    modified['current_candidate_plan']['candidates'] = []
    with pytest.raises(ValueError, match='candidate_plan_replay'):
        project(p, modified, tmp_path, reader.receipts, field_semantics=True)


def source_absence():
    p, f = plan(), filing('6-K')
    d = classify_document(b'Cash dividend adjustment.',url=sec_base(p,f)+f['primaryDocument'],filing=f,plan=p)
    inventory = {'current_financial_plan': {'candidates':[f], 'outside_bound':[]}}
    return dict(plan=p, acquisition={}, inventory=inventory, documents=[d], uncaptured=[], acquisition_denials=[])


def test_source_complete_absence_is_not_clean_financial_quality():
    result = completeness(**source_absence())
    assert result['state'] == UNAVAILABLE and not result['direction_eligible']
    assert result['financial_fact_count'] == 0 and not result['source_history_exhausted']


@pytest.mark.parametrize('kind', ['purpose', 'parser', 'unattempted', 'denial', 'outside', 'lineage'])
def test_incomplete_source_never_unknown_limit(kind):
    args = source_absence()
    if kind == 'purpose':
        args['documents'][0]['purpose'] = 'UNKNOWN_PURPOSE'
    if kind == 'parser':
        args['documents'][0]['inline_owner']['status'] = 'NOT_RUN'
    if kind == 'unattempted':
        args['uncaptured'] = [filing()]
    if kind == 'denial':
        args['acquisition_denials'] = ['HTTP_FAILURE']
    if kind == 'outside':
        args['inventory']['current_financial_plan']['outside_bound'] = [{'reason':'OUTSIDE_FROZEN_TWO_CANDIDATE_BOUND'}]
    if kind == 'lineage':
        args['documents'][0]['inline_owner']['denials'] = [{'reason':'INLINE_PARSE_ERROR'}]
    assert completeness(**args)['state'] == 'SOURCE_OWNER_UNRESOLVED'


def test_policy_is_opt_in_not_a_production_default():
    p = plan()
    original = make_plan(p['security'], market='us', cutoff=datetime.fromisoformat(p['cutoff']),run_id=p['run_id'])
    assert 'financial_owner_policy' not in original and original['maximum_logical_requests'] == 18
    assert digest(original) != digest(p)
    assert json.dumps(p).find('SNDK') == -1


def test_same_filing_53_52_project_quality_fact_and_period_label(tmp_path):
    from test_external_api_accuracy import _companyfact_entry, _companyfacts_payload
    from scripts.m12dr_financial_source_authority import comparative_facts
    from app.services.canonical_business_quality_owner import derive_fresh
    security = {**plan()['security'], 'issuer_type':'domestic_us'}
    p = make_plan(security, market='us',cutoff=datetime(2026,9,29,tzinfo=timezone.utc),
        run_id='fiscal-fixture',exact_financial_owner=True)
    f = {**filing('10-K'), 'reportDate':'2026-07-03', 'filingDate':'2026-08-17'}
    current = {**_companyfact_entry(120,fp='FY',form='10-K',start='2025-06-28',end='2026-07-03',filed=f['filingDate']),
        'accn':f['accessionNumber']}
    prior = {**current,'start':'2024-06-29','end':'2025-06-27','val':100}
    payload = _companyfacts_payload('us-gaap',{'Revenues':[current,prior],'OperatingIncomeLoss':[
        {**current,'val':30},{**prior,'val':20}]})
    payload['cik'] = 123
    def respond(request):
        if '/submissions/' in str(request.url):
            return httpx.Response(200,json=submission([f]))
        if '/companyfacts/' in str(request.url):
            return httpx.Response(200,json=payload)
        return httpx.Response(200,text=CALENDAR)
    reader=BoundedReader(p,tmp_path,transport=httpx.MockTransport(respond))
    acquisition=asyncio.run(collect(reader))
    projection=project(p,acquisition,tmp_path,reader.receipts,field_semantics=True)
    assert len(projection['comparisons'])==2
    facts = [f for b in projection['quality_bundles'] for f in comparative_facts(b['quality'],ticker=p['ticker'],issuer_id='CIK:0000000123')]
    assert len(facts)==2 and all(f['fields']['period_type']=='annual' for f in facts)
    assert all(f['fields']['anomaly_cautions']==[WARNING] for f in facts)
    quality=derive_fresh(projection=projection,facts=facts,ticker=p['ticker'],security_id='security',run_id=p['run_id'])
    assert WARNING in quality['fact']['fields']['reason_codes']


@pytest.mark.parametrize('body,blocked', [('Cash dividend adjustment',False),('Financial results attached',True)])
@pytest.mark.parametrize('same_filing', [False, True])
def test_newer_document_purpose_content_not_filename(body,blocked,same_filing):
    from app.services.sec_fpi_field_selection import select_fields
    from app.models.financial import FinancialSnapshot
    p=plan()
    f={**filing('20-F'),'reportDate':'2025-12-31','filingDate':'2026-03-15'}
    url=sec_base(p,f)+f['primaryDocument']
    doc=classify_document(inline_html().encode(),url=url,filing=f,plan=p)
    row=FinancialSnapshot(ticker=p['ticker'],period='2025-12-31',financial_period_end=date(2025,12,31),
        filing_date=date(2026,3,15),source_filing_id=f['accessionNumber'],source=url,provider='sec_foreign_filing',
        currency='TWD',revenue=120000,period_scope='annual',period_type='annual',is_cumulative=True,
        raw_financial_fields=json.dumps([{'field':'foreign_business_occurrences','occurrences':doc['occurrences']}]))
    newer=f if same_filing else filing('6-K',2)
    other=classify_document(body.encode(),url=sec_base(p,newer)+newer['primaryDocument'],filing=newer,plan=p)
    _,result=select_fields([doc,other],[row],ticker=p['ticker'],cutoff=p['cutoff'],allow_inline_annual=True)
    assert (result['status']=='BLOCKED') is blocked
