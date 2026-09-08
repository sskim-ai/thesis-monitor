from __future__ import annotations

from pathlib import Path

from scripts import source_domain_enrichment_design_review as review


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_all_six_domains_have_complete_safe_contracts() -> None:
    rows = review.domain_contracts()

    assert tuple(row["domain"] for row in rows) == review.DOMAINS
    assert len(rows) == 6
    for row in rows:
        assert row["safe_derivations"]
        assert row["forbidden_derivations"]
        assert row["comparability_requirements"]
        assert row["required_validation_tests"]
        assert row["missing_data_behavior"]
        assert row["source_sufficiency_impact"] in {
            "NO_SOURCE_SUFFICIENCY_IMPACT",
            "PREFERRED_WHEN_AVAILABLE",
            "SECTOR_CONDITIONAL_REQUIRED",
            "REQUIRED_ONLY_FOR_SPECIFIC_CLAIM",
            "FUTURE_DESIGN_REQUIRED",
        }
        assert row["schema_change_required"] is True


def test_market_support_matrix_is_dual_market_and_selective() -> None:
    rows = review.market_support_matrix(review.domain_contracts())
    us = review._market_audit("us", rows)
    kr = review._market_audit("kr", rows)

    assert len(rows) == 12
    assert {row["market"] for row in rows} == {"us", "kr"}
    assert all(row["support_status"] in review.SUPPORT_STATUSES for row in rows)
    assert all(row["universal_issuer_coverage_claimed"] is False for row in rows)
    assert (us["supported_domain_count"], us["partial_domain_count"]) == (2, 4)
    assert (kr["supported_domain_count"], kr["partial_domain_count"]) == (1, 5)
    assert us["unsupported_domain_count"] == 0
    assert kr["unsupported_domain_count"] == 0


def test_schema_review_requires_additive_typed_financial_context() -> None:
    result = review.schema_compatibility(review.domain_contracts())
    proposal = result["bounded_schema_proposal"]

    assert result["schema_sufficient_domain_count"] == 0
    assert result["schema_extension_required_domain_count"] == 6
    assert all(
        row["classification"] == "SCHEMA_EXTENSION_REQUIRED"
        for row in result["rows"]
    )
    assert proposal["field"] == "financial_context"
    assert proposal["production_activation"] is False
    assert set(proposal["shape"]) >= {
        "metric",
        "evidence_status",
        "currency",
        "period",
        "entity_scope",
        "statement_basis",
        "comparison",
        "derivation",
        "limitations",
    }


def test_sector_matrix_has_required_families_without_universal_gate() -> None:
    rows = review.sector_matrix()
    sectors = {row["sector_family"] for row in rows}

    assert len(rows) == 13
    assert {
        "standard_operating_company",
        "semiconductor_memory",
        "automotive",
        "bank",
        "insurance_reinsurance",
        "shipping_transport",
        "holding_company",
        "consumer",
        "epc_construction",
        "saas_recurring_revenue",
        "cloud_platform",
        "biotech",
        "preprofit_robotaxi_like",
    } == sectors
    assert all(len(row["domain_applicability"]) == 6 for row in rows)
    assert all(row["generic_domain_required_for_all_issuers"] is False for row in rows)


def test_offline_source_inventory_and_semantics_are_observable() -> None:
    inventory = review.source_inventory(REPO_ROOT)
    semantics = review.semantics_audit(REPO_ROOT)

    assert inventory["status"] == "PASS"
    assert inventory["verified_count"] == len(inventory["rows"])
    assert inventory["provider_calls"] == 0
    assert semantics["status"] == "PASS"
    assert semantics["pass_count"] == semantics["check_count"]
    assert semantics["checks"]["unsafe_total_liabilities_debt_mapping_detected"]


def test_representative_fixture_manifest_uses_only_preserved_evidence() -> None:
    manifest = review.representative_fixtures(REPO_ROOT)
    by_case = {row["case"]: row for row in manifest["rows"]}

    assert manifest["status"] == "PASS"
    assert manifest["fixture_count"] == manifest["pass_count"] == 7
    assert manifest["model_calls"] == 0
    assert manifest["provider_calls"] == 0
    assert by_case["profitable_strong_cash_conversion"]["evidence"][
        "lineage_complete"
    ]
    assert (
        by_case["high_leverage_weak_liquidity"]["result"]
        == "BLOCKED_UNSAFE_DEBT_SCOPE"
    )
    assert (
        by_case["generic_domain_not_applicable"]["generic_fcf_status"]
        == "NOT_APPLICABLE"
    )


def test_direct_derived_and_directional_designs_do_not_add_scores() -> None:
    derived = review.direct_derived_contract(review.domain_contracts())
    materiality = review.materiality_contract()
    specificity = review.directional_specificity_contract()

    assert derived["derived_metric_count"] > 0
    assert derived["forbidden_derivation_count"] > 0
    assert materiality["fixed_score"] is False
    assert specificity["checklist_or_fixed_score"] is False
    assert specificity["production_prompt_modified"] is False


def test_candidate_order_freezes_schema_before_prompt_and_holdout() -> None:
    packages = review.candidate_packages()
    order = review.package_order(packages)

    assert order[0] == "B_PACKET_FINANCIAL_CONTEXT_EXTENSION"
    assert order[1] == "A_EXISTING_CANONICAL_DOMAIN_ADAPTERS"
    assert order.index("C_DIRECTIONAL_SPECIFICITY_CONTRACT") > order.index(
        "A_ADDITIONAL_SOURCE_MAPPING_SUBPACKAGES"
    )
    assert packages[-1]["scope"].startswith("separate decision")


def test_m4_side_effect_firewall_is_zero() -> None:
    assert review.SIDE_EFFECT_COUNTS
    assert set(review.SIDE_EFFECT_COUNTS.values()) == {0}


def test_report_manifest_has_38_numbered_artifacts() -> None:
    assert len(review.REPORT_NAMES) == 38
    assert review.REPORT_NAMES[0].startswith("01-")
    assert review.REPORT_NAMES[-1].startswith("38-")
    assert len(set(review.REPORT_NAMES)) == 38
