from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from scripts.m12cg_r3_native_probe import export_fixture


class _Dumpable:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def model_dump(self, *, mode: str) -> dict[str, object]:
        assert mode == "json"
        return self.payload


def test_export_fixture_returns_complete_non_null_manifest_row(tmp_path: Path) -> None:
    fixture = SimpleNamespace(
        name="fixture-a",
        ticker="TEST",
        packet={"packet_id": "packet-a"},
        output={"packet_id": "packet-a", "claim_id": "claim-a"},
        raw_output={"contract": "raw-v1"},
        normalized_output=_Dumpable({"contract": "normalized-v1"}),
        artifact=_Dumpable({"contract": "artifact-v1"}),
        source_paths={"context": "/frozen/context.json"},
        source_hashes={"context": "a" * 64},
        transformations={"projection": "TEST_ONLY"},
    )

    result = export_fixture(tmp_path, fixture)

    assert result["fixture_name"] == "fixture-a"
    assert result["ticker"] == "TEST"
    assert result["source_hashes"] == {"context": "a" * 64}
    assert result["transformations"] == {"projection": "TEST_ONLY"}
    assert set(result["exported_files"]) == {
        "packet",
        "ai_output",
        "raw_stage2",
        "normalized_stage2",
        "artifact",
    }
    for row in result["exported_files"].values():
        path = tmp_path / row["path"]
        assert path.is_file()
        assert row["size"] == path.stat().st_size
        assert len(row["sha256"]) == 64
