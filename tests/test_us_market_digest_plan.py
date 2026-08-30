from __future__ import annotations

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
from app.services.us_market_digest_plan_service import (
    DigestOmissionReason,
    UsMarketDigestPlan,
    UsMarketDigestSlot,
    build_us_market_digest_plan,
)


def _fact(
    symbol: str,
    fact_type: str,
    return_pct: float | None,
    *,
    label: str,
    temporal_role: str = "CURRENT_OBSERVATION",
) -> dict[str, object]:
    fields: dict[str, object] = {
        "series_code": symbol,
        "label": label,
        "temporal_role": temporal_role,
        "today_signal_eligible": temporal_role == "CURRENT_OBSERVATION",
        "structured_state": (
            "CURRENT_DIRECTIONAL" if return_pct is not None else "CURRENT_LEVEL_ONLY"
        ),
    }
    if return_pct is not None:
        fields["return_pct"] = return_pct
    return {
        "fact_id": f"market:{fact_type.removeprefix('market_')}:{symbol}",
        "fact_type": fact_type,
        "as_of_date": "2026-08-26",
        "fields": fields,
    }


def run41_market_context() -> dict[str, object]:
    facts = [
        _fact("SPY", "market_index", 0.0222, label="S&P500"),
        _fact("QQQ", "market_index", 0.0915, label="Nasdaq"),
        _fact("IWM", "market_index", -0.1003, label="Russell 2000"),
        _fact("SOXX", "market_sector", 0.2607, label="반도체"),
        _fact("RSP", "market_style", 0.1533, label="S&P500 동일가중"),
        _fact("XLI", "market_sector", 1.0874, label="산업재"),
        _fact("XLV", "market_sector", -0.9983, label="헬스케어"),
        _fact("XLC", "market_sector", None, label="커뮤니케이션 서비스"),
        {
            "fact_id": "market:real_yield:DFII10",
            "fact_type": "market_real_yield",
            "as_of_date": "2026-08-25",
            "fields": {
                "series_code": "DFII10",
                "label": "미국 10년물 실질금리",
                "change_bp": -6.0,
                "temporal_role": "REFERENCE_LAGGING",
                "today_signal_eligible": False,
                "structured_state": "REFERENCE_LAGGING",
            },
        },
    ]
    return {
        "fact_catalog": facts,
        "key_change_fact_ids": ["market:real_yield:DFII10"],
        "coverage": {
            "breadth": {
                "status": "unavailable",
                "reason": "provider_publication_pending",
            }
        },
    }


def test_run41_plan_keeps_current_core_rsp_and_sector_extremes() -> None:
    plan = build_us_market_digest_plan(run41_market_context())
    items = {item.slot: item for item in plan.items}

    assert [item.slot for item in plan.items] == list(UsMarketDigestSlot)
    assert items[UsMarketDigestSlot.CURRENT_MARKET].evidence_refs == (
        "market:index:SPY",
        "market:index:QQQ",
        "market:index:IWM",
        "market:sector:SOXX",
    )
    assert "상승은 S&P500·Nasdaq·반도체" in items[
        UsMarketDigestSlot.CURRENT_MARKET
    ].claim_text
    assert "하락은 Russell 2000" in items[
        UsMarketDigestSlot.CURRENT_MARKET
    ].claim_text
    assert items[UsMarketDigestSlot.PARTICIPATION_STYLE].evidence_refs == (
        "market:style:RSP",
        "market:index:SPY",
    )
    assert items[UsMarketDigestSlot.SMALL_CAP_RELATIVE].omission_reason == (
        DigestOmissionReason.OMITTED_SAFE_NOT_MATERIAL
    )
    assert items[UsMarketDigestSlot.SEMICONDUCTOR_RELATIVE].omission_reason == (
        DigestOmissionReason.OMITTED_SAFE_NOT_MATERIAL
    )
    assert items[UsMarketDigestSlot.SECTOR_DISPERSION].evidence_refs == (
        "market:sector:XLI",
        "market:sector:XLV",
    )
    assert items[UsMarketDigestSlot.BREADTH_STATE].omission_reason == (
        DigestOmissionReason.OMITTED_UNAVAILABLE
    )
    assert items[UsMarketDigestSlot.MACRO_CONTEXT].required_consumption is False


def test_material_iwm_and_soxx_relative_signals_are_selected_by_backend() -> None:
    context = run41_market_context()
    current_returns = {
        "SPY": -0.2269,
        "QQQ": -0.6490,
        "IWM": -1.3542,
        "SOXX": -3.1993,
        "RSP": -0.3432,
    }
    for fact in context["fact_catalog"]:
        if not isinstance(fact, dict):
            continue
        fields = fact.get("fields")
        if not isinstance(fields, dict):
            continue
        series = fields.get("series_code")
        if series in current_returns:
            fields["return_pct"] = current_returns[series]

    plan = build_us_market_digest_plan(context)
    items = {item.slot: item for item in plan.items}
    small_cap = items[UsMarketDigestSlot.SMALL_CAP_RELATIVE]
    semiconductor = items[UsMarketDigestSlot.SEMICONDUCTOR_RELATIVE]

    assert small_cap.selected is True
    assert small_cap.evidence_refs == ("market:index:IWM", "market:index:SPY")
    assert small_cap.claim_text == (
        "소형주 IWM도 SPY보다 약해 위험선호는 제한적이었습니다."
    )
    assert "-1.13pp" in small_cap.materiality
    assert semiconductor.selected is True
    assert semiconductor.evidence_refs == (
        "market:sector:SOXX",
        "market:index:SPY",
    )
    assert semiconductor.claim_text == (
        "반도체 SOXX가 SPY를 크게 밑돌아 반도체 상대약세가 두드러졌습니다."
    )
    assert "-2.97pp" in semiconductor.materiality


def test_plan_round_trip_preserves_typed_slots_and_refs() -> None:
    plan = build_us_market_digest_plan(run41_market_context())

    restored = UsMarketDigestPlan.from_dict(plan.to_dict())

    assert restored == plan
    assert restored is not None
    assert restored.required_evidence_refs() == plan.required_evidence_refs()


def test_fallback_renders_plan_before_lagging_macro_without_numeric_dump() -> None:
    plan = build_us_market_digest_plan(run41_market_context())
    digest = DailyDigest(
        digest_date=date(2026, 8, 27),
        market_scope="us",
        macro=MacroInterpretation(
            regime_label="혼합",
            confidence=0.8,
            one_line="공식 관측(8/25) 미국 실질금리가 하락했습니다.",
            key_changes=["미국 실질금리는 직전 관측에서 하락했습니다."],
            axis_explanations=[("할인율", "실질금리 하락은 성장주에 우호적입니다.")],
            integrated_view=["• 할인율 맥락은 보조적으로 확인합니다."],
            market_assumptions=[],
        ),
        portfolio=PortfolioSummary(
            thesis_counts={
                "strengthened": 0,
                "maintained": 13,
                "weakened": 0,
                "invalidated": 0,
            },
            valuation_counts={
                "expansion": 0,
                "neutral": 13,
                "mixed": 0,
                "compression": 0,
                "unknown": 0,
            },
            tickers=[],
            focus_tickers=[],
        ),
        schedule=ScheduleSummary(),
        data_quality=DataQualitySummary(),
        us_market_digest_plan=plan,
    )

    rendered = render_daily_digest(digest, include_stock_details=False)

    assert rendered.index("📍 미국장 세션 구조") < rendered.index("🌐 보조 거시환경")
    assert rendered.index("현재 세션에서") < rendered.index("미국 실질금리가")
    assert "동일가중 S&P500은 상승" in rendered
    assert "산업재가 가장 강했고 헬스케어가 가장 약했습니다" in rendered
    for value in ("0.0222", "0.0915", "-0.1003", "1.0874", "-0.9983"):
        assert value not in rendered


def test_non_current_core_is_temporally_omitted_not_promoted() -> None:
    context = run41_market_context()
    for fact in context["fact_catalog"]:
        if not isinstance(fact, dict):
            continue
        fields = fact.get("fields")
        if isinstance(fields, dict) and fields.get("series_code") in {
            "SPY",
            "QQQ",
            "IWM",
            "SOXX",
        }:
            fields["temporal_role"] = "REFERENCE_LAGGING"
            fields["today_signal_eligible"] = False

    plan = build_us_market_digest_plan(context)
    current = plan.items[0]

    assert current.slot == UsMarketDigestSlot.CURRENT_MARKET
    assert current.omission_reason == DigestOmissionReason.OMITTED_TEMPORAL
    assert current.required_consumption is False


def test_adaptive_market_renderer_retains_shared_plan_claims() -> None:
    context = run41_market_context()
    plan = build_us_market_digest_plan(context)
    context["us_market_digest_plan"] = plan.to_dict()
    source = """🤖 AI 보조 미국시장 점검 · US Pilot 4/5

🎯 판단
공식 관측 미국 실질금리는 하락했습니다.

🔎 왜 중요한가
할인율 신호가 가격을 결정하는 시장입니다.

📌 다음 확인
• 다음 공식 실질금리 관측을 확인합니다.
"""
    deterministic = """🌎 미국 종목 점검 · 2026-08-27

📍 미국장 세션 구조
• 현재 세션에서 상승은 S&P500·Nasdaq·반도체, 하락은 Russell 2000이었습니다.
• 동일가중 S&P500은 상승해 시가총액가중 S&P500과 방향이 같았습니다.
• 업종 프록시에서는 산업재가 가장 강했고 헬스케어가 가장 약했습니다.

🌐 보조 거시환경
미국 실질금리는 직전 공식 관측에서 하락했습니다.
"""

    candidate = build_production_candidate(
        source,
        deterministic_text=deterministic,
        message_key="market:run41-repair",
        market="us",
        packet_owner="2026-08-27-us-run-41-ae4f42c23abc",
        is_market_digest=True,
        market_context=context,
    )

    assert candidate.eligible is True
    assert "현재 세션에서 상승은 S&P500·Nasdaq·반도체" in candidate.candidate_text
    assert "동일가중 S&P500은 상승" in candidate.candidate_text
    assert "산업재가 가장 강했고 헬스케어가 가장 약했습니다" in candidate.candidate_text
