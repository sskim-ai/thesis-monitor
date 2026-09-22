"""One official source read for a hash-matched diagnostic, never source promotion."""
from __future__ import annotations

import argparse
import asyncio
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import sqlite3

from scripts.m12ds_r4_source_preflight import OPERATING, helpers


def diagnose(payload, snapshot):
    from app.services.sec_financial_snapshot_service import (
        _business_occurrence_error, _duration_days, _facts, _parse_date,
    )

    expected = {row['source_payload_sha256'] for row in json.loads(snapshot['raw_financial_fields'])}
    actual = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if expected != {actual}:
        raise ValueError('diagnostic_payload_differs_from_collected_source')
    fy = snapshot['fiscal_year']
    fp = {'H1': 'Q2'}.get(snapshot['period_type'], snapshot['period_type'])
    filed, end = date.fromisoformat(snapshot['filing_date']), date.fromisoformat(snapshot['financial_period_end'])
    fields = {}
    for field in ('revenue', 'operating_income'):
        entries = _facts(payload, field)
        error = _business_occurrence_error(entries, fy, fp, filed, end)
        candidates = [r for r in entries if r.get('fy') == fy and r.get('fp') == fp
                      and _parse_date(r.get('filed')) == filed and _parse_date(r.get('end')) == end
                      and 0 < _duration_days(r) <= 130]
        duration = min((_duration_days(r) for r in candidates), default=None)
        peers = [r for r in candidates if _duration_days(r) == duration]
        fields[field] = {'error': error, 'selected_value': snapshot[field], 'peer_occurrences': peers}
    return {'source_payload_sha256': actual, 'hash_matches_original_collection': True,
            'ticker': snapshot['ticker'], 'period_end': str(end), 'filing_date': str(filed),
            'source_document_id': snapshot['source_filing_id'], 'fields': fields,
            'source_promotion': False, 'packet_rewritten': False, 'model_calls': 0}


async def run(root, ticker):
    target = root / 'report/source-conflict-diagnostic.json'
    if target.exists():
        raise ValueError('diagnostic_already_exists')
    os.environ.update(THESIS_MONITOR_ENV_FILE=str(OPERATING / '.env'),
                      NOTIFICATION_DRY_RUN='true', TELEGRAM_BOT_TOKEN='', TELEGRAM_CHAT_ID='')
    import httpx
    from app.config import get_settings

    database = root / 'private/isolated-data/thesis_monitor.sqlite3'
    before = helpers.sha256_file(database)
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute('select * from financialsnapshot where ticker=? '
                                 'and provider=? order by financial_period_end desc, filing_date desc limit 1',
                                 (ticker, 'sec_companyfacts')).fetchone()
        snapshot = dict(row)
    bindings = helpers.read_json(root / 'report/issuer-security-binding.json')['rows']
    binding = next(row for row in bindings if row['ticker'] == ticker)
    cik = str(binding['issuer_id']).removeprefix('CIK:').removeprefix('SEC:').zfill(10)
    if not cik.isdecimal():
        raise ValueError('numeric_sec_cik_required')
    async with httpx.AsyncClient(timeout=30, headers={'User-Agent': get_settings().sec_user_agent}) as client:
        response = await client.get(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json')
        response.raise_for_status()
    result = diagnose(response.json(), snapshot)
    helpers.write_json(root / 'source/sec-diagnostic-payload.json', response.json())
    result['raw_response_sha256'] = hashlib.sha256(response.content).hexdigest()
    result['provider_requests'] = 1
    result['isolated_db_unchanged'] = helpers.sha256_file(database) == before
    if not result['isolated_db_unchanged']:
        raise ValueError('unexpected_database_mutation')
    helpers.write_json(target, result)
    print(json.dumps({'status': 'DIAGNOSTIC_ONLY', 'ticker': ticker,
                      'errors': {k: v['error'] for k, v in result['fields'].items()},
                      'original_source_hash_matches': True, 'model_calls': 0}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--ticker', required=True)
    args = parser.parse_args()
    asyncio.run(run(args.root.resolve(), args.ticker))
