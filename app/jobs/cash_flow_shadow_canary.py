from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from app.services.cash_flow_runtime_shadow_canary_service import (
    run_cash_flow_runtime_shadow_canary,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a delivery-isolated cash-flow shadow canary."
    )
    parser.add_argument("--packet-id", required=True)
    parser.add_argument("--delivery-mode", required=True)
    parser.add_argument("--delivery-result-sha256", required=True)
    args = parser.parse_args()
    result = run_cash_flow_runtime_shadow_canary(
        args.packet_id,
        delivery_mode=args.delivery_mode,
        expected_delivery_sha256=args.delivery_result_sha256,
    )
    print(json.dumps(asdict(result), ensure_ascii=False))


if __name__ == "__main__":
    main()
