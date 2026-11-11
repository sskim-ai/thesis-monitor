"""Bounded worker for the existing synchronous KIS transport; no scheduler."""
import json
from pathlib import Path
import sys
import time

from app.services.production_kis_sources import current_inventories, _source_plan
from app.services.production_source_seal import read
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest
from scripts import kr8_kis_integration as kis


def run(frame):
    if (set(frame) != {"contract", "root", "frozen_sha256", "plan_sha256", "seconds_remaining", "credentials"}
            or frame["contract"] != "production-kis-worker-authorization-v1"
            or not 0 < frame["seconds_remaining"] <= 600):
        raise ValueError("production_kis_worker_authorization")
    root = Path(frame["root"])
    if not root.is_absolute() or any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError("production_kis_worker_root")
    frozen_path = root / "production-frozen-source-plan.json"
    frozen, plan = read(frozen_path), read(root / "kis-plan.json")
    if (sha256_bytes(frozen_path.read_bytes()) != frame["frozen_sha256"]
            or digest(plan) != frame["plan_sha256"]
            or _source_plan(frozen).kis_plan_sha256 != digest(plan)):
        raise ValueError("production_kis_worker_frozen_binding")
    outcome = read(root / "acquisition-outcome.json")
    inventory = current_inventories(root, frozen, outcome)
    deadline = time.monotonic() + frame["seconds_remaining"]
    accounting=None
    if frozen.get('scope')=='SELECTED_ORIGINAL_RESEARCH_V1':
        from app.services.selected_run_lifecycle import SelectedRunLedger
        accounting=SelectedRunLedger.attach_worker(frozen['shared_run_ledger'])
        child=accounting.identity['children']['kr']
        original_plan=_source_plan(frozen)
        if (child['generation']!=frozen['generation_id'] or tuple(child['subjects'])!=original_plan.subjects
                or accounting.state()['plans'].get('kr')!=original_plan.plan_sha256):
            raise ValueError('selected_kis_worker_shared_scope_changed')

    def guard():
        if (time.monotonic() >= deadline or sha256_bytes(frozen_path.read_bytes()) != frame["frozen_sha256"]
                or digest(read(root / "kis-plan.json")) != frame["plan_sha256"]):
            raise ValueError("production_kis_worker_deadline_or_plan_drift")

    credentials = kis.base.Credentials(**frame["credentials"])
    frame["credentials"].clear()
    extra={} if accounting is None else dict(physical_accounting=accounting,
        source_plan_sha256=_source_plan(frozen).plan_sha256)
    return kis.acquire(root / "kis", plan=plan, credentials=credentials, inventories=inventory,
                       static=root / "static/kis", guard=guard,**extra)


def main():
    try:
        terminal = run(json.loads(sys.stdin.buffer.read()))
    except Exception as exc:
        # Exceptions can contain credential-bearing URLs; only the type exits.
        print(json.dumps({"status": "FAIL", "error_type": type(exc).__name__}), flush=True)
        raise SystemExit(1) from None
    print(json.dumps({"terminal": terminal}), flush=True)
    if terminal != "KIS_FRESH_ACQUISITION_COMPLETE_REPLAY_REQUIRED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
