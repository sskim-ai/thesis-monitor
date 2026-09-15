from __future__ import annotations

import json
from pathlib import Path

from scripts import fresh_monitored_semantic_convergence_m12bh as audit


def test_debt_report_payloads_stop_without_network_or_model_calls(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(audit, "REPORTS", tmp_path / "reports")
    monkeypatch.setattr(audit, "OUTPUT", tmp_path / "artifacts")
    corpus = audit.golden_corpus()
    payloads = audit._report_payloads(
        {
            "status": "PASS",
            "actual_sha256": audit.LATEST_RESULT_SHA256,
        },
        corpus,
        audit._entrypoint_map(),
        {"hit_count": 0, "classification_counts": {}, "rows": []},
    )

    assert payloads[17]["semantic_convergence_audit_status"] == ("CONVERGENCE_DEBT_PRESENT")
    assert payloads[45]["status"] == "STOP_BEFORE_SHADOW"
    assert payloads[45]["model_calls"] == 0
    assert payloads[45]["network_gate_attempts"] == 0
    assert payloads[105]["decision"] == "NO_NETWORK_GATE_AND_NO_SHADOW"


def test_bundle_index_excludes_itself(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "artifacts"
    reports = tmp_path / "reports"
    output.mkdir()
    reports.mkdir()
    monkeypatch.setattr(audit, "OUTPUT", output)
    monkeypatch.setattr(audit, "REPORTS", reports)
    monkeypatch.setattr(audit, "RUNNER", tmp_path / "missing-runner.py")
    monkeypatch.setattr(audit, "ARCHITECTURE", tmp_path / "missing-architecture.md")
    monkeypatch.setattr(audit, "WORK_INSTRUCTION", tmp_path / "missing-instruction.md")
    monkeypatch.setattr(audit, "artifact_files", lambda: [output / "program-completion.json"])

    completion = audit.build_completion(
        {"status": "PASS", "actual_sha256": audit.LATEST_RESULT_SHA256},
        audit.golden_corpus(),
        {
            "focused_test_result": "PASS",
            "full_test_result": "PASS",
            "ruff_result": "PASS",
            "git_diff_check": "PASS",
        },
    )
    audit.write_json(output / "program-completion.json", completion)
    for number, slug in enumerate(audit.BASE_REPORT_SLUGS, start=1):
        audit.report(number, slug, {"status": "TEST"})
    for number, slug in enumerate(audit.DEBT_REPORT_SLUGS, start=40):
        audit.report(number, slug, {"status": "TEST"})
    for number, slug in enumerate(audit.COMPLETION_REPORT_SLUGS, start=104):
        audit.report(number, slug, {"status": "TEST"})

    bundle = tmp_path / "result.zip"
    audit.bundle(bundle)

    index = json.loads((output / "artifact-index.json").read_text())
    assert index["status"] == "PASS"
    assert index["artifact_count"] == 1
    assert index["rows"][0]["path"] == "program-completion.json"
    assert bundle.is_file()
    assert Path(str(bundle) + ".sha256").is_file()
