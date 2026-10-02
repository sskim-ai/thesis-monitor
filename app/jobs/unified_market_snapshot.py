"""Disabled-by-default single-run entrypoint; no implicit legacy adapter fallback."""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime
import json
from pathlib import Path

from app.config import get_settings
from app.services.unified_market_run import KST, RunConfiguration, UnifiedMarketRun
from app.services.unified_run_artifacts import SECRET_KEY


class UnqualifiedAdapter:
    async def policy(self, market, session, run_id):
        raise RuntimeError("unified_production_adapter_not_qualified")

    async def collect(self, request, directory):
        raise RuntimeError("unified_production_adapter_not_qualified")

    async def stage(self, request, directory):
        raise RuntimeError("unified_production_adapter_not_qualified")

    async def notify_failure(self, payload):
        from app.services.notification_service import TelegramNotifier

        # Existing production recipient contract. No recipient literal or investment AI.
        text = "[MONITORING OPERATIONAL FAILURE]\n" + "\n".join(
            f"{key}: {value}" for key, value in payload.items() if key != "kind")
        result = await TelegramNotifier().send({"text": text, "use_llm": False})
        return {"status": result}


def load_adapter(settings):
    # No production adapter is qualified by the state-machine fixture alone.
    # This registry stays closed until concrete source and Market/Core/A/B parity
    # is proven; a dotted-path setting cannot bypass that qualification.
    return UnqualifiedAdapter()


async def run_selected(market, engine, day):
    results = []
    for selected in ("us", "kr") if market == "all" else (market,):
        results.append(await engine.run(selected, day))
    return results


async def main():
    parser = argparse.ArgumentParser(description="Run one immutable market snapshot cycle")
    parser.add_argument("--market", choices=("us", "kr", "all"), required=True)
    args = parser.parse_args()
    settings = get_settings()
    if not settings.unified_snapshot_enabled:
        print(json.dumps({"status": "DISABLED", "mutations": 0}))
        return
    config = RunConfiguration(
        root=Path(settings.data_dir) / "unified-snapshot-runs",
        debug_destination=(Path(settings.unified_snapshot_debug_destination)
                           if settings.unified_snapshot_debug_destination else None),
        repo_commit="UNQUALIFIED", scheduler_identity=f"unified-{args.market}",
        adapter_fingerprint="UNQUALIFIED",
        secrets=tuple(str(value) for key, value in settings.model_dump().items()
                      if value and SECRET_KEY.search(key)),
    )
    result = await run_selected(args.market, UnifiedMarketRun(config, load_adapter(settings)),
                                datetime.now(KST).date())
    print(json.dumps([{"run_id": r["run_id"], "status": r["status"]} for r in result]))
    if any(r["status"] == "FAILED" for r in result):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
