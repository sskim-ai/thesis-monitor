from datetime import UTC, date, datetime

import pytest

from app.services.market_context_adapter_service import (
    KrMarketContextAdapter,
    UsMarketContextAdapter,
    event_time_eligible,
    market_context_adapter,
)
from app.services.market_cross_section_service import (
    MarketBreadth,
    MarketCrossSection,
    MarketCrossSectionQuality,
    MarketFlowFact,
)
from app.services.market_research_seed_adapter_service import (
    audit_production_research_connector,
    research_seed_adapter,
)


ASSESSMENT = date(2026, 8, 25)
CUTOFF = datetime(2026, 8, 25, 8, 10, tzinfo=UTC)


def _fact(
    fact_id: str,
    fact_type: str,
    fields: dict[str, object],
    *,
    as_of: str = "2026-08-24",
) -> dict[str, object]:
    return {
        "fact_id": fact_id,
        "fact_type": fact_type,
        "as_of_date": as_of,
        "source": "fixture",
        "fields": fields,
    }


def test_missing_fields_remain_unknown_without_default_zero() -> None:
    value = KrMarketContextAdapter().normalize(
        assessment_date=ASSESSMENT,
        as_of=CUTOFF,
        cutoff=CUTOFF,
        fact_catalog=[],
        coverage={
            "breadth": {
                "status": "unavailable",
                "reason": "not_provided_by_backend",
            }
        },
        provider_publication_state="MARKET_COMPLETED_PROVIDER_PENDING",
    )

    assert value.indices == []
    assert value.breadth.availability == "UNKNOWN"
    assert value.breadth.advancers is None
    assert value.size_context == []
    assert value.concentration == []
    assert value.market_flows == []
    assert value.session_context.provider_publication_state == (
        "MARKET_COMPLETED_PROVIDER_PENDING"
    )
    assert "breadth_unavailable" in value.data_gaps


def test_missing_and_future_fact_dates_are_suppressed() -> None:
    missing_date = _fact(
        "market:index:SPY:missing-date",
        "market_index",
        {"series_code": "SPY", "return_pct": 1.0},
        as_of="",
    )
    future = _fact(
        "market:index:QQQ:future",
        "market_index",
        {"series_code": "QQQ", "return_pct": 2.0},
        as_of="2026-08-26",
    )

    value = UsMarketContextAdapter().normalize(
        assessment_date=ASSESSMENT,
        as_of=CUTOFF,
        cutoff=CUTOFF,
        fact_catalog=[missing_date, future],
    )

    assert value.indices == []
    assert "fact_date_missing:market:index:SPY:missing-date" in value.data_gaps
    assert "future_fact_suppressed:market:index:QQQ:future" in value.data_gaps


def test_fact_without_canonical_identity_is_suppressed() -> None:
    fact = _fact(
        "",
        "market_index",
        {"series_code": "SPY", "return_pct": 1.0},
    )

    value = UsMarketContextAdapter().normalize(
        assessment_date=ASSESSMENT,
        as_of=CUTOFF,
        cutoff=CUTOFF,
        fact_catalog=[fact],
    )

    assert value.indices == []
    assert "fact_id_missing" in value.data_gaps


def test_us_adapter_normalizes_indices_sector_and_provenance_relations() -> None:
    facts = [
        _fact(
            "market:index:SPY",
            "market_index",
            {"series_code": "SPY", "label": "S&P500", "return_pct": -0.3},
        ),
        _fact(
            "market:index:QQQ",
            "market_index",
            {"series_code": "QQQ", "label": "Nasdaq", "return_pct": -1.0},
        ),
        _fact(
            "market:sector:SOXX",
            "market_sector",
            {"series_code": "SOXX", "label": "Semiconductor", "return_pct": -2.7},
        ),
        _fact(
            "market:relative:QQQ:SPY",
            "market_growth_relative",
            {
                "source_fact_ids": ["market:index:QQQ", "market:index:SPY"],
                "relative_return_pct": -0.7,
            },
        ),
    ]

    value = UsMarketContextAdapter().normalize(
        assessment_date=ASSESSMENT,
        as_of=CUTOFF,
        cutoff=CUTOFF,
        fact_catalog=facts,
    )

    assert [item.symbol for item in value.indices] == ["SPY", "QQQ"]
    assert value.session_date == date(2026, 8, 24)
    assert value.sectors[0].basis == "sector_price_proxy"
    relation = value.deterministic_relations[0]
    assert relation.formula == "subject_return_pct - benchmark_return_pct"
    assert relation.input_refs == ["market:index:QQQ", "market:index:SPY"]
    assert relation.result == -0.7
    assert relation.scope == "US"
    assert relation.as_of_date == date(2026, 8, 24)
    assert value.market_flows == []
    assert "us_participant_flow_not_supported" in value.data_gaps


def test_relative_relation_requires_inputs_same_date_and_exact_arithmetic() -> None:
    facts = [
        _fact(
            "market:index:SPY",
            "market_index",
            {"series_code": "SPY", "return_pct": -0.3},
        ),
        _fact(
            "market:index:QQQ",
            "market_index",
            {"series_code": "QQQ", "return_pct": -1.0},
        ),
        _fact(
            "market:relative:QQQ:SPY",
            "market_growth_relative",
            {
                "source_fact_ids": ["market:index:QQQ", "market:index:SPY"],
                "relative_return_pct": 99.0,
            },
        ),
    ]

    value = UsMarketContextAdapter().normalize(
        assessment_date=ASSESSMENT,
        as_of=CUTOFF,
        cutoff=CUTOFF,
        fact_catalog=facts,
    )

    assert value.deterministic_relations == []


def test_kr_adapter_normalizes_local_indices_breadth_and_monetary_flow() -> None:
    facts = [
        _fact(
            "market:cross-section:index:KOSPI",
            "market_cross_section_index",
            {"symbol": "KOSPI", "label": "KOSPI", "close": 3200, "return_pct": 1.2},
            as_of="2026-08-25",
        ),
        _fact(
            "market:cross-section:index:KOSDAQ",
            "market_cross_section_index",
            {
                "symbol": "KOSDAQ",
                "label": "KOSDAQ",
                "close": 900,
                "return_pct": -0.4,
            },
            as_of="2026-08-25",
        ),
        _fact(
            "market:breadth:kr:counts",
            "market_breadth_counts",
            {"advance_count": 600, "decline_count": 300, "unchanged_count": 100},
            as_of="2026-08-25",
        ),
        _fact(
            "market:flow:kr:foreign",
            "market_flow",
            {"actor": "foreign", "net_buy_amount": 125_000_000_000, "currency": "KRW"},
            as_of="2026-08-25",
        ),
    ]

    value = KrMarketContextAdapter().normalize(
        assessment_date=ASSESSMENT,
        as_of=CUTOFF,
        cutoff=CUTOFF,
        fact_catalog=facts,
        provider_publication_state="PROVIDER_COMPLETE",
    )

    assert [item.symbol for item in value.indices] == ["KOSPI", "KOSDAQ"]
    assert value.breadth.eligible_count == 1000
    assert value.breadth.breadth_ratio == pytest.approx(2 / 3)
    assert value.deterministic_relations[0].input_refs == [
        "market:breadth:kr:counts"
    ]
    assert value.market_flows[0].unit == "KRW"
    assert value.market_flows[0].scope == "KR_MARKET"


def test_kr_market_flow_rejects_incompatible_unit() -> None:
    fact = _fact(
        "market:flow:kr:foreign",
        "market_flow",
        {"actor": "foreign", "net_buy_amount": 12, "currency": "shares"},
    )

    with pytest.raises(ValueError, match="KRW monetary units"):
        KrMarketContextAdapter().normalize(
            assessment_date=ASSESSMENT,
            as_of=CUTOFF,
            cutoff=CUTOFF,
            fact_catalog=[fact],
        )


def test_us_adapter_rejects_invented_participant_flow() -> None:
    fact = _fact(
        "market:flow:us:foreign",
        "market_flow",
        {"actor": "foreign", "net_buy_amount": 12, "currency": "USD"},
    )

    with pytest.raises(ValueError, match="unsupported"):
        UsMarketContextAdapter().normalize(
            assessment_date=ASSESSMENT,
            as_of=CUTOFF,
            cutoff=CUTOFF,
            fact_catalog=[fact],
        )


def test_stock_flow_and_macro_facts_are_not_recast_as_market_adapter_facts() -> None:
    facts = [
        _fact(
            "stock:MU:positioning",
            "stock_positioning",
            {"actor": "institution", "net_buy_amount": 100, "currency": "shares"},
        ),
        _fact(
            "market:nominal_yield:DGS10",
            "market_nominal_yield",
            {"level_pct": 4.2},
        ),
    ]

    value = UsMarketContextAdapter().normalize(
        assessment_date=ASSESSMENT,
        as_of=CUTOFF,
        cutoff=CUTOFF,
        fact_catalog=facts,
    )

    assert value.market_flows == []
    assert value.indices == []
    assert value.sectors == []
    assert value.deterministic_relations == []


def test_cross_section_concentration_requires_exact_arithmetic() -> None:
    section = MarketCrossSection(
        market="US",
        session_date=date(2026, 8, 24),
        as_of=CUTOFF,
        breadth=MarketBreadth(
            eligible_count=2,
            advance_count=1,
            decline_count=1,
            unchanged_count=0,
            advance_ratio=0.5,
            ad_ratio=1,
            median_return_pct=0,
            equal_weight_return_pct=0.2,
            positive_return_pct=50,
            negative_return_pct=50,
            total_trading_volume=None,
            total_trading_value=None,
        ),
        concentration={
            "metric_role": "broad_cap_weight_proxy_gap",
            "proxy_symbol": "SPY",
            "proxy_return_pct": 1.0,
            "equal_weight_return_pct": 0.2,
            "concentration_gap_pct": 0.8,
            "limitations": ["proxy only"],
        },
        quality=MarketCrossSectionQuality(
            provider="fixture",
            provider_role="shadow",
            coverage="full",
            freshness="fresh",
            universe_version="fixture-v1",
            eligible_count=2,
        ),
        source_payload_sha256="a" * 64,
    )

    value = UsMarketContextAdapter().normalize(
        assessment_date=ASSESSMENT,
        as_of=CUTOFF,
        cutoff=CUTOFF,
        fact_catalog=[],
        cross_section=section,
    )

    assert value.breadth.availability == "AVAILABLE"
    relation_scopes = {
        item.metric: item.scope for item in value.deterministic_relations
    }
    assert relation_scopes["net_advances"] == "US_BROAD"
    assert relation_scopes["advance_share"] == "US_BROAD"
    assert value.concentration[0].result == pytest.approx(0.8)
    assert value.concentration[0].scope == "US"
    section.concentration["concentration_gap_pct"] = 0.9
    with pytest.raises(ValueError, match="arithmetic mismatch"):
        UsMarketContextAdapter().normalize(
            assessment_date=ASSESSMENT,
            as_of=CUTOFF,
            cutoff=CUTOFF,
            fact_catalog=[],
            cross_section=section,
        )


def test_cross_section_after_cutoff_is_rejected() -> None:
    section = MarketCrossSection(
        market="US",
        session_date=date(2026, 8, 26),
        as_of=datetime(2026, 8, 26, 1, 0, tzinfo=UTC),
        quality=MarketCrossSectionQuality(
            provider="fixture",
            provider_role="shadow",
            coverage="unavailable",
            freshness="unknown",
            universe_version="fixture-v1",
        ),
        source_payload_sha256="a" * 64,
    )

    with pytest.raises(ValueError, match="after the adapter cutoff"):
        UsMarketContextAdapter().normalize(
            assessment_date=ASSESSMENT,
            as_of=CUTOFF,
            cutoff=CUTOFF,
            fact_catalog=[],
            cross_section=section,
        )


def test_post_close_us_event_cannot_explain_regular_session() -> None:
    event = datetime(2026, 8, 24, 20, 5, tzinfo=UTC)

    assert event_time_eligible(
        market="US",
        event_at=event,
        claimed_session_role="regular",
    ) is False
    assert event_time_eligible(
        market="US",
        event_at=event,
        claimed_session_role="after_hours",
    ) is True


@pytest.mark.parametrize(
    ("market", "at", "expected"),
    [
        ("KR", datetime(2026, 8, 24, 22, 30, tzinfo=UTC), "pre_market"),
        ("KR", datetime(2026, 8, 25, 1, 0, tzinfo=UTC), "regular"),
        ("KR", datetime(2026, 8, 25, 7, 0, tzinfo=UTC), "after_hours"),
        ("US", datetime(2026, 8, 25, 12, 0, tzinfo=UTC), "pre_market"),
        ("US", datetime(2026, 8, 25, 15, 0, tzinfo=UTC), "regular"),
        ("US", datetime(2026, 8, 25, 21, 0, tzinfo=UTC), "after_hours"),
    ],
)
def test_session_normalization(
    market: str,
    at: datetime,
    expected: str,
) -> None:
    value = market_context_adapter(market).normalize(
        assessment_date=ASSESSMENT,
        as_of=at,
        cutoff=at,
        fact_catalog=[],
    )

    assert value.session_context.role == expected


def test_market_enum_normalization_and_common_schema() -> None:
    kr = market_context_adapter("kr")
    us = market_context_adapter("US")

    assert kr.market == "KR"
    assert us.market == "US"
    with pytest.raises(ValueError, match="unsupported market"):
        market_context_adapter("EU")


def test_research_seed_adapters_share_semantics_without_conclusions() -> None:
    kr = research_seed_adapter("KR")
    us = research_seed_adapter("US")

    assert kr.common_semantics == us.common_semantics
    assert kr.seed_vocabulary != us.seed_vocabulary
    assert "OpenDART" in kr.primary_source_hints
    assert "SEC" in us.primary_source_hints
    assert kr.conclusions == us.conclusions == []
    assert kr.ticker_rules == us.ticker_rules == []


def test_runtime_connector_absence_blocks_live_research() -> None:
    unavailable = audit_production_research_connector()
    ambiguous = audit_production_research_connector({"free": True})
    available = audit_production_research_connector(
        {
            "free": True,
            "source_refs_preserved": True,
            "bounded_query_budget": True,
            "non_interactive": True,
            "production_timeout": True,
            "secret_safe": True,
        }
    )

    assert unavailable.status == "NOT_AVAILABLE"
    assert ambiguous.status == "AMBIGUOUS"
    assert available.status == "AVAILABLE"


def test_cross_section_market_mismatch_fails_closed() -> None:
    section = MarketCrossSection(
        market="KR",
        session_date=ASSESSMENT,
        as_of=CUTOFF,
        quality=MarketCrossSectionQuality(
            provider="fixture",
            provider_role="shadow",
            coverage="unavailable",
            freshness="unknown",
            universe_version="fixture-v1",
        ),
        source_payload_sha256="a" * 64,
    )

    with pytest.raises(ValueError, match="market mismatch"):
        UsMarketContextAdapter().normalize(
            assessment_date=ASSESSMENT,
            as_of=CUTOFF,
            cutoff=CUTOFF,
            fact_catalog=[],
            cross_section=section,
        )


def test_kr_cross_section_flow_keeps_scope_and_currency() -> None:
    section = MarketCrossSection(
        market="KR",
        session_date=ASSESSMENT,
        as_of=CUTOFF,
        market_flows=[
            MarketFlowFact(
                actor="institution",
                net_buy_amount=-10,
                currency="KRW",
                market="KOSPI",
            )
        ],
        quality=MarketCrossSectionQuality(
            provider="fixture",
            provider_role="shadow",
            coverage="partial",
            freshness="fresh",
            universe_version="fixture-v1",
        ),
        source_payload_sha256="a" * 64,
    )

    value = KrMarketContextAdapter().normalize(
        assessment_date=ASSESSMENT,
        as_of=CUTOFF,
        cutoff=CUTOFF,
        fact_catalog=[],
        cross_section=section,
    )

    assert value.market_flows[0].net_flow == -10
    assert value.market_flows[0].scope == "KOSPI"


def test_kr_cross_section_flow_rejects_non_krw_units() -> None:
    section = MarketCrossSection(
        market="KR",
        session_date=ASSESSMENT,
        as_of=CUTOFF,
        market_flows=[
            MarketFlowFact(
                actor="retail",
                net_buy_amount=10,
                currency="shares",
                market="KOSPI",
            )
        ],
        quality=MarketCrossSectionQuality(
            provider="fixture",
            provider_role="shadow",
            coverage="partial",
            freshness="fresh",
            universe_version="fixture-v1",
        ),
        source_payload_sha256="a" * 64,
    )

    with pytest.raises(ValueError, match="KRW monetary units"):
        KrMarketContextAdapter().normalize(
            assessment_date=ASSESSMENT,
            as_of=CUTOFF,
            cutoff=CUTOFF,
            fact_catalog=[],
            cross_section=section,
        )
