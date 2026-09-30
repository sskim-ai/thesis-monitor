"""Sealed optional valuation reads; replay through the REV28 atomic owner.

Listing metadata is route-selection input only. Current identity always needs
this generation's list/profile response. No diagnostic HTTP side channel.
"""

from datetime import datetime
import json

import httpx

from app.providers.kiwoom_rest_client import KiwoomRestClient
from app.services.provider_native_valuation_snapshot import (
    INPUT_CONTRACT,
    KIWOOM_ROUTE,
    FINNHUB_BASE,
)
from app.services.sealed_fresh_dispatch import ProviderPlan, consume_bound_result
from app.services.unified_live_source_transport import SourceSafetyStop
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest

UNAVAILABLE_CONTRACT = "provider-native-valuation-unavailable-v1"


def routing_markets(identities, *, listing_rows):
    """Never infer KOSPI from a generic KRX exchange or a six-digit ticker."""
    result = {}
    for ticker, security in identities.items():
        if security.get("country") != "KR":
            continue
        exact = {"KOSPI": "0", "KOSDAQ": "10"}.get(security.get("exchange"))
        rows = [r for r in listing_rows if r.get("code") == ticker]
        markets = {str(r.get("marketCode")) for r in rows}
        if exact:
            if markets and markets != {exact}:
                raise ValueError("valuation_market_routing_conflict:" + ticker)
            result[ticker] = exact
        elif (
            security.get("exchange") == "KRX"
            and len(rows) == 1
            and len(markets) == 1
            and markets <= {"0", "10"}
        ):
            result[ticker] = next(iter(markets))
        else:
            raise ValueError("valuation_market_routing_authority_missing:" + ticker)
    return result


def add_slots(*, identities, market_types, add, kiwoom):
    if set(market_types) != {t for t, s in identities.items() if s.get("country") == "KR"}:
        raise ValueError("valuation_market_roster_mismatch")
    inventory = {}
    for market in sorted(set(market_types.values())):
        if market not in {"0", "10"}:
            raise ValueError("valuation_market_type_unknown")
        kiwoom(
            "valuation:list:" + market,
            "valuation:list:" + market,
            "kr",
            "*",
            "ka10099",
            "/api/dostk/stkinfo",
            {"mrkt_tp": market},
            pages=5,
            mandatory=False,
            retries=0,
        )
    for ticker, security in sorted(identities.items()):
        if security.get("country") == "KR":
            key = "valuation:basic:" + ticker
            kiwoom(
                key,
                key,
                "kr",
                ticker,
                "ka10001",
                "/api/dostk/stkinfo",
                {"stk_cd": ticker},
                mandatory=False,
                retries=0,
            )
            inventory[ticker] = dict(
                provider="kiwoom",
                market_type=market_types[ticker],
                slots=["valuation:list:" + market_types[ticker], key],
                security_sha256=digest(security),
            )
        else:
            # No speculative ADR skip: all US subjects receive exact current
            # responses; the existing identity owner still denies depositaries.
            keys = []
            for endpoint in ("profile2", "metric"):
                key = "valuation:" + endpoint + ":" + ticker
                params = {"symbol": ticker, "token": "PLAN_CREDENTIAL"}
                if endpoint == "metric":
                    params["metric"] = "all"
                add(
                    key,
                    "finnhub",
                    key,
                    "us",
                    ticker,
                    endpoint,
                    httpx.Request("GET", FINNHUB_BASE + endpoint, params=params),
                    mandatory=False,
                    retries=0,
                )
                keys.append(key)
            inventory[ticker] = dict(
                provider="finnhub", slots=keys, security_sha256=digest(security)
            )
    return inventory


async def collect_native(*, frozen, settings, sealed):
    inventory = frozen["valuation_slots"]
    client = KiwoomRestClient(
        app_key=settings.kiwoom_app_key,
        secret_key=settings.kiwoom_secret_key,
        base_url=settings.kiwoom_rest_base_url,
        timeout_seconds=600,
        max_retries=0,
        request_interval_seconds=settings.kiwoom_rest_request_interval_seconds,
        transport=sealed,
    )
    outcomes = {}

    async def capture(key, action):
        try:
            await action()
            outcomes[key] = "CAPTURED_NOT_QUALIFIED"
        except SourceSafetyStop:
            raise
        except Exception as exc:
            outcomes[key] = "UNAVAILABLE_" + type(exc).__name__

    async def listing(market):
        cursor = ""
        wanted = {t for t, r in inventory.items() if r.get("market_type") == market}
        for page in range(5):
            response = await client.request(
                endpoint="/api/dostk/stkinfo",
                api_id="ka10099",
                body={"mrkt_tp": market},
                continuation=page > 0,
                next_key=cursor,
            )
            body = response.payload
            wanted -= {r.get("code") for r in body.get("list", [])}
            if not wanted or not response.continuation:
                return
            cursor = response.next_key

    for market in sorted(
        {r["market_type"] for r in inventory.values() if r["provider"] == "kiwoom"}
    ):
        await capture("list:" + market, lambda m=market: listing(m))
    for ticker, row in inventory.items():
        if row["provider"] == "kiwoom":
            await capture(
                ticker,
                lambda t=ticker: client.request(
                    endpoint="/api/dostk/stkinfo", api_id="ka10001", body={"stk_cd": t}
                ),
            )
        else:
            async with httpx.AsyncClient(
                transport=sealed, timeout=600, follow_redirects=False
            ) as http:
                for endpoint in ("profile2", "metric"):
                    params = {"symbol": ticker, "token": settings.finnhub_api_key}
                    if endpoint == "metric":
                        params["metric"] = "all"
                    await capture(
                        ticker + ":" + endpoint,
                        lambda e=endpoint, p=params: http.get(FINNHUB_BASE + e, params=p),
                    )
    return outcomes


def replay_native(*, root, frozen, outcome, security, policy):
    """Project native-owner receipts only from exact dispatcher final records."""
    ticker = security["ticker"]
    inventory = frozen["valuation_slots"][ticker]
    if inventory["security_sha256"] != digest(security):
        raise ValueError("valuation_slot_security_drift")
    plan = ProviderPlan.model_validate(frozen["plan"])
    if plan.generation_id != frozen["generation_id"]:
        raise ValueError("valuation_plan_generation_drift")
    bindings = []

    def captured(key, request):
        final = outcome["logical_results"].get(key)
        if final is None:
            raise LookupError("UNAVAILABLE_PROVIDER_REQUEST_NOT_COMPLETED")
        if final.get("status") != "PASS":
            # A typed failure is admissible only with its exact persisted final
            # receipt, not a caller-provided unavailable flag.
            persisted = json.loads((root / "dispatch/receipts" / key / "final.json").read_bytes())
            if persisted != final or final["receipt_sha256"] != digest(
                {k: v for k, v in final.items() if k != "receipt_sha256"}
            ):
                raise ValueError("valuation_failed_receipt_drift")
            raise LookupError("UNAVAILABLE_PROVIDER_RESPONSE")
        bound = consume_bound_result(
            root=root / "dispatch",
            plan=plan,
            logical_id=key,
            receipt_sha256=final["receipt_sha256"],
        )
        descriptor = next(d for d in plan.descriptors if d.logical_request_id == key)
        raw = (root / "dispatch" / descriptor.raw_path).read_bytes()
        bindings.append(final["receipt_sha256"])
        last = final["attempts"][-1]
        receipt = dict(
            provider=inventory["provider"],
            run_id=plan.generation_id,
            security_sha256=digest(security),
            source_sha256=sha256_bytes(raw),
            acquisition_class="FRESH_CURRENT_RUN",
            http_status=200,
            request=request,
            requested_at=last["started_at"],
            received_at=last["finished_at"],
            response_headers=final["response_headers"],
            sealed_receipt_sha256=final["receipt_sha256"],
            sealed_plan_sha256=plan.plan_sha256,
            consumed_binding=bound,
        )
        return dict(raw=raw, receipt=receipt)

    common = dict(
        run_started_at=datetime.fromisoformat(frozen["frozen_at"]),
        cutoff=datetime.fromisoformat(outcome["completed_at"]),
        policy=policy,
    )
    try:
        if inventory["provider"] == "kiwoom":
            market = inventory["market_type"]
            pages, previous = [], None
            for page in range(1, 6):
                key = (
                    "valuation:list:" + market + (":continuation:" + str(page) if page > 1 else "")
                )
                if key not in outcome["logical_results"] and page > 1:
                    break
                continuation = (
                    {} if previous is None else {"cont-yn": "Y", "next-key": previous["next-key"]}
                )
                item = captured(
                    key,
                    dict(
                        method="POST",
                        route=KIWOOM_ROUTE,
                        api_id="ka10099",
                        body={"mrkt_tp": market},
                        continuation=continuation,
                    ),
                )
                pages.append(item)
                previous = item["receipt"]["response_headers"]
            metric = captured(
                "valuation:basic:" + ticker,
                dict(method="POST", route=KIWOOM_ROUTE, api_id="ka10001", body={"stk_cd": ticker}),
            )
            identity = dict(market_type=market, list_pages=pages)
        else:
            profile = captured(
                "valuation:profile2:" + ticker,
                dict(method="GET", route=FINNHUB_BASE + "profile2", params={"symbol": ticker}),
            )
            metric = captured(
                "valuation:metric:" + ticker,
                dict(
                    method="GET",
                    route=FINNHUB_BASE + "metric",
                    params={"symbol": ticker, "metric": "all"},
                ),
            )
            official = frozen["valuation_official_identities"].get(ticker)
            identity = dict(
                profile=profile,
                official_identity=official,
                official_identity_sha256=digest(official) if official else None,
            )
        return dict(
            contract=INPUT_CONTRACT,
            provider=inventory["provider"],
            identity_inputs=identity,
            **metric,
            **common,
        )
    except LookupError as exc:
        return dict(
            contract=UNAVAILABLE_CONTRACT,
            reason=str(exc),
            run_id=plan.generation_id,
            security_sha256=digest(security),
            acquisition_binding=digest(
                dict(
                    plan=plan.plan_sha256,
                    inventory=inventory,
                    results={
                        k: v
                        for k, v in outcome["logical_results"].items()
                        if k in inventory["slots"]
                    },
                )
            ),
            **common,
        )
