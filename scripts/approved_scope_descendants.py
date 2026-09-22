"""Exact accepted descendants for historical global scope freezes, not path exemptions."""
from hashlib import sha256
from pathlib import Path
import subprocess


# Each pin names the implementation owner reviewed under its frozen instruction.
PINS = {
    "app/services/ai_review_service.py": ("M12DI", "5c757226f8c447cb93508e7bb34017c7b0f71af3"),
    "tests/test_ai_review_service.py": ("M12DI", "5c757226f8c447cb93508e7bb34017c7b0f71af3"),
    "app/services/financial_backfill_service.py": ("M12DQ", "d9907928dd659325fcec074f727e2005871acd79"),
    **{p: ("M12DS-R4-R1", "24cab21ba006412dcd11d22ada4c2fd6eab07a88") for p in (
        "app/macro/briefing.py",
        "app/services/night_futures_visibility_service.py",
        "app/services/valuation_snapshot_service.py",
    )},
    "app/services/sec_financial_snapshot_service.py": (
        "M12DS-R4-R3", "b3f89e4546b4d0783ba76870d2e890fe31b07e0d"),
    "app/services/daily_digest_renderer.py": ("M12DS-R4-R1", "dc8561e0fa199e5360eb4fda4bd59ac72fdffe09"),
}


def approved_descendant(path):
    pin = PINS.get(path)
    if pin is None or not Path(path).is_file():
        return None
    owner, commit = pin
    try:
        subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        expected = subprocess.check_output(["git", "show", f"{commit}:{path}"], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return None
    observed = Path(path).read_bytes()
    if observed != expected:
        return None
    return {"owner": owner, "commit": commit, "path": path, "sha256": sha256(expected).hexdigest(),
            "ancestor_verified": True, "exact_blob_verified": True}
