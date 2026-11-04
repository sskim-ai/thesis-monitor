"""Source-review capability is deliberately not an investment output."""
import hashlib
from datetime import datetime, timezone

import pytest

from app.services.production_message_renderer import source_only_message
from app.services.source_only_report import (
    RawOccurrenceV1, SourceOnlyReportOwner, SourceOnlyReviewV1, SourceReviewFieldV1,
)

def fixture():
    raw = b'{"value":"2.5"}'
    at = datetime(2026, 1, 2, tzinfo=timezone.utc)
    occurrence = RawOccurrenceV1(provider="FICTIONAL", source_owner="test-source-owner",
        source_generation="source-v1", response_sha256=hashlib.sha256(raw).hexdigest(),
        raw_bytes=len(raw), request_sha256="1"*64, raw_member="fact.json", json_pointer="/value",
        raw_lexical="2.5", captured_at=at, concept="reported_fact", occurrence_id="one")
    view = SourceOnlyReviewV1(lane_id="fictional", market="US", subject_id="UNSEEN",
        generation="execution-v2", original_packet_generation="source-v1", source_packet_sha256="2"*64,
        source_manifest_sha256="3"*64, replayed_at=at, requested_cutoff=at, d01_status="PARTIAL",
        fields=(SourceReviewFieldV1(field_id="reported_fact", reason="SOURCE_USE_NOT_ISSUED", raw=occurrence),))
    return view, {occurrence.response_sha256:raw}

def test_source_report_is_explicit_unsent_and_not_accepted():
    view, raw = fixture()
    owner = SourceOnlyReportOwner((view,), raw)
    handle = owner.issue(view.lane_id)
    result = source_only_message(owner, handle)
    assert result["analysis_status"] == "ANALYSIS_NOT_RUN"
    assert not result["send_allowed"] and not result["accepted_authority"]
    assert "RAW" not in result["consumer"]
    assert source_only_message(owner, handle) == result
    owner.revoke(handle)
    with pytest.raises(ValueError, match="lookup_denied"):
        source_only_message(owner, handle)

def test_constructor_rejects_modified_raw_before_any_issue():
    view, raw = fixture()
    key = next(iter(raw))
    raw[key] += b" "
    with pytest.raises(ValueError, match="raw_binding"):
        SourceOnlyReportOwner((view,), raw)

@pytest.mark.parametrize("key,value", [("canonical_value", 2.5), ("unknown_claim", "BUY")])
def test_unqualified_field_cannot_become_numeric_judgment(key, value):
    view, _ = fixture()
    field = view.fields[0].model_dump()
    field[key] = value
    with pytest.raises(ValueError):
        SourceReviewFieldV1.model_validate(field)

def test_no_same_bytes_cross_owner_transfer():
    view, raw = fixture()
    first = SourceOnlyReportOwner((view,), raw)
    second = SourceOnlyReportOwner((view,), raw)
    with pytest.raises(ValueError, match="lookup_denied"):
        source_only_message(second, first.issue(view.lane_id))


def test_public_lookup_shaped_object_is_not_backend_capability():
    from types import SimpleNamespace
    view, _ = fixture()
    with pytest.raises(ValueError, match="capability_required"):
        source_only_message(SimpleNamespace(lookup=lambda _: view), {})
