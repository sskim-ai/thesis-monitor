import asyncio
from datetime import date
import json
from types import SimpleNamespace

import httpx
import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.financial import FinancialSnapshot
from app.providers.filings import OpenDARTProvider
from app.services import financial_backfill_service as backfill
from app.services.sec_financial_snapshot_service import SecFinancialSnapshotService, _companyfacts_snapshots
from app.services.valuation_snapshot_service import _earnings_quarters
from tests.test_external_api_accuracy import _companyfact_entry, _companyfacts_payload
from tests.test_kr_financial_lineage_service import _item


def test_business_concept_selection_is_per_period_not_first_inventory():
    old = _companyfact_entry(100, end="2025-03-31", filed="2025-04-30", fy=2025)
    current = _companyfact_entry(200)
    payload = _companyfacts_payload("us-gaap", {
        "RevenueFromContractWithCustomerExcludingAssessedTax": [old],
        "Revenues": [current], "OperatingIncomeLoss": [_companyfact_entry(30)],
    })
    payload['cik'] = 1234
    row = max(_companyfacts_snapshots(payload, "GENERIC"), key=lambda r: r.financial_period_end)
    assert row.revenue == 200
    assert row.operating_income == 30
    assert row.operating_margin == 15
    raw = {item['field']: item for item in json.loads(row.raw_financial_fields)}
    assert raw['revenue']['concept'] == 'Revenues'
    assert raw['revenue']['issuer_cik'] == 1234
    assert raw['revenue']['period_start'] == current['start']
    assert raw['revenue']['period_end'] == current['end']
    assert len(raw['revenue']['source_row_identity']) == 64


@pytest.mark.parametrize('concept', ['CostOfRevenue', 'NonoperatingIncomeExpense',
    'RevenueRemainingPerformanceObligation', 'RevenueFromContractWithCustomerIncludingAssessedTax'])
def test_unreviewed_or_different_economic_concepts_not_projected(concept):
    payload = _companyfacts_payload('us-gaap', {concept: [_companyfact_entry(200)]})
    assert _companyfacts_snapshots(payload, 'GENERIC') == []


def test_conflicting_business_aliases_fail_closed():
    payload = _companyfacts_payload('us-gaap', {
        'Revenues': [_companyfact_entry(100)],
        'RevenueFromContractWithCustomerExcludingAssessedTax': [_companyfact_entry(200)],
    })
    row = _companyfacts_snapshots(payload, 'GENERIC')[0]
    assert row.revenue is None
    assert 'sec_business_occurrence_conflict' in json.loads(row.financial_hard_errors)
    assert _earnings_quarters([row]) == []


@pytest.mark.parametrize('unit,value', [('USD/shares', 100), ('shares', 100), ('USD', True), ('USD', float('inf'))])
def test_business_amount_unit_and_finite_number_fail_closed(unit, value):
    payload = {'facts': {'us-gaap': {'Revenues': {'units': {unit: [_companyfact_entry(value)]}}}}}
    row = _companyfacts_snapshots(payload, 'GENERIC')[0]
    assert row.revenue is None
    assert json.loads(row.financial_hard_errors) == ['sec_business_occurrence_invalid_unit_or_value']
    assert _earnings_quarters([row]) == []


@pytest.mark.parametrize('start', ['2026-01-01', None])
def test_ytd_or_instant_not_projected_as_single_quarter(start):
    entry = _companyfact_entry(100, fp='Q2', start=start, end='2026-06-30', filed='2026-08-01')
    rows = _companyfacts_snapshots(_companyfacts_payload('us-gaap', {'Revenues': [entry]}), 'GENERIC')
    assert rows[0].revenue is None


def test_operating_loss_is_preserved_without_revenue_substitution():
    rows = _companyfacts_snapshots(_companyfacts_payload('us-gaap', {
        'OperatingIncomeLoss': [_companyfact_entry(-20)]}), 'GENERIC')
    assert rows[0].operating_income == -20
    assert rows[0].revenue is None
    assert rows[0].operating_margin is None


def test_comparative_occurrences_do_not_overwrite_current_and_refresh_is_idempotent(monkeypatch):
    entry = _companyfact_entry(200, fp='Q2', start='2026-04-01', end='2026-06-30', filed='2026-08-01')
    prior = dict(entry, start='2026-01-01', end='2026-03-31', val=150)
    payload = _companyfacts_payload('us-gaap', {'Revenues': [entry, prior]})
    async def resolve(*args):
        return '0000001234'
    async def foreign(*args):
        return {}
    service = SecFinancialSnapshotService(httpx.MockTransport(lambda req: httpx.Response(200, json=payload)))
    monkeypatch.setattr(service, '_resolve_cik', resolve)
    monkeypatch.setattr(service, '_scan_foreign_filings', foreign)
    engine = create_engine('sqlite://')
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        for _ in range(2):
            asyncio.run(service.refresh(session, 'GENERIC', 'unit-test'))
        rows = session.exec(select(FinancialSnapshot)).all()
        assert len(rows) == 2
        assert max(rows, key=lambda r:r.financial_period_end).revenue == 200


def setup_backfill(monkeypatch, *, receipt='20260814000001', filing_date='20260814'):
    monkeypatch.setattr(backfill, 'get_settings', lambda: SimpleNamespace(
        opendart_api_key='fixture', financial_operating_margin_upper_bound=60))
    async def resolve(*args):
        return SimpleNamespace(stock_code='GENERIC', corp_code='00012345', corp_name='Generic')
    monkeypatch.setattr(backfill, '_resolve_opendart_company', resolve)
    requests = []
    def handler(request):
        requests.append(request)
        if request.url.path.endswith('/list.json'):
            return httpx.Response(200, json={'status':'000', 'total_page':1, 'list':[
                {'report_nm':'반기보고서 (2026.06)', 'rcept_dt':filing_date, 'rcept_no':receipt}]})
        if request.url.path.endswith('/fnlttSinglAcntAll.json'):
            if request.url.params.get('fs_div') == 'OFS':
                return httpx.Response(200, json={'status':'013'})
            return httpx.Response(200, json={'status':'000', 'list':[_item(thstrm_amount='200', thstrm_add_amount='350')]})
        return httpx.Response(200, json={'status':'013'})
    client = httpx.AsyncClient
    monkeypatch.setattr(backfill.httpx, 'AsyncClient', lambda **kwargs: client(transport=httpx.MockTransport(handler)))
    engine = create_engine('sqlite://')
    SQLModel.metadata.create_all(engine)
    return engine, requests


def test_backfill_actual_provider_three_part_receipt_lineage_and_unknowns(monkeypatch):
    engine, requests = setup_backfill(monkeypatch)
    original = OpenDARTProvider._fetch_financial_facts
    calls = []
    async def spy(self, *args, **kwargs):
        calls.append(kwargs['receipt_no'])
        result = await original(self, *args, **kwargs)
        assert len(result) == 3
        return result
    monkeypatch.setattr(OpenDARTProvider, '_fetch_financial_facts', spy)
    with Session(engine) as session:
        result = asyncio.run(backfill.backfill_financial_snapshots(session, 'GENERIC', years=1))
        assert result.backfilled_count == 1
        assert calls == ['20260814000001']
        row = session.exec(select(FinancialSnapshot)).one()
        records = json.loads(row.raw_financial_fields)
        lineage = next(r for r in records if r.get('source_column') == 'thstrm_amount')
        assert lineage['lineage_verified'] is True
        assert lineage['amount_period_start'] == '2026-04-01'
        assert lineage['amount_period_end'] == '2026-06-30'
        assert lineage['statement_basis_state'] == 'verified_consolidated'
        assert row.source_filing_id == calls[0]
        assert row.revenue == 200
        assert records[-1]['unknowns'] == result.warnings
        assert result.warnings


@pytest.mark.parametrize('receipt,filing_date', [('', '20260814'), ('20260814000001','bad')])
def test_missing_receipt_or_date_never_calls_financial_endpoint(monkeypatch, receipt, filing_date):
    engine, requests = setup_backfill(monkeypatch, receipt=receipt, filing_date=filing_date)
    with Session(engine) as session:
        result = asyncio.run(backfill.backfill_financial_snapshots(session, 'GENERIC'))
        assert result.skipped_count == 1
        assert result.backfilled_count == 0
        assert len(requests) == 1


def test_old_two_product_provider_contract_is_not_silently_accepted(monkeypatch):
    engine, _ = setup_backfill(monkeypatch)
    async def old(*args, **kwargs):
        return [], []
    monkeypatch.setattr(OpenDARTProvider, '_fetch_financial_facts', old)
    with Session(engine) as session, pytest.raises(ValueError, match='not enough values'):
        asyncio.run(backfill.backfill_financial_snapshots(session, 'GENERIC'))
    with Session(engine) as session:
        assert session.exec(select(FinancialSnapshot)).all() == []


def test_existing_formal_precedence_not_order_or_later_preliminary():
    formal = FinancialSnapshot(ticker='GENERIC', period='2026-Q2', provider='opendart',
        snapshot_type='full_statement', revenue=200, financial_period_end=date(2026,6,30),
        reported_date=date(2026,8,14))
    preliminary = formal.model_copy(update={'snapshot_type':'preliminary_earnings',
        'reported_date':date(2026,8,20), 'revenue':1})
    assert _earnings_quarters([preliminary, formal]) == [formal]
