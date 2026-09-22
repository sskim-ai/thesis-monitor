from datetime import date

import pytest

from app.services.sec_foreign_comparison_service import extract_occurrences, occurrence_errors, foreign_comparison_quality
from app.services.sec_foreign_statement_boundary_service import statement_boundaries
from tests.test_m12ds_r4_r3_foreign_comparison import document, quality, resign, snapshot


TABLE = '''<table><tr><td></td><td>2026-04-01 to 2026-06-30</td><td>2025-04-01 to 2025-06-30</td></tr>
<tr><td>Net revenue</td><td>150</td><td>100</td></tr></table>'''


def html_rows(html):
    return extract_occurrences(html, issuer_cik="1234", accession="0000001234-26-000010", document_type="6-K",
        filing_date="2026-08-01", source_url="https://www.sec.gov/Archives/edgar/data/1234/000000123426000010/statement.htm", payload_sha256="a"*64)


def heading(basis, unit):
    return f"<h2>{basis} Statements of Income</h2><p>In {unit}</p>"


@pytest.mark.parametrize("a,b,unit_a,unit_b,expected", [
    ("Consolidated","Separate","Thousands of New Taiwan Dollars","Millions of US Dollars",("separate","USD",1000000)),
    ("Separate","Consolidated","Millions of US Dollars","Thousands of New Taiwan Dollars",("consolidated","TWD",1000)),
    ("Consolidated","Consolidated","Thousands of US Dollars","Millions of US Dollars",("consolidated","USD",1000000)),
])
def test_adjacent_statement_metadata_is_local(a,b,unit_a,unit_b,expected):
    rows = html_rows(heading(a,unit_a)+TABLE+heading(b,unit_b)+TABLE)
    assert len(rows) == 4
    later = rows[-1]
    assert tuple(later[k] for k in ("statement_basis","currency","unit_scale")) == expected
    assert occurrence_errors(later,date(2026,9,22)) == []


def test_explicit_section_shared_caption_and_flat_table_boundary():
    caption = heading("Consolidated", "Thousands of US Dollars")
    shared = html_rows("<section>"+caption+TABLE+TABLE+"</section>")
    assert len(shared) == 4
    assert len(html_rows(caption+TABLE+TABLE)) == 2


def test_ambiguous_intervening_caption_and_units_fail_closed():
    a = heading("Consolidated", "Thousands of US Dollars")
    ambiguous = "<div><h2>Consolidated Statements of Income / Separate Statements of Income</h2><p>In Thousands of US Dollars</p></div>"
    assert len(html_rows(a+TABLE+ambiguous+TABLE)) == 2
    assert len(html_rows(a+TABLE+heading("Separate","Thousands of US Dollars")+"<p>In Millions of US Dollars</p>"+TABLE)) == 2


def test_explicit_table_caption_and_layout_caption_table():
    caption = "<caption>Separate Statements of Income (In Millions of US Dollars)</caption>"
    assert html_rows(TABLE.replace("<table>","<table>"+caption))[0]["statement_basis"] == "separate"
    layout = "<div><table><tr><td>Consolidated Statements of Income</td></tr><tr><td>In Thousands of New Taiwan Dollars</td></tr></table></div>"
    rows = html_rows("<div>"+layout+"<div>"+TABLE+"</div></div>")
    assert len(rows) == 2 and rows[0]["currency"] == "TWD"
    assert statement_boundaries(layout)[0]["status"] == "FAIL"


def test_statement_caption_inside_previous_data_table_is_a_boundary():
    prior=TABLE.replace('<table>', '<table><caption>Separate Statements of Income (In Millions of US Dollars)</caption>')
    rows=html_rows('<section>'+heading('Consolidated','Thousands of New Taiwan Dollars')+prior+TABLE+'</section>')
    assert len(rows)==2 and all(r['currency']=='USD' for r in rows)


def versioned(*, newer_conflict=False, partial=False):
    current = snapshot([r for r in document() if r["period_end"] == "2026-06-30"])
    old = document(current="2025-04-01 to 2025-06-30",prior="2024-04-01 to 2024-06-30",accession="0000001234-25-000009",filed="2025-08-01")
    new = document(current="2025-04-01 to 2025-06-30",prior="2024-04-01 to 2024-06-30",accession="0000001234-25-000010",filed="2025-08-02",
                   duplicate='<tr><td>Net revenue</td><td>999</td><td>100</td></tr>' if newer_conflict else "")
    if partial:
        new = [r for r in new if r["field"] == "operating_income"]
    for rows, parent in ((old,None),(new,old[0]["accession"])):
        for row in rows:
            row["document_version"] = dict(report_identity="issuer-report-2025q2", supersedes_accession=parent,
                source_evidence="Explicit amendment replaces report 2025Q2" if parent else "Original report 2025Q2")
            resign(row)
    return current, snapshot(old), snapshot(new)


def test_authoritative_version_precedes_conflict_filter():
    current, old, new = versioned(newer_conflict=True)
    q = quality(current,[old,new])
    assert [r["metric"] for r in q["comparative_observations"]] == ["operating_income"]
    assert all(r["accession"]==new.source_filing_id for r in q["prior_version_authority"])
    assert "prior_field_occurrence_conflict" in q["fields"]["revenue"]["denial_reasons"]


def test_explicit_new_version_owns_clean_values():
    current, old, new = versioned()
    q = quality(current,[old,new])
    assert q["status"] == "PASS"
    assert all(r["comparison"]["lineage"]["receipt"] == new.source_filing_id for r in q["comparative_observations"])


def test_ambiguous_supersession_denied_even_equal_values():
    current, old, new = versioned()
    import json
    payload = json.loads(new.raw_financial_fields)
    for row in payload[0]["occurrences"]:
        row.pop("document_version")
        resign(row)
    new.raw_financial_fields = json.dumps(payload)
    assert quality(current,[old,new])["status"] == "FAIL"


def test_cutoff_before_amendment_uses_original():
    current, old, new = versioned()
    import json
    payload = json.loads(new.raw_financial_fields)
    for row in payload[0]["occurrences"]:
        row["filing_date"] = "2026-09-23"
        resign(row)
    new.raw_financial_fields = json.dumps(payload)
    q = foreign_comparison_quality(formal=current,candidates=[old,new],ticker=current.ticker,cutoff=date(2026,9,22))
    assert q["status"] == "PASS"
    assert all(r["comparison"]["lineage"]["receipt"] == old.source_filing_id for r in q["comparative_observations"])


def test_partial_amendment_does_not_invent_carry_forward():
    current, old, new = versioned(partial=True)
    assert [r["metric"] for r in quality(current,[old,new])["comparative_observations"]] == ["operating_income"]
