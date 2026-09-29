from copy import deepcopy

import pytest

from app.services.sec_logical_cell_reference import (
    LogicalCellReferenceGroup, ReferenceTarget, logical_reference_inventory,
)
from app.services.fpi_filing_document_graph import logical_document_purpose, document_slot_plan
from test_r9_rev15_financial_owners import plan, filing


def inventory(source, accession="acc"):
    return logical_reference_inventory(source, accession=accession, filing_form="20-F",
        source_document="https://example.test/primary.htm",
        resolve=lambda ref: None if ref.startswith("https:") else ReferenceTarget(
            canonical_href=ref, document_identity=ref.split("#")[0]))


def anchor(label, ref="ex.htm"):
    return f'<div><span><a href="{ref}">{label}</a></span></div>'


def cell(content):
    return '<table><tr><td>' + content + '</td></tr></table>'


def test_raw_join_preserves_split_word_punctuation_and_exact_utf8_spans():
    source = cell(' '.join(anchor(t) for t in ["Consolidated Financial Statements for the ",
        "S", "ix", " Months Ended June ", "3", "0", ", ", "2026 and Auditors’ Review"]))
    result = inventory(source)
    assert len(result["groups"]) == 1
    group = result["groups"][0]
    assert len(group["anchors"]) == 8
    assert group["normalized_label"] == (
        "Consolidated Financial Statements for the Six Months Ended June 30, 2026 and Auditors’ Review")
    assert logical_document_purpose([group], filing("20-F")) == (False, None)
    for a in group["anchors"]:
        assert source.encode()[a["byte_start"]:a["byte_end"]].decode() == a["exact_html"]
    assert result == inventory(source)


@pytest.mark.parametrize("separator", ["plain text", '<a href="other.htm">Other</a>',
    '<a>unowned</a>', '<a href="https://elsewhere.test">External</a>', '<img src="chart.png">',
    '</td><td>', '</td></tr><tr><td>'])
def test_interruption_and_cross_cell_row_never_group(separator):
    result = inventory(cell(anchor("Articles of Incorporation ") + separator + anchor("continued")))
    assert all(len(g["anchors"]) == 1 for g in result["groups"])
    groups = [g for g in result["groups"] if g["document_identity"] == "ex.htm"]
    assert not logical_document_purpose(groups, filing("20-F"))[0]


@pytest.mark.parametrize("mutation", ["accession", "source_document", "cell_id", "row_id",
    "document_identity", "canonical_href", "duplicate", "order", "label", "hash", "span", "overlap", "unknown_order"])
def test_typed_group_rejects_forged_membership(mutation):
    raw = inventory(cell(anchor("Land Lease with ") + anchor("Local Government")))["groups"][0]
    raw = deepcopy(raw)
    raw.pop("group_sha256")
    if mutation in {"accession", "source_document", "cell_id", "row_id", "document_identity", "canonical_href"}:
        raw["anchors"][1][mutation] = "wrong"
    elif mutation == "duplicate":
        raw["anchors"][1] = raw["anchors"][0]
    elif mutation == "order":
        raw["anchors"].reverse()
    elif mutation == "label":
        raw["normalized_label"] += " invented"
    elif mutation == "hash":
        raw["anchors"][0]["html_sha256"] = "0"*64
    elif mutation == "overlap":
        raw["anchors"][1]["byte_end"] -= raw["anchors"][1]["byte_start"]
        raw["anchors"][1]["byte_start"] = 0
    elif mutation == "unknown_order":
        raw["anchors"][1]["dom_order"] = None
    else:
        raw["anchors"][0]["byte_end"] += 1
    with pytest.raises(ValueError):
        LogicalCellReferenceGroup.model_validate(raw)


@pytest.mark.parametrize("source", [
    '<table><tr><td><a href="ex.htm">Articles of Incorporation',
    '<table><tr><td><a href="ex.htm">Articles <a href="ex.htm">of Incorporation</a></a></td></tr></table>',
    '<table><tr><td><a href="ex.htm">Articles of Incorporation</a></tr></table>',
    '<table><tr><td><a href="ex.htm">Articles of Incorporation</a></th></tr></table>',
    '<table><tr><td><a href="ex.htm" href="other.htm">Articles of Incorporation</a></td></tr></table>',
    '<table><tr><td><a href="ex.htm">Articles of Incorporation</a><table><tr><td>x</td></tr></table></td></tr></table>',
    '<table><tr><td>outer<tr><td><a href="ex.htm">Articles of </a><a href="ex.htm">Incorporation</a></td></tr></td></tr></table>',
    '<table><tr><td>outer<td><a href="ex.htm">Articles of </a><a href="ex.htm">Incorporation</a></td></td></tr></table>',
])
def test_ambiguous_html_does_not_authorize_grouping(source):
    result = inventory(source)
    assert any(a["ambiguous"] for a in result["anchors"])
    assert not result["groups"]


def test_single_outside_cell_allowed_but_multiple_never_join():
    result = inventory(anchor("Articles of Incorporation") + anchor("continued"))
    assert len(result["groups"]) == 2
    assert not logical_document_purpose(result["groups"], filing("20-F"))[0]


def test_valid_nested_table_owns_a_distinct_row_and_cell():
    result = inventory(cell(cell(anchor("Articles of ") + anchor("Incorporation"))))
    assert len(result["groups"]) == 1
    assert len(result["groups"][0]["anchors"]) == 2
    assert not result["malformed_rows"]


@pytest.mark.parametrize("label", ["Land Lease with Government and lease liabilities",
    "Land Lease with Government financial statement note", "Land Lease with Government right-of-use assets",
    "Land Lease with Government lease accounting policy", "Articles of Incorporation and accounting schedules",
    "lease summary", "Financial Statements", "Earnings report"])
def test_financial_or_ambiguous_labels_remain_candidates(label):
    groups = inventory(cell(anchor(label)))["groups"]
    assert not logical_document_purpose(groups, filing("20-F"))[0]


def test_compatible_independent_groups_not_merged_conflicts_fail_closed():
    result = inventory(cell(anchor("Land Lease with Government")) + cell(anchor("Land Lease with City")))
    assert len(result["groups"]) == 2
    assert logical_document_purpose(result["groups"], filing("20-F"))[0] == "PROPERTY_LEASE_AGREEMENT_NON_FINANCIAL"
    conflict = inventory(cell(anchor("Land Lease with Government")) + cell(anchor("Financial Statements")))
    assert logical_document_purpose(conflict["groups"], filing("20-F")) == (
        False, "DOCUMENT_REFERENCE_PURPOSE_CONFLICT")


def test_fragment_targets_and_case_are_not_collapsed():
    assert len(inventory(cell(anchor("first", "ex.htm#a") + anchor("second", "ex.htm#b")))["groups"]) == 2
    assert len(inventory(cell(anchor("first", "EX.htm") + anchor("second", "ex.htm")))["groups"]) == 2


def test_unresolved_candidates_still_exhaust_unchanged_two_document_bound():
    p, f = plan(), filing("20-F")
    names = ["a.htm", "b.htm", "c.htm"]
    index = dict(directory=dict(item=[dict(name=f["primaryDocument"], type="text.gif")] +
                                [dict(name=n, type="text.gif") for n in names]))
    source = ''.join(cell(anchor("Financial ", n) + anchor("Statements", n)) for n in names)
    slots = document_slot_plan(index, source, p, f)
    assert slots["candidate_count"] == 3 and slots["content_slot_limit"] == 2
    assert slots["denial_reason"] == "FPI_FINANCIAL_DOCUMENT_CANDIDATE_BOUND_EXHAUSTED"
    assert not slots["selected_urls"]
