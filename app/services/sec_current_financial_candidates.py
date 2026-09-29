"""Metadata-only finite FPI discovery. No filename grants financial authority."""
from calendar import monthrange
from datetime import date
import re

from app.services.unified_snapshot_contract import digest

POLICY = 'EXACT_FISCAL_ANNUAL_AND_CURRENT_FPI_V1'
CONTRACT = 'fpi-current-financial-candidate-plan-v1'


def candidate_plan(rows, plan):
    annual = sorted((r for r in rows if r['form'].split('/')[0] in {'20-F', '40-F'} and r['reportDate']),
                    key=lambda r: (r['reportDate'], r['filingDate'], r['accessionNumber']), reverse=True)
    baseline = annual[0]['reportDate'] if annual else plan['begin']
    eligible, outside = [], []
    for row in rows:
        try:
            end = date.fromisoformat(row['reportDate'])
            boundary = end.month in {3, 6, 9, 12} and end.day == monthrange(end.year, end.month)[1]
        except ValueError:
            boundary = False
        if row['form'].split('/')[0] == '6-K' and boundary and row['reportDate'] > baseline:
            eligible.append(row)
        elif row not in annual[:1]:
            outside.append(dict(filing=row, reason='OUTSIDE_QUARTER_BOUNDARY_DISCOVERY_CLASS_NO_PURPOSE_VERDICT'))
    # Recurring document stem is a discovery rank only. Filing date breaks ties.
    def rank(row):
        stem = re.sub(r'\d+', '#', row['primaryDocument'].lower())
        recurrence = sum(re.sub(r'\d+', '#', r['primaryDocument'].lower()) == stem for r in rows)
        financial_name = bool(re.search(r'(?:financial|statement|results|(?:^|[-_])fs(?:x|[-_]))', row['primaryDocument'], re.I))
        return row['reportDate'], financial_name, recurrence > 1, row['filingDate'], row['accessionNumber']
    eligible.sort(key=rank, reverse=True)
    # Two distinct quarter-boundary candidates, not every monthly 6-K body.
    selected = eligible[:2]
    outside.extend(dict(filing=r, reason='OUTSIDE_FROZEN_TWO_CANDIDATE_BOUND') for r in eligible[2:])
    selected = [{**r, 'role': 'current'} for r in [*selected, *annual[:1]]]
    value = dict(contract=CONTRACT, issuer=plan['issuer'], cutoff=plan['cutoff'],
        discovery_sha256=digest(rows), baseline_economic_period_metadata=baseline,
        baseline_is_financial_authority=False, candidates=selected, candidate_cap=3,
        boundary_candidate_cap=2, current_annual_cap=1, outside_bound=outside,
        history_exhausted=False, purpose_authority='FETCHED_CONTENT_ONLY',
        indexes_per_candidate=1, primary_per_candidate=1, exhibits_per_candidate=plan['limits']['linked_exhibits'])
    value['receipt_sha256'] = digest(value)
    return value
