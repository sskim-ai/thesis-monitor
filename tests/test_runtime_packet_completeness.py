import pytest

from app.services.numeric_semantic_registry import build_numeric_registry
from app.services.runtime_packet_completeness_service import (
    current_price_rr_packet_preflight,
)


def _stock(
    ratio: float | None,
    *,
    include_current_fact: bool = True,
    include_support_fact: bool = False,
) -> dict[str, object]:
    risk_reward: dict[str, object]
    if ratio is None:
        risk_reward = {
            "available": False,
            "reason": "resistance_unavailable",
        }
    else:
        risk_reward = {
            "available": True,
            "current_price": {"ratio": ratio},
        }
    facts: list[dict[str, object]] = []
    if include_current_fact and ratio is not None:
        facts.append(
            {
                "fact_id": "chart:structure:risk_reward:current_price",
                "fact_type": "chart_risk_reward_current_price",
                "fields": {"ratio": ratio, "rr_basis": "current_price", "currency": "KRW"},
            }
        )
    if include_support_fact and ratio is not None:
        facts.append(
            {
                "fact_id": "chart:structure:risk_reward:support_entry",
                "fact_type": "chart_risk_reward_support_entry",
                "fields": {"ratio": ratio, "rr_basis": "support_entry", "currency": "KRW"},
            }
        )
    return {
        "monitoring_state": {
            "current": {"price_structure": {"risk_reward": risk_reward}}
        },
        "fact_catalog": facts,
        "numeric_registry": build_numeric_registry(facts),
    }


@pytest.mark.parametrize(
    ("ticker", "ratio", "display"),
    [
        ("005490", 0.16778, "0.17배"),
        ("010120", 0.318131, "0.32배"),
        ("012450", 0.152999, "0.15배"),
        ("086280", 0.466189, "0.47배"),
    ],
)
def test_run23_affected_rr_numeric_path_is_exact(
    ticker: str,
    ratio: float,
    display: str,
) -> None:
    result = current_price_rr_packet_preflight(_stock(ratio))

    assert ticker
    assert result.status == "READY"
    assert result.required is True
    assert result.expected_value == ratio
    assert result.semantic_type == "current_price_risk_reward_ratio"
    assert result.unit == "x"
    assert result.canonical_display_value == display


@pytest.mark.parametrize("ticker", ["005930", "003690", "000660"])
def test_run23_unaffected_controls_allow_unavailable_rr(ticker: str) -> None:
    result = current_price_rr_packet_preflight(_stock(None))

    assert ticker
    assert result.status == "UNAVAILABLE_BY_CONTRACT"
    assert result.required is False


def test_calculated_rr_missing_from_catalog_is_a_bug() -> None:
    result = current_price_rr_packet_preflight(
        _stock(0.47, include_current_fact=False)
    )

    assert result.status == "BUG_MISSING_FACT"
    assert result.required is True


def test_scenario_rr_does_not_satisfy_current_price_rr() -> None:
    result = current_price_rr_packet_preflight(
        _stock(0.47, include_current_fact=False, include_support_fact=True)
    )

    assert result.status == "BUG_MISSING_FACT"


def test_canonical_rr_without_registry_is_a_bug() -> None:
    stock = _stock(0.47)
    stock["numeric_registry"] = []

    result = current_price_rr_packet_preflight(stock)

    assert result.status == "BUG_MISSING_NUMERIC_PATH"


def test_wrong_rr_semantic_does_not_cover_current_price_rr() -> None:
    stock = _stock(0.47)
    stock["numeric_registry"][0]["semantic_type"] = "price_to_book"

    result = current_price_rr_packet_preflight(stock)

    assert result.status == "BUG_INVALID_NUMERIC_PATH"
