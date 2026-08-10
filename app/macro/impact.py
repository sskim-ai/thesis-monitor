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
USABLE_QUALITY = {"fresh", "revised"}
CANONICAL_CHANNELS = {
    "market_volatility": "risk_appetite",
    "us_10y_real_yield": "discount_rate",
    "us_10y_yield": "discount_rate",
    "hyperscaler_capex": "demand",
}


def migrate_macro_exposure_channels(session: Session) -> dict[str, int]:
    theses = session.exec(select(InvestmentThesis)).all()
    updated_theses = 0
    updated_exposures = 0
    for thesis in theses:
        try:
            exposures = json.loads(thesis.macro_exposures)
        except json.JSONDecodeError:
            continue
        if not isinstance(exposures, list):
            continue
        changed = False
        for exposure in exposures:
            if not isinstance(exposure, dict):
                continue
            factor = str(exposure.get("factor", ""))
            canonical = CANONICAL_CHANNELS.get(factor)
            if canonical and exposure.get("channel") != canonical:
                exposure["channel"] = canonical
                changed = True
                updated_exposures += 1
        if changed:
            thesis.macro_exposures = json.dumps(exposures, ensure_ascii=False)
            session.add(thesis)
            updated_theses += 1
    if updated_theses:
        session.commit()
    return {"theses": updated_theses, "exposures": updated_exposures}


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
        add("hyperscaler_capex", "positive", 5, "demand")
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


def _channel(exposure: dict[str, object]) -> str:
    factor = str(exposure.get("factor", ""))
    return CANONICAL_CHANNELS.get(factor, str(exposure.get("channel", "unknown")))


def _has_defined_condition(exposure: dict[str, object]) -> bool:
    condition = str(exposure.get("condition") or "").strip().lower()
    return bool(condition and condition != "auto_draft") and not bool(
        exposure.get("review_required", False)
    )


def _earnings_channel_is_eligible(
    factor: str,
    channel: str,
    exposure: dict[str, object],
) -> bool:
    if channel in {"discount_rate", "risk_appetite", "liquidity"}:
        return False
    if factor in {"usdkrw", "dollar", "wti", "brent", "oil"}:
        return _has_defined_condition(exposure)
    if factor == "credit_spread":
        condition = str(exposure.get("condition") or "").lower()
        return _has_defined_condition(exposure) and any(
            term in condition for term in ("debt", "leverage", "refinanc", "차입", "부채")
        )
    return channel in {"demand", "pricing", "cost", "fx", "funding"}


def _impact_direction(net: float) -> str:
    if net >= 5:
        return "strengthen"
    if net <= -5:
        return "weaken"
    return "neutral"


def _material_channel_effect(contributions: list[float]) -> str:
    positive = sum(value for value in contributions if value > 0)
    negative = abs(sum(value for value in contributions if value < 0))
    if positive >= 5 and negative >= 5:
        return "mixed"
    if positive - negative >= 5:
        return "strengthen"
    if negative - positive >= 5:
        return "weaken"
    return "neutral"


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
    if observation is None or observation.quality_status not in USABLE_QUALITY:
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
    migrate_macro_exposure_channels(session)
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
        reviewed_weights: list[int] = []
        channel_contributions: dict[str, float] = {}
        channel_evidence_contributions: dict[str, list[float]] = {}
        earnings_contributions: dict[str, float] = {}
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
            condition_required = factor in {
                "usdkrw",
                "dollar",
                "wti",
                "brent",
                "oil",
                "credit_spread",
            } and not _has_defined_condition(exposure)
            contribution = (
                0
                if condition_required
                else factor_signal * direction_multiplier * weight * magnitude
            )
            net += contribution
            max_magnitude = max(max_magnitude, magnitude)
            channel = _channel(exposure)
            channels.add(channel)
            channel_contributions[channel] = channel_contributions.get(channel, 0) + contribution
            channel_evidence_contributions.setdefault(channel, []).append(contribution)
            if _earnings_channel_is_eligible(factor, channel, exposure):
                earnings_contributions[channel] = (
                    earnings_contributions.get(channel, 0) + contribution
                )
            reviewed_count += 1
            reviewed_weights.append(weight)
            item_evidence["contribution"] = contribution
            item_evidence["exposure"] = {**exposure, "channel": channel}
            item_evidence["earnings_link_validated"] = _earnings_channel_is_eligible(
                factor, channel, exposure
            )
            item_evidence["condition_required"] = condition_required
            evidence.append(item_evidence)

        direction = _impact_direction(net)
        low_weight_only = reviewed_count == 1 and reviewed_weights[0] <= 2
        if low_weight_only:
            direction = "neutral"
        earnings_values = list(earnings_contributions.values())
        valuation_values = [
            value
            for channel in {"discount_rate", "risk_appetite"}
            for value in channel_evidence_contributions.get(channel, [])
        ]
        earnings_effect = (
            "neutral" if low_weight_only else _material_channel_effect(earnings_values)
        )
        valuation_effect = (
            "neutral" if low_weight_only else _material_channel_effect(valuation_values)
        )
        confidence = round(min(0.9, 0.35 + reviewed_count * 0.1), 2) if evidence else 0.0
        rationale = (
            "검토 가능한 거시 exposure 근거가 없습니다."
            if not evidence
            else f"{len(evidence)}개 거시 전달 경로의 합산 점수는 {net:+.1f}입니다."
        )
        if evidence and low_weight_only:
            rationale += " 단일 저가중치 경로이므로 일일 방향 판정은 유지했습니다."
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
            "earnings_effect": earnings_effect,
            "valuation_effect": valuation_effect,
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
