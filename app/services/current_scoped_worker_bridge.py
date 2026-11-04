"""Backend scoped worker capability; no model or Full22 Native invocation."""
import asyncio
import base64
import hashlib
import json
from pathlib import Path
import sys
import time

import httpx

from app.services.current_scoped_source_owner import resolve_parent
from app.services.unified_live_source_transport import SourceSafetyStop
from app.services.unified_run_artifacts import durable_json
from app.services.unified_snapshot_contract import digest, encoded


class ScopedBridge(httpx.AsyncBaseTransport):
    COMMAND_SECONDS = 600
    LINE_SECONDS = 180
    STDOUT_LINE_BYTES = 16 * 1024 * 1024
    STDOUT_COMMAND_BYTES = 64 * 1024 * 1024
    STDERR_BYTES = 1024 * 1024
    CLOSE_SECONDS = 10
    TERMINATE_SECONDS = 5
    KILL_SECONDS = 5

    def __init__(self, *, parent, original_plan, transport, worker, frozen, sha, output, credentials, market_reads,
                 source_session=None, custody_policy=None):
        expected_worker = Path(__file__).resolve().parents[2] / "scripts/current_scoped_source_worker.py"
        if Path(worker).resolve() != expected_worker or Path(worker).is_symlink():
            raise ValueError("scoped_original_worker_required")
        if hashlib.sha256(Path(frozen).read_bytes()).hexdigest() != sha:
            raise ValueError("scoped_worker_frozen_input_mismatch")
        self.parent,self.plan,self.transport=parent,original_plan,transport
        self.worker,self.frozen,self.sha,self.output=worker,frozen,sha,output
        self.credentials,self.market_reads=credentials,market_reads
        self.source_session,self.custody_policy=source_session,custody_policy
        self.process=None
        self.commands=[]
        self.busy=False
        self._closed=False
        self._failure=None
        self._stderr_task=None
        self._stderr_problem=None
        self._stderr_bytes=0
        self._stderr_sha=hashlib.sha256()
        self._stdout_bytes=0
        self._stdout_sha=hashlib.sha256()
        self._shutdown_task=None
        self.launch=None

    async def _drain_stderr(self):
        try:
            while chunk := await self.process.stderr.read(8192):
                self._stderr_bytes += len(chunk)
                self._stderr_sha.update(chunk)
                if self._stderr_bytes > self.STDERR_BYTES:
                    if not self._stderr_problem.done():
                        self._stderr_problem.set_result('scoped_worker_stderr_overflow')
                # Keep draining during termination; never retain private protocol text.
        except Exception:
            if not self._stderr_problem.done():
                self._stderr_problem.set_result('scoped_worker_stderr_read_failed')

    async def command(self, command):
        if self._closed or self._failure:
            raise SourceSafetyStop('scoped_worker_terminal_no_restart')
        resolve_parent(self.parent,plan=self.plan)
        if self.busy: raise SourceSafetyStop('scoped_worker_concurrent_command')
        self.busy=True
        started=time.monotonic()
        work=None
        try:
            from app.services.kiwoom_participant_session import ParticipatingSession
            if type(self.source_session) is not ParticipatingSession:
                raise SourceSafetyStop('scoped_source_parent_delegation_required')
            with self.source_session.operation():
                self._stderr_problem = self._stderr_problem or asyncio.get_running_loop().create_future()
                work=asyncio.create_task(self._command(command))
                done,_=await asyncio.wait((work,self._stderr_problem),timeout=self.COMMAND_SECONDS,
                    return_when=asyncio.FIRST_COMPLETED)
                if self._stderr_problem in done:
                    raise SourceSafetyStop(self._stderr_problem.result())
                if work not in done:
                    raise SourceSafetyStop('scoped_worker_command_deadline')
                return work.result()
        except BaseException as exc:
            self._failure='CANCELLED' if isinstance(exc,asyncio.CancelledError) else 'COMMAND_FAILED'
            if work is not None and not work.done():
                work.cancel()
            if work is not None:
                await asyncio.gather(work,return_exceptions=True)
            try:
                await self.shutdown()
            finally:
                durable_json(self.output/'command-failure.json',dict(
                    command_sha256=digest(command),exception_type=type(exc).__name__,
                    state=self._failure,elapsed_seconds=time.monotonic()-started,
                    stdout_bytes_withheld=self._stdout_bytes,stdout_sha256=self._stdout_sha.hexdigest(),
                    stderr_bytes_withheld=self._stderr_bytes,stderr_sha256=self._stderr_sha.hexdigest(),
                    restart_allowed=False),exclusive=True)
            raise
        finally:
            self.busy=False

    async def _command(self, command):
        self._stdout_bytes=0
        self._stdout_sha=hashlib.sha256()
        if self.process is None:
            from app.services.scoped_worker_launch import prepare
            self.launch=prepare(self)
            durable_json(self.output/'launch-policy.json',{k:v for k,v in self.launch.items()
                if k!='argv'},exclusive=True)
            self.process=await asyncio.create_subprocess_exec(*self.launch['argv'],
                stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,limit=self.STDOUT_LINE_BYTES,
                env=self.launch['env'],cwd=self.launch['cwd'],close_fds=True)
            self._stderr_task=asyncio.create_task(self._drain_stderr())
            durable_json(self.output/'process-start.json',dict(pid=self.process.pid,start=time.time(),
                launch_contract=self.launch['contract'],policy_sha256=self.launch['policy_sha256'],
                test_only=self.launch['test_only'],uid=self.launch['uid'],
                worker_sha256=hashlib.sha256(Path(self.worker).read_bytes()).hexdigest()),exclusive=True)
            self.process.stdin.write(encoded(self.credentials)+b'\n')
            self.credentials=None
        self.source_session._check()
        self.process.stdin.write(encoded(command)+b'\n')
        await self.process.stdin.drain()
        before=set(self.transport.dispatcher.results)
        while True:
            line=await asyncio.wait_for(self.process.stdout.readline(),timeout=self.LINE_SECONDS)
            self._stdout_bytes+=len(line)
            self._stdout_sha.update(line)
            if self._stdout_bytes>self.STDOUT_COMMAND_BYTES:
                raise SourceSafetyStop('scoped_worker_stdout_overflow')
            resolve_parent(self.parent,plan=self.plan)
            if not line: raise SourceSafetyStop('scoped_worker_stopped')
            value=json.loads(line)
            if set(value)=={'wire'}:
                r=value['wire']
                request=httpx.Request(r['method'],r['url'],headers=r['headers'],
                    content=base64.b64decode(r['body_b64'],validate=True))
                try:
                    response=await self.transport.handle_async_request(request)
                    try:
                        await response.aread()
                        answer=dict(status=response.status_code,headers=list(response.headers.multi_items()),
                            body_b64=base64.b64encode(response.content).decode())
                    finally:
                        await response.aclose()
                except httpx.TransportError:
                    answer=dict(error='SEALED_TRANSPORT_ERROR')
                self.process.stdin.write(encoded({'response':answer})+b'\n')
                await self.process.stdin.drain()
            elif set(value)=={'progress'}:
                row=value['progress']
                durable_json(self.output/('progress-'+str(row['logical'])+'.json'),row,exclusive=True)
            elif set(value)=={'attestation'}:
                durable_json(self.output/'effective-settings.json',value['attestation'],exclusive=True)
            elif set(value)=={'result'}:
                row=dict(command=command,result_sha256=digest(value['result']),
                    sealed_receipts={k:self.transport.dispatcher.results[k]['receipt_sha256']
                        for k in sorted(set(self.transport.dispatcher.results)-before)})
                self.commands.append(row)
                durable_json(self.output/f'command-{len(self.commands):03d}.json',row,exclusive=True)
                return value['result']
            else: raise SourceSafetyStop('scoped_worker_protocol_shape')

    async def handle_async_request(self,request):
        params=dict(request.url.params)
        for key in ('count','indicator_limit'):
            if key in params: params[key]=int(params[key])
        matches=[r for r in self.market_reads if r.params==params]
        if request.method!='GET' or request.url.path!='/ohlcv' or len(matches)!=1:
            raise SourceSafetyStop('scoped_market_rpc_not_planned')
        result=await self.command({'market':matches[0].symbol})
        return httpx.Response(result.get('status',502) if isinstance(result.get('status'),int) else 502,
            json=result.get('body',{'error':'original_owner_rejected'}),request=request)

    async def aclose(self): pass

    async def shutdown(self):
        self._closed=True
        self.credentials=None
        if self._shutdown_task is None:
            self._shutdown_task=asyncio.create_task(self._shutdown())
        try:
            await asyncio.shield(self._shutdown_task)
        except asyncio.CancelledError:
            # Caller cancellation does not leave a private Worker running.
            await self._shutdown_task
            raise

    async def _shutdown(self):
        if self.process is None: return
        actions=[]
        try:
            if self.process.returncode is None and not self._failure:
                self.process.stdin.write(encoded({'close':True})+b'\n')
                await asyncio.wait_for(self.process.stdin.drain(),timeout=self.CLOSE_SECONDS)
                self.process.stdin.close()
                await asyncio.wait_for(self.process.wait(),timeout=self.CLOSE_SECONDS)
        except (BrokenPipeError,ConnectionResetError,asyncio.TimeoutError):
            self._failure=self._failure or 'CLOSE_FAILED'
        if self.process.returncode is None:
            actions.append('terminate')
            try:self.process.terminate()
            except ProcessLookupError:pass
            try:await asyncio.wait_for(self.process.wait(),timeout=self.TERMINATE_SECONDS)
            except asyncio.TimeoutError:
                actions.append('kill')
                try:self.process.kill()
                except ProcessLookupError:pass
                try:await asyncio.wait_for(self.process.wait(),timeout=self.KILL_SECONDS)
                except asyncio.TimeoutError:self._failure='UNREAPED_PROCESS'
        if self._stderr_task is not None:
            try:await asyncio.wait_for(asyncio.shield(self._stderr_task),timeout=self.KILL_SECONDS)
            except asyncio.TimeoutError:
                self._failure=self._failure or 'STDERR_NOT_CLOSED'
                self._stderr_task.cancel()
                await asyncio.gather(self._stderr_task,return_exceptions=True)
        if self._stderr_problem is not None and self._stderr_problem.done():
            self._failure=self._failure or 'STDERR_FAILED'
        # No arbitrary exception text or RPC line is an exportable receipt.
        durable_json(self.output/'process-end.json',dict(pid=self.process.pid,end=time.time(),
            exit=self.process.returncode,stderr_bytes_withheld=self._stderr_bytes,
            stderr_sha256=self._stderr_sha.hexdigest(),shutdown_actions=actions,
            failure=self._failure,restart_allowed=False,
            state='NORMAL_END' if self.process.returncode==0 and not self._failure else 'FAILED_OR_CANCELLED'),exclusive=True)
        if self.process.returncode is None:
            raise SourceSafetyStop('scoped_worker_unreaped_process')
