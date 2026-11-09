"""Consume sealed C22C inputs and selected original Finnhub files, offline only."""
import argparse
from copy import deepcopy
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.dated_economic_research import consume_research


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()


def original_finnhub(archive, result, ticker):
    """Verify existing receipts/bytes; issue no Owner or fresh-generation receipt."""
    seal_bytes = (archive / 'capture-seal.json').read_bytes()
    if digest(seal_bytes) != result['capture_seal_sha256']:
        raise ValueError('original_capture_seal_mismatch')
    seal = json.loads(seal_bytes)
    manifest_bytes = (archive / 'archive.json').read_bytes()
    if digest(manifest_bytes) != seal['manifest_sha256']:
        raise ValueError('original_archive_manifest_mismatch')
    manifest = json.loads(manifest_bytes)
    identities = [s for s in manifest['securities'] if s['ticker'] == ticker]
    if len(identities) != 1:
        raise ValueError('original_identity_not_unique')
    security = identities[0]
    rows = [r for r in result['rows'] if r['ticker'] == ticker]
    if len(rows) != 1 or rows[0]['status'] != 'ORIGINAL_ATOMIC_OWNER_REPLAY':
        raise ValueError('original_valuation_replay_not_approved')
    found = {}; evidence = {}
    for relative, expected in seal['files'].items():
        if not relative.startswith('captures/'):
            continue
        path = archive / relative
        raw_wrapper = path.read_bytes()
        if digest(raw_wrapper) != expected:
            raise ValueError('original_capture_wrapper_mismatch')
        wrapper = json.loads(raw_wrapper)
        receipt = wrapper['receipt']; request = receipt['request']
        if request.get('query', {}).get('symbol') != ticker:
            continue
        if request.get('path') not in {'/api/v1/stock/metric', '/api/v1/stock/profile2'}:
            continue
        if set(request['query']) - {'symbol', 'metric'}:
            raise ValueError('unexpected_original_request_query')
        if (receipt['status'] != 200 or receipt['auth'] or receipt['run_id'] != manifest['run_id']
                or request['method'] != 'GET' or request['host'] != 'finnhub.io'):
            raise ValueError('original_receipt_scope_mismatch')
        body_path = 'raw/' + receipt['raw_sha256']; body_bytes = (archive / body_path).read_bytes()
        if digest(body_bytes) != receipt['raw_sha256'] or seal['files'].get(body_path) != digest(body_bytes):
            raise ValueError('original_valuation_raw_mismatch')
        body = json.loads(body_bytes)
        if (body.get('symbol') or body.get('ticker')) != ticker:
            raise ValueError('original_response_identity_mismatch')
        key = request['path'].rsplit('/', 1)[1]
        if key in found:
            raise ValueError('original_capture_not_unique')
        found[key] = (body, receipt)
        evidence[relative] = raw_wrapper; evidence[body_path] = body_bytes
    if 'metric' not in found:
        raise ValueError('original_metric_raw_missing')
    body, receipt = found['metric']
    normalized = dict(provider=receipt['provider'].lower(), run_id=receipt['run_id'],
        security_sha256=digest(encoded(security)), source_sha256=receipt['raw_sha256'],
        acquisition_class='FRESH_CURRENT_RUN', http_status=receipt['status'],
        request=dict(method=receipt['request']['method'], route='https://' + receipt['request']['host'] + receipt['request']['path'], params=receipt['request']['query']),
        requested_at=receipt['started_at'], received_at=receipt['captured_at'], response_headers=receipt['response_headers'],
        research_capture_receipt_sha256=digest(encoded(receipt)))
    facts = []
    for metadata in rows[0]['metrics']:
        checks = dict(raw=metadata['raw_sha256'] == receipt['raw_sha256'],
            requested_identity=metadata['requested_security_id'] == ticker,
            returned_identity=metadata['returned_security_id'] == ticker,
            timestamp=datetime.fromisoformat(metadata['retrieval_timestamp']) == datetime.fromisoformat(receipt['captured_at']),
            normalized_receipt=metadata['source_receipt_sha256'] == digest(encoded(normalized)))
        if not all(checks.values()):
            raise ValueError('original_snapshot_mismatch:' + ','.join(k for k, valid in checks.items() if not valid))
        fact = deepcopy(metadata)
        fact['value'] = body['metric'].get(metadata['provider_field'])
        fact['original_capture_receipt_sha256'] = digest(encoded(receipt))
        fact['original_capture_generation'] = receipt['run_id']
        facts.append(fact)
    contexts = []
    if 'profile2' in found:
        profile, source = found['profile2']
        contexts.append(dict(ticker=ticker, category='business_context',
            content={k: profile.get(k) for k in ('name', 'finnhubIndustry', 'country', 'exchange', 'currency')},
            source_ref='original-capture:' + digest(encoded(source)), source_sha256=source['raw_sha256'],
            as_of=source['captured_at'], interpretation='Provider profile, not a verified cause of earnings change'))
    return facts, contexts, evidence


def sealed_member(archive, name):
    expected = archive.with_suffix(archive.suffix + '.sha256').read_text().split()[0]
    if digest(archive.read_bytes()) != expected:
        raise ValueError('source_zip_hash_mismatch')
    with zipfile.ZipFile(archive) as z:
        raw = z.read(name)
        manifest = json.loads(z.read('MANIFEST.json'))
        record = manifest.get('files', manifest)[name]
        if digest(raw) != (record['sha256'] if isinstance(record, dict) else record):
            raise ValueError('source_member_hash_mismatch')
    return json.loads(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--c22c-zip', type=Path, required=True)
    parser.add_argument('--c16-zip', type=Path, required=True)
    parser.add_argument('--finnhub-archive', type=Path, required=True)
    parser.add_argument('--tickers', nargs='+', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError('output_exists_preserve_previous_attempt')
    args.out.mkdir(parents=True)
    # Any accidental network or SQLite access is a hard failure, including imports above.
    def audit(event, arguments):
        if event.startswith(('socket.', 'sqlite3.connect', 'subprocess.')):
            raise RuntimeError('offline_side_effect_forbidden:' + event)
    sys.addaudithook(audit)
    metadata = sealed_member(args.c16_zip, 'FINNHUB_RESULT.json')
    summary = []; matrix = []
    with zipfile.ZipFile(args.c22c_zip) as z:
        expected = args.c22c_zip.with_suffix('.zip.sha256').read_text().split()[0]
        if digest(args.c22c_zip.read_bytes()) != expected:
            raise ValueError('C22C_source_zip_hash_mismatch')
        manifest = json.loads(z.read('MANIFEST.json'))['files']
        for ticker in args.tickers:
            name = 'investment-inputs/' + ticker + '.json'; raw = z.read(name)
            if digest(raw) != manifest[name]['sha256']:
                raise ValueError('C22C_input_hash_mismatch')
            packet = json.loads(raw); facts = []; contexts = []
            if any(r['ticker'] == ticker for r in metadata['rows']):
                facts, contexts, source_files = original_finnhub(args.finnhub_archive, metadata, ticker)
                for relative, content in source_files.items():
                    dest = args.out / 'US_SOURCE_EVIDENCE' / relative
                    dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(content)
            view = consume_research(packet, input_sha256=digest(raw), extra_valuation=facts, public_context=contexts)
            dest = args.out / 'C22D_V2_INVESTMENT_RESEARCH_INPUTS' / (ticker + '.json')
            dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(encoded(view))
            source = args.out / 'ORIGINAL_INPUTS' / (ticker + '.json')
            source.parent.mkdir(parents=True, exist_ok=True); source.write_bytes(raw)
            preview = ['# ' + ticker + ' NO-SEND / PRE-MODEL INPUT',
                'No AI judgment, current-price permission or Strict Stage approval is issued.',
                'Financial as-of: ' + view['as_of'], '', '## Original reported comparisons']
            for row in view['business_change_candidates']:
                f = row['source_fields']
                preview.append(f"- {row['field']}: {f['current_value']} vs {f['prior_comparable_value']}; delta={f['delta']}; {f['currency']}; {f['period_start']}..{f['period_end']} vs {f['prior_period_start']}..{f['prior_period_end']}; ref={row['evidence_ref']}. Cause/recurrence unverified.")
            preview += ['', '## Dated valuation']
            preview += [f"- {v['metric']}: {v['value']}; as-of {v['original_fact']['retrieval_timestamp']}; {v['source_locator']}" for v in view['valuation']]
            preview += [f"- {v['metric']}: N/A ({v['state']})" for v in view['valuation_unavailable']]
            preview += ['', '## Business / expectations / risk', json.dumps({k:view[k] for k in ('business_mechanism','market_expectations','structural_risk')}, ensure_ascii=False, indent=2),
                '', '## Original dated Pivot / SR (no new price calculation)', json.dumps(view['dated_price_structure'], ensure_ascii=False, indent=2)]
            dest = args.out / 'C22D_V2_NO_SEND' / (ticker + '.md')
            dest.parent.mkdir(parents=True, exist_ok=True); dest.write_text('\n'.join(preview))
            for observation in view['financial_observations']:
                f = observation['original_fields']
                matrix.append(dict(ticker=ticker, original_ref=observation['original_ref'], field=observation['field'],
                    source_sha=observation['source_sha'], receipt=observation['source_receipt'], lineage=observation['lineage_group'],
                    role=observation['role'], consumed=observation['role'] != 'EXCLUDED',
                    current_value=f.get('current_value'), prior_comparable_value=f.get('prior_comparable_value'),
                    delta=f.get('delta'), growth_pct=f.get('growth_pct'), currency=f.get('currency'), unit=f.get('unit'),
                    period_start=f.get('period_start'), period_end=f.get('period_end'), period_type=f.get('period_type'),
                    prior_period_start=f.get('prior_period_start'), prior_period_end=f.get('prior_period_end'),
                    statement_basis=f.get('statement_basis'), interpretation_eligible=observation['original_quality'].get('interpretation_eligible'),
                    original_fields=json.dumps(f, ensure_ascii=False, sort_keys=True),
                    original_quality=json.dumps(observation['original_quality'], ensure_ascii=False, sort_keys=True),
                    business_claim='REPORTED_CHANGE_NOT_VERIFIED_CAUSE', expectation_ref='NONE_VERIFIED',
                    risk_ref=observation['original_ref'], risk_use='EXPOSURE_QUESTION_NOT_OCCURRED_RISK'))
            summary.append(dict(ticker=ticker, observations=len(view['financial_observations']), comparisons=view['economic_driver_count'],
                valuations=len(view['valuation']), DATED_RESEARCH_EVIDENCE_READY=view['DATED_RESEARCH_EVIDENCE_READY'],
                ECONOMIC_REASONING_INPUT_READY=view['ECONOMIC_REASONING_INPUT_READY'], STRICT_NATIVE_STAGE_READY=False))
    with (args.out / 'C22D_V2_SOURCE_TO_REASONING_MATRIX.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=list(matrix[0])); writer.writeheader(); writer.writerows(matrix)
    (args.out / 'CONSUMPTION_RECEIPT.json').write_bytes(encoded(dict(stocks=summary, financial_HTTP=0, models=0,
        DB_reads=0, DB_writes=0, send=0, service_changes=0, lane_changes=0, audit_guard='socket/sqlite/subprocess denied')))
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
