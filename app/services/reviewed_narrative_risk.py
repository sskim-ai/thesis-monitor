"""Opt-in historical narrative risk ownership, separate from R17 BUY support.

Constructors are trusted backend composition, never native request parameters.
Pins must come from the immutable source/review store, not caller-rehashed JSON.
The source owner authenticates transport and filing identity only. An independent
semantic decision is still required; neither source hashes nor scale facts grant
economic meaning. Same-process hostile Python is outside this capability boundary.
"""

from __future__ import annotations

from datetime import date, datetime
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import secrets
from threading import RLock
from typing import Literal

from pydantic import Field, model_validator

from app.services.economic_claim_qualification import BackendQualifiedEconomicPolicy
from app.services.native_input_admission import Closed, Identity, SHA
from app.services.reported_fact_owner import (
    BackendReportedFactOwner,
    RegisteredIssuerBinding,
    ReportedFact,
)
from app.services.unified_snapshot_contract import digest

CONTRACT = "real-narrative-risk-property-owner-v1"
SOURCE_CONTRACT = "backend-sealed-narrative-source-owner-v1"
RULE = "reviewed-disclosed-business-risk-v1"
SOURCE_KEYS = frozenset(
    {"html", "html_receipt", "html_request", "discovery", "discovery_receipt", "registration"}
)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _governing_policy_sha256():
    from app.services import directional_balance_service

    return _sha(Path(directional_balance_service.__file__).read_bytes())


class _DEIParser(HTMLParser):
    """Read identity facts, without treating stripped HTML as span authority."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.values = {}
        self.active = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "ix:exclude" and self.active is not None:
            raise ValueError("NARRATIVE_DEI_EXCLUDED_TEXT_NOT_SUPPORTED")
        if tag == "ix:nonnumeric" and attrs.get("name", "").lower() in {
            "dei:entitycentralindexkey",
            "dei:documentperiodenddate",
        }:
            if self.active is not None or attrs.get("continuedat") or not attrs.get("contextref"):
                raise ValueError("NARRATIVE_DEI_CONTINUATION_OR_CONTEXT_GAP")
            self.active = (attrs, [])

    def handle_data(self, data):
        if self.active is not None:
            self.active[1].append(data)

    def handle_endtag(self, tag):
        if tag == "ix:nonnumeric" and self.active is not None:
            attrs, parts = self.active
            row = (" ".join("".join(parts).split()), attrs["contextref"], attrs.get("format"))
            self.values.setdefault(attrs["name"].lower(), set()).add(row)
            self.active = None

    def identity(self, raw):
        self.feed(raw.decode("utf-8-sig"))
        self.close()
        if self.active is not None or any(
            len(self.values.get(k, ())) != 1
            for k in ("dei:entitycentralindexkey", "dei:documentperiodenddate")
        ):
            raise ValueError("NARRATIVE_DEI_IDENTITY_MISSING_OR_CONFLICTING")
        cik, context, cik_format = next(iter(self.values["dei:entitycentralindexkey"]))
        period, period_context, period_format = next(iter(self.values["dei:documentperiodenddate"]))
        if context != period_context or cik_format or not re.fullmatch(r"[0-9]{1,10}", cik):
            raise ValueError("NARRATIVE_DEI_ISSUER_CONTEXT_MISMATCH")
        if period_format is None:
            parsed_period = date.fromisoformat(period)
        elif period_format == "ixt:date-monthname-day-year-en":
            parsed_period = datetime.strptime(period, "%B %d, %Y").date()
        else:
            raise ValueError("NARRATIVE_DEI_DATE_TRANSFORM_NOT_SUPPORTED")
        return str(int(cik)), parsed_period


class _SpanTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


class NarrativeSourceAdmission(Closed):
    contract: Literal["backend-sealed-narrative-source-owner-v1"] = SOURCE_CONTRACT
    admission_id: Identity
    source_kind: Literal["REAL_SEALED_SOURCE", "SYNTHETIC_REVIEW_FIXTURE"]
    registration: RegisteredIssuerBinding
    source_artifact_sha256: SHA
    source_receipt_artifact_sha256: SHA
    source_request_artifact_sha256: SHA
    discovery_source_sha256: SHA
    discovery_receipt_artifact_sha256: SHA
    filing_accession: Identity
    filing_form: Literal["10-Q", "10-K", "20-F", "6-K"]
    filed: date
    statement_date: date
    cutoff: date
    primary_document: Identity
    filing_url: Identity
    logical_request_id: Identity
    facts: tuple[ReportedFact, ...] = Field(min_length=4, max_length=4)
    source_owner_sha256: SHA
    supporting_fact_admission_sha256: tuple[SHA, ...] = Field(min_length=4, max_length=4)
    authority: Literal["AUTHENTICATED_HISTORICAL_HTML_NOT_ECONOMIC_QUALIFICATION"] = (
        "AUTHENTICATED_HISTORICAL_HTML_NOT_ECONOMIC_QUALIFICATION"
    )
    source_binding_sha256: SHA
    admission_sha256: SHA


class BackendNarrativeSourceOwner:
    """New source admission over original transport and original live fact owner.

    Artifact keys are html, html_receipt (original final.json), html_request
    (original resolved-request.json), discovery, discovery_receipt, registration.
    All values and their independent store pins are exact bytes, not projections.
    """

    def __init__(
        self, *, fact_owner, artifacts, trusted_artifact_sha256, source_kind, filing_accession
    ):
        if type(fact_owner) is not BackendReportedFactOwner:
            raise ValueError("LIVE_REPORTED_FACT_OWNER_REQUIRED")
        if set(artifacts) != SOURCE_KEYS or set(trusted_artifact_sha256) != SOURCE_KEYS:
            raise ValueError("EXACT_NARRATIVE_SOURCE_ANCHORS_REQUIRED")
        for key in SOURCE_KEYS:
            if (
                type(artifacts[key]) is not bytes
                or _sha(artifacts[key]) != trusted_artifact_sha256[key]
            ):
                raise ValueError("INDEPENDENT_NARRATIVE_SOURCE_ANCHOR_MISMATCH")
        parsed = {k: json.loads(v) for k, v in artifacts.items() if k != "html"}
        r = fact_owner.registration
        facts = fact_owner.facts
        if (
            len(facts) != 4
            or len({f.source_row_identity for f in facts}) != 4
            or any(
                sum(f.field == field for f in facts) != 2
                for field in ("revenue", "operating_income")
            )
        ):
            raise ValueError("NARRATIVE_ORIGINAL_FOUR_SCALE_FACTS_REQUIRED")
        if trusted_artifact_sha256["registration"] != r.registration_artifact_sha256 or any(
            f.discovery_source_sha256 != trusted_artifact_sha256["discovery"] for f in facts
        ):
            raise ValueError("NARRATIVE_ORIGINAL_REGISTRATION_OR_DISCOVERY_MISMATCH")
        records = parsed["registration"]["roles"]["security_identity"]["records"]
        rows = [
            x["record"]
            for x in records
            if x["record"].get("canonical_security_id") == r.security_id
        ]
        if len(rows) != 1:
            raise ValueError("NARRATIVE_REGISTERED_SECURITY_MISSING_OR_CONFLICTING")
        reg = rows[0]
        if (
            reg["ticker"],
            str(int(reg["cik"])),
            reg["security_type"],
            reg["country"].upper(),
            reg["exchange"].upper(),
        ) != (
            r.ticker,
            str(int(r.issuer_id)),
            r.security_type,
            r.market.upper(),
            r.exchange.upper(),
        ):
            raise ValueError("NARRATIVE_REGISTERED_ISSUER_BASIS_MISMATCH")
        discovery = parsed["discovery"]
        if str(int(discovery["cik"])) != str(int(r.issuer_id)) or (
            r.ticker,
            r.exchange.upper(),
        ) not in {
            (t, e.upper())
            for t, e in zip(discovery["tickers"], discovery["exchanges"], strict=True)
        }:
            raise ValueError("NARRATIVE_DISCOVERY_ISSUER_MISMATCH")
        recent = discovery["filings"]["recent"]
        names = ("accessionNumber", "form", "filingDate", "reportDate", "primaryDocument")
        if (
            any(not isinstance(recent.get(k), list) for k in names)
            or len({len(recent[k]) for k in names}) != 1
        ):
            raise ValueError("NARRATIVE_DISCOVERY_COLUMNS_MISSING_OR_CONFLICTING")
        indices = [
            i for i, value in enumerate(recent["accessionNumber"]) if value == filing_accession
        ]
        if len(indices) != 1:
            raise ValueError("NARRATIVE_DISCOVERY_ACCESSION_MISSING_OR_CONFLICTING")
        filing = {k: recent[k][indices[0]] for k in names}
        primary = filing["primaryDocument"]
        if not re.fullmatch(r"[0-9]{10}-[0-9]{2}-[0-9]{6}", filing_accession) or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9_.-]*\.(?:htm|html)", primary
        ):
            raise ValueError("NARRATIVE_FILING_PATH_NOT_APPLICABLE")
        url = f"https://www.sec.gov/Archives/edgar/data/{int(r.issuer_id)}/{filing_accession.replace('-', '')}/{primary}"
        filed, period = (
            date.fromisoformat(filing["filingDate"]),
            date.fromisoformat(filing["reportDate"]),
        )
        if not period <= filed <= r.cutoff or not any(
            (f.filing_accession, f.filing_form, f.filed, f.period_end)
            == (filing_accession, filing["form"], filed, period)
            for f in facts
        ):
            raise ValueError("NARRATIVE_FILING_PERIOD_OR_ORIGINAL_FACT_BINDING_MISMATCH")
        receipt, discovery_receipt, resolved = (
            parsed[k] for k in ("html_receipt", "discovery_receipt", "html_request")
        )
        discovery_id = f"financial:{r.ticker}:discovery"
        logical_id = receipt.get("logical_request_id", "")
        if not re.fullmatch(
            re.escape(f"financial:{r.ticker}:filing") + r"[1-9][0-9]*:primary", logical_id
        ):
            raise ValueError("NARRATIVE_PRIMARY_TRANSPORT_REQUIRED")
        for rec, raw_key, key in (
            (receipt, "html", logical_id),
            (discovery_receipt, "discovery", discovery_id),
        ):
            if (
                rec.get("status"),
                rec.get("raw_sha256"),
                rec.get("generation_id"),
                rec.get("logical_request_id"),
                rec.get("role"),
            ) != (
                "PASS",
                trusted_artifact_sha256[raw_key],
                r.source_generation_id,
                key,
                f"financial:{r.ticker}",
            ):
                raise ValueError("NARRATIVE_TRANSPORT_SOURCE_GENERATION_MISMATCH")
            if rec.get("receipt_sha256") != digest(
                {k: v for k, v in rec.items() if k != "receipt_sha256"}
            ):
                raise ValueError("NARRATIVE_TRANSPORT_RECEIPT_INTEGRITY_MISMATCH")
        if receipt.get("parent_receipts") != {discovery_id: discovery_receipt["receipt_sha256"]}:
            raise ValueError("NARRATIVE_DISCOVERY_PARENT_RECEIPT_MISMATCH")
        for key in (
            "generation_id",
            "logical_request_id",
            "role",
            "parent_receipts",
            "descriptor_sha256",
            "plan_sha256",
            "request_sha256",
            "resolved_request_sha256",
        ):
            if key not in receipt or resolved.get(key) != receipt[key]:
                raise ValueError("NARRATIVE_RESOLVED_TRANSPORT_BINDING_MISMATCH")
        request = resolved["request"]
        if (
            digest(request) != receipt["resolved_request_sha256"]
            or (request.get("method"), request.get("url"), request.get("body")) != ("GET", url, "")
            or any(resolved.get("selected", {}).get(k) != v for k, v in filing.items())
        ):
            raise ValueError("NARRATIVE_DISCOVERY_URL_OR_SELECTED_FILING_MISMATCH")
        if _DEIParser().identity(artifacts["html"]) != (str(int(r.issuer_id)), period):
            raise ValueError("NARRATIVE_HTML_DEI_ISSUER_OR_PERIOD_MISMATCH")
        admissions = tuple(fact_owner.admit(f) for f in facts)
        if len({a.owner_evidence_sha256 for a in admissions}) != 1:
            raise ValueError("NARRATIVE_ORIGINAL_FACT_OWNER_MISMATCH")
        body = dict(
            admission_id=secrets.token_hex(24),
            source_kind=source_kind,
            registration=r,
            source_artifact_sha256=trusted_artifact_sha256["html"],
            source_receipt_artifact_sha256=trusted_artifact_sha256["html_receipt"],
            source_request_artifact_sha256=trusted_artifact_sha256["html_request"],
            discovery_source_sha256=trusted_artifact_sha256["discovery"],
            discovery_receipt_artifact_sha256=trusted_artifact_sha256["discovery_receipt"],
            filing_accession=filing_accession,
            filing_form=filing["form"],
            filed=filed,
            statement_date=period,
            cutoff=r.cutoff,
            primary_document=primary,
            filing_url=url,
            logical_request_id=logical_id,
            facts=facts,
            source_owner_sha256=admissions[0].owner_evidence_sha256,
            supporting_fact_admission_sha256=tuple(a.admission_sha256 for a in admissions),
        )
        admission = NarrativeSourceAdmission(
            **body, source_binding_sha256="0" * 64, admission_sha256="0" * 64
        )
        # Stable review commitment is not bearer authority. Random live receipts
        # still bind admission_sha256 and exact owner-local resolution below.
        admission = admission.model_copy(
            update={
                "source_binding_sha256": digest(
                    admission.model_dump(
                        mode="json",
                        exclude={
                            "admission_id",
                            "supporting_fact_admission_sha256",
                            "source_binding_sha256",
                            "admission_sha256",
                        },
                    )
                )
            }
        )
        admission = admission.model_copy(
            update={
                "admission_sha256": digest(
                    admission.model_dump(mode="json", exclude={"admission_sha256"})
                )
            }
        )
        self._owner, self._admissions = fact_owner, admissions
        self._raw = artifacts["html"]
        self._json, self._revoked, self._lock = admission.model_dump_json(), False, RLock()

    @property
    def admission(self):
        return NarrativeSourceAdmission.model_validate_json(self._json)

    def resolve(self, admission):
        with self._lock:
            if (
                self._revoked
                or type(admission) is not NarrativeSourceAdmission
                or admission.model_dump_json() != self._json
            ):
                raise ValueError("UNISSUED_CHANGED_OR_REVOKED_NARRATIVE_SOURCE")
            r = admission.registration
            if self._owner.registration != r:
                raise ValueError("NARRATIVE_ORIGINAL_REGISTRATION_CHANGED")
            for a in self._admissions:
                self._owner.resolve(
                    a,
                    axis="DISPLAY",
                    security_id=r.security_id,
                    execution_generation_id=r.execution_generation_id,
                    source_generation_id=r.source_generation_id,
                )
            return admission

    def verify_span(self, span):
        self.resolve(self.admission)
        span = NarrativeSpan.model_validate(span.model_dump(mode="json"))
        if (
            span.end_byte > len(self._raw)
            or _sha(self._raw[span.start_byte : span.end_byte]) != span.raw_sha256
        ):
            raise ValueError("NARRATIVE_EXACT_RAW_BYTE_SPAN_MISMATCH")
        return span

    def excerpt(self, span):
        """Historical raw-source quotation data, not new current assertions."""
        span = self.verify_span(span)
        parser = _SpanTextParser()
        parser.feed(self._raw[span.start_byte : span.end_byte].decode("utf-8"))
        parser.close()
        text = " ".join(" ".join(parser.parts).split())
        if not text or len(text) > 5000:
            raise ValueError("NARRATIVE_EXCERPT_EMPTY_OR_EXCEEDS_5000")
        return span.model_dump(mode="json") | {"text": text}

    def revoke(self, admission):
        with self._lock:
            self.resolve(admission)
            self._revoked = True


class NarrativeSpan(Closed):
    category: Literal["RISK", "MECHANISM", "MITIGATION"]
    start_byte: int = Field(ge=0, strict=True)
    end_byte: int = Field(gt=0, strict=True)
    raw_sha256: SHA

    @model_validator(mode="after")
    def nonempty(self):
        if self.end_byte <= self.start_byte:
            raise ValueError("NARRATIVE_EMPTY_OR_REVERSED_SPAN")
        return self


def _render_review(decision):
    return (
        f"Historical filing {decision.filed} (period {decision.statement_date}): {decision.risk_summary}. "
        f"If {decision.condition_summary}, {decision.mechanism_summary}. "
        f"Mitigation (historical timing/coverage limits apply): {decision.mitigation_summary}. "
        "LOW/LIMITED; conditional disclosure only. Realization, cause, recurrence, independence, "
        "current truth, forecast and stance not established."
    )


class NarrativeRiskReviewDecision(Closed):
    contract: Literal["independent-narrative-risk-review-v1"] = (
        "independent-narrative-risk-review-v1"
    )
    review_event_id: Identity
    reviewer: Identity
    mandate: Literal["R18_USER_AUTHORIZED_EXISTING_POLICY_QUALIFICATION"]
    rule_version: Literal["reviewed-disclosed-business-risk-v1"] = RULE
    decision: Literal["APPROVE_BOUNDED_EXISTING_POLICY_QUALIFICATION"]
    proposal_sha256: SHA
    independent_review_sha256: SHA
    inherited_policy_sha256: SHA
    source_kind: Literal["REAL_SEALED_SOURCE", "SYNTHETIC_REVIEW_FIXTURE"]
    source_binding_sha256: SHA
    source_artifact_sha256: SHA
    source_generation_id: Identity
    owner_execution_generation_id: Identity
    security_id: Identity
    issuer_id: Identity
    facts: tuple[ReportedFact, ...] = Field(min_length=4, max_length=4)
    filed: date
    statement_date: date
    cutoff: date
    spans: tuple[NarrativeSpan, ...] = Field(min_length=3, max_length=12)
    property_type: Literal["BUSINESS_RISK"] = "BUSINESS_RISK"
    economic_meaning: Literal["HISTORICAL_CONDITIONAL_DISCLOSED_BUSINESS_RISK"] = (
        "HISTORICAL_CONDITIONAL_DISCLOSED_BUSINESS_RISK"
    )
    materiality_basis: Literal["INDEPENDENT_CASE_REVIEW_OF_DISCLOSED_RISK_AND_ENTITY_SCALE"]
    counterevidence_scope: Literal["EXACT_DISCLOSED_MITIGANTS_AND_ORIGINAL_SCALE_FACTS"]
    risk_summary: str = Field(min_length=1, max_length=140)
    condition_summary: str = Field(min_length=1, max_length=140)
    mechanism_summary: str = Field(min_length=1, max_length=140)
    mitigation_summary: str = Field(min_length=1, max_length=140)
    permitted_role: Literal["SELL_DRIVER"] = "SELL_DRIVER"
    interpretation_type: Literal["BUSINESS_CAUTION"] = "BUSINESS_CAUTION"
    polarity: Literal["NEGATIVE"] = "NEGATIVE"
    consumer: Literal["CORE"] = "CORE"
    use_axis: Literal["CORE_DIRECTION"] = "CORE_DIRECTION"
    allowed_confidences: tuple[Literal["LOW"], ...] = ("LOW",)
    uncertainty: Literal["LIMITED"] = "LIMITED"
    asserts_realization: Literal[False] = False
    asserts_causality: Literal[False] = False
    asserts_recurrence: Literal[False] = False
    asserts_independence: Literal[False] = False
    asserts_currentness: Literal[False] = False
    asserts_forecast: Literal[False] = False
    asserts_stance: Literal[False] = False
    active_material_risk_override: Literal[False] = False
    numeric_fact_use: Literal["BACKGROUND_SCALE_NOT_INDEPENDENT_RISK_PROOF"] = (
        "BACKGROUND_SCALE_NOT_INDEPENDENT_RISK_PROOF"
    )

    @model_validator(mode="after")
    def bounded_review(self):
        if (
            self.allowed_confidences != ("LOW",)
            or {s.category for s in self.spans} != {"RISK", "MECHANISM", "MITIGATION"}
            or len({(s.start_byte, s.end_byte) for s in self.spans}) != len(self.spans)
        ):
            raise ValueError("NARRATIVE_REVIEW_CATEGORIES_OR_LIMITS_REQUIRED")
        if not self.statement_date <= self.filed <= self.cutoff:
            raise ValueError("NARRATIVE_REVIEW_TEMPORAL_BINDING_MISMATCH")
        for value in (
            self.risk_summary,
            self.condition_summary,
            self.mechanism_summary,
            self.mitigation_summary,
        ):
            if value != " ".join(value.split()):
                raise ValueError("NARRATIVE_REVIEW_SINGLE_LINE_MEANING_REQUIRED")
        if len(_render_review(self)) > 420:
            raise ValueError("NARRATIVE_REVIEW_RENDERING_EXCEEDS_420")
        return self


class ReviewedNarrativeRiskAdmission(Closed):
    contract: Literal["real-narrative-risk-property-owner-v1"] = CONTRACT
    admission_id: Identity
    review: NarrativeRiskReviewDecision
    review_artifact_sha256: SHA
    narrative_source: NarrativeSourceAdmission
    source_owner_sha256: SHA
    supporting_fact_admission_sha256: tuple[SHA, ...]
    execution_generation_id: Identity
    lineage: Literal["NEW_NARRATIVE_REVIEW_REFERENCES_UNCHANGED_HISTORICAL_FACT_OWNER"] = (
        "NEW_NARRATIVE_REVIEW_REFERENCES_UNCHANGED_HISTORICAL_FACT_OWNER"
    )
    admission_sha256: SHA


class BackendReviewedNarrativeRiskOwner:
    """A pinned independent semantic decision, not a public approval endpoint."""

    def __init__(
        self,
        *,
        source_owner,
        decision_bytes,
        trusted_decision_sha256,
        review_bytes,
        trusted_review_sha256,
        proposal_bytes,
        execution_generation_id,
    ):
        if type(source_owner) is not BackendNarrativeSourceOwner:
            raise ValueError("LIVE_NARRATIVE_SOURCE_OWNER_REQUIRED")
        for raw, expected in (
            (decision_bytes, trusted_decision_sha256),
            (review_bytes, trusted_review_sha256),
        ):
            if type(raw) is not bytes or _sha(raw) != expected:
                raise ValueError("INDEPENDENT_NARRATIVE_REVIEW_ANCHOR_MISMATCH")
        d = NarrativeRiskReviewDecision.model_validate_json(decision_bytes)
        source = source_owner.resolve(source_owner.admission)
        r = source.registration
        if (
            type(proposal_bytes) is not bytes
            or d.proposal_sha256 != _sha(proposal_bytes)
            or d.independent_review_sha256 != trusted_review_sha256
            or d.inherited_policy_sha256 != _governing_policy_sha256()
        ):
            raise ValueError("NARRATIVE_REVIEW_PROPOSAL_OR_POLICY_BINDING_MISMATCH")
        if (
            d.source_binding_sha256,
            d.source_artifact_sha256,
            d.source_kind,
            d.security_id,
            d.issuer_id,
            d.source_generation_id,
            d.owner_execution_generation_id,
            d.statement_date,
            d.filed,
            d.cutoff,
        ) != (
            source.source_binding_sha256,
            source.source_artifact_sha256,
            source.source_kind,
            r.security_id,
            r.issuer_id,
            r.source_generation_id,
            r.execution_generation_id,
            source.statement_date,
            source.filed,
            source.cutoff,
        ):
            raise ValueError("NARRATIVE_REVIEW_SOURCE_IDENTITY_OR_TIME_MISMATCH")
        if len({f.model_dump_json() for f in d.facts}) != 4 or {
            f.model_dump_json() for f in d.facts
        } != {f.model_dump_json() for f in source.facts}:
            raise ValueError("NARRATIVE_REVIEW_EXACT_ORIGINAL_FACT_SET_REQUIRED")
        for span in d.spans:
            source_owner.excerpt(span)
        if execution_generation_id == r.execution_generation_id:
            raise ValueError("NARRATIVE_NEW_REVIEW_CONSUMER_GENERATION_REQUIRED")
        body = dict(
            admission_id=secrets.token_hex(24),
            review=d,
            review_artifact_sha256=trusted_decision_sha256,
            narrative_source=source,
            source_owner_sha256=source.source_owner_sha256,
            supporting_fact_admission_sha256=source.supporting_fact_admission_sha256,
            execution_generation_id=execution_generation_id,
        )
        admission = ReviewedNarrativeRiskAdmission(**body, admission_sha256="0" * 64)
        admission = admission.model_copy(
            update={
                "admission_sha256": digest(
                    admission.model_dump(mode="json", exclude={"admission_sha256"})
                )
            }
        )
        self._source_owner, self._owner = source_owner, source_owner._owner
        self._json, self._revoked, self._lock = admission.model_dump_json(), False, RLock()

    @property
    def admission(self):
        return ReviewedNarrativeRiskAdmission.model_validate_json(self._json)

    def resolve(self, admission):
        with self._lock:
            if (
                self._revoked
                or type(admission) is not ReviewedNarrativeRiskAdmission
                or admission.model_dump_json() != self._json
            ):
                raise ValueError("UNISSUED_CHANGED_OR_REVOKED_NARRATIVE_PROPERTY")
            if admission.review.inherited_policy_sha256 != _governing_policy_sha256():
                raise ValueError("NARRATIVE_GOVERNING_POLICY_CHANGED")
            self._source_owner.resolve(admission.narrative_source)
            return admission

    def revoke(self, admission):
        with self._lock:
            self.resolve(admission)
            self._revoked = True


def _project_bundle(admission):
    from app.services.native_input_admission import (
        BackendOwnerBundle,
        MetricAuthorityEnvelope,
        Permission,
        TemporalField,
        UseAxis,
    )

    d = admission.review
    reg = admission.narrative_source.registration
    owner_ref = CONTRACT + ":" + admission.admission_id
    metrics = []
    for f in d.facts:
        temporal = []
        for field in (
            "retrieval_timestamp",
            "metric_as_of",
            "denominator_period_start",
            "denominator_period_end",
            "source_statement_period",
            "price_session",
            "financial_period",
        ):
            known = field in {"source_statement_period", "financial_period"}
            temporal.append(
                TemporalField(
                    field=field,
                    value=f.period_end.isoformat() if known else None,
                    state="VERIFIED_OWNER_PERIOD"
                    if known
                    else "NOT_APPLICABLE"
                    if field
                    in {"denominator_period_start", "denominator_period_end", "price_session"}
                    else "UNKNOWN_NOT_PROVIDED",
                    owner_ref=owner_ref if known else None,
                    source_artifact_sha256=f.raw_source_sha256 if known else None,
                )
            )
        metrics.append(
            MetricAuthorityEnvelope(
                metric_ref="reported-fact:" + f.source_row_identity,
                metric_type=f.concept,
                value=f.value,
                unit=f.currency,
                security_id=d.security_id,
                security_type=reg.security_type,
                generation_id=admission.execution_generation_id,
                source_generation_id=d.source_generation_id,
                owner_contract=CONTRACT,
                owner_ref=owner_ref,
                owner_receipt_sha256=admission.admission_sha256,
                source_provider="SEC_COMPANYFACTS_SEALED",
                source_artifact_ref=f.raw_source_sha256,
                source_artifact_sha256=f.raw_source_sha256,
                currency=f.currency,
                share_basis=f.share_basis,
                authority_state="REVIEWED_NARRATIVE_RISK_BACKGROUND_SCALE_ONLY",
                permissions=tuple(
                    Permission(
                        axis=a,
                        state="ALLOWED"
                        if a in {UseAxis.CORE_VISIBILITY, UseAxis.CORE_DIRECTION}
                        else "UNSPECIFIED",
                        owner_evidence_ref=owner_ref + "#/" + a.value
                        if a in {UseAxis.CORE_VISIBILITY, UseAxis.CORE_DIRECTION}
                        else None,
                    )
                    for a in UseAxis
                ),
                temporal=tuple(temporal),
                input_sha256=f.occurrence_sha256,
                caveats=(
                    "ORIGINAL_NUMERIC_FACTS_ARE_BACKGROUND_SCALE_NOT_NARRATIVE_PROOF",
                    "HISTORICAL_CONDITIONAL_DISCLOSURE_WITH_REVIEWED_MITIGANTS",
                    "NO_REALIZATION_CAUSALITY_RECURRENCE_INDEPENDENCE_CURRENTNESS_FORECAST_OR_STANCE",
                    "NO_ACTIVE_MATERIAL_RISK_OVERRIDE",
                ),
            )
        )
    return BackendOwnerBundle(
        security_id=d.security_id,
        ticker=reg.ticker,
        market=reg.market.lower(),
        generation_id=admission.execution_generation_id,
        source_generation_id=d.source_generation_id,
        source_envelope_sha256=digest(
            dict(
                narrative_source=admission.narrative_source.admission_sha256,
                raw=d.source_artifact_sha256,
                property=admission.admission_sha256,
            )
        ),
        metrics=tuple(metrics),
        issuer_context=None,
    )


def _support_rows(admission, registry):
    from app.services.native_economic_core import bound_reference

    refs = tuple(m.metric_ref for m in registry.bundle.metrics)
    owner_ref = CONTRACT + ":" + admission.admission_id
    return [
        dict(
            support_ref="reviewed-narrative:" + kind,
            property=kind,
            evidence_refs=refs,
            evidence_bindings=tuple(
                bound_reference(registry, r).model_dump(mode="json") for r in refs
            ),
            applies_to_supports=("reviewed-narrative:BUSINESS_RISK",)
            if kind == "COUNTEREVIDENCE"
            else (),
            independent_of_supports=(),
            property_owner_ref=owner_ref,
            economic_lineage=admission.review.source_artifact_sha256,
            polarity=polarity,
            state="AVAILABLE_SUPPORTING",
            temporal_rules=(
                dict(
                    field="metric_as_of",
                    allowed_states=("UNKNOWN_NOT_PROVIDED",),
                    maximum_age_days=None,
                ),
                dict(
                    field="financial_period",
                    allowed_states=("VERIFIED_OWNER_PERIOD",),
                    maximum_age_days=None,
                ),
            ),
            allowed_confidences=admission.review.allowed_confidences,
        )
        for kind, polarity in (("BUSINESS_RISK", "NEGATIVE"), ("COUNTEREVIDENCE", "MIXED"))
    ]


def _scale_ownership(bundle):
    from app.services.accepted_decision_v2_runtime_service import AcceptedV2EvidenceOwnership
    from app.services.expectation_valuation_interaction_service import (
        ExpectationValuationInteraction,
    )

    return AcceptedV2EvidenceOwnership(
        ticker=bundle.ticker,
        core_ref_ids=tuple(m.metric_ref for m in bundle.metrics),
        timing_ref_ids=(),
        expectation_valuation=ExpectationValuationInteraction(
            ticker=bundle.ticker,
            classification="UNKNOWN",
            expectation_refs=(),
            valuation_refs=(),
            independent_expectation_basis_refs=(),
            shared_underlying_refs=(),
            reason="NO_VALUATION_OR_EXPECTATION_AUTHORIZATION_IN_NARRATIVE_RISK_REVIEW",
        ),
    )


class BackendNarrativeRiskClaimPolicy(BackendQualifiedEconomicPolicy):
    """Uses the inherited claim engine, with one exact reviewed risk projection."""

    def __init__(self, *args, property_owner, **kwargs):
        if type(property_owner) is not BackendReviewedNarrativeRiskOwner:
            raise ValueError("LIVE_REVIEWED_NARRATIVE_PROPERTY_OWNER_REQUIRED")
        self.reported_property_owner = property_owner
        self._property = property_owner.resolve(property_owner.admission)
        super().__init__(*args, **kwargs)
        self._verify_property_projection(kwargs["registry"])

    def _verify_property_projection(self, registry):
        from app.services.economic_claim_qualification import EconomicSupport

        a = self.reported_property_owner.resolve(self._property)
        if registry.bundle != _project_bundle(a):
            raise ValueError("NARRATIVE_PROPERTY_EXACT_FACT_PROJECTION_REQUIRED")
        if self.bundle.ownership != _scale_ownership(registry.bundle):
            raise ValueError("NARRATIVE_PROPERTY_OWNERSHIP_SCOPE_BROADENED")
        expected_rows = _support_rows(a, registry)
        supports = self.bundle.supports
        if len(supports) != len(expected_rows) or any(
            s != EconomicSupport(**row, property_source_sha256=s.property_source_sha256)
            for s, row in zip(supports, expected_rows, strict=True)
        ):
            raise ValueError("NARRATIVE_PROPERTY_SUPPORT_SCOPE_BROADENED")
        if (self.bundle.policy_owner, self.bundle.approval_version, self.bundle.source_kind) != (
            CONTRACT + ":" + a.admission_id,
            RULE,
            "QUALIFIED_PROPERTY_OWNER"
            if a.review.source_kind == "REAL_SEALED_SOURCE"
            else "SYNTHETIC_TEST_PROPERTIES",
        ):
            raise ValueError("NARRATIVE_PROPERTY_REVIEW_OR_PROVENANCE_SUBSTITUTION")

    def verify_backend(self, registry):
        self._verify_property_projection(registry)
        return super().verify_backend(registry)

    def narrative_packet_binding(self):
        """Every admitted excerpt is historical source data, not current truth."""
        a = self.reported_property_owner.resolve(self._property)
        return dict(
            narrative_admission_sha256=a.admission_sha256,
            narrative_source_sha256=a.review.source_artifact_sha256,
            narrative_span_sha256=tuple(s.raw_sha256 for s in a.review.spans),
            narrative_context=tuple(
                self.reported_property_owner._source_owner.excerpt(s) for s in a.review.spans
            ),
        )

    def qualify(self, proposal, *, request, invocation):
        from app.services.economic_claim_qualification import EconomicClaimProposal
        from app.services.cross_market_decision_engine_service import EvidenceClaim

        a = self.reported_property_owner.resolve(self._property)
        proposal = EconomicClaimProposal.model_validate(proposal.model_dump(mode="json"))
        if (
            proposal.requested_role,
            proposal.interpretation_type,
            proposal.polarity,
            proposal.uncertainty,
            proposal.consumer,
            proposal.use_axis,
            proposal.asserts_causality,
            proposal.asserts_recurrence,
            proposal.asserts_independent_corroboration,
            proposal.numeric_assertions,
        ) != (
            "SELL_DRIVER",
            "BUSINESS_CAUTION",
            "NEGATIVE",
            "LIMITED",
            "CORE",
            "CORE_DIRECTION",
            False,
            False,
            False,
            (),
        ):
            raise ValueError("CLAIM_OUTSIDE_REVIEWED_NARRATIVE_RISK_SCOPE")
        if proposal.support_refs != tuple(s.support_ref for s in self.bundle.supports):
            raise ValueError("NARRATIVE_REQUIRED_RISK_OR_MITIGANT_OMITTED")
        if request.invocation.assessment_as_of < max(
            a.review.cutoff, *(f.filed for f in a.review.facts)
        ):
            raise ValueError("NARRATIVE_REVIEW_NOT_AVAILABLE_AT_ASSESSMENT")
        claim, receipt, supports = super().qualify(proposal, request=request, invocation=invocation)
        return (
            EvidenceClaim(text=_render_review(a.review), evidence_refs=claim.evidence_refs),
            receipt,
            supports,
        )


def build_reported_narrative_risk_invocation(property_owner, *, invocation_id, assessment_as_of):
    """Backend-only factory; requires the generalized native fact-v2 role route."""
    from app.services.native_input_admission import BackendAdmissionRegistry, UseAxis
    from app.services.native_economic_core import InvocationSpec
    from app.services.native_authority_core import build_context
    from app.services.economic_claim_qualification import (
        ClaimPolicyBundle,
        EconomicSupport,
        policy_sha256,
    )
    from app.services.accepted_decision_v2_runtime_service import (
        build_accepted_v2_economic_core_invocation,
    )
    from app.services.reported_economic_claim_consumer import _build_role_request

    if type(property_owner) is not BackendReviewedNarrativeRiskOwner:
        raise ValueError("LIVE_REVIEWED_NARRATIVE_PROPERTY_OWNER_REQUIRED")
    a = property_owner.resolve(property_owner.admission)
    if date.fromisoformat(str(assessment_as_of)) < max(
        a.review.cutoff, *(f.filed for f in a.review.facts)
    ):
        raise ValueError("NARRATIVE_REVIEW_NOT_AVAILABLE_AT_ASSESSMENT")
    bundle = _project_bundle(a)
    bundle_sha = digest(bundle.model_dump(mode="json"))
    registry = BackendAdmissionRegistry(bundle, expected_bundle_sha256=bundle_sha)
    refs = tuple(m.metric_ref for m in bundle.metrics)
    owner_ref = CONTRACT + ":" + a.admission_id
    rows = _support_rows(a, registry)
    body = json.dumps(
        dict(
            security_id=bundle.security_id,
            generation_id=bundle.generation_id,
            source_generation_id=bundle.source_generation_id,
            owner_ref=owner_ref,
            properties=rows,
            backend_bundle_sha256=bundle_sha,
            source_envelope_sha256=bundle.source_envelope_sha256,
        )
    ).encode()
    source_sha = _sha(body)
    policy_bundle = ClaimPolicyBundle(
        security_id=bundle.security_id,
        generation_id=bundle.generation_id,
        source_generation_id=bundle.source_generation_id,
        backend_bundle_sha256=bundle_sha,
        policy_owner=owner_ref,
        approval_version=RULE,
        ownership=_scale_ownership(bundle),
        supports=tuple(EconomicSupport(**row, property_source_sha256=source_sha) for row in rows),
        rule_sha256=policy_sha256(),
        source_kind="QUALIFIED_PROPERTY_OWNER"
        if a.review.source_kind == "REAL_SEALED_SOURCE"
        else "SYNTHETIC_TEST_PROPERTIES",
    )
    policy = BackendNarrativeRiskClaimPolicy(
        policy_bundle,
        property_owner=property_owner,
        expected_policy_sha256=digest(policy_bundle.model_dump(mode="json")),
        registry=registry,
        property_sources={"reviewed-narrative": body},
        trusted_source_sha256={"reviewed-narrative": source_sha},
    )
    context = build_context(
        admission_input=dict(
            security_id=bundle.security_id,
            generation_id=bundle.generation_id,
            source_generation_id=bundle.source_generation_id,
            metric_refs=refs,
            issuer_context=None,
        ),
        registry=registry,
        request_id=invocation_id,
    )
    axes = (UseAxis.CORE_VISIBILITY, UseAxis.CORE_DIRECTION)
    spec = InvocationSpec(
        invocation_id=invocation_id,
        security_id=bundle.security_id,
        generation_id=bundle.generation_id,
        source_generation_id=bundle.source_generation_id,
        assessment_as_of=assessment_as_of,
        intended_consumer="CORE",
        allowed_use_axes=axes,
        forbidden_use_axes=tuple(axis for axis in UseAxis if axis not in axes),
    )
    inv = build_accepted_v2_economic_core_invocation(
        context=context,
        admission_registry=registry,
        invocation_spec=spec,
        economic_policy=policy,
        authority_native_v2=True,
    )
    role_request = _build_role_request(inv)
    if (
        role_request.required_role != "SELL_DRIVER"
        or role_request.property_admission_sha256 != a.admission_sha256
    ):
        raise ValueError("NARRATIVE_NATIVE_ROLE_REQUEST_BINDING_MISMATCH")
    inv._reported_role_request_json = role_request.model_dump_json()
    return inv
