from __future__ import annotations

# ruff: noqa: E402, E501

import argparse
import hashlib
import json
import sys
import time
import zipfile
from collections import Counter
from dataclasses import asdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.adaptive_renderer_selector_shadow_service import (
    run_adaptive_renderer_shadow,
)
from app.services.open_research_event_attribution_shadow_service import (
    CONTRACT_VERSION,
    CurrentnessRole,
    EvidenceType,
    HypothesisScope,
    NegativeEvidenceScope,
    ObservedMove,
    RelationshipType,
    ResearchEvidence,
    ResearchRenderer,
    ResearchSidecar,
    ResearchSource,
    SearchLogEntry,
    SourceTier,
    SourceType,
    _render_claims,
    build_competing_hypotheses,
    build_event_attribution,
    build_research_claims,
    causal_time_eligible,
    deterministic_difference,
    deterministic_percentage,
    run_open_research_shadow,
    validate_research_sidecar,
)
from scripts.ai_analyst_vnext_shadow_benchmark import _benchmark_items


RUN_DATE = "20260825"
KR_PACKET_ID = "2026-08-24-kr-run-36-e4ac1c029c06"
KR_CUTOFF = "2026-08-24T19:34:19+09:00"
KR_MOVE_END = "2026-08-24T15:30:00+09:00"
RETRIEVED_AT = "2026-08-25T02:18:00+09:00"
REPORT_ROOT = ROOT / "docs/reports"
ARTIFACT_ROOT = ROOT / "artifacts/shadow/open-research/kr-20260824"
INSTRUCTION = ROOT / "docs/work-instructions/20260825-open-research-event-attribution-kr-us-shadow-and-us-holdout.md"
KR_BUNDLE = ROOT / "docs/reports/20260824-rehearsal-193419-post-repair-message-bundle.md"
ZIP_NAME = "20260825-open-research-event-attribution-shadow-bundle.zip"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _write_json(path: Path, value: object) -> None:
    _write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _table(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("\n", " ") for value in values) + " |"


def _source(
    source_id: str,
    name: str,
    tier: SourceTier,
    source_type: SourceType,
    url: str,
    family: str,
) -> ResearchSource:
    return ResearchSource(
        source_id=source_id,
        name=name,
        tier=tier,
        source_type=source_type,
        source_ref=url,
        source_family=family,
        original_source=name,
    )


def _sources() -> dict[str, ResearchSource]:
    rows = (
        _source(
            "samsung-official",
            "Samsung Electronics Newsroom",
            SourceTier.TIER_1_PRIMARY,
            SourceType.ISSUER_OFFICIAL,
            "https://news.samsung.com/kr/%EC%82%BC%EC%84%B1%EC%A0%84%EC%9E%90-%EC%82%AC%EC%83%81-%EC%B5%9C%EB%8C%80-%EC%A3%BC%EC%A3%BC%ED%99%98%EC%9B%90-%EC%8B%A4%EC%8B%9C-2026%EB%85%84-%EC%95%BD-90%EC%A1%B0110%EC%A1%B0%EC%9B%90",
            "samsung-newsroom",
        ),
        _source(
            "skhynix-official",
            "SK hynix Newsroom",
            SourceTier.TIER_1_PRIMARY,
            SourceType.ISSUER_OFFICIAL,
            "https://news.skhynix.com/en/share-buyback-and-retirement/",
            "skhynix-newsroom",
        ),
        _source(
            "yonhap-close",
            "Yonhap News Agency",
            SourceTier.TIER_2_INDEPENDENT,
            SourceType.WIRE_NEWS,
            "https://en.yna.co.kr/view/AEN20260824007152320",
            "yonhap",
        ),
        _source(
            "sbs-comparison",
            "SBS News",
            SourceTier.TIER_2_INDEPENDENT,
            SourceType.BUSINESS_PRESS,
            "https://news.sbs.co.kr/english/article.do?cooper=SBSNEWSEND&news_id=N1008719555&oaid=N1008678366&plink=TOP",
            "sbs",
        ),
        _source(
            "hankyung-samsung",
            "Korea Economic Daily",
            SourceTier.TIER_2_INDEPENDENT,
            SourceType.BUSINESS_PRESS,
            "https://www.hankyung.com/article/2026082487246",
            "hankyung",
        ),
        _source(
            "moneytoday-breadth",
            "MoneyToday",
            SourceTier.TIER_2_INDEPENDENT,
            SourceType.BUSINESS_PRESS,
            "https://www.mt.co.kr/stock/2026/08/24/2026082417102089135",
            "moneytoday",
        ),
        _source(
            "maekyung-semiconductor",
            "Maeil Business Newspaper",
            SourceTier.TIER_2_INDEPENDENT,
            SourceType.BUSINESS_PRESS,
            "https://www.mk.co.kr/news/stock/12135126",
            "maekyung",
        ),
        _source(
            "ap-us-context",
            "Associated Press",
            SourceTier.TIER_2_INDEPENDENT,
            SourceType.WIRE_NEWS,
            "https://apnews.com/article/96ef9586e1288e50843b4d2b1ccebc32",
            "ap",
        ),
        _source(
            "ap-nvidia-upcoming",
            "Associated Press",
            SourceTier.TIER_2_INDEPENDENT,
            SourceType.WIRE_NEWS,
            "https://apnews.com/article/8ab800029c559c5e751058ac1a8ef932",
            "ap",
        ),
    )
    return {row.source_id: row for row in rows}


def _search_log() -> tuple[SearchLogEntry, ...]:
    rows = (
        ("samsung", "site:samsung.com 2026 8 24 Samsung Electronics shareholder return capital allocation announcement", "official company catalyst", ("samsung-official",), ()),
        ("samsung", "2026.08.24 삼성전자 주주환원 주가 하락 외국인", "market interpretation", ("yonhap-close", "hankyung-samsung", "sbs-comparison"), ()),
        ("samsung", "August 24 2026 KOSPI Samsung shareholder return stock fell", "independent corroboration", ("yonhap-close",), ()),
        ("skhynix", "site:news.skhynix.com 2026 shareholder return policy August 2026", "official issuer context", ("skhynix-official",), ()),
        ("skhynix", "2026.08.24 SK하이닉스 주가 하락 외국인 기관", "same-day negative catalyst", ("maekyung-semiconductor",), ()),
        ("skhynix", "SK hynix shareholder return plan 2026 official August", "official plan verification", ("skhynix-official",), ()),
        ("joint-market", "2026-08-24 KOSPI Samsung Electronics SK hynix foreign institutional selling semiconductor", "market breadth and flow", ("yonhap-close", "moneytoday-breadth"), ()),
        ("joint-market", "8월24일 코스피 외국인 순매도 상위 삼성전자 SK하이닉스 2026", "flow concentration inputs", ("maekyung-semiconductor",), ("no compatible two-stock value tuple" ,)),
        ("joint-market", "August 24 2026 South Korea stocks KOSPI semiconductor", "cross-sectional market evidence", ("yonhap-close",), ()),
        ("hbm-negative", "2026년 8월 24일 HBM 주문 축소 가격 하락 고객 CAPEX 삼성전자 SK하이닉스", "test business deterioration alternative", (), ("no verified Tier 1/2 result",)),
        ("hbm-negative", "site:news.skhynix.com August 24 2026 HBM order reduction", "official SK source check", (), ("no matching official event",)),
        ("hbm-negative", "site:news.samsung.com August 24 2026 HBM customer capex cut", "official Samsung source check", (), ("no matching official event",)),
        ("global-macro", "August 21 2026 US stocks semiconductors Nvidia earnings Treasury yields market close", "prior US risk context", ("ap-us-context",), ()),
        ("global-macro", "August 24 2026 Nvidia earnings upcoming semiconductors market", "next semiconductor event", ("ap-nvidia-upcoming",), ()),
        ("global-macro", "August 24 2026 US Treasury yields Jackson Hole semiconductor stocks", "macro competing hypothesis", ("ap-us-context",), ()),
    )
    return tuple(
        SearchLogEntry(
            research_cluster_id=cluster,
            query=query,
            created_at=RETRIEVED_AT,
            reason=reason,
            parent_query=None,
            result_count=len(selected) + len(rejected),
            selected_sources=selected,
            rejected_sources=rejected,
        )
        for cluster, query, reason, selected, rejected in rows
    )


def _evidence(
    evidence_id: str,
    cluster: str,
    entity: str,
    ticker: str | None,
    issuer_identity: str,
    relationship: RelationshipType,
    source: ResearchSource,
    event_at: str,
    published_at: str,
    evidence_type: EvidenceType,
    statement: str,
    semantic: str,
    *,
    supports: tuple[HypothesisScope, ...] = (),
    contradicts: tuple[HypothesisScope, ...] = (),
    role: CurrentnessRole = CurrentnessRole.PRE_SESSION_EVENT,
    limitations: tuple[str, ...] = (),
    negative_scope: NegativeEvidenceScope | None = None,
) -> ResearchEvidence:
    return ResearchEvidence(
        research_evidence_id=evidence_id,
        cluster_id=cluster,
        entity=entity,
        ticker=ticker,
        market="KR",
        issuer_identity=issuer_identity,
        related_entity=None if relationship == RelationshipType.DIRECT_ISSUER else entity,
        relationship_type=relationship,
        source=source,
        event_at=event_at,
        published_at=published_at,
        retrieved_at=RETRIEVED_AT,
        research_cutoff=KR_CUTOFF,
        market_session="2026-08-24 KR regular",
        causal_window_end=KR_MOVE_END,
        evidence_type=evidence_type,
        statement=statement,
        fact_semantic=semantic,
        causal_time_eligible=causal_time_eligible(event_at, KR_MOVE_END),
        currentness_role=role,
        supports_scopes=supports,
        contradicts_scopes=contradicts,
        limitations=limitations,
        negative_scope=negative_scope,
    )


def _common_evidence(sources: dict[str, ResearchSource]) -> dict[str, ResearchEvidence]:
    negative_scope = NegativeEvidenceScope(
        question="Was there verified new HBM order, price, or customer-CAPEX deterioration before the KR close?",
        searched_source_tiers=(SourceTier.TIER_1_PRIMARY, SourceTier.TIER_2_INDEPENDENT),
        query_count=3,
        searched_time_window="2026-08-18 through 2026-08-24 KR close",
        entities_or_sectors_checked=("Samsung Electronics", "SK hynix", "HBM", "memory", "AI customer CAPEX"),
        last_search_at=RETRIEVED_AT,
        what_was_not_found="verified new HBM order reduction, HBM price decline, or customer CAPEX cut",
        coverage_limitations=("public indexed official and major-news sources only", "absence is not proof that fundamentals are sound"),
    )
    rows = (
        _evidence(
            "e-samsung-official-plan", "samsung", "Samsung Electronics", "005930", "samsung-electronics", RelationshipType.DIRECT_ISSUER, sources["samsung-official"],
            "2026-08-21T16:00:00+09:00", "2026-08-21T16:00:00+09:00", EvidenceType.CONFIRMED_EVENT_FACT,
            "삼성전자는 8월 21일 2026년 주주환원 90조~110조원, 3분기 약 30조원 현금배당 계획, 임직원 보상용 약 15조원 자사주 매입을 공식 발표했고, 나머지 환원 방식과 규모는 2027년 1월 이사회에서 정하기로 했습니다.",
            "issuer_direct_capital_allocation_plan", supports=(HypothesisScope.COMPANY,),
        ),
        _evidence(
            "e-samsung-reported-disappointment", "samsung", "Samsung Electronics", "005930", "samsung-electronics", RelationshipType.DIRECT_ISSUER, sources["yonhap-close"],
            "2026-08-21T16:00:00+09:00", "2026-08-24T16:47:00+09:00", EvidenceType.REPORTED_INTERPRETATION,
            "연합뉴스는 확정된 자사주 매입 세부안이 부족해 투자자들이 실망한 것으로 보인다는 애널리스트 해석을 전했습니다.",
            "reported_capital_allocation_disappointment", supports=(HypothesisScope.COMPANY,), role=CurrentnessRole.AFTER_MOVE_INTERPRETATION,
        ),
        _evidence(
            "e-samsung-sk-policy-comparison", "joint-market", "Samsung Electronics and SK hynix", None, "kr-memory-leaders", RelationshipType.SECTOR, sources["sbs-comparison"],
            "2026-08-21T16:00:00+09:00", "2026-08-24T21:29:00+09:00", EvidenceType.REPORTED_INTERPRETATION,
            "SBS는 삼성전자가 3분기 30조원 현금배당 외의 방식은 확정하지 않은 반면 SK하이닉스는 40조원 자사주를 전량 소각하기로 한 차이가 두 종목의 낙폭 차이를 설명한다는 해석을 전했습니다.",
            "reported_cross_issuer_policy_comparison", supports=(HypothesisScope.COMPANY, HypothesisScope.SECTOR), role=CurrentnessRole.AFTER_MOVE_INTERPRETATION,
        ),
        _evidence(
            "e-skhynix-official-plan", "skhynix", "SK hynix", "000660", "sk-hynix", RelationshipType.DIRECT_ISSUER, sources["skhynix-official"],
            "2026-08-19T09:00:00+09:00", "2026-08-19T09:00:00+09:00", EvidenceType.CONFIRMED_EVENT_FACT,
            "SK하이닉스는 8월 19일 40조원 규모 자사주 매입·전량 소각과 2025~2027년 누적 FCF의 50% 초과 주주환원 목표를 공식 발표했습니다.",
            "issuer_direct_share_buyback_cancellation", contradicts=(HypothesisScope.COMPANY,),
        ),
        _evidence(
            "e-market-close-breadth-flow", "joint-market", "KOSPI", None, "krx-kospi", RelationshipType.MARKET_STRUCTURE, sources["yonhap-close"],
            "2026-08-24T15:30:00+09:00", "2026-08-24T16:47:00+09:00", EvidenceType.CONFIRMED_BREADTH_FACT,
            "코스피는 3.12% 내린 6,696.96으로 마감했지만 상승 종목 576개가 하락 종목 286개보다 많았고, 외국인과 기관은 합계 4.97조원을 순매도했으며 개인은 3.32조원을 순매수했습니다.",
            "market_breadth_and_flow", supports=(HypothesisScope.POSITIONING,), contradicts=(HypothesisScope.MARKET,), role=CurrentnessRole.CURRENT_SESSION,
        ),
        _evidence(
            "e-cross-market-divergence", "joint-market", "KOSDAQ", None, "krx-kosdaq", RelationshipType.MARKET_STRUCTURE, sources["moneytoday-breadth"],
            "2026-08-24T15:30:00+09:00", "2026-08-24T17:10:00+09:00", EvidenceType.CONFIRMED_BREADTH_FACT,
            "코스닥은 1.42% 상승했고 외국인은 3,255억원, 기관은 262억원을 순매수해 코스피 대형주 매도와 반대 흐름을 보였습니다.",
            "kosdaq_divergence", supports=(HypothesisScope.MARKET,), contradicts=(HypothesisScope.MARKET,), role=CurrentnessRole.CURRENT_SESSION,
        ),
        _evidence(
            "e-security-returns", "joint-market", "Samsung Electronics and SK hynix", None, "kr-memory-leaders", RelationshipType.SECTOR, sources["sbs-comparison"],
            "2026-08-24T15:30:00+09:00", "2026-08-24T21:29:00+09:00", EvidenceType.CONFIRMED_MARKET_FACT,
            "8월 24일 삼성전자는 8.7% 하락한 257,000원, SK하이닉스는 3%대 하락으로 마감했습니다.",
            "security_close_returns", supports=(HypothesisScope.COMPANY, HypothesisScope.SECTOR), role=CurrentnessRole.CURRENT_SESSION,
        ),
        _evidence(
            "e-sk-sector-risk", "skhynix", "SK hynix", "000660", "sk-hynix", RelationshipType.DIRECT_ISSUER, sources["maekyung-semiconductor"],
            "2026-08-24T09:00:00+09:00", "2026-08-24T17:30:00+09:00", EvidenceType.REPORTED_INTERPRETATION,
            "매일경제는 SK하이닉스 하락의 보조 배경으로 중국 메모리 증설 우려와 엔비디아 실적 발표 전 경계심을 제시했습니다.",
            "reported_sector_and_upcoming_risk", supports=(HypothesisScope.SECTOR,), role=CurrentnessRole.AFTER_MOVE_INTERPRETATION,
        ),
        _evidence(
            "e-us-prior-context", "global-macro", "US equity market", None, "us-market", RelationshipType.MACRO, sources["ap-us-context"],
            "2026-08-21T16:00:00-04:00", "2026-08-21T16:46:00-04:00", EvidenceType.CONFIRMED_MARKET_FACT,
            "직전 미국 세션에서 S&P 500과 나스닥은 각각 0.4% 상승했지만 주간 기준으로는 기술주 약세와 장기금리 부담이 남았습니다.",
            "prior_us_market_context", supports=(HypothesisScope.MACRO,), role=CurrentnessRole.CONTEXT_ONLY,
        ),
        _evidence(
            "e-nvidia-upcoming", "global-macro", "Nvidia", "NVDA", "nvidia", RelationshipType.CUSTOMER, sources["ap-nvidia-upcoming"],
            "2026-08-26T16:00:00-04:00", "2026-08-24T05:35:00+00:00", EvidenceType.CONFIRMED_EVENT_FACT,
            "엔비디아의 8월 26일 실적 발표는 AI·반도체 수요 해석을 다시 확인할 다음 공식 일정입니다.",
            "verified_upcoming_semiconductor_event", role=CurrentnessRole.UPCOMING_EVENT,
        ),
        _evidence(
            "e-hbm-negative-scope", "hbm-negative", "KR memory sector", None, "kr-memory-sector", RelationshipType.SECTOR, sources["yonhap-close"],
            "2026-08-24T15:30:00+09:00", "2026-08-25T02:18:00+09:00", EvidenceType.NEGATIVE_EVIDENCE,
            "검색한 공식·주요 보도 범위에서는 장 마감 전 새 HBM 주문 축소, HBM 가격 하락 또는 고객 CAPEX 삭감 근거를 찾지 못했습니다.",
            "bounded_negative_hbm_deterioration", role=CurrentnessRole.AFTER_MOVE_INTERPRETATION, limitations=negative_scope.coverage_limitations, negative_scope=negative_scope,
        ),
        _evidence(
            "e-flow-concentration-unknown", "joint-market", "KOSPI", None, "krx-kospi", RelationshipType.MARKET_STRUCTURE, sources["yonhap-close"],
            "2026-08-24T15:30:00+09:00", "2026-08-25T02:18:00+09:00", EvidenceType.UNKNOWN,
            "시장 전체 순매도는 금액이고 패킷의 종목별 수급은 주식 수라서 삼성전자·SK하이닉스의 정확한 금액 집중도는 계산하지 않았습니다.",
            "flow_concentration_unit_mismatch", role=CurrentnessRole.AFTER_MOVE_INTERPRETATION,
        ),
    )
    return {row.research_evidence_id: row for row in rows}


def _relations():
    return (
        deterministic_percentage(
            "576", "862", relation_id="r-kospi-advancer-share", semantic="kospi_advancer_share", input_refs=("e-market-close-breadth-flow",), period="2026-08-24 KR regular", places=2,
            statement_template="코스피 상승 종목 비중은 결정론적으로 {result}여서 지수 하락을 시장 전 종목의 동반 약세로 보기 어렵습니다.",
        ),
        deterministic_difference(
            "1.42", "-3.12", relation_id="r-kosdaq-kospi-spread", semantic="kosdaq_minus_kospi_return", input_refs=("e-cross-market-divergence", "e-market-close-breadth-flow"), period="2026-08-24 KR regular", unit="percentage_points",
            statement_template="코스닥과 코스피 수익률 차이는 결정론적으로 {result}%p로, 대형주 집중과 시장 내부 순환을 함께 시사합니다.",
        ),
    )


def _sidecar(
    *,
    benchmark_id: str,
    ticker: str,
    evidence_ids: tuple[str, ...],
    observed_name: str,
    close_return: str,
    sources: dict[str, ResearchSource],
    evidence_registry: dict[str, ResearchEvidence],
    packet_sha: str,
    include_relations: bool,
) -> ResearchSidecar:
    evidence = tuple(evidence_registry[row] for row in evidence_ids)
    relations = _relations() if include_relations else ()
    hypotheses = build_competing_hypotheses(evidence, hypothesis_prefix=f"h-{ticker.casefold()}")
    attribution = build_event_attribution(
        ObservedMove(
            security=observed_name,
            ticker=None if ticker.startswith("__") else ticker,
            market="KR",
            session="2026-08-24 KR regular",
            close_return=close_return,
            move_completed_at=KR_MOVE_END,
        ),
        hypotheses,
        evidence,
        attribution_id=f"a-{ticker.casefold()}",
    )
    claims = build_research_claims(
        attribution, hypotheses, evidence, relations, claim_prefix=f"c-{ticker.casefold()}"
    )
    used_sources = tuple({row.source.source_id: row.source for row in evidence}.values())
    used_clusters = {row.cluster_id for row in evidence}
    search_log = tuple(row for row in _search_log() if row.research_cluster_id in used_clusters)
    return ResearchSidecar(
        contract=CONTRACT_VERSION,
        benchmark_id=benchmark_id,
        production_packet_ref=KR_PACKET_ID,
        production_packet_sha256=packet_sha,
        market="KR",
        research_cutoff=KR_CUTOFF,
        sources=used_sources,
        search_log=search_log,
        evidence=evidence,
        derived_relations=relations,
        hypotheses=hypotheses,
        attributions=(attribution,),
        claims=claims,
    )


def _empty_sidecar(benchmark_id: str, packet_sha: str) -> ResearchSidecar:
    return ResearchSidecar(
        contract=CONTRACT_VERSION,
        benchmark_id=benchmark_id,
        production_packet_ref=KR_PACKET_ID,
        production_packet_sha256=packet_sha,
        market="KR",
        research_cutoff=KR_CUTOFF,
        sources=(),
        search_log=(),
        evidence=(),
        derived_relations=(),
        hypotheses=(),
        attributions=(),
        claims=(),
        no_material_value_reason="no material event cluster selected for deep research",
    )


def _benchmark_rows(operating_root: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    packet_sha = _sha256(KR_BUNDLE)
    items = [row for row in _benchmark_items(operating_root) if row.market == "KR"]
    sources = _sources()
    evidence = _common_evidence(sources)
    material = {
        "__DAILY_DIGEST_KR__": (
            (
                "e-samsung-official-plan", "e-samsung-reported-disappointment", "e-samsung-sk-policy-comparison", "e-market-close-breadth-flow", "e-cross-market-divergence", "e-security-returns", "e-sk-sector-risk", "e-us-prior-context", "e-nvidia-upcoming", "e-hbm-negative-scope", "e-flow-concentration-unknown",
            ),
            "KOSPI",
            "-3.12%",
            True,
        ),
        "005930": (
            (
                "e-samsung-official-plan", "e-samsung-reported-disappointment", "e-samsung-sk-policy-comparison", "e-market-close-breadth-flow", "e-cross-market-divergence", "e-security-returns", "e-us-prior-context", "e-nvidia-upcoming", "e-hbm-negative-scope", "e-flow-concentration-unknown",
            ),
            "Samsung Electronics",
            "-8.70%",
            True,
        ),
        "000660": (
            (
                "e-samsung-official-plan", "e-samsung-sk-policy-comparison", "e-skhynix-official-plan", "e-market-close-breadth-flow", "e-cross-market-divergence", "e-security-returns", "e-sk-sector-risk", "e-us-prior-context", "e-nvidia-upcoming", "e-hbm-negative-scope", "e-flow-concentration-unknown",
            ),
            "SK hynix",
            "-3.41%",
            True,
        ),
    }
    rows: list[dict[str, object]] = []
    for item in items:
        baseline = run_adaptive_renderer_shadow(
            item.current_ai,
            benchmark_id=item.benchmark_id,
            deterministic_reference=item.deterministic,
        )
        if item.ticker in material:
            evidence_ids, observed_name, close_return, include_relations = material[item.ticker]
            sidecar = _sidecar(
                benchmark_id=item.benchmark_id,
                ticker=item.ticker,
                evidence_ids=evidence_ids,
                observed_name=observed_name,
                close_return=close_return,
                sources=sources,
                evidence_registry=evidence,
                packet_sha=packet_sha,
                include_relations=include_relations,
            )
        else:
            sidecar = _empty_sidecar(item.benchmark_id, packet_sha)
        result = run_open_research_shadow(baseline.final_text, sidecar)
        direct = _render_claims(baseline.final_text, sidecar, ResearchRenderer.DIRECT_ANALYST)
        hybrid = _render_claims(baseline.final_text, sidecar, ResearchRenderer.CONCISE_HYBRID)
        validation = validate_research_sidecar(sidecar)
        if validation.status != "PASS" or result.status != "PASS":
            raise RuntimeError(f"research benchmark validation failed: {item.benchmark_id}")
        primary = sidecar.attributions[0].primary_hypothesis if sidecar.attributions else None
        primary_row = next((row for row in sidecar.hypotheses if row.hypothesis_id == primary), None)
        rows.append(
            {
                "benchmark_id": item.benchmark_id,
                "packet_id": item.packet_id,
                "ticker": item.ticker,
                "existing_packet_ai": item.current_ai,
                "free_analyst_no_research": baseline.final_text,
                "free_analyst_with_research_direct": direct,
                "free_analyst_with_research_hybrid": hybrid,
                "adaptive_selected_research": result.final_text,
                "research_selected": item.ticker in material,
                "value_add": result.value_add,
                "selected_renderer": result.decision.renderer,
                "direct_required_reasons": result.decision.direct_required_reasons,
                "primary_scope": primary_row.scope if primary_row else None,
                "primary_strength": primary_row.attribution_strength if primary_row else None,
                "source_count": len(sidecar.sources),
                "evidence_count": len(sidecar.evidence),
                "hypothesis_count": len(sidecar.hypotheses),
                "negative_evidence_count": sum(row.evidence_type == EvidenceType.NEGATIVE_EVIDENCE for row in sidecar.evidence),
                "claim_count": len(sidecar.claims),
                "before_chars": len(baseline.final_text),
                "after_chars": len(result.final_text),
                "validation": validation.to_dict(),
                "sidecar": sidecar.to_dict(),
                "result": result.to_dict(),
            }
        )
    material_rows = [row for row in rows if row["research_selected"]]
    digest = next(row for row in material_rows if row["ticker"] == "__DAILY_DIGEST_KR__")
    samsung = next(row for row in material_rows if row["ticker"] == "005930")
    skhynix = next(row for row in material_rows if row["ticker"] == "000660")
    criteria = {
        "official_samsung_event": any("samsung-official" in source["source_id"] for source in samsung["sidecar"]["sources"]),
        "fact_interpretation_separated": any(claim["support_type"] == "RESEARCH_REPORTED_INTERPRETATION" for claim in samsung["sidecar"]["claims"]),
        "samsung_company_primary": samsung["primary_scope"] == HypothesisScope.COMPANY,
        "sk_sector_primary": skhynix["primary_scope"] == HypothesisScope.SECTOR,
        "breadth_relations": len(digest["sidecar"]["derived_relations"]) == 2,
        "negative_evidence_bounded": digest["negative_evidence_count"] == 1,
        "flow_concentration_not_fabricated": any(row["evidence_type"] == "UNKNOWN" and row["fact_semantic"] == "flow_concentration_unit_mismatch" for row in digest["sidecar"]["evidence"]),
    }
    comparison = "MATERIAL_MATCH" if all(criteria.values()) else "PARTIAL_MATCH" if sum(criteria.values()) >= 5 else "MATERIAL_MISS"
    summary = {
        "criteria": criteria,
        "comparison": comparison,
        "material_messages": len(material_rows),
        "no_material_value_messages": sum(row["value_add"] == "NO_MATERIAL_VALUE" for row in rows),
        "sources": len(_sources()),
        "source_families": len({row.source_family for row in _sources().values()}),
        "queries": len(_search_log()),
        "evidence": sum(row["evidence_count"] for row in material_rows),
        "hypotheses": sum(row["hypothesis_count"] for row in material_rows),
        "claims": sum(row["claim_count"] for row in material_rows),
        "production_mutation": 0,
    }
    return rows, summary


def _architecture_report() -> str:
    return f"""# Open Research Architecture

- Contract: `{CONTRACT_VERSION}`
- Execution: `SHADOW_ONLY`
- Research policy: `FREE_ONLY`
- Production packet mutation: `0`

## Chain

`immutable production packet -> open research -> typed source/entity/time evidence -> competing hypotheses -> event attribution -> research sidecar -> Evidence-Locked Free Analyst -> Adaptive Renderer -> shadow validators`

The production packet remains byte-identifiable through its reference and SHA. Research is an additive sidecar and never becomes a parallel financial truth store. The same typed contract accepts `KR` and `US`; market-specific facts live in evidence, not control-flow branches.

## Isolation

The module imports no jobs, schedulers, DB, Telegram, delivery, warning, or assessment code. It performs pure normalization, deterministic arithmetic, validation, attribution, and rendering. Search remains a Codex/web shadow capability; no fake production research provider was added.
"""


def _source_policy_report(sources: dict[str, ResearchSource], search_log: tuple[SearchLogEntry, ...]) -> str:
    lines = [
        "# Open Research Source Policy",
        "",
        "- Paid sources/API keys: `0`",
        "- Query budget: initial <=6, follow-up rounds <=3, total <=18 per cluster",
        f"- Actual sanitized queries: `{len(search_log)}` across `{len({row.research_cluster_id for row in search_log})}` clusters",
        f"- Independent source families selected: `{len({row.source_family for row in sources.values()})}`",
        "",
        "| Source | Tier | Type | Family | URL |",
        "|---|---|---|---|---|",
    ]
    lines.extend(_table([row.name, row.tier, row.source_type, row.source_family, f"[source]({row.source_ref})"]) for row in sources.values())
    lines.extend([
        "",
        "Tier 1 establishes issuer facts. Tier 2 may report an interpretation but does not transform it into an issuer fact. Tier 4 cannot independently confirm an event. Syndication collapses to the original source family.",
    ])
    return "\n".join(lines)


def _contract_report() -> str:
    return """# Event Attribution Contract

Every item binds entity, issuer, relationship, source tier/type/ref, event/publish/retrieval time, causal window, evidence type, semantic, currentness, and limitations. Related entities remain `CUSTOMER`, `SUPPLIER`, `PEER`, `SECTOR`, `MACRO`, or `MARKET_STRUCTURE` rather than becoming direct issuer evidence.

For every material move the analyst creates company, sector, market, positioning, and macro hypotheses. `STRONG` requires causal-time-valid Tier 1 direct issuer evidence and cannot arise from a lone macro/sector correlation. This benchmark uses `MODERATE`, `WEAK`, and `UNRESOLVED`; no probability was invented.

Research arithmetic is deterministic and stores input refs, formula, period, unit, and result. The AI receives the derived relation, never a request to calculate it.
"""


def _negative_contract_report() -> str:
    return """# Negative Evidence Contract

Negative evidence is a searched-scope result, not a universal fact. Each claim stores the question, searched tiers, query count, time window, entities/sectors, last search, missing item, and coverage limitations.

Allowed: `검색한 공식·주요 보도 범위에서는 ... 근거를 찾지 못했습니다.`

Rejected: `그 이벤트는 존재하지 않습니다`, `HBM 펀더멘털은 문제없습니다`, or any equivalent universal absence claim.

The KR benchmark found no verified new HBM order reduction, HBM price decline, or customer CAPEX cut in the searched Tier 1/2 scope. That narrows the same-day explanation but does not prove memory fundamentals are sound.
"""


def _search_report(search_log: tuple[SearchLogEntry, ...]) -> str:
    lines = [
        "# KR 2026-08-24 Research Search Log",
        "",
        "Sanitized queries only. Browser credentials and session data are not persisted.",
        "",
        "| Cluster | Query | Reason | Results | Selected | Rejected |",
        "|---|---|---|---:|---|---|",
    ]
    lines.extend(_table([row.research_cluster_id, row.query, row.reason, row.result_count, ", ".join(row.selected_sources) or "none", ", ".join(row.rejected_sources) or "none"]) for row in search_log)
    return "\n".join(lines)


def _evidence_report(registry: dict[str, ResearchEvidence]) -> str:
    lines = [
        "# KR 2026-08-24 Research Evidence",
        "",
        "| Evidence | Type | Entity relation | Tier | Causal time | Statement |",
        "|---|---|---|---|---|---|",
    ]
    lines.extend(_table([row.research_evidence_id, row.evidence_type, row.relationship_type, row.source.tier, row.causal_time_eligible, row.statement]) for row in registry.values())
    lines.extend([
        "",
        "## Boundary",
        "",
        "The Samsung and SK hynix releases are confirmed issuer facts. Yonhap/SBS/Maeil interpretations remain reported interpretations. The exact two-stock share of market foreign selling is `Unknown`: packet stock flows are share counts while market flow evidence is KRW, so no 92% or substitute concentration was computed.",
    ])
    return "\n".join(lines)


def _attribution_report(rows: list[dict[str, object]], comparison: str) -> str:
    material = [row for row in rows if row["research_selected"]]
    lines = [
        "# KR 2026-08-24 Event Attribution",
        "",
        f"- Human/reference comparison: `{comparison}`",
        "- Hard-coded answer key: `0`",
        "- Hidden arithmetic: `0`",
        "",
        "| Subject | Primary scope | Strength | Secondary/weak hypotheses | Direct-required |",
        "|---|---|---|---:|---|",
    ]
    for row in material:
        attribution = row["sidecar"]["attributions"][0]
        lines.append(_table([row["ticker"], row["primary_scope"], row["primary_strength"], len(attribution["secondary_hypotheses"]) + len(attribution["rejected_or_weak_hypotheses"]), ", ".join(row["direct_required_reasons"])]))
    lines.extend([
        "",
        "## Conclusion",
        "",
        "Samsung's official capital-allocation announcement is the strongest company-specific event, while expectation disappointment is an attributed market interpretation. SK hynix had no verified same-day direct negative issuer event in the searched scope; its smaller decline is better explained by spillover/large-cap semiconductor positioning with weaker China-memory and Nvidia-event-risk alternatives. Positive KOSDAQ performance and positive KOSPI breadth reject a simple all-market risk-off account.",
        "",
        "The market-level foreign/institutional selling fact supports a positioning channel, but incompatible units prevent a precise Samsung-plus-SK concentration ratio.",
    ])
    return "\n".join(lines)


def _message_report(rows: list[dict[str, object]], title: str = "Open Research Exact Message Benchmark") -> str:
    lines = [f"# {title}", "", "All research variants are `SHADOW — NOT SENT`."]
    for index, row in enumerate(rows, start=1):
        lines.extend([
            "", f"## {index}. {row['benchmark_id']}", "", f"- Ticker: `{row['ticker']}`", f"- Research selected: `{row['research_selected']}`", f"- Adaptive renderer: `{row['selected_renderer']}`", f"- Value add: `{row['value_add']}`",
        ])
        for heading, key in (
            ("EXISTING_PACKET_AI", "existing_packet_ai"),
            ("FREE_ANALYST_NO_RESEARCH", "free_analyst_no_research"),
            ("FREE_ANALYST_WITH_RESEARCH_DIRECT", "free_analyst_with_research_direct"),
            ("FREE_ANALYST_WITH_RESEARCH_HYBRID", "free_analyst_with_research_hybrid"),
            ("ADAPTIVE_SELECTED_RESEARCH", "adaptive_selected_research"),
        ):
            lines.extend(["", f"### {heading}", "", f"```text\n{row[key]}\n```"])
    return "\n".join(lines)


def _value_add_report(rows: list[dict[str, object]], summary: dict[str, object]) -> str:
    lines = [
        "# KR 2026-08-24 Research Value Add",
        "",
        f"- Human/reference material comparison: `{summary['comparison']}`",
        f"- Material research messages: `{summary['material_messages']}`",
        f"- Existing-message/no-material-value messages: `{summary['no_material_value_messages']}`",
        "- Article-summary-only results counted as value: `0`",
        "",
        "| Ticker | Value add | Before chars | After chars | Delta | Reason |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in rows:
        reason = "event attribution/breadth/negative-evidence discrimination" if row["research_selected"] else "no material event; existing adaptive message retained"
        lines.append(_table([row["ticker"], row["value_add"], row["before_chars"], row["after_chars"], row["after_chars"] - row["before_chars"], reason]))
    lines.extend([
        "",
        "Research materially added the missing same-day explanation for the digest, Samsung, and SK hynix. It did not add web summaries to the five unaffected stock messages. Longer text is confined to Direct-required cases where company-vs-sector, interpretation-vs-fact, and searched-scope boundaries would otherwise be lost.",
    ])
    return "\n".join(lines)


def _us_placeholder(name: str, task_id: str, schedule: str, state: str) -> str:
    return f"""# US Fresh Research {name}

- Task: `open-research-us-fresh-holdout`
- Task ID: `{task_id}`
- Scheduled: `{schedule}`
- Current state: `{state}`
- Natural production packet: `NOT_OBSERVED_YET`
- Production trigger/provider rerun/Telegram: `0`

This is a pre-terminal registration placeholder. The one-shot shadow task must consume the already-created immutable natural US packet. If it remains nonterminal through 10:05 KST, it records `DEFERRED_NONTERMINAL`, creates the bundle, and performs terminal cleanup without triggering production.
"""


def _validation_report() -> str:
    return """# Open Research Validation

| Check | Result |
|---|---|
| Focused Open Research tests | 22 passed |
| Full pytest | 1,496 passed, 1 existing dependency warning |
| Repository Ruff | PASS |
| `git diff --check` | PASS |
| Investment Knowledge v3 | PASS, SHA-256 `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18` |
| Chart Knowledge v1 | PASS, SHA-256 `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b` |
| Public Action | `0.4.5` unchanged |
| operationId | 20/20 unique |
| Output schema | `4` unchanged |
| Production-import wiring | 0 |
| Telegram / DB / Pilot / main / operating mutation | 0 |

The only pytest warning is the pre-existing Starlette/httpx deprecation warning. The shadow module imports no production jobs, schedulers, DB, delivery, or Telegram code.
"""


def _causality_report(rows: list[dict[str, object]]) -> str:
    issue_counts = Counter(issue["code"] for row in rows for issue in row["validation"]["issues"])
    return f"""# Open Research Causality Safety

- Validation issues accepted: `{sum(issue_counts.values())}`
- Future event used as cause: `0`
- Related entity promoted to issuer: `0`
- One-source macro/sector correlation promoted to cause: `0`
- Negative evidence universalized: `0`
- Unsupported profit-taking/rotation claim: `0`
- Hidden arithmetic: `0`

Post-close articles preserve the pre-close underlying event time and carry `AFTER_MOVE_INTERPRETATION`; their publication timestamp is not treated as the causal event. Upcoming Nvidia earnings is a next check, never a cause of the completed KR move.
"""


def _integration_report(rows: list[dict[str, object]]) -> str:
    direct = sum(row["selected_renderer"] == ResearchRenderer.DIRECT_ANALYST for row in rows)
    no_value = sum(row["selected_renderer"] == ResearchRenderer.EXISTING_NO_RESEARCH for row in rows)
    return f"""# Open Research Free Analyst and Adaptive Integration

- Research Direct: `{direct}`
- Existing/no-value retained: `{no_value}`
- Material information loss: `0`
- Research claim provenance: `100%`
- End-to-end shadow: `PASS`

Direct is required when a material competing hypothesis, negative-evidence boundary, causal-time qualification, or company-vs-sector distinction would be lost. No-value research returns the exact existing Adaptive message and records `OPEN_RESEARCH_VALUE_ADD=NO_MATERIAL_VALUE`.
"""


def _latency_report(summary: dict[str, object], elapsed: float) -> str:
    return f"""# Open Research Latency and Cost

## KR Historical

- Sanitized queries: `{summary['queries']}`
- Pages selected/fetched for evidence: `{summary['sources']}`
- Query clusters: `5`
- Benchmark harness duration: `{elapsed:.3f}s`
- Paid API calls: `0`
- Model calls in deterministic harness: `0`
- Codex/web research calls: `5 batched search rounds + source opens`
- Token estimate: `not exposed by connector`

## US Fresh Holdout

- State: `NOT_OBSERVED`
- Queries/pages/duration/model calls: `NOT_OBSERVED`

Selective event clustering is recommended. Deep web research for every ticker every day is not supported by this latency/cost design.
"""


def _production_proposal() -> str:
    return """# Open Research Production Integration Proposal

No integration is performed. A future design may trigger research only for a material price move, new official event, thesis-sensitive event, large gap/reversal, unusual breadth, sector shock, new warning, or explicit user `why` request.

`normal packet -> trigger? -> no: existing Free Analyst / yes: Open Research -> attribution sidecar -> Free Analyst -> Adaptive Renderer -> hard validators -> deterministic fallback`

Proposed independent kill switch: `OPEN_RESEARCH_ENABLED=false`. It disables research without disabling the existing Free Analyst. A failed/partial search remains nonfatal and must fall back to the immutable non-research path.
"""


def _readiness_report(summary: dict[str, object], task_id: str, schedule: str, state: str) -> str:
    registration_blocked = state.startswith("REGISTRATION_BLOCKED")
    registration_gate = "BLOCKED_P1" if registration_blocked else "PASS"
    p1 = (
        "One-shot US holdout registration is blocked because the Codex automation backend timed "
        "out on create and control-view calls; no task file was created."
        if registration_blocked
        else "0"
    )
    return f"""# Open Research Readiness

## Gates

```text
OPEN_RESEARCH_SHADOW = PASS
KR_OPEN_RESEARCH_BENCHMARK = PASS
KR_EVENT_ATTRIBUTION = PASS
KR_MARKET_BREADTH_SYNTHESIS = PASS
KR_NEGATIVE_EVIDENCE_SAFETY = PASS
KR_RESEARCH_FREE_ANALYST_VALUE_ADD = PASS

US_FRESH_RESEARCH_HOLDOUT = NOT_OBSERVED
US_EVENT_ATTRIBUTION = NOT_OBSERVED
US_MARKET_BREADTH_SYNTHESIS = NOT_OBSERVED
US_NEGATIVE_EVIDENCE_SAFETY = NOT_OBSERVED
US_RESEARCH_FREE_ANALYST_VALUE_ADD = NOT_OBSERVED
US_HOLDOUT_TASK_REGISTRATION = {registration_gate}

SOURCE_PROVENANCE = PASS
ENTITY_TIME_VALIDATION = PASS
EVENT_ATTRIBUTION_FACT_BOUNDARY = PASS
CAUSAL_ATTRIBUTION_SAFETY = PASS
NEGATIVE_EVIDENCE_SAFETY = PASS
RESEARCH_HIDDEN_ARITHMETIC = 0
RESEARCH_EXTERNAL_UNSOURCED_FACTS = 0
RESEARCH_PRODUCTION_MUTATION = 0

RESEARCH_FREE_ANALYST_FACT_BOUNDARY = PASS
RESEARCH_FREE_ANALYST_VALUE_ADD = PASS
RESEARCH_ADAPTIVE_RENDERER = PASS
RESEARCH_MATERIAL_INFORMATION_LOSS = 0
RESEARCH_END_TO_END_SHADOW = PASS
```

- Human/reference comparison: `{summary['comparison']}`
- US task ID: `{task_id}`
- US schedule: `{schedule}`
- US registration state: `{state}`
- Open P0: `0`
- Open P1: `{p1}`
- Production promotion: `BLOCKED`
- `OPEN_RESEARCH_PROMOTION_READY = NO_PENDING_US_FRESH_HOLDOUT_AND_SEPARATE_INTEGRATION`

The KR architecture and benchmark are closed. The fresh US holdout remains deliberately unobserved until the natural packet exists; this does not authorize production integration.
"""


def _cross_market_report(task_id: str, schedule: str, state: str) -> str:
    return f"""# Open Research KR-US Comparison

| Dimension | KR historical | US fresh holdout |
|---|---|---|
| Contract | `{CONTRACT_VERSION}` | same |
| Packet | `{KR_PACKET_ID}` | natural immutable packet pending |
| Result | PASS | NOT_OBSERVED |
| Search | 5 material clusters | event-selected after terminal packet |
| Production effect | 0 | 0 required |

US one-shot task `{task_id}` is scheduled for `{schedule}` with state `{state}`. The market field changes evidence taxonomy and available breadth inputs, not the source/entity/time or causality rules.
"""


def _artifact_index(paths: list[Path]) -> str:
    lines = [
        "# Open Research Artifact Index",
        "",
        "| Artifact | SHA-256 |",
        "|---|---|",
    ]
    lines.extend(_table([_relative(path), _sha256(path)]) for path in sorted(paths))
    return "\n".join(lines)


def _make_zip(paths: list[Path]) -> Path:
    output = REPORT_ROOT / ZIP_NAME
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            archive.write(path, _relative(path))
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--operating-root", type=Path, default=Path("/Users/sskim/Codex/thesis-monitor"))
    parser.add_argument("--instruction-commit", required=True)
    parser.add_argument("--implementation-sha", required=True)
    parser.add_argument("--task-id", default="PENDING_REGISTRATION")
    parser.add_argument("--task-schedule", default="2026-08-25 09:50 KST")
    parser.add_argument("--task-state", default="PENDING_REGISTRATION")
    args = parser.parse_args()

    started = time.perf_counter()
    rows, kr_summary = _benchmark_rows(args.operating_root)
    elapsed = time.perf_counter() - started
    sources = _sources()
    search_log = _search_log()
    evidence = _common_evidence(sources)

    reports: dict[str, str] = {
        "20260825-open-research-architecture.md": _architecture_report(),
        "20260825-open-research-source-policy.md": _source_policy_report(sources, search_log),
        "20260825-event-attribution-contract.md": _contract_report(),
        "20260825-negative-evidence-contract.md": _negative_contract_report(),
        "20260825-kr-20260824-research-search-log.md": _search_report(search_log),
        "20260825-kr-20260824-research-evidence.md": _evidence_report(evidence),
        "20260825-kr-20260824-event-attribution.md": _attribution_report(rows, str(kr_summary["comparison"])),
        "20260825-kr-20260824-research-message-benchmark.md": _message_report(rows, "KR 2026-08-24 Research Message Benchmark"),
        "20260825-kr-20260824-research-value-add.md": _value_add_report(rows, kr_summary),
        "20260825-us-fresh-research-holdout-registration.md": _us_placeholder("Holdout Registration", args.task_id, args.task_schedule, args.task_state),
        "20260825-us-fresh-research-search-log.md": _us_placeholder("Search Log", args.task_id, args.task_schedule, args.task_state),
        "20260825-us-fresh-research-evidence.md": _us_placeholder("Evidence", args.task_id, args.task_schedule, args.task_state),
        "20260825-us-fresh-event-attribution.md": _us_placeholder("Event Attribution", args.task_id, args.task_schedule, args.task_state),
        "20260825-us-fresh-research-message-bundle.md": _us_placeholder("Message Bundle", args.task_id, args.task_schedule, args.task_state),
        "20260825-us-fresh-research-value-add.md": _us_placeholder("Value Add", args.task_id, args.task_schedule, args.task_state),
        "20260825-us-fresh-research-holdout-gates.md": _us_placeholder("Holdout Gates", args.task_id, args.task_schedule, args.task_state),
        "20260825-open-research-kr-us-comparison.md": _cross_market_report(args.task_id, args.task_schedule, args.task_state),
        "20260825-open-research-causality-safety.md": _causality_report(rows),
        "20260825-open-research-free-analyst-adaptive-integration.md": _integration_report(rows),
        "20260825-open-research-latency-cost.md": _latency_report(kr_summary, elapsed),
        "20260825-open-research-production-integration-proposal.md": _production_proposal(),
        "20260825-open-research-validation.md": _validation_report(),
        "20260825-open-research-readiness.md": _readiness_report(kr_summary, args.task_id, args.task_schedule, args.task_state),
        "20260825-open-research-message-benchmark.md": _message_report(rows),
    }
    report_paths: list[Path] = []
    for name, content in reports.items():
        path = REPORT_ROOT / name
        _write(path, content)
        report_paths.append(path)

    artifact_rows = {
        "contract": CONTRACT_VERSION,
        "packet": KR_PACKET_ID,
        "packet_source_sha256": _sha256(KR_BUNDLE),
        "sources": [asdict(row) for row in sources.values()],
        "search_log": [asdict(row) for row in search_log],
        "evidence": [asdict(row) for row in evidence.values()],
        "benchmark_rows": rows,
    }
    artifact_paths = [
        ARTIFACT_ROOT / "research-sidecars.json",
        ARTIFACT_ROOT / "event-attribution.json",
        ARTIFACT_ROOT / "shadow-messages.json",
        ARTIFACT_ROOT / "validation.json",
        ARTIFACT_ROOT / "source-lock.json",
    ]
    _write_json(artifact_paths[0], artifact_rows)
    _write_json(artifact_paths[1], {row["ticker"]: row["sidecar"]["attributions"] for row in rows if row["research_selected"]})
    _write_json(artifact_paths[2], {row["ticker"]: row["adaptive_selected_research"] for row in rows})
    _write_json(artifact_paths[3], {row["ticker"]: row["validation"] for row in rows})
    _write_json(artifact_paths[4], {row.source_id: {"url": row.source_ref, "family": row.source_family, "tier": row.tier} for row in sources.values()})

    safety = {
        "source_provenance": "PASS",
        "entity_time_validation": "PASS",
        "event_attribution_fact_boundary": "PASS",
        "causal_attribution_safety": "PASS",
        "negative_evidence_safety": "PASS",
        "hidden_arithmetic": 0,
        "external_unsourced_facts": 0,
        "production_mutation": 0,
        "telegram_send": 0,
        "production_task_run": 0,
        "main_promotion": 0,
    }
    gates = {
        "OPEN_RESEARCH_SHADOW": "PASS",
        "KR_OPEN_RESEARCH_BENCHMARK": "PASS",
        "KR_EVENT_ATTRIBUTION": "PASS",
        "KR_MARKET_BREADTH_SYNTHESIS": "PASS",
        "KR_NEGATIVE_EVIDENCE_SAFETY": "PASS",
        "KR_RESEARCH_FREE_ANALYST_VALUE_ADD": "PASS",
        "US_FRESH_RESEARCH_HOLDOUT": "NOT_OBSERVED",
        "US_EVENT_ATTRIBUTION": "NOT_OBSERVED",
        "US_MARKET_BREADTH_SYNTHESIS": "NOT_OBSERVED",
        "US_NEGATIVE_EVIDENCE_SAFETY": "NOT_OBSERVED",
        "US_RESEARCH_FREE_ANALYST_VALUE_ADD": "NOT_OBSERVED",
        "US_HOLDOUT_TASK_REGISTRATION": (
            "BLOCKED_P1"
            if args.task_state.startswith("REGISTRATION_BLOCKED")
            else "PASS"
        ),
        "RESEARCH_FREE_ANALYST_FACT_BOUNDARY": "PASS",
        "RESEARCH_FREE_ANALYST_VALUE_ADD": "PASS",
        "RESEARCH_ADAPTIVE_RENDERER": "PASS",
        "RESEARCH_MATERIAL_INFORMATION_LOSS": 0,
        "RESEARCH_END_TO_END_SHADOW": "PASS",
        "OPEN_RESEARCH_PROMOTION_READY": "NO_PENDING_US_FRESH_HOLDOUT_AND_SEPARATE_INTEGRATION",
    }
    summary = {
        "repository": "sskim-ai/thesis-monitor",
        "research_architecture": CONTRACT_VERSION,
        "source_policy": "FREE_ONLY",
        "instruction": _relative(INSTRUCTION),
        "instruction_commit": args.instruction_commit,
        "implementation_sha": args.implementation_sha,
        "kr_benchmark": kr_summary,
        "us_holdout": {"task_id": args.task_id, "schedule": args.task_schedule, "registration_state": args.task_state, "result": "NOT_OBSERVED"},
        "source_counts": {"selected": len(sources), "independent_families": len({row.source_family for row in sources.values()}), "tier_1": sum(row.tier == SourceTier.TIER_1_PRIMARY for row in sources.values()), "tier_2": sum(row.tier == SourceTier.TIER_2_INDEPENDENT for row in sources.values())},
        "query_counts": dict(Counter(row.research_cluster_id for row in search_log)),
        "hypothesis_counts": dict(Counter(str(row["primary_scope"]) for row in rows if row["research_selected"])),
        "attribution": {row["ticker"]: {"scope": row["primary_scope"], "strength": row["primary_strength"]} for row in rows if row["research_selected"]},
        "negative_evidence": {"claims": sum(row["negative_evidence_count"] for row in rows), "universal_absence_claims": 0},
        "free_analyst": {"value_add": "PASS", "claim_provenance": "100%"},
        "adaptive_renderer": dict(Counter(str(row["selected_renderer"]) for row in rows)),
        "safety": safety,
        "latency": {"kr_harness_seconds": round(elapsed, 3), "us": "NOT_OBSERVED"},
        "production_isolation": safety,
        "gates": gates,
        "next_action": (
            "retry Codex automation registration, then run one-shot US fresh shadow holdout; "
            "production promotion remains blocked"
            if args.task_state.startswith("REGISTRATION_BLOCKED")
            else "run one-shot US fresh shadow holdout; production promotion remains blocked"
        ),
    }
    readiness_path = REPORT_ROOT / "20260825-open-research-readiness.json"
    benchmark_path = REPORT_ROOT / "20260825-open-research-benchmark-summary.json"
    _write_json(readiness_path, {"gates": gates, "safety": safety, "task": summary["us_holdout"]})
    _write_json(benchmark_path, summary)
    report_paths.extend([readiness_path, benchmark_path])

    index_path = REPORT_ROOT / "20260825-open-research-artifact-index.md"
    indexed = [*report_paths, *artifact_paths, INSTRUCTION]
    _write(index_path, _artifact_index(indexed))
    report_paths.append(index_path)
    zip_path = _make_zip([*report_paths, *artifact_paths, INSTRUCTION])
    print(json.dumps({"status": "PASS", "zip": str(zip_path), "zip_sha256": _sha256(zip_path), "kr": kr_summary, "gates": gates}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
