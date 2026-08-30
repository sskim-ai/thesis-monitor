from __future__ import annotations

import argparse
import asyncio
import json

from app.config import get_settings
from app.jobs.accepted_decision_v2_runtime import generate as generate_v2
from app.jobs.decision_canary import generate as generate_v1


async def _run(args: argparse.Namespace) -> None:
    settings = get_settings()
    if settings.visible_stock_decision_engine == "v2_accepted":
        result = await generate_v2(args.packet_id, args.claim_id, timeout=args.timeout)
    else:
        result = await generate_v1(args.packet_id, args.claim_id, timeout=args.timeout)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("generate",))
    parser.add_argument("--packet-id", required=True)
    parser.add_argument("--claim-id", required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    main()
