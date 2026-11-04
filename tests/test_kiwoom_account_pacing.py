"""Synthetic physical-boundary proof; no credential or provider access."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import time

import httpx
import pytest

from app.services.kiwoom_account_pacing import AccountQueryPacer
from app.services.current_scoped_source_dispatch import CurrentScopedDispatcher
from app.services import current_scoped_source_owner as owner
from app.services.unified_live_source_transport import SourceSafetyStop
from test_current_scoped_source_dispatch import setup_parent, first_read, execute


class Clock:
    now = 100.0
    def __call__(self): return self.now
    async def sleep(self, seconds): self.now += seconds


def pacer(root, clock=None, **kw):
    root.mkdir(mode=0o700, exist_ok=True)
    args = dict(directory=root, account_key='a'*64, environment='real')
    if clock is not None: args.update(clock=clock, sleep=clock.sleep)
    return AccountQueryPacer(**dict(args, **kw))


def enter(p):
    async def run():
        async with p.slot() as receipt: return dict(receipt)
    return asyncio.run(run())


def test_eight_burst_requests_are_serialized(tmp_path):
    clock = Clock(); p = pacer(tmp_path/'pace', clock)
    starts = [enter(p)['started_monotonic'] for _ in range(8)]
    assert starts == [100 + i*1.5 for i in range(8)]
    assert starts[-1]-starts[0] == 10.5


@pytest.mark.parametrize('environment', ['real', 'demo'])
def test_account_isolation_and_environment_boundary(tmp_path, environment):
    clock=Clock(); root=tmp_path/'pace'
    a=pacer(root,clock,environment=environment); enter(a)
    b=pacer(root,clock,environment=environment,account_key='b'*64)
    assert enter(b)['previous_boundary_distance'] is None
    asyncio.run(a.halt())
    with pytest.raises(SourceSafetyStop): enter(pacer(root,clock,environment=environment))
    assert enter(b)['started_monotonic'] == 101.5


@pytest.mark.parametrize('change', [dict(interval=1.49),dict(interval=float('nan')),
    dict(account_key='caller-token'),dict(environment='unknown')])
def test_invalid_pacing_policy_denied(tmp_path, change):
    with pytest.raises(ValueError): pacer(tmp_path/'pace', **change)


def test_clock_reversal_persists_stop(tmp_path):
    clock=Clock();p=pacer(tmp_path/'pace',clock);enter(p);clock.now=99
    with pytest.raises(SourceSafetyStop,match='clock_reversed'): enter(p)
    clock.now=1000
    with pytest.raises(SourceSafetyStop,match='stop_latched'): enter(p)


@pytest.mark.parametrize('state', ['{"in_flight":true,"halted":false,"last_boundary":1}', '{broken'])
def test_crash_or_corrupt_state_cannot_reset_budget(tmp_path,state):
    p=pacer(tmp_path/'pace');p.path.write_text(state);p.path.chmod(0o600)
    with pytest.raises(SourceSafetyStop): enter(p)


def test_thread_competition_and_idempotent_shared_file(tmp_path,record_property):
    root=tmp_path/'pace';pacer(root)
    with ThreadPoolExecutor(2) as pool:
        rows=list(pool.map(lambda _:enter(pacer(root)),range(2)))
    starts=sorted(r['started_monotonic'] for r in rows)
    assert starts[1]-starts[0]>=1.5
    record_property('thread_starts',starts)


def test_two_process_same_host_lock(tmp_path,record_property):
    root=tmp_path/'pace';pacer(root);children=[]
    for index in range(2):
        pid=os.fork()
        if pid==0:
            try:
                row=enter(pacer(root))
                (tmp_path/f'child-{index}.json').write_text(json.dumps(dict(row,pid=os.getpid())))
                os._exit(0)
            except BaseException: os._exit(7)
        children.append(pid)
    ends=[dict(pid=pid,wait_status=os.waitpid(pid,0)[1]) for pid in children]
    assert all(row['wait_status']==0 for row in ends)
    rows=[json.loads((tmp_path/f'child-{i}.json').read_text()) for i in range(2)]
    starts=sorted(r['started_monotonic'] for r in rows)
    assert starts[1]-starts[0]>=1.5
    record_property('explicit_fork_process_receipts',dict(starts=rows,ends=ends,
        boundary='SAME_MAC_HOST_NOT_DOCKER_VM'))


@pytest.mark.parametrize('status', [401,403,429])
@pytest.mark.parametrize('position',[1,2])
def test_original_physical_boundary_stop_revoke_and_no_followup(setup_parent,tmp_path,status,position):
    args,_=setup_parent;clock=Clock();p=pacer(tmp_path/'pace',clock)
    run=CurrentScopedDispatcher(**args,account_pacer=p)
    descriptors=[d for d in run.plan.descriptors if d.consumer_role.startswith('stock:') and d.page_ordinal==1]
    calls=[]
    def respond(request):
        calls.append(request)
        return httpx.Response(status if len(calls)==position else 200,json={'return_code':0,'rows':[]})
    transport=httpx.MockTransport(respond)
    if position==2: assert execute(run,descriptors[0],transport)['status']=='PASS'
    with pytest.raises(SourceSafetyStop): execute(run,descriptors[position-1],transport)
    assert len(calls)==run.physical_attempts==position
    with pytest.raises(SourceSafetyStop): execute(run,descriptors[0],transport)
    with pytest.raises(ValueError): owner.resolve_parent(args['parent'])
    with pytest.raises(SourceSafetyStop): enter(pacer(tmp_path/'pace',clock))
    assert len(calls)==position


@pytest.mark.parametrize('kind',['transport','json_shape','normalizer'])
def test_failed_normalization_holds_stop_before_next_request(setup_parent,tmp_path,kind):
    from app.services.sealed_source_transport import CapturedFragment
    from test_current_scoped_source_dispatch import request_for
    args,_=setup_parent;p=pacer(tmp_path/'pace',Clock());run=CurrentScopedDispatcher(**args,account_pacer=p)
    d=first_read(run)
    def response(request):
        if kind=='transport': raise httpx.ConnectError('SYNTHETIC_FAILURE')
        return httpx.Response(200,json=[] if kind=='json_shape' else {'return_code':0})
    normalize=CapturedFragment(d)
    if kind=='normalizer':
        def normalize(*a,**kw): raise ValueError('SYNTHETIC_BAD_DATE')
        normalize.identity=(d.normalizer,d.owner_sha256)
    with pytest.raises((SourceSafetyStop,Exception)):
        asyncio.run(run.execute(d.logical_request_id,request_for(d),transport=httpx.MockTransport(response),normalize=normalize))
    assert run.halted and run.physical_attempts==1
    with pytest.raises(SourceSafetyStop): enter(p)
    with pytest.raises(ValueError): owner.resolve_parent(args['parent'])


def test_lock_spans_response_semantic_validation(setup_parent,tmp_path):
    from app.services.sealed_source_transport import CapturedFragment
    from test_current_scoped_source_dispatch import request_for
    import fcntl
    args,_=setup_parent;p=pacer(tmp_path/'pace',Clock());run=CurrentScopedDispatcher(**args,account_pacer=p)
    d=first_read(run);original=CapturedFragment(d);seen=[]
    def normalize(*a,**kw):
        fd=os.open(p.path,os.O_RDWR)
        try:
            with pytest.raises(BlockingIOError): fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            seen.append(True)
            return original(*a,**kw)
        finally: os.close(fd)
    normalize.identity=original.identity
    result=asyncio.run(run.execute(d.logical_request_id,request_for(d),
        transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'return_code':0})),normalize=normalize))
    assert result['status']=='PASS' and seen==[True]
    assert not run.halted


def test_reboot_with_later_monotonic_cannot_reuse_state(tmp_path):
    clock=Clock();root=tmp_path/'pace'
    enter(pacer(root,clock,boot_identity=lambda:'boot-A'))
    clock.now=10000
    with pytest.raises(SourceSafetyStop,match='boot_domain_changed'):
        enter(pacer(root,clock,boot_identity=lambda:'boot-B'))
    with pytest.raises(SourceSafetyStop,match='stop_latched'):
        enter(pacer(root,clock,boot_identity=lambda:'boot-A'))


def test_token_refresh_keeps_the_same_account_latch(tmp_path):
    root=tmp_path/'pace';first=pacer(root,Clock())
    asyncio.run(first.halt())
    # Tokens do not participate in the backend-pinned account/environment key.
    refreshed=pacer(root,Clock())
    assert refreshed.path==first.path
    with pytest.raises(SourceSafetyStop,match='stop_latched'):enter(refreshed)


def test_actual_process_death_leaves_inflight_denied(tmp_path,record_property):
    root=tmp_path/'pace';pacer(root)
    pid=os.fork()
    if pid==0:
        async def crash():
            async with pacer(root).slot():os._exit(23)
        asyncio.run(crash());os._exit(24)
    status=os.waitpid(pid,0)[1]
    assert os.waitstatus_to_exitcode(status)==23
    with pytest.raises(SourceSafetyStop,match='stop_latched'):enter(pacer(root))
    record_property('expected_fixture_exit',dict(pid=pid,exit=23,classification='EXPECTED_FIXTURE_KILL'))


@pytest.mark.parametrize('kind',['valid','missing_date','duplicate','bad_price','bad_shape'])
def test_paced_price_reuses_original_row_guard(tmp_path,kind):
    from test_scoped_price_only_selection import selected
    args,_=selected(tmp_path)
    parent=owner.issue_parent(**args);spec=args['spec'];p=pacer(tmp_path/'pace',Clock())
    run=CurrentScopedDispatcher(parent=parent,plan=args['plan'],root=tmp_path/'dispatch',
        owners={d.normalizer:d.owner_sha256 for d in args['plan'].descriptors},
        config_identities={'kiwoom':spec.provider_config_sha256},credential_presence={'kiwoom':True},account_pacer=p)
    d=next(d for d in run.plan.descriptors if d.endpoint_operation=='usa20590')
    row=dict(dt=d.target_period.replace('-',''),cur_prc='105',open_pric='104',high_pric='106',low_pric='103')
    if kind=='missing_date':row['dt']='19990101'
    if kind=='bad_price':row['cur_prc']='nan'
    rows=[row,row] if kind=='duplicate' else ['wrong'] if kind=='bad_shape' else [row]
    transport=httpx.MockTransport(lambda r:httpx.Response(200,json=dict(return_code=0,result_list=rows)))
    if kind=='valid':
        assert execute(run,d,transport)['status']=='PASS'
        assert not run.halted
    else:
        with pytest.raises((ValueError,SourceSafetyStop)):execute(run,d,transport)
        with pytest.raises(ValueError):owner.resolve_parent(parent)
        with pytest.raises(SourceSafetyStop):enter(p)
    assert run.physical_attempts==1
