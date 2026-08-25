from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass, replace
from enum import StrEnum

from app.services.free_analyst_message_service import (
    _content_lines,
    _sections,
    _sentences,
    numeric_tokens,
    parse_rendered_message,
)
from app.services.kr_market_digest_quality_service import (
    KrMarketDigestPlan,
    build_kr_market_digest_plan,
)


CONTRACT_VERSION = "evidence-locked-free-analyst-v1"
SEMANTIC_OWNERSHIP_CONTRACT_VERSION = "free-analyst-semantic-ownership-v1"


class SupportType(StrEnum):
    DIRECT_FACT = "DIRECT_FACT"
    DIRECT_RELATION = "DIRECT_RELATION"
    THESIS_LINKAGE = "THESIS_LINKAGE"
    BOUNDED_INFERENCE = "BOUNDED_INFERENCE"
    ALTERNATIVE_INTERPRETATION = "ALTERNATIVE_INTERPRETATION"
    UNCERTAINTY_BOUNDARY = "UNCERTAINTY_BOUNDARY"
    EXPECTATION_VALUATION_LINK = "EXPECTATION_VALUATION_LINK"
    POSITIONING_SYNTHESIS = "POSITIONING_SYNTHESIS"


class InferenceRule(StrEnum):
    TEMPORAL_EVIDENCE_BOUNDARY = "temporal_evidence_boundary"
    INVENTORY_NOT_OUTPACING_SCALE = "inventory_not_outpacing_scale"
    INVENTORY_OUTPACING_SCALE = "inventory_outpacing_scale"
    INVENTORY_ALTERNATIVES = "inventory_alternatives"
    INSURANCE_APPLICABILITY = "insurance_applicability"
    ORDER_TO_CASH_GAP = "order_to_cash_gap"
    CONTRACT_ASSET_RECOVERY_GAP = "contract_asset_recovery_gap"
    FLEET_INVESTMENT_RECOVERY_GAP = "fleet_investment_recovery_gap"
    HPC_EXECUTION_THRESHOLD = "hpc_execution_threshold"
    PLATFORM_REVENUE_QUALITY_GAP = "platform_revenue_quality_gap"
    FCF_CAPEX_RECOVERY = "fcf_capex_recovery"
    MEMORY_CYCLE_FCF = "memory_cycle_fcf"
    EXPECTATION_VERIFICATION_THRESHOLD = "expectation_verification_threshold"
    POSITIONING_FUNDAMENTAL_BOUNDARY = "positioning_fundamental_boundary"
    PRICE_EXECUTION_SEPARATION = "price_execution_separation"
    UNKNOWN_TO_NEXT_EVIDENCE = "unknown_to_next_evidence"


class ConfidenceLabel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Direction(StrEnum):
    SUPPORTS = "supports"
    CHALLENGES = "challenges"
    MIXED = "mixed"
    NEUTRAL = "neutral"


class CurrentBalance(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    MIXED = "mixed"
    UNRESOLVED = "unresolved"


class SemanticConceptFamily(StrEnum):
    MEMORY_HBM = "memory_hbm"
    MEMORY_ASP = "memory_asp"
    MEMORY_PRODUCT_MIX = "memory_product_mix"
    OPERATING_PRODUCT_MIX = "operating_product_mix"
    DEFENSE_BACKLOG = "defense_backlog"
    DEFENSE_DELIVERY = "defense_delivery"
    DEFENSE_PROJECT_MARGIN = "defense_project_margin"
    INSURANCE_UNDERWRITING = "insurance_underwriting"
    LOGISTICS_FREIGHT = "logistics_freight"
    CLOUD_AI_CAPEX = "cloud_ai_capex"
    HPC_EXECUTION = "hpc_execution"
    FOUNDRY_ADVANCED_NODE = "foundry_advanced_node"
    FOUNDRY_WAFER_ASP = "foundry_wafer_asp"


@dataclass(frozen=True)
class SemanticOwnerIdentity:
    entity_owner: str
    ticker_owner: str
    market_owner: str
    packet_owner: str


@dataclass(frozen=True)
class ClaimOwnership:
    contract: str
    entity_owner: str
    ticker_owner: str
    market_owner: str
    packet_owner: str
    industry_context_owner: str
    thesis_driver_refs: tuple[str, ...]
    fact_refs: tuple[str, ...]
    relation_refs: tuple[str, ...]
    expectation_refs: tuple[str, ...]
    valuation_refs: tuple[str, ...]
    unknown_refs: tuple[str, ...]
    concept_families: tuple[SemanticConceptFamily, ...]
    expectation_level: str


@dataclass(frozen=True)
class EvidenceAtom:
    ref: str
    section_key: str
    text: str
    owner: SemanticOwnerIdentity
    concept_families: tuple[SemanticConceptFamily, ...]


@dataclass(frozen=True)
class AnalysisItem:
    item_id: str
    text: str
    support_type: SupportType
    evidence_refs: tuple[str, ...]
    materiality_reason: str
    confidence_label: ConfidenceLabel
    rule_id: InferenceRule | None = None
    direction: Direction = Direction.NEUTRAL
    boundary: str = ""
    ownership: ClaimOwnership | None = None


@dataclass(frozen=True)
class AlternativeInterpretation:
    item_id: str
    positive_interpretation: AnalysisItem
    negative_interpretation: AnalysisItem
    evidence_refs: tuple[str, ...]
    current_balance: CurrentBalance
    unresolved_reason: str


@dataclass(frozen=True)
class UnknownItem:
    unresolved_question: str
    why_it_matters: str
    evidence_needed: str
    evidence_refs: tuple[str, ...]
    ownership: ClaimOwnership | None = None


@dataclass(frozen=True)
class NextCheck:
    check: str
    linked_thesis_driver: str
    linked_unknown: str
    evidence_refs: tuple[str, ...]
    ownership: ClaimOwnership | None = None


@dataclass(frozen=True)
class MessagePlan:
    primary_conclusion: str
    selected_blocks: tuple[str, ...]
    omitted_blocks: tuple[str, ...]
    omission_reasons: tuple[str, ...]


@dataclass(frozen=True)
class FreeAnalystAnalysis:
    analysis_version: str
    benchmark_id: str
    semantic_owner: SemanticOwnerIdentity
    industry_context_owner: str
    preamble: str
    evidence_catalog: tuple[EvidenceAtom, ...]
    top_findings: tuple[AnalysisItem, ...]
    thesis_implications: tuple[AnalysisItem, ...]
    alternative_interpretations: tuple[AlternativeInterpretation, ...]
    expectation_valuation_interaction: tuple[AnalysisItem, ...]
    positioning_synthesis: tuple[AnalysisItem, ...]
    unknowns: tuple[UnknownItem, ...]
    next_checks: tuple[NextCheck, ...]
    message_plan: MessagePlan

    def analysis_items(self) -> tuple[AnalysisItem, ...]:
        alternatives = tuple(
            item
            for row in self.alternative_interpretations
            for item in (row.positive_interpretation, row.negative_interpretation)
        )
        return (
            *self.top_findings,
            *self.thesis_implications,
            *alternatives,
            *self.expectation_valuation_interaction,
            *self.positioning_synthesis,
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    item_id: str
    detail: str


@dataclass(frozen=True)
class SynthesisValidation:
    status: str
    issues: tuple[ValidationIssue, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SentenceSupport:
    final_sentence: str
    analysis_item_id: str
    support_type: SupportType
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class RenderedFreeAnalyst:
    renderer: str
    text: str
    sentence_supports: tuple[SentenceSupport, ...]


_RULE_REQUIRED_SECTIONS: dict[InferenceRule, frozenset[str]] = {
    InferenceRule.TEMPORAL_EVIDENCE_BOUNDARY: frozenset({"core", "risk"}),
    InferenceRule.INVENTORY_NOT_OUTPACING_SCALE: frozenset({"business"}),
    InferenceRule.INVENTORY_OUTPACING_SCALE: frozenset({"business"}),
    InferenceRule.INVENTORY_ALTERNATIVES: frozenset({"business"}),
    InferenceRule.INSURANCE_APPLICABILITY: frozenset({"core", "business"}),
    InferenceRule.ORDER_TO_CASH_GAP: frozenset({"core", "business", "next_check"}),
    InferenceRule.CONTRACT_ASSET_RECOVERY_GAP: frozenset({"core", "business", "next_check"}),
    InferenceRule.FLEET_INVESTMENT_RECOVERY_GAP: frozenset({"core", "business", "next_check"}),
    InferenceRule.HPC_EXECUTION_THRESHOLD: frozenset(
        {"metadata", "core", "business", "next_check"}
    ),
    InferenceRule.PLATFORM_REVENUE_QUALITY_GAP: frozenset(
        {"metadata", "core", "business", "next_check"}
    ),
    InferenceRule.FCF_CAPEX_RECOVERY: frozenset({"core", "business", "next_check"}),
    InferenceRule.MEMORY_CYCLE_FCF: frozenset({"metadata", "core", "business", "next_check"}),
    InferenceRule.EXPECTATION_VERIFICATION_THRESHOLD: frozenset({"metadata", "core", "next_check"}),
    InferenceRule.POSITIONING_FUNDAMENTAL_BOUNDARY: frozenset({"supply"}),
    InferenceRule.PRICE_EXECUTION_SEPARATION: frozenset({"price", "core"}),
    InferenceRule.UNKNOWN_TO_NEXT_EVIDENCE: frozenset({"core", "next_check"}),
}

_BOUNDED_MARKERS = (
    "현재 자료",
    "현재 판단",
    "새 관측",
    "시사",
    "가능성",
    "단정",
    "확인",
    "확정",
    "열려",
    "필요",
    "그 자체로",
    "볼 수 없",
    "뜻하지",
)
_FORBIDDEN_OUTPUT = re.compile(
    r"(?:FCF\s*(?:yield|수익률|/share|주당)|EV\s*/\s*FCF|P\s*/\s*FCF|"
    r"\b(?:DSO|DPO|CCC|ROIC)\b|Trade\s*AR|trade receivables?|"
    r"매출채권\s*(?:증가율|금액|잔액)|고객\s*채택이\s*가속)",
    re.IGNORECASE,
)
_CAUSAL_OVERREACH = re.compile(
    r"(?:수요가?\s*(?:붕괴|확정적으로 감소)|사업\s*실패가?\s*확정|"
    r"재고\s*증가로\s*인해\s*매출|외국인.*(?:투자 논리|사업).*(?:약화|훼손))"
)
_STRONG_CAUSE = re.compile(r"(?:원인이다|때문이다|확정한다|증명한다)")
_REFERENCE_LAG = re.compile(
    r"(?:직전|이전 세션|reference|지연 공표|오늘의 신규 관측은 아닙니다)",
    re.IGNORECASE,
)
_EXTERNAL_TOKEN = re.compile(r"\b[A-Z][A-Z0-9-]{2,}\b")
_ALLOWED_ANALYTIC_TOKENS = {
    "AI",
    "ASP",
    "CAPEX",
    "FCF",
    "HBM",
    "HPC",
    "PPE",
    "USDC",
}

_ENTITY_LINE = re.compile(r"^🏢\s*(?P<entity>.+?)\((?P<ticker>[^()]+)\)\s*$", re.MULTILINE)


def _semantic_owner(
    current_ai_text: str,
    *,
    benchmark_id: str,
    market: str | None,
    packet_owner: str | None,
) -> SemanticOwnerIdentity:
    matched = _ENTITY_LINE.search(current_ai_text)
    entity = matched.group("entity").strip() if matched else "market"
    ticker = matched.group("ticker").strip() if matched else ""
    inferred_market = market
    if inferred_market is None:
        preamble = parse_rendered_message(current_ai_text).preamble
        if re.search(r"(?:\bKR\b|한국|국내)", preamble, re.IGNORECASE):
            inferred_market = "kr"
        elif re.search(r"(?:\bUS\b|미국)", preamble, re.IGNORECASE):
            inferred_market = "us"
        else:
            inferred_market = "unknown"
    return SemanticOwnerIdentity(
        entity_owner=entity,
        ticker_owner=ticker,
        market_owner=inferred_market,
        packet_owner=packet_owner or benchmark_id,
    )


def _industry_context_owner(text: str) -> str:
    checks = (
        (
            "semiconductor_foundry",
            r"(?:첨단공정|선단공정|wafer\s*ASP|파운드리|foundry|해외\s*팹)",
        ),
        ("memory", r"(?:HBM|DRAM|NAND|메모리)"),
        ("defense", r"(?:지상방산|방산|K9|천무)"),
        ("steel_materials", r"(?:철강|스프레드|원재료)"),
        ("insurance", r"(?:보험영업|재보험|합산비율|combined ratio|CSM)"),
        ("logistics", r"(?:물류|선대|운임|freight)"),
        ("cloud_platform", r"(?:AI·Cloud|Cloud 성장|클라우드 마진)"),
        (
            "hpc_data_center",
            r"(?:HPC|colocation|코로케이션|billing|leased customer power|가동·매출|energized capacity)",
        ),
    )
    for owner, pattern in checks:
        if re.search(pattern, text, re.IGNORECASE):
            return owner
    return "general"


def _concept_families(
    text: str,
    *,
    industry_context_owner: str,
) -> tuple[SemanticConceptFamily, ...]:
    concepts: list[SemanticConceptFamily] = []

    def add(concept: SemanticConceptFamily, pattern: str) -> None:
        if re.search(pattern, text, re.IGNORECASE):
            concepts.append(concept)

    add(SemanticConceptFamily.MEMORY_HBM, r"(?<![A-Z0-9])HBM(?![A-Z0-9])")
    add(SemanticConceptFamily.MEMORY_ASP, r"(?<![A-Z0-9])ASP(?![A-Z0-9])")
    if re.search(r"(?:제품\s*믹스|product\s+mix)", text, re.IGNORECASE):
        concepts.append(
            SemanticConceptFamily.MEMORY_PRODUCT_MIX
            if industry_context_owner == "memory"
            else SemanticConceptFamily.OPERATING_PRODUCT_MIX
        )
    if industry_context_owner == "defense":
        add(SemanticConceptFamily.DEFENSE_BACKLOG, r"(?:수주잔고|대형\s*수주)")
        add(SemanticConceptFamily.DEFENSE_DELIVERY, r"(?:인도|납품)")
        add(SemanticConceptFamily.DEFENSE_PROJECT_MARGIN, r"(?:방산.*마진|지상방산.*수익성)")
    add(SemanticConceptFamily.INSURANCE_UNDERWRITING, r"(?:보험영업|합산비율|combined ratio|CSM)")
    add(SemanticConceptFamily.LOGISTICS_FREIGHT, r"(?:선대|운임|freight)")
    add(SemanticConceptFamily.CLOUD_AI_CAPEX, r"(?:AI.*Cloud|Cloud.*(?:CAPEX|투자)|AI\s*투자)")
    add(SemanticConceptFamily.HPC_EXECUTION, r"(?:HPC|가동.*매출.*현금전환)")
    add(
        SemanticConceptFamily.FOUNDRY_ADVANCED_NODE,
        r"(?:첨단공정|선단공정|파운드리|foundry|해외\s*팹)",
    )
    add(SemanticConceptFamily.FOUNDRY_WAFER_ASP, r"(?:wafer\s*ASP)")
    return tuple(dict.fromkeys(concepts))


def _expectation_level(catalog: tuple[EvidenceAtom, ...]) -> str:
    text = _source_text(catalog, _expectation_ref(catalog))
    if not text:
        return "unknown"
    return text.split(":", 1)[-1].strip()


def _claim_ownership(
    *,
    owner: SemanticOwnerIdentity,
    industry_context_owner: str,
    evidence_refs: tuple[str, ...],
    catalog: tuple[EvidenceAtom, ...],
    text: str,
) -> ClaimOwnership:
    by_ref = {atom.ref: atom for atom in catalog}

    def refs_for(*section_keys: str) -> tuple[str, ...]:
        wanted = set(section_keys)
        return tuple(
            ref for ref in evidence_refs if ref in by_ref and by_ref[ref].section_key in wanted
        )

    return ClaimOwnership(
        contract=SEMANTIC_OWNERSHIP_CONTRACT_VERSION,
        entity_owner=owner.entity_owner,
        ticker_owner=owner.ticker_owner,
        market_owner=owner.market_owner,
        packet_owner=owner.packet_owner,
        industry_context_owner=industry_context_owner,
        thesis_driver_refs=refs_for("core", "next_check"),
        fact_refs=refs_for("business"),
        relation_refs=refs_for("business", "supply"),
        expectation_refs=tuple(
            ref
            for ref in refs_for("metadata")
            if by_ref[ref].text.startswith("시장 기대:")
        ),
        valuation_refs=refs_for("valuation"),
        unknown_refs=refs_for("unknown", "next_check"),
        concept_families=_concept_families(
            text,
            industry_context_owner=industry_context_owner,
        ),
        expectation_level=_expectation_level(catalog),
    )


def _bind_item_ownership(
    item: AnalysisItem,
    *,
    owner: SemanticOwnerIdentity,
    industry_context_owner: str,
    catalog: tuple[EvidenceAtom, ...],
) -> AnalysisItem:
    return replace(
        item,
        ownership=_claim_ownership(
            owner=owner,
            industry_context_owner=industry_context_owner,
            evidence_refs=item.evidence_refs,
            catalog=catalog,
            text=item.text,
        ),
    )


def _safe_id(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return normalized or "benchmark"


def build_evidence_catalog(
    current_ai_text: str,
    *,
    owner: SemanticOwnerIdentity | None = None,
    benchmark_id: str = "analysis",
    market: str | None = None,
    packet_owner: str | None = None,
    prefix: str = "evidence",
) -> tuple[EvidenceAtom, ...]:
    parsed = parse_rendered_message(current_ai_text)
    resolved_owner = owner or _semantic_owner(
        current_ai_text,
        benchmark_id=benchmark_id,
        market=market,
        packet_owner=packet_owner,
    )
    industry_owner = (
        "market_global" if not resolved_owner.ticker_owner else _industry_context_owner(current_ai_text)
    )
    atoms: list[EvidenceAtom] = []
    metadata_index = 0
    for line in _content_lines(parsed.preamble):
        metadata_index += 1
        atoms.append(
            EvidenceAtom(
                f"{prefix}:metadata:{metadata_index:02d}",
                "metadata",
                line,
                resolved_owner,
                _concept_families(line, industry_context_owner=industry_owner),
            )
        )
    section_counts: Counter[str] = Counter()
    for section in parsed.sections:
        section_counts[section.key] += 1
        atoms.append(
            EvidenceAtom(
                f"{prefix}:{section.key}:{section_counts[section.key]:02d}",
                section.key,
                section.body,
                resolved_owner,
                _concept_families(section.body, industry_context_owner=industry_owner),
            )
        )
    return tuple(atoms)


def _refs(catalog: tuple[EvidenceAtom, ...], *section_keys: str) -> tuple[str, ...]:
    wanted = set(section_keys)
    return tuple(atom.ref for atom in catalog if atom.section_key in wanted)


def _source_text(catalog: tuple[EvidenceAtom, ...], refs: tuple[str, ...]) -> str:
    by_ref = {atom.ref: atom.text for atom in catalog}
    return "\n".join(by_ref[ref] for ref in refs if ref in by_ref)


def _first_body(current_ai_text: str, key: str) -> str:
    rows = _sections(parse_rendered_message(current_ai_text), key)
    return rows[0].body if rows else ""


def _supporting_refs(
    catalog: tuple[EvidenceAtom, ...],
    *section_keys: str,
) -> tuple[str, ...]:
    wanted = set(section_keys)
    return tuple(
        atom.ref
        for atom in catalog
        if atom.ref.startswith("supporting:") and atom.section_key in wanted
    )


def _first_content_sentence(text: str, key: str) -> str:
    body = _first_body(text, key)
    for line in _content_lines(body):
        cleaned = _clean_bullet(line)
        if cleaned:
            return cleaned
    return ""


def _best_specific_core_sentence(text: str) -> str:
    body = _first_body(text, "core")
    candidates = [sentence.strip() for sentence in _sentences(body) if sentence.strip()]
    generic = re.compile(
        r"(?:현재 근거는 핵심 사업 조건|투자 논리의 다음 확인까지 닫지는 못)"
    )
    specific = [sentence for sentence in candidates if not generic.search(sentence)]
    if not specific:
        return ""
    return min(
        specific,
        key=lambda sentence: (
            len(numeric_tokens(sentence)),
            len(sentence),
        ),
    )


def _expectation_ref(catalog: tuple[EvidenceAtom, ...]) -> tuple[str, ...]:
    return tuple(
        atom.ref
        for atom in catalog
        if atom.section_key == "metadata" and atom.text.startswith("시장 기대:")
    )


def _item(
    *,
    item_id: str,
    text: str,
    support_type: SupportType,
    evidence_refs: tuple[str, ...],
    materiality_reason: str,
    rule_id: InferenceRule | None,
    boundary: str,
    direction: Direction = Direction.NEUTRAL,
    confidence: ConfidenceLabel = ConfidenceLabel.MEDIUM,
) -> AnalysisItem:
    return AnalysisItem(
        item_id=item_id,
        text=text,
        support_type=support_type,
        evidence_refs=evidence_refs,
        materiality_reason=materiality_reason,
        confidence_label=confidence,
        rule_id=rule_id,
        direction=direction,
        boundary=boundary,
    )


def _clean_bullet(value: str) -> str:
    return re.sub(r"^[•*-]\s*", "", value.strip())


def _next_check(current_ai_text: str, catalog: tuple[EvidenceAtom, ...]) -> tuple[NextCheck, ...]:
    body = _first_body(current_ai_text, "next_check")
    if not body:
        body = _first_body(current_ai_text, "risk")
    lines = _content_lines(body)
    if not lines:
        return ()
    check = _clean_bullet(lines[0])
    return (
        NextCheck(
            check=check,
            linked_thesis_driver="current core judgment",
            linked_unknown=check,
            evidence_refs=_refs(catalog, "core", "next_check") or _refs(catalog, "risk"),
        ),
    )


def _unknowns(current_ai_text: str, catalog: tuple[EvidenceAtom, ...]) -> tuple[UnknownItem, ...]:
    body = _first_body(current_ai_text, "unknown")
    if not body:
        return ()
    question = _clean_bullet(_content_lines(body)[0])
    return (
        UnknownItem(
            unresolved_question=question,
            why_it_matters="stored investment logic의 다음 확인 조건과 연결됩니다.",
            evidence_needed=question,
            evidence_refs=_refs(catalog, "core", "unknown", "next_check"),
        ),
    )


def _positioning_item(
    current_ai_text: str,
    catalog: tuple[EvidenceAtom, ...],
    identifier: str,
) -> AnalysisItem | None:
    body = _first_body(current_ai_text, "supply")
    if not body:
        return None
    relation = _sentences(body)[-1]
    text = relation
    if "중기 사업 근거" in relation:
        text = "기간별 주체 방향이 엇갈린 수급은 전술적 배경일 뿐, 중기 사업 판단의 근거로는 부족합니다."
    elif "사업 변화의 증거" in relation or "실적 변화" in relation:
        text = "현재 가격·거래 흐름은 사업 변화의 확인보다 전술적 배경으로만 해석해야 합니다."
    elif "대리 지표" in relation:
        text = "기관 유입은 장기 수주 실행을 확인하는 대리 지표가 될 수 없습니다."
    elif "증거로 쓰지" in relation:
        text = "외국인·기관의 엇갈린 흐름은 수주 전환을 확인하는 근거가 아닙니다."
    elif "구조적 매수세" in relation:
        text = "단기와 누적 주체가 다른 수급은 구조적 매수세로 단정하기 어렵습니다."
    elif "사업 기대의 확인" in relation:
        text = "가격·거래 확인은 사업 기대가 실적으로 전환됐다는 증거가 아닙니다."
    return _item(
        item_id=f"{identifier}-positioning",
        text=text,
        support_type=SupportType.POSITIONING_SYNTHESIS,
        evidence_refs=_refs(catalog, "supply"),
        materiality_reason="separates tactical flow from fundamental evidence",
        rule_id=InferenceRule.POSITIONING_FUNDAMENTAL_BOUNDARY,
        boundary="수급만으로 투자 논리나 사업 상태를 바꾸지 않습니다.",
        confidence=ConfidenceLabel.HIGH,
    )


def _expectation_item(
    *,
    identifier: str,
    current_ai_text: str,
    catalog: tuple[EvidenceAtom, ...],
    category: str,
    industry_context_owner: str,
) -> AnalysisItem | None:
    expectation = _expectation_ref(catalog)
    if not expectation:
        return None
    expectation_text = _source_text(catalog, expectation)
    if "균형" in expectation_text:
        return None
    if "매우 높" in expectation_text:
        level = "매우 높은 기대"
    elif "높" in expectation_text:
        level = "높은 기대"
    elif "투기" in expectation_text:
        level = "투기적 기대"
    else:
        return None
    inventory_focus = {
        "memory": "HBM 실행과 수익성의 지속 확인",
        "defense": "수주잔고의 인도와 방산 수익성의 지속 확인",
        "steel_materials": "철강 스프레드와 운전자본 회수의 확인",
    }.get(industry_context_owner, "핵심 사업 실행과 수익성의 지속 확인")
    phrases = {
        "inventory_low": f"{level}를 정당화하려면 재고 관계 하나보다 {inventory_focus}이 더 중요합니다.",
        "inventory_high": f"{level} 아래에서는 재고 부담 가능성을 해소할 실적 근거가 추가로 확인돼야 합니다.",
        "order_cash": f"{level}를 추가로 정당화하려면 수주 규모보다 현금 회수까지 이어지는 근거가 필요합니다.",
        "contract_cash": f"{level}를 추가로 정당화하려면 수주잔고보다 인도와 운전자본 회수의 확인이 필요합니다.",
        "fleet_cash": f"{level}를 추가로 정당화하려면 물류 흐름과 자산 투자 회수가 함께 확인돼야 합니다.",
        "hpc": f"{level}를 정당화하려면 가격 반등보다 가동·매출·현금전환의 연결이 먼저 확인돼야 합니다.",
        "platform": f"{level}를 정당화하려면 단일 매출보다 수익원 전환과 현금흐름의 질이 확인돼야 합니다.",
        "cloud_fcf": f"{level}를 정당화하려면 AI 투자 확대가 Cloud 성장·마진과 현금 회수로 이어지는 확인이 필요합니다.",
        "memory_fcf": f"{level}를 정당화하려면 확대된 현금흐름이 메모리 사이클 전반에서 지속되는지 확인해야 합니다.",
    }
    text = phrases.get(category)
    if text is None:
        return None
    refs = (*expectation, *_refs(catalog, "core", "business", "next_check"))
    return _item(
        item_id=f"{identifier}-expectation",
        text=text,
        support_type=SupportType.EXPECTATION_VALUATION_LINK,
        evidence_refs=tuple(dict.fromkeys(refs)),
        materiality_reason="expectation level changes the evidence threshold",
        rule_id=InferenceRule.EXPECTATION_VERIFICATION_THRESHOLD,
        boundary="기대 수준은 확인 문턱을 바꾸지만 투자 상태를 자동 변경하지 않습니다.",
    )


def _thesis_implication_text(
    category: str,
    business: str,
    *,
    industry_context_owner: str,
) -> str:
    if category == "inventory_low":
        focus = {
            "memory": "HBM 실행과 수익성의 지속 확인",
            "defense": "지상방산 수주잔고의 인도와 수익성 지속 확인",
            "steel_materials": "철강 스프레드와 소재 현금 회수의 확인",
        }.get(industry_context_owner, "핵심 사업 실행과 수익성의 지속 확인")
        return f"이 재고 관계는 현재 투자 논리를 약화시키지는 않지만, {focus}을 대체하지 못합니다."
    if category == "inventory_high" and industry_context_owner == "memory":
        return "따라서 메모리 재고 부담 가능성은 열려 있으며, HBM 채택과 마진의 다음 확인 전에는 구조적 개선을 확정하기 어렵습니다."
    if category == "inventory_high":
        if industry_context_owner == "steel_materials":
            return "따라서 재고 관계는 철강 스프레드와 소재 현금 회수의 확인 필요성을 높이지만, 사이클 악화를 확정하지는 않습니다."
        if industry_context_owner == "defense":
            return "따라서 재고 관계는 방산 인도와 운전자본 회수의 확인 필요성을 높이지만, 사업 악화를 확정하지는 않습니다."
        return "따라서 재고 관계는 운전자본 전환의 확인 필요성을 높이지만, 사업 악화를 확정하지는 않습니다."
    if category == "insurance":
        return "따라서 보험영업과 자본 여력이 확인되기 전에는 새로운 방향 전환도 성립하지 않습니다."
    if category == "order_cash":
        return "따라서 수주 전환은 논리 유지 근거지만, 현금 회수 확인 전에는 기대 상향의 근거가 충분하지 않습니다."
    if category == "contract_cash":
        return "따라서 수주잔고의 사업 규모와 실제 인도·회수는 분리해 확인해야 합니다."
    if category == "fleet_cash":
        return "따라서 물류 사업 흐름과 선대 투자 회수는 별도 증거로 확인해야 합니다."
    if category == "hpc":
        return "따라서 가격 경계와 HPC 사업 실행은 분리해 확인해야 하며, 현재 가격은 가동과 현금 전환을 증명하지 않습니다."
    if category == "platform":
        return "따라서 현재 매출은 성장의 한 단면이지만, 수익원 전환과 FCF가 함께 확인되기 전에는 기대 검증이 끝나지 않습니다."
    if category == "cloud_fcf":
        return "따라서 AI 투자 부담은 Cloud 성장·마진과 현금 전환이 함께 확인될 때 투자 논리의 검증 근거가 됩니다."
    if category == "memory_fcf":
        return "따라서 현재 FCF는 업사이클과 양립하지만, ASP·HBM 믹스와 투자 규율의 확인 없이 구조적 개선을 확정하기 어렵습니다."
    return "현재 근거는 핵심 사업 조건을 보여도 투자 논리의 다음 확인까지 닫지는 못합니다."


def build_free_analyst_analysis(
    current_ai_text: str,
    *,
    benchmark_id: str = "analysis",
    market: str | None = None,
    packet_owner: str | None = None,
    supporting_reference_text: str = "",
    market_context: object = None,
) -> FreeAnalystAnalysis:
    parsed = parse_rendered_message(current_ai_text)
    semantic_owner = _semantic_owner(
        current_ai_text,
        benchmark_id=benchmark_id,
        market=market,
        packet_owner=packet_owner,
    )
    supporting_reference = supporting_reference_text.strip()
    if supporting_reference:
        supporting_owner = _semantic_owner(
            supporting_reference,
            benchmark_id=benchmark_id,
            market=market,
            packet_owner=packet_owner,
        )
        if (
            semantic_owner.ticker_owner
            and supporting_owner.ticker_owner
            and semantic_owner.ticker_owner != supporting_owner.ticker_owner
        ):
            raise ValueError("supporting reference ticker owner mismatch")
    analysis_source = "\n\n".join(
        value for value in (current_ai_text.strip(), supporting_reference) if value
    )
    industry_source = "\n\n".join(
        value
        for value in (
            _first_body(current_ai_text, "core"),
            _first_body(current_ai_text, "business"),
            _first_body(supporting_reference, "core"),
            _first_body(supporting_reference, "business"),
            _first_body(supporting_reference, "next_check"),
        )
        if value
    )
    industry_context_owner = (
        "market_global"
        if parsed.is_market_digest
        else _industry_context_owner(industry_source or analysis_source)
    )
    catalog = build_evidence_catalog(current_ai_text, owner=semantic_owner)
    if supporting_reference:
        catalog = (
            *catalog,
            *build_evidence_catalog(
                supporting_reference,
                owner=semantic_owner,
                prefix="supporting",
            ),
        )
    kr_digest_plan: KrMarketDigestPlan | None = None
    kr_claim_refs: dict[str, str] = {}
    if parsed.is_market_digest and str(market or "").lower() == "kr":
        kr_digest_plan = build_kr_market_digest_plan(
            market_context,
            available_text=analysis_source,
        )
        if kr_digest_plan.richness.status:
            context_atoms: list[EvidenceAtom] = []
            for claim in kr_digest_plan.claims():
                ref = f"market-context:{claim.priority.value}:{claim.role}"
                kr_claim_refs[claim.role] = ref
                context_atoms.append(
                    EvidenceAtom(
                        ref=ref,
                        section_key="market_context",
                        text=claim.text,
                        owner=semantic_owner,
                        concept_families=(),
                    )
                )
            catalog = (*catalog, *context_atoms)
    identifier = _safe_id(benchmark_id)
    core_refs = _refs(catalog, "core")
    business_refs = _refs(catalog, "business")
    next_refs = _refs(catalog, "next_check")
    common_refs = tuple(
        dict.fromkeys((*_expectation_ref(catalog), *core_refs, *business_refs, *next_refs))
    )
    business = _first_body(current_ai_text, "business") or _first_body(
        supporting_reference,
        "business",
    )
    core = _first_body(current_ai_text, "core")
    supported_concepts = {
        concept for atom in catalog for concept in atom.concept_families
    }
    next_check_source = (
        current_ai_text
        if _first_body(current_ai_text, "next_check")
        else supporting_reference
    )
    next_checks = _next_check(next_check_source, catalog)
    top: list[AnalysisItem] = []
    thesis: list[AnalysisItem] = []
    alternatives: list[AlternativeInterpretation] = []
    expectation: list[AnalysisItem] = []
    category = "generic"
    specific_source = _best_specific_core_sentence(supporting_reference)
    inventory_is_auxiliary = bool(
        specific_source
        and "재고 증가율" in business
        and ("밑돌았습니다" in business or "앞섰습니다" in business)
    )
    entity_specific_lead = bool(
        str(market or "").lower() == "us" and specific_source
    )

    if parsed.is_market_digest:
        if kr_digest_plan is not None and kr_digest_plan.richness.status:
            assert kr_digest_plan.judgment is not None
            assert kr_digest_plan.interpretation is not None
            assert kr_digest_plan.next_check is not None
            top.append(
                _item(
                    item_id=f"{identifier}-kr-local-judgment",
                    text=kr_digest_plan.judgment.text,
                    support_type=SupportType.DIRECT_RELATION,
                    evidence_refs=(kr_claim_refs["judgment"],),
                    materiality_reason="keeps rich current KR structure in the primary judgment",
                    rule_id=None,
                    boundary="",
                    confidence=ConfidenceLabel.HIGH,
                )
            )
            thesis.append(
                _item(
                    item_id=f"{identifier}-kr-local-interpretation",
                    text=kr_digest_plan.interpretation.text,
                    support_type=SupportType.DIRECT_RELATION,
                    evidence_refs=(kr_claim_refs["interpretation"],),
                    materiality_reason="interprets current local flow or structure before global context",
                    rule_id=None,
                    boundary="",
                    confidence=ConfidenceLabel.HIGH,
                )
            )
            next_checks = (
                NextCheck(
                    check=kr_digest_plan.next_check.text,
                    linked_thesis_driver="current KR local market structure",
                    linked_unknown=kr_digest_plan.next_check.text,
                    evidence_refs=(kr_claim_refs["next_check"],),
                ),
            )
            selected = ("judgment", "evidence", "next_check")
        else:
            current_change = _first_content_sentence(
                supporting_reference,
                "important_changes",
            )
            if str(market or "").lower() == "kr" and not re.search(
                r"(?:KOSPI|KOSDAQ|코스피|코스닥)",
                supporting_reference,
                re.IGNORECASE,
            ):
                current_change = ""
            if current_change and not _REFERENCE_LAG.search(current_change):
                top.append(
                    _item(
                        item_id=f"{identifier}-current-market-change",
                        text=current_change,
                        support_type=SupportType.DIRECT_FACT,
                        evidence_refs=_supporting_refs(catalog, "important_changes"),
                        materiality_reason="leads with the strongest current market observation",
                        rule_id=None,
                        boundary="",
                        confidence=ConfidenceLabel.HIGH,
                    )
                )
                market_meaning = _first_content_sentence(
                    supporting_reference,
                    "market_meaning",
                )
                if str(market or "").lower() == "kr" and re.search(
                    r"(?:공표\s*대기|PUBLICATION_PENDING)",
                    current_change,
                    re.IGNORECASE,
                ):
                    market_meaning = ""
                if market_meaning:
                    thesis.append(
                        _item(
                            item_id=f"{identifier}-market-meaning",
                            text=market_meaning,
                            support_type=SupportType.DIRECT_FACT,
                            evidence_refs=_supporting_refs(catalog, "market_meaning"),
                            materiality_reason="preserves the deterministic market interpretation",
                            rule_id=None,
                            boundary="",
                        )
                    )
                selected = ("judgment", "evidence", "next_check")
            else:
                item = _item(
                    item_id=f"{identifier}-temporal-boundary",
                    text="오늘은 방향성 예측보다 새 관측이 없다는 시점 경계를 지키는 것이 판단의 핵심입니다.",
                    support_type=SupportType.BOUNDED_INFERENCE,
                    evidence_refs=_refs(catalog, "core", "risk"),
                    materiality_reason="prevents lagging context from becoming a current signal",
                    rule_id=InferenceRule.TEMPORAL_EVIDENCE_BOUNDARY,
                    boundary="직전 세션 자료는 배경일 뿐 오늘의 신규 관측이 아닙니다.",
                    confidence=ConfidenceLabel.HIGH,
                )
                top.append(item)
                selected = ("judgment", "risk")
    else:
        if inventory_is_auxiliary and not entity_specific_lead:
            top.append(
                _item(
                    item_id=f"{identifier}-source-thesis",
                    text=specific_source,
                    support_type=SupportType.DIRECT_FACT,
                    evidence_refs=_supporting_refs(catalog, "core"),
                    materiality_reason=(
                        "leads with the stored entity-specific thesis before inventory"
                    ),
                    rule_id=None,
                    boundary="",
                    direction=Direction.NEUTRAL,
                )
            )
        if "재고 증가율" in business and "밑돌았습니다" in business:
            category = "inventory_low"
            scale = "원가 규모" if "매출원가" in business else "매출 규모"
            primary = _item(
                item_id=f"{identifier}-inventory-balance",
                text=f"현재 자료에서는 재고가 {scale}보다 더 빠르게 쌓인다는 신호가 뚜렷하지 않습니다.",
                support_type=SupportType.BOUNDED_INFERENCE,
                evidence_refs=business_refs,
                materiality_reason="tests the stored inventory pressure driver",
                rule_id=InferenceRule.INVENTORY_NOT_OUTPACING_SCALE,
                boundary="이 관계만으로 수요 개선을 확정할 수 없습니다.",
                direction=Direction.SUPPORTS,
            )
            if inventory_is_auxiliary:
                thesis.append(primary)
            else:
                top.append(primary)
            positive = primary
            if industry_context_owner == "memory" and {
                SemanticConceptFamily.MEMORY_ASP,
                SemanticConceptFamily.MEMORY_PRODUCT_MIX,
            }.issubset(supported_concepts):
                negative_text = "다만 ASP와 제품 믹스의 영향이 남아 있어 이 관계만으로 최종 수요 개선을 단정하기 어렵습니다."
                unresolved_reason = "ASP, product mix, and demand are not separated by the relation."
            elif industry_context_owner == "memory":
                negative_text = "다만 재고와 매출의 상대 변화만으로 출하 시점과 수익성 개선을 단정하기 어렵습니다."
                unresolved_reason = "shipment timing, profitability, and demand are not separated."
            elif industry_context_owner == "defense":
                negative_text = "다만 인도 시점과 계약별 매출 인식의 영향이 남아 있어 이 관계만으로 방산 수요의 현금 전환을 단정하기 어렵습니다."
                unresolved_reason = "delivery timing, revenue recognition, and cash conversion are not separated."
            elif industry_context_owner == "steel_materials":
                negative_text = "다만 원재료 가격과 철강 스프레드의 영향이 남아 있어 이 관계만으로 수요 개선을 단정하기 어렵습니다."
                unresolved_reason = "raw-material prices, spread, and demand are not separated."
            else:
                negative_text = "다만 가격과 물량의 영향이 분리되지 않아 이 관계만으로 최종 수요 개선을 단정하기 어렵습니다."
                unresolved_reason = "price, volume, and demand are not separated by the relation."
            negative = _item(
                item_id=f"{identifier}-inventory-boundary",
                text=negative_text,
                support_type=SupportType.ALTERNATIVE_INTERPRETATION,
                evidence_refs=common_refs,
                materiality_reason="preserves the current entity's operating alternative",
                rule_id=InferenceRule.INVENTORY_ALTERNATIVES,
                boundary="수요 방향은 추가 영업 근거가 필요합니다.",
                direction=Direction.MIXED,
            )
            alternatives.append(
                AlternativeInterpretation(
                    item_id=f"{identifier}-inventory-alternatives",
                    positive_interpretation=positive,
                    negative_interpretation=negative,
                    evidence_refs=business_refs,
                    current_balance=CurrentBalance.MIXED,
                    unresolved_reason=unresolved_reason,
                )
            )
        elif "재고 증가율" in business and "앞섰습니다" in business:
            category = "inventory_high"
            scale = "원가" if "매출원가" in business else "매출"
            primary = _item(
                item_id=f"{identifier}-inventory-pressure",
                text=f"재고가 {scale}보다 빠르게 늘어난 관계는 재고 부담 점검의 우선순위가 높아졌음을 시사합니다.",
                support_type=SupportType.BOUNDED_INFERENCE,
                evidence_refs=business_refs,
                materiality_reason="flags inventory pressure without inventing its cause",
                rule_id=InferenceRule.INVENTORY_OUTPACING_SCALE,
                boundary="가격, 물량, 제품 믹스가 분리되지 않아 원인은 확정할 수 없습니다.",
                direction=Direction.CHALLENGES,
            )
            if inventory_is_auxiliary:
                thesis.append(primary)
            else:
                top.append(primary)
            if industry_context_owner == "memory":
                positive_text = "ASP나 제품 믹스 변화가 재고 관계에 영향을 준 결과일 가능성은 남아 있습니다."
            elif industry_context_owner == "steel_materials":
                positive_text = "철강 물량과 원재료 가격 변화가 재고 관계에 영향을 준 결과일 가능성은 남아 있습니다."
            elif industry_context_owner == "defense":
                positive_text = "인도 일정과 계약별 매출 인식이 재고 관계에 영향을 준 결과일 가능성은 남아 있습니다."
            else:
                positive_text = "가격이나 물량 변화가 재고 관계에 영향을 준 결과일 가능성은 남아 있습니다."
            positive = _item(
                item_id=f"{identifier}-inventory-scale-alternative",
                text=positive_text,
                support_type=SupportType.ALTERNATIVE_INTERPRETATION,
                evidence_refs=common_refs,
                materiality_reason="keeps a non-deterioration explanation open",
                rule_id=InferenceRule.INVENTORY_ALTERNATIVES,
                boundary="상대 증가율만으로 원인을 식별할 수 없습니다.",
                direction=Direction.NEUTRAL,
            )
            negative = _item(
                item_id=f"{identifier}-inventory-risk-alternative",
                text=f"반대로 재고가 {scale}보다 빠르게 늘어난 점은 운전자본 부담 가능성을 열어 둡니다.",
                support_type=SupportType.ALTERNATIVE_INTERPRETATION,
                evidence_refs=business_refs,
                materiality_reason="surfaces the downside interpretation",
                rule_id=InferenceRule.INVENTORY_ALTERNATIVES,
                boundary="실제 원인은 다음 사업 지표로 확인해야 합니다.",
                direction=Direction.CHALLENGES,
            )
            alternatives.append(
                AlternativeInterpretation(
                    item_id=f"{identifier}-inventory-alternatives",
                    positive_interpretation=positive,
                    negative_interpretation=negative,
                    evidence_refs=business_refs,
                    current_balance=CurrentBalance.UNRESOLVED,
                    unresolved_reason="price, volume, and mix contributions are not separated.",
                )
            )
        elif "일반 제조업 현금흐름 틀" in core:
            category = "insurance"
            top.append(
                _item(
                    item_id=f"{identifier}-insurance-applicability",
                    text="현재 판단을 가르는 것은 일반기업 FCF가 아니라 보험영업의 지속성과 자본 여력입니다.",
                    support_type=SupportType.THESIS_LINKAGE,
                    evidence_refs=common_refs,
                    materiality_reason="applies the insurance-specific investment framework",
                    rule_id=InferenceRule.INSURANCE_APPLICABILITY,
                    boundary="일반 제조업 현금흐름 부재를 Unknown으로 만들지 않습니다.",
                    confidence=ConfidenceLabel.HIGH,
                )
            )
        elif "매출채권과 현금 회수" in business:
            category = "order_cash"
            top.append(
                _item(
                    item_id=f"{identifier}-order-cash-gap",
                    text="수주가 매출로 전환된 근거만으로 현금 회수까지 확인된 것은 아니어서, 다음 판단에는 정식 회수 근거가 필요합니다.",
                    support_type=SupportType.THESIS_LINKAGE,
                    evidence_refs=common_refs,
                    materiality_reason="separates order conversion from cash collection",
                    rule_id=InferenceRule.ORDER_TO_CASH_GAP,
                    boundary="매출채권 수치나 회수 속도는 새로 추론하지 않습니다.",
                )
            )
        elif "계약자산과 현금 전환" in business:
            category = "contract_cash"
            top.append(
                _item(
                    item_id=f"{identifier}-contract-cash-gap",
                    text="사업 규모만으로 수주가 현금으로 전환됐다고 볼 수 없어, 인도 일정과 운전자본 회수 조건의 확인이 필요합니다.",
                    support_type=SupportType.THESIS_LINKAGE,
                    evidence_refs=common_refs,
                    materiality_reason="separates backlog scale from cash recovery",
                    rule_id=InferenceRule.CONTRACT_ASSET_RECOVERY_GAP,
                    boundary="계약자산 규모나 회수율은 추론하지 않습니다.",
                )
            )
        elif "선대 투자와 현금 전환" in business:
            category = "fleet_cash"
            top.append(
                _item(
                    item_id=f"{identifier}-fleet-cash-gap",
                    text="현재 사업 흐름과 선대 투자의 현금 전환은 별도 문제이므로, 운임·물량과 자산 효율이 함께 확인돼야 합니다.",
                    support_type=SupportType.THESIS_LINKAGE,
                    evidence_refs=common_refs,
                    materiality_reason="links fleet reinvestment to the transport thesis",
                    rule_id=InferenceRule.FLEET_INVESTMENT_RECOVERY_GAP,
                    boundary="투자 회수율은 현재 근거로 계산하지 않습니다.",
                )
            )
        elif industry_context_owner == "hpc_data_center" and re.search(
            r"(?:HPC|colocation|코로케이션|billing|leased customer power)",
            analysis_source,
            re.IGNORECASE,
        ):
            category = "hpc"
            top.append(
                _item(
                    item_id=f"{identifier}-hpc-threshold",
                    text="현재 근거로는 HPC 실행과 현금 전환의 연결이 닫히지 않아, 가격 움직임만으로 전환 기대를 확인했다고 볼 수 없습니다.",
                    support_type=SupportType.THESIS_LINKAGE,
                    evidence_refs=common_refs,
                    materiality_reason="connects the build-out thesis to missing operating proof",
                    rule_id=InferenceRule.HPC_EXECUTION_THRESHOLD,
                    boundary="가동, 매출, CAPEX, FCF의 새 수치나 관계는 추론하지 않습니다.",
                    direction=Direction.MIXED,
                )
            )
        elif "USDC" in analysis_source and re.search(
            r"(?:reserve|준비금|비이자)", analysis_source, re.IGNORECASE
        ):
            category = "platform"
            top.append(
                _item(
                    item_id=f"{identifier}-platform-quality-gap",
                    text="단일 매출 근거만으로는 준비금 수익을 비이자 수익이 대체하는지와 FCF의 질을 확인할 수 없습니다.",
                    support_type=SupportType.THESIS_LINKAGE,
                    evidence_refs=common_refs,
                    materiality_reason="connects reported revenue to the stated platform-quality test",
                    rule_id=InferenceRule.PLATFORM_REVENUE_QUALITY_GAP,
                    boundary="수익원 구성과 FCF는 다음 공식 자료까지 Unknown입니다.",
                    direction=Direction.MIXED,
                )
            )
        elif "PPE 투자 후 잉여현금흐름" in business and "AI·Cloud" in business:
            category = "cloud_fcf"
            top.append(
                _item(
                    item_id=f"{identifier}-cloud-fcf",
                    text="전년보다 줄어든 PPE 투자 후 FCF는 AI 투자 회수 확인의 중요성을 높이지만, 그 자체로 투자 실패를 뜻하지는 않습니다.",
                    support_type=SupportType.BOUNDED_INFERENCE,
                    evidence_refs=common_refs,
                    materiality_reason="separates lower FCF from an unsupported failure verdict",
                    rule_id=InferenceRule.FCF_CAPEX_RECOVERY,
                    boundary="Cloud 성장과 마진이 투자 회수로 이어지는지는 아직 확인이 필요합니다.",
                    direction=Direction.MIXED,
                )
            )
        elif "PPE 투자 후 잉여현금흐름" in business and "메모리" in business:
            category = "memory_fcf"
            top.append(
                _item(
                    item_id=f"{identifier}-memory-fcf",
                    text="늘어난 PPE 투자 후 FCF는 현금 전환과 양립하지만, 메모리 사이클 전반의 지속성을 확정하지는 않습니다.",
                    support_type=SupportType.BOUNDED_INFERENCE,
                    evidence_refs=common_refs,
                    materiality_reason="uses FCF without promoting a peak-cycle observation",
                    rule_id=InferenceRule.MEMORY_CYCLE_FCF,
                    boundary="ASP, HBM 믹스, 재고 사이클과 투자 시점의 추가 확인이 필요합니다.",
                    direction=Direction.SUPPORTS,
                )
            )
        else:
            if specific_source:
                category = "source_thesis"
                top.append(
                    _item(
                        item_id=f"{identifier}-source-thesis",
                        text=specific_source,
                        support_type=SupportType.DIRECT_FACT,
                        evidence_refs=_supporting_refs(catalog, "core"),
                        materiality_reason="uses the stored entity-specific thesis before auxiliary evidence",
                        rule_id=None,
                        boundary="",
                        direction=Direction.NEUTRAL,
                    )
                )
            else:
                top.append(
                    _item(
                        item_id=f"{identifier}-evidence-gap",
                        text="현재 근거는 핵심 사업 조건의 존재를 보여도 투자 논리의 다음 확인까지 닫지는 못합니다.",
                        support_type=SupportType.BOUNDED_INFERENCE,
                        evidence_refs=common_refs,
                        materiality_reason="keeps the analysis tied to the next unresolved driver",
                        rule_id=InferenceRule.UNKNOWN_TO_NEXT_EVIDENCE,
                        boundary="새 사실이나 원인은 추가하지 않습니다.",
                        direction=Direction.NEUTRAL,
                    )
                )

        if entity_specific_lead and category != "source_thesis":
            category_findings = tuple(top)
            top = [
                _item(
                    item_id=f"{identifier}-source-thesis",
                    text=specific_source,
                    support_type=SupportType.DIRECT_FACT,
                    evidence_refs=_supporting_refs(catalog, "core"),
                    materiality_reason="leads with the current entity-specific stored thesis",
                    rule_id=None,
                    boundary="",
                    direction=Direction.NEUTRAL,
                )
            ]
            thesis = [*category_findings, *thesis]

        primary = top[0]
        if category != "source_thesis":
            thesis.append(
                _item(
                    item_id=f"{identifier}-thesis-implication",
                    text=_thesis_implication_text(
                        category,
                        business,
                        industry_context_owner=industry_context_owner,
                    ),
                    support_type=SupportType.THESIS_LINKAGE,
                    evidence_refs=common_refs,
                    materiality_reason="states what the evidence changes and does not change",
                    rule_id=(
                        primary.rule_id
                        if primary.rule_id in _RULE_REQUIRED_SECTIONS
                        else InferenceRule.UNKNOWN_TO_NEXT_EVIDENCE
                    ),
                    boundary="저장된 투자 상태는 변경하지 않습니다.",
                    direction=Direction.NEUTRAL,
                )
            )
        expectation_item = _expectation_item(
            identifier=identifier,
            current_ai_text=current_ai_text,
            catalog=catalog,
            category=category,
            industry_context_owner=industry_context_owner,
        )
        if expectation_item is not None:
            expectation.append(expectation_item)
        selected = ["judgment", "evidence", "next_check"]
        if alternatives:
            selected.append("balance")
        if expectation:
            selected.append("expectation")
        selected = tuple(selected)

    positioning = _positioning_item(current_ai_text, catalog, identifier)
    positioning_rows = (positioning,) if positioning is not None else ()
    omitted = ["raw_numeric_tuple", "unselected_price_detail"]
    if not positioning_rows:
        omitted.append("positioning")
    if not expectation:
        omitted.append("expectation_valuation")
    if not alternatives:
        omitted.append("alternative_interpretation")

    top = [
        _bind_item_ownership(
            item,
            owner=semantic_owner,
            industry_context_owner=industry_context_owner,
            catalog=catalog,
        )
        for item in top
    ]
    thesis = [
        _bind_item_ownership(
            item,
            owner=semantic_owner,
            industry_context_owner=industry_context_owner,
            catalog=catalog,
        )
        for item in thesis
    ]
    alternatives = [
        replace(
            row,
            positive_interpretation=_bind_item_ownership(
                row.positive_interpretation,
                owner=semantic_owner,
                industry_context_owner=industry_context_owner,
                catalog=catalog,
            ),
            negative_interpretation=_bind_item_ownership(
                row.negative_interpretation,
                owner=semantic_owner,
                industry_context_owner=industry_context_owner,
                catalog=catalog,
            ),
        )
        for row in alternatives
    ]
    expectation = [
        _bind_item_ownership(
            item,
            owner=semantic_owner,
            industry_context_owner=industry_context_owner,
            catalog=catalog,
        )
        for item in expectation
    ]
    positioning_rows = tuple(
        _bind_item_ownership(
            item,
            owner=semantic_owner,
            industry_context_owner=industry_context_owner,
            catalog=catalog,
        )
        for item in positioning_rows
    )
    unknowns = tuple(
        replace(
            row,
            ownership=_claim_ownership(
                owner=semantic_owner,
                industry_context_owner=industry_context_owner,
                evidence_refs=row.evidence_refs,
                catalog=catalog,
                text=row.unresolved_question,
            ),
        )
        for row in _unknowns(current_ai_text, catalog)
    )
    next_checks = tuple(
        replace(
            row,
            ownership=_claim_ownership(
                owner=semantic_owner,
                industry_context_owner=industry_context_owner,
                evidence_refs=row.evidence_refs,
                catalog=catalog,
                text=row.check,
            ),
        )
        for row in next_checks
    )

    return FreeAnalystAnalysis(
        analysis_version=CONTRACT_VERSION,
        benchmark_id=benchmark_id,
        semantic_owner=semantic_owner,
        industry_context_owner=industry_context_owner,
        preamble=parsed.preamble,
        evidence_catalog=catalog,
        top_findings=tuple(top),
        thesis_implications=tuple(thesis),
        alternative_interpretations=tuple(alternatives),
        expectation_valuation_interaction=tuple(expectation),
        positioning_synthesis=positioning_rows,
        unknowns=unknowns,
        next_checks=next_checks,
        message_plan=MessagePlan(
            primary_conclusion=top[0].item_id,
            selected_blocks=selected,
            omitted_blocks=tuple(omitted),
            omission_reasons=(
                "exact numeric tuples remain in structured evidence and are not repeated",
                "low-materiality blocks are omitted from concise prose",
            ),
        ),
    )


def _rule_sections(
    item: AnalysisItem,
    catalog: dict[str, EvidenceAtom],
) -> frozenset[str]:
    return frozenset(catalog[ref].section_key for ref in item.evidence_refs if ref in catalog)


def _owner_mismatch_codes(
    ownership: ClaimOwnership,
    expected: SemanticOwnerIdentity,
) -> tuple[str, ...]:
    checks = (
        ("entity_owner_mismatch", ownership.entity_owner, expected.entity_owner),
        ("ticker_owner_mismatch", ownership.ticker_owner, expected.ticker_owner),
        ("market_owner_mismatch", ownership.market_owner, expected.market_owner),
        ("packet_owner_mismatch", ownership.packet_owner, expected.packet_owner),
    )
    return tuple(code for code, actual, wanted in checks if actual != wanted)


def _validate_claim_ownership(
    *,
    item_id: str,
    text: str,
    evidence_refs: tuple[str, ...],
    ownership: ClaimOwnership | None,
    analysis: FreeAnalystAnalysis,
    catalog: dict[str, EvidenceAtom],
) -> list[ValidationIssue]:
    if ownership is None:
        return [ValidationIssue("semantic_ownership_missing", item_id, text)]
    issues = [
        ValidationIssue(code, item_id, text)
        for code in _owner_mismatch_codes(ownership, analysis.semantic_owner)
    ]
    if ownership.industry_context_owner != analysis.industry_context_owner:
        issues.append(
            ValidationIssue(
                "industry_context_owner_mismatch",
                item_id,
                f"claim={ownership.industry_context_owner} current={analysis.industry_context_owner}",
            )
        )
    for ref in evidence_refs:
        atom = catalog.get(ref)
        if atom is not None and atom.owner != analysis.semantic_owner:
            issues.append(ValidationIssue("support_ref_owner_mismatch", item_id, ref))

    role_refs = (
        ("thesis_driver_owner_mismatch", ownership.thesis_driver_refs),
        ("fact_ref_owner_mismatch", ownership.fact_refs),
        ("relation_owner_mismatch", ownership.relation_refs),
        ("expectation_owner_mismatch", ownership.expectation_refs),
        ("valuation_owner_mismatch", ownership.valuation_refs),
        ("unknown_owner_mismatch", ownership.unknown_refs),
    )
    for code, refs in role_refs:
        for ref in refs:
            atom = catalog.get(ref)
            if ref not in evidence_refs or atom is None or atom.owner != analysis.semantic_owner:
                issues.append(ValidationIssue(code, item_id, ref))

    declared = set(ownership.concept_families)
    detected = set(
        _concept_families(text, industry_context_owner=analysis.industry_context_owner)
    )
    if detected != declared:
        issues.append(
            ValidationIssue(
                "semantic_concept_declaration_mismatch",
                item_id,
                f"declared={sorted(declared)} detected={sorted(detected)}",
            )
        )
    supported = {
        concept
        for ref in evidence_refs
        if ref in catalog
        for concept in catalog[ref].concept_families
    }
    unsupported = declared - supported
    if unsupported:
        issues.append(
            ValidationIssue(
                "industry_concept_ownership_mismatch",
                item_id,
                ", ".join(sorted(concept.value for concept in unsupported)),
            )
        )

    expectation_source = "\n".join(
        catalog[ref].text for ref in ownership.expectation_refs if ref in catalog
    )
    if "매우 높은 기대" in text and "매우 높" not in expectation_source:
        issues.append(ValidationIssue("expectation_level_mismatch", item_id, text))
    elif "높은 기대" in text and not re.search(r"(?:매우\s*)?높", expectation_source):
        issues.append(ValidationIssue("expectation_level_mismatch", item_id, text))
    elif "투기적 기대" in text and "투기" not in expectation_source:
        issues.append(ValidationIssue("expectation_level_mismatch", item_id, text))
    return issues


def validate_free_analyst_analysis(
    analysis: FreeAnalystAnalysis,
) -> SynthesisValidation:
    catalog = {atom.ref: atom for atom in analysis.evidence_catalog}
    issues: list[ValidationIssue] = []
    source_all = "\n".join(atom.text for atom in analysis.evidence_catalog)
    source_numbers = Counter(numeric_tokens(source_all))

    for item in analysis.analysis_items():
        missing = [ref for ref in item.evidence_refs if ref not in catalog]
        if not item.evidence_refs or missing:
            issues.append(
                ValidationIssue(
                    "evidence_ref_integrity",
                    item.item_id,
                    ", ".join(missing) or "no evidence refs",
                )
            )
            continue
        issues.extend(
            _validate_claim_ownership(
                item_id=item.item_id,
                text=item.text,
                evidence_refs=item.evidence_refs,
                ownership=item.ownership,
                analysis=analysis,
                catalog=catalog,
            )
        )
        source = _source_text(analysis.evidence_catalog, item.evidence_refs)
        if item.support_type in {SupportType.DIRECT_FACT, SupportType.DIRECT_RELATION}:
            if item.text not in source:
                issues.append(
                    ValidationIssue("direct_claim_not_source_span", item.item_id, item.text)
                )
        else:
            if item.rule_id is None:
                issues.append(
                    ValidationIssue("unclassified_synthesis_rule", item.item_id, item.text)
                )
            else:
                required = _RULE_REQUIRED_SECTIONS[item.rule_id]
                available = _rule_sections(item, catalog)
                if not required.issubset(available):
                    issues.append(
                        ValidationIssue(
                            "support_semantic_mismatch",
                            item.item_id,
                            f"required={sorted(required)} available={sorted(available)}",
                        )
                    )
            if item.support_type in {
                SupportType.BOUNDED_INFERENCE,
                SupportType.ALTERNATIVE_INTERPRETATION,
                SupportType.THESIS_LINKAGE,
                SupportType.EXPECTATION_VALUATION_LINK,
            } and not (item.boundary and any(mark in item.text for mark in _BOUNDED_MARKERS)):
                issues.append(
                    ValidationIssue("claim_strength_exceeds_support", item.item_id, item.text)
                )

        item_numbers = Counter(numeric_tokens(item.text))
        if item_numbers and item.support_type not in {
            SupportType.DIRECT_FACT,
            SupportType.DIRECT_RELATION,
        } and item.text not in source:
            issues.append(
                ValidationIssue("hidden_arithmetic_or_numeric_synthesis", item.item_id, item.text)
            )
        elif any(count > source_numbers.get(token, 0) for token, count in item_numbers.items()):
            issues.append(ValidationIssue("unsupported_numeric_claim", item.item_id, item.text))

        if _FORBIDDEN_OUTPUT.search(item.text):
            issues.append(ValidationIssue("forbidden_field_leak", item.item_id, item.text))
        if _CAUSAL_OVERREACH.search(item.text) or (
            item.support_type != SupportType.DIRECT_FACT and _STRONG_CAUSE.search(item.text)
        ):
            issues.append(ValidationIssue("unsupported_causal_conclusion", item.item_id, item.text))
        external_tokens = {
            token
            for token in _EXTERNAL_TOKEN.findall(item.text)
            if token not in _ALLOWED_ANALYTIC_TOKENS and token not in source
        }
        if external_tokens:
            issues.append(
                ValidationIssue(
                    "external_knowledge_claim",
                    item.item_id,
                    ", ".join(sorted(external_tokens)),
                )
            )
        if item.support_type == SupportType.POSITIONING_SYNTHESIS and re.search(
            r"(?:투자 논리|사업).*(?:약화|훼손)", item.text
        ):
            issues.append(ValidationIssue("supply_fundamental_promotion", item.item_id, item.text))
        if "오늘 상승" in item.text and (
            "오늘의 신규 관측은 아닙니다" in source_all
            or "현재 신호로 승격하지 않습니다" in source_all
        ):
            issues.append(ValidationIssue("temporal_leakage", item.item_id, item.text))

    for row in (*analysis.unknowns, *analysis.next_checks):
        row_id = "unknown" if isinstance(row, UnknownItem) else "next-check"
        row_text = row.unresolved_question if isinstance(row, UnknownItem) else row.check
        issues.extend(
            _validate_claim_ownership(
                item_id=row_id,
                text=row_text,
                evidence_refs=row.evidence_refs,
                ownership=row.ownership,
                analysis=analysis,
                catalog=catalog,
            )
        )
        for ref in row.evidence_refs:
            if ref not in catalog:
                issues.append(
                    ValidationIssue("evidence_ref_integrity", "unknown_or_next_check", ref)
                )

    return SynthesisValidation(status="PASS" if not issues else "FAIL", issues=tuple(issues))


def _render_blocks(
    analysis: FreeAnalystAnalysis,
    blocks: list[tuple[str, list[AnalysisItem | NextCheck]]],
    *,
    renderer: str,
) -> RenderedFreeAnalyst:
    rendered = [analysis.preamble.strip()]
    support_rows: list[SentenceSupport] = []
    for heading, items in blocks:
        lines: list[str] = []
        for item in items:
            if isinstance(item, NextCheck):
                line = f"• {item.check}"
                lines.append(line)
                support_rows.append(
                    SentenceSupport(
                        final_sentence=item.check,
                        analysis_item_id="next-check",
                        support_type=SupportType.UNCERTAINTY_BOUNDARY,
                        evidence_refs=item.evidence_refs,
                    )
                )
            else:
                lines.append(item.text)
                support_rows.append(
                    SentenceSupport(
                        final_sentence=item.text,
                        analysis_item_id=item.item_id,
                        support_type=item.support_type,
                        evidence_refs=item.evidence_refs,
                    )
                )
        if lines:
            rendered.append(f"{heading}\n" + "\n".join(lines))
    return RenderedFreeAnalyst(
        renderer=renderer,
        text="\n\n".join(value for value in rendered if value).strip(),
        sentence_supports=tuple(support_rows),
    )


def render_free_analyst_direct(analysis: FreeAnalystAnalysis) -> RenderedFreeAnalyst:
    blocks: list[tuple[str, list[AnalysisItem | NextCheck]]] = []
    if analysis.top_findings:
        blocks.append(("🎯 판단", [analysis.top_findings[0]]))
    if analysis.thesis_implications:
        blocks.append(("🔎 핵심 근거", [analysis.thesis_implications[0]]))
    if analysis.alternative_interpretations:
        row = analysis.alternative_interpretations[0]
        balance_items = [row.negative_interpretation]
        already_rendered = {
            analysis.message_plan.primary_conclusion,
            *(item.item_id for item in analysis.thesis_implications[:1]),
        }
        if row.positive_interpretation.item_id not in already_rendered:
            balance_items.insert(0, row.positive_interpretation)
        blocks.append(
            (
                "⚖️ 해석의 균형",
                balance_items,
            )
        )
    if analysis.expectation_valuation_interaction:
        blocks.append(("💰 기대·Valuation", [analysis.expectation_valuation_interaction[0]]))
    if analysis.positioning_synthesis and not analysis.alternative_interpretations:
        blocks.append(("📊 포지셔닝", [analysis.positioning_synthesis[0]]))
    if analysis.next_checks:
        blocks.append(("📌 다음 확인", [analysis.next_checks[0]]))
    return _render_blocks(analysis, blocks, renderer="DIRECT")


def render_free_analyst_vnext_hybrid(
    analysis: FreeAnalystAnalysis,
) -> RenderedFreeAnalyst:
    blocks: list[tuple[str, list[AnalysisItem | NextCheck]]] = []
    if analysis.top_findings:
        blocks.append(("🎯 판단", [analysis.top_findings[0]]))
    if analysis.expectation_valuation_interaction:
        blocks.append(("🔎 왜 중요한가", [analysis.expectation_valuation_interaction[0]]))
    elif analysis.alternative_interpretations:
        blocks.append(("⚖️ 경계", [analysis.alternative_interpretations[0].negative_interpretation]))
    elif analysis.thesis_implications:
        blocks.append(("🔎 왜 중요한가", [analysis.thesis_implications[0]]))
    if analysis.next_checks:
        blocks.append(("📌 다음 확인", [analysis.next_checks[0]]))
    return _render_blocks(analysis, blocks, renderer="VNEXT_HYBRID")


def rendered_safety_report(
    current_ai_text: str,
    analysis: FreeAnalystAnalysis,
    rendered: RenderedFreeAnalyst,
) -> dict[str, object]:
    validation = validate_free_analyst_analysis(analysis)
    current_numbers = Counter(numeric_tokens(current_ai_text))
    rendered_numbers = Counter(numeric_tokens(rendered.text))
    unsupported_numbers = sorted(
        token for token, count in rendered_numbers.items() if count > current_numbers.get(token, 0)
    )
    supported_ids = {item.item_id for item in analysis.analysis_items()}
    unsupported_sentences = [
        row.final_sentence
        for row in rendered.sentence_supports
        if row.analysis_item_id != "next-check" and row.analysis_item_id not in supported_ids
    ]
    issue_counts = Counter(issue.code for issue in validation.issues)
    trade_ar_leaks = [
        match.group(0)
        for match in _FORBIDDEN_OUTPUT.finditer(rendered.text)
        if "AR" in match.group(0) or "매출채권" in match.group(0)
    ]
    status = (
        "PASS"
        if validation.status == "PASS"
        and not unsupported_numbers
        and not unsupported_sentences
        and not trade_ar_leaks
        else "FAIL"
    )
    return {
        "contract": CONTRACT_VERSION,
        "status": status,
        "fact_mismatch": len(unsupported_sentences),
        "unsupported_numeric_claims": unsupported_numbers,
        "unsupported_causality": issue_counts["unsupported_causal_conclusion"],
        "temporal_violations": issue_counts["temporal_leakage"],
        "trade_ar_leak": len(trade_ar_leaks),
        "hidden_arithmetic": issue_counts["hidden_arithmetic_or_numeric_synthesis"],
        "external_knowledge": issue_counts["external_knowledge_claim"],
        "entity_owner_mismatch": issue_counts["entity_owner_mismatch"],
        "ticker_owner_mismatch": issue_counts["ticker_owner_mismatch"],
        "market_owner_mismatch": issue_counts["market_owner_mismatch"],
        "packet_owner_mismatch": issue_counts["packet_owner_mismatch"],
        "support_ref_owner_mismatch": issue_counts["support_ref_owner_mismatch"],
        "industry_context_mismatch": (
            issue_counts["industry_context_owner_mismatch"]
            + issue_counts["industry_concept_ownership_mismatch"]
            + issue_counts["semantic_concept_declaration_mismatch"]
        ),
        "thesis_driver_owner_mismatch": issue_counts["thesis_driver_owner_mismatch"],
        "fact_ref_owner_mismatch": issue_counts["fact_ref_owner_mismatch"],
        "relation_owner_mismatch": issue_counts["relation_owner_mismatch"],
        "expectation_owner_mismatch": (
            issue_counts["expectation_owner_mismatch"]
            + issue_counts["expectation_level_mismatch"]
        ),
        "unsupported_synthesis": len(validation.issues),
        "validation": validation.to_dict(),
    }


def novel_synthesis_report(
    current_ai_text: str,
    vnext_text: str,
    rendered: RenderedFreeAnalyst,
    safety: dict[str, object],
) -> dict[str, int]:
    exact = 0
    novel = 0
    for row in rendered.sentence_supports:
        sentence = row.final_sentence
        if sentence in current_ai_text or sentence in vnext_text:
            exact += 1
        else:
            novel += 1
    return {
        "claim_bearing_sentences": len(rendered.sentence_supports),
        "exact_source_span_sentences": exact,
        "novel_supported_synthesis_sentences": (novel if safety["status"] == "PASS" else 0),
        "unsupported_synthesis_sentences": int(safety["unsupported_synthesis"]),
    }
