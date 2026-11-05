import hashlib,json,os,time
from copy import deepcopy
from datetime import datetime,timezone
from types import SimpleNamespace
import pytest
from app.services import kiwoom_global_lane as lane
from app.services.operator_lane_epoch import acknowledge_cold_restart
from app.services.price_session_projection import project_price_session,validate_price_session,render_price_session

def options():
    at=datetime(2026,11,5,1,12,31,tzinfo=timezone.utc)
    read=SimpleNamespace(timeframe='daily',market='us',canonical_security_id='unseen-security',exchange='ND',
        owner='ohlcv_analyst.KiwoomProvider.get_bars',provider='kiwoom',api_id='usa06012',adjusted=True,
        latest_completed_session='2026-11-04',count=3)
    return dict(read=read,frozen_at=at,observed_at=at,source_pages=[dict(sha256='a'*64,page=1)])

@pytest.mark.parametrize('kind',['outside','normal','bad_open','bad_range','negative','duplicate','future','basis_tamper','proof_tamper','missing_hash','verified_after_hours_forgery'])
def test_session_semantics(kind):
    rows=[dict(date=d,open=10,high=12,low=9,close=11) for d in ('2026-11-02','2026-11-03','2026-11-04')]
    opts=options()
    if kind=='outside':rows[-1]['close']=8
    if kind=='bad_open':rows[-1]['open']=13
    if kind=='bad_range':rows[-1]['low']=13
    if kind=='negative':rows[-1]['close']=-1
    if kind=='duplicate':rows.append(dict(rows[-1]))
    if kind=='future':rows[-1]['date']='2026-11-06'
    if kind=='missing_hash':opts['source_pages']=[]
    if kind in ('duplicate','future','missing_hash'):
        with pytest.raises(ValueError):project_price_session(rows,**opts)
        return
    before=deepcopy(rows);value=project_price_session(rows,**opts);assert rows==before
    if kind in ('basis_tamper','proof_tamper','verified_after_hours_forgery'):
        if kind=='basis_tamper':value['adjusted']=False
        elif kind=='proof_tamper':value['source_pages'][0]['sha256']='b'*64;opts=options()
        else:value['extended_hours_verified']=dict(value=8,session='AFTER_HOURS')
        with pytest.raises(ValueError):validate_price_session(value,rows=rows,**opts)
        return
    assert validate_price_session(value,rows=rows,**opts)['strict_close'] is False
    assert 'UNCONFIRMED' in render_price_session(value)
    assert value['regular_bar_close'] is None and value['extended_hours_verified'] is None
    if kind=='outside':
        assert value['quote']['semantics']=='SESSION_UNCONFIRMED_OUTSIDE_REGULAR_RANGE'
        assert value['bar_status']=='UNRESOLVED_LATEST_BAR'
        assert value['valid_historical_suffix_count']==2 and value['missing_required_window']==1
    elif kind in ('bad_open','bad_range','negative'):
        assert value['bar_status']=='TRUE_BAR_INTEGRITY_INVALID'

@pytest.fixture
def stopped(tmp_path):
    root=tmp_path/'lane';root.mkdir(mode=0o700)
    activation=dict(protocol=lane.PROTOCOL,generation='legacy-stop',boot_identity=lane.boot_identity(),
        implementation_sha256=hashlib.sha256(__import__('pathlib').Path(lane.__file__).read_bytes()).hexdigest())
    state=dict(protocol=lane.PROTOCOL,generation='legacy-stop',boot_identity=activation['boot_identity'],
        last_end=time.monotonic(),in_flight=False,halted=True,sequence=877,pid=1073741824)
    for name,v in (('activation.json',activation),('state.json',state)):
        (root/name).write_text(json.dumps(v));(root/name).chmod(0o600)
    (root/'lane.lock').touch(mode=0o600)
    instance=lane.GlobalKiwoomLane(root)
    opts=dict(operation_id='c2s-test-operation',expected_state_sha256=hashlib.sha256((root/'state.json').read_bytes()).hexdigest(),
        expected_activation_sha256=hashlib.sha256((root/'activation.json').read_bytes()).hexdigest(),
        expected_lock_identity=instance.lock_identity,operator_message_sha256='a'*64,
        account_exclusive_confirmed=True,quiet_pids=(),explicit_approval=True)
    return root,instance,opts

@pytest.mark.parametrize('kind',['success','no_approval','wrong_hash','wrong_lock','live_pid','before_state','after_state','after_activation','changed_archive','used_twice'])
def test_original_epoch_lock_and_crash_recovery(stopped,kind):
    root,old,opts=stopped;before=(root/'state.json').read_bytes()
    if kind=='no_approval':opts['explicit_approval']=False
    if kind=='wrong_hash':opts['expected_state_sha256']='b'*64
    if kind=='wrong_lock':opts['expected_lock_identity']=(0,0)
    if kind=='live_pid':opts['quiet_pids']=(os.getpid(),)
    if kind in ('no_approval','wrong_hash','wrong_lock','live_pid'):
        with pytest.raises(ValueError):acknowledge_cold_restart(root,**opts)
        assert (root/'state.json').read_bytes()==before;return
    if kind in ('before_state','after_state','after_activation'):
        with pytest.raises(RuntimeError):acknowledge_cold_restart(root,**opts,_crash_at=kind)
        with pytest.raises(lane.GlobalLaneStop):old._state()
    receipt=acknowledge_cold_restart(root,**opts)
    assert receipt['semantic_only_proven'] is False and receipt['old_STOP_preserved']
    fresh=lane.GlobalKiwoomLane(root);state=fresh._state()
    assert state['sequence']==877 and state['last_end'] is not None and not state['halted']
    assert fresh.lock_identity==old.lock_identity
    archive=root/'operator-epochs'/opts['operation_id']/'state.json'
    assert archive.read_bytes()==before and json.loads(before)['halted'] is True
    if kind=='changed_archive':
        archive.write_text('{}')
        with pytest.raises(ValueError):acknowledge_cold_restart(root,**opts)
    elif kind=='used_twice':
        state['sequence']+=1;lane._atomic(root/'state.json',state)
        with pytest.raises(ValueError):acknowledge_cold_restart(root,**opts)
    else:assert acknowledge_cold_restart(root,**opts)==receipt
