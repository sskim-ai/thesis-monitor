"""REV5 local residual semantics and one sealed second FPI window."""
import argparse
import asyncio
import json
from pathlib import Path

from app.services.unified_run_artifacts import durable_json, durable_bytes, sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.fpi_discovered_exhibit_phase2 import sealed_source
from app.services.bounded_financial_stock_owner import assemble, validate, validate_frozen_baseline
from app.services.bounded_financial_acquisition import RETAINED
from app.services.unified_stock_acquisition import UNIVERSE
from scripts.residual_financial_semantics_proof import inputs
from scripts.bounded_financial_owner_proof import offline
from scripts.unified_event_union_proof import snapshot, git

REV4_SHA = '034cde40aa18ad365782425ec89255e89c3e9df23987283a6bb5e6f871eeab02'
RESIDUAL = {'TSM', 'WRD', 'SKHY'}


def read(path):
    return json.loads(path.read_bytes())


def save(args, name, value):
    durable_json(args.output / name, value, exclusive=True)


def sources(args):
    four = sealed_source(args.rev4_zip, REV4_SHA)
    # The nested parent is bound by REV4's verified manifest, not a caller assertion.
    parent = read(args.rev4 / 'REV3-identity.json')
    three = sealed_source(args.rev3_zip, parent['zip_sha256'])
    two = sealed_source(args.rev2_zip, parent['REV2_zip_sha256'])
    for directory, src in ((args.rev4, four), (args.rev3, three), (args.rev2, two)):
        for name, value in src['files'].items():
            if (directory / name).read_bytes() != value:
                raise ValueError('sealed_source_local_drift:' + name)
    return three


def prepare(args, root):
    sources(args)
    save(args, 'REV4-identity.json', {'zip_sha256': REV4_SHA, 'base': '9aa2ec1d47bd31dbe0111bf5b85edfa2e030efd0',
        'instruction_sha': git(root, 'rev-parse', 'HEAD'), 'network_calls': 0})
    save(args, 'state-before.json', snapshot(root, args.operating))


def prove(args, root):
    src = sources(args)
    entries = {p['ticker']: p for p in read(args.rev2 / 'financial-acquisition-plan.json')['entries']}
    matrix, controls = [], []
    for market, tickers in UNIVERSE.items():
        for ticker in tickers:
            old = read(args.rev4 / 'proof-closure/assembled' / (ticker + '.json'))
            if ticker in RETAINED:
                validate_frozen_baseline(old)
                result = old
            else:
                params = inputs(args.rev2, ticker, market, entries)
                if ticker in RESIDUAL:
                    params.update(followup_directory=args.rev3 / 'followup-phase/followup' / ticker,
                        phase2={'source': src, 'directory': args.rev4 / 'phase2' / ticker}, field_semantics=True)
                    if ticker == 'SKHY' and args.with_window:
                        params['coverage_window'] = {'directory': args.output / 'window2/phase1',
                            'phase2_directory': args.output / 'window2/phase2' if args.with_exhibits else None}
                result = assemble(**params)
                validate(result, **params)
            if ticker not in RESIDUAL:
                controls.append({'ticker': ticker, 'status': result['status'], 'result_invariant': result == old,
                    'previous_result_sha256': digest(old), 'result_sha256': digest(result),
                    'previous_packet_sha256': old['packet_sha256'], 'packet_sha256': result['packet_sha256']})
                if old != result or result['status'] != 'PASS':
                    raise ValueError('19_control_regression:' + ticker)
            save(args, args.tag + '/assembled/' + ticker + '.json', result)
            matrix.append({'ticker': ticker, 'market': market, 'status': result['status'],
                'packet_sha256': result['packet_sha256'], 'result_sha256': digest(result),
                'mandatory_missing': result.get('mandatory_missing', []),
                'acquisition_denials': result.get('acquisition_denials', []),
                'comparison_denials': result.get('comparison_denials', []),
                'projection_denials': result.get('projection', {}).get('denials', [])})
            print(ticker, result['status'], flush=True)
    save(args, args.tag + '/22-subject-matrix.json', matrix)
    save(args, args.tag + '/19-control-invariance.json', controls)
    save(args, args.tag + '/offline-receipt.json', {'head': git(root, 'rev-parse', 'HEAD'),
        'network_calls': 0, 'model_calls': 0, 'invariant': all(c['result_invariant'] for c in controls)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'prove', 'plan-review', 'freeze', 'acquire', 'freeze-exhibits', 'acquire-exhibits'])
    parser.add_argument('--tag', default='offline-first')
    parser.add_argument('--with-window', action='store_true')
    parser.add_argument('--with-exhibits', action='store_true')
    for name in ('rev4', 'rev4-zip', 'rev3', 'rev3-zip', 'rev2', 'rev2-zip', 'output', 'operating'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.mode in {'acquire', 'acquire-exhibits'}:
        asyncio.run(acquire(args, root))
    else:
        offline()
        {'prepare': prepare, 'prove': prove, 'plan-review': plan_review, 'freeze': freeze, 'freeze-exhibits': freeze}[args.mode](args, root)


def plan_review(args, root):
    from app.services.fpi_coverage_window import make_window_plan
    p, discovery, captured, first, second = window_inputs(args)
    plan = make_window_plan(p, discovery, captured, first, second)
    save(args, 'window2-draft-review.json', {'network_authorized_by_this_draft': False, 'plan': plan})
    print(json.dumps({'candidates': plan['candidates'], 'requests': len(plan['exact_requests'])}), flush=True)


def freeze(args, root):
    from app.services.fpi_coverage_window import make_window_plan, make_window_exhibit_plan, verify_window
    from app.services.bounded_fpi_followup import request_manifest
    parent, discovery, captured, first, second = window_inputs(args)
    validation = read(args.output / 'final-validation.json')
    if (git(root, 'status', '--porcelain') or validation['head'] != git(root, 'rev-parse', 'HEAD')
            or any(v['returncode'] for v in validation['commands'].values())
            or not validation['skip_xfail_identity_unchanged'] or not validation['frozen_source_during_validation']):
        raise ValueError('clean_exact_sha_full_validation_required')
    controls = read(args.output / 'preacquisition/19-control-invariance.json')
    if len(controls) != 19 or not all(c['result_invariant'] for c in controls):
        raise ValueError('19_controls_required')
    phase = 'phase1'
    plan = make_window_plan(parent, discovery, captured, first, second)
    if args.mode == 'freeze-exhibits':
        phase = 'phase2'
        one = verify_window(parent, discovery, captured, first, second, directory=args.output / 'window2/phase1')
        plan = make_window_exhibit_plan(parent, one, args.output / 'window2/phase1')
    save(args, f'window2/{phase}/plan.json', plan)
    save(args, f'window2/{phase}/request-manifest.json', [{'request': r, 'request_sha256': digest(r)} for r in request_manifest(plan)])
    global_plan = {'plan': plan, 'code_sha': git(root, 'rev-parse', 'HEAD'),
        'config_fingerprint': snapshot(root, args.operating)['config'], 'REV4_sha256': REV4_SHA,
        'timeout_seconds': 600, 'maximum_transient_retries': 2, 'new_submissions': 0,
        'other_subject_requests': 0, 'maximum_total_logical': 19, 'maximum_total_attempts': 57}
    name = f'window2-{phase}-frozen.json'
    save(args, name, global_plan)
    durable_bytes(args.output / (name + '.sha256'),
        (sha256_bytes((args.output / name).read_bytes()) + '  ' + name + '\n').encode(), exclusive=True)
    print(json.dumps({'phase': phase, 'logical': plan['planned_logical_requests'], 'maximum_attempts': plan['maximum_HTTP_attempts']}))


async def acquire(args, root):
    from app.config import Settings
    from app.services.bounded_financial_acquisition import AcquisitionDenied, SystemicStop
    from app.services.fpi_coverage_window import make_window_plan, make_window_exhibit_plan, verify_window, WindowReader
    from app.services.fpi_discovered_exhibit_phase2 import Phase2Reader, verify_phase2_capture
    from app.services.bounded_fpi_followup import request_manifest, verify_frozen_followup
    from scripts.unified_stock_source_plan import state
    parent, discovery, captured, first, second = window_inputs(args)
    phase = 'phase2' if args.mode == 'acquire-exhibits' else 'phase1'
    global_path = args.output / f'window2-{phase}-frozen.json'
    frozen = global_path.read_bytes()
    if sha256_bytes(frozen) != (args.output / (global_path.name + '.sha256')).read_text().split()[0]:
        raise SystemicStop('global_manifest_hash_mismatch')
    global_plan = json.loads(frozen)
    plan = make_window_plan(parent, discovery, captured, first, second)
    if phase == 'phase2':
        one = verify_window(parent, discovery, captured, first, second, directory=args.output / 'window2/phase1')
        plan = make_window_exhibit_plan(parent, one, args.output / 'window2/phase1')
    if plan != global_plan['plan'] or plan['ticker'] != 'SKHY':
        raise SystemicStop('campaign_scope_or_manifest_mismatch')
    directory = args.output / 'window2' / phase
    if read(directory / 'plan.json') != plan or read(directory / 'request-manifest.json') != [
            {'request': r, 'request_sha256': digest(r)} for r in request_manifest(plan)]:
        raise SystemicStop('subject_manifest_mismatch')
    def guard():
        if git(root, 'status', '--porcelain') or git(root, 'rev-parse', 'HEAD') != global_plan['code_sha']:
            raise SystemicStop('frozen_code_drift')
        if state(root, args.operating)['config'] != global_plan['config_fingerprint'] or global_path.read_bytes() != frozen:
            raise SystemicStop('config_or_manifest_drift')
    guard()
    settings = Settings(_env_file=args.operating / '.env')
    if not settings.sec_user_agent:
        raise SystemicStop('existing_sec_configuration_missing')
    save(args, f'window2/{phase}/dispatch-once.json', {'manifest_sha256': sha256_bytes(frozen)})
    reader = (Phase2Reader if phase == 'phase2' else WindowReader)(plan, directory, user_agent=settings.sec_user_agent, guard=guard)
    reader.select(plan['candidates'])
    errors, stop = [], None
    for request in plan['exact_requests']:
        try:
            await reader.read(**request)
        except SystemicStop as exc:
            stop = str(exc)
            errors.append({'url': request['url'], 'reason': stop})
            break
        except AcquisitionDenied as exc:
            errors.append({'url': request['url'], 'reason': str(exc)})
        print(json.dumps({'logical_completed': reader.logical, 'attempts': reader.attempts}), flush=True)
    save(args, f'window2/{phase}/receipts.json', reader.receipts)
    verified = verify_phase2_capture(plan, directory) if phase == 'phase2' else verify_frozen_followup(plan, [], directory)
    row = {'logical': reader.logical, 'attempts': reader.attempts, 'retries': reader.attempts-reader.logical,
        'errors': errors, 'systemic_stop': stop, 'receipt_sha256': verified['receipt_sha256'],
        'documents': len(verified['documents']), 'planned': len(plan['exact_requests']), 'model_calls': 0}
    save(args, f'window2/{phase}/result.json', row)
    print(json.dumps(row), flush=True)


def window_inputs(args):
    from app.services.bounded_financial_projection import verify_capture, _raw
    from app.services.bounded_fpi_followup import verify_followup
    from app.services.fpi_discovered_exhibit_phase2 import verify_phase2
    src = sources(args)
    entries = {p['ticker']: p for p in read(args.rev2 / 'financial-acquisition-plan.json')['entries']}
    params = inputs(args.rev2, 'SKHY', 'us', entries)
    p, a, d, r = [params[k] for k in ('plan', 'acquisition', 'directory', 'receipts')]
    verify_capture(p, a, d, r)
    receipt = next(x for x in r if x['stage'] == 'discovery' and not x['failure_class'])
    discovery = _raw(d, receipt['artifact'], r)
    first = verify_followup(p, discovery, a['documents'], args.rev3 / 'followup-phase/followup/SKHY')
    from app.services.bounded_financial_acquisition import sec_base
    urls = {sec_base(p, f) + f['primaryDocument'] for f in first['plan']['candidates']}
    first['captured_window_documents'] = [{**doc, 'raw': _raw(d, doc['artifact'], r)} for doc in a['documents'] if doc['url'] in urls]
    second = verify_phase2(p, src, args.rev4 / 'phase2/SKHY')
    return p, discovery, a['documents'], first, second


if __name__ == '__main__':
    main()
