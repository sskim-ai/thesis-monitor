from __future__ import annotations

from datetime import UTC, datetime
import inspect
from pathlib import Path
import subprocess

import pytest

from scripts import kr_financial_coldstart_repair_m12bp as proof
from scripts import new_issuer_holdout_selection_ownership_proof as fresh


def test_m12bp_contract_freezes_one_two_stage_twelve_subject_proof() -> None:
    assert proof.MODEL == "gpt-5.6-sol"
    assert proof.EFFORT == "xhigh"
    assert proof.TARGET_TOTAL == 12
    assert proof.MAX_SUBJECTS_PER_CALL == 4
    assert proof.PLANNED_MODEL_CALLS == 6
    assert len(proof.REPORT_SLUGS) == 74
    assert proof.REPORT_SLUGS[28] == "production-firewall-model-call-gate"
    assert proof.REPORT_SLUGS[73] == "program-completion"


def test_generation_id_is_deterministic_and_m12bp_scoped() -> None:
    when = datetime(2026, 9, 15, 3, 0, tzinfo=UTC)

    first = proof.generation_id("abc123", when)
    second = proof.generation_id("abc123", when)

    assert first == second
    assert first.startswith("20260915-m12bp-fresh-20260915T030000Z-")
    assert proof.generation_id("def456", when) != first


def test_fresh_runner_keeps_legacy_stop_default_and_exposes_bounded_override() -> None:
    signature = inspect.signature(fresh.execute_run)
    parameter = signature.parameters["stop_on_candidate_semantic_failure"]

    assert parameter.default is True
    assert parameter.annotation in {bool, "bool"}


def test_financial_candidate_fixture_partition_is_exact() -> None:
    holdings = {"138930", "139130", "316140", "086790"}
    insurers = {"000810", "032830"}

    assert set(proof.SIX_FINANCIAL_CANDIDATES) == holdings | insurers
    assert holdings.isdisjoint(insurers)


def test_workload_observer_treats_explicitly_unloaded_service_as_inactive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observer = proof.M12BPWorkloadObserver(uid=501)
    monkeypatch.setattr(observer, "_natural_job_labels", lambda: ["stale.job"])
    monkeypatch.setattr(
        proof.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0],
            113,
            stdout="",
            stderr='Could not find service "stale.job" in domain for user gui: 501',
        ),
    )

    active_count, rows = observer._natural_jobs()

    assert active_count == 0
    assert rows == [
        {
            "label": "stale.job",
            "state": "unloaded",
            "active": False,
            "observation": "launchctl_service_not_loaded",
        }
    ]


def test_workload_observer_keeps_unknown_launchctl_failure_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observer = proof.M12BPWorkloadObserver(uid=501)
    monkeypatch.setattr(observer, "_natural_job_labels", lambda: ["unknown.job"])
    monkeypatch.setattr(
        proof.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 1, stdout="", stderr="permission denied"
        ),
    )

    with pytest.raises(
        proof.guarded.LiveWorkloadObservationUnavailable,
        match="launch_agent_state_unavailable:unknown.job",
    ):
        observer._natural_jobs()


def test_report_secret_scan_avoids_self_and_risk_slug_false_positives(
    tmp_path: Path,
) -> None:
    benign = tmp_path / "risk-context.txt"
    benign.write_text("bounded risk-context report\n", encoding="utf-8")

    result = proof._secret_scan([Path(proof.__file__), benign])

    assert result["status"] == "PASS"
    assert result["secret_scan_failure_count"] == 0


def test_report_secret_scan_detects_supported_secret_shapes(tmp_path: Path) -> None:
    synthetic = tmp_path / "synthetic-secrets.txt"
    synthetic.write_text(
        "OPENAI_API_KEY=" + "sk-" + "a" * 32 + "\n"
        + "TELEGRAM_" + "BOT_TOKEN = synthetic\n"
        + "-----BEGIN " + "PRIVATE KEY-----\n",
        encoding="utf-8",
    )

    result = proof._secret_scan([synthetic])

    assert result["status"] == "FAIL"
    assert result["secret_scan_failure_count"] == 3
    assert {row["pattern"] for row in result["findings"]} == {
        "openai_key",
        "private_key",
        "telegram_token_marker",
    }
