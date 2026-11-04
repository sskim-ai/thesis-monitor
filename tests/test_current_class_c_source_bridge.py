"""P2G synthetic capture/real code boundary tests; never real issuer authority."""
import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3

import httpx
import pytest

from app.services import current_class_c_source_bridge as bridge
from app.services import prospective_class_c_owner as owner
from app.services.canonical_source_replay import current_local_seed, require_sealed_body, stock_inputs
from app.services.minimal_class_c_export import CapturedClassC, capture_authorized_class_c
from app.services.sealed_fresh_dispatch import ProviderPlan, SealedDispatcher, consume_bound_result
from app.services.unified_snapshot_contract import encoded, digest
from app.services.unified_stock_acquisition import UNIVERSE, ROLES, validate_role
from app.services.unified_run_artifacts import sha256_bytes
from tests.test_minimal_class_c_export import database, POLICY
from tests.test_r9_rev11_sealed_dispatch import ROOT, CONFIG


@pytest.fixture
def case(tmp_path):
    subjects = [(t, m) for m, ts in UNIVERSE.items() for t in ts]
    permission = database(tmp_path, subjects)
    with sqlite3.connect(permission.database) as db:
        for n, (ticker, market) in enumerate(subjects, 1):
            db.execute('UPDATE securitymaster SET cik=?, corp_code=?, company_name=? WHERE ticker=?',
                (str(n) if market == 'us' else None, str(n).zfill(8) if market == 'kr' else None,
                 f'Synthetic issuer {n}', ticker))
    at = datetime.now(timezone.utc)
    approval = owner.record_backend_approval(owner.ApprovalDecision(event_id='P2G_SYNTHETIC_ONLY',
        user_message_sha256='a'*64, approved=True, effective_at=at,
        expires_at=at+timedelta(minutes=50), subjects=permission.subjects))
    capture = capture_authorized_class_c(permission)
    owners = {m: owner.issue_prospective_owner(approval=approval, capture=capture, market=m,
        source_generation_id='synthetic-registration', generation_id='p2g-test', policy=POLICY)[0]
        for m in UNIVERSE}
    kwargs = dict(capture=capture, owners=owners, policy=POLICY,
        stock_metadata=dict(run_id='p2g-test', acquisition_id='p2g-capture',
            instruction_sha='1'*40, implementation_sha='2'*40, owner_files={'synthetic.py': '3'*64},
            owner_head='4'*40, settings_sha256=CONFIG, request_environment_sha256=CONFIG),
        counts={m: {r: 100 for r in ROLES} for m in UNIVERSE},
        config_identities={p: CONFIG for p in ('kiwoom', 'sec_edgar', 'opendart', 'fred',
            'eia', 'ecos', 'krx_night_futures', 'google_news_rss', 'naver_news')},
        configured_kr_pages=50, kr_post_acquisition_completeness_approved=True)
    handle, stock, frozen = bridge.prepare_current_bridge(**kwargs, enabled=True)
    return dict(handle=handle, stock=stock, frozen=frozen, kwargs=kwargs,
        approval=approval, owners=owners, root=tmp_path/'public')


def local(c, market='kr', **changes):
    args = dict(root=c['root'], frozen=c['frozen'], plan=c['stock'], market=market,
        policy=POLICY, class_c_bridge=c['handle'])
    args.update(changes)
    return current_local_seed(**args)


def dispatch(c):
    # Existing historical proof authority is synthetic here; it is NOT current approval.
    plan = ProviderPlan(**c['frozen']['plan'], rev10_receipt_sha256=sha256_bytes(encoded(ROOT)+b'\n'))
    owners = {d.normalizer: d.owner_sha256 for d in plan.descriptors}
    run = SealedDispatcher(plan=plan, root=c['root']/'dispatch', rev10_receipt=ROOT,
        owners=owners, config_identities=c['kwargs']['config_identities'],
        credential_presence={p: True for p in c['kwargs']['config_identities']})
    c['frozen'] = bridge.bind_existing_dispatcher(c['handle'], run, policy=POLICY)
    return run


@pytest.mark.parametrize('market,count', [('kr', 8), ('us', 14)])
def test_original_capture_to_current_consumer(case, market, count):
    doc = local(case, market)
    assert len(doc['universe']['eligible_subjects']) == count
    assert not doc['denials']
    assert len([r for r in case['stock'].reads if r.market == market]) == count*4
    assert not case['root'].exists()


def test_same_run_reuse_private_memory_and_copy_isolation(case):
    first = local(case)
    first['roles'].clear()
    assert local(case)['roles'] and local(case) == local(case)
    public = encoded(case['frozen'])
    for marker in (b'selected private', b'core_thesis', b'private-not-in-projection'):
        assert marker not in public
    versions = bridge.memory_version_set(case['handle'], frozen=case['frozen'], policy=POLICY)
    assert versions['class-c/local-kr.json'] == sha256_bytes(encoded(local(case))+b'\n')
    case['stock'].owner_files['synthetic.py'] = 'f'*64
    with pytest.raises(ValueError, match='frozen_contract'):
        local(case)


@pytest.mark.parametrize('field', ['generation', 'session', 'pin', 'purpose', 'alias', 'ads_identity'])
def test_exact_frozen_binding_cannot_be_self_rehashed(case, field):
    f = deepcopy(case['frozen'])
    if field == 'generation': f['generation_id'] = 'other'
    elif field == 'session': f['sessions']['us'] = '1900-01-01'
    elif field == 'pin': f['protected_input_hashes']['class-c/local-kr.json'] = 'f'*64
    elif field == 'purpose': f['execution_purpose'] = 'PRODUCTION_MONITORING'
    else:
        key = 'subject' if field == 'alias' else 'canonical_security_id'
        f['stock_plan']['reads'][0][key] = 'caller-substitution'
    with pytest.raises(ValueError, match='frozen_contract'):
        local(case, frozen=f)


def test_default_off_and_unissued_capture_and_json_handle(case):
    with pytest.raises(ValueError, match='default_off'):
        bridge.prepare_current_bridge(**case['kwargs'])
    with pytest.raises(ValueError, match='unissued_capture'):
        bridge.prepare_current_bridge(**dict(case['kwargs'], capture=CapturedClassC()), enabled=True)
    for invalid in (bridge.CurrentClassCBridge(), case['frozen']):
        with pytest.raises(ValueError, match='live_bridge'):
            local(case, class_c_bridge=invalid)


def test_expired_original_owner_before_consumption(case, monkeypatch):
    monkeypatch.setattr(owner, '_now', lambda: datetime.now(timezone.utc)+timedelta(hours=2))
    with pytest.raises(ValueError, match='expired'):
        local(case)


def test_revoked_original_owner_before_consumption(case):
    owner.revoke_prospective_owner(case['owners']['kr'])
    with pytest.raises(ValueError, match='live_backend_owner'):
        local(case)


def test_wrong_process_and_bridge_revocation(case, monkeypatch):
    pid = bridge.os.getpid()
    with monkeypatch.context() as m:
        m.setattr(bridge.os, 'getpid', lambda: pid+1)
        with pytest.raises(ValueError, match='process_or_code'):
            local(case)
    bridge.revoke_bridge(case['handle'])
    with pytest.raises(ValueError, match='live_bridge'):
        local(case)


def test_new_six_not_registered_or_added_by_plan(case):
    six = {'010140', '016360', '272210', 'META', 'JOBY', 'MRVL'}
    assert not six & {r.subject for r in case['stock'].reads}
    for ticker in six:
        member = deepcopy(case['frozen'])
        member['stock_plan']['reads'][0]['subject'] = ticker
        with pytest.raises(ValueError, match='frozen_contract'):
            local(case, frozen=member)


def test_mixed_legacy_owner_and_wrong_policy_denied(case):
    with pytest.raises(ValueError, match='mixed_owner'):
        local(case, prospective_owner=case['owners']['kr'])
    from app.services.unified_source_policy import UnifiedSourcePolicy
    with pytest.raises(ValueError, match='frozen_contract'):
        local(case, policy=UnifiedSourcePolicy(frozenset({'canonical_local'})))


def test_original_dispatch_and_publication_receipt_and_consumer(case):
    run = dispatch(case)
    assert bridge.bind_existing_dispatcher(case['handle'], run, policy=POLICY) == case['frozen']
    descriptor = next(d for d in run.plan.descriptors if d.provider == 'fred')
    wire = json.loads(descriptor.request_json)
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json={'observations': []}))
    capture = bridge.publication_capture(case['handle'], root=case['root'], frozen=case['frozen'],
        policy=POLICY, provider='fred', inner=transport)
    response = asyncio.run(capture.handle_async_request(httpx.Request(wire['method'], wire['url'],
        headers=wire['headers'], content=wire['body'])))
    final = run.results[descriptor.logical_request_id]
    assert response.status_code == 200 and len(capture.receipts) == 1
    consume_bound_result(root=run.root, plan=run.plan, logical_id=descriptor.logical_request_id,
        receipt_sha256=final['receipt_sha256'])
    require_sealed_body(case['root'], case['frozen'], {'logical_results': run.results},
        role=descriptor.role_id, raw_sha256=sha256_bytes(response.content))
    assert capture.receipts[0]['run_id'] == case['stock'].run_id
    assert not (case['root']/'class-c').exists()


def test_source_role_denied_before_mock_transport(case):
    dispatch(case)
    calls = []
    capture = bridge.publication_capture(case['handle'], root=case['root'], frozen=case['frozen'],
        policy=POLICY, provider='fred', inner=httpx.MockTransport(lambda r: calls.append(r)))
    with pytest.raises(BaseException, match='not_unique_sealed_slot'):
        asyncio.run(capture.handle_async_request(httpx.Request('GET', 'https://api.stlouisfed.org/not-planned')))
    assert not calls


def test_revocation_after_publication_construction_blocks_dispatch(case):
    run = dispatch(case)
    calls = []
    capture = bridge.publication_capture(case['handle'], root=case['root'], frozen=case['frozen'],
        policy=POLICY, provider='fred', inner=httpx.MockTransport(lambda r: calls.append(r)))
    bridge.revoke_bridge(case['handle'])
    with pytest.raises(ValueError, match='live_bridge'):
        asyncio.run(capture.handle_async_request(httpx.Request('GET', 'https://api.stlouisfed.org/not-planned')))
    assert not calls and not run.used


def test_fake_publication_has_no_source_use(case):
    dispatch(case)
    with pytest.raises(ValueError, match='consumer_body_not_bound'):
        require_sealed_body(case['root'], case['frozen'], {'logical_results': {}},
            role='fred:invented', raw_sha256='f'*64)


def test_missing_raw_and_dispatch_are_not_current_source_pass(case):
    with pytest.raises(ValueError, match='bound_dispatcher'):
        stock_inputs(case['root'], case['frozen'], POLICY, {}, class_c_bridge=case['handle'])
    dispatch(case)
    with pytest.raises(FileNotFoundError):
        stock_inputs(case['root'], case['frozen'], POLICY, {'logical_results': {}}, class_c_bridge=case['handle'])
    from app.services.canonical_source_inputs import build_source_replay_inputs
    with pytest.raises(FileNotFoundError, match='raw-owner-replay'):
        build_source_replay_inputs(case['root'], case['frozen'], {'logical_results': {}}, POLICY,
            binding_factory=lambda **kw: pytest.fail('no source seed without raw'), class_c_bridge=case['handle'])


def test_dispatch_plan_mutation_and_wrong_root_rejected(case):
    run = dispatch(case)
    with pytest.raises(ValueError, match='bound_dispatcher'):
        bridge.require_dispatch(case['handle'], root=case['root']/'wrong', frozen=case['frozen'], policy=POLICY)
    original = (run.root/'plan.json').read_bytes()
    (run.root/'plan.json').unlink()
    (run.root/'plan.json').symlink_to(run.root/'admission.json')
    with pytest.raises(ValueError, match='symlink_denied'):
        bridge.require_dispatch(case['handle'], root=case['root'], frozen=case['frozen'], policy=POLICY)
    (run.root/'plan.json').unlink()
    (run.root/'plan.json').write_bytes(original)
    (run.root/'plan.json').write_bytes(b'{}')
    with pytest.raises(ValueError, match='seal_changed'):
        bridge.require_dispatch(case['handle'], root=case['root'], frozen=case['frozen'], policy=POLICY)


def test_original_overlap_bar_rejection_unchanged(case, tmp_path):
    read = next(r for r in case['stock'].reads if r.market == 'kr')
    request = dict(route=read.route, api_id=read.api_id,
        payload=dict(stk_cd=read.subject, upd_stkpc_tp=str(int(read.adjusted))))
    raw = encoded({'return_code': 0})
    bar = dict(date=read.latest_completed_session, open=10, high=12, low=9, close=11, volume=100)
    rows = encoded([bar, bar])
    (tmp_path/'raw.json').write_bytes(raw)
    (tmp_path/'rows.json').write_bytes(rows)
    at = case['stock'].frozen_at.isoformat()
    receipt = dict(run_id=case['stock'].run_id, acquisition_id=case['stock'].acquisition_id,
        plan_sha256=digest(case['stock'].model_dump(mode='json')), entry=read.model_dump(mode='json'),
        started_at=at, completed_at=at, status='CAPTURED', normalized_artifact='rows.json',
        normalized_sha256=sha256_bytes(rows), pages=[dict(provider='kiwoom', entry_id=read.entry_id,
            page_ordinal=1, request=request, request_sha256=digest(request), requested_at=at,
            received_at=at, artifact='raw.json', source_sha256=sha256_bytes(raw), http_status=200)])
    with pytest.raises(ValueError, match='ohlcv_integrity_failed'):
        validate_role(case['stock'], read, receipt, tmp_path)


def test_revocation_between_attempts_stops_original_retry(case, monkeypatch):
    run = dispatch(case)
    d = next(d for d in run.plan.descriptors if d.provider == 'fred')
    wire = json.loads(d.request_json)
    calls = []
    def respond(request):
        calls.append(request)
        return httpx.Response(503, json={'status': 'synthetic_transient'})
    async def revoke_during_retry_wait(seconds):
        bridge.revoke_bridge(case['handle'])
    monkeypatch.setattr(asyncio, 'sleep', revoke_during_retry_wait)
    capture = bridge.publication_capture(case['handle'], root=case['root'], frozen=case['frozen'],
        policy=POLICY, provider='fred', inner=httpx.MockTransport(respond))
    from app.services.unified_live_source_transport import SourceSafetyStop
    with pytest.raises(SourceSafetyStop, match='attempt_authority_lost'):
        asyncio.run(capture.handle_async_request(httpx.Request(wire['method'], wire['url'],
            headers=wire['headers'], content=wire['body'])))
    assert len(calls) == 1 and run.halted
    assert run.results[d.logical_request_id]['status'] == 'SYSTEMIC_STOP'
    assert not capture.receipts


@pytest.mark.parametrize('role', ['probe', 'history'])
def test_original_night_receipt_locations(case, role):
    run = dispatch(case)
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={'OutBlock_1': []}))
    with pytest.raises(ValueError, match='night_role_required'):
        bridge.publication_capture(case['handle'], root=case['root'], frozen=case['frozen'],
            policy=POLICY, provider='krx_night_futures', inner=transport)
    capture = bridge.publication_capture(case['handle'], root=case['root'], frozen=case['frozen'],
        policy=POLICY, provider='krx_night_futures', inner=transport, night_role=role)
    d = next(d for d in run.plan.descriptors if d.provider == 'krx_night_futures')
    wire = json.loads(d.request_json)
    asyncio.run(capture.handle_async_request(httpx.Request(wire['method'], wire['url'],
        headers=wire['headers'], content=wire['body'])))
    assert (case['root']/'night'/role/'receipt-001.json').is_file()
    assert not (case['root']/'publications'/'krx_night_futures').exists()
    final = run.results[d.logical_request_id]
    consume_bound_result(root=run.root, plan=run.plan, logical_id=d.logical_request_id,
        receipt_sha256=final['receipt_sha256'])
