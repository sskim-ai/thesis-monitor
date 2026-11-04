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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str) + "\n")
