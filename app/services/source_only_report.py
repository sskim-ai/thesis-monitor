"""Explicit offline source review, separate from accepted investment messages.

The trusted importer binds frozen evidence and raw bytes once per review owner.
Handles are process-local capabilities, not transferable economic receipts.
This module neither qualifies historical as-of truth nor issues source-use grants.
"""
from collections.abc import Mapping
from datetime import date
import hashlib
import json
import re
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, model_validator

Token = Annotated[str, StringConstraints(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9_./:@+\-]+$")]
Sha = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Reason = Annotated[str, StringConstraints(min_length=1, max_length=500, pattern=r"^[A-Z0-9_:/ .\-]+$")]


class Closed(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")


class RawOccurrenceV1(Closed):
    provider: Token
    source_owner: Token
    source_generation: Token
    response_sha256: Sha
    raw_bytes: int = Field(gt=0, le=24_000_000)
    request_sha256: Sha
    raw_member: Token
    json_pointer: str = Field(min_length=1, max_length=1000, pattern=r"^/")
    raw_lexical: str = Field(min_length=1, max_length=100, pattern=r"^[+\-]?[0-9.,]+$")
    captured_at: AwareDatetime
    period_start: date | None = None
    period_end: date | None = None
    asof: AwareDatetime | None = None
    published_at: AwareDatetime | None = None
    currency_label: Token | None = None
    unit_label: Token | None = None
    scale: Literal[None] = None
    concept: Token
    occurrence_id: Token
    qualification: Literal["RAW_OCCURRENCE_ONLY"] = "RAW_OCCURRENCE_ONLY"
    historical_asof_qualified: Literal[False] = False

    @model_validator(mode="after")
    def ordered_period(self):
        if (self.period_start is None) != (self.period_end is None):
            raise ValueError("incomplete_source_period")
        if self.period_start and self.period_start > self.period_end:
            raise ValueError("reversed_source_period")
        return self


class SourceReviewFieldV1(Closed):
    field_id: Token
    canonical_value: Literal[None] = None
    reason: Reason
    raw: RawOccurrenceV1 | None = None


class SourceOnlyReviewV1(Closed):
    contract: Literal["source-only-review-v1"] = "source-only-review-v1"
    consumer: Literal["SOURCE_ONLY_REPORT"] = "SOURCE_ONLY_REPORT"
    lane_id: Token
    market: Literal["KR", "US"]
    subject_id: Token
    issuer_id: Token | None = None
    generation: Token
    original_packet_generation: Token
    source_packet_sha256: Sha
    source_manifest_sha256: Sha
    replayed_at: AwareDatetime
    requested_cutoff: AwareDatetime
    snapshot_semantics: Literal["QUERY_TIME_SNAPSHOT"] = "QUERY_TIME_SNAPSHOT"
    finality_claim: Literal["NOT_CLAIMED"] = "NOT_CLAIMED"
    analysis_status: Literal["ANALYSIS_NOT_RUN"] = "ANALYSIS_NOT_RUN"
    decision_consumer: Literal["PRODUCTION_CONSUMER_NOT_AUTHORIZED"] = "PRODUCTION_CONSUMER_NOT_AUTHORIZED"
    d01_status: Literal["PARTIAL", "NOT_APPLICABLE"]
    d02_status: Literal["NOT_ISSUED"] = "NOT_ISSUED"
    accepted_authority: Literal[False] = False
    grants: tuple[()] = ()
    send_allowed: Literal[False] = False
    fields: tuple[SourceReviewFieldV1, ...] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique_and_historical(self):
        if len({row.field_id for row in self.fields}) != len(self.fields):
            raise ValueError("duplicate_source_review_field")
        for row in self.fields:
            if row.raw and row.raw.captured_at > self.replayed_at:
                raise ValueError("capture_after_replay")
        return self


class SourceOnlyReviewHandleV1(Closed):
    contract: Literal["source-only-review-handle-v1"] = "source-only-review-handle-v1"
    owner_id: Token
    report_id: Token
    view_sha256: Sha


def digest(value: SourceOnlyReviewV1) -> str:
    raw = json.dumps(value.model_dump(mode="json"), ensure_ascii=False,
                     sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _json_scalar(raw: bytes, pointer: str):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate_json_key")
            result[key] = value
        return result

    value = json.loads(raw, object_pairs_hook=pairs,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite_json")))
    for part in pointer[1:].split("/"):
        if re.search(r"~(?![01])", part):
            raise ValueError("invalid_json_pointer")
        key = part.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) and re.fullmatch(r"0|[1-9][0-9]*", key) else value[key]
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError("source_scalar_required")
    return str(value)


class SourceOnlyReportOwner:
    """Trusted backend import boundary; never expose construction to model output.

    approved_views must be derived from a verified immutable source manifest.
    This is read-only display authority, not D01/D02 or an economic owner.
    """
    def __init__(self, approved_views: tuple[SourceOnlyReviewV1, ...], sources: Mapping[str, bytes]):
        self._owner_id = uuid4().hex
        self._views = {}
        self._handles = {}
        for supplied in approved_views:
            view = SourceOnlyReviewV1.model_validate(supplied)
            if view.lane_id in self._views:
                raise ValueError("duplicate_review_lane")
            for field in view.fields:
                row = field.raw
                if row is None:
                    continue
                raw = sources.get(row.response_sha256)
                if raw is None or len(raw) != row.raw_bytes or hashlib.sha256(raw).hexdigest() != row.response_sha256:
                    raise ValueError("source_raw_binding_mismatch")
                if _json_scalar(raw, row.json_pointer) != row.raw_lexical:
                    raise ValueError("source_lexical_binding_mismatch")
            self._views[view.lane_id] = view.model_dump_json()

    def issue(self, lane_id: str) -> SourceOnlyReviewHandleV1:
        if lane_id not in self._views:
            raise ValueError("unapproved_review_lane")
        view = SourceOnlyReviewV1.model_validate_json(self._views[lane_id])
        handle = SourceOnlyReviewHandleV1(owner_id=self._owner_id, report_id=uuid4().hex, view_sha256=digest(view))
        self._handles[handle.report_id] = (handle.model_dump_json(), self._views[lane_id])
        return handle

    def lookup(self, handle: SourceOnlyReviewHandleV1) -> SourceOnlyReviewV1:
        handle = SourceOnlyReviewHandleV1.model_validate(handle)
        record = self._handles.get(handle.report_id)
        if handle.owner_id != self._owner_id or record is None or record[0] != handle.model_dump_json():
            raise ValueError("source_review_owner_lookup_denied")
        view = SourceOnlyReviewV1.model_validate_json(record[1])
        if digest(view) != handle.view_sha256:
            raise ValueError("source_review_content_mismatch")
        return view

    def revoke(self, handle: SourceOnlyReviewHandleV1) -> None:
        self.lookup(handle)
        del self._handles[handle.report_id]


def render_source_only_report(owner: SourceOnlyReportOwner, handle: SourceOnlyReviewHandleV1) -> dict:
    if type(owner) is not SourceOnlyReportOwner:
        raise ValueError("source_review_owner_capability_required")
    view = owner.lookup(handle)
    lines = [f"[SOURCE_ONLY_TYPED_VIEW / UNSENT] {view.subject_id}",
             "ANALYSIS_NOT_RUN / PRODUCTION_CONSUMER_NOT_AUTHORIZED",
             f"generation={view.generation}; source_packet_generation={view.original_packet_generation}",
             f"cutoff={view.requested_cutoff.isoformat()}; replay={view.replayed_at.isoformat()}",
             "QUERY_TIME_SNAPSHOT / finality NOT_CLAIMED / D02 NOT_ISSUED"]
    for field in view.fields:
        lines.append(f"{field.field_id}: 자료 부족 [{field.reason}]")
        raw = field.raw
        if raw:
            lines.append(f"  원문 관측만: {raw.raw_lexical}; 경제 사용 미승인")
            lines.append(f"  {raw.provider} / {raw.concept} / {raw.occurrence_id}")
            lines.append(f"  period={raw.period_start}..{raw.period_end}; unit_label={raw.unit_label}; scale=UNKNOWN")
            lines.append(f"  captured={raw.captured_at.isoformat()}; published={raw.published_at}; asof={raw.asof}")
            lines.append(f"  source_generation={raw.source_generation}; raw_sha256={raw.response_sha256}")
            lines.append(f"  raw_member={raw.raw_member}; pointer={raw.json_pointer}")
    return dict(contract="source-only-message-v1", consumer="SOURCE_ONLY_REPORT", lane_id=view.lane_id,
                text="\n".join(lines), view_sha256=digest(view), analysis_status="ANALYSIS_NOT_RUN",
                production_consumer_status="PRODUCTION_CONSUMER_NOT_AUTHORIZED", send_allowed=False,
                accepted_authority=False)
