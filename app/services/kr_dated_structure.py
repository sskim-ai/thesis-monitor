"""Dated KR support/resistance display from the existing V3 rollout owner."""
from datetime import date

from app.services.dated_multiframe_research import period_end
from app.services.kr_price_structure_selective_rollout_service import (
    build_kr_price_structure_rollout_decision, build_kr_price_structure_runtime_context,
)

CONTRACT = "kr-v3-dated-reference-v1"


def from_completed_periods(*, ticker, cutoff, periods, observed_at, provider_limit, include_entry_zones=False):
    if set(periods) != {"daily", "weekly", "monthly"} or not all(periods.values()):
        return {}
    if periods["daily"][-1]["date"] != cutoff:
        return {}
    target = date.fromisoformat(cutoff)
    complete = {}
    last_completed = {}
    for tf, rows in periods.items():
        complete[tf] = [row for row in rows
                        if str(row.get("bar_state") or row.get("completion_state") or "").upper()
                        not in {"PARTIAL", "PROVISIONAL", "OPEN", "LIVE", "UNCONFIRMED", "UNKNOWN", "INVALID"}
                        and period_end(date.fromisoformat(row["date"]), tf, "kr") <= target]
        if not complete[tf]:
            return {}
        label = complete[tf][-1]["date"]
        last_completed[tf] = dict(label=label, session=period_end(date.fromisoformat(label), tf, "kr").isoformat())
    if last_completed["daily"]["session"] != cutoff:
        return {}
    ctx = build_kr_price_structure_runtime_context(ticker=ticker, cutoff=cutoff,
        raw_by_timeframe=complete, observed_at=observed_at, provider_limit=provider_limit,
        provider_native=True, include_entry_zones=include_entry_zones)
    if (ctx["as_of"] != cutoff or ctx["current_quote"] is not None
            or ctx["native_current_price_qualified"] is not False
            or ctx["partial_bar_used_for_pivot_confirmation"]):
        return {}
    entry = {}
    if (include_entry_zones and ctx.get('structure_basis_session') == cutoff
            and ctx.get('entry_zone_proposals')):
        entry = dict(v3_entry_proposals=ctx['entry_zone_proposals'],
                     v3_entry_basis_close=ctx.get('structure_basis_close'))
    rollout = build_kr_price_structure_rollout_decision(
        ctx, ticker=ticker, monitored_subject=True, enabled=True).to_dict()
    if rollout["render_validation_errors"]:
        return entry
    rendered_lines = (rollout.get("section") or "").splitlines()
    zones = []
    for binding in rollout["numeric_bindings"]:
        role, display = binding["semantic_type"], binding.get("display")
        label = "지지" if "SUPPORT" in role else "저항" if "RESISTANCE" in role else None
        if (not label or not display or binding["currency"] != "KRW"
                or binding["security_basis"] != f"KR:{ticker}"
                or binding["adjustment_basis"] != "provider_adjusted_price_v1"
                or not binding["source_refs"] or binding["raw_low"] is None or binding["raw_high"] is None):
            continue
        lines = [line for line in rendered_lines if label in line and display in line]
        if len(lines) == 1 and all(z["text"] != lines[0] for z in zones):
            zones.append(dict(text=lines[0], zone_id=binding["fact_ref"], role=role,
                              source_refs=binding["source_refs"], timeframes=binding["source_timeframes"]))
    return dict(contract=CONTRACT, as_of=date.fromisoformat(cutoff).isoformat(), ticker=ticker,
                adjustment_basis="provider_adjusted_price_v1", eligible_for_current_price=False,
                eligible_for_b2_timing=False, last_completed=last_completed, zones=zones, **entry) if zones else entry
