from __future__ import annotations

from pathlib import Path

from scripts import persistence_v2_local_proof_m12bn as runner


def test_required_report_inventory_is_exact() -> None:
    assert len(runner.REPORT_SLUGS) == 113
    assert len(set(runner.REPORT_SLUGS)) == 113
    assert runner.REPORT_SLUGS[0] == "repository-provenance"
    assert runner.REPORT_SLUGS[-1] == "program-completion"


def test_bundle_inventory_excludes_raw_model_material() -> None:
    forbidden = ("model-calls", "prompt.txt", "output.raw.json", "transport.log")
    paths = tuple(str(path) for path in runner.artifact_files())
    assert not any(marker in path for path in paths for marker in forbidden)


def test_runner_has_no_network_or_external_sender_imports() -> None:
    source = Path(runner.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "import requests",
        "import httpx",
        "import telegram",
        "from telegram",
        "subprocess.run(['git', 'push",
    ):
        assert forbidden not in source
