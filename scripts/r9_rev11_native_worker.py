"""Native source owner over private stdio; this process has no network transport.

The controller handles only sealed requests. Private protocol bytes (including
credential exchanges) must never be logged or included in report artifacts.
"""
import argparse
import base64
import contextlib
import hashlib
import json
from pathlib import Path
import socket
import sys
import traceback
from types import SimpleNamespace

import httpx

from scripts import unified_stock_source_worker as stock_worker
from app.services.native_completed_market import select_completed_daily_rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--owner-root', type=Path, required=True)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    raw = args.input.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.sha256:
        raise ValueError('native_input_hash_mismatch')
    frozen = json.loads(raw)
    def no_network(*args, **kwargs):
        raise ValueError('native_direct_network_denied')
    socket.socket.connect = socket.socket.connect_ex = socket.getaddrinfo = no_network
    for key in list(sys.modules):
        if key == 'app' or key.startswith('app.'):
            del sys.modules[key]
    sys.path.insert(0, str(args.owner_root))
    from app.config import Settings
    from app.providers import kiwoom as owner
    from app.services.ohlcv_service import OhlcvService
    from app.services.symbol_resolver import SymbolResolver
    settings = Settings(_env_file=args.owner_root / '.env')
    if stock_worker.owner_configuration(args.owner_root, settings) != frozen['native_owner']:
        raise ValueError('native_owner_configuration_drift')
    output = sys.stdout
    def emit(value):
        output.write(json.dumps(value, ensure_ascii=False) + '\n')
        output.flush()
    def post(url, *, json, headers, timeout):
        request = httpx.Request('POST', url, json=json, headers=headers)
        emit({'wire': dict(method=request.method, url=str(request.url), headers=list(request.headers.multi_items()),
                           body_b64=base64.b64encode(request.content).decode())})
        line = sys.stdin.readline()
        if not line:
            raise ValueError('controller_disconnected')
        value = __import__('json').loads(line)
        if set(value) != {'response'}:
            raise ValueError('controller_response_required')
        r = value['response']
        if r.get('error'):
            raise httpx.TransportError('sealed_controller_transport_failed')
        return httpx.Response(r['status'], content=base64.b64decode(r['body_b64'], validate=True),
                              headers=r['headers'], request=request)
    bounded = settings.model_copy(update={'kiwoom_max_retries': 0, 'kiwoom_timeout_seconds': 600})
    owner.httpx = SimpleNamespace(post=post, HTTPError=httpx.HTTPError)
    class CompletedMarketProvider(owner.KiwoomProvider):
        def _normalize_rows(self, rows, count):
            target = frozen.get('latest_completed_us_session')
            if not target:
                raise ValueError('native_market_frozen_session_missing')
            normalized = super()._normalize_rows(rows, max(count, len(rows)))
            return select_completed_daily_rows(normalized, target_session=target, count=count)

    service = OhlcvService(SymbolResolver(settings.sector_map_path),
        CompletedMarketProvider(owner.KiwoomClient(bounded, owner.KiwoomAuth(bounded))))
    class Client:
        def __enter__(self):
            return self

        def __exit__(self, *unused):
            return False

        def post(self, *a, **kw):
            return post(*a, **kw)
    class Progress:
        def write(self, text):
            if text.strip():
                emit({'progress': json.loads(text)})

        def flush(self):
            pass
    stocks_done, discovery_done, replay_done, symbols = False, False, False, set()
    for line in sys.stdin:
        command = json.loads(line)
        if command == {'close': True}:
            break
        if command == {'replay-stocks': True}:
            if not stocks_done or replay_done:
                raise ValueError('native_stock_replay_state_invalid')
            replay_done = True
            original_datetime = owner.datetime
            try:
                stock_worker.replay(frozen['stock_plan'], args.output / 'stocks', owner)
            finally:
                owner.datetime = original_datetime
            rows = json.loads((args.output / 'raw-owner-replay.json').read_bytes())
            emit({'result': {'status': 'PASS' if len(rows) == len(frozen['stock_plan']['reads'])
                and all(r['status'] == 'PASS' for r in rows) else 'SOURCE_PARTIAL', 'rows': rows}})
        elif command == {'discovery': True}:
            if discovery_done:
                raise ValueError('native_discovery_repeat_denied')
            discovery_done = True
            for exchange in ('ND', 'NY', 'NA'):
                service.provider._get_us_stock_list(exchange)
            emit({'result': {'status': 'DISCOVERY_CAPTURE_COMPLETE_NOT_QUALIFIED'}})
        elif command == {'stocks': True}:
            if stocks_done:
                raise ValueError('native_stock_repeat_denied')
            stocks_done = True
            stock_worker.httpx = SimpleNamespace(Client=lambda **kw: Client(), HTTPTransport=lambda **kw: None,
                                                 HTTPError=httpx.HTTPError)
            with contextlib.redirect_stdout(Progress()):
                stock_worker.acquire(frozen['stock_plan'], args.output / 'stocks', owner, bounded)
            owner.httpx = SimpleNamespace(post=post, HTTPError=httpx.HTTPError)
            emit({'result': {'status': 'STOCK_CAPTURE_COMPLETE_NOT_QUALIFIED'}})
        elif set(command) == {'market'} and command['market'] in frozen['us_market_symbols'] and command['market'] not in symbols:
            if not discovery_done:
                raise ValueError('native_discovery_required')
            symbol = command['market']
            symbols.add(symbol)
            try:
                value = service.get_ohlcv(symbol=symbol, market='US', periods=['daily'], count=2,
                    include_indicators=False, indicator_limit=0, adjusted=True)
                result = dict(status=200, body=value.model_dump(mode='json'))
            except Exception as exc:
                frames = traceback.extract_tb(exc.__traceback__)[-4:]
                allowed = {'native_market_frozen_session_missing', 'native_market_exact_two_completed_rows_required',
                    'native_market_duplicate_session', 'native_market_target_completed_session_missing',
                    'native_market_adjacent_completed_baseline_missing'}
                result = dict(status=502, body={'error_class': type(exc).__name__,
                    'contract_error': str(exc) if str(exc) in allowed else 'native_market_owner_failure',
                    'stack': [{'module': Path(f.filename).name, 'function': f.name, 'line': f.lineno} for f in frames]})
            emit({'result': result})
        else:
            raise ValueError('native_unplanned_command')


if __name__ == '__main__':
    main()
