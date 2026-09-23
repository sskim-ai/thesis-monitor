import asyncio
import json

import httpx

from scripts.m12ds_r6_r1_source_diagnostics import DiagnosticTransport, sanitize


def test_sanitizer_nested_secret_fields():
    assert sanitize({'meta': [{'token': 'private', 'provider': 'official'}]}) == {
        'meta': [{'token': '[REDACTED]', 'provider': 'official'}]}


def test_transport_never_archives_auth_or_headers(tmp_path):
    async def exercise():
        transport = DiagnosticTransport(tmp_path, httpx.MockTransport(
            lambda req: httpx.Response(200, json={'token': 'secret', 'periods': {'daily': []}})))
        async with httpx.AsyncClient(transport=transport, base_url='https://example.test') as client:
            await client.post('/oauth2/token', json={'appkey': 'secret'})
            await client.get('/ohlcv', params={'symbol': 'SPY'}, headers={'X-API-Key': 'secret'})
        assert len(transport.rows) == 1
        receipt = json.loads((tmp_path / 'response-01.json').read_text())
        assert receipt['response']['token'] == '[REDACTED]'
        assert receipt['request_parameters'] == {'symbol': 'SPY'}
        assert 'secret' not in (tmp_path / 'response-01.json').read_text()
    asyncio.run(exercise())


def test_http_failure_keeps_native_error_separate_from_bar_parser(tmp_path):
    async def exercise():
        transport = DiagnosticTransport(tmp_path, httpx.MockTransport(
            lambda req: httpx.Response(502, json={'detail': 'upstream token HTTP 429'})))
        async with httpx.AsyncClient(transport=transport, base_url='https://example.test') as client:
            result = await client.get('/ohlcv', params={'symbol': 'XLC'}, headers={'X-API-Key':'private'})
            assert result.status_code == 502
        row = transport.rows[0]
        assert row['http_exception']['type'] == 'HTTPStatusError'
        assert '502' in row['http_exception']['message']
        assert row['http_exception']['stack']
        assert row['response']['detail'] == 'upstream token HTTP 429'
        assert 'private' not in json.dumps(row)
    asyncio.run(exercise())
