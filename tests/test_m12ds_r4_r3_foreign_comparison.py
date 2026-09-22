from copy import deepcopy
from datetime import date
import json

import pytest

from app.models.financial import FinancialSnapshot
from app.services.sec_business_field_quality_service import sha
from app.services.sec_foreign_comparison_service import (
    current_projection, extract_occurrences, foreign_comparison_quality,
    occurrence_errors, period_from_headers,
)
from scripts.m12dr_financial_source_authority import comparative_facts, source_quality
from app.services.financial_observation_quality_service import digest


def document(*, prior="2025-04-01 to 2025-06-30", current="2026-04-01 to 2026-06-30", duplicate="", issuer="1234", accession="0000001234-26-000010", filed="2026-08-01", basis="Consolidated"):
    html = f'''<h2>{basis} Statements of Comprehensive Income</h2>
    <p>(In Thousands of New Taiwan Dollars)</p><table>
    <tr><th></th><th>{current}</th><th>{prior}</th></tr>
    <tr><td>NET REVENUE (Notes 20, 31 and 37)</td><td>150</td><td>100</td></tr>
    <tr><td>INCOME FROM OPERATIONS (Note 37)</td><td>30</td><td>(10)</td></tr>{duplicate}</table>'''
    return extract_occurrences(html, issuer_cik=issuer, accession=accession, document_type="6-K",
        filing_date=filed, source_url=f"https://www.sec.gov/Archives/edgar/data/{int(issuer)}/{accession.replace('-', '')}/statement.htm",
        payload_sha256="a" * 64)


def snapshot(items=None, ticker="RENAMED"):
    items = document() if items is None else items
    sample = items[0]
    row = FinancialSnapshot(ticker=ticker, period="2026-Q2", provider="sec_foreign_filing",
        snapshot_type="preliminary_earnings", period_scope="single-quarter", period_type="Q2",
        financial_period_end=date(2026,6,30), filing_date=date.fromisoformat(sample["filing_date"]),
        source_filing_id=sample["accession"], source=sample["source_url"], currency="TWD",
        revenue=150000, operating_income=30000,
        raw_financial_fields=json.dumps([dict(field="foreign_business_occurrences", occurrences=items)]))
    return row


def quality(row=None, candidates=()):
    row = snapshot() if row is None else row
    return foreign_comparison_quality(formal=row, candidates=candidates, ticker=row.ticker, cutoff=date(2026,9,22))


def resign(o):
    o["occurrence_id"] = sha({k:v for k,v in o.items() if k != "occurrence_id"})


def test_same_document_exact_comparisons_and_automatic_authority_binding():
    row = snapshot()
    q = quality(row)
    assert q["status"] == "PASS"
    assert len(q["comparative_observations"]) == 2
    assert q["comparative_observations"][1]["growth_pct"] is None
    inputs = dict(ticker=row.ticker, formal=row.model_dump(mode="json"), cutoff="2026-09-22", foreign_candidates=[])
    assert source_quality(dict(source_inputs=inputs, source_inputs_sha256=digest(inputs))) == q
    assert len(comparative_facts(q, ticker=row.ticker, issuer_id="CIK:0000001234")) == 2


@pytest.mark.parametrize("prior", ["2025-01-01 to 2025-06-30", "2025-04-02 to 2025-06-30", "Q2 2025", "2024-04-01 to 2024-06-30"])
def test_incompatible_or_unresolved_period_denied(prior):
    q = quality(snapshot(document(prior=prior)))
    assert q["status"] == "FAIL"
    assert not q["comparative_observations"]


def test_same_provider_prior_filing_allowed_without_direction_bias():
    current = [o for o in document() if o["period_end"] == "2026-06-30"]
    old = document(current="2025-04-01 to 2025-06-30", prior="2024-04-01 to 2024-06-30",
                   accession="0000001234-25-000009", filed="2025-08-01")
    assert quality(snapshot(current), [snapshot(old)])["status"] == "PASS"
    prior_row = snapshot(old)
    prior_row.provider = "sec_companyfacts"
    assert quality(snapshot(current), [prior_row])["status"] == "FAIL"


@pytest.mark.parametrize("key,value", [("currency","USD"), ("statement_basis","separate"), ("provider","sec_companyfacts"),
    ("period_start",None), ("issuer_cik","9999"), ("source_payload_sha256","bad"), ("duration_days",100),
    ("source_url","https://example.com/statement.htm"), ("filing_date","2026-09-23"), ("unit_scale",1)])
def test_mutated_lineage_denied(key,value):
    items = document()
    for o in items:
        if o["period_end"] == "2025-06-30":
            o[key] = value
            resign(o)
    assert quality(snapshot(items))["status"] == "FAIL"


def test_duplicate_prior_conflict_is_field_scoped_and_no_value_selection():
    items = document(duplicate='<tr><td>NET REVENUE</td><td>150</td><td>999</td></tr>')
    q = quality(snapshot(items))
    assert [c["metric"] for c in q["comparative_observations"]] == ["operating_income"]
    assert any("prior_field_occurrence_conflict" in c["denial_reasons"] for c in q["comparison_attempts"])


def test_missing_operating_income_does_not_deny_revenue():
    items = [o for o in document() if o["field"] == "revenue"]
    row = snapshot(items)
    row.operating_income = None
    assert [c["metric"] for c in quality(row)["comparative_observations"]] == ["revenue"]


def test_renamed_issuer_policy_and_deduplication():
    items = document(issuer="5678", accession="0000005678-26-000010")
    q = quality(snapshot(items + deepcopy(items), ticker="ANOTHER"))
    assert q["status"] == "PASS"
    assert [c["delta"] for c in q["comparative_observations"]] == [50000,40000]


def test_absolute_only_never_direction():
    assert quality(snapshot([o for o in document() if o["period_end"] == "2026-06-30"]))["status"] == "FAIL"


def test_explicit_merged_duration_and_year_headers_not_percentage_columns():
    html = '''<h2>Consolidated Statements of Income</h2><p>In Thousands of New Taiwan Dollars</p><table>
    <tr><td></td><td colspan="4">For the Three Months Ended June 30</td><td colspan="2">For the Six Months Ended June 30</td></tr>
    <tr><td></td><td colspan="2">2026</td><td colspan="2">2025</td><td colspan="2">2026</td></tr>
    <tr><td></td><td>Amount</td><td>%</td><td>Amount</td><td>%</td><td>Amount</td><td>%</td></tr>
    <tr><td>Net revenue</td><td>$ 150</td><td>100</td><td>$ 100</td><td>100</td><td>$ 250</td><td>100</td></tr></table>'''
    items = extract_occurrences(html, issuer_cik="1234", accession="0000001234-26-000010", document_type="6-K",
        filing_date="2026-08-01", source_url="https://www.sec.gov/Archives/edgar/data/1234/000000123426000010/statement.htm",payload_sha256="a"*64)
    assert len(items) == 3
    assert [o["period_start"] for o in items] == ["2026-04-01","2025-04-01","2026-01-01"]
    assert quality(snapshot(items))["status"] == "PASS"


def test_bare_quarter_labels_never_dates():
    assert period_from_headers(["2Q26 Amount"])["period_start"] is None
    assert period_from_headers(["Three months ended June 29, 2026"])["period_start"] is None


def test_duplicate_current_conflict_leaves_clean_field():
    items = document(duplicate='<tr><td>NET REVENUE</td><td>999</td><td>100</td></tr>')
    assert [c["metric"] for c in quality(snapshot(items))["comparative_observations"]] == ["operating_income"]
    assert "revenue" not in current_projection(items)


def test_prior_hard_taint_and_selected_projection_mutation():
    current = [o for o in document() if o["period_end"] == "2026-06-30"]
    old = snapshot(document(current="2025-04-01 to 2025-06-30", prior="2024-04-01 to 2024-06-30",
                            accession="0000001234-25-000010", filed="2025-08-01"))
    old.financial_hard_errors = '["source_conflict"]'
    assert quality(snapshot(current), [old])["status"] == "FAIL"
    row = snapshot()
    row.revenue = 1
    assert [c["metric"] for c in quality(row)["comparative_observations"]] == ["operating_income"]


def test_occurrence_identity_tamper():
    o = document()[0]
    o["value"] = 1
    assert "foreign_occurrence_identity_mismatch" in occurrence_errors(o, date(2026,9,22))


def test_no_statement_basis_or_component_semantic_invention():
    items = document(basis="Unknown")
    assert items == []


def test_scan_projects_exact_source_without_rebinding_primary_to_exhibit():
    import asyncio
    import httpx
    from sqlmodel import Session, SQLModel, create_engine, select
    from app.services.sec_financial_snapshot_service import SecFinancialSnapshotService
    html = '''<h2>Consolidated Statements of Income</h2><p>In Thousands of New Taiwan Dollars</p>
    <table><tr><td></td><td>2026-04-01 to 2026-06-30</td><td>2025-04-01 to 2025-06-30</td></tr>
    <tr><td>Net revenue</td><td>150</td><td>100</td></tr></table>'''
    def handler(request):
        if '/submissions/' in str(request.url):
            return httpx.Response(200, json={'filings': {'recent': dict(form=['6-K'],
                accessionNumber=['0000001234-26-000010'], primaryDocument=['statement.htm'], filingDate=['2026-08-01'])}})
        if request.url.path.endswith('index.json'):
            return httpx.Response(200, json={'directory': {'item': [{'name': 'ex99.htm'}]}})
        return httpx.Response(200, text=html if request.url.path.endswith('/statement.htm') else '<p>No results</p>')
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await SecFinancialSnapshotService()._scan_foreign_filings(client, '0000001234')
    result = asyncio.run(run())
    parsed = result['parsed_statement']
    assert parsed['source_url'].endswith('/statement.htm')
    assert parsed['revenue'] == 150000
    engine = create_engine('sqlite://')
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        for _ in range(2):
            SecFinancialSnapshotService._upsert_foreign_preliminary_snapshot(session, 'RENAMED', parsed)
        rows = session.exec(select(FinancialSnapshot)).all()
        assert len(rows) == 1
        assert quality(rows[0])['status'] == 'PASS'


def test_authoritative_prior_conflict_not_bypassed_by_older_filing():
    current = snapshot(document(duplicate='<tr><td>NET REVENUE</td><td>150</td><td>999</td></tr>'))
    prior = snapshot(document(current='2025-04-01 to 2025-06-30', prior='2024-04-01 to 2024-06-30',
                              accession='0000001234-25-000010', filed='2025-08-01'))
    assert [c['metric'] for c in quality(current, [prior])['comparative_observations']] == ['operating_income']
