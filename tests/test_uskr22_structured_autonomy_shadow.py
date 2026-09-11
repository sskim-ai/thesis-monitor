from __future__ import annotations

from pathlib import Path

from scripts.uskr22_structured_autonomy_shadow import (
    isolated_model_working_directory,
)


def test_model_working_directories_are_empty_ephemeral_and_isolated() -> None:
    with isolated_model_working_directory(run="first", batch=1) as first:
        assert list(first.iterdir()) == []
        (first / "prior-candidate.json").write_text("{}", encoding="utf-8")
        first_path = Path(first)

    assert not first_path.exists()

    with isolated_model_working_directory(run="first", batch=2) as second:
        assert second != first_path
        assert list(second.iterdir()) == []
        assert not (second / "prior-candidate.json").exists()

