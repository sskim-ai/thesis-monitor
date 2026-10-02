"""Reproducible orchestration fixtures, explicitly not production adapter qualification."""

import argparse
import asyncio
from datetime import date
import importlib.util
from pathlib import Path
import plistlib
import tempfile

from app.services.unified_run_artifacts import durable_bytes, durable_json
from app.services.unified_scheduler_plan import migration_plan


def proof(output: Path):
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("snapshot_fixture", root / "tests/test_unified_market_snapshot.py")
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    rows = []
    with tempfile.TemporaryDirectory(prefix="unified-offline-proof-") as temporary:
        private = Path(temporary)
        for market in ("us", "kr"):
            for failures in range(4):
                case = f"{market}-collection-{failures}-incomplete"
                work = private / case
                work.mkdir()
                engine, ports, clock = fixture.setup(work, market, failed_attempts=failures)
                result = fixture.execute(engine, market)
                row = {"case": case, "fixture_only": True, "result": result,
                       "collection_calls": len(ports.collections),
                       "stage_order": [r["stage"] for r in ports.stages],
                       "snapshot_hashes": sorted({r["snapshot_sha256"] for r in ports.stages}),
                       "waits": [w.isoformat() for w in clock.waits],
                       "notification_fixture_calls": len(ports.notifications), "real_sends": 0}
                assert result["status"] == ("FAILED" if failures == 3 else "SUCCESS")
                assert len(ports.collections) == min(failures + 1, 3)
                rows.append(row)
                if market == "us" and failures == 3:
                    bundle = next(engine.config.root.glob("*/*-debug.zip"))
                    durable_bytes(output / "debug-fixture" / bundle.name, bundle.read_bytes(), exclusive=True)
                    durable_bytes(output / "debug-fixture" / (bundle.name + ".sha256"),
                                  bundle.with_suffix(".zip.sha256").read_bytes(), exclusive=True)
                    durable_json(output / "failure-notification-fixture.json", ports.notifications[0], exclusive=True)
        for stage in fixture.STAGES:
            work = private / stage
            work.mkdir()
            engine, ports, _ = fixture.setup(work, fail_stage=stage)
            result = fixture.execute(engine)
            assert result["status"] == "FAILED" and len(ports.collections) == 1
            rows.append({"case": "downstream-" + stage, "fixture_only": True, "result": result,
                         "collection_calls": len(ports.collections), "stage_order": [r["stage"] for r in ports.stages]})
        work = private / "all-holiday"
        work.mkdir()
        engine, ports, _ = fixture.setup(work, day=date(2026, 9, 25))
        result = asyncio.run(fixture.run_selected("all", engine, date(2026, 9, 25)))
        assert [r["status"] for r in result] == ["SUCCESS", "SKIPPED"]
        rows.append({"case": "all-kr-holiday-us-eligible", "fixture_only": True, "result": result})
    durable_json(output / "state-machine-proof.json", {"fixture_only": True, "rows": rows}, exclusive=True)
    plan = migration_plan(Path("/configured/operating"), Path("/configured/operating/.venv/bin/python"),
                          host_timezone="Asia/Seoul")
    durable_json(output / "scheduler-migration-plan.json", plan, exclusive=True)
    for agent in plan["new_agents"]:
        durable_bytes(output / "inactive-scheduler-templates" / (agent["Label"] + ".plist"),
                      plistlib.dumps(agent), exclusive=True)
    durable_json(output / "network-model-production-counters.json", {
        "real_provider_calls": 0, "alpha_vantage_calls": 0, "massive_calls": 0,
        "model_calls": 0, "telegram_sends": 0, "scheduler_mutations": 0,
        "production_database_mutations": 0, "push": 0, "deploy": 0,
        "proof_kind": "OFFLINE_ORCHESTRATION_FIXTURE_ONLY",
    }, exclusive=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    proof(args.output)
