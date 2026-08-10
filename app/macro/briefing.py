import json
from datetime import date, datetime, timedelta

from sqlmodel import Session, select

from app.models.macro import (
    MacroBriefing,
    MacroEvent,
    MacroObservation,
    MacroRegimeAssessment,
    MacroThesis,
    ThesisMacroImpact,
)


MARKET_DISPLAY = {
    "SPY": "S&P",
    "QQQ": "Nasdaq",
    "IWM": "Russell 2000",
    "SOXX": "SOXX",
    "DGS10": "미10Y",
    "DFII10": "실질10Y",
    "T10YIE": "미10Y 기대인플레이션",
    "BAMLH0A0HYM2": "미 하이일드 스프레드",
    "DTWEXBGS": "미 달러지수(광의)",
    "USDKRW": "USD/KRW",
    "DCOILWTICO": "WTI",
    "VIXCLS": "VIX",
}

REGIME_DISPLAY = {
    "goldilocks": "골디락스",
    "stagflation_risk": "스태그플레이션 위험",
    "recession_risk": "경기침체 위험",
    "liquidity_risk_on": "유동성 주도 위험선호",
    "mixed": "혼합",
}

MACRO_STATUS_DISPLAY = {
    "strengthening": "근거 우세",
    "intact": "유지",
    "weakening": "약화",
    "structural_break": "구조적 재검토",
}

IMPACT_DISPLAY = {
    "strengthen": "강화",
    "weaken": "약화",
    "mixed": "혼재",
    "neutral": "중립",
}


def _thesis_daily_signal(
    thesis_key: str,
    regime: MacroRegimeAssessment,
) -> tuple[int, str]:
    if thesis_key == "us_soft_landing_disinflation":
        if (
            regime.growth_momentum >= 1
            and regime.inflation_pressure <= 0
        ) or (
            regime.growth_momentum >= 0
            and regime.inflation_pressure <= -1
        ):
            signal = 1
        elif regime.growth_momentum <= -1 or regime.inflation_pressure >= 1:
            signal = -1
        else:
            signal = 0
        rationale = (
            f"성장 {regime.growth_momentum:+d}, 물가 {regime.inflation_pressure:+d}: "
            "성장 급락과 물가 재가속이 함께 나타나는지 점검했습니다."
        )
    elif thesis_key == "fed_policy_path":
        signal = int(regime.financial_conditions >= 1) - int(
            regime.financial_conditions <= -1
        )
        rationale = (
            f"금융여건 {regime.financial_conditions:+d}: 실질금리와 신용스프레드가 "
            "구조적 재긴축을 가리키는지 점검했습니다."
        )
    elif thesis_key == "ai_capex_cycle":
        signal = regime.earnings_momentum
        rationale = (
            f"이익 모멘텀 {regime.earnings_momentum:+d}: 반도체 가격 반응을 "
            "AI CAPEX·이익 기대의 단기 대용치로 사용했습니다."
        )
    elif thesis_key == "china_korea_export_cycle":
        signal = regime.growth_momentum
        rationale = (
            f"성장 모멘텀 {regime.growth_momentum:+d}: 소형주·반도체 위험선호를 "
            "수출 경기의 단기 대용치로 사용했습니다."
        )
    else:
        signal = -1 if regime.inflation_pressure >= 2 else 0
        rationale = (
            f"물가 압력 {regime.inflation_pressure:+d}: 유가·기대인플레이션이 "
            "지속적 공급 충격 수준인지 점검했습니다."
        )
    return signal, rationale


def _json(value: str, fallback: object) -> object:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return fallback
    return parsed


def _latest_observations(session: Session) -> list[MacroObservation]:
    rows: list[MacroObservation] = []
    for series_code in MARKET_DISPLAY:
        row = session.exec(
            select(MacroObservation)
            .where(MacroObservation.series_code == series_code)
            .order_by(MacroObservation.observed_at.desc())
        ).first()
        if row is not None:
            rows.append(row)
    return rows


def _format_move(row: MacroObservation) -> str:
    label = MARKET_DISPLAY.get(row.series_code, row.series_code)
    if row.category in {"rates", "real_rates", "credit", "inflation_expectations"}:
        move = (row.change_value or 0) * 100
        return f"{label} {move:+.0f}bp"
    if row.change_pct is not None:
        return f"{label} {row.change_pct:+.1f}%"
    return f"{label} {row.value:g}"


def build_macro_briefing(
    session: Session,
    briefing_date: date,
    as_of: datetime,
    regime: MacroRegimeAssessment,
    theses: list[MacroThesis],
    impacts: list[ThesisMacroImpact],
    provider_warnings: list[str],
) -> MacroBriefing:
    observations = _latest_observations(session)
    market_items = [_format_move(item) for item in observations]
    calendar = session.exec(
        select(MacroEvent)
        .where(MacroEvent.scheduled_at.is_not(None))
        .order_by(MacroEvent.scheduled_at)
    ).all()
    calendar_items = [
        {
            "event_key": item.event_key,
            "title": item.title,
            "scheduled_at": item.scheduled_at,
            "status": item.event_status,
            "actual": item.actual,
            "consensus": item.consensus,
            "previous": item.previous,
            "unit": item.unit,
            "impact_level": item.impact_level,
        }
        for item in calendar
        if item.scheduled_at is not None
        and briefing_date <= item.scheduled_at.date() <= briefing_date + timedelta(days=7)
    ]
    thesis_items = []
    for item in theses:
        daily_signal, signal_rationale = _thesis_daily_signal(item.thesis_key, regime)
        thesis_items.append(
            {
            "thesis_key": item.thesis_key,
            "title": item.title,
            "status": item.status,
            "today_signal": item.today_signal,
            "today_signal_rationale": item.today_signal_rationale,
            "confidence": item.confidence,
            "description": item.description,
            "expected_evidence": _json(item.expected_evidence, []),
            "weakening_evidence": _json(item.weakening_evidence, []),
            "valuation_channels": _json(item.valuation_channels, []),
            "daily_signal": daily_signal,
            "signal_rationale": signal_rationale,
            "confidence_meaning": "내부 근거 충족도이며 발생 확률이 아님",
            }
        )
    impact_items = [
        {
            "ticker": item.ticker,
            "direction": item.direction,
            "magnitude": item.magnitude,
            "confidence": item.confidence,
            "rationale": item.rationale,
            "earnings_effect": item.earnings_effect,
            "valuation_effect": item.valuation_effect,
            "channels": _json(item.channels, []),
        }
        for item in impacts
        if item.direction != "neutral"
    ]
    quality_items = [{"warning": warning} for warning in provider_warnings]
    quality_items.extend(
        {
            "series_code": item.series_code,
            "quality_status": item.quality_status,
            "observed_at": item.observed_at,
        }
        for item in observations
        if item.quality_status != "fresh"
    )
    headline = f"{regime.regime_label}: {regime.summary}"
    market_text = ", ".join(market_items[:6]) or "시장 데이터 없음"
    changed_theses = [item for item in thesis_items if item["status"] != "intact"]
    thesis_text = ", ".join(
        f"{item['title']} {MACRO_STATUS_DISPLAY.get(str(item['status']), item['status'])}"
        for item in changed_theses[:2]
    ) or "주요 시장 가정 큰 변화 없음"
    impact_text = ", ".join(
        f"{item['ticker']} {IMPACT_DISPLAY.get(str(item['direction']), item['direction'])} "
        f"{item['magnitude']}/5"
        for item in impact_items[:3]
    ) or "종목별 유의미한 변화 없음"
    regime_display = REGIME_DISPLAY.get(regime.regime_label, regime.regime_label)
    kakao_text = (
        f"[시장환경 점검] {regime_display}\n"
        f"{market_text}\n"
        f"{thesis_text}\n"
        f"{impact_text}"
    )[:200]

    row = session.exec(
        select(MacroBriefing).where(
            MacroBriefing.briefing_date == briefing_date,
            MacroBriefing.briefing_type == "morning",
        )
    ).first()
    values = {
        "as_of": as_of,
        "headline": headline,
        "market_summary": json.dumps(
            {
                "items": market_items,
                "observations": [
                    {
                        "series_code": item.series_code,
                        "category": item.category,
                        "value": item.value,
                        "unit": item.unit,
                        "change_value": item.change_value,
                        "change_pct": item.change_pct,
                        "quality_status": item.quality_status,
                        "source_url": item.source_url,
                    }
                    for item in observations
                ],
            },
            ensure_ascii=False,
            default=str,
        ),
        "regime_summary": json.dumps(
            {
                "label": regime.regime_label,
                "summary": regime.summary,
                "confidence": regime.confidence,
                "provisional": regime.provisional,
                "market_session": regime.market_session,
                "assessment_state": regime.assessment_state,
                "growth_momentum": regime.growth_momentum,
                "inflation_pressure": regime.inflation_pressure,
                "liquidity_condition": regime.liquidity_condition,
                "financial_conditions": regime.financial_conditions,
                "risk_appetite": regime.risk_appetite,
                "earnings_momentum": regime.earnings_momentum,
            },
            ensure_ascii=False,
        ),
        "today_calendar": json.dumps(calendar_items, ensure_ascii=False, default=str),
        "macro_theses": json.dumps(thesis_items, ensure_ascii=False),
        "ticker_impacts": json.dumps(impact_items, ensure_ascii=False),
        "data_quality": json.dumps(quality_items, ensure_ascii=False, default=str),
        "kakao_text": kakao_text,
        "status": "ready",
        "market_session": regime.market_session,
        "assessment_state": regime.assessment_state,
    }
    if row is None:
        row = MacroBriefing(
            briefing_date=briefing_date,
            briefing_type="morning",
            dedupe_key=f"macro:{briefing_date}:morning",
            **values,
        )
    else:
        for key, value in values.items():
            setattr(row, key, value)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def briefing_to_dict(row: MacroBriefing) -> dict[str, object]:
    return {
        "briefing_date": row.briefing_date,
        "briefing_type": row.briefing_type,
        "as_of": row.as_of,
        "headline": row.headline,
        "market_summary": _json(row.market_summary, {}),
        "regime_summary": _json(row.regime_summary, {}),
        "today_calendar": _json(row.today_calendar, []),
        "macro_theses": _json(row.macro_theses, []),
        "ticker_impacts": _json(row.ticker_impacts, []),
        "data_quality": _json(row.data_quality, []),
        "kakao_text": row.kakao_text,
        "status": row.status,
        "market_session": row.market_session,
        "assessment_state": row.assessment_state,
    }
