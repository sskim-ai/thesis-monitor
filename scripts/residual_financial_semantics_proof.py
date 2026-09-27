"""REV3 offline four-subject semantics proof and eighteen-control invariance."""
import argparse
import asyncio
import json
from pathlib import Path
import zipfile

from app.services.bounded_financial_acquisition import RETAINED
from app.services.bounded_financial_acquisition import AcquisitionDenied, SystemicStop
from app.services.bounded_fpi_followup import make_followup_plan, request_manifest, FrozenFpiReader
from app.services.bounded_financial_projection import verify_capture, _raw
from app.services.bounded_financial_stock_owner import assemble, validate, validate_frozen_baseline
from app.services.sec_fpi_financial_purpose import candidate_inventory
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE
from scripts.bounded_financial_owner_proof import offline
from scripts.unified_event_union_proof import snapshot, git

RESIDUAL = frozenset({'SKHY', 'TSM', 'WRD', '003690'})
REV2_SHA = '5a6b59e7406eddd2c19f3890859073afeefd474b515f6a73617c579748b896e6'


def read(root, name):
    return json.loads((root / name).read_bytes())


def save(root, name, value):
    durable_json(root / name, value, exclusive=True)


def prepare(args, root):
    raw = args.rev2_zip.read_bytes()
    if sha256_bytes(raw) != REV2_SHA:
        raise ValueError('rev2_zip_identity_mismatch')
    with zipfile.ZipFile(args.rev2_zip) as archive:
        manifest = json.loads(archive.read('bundle-manifest.json'))
        if set(archive.namelist()) != set(manifest) | {'bundle-manifest.json'}:
            raise ValueError('rev2_manifest_members_mismatch')
        for name, item in manifest.items():
            data = archive.read(name)
            if sha256_bytes(data) != item['sha256'] or data != (args.rev2 / name).read_bytes():
                raise ValueError('rev2_artifact_mismatch:' + name)
    save(args.output, 'REV2-identity.json', {'zip_sha256': REV2_SHA, 'verified_members': len(manifest),
        'authoritative_proof': 'proof-closure', 'source_root': str(args.rev2),
        'repo_base': git(root, 'rev-parse', 'HEAD~1'), 'instruction_commit': git(root, 'rev-parse', 'HEAD')})
    save(args.output, 'state-before.json', snapshot(root, args.operating))


def inputs(rev2, ticker, market, entries):
    directory = rev2 / 'financial-acquisition' / ticker
    return {'baseline': read(rev2, 'proof-before/assembled/' + ticker + '.json'),
        'plan': entries[ticker], 'acquisition': read(directory, 'result.json')['output'],
        'directory': directory, 'receipts': read(directory, 'receipts.json'),
        'local_seed': read(rev2, 'class-c/local-' + market + '.json')}


def prove(args, root):
    entries = {p['ticker']: p for p in read(args.rev2, 'financial-acquisition-plan.json')['entries']}
    matrix, controls = [], []
    for market, tickers in UNIVERSE.items():
        for ticker in tickers:
            previous = read(args.rev2, 'proof-closure/assembled/' + ticker + '.json')
            if ticker in RETAINED:
                validate_frozen_baseline(previous)
                result = previous
            else:
                params = inputs(args.rev2, ticker, market, entries)
                if args.followup and ticker in RESIDUAL and market == 'us':
                    params['followup_directory'] = args.followup / ticker
                result = assemble(**params)
                validate(result, **params)
                if ticker in RESIDUAL and market == 'us':
                    p, a, d, r = (params[k] for k in ('plan', 'acquisition', 'directory', 'receipts'))
                    verify_capture(p, a, d, r)
                    discovery = next(v for v in r if v['stage'] == 'discovery' and not v['failure_class'])
                    inventory = candidate_inventory(json.loads(_raw(d, discovery['artifact'], r)), p)
                    purpose = result['projection']['fpi_purpose']
                    by_accession = {}
                    for doc in purpose['documents']:
                        by_accession.setdefault(doc['accession'], []).append(doc)
                    inventory['candidates'] = [{**c,
                        'purpose_documents': by_accession.get(c['accessionNumber'], []),
                        'document_captured': c['accessionNumber'] in by_accession,
                        'purpose': sorted({r['purpose'] for r in by_accession.get(c['accessionNumber'], [])}) or ['UNKNOWN_PURPOSE'],
                        'reason': 'CAPTURED_EXACT_DOCUMENT_REPLAY' if c['accessionNumber'] in by_accession else 'DOCUMENT_NOT_CAPTURED_NO_PURPOSE_INFERENCE'}
                        for c in inventory['candidates']]
                    save(args.output, args.tag + '/inventory/' + ticker + '.json', inventory)
            if ticker not in RESIDUAL:
                invariant = result == previous
                controls.append({'ticker': ticker, 'status': result['status'], 'result_invariant': invariant,
                    'previous_packet_sha256': previous['packet_sha256'], 'packet_sha256': result['packet_sha256'],
                    'result_sha256': digest(result), 'previous_result_sha256': digest(previous)})
                if not invariant or result['status'] != 'PASS':
                    raise ValueError('complete_control_changed:' + ticker)
            save(args.output, args.tag + '/assembled/' + ticker + '.json', result)
            row = {k: result.get(k) for k in ('ticker', 'market', 'status', 'packet_sha256', 'mandatory_missing', 'acquisition_denials', 'comparison_denials')}
            row['direction_eligible'] = result.get('projection', {}).get('direction_eligible', 'RETAINED_AUTHORITY')
            row['projection_denials'] = result.get('projection', {}).get('denials', [])
            matrix.append(row)
            print(ticker, result['status'], row['direction_eligible'], flush=True)
    save(args.output, args.tag + '/22-subject-matrix.json', matrix)
    save(args.output, args.tag + '/18-control-invariance.json', controls)
    save(args.output, args.tag + '/offline-replay-receipt.json', {'network_calls': 0, 'model_calls': 0,
        'controls_invariant': len(controls) == 18 and all(c['result_invariant'] for c in controls),
        'code_sha': git(root, 'rev-parse', 'HEAD'), 'working_diff': git(root, 'diff', '--stat')})


def freeze_followup(args, root):
    validation = read(args.output, 'closure-validation.json')
    if (git(root, 'status', '--porcelain') or validation['head'] != git(root, 'rev-parse', 'HEAD')
            or any(r['returncode'] for r in validation['commands'].values())
            or not validation['skip_xfail_identity_unchanged'] or not validation['frozen_source_during_validation']):
        raise ValueError('clean_exact_sha_full_validation_required')
    if not read(args.output, 'offline-first/18-control-invariance.json') or not all(
            r['result_invariant'] for r in read(args.output, 'offline-first/18-control-invariance.json')):
        raise ValueError('offline_invariance_required')
    parent = read(args.rev2, 'financial-acquisition-plan.json')
    entries, requests = [], []
    for p in parent['entries']:
        if p['ticker'] not in RESIDUAL or p['market'] != 'us':
            continue
        params = inputs(args.rev2, p['ticker'], 'us', {p['ticker']: p})
        a, d, r = (params[k] for k in ('acquisition', 'directory', 'receipts'))
        verify_capture(p, a, d, r)
        discovery = next(v for v in r if v['stage'] == 'discovery' and not v['failure_class'])
        plan = make_followup_plan(p, _raw(d, discovery['artifact'], r), a['documents'])
        entries.append(plan)
        manifest = [{'request': v, 'request_sha256': digest(v)} for v in request_manifest(plan)]
        requests.extend(manifest)
        save(args.output, 'followup/' + p['ticker'] + '/plan.json', plan)
        save(args.output, 'followup/' + p['ticker'] + '/request-manifest.json', manifest)
    value = {'contract': 'rev3-residual-fpi-exact-followup', 'code_sha': git(root, 'rev-parse', 'HEAD'),
        'config_fingerprint': snapshot(root, args.operating)['config'], 'entries': entries,
        'request_manifest': requests, 'planned_logical_requests': len(requests),
        'maximum_logical_requests': len(requests), 'maximum_HTTP_attempts': len(requests) * 3,
        'timeout_seconds': 600, 'maximum_retries': 2, 'pagination': 0,
        'unfrozen_exhibits': 'NO_CALLS_ALLOWED', 'OpenDART': 0, 'AlphaVantage': 0,
        'model': 0, 'OHLCV': 0, 'news': 0, 'SEC_additional_discovery': 0}
    save(args.output, 'residual-fpi-followup-plan.json', value)
    from app.services.unified_run_artifacts import durable_bytes
    filename = 'residual-fpi-followup-plan.json'
    durable_bytes(args.output / (filename + '.sha256'),
        (sha256_bytes((args.output / filename).read_bytes()) + '  ' + filename + '\n').encode(), exclusive=True)
    print('Frozen', len(entries), 'subjects;', len(requests), 'logical requests;', len(requests) * 3, 'max attempts', flush=True)


async def acquire(args, root):
    from app.config import Settings
    from scripts.unified_stock_source_plan import state as source_state
    from urllib.parse import urlsplit
    from app.services.bounded_financial_acquisition import sec_base
    plan = read(args.output, 'residual-fpi-followup-plan.json')
    expected = (args.output / 'residual-fpi-followup-plan.json.sha256').read_text().split()[0]
    if sha256_bytes((args.output / 'residual-fpi-followup-plan.json').read_bytes()) != expected:
        raise ValueError('followup_plan_drift')
    def guard():
        if git(root, 'rev-parse', 'HEAD') != plan['code_sha'] or git(root, 'status', '--porcelain'):
            raise SystemicStop('fpi_code_drift')
        if source_state(root, args.operating)['config'] != plan['config_fingerprint']:
            raise SystemicStop('fpi_config_drift')
    guard()
    settings = Settings(_env_file=args.operating / '.env')
    if not settings.sec_user_agent:
        raise ValueError('existing_SEC_configuration_missing')
    save(args.output, 'followup-dispatch-once.json', {'plan_sha256': expected})
    rows, stopped = [], None
    for entry in plan['entries']:
        directory = args.output / 'followup' / entry['ticker']
        if read(directory, 'plan.json') != entry or read(directory, 'request-manifest.json') != [
                {'request': r, 'request_sha256': digest(r)} for r in request_manifest(entry)]:
            raise SystemicStop('fpi_manifest_drift')
        reader = FrozenFpiReader(entry, directory, user_agent=settings.sec_user_agent, guard=guard)
        reader.select(entry['candidates'])
        failures = []
        for request in entry['exact_requests']:
            if stopped:
                break
            try:
                raw, receipt = await reader.read(**request)
                if request['stage'] == 'index':
                    if json.loads(raw).get('directory', {}).get('name') != urlsplit(sec_base(entry, request['filing'])).path.rstrip('/'):
                        raise SystemicStop('fpi_index_identity_mismatch')
            except SystemicStop as exc:
                stopped = str(exc)
                failures.append({'request_sha256': digest(request), 'reason': stopped})
            except (AcquisitionDenied, ValueError, KeyError, TypeError) as exc:
                failures.append({'request_sha256': digest(request), 'reason': str(exc) if isinstance(exc, AcquisitionDenied) else type(exc).__name__})
        save(directory, 'receipts.json', reader.receipts)
        row = {'ticker': entry['ticker'], 'logical': reader.logical, 'attempts': reader.attempts,
            'retries': reader.attempts - reader.logical, 'failures': failures, 'systemic_stop': stopped}
        save(directory, 'result.json', row)
        rows.append(row)
        print(entry['ticker'], 'requests', reader.logical, 'attempts', reader.attempts, 'failures', len(failures), flush=True)
    save(args.output, 'followup-result.json', {'rows': rows, 'systemic_stop': stopped})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['prepare', 'prove', 'freeze-followup', 'acquire'])
    p.add_argument('--tag', default='offline-first')
    p.add_argument('--followup', type=Path)
    for name in ('rev2', 'rev2-zip', 'output', 'operating'):
        p.add_argument('--' + name, type=Path, required=True)
    args = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.mode == 'acquire':
        asyncio.run(acquire(args, root))
    else:
        offline()
        {'prepare': prepare, 'prove': prove, 'freeze-followup': freeze_followup}[args.mode](args, root)


if __name__ == '__main__':
    main()
