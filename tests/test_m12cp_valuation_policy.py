from __future__ import annotations

import json
from copy import deepcopy

import pytest

from scripts.m12co_entry_range_contract import MethodFamily
from scripts.m12cp_valuation_policy_contract import (
    Archetype,
    ValuationRegimeTier,
    build_component_inventory,
    build_subject_policy_matrix,
    depositary_basis_audit,
    derive_enterprise_value_input,
    generic_control_matrix,
    historical_projection_gap_analysis,
    method_intersection_analysis,
    scenario_method_source_coverage,
    select_policy_option,
    updated_policy_coverage,
)


def _candidate(
    method: MethodFamily,
    band: str,
    low: float,
    high: float,
    *,
    ticker: str = "GENERIC",
) -> dict[str, object]:
    return {
        "candidate_id": f"candidate:{ticker}:{method.value}:{band}",
        "ticker": ticker,
        "method_family": method.value,
        "quantile_band": band,
        "low": low,
        "high": high,
        "currency": "USD",
        "evidence_refs": [f"ref:{ticker}:{method.value}"],
    }


def _subject(
    *,
    pe: tuple[float, float] | None = (90, 110),
    pb: tuple[float, float] | None = (80, 100),
    band: str = "P50_P75",
    ticker: str = "GENERIC",
) -> dict[str, object]:
    candidates = []
    if pe:
        candidates.append(
            _candidate(
                MethodFamily.HISTORICAL_TRAILING_PE_QUANTILE,
                band,
                *pe,
                ticker=ticker,
            )
        )
    if pb:
        candidates.append(
            _candidate(
                MethodFamily.HISTORICAL_PB_QUANTILE,
                band,
                *pb,
                ticker=ticker,
            )
        )
    return {
        "market": "test",
        "ticker": ticker,
        "fundamental_candidates": candidates,
        "fundamental_candidate_count": len(candidates),
        "safe_method_families": sorted(
            {str(candidate["method_family"]) for candidate in candidates}
        ),
    }


def _select(
    subject: dict[str, object],
    archetype: Archetype,
    tier: ValuationRegimeTier = ValuationRegimeTier.BASE,
    **kwargs: object,
) -> dict[str, object]:
    return select_policy_option(
        subject=subject,
        archetype=archetype,
        valuation_regime_tier=tier,
        **kwargs,
    )


def test_durable_franchise_uses_pe_and_does_not_fallback_to_pb() -> None:
    resolved = _select(_subject(), Archetype.DURABLE_FRANCHISE)
    unresolved = _select(_subject(pe=None), Archetype.DURABLE_FRANCHISE)

    assert resolved["method_family"] == MethodFamily.HISTORICAL_TRAILING_PE_QUANTILE.value
    assert unresolved["status"] == "UNRESOLVED"
    assert unresolved["unresolved_reasons"] == ["DURABLE_PRIMARY_PE_UNAVAILABLE"]


def test_explicit_asset_relevance_can_make_pb_primary_without_automatic_fallback() -> None:
    result = _select(
        _subject(pe=None),
        Archetype.DURABLE_FRANCHISE,
        asset_relevance_proven=True,
    )

    assert result["status"] == "RESOLVED"
    assert result["method_family"] == MethodFamily.HISTORICAL_PB_QUANTILE.value
    assert result["selection_basis"] == "EXPLICIT_ASSET_RELEVANCE_PRIMARY_PB"


def test_structural_cyclical_uses_pb_and_rejects_raw_pe_only() -> None:
    resolved = _select(_subject(), Archetype.STRUCTURAL_CYCLICAL_LEADER)
    unresolved = _select(_subject(pb=None), Archetype.STRUCTURAL_CYCLICAL_LEADER)

    assert resolved["method_family"] == MethodFamily.HISTORICAL_PB_QUANTILE.value
    assert unresolved["status"] == "UNRESOLVED"


def test_profitable_growth_uses_pe_and_execution_growth_ignores_historical_methods() -> None:
    profitable = _select(_subject(), Archetype.PROFITABLE_PREMIUM_GROWTH)
    execution = _select(_subject(), Archetype.EXECUTION_DEPENDENT_GROWTH)

    assert profitable["method_family"] == MethodFamily.HISTORICAL_TRAILING_PE_QUANTILE.value
    assert execution["status"] == "UNRESOLVED"
    assert "EXECUTION_GROWTH_SCENARIO_METHOD_UNAVAILABLE" in execution["unresolved_reasons"]


def test_execution_growth_accepts_exactly_one_safe_scenario_method() -> None:
    scenario = {
        "candidate_id": "scenario:one",
        "ticker": "GENERIC",
        "method_family": MethodFamily.EV_SALES_SCENARIO.value,
        "quantile_band": "P50_P75",
        "low": 70,
        "high": 90,
        "currency": "USD",
        "evidence_refs": ["ref:ev", "ref:revenue"],
        "status": "SAFE",
    }
    resolved = _select(
        _subject(),
        Archetype.EXECUTION_DEPENDENT_GROWTH,
        scenario_candidates=[scenario],
    )
    ambiguous = _select(
        _subject(),
        Archetype.EXECUTION_DEPENDENT_GROWTH,
        scenario_candidates=[scenario, {**scenario, "candidate_id": "scenario:two"}],
    )

    assert resolved["status"] == "RESOLVED"
    assert resolved["source_candidate_ids"] == ["scenario:one"]
    assert ambiguous["unresolved_reasons"] == ["MULTIPLE_SCENARIO_METHODS_REQUIRE_POLICY_OWNER"]


def test_mature_value_intersection_is_exact_and_never_averaged() -> None:
    result = _select(_subject(pe=(90, 110), pb=(80, 100)), Archetype.MATURE_VALUE_DEFENSIVE)

    assert result["status"] == "RESOLVED"
    assert result["method_family"] == "METHOD_INTERSECTION"
    assert (result["low"], result["high"]) == (90.0, 100.0)
    assert result["methods_averaged"] is False
    assert len(result["source_candidate_ids"]) == 2


def test_mature_value_non_overlap_is_unresolved_and_single_method_remains_selectable() -> None:
    diverged = _select(_subject(pe=(120, 130), pb=(80, 100)), Archetype.MATURE_VALUE_DEFENSIVE)
    single = _select(_subject(pe=None), Archetype.MATURE_VALUE_DEFENSIVE)

    assert diverged["status"] == "UNRESOLVED"
    assert diverged["unresolved_reasons"] == ["METHODS_DIVERGE_REQUIRES_RESOLUTION"]
    assert single["status"] == "RESOLVED"
    assert single["method_family"] == MethodFamily.HISTORICAL_PB_QUANTILE.value


@pytest.mark.parametrize(
    ("tier", "band"),
    [
        (ValuationRegimeTier.CONSERVATIVE, "P25_P50"),
        (ValuationRegimeTier.BASE, "P50_P75"),
        (ValuationRegimeTier.PREMIUM, "P75_P90"),
    ],
)
def test_regime_tier_maps_to_exact_band(tier: ValuationRegimeTier, band: str) -> None:
    result = _select(
        _subject(pe=None, pb=(80, 100), band=band),
        Archetype.STRUCTURAL_CYCLICAL_LEADER,
        tier,
    )

    assert result["status"] == "RESOLVED"
    assert result["quantile_band"] == band


def test_unresolved_tier_never_selects_and_option_identity_is_deterministic() -> None:
    subject = _subject()
    first = _select(subject, Archetype.MATURE_VALUE_DEFENSIVE)
    second = _select(deepcopy(subject), Archetype.MATURE_VALUE_DEFENSIVE)
    unresolved = _select(
        subject,
        Archetype.MATURE_VALUE_DEFENSIVE,
        ValuationRegimeTier.UNRESOLVED,
    )

    assert first["option_id"] == second["option_id"]
    assert unresolved["status"] == "UNRESOLVED"
    assert unresolved["option_id"] is None


def test_cross_ticker_candidate_is_rejected() -> None:
    subject = _subject()
    subject["fundamental_candidates"][0]["ticker"] = "OTHER"

    with pytest.raises(ValueError, match="cross_ticker_source_candidate"):
        _select(subject, Archetype.MATURE_VALUE_DEFENSIVE)


def test_current_price_does_not_affect_policy_band() -> None:
    first = _subject()
    first["current_price"] = {"value": 10}
    second = deepcopy(first)
    second["current_price"] = {"value": 1000}

    left = _select(first, Archetype.MATURE_VALUE_DEFENSIVE)
    right = _select(second, Archetype.MATURE_VALUE_DEFENSIVE)

    assert (left["low"], left["high"], left["option_id"]) == (
        right["low"],
        right["high"],
        right["option_id"],
    )
    assert left["current_price_used_in_formula"] is False


def _canonical_row(ref_id: str, statement: dict[str, object], *, as_of: str) -> dict[str, object]:
    return {
        "ref_id": ref_id,
        "statement": json.dumps(statement),
        "as_of": as_of,
        "unit": None,
    }


def test_component_inventory_and_safe_ev_derivation_are_typed_and_same_basis() -> None:
    packet = {
        "ticker": "GENERIC",
        "assessment_date": "2026-09-17",
        "evidence": [
            _canonical_row(
                "canonical:valuation:market_cap",
                {
                    "market_cap": 1000,
                    "currency": "USD",
                    "basis": "current_security",
                },
                as_of="2026-09-16",
            ),
            _canonical_row(
                "canonical:financial:debt",
                {"total_debt": 300, "currency": "USD", "basis": "current_security"},
                as_of="2026-09-16",
            ),
            _canonical_row(
                "canonical:financial:cash",
                {
                    "cash_and_equivalents": 200,
                    "currency": "USD",
                    "basis": "current_security",
                },
                as_of="2026-09-16",
            ),
            _canonical_row(
                "canonical:earnings:period",
                {
                    "operating_income": {"value": 55, "currency": "USD"},
                    "period": "2026-06-30",
                    "period_type": "H1",
                    "basis": "issuer",
                },
                as_of="2026-09-16",
            ),
            {
                "ref_id": "decision-evidence:prose",
                "statement": "market cap 999999 and cash 888888",
            },
        ],
    }
    inventory = build_component_inventory(market="test", packet=packet)
    enterprise_value = derive_enterprise_value_input(inventory)

    assert inventory["components"]["current_market_cap"]["fact_count"] == 1
    assert inventory["components"]["operating_income"]["fact_count"] == 1
    assert enterprise_value["status"] == "SAFE_DERIVED_INPUT"
    assert enterprise_value["value"] == 1100.0
    assert set(enterprise_value["source_refs"]) == {
        "canonical:valuation:market_cap",
        "canonical:financial:debt",
        "canonical:financial:cash",
    }


def test_ev_derivation_fails_closed_on_currency_or_basis_mismatch() -> None:
    packet = {
        "ticker": "GENERIC",
        "evidence": [
            _canonical_row(
                "canonical:market-cap",
                {"market_cap": 1000, "currency": "USD", "basis": "issuer"},
                as_of="2026-09-16",
            ),
            _canonical_row(
                "canonical:debt",
                {"total_debt": 300, "currency": "EUR", "basis": "issuer"},
                as_of="2026-09-16",
            ),
            _canonical_row(
                "canonical:cash",
                {"cash_and_equivalents": 200, "currency": "USD", "basis": "issuer"},
                as_of="2026-09-16",
            ),
        ],
    }

    result = derive_enterprise_value_input(build_component_inventory(market="test", packet=packet))

    assert result["status"] == "ENTERPRISE_VALUE_COMPONENTS_INCOMPLETE"
    assert "CURRENCY_INCOMPATIBLE" in result["missing_or_ambiguous_components"]


def test_scenario_methods_report_exact_source_gaps_without_fabrication() -> None:
    inventory = build_component_inventory(
        market="test", packet={"ticker": "GENERIC", "evidence": []}
    )
    enterprise_value = derive_enterprise_value_input(inventory)
    result = scenario_method_source_coverage(inventory, enterprise_value)

    assert result["scenario_ready"] is False
    assert all(row["status"] == "NOT_READY" for row in result["methods"])
    assert all(row["forecast_fabricated"] is False for row in result["methods"])
    ev_sales = next(row for row in result["methods"] if row["method_family"] == "EV_SALES_SCENARIO")
    assert "SAFE_EV" in ev_sales["minimal_source_contract_gaps"]
    assert "CANONICAL_FUTURE_REVENUE_SCENARIO" in ev_sales["minimal_source_contract_gaps"]


def test_depositary_basis_requires_complete_verified_conversion_contract() -> None:
    resolved_packet = {
        "ticker": "ADR",
        "evidence": [
            _canonical_row(
                "canonical:security_identity:current",
                {
                    "selected_security_type": "depositary_receipt",
                    "depositary_evidence_present": True,
                    "depositary_ratio": 0.2,
                    "depositary_ratio_direction": "ordinary_shares_per_adr",
                    "depositary_ratio_source": "official-filing",
                    "ordinary_share_identifier": "ORDINARY",
                    "identity_state": "verified_depositary",
                },
                as_of="2026-09-16",
            ),
            _canonical_row(
                "canonical:security_basis:current",
                {
                    "security_identity_state": "verified_depositary",
                    "book_value_currency": "TWD",
                    "price_currency": "USD",
                    "earnings_per_share_security_basis": "current_security",
                },
                as_of="2026-09-16",
            ),
        ],
    }
    unresolved_packet = {
        "ticker": "TRUNCATED_ADR",
        "evidence": [
            {
                "ref_id": "canonical:security_identity:current",
                "statement": '{"selected_security_type": "depositary_receipt", "depositary_ratio": 0.1, "x": "tr…',
            }
        ],
    }

    resolved = depositary_basis_audit(resolved_packet)
    unresolved = depositary_basis_audit(unresolved_packet)

    assert resolved["status"] == "RESOLVED"
    assert resolved["conversion_contract_materialized"] is True
    assert unresolved["status"] == "DEPOSITARY_SECURITY_BASIS_UNRESOLVED"
    assert "complete_parseable_canonical_identity_record" in unresolved["missing_fields"]


@pytest.mark.parametrize(
    ("reasons", "available", "expected"),
    [
        (
            ["REF_NOT_OWNED:canonical:valuation:historical_pb"],
            [
                "canonical:valuation:book_quality",
                "canonical:valuation:book_value",
                "canonical:valuation:historical_pb",
            ],
            "B_SOURCE_EXISTS_NOT_PROJECTED",
        ),
        (
            ["BOOK_SHARE_BASIS_NOT_CURRENT_SECURITY"],
            ["canonical:valuation:book_quality"],
            "C_SECURITY_SHARE_OR_CURRENCY_BASIS_UNRESOLVED",
        ),
        (
            ["MISSING_HISTORICAL_PB_STATISTICS"],
            ["canonical:valuation:book_quality"],
            "A_DATA_OR_SAFE_SEMANTIC_UNAVAILABLE",
        ),
    ],
)
def test_historical_projection_gap_categories(
    reasons: list[str], available: list[str], expected: str
) -> None:
    subject = {
        "ticker": "GENERIC",
        "market": "test",
        "available_valuation_facts": available,
        "method_feasibility": [
            {
                "method_family": MethodFamily.HISTORICAL_PB_QUANTILE.value,
                "arithmetic_feasible": False,
                "required_refs": [
                    "canonical:valuation:book_quality",
                    "canonical:valuation:book_value",
                    "canonical:valuation:historical_pb",
                ],
                "rejected_reasons": reasons,
            }
        ],
    }

    result = historical_projection_gap_analysis(subject)

    assert result["methods"][0]["category"] == expected
    assert result["methods"][0]["safe_shadow_projection_performed"] is False


def test_policy_matrix_coverage_and_intersection_summary() -> None:
    first = _subject(ticker="A")
    second = _subject(pe=None, pb=None, ticker="B")
    matrices = [build_subject_policy_matrix(first), build_subject_policy_matrix(second)]
    coverage = updated_policy_coverage([first, second], matrices)
    intersections = method_intersection_analysis(matrices)

    assert coverage["safe_arithmetic_subject_count"] == 1
    assert coverage["policy_selectable_subject_count"] == 1
    assert coverage["no_safe_policy_method_subject_count"] == 1
    assert coverage["mature_value_intersection_subject_count"] == 1
    assert intersections["intersection_count"] == 1
    assert intersections["methods_averaged_count"] == 0


def test_generic_control_matrix_closes_all_required_controls() -> None:
    result = generic_control_matrix()

    assert result["status"] == "PASS"
    assert result["failed"] == 0
    assert result["passed"] >= 13
