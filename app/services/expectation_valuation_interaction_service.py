from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from enum import StrEnum

from pydantic import Field, model_validator

from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    EvidenceCategory,
    FrozenModel,
)


CONTRACT_VERSION = "expectation-valuation-interaction-v1"


class ExpectationValuationOverlap(StrEnum):
    INDEPENDENT = "INDEPENDENT"
    PARTIALLY_OVERLAPPING = "PARTIALLY_OVERLAPPING"
    VALUATION_DERIVED_EXPECTATION_ONLY = "VALUATION_DERIVED_EXPECTATION_ONLY"
    UNKNOWN = "UNKNOWN"


class ExpectationValuationLineage(FrozenModel):
    expectation_refs: tuple[str, ...] = Field(min_length=1)
    valuation_refs: tuple[str, ...] = Field(min_length=1)
    independent_expectation_basis_refs: tuple[str, ...] = ()
    shared_underlying_refs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_lineage(self) -> ExpectationValuationLineage:
        expectation = set(self.expectation_refs)
        if not set(self.independent_expectation_basis_refs).issubset(expectation):
            raise ValueError("independent_expectation_basis_outside_expectation_refs")
        if len(expectation) != len(self.expectation_refs):
            raise ValueError("duplicate_expectation_ref")
        if len(set(self.valuation_refs)) != len(self.valuation_refs):
            raise ValueError("duplicate_valuation_ref")
        if len(set(self.shared_underlying_refs)) != len(self.shared_underlying_refs):
            raise ValueError("duplicate_shared_underlying_ref")
        return self


class ExpectationValuationInteraction(FrozenModel):
    contract: str = CONTRACT_VERSION
    ticker: str
    classification: ExpectationValuationOverlap
    expectation_refs: tuple[str, ...]
    valuation_refs: tuple[str, ...]
    independent_expectation_basis_refs: tuple[str, ...]
    shared_underlying_refs: tuple[str, ...]
    reason: str


def classify_expectation_valuation_interaction(
    *,
    ticker: str,
    lineage: ExpectationValuationLineage,
) -> ExpectationValuationInteraction:
    independent = set(lineage.independent_expectation_basis_refs)
    shared = set(lineage.shared_underlying_refs)
    if independent and shared:
        classification = ExpectationValuationOverlap.PARTIALLY_OVERLAPPING
        reason = "INDEPENDENT_EXPECTATION_AND_SHARED_VALUATION_LINEAGE"
    elif shared:
        classification = ExpectationValuationOverlap.VALUATION_DERIVED_EXPECTATION_ONLY
        reason = "EXPECTATION_SUPPORTED_ONLY_BY_SHARED_VALUATION_LINEAGE"
    elif independent:
        classification = ExpectationValuationOverlap.INDEPENDENT
        reason = "INDEPENDENT_EXPECTATION_LINEAGE"
    else:
        classification = ExpectationValuationOverlap.UNKNOWN
        reason = "EXPECTATION_VALUATION_LINEAGE_UNRESOLVED"
    return ExpectationValuationInteraction(
        ticker=ticker,
        classification=classification,
        expectation_refs=lineage.expectation_refs,
        valuation_refs=lineage.valuation_refs,
        independent_expectation_basis_refs=lineage.independent_expectation_basis_refs,
        shared_underlying_refs=lineage.shared_underlying_refs,
        reason=reason,
    )


def _structured_expectation_is_independent(statement: str) -> bool:
    """Recognize explicit stored expectation content, not prose sentiment or a multiple."""

    try:
        value = json.loads(statement)
    except (TypeError, json.JSONDecodeError):
        return False
    if not isinstance(value, Mapping):
        return False
    return any(
        isinstance(value.get(key), Sequence)
        and not isinstance(value.get(key), (str, bytes))
        and bool(value.get(key))
        for key in ("priced_in", "upside_surprises", "downside_surprises")
    )


def interaction_from_packet(
    packet: DecisionEvidencePacket,
) -> ExpectationValuationInteraction:
    expectations = tuple(
        row for row in packet.evidence if row.category == EvidenceCategory.EXPECTATIONS
    )
    valuations = tuple(
        row for row in packet.evidence if row.category == EvidenceCategory.VALUATION
    )
    expectation_refs = tuple(row.ref_id for row in expectations)
    valuation_refs = tuple(row.ref_id for row in valuations)
    if not expectation_refs or not valuation_refs:
        return ExpectationValuationInteraction(
            ticker=packet.ticker,
            classification=ExpectationValuationOverlap.UNKNOWN,
            expectation_refs=expectation_refs,
            valuation_refs=valuation_refs,
            independent_expectation_basis_refs=(),
            shared_underlying_refs=(),
            reason="EXPECTATION_OR_VALUATION_EVIDENCE_MISSING",
        )

    valuation_sources = {row.source_ref for row in valuations}
    shared = tuple(
        row.ref_id for row in expectations if row.source_ref in valuation_sources
    )
    independent = tuple(
        row.ref_id
        for row in expectations
        if row.ref_id not in shared
        and row.source_ref == "stock.thesis.market_expectations"
        and _structured_expectation_is_independent(row.statement)
    )
    return classify_expectation_valuation_interaction(
        ticker=packet.ticker,
        lineage=ExpectationValuationLineage(
            expectation_refs=expectation_refs,
            valuation_refs=valuation_refs,
            independent_expectation_basis_refs=independent,
            shared_underlying_refs=shared,
        ),
    )


def duplicate_directional_anchor_errors(
    *,
    interaction: ExpectationValuationInteraction,
    driver_ref_groups: Sequence[Sequence[str]],
) -> tuple[str, ...]:
    if interaction.classification == ExpectationValuationOverlap.INDEPENDENT:
        return ()
    expectation_refs = set(interaction.expectation_refs)
    valuation_refs = set(interaction.valuation_refs)
    expectation_groups = 0
    valuation_groups = 0
    for refs in driver_ref_groups:
        selected = set(refs)
        expectation_groups += bool(selected & expectation_refs)
        valuation_groups += bool(selected & valuation_refs)
    errors: list[str] = []
    if interaction.classification in {
        ExpectationValuationOverlap.VALUATION_DERIVED_EXPECTATION_ONLY,
        ExpectationValuationOverlap.UNKNOWN,
    } and expectation_groups:
        errors.append("nonindependent_expectation_used_as_directional_anchor")
    if interaction.classification in {
        ExpectationValuationOverlap.PARTIALLY_OVERLAPPING,
        ExpectationValuationOverlap.VALUATION_DERIVED_EXPECTATION_ONLY,
    } and expectation_groups and valuation_groups:
        errors.append("expectation_valuation_shared_signal_used_as_duplicate_anchor")
    return tuple(errors)
