"""Original dispatcher + actual response binding; synthetic clock/HTTP, not live."""
import asyncio,json,os,subprocess,sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path

import httpx
import pytest

from tests.test_p3g_pending_worker import pending,prepared
from tests.test_current_financial_parent_generality import registered,synthetic_clock,POLICY
from app.services import current_scoped_source_owner as owner,prospective_class_c_owner as registration
from app.services.current_scoped_source_dispatch import CurrentScopedDispatcher
from app.services.scoped_source_plan import ScopedConfig,ScopedSubject,ScopedCaptureSelection,compile_scoped_wire_contract
from app.services.sealed_source_transport import SealedSourceTransport
from app.services.same_session_market_windows import SameSessionWindows,cold_window_readback
from app.services.unified_snapshot_contract import digest


@pytest.fixture
def market_run(prepared,monkeypatch,tmp_path):
    args,_,_=prepared
    clock=synthetic_clock(monkeypatch);monkeypatch.setattr(owner,'_now',clock.now)
    registered_owner,doc,security=registered(tmp_path/'market-registration','654321','kr',
        {'corp_code':'00000123'},run_id='SYNTHETIC-MARKET-WINDOWS')
    at=datetime.fromisoformat(doc['cutoff'])
    proto=args['config']
    config=ScopedConfig(subjects=(ScopedSubject(ticker=security['ticker'],market='kr',
        security_id=security['canonical_security_id'],issuer_id=security['corp_code'],venue=security['exchange'],currency='KRW'),),
        kr_history=proto.kr_history,us_history=proto.us_history,kr_max_pages=20,
        capture_selection=ScopedCaptureSelection(stock_markets=(),stock_roles=(),market_contexts=('kr',),us_completed_closes=False))
    wire=compile_scoped_wire_contract(config=config,identities={security['ticker']:security},generation_id='SYNTHETIC-MARKET-WINDOWS',
        at=at,code_sha='a'*40,provider_config_sha256='b'*64,retries=0)
    plan=wire['request_plan'];assert len(plan.descriptors)==49
    parent=owner.issue_parent(registration_owners={'kr':registered_owner},admitted_projections={'kr':doc},
        spec=owner.ScopedSourceSpec(config=config,generation_id=plan.generation_id,cutoff=at,code_sha='a'*40,
            provider_config_sha256='b'*64,maximum_attempts=49),plan=plan,policy=POLICY,code_pins=owner.current_code_pins(),enabled=True)
    pacer=args['session']._lane
    timer=[0.0]
    pacer.clock=lambda:timer[0]
    async def sleep(delay):timer[0]+=delay
    pacer.async_sleep=sleep
    run=CurrentScopedDispatcher(parent=parent,plan=plan,root=tmp_path/'market-capture',
        owners={d.normalizer:d.owner_sha256 for d in plan.descriptors},config_identities={'kiwoom':'b'*64},
        credential_presence={'kiwoom':True},secrets=('TEST_ONLY_TOKEN',),account_pacer=pacer)
    def respond(request):
        if request.url.path=='/oauth2/token':return httpx.Response(200,json=dict(return_code=0,token='TEST_ONLY_TOKEN',expires_dt='20991231235959'))
        # Native response binding, not the caller, supplies each cursor.
        matching=[d for d in plan.descriptors if d.endpoint_operation==request.headers['api-id']
            and json.loads(json.loads(d.request_json)['body'])==json.loads(request.content)
            and d.page_ordinal==(1 if request.headers.get('cont-yn')!='Y' else int(request.headers['next-key']))]
        assert len(matching)==1
        d=matching[0];more=d.page_ordinal<d.max_pages
        return httpx.Response(200,json=dict(return_code=0,items=[dict(SYNTHETIC=True,id=d.logical_request_id)]),
            headers={'cont-yn':'Y' if more else 'N','next-key':str(d.page_ordinal+1) if more else ''})
    transport=SealedSourceTransport(run,httpx.MockTransport(respond),providers={'kiwoom'})
    return run,transport,tmp_path


async def capture_all(run,windows):
    for d in run.plan.descriptors:
        wire,_,_=run.resolve(d.logical_request_id)
        w=json.loads(wire)
        request=httpx.Request(w['method'],w['url'],headers=w['headers'],content=w['body'].encode())
        await windows.handle_async_request(request)
    return windows.finish()


def test_kr49_exact_twenty_pages_same_token_windows_and_cold(market_run):
    run,transport,tmp=market_run
    windows=SameSessionWindows(transport)
    record=asyncio.run(capture_all(run,windows))
    assert [w['physical_attempts'] for w in record['windows']]==[20,20,9]
    assert run.physical_attempts==49
    proof=cold_window_readback(plan=run.plan.model_dump(mode='json'),root=run.root,record=record)
    assert sorted(proof['pages'].values())==[20,20]
    assert proof['MarketParent']=='NOT_ISSUED' and not proof['reauthentication_proven']
    script="""import json,sys
from app.services.same_session_market_windows import cold_window_readback
v=json.load(sys.stdin);print(json.dumps(cold_window_readback(**v)))
"""
    for tamper in (False,True):
        bad=deepcopy(record)
        if tamper:bad['windows'][1]['first']+=1
        r=subprocess.run([sys.executable,'-B','-c',script],input=json.dumps(dict(plan=run.plan.model_dump(mode='json'),root=str(run.root),record=bad)),
            capture_output=True,text=True,timeout=30,env={**os.environ,'THESIS_MONITOR_ENV_FILE':''})
        assert (r.returncode==0) is (not tamper)
    receipt=os.environ.get('P3G_KR49_RECEIPT')
    if receipt:Path(receipt).write_text(json.dumps(dict(status='ORIGINAL_KR49_SAME_TOKEN_WINDOW_SYNTHETIC_PASS',
        windows=[20,20,9],ka10066_pages=[20,20],mock_physical=49,auth_count=1,
        independent_Cold_positive=True,tamper_denied=True,real_HTTP=0,
        reauthentication_carry='NOT_PROVEN_NOT_USED',Parent='NOT_ISSUED')))


@pytest.mark.parametrize('mutation',['parallel','PID','token','timeout','cap'])
def test_market_windows_reject_scope_and_reauth(market_run,mutation,monkeypatch):
    run,transport,_=market_run
    windows=SameSessionWindows(transport)
    if mutation=='cap':
        with pytest.raises(ValueError):SameSessionWindows(transport,maximum=21)
        return
    if mutation=='parallel':windows.busy=True
    elif mutation=='PID':windows.pid=-1
    elif mutation=='timeout':windows.expires=0
    else:windows.token=object()
    d=run.plan.descriptors[0];w=json.loads(d.request_json)
    with pytest.raises(ValueError):
        asyncio.run(windows.handle_async_request(httpx.Request(w['method'],w['url'],headers=w['headers'],content=w['body'].encode())))


def test_market_parent_exact_typed_missing_originals_and_public_receipt_denied():
    from app.services.market_component_handoff import required_original_parents,project_original_parent
    denial=required_original_parents({}, {}, {}, 'us')
    assert denial.status=='MISSING_REQUIRED_COMPONENT' and denial.MarketParent=='NOT_ISSUED'
    assert set(denial.missing)=={'packet','binding','authority_graph'}
    with pytest.raises(ValueError,match='unissued'):
        project_original_parent({'status':'COMPONENT_SOURCE_OBSERVED'},packet={},binding={},graph={},expected_authority_sha256='a'*64)


@pytest.mark.parametrize('missing',['energy','korea_macro','kr_overnight_cross_assets','rates_credit_liquidity_risk','central_bank_published_events','night'])
def test_each_original_provider_parent_missing_is_not_replaced(missing):
    from app.services.market_component_handoff import required_original_parents
    from app.services.canonical_market_projection import PUBLICATIONS
    # This only tests denial inventory, not fake positive Owner/Parent evidence.
    packet={'market':'us'}
    binding={k:'NOT_ADMITTED' for k in ('parent_run_id','started_at','attempts','attempt_hashes','class_c_version_set_sha256','optional_denial_set_sha256')}
    graph=dict(run_seed_sha256='NOT_ADMITTED',class_c={},markets={'us':{}},optional_denials={},
        publication_context={'class-c/'+r+'.json':{} for r in PUBLICATIONS},night={})
    if missing=='night':del graph['night']
    else:del graph['publication_context']['class-c/'+missing+'.json']
    denial=required_original_parents(packet,binding,graph,'us')
    assert denial and denial.MarketParent=='NOT_ISSUED'
    assert any(missing in path for path in denial.missing)
