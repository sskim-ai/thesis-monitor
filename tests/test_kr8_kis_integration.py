from copy import deepcopy
import time

import httpx
import pytest

from scripts import kr8_kis_integration as k
from scripts.kis_estimate_capability_probe import Credentials, ProbeStop
from tests.test_kis_current_fy1_owner import ASOF, ev, eps, price_inputs, reseal
from tests.test_kis_exact_action_guard import docs


def plan():
    return k.build_plan(generation='fictional-kr8', as_of=ASOF,
        securities={c:dict(ticker=c,exchange='KRX',currency='KRW',canonical_security_id='kr:'+c,
            corp_code='00123456') for c in k.SUBJECTS}, static_hashes={})


def keyed_eps(code, value='30'):
    source = eps(value)
    security = dict(source['security'], request_code=code, short_code=code,
        provider_product_number='00000A'+code, estimate_sht_cd='A'+code)
    return reseal(source, security_code=code, security=security)


def rows(eligible):
    result=[]
    for code in k.SUBJECTS:
        e = keyed_eps(code) if code in eligible else {'state':'UNAVAILABLE_NO_KIS_RESEARCH_ESTIMATE','value':None}
        close = None
        if code in eligible:
            i=price_inputs()
            i['eps']=e
            i['security']['ticker']=code
            i['receipt']['request']['params']=k.price.price_params(code)
            close=k.price.price_receipt(**i)
        result.append(dict(security_code=code,eps=e,price=close))
    return result


@pytest.mark.parametrize('count', [0,1,7,8])
def test_no_prior_seven_subject_eligibility_assumption(count):
    p=k.action_plan(rows(set(k.SUBJECTS[:count])), docs())
    assert len(p['requests'])==count*6
    assert p['maximum_data_calls']==60
    assert all(r['params']['SHT_CD']==r['subject'] for r in p['requests'])
    assert '003690' in {r['subject'] for r in k.action_plan(rows(set(k.SUBJECTS)), docs())['requests']}


def test_missing_price_and_cross_subject_eps_denied():
    r=rows(set(k.SUBJECTS))
    r[0]['price']=None
    with pytest.raises(ValueError,match='ELIGIBLE_PRICE'):
        k.action_plan(r,docs())
    r=rows(set(k.SUBJECTS))
    r[0]['eps']=r[1]['eps']
    with pytest.raises(ValueError,match='IDENTITY'):
        k.action_plan(r,docs())


@pytest.mark.parametrize('code', ['IBM','000660.KS','00066',''])
def test_foreign_or_ambiguous_security_request_never_reaches_http(tmp_path,code):
    calls=[]
    probe=k.FreshProbe(tmp_path,Credentials('fake-key','fake-secret'),
        httpx.Client(transport=httpx.MockTransport(lambda r:calls.append(r))),plan=plan())
    probe.token='fake-token'
    probe.last_finished=time.monotonic()-2
    with pytest.raises(ProbeStop,match='REQUEST_SCOPE_GAP'):
        probe.fetch(code,'estimate')
    assert not calls and probe.data_count==0


def test_price_requires_positive_same_security_qualified_eps(tmp_path):
    probe=k.FreshProbe(tmp_path,Credentials('fake-key','fake-secret'),None,plan=plan())
    probe.token='fake-token'
    for e in (None,keyed_eps('005930'),keyed_eps('000660','0'),keyed_eps('000660','-10')):
        with pytest.raises(ProbeStop,match='PRICE_EPS_ADMISSION'):
            probe.fetch('000660','price',eps=e)
    assert probe.data_count==0


def inventory():
    body=ev(dict(status='000',page_no=1,total_page=1,total_count=1,list=[dict(
        stock_code='000660',corp_code='00123456',rcept_dt='20260315',report_nm='annual',rcept_no='20260315000001')]))
    receipt=dict(http_status=200,raw_sha256=body.sha256,
        request=dict(path='/api/list.json',params=dict(corp_code='00123456')))
    return body,receipt


def test_fiscal_projection_preserves_all_values_except_date_representation():
    body,r=inventory()
    projected,proof=k.normalized_inventory(body,r,code='000660',corp_code='00123456')
    expected=deepcopy(body.payload())
    expected['list'][0]['rcept_dt']='2026-03-15'
    assert projected.payload()==expected and proof['raw_sha256']==body.sha256


@pytest.mark.parametrize('change', ['hash','status','path','corp','pages','security'])
def test_fiscal_projection_rejects_unbound_incomplete_source(change):
    body,r=inventory()
    if change in {'pages','security'}:
        payload=body.payload()
        if change=='pages':
            payload['total_page']=2
        else:
            payload['list'][0]['stock_code']='005930'
        body=ev(payload)
        r['raw_sha256']=body.sha256
    elif change=='hash':
        r['raw_sha256']='0'*64
    elif change=='status':
        r['http_status']=302
    elif change=='path':
        r['request']['path']='/api/company.json'
    else:
        r['request']['params']['corp_code']='99999999'
    with pytest.raises(ValueError):
        k.normalized_inventory(body,r,code='000660',corp_code='00123456')
