"""Consume bytes produced by the real Analyst handler in a separate process.

TEST_ONLY receipt consumption is not a live root or a current registration.
"""
import asyncio
from copy import deepcopy
from datetime import datetime,timedelta,timezone
import hmac,json,os
from pathlib import Path
import httpx
import pytest
from app.config import Settings
from app.services import native_source_v2 as v2
from app.services import native_service_enrollment as enrollment
from app.services import ohlcv_client as cli
from app.services.unified_snapshot_contract import encoded
from app.services.packet_owned_technical_context_service import load_packet_owned_technical_context
from app.services.cross_market_decision_engine_service import build_decision_evidence_packet,compact_ai_context
from app.services.us_price_structure_selective_rollout_service import build_us_price_structure_rollout_decision

KEY=b'C21V synthetic-only published fixture key'
NOW=datetime(2026,11,8,14,30,tzinfo=timezone.utc)


def harness(monkeypatch,tmp_path,market='us',fault=None):
    rows=json.loads((Path(os.environ['C21V_EVIDENCE'])/'ACTUAL_SERVICE_MOCK_RESPONSES.json').read_text())
    wire=deepcopy(next(r for r in rows if r['symbol']==('CORZ' if market=='us' else '047810')))
    read=v2.NativeReadV2(role=market+'-daily',symbol=wire['symbol'],market=market,
        security_id='SYNTHETIC:'+market,issuer_id='SYNTHETIC-ISSUER:'+market,
        exchange=json.loads(wire['body'])['resolved_symbol']['exchange'],currency='USD' if market=='us' else 'KRW',
        session='2026-11-06',count=300,indicator_limit=5,include_investor_flows=market=='kr')
    monkeypatch.setattr(v2,'_now',lambda:NOW)
    monkeypatch.setattr(v2.secrets,'token_hex',lambda size:('2' if market=='us' else '1')*32)
    root=v2.NativeRuntimeRoot()
    v2._ROOTS[root]=v2._Runtime(mode='TEST_ONLY',issuer_id='C21V-OFFLINE',caller_id='C21V-OFFLINE',
        account_sha256=wire['account'],service_code_sha256=wire['code'],service_config_sha256=wire['config'],
        endpoint='https://native.invalid',generation_id='C21V-OFFLINE',expires=NOW+timedelta(minutes=5),
        bindings=((market,read.symbol,read.security_id,read.issuer_id,read.exchange,read.currency,read.session.isoformat()),),
        registration_check=lambda:None,key=KEY,meter_id=wire['meter_id'],physical_max=44)
    parent,_=v2.issue_parent(runtime=root,reads=[read])
    observer=v2.NativeObserverV2(parent=parent,root=tmp_path/'capture')
    hits=[]
    def send(request):
        hits.append(1)
        headers=wire['headers'].copy();body=wire['body'].encode()
        proof=json.loads(headers['x-native-source-proof'])
        if fault in ('account_sha256','service_code_sha256','service_config_sha256','issuer','nonce'):
            proof[fault]='TAMPERED'
        if fault=='pages':proof['raw_pages']=[]
        if fault=='count':proof['physical_count']=45
        headers['x-native-source-proof']=encoded(proof).decode()
        headers['x-native-source-signature']=hmac.new(KEY,encoded(proof),'sha256').hexdigest()
        if fault=='body':body+=b' '
        if fault=='signature':headers['x-native-source-signature']='0'*64
        return httpx.Response(200,content=body,headers=headers)
    settings=Settings(_env_file=None,ohlcv_base_url='https://native.invalid',monitor_retry_attempts=1,
        kr_price_structure_v3_enabled=True,us_price_structure_v3_enabled=True)
    monkeypatch.setattr(cli,'get_settings',lambda:settings)
    client=cli.OhlcvClient(transport=httpx.MockTransport(send),source_observer=observer)
    def run():return asyncio.run(v2.fetch_native_daily(client=client,observer=observer,read=read,as_of=NOW))
    return run,parent,read,hits


def test_actual_us_service_to_observer_completed_projection_sr_no_send(monkeypatch,tmp_path):
    from app.services import packet_owned_technical_context_service as packet
    from app.services import price_structure_wave_fibonacci_v3_service as structure
    def forbidden(*a,**k):raise AssertionError('NATIVE_RECOMPUTATION')
    monkeypatch.setattr(packet,'build_multi_timeframe_feature_packet',forbidden)
    monkeypatch.setattr(structure,'_bollinger_sources',forbidden)
    monkeypatch.setattr(structure,'_provisional_bollinger_sources',forbidden)
    run,parent,read,hits=harness(monkeypatch,tmp_path)
    context,cap,receipt=run()
    view=context.technical_context_payload()['native_view'];daily=view['periods']['daily']
    assert daily['returned_count']==86 and daily['completed_count']==85 and daily['quarantined_count']==1
    assert daily['completed_as_of']=='2026-11-06' and daily['raw_bar_date']=='2026-11-09'
    wire=json.loads((Path(os.environ['C21V_EVIDENCE'])/'ACTUAL_SERVICE_MOCK_RESPONSES.json').read_text())[1]
    provider=json.loads(wire['body'])['periods']['daily'][-2]['indicators']
    assert daily['indicators']==provider and daily['indicators']['MA288'] is None
    assert context.decision.current_price is None and not context.supply.available
    assert receipt['mode']=='TEST_ONLY' and receipt['physical_count']==11 and hits==[1]
    technical=load_packet_owned_technical_context(context.technical_context_payload(),ticker=read.symbol)
    evidence=build_decision_evidence_packet(packet={'packet_id':'C21V_OFFLINE','market':'us','assessment_date':'2026-11-06'},
        stock={'ticker':read.symbol,'company_name':'SYNTHETIC','fact_catalog':[]},technical_context=technical)
    rendered=build_us_price_structure_rollout_decision(context.chart.structure['price_structure_v3'],ticker=read.symbol,monitored_subject=True,enabled=True)
    assert rendered.section and rendered.numeric_bindings and not rendered.render_validation_errors
    assert v2.consume_result(parent=parent,result=cap,context=context)['scope']==list(v2.SCOPE)
    (Path(os.environ['C21V_EVIDENCE'])/'HOST_NO_SEND.json').write_text(json.dumps(dict(
        mode='TEST_ONLY',receipt=receipt,prompt=compact_ai_context(evidence),renderer=rendered.to_dict()),ensure_ascii=False,indent=2))


def test_actual_kr_service_finality_missing_denies_without_relabel(monkeypatch,tmp_path):
    run,parent,read,hits=harness(monkeypatch,tmp_path,market='kr')
    with pytest.raises(ValueError,match='UNCONFIRMED_FINALITY'):run()
    assert hits==[1] and v2._PARENTS[parent]['failed']
    assert not any(s['parent'] is parent for s in v2._RESULTS.values())


@pytest.mark.parametrize('fault',['account_sha256','service_code_sha256','service_config_sha256','issuer','nonce','pages','count','body','signature'])
def test_real_service_wire_tampering_rejected_no_refetch(monkeypatch,tmp_path,fault):
    run,parent,read,hits=harness(monkeypatch,tmp_path,fault=fault)
    with pytest.raises(ValueError):run()
    assert hits==[1] and v2._PARENTS[parent]['failed']


@pytest.mark.parametrize('value',[None,{},v2.NativeGetParent()])
def test_live_enrollment_never_from_public_receipt(value):
    with pytest.raises(ValueError,match='signed_service_runtime'):v2.bind_live_runtime(participant=value)


def test_native_consent_required_in_addition_to_membership(monkeypatch):
    monkeypatch.setattr(enrollment.original,'_approval',lambda handle:object())
    with pytest.raises(ValueError,match='GET_consent'):
        enrollment.enroll_participant(approval=object(),consent={'approved':True},owners={'us':object()},
            reads=[v2.NativeReadV2(role='us',symbol='CORZ',market='us',security_id='S',issuer_id='I',exchange='ND',
                currency='USD',session='2026-11-06',count=300,indicator_limit=5,include_investor_flows=False)],
            service_enrollment={},resolve_service_enrollment=lambda x:x,generation_id='X')


def test_resolver_substitution_cannot_enroll_even_with_explicit_consent(monkeypatch):
    monkeypatch.setattr(enrollment.original,'_approval',lambda handle:object())
    approval=object()
    read=v2.NativeReadV2(role='us',symbol='CORZ',market='us',security_id='S',issuer_id='I',exchange='ND',
        currency='USD',session='2026-11-06',count=300,indicator_limit=5,include_investor_flows=False)
    consent=enrollment.record_native_get_consent(approval=approval,reads=[read],generation_id='X',
        physical_max=44,consent_event_sha256='a'*64)
    with pytest.raises(ValueError,match='pinned_service_resolver'):
        enrollment.enroll_participant(approval=approval,consent=consent,owners={'us':object()},
            reads=[read],service_enrollment={'mode':'LIVE'},resolve_service_enrollment=lambda x:x,generation_id='X')
