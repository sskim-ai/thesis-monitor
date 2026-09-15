from __future__ import annotations

from app.services.expectation_valuation_interaction_service import (
    ExpectationValuationLineage,
    ExpectationValuationOverlap,
    classify_expectation_valuation_interaction,
    duplicate_directional_anchor_errors,
)


def test_ev01_valuation_derived_expectation_is_not_a_second_anchor() -> None:
    interaction = classify_expectation_valuation_interaction(
        ticker="EV01",
        lineage=ExpectationValuationLineage(
            expectation_refs=("expectation:high-pbr",),
            valuation_refs=("valuation:high-pbr",),
            shared_underlying_refs=("expectation:high-pbr",),
        ),
    )

    errors = duplicate_directional_anchor_errors(
        interaction=interaction,
        driver_ref_groups=(("expectation:high-pbr",), ("valuation:high-pbr",)),
    )

    assert interaction.classification == ExpectationValuationOverlap.VALUATION_DERIVED_EXPECTATION_ONLY
    assert "nonindependent_expectation_used_as_directional_anchor" in errors
    assert "expectation_valuation_shared_signal_used_as_duplicate_anchor" in errors


def test_ev02_independent_growth_expectation_and_valuation_can_both_matter() -> None:
    interaction = classify_expectation_valuation_interaction(
        ticker="EV02",
        lineage=ExpectationValuationLineage(
            expectation_refs=("expectation:guidance-growth",),
            valuation_refs=("valuation:historical-percentile",),
            independent_expectation_basis_refs=("expectation:guidance-growth",),
        ),
    )

    errors = duplicate_directional_anchor_errors(
        interaction=interaction,
        driver_ref_groups=(
            ("expectation:guidance-growth",),
            ("valuation:historical-percentile",),
        ),
    )

    assert interaction.classification == ExpectationValuationOverlap.INDEPENDENT
    assert errors == ()


def test_ev03_high_expectation_and_discounted_valuation_do_not_resolve_direction() -> None:
    interaction = classify_expectation_valuation_interaction(
        ticker="GOOGL-LIKE",
        lineage=ExpectationValuationLineage(
            expectation_refs=("expectation:cloud-growth",),
            valuation_refs=("valuation:historical-discount",),
            independent_expectation_basis_refs=("expectation:cloud-growth",),
        ),
    )

    assert interaction.classification == ExpectationValuationOverlap.INDEPENDENT
    assert "decision" not in interaction.model_dump(mode="json")
