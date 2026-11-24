"""Receipt-only Source STOP handling; no live main, commands, or model replay."""

import ast
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "ops/c44/postrun.py"
C45_COMMIT = "374145c4337d50673db672c73a49e071b1801b5b"


@pytest.fixture
def closeout(tmp_path):
    root, run, out = (tmp_path / name for name in ("code", "run", "out"))
    for path in (root / "app/services", run, out):
        path.mkdir(parents=True)
    timer = root / "app/services/research_no_send_run.py"
    timer.write_text("synthetic pinned timer\n")
    file_sha = sha256(timer.read_bytes()).hexdigest()

    def data(path, value):
        path.write_text(json.dumps(value))

    def read(path):
        return json.loads(Path(path).read_bytes())

    def write(folder, name, value):
        with (folder / name).open("x") as stream:
            json.dump(value, stream)

    terminal = dict(status="STOPPED_NO_SEND", error_type="ValueError", normal_messages_sent=False)
    diagnostic = dict(stage="SOURCE_POST_COLLECTION", NO_SEND=True,
        market="us", target_session="2026-11-23", code_commit=C45_COMMIT,
        exception_class="ValueError", stable_error_code=None, recorded_before_owner_cleanup=True,
        last_application_frame=dict(basename="production_source_seal.py", function="seal_collection", line=233))
    info = dict(execution="synthetic-c46", journal_path=str(run / "model/events.jsonl"),
        runtime_root=str(run / "model"))
    data(run / "terminal.json", terminal)
    data(run / "intent.json", dict(session="2026-11-23", code_commit=C45_COMMIT))
    data(run / "failure-diagnostic.json", diagnostic)
    data(run / "model-runtime-preflight.json", info)
    rows = [dict(event="STOP", value=dict(reason="ORIGINAL_BACKEND_AUTHORITY_REVOKED"))]
    (run / "campaign.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    schedule = dict(code_root=str(root), code_commit=C45_COMMIT, run_root=str(run),
        target_session="2026-11-23", provider_caps={}, C37_timer_sha256=file_sha,
        _current_code_pins=dict(files={"app/services/research_no_send_run.py": {"sha256": file_sha}}))
    observed = dict(journal_chain="PASS", source_accepted=False, model_plan_accepted=False,
        financial_HTTP=0, providers={}, model_calls=0, model_acceptances=0, model_retries=0)
    functions = [node for node in ast.parse(SCRIPT.read_text()).body
        if isinstance(node, ast.FunctionDef) and node.name == "verify_receipts"]
    env = dict(Path=Path, read=read, write=write, json=json,
        pin=lambda path: sha256(Path(path).read_bytes()).hexdigest(),
        command=lambda *args: C45_COMMIT, sys=SimpleNamespace(path=[]))
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(SCRIPT), "exec"), env)
    return SimpleNamespace(run=run, out=out, schedule=schedule, observed=observed,
        diagnostic=diagnostic, terminal=terminal, info=info, read=read, data=data,
        verify=lambda: env["verify_receipts"](out, schedule, observed))


def test_source_stop_without_model_artifacts_reports_not_reached_and_original_failure(closeout):
    assert closeout.verify() is False
    assert closeout.read(closeout.out / "FAILURE_DIAGNOSTIC.json") == closeout.diagnostic
    first = closeout.read(closeout.out / "FIRST_FAILURE_LOCATION.json")
    assert first["first_failure"] == closeout.diagnostic
    assert first["last_original_frame"] == closeout.diagnostic["last_application_frame"]
    assert closeout.read(closeout.run / "terminal.json") == closeout.terminal
    stages = closeout.read(closeout.out / "STAGES.json")
    assert stages["Source"] is False and stages["ModelPlan"] is False
    assert [row["stage"] for row in stages["stages"]] == ["MARKET", "CORE", "A", "B", "B2", "VALIDATE", "RENDER"]
    assert all(row["status"] == "NOT_REACHED" for row in stages["stages"])
    model = closeout.read(closeout.out / "MODEL_ATTEMPTS.json")
    assert model["status"] == "NOT_REACHED" and model["attempts"] == []
    assert model["physical_intents"] == model["actual_CLI_starts"] == model["accepted"] == model["retries"] == 0
    messages = closeout.read(closeout.out / "FINAL_MESSAGES.json")
    assert messages["status"] == "STOPPED_NO_SEND" and messages["messages"] == [] and messages["NO_SEND"] is True
    assert not Path(closeout.info["journal_path"]).exists()
    assert not (closeout.run / "results").exists()


def test_model_reached_missing_journal_is_still_a_verification_failure(closeout):
    closeout.observed.update(source_accepted=True, model_plan_accepted=True)
    inner = closeout.run / "results/unified-snapshot-runs" / closeout.info["execution"]
    inner.mkdir(parents=True)
    closeout.data(inner / "state.json", dict(status="FAILED_NO_SEND", stage_receipts=[]))
    with pytest.raises(FileNotFoundError) as raised:
        closeout.verify()
    assert raised.value.filename == closeout.info["journal_path"]
    assert closeout.read(closeout.out / "FAILURE_DIAGNOSTIC.json") == closeout.diagnostic
    assert not (closeout.out / "MODEL_ATTEMPTS.json").exists()


def test_source_stop_does_not_hide_an_existing_model_journal(closeout):
    journal = Path(closeout.info["journal_path"])
    journal.parent.mkdir()
    journal.write_text("model artifact unexpectedly exists\n")
    with pytest.raises(AssertionError):
        closeout.verify()
    assert closeout.read(closeout.out / "FAILURE_DIAGNOSTIC.json") == closeout.diagnostic
    assert not (closeout.out / "MODEL_ATTEMPTS.json").exists()


def test_source_stop_does_not_hide_a_source_acceptance_in_campaign(closeout):
    (closeout.run / "campaign.jsonl").write_text(json.dumps(dict(event="SOURCE", value={})) + "\n")
    with pytest.raises(AssertionError):
        closeout.verify()
    assert closeout.read(closeout.out / "FAILURE_DIAGNOSTIC.json") == closeout.diagnostic
    assert not (closeout.out / "FINAL_MESSAGES.json").exists()


def test_busy_other_run_defers_cleanup_without_hiding_original_receipts(tmp_path):
    from tests.test_c44_postrun import run_closeout

    summary, calls, out = run_closeout(tmp_path, full=False, lease_busy=True)
    assert summary["status"] == "C38_LIVE_PARTIAL_US_OFF"
    assert summary["actual15of15"] is False and summary["US_regular_activated"] is False
    assert summary["first_failure"] == {"code": "TRANSPORT_TIMEOUT", "stage": "B2"}
    assert summary["postrun_error"] is None
    assert summary["one_shot_cleanup"] == "DEFERRED_OTHER_RUN_ACTIVE"
    assert ("verify",) in calls and ("package",) in calls and ("clean",) not in calls
    assert not any(call and call[0] == "ps" for call in calls)
    release = json.loads((out / "RESOURCE_RELEASE.json").read_text())
    assert release["status"] == "DEFERRED_OTHER_RUN_ACTIVE"
    assert release["cleanup_performed"] is False and release["Lane_writes"] == 0
    assert "lease_free" not in release
    assert not (out / "POSTRUN_ERROR.json").exists()
