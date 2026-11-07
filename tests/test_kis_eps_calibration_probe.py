from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from scripts import kis_eps_calibration_probe as p
from scripts.kis_estimate_capability_probe import Credentials, ProbeStop


def probe(tmp_path, payload=None, headers=None):
    seen = []

    def handle(request):
        seen.append(request)
        return httpx.Response(200, json=payload or {"rt_cd": "0", "output": []}, headers=headers)

    obj = p.CalibrationProbe(tmp_path, Credentials("key-not-real", "secret-not-real"),
                             httpx.Client(transport=httpx.MockTransport(handle)))
    obj.token = "token-not-real"
    return obj, seen


def test_retired_ratio_stops_before_any_transport_or_pacing(tmp_path):
    obj, seen = probe(tmp_path)
    with patch.object(p.time, "sleep") as sleep:
        with pytest.raises(ProbeStop, match=p.RETIRED):obj.fetch("005930")
        with pytest.raises(ProbeStop, match=p.RETIRED):obj.fetch("000660")
    assert not seen and not sleep.called
    assert obj.counters()["estimate_perform"] == 0
    assert all("token-not-real" not in f.read_text() for f in tmp_path.rglob("*") if f.is_file())


@pytest.mark.parametrize("code,kind", [("005930", "estimate"), ("000660", "estimate"), ("003690", "estimate"), ("999999", "ratio")])
def test_disallowed_requests_never_transmitted(tmp_path, code, kind):
    obj, seen = probe(tmp_path)
    with pytest.raises(ProbeStop):
        obj.fetch(code, kind)
    assert not seen


def test_retired_ratio_continuation_cannot_transmit(tmp_path):
    obj, seen = probe(tmp_path, headers={"tr_cont": "M"})
    with patch.object(p.time, "sleep"), pytest.raises(ProbeStop, match=p.RETIRED):
        obj.fetch("005930")
    with pytest.raises(ProbeStop):
        obj.fetch("005930")
    assert not seen


def test_retired_ratio_rate_limit_transport_never_reached(tmp_path):
    obj, seen = probe(tmp_path, {"rt_cd": "1", "msg_cd": "EGW00201"})
    with patch.object(p.time, "sleep"), pytest.raises(ProbeStop, match=p.RETIRED):
        obj.fetch("005930")
    assert not seen


def test_retired_ratio_stage_b_cannot_enable(tmp_path):
    obj, seen = probe(tmp_path)
    obj.stage_b_allowed = True
    with pytest.raises(ProbeStop, match=p.RETIRED):
        obj.fetch("003690", "ratio")
    assert not seen


def test_retired_run_precedes_directory_secret_auth_and_client(tmp_path):
    target=tmp_path/'must-not-exist'
    with patch.object(Path,'mkdir',side_effect=AssertionError('mkdir reached')), \
         patch.object(p.base,'load_credentials',side_effect=AssertionError('secret reached')), \
         patch.object(p.httpx,'Client',side_effect=AssertionError('client reached')), \
         patch.object(p.CalibrationProbe,'authenticate',side_effect=AssertionError('auth reached')):
        with pytest.raises(ProbeStop,match=p.RETIRED):p.run(target,tmp_path/'not-a-real-env')
    assert not target.exists()


def test_retired_fetch_requires_no_initialized_credentials():
    obj=object.__new__(p.CalibrationProbe)
    with pytest.raises(ProbeStop,match=p.RETIRED):obj.fetch('not-a-real-code','ratio')


def test_retained_parser_and_live_estimate_paths_unchanged():
    from scripts import kis_eps_wire_calibration as offline
    from app.services import kis_estimate_source_contract as current
    assert offline.RATIO_PATH==p.RATIO_PATH and offline.RATIO_TR==p.RATIO_TR
    assert current.base.DATA_PATH=='/uapi/domestic-stock/v1/quotations/estimate-perform'
    assert current.IDENTITY_PATH=='/uapi/domestic-stock/v1/quotations/search-info'
    import ast
    tree=ast.parse(Path(offline.__file__).read_text())
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('get','request')
        and isinstance(n.func.value,ast.Attribute) and n.func.value.attr=='client' for n in ast.walk(tree))


def test_no_runtime_imports():
    for path in Path("app").rglob("*.py"):
        assert "kis_eps_calibration_probe" not in path.read_text()
