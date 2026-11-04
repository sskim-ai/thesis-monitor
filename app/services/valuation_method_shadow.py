"""Offline shadow arithmetic. Not an API, owner, persistence or decision adapter."""

from __future__ import annotations

from datetime import date
from statistics import median
from typing import Annotated, Literal

from pydantic import Field, model_validator

from app.models.financial import HistoricalValuationObservation
from app.services.historical_valuation_service import (
    _position_from_percentile,
    _statistics,
    _weekly_observations,
)
from app.services.unified_snapshot_contract import ContractModel
from app.services.valuation_method_policy import (
    Domain,
    EvidenceReference,
    ForwardMethod,
    HistoricalMethod,
    IssuerCharacteristics,
    MethodApproval,
    MethodSelection,
    Nonempty,
    Sha256,
    ShadowAuthority,
    ValuationIdentity,
    receipt_sha256,
    select_shadow_methods,
)


Number = Annotated[float, Field(allow_inf_nan=False)]
Positive = Annotated[float, Field(gt=0, allow_inf_nan=False)]
Nonnegative = Annotated[float, Field(ge=0, allow_inf_nan=False)]
InputScope = Literal["FORWARD_INCOME", "HISTORICAL_MULTIPLE", "BOOK_SCENARIO"]


class LegacyArithmeticPolicy(ContractModel):
    """Pinned existing defaults, not a new user-configurable economic policy."""

    version: Literal["legacy-forward-arithmetic-v1"] = "legacy-forward-arithmetic-v1"
    minimum_quarters: Literal[8] = 8
    growth_floor: Literal[-0.3] = -0.3
    growth_cap: Literal[0.5] = 0.5
    valuation_history_min_observations: Literal[26] = 26
    valuation_history_min_days: Literal[180] = 180
    valuation_history_minimum_years: Literal[3] = 3
    valuation_history_discounted_percentile: Literal[20.0] = 20.0
    valuation_history_somewhat_discounted_percentile: Literal[40.0] = 40.0
    valuation_history_somewhat_premium_percentile: Literal[60.0] = 60.0
    valuation_history_premium_percentile: Literal[80.0] = 80.0


class Quarter(ContractModel):
    period_end: date
    available_on: date
    period_type: Literal["Q1", "H1", "Q3", "FY"]
    revenue: Number | None = None
    common_income: Number | None = None
    common_equity: Number | None = None
    dividends: Nonnegative | None = None
    equity_issuance: Number | None = None
    other_comprehensive_income: Number | None = None


class BuybackEvidence(ContractModel):
    state: Literal["VERIFIED_AMOUNT", "VERIFIED_ZERO", "UNAVAILABLE", "INVALID"]
    observed_amount: Nonnegative | None = None
    observed_period_end: date | None = None
    reason: Nonempty
    evidence: tuple[EvidenceReference, ...] = ()

    @model_validator(mode="after")
    def observation_not_assumption(self):
        if self.state in {"VERIFIED_AMOUNT", "VERIFIED_ZERO"}:
            if self.observed_amount is None or not self.evidence or self.observed_period_end is None:
                raise ValueError("observed_buyback_requires_amount_period_and_evidence")
            if self.state == "VERIFIED_ZERO" and self.observed_amount != 0:
                raise ValueError("verified_zero_amount_mismatch")
            if self.state == "VERIFIED_AMOUNT" and self.observed_amount <= 0:
                raise ValueError("positive_buyback_amount_required")
        elif self.observed_amount is not None:
            raise ValueError("unqualified_buyback_cannot_be_numeric_fact")
        return self


class MultipleObservation(ContractModel):
    date: date
    trailing_pe: Positive | None = None
    price_to_book: Positive | None = None


class SourcedMetric(ContractModel):
    metric: Nonempty
    value: Number | None
    status: Nonempty
    source_receipt_sha256: Sha256


class FinancialInputs(ContractModel):
    contract: Literal["valuation-shadow-financial-inputs-v1"] = "valuation-shadow-financial-inputs-v1"
    authority_domain: Domain
    binding: ValuationIdentity
    currency: Literal["USD", "KRW"]
    price_currency: Literal["USD", "KRW"]
    share_basis: Literal["ordinary_share"]
    reporting_basis: Nonempty
    price_as_of: date
    current_price: Positive | None
    income_shares: Positive | None
    common_shares: Positive | None
    current_equity: Positive | None
    quarters: tuple[Quarter, ...]
    buybacks: BuybackEvidence
    evidence: tuple[EvidenceReference, ...] = Field(min_length=1)
    sourced_metrics: tuple[SourcedMetric, ...] = ()
    historical_observations: tuple[MultipleObservation, ...] = ()
    trailing_pe: Positive | None = None
    current_pbr: Positive | None = None
    historical_comparability: Literal["qualified", "low"] = "qualified"


class InputQualification(ContractModel):
    contract: Literal["valuation-model-input-qualification-v1"] = "valuation-model-input-qualification-v1"
    authority_domain: Domain
    binding: ValuationIdentity
    financial_inputs_sha256: Sha256
    reporting_basis: Nonempty
    qualified_scopes: tuple[InputScope, ...]
    owner: Nonempty
    qualification_version: Nonempty
    evidence: tuple[EvidenceReference, ...] = Field(min_length=1)


class ForwardResult(ContractModel):
    status: Literal["VALUE", "NOT_MEANINGFUL", "UNRESOLVED", "INAPPLICABLE"]
    method: str
    expected_earnings: Number | None = None
    forward_eps: Number | None = None
    forward_pe: Number | None = None
    confidence: Number | None = None
    confidence_scope: Literal["MODEL_INTRINSIC_BEFORE_SOURCE_FRESHNESS"] = (
        "MODEL_INTRINSIC_BEFORE_SOURCE_FRESHNESS"
    )
    reason_codes: tuple[str, ...]


class HistoricalResult(ContractModel):
    position: str = "unknown"
    confidence: Literal["low", "medium", "high"] = "low"
    confidence_scope: Literal["HISTORY_COMPARABILITY_BEFORE_SOURCE_FRESHNESS"] = (
        "HISTORY_COMPARABILITY_BEFORE_SOURCE_FRESHNESS"
    )
    pe_percentile: Number | None = None
    pb_percentile: Number | None = None
    selected_percentile: Number | None = None
    reason_codes: tuple[str, ...]


class CalculationAssumption(ContractModel):
    component: Nonempty
    method: Nonempty
    value: Number
    limitation: Nonempty


class ZeroBuybackScenario(ContractModel):
    scenario_id: Literal["BUYBACK_ASSUMED_ZERO_V1"] = "BUYBACK_ASSUMED_ZERO_V1"
    scenario_type: Literal["ASSUMPTION_BASED_VALUATION"] = "ASSUMPTION_BASED_VALUATION"
    status: Literal["SCENARIO_ONLY", "UNRESOLVED", "INAPPLICABLE"]
    binding: ValuationIdentity
    authority_domain: Domain
    eligible_as_authoritative_evidence: Literal[False] = False
    assumption_status: Literal["ASSUMED_ZERO"] = "ASSUMED_ZERO"
    assumed_future_buybacks: Literal[0.0] = 0.0
    buyback_evidence: BuybackEvidence
    model_version: Literal["legacy-forward-arithmetic-v1"] = "legacy-forward-arithmetic-v1"
    currency: str
    share_basis: str
    price_as_of: date
    method: str
    forward_bvps_scenario: Number | None = None
    forward_pbr_scenario: Number | None = None
    forecast_equity_scenario: Number | None = None
    assumptions: tuple[CalculationAssumption, ...] = ()
    confidence_class: Literal["LOW_ASSUMPTION_BASED"] = "LOW_ASSUMPTION_BASED"
    reason_codes: tuple[str, ...]
    financial_inputs_sha256: Sha256
    selection_sha256: Sha256
    input_qualification_sha256: Sha256 | None
    disclosure: str = (
        "Conditional zero-future-buyback scenario, not verified financial evidence. "
        "Other forecast and denominator assumptions are listed separately."
    )


class ShadowValuation(ContractModel):
    contract: Literal["valuation-policy-shadow-result-v1"] = "valuation-policy-shadow-result-v1"
    purpose: Literal["VALUATION_SHADOW_ONLY"] = "VALUATION_SHADOW_ONLY"
    eligible_as_production_authority: Literal[False] = False
    binding: ValuationIdentity
    buyback_evidence: BuybackEvidence
    selection: MethodSelection
    forward: ForwardResult
    historical: HistoricalResult
    zero_buyback_scenario: ZeroBuybackScenario | None
    canonical_modeled_forward_bvps: None = None
    canonical_modeled_forward_pbr: None = None
    canonical_model_status: Literal["NOT_CALCULATED_BY_SHADOW"] = "NOT_CALCULATED_BY_SHADOW"
    independent_sourced_metrics: tuple[SourcedMetric, ...]
    sourced_metric_handling: Literal["UNCHANGED_NOT_REQUALIFIED"] = "UNCHANGED_NOT_REQUALIFIED"
    financial_inputs_sha256: Sha256
    input_qualification_sha256: Sha256 | None
    input_reason_codes: tuple[str, ...]


def _input_reasons(binding, inputs, qualification, authority, characteristics):
    reasons = []
    if binding.security_type != "common_stock":
        reasons.append("DEPOSITARY_FINANCIAL_CONVERSION_NOT_QUALIFIED")
    if inputs.binding != binding or authority.binding != binding:
        reasons.append("FINANCIAL_BINDING_MISMATCH")
    if inputs.authority_domain != authority.authority_domain:
        reasons.append("FINANCIAL_AUTHORITY_DOMAIN_MISMATCH")
    if qualification is None:
        reasons.append("INPUT_QUALIFICATION_MISSING")
    else:
        if receipt_sha256(qualification) not in authority.input_qualification_sha256:
            reasons.append("INPUT_OWNER_NOT_AUTHORIZED")
        if qualification.financial_inputs_sha256 != receipt_sha256(inputs):
            reasons.append("INPUT_DIGEST_MISMATCH")
        if qualification.binding != binding:
            reasons.append("INPUT_QUALIFICATION_BINDING_MISMATCH")
        if qualification.authority_domain != authority.authority_domain:
            reasons.append("INPUT_QUALIFICATION_DOMAIN_MISMATCH")
        if qualification.reporting_basis != inputs.reporting_basis:
            reasons.append("FINANCIAL_BASIS_UNQUALIFIED")
        if any(e.available_on > binding.as_of for e in qualification.evidence):
            reasons.append("INPUT_QUALIFICATION_FUTURE_EVIDENCE")
    if characteristics and characteristics.reporting_basis != inputs.reporting_basis:
        reasons.append("CHARACTERISTICS_FINANCIAL_BASIS_MISMATCH")
    if inputs.currency != inputs.price_currency:
        reasons.append("PRICE_FINANCIAL_CURRENCY_MISMATCH")
    dates = [q.period_end for q in inputs.quarters]
    if dates != sorted(set(dates)):
        reasons.append("QUARTER_ORDER_OR_DUPLICATE_GAP")
    if any(q.period_end > q.available_on or q.available_on > binding.as_of for q in inputs.quarters):
        reasons.append("QUARTER_TEMPORAL_GAP")
    refs = (*inputs.evidence, *inputs.buybacks.evidence)
    if any(e.available_on > binding.as_of for e in refs):
        reasons.append("FINANCIAL_FUTURE_EVIDENCE")
    if inputs.buybacks.observed_period_end and inputs.buybacks.observed_period_end > binding.as_of:
        reasons.append("BUYBACK_FUTURE_OBSERVATION")
    if inputs.price_as_of > binding.as_of:
        reasons.append("PRICE_FUTURE_DATA")
    if any(o.date > binding.as_of for o in inputs.historical_observations):
        reasons.append("HISTORY_FUTURE_DATA")
    return tuple(reasons)


def _forward(selection, inputs, reasons, policy):
    method = selection.forward.method
    if selection.forward.status == "UNRESOLVED":
        return ForwardResult(status="UNRESOLVED", method=method,
                             reason_codes=selection.forward.reason_codes)
    if method in {ForwardMethod.SPECIAL_SCENARIO_METHOD, ForwardMethod.FORWARD_MODEL_INAPPLICABLE}:
        return ForwardResult(status="INAPPLICABLE", method=method,
                             reason_codes=("ORDINARY_FORWARD_MODEL_INAPPLICABLE",))
    if reasons:
        return ForwardResult(status="UNRESOLVED", method=method, reason_codes=reasons)
    recent = inputs.quarters[-policy.minimum_quarters:]
    if len(recent) < policy.minimum_quarters or inputs.income_shares is None:
        return ForwardResult(status="UNRESOLVED", method=method,
                             reason_codes=("INCOME_QUARTERS_OR_SHARE_BASIS_MISSING",))
    if method == ForwardMethod.NORMALIZED_ROE:
        values = [q.common_income * 4 / q.common_equity for q in recent
                  if q.common_income is not None and q.common_equity and q.common_equity > 0]
        if not values or inputs.current_equity is None:
            return ForwardResult(status="UNRESOLVED", method=method,
                                 reason_codes=("EQUITY_EARNINGS_BASIS_MISSING",))
        income = inputs.current_equity * median(values)
    else:
        if any(q.revenue is None or q.revenue <= 0 or q.common_income is None for q in recent):
            return ForwardResult(status="UNRESOLVED", method=method,
                                 reason_codes=("MARGIN_INPUT_MISSING",))
        current_revenue = sum(q.revenue for q in recent[-4:])
        prior_revenue = sum(q.revenue for q in recent[-8:-4])
        growth = max(policy.growth_floor, min(policy.growth_cap,
                                             current_revenue / prior_revenue - 1))
        normalized = median(q.common_income / q.revenue for q in recent)
        latest = sum(q.common_income for q in recent[-4:]) / current_revenue
        margin = (normalized if method == ForwardMethod.NORMALIZED_CYCLE_MARGIN
                  else latest * 0.6 + normalized * 0.4)
        income = current_revenue * (1 + growth) * margin
    if income <= 0:
        return ForwardResult(status="NOT_MEANINGFUL", method=method, expected_earnings=income,
                             reason_codes=("QUALIFIED_NONPOSITIVE_MODELED_EARNINGS",))
    eps = income / inputs.income_shares
    return ForwardResult(status="VALUE", method=method, expected_earnings=income, forward_eps=eps,
                         forward_pe=round(inputs.current_price / eps, 4)
                         if inputs.current_price is not None else None,
                         confidence=0.55, reason_codes=("QUALIFIED_SHADOW_FORECAST_NOT_FUTURE_FACT",))


def _historical(selection, inputs, reasons, policy):
    axis = selection.historical
    if axis.status == "UNRESOLVED":
        return HistoricalResult(reason_codes=axis.reason_codes)
    if axis.method == HistoricalMethod.INAPPLICABLE:
        return HistoricalResult(reason_codes=("HISTORICAL_METHOD_INAPPLICABLE",))
    if reasons:
        return HistoricalResult(reason_codes=reasons)
    # Reuse unchanged percentile primitives, never the legacy ticker-driven apply().
    rows = [HistoricalValuationObservation(ticker="", observation_date=o.date,
            trailing_pe=o.trailing_pe, price_to_book=o.price_to_book)
            for o in inputs.historical_observations]
    weekly = _weekly_observations(rows)
    stats = [_statistics(name, value, weekly, raw_observation_count=len(rows),
                         minimum_observations=policy.valuation_history_min_observations,
                         minimum_days=policy.valuation_history_min_days)
             for name, value in (("trailing_pe", inputs.trailing_pe),
                                 ("price_to_book", inputs.current_pbr))]
    pe, pb = stats
    pe_pct = pe.current_percentile if pe else None
    pb_pct = pb.current_percentile if pb else None
    selected = [p for p in ([pb_pct] if axis.historical_signal == "PB_ONLY"
                            else [pe_pct, pb_pct]) if p is not None]
    if not selected:
        return HistoricalResult(reason_codes=("insufficient_history",))
    conflict = pe_pct is not None and pb_pct is not None and abs(pe_pct - pb_pct) >= 40
    combined = (50.0 if conflict and axis.historical_signal == "PE_AND_PB" else median(selected))
    confidence = "high" if min(s.observation_count for s in stats
                               if s and s.current_percentile is not None) >= 156 else "medium"
    max_years = max(s.lookback_years for s in stats if s)
    low = inputs.historical_comparability == "low" or 0 < max_years < 3
    reasons = ("conflicting_multiples",) if conflict else ()
    if low:
        confidence = "low"
        reasons += ("low_comparability",)
    return HistoricalResult(position=_position_from_percentile(combined, policy).value,
                            confidence=confidence, pe_percentile=pe_pct, pb_percentile=pb_pct,
                            selected_percentile=combined, reason_codes=reasons)


def _scenario(selection, inputs, qualification, forward, reasons, policy):
    common = dict(binding=selection.binding, authority_domain=selection.authority_domain,
                  buyback_evidence=inputs.buybacks, currency=inputs.currency,
                  share_basis=inputs.share_basis, price_as_of=inputs.price_as_of,
                  method=forward.method, financial_inputs_sha256=receipt_sha256(inputs),
                  selection_sha256=receipt_sha256(selection),
                  input_qualification_sha256=receipt_sha256(qualification) if qualification else None)
    if forward.status == "INAPPLICABLE":
        return ZeroBuybackScenario(status="INAPPLICABLE", reason_codes=forward.reason_codes, **common)
    if reasons or forward.status != "VALUE":
        return ZeroBuybackScenario(status="UNRESOLVED",
                                  reason_codes=reasons or forward.reason_codes, **common)
    if inputs.buybacks.state == "INVALID":
        return ZeroBuybackScenario(status="UNRESOLVED", reason_codes=("BUYBACK_EVIDENCE_INVALID",),
                                  **common)
    if any(v is None for v in (inputs.current_equity, inputs.common_shares, inputs.current_price)):
        return ZeroBuybackScenario(status="UNRESOLVED", reason_codes=("BOOK_BASIS_MISSING",),
                                  **common)
    annual = [q for q in inputs.quarters if q.period_type == "FY" and q.dividends is not None][-3:]
    payouts = [q.dividends / q.common_income for q in annual
               if q.common_income is not None and q.common_income > 0]
    if len(payouts) >= 3:
        dividends = forward.expected_earnings * max(0.0, min(1.0, median(payouts)))
        dividend_method = "median_3y_payout_ratio"
    elif annual:
        dividends = median(q.dividends for q in annual) if len(annual) >= 3 else annual[-1].dividends
        dividend_method = "median_3y_dividend" if len(annual) >= 3 else "latest_dividend"
    else:
        return ZeroBuybackScenario(status="UNRESOLVED", reason_codes=("DIVIDEND_INPUT_MISSING",),
                                  **common)
    assumptions = [
        CalculationAssumption(component="forecast_common_income", method=forward.method,
                              value=forward.expected_earnings, limitation="Forecast, not observed income"),
        CalculationAssumption(component="forecast_dividends", method=dividend_method, value=dividends,
                              limitation="Historical projection, not an announced future dividend"),
        CalculationAssumption(component="forecast_buybacks", method="ASSUMED_ZERO", value=0,
                              limitation="Conditional future zero; observed evidence is unchanged"),
        CalculationAssumption(component="common_shares", method="FIXED_CURRENT_COMMON_SHARES",
                              value=inputs.common_shares,
                              limitation="No modeled repurchase, treasury-share or financing share-count effects"),
    ]
    extras = []
    for field in ("equity_issuance", "other_comprehensive_income"):
        values = [getattr(q, field) for q in inputs.quarters[-policy.minimum_quarters:]
                  if getattr(q, field) is not None]
        amount = median(values) if values else 0.0
        extras.append(amount)
        assumptions.append(CalculationAssumption(component=field, value=amount,
                           method="HISTORICAL_MEDIAN_PROJECTION" if values else "ASSUMED_ZERO",
                           limitation="Projection, not a future fact" if values
                           else "Missing input explicitly assumed zero for this scenario only"))
    equity = inputs.current_equity + forward.expected_earnings - dividends - 0.0 + sum(extras)
    if equity <= 0:
        return ZeroBuybackScenario(status="UNRESOLVED", assumptions=tuple(assumptions),
                                  reason_codes=("NONPOSITIVE_PROJECTED_EQUITY",), **common)
    bvps = equity / inputs.common_shares
    reason = ("MISSING_BUYBACK_EVIDENCE_ASSUMED_ZERO" if inputs.buybacks.state == "UNAVAILABLE"
              else "HISTORICAL_BUYBACK_DOES_NOT_ESTABLISH_FUTURE_ZERO")
    return ZeroBuybackScenario(status="SCENARIO_ONLY", forward_bvps_scenario=bvps,
                              forward_pbr_scenario=round(inputs.current_price / bvps, 4),
                              forecast_equity_scenario=equity, assumptions=tuple(assumptions),
                              reason_codes=(reason,), **common)


def evaluate_shadow_valuation(
    *,
    binding: ValuationIdentity,
    characteristics: IssuerCharacteristics | None,
    approvals: tuple[MethodApproval, ...],
    financial_inputs: FinancialInputs,
    input_qualification: InputQualification | None,
    authority: ShadowAuthority,
    include_zero_buyback_scenario: bool = False,
) -> ShadowValuation:
    selection = select_shadow_methods(binding, characteristics, approvals, authority)
    reasons = _input_reasons(binding, financial_inputs, input_qualification, authority, characteristics)
    scopes = input_qualification.qualified_scopes if input_qualification else ()

    def scoped(scope):
        return reasons + (() if scope in scopes else ("INPUT_SCOPE_UNQUALIFIED:" + scope,))

    policy = LegacyArithmeticPolicy()
    forward = _forward(selection, financial_inputs, scoped("FORWARD_INCOME"), policy)
    return ShadowValuation(
        binding=binding, buyback_evidence=financial_inputs.buybacks, selection=selection, forward=forward,
        historical=_historical(selection, financial_inputs, scoped("HISTORICAL_MULTIPLE"), policy),
        zero_buyback_scenario=_scenario(selection, financial_inputs, input_qualification, forward,
                                       scoped("BOOK_SCENARIO"), policy)
        if include_zero_buyback_scenario else None,
        independent_sourced_metrics=financial_inputs.sourced_metrics,
        financial_inputs_sha256=receipt_sha256(financial_inputs),
        input_qualification_sha256=receipt_sha256(input_qualification) if input_qualification else None,
        input_reason_codes=reasons,
    )
