"""Opt-in M12AT role-scoped schema; not model-candidate acceptance authority."""
from app.services.configured_signal_evidence_service import build_configured_signal_evidence_view
from app.services.direction_timing_ownership_service import stage_alias_catalogs
from app.services.reviewed_configured_composition import (
    SCHEMA_CONSUMER,
    verify_reviewed_configured_composition,
)

CONTRACT = "reviewed-configured-role-schema-v2"


def configured_role_schema_v2(children):
    """Use only existing schema grants and preserve the frozen v1 route."""
    from scripts import configured_signal_field_ownership_m12at as historical

    capability = historical.capability
    if tuple(children) != tuple(capability.m12.CONTEXTS[0]):
        raise ValueError("configured_composition_context0_exact_subjects_required")
    parents, catalogs, contexts, aliases, constraints = {}, {}, {}, {}, {}
    for ticker, child in children.items():
        recipe = verify_reviewed_configured_composition(child, consumer=SCHEMA_CONSUMER)
        if ticker != recipe["subject"]:
            raise ValueError("configured_composition_candidate_identity_mismatch")
        parents[ticker] = child.parent
        catalog, _ = stage_alias_catalogs(child.parent)
        catalogs[ticker] = catalog
        contexts[ticker] = capability.m12.holdout._owned_context(child.parent, catalog)
        current = tuple(catalog.by_alias)
        future = tuple(f"P{i:02d}" for i in range(1, len(child.configured_rows) + 1))
        if set(current) & set(future):
            raise ValueError("configured_composition_alias_collision")
        aliases[ticker] = current + future
        roles = build_configured_signal_evidence_view(
            ticker=ticker, supplied_refs=child.configured_rows,
        ).by_ref
        constraints[ticker] = {
            field: current for field in historical.DirectionalCoreJudgment.model_fields
        }
        for field, permission in (
            ("business_reevaluation_up", "future_reevaluation_eligible"),
            ("business_reevaluation_down", "future_reevaluation_eligible"),
            ("risk_context", "risk_context_eligible"),
        ):
            constraints[ticker][field] = current + tuple(
                alias for alias, row in zip(future, child.configured_rows, strict=True)
                if getattr(roles[row.ref_id], permission)
            )
    views = capability._views(parents, catalogs, contexts)
    expectations = capability._expectation_views(parents, catalogs)
    schema = capability.build_business_delta_constrained_batch_schema(
        candidate_schema=capability.base._candidate_schema(historical.DirectionalCoreJudgment),
        contract="directional-core-judgment-output-v1",
        packet_id="m12at-deterministic-preflight",
        aliases_by_ticker=aliases, views=views,
        reference_aliases_by_ticker_field=constraints,
    )
    return capability.constrain_market_expectation_batch_schema(schema, views=expectations)

