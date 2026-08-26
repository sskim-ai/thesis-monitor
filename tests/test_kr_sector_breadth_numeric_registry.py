from app.services.numeric_semantic_registry import (
    build_numeric_registry,
    numeric_registry_coverage,
)
from app.services.market_cross_section_service import MarketSectorFact
from app.services.market_intelligence_service import (
    market_cross_section_sector_fact_id,
)


def _sector_fact(**overrides: object) -> dict[str, object]:
    fields: dict[str, object] = {
        "sector": "보험",
        "taxonomy": "kiwoom-sector-index-v1",
        "metric_role": "actual_sector_breadth",
        "sector_code": "021",
        "market_scope": "KOSPI",
        "listed_count": 12,
        "advance_count": 9,
        "decline_count": 2,
        "unchanged_count": 1,
        "limit_up_count": 0,
        "limit_down_count": 0,
        "source_ref": "kiwoom:ka20003:KOSPI:021:2026-08-26",
    }
    fields.update(overrides)
    return {
        "fact_id": "market:cross-section:sector:kiwoom-sector-index-v1:보험",
        "fact_type": "market_cross_section_sector",
        "as_of_date": "2026-08-26",
        "fields": fields,
        "source": "KIWOOM_REST",
    }


def _by_path(fact: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        str(item["field_path"]): item
        for item in build_numeric_registry([fact])
    }


def test_sector_breadth_supported_counts_have_exact_semantics() -> None:
    rows = _by_path(_sector_fact())
    expected = {
        "fields.listed_count": "sector_listed_issue_count",
        "fields.advance_count": "sector_advance_count",
        "fields.decline_count": "sector_decline_count",
        "fields.unchanged_count": "sector_unchanged_count",
    }
    for path, semantic_type in expected.items():
        row = rows[path]
        assert row["semantic_type"] == semantic_type
        assert row["unit"] == "count"
        assert row["registered"] is True
        assert row["prose_allowed"] is True
        assert row["registry_class"] == "REGISTERED_PROSE_ELIGIBLE"
        assert row["owner"] == "market_context"
        assert row["market_scope"] == "KOSPI"
        assert row["sector_scope"] == "보험"
        assert row["session_basis"] == "same_session_cross_section"
        assert row["source_owner"] == "kiwoom"
        assert row["comparison_eligible"] is False
        assert row["allowed_sections"] == ["market_context"]


def test_sector_limit_counts_are_registered_audit_only() -> None:
    rows = _by_path(_sector_fact())
    for path, semantic_type in {
        "fields.limit_up_count": "sector_limit_up_count_audit",
        "fields.limit_down_count": "sector_limit_down_count_audit",
    }.items():
        row = rows[path]
        assert row["semantic_type"] == semantic_type
        assert row["registered"] is True
        assert row["prose_allowed"] is False
        assert row["registry_class"] == "REGISTERED_AUDIT_ONLY"
        assert row["audit_only"] is True
        assert row["allowed_sections"] == []


def test_sector_registry_has_one_owner_per_exact_supported_path() -> None:
    registry = build_numeric_registry([_sector_fact()])
    paths = [
        item["field_path"]
        for item in registry
        if str(item["field_path"]).endswith("_count")
    ]
    assert len(paths) == len(set(paths)) == 6


def test_unknown_future_sector_count_remains_fail_closed() -> None:
    registry = build_numeric_registry(
        [_sector_fact(experimental_component_count=7)]
    )
    unknown = next(
        item
        for item in registry
        if item["field_path"] == "fields.experimental_component_count"
    )
    assert unknown["registered"] is False
    assert unknown["prose_allowed"] is False
    assert unknown["registry_class"] == "UNSUPPORTED_BLOCKING"
    assert numeric_registry_coverage([registry])["ready"] is False


def test_same_sector_name_on_two_markets_has_distinct_fact_identity() -> None:
    kospi = MarketSectorFact(
        sector="금속",
        taxonomy="kiwoom-sector-index-v1",
        metric_role="actual_sector_breadth",
        sector_code="011",
        market_scope="KOSPI",
    )
    kosdaq = MarketSectorFact(
        sector="금속",
        taxonomy="kiwoom-sector-index-v1",
        metric_role="actual_sector_breadth",
        sector_code="122",
        market_scope="KOSDAQ",
    )

    assert market_cross_section_sector_fact_id(kospi) != (
        market_cross_section_sector_fact_id(kosdaq)
    )
    assert market_cross_section_sector_fact_id(kospi).endswith("KOSPI:011")
    assert market_cross_section_sector_fact_id(kosdaq).endswith("KOSDAQ:122")
