"""Offline actual-cutoff diagnostics. Never collects or promotes source authority."""

from datetime import date, datetime, timezone
from hashlib import sha256
import json

import exchange_calendars

from scripts.m12ds_r6_r2_cutoff_audit import KST, NY, session_at
from scripts.m12ds_r6_r3_source_qualification import number
from scripts.m12ds_r6_r4_kiwoom_finality import aware, daily_observation, owned_response
from scripts.m12ds_r6_r5_close_ownership import cross_context_alignment, quote_observation
from scripts.m12ds_r6_r5_cutoff_observer import plan


def canonical_hash(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def dated_values(payload, day):
    matches = [r for r in payload["result_list"] if r.get("dt") == day.replace("-", "")]
    if len(matches) != 1:
        raise ValueError("exact_dated_row_missing_or_duplicated")
    row = matches[0]
    values = {
        key: str(number(row[field]))
        for key, field in dict(
            open="open_pric", high="high_pric", low="low_pric", close="cur_prc"
        ).items()
    }
    if any(number(v) <= 0 for v in values.values()):
        raise ValueError("positive_diagnostic_price_required")
    return dict(date=day, **values)


def request_receipt(item, envelope, route, cutoff):
    record = dict(
        symbol=item["symbol"],
        mode=item["mode"],
        exchange=route["exchange"],
        api_id=item["api_id"],
        request=item["request"],
        request_sha256=canonical_hash({k: item[k] for k in ("api_id", "endpoint", "request")}),
        request_hash_encoding="sorted compact UTF-8 JSON of api_id/endpoint/request",
        status="MISSING",
        diagnostic_available=False,
        strict_valid=False,
        production_authority=False,
    )
    if envelope is None:
        return record
    record.update(
        raw_response_sha256=envelope.get("raw_response_sha256"),
        http_status=envelope.get("http_status"),
        started_at=envelope.get("started_at"),
        received_at=envelope.get("received_at"),
    )
    try:
        for field in ("api_id", "endpoint", "request"):
            if envelope[field] != item[field]:
                raise ValueError("frozen_request_mismatch")
        start, end = aware(envelope["started_at"]), aware(envelope["received_at"])
        for label, at in (("start", start), ("end", end)):
            record[label + "_kst"] = at.astimezone(KST).isoformat()
            record[label + "_utc"] = at.astimezone(timezone.utc).isoformat()
            record[label + "_et"] = at.astimezone(NY).isoformat()
        payload, start, end = owned_response(envelope)
        record["provider_status"] = payload["return_code"]
        record["started_in_owned_minute"] = (
            start.astimezone(KST).replace(second=0, microsecond=0) == cutoff
        )
        record["ended_in_owned_minute"] = (
            end.astimezone(KST).replace(second=0, microsecond=0) == cutoff
        )
        if not (record["started_in_owned_minute"] and record["ended_in_owned_minute"]):
            raise ValueError("outside_frozen_exact_minute")
        target = session_at(start, "US")["intended_completed_session"]
        if target != session_at(cutoff, "US")["intended_completed_session"]:
            raise ValueError("target_session_mismatch")
        for field, expected in (("stk_cd", route["symbol"]), ("stex_tp", route["exchange"])):
            if payload.get(field) not in (None, "", expected):
                raise ValueError("response_identity_mismatch")
        if item["mode"] == "quote":
            quote = quote_observation(envelope, route)
            record.update(quote=quote, basis=quote["basis"], strict_valid=True)
        else:
            previous = exchange_calendars.get_calendar("XNYS").previous_session(target).date()
            record.update(
                target_row=dated_values(payload, target),
                previous_row=dated_values(payload, previous.isoformat()),
                basis=item["mode"].upper(),
                values_role="DIAGNOSTIC_OBSERVED_FIELDS_NOT_FINAL_CLOSE",
            )
            try:
                record["strict_observation"] = daily_observation(envelope, route)
                record["strict_valid"] = True
            except (ValueError, KeyError, TypeError) as exc:
                record["strict_error"] = str(exc)
        record.update(status="OBSERVED", diagnostic_available=True)
    except (ValueError, KeyError, TypeError) as exc:
        record.update(status="FAILED", error=str(exc))
        # Keep provider failure codes without trusting values from failed responses.
        try:
            payload = json.loads(envelope["raw_body"])
            if isinstance(payload, dict):
                record["provider_status"] = payload.get("return_code")
        except (ValueError, KeyError, TypeError):
            pass
    return record


def quote_relation(symbol, records, envelopes, route):
    names = [symbol + "-" + mode for mode in ("quote", "raw", "adjusted")]
    if not all(records[n]["diagnostic_available"] for n in names):
        return dict(symbol=symbol, relation="UNAVAILABLE", production_authority=False)
    quote = records[names[0]]["quote"]
    base = quote["previous_ohlc"]["close"]
    matches = []
    for name in names[1:]:
        for role in ("target_row", "previous_row"):
            row = records[name][role]
            matches.append(
                dict(
                    basis=records[name]["basis"],
                    date=row["date"],
                    row_role=role,
                    daily_close=row["close"],
                    base_close=base,
                    close_equal=number(row["close"]) == number(base),
                    full_ohlc_equal=all(
                        number(row[k]) == number(quote["previous_ohlc"][k])
                        for k in ("open", "high", "low", "close")
                    ),
                )
            )
    result = dict(
        symbol=symbol,
        base_close=base,
        comparisons=matches,
        relation="DIAGNOSTIC_ONLY",
        production_authority=False,
    )
    try:
        result["frozen_alignment"] = cross_context_alignment(*(envelopes[n] for n in names), route)
        result["relation"] = result["frozen_alignment"]["relation"]
    except (ValueError, KeyError, TypeError) as exc:
        result["strict_error"] = str(exc)
    return result


def changes(left, right):
    if left is None or right is None:
        return dict(status="UNAVAILABLE", changes=None)
    return dict(
        status="OBSERVED",
        changes={
            k: dict(
                from_value=left[k],
                to_value=right[k],
                delta=str(number(right[k]) - number(left[k])),
                changed=number(right[k]) != number(left[k]),
            )
            for k in ("open", "high", "low", "close")
        },
    )


def build_report(output, frozen_plan, routes):
    if frozen_plan != plan(date.fromisoformat(frozen_plan["cutoff_date"]), routes):
        raise ValueError("frozen_plan_mismatch")
    windows = []
    for value in frozen_plan["cutoffs"]:
        cutoff = aware(value).astimezone(KST)
        slot = cutoff.strftime("%H%M")
        envelopes, records = {}, {}
        for item in frozen_plan["requests"]:
            name = item["symbol"] + "-" + item["mode"]
            path = output / slot / (name + ".json")
            envelope = json.loads(path.read_text()) if path.exists() else None
            if envelope is not None:
                envelopes[name] = envelope
            records[name] = request_receipt(item, envelope, routes[item["symbol"]], cutoff)
        receipt_path = output / (slot + "-receipt.json")
        receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else None
        adjusted = [records[s + "-adjusted"] for s in routes]
        missing = [k for k, v in records.items() if not v["diagnostic_available"]]
        windows.append(
            dict(
                cutoff=value,
                receipt=receipt,
                raw_response_count=len(envelopes),
                diagnostic_available=sum(r["diagnostic_available"] for r in records.values()),
                full22_available=sum(r["diagnostic_available"] for r in adjusted),
                full22_strict_valid=sum(r["strict_valid"] for r in adjusted),
                missing_or_failed=missing,
                requests=records,
                strict_failures={
                    k: r["strict_error"] for k, r in records.items() if "strict_error" in r
                },
                status="COMPLETE" if not missing else "PARTIAL" if envelopes else "MISSED",
                quote_relations=[
                    quote_relation(s, records, envelopes, routes[s])
                    for s in frozen_plan["quote_subset"]
                ],
            )
        )
    matrix = []
    for symbol in routes:
        rows = [
            w["requests"][symbol + "-adjusted"].get("target_row")
            if w["requests"][symbol + "-adjusted"]["diagnostic_available"]
            else None
            for w in windows
        ]
        matrix.append(
            dict(
                symbol=symbol,
                observations=dict(zip(frozen_plan["cutoffs"], rows, strict=True)),
                transitions=[
                    dict(
                        from_cutoff=windows[i]["cutoff"],
                        to_cutoff=windows[i + 1]["cutoff"],
                        **changes(rows[i], rows[i + 1]),
                    )
                    for i in range(3)
                ],
            )
        )
    complete = all(w["status"] == "COMPLETE" for w in windows)
    any_response = any(w["raw_response_count"] for w in windows)
    attempted = (output / "start.json").exists()
    classification = (
        "CUTOFF_OBSERVATION_COMPLETE"
        if complete
        else "CUTOFF_OBSERVATION_PARTIAL"
        if any_response
        else "TECHNICAL_COLLECTION_FAILURE"
        if attempted
        else "CUTOFF_WINDOW_MISSED"
    )
    return dict(
        task="M12DS_R6_R5A",
        target_session=frozen_plan["target"],
        calendar="XNYS",
        classification=classification,
        windows=windows,
        ohlc_change_matrix=matrix,
        final_owner_decision=None,
        finality_proven=False,
        external_source_required=None,
        production_authority=False,
        later_comparison_executed=False,
        diagnostic_availability_is_not_strict_validity=True,
        timestamp_policy="frozen R5 conservatively requires start and response in the same minute",
        generated_at=datetime.now(KST).isoformat(),
    )
