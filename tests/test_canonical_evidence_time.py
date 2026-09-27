from copy import deepcopy

import pytest

from app.services.canonical_evidence_time_service import (
    SourceTimeKind, UNDATED_METADATA_OWNERS, fact_sha256, project_canonical_time,
    source_as_of, source_time_kind,
)
from app.services.cross_market_decision_engine_service import build_decision_evidence_packet
from scripts.m12ds_r2_judgment_policy import frozen_fact_fields


def source(owner=None, date=""):
    owner = owner or ("security_identity:current", "security_identity", "deterministic_security_identity")
    return dict(zip(("fact_id", "fact_type", "source"), owner), as_of_date=date,
                fields={"state": "verified", "currency": "USD"})


def project(fact, ticker="FICTIONAL", clock="2026-09-27T08:38:36+00:00"):
    stock = {"ticker": ticker, "fact_catalog": [fact]}
    packet = {"market": "us", "assessment_date": "2026-09-27", "generated_at": clock,
              "stocks": [stock]}
    evidence = build_decision_evidence_packet(packet=packet, stock=stock)
    row = next(r.model_dump(mode="json") for r in evidence.evidence
               if r.ref_id == "canonical:" + fact["fact_id"])
    return packet, row


@pytest.mark.parametrize("owner", sorted(UNDATED_METADATA_OWNERS))
@pytest.mark.parametrize("date", ["", None])
def test_undated_metadata_preserves_exact_representation_and_separate_clock(owner, date):
    fact = source(owner, date)
    packet, row = project(fact)
    assert row["as_of"] == date
    assert row["source_time"]["kind"] == "UNDATED_DETERMINISTIC_METADATA"
    assert row["source_time"]["projection_at"] == packet["generated_at"]
    assert row["source_time"]["canonical_fact_sha256"] == fact_sha256(fact)
    assert frozen_fact_fields(packet, "FICTIONAL", [row])[row["ref_id"]]["fields"] == fact["fields"]


def test_projection_clock_metamorphic_does_not_create_source_time_or_change_economics():
    fact = source()
    original = deepcopy(fact)
    first, row = project(fact)
    later, changed = project(fact, clock="2030-01-01")
    assert row["as_of"] == changed["as_of"] == ""
    assert row["statement"] == changed["statement"]
    assert row["source_time"]["canonical_fact_sha256"] == changed["source_time"]["canonical_fact_sha256"]
    assert frozen_fact_fields(first, "FICTIONAL", [row]) == frozen_fact_fields(later, "FICTIONAL", [changed])
    assert fact == original


@pytest.mark.parametrize("legacy", [True, False])
def test_dated_exact_source_match(legacy):
    fact = source(date="2026-06-30")
    packet, row = project(fact)
    assert row["source_time"]["kind"] == "SOURCE_AS_OF"
    assert row["as_of"] == "2026-06-30"
    if legacy:
        row.pop("source_time")
    assert frozen_fact_fields(packet, "FICTIONAL", [row])


@pytest.mark.parametrize("canonical,projected", [
    ("2026-06-30", ""), ("2026-06-30", None), ("2026-06-30", "2026-09-27"),
    ("", "2026-09-27"), (None, ""), ("", None),
])
def test_strict_date_equality(canonical, projected):
    packet, row = project(source(date=canonical))
    row["as_of"] = projected
    with pytest.raises(ValueError, match="source_date_mismatch"):
        frozen_fact_fields(packet, "FICTIONAL", [row])


@pytest.mark.parametrize("owner", [
    ("earnings:latest", "earnings", "official_filing"),
    ("security_identity:current", "security_identity", "unverified_owner"),
    ("security_identity:current", "earnings", "deterministic_security_identity"),
])
def test_unknown_undated_family_fails_closed(owner):
    packet, row = project(source(owner))
    assert row["source_time"]["kind"] == "SOURCE_DATE_UNAVAILABLE"
    with pytest.raises(ValueError, match="undated_source_unclassified"):
        frozen_fact_fields(packet, "FICTIONAL", [row])


@pytest.mark.parametrize("field,value,error", [
    ("statement", "altered", "projection_mismatch"),
    ("source_ref", "stock.fact_catalog.other_security", "ref_mismatch"),
    ("ref_id", "canonical:other", "unknown_canonical_ref"),
    ("source_time", None, "metadata_binding_required"),
])
def test_projection_identity_and_statement_binding(field, value, error):
    packet, row = project(source())
    row[field] = value
    with pytest.raises(ValueError, match=error):
        frozen_fact_fields(packet, "FICTIONAL", [row])


@pytest.mark.parametrize("field,value", [
    ("subject_ticker", "OTHER"), ("canonical_ref", "canonical:other"),
    ("canonical_fact_sha256", "0" * 64), ("kind", "SOURCE_AS_OF"),
])
def test_typed_time_binding_cannot_be_rebound(field, value):
    packet, row = project(source())
    row["source_time"][field] = value
    with pytest.raises(ValueError, match="time_binding_mismatch"):
        frozen_fact_fields(packet, "FICTIONAL", [row])


def test_wrong_packet_subject_and_canonical_hash_mutation():
    packet, row = project(source())
    with pytest.raises(ValueError, match="subject_binding_mismatch"):
        frozen_fact_fields(packet, "OTHER", [row])
    packet["stocks"][0]["fact_catalog"][0]["source"] = "another_owner"
    with pytest.raises(ValueError):
        frozen_fact_fields(packet, "FICTIONAL", [row])


def test_malformed_date_clock_and_owner_are_not_verified():
    with pytest.raises(ValueError, match="source_date_type_invalid"):
        source_as_of(source(date=123))
    with pytest.raises(ValueError):
        project_canonical_time(source(), ticker="FICTIONAL", projection_at="unknown")
    malformed = source()
    malformed["source"] = {"not": "an_owner"}
    assert source_time_kind(malformed) == SourceTimeKind.SOURCE_DATE_UNAVAILABLE


def test_dated_source_metadata_hash_is_verified_when_present():
    packet, row = project(source(date="2026-06-30"))
    packet["stocks"][0]["fact_catalog"][0]["source"] = "changed_source"
    with pytest.raises(ValueError, match="time_binding_mismatch"):
        frozen_fact_fields(packet, "FICTIONAL", [row])
