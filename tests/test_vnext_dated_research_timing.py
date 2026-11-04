from copy import deepcopy
import pytest

from app.services import vnext_dated_research_timing as t
from app.services import vnext_balanced_stage_review as stage
from app.services.vnext_dated_technical_owner import DatedTechnicalOwner
from test_vnext_dated_technical_owner import source, owner, kw
from test_vnext_balanced_research_v2 import case


def setup(monkeypatch, code='UNSEEN', market='US', enabled=True, clock=lambda:0):
    p, _, registry = case()
    values = [source(code=code,market=market,tf=tf,n=80) for tf in ('daily','weekly','monthly')]
    security = values[0]['security']
    p['base']['public_security'] = security
    p['base']['as_of'] = kw(values[0])['cutoff']
    parents = {v['timeframe']:owner(monkeypatch,[v],clock=clock).sources[v['timeframe']] for v in values}
    parent = DatedTechnicalOwner(parents,parser_root=None,parser_pins=None,enabled=True,clock=clock)
    o = t.DatedResearchTimingOwner(parent,enabled=enabled,clock=clock)
    if not enabled:return o,p,registry
    packet = t.attach(p,timing_owner=o,registry=registry,cutoff=p['base']['as_of'])
    citations=[]
    for tf in ('daily','weekly','monthly'):
        for metric in (('close','rsi_14') if tf=='daily' else ('close',)):
            r=next(r for r in packet['technical']['facts'] if r['timeframe']==tf and r['fact']['semantic']==metric)
            f=r['fact'];citations.append(dict(ref=r['ref'],timeframe=tf,period_end=r['period_end'],
                metric=metric,value=str(f['value']),unit=f['unit'],formula=f['formula'],
                source_sha256=r['source_sha256'],interpretation='과거 기준 관측이며 방향을 확정하지 않는다.'))
    value=dict(contract=t.CONTRACT,security_id=security['canonical_security_id'],state='MIXED',confidence='LOW',
        summary='기간별 근거를 비교한 제한적 연구 판단이다.',citations=citations,
        periods=[dict(timeframe=tf,as_of=packet['technical']['roles'][tf]['as_of'],state='MIXED',
            refs=[c['ref'] for c in citations if c['timeframe']==tf],reasoning='불확실성을 유지한다.') for tf in ('daily','weekly','monthly')],
        conflicts='독립적인 보강으로 보지 않는다.',uncertainty='통화는 미검증이다.',
        change_condition='새로운 적격 자료가 나오면 다시 검토한다.',economic_separation='사업 판단은 별개다.',
        current_price_qualified=False,investment_axes_changed=False,no_send=True)
    return o,p,registry,packet,value


def validate(args):
    o,p,r,packet,value=args
    return t.validate_and_render(value,packet,registry=r,timing_owner=o,economic_loader=lambda:p)


@pytest.mark.parametrize('market,code',[('KR','UNSEEN_KR'),('US','UNSEEN_ORDINARY'),('US','UNSEEN_ADS'),('US','UNSEEN_FINANCIAL')])
def test_generic_real_owner_contract_and_exact_citations(monkeypatch,market,code):
    args=setup(monkeypatch,code,market);checked=validate(args)
    assert checked['citations_verified']==4 and not checked['formal_timing']
    assert not checked['current_price'] and not checked['investment_axes_changed']
    assert 'NOT_CURRENT' in checked['rendered'] and 'NOT_QUALIFIED' in checked['rendered']
    assert stage._engine(stage.DATED_TIMING) is t
    assert stage._engine(stage.POLICY_V2) is not t
    prompt=stage.prompt(args[3],'BLIND',knowledge={},registry=args[2],version=stage.DATED_TIMING)
    assert 'NEW_ACCEPTED_BLIND_ONLY' not in prompt
    assert 'past model results' in prompt


@pytest.mark.parametrize('change,error',[
    ('value','numeric_source_binding'),('unit','numeric_source_binding'),('formula','numeric_source_binding'),
    ('source_sha256','numeric_source_binding'),('period_end','numeric_source_binding'),
    ('timeframe','numeric_source_binding'),('ref','unissued_fact'),('metric','numeric_source_binding'),
    ('only_one','two_distinct'),('duplicate','two_distinct'),('same_metric','two_distinct_metrics'),
    ('wrong_period','period_binding'),('cross_period_ref','period_reference'),('security','security'),
    ('currency_prose','forbidden_prose'),('price_prose','forbidden_prose'),('order_prose','forbidden_prose'),
    ('numeric_prose','forbidden_prose'),('confidence','confidence'),('missing_month','all_periods'),
])
def test_numerical_and_axis_forgery_rejected(monkeypatch,change,error):
    a=list(setup(monkeypatch));v=a[-1];c=v['citations'][0]
    if change in ('value','unit','formula','source_sha256','period_end','timeframe','ref','metric'):
        c[change]=['fake'] if change=='source_sha256' else 'fake'
        if change=='timeframe':c[change]='monthly'
    elif change=='only_one':v['citations']=v['citations'][:1]
    elif change=='duplicate':v['citations'].append(deepcopy(c))
    elif change=='same_metric':v['citations']=[x for x in v['citations'] if x['metric']=='close']
    elif change=='wrong_period':v['periods'][0]['as_of']='2026-10-29'
    elif change=='cross_period_ref':v['periods'][1]['refs']=[c['ref']]
    elif change=='security':v['security_id']='fake'
    elif change=='currency_prose':v['summary']='USD 기준이다.'
    elif change=='price_prose':v['summary']='목표가를 정한다.'
    elif change=='order_prose':v['summary']='BUY now'
    elif change=='numeric_prose':v['summary']='추세는 100 이다.'
    elif change=='confidence':v['state']='UNRESOLVED'
    else:v['periods']=v['periods'][:2]
    with pytest.raises(ValueError,match=error):validate(a)


def test_default_off_and_receipt_registry_lifetime(monkeypatch):
    o,p,r=setup(monkeypatch,enabled=False)
    args=dict(security=p['base']['public_security'],cutoff=p['base']['as_of'])
    with pytest.raises(ValueError,match='disabled'):o.issue(**args)
    now=[0];o,p,r,packet,value=setup(monkeypatch,clock=lambda:now[0]);receipt=o.issue(**args)
    assert o.issue(**args) is receipt
    assert o.consume(receipt,**args)==packet['technical']
    with pytest.raises(ValueError,match='wrong_registry'):o.consume(deepcopy(receipt),**args)
    other=t.DatedResearchTimingOwner(o.parent,enabled=True,clock=lambda:now[0])
    with pytest.raises(ValueError,match='wrong_registry'):other.consume(receipt,**args)
    now[0]=1801
    with pytest.raises(ValueError,match='expired'):o.issue(**args)


@pytest.mark.parametrize('use',t.PROHIBITED)
def test_no_old_or_directional_use(monkeypatch,use):
    o,p,r,packet,value=setup(monkeypatch)
    args=dict(security=p['base']['public_security'],cutoff=p['base']['as_of'])
    with pytest.raises(ValueError,match='consumer_or_use'):o.issue(**args,use=use)
    with pytest.raises(ValueError,match='consumer_or_use'):o.parent.issue(**args,timeframe='daily',use=t.PURPOSE)


@pytest.mark.parametrize('target',['child','parent','serialized','changed_receipt','economic_packet'])
def test_live_authority_and_source_must_remain_valid(monkeypatch,target):
    a=list(setup(monkeypatch));o,p,_,packet,_=a
    if target=='child':o.revoke()
    elif target=='parent':o.parent.revoke()
    elif target=='serialized':a[0]=deepcopy(packet['technical'])
    elif target=='changed_receipt':o.issue(security=p['base']['public_security'],cutoff=p['base']['as_of'])['issuer']='forged'
    else:p['base']['run_id']='forged-generation'
    with pytest.raises(ValueError):validate(a)


def test_original_stage_controller_and_new_only_outbox(monkeypatch):
    import time
    from contextlib import nullcontext
    from app.services.vnext_research_store import digest
    from app.services.vnext_dated_timing_controller import DatedTimingController
    from test_vnext_balanced_stage_review import MemoryController
    class MemoryTiming(DatedTimingController):
        __init__=MemoryController.__init__
        _read=MemoryController._read
        _append=MemoryController._append
    o,p,r,packet,value=setup(monkeypatch);ctrl=MemoryTiming();calls=[]
    inputs=dict(timing_owner=o,economic_loader=lambda:p)
    def run(name,prior=None,bad=False):
        def invoke(req,text,deadline):
            calls.append(name);out=deepcopy(value)
            if bad:out['citations'][0]['value']='999'
            checked=t.validate_and_render(out,packet,registry=r,**inputs)
            now=time.time()
            e=dict(stage=name,status='VALIDATED',exit=0,attempt=1,retry=0,
                runtime=dict(verified=True,session='SYNTHETIC_'+name),model='gpt-6-astra',effort='xhigh',
                packet_sha=digest(packet),prompt_sha=digest(text.encode()),schema_sha=digest(t.schema()),
                output_sha=digest(out),started=now,ended=now,deadline=deadline,
                stage_contract=stage.CONTRACT,prompt_version=stage.DATED_TIMING,invocation_id=req['invocation_id'],
                request_sha=digest(req),approved_request_sha=digest(req))
            return dict(output=out,validation=checked,execution=e)
        return ctrl.run_stage(invocation_id='TEST_ONLY_'+name,account='TEST_ONLY',packet=packet,stage=name,
            version=stage.DATED_TIMING,knowledge={},registry=r,source_loader=lambda:packet,
            approval=lambda req:True,account_lease=nullcontext,invoke=invoke,prior=prior,**inputs)
    with pytest.raises(ValueError,match='numeric_source_binding'):run('BLIND',bad=True)
    with pytest.raises(ValueError,match='already_attempted'):run('BLIND')
    assert calls==['BLIND'] and not any('accepted' in key for key in ctrl.rows)
    ctrl=MemoryTiming();calls=[]
    blind=run('BLIND');adj=run('ADJUDICATION',blind)
    reviewed=stage.StageReviewOwner(blind,adj,enabled=True)
    result=ctrl.finalize_timing(packet=packet,owner=reviewed,timing_owner=o)
    assert ctrl.finalize_timing(packet=packet,owner=reviewed,timing_owner=o)==result
    assert sum(k.startswith('dated-timing-outbox-') for k in ctrl.rows)==1
    assert not any(k.startswith('daily-outbox-') for k in ctrl.rows)
    assert calls==['BLIND','ADJUDICATION'] and not result['formal_timing']
    o.revoke()
    with pytest.raises(ValueError,match='revoked'):
        ctrl.finalize_timing(packet=packet,owner=reviewed,timing_owner=o)
