"""C44 closeout control flow only; no Mac commands, receipt replay, or network.

The script has a process-wide audit hook, so extract its main and schedule loader
instead of importing the module. All process, observation, receipt verification,
cleanup, and delivery boundaries are fakes; file writes use pytest's temp tree.
"""
import ast
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "ops/c44/postrun.py"
KST = ZoneInfo("Asia/Seoul")
REGULAR_LABEL = "local.thesis-monitor.canonical.us.no-send"
POSTRUN_LABEL = "local.thesis-monitor.us.postrun.once.c38.20261124"


def run_closeout(tmp_path, *, full, receipt_error=False, cleanup_error=False, mutate_kr=False):
    """Run the real main body with every external boundary replaced."""
    here = tmp_path / "postrun"
    c38 = tmp_path / "c38"
    run = tmp_path / "run"
    lane = tmp_path / "lane/state.json"
    lease = tmp_path / "lease"
    private_tmp = tmp_path / "private-tmp"
    delivery = tmp_path / "delivery"
    for path in (here, c38, run, lane.parent, private_tmp, delivery):
        path.mkdir(parents=True)
    lease.touch()
    (lane.parent / "lane.lock").touch()
    kr_files = {key: tmp_path / key for key in ("kr_config", "kr_plist")}
    for key, path in kr_files.items():
        path.write_text("current approved C42 " + key)

    def pin(path):
        return sha256(Path(path).read_bytes()).hexdigest()

    def write(root, name, value):
        with (root / name).open("x") as stream:
            json.dump(value, stream)

    def read(path):
        return json.loads(Path(path).read_text())

    def data(path, value):
        path.write_text(json.dumps(value))

    config = tmp_path / "config.json"
    data(config, {"shared_lease_path": str(lease)})
    data(lane, {"in_flight": False, "halted": False, "sequence": 1})
    data(c38 / "SCHEDULE.json", {"configuration_path": str(config), "run_root": str(run),
        "code_root": str(tmp_path / "code"), "code_commit": "synthetic-original-C38"})
    data(c38 / "PREFLIGHT.json", {"protected": {
        key: {"path": str(path), "sha256": "0" * 64} for key, path in kr_files.items()
    }})
    data(here / "INSTALL_INTENT.json", {
        "original_C38_schedule_sha256": pin(c38 / "SCHEDULE.json")
    })
    data(here / "FINAL_COMMAND_PIN.json", {"script_sha256": pin(SCRIPT)})
    original_failure = None if full else {"code": "TRANSPORT_TIMEOUT", "stage": "B2"}
    data(run / "terminal.json", {
        "status": "RENDER_VERIFIED_NO_SEND" if full else "FAILED",
        "messages": [],
        "first_failure": original_failure,
    })
    observed = dict(active=False, terminal_exists=True, source_accepted=True,
        model_plan_accepted=True, financial_HTTP=0, model_calls=29,
        model_acceptances=29 if full else 28, messages=15 if full else 0,
        first_failure=original_failure)
    calls = []

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            value = cls(2026, 11, 24, 12, 45, tzinfo=KST)
            return value.astimezone(tz) if tz else value.replace(tzinfo=None)

    def mapped_path(value):
        return {
            "/private/tmp": private_tmp,
            "/Users/sskim/Library/Mobile Documents/com~apple~CloudDocs/Codex Results": delivery,
            "/Users/sskim/Library/Application Support/ThesisMonitor/KiwoomGlobalLane/state.json": lane,
        }.get(str(value), Path(value))

    def verify(out, schedule, observation):
        calls.append(("verify",))
        if receipt_error:
            raise ValueError("ORIGINAL_RECEIPT_FAILURE")
        return full

    def clean(out, schedule):
        calls.append(("clean",))
        if mutate_kr:
            kr_files["kr_config"].write_text("changed during closeout")
        if cleanup_error:
            raise ValueError("SECONDARY_CLEANUP_FAILURE")

    def command(*args):
        assert args == ("ps", "-axo", "pid=,args=")
        calls.append(args)
        return ""

    def fake_subprocess(args, **kwargs):
        # Any enable/bootstrap, including an accidental reintroduced activation,
        # fails the test. Only the original self-disable is allowed as a fake.
        assert args == ["launchctl", "disable", "gui/501/" + POSTRUN_LABEL]
        assert REGULAR_LABEL not in " ".join(args)
        calls.append(tuple(args))

    tree = ast.parse(SCRIPT.read_text())
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
        and node.name in {"main", "load_execution_schedule"}]
    env = dict(datetime=FrozenDateTime, KST=KST,
        DUE=datetime(2026, 11, 24, 12, 45, tzinfo=KST), HERE=here, C38=c38,
        Path=mapped_path, __file__=str(SCRIPT), SELF_LABEL=POSTRUN_LABEL,
        read=read, pin=pin, write=write, observe=lambda *_: observed,
        verify_receipts=verify, clean_one_shot=clean, command=command,
        package=lambda out: calls.append(("package",)),
        fcntl=SimpleNamespace(flock=lambda *_: None, LOCK_EX=2, LOCK_NB=4),
        os=SimpleNamespace(getuid=lambda: 501,
            statvfs=lambda _: SimpleNamespace(f_bavail=10**10, f_frsize=1)),
        subprocess=SimpleNamespace(run=fake_subprocess), json=json, sha256=sha256,
        sys=SimpleNamespace(path=[]),
        re=__import__("re"))
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(SCRIPT), "exec"), env)
    env["main"]()
    out = here / "actual-20261124"
    return read(out / "SUMMARY.json"), calls, out


def test_complete_closeout_preserves_off_and_uses_current_kr_baseline(tmp_path):
    summary, calls, out = run_closeout(tmp_path, full=True)
    assert summary["actual15of15"] is True
    assert summary["status"] == "C38_US_LIVE_15_15_PASS_US_REGULAR_DEFERRED"
    assert summary["US_regular_activated"] is False
    assert summary["postrun_error"] is None
    assert summary["KR_unchanged"] == {"kr_config": True, "kr_plist": True}
    assert summary["KR_hashes_before"] == summary["KR_hashes_after"]
    assert all(value != "0" * 64 for value in summary["KR_hashes_before"].values())
    assert ("clean",) in calls and ("package",) in calls
    pin_update = json.loads(SCRIPT.with_name("PIN_UPDATE.json").read_text())
    assert pin_update["update_only"] == {"script_sha256": sha256(SCRIPT.read_bytes()).hexdigest()}


@pytest.mark.parametrize("receipt_error,cleanup_error", [(False, False), (True, True)])
def test_partial_or_failed_closeout_never_claims_pass_and_preserves_first_failure(
        tmp_path, receipt_error, cleanup_error):
    summary, calls, out = run_closeout(tmp_path, full=False,
        receipt_error=receipt_error, cleanup_error=cleanup_error)
    assert summary["actual15of15"] is False
    assert summary["status"] == "C38_LIVE_PARTIAL_US_OFF"
    assert summary["US_regular_activated"] is False
    assert summary["first_failure"] == {"code": "TRANSPORT_TIMEOUT", "stage": "B2"}
    assert ("package",) in calls
    if receipt_error:
        receipt = json.loads((out / "RECEIPT_VERIFICATION_ERROR.json").read_text())
        assert receipt["code"] == "ORIGINAL_RECEIPT_FAILURE"
        assert summary["postrun_error"]["code"] == "SECONDARY_CLEANUP_FAILURE"


def test_current_kr_mutation_is_reported_even_when_historical_baseline_already_differs(tmp_path):
    summary, _, _ = run_closeout(tmp_path, full=True, mutate_kr=True)
    assert summary["KR_unchanged"] == {"kr_config": False, "kr_plist": True}
    assert summary["KR_hashes_before"]["kr_config"] != summary["KR_hashes_after"]["kr_config"]
