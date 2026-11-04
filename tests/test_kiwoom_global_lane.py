"""Synthetic coordinator contracts. No credentials or real provider requests."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import time

import httpx
import pytest

from app.services import kiwoom_global_lane as g
from app.services.unified_live_source_transport import SourceSafetyStop
from test_current_scoped_source_dispatch import setup_parent, first_read, execute, request_for


class Clock:
    now=100.0
    def __call__(self):return self.now
    def sleep(self,n):self.now+=n
    async def asleep(self,n):self.now+=n


def initialize(root):
    root.mkdir(mode=0o700)
    activation=dict(protocol=g.PROTOCOL,generation='isolated-test',boot_identity='test-boot',
        implementation_sha256=hashlib.sha256(Path(g.__file__).read_bytes()).hexdigest())
    state=dict(protocol=g.PROTOCOL,generation='isolated-test',boot_identity='test-boot',
        last_end=None,in_flight=False,halted=False,sequence=0,pid=0)
    for n,v in [('activation.json',activation),('state.json',state)]:
        (root/n).write_text(json.dumps(v));(root/n).chmod(0o600)
    (root/'lane.lock').touch(mode=0o600)
    return root


def lane(root, clock=None, **kw):
    args=dict(boot=lambda:'test-boot')
    if clock:args.update(clock=clock,sleep=clock.sleep,async_sleep=clock.asleep)
    return g.GlobalKiwoomLane(root,**dict(args,**kw))


def enter(p):
    async def run():
        async with p.slot() as r:return dict(r)
    return asyncio.run(run())


def test_sync_async_clients_share_completion_spacing(tmp_path):
    root=initialize(tmp_path/'lane');c=Clock();p=lane(root,c)
    with p.sync_slot() as r:
        assert r['sequence']==1;c.now+=2
    second=enter(lane(root,c))
    assert second['started_monotonic']-second['previous_end']==1.5


@pytest.mark.parametrize('status',[401,403,429,500])
def test_http_error_halts_other_client(tmp_path,status):
    root=initialize(tmp_path/'lane');p=lane(root,Clock())
    with pytest.raises(httpx.HTTPStatusError):
        with p.sync_slot():
            g.validate_envelope(httpx.Response(status,request=httpx.Request('POST','https://example.invalid')))
    with pytest.raises(g.GlobalLaneStop,match='persistent_stop'):enter(lane(root,Clock()))


@pytest.mark.parametrize('body',[b'bad',b'[]',b'{"return_code":9}',b'{"return_code":"429"}'])
def test_malformed_provider_payload_latches(tmp_path,body):
    root=initialize(tmp_path/'lane');p=lane(root,Clock())
    with pytest.raises((ValueError,g.GlobalLaneStop)):
        with p.sync_slot():
            g.validate_envelope(httpx.Response(200,content=body,request=httpx.Request('POST','https://example.invalid')))
    with pytest.raises(g.GlobalLaneStop):enter(lane(root,Clock()))


@pytest.mark.parametrize('field,value',[('halted',True),('in_flight',True),('last_end',-1),
    ('last_end',float('nan')),('sequence',-1),('pid','stale'),('generation','other'),('protocol','v2')])
def test_invalid_or_crashed_state_never_resets(tmp_path,field,value):
    root=initialize(tmp_path/'lane');v=json.loads((root/'state.json').read_text());v[field]=value
    (root/'state.json').write_text(json.dumps(v))
    with pytest.raises(g.GlobalLaneStop):enter(lane(root,Clock()))


def test_boot_change_at_existing_instance_latches(tmp_path):
    root=initialize(tmp_path/'lane');p=lane(root,Clock());p.boot=lambda:'new-boot'
    with pytest.raises(g.GlobalLaneStop,match='boot_changed'):enter(p)
    assert json.loads((root/'state.json').read_text())['halted']


def test_clock_reversal_latches(tmp_path):
    root=initialize(tmp_path/'lane');c=Clock();p=lane(root,c);enter(p);c.now=99
    with pytest.raises(g.GlobalLaneStop,match='clock_reversed'):enter(p)
    c.now=500
    with pytest.raises(g.GlobalLaneStop,match='persistent_stop'):enter(p)


def test_no_automatic_bootstrap(tmp_path):
    root=tmp_path/'lane';root.mkdir(mode=0o700)
    with pytest.raises(FileNotFoundError):lane(root)
    assert list(root.iterdir())==[]


def test_no_shared_writable_state(tmp_path):
    root=initialize(tmp_path/'lane');(root/'state.json').chmod(0o644)
    with pytest.raises(g.GlobalLaneStop,match='private_custody'):enter(lane(root))


def test_symlink_rejected(tmp_path):
    root=initialize(tmp_path/'lane');alias=tmp_path/'alias';alias.symlink_to(root,target_is_directory=True)
    with pytest.raises(g.GlobalLaneStop,match='symlink'):lane(alias)


def test_missing_activation_after_load_denies(tmp_path):
    root=initialize(tmp_path/'lane');p=lane(root);(root/'activation.json').unlink()
    with pytest.raises(FileNotFoundError):enter(p)


def test_replaced_lock_inode_denied(tmp_path):
    root=initialize(tmp_path/'lane');p=lane(root)
    (root/'replacement').touch(mode=0o600);os.replace(root/'replacement',root/'lane.lock')
    with pytest.raises(g.GlobalLaneStop,match='lock_replaced'):enter(p)


def test_timeout_is_bounded_and_does_not_clear_lease(tmp_path):
    root=initialize(tmp_path/'lane');p=lane(root);c=Clock();q=lane(root,c,lock_timeout=.1)
    with p.sync_slot():
        with pytest.raises(g.GlobalLaneStop,match='lock_timeout'):enter(q)
        assert json.loads((root/'state.json').read_text())['in_flight']


def test_process_crash_does_not_reset_inflight(tmp_path,record_property):
    root=initialize(tmp_path/'lane');pid=os.fork()
    if pid==0:
        with lane(root).sync_slot():os._exit(23)
    status=os.waitpid(pid,0)[1];assert os.waitstatus_to_exitcode(status)==23
    with pytest.raises(g.GlobalLaneStop,match='persistent_stop'):enter(lane(root))
    record_property('expected_crash',dict(pid=pid,exit=23))


def test_real_fork_completion_to_start_spacing(tmp_path,record_property):
    root=initialize(tmp_path/'lane');children=[]
    for i in range(2):
        pid=os.fork()
        if pid==0:
            try:
                with lane(root).sync_slot() as r:
                    time.sleep(.03)
                (tmp_path/f'child-{i}.json').write_text(json.dumps(dict(r,end=time.monotonic())))
                os._exit(0)
            except BaseException:os._exit(9)
        children.append(pid)
    ends=[dict(pid=p,exit=os.waitstatus_to_exitcode(os.waitpid(p,0)[1])) for p in children]
    assert all(x['exit']==0 for x in ends)
    rows=sorted([json.loads((tmp_path/f'child-{i}.json').read_text()) for i in range(2)],key=lambda r:r['sequence'])
    assert rows[1]['started_monotonic']-rows[1]['previous_end']>=1.5
    record_property('actual_fork_receipts',dict(rows=rows,ends=ends,scope='ISOLATED_TEST_NOT_LIVE_SERVICE'))


def test_absent_optin_preserves_legacy(monkeypatch):
    monkeypatch.setattr(g,'_loaded_lane',None);monkeypatch.delenv('KIWOOM_GLOBAL_LANE_REQUIRED',raising=False)
    assert g.configured_lane() is None


def test_optin_missing_activation_fails_closed(monkeypatch,tmp_path):
    monkeypatch.setattr(g,'_loaded_lane',None);monkeypatch.setenv('KIWOOM_GLOBAL_LANE_REQUIRED','1')
    monkeypatch.setattr(g,'DEFAULT_ROOT',tmp_path/'absent')
    with pytest.raises(FileNotFoundError):g.configured_lane()


def test_sticky_loaded_lane_cannot_deactivate(monkeypatch,tmp_path):
    p=lane(initialize(tmp_path/'lane'));monkeypatch.setattr(g,'_loaded_lane',p)
    monkeypatch.delenv('KIWOOM_GLOBAL_LANE_REQUIRED',raising=False)
    with pytest.raises(g.GlobalLaneStop,match='optin_changed'):g.configured_lane()


def test_scoped_dispatch_cannot_override_configured_global_lane(setup_parent,tmp_path,monkeypatch):
    monkeypatch.setenv('KIWOOM_GLOBAL_LANE_REQUIRED','1')
    from app.services.current_scoped_source_dispatch import CurrentScopedDispatcher
    from app.services.kiwoom_account_pacing import AccountQueryPacer
    args,_=setup_parent;p=lane(initialize(tmp_path/'global'),Clock())
    monkeypatch.setattr(g,'_loaded_lane',p)
    private=tmp_path/'private';private.mkdir(mode=0o700)
    other=AccountQueryPacer(directory=private,account_key='a'*64,environment='real')
    with pytest.raises(ValueError,match='override_denied'):CurrentScopedDispatcher(**args,account_pacer=other)
    assert not args['root'].exists()


@pytest.mark.parametrize('kind',['valid','malformed','normalizer','http429'])
def test_scoped_actual_normalization_stays_inside_global_lease(setup_parent,tmp_path,monkeypatch,kind):
    monkeypatch.setenv('KIWOOM_GLOBAL_LANE_REQUIRED','1')
    import fcntl
    from app.services.current_scoped_source_dispatch import CurrentScopedDispatcher
    from app.services import current_scoped_source_owner as owner
    from app.services.sealed_source_transport import CapturedFragment
    args,_=setup_parent;root=initialize(tmp_path/'global');p=lane(root,Clock())
    monkeypatch.setattr(g,'_loaded_lane',p)
    run=CurrentScopedDispatcher(**args);d=first_read(run);original=CapturedFragment(d);seen=[]
    def normalize(*a,**kw):
        fd=os.open(root/'lane.lock',os.O_RDWR)
        try:
            with pytest.raises(BlockingIOError):fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            seen.append(True)
        finally:os.close(fd)
        if kind=='normalizer':raise ValueError('TEST_ONLY_BAD_SESSION')
        return original(*a,**kw)
    normalize.identity=original.identity
    transport=httpx.MockTransport(lambda r:httpx.Response(429 if kind=='http429' else 200,
        json=[] if kind=='malformed' else {'return_code':0,'rows':[]}))
    def call():return asyncio.run(run.execute(d.logical_request_id,request_for(d),transport=transport,normalize=normalize))
    if kind=='valid':assert call()['status']=='PASS' and seen==[True]
    else:
        with pytest.raises((ValueError,SourceSafetyStop)):call()
        with pytest.raises(g.GlobalLaneStop):enter(lane(root,Clock()))
        with pytest.raises(ValueError):owner.resolve_parent(args['parent'])
    assert run.physical_attempts==1


@pytest.mark.parametrize('kind',['valid','wrong_session','invalid_price'])
def test_original_close_validation_in_global_lane(tmp_path,monkeypatch,kind):
    monkeypatch.setenv('KIWOOM_GLOBAL_LANE_REQUIRED','1')
    from test_scoped_price_only_selection import selected
    from app.services import current_scoped_source_owner as owner
    from app.services.current_scoped_source_dispatch import CurrentScopedDispatcher
    args,_=selected(tmp_path);parent=owner.issue_parent(**args);spec=args['spec']
    root=initialize(tmp_path/'global');p=lane(root,Clock());monkeypatch.setattr(g,'_loaded_lane',p)
    run=CurrentScopedDispatcher(parent=parent,plan=args['plan'],root=tmp_path/'dispatch',
        owners={d.normalizer:d.owner_sha256 for d in args['plan'].descriptors},
        config_identities={'kiwoom':spec.provider_config_sha256},credential_presence={'kiwoom':True})
    d=next(d for d in run.plan.descriptors if d.endpoint_operation=='usa20590')
    row=dict(dt=d.target_period.replace('-',''),cur_prc='105',open_pric='104',high_pric='106',low_pric='103')
    if kind=='wrong_session':row['dt']='19990101'
    if kind=='invalid_price':row['cur_prc']='nan'
    transport=httpx.MockTransport(lambda r:httpx.Response(200,json=dict(return_code=0,result_list=[row])))
    if kind=='valid':assert execute(run,d,transport)['status']=='PASS'
    else:
        with pytest.raises((ValueError,SourceSafetyStop)):execute(run,d,transport)
        with pytest.raises(g.GlobalLaneStop):enter(lane(root,Clock()))
        with pytest.raises(ValueError):owner.resolve_parent(parent)
