import json

import httpx
import pytest

from scripts import kis_estimate_capability_probe as k


def test_credentials_read_only_commented_alias(tmp_path):
    path = tmp_path / "env"
    raw = '# KIS_APP_KEY="fictional-app"\n# KIS_SECRET_APP_KEY="fictional-secret"\n'
    path.write_text(raw)
    credentials = k.load_credentials(path)
    assert credentials.app_key == "fictional-app"
    assert credentials.app_secret == "fictional-secret"
    assert "fictional" not in repr(credentials)
    assert path.read_text() == raw


@pytest.mark.parametrize("raw", ["", "KIS_APP_KEY=x", 'KIS_APP_KEY="unterminated',
    "KIS_APP_KEY=a\nKIS_APP_KEY=b\nKIS_APP_SECRET=s",
    "KIS_APP_KEY=a\nKIS_APP_SECRET=s\nKIS_SECRET_APP_KEY=t"])
def test_credentials_fail_closed_without_values_in_error(tmp_path, raw):
    path = tmp_path / "env"
    path.write_text(raw)
    with pytest.raises(k.ProbeStop, match="^CREDENTIAL_GAP$"):
        k.load_credentials(path)


def make_probe(tmp_path, handler):
    client = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False)
    p = k.Probe(tmp_path, k.Credentials("fictional-app", "fictional-secret"), client)
    p.disk_guard = lambda: None
    return p


def response(payload=None, headers=None, status=200):
    return httpx.Response(status, json=payload or {"rt_cd": "0", "output1": []}, headers=headers)


def test_single_auth_redacted_receipt_and_memory_token(tmp_path):
    requests = []

    def handler(request):
        requests.append(request)
        assert request.url.path == k.AUTH_PATH
        return response({"access_token": "fictional-token", "token_type": "Bearer"})

    p = make_probe(tmp_path, handler)
    p.authenticate()
    assert p.token == "fictional-token"
    with pytest.raises(k.ProbeStop, match="AUTH_BUDGET_EXCEEDED"):
        p.authenticate()
    assert len(requests) == 1
    assert not any(b"fictional-" in f.read_bytes() for f in tmp_path.iterdir())


@pytest.mark.parametrize("status", [302, 401, 403, 500])
def test_auth_no_redirect_retry_or_error_body(tmp_path, status):
    calls = []

    def handler(request):
        calls.append(request)
        return response({"error": "fictional-secret"}, {"location": "https://example.org"}, status)

    p = make_probe(tmp_path, handler)
    with pytest.raises(k.ProbeStop, match="AUTH_FAILURE"):
        p.authenticate()
    assert len(calls) == 1
    assert not any(b"fictional-secret" in f.read_bytes() for f in tmp_path.iterdir())


def test_all_four_groups_preserve_exact_format_and_order(tmp_path):
    payload = {"rt_cd": "0", "msg_cd": "OK", "msg1": "ok",
               "output1": {"sht_cd": "000660"},
               "output2": [{"data1": "-1.000", "data2": ""}, {"data1": "0.00", "data2": None}],
               "output3": [{"eps": "1,234.50", "per": "-2.30"}],
               "output4": [{"dt": "2026/12(E)"}]}

    def handler(request):
        assert dict(request.url.params) == {"SHT_CD": "000660"}
        assert request.headers["tr_id"] == k.TR_ID
        return response(payload)

    p = make_probe(tmp_path, handler)
    p.token = "fictional-token"
    p.fetch("000660")
    assert json.loads((tmp_path / "data/000660-1.body").read_bytes()) == payload
    inventory = json.loads((tmp_path / "data/000660-1-schema.json").read_bytes())
    assert set(inventory) == set(k.GROUPS)
    assert inventory["output2"]["fields"]["data1"]["values_in_row_order"][0]["raw"] == "-1.000"
    assert all(group["semantic_assignment"] == "NOT_INFERRED" for group in inventory.values())
    with pytest.raises(k.ProbeStop, match="REQUEST_SCOPE_GAP"):
        p.fetch("000660")


@pytest.mark.parametrize("header", ["M", "F"])
def test_continuation_maximum_one_then_typed_incomplete(tmp_path, header):
    continuations = []

    def handler(request):
        continuations.append(request.headers["tr_cont"])
        return response(headers={"tr_cont": header})

    p = make_probe(tmp_path, handler)
    p.token = "fictional-token"
    p.fetch("005930")
    assert continuations == ["", "N"]
    assert p.results["005930"]["state"] == "BOUNDED_CONTINUATION_INCOMPLETE"
    assert p.counters()["continuations"] == 1


@pytest.mark.parametrize("code", ["005935", "AAPL", "00593", "999999"])
def test_disallowed_security_never_calls(tmp_path, code):
    def handler(request):
        pytest.fail("must not call")

    p = make_probe(tmp_path, handler)
    p.token = "fictional-token"
    with pytest.raises(k.ProbeStop, match="REQUEST_SCOPE_GAP"):
        p.fetch(code)
    assert p.data_count == 0


def test_return_error_preserved_without_semantic_retry(tmp_path):
    p = make_probe(tmp_path, lambda request: response({"rt_cd": "1", "msg1": "no rows"}))
    p.token = "fictional-token"
    p.fetch("000660")
    assert p.results["000660"]["state"] == "KIS_RETURN_ERROR"
    assert p.data_count == 1


@pytest.mark.parametrize("payload", [
    {"rt_cd": "0", "output1": {"secret": "unfamiliar-secret"}},
    {"rt_cd": "0", "output1": {"message": "fictional-secret"}},
    {"rt_cd": "0", "output1": {"message": "Bearer unknown-token"}},
])
def test_secret_response_never_persisted(tmp_path, payload):
    p = make_probe(tmp_path, lambda request: response(payload))
    p.token = "fictional-token"
    with pytest.raises(k.ProbeStop, match="SECRET_EXPOSURE_GAP"):
        p.fetch("000660")
    assert not list(tmp_path.rglob("*.body"))
    assert not list(tmp_path.rglob("*-receipt.json"))


def test_transport_error_exception_is_not_persisted(tmp_path):
    def handler(request):
        raise httpx.ConnectError("fictional-secret", request=request)

    p = make_probe(tmp_path, handler)
    p.token = "fictional-token"
    with pytest.raises(k.ProbeStop, match="^TRANSPORT_FAILURE$"):
        p.fetch("000660")
    assert p.data_count == 1
    assert not any(b"fictional-secret" in f.read_bytes() for f in tmp_path.rglob("*.json"))


def test_redirect_not_followed(tmp_path):
    calls = []

    def handler(request):
        calls.append(request)
        return response(headers={"location": "https://example.org"}, status=302)

    p = make_probe(tmp_path, handler)
    p.token = "fictional-token"
    with pytest.raises(k.ProbeStop, match="TRANSPORT_FAILURE"):
        p.fetch("000660")
    assert len(calls) == 1


def test_raw_unlabeled_future_or_generic_data_fields_not_promoted():
    inventory = k.schema_inventory({"output2": [{"data1": "100"}],
                                    "output4": [{"dt": "2030"}]})
    assert inventory["output4"]["semantic_assignment"] == "NOT_INFERRED"


def test_empty_success_is_complete_not_coverage_failure(tmp_path):
    p = make_probe(tmp_path, lambda request: response())
    p.token = "fictional-token"
    p.fetch("000660")
    assert p.results["000660"]["state"] == "COMPLETE"
    assert p.results["000660"]["pages"][0]["payload"]["output1"] == []
