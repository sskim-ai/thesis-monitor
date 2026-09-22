"""Verify selected-source ownership on an immutable prior cohort; no fresh claim."""
import argparse
from pathlib import Path

from scripts.m12dr_offline_source_closure import read, run, write, sha


def audit(baseline, output):
    run(baseline, output / 'source-proof')
    gate = read(output / 'source-proof/report/source-coverage.json')
    audits = read(output / 'source-proof/report/selected-source-quality-audit.json')['rows']
    old = read(baseline / 'reproof/report/source-coverage.json')
    old_ready = {r['ticker'] for r in old['subjects'] if r['status'] == 'DIRECTIONAL_BUSINESS_SOURCE_READY'}
    new_ready = {r['ticker'] for r in gate['subjects'] if r['status'] == 'DIRECTIONAL_BUSINESS_SOURCE_READY'}
    errors = []
    if old_ready - new_ready:
        errors.append('previously_ready_source_regression')
    for row in audits:
        if row['selection_errors']:
            errors.append('selected_source_binding_failed:' + row['ticker'])
        if row['selected'] and row['selected']['provider'] == 'sec_foreign_filing':
            if (row['selected']['hard_errors'] or row['direction_status'] != 'SOURCE_COMPARISON_UNAVAILABLE'
                    or not any(a['hard_errors'] for a in row['alternate_sources'])):
                errors.append('selected_foreign_and_alternate_quality_not_isolated')
    quality = read(output / 'source-proof/report/quality-receipts.json')
    prior_quality = read(baseline / 'reproof/report/quality-receipts.json')
    for ticker, expected in prior_quality.items():
        if ticker not in quality or quality[ticker]['comparative_observations'] != expected['comparative_observations']:
            errors.append('previous_comparison_regression:' + ticker)
    receipt = dict(status='FAIL' if errors else 'PASS', errors=errors,
        subjects=len(audits), old_ready=len(old_ready), ready=len(new_ready),
        selected_source_ownership_pass=not errors,
        coverage_is_not_ownership_pass=gate['ready_count'] != gate['active_count'],
        source_gate_sha256=sha(output / 'source-proof/report/source-coverage.json'),
        baseline=str(baseline), historical_diagnostic_only=True, final_current_input=False,
        source_calls=0, model_calls=0)
    write(output / 'receipt.json', receipt)
    print(receipt)
    if errors:
        raise ValueError('offline_selected_source_regression')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    audit(args.baseline, args.output)
