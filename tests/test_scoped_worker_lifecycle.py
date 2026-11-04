"""Synthetic pipe peers; original parent admission, never a real Worker PASS."""
import asyncio
import base64
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services import current_scoped_worker_bridge as module
from app.services.current_scoped_worker_bridge import ScopedBridge
from app.services.unified_live_source_transport import SourceSafetyStop
from test_current_scoped_source_dispatch import setup_parent
from test_current_scoped_source_results import capture


class Peer:
    def __init__(self, behavior, ignore_term=False):
        self.behavior=behavior
        self.ignore_term=ignore_term
        self.pid=900001
        self.returncode=None
        self.stdout=asyncio.StreamReader(limit=128)
        self.stderr=asyncio.StreamReader(limit=128)
        self.done=asyncio.Event()
        self.stdin=self
        self.messages=[]
        self.background=[]
        self.terminated=self.killed=0

    def write(self, raw):
        value=json.loads(raw)
        self.messages.append(value)
        if value=={'close':True}:
            self.end(0)
        elif 'app_key' not in value:
            self.behavior(self,value)

    async def drain(self):pass
    def close(self):pass
    async def wait(self):
        await self.done.wait()
        return self.returncode
    def end(self, code):
        if self.returncode is None:
            self.returncode=code
            for task in self.background:task.cancel()
            self.stdout.feed_eof();self.stderr.feed_eof();self.done.set()
    def terminate(self):
        self.terminated+=1
        if not self.ignore_term:self.end(-15)
    def kill(self):
        self.killed+=1;self.end(-9)


@pytest.fixture
def make_bridge(setup_parent, tmp_path, monkeypatch):
    args,_=setup_parent
    out=tmp_path/'worker';out.mkdir()
    frozen=tmp_path/'frozen.json';frozen.write_text('{}')
    bridge=ScopedBridge(parent=args['parent'],original_plan=args['plan'],
        transport=SimpleNamespace(dispatcher=SimpleNamespace(results={})),
        worker=Path(module.__file__).resolve().parents[2]/'scripts/current_scoped_source_worker.py',
        frozen=frozen,sha=hashlib.sha256(frozen.read_bytes()).hexdigest(),output=out,
        credentials={'app_key':'TEST_ONLY_APP','secret_key':'TEST_ONLY_SECRET'},market_reads=[])
    bridge.COMMAND_SECONDS=.3
    bridge.LINE_SECONDS=.5
    bridge.CLOSE_SECONDS=.03
    bridge.TERMINATE_SECONDS=.03
    bridge.KILL_SECONDS=.03
    spawned=[]
    def attach(peer):
        async def spawn(*argv,**kwargs):
            spawned.append(argv)
            assert kwargs['env']=={'PATH':'/usr/bin:/bin','LC_ALL':'C'}
            return peer
        monkeypatch.setattr(module.asyncio,'create_subprocess_exec',spawn)
        return bridge,spawned
    return attach,out


def test_normal_multiple_commands_and_idempotent_close(make_bridge):
    async def go():
        peer=Peer(lambda p,v:p.stdout.feed_data(b'{"result":{"ok":true}}\n'))
        bridge,spawned=make_bridge[0](peer)
        assert await bridge.command({'replay':1})=={'ok':True}
        assert await bridge.command({'replay':2})=={'ok':True}
        await bridge.shutdown();await bridge.shutdown()
        assert len(spawned)==1 and len(bridge.commands)==2 and peer.returncode==0
        assert bridge.credentials is None
        with pytest.raises(SourceSafetyStop,match='terminal_no_restart'):
            await bridge.command({'replay':1})
    asyncio.run(go())
    assert json.loads((make_bridge[1]/'process-end.json').read_bytes())['state']=='NORMAL_END'


@pytest.mark.parametrize('mode',['eof','json','stderr','stdout','deadline','chatter','kill','wire'])
def test_terminal_failures_reap_and_never_restart(make_bridge, mode):
    async def go():
        def behavior(p,v):
            if mode=='eof':p.end(0)
            elif mode=='json':p.stdout.feed_data(b'NOT_JSON_TEST_ONLY_SECRET\n')
            elif mode=='stderr':p.stderr.feed_data(b'TEST_ONLY_SECRET'*100)
            elif mode=='stdout':p.stdout.feed_data(b'X'*256+b'\n')
            elif mode=='wire':
                wire=dict(method='POST',url='https://example.invalid',headers=[],body_b64='')
                p.stdout.feed_data(json.dumps({'wire':wire}).encode()+b'\n')
            elif mode=='chatter':
                async def talk():
                    for n in range(100):
                        p.stdout.feed_data(json.dumps({'progress':{'logical':str(n)}}).encode()+b'\n')
                        await asyncio.sleep(.01)
                p.background.append(asyncio.create_task(talk()))
        peer=Peer(behavior,ignore_term=mode=='kill')
        bridge,spawned=make_bridge[0](peer)
        bridge.STDERR_BYTES=128
        bridge.STDOUT_COMMAND_BYTES=128
        if mode in ('deadline','chatter','kill','wire'):
            bridge.COMMAND_SECONDS=.06
            bridge.STDOUT_COMMAND_BYTES=4096
        async def transport(request):await asyncio.Event().wait()
        bridge.transport.handle_async_request=transport
        with pytest.raises((SourceSafetyStop,ValueError)):
            await bridge.command({'stocks':True})
        assert peer.returncode is not None
        assert not bridge.busy and bridge.credentials is None
        if mode=='kill':assert peer.terminated==peer.killed==1
        with pytest.raises(SourceSafetyStop,match='terminal_no_restart'):
            await bridge.command({'stocks':True})
        assert len(spawned)==1 and not bridge.commands
        await bridge.shutdown()
    asyncio.run(go())
    for path in make_bridge[1].glob('*.json'):
        assert b'TEST_ONLY_SECRET' not in path.read_bytes()
    end=json.loads((make_bridge[1]/'process-end.json').read_bytes())
    assert end['state']=='FAILED_OR_CANCELLED'
    assert end['restart_allowed'] is False
    assert (make_bridge[1]/'command-failure.json').exists()


def test_cancellation_reaps_and_closes_journal(make_bridge):
    async def go():
        peer=Peer(lambda p,v:None)
        bridge,_=make_bridge[0](peer)
        command=asyncio.create_task(bridge.command({'stocks':True}))
        await asyncio.sleep(.01)
        command.cancel()
        with pytest.raises(asyncio.CancelledError):await command
        assert peer.returncode==-15 and bridge._stderr_task.done()
    asyncio.run(go())
    assert json.loads((make_bridge[1]/'command-failure.json').read_bytes())['state']=='CANCELLED'


def test_concurrent_command_rejected_without_second_peer(make_bridge):
    async def go():
        peer=Peer(lambda p,v:None)
        bridge,spawned=make_bridge[0](peer)
        first=asyncio.create_task(bridge.command({'stocks':True}))
        await asyncio.sleep(.01)
        with pytest.raises(SourceSafetyStop,match='concurrent_command'):
            await bridge.command({'replay':1})
        first.cancel()
        with pytest.raises(asyncio.CancelledError):await first
        assert len(spawned)==1
    asyncio.run(go())


def test_bounded_stderr_is_drained_while_command_active(make_bridge):
    async def go():
        def behavior(p,v):
            p.stderr.feed_data(b'TEST_ONLY_DIAGNOSTIC'*1000)
            async def result():
                await asyncio.sleep(.01)
                assert bridge._stderr_bytes==len(b'TEST_ONLY_DIAGNOSTIC')*1000
                p.stdout.feed_data(b'{"result":{"ok":true}}\n')
            p.background.append(asyncio.create_task(result()))
        peer=Peer(behavior)
        bridge,_=make_bridge[0](peer)
        assert await bridge.command({'replay':1})=={'ok':True}
        await bridge.shutdown()
        assert bridge._stderr_bytes==len(b'TEST_ONLY_DIAGNOSTIC')*1000
    asyncio.run(go())


def test_original_consumer_rejects_failed_lifecycle_even_with_zero_exit(capture):
    from app.services import current_scoped_source_results as results
    args,bridge,_=capture
    results.bind_capture(**args,worker_bridge=bridge)
    bridge.process=SimpleNamespace(pid=900002,returncode=0)
    start={'pid':900002,'start':1,'worker_sha256':hashlib.sha256(bridge.worker.read_bytes()).hexdigest()}
    end={'pid':900002,'end':2,'exit':0,'state':'FAILED_OR_CANCELLED'}
    (bridge.output/'process-start.json').write_text(json.dumps(start))
    (bridge.output/'process-end.json').write_text(json.dumps(end))
    _,_,plan,stock,root,worker=results._context(**args)
    with pytest.raises(ValueError,match='worker_end_missing'):
        results._worker_custody(args['parent'],args['dispatcher'],plan,stock,root,worker)
