import json
from datetime import date, timedelta

from sqlmodel import Session, select

from app.models.macro import MacroObservation, MacroRegimeAssessment


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


def _clamp(value: int) -> int:
    return max(-2, min(2, value))


def assess_macro_regime(session: Session, assessment_date: date) -> MacroRegimeAssessment:
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
        _direction(iwm.change_pct if iwm else None, 0.5)
        + _direction(soxx.change_pct if soxx else None, 0.8)
    )
    inflation = _clamp(
        _direction(breakeven.change_value if breakeven else None, 0.05)
        + _direction(oil.change_pct if oil else None, 2.0)
    )
    liquidity = _clamp(-_direction(dollar.change_pct if dollar else None, 0.3))
    financial = _clamp(
        -_direction(real_yield.change_value if real_yield else None, 0.05)
        - _direction(credit.change_value if credit else None, 0.1)
    )
    risk = _clamp(
        _direction(spy.change_pct if spy else None, 0.5)
        + _direction(qqq.change_pct if qqq else None, 0.7)
        - _direction(vix.change_pct if vix else None, 5.0)
    )
    earnings = _clamp(_direction(soxx.change_pct if soxx else None, 1.0))

    available = [
        item
        for item in (spy, qqq, iwm, soxx, vix, real_yield, dollar, credit, breakeven, oil)
        if item is not None
    ]
    confidence = round(min(0.9, len(available) / 10 * 0.9), 2)
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
            provisional=confidence < 0.5,
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
        row.provisional = confidence < 0.5
        row.summary = summary
        row.evidence = json.dumps(evidence, ensure_ascii=False)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row
