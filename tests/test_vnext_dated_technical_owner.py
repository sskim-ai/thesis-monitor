"""Synthetic capability/consumer regressions, never real issuer acceptance."""
from copy import deepcopy
from datetime import date
import pytest

from app.services import vnext_dated_technical_owner as h
from app.services.market_session import _exchange_calendar
from app.services.vnext_optional_fy1_research import attach,prompt


def source(market='US',code='UNSEEN',tf='daily',n=260):
    security=dict(ticker=code,country=market,exchange='NASDAQ' if market=='US' else 'KRX',
                  canonical_security_id='security-'+code,canonical_company_id='issuer-'+code)
    cal=_exchange_calendar('XNYS' if market=='US' else 'XKRX')
    days=[str(x.date()) for x in cal.sessions_in_range('2023-01-03','2026-10-29')]
    if tf!='daily':
        grouped={}
        for day in days:grouped.setdefault(h.bounds(date.fromisoformat(day),tf)[0],day)
        days=list(grouped.values())
    rows=[dict(date=d,open=10.,high=12.,low=9.,close=11.,volume=100.) for d in days[-n:]]
    return dict(security=security,timeframe=tf,rows=rows,last_raw_date=rows[-1]['date'],
        source_generation='TEST_ONLY',source_sha256='a'*64,receipt_sha256='b'*64,page_sha256=['c'*64],
        requested_source_session='2026-10-29',captured_at='2026-10-30T01:00:00+00:00',
        parser_sha256='d'*64,basis='adjusted_close',source_kind='NATIVE',source_exhausted=False)


def owner(monkeypatch,values,*,enabled=True,clock=lambda:0):
    parents=[]
    for value in values:
        parent=object.__new__(h.LegacyChartReplay)
        def replay(security,timeframe,value=value):
            if security!=value['security'] or timeframe!=value['timeframe']:
                raise ValueError('history_security_binding')
            return deepcopy(value)
        monkeypatch.setattr(parent,'replay',replay)
        parents.append(parent)
    return h.DatedTechnicalOwner({values[0]['timeframe']:parents},parser_root=None,parser_pins=None,enabled=enabled,clock=clock)


def kw(s):
    return dict(security=s['security'],timeframe=s['timeframe'],cutoff='2026-10-30T06:00:00+00:00')


@pytest.mark.parametrize('market',['US','KR'])
@pytest.mark.parametrize('tf',['daily','weekly','monthly'])
def test_independent_native_periods_keep_dates_and_purpose(monkeypatch,market,tf):
    s=source(market,tf=tf);o=owner(monkeypatch,[s]);r=o.issue(**kw(s))
    assert o.consume(r,**kw(s))==r
    assert not r['current_price'] and not r['economic_direction'] and not r['send']
    assert r['source_kind']=='NATIVE' and r['features']['facts']
    assert r['effective_analysis_as_of']<='2026-10-29'
    assert 'STRICT_NATIVE' in r['prohibited_uses']


@pytest.mark.parametrize('code',['UNSEEN_US','NEW_ADS','NEW_BANK','NEW_CYCLICAL'])
def test_equivalent_unseen_identity_has_equivalent_behavior(monkeypatch,code):
    s=source(code=code);r=owner(monkeypatch,[s]).issue(**kw(s))
    assert len(r['rows'])==259
    assert {f['semantic'] for f in r['features']['facts']} >= {'sma_200','return_252'}


def test_terminal_anomaly_remains_raw_and_prior_only(monkeypatch):
    s=source(n=100);s['rows'][-1]['close']=8;before=deepcopy(s)
    r=owner(monkeypatch,[s]).issue(**kw(s))
    assert len(r['rows'])==99 and r['effective_analysis_as_of']=='2026-10-28'
    assert s==before and not r['current_price']
    assert 'sma_100' not in {f['semantic'] for f in r['features']['facts']}


@pytest.mark.parametrize('count',[20,60,100,200,252,253])
def test_indicator_minima_count_actual_admitted_rows(monkeypatch,count):
    s=source(n=count+1);r=owner(monkeypatch,[s]).issue(**kw(s))
    assert len(r['rows'])==count
    assert all(f['minimum_history']<=count for f in r['features']['facts'])
    assert ('return_252' in {f['semantic'] for f in r['features']['facts']})==(count>=253)


@pytest.mark.parametrize('change',['gap','ohlc','basis','volume'])
def test_internal_defect_limits_only_contiguous_suffix(monkeypatch,change):
    s=source(n=100)
    if change=='gap':s['rows'].pop(-10)
    elif change=='ohlc':s['rows'][-10]['low']=13
    elif change=='basis':s['rows'][-10]['price_basis']='unadjusted'
    else:
        s['rows'][-10]['volume']=float('nan')
        with pytest.raises(ValueError,match='JSON compliant'):
            owner(monkeypatch,[s]).issue(**kw(s))
        return
    r=owner(monkeypatch,[s]).issue(**kw(s))
    assert len(r['rows'])==8


@pytest.mark.parametrize('use',h.PROHIBITED+['CONTEXT_RECEIPT'])
def test_purpose_escalation_rejected(monkeypatch,use):
    s=source();o=owner(monkeypatch,[s])
    with pytest.raises(ValueError,match='consumer_or_use'):o.issue(**kw(s),use=use)


def test_default_off_revocation_expiry_and_live_identity(monkeypatch):
    s=source();o=owner(monkeypatch,[s],enabled=False)
    with pytest.raises(ValueError,match='disabled'):o.issue(**kw(s))
    now=[0];o=owner(monkeypatch,[s],clock=lambda:now[0]);r=o.issue(**kw(s))
    assert o.issue(**kw(s)) is r
    with pytest.raises(ValueError,match='unissued'):o.consume(deepcopy(r),**kw(s))
    other=owner(monkeypatch,[s])
    with pytest.raises(ValueError,match='unissued'):other.consume(r,**kw(s))
    now[0]=601
    with pytest.raises(ValueError,match='expired'):o.consume(r,**kw(s))
    other.revoke()
    with pytest.raises(ValueError,match='revoked'):other.issue(**kw(s))


def test_source_mutation_does_not_reissue_same_invocation(monkeypatch):
    s=source();o=owner(monkeypatch,[s]);o.issue(**kw(s));s['source_generation']='altered'
    with pytest.raises(ValueError,match='source_changed'):o.issue(**kw(s))


def test_changed_overlap_not_silently_overwritten(monkeypatch):
    s=source(n=100);new=deepcopy(s);new['captured_at']='2026-10-30T02:00:00+00:00';new['rows'][-3]['close']=10
    r=owner(monkeypatch,[s,new]).issue(**kw(s))
    assert r['conflicts'][0]['reason']=='REVISED_OVERLAP' and r['rows'][-2]['close']==11


def test_current_ohlc_pass_does_not_certify_rth(monkeypatch):
    s=source(n=100);r=owner(monkeypatch,[s]).issue(**kw(s))
    assert r['rows'][-1]['date']=='2026-10-28' and r['current_price'] is False


def test_wrong_security_future_capture_and_public_json_rejected(monkeypatch):
    s=source();o=owner(monkeypatch,[s]);wrong=kw(s);wrong['security']=dict(s['security'],ticker='OTHER')
    with pytest.raises(ValueError,match='security'):o.issue(**wrong)
    with pytest.raises(ValueError,match='future'):o.issue(**dict(kw(s),cutoff='2026-10-29T00:00:00+00:00'))
    with pytest.raises(ValueError,match='backend_sources'):h.DatedTechnicalOwner([s],parser_root=None,parser_pins=None,enabled=True)


def test_existing_research_attach_requires_live_owner_and_pins_whole_input(monkeypatch):
    s=source(n=100);o=owner(monkeypatch,[s]);base=dict(public_security=s['security'],as_of=kw(s)['cutoff'])
    original=attach(base);packet=attach(base,technical_owner=o)
    assert 'dated_technical_scopes' not in original and packet['base']==base
    assert packet['numeric_reference_catalog'] and all(r['catalog_id'].startswith('t') for r in packet['numeric_reference_catalog'])
    assert packet==attach(base,technical_owner=o)
    with pytest.raises(ValueError,match='live_owner'):attach(base,technical_owner=packet)
    o.revoke()
    with pytest.raises(ValueError,match='revoked'):attach(base,technical_owner=o)


def test_prompt_table_retains_each_feature_definition_and_proof_binding(monkeypatch):
    from app.services.vnext_optional_fy1_research import _prompt_technical_scopes
    s=source();o=owner(monkeypatch,[s]);packet=attach(dict(public_security=s['security'],as_of=kw(s)['cutoff']),technical_owner=o)
    scope=packet['dated_technical_scopes'][0];view=_prompt_technical_scopes([scope])[0]
    assert view['receipt_sha256']==scope['receipt_sha256']
    assert view['prohibited_uses']==scope['prohibited_uses']
    for fact,row in zip(scope['features']['facts'],view['feature_definitions'],strict=True):
        rebuilt=dict(zip(view['feature_definition_columns'],row,strict=True))
        assert all(rebuilt[k]==fact[k] for k in view['feature_definition_columns'][:-1])
        if rebuilt['symbolic_value'] is not None:assert rebuilt['symbolic_value']==fact['value']


def test_actual_balanced_validator_consumes_dated_number_not_direction(monkeypatch):
    from test_vnext_balanced_research_v2 import case
    from app.services import vnext_balanced_research_v2 as engine
    p,value,registry=case()
    s=source(n=260);s['security']=deepcopy(p['base']['public_security'])
    p['base']['as_of']=kw(s)['cutoff'];o=owner(monkeypatch,[s])
    packet=attach(p['base'],technical_owner=o)
    number=next(r for r in packet['numeric_reference_catalog'] if r['metric']=='sma_200')
    value['summary']+=' Dated technical reference {{numeric:history}}.'
    value['numeric_fact_refs'].append(dict(ref_id='history',catalog_id=number['catalog_id'],text_ref='summary'))
    checked=engine.validate_and_render(value,packet,registry=registry,technical_owner=o)
    assert checked['balanced']['overall']['stance']=='NOT_ISSUED'
    assert checked['dated_reference_occurrences']==1
    bad=deepcopy(value);bad['valuation_evidence_refs']=[number['catalog_id']]
    with pytest.raises(ValueError):engine.validate_and_render(bad,packet,registry=registry,technical_owner=o)
    o.revoke()
    with pytest.raises(ValueError,match='revoked'):
        engine.validate_and_render(value,packet,registry=registry,technical_owner=o)


@pytest.mark.parametrize('slot',['valuation_expectations','provisional_business_signal'])
def test_dated_number_cannot_become_economic_or_valuation_text(monkeypatch,slot):
    from test_vnext_balanced_research_v2 import case
    from app.services import vnext_balanced_research_v2 as engine
    p,value,registry=case();s=source();s['security']=deepcopy(p['base']['public_security'])
    p['base']['as_of']=kw(s)['cutoff'];o=owner(monkeypatch,[s]);packet=attach(p['base'],technical_owner=o)
    value[slot]+=' {{numeric:history}}'
    value['numeric_fact_refs'].append(dict(ref_id='history',catalog_id=packet['numeric_reference_catalog'][0]['catalog_id'],text_ref=slot))
    with pytest.raises(ValueError,match='dated_technical_wrong_consumer_slot'):
        engine.validate_and_render(value,packet,registry=registry,technical_owner=o)
