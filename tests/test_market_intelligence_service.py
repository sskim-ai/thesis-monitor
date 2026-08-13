import json
from datetime import UTC, date, datetime

from app.models.macro import MacroBriefing
from app.services.market_intelligence_service import build_market_intelligence
from app.services.numeric_semantic_registry import (
    build_numeric_registry,
    numeric_registry_coverage,
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
