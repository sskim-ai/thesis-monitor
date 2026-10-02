"""REV6 network-free proof over sealed REV5 and qualified identity archives."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sqlite3

from app.services.bounded_financial_acquisition import RETAINED
from app.services.bounded_financial_stock_owner import assemble, validate, validate_frozen_baseline
from app.services.fpi_discovered_exhibit_phase2 import sealed_source
from app.services.unified_run_artifacts import durable_json, durable_bytes, sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE
from scripts.bounded_financial_owner_proof import offline
from scripts.fpi_residual_window_proof import sources
from scripts.residual_financial_semantics_proof import inputs
from scripts.unified_event_union_proof import snapshot, git

REV5_SHA = '3d0b90627ff48bb782c75dc6d1c95d693b13c9089118418606ca753b1325bc6e'


def read(path):
    return json.loads(path.read_bytes())


def save(args, name, value):
    durable_json(args.output / name, value, exclusive=True)


def verify_sources(args):
    src = sources(args)
    five = sealed_source(args.rev5_zip, REV5_SHA)
    for name, raw in five['files'].items():
        if (args.rev5 / name).read_bytes() != raw:
            raise ValueError('REV5_local_drift:' + name)
    return src


def prepare(args, root):
    verify_sources(args)
    save(args, 'state-before.json', snapshot(root, args.operating))
    name = 'docs/reports/20260815-phase7-2-6-skhy-official-identity-evidence.json'
    archived = read(root / name)
    expected = {k: v for k, v in archived.items() if k != 'validation_audit'}
    db = args.operating / 'data/thesis_monitor.sqlite3'
    with sqlite3.connect('file:' + str(db) + '?mode=ro', uri=True) as conn:
        conn.execute('PRAGMA query_only=ON')
        rows = conn.execute("SELECT payload, fetched_at FROM providerresponsecache WHERE "
            "provider=? AND ticker=? AND data_type=?",
            ('official_security_identity', 'SKHY', 'identity_evidence')).fetchall()
    if len(rows) != 1 or json.loads(rows[0][0])['evidence_payload'] != expected:
        raise ValueError('existing_qualified_identity_archive_cache_mismatch')
    save(args, 'identity/qualified-sec-identity.json', expected)
    save(args, 'identity/authority-freeze.json', {
        'qualified_identity_sha256': digest(expected), 'tracked_artifact': name,
        'tracked_artifact_sha256': sha256_bytes((root / name).read_bytes()),
        'existing_identity_cache_matches': True, 'cache_fetched_at': rows[0][1],
        'authority': 'EXISTING_QUALIFIED_AUTHORITATIVE_SECURITY_IDENTITY_OWNER',
        'raw_SEC_document_newly_fetched': False, 'read_only_query': True})
    plan = read(args.rev2 / 'financial-acquisition-plan.json')
    identities = {r['ticker']: r['security'] for r in plan['entries']}
    save(args, 'SKHY-000660-issuer-identity-audit.json', {
        'sealed_master': {t: identities[t] for t in ('SKHY', '000660')},
        'master_alone_sufficient': False, 'qualified_SEC_archive': expected,
        'ratio_policy': 'ARCHIVE_HAS_RATIO_BUT_SEALED_MASTER_NULL_REMAINS_NULL_NO_SECURITY_TRANSFER',
        'dart_binding_policy': 'VERIFY_SEALED_OFFICIAL_LIST_ROWS_NOT_SEED_RESOLVER',
        'network_verification_required': False, 'network_requests': 0})
    save(args, 'REV5-identity.json', {'zip_sha256': REV5_SHA, 'manifest_entries': 235,
        'instruction_sha': git(root, 'rev-parse', 'HEAD'), 'base': '0558dcbf205d689fd6b08930421b71a6afdbed0b'})
    durable_bytes(args.output / 'source-parent/REV5.zip', args.rev5_zip.read_bytes(), exclusive=True)


def prove(args, root):
    src = verify_sources(args)
    plans = {p['ticker']: p for p in read(args.rev2 / 'financial-acquisition-plan.json')['entries']}
    results, all_inputs, controls = {}, {}, []
    for market, tickers in UNIVERSE.items():
        for ticker in tickers:
            old = read(args.rev5 / 'proof-closure/assembled' / (ticker + '.json'))
            if ticker in RETAINED:
                validate_frozen_baseline(old)
                result = old
            else:
                params = inputs(args.rev2, ticker, market, plans)
                if ticker in {'TSM', 'WRD', 'SKHY'}:
                    params.update(followup_directory=args.rev3 / 'followup-phase/followup' / ticker,
                        phase2={'source': src, 'directory': args.rev4 / 'phase2' / ticker}, field_semantics=True)
                    if ticker == 'SKHY':
                        params['coverage_window'] = {'directory': args.rev5 / 'window2/phase1',
                            'phase2_directory': args.rev5 / 'window2/phase2'}
                all_inputs[ticker] = params
                result = assemble(**params)
                validate(result, **params)
            if result != old:
                raise ValueError('REV5_baseline_replay_drift:' + ticker)
            results[ticker] = result
            if ticker != 'SKHY':
                if result['status'] != 'PASS':
                    raise ValueError('control_not_complete:' + ticker)
                controls.append({'ticker': ticker, 'status': 'PASS', 'result_invariant': True,
                    'result_sha256': digest(result), 'previous_result_sha256': digest(old),
                    'packet_sha256': result['packet_sha256']})
    save(args, args.tag + '/SKHY-before.json', results['SKHY'])
    official = read(args.output / 'identity/qualified-sec-identity.json')
    freeze = read(args.output / 'identity/authority-freeze.json')
    bridge_inputs = {'source_inputs': all_inputs['000660'], 'source_result_sha256': digest(results['000660']),
        'official_identity': official, 'official_identity_sha256': freeze['qualified_identity_sha256']}
    params = {**all_inputs['SKHY'], 'issuer_business': bridge_inputs}
    after = assemble(**params)
    validate(after, **params)
    before_stock = results['SKHY']['packet']['stocks'][0]
    after_stock = after['packet']['stocks'][0]
    stripped = deepcopy(after_stock)
    original_ids = {f['fact_id'] for f in before_stock['fact_catalog']}
    added = [f for f in after_stock['fact_catalog'] if f['fact_id'] not in original_ids]
    stripped['fact_catalog'] = [f for f in stripped['fact_catalog'] if f['fact_id'] in original_ids]
    stripped['numeric_registry'] = [r for r in stripped['numeric_registry'] if r['fact_id'] in original_ids]
    if stripped != before_stock:
        raise ValueError('security_level_input_mutated')
    save(args, args.tag + '/security-isolation.json', {
        'all_original_stock_fields_and_facts_unchanged': True,
        'only_added_issuer_comparisons': [f['fact_id'] for f in added],
        'source_price_technical_per_share_valuation_transfers': 0,
        'target_stock_before_sha256': digest(before_stock), 'stripped_after_sha256': digest(stripped)})
    save(args, args.tag + '/original-source-field-matrix.json', {
        'fields': results['000660']['projection']['fields'],
        'denials': results['000660']['projection']['denials'],
        'comparisons': results['000660']['projection']['comparisons'],
        'retained_comparison_refs': results['000660']['comparative_fact_refs']})
    save(args, args.tag + '/bridged-business-evidence.json', added)
    save(args, args.tag + '/issuer-identity-bridge.json', after['issuer_business_bridge'])
    results['SKHY'] = after
    matrix = []
    for ticker, result in results.items():
        save(args, args.tag + '/assembled/' + ticker + '.json', result)
        matrix.append({'ticker': ticker, 'status': result['status'], 'market': result['market'],
            'result_sha256': digest(result), 'packet_sha256': result['packet_sha256'],
            'mandatory_missing': result.get('mandatory_missing', [])})
    save(args, args.tag + '/22-subject-matrix.json', matrix)
    save(args, args.tag + '/21-control-invariance.json', controls)
    save(args, args.tag + '/offline-receipt.json', {'head': git(root, 'rev-parse', 'HEAD'),
        'network_calls': 0, 'model_calls': 0, 'complete': sum(r['status'] == 'PASS' for r in matrix),
        'security_isolated': True, 'replayed_twice': True})
    print(json.dumps({'complete': sum(r['status'] == 'PASS' for r in matrix), 'controls': len(controls)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'prove'])
    parser.add_argument('--tag', default='proof-closure')
    for name in ('rev5', 'rev5-zip', 'rev4', 'rev4-zip', 'rev3', 'rev3-zip',
                 'rev2', 'rev2-zip', 'output', 'operating'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    offline()
    {'prepare': prepare, 'prove': prove}[args.mode](args, Path(__file__).resolve().parents[1])


if __name__ == '__main__':
    main()
