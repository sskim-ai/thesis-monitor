"""Offline subprocess probe of the new KIS pre-wire hook; no real sockets."""
from datetime import datetime, timedelta
import json
from pathlib import Path
import socket
import sys
from unittest.mock import patch

import httpx

from app.services import selected_run_lifecycle as lifecycle
from app.services.unified_snapshot_contract import digest
from scripts import kr8_kis_integration as kis


def main():
    binding_path, output_path, mode = sys.argv[1:]
    binding = json.loads(Path(binding_path).read_bytes())
    worker = lifecycle.SelectedRunLedger.attach_worker(binding)
    sent = []

    def denied(*args, **kwargs):
        raise AssertionError('REAL_NETWORK_FORBIDDEN')

    def wire(self, request):
        state = worker.state()
        assert state['pending'] and state['http_total'] == len(sent) + 1
        sent.append(request.method)
        if mode == 'transport':
            raise httpx.ConnectError('OFFLINE_INJECTED_TRANSPORT_FAILURE', request=request)
        return httpx.Response(403 if mode == 'forbidden' else 200)

    def auth(self):
        for _ in range(6):
            self.client.post('https://offline.invalid/oauth2/tokenP', json={})

    class Expired(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.now(tz) + timedelta(hours=2)

    plan = dict(contract='selected-original-kis-source-v1', static_hashes={},
        maximum_physical_HTTP=20, receipt_sha256=digest('OFFLINE_KIS_PLAN'))
    with patch.object(socket.socket, 'connect', denied), patch.object(socket, 'getaddrinfo', denied), \
            patch.object(kis, '_subjects', return_value=('999999',)), \
            patch.object(kis, 'semantic_inputs', return_value={}), \
            patch.object(kis.FreshProbe, 'authenticate', auth), \
            patch.object(httpx.HTTPTransport, 'handle_request', wire):
        if mode == 'ttl':
            with patch.object(lifecycle, 'datetime', Expired):
                terminal = kis.acquire(Path(output_path).parent/'kis', plan=plan,
                    credentials=kis.base.Credentials('OFFLINE_DUMMY_KEY', 'OFFLINE_DUMMY_SECRET'),
                    inventories={}, static=Path('.'), guard=lambda: None,
                    physical_accounting=worker, source_plan_sha256=digest('kr'))
        else:
            terminal = kis.acquire(Path(output_path).parent/'kis', plan=plan,
                credentials=kis.base.Credentials('OFFLINE_DUMMY_KEY', 'OFFLINE_DUMMY_SECRET'),
                inventories={}, static=Path('.'), guard=lambda: None,
                physical_accounting=worker, source_plan_sha256=digest('kr'))
    Path(output_path).write_text(json.dumps(dict(sent=len(sent), terminal=terminal,
        state=worker.state()['state'], real_HTTP=0, original_worker_frame_tested=False)))


if __name__ == '__main__':
    main()
