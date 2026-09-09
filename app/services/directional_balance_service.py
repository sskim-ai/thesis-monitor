from __future__ import annotations

import re
from collections.abc import Iterable
from decimal import Decimal

from pydantic import model_validator

from app.services.cross_market_decision_engine_service import Decision, FrozenModel


CONTRACT_VERSION = "v2-directional-balance-v1"
ORDINAL_CALIBRATION_CONTRACT_VERSION = "directional-balance-ordinal-calibration-v1"
ORDINAL_CALIBRATION_PROMPT = """Calibrate directional_balance as an ordinal evidence-sufficiency ladder, not as probability or a fixed-weight scorecard.

5.0:5.0 means the evidence is genuinely balanced, unresolved, or too incomplete to support even a lean. 5.5:4.5 means a positive issuer-level material anchor exists, but missing corroboration, currentness, persistence, valuation, or a critical business KPI prevents a full positive direction. 6.0:4.0 is the minimum BUY and requires both a positive issuer-level material anchor and sufficiently current or independent corroboration; unresolved counterevidence must not keep the case at lean-only. 6.5:3.5 and stronger positive balances require progressively stronger corroboration, persistence, quality, visibility, or valuation support under the same evidence-only rules.

Apply the exact symmetric meanings to 4.5:5.5, 4.0:6.0, and 3.5:6.5 or stronger negative balances. Missing evidence limits conviction but is not negative evidence by itself. When the same supplied evidence reasonably fits two adjacent balance buckets, choose the less directional bucket toward 5.0:5.0. Low confidence should trigger a careful check that the full directional bucket is actually supported, but LOW confidence does not mechanically require HOLD.

Independent corroboration adds a distinct economic fact. Multiple financial metrics sharing underlying cash-flow inputs, derivation lineage, or substantially overlapping source basis are not automatically independent corroboration for moving from a 5.5 lean to a 6.0 directional bucket. For example, operating cash flow and OCF less identified PPE cash outflow can describe overlapping economics. Judge the economic contribution, not the number of metrics or evidence references; apply this equally to positive and negative cases.

A material unresolved causal, reversibility, persistence, or critical-validation limit constrains justified directional strength without becoming negative evidence. When an anchor and support exist but such a limit leaves adjacent buckets reasonably supportable, apply the existing tie-break toward 5.0. Do not mechanically subtract strength for every Unknown or require HOLD solely from LOW confidence.

A financial or non-operating effect that improves reported net income while underlying operations remain broadly flat explains earnings composition; by itself it does not support a positive 5.5 lean. A positive lean needs a separate positive issuer-level operating/business, cash-conversion, balance-sheet, valuation, or other material anchor. Apply the same composition-versus-direction distinction on the negative side where appropriate. Do not assume that all non-operating gains are one-off or low quality.

6.0 is minimum directional support. A 6.5-or-stronger bucket needs evidence beyond that minimum which materially strengthens persistence, quality, visibility, independent corroboration, or valuation support. If an unresolved material confirmation leaves both 6.0 and 6.5 reasonably supportable, the existing tie-break selects 6.0. Apply this equally to BUY and SELL strength; missing one particular domain is not an automatic cap when distinct stronger support is actually established.

Source-category independence is not economic independence. A market-expectation claim conditional on the same materially unresolved business or financing downside does not automatically add independent corroboration to cross from a 5.5 lean to minimum direction. It may describe surprise asymmetry or caution, but a stronger bucket requires the adverse condition to be sufficiently established or the expectation evidence to establish a distinct current pricing/expectation risk. Confirmed financing stress together with independently established expectations of benign financing may support minimum negative direction; expectations already reflecting stress do not mechanically add a negative axis. Apply the same economic-independence test to positive cases: strong resilience with already elevated expectations does not mechanically justify BUY. Judge distinct established economic propositions, not source categories or reference counts. Expectation assumptions are not a valuation multiple and do not alone establish that a stock is expensive or cheap; missing safe valuation remains a limitation, not an invented negative fact or universal directional veto."""
_KOREAN_TOKEN_PARTICLE = r"(?:은|는|이|가|을|를|도|만)?"
_PROBABILITY_LANGUAGE = re.compile(
    rf"(?<![가-힣A-Za-z0-9_])(?:성공\s*)?확률{_KOREAN_TOKEN_PARTICLE}"
    rf"(?![가-힣A-Za-z0-9_])|"
    rf"(?<![가-힣A-Za-z0-9_])승률{_KOREAN_TOKEN_PARTICLE}"
    rf"(?![가-힣A-Za-z0-9_])|"
    r"기대\s*수익률|\bprobability\b|\bexpected\s+return\b|\bodds\b|"
    r"\bwin\s+rate\b",
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


def directional_balance_ordinal_calibration_prompt() -> str:
    return ORDINAL_CALIBRATION_PROMPT
