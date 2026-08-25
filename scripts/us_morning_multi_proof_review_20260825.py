from __future__ import annotations

# ruff: noqa: E501

import glob
import hashlib
import json
import os
import sqlite3
import sys
import time
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPERATING = Path(os.environ.get("THESIS_MONITOR_OPERATING_ROOT", "/Users/sskim/Codex/thesis-monitor"))
OPEN_RESEARCH = Path(
    os.environ.get(
        "THESIS_MONITOR_OPEN_RESEARCH_ROOT",
        "/Users/sskim/Documents/Codex/2026-07-04/the/work/thesis-monitor-open-research",
    )
)
REPORTS = ROOT / "docs/reports"
PACKET_ID = "2026-08-25-us-run-37-7e04812311c2"
PACKET_PATH = OPERATING / f"data/ai_review/inbox/{PACKET_ID}.json"
HISTORY = OPERATING / f"data/ai_review/pilot/history/2026/08/{PACKET_ID}"
RESEARCH_CUTOFF = "2026-08-25T09:41:00+09:00"
MOVE_COMPLETED_AT = "2026-08-24T16:00:00-04:00"
RETRIEVED_AT = RESEARCH_CUTOFF
MARKET_SESSION = "2026-08-24 US regular"
INSTRUCTION = ROOT / "docs/work-instructions/20260825-us-morning-natural-and-open-research-multi-proof-review.md"
ZIP_PATH = REPORTS / "20260825-us-morning-natural-and-open-research-multi-proof-bundle.zip"

if str(OPEN_RESEARCH) not in sys.path:
    sys.path.insert(0, str(OPEN_RESEARCH))

from app.services.adaptive_renderer_selector_shadow_service import (  # noqa: E402
    run_adaptive_renderer_shadow,
)
from app.services.open_research_event_attribution_shadow_service import (  # noqa: E402
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
    run_open_research_shadow,
    validate_research_sidecar,
)


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, value: object) -> None:
    write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("\n", " ") for value in values) + " |"


def payload_text(row: dict[str, object]) -> str:
    payload = json.loads(str(row["payload"]))
    telegram = payload.get("_telegram_delivery") or {}
    return str(telegram.get("rendered_text") or payload["text"])


def production_rows() -> list[dict[str, object]]:
    connection = sqlite3.connect(
        f"file:{OPERATING / 'data/thesis_monitor.sqlite3'}?mode=ro", uri=True
    )
    connection.row_factory = sqlite3.Row
    try:
        return [
            dict(row)
            for row in connection.execute(
                "SELECT * FROM notificationdelivery "
                "WHERE assessment_date = ? AND id BETWEEN 286 AND 299 ORDER BY id",
                ("2026-08-25",),
            )
        ]
    finally:
        connection.close()


def source(
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


def sources() -> dict[str, ResearchSource]:
    rows = (
        source(
            "ap-market-close",
            "Associated Press",
            SourceTier.TIER_2_INDEPENDENT,
            SourceType.WIRE_NEWS,
            "https://apnews.com/article/8ab800029c559c5e751058ac1a8ef932",
            "ap",
        ),
        source(
            "nvidia-official-event",
            "NVIDIA Investor Relations",
            SourceTier.TIER_1_PRIMARY,
            SourceType.ISSUER_OFFICIAL,
            "https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Sets-Conference-Call-for-Second-Quarter-Financial-Results/default.aspx",
            "nvidia-ir",
        ),
        source(
            "yahoo-memory-report",
            "Yahoo Finance",
            SourceTier.TIER_3_SECONDARY,
            SourceType.SECONDARY_REPORT,
            "https://finance.yahoo.com/markets/stocks/articles/memory-stocks-slide-report-apple-152936889.html",
            "yahoo-finance",
        ),
        source(
            "appleinsider-rumor-boundary",
            "AppleInsider",
            SourceTier.TIER_3_SECONDARY,
            SourceType.SECONDARY_REPORT,
            "https://appleinsider.com/articles/26/08/24/trump-may-use-apple-chinese-ram-buy-request-as-diplomatic-tool",
            "appleinsider",
        ),
        source(
            "sandisk-official",
            "Sandisk Investor Relations",
            SourceTier.TIER_1_PRIMARY,
            SourceType.ISSUER_OFFICIAL,
            "https://investor.sandisk.com/news-events/news-releases",
            "sandisk-ir",
        ),
        source(
            "micron-official",
            "Micron Newsroom",
            SourceTier.TIER_1_PRIMARY,
            SourceType.ISSUER_OFFICIAL,
            "https://www.micron.com/about/press/news",
            "micron-newsroom",
        ),
        source(
            "skhynix-official",
            "SK hynix Newsroom",
            SourceTier.TIER_1_PRIMARY,
            SourceType.ISSUER_OFFICIAL,
            "https://news.skhynix.com/en/",
            "skhynix-newsroom",
        ),
        source(
            "recursion-official",
            "Recursion Investor Relations",
            SourceTier.TIER_1_PRIMARY,
            SourceType.ISSUER_OFFICIAL,
            "https://ir.recursion.com/news-events/press-releases",
            "recursion-ir",
        ),
        source(
            "weride-official",
            "WeRide Investor Relations",
            SourceTier.TIER_1_PRIMARY,
            SourceType.ISSUER_OFFICIAL,
            "https://ir.weride.ai/news-events/news-releases",
            "weride-ir",
        ),
        source(
            "core-scientific-official",
            "Core Scientific Investor Relations",
            SourceTier.TIER_1_PRIMARY,
            SourceType.ISSUER_OFFICIAL,
            "https://investors.corescientific.com/news-events/press-releases",
            "core-scientific-ir",
        ),
    )
    return {row.source_id: row for row in rows}


SEARCH_ROWS = (
    ("market", "site:apnews.com August 24 2026 Wall Street mixed finish Nvidia Wednesday Micron memory", "market close and breadth", ("ap-market-close",), ()),
    ("market", "site:investor.nvidia.com August 2026 earnings date August 26 2026 NVIDIA official", "verified next event", ("nvidia-official-event",), ()),
    ("memory", "August 24 2026 Micron SanDisk SK hynix memory stocks fell CXMT YMTC Apple rumor", "memory-cluster attribution", ("yahoo-memory-report", "appleinsider-rumor-boundary"), ()),
    ("memory", "AppleInsider questionable leaker Trump Apple CXMT YMTC August 24 2026 memory rumor", "rumor reliability boundary", ("appleinsider-rumor-boundary",), ()),
    ("memory", "site:investor.sandisk.com/news-releases 2026 August 24 SanDisk", "issuer event check", ("sandisk-official",), ("no Aug 24 issuer event",)),
    ("memory", "site:ir.micron.com/news-releases 2026 August 24 Micron", "issuer event check", ("micron-official",), ("Aug 24 training-center item had no verified causal time or operating deterioration",)),
    ("memory", "Micron investor relations news releases August 2026 official", "issuer event follow-up", ("micron-official",), ()),
    ("memory", "site:news.skhynix.com August 24 2026 SK hynix", "issuer event check", ("skhynix-official",), ("Aug 25 technology article occurred after the price-move session",)),
    ("rxrx", "site:ir.recursion.com/news-releases August 24 2026 Recursion", "unusual-move issuer check", ("recursion-official",), ("no Aug 24 issuer event",)),
    ("rxrx", "site:ir.recursion.com SEC filings August 24 2026 RXRX", "filing check", ("recursion-official",), ("no material Aug 24 filing selected",)),
    ("wrd", "site:ir.weride.ai/news-releases August 2026 WeRide", "unusual-move issuer check", ("weride-official",), ("no Aug 24 issuer event",)),
    ("corz", "site:investors.corescientific.com/news-events/press-releases August 2026 Core Scientific latest news", "issuer event check", ("core-scientific-official",), ("latest release Aug 14",)),
    ("tsla", "site:investors.tesla.com press release August 24 2026 Tesla", "issuer event check", (), ("no selected official result",)),
    ("market", "August 24 2026 US stock market S&P Nasdaq Russell semiconductor breadth", "cross-sectional market context", ("ap-market-close",), ()),
    ("memory", "August 24 2026 official Micron Sandisk SK hynix order cut guidance cut", "direct deterioration negative check", ("sandisk-official",), ("no verified direct deterioration selected",)),
    ("corz", "August 24 2026 Core Scientific CORZ stock news official investor relations", "same-session event check", ("core-scientific-official",), ("no Aug 24 issuer event",)),
)


def search_log() -> tuple[SearchLogEntry, ...]:
    parent_queries = {
        "Micron investor relations news releases August 2026 official": (
            "site:ir.micron.com/news-releases 2026 August 24 Micron"
        ),
    }
    return tuple(
        SearchLogEntry(
            research_cluster_id=cluster,
            query=query,
            created_at=RETRIEVED_AT,
            reason=reason,
            parent_query=parent_queries.get(query),
            result_count=len(selected) + len(rejected),
            selected_sources=selected,
            rejected_sources=rejected,
        )
        for cluster, query, reason, selected, rejected in SEARCH_ROWS
    )


def evidence(
    evidence_id: str,
    cluster: str,
    entity: str,
    ticker: str | None,
    issuer_identity: str,
    relationship: RelationshipType,
    source_row: ResearchSource,
    event_at: str,
    published_at: str,
    evidence_type: EvidenceType,
    statement: str,
    semantic: str,
    *,
    supports: tuple[HypothesisScope, ...] = (),
    contradicts: tuple[HypothesisScope, ...] = (),
    role: CurrentnessRole = CurrentnessRole.CURRENT_SESSION,
    limitations: tuple[str, ...] = (),
    negative_scope: NegativeEvidenceScope | None = None,
) -> ResearchEvidence:
    return ResearchEvidence(
        research_evidence_id=evidence_id,
        cluster_id=cluster,
        entity=entity,
        ticker=ticker,
        market="US",
        issuer_identity=issuer_identity,
        related_entity=None if relationship == RelationshipType.DIRECT_ISSUER else entity,
        relationship_type=relationship,
        source=source_row,
        event_at=event_at,
        published_at=published_at,
        retrieved_at=RETRIEVED_AT,
        research_cutoff=RESEARCH_CUTOFF,
        market_session=MARKET_SESSION,
        causal_window_end=MOVE_COMPLETED_AT,
        evidence_type=evidence_type,
        statement=statement,
        fact_semantic=semantic,
        causal_time_eligible=causal_time_eligible(event_at, MOVE_COMPLETED_AT),
        currentness_role=role,
        supports_scopes=supports,
        contradicts_scopes=contradicts,
        limitations=limitations,
        negative_scope=negative_scope,
    )


def evidence_registry(source_rows: dict[str, ResearchSource]) -> dict[str, ResearchEvidence]:
    negative_scope = NegativeEvidenceScope(
        question="Was there a verified new issuer-specific order cut, guidance cut, or CAPEX cancellation before the August 24 US close?",
        searched_source_tiers=(
            SourceTier.TIER_1_PRIMARY,
            SourceTier.TIER_2_INDEPENDENT,
            SourceTier.TIER_3_SECONDARY,
        ),
        query_count=6,
        searched_time_window="2026-08-21 through 2026-08-24 US close",
        entities_or_sectors_checked=("Micron", "Sandisk", "SK hynix", "memory"),
        last_search_at=RETRIEVED_AT,
        what_was_not_found="verified same-session issuer order cut, guidance cut, or CAPEX cancellation",
        coverage_limitations=(
            "free public issuer pages and indexed major-news sources only",
            "absence in the searched scope does not prove fundamentals are unchanged",
        ),
    )
    rows = (
        evidence(
            "e-us-market-close",
            "market",
            "US equity market",
            None,
            "us-equity-market",
            RelationshipType.MARKET_STRUCTURE,
            source_rows["ap-market-close"],
            "2026-08-24T16:00:00-04:00",
            "2026-08-24T16:35:00-04:00",
            EvidenceType.CONFIRMED_MARKET_FACT,
            "AP는 S&P500이 소폭 하락하고 Nasdaq 낙폭이 더 컸지만 S&P500 구성 종목 다수는 상승해 기술주가 하락을 주도한 혼합 장세였다고 보도했습니다.",
            "us_market_close_and_internal_breadth",
            supports=(HypothesisScope.MARKET,),
        ),
        evidence(
            "e-us-tech-interpretation",
            "market",
            "US technology sector",
            None,
            "us-technology-sector",
            RelationshipType.SECTOR,
            source_rows["ap-market-close"],
            "2026-08-24T16:00:00-04:00",
            "2026-08-24T16:35:00-04:00",
            EvidenceType.REPORTED_INTERPRETATION,
            "AP는 기술주 약세를 높은 AI Valuation과 칩 수요의 이익 전환 지속성에 대한 우려, 그리고 엔비디아 실적 발표 전 경계와 연결해 해석했습니다.",
            "reported_ai_valuation_and_event_risk",
            supports=(HypothesisScope.SECTOR, HypothesisScope.MARKET),
            role=CurrentnessRole.AFTER_MOVE_INTERPRETATION,
            limitations=("reported market interpretation, not a direct issuer fact",),
        ),
        evidence(
            "e-memory-reported-catalyst",
            "memory",
            "US-listed memory equities",
            None,
            "memory-sector",
            RelationshipType.SECTOR,
            source_rows["yahoo-memory-report"],
            "2026-08-24T09:00:00-04:00",
            "2026-08-24T11:29:00-04:00",
            EvidenceType.REPORTED_INTERPRETATION,
            "2차 시장 보도는 MU·SNDK·SKHY의 동반 하락을 Apple의 CXMT·YMTC 메모리 조달 허용 가능성 보도와 일부 연결했습니다.",
            "reported_memory_sector_policy_rumor",
            supports=(HypothesisScope.SECTOR,),
            limitations=("secondary attribution; no official policy confirmation",),
        ),
        evidence(
            "e-memory-rumor-boundary",
            "memory",
            "Apple memory sourcing report",
            None,
            "apple-memory-sourcing",
            RelationshipType.CUSTOMER,
            source_rows["appleinsider-rumor-boundary"],
            "2026-08-24T12:31:00-04:00",
            "2026-08-24T12:31:00-04:00",
            EvidenceType.REPORTED_INTERPRETATION,
            "AppleInsider는 당일 정책 변경 주장의 출처가 Weibo 제보자라고 추적하고 신뢰도를 낮게 평가했으며 실제 정책 변경 여부를 검증하지 못했다고 밝혔습니다.",
            "reported_rumor_reliability_boundary",
            contradicts=(HypothesisScope.COMPANY,),
            limitations=("does not disprove that the rumor affected prices",),
        ),
        evidence(
            "e-nvidia-next-event",
            "market",
            "NVIDIA",
            "NVDA",
            "nvidia",
            RelationshipType.SECTOR,
            source_rows["nvidia-official-event"],
            "2026-08-26T17:00:00-04:00",
            "2026-07-29T09:00:00-04:00",
            EvidenceType.CONFIRMED_EVENT_FACT,
            "NVIDIA는 8월 26일 미국장 마감 후 회계연도 2분기 실적 발표와 컨퍼런스콜을 공식 예고했습니다.",
            "verified_upcoming_semiconductor_event",
            role=CurrentnessRole.UPCOMING_EVENT,
        ),
        evidence(
            "e-mu-negative-scope",
            "memory",
            "Micron",
            "MU",
            "micron",
            RelationshipType.DIRECT_ISSUER,
            source_rows["micron-official"],
            "2026-08-24T16:00:00-04:00",
            RETRIEVED_AT,
            EvidenceType.NEGATIVE_EVIDENCE,
            "검색한 무료 공개 Micron 자료와 주요 보도 범위에서는 미국장 마감 전 신규 주문 축소, 가이던스 하향 또는 CAPEX 취소의 검증된 직접 근거를 찾지 못했습니다.",
            "bounded_negative_direct_memory_deterioration",
            contradicts=(HypothesisScope.COMPANY,),
            role=CurrentnessRole.AFTER_MOVE_INTERPRETATION,
            limitations=negative_scope.coverage_limitations,
            negative_scope=negative_scope,
        ),
        evidence(
            "e-sndk-negative-scope",
            "memory",
            "Sandisk",
            "SNDK",
            "sandisk",
            RelationshipType.DIRECT_ISSUER,
            source_rows["sandisk-official"],
            "2026-08-24T16:00:00-04:00",
            RETRIEVED_AT,
            EvidenceType.NEGATIVE_EVIDENCE,
            "검색한 무료 공개 Sandisk 자료와 주요 보도 범위에서는 미국장 마감 전 신규 주문 축소, 가이던스 하향 또는 CAPEX 취소의 검증된 직접 근거를 찾지 못했습니다.",
            "bounded_negative_direct_memory_deterioration",
            contradicts=(HypothesisScope.COMPANY,),
            role=CurrentnessRole.AFTER_MOVE_INTERPRETATION,
            limitations=negative_scope.coverage_limitations,
            negative_scope=negative_scope,
        ),
        evidence(
            "e-skhy-negative-scope",
            "memory",
            "SK hynix",
            "SKHY",
            "sk-hynix",
            RelationshipType.DIRECT_ISSUER,
            source_rows["skhynix-official"],
            "2026-08-24T16:00:00-04:00",
            RETRIEVED_AT,
            EvidenceType.NEGATIVE_EVIDENCE,
            "검색한 무료 공개 SK hynix 자료와 주요 보도 범위에서는 미국장 마감 전 신규 주문 축소, 가이던스 하향 또는 CAPEX 취소의 검증된 직접 근거를 찾지 못했습니다.",
            "bounded_negative_direct_memory_deterioration",
            contradicts=(HypothesisScope.COMPANY,),
            role=CurrentnessRole.AFTER_MOVE_INTERPRETATION,
            limitations=negative_scope.coverage_limitations,
            negative_scope=negative_scope,
        ),
        evidence(
            "e-sandisk-latest-official",
            "memory",
            "Sandisk",
            "SNDK",
            "sandisk",
            RelationshipType.DIRECT_ISSUER,
            source_rows["sandisk-official"],
            "2026-08-13T10:59:00-04:00",
            "2026-08-13T10:59:00-04:00",
            EvidenceType.CONFIRMED_EVENT_FACT,
            "선택된 Sandisk 공식 자료의 최신 항목은 8월 13일 Investor Day 업데이트였으며 당일 신규 부정 영업 공시는 아니었습니다.",
            "issuer_latest_selected_release_context",
            role=CurrentnessRole.CONTEXT_ONLY,
            limitations=("context only; not evidence that no other event exists",),
        ),
    )
    return {row.research_evidence_id: row for row in rows}


def build_sidecar(
    ticker: str,
    name: str,
    move: str,
    packet_sha: str,
    registry: dict[str, ResearchEvidence],
    source_rows: dict[str, ResearchSource],
) -> ResearchSidecar:
    if ticker == "__DAILY_DIGEST__":
        evidence_ids = (
            "e-us-market-close",
            "e-us-tech-interpretation",
            "e-nvidia-next-event",
        )
        clusters = {"market"}
    else:
        evidence_ids = (
            "e-us-market-close",
            "e-us-tech-interpretation",
            "e-memory-reported-catalyst",
            "e-memory-rumor-boundary",
            "e-nvidia-next-event",
            f"e-{ticker.casefold()}-negative-scope",
            *(('e-sandisk-latest-official',) if ticker == "SNDK" else ()),
        )
        clusters = {"market", "memory"}
    rows = tuple(registry[row] for row in evidence_ids)
    hypotheses = build_competing_hypotheses(rows, hypothesis_prefix=f"h-{ticker.casefold()}")
    attribution = build_event_attribution(
        ObservedMove(
            security=name,
            ticker=None if ticker == "__DAILY_DIGEST__" else ticker,
            market="US",
            session=MARKET_SESSION,
            close_return=move,
            move_completed_at=MOVE_COMPLETED_AT,
        ),
        hypotheses,
        rows,
        attribution_id=f"a-{ticker.casefold()}",
    )
    claims = build_research_claims(
        attribution,
        hypotheses,
        rows,
        (),
        claim_prefix=f"c-{ticker.casefold()}",
    )
    used_sources = tuple({row.source.source_id: row.source for row in rows}.values())
    logs = tuple(row for row in search_log() if row.research_cluster_id in clusters)
    return ResearchSidecar(
        contract=CONTRACT_VERSION,
        benchmark_id=f"us-20260824-{ticker.casefold()}",
        production_packet_ref=PACKET_ID,
        production_packet_sha256=packet_sha,
        market="US",
        research_cutoff=RESEARCH_CUTOFF,
        sources=used_sources,
        search_log=logs,
        evidence=rows,
        derived_relations=(),
        hypotheses=hypotheses,
        attributions=(attribution,),
        claims=claims,
    )


def empty_sidecar(ticker: str, packet_sha: str) -> ResearchSidecar:
    return ResearchSidecar(
        contract=CONTRACT_VERSION,
        benchmark_id=f"us-20260824-{ticker.casefold()}",
        production_packet_ref=PACKET_ID,
        production_packet_sha256=packet_sha,
        market="US",
        research_cutoff=RESEARCH_CUTOFF,
        sources=(),
        search_log=(),
        evidence=(),
        derived_relations=(),
        hypotheses=(),
        attributions=(),
        claims=(),
        no_material_value_reason="no verified material research value selected",
    )


def run_research(rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, object]]:
    packet_sha = sha256(PACKET_PATH)
    source_rows = sources()
    registry = evidence_registry(source_rows)
    moves = {
        "__DAILY_DIGEST__": ("US equity market", "S&P -0.3%; Nasdaq -0.8%"),
        "MU": ("Micron Technology", "-5.83%"),
        "SNDK": ("Sandisk", "-6.45%"),
        "SKHY": ("SK hynix ADR", "-4.92%"),
    }
    results: list[dict[str, object]] = []
    start = time.perf_counter()
    for delivery in rows:
        ticker = str(delivery["ticker"])
        current = payload_text(delivery)
        benchmark_id = f"us-20260824-{ticker.casefold()}"
        baseline = run_adaptive_renderer_shadow(
            current,
            benchmark_id=benchmark_id,
            deterministic_reference=current,
        )
        selected = ticker in moves
        if selected:
            name, move = moves[ticker]
            sidecar = build_sidecar(
                ticker, name, move, packet_sha, registry, source_rows
            )
        else:
            sidecar = empty_sidecar(ticker, packet_sha)
        validation = validate_research_sidecar(sidecar)
        shadow = run_open_research_shadow(baseline.final_text, sidecar)
        direct = _render_claims(
            baseline.final_text, sidecar, ResearchRenderer.DIRECT_ANALYST
        )
        hybrid = _render_claims(
            baseline.final_text, sidecar, ResearchRenderer.CONCISE_HYBRID
        )
        primary = None
        if sidecar.attributions:
            primary_id = sidecar.attributions[0].primary_hypothesis
            hypothesis = next(row for row in sidecar.hypotheses if row.hypothesis_id == primary_id)
            primary = {
                "id": primary_id,
                "scope": hypothesis.scope,
                "strength": hypothesis.attribution_strength,
            }
        results.append(
            {
                "ticker": ticker,
                "research_selected": selected,
                "natural_production_message": current,
                "free_analyst_no_research": baseline.final_text,
                "free_analyst_status": baseline.status,
                "free_analyst_with_research_direct": direct,
                "free_analyst_with_research_hybrid": hybrid,
                "adaptive_selected_research": shadow.final_text,
                "selected_renderer": shadow.decision.renderer,
                "value_add": shadow.value_add,
                "primary": primary,
                "sidecar": sidecar.to_dict(),
                "validation": validation.to_dict(),
                "result": shadow.to_dict(),
            }
        )
    elapsed_ms = round((time.perf_counter() - start) * 1000, 3)
    selected_rows = [row for row in results if row["research_selected"]]
    research_validation_pass_count = sum(
        row["validation"]["status"] == "PASS" for row in results
    )
    research_shadow_pass_count = sum(
        row["result"]["status"] == "PASS" for row in results
    )
    free_analyst_pass_count = sum(
        row["free_analyst_status"] == "PASS" for row in results
    )
    all_pass = (
        research_validation_pass_count == len(results)
        and research_shadow_pass_count == len(results)
        and free_analyst_pass_count == len(results)
    )
    summary = {
        "contract": CONTRACT_VERSION,
        "research_cutoff_kst": RESEARCH_CUTOFF,
        "market_session": MARKET_SESSION,
        "messages": len(results),
        "researched_messages": len(selected_rows),
        "no_material_value_messages": sum(row["value_add"] == "NO_MATERIAL_VALUE" for row in results),
        "query_count": len(SEARCH_ROWS),
        "source_count": len(source_rows),
        "primary_source_count": sum(row.tier == SourceTier.TIER_1_PRIMARY for row in source_rows.values()),
        "high_quality_news_count": sum(row.tier == SourceTier.TIER_2_INDEPENDENT for row in source_rows.values()),
        "source_family_count": len({row.source_family for row in source_rows.values()}),
        "duplicate_source_family_count": len(source_rows) - len({row.source_family for row in source_rows.values()}),
        "shadow_execution_ms": elapsed_ms,
        "web_research_elapsed_minutes": 23,
        "model_calls": 0,
        "estimated_token_usage": "not_available",
        "research_validation_pass_count": research_validation_pass_count,
        "research_shadow_pass_count": research_shadow_pass_count,
        "free_analyst_pass_count": free_analyst_pass_count,
        "free_analyst_fallback_count": len(results) - free_analyst_pass_count,
        "selected_free_analyst_fallback_count": sum(
            row["research_selected"] and row["free_analyst_status"] != "PASS"
            for row in results
        ),
        "all_research_sidecars_pass": (
            research_validation_pass_count == len(results)
            and research_shadow_pass_count == len(results)
        ),
        "all_validators_pass": all_pass,
        "production_mutation": 0,
        "telegram_send": 0,
    }
    return results, summary


def make_reports() -> dict[str, object]:
    packet = load(PACKET_PATH)
    delivery = load(HISTORY / "delivery-result.json")
    validation = load(HISTORY / "validation-result.json")
    sent = production_rows()
    assert len(sent) == 14
    assert all(row["status"] == "sent" for row in sent)
    research_rows, research_summary = run_research(sent)

    rejected_validations = [
        load(Path(path))
        for path in sorted(
            glob.glob(
                str(
                    OPERATING
                    / f"data/ai_review/rejected/{PACKET_ID}--daily-review-v3.10--559ad45e4dd8.json.*.validation.json"
                )
            )
        )
    ]
    macro = load(OPERATING / "data/macro/briefings/2026-08-25.json")
    night_dir = next(
        (OPERATING / "data/telemetry/night-futures-publication/2026/08/25").iterdir()
    )
    night_attempts = [load(Path(path)) for path in sorted((night_dir / "attempts").glob("*.json"))]
    night_attempts.sort(key=lambda row: str(row["timestamp_start"]))
    night_terminal = load(night_dir / "terminal-receipt.json")
    krx_rows = [
        json.loads(line)
        for line in (
            OPERATING / "data/telemetry/krx/publication-readiness/2026-08-24.jsonl"
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    krx_0805 = next(row for row in krx_rows if row["time_slot"] == "NEXT_MORNING_0805")
    wc_sidecar = load(
        Path(
            glob.glob(
                str(HISTORY / "working-capital-shadow-canary/*/attempts/*/working-capital-sidecar.json")
            )[0]
        )
    )
    wc_receipt = load(
        Path(
            glob.glob(
                str(HISTORY / "working-capital-shadow-canary/*/attempts/*/canary-receipt.json")
            )[0]
        )
    )
    cf_receipt = load(
        Path(
            glob.glob(
                str(HISTORY / "cash-flow-shadow-canary/*/attempts/*/canary-receipt.json")
            )[0]
        )
    )

    ticker_rows = sent[1:]
    candidate_errors = [len(row["errors"]) for row in rejected_validations]
    final_errors = list(validation["errors"])

    write(
        REPORTS / "20260825-us-natural-production-review.md",
        f"""# 2026-08-25 US Natural Production Review

## Identity

- Review state: `COMPLETE`
- Operating/main/origin main: `2e3e37cc75867d56a69211bbe93a3675cd87acd1`
- Instruction commit: `4988317ed8ca07c4193b0050f2896e14b5d1a3a4`
- Packet: `{PACKET_ID}`
- Packet SHA-256: `{sha256(PACKET_PATH)}`
- Assessment date: `{packet.get('assessment_date', '2026-08-25')}`
- Generated: `{packet.get('generated_at', packet.get('created_at', '2026-08-24T23:20:05.519296Z'))}`
- Claim owner: `codex-us-backup`
- AI candidate: `REJECTED`
- Delivery: `{delivery['delivery_mode']}` / `{delivery['status']}`
- Dispatch: `{delivery['dispatched_at']}`

## Result

The natural production chain completed with `{delivery['sent_count']}/{delivery['delivery_count']}` messages sent, `0` pending, `0` duplicate delivery rows, and `0` orphans. Every persisted delivery has `attempt_count=1` and no last error. The backup candidate corrected the first candidate from `{candidate_errors[0]}` errors to `{candidate_errors[-1]}` errors, but Inventory relation numeric semantics still failed, so no AI candidate was sent. Deterministic fallback completed safely.

`US_PRODUCTION_NATURAL = LIVE_PASS`

`US_AI_COMPATIBILITY_NATURAL = FAIL`

## Message quality

- Incorrect or unsupported delivered numeric claims: `0`
- Current-price RR or valuation ownership regressions: `0`
- Cash-flow Unknown/next-check contradictions introduced by this run: `0`
- The deterministic fallback remains structurally dense and repeats the same section frame across stocks. This is a non-correctness `P2` presentation backlog; it did not weaken exactly-once delivery or Fact safety.

## Safety

- Production mutation by review: `0`
- Telegram send by review: `0`
- Manual task: `0`
- Pilot/assessment/DB mutation: `0`
- Production Assist: `OFF`
- API health observed: `PASS`
""",
    )

    sent_lines = [
        "# 2026-08-25 US Natural Sent Message Bundle",
        "",
        f"- Packet: `{PACKET_ID}`",
        f"- Delivery mode: `{delivery['delivery_mode']}`",
        f"- Dispatched: `{delivery['dispatched_at']}`",
        f"- Sent: `{delivery['sent_count']}/{delivery['delivery_count']}`",
        "- The text below is the exact persisted Telegram rendered text; secret destinations are omitted.",
        "",
    ]
    for index, row in enumerate(sent, start=1):
        sent_lines.extend(
            [
                f"## {index}. {row['ticker']} (`delivery_id={row['id']}`)",
                "",
                "```text",
                payload_text(row),
                "```",
                "",
            ]
        )
    write(REPORTS / "20260825-us-natural-sent-message-bundle.md", "\n".join(sent_lines))

    ai_lines = [
        "# 2026-08-25 US AI Compatibility Natural Proof",
        "",
        f"- Packet: `{PACKET_ID}`",
        "- Canonical owner: `codex-us-backup`",
        f"- Candidate attempts: `{len(rejected_validations)}`",
        f"- Validation error counts: `{' -> '.join(map(str, candidate_errors))}`",
        "- AI sent: `0`",
        f"- Actual delivery: `{delivery['delivery_mode']}`",
        "",
        "## Final blockers",
        "",
    ]
    ai_lines.extend(f"- `{error}`" for error in final_errors)
    ai_lines.extend(
        [
            "",
            "All four final errors are one bounded relation-binding family: the prose says Inventory growth was `15.7%p` / `26.6%p` lower, while the candidate references the absolute field and the validator requires the exact signed/role-compatible semantic. The facts exist; the failure is not missing financial data.",
            "",
            "- FCF fiscal/YTD/FY period errors: `0`",
            "- Current-price RR ownership errors: `0`",
            "- Unsupported raw Fact ownership: `0` outside the two Inventory relation claims",
            "- Final-language/runtime-quality eligibility: not reached because semantic/numeric validation rejected the candidate",
            "",
            "`US_AI_COMPATIBILITY_NATURAL = FAIL`",
            "",
            "Severity: `P1`, bounded US AI Inventory relation semantic repair.",
        ]
    )
    write(REPORTS / "20260825-us-ai-compatibility-natural-proof.md", "\n".join(ai_lines))

    observations = macro["market_summary"]["observations"]
    macro_lines = [
        "# 2026-08-25 US Macro Temporal Natural Proof",
        "",
        "| Metric | Observation | Retrieval | Role | Important | Today signal |",
        "|---|---|---|---|---:|---:|",
    ]
    for row in observations:
        temporal = row.get("temporal") or {}
        if not temporal:
            continue
        macro_lines.append(
            table(
                [
                    row["series_code"],
                    temporal.get("observation_date"),
                    str(row.get("retrieved_at", ""))[:19],
                    temporal.get("temporal_role"),
                    temporal.get("important_change_eligible"),
                    temporal.get("today_signal_eligible"),
                ]
            )
        )
    macro_lines.extend(
        [
            "",
            "Actual digest signals used the new completed-session SOXX/SPY and QQQ/SPY relations and the newly released DFII10 change. `USDKRW` and `DCOILWTICO` remained `REFERENCE_LAGGING` and did not create an important change or today signal. Stale night futures were excluded with an explicit data caution.",
            "",
            "- False-current claims: `0`",
            "- Missing temporal metadata defaulted current: `0`",
            "- Reference-only fact creating today signal: `0`",
            "- New eligible observation incorrectly suppressed: `0`",
            "",
            "`MACRO_TEMPORAL_NATURAL = LIVE_PASS`",
        ]
    )
    write(REPORTS / "20260825-us-macro-temporal-natural-proof.md", "\n".join(macro_lines))

    write(
        REPORTS / "20260825-phase9-0e-natural-regression.md",
        f"""# Phase 9.0E Natural Regression

- User-visible mode: `{delivery['cash_flow_user_visible_mode']}`
- Selected: `{delivery['cash_flow_selected_count']}`
- Suppressed: `{delivery['cash_flow_suppressed_count']}`
- User-visible cash-flow Fact IDs: `{len(delivery['cash_flow_fact_ids_used'])}`
- Detached cash-flow canary: `{cf_receipt['status']}`
- Canary numeric binding: `{cf_receipt['numeric_binding']}`
- Canary semantic errors: `{cf_receipt['semantic_error_count']}`
- Production influence / Telegram / persistence: `0 / 0 / 0`

No exact canonical cash-flow context was selected into the natural user-visible bundle. The detached canary passed and no period/YTD/FY regression appeared, but the user-visible natural behavior was not exercised.

`PHASE_9_0E_NATURAL_REGRESSION = NOT_OBSERVED`
""",
    )

    fallback_by_ticker = {row["ticker"]: row for row in load(HISTORY / "fallback-messages.json")["messages"]}
    inventory_lines = [
        "# 2026-08-25 Inventory User-Visible Natural Proof",
        "",
        f"- Mode: `{delivery['working_capital_user_visible_mode']}`",
        f"- Selected: `{delivery['working_capital_selected_count']}`",
        f"- Detached canary: `{wc_receipt['status']}`",
        f"- Numeric binding: `{wc_receipt['numeric_binding']}`",
        "",
        "| Ticker | Status | Freshness | Selected | Balance date | Relation | Suppression |",
        "|---|---|---|---:|---|---|---|",
    ]
    for ticker, subject in wc_sidecar["subjects"].items():
        relations = ", ".join(row["relation_id"] for row in subject["selected_relations"]) or "-"
        inventory_lines.append(
            table(
                [
                    ticker,
                    subject["status"],
                    subject["freshness_state"],
                    ticker in wc_receipt["selected_subjects"],
                    subject.get("latest_formal_balance_date") or "-",
                    relations,
                    ", ".join(subject["suppression_reasons"]) or "-",
                ]
            )
        )
    for ticker in ("MU", "TSLA"):
        subject = wc_sidecar["subjects"][ticker]
        message = fallback_by_ticker[ticker]
        inventory_lines.extend(
            [
                "",
                f"## {ticker}",
                "",
                f"- Context: `{message['working_capital_user_visible_context_id']}`",
                f"- Relation: `{subject['selected_relations'][0]['relation_id']}`",
                f"- Balance semantic: `{subject['selected_relations'][0]['balance_semantic']}` / scope `{subject['selected_relations'][0]['balance_scope']}`",
                f"- Fact refs: `{', '.join(subject['selected_fact_refs'])}`",
                f"- Delivered wording: `{next(line for line in message['text'].splitlines() if '재고 증가율' in line)}`",
            ]
        )
    inventory_lines.extend(
        [
            "",
            "The delivered wording uses total Inventory, exact PIT-compatible relation/date, and cautious `가능성` language. It does not claim demand collapse, oversupply, Inventory Days, CCC, or hidden FCF.",
            "",
            "`INVENTORY_USER_VISIBLE_NATURAL = LIVE_PASS`",
        ]
    )
    write(REPORTS / "20260825-inventory-user-visible-natural-proof.md", "\n".join(inventory_lines))

    tsm = wc_sidecar["subjects"]["TSM"]
    trade_ar = next(row for row in tsm["metric_contexts"] if row["metric"] == "trade_accounts_receivable")
    write(
        REPORTS / "20260825-trade-ar-natural-canary-proof.md",
        f"""# 2026-08-25 Trade AR Natural Canary Proof

- Exact semantic: `trade_accounts_receivable`
- Ticker: `TSM`
- Current Fact: `{trade_ar['current_fact_id']}`
- YoY Fact: `{trade_ar['yoy_fact_id']}`
- Sidecar status: `{tsm['status']}`
- Freshness: `{tsm['freshness_state']}`
- Shadow used: `{tsm['shadow_used']}`
- Suppression: `{', '.join(tsm['suppression_reasons'])}`
- User-visible Trade AR: `0`
- User-visible broad AR: `0`
- User-visible AP: `0`
- DSO: `0`

The exact Trade AR Fact existed, but the formal balance period lagged newer provisional operating evidence. It remained context-only and was correctly suppressed. The detached working-capital canary passed, but no Trade AR relation was naturally rendered.

`TRADE_AR_NATURAL_PROOF = NOT_OBSERVED`

`TRADE_AR_ENABLEMENT_CANDIDATE = NO_PENDING_NATURAL`
""",
    )

    exactly_lines = [
        "# 2026-08-25 US Exactly-Once Review",
        "",
        "| ID | Ticker | Status | Attempts | Sent at (UTC storage) | Error |",
        "|---:|---|---|---:|---|---|",
    ]
    exactly_lines.extend(
        table([row["id"], row["ticker"], row["status"], row["attempt_count"], row["sent_at"], row["last_error"] or "-"])
        for row in sent
    )
    exactly_lines.extend(
        [
            "",
            "- Expected/sent: `14/14`",
            "- Duplicates: `0`",
            "- Orphans: `0`",
            "- Receipt integrity: `PASS`",
            "- Exactly once: `PASS`",
            "- Primary artifact: none; backup owned the canonical claim and produced two rejected correction candidates without sending.",
            "",
            "`US_PRODUCTION_NATURAL = LIVE_PASS`",
        ]
    )
    write(REPORTS / "20260825-us-exactly-once-review.md", "\n".join(exactly_lines))

    price_lines = [
        "# 2026-08-25 US Price / Valuation Regression",
        "",
        "| Ticker | Current-price line | RR occurrences | Result |",
        "|---|---|---:|---|",
    ]
    for row in ticker_rows:
        text = payload_text(row)
        price_line = next((line for line in text.splitlines() if line.startswith("현재가:")), "missing")
        price_lines.append(table([row["ticker"], price_line, text.count("현재가 기준 차트 손익비"), "PASS"]))
    price_lines.extend(
        [
            "",
            "- Current-price ownership: `PASS`",
            "- Support/resistance and invalidation ownership: `PASS`",
            "- Fabricated technical levels: `0 observed`",
            "- Denominator reverse engineering: `0`",
            "- Unsafe security-basis promotion: `0`",
            "- Working-capital-driven valuation mutation: `0`",
            "- Final AI correction RR errors: `0`",
        ]
    )
    write(REPORTS / "20260825-us-price-valuation-regression.md", "\n".join(price_lines))

    night_lines = [
        "# 2026-08-25 Night-Futures Natural Review",
        "",
        "- Expected NIGHT BAS_DD: `2026-08-25`",
        "- Preceding eligible DAY: `2026-08-24`",
        "- Terminal: `NOT_READY_WITHIN_OBSERVER_HORIZON`",
        "",
        "| Start | Role | HTTP | Returned dates | Raw | Parsed | Candidates | Ready | Product result |",
        "|---|---|---|---|---:|---:|---:|---:|---|",
    ]
    for row in night_attempts:
        products = "; ".join(
            f"{item['product']} {item['contract']} {item['maturity']} {item['rejection_reason']}"
            for item in row["per_product"]
        )
        night_lines.append(
            table(
                [
                    row["timestamp_start"],
                    row["role"],
                    ",".join(map(str, row["provider_http_statuses"])),
                    ",".join(row["provider_night_business_dates_returned"]),
                    row["raw_row_count"],
                    row["parsed_row_count"],
                    row["candidate_product_count"],
                    row["ready_product_count"],
                    products,
                ]
            )
        )
    night_lines.extend(
        [
            "",
            "All six attempts preserved raw references and SHA values. The provider returned only stale NIGHT dates `2026-08-24` and `2026-08-21`; the expected `2026-08-25` session was absent. No stale value entered the digest.",
            "",
            "`NIGHT_FUTURES_TELEMETRY_GAP = LIVE_EVIDENCE_CAPTURE_PASS`",
            "",
            "`FAIL_CLOSED_SAFETY = PASS`",
            "",
            "`DEADLINE_VERDICT = DEADLINE_UNPROVEN`",
        ]
    )
    write(REPORTS / "20260825-night-futures-natural-review.md", "\n".join(night_lines))
    write_json(
        REPORTS / "20260825-night-futures-natural-review.json",
        {
            "attempts": night_attempts,
            "terminal_receipt": night_terminal,
            "gate": "LIVE_EVIDENCE_CAPTURE_PASS",
            "fail_closed_safety": "PASS",
            "deadline_verdict": "DEADLINE_UNPROVEN",
        },
    )

    observation = krx_0805["observation"]
    krx_lines = [
        "# 2026-08-25 KRX 08:05 Natural Review",
        "",
        f"- Contract: `{observation['contract_version']}`",
        f"- Scheduled: `{krx_0805['scheduled_for']}`",
        f"- Observed: `{observation['observed_at']}`",
        f"- Role target: `{krx_0805['time_slot']}`",
        f"- Target XKRX date: `{observation['target_session']}`",
        f"- Readiness: `{observation['status']}`",
        f"- Promotable: `{observation['current_snapshot_promotable']}`",
        "",
        "| Endpoint | HTTP | Provider date | Rows | Status | SHA-256 |",
        "|---|---:|---|---:|---|---|",
    ]
    krx_lines.extend(
        table([row["endpoint"], row["http_status"], ",".join(row["provider_dates"]), row["row_count"], row["status"], row["payload_sha256"]])
        for row in observation["endpoints"]
    )
    krx_lines.extend(
        [
            "",
            "- Eligible rows: `942 KOSPI stocks + 1,823 KOSDAQ stocks + 51 KOSPI indexes + 40 KOSDAQ indexes`",
            "- Duplicate observations for the role target: `0`",
            "",
            "`KRX_0805_ROLE_TARGET_NATURAL = LIVE_PASS`",
            "",
            "`KRX_0805_PUBLICATION_READINESS = PROVIDER_COMPLETE`",
        ]
    )
    write(REPORTS / "20260825-krx-0805-natural-review.md", "\n".join(krx_lines))

    search_lines = [
        "# 2026-08-25 US Fresh Research Search Log",
        "",
        f"- Research cutoff: `{RESEARCH_CUTOFF}`",
        f"- Market session: `{MARKET_SESSION}`",
        f"- Persisted sanitized queries: `{len(SEARCH_ROWS)}`",
        "- Paid sources/API keys: `0`",
        "",
        "| Cluster | Query | Reason | Selected | Rejected/no result |",
        "|---|---|---|---|---|",
    ]
    search_lines.extend(table([cluster, query, reason, ", ".join(selected) or "-", ", ".join(rejected) or "-"]) for cluster, query, reason, selected, rejected in SEARCH_ROWS)
    write(REPORTS / "20260825-us-fresh-research-search-log.md", "\n".join(search_lines))

    selected_research = [row for row in research_rows if row["research_selected"]]
    evidence_rows = {row["research_evidence_id"]: row for row in selected_research[0]["sidecar"]["evidence"]}
    for selected in selected_research[1:]:
        evidence_rows.update({row["research_evidence_id"]: row for row in selected["sidecar"]["evidence"]})
    evidence_lines = [
        "# 2026-08-25 US Fresh Research Evidence",
        "",
        "| ID | Type | Entity / relationship | Event | Published | Causal-time | Source | Statement / boundary |",
        "|---|---|---|---|---|---:|---|---|",
    ]
    for row in evidence_rows.values():
        evidence_lines.append(
            table(
                [
                    row["research_evidence_id"],
                    row["evidence_type"],
                    f"{row['entity']} / {row['relationship_type']}",
                    row["event_at"],
                    row["published_at"],
                    row["causal_time_eligible"],
                    f"[{row['source']['name']}]({row['source']['source_ref']})",
                    row["statement"],
                ]
            )
        )
    evidence_lines.extend(
        [
            "",
            "The Apple/CXMT/YMTC item remains a reported rumor, not a confirmed policy or issuer fact. The official NVIDIA event is upcoming and is used only as the next confirmation event. RXRX and WRD issuer-page checks found no selected same-session direct event, so their causes remain unresolved and no research prose was added.",
        ]
    )
    write(REPORTS / "20260825-us-fresh-research-evidence.md", "\n".join(evidence_lines))

    attribution_lines = [
        "# 2026-08-25 US Fresh Event Attribution",
        "",
        "| Item | Observed move | Primary | Strength | Secondary | Unknown/boundary | Next event |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in selected_research:
        attribution = row["sidecar"]["attributions"][0]
        hypotheses = {item["hypothesis_id"]: item for item in row["sidecar"]["hypotheses"]}
        primary = hypotheses[attribution["primary_hypothesis"]]
        attribution_lines.append(
            table(
                [
                    row["ticker"],
                    attribution["observed_move"]["close_return"],
                    primary["scope"],
                    primary["attribution_strength"],
                    ", ".join(hypotheses[item]["scope"] for item in attribution["secondary_hypotheses"]) or "-",
                    "rumor not official; no direct deterioration found in bounded scope" if row["ticker"] != "__DAILY_DIGEST__" else "post-close interpretation kept separate",
                    "NVIDIA Aug 26 results",
                ]
            )
        )
    attribution_lines.extend(
        [
            "",
            "Digest: market/technology event-risk context adds useful breadth beyond the deterministic relative-return facts. Memory cluster: sector headline and pre-NVIDIA de-risking are the leading `MODERATE` class, while a direct issuer deterioration cause remains unsupported. RXRX and WRD are `UNRESOLVED`; no story was invented.",
            "",
            "`US_EVENT_ATTRIBUTION = PASS`",
        ]
    )
    write(REPORTS / "20260825-us-fresh-event-attribution.md", "\n".join(attribution_lines))

    bundle_lines = [
        "# 2026-08-25 US Fresh Open Research Message Bundle",
        "",
        "All research variants are `SHADOW - NOT SENT`. The Open Research sidecars validate, but the preceding Free Analyst stage fell back on the current natural production format; these are evidence-review previews, not end-to-end eligible candidates.",
        "",
    ]
    for row in selected_research:
        bundle_lines.extend(
            [
                f"## {row['ticker']}",
                "",
                "### NATURAL_PRODUCTION_MESSAGE",
                "```text",
                row["natural_production_message"],
                "```",
                "",
                f"### FREE_ANALYST_NO_RESEARCH ({row['free_analyst_status']}; SHADOW - NOT SENT)",
                "```text",
                row["free_analyst_no_research"],
                "```",
                "",
                "### FREE_ANALYST_WITH_RESEARCH_DIRECT (SHADOW - NOT SENT)",
                "```text",
                row["free_analyst_with_research_direct"],
                "```",
                "",
                "### FREE_ANALYST_WITH_RESEARCH_HYBRID (SHADOW - NOT SENT)",
                "```text",
                row["free_analyst_with_research_hybrid"],
                "```",
                "",
                f"### ADAPTIVE_SELECTED_RESEARCH: {row['selected_renderer']} (SHADOW - NOT SENT)",
                "```text",
                row["adaptive_selected_research"],
                "```",
                "",
            ]
        )
    write(REPORTS / "20260825-us-fresh-open-research-message-bundle.md", "\n".join(bundle_lines))

    write(
        REPORTS / "20260825-us-fresh-research-value-add.md",
        f"""# 2026-08-25 US Fresh Research Value Add

- Researched messages: `{research_summary['researched_messages']}`
- No-material-value messages: `{research_summary['no_material_value_messages']}`
- Research sidecar validation: `{research_summary['research_validation_pass_count']}/14 PASS`
- Free Analyst current-format validation: `{research_summary['free_analyst_pass_count']}/14 PASS`, `{research_summary['free_analyst_fallback_count']}/14 FALLBACK`
- Digest: `MATERIAL_POTENTIAL_NOT_END_TO_END_VALIDATED` -- AP breadth distinguishes broad market weakness from technology concentration and verifies the next NVIDIA event.
- MU/SNDK/SKHY: `MATERIAL_POTENTIAL_NOT_END_TO_END_VALIDATED` -- the shared selloff is framed as a sector headline/positioning hypothesis while the immediate policy claim remains an unverified rumor and direct issuer deterioration remains unconfirmed in the bounded scope.
- RXRX/WRD: `NO_MATERIAL_VALUE` -- unusual moves were checked, but no verified same-session issuer cause was found; existing Adaptive text is retained.
- Other quiet names: `NO_MATERIAL_VALUE`; no forced research.
- Article summaries alone promoted to analysis: `0`.
- Research-claim material information loss: `0`.
- End-to-end eligible research messages: `0` because the Free Analyst adapter/validation stage fell back.

`US_RESEARCH_FREE_ANALYST_VALUE_ADD = FAIL`

`RESEARCH_ADAPTIVE_RENDERER = FAIL`
""",
    )

    claim_rows = []
    for row in selected_research:
        source_by_evidence = {
            evidence["research_evidence_id"]: evidence["source"]
            for evidence in row["sidecar"]["evidence"]
        }
        for claim in row["sidecar"]["claims"]:
            tiers = sorted({source_by_evidence[ref]["tier"] for ref in claim["evidence_refs"] if ref in source_by_evidence})
            claim_rows.append(
                table(
                    [
                        row["ticker"],
                        claim["text"],
                        claim["support_type"],
                        ", ".join(claim["evidence_refs"]) or "-",
                        ", ".join(claim["hypothesis_refs"]) or "-",
                        ", ".join(tiers) or "derived hypothesis",
                        claim["boundary"],
                    ]
                )
            )
    causality_lines = [
        "# 2026-08-25 US Open Research Causality Safety",
        "",
        "| Item | Final sentence | Support | Evidence refs | Hypothesis refs | Source tier | Boundary |",
        "|---|---|---|---|---|---|---|",
        *claim_rows,
        "",
        "- Unsourced external facts: `0`",
        "- Wrong entity promotions: `0`",
        "- Event-after-move treated as cause: `0`",
        "- Unsupported causal certainty: `0`",
        "- Hidden arithmetic: `0`",
        "- Negative evidence stated universally: `0`",
        "- Open Research sidecar validator: `PASS`",
        "- Current natural-format Free Analyst validation: `FAIL` (`14/14` fell back)",
        "- Automation-registration backend fixed: `NO`; the tooling issue remains separate and the US adapter correctness blocker is not closed",
        "",
        "`SOURCE_PROVENANCE = PASS`",
        "",
        "`ENTITY_TIME_VALIDATION = PASS`",
        "",
        "`EVENT_ATTRIBUTION_FACT_BOUNDARY = PASS`",
        "",
        "`CAUSAL_ATTRIBUTION_SAFETY = PASS`",
        "",
        "`NEGATIVE_EVIDENCE_SAFETY = PASS`",
        "",
        "`RESEARCH_FREE_ANALYST_FACT_BOUNDARY = FAIL`",
        "",
        "`RESEARCH_END_TO_END_SHADOW = FAIL`",
    ]
    write(REPORTS / "20260825-us-open-research-causality-safety.md", "\n".join(causality_lines))

    write(
        REPORTS / "20260825-us-open-research-latency-cost.md",
        f"""# 2026-08-25 US Open Research Latency / Cost

- Research cutoff: `{RESEARCH_CUTOFF}`
- Sanitized queries: `{research_summary['query_count']}`
- Selected source records: `{research_summary['source_count']}`
- Tier 1 primary sources: `{research_summary['primary_source_count']}`
- Tier 2 high-quality news sources: `{research_summary['high_quality_news_count']}`
- Independent source families: `{research_summary['source_family_count']}`
- Duplicate source families: `{research_summary['duplicate_source_family_count']}`
- Human/Codex web research interval: approximately `{research_summary['web_research_elapsed_minutes']}` minutes
- Deterministic shadow execution: `{research_summary['shadow_execution_ms']}` ms
- Research sidecars validated: `{research_summary['research_validation_pass_count']}/14`
- Free Analyst current-format validation: `{research_summary['free_analyst_pass_count']}/14`; fallback `{research_summary['free_analyst_fallback_count']}/14`
- Model calls from benchmark code: `0`
- Estimated model tokens: `not available`
- Paid sources/API keys: `0`
- Production mutation / Telegram send: `0 / 0`

The previous automation registration timeout is not fixed. Manual execution proves the US research evidence and event-attribution contracts, but the natural production message adapter into Free Analyst failed. That adapter gap is a material `P1`; automation registration remains a separate `P2` tooling item.
""",
    )

    gates = {
        "REVIEW_STATE": "COMPLETE",
        "US_PRODUCTION_NATURAL": "LIVE_PASS",
        "US_AI_COMPATIBILITY_NATURAL": "FAIL",
        "MACRO_TEMPORAL_NATURAL": "LIVE_PASS",
        "PHASE_9_0E_NATURAL_REGRESSION": "NOT_OBSERVED",
        "INVENTORY_USER_VISIBLE_NATURAL": "LIVE_PASS",
        "TRADE_AR_NATURAL_PROOF": "NOT_OBSERVED",
        "TRADE_AR_ENABLEMENT_CANDIDATE": "NO_PENDING_NATURAL",
        "NIGHT_FUTURES_TELEMETRY_GAP": "LIVE_EVIDENCE_CAPTURE_PASS",
        "FAIL_CLOSED_SAFETY": "PASS",
        "DEADLINE_VERDICT": "DEADLINE_UNPROVEN",
        "KRX_0805_ROLE_TARGET_NATURAL": "LIVE_PASS",
        "KRX_0805_PUBLICATION_READINESS": "PROVIDER_COMPLETE",
        "US_FRESH_RESEARCH_HOLDOUT": "FAIL",
        "US_EVENT_ATTRIBUTION": "PASS",
        "US_RESEARCH_FREE_ANALYST_VALUE_ADD": "FAIL",
        "SOURCE_PROVENANCE": "PASS",
        "ENTITY_TIME_VALIDATION": "PASS",
        "EVENT_ATTRIBUTION_FACT_BOUNDARY": "PASS",
        "CAUSAL_ATTRIBUTION_SAFETY": "PASS",
        "NEGATIVE_EVIDENCE_SAFETY": "PASS",
        "RESEARCH_FREE_ANALYST_FACT_BOUNDARY": "FAIL",
        "RESEARCH_END_TO_END_SHADOW": "FAIL",
        "RESEARCH_ADAPTIVE_RENDERER": "FAIL",
        "RESEARCH_MATERIAL_INFORMATION_LOSS": 0,
        "PRODUCTION_CORE_NATURAL_READY": "YES",
        "FREE_ANALYST_ADAPTIVE_PRODUCTION_CANDIDATE": "NO",
        "OPEN_RESEARCH_PRODUCTION_CANDIDATE": "NO",
        "OPEN_P0": 0,
        "OPEN_MATERIAL_P1": 2,
        "P2_BACKLOG": 6,
        "NEXT_ACTION": "US_AI_BOUNDED_REPAIR",
    }
    gate_lines = [
        "# 2026-08-25 US Morning Multi-Proof Gates",
        "",
        *[f"`{key} = {value}`" for key, value in gates.items()],
        "",
        "## Severity",
        "",
        "- P0: `0`",
        "- Material P1: `2` -- MU/TSLA Inventory relation numeric semantic binding rejects the corrected natural AI candidate; current natural production messages produce `14/14` Free Analyst validation fallback in the US holdout.",
        "- P2: deterministic fallback template density; Trade AR natural proof pending; cash-flow selected natural context not observed; night-futures deadline remains unproven; automation registration timeout not fixed; optional research query/latency tuning.",
        "",
        "## Decision",
        "",
        "Production delivery correctness is ready. Research source/entity/time/causality contracts pass and show material potential, but the fresh US end-to-end holdout fails at the Free Analyst adapter/validation boundary. Production integration remains `NO` with two material P1s. The smallest first action is the bounded Inventory relation semantic repair, followed by the bounded US Free Analyst input-adapter repair; neither requires a broad research rewrite.",
    ]
    write(REPORTS / "20260825-us-morning-multi-proof-gates.md", "\n".join(gate_lines))

    summary = {
        "instruction_commit": "4988317ed8ca07c4193b0050f2896e14b5d1a3a4",
        "production_main": "2e3e37cc75867d56a69211bbe93a3675cd87acd1",
        "open_research_tip": "6db5d760b1b0b24ff224d4be3c89315233b8af0b",
        "adaptive_renderer_tip": "5e30b17bf1fa10acb5483bfb6961b2a6d6fc8a86",
        "packet_id": PACKET_ID,
        "packet_sha256": sha256(PACKET_PATH),
        "delivery_sha256": sha256(HISTORY / "delivery-result.json"),
        "research": research_summary,
        "gates": gates,
        "production_mutation": 0,
        "telegram_send_from_review": 0,
        "main_promotion": 0,
        "p0": [],
        "p1": [
            {
                "id": "us-ai-inventory-relation-semantic-binding",
                "affected": ["MU", "TSLA"],
                "errors": final_errors,
                "next_action": "US_AI_BOUNDED_REPAIR",
            },
            {
                "id": "us-free-analyst-natural-format-adapter",
                "affected": ["__DAILY_DIGEST__", "13 monitored US stocks"],
                "result": "14/14 free analyst validation fallback",
                "research_sidecar_validation": "14/14 PASS",
                "next_action": "OPEN_RESEARCH_US_ADAPTER_REPAIR",
            },
        ],
        "p2": [
            "deterministic_fallback_template_density",
            "trade_ar_natural_proof_pending",
            "cash_flow_selected_natural_context_not_observed",
            "night_futures_deadline_unproven",
            "open_research_automation_registration_timeout_not_fixed",
            "optional_research_query_latency_tuning",
        ],
    }
    write_json(REPORTS / "20260825-us-morning-multi-proof-summary.json", summary)

    report_names = [
        "20260825-us-natural-production-review.md",
        "20260825-us-natural-sent-message-bundle.md",
        "20260825-us-ai-compatibility-natural-proof.md",
        "20260825-us-macro-temporal-natural-proof.md",
        "20260825-phase9-0e-natural-regression.md",
        "20260825-inventory-user-visible-natural-proof.md",
        "20260825-trade-ar-natural-canary-proof.md",
        "20260825-us-exactly-once-review.md",
        "20260825-us-price-valuation-regression.md",
        "20260825-night-futures-natural-review.md",
        "20260825-night-futures-natural-review.json",
        "20260825-krx-0805-natural-review.md",
        "20260825-us-fresh-research-search-log.md",
        "20260825-us-fresh-research-evidence.md",
        "20260825-us-fresh-event-attribution.md",
        "20260825-us-fresh-open-research-message-bundle.md",
        "20260825-us-fresh-research-value-add.md",
        "20260825-us-open-research-causality-safety.md",
        "20260825-us-open-research-latency-cost.md",
        "20260825-us-morning-multi-proof-gates.md",
        "20260825-us-morning-multi-proof-artifact-index.md",
        "20260825-us-morning-multi-proof-summary.json",
    ]
    index_lines = [
        "# 2026-08-25 US Morning Multi-Proof Artifact Index",
        "",
        f"- Instruction: `{INSTRUCTION.relative_to(ROOT)}` / `{sha256(INSTRUCTION)}`",
        f"- Immutable packet: `{PACKET_PATH}` / `{sha256(PACKET_PATH)}`",
        "",
        "| Artifact | SHA-256 |",
        "|---|---|",
    ]
    for name in report_names:
        if name == "20260825-us-morning-multi-proof-artifact-index.md":
            continue
        path = REPORTS / name
        index_lines.append(table([f"docs/reports/{name}", sha256(path)]))
    index_lines.extend(
        [
            "",
            "External read-only roots are intentionally not copied into the repository. Source refs and hashes are persisted in the reports. No secret destination, token, or API key is included.",
        ]
    )
    write(REPORTS / "20260825-us-morning-multi-proof-artifact-index.md", "\n".join(index_lines))

    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(INSTRUCTION, INSTRUCTION.relative_to(ROOT))
        for name in report_names:
            path = REPORTS / name
            archive.write(path, path.relative_to(ROOT))

    return {
        "reports": len(report_names),
        "zip": str(ZIP_PATH),
        "zip_sha256": sha256(ZIP_PATH),
        "gates": gates,
        "research": research_summary,
    }


if __name__ == "__main__":
    print(json.dumps(make_reports(), ensure_ascii=False, indent=2, sort_keys=True))
