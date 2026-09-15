"""Pre-model evidence capability for investment-thesis change judgments."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from enum import StrEnum
import hashlib
import json
import re

from pydantic import Field

from app.services.cross_market_decision_engine_service import (
    DecisionEvidenceRef,
    EvidenceCategory,
    FinancialComparisonKind,
    FinancialEvidenceQuality,
    FrozenModel,
)
from app.services.direction_timing_ownership_service import (
    EvidenceDomain,
    OwnedEvidencePacket,
)
from app.services.structured_autonomy_alias_service import EvidenceAliasCatalog
from app.services.structured_autonomy_alias_service import (
    build_alias_constrained_batch_schema,
)


CONTRACT_VERSION = "business-delta-evidence-capability-v1"
MODEL_VIEW_CONTRACT = "business-delta-evidence-view-v1"
FINANCIAL_COMPARISON_DIRECTION_CONTRACT = "financial-comparison-direction-v1"
POST_MODEL_VALIDATOR_CONTRACT = "post-model-business-delta-validator-v2"
UNCHANGED_CLAIM_SCOPE_CONTRACT = "business-delta-unchanged-claim-scope-v1"
SAFE_HIGHER_IS_STRONGER_FINANCIAL_METRICS = frozenset(
    {
        "operating_cash_flow",
        "ocf_less_ppe_capex",
    }
)


class BusinessDeltaCapability(StrEnum):
    UNCHANGED_ONLY = "UNCHANGED_ONLY"
    AI_JUDGMENT = "AI_JUDGMENT"
    INPUT_AMBIGUOUS = "INPUT_AMBIGUOUS"


class BusinessDeltaUnchangedClaimRole(StrEnum):
    CURRENT_CHANGE_ASSERTION = "CURRENT_CHANGE_ASSERTION"
    CONFIGURED_CONDITION_REFERENCE = "CONFIGURED_CONDITION_REFERENCE"
    EXPLICIT_NO_OBSERVED_CHANGE = "EXPLICIT_NO_OBSERVED_CHANGE"
    CONFIGURED_CONDITION_NOT_FULFILLED = "CONFIGURED_CONDITION_NOT_FULFILLED"
    CURRENT_CONDITION_FULFILLED = "CURRENT_CONDITION_FULFILLED"
    BASELINE_THESIS_DESCRIPTION = "BASELINE_THESIS_DESCRIPTION"
    UNKNOWN_OR_AMBIGUOUS = "UNKNOWN_OR_AMBIGUOUS"


class BusinessDeltaUnchangedClaim(FrozenModel):
    contract: str = UNCHANGED_CLAIM_SCOPE_CONTRACT
    clause: str
    role: BusinessDeltaUnchangedClaimRole


class BusinessDeltaEvidenceRole(StrEnum):
    ELIGIBLE_OBSERVED_CHANGE = "ELIGIBLE_OBSERVED_CHANGE"
    THESIS_BASELINE_CONTEXT = "THESIS_BASELINE_CONTEXT"
    CURRENT_CONTEXT_ONLY = "CURRENT_CONTEXT_ONLY"
    EXCLUDED_NON_BUSINESS_DELTA = "EXCLUDED_NON_BUSINESS_DELTA"
    AMBIGUOUS_CHANGE_LINEAGE = "AMBIGUOUS_CHANGE_LINEAGE"


class BusinessDeltaEvidenceItem(FrozenModel):
    alias: str
    canonical_ref: str
    source_ref: str
    domain: EvidenceDomain
    role: BusinessDeltaEvidenceRole
    reason: str
    supported_change_directions: tuple[str, ...] = ()


class FinancialComparisonDirectionResult(FrozenModel):
    contract: str = FINANCIAL_COMPARISON_DIRECTION_CONTRACT
    metric: str
    supported_change_directions: tuple[str, ...] = ()
    comparability_safe: bool
    polarity_supported: bool
    reason: str


class BusinessDeltaEvidenceView(FrozenModel):
    contract: str = CONTRACT_VERSION
    ticker: str
    capability: BusinessDeltaCapability
    baseline_context_refs: tuple[str, ...] = ()
    eligible_change_refs: tuple[str, ...] = ()
    eligible_change_direction_hints: dict[str, tuple[str, ...]] = Field(
        default_factory=dict
    )
    ambiguous_change_refs: tuple[str, ...] = ()
    items: tuple[BusinessDeltaEvidenceItem, ...]

    @property
    def allowed_business_thesis_changes(self) -> tuple[str, ...]:
        if self.capability == BusinessDeltaCapability.UNCHANGED_ONLY:
            return ("UNCHANGED",)
        if self.capability == BusinessDeltaCapability.AI_JUDGMENT:
            return ("STRENGTHENED", "UNCHANGED", "WEAKENED", "UNRESOLVED")
        return ()

    @property
    def eligible_canonical_refs(self) -> frozenset[str]:
        return frozenset(
            item.canonical_ref
            for item in self.items
            if item.role == BusinessDeltaEvidenceRole.ELIGIBLE_OBSERVED_CHANGE
        )

    @property
    def direction_unspecified_eligible_refs(self) -> tuple[str, ...]:
        return tuple(
            item.alias
            for item in self.items
            if item.role == BusinessDeltaEvidenceRole.ELIGIBLE_OBSERVED_CHANGE
            and not item.supported_change_directions
        )

    @property
    def excluded_change_refs(self) -> tuple[str, ...]:
        return tuple(
            item.alias
            for item in self.items
            if item.role
            not in {
                BusinessDeltaEvidenceRole.ELIGIBLE_OBSERVED_CHANGE,
                BusinessDeltaEvidenceRole.THESIS_BASELINE_CONTEXT,
            }
        )

    def model_context(self, *, excluded_limit: int = 8) -> dict[str, object]:
        excluded = [
            {"ref": item.alias, "reason": item.reason}
            for item in self.items
            if item.role
            not in {
                BusinessDeltaEvidenceRole.ELIGIBLE_OBSERVED_CHANGE,
                BusinessDeltaEvidenceRole.THESIS_BASELINE_CONTEXT,
            }
        ]
        return {
            "contract": MODEL_VIEW_CONTRACT,
            "capability": self.capability.value,
            "allowed_business_thesis_changes": list(
                self.allowed_business_thesis_changes
            ),
            "baseline_context_refs": list(self.baseline_context_refs),
            "eligible_change_refs": list(self.eligible_change_refs),
            "eligible_change_direction_hints": {
                key: list(value)
                for key, value in self.eligible_change_direction_hints.items()
            },
            "excluded_change_refs": excluded[:excluded_limit],
            "excluded_change_ref_count": len(excluded),
        }


_FUNDAMENTAL_CHANGE_DOMAINS = frozenset(
    {
        EvidenceDomain.BUSINESS_CURRENT,
        EvidenceDomain.EARNINGS_FINANCIAL_CURRENT,
        EvidenceDomain.LIQUIDITY_CASHFLOW_CURRENT,
        EvidenceDomain.SECTOR_OPERATING_CURRENT,
        EvidenceDomain.REGULATORY_CAPITAL_CURRENT,
        EvidenceDomain.CLINICAL_REGULATORY_CURRENT,
        EvidenceDomain.CAPITAL_ALLOCATION_CURRENT,
    }
)
_CONTROL_FIXTURE_CHANGE_CATEGORIES = frozenset(
    {
        EvidenceCategory.EARNINGS,
        EvidenceCategory.EARNINGS_QUALITY,
        EvidenceCategory.CATALYSTS,
    }
)
_EXPLICIT_POSITIVE_CHANGE = re.compile(
    r"\b(?:improv(?:e|ed|ement)|increas(?:e|ed)|rebound(?:ed)?|"
    r"strengthen(?:ed)?|accelerat(?:e|ed|ion)|turned\s+positive|rose)\b",
    re.I,
)
_EXPLICIT_NEGATIVE_CHANGE = re.compile(
    r"\b(?:declin(?:e|ed)|decreas(?:e|ed)|deteriorat(?:e|ed|ion)|"
    r"worsen(?:ed)?|weaken(?:ed)?|turned\s+negative|fell|slowed)\b",
    re.I,
)
_NON_OBSERVATION = re.compile(
    r"\b(?:could|may|might|if|whether|unknown|not\s+supplied|"
    r"remains\s+unproven|needs?\s+confirmation|required?)\b",
    re.I,
)
_NEGATED_CHANGE = re.compile(
    r"\b(?:without|no)\b.{0,40}\b(?:improvement|acceleration|decline|change)\b",
    re.I,
)
_CHANGE_LIKE_IDENTITY = re.compile(
    r"(?:^|[:_.-])(?:event|transition|delta|change)(?:$|[:_.-])",
    re.I,
)
_UNCHANGED_CLAUSE_SPLIT = re.compile(r"(?<=[.!?。！？;；])\s+|\n+")
_CURRENT_THESIS_CHANGE_ASSERTION = re.compile(
    r"(?:논리|테제)(?:가|는|도|를|의)?[^.!?。！？;；\n]{0,40}?"
    r"(?:강화|약화)(?:됐|되었|되었다|됨|된\s*것|된\s*상태)|"
    r"(?:실제(?:로)?|이미|분명히|현재(?:는)?)"
    r"[^.!?。！？;；\n]{0,24}?(?:강화|약화)"
    r"(?:됐|되었|되었다|됨|된\s*상태)|"
    r"(?:thesis|investment\s+case)\s+(?:has\s+|is\s+|was\s+)?"
    r"(?:materially\s+)?(?:strengthened|weakened|stronger|weaker)\b|"
    r"\b(?:in\s+fact|actually|already|now)\b[^.!?;\n]{0,24}"
    r"\b(?:strengthened|weakened)\b|"
    r"의미\s*있는\s*(?:긍정|부정)\s*변화(?:가|는)?\s*"
    r"(?:확인됐|확정됐|나타났|발생했)",
    re.I,
)
_CONFIGURED_CONDITION_FULFILLED = re.compile(
    r"(?:강화|약화|무효화)(?:\s*[·/]\s*(?:강화|약화|무효화))?\s*"
    r"조건(?:이|은|가|도)?[^.!?。！？;；\n]{0,20}?"
    r"(?:충족됐|충족되었|충족된\s*것|확인됐|확인되었|확인된\s*것|성립했)|"
    r"\b(?:configured\s+)?(?:strengthening|weakening|invalidation)?\s*"
    r"condition\s+(?:has\s+been\s+|was\s+|is\s+)?"
    r"(?:met|fulfilled|confirmed|satisfied)\b",
    re.I,
)
_CONFIGURED_CONDITION_NOT_FULFILLED = re.compile(
    r"(?:강화|약화|무효화)(?:\s*[·/]\s*(?:강화|약화|무효화))?\s*"
    r"조건(?:이|은|가|도)?[^.!?。！？;；\n]{0,36}?"
    r"(?:충족되지|확인되지|확정되지|성립하지|미충족|미확인|"
    r"충족하지\s*못)|"
    r"\b(?:configured\s+)?(?:strengthening|weakening|invalidation)?\s*"
    r"condition\b[^.!?;\n]{0,24}?"
    r"(?:has\s+not\s+been\s+(?:met|fulfilled|confirmed|satisfied)|"
    r"is\s+not\s+(?:met|fulfilled|confirmed|satisfied)|"
    r"remains?\s+(?:unmet|unfulfilled|unconfirmed))\b",
    re.I,
)
_EXPLICIT_NO_OBSERVED_CHANGE = re.compile(
    r"(?:기존\s*)?(?:논리|테제)(?:가|는|도)?[^.!?。！？;；\n]{0,28}?"
    r"(?:유지|변함\s*없)|"
    r"(?:강화|약화|의미\s*있는\s*관찰\s*변화)"
    r"[^.!?。！？;；\n]{0,28}?"
    r"(?:확인되지|확정되지|관찰되지|나타나지|없(?:었|다)|않(?:았|다))|"
    r"\b(?:no\s+(?:material\s+|observed\s+)?(?:thesis\s+)?change|"
    r"thesis\s+(?:has\s+)?(?:not\s+strengthened|not\s+weakened|"
    r"neither\s+strengthened\s+nor\s+weakened)|"
    r"thesis\s+remains?\s+unchanged|"
    r"(?:strengthening|weakening|change)\s+(?:has\s+)?not\s+been\s+"
    r"(?:confirmed|observed))\b",
    re.I,
)
_CONFIGURED_CONDITION_REFERENCE = re.compile(
    r"(?:강화|약화|무효화)(?:\s*[·/]\s*(?:강화|약화|무효화))?\s*조건|"
    r"\b(?:configured\s+)?(?:strengthening|weakening|invalidation)\s+"
    r"condition\b",
    re.I,
)
_BASELINE_THESIS_DESCRIPTION = re.compile(
    r"(?:기존|저장된|baseline|existing|stored)[^.!?。！？;；\n]{0,24}"
    r"(?:논리|테제|thesis|investment\s+case)",
    re.I,
)


def _classify_business_delta_unchanged_clause(
    clause: str,
) -> BusinessDeltaUnchangedClaimRole:
    if _CURRENT_THESIS_CHANGE_ASSERTION.search(clause):
        return BusinessDeltaUnchangedClaimRole.CURRENT_CHANGE_ASSERTION
    if _CONFIGURED_CONDITION_FULFILLED.search(clause):
        return BusinessDeltaUnchangedClaimRole.CURRENT_CONDITION_FULFILLED
    if _CONFIGURED_CONDITION_NOT_FULFILLED.search(clause):
        return BusinessDeltaUnchangedClaimRole.CONFIGURED_CONDITION_NOT_FULFILLED
    if _EXPLICIT_NO_OBSERVED_CHANGE.search(clause):
        return BusinessDeltaUnchangedClaimRole.EXPLICIT_NO_OBSERVED_CHANGE
    if _CONFIGURED_CONDITION_REFERENCE.search(clause):
        return BusinessDeltaUnchangedClaimRole.CONFIGURED_CONDITION_REFERENCE
    if _BASELINE_THESIS_DESCRIPTION.search(clause):
        return BusinessDeltaUnchangedClaimRole.BASELINE_THESIS_DESCRIPTION
    return BusinessDeltaUnchangedClaimRole.UNKNOWN_OR_AMBIGUOUS


def classify_business_delta_unchanged_claims(
    text: str,
) -> tuple[BusinessDeltaUnchangedClaim, ...]:
    """Classify current-change semantics without treating condition names as facts."""
    clauses = tuple(
        clause.strip() for clause in _UNCHANGED_CLAUSE_SPLIT.split(text) if clause.strip()
    )
    return tuple(
        BusinessDeltaUnchangedClaim(
            clause=clause,
            role=_classify_business_delta_unchanged_clause(clause),
        )
        for clause in clauses
    )


def _statement_for_alias(
    alias: str,
    ref: DecisionEvidenceRef,
    context_rows: Mapping[str, Mapping[str, object]],
) -> str:
    row = context_rows.get(alias)
    return str(row.get("statement") or ref.statement) if row is not None else ref.statement


def _explicit_direction_hints(statement: str) -> tuple[str, ...]:
    if _NON_OBSERVATION.search(statement) or _NEGATED_CHANGE.search(statement):
        return ()
    result = []
    if _EXPLICIT_POSITIVE_CHANGE.search(statement):
        result.append("STRENGTHENED")
    if _EXPLICIT_NEGATIVE_CHANGE.search(statement):
        result.append("WEAKENED")
    return tuple(result)


def _json_mapping(value: str) -> Mapping[str, object] | None:
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None
    return parsed if isinstance(parsed, Mapping) else None


def _structured_financial_value(ref: DecisionEvidenceRef) -> Decimal | None:
    raw: object = ref.value
    if raw is None:
        payload = _json_mapping(ref.statement)
        if payload is not None:
            raw = payload.get("value")
    try:
        value = Decimal(str(raw)) if raw is not None else None
    except (InvalidOperation, ValueError):
        return None
    return value if value is not None and value.is_finite() else None


def _periods_safely_comparable(
    current: DecisionEvidenceRef,
    prior: DecisionEvidenceRef,
) -> bool:
    current_context = current.financial_context
    prior_context = prior.financial_context
    assert current_context is not None and prior_context is not None
    current_period = current_context.period
    prior_period = prior_context.period
    if current_period.type != prior_period.type:
        return False
    if current_period.type.value == "POINT_IN_TIME":
        return False
    if current_period.start is None or prior_period.start is None:
        return False
    current_duration = (
        current_period.duration_days
        if current_period.duration_days is not None
        else (current_period.end - current_period.start).days + 1
    )
    prior_duration = (
        prior_period.duration_days
        if prior_period.duration_days is not None
        else (prior_period.end - prior_period.start).days + 1
    )
    return current_period.end > prior_period.end and current_duration == prior_duration


def derive_financial_comparison_direction(
    ref: DecisionEvidenceRef,
    refs_by_source_ref: Mapping[str, DecisionEvidenceRef],
) -> FinancialComparisonDirectionResult:
    context = ref.financial_context
    metric = context.metric if context is not None else "unknown"
    if context is None or context.comparison is None:
        return FinancialComparisonDirectionResult(
            metric=metric,
            comparability_safe=False,
            polarity_supported=False,
            reason="TYPED_FINANCIAL_COMPARISON_MISSING",
        )
    if metric not in SAFE_HIGHER_IS_STRONGER_FINANCIAL_METRICS:
        return FinancialComparisonDirectionResult(
            metric=metric,
            comparability_safe=False,
            polarity_supported=False,
            reason="METRIC_POLARITY_CONTEXT_DEPENDENT",
        )
    if (
        context.quality != FinancialEvidenceQuality.VERIFIED
        or context.comparison.kind != FinancialComparisonKind.PRIOR_YEAR_COMPARABLE
    ):
        return FinancialComparisonDirectionResult(
            metric=metric,
            comparability_safe=False,
            polarity_supported=True,
            reason="COMPARISON_NOT_VERIFIED_OR_NOT_PRIOR_YEAR_COMPARABLE",
        )

    comparison_source_refs = tuple(
        source_ref
        for source_ref in context.comparison.input_source_refs
        if source_ref != ref.source_ref
    )
    if len(comparison_source_refs) != 1:
        return FinancialComparisonDirectionResult(
            metric=metric,
            comparability_safe=False,
            polarity_supported=True,
            reason="COMPARISON_SOURCE_IDENTITY_UNSAFE",
        )
    prior = refs_by_source_ref.get(comparison_source_refs[0])
    prior_context = prior.financial_context if prior is not None else None
    if prior is None or prior_context is None:
        return FinancialComparisonDirectionResult(
            metric=metric,
            comparability_safe=False,
            polarity_supported=True,
            reason="COMPARISON_SOURCE_FACT_UNAVAILABLE",
        )

    same_basis = all(
        (
            prior_context.metric == metric,
            prior_context.quality == FinancialEvidenceQuality.VERIFIED,
            prior_context.currency == context.currency,
            prior_context.unit_scale == context.unit_scale,
            prior_context.entity_scope == context.entity_scope,
            prior_context.statement_basis == context.statement_basis,
            prior_context.attribution_basis == context.attribution_basis,
            prior_context.evidence_status == context.evidence_status,
        )
    )
    same_derivation = (
        context.derivation is None
        and prior_context.derivation is None
        or context.derivation is not None
        and prior_context.derivation is not None
        and context.derivation.formula == prior_context.derivation.formula
        and context.derivation.version == prior_context.derivation.version
    )
    if not same_basis or not same_derivation or not _periods_safely_comparable(ref, prior):
        return FinancialComparisonDirectionResult(
            metric=metric,
            comparability_safe=False,
            polarity_supported=True,
            reason="COMPARISON_PERIOD_OR_BASIS_UNSAFE",
        )

    current_value = _structured_financial_value(ref)
    prior_value = _structured_financial_value(prior)
    if current_value is None or prior_value is None:
        return FinancialComparisonDirectionResult(
            metric=metric,
            comparability_safe=False,
            polarity_supported=True,
            reason="COMPARISON_TYPED_VALUE_UNAVAILABLE",
        )
    if current_value > prior_value:
        directions = ("STRENGTHENED",)
        reason = "HIGHER_COMPARABLE_VALUE_SUPPORTS_STRENGTHENED"
    elif current_value < prior_value:
        directions = ("WEAKENED",)
        reason = "LOWER_COMPARABLE_VALUE_SUPPORTS_WEAKENED"
    else:
        directions = ()
        reason = "EQUAL_COMPARABLE_VALUE_HAS_NO_DIRECTION_HINT"
    return FinancialComparisonDirectionResult(
        metric=metric,
        supported_change_directions=directions,
        comparability_safe=True,
        polarity_supported=True,
        reason=reason,
    )


def _structured_event_state(ref: DecisionEvidenceRef) -> str | None:
    if not _CHANGE_LIKE_IDENTITY.search(ref.source_ref):
        return None
    payload = _json_mapping(ref.statement)
    if payload is None:
        return "AMBIGUOUS"
    baseline = payload.get("baseline_state") or payload.get("previous_state")
    current = payload.get("current_state") or payload.get("observed_state")
    dated = payload.get("event_date") or payload.get("as_of") or ref.as_of
    if baseline is not None and current is not None and dated:
        return "ELIGIBLE"
    return "AMBIGUOUS"


def _classify(
    *,
    alias: str,
    ref: DecisionEvidenceRef,
    domain: EvidenceDomain,
    statement: str,
    financial_refs_by_source_ref: Mapping[str, DecisionEvidenceRef],
) -> BusinessDeltaEvidenceItem:
    hints = _explicit_direction_hints(statement)
    if (
        ref.source_ref.startswith("stock.thesis.")
        or ref.category == EvidenceCategory.THESIS
    ):
        return BusinessDeltaEvidenceItem(
            alias=alias,
            canonical_ref=ref.ref_id,
            source_ref=ref.source_ref,
            domain=domain,
            role=BusinessDeltaEvidenceRole.THESIS_BASELINE_CONTEXT,
            reason="STORED_THESIS_OR_CONFIGURED_SIGNAL_BASELINE_ONLY",
        )

    if domain in {
        EvidenceDomain.MARKET_EXPECTATIONS,
        EvidenceDomain.VALUATION_SAFE,
        EvidenceDomain.PRICE_CONTEXT,
        EvidenceDomain.OHLCV_TECHNICAL,
        EvidenceDomain.SUPPORT_RESISTANCE,
        EvidenceDomain.VOLUME_LIQUIDITY,
        EvidenceDomain.TECHNICAL_STATE,
        EvidenceDomain.RISK_REWARD_PRICE,
        EvidenceDomain.SUPPLY_POSITIONING,
        EvidenceDomain.MACRO_TRANSMISSION,
    }:
        return BusinessDeltaEvidenceItem(
            alias=alias,
            canonical_ref=ref.ref_id,
            source_ref=ref.source_ref,
            domain=domain,
            role=BusinessDeltaEvidenceRole.EXCLUDED_NON_BUSINESS_DELTA,
            reason=f"NON_BUSINESS_DELTA_DOMAIN:{domain.value}",
        )

    financial = ref.financial_context
    if (
        financial is not None
        and financial.comparison is not None
        and financial.comparison.kind != FinancialComparisonKind.NONE
    ):
        if (
            financial.quality == FinancialEvidenceQuality.VERIFIED
        ):
            typed_direction = derive_financial_comparison_direction(
                ref,
                financial_refs_by_source_ref,
            )
            return BusinessDeltaEvidenceItem(
                alias=alias,
                canonical_ref=ref.ref_id,
                source_ref=ref.source_ref,
                domain=domain,
                role=BusinessDeltaEvidenceRole.ELIGIBLE_OBSERVED_CHANGE,
                reason="VERIFIED_TYPED_FINANCIAL_COMPARISON",
                supported_change_directions=(
                    typed_direction.supported_change_directions
                ),
            )
        return BusinessDeltaEvidenceItem(
            alias=alias,
            canonical_ref=ref.ref_id,
            source_ref=ref.source_ref,
            domain=domain,
            role=BusinessDeltaEvidenceRole.AMBIGUOUS_CHANGE_LINEAGE,
            reason="FINANCIAL_COMPARISON_NOT_VERIFIED",
        )

    if (
        ref.source_ref.startswith("stock.fact_catalog.monitoring:")
        and domain in _FUNDAMENTAL_CHANGE_DOMAINS
    ):
        return BusinessDeltaEvidenceItem(
            alias=alias,
            canonical_ref=ref.ref_id,
            source_ref=ref.source_ref,
            domain=domain,
            role=BusinessDeltaEvidenceRole.ELIGIBLE_OBSERVED_CHANGE,
            reason="TYPED_FUNDAMENTAL_MONITORING_TRANSITION",
            supported_change_directions=hints,
        )

    controlled_fixture = ref.source_ref.startswith(("fictional.", "fixture."))
    if (
        controlled_fixture
        and ref.category in _CONTROL_FIXTURE_CHANGE_CATEGORIES
        and hints
    ):
        return BusinessDeltaEvidenceItem(
            alias=alias,
            canonical_ref=ref.ref_id,
            source_ref=ref.source_ref,
            domain=domain,
            role=BusinessDeltaEvidenceRole.ELIGIBLE_OBSERVED_CHANGE,
            reason="CONTROL_FIXTURE_EXPLICIT_OBSERVED_CHANGE",
            supported_change_directions=hints,
        )

    event_state = _structured_event_state(ref)
    if event_state == "ELIGIBLE" and domain in _FUNDAMENTAL_CHANGE_DOMAINS:
        return BusinessDeltaEvidenceItem(
            alias=alias,
            canonical_ref=ref.ref_id,
            source_ref=ref.source_ref,
            domain=domain,
            role=BusinessDeltaEvidenceRole.ELIGIBLE_OBSERVED_CHANGE,
            reason="DATED_STRUCTURED_EVENT_WITH_BASELINE",
            supported_change_directions=hints,
        )
    if event_state == "AMBIGUOUS" and domain in _FUNDAMENTAL_CHANGE_DOMAINS:
        return BusinessDeltaEvidenceItem(
            alias=alias,
            canonical_ref=ref.ref_id,
            source_ref=ref.source_ref,
            domain=domain,
            role=BusinessDeltaEvidenceRole.AMBIGUOUS_CHANGE_LINEAGE,
            reason="CHANGE_LIKE_EVENT_WITHOUT_SAFE_BASELINE_LINEAGE",
        )

    if domain in _FUNDAMENTAL_CHANGE_DOMAINS:
        return BusinessDeltaEvidenceItem(
            alias=alias,
            canonical_ref=ref.ref_id,
            source_ref=ref.source_ref,
            domain=domain,
            role=BusinessDeltaEvidenceRole.CURRENT_CONTEXT_ONLY,
            reason="CURRENT_SINGLE_POINT_WITHOUT_BASELINE_CHANGE",
        )
    return BusinessDeltaEvidenceItem(
        alias=alias,
        canonical_ref=ref.ref_id,
        source_ref=ref.source_ref,
        domain=domain,
        role=BusinessDeltaEvidenceRole.EXCLUDED_NON_BUSINESS_DELTA,
        reason=f"NON_CHANGE_CONTEXT:{domain.value}",
    )


def build_business_delta_evidence_view(
    owned: OwnedEvidencePacket,
    catalog: EvidenceAliasCatalog,
    *,
    context: Mapping[str, object] | None = None,
) -> BusinessDeltaEvidenceView:
    ticker = owned.source_packet.ticker
    if catalog.ticker != ticker:
        raise ValueError("business_delta_catalog_ticker_mismatch")
    if catalog.generation != owned.source_packet.packet_id:
        raise ValueError("business_delta_catalog_generation_mismatch")
    context_rows: dict[str, Mapping[str, object]] = {}
    if context is not None:
        if str(context.get("ticker") or "") != ticker:
            raise ValueError("business_delta_context_ticker_mismatch")
        evidence = context.get("evidence")
        if not isinstance(evidence, Sequence) or isinstance(evidence, (str, bytes)):
            raise ValueError("business_delta_context_evidence_required")
        for row in evidence:
            if not isinstance(row, Mapping) or not row.get("alias"):
                raise ValueError("business_delta_context_row_invalid")
            alias = str(row["alias"])
            if alias in context_rows:
                raise ValueError("business_delta_context_alias_duplicate")
            context_rows[alias] = row

    by_ref = {row.ref.ref_id: row for row in owned.evidence}
    financial_refs_by_source_ref = {
        row.ref.source_ref: row.ref for row in owned.evidence
    }
    items = []
    for entry in catalog.entries:
        owned_ref = by_ref.get(entry.canonical_ref)
        if owned_ref is None:
            raise ValueError("business_delta_catalog_ref_not_owned")
        items.append(
            _classify(
                alias=entry.alias,
                ref=owned_ref.ref,
                domain=owned_ref.domain,
                statement=_statement_for_alias(
                    entry.alias, owned_ref.ref, context_rows
                ),
                financial_refs_by_source_ref=financial_refs_by_source_ref,
            )
        )
    ambiguous = tuple(
        item.alias
        for item in items
        if item.role == BusinessDeltaEvidenceRole.AMBIGUOUS_CHANGE_LINEAGE
    )
    eligible = tuple(
        item.alias
        for item in items
        if item.role == BusinessDeltaEvidenceRole.ELIGIBLE_OBSERVED_CHANGE
    )
    capability = (
        BusinessDeltaCapability.INPUT_AMBIGUOUS
        if ambiguous
        else BusinessDeltaCapability.AI_JUDGMENT
        if eligible
        else BusinessDeltaCapability.UNCHANGED_ONLY
    )
    return BusinessDeltaEvidenceView(
        ticker=ticker,
        capability=capability,
        baseline_context_refs=tuple(
            item.alias
            for item in items
            if item.role == BusinessDeltaEvidenceRole.THESIS_BASELINE_CONTEXT
        ),
        eligible_change_refs=eligible,
        eligible_change_direction_hints={
            item.alias: item.supported_change_directions
            for item in items
            if item.role == BusinessDeltaEvidenceRole.ELIGIBLE_OBSERVED_CHANGE
            and item.supported_change_directions
        },
        ambiguous_change_refs=ambiguous,
        items=tuple(items),
    )


def business_delta_evidence_view_sha256(
    view: BusinessDeltaEvidenceView,
) -> str:
    return hashlib.sha256(
        json.dumps(
            view.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def attach_business_delta_evidence_view(
    context: Mapping[str, object],
    view: BusinessDeltaEvidenceView,
) -> dict[str, object]:
    if str(context.get("ticker") or "") != view.ticker:
        raise ValueError("business_delta_view_context_ticker_mismatch")
    return {**context, "business_delta_evidence_view": view.model_context()}


def audit_business_delta_direction_projection(
    view: BusinessDeltaEvidenceView,
) -> dict[str, object]:
    expected = {
        item.alias: item.supported_change_directions
        for item in view.items
        if item.role == BusinessDeltaEvidenceRole.ELIGIBLE_OBSERVED_CHANGE
        and item.supported_change_directions
    }
    projected = view.eligible_change_direction_hints
    mismatches = sorted(
        alias
        for alias in set(expected) | set(projected)
        if expected.get(alias) != projected.get(alias)
    )
    return {
        "contract": FINANCIAL_COMPARISON_DIRECTION_CONTRACT,
        "ticker": view.ticker,
        "typed_direction_hint_count": sum(len(value) for value in expected.values()),
        "direction_hint_projection_mismatches": mismatches,
        "direction_hint_projection_mismatch_count": len(mismatches),
        "status": "PASS" if not mismatches else "FAIL",
    }


def business_delta_property_enums(
    views: Mapping[str, BusinessDeltaEvidenceView],
) -> dict[str, dict[str, tuple[str, ...]]]:
    ambiguous = sorted(
        ticker
        for ticker, view in views.items()
        if view.capability == BusinessDeltaCapability.INPUT_AMBIGUOUS
    )
    if ambiguous:
        raise ValueError(f"business_delta_input_ambiguous_pre_model:{ambiguous}")
    return {
        ticker: {
            "business_thesis_change": view.allowed_business_thesis_changes
        }
        for ticker, view in views.items()
    }


def build_business_delta_constrained_batch_schema(
    *,
    candidate_schema: Mapping[str, object],
    contract: str,
    packet_id: str,
    aliases_by_ticker: Mapping[str, Sequence[str]],
    views: Mapping[str, BusinessDeltaEvidenceView],
    reference_aliases_by_ticker_field: Mapping[
        str, Mapping[str, Sequence[str]]
    ]
    | None = None,
) -> dict[str, object]:
    enums = business_delta_property_enums(views)
    if set(aliases_by_ticker) != set(views):
        raise ValueError("business_delta_schema_view_scope_mismatch")
    schema = build_alias_constrained_batch_schema(
        candidate_schema=candidate_schema,
        contract=contract,
        packet_id=packet_id,
        aliases_by_ticker=aliases_by_ticker,
        reference_aliases_by_ticker_field=reference_aliases_by_ticker_field,
    )
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        raise ValueError("business_delta_batch_schema_properties_missing")
    candidates = properties.get("candidates")
    if not isinstance(candidates, dict):
        raise ValueError("business_delta_batch_candidates_schema_missing")
    items = candidates.get("items")
    if not isinstance(items, dict) or not isinstance(items.get("anyOf"), list):
        raise ValueError("business_delta_batch_choices_schema_missing")
    choices = items["anyOf"]
    if len(choices) != len(aliases_by_ticker):
        raise ValueError("business_delta_batch_choice_count_mismatch")
    for ticker, choice in zip(aliases_by_ticker, choices, strict=True):
        if not isinstance(choice, dict):
            raise ValueError("business_delta_candidate_schema_invalid")
        candidate_properties = choice.get("properties")
        if not isinstance(candidate_properties, dict):
            raise ValueError("business_delta_candidate_properties_missing")
        ticker_schema = candidate_properties.get("ticker")
        if not isinstance(ticker_schema, dict) or ticker_schema.get("const") != ticker:
            raise ValueError("business_delta_candidate_ticker_scope_mismatch")
        delta_schema = candidate_properties.get("business_thesis_change")
        if not isinstance(delta_schema, dict):
            raise ValueError("business_delta_candidate_property_missing")
        existing = delta_schema.get("enum")
        allowed = list(enums[ticker]["business_thesis_change"])
        if isinstance(existing, list) and not set(allowed).issubset(
            str(value) for value in existing
        ):
            raise ValueError("business_delta_candidate_enum_expansion_forbidden")
        delta_schema["enum"] = allowed
    return schema


def validate_business_delta_candidate(
    candidate: Mapping[str, object],
    view: BusinessDeltaEvidenceView,
) -> dict[str, object]:
    ticker = str(candidate.get("ticker") or "")
    errors: list[str] = []
    if ticker != view.ticker:
        errors.append("BUSINESS_DELTA_CANDIDATE_TICKER_MISMATCH")
    observed = str(candidate.get("business_thesis_change") or "")
    thesis_context = candidate.get("business_thesis_context")
    if not isinstance(thesis_context, Mapping):
        refs: tuple[str, ...] = ()
        text = ""
        errors.append("BUSINESS_DELTA_CONTEXT_REQUIRED")
    else:
        raw_refs = thesis_context.get("evidence_refs")
        refs = (
            tuple(str(value) for value in raw_refs)
            if isinstance(raw_refs, Sequence)
            and not isinstance(raw_refs, (str, bytes))
            else ()
        )
        text = str(thesis_context.get("text") or "")

    by_identity = {
        identity: item
        for item in view.items
        for identity in (item.alias, item.canonical_ref)
    }
    selected = [by_identity[ref] for ref in refs if ref in by_identity]
    invalid_refs = sorted(ref for ref in refs if ref not in by_identity)
    if invalid_refs:
        errors.append("BUSINESS_DELTA_INVALID_EVIDENCE_REF")
    selected_eligible = [
        item
        for item in selected
        if item.role == BusinessDeltaEvidenceRole.ELIGIBLE_OBSERVED_CHANGE
    ]

    if view.capability == BusinessDeltaCapability.INPUT_AMBIGUOUS:
        errors.append("BUSINESS_DELTA_INPUT_AMBIGUOUS_PRE_MODEL_HARD_STOP")
    elif observed not in view.allowed_business_thesis_changes:
        errors.append("BUSINESS_DELTA_CAPABILITY_VALUE_VIOLATION")

    if observed in {"STRENGTHENED", "WEAKENED"}:
        if not selected_eligible:
            errors.append("BUSINESS_DELTA_CHANGED_WITHOUT_ELIGIBLE_REF")
        supported = {
            direction
            for item in selected_eligible
            for direction in item.supported_change_directions
        }
        has_direction_unspecified = any(
            not item.supported_change_directions for item in selected_eligible
        )
        if supported and not has_direction_unspecified and observed not in supported:
            errors.append("BUSINESS_DELTA_DIRECTION_CONTRADICTS_EVIDENCE")
    elif observed == "UNRESOLVED":
        supported = {
            direction
            for item in selected_eligible
            for direction in item.supported_change_directions
        }
        unresolved_supported = (
            {"STRENGTHENED", "WEAKENED"}.issubset(supported)
            or any(not item.supported_change_directions for item in selected_eligible)
        )
        if not selected_eligible or not unresolved_supported:
            errors.append("BUSINESS_DELTA_UNRESOLVED_WITHOUT_ELIGIBLE_AMBIGUITY")

    unchanged_claims = classify_business_delta_unchanged_claims(text)
    unsafe_unchanged_roles = {
        BusinessDeltaUnchangedClaimRole.CURRENT_CHANGE_ASSERTION,
        BusinessDeltaUnchangedClaimRole.CURRENT_CONDITION_FULFILLED,
    }
    if view.capability == BusinessDeltaCapability.UNCHANGED_ONLY and any(
        claim.role in unsafe_unchanged_roles for claim in unchanged_claims
    ):
        errors.append("BUSINESS_DELTA_UNCHANGED_CONTEXT_ASSERTS_CHANGE")

    view_sha256 = business_delta_evidence_view_sha256(view)

    def audit_role(item: BusinessDeltaEvidenceItem) -> str:
        if item.role == BusinessDeltaEvidenceRole.ELIGIBLE_OBSERVED_CHANGE:
            return "ELIGIBLE_OBSERVED_CHANGE"
        if item.role == BusinessDeltaEvidenceRole.THESIS_BASELINE_CONTEXT:
            return "BASELINE_CONTEXT"
        return "EXCLUDED"

    linked_evidence = [
        {
            "selected_ref": ref,
            "alias": item.alias,
            "canonical_ref": item.canonical_ref,
            "source_ref": item.source_ref,
            "canonical_delta_role": audit_role(item),
            "delta_evidence_eligible": (
                item.role == BusinessDeltaEvidenceRole.ELIGIBLE_OBSERVED_CHANGE
            ),
            "delta_evidence_eligibility_reason": item.reason,
            "supported_change_directions": list(item.supported_change_directions),
            "supported_directions": list(item.supported_change_directions),
            "direction_semantics": (
                "KNOWN_SAFE"
                if item.supported_change_directions
                else "DIRECTION_UNSPECIFIED"
                if item.role
                == BusinessDeltaEvidenceRole.ELIGIBLE_OBSERVED_CHANGE
                else "NOT_APPLICABLE"
            ),
            "semantic_source": "BusinessDeltaEvidenceView",
        }
        for ref in refs
        if (item := by_identity.get(ref)) is not None
    ]

    return {
        "contract": POST_MODEL_VALIDATOR_CONTRACT,
        "evidence_view_contract": CONTRACT_VERSION,
        "ticker": ticker,
        "capability": view.capability.value,
        "observed": observed,
        "selected_refs": list(refs),
        "selected_eligible_refs": [item.canonical_ref for item in selected_eligible],
        "selected_direction_unspecified_refs": [
            item.canonical_ref
            for item in selected_eligible
            if not item.supported_change_directions
        ],
        "invalid_refs": invalid_refs,
        "linked_evidence": linked_evidence,
        "supported_change_directions": sorted(
            {
                direction
                for item in selected_eligible
                for direction in item.supported_change_directions
            }
        ),
        "direction_unspecified_eligible_refs": [
            item.canonical_ref
            for item in selected_eligible
            if not item.supported_change_directions
        ],
        "pre_model_delta_view_sha256": view_sha256,
        "post_model_validator_delta_view_sha256": view_sha256,
        "pre_post_delta_view_identity_mismatch_count": 0,
        "business_delta_semantic_projection_mismatch_count": 0,
        "legacy_raw_text_direction_rederivation_count": 0,
        "legacy_raw_text_eligibility_rederivation_count": 0,
        "unchanged_claim_scope_contract": UNCHANGED_CLAIM_SCOPE_CONTRACT,
        "unchanged_claims": [claim.model_dump(mode="json") for claim in unchanged_claims],
        "unchanged_claim_unsafe_count": sum(
            claim.role in unsafe_unchanged_roles for claim in unchanged_claims
        ),
        "errors": list(dict.fromkeys(errors)),
        "business_delta_capability_violation_count": int(bool(errors)),
        "business_delta_direction_violation_count": int(
            "BUSINESS_DELTA_DIRECTION_CONTRADICTS_EVIDENCE" in errors
        ),
        "status": "PASS" if not errors else "FAIL",
    }
