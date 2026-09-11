"""Pre-model evidence capability for investment-thesis change judgments."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum
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


class BusinessDeltaCapability(StrEnum):
    UNCHANGED_ONLY = "UNCHANGED_ONLY"
    AI_JUDGMENT = "AI_JUDGMENT"
    INPUT_AMBIGUOUS = "INPUT_AMBIGUOUS"


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
_CURRENT_THESIS_CHANGE_ASSERTION = re.compile(
    r"(?:논리|테제|thesis).{0,32}(?:강화|약화|strengthen|weaken)|"
    r"(?:강화|약화|strengthen|weaken).{0,32}(?:논리|테제|thesis)|"
    r"의미\s*있는\s*(?:긍정|부정)\s*변화",
    re.I,
)
_CONFIGURED_CONDITION_FULFILLED = re.compile(
    r"(?:강화|약화|무효화|configured).{0,32}(?:조건|condition).{0,24}"
    r"(?:충족|확인|fulfilled|met)",
    re.I,
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
            return BusinessDeltaEvidenceItem(
                alias=alias,
                canonical_ref=ref.ref_id,
                source_ref=ref.source_ref,
                domain=domain,
                role=BusinessDeltaEvidenceRole.ELIGIBLE_OBSERVED_CHANGE,
                reason="VERIFIED_TYPED_FINANCIAL_COMPARISON",
                supported_change_directions=hints,
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


def attach_business_delta_evidence_view(
    context: Mapping[str, object],
    view: BusinessDeltaEvidenceView,
) -> dict[str, object]:
    if str(context.get("ticker") or "") != view.ticker:
        raise ValueError("business_delta_view_context_ticker_mismatch")
    return {**context, "business_delta_evidence_view": view.model_context()}


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
) -> dict[str, object]:
    enums = business_delta_property_enums(views)
    if set(aliases_by_ticker) != set(views):
        raise ValueError("business_delta_schema_view_scope_mismatch")
    schema = build_alias_constrained_batch_schema(
        candidate_schema=candidate_schema,
        contract=contract,
        packet_id=packet_id,
        aliases_by_ticker=aliases_by_ticker,
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
        if supported and observed not in supported:
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

    if view.capability == BusinessDeltaCapability.UNCHANGED_ONLY and (
        _CURRENT_THESIS_CHANGE_ASSERTION.search(text)
        or _CONFIGURED_CONDITION_FULFILLED.search(text)
    ):
        errors.append("BUSINESS_DELTA_UNCHANGED_CONTEXT_ASSERTS_CHANGE")

    return {
        "contract": CONTRACT_VERSION,
        "ticker": ticker,
        "capability": view.capability.value,
        "observed": observed,
        "selected_refs": list(refs),
        "selected_eligible_refs": [item.canonical_ref for item in selected_eligible],
        "invalid_refs": invalid_refs,
        "errors": list(dict.fromkeys(errors)),
        "business_delta_capability_violation_count": int(bool(errors)),
        "status": "PASS" if not errors else "FAIL",
    }
