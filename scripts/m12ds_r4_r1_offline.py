"""Audit frozen R4 source evidence only. Never certify it as R4-R1 current input."""
import argparse
from datetime import date
import json
import sqlite3
import sys

from app.models.financial import FinancialSnapshot
from app.services.sec_business_field_quality_service import field_errors, reported_comparison_quality
from app.services.sec_financial_snapshot_service import _companyfacts_snapshots
from app.services.us_full_message_service import _night_timeframe_block, render_us_full_market_message
from scripts.m12dr_offline_source_closure import read, write, sha
from scripts.m12ds_r4_r1_market import market_context


def run(baseline, output):
    def offline(event, _args):
        if event in {'socket.connect', 'socket.getaddrinfo', 'subprocess.Popen', 'os.system'}:
            raise RuntimeError('OFFLINE_REPAIR_AUDIT')
    sys.addaudithook(offline)
    database = baseline / 'private/isolated-data/thesis_monitor.sqlite3'
    before = sha(database)
    population = read(baseline / 'report/monitored-population.json')['markets']['us']['tickers']
    inventory = []
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        for ticker in population:
            rows = [FinancialSnapshot.model_validate(dict(r)) for r in db.execute(
                'select * from financialsnapshot where ticker=? and provider=? and financial_period_end is not null',
                (ticker, 'sec_companyfacts'))]
            current = max(rows, key=lambda r: (r.financial_period_end, r.filing_date or date.min)) if rows else None
            inventory.append(dict(ticker=ticker, provider_rows=len(rows),
                legacy_period=str(current.financial_period_end) if current else None,
                field_denials={m: field_errors(current, m) for m in ('revenue', 'operating_income')} if current else {},
                legacy_receipts_not_synthesized=True))
    payload = read(baseline / 'source/sec-diagnostic-payload.json')
    rows = _companyfacts_snapshots(payload, 'CRCL')
    current = max(rows, key=lambda r: (r.financial_period_end, r.filing_date))
    peers = [r for r in rows if r.source_filing_id == current.source_filing_id
             and 330 <= (current.financial_period_end - r.financial_period_end).days <= 400]
    if len(peers) != 1:
        raise ValueError('exact_same_filing_comparison_required')
    quality = reported_comparison_quality(formal=current, comparison=peers[0], ticker='CRCL', cutoff=date(2026, 9, 22))
    write(output / 'crcl-semantic-receipt.json', dict(current=current.model_dump(mode='json'),
        comparison=peers[0].model_dump(mode='json'), quality=quality, source_payload_sha256=sha(baseline / 'source/sec-diagnostic-payload.json'),
        total_vs_component='UNRESOLVED_NO_STATEMENT_PRESENTATION_PROOF',
        revenue_state='UNRESOLVED', operating_income_state='INDEPENDENT_EXACT_OCCURRENCE',
        diagnostic_only=True, fresh_final_input=False))
    # Re-serialize original canonical metadata to diagnose the serializer repair;
    # this is explicitly not a replacement for the required new source collection.
    packet = read(baseline / 'snapshot/us-packet.json')
    canonical = read(baseline / 'source/night-provider.json')['observations']
    fields = ('contract_maturity', 'reference_date_contract', 'expected_reference_date',
              'provider_raw_bas_dd', 'reference_date_match', 'finality_valid', 'night_timeframes')
    for row in packet['market_context']['night_futures']:
        fact = next(f for f in canonical if f['series_code'] == row['series_code'])
        row.update({k: fact['raw_payload'][k] for k in fields})
        catalog = next(f for f in packet['market_context']['fact_catalog'] if f['fact_id'] == row['fact_id'])
        catalog['fields'] = {k: v for k, v in row.items() if k != 'night_timeframes'}
    context = market_context(packet)
    rendered = render_us_full_market_message(packet['market_context'])
    night = []
    for row in packet['market_context']['night_futures']:
        block = _night_timeframe_block(row, series=row['series_code'])
        night.append(dict(fact_id=row['fact_id'], eligible=row['fact_id'] in context['facts'],
            exact_block=block[0] if block else None, rendered=bool(block and block[0] in rendered.text)))
    write(output / 'night-offline-chain.json', dict(diagnostic_only=True, model_calls=0, records=night,
        parity=context['parity_status'], render_status=rendered.status, render_errors=rendered.validation_errors))
    valid = (len(inventory) == 14 and quality['status'] == 'PASS' and current.revenue is None
        and len(night) == 2 and all(r['eligible'] and r['rendered'] for r in night)
        and before == sha(database))
    receipt = dict(status='PASS' if valid else 'FAIL', sec_inventory=inventory,
        sec_subjects_audited=len(inventory), crcl_comparable_metrics=[r['metric'] for r in quality['comparative_observations']],
        source_generation='R4_DIAGNOSTIC_ONLY', prior_generation_modified=False,
        database_before_sha256=before, database_after_sha256=sha(database), model_calls=0, source_calls=0)
    write(output / 'receipt.json', receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k != 'sec_inventory'}))


if __name__ == '__main__':
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.baseline, args.output)
