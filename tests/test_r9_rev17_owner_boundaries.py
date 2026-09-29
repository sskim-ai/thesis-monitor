from copy import deepcopy
from datetime import date, datetime, timezone
import re

import pytest

from app.services.fpi_filing_document_graph import declared_nonfinancial_exhibit
from app.services.latest_published_fx import validate_context
from app.services.macro_source_time import publication_context
from app.services.sec_primary_inline_financial import extract, errors
from app.services.selected_financial_owner import select, validate
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_anomaly_scope import materialize_source_components
from app.services.unified_stock_owner import _technical
from test_r9_rev15_financial_owners import plan, filing, inline_html
from app.services.bounded_financial_acquisition import sec_base
from test_unified_stock_anomaly_scope import bars, bad


def fx(day='20260928'):
    return publication_context(provider='ecos', series='USDKRW', period=day,
        query_as_of=datetime(2026,9,29,6,tzinfo=timezone.utc),
        retrieved_at=datetime(2026,9,29,6,1,tzinfo=timezone.utc), response_bytes=b'official',
        cadence='provider_key_statistics', latest_verified=True, daily_required=True)


@pytest.mark.parametrize('day', ['20260928','20260929'])
def test_fx_latest_published_keeps_real_date(day):
    context = fx(day)
    assert validate_context(context, observation_date=context['observation_date'],
        response_hashes={context['response_sha256']}, query_as_of=context['query_as_of'])
    assert not context['direction_eligible']


@pytest.mark.parametrize('mutation', ['stale','latest','unproven','relabel','direction','query_as_cycle'])
def test_fx_fail_closed(mutation):
    context = fx()
    hashes = {context['response_sha256']}
    if mutation == 'stale':
        hashes = {'unrelated'}
    if mutation == 'latest':
        context['latest_available_at_query_time'] = False
    if mutation == 'unproven':
        context['freshness_state'] = 'PUBLICATION_CURRENTNESS_UNPROVEN'
    if mutation == 'relabel':
        context['observation_date'] = '2026-09-29'
    if mutation == 'direction':
        context['direction_eligible'] = True
    if mutation == 'query_as_cycle':
        context['observation_period'] = context['query_as_of']
    assert not validate_context(context, observation_date=context['observation_date'],
        response_hashes=hashes, query_as_of=context['query_as_of'])


def test_fx_renderer_uses_observation_not_equity_date():
    from test_r9_rev6_display_and_source_time import source, plan
    from app.services.market_display_plan import render_display_plan
    s = source('kr')
    s['session']['latest_completed_regular_session_date'] = '2026-09-28'
    value = render_display_plan(plan(s,'kr'),s,'시장 판단')
    assert '2026-09-25 관측' in value
    usd = next(f for f in s['fact_catalog'] if f['fields'].get('series_code')=='USDKRW')
    usd['fields']['publication_context']['direction_eligible']=True
    assert plan(s,'kr').items[-1].status=='UNAVAILABLE'


LABELS = [
    *(f'Certification by Principal {officer} Officer Pursuant to Section {section} of the Sarbanes-Oxley Act of 2002'
        for officer in ('Executive','Financial') for section in ('302','906')),
    'Description of Securities',
    'Equity Commitment Letter between the Registrant and Fictional Corp., dated May 5, 2025']


@pytest.mark.parametrize('label', LABELS)
def test_exact_annual_exhibit_routing(label):
    assert declared_nonfinancial_exhibit([dict(label=label)], filing('20-F'))
    assert not declared_nonfinancial_exhibit([dict(label=label)], filing('6-K'))


@pytest.mark.parametrize('label', ['Financial Information','Financial Statements',
    'Results of Operations','unknown','Description of Securities and Financial Statements',
    'Certification by Principal Financial Officer','Commitment Letter earnings results'])
def test_unknown_mixed_financial_labels_never_discarded(label):
    assert not declared_nonfinancial_exhibit([dict(label=label)], filing('20-F'))


def test_conflicting_label_no_nonfinancial_authority():
    assert not declared_nonfinancial_exhibit([dict(label=LABELS[0]),dict(label='Financial Statements')],filing('20-F'))


def split_inline(**kwargs):
    p, f = plan(), filing('6-K')
    html = inline_html(concept='ProfitLossFromOperatingActivities', **kwargs)
    resources = re.search(r'<ix:resources>.*?</ix:resources>',html,re.S)[0]
    start = html[:html.index('<h1>')]
    primary = (start + resources + '<a href="attachment.htm">Consolidated Financial Statements</a></html>').encode()
    attachment = html.replace(resources, '').replace('scale="3"', 'decimals="-3" scale="3"').encode()
    document = dict(raw=primary, url=sec_base(p,f)+f['primaryDocument'], filing=f)
    return dict(raw=attachment,issuer_cik=p['issuer'],filing=f,source_url=sec_base(p,f)+'attachment.htm',
                context_documents=[document])


def test_same_accession_context_unit_owned_half_year():
    args = split_inline(start='2025-01-01',end='2025-06-30',sign='-')
    rows = extract(**args)['occurrences']
    assert len(rows) == 2 and rows[0]['value'] == -120000
    assert rows[0]['field'] == 'operating_income' and rows[0]['period_scope'] == 'half-year'
    assert rows[0]['source_cell']['decimals'] == '-3'
    assert rows[0]['source_cell']['context_source']['source_payload_sha256']
    assert rows[0]['source_cell']['unit_source']['source_payload_sha256']
    assert not errors(rows[0],date(2026,9,29))


@pytest.mark.parametrize('mutation', ['accession','link','duplicate','unit','dimension','issuer','accuracy'])
def test_cross_document_context_negatives(mutation):
    args = split_inline()
    source = args['context_documents'][0]
    if mutation == 'accession':
        source['filing'] = filing('6-K',2)
    elif mutation == 'link':
        source['raw'] = source['raw'].replace(b'attachment.htm',b'other.htm')
    elif mutation == 'duplicate':
        args['context_documents'].append(deepcopy(source))
    elif mutation == 'unit':
        source['raw'] = source['raw'].replace(b'iso4217:TWD',b'iso4217:shares')
    elif mutation == 'dimension':
        source['raw'] = source['raw'].replace(b'</xbrli:entity>',b'<xbrli:segment/></xbrli:entity>')
    elif mutation == 'issuer':
        args['issuer_cik'] = '999'
    else:
        args['raw'] = args['raw'].replace(b'decimals="-3"',b'decimals="bogus"')
    try:
        value = extract(**args)
    except ValueError:
        assert mutation in {'accession','link','issuer'}
    else:
        assert not value['occurrences'] and value['denials']


def test_selected_owner_binds_projection_and_incomplete_state():
    p = plan()
    projection = dict(financial_field_completeness=dict(partial_field_consumption_allowed=False))
    envelope = select(plan=p,acquisition={},projection=projection,facts=[])
    assert envelope['field_completeness']['partial_field_consumption_allowed'] is False
    assert validate(envelope,projection=projection,facts=[],bridge=None) == envelope
    with pytest.raises(ValueError,match='binding_mismatch'):
        validate(envelope,projection={},facts=[],bridge=None)


def bridge_fixture():
    bridge = dict(status='PASS',legal_issuer_id='legal:test',ISSUER_BUSINESS_EVIDENCE_ELIGIBLE=True,
        SECURITY_PER_SHARE_BRIDGE_ELIGIBLE=False,SECURITY_VALUATION_BRIDGE_ELIGIBLE=False,
        security_valuation_transfer=False,scope='issuer_business_only')
    bridge['receipt_sha256'] = digest(bridge)
    origin = dict(status='PASS',projection={'native':'opendart'},input_hashes={'acquisition':'a'*64})
    facts = [dict(fact_id='f1',issuer_business_bridge=dict(bridge_receipt_sha256=bridge['receipt_sha256'],
        source_result_sha256=digest(origin),scope='issuer_business_only',security_valuation_transfer=False))]
    return bridge,origin,facts


def test_bridge_ignores_unselected_empty_sec():
    bridge,origin,facts = bridge_fixture()
    envelope = select(plan=plan(),acquisition={},projection={'empty_sec':True},
        facts=facts,bridge=bridge,origin=origin)
    assert envelope['owner_type']=='issuer_business_bridge'
    assert envelope['field_completeness']['partial_field_consumption_allowed']
    assert envelope['unselected_owner_states'][0]['state']=='UNSELECTED'
    validate(envelope,projection=origin['projection'],facts=facts,bridge=bridge)


@pytest.mark.parametrize('mutation',['invalid_bridge','legal','incomplete','valuation','per_share','fact_transfer'])
def test_bridge_boundary_denials(mutation):
    bridge,origin,facts = bridge_fixture()
    if mutation=='invalid_bridge':
        bridge['status']='FAIL'
    if mutation=='legal':
        bridge['legal_issuer_id']=''
    if mutation=='incomplete':
        origin['status']='BLOCKED'
    if mutation=='valuation':
        bridge['SECURITY_VALUATION_BRIDGE_ELIGIBLE']=True
    if mutation=='per_share':
        bridge['SECURITY_PER_SHARE_BRIDGE_ELIGIBLE']=True
    if mutation=='fact_transfer':
        facts[0]['issuer_business_bridge']['security_valuation_transfer']=True
    with pytest.raises(ValueError):
        select(plan=plan(),acquisition={},projection={},facts=facts,bridge=bridge,origin=origin)


def technical_fixture():
    roles = {f'adjusted_{tf}': bars() for tf in ('daily','weekly','monthly')}
    roles['unadjusted_weekly_valuation'] = bars()
    bad(roles['adjusted_daily'],-1)
    bad(roles['adjusted_weekly'],-1)
    args = dict(ticker='FICTIONAL',market='us',cutoff=date(2026,9,25),observed_at='2026-09-26T07:54:00+00:00')
    return roles,args,materialize_source_components(roles=roles,**args)


def test_invalid_ohlc_current_surface_parity_not_historical():
    roles,args,c = technical_fixture()
    original = deepcopy(roles)
    context,_ = _technical(c,roles,**args)
    assert not context.features.daily.facts and not context.features.weekly.facts
    assert c['features']['daily']['source_invalid_rows']
    assert c['current_price'] is None and c['mandatory_current_price_failure']
    assert c['historical_technical_inventory']['current_authority'] is False
    assert c['historical_technical_inventory']['facts']['daily']
    assert roles==original


def test_historical_injected_into_effective_denied():
    roles,args,c = technical_fixture()
    c['features']['daily']['facts'] = c['historical_technical_inventory']['facts']['daily']
    with pytest.raises(ValueError,match='historical_features'):
        _technical(c,roles,**args)
