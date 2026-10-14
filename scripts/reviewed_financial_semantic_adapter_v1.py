"""Fixed historical M12AU financial semantics, never augmented or current authority."""

from collections.abc import Mapping

from app.services.direction_timing_ownership_service import stage_alias_catalogs
from app.services.directional_financial_context_service import (
    FinancialSemanticValidation,
    validate_directional_financial_semantics,
)
from app.services.reviewed_fixture_authority import (
    build_reviewed_owned_fixture,
    verify_reviewed_owned_fixture,
)


_RECIPE_ID = "financial:FIC-FIN-01"
_GENERATION = "m12au-test"
_TICKER = "FIC-FIN-01"


def validate_m12au_financial_v1(
    candidate: Mapping[str, object],
) -> FinancialSemanticValidation:
    """Use only the existing fixed parent and its actual selected catalog."""
    if not isinstance(candidate, Mapping) or candidate.get("ticker") != _TICKER:
        raise ValueError("m12au_financial_candidate_identity_mismatch")
    parent = build_reviewed_owned_fixture(_RECIPE_ID, generation=_GENERATION)
    seal = verify_reviewed_owned_fixture(parent, consumer="FINANCIAL_CONTEXT")
    if seal.recipe_id != _RECIPE_ID or seal.parameters != (
        ("generation", _GENERATION),
    ):
        raise ValueError("m12au_financial_parent_contract_mismatch")
    catalog, _ = stage_alias_catalogs(parent)
    return validate_directional_financial_semantics(
        candidate,
        supplied_refs=tuple(row.ref for row in parent.evidence),
        allowed_ref_ids=tuple(catalog.by_ref),
        sector_framework=parent.sector_framework,
    )
