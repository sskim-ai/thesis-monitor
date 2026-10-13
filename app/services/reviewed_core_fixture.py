"""Three finite schema/semantic fixtures; not an accepted production context."""
from typing import Literal

from app.services.accepted_decision_v2_runtime_service import (
    AcceptedV2EvidenceOwnership,
    AcceptedV2ProductionContext,
    canonical_sha256,
    interaction_from_packet,
)
from app.services.cross_market_decision_engine_service import DecisionEvidencePacket
from app.services.reviewed_fixture_authority import ReviewedFixtureSeal


class ReviewedCoreFixtureContext(AcceptedV2ProductionContext):
    provenance: Literal["TEST_ONLY"] = "TEST_ONLY"
    backend_seal: ReviewedFixtureSeal | None = None


def frozen_core_context(arguments):
    packets = tuple(DecisionEvidencePacket.model_validate(p) for p in arguments["evidence_packets"])
    ownership = []
    for packet in packets:
        if any(ref.category.name not in {"THESIS", "PRICE_STRUCTURE"} for ref in packet.evidence):
            raise ValueError("reviewed_core_fixture_category_drift")
        core_refs = tuple(sorted(ref.ref_id for ref in packet.evidence if ref.category.name == "THESIS"))
        ownership.append(AcceptedV2EvidenceOwnership(ticker=packet.ticker,
            core_ref_ids=core_refs,
            timing_ref_ids=tuple(sorted(ref.ref_id for ref in packet.evidence if ref.category.name == "PRICE_STRUCTURE")),
            expectation_valuation=interaction_from_packet(packet.model_copy(update={"evidence":tuple(ref for ref in packet.evidence if ref.ref_id in core_refs)}))))
    raw = arguments["packet"]
    return ReviewedCoreFixtureContext(packet_id=raw["packet_id"],claim_id=arguments["claim_id"],
        market=raw["market"],assessment_date=raw["assessment_date"],source_packet_sha256=canonical_sha256(raw),
        selected_subjects=tuple(packet.ticker for packet in packets),evidence_packets=packets,
        evidence_ownership=tuple(ownership),prior_accepted=(),prepared_at="2026-09-15T00:00:00+00:00")
