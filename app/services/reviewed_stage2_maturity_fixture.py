"""Finite offline maturity recipes, not economic or production source authority."""
from typing import Literal

from app.services.accepted_decision_v2_runtime_service import (
    AcceptedV2EvidenceOwnership,
    AcceptedV2ProductionBatchOutput,
    AcceptedV2ProductionBatchOutputV2,
    STAGE2_MATURITY_PROVENANCE_MATERIALIZATION_CONTRACT,
    canonical_sha256,
    interaction_from_packet,
)
from app.services.cross_market_decision_engine_service import DecisionEvidencePacket
from app.services.reviewed_core_fixture import ReviewedCoreFixtureContext
from app.services import reviewed_fixture_authority as owner


class ReviewedMaturityFixtureContext(ReviewedCoreFixtureContext):
    fixture_use: Literal["STAGE2_MATURITY_ONLY"] = "STAGE2_MATURITY_ONLY"


class ReviewedMaturityOutput(AcceptedV2ProductionBatchOutput):
    provenance: Literal["TEST_ONLY"] = "TEST_ONLY"
    production_eligible: Literal[False] = False


class ReviewedMaturityOutputV2(AcceptedV2ProductionBatchOutputV2):
    provenance: Literal["TEST_ONLY"] = "TEST_ONLY"
    production_eligible: Literal[False] = False


def frozen_maturity_context(arguments):
    packets = tuple(DecisionEvidencePacket.model_validate(p) for p in arguments["evidence_packets"])
    ownership = tuple(AcceptedV2EvidenceOwnership(
        ticker=p.ticker,
        core_ref_ids=tuple(sorted(r.ref_id for r in p.evidence if r.category.name != "PRICE_STRUCTURE")),
        timing_ref_ids=tuple(sorted(r.ref_id for r in p.evidence if r.category.name == "PRICE_STRUCTURE")),
        expectation_valuation=interaction_from_packet(p),
    ) for p in packets)
    raw = arguments["packet"]
    return ReviewedMaturityFixtureContext(
        packet_id=raw["packet_id"], claim_id=arguments["claim_id"], market=raw["market"],
        assessment_date=raw["assessment_date"], source_packet_sha256=canonical_sha256(raw),
        selected_subjects=tuple(p.ticker for p in packets), evidence_packets=packets,
        evidence_ownership=ownership, prior_accepted=(), prepared_at="2026-08-30T00:00:00+00:00",
    )


def build_reviewed_maturity_fixture(*, packet, claim_id, evidence_packets):
    """No arbitrary packet signing: exact backend recipe equality is required."""
    owner._process()
    packets = tuple(evidence_packets)
    for recipe_id, recipe in owner._recipes()["recipes"].items():
        if recipe.get("fixture_kind") != "STAGE2_MATURITY":
            continue
        arguments = recipe["arguments"]
        expected, _ = owner._expected(recipe_id, {})
        if (packet != arguments["packet"] or claim_id != arguments["claim_id"]
                or packets != expected.evidence_packets):
            continue
        seal = owner._issue_seal(expected, recipe_id, recipe, {})
        return expected.model_copy(update={"backend_seal": seal})
    raise ValueError("reviewed_maturity_unapproved_recipe")


def materialize_reviewed_stage2_fixture(
    context, raw_output, *, fundamental_cores=None, subjects=None,
    normalized_contract=STAGE2_MATURITY_PROVENANCE_MATERIALIZATION_CONTRACT,
):
    """Run native materialization semantics after a separate test-only admission."""
    from app.services.accepted_decision_v2_runtime_service import _materialize_v2_stage2_output
    from app.services.legacy_context_authority import verify_legacy_context

    if type(context) is not ReviewedMaturityFixtureContext:
        raise ValueError("reviewed_maturity_context_required")
    verify_legacy_context(context, fixture_consumer="STAGE2_MATERIALIZATION")
    result = _materialize_v2_stage2_output(
        context, raw_output, fundamental_cores=fundamental_cores,
        subjects=subjects, normalized_contract=normalized_contract,
    )
    cls = ReviewedMaturityOutputV2 if isinstance(result, AcceptedV2ProductionBatchOutputV2) else ReviewedMaturityOutput
    return cls.model_validate(result.model_dump(mode="json"))
