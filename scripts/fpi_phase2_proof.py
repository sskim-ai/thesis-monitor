"""REV4 exact discovered-exhibit acquisition and offline full-cohort replay."""
import argparse
import asyncio
import json
from pathlib import Path

from app.services.bounded_financial_acquisition import RETAINED, AcquisitionDenied, SystemicStop
from app.services.bounded_financial_stock_owner import assemble, validate, validate_frozen_baseline
from app.services.bounded_fpi_followup import request_manifest
from app.services.fpi_discovered_exhibit_phase2 import sealed_source, make_phase2_plan, Phase2Reader, verify_phase2
from app.services.unified_run_artifacts import durable_json, durable_bytes, sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE
from scripts.bounded_financial_owner_proof import offline
from scripts.residual_financial_semantics_proof import inputs
from scripts.unified_event_union_proof import snapshot, git

REV3_SHA = '3cd387be5c553e52d94470c2ab158e49dadf961b719ad0cde522ec6fbdab0e78'
BASE = 'aacfe8a5f2cfe6f94e4bd99b01acc4ce4654512b'
RESIDUAL = frozenset({'SKHY', 'TSM', 'WRD'})


def read(path):
    return json.loads(path.read_bytes())


def save(args, name, value):
    durable_json(args.output / name, value, exclusive=True)


def source(args):
    result = sealed_source(args.rev3_zip, REV3_SHA)
    for name, data in result['files'].items():
        if (args.rev3 / name).read_bytes() != data:
            raise ValueError('rev3_local_source_drift:' + name)
    return result


def prepare(args, root):
    src = source(args)
    # The original full-cohort input bundle is also immutable and independently verified.
    parent_sha = read(args.rev3 / 'REV2-identity.json')['zip_sha256']
    parent = sealed_source(args.rev2_zip, parent_sha)
    for name, data in parent['files'].items():
        if (args.rev2 / name).read_bytes() != data:
            raise ValueError('rev2_local_source_drift:' + name)
    save(args, 'REV3-identity.json', {'zip_sha256': REV3_SHA, 'verified_members': len(src['manifest']),
        'REV2_zip_sha256': parent_sha, 'REV2_members': len(parent['manifest']), 'base': BASE,
        'instruction_sha': git(root, 'rev-parse', 'HEAD'), 'network_calls': 0})
    save(args, 'state-before.json', snapshot(root, args.operating))


def prove(args, root):
    src = source(args)
    entries = {p['ticker']: p for p in read(args.rev2 / 'financial-acquisition-plan.json')['entries']}
    rows, controls = [], []
    for market, tickers in UNIVERSE.items():
        for ticker in tickers:
            old = read(args.rev3 / 'proof-closure/assembled' / (ticker + '.json'))
            if ticker in RETAINED:
                validate_frozen_baseline(old)
                result = old
            else:
                params = inputs(args.rev2, ticker, market, entries)
                if ticker in RESIDUAL:
                    params['followup_directory'] = args.rev3 / 'followup-phase/followup' / ticker
                    if args.with_phase2:
                        params['phase2'] = {'source': src, 'directory': args.output / 'phase2' / ticker}
                result = assemble(**params)
                validate(result, **params)
            if ticker not in RESIDUAL:
                controls.append({'ticker': ticker, 'status': result['status'], 'result_invariant': old == result,
                    'previous_result_sha256': digest(old), 'result_sha256': digest(result),
                    'previous_packet_sha256': old['packet_sha256'], 'packet_sha256': result['packet_sha256']})
                if old != result or result['status'] != 'PASS':
                    raise ValueError('19_control_regression:' + ticker)
            save(args, args.tag + '/assembled/' + ticker + '.json', result)
            rows.append({'ticker': ticker, 'market': market, 'status': result['status'],
                'packet_sha256': result['packet_sha256'], 'result_sha256': digest(result),
                'mandatory_missing': result.get('mandatory_missing', []),
                'acquisition_denials': result.get('acquisition_denials', []),
                'comparison_denials': result.get('comparison_denials', []),
                'projection_denials': result.get('projection', {}).get('denials', []),
                'direction_eligible': result.get('projection', {}).get('direction_eligible', 'RETAINED_AUTHORITY'),
                'observed_business_cardinality': result.get('observed_business_cardinality'),
                'event_authority_unchanged': result.get('baseline_sha256') == old.get('baseline_sha256')})
            print(ticker, result['status'], flush=True)
    save(args, args.tag + '/22-subject-matrix.json', rows)
    save(args, args.tag + '/19-control-invariance.json', controls)
    save(args, args.tag + '/offline-receipt.json', {'network_calls': 0, 'model_calls': 0,
        'head': git(root, 'rev-parse', 'HEAD'), 'controls': len(controls), 'invariant': all(r['result_invariant'] for r in controls)})


def freeze(args, root):
    src = source(args)
    val = read(args.output / 'final-validation.json')
    if (git(root, 'status', '--porcelain') or val['head'] != git(root, 'rev-parse', 'HEAD')
            or any(r['returncode'] for r in val['commands'].values())
            or not val['skip_xfail_identity_unchanged'] or not val['frozen_source_during_validation']):
        raise ValueError('exact_sha_clean_full_validation_required')
    controls = read(args.output / 'offline-first/19-control-invariance.json')
    if len(controls) != 19 or not all(r['result_invariant'] for r in controls):
        raise ValueError('19_controls_required_before_network')
    entries = []
    for p in read(args.rev2 / 'financial-acquisition-plan.json')['entries']:
        if p['ticker'] not in RESIDUAL:
            continue
        plan = make_phase2_plan(p, src)
        entries.append(plan)
        save(args, 'phase2/' + p['ticker'] + '/plan.json', plan)
        save(args, 'phase2/' + p['ticker'] + '/request-manifest.json', [
            {'request': r, 'request_sha256': digest(r)} for r in request_manifest(plan)])
    n = sum(p['planned_logical_requests'] for p in entries)
    plan = {'contract': 'FPI_DISCOVERED_EXHIBIT_PHASE2', 'source_REV3_zip_sha256': REV3_SHA,
        'code_sha': git(root, 'rev-parse', 'HEAD'), 'config_fingerprint': snapshot(root, args.operating)['config'],
        'entries': entries, 'planned_logical_requests': n, 'maximum_HTTP_attempts': n * 3,
        'timeout_seconds': 600, 'maximum_transient_retries': 2,
        'skipped_as_not_required': [], 'recursive_discovery': False, 'new_discovery': 0,
        'model': 0, 'OpenDART': 0, 'OHLCV': 0, 'AlphaVantage': 0}
    save(args, 'fpi-phase2-exhibit-plan.json', plan)
    filename = 'fpi-phase2-exhibit-plan.json'
    durable_bytes(args.output / (filename + '.sha256'),
        (sha256_bytes((args.output / filename).read_bytes()) + '  ' + filename + '\n').encode(), exclusive=True)
    print(json.dumps({'planned': n, 'maximum_attempts': n * 3, 'subjects': {p['ticker']: p['planned_logical_requests'] for p in entries}}))


async def acquire(args, root):
    from app.config import Settings
    from scripts.unified_stock_source_plan import state
    src = source(args)
    plan_path = args.output / 'fpi-phase2-exhibit-plan.json'
    raw = plan_path.read_bytes()
    if sha256_bytes(raw) != (args.output / 'fpi-phase2-exhibit-plan.json.sha256').read_text().split()[0]:
        raise SystemicStop('phase2_global_manifest_drift')
    plan = json.loads(raw)
    parents = {p['ticker']: p for p in read(args.rev2 / 'financial-acquisition-plan.json')['entries']}
    expected = [make_phase2_plan(p, src) for p in parents.values() if p['ticker'] in RESIDUAL]
    if plan['entries'] != expected:
        raise SystemicStop('phase2_exact_plan_source_mismatch')
    def guard():
        if git(root, 'rev-parse', 'HEAD') != plan['code_sha'] or git(root, 'status', '--porcelain'):
            raise SystemicStop('phase2_code_drift')
        if state(root, args.operating)['config'] != plan['config_fingerprint']:
            raise SystemicStop('phase2_config_drift')
        if plan_path.read_bytes() != raw:
            raise SystemicStop('phase2_global_manifest_drift')
    guard()
    settings = Settings(_env_file=args.operating / '.env')
    if not settings.sec_user_agent:
        raise SystemicStop('existing_sec_configuration_missing')
    save(args, 'dispatch-once.json', {'plan_sha256': sha256_bytes(raw), 'code_sha': plan['code_sha']})
    results, stopped = [], None
    for p in plan['entries']:
        directory = args.output / 'phase2' / p['ticker']
        manifest = [{'request': r, 'request_sha256': digest(r)} for r in request_manifest(p)]
        if read(directory / 'plan.json') != p or read(directory / 'request-manifest.json') != manifest:
            raise SystemicStop('phase2_subject_manifest_drift')
        reader = Phase2Reader(p, directory, user_agent=settings.sec_user_agent, guard=guard)
        reader.select(p['candidates'])
        errors = []
        for request in p['exact_requests']:
            if stopped:
                break
            try:
                await reader.read(**request)
            except SystemicStop as exc:
                stopped = str(exc)
                errors.append({'url': request['url'], 'reason': stopped})
            except AcquisitionDenied as exc:
                errors.append({'url': request['url'], 'reason': str(exc)})
        durable_json(directory / 'receipts.json', reader.receipts, exclusive=True)
        verified = verify_phase2(parents[p['ticker']], src, directory)
        row = {'ticker': p['ticker'], 'logical': reader.logical, 'attempts': reader.attempts,
            'retries': reader.attempts - reader.logical, 'errors': errors, 'systemic_stop': stopped,
            'qualified_document_mime_count': len(verified['documents']), 'unattempted': verified['unattempted'],
            'phase2_result_sha256': verified['phase2_result_sha256']}
        durable_json(directory / 'result.json', row, exclusive=True)
        results.append(row)
        print(json.dumps(row), flush=True)
    save(args, 'phase2-result.json', {'rows': results, 'systemic_stop': stopped})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'prove', 'freeze', 'acquire'])
    parser.add_argument('--tag', default='offline-first')
    parser.add_argument('--with-phase2', action='store_true')
    for name in ('rev3', 'rev3-zip', 'rev2', 'rev2-zip', 'output', 'operating'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.mode == 'acquire':
        asyncio.run(acquire(args, root))
    else:
        offline()
        {'prepare': prepare, 'prove': prove, 'freeze': freeze}[args.mode](args, root)


if __name__ == '__main__':
    main()
