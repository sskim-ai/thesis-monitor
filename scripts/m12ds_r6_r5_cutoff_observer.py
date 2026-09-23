"""Manual R5 observer: four actual cutoff samples and one later historical sample.

Plan-only by default. Never enables schedules or invokes model/delivery/DB routes.
"""

import argparse
import asyncio
from datetime import date, datetime, time, timezone
from hashlib import sha256
from pathlib import Path
import json

import httpx

from scripts.m12ds_r6_r2_cutoff_audit import KST, NY, session_at
from scripts.m12ds_r6_r4_cutoff_observer import load_routes, put
from scripts.m12ds_r6_r4_kiwoom_finality import CUTOFF_MINUTES, daily_request, validate_routes
from scripts.m12ds_r6_r5_close_ownership import DIAGNOSTIC_SYMBOLS, review_cutoff


def requests(routes):
    validate_routes(routes)
    result = []
    for symbol, route in routes.items():
        result.append(
            dict(
                symbol=symbol,
                mode="adjusted",
                api_id="usa06012",
                endpoint="/api/us/chart",
                request=daily_request(route),
            )
        )
        if symbol in DIAGNOSTIC_SYMBOLS:
            result.extend(
                [
                    dict(
                        symbol=symbol,
                        mode="raw",
                        api_id="usa06012",
                        endpoint="/api/us/chart",
                        request=daily_request(route, adjusted=False),
                    ),
                    dict(
                        symbol=symbol,
                        mode="quote",
                        api_id="usa20100",
                        endpoint="/api/us/mrkcond",
                        request=dict(stex_tp=route["exchange"], stk_cd=symbol),
                    ),
                ]
            )
    return result


def plan(day, routes):
    items = requests(routes)
    cutoff = datetime.combine(day, time(8, 5), KST)
    return dict(
        contract="kiwoom-r5-bounded-ownership-observer-v1",
        cutoff_date=day.isoformat(),
        target=session_at(cutoff, "US")["intended_completed_session"],
        cutoffs=[datetime.combine(day, time(8, m), KST).isoformat() for m in CUTOFF_MINUTES],
        requests=items,
        requests_sha256=sha256(json.dumps(items, sort_keys=True).encode()).hexdigest(),
        request_count_per_sample=len(items),
        maximum_cutoff_data_calls=4 * len(items),
        maximum_later_data_calls=len(items),
        maximum_auth_calls_per_invocation=1,
        quote_subset=list(DIAGNOSTIC_SYMBOLS),
        maximum_attempts_per_mode=1,
        retries=0,
        request_timeout_seconds=10,
        paginate=False,
        missed_windows="RECORD_MISSED_NEVER_BACKFILL",
        scheduler_registration=False,
        model_calls=0,
        sends=0,
        authority_promotion=False,
    )


def window_gate(now, *, day, mode):
    local = now.astimezone(KST)
    if mode == "cutoff":
        if local.date() != day or not time(8, 4) <= local.time().replace(tzinfo=None) < time(8, 21):
            raise ValueError("manual_cutoff_mode_requires_actual_0804_to_0820_window")
    elif mode == "later":
        target = session_at(datetime.combine(day, time(8, 5), KST), "US")[
            "intended_completed_session"
        ]
        state = session_at(now, "US")
        et = now.astimezone(NY)
        if (
            state["intended_completed_session"] != target
            or state["regular_session_state"] != "PRE_OPEN"
            or et.date() <= date.fromisoformat(target)
            or et.hour < 4
        ):
            raise ValueError("later_mode_requires_target_historical_next_premarket")
    else:
        raise ValueError("unknown_observation_mode")


async def fetch(client, token, item):
    if (item["api_id"], item["endpoint"]) not in {
        ("usa06012", "/api/us/chart"),
        ("usa20100", "/api/us/mrkcond"),
    }:
        raise ValueError("read_only_chart_quote_allowlist_required")
    start = datetime.now(KST)
    response = await client.post(
        item["endpoint"],
        json=item["request"],
        headers={
            "authorization": f"Bearer {token}",
            "api-id": item["api_id"],
            "Content-Type": "application/json;charset=UTF-8",
            "cont-yn": "N",
            "next-key": "",
        },
    )
    end = datetime.now(KST)
    raw = response.content
    return dict(
        api_id=item["api_id"],
        endpoint=item["endpoint"],
        request=item["request"],
        started_at=start.isoformat(),
        received_at=end.isoformat(),
        received_utc=end.astimezone(timezone.utc).isoformat(),
        received_et=end.astimezone(NY).isoformat(),
        http_status=response.status_code,
        raw_body=raw.decode("utf-8"),
        raw_response_sha256=sha256(raw).hexdigest(),
        continuation=response.headers.get("cont-yn") == "Y",
    )


async def sample(client, token, items, output, *, cutoff=None):
    collected, errors = {}, []
    for item in items:
        if cutoff and datetime.now(KST).replace(second=0, microsecond=0) != cutoff:
            errors.append(dict(error="configured_minute_exhausted", before_symbol=item["symbol"]))
            break
        name = item["symbol"] + "-" + item["mode"]
        try:
            envelope = await fetch(client, token, item)
            put(output / (name + ".json"), envelope)
            collected[name] = envelope
        except (httpx.HTTPError, ValueError) as exc:
            errors.append(dict(request=name, error_type=type(exc).__name__))
        await asyncio.sleep(0.6)
    return collected, errors


def split(envelopes, items, mode):
    return {
        item["symbol"]: envelopes[item["symbol"] + "-" + mode]
        for item in items
        if item["mode"] == mode
    }


async def observe(day, routes, output, *, mode, env_file, frozen_plan):
    expected = plan(day, routes)
    if frozen_plan != expected:
        raise ValueError("frozen_plan_drift")
    window_gate(datetime.now(KST), day=day, mode=mode)
    if output.exists():
        raise ValueError("new_output_directory_required")
    from app.config import Settings
    from app.providers.kiwoom_rest_client import KiwoomRestClient

    settings = Settings(_env_file=env_file)
    owner = KiwoomRestClient(
        app_key=settings.kiwoom_app_key,
        secret_key=settings.kiwoom_secret_key,
        base_url=settings.kiwoom_rest_base_url,
        max_retries=0,
    )
    if owner.base_url != "https://api.kiwoom.com":
        raise ValueError("official_endpoint_required")
    put(output / "start.json", dict(mode=mode, plan=expected, at=datetime.now(KST).isoformat()))
    receipts = []
    async with httpx.AsyncClient(base_url=owner.base_url, timeout=10, trust_env=False) as client:
        token = await owner._access_token(client)
        slots = (
            [datetime.combine(day, time(8, m), KST) for m in CUTOFF_MINUTES]
            if mode == "cutoff"
            else [None]
        )
        for slot in slots:
            now = datetime.now(KST)
            if slot and now >= slot.replace(second=59, microsecond=999999):
                receipts.append(dict(slot=slot.isoformat(), status="MISSED_NOT_BACKFILLED"))
                continue
            if slot:
                await asyncio.sleep(max(0, (slot - now).total_seconds()))
            name = slot.strftime("%H%M") if slot else "later"
            envelopes, errors = await sample(
                client, token, expected["requests"], output / name, cutoff=slot
            )
            receipt = dict(
                slot=slot.isoformat() if slot else None,
                errors=errors,
                collected=len(envelopes),
                status="INCOMPLETE" if errors else "COLLECTED_NOT_QUALIFIED",
            )
            if slot and not errors:
                try:
                    receipt["review"] = review_cutoff(
                        split(envelopes, expected["requests"], "adjusted"),
                        split(envelopes, expected["requests"], "raw"),
                        split(envelopes, expected["requests"], "quote"),
                        routes,
                        cutoff=slot,
                    )
                except (ValueError, KeyError) as exc:
                    receipt.update(status="VALIDATION_FAILED", error_type=type(exc).__name__)
            put(output / (name + "-receipt.json"), receipt)
            receipts.append(receipt)
    put(
        output / "result.json",
        dict(
            mode=mode,
            receipts=receipts,
            final_owner_decision=None,
            production_authority=False,
            model_calls=0,
            retries=0,
        ),
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=["plan", "cutoff", "later"], default="plan")
    p.add_argument("--routes", type=Path, required=True)
    p.add_argument("--routes-sha256", required=True)
    p.add_argument("--date", type=date.fromisoformat, required=True)
    p.add_argument("--output", type=Path)
    p.add_argument("--env-file", type=Path)
    p.add_argument("--plan", type=Path)
    p.add_argument("--plan-sha256")
    args = p.parse_args()
    routes = load_routes(args.routes, args.routes_sha256)
    if args.mode == "plan":
        print(json.dumps(plan(args.date, routes), ensure_ascii=False, indent=2))
        return
    if not all((args.output, args.env_file, args.plan, args.plan_sha256)):
        p.error("execution requires output, env-file, plan, and plan-sha256")
    raw = args.plan.read_bytes()
    if sha256(raw).hexdigest() != args.plan_sha256:
        raise ValueError("frozen_plan_hash_mismatch")
    asyncio.run(
        observe(
            args.date,
            routes,
            args.output,
            mode=args.mode,
            env_file=args.env_file,
            frozen_plan=json.loads(raw),
        )
    )


if __name__ == "__main__":
    main()
