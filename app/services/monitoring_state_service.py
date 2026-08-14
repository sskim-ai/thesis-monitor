from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import date
from statistics import mean, median
from typing import Iterable, Mapping

from sqlmodel import Session, select

from app.config import get_settings
from app.models.company import Company
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.services.company_profile_service import read_profile_provenance


MONITORING_STATE_VERSION = "monitoring-state-v1"
PEER_GROUP_VERSION = "verified-profile-peers-v1"
MINIMUM_PEER_SAMPLE = 3
_COMPARABLE_BASIS = {"directly_comparable", "normalized_to_current_security"}
_PE_UNSUITABLE_PROFILE_TOKENS = {
    "biotech",
    "biotechnology",
    "drug_discovery",
    "life_sciences",
    "pharmaceutical",
    "pharmaceuticals",
}


def _dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return {}
    try:
        parsed = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _number(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = float(value)
        return number if math.isfinite(number) else None
    return None


def _normalized_label(value: object) -> str | None:
    text = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return text or None


def stable_zone_id(zone: Mapping[str, object], role: str) -> str:
    identity = {
        "timeframe": str(zone.get("timeframe") or "unknown"),
        "pivot_dates": sorted(str(item) for item in zone.get("pivot_dates", []) or []),
        "pivot_type": str(zone.get("pivot_type") or "unknown"),
        "role": role,
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:16]
    return f"zone:{identity['timeframe']}:{role}:{digest}"


def _zone_snapshot(zone: Mapping[str, object] | None, role: str) -> dict[str, object]:
    if zone is None:
        return {
            "available": False,
            "zone_low": None,
            "zone_high": None,
            "strength": None,
            "timeframe": None,
            "zone_id": None,
            "source": "dynamic",
        }
    return {
        "available": True,
        "zone_low": _number(zone.get("zone_low")),
        "zone_high": _number(zone.get("zone_high")),
        "center": _number(zone.get("center")),
        "strength": str(zone.get("strength") or "unknown"),
        "timeframe": str(zone.get("timeframe") or "unknown"),
        "zone_id": stable_zone_id(zone, role),
        "source": "dynamic",
        "pivot_dates": sorted(str(item) for item in zone.get("pivot_dates", []) or []),
        **{
            key: zone[key]
            for key in (
                "distance_pct",
                "distance_to_lower_pct",
                "distance_to_upper_pct",
                "score",
            )
            if zone.get(key) is not None
        },
    }


def _nearest_meaningful_zones(
    structure: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    zones = _dict(structure.get("zones"))
    active = [
        item
        for item in zones.get("active", []) or []
        if isinstance(item, dict) and item.get("strength") in {"Strong", "Medium"}
    ]
    supports = [
        item
        for item in zones.get("support", []) or []
        if isinstance(item, dict) and item.get("strength") in {"Strong", "Medium"}
    ]
    resistances = [
        item
        for item in zones.get("resistance", []) or []
        if isinstance(item, dict) and item.get("strength") in {"Strong", "Medium"}
    ]
    support = active[0] if active else supports[0] if supports else None
    resistance = resistances[0] if resistances else None
    return _zone_snapshot(support, "support"), _zone_snapshot(resistance, "resistance")


def _supply_state(raw: Mapping[str, object]) -> dict[str, object]:
    if raw.get("available") is not True:
        return {"available": False, "reason": "verified_supply_unavailable"}

    def pair(horizon: str) -> tuple[float | None, float | None]:
        suffix = "" if horizon == "1d" else "_5" if horizon == "5d" else "_20"
        return (
            _number(raw.get(f"foreign_net_buy_qty{suffix}")),
            _number(raw.get(f"institution_net_buy_qty{suffix}")),
        )

    def classify(values: tuple[float | None, float | None]) -> str:
        foreign, institution = values
        if foreign is None or institution is None:
            return "unavailable"
        if foreign > 0 and institution > 0:
            return "joint_buying"
        if foreign < 0 and institution < 0:
            return "joint_selling"
        return "mixed"

    one_day = pair("1d")
    five_day = pair("5d")
    twenty_day = pair("20d")
    short_term = classify(five_day)
    medium_term = classify(twenty_day)
    transition = (
        "aligned"
        if short_term == medium_term and short_term != "unavailable"
        else "short_term_divergence"
        if "unavailable" not in {short_term, medium_term}
        else "unavailable"
    )
    return {
        "available": True,
        "as_of_date": raw.get("as_of_date"),
        "one_day": {
            "foreign": one_day[0],
            "institution": one_day[1],
            "state": classify(one_day),
        },
        "five_day": {
            "foreign": five_day[0],
            "institution": five_day[1],
            "state": short_term,
        },
        "twenty_day": {
            "foreign": twenty_day[0],
            "institution": twenty_day[1],
            "state": medium_term,
        },
        "short_term": short_term,
        "medium_term": medium_term,
        "transition": transition,
        "quality": raw.get("quality"),
        "source": "verified_investor_flow",
    }


def _valuation_state(snapshot: Mapping[str, object]) -> dict[str, object]:
    pe_stats = _dict(snapshot.get("historical_pe_statistics"))
    pb_stats = _dict(snapshot.get("historical_pb_statistics"))
    return {
        key: value
        for key, value in {
            "as_of_date": snapshot.get("price_as_of"),
            "trailing_pe": _number(snapshot.get("trailing_pe")),
            "price_to_book": _number(snapshot.get("price_to_book")),
            "forward_pe": _number(snapshot.get("forward_pe")),
            "forward_price_to_book": _number(snapshot.get("forward_price_to_book")),
            "forward_pe_source": snapshot.get("forward_pe_source"),
            "historical_comparability": snapshot.get("historical_comparability"),
            "historical_pe_percentile": _number(pe_stats.get("current_percentile")),
            "historical_pb_percentile": _number(pb_stats.get("current_percentile")),
            "latest_earnings_period": snapshot.get("latest_earnings_period"),
            "latest_revenue": _number(snapshot.get("latest_revenue")),
            "latest_operating_income": _number(snapshot.get("latest_operating_income")),
            "latest_operating_margin": _number(snapshot.get("latest_operating_margin")),
            "currency": snapshot.get("currency"),
        }.items()
        if value is not None
    }


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return round(ordered[lower], 4)
    weight = position - lower
    return round(ordered[lower] * (1 - weight) + ordered[upper] * weight, 4)


def _metric_value(
    snapshot: Mapping[str, object], metric: str, assessment_date: date
) -> tuple[float | None, str | None]:
    status_field = "trailing_pe_status" if metric == "trailing_pe" else "price_to_book_status"
    basis_field = (
        "trailing_pe_basis_status"
        if metric == "trailing_pe"
        else "price_to_book_basis_status"
    )
    denominator_field = (
        "trailing_pe_denominator_filing_date"
        if metric == "trailing_pe"
        else "pbr_denominator_filing_date"
    )
    value = _number(snapshot.get(metric))
    if value is None or value <= 0:
        return None, "non_positive_or_missing_denominator"
    denominator_field_name = "ttm_eps" if metric == "trailing_pe" else "bvps"
    denominator = _number(snapshot.get(denominator_field_name))
    if denominator is None or denominator <= 0:
        return None, f"non_positive_or_missing_{denominator_field_name}"
    if str(snapshot.get(status_field) or "") != "value":
        return None, "metric_status_not_value"
    if str(snapshot.get(basis_field) or "") not in _COMPARABLE_BASIS:
        return None, "security_or_share_basis_not_comparable"
    price_as_of = str(snapshot.get("price_as_of") or "")[:10]
    if price_as_of != assessment_date.isoformat():
        return None, "stale_or_mismatched_price_date"
    filing_date = str(snapshot.get(denominator_field) or "")[:10]
    if filing_date and filing_date > assessment_date.isoformat():
        return None, "future_denominator_filing"
    return value, None


def _metric_allowed_for_profile(
    metric: str, profile: Mapping[str, str | None]
) -> bool:
    if metric != "trailing_pe":
        return True
    labels = {
        token
        for value in profile.values()
        if value
        for token in str(value).split("_")
    }
    combined = "_".join(str(value) for value in profile.values() if value)
    return not (
        labels & _PE_UNSUITABLE_PROFILE_TOKENS
        or any(token in combined for token in _PE_UNSUITABLE_PROFILE_TOKENS)
    )


def _profile_key(company: Company) -> dict[str, str | None]:
    provenance = read_profile_provenance(company.ticker, get_settings().data_dir) or {}
    quality = str(provenance.get("quality") or "unavailable")
    if quality != "verified":
        return {"quality": quality, "taxonomy": None, "industry": None, "sector": None}
    return {
        "quality": quality,
        "taxonomy": _normalized_label(provenance.get("taxonomy_key")),
        "industry": _normalized_label(company.industry),
        "sector": _normalized_label(company.sector),
    }


def _market(company: Company) -> str:
    return "kr" if company.ticker.isdigit() or (company.exchange or "").upper() == "KRX" else "us"


def build_peer_valuation_states(
    session: Session,
    assessments: Iterable[ThesisAssessment],
    assessment_date: date,
) -> dict[str, dict[str, object]]:
    rows = list(assessments)
    tickers = {row.ticker for row in rows}
    companies = {
        item.ticker: item
        for item in session.exec(select(Company).where(Company.ticker.in_(tickers))).all()
    }
    snapshots = {row.ticker: _dict(row.valuation_snapshot) for row in rows}
    profiles = {
        ticker: _profile_key(company) for ticker, company in companies.items()
    }
    results: dict[str, dict[str, object]] = {}
    for row in rows:
        company = companies.get(row.ticker)
        profile = profiles.get(row.ticker, {})
        if company is None or profile.get("quality") != "verified":
            results[row.ticker] = {
                "available": False,
                "reason": "verified_company_profile_unavailable",
                "provider": "validated_active_monitoring_assessments",
            }
            continue
        market = _market(company)
        group_basis = None
        group_value = None
        candidate_tickers: list[str] = []
        for basis in ("taxonomy", "industry", "sector"):
            value = profile.get(basis)
            if not value:
                continue
            matches = [
                ticker
                for ticker, candidate in companies.items()
                if ticker != row.ticker
                and _market(candidate) == market
                and profiles.get(ticker, {}).get("quality") == "verified"
                and profiles.get(ticker, {}).get(basis) == value
            ]
            if len(matches) >= MINIMUM_PEER_SAMPLE:
                group_basis = basis
                group_value = value
                candidate_tickers = sorted(matches)
                break
        if group_basis is None:
            results[row.ticker] = {
                "available": False,
                "reason": "insufficient_verified_peer_universe",
                "provider": "validated_active_monitoring_assessments",
                "minimum_sample": MINIMUM_PEER_SAMPLE,
                "profile_quality": profile.get("quality"),
            }
            continue
        metrics: dict[str, object] = {}
        audit: dict[str, object] = {"included": {}, "excluded": {}}
        company_snapshot = snapshots.get(row.ticker, {})
        for metric in ("trailing_pe", "price_to_book"):
            if not _metric_allowed_for_profile(metric, profile):
                metrics[metric] = {
                    "available": False,
                    "sample_count": 0,
                    "reason": "industry_metric_not_primary",
                }
                audit["included"][metric] = []  # type: ignore[index]
                audit["excluded"][metric] = []  # type: ignore[index]
                continue
            values: list[float] = []
            included: list[str] = []
            excluded: list[dict[str, str]] = []
            for ticker in candidate_tickers:
                value, reason = _metric_value(
                    snapshots.get(ticker, {}), metric, assessment_date
                )
                if value is None:
                    excluded.append({"ticker": ticker, "reason": reason or "unavailable"})
                else:
                    values.append(value)
                    included.append(ticker)
            audit["included"][metric] = included  # type: ignore[index]
            audit["excluded"][metric] = excluded  # type: ignore[index]
            company_value, company_reason = _metric_value(
                company_snapshot, metric, assessment_date
            )
            if len(values) < MINIMUM_PEER_SAMPLE or company_value is None:
                metrics[metric] = {
                    "available": False,
                    "sample_count": len(values),
                    "reason": (
                        company_reason
                        if company_value is None
                        else "insufficient_comparable_metric_sample"
                    ),
                }
                continue
            peer_median = float(median(values))
            metrics[metric] = {
                "available": True,
                "company_value": round(company_value, 4),
                "median": round(peer_median, 4),
                "mean": round(mean(values), 4),
                "percentile_25": _percentile(values, 0.25),
                "percentile_75": _percentile(values, 0.75),
                "sample_count": len(values),
                "company_vs_median_pct": round(
                    (company_value / peer_median - 1) * 100, 4
                ),
            }
        available = any(
            isinstance(value, dict) and value.get("available") is True
            for value in metrics.values()
        )
        results[row.ticker] = {
            "available": available,
            "as_of_date": assessment_date.isoformat(),
            "provider": "validated_active_monitoring_assessments",
            "peer_group": f"{market}_{group_basis}_{group_value}",
            "peer_group_version": PEER_GROUP_VERSION,
            "group_basis": group_basis,
            "group_value": group_value,
            "minimum_sample": MINIMUM_PEER_SAMPLE,
            "sample_quality": "sufficient" if available else "limited",
            "metrics": metrics,
            "audit": audit,
        }
    return results


def _confirmation_history(
    session: Session,
    assessment: ThesisAssessment,
    confirmation_price: float | None,
) -> tuple[str | None, int]:
    if confirmation_price is None:
        return None, 0
    rows = list(
        session.exec(
            select(ThesisAssessment)
            .where(
                ThesisAssessment.ticker == assessment.ticker,
                ThesisAssessment.thesis_version == assessment.thesis_version,
                ThesisAssessment.assessment_date <= assessment.assessment_date,
                ThesisAssessment.assessment_state == "final",
            )
            .order_by(ThesisAssessment.assessment_date, ThesisAssessment.id)
        ).all()
    )
    crossed_at: str | None = None
    sessions_above = 0
    previous_price: float | None = None
    for row in rows:
        price = _number(_dict(_dict(row.price_context).get("decision")).get("current_price"))
        if price is None:
            continue
        if price >= confirmation_price:
            sessions_above += 1
            if (
                crossed_at is None
                and previous_price is not None
                and previous_price < confirmation_price
            ):
                crossed_at = row.assessment_date.isoformat()
        else:
            sessions_above = 0
            crossed_at = None
        previous_price = price
    return crossed_at, sessions_above


def _registered_rule_state(
    rules: Mapping[str, object],
    current_price: float | None,
    previous_price: float | None,
    active_support: Mapping[str, object],
    *,
    crossed_at: str | None,
    sessions_above: int,
    previous_lifecycle: str | None,
) -> dict[str, object]:
    confirmation = _number(rules.get("confirmation_price"))
    lifecycle = "not_configured"
    if confirmation is not None and current_price is not None:
        if current_price < confirmation:
            lifecycle = (
                "failed_breakout"
                if previous_price is not None and previous_price >= confirmation
                else "not_reached"
            )
        elif previous_price is not None and previous_price < confirmation:
            lifecycle = "crossed"
        else:
            support_low = _number(active_support.get("zone_low"))
            support_high = _number(active_support.get("zone_high"))
            retest = (
                support_low is not None
                and support_high is not None
                and support_low <= confirmation <= support_high
                and support_low <= current_price <= support_high
            )
            if retest:
                lifecycle = "retest_in_progress"
            elif previous_lifecycle == "retest_in_progress":
                lifecycle = "retest_held"
            else:
                lifecycle = "holding_above"
    confirmation_relevance = (
        "unavailable"
        if lifecycle == "not_configured"
        else
        "active"
        if lifecycle in {"not_reached", "crossed", "retest_in_progress", "failed_breakout"}
        else "transition_reference"
        if lifecycle == "retest_held" or sessions_above <= 2
        else "background"
    )
    dynamic_support_available = active_support.get("available") is True
    return {
        "confirmation": {
            "price": confirmation,
            "state": lifecycle,
            "relevance": confirmation_relevance,
            "crossed_at": crossed_at,
            "final_sessions_above": sessions_above,
            "automatically_promoted_to_support": False,
        },
        "support": {
            "zone_low": _number(rules.get("support_zone_low")),
            "zone_high": _number(rules.get("support_zone_high")),
            "relevance": (
                "superseded_for_current_structure"
                if dynamic_support_available
                else "background"
            ),
        },
        "warning": {
            "price": _number(rules.get("warning_price")),
            "relevance": "active" if rules.get("warning_price") is not None else "unavailable",
        },
        "invalidation": {
            "price": _number(rules.get("invalidation_price")),
            "relevance": "thesis_reference" if rules.get("invalidation_price") is not None else "unavailable",
            "chart_invalidation": False,
        },
    }


def _previous_assessment(
    session: Session, assessment: ThesisAssessment
) -> ThesisAssessment | None:
    return session.exec(
        select(ThesisAssessment)
        .where(
            ThesisAssessment.ticker == assessment.ticker,
            ThesisAssessment.assessment_date < assessment.assessment_date,
            ThesisAssessment.assessment_state == "final",
        )
        .order_by(ThesisAssessment.assessment_date.desc(), ThesisAssessment.id.desc())
    ).first()


def _state_from_assessment(assessment: ThesisAssessment | None) -> dict[str, object]:
    if assessment is None:
        return {}
    context = _dict(assessment.price_context)
    monitoring = _dict(context.get("monitoring_state"))
    current = monitoring.get("current")
    if isinstance(current, dict):
        return current
    structure = _dict(_dict(context.get("chart")).get("structure"))
    support, resistance = _nearest_meaningful_zones(structure)
    return {
        "price_structure": {
            "as_of_date": _dict(context.get("decision")).get("price_as_of"),
            "engine_version": structure.get("algorithm_version"),
            "current_price": _number(_dict(context.get("decision")).get("current_price")),
            "active_support": support,
            "active_resistance": resistance,
            "risk_reward": _dict(structure.get("risk_reward")),
            "chart_invalidation": _dict(structure.get("invalidation")),
            "chart_state": _dict(structure.get("chart_state")),
        },
        "supply": _supply_state(_dict(context.get("supply"))),
        "valuation": _valuation_state(_dict(assessment.valuation_snapshot)),
    }


def _zone_change(
    current: Mapping[str, object], previous: Mapping[str, object]
) -> str:
    if current.get("available") is not True:
        return "unavailable" if previous.get("available") is not True else "became_unavailable"
    if previous.get("available") is not True:
        return "new"
    if current.get("zone_id") == previous.get("zone_id"):
        return "unchanged"
    current_center = _number(current.get("center"))
    previous_center = _number(previous.get("center"))
    if current_center is None or previous_center is None:
        return "replaced"
    return "shifted_up" if current_center > previous_center else "shifted_down"


def _state_delta(
    current: Mapping[str, object], previous: Mapping[str, object]
) -> dict[str, object]:
    price = _dict(current.get("price_structure"))
    previous_price = _dict(previous.get("price_structure"))
    rule_state = _dict(_dict(price.get("registered_rule_state")).get("confirmation"))
    previous_rule_state = _dict(
        _dict(previous_price.get("registered_rule_state")).get("confirmation")
    )
    current_rr = _number(_dict(_dict(price.get("risk_reward")).get("current_price")).get("ratio"))
    previous_rr = _number(
        _dict(_dict(previous_price.get("risk_reward")).get("current_price")).get("ratio")
    )
    rr_change = "unavailable"
    if current_rr is not None and previous_rr is not None:
        rr_change = "improved" if current_rr > previous_rr else "deteriorated" if current_rr < previous_rr else "unchanged"
    elif current_rr is not None:
        rr_change = "became_available"
    elif previous_rr is not None:
        rr_change = "became_unavailable"
    valuation = _dict(current.get("valuation"))
    previous_valuation = _dict(previous.get("valuation"))
    pe_pct = _number(valuation.get("historical_pe_percentile"))
    previous_pe_pct = _number(previous_valuation.get("historical_pe_percentile"))
    return {
        "baseline": not bool(previous),
        "confirmation_transition": (
            f"{previous_rule_state.get('state', 'baseline')}_to_{rule_state.get('state', 'unavailable')}"
        ),
        "support_change": _zone_change(
            _dict(price.get("active_support")),
            _dict(previous_price.get("active_support")),
        ),
        "resistance_change": _zone_change(
            _dict(price.get("active_resistance")),
            _dict(previous_price.get("active_resistance")),
        ),
        "rr_change": rr_change,
        "rr_previous": previous_rr,
        "rr_current": current_rr,
        "chart_state_change": (
            f"{_dict(previous_price.get('chart_state')).get('state', 'baseline')}_to_"
            f"{_dict(price.get('chart_state')).get('state', 'unavailable')}"
        ),
        "supply_transition": _dict(current.get("supply")).get("transition"),
        "valuation_change": (
            "more_expensive"
            if pe_pct is not None and previous_pe_pct is not None and pe_pct > previous_pe_pct
            else "less_expensive"
            if pe_pct is not None and previous_pe_pct is not None and pe_pct < previous_pe_pct
            else "unchanged_or_unavailable"
        ),
        "historical_pe_percentile_previous": previous_pe_pct,
        "historical_pe_percentile_current": pe_pct,
    }


def build_monitoring_state(
    session: Session,
    assessment: ThesisAssessment,
    thesis: InvestmentThesis,
    peer_valuation: Mapping[str, object],
) -> dict[str, object]:
    context = _dict(assessment.price_context)
    decision = _dict(context.get("decision"))
    structure = _dict(_dict(context.get("chart")).get("structure"))
    support, resistance = _nearest_meaningful_zones(structure)
    previous_assessment = _previous_assessment(session, assessment)
    previous = _state_from_assessment(previous_assessment)
    previous_price = _dict(previous.get("price_structure"))
    current_price = _number(decision.get("current_price"))
    previous_current_price = _number(previous_price.get("current_price"))
    rules = _dict(thesis.price_rules)
    confirmation = _number(rules.get("confirmation_price"))
    crossed_at, sessions_above = _confirmation_history(
        session, assessment, confirmation
    )
    if previous_assessment is not None and not previous_price.get(
        "registered_rule_state"
    ):
        previous_previous = _previous_assessment(session, previous_assessment)
        previous_previous_price = _number(
            _dict(_dict(previous_previous.price_context).get("decision")).get(
                "current_price"
            )
        ) if previous_previous is not None else None
        previous_crossed_at, previous_sessions_above = _confirmation_history(
            session,
            previous_assessment,
            confirmation,
        )
        previous_price["registered_rule_state"] = _registered_rule_state(
            rules,
            previous_current_price,
            previous_previous_price,
            _dict(previous_price.get("active_support")),
            crossed_at=previous_crossed_at,
            sessions_above=previous_sessions_above,
            previous_lifecycle=None,
        )
        previous["price_structure"] = previous_price
    previous_lifecycle = _dict(
        _dict(previous_price.get("registered_rule_state")).get("confirmation")
    ).get("state")
    if (
        previous_assessment is not None
        and previous_assessment.thesis_version != assessment.thesis_version
    ):
        previous_lifecycle = None
    current = {
        "price_structure": {
            "as_of_date": decision.get("price_as_of"),
            "engine_version": structure.get("algorithm_version"),
            "price_basis": _dict(context.get("chart")).get("price_basis"),
            "current_price": current_price,
            "active_support": support,
            "active_resistance": resistance,
            "risk_reward": _dict(structure.get("risk_reward")),
            "chart_invalidation": _dict(structure.get("invalidation")),
            "chart_state": _dict(structure.get("chart_state")),
            "registered_rule_state": _registered_rule_state(
                rules,
                current_price,
                previous_current_price,
                support,
                crossed_at=crossed_at,
                sessions_above=sessions_above,
                previous_lifecycle=(str(previous_lifecycle) if previous_lifecycle else None),
            ),
            "structure_quality": {
                "chart_quality": _dict(context.get("chart")).get("quality"),
                "unavailable_fields": _dict(context.get("chart")).get("unavailable_fields", []),
            },
        },
        "supply": _supply_state(_dict(context.get("supply"))),
        "valuation": _valuation_state(_dict(assessment.valuation_snapshot)),
        "peer_valuation": dict(peer_valuation),
        "market_expectation": _dict(assessment.market_expectation_assessment),
        "macro": {
            key: value
            for key, value in _dict(assessment.valuation_context).items()
            if key in {"macro_valuation_effect", "macro_valuation_effects"}
        },
    }
    return {
        "version": MONITORING_STATE_VERSION,
        "ticker": assessment.ticker,
        "thesis_version": assessment.thesis_version,
        "assessment_date": assessment.assessment_date.isoformat(),
        "previous_assessment_id": (
            previous_assessment.id if previous_assessment is not None else None
        ),
        "current": current,
        "previous": previous,
        "delta": _state_delta(current, previous),
    }


def persist_monitoring_states(
    session: Session,
    assessments: Iterable[ThesisAssessment],
    assessment_date: date,
) -> None:
    rows = list(assessments)
    if not rows:
        return
    active_tickers = list(
        session.exec(select(WatchlistItem.ticker).where(WatchlistItem.active.is_(True))).all()
    )
    peer_rows = (
        list(
            session.exec(
                select(ThesisAssessment).where(
                    ThesisAssessment.assessment_date == assessment_date,
                    ThesisAssessment.assessment_state == "final",
                    ThesisAssessment.ticker.in_(active_tickers),
                )
            ).all()
        )
        if active_tickers
        else rows
    )
    peer_states = build_peer_valuation_states(session, peer_rows, assessment_date)
    theses = {
        (item.ticker, item.version): item
        for item in session.exec(
            select(InvestmentThesis).where(
                InvestmentThesis.ticker.in_({row.ticker for row in rows})
            )
        ).all()
    }
    for assessment in rows:
        thesis = theses.get((assessment.ticker, assessment.thesis_version))
        if thesis is None:
            raise ValueError(f"active thesis snapshot unavailable: {assessment.ticker}")
        context = _dict(assessment.price_context)
        context["monitoring_state"] = build_monitoring_state(
            session,
            assessment,
            thesis,
            peer_states.get(
                assessment.ticker,
                {"available": False, "reason": "peer_state_unavailable"},
            ),
        )
        assessment.price_context = json.dumps(context, ensure_ascii=False)
        session.add(assessment)
    session.commit()
