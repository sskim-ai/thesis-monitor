"""Dated USD display from the existing US V3 owner, with no B2 authority."""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re

from app.services.dated_multiframe_research import period_end
from app.services.market_session import us_market_session, preceding_exchange_session_date
from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows
from app.services.price_structure_wave_fibonacci_v3_service import normalize_completed_bars
from app.services.unified_snapshot_contract import digest
from app.services.us_price_structure_selective_rollout_service import (
    build_us_price_structure_rollout_decision, build_us_price_structure_runtime_context,
)

CONTRACT = "us-v3-dated-source-reference-v1"
FRAMES = {"daily", "weekly", "monthly"}
INCOMPLETE = {"PARTIAL", "PROVISIONAL", "OPEN", "LIVE", "UNCONFIRMED", "UNKNOWN", "INVALID"}
REFERENCE = re.compile(r"[a-zA-Z0-9_:.-]{1,100}\Z")


def valid_reference_lineage(ref):
    """A single rejected target row may date an independent historical reference."""
    target, reference = ref.get('target_session'), ref.get('as_of')
    if not isinstance(target,str) or not isinstance(reference,str):
        return False
    proof = ref.get('latest_daily_exclusion')
    if reference == target:
        return proof is None
    if not isinstance(proof, dict) or ref.get('reference_as_of') != reference:
        return False
    try:
        excluded, used = proof['excluded_row'], proof['reference_row']
        return (str(preceding_exchange_session_date('XNYS',date.fromisoformat(target))) == reference
            and proof['reason'] == 'LOW_GT_CLOSE' and excluded['date'] == target and used['date'] == reference
            and digest(excluded) == proof['excluded_row_sha256'] and digest(used) == proof['reference_row_sha256']
            and {str(i.violation) for i in inspect_normalized_ohlcv_rows([excluded],timeframe='daily').issues} == {'LOW_GT_CLOSE'}
            and inspect_normalized_ohlcv_rows([used],timeframe='daily',cutoff=date.fromisoformat(reference)).valid
            and proof['source_generation'] == ref['source_generation'] and proof['security_id'] == ref['security_id']
            and proof['source_plan_sha256'] == ref['source_plan_sha256']
            and set(proof['role_lineage']) == FRAMES
            and len({p['acquisition_id'] for p in proof['role_lineage'].values()}) == 1
            and all(p['acquisition_id'] and p['source_plan_sha256'] == ref['source_plan_sha256']
                and all(p[k] == ref['completed_sources'][tf][k] for k in ('receipt_sha256','normalized_sha256','original_rows_sha256'))
                for tf,p in proof['role_lineage'].items()))
    except (KeyError, TypeError, ValueError):
        return False


def attach(structure, *, enabled, ticker, security_id, generation, cutoff, observed_at, periods, receipts, provider_limit,
           include_entry_zones=False):
    if not enabled:
        return structure
    target = date.fromisoformat(cutoff)
    now = datetime.fromisoformat(observed_at)
    if (now.utcoffset() is None
            or us_market_session(now).latest_completed_regular_session_date != target
            or set(periods) != FRAMES or ticker.isdigit()):
        return structure
    reference, exclusion = cutoff, None
    daily = periods['daily']
    normalized_daily = normalize_completed_bars(daily,cutoff=cutoff,timeframe='daily',market='US',observed_at=observed_at)
    if normalized_daily and normalized_daily[-1].date != cutoff:
        previous = preceding_exchange_session_date('XNYS',target)
        bad = [r for r in daily if r['date'] == cutoff]
        if (not daily or daily[-1]['date'] != cutoff or len(bad) != 1 or previous is None
                or normalized_daily[-1].date != previous.isoformat()
                or str(bad[0].get('bar_state') or bad[0].get('completion_state') or '').upper() in INCOMPLETE
                or {str(i.violation) for i in inspect_normalized_ohlcv_rows(bad,timeframe='daily').issues} != {'LOW_GT_CLOSE'}):
            return structure
        reference = previous.isoformat()
        used = next(r for r in daily if r['date'] == reference)
        exclusion = dict(reason='LOW_GT_CLOSE',excluded_row=bad[0],excluded_row_sha256=digest(bad[0]),
            reference_row=used,reference_row_sha256=digest(used),source_generation=generation,security_id=security_id)
    reference_target = date.fromisoformat(reference)
    complete, evidence = {}, {}
    plan_hashes = set()
    acquisitions = set()
    for tf in sorted(FRAMES):
        receipt = receipts[f"adjusted_{tf}"]
        entry = receipt["entry"]
        pin = receipt["normalized_sha256"]
        if (entry["market"] != "us" or entry["subject"] != ticker
                or entry["canonical_security_id"] != security_id or entry["adjusted"] is not True
                or entry["latest_completed_session"] != cutoff or receipt["run_id"] != generation
                or entry.get("timeframe") != tf or entry.get("role") != "adjusted_" + tf
                or receipt.get("status") != "CAPTURED" or not receipt.get("pages")
                or not re.fullmatch(r"[a-f0-9]{64}", receipt.get("plan_sha256", ""))
                or not re.fullmatch(r"[a-f0-9]{64}", pin)):
            return structure
        plan_hashes.add(receipt["plan_sha256"])
        acquisitions.add(receipt.get("acquisition_id"))
        original = periods[tf]
        original_dates = [r["date"] for r in original]
        if original_dates != sorted(set(original_dates)):
            return structure
        normalized = normalize_completed_bars(original, cutoff=reference, timeframe=tf,
            market="US", observed_at=observed_at)
        by_date = {bar.date: bar for bar in normalized}
        good = []
        for row in original:
            label = date.fromisoformat(row["date"])
            marker = str(row.get("bar_state") or row.get("completion_state") or "").upper()
            bar = by_date.get(row["date"])
            if (marker not in INCOMPLETE and bar is not None and bar.bar_state == "COMPLETE"
                    and label <= reference_target and period_end(label, tf, "us") <= reference_target):
                good.append(row)
        if not good or not inspect_normalized_ohlcv_rows(good, timeframe=tf, cutoff=reference_target).valid:
            return structure
        dates = [r["date"] for r in good]
        if dates != sorted(set(dates)) or tf == "daily" and dates[-1] != reference:
            return structure
        complete[tf] = good
        evidence[tf] = dict(label=dates[-1], completed=period_end(date.fromisoformat(dates[-1]), tf, "us").isoformat(),
            normalized_sha256=pin, receipt_sha256=digest(receipt), source_role="adjusted_" + tf,
            original_rows_sha256=digest(original), completed_rows_sha256=digest(good),
            completed_count=len(good), calendar=by_date[dates[-1]].market_calendar,
            completion_owner="normalize_completed_bars", bar_state="COMPLETE")
    if len(plan_hashes) != 1 or len(acquisitions) != 1 or not next(iter(acquisitions)):
        return structure
    context = build_us_price_structure_runtime_context(ticker=ticker, cutoff=reference,
        raw_by_timeframe=complete, observed_at=observed_at, provider_limit=provider_limit, provider_native=True,
        include_entry_zones=include_entry_zones)
    if (context.get("as_of") != reference or context.get("current_quote") is not None
            or context.get("native_current_price_qualified") is not False
            or context.get("partial_bar_used_for_pivot_confirmation") != 0):
        return structure
    if (include_entry_zones and reference == cutoff and context.get('structure_basis_session') == cutoff
            and context.get('entry_zone_proposals')):
        # Independent of the display rollout and its four-zone cap. The Source
        # owner below still checks the canonical quote and each completed frame.
        structure = dict(structure, v3_entry_proposals=context['entry_zone_proposals'],
                         v3_entry_basis_close=context.get('structure_basis_close'))
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
                or b.get("as_of") != reference
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
    extra = {}
    if exclusion is not None:
        exclusion.update(source_plan_sha256=next(iter(plan_hashes)),role_lineage={tf:dict(
            acquisition_id=receipts['adjusted_'+tf]['acquisition_id'],source_plan_sha256=next(iter(plan_hashes)),
            **{k:evidence[tf][k] for k in ('receipt_sha256','normalized_sha256','original_rows_sha256')}) for tf in FRAMES})
        extra = dict(reference_as_of=reference,latest_daily_exclusion=exclusion)
    return dict(structure, price_structure_v3=dict(contract=CONTRACT,
        scope="DATED_REFERENCE_ONLY", ticker=ticker, security_id=security_id, source_generation=generation,
        as_of=reference, currency="USD", adjustment_basis="provider_adjusted_price_v1", completed_sources=evidence,
        target_session=cutoff, observed_at=observed_at, source_plan_sha256=next(iter(plan_hashes)),
        eligible_for_current_price=False, eligible_for_b2_timing=False, zones=zones[:4],**extra))
