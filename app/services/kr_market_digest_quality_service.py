from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from enum import StrEnum

from app.config import get_settings
from app.services.market_context_adapter_service import NormalizedMarketContext


CONTRACT_VERSION = "kr-market-digest-quality-v1"
SECTOR_RANKING_CONTRACT = "kr-sector-relative-ranking-v1"


class KrEvidencePriority(StrEnum):
    P1_LOCAL_MARKET_STRUCTURE = "P1_KR_LOCAL_MARKET_STRUCTURE"
    P2_LOCAL_MARKET_FLOW = "P2_KR_LOCAL_MARKET_FLOW"
    P3_LOCAL_STOCK_CROSS_SECTION = "P3_KR_LOCAL_STOCK_CROSS_SECTION"
    P4_GLOBAL_CURRENT_CONTEXT = "P4_GLOBAL_CURRENT_CONTEXT"
    P5_REFERENCE_LAGGING_MACRO = "P5_REFERENCE_LAGGING_MACRO"


class KrDigestSelectionState(StrEnum):
    SELECTED_REQUIRED = "SELECTED_REQUIRED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    WRONG_SESSION = "WRONG_SESSION"
    INVALID_SEMANTIC = "INVALID_SEMANTIC"
    NO_VALID_ROWS = "NO_VALID_ROWS"


@dataclass(frozen=True)
class KrDigestClaim:
    role: str
    text: str
    priority: KrEvidencePriority
    source_refs: tuple[str, ...]


@dataclass(frozen=True)
class KrDomesticRichness:
    contract: str
    status: bool
    completed_session: bool
    kospi_kosdaq_indices: bool
    kospi_kosdaq_breadth: bool
    supporting_local_context: tuple[str, ...]
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class KrMarketDigestPlan:
    contract: str
    richness: KrDomesticRichness
    judgment: KrDigestClaim | None
    interpretation: KrDigestClaim | None
    size_context: KrDigestClaim | None
    sector_context: KrDigestClaim | None
    next_check: KrDigestClaim | None
    size_style_state: KrDigestSelectionState
    sector_extremes_state: KrDigestSelectionState
    global_context_retained: bool
    global_context_reason: str
    concentration_scopes_used: tuple[str, ...]
    sector_rank_limit: int
    sector_safe_counts: dict[str, int]

    def claims(self) -> tuple[KrDigestClaim, ...]:
        return tuple(
            claim
            for claim in (
                self.judgment,
                self.interpretation,
                self.size_context,
                self.sector_context,
                self.next_check,
            )
            if claim is not None
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _normalized_context(value: object) -> NormalizedMarketContext | None:
    if isinstance(value, NormalizedMarketContext):
        return value
    if not isinstance(value, dict):
        return None
    candidate = value.get("adapter_context", value)
    if not isinstance(candidate, dict):
        return None
    try:
        return NormalizedMarketContext.model_validate(candidate)
    except (TypeError, ValueError):
        return None


def kr_domestic_context_richness(value: object) -> KrDomesticRichness:
    context = _normalized_context(value)
    if context is None or context.market != "KR":
        return KrDomesticRichness(
            contract=CONTRACT_VERSION,
            status=False,
            completed_session=False,
            kospi_kosdaq_indices=False,
            kospi_kosdaq_breadth=False,
            supporting_local_context=(),
            reasons=("typed_kr_context_unavailable",),
        )

    completed_session = bool(
        context.session_context.assessment_state == "final"
        and context.session_context.provider_publication_state == "PROVIDER_COMPLETE"
        and context.session_date
        == context.session_context.latest_completed_regular_session_date
    )
    indices = {
        item.symbol.upper(): item
        for item in context.indices
        if item.as_of_date == context.session_date
    }
    kospi_kosdaq_indices = {"KOSPI", "KOSDAQ"}.issubset(indices)
    breadth = {
        item.scope.upper(): item.breadth for item in context.breadth_by_scope
    }
    kospi_kosdaq_breadth = all(
        scope in breadth
        and breadth[scope].availability == "AVAILABLE"
        and breadth[scope].eligible_count is not None
        for scope in ("KOSPI", "KOSDAQ")
    )
    supporting: list[str] = []
    if context.market_flows:
        supporting.append("market_wide_participant_flow")
    if context.size_context:
        supporting.append("size_style_context")
    if context.sectors:
        supporting.append("sector_context")
    reasons: list[str] = []
    if not completed_session:
        reasons.append("completed_session_not_verified")
    if not kospi_kosdaq_indices:
        reasons.append("kospi_kosdaq_indices_incomplete")
    if not kospi_kosdaq_breadth:
        reasons.append("kospi_kosdaq_breadth_incomplete")
    status = bool(
        completed_session
        and kospi_kosdaq_indices
        and kospi_kosdaq_breadth
    )
    return KrDomesticRichness(
        contract=CONTRACT_VERSION,
        status=status,
        completed_session=completed_session,
        kospi_kosdaq_indices=kospi_kosdaq_indices,
        kospi_kosdaq_breadth=kospi_kosdaq_breadth,
        supporting_local_context=tuple(supporting),
        reasons=tuple(reasons),
    )


def _index_refs(context: NormalizedMarketContext) -> tuple[str, ...]:
    return tuple(
        item.source_ref
        for item in context.indices
        if item.symbol.upper() in {"KOSPI", "KOSDAQ"}
    )


def _breadth_refs(context: NormalizedMarketContext) -> tuple[str, ...]:
    return tuple(
        ref
        for item in context.breadth_by_scope
        if item.scope.upper() in {"KOSPI", "KOSDAQ"}
        for ref in item.breadth.source_refs
    )


def _flow_map(context: NormalizedMarketContext) -> dict[tuple[str, str], float]:
    return {
        (item.scope.upper(), item.participant): item.net_flow
        for item in context.market_flows
        if item.as_of_date == context.session_date
    }


_PARTICIPANT_LABELS = {
    "foreign": "외국인",
    "institution": "기관",
    "retail": "개인",
}

_KOSPI_SIZE_LABELS = (
    ("대형주", "대형"),
    ("중형주", "중형"),
    ("소형주", "소형"),
)
_KOSDAQ_SIZE_LABELS = (
    ("KOSDAQ 100", "KOSDAQ100"),
    ("KOSDAQ MID 300", "MID300"),
    ("KOSDAQ SMALL", "SMALL"),
)
_KOSDAQ_SIZE_NAMES = {name for name, _label in _KOSDAQ_SIZE_LABELS}


def _flow_action(value: float) -> str:
    if value > 0:
        return "순매수"
    if value < 0:
        return "순매도"
    return "중립"


def _participant_flow_clause(
    participant: str,
    flows: dict[tuple[str, str], float],
) -> str | None:
    scopes = [
        scope for scope in ("KOSPI", "KOSDAQ") if (scope, participant) in flows
    ]
    if not scopes:
        return None
    label = _PARTICIPANT_LABELS[participant]
    actions = {
        scope: _flow_action(flows[(scope, participant)]) for scope in scopes
    }
    if len(scopes) == 2 and len(set(actions.values())) == 1:
        return f"{label}은 양 시장에서 {actions[scopes[0]]}했습니다."
    if len(scopes) == 2:
        return (
            f"{label}은 KOSPI에서 {actions['KOSPI']}하고 "
            f"KOSDAQ에서 {actions['KOSDAQ']}했습니다."
        )
    return f"{label}은 {scopes[0]}에서 {actions[scopes[0]]}했습니다."


def _normalized_name(value: str) -> str:
    return " ".join(value.upper().split())


def _display_name(value: str) -> str:
    return re.sub(r"\s*/\s*", "·", value.strip())


def _return_text(value: float) -> str:
    return f"{float(value):+.2f}%"


def _size_claim(
    context: NormalizedMarketContext,
) -> tuple[KrDigestClaim | None, KrDigestSelectionState]:
    current_kospi = [
        item
        for item in context.size_context
        if item.as_of_date == context.session_date
        and item.state == "CURRENT_DIRECTIONAL"
        and item.return_pct is not None
    ]
    current_kosdaq = [
        item
        for item in context.sectors
        if item.market_scope == "KOSDAQ"
        and _normalized_name(item.name) in _KOSDAQ_SIZE_NAMES
        and item.state == "CURRENT_DIRECTIONAL"
        and item.return_pct is not None
        and (item.listed_count is None or item.listed_count > 0)
    ]
    clauses: list[str] = []
    refs: list[str] = []
    for scope, rows, labels in (
        ("KOSPI", current_kospi, _KOSPI_SIZE_LABELS),
        ("KOSDAQ", current_kosdaq, _KOSDAQ_SIZE_LABELS),
    ):
        by_name = {_normalized_name(item.name): item for item in rows}
        required_names = {_normalized_name(name) for name, _label in labels}
        if set(by_name) != required_names:
            continue
        rendered = []
        for name, label in labels:
            item = by_name[_normalized_name(name)]
            rendered.append(f"{label} {_return_text(float(item.return_pct))}")
            refs.append(item.source_ref)
        prefix = "KOSPI " if scope == "KOSPI" else ""
        clauses.append(f"{prefix}{' · '.join(rendered)}")
    if clauses:
        return (
            KrDigestClaim(
                role="size_context",
                text=f"규모별: {'; '.join(clauses)}.",
                priority=KrEvidencePriority.P1_LOCAL_MARKET_STRUCTURE,
                source_refs=tuple(dict.fromkeys(refs)),
            ),
            KrDigestSelectionState.SELECTED_REQUIRED,
        )
    if any(item.as_of_date != context.session_date for item in context.size_context):
        return None, KrDigestSelectionState.WRONG_SESSION
    if context.size_context or current_kosdaq:
        return None, KrDigestSelectionState.INVALID_SEMANTIC
    return None, KrDigestSelectionState.NO_VALID_ROWS


def _sector_claim(
    context: NormalizedMarketContext,
    *,
    rank_limit: int,
) -> tuple[KrDigestClaim | None, KrDigestSelectionState, dict[str, int]]:
    if rank_limit not in {1, 3}:
        raise ValueError("KR sector rank limit must be 1 or 3")
    strongest_clauses: list[str] = []
    weakest_clauses: list[str] = []
    refs: list[str] = []
    valid_rows = 0
    stale_rows = 0
    safe_counts: dict[str, int] = {}
    for scope in ("KOSPI", "KOSDAQ"):
        candidates = [
            item
            for item in context.sectors
            if item.market_scope == scope
            and item.basis == "actual_sector_breadth"
            and item.state == "CURRENT_DIRECTIONAL"
            and item.return_pct is not None
            and (item.listed_count is None or item.listed_count > 0)
            and not (
                scope == "KOSDAQ"
                and _normalized_name(item.name) in _KOSDAQ_SIZE_NAMES
            )
        ]
        stale_rows += sum(
            item.as_of_date is not None and item.as_of_date != context.session_date
            for item in candidates
        )
        current_by_name: dict[str, object] = {}
        for item in sorted(
            candidates,
            key=lambda value: (_normalized_name(value.name), value.source_ref),
        ):
            if item.as_of_date is not None and item.as_of_date != context.session_date:
                continue
            current_by_name.setdefault(_normalized_name(item.name), item)
        current = list(current_by_name.values())
        safe_counts[scope] = len(current)
        valid_rows += len(current)
        if not current:
            continue
        descending = sorted(
            current,
            key=lambda item: (
                -float(item.return_pct),
                _normalized_name(item.name),
                item.source_ref,
            ),
        )
        ascending = sorted(
            current,
            key=lambda item: (
                float(item.return_pct),
                _normalized_name(item.name),
                item.source_ref,
            ),
        )
        if rank_limit == 3 and len(current) < 3:
            strongest = descending[:1]
            strongest_refs = {item.source_ref for item in strongest}
            weakest = [
                item for item in ascending if item.source_ref not in strongest_refs
            ][:1]
        else:
            strongest = descending[:rank_limit]
            weakest = ascending[:rank_limit]
        if strongest:
            strongest_clauses.append(
                f"{scope} "
                + " · ".join(
                    f"{_display_name(item.name)} "
                    f"{_return_text(float(item.return_pct))}"
                    for item in strongest
                )
            )
            refs.extend(item.source_ref for item in strongest)
        if weakest:
            weakest_clauses.append(
                f"{scope} "
                + " · ".join(
                    f"{_display_name(item.name)} "
                    f"{_return_text(float(item.return_pct))}"
                    for item in weakest
                )
            )
            refs.extend(item.source_ref for item in weakest)
    if not strongest_clauses:
        return (
            None,
            (
                KrDigestSelectionState.WRONG_SESSION
                if stale_rows
                else KrDigestSelectionState.INVALID_SEMANTIC
                if valid_rows
                else KrDigestSelectionState.NO_VALID_ROWS
            ),
            safe_counts,
        )
    scope_delimiter = " · " if rank_limit == 1 else "; "
    text_parts = [
        f"업종 상대 강세: {scope_delimiter.join(strongest_clauses)}."
    ]
    if weakest_clauses:
        text_parts.append(
            f"업종 상대 약세: {scope_delimiter.join(weakest_clauses)}."
        )
    return (
        KrDigestClaim(
            role="sector_context",
            text=" ".join(text_parts),
            priority=KrEvidencePriority.P3_LOCAL_STOCK_CROSS_SECTION,
            source_refs=tuple(dict.fromkeys(refs)),
        ),
        KrDigestSelectionState.SELECTED_REQUIRED,
        safe_counts,
    )


def _global_contradiction(text: str) -> bool:
    return bool(
        re.search(
            r"(?:미국|글로벌|해외).{0,30}(?:반도체|성장주).{0,20}(?:약세|부진|압력)",
            text,
            re.IGNORECASE,
        )
    )


def build_kr_market_digest_plan(
    value: object,
    *,
    available_text: str = "",
    sector_rank_limit: int | None = None,
) -> KrMarketDigestPlan:
    effective_sector_rank_limit = (
        sector_rank_limit
        if sector_rank_limit is not None
        else 3
        if get_settings().kr_market_sector_top3_enabled
        else 1
    )
    context = _normalized_context(value)
    richness = kr_domestic_context_richness(context)
    if context is None or not richness.status:
        return KrMarketDigestPlan(
            contract=CONTRACT_VERSION,
            richness=richness,
            judgment=None,
            interpretation=None,
            size_context=None,
            sector_context=None,
            next_check=None,
            size_style_state=KrDigestSelectionState.SOURCE_UNAVAILABLE,
            sector_extremes_state=KrDigestSelectionState.SOURCE_UNAVAILABLE,
            global_context_retained=False,
            global_context_reason="domestic_context_not_rich",
            concentration_scopes_used=(),
            sector_rank_limit=effective_sector_rank_limit,
            sector_safe_counts={},
        )

    indices = {item.symbol.upper(): item for item in context.indices}
    breadth = {
        item.scope.upper(): item.breadth for item in context.breadth_by_scope
    }
    kospi = indices["KOSPI"]
    kosdaq = indices["KOSDAQ"]
    kospi_breadth = breadth["KOSPI"]
    kosdaq_breadth = breadth["KOSDAQ"]
    both_positive_breadth = bool(
        kospi_breadth.breadth_ratio is not None
        and kosdaq_breadth.breadth_ratio is not None
        and kospi_breadth.breadth_ratio > 0.5
        and kosdaq_breadth.breadth_ratio > 0.5
    )
    opposite_index_directions = bool(
        kospi.return_pct is not None
        and kosdaq.return_pct is not None
        and (
            (kospi.return_pct > 0 >= kosdaq.return_pct)
            or (kosdaq.return_pct > 0 >= kospi.return_pct)
        )
    )
    if opposite_index_directions:
        kospi_direction = (
            "상승"
            if float(kospi.return_pct) > 0
            else "하락"
            if float(kospi.return_pct) < 0
            else "보합"
        )
        kosdaq_direction = (
            "상승"
            if float(kosdaq.return_pct) > 0
            else "하락"
            if float(kosdaq.return_pct) < 0
            else "보합"
        )
        breadth_text = (
            "두 시장 모두 상승 종목이 하락 종목보다 많았습니다"
            if both_positive_breadth
            else "양 시장의 시장 폭은 같은 방향으로 정렬되지 않았습니다"
        )
        judgment_text = (
            f"KOSPI는 {kospi_direction}, KOSDAQ은 {kosdaq_direction}으로 지수 방향이 "
            f"달랐지만 {breadth_text}."
        )
    elif (
        kospi.return_pct is not None
        and kosdaq.return_pct is not None
        and kosdaq.return_pct > kospi.return_pct
        and both_positive_breadth
    ):
        judgment_text = (
            "KOSDAQ이 KOSPI보다 강했고 두 시장 모두 상승 종목이 하락 종목보다 "
            "많아, 국내 장의 폭을 한 지수 흐름만으로 설명하기 어렵습니다."
        )
    elif both_positive_breadth:
        judgment_text = (
            "KOSPI와 KOSDAQ 모두 상승 종목이 하락 종목보다 많아 국내 참여 폭이 "
            "양 시장에 걸쳐 확인됐습니다."
        )
    else:
        judgment_text = (
            "KOSPI와 KOSDAQ의 지수 방향과 시장 폭이 엇갈려 국내 장을 하나의 "
            "방향으로 묶기 어렵습니다."
        )
    p1_refs = tuple(dict.fromkeys((*_index_refs(context), *_breadth_refs(context))))
    judgment = KrDigestClaim(
        role="judgment",
        text=judgment_text,
        priority=KrEvidencePriority.P1_LOCAL_MARKET_STRUCTURE,
        source_refs=p1_refs,
    )

    flows = _flow_map(context)
    flow_refs = tuple(
        item.source_ref
        for item in context.market_flows
        if item.as_of_date == context.session_date
    )
    flow_clauses = [
        clause
        for participant in _PARTICIPANT_LABELS
        if (clause := _participant_flow_clause(participant, flows)) is not None
    ]
    size_context, size_style_state = _size_claim(context)
    sector_context, sector_extremes_state, sector_safe_counts = _sector_claim(
        context,
        rank_limit=effective_sector_rank_limit,
    )
    if flow_clauses:
        interpretation_text = " ".join(flow_clauses)
        interpretation_priority = KrEvidencePriority.P2_LOCAL_MARKET_FLOW
        interpretation_refs = flow_refs
        next_text = (
            "양 시장의 상승 종목 우위가 유지되는지, 외국인·기관의 시장별 "
            "수급 방향과 함께 확인합니다."
            if both_positive_breadth
            else "양 시장의 상승·하락 종목 분포와 외국인·기관의 시장별 수급 "
            "방향이 함께 유지되는지 확인합니다."
        )
        next_refs = tuple(dict.fromkeys((*p1_refs, *flow_refs)))
    elif size_context is not None:
        interpretation_text = size_context.text
        interpretation_priority = KrEvidencePriority.P1_LOCAL_MARKET_STRUCTURE
        interpretation_refs = size_context.source_refs
        next_text = "양 시장의 상승 종목 우위와 중소형주 상대 흐름이 이어지는지 확인합니다."
        next_refs = tuple(dict.fromkeys((*p1_refs, *interpretation_refs)))
    else:
        interpretation_text = (
            "양 시장의 폭이 함께 확인됐지만 이 한 번의 관측만으로 전면적 "
            "위험선호나 지속적인 순환을 확정하지 않습니다."
        )
        interpretation_priority = KrEvidencePriority.P1_LOCAL_MARKET_STRUCTURE
        interpretation_refs = p1_refs
        next_text = "다음 국내 장에서도 양 시장의 상승 종목 우위가 유지되는지 확인합니다."
        next_refs = p1_refs

    interpretation = KrDigestClaim(
        role="interpretation",
        text=interpretation_text,
        priority=interpretation_priority,
        source_refs=interpretation_refs,
    )
    next_check = KrDigestClaim(
        role="next_check",
        text=next_text,
        priority=(
            KrEvidencePriority.P2_LOCAL_MARKET_FLOW
            if flow_refs
            else KrEvidencePriority.P1_LOCAL_MARKET_STRUCTURE
        ),
        source_refs=next_refs,
    )
    contradiction = _global_contradiction(available_text)
    return KrMarketDigestPlan(
        contract=CONTRACT_VERSION,
        richness=richness,
        judgment=judgment,
        interpretation=interpretation,
        size_context=size_context,
        sector_context=sector_context,
        next_check=next_check,
        size_style_state=size_style_state,
        sector_extremes_state=sector_extremes_state,
        global_context_retained=contradiction,
        global_context_reason=(
            "supported_global_semiconductor_contradiction_available"
            if contradiction
            else "no_material_global_contradiction_required"
        ),
        concentration_scopes_used=(),
        sector_rank_limit=effective_sector_rank_limit,
        sector_safe_counts=sector_safe_counts,
    )
