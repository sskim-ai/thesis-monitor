"""Explicit finite M12AT/M12AU successor; frozen historical builders stay intact."""
from app.services.configured_signal_evidence_service import (
    CURRENT_DIRECTIONAL_REFERENCE_FIELDS,
    build_configured_signal_evidence_view,
    configured_signal_model_context,
    validate_configured_signal_field_ownership,
)
from app.services.direction_timing_ownership_service import stage_alias_catalogs
from app.services.directional_financial_context_service import validate_directional_financial_semantics
from app.services.reviewed_configured_composition import (
    FUTURE_FIELDS,
    M12AU_CONSUMER,
    MODEL_VIEW_CONSUMER,
    SCHEMA_CONSUMER,
    build_reviewed_configured_composition,
    validate_composed_reference_use,
    verify_reviewed_configured_composition,
)
from app.services.reviewed_fixture_authority import build_reviewed_owned_fixture


def m12au_composition_v1():
    parent = build_reviewed_owned_fixture("financial:FIC-FIN-01", generation="m12au-test")
    return build_reviewed_configured_composition(parent,
        recipe_id="m12au-test:FIC-FIN-01", consumer=M12AU_CONSUMER)


def validate_m12au_composition_v1(child, candidate):
    allowed = validate_composed_reference_use(child, candidate, consumer=M12AU_CONSUMER)
    view = build_configured_signal_evidence_view(ticker=child.parent.source_packet.ticker,
        supplied_refs=child.configured_rows)
    configured = validate_configured_signal_field_ownership(candidate, view)
    if not configured.valid:
        raise ValueError("configured_composition_prospective_only")
    return validate_directional_financial_semantics(candidate,
        supplied_refs=tuple(row.ref for row in child.parent.evidence) + child.configured_rows,
        allowed_ref_ids=allowed, sector_framework=child.parent.sector_framework)


def validate_m12au_configured_v1(candidate):
    return validate_m12au_composition_v1(m12au_composition_v1(), candidate)


def configured_model_projection_v1(child, parent_context):
    verify_reviewed_configured_composition(child, consumer=MODEL_VIEW_CONSUMER)
    from scripts import directional_core_price_timing_holdout as holdout

    catalog, _ = stage_alias_catalogs(child.parent)
    expected = holdout._owned_context(child.parent, catalog)
    if parent_context != expected:
        raise ValueError("configured_composition_parent_context_mismatch")
    view = build_configured_signal_evidence_view(ticker=child.parent.source_packet.ticker,
        supplied_refs=child.configured_rows)
    metadata = configured_signal_model_context(view)
    # Separate future-only attachment: no new parent catalog or current evidence.
    return dict(contract="reviewed-configured-model-projection-v1", provenance="TEST_ONLY",
        parent_context=parent_context, future_configured_conditions=[
            dict(alias=f"P{index:02d}", **row.model_dump(mode="json"),
                configured_signal=metadata[row.ref_id])
            for index, row in enumerate(child.configured_rows, 1)])


def configured_schema_v1(children):
    from scripts import configured_signal_field_ownership_m12at as historical

    capability = historical.capability
    expected_tickers = tuple(capability.m12.CONTEXTS[0])
    if tuple(children) != expected_tickers:
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
        configured = build_configured_signal_evidence_view(ticker=ticker,
            supplied_refs=child.configured_rows).by_ref
        constraints[ticker] = {field: aliases[ticker] if field in FUTURE_FIELDS else current
            for field in historical.DirectionalCoreJudgment.model_fields}
        constraints[ticker]["risk_context"] = current + tuple(alias
            for alias, row in zip(future, child.configured_rows, strict=True)
            if configured[row.ref_id].risk_context_eligible)
    views = capability._views(parents, catalogs, contexts)
    expectations = capability._expectation_views(parents, catalogs)
    schema = capability.build_business_delta_constrained_batch_schema(
        candidate_schema=capability.base._candidate_schema(historical.DirectionalCoreJudgment),
        contract="directional-core-judgment-output-v1",
        packet_id="m12at-deterministic-preflight", aliases_by_ticker=aliases,
        views=views, reference_aliases_by_ticker_field=constraints)
    return capability.constrain_market_expectation_batch_schema(schema, views=expectations)


def m12at_schema_impact_v1():
    from scripts import configured_signal_field_ownership_m12at as historical

    generation = "m12at-deterministic-preflight"
    children = {}
    for ticker in historical.capability.m12.CONTEXTS[0]:
        parent = build_reviewed_owned_fixture("financial:" + ticker, generation=generation)
        children[ticker] = build_reviewed_configured_composition(parent,
            recipe_id=generation + ":" + ticker, consumer=SCHEMA_CONSUMER)
    schema = configured_schema_v1(children)
    first = next(iter(children.values()))
    model_child = build_reviewed_configured_composition(first.parent,
        recipe_id=first.recipe_id, consumer=MODEL_VIEW_CONSUMER)
    catalog, _ = stage_alias_catalogs(first.parent)
    context = historical.capability.m12.holdout._owned_context(first.parent, catalog)
    projection = configured_model_projection_v1(model_child, context)
    configured = {row["alias"] for row in projection["future_configured_conditions"]}
    current = {field: historical._schema_ref_values(schema, field)
        for field in CURRENT_DIRECTIONAL_REFERENCE_FIELDS}
    future = historical._schema_ref_values(schema, "business_reevaluation_down")
    passed = all(configured.isdisjoint(values) for values in current.values()) and configured <= set(future)
    return dict(status="PASS" if passed else "FAIL", ticker=first.parent.source_packet.ticker,
        contract="reviewed-configured-semantic-adapter-v1", provenance="TEST_ONLY",
        configured_aliases=sorted(configured), current_field_aliases=current,
        future_field_aliases=future,
        configured_model_surface_rows=projection["future_configured_conditions"],
        parent_context=projection["parent_context"], schema=schema)
