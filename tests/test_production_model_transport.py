"""Offline process doubles never execute the signed-in executable."""
import asyncio
from dataclasses import asdict
import json
from pathlib import Path

import pytest

from app.services import production_model_transport as model
from app.services.production_b2_execution import ModelTransportError
from app.services.unified_run_artifacts import durable_bytes, durable_json, sha256_bytes
from tests.test_official_codex_shadow_transport import invocation as installation_fixture


@pytest.fixture
def invocation(tmp_path, monkeypatch):
    return installation_fixture.__wrapped__(tmp_path, monkeypatch)


def payload(stage="B2"):
    context = {"synthetic": True}
    prompt = "Synthetic no-call input."
    if stage != "B2":
        prompt += "\nFROZEN_CONTEXT:\n" + json.dumps(context) + "\n"
    return dict(prompt=prompt, input=context, response_schema={"type": "object"})


class Process:
    pid = 123456789
    returncode = 0

    def __init__(self, receipt=None, raw=b"{}", *, returncode=0):
        self.receipt = receipt or {"status": "PASS"}
        self.raw, self.frame, self.returncode = raw, None, returncode

    async def communicate(self, data):
        self.frame = json.loads(data)
        root = Path(self.frame["directory"])
        files = root / "approved-input"
        assert {p.name for p in files.iterdir()} == {"prompt.txt", "provider-wire-schema.json"}
        assert sha256_bytes((files / "prompt.txt").read_bytes()) == self.frame["prompt_sha256"]
        durable_bytes(root / "raw-output.json", self.raw, exclusive=True)
        durable_json(root / "transport-receipt.json", self.receipt, exclusive=True)
        return b"", b""

    async def wait(self):
        self.reaped = True
        return self.returncode


def transport(invocation, tmp_path, process=None, **kwargs):
    binding = json.loads(json.dumps(asdict(invocation["official_shadow"].binding), default=str))
    calls = []

    async def factory(*args, **options):
        calls.append((args, options))
        assert options["start_new_session"] is True
        assert options["env"]["DATABASE_URL"] == "sqlite://"
        assert options["env"]["UNIFIED_SNAPSHOT_ENABLED"] == "false"
        return process or Process()

    item = model.OfficialProductionModelTransport(binding=binding, runtime_root=tmp_path / "runtime",
        worker_factory=factory, **kwargs)
    item.bind_cycle(market="us", run_id="synthetic-current")
    return item, calls


@pytest.mark.parametrize("stage", ["MARKET", "CORE", "A", "B", "B2"])
def test_exact_stage_bytes_detached_authority_and_raw_receipt(invocation, tmp_path, stage):
    process = Process()
    item, calls = transport(invocation, tmp_path, process)
    value = payload(stage)
    raw = asyncio.run(item.request(value, model="gpt-5.6-sol", effort="xhigh", timeout=600, stage=stage))
    assert raw == b"{}" and len(calls) == item.total == 1
    root = Path(process.frame["directory"])
    assert (root / "approved-input/prompt.txt").read_bytes() == model.render_prompt(value, stage)
    auth = json.loads((root / "production-authorization.json").read_bytes())
    assert auth["purpose"] == "PRODUCTION_MONITORING" and not auth["semantic_retry_allowed"]
    assert json.loads((root / "parent-exit.json").read_bytes())["child_reaped"]


def test_binding_and_secret_failure_before_worker(invocation, tmp_path):
    item, calls = transport(invocation, tmp_path, secrets=("Synthetic no-call",))
    with pytest.raises(ValueError, match="secret_detected"):
        asyncio.run(item.request(payload(), model="gpt-5.6-sol", effort="xhigh", timeout=600))
    assert not calls and item.total == 0
    with pytest.raises(ValueError, match="contract_not_bound"):
        asyncio.run(item.request(payload(), model="gpt-6-astra", effort="xhigh", timeout=600))
    assert not calls


def test_only_bounded_identical_requests_reach_worker(invocation, tmp_path):
    item, calls = transport(invocation, tmp_path)
    for _ in range(3):
        asyncio.run(item.request(payload(), model="gpt-5.6-sol", effort="xhigh", timeout=600))
    with pytest.raises(ValueError, match="budget_exhausted"):
        asyncio.run(item.request(payload(), model="gpt-5.6-sol", effort="xhigh", timeout=600))
    assert len(calls) == 3
    with pytest.raises(ValueError, match="cycle_binding"):
        item.bind_cycle(market="us", run_id="synthetic-current")


def test_transport_failure_preserves_raw_and_does_not_retry_itself(invocation, tmp_path):
    process = Process({"status": "FAIL", "error_code": "PROCESS_NONZERO"}, b"partial", returncode=1)
    item, calls = transport(invocation, tmp_path, process)
    with pytest.raises(ModelTransportError):
        asyncio.run(item.request(payload(), model="gpt-5.6-sol", effort="xhigh", timeout=600))
    assert len(calls) == 1
    assert (Path(process.frame["directory"]) / "raw-output.json").read_bytes() == b"partial"


def test_cancel_reaps_owned_group(invocation, tmp_path, monkeypatch):
    class Waiting(Process):
        returncode = None

        async def communicate(self, data):
            self.returncode = None
            raise asyncio.CancelledError()

    process = Waiting()
    item, calls = transport(invocation, tmp_path, process)
    killed = []
    monkeypatch.setattr(model.os, "killpg", lambda pid, sig: killed.append((pid, sig)))
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(item.request(payload(), model="gpt-5.6-sol", effort="xhigh", timeout=600))
    assert killed == [(process.pid, model.signal.SIGKILL)] and process.reaped
    assert len(calls) == 1


def test_changed_embedded_context_not_repaired(invocation, tmp_path):
    item, calls = transport(invocation, tmp_path)
    value = payload("CORE")
    value["input"]["changed"] = True
    with pytest.raises(ValueError, match="context_mismatch"):
        asyncio.run(item.request(value, model="gpt-5.6-sol", effort="xhigh", timeout=600, stage="CORE"))
    assert not calls
