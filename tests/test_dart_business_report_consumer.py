"""Current-report binding, quantitative provenance and price-blind consumption on a fictional issuer."""
from copy import deepcopy
from io import BytesIO
import json
import zipfile

import pytest

from app.services.bounded_financial_projection import reported_filing_context
from app.services.canonical_monitoring_input import economic_context, filing_observations, pass_a_filing_context
from app.services.dart_report_artifact import DART_REPORT_URL
from app.services.detailed_stock_message_v2 import _cited_filing_rows
from app.services.numeric_semantic_registry import build_numeric_registry
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest
from tests.test_step2_dart_operating_context import PLAN, FILING, DOCUMENT, RND, view


_PERIOD = '<TU AUNIT="PERIODFROM" AUNITVALUE="20260101"></TU><TU AUNIT="PERIODTO" AUNITVALUE="20260630"></TU>'
_RAW = f'''<DOCUMENT><DOCUMENT-NAME ACODE="11012">반기보고서</DOCUMENT-NAME>
<COMPANY-NAME AREGCIK="{PLAN['issuer']}">가상기업</COMPANY-NAME><BODY><COVER>{_PERIOD}</COVER>
<SECTION-1><TITLE>II. 사업의 내용</TITLE><SECTION-2><TITLE>영업 현황</TITLE>
<P>당사는 생산 물량 증가에 힘입어 수익성이 개선되었습니다.</P>
<P>당사는 공장 증설을 통해 생산능력을 확대할 계획입니다.</P>
<P>당사는 현재 주가 변동으로 인한 공정가치 위험에 노출되어 있습니다.</P>
</SECTION-2><SECTION-2><TITLE>생산시설 및 가동 현황</TITLE>
<TABLE><TR><TD>(단위 : 배치)</TD></TR></TABLE>
<TABLE><TR><TH>구분</TH><TH>당반기 누적</TH></TR><TR><TD>생산능력</TD><TD>150</TD></TR>
<TR><TD>생산실적</TD><TD>120</TD></TR><TR><TD>가동률</TD><TD>80.00%</TD></TR></TABLE>
</SECTION-2></SECTION-1></BODY></DOCUMENT>'''


def source_rows(directory, xml=_RAW, *, filing=FILING, diagnostic=None):
    plan = dict(PLAN, dart_business_report=True)
    data = BytesIO()
    with zipfile.ZipFile(data, 'w') as archive:
        archive.writestr(filing['receipt_no']+'.xml', xml.encode())
    artifact = 'request-2-attempt-1.body'
    (directory/artifact).write_bytes(data.getvalue())
    cfs = json.dumps(dict(status='000', list=[RND])).encode()
    (directory/'current.body').write_bytes(cfs)
    frozen = dict(plan_sha256=digest(plan), method='GET', stage='dart_report', logical_id=2, filing=filing,
                  url=DART_REPORT_URL, params=dict(rcept_no=filing['receipt_no']))
    (directory/'request-2.plan.json').write_text(json.dumps(frozen))
    receipts = [
        dict(stage='statement', artifact='current.body', raw_sha256=sha256_bytes(cfs)),
        dict(stage='dart_report', plan_sha256=digest(plan), request_sha256=digest(frozen), logical_id=2,
             filing=filing, artifact=artifact,
             finished_at=PLAN['cutoff'], attempt=1, HTTP_status=200, raw_sha256=sha256_bytes(data.getvalue())),
    ]
    acquisition = dict(selected_filings=[filing], documents=[DOCUMENT], dart_report=dict(
        filing=filing, status='CAPTURED', artifact=artifact))
    return reported_filing_context(plan, acquisition, directory, receipts, report_diagnostic=diagnostic)


def test_original_and_business_context_mix_and_keep_separate_permissions(tmp_path):
    rows = source_rows(tmp_path)
    stocks = view(rows)
    ctx = dict(source_use_projection=dict(source_permissions=[]), decision_evidence=[])
    model = economic_context(stocks, ctx, {})
    assert 'Consolidated reported accounts' in model['filing_scope'] and 'DART business' in model['filing_scope']
    assert {r['ref_id'] for r in model['observations']} == {r['ref_id'] for r in rows}
    assert not model['relationships']
    assert len([r for r in rows if r['kind']=='REPORTED_OPERATING_CONTEXT_ONLY']) == 2
    measures = {r['observation']['metric']:r for r in rows if r['kind']=='DART_BUSINESS_METRIC_CONTEXT_ONLY'}
    assert set(measures) == {'production_capacity', 'production_output', 'utilization_rate'}
    row = measures['production_capacity']
    assert row['observation']['currency'] is None and row['observation']['unit']=='배치'
    assert not row['observation']['direction_eligible']
    assert row['observation']['source_document_id']==FILING['receipt_no']
    assert row['observation']['xml_sha256']==sha256_bytes(_RAW.encode())
    assert row['observation']['source_literal'].endswith('150')

    grant = dict(ref_id='canonical:comparison:parent', allowed_uses=['PASS_A_ARCHETYPE'])
    gate = dict(source_use_projection=dict(source_permissions=[grant]), eligible_non_price_evidence=[grant])
    blind = pass_a_filing_context(stocks, gate)
    assert row['ref_id'] in {r['ref_id'] for r in blind}
    assert not any('현재 주가' in str(r) for r in blind)
    stocks['packet']['stocks'][0]['fact_catalog'][0]['fields']['source_receipt'] = 'another'
    assert pass_a_filing_context(stocks, gate) == []

    reported = next(r for r in rows if r['observation'].get('classification')=='MANAGEMENT_OUTLOOK_OR_ESTIMATE')
    ref = measures['utilization_rate']['ref_id']
    output = dict(valuation_context=dict(business_evidence_refs=[reported['ref_id'], ref]))
    cited = _cited_filing_rows(dict(economic_context=model), output, stocks)
    assert len(cited)==2
    assert '계획입니다' in cited[0].text and '전망·계획' in cited[0].text
    assert '80%' in cited[1].text and '2026-01-01~2026-06-30' in cited[1].text
    assert cited[1].numeric_registry_keys == (ref+':fields.utilization_rate',)
    assert 'KRW' not in cited[1].text
    assert not _cited_filing_rows(dict(economic_context=model), dict(valuation_context=dict(business_evidence_refs=[])), stocks)


def test_dart_numeric_citation_requires_measured_field_same_owner_and_signed_content(tmp_path):
    rows = source_rows(tmp_path)
    row = next(r for r in rows if r['kind']=='DART_BUSINESS_METRIC_CONTEXT_ONLY')
    original = view([row])
    assert len(filing_observations(original))==1
    for alteration in [dict(unit='KRW'), dict(field_path='fields.other'), dict(registered=False),
                       dict(fact_type='earnings_comparison'), dict(prose_allowed=False), dict(value=399)]:
        changed = deepcopy(row)
        changed['numeric_registry_entry'].update(alteration)
        assert not filing_observations(view([changed]))
    for alteration in [dict(owner_type='direct_sec'), dict(bridge_receipt={'security':'another'})]:
        changed = deepcopy(original)
        changed['selected_financial_owner'].update(alteration)
        assert not filing_observations(changed)
    changed = deepcopy(row)
    changed['observation']['subject']='다른 사업부'
    assert not filing_observations(view([changed]))


@pytest.mark.parametrize('xml,filing', [
    (_RAW.replace('AUNITVALUE="20260630"', 'AUNITVALUE="20260331"'), FILING),
    (_RAW, dict(FILING,report_name='반기보고서 (2025.06)')),
    (_RAW.replace('AREGCIK="12345678"','AREGCIK="12345679"'), FILING),
])
def test_optional_invalid_document_preserves_existing_opendart_accounts(tmp_path, xml, filing):
    diagnostic = {}
    rows = source_rows(tmp_path, xml, filing=filing, diagnostic=diagnostic)
    assert diagnostic['acquisition_status']=='CAPTURED' and diagnostic['status']=='UNAVAILABLE'
    assert diagnostic['receipt_no']==FILING['receipt_no']
    if '20260331' in xml:
        assert diagnostic['reason']=='DART_REPORT_PARSE_UNAVAILABLE'
    assert all(row['kind']=='REPORTED_OPERATING_CONTEXT_ONLY' for row in rows)
    if filing==FILING:
        assert len(rows)==2


def test_registry_currency_scale_precision_and_wrong_units():
    amount = 9007199254740993
    def registered(metric, value, unit):
        row, = build_numeric_registry([dict(fact_type='dart_business_metric', fact_id='example',
            as_of_date='2026-06-30', fields={metric:value, 'unit':unit})])
        return row
    assert registered('business_revenue', amount, 'KRW')['canonical_display_value'] == '9,007,199,254,740,993 KRW'
    assert registered('business_revenue_share', 19.23, 'pct')['canonical_display_value'] == '19.23%'
    assert not registered('business_revenue', 1, 'pct')['registered']
    assert not registered('production_capacity', 1, 'KRW')['registered']
    assert not registered('new_metric', 1, '배치')['registered']

def test_accepted_kr_citations_in_final_detail_and_preopen_terminal(tmp_path, monkeypatch):
    from datetime import date
    from app.services import production_message_renderer as renderer
    from app.services.preopen_base import read_preopen_base
    from app.services.vnext_execution_profile import SOL_HIGH_V1
    from tests.test_c44_renderer_replay import synthetic_renderer_case
    from tests.test_preopen_base import _terminal

    rows = source_rows(tmp_path)
    cited = [r['ref_id'] for r in rows if r['observation'].get('metric')=='production_output'
             or r['observation'].get('classification')=='MANAGEMENT_OUTLOOK_OR_ESTIMATE']
    assert len(cited)==2
    session, ticker, accepted, result, request = synthetic_renderer_case(
        'kr', filing_view=view(rows), cited_refs=cited, include_support=True)
    monkeypatch.setattr(renderer, 'stock_plan', lambda *_: accepted)
    detail = renderer.stock_message(session, ticker, result, execution_profile=SOL_HIGH_V1, include_summary=True)
    assert '120 배치' in detail['text'] and '생산능력을 확대할 계획입니다' in detail['text']
    assert '150 배치' not in detail['text']
    assert detail['summary_row']['action'] in detail['text']
    assert detail['summary_row']['overall']==accepted.decision['overall_direction']
    session_date = date(2026,11,23)
    _, terminal = _terminal(tmp_path, market='kr', session=str(session_date), details=[detail])
    read = read_preopen_base(tmp_path, 'kr', session_date)
    assert read.status=='COMPLETE' and list(read.messages)==terminal['messages']
    assert read.rows[0]['preopen']==detail['summary_row']['preopen']
    assert request['provider_request']['input']['business_gate']['eligible_positive_core_refs_after_quality']
