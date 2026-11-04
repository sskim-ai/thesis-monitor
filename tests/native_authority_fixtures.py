"""Synthetic backend trust roots, never corporate evidence or accepted judgments."""

from app.services.native_input_admission import (
    BackendAdmissionRegistry,
    BackendOwnerBundle,
    IssuerFinancialContext,
    MetricAuthorityEnvelope,
    Permission,
    TemporalField,
    UseAxis,
    UseState,
)
from app.services.native_authority_core import build_native_core_request
from app.services.accepted_decision_v2_runtime_service import build_accepted_v2_production_context
from app.services.unified_snapshot_contract import digest


def synthetic_registry(
    identity="SYNTHETIC_NATIVE_SUBJECT", *, grants=None, market="us", security_type="common_stock"
):
    grants = grants or {"METRIC_A": {}, "METRIC_B": {}}
    metrics = []
    for name, override in grants.items():
        owner = identity + ":" + name + ":synthetic-owner"
        raw = digest([identity, name, "SYNTHETIC_SOURCE_ONLY"])
        permissions = {a: UseState.UNSPECIFIED for a in UseAxis}
        permissions.update(
            {
                UseAxis.CORE_VISIBILITY: UseState.ALLOWED,
                UseAxis.CORE_VALUATION_CONTEXT: UseState.ALLOWED,
                UseAxis.CORE_DIRECTION: UseState.ALLOWED,
                UseAxis.OVERALL_DIRECTION: UseState.DENIED,
            }
        )
        permissions.update({UseAxis(k): UseState(v) for k, v in override.items()})
        metrics.append(
            MetricAuthorityEnvelope(
                metric_ref=identity + ":" + name,
                metric_type=name,
                value=12.25,
                unit="ratio",
                security_id=identity,
                security_type=security_type,
                generation_id="synthetic-native-generation",
                source_generation_id="synthetic-source-generation",
                owner_contract="synthetic-test-owner-v1",
                owner_ref=owner,
                owner_receipt_sha256=digest([owner, permissions]),
                source_provider="SYNTHETIC_TEST_ONLY",
                source_artifact_ref=identity + ":raw",
                source_artifact_sha256=raw,
                currency=None,
                share_basis=None,
                authority_state="SYNTHETIC_TEST_AUTHORITY",
                permissions=tuple(
                    Permission(
                        axis=a,
                        state=s,
                        owner_evidence_ref=owner + "#/" + a.value
                        if s != UseState.UNSPECIFIED
                        else None,
                    )
                    for a, s in permissions.items()
                ),
                temporal=tuple(
                    TemporalField(
                        field=f,
                        value="2026-10-09T00:00:00Z" if f == "retrieval_timestamp" else None,
                        state="RETRIEVAL_TIME_ONLY"
                        if f == "retrieval_timestamp"
                        else "UNKNOWN_NOT_PROVIDED",
                        owner_ref=owner if f == "retrieval_timestamp" else None,
                        source_artifact_sha256=raw if f == "retrieval_timestamp" else None,
                    )
                    for f in (
                        "retrieval_timestamp",
                        "metric_as_of",
                        "denominator_period_start",
                        "denominator_period_end",
                        "source_statement_period",
                        "price_session",
                        "financial_period",
                    )
                ),
                caveats=("SYNTHETIC_TEST_ONLY_NOT_CORPORATE_EVIDENCE",),
                input_sha256=raw,
            )
        )
    raw = digest([identity, "SYNTHETIC_ISSUER_PERIOD"])
    issuer = IssuerFinancialContext(
        context_id=identity + ":issuer-periods",
        security_id=identity,
        issuer_id=identity + ":issuer",
        generation_id="synthetic-native-generation",
        source_generation_id="synthetic-source-generation",
        owner_ref=identity + ":period-owner",
        financial_period_observations=(
            {"period_end": "2025-06-30", "source_artifact_sha256": raw},
        ),
        source_artifact_refs=(raw,),
        permissions=tuple(
            Permission(
                axis=a,
                state="ALLOWED"
                if a in {UseAxis.CORE_VISIBILITY, UseAxis.CORE_VALUATION_CONTEXT}
                else "UNSPECIFIED",
                owner_evidence_ref=identity + ":period-owner#/synthetic-role-grant"
                if a in {UseAxis.CORE_VISIBILITY, UseAxis.CORE_VALUATION_CONTEXT}
                else None,
            )
            for a in UseAxis
        ),
    )
    bundle = BackendOwnerBundle(
        security_id=identity,
        ticker=identity,
        market=market,
        generation_id=issuer.generation_id,
        source_generation_id=issuer.source_generation_id,
        source_envelope_sha256=digest([raw, "synthetic-envelope"]),
        metrics=tuple(metrics),
        issuer_context=issuer,
    )
    return BackendAdmissionRegistry(
        bundle, expected_bundle_sha256=digest(bundle.model_dump(mode="json"))
    )


def native_input(registry, refs=None):
    b = registry.bundle
    return dict(
        security_id=b.security_id,
        generation_id=b.generation_id,
        source_generation_id=b.source_generation_id,
        metric_refs=list(refs if refs is not None else [m.metric_ref for m in b.metrics]),
        issuer_context=b.issuer_context.model_dump(mode="json") if b.issuer_context else None,
    )


def native_request(registry, refs=None):
    context = build_accepted_v2_production_context(
        packet={},
        claim_id="synthetic-native-invocation",
        evidence_packets=(),
        authority_native_v2=True,
        admission_input=native_input(registry, refs),
        admission_registry=registry,
    )
    return build_native_core_request(context, registry=registry)


def output_for(registry, request, ref=None, axis="CORE_DIRECTION"):
    ref = ref or registry.bundle.metrics[0].metric_ref
    receipt = registry.receipt(ref)
    return dict(
        contract="native-core-authority-output-v2",
        request_sha256=request.authorization.request_sha256,
        security_id=request.context.security_id,
        generation_id=request.context.generation_id,
        source_generation_id=request.context.source_generation_id,
        claims=[
            dict(
                consumer=axis.split("_", 1)[0],
                use_axis=axis,
                evidence=[
                    dict(
                        evidence_ref=ref,
                        owner_ref=receipt.owner_ref,
                        admission_sha256=digest(receipt.model_dump(mode="json")),
                        authority_sha256=receipt.authority_sha256,
                        temporal_sha256=receipt.temporal_sha256,
                    )
                ],
            )
        ],
    )
