"""Production source owners against the R4 isolated database, never production state."""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime
import json
import hashlib
import logging
import os
from pathlib import Path

from scripts.m12ds_r4_source_preflight import KST, OPERATING, REPO, git_state, helpers


async def run(root):
    root = root.resolve()
    data = root / 'private/isolated-data'
    report = root / 'report'

    def read(name):
        return json.loads((root / name).read_bytes())

    def put(name, value):
        helpers.write_json(root / name, value)

    if (report / 'collection-start.json').exists():
        raise ValueError('one_current_collection_only')
    if read('report/night-source-gate.json')['status'] != 'PASS':
        raise ValueError('night_source_gate_required')
    states = {str(p): git_state(p) for p in (REPO, OPERATING)}
    if any(s['status'] for s in states.values()):
        raise ValueError('clean_collection_commit_required')
    source_db = OPERATING / 'data/thesis_monitor.sqlite3'
    before_db = helpers.source_db_identity(source_db)
    helpers.copy_runtime_state(OPERATING / 'data', data)
    os.environ.update(THESIS_MONITOR_ENV_FILE=str(OPERATING / '.env'), DATA_DIR=str(data),
        DATABASE_URL=f'sqlite:///{data / source_db.name}', MASSIVE_CACHE_DIR=str(data / 'cache/massive'),
        NOTIFICATION_DRY_RUN='true', NOTIFICATION_RECIPIENT_CLASS='test', AI_REVIEW_MODE='shadow',
        PERSISTENCE_V2_WRITER_ENABLED='false', PERSISTENCE_V2_OUTBOX_DELIVERY_ENABLED='false',
        TELEGRAM_BOT_TOKEN='', TELEGRAM_CHAT_ID='', TELEGRAM_TEST_CHAT_ID='')
    os.chdir(root / 'private')
    logging.basicConfig(filename=root / 'private/collection.log', level=logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.CRITICAL)
    logging.getLogger('httpcore').setLevel(logging.CRITICAL)
    from sqlmodel import Session
    from app.config import get_settings
    from app.database import engine, init_db
    from app.macro.kr_close import run_kr_close_market_briefing
    from app.macro.providers.base import CollectedObservation
    from app.macro.service import run_macro_monitor
    from app.macro.storage import persist_observation
    from app.services.ai_review_service import write_ai_review_packet
    from app.services.daily_monitor_service import run_daily_monitor
    from app.services.financial_backfill_service import backfill_financial_snapshots
    from app.services.kiwoom_kr_market_context_service import collect_and_persist_kiwoom_market_context
    from app.services.market_session import korea_market_session, us_market_session
    from app.services.morning_gate import _replace_night_observations, _write_gate_metadata
    from app.services.sec_financial_snapshot_service import SecFinancialSnapshotService
    from app.services.us_exchange_breadth_service import collect_and_persist_us_exchange_breadth

    settings = get_settings()
    if (Path(settings.data_dir).resolve() != data or settings.include_mock_provider
            or settings.telegram_bot_token or settings.telegram_chat_id or not settings.notification_dry_run
            or settings.persistence_v2_writer_enabled or settings.persistence_v2_outbox_delivery_enabled):
        raise ValueError('source_isolation_failed')
    init_db()
    observed = datetime.now(KST)
    ledger = []
    foreign_raw = []

    async def record_foreign_response(response):
        if response.url.host != 'www.sec.gov' or not response.url.path.startswith('/Archives/edgar/data/'):
            return
        body = await response.aread()
        digest = hashlib.sha256(body).hexdigest()
        path = root / 'source/sec-foreign-raw' / (digest + '.payload')
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(body)
        foreign_raw.append(dict(url=str(response.url), status=response.status_code,
            sha256=digest, bytes=len(body), path=str(path.relative_to(root)), observed_at=datetime.now(KST)))
        put('report/sec-foreign-raw-manifest.json', foreign_raw)
    put('report/collection-start.json', {'at': observed, 'git': states, 'source_db': before_db,
        'night_snapshot_sha256': helpers.sha256_file(root / 'source/night-provider.json'),
        'model_calls': 0, 'controller_retries': 0})

    async def call(name, fn):
        print(json.dumps({'source': name, 'state': 'START'}), flush=True)
        row = {'owner': name, 'started_at': datetime.now(KST)}
        try:
            result = await asyncio.wait_for(fn(), timeout=1200)
            put('private/source-results/' + name + '.json', helpers.json_value(result))
            row['status'] = 'RETURNED'
        except Exception as exc:
            row.update(status='FAILED', error_type=type(exc).__name__)
            logging.exception('source owner %s failed', name)
        row['completed_at'] = datetime.now(KST)
        ledger.append(row)
        put('report/source-call-ledger.json', {'rows': ledger, 'controller_retries': 0})
        print(json.dumps({'source': name, 'state': row['status']}), flush=True)

    with Session(engine) as session:
        population = helpers.current_population(session, observed)
        prior = read('report/monitored-population.json')
        if any(sorted(population['markets'][m]['tickers']) != sorted(prior['markets'][m]['tickers']) for m in ('us', 'kr')):
            raise ValueError('population_changed_since_preflight')
        telemetry_before = helpers.telemetry_snapshot(session)
        put('report/source-configuration.json', {'SEC_USER_AGENT': bool(settings.sec_user_agent),
            'OPENDART_API_KEY': bool(settings.opendart_api_key), 'secret_values_exported': False})
        for ticker in sorted(population['markets']['us']['tickers']):
            await call('sec-financial-' + ticker, lambda t=ticker: SecFinancialSnapshotService(response_hook=record_foreign_response).refresh(
                session, t, settings.sec_user_agent))
        for ticker in sorted(population['markets']['kr']['tickers']):
            await call('opendart-financial-' + ticker, lambda t=ticker: backfill_financial_snapshots(
                session, t, years=1, provider='opendart'))
        # Each market owns its actual collection/session cutoff, not the other market's date.
        us_at = datetime.now(KST)
        us_session = us_market_session(us_at)
        await call('macro', lambda: run_macro_monitor(session, run_date=us_at.date(), force=True,
            excluded_provider_names={'krx_night_futures'}, as_of=us_at,
            queue_notifications=False, dispatch_notifications=False))
        await call('us-breadth', lambda: collect_and_persist_us_exchange_breadth(
            session_date=us_session.latest_completed_regular_session_date, observed_at=us_at))
        rows = []
        probe = read('source/night-probe.json')
        for values in read('source/night-provider.json')['observations']:
            values['observed_at'] = datetime.fromisoformat(values['observed_at'])
            row, _ = persist_observation(session, 'krx_night_futures', CollectedObservation(**values), us_at)
            from datetime import date
            rows.append(helpers.serialized_market_observation(row, date.fromisoformat(probe['expected_reference_date'])))
        _replace_night_observations(session, us_at.date(), rows)
        _write_gate_metadata(session, us_at.date(), {'state': 'ready',
            'expected_session': probe['expected_reference_date'], 'expected_reference_date': probe['expected_reference_date'],
            'query_attempted': True, 'first_query_at': probe['fetched_at'], 'last_query_at': probe['fetched_at'],
            'ready_products': [r['series_code'] for r in rows], 'retry_count': 0, 'deadline_reached': True})
        await call('us-stock-sources', lambda: run_daily_monitor(session, run_date=us_at.date(), force=True,
            market_scope='us', as_of=us_at, queue_notifications=False, dispatch_notifications=False))
        kr_at = datetime.now(KST)
        kr_session = korea_market_session(kr_at)
        kr_date = kr_session.latest_completed_regular_session_date
        await call('kr-close-market', lambda: run_kr_close_market_briefing(session, kr_date, as_of=kr_at,
            force=True, queue_notifications=False, dispatch_notifications=False))
        await call('kr-market-internals', lambda: collect_and_persist_kiwoom_market_context(
            session_date=kr_date, observed_at=kr_at))
        await call('kr-stock-sources', lambda: run_daily_monitor(session, run_date=kr_at.date(), force=True,
            market_scope='kr', as_of=kr_at, queue_notifications=False, dispatch_notifications=False))
        packets = []
        for market, at in (('us', us_at), ('kr', kr_at)):
            result = write_ai_review_packet(session, at.date(), market, generated_at=at)
            if result.path:
                packet = helpers.read_json(Path(result.path))
                put('private/current-packets/' + market + '.json', packet)
                packets.append(market)
            put('report/' + market + '-packet-structure.json', {'status': result.status,
                'packet_present': market in packets, 'observed_at': at})
        put('report/current-market-sessions.json', {'us': {'observed_at': us_at,
            'latest_completed_regular_session_date': us_session.latest_completed_regular_session_date, 'state': us_session.session},
            'kr': {'observed_at': kr_at, 'latest_completed_regular_session_date': kr_date, 'state': kr_session.session}})
        put('report/provider-telemetry.json', {'rows': [{k: v for k, v in r.items() if k != 'error_reason'}
            for r in helpers.telemetry_delta(telemetry_before, helpers.telemetry_snapshot(session))]})
    after_db = helpers.source_db_identity(source_db)
    unchanged = before_db == after_db and states == {str(p): git_state(p) for p in (REPO, OPERATING)}
    put('report/collection-complete.json', {'at': datetime.now(KST), 'packet_markets': sorted(packets),
        'production_db_unchanged': before_db == after_db, 'source_and_operating_code_unchanged': unchanged,
        'model_calls': 0, 'production_send': 0, 'production_recipient_intent': 0, 'scheduler_changes': 0})
    if not unchanged:
        raise ValueError('production_or_source_drift')
    print(json.dumps({'collection': 'COMPLETE', 'packet_markets': sorted(packets)}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    asyncio.run(run(parser.parse_args().root))
