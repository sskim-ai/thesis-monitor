from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from enum import StrEnum

from app.services.market_context_adapter_service import NormalizedMarketContext


CONTRACT_VERSION = "kr-market-digest-quality-v1"


class KrEvidencePriority(StrEnum):
    P1_LOCAL_MARKET_STRUCTURE = "P1_KR_LOCAL_MARKET_STRUCTURE"
    P2_LOCAL_MARKET_FLOW = "P2_KR_LOCAL_MARKET_FLOW"
    P3_LOCAL_STOCK_CROSS_SECTION = "P3_KR_LOCAL_STOCK_CROSS_SECTION"
    P4_GLOBAL_CURRENT_CONTEXT = "P4_GLOBAL_CURRENT_CONTEXT"
    P5_REFERENCE_LAGGING_MACRO = "P5_REFERENCE_LAGGING_MACRO"


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
    next_check: KrDigestClaim | None
    global_context_retained: bool
    global_context_reason: str
    concentration_scopes_used: tuple[str, ...]

    def claims(self) -> tuple[KrDigestClaim, ...]:
        return tuple(
            claim
            for claim in (self.judgment, self.interpretation, self.next_check)
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
    if not supporting:
        reasons.append("local_flow_size_sector_context_missing")
    status = bool(
        completed_session
        and kospi_kosdaq_indices
        and kospi_kosdaq_breadth
        and supporting
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
) -> KrMarketDigestPlan:
    context = _normalized_context(value)
    richness = kr_domestic_context_richness(context)
    if context is None or not richness.status:
        return KrMarketDigestPlan(
            contract=CONTRACT_VERSION,
            richness=richness,
            judgment=None,
            interpretation=None,
            next_check=None,
            global_context_retained=False,
            global_context_reason="domestic_context_not_rich",
            concentration_scopes_used=(),
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
    if (
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
    split_foreign = bool(
        flows.get(("KOSPI", "foreign"), 0) < 0
        and flows.get(("KOSDAQ", "foreign"), 0) > 0
    )
    institutions_buy_both = bool(
        flows.get(("KOSPI", "institution"), 0) > 0
        and flows.get(("KOSDAQ", "institution"), 0) > 0
    )
    if split_foreign and institutions_buy_both:
        interpretation_text = (
            "외국인은 KOSPI에서 순매도하고 KOSDAQ에서 순매수한 반면 기관은 "
            "양 시장에서 순매수해, 시장별 참여 흐름이 한 방향으로 정렬되지는 "
            "않았습니다."
        )
        interpretation_priority = KrEvidencePriority.P2_LOCAL_MARKET_FLOW
        interpretation_refs = flow_refs
        next_text = (
            "외국인의 KOSPI 순매도가 이어지는 동안 양 시장의 상승 종목 우위가 "
            "유지되는지 확인합니다."
        )
        next_refs = tuple(dict.fromkeys((*p1_refs, *flow_refs)))
    elif context.size_context:
        returns = {
            item.name: item.return_pct
            for item in context.size_context
            if item.return_pct is not None
        }
        large = returns.get("대형주")
        medium = returns.get("중형주")
        small = returns.get("소형주")
        if large is not None and medium is not None and small is not None and min(
            medium, small
        ) > large:
            interpretation_text = (
                "중형주와 소형주가 대형주보다 강해 국내 상승 참여가 대형주에만 "
                "집중된 구조는 아니었습니다."
            )
        else:
            interpretation_text = (
                "지수와 시장 폭을 함께 보면 국내 상승 참여의 지속 여부가 다음 "
                "판단을 가를 핵심입니다."
            )
        interpretation_priority = KrEvidencePriority.P1_LOCAL_MARKET_STRUCTURE
        interpretation_refs = tuple(item.source_ref for item in context.size_context)
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
        next_check=next_check,
        global_context_retained=contradiction,
        global_context_reason=(
            "supported_global_semiconductor_contradiction_available"
            if contradiction
            else "no_material_global_contradiction_required"
        ),
        concentration_scopes_used=(),
    )
