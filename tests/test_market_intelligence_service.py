import json
from datetime import UTC, date, datetime

from app.models.macro import MacroBriefing
from app.services.market_intelligence_service import build_market_intelligence
from app.services.market_cross_section_service import (
    MarketBreadth,
    MarketCrossSection,
    MarketCrossSectionQuality,
)
from app.services.numeric_semantic_registry import (
    build_numeric_registry,
    numeric_registry_coverage,
    usage_matches_semantic,
)


RUN_DATE = date(2026, 8, 13)


def _briefing(observations: list[dict[str, object]]) -> MacroBriefing:
    return MacroBriefing(
        briefing_date=RUN_DATE,
        briefing_type="morning",
        as_of=datetime(2026, 8, 13, 0, 0, tzinfo=UTC),
        headline="fixture",
        market_summary=json.dumps({"observations": observations}),
        regime_summary="{}",
        today_calendar="[]",
        macro_theses="[]",
        ticker_impacts="[]",
        data_quality="[]",
        kakao_text="fixture",
        status="ready",
        dedupe_key="market-intelligence-fixture",
    )


def _observation(
    series_code: str,
    category: str,
    value: float,
    change_pct: float,
    *,
    change_value: float | None = None,
    quality: str = "fresh",
) -> dict[str, object]:
    return {
        "series_code": series_code,
        "category": category,
        "value": value,
        "change_value": change_value,
        "change_pct": change_pct,
        "observed_at": "2026-08-12 00:00:00",
        "quality_status": quality,
    }


def _stocks() -> list[dict[str, object]]:
    return [
        {
            "ticker": "MEMORY",
            "company_profile": {"quality": "verified", "taxonomy_key": "memory"},
            "knowledge_routing": {"industry_key": "memory"},
        },
        {
            "ticker": "LOGISTICS",
            "company_profile": {"quality": "verified", "taxonomy_key": "shipping"},
            "knowledge_routing": {"industry_key": "shipping"},
        },
    ]


def _diverse_stocks() -> list[dict[str, object]]:
    return [
        {
            "ticker": ticker,
            "company_profile": {"quality": "verified", "taxonomy_key": taxonomy},
            "knowledge_routing": {"industry_key": taxonomy},
        }
        for ticker, taxonomy in (
            ("CHIP", "semiconductor"),
            ("INSURE", "insurance"),
            ("SHIP", "shipping"),
            ("AUTO", "automotive"),
            ("BIO", "biotech"),
            ("DIVERSE", "general"),
        )
    ]


def _observations() -> list[dict[str, object]]:
    return [
        _observation("SPY", "market_index", 772.37, 0.2194),
        _observation("QQQ", "market_index", 722.33, 0.5296),
        _observation("IWM", "market_index", 302.92, 0.6446),
        _observation("SOXX", "sector", 546.9, 2.1422),
        _observation("DGS10", "rates", 4.7, -0.4237, change_value=-0.02),
        _observation("DFII10", "real_rates", 2.43, 0.0, change_value=0.0),
        _observation("T10YIE", "inflation", 2.26, -0.4405, change_value=-0.01),
        _observation(
            "BAMLH0A0HYM2", "credit", 2.72, 0.7407, change_value=0.02
        ),
        _observation("USDKRW", "fx", 1415.7, -0.1904, change_value=-2.7),
        _observation("DCOILWTICO", "commodities", 84.77, 3.4285, change_value=2.81),
        _observation("VIXCLS", "volatility", 15.28, -1.1643, change_value=-0.18),
        _observation("DTWEXBGS", "fx", 119.06, -0.5334, quality="stale"),
    ]


def test_market_fact_selection_uses_verified_changes_and_excludes_stale() -> None:
    result = build_market_intelligence(
        _briefing(_observations()), RUN_DATE, _stocks(), [], market="kr"
    )
    facts = {item["fact_id"]: item for item in result["fact_catalog"]}

    assert "market:relative:SOXX:SPY" in facts
    assert facts["market:relative:SOXX:SPY"]["fields"]["relative_return_pct"] == (
        2.1422 - 0.2194
    )
    assert result["key_change_fact_ids"] == [
        "market:relative:SOXX:SPY",
        "market:oil:DCOILWTICO",
    ]
    assert all("DTWEXBGS" not in fact_id for fact_id in facts)
    assert result["coverage"]["breadth"]["status"] == "unavailable"
    assert result["coverage"]["market_flows"]["status"] == "unavailable"
    assert result["coverage"]["local_market_indices"]["status"] == "unavailable"
    assert result["coverage"]["indices"]["role"] == "overnight_cross_asset_context"
    assert result["coverage"]["sectors"]["status"] == "partial"
    assert any("DTWEXBGS" in item for item in result["unknowns"])


def test_fx_change_uses_its_exact_field_for_key_change_selection() -> None:
    observations = [
        _observation("SPY", "market_index", 772.37, 0.1),
        _observation("USDKRW", "fx", 1430.0, 0.9, change_value=12.8),
    ]
    result = build_market_intelligence(
        _briefing(observations), RUN_DATE, _stocks(), [], market="kr"
    )

    assert result["key_change_fact_ids"] == ["market:fx:USDKRW"]


def test_us_indices_are_local_proxies_but_breadth_remains_unknown() -> None:
    result = build_market_intelligence(
        _briefing(_observations()), RUN_DATE, _stocks(), [], market="us"
    )

    assert result["coverage"]["indices"]["role"] == "local_market_proxy"
    assert result["coverage"]["sectors"]["role"] == "local_sector_proxy"
    assert result["coverage"]["local_market_indices"]["status"] == "available"
    assert result["coverage"]["breadth"]["status"] == "unavailable"


def test_verified_fresh_cross_section_adds_breadth_facts_without_thesis_mutation() -> None:
    section = MarketCrossSection(
        market="US",
        session_date=RUN_DATE,
        as_of=datetime(2026, 8, 13, tzinfo=UTC),
        breadth=MarketBreadth(
            eligible_count=4,
            advance_count=2,
            decline_count=1,
            unchanged_count=1,
            advance_ratio=0.5,
            ad_ratio=2.0,
            median_return_pct=0.1,
            equal_weight_return_pct=0.2,
            positive_return_pct=50.0,
            negative_return_pct=25.0,
            total_trading_volume=1000,
            total_trading_value=20000,
        ),
        concentration={
            "metric_role": "broad_cap_weight_proxy_gap",
            "proxy_symbol": "SPY",
            "proxy_return_pct": 1.0,
            "equal_weight_return_pct": 0.2,
            "concentration_gap_pct": 0.8,
        },
            quality=MarketCrossSectionQuality(
                provider="massive",
                provider_role="shadow",
                coverage="full",
                freshness="fresh",
                universe_version="massive-v1",
                volume_semantics="raw_reported_shares",
                trading_value_semantics="official_reported",
                raw_count=5,
                eligible_count=4,
                excluded_count=1,
            ),
        source_payload_sha256="a" * 64,
    )
    result = build_market_intelligence(
        _briefing(_observations()),
        RUN_DATE,
        _stocks(),
        [],
        market="us",
        cross_section=section,
    )

    facts = {item["fact_id"]: item for item in result["fact_catalog"]}
    assert result["coverage"]["breadth"]["provider"] == "massive"
    assert facts["market:breadth:us:counts"]["fields"]["advance_count"] == 2
    assert facts["market:concentration:us"]["fields"]["metric_role"] == (
        "broad_cap_weight_proxy_gap"
    )
    assert all(
        link["not_fundamental_confirmation"]
        for links in result["stock_transmissions"].values()
        for link in links
    )
    registry = build_numeric_registry(result["fact_catalog"])
    assert numeric_registry_coverage([registry])["ready"] is True
    semantics = {item["semantic_type"] for item in registry}
    assert {
        "market_eligible_count",
        "market_advance_count",
        "market_decline_count",
        "market_unchanged_count",
        "market_advance_ratio",
        "market_ad_ratio",
        "market_median_return_pct",
        "market_equal_weight_return_pct",
        "market_positive_return_pct",
        "market_negative_return_pct",
        "market_total_volume",
        "market_total_trading_value",
        "market_concentration_gap_pct",
    } <= semantics


def test_adjusted_volume_and_close_times_volume_stay_audit_only() -> None:
    section = MarketCrossSection(
        market="US",
        session_date=RUN_DATE,
        as_of=datetime(2026, 8, 13, tzinfo=UTC),
        breadth=MarketBreadth(
            eligible_count=4,
            advance_count=2,
            decline_count=1,
            unchanged_count=1,
            advance_ratio=0.5,
            ad_ratio=2.0,
            median_return_pct=0.1,
            equal_weight_return_pct=0.2,
            positive_return_pct=50.0,
            negative_return_pct=25.0,
            total_trading_volume=1000.5,
            total_trading_value=20000.25,
        ),
        quality=MarketCrossSectionQuality(
            provider="massive",
            provider_role="shadow",
            coverage="full",
            freshness="fresh",
            universe_version="massive-v1",
            volume_semantics="split_adjusted_aggregate_volume",
            trading_value_semantics=(
                "deterministic_close_times_adjusted_volume_estimate"
            ),
            raw_count=5,
            eligible_count=4,
            excluded_count=1,
        ),
        source_payload_sha256="a" * 64,
    )

    result = build_market_intelligence(
        _briefing(_observations()),
        RUN_DATE,
        _stocks(),
        [],
        market="us",
        cross_section=section,
    )
    semantics = {
        item["semantic_type"]
        for item in build_numeric_registry(result["fact_catalog"])
    }

    assert "market_total_volume" not in semantics
    assert "market_total_trading_value" not in semantics


def test_stale_cross_section_is_excluded_and_breadth_remains_unknown() -> None:
    section = MarketCrossSection(
        market="US",
        session_date=RUN_DATE,
        as_of=datetime(2026, 8, 13, tzinfo=UTC),
        breadth=None,
        quality=MarketCrossSectionQuality(
            provider="massive",
            provider_role="shadow",
            coverage="unavailable",
            freshness="stale",
            universe_version="massive-v1",
        ),
        source_payload_sha256="a" * 64,
    )
    result = build_market_intelligence(
        _briefing(_observations()),
        RUN_DATE,
        _stocks(),
        [],
        market="us",
        cross_section=section,
    )

    assert result["coverage"]["breadth"]["status"] == "unavailable"
    assert not any(
        str(item["fact_id"]).startswith("market:breadth")
        for item in result["fact_catalog"]
    )


def test_portfolio_transmission_uses_verified_profiles_and_macro_evidence() -> None:
    impacts = [
        {
            "ticker": "LOGISTICS",
            "evidence": [
                {
                    "series_code": "DCOILWTICO",
                    "direction": "negative",
                    "materiality": "high",
                    "earnings_link_validated": True,
                    "eligible_for_valuation_context": False,
                    "exposure": {
                        "factor": "wti",
                        "channel": "cost",
                        "condition": "연료비 상승이 운임 전가보다 빠를 때",
                        "horizon": "단기~분기",
                    },
                }
            ],
        }
    ]
    result = build_market_intelligence(
        _briefing(_observations()), RUN_DATE, _stocks(), impacts, market="kr"
    )

    groups = {item["group_key"]: item for item in result["portfolio_exposure_groups"]}
    assert groups["memory"]["tickers"] == ["MEMORY"]
    assert groups["shipping"]["tickers"] == ["LOGISTICS"]
    memory = result["stock_transmissions"]["MEMORY"]
    logistics = result["stock_transmissions"]["LOGISTICS"]
    assert {item["fact_id"] for item in memory} == {
        "market:relative:SOXX:SPY"
    }
    assert {item["fact_id"] for item in logistics} == {
        "market:oil:DCOILWTICO"
    }
    assert all(item["not_fundamental_confirmation"] for item in memory + logistics)


def test_missing_sector_data_does_not_create_sector_fact_or_transmission() -> None:
    observations = [item for item in _observations() if item["series_code"] != "SOXX"]
    result = build_market_intelligence(
        _briefing(observations), RUN_DATE, _stocks(), [], market="kr"
    )

    assert result["coverage"]["sectors"]["status"] == "unavailable"
    assert "market:relative:SOXX:SPY" not in {
        item["fact_id"] for item in result["fact_catalog"]
    }
    assert "MEMORY" not in result["stock_transmissions"]


def test_market_numeric_semantics_have_complete_fail_closed_coverage() -> None:
    result = build_market_intelligence(
        _briefing(_observations()), RUN_DATE, _stocks(), [], market="kr"
    )
    registry = build_numeric_registry(result["fact_catalog"])
    coverage = numeric_registry_coverage([registry])

    assert coverage["ready"] is True
    assert coverage["unsupported"] == []
    semantics = {item["semantic_type"] for item in registry}
    assert {
        "index_return_pct",
        "sector_return_pct",
        "sector_relative_return_pct",
        "nominal_yield_level",
        "nominal_yield_change_bp",
        "oil_price",
        "oil_return_pct",
        "volatility_index_level",
        "volatility_return_pct",
    } <= semantics


def test_fx_yield_and_oil_level_change_semantics_are_distinct() -> None:
    result = build_market_intelligence(
        _briefing(_observations()), RUN_DATE, _stocks(), [], market="us"
    )
    registry = {
        (item["fact_id"], item["field_path"]): item
        for item in build_numeric_registry(result["fact_catalog"])
    }

    assert registry[("market:fx:USDKRW", "fields.value")]["semantic_type"] == "fx_rate"
    assert registry[("market:fx:USDKRW", "fields.change_pct")][
        "semantic_type"
    ] == "fx_return_pct"
    assert registry[("market:nominal_yield:DGS10", "fields.level_pct")][
        "semantic_type"
    ] == "nominal_yield_level"
    assert registry[("market:nominal_yield:DGS10", "fields.change_bp")][
        "semantic_type"
    ] == "nominal_yield_change_bp"
    assert registry[("market:oil:DCOILWTICO", "fields.price_usd_per_barrel")][
        "semantic_type"
    ] == "oil_price"
    assert registry[("market:oil:DCOILWTICO", "fields.return_pct")][
        "semantic_type"
    ] == "oil_return_pct"
    assert usage_matches_semantic("fx_rate", "원/달러 환율 1,415.7원")
    assert not usage_matches_semantic("fx_rate", "원/달러 환율 등락률 +0.9%")
    assert usage_matches_semantic("fx_return_pct", "원/달러 환율 등락률 +0.9%")
    assert usage_matches_semantic("nominal_yield_level", "미국 10년물 금리 4.7%")
    assert not usage_matches_semantic(
        "nominal_yield_level", "미국 10년물 금리 2bp 상승"
    )
    assert usage_matches_semantic(
        "nominal_yield_change_bp", "미국 10년물 금리 2bp 상승"
    )
    assert usage_matches_semantic("oil_price", "WTI 유가 84.77달러/배럴")
    assert not usage_matches_semantic("oil_price", "WTI 등락률 +3.4%")
    assert usage_matches_semantic("oil_return_pct", "WTI 등락률 +3.4%")


def test_verified_profile_groups_do_not_receive_irrelevant_sector_links() -> None:
    result = build_market_intelligence(
        _briefing(_observations()), RUN_DATE, _diverse_stocks(), [], market="us"
    )

    assert {item["group_key"] for item in result["portfolio_exposure_groups"]} == {
        "semiconductor",
        "insurance",
        "shipping",
        "automotive",
        "biotech",
        "general",
    }
    assert {
        item["fact_id"] for item in result["stock_transmissions"]["CHIP"]
    } == {"market:relative:SOXX:SPY"}
    assert all(
        ticker not in result["stock_transmissions"]
        for ticker in ("INSURE", "SHIP", "AUTO", "BIO", "DIVERSE")
    )


def test_rate_fx_and_oil_stay_generic_without_verified_company_exposure() -> None:
    result = build_market_intelligence(
        _briefing(_observations()), RUN_DATE, _diverse_stocks(), [], market="us"
    )

    linked_facts = {
        item["market_fact_id"] for item in result["transmission_candidates"]
    }
    assert "market:nominal_yield:DGS10" not in linked_facts
    assert "market:fx:USDKRW" not in linked_facts
    assert "market:oil:DCOILWTICO" not in linked_facts


def test_verified_oil_exposures_preserve_distinct_transmission_channels() -> None:
    impacts = [
        {
            "ticker": ticker,
            "evidence": [
                {
                    "series_code": "DCOILWTICO",
                    "direction": direction,
                    "materiality": "high",
                    "earnings_link_validated": False,
                    "eligible_for_valuation_context": False,
                    "exposure": {
                        "factor": "wti",
                        "channel": channel,
                        "condition": condition,
                        "horizon": "conditional",
                    },
                }
            ],
        }
        for ticker, channel, direction, condition in (
            ("SHIP", "transport_cost", "negative", "fuel cost exceeds freight pass-through"),
            ("DIVERSE", "inflation", "neutral", "oil broadens inflation pressure"),
            ("AUTO", "energy_margin", "neutral", "verified energy exposure changes margin"),
        )
    ]
    result = build_market_intelligence(
        _briefing(_observations()), RUN_DATE, _diverse_stocks(), impacts, market="us"
    )

    channels = {
        ticker: {item["channel"] for item in result["stock_transmissions"][ticker]}
        for ticker in ("SHIP", "DIVERSE", "AUTO")
    }
    assert channels == {
        "SHIP": {"transport_cost"},
        "DIVERSE": {"inflation"},
        "AUTO": {"energy_margin"},
    }
    assert all(
        item["not_fundamental_confirmation"]
        for ticker in channels
        for item in result["stock_transmissions"][ticker]
    )
