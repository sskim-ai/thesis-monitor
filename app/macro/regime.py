import json
from datetime import date, datetime, timedelta

from sqlmodel import Session, select

from app.models.macro import MacroObservation, MacroRegimeAssessment
from app.services.market_session import us_market_session


QUALITY_WEIGHTS = {
    "fresh": 1.0,
    "revised": 0.9,
    "partial": 0.5,
    "provisional": 0.5,
    "stale": 0.0,
}
DIRECTIONAL_QUALITY = {"fresh", "revised"}


def _latest(session: Session, series_code: str) -> MacroObservation | None:
    return session.exec(
        select(MacroObservation)
        .where(MacroObservation.series_code == series_code)
        .order_by(MacroObservation.observed_at.desc())
    ).first()


def _direction(value: float | None, threshold: float) -> int:
    if value is None:
        return 0
    if value >= threshold:
        return 1
    if value <= -threshold:
        return -1
    return 0


def _value(observation: MacroObservation | None, field: str) -> float | None:
    if observation is None or observation.quality_status not in DIRECTIONAL_QUALITY:
        return None
    value = getattr(observation, field)
    return float(value) if isinstance(value, (int, float)) else None


def _clamp(value: int) -> int:
    return max(-2, min(2, value))


def assess_macro_regime(
    session: Session,
    assessment_date: date,
    as_of: datetime | None = None,
) -> MacroRegimeAssessment:
    spy = _latest(session, "SPY")
    qqq = _latest(session, "QQQ")
    iwm = _latest(session, "IWM")
    soxx = _latest(session, "SOXX")
    vix = _latest(session, "VIXCLS")
    real_yield = _latest(session, "DFII10")
    dollar = _latest(session, "DTWEXBGS")
    credit = _latest(session, "BAMLH0A0HYM2")
    breakeven = _latest(session, "T10YIE")
    oil = _latest(session, "DCOILWTICO")

    growth = _clamp(
        _direction(_value(iwm, "change_pct"), 0.5)
        + _direction(_value(soxx, "change_pct"), 0.8)
    )
    inflation = _clamp(
        _direction(_value(breakeven, "change_value"), 0.05)
        + _direction(_value(oil, "change_pct"), 2.0)
    )
    liquidity = _clamp(-_direction(_value(dollar, "change_pct"), 0.3))
    financial = _clamp(
        -_direction(_value(real_yield, "change_value"), 0.05)
        - _direction(_value(credit, "change_value"), 0.1)
    )
    risk = _clamp(
        _direction(_value(spy, "change_pct"), 0.5)
        + _direction(_value(qqq, "change_pct"), 0.7)
        - _direction(_value(vix, "change_pct"), 5.0)
    )
    earnings = _clamp(_direction(_value(soxx, "change_pct"), 1.0))

    available = [
        item
        for item in (spy, qqq, iwm, soxx, vix, real_yield, dollar, credit, breakeven, oil)
        if item is not None
    ]
    completeness = sum(
        QUALITY_WEIGHTS.get(item.quality_status, 0.0) for item in available
    ) / 10
    confidence = round(min(0.9, completeness * 0.9), 2)
    if growth >= 1 and inflation <= 0 and risk >= 1:
        label = "goldilocks"
    elif growth <= -1 and inflation >= 1:
        label = "stagflation_risk"
    elif growth <= -1 and financial <= -1:
        label = "recession_risk"
    elif liquidity >= 1 and risk >= 1:
        label = "liquidity_risk_on"
    else:
        label = "mixed"

    evidence = [
        {
            "series_code": item.series_code,
            "value": item.value,
            "change_pct": item.change_pct,
            "change_value": item.change_value,
            "quality_status": item.quality_status,
            "source_url": item.source_url,
        }
        for item in available
    ]
    summary = (
        f"성장 {growth:+d}, 물가 {inflation:+d}, 유동성 {liquidity:+d}, "
        f"금융여건 {financial:+d}, 위험선호 {risk:+d}, 이익 {earnings:+d}"
    )
    previous = session.exec(
        select(MacroRegimeAssessment)
        .where(MacroRegimeAssessment.assessment_date < assessment_date)
        .order_by(MacroRegimeAssessment.assessment_date.desc())
    ).first()
    persistence_days = 1
    if (
        previous is not None
        and previous.regime_label == label
        and assessment_date - previous.assessment_date <= timedelta(days=4)
    ):
        persistence_days = previous.persistence_days + 1

    raw_label = label
    if (
        previous is not None
        and previous.regime_label != label
        and label != "mixed"
        and confidence < 0.6
    ):
        label = previous.regime_label
        persistence_days = previous.persistence_days
        summary = f"판정 유보({raw_label}): {summary}"

    session_state = us_market_session(as_of)
    provisional = confidence < 0.5 or session_state.assessment_state == "provisional"
    row = session.get(MacroRegimeAssessment, assessment_date)
    if row is None:
        row = MacroRegimeAssessment(
            assessment_date=assessment_date,
            growth_momentum=growth,
            inflation_pressure=inflation,
            liquidity_condition=liquidity,
            financial_conditions=financial,
            risk_appetite=risk,
            earnings_momentum=earnings,
            regime_label=label,
            confidence=confidence,
            persistence_days=persistence_days,
            provisional=provisional,
            market_session=session_state.session,
            assessment_state=session_state.assessment_state,
            summary=summary,
            evidence=json.dumps(evidence, ensure_ascii=False),
        )
    else:
        row.growth_momentum = growth
        row.inflation_pressure = inflation
        row.liquidity_condition = liquidity
        row.financial_conditions = financial
        row.risk_appetite = risk
        row.earnings_momentum = earnings
        row.regime_label = label
        row.confidence = confidence
        row.persistence_days = persistence_days
        row.provisional = provisional
        row.market_session = session_state.session
        row.assessment_state = session_state.assessment_state
        row.summary = summary
        row.evidence = json.dumps(evidence, ensure_ascii=False)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row
