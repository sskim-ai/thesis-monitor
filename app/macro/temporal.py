from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone

from sqlmodel import Session, select

from app.models.macro import MacroBriefing, MacroObservation
from app.services.market_session import us_market_session


TEMPORAL_CONTRACT = "macro-digest-temporal-eligibility-v1"

CURRENT_OBSERVATION = "CURRENT_OBSERVATION"
PRIOR_MARKET_SESSION = "PRIOR_MARKET_SESSION"
REFERENCE_LAGGING = "REFERENCE_LAGGING"
STALE_FOR_DAILY_SIGNAL = "STALE_FOR_DAILY_SIGNAL"
UNAVAILABLE = "UNAVAILABLE"

SESSION_BOUND_SERIES = {"SPY", "QQQ", "IWM", "SOXX"}
RELEASE_BOUND_SERIES = {
    "DGS10",
    "DFII10",
    "T10YIE",
    "BAMLH0A0HYM2",
    "DTWEXBGS",
    "DCOILWTICO",
    "VIXCLS",
}
REFERENCE_ONLY_SERIES = {"USDKRW"}
SUPPORTED_SERIES = SESSION_BOUND_SERIES | RELEASE_BOUND_SERIES | REFERENCE_ONLY_SERIES
USABLE_QUALITY = {"fresh", "revised"}


@dataclass(frozen=True)
class TemporalDecision:
    series_code: str
    temporal_role: str
    cadence_basis: str
    observation_date: str | None
    prior_observation_date: str | None
    quality_status: str
    frequency: str | None
    market_session: str | None
    new_since_previous_briefing: bool
    today_signal_eligible: bool
    important_change_eligible: bool
    prior_context_eligible: bool
    regime_state_eligible: bool
    reason: str


def _date_value(value: object) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None


def _observation_map(value: object) -> dict[str, dict[str, object]]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    if not isinstance(value, dict):
        return {}
    rows = value.get("observations", [])
    if not isinstance(rows, list):
        return {}
    return {
        str(item["series_code"]): item
        for item in rows
        if isinstance(item, dict) and item.get("series_code")
    }


def classify_observation(
    item: dict[str, object],
    previous_item: dict[str, object] | None,
    *,
    as_of: datetime,
) -> TemporalDecision:
    code = str(item.get("series_code") or "")
    observed = _date_value(item.get("observed_at"))
    previous = _date_value(previous_item.get("observed_at")) if previous_item else None
    quality = str(item.get("quality_status") or "fresh")
    frequency = str(item.get("frequency")) if item.get("frequency") else None
    market_session = (
        str(item.get("market_session")) if item.get("market_session") else None
    )
    revised_value = bool(
        previous_item
        and observed == previous
        and quality == "revised"
        and item.get("value") != previous_item.get("value")
    )
    changed = bool(observed and (previous is None or observed > previous or revised_value))
    session = us_market_session(as_of)

    if quality not in USABLE_QUALITY or observed is None:
        role = STALE_FOR_DAILY_SIGNAL if observed is not None else UNAVAILABLE
        basis = "quality_or_identity_gate"
        reason = "provider_quality_not_usable" if observed is not None else "observation_date_missing"
    elif code in REFERENCE_ONLY_SERIES:
        role = REFERENCE_LAGGING
        basis = "reference_only_source_occurrence"
        reason = "source_occurrence_date_not_verified_for_daily_delta"
    elif code in SESSION_BOUND_SERIES:
        basis = "XNYS_completed_regular_session"
        completed = session.latest_completed_regular_session_date
        if observed > completed:
            role = UNAVAILABLE
            reason = "observation_after_latest_completed_session"
        elif observed < completed:
            role = STALE_FOR_DAILY_SIGNAL
            reason = "older_than_latest_completed_session"
        elif changed:
            role = CURRENT_OBSERVATION
            reason = "new_completed_session_since_previous_briefing"
        else:
            role = PRIOR_MARKET_SESSION
            reason = "same_completed_session_as_previous_briefing"
    elif code in RELEASE_BOUND_SERIES:
        basis = "official_release_occurrence"
        if previous is not None and observed < previous:
            role = STALE_FOR_DAILY_SIGNAL
            reason = "observation_older_than_previous_briefing"
        elif changed:
            role = CURRENT_OBSERVATION
            reason = "new_official_observation_since_previous_briefing"
        else:
            role = REFERENCE_LAGGING
            reason = "no_new_official_observation_since_previous_briefing"
    else:
        role = REFERENCE_LAGGING
        basis = "unknown_cadence_fail_closed"
        reason = "series_cadence_not_registered"

    return TemporalDecision(
        series_code=code,
        temporal_role=role,
        cadence_basis=basis,
        observation_date=observed.isoformat() if observed else None,
        prior_observation_date=previous.isoformat() if previous else None,
        quality_status=quality,
        frequency=frequency,
        market_session=market_session,
        new_since_previous_briefing=changed,
        today_signal_eligible=role == CURRENT_OBSERVATION,
        important_change_eligible=role in {CURRENT_OBSERVATION, PRIOR_MARKET_SESSION},
        prior_context_eligible=role == PRIOR_MARKET_SESSION,
        regime_state_eligible=quality in USABLE_QUALITY,
        reason=reason,
    )


def _direction(value: object, threshold: float) -> int:
    if not isinstance(value, (int, float)):
        return 0
    if value >= threshold:
        return 1
    if value <= -threshold:
        return -1
    return 0


def _clamp(value: int) -> int:
    return max(-2, min(2, value))


def _daily_axes(
    observations: dict[str, dict[str, object]],
    decisions: dict[str, TemporalDecision],
) -> dict[str, int]:
    def value(code: str, field: str) -> object:
        decision = decisions.get(code)
        if decision is None or not decision.today_signal_eligible:
            return None
        return observations.get(code, {}).get(field)

    growth = _clamp(
        _direction(value("IWM", "change_pct"), 0.5)
        + _direction(value("SOXX", "change_pct"), 0.8)
    )
    inflation = _clamp(
        _direction(value("T10YIE", "change_value"), 0.05)
        + _direction(value("DCOILWTICO", "change_pct"), 2.0)
    )
    liquidity = _clamp(-_direction(value("DTWEXBGS", "change_pct"), 0.3))
    financial = _clamp(
        -_direction(value("DFII10", "change_value"), 0.05)
        - _direction(value("BAMLH0A0HYM2", "change_value"), 0.1)
    )
    risk = _clamp(
        _direction(value("SPY", "change_pct"), 0.5)
        + _direction(value("QQQ", "change_pct"), 0.7)
        - _direction(value("VIXCLS", "change_pct"), 5.0)
    )
    earnings = _clamp(_direction(value("SOXX", "change_pct"), 1.0))
    return {
        "growth_momentum": growth,
        "inflation_pressure": inflation,
        "liquidity_condition": liquidity,
        "financial_conditions": financial,
        "risk_appetite": risk,
        "earnings_momentum": earnings,
    }


def build_temporal_context(
    current_market_summary: object,
    previous_market_summary: object,
    *,
    as_of: datetime,
) -> dict[str, object]:
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)
    current = _observation_map(current_market_summary)
    previous = _observation_map(previous_market_summary)
    decisions = {
        code: classify_observation(item, previous.get(code), as_of=as_of)
        for code, item in current.items()
        if code in SUPPORTED_SERIES
    }
    session = us_market_session(as_of)
    current_series = sorted(
        code for code, decision in decisions.items() if decision.today_signal_eligible
    )
    prior_series = sorted(
        code for code, decision in decisions.items() if decision.prior_context_eligible
    )
    reference_series = sorted(
        code
        for code, decision in decisions.items()
        if decision.temporal_role == REFERENCE_LAGGING
    )
    suppressed_series = sorted(
        code
        for code, decision in decisions.items()
        if decision.temporal_role in {STALE_FOR_DAILY_SIGNAL, UNAVAILABLE}
    )
    return {
        "contract": TEMPORAL_CONTRACT,
        "as_of": as_of.isoformat(),
        "market_date": session.market_date.isoformat(),
        "market_session": session.session,
        "latest_completed_regular_session_date": (
            session.latest_completed_regular_session_date.isoformat()
        ),
        "decisions": {code: asdict(value) for code, value in decisions.items()},
        "current_series": current_series,
        "prior_market_session_series": prior_series,
        "reference_series": reference_series,
        "suppressed_series": suppressed_series,
        "has_current_observation": bool(current_series),
        "daily_axes": _daily_axes(current, decisions),
    }


def build_session_temporal_context(
    session: Session,
    *,
    briefing_date: date,
    as_of: datetime,
) -> dict[str, object]:
    latest: list[MacroObservation] = []
    for code in sorted(SUPPORTED_SERIES):
        row = session.exec(
            select(MacroObservation)
            .where(MacroObservation.series_code == code)
            .order_by(MacroObservation.observed_at.desc())
        ).first()
        if row is not None:
            latest.append(row)
    current = {
        "observations": [
            {
                "series_code": row.series_code,
                "observed_at": row.observed_at,
                "retrieved_at": row.retrieved_at,
                "quality_status": row.quality_status,
                "frequency": row.frequency,
                "market_session": row.market_session,
                "change_value": row.change_value,
                "change_pct": row.change_pct,
            }
            for row in latest
        ]
    }
    previous = session.exec(
        select(MacroBriefing)
        .where(
            MacroBriefing.briefing_date < briefing_date,
            MacroBriefing.briefing_type == "morning",
        )
        .order_by(MacroBriefing.briefing_date.desc())
    ).first()
    return build_temporal_context(
        current,
        previous.market_summary if previous is not None else {},
        as_of=as_of,
    )
