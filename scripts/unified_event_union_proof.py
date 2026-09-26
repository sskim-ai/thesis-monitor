"""Explicit freeze / one-shot event acquisition / network-free R4 stock proof."""

import argparse
import asyncio
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import socket
import sqlite3
import subprocess
import zipfile

import httpx
from sqlmodel import Session, SQLModel, create_engine

from app.config import Settings, get_settings
from app.models.security import SecurityMaster
from app.services.unified_event_acquisition import EventAcquisition
from app.services.unified_run_artifacts import durable_json, durable_bytes, sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_stock_acquisition import StockPlan, UNIVERSE
from app.services.unified_stock_event_input import (
    BoundNewsInput, NewsRead, PROVIDERS, PlannedNewsTransport, make_read,
)
from app.services.unified_stock_owner import assemble_stock, validate_assembled
from scripts.unified_stock_anomaly_proof import verify_seal
from scripts.unified_stock_owner_proof import POLICY as BASE_POLICY, r1_identity
from scripts.unified_stock_source_plan import state


BASE = 'a0de7b591c33ac5cc0f5c449def29c1460a2d539'
R3_SHA = 'b43e88df23b490403689d73ebee039d68b9aefd106d11f8f5e3380b854f7d50c'
RETAINED = {'005930', '047810'}
POLICY = UnifiedSourcePolicy(BASE_POLICY.allowed_providers | {'google_news_rss', 'naver_news'})


def require_twenty(reads):
    expected = {(m, t) for m, ts in UNIVERSE.items() for t in ts if t not in RETAINED}
    if len(reads) != 20 or {(r.market, r.subject) for r in reads} != expected:
        raise ValueError('exact_us14_kr6_one_shot_plan_required')
    if len({r.acquisition_id for r in reads}) != 20 or len({r.run_id for r in reads}) != 1:
        raise ValueError('duplicate_event_acquisition_identity')


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()


def save(out, name, value):
    durable_json(out / name, value, exclusive=True)


def load(out, name):
    return json.loads((out / name).read_bytes())


def snapshot(root, operating):
    value = state(root, operating)
    import hashlib
    db = {}
    for path in sorted((operating / 'data').glob('thesis_monitor.sqlite3*')):
        h = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1048576), b''):
                h.update(block)
        db[path.name] = {'sha256': h.hexdigest(), 'bytes': path.stat().st_size}
    value['production_db_files_readonly_hashes'] = db
    return value


def freeze(args, root):
    if git(root, 'status', '--porcelain'):
        raise ValueError('clean_frozen_worktree_required')
    raw = args.r3_bundle.read_bytes()
    if sha256_bytes(raw) != R3_SHA:
        raise ValueError('accepted_r3_zip_mismatch')
    with zipfile.ZipFile(args.r3_bundle) as archive:
        manifest = json.loads(archive.read('bundle-manifest.json'))
        if set(archive.namelist()) != set(manifest) | {'bundle-manifest.json'}:
            raise ValueError('r3_manifest_mismatch')
        for name, item in manifest.items():
            data = archive.read(name)
            if sha256_bytes(data) != item['sha256'] or len(data) != item['bytes']:
                raise ValueError('r3_artifact_hash_mismatch')
            if name.startswith('class-c/'):
                durable_bytes(args.output / name, data, exclusive=True)
        save(args.output, 'accepted-R3-baseline-matrix.json', json.loads(archive.read('proof-closure/22-subject-matrix.json')))
    save(args.output, 'R3-identity.json', {'sha256': R3_SHA, 'manifest_entries': len(manifest), 'base': BASE})
    save(args.output, 'R2B0-source-identity.json', verify_seal(
        args.corpus / 'thesis-monitor-20260926-m12ds-r6-r5f-r2b0-report.zip', args.corpus))
    r1, _ = r1_identity(args.r1_bundle)
    save(args.output, 'R1-identity.json', r1)
    before = snapshot(root, args.operating)
    if not before['operating_clean']:
        raise ValueError('operating_not_clean')
    save(args.output, 'state-before.json', before)
    db = args.operating / 'data/thesis_monitor.sqlite3'
    with sqlite3.connect(f'{db.as_uri()}?mode=ro', uri=True) as connection:
        connection.execute('PRAGMA query_only=ON')
        connection.row_factory = sqlite3.Row
        records = [SecurityMaster.model_validate(dict(r)).model_dump(mode='json')
                   for r in connection.execute('SELECT * FROM securitymaster ORDER BY id')]
    ids = {r['ticker']: r for r in records}
    for market, tickers in UNIVERSE.items():
        for ticker in tickers:
            old = next(r['record'] for r in load(args.output, 'class-c/financial-' + ticker + '.json')['projection']['records']
                       if r['table'] == 'securitymaster')
            if SecurityMaster.model_validate(old).model_dump(mode='json') != ids[ticker]:
                raise ValueError('sealed_subject_identity_drift:' + ticker)
    save(args.output, 'security-records.json', records)
    settings = Settings(_env_file=args.operating / '.env')
    if not settings.naver_client_id or not settings.naver_client_secret:
        raise ValueError('existing_naver_credentials_missing')
    at = datetime.now(timezone.utc)
    run = 'm12ds-r6-r5f-r2b0-r4-' + at.strftime('%Y%m%dT%H%M%SZ')
    reads = [make_read(security=ids[t], market=m, run_id=run, lookback_days=settings.monitor_lookback_days,
                     security_records=records) for m, ts in UNIVERSE.items() for t in ts if t not in RETAINED]
    require_twenty(reads)
    plan = {'run_id': run, 'frozen_at': at.isoformat(), 'code_sha': before['head'],
        'instruction_sha': args.instruction_sha, 'base': BASE, 'entries': [r.model_dump(mode='json') for r in reads],
        'maximum_logical_requests': 20, 'maximum_HTTP_requests': 20, 'retries': 0, 'redirects': False,
        'financial_refresh': False, 'business_cutoff_policy': 'ACTUAL_ONE_SHOT_ACQUISITION_COMPLETION_REVIEW_TIME',
        'proof_scope': 'MIXED_TIME_MATERIALIZER_NOT_HISTORICAL_PRODUCTION_DECISION',
        'query_owner': 'NewsQueryService + existing provider request_url/request_params',
        'source_config_fingerprint': before['config'], 'retained_without_recollection': sorted(RETAINED)}
    save(args.output, 'event-plan.json', plan)
    durable_bytes(args.output / 'event-plan.json.sha256',
        (sha256_bytes((args.output / 'event-plan.json').read_bytes()) + '  event-plan.json\n').encode(), exclusive=True)
    print(json.dumps({'frozen_requests': 20, 'run_id': run,
        'plan_sha256': sha256_bytes((args.output / 'event-plan.json').read_bytes())}), flush=True)


async def acquire(args, root):
    plan = load(args.output, 'event-plan.json')
    if git(root, 'rev-parse', 'HEAD') != plan['code_sha'] or git(root, 'status', '--porcelain'):
        raise ValueError('event_code_changed_after_freeze')
    current = snapshot(root, args.operating)
    if current['config'] != plan['source_config_fingerprint']:
        raise ValueError('event_configuration_changed_after_freeze')
    reads = [NewsRead.model_validate(r) for r in plan['entries']]
    require_twenty(reads)
    records = load(args.output, 'security-records.json')
    if any(r.security_universe_sha256 != digest(records) for r in reads):
        raise ValueError('frozen_security_records_changed')
    settings = Settings(_env_file=args.operating / '.env')
    get_settings().naver_client_id = settings.naver_client_id
    get_settings().naver_client_secret = settings.naver_client_secret
    if not settings.naver_client_id or not settings.naver_client_secret:
        raise ValueError('existing_naver_credentials_missing')
    save(args.output, 'dispatch-once.json', {'plan_sha256': sha256_bytes((args.output / 'event-plan.json').read_bytes()),
        'started_at': datetime.now(timezone.utc).isoformat(), 'retry_forbidden': True})
    engine = create_engine('sqlite://')
    SQLModel.metadata.create_all(engine)
    counts = []
    try:
        with Session(engine) as session:
            targets = [SecurityMaster.model_validate(r) for r in records]
            session.add_all(targets)
            session.commit()
            by_ticker = {r.ticker: r for r in targets}
            for read in reads:
                folder = args.output / 'acquisition' / read.subject
                transport = PlannedNewsTransport(read=read, root=folder, policy=POLICY,
                    inner=httpx.AsyncHTTPTransport(retries=0))
                owner = EventAcquisition(transport, cutoff=datetime.now(timezone.utc), max_attempts=1)
                error = None
                try:
                    await owner.collect(session, PROVIDERS[read.market](), by_ticker[read.subject],
                                        lookback_days=read.lookback_days, aliases=list(read.aliases))
                except (ValueError, KeyError, TypeError, OSError, httpx.HTTPError) as exc:
                    error = type(exc).__name__
                    await transport.close_owner()
                counts.append({'subject': read.subject, 'provider': read.provider,
                    'logical_attempts': 1, 'HTTP_attempts': transport.ordinal, 'owner_error': error})
                save(args.output, 'acquisition/' + read.subject + '/logical-receipt.json', counts[-1])
                print(read.subject, 'HTTP', transport.ordinal, 'owner_error', error, flush=True)
    finally:
        engine.dispose()
    save(args.output, 'business-cutoff.json', {'business_cutoff': datetime.now(timezone.utc).isoformat(),
        'actual_completed': True, 'historical_production_decision': False, 'counts': counts,
        'logical_attempts': sum(r['logical_attempts'] for r in counts),
        'HTTP_attempts': sum(r['HTTP_attempts'] for r in counts), 'retries': 0})


def bound_input(out, read):
    folder = out / 'acquisition' / read.subject
    def enc(path):
        return base64.b64encode(path.read_bytes()).decode()
    receipt = load(folder, 'read-0001.response.json')
    return BoundNewsInput(read=read, security_records=tuple(load(out, 'security-records.json')),
        response_receipt_b64=enc(folder / 'read-0001.response.json'),
        normalization_b64=enc(folder / 'normalization.json'),
        raw_response_b64=enc(folder / receipt['artifact']) if receipt.get('artifact') else None)


def prove(args, root):
    attempts = []
    def deny(*unused, **unused_kw):
        attempts.append('denied')
        raise RuntimeError('offline_event_union_proof_network_denied')
    socket.socket.connect = socket.socket.connect_ex = socket.getaddrinfo = deny
    identity = verify_seal(args.corpus / 'thesis-monitor-20260926-m12ds-r6-r5f-r2b0-report.zip', args.corpus)
    r1, components = r1_identity(args.r1_bundle)
    plan = StockPlan.model_validate_json((args.corpus / 'request-plan.json').read_bytes())
    event_plan = load(args.output, 'event-plan.json')
    reads = {r['subject']: NewsRead.model_validate(r) for r in event_plan['entries']}
    cutoff = datetime.fromisoformat(load(args.output, 'business-cutoff.json')['business_cutoff'])
    proof, rows = args.output / args.proof_tag, []
    for market, tickers in UNIVERSE.items():
        local = load(args.output, 'class-c/local-' + market + '.json')
        for ticker in tickers:
            receipts, artifacts = {}, {}
            for index, read in enumerate(plan.reads, 1):
                if read.subject != ticker:
                    continue
                receipt = load(args.corpus, f'acquisition/role-{index:03d}.receipt.json')
                receipts[read.role] = receipt
                for path in [receipt['normalized_artifact'], *[p['artifact'] for p in receipt['pages']]]:
                    artifacts[path] = (args.corpus / 'acquisition' / path).read_bytes()
            financial = load(args.output, 'class-c/financial-' + ticker + '.json')
            hashes = {'local': digest(local), 'financial': digest(financial), 'components': digest(components[ticker]),
                'receipts': digest(receipts), 'plan': digest(plan.model_dump(mode='json'))}
            params = dict(plan=plan, ticker=ticker, receipts=receipts, artifacts=artifacts, local_seed=local,
                financial=financial, components=components[ticker], expected_hashes=hashes, policy=POLICY)
            try:
                if ticker in reads:
                    source = bound_input(args.output, reads[ticker])
                    params.update(event_source=source, business_cutoff=cutoff)
                    hashes.update(events=digest(source.model_dump(mode='json')), business_cutoff=digest(cutoff.isoformat()))
                result = assemble_stock(**params)
                if result != assemble_stock(**params):
                    raise ValueError('event_stock_owner_not_deterministic')
                validate_assembled(result, expected_result_sha256=digest(result))
                save(proof, 'assembled/' + ticker + '.json', result)
                row = {k: result[k] for k in ('ticker', 'market', 'status', 'packet_sha256',
                    'diagnostic_packet_sha256', 'mandatory_missing', 'observed_business_cardinality', 'financial_state')}
                row.update(safe_technical_facts=sum(len(v['facts']) for v in components[ticker]['features'].values()),
                    current_price_eligible=components[ticker]['current_price_eligible'],
                    event_count=len(result.get('event_binding', {}).get('evidence', [])),
                    event_denial=result.get('event_binding', {}).get('denial'), owner_error=None)
            except (ValueError, KeyError, TypeError, OSError) as exc:
                row = {'ticker': ticker, 'market': market, 'status': 'OWNER_ERROR', 'packet_sha256': None,
                       'owner_error': type(exc).__name__ + ':' + str(exc), 'event_count': 0}
                save(proof, 'assembled/' + ticker + '.json', row)
            rows.append(row)
            print(ticker, row['status'], 'events', row['event_count'], row.get('owner_error'), flush=True)
    save(proof, '22-subject-matrix.json', rows)
    save(proof, 'source-invariance.json', {'R2B0': identity, 'R1': r1, 'sealed_price_recollected': False})
    save(proof, 'offline-execution.json', {'network_attempts': len(attempts), 'model_calls': 0,
        'render': 0, 'production_db_writes': 0, 'telegram': 0, 'scheduler_mutation': 0})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('freeze', 'acquire', 'prove'))
    for name in ('output', 'operating', 'corpus', 'r1-bundle', 'r3-bundle'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--instruction-sha')
    parser.add_argument('--proof-tag', default='proof-final')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.mode == 'acquire':
        asyncio.run(acquire(args, root))
    elif args.mode == 'freeze':
        freeze(args, root)
    else:
        prove(args, root)


if __name__ == '__main__':
    main()
