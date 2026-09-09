from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from enum import StrEnum

from pydantic import Field

from app.services.cross_market_decision_engine_service import (
    DecisionEvidenceRef,
    FinancialComparisonKind,
    FinancialEvidenceQuality,
    FinancialEvidenceStatus,
    FinancialPeriod,
    FinancialPeriodType,
    FrozenModel,
)
from app.services.financial_framework_claim_service import (
    FrameworkClaimKind,
    candidate_financial_framework_claims,
    financial_framework_claims,
)


CONTRACT_VERSION = "directional-financial-decision-context-v1"
VALIDATOR_CONTRACT = "directional-financial-semantic-validator-v1"
QTD_YTD_VALIDATOR_CONTRACT = "directional-financial-qtd-ytd-validator-v1"
FIRST_CLASS_FINANCIAL_EVIDENCE_KIND = "TYPED_FINANCIAL"
FINANCIAL_DECISION_CONTEXT_ITEM_CAP = 8
FINANCIAL_DECISION_CONTEXT_CATEGORY_CAP = 2


class FinancialSemanticCategory(StrEnum):
    PERFORMANCE_TREND = "PERFORMANCE_TREND"
    CASH_CONVERSION = "CASH_CONVERSION"
    FINANCIAL_RESILIENCE = "FINANCIAL_RESILIENCE"
    WORKING_CAPITAL = "WORKING_CAPITAL"
    NON_OPERATING_EFFECT = "NON_OPERATING_EFFECT"
    VALUATION_READINESS = "VALUATION_READINESS"
    SECTOR_KPI = "SECTOR_KPI"
    OTHER_FINANCIAL_CONTEXT = "OTHER_FINANCIAL_CONTEXT"


class FinancialDecisionComparison(FrozenModel):
    kind: FinancialComparisonKind
    input_source_refs: tuple[str, ...] = Field(min_length=1, max_length=8)
    comparison_value: Decimal | None = None
    comparison_period: FinancialPeriod | None = None


class FinancialDecisionEvidenceItem(FrozenModel):
    evidence_id: str
    source_ref: str
    semantic_category: FinancialSemanticCategory
    metric: str
    value: Decimal
    currency: str | None
    unit_scale: int
    period: FinancialPeriod
    comparison: FinancialDecisionComparison | None = None
    evidence_status: FinancialEvidenceStatus
    quality: FinancialEvidenceQuality
    derivation_formula: str | None = None
    derivation_input_source_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


class FinancialDecisionContext(FrozenModel):
    contract: str = CONTRACT_VERSION
    sector_framework: str
    evidence_items: tuple[FinancialDecisionEvidenceItem, ...] = Field(
        max_length=FINANCIAL_DECISION_CONTEXT_ITEM_CAP
    )
    unavailable_or_not_applicable: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    selected_item_cap: int = FINANCIAL_DECISION_CONTEXT_ITEM_CAP
    eligible_input_count: int = 0
    selected_input_count: int = 0
    suppressed_input_count: int = 0


class FinancialSemanticValidation(FrozenModel):
    contract: str = VALIDATOR_CONTRACT
    valid: bool
    errors: tuple[str, ...]
    invalid_financial_reference_count: int = 0
    partial_capex_called_fcf_count: int = 0
    year_end_as_yoy_count: int = 0
    partial_debt_total_claim_count: int = 0
    normalized_earnings_claim_violation_count: int = 0
    financial_sector_generic_financial_context_leak_count: int = 0
    fixed_financial_score_rule_count: int = 0


class QtdYtdConflictValidation(FrozenModel):
    contract: str = QTD_YTD_VALIDATOR_CONTRACT
    required: bool
    valid: bool
    errors: tuple[str, ...]
    required_metrics: tuple[str, ...] = ()
    qtd_evidence_ref_count: int = 0
    ytd_evidence_ref_count: int = 0
    linked_claim_count: int = 0
    explicit_claim_count: int = 0


_CATEGORY_ORDER = {
    FinancialSemanticCategory.PERFORMANCE_TREND: 0,
    FinancialSemanticCategory.CASH_CONVERSION: 1,
    FinancialSemanticCategory.FINANCIAL_RESILIENCE: 2,
    FinancialSemanticCategory.WORKING_CAPITAL: 3,
    FinancialSemanticCategory.NON_OPERATING_EFFECT: 4,
    FinancialSemanticCategory.VALUATION_READINESS: 5,
    FinancialSemanticCategory.SECTOR_KPI: 6,
    FinancialSemanticCategory.OTHER_FINANCIAL_CONTEXT: 7,
}

_CASH_CONVERSION_METRICS = frozenset(
    {
        "operating_cash_flow",
        "ppe_capex_cash_outflow",
        "ocf_less_ppe_capex",
    }
)
_FINANCIAL_RESILIENCE_METRICS = frozenset(
    {
        "cash_and_cash_equivalents",
        "cash_and_restricted_cash",
        "restricted_cash_current",
        "restricted_cash_noncurrent",
        "short_term_borrowings",
        "current_portion_of_long_term_debt",
        "current_interest_bearing_debt",
        "long_term_borrowings",
        "bonds_payable_current",
        "bonds_payable_noncurrent",
        "notes_payable_current",
        "notes_payable_noncurrent",
        "convertible_debt_current",
        "convertible_debt_noncurrent",
        "lease_liabilities_current",
        "lease_liabilities_noncurrent",
        "interest_bearing_debt_total",
        "net_debt",
    }
)
_WORKING_CAPITAL_METRICS = frozenset(
    {
        "inventory",
        "inventory_component",
        "trade_accounts_receivable",
        "accounts_receivable_broad",
        "trade_accounts_payable",
        "accounts_payable_broad",
        "current_assets",
        "current_liabilities",
        "contract_assets_context",
        "contract_liabilities_context",
        "working_capital_balance_delta",
    }
)
_NON_OPERATING_METRICS = frozenset(
    {
        "financial_income",
        "financial_cost",
        "net_financial_income_effect",
        "interest_income",
        "interest_expense",
        "foreign_exchange_gain",
        "foreign_exchange_loss",
        "foreign_exchange_net_effect",
        "other_income_context",
        "other_expense_context",
        "asset_disposal_gain",
        "asset_disposal_loss",
        "asset_disposal_result_context",
        "fair_value_gain",
        "fair_value_loss",
        "fair_value_result_context",
        "equity_method_result_context",
        "income_tax_expense",
        "income_tax_benefit",
        "continuing_operations_income",
        "discontinued_operations_result",
    }
)
_PERFORMANCE_METRIC_TOKENS = (
    "revenue",
    "sales",
    "operating_income",
    "operating_profit",
    "net_income",
    "gross_profit",
    "margin",
)
_FINANCIAL_SECTOR_TOKENS = (
    "bank",
    "insurance",
    "insurer",
    "reinsurance",
    "financial_institution",
    "financial institution",
    "은행",
    "보험",
    "재보험",
)

_DEBT_COMPONENT_METRICS = _FINANCIAL_RESILIENCE_METRICS - {
    "cash_and_cash_equivalents",
    "cash_and_restricted_cash",
    "restricted_cash_current",
    "restricted_cash_noncurrent",
    "interest_bearing_debt_total",
    "net_debt",
}
_NET_DEBT_CHILD_METRICS = _FINANCIAL_RESILIENCE_METRICS - {"net_debt"}

_METRIC_PRIORITY = {
    "ocf_less_ppe_capex": 0,
    "operating_cash_flow": 1,
    "ppe_capex_cash_outflow": 2,
    "net_debt": 0,
    "interest_bearing_debt_total": 1,
    "cash_and_cash_equivalents": 2,
    "inventory": 0,
    "trade_accounts_receivable": 1,
    "trade_accounts_payable": 2,
    "working_capital_balance_delta": 3,
    "net_financial_income_effect": 0,
    "foreign_exchange_net_effect": 1,
    "asset_disposal_result_context": 2,
    "fair_value_result_context": 3,
    "continuing_operations_income": 4,
}

_FINANCIAL_METRIC_LABELS = {
    "operating_cash_flow": "operating cash flow",
    "ppe_capex_cash_outflow": "PPE acquisition cash outflow",
    "ocf_less_ppe_capex": "OCF less PPE acquisition cash outflow",
    "cash_and_cash_equivalents": "cash and cash equivalents",
    "cash_and_restricted_cash": "cash and restricted cash",
    "interest_bearing_debt_total": "complete interest-bearing debt",
    "net_debt": "net debt",
    "inventory": "inventory",
    "trade_accounts_receivable": "trade accounts receivable",
    "trade_accounts_payable": "trade accounts payable",
    "operating_income": "operating income",
    "net_income": "net income",
    "net_financial_income_effect": "net financial income effect",
}

_FINANCIAL_COMPARISON_LABELS = {
    FinancialComparisonKind.PRIOR_YEAR_COMPARABLE: "prior-year comparable period",
    FinancialComparisonKind.PRIOR_YEAR_END: "prior year-end balance",
    FinancialComparisonKind.NONE: "supplied comparison basis",
}

_QTD_PERIOD_PATTERNS = (
    re.compile(r"(?<![a-z0-9])qtd(?![a-z0-9])"),
    re.compile(
        r"(?<![a-z])(?:(?:current|latest|this|recent|single)[ ]+)?"
        r"quarter(?:ly)?(?![a-z])"
    ),
    re.compile(r"(?<![가-힣])(?:최근|해당|이번|지난|단일|한)?[ ]*분기(?!점)"),
)
_YTD_PERIOD_PATTERNS = (
    re.compile(r"(?<![a-z0-9])ytd(?![a-z0-9])"),
    re.compile(r"(?<![a-z])year[ -]*to[ -]*date(?![a-z])"),
    re.compile(r"(?<![a-z])since[ ]+(?:the[ ]+)?start[ ]+of[ ]+(?:the[ ]+)?year(?![a-z])"),
    re.compile(r"(?<![a-z])cumulative(?:[ ]+ytd)?(?![a-z])"),
    re.compile(r"누계"),
    re.compile(r"누적(?!적)"),
    re.compile(r"연초[ ]*(?:이후|부터)(?:[ ]*누적)?"),
)
_PERIOD_RELATION_PATTERNS = (
    re.compile(r"(?<![a-z])(?:while|whereas|but|versus|vs)[.]?(?![a-z])"),
    re.compile(r"(?<![a-z])contrast(?:s|ed|ing)?(?![a-z])"),
    re.compile(r"(?<![a-z])coexist(?:s|ed|ing)?(?![a-z])"),
    re.compile(r"지만|반면|공존|충돌|상충|맞서|엇갈"),
)


def normalize_sector_framework(value: object) -> str:
    raw = getattr(value, "value", value)
    normalized = str(raw or "unspecified").strip().lower()
    return normalized or "unspecified"


def sector_requires_specialized_financial_framework(value: object) -> bool:
    framework = normalize_sector_framework(value)
    return any(token in framework for token in _FINANCIAL_SECTOR_TOKENS)


def semantic_category(metric: str) -> FinancialSemanticCategory:
    if metric in _CASH_CONVERSION_METRICS:
        return FinancialSemanticCategory.CASH_CONVERSION
    if metric in _FINANCIAL_RESILIENCE_METRICS:
        return FinancialSemanticCategory.FINANCIAL_RESILIENCE
    if metric in _WORKING_CAPITAL_METRICS:
        return FinancialSemanticCategory.WORKING_CAPITAL
    if metric in _NON_OPERATING_METRICS:
        return FinancialSemanticCategory.NON_OPERATING_EFFECT
    if any(token in metric for token in _PERFORMANCE_METRIC_TOKENS):
        return FinancialSemanticCategory.PERFORMANCE_TREND
    if any(token in metric for token in ("valuation", "multiple", "yield")):
        return FinancialSemanticCategory.VALUATION_READINESS
    if metric.startswith("sector_"):
        return FinancialSemanticCategory.SECTOR_KPI
    return FinancialSemanticCategory.OTHER_FINANCIAL_CONTEXT


def _structured_value(ref: DecisionEvidenceRef) -> Decimal | None:
    raw: object = ref.value
    if raw is None:
        try:
            statement = json.loads(ref.statement)
        except (json.JSONDecodeError, TypeError):
            statement = None
        if isinstance(statement, Mapping):
            raw = statement.get("value")
    try:
        return Decimal(str(raw)) if raw is not None else None
    except (InvalidOperation, ValueError):
        return None


def _period_rank(ref: DecisionEvidenceRef) -> tuple[int, int, int]:
    context = ref.financial_context
    assert context is not None
    quality_rank = 0 if context.quality == FinancialEvidenceQuality.VERIFIED else 1
    status_rank = (
        0 if context.evidence_status == FinancialEvidenceStatus.DIRECT_REPORTED else 1
    )
    return (-context.period.end.toordinal(), quality_rank, status_rank)


def _metric_rank(ref: DecisionEvidenceRef) -> tuple[object, ...]:
    context = ref.financial_context
    assert context is not None
    return (
        _METRIC_PRIORITY.get(context.metric, 50),
        *_period_rank(ref),
        context.metric,
        ref.ref_id,
    )


def _latest_per_metric_period(
    refs: Sequence[DecisionEvidenceRef],
) -> list[DecisionEvidenceRef]:
    by_metric_period: dict[tuple[str, object], list[DecisionEvidenceRef]] = {}
    for ref in refs:
        assert ref.financial_context is not None
        key = (ref.financial_context.metric, ref.financial_context.period.type)
        by_metric_period.setdefault(key, []).append(ref)
    return [sorted(rows, key=_period_rank)[0] for rows in by_metric_period.values()]


def _suppress_redundant_refs(
    refs: Sequence[DecisionEvidenceRef],
) -> list[DecisionEvidenceRef]:
    metrics = {
        ref.financial_context.metric
        for ref in refs
        if ref.financial_context is not None
    }
    suppressed: set[str] = set()
    if "net_debt" in metrics:
        suppressed.update(_NET_DEBT_CHILD_METRICS)
    elif "interest_bearing_debt_total" in metrics:
        suppressed.update(_DEBT_COMPONENT_METRICS)
    if "inventory" in metrics:
        suppressed.add("inventory_component")
    if "trade_accounts_receivable" in metrics:
        suppressed.add("accounts_receivable_broad")
    if "trade_accounts_payable" in metrics:
        suppressed.add("accounts_payable_broad")
    if "net_financial_income_effect" in metrics:
        suppressed.update(
            {
                "financial_income",
                "financial_cost",
                "interest_income",
                "interest_expense",
            }
        )
    if "foreign_exchange_net_effect" in metrics:
        suppressed.update({"foreign_exchange_gain", "foreign_exchange_loss"})
    if "asset_disposal_result_context" in metrics:
        suppressed.update({"asset_disposal_gain", "asset_disposal_loss"})
    if "fair_value_result_context" in metrics:
        suppressed.update({"fair_value_gain", "fair_value_loss"})
    return [
        ref
        for ref in refs
        if ref.financial_context is not None
        and ref.financial_context.metric not in suppressed
    ]


def _comparison(
    ref: DecisionEvidenceRef,
    by_source_ref: Mapping[str, DecisionEvidenceRef],
) -> FinancialDecisionComparison | None:
    context = ref.financial_context
    assert context is not None
    comparison = context.comparison
    if comparison is None:
        return None
    other_refs = [
        source_ref
        for source_ref in comparison.input_source_refs
        if source_ref != ref.source_ref
    ]
    comparison_ref = by_source_ref.get(other_refs[0]) if len(other_refs) == 1 else None
    return FinancialDecisionComparison(
        kind=comparison.kind,
        input_source_refs=comparison.input_source_refs,
        comparison_value=(
            _structured_value(comparison_ref) if comparison_ref is not None else None
        ),
        comparison_period=(
            comparison_ref.financial_context.period
            if comparison_ref is not None and comparison_ref.financial_context is not None
            else None
        ),
    )


def _decision_item(
    ref: DecisionEvidenceRef,
    by_source_ref: Mapping[str, DecisionEvidenceRef],
) -> FinancialDecisionEvidenceItem:
    context = ref.financial_context
    value = _structured_value(ref)
    assert context is not None and value is not None
    return FinancialDecisionEvidenceItem(
        evidence_id=ref.ref_id,
        source_ref=ref.source_ref,
        semantic_category=semantic_category(context.metric),
        metric=context.metric,
        value=value,
        currency=context.currency,
        unit_scale=context.unit_scale,
        period=context.period,
        comparison=_comparison(ref, by_source_ref),
        evidence_status=context.evidence_status,
        quality=context.quality,
        derivation_formula=(
            context.derivation.formula if context.derivation is not None else None
        ),
        derivation_input_source_refs=(
            context.derivation.input_source_refs
            if context.derivation is not None
            else ()
        ),
        limitations=context.limitations,
    )


def build_financial_decision_context(
    refs: Sequence[DecisionEvidenceRef],
    *,
    sector_framework: object = None,
) -> FinancialDecisionContext | None:
    typed = [ref for ref in refs if ref.financial_context is not None]
    if not typed:
        return None
    framework = normalize_sector_framework(sector_framework)
    if sector_requires_specialized_financial_framework(framework):
        return FinancialDecisionContext(
            sector_framework=framework,
            evidence_items=(),
            unavailable_or_not_applicable=("SECTOR_FRAMEWORK_REQUIRED",),
            limitations=("generic_industrial_financial_context_disabled",),
            eligible_input_count=len(typed),
            selected_input_count=0,
            suppressed_input_count=len(typed),
        )

    with_values = [ref for ref in typed if _structured_value(ref) is not None]
    if not with_values:
        return FinancialDecisionContext(
            sector_framework=framework,
            evidence_items=(),
            unavailable_or_not_applicable=("FINANCIAL_VALUE_UNAVAILABLE",),
            limitations=("typed_context_without_structured_value",),
            eligible_input_count=0,
            selected_input_count=0,
            suppressed_input_count=len(typed),
        )

    current = _suppress_redundant_refs(_latest_per_metric_period(with_values))
    grouped: dict[FinancialSemanticCategory, list[DecisionEvidenceRef]] = {}
    for ref in current:
        assert ref.financial_context is not None
        grouped.setdefault(semantic_category(ref.financial_context.metric), []).append(ref)
    for rows in grouped.values():
        rows.sort(key=_metric_rank)

    selected: list[DecisionEvidenceRef] = []
    categories = sorted(grouped, key=lambda value: (_CATEGORY_ORDER[value], value.value))
    for offset in range(FINANCIAL_DECISION_CONTEXT_CATEGORY_CAP):
        for category in categories:
            rows = grouped[category]
            if offset < len(rows):
                selected.append(rows[offset])
                if len(selected) == FINANCIAL_DECISION_CONTEXT_ITEM_CAP:
                    break
        if len(selected) == FINANCIAL_DECISION_CONTEXT_ITEM_CAP:
            break

    selected.sort(
        key=lambda ref: (
            _CATEGORY_ORDER[semantic_category(ref.financial_context.metric)],
            _metric_rank(ref),
        )
    )
    by_source_ref = {ref.source_ref: ref for ref in typed}
    items = tuple(_decision_item(ref, by_source_ref) for ref in selected)
    suppressed = len(typed) - len(items)
    limitations = tuple(
        dict.fromkeys(
            limitation
            for item in items
            for limitation in item.limitations
        )
    )
    if len(current) > len(items):
        limitations = (*limitations, "bounded_non_overlapping_selection")
    return FinancialDecisionContext(
        sector_framework=framework,
        evidence_items=items,
        limitations=limitations,
        eligible_input_count=len(with_values),
        selected_input_count=len(items),
        suppressed_input_count=suppressed,
    )


def compact_financial_decision_context(
    context: FinancialDecisionContext | None,
    *,
    aliases_by_ref: Mapping[str, str],
) -> dict[str, object] | None:
    if context is None:
        return None
    payload = context.model_dump(mode="json")
    rows = []
    for item in context.evidence_items:
        alias = aliases_by_ref.get(item.evidence_id)
        if alias is None:
            raise ValueError(f"selected_financial_ref_missing_alias:{item.evidence_id}")
        row = item.model_dump(mode="json")
        row["evidence_id"] = alias
        rows.append(row)
    payload["evidence_items"] = rows
    return payload


def _comparison_relation(item: FinancialDecisionEvidenceItem) -> str | None:
    if item.comparison is None or item.comparison.comparison_value is None:
        return None
    if item.value > item.comparison.comparison_value:
        return "higher"
    if item.value < item.comparison.comparison_value:
        return "lower"
    return "unchanged"


def neutral_financial_evidence_statement(
    item: FinancialDecisionEvidenceItem,
) -> str:
    label = _FINANCIAL_METRIC_LABELS.get(
        item.metric,
        item.metric.replace("_", " "),
    )
    status = (
        "Reported"
        if item.evidence_status == FinancialEvidenceStatus.DIRECT_REPORTED
        else "Safely derived"
    )
    period_end = item.period.end.isoformat()
    if item.period.type == FinancialPeriodType.POINT_IN_TIME:
        subject = f"{status} {label} balance as of {period_end}"
    else:
        subject = (
            f"{status} {label} for {item.period.type.value} ending {period_end}"
        )

    relation = _comparison_relation(item)
    if relation is None or item.comparison is None:
        return subject + "."
    comparison = _FINANCIAL_COMPARISON_LABELS[item.comparison.kind]
    return f"{subject} is {relation} than the {comparison}."


def first_class_financial_evidence_projection(
    context: FinancialDecisionContext | None,
) -> dict[str, dict[str, object]]:
    if context is None:
        return {}
    rows: dict[str, dict[str, object]] = {}
    for item in context.evidence_items:
        if item.evidence_id in rows:
            raise ValueError(
                f"duplicate_selected_financial_evidence:{item.evidence_id}"
            )
        rows[item.evidence_id] = {
            "evidence_kind": FIRST_CLASS_FINANCIAL_EVIDENCE_KIND,
            "statement": neutral_financial_evidence_statement(item),
            "value": str(item.value),
            "financial_semantics": {
                "metric": item.metric,
                "semantic_category": item.semantic_category.value,
                "period_type": item.period.type.value,
                "comparison_kind": (
                    item.comparison.kind.value
                    if item.comparison is not None
                    else None
                ),
                "evidence_status": item.evidence_status.value,
                "quality": item.quality.value,
            },
        }
    return rows


def _claim_rows(value: object) -> list[tuple[str, tuple[str, ...]]]:
    rows: list[tuple[str, tuple[str, ...]]] = []

    def collect(item: object) -> None:
        if isinstance(item, Mapping):
            refs = item.get("evidence_refs")
            refs_tuple = (
                tuple(str(ref) for ref in refs)
                if isinstance(refs, Sequence) and not isinstance(refs, (str, bytes))
                else ()
            )
            for key in ("text", "summary"):
                text = item.get(key)
                if isinstance(text, str) and text.strip():
                    rows.append((text, refs_tuple))
            for child in item.values():
                collect(child)
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes)):
            for child in item:
                collect(child)

    collect(value)
    return rows


def _period_claim_rows(value: object) -> list[tuple[str, tuple[str, ...]]]:
    rows: list[tuple[str, tuple[str, ...]]] = []

    def refs_for(item: Mapping[object, object], key: str) -> tuple[str, ...]:
        raw = item.get(key)
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
            return ()
        return tuple(str(ref) for ref in raw)

    def collect(item: object) -> None:
        if isinstance(item, Mapping):
            direct_refs = refs_for(item, "evidence_refs")
            for key in ("text", "summary"):
                text = item.get(key)
                if isinstance(text, str) and text.strip():
                    rows.append((text, direct_refs))
            for text_key, refs_key in (
                (
                    "confirmation_business_condition",
                    "confirmation_business_condition_refs",
                ),
                (
                    "business_invalidation_condition",
                    "business_invalidation_condition_refs",
                ),
            ):
                text = item.get(text_key)
                if isinstance(text, str) and text.strip():
                    rows.append((text, refs_for(item, refs_key)))
            for child in item.values():
                collect(child)
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes)):
            for child in item:
                collect(child)

    collect(value)
    return rows


def _normalized_period_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"\s+", " ", normalized).strip()


def _matches_period_family(
    text: str,
    patterns: Sequence[re.Pattern[str]],
) -> bool:
    return any(pattern.search(text) is not None for pattern in patterns)


def validate_qtd_ytd_conflict_semantics(
    candidate: object,
    *,
    supplied_refs: Sequence[DecisionEvidenceRef],
    required_ref_ids: Sequence[str],
) -> QtdYtdConflictValidation:
    """Require one evidence-linked claim to distinguish comparable QTD and YTD facts."""

    required = set(required_ref_ids)
    by_metric: dict[str, dict[FinancialPeriodType, set[str]]] = {}
    for ref in supplied_refs:
        context = ref.financial_context
        if ref.ref_id not in required or context is None:
            continue
        if context.period.type not in {
            FinancialPeriodType.QTD,
            FinancialPeriodType.YTD,
        }:
            continue
        by_metric.setdefault(context.metric, {}).setdefault(
            context.period.type, set()
        ).add(ref.ref_id)

    required_metrics = tuple(
        sorted(
            metric
            for metric, periods in by_metric.items()
            if periods.get(FinancialPeriodType.QTD)
            and periods.get(FinancialPeriodType.YTD)
        )
    )
    qtd_refs = {
        ref
        for metric in required_metrics
        for ref in by_metric[metric][FinancialPeriodType.QTD]
    }
    ytd_refs = {
        ref
        for metric in required_metrics
        for ref in by_metric[metric][FinancialPeriodType.YTD]
    }
    if not required_metrics:
        return QtdYtdConflictValidation(
            required=False,
            valid=True,
            errors=(),
            qtd_evidence_ref_count=len(qtd_refs),
            ytd_evidence_ref_count=len(ytd_refs),
        )

    payload = (
        candidate.model_dump(mode="json")
        if hasattr(candidate, "model_dump")
        else candidate
    )
    linked_claim_count = 0
    explicit_claim_count = 0
    for text, refs in _period_claim_rows(payload):
        claim_refs = set(refs)
        linked_metrics = tuple(
            metric
            for metric in required_metrics
            if claim_refs & by_metric[metric][FinancialPeriodType.QTD]
            and claim_refs & by_metric[metric][FinancialPeriodType.YTD]
        )
        if not linked_metrics:
            continue
        linked_claim_count += 1
        normalized = _normalized_period_text(text)
        if (
            _matches_period_family(normalized, _QTD_PERIOD_PATTERNS)
            and _matches_period_family(normalized, _YTD_PERIOD_PATTERNS)
            and _matches_period_family(normalized, _PERIOD_RELATION_PATTERNS)
        ):
            explicit_claim_count += 1

    errors = (() if explicit_claim_count else ("qtd_ytd_conflict_not_explicit",))
    return QtdYtdConflictValidation(
        required=True,
        valid=not errors,
        errors=errors,
        required_metrics=required_metrics,
        qtd_evidence_ref_count=len(qtd_refs),
        ytd_evidence_ref_count=len(ytd_refs),
        linked_claim_count=linked_claim_count,
        explicit_claim_count=explicit_claim_count,
    )


def validate_directional_financial_semantics(
    candidate: object,
    *,
    supplied_refs: Sequence[DecisionEvidenceRef],
    allowed_ref_ids: Sequence[str],
    sector_framework: object = None,
) -> FinancialSemanticValidation:
    payload = (
        candidate.model_dump(mode="json")
        if hasattr(candidate, "model_dump")
        else candidate
    )
    financial = {
        ref.ref_id: ref.financial_context
        for ref in supplied_refs
        if ref.financial_context is not None
    }
    allowed = set(allowed_ref_ids)
    errors: list[str] = []
    counts = {
        "invalid_financial_reference_count": 0,
        "partial_capex_called_fcf_count": 0,
        "year_end_as_yoy_count": 0,
        "partial_debt_total_claim_count": 0,
        "normalized_earnings_claim_violation_count": 0,
        "financial_sector_generic_financial_context_leak_count": 0,
        "fixed_financial_score_rule_count": 0,
    }
    financial_sector = sector_requires_specialized_financial_framework(sector_framework)
    for text, refs in _claim_rows(payload):
        invalid = [ref for ref in refs if ref not in allowed]
        if invalid:
            counts["invalid_financial_reference_count"] += len(invalid)
            errors.append("invalid_financial_evidence_reference")
        contexts = [financial[ref] for ref in refs if ref in financial]
        metrics = {context.metric for context in contexts}
        folded = text.casefold()

        if (
            ("fcf" in folded or "잉여현금흐름" in text)
            and "ocf_less_ppe_capex" in metrics
        ):
            counts["partial_capex_called_fcf_count"] += 1
            errors.append("ppe_only_cash_conversion_proxy_called_fcf")

        comparison_kinds = {
            context.comparison.kind
            for context in contexts
            if context.comparison is not None
        }
        yoy_language = any(
            token in folded
            for token in ("yoy", "year-over-year", "전년 동기", "전년대비", "전년 대비")
        )
        if (
            yoy_language
            and FinancialComparisonKind.PRIOR_YEAR_END in comparison_kinds
            and FinancialComparisonKind.PRIOR_YEAR_COMPARABLE not in comparison_kinds
        ):
            counts["year_end_as_yoy_count"] += 1
            errors.append("prior_year_end_described_as_yoy")

        net_debt_language = any(
            claim.framework == "net_debt" and claim.kind != FrameworkClaimKind.EXPLICIT_EXCLUSION
            for claim in financial_framework_claims(text)
        )
        total_debt_language = any(
            token in folded for token in ("total debt", "총부채", "전체 부채")
        )
        if net_debt_language and "net_debt" not in metrics:
            counts["partial_debt_total_claim_count"] += 1
            errors.append("net_debt_claim_without_complete_net_debt_evidence")
        if total_debt_language and "interest_bearing_debt_total" not in metrics:
            counts["partial_debt_total_claim_count"] += 1
            errors.append("total_debt_claim_without_complete_debt_evidence")

        normalized_language = any(
            token in folded
            for token in (
                "normalized earnings",
                "adjusted earnings",
                "normalized net income",
                "adjusted net income",
                "normalized eps",
                "adjusted eps",
                "정상화 이익",
                "조정 이익",
                "정상화 순이익",
                "조정 순이익",
            )
        )
        explicit_normalized_metric = any(
            "normalized" in metric or "adjusted" in metric for metric in metrics
        )
        if normalized_language and not explicit_normalized_metric:
            counts["normalized_earnings_claim_violation_count"] += 1
            errors.append("normalized_or_adjusted_earnings_without_explicit_metric")

        if financial_sector and contexts:
            counts["financial_sector_generic_financial_context_leak_count"] += 1
            errors.append("financial_sector_generic_financial_context_used")

        fixed_score_language = bool(
            re.search(r"(?:\+|-)[ ]*1(?:\.0)?(?:점)?", text)
            or ("score" in folded and any(metric in folded for metric in metrics))
            or ("점수" in text and bool(metrics))
        )
        if fixed_score_language:
            counts["fixed_financial_score_rule_count"] += 1
            errors.append("fixed_financial_scorecard_language")

    if financial_sector:
        applications = [
            claim for claim in candidate_financial_framework_claims(payload)
            if claim.kind != FrameworkClaimKind.EXPLICIT_EXCLUSION
        ]
        if applications:
            counts["financial_sector_generic_financial_context_leak_count"] += len(applications)
            errors.append("financial_sector_generic_reasoning")
        anchors = payload.get("material_directional_anchor_basis", ()) if isinstance(payload, Mapping) else ()
        if isinstance(anchors, (list, tuple)) and any(ref in financial for ref in anchors):
            counts["financial_sector_generic_financial_context_leak_count"] += 1
            errors.append("financial_sector_industrial_financial_anchor_used")

    unique_errors = tuple(dict.fromkeys(errors))
    return FinancialSemanticValidation(
        valid=not unique_errors,
        errors=unique_errors,
        **counts,
    )
