import json
from datetime import date, datetime

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
    "SOXX": "SOXX",
    "DGS10": "미10Y",
    "DFII10": "실질10Y",
    "DTWEXBGS": "달러",
    "USDKRW": "USD/KRW",
    "DCOILWTICO": "WTI",
    "VIXCLS": "VIX",
}


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
        }
        for item in calendar
        if item.scheduled_at is not None and item.scheduled_at.date() == briefing_date
    ]
    thesis_items = [
        {
            "thesis_key": item.thesis_key,
            "title": item.title,
            "status": item.status,
            "confidence": item.confidence,
        }
        for item in theses
    ]
    impact_items = [
        {
            "ticker": item.ticker,
            "direction": item.direction,
            "magnitude": item.magnitude,
            "confidence": item.confidence,
            "rationale": item.rationale,
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
        f"{item['title']} {item['status']}" for item in changed_theses[:2]
    ) or "Macro Thesis 큰 변화 없음"
    impact_text = ", ".join(
        f"{item['ticker']} {item['direction']} {item['magnitude']}/5"
        for item in impact_items[:3]
    ) or "종목별 유의미한 변화 없음"
    kakao_text = (
        f"[거시 브리핑] {regime.regime_label}\n"
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
                        "value": item.value,
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
            },
            ensure_ascii=False,
        ),
        "today_calendar": json.dumps(calendar_items, ensure_ascii=False, default=str),
        "macro_theses": json.dumps(thesis_items, ensure_ascii=False),
        "ticker_impacts": json.dumps(impact_items, ensure_ascii=False),
        "data_quality": json.dumps(quality_items, ensure_ascii=False, default=str),
        "kakao_text": kakao_text,
        "status": "ready",
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
    }
