from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/m12cg_r1_offline_proof.py"
SPEC = importlib.util.spec_from_file_location("m12cg_r1_offline_proof", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_json_pointer_diffs_reports_exact_nested_pointer() -> None:
    assert MODULE.json_pointer_diffs(
        {"rows": [{"value": 1}]},
        {"rows": [{"value": 2}]},
    ) == [
        {
            "pointer": "/rows/0/value",
            "kind": "VALUE_CHANGED",
            "before": 1,
            "after": 2,
        }
    ]


def test_row_projection_removes_only_runtime_owned_fields() -> None:
    row = {
        "driver": "driver",
        "as_of": None,
        "provenance_status": "SYMBOLIC_ONLY_NO_CONCRETE_DATE",
        "supporting_evidence_refs": ["canonical:financial_quality:latest"],
    }
    assert MODULE.strip_runtime_row_fields(row) == {
        "driver": "driver",
        "supporting_evidence_refs": ["canonical:financial_quality:latest"],
    }
    assert row["as_of"] is None
    assert row["provenance_status"] == "SYMBOLIC_ONLY_NO_CONCRETE_DATE"


def test_historical_ephemeral_projection_preserves_nonruntime_fields() -> None:
    original = {
        "contract": "v2-accepted-production-output-v1",
        "candidates": [
            {
                "ticker": "010120",
                "driver_maturity": [
                    {
                        "driver": "driver",
                        "as_of": "2026-09-15",
                        "maturity": "CONFIRMED",
                        "supporting_evidence_refs": ["ref"],
                    }
                ],
            }
        ],
    }
    projected = MODULE.historical_ephemeral_raw(original)
    assert projected["contract"] == MODULE.STAGE2_MODEL_OUTPUT_CONTRACT
    assert projected["candidates"][0]["driver_maturity"][0] == {
        "driver": "driver",
        "maturity": "CONFIRMED",
        "supporting_evidence_refs": ["ref"],
    }
    assert original["candidates"][0]["driver_maturity"][0]["as_of"] == "2026-09-15"


def test_artifact_manifest_excludes_itself(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "artifact-manifest.json").write_text("{}", encoding="utf-8")
    manifest = MODULE.artifact_manifest(tmp_path)
    assert manifest["manifest_self_excluded"] is True
    assert [row["path"] for row in manifest["artifacts"]] == ["a.txt"]
