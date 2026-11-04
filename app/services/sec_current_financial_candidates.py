"""Metadata-only finite FPI discovery. No filename grants financial authority."""
from calendar import monthrange
from datetime import date
import re
from typing import Literal

from pydantic import Field, model_validator

from app.services.unified_snapshot_contract import ContractModel, digest

POLICY = 'EXACT_FISCAL_ANNUAL_AND_CURRENT_FPI_V1'
CONTRACT = 'fpi-current-financial-candidate-plan-v1'
NOMINATED_CONTRACT = 'fpi-source-nominated-candidate-plan-v2'


class FilingNomination(ContractModel):
    """A predeclared fetch hint, never a financial-purpose or use grant.

    The backend verifies historical anchors before freezing the plan. Current
    admission still requires exact membership in dispatcher-owned discovery.
    """
    form: Literal['6-K', '6-K/A']
    accessionNumber: str = Field(pattern=r'^\d{10}-\d{2}-\d{6}$')
    primaryDocument: str = Field(pattern=r'^[A-Za-z0-9_][A-Za-z0-9_.-]*$')
    filingDate: str
    reportDate: str

    @model_validator(mode='after')
    def exact_metadata_dates(self):
        for value in (self.filingDate, self.reportDate):
            if value and date.fromisoformat(value).isoformat() != value:
                raise ValueError('nomination_date_not_canonical')
        if not self.filingDate or self.primaryDocument in {'.', '..'}:
            raise ValueError('nomination_metadata_incomplete')
        return self


class FpiNomination(ContractModel):
    contract: Literal['fpi-fetch-nomination-v1'] = 'fpi-fetch-nomination-v1'
    issuer: str = Field(pattern=r'^\d{10}$')
    run_id: str = Field(min_length=1)
    cutoff: str
    base_plan_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    historical_discovery_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    historical_receipt_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    authorizing_instruction_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    filings: tuple[FilingNomination, ...] = Field(min_length=1, max_length=2)
    purpose: Literal['FETCH_ONLY_NO_FINANCIAL_AUTHORITY'] = 'FETCH_ONLY_NO_FINANCIAL_AUTHORITY'


def validate_nomination(value, base_plan):
    nomination = FpiNomination.model_validate(value)
    if (base_plan.get('financial_owner_policy') != POLICY or '6-K' not in base_plan['forms']
            or nomination.issuer != base_plan['issuer'] or nomination.run_id != base_plan['run_id']
            or nomination.cutoff != base_plan['cutoff'] or nomination.base_plan_sha256 != digest(base_plan)):
        raise ValueError('nomination_base_plan_binding_mismatch')
    accessions = [f.accessionNumber for f in nomination.filings]
    if len(accessions) != len(set(accessions)):
        raise ValueError('nomination_duplicate_accession')
    if any(not base_plan['begin'] <= f.filingDate <= base_plan['cutoff'][:10] for f in nomination.filings):
        raise ValueError('nomination_outside_source_window')
    return nomination.model_dump(mode='json')


def _nominated_plan(rows, plan):
    base = {k: v for k, v in plan.items() if k not in {'fpi_candidate_contract', 'fpi_nomination'}}
    nomination = validate_nomination(plan['fpi_nomination'], base)
    if len({r['accessionNumber'] for r in rows}) != len(rows):
        raise ValueError('nomination_discovery_duplicate_accession')
    selected = []
    for requested in nomination['filings']:
        found = [row for row in rows if row['accessionNumber'] == requested['accessionNumber']]
        if len(found) != 1 or found[0] != requested:
            raise ValueError('nomination_not_exact_current_discovery_member')
        selected.append(found[0])
    annual = sorted((r for r in rows if r['form'].split('/')[0] in {'20-F', '40-F'} and r['reportDate']),
                    key=lambda r: (r['reportDate'], r['filingDate'], r['accessionNumber']), reverse=True)[:1]
    selected.extend(annual)
    outside = [dict(filing=r, reason='OUTSIDE_FROZEN_TWO_CANDIDATE_BOUND',
                    purpose='NOT_INSPECTED_PURPOSE_UNKNOWN') for r in rows if r not in selected]
    value = dict(contract=NOMINATED_CONTRACT, issuer=plan['issuer'], cutoff=plan['cutoff'],
        plan_sha256=digest(plan), discovery_sha256=digest(rows), nomination_sha256=digest(nomination),
        historical_source_sha256=nomination['historical_discovery_sha256'],
        candidates=[{**r, 'role': 'current'} for r in selected], candidate_cap=3,
        interim_candidate_cap=2, current_annual_cap=1, outside_bound=outside,
        metadata_nomination_reason='PREDECLARED_EXACT_CURRENT_OFFICIAL_DISCOVERY_MEMBER',
        financial_purpose_unverified=True, real_period_unverified=True,
        report_date_semantics='UNMODIFIED_SEC_METADATA_NOT_ECONOMIC_PERIOD',
        history_exhausted=False, purpose_authority='FETCHED_CONTENT_ONLY',
        indexes_per_candidate=1, primary_per_candidate=1, exhibits_per_candidate=plan['limits']['linked_exhibits'])
    value['receipt_sha256'] = digest(value)
    return value


def candidate_plan(rows, plan):
    version = plan.get('fpi_candidate_contract')
    if version == NOMINATED_CONTRACT:
        return _nominated_plan(rows, plan)
    if version is not None or 'fpi_nomination' in plan:
        raise ValueError('unsupported_fpi_candidate_contract')
    # Frozen v1 plans retain their historical discovery behavior for replay.
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
