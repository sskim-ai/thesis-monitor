"""Dated USD display from the existing US V3 owner, with no B2 authority."""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re

from app.services.dated_multiframe_research import period_end
from app.services.market_session import us_market_session
from app.services.us_price_structure_selective_rollout_service import (
    build_us_price_structure_rollout_decision, build_us_price_structure_runtime_context,
)

CONTRACT = "us-v3-dated-source-reference-v1"
FRAMES = {"daily", "weekly", "monthly"}
INCOMPLETE = {"PARTIAL", "PROVISIONAL", "OPEN", "LIVE", "UNCONFIRMED", "UNKNOWN", "INVALID"}
REFERENCE = re.compile(r"[a-zA-Z0-9_:.-]{1,100}\Z")


def attach(structure, *, enabled, ticker, security_id, generation, cutoff, observed_at, periods, receipts, provider_limit):
    if not enabled:
        return structure
    target = date.fromisoformat(cutoff)
    now = datetime.fromisoformat(observed_at)
    if (now.utcoffset() is None
            or us_market_session(now).latest_completed_regular_session_date != target
            or set(periods) != FRAMES or ticker.isdigit()):
        return structure
    complete, evidence = {}, {}
    for tf in sorted(FRAMES):
        receipt = receipts[f"adjusted_{tf}"]
        entry = receipt["entry"]
        pin = receipt["normalized_sha256"]
        if (entry["market"] != "us" or entry["subject"] != ticker
                or entry["canonical_security_id"] != security_id or entry["adjusted"] is not True
                or entry["latest_completed_session"] != cutoff or receipt["run_id"] != generation
                or not re.fullmatch(r"[a-f0-9]{64}", pin)):
            return structure
        good = []
        for row in periods[tf]:
            label = date.fromisoformat(row["date"])
            marker = str(row.get("bar_state") or row.get("completion_state") or "").upper()
            if marker not in INCOMPLETE and label <= target and period_end(label, tf, "us") <= target:
                good.append(row)
        if not good:
            return structure
        dates = [r["date"] for r in good]
        if dates != sorted(set(dates)) or tf == "daily" and dates[-1] != cutoff:
            return structure
        complete[tf] = good
        evidence[tf] = dict(label=dates[-1], completed=period_end(date.fromisoformat(dates[-1]), tf, "us").isoformat(),
                            normalized_sha256=pin)
    context = build_us_price_structure_runtime_context(ticker=ticker, cutoff=cutoff,
        raw_by_timeframe=complete, observed_at=observed_at, provider_limit=provider_limit, provider_native=True)
    if (context.get("as_of") != cutoff or context.get("current_quote") is not None
            or context.get("native_current_price_qualified") is not False
            or context.get("partial_bar_used_for_pivot_confirmation") != 0):
        return structure
    rollout = build_us_price_structure_rollout_decision(context, ticker=ticker, monitored_subject=True, enabled=True)
    if rollout.render_validation_errors:
        return structure
    zones, used = [], set()
    for b in rollout.numeric_bindings:
        role = str(b.get("semantic_type") or "")
        ref, refs = b.get("fact_ref"), tuple(b.get("source_refs") or ())
        side = "support" if "SUPPORT" in role else "resistance" if "RESISTANCE" in role else None
        frames = tuple(b.get("source_timeframes") or ())
        if (side is None or ref not in rollout.displayed_zone_ids or ref in used
                or b.get("currency") != "USD" or b.get("security_basis") != f"US_LISTED:{ticker}"
                or b.get("as_of") != cutoff
                or b.get("adjustment_basis") != "provider_adjusted_price_v1"
                or not refs or not frames or not set(frames) <= FRAMES
                or not all(isinstance(x, str) and REFERENCE.fullmatch(x) for x in (ref, *refs))):
            continue
        try:
            low, high = Decimal(str(b["raw_low"])), Decimal(str(b["raw_high"]))
        except (KeyError, InvalidOperation):
            continue
        if not low.is_finite() or not high.is_finite() or not 0 < low <= high:
            continue
        zones.append(dict(id=ref, side=side, tier="major" if role.startswith("MAJOR_") else "near",
                          low=str(low), high=str(high), source_refs=list(refs),
                          timeframes=list(frames)))
        used.add(ref)
    if not zones:
        return structure
    return dict(structure, price_structure_v3=dict(contract=CONTRACT,
        scope="DATED_REFERENCE_ONLY", ticker=ticker, security_id=security_id, source_generation=generation,
        as_of=cutoff, currency="USD", adjustment_basis="provider_adjusted_price_v1", completed_sources=evidence,
        eligible_for_current_price=False, eligible_for_b2_timing=False, zones=zones[:4]))
