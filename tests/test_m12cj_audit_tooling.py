from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import zipfile

from scripts.m12cj_current_market_smoke import json_value
from scripts.m12cj_monitored_stock_smoke import (
    banned_key_paths,
    facts_only,
    zip_tree,
)


@dataclass
class _ProviderResult:
    provider: str
    telemetry: dict[str, object]


def test_current_market_audit_serializes_dataclass_provider_result() -> None:
    value = json_value(
        _ProviderResult(provider="official", telemetry={"queried_dates": ["2026-09-16"]})
    )

    assert value == {
        "provider": "official",
        "telemetry": {"queried_dates": ["2026-09-16"]},
    }


def test_facts_only_removes_ai_verdict_fields_recursively() -> None:
    source = {
        "ticker": "TEST",
        "fact_catalog": [{"fact_id": "fact:1", "value": 10}],
        "nested": {
            "decision": "BUY",
            "new_buyer_axis": {"stance": "BUY_NOW"},
            "holder_result": "HOLD",
            "overall_maturity": "POSTCONFIRMATION",
            "safe": "retained",
        },
    }

    sanitized = facts_only(source)

    assert sanitized["nested"] == {"safe": "retained"}
    assert banned_key_paths(sanitized) == []
    assert source["nested"]["decision"] == "BUY"


def test_sealed_zip_manifest_excludes_itself_from_nested_manifest(tmp_path: Path) -> None:
    source = tmp_path / "sealed"
    source.mkdir()
    (source / "output.json").write_text(
        json.dumps({"decision": "HOLD"}), encoding="utf-8"
    )
    destination = tmp_path / "sealed-ai-verdicts.zip"

    receipt = zip_tree(source, destination)

    assert receipt["nested_file_count"] == 2
    with zipfile.ZipFile(destination) as archive:
        assert sorted(archive.namelist()) == ["output.json", "sealed-manifest.json"]
        manifest = json.loads(archive.read("sealed-manifest.json"))
    assert manifest["file_count"] == 1
    assert manifest["self_exclusion"].startswith("sealed-manifest.json")
