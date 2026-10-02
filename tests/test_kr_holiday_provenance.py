from pathlib import Path

import pytest

from scripts import approved_scope_descendants as provenance


def test_holiday_descendant_requires_reviewed_bytes_and_ancestry(monkeypatch):
    receipt = provenance.approved_descendant(provenance.KR_HOLIDAY_PATH)
    assert receipt and receipt["exact_blob_verified"]
    assert receipt["sha256"] == provenance.KR_HOLIDAY_AFTER
    assert receipt["implementation_commit"] == provenance.KR_HOLIDAY_IMPLEMENTATION
    observed = Path(provenance.KR_HOLIDAY_PATH).read_bytes()
    assert provenance._kr_holiday_approval(observed + b"\n") is None
    monkeypatch.setattr(provenance, "_ancestor", lambda commit: False)
    assert provenance._kr_holiday_approval(observed) is None


@pytest.mark.parametrize("ref", [
    provenance.KR_HOLIDAY_IMPLEMENTATION,
    provenance.KR_HOLIDAY_INSTRUCTION,
])
def test_holiday_descendant_rejects_wrong_parent(monkeypatch, ref):
    original = provenance._git

    def git(*args):
        if args == ("show", "-s", "--format=%P", ref):
            return b"wrong-parent"
        return original(*args)

    monkeypatch.setattr(provenance, "_git", git)
    assert provenance.approved_descendant(provenance.KR_HOLIDAY_PATH) is None


@pytest.mark.parametrize("ref", [
    provenance.KR_HOLIDAY_INSTRUCTION,
    provenance.KR_HOLIDAY_IMPLEMENTATION,
    "HEAD",
])
def test_holiday_descendant_rejects_changed_commit_blob(monkeypatch, ref):
    original = provenance._git

    def git(*args):
        value = original(*args)
        if args == ("show", f"{ref}:{provenance.KR_HOLIDAY_PATH}"):
            return value + b"\n"
        return value

    monkeypatch.setattr(provenance, "_git", git)
    assert provenance.approved_descendant(provenance.KR_HOLIDAY_PATH) is None
