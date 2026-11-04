"""Canonical source visibility, separate from independently owned properties.

Source preparation and D02 are necessary, not economic interpretation authority.
This module neither creates review decisions nor issues manual/model permission.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
import os
from threading import RLock
from typing import Literal
from weakref import WeakKeyDictionary

from app.services.canonical_native_source_owner import CanonicalPreparedSourceOwner
from app.services.direction_timing_ownership_service import verified_owned_packet_view
from app.services.native_authority_core import build_context, build_native_core_request
from app.services.native_input_admission import (
    BackendAdmissionRegistry, BackendOwnerBundle, Closed, Identity,
    MetricAuthorityEnvelope, NativeAdmissionInput, Permission, SHA, TemporalField,
    UseAxis, UseState,
)
from app.services.reported_business_projection import projection_for_fact
from app.services.reviewed_economic_property import (
    BackendReviewedPropertyOwner,
    build_reported_property_invocation,
)
from app.services.unified_snapshot_contract import digest
from scripts import r2b_r2_contract as canonical
from scripts.m12da_source_use_contract import (
    SourceUse,
    is_use_allowed,
    validate_source_use_current_input,
)

_ADMISSIONS = WeakKeyDictionary()
_LOCK = RLock()
SOURCE_INPUT_CONTRACT = "canonical-comparison-native-visibility-v1"
SOURCE_INPUT_GAPS = (
    "NATIVE_REPORTED_FACT_PROMPT_ROUTE_NOT_AVAILABLE_FOR_VISIBILITY_ONLY",
    "INDEPENDENT_ECONOMIC_PROPERTY_OWNER_REQUIRED_FOR_CORE_DIRECTION",
)


def _require(condition, reason):
    if not condition:
        raise ValueError("canonical_native_" + reason)


class CanonicalNativeGap(Closed):
    contract: Literal["canonical-native-admission-gap-v1"] = "canonical-native-admission-gap-v1"
    ticker: Identity
    market: Literal["us", "kr"]
    generation_id: Identity
    source_generation_id: Identity
    source_relationship_sha256: SHA
    reasons: tuple[str, ...]
    canonical_evidence_refs: tuple[str, ...]
    native_admission_issued: Literal[False] = False
    model_dispatch_allowed: Literal[False] = False


def _gap(subject, ticker, reasons, comparisons):
    return CanonicalNativeGap(
        ticker=ticker, market=subject["market"], generation_id=subject["generation_id"],
        source_generation_id=subject["source_generation_id"],
        source_relationship_sha256=subject["source_relationship_sha256"],
        reasons=tuple(reasons), canonical_evidence_refs=tuple(sorted(comparisons)),
    )


def _subject_evidence(subject, ticker):
    """Validate original subject contracts; this diagnostic cannot issue a handle."""
    stock, prepared = subject["stock"], subject["prepared"]
    original = verified_owned_packet_view(stock)
    owned = verified_owned_packet_view(prepared["view"])
    chain, core = prepared["initial_chain"], prepared["core_input"]
    authority = subject["source_authority"]
    _require(
        stock["ticker"] == core["ticker"] == ticker
        and stock["market"] == original.source_packet.market == subject["market"]
        and stock["fresh_run_id"] == chain["source_generation_id"] == subject["source_generation_id"]
        and chain["execution_generation_id"] == subject["generation_id"]
        and stock["packet"]["generated_at"] == subject["cutoff"]
        and stock["status"] == "PASS" and not stock["mandatory_missing"]
        and prepared["mode"] == core["decision_mode"] == "EVIDENCE_BASED",
        "subject_identity_or_readiness_mismatch",
    )
    cutoff = datetime.fromisoformat(subject["cutoff"])
    _require(cutoff.tzinfo is not None and cutoff.utcoffset() is not None,
             "owned_cutoff_timezone_required")
    receipt = prepared["view_receipt"]
    _require(
        authority == prepared["source_authority"]
        and receipt["raw_source_sha256"] == digest(stock)
        and receipt["raw_authority_sha256"] == digest(authority)
        and chain["authority"]["parent_authority_sha256"] == digest(authority["authority"])
        and core["authority"] == chain["authority"],
        "original_authority_binding_mismatch",
    )
    metadata = prepared["subject"]["decision_evidence"]
    validation = validate_source_use_current_input(
        chain["projection"], chain["binding"], chain["expectation"],
        ticker=ticker, source_generation_id=subject["source_generation_id"],
        execution_generation_id=subject["generation_id"],
        catalog=prepared["catalog"], source_metadata=metadata,
    )
    _require(validation["status"] == "PASS", "current_d01_d02_required")
    expected_metadata = [row for row in metadata if row["ref_id"] in owned.core_refs]
    fields = canonical.policy.frozen_fact_fields(stock["packet"], ticker, expected_metadata)
    _require(core["metadata"] == expected_metadata and core["frozen_fact_fields"] == fields
             and core["observed_propositions"] == canonical.policy.observations(
                 expected_metadata, chain["authority"], fields), "canonical_core_input_mismatch")
    raw_stocks = [s for s in stock["packet"]["stocks"] if s["ticker"] == ticker]
    _require(len(raw_stocks) == 1, "exact_source_stock_required")
    raw_stock = raw_stocks[0]
    facts = {"canonical:" + f["fact_id"]: f for f in raw_stock["fact_catalog"]}
    selected = stock["selected_financial_owner"]
    comparisons, excluded = {}, []
    for ref in owned.source_packet.evidence:
        if ref.reported_business is None:
            continue
        fact = facts[ref.ref_id]
        projection = projection_for_fact(
            raw_stock, fact, ticker=ticker, packet_id=stock["packet"]["packet_id"],
            assessment_date=stock["packet"]["assessment_date"], market=subject["market"],
        )
        _require(projection is not None and projection == ref.reported_business,
                 "original_property_projection_required")
        if projection.kind != "COMPARISON":
            excluded.append("ISSUER_OR_QUALITY_CONTEXT_NOT_ECONOMIC_PROPERTY")
            continue
        _require(
            projection.source_generation == subject["source_generation_id"]
            and projection.selected_owner_sha256 == selected["envelope_sha256"]
            and projection.acquisition_sha256 == selected["selected_acquisition_sha256"]
            and projection.projection_sha256 == selected["selected_projection_sha256"]
            and fact["fact_id"] in selected["selected_fact_ids"]
            and projection.source_window_sha256 == digest(stock["packet"]["source_time_domains"]["business_window"]),
            "selected_property_source_binding_mismatch",
        )
        required_uses = (SourceUse.CONTEXT, SourceUse.BUSINESS_CONTEXT, SourceUse.OVERALL_DIRECTION)
        if ref.ref_id not in owned.core_refs or ref.ref_id not in {
            row["ref_id"] for row in core["metadata"]
        } or not all(
            use.value in projection.allowed_uses and is_use_allowed(
                chain["projection"], ref_id=ref.ref_id, use=use, binding=chain["binding"])
            for use in required_uses
        ):
            excluded.append("CANONICAL_PROPERTY_ECONOMIC_D02_NOT_GRANTED")
            continue
        comparisons[ref.ref_id] = (fact, projection)
    return comparisons, tuple(sorted(set(excluded)))


def _source_input_bundle(subject, ticker, comparisons):
    """Map authenticated comparative facts, not caller amounts or use flags.

    The artifact is the original canonical comparison (including its occurrence
    receipts), not a claimed new raw capture. Its statement dates are not price,
    retrieval or valuation-denominator dates.
    """
    _require(bool(comparisons), "economic_comparison_source_inputs_required")
    metrics, occurrences = [], []
    security_ids = {projection.security_id for _, projection in comparisons.values()}
    _require(len(security_ids) == 1, "comparison_security_scope_mismatch")
    selected = subject["stock"]["selected_financial_owner"]
    source_kinds = {"direct_sec": ("CIK:", "sec_edgar"), "direct_opendart": ("DART:", "opendart")}
    _require(selected["owner_type"] in source_kinds, "direct_comparison_owner_required")
    issuer_prefix, provider = source_kinds[selected["owner_type"]]
    for ref, (fact, projection) in sorted(comparisons.items()):
        fields = fact["fields"]
        _require(projection.kind == "COMPARISON" and projection.fact_sha256 == digest(fact)
                 and selected["issuer_identity"] == projection.issuer_id
                 and fields["issuer_id"] == issuer_prefix + projection.issuer_id,
                 "comparison_issuer_scope_mismatch")
        owner_ref = SOURCE_INPUT_CONTRACT + ":" + digest(dict(
            relationship=subject["source_relationship_sha256"], ref=ref))
        fact_sha = digest(fact)
        receipt = dict(contract=SOURCE_INPUT_CONTRACT, canonical_ref=ref,
            source_relationship_sha256=subject["source_relationship_sha256"],
            canonical_core_input_sha256=digest(subject["prepared"]["core_input"]),
            source_use_projection_sha256=digest(subject["prepared"]["initial_chain"]["projection"]),
            authenticated_comparison=projection.model_dump(mode="json"),
            granted_axes=[UseAxis.CORE_VISIBILITY.value])
        for role, value_field, start_field, end_field in (
            ("current", "current_value", "period_start", "period_end"),
            ("comparison", "prior_comparable_value", "prior_period_start", "prior_period_end"),
        ):
            lineage = fact["field_dependency_receipts"][role]["lineage"]
            start, end = (lineage[k] for k in ("amount_period_start", "amount_period_end"))
            _require(
                lineage["amount"] == fields[value_field]
                and type(lineage["amount"]) in (int, float)
                and (start, end) == (fields[start_field], fields[end_field])
                and date.fromisoformat(start) <= date.fromisoformat(end)
                <= datetime.fromisoformat(subject["cutoff"]).date()
                and lineage["currency"] == fields["currency"]
                and lineage["statement_basis"] == fields["statement_basis"]
                and lineage["source_row_identity"] in fields["source_occurrences"],
                "comparison_occurrence_binding_mismatch",
            )
            metric_ref = ref + ":" + role
            temporal = tuple(TemporalField(
                field=field,
                value=(start + "/" + end if field == "source_statement_period" else end)
                    if field in {"source_statement_period", "financial_period"} else None,
                state="VERIFIED_OWNER_PERIOD"
                    if field in {"source_statement_period", "financial_period"}
                    else "NOT_APPLICABLE" if field in {
                        "denominator_period_start", "denominator_period_end", "price_session"}
                    else "UNKNOWN_NOT_PROVIDED",
                owner_ref=owner_ref if field in {"source_statement_period", "financial_period"} else None,
                source_artifact_sha256=fact_sha
                    if field in {"source_statement_period", "financial_period"} else None,
            ) for field in (
                "retrieval_timestamp", "metric_as_of", "denominator_period_start",
                "denominator_period_end", "source_statement_period", "price_session", "financial_period",
            ))
            metrics.append(MetricAuthorityEnvelope(
                metric_ref=metric_ref, metric_type="reported_comparative_" + fields["metric"] + "_" + role,
                value=lineage["amount"], unit=fields["currency"], security_id=projection.security_id,
                security_type="UNKNOWN_NOT_PROVIDED", generation_id=subject["generation_id"],
                source_generation_id=subject["source_generation_id"], owner_contract=SOURCE_INPUT_CONTRACT,
                owner_ref=owner_ref, owner_receipt_sha256=digest(receipt),
                source_provider=provider,
                source_artifact_ref=ref, source_artifact_sha256=fact_sha,
                currency=fields["currency"], share_basis=None,
                authority_state="SOURCE_INPUT_VISIBILITY_NOT_ECONOMIC_ROLE",
                permissions=tuple(Permission(axis=axis,
                    state=UseState.ALLOWED if axis == UseAxis.CORE_VISIBILITY else UseState.UNSPECIFIED,
                    owner_evidence_ref=owner_ref + "#/" + axis.value
                        if axis == UseAxis.CORE_VISIBILITY else None) for axis in UseAxis),
                temporal=temporal,
                caveats=("ORIGINAL_COMPARISON_OCCURRENCE_NOT_INDEPENDENT_PROPERTY_REVIEW",
                    "SOURCE_ARTIFACT_IS_AUTHENTICATED_CANONICAL_FACT_NOT_RAW_CAPTURE",
                    "NO_DIRECTION_VALUATION_PER_SHARE_OR_MODEL_DISPATCH_GRANT",
                    "SECURITY_TYPE_NOT_CARRIED_BY_CANONICAL_COMPARISON",
                    *SOURCE_INPUT_GAPS),
                input_sha256=digest(fact["field_dependency_receipts"][role]),
            ))
            occurrences.append(dict(metric_ref=metric_ref, canonical_ref=ref, role=role,
                source_row_identity=lineage["source_row_identity"], issuer_id=fields["issuer_id"],
                provider_issuer_id=projection.issuer_id, selected_owner_type=selected["owner_type"],
                statement_basis=fields["statement_basis"], period_start=start, period_end=end,
                fact_sha256=fact_sha, lineage_sha256=digest(lineage),
                owner_receipt=receipt))
    crosswalk = dict(contract=SOURCE_INPUT_CONTRACT, occurrences=occurrences,
        source_relationship_sha256=subject["source_relationship_sha256"])
    bundle = BackendOwnerBundle(security_id=next(iter(security_ids)), ticker=ticker,
        market=subject["market"], generation_id=subject["generation_id"],
        source_generation_id=subject["source_generation_id"],
        source_envelope_sha256=digest(crosswalk), metrics=tuple(metrics), issuer_context=None)
    return bundle, crosswalk


def _source_reference_request(bundle, registry, request_id):
    value = NativeAdmissionInput(security_id=bundle.security_id,
        generation_id=bundle.generation_id, source_generation_id=bundle.source_generation_id,
        metric_refs=tuple(m.metric_ref for m in bundle.metrics))
    return build_native_core_request(build_context(
        admission_input=value, registry=registry, request_id=request_id), registry=registry)


def _property_crosswalk(subject, ticker, comparisons, property_owner):
    if property_owner is None:
        return None, ("INDEPENDENT_ECONOMIC_PROPERTY_OWNER_REQUIRED",)
    _require(type(property_owner) is BackendReviewedPropertyOwner,
             "live_independent_property_owner_required")
    admission = property_owner.resolve(property_owner.admission)
    review = admission.review
    registration = property_owner._owner.registration
    if (registration.ticker, registration.market.lower(), admission.execution_generation_id,
        review.source_generation_id) != (
        ticker, subject["market"], subject["generation_id"], subject["source_generation_id"]
    ):
        return None, ("INDEPENDENT_PROPERTY_SOURCE_SCOPE_MISMATCH",)
    if not comparisons:
        return None, ("CANONICAL_PROPERTY_ECONOMIC_D02_NOT_GRANTED",)
    matches = []
    for reported in review.facts:
        candidates = []
        for ref, (fact, projection) in comparisons.items():
            if (projection.security_id != review.security_id
                    or subject["stock"]["selected_financial_owner"]["owner_type"] != "direct_sec"
                    or projection.issuer_id.lstrip("0") != review.issuer_id.lstrip("0")
                    or fact["fields"]["metric"] != reported.field):
                continue
            for role in ("current", "comparison"):
                row = fact["field_dependency_receipts"][role]["lineage"]
                expected = dict(
                    amount=reported.value, amount_period_start=reported.period_start.isoformat(),
                    amount_period_end=reported.period_end.isoformat(), currency=reported.currency,
                    statement_basis=reported.statement_basis, source_row_identity=reported.source_row_identity,
                    source_payload_sha256=reported.normalized_source_sha256, concept=reported.concept,
                    taxonomy=reported.taxonomy, receipt=reported.filing_accession,
                )
                if all(row.get(k) == value for k, value in expected.items()) and (
                    str(row.get("issuer_cik")).lstrip("0") == reported.issuer_id.lstrip("0")
                    and reported.source_row_identity in fact["fields"]["source_occurrences"]
                    and reported.filed <= datetime.fromisoformat(subject["cutoff"]).date()
                ):
                    candidates.append(dict(
                        canonical_ref=ref, fact_sha256=digest(fact), role=role,
                        source_row_identity=reported.source_row_identity,
                        native_fact_sha256=digest(reported.model_dump(mode="json")),
                        native_raw_source_sha256=reported.raw_source_sha256,
                        normalized_source_sha256=reported.normalized_source_sha256,
                        acquisition_sha256=projection.acquisition_sha256,
                        selected_owner_sha256=projection.selected_owner_sha256,
                        quality_sha256=projection.quality_sha256,
                        source_window_sha256=projection.source_window_sha256,
                    ))
        if len(candidates) != 1:
            return None, ("EXACT_CANONICAL_PROPERTY_OCCURRENCE_CROSSWALK_REQUIRED",)
        matches.append(candidates[0])
    if len({(r["canonical_ref"], r["role"]) for r in matches}) != len(review.facts):
        return None, ("DUPLICATE_CANONICAL_PROPERTY_OCCURRENCE",)
    return dict(property_admission_sha256=admission.admission_sha256, occurrences=matches), ()


class CanonicalNativeAdmission:
    """Opaque backend result. A serialized receipt cannot recreate this handle."""

    def __init__(self):
        raise ValueError("canonical_native_backend_admission_issuance_required")

    def _record(self):
        with _LOCK:
            row = _ADMISSIONS.get(self)
            _require(row is not None and row["pid"] == os.getpid(), "live_admission_required")
            return row

    @property
    def source_owner(self):
        return self._record()["source_owner"]

    @property
    def ticker(self):
        return self._record()["ticker"]

    @property
    def reference_request(self):
        self.verify()
        return self._record()["reference_request"]

    @property
    def registry(self):
        self.verify()
        return self._record()["registry"]

    @property
    def policy(self):
        self.verify()
        return self._record()["policy"]

    @property
    def receipt(self):
        self.verify()
        row = self._record()
        subject = row["source_owner"].resolve_subject(row["ticker"])
        return dict(contract="canonical-native-source-relationship-v1", ticker=row["ticker"],
            generation_id=subject["generation_id"], source_generation_id=subject["source_generation_id"],
            outer_source_envelope_sha256=subject["outer_source_envelope_sha256"],
            inner_consumed_source_sha256=subject["inner_consumed_source_sha256"],
            source_relationship_sha256=subject["source_relationship_sha256"],
            native_owner_envelope_sha256=row["registry"].bundle.source_envelope_sha256,
            crosswalk_sha256=row["crosswalk_sha256"], model_dispatch_allowed=False,
            admission_scope=row["scope"],
            source_occurrences=deepcopy(row.get("crosswalk", {}).get("occurrences", [])),
            consumer_gaps=list(SOURCE_INPUT_GAPS) if row["scope"] == "CORE_VISIBILITY_ONLY" else [])

    def verify(self):
        row = self._record()
        subject = row["source_owner"].resolve_subject(row["ticker"])
        _require(digest(subject) == row["subject_sha256"], "prepared_source_changed")
        comparisons, _ = _subject_evidence(subject, row["ticker"])
        if row["scope"] == "CORE_VISIBILITY_ONLY":
            bundle, crosswalk = _source_input_bundle(subject, row["ticker"], comparisons)
            _require(bundle == row["registry"].bundle and digest(crosswalk) == row["crosswalk_sha256"],
                     "source_input_mapping_changed")
            _require(_source_reference_request(bundle, row["registry"], row["request_id"])
                     == row["reference_request"], "native_reference_request_changed")
            return self
        crosswalk, errors = _property_crosswalk(subject, row["ticker"], comparisons, row["property_owner"])
        _require(not errors and digest(crosswalk) == row["crosswalk_sha256"], "property_crosswalk_changed")
        invocation = row["invocation"]
        request = invocation.verify(invocation.request).reference_request
        _require(build_native_core_request(request.context, registry=invocation._registry) == request,
                 "native_reference_request_changed")
        return self


class CanonicalToNativeAdmissionProducer:
    def __init__(self, source_owner):
        _require(type(source_owner) is CanonicalPreparedSourceOwner, "live_source_capability_required")
        self._source_owner = source_owner

    def produce_source_inputs(self, ticker, *, request_id):
        """Source-owned Core visibility only; no property review or role grant."""
        subject = self._source_owner.resolve_subject(ticker)
        comparisons, excluded = _subject_evidence(subject, ticker)
        if not comparisons:
            return _gap(subject, ticker, tuple(sorted(set((
                "CANONICAL_COMPARISON_D02_CORE_VISIBILITY_REQUIRED", *excluded)))), comparisons)
        bundle, crosswalk = _source_input_bundle(subject, ticker, comparisons)
        # The anchor is derived here only after resolving the live original
        # owner and authenticated projection, never supplied by the request.
        registry = BackendAdmissionRegistry(bundle,
            expected_bundle_sha256=digest(bundle.model_dump(mode="json")))
        request = _source_reference_request(bundle, registry, request_id)
        handle = object.__new__(CanonicalNativeAdmission)
        with _LOCK:
            _ADMISSIONS[handle] = dict(source_owner=self._source_owner, ticker=ticker,
                scope="CORE_VISIBILITY_ONLY", registry=registry, reference_request=request,
                policy=None, request_id=request_id, subject_sha256=digest(subject),
                crosswalk=crosswalk, crosswalk_sha256=digest(crosswalk), pid=os.getpid())
        return handle.verify()

    def produce(self, ticker, *, request_id, property_owner=None):
        subject = self._source_owner.resolve_subject(ticker)
        comparisons, excluded = _subject_evidence(subject, ticker)
        crosswalk, reasons = _property_crosswalk(subject, ticker, comparisons, property_owner)
        if reasons:
            return _gap(subject, ticker, tuple(sorted(set((*reasons, *excluded)))), comparisons)
        # This existing factory owns its permissions. Its offline invocation is
        # retained solely to revalidate the Native reference/policy, never renamed
        # or handed out as manual purpose, transport or accepted-output authority.
        invocation = build_reported_property_invocation(
            property_owner, invocation_id=request_id,
            assessment_as_of=datetime.fromisoformat(subject["cutoff"]).date(),
        )
        handle = object.__new__(CanonicalNativeAdmission)
        with _LOCK:
            _ADMISSIONS[handle] = dict(
                source_owner=self._source_owner, ticker=ticker, property_owner=property_owner,
                invocation=invocation, scope="INDEPENDENT_ECONOMIC_PROPERTY",
                registry=invocation._registry, policy=invocation._policy,
                reference_request=invocation.request.reference_request, subject_sha256=digest(subject),
                crosswalk_sha256=digest(crosswalk), pid=os.getpid(),
            )
        return handle.verify()
