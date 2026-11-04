"""Versioned backend admission. Request callers cannot supply the trust registry."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.unified_snapshot_contract import digest

SHA = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Identity = Annotated[
    str, Field(min_length=1, max_length=512, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/#@+=-]*$")
]


class Closed(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")


class UseState(str, Enum):
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    UNSPECIFIED = "UNSPECIFIED"


class Consumer(str, Enum):
    CORE = "CORE"
    OVERALL = "OVERALL"
    NEWBUYER = "NEWBUYER"
    HOLDER = "HOLDER"
    TIMING = "TIMING"


class UseAxis(str, Enum):
    CORE_VISIBILITY = "CORE_VISIBILITY"
    CORE_VALUATION_CONTEXT = "CORE_VALUATION_CONTEXT"
    CORE_DIRECTION = "CORE_DIRECTION"
    OVERALL_CONTEXT = "OVERALL_CONTEXT"
    OVERALL_DIRECTION = "OVERALL_DIRECTION"
    NEWBUYER_CONTEXT = "NEWBUYER_CONTEXT"
    NEWBUYER_DIRECTION = "NEWBUYER_DIRECTION"
    HOLDER_CONTEXT = "HOLDER_CONTEXT"
    HOLDER_DIRECTION = "HOLDER_DIRECTION"
    TIMING_CONTEXT = "TIMING_CONTEXT"
    TIMING_DIRECTION = "TIMING_DIRECTION"


class Permission(Closed):
    axis: UseAxis
    state: UseState
    owner_evidence_ref: str | None

    @model_validator(mode="after")
    def explicit_authority(self):
        if self.state != UseState.UNSPECIFIED and not self.owner_evidence_ref:
            raise ValueError("EXPLICIT_USE_REQUIRES_OWNER_EVIDENCE")
        return self


class TimeState(str, Enum):
    VERIFIED_OWNER_PERIOD = "VERIFIED_OWNER_PERIOD"
    VERIFIED_METRIC_AS_OF = "VERIFIED_METRIC_AS_OF"
    RETRIEVAL_TIME_ONLY = "RETRIEVAL_TIME_ONLY"
    UNKNOWN_NOT_PROVIDED = "UNKNOWN_NOT_PROVIDED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INVALID_CONFLICT = "INVALID_CONFLICT"


class TemporalField(Closed):
    field: Literal[
        "retrieval_timestamp",
        "metric_as_of",
        "denominator_period_start",
        "denominator_period_end",
        "source_statement_period",
        "price_session",
        "financial_period",
    ]
    value: str | None
    state: TimeState
    owner_ref: str | None
    source_artifact_sha256: SHA | None

    @model_validator(mode="after")
    def owned_time(self):
        known = self.state in {
            TimeState.VERIFIED_OWNER_PERIOD,
            TimeState.VERIFIED_METRIC_AS_OF,
            TimeState.RETRIEVAL_TIME_ONLY,
        }
        if known and not (self.value and self.owner_ref and self.source_artifact_sha256):
            raise ValueError("TEMPORAL_OWNER_REQUIRED")
        if not known and self.value is not None:
            raise ValueError("UNQUALIFIED_TEMPORAL_VALUE")
        if self.state == TimeState.RETRIEVAL_TIME_ONLY and self.field != "retrieval_timestamp":
            raise ValueError("RETRIEVAL_IS_NOT_METRIC_TIME")
        return self


class MetricAuthorityEnvelope(Closed):
    contract: Literal["native-qualified-metric-authority-v1"] = (
        "native-qualified-metric-authority-v1"
    )
    metric_ref: Identity
    metric_type: Identity
    value: float | None = Field(allow_inf_nan=False)
    unit: str | None
    security_id: Identity
    security_type: Identity
    generation_id: Identity
    source_generation_id: Identity
    owner_contract: Identity
    owner_ref: Identity
    owner_receipt_sha256: SHA
    source_provider: Identity
    source_artifact_ref: Identity
    source_artifact_sha256: SHA
    currency: str | None
    share_basis: str | None
    authority_state: Identity
    permissions: tuple[Permission, ...]
    temporal: tuple[TemporalField, ...]
    caveats: tuple[str, ...]
    input_sha256: SHA

    @model_validator(mode="after")
    def complete_contract(self):
        if len(self.permissions) != len(UseAxis) or {p.axis for p in self.permissions} != set(
            UseAxis
        ):
            raise ValueError("EXACT_ALL_CONSUMER_AXES_REQUIRED")
        required = {
            "retrieval_timestamp",
            "metric_as_of",
            "denominator_period_start",
            "denominator_period_end",
            "source_statement_period",
            "price_session",
            "financial_period",
        }
        if len(self.temporal) != len(required) or {t.field for t in self.temporal} != required:
            raise ValueError("EXACT_TEMPORAL_FIELDS_REQUIRED")
        for p in self.permissions:
            if p.owner_evidence_ref and not p.owner_evidence_ref.startswith(self.owner_ref + "#/"):
                raise ValueError("USE_OWNER_BINDING_MISMATCH")
        for t in self.temporal:
            if t.owner_ref is not None and t.owner_ref != self.owner_ref:
                raise ValueError("CROSS_OWNER_TEMPORAL_BINDING")
            if (
                t.source_artifact_sha256 is not None
                and t.source_artifact_sha256 != self.source_artifact_sha256
            ):
                raise ValueError("TEMPORAL_SOURCE_BINDING_MISMATCH")
        return self

    def use(self, axis: UseAxis) -> UseState:
        return next(p.state for p in self.permissions if p.axis == axis)


class FinancialPeriodObservation(Closed):
    period_end: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    source_artifact_sha256: SHA


class IssuerFinancialContext(Closed):
    contract: Literal["issuer-financial-context-v1"] = "issuer-financial-context-v1"
    context_id: Identity
    security_id: Identity
    issuer_id: Identity
    generation_id: Identity
    source_generation_id: Identity
    owner_contract: Literal["admitted-financial-period-observations-v1"] = (
        "admitted-financial-period-observations-v1"
    )
    owner_ref: Identity
    context_role: Literal["ISSUER_FINANCIAL_RECENCY"] = "ISSUER_FINANCIAL_RECENCY"
    financial_period_observations: tuple[FinancialPeriodObservation, ...] = Field(min_length=1)
    issuer_recency: None = None
    statement_basis: None = None
    currency: str | None = None
    share_basis: None = None
    quality_state: Literal["ADMITTED_PERIOD_OBSERVATIONS_ONLY"] = (
        "ADMITTED_PERIOD_OBSERVATIONS_ONLY"
    )
    source_artifact_refs: tuple[SHA, ...] = Field(min_length=1)
    permissions: tuple[Permission, ...]

    @model_validator(mode="after")
    def period_sources(self):
        if len(self.permissions) != len(UseAxis) or {p.axis for p in self.permissions} != set(
            UseAxis
        ):
            raise ValueError("EXACT_ALL_CONSUMER_AXES_REQUIRED")
        for p in self.permissions:
            if p.owner_evidence_ref and not p.owner_evidence_ref.startswith(self.owner_ref + "#/"):
                raise ValueError("ISSUER_USE_OWNER_MISMATCH")
        if {p.source_artifact_sha256 for p in self.financial_period_observations} != set(
            self.source_artifact_refs
        ):
            raise ValueError("ISSUER_PERIOD_SOURCE_MISMATCH")
        return self

    def use(self, axis: UseAxis) -> UseState:
        return next(p.state for p in self.permissions if p.axis == axis)


class BackendOwnerBundle(Closed):
    """Backend composition input, never accepted as a caller request field.

    The backend must supply its independently sealed expected bundle digest.
    This is a trust boundary, not a signature that an untrusted caller can mint.
    """

    contract: Literal["native-backend-owner-bundle-v1"] = "native-backend-owner-bundle-v1"
    security_id: Identity
    ticker: Identity
    market: Literal["us", "kr"]
    generation_id: Identity
    source_generation_id: Identity
    source_envelope_sha256: SHA
    metrics: tuple[MetricAuthorityEnvelope, ...]
    issuer_context: IssuerFinancialContext | None

    @model_validator(mode="after")
    def scope(self):
        entities = [*self.metrics, *([self.issuer_context] if self.issuer_context else [])]
        refs = [m.metric_ref for m in self.metrics]
        if self.issuer_context:
            refs.append(self.issuer_context.context_id)
        if len(refs) != len(set(refs)):
            raise ValueError("DUPLICATE_ADMITTED_REFERENCE")
        for item in entities:
            if (item.security_id, item.generation_id, item.source_generation_id) != (
                self.security_id,
                self.generation_id,
                self.source_generation_id,
            ):
                raise ValueError("BACKEND_OWNER_SCOPE_MISMATCH")
        return self


class AdmissionReceipt(Closed):
    evidence_ref: Identity
    security_id: Identity
    generation_id: Identity
    source_generation_id: Identity
    owner_contract: Identity
    owner_ref: Identity
    source_artifact_sha256: SHA
    schema_sha256: SHA
    payload_sha256: SHA
    authority_sha256: SHA
    temporal_sha256: SHA
    backend_bundle_sha256: SHA


class NativeAdmissionInput(Closed):
    security_id: Identity
    generation_id: Identity
    source_generation_id: Identity
    metric_refs: tuple[Identity, ...]
    issuer_context: IssuerFinancialContext | None = None


class BackendAdmissionRegistry:
    """Read-only backend dependency; not serializable caller authorization."""

    def __init__(self, bundle: BackendOwnerBundle, *, expected_bundle_sha256: str):
        frozen = BackendOwnerBundle.model_validate(bundle.model_dump(mode="json"))
        if digest(frozen.model_dump(mode="json")) != expected_bundle_sha256:
            raise ValueError("BACKEND_INDEPENDENT_ANCHOR_MISMATCH")
        self._bundle_json = frozen.model_dump_json()
        self._anchor = expected_bundle_sha256

    @property
    def bundle(self) -> BackendOwnerBundle:
        return BackendOwnerBundle.model_validate_json(self._bundle_json)

    def entity(self, ref: str) -> MetricAuthorityEnvelope | IssuerFinancialContext:
        bundle = self.bundle
        for m in bundle.metrics:
            if m.metric_ref == ref:
                return m
        if bundle.issuer_context and bundle.issuer_context.context_id == ref:
            return bundle.issuer_context
        raise ValueError("UNADMITTED_REFERENCE")

    def receipt(self, ref: str) -> AdmissionReceipt:
        item = self.entity(ref)
        metric = isinstance(item, MetricAuthorityEnvelope)
        payload = item.model_dump(mode="json")
        return AdmissionReceipt(
            evidence_ref=ref,
            security_id=item.security_id,
            generation_id=item.generation_id,
            source_generation_id=item.source_generation_id,
            owner_contract=item.owner_contract,
            owner_ref=item.owner_ref,
            source_artifact_sha256=item.source_artifact_sha256
            if metric
            else digest(item.source_artifact_refs),
            schema_sha256=digest(type(item).model_json_schema()),
            payload_sha256=digest(payload),
            authority_sha256=digest(payload["permissions"]),
            temporal_sha256=digest(
                payload["temporal"] if metric else payload["financial_period_observations"]
            ),
            backend_bundle_sha256=self._anchor,
        )

    def admit(self, value: NativeAdmissionInput | dict) -> NativeAdmissionInput:
        value = NativeAdmissionInput.model_validate(
            value.model_dump(mode="json") if isinstance(value, NativeAdmissionInput) else value
        )
        b = self.bundle
        if (value.security_id, value.generation_id, value.source_generation_id) != (
            b.security_id,
            b.generation_id,
            b.source_generation_id,
        ):
            raise ValueError("INPUT_IDENTITY_BINDING_MISMATCH")
        if len(value.metric_refs) != len(set(value.metric_refs)):
            raise ValueError("DUPLICATE_REQUEST_REFERENCE")
        for ref in value.metric_refs:
            if not isinstance(self.entity(ref), MetricAuthorityEnvelope):
                raise ValueError("METRIC_ROLE_REQUIRED")
        if value.issuer_context is not None and value.issuer_context != b.issuer_context:
            raise ValueError("ISSUER_CONTEXT_ADMISSION_MISMATCH")
        return value

    def allowed(self, ref: str, consumer: Consumer, axis: UseAxis) -> bool:
        if axis.value.split("_", 1)[0] != consumer.value:
            return False
        entity = self.entity(ref)
        return entity.use(axis) == UseState.ALLOWED
