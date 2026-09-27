import asyncio
from copy import deepcopy
import json

import httpx
import pytest

from app.services.bounded_financial_acquisition import (
    AcquisitionDenied, BoundedReader, collect, sec_base, sec_document_identity,
    exhibit_identities, exhibit_selection,
)
from app.services.bounded_financial_projection import REPORTED_FIELD_SPECS, project
from app.services.opendart_financial_recovery_service import FIELD_SPECS, select_field_occurrence
from app.services.sec_fpi_financial_purpose import (
    classify_document, candidate_inventory, select_economic_period, SEC_FPI_MAX_PURPOSE_CANDIDATES,
)
from test_bounded_financial_acquisition import plan, filing, submission
from app.services.bounded_fpi_followup import (
    make_followup_plan, request_manifest, FrozenFpiReader, verify_followup,
)
from app.services.unified_run_artifacts import durable_json
from app.services.unified_snapshot_contract import digest
from app.services.bounded_financial_acquisition import SystemicStop


@pytest.mark.parametrize('anchor', ['', '#income', '#balance', '#different'])
def test_same_document_fragment_identity(anchor):
    p, f = plan(foreign=True), filing()
    url = sec_base(p, f) + f['primaryDocument']
    assert sec_document_identity(url + anchor, p, f) == url


@pytest.mark.parametrize('suffix', ['../elsewhere.htm', './primary.htm', '%2e%2e/primary.htm',
    'primary.htm?version=2', 'primary.htm?', '/primary.htm', 'sub/primary.htm'])
def test_document_aliases_not_over_normalized(suffix):
    p, f = plan(foreign=True), filing()
    with pytest.raises(AcquisitionDenied):
        sec_document_identity(sec_base(p, f) + suffix, p, f)


@pytest.mark.parametrize('replacement', ['http://www.sec.gov', 'https://sec.gov', 'https://www.sec.gov:443',
    'https://www.sec.gov.evil.invalid', 'https://other.invalid', 'https://user@www.sec.gov'])
def test_document_host_identity(replacement):
    p, f = plan(foreign=True), filing()
    url = sec_base(p, f) + 'primary.htm'
    with pytest.raises(AcquisitionDenied):
        sec_document_identity(url.replace('https://www.sec.gov', replacement), p, f)


def test_other_filing_issuer_and_document_are_not_same():
    p, f = plan(foreign=True), filing()
    base = sec_base(p, f)
    assert sec_document_identity(base + 'ex99.htm', p, f) != sec_document_identity(base + 'primary.htm', p, f)
    for url in [sec_base(p, filing(ordinal=2)) + 'primary.htm', base.replace('/123/', '/456/') + 'primary.htm']:
        with pytest.raises(AcquisitionDenied):
            sec_document_identity(url, p, f)


def test_fragment_diagnostics_preserve_original_and_use_zero_exhibit_calls():
    p, f = plan(foreign=True), filing()
    html = '<a href="primary.htm#statement">Consolidated financial statements</a>'
    aliases = exhibit_identities({}, html, p, f)
    assert aliases and aliases[0]['original_url'].endswith('#statement')
    assert aliases[0]['already_captured_primary']
    assert exhibit_selection({}, html, p, f) == []


@pytest.mark.parametrize('href', ['../primary.htm#statement', './primary.htm#statement', '%2e%2e/primary.htm'])
def test_link_traversal_rejected_before_join(href):
    with pytest.raises(AcquisitionDenied):
        exhibit_selection({}, f'<a href="{href}">financial statements</a>', plan(foreign=True), filing())


def html_statement(current='2026-04-01 to 2026-06-30', prior='2025-04-01 to 2025-06-30'):
    return f'''<h2>Consolidated Statements of Income</h2>
    <p>In Thousands of New Taiwan Dollars</p><table>
    <tr><th></th><th>{current}</th><th>{prior}</th></tr>
    <tr><td>Net revenue</td><td>150</td><td>100</td></tr>
    <tr><td>Operating income</td><td>30</td><td>20</td></tr></table>'''


def purpose(html, f=None, name=None):
    f = f or filing('6-K')
    p = plan(foreign=True)
    return classify_document(html.encode(), url=sec_base(p, f) + (name or f['primaryDocument']), filing=f, plan=p)


@pytest.mark.parametrize('body,expected', [
    ('Response to disclosure inquiry about a possible factory.', 'RUMOR_OR_DISCLOSURE_RESPONSE'),
    ('Cash dividend adjustment', 'DIVIDEND_OR_CAPITAL_RETURN'),
    ('Restricted share award plan', 'GOVERNANCE_OR_COMPENSATION'),
    ('Initial public offering and lock-up terms', 'CORPORATE_EVENT_NONFINANCIAL'),
    ('Monthly revenue for August', 'REVENUE_DISCLOSURE_ONLY'),
    ('Financial results are attached.', 'UNKNOWN_PURPOSE'),
    ('Consolidated Statements of Income without actual cells', 'UNKNOWN_PURPOSE'),
    ('No recognized document purpose', 'UNKNOWN_PURPOSE'),
])
@pytest.mark.parametrize('cover', ['', 'The registrant files annual reports under cover of Form 20-F or Form 40-F.'])
def test_nonfinancial_or_title_only_never_authority(body, expected, cover):
    result = purpose('<p>' + cover + '</p><p>' + body + '</p>')
    assert result['purpose'] == expected
    assert not result['financial_authority'] and not result['economic_periods']


@pytest.mark.parametrize('form,prefix,name,expected', [
    ('6-K', '', 'primary.htm', 'FINANCIAL_STATEMENTS'),
    ('6-K', '<p>Quarterly financial results</p>', 'primary.htm', 'FINANCIAL_RESULTS_OR_EARNINGS'),
    ('6-K', '', 'ex99.htm', 'FINANCIAL_STATEMENTS'),
    ('20-F', '', 'primary.htm', 'FINANCIAL_STATEMENTS'),
])
def test_source_owned_financial_tables_not_filename(form, prefix, name, expected):
    html = html_statement('2025-01-01 to 2025-12-31', '2024-01-01 to 2024-12-31') if form == '20-F' else html_statement()
    result = purpose(prefix + html, filing(form), name)
    assert result['purpose'] == expected and result['financial_authority']
    assert result['purpose_evidence'] and all(p['source'] == 'EXACT_STATEMENT_CELL_HEADERS' for p in result['economic_periods'])
    if form == '20-F':
        assert select_economic_period([result])['status'] == 'BLOCKED'


def test_filing_event_date_does_not_become_financial_period():
    financial = purpose(html_statement(), {**filing('6-K'), 'reportDate': '2026-08-01'})
    event = purpose('<p>Cash dividend adjustment</p>', {**filing('6-K', 2), 'filingDate': '2026-09-01', 'reportDate': '2026-09-01'})
    selected = select_economic_period([financial, event])
    assert selected['status'] == 'PASS' and selected['period_end'] == '2026-06-30'
    assert financial['sec_report_date'] == '2026-08-01'
    assert not event['economic_periods']


def test_unresolved_newer_financial_and_annual_never_fallback():
    financial = purpose(html_statement())
    unresolved = purpose('<p>Financial results attached</p>', {**filing('6-K', 2), 'filingDate': '2026-09-01'})
    assert select_economic_period([financial, unresolved])['status'] == 'BLOCKED'
    assert select_economic_period([financial], uncaptured=[{'filingDate': '2026-09-01'}])['status'] == 'BLOCKED'
    annual = purpose(html_statement('2026-01-01 to 2026-08-31', '2025-01-01 to 2025-08-31'),
                     {**filing('20-F', 2), 'filingDate': '2026-09-01'})
    assert select_economic_period([financial, annual])['status'] == 'BLOCKED'


def test_financial_exhibit_owns_same_filing_even_if_cover_has_no_cells():
    cover = purpose('<p>Financial results attached.</p>')
    exhibit = purpose(html_statement(), name='ex99.htm')
    assert select_economic_period([cover, exhibit])['status'] == 'PASS'


def test_unparsed_annual_report_cannot_be_classified_by_incidental_dividend():
    annual = purpose('<p>Cash dividend paid. Annual report.</p>', filing('20-F'))
    assert annual['purpose'] == 'UNKNOWN_PURPOSE'
    assert not annual['financial_authority']


@pytest.mark.parametrize('caption', ['Consolidated interim statements of income',
    'Quarterly financial report', 'Interim financial statements', 'Annual financial information'])
def test_unparsed_financial_content_cannot_be_denied_by_incidental_purpose_words(caption):
    report = purpose(f'<p>{caption}. Cash dividend paid and compensation paid.</p>')
    assert report['purpose'] == 'UNKNOWN_PURPOSE'
    assert not report['financial_authority']


@pytest.mark.parametrize('count', [0, 1, 7, 8, 9, 30])
def test_purpose_candidate_cap_and_metadata_order(count):
    rows = [filing('6-K', i + 1) for i in range(count)]
    p = plan(foreign=True)
    first = candidate_inventory(submission(rows), p)
    assert first == candidate_inventory(submission(list(reversed(rows))), p)
    assert len(first['inspection_window']) == min(count, SEC_FPI_MAX_PURPOSE_CANDIDATES)
    assert first['exhaustion_reason'] == ('FPI_FINANCIAL_PURPOSE_BOUND_EXHAUSTED' if count > 8 else None)
    renamed = deepcopy(rows)
    for row in renamed:
        row['primaryDocument'] = 'financial-results.htm'
    assert [r['accessionNumber'] for r in first['inspection_window']] == [
        r['accessionNumber'] for r in candidate_inventory(submission(renamed), p)['inspection_window']]


def insurance_row(**kw):
    return {'account_id': 'ifrs-full_InsuranceRevenue', 'account_nm': '보험수익', 'fs_div': 'CFS',
        'sj_div': 'CIS', 'thstrm_amount': '1000', 'frmtrm_q_amount': '800', 'currency': 'KRW', **kw}


@pytest.mark.parametrize('statement', ['IS', 'CIS'])
def test_exact_insurance_standard_concept(statement):
    row = insurance_row(sj_div=statement)
    result = select_field_occurrence({'CFS': [row]}, REPORTED_FIELD_SPECS['revenue'])
    assert result.status == 'selected' and result.row['account_id'] == 'ifrs-full_InsuranceRevenue'
    assert 'ifrs-full_insurancerevenue' not in FIELD_SPECS['revenue'].account_ids


@pytest.mark.parametrize('change', [
    {'sj_div': 'BS'}, {'sj_div': 'CF'}, {'account_id': 'ifrs-full_InvestmentIncome'},
    {'account_id': 'ifrs-full_InterestRevenue'}, {'account_id': 'ifrs-full_DividendRevenue'},
    {'account_id': 'ifrs-full_ReinsuranceIncome'}, {'account_id': 'ifrs-full_FinanceIncome'},
    {'account_id': 'dart_OtherOperatingIncome'}, {'account_id': 'custom_InsuranceRevenue'},
    {'account_id': 'dart_OperatingIncomeInsurance', 'account_nm': '보험영업수익'},
])
def test_insurance_names_never_fuzzy_financial_authority(change):
    row = insurance_row(**change)
    for metric in ('revenue', 'operating_income'):
        assert select_field_occurrence({'CFS': [row]}, REPORTED_FIELD_SPECS[metric]).status == 'missing'


@pytest.mark.parametrize('case', ['clean', 'extreme', 'missing_currency', 'wrong_period', 'wrong_issuer'])
def test_insurance_mapping_uses_unchanged_lineage_and_quality(tmp_path, case):
    p = plan('kr')
    filing_id = '20260814000001'
    identity = {'corp_code': p['issuer'], 'rcept_no': filing_id, 'bsns_year': '2026', 'reprt_code': '11012'}
    revenue = insurance_row(**identity, ord='1', account_detail='-')
    income = {**insurance_row(**identity), 'ord': '2', 'account_detail': '-', 'account_id': 'ifrs-full_ProfitLossFromOperatingActivities',
        'account_nm': '영업이익', 'thstrm_amount': '120' if case != 'extreme' else '900', 'frmtrm_q_amount': '100'}
    if case == 'missing_currency':
        revenue['currency'] = None
    if case == 'wrong_period':
        revenue['reprt_code'] = '11013'
    if case == 'wrong_issuer':
        revenue['corp_code'] = '00999999'
    def respond(request):
        if request.url.path.endswith('list.json'):
            return httpx.Response(200, json={'status': '000', 'total_page': 1, 'list': [
                {'corp_code': p['issuer'], 'report_nm': '반기보고서 (2026.06)', 'rcept_no': filing_id, 'rcept_dt': '20260814'}]})
        return httpx.Response(200, json={'status': '000', 'list': [revenue, income] if request.url.params['fs_div'] == 'CFS' else []})
    reader = BoundedReader(p, tmp_path, api_key='test', transport=httpx.MockTransport(respond))
    acquired = asyncio.run(collect(reader))
    result = project(p, acquired, tmp_path, reader.receipts)
    if case in {'missing_currency', 'wrong_period', 'wrong_issuer'}:
        assert not result['direction_eligible']
    else:
        assert result['direction_eligible']
        metrics = {r['metric'] for r in result['comparisons']}
        assert 'revenue' in metrics
        assert ('operating_income' in metrics) == (case == 'clean')


def followup_fixture(tmp_path, monkeypatch=None, *, status=200):
    parent = plan(foreign=True)
    discovery = json.dumps(submission([filing('6-K')])).encode()
    p = make_followup_plan(parent, discovery, [])
    durable_json(tmp_path / 'plan.json', p)
    durable_json(tmp_path / 'request-manifest.json', [
        {'request': r, 'request_sha256': digest(r)} for r in request_manifest(p)])
    async def no_sleep(_):
        pass
    if monkeypatch:
        monkeypatch.setattr('app.services.bounded_financial_acquisition.asyncio.sleep', no_sleep)
    calls = []
    def respond(request):
        calls.append(str(request.url))
        if status != 200:
            return httpx.Response(status)
        if request.url.path.endswith('index.json'):
            return httpx.Response(200, json={'directory': {'name': request.url.path.rsplit('/', 1)[0], 'item': []}})
        return httpx.Response(200, text=html_statement())
    reader = FrozenFpiReader(p, tmp_path, transport=httpx.MockTransport(respond))
    reader.select(p['candidates'])
    for request in p['exact_requests']:
        try:
            asyncio.run(reader.read(**request))
        except AcquisitionDenied:
            pass
    durable_json(tmp_path / 'receipts.json', reader.receipts)
    return parent, discovery, p, reader, calls


def test_followup_exact_receipts_and_no_response_dependent_calls(tmp_path):
    parent, raw, p, reader, calls = followup_fixture(tmp_path)
    verified = verify_followup(parent, raw, [], tmp_path)
    assert verified['complete_exact_manifest'] and len(verified['documents']) == 1
    assert reader.logical == reader.attempts == p['maximum_logical_requests'] == 2
    assert len(calls) == 2 and p['limits']['linked_exhibits'] == 0
    assert p['limits']['documents_per_filing'] <= parent['limits']['documents_per_filing']
    with pytest.raises(SystemicStop, match='frozen_manifest'):
        asyncio.run(reader.read('document', sec_base(p, p['candidates'][0]) + 'ex99.htm', filing=p['candidates'][0]))
    assert len(calls) == 2


@pytest.mark.parametrize('status,attempts', [(503, 6), (429, 6), (404, 2)])
def test_followup_transient_only_byte_identical_retry(tmp_path, monkeypatch, status, attempts):
    parent, raw, p, reader, calls = followup_fixture(tmp_path, monkeypatch, status=status)
    verified = verify_followup(parent, raw, [], tmp_path)
    assert not verified['complete_exact_manifest'] and not verified['documents']
    assert reader.logical == 2 and reader.attempts == attempts <= p['maximum_HTTP_attempts']
    assert len(set(calls)) == 2


@pytest.mark.parametrize('mutation', ['plan', 'manifest', 'raw', 'receipt_hash', 'receipt_issuer',
    'receipt_stage', 'receipt_attempt', 'source_identity', 'discovery', 'dispatched_request'])
def test_followup_rejects_source_plan_receipt_mutations(tmp_path, mutation):
    parent, raw, _p, _reader, _calls = followup_fixture(tmp_path)
    if mutation == 'source_identity':
        parent['issuer'] = '0000000456'
    elif mutation == 'discovery':
        payload = json.loads(raw)
        payload['cik'] = 456
        raw = json.dumps(payload).encode()
    elif mutation == 'raw':
        (tmp_path / 'request-002-attempt-1.body').write_bytes(b'altered')
    else:
        name = {'plan': 'plan.json', 'manifest': 'request-manifest.json',
                'dispatched_request': 'request-002.plan.json'}.get(mutation, 'receipts.json')
        data = json.loads((tmp_path / name).read_bytes())
        if mutation == 'plan':
            data['maximum_logical_requests'] += 1
        elif mutation == 'manifest':
            data[0]['request']['url'] += '?query=1'
        elif mutation == 'dispatched_request':
            data['url'] += '#fragment'
        elif mutation == 'receipt_hash':
            data[-1]['request_sha256'] = 'f' * 64
        elif mutation == 'receipt_issuer':
            data[-1]['filing']['accessionNumber'] = filing(ordinal=3)['accessionNumber']
        elif mutation == 'receipt_stage':
            data[-1]['stage'] = 'companyfacts'
        else:
            data[-1]['attempt'] = 4
        (tmp_path / name).write_text(json.dumps(data))
    with pytest.raises((ValueError, AcquisitionDenied)):
        verify_followup(parent, raw, [], tmp_path)


def test_followup_reuses_captured_primary_without_new_call(tmp_path):
    parent = plan(foreign=True)
    f = filing('6-K')
    discovery = json.dumps(submission([f])).encode()
    p = make_followup_plan(parent, discovery, [{'url': sec_base(parent, f) + f['primaryDocument']}])
    assert p['exact_requests'] == [] and p['maximum_HTTP_attempts'] == 0
