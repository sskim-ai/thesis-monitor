from __future__ import annotations

import argparse
import asyncio
from datetime import date
import json

from app.providers.kiwoom_kr_market_provider import KiwoomKrMarketProvider


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Probe the authenticated Kiwoom KR market gateway")
    parser.add_argument("--date", type=date.fromisoformat)
    parser.add_argument("--live", action="store_true")
    return parser


async def _run(args: argparse.Namespace) -> dict[str, object]:
    provider = KiwoomKrMarketProvider()
    if not args.live:
        return {
            "status": "NOT_CONFIGURED" if not provider.configured else "configured_not_run",
            "production_role": provider.provider_role,
            "gateway_contract": "kiwoom-kr-market-gateway-v1",
            "reason": "Pass --live to query a configured authenticated Windows gateway.",
        }
    capabilities = await provider.capabilities()
    result: dict[str, object] = {
        "status": "ok",
        "production_role": provider.provider_role,
        "efficient_breadth_supported": capabilities.efficient_breadth_supported,
        "capabilities": [item.model_dump(mode="json") for item in capabilities.metrics],
    }
    if args.date and capabilities.efficient_breadth_supported:
        section = await provider.collect(args.date)
        result["snapshot"] = section.model_dump(mode="json")
    return result


def main() -> None:
    result = asyncio.run(_run(_parser().parse_args()))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
