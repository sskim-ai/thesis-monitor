from __future__ import annotations

import re
from collections import Counter
from enum import StrEnum
from typing import Iterable, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field


CONTRACT_VERSION = "validation-semantic-ownership-shadow-v2"
SEMANTIC_CLAIM_CONTRACT = "structured-semantic-claim-v2"
AI_REVIEWER_CONTRACT = "ai-semantic-reviewer-shadow-v1"
BOUNDED_REWRITE_CONTRACT = "soft-quality-bounded-rewrite-v1"


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ValidationClass(StrEnum):
    HARD_DETERMINISTIC = "HARD_DETERMINISTIC"
    SEMANTIC_HARD = "SEMANTIC_HARD"
    SOFT_QUALITY = "SOFT_QUALITY"


class SemanticClaimType(StrEnum):
    CURRENT_FACT = "CURRENT_FACT"
    CURRENT_NUMERIC_FACT = "CURRENT_NUMERIC_FACT"
    HISTORICAL_FACT = "HISTORICAL_FACT"
    FUTURE_VALIDATION_CONDITION = "FUTURE_VALIDATION_CONDITION"
    RISK_CONDITION = "RISK_CONDITION"
    BUSINESS_INVALIDATION_CONDITION = "BUSINESS_INVALIDATION_CONDITION"
    PRICE_REVIEW_CONDITION = "PRICE_REVIEW_CONDITION"
    VALUATION_INTERPRETATION = "VALUATION_INTERPRETATION"
    MARKET_EXPECTATION_INTERPRETATION = "MARKET_EXPECTATION_INTERPRETATION"
    HOLDER_REASSESSMENT = "HOLDER_REASSESSMENT"
    NEW_BUYER_CONDITION = "NEW_BUYER_CONDITION"
    UNKNOWN = "UNKNOWN"


class ClaimOwner(StrEnum):
    AI_SEMANTIC_PLANNER = "AI_SEMANTIC_PLANNER"
    AI_WRITER = "AI_WRITER"
    DETERMINISTIC_RENDERER = "DETERMINISTIC_RENDERER"
    SAFETY_POLICY = "SAFETY_POLICY"


class RepetitionClass(StrEnum):
    RENDERER_OWNED_REPEAT = "RENDERER_OWNED_REPEAT"
    MODEL_OWNED_SUBSTANTIVE_REPEAT = "MODEL_OWNED_SUBSTANTIVE_REPEAT"
    REQUIRED_SAFETY_REPEAT = "REQUIRED_SAFETY_REPEAT"
    BENIGN_TEMPLATE_REPEAT = "BENIGN_TEMPLATE_REPEAT"
    MATERIAL_SPAM_REPEAT = "MATERIAL_SPAM_REPEAT"


class RewriteDisposition(StrEnum):
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED_KEEP_ORIGINAL = "FAILED_KEEP_ORIGINAL"
    REJECTED_INVARIANCE = "REJECTED_INVARIANCE"


class ReviewerVerdict(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL_ADVISORY = "FAIL_ADVISORY"


class EvidenceSeverity(StrEnum):
    STRENGTHENING = "STRENGTHENING"
    MAINTAIN = "MAINTAIN"
    WEAKENING = "WEAKENING"
    INVALIDATION_CANDIDATE = "INVALIDATION_CANDIDATE"
    INVALIDATION = "INVALIDATION"


class ValuationEvidenceRole(StrEnum):
    NONE = "NONE"
    CAUTION_ONLY = "CAUTION_ONLY"
    INTERPRETATION = "INTERPRETATION"


_SEVERITY_RANK = {
    EvidenceSeverity.STRENGTHENING: 0,
    EvidenceSeverity.MAINTAIN: 1,
    EvidenceSeverity.WEAKENING: 2,
    EvidenceSeverity.INVALIDATION_CANDIDATE: 3,
    EvidenceSeverity.INVALIDATION: 4,
}


class ValidatorRule(FrozenModel):
    rule_id: str
    file: str
    function: str
    mechanism: str
    current_severity: str
    current_owner: str
    protected_risk: str
    known_incidents: tuple[str, ...] = ()
    false_positive_history: str = "none observed"
    false_negative_risk: str
    proposed_class: ValidationClass
    proposed_owner: str
    production_gate_impact: str


class UnknownEvidenceScope(FrozenModel):
    unknown_subject: str
    unknown_metric: str | None = None
    unknown_effect: str
    allowed_context_refs: tuple[str, ...] = ()


class EvidenceOwnership(FrozenModel):
    evidence_ref: str
    ticker: str
    generation_id: str
    semantic_family: str
    metric: str | None = None
    current: bool = True
    denied: bool = False
    prose_eligible: bool = True
    semantic_eligible: bool = True
    numeric_eligible: bool = False
    valuation_eligible: bool = False
    valuation_role: ValuationEvidenceRole = ValuationEvidenceRole.NONE
    severity: EvidenceSeverity | None = None
    unknown_scope: UnknownEvidenceScope | None = None


class NumericOwnership(FrozenModel):
    numeric_ref: str
    evidence_ref: str
    field_path: str
    semantic_type: str
    unit: str


class DecisionFields(FrozenModel):
    overall_direction: str
    new_buyer_stance: str
    holder_stance: str
    buy_balance: float
    sell_balance: float


class StructuredSemanticClaim(FrozenModel):
    contract: str = SEMANTIC_CLAIM_CONTRACT
    claim_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    generation_id: str = Field(min_length=1)
    claim_type: SemanticClaimType
    topic: str = Field(min_length=1)
    metrics: tuple[str, ...] = ()
    direction: str | None = None
    evidence_refs: tuple[str, ...] = ()
    numeric_refs: tuple[str, ...] = ()
    text_ref: str = Field(min_length=1)
    text: str = Field(min_length=1)
    owner: ClaimOwner = ClaimOwner.AI_WRITER
    trade_action: str | None = None
    trade_force: str | None = None
    severity: EvidenceSeverity | None = None
    valuation_role: ValuationEvidenceRole | None = None
    unknown_scope_ref: str | None = None
    unknown_subject: str | None = None
    unknown_metric: str | None = None
    unknown_effect: str | None = None
    context_refs: tuple[str, ...] = ()


class ValidationIssue(FrozenModel):
    code: str
    validation_class: ValidationClass
    claim_id: str | None = None
    detail: str


class SemanticValidationResult(FrozenModel):
    contract: str = CONTRACT_VERSION
    hard_issues: tuple[ValidationIssue, ...] = ()
    semantic_issues: tuple[ValidationIssue, ...] = ()
    soft_issues: tuple[ValidationIssue, ...] = ()
    temporal_grammar_required_for_metric_ownership: int = 0
    freeform_unbound_numeric: int = 0
    class_ab_passed: bool


class RepetitionObservation(FrozenModel):
    normalized_span: str
    owner: ClaimOwner
    stock_count: int = Field(ge=1)
    evidence_signature_count: int = Field(ge=0)
    is_required_safety: bool = False
    is_structural_heading: bool = False
    has_bound_numeric_token: bool = False


class RepetitionAssessment(FrozenModel):
    classification: RepetitionClass
    hard_block_candidate: bool
    reason: str


class RewriteInvariantSnapshot(FrozenModel):
    fact_refs: tuple[str, ...]
    numeric_refs: tuple[str, ...]
    decision_fields: DecisionFields
    semantic_claim_types: tuple[SemanticClaimType, ...]
    evidence_refs: tuple[str, ...]
    metrics: tuple[str, ...]
    claim_severities: tuple[EvidenceSeverity | None, ...]
    valuation_roles: tuple[ValuationEvidenceRole | None, ...]
    unknown_scopes: tuple[tuple[str | None, str | None, str | None, str | None], ...]
    context_refs: tuple[str, ...]


class BoundedRewriteResult(FrozenModel):
    contract: str = BOUNDED_REWRITE_CONTRACT
    disposition: RewriteDisposition
    invariant_errors: tuple[str, ...] = ()
    class_ab_rerun_required: bool
    original_remains_eligible: bool
    attempt_count: int = Field(ge=0, le=1)


class AISemanticReviewerIssue(FrozenModel):
    code: str
    confidence: str
    claim_ids: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    explanation: str


class AISemanticReviewerResult(FrozenModel):
    contract: str = AI_REVIEWER_CONTRACT
    verdict: ReviewerVerdict
    issues: tuple[AISemanticReviewerIssue, ...] = ()
    proposed_fact_refs: tuple[str, ...] = ()
    proposed_numeric_refs: tuple[str, ...] = ()
    external_fetch_performed: bool = False
    rewrite_performed: bool = False


class ReviewerContractValidation(FrozenModel):
    valid: bool
    errors: tuple[str, ...] = ()
    production_hard_gate: bool = False


class ShadowPolicyDecision(FrozenModel):
    old_policy_eligible: bool
    new_shadow_policy_eligible: bool
    class_a_failures: int
    class_b_failures: int
    class_c_warnings: int
    rewrite_disposition: RewriteDisposition
    reason: str


class ShadowGeneratedSubject(FrozenModel):
    ticker: str
    claims: tuple[StructuredSemanticClaim, ...] = Field(min_length=1, max_length=3)


class ShadowGenerationBatch(FrozenModel):
    contract: str
    generation_id: str
    subjects: tuple[ShadowGeneratedSubject, ...]


class ShadowSubjectReview(FrozenModel):
    ticker: str
    result: AISemanticReviewerResult


class ShadowReviewerBatch(FrozenModel):
    contract: str
    generation_id: str
    reviews: tuple[ShadowSubjectReview, ...]


def _rule(
    rule_id: str,
    file: str,
    function: str,
    mechanism: str,
    current_severity: str,
    current_owner: str,
    protected_risk: str,
    false_negative_risk: str,
    proposed_class: ValidationClass,
    proposed_owner: str,
    production_gate_impact: str,
    *,
    known_incidents: tuple[str, ...] = (),
    false_positive_history: str = "none observed",
) -> ValidatorRule:
    return ValidatorRule(
        rule_id=rule_id,
        file=file,
        function=function,
        mechanism=mechanism,
        current_severity=current_severity,
        current_owner=current_owner,
        protected_risk=protected_risk,
        known_incidents=known_incidents,
        false_positive_history=false_positive_history,
        false_negative_risk=false_negative_risk,
        proposed_class=proposed_class,
        proposed_owner=proposed_owner,
        production_gate_impact=production_gate_impact,
    )


def validator_inventory() -> tuple[ValidatorRule, ...]:
    """Return the complete logical-rule inventory for the scoped decision path.

    One record represents one enforcement family, rather than every branch that emits
    the same error code. The scope is intentionally explicit and covered by tests.
    """

    a = ValidationClass.HARD_DETERMINISTIC
    b = ValidationClass.SEMANTIC_HARD
    c = ValidationClass.SOFT_QUALITY
    rules = (
        _rule("schema.output_shape", "app/schemas/ai_review.py", "AIDailyReviewOutput", "pydantic schema", "hard", "schema", "schema corruption and missing fields", "invalid output can reach a validator", a, "deterministic schema", "unchanged hard gate"),
        _rule("numeric.fact_identity", "app/services/numeric_provenance_service.py", "bind_numeric_fact_references", "registry lookup", "hard", "numeric binder", "nonexistent fact_id or field_path", "fabricated number", a, "numeric registry", "unchanged hard gate"),
        _rule("numeric.value_exactness", "app/services/numeric_provenance_service.py", "bind_numeric_fact_references", "exact value comparison", "hard", "numeric binder", "unsupported numeric value", "wrong user-visible number", a, "numeric registry", "unchanged hard gate"),
        _rule("numeric.semantic_unit", "app/services/numeric_semantic_registry.py", "resolve_numeric_semantic", "typed registry", "hard", "numeric registry", "semantic or unit mismatch", "PBR/PER, percent, amount confusion", a, "numeric registry", "unchanged hard gate"),
        _rule("numeric.currency_security_basis", "app/services/numeric_semantic_registry.py", "resolve_numeric_semantic", "typed registry", "hard", "numeric registry", "currency, issuer, ADR, or share-basis mismatch", "cross-basis arithmetic", a, "numeric registry", "unchanged hard gate"),
        _rule("numeric.bound_label_source", "app/services/ai_reasoning_quality_service.py", "_numeric_label_quality_report", "canonical metadata comparison", "hard", "message quality", "source, instrument, period, and zone-role mislabel", "fact presented as another fact", a, "numeric binder", "remain hard; detach from style aggregate"),
        _rule("numeric.postposition", "app/services/ai_reasoning_quality_service.py", "_numeric_label_quality_report", "Korean particle parser", "hard", "message quality", "awkward numeric postposition", "language defect only", c, "AI writer quality", "soft warning or one rewrite", known_incidents=("Korean particle suffix",), false_positive_history="lexical morphology can misread unfamiliar labels"),
        _rule("numeric.cross_section_repetition", "app/services/ai_reasoning_quality_service.py", "_numeric_fact_repetition_report", "claim occurrence count", "hard", "message quality", "same exact fact repeated three or more times", "numeric clutter", c, "AI writer quality", "soft warning unless ownership is contradictory", false_positive_history="safe canonical fact repetition blocked a complete message"),
        _rule("numeric.primary_owner", "app/services/ai_reasoning_quality_service.py", "_numeric_primary_ownership_report", "typed claim owner", "hard", "message quality", "exact RR value outside canonical owner", "same number gains conflicting meaning", a, "structured semantic planner", "unchanged hard gate"),
        _rule("numeric.business_valuation_owner", "app/services/ai_reasoning_quality_service.py", "_business_numeric_ownership_report", "typed semantic owner", "hard", "message quality", "valuation denominator used as business filler", "section semantics become misleading", b, "structured semantic planner", "hard only on explicit metadata mismatch"),
        _rule("semantic.evidence_exists", "app/services/semantic_decision_service.py", "semantic_claim_reference_errors", "structured reference", "hard", "semantic scope", "claim with nonexistent evidence", "unsupported assertion", a, "structured semantic planner", "unchanged hard gate"),
        _rule("semantic.evidence_section_fencing", "app/services/semantic_decision_service.py", "semantic_claim_reference_errors", "section fact set", "hard", "semantic scope", "fact used outside fenced section", "ownership escape", a, "structured semantic planner", "unchanged hard gate"),
        _rule("semantic.denied_fact_echo", "app/services/semantic_decision_service.py", "semantic_claim_reference_errors", "structured ref plus narrow lexical echo", "hard", "semantic scope", "denied evidence asserted as usable", "tainted fact leaks into prose", b, "structured semantic planner", "migrate lexical ownership to claim metadata"),
        _rule("semantic.valuation_scope", "app/services/semantic_decision_service.py", "valuation_context_reference_errors", "typed scope", "hard", "valuation scope", "issuer/security/peer/historical scope confusion", "unsafe valuation interpretation", b, "structured semantic planner", "hard on explicit scope contradiction"),
        _rule("semantic.typed_valuation", "app/services/semantic_decision_service.py", "typed_valuation_scope_error", "typed field", "hard", "valuation scope", "typed valuation class mismatch", "wrong valuation basis", b, "structured semantic planner", "unchanged semantic hard gate"),
        _rule("semantic.holder_observer", "app/services/semantic_decision_service.py", "observer_holder_semantic_error", "structured stance comparison", "hard", "decision semantics", "holder and new-buyer contradiction", "trade stance becomes misleading", b, "structured decision fields", "hard only on material contradiction"),
        _rule("quality.exact_sentence_repeat", "app/services/ai_reasoning_quality_service.py", "relational_reasoning_quality_report", "normalized sentence count", "hard", "message quality", "cross-ticker identical prose", "material spam can hide stock-specific reasoning", c, "AI writer quality", "soft by default; material spam separately reviewed", known_incidents=("US14 repeated volume participation",), false_positive_history="short safe factual patterns blocked delivery"),
        _rule("quality.typed_skeleton_repeat", "app/services/ai_reasoning_quality_service.py", "relational_reasoning_quality_report", "regex skeleton and typed identity", "hard", "message quality", "cross-ticker phrasing skeleton reuse", "material rationale copied across unlike evidence", c, "AI writer quality", "taxonomy plus one bounded rewrite", known_incidents=("US14 volume and current-price skeletons",), false_positive_history="two short bound-numeric patterns blocked otherwise safe US14"),
        _rule("quality.generic_methodology", "app/services/ai_reasoning_quality_service.py", "relational_reasoning_quality_report", "Korean regex family", "hard", "message quality", "repeated methodology prose", "boilerplate crowds out evidence", c, "AI writer quality", "soft warning", false_positive_history="natural paraphrases are difficult to classify lexically"),
        _rule("quality.generic_numeric_summary", "app/services/ai_reasoning_quality_service.py", "relational_reasoning_quality_report", "Korean regex", "hard", "message quality", "generic numeric intro reuse", "low-specificity prose", c, "AI writer quality", "soft warning"),
        _rule("quality.next_unknown_repeat", "app/services/ai_reasoning_quality_service.py", "relational_reasoning_quality_report", "normalized string count", "hard", "message quality", "generic next-check or Unknown repetition", "decision usefulness degrades", c, "AI writer quality", "soft warning or rewrite"),
        _rule("quality.watch_next_overlap", "app/services/ai_reasoning_quality_service.py", "_watch_next_overlap_report", "Korean regex and containment", "hard", "message quality", "watch and next-check semantic duplication", "redundant message", c, "AI writer quality", "soft warning", false_positive_history="event-oriented grammar can be interpreted inconsistently"),
        _rule("quality.observer_holder_distinct_wording", "app/services/ai_reasoning_quality_service.py", "relational_reasoning_quality_report", "exact normalized text", "hard", "message quality", "identical observer and holder prose", "audiences receive no distinction", c, "AI writer quality", "soft unless structured stances contradict"),
        _rule("quality.us_kr_supply_language", "app/services/ai_reasoning_quality_service.py", "relational_reasoning_quality_report", "Korean regex", "hard", "message quality", "KR investor-flow semantics leak into US", "unsupported market-specific claim", b, "structured semantic planner", "hard on semantic family mismatch; wording itself soft"),
        _rule("quality.supply_grounding", "app/services/ai_reasoning_quality_service.py", "relational_reasoning_quality_report", "validation error aggregation", "hard", "message quality", "unsupported supply fact", "invented market evidence", a, "evidence ownership", "unchanged hard gate"),
        _rule("quality.financial_period", "app/services/ai_reasoning_quality_service.py", "relational_reasoning_quality_report", "validation error aggregation", "hard", "message quality", "missing or wrong financial period label", "stale/current confusion", a, "financial lineage", "unchanged hard gate"),
        _rule("quality.valuation_evidence", "app/services/ai_reasoning_quality_service.py", "relational_reasoning_quality_report", "validation error aggregation", "hard", "message quality", "unsupported valuation comparison", "false cheap/expensive conclusion", a, "valuation lineage", "unchanged hard gate"),
        _rule("quality.message_completeness", "app/services/ai_reasoning_quality_service.py", "relational_reasoning_quality_report", "ticker and message cardinality", "hard", "message quality", "partial batch or missing ticker", "partial delivery", a, "delivery integrity", "unchanged hard gate"),
        _rule("quality.rendered_heading", "app/services/ai_reasoning_quality_service.py", "relational_reasoning_quality_report", "heading substring", "hard", "message quality", "wrong section heading", "presentation defect", c, "thin renderer", "soft unless schema is unparseable"),
        _rule("quality.identity_prose", "app/services/ai_reasoning_quality_service.py", "relational_reasoning_quality_report", "security-state plus prose regex", "hard", "message quality", "ADR/common-stock identity overclaim", "security identity misinformation", b, "structured security identity", "hard on structured identity contradiction"),
        _rule("quality.internal_lexicon", "app/services/ai_reasoning_quality_service.py", "_final_rendered_language_report", "lexical regex", "hard", "message quality", "internal implementation words in output", "poor UX", c, "thin renderer", "soft warning or rewrite"),
        _rule("quality.korean_grammar", "app/services/ai_reasoning_quality_service.py", "_final_rendered_language_report", "Korean morphology regex", "hard", "message quality", "malformed particles or incomplete predicate", "awkward prose", c, "AI writer quality", "soft warning", known_incidents=("supply actor particle",), false_positive_history="surface morphology is not semantic ownership"),
        _rule("financial.raw_mapping", "app/services/financial_validation.py", "validate_event_financials", "structured source field map", "hard", "financial validation", "raw statement field mismatch", "wrong accounting amount", a, "financial lineage", "unchanged hard gate"),
        _rule("financial.period_basis", "app/services/financial_validation.py", "validate_event_financials", "period and basis fields", "hard", "financial validation", "QTD/YTD/CFS/OFS mismatch", "wrong accounting period", a, "financial lineage", "unchanged hard gate"),
        _rule("financial.attribution", "app/services/financial_validation.py", "validate_event_financials", "entity attribution", "hard", "financial validation", "parent/common/total attribution mismatch", "wrong earnings owner", a, "financial lineage", "unchanged hard gate"),
        _rule("financial.quality_taint", "app/services/financial_quality_service.py", "build_financial_quality_state", "lineage quality graph", "hard", "financial quality", "tainted dependency used downstream", "derived metric inherits unsafe input", a, "financial lineage", "unchanged hard gate"),
        _rule("financial.book_coherence", "app/services/financial_quality_service.py", "_book_valuation_coherence", "structured arithmetic", "hard", "financial quality", "book value or PBR coherence failure", "unsafe BVPS/PBR reconstruction", a, "financial lineage", "unchanged hard gate"),
        _rule("price.current_context", "app/services/current_price_context_service.py", "select_current_price_context", "typed quote and session selection", "hard", "price context", "stale or wrong-session current price", "historical value presented as current", a, "price lineage", "unchanged hard gate"),
        _rule("price.fallback_context", "app/services/current_price_context_service.py", "fallback_price_context_errors", "typed fallback contract", "hard", "price context", "unsafe fallback price semantics", "wrong current price", a, "price lineage", "unchanged hard gate"),
        _rule("price.structure_numeric", "app/services/price_structure_v3_renderer_service.py", "validate_price_structure_render", "typed zone validation", "hard", "price structure", "wrong support/resistance value or role", "trade boundary misinformation", a, "price structure lineage", "unchanged hard gate"),
        _rule("price.legacy_token", "app/services/price_structure_v3_renderer_service.py", "detect_legacy_technical_tokens", "natural-language token detector", "hard", "renderer safety", "legacy technical prose survives replacement", "duplicate or stale technical context", b, "structured render occurrence", "hard only when a structured stale occurrence is identified", known_incidents=("수주가 token boundary",), false_positive_history="주가 substring matched inside 수주가"),
        _rule("market.us_evidence_utilization", "app/services/market_evidence_utilization_validator_service.py", "validate_us_market_evidence_utilization", "structured slot consumption", "hard", "market context", "required market evidence omitted or misowned", "market message contradicts available facts", b, "structured semantic planner", "hard on material required-slot contradiction"),
        _rule("market.kr_evidence_utilization", "app/services/market_evidence_utilization_validator_service.py", "validate_kr_market_evidence_utilization", "structured slot consumption", "hard", "market context", "KR breadth/sector/size evidence misowned", "market message uses wrong cohort", b, "structured semantic planner", "hard on material required-slot contradiction"),
        _rule("market.us_payload_identity", "app/services/us_market_message_quality_service.py", "quality_result_matches_received_payload", "payload sha256", "hard", "market message", "quality receipt for a different payload", "unvalidated text delivered", a, "delivery integrity", "unchanged hard gate"),
        _rule("market.us_wording_quality", "app/services/us_market_message_quality_service.py", "validate_us_market_message_payload", "section parser and wording checks", "hard", "market message", "missing sections or weak prose", "message readability", c, "AI writer and thin renderer", "split structural completeness from soft wording"),
        _rule("decision.evidence_ownership", "app/services/cross_market_decision_engine_service.py", "validate_decision_candidate", "structured evidence refs", "hard", "decision engine", "cross-ticker or unsupported evidence", "wrong decision basis", a, "decision evidence packet", "unchanged hard gate"),
        _rule("decision.numeric_fencing", "app/services/cross_market_decision_engine_service.py", "validate_decision_candidate", "numeric ref registry", "hard", "decision engine", "unbound numeric or wrong fact scope", "fabricated decision number", a, "numeric registry", "unchanged hard gate"),
        _rule("decision.trade_contradiction", "app/services/preconfirmation_decision_v2_service.py", "validate_preconfirmation_candidate", "structured decision comparison plus lexical fallback", "hard", "decision semantics", "mandatory trade command contradicts decision", "unsafe trade instruction", b, "structured semantic planner", "hard only on explicit mandatory contradiction", known_incidents=("자동 매도보다 재평가",), false_positive_history="keyword parsing confused comparison with instruction"),
        _rule("decision.confirmation_condition", "app/services/accepted_decision_v2_service.py", "decision_change_condition_errors", "condition parser", "hard", "accepted decision", "upgrade/downgrade conditions contradict accepted decision", "incorrect reassessment rule", b, "structured decision fields", "migrate condition type from prose to metadata"),
        _rule("decision.accepted_candidate", "app/services/accepted_decision_v2_service.py", "validate_accepted_v2_decision", "structured model validation", "hard", "accepted decision", "invalid accepted decision or adjudication", "unapproved decision becomes authoritative", a, "accepted-decision owner", "unchanged hard gate"),
        _rule("decision.accepted_render", "app/services/accepted_decision_v2_service.py", "validate_accepted_v2_render", "accepted id and field equality", "hard", "accepted renderer", "render differs from accepted decision", "renderer changes recommendation", a, "thin renderer", "unchanged hard gate"),
        _rule("decision.accepted_message_quality", "app/services/accepted_decision_v2_service.py", "accepted_message_quality", "numeric and repeated span checks", "hard", "accepted renderer", "unbound number or repeated rationale", "numeric invention or spam", b, "split numeric binder and soft reviewer", "numeric remains hard; repetition becomes soft"),
        _rule("decision.consistency", "app/services/accepted_decision_consistency_service.py", "audit_accepted_decision_consistency", "structured field comparison", "hard", "accepted decision", "accepted fields contradict evidence/adjudication", "decision drift", a, "accepted-decision owner", "unchanged hard gate"),
        _rule("decision.polarity", "app/services/decision_canary_service.py", "decision_polarity_errors", "structured polarity refs", "hard", "decision canary", "evidence polarity contradicts decision reason", "positive evidence rendered as negative", b, "structured semantic planner", "hard on explicit polarity mismatch"),
        _rule("decision.localization", "app/services/decision_canary_service.py", "decision_korean_localization_errors", "lexical localization checks", "hard", "decision canary", "English/internal enum leaks", "poor Korean UX", c, "AI writer quality", "soft warning or rewrite"),
        _rule("free_analyst.claim_ownership", "app/services/evidence_locked_free_analyst_service.py", "_validate_claim_ownership", "structured owner identity", "hard", "free analyst", "claim uses wrong ticker/generation/fact", "cross-owner evidence leak", a, "structured semantic planner", "unchanged hard gate"),
        _rule("free_analyst.synthesis", "app/services/evidence_locked_free_analyst_service.py", "validate_free_analyst_analysis", "structured inference rules", "hard", "free analyst", "unsupported inference or contradiction", "invented causal conclusion", b, "structured semantic planner", "hard on explicit unsupported inference"),
        _rule("free_analyst.rendered_safety", "app/services/evidence_locked_free_analyst_service.py", "rendered_safety_report", "rendered text and refs", "hard", "free analyst renderer", "numeric or semantic claim lost in rendering", "unsafe rendered output", b, "thin renderer", "split hard binding from soft prose"),
        _rule("free_analyst.novelty", "app/services/evidence_locked_free_analyst_service.py", "novel_synthesis_report", "text novelty comparison", "hard", "free analyst quality", "insufficient novel synthesis", "low analyst value", c, "AI writer quality", "soft quality only"),
        _rule("delivery.claim_fencing", "app/services/ai_assisted_delivery_service.py", "_same_analysis_generation", "generation identity", "hard", "delivery", "cross-generation artifact delivery", "stale owner sends", a, "delivery state machine", "unchanged hard gate"),
        _rule("delivery.receipt_integrity", "app/services/ai_assisted_delivery_service.py", "_persisted_quality_integrity_errors", "hash and receipt verification", "hard", "delivery", "receipt does not match payload", "unvalidated payload delivery", a, "delivery state machine", "unchanged hard gate"),
        _rule("delivery.exactly_once", "app/services/ai_assisted_delivery_service.py", "_session_deliveries", "delivery identity lookup", "hard", "delivery", "duplicate send", "duplicate user message", a, "delivery state machine", "unchanged hard gate"),
        _rule("delivery.terminal_immutability", "app/services/accepted_decision_v2_runtime_service.py", "advance_accepted_v2_state", "state transition guard", "hard", "runtime state", "terminal state overwritten", "late child changes settled run", a, "delivery state machine", "unchanged hard gate"),
        _rule("delivery.orphan_reconciliation", "app/services/notification_delivery_integrity_service.py", "inspect_kr_orphan_incident", "DB row and artifact reconciliation", "hard", "delivery integrity", "orphan or duplicate KR notification", "missing or duplicate message", a, "delivery state machine", "unchanged hard gate"),
    )
    return rules


def inventory_summary(rules: Sequence[ValidatorRule] | None = None) -> dict[str, object]:
    values = tuple(rules or validator_inventory())
    ids = [rule.rule_id for rule in values]
    class_counts = Counter(rule.proposed_class.value for rule in values)
    return {
        "contract": CONTRACT_VERSION,
        "total": len(values),
        "unique_rule_ids": len(set(ids)),
        "duplicate_rule_ids": sorted(rule_id for rule_id, count in Counter(ids).items() if count > 1),
        "unclassified_rules": 0,
        "rules_inventoried_pct": 100 if values and len(ids) == len(set(ids)) else 0,
        "class_counts": dict(sorted(class_counts.items())),
    }


def validate_structured_claims(
    claims: Sequence[StructuredSemanticClaim],
    *,
    evidence: Mapping[str, EvidenceOwnership],
    numeric: Mapping[str, NumericOwnership],
    decision: DecisionFields,
) -> SemanticValidationResult:
    hard: list[ValidationIssue] = []
    semantic: list[ValidationIssue] = []
    soft: list[ValidationIssue] = []
    seen: set[str] = set()
    unbound_numeric = 0

    for claim in claims:
        if claim.claim_id in seen:
            hard.append(_issue("duplicate_claim_id", ValidationClass.HARD_DETERMINISTIC, claim, "claim_id must be unique"))
        seen.add(claim.claim_id)

        claim_evidence: list[EvidenceOwnership] = []
        for evidence_ref in claim.evidence_refs:
            owned = evidence.get(evidence_ref)
            if owned is None:
                hard.append(_issue("nonexistent_evidence_ref", ValidationClass.HARD_DETERMINISTIC, claim, evidence_ref))
                continue
            claim_evidence.append(owned)
            if owned.ticker != claim.ticker:
                hard.append(_issue("cross_ticker_evidence_ref", ValidationClass.HARD_DETERMINISTIC, claim, evidence_ref))
            if owned.generation_id != claim.generation_id:
                hard.append(_issue("cross_generation_evidence_ref", ValidationClass.HARD_DETERMINISTIC, claim, evidence_ref))
            if owned.denied:
                hard.append(_issue("denied_evidence_ref", ValidationClass.HARD_DETERMINISTIC, claim, evidence_ref))
            elif not owned.semantic_eligible:
                semantic.append(
                    _issue(
                        "semantic_ineligible_evidence_ref",
                        ValidationClass.SEMANTIC_HARD,
                        claim,
                        evidence_ref,
                    )
                )
            elif not owned.prose_eligible:
                semantic.append(
                    _issue(
                        "prose_ineligible_evidence_ref",
                        ValidationClass.SEMANTIC_HARD,
                        claim,
                        evidence_ref,
                    )
                )

        claim_numeric: list[NumericOwnership] = []
        for numeric_ref in claim.numeric_refs:
            owned_numeric = numeric.get(numeric_ref)
            if owned_numeric is None:
                hard.append(_issue("nonexistent_numeric_ref", ValidationClass.HARD_DETERMINISTIC, claim, numeric_ref))
                continue
            claim_numeric.append(owned_numeric)
            if owned_numeric.evidence_ref not in claim.evidence_refs:
                hard.append(_issue("numeric_ref_outside_claim_evidence", ValidationClass.HARD_DETERMINISTIC, claim, numeric_ref))
            source = evidence.get(owned_numeric.evidence_ref)
            if source is None:
                hard.append(_issue("numeric_source_missing", ValidationClass.HARD_DETERMINISTIC, claim, numeric_ref))
            elif source.ticker != claim.ticker or source.generation_id != claim.generation_id:
                hard.append(_issue("numeric_owner_mismatch", ValidationClass.HARD_DETERMINISTIC, claim, numeric_ref))
            elif not source.numeric_eligible:
                hard.append(
                    _issue(
                        "numeric_ineligible_evidence_ref",
                        ValidationClass.HARD_DETERMINISTIC,
                        claim,
                        numeric_ref,
                    )
                )

        has_digit = bool(re.search(r"(?<![A-Za-z])\d", claim.text))
        if has_digit and not claim.numeric_refs:
            unbound_numeric += 1
            hard.append(_issue("freeform_unbound_numeric", ValidationClass.HARD_DETERMINISTIC, claim, "numeric prose requires a registry ref"))

        if claim.claim_type == SemanticClaimType.CURRENT_NUMERIC_FACT:
            if not claim.numeric_refs:
                hard.append(_issue("current_numeric_fact_without_numeric_ref", ValidationClass.HARD_DETERMINISTIC, claim, "CURRENT_NUMERIC_FACT requires numeric_refs"))
            semantic_types = {item.semantic_type.casefold() for item in claim_numeric}
            metrics = {item.casefold() for item in claim.metrics}
            if metrics and semantic_types and not metrics.intersection(semantic_types):
                semantic.append(_issue("numeric_metric_semantic_mismatch", ValidationClass.SEMANTIC_HARD, claim, f"metrics={sorted(metrics)} semantic_types={sorted(semantic_types)}"))

        if claim.claim_type in {SemanticClaimType.CURRENT_FACT, SemanticClaimType.CURRENT_NUMERIC_FACT}:
            if not claim_evidence:
                hard.append(_issue("current_claim_without_evidence", ValidationClass.HARD_DETERMINISTIC, claim, "current claims require evidence"))
            elif all(not item.current for item in claim_evidence):
                semantic.append(_issue("historical_evidence_asserted_current", ValidationClass.SEMANTIC_HARD, claim, "all supporting evidence is historical"))

        if claim.claim_type == SemanticClaimType.VALUATION_INTERPRETATION and claim_evidence:
            if claim.valuation_role is None:
                semantic.append(
                    _issue(
                        "valuation_role_missing",
                        ValidationClass.SEMANTIC_HARD,
                        claim,
                        "valuation claims require a structured valuation role",
                    )
                )
            ineligible = [item.evidence_ref for item in claim_evidence if not item.valuation_eligible]
            if ineligible:
                semantic.append(
                    _issue(
                        "ineligible_valuation_evidence_ref",
                        ValidationClass.SEMANTIC_HARD,
                        claim,
                        ",".join(ineligible),
                    )
                )
            eligible_roles = {item.valuation_role for item in claim_evidence if item.valuation_eligible}
            if claim.valuation_role == ValuationEvidenceRole.INTERPRETATION:
                role_supported = ValuationEvidenceRole.INTERPRETATION in eligible_roles
            else:
                role_supported = bool(
                    eligible_roles
                    & {
                        ValuationEvidenceRole.CAUTION_ONLY,
                        ValuationEvidenceRole.INTERPRETATION,
                    }
                )
            if not role_supported:
                semantic.append(
                    _issue(
                        "valuation_role_not_owned",
                        ValidationClass.SEMANTIC_HARD,
                        claim,
                        f"claim_role={claim.valuation_role}; evidence_roles={sorted(eligible_roles)}",
                    )
                )

        if claim.claim_type == SemanticClaimType.MARKET_EXPECTATION_INTERPRETATION and claim_evidence:
            if not any(item.semantic_family == "market_expectation" for item in claim_evidence):
                semantic.append(_issue("market_expectation_without_owned_evidence", ValidationClass.SEMANTIC_HARD, claim, "expectation claim lacks expectation evidence"))

        severity_requirements = {
            SemanticClaimType.RISK_CONDITION: EvidenceSeverity.WEAKENING,
            SemanticClaimType.BUSINESS_INVALIDATION_CONDITION: EvidenceSeverity.INVALIDATION_CANDIDATE,
        }
        required_severity = severity_requirements.get(claim.claim_type)
        if required_severity is not None:
            if claim.severity is None:
                semantic.append(
                    _issue(
                        "claim_severity_missing",
                        ValidationClass.SEMANTIC_HARD,
                        claim,
                        f"{claim.claim_type} requires structured severity",
                    )
                )
            elif _SEVERITY_RANK[claim.severity] < _SEVERITY_RANK[required_severity]:
                semantic.append(
                    _issue(
                        "claim_type_severity_mismatch",
                        ValidationClass.SEMANTIC_HARD,
                        claim,
                        f"claim_type={claim.claim_type}; severity={claim.severity}",
                    )
                )
            owned_severities = [item.severity for item in claim_evidence if item.severity is not None]
            if claim.severity is not None and (
                not owned_severities
                or max(_SEVERITY_RANK[item] for item in owned_severities)
                < _SEVERITY_RANK[claim.severity]
            ):
                semantic.append(
                    _issue(
                        "unsupported_severity_escalation",
                        ValidationClass.SEMANTIC_HARD,
                        claim,
                        f"claim={claim.severity}; owned={sorted(owned_severities)}",
                    )
                )

        if claim.claim_type == SemanticClaimType.UNKNOWN:
            scope = evidence.get(claim.unknown_scope_ref or "")
            owned_scope = scope.unknown_scope if scope is not None else None
            if owned_scope is None:
                semantic.append(
                    _issue(
                        "unknown_scope_missing",
                        ValidationClass.SEMANTIC_HARD,
                        claim,
                        str(claim.unknown_scope_ref),
                    )
                )
            else:
                expected_scope = (
                    owned_scope.unknown_subject,
                    owned_scope.unknown_metric,
                    owned_scope.unknown_effect,
                )
                actual_scope = (
                    claim.unknown_subject,
                    claim.unknown_metric,
                    claim.unknown_effect,
                )
                if actual_scope != expected_scope:
                    semantic.append(
                        _issue(
                            "unknown_scope_mismatch",
                            ValidationClass.SEMANTIC_HARD,
                            claim,
                            f"expected={expected_scope}; actual={actual_scope}",
                        )
                    )
                if not set(claim.context_refs).issubset(owned_scope.allowed_context_refs):
                    semantic.append(
                        _issue(
                            "unsupported_unknown_context_ref",
                            ValidationClass.SEMANTIC_HARD,
                            claim,
                            ",".join(claim.context_refs),
                        )
                    )
                expected_refs = {claim.unknown_scope_ref, *claim.context_refs}
                if set(claim.evidence_refs) != expected_refs:
                    semantic.append(
                        _issue(
                            "unknown_evidence_scope_escape",
                            ValidationClass.SEMANTIC_HARD,
                            claim,
                            f"expected={sorted(expected_refs)}; actual={sorted(claim.evidence_refs)}",
                        )
                    )
        elif any(
            value is not None
            for value in (
                claim.unknown_scope_ref,
                claim.unknown_subject,
                claim.unknown_metric,
                claim.unknown_effect,
            )
        ) or claim.context_refs:
            semantic.append(
                _issue(
                    "unknown_metadata_on_non_unknown_claim",
                    ValidationClass.SEMANTIC_HARD,
                    claim,
                    "unknown ownership fields are exclusive to UNKNOWN claims",
                )
            )

        if claim.trade_force == "MANDATORY" and claim.trade_action == "SELL":
            if decision.overall_direction in {"BUY", "HOLD"}:
                semantic.append(_issue("mandatory_sell_contradicts_decision", ValidationClass.SEMANTIC_HARD, claim, f"overall_direction={decision.overall_direction}"))

    return SemanticValidationResult(
        hard_issues=tuple(hard),
        semantic_issues=tuple(semantic),
        soft_issues=tuple(soft),
        temporal_grammar_required_for_metric_ownership=0,
        freeform_unbound_numeric=unbound_numeric,
        class_ab_passed=not hard and not semantic,
    )


def _issue(
    code: str,
    validation_class: ValidationClass,
    claim: StructuredSemanticClaim,
    detail: str,
) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        validation_class=validation_class,
        claim_id=claim.claim_id,
        detail=detail,
    )


def classify_repetition(observation: RepetitionObservation) -> RepetitionAssessment:
    if observation.is_required_safety:
        return RepetitionAssessment(
            classification=RepetitionClass.REQUIRED_SAFETY_REPEAT,
            hard_block_candidate=False,
            reason="identical wording is owned by an explicit safety contract",
        )
    if observation.owner == ClaimOwner.DETERMINISTIC_RENDERER:
        return RepetitionAssessment(
            classification=RepetitionClass.RENDERER_OWNED_REPEAT,
            hard_block_candidate=False,
            reason="renderer ownership should be thinned rather than vetoing a safe candidate",
        )
    compact = re.sub(r"\s+", " ", observation.normalized_span).strip()
    lexical_count = len(compact.split())
    if observation.is_structural_heading or (
        lexical_count <= 8 and observation.has_bound_numeric_token
    ):
        return RepetitionAssessment(
            classification=RepetitionClass.BENIGN_TEMPLATE_REPEAT,
            hard_block_candidate=False,
            reason="short structural or bound-numeric pattern carries little substantive rationale",
        )
    if (
        observation.owner == ClaimOwner.AI_WRITER
        and observation.stock_count >= 3
        and observation.evidence_signature_count >= 2
        and len(compact) >= 48
    ):
        return RepetitionAssessment(
            classification=RepetitionClass.MATERIAL_SPAM_REPEAT,
            hard_block_candidate=True,
            reason="long identical rationale spans materially different evidence signatures",
        )
    return RepetitionAssessment(
        classification=RepetitionClass.MODEL_OWNED_SUBSTANTIVE_REPEAT,
        hard_block_candidate=False,
        reason="substantive model repetition merits review or one rewrite, not an automatic veto",
    )


def rewrite_snapshot(claims: Sequence[StructuredSemanticClaim], decision: DecisionFields) -> RewriteInvariantSnapshot:
    return RewriteInvariantSnapshot(
        fact_refs=tuple(sorted({ref for claim in claims for ref in claim.evidence_refs})),
        numeric_refs=tuple(sorted({ref for claim in claims for ref in claim.numeric_refs})),
        decision_fields=decision,
        semantic_claim_types=tuple(sorted((claim.claim_type for claim in claims), key=str)),
        evidence_refs=tuple(sorted(ref for claim in claims for ref in claim.evidence_refs)),
        metrics=tuple(sorted(metric for claim in claims for metric in claim.metrics)),
        claim_severities=tuple(claim.severity for claim in claims),
        valuation_roles=tuple(claim.valuation_role for claim in claims),
        unknown_scopes=tuple(
            (
                claim.unknown_scope_ref,
                claim.unknown_subject,
                claim.unknown_metric,
                claim.unknown_effect,
            )
            for claim in claims
        ),
        context_refs=tuple(sorted(ref for claim in claims for ref in claim.context_refs)),
    )


def evaluate_bounded_rewrite(
    before: RewriteInvariantSnapshot,
    after: RewriteInvariantSnapshot | None,
    *,
    attempted: bool,
    attempt_count: int | None = None,
) -> BoundedRewriteResult:
    attempts = int(attempted) if attempt_count is None else attempt_count
    if attempts > 1:
        return BoundedRewriteResult(
            disposition=RewriteDisposition.REJECTED_INVARIANCE,
            invariant_errors=("rewrite_attempt_limit",),
            class_ab_rerun_required=False,
            original_remains_eligible=True,
            attempt_count=1,
        )
    if not attempted:
        return BoundedRewriteResult(
            disposition=RewriteDisposition.NOT_ATTEMPTED,
            class_ab_rerun_required=False,
            original_remains_eligible=True,
            attempt_count=0,
        )
    if after is None:
        return BoundedRewriteResult(
            disposition=RewriteDisposition.FAILED_KEEP_ORIGINAL,
            class_ab_rerun_required=False,
            original_remains_eligible=True,
            attempt_count=1,
        )
    errors = tuple(
        field
        for field in (
            "fact_refs",
            "numeric_refs",
            "decision_fields",
            "semantic_claim_types",
            "evidence_refs",
            "metrics",
            "claim_severities",
            "valuation_roles",
            "unknown_scopes",
            "context_refs",
        )
        if getattr(before, field) != getattr(after, field)
    )
    if errors:
        return BoundedRewriteResult(
            disposition=RewriteDisposition.REJECTED_INVARIANCE,
            invariant_errors=errors,
            class_ab_rerun_required=False,
            original_remains_eligible=True,
            attempt_count=1,
        )
    return BoundedRewriteResult(
        disposition=RewriteDisposition.SUCCEEDED,
        class_ab_rerun_required=True,
        original_remains_eligible=True,
        attempt_count=1,
    )


def validate_ai_semantic_reviewer(
    result: AISemanticReviewerResult,
    *,
    allowed_claim_ids: Iterable[str],
    allowed_evidence_refs: Iterable[str],
    allowed_numeric_refs: Iterable[str],
) -> ReviewerContractValidation:
    claim_ids = set(allowed_claim_ids)
    evidence_refs = set(allowed_evidence_refs)
    numeric_refs = set(allowed_numeric_refs)
    errors: list[str] = []
    if result.external_fetch_performed:
        errors.append("external_fetch_not_allowed")
    if result.rewrite_performed:
        errors.append("reviewer_rewrite_not_allowed")
    if not set(result.proposed_fact_refs).issubset(evidence_refs):
        errors.append("reviewer_added_fact")
    if not set(result.proposed_numeric_refs).issubset(numeric_refs):
        errors.append("reviewer_added_numeric")
    for issue in result.issues:
        if not set(issue.claim_ids).issubset(claim_ids):
            errors.append("reviewer_unknown_claim")
        if not set(issue.evidence_refs).issubset(evidence_refs):
            errors.append("reviewer_unknown_evidence")
    return ReviewerContractValidation(valid=not errors, errors=tuple(dict.fromkeys(errors)))


def evaluate_shadow_policy(
    validation: SemanticValidationResult,
    *,
    class_c_warning_count: int,
    rewrite: BoundedRewriteResult | None = None,
) -> ShadowPolicyDecision:
    class_a = len(validation.hard_issues)
    class_b = len(validation.semantic_issues)
    old_eligible = class_a == 0 and class_b == 0 and class_c_warning_count == 0
    new_eligible = class_a == 0 and class_b == 0
    disposition = rewrite.disposition if rewrite is not None else RewriteDisposition.NOT_ATTEMPTED
    if class_a:
        reason = "Class A factual safety failure"
    elif class_b:
        reason = "Class B unambiguous semantic contradiction"
    elif class_c_warning_count:
        reason = "Class C warning does not veto a Class A/B-safe original"
    else:
        reason = "all Class A/B checks passed and no Class C warning was observed"
    return ShadowPolicyDecision(
        old_policy_eligible=old_eligible,
        new_shadow_policy_eligible=new_eligible,
        class_a_failures=class_a,
        class_b_failures=class_b,
        class_c_warnings=class_c_warning_count,
        rewrite_disposition=disposition,
        reason=reason,
    )
