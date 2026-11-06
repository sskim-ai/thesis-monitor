"""Focused C20 only: retained official bytes, no HTTP, SQL or AI."""
import asyncio,json
from copy import deepcopy
from datetime import datetime,timezone
from pathlib import Path
import httpx,pytest
from app.services import valuation_analysis as analysis
from app.services.vnext_daily_research import UseRegistry
from app.services.vnext_research_store import digest

W=Path(__file__).resolve().parents[1]
P=W/'data/vnext/c16-20261106/kis'
ARCHIVE=Path('/Users/sskim/Documents/Codex/Reports/20261001-r2b-r9-rev40-r1-kr8-live-fper/thesis-monitor-20261001-r2b-r9-rev40-r1-kr8-live-fper-report.zip')
ARCHIVE_SHA='34c3ade5f8b1f640f3d4f88b6aa6a35b82c2da3151ca1236a193addb7e571d35'
def read(p):return json.loads(p.read_bytes())

@pytest.fixture(scope='module',autouse=True)
def deny_network():
    import socket
    with pytest.MonkeyPatch.context() as mp:
        def deny(*a,**k):raise AssertionError('C20_TEST_NETWORK_FORBIDDEN')
        mp.setattr(socket.socket,'connect',deny);mp.setattr(socket,'create_connection',deny)
        yield

@pytest.fixture(scope='module')
def retained():
    at=datetime.now(timezone.utc).isoformat();plan=read(P/'plan.json')
    src=analysis.kis_source(root=P,plan=plan,calibration_archive=ARCHIVE,calibration_sha256=ARCHIVE_SHA,as_of=at)
    return at,plan,src,src.read()

def test_real_KIS_original_receipts_calibration_and_first_forecast(retained):
    at,plan,src,(ids,facts,denials)=retained
    assert len(facts)==5 and len(denials)==3
    assert {f.forecast_fiscal_period for f in facts}=={'2026.12E'}
    assert all(f.unit=='KRW_PER_SHARE' and f.estimated and not f.formal_native for f in facts)
    assert next(f for f in facts if f.ticker=='005490').exact_value=='29666.1'

@pytest.mark.parametrize('mutation',['wrong_ticker','non_EPS_layout','unknown_scale','no_forecast','FY2_only'])
def test_semantic_mutations_denied(retained,mutation):
    at,plan,_,_=retained;code='005490'
    body=read(P/'estimate'/f'{code}.body');identity=read(P/'identity'/f'{code}.body')
    receipt=read(P/'estimate'/f'{code}-receipt.json');docs,protocol=analysis.calibration_from_archive(ARCHIVE,ARCHIVE_SHA)
    if mutation=='wrong_ticker':body['output1']['sht_cd']='A999999'
    if mutation=='non_EPS_layout':body['output3']=[body['output3'][0]]
    if mutation=='unknown_scale':protocol['factors']['EPS']='1'
    if mutation=='no_forecast':body['output4']=[dict(dt=f'{2021+i}.12') for i in range(5)]
    if mutation=='FY2_only':body['output4'][3]['dt']='2027.12E'
    with pytest.raises(ValueError):analysis.parse_analyst_eps(ticker=code,security=plan['securities'][code],
        estimate=body,identity=identity,receipt=receipt,generation=plan['generation_id'],as_of=at,docs=docs,protocol=protocol)

def test_KR_Composite_catalog_optional_Unified_prompt_and_gates(retained):
    from app.services.vnext_unified_judgment import prompt,AI_OWNED_V3
    at,_,src,_=retained
    view=analysis.AnalysisView(sources=[src],ticker='005490',as_of=at,enabled=True)
    registry=UseRegistry();packet=view.unified_premodel(registry=registry,contract=AI_OWNED_V3)
    ctx=packet['investment_valuation_context']
    assert all(ctx['axes'][a][0]['value']==29666.1 for a in ('Overall','NewBuyer','Holders'))
    assert packet['valuation_facts'][0]['unit']=='KRW_PER_SHARE'
    assert packet['admissibility'][0]['analytic_opinion_use']['eligible']
    assert not ctx['standalone_direction'] and not ctx['formal_native'] and not packet['strict_ready']
    assert 'VALUATION_ANALYSIS_FACT_V1' in prompt(packet,'BLIND',knowledge='',registry=registry,version=AI_OWNED_V3)
    from app.services.vnext_unified_judgment import _resolve_axis_evidence
    ref=packet['admissibility'][0]['ref']
    candidate=dict(business='INSUFFICIENT',technical_review=None,
        security_id=packet['base']['public_security']['canonical_security_id'],as_of=packet['base']['as_of'],
        **{name:dict(stance='NOT_ISSUED',refs=[],counterevidence_refs=[])
           for name in ('overall','newbuyer','holder_virtual','valuation','timing')})
    candidate['overall']=dict(stance='BUY',refs=[ref],counterevidence_refs=[])
    with pytest.raises(ValueError,match='economic_anchor_missing'):
        _resolve_axis_evidence(candidate,packet,{ref},None)

def test_US_native_ratios_to_same_Unified_without_EPS():
    from app.services.dated_capture_research import bind_dated_archive
    from app.services.vnext_unified_judgment import AI_OWNED_V3
    p=W/'data/vnext/c16-20261106/finnhub';meta=read(p/'cold-ingress.json')
    from app.services.public_capture_storage import FileCaptureArchive
    store=FileCaptureArchive.open_sealed_read_only(meta['root'],expected_manifest_sha256=meta['manifest_sha256'],
        expected_capture_seal_sha256=meta['capture_seal_sha256'])
    s=next(s for s in store.identities() if s['ticker']=='GOOGL')
    at=datetime.now(timezone.utc).isoformat()
    bundle=bind_dated_archive(root=meta['root'],manifest_sha256=meta['manifest_sha256'],
        capture_seal_sha256=meta['capture_seal_sha256'],run_id=store._manifest['run_id'],
        ticker=s['ticker'],canonical_security_id=s['canonical_security_id'],as_of=at,enabled=True)
    view=analysis.AnalysisView(sources=[analysis.dated_native_source(bundle)],ticker='GOOGL',as_of=at,enabled=True)
    packet=view.unified_premodel(registry=UseRegistry(),contract=AI_OWNED_V3)
    assert {f['metric'] for f in packet['investment_valuation_context']['facts']}=={'PER','PBR','FPER'}
    assert all(r['analytic_opinion_use']['eligible'] for r in packet['admissibility'])

def test_FPER_missing_price_zero_EPS_and_wrong_original_preserve_EPS(retained):
    f=retained[3][1][0]
    assert analysis.matched_fper(f)['value'] is None
    zero=analysis.ValuationAnalysisFact.model_validate(dict(f.model_dump(),value=0,exact_value='0'))
    assert analysis.matched_fper(zero)['state']=='NOT_MEANINGFUL'
    with pytest.raises(ValueError):analysis.matched_fper(f,original_eps={},price={'adjusted':True},actions={})
    assert f.display_eligible

def test_live_composition_default_off_and_pre_parent_config_check(tmp_path,monkeypatch):
    from app import vnext_worker as entry
    from app.services import kiwoom_participant_session
    observed={}
    def session(**kwargs):observed.update(kwargs);return object()
    with monkeypatch.context() as mp:
        mp.setattr(kiwoom_participant_session,'ParticipatingSession',session)
        entry._mac_valuation_session()
    assert {'app.services.current_scoped_worker_bridge','app.services.current_scoped_source_dispatch',
        'app.services.scoped_worker_launch','app.services.sealed_source_transport'} <= {m.__name__ for m in observed['modules']}
    with pytest.raises(ValueError):asyncio.run(entry.run_mac_registered_valuation(decision=None,database=None,
        preflight=None,base=None,external_root=None,settings_env_file=None,attempt_marker=None))
    from test_c19_runner import configure
    pre,_,_=configure(tmp_path,monkeypatch);called=[]
    with pytest.raises(ValueError,match='credentials_transport'):
        asyncio.run(entry.run_registered_valuation_source(preflight=pre,base=tmp_path/'unused',
            external_root='/Users/sskim/Codex/ohlcv-analyst',acquire_current_context=lambda:called.append(True),
            load_credentials=None,inner=httpx.MockTransport(lambda _:None),enabled=True))
    assert not called and not (tmp_path/'unused').exists()
