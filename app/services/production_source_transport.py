"""Native acquisition transports with bounded child ownership and raw receipts."""
import asyncio
import json
import os
from pathlib import Path
import sys
import time

import httpx

from app.services.canonical_source_acquisition import acquire_all
from app.services.production_source_context import POLICY
from app.services.production_source_dispatch import ProductionSourceDispatcher
from app.services.production_source_seal import read
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest

ROOT = Path(__file__).resolve().parents[2]


async def acquire_kis_worker(*, root, frozen, plan, credentials, remaining):
    path = root / "production-frozen-source-plan.json"
    frame = dict(contract="production-kis-worker-authorization-v1", root=str(root),
        frozen_sha256=sha256_bytes(path.read_bytes()), plan_sha256=digest(plan), seconds_remaining=remaining,
        credentials=dict(app_key=credentials["kis"][0], app_secret=credentials["kis"][1]))
    env = {k: os.environ[k] for k in ("PATH", "HOME", "TMPDIR", "LANG") if k in os.environ}
    env.update(PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE="1", THESIS_MONITOR_ENV_FILE="",
        DATABASE_URL="sqlite://", NOTIFICATION_DRY_RUN="true", ENABLE_LIVE_PROVIDERS="false",
        UNIFIED_SNAPSHOT_ENABLED="false")
    process = await asyncio.create_subprocess_exec(sys.executable, "-B", "-m", "app.jobs.production_kis_worker",
        cwd=ROOT, env=env, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    try:
        stdout, _ = await asyncio.wait_for(process.communicate(json.dumps(frame).encode()), remaining)
    except BaseException:
        if process.returncode is None:
            process.kill()
        await process.wait()
        durable_json(root / "kis-worker-exit.json", dict(status="INTERRUPTED", child_reaped=True), exclusive=True)
        raise
    finally:
        frame["credentials"].clear()
    receipt = dict(status="PASS" if process.returncode == 0 else "FAIL", returncode=process.returncode,
                   child_reaped=True, generation_id=frozen["generation_id"])
    durable_json(root / "kis-worker-exit.json", receipt, exclusive=True)
    if process.returncode != 0 or json.loads(stdout)["terminal"] != "KIS_FRESH_ACQUISITION_COMPLETE_REPLAY_REQUIRED":
        raise ValueError("production_kis_acquisition_failed")


class NativeProductionSourceTransport:
    def __init__(self, settings, *, http_transport_factory=None, kis_worker=acquire_kis_worker):
        self.settings = settings
        self.http_transport_factory = http_transport_factory or (lambda: httpx.AsyncHTTPTransport(retries=0))
        self.kis_worker = kis_worker

    async def collect(self, *, root, frozen, compiler, kis_plan, credentials, deadline):
        plan_path = root / "production-frozen-source-plan.json"
        initial = sha256_bytes(plan_path.read_bytes())
        dispatcher = ProductionSourceDispatcher(plan=frozen["plan"], root=root / "dispatch", compiler_args=compiler,
            kis_plan=kis_plan, config_identities=frozen["config_identities"],
            credential_presence={k: all(v) for k, v in credentials.items()}, repository_root=ROOT,
            secrets=tuple(v for values in credentials.values() for v in values if v != "NO_CREDENTIAL_REQUIRED"))

        def guard():
            if time.monotonic() >= deadline or sha256_bytes(plan_path.read_bytes()) != initial:
                raise ValueError("production_source_deadline_or_plan_drift")

        await acquire_all(root=root, frozen=frozen, settings=self.settings, dispatcher=dispatcher,
            inner=self.http_transport_factory(), policy=POLICY, guard=guard)
        outcome = read(root / "acquisition-outcome.json")
        if "systemic_stop" in outcome["phases"]:
            raise ValueError("production_source_systemic_stop")
        if kis_plan is not None:
            guard()
            await self.kis_worker(root=root, frozen=frozen, plan=kis_plan, credentials=credentials,
                                  remaining=deadline - time.monotonic())
        return outcome
