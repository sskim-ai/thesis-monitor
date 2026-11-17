"""Shared local receipt operations; no dispatch or historical controller."""
import json
from app.services.unified_snapshot_contract import digest  # noqa: F401

class BatchFailure(ValueError):
    pass

def require(ok, code):
    if not ok:
        raise BatchFailure(code)

def read(path):
    return json.loads(path.read_bytes())

def write(path, value):
    from app.services.research_artifact_budget import active_budget
    if active_budget() is not None:
        from app.services.unified_run_artifacts import durable_bytes
        durable_bytes(path, (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str) + '\n').encode())
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str) + "\n")
