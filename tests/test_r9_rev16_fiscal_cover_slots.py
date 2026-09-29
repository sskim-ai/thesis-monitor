import asyncio
from datetime import date
import json

import httpx
import pytest

from app.services.bounded_financial_acquisition import (
    collect,
    exhibit_selection,
    sec_base,
    AcquisitionDenied,
)
from app.services.bounded_financial_stock_owner import build_shadow_numeric_registry
from app.services.fiscal_comparability_metadata import NUMERIC_FIELDS, validate_metadata
from app.services.fpi_filing_document_graph import (
    document_slot_plan,
    build_graph,
    bind_graph,
    FORWARDING,
    EXHAUSTED,
)
from app.services.issuer_fiscal_week_policy import extract_policy, annual_comparability
from app.services.sec_fpi_financial_purpose import classify_document
from app.services.sealed_financial_reader import SealedFinancialReader
from app.services.sealed_financial_slots import financial_slots
from app.services.unified_snapshot_contract import digest
from app.services.unified_run_artifacts import sha256_bytes
from scripts.m12dr_financial_source_authority import comparative_facts
from test_r9_rev15_financial_owners import (
    plan,
    filing,
    submission,
    CALENDAR,
    fiscal_tuple,
    inline_html,
)
from test_r9_rev11_response_slots import run_slots, OWNER, CONFIG


def fiscal_fact():
    policy = extract_policy(CALENDAR.encode(), issuer="123", filing=filing("10-K"))
    a, b = fiscal_tuple(), fiscal_tuple("2024-06-29", "2025-06-27")

    def lineage(t, amount, ref):
        return dict(
            issuer_cik="123",
            amount=amount,
            amount_period_start=t["period_start"],
            amount_period_end=t["period_end"],
            currency="USD",
            statement_basis="entity_wide",
            receipt=t["source_document_id"],
            source_row_identity=ref,
            taxonomy="us-gaap",
            concept="Revenues",
        )

    comp = dict(
        metric="revenue",
        current={"lineage": lineage(a, 120, "current-occurrence")},
        comparison={"lineage": lineage(b, 100, "prior-occurrence")},
        delta=20,
        growth_pct=20,
        direction="higher",
        fiscal_comparability=annual_comparability(a, b, policy),
    )
    quality = dict(
        status="PASS",
        ticker="FICTIONAL",
        comparative_observations=[comp],
        formal_receipt=a["source_document_id"],
        quality_reason_codes=["FISCAL_WEEK_COUNT_DIFFERENCE"],
        limitations=[],
        contract="fixture",
        receipt_sha256="a" * 64,
        fiscal_metadata_policy=policy,
    )
    return comparative_facts(quality, ticker="FICTIONAL", issuer_id="CIK:0000000123")[0]


def test_annual_nonfinancial_routing_uses_official_labels_not_filename():
    p, f = plan(), filing("20-F")
    names = ["articles.htm", "cert.htm", "lease.htm", "unknown.htm", "financial.htm"]
    labels = [
        "Articles of Incorporation of Fictional Limited",
        "Certification of Chief Financial Officer required by Rule 13a-14(a)",
        "Land Lease with Local Government",
        "Exhibit 99",
        "Consent of auditor and Financial Statements",
    ]
    index = {
        "directory": {
            "item": [{"name": f["primaryDocument"], "type": "text.gif"}]
            + [{"name": name, "type": "text.gif"} for name in names]
        }
    }
    html = "".join(f'<a href="{name}">{label}</a>' for name, label in zip(names, labels))
    slots = document_slot_plan(index, html, p, f)
    assert slots["status"] == "PASS" and slots["candidate_count"] == 2
    assert {u.rsplit("/", 1)[-1] for u in slots["selected_urls"]} == {
        "unknown.htm",
        "financial.htm",
    }
    excluded = [
        r
        for r in slots["all_linked_identities"]
        if r["excluded_reason"] == "OFFICIAL_ANNUAL_EXHIBIT_DESCRIPTION_NON_FINANCIAL_NO_FETCH"
    ]
    assert len(excluded) == 3 and all(r["exact_references"] for r in excluded)
    # Unknown labels do not inherit exclusion authority from suggestive filenames.
    ambiguous = document_slot_plan(
        index, html.replace("Land Lease with Local Government", "Unclassified attachment"), p, f
    )
    assert ambiguous["status"] == "DENIED"
    current = document_slot_plan(index, html, p, {**f, "form": "6-K"})
    assert current["status"] == "DENIED"


def test_exact_metadata_registered_audit_only_and_no_direction_authority():
    f = fiscal_fact()
    registry = build_shadow_numeric_registry([f])
    metadata = [r for r in registry if r.get("audit_only")]
    assert len(metadata) == 4 and all(r["registered"] for r in registry)
    assert {r["field_path"].split(".")[-1] for r in metadata} == NUMERIC_FIELDS
    for row in metadata:
        assert not row["prose_allowed"] and not row["approved_labels"]
        assert (
            not row["investment_number_authority"]
            and not row["valuation_use"]
            and not row["directional_use"]
        )
        assert (
            row["source_fact_ref"] == f["fact_id"]
            and row["source_occurrence_refs"] == f["fields"]["source_occurrences"]
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown_sibling",
        "amount",
        "weeks",
        "receipt",
        "source_relation",
        "price_fact",
        "policy_tamper",
    ],
)
def test_fiscal_metadata_never_blanket_numeric_exclusion(mutation):
    f = fiscal_fact()
    m = f["fields"]["fiscal_comparability"]
    if mutation == "unknown_sibling":
        m["unknown_amount"] = 300
    if mutation == "amount":
        m["current_fiscal_year"] = 120000000
    if mutation == "weeks":
        m["current_weeks"] = 54
    if mutation == "receipt":
        m["policy_receipt_sha256"] = "b" * 64
    if mutation == "source_relation":
        f["fields"]["source_occurrences"] = []
    if mutation == "price_fact":
        f["fact_type"] = "valuation"
    if mutation == "policy_tamper":
        f["fiscal_metadata_policy"]["years"][0]["weeks"] = 52
    with pytest.raises((ValueError, KeyError)):
        validate_metadata(f)
    with pytest.raises((ValueError, KeyError)):
        build_shadow_numeric_registry([f])


def test_other_nested_number_stays_unregistered():
    f = fiscal_fact()
    f["fields"]["new_context"] = {"unknown": 99}
    assert any(
        not r["registered"] and r["field_path"] == "fields.new_context.unknown"
        for r in build_shadow_numeric_registry([f])
    )


def graph_fixture(
    *, linked=True, child_body=None, cross=False, label="Consolidated Financial Statements"
):
    p = plan()
    f = {**filing("6-K"), "reportDate": "2025-12-31"}
    base = sec_base(p, f)
    raw = (
        "<h1>FORM 6-K</h1><h2>EXHIBIT INDEX</h2>"
        + (
            f'<a href="attachment.htm">{label}</a>'
            if linked
            else "financial statements referenced without exact link"
        )
    ).encode()
    cf = {**f, "accessionNumber": filing("6-K", 2)["accessionNumber"]} if cross else f
    child = (child_body or inline_html()).encode()
    sources = [
        dict(url=base + f["primaryDocument"], filing=f, raw=raw),
        dict(url=sec_base(p, cf) + "attachment.htm", filing=cf, raw=child),
    ]
    docs = [classify_document(d["raw"], url=d["url"], filing=d["filing"], plan=p) for d in sources]
    payload = {
        "directory": {
            "item": [
                {"name": f["primaryDocument"], "type": "text.gif"},
                {"name": "attachment.htm", "type": "text.gif"},
            ]
        }
    }
    indexes = {f["accessionNumber"]: dict(payload=payload, raw_sha256=digest(payload))}
    return p, f, sources, docs, indexes


def test_exact_forwarding_relation_preserves_hashes_periods_and_no_fact_on_cover():
    p, f, sources, docs, indexes = graph_fixture()
    graph = build_graph(documents=docs, source_documents=sources, indexes=indexes, plan=p)
    assert len(graph["edges"]) == 1 and graph["edges"][0]["relation"] == FORWARDING
    edge = graph["edges"][0]
    assert edge["accession"] == f["accessionNumber"] and edge["cover_sha256"] == sha256_bytes(
        sources[0]["raw"]
    )
    assert edge["attachment_sha256"] == sha256_bytes(sources[1]["raw"]) and edge["economic_periods"]
    bind_graph(docs, graph)
    assert (
        docs[0]["purpose"] == "FORWARDING_COVER"
        and not docs[0]["financial_authority"]
        and not docs[0]["occurrences"]
    )


@pytest.mark.parametrize(
    "kw",
    [
        dict(linked=False),
        dict(child_body="Cash dividend adjustment"),
        dict(child_body="Unknown financial information"),
        dict(cross=True),
        dict(label="Unrelated financial statements"),
    ],
)
def test_relationship_negatives(kw):
    p, f, sources, docs, indexes = graph_fixture(**kw)
    assert not build_graph(documents=docs, source_documents=sources, indexes=indexes, plan=p)[
        "edges"
    ]


def test_missing_index_or_changed_raw_blocks_relationship():
    p, f, sources, docs, indexes = graph_fixture()
    assert not build_graph(documents=docs, source_documents=sources, indexes={}, plan=p)["edges"]
    sources[1]["raw"] += b"x"
    with pytest.raises(ValueError, match="source_identity"):
        build_graph(documents=docs, source_documents=sources, indexes=indexes, plan=p)


def test_conflicting_attachments_not_discharged_by_cover():
    p, f, sources, docs, indexes = graph_fixture()
    second = dict(
        url=sec_base(p, f) + "second.htm", filing=f, raw=inline_html(value="121").encode()
    )
    sources.append(second)
    docs.append(classify_document(second["raw"], url=second["url"], filing=f, plan=p))
    indexes[f["accessionNumber"]]["payload"]["directory"]["item"].append(
        {"name": "second.htm", "type": "text.gif"}
    )
    graph = build_graph(documents=docs, source_documents=sources, indexes=indexes, plan=p)
    assert graph["conflicts"] and not graph["edges"]


def test_exact_slot_accounting_separates_images_but_never_text_by_filename():
    p, f, sources, docs, indexes = graph_fixture()
    index = indexes[f["accessionNumber"]]["payload"]
    index["directory"]["item"] += [
        {"name": f"ex99image{i}.jpg", "type": "image2.gif"} for i in range(7)
    ]
    slots = document_slot_plan(index, sources[0]["raw"].decode(), p, f)
    assert (
        slots["selected_urls"] == [sources[1]["url"]] and slots["remaining_attachment_slots"] == 1
    )
    assert sum(r["asset_class"] == "IMAGE_ASSET" for r in slots["all_linked_identities"]) == 7
    for r in slots["all_linked_identities"]:
        if r["asset_class"] == "IMAGE_ASSET":
            assert not r["selected_for_fetch"] and not r["slot_class_consumed"]
    index["directory"]["item"] += [
        {"name": "ex99-a.htm", "type": "image2.gif"},
        {"name": "ex99-b.htm", "type": "text.gif"},
    ]
    slots = document_slot_plan(index, sources[0]["raw"].decode(), p, f)
    assert slots["status"] == "DENIED" and slots["denial_reason"] == EXHAUSTED
    with pytest.raises(AcquisitionDenied, match=EXHAUSTED):
        exhibit_selection(index, sources[0]["raw"].decode(), p, f)


@pytest.mark.parametrize("excess", [False, True])
def test_sealed_annual_reserved_slot_survives_other_candidate_enumeration(tmp_path, excess):
    p = plan()
    p["run_id"] = "fresh-1"
    current = {**filing("6-K", 1), "primaryDocument": "financial-results.htm"}
    annual = {**filing("20-F", 99), "reportDate": "2025-12-31"}
    slots = financial_slots(p, owner="test-owner", owner_sha256=OWNER, config_sha256=CONFIG)
    run = run_slots(tmp_path, slots)
    calls = []

    def response(req):
        calls.append(str(req.url))
        if "submissions" in req.url.path:
            return httpx.Response(200, json=submission([current, annual]))
        if "companyfacts" in req.url.path:
            return httpx.Response(200, json={"cik": 123})
        if req.url.path.endswith("index.json"):
            f = annual if sec_base(p, annual) in str(req.url) else current
            names = [{"name": f["primaryDocument"], "type": "text.gif"}]
            if f == current:
                names += [
                    {"name": f"ex99-{i}.htm", "type": "text.gif"} for i in range(3 if excess else 1)
                ]
                names += [{"name": f"ex99-image{i}.jpg", "type": "image2.gif"} for i in range(7)]
            return httpx.Response(200, json={"directory": {"item": names}})
        return httpx.Response(200, content=b"<html>Document</html>")

    reader = SealedFinancialReader(
        p,
        tmp_path / "native",
        dispatcher=run,
        transport=httpx.MockTransport(response),
        user_agent="PLAN_CREDENTIAL",
    )
    capture = asyncio.run(collect(reader))
    assert any(
        d["url"] == sec_base(p, annual) + annual["primaryDocument"] for d in capture["documents"]
    )
    assert len(slots) == 14 and len(calls) <= 14 and not any(u.endswith(".jpg") for u in calls)
    assert bool(capture["denials"]) == excess
    accounting = capture["document_slot_accounting"]
    assert len(capture["frozen_slot_accounting"]["slots"]) == 14
    assert any(s["state"] == "RESERVED_UNUSED" for s in capture["frozen_slot_accounting"]["slots"])
    assert any(
        s["slot_class"] == "ANNUAL_PRIMARY" and s["state"] == "EXECUTED"
        for r in accounting
        for s in r["slots"]
    )
    assert (tmp_path / "native/fpi-document-slot-accounting.json").exists()


def test_unknown_same_accession_attachment_is_not_resolved_by_another_link():
    from app.models.financial import FinancialSnapshot
    from app.services.sec_fpi_field_selection import select_fields

    p, f, sources, docs, indexes = graph_fixture()
    graph = build_graph(documents=docs, source_documents=sources, indexes=indexes, plan=p)
    bind_graph(docs, graph)
    row = FinancialSnapshot(
        ticker=p["ticker"],
        period="2025-12-31",
        financial_period_end=date(2025, 12, 31),
        filing_date=date.fromisoformat(f["filingDate"]),
        source_filing_id=f["accessionNumber"],
        source=sources[1]["url"],
        provider="sec_foreign_filing",
        currency="TWD",
        revenue=120000,
        period_scope="annual",
        period_type="annual",
        is_cumulative=True,
        raw_financial_fields=json.dumps(
            [{"field": "foreign_business_occurrences", "occurrences": docs[1]["occurrences"]}]
        ),
    )
    _, good = select_fields(
        docs, [row], ticker=p["ticker"], cutoff=p["cutoff"], allow_inline_annual=True
    )
    assert good["status"] == "PASS"
    unknown = classify_document(
        b"Unresolved financial information", url=sec_base(p, f) + "other.htm", filing=f, plan=p
    )
    _, bad = select_fields(
        [*docs, unknown], [row], ticker=p["ticker"], cutoff=p["cutoff"], allow_inline_annual=True
    )
    assert (
        bad["status"] == "BLOCKED" and "NEWER_DOCUMENT_PURPOSE_UNRESOLVED" in bad["denial_reasons"]
    )


@pytest.mark.parametrize(
    "issue", [None, "parser", "acquisition", "missing_index", "unresolved_purpose"]
)
def test_partial_field_availability_requires_complete_exact_owner(issue):
    from app.services.sec_financial_source_completeness import completeness, field_completeness

    p, f, sources, docs, indexes = graph_fixture()
    bind_graph(docs, build_graph(documents=docs, source_documents=sources, indexes=indexes, plan=p))
    if issue == "parser":
        docs[1]["inline_owner"]["denials"].append(
            dict(field="operating_income", reason="INLINE_CONTEXT_OR_UNIT_AMBIGUOUS")
        )
    if issue == "unresolved_purpose":
        docs[0]["purpose"] = "UNKNOWN_PURPOSE"
    if issue == "missing_index":
        acquisition = {"document_slot_accounting": [dict(slots=[dict(state="UNAVAILABLE")])]}
    else:
        acquisition = {}
    complete = completeness(
        plan=p,
        acquisition=acquisition,
        inventory={"current_financial_plan": {"candidates": [f], "outside_bound": []}},
        documents=docs,
        uncaptured=[],
        acquisition_denials=["HTTP_FAILURE"] if issue == "acquisition" else [],
    )
    selection = {
        "fields": {"revenue": {"status": "PASS"}, "operating_income": {"status": "BLOCKED"}}
    }
    result = field_completeness(selection, docs, complete)
    assert result["fields"]["revenue"]["state"] == "QUALIFIED_CURRENT_PRIOR_PAIR"
    assert result["partial_field_consumption_allowed"] is (issue is None)
    assert (
        result["fields"]["operating_income"]["state"] == "SOURCE_COMPLETE_NO_QUALIFIED_FIELD"
    ) is (issue is None)


def test_newer_inline_field_gap_blocks_older_metric_fallback():
    from app.models.financial import FinancialSnapshot
    from app.services.sec_fpi_field_selection import select_fields

    p, f, sources, docs, indexes = graph_fixture()
    bind_graph(docs, build_graph(documents=docs, source_documents=sources, indexes=indexes, plan=p))
    row = FinancialSnapshot(
        ticker=p["ticker"],
        period="2025-12-31",
        financial_period_end=date(2025, 12, 31),
        filing_date=date.fromisoformat(f["filingDate"]),
        source_filing_id=f["accessionNumber"],
        source=sources[1]["url"],
        provider="sec_foreign_filing",
        currency="TWD",
        revenue=120000,
        period_scope="annual",
        period_type="annual",
        is_cumulative=True,
        raw_financial_fields=json.dumps(
            [{"field": "foreign_business_occurrences", "occurrences": docs[1]["occurrences"]}]
        ),
    )
    docs[1]["inline_owner"]["denials"].append(
        dict(field="revenue", reason="INLINE_CONTEXT_OR_UNIT_AMBIGUOUS")
    )
    _, current = select_fields(
        docs, [row], ticker=p["ticker"], cutoff=p["cutoff"], allow_inline_annual=True
    )
    assert current["status"] == "PASS"
    newer_filing = {**filing("6-K", 2), "reportDate": "2026-06-30"}
    newer = classify_document(
        inline_html(start="2026-01-01", end="2026-06-30").encode(),
        url=sec_base(p, newer_filing) + "newer.htm",
        filing=newer_filing,
        plan=p,
    )
    newer["inline_owner"]["denials"].append(
        dict(field="revenue", reason="INLINE_CONTEXT_OR_UNIT_AMBIGUOUS")
    )
    _, result = select_fields(
        [*docs, newer], [row], ticker=p["ticker"], cutoff=p["cutoff"], allow_inline_annual=True
    )
    assert "LATEST_FIELD_EXACT_OWNER_UNRESOLVED" in result["denial_reasons"]
