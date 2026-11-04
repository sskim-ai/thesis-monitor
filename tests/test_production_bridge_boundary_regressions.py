"""Regression probes for newly found adapter gaps; never live transport."""
import asyncio
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services.production_b2_execution import ModelTransportError
from app.services.production_source_configuration import ProtocolFile
from app.services.unified_run_artifacts import sha256_bytes
from tests import test_production_model_transport as boundary


@pytest.fixture
def invocation(tmp_path, monkeypatch):
    return boundary.invocation.__wrapped__(tmp_path, monkeypatch)


def test_nonzero_worker_cannot_claim_pass(invocation, tmp_path):
    process = boundary.Process({"status": "PASS"}, b"{}", returncode=9)
    transport, calls = boundary.transport(invocation, tmp_path, process)
    with pytest.raises(ModelTransportError, match="WORKER_NONZERO"):
        asyncio.run(transport.request(boundary.payload(), model="gpt-5.6-sol", effort="xhigh", timeout=600))
    assert len(calls) == 1
    assert (Path(process.frame["directory"]) / "raw-output.json").read_bytes() == b"{}"


def test_protocol_parent_symlink_rejected(tmp_path):
    actual = tmp_path / "deployed"
    actual.mkdir()
    path = actual / "public.json"
    path.write_bytes(b"{}")
    alias = tmp_path / "alias"
    alias.symlink_to(actual, target_is_directory=True)
    item = ProtocolFile(path=str(alias / path.name), sha256=sha256_bytes(path.read_bytes()), purpose="PUBLIC_PROTOCOL")
    with pytest.raises(ValueError, match="not_deployed"):
        item.read()


def test_kr_current_view_reaches_renderer_input(monkeypatch):
    from app.services import production_source_projection as projection
    from app.services import kr_current_valuation_projection as kr
    from app.services.kr_forward_valuation_context import calibration_context
    from tests.test_kr_forward_valuation_integration import view
    current = view()
    ticker = current.native.ticker
    typed = current.model_dump(mode="json")
    expected = {ticker: calibration_context(current)}
    monkeypatch.setattr(projection.ProductionRequestPlan, "model_validate", lambda _: SimpleNamespace(market="kr", generation_id="fictional"))
    monkeypatch.setattr(kr, "source_only_projection", lambda *a, **kw: {
        "expected_valuation_contexts": deepcopy(expected),
        "stocks": {ticker: {"kr_fy1_evidence": {k: v for k, v in typed.items() if k != "native"}}}})
    monkeypatch.setattr(projection, "prepare_monitoring_source", lambda **kw: {"valuation_contexts": kw["valuation_contexts"]})
    result = projection.monitoring_source(
        args={"stock_inputs": {ticker: {"fresh_financial_binding": {"technical_inputs": {"local_seed": {}}}}}},
        whole={"packets": {"kr": {"stocks": {ticker: {"valuation_view": typed["native"]}}}}},
        frozen={"plan": {}}, coverage={"coverage": {}, "census": {}},
        kis_plan={"as_of": typed["as_of"], "receipt_sha256": typed["fresh_plan_sha256"]},
        kis_view={"rows": [typed["kis"]]})
    assert set(result["forward_views"]) == {ticker}
    assert calibration_context(result["forward_views"][ticker]) == result["valuation_contexts"][ticker]


def test_unresponsive_native_child_is_killed_and_reaped(monkeypatch):
    from app.services import sealed_native_bridge as bridge
    events = []
    class Pipe:
        def write(self, value):
            events.append("close_requested")
        async def drain(self):
            pass
    class Child:
        returncode = None
        stdin = Pipe()
        async def communicate(self):
            if self.returncode is None:
                raise TimeoutError()
            return b"", b""
        def terminate(self):
            events.append("terminate")
        def kill(self):
            events.append("kill")
            self.returncode = -9
        async def wait(self):
            events.append("reaped")
            return self.returncode
    owned = object.__new__(bridge.SealedNativeBridge)
    owned.process = Child()
    owned.exit_receipt = None
    asyncio.run(owned.shutdown())
    assert events == ["close_requested", "terminate", "kill", "reaped"]
    assert owned.exit_receipt["returncode"] == -9
