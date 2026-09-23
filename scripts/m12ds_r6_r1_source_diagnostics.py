"""Bounded, no-model diagnostics for the existing approved market sources."""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import traceback
from zoneinfo import ZoneInfo

import httpx


KST = ZoneInfo('Asia/Seoul')
ALLOWED_PATHS = {'/ohlcv', '/api/dostk/sect'}
ALLOWED_PARAMETERS = {'symbol', 'market', 'periods', 'count', 'include_indicators',
                      'indicator_limit', 'adjusted', 'mrkt_tp', 'inds_cd', 'amt_qty_tp',
                      'base_dt', 'stex_tp'}
SECRET_KEYS = {'token', 'access_token', 'refresh_token', 'appkey', 'secretkey',
               'authorization', 'api_key', 'x-api-key', 'next-key', 'next_key'}


def sanitize(value):
    if isinstance(value, dict):
        return {k: ('[REDACTED]' if k.lower() in SECRET_KEYS else sanitize(v))
                for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    return value


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, default=str)
        stream.write('\n')


def shape(value):
    if isinstance(value, dict):
        return {k: shape(v) for k, v in value.items()}
    if isinstance(value, list):
        return {'row_count': len(value), 'first_row_schema': shape(value[0]) if value else None}
    return type(value).__name__


class DiagnosticTransport(httpx.AsyncBaseTransport):
    def __init__(self, root, delegate=None):
        self.root = root
        self.delegate = delegate or httpx.AsyncHTTPTransport()
        self.rows = []

    async def handle_async_request(self, request):
        response = await self.delegate.handle_async_request(request)
        if request.url.path not in ALLOWED_PATHS:
            return response  # In particular, never retain token requests/responses.
        body = await response.aread()
        payload = json.loads(body)
        params = dict(request.url.params) if request.method == 'GET' else json.loads(request.content)
        if not set(params) <= ALLOWED_PARAMETERS:
            raise ValueError('diagnostic_request_parameter_not_allowlisted')
        row = {'endpoint': request.url.path, 'host': request.url.host,
               'action': request.headers.get('api-id'), 'request_parameters': params,
               'http_status': response.status_code, 'raw_response_sha256': sha256(body).hexdigest(),
               'response_shape': shape(payload), 'response': sanitize(payload),
               'received_utc': datetime.now(timezone.utc).isoformat()}
        self.rows.append(row)
        put(self.root / f'response-{len(self.rows):02d}.json', row)
        return response

    async def aclose(self):
        await self.delegate.aclose()


def exception_receipt(exc):
    return {'type': type(exc).__name__, 'message': str(exc),
            'stack': traceback.format_exception(type(exc), exc, exc.__traceback__)}


async def run(root):
    from app.macro.providers.market import OhlcvMarketProvider, completed_market_bars
    from app.providers.kiwoom_rest_client import KiwoomRestClient
    from app.services.kiwoom_kr_market_context_service import (
        KiwoomKrMarketContextService, MARKETS, SECTOR_ENDPOINT,
    )
    from app.services.market_session import korea_market_session, us_market_session
    from app.services.ohlcv_completed_bar_finality_service import (
        annotate_normalized_bar, assess_completed_bar_finality,
    )

    root.mkdir(parents=True, exist_ok=False)
    at = datetime.now(KST)
    us_date = us_market_session(at).latest_completed_regular_session_date
    kr_date = korea_market_session(at).latest_completed_regular_session_date
    put(root / 'start.json', {'at': at, 'utc': at.astimezone(timezone.utc),
        'us_completed_session': us_date, 'kr_completed_session': kr_date,
        'model_calls': 0, 'db_writes': 0, 'sends': 0, 'source_retries': 0})
    transport = DiagnosticTransport(root / 'private/us')
    result = await OhlcvMarketProvider(transport=transport).collect(at)
    us = []
    for response in transport.rows:
        payload = response['response']
        raw_rows = payload.get('periods', {}).get('daily', [])
        row = {'symbol': response['request_parameters']['symbol'],
               'provider': payload.get('meta', {}).get('provider'),
               'http_status': response['http_status'],
               'raw_response_sha256': response['raw_response_sha256'],
               'raw_dates': [r.get('date') for r in raw_rows],
               'metadata': payload.get('meta'), 'selected_current_row': None,
               'client_cache_or_fallback_used': False,
               'server_cache_path_version': 'not_exposed_unless_in_source_metadata'}
        row['bar_finality'] = []
        for i, raw in enumerate(sorted(raw_rows, key=lambda r: str(r.get('date') or ''))):
            annotated = annotate_normalized_bar(raw, provider=row['provider'] or '',
                market='US', timeframe='daily', has_later_chart_row=i < len(raw_rows)-1)
            row['bar_finality'].append({'date': raw.get('date'),
                'assessment': assess_completed_bar_finality(annotated, cutoff=us_date).model_dump(mode='json')})
        try:
            latest, previous, receipt = completed_market_bars(payload, at)
            row.update(status='PASS', selected_current_row=latest, previous=previous, receipt=receipt)
        except (ValueError, TypeError, KeyError) as exc:
            row.update(status='FAIL', exception=exception_receipt(exc))
        us.append(row)
    put(root / 'us-diagnostic.json', {'cutoff': at, 'completed_session': us_date,
        'rows': us, 'warnings': result.warnings, 'observations': len(result.observations)})
    print(json.dumps({'us_rows': len(us), 'us_pass': sum(r['status']=='PASS' for r in us)}), flush=True)

    # Retain both market families even when the first native validation rejects.
    kr_transport = DiagnosticTransport(root / 'private/kr')
    client = KiwoomRestClient(transport=kr_transport, max_retries=0)
    service = KiwoomKrMarketContextService(client, max_pages=1)
    kr = []
    for market, spec in MARKETS.items():
        bodies = [
            ('ka20001', {'mrkt_tp': spec['ka20001_market'], 'inds_cd': spec['code']}),
            ('ka20003', {'inds_cd': spec['code']}),
            ('ka20009', {'mrkt_tp': spec['ka20001_market'], 'inds_cd': spec['code']}),
            ('ka10051', {'mrkt_tp': spec['ka10051_market'], 'amt_qty_tp': '0',
                         'base_dt': kr_date.strftime('%Y%m%d'), 'stex_tp': '3'}),
        ]
        row = {'market': market, 'session_date': kr_date, 'observed_at': at}
        values = {}
        try:
            for action, body in bodies:
                response = await service._request(api_id=action, endpoint=SECTOR_ENDPOINT, body=body)
                values[action] = response.payload
            service._validate_session_identity(session_date=kr_date, observed_at=at,
                current=values['ka20001'], sectors=values['ka20003'], history=values['ka20009'],
                market=market, code=spec['code'])
            row['status'] = 'PASS'
        except (ValueError, TypeError, RuntimeError, httpx.HTTPError) as exc:
            row.update(status='FAIL', exception=exception_receipt(exc))
        row['payload_hashes'] = [r['payload_sha256'] for r in service._archive_rows]
        kr.append(row)
    put(root / 'kr-diagnostic.json', {'rows': kr, 'provider_calls': asdict(client.stats)})
    put(root / 'complete.json', {'at': datetime.now(KST), 'model_calls': 0,
        'production_writes': 0, 'source_http_responses': len(transport.rows)+len(kr_transport.rows),
        'diagnostic_only': True})
    print(json.dumps({'kr_rows': len(kr), 'kr_pass': sum(r['status']=='PASS' for r in kr)}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    args = parser.parse_args()
    os.environ.update(THESIS_MONITOR_ENV_FILE='/Users/sskim/Codex/thesis-monitor/.env',
        DATA_DIR=str(args.root / 'isolated-data'), DATABASE_URL='sqlite:///:memory:',
        TELEGRAM_BOT_TOKEN='', TELEGRAM_CHAT_ID='', TELEGRAM_TEST_CHAT_ID='',
        NOTIFICATION_DRY_RUN='true', PERSISTENCE_V2_WRITER_ENABLED='false',
        PERSISTENCE_V2_OUTBOX_DELIVERY_ENABLED='false')
    asyncio.run(run(args.root.resolve()))
