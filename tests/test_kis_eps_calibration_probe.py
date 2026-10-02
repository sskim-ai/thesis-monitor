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


def test_ratio_contract_and_pacing(tmp_path):
    obj, seen = probe(tmp_path)
    with patch.object(p.time, "sleep") as sleep:
        obj.fetch("005930")
        obj.fetch("000660")
    assert len(seen) == 2
    assert str(seen[0].url.path) == p.RATIO_PATH
    assert dict(seen[0].url.params) == {"FID_DIV_CLS_CODE": "0", "fid_cond_mrkt_div_code": "J", "fid_input_iscd": "005930"}
    assert seen[0].headers["tr_id"] == p.RATIO_TR
    assert all(call.args[0] > 1 for call in sleep.call_args_list)
    assert obj.counters()["estimate_perform"] == 0
    assert all("token-not-real" not in f.read_text() for f in tmp_path.rglob("*") if f.is_file())


@pytest.mark.parametrize("code,kind", [("005930", "estimate"), ("000660", "estimate"), ("003690", "estimate"), ("999999", "ratio")])
def test_disallowed_requests_never_transmitted(tmp_path, code, kind):
    obj, seen = probe(tmp_path)
    with pytest.raises(ProbeStop):
        obj.fetch(code, kind)
    assert not seen


def test_duplicate_and_continuation_not_retried(tmp_path):
    obj, seen = probe(tmp_path, headers={"tr_cont": "M"})
    with patch.object(p.time, "sleep"), pytest.raises(ProbeStop, match="CONTINUATION"):
        obj.fetch("005930")
    with pytest.raises(ProbeStop):
        obj.fetch("005930")
    assert len(seen) == 1


def test_rate_limit_terminal_no_retry(tmp_path):
    obj, seen = probe(tmp_path, {"rt_cd": "1", "msg_cd": "EGW00201"})
    with patch.object(p.time, "sleep"), pytest.raises(ProbeStop, match="RATE_LIMIT"):
        obj.fetch("005930")
    assert len(seen) == 1


def test_stage_b_ratio_requires_actual_partial(tmp_path):
    obj, seen = probe(tmp_path)
    obj.stage_b_allowed = True
    with pytest.raises(ProbeStop, match="PARTIAL_LAYOUT"):
        obj.fetch("003690", "ratio")
    assert not seen


def test_no_runtime_imports():
    for path in Path("app").rglob("*.py"):
        assert "kis_eps_calibration_probe" not in path.read_text()
