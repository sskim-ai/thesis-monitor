"""Manual, bounded read-only observer. Plan-only unless --execute is specified.

No scheduler registration, model, delivery, database, or authority promotion.
Run manually during one of the configured minutes, using a frozen route-file hash.
"""

import argparse
import asyncio
from datetime import date, datetime, time, timezone
from hashlib import sha256
import json
from pathlib import Path

import httpx

from scripts.m12ds_r6_r2_cutoff_audit import KST, NY, session_at
from scripts.m12ds_r6_r4_kiwoom_finality import (
    CUTOFF_MINUTES,
    cutoff_attempt,
    daily_observation,
    daily_request,
    validate_routes,
)


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")


def load_routes(path, expected_hash):
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != expected_hash:
        raise ValueError("frozen_routing_hash_mismatch")
    return validate_routes(json.loads(raw)["routes"])


def plan(day, routes):
    return dict(
        contract="manual-kiwoom-cutoff-observer-v1",
        date=day.isoformat(),
        cutoffs=[
            datetime.combine(day, time(8, minute), KST).isoformat() for minute in CUTOFF_MINUTES
        ],
        requests={s: daily_request(r) for s, r in routes.items()},
        api_id="usa06012",
        endpoint="/api/us/chart",
        max_daily_calls=88,
        max_auth_calls=1,
        timeout_per_request_seconds=10,
        retries=0,
        pagination=False,
        acquisition_policy="All 22 actual request and response times must fall in one configured minute.",
        current_quote_calls=0,
        model_calls=0,
        sends=0,
        scheduler_mutations=0,
        finality_promotion=False,
        registration="NONE_MANUAL_PROCESS_ONLY",
    )


async def fetch_daily(client, token, route):
    started = datetime.now(KST)
    response = await client.post(
        "/api/us/chart",
        json=daily_request(route),
        headers={
            "Content-Type": "application/json;charset=UTF-8",
            "authorization": f"Bearer {token}",
            "api-id": "usa06012",
            "cont-yn": "N",
            "next-key": "",
        },
    )
    received = datetime.now(KST)
    raw = response.content
    # Preserve byte identity, rather than reserializing JSON and calling it raw.
    body = raw.decode("utf-8")
    return dict(
        api_id="usa06012",
        endpoint="/api/us/chart",
        request=daily_request(route),
        started_at=started.isoformat(),
        received_at=received.isoformat(),
        received_utc=received.astimezone(timezone.utc).isoformat(),
        received_et=received.astimezone(NY).isoformat(),
        http_status=response.status_code,
        raw_body=body,
        raw_response_sha256=sha256(raw).hexdigest(),
        continuation=response.headers.get("cont-yn") == "Y",
    )


async def observe(day, routes, output, *, env_file):
    # Authenticate only in the requested real window; never let a stale date replay.
    now = datetime.now(KST)
    if now.date() != day or not time(8, 4) <= now.time().replace(tzinfo=None) < time(8, 21):
        raise ValueError("start_manually_between_0804_and_0820_on_observation_date")
    if output.exists():
        raise ValueError("fresh_output_directory_required")
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
        raise ValueError("official_production_readonly_endpoint_required")
    put(output / "plan.json", plan(day, routes))
    attempts = []
    async with httpx.AsyncClient(base_url=owner.base_url, timeout=10, trust_env=False) as client:
        token = await owner._access_token(client)
        for minute in CUTOFF_MINUTES:
            cutoff = datetime.combine(day, time(8, minute), KST)
            now = datetime.now(KST)
            if now >= cutoff.replace(second=59, microsecond=999999):
                attempts.append(dict(cutoff=cutoff.isoformat(), status="MISSED_NOT_BACKFILLED"))
                continue
            await asyncio.sleep(max(0, (cutoff - now).total_seconds()))
            envelopes, errors = {}, {}
            for symbol, route in routes.items():
                if datetime.now(KST).replace(second=0, microsecond=0) != cutoff:
                    errors[symbol] = "configured_minute_exhausted"
                    break
                try:
                    envelope = await fetch_daily(client, token, route)
                    put(output / f"08{minute:02d}/{symbol}.json", envelope)
                    envelopes[symbol] = envelope
                    daily_observation(envelope, route)
                except (ValueError, KeyError, httpx.HTTPError) as exc:
                    errors[symbol] = type(exc).__name__
                await asyncio.sleep(0.6)
            receipt = dict(
                cutoff=cutoff.isoformat(),
                calendar=session_at(cutoff, "US"),
                received_symbols=sorted(envelopes),
                errors=errors,
                status="FAIL",
            )
            if not errors:
                try:
                    receipt.update(cutoff_attempt(envelopes, routes, cutoff=cutoff))
                except ValueError as exc:
                    receipt["errors"]["cutoff"] = str(exc)
            put(output / f"attempt-{minute:02d}.json", receipt)
            attempts.append(receipt)
            if receipt["status"] == "PASS":
                break
    put(
        output / "result.json",
        dict(
            attempts=attempts,
            status="PASS" if any(a["status"] == "PASS" for a in attempts) else "UNAVAILABLE",
            availability_only=True,
            regular_session_finality="NOT_PROMOTED",
            model_calls=0,
            sends=0,
        ),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--routes", type=Path, required=True)
    parser.add_argument("--routes-sha256", required=True)
    parser.add_argument("--date", type=date.fromisoformat, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    routes = load_routes(args.routes, args.routes_sha256)
    if not args.execute:
        print(json.dumps(plan(args.date, routes), ensure_ascii=False, indent=2))
        return
    if args.output is None or args.env_file is None:
        parser.error("--execute requires --output and --env-file")
    asyncio.run(observe(args.date, routes, args.output, env_file=args.env_file))


if __name__ == "__main__":
    main()
