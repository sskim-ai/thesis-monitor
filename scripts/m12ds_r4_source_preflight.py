"""Fresh R4 registry/session/night preflight; no inference or delivery entrypoint."""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
from unittest.mock import patch
from zoneinfo import ZoneInfo

from scripts import m12cj_current_market_smoke as helpers

REPO = Path(__file__).resolve().parents[1]
OPERATING = Path('/Users/sskim/Codex/thesis-monitor')
KST = ZoneInfo('Asia/Seoul')


def git_state(path):
    return {'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=path, text=True).strip(),
            'status': subprocess.check_output(['git', 'status', '--porcelain'], cwd=path, text=True).strip()}


def gate(probe, canonical, rows):
    """Availability is not proven by cached or stale observations or empty HTTP 200."""
    errors = []
    if not probe.get('live_source'):
        errors.append('official_live_response_required')
    if not probe.get('night_session_usable') or probe.get('session_freshness') != 'fresh':
        errors.append('current_official_night_pair_unavailable')
    if not probe.get('finality_valid'):
        errors.append('night_finality_unverified')
    expected = probe.get('expected_reference_date')
    observations = probe.get('observations', [])
    for product in ('KOSPI200', 'KOSDAQ150'):
        selected = [r for r in observations if r['product'] == product]
        emitted = [r for r in canonical if r['raw_payload'].get('product') == product]
        if len(selected) != 1 or len(emitted) != 1:
            errors.append(product + ':exact_pair_and_canonical_required')
            continue
        item, fact = selected[0], emitted[0]
        if not (item['session_date'] == expected and item['reference_date_match'] and item['finality_valid']):
            errors.append(product + ':reference_or_finality_mismatch')
        if (fact['value'] != item['night_close'] or fact['previous_value'] != item['reference_price']
                or fact['change_value'] != item['point_change'] or fact['change_pct'] != item['change_pct']):
            errors.append(product + ':canonical_mapping_mismatch')
        for prefix in ('night', 'reference'):
            matches = [r for r in rows if r['row_identity'] == item[prefix + '_source_record_id']
                       and r['response_sha256'] == item[prefix + '_source_payload_sha256']]
            if len(matches) != 1:
                errors.append(product + ':' + prefix + '_raw_binding_missing_or_ambiguous')
        if not item['reference_price'] or abs(item['night_close'] - item['reference_price'] - item['point_change']) > 1e-7:
            errors.append(product + ':change_arithmetic')
        elif abs(item['point_change'] / item['reference_price'] * 100 - item['change_pct']) > 1e-7:
            errors.append(product + ':change_pct_arithmetic')
    return {'status': 'FAIL' if errors else 'PASS', 'errors': errors,
            'publication_unavailable_proven': False, 'empty_response_is_not_publication_proof': True,
            'owner': 'app.macro.providers.krx.KrxNightFuturesProvider',
            'downstream_render_status': 'NOT_RUN', 'production_send': 0, 'model_calls': 0}


async def run(root, generation_prefix='20260922-m12ds-r4-current-'):
    root = root.resolve()
    if root.exists():
        raise ValueError('new_r4_source_directory_required')
    root.mkdir(parents=True)
    root.chmod(0o700)
    data = root / 'private/isolated-data'
    data.mkdir(parents=True)
    (root / 'private').chmod(0o700)
    def put(name, value):
        helpers.write_json(root / name, value)

    initial = {str(p): git_state(p) for p in (REPO, OPERATING)}
    if any(s['status'] for s in initial.values()):
        raise ValueError('clean_source_collection_commit_required')
    source_db = OPERATING / 'data/thesis_monitor.sqlite3'
    before_db = helpers.source_db_identity(source_db)
    helpers.sqlite_backup(source_db, data / source_db.name)
    os.environ.update(THESIS_MONITOR_ENV_FILE=str(OPERATING / '.env'), DATA_DIR=str(data),
        DATABASE_URL=f'sqlite:///{data / source_db.name}', NOTIFICATION_DRY_RUN='true',
        NOTIFICATION_RECIPIENT_CLASS='test', AI_REVIEW_MODE='shadow',
        PERSISTENCE_V2_WRITER_ENABLED='false', PERSISTENCE_V2_OUTBOX_DELIVERY_ENABLED='false',
        TELEGRAM_BOT_TOKEN='', TELEGRAM_CHAT_ID='', TELEGRAM_TEST_CHAT_ID='')
    from sqlmodel import Session, create_engine
    from app.config import get_settings
    from app.jobs import probe_krx_night_futures as source
    from app.macro.providers import krx as provider
    from app.services.market_session import korea_market_session, us_market_session

    settings = get_settings()
    if Path(settings.data_dir).resolve() != data or not settings.notification_dry_run:
        raise ValueError('isolated_settings_required')
    if settings.telegram_bot_token or settings.telegram_chat_id:
        raise ValueError('recipient_credential_exclusion_required')
    observed = datetime.now(KST)
    generation = generation_prefix + observed.strftime('%Y%m%dT%H%M%S%z')
    put('report/source-freeze.json', {'generation_id': generation, 'at': observed, 'git': initial,
        'source_owner_sha256': {n: helpers.sha256_file(REPO / n) for n in (
            'scripts/m12ds_r4_source_preflight.py', 'app/jobs/probe_krx_night_futures.py',
            'app/macro/providers/krx.py', 'app/services/krx_night_history_service.py')},
        'production_db_before': before_db})
    sessions = {}
    for market, owner in (('us', us_market_session), ('kr', korea_market_session)):
        session = owner(observed)
        sessions[market] = {'observed_at': observed, 'state': session.session,
            'latest_completed_regular_session_date': session.latest_completed_regular_session_date}
    sessions['night_expected_reference_date'] = source.expected_latest_completed_krx_session(observed.date())
    put('report/session-resolution.json', sessions)
    engine = create_engine(f'sqlite:///{data / source_db.name}')
    with Session(engine) as session:
        population = helpers.current_population(session, observed)
    put('report/monitored-population.json', population)
    expected = json.loads((Path('/Users/sskim/Documents/Codex/Reports/20260922-m12ds-r3-rev1-calibration')
        / 'snapshot/us-context.json').read_bytes())['selected_subjects']
    expected_kr = json.loads((Path('/Users/sskim/Documents/Codex/Reports/20260922-m12ds-r3-rev1-calibration')
        / 'snapshot/kr-context.json').read_bytes())['selected_subjects']
    drift = {m: {'added': sorted(set(population['markets'][m]['tickers']) - set(prior)),
                 'removed': sorted(set(prior) - set(population['markets'][m]['tickers']))}
             for m, prior in (('us', expected), ('kr', expected_kr))}
    put('report/population-drift.json', drift)
    if any(r['added'] or r['removed'] for r in drift.values()) or population['duplicate_count']:
        raise ValueError('M12DS_R4_UNCERTIFIED_POPULATION_DRIFT')
    captured = []

    async def traced_fetch(**kwargs):
        result = await source.fetch_live_probe(**kwargs)
        captured.append(result)
        return result

    with patch.object(provider, 'fetch_live_probe', traced_fetch):
        result = await asyncio.wait_for(provider.KrxNightFuturesProvider().collect(observed), timeout=1200)
    if len(captured) != 1:
        raise ValueError('exact_official_probe_invocation_required')
    probe = captured[0]
    parsed = probe.model_dump(mode='json')
    parsed['live_source'] = probe.live_source
    put('source/night-probe.json', parsed)
    canonical = [helpers.json_value(r) for r in result.observations]
    put('source/night-provider.json', helpers.json_value(result))
    rows, responses = [], []
    for date, body in probe.source_response_bodies_by_date.items():
        digest = hashlib.sha256(body).hexdigest()
        path = root / f'source/krx-raw/{date}.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        responses.append({'query_date': date, 'path': str(path.relative_to(root)), 'sha256': digest,
                          'size': len(body)})
        for raw in source._rows(json.loads(body)):
            row = source._parse_row(raw)
            if row:
                rows.append({'row_identity': source._source_record_id(row), 'response_sha256': digest,
                    'raw_row': raw, 'parsed_row': row.model_dump(mode='json')})
    put('source/night-raw-row-index.json', rows)
    put('report/krx-response-manifest.json', responses)
    receipt = gate(parsed, canonical, rows)
    receipt.update(generation_id=generation, official_probe_invocations=1,
        provider_http_requests=len(probe.queried_dates), current_time=observed,
        source_root=str(root), observations=len(canonical), active_count=population['total_count'])
    put('report/night-source-gate.json', receipt)
    after_db = helpers.source_db_identity(source_db)
    after_git = {str(p): git_state(p) for p in (REPO, OPERATING)}
    unchanged = before_db == after_db and initial == after_git
    put('report/isolation-receipt.json', {'status': 'PASS' if unchanged else 'FAIL',
        'production_db_before': before_db, 'production_db_after': after_db,
        'git_unchanged': initial == after_git, 'production_db_unchanged': before_db == after_db,
        'production_recipient_credentials_loaded': False, 'production_send': 0,
        'production_recipient_intent': 0, 'production_decision_writes': 0,
        'production_warning_writes': 0, 'scheduler_changes': 0, 'notification_changes': 0,
        'broker_actions': 0, 'main_merge': 0, 'push': 0, 'deploy': 0})
    if not unchanged:
        raise ValueError('M12DS_R4_RUNTIME_OR_SECURITY_STOP')
    print(json.dumps({'generation_id': generation, 'night_gate': receipt['status'],
        'errors': receipt['errors'], 'active': population['total_count'],
        'http_requests': len(probe.queried_dates), 'model_calls': 0}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--generation-prefix', default='20260922-m12ds-r4-current-')
    args = parser.parse_args()
    asyncio.run(run(args.root, args.generation_prefix))
