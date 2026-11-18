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


def load_adapter(settings, **prepared):
    if settings.unified_snapshot_adapter_version == "production-v1":
        from app.services.production_adapter_factory import build_production_adapter
        return build_production_adapter(settings, **prepared)
    if prepared:
        raise ValueError('prepared_cycle_production_registry_required')
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


async def run_registered(settings, *, source, model=None, mode='SOURCE_ONLY', clock=None,
                         manual_source_seconds=None):
    """Explicit registered cycle for manual and future scheduler callers.

    Callers supply the original approval/Owner/ledger and already frozen plan;
    neither settings nor this entry issues permissions or installs a trigger.
    """
    from app.services.production_source_backend import CanonicalProductionSourceBackend
    from app.services.unified_snapshot_contract import digest

    if mode not in {'SOURCE_ONLY', 'LIVE_NO_SEND'} or mode == 'SOURCE_ONLY' and model is not None:
        raise ValueError('registered_cycle_source_only_or_explicit_no_send_required')
    if mode == 'LIVE_NO_SEND' and (not model or model.get('run_ledger') is not source.get('run_ledger')):
        raise ValueError('registered_cycle_same_source_model_ledger_required')
    if manual_source_seconds is not None and mode != 'LIVE_NO_SEND':
        raise ValueError('registered_manual_source_budget_requires_no_send')
    if {'manual_source_seconds', 'manual_no_send'} & source.keys():
        raise ValueError('registered_manual_source_budget_requires_explicit_entry_argument')
    options = {} if manual_source_seconds is None else dict(
        manual_no_send=True, manual_source_seconds=manual_source_seconds)
    child, proof = await CanonicalProductionSourceBackend.prepare_registered(settings=settings, **source, **options)
    try:
        child.verify()
        if mode == 'SOURCE_ONLY':
            return dict(status='SOURCE_ADMISSION_PASS', market=child.market,
                model_plan_sha256=child.plan.sha256, model_slots=len(child.plan.slots),
                source_acceptance_sha256=digest(child.owner.acceptance()), normal_messages_sent=False)
        model_options = dict(model)
        model_options.setdefault('approved_plan_sha256', child.plan.sha256)
        adapter = load_adapter(settings, child=child, clock=clock, **model_options)
        source['run_ledger'].bind_model_plan(child)
        engine = build_engine(settings, adapter, repo_commit=source['frozen']['stock_plan']['implementation_sha'],
            adapter_fingerprint=digest(child.binding()), clock=clock)
        return await engine.run(child.market, datetime.fromisoformat(child.plan.cohort.cutoff).astimezone(KST).date())
    finally:
        child.owner.close()


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
