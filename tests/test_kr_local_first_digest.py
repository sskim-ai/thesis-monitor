from copy import deepcopy
from datetime import date

from app.services.daily_digest import (
    DailyDigest,
    DataQualitySummary,
    MacroInterpretation,
    PortfolioSummary,
    ScheduleSummary,
)
from app.services.daily_digest_renderer import render_daily_digest
from app.services.free_analyst_production_integration_service import (
    build_production_candidate,
)
from app.services.kr_close_fx import KrCloseFxItem, KrCloseFxSummary
from app.services.kr_market_digest_quality_service import (
    build_kr_market_digest_plan,
)


def _run40_style_context() -> dict[str, object]:
    return {
        "contract_version": "market-context-adapter-v1",
        "market": "KR",
        "assessment_date": "2026-08-26",
        "session_date": "2026-08-26",
        "as_of": "2026-08-26T17:10:00+09:00",
        "cutoff": "2026-08-26T17:10:00+09:00",
        "indices": [
            {
                "symbol": "KOSPI",
                "name": "KOSPI",
                "close": 6808.21,
                "return_pct": 0.97,
                "basis": "official_or_provider_index",
                "as_of_date": "2026-08-26",
                "source_ref": "kiwoom:index:kospi",
            },
            {
                "symbol": "KOSDAQ",
                "name": "KOSDAQ",
                "close": 826.87,
                "return_pct": -0.03,
                "basis": "official_or_provider_index",
                "as_of_date": "2026-08-26",
                "source_ref": "kiwoom:index:kosdaq",
            },
        ],
        "breadth": {
            "availability": "AVAILABLE",
            "advancers": 1492,
            "decliners": 983,
            "unchanged": 158,
            "eligible_count": 2633,
            "breadth_ratio": 0.6028,
            "source_refs": ["breadth:all"],
        },
        "breadth_by_scope": [
            {
                "scope": "KOSPI",
                "breadth": {
                    "availability": "AVAILABLE",
                    "advancers": 585,
                    "decliners": 275,
                    "unchanged": 47,
                    "eligible_count": 907,
                    "breadth_ratio": 0.6802,
                    "source_refs": ["breadth:kospi"],
                },
            },
            {
                "scope": "KOSDAQ",
                "breadth": {
                    "availability": "AVAILABLE",
                    "advancers": 907,
                    "decliners": 708,
                    "unchanged": 111,
                    "eligible_count": 1726,
                    "breadth_ratio": 0.5616,
                    "source_refs": ["breadth:kosdaq"],
                },
            },
        ],
        "size_context": [
            {
                "name": name,
                "return_pct": value,
                "basis": "official_size_index",
                "as_of_date": "2026-08-26",
                "source_ref": f"size:{name}",
            }
            for name, value in (("대형주", 0.93), ("중형주", 1.69), ("소형주", 0.70))
        ],
        "sectors": [
            {
                "name": name,
                "return_pct": value,
                "basis": "actual_sector_breadth",
                "source_ref": f"sector:{scope}:{name}",
                "market_scope": scope,
                "listed_count": listed,
            }
            for scope, name, value, listed in (
                ("KOSPI", "보험", 5.88, 12),
                ("KOSPI", "운송/창고", -2.66, 20),
                ("KOSDAQ", "금속", 2.87, 65),
                ("KOSDAQ", "통신", -0.93, 8),
                ("KOSDAQ", "빈 업종", 20.0, 0),
            )
        ],
        "market_flows": [
            {
                "participant": actor,
                "net_flow": amount,
                "unit": "KRW",
                "scope": scope,
                "as_of_date": "2026-08-26",
                "source_ref": f"kiwoom:ka10051:{scope}:{actor}",
            }
            for scope, actor, amount in (
                ("KOSPI", "foreign", 111_500_000_000),
                ("KOSPI", "institution", 818_100_000_000),
                ("KOSPI", "retail", -2_503_000_000_000),
                ("KOSDAQ", "foreign", -129_600_000_000),
                ("KOSDAQ", "institution", -108_700_000_000),
                ("KOSDAQ", "retail", 233_300_000_000),
            )
        ],
        "concentration": [],
        "deterministic_relations": [],
        "session_context": {
            "role": "after_hours",
            "assessment_state": "final",
            "market_date": "2026-08-26",
            "latest_completed_regular_session_date": "2026-08-26",
            "timezone": "Asia/Seoul",
            "provider_publication_state": "PROVIDER_COMPLETE",
        },
        "data_gaps": [],
    }


def _digest(plan: object | None) -> DailyDigest:
    return DailyDigest(
        digest_date=date(2026, 8, 26),
        market_scope="kr",
        macro=MacroInterpretation(
            regime_label="혼합",
            confidence=0.8,
            one_line="직전 미국 성장주 약세는 국내 장의 보조 배경입니다.",
            key_changes=["미국 반도체 상대 약세가 이어졌습니다."],
            axis_explanations=[],
            integrated_view=["• 국내 종목 영향은 별도로 확인합니다."],
            market_assumptions=[],
        ),
        portfolio=PortfolioSummary(
            thesis_counts={
                "strengthened": 0,
                "maintained": 7,
                "weakened": 0,
                "invalidated": 0,
            },
            valuation_counts={
                "expansion": 0,
                "neutral": 7,
                "mixed": 0,
                "compression": 0,
                "unknown": 0,
            },
            tickers=[],
            focus_tickers=[],
        ),
        schedule=ScheduleSummary(),
        data_quality=DataQualitySummary(),
        kr_close_fx=KrCloseFxSummary(
            items=[
                KrCloseFxItem(
                    series_code="USDKRW_KR_CLOSE",
                    label="원/달러",
                    value=1390.0,
                )
            ]
        ),
        kr_market_digest_plan=plan,
    )


def test_run40_local_first_plan_uses_all_material_local_layers() -> None:
    plan = build_kr_market_digest_plan(_run40_style_context())

    assert plan.richness.status is True
    assert "KOSPI는 상승" in plan.judgment.text
    assert "KOSDAQ은 하락" in plan.judgment.text
    assert "두 시장 모두 상승 종목이 하락 종목보다 많았습니다" in plan.judgment.text
    assert "외국인은 KOSPI에서 순매수하고 KOSDAQ에서 순매도" in plan.interpretation.text
    assert "기관은 KOSPI에서 순매수하고 KOSDAQ에서 순매도" in plan.interpretation.text
    assert "개인은 KOSPI에서 순매도하고 KOSDAQ에서 순매수" in plan.interpretation.text
    assert "• KOSPI: 대형 +0.93% · 중형 +1.69% · 소형 +0.70%" in plan.size_context.text
    assert "업종 상대 강세\n• KOSPI: 보험 +5.88%\n• KOSDAQ: 금속 +2.87%" in plan.sector_context.text
    assert "업종 상대 약세\n• KOSPI: 운송·창고 -2.66%\n• KOSDAQ: 통신 -0.93%" in plan.sector_context.text
    assert "빈 업종" not in plan.sector_context.text
    assert plan.concentration_scopes_used == ()


def test_renderer_places_local_structure_before_fx_and_global_context() -> None:
    plan = build_kr_market_digest_plan(_run40_style_context())
    rendered = render_daily_digest(_digest(plan), include_stock_details=False)

    ordered = [
        "📍 국내 장마감 구조",
        "KOSPI는 상승",
        "외국인은 KOSPI에서 순매수하고 KOSDAQ에서 순매도",
        "📊 시장 내부",
        "규모별\n• KOSPI: 대형 +0.93%",
        "업종 상대 강세",
        "💱 환율",
        "🌐 보조 시장환경",
        "현재 환경: 혼합",
        "직전 미국 성장주 약세는 국내 장의 보조 배경입니다.",
    ]
    positions = [rendered.index(value) for value in ordered]
    assert positions == sorted(positions)


def test_ai_and_fallback_share_exact_market_internal_layout() -> None:
    context = _run40_style_context()
    plan = build_kr_market_digest_plan(context, sector_rank_limit=3)
    fallback = render_daily_digest(_digest(plan), include_stock_details=False)
    source = """🤖 AI 보조 한국시장 마감 · KR Pilot 4/5

🎯 판단
KOSPI와 KOSDAQ의 지수 방향이 달랐습니다.

🔎 핵심 근거
외국인과 기관의 양 시장 수급 방향이 엇갈렸습니다.

📌 다음 확인
• 양 시장의 수급 방향을 확인합니다.
"""
    candidate = build_production_candidate(
        source,
        deterministic_text=fallback,
        message_key="market:kr-linebreak-formatting",
        market="kr",
        packet_owner="packet:kr-linebreak-formatting",
        is_market_digest=True,
        market_context={"adapter_context": context},
    )

    assert candidate.eligible is True
    assert plan.size_context is not None
    assert plan.sector_context is not None
    expected = (
        f"📊 시장 내부\n\n{plan.size_context.text}\n\n"
        f"{plan.sector_context.text}"
    )
    assert expected in fallback
    assert expected in candidate.candidate_text
    assert fallback.count(expected) == 1
    assert candidate.candidate_text.count(expected) == 1
    assert "규모별:" not in candidate.candidate_text
    assert "업종 상대 강세:" not in candidate.candidate_text
    assert "업종 상대 약세:" not in candidate.candidate_text
    assert "• •" not in candidate.candidate_text


def test_missing_local_context_preserves_safe_existing_digest_path() -> None:
    plan = build_kr_market_digest_plan(None)
    rendered = render_daily_digest(_digest(plan), include_stock_details=False)

    assert plan.richness.status is False
    assert "📍 국내 장마감 구조" not in rendered
    assert rendered.index("💱 환율") < rendered.index("현재 환경: 혼합")


def test_completed_indices_and_scoped_breadth_are_sufficient_local_minimum() -> None:
    context = deepcopy(_run40_style_context())
    context["market_flows"] = []
    context["size_context"] = []
    context["sectors"] = []

    plan = build_kr_market_digest_plan(context)

    assert plan.richness.status is True
    assert plan.richness.supporting_local_context == ()
    assert plan.judgment is not None
    assert "두 시장 모두 상승 종목이 하락 종목보다 많았습니다" in plan.judgment.text
    assert plan.interpretation is not None
    assert "전면적 위험선호" in plan.interpretation.text
