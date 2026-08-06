import json
from datetime import date

from sqlmodel import Session, select

from app.models.macro import MacroEvent, MacroObservation, MacroShockAssessment


SERIES_SHOCKS: dict[str, tuple[str, float, str]] = {
    "DFII10": ("monetary_tightening", 0.08, "change_value"),
    "BAMLH0A0HYM2": ("credit_stress", 0.15, "change_value"),
    "DCOILWTICO": ("supply_inflation", 3.0, "change_pct"),
    "DTWEXBGS": ("liquidity_drain", 0.7, "change_pct"),
    "VIXCLS": ("risk_aversion", 8.0, "change_pct"),
    "SOXX": ("technology_capex_acceleration", 2.0, "change_pct"),
}


def _latest(session: Session, series_code: str) -> MacroObservation | None:
    return session.exec(
        select(MacroObservation)
        .where(MacroObservation.series_code == series_code)
        .order_by(MacroObservation.observed_at.desc())
    ).first()


def _upsert(
    session: Session,
    assessment_date: date,
    event_id: int | None,
    shock_type: str,
    direction: str,
    magnitude: int,
    confidence: float,
    evidence: list[dict[str, object]],
) -> MacroShockAssessment:
    query = select(MacroShockAssessment).where(
        MacroShockAssessment.assessment_date == assessment_date,
        MacroShockAssessment.shock_type == shock_type,
    )
    query = (
        query.where(MacroShockAssessment.event_id.is_(None))
        if event_id is None
        else query.where(MacroShockAssessment.event_id == event_id)
    )
    row = session.exec(query).first()
    values = {
        "direction": direction,
        "magnitude": magnitude,
        "persistence": "temporary",
        "confidence": confidence,
        "evidence": json.dumps(evidence, ensure_ascii=False),
    }
    if row is None:
        row = MacroShockAssessment(
            assessment_date=assessment_date,
            event_id=event_id,
            shock_type=shock_type,
            **values,
        )
    else:
        for key, value in values.items():
            setattr(row, key, value)
    session.add(row)
    return row


def assess_macro_shocks(
    session: Session,
    assessment_date: date,
) -> list[MacroShockAssessment]:
    rows: list[MacroShockAssessment] = []
    for series_code, (positive_type, threshold, change_field) in SERIES_SHOCKS.items():
        observation = _latest(session, series_code)
        if observation is None or observation.quality_status != "fresh":
            continue
        change = getattr(observation, change_field)
        if change is None or abs(change) < threshold:
            continue
        shock_type = positive_type
        if change < 0:
            shock_type = {
                "monetary_tightening": "monetary_easing",
                "credit_stress": "credit_relief",
                "supply_inflation": "disinflation",
                "liquidity_drain": "liquidity_injection",
                "risk_aversion": "risk_appetite",
                "technology_capex_acceleration": "technology_capex_slowdown",
            }[positive_type]
        ratio = abs(change) / threshold
        magnitude = min(5, max(1, int(ratio) + 1))
        rows.append(
            _upsert(
                session,
                assessment_date,
                None,
                f"{shock_type}:{series_code}",
                "positive" if change > 0 else "negative",
                magnitude,
                min(0.9, 0.55 + ratio * 0.08),
                [
                    {
                        "series_code": series_code,
                        "value": observation.value,
                        "change": change,
                        "source_url": observation.source_url,
                    }
                ],
            )
        )

    events = session.exec(
        select(MacroEvent).where(MacroEvent.released_at.is_not(None))
    ).all()
    for event in events:
        if (
            event.id is None
            or event.released_at is None
            or event.released_at.date() != assessment_date
            or event.surprise_value in {None, 0}
        ):
            continue
        rows.append(
            _upsert(
                session,
                assessment_date,
                event.id,
                f"event_surprise:{event.category}",
                "positive" if event.surprise_value > 0 else "negative",
                max(1, min(5, event.impact_level)),
                event.source_reliability,
                [
                    {
                        "event_key": event.event_key,
                        "actual": event.actual,
                        "consensus": event.consensus,
                        "source_url": event.source_url,
                    }
                ],
            )
        )
    session.commit()
    for row in rows:
        session.refresh(row)
    return rows
