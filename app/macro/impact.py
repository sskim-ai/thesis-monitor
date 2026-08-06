import json
from datetime import date

from sqlmodel import Session, select

from app.models.macro import MacroEvent, MacroObservation, ThesisMacroImpact
from app.models.thesis import InvestmentThesis
from app.models.watchlist import WatchlistItem


FACTOR_SERIES = {
    "us_10y_real_yield": "DFII10",
    "us_10y_yield": "DGS10",
    "usdkrw": "USDKRW",
    "dollar": "DTWEXBGS",
    "brent": "DCOILWTICO",
    "wti": "DCOILWTICO",
    "oil": "DCOILWTICO",
    "credit_spread": "BAMLH0A0HYM2",
    "market_volatility": "VIXCLS",
}


def _latest_observation(session: Session, series_code: str) -> MacroObservation | None:
    return session.exec(
        select(MacroObservation)
        .where(MacroObservation.series_code == series_code)
        .order_by(MacroObservation.observed_at.desc())
    ).first()


def _active_thesis(session: Session, ticker: str) -> InvestmentThesis | None:
    return session.exec(
        select(InvestmentThesis)
        .where(InvestmentThesis.ticker == ticker, InvestmentThesis.status == "active")
        .order_by(InvestmentThesis.version.desc())
    ).first()


def _inferred_exposures(thesis: InvestmentThesis) -> list[dict[str, object]]:
    text = " ".join(
        [thesis.core_thesis, thesis.strengthen_signals, thesis.weaken_signals]
    ).lower()
    exposures: list[dict[str, object]] = []

    def add(factor: str, direction: str, weight: int, channel: str) -> None:
        exposures.append(
            {
                "factor": factor,
                "direction": direction,
                "weight": weight,
                "channel": channel,
                "condition": "auto_draft",
                "review_required": True,
            }
        )

    if any(term in text for term in ("ai", "hbm", "반도체", "데이터센터", "semiconductor")):
        add("hyperscaler_capex", "positive", 5, "capex")
        add("us_10y_real_yield", "negative", 2, "discount_rate")
    if any(term in text for term in ("항공", "운송", "airline")):
        add("wti", "negative", 4, "cost")
        add("usdkrw", "negative", 3, "fx")
    if any(term in text for term in ("정유", "에너지", "oil producer", "energy")):
        add("wti", "positive", 4, "pricing")
    if any(term in text for term in ("수출", "export")):
        add("usdkrw", "positive", 2, "fx")
    return exposures


def _exposures(thesis: InvestmentThesis) -> list[dict[str, object]]:
    try:
        values = json.loads(thesis.macro_exposures)
    except json.JSONDecodeError:
        values = []
    parsed = [item for item in values if isinstance(item, dict)] if isinstance(values, list) else []
    if parsed:
        return parsed
    inferred = _inferred_exposures(thesis)
    if inferred:
        thesis.macro_exposures = json.dumps(inferred, ensure_ascii=False)
    return inferred


def _magnitude(observation: MacroObservation) -> int:
    if observation.category in {"rates", "real_rates", "credit", "inflation_expectations"}:
        move = abs(observation.change_value or 0) * 100
        thresholds = (3, 7, 12, 20)
    else:
        move = abs(observation.change_pct or 0)
        thresholds = (0.3, 0.8, 1.5, 3.0)
    if move == 0:
        return 0
    return 1 + sum(move >= threshold for threshold in thresholds)


def _weight(exposure: dict[str, object]) -> int:
    try:
        value = int(exposure.get("weight", 1))
    except (TypeError, ValueError):
        value = 1
    return max(1, min(5, value))


def _factor_signal(
    session: Session,
    factor: str,
    assessment_date: date,
) -> tuple[int, int, dict[str, object]] | None:
    if factor == "hyperscaler_capex":
        events = session.exec(
            select(MacroEvent).where(
                MacroEvent.category == "big_tech_earnings",
                MacroEvent.released_at.is_not(None),
            )
        ).all()
        scored = [
            event
            for event in events
            if event.released_at is not None and event.released_at.date() >= assessment_date
        ]
        if not scored:
            return None
        net = sum(
            1
            if event.surprise_value is not None and event.surprise_value > 0
            else -1
            if event.surprise_value is not None and event.surprise_value < 0
            else 0
            for event in scored
        )
        return (
            1 if net > 0 else -1 if net < 0 else 0,
            min(5, max(event.impact_level for event in scored)),
            {"factor": factor, "events": [event.event_key for event in scored]},
        )

    series_code = FACTOR_SERIES.get(factor)
    if series_code is None:
        return None
    observation = _latest_observation(session, series_code)
    if observation is None:
        return None
    change = observation.change_value
    if observation.category not in {"rates", "real_rates", "credit", "inflation_expectations"}:
        change = observation.change_pct
    signal = 1 if change is not None and change > 0 else -1 if change is not None and change < 0 else 0
    return (
        signal,
        _magnitude(observation),
        {
            "factor": factor,
            "series_code": series_code,
            "value": observation.value,
            "change_value": observation.change_value,
            "change_pct": observation.change_pct,
            "source_url": observation.source_url,
            "quality_status": observation.quality_status,
        },
    )


def assess_thesis_macro_impacts(
    session: Session,
    assessment_date: date,
) -> list[ThesisMacroImpact]:
    watchlist = session.exec(
        select(WatchlistItem).where(WatchlistItem.active.is_(True)).order_by(WatchlistItem.ticker)
    ).all()
    impacts: list[ThesisMacroImpact] = []
    for item in watchlist:
        thesis = _active_thesis(session, item.ticker)
        if thesis is None:
            continue
        exposures = _exposures(thesis)
        net = 0.0
        channels: set[str] = set()
        evidence: list[dict[str, object]] = []
        max_magnitude = 0
        reviewed_count = 0
        for exposure in exposures:
            factor = str(exposure.get("factor", ""))
            result = _factor_signal(session, factor, assessment_date)
            if result is None:
                continue
            factor_signal, magnitude, item_evidence = result
            if magnitude == 0 or factor_signal == 0:
                continue
            exposure_direction = str(exposure.get("direction", "mixed"))
            direction_multiplier = 1 if exposure_direction == "positive" else -1 if exposure_direction == "negative" else 0
            weight = _weight(exposure)
            contribution = factor_signal * direction_multiplier * weight * magnitude
            net += contribution
            max_magnitude = max(max_magnitude, magnitude)
            channels.add(str(exposure.get("channel", "unknown")))
            reviewed_count += 1
            item_evidence["contribution"] = contribution
            item_evidence["exposure"] = exposure
            evidence.append(item_evidence)

        direction = "neutral"
        if net >= 5:
            direction = "strengthen"
        elif net <= -5:
            direction = "weaken"
        elif net != 0:
            direction = "mixed"
        confidence = round(min(0.9, 0.35 + reviewed_count * 0.1), 2) if evidence else 0.0
        rationale = (
            "검토 가능한 거시 exposure 근거가 없습니다."
            if not evidence
            else f"{len(evidence)}개 거시 전달 경로의 합산 점수는 {net:+.1f}입니다."
        )
        existing = session.exec(
            select(ThesisMacroImpact).where(
                ThesisMacroImpact.ticker == thesis.ticker,
                ThesisMacroImpact.thesis_version == thesis.version,
                ThesisMacroImpact.assessment_date == assessment_date,
            )
        ).first()
        values = {
            "direction": direction,
            "magnitude": max_magnitude,
            "persistence": "temporary",
            "confidence": confidence,
            "channels": json.dumps(sorted(channels), ensure_ascii=False),
            "affected_thesis_pillars": json.dumps([], ensure_ascii=False),
            "earnings_effect": direction if "demand" in channels or "capex" in channels else "neutral",
            "valuation_effect": direction if "discount_rate" in channels else "neutral",
            "rationale": rationale,
            "evidence": json.dumps(evidence, ensure_ascii=False),
        }
        if existing is None:
            existing = ThesisMacroImpact(
                ticker=thesis.ticker,
                thesis_version=thesis.version,
                assessment_date=assessment_date,
                **values,
            )
        else:
            for key, value in values.items():
                setattr(existing, key, value)
        session.add(thesis)
        session.add(existing)
        session.commit()
        session.refresh(existing)
        impacts.append(existing)
    return impacts
