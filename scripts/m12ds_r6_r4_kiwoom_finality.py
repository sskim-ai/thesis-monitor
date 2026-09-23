"""Audit-only Kiwoom daily finality and actual-cutoff contracts; no live imports."""

from datetime import date, datetime
from hashlib import sha256
import json

import exchange_calendars

from app.macro.providers.market import MARKET_SYMBOLS
from scripts.m12ds_r6_r2_cutoff_audit import KST, NY, session_at
from scripts.m12ds_r6_r3_source_qualification import (
    daily_pair,
    latest_available_information,
    number,
    source_hash,
)

CONTRACT = "us-regular-session-close-kiwoom-daily-v1"
CUTOFF_MINUTES = (5, 10, 15, 20)
SECTORS = ("XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY")
FIELDS = dict(
    open="open_pric", high="high_pric", low="low_pric", close="cur_prc", volume="acc_trde_qty"
)


def aware(value):
    result = datetime.fromisoformat(str(value))
    if result.tzinfo is None:
        raise ValueError("actual_aware_acquisition_required")
    return result


def route_from_gateway(envelope, *, symbol, artifact_sha256):
    """Only a successful exact-symbol gateway identity can own an exchange route."""
    response = envelope["response"]
    identity = response["resolved_symbol"]
    request = envelope["request_parameters"]
    if (
        envelope["http_status"] != 200
        or envelope["endpoint"] != "/ohlcv"
        or response["meta"]["provider"] != "kiwoom"
        or request.get("symbol") != symbol
        or request.get("market") != "US"
        or identity["code"] != symbol
        or identity["market"] != "US"
        or identity["exchange"] not in {"NY", "ND", "NA"}
        or identity["matched_by"]
        not in {"us_stock_list_code", "us_ticker_exchange_map", "us_name_alias"}
    ):
        raise ValueError("successful_exact_gateway_identity_required")
    return dict(
        symbol=symbol,
        exchange=identity["exchange"],
        security_identity=identity,
        identity_source="successful gateway resolved_symbol:" + identity["matched_by"],
        identity_artifact_sha256=source_hash(artifact_sha256),
        gateway_response_sha256=source_hash(envelope["raw_response_sha256"]),
    )


def validate_routes(routes):
    if set(routes) != set(MARKET_SYMBOLS):
        raise ValueError("exact_canonical_universe_required")
    for symbol, route in routes.items():
        if (
            route["symbol"] != symbol
            or route["exchange"] not in {"NY", "ND", "NA"}
            or route["security_identity"]["code"] != symbol
            or route["security_identity"]["exchange"] != route["exchange"]
        ):
            raise ValueError("route_identity_mismatch")
        source_hash(route["identity_artifact_sha256"])
        source_hash(route["gateway_response_sha256"])
    return routes


def daily_request(route, *, adjusted=True):
    return dict(
        stex_tp=route["exchange"],
        stk_cd=route["symbol"],
        strt_dt="",
        upd_stkpc_tp="1" if adjusted else "0",
        exrt_appl_tp="0",
    )


def owned_response(envelope):
    raw = envelope["raw_body"].encode("utf-8")
    if sha256(raw).hexdigest() != source_hash(envelope["raw_response_sha256"]):
        raise ValueError("raw_response_hash_mismatch")
    payload = json.loads(raw)
    start, end = aware(envelope["started_at"]), aware(envelope["received_at"])
    if start > end:
        raise ValueError("acquisition_time_reversed")
    if envelope["http_status"] != 200 or str(payload.get("return_code")) != "0":
        raise ValueError("provider_response_failed")
    return payload, start, end


def daily_observation(envelope, route):
    payload, start, end = owned_response(envelope)
    request = envelope["request"]
    if (
        envelope["api_id"] != "usa06012"
        or envelope["endpoint"] != "/api/us/chart"
        or request != daily_request(route, adjusted=request.get("upd_stkpc_tp") == "1")
    ):
        raise ValueError("daily_context_route_or_basis_mismatch")
    for key, expected in (("stk_cd", route["symbol"]), ("stex_tp", route["exchange"])):
        if payload.get(key) not in (None, "", expected):
            raise ValueError("provider_identity_conflict")
    state = session_at(start, "US")
    target = date.fromisoformat(state["intended_completed_session"])
    if session_at(end, "US")["intended_completed_session"] != target.isoformat():
        raise ValueError("collection_crosses_regular_close")
    calendar = exchange_calendars.get_calendar("XNYS")
    previous = calendar.previous_session(target).date()
    rows = {}
    provisional = []
    for row in payload["result_list"]:
        day = datetime.strptime(row["dt"], "%Y%m%d").date()
        if day.strftime("%Y%m%d") != row["dt"] or day.isoformat() in rows:
            raise ValueError("duplicate_or_invalid_date")
        if day in {target, previous} and row.get("upd_stkpc_tp") not in (
            None,
            "",
            request["upd_stkpc_tp"],
        ):
            raise ValueError("adjustment_basis_mismatch")
        if day > target:
            # An explicitly dated currently-open/premarket row is not a completed row.
            if day != start.astimezone(NY).date() or not calendar.is_session(day):
                raise ValueError("future_daily_row")
            provisional.append(day.isoformat())
        rows[day.isoformat()] = row
    completed = {k: v for k, v in rows.items() if k <= target.isoformat()}
    pair = daily_pair(completed, target, previous, FIELDS)
    return dict(
        symbol=route["symbol"],
        exchange=route["exchange"],
        pair=pair,
        basis="ADJUSTED" if request["upd_stkpc_tp"] == "1" else "RAW",
        currency="USD",
        calendar=state,
        started_at=start.isoformat(),
        received_at=end.isoformat(),
        latest_row_date=max(rows),
        excluded_provisional_dates=provisional,
        source_sha256=envelope["raw_response_sha256"],
        regular_session_finality="UNPROVEN",
        current_direction_eligible=False,
    )


def extended_hours_finality(dailies, quotes, route):
    """A per-symbol, per-date qualification receipt, never a provider-wide promotion."""
    if len(dailies) != 2 or len(quotes) != 2:
        raise ValueError("two_owned_cross_context_samples_required")
    observed = [daily_observation(e, route) for e in dailies]
    values, quote_times, hashes = [], [], []
    for envelope in quotes:
        payload, start, end = owned_response(envelope)
        if (
            envelope["api_id"] != "usa20100"
            or envelope["endpoint"] != "/api/us/mrkcond"
            or envelope["request"] != dict(stex_tp=route["exchange"], stk_cd=route["symbol"])
            or payload.get("stk_cd") != route["symbol"]
            or payload.get("stex_tp") != route["exchange"]
        ):
            raise ValueError("quote_context_identity_mismatch")
        for at in (start, end):
            local = at.astimezone(NY)
            state = session_at(at, "US")
            if not (
                state["regular_session_state"] == "PRE_OPEN"
                and (4, 0) <= (local.hour, local.minute) < (9, 30)
                or state["regular_session_state"] == "POST_CLOSE"
                and 16 <= local.hour < 20
            ):
                raise ValueError("extended_hours_observation_required")
        values.append(abs(number(payload["cur_prc"])))
        quote_times.append((start, end))
        hashes.append(envelope["raw_response_sha256"])
    if not (
        aware(dailies[0]["received_at"])
        <= quote_times[0][0]
        <= quote_times[0][1]
        < quote_times[1][0]
        <= quote_times[1][1]
        <= aware(dailies[1]["started_at"])
    ):
        raise ValueError("daily_samples_must_bracket_quote_movement")
    comparable = ("symbol", "exchange", "basis", "currency", "pair")
    if any(observed[0][key] != observed[1][key] for key in comparable):
        raise ValueError("completed_daily_row_mutated_or_incompatible")
    if min(values) <= 0 or values[0] == values[1]:
        raise ValueError("no_observed_quote_movement_inconclusive")
    return dict(
        contract=CONTRACT,
        status="PASS",
        symbol=route["symbol"],
        session_date=observed[0]["pair"][0]["date"],
        basis=observed[0]["basis"],
        authority="SETTLED_REGULAR_SESSION_CLOSE",
        scope="OBSERVED_SYMBOL_SESSION_ONLY",
        proof="DAILY_OHLCV_UNCHANGED_BRACKETING_EXTENDED_QUOTE_MOVEMENT",
        daily_source_hashes=[o["source_sha256"] for o in observed],
        quote_source_hashes=hashes,
        current_direction_eligible=False,
        cutoff_proven=False,
        lookahead_required_in_production=False,
    )


def cutoff_attempt(envelopes, routes, *, cutoff):
    """Conservative exact-minute observation, not a synthetic scheduled timestamp."""
    validate_routes(routes)
    local = aware(cutoff).astimezone(KST)
    if local.hour != 8 or local.minute not in CUTOFF_MINUTES or local.second or local.microsecond:
        raise ValueError("configured_cutoff_required")
    if set(envelopes) != set(routes):
        raise ValueError("full_actual_cutoff_universe_required")
    observed = {}
    for symbol, envelope in envelopes.items():
        row = daily_observation(envelope, routes[symbol])
        for key in ("started_at", "received_at"):
            at = aware(row[key]).astimezone(KST)
            if at.replace(second=0, microsecond=0) != local:
                raise ValueError("not_actual_configured_minute")
        observed[symbol] = row
    if len({(r["pair"][0]["date"], r["basis"]) for r in observed.values()}) != 1:
        raise ValueError("cutoff_session_basis_mismatch")
    return dict(
        status="PASS",
        contract="kiwoom-actual-cutoff-availability-v1",
        cutoff=local.isoformat(),
        count=len(observed),
        observations=observed,
        finality_proven=False,
        current_direction_eligible=False,
    )


def qualified_universe(observations, finalities, cutoff):
    if set(observations) != set(MARKET_SYMBOLS) or set(finalities) != set(MARKET_SYMBOLS):
        raise ValueError("full_universe_finality_required")
    if cutoff.get("status") != "PASS" or cutoff.get("count") != len(MARKET_SYMBOLS):
        raise ValueError("actual_full_cutoff_required")
    if observations != cutoff["observations"]:
        raise ValueError("cutoff_input_binding_mismatch")
    for symbol, row in observations.items():
        proof = finalities[symbol]
        if (
            proof.get("contract") != CONTRACT
            or proof.get("status") != "PASS"
            or proof.get("symbol") != symbol
            or proof.get("basis") != row["basis"]
            or proof.get("session_date") != row["pair"][0]["date"]
            or row["source_sha256"] not in proof.get("daily_source_hashes", [])
        ):
            raise ValueError("exact_finality_binding_required")
    ranking = []
    for symbol in SECTORS:
        current, previous = observations[symbol]["pair"]
        delta = (number(current["close"]) / number(previous["close"]) - 1) * 100
        ranking.append(dict(symbol=symbol, return_pct=str(delta)))
    return dict(
        status="PASS",
        count=len(observations),
        top3=sorted(ranking, key=lambda r: (-number(r["return_pct"]), r["symbol"]))[:3],
        bottom3=sorted(ranking, key=lambda r: (number(r["return_pct"]), r["symbol"]))[:3],
    )


def macro_information_block(envelopes, *, as_of):
    """Backend-only shadow display; rows never enter the AI direction fact catalog."""
    labels = {
        "DCOILWTICO": ("WTI", "USD/배럴"),
        "DGS3": ("미국 국채 3년", "%"),
        "DGS5": ("미국 국채 5년", "%"),
        "DGS10": ("미국 국채 10년", "%"),
        "DGS30": ("미국 국채 30년", "%"),
    }
    rows, lines = [], []
    for series, envelope in sorted(envelopes.items()):
        if series not in labels:
            raise ValueError("unsupported_macro_display_series")
        row = latest_available_information(envelope, series=series, as_of=as_of)
        label, unit = labels[series]
        lines.append(f"{label} {row['value']} {unit} · {row['label']}")
        rows.append(row)
    return dict(
        text="\n".join(lines),
        rows=rows,
        direction_fact_refs=[],
        current_direction_eligible=False,
        renderer_scope="INFORMATION_ONLY",
    )
