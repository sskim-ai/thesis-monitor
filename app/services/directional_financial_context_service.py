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
from app.services.configured_signal_evidence_service import (
    build_configured_signal_evidence_view,
    validate_configured_signal_field_ownership,
)
from app.services.configured_financial_support_concept_service import (
    configured_financial_support_concepts,
)
from app.services.financial_framework_claim_service import (
    FrameworkClaim,
    FrameworkClaimKind,
    FrameworkReferenceRole,
    candidate_financial_framework_claims,
    framework_reference_is_application,
    local_financial_claim_spans,
)


CONTRACT_VERSION = "directional-financial-decision-context-v1"
VALIDATOR_CONTRACT = "directional-financial-semantic-validator-v1"
QTD_YTD_VALIDATOR_CONTRACT = "directional-financial-qtd-ytd-validator-v1"
PPE_PROXY_FCF_CLAIM_CONTRACT = "ppe-proxy-fcf-claim-polarity-v1"
FINANCIAL_CLAIM_ROW_CONTRACT = "financial-claim-row-v2"
PROSPECTIVE_CONDITION_NOMINALIZATION_CONTRACT = (
    "prospective-financial-condition-nominalization-v1"
)
PROSPECTIVE_MONITORING_OBLIGATION_CONTRACT = (
    "prospective-financial-monitoring-obligation-v1"
)
FCF_TEMPORAL_CLAIM_SPAN_CONTRACT = "fcf-temporal-claim-span-v1"
CURRENT_FULFILLMENT_POLARITY_CONTRACT = "current-fulfillment-polarity-v1"
FCF_PROSPECTIVE_REQUIREMENT_CONTRACT = "fcf-prospective-requirement-v1"
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


class FinancialClaimRole(StrEnum):
    CURRENT_STATE_ASSERTION = "CURRENT_STATE_ASSERTION"
    CURRENT_DIRECTIONAL_BASIS = "CURRENT_DIRECTIONAL_BASIS"
    CURRENT_NUMERIC_CLAIM = "CURRENT_NUMERIC_CLAIM"
    CONFIGURED_CONDITIONAL_CHECK = "CONFIGURED_CONDITIONAL_CHECK"
    FUTURE_REEVALUATION_CONDITION = "FUTURE_REEVALUATION_CONDITION"
    INVALIDATION_CONDITION = "INVALIDATION_CONDITION"
    PROSPECTIVE_RISK_SCENARIO = "PROSPECTIVE_RISK_SCENARIO"
    PROSPECTIVE_VERIFICATION_REQUIREMENT = (
        "PROSPECTIVE_VERIFICATION_REQUIREMENT"
    )
    UNKNOWN_OR_AMBIGUOUS = "UNKNOWN_OR_AMBIGUOUS"


class CurrentFulfillmentPolarity(StrEnum):
    AFFIRMATIVE_CURRENT_FULFILLMENT = "AFFIRMATIVE_CURRENT_FULFILLMENT"
    NEGATED_CURRENT_FULFILLMENT = "NEGATED_CURRENT_FULFILLMENT"
    CURRENT_SCOPE_MARKER_ONLY = "CURRENT_SCOPE_MARKER_ONLY"
    NONE = "NONE"
    AMBIGUOUS = "AMBIGUOUS"


class PPEProxyFCFClaimRole(StrEnum):
    AFFIRMATIVE_FCF_ATTRIBUTION = "AFFIRMATIVE_FCF_ATTRIBUTION"
    NUMERIC_FCF_ATTRIBUTION = "NUMERIC_FCF_ATTRIBUTION"
    PROXY_AS_FCF_ATTRIBUTION = "PROXY_AS_FCF_ATTRIBUTION"
    PROXY_DESCRIPTIVE_CASH_CONVERSION = "PROXY_DESCRIPTIVE_CASH_CONVERSION"
    EXPLICIT_NOT_FCF_DISCLAIMER = "EXPLICIT_NOT_FCF_DISCLAIMER"
    UNKNOWN_OR_AMBIGUOUS = "UNKNOWN_OR_AMBIGUOUS"


class PPEProxyFCFClaimSpan(FrozenModel):
    contract: str = PPE_PROXY_FCF_CLAIM_CONTRACT
    role: PPEProxyFCFClaimRole
    text: str
    start: int
    end: int


class FinancialClaimFieldRole(StrEnum):
    CURRENT_CORE_CLAIM = "CURRENT_CORE_CLAIM"
    FUTURE_REEVALUATION_CONDITION = "FUTURE_REEVALUATION_CONDITION"
    STANCE_CONFIRMATION_CONDITION = "STANCE_CONFIRMATION_CONDITION"
    STANCE_INVALIDATION_CONDITION = "STANCE_INVALIDATION_CONDITION"
    STANCE_SUMMARY = "STANCE_SUMMARY"
    RISK_CONTEXT = "RISK_CONTEXT"
    UNKNOWN = "UNKNOWN"


class FinancialClaimRow(FrozenModel):
    contract: str = FINANCIAL_CLAIM_ROW_CONTRACT
    field_path: str
    text: str
    bound_evidence_refs: tuple[str, ...] = ()
    field_semantic_role: FinancialClaimFieldRole


class FCFTemporalClaimSpan(FrozenModel):
    contract: str = FCF_TEMPORAL_CLAIM_SPAN_CONTRACT
    framework: str = "free_cash_flow"
    field_path: str
    full_field_text: str
    local_clause_text: str
    local_clause_start: int
    local_clause_end: int
    term_text: str
    term_start: int
    term_end: int
    bound_evidence_refs: tuple[str, ...] = ()
    span_contract: str


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
    explicit_not_fcf_disclaimer_count: int = 0
    affirmative_proxy_as_fcf_violation_count: int = 0
    unsupported_current_fcf_claim_count: int = 0
    prospective_fcf_requirement_directional_violation_count: int = 0
    year_end_as_yoy_count: int = 0
    partial_debt_total_claim_count: int = 0
    normalized_earnings_claim_violation_count: int = 0
    financial_sector_generic_financial_context_leak_count: int = 0
    fixed_financial_score_rule_count: int = 0
    configured_signal_count: int = 0
    configured_only_current_driver_violation_count: int = 0
    configured_signal_false_fulfillment_count: int = 0


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

_CONDITIONAL_FINANCIAL_LANGUAGE = re.compile(
    r"(?:라면|다면|하면|되면|나면|으면|경우|때|시에|확인\s*후|"
    r"\bif\b|\bwhen\b|\bunless\b|\bwould\b)",
    re.IGNORECASE,
)
_CURRENT_SCOPE_MARKER_LANGUAGE = re.compile(
    r"(?:현재(?:까지)?|이미|지금|아직)|\b(?:currently|now|already|yet)\b",
    re.IGNORECASE,
)
_CURRENT_FULFILLMENT_LANGUAGE = re.compile(
    r"(?:(?:현재|이미|지금)\s+[^.!?;:\n]{0,24}?(?:확인|충족)된)|"
    r"(?:증가했|증가해|늘었|상승했|개선됐|개선되었|개선했다|"
    r"악화됐|악화되었|악화돼(?!야)|높아졌|발생했|나타났|"
    r"확인됐|확인돼(?!야)|확인되어(?!야)|확인되었|약화됐|약화되었|커졌|"
    r"입증됐|입증되었|증명됐|증명되었|검증됐|검증되었|"
    r"확대됐|확대되었|감소했|하락했|줄었|"
    r"충족됐|충족되었|충족했)|"
    r"\b(?:has|have|had)\s+(?:already\s+)?"
    r"(?:increased|risen|improved|worsened|weakened|deteriorated|declined|decreased|fallen)\b|"
    r"\b(?:has|have|had)\s+(?:been\s+)?"
    r"(?:confirmed|demonstrated|proven|verified)\b|"
    r"\b(?:has|have|had)\s+occurred\b|"
    r"\b(?:has|have|had)\s+(?:been\s+)?(?:fulfilled|met|triggered)\b|"
    r"\b(?:is|are|was|were)\s+(?:already\s+)?(?:fulfilled|met|triggered)\b|"
    r"\b(?:increased|rose|improved|worsened|weakened|deteriorated|declined|decreased|fell)\b"
    r".{0,24}\b(?:and|is|was)\b|"
    r"\b(?:is|are)\s+(?:weighing|pressuring|hurting)\b",
    re.IGNORECASE,
)
_NEGATED_CURRENT_FULFILLMENT_LANGUAGE = re.compile(
    r"(?:현재(?:까지)?|아직)[^.!?;:\n]{0,32}?"
    r"(?:충족|확인|입증|증명|검증)(?:된|되지는|되지|되지도|되지가)?"
    r"[^.!?;:\n]{0,28}?"
    r"(?:아니(?:다|며|고|지만|라고)|않(?:았|았다|았습니다|는다|음))|"
    r"(?:현재\s*)?(?:FCF|free[ -]cash[ -]flow|잉여현금흐름)"
    r"(?:이|가|은|는)?[^.!?;:\n]{0,24}?"
    r"(?:개선|증가|회복)(?:됐다는|되었다는|했다는)\s*"
    r"(?:증거|근거)(?:는|가)?\s*없(?:다|습니다)|"
    r"\b(?:is\s+not\s+currently|isn't\s+currently|not\s+currently)\s+"
    r"(?:fulfilled|met|confirmed|triggered)\b|"
    r"\b(?:has|have|had)\s+not\s+(?:been\s+)?"
    r"(?:fulfilled|met|confirmed|triggered)\b",
    re.IGNORECASE,
)
_FULFILLMENT_TERM_LANGUAGE = re.compile(
    r"(?:충족|확인)|\b(?:fulfill(?:ed|ment)?|met|confirm(?:ed|ation)?|triggered)\b",
    re.IGNORECASE,
)
_CURRENT_MAGNITUDE_LANGUAGE = re.compile(
    r"(?:높은|과도한|큰)\s*(?:순부채|부채|운전자본)|"
    r"(?:순부채|부채|운전자본)(?:\s*부담)?(?:이|가|은|는)?\s*"
    r"(?:높다|높아|높고|과도하다|과도하고|크다|크고)|"
    r"\b(?:net[ -]debt|leverage|working[ -]capital)\s+(?:is|remains|was)\s+"
    r"(?:currently\s+)?"
    r"(?:high|elevated|excessive)\b|"
    r"\bhigher\s+(?:net[ -]debt|leverage)\s+(?:is|remains)\s+"
    r"(?:weighing|pressuring|hurting)\b",
    re.IGNORECASE,
)
_CURRENT_FCF_STATE_LANGUAGE = re.compile(
    r"(?:현재\s*)?(?:(?<![A-Za-z0-9_])FCF(?![A-Za-z0-9_])|"
    r"(?<![A-Za-z0-9_])free[ -]cash[ -]flow(?![A-Za-z0-9_])|잉여현금흐름)"
    r"(?:이|가|은|는)?\s*(?:현재\s*)?"
    r"(?:음수|양수|약해|약하다|약합니다|부족해|부족하다|부족합니다|"
    r"부진해|부진하다|부진합니다)(?:다|이다|입니다)?|"
    r"현재\s*(?:영업)?현금흐름(?:이|가|은|는)?\s*"
    r"(?:약해|약하다|약합니다|부족해|부족하다|부족합니다|"
    r"부진해|부진하다|부진합니다)|"
    r"(?:\bFCF\b|\bfree[ -]cash[ -]flow\b)\s+"
    r"(?:is|remains|was)\s+(?:currently\s+)?"
    r"(?:negative|positive|weak|insufficient|depressed)\b",
    re.IGNORECASE,
)
_PROSPECTIVE_RISK_LANGUAGE = re.compile(
    r"(?:핵심|주요)?\s*(?:위험|리스크)|(?:위험|리스크)(?:이다|입니다|요인|시나리오)|"
    r"가능성|모니터링|동반\s*발생|겹치는\s*(?:경우|상황)|늘어나는\s*(?:경우|상황)|"
    r"\b(?:key|major)\s+risk\b|\brisk\s+of\b|\brisk\s+scenario\b|"
    r"\b(?:monitor|monitoring|possibility|scenario)\b|"
    r"\balongside\b|\bwhile\b",
    re.IGNORECASE,
)
_EXPLICIT_LOCAL_FUTURE_LANGUAGE = re.compile(
    r"(?:향후|앞으로|추후|미래(?:의|에)?|장래(?:의|에)?)|"
    r"\b(?:future|prospective|going[ -]forward)\b",
    re.IGNORECASE,
)
_KOREAN_NOMINALIZED_PROSPECTIVE_CONDITION = re.compile(
    r"(?:확인|발생|증가|감소|악화|저하|약화|확대|축소|회복)"
    r"(?:의|은|는|이|가)?[^.!?;:\n]{0,56}?"
    r"(?:추가\s*)?(?:하향(?:\s*재평가)?|재평가|무효화|훼손|약화|위험|"
    r"모니터링할\s*약화)?\s*(?:조건|기준|트리거)",
    re.IGNORECASE,
)
_ENGLISH_NOMINALIZED_PROSPECTIVE_CONDITION = re.compile(
    r"(?:\b(?:confirmation|occurrence)\s+of\b|"
    r"\b(?:increase|decrease|deterioration|worsening|weakening|decline)\b)"
    r"[^.!?;:\n]{0,72}?\b(?:is|would\s+be)\b\s+"
    r"(?:an?\s+)?(?:monitored\s+)?(?:downside\s+|weakening\s+|"
    r"reevaluation\s+|invalidation\s+)?(?:condition|criterion|trigger)\b",
    re.IGNORECASE,
)
_PROSPECTIVE_MONITORING_OBLIGATION_FAMILIES = (
    (
        "KOREAN_GAMSI",
        re.compile(r"감시(?:해야\s*한다|할\s*필요가\s*있다|한다)", re.IGNORECASE),
    ),
    (
        "KOREAN_MONITORING",
        re.compile(
            r"모니터링(?:해야\s*한다|할\s*필요가\s*있다|한다)",
            re.IGNORECASE,
        ),
    ),
    (
        "KOREAN_JUSI",
        re.compile(r"주시(?:해야\s*한다|할\s*필요가\s*있다|한다)", re.IGNORECASE),
    ),
    (
        "KOREAN_TRACK",
        re.compile(r"추적(?:해야\s*한다|할\s*필요가\s*있다|한다)", re.IGNORECASE),
    ),
    (
        "KOREAN_INSPECT",
        re.compile(r"점검(?:해야\s*한다|할\s*필요가\s*있다|한다)", re.IGNORECASE),
    ),
    (
        "ENGLISH_MONITOR",
        re.compile(
            r"(?:\bmonitor\s+whether\b|"
            r"\b(?:should|must|needs?\s+to)\s+(?:be\s+)?(?:monitor(?:ed)?|"
            r"track(?:ed)?|watch(?:ed)?|review(?:ed)?)\b|"
            r"\bneeds?\s+(?:monitoring|tracking|watching|review)\b)",
            re.IGNORECASE,
        ),
    ),
)
_FOLLOWING_CONDITION_FULFILLMENT = re.compile(
    r"^\s*(?:이며|이고|이고는|이며는)?\s*(?:현재|이미|지금)(?:\s+이미)?"
    r"[^.!?;:\n]{0,32}(?:충족됐|충족되었|충족했)|"
    r"^\s*(?:and\s+)?(?:it|the\s+condition)?\s*"
    r"(?:is|was|has\s+been)\s+(?:already\s+)?(?:fulfilled|met|triggered)\b",
    re.IGNORECASE,
)
_ALWAYS_CURRENT_DIRECTION_PATHS = (
    "buy_drivers",
    "sell_drivers",
    "dominant_evidence",
    "core_investment_judgment",
    "material_directional_anchor_basis",
)
_PROSPECTIVE_REQUIREMENT_DIRECTIONAL_PATHS = (
    "buy_drivers",
    "sell_drivers",
    "dominant_evidence",
)
_RISK_CONTEXT_PATH = "risk_context"
_FUTURE_REEVALUATION_PATH = "business_reevaluation"
_INVALIDATION_PATH = "business_invalidation_condition"
_CONFIGURED_PROSPECTIVE_SOURCE_REFS = frozenset(
    {
        "stock.thesis.strengthen_signals",
        "stock.thesis.weaken_signals",
        "stock.thesis.invalidation_signals",
    }
)

_FCF_TERM = re.compile(
    r"(?<![A-Za-z0-9_])FCF(?![A-Za-z0-9_])|"
    r"(?<![A-Za-z0-9_])free[ -]cash[ -]flow(?![A-Za-z0-9_])|잉여현금흐름",
    re.IGNORECASE,
)
_FCF_CLAUSE_BOUNDARY = re.compile(
    r"(?:[.!?;:\n]+|[,，]?\s*(?:하지만|그러나|다만|반면|그렇지만|"
    r"but|however|yet)\s+)",
    re.IGNORECASE,
)
_FCF_NEGATION_BEFORE = re.compile(
    r"(?:\bnot\b|\bnever\b|\bis\s+not\b|\bisn't\b|\bshould\s+not\b|"
    r"\bmust\s+not\b|\bcannot\b|\bcan't\b|\bdo\s+not\b|\bdon't\b|"
    r"아닌|아니며|아니고|부르지\s*않는|보지\s*않는|간주하지\s*않는)"
    r"[^.!?;:\n]{0,48}$",
    re.IGNORECASE,
)
_FCF_NEGATION_AFTER = re.compile(
    r"^[^.!?;:\n]{0,48}(?:아니다|아닙니다|아님|아닌\s+지표|"
    r"라고\s*부르지\s*않|로\s*부르지\s*않|로\s*보지\s*않|"
    r"로\s*간주하지\s*않|\bis\s+not\b|\bisn't\b|"
    r"\bshould\s+not\s+be\s+called\b)",
    re.IGNORECASE,
)
_FCF_AMBIGUOUS = re.compile(
    r"(?:인지|여부|확인\s*필요|알\s*수\s*없|불분명|불확실|"
    r"\bwhether\b|\bunclear\b|\bunknown\b)",
    re.IGNORECASE,
)
_FCF_UNCONFIRMED_REQUIREMENT = re.compile(
    r"(?:아직[^.!?;:\n]{0,48}(?:확인되지|미확인|미검증)|"
    r"(?:확인|검증)(?:이|가)?\s*(?:필요|되어야)|"
    r"(?:재가속|개선|증가|회복)(?:이|가|은|는)?\s*(?:필요|되어야)|"
    r"\b(?:not yet confirmed|requires? confirmation|must be confirmed|"
    r"needs? to (?:improve|reaccelerate|recover))\b)",
    re.IGNORECASE,
)
_FCF_PROSPECTIVE_REQUIREMENT_FAMILIES = (
    (
        "KOREAN_OUTCOME_REQUIREMENT",
        re.compile(
            r"(?:이어져|연결되어|나타나|상쇄해|상쇄되어)야\s*"
            r"(?:한다|합니다|함|할\s*필요가\s*있다)?",
            re.IGNORECASE,
        ),
    ),
    (
        "KOREAN_VERIFICATION_REQUIREMENT",
        re.compile(
            r"(?:확인|입증|증명|검증)"
            r"(?:(?:이|가|은|는)?\s*필요(?:하다|합니다|함|한)|"
            r"(?:되어|돼|되)야\s*(?:한다|합니다|함)?|"
            r"해야\s*(?:한다|합니다|함)?)",
            re.IGNORECASE,
        ),
    ),
    (
        "KOREAN_IMPROVEMENT_REQUIREMENT",
        re.compile(
            r"(?:개선|회복|증가)(?:이|가|은|는)?\s*"
            r"필요(?:하다|합니다|함|한)",
            re.IGNORECASE,
        ),
    ),
    (
        "ENGLISH_OUTCOME_REQUIREMENT",
        re.compile(
            r"\b(?:must|needs?\s+to|has\s+to)\s+"
            r"(?:translate\s+into|flow\s+through\s+to|show\s+up\s+in|offset)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "ENGLISH_VERIFICATION_REQUIREMENT",
        re.compile(
            r"\bneeds?\s+to\s+be\s+"
            r"(?:demonstrated|confirmed|proven|verified)\b|"
            r"\b(?:proof|evidence)(?:\s+of\b[^.!?;:\n]{0,64})?\s+"
            r"(?:is\s+)?(?:still\s+)?(?:needed|required)\b|"
            r"\b(?:thesis|market)\b[^.!?;:\n]{0,64}\b"
            r"requires?\b[^.!?;:\n]{0,64}\b(?:proof|evidence)\b|"
            r"\b(?:FCF|free[ -]cash[ -]flow)\s+improvement\s+"
            r"(?:is\s+)?(?:still\s+)?(?:needed|required)\b",
            re.IGNORECASE,
        ),
    ),
)
_FCF_NUMERIC = re.compile(
    r"(?:[$€£₩]|\b(?:usd|krw|eur|million|billion|mn|bn)\b|"
    r"\d[\d,.]*\s*(?:억|조|만|m|b)?)",
    re.IGNORECASE,
)
_FCF_PROXY_AS_FCF = re.compile(
    r"(?:사실상\s*(?:FCF|잉여현금흐름)|(?:FCF|잉여현금흐름)(?:로|이라고)\s*"
    r"(?:본|보|간주|부르)|OCF\s*[-−]\s*PPE[^.!?;:\n]{0,20}FCF|"
    r"\b(?:treat|regard|call|consider)(?:s|ed)?\b[^.!?;:\n]{0,32}"
    r"\b(?:FCF|free[ -]cash[ -]flow)\b)",
    re.IGNORECASE,
)
_PROXY_DESCRIPTIVE_CASH_CONVERSION = re.compile(
    r"(?:유형자산\s*취득|PPE\s*(?:acquisition|purchase)|"
    r"OCF\s*(?:less|대비)|현금\s*전환\s*대용치|cash[- ]conversion\s*proxy)",
    re.IGNORECASE,
)


def _configured_prospective_evidence(ref: DecisionEvidenceRef) -> bool:
    source_ref = ref.source_ref.casefold()
    configured_source = any(
        source_ref == expected or source_ref.startswith(f"{expected}.")
        for expected in _CONFIGURED_PROSPECTIVE_SOURCE_REFS
    )
    return configured_source and ref.financial_context is None


def _claim_has_only_configured_prospective_evidence(
    claim: FrameworkClaim,
    evidence_by_ref: Mapping[str, DecisionEvidenceRef] | None,
) -> bool:
    if evidence_by_ref is None or not claim.evidence_refs:
        return False
    refs = [evidence_by_ref.get(ref_id) for ref_id in claim.evidence_refs]
    return all(
        ref is not None and _configured_prospective_evidence(ref) for ref in refs
    )


def _claim_has_framework_relevant_configured_evidence(
    claim: FrameworkClaim,
    evidence_by_ref: Mapping[str, DecisionEvidenceRef] | None,
) -> bool:
    if evidence_by_ref is None or not claim.evidence_refs:
        return False
    for ref_id in claim.evidence_refs:
        ref = evidence_by_ref.get(ref_id)
        if ref is None or not _configured_prospective_evidence(ref):
            continue
        if claim.framework in configured_financial_support_concepts(ref):
            return True
    return False


def _is_nominalized_prospective_condition(text: str) -> bool:
    return bool(
        _KOREAN_NOMINALIZED_PROSPECTIVE_CONDITION.search(text)
        or _ENGLISH_NOMINALIZED_PROSPECTIVE_CONDITION.search(text)
    )


def _prospective_monitoring_obligation_family(text: str) -> str | None:
    normalized = unicodedata.normalize("NFKC", text)
    for family, pattern in _PROSPECTIVE_MONITORING_OBLIGATION_FAMILIES:
        if pattern.search(normalized):
            return family
    return None


def _is_prospective_monitoring_obligation(text: str) -> bool:
    return _prospective_monitoring_obligation_family(text) is not None


def fcf_prospective_requirement_family(text: str) -> str | None:
    """Return the bounded predicate family for a local prospective FCF clause."""

    normalized = unicodedata.normalize("NFKC", text)
    if not _FCF_TERM.search(normalized):
        return None
    if _FCF_UNCONFIRMED_REQUIREMENT.search(normalized):
        return "UNCONFIRMED_FCF_REQUIREMENT"
    for family, pattern in _FCF_PROSPECTIVE_REQUIREMENT_FAMILIES:
        if pattern.search(normalized):
            return family
    return None


def _current_fulfillment_matches(
    text: str,
) -> tuple[tuple[re.Match[str], ...], re.Match[str] | None, str]:
    normalized = unicodedata.normalize("NFKC", text)
    negated = tuple(_NEGATED_CURRENT_FULFILLMENT_LANGUAGE.finditer(normalized))
    unnegated = list(normalized)
    for match in negated:
        unnegated[match.start() : match.end()] = " " * (match.end() - match.start())
    remaining = "".join(unnegated)
    return negated, _CURRENT_FULFILLMENT_LANGUAGE.search(remaining), remaining


def current_fulfillment_polarity(text: str) -> CurrentFulfillmentPolarity:
    """Classify current fulfillment without letting local negation leak."""

    negated, affirmative, remaining = _current_fulfillment_matches(text)
    if affirmative is not None:
        return CurrentFulfillmentPolarity.AFFIRMATIVE_CURRENT_FULFILLMENT
    if negated:
        return CurrentFulfillmentPolarity.NEGATED_CURRENT_FULFILLMENT
    if _CURRENT_SCOPE_MARKER_LANGUAGE.search(remaining):
        return CurrentFulfillmentPolarity.CURRENT_SCOPE_MARKER_ONLY
    if _FULFILLMENT_TERM_LANGUAGE.search(remaining):
        return CurrentFulfillmentPolarity.AMBIGUOUS
    return CurrentFulfillmentPolarity.NONE


def _has_following_condition_fulfillment(claim: FrameworkClaim) -> bool:
    full_text = claim.full_field_text
    if not full_text or claim.local_clause_end >= len(full_text):
        return False
    following = full_text[claim.local_clause_end :]
    return bool(_FOLLOWING_CONDITION_FULFILLMENT.search(following)) and (
        current_fulfillment_polarity(following)
        == CurrentFulfillmentPolarity.AFFIRMATIVE_CURRENT_FULFILLMENT
    )


def financial_claim_role(
    claim: FrameworkClaim,
    *,
    evidence_by_ref: Mapping[str, DecisionEvidenceRef] | None = None,
) -> FinancialClaimRole:
    """Classify assertion time/scope before requiring complete financial evidence."""

    path = claim.field_path.casefold()
    text = unicodedata.normalize("NFKC", claim.local_clause_text or claim.text)
    conditional = _CONDITIONAL_FINANCIAL_LANGUAGE.search(text)
    _negated_fulfillment, fulfilled, _unnegated_text = (
        _current_fulfillment_matches(text)
    )
    current_magnitude = _CURRENT_MAGNITUDE_LANGUAGE.search(text)
    if claim.framework == "free_cash_flow" and current_magnitude is None:
        current_magnitude = _CURRENT_FCF_STATE_LANGUAGE.search(text)
    configured_only = _claim_has_only_configured_prospective_evidence(
        claim, evidence_by_ref
    )
    framework_relevant_configured = (
        _claim_has_framework_relevant_configured_evidence(claim, evidence_by_ref)
    )
    explicit_local_future = _EXPLICIT_LOCAL_FUTURE_LANGUAGE.search(text)
    current_numeric = re.search(r"[-+]?\d[\d,.]*(?:\.\d+)?", text)
    nominalized_condition = _is_nominalized_prospective_condition(text)
    monitoring_obligation = _is_prospective_monitoring_obligation(text)
    fcf_requirement = (
        fcf_prospective_requirement_family(text)
        if claim.framework == "free_cash_flow"
        else None
    )
    following_condition_fulfillment = (
        nominalized_condition and _has_following_condition_fulfillment(claim)
    )
    if _RISK_CONTEXT_PATH in path and (
        fulfilled is not None
        or current_magnitude is not None
        or following_condition_fulfillment
    ):
        return FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS
    if conditional is not None and (
        fulfilled is None or fulfilled.start() >= conditional.start()
    ):
        if _FUTURE_REEVALUATION_PATH in path:
            return FinancialClaimRole.FUTURE_REEVALUATION_CONDITION
        if _INVALIDATION_PATH in path or "invalidation" in path:
            return FinancialClaimRole.INVALIDATION_CONDITION
        if _RISK_CONTEXT_PATH in path:
            if framework_relevant_configured:
                return FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO
            return FinancialClaimRole.UNKNOWN_OR_AMBIGUOUS
        return FinancialClaimRole.CONFIGURED_CONDITIONAL_CHECK
    if (
        _RISK_CONTEXT_PATH in path
        and nominalized_condition
        and current_numeric is not None
        and conditional is None
    ):
        return FinancialClaimRole.CURRENT_NUMERIC_CLAIM
    if (
        _RISK_CONTEXT_PATH in path
        and nominalized_condition
        and framework_relevant_configured
        and current_numeric is None
    ):
        return FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO
    if (
        _RISK_CONTEXT_PATH in path
        and monitoring_obligation
        and framework_relevant_configured
        and fulfilled is None
        and current_magnitude is None
        and current_numeric is None
    ):
        return FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO
    if (
        configured_only
        and fulfilled is None
        and current_magnitude is None
        and current_numeric is None
    ):
        if _FUTURE_REEVALUATION_PATH in path:
            return FinancialClaimRole.FUTURE_REEVALUATION_CONDITION
        if _INVALIDATION_PATH in path or "invalidation" in path:
            return FinancialClaimRole.INVALIDATION_CONDITION
        if _RISK_CONTEXT_PATH in path and framework_relevant_configured:
            return FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO
        if any(token in path for token in _ALWAYS_CURRENT_DIRECTION_PATHS):
            return FinancialClaimRole.CONFIGURED_CONDITIONAL_CHECK
    if (
        fcf_requirement is not None
        and fulfilled is None
        and current_magnitude is None
        and current_numeric is None
    ):
        return FinancialClaimRole.PROSPECTIVE_VERIFICATION_REQUIREMENT
    if current_numeric is not None:
        return FinancialClaimRole.CURRENT_NUMERIC_CLAIM
    if any(token in path for token in _ALWAYS_CURRENT_DIRECTION_PATHS):
        return FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS
    if _RISK_CONTEXT_PATH in path:
        if explicit_local_future is not None and framework_relevant_configured:
            return FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO
        if (
            _PROSPECTIVE_RISK_LANGUAGE.search(text)
            and _claim_has_only_configured_prospective_evidence(
                claim, evidence_by_ref
            )
        ):
            return FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO
        return FinancialClaimRole.UNKNOWN_OR_AMBIGUOUS
    if (
        _FUTURE_REEVALUATION_PATH in path
        and _claim_has_only_configured_prospective_evidence(claim, evidence_by_ref)
    ):
        return FinancialClaimRole.FUTURE_REEVALUATION_CONDITION
    if (
        (_INVALIDATION_PATH in path or "invalidation" in path)
        and _claim_has_only_configured_prospective_evidence(claim, evidence_by_ref)
    ):
        return FinancialClaimRole.INVALIDATION_CONDITION
    if claim.role == FrameworkReferenceRole.UNRESOLVED:
        return FinancialClaimRole.UNKNOWN_OR_AMBIGUOUS
    return FinancialClaimRole.CURRENT_STATE_ASSERTION


def financial_claim_requires_current_evidence(
    claim: FrameworkClaim,
    *,
    evidence_by_ref: Mapping[str, DecisionEvidenceRef] | None = None,
) -> bool:
    if not framework_reference_is_application(claim):
        return False
    return financial_claim_role(claim, evidence_by_ref=evidence_by_ref) in {
        FinancialClaimRole.CURRENT_STATE_ASSERTION,
        FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS,
        FinancialClaimRole.CURRENT_NUMERIC_CLAIM,
        FinancialClaimRole.UNKNOWN_OR_AMBIGUOUS,
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


def _financial_claim_field_role(
    *,
    field_path: str,
    field_name: str,
) -> FinancialClaimFieldRole:
    folded_path = field_path.casefold()
    if field_name == "confirmation_business_condition":
        return FinancialClaimFieldRole.STANCE_CONFIRMATION_CONDITION
    if field_name == "business_invalidation_condition":
        return FinancialClaimFieldRole.STANCE_INVALIDATION_CONDITION
    if field_name == "summary" and any(
        token in folded_path
        for token in ("new_buyer", "fundamental_new_buyer", "holder")
    ):
        return FinancialClaimFieldRole.STANCE_SUMMARY
    if "business_reevaluation" in folded_path or "reevaluation_" in folded_path:
        return FinancialClaimFieldRole.FUTURE_REEVALUATION_CONDITION
    if "risk_context" in folded_path:
        return FinancialClaimFieldRole.RISK_CONTEXT
    if "unknown" in folded_path or "uncertainty" in folded_path:
        return FinancialClaimFieldRole.UNKNOWN
    return FinancialClaimFieldRole.CURRENT_CORE_CLAIM


def financial_claim_rows(value: object) -> tuple[FinancialClaimRow, ...]:
    """Bind every financial prose field to only its sibling evidence references."""

    rows: list[FinancialClaimRow] = []

    def refs_for(item: Mapping[object, object], key: str) -> tuple[str, ...]:
        raw = item.get(key)
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
            return ()
        return tuple(str(ref) for ref in raw)

    def collect(item: object, path: str = "") -> None:
        if isinstance(item, Mapping):
            refs_tuple = refs_for(item, "evidence_refs")
            for key in ("text", "summary"):
                text = item.get(key)
                if isinstance(text, str) and text.strip():
                    field_path = f"{path}.{key}" if path else key
                    rows.append(
                        FinancialClaimRow(
                            field_path=field_path,
                            text=text,
                            bound_evidence_refs=refs_tuple,
                            field_semantic_role=_financial_claim_field_role(
                                field_path=field_path,
                                field_name=key,
                            ),
                        )
                    )
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
                    field_path = f"{path}.{text_key}" if path else text_key
                    rows.append(
                        FinancialClaimRow(
                            field_path=field_path,
                            text=text,
                            bound_evidence_refs=refs_for(item, refs_key),
                            field_semantic_role=_financial_claim_field_role(
                                field_path=field_path,
                                field_name=text_key,
                            ),
                        )
                    )
            for key, child in item.items():
                child_path = f"{path}.{key}" if path else str(key)
                collect(child, child_path)
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes)):
            for index, child in enumerate(item):
                collect(child, f"{path}[{index}]")

    collect(value)
    return tuple(rows)


def _claim_rows(value: object) -> list[FinancialClaimRow]:
    return list(financial_claim_rows(value))


def financial_claim_row_requires_current_fcf_evidence(
    row: FinancialClaimRow,
    *,
    evidence_by_ref: Mapping[str, DecisionEvidenceRef] | None = None,
) -> bool:
    """Distinguish present FCF assertions from configured or unconfirmed checks."""

    if row.field_semantic_role in {
        FinancialClaimFieldRole.FUTURE_REEVALUATION_CONDITION,
        FinancialClaimFieldRole.STANCE_CONFIRMATION_CONDITION,
        FinancialClaimFieldRole.STANCE_INVALIDATION_CONDITION,
        FinancialClaimFieldRole.UNKNOWN,
    }:
        return False
    if (
        row.field_semantic_role == FinancialClaimFieldRole.STANCE_SUMMARY
        and _FCF_UNCONFIRMED_REQUIREMENT.search(row.text)
    ):
        return False
    return any(
        fcf_temporal_claim_role(span, evidence_by_ref=evidence_by_ref)
        in {
            FinancialClaimRole.CURRENT_STATE_ASSERTION,
            FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS,
            FinancialClaimRole.CURRENT_NUMERIC_CLAIM,
            FinancialClaimRole.UNKNOWN_OR_AMBIGUOUS,
        }
        for span in fcf_temporal_claim_spans(row)
    )


def fcf_temporal_claim_spans(
    row: FinancialClaimRow,
) -> tuple[FCFTemporalClaimSpan, ...]:
    """Bind each FCF occurrence to the established local financial clause."""

    return tuple(
        FCFTemporalClaimSpan(
            field_path=row.field_path,
            full_field_text=span.full_field_text,
            local_clause_text=span.local_clause_text,
            local_clause_start=span.local_clause_start,
            local_clause_end=span.local_clause_end,
            term_text=span.term_text,
            term_start=span.term_start,
            term_end=span.term_end,
            bound_evidence_refs=row.bound_evidence_refs,
            span_contract=span.span_contract,
        )
        for span in local_financial_claim_spans(
            row.text,
            term_pattern=_FCF_TERM,
        )
    )


def fcf_temporal_claim_role(
    span: FCFTemporalClaimSpan,
    *,
    evidence_by_ref: Mapping[str, DecisionEvidenceRef] | None = None,
) -> FinancialClaimRole:
    """Classify one clause-local FCF occurrence without inheriting field tense."""

    return financial_claim_role(
        FrameworkClaim(
            framework=span.framework,
            kind=FrameworkClaimKind.ASSERTION_OR_APPLICATION,
            text=span.local_clause_text,
            field_path=span.field_path,
            evidence_refs=span.bound_evidence_refs,
            role=FrameworkReferenceRole.UNRESOLVED,
            full_field_text=span.full_field_text,
            local_clause_text=span.local_clause_text,
            local_clause_start=span.local_clause_start,
            local_clause_end=span.local_clause_end,
            span_contract=span.span_contract,
        ),
        evidence_by_ref=evidence_by_ref,
    )


def classify_ppe_proxy_fcf_claims(text: str) -> tuple[PPEProxyFCFClaimSpan, ...]:
    """Classify FCF wording with clause-local negation and polarity."""

    clauses: list[tuple[int, int, str]] = []
    start = 0
    for boundary in _FCF_CLAUSE_BOUNDARY.finditer(text):
        if boundary.start() > start:
            clauses.append((start, boundary.start(), text[start : boundary.start()]))
        start = boundary.end()
    if start < len(text):
        clauses.append((start, len(text), text[start:]))

    classified: list[PPEProxyFCFClaimSpan] = []
    for clause_start, clause_end, clause in clauses:
        terms = tuple(_FCF_TERM.finditer(clause))
        if not terms:
            if _PROXY_DESCRIPTIVE_CASH_CONVERSION.search(clause):
                classified.append(
                    PPEProxyFCFClaimSpan(
                        role=PPEProxyFCFClaimRole.PROXY_DESCRIPTIVE_CASH_CONVERSION,
                        text=clause.strip(),
                        start=clause_start,
                        end=clause_end,
                    )
                )
            continue

        for term in terms:
            before = clause[max(0, term.start() - 64) : term.start()]
            after = clause[term.end() : min(len(clause), term.end() + 64)]
            local = clause[
                max(0, term.start() - 64) : min(len(clause), term.end() + 64)
            ]
            if _FCF_NEGATION_BEFORE.search(before) or _FCF_NEGATION_AFTER.search(after):
                role = PPEProxyFCFClaimRole.EXPLICIT_NOT_FCF_DISCLAIMER
            elif _FCF_AMBIGUOUS.search(local):
                role = PPEProxyFCFClaimRole.UNKNOWN_OR_AMBIGUOUS
            elif _FCF_PROXY_AS_FCF.search(clause):
                role = PPEProxyFCFClaimRole.PROXY_AS_FCF_ATTRIBUTION
            elif _FCF_NUMERIC.search(local):
                role = PPEProxyFCFClaimRole.NUMERIC_FCF_ATTRIBUTION
            else:
                role = PPEProxyFCFClaimRole.AFFIRMATIVE_FCF_ATTRIBUTION
            classified.append(
                PPEProxyFCFClaimSpan(
                    role=role,
                    text=clause.strip(),
                    start=clause_start + term.start(),
                    end=clause_start + term.end(),
                )
            )
    return tuple(classified)


def _period_claim_rows(value: object) -> list[tuple[str, tuple[str, ...]]]:
    return [
        (row.text, row.bound_evidence_refs)
        for row in financial_claim_rows(value)
    ]


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
    evidence_by_ref = {ref.ref_id: ref for ref in supplied_refs}
    allowed = set(allowed_ref_ids)
    errors: list[str] = []
    counts = {
        "invalid_financial_reference_count": 0,
        "partial_capex_called_fcf_count": 0,
        "explicit_not_fcf_disclaimer_count": 0,
        "affirmative_proxy_as_fcf_violation_count": 0,
        "unsupported_current_fcf_claim_count": 0,
        "prospective_fcf_requirement_directional_violation_count": 0,
        "year_end_as_yoy_count": 0,
        "partial_debt_total_claim_count": 0,
        "normalized_earnings_claim_violation_count": 0,
        "financial_sector_generic_financial_context_leak_count": 0,
        "fixed_financial_score_rule_count": 0,
        "configured_signal_count": 0,
        "configured_only_current_driver_violation_count": 0,
        "configured_signal_false_fulfillment_count": 0,
    }
    configured_signal_view = build_configured_signal_evidence_view(
        ticker=str(payload.get("ticker") or "") if isinstance(payload, Mapping) else "",
        supplied_refs=supplied_refs,
    )
    configured_signal_validation = validate_configured_signal_field_ownership(
        payload,
        configured_signal_view,
    )
    errors.extend(configured_signal_validation.errors)
    counts["configured_signal_count"] = (
        configured_signal_validation.configured_signal_count
    )
    counts["configured_only_current_driver_violation_count"] = (
        configured_signal_validation.configured_only_current_driver_violation_count
    )
    counts["configured_signal_false_fulfillment_count"] = (
        configured_signal_validation.configured_signal_false_fulfillment_count
    )
    financial_sector = sector_requires_specialized_financial_framework(sector_framework)
    framework_claims = candidate_financial_framework_claims(
        payload,
        metric_by_ref={ref: context.metric for ref, context in financial.items()},
    )
    claims_by_path: dict[str, list[object]] = {}
    for claim in framework_claims:
        claims_by_path.setdefault(claim.field_path, []).append(claim)
    claim_rows = _claim_rows(payload)
    violation_roles = {
        PPEProxyFCFClaimRole.AFFIRMATIVE_FCF_ATTRIBUTION,
        PPEProxyFCFClaimRole.NUMERIC_FCF_ATTRIBUTION,
        PPEProxyFCFClaimRole.PROXY_AS_FCF_ATTRIBUTION,
    }
    for row in claim_rows:
        field_path = row.field_path
        text = row.text
        refs = row.bound_evidence_refs
        invalid = [ref for ref in refs if ref not in allowed]
        if invalid:
            counts["invalid_financial_reference_count"] += len(invalid)
            errors.append("invalid_financial_evidence_reference")
        contexts = [financial[ref] for ref in refs if ref in financial]
        metrics = {context.metric for context in contexts}
        folded = text.casefold()

        fcf_claims = classify_ppe_proxy_fcf_claims(text)
        counts["explicit_not_fcf_disclaimer_count"] += sum(
            claim.role == PPEProxyFCFClaimRole.EXPLICIT_NOT_FCF_DISCLAIMER
            for claim in fcf_claims
        )
        proxy_applies = "ocf_less_ppe_capex" in metrics
        explicit_proxy_equivalence = any(
            claim.role == PPEProxyFCFClaimRole.PROXY_AS_FCF_ATTRIBUTION
            for claim in fcf_claims
        )
        violation_count = (
            sum(claim.role in violation_roles for claim in fcf_claims)
            if proxy_applies
            else 0
        )
        if explicit_proxy_equivalence and not proxy_applies:
            violation_count += 1
        if violation_count:
            counts["partial_capex_called_fcf_count"] += violation_count
            counts["affirmative_proxy_as_fcf_violation_count"] += violation_count
            errors.append("ppe_only_cash_conversion_proxy_called_fcf")

        current_fcf_claim = (
            bool(fcf_claims)
            and not proxy_applies
            and not explicit_proxy_equivalence
            and financial_claim_row_requires_current_fcf_evidence(
                row,
                evidence_by_ref=evidence_by_ref,
            )
        )
        supported_current_fcf = bool(
            metrics & {"free_cash_flow", "reported_free_cash_flow"}
        )
        if current_fcf_claim and not supported_current_fcf:
            counts["unsupported_current_fcf_claim_count"] += 1
            errors.append("unsupported_current_fcf_claim")

        prospective_directional_count = sum(
            fcf_temporal_claim_role(span, evidence_by_ref=evidence_by_ref)
            == FinancialClaimRole.PROSPECTIVE_VERIFICATION_REQUIREMENT
            and any(
                token in field_path.casefold()
                for token in _PROSPECTIVE_REQUIREMENT_DIRECTIONAL_PATHS
            )
            for span in fcf_temporal_claim_spans(row)
        )
        if prospective_directional_count:
            counts["prospective_fcf_requirement_directional_violation_count"] += (
                prospective_directional_count
            )
            errors.append(
                "prospective_fcf_requirement_used_as_current_directional_evidence"
            )

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
            claim.framework == "net_debt"
            and financial_claim_requires_current_evidence(
                claim,
                evidence_by_ref=evidence_by_ref,
            )
            for claim in claims_by_path.get(field_path, ())
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
            claim
            for claim in framework_claims
            if framework_reference_is_application(claim)
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
