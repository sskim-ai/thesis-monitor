"""Schema/validation bridge to the unchanged canonical directional balance owner."""
from decimal import Decimal

from app.services.cross_market_decision_engine_service import Decision
from app.services.directional_balance_service import (
    DirectionalBalance, decision_from_directional_balance, directional_balance_matches_decision,
)


def compatible_buy_scores(decision: Decision) -> tuple[float, ...]:
    return tuple(n / 2 for n in range(21)
                 if decision_from_directional_balance(DirectionalBalance(buy=n / 2, sell=10 - n / 2)) == decision)


def accepted_directional_balance(buy: float, decision: Decision) -> DirectionalBalance:
    """Validate the accepted label; never round the score or replace its direction."""
    if isinstance(buy, bool) or not isinstance(buy, (int, float)):
        raise ValueError("directional_balance_invalid_number")
    balance = DirectionalBalance(buy=buy, sell=float(Decimal("10") - Decimal(str(buy))))
    if not directional_balance_matches_decision(balance, decision):
        raise ValueError("accepted_decision_balance_mismatch")
    return balance


DIRECTION_BALANCE_OUTPUT_RULE = (
    "Choose Overall from business evidence first. Express the accepted direction using its canonical buy score set: "
    + "; ".join(f"{direction}: {compatible_buy_scores(direction)}" for direction in ('BUY', 'HOLD', 'SELL'))
    + ". The backend derives sell = 10 - buy. This is explanatory evidence balance, not probability. "
    "Never choose a different Overall merely to fit a desired score. No other precision and no post-output rounding."
)
