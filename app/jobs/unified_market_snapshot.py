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
    if settings.unified_snapshot_adapter_version == "production-v1":
        from app.services.production_adapter_factory import build_production_adapter
        return build_production_adapter(settings)
    return UnqualifiedAdapter()


def build_engine(settings, adapter, *, repo_commit, adapter_fingerprint, clock=None):
    config = RunConfiguration(
        root=Path(settings.data_dir) / "unified-snapshot-runs",
        debug_destination=(Path(settings.unified_snapshot_debug_destination)
                           if settings.unified_snapshot_debug_destination else None),
        repo_commit=repo_commit, scheduler_identity="unified-runtime",
        adapter_fingerprint=adapter_fingerprint,
        runtime_contract=settings.unified_snapshot_runtime_contract,
        stage_timeout_seconds=600 if settings.unified_snapshot_runtime_contract.endswith("-v2") else 1200,
        collection_timeout_seconds=600 if settings.unified_snapshot_runtime_contract.endswith("-v2") else 1200,
        secrets=tuple(value.get_secret_value() if hasattr(value, "get_secret_value") else str(value)
                      for key, value in settings.model_dump().items() if value and SECRET_KEY.search(key)),
    )
    return UnifiedMarketRun(config, adapter, clock=clock)


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
    adapter = load_adapter(settings)
    engine = build_engine(settings, adapter, repo_commit=getattr(adapter, "repository_commit", "UNQUALIFIED"),
                          adapter_fingerprint=getattr(adapter, "adapter_fingerprint", "UNQUALIFIED"))
    result = await run_selected(args.market, engine,
                                datetime.now(KST).date())
    print(json.dumps([{"run_id": r["run_id"], "status": r["status"]} for r in result]))
    if any(r["status"] == "FAILED" for r in result):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
