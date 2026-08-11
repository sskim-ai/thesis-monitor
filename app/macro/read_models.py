import json

from app.models.macro import (
    MacroBriefing,
    MacroEvent,
    MacroRegimeAssessment,
    MacroThesis,
    ThesisMacroImpact,
)
from app.schemas.macro import (
    MacroBriefingRead,
    MacroEventRead,
    MacroRegimeRead,
    MacroThesisRead,
    ThesisMacroImpactRead,
)


def _list(value: str) -> list:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def macro_event_to_read(row: MacroEvent) -> MacroEventRead:
    return MacroEventRead(
        event_key=row.event_key,
        event_type=row.event_type,
        category=row.category,
        title=row.title,
        country=row.country,
        scheduled_at=row.scheduled_at,
        released_at=row.released_at,
        event_status=row.event_status,
        actual=row.actual,
        consensus=row.consensus,
        previous=row.previous,
        revised_previous=row.revised_previous,
        unit=row.unit,
        surprise_value=row.surprise_value,
        surprise_score=row.surprise_score,
        impact_level=row.impact_level,
        confirmed_facts=_list(row.confirmed_facts),
        inferred_implications=_list(row.inferred_implications),
        unknowns=_list(row.unknowns),
        provider=row.provider,
        source_url=row.source_url,
        source_reliability=row.source_reliability,
    )


def macro_regime_to_read(row: MacroRegimeAssessment) -> MacroRegimeRead:
    return MacroRegimeRead(
        assessment_date=row.assessment_date,
        growth_momentum=row.growth_momentum,
        inflation_pressure=row.inflation_pressure,
        liquidity_condition=row.liquidity_condition,
        financial_conditions=row.financial_conditions,
        risk_appetite=row.risk_appetite,
        earnings_momentum=row.earnings_momentum,
        regime_label=row.regime_label,
        confidence=row.confidence,
        persistence_days=row.persistence_days,
        provisional=row.provisional,
        market_session=row.market_session,
        assessment_state=row.assessment_state,
        summary=row.summary,
        evidence=_list(row.evidence),
    )


def macro_thesis_to_read(row: MacroThesis) -> MacroThesisRead:
    return MacroThesisRead(
        thesis_key=row.thesis_key,
        version=row.version,
        title=row.title,
        description=row.description,
        region=row.region,
        horizon=row.horizon,
        status=row.status,
        today_signal=row.today_signal,
        today_signal_strength=row.today_signal_strength,
        today_signal_evidence=_list(row.today_signal_evidence),
        today_signal_rationale=row.today_signal_rationale,
        today_signal_date=row.today_signal_date,
        confidence=row.confidence,
        base_case_probability=row.base_case_probability,
        bull_case=row.bull_case,
        base_case=row.base_case,
        bear_case=row.bear_case,
        expected_evidence=_list(row.expected_evidence),
        weakening_evidence=_list(row.weakening_evidence),
        kill_conditions=_list(row.kill_conditions),
        valuation_channels=_list(row.valuation_channels),
        affected_assets=_list(row.affected_assets),
        last_reviewed_at=row.last_reviewed_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def macro_impact_to_read(row: ThesisMacroImpact) -> ThesisMacroImpactRead:
    return ThesisMacroImpactRead(
        ticker=row.ticker,
        thesis_version=row.thesis_version,
        assessment_date=row.assessment_date,
        direction=row.direction,
        magnitude=row.magnitude,
        persistence=row.persistence,
        confidence=row.confidence,
        channels=_list(row.channels),
        affected_thesis_pillars=_list(row.affected_thesis_pillars),
        earnings_effect=row.earnings_effect,
        valuation_effect=row.valuation_effect,
        rationale=row.rationale,
        evidence=_list(row.evidence),
    )


def macro_briefing_to_read(row: MacroBriefing) -> MacroBriefingRead:
    from app.macro.briefing import briefing_to_dict

    return MacroBriefingRead.model_validate(briefing_to_dict(row))
