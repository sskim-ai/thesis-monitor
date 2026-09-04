from __future__ import annotations

import argparse
import asyncio
import json

from app.config import get_settings
from app.jobs.accepted_decision_v2_runtime import (
    generate as generate_v2,
    record_unexpected_terminal_failure,
    v2_interruption_signal_context,
)
from app.jobs.decision_canary import generate as generate_v1


async def _run(args: argparse.Namespace) -> None:
    settings = get_settings()
    v2_active = settings.visible_stock_decision_engine == "v2_accepted"
    try:
        if v2_active:
            result = await generate_v2(args.packet_id, args.claim_id, timeout=args.timeout)
        else:
            result = await generate_v1(args.packet_id, args.claim_id, timeout=args.timeout)
    except Exception as exc:
        if v2_active:
            record_unexpected_terminal_failure(
                args.packet_id,
                args.claim_id,
                reason=f"UNEXPECTED:{type(exc).__name__}",
            )
        raise
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("generate",))
    parser.add_argument("--packet-id", required=True)
    parser.add_argument("--claim-id", required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    with v2_interruption_signal_context():
        asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    main()
