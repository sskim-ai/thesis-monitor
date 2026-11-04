"""Opt-in historical comparison context; never economic or current-use authority."""
from __future__ import annotations

from datetime import date, datetime
from dataclasses import replace
from decimal import Decimal
import hashlib
import hmac
import json
import os
import secrets
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.unified_snapshot_contract import digest, encoded

CONTRACT = "reported-comparison-context-v1"
_BUILDER_PERMIT = object()
_KEY = secrets.token_bytes(32)
_PID = os.getpid()


class Closed(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ReportedOccurrence(Closed):
    occurrence_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    document_type: str = Field(min_length=1)
    filing_date: date
    publication_precision: Literal["DATE_ONLY"] = "DATE_ONLY"
    period_start: date
    period_end: date
    duration_days: int = Field(gt=0)
    duration_convention: Literal["SEC_END_MINUS_START"] = "SEC_END_MINUS_START"
    period_role: Literal["SINGLE_QUARTER"]
    value: Decimal
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    unit: str
    unit_scale: int = Field(gt=0)
    statement_basis: str
    taxonomy: str
    concept: str
    source_filing_fiscal_year: int | None
    source_filing_fiscal_label: str | None
    economic_period_fiscal_year: None = None
    economic_period_fiscal_basis: Literal["UNAVAILABLE_NOT_INFERRED"] = "UNAVAILABLE_NOT_INFERRED"
    raw_artifact_sha256: str
    projected_field_sha256: str

    @model_validator(mode="after")
    def period_and_unit(self):
        if (not self.value.is_finite() or self.unit != self.currency or self.unit_scale != 1
                or self.duration_days != (self.period_end - self.period_start).days
                or not self.period_start < self.period_end <= self.filing_date):
            raise ValueError("comparison_occurrence_period_or_unit")
        return self


class DartReportedOccurrence(ReportedOccurrence):
    duration_convention: Literal["OPENDART_COLUMN_END_MINUS_START"] = "OPENDART_COLUMN_END_MINUS_START"
    source_period_owner: Literal["financial-lineage-v2"] = "financial-lineage-v2"
    period_basis: Literal["SOURCE_COLUMN_AND_REPORT_CODE_CONVENTION"] = "SOURCE_COLUMN_AND_REPORT_CODE_CONVENTION"
    source_column: Literal["thstrm_amount", "frmtrm_q_amount"]
    report_code: Literal["11013", "11012", "11014"]
    source_business_year: int
    source_row_sha256: str
    source_request_sha256: str


class ReportedComparisonContext(Closed):
    contract: Literal["reported-comparison-context-v1"] = CONTRACT
    scope: Literal["HISTORICAL_SOURCE_ATTRIBUTION_ONLY"] = "HISTORICAL_SOURCE_ATTRIBUTION_ONLY"
    allowed_uses: tuple[Literal["CONTEXT"], ...] = ("CONTEXT",)
    direction_allowed: Literal[False] = False
    collection_start_byte_possession_proven: Literal[False] = False
    recurrence_verified: Literal[False] = False
    interpretation_confidence: None = None
    ticker: str
    security_id: str
    issuer_id: str
    market: Literal["us", "kr"]
    venue: str
    security_type: str
    share_class: str | None
    source_generation: str
    source_collection_started_at: datetime
    source_response_completed_at: tuple[datetime, ...]
    decision_projection_at: datetime
    fact_id: str
    fact_sha256: str
    selected_owner_sha256: str
    acquisition_sha256: str
    projection_sha256: str
    receipts_sha256: str
    quality_receipt_sha256: str
    current: ReportedOccurrence | DartReportedOccurrence
    prior: ReportedOccurrence | DartReportedOccurrence
    metric: Literal["revenue", "operating_income"]
    arithmetic_delta: Decimal
    limitations: tuple[str, ...] = (
        "Captured occurrences attributed to identified prior filings, not verified current truth.",
        "Acquisition, publication and original projection clocks remain distinct.",
        "No proof of byte possession at original collection start or retrospective filing-version authority.",
        "No direction, valuation, recurrence, timing, confidence or share-denominator permission.",
    )

    @model_validator(mode="after")
    def comparable(self):
        a, b = self.current, self.prior
        if (self.allowed_uses != ("CONTEXT",) or a.occurrence_id == b.occurrence_id
                or (a.currency, a.unit_scale, a.statement_basis, a.taxonomy, a.concept,
                    a.period_role, a.duration_days) !=
                   (b.currency, b.unit_scale, b.statement_basis, b.taxonomy, b.concept,
                    b.period_role, b.duration_days)
                or b.period_end >= a.period_start or a.period_end.year != b.period_end.year + 1
                or self.arithmetic_delta != a.value - b.value
                or any(t.utcoffset() is None for t in (*self.source_response_completed_at,
                     self.source_collection_started_at, self.decision_projection_at))
                or not self.source_response_completed_at
                or any(t < self.source_collection_started_at for t in self.source_response_completed_at)
                or any(t > self.decision_projection_at for t in self.source_response_completed_at)
                or any(o.filing_date >= self.decision_projection_at.date() for o in (a, b))):
            raise ValueError("comparison_basis_or_time_unqualified")
        return self


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _dart_comparison_row(rows, basis, spec):
    from app.services.opendart_financial_recovery_service import select_field_occurrence

    # Each consumed column must be unique under the existing selector, and
    # both selections must resolve to the same original normalized row.
    selected = [
        select_field_occurrence({basis: rows}, replace(spec, source_column=column))
        for column in ("thstrm_amount", "frmtrm_q_amount")
    ]
    _require(all(s.status == "selected" and s.row is not None for s in selected),
             "comparison_dart_consumed_column_ambiguous_or_missing")
    _require(selected[0].row == selected[1].row,
             "comparison_dart_consumed_columns_not_same_row")
    return selected[0]


def _dart_occurrence(*, fact, support, occurrence, role, plan, projection, receipts, financial_inputs):
    from app.services.bounded_financial_projection import REPORTED_FIELD_SPECS, _raw, verify_capture
    from app.services.kr_financial_lineage_service import opendart_field_lineage

    _require(financial_inputs is not None, "comparison_original_dart_capture_required")
    acquisition, directory = financial_inputs["acquisition"], financial_inputs["directory"]
    verify_capture(plan, acquisition, directory, receipts)
    lineage = support["lineage"]
    column = {"current": "thstrm_amount", "comparison": "frmtrm_q_amount"}[role]
    _require(lineage["source_column"] == column and lineage["amount_role"] == role
             and lineage["amount_period_type"] == "single_quarter"
             and lineage["reprt_code"] in {"11013", "11012", "11014"}
             and lineage["sj_div"] in {"IS", "CIS"}
             and lineage["source_row_identity"] == occurrence
             and not support["hard_denial_reasons"] and support["prose_eligible"],
             "comparison_dart_column_or_quality_unqualified")
    anchors = [r for r in projection["fields"]
               if r["metric"] == fact["fields"]["metric"]
               and r["source_document_id"] == lineage["rcept_no"]
               and r["statement_basis"] == lineage["statement_basis"]]
    _require(len(anchors) == 1, "comparison_dart_selected_anchor_required")
    anchor = anchors[0]
    _require(anchor["canonical_security_id"] == plan["security"]["canonical_security_id"]
             and anchor["provider_issuer_id"] == plan["issuer"]
             and anchor["ticker"] == plan["ticker"] and anchor["context_eligible"]
             and anchor["source_use"] == "ABSOLUTE_CONTEXT_ELIGIBLE"
             and not anchor["quality_errors"], "comparison_dart_anchor_identity")
    matches = [r for r in receipts if r.get("raw_sha256") == anchor["raw_artifact_sha256"]
               and not r.get("failure_class") and r.get("filing", {}).get("receipt_no") == lineage["rcept_no"]
               and r["filing"]["basis"] == lineage["fs_div"]]
    _require(len(matches) == 1 and matches[0]["sealed_generation_id"] == plan["run_id"],
             "comparison_dart_raw_receipt_required")
    receipt = matches[0]
    rows = json.loads(_raw(directory, receipt["artifact"], receipts))["list"]
    selection = _dart_comparison_row(rows, lineage["fs_div"],
                                     REPORTED_FIELD_SPECS[fact["fields"]["metric"]])
    _require(selection.status == "selected" and selection.row is not None,
             "comparison_dart_exact_row_required")
    raw_row = selection.row
    _require(raw_row["corp_code"] == plan["issuer"]
             and raw_row["rcept_no"] == lineage["rcept_no"]
             and str(raw_row["bsns_year"]) == str(lineage["bsns_year"])
             and raw_row["reprt_code"] == lineage["reprt_code"],
             "comparison_dart_filing_identity")
    replay = opendart_field_lineage(raw_row, logical_field=fact["fields"]["metric"],
        report_code=lineage["reprt_code"], source_column=column, selected=role == "current",
        requested_fs_div=selection.basis)
    _require(replay == lineage and replay["lineage_verified"],
             "comparison_dart_lineage_replay_mismatch")
    start, end = (date.fromisoformat(lineage[k]) for k in ("amount_period_start", "amount_period_end"))
    # The original report/column owner defines the period. A half-year label,
    # caller date, or cumulative sibling is never used to invent a quarter.
    return DartReportedOccurrence(
        occurrence_id=occurrence, document_id=lineage["rcept_no"],
        document_type=lineage["reprt_code"], filing_date=anchor["filing_date"],
        period_start=start, period_end=end, duration_days=(end-start).days,
        period_role="SINGLE_QUARTER", value=Decimal(str(raw_row[column]).replace(",", "")),
        currency=lineage["currency"], unit=anchor["unit"], unit_scale=anchor["unit_scale"],
        statement_basis=lineage["statement_basis"], taxonomy=lineage["account_id"].split("_", 1)[0],
        concept=lineage["account_id"], source_filing_fiscal_year=lineage["bsns_year"],
        source_filing_fiscal_label=lineage["source_labels"].get("thstrm_nm"),
        raw_artifact_sha256=anchor["raw_artifact_sha256"], projected_field_sha256=digest(lineage),
        source_column=column, report_code=lineage["reprt_code"],
        source_business_year=lineage["bsns_year"], source_row_sha256=digest(raw_row),
        source_request_sha256=receipt["request_sha256"])


def _projection(*, fact, plan, projection, selected_owner, receipts, generated_at, financial_inputs=None):
    from app.services.selected_financial_owner import validate
    from app.services.bounded_financial_stock_owner import reported_comparisons

    facts, denials = reported_comparisons(plan, projection)
    _require(not denials and fact in facts, "comparison_selected_quality_unproven")
    validate(selected_owner, projection=projection, facts=facts, bridge=None,
        current_financial_parent=(financial_inputs or {}).get('current_financial_parent'),
        current_purpose_intake=(financial_inputs or {}).get('current_purpose_intake'))
    _require(selected_owner["owner_type"] in {"direct_sec", "direct_opendart"},
             "comparison_issuer_bridge_not_qualified")
    _require(plan["identity_sha256"] == digest(plan["security"]),
             "comparison_security_identity_mismatch")
    security, fields = plan["security"], fact["fields"]
    issuer = ("CIK:" if plan["market"] == "us" else "DART:") + plan["issuer"]
    _require(fields["issuer_id"] == issuer and fields["source_ticker"] == plan["ticker"],
             "comparison_issuer_mismatch")
    _require(fact["fact_type"] == "earnings_comparison" and fields["period_type"] == "single_quarter",
             "comparison_source_ontology_or_period")
    occurrences = []
    for role, occurrence in zip(("current", "comparison"), fields["source_occurrences"], strict=True):
        if plan["provider"] == "opendart":
            occurrences.append(_dart_occurrence(fact=fact, support=fact["field_dependency_receipts"][role],
                occurrence=occurrence, role=role, plan=plan, projection=projection,
                receipts=receipts, financial_inputs=financial_inputs))
            continue
        candidates = [r for r in projection["fields"] if r["occurrence_id"] == occurrence]
        _require(plan["provider"] == "sec_edgar", "comparison_source_calendar_and_duration_owner_required")
        _require(len(candidates) == 1, "comparison_exact_occurrence_required")
        row = candidates[0]
        lineage = row["original_lineage"]
        support = fact["field_dependency_receipts"][role]
        _require(row["canonical_security_id"] == security["canonical_security_id"]
                 and row["provider_issuer_id"] == plan["issuer"]
                 and row["ticker"] == plan["ticker"] and row["metric"] == fields["metric"]
                 and row["context_eligible"] and row["source_use"] == "ABSOLUTE_CONTEXT_ELIGIBLE"
                 and not row["quality_errors"] and not support["hard_denial_reasons"]
                 and support["prose_eligible"]
                 and lineage["source_row_identity"] == support["lineage"]["source_row_identity"]
                 and lineage["source_document_id"] == support["lineage"]["receipt"]
                 and int(lineage["issuer_cik"]) == int(plan["issuer"])
                 and Decimal(str(row["value"])) == Decimal(str(support["lineage"]["amount"])),
                 "comparison_occurrence_owner_mismatch")
        raw = [r for r in receipts if r.get("raw_sha256") == row["raw_artifact_sha256"]
               and r.get("failure_class") is None]
        _require(len(raw) == 1 and raw[0]["sealed_generation_id"] == plan["run_id"],
                 "comparison_raw_receipt_required")
        occurrences.append(ReportedOccurrence(
            occurrence_id=occurrence, document_id=row["source_document_id"],
            document_type=row["source_document_type"], filing_date=row["filing_date"],
            period_start=row["period_start"], period_end=row["period_end"],
            duration_days=lineage["duration_days"], period_role=row["period_role"],
            value=Decimal(str(support["lineage"]["amount"])), currency=row["currency"],
            unit=row["unit"], unit_scale=row["unit_scale"], statement_basis=row["statement_basis"],
            taxonomy=lineage["taxonomy"], concept=lineage["concept"],
            source_filing_fiscal_year=row.get("fiscal_year"),
            source_filing_fiscal_label=row.get("source_fiscal_period_label"),
            raw_artifact_sha256=row["raw_artifact_sha256"], projected_field_sha256=digest(row)))
    a, b = occurrences
    _require((str(a.period_start), str(a.period_end), str(b.period_start), str(b.period_end)) ==
             (fields["period_start"], fields["period_end"], fields["prior_period_start"], fields["prior_period_end"])
             and (a.currency == b.currency == fields["currency"])
             and (a.statement_basis == b.statement_basis == fields["statement_basis"])
             and a.value == Decimal(str(fields["current_value"]))
             and b.value == Decimal(str(fields["prior_comparable_value"])),
             "comparison_fact_projection_mismatch")
    return ReportedComparisonContext(
        ticker=plan["ticker"], security_id=security["canonical_security_id"], issuer_id=issuer,
        market=plan["market"], venue=security["exchange"], security_type=security["security_type"],
        share_class=security.get("share_class"), source_generation=plan["run_id"],
        source_collection_started_at=plan["cutoff"],
        source_response_completed_at=tuple(r["finished_at"] for r in receipts if not r.get("failure_class")),
        decision_projection_at=generated_at, fact_id=fact["fact_id"], fact_sha256=digest(fact),
        selected_owner_sha256=selected_owner["envelope_sha256"],
        acquisition_sha256=selected_owner["selected_acquisition_sha256"],
        projection_sha256=digest(projection), receipts_sha256=digest(receipts),
        quality_receipt_sha256=fact["quality_receipt_sha256"], current=a, prior=b,
        metric=fields["metric"], arithmetic_delta=a.value - b.value)


def _stock_identity(stock):
    return digest({k: v for k, v in stock.items() if k != "reported_comparison_context"})


def _signature(payload):
    return hmac.new(_KEY, encoded(payload), hashlib.sha256).hexdigest()


def issue_context(*, stock, packet, facts, plan, projection, selected_owner, receipts,
                  financial_inputs=None, _permit=None):
    """Only the completed original-owner replay may issue this live capability."""
    _require(_permit is _BUILDER_PERMIT and os.getpid() == _PID, "comparison_backend_permit_required")
    entries, denials = {}, {}
    for fact in facts:
        try:
            entries[fact["fact_id"]] = _projection(fact=fact, plan=plan, projection=projection,
                selected_owner=selected_owner, receipts=receipts,
                generated_at=packet["generated_at"], financial_inputs=financial_inputs).model_dump(mode="json")
        except (ValueError, KeyError, TypeError) as exc:
            denials[fact["fact_id"]] = str(exc)
    payload = dict(contract=CONTRACT, ticker=plan["ticker"], source_generation=plan["run_id"],
        packet_id=packet["packet_id"], assessment_date=packet["assessment_date"],
        projection_at=packet["generated_at"], stock_sha256=_stock_identity(stock),
        entries=entries, denials=denials)
    return dict(payload=payload, signature=_signature(payload))


def context_for_fact(stock, fact, *, ticker, packet_id, assessment_date):
    """Native reconstruction checks the backend capability and exact consumed content."""
    envelope = stock.get("reported_comparison_context")
    if envelope is None:
        return None
    _require(isinstance(envelope, dict) and set(envelope) == {"payload", "signature"},
             "comparison_envelope_closed_shape")
    payload = envelope["payload"]
    _require(os.getpid() == _PID and isinstance(envelope["signature"], str)
             and hmac.compare_digest(envelope["signature"], _signature(payload)),
             "comparison_unissued_or_changed_context")
    _require(payload["contract"] == CONTRACT and payload["ticker"] == ticker
             and payload["packet_id"] == packet_id and payload["assessment_date"] == assessment_date
             and payload["stock_sha256"] == _stock_identity(stock),
             "comparison_native_binding_mismatch")
    data = payload["entries"].get(fact["fact_id"])
    if data is None:
        return None
    result = ReportedComparisonContext.model_validate(data)
    _require(result.fact_sha256 == digest(fact) and result.ticker == ticker
             and result.source_generation == payload["source_generation"]
             and result.decision_projection_at == datetime.fromisoformat(payload["projection_at"]),
             "comparison_native_fact_or_generation_mismatch")
    return result
