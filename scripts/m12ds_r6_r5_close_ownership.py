"""Qualification-only quote/date alignment; never a production close owner."""

from datetime import date

from scripts.m12ds_r6_r2_cutoff_audit import KST, NY, session_at
from scripts.m12ds_r6_r3_source_qualification import number
from scripts.m12ds_r6_r4_kiwoom_finality import (
    CUTOFF_MINUTES,
    aware,
    cutoff_attempt,
    daily_observation,
    owned_response,
)

QUOTE_FIELDS = dict(
    open="pre_open_pric", high="pre_high_pric", low="pre_low_pric", close="base_close_pric"
)
DIAGNOSTIC_SYMBOLS = ("SPY", "SOXX", "XLC")
DRIFT_CLASSIFICATION = "PRODUCTION_ROUTE_SAME_DATE_CLOSE_NOT_REPRODUCIBLY_FINAL"


def quote_observation(envelope, route):
    payload, start, end = owned_response(envelope)
    if (
        envelope["api_id"] != "usa20100"
        or envelope["endpoint"] != "/api/us/mrkcond"
        or envelope["request"] != dict(stex_tp=route["exchange"], stk_cd=route["symbol"])
        or payload.get("stex_tp") != route["exchange"]
        or payload.get("stk_cd") != route["symbol"]
        or payload.get("curr_unit") != "USD"
    ):
        raise ValueError("exact_quote_identity_currency_required")
    if (
        session_at(start, "US")["intended_completed_session"]
        != session_at(end, "US")["intended_completed_session"]
        or start.astimezone(NY).date() != end.astimezone(NY).date()
    ):
        raise ValueError("quote_crosses_session_ownership")
    previous = {k: number(payload[v]) for k, v in QUOTE_FIELDS.items()}
    o, h, low, c = (previous[k] for k in ("open", "high", "low", "close"))
    if not 0 < low <= min(o, c) <= max(o, c) <= h:
        raise ValueError("previous_quote_ohlc_invalid")
    # Only cur_prc uses the official price-direction sign convention.
    current = abs(number(payload["cur_prc"]))
    if current <= 0:
        raise ValueError("positive_current_price_required")
    return dict(
        symbol=route["symbol"],
        exchange=route["exchange"],
        currency="USD",
        current_price=str(current),
        previous_ohlc={k: str(v) for k, v in previous.items()},
        delta=str(number(payload["pred_pre"])),
        return_pct=str(number(payload["flu_rt"])),
        delta_exact=current - previous["close"] == number(payload["pred_pre"]),
        source_sha256=envelope["raw_response_sha256"],
        started_at=start.isoformat(),
        received_at=end.isoformat(),
        calendar=session_at(start, "US"),
        provider_session_date=None,
        basis="NOT_DECLARED_BY_QUOTE",
        current_price_role="CURRENT_QUOTE",
        production_authority=False,
    )


def tuple_equal(left, right):
    return all(number(left[k]) == number(right[k]) for k in QUOTE_FIELDS)


def cross_context_alignment(quote, raw_daily, adjusted_daily, route):
    """Exact four-field numeric matching, explicitly distinct from session ownership."""
    q = quote_observation(quote, route)
    raw = daily_observation(raw_daily, route)
    adjusted = daily_observation(adjusted_daily, route)
    if raw["basis"] != "RAW" or adjusted["basis"] != "ADJUSTED":
        raise ValueError("explicit_raw_and_adjusted_requests_required")
    days = [r["date"] for r in raw["pair"]]
    if days != [r["date"] for r in adjusted["pair"]]:
        raise ValueError("dated_basis_context_mismatch")
    states = [q["calendar"], raw["calendar"], adjusted["calendar"]]
    if len({s["intended_completed_session"] for s in states}) != 1:
        raise ValueError("quote_and_daily_contexts_not_same_completed_session")
    comparisons = []
    for r, a in zip(raw["pair"], adjusted["pair"], strict=True):
        basis_equal = tuple_equal(r, a)
        comparisons.append(
            dict(
                date=r["date"],
                raw_ohlc={k: r[k] for k in QUOTE_FIELDS},
                adjusted_ohlc={k: a[k] for k in QUOTE_FIELDS},
                basis_equal=basis_equal,
                quote_matches_raw=tuple_equal(q["previous_ohlc"], r),
                quote_matches_adjusted=tuple_equal(q["previous_ohlc"], a),
            )
        )
    matches = [
        r["date"]
        for r in comparisons
        if r["basis_equal"] and r["quote_matches_raw"] and r["quote_matches_adjusted"]
    ]
    matched = matches[0] if len(matches) == 1 and q["delta_exact"] else None
    return dict(
        contract="kiwoom-quote-historical-numeric-alignment-v1",
        symbol=route["symbol"],
        status="EXACT_NUMERIC_ALIGNMENT" if matched else "UNOWNED_ALIGNMENT",
        quote=q,
        matched_dated_row=matched,
        comparisons=comparisons,
        target=days[0],
        previous=days[1],
        relation=(
            "TARGET_VALUES"
            if matched == days[0]
            else "PREVIOUS_SESSION_VALUES"
            if matched == days[1]
            else "AMBIGUOUS"
        ),
        basis_reconciliation="EXACT_RAW_ADJUSTED_FOUR_FIELD_EQUALITY_ON_MATCHED_DATE"
        if matched
        else None,
        provider_session_owner="NOT_PROVEN_BY_NUMERIC_MATCH",
        source_hashes=dict(
            quote=q["source_sha256"], raw=raw["source_sha256"], adjusted=adjusted["source_sha256"]
        ),
        production_authority=False,
        cutoff_proven=False,
    )


def review_cutoff(dailies, raw_subset, quotes, routes, *, cutoff):
    receipt = cutoff_attempt(dailies, routes, cutoff=cutoff)
    if set(raw_subset) != set(DIAGNOSTIC_SYMBOLS) or set(quotes) != set(DIAGNOSTIC_SYMBOLS):
        raise ValueError("frozen_diagnostic_subset_required")
    expected = aware(cutoff).astimezone(KST)
    for envelope in [*raw_subset.values(), *quotes.values()]:
        _, start, end = owned_response(envelope)
        if any(
            at.astimezone(KST).replace(second=0, microsecond=0) != expected for at in (start, end)
        ):
            raise ValueError("quote_and_basis_requests_must_be_at_actual_cutoff")
    alignment = {
        s: cross_context_alignment(quotes[s], raw_subset[s], dailies[s], routes[s])
        for s in DIAGNOSTIC_SYMBOLS
    }
    return dict(
        contract="kiwoom-cutoff-cross-context-diagnostic-v1",
        availability=receipt,
        alignment=alignment,
        status="COLLECTED_NOT_FINALITY",
        final_decision=None,
        production_authority=False,
    )


def later_historical_comparison(at_cutoff, later, route):
    start = aware(at_cutoff["started_at"]).astimezone(KST)
    end = aware(at_cutoff["received_at"]).astimezone(KST)
    if (
        start.hour != 8
        or start.minute not in CUTOFF_MINUTES
        or start.replace(second=0, microsecond=0) != end.replace(second=0, microsecond=0)
    ):
        raise ValueError("delayed_comparison_requires_actual_configured_cutoff")
    early, late = (daily_observation(e, route) for e in (at_cutoff, later))
    target = early["pair"][0]["date"]
    if (
        late["pair"][0]["date"] != target
        or early["basis"] != late["basis"]
        or aware(later["started_at"]) <= aware(at_cutoff["received_at"])
        or aware(later["started_at"]).astimezone(NY).date() <= date.fromisoformat(target)
        or late["calendar"]["regular_session_state"] != "PRE_OPEN"
    ):
        raise ValueError("same_target_next_day_premarket_same_basis_required")
    return dict(
        symbol=route["symbol"],
        target=target,
        basis=early["basis"],
        cutoff_close=early["pair"][0]["close"],
        later_historical_close=late["pair"][0]["close"],
        close_equal=number(early["pair"][0]["close"]) == number(late["pair"][0]["close"]),
        ohlc_equal=tuple_equal(early["pair"][0], late["pair"][0]),
        source_hashes=[early["source_sha256"], late["source_sha256"]],
        role="DELAYED_QUALIFICATION_ONLY",
        production_lookahead_dependency=False,
        prior_drift_erased=False,
        production_authority=False,
    )
