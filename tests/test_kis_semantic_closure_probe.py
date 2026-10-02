import json

import httpx
import pytest

from scripts import kis_semantic_closure_probe as p
from scripts.kis_estimate_capability_probe import Credentials, ProbeStop


def probe(tmp_path, handler):
    obj = p.ClosureProbe(tmp_path, Credentials("fictional-app", "fictional-secret"),
                         httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False))
    obj.disk_guard = lambda: None
    obj.token = "fictional-token"
    obj.secrets.append(obj.token.encode())
    return obj


def test_primary_params_and_conditional_secondary(tmp_path):
    calls = []

    def handle(request):
        calls.append(request)
        assert dict(request.url.params) == {"PDNO": "005930", "PRDT_TYPE_CD": "300"}
        return httpx.Response(200, json={"rt_cd": "0", "output": {"pdno": "005930"}})

    obj = probe(tmp_path, handle)
    obj.identity("005930", "search-info")
    obj.identity("005930", "search-stock-info")
    assert len(calls) == 2
    assert obj.counters()["identity"] == 2
    assert obj.counters()["estimate_perform"] == 0
    with pytest.raises(ProbeStop, match="IDENTITY_REQUEST_SCOPE_GAP"):
        obj.identity("005930", "search-info")


def test_secondary_not_called_before_primary_or_when_complete(tmp_path):
    row = {"pdno": "005930", "shtn_pdno": "A005930", "prdt_type_cd": "300",
           "mket_id_cd": "STK", "scty_grp_id_cd": "ST", "prdt_name": "Fictional"}
    obj = probe(tmp_path, lambda request: httpx.Response(200, json={"rt_cd": "0", "output": row}))
    with pytest.raises(ProbeStop, match="SECONDARY_NOT_REQUIRED"):
        obj.identity("005930", "search-stock-info")
    obj.identity("005930", "search-info")
    with pytest.raises(ProbeStop, match="SECONDARY_NOT_REQUIRED"):
        obj.identity("005930", "search-stock-info")
    assert obj.counters()["identity"] == 1


@pytest.mark.parametrize("code", ["005935", "003690", "A005930", "999999"])
def test_identity_scope(tmp_path, code):
    obj = probe(tmp_path, lambda request: pytest.fail("network forbidden"))
    with pytest.raises(ProbeStop, match="IDENTITY_REQUEST_SCOPE_GAP"):
        obj.identity(code, "search-info")


@pytest.mark.parametrize("code", ["000660", "005930", "003690"])
def test_estimate_refresh_or_unadmitted_b_rejected(tmp_path, code):
    obj = probe(tmp_path, lambda request: pytest.fail("network forbidden"))
    with pytest.raises(ProbeStop, match="STAGE_B_NOT_ADMITTED"):
        obj.fetch(code)
    assert obj.data_count == 0


@pytest.mark.parametrize("status", [302, 401, 500])
def test_no_redirect_or_retry(tmp_path, status):
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(status, json={"rt_cd": "1"}, headers={"location": "https://example.org"})

    obj = probe(tmp_path, handle)
    with pytest.raises(ProbeStop, match="IDENTITY_SOURCE_FAILURE"):
        obj.identity("000660", "search-info")
    assert len(calls) == 1


def test_secret_never_persisted(tmp_path):
    obj = probe(tmp_path, lambda request: httpx.Response(200,
        json={"rt_cd": "0", "output": {"value": "fictional-token"}}))
    with pytest.raises(ProbeStop, match="SECRET_EXPOSURE_GAP"):
        obj.identity("000660", "search-info")
    assert not list(tmp_path.rglob("*.body"))


def test_admitted_b_single_page_preserves_raw_and_no_a_refresh(tmp_path):
    payload = {"rt_cd": "0", "output3": [{"data1": "-100.00"}], "output4": [{"dt": "2027.03E"}]}
    obj = probe(tmp_path, lambda request: httpx.Response(200, json=payload))
    obj.stage_b_admitted = True
    obj.fetch("003690")
    assert json.loads((tmp_path / "stage-b/003690.body").read_bytes()) == payload
    with pytest.raises(ProbeStop, match="STAGE_B_BUDGET_GAP"):
        obj.fetch("003690")
    with pytest.raises(ProbeStop, match="STAGE_B_NOT_ADMITTED"):
        obj.fetch("005930")


def test_unexpected_continuation_never_followed(tmp_path):
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(200, json={"rt_cd": "0"}, headers={"tr_cont": "M"})

    obj = probe(tmp_path, handle)
    obj.stage_b_admitted = True
    with pytest.raises(ProbeStop, match="ESTIMATE_CONTINUATION_POLICY_GAP"):
        obj.fetch("003690")
    assert len(calls) == 1
