"""Four focused host-wiring cases only; no real SQL, HTTP or AI."""
import asyncio
from datetime import datetime,timedelta,timezone
from types import SimpleNamespace
import pytest
from app import vnext_worker as entry
from app.services.prospective_class_c_owner import ApprovalDecision


@pytest.mark.parametrize('kind',['env','external'])
def test_configuration_rejected_before_marker_DB_and_Parent(tmp_path,monkeypatch,kind):
    from app.services import minimal_class_c_export as sql,prospective_class_c_owner as authority
    monkeypatch.setattr(sql,'capture_authorized_class_c',lambda *a,**k:pytest.fail('SQL before configuration'))
    monkeypatch.setattr(authority,'record_backend_approval',lambda *a,**k:pytest.fail('Parent before configuration'))
    env=tmp_path/'example.env';env.write_text('UNKNOWN_C20R1_SETTING=invalid\n')
    external=tmp_path/'external';external.mkdir()
    at=datetime.now(timezone.utc)
    decision=ApprovalDecision(event_id='TEST_ONLY',user_message_sha256='a'*64,approved=True,
        effective_at=at,expires_at=at+timedelta(minutes=5),subjects=('999999',))
    with pytest.raises(ValueError):
        asyncio.run(entry.run_mac_registered_valuation(decision=decision,database=tmp_path/'never.sqlite',
            preflight={'identities':{'999999':{}}},base=tmp_path/'unused',
            external_root=external if kind=='env' else tmp_path/'missing',
            settings_env_file=env,attempt_marker=tmp_path/'marker.json',enabled=True))
    assert not (tmp_path/'marker.json').exists() and not (tmp_path/'never.sqlite').exists()


def test_original_missing_closure_denied_and_fixed_session_uses_required_modules(tmp_path,monkeypatch):
    from test_c19_runner import configure
    from app.services import kiwoom_global_lane,kiwoom_participant_session,scoped_worker_launch
    configure(tmp_path,monkeypatch)
    old=kiwoom_participant_session.ParticipatingSession(modules=(kiwoom_global_lane,kiwoom_participant_session),caller_kind='CLI')
    bridge=SimpleNamespace(custody_policy=scoped_worker_launch.CUSTODY_POLICY,source_session=old,
        transport=SimpleNamespace(dispatcher=SimpleNamespace(_account_pacer=old._lane)))
    with pytest.raises(ValueError,match='scoped_source_parent_loaded_closure_required'):
        scoped_worker_launch.prepare(bridge)
    fixed=entry._mac_valuation_session();fixed.attestation()
    assert {'app.services.current_scoped_worker_bridge','app.services.current_scoped_source_dispatch',
        'app.services.scoped_worker_launch','app.services.sealed_source_transport'} <= {m.__name__ for m in fixed._modules}


def test_default_OFF_original_19_cap_and_terminal_no_retry(tmp_path):
    from app.services.current_scoped_worker_bridge import ScopedBridge
    from app.services.unified_live_source_transport import SourceSafetyStop
    from app.services.registered_valuation_source_parent import compile_plan
    with pytest.raises(ValueError,match='explicit_enable'):
        asyncio.run(entry.run_mac_registered_valuation(decision=None,database=None,preflight=None,
            base=None,external_root=None,settings_env_file=None,attempt_marker=None))
    closed=object.__new__(ScopedBridge);closed._closed=True
    with pytest.raises(SourceSafetyStop,match='terminal_no_restart'):
        asyncio.run(closed.command({}))
    ids={f'{i:06d}':dict(ticker=f'{i:06d}',country='KR',exchange='KOSPI') for i in range(9)}
    with pytest.raises(ValueError):compile_plan(identities=ids,
        listing_rows=[dict(code=t,marketCode='0') for t in ids],generation_id='TEST_ONLY',
        cutoff=datetime.now(timezone.utc),code_sha='a'*40,provider_config_sha256='b'*64)
    source=__import__('inspect').getsource(compile_plan)
    assert 'retries=0' in source and '>19' in source
