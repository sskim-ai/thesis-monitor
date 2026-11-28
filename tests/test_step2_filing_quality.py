import json
from types import SimpleNamespace

import pytest

from app.services import new_buyer_request_owner
from app.services.accepted_calibration_message_service import _session_index_line
from app.services.bounded_financial_projection import _sec_context_fields, reported_filing_context
from app.services.canonical_monitoring_input import economic_context, pass_a_filing_context
from app.services.detailed_stock_message_v2 import _cited_filing_rows, _sentence_lines
from app.services.event_relevance_service import operating_headline_lead
from app.services.reported_filing_context import extract_filing, select_observations
from app.services.unified_snapshot_contract import digest


PLAN = dict(provider='sec_edgar', ticker='EXAMPLE', issuer='123', cutoff='2026-11-28',
            security=dict(canonical_company_id='issuer', canonical_security_id='security'))
FILING = dict(role='current', accessionNumber='0000000123-26-000001', filingDate='2026-11-03',
              reportDate='2026-09-30', form='10-Q', primaryDocument='q.htm')
RAW = b'''<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
 xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:xbrldi="http://xbrl.org/2006/xbrldi"
 xmlns:ex="https://example.com/2026" xmlns:us-gaap="http://fasb.org/us-gaap/2026" xmlns:iso4217="http://www.xbrl.org/2003/iso4217">
 <ix:header><xbrli:context id="op"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">123</xbrli:identifier>
 <xbrli:segment><xbrldi:explicitmember dimension="us-gaap:StatementBusinessSegmentsAxis">ex:CloudMember</xbrldi:explicitmember>
 </xbrli:segment></xbrli:entity><xbrli:period><xbrli:startdate>2026-07-01</xbrli:startdate><xbrli:enddate>2026-09-30</xbrli:enddate>
 </xbrli:period></xbrli:context><xbrli:unit id="usd"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit></ix:header>
 <p>Revenue increased primarily due to higher demand for hosted services.</p>
 <p>We expect our production capacity to increase after the new facility opens.</p>
 <p>The company delivered services under a new customer contract during the quarter.</p>
 <table><tr><td><ix:nonfraction name="us-gaap:Revenues" contextref="op" unitref="usd" scale="6">12.5</ix:nonfraction></td></tr></table>
 </html>'''


def source(raw=RAW):
    native = select_observations(*extract_filing(PLAN, FILING, 'q.htm', raw))
    stock = dict(ticker='EXAMPLE', reported_filing_context=native, fact_catalog=[
        dict(fact_id='earnings_comparison:example', fact_type='earnings_comparison', fields={'source_receipt':FILING['accessionNumber']})])
    return dict(ticker='EXAMPLE', packet={'stocks':[stock]}, projection={'fields':[]},
                valuation_view={'security_id':'security'}, selected_financial_owner=dict(
                    owner_type='direct_sec', issuer_identity='123', monitored_security='EXAMPLE',
                    selected_projection_sha256=digest({'fields':[]})))


def economy(view):
    return economic_context(view, dict(decision_evidence=[],source_use_projection={'source_permissions':[]}), {})


def test_filing_provenance_segment_units_and_management_voice():
    view = source()
    fields = economy(view)['observations']
    assert {r['observation'].get('classification') for r in fields} == {
        'MANAGEMENT_EXPLANATION', 'COMPANY_REPORTED_OBSERVATION', 'MANAGEMENT_OUTLOOK_OR_ESTIMATE', None}
    [segment] = [r for r in fields if r['kind']=='REPORTED_SEGMENT_CONTEXT_ONLY']
    assert (segment['observation']['value'],segment['observation']['currency'])==(12_500_000,'USD')
    assert segment['observation']['period_start']=='2026-07-01'
    assert segment['observation']['dimensions']=={'us-gaap:StatementBusinessSegmentsAxis':'ex:CloudMember'}
    assert economy(view)['relationships']==[]
    row, = _cited_filing_rows(dict(economic_context=economy(view)),
                             {'valuation_context':{'business_evidence_refs':[segment['ref_id']]}}, view)
    assert 'Cloud' in row.text and '12,500,000 USD' in row.text
    assert row.numeric_registry_keys==(segment['ref_id']+':fields.segment_revenue',)
    assert _cited_filing_rows(dict(economic_context=economy(view)),
                             {'valuation_context':{'business_evidence_refs':[]}},view)==[]


@pytest.mark.parametrize('old,new', [
    (b'>123</',b'>999</'), (b'2026-09-30',b'2025-09-30'),
    (b'StatementBusinessSegmentsAxis',b'StatementClassOfStockAxis'),
    (b'iso4217:USD',b'bad:USD'), (b'scale="6"',b'scale="600"'),
])
def test_unresolved_segment_amount_has_no_numeric_or_comparison_role(old,new):
    result=economy(source(RAW.replace(old,new)))
    assert not any(r['kind']=='REPORTED_SEGMENT_CONTEXT_ONLY' for r in result['observations'])
    assert not result['relationships']


def test_duplicate_or_conflicting_segment_occurrences_do_not_add():
    cell=RAW[RAW.index(b'<ix:nonfraction'):RAW.index(b'</ix:nonfraction>')+len(b'</ix:nonfraction>')]
    def amounts(extra):
        return [r for r in economy(source(RAW.replace(cell,cell+extra)))['observations'] if r['kind']=='REPORTED_SEGMENT_CONTEXT_ONLY']
    assert len(amounts(cell))==1
    assert amounts(cell.replace(b'12.5',b'17.5'))==[]


def test_equal_product_and_product_segment_intersection_keeps_one_value():
    context = RAW[RAW.index(b'<xbrli:context'):RAW.index(b'</xbrli:context>')+len(b'</xbrli:context>')]
    combined = context.replace(b'id="op"', b'id="both"').replace(b'</xbrli:segment>', (
        b'<xbrldi:explicitmember dimension="srt:ProductOrServiceAxis">ex:HostedProductMember</xbrldi:explicitmember>'
        b'</xbrli:segment>'))
    cell = RAW[RAW.index(b'<ix:nonfraction'):RAW.index(b'</ix:nonfraction>')+len(b'</ix:nonfraction>')]
    raw = RAW.replace(b'<html ', b'<html xmlns:srt="http://fasb.org/srt/2026" ').replace(
        context,context+combined).replace(cell,cell+cell.replace(b'contextref="op"',b'contextref="both"'))
    amounts = [r for r in economy(source(raw))['observations'] if r['kind']=='REPORTED_SEGMENT_CONTEXT_ONLY']
    assert len(amounts)==1 and len(amounts[0]['observation']['dimensions'])==1


def test_original_acquisition_selection_and_missing_capture(tmp_path):
    import hashlib
    sha=hashlib.sha256(RAW).hexdigest()
    (tmp_path/'raw.body').write_bytes(RAW)
    url='https://www.sec.gov/Archives/edgar/data/123/000000012326000001/q.htm'
    doc=dict(filing=FILING,artifact='raw.body',url=url)
    receipts=[dict(artifact='raw.body',raw_sha256=sha)]
    got=reported_filing_context(PLAN,dict(selected_filings=[FILING],documents=[doc]),tmp_path,receipts)
    assert got==source()['packet']['stocks'][0]['reported_filing_context']
    assert reported_filing_context(PLAN,dict(selected_filings=[],documents=[doc]),tmp_path,receipts)==[]
    with pytest.raises(ValueError,match='raw_receipt_hash'):
        reported_filing_context(PLAN,dict(selected_filings=[FILING],documents=[doc]),tmp_path,[dict(artifact='raw.body',raw_sha256='0'*64)])
    with pytest.raises(ValueError,match='SCOPE_DENIED'):
        reported_filing_context(PLAN,dict(selected_filings=[FILING],documents=[dict(doc,url=url.replace('/123/','/124/'))]),tmp_path,receipts)


def test_pass_a_needs_visible_archetype_parent_and_preserves_price_blindness():
    view=source(RAW.replace(b'</html>',b'<p>Our current price increased due to strong customer demand across all segments.</p></html>'))
    ref='canonical:earnings_comparison:example'
    final=dict(eligible_non_price_evidence=[dict(ref_id=ref)],source_use_projection={
        'source_permissions':[dict(ref_id=ref,allowed_uses=['PASS_A_ARCHETYPE'])]})
    assert pass_a_filing_context(view,final)
    assert 'current price' not in str(pass_a_filing_context(view,final))
    final['source_use_projection']['source_permissions'][0]['allowed_uses']=['CONTEXT']
    assert pass_a_filing_context(view,final)==[]
    view['selected_financial_owner']['bridge_receipt']={'scope':'issuer_business_only'}
    assert economy(view)['observations']==[]


def test_mismatched_registry_cannot_feed_model():
    view=source()
    segment=next(x for x in view['packet']['stocks'][0]['reported_filing_context'] if 'numeric_registry_entry' in x)
    segment['numeric_registry_entry']['value']+=1
    assert not any(r['kind']=='REPORTED_SEGMENT_CONTEXT_ONLY' for r in economy(view)['observations'])


def test_reported_eps_is_not_provider_ttm_or_a_price_grant():
    ref={'currency':'USD','direct':[dict(field='epsTTM',own_denominator_basis_resolved=False)]}
    row=dict(kind='REPORTED_ABSOLUTE_CONTEXT_ONLY',ref_id='eps-source',observation=dict(metric='diluted_eps',
        semantic='us-gaap:EarningsPerShareDiluted',unit='USD/shares',currency='USD',
        source_document_id='doc',period_start='2026-01-01',period_end='2026-09-30'))
    new_buyer_request_owner._link_reported_eps(ref,[row])
    assert ref['direct'][0]['reported_diluted_eps_context_refs']==['eps-source']
    assert ref['direct'][0]['period_equivalence'].startswith('NOT_ESTABLISHED')
    assert not ref['direct'][0]['own_denominator_basis_resolved']


def test_step2_companyfacts_fields_keep_original_context_consumers_and_units():
    occurrence = dict(accn=FILING['accessionNumber'], start='2026-07-01', end=FILING['reportDate'],
                      filed=FILING['filingDate'], form='10-Q', fy=2026, fp='Q3', val=3.25)
    raw = json.dumps(dict(cik=123, facts={'us-gaap':{'EarningsPerShareDiluted':{
        'units':{'USD/shares':[occurrence], 'USD':[occurrence]}}}})).encode()
    original, _ = _sec_context_fields(PLAN,FILING,raw,True)
    assert not original
    new, _ = _sec_context_fields(PLAN,FILING,raw,True,business_analysis_fields=True)
    good, = [r for r in new if r['context_eligible']]
    assert (good['metric'], good['value'], good['currency'], good['unit'], good['period_start']) == (
        'diluted_eps', 3.25, 'USD','USD/shares','2026-07-01')
    assert not good['direction_eligible'] and len(new)==2


def test_optional_unreadable_or_hidden_prose_never_supplies_an_observation():
    assert extract_filing(PLAN, FILING, 'q.htm', b'<![invalid [>') == ([], [])
    raw = b'<p style="display: none">Revenue increased primarily due to higher customer demand.</p>'
    assert select_observations(*extract_filing(PLAN, FILING, 'q.htm', raw)) == []


@pytest.mark.parametrize('title,expected',[
    ('Example (EX) Has Secured $32 Billion in Customer Commitments. Here is why', True),
    ('Governor to Break Ground on Example’s New Chip Plant',True),
    ('Example shares rise as Rival signs a supply contract',False),
    ('Example might sign a supply contract',False),
    ('Is Example a Buy After Rival Wins a Supply Contract?',False),
])
def test_news_is_a_subject_bound_followup(title,expected):
    assert operating_headline_lead(title,['Example','EX'])==expected


def test_market_session_direction_only_uses_displayed_index_returns():
    def item(label, value,block='indices',status='AVAILABLE'):
        return SimpleNamespace(block_id=block,status=status,label=label,
                               bindings=[SimpleNamespace(field_path='fields.return_pct',value=value)])
    plan=SimpleNamespace(items=[item('SPY',1),item('QQQ',-.5),item('IWM',0),item('VIX',-3,'macro'),item('X',1,status='UNAVAILABLE')])
    assert _session_index_line(plan)=='완료장 지수 흐름 · SPY 상승, QQQ 하락, IWM 보합'
    text='공시에서 고객 인도와 가동을 확인했다. '*35
    assert _sentence_lines(text).replace('\n',' ')==text
