"""Read a completed cycle's saved inputs; never acquire, accept or render them.

The candidate comparison is a pure diagnostic using the current code. It is
not a replacement for the original B/B2 decision or an accepted Source replay.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from app.services.entry_candidate_basis import assess_entry_candidates
from app.services.unified_snapshot_contract import digest


def read(path):
    return json.loads(path.read_bytes())


def snapshot(cycle):
    path = cycle / 'b2' / 'request.json'
    record = read(path)
    if 'storage_contract' not in record:
        value = record['snapshot']
        if (record['stage'] != 'B2' or record['run_id'] != cycle.name or
                digest(value) != record['snapshot_sha256']):
            raise ValueError('saved_cycle_snapshot_content_mismatch')
    else:
        pin = record['header']['snapshot_sha256']
        if (record['storage_contract'] != 'prepared-research-request-reference-v1' or
                record['header']['stage'] != 'B2' or record['header']['run_id'] != cycle.name or
                not isinstance(pin, str) or not re.fullmatch('[a-f0-9]{64}', pin) or
                record['snapshot_ref'] != f'snapshots/{pin}.json'):
            raise ValueError('saved_cycle_snapshot_reference_mismatch')
        value = read(cycle / 'snapshots' / (pin + '.json'))
        if digest(value) != pin:
            raise ValueError('saved_cycle_snapshot_content_mismatch')
    if value['child_binding']['run_id'] != cycle.name:
        raise ValueError('saved_cycle_execution_mismatch')
    return value


def contexts(cycle):
    """Prefer the exact contexts rebuilt for the original B2 stage."""
    rows, origins = {}, {}
    for stage in ('b2', 'b'):
        folder = cycle / stage / 'canonical' / 'sealed' / 'requests' / 'pass-b'
        paths = sorted(folder.glob('*/batch-*/subject-context.json'))
        if not paths:
            continue
        seen = set()
        for path in paths:
            for ticker, context in read(path).items():
                if ticker in seen:
                    raise ValueError('duplicate_saved_subject_context')
                seen.add(ticker)
                if ticker not in rows:
                    rows[ticker], origins[ticker] = context, str(path)
    return rows, origins


def entry_inputs(context):
    candidates = context['r2_eligible_range_catalog']['tactical_candidates']
    refs = {ref for row in candidates for ref in row.get('evidence_refs', [])}
    price = context.get('current_price')
    if isinstance(price, dict) and price.get('ref_id'):
        refs.add(price['ref_id'])
    refs.update('canonical:chart:' + frame for frame in ('daily', 'weekly', 'monthly'))
    return dict(current_price=price, tactical_candidates=candidates,
        source_evidence_binding=context.get('source_evidence_binding'),
        decision_evidence=[row for row in context['decision_evidence'] if row['ref_id'] in refs],
        source_permissions=[row for row in context['source_use_projection']['source_permissions']
                            if row['ref_id'] in refs])


def issuer_inputs(source, ticker):
    prepared, stock = source['prepared'][ticker], source['stocks'][ticker]
    owner = stock.get('selected_financial_owner') or {}
    selected = set(owner.get('selected_fact_ids', []))
    packet_stock = next((row for row in stock['packet']['stocks'] if row['ticker'] == ticker), {})
    authority = prepared.get('initial_chain', {}).get('authority', {})
    return dict(original_mode=prepared['mode'],
        issuer_business_bridge=stock.get('issuer_business_bridge'),
        selected_financial_owner=owner, financial_state=stock.get('financial_state'),
        selected_comparative_facts=[row for row in packet_stock.get('fact_catalog', [])
                                    if row.get('fact_id') in selected],
        original_authority_records=authority.get('authority_records', []),
        original_recovery=prepared.get('recovery'))


def inspect(cycle):
    value = snapshot(cycle)
    source = value['collection']['monitoring_input']
    binding = value['child_binding']
    if source['source_generation_id'] != binding['source_generation']:
        raise ValueError('saved_cycle_source_generation_mismatch')
    saved, origins = contexts(cycle)
    result = dict(contract='saved-entry-issuer-inspection-v1',
        purpose='READ_ONLY_DIAGNOSTIC_NOT_MODEL_ACCEPTANCE', cycle=str(cycle),
        child_binding=binding, entries={}, issuer_subjects={})
    terminal = cycle / 'terminal.json'
    if terminal.is_file():
        previous = read(terminal)
        result['original_terminal'] = {key: previous.get(key) for key in
            ('status', 'first_failure', 'unissued', 'normal_messages_sent')}
    for ticker, prepared in sorted(source['prepared'].items()):
        stock = source['stocks'][ticker]
        if stock.get('issuer_business_bridge'):
            result['issuer_subjects'][ticker] = issuer_inputs(source, ticker)
        path = cycle / 'b2' / ticker / 'request.json'
        row = dict(original_mode=prepared['mode'], original_request_path=str(path),
            original_accepted_file_present=(cycle / 'b2' / ticker / 'accepted.json').is_file())
        result['entries'][ticker] = row
        if not path.is_file():
            row['diagnostic_status'] = 'NO_SAVED_B2_REQUEST'
            continue
        request = read(path)['provider_request']['input']
        if (request['ticker'] != ticker or request['source_generation'] != binding['source_generation']):
            raise ValueError('saved_b2_subject_generation_mismatch')
        row['original_timing_context'] = request['timing_context']
        if ticker not in saved:
            row['diagnostic_status'] = 'NO_SAVED_B_CONTEXT'
            continue
        context = saved[ticker]
        row['context_path'] = origins[ticker]
        row['original_context_matches_b2'] = digest(context) == request['authority_digests']['context']
        row['original_entry_inputs'] = entry_inputs(context)
        if not row['original_context_matches_b2']:
            row['diagnostic_status'] = 'SAVED_CONTEXT_DIFFERS_FROM_B2_INPUT'
            continue
        candidates = assess_entry_candidates(context, ticker=ticker,
            security_id=request['security_id'], source_generation_id=binding['source_generation'])
        row['candidate_assessment_under_current_code'] = candidates
        selected = request['timing_context']['selected']
        row['original_selected_candidate_assessment'] = next(
            (candidate for candidate in candidates if candidate['candidate_id'] == selected), None)
        row['eligible_candidate_ids_under_current_code'] = [
            candidate['candidate_id'] for candidate in candidates if candidate['eligible']]
        row['diagnostic_status'] = 'INSPECTED_ORIGINAL_INPUT_ONLY'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cycle', type=Path, required=True, help='Original consumer execution directory')
    parser.add_argument('--output', type=Path, required=True, help='New JSON outside the original cycle')
    args = parser.parse_args()
    cycle, output = args.cycle.resolve(), args.output.resolve()
    if output == cycle or cycle in output.parents:
        raise ValueError('inspection_output_must_be_outside_original_cycle')
    report = inspect(cycle)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(output=str(output), subjects=len(report['entries']),
        inspected=sum(row['diagnostic_status'] == 'INSPECTED_ORIGINAL_INPUT_ONLY'
                      for row in report['entries'].values()),
        issuer_subjects=sorted(report['issuer_subjects']),
        model_acceptance=False, rendered_messages=0), ensure_ascii=False))


if __name__ == '__main__':
    main()
