"""C18-only focused tests, synthetic data and original capability issuers."""
from datetime import datetime,timezone,timedelta
import json
from pathlib import Path
import pytest
from app.services import valuation_research_preflight as entry
from app.services import registered_valuation_source_intent as intents
from app.services import pending_source_parent as pending
from app.services.vnext_research_store import digest,encoded
from app.services.provider_native_valuation_snapshot import derive_provider_snapshots,derive_forward_snapshot
from tests.rev28_native_fixtures import security,native_input
from test_registered_valuation_source import setup
from test_kis_fy1_semantic_owner import run as semantic_run,source,documentation,inventory,filing


def args(tmp_path,monkeypatch):
    h,parent=setup(tmp_path,monkeypatch)
    identities=intents.require_intent(h,generation_id='VALUATION_INTENT',provider='kiwoom',subjects=('999999',))
    monkeypatch.setattr(entry,'retained_listing_rows',lambda root:[dict(code='999999',marketCode='0')])
    return dict(routing_root=tmp_path,identities=identities,generation_id='C18_SYNTHETIC',
        cutoff=datetime.now(timezone.utc),code_sha='a'*40,provider_config_sha256='b'*64,enabled=True),h,parent


def test_preflight_static_and_original_parent_one_claim_ttl(tmp_path,monkeypatch):
    kw,h,p=args(tmp_path,monkeypatch);events=[]
    result=entry.prepare_registered_valuation(**kw)
    assert result['parent'] is None and result['receipt']['planned_attempts']==7
    def backend():
        events.append('AFTER_STATIC_FREEZE')
        return dict(intent=h,intent_generation='VALUATION_INTENT',session=p['session'])
    actual=entry.prepare_registered_valuation(**kw,acquire_current_context=backend)
    receipt=pending.resolve_parent(actual['parent'])
    assert result['receipt']['plan_sha256']==actual['receipt']['plan_sha256']
    assert (datetime.fromisoformat(receipt['expires_at'])-kw['cutoff']).total_seconds()==600
    assert receipt['maximum_attempts']==19 and events==['AFTER_STATIC_FREEZE']
    with pytest.raises(ValueError,match='already_claimed'):
        entry.prepare_registered_valuation(**kw,acquire_current_context=backend)


def test_missing_legacy_plan_before_backend_or_credentials(tmp_path):
    calls=[]
    with pytest.raises(FileNotFoundError):
        entry.prepare_registered_valuation(routing_root=tmp_path,identities={},generation_id='X',
            cutoff=datetime.now(timezone.utc),code_sha='a'*40,provider_config_sha256='b'*64,
            acquire_current_context=lambda:calls.append(True),enabled=True)
    assert calls==[]


def test_invalid_routing_before_backend(tmp_path,monkeypatch):
    kw,h,p=args(tmp_path,monkeypatch);kw['identities']['999999']['exchange']='UNKNOWN'
    monkeypatch.setattr(entry,'retained_listing_rows',lambda root:[])
    with pytest.raises(ValueError):entry.prepare_registered_valuation(**kw,acquire_current_context=lambda:pytest.fail('backend accessed'))


@pytest.mark.parametrize('change',['forged','expired','revoked','identity'])
def test_current_intent_not_recovered_or_reused(tmp_path,monkeypatch,change):
    kw,h,p=args(tmp_path,monkeypatch)
    if change=='forged':h={}
    if change=='expired':intents._LIVE[h]['expires']=datetime.now(timezone.utc)-timedelta(seconds=1)
    if change=='revoked':intents.revoke_intent(h)
    if change=='identity':kw['identities']['999999']['canonical_security_id']='OTHER'
    with pytest.raises((ValueError,TypeError)):
        entry.prepare_registered_valuation(**kw,acquire_current_context=lambda:dict(intent=h,intent_generation='VALUATION_INTENT',session=p['session']))


def test_default_off_and_no_empty_static_grant(tmp_path):
    from app.services.kis_retained_semantic_replay import replay_estimates
    with pytest.raises(ValueError,match='enable'):replay_estimates(tmp_path,{})
    with pytest.raises(ValueError,match='enable'):
        entry.prepare_registered_valuation(routing_root=tmp_path,identities={},generation_id='X',cutoff=None,code_sha='',provider_config_sha256='')


@pytest.mark.parametrize('kind',['wrong_fiscal','wire_missing','empty_estimate'])
def test_original_kis_semantic_gaps_preserved(kind):
    if kind=='wrong_fiscal':result=semantic_run(fiscal=inventory(filing(2020,12)))
    elif kind=='empty_estimate':result=semantic_run(raw=dict(rt_cd='0',output1={},output3=[],output4=[]))
    else:result=semantic_run()
    assert result['eps']['value'] is None
    assert result['eps']['state'].startswith('UNAVAILABLE_')


@pytest.mark.parametrize('kind',['missing_field','ADS','raw_tamper'])
def test_original_provider_missing_identity_hash_not_waived(kind):
    sec=security('FICTIONAL')
    if kind=='ADS':sec.update(issuer_type='foreign_private_issuer',security_type='adr')
    inputs=native_input(sec)
    if kind=='raw_tamper':
        inputs['raw']=b'{}'
        with pytest.raises(ValueError):derive_provider_snapshots(inputs,security=sec,run_id='fictional-snapshot')
        return
    if kind=='missing_field':
        body=json.loads(inputs['raw']);body['metric'].pop('peTTM',None)
        inputs['raw']=encoded(body);inputs['receipt']['source_sha256']=digest(inputs['raw'])
    result=derive_provider_snapshots(inputs,security=sec,run_id='fictional-snapshot')
    assert not result[0].display_eligible and result[0].value is None


def test_missing_current_registry_and_false_current_claim_denied():
    from app.services.vnext_unified_judgment import build_bundle
    from app.services.canonical_source_composition import validate_fresh_context_generation
    from app.services.unified_source_policy import UnifiedSourcePolicy
    with pytest.raises(ValueError,match='balanced_live_use_registry_required'):
        build_bundle(dict(base=dict(evidence=[])),registry=None)
    policy=UnifiedSourcePolicy(frozenset({'finnhub'}))
    with pytest.raises(ValueError,match='fresh_context_generation_or_policy_mismatch'):
        validate_fresh_context_generation(dict(run_id='OLD',run_started_at='OLD',policy=policy),
            parent_run_id='CURRENT',started_at='CURRENT',source_policy_sha256=digest(sorted(policy.allowed_providers)))


def test_new_kis_connector_uses_original_semantic_denial(tmp_path,monkeypatch):
    from app.services import kis_retained_semantic_replay as replay
    from test_kis_fy1_semantic_owner import identity
    monkeypatch.setattr(replay,'cold_source',lambda *a:dict(rows=[{}]*16))
    for kind,payload in [('estimate',source()),('identity',identity())]:
        (tmp_path/kind).mkdir();(tmp_path/kind/'123456.body').write_bytes(encoded(payload))
    plan=dict(securities={'123456':dict(corp_code='01234567')},as_of='2024-08-01T00:00:00+00:00',generation_id='SYNTHETIC')
    result=replay.replay_estimates(tmp_path,plan,enabled=True)
    assert result['rows'][0]['result']['eps']['state']=='UNAVAILABLE_FISCAL_PERIOD'
    assert not result['rows'][0]['FPER_issued'] and not result['source_plan_relabelled']
    with pytest.raises(ValueError,match='KIS_STATIC_CONTRACT_HASH_GAP'):
        replay.replay_estimates(tmp_path,plan,static_root=tmp_path,static_hashes={},enabled=True)


def test_original_static_hash_mismatch_not_repaired(tmp_path):
    from scripts.kr8_kis_integration import semantic_inputs
    p=tmp_path/'estimate-docs.json';p.write_bytes(b'{}')
    with pytest.raises(ValueError,match='KIS_STATIC_CONTRACT_HASH_GAP'):
        semantic_inputs(tmp_path,{'estimate-docs.json':'0'*64})


@pytest.mark.parametrize('kind',['valid','request_tamper','raw_tamper'])
def test_retained_inventory_original_receipt_projection(tmp_path,monkeypatch,kind):
    from app.services.kis_retained_semantic_replay import retained_fiscal_inventory
    from app.services import bounded_financial_projection as financial
    from test_kis_fy1_semantic_owner import inventory,filing
    monkeypatch.setattr(financial,'project',lambda *a,**kw:{})
    request=dict(logical_id='123456:request-001',method='GET',url='https://opendart.fss.or.kr/api/list.json',
        params=dict(corp_code='01234567'),plan_sha256='a'*64)
    raw=encoded(inventory(filing()));path=tmp_path/'request-001-attempt-1.body';path.write_bytes(raw)
    receipt=dict(logical_id=request['logical_id'],artifact=path.name,raw_sha256=digest(raw),
        request_sha256=digest(request),plan_sha256='a'*64,HTTP_status=200)
    (tmp_path/'request-001.plan.json').write_bytes(encoded(request))
    path.with_name(path.name.replace('.body','.receipt.json')).write_bytes(encoded(receipt))
    context=dict(directory=tmp_path,plan=dict(run_id='OLD_SYNTHETIC',cutoff='2024-08-01T00:00:00+00:00'),
        acquisition=dict(plan_sha256='a'*64),receipts={},expected_projection={},
        security=dict(ticker='123456',corp_code='01234567'))
    if kind=='request_tamper':
        request['params']['corp_code']='OTHER';(tmp_path/'request-001.plan.json').write_bytes(encoded(request))
    if kind=='raw_tamper':path.write_bytes(b'{}')
    if kind!='valid':
        with pytest.raises(ValueError,match='FRESH_DART_INVENTORY_RECEIPT_GAP'):
            retained_fiscal_inventory(context,path)
        return
    value,proof=retained_fiscal_inventory(context,path)
    assert value.payload()['list'][0]['rcept_dt']=='2023-12-15'
    assert proof['original_generation']=='OLD_SYNTHETIC' and not proof['current_owner'] and not proof['new_HTTP']
