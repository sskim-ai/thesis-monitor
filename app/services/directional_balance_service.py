from __future__ import annotations

import re
from collections.abc import Iterable
from decimal import Decimal

from pydantic import model_validator

from app.services.cross_market_decision_engine_service import Decision, FrozenModel


CONTRACT_VERSION = "v2-directional-balance-v1"
_PROBABILITY_LANGUAGE = re.compile(
    r"확률|승률|기대\s*수익률|probability|expected\s+return|odds",
    re.IGNORECASE,
)
_FIXED_SCORE_LANGUAGE = re.compile(
    r"(?:가중|고정)\s*(?:점수|배점)|점수\s*합산|weighted\s+score",
    re.IGNORECASE,
)


class DirectionalBalance(FrozenModel):
    buy: float
    sell: float

    @model_validator(mode="after")
    def validate_normalized_pair(self) -> "DirectionalBalance":
        buy = Decimal(str(self.buy))
        sell = Decimal(str(self.sell))
        if not buy.is_finite() or not sell.is_finite():
            raise ValueError("directional_balance_non_finite")
        if buy < 0 or sell < 0 or buy > 10 or sell > 10:
            raise ValueError("directional_balance_out_of_range")
        if buy + sell != Decimal("10"):
            raise ValueError("directional_balance_sum_not_10")
        if buy * 2 != (buy * 2).to_integral_value() or sell * 2 != (sell * 2).to_integral_value():
            raise ValueError("directional_balance_false_precision")
        return self


def decision_from_directional_balance(balance: DirectionalBalance) -> Decision:
    if balance.buy >= 6:
        return "BUY"
    if balance.sell >= 6:
        return "SELL"
    return "HOLD"


def directional_balance_matches_decision(
    balance: DirectionalBalance,
    decision: Decision,
) -> bool:
    return decision_from_directional_balance(balance) == decision


def _display(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.1f}"


def render_directional_balance(balance: DirectionalBalance) -> str:
    return f"BUY {_display(balance.buy)} : SELL {_display(balance.sell)}"


def directional_balance_language_errors(texts: Iterable[str]) -> tuple[str, ...]:
    combined = " ".join(texts)
    errors: list[str] = []
    if _PROBABILITY_LANGUAGE.search(combined):
        errors.append("directional_balance_probability_language")
    if _FIXED_SCORE_LANGUAGE.search(combined):
        errors.append("directional_balance_fixed_score_language")
    return tuple(errors)
