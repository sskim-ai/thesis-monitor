from pathlib import Path

import pytest

from scripts.approved_scope_descendants import PINS, approved_descendant
from scripts import financial_exclusion_expectation_m12u as u
from scripts import sol_restoration_m12w as w
from scripts import boundary_band_application_scope_m12aa as aa
from scripts import leverage_hold_sell_boundary_m12ab as ab


def test_approved_descendants_require_exact_ancestor_blobs():
    for path in PINS:
        assert approved_descendant(path), path
    assert approved_descendant("app/services/daily_monitor_service.py") is None


@pytest.mark.parametrize("protected_test", ["M12E", "M12U", "M12F", "M12W", "M12AA", "M12AB"])
def test_each_migrated_scope_still_detects_unauthorized_owner_mutation(monkeypatch, protected_test):
    target = "app/services/daily_digest_renderer.py"
    original = Path.read_bytes

    def mutated(path):
        payload = original(path)
        return payload + b"\n# unauthorized mutation\n" if str(path) == target else payload

    monkeypatch.setattr(Path, "read_bytes", mutated)
    assert approved_descendant(target) is None
    if protected_test in {"M12E", "M12U", "M12F"}:
        assert target in u.scope_audit()["unexpected_file_changes"]
    elif protected_test == "M12W":
        assert target in w.freeze()["changed_existing_paths"]
    else:
        assert (aa if protected_test == "M12AA" else ab)._freeze_paths((target,))["status"] == "FAIL"
