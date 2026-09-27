import asyncio
from copy import deepcopy
from datetime import date
import json

import httpx
import pytest

from app.services.sec_foreign_statement_boundary_service import (
    unit_candidates,
    document_evidence_class,
)
from app.services.sec_foreign_comparison_service import foreign_comparison_quality
from app.services.sec_fpi_field_selection import select_fields, reconcile_historical_denials
from app.services.sec_fpi_financial_purpose import (
    candidate_inventory,
    bind_nonfinancial_embedded_assets,
)
from app.services.bounded_fpi_followup import (
    make_followup_plan,
    request_manifest,
    verify_frozen_followup,
)
from app.services.fpi_coverage_window import (
    make_window_plan,
    WindowReader,
    make_window_exhibit_plan,
)
from app.services.unified_snapshot_contract import digest
from app.services.unified_run_artifacts import durable_json
from app.services.bounded_financial_acquisition import AcquisitionDenied, SystemicStop, sec_base
from test_m12ds_r4_r4_foreign_boundaries import html_rows, TABLE, heading
from test_m12ds_r4_r3_foreign_comparison import snapshot as base_snapshot, document
from test_residual_financial_semantics import purpose, html_statement
from test_bounded_financial_acquisition import plan, filing, submission


def snapshot(rows):
    value = base_snapshot(rows, ticker="TSM")
    value.currency = rows[0]["currency"]
    value.financial_period_end = date.fromisoformat(max(r["period_end"] for r in rows))
    for metric in ("revenue", "operating_income"):
        current = [
            r
            for r in rows
            if r["field"] == metric and r["period_end"] == value.financial_period_end.isoformat()
        ]
        setattr(value, metric, current[0]["value"] if current else None)
    return value


@pytest.mark.parametrize("prefix", ["", "Condensed ", "Unaudited Condensed "])
@pytest.mark.parametrize(
    "unit",
    [
        "In thousands of Renminbi",
        'Expressed in thousands of Renminbi ("RMB"), except for per share data',
        "RMB in thousands",
        "In thousands of RMB",
    ],
)
def test_structural_ifrs_half_year(prefix, unit):
    table = TABLE.replace("2026-04-01", "2026-01-01").replace("2025-04-01", "2025-01-01")
    rows = html_rows(
        f"<h2>{prefix}Consolidated Statements of Profit or Loss</h2><p>{unit}</p>" + table
    )
    assert len(rows) == 2
    assert all(
        (r["currency"], r["unit_scale"], r["period_scope"], r["is_cumulative"])
        == ("CNY", 1000, "half-year", True)
        for r in rows
    )
    s = snapshot(rows)
    s.period_scope, s.period_type, s.is_cumulative = "half-year", "half-year", True
    assert (
        foreign_comparison_quality(
            formal=s, candidates=[], ticker=s.ticker, cutoff=date(2026, 9, 27)
        )["status"]
        == "FAIL"
    )
    q = foreign_comparison_quality(
        formal=s,
        candidates=[],
        ticker=s.ticker,
        cutoff=date(2026, 9, 27),
        allow_reported_half_year=True,
    )
    assert q["status"] == "PASS" and len(q["comparative_observations"]) == 1


def test_units_and_statement_do_not_leak():
    assert not unit_candidates("Per-share data: RMB in thousands")
    assert not unit_candidates('RMB in thousands per share')
    caption = "<h2>Consolidated Statements of Profit or Loss</h2><p>In thousands of RMB</p>"
    assert (
        html_rows(caption + TABLE + "<h2>Separate Statements of Income</h2>" + TABLE)[-1][
            "statement_basis"
        ]
        == "consolidated"
    )
    assert not html_rows("<section>" + caption + "</section><section>" + TABLE + "</section>")
    assert not html_rows(caption + "<p>In millions of US Dollars</p>" + TABLE)
    assert not html_rows(
        "<p>Per-share data: RMB in thousands</p><h2>Consolidated Statements of Profit or Loss</h2>"
        + TABLE
    )
    assert (
        html_rows(heading("Separate", "Millions of US Dollars") + TABLE + caption + TABLE)[-1][
            "currency"
        ]
        == "CNY"
    )


def test_review_requires_review_procedure_and_interim_standard():
    assert document_evidence_class("Independent Auditor’s Report") is None
    assert (
        document_evidence_class(
            "Independent Auditor’s Report. We have reviewed the accompanying condensed consolidated statements. IAS34 Interim Financial Reporting."
        )["evidence_class"]
        == "AUDITOR_REVIEWED_INTERIM_STATEMENT"
    )


def financial_doc(rows):
    return {
        "accession": rows[0]["accession"],
        "financial_authority": True,
        "purpose": "FINANCIAL_STATEMENTS",
        "filing_date": rows[0]["filing_date"],
        "document_identity": rows[0]["source_url"],
        "occurrences": rows,
    }


@pytest.mark.parametrize(
    "body",
    [
        "Changes in shareholdings of directors",
        "Waiver from Strict Compliance with Rule 8A.18",
        "Monthly revenue for August",
        "Cash dividend adjustment",
    ],
)
def test_nonfinancial_does_not_supersede_fields(body):
    rows = document()
    nonfinancial = purpose(body, {**filing("6-K", 2), "filingDate": "2026-09-20"})
    selected, receipt = select_fields(
        [financial_doc(rows), nonfinancial], [snapshot(rows)], ticker="TSM", cutoff="2026-09-27"
    )
    assert receipt["status"] == "PASS" and len(selected) == 2


def test_unknown_newer_and_missing_primary_fail_closed():
    rows = document()
    unknown = purpose(
        "Financial results attached", {**filing("6-K", 2), "filingDate": "2026-09-20"}
    )
    for docs, uncaptured in (
        ([financial_doc(rows), unknown], []),
        ([financial_doc(rows)], [{"accessionNumber": "missing", "filingDate": "2026-09-20"}]),
    ):
        selected, receipt = select_fields(
            docs, [snapshot(rows)], ticker="TSM", cutoff="2026-09-27", uncaptured=uncaptured
        )
        assert not selected and receipt["status"] == "BLOCKED"


def test_newer_bad_field_does_not_demote_other_field():
    rows = document()
    later = document(
        current="2026-07-01 to 2026-08-31",
        prior="2025-07-01 to 2025-08-31",
        accession="0000001234-26-000099",
        filed="2026-09-20",
    )
    later = [r for r in later if r["field"] == "revenue"]
    selected, receipt = select_fields(
        [financial_doc(rows), financial_doc(later)],
        [snapshot(rows)],
        ticker="TSM",
        cutoff="2026-09-27",
    )
    assert len(selected) == 1 and selected[0].revenue is None
    assert receipt["fields"]["revenue"]["status"] == "BLOCKED"
    assert receipt["fields"]["operating_income"]["status"] == "PASS"


def test_ambiguous_same_period_is_not_resolved_by_filing_date():
    a, b = document(), document(accession="0000001234-26-000099", filed="2026-09-20")
    selected, receipt = select_fields(
        [financial_doc(a), financial_doc(b)],
        [snapshot(a), snapshot(b)],
        ticker="TSM",
        cutoff="2026-09-27",
    )
    assert not selected
    assert "AMBIGUOUS_CURRENT_FIELD_AUTHORITY" in receipt["denial_reasons"]


def test_mixed_qtd_halfyear_comparison_denied_even_opt_in():
    rows = document(prior="2025-01-01 to 2025-06-30")
    s = snapshot(rows)
    assert (
        foreign_comparison_quality(
            formal=s,
            candidates=[],
            ticker=s.ticker,
            cutoff=date(2026, 9, 27),
            allow_reported_half_year=True,
        )["status"]
        == "FAIL"
    )


def test_reviewed_authority_not_value_choice():
    a, b = document(), document(accession="0000001234-26-000099", filed="2026-09-20")
    from test_m12ds_r4_r3_foreign_comparison import resign

    for row in a:
        row["document_evidence_class"] = {"evidence_class": "AUDITOR_REVIEWED_INTERIM_STATEMENT"}
        resign(row)
    selected, receipt = select_fields(
        [financial_doc(a), financial_doc(b)],
        [snapshot(a), snapshot(b)],
        ticker="TSM",
        cutoff="2026-09-27",
    )
    assert len(selected) == 2 and all(
        r["source_accession"] == a[0]["accession"] for r in receipt["fields"].values()
    )


def test_unrelated_historical_denials_preserved_not_blindly_cleared():
    rows = document()
    docs = [financial_doc(rows)]
    _, chosen = select_fields(docs, [snapshot(rows)], ticker="TSM", cutoff="2026-09-27")
    old = {
        "effective_denials": ["SEC_DOCUMENT_BOUND_EXHAUSTED", "IDENTITY_FAILURE"],
        "diagnostics": [{"filing": {"accessionNumber": "old", "filingDate": "2025-01-01"}}],
    }
    result = reconcile_historical_denials(old, docs, chosen)
    assert result["effective_denials"] == ["IDENTITY_FAILURE"]
    assert result["historical_denials_preserved"] == old["effective_denials"]
    changed = deepcopy(chosen)
    changed["fields"]["revenue"]["prior_source_accession"] = "old"
    assert (
        reconcile_historical_denials(old, docs, changed)["effective_denials"]
        == old["effective_denials"]
    )


def test_embedded_resource_requires_exact_nonfinancial_parent():
    p, f = plan(foreign=True), filing("6-K")
    raw = b'<p>Restricted share award plan</p><img src="logo.jpg">'
    for primary, expected in (
        (raw, "NONFINANCIAL_EMBEDDED_ASSET"),
        (html_statement().encode() + b'<img src="logo.jpg">', "UNKNOWN_PURPOSE"),
    ):
        docs = [purpose(primary.decode(), f), purpose("\ufffd", f, "logo.jpg")]
        sources = [{"raw": primary, "filing": f}, {"raw": b"\xff\xd8\xfffake", "filing": f}]
        bind_nonfinancial_embedded_assets(docs, sources, p)
        assert docs[1]["purpose"] == expected and not docs[1]["financial_authority"]


def window_fixture(n=18):
    p = plan(foreign=True)
    payload = submission([filing("6-K", i + 1) for i in range(n)])
    raw = json.dumps(payload).encode()
    first_plan = make_followup_plan(p, raw, [])
    first = {
        "plan": first_plan,
        "complete_exact_manifest": True,
        "uncaptured": [],
        "documents": [{'raw': b'<p>Cash dividend adjustment</p>', 'filing': f,
            'url': sec_base(p, f) + f['primaryDocument']} for f in first_plan['candidates']],
        "receipt_sha256": "a" * 64,
    }
    exhibits = {
        "plan": {
            "phase1_plan_sha256": digest(first_plan),
            "phase1_receipts_sha256": "a" * 64,
            "exact_requests": [],
        },
        "documents": [],
        "phase2_result_sha256": "b" * 64,
    }
    return p, raw, first, exhibits


def test_window_exact_next_eight_and_never_third():
    p, raw, first, exhibits = window_fixture()
    value = make_window_plan(p, raw, [], first, exhibits)
    inventory = candidate_inventory(json.loads(raw), p)
    assert [r["accessionNumber"] for r in value["candidates"]] == [
        r["accessionNumber"] for r in inventory["candidates"][8:16]
    ]
    assert len(value["exact_requests"]) == 16 and value["maximum_HTTP_attempts"] == 48
    assert value["overall_maximum_HTTP_attempts"] == 57
    for n in (0, 1, 3, 4):
        with pytest.raises(ValueError):
            make_window_plan(p, raw, [], first, exhibits, window_number=n)


@pytest.mark.parametrize(
    "mutation", ["missing", "uncaptured", "exhibit", "financial", "source", "window"]
)
def test_window_prerequisites(mutation):
    p, raw, first, exhibits = window_fixture()
    if mutation == "missing":
        first["complete_exact_manifest"] = False
    if mutation == "uncaptured":
        first["uncaptured"] = [first["plan"]["candidates"][0]]
    if mutation == "exhibit":
        exhibits["plan"]["exact_requests"] = [{}]
    if mutation == "financial":
        f = first["plan"]["candidates"][0]
        first["documents"] = [
            {
                "raw": html_statement().encode(),
                "filing": f,
                "url": sec_base(p, f) + f["primaryDocument"],
            }
        ]
    if mutation == "source":
        raw = raw + b" "
    if mutation == "window":
        first["plan"]["candidates"].reverse()
    with pytest.raises(ValueError):
        make_window_plan(p, raw, [], first, exhibits)


def test_window_mock_nonfailfast_and_receipt_tamper(tmp_path):
    p, raw, first, exhibits = window_fixture(9)
    value = make_window_plan(p, raw, [], first, exhibits)
    durable_json(tmp_path / "plan.json", value)
    durable_json(
        tmp_path / "request-manifest.json",
        [{"request": r, "request_sha256": digest(r)} for r in request_manifest(value)],
    )
    calls = []

    def transport(request):
        calls.append(str(request.url))
        return httpx.Response(
            403 if len(calls) == 1 else 200, text="<p>Cash dividend adjustment</p>"
        )

    reader = WindowReader(value, tmp_path, transport=httpx.MockTransport(transport))
    reader.select(value["candidates"])
    with pytest.raises(AcquisitionDenied):
        asyncio.run(reader.read(**value["exact_requests"][0]))
    asyncio.run(reader.read(**value["exact_requests"][1]))
    durable_json(tmp_path / "receipts.json", reader.receipts)
    result = verify_frozen_followup(value, [], tmp_path)
    assert result["logical_requests"] == 2 and len(result["documents"]) == 1
    second = make_window_exhibit_plan(p, result, tmp_path)
    assert not second["exact_requests"]
    with pytest.raises(SystemicStop):
        asyncio.run(reader.read("discovery", "https://data.sec.gov/submissions/CIK0000000123.json"))
    with pytest.raises(ValueError):
        verify_frozen_followup({**value, "maximum_HTTP_attempts": 99}, [], tmp_path)
