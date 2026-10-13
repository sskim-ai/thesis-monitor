"""Default-off native Core authority path with request-bound claim acceptance."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import Field

from app.services.contract_schema_validation import validate_json_schema
from app.services.native_input_admission import (
    SHA,
    AdmissionReceipt,
    BackendAdmissionRegistry,
    Closed,
    Consumer,
    Identity,
    IssuerFinancialContext,
    MetricAuthorityEnvelope,
    NativeAdmissionInput,
    Permission,
    TemporalField,
    UseAxis,
    UseState,
)
from app.services.unified_snapshot_contract import digest

CONTRACT = "accepted-v2-production-context-authority-v2"
POLICY = "native-core-request-membership-and-exact-axis-v1"


class MetricTemporalProvenance(Closed):
    evidence_ref: Identity
    fields: tuple[TemporalField, ...]


class MetricPermissions(Closed):
    evidence_ref: Identity
    permissions: tuple[Permission, ...]


class AcceptedV2AuthorityContext(Closed):
    contract: Literal["accepted-v2-production-context-authority-v2"] = CONTRACT
    policy: Literal["native-core-request-membership-and-exact-axis-v1"] = POLICY
    request_id: Identity
    security_id: Identity
    ticker: Identity
    market: Literal["us", "kr"]
    generation_id: Identity
    source_generation_id: Identity
    source_envelope_sha256: SHA
    input_admission: tuple[AdmissionReceipt, ...]
    metric_authority_envelopes: tuple[MetricAuthorityEnvelope, ...]
    issuer_context_admissions: tuple[AdmissionReceipt, ...]
    issuer_financial_context: IssuerFinancialContext | None
    temporal_provenance: tuple[MetricTemporalProvenance, ...]
    consumer_axis_permissions: tuple[MetricPermissions, ...]
    request_evidence_membership: tuple[Identity, ...]
    backend_bundle_sha256: SHA


class BoundEvidenceReference(Closed):
    evidence_ref: Identity
    owner_ref: Identity
    admission_sha256: SHA
    authority_sha256: SHA
    temporal_sha256: SHA


class NativeAuthorityClaim(Closed):
    consumer: Consumer
    use_axis: UseAxis
    evidence: tuple[BoundEvidenceReference, ...] = Field(min_length=1, max_length=6)


class ModelReferenceSelection(Closed):
    consumer: Consumer
    use_axis: UseAxis
    evidence_refs: tuple[Identity, ...] = Field(min_length=1, max_length=6)


class NativeModelReferenceOutput(Closed):
    """Model-facing reference selection only. Backend owns all binding hashes."""

    selections: tuple[ModelReferenceSelection, ...] = Field(min_length=1)


class NativeCoreAuthorityOutput(Closed):
    """Reference-authorized Core output, not an accepted investment judgment.

    Model execution, economic decision acceptance and downstream judgment owners
    remain separately authorized runtime boundaries.
    """

    contract: Literal["native-core-authority-output-v2"] = "native-core-authority-output-v2"
    request_sha256: SHA
    security_id: Identity
    generation_id: Identity
    source_generation_id: Identity
    claims: tuple[NativeAuthorityClaim, ...] = Field(min_length=1)


class RequestAuthorization(Closed):
    contract: Literal["native-core-request-authorization-v2"] = (
        "native-core-request-authorization-v2"
    )
    context_contract: Literal["accepted-v2-production-context-authority-v2"] = CONTRACT
    request_sha256: SHA
    context_sha256: SHA
    prompt_sha256: SHA
    schema_sha256: SHA
    policy_sha256: SHA
    validator_sha256: SHA
    authority_sha256: SHA
    source_envelope_sha256: SHA
    owner_sha256: SHA
    security_id: Identity
    generation_id: Identity
    source_generation_id: Identity
    allowed_evidence_refs: tuple[Identity, ...]
    consumer_axis_map: tuple[MetricPermissions, ...]
    admission_sha256: SHA


class NativeCoreRequest(Closed):
    contract: Literal["native-core-authority-request-v2"] = "native-core-authority-request-v2"
    context: AcceptedV2AuthorityContext
    prompt: str
    response_schema_json: str
    authorization: RequestAuthorization


def build_context(*, admission_input, registry: BackendAdmissionRegistry, request_id: str):
    if not isinstance(registry, BackendAdmissionRegistry):
        raise ValueError("BACKEND_ADMISSION_REGISTRY_REQUIRED")
    admitted = registry.admit(admission_input)
    bundle = registry.bundle
    metrics = tuple(registry.entity(ref) for ref in admitted.metric_refs)
    issuer = admitted.issuer_context
    refs = (*admitted.metric_refs, *((issuer.context_id,) if issuer else ()))
    receipts = tuple(registry.receipt(ref) for ref in refs)
    return AcceptedV2AuthorityContext(
        request_id=request_id,
        security_id=bundle.security_id,
        ticker=bundle.ticker,
        market=bundle.market,
        generation_id=bundle.generation_id,
        source_generation_id=bundle.source_generation_id,
        source_envelope_sha256=bundle.source_envelope_sha256,
        input_admission=receipts,
        metric_authority_envelopes=metrics,
        issuer_context_admissions=tuple(
            r for r in receipts if issuer and r.evidence_ref == issuer.context_id
        ),
        issuer_financial_context=issuer,
        temporal_provenance=tuple(
            MetricTemporalProvenance(evidence_ref=m.metric_ref, fields=m.temporal) for m in metrics
        ),
        consumer_axis_permissions=tuple(
            MetricPermissions(evidence_ref=m.metric_ref, permissions=m.permissions) for m in metrics
        )
        + (
            (MetricPermissions(evidence_ref=issuer.context_id, permissions=issuer.permissions),)
            if issuer
            else ()
        ),
        request_evidence_membership=refs,
        backend_bundle_sha256=digest(bundle.model_dump(mode="json")),
    )


def verify_context(context, registry):
    if not isinstance(registry, BackendAdmissionRegistry):
        raise ValueError("BACKEND_ADMISSION_REGISTRY_REQUIRED")
    context = AcceptedV2AuthorityContext.model_validate(
        context.model_dump(mode="json")
        if isinstance(context, AcceptedV2AuthorityContext)
        else context
    )
    value = NativeAdmissionInput(
        security_id=context.security_id,
        generation_id=context.generation_id,
        source_generation_id=context.source_generation_id,
        metric_refs=tuple(m.metric_ref for m in context.metric_authority_envelopes),
        issuer_context=context.issuer_financial_context,
    )
    expected = build_context(
        admission_input=value, registry=registry, request_id=context.request_id
    )
    if context != expected:
        raise ValueError("NATIVE_CONTEXT_ADMISSION_MISMATCH")
    return context


def _visible(metric):
    return metric.use(UseAxis.CORE_VISIBILITY) == UseState.ALLOWED


def _usable(metric, axis):
    return _visible(metric) and metric.use(axis) == UseState.ALLOWED


def prompt_context(context: AcceptedV2AuthorityContext):
    visible = []
    restrictions = []
    for metric in context.metric_authority_envelopes:
        metadata = dict(
            evidence_ref=metric.metric_ref,
            owner_ref=metric.owner_ref,
            permissions=[p.model_dump(mode="json") for p in metric.permissions],
            temporal=[t.model_dump(mode="json") for t in metric.temporal],
        )
        restrictions.append(metadata)
        if _visible(metric) and any(
            _usable(metric, a) for a in UseAxis if a != UseAxis.CORE_VISIBILITY
        ):
            visible.append(
                dict(
                    **metadata,
                    value=metric.value,
                    unit=metric.unit,
                    metric_type=metric.metric_type,
                    caveats=metric.caveats,
                )
            )
    return dict(
        contract=CONTRACT,
        request_id=context.request_id,
        security_id=context.security_id,
        generation_id=context.generation_id,
        source_generation_id=context.source_generation_id,
        NON_DIRECTIONAL_VALUATION_CONTEXT=[
            v
            for v in visible
            if next(
                m for m in context.metric_authority_envelopes if m.metric_ref == v["evidence_ref"]
            ).use(UseAxis.CORE_VALUATION_CONTEXT)
            == UseState.ALLOWED
        ],
        DIRECTIONAL_EVIDENCE=[
            v
            for v in visible
            if next(
                m for m in context.metric_authority_envelopes if m.metric_ref == v["evidence_ref"]
            ).use(UseAxis.CORE_DIRECTION)
            == UseState.ALLOWED
        ],
        authority_restrictions=restrictions,
        issuer_financial_context=context.issuer_financial_context.model_dump(mode="json")
        if context.issuer_financial_context
        and _usable(context.issuer_financial_context, UseAxis.CORE_VALUATION_CONTEXT)
        else None,
    )


def core_prompt(context):
    return (
        "Native Core authority contract v2. Return structured reference selections only; no free prose or decisions. "
        "Each claim requires current-request membership and an explicit grant for its consumer/use axis. "
        "Numbers, availability and another consumer's permission do not grant authority. "
        "Unknown metric dates remain unknown; issuer statement recency is not a ratio denominator. "
        "This request does not authorize accepted investment judgments, downstream delivery or B2.\n"
        + json.dumps(
            prompt_context(context), sort_keys=True, ensure_ascii=False, separators=(",", ":")
        )
    )


def output_schema(context):
    schema = NativeModelReferenceOutput.model_json_schema()
    schema["$defs"]["ModelReferenceSelection"]["properties"]["evidence_refs"]["items"] = {
        "type": "string",
        "enum": list(context.request_evidence_membership),
    }
    return schema


def batch_identity(context):
    return dict(
        contract="fundamental-core-authority-batch-identity-v2",
        context_contract=context.contract,
        request_id=context.request_id,
        security_id=context.security_id,
        generation_id=context.generation_id,
        source_generation_id=context.source_generation_id,
        admission_sha256=digest([x.model_dump(mode="json") for x in context.input_admission]),
        authority_sha256=digest(
            [x.model_dump(mode="json") for x in context.consumer_axis_permissions]
        ),
        membership_sha256=digest(context.request_evidence_membership),
        source_envelope_sha256=context.source_envelope_sha256,
    )


def _code_sha():
    from app.services import (
        native_input_admission,
        accepted_decision_v2_runtime_service,
        contract_schema_validation,
        unified_snapshot_contract,
    )

    return digest(
        [
            hashlib.sha256(Path(path).read_bytes()).hexdigest()
            for path in [
                __file__,
                native_input_admission.__file__,
                accepted_decision_v2_runtime_service.__file__,
                contract_schema_validation.__file__,
                unified_snapshot_contract.__file__,
            ]
        ]
    )


def build_native_core_request(context, *, registry):
    context = verify_context(context, registry)
    # Call the real, version-dispatched native entrypoints, not a report builder.
    from app.services.accepted_decision_v2_runtime_service import (
        accepted_v2_fundamental_core_prompt,
        accepted_v2_fundamental_core_output_schema,
    )

    prompt = accepted_v2_fundamental_core_prompt(context, admission_registry=registry)
    schema = accepted_v2_fundamental_core_output_schema(context, admission_registry=registry)
    body = dict(
        contract="native-core-authority-request-v2",
        context=context.model_dump(mode="json"),
        prompt=prompt,
        response_schema=schema,
        validator_sha256=_code_sha(),
        policy_sha256=digest(POLICY),
    )
    receipts = [x.model_dump(mode="json") for x in context.input_admission]
    authorization = RequestAuthorization(
        request_sha256=digest(body),
        context_sha256=digest(body["context"]),
        prompt_sha256=digest(prompt),
        schema_sha256=digest(schema),
        policy_sha256=digest(POLICY),
        validator_sha256=body["validator_sha256"],
        authority_sha256=digest(
            [x.model_dump(mode="json") for x in context.consumer_axis_permissions]
        ),
        source_envelope_sha256=context.source_envelope_sha256,
        owner_sha256=digest(receipts),
        security_id=context.security_id,
        generation_id=context.generation_id,
        source_generation_id=context.source_generation_id,
        allowed_evidence_refs=context.request_evidence_membership,
        consumer_axis_map=context.consumer_axis_permissions,
        admission_sha256=digest(receipts),
    )
    return NativeCoreRequest(
        context=context,
        prompt=prompt,
        response_schema_json=json.dumps(schema, sort_keys=True, separators=(",", ":")),
        authorization=authorization,
    )


def accept_native_core_output(output, request, *, registry, expected_request_sha256):
    """The single AND boundary. Expected request SHA is held by the backend invocation."""
    request = NativeCoreRequest.model_validate(
        request.model_dump(mode="json") if isinstance(request, NativeCoreRequest) else request
    )
    expected = build_native_core_request(request.context, registry=registry)
    if request != expected or request.authorization.request_sha256 != expected_request_sha256:
        raise ValueError("REJECT_REQUEST_IDENTITY_BINDING")
    output = NativeCoreAuthorityOutput.model_validate(
        output.model_dump(mode="json") if isinstance(output, NativeCoreAuthorityOutput) else output
    )
    c = request.context
    if (
        output.request_sha256,
        output.security_id,
        output.generation_id,
        output.source_generation_id,
    ) != (expected_request_sha256, c.security_id, c.generation_id, c.source_generation_id):
        raise ValueError("REJECT_OUTPUT_IDENTITY_BINDING")
    for claim in output.claims:
        for use in claim.evidence:
            # Authority in the store is necessary but never substitutes for request membership.
            if use.evidence_ref not in c.request_evidence_membership:
                raise ValueError("REJECT_REQUEST_MEMBERSHIP")
            if not registry.allowed(use.evidence_ref, claim.consumer, claim.use_axis):
                raise ValueError("REJECT_CONSUMER_AUTHORITY")
            entity = registry.entity(use.evidence_ref)
            if claim.consumer == Consumer.CORE and not _visible(entity):
                raise ValueError("REJECT_CORE_INPUT_VISIBILITY")
            receipt = registry.receipt(use.evidence_ref)
            if (use.owner_ref, use.admission_sha256, use.authority_sha256, use.temporal_sha256) != (
                receipt.owner_ref,
                digest(receipt.model_dump(mode="json")),
                receipt.authority_sha256,
                receipt.temporal_sha256,
            ):
                raise ValueError("REJECT_OWNER_ADMISSION_TEMPORAL_BINDING")
    selection = dict(
        selections=[
            dict(
                consumer=c.consumer.value,
                use_axis=c.use_axis.value,
                evidence_refs=[r.evidence_ref for r in c.evidence],
            )
            for c in output.claims
        ]
    )
    if validate_json_schema(selection, json.loads(request.response_schema_json)):
        raise ValueError("REJECT_REQUEST_SCHEMA")
    return output


def materialize_native_reference_output(selection, request, *, registry, expected_request_sha256):
    """Bind only schema-admitted model refs using the independent backend invocation."""
    selection = NativeModelReferenceOutput.model_validate(selection)
    if validate_json_schema(
        selection.model_dump(mode="json"), json.loads(request.response_schema_json)
    ):
        raise ValueError("REJECT_REQUEST_SCHEMA")
    claims = []
    for item in selection.selections:
        refs = []
        for ref in item.evidence_refs:
            receipt = registry.receipt(ref)
            refs.append(
                BoundEvidenceReference(
                    evidence_ref=ref,
                    owner_ref=receipt.owner_ref,
                    admission_sha256=digest(receipt.model_dump(mode="json")),
                    authority_sha256=receipt.authority_sha256,
                    temporal_sha256=receipt.temporal_sha256,
                )
            )
        claims.append(
            NativeAuthorityClaim(
                consumer=item.consumer, use_axis=item.use_axis, evidence=tuple(refs)
            )
        )
    output = NativeCoreAuthorityOutput(
        request_sha256=request.authorization.request_sha256,
        security_id=request.context.security_id,
        generation_id=request.context.generation_id,
        source_generation_id=request.context.source_generation_id,
        claims=tuple(claims),
    )
    return accept_native_core_output(
        output, request, registry=registry, expected_request_sha256=expected_request_sha256
    )
