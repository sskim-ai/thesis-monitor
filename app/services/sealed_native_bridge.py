"""Private native-owner RPC; only the parent sealed transport has network access."""
import asyncio
import base64
import json
from pathlib import Path
import sys

import httpx

from app.services.unified_live_source_transport import SourceSafetyStop
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest, encoded


class SealedNativeBridge(httpx.AsyncBaseTransport):
    def __init__(self, *, owner_root, input_path, input_sha256, output, transport, market_reads):
        self.owner_root, self.input_path, self.input_sha256 = owner_root, input_path, input_sha256
        self.output, self.transport, self.market_reads = output, transport, tuple(market_reads)
        self.process = None
        self.busy = False
        self.progress = []
        self.commands = []
        self.exit_receipt = None

    async def command(self, command):
        if self.busy:
            raise SourceSafetyStop('native_concurrent_command_denied')
        self.busy = True
        before = set(self.transport.dispatcher.results)
        try:
            if self.process is None:
                if sha256_bytes(Path(self.input_path).read_bytes()) != self.input_sha256:
                    raise SourceSafetyStop('native_input_drift')
                self.process = await asyncio.create_subprocess_exec(sys.executable, '-m', 'scripts.r9_rev11_native_worker',
                    '--owner-root', str(self.owner_root), '--input', str(self.input_path), '--sha256', self.input_sha256,
                    '--output', str(self.output), stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE, limit=64 * 1024 * 1024)
            self.process.stdin.write(encoded(command) + b'\n')
            await self.process.stdin.drain()
            while True:
                line = await asyncio.wait_for(self.process.stdout.readline(), timeout=600)
                if not line:
                    raise SourceSafetyStop('native_worker_stopped')
                item = json.loads(line)
                if set(item) == {'wire'}:
                    r = item['wire']
                    request = httpx.Request(r['method'], r['url'], headers=r['headers'],
                        content=base64.b64decode(r['body_b64'], validate=True))
                    try:
                        response = await self.transport.handle_async_request(request)
                        await response.aread()
                        value = dict(status=response.status_code, headers=list(response.headers.multi_items()),
                                     body_b64=base64.b64encode(response.content).decode())
                    except httpx.TransportError:
                        value = {'error': 'TRANSPORT_ERROR'}
                    self.process.stdin.write(encoded({'response': value}) + b'\n')
                    await self.process.stdin.drain()
                elif set(item) == {'progress'}:
                    # Only the original role status is public; never retain RPC wire bytes.
                    self.progress.append(item['progress'])
                elif set(item) == {'result'}:
                    keys = sorted(set(self.transport.dispatcher.results) - before)
                    receipt = dict(command=command, result_sha256=digest(item['result']),
                        generation_id=self.transport.dispatcher.plan.generation_id,
                        sealed_receipts={key:self.transport.dispatcher.results[key]['receipt_sha256'] for key in keys},
                        native_input_sha256=self.input_sha256)
                    self.commands.append(receipt)
                    durable_json(Path(self.output)/f'command-{len(self.commands):03d}.json', receipt, exclusive=True)
                    return item['result']
                else:
                    raise SourceSafetyStop('native_protocol_unknown')
        finally:
            self.busy = False

    async def handle_async_request(self, request):
        params = dict(request.url.params)
        if request.method != 'GET' or request.url.path != '/ohlcv':
            raise SourceSafetyStop('native_market_route_denied')
        for name in ('count', 'indicator_limit'):
            params[name] = int(params[name])
        if params not in [r['params'] for r in self.market_reads]:
            raise SourceSafetyStop('native_market_query_not_frozen')
        result = await self.command({'market': params['symbol']})
        return httpx.Response(result['status'], json=result['body'], request=request)

    async def aclose(self):
        # Short-lived HTTP clients do not own the run's private child process.
        pass

    async def shutdown(self):
        if self.process is None:
            return
        if self.process.returncode is None:
            try:
                self.process.stdin.write(b'{"close":true}\n')
                await self.process.stdin.drain()
                _, error = await asyncio.wait_for(self.process.communicate(), timeout=10)
            except (TimeoutError, BrokenPipeError, ConnectionResetError):
                self.process.terminate()
                _, error = await self.process.communicate()
        else:
            _, error = await self.process.communicate()
        self.exit_receipt = dict(returncode=self.process.returncode, stderr_bytes=len(error),
            stderr_sha256=sha256_bytes(error), private_protocol_exported=False)


def require_complete_stock_window(read, receipt, normalized_rows):
    """The native owner may stop at a row target, never at an unresolved cap."""
    if receipt.get('status') != 'CAPTURED' or not receipt.get('pages') or not normalized_rows:
        raise ValueError('SOURCE_PARTIAL:stock_owner_failed_or_empty')
    pages = receipt['pages']
    last = pages[-1]['response_continuation']
    pending = str(last['cont_yn']).upper() == 'Y'
    if pending and not last['next_key']:
        raise ValueError('SOURCE_PARTIAL:missing_continuation_key')
    if pending and len(normalized_rows) < read.count:
        raise ValueError('SOURCE_PARTIAL:unresolved_consumer_window')
    if len(pages) > read.max_pages:
        raise ValueError('SOURCE_PARTIAL:page_bound_exceeded')
    return dict(status='PASS', consumer_rows=len(normalized_rows), requested_rows=read.count,
        source_exhausted=not pending, consumer_complete=True, source_pages=len(pages),
        configured_global_page_cap_modified=False)
