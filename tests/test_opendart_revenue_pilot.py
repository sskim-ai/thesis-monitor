"""Synthetic protocol tests only; never official issuer evidence or Core grants."""

from copy import deepcopy
from datetime import date, datetime, timezone
from email.message import Message
import io
import json
import zipfile

import pytest

from scripts import opendart_revenue_pilot as p


def raw(value):
    return json.dumps(value, ensure_ascii=False).encode()


def company():
    return dict(corp_code="00123456", stock_code="005930", corp_name="\uc0bc\uc131\uc804\uc790")


def listing():
    return dict(
        status="000",
        total_page=1,
        total_count=1,
        list=[
            dict(
                **company(),
                rcept_no="20260814000001",
                rcept_dt="20260814",
                report_nm="\ubc18\uae30\ubcf4\uace0\uc11c (2026.06)",
            )
        ],
    )


def filing():
    return p.select_filing(raw(listing()), company(), date(2026, 10, 16))


def financial():
    return dict(
        status="000",
        list=[
            dict(
                corp_code="00123456",
                rcept_no="20260814000001",
                bsns_year="2026",
                reprt_code="11012",
                sj_div="CIS",
                account_id="ifrs-full_Revenue",
                account_nm="synthetic revenue",
                account_detail="-",
                currency="KRW",
                ord="1",
                thstrm_nm="synthetic current",
                thstrm_amount="9,007,199,254,740,993.125",
                thstrm_add_amount="999999999999999999",
                frmtrm_amount="80",
            )
        ],
    )


def test_lexical_occurrence_and_decimal_are_not_authority():
    data = raw(financial())
    row = p.parse_revenue(data, company(), filing(), "TEST_ONLY")
    assert row["parsed_decimal"] == "9007199254740993.125"
    assert json.loads(data[row["row_byte_start"] : row["row_byte_end"]]) == financial()["list"][0]
    assert row["row_sha256"] == p.digest(data[row["row_byte_start"] : row["row_byte_end"]])
    assert row["canonical_value"] is None and row["unit_scale"] is None
    assert row["prior_comparison"] == "NOT_ADMITTED"
    assert row["current_period_start"] is None
    assert row["amount_semantics"] == "quarter_3_month"
    assert row["core_permission"] == "NOT_ISSUED"


@pytest.mark.parametrize(
    "key,value",
    [
        ("corp_code", "00999999"),
        ("rcept_no", "20260814000002"),
        ("bsns_year", "2025"),
        ("reprt_code", "11014"),
        ("fs_div", "OFS"),
        ("sj_div", "BS"),
        ("account_id", "earnings_comparison"),
        ("account_detail", "segment"),
        ("currency", "USD"),
        ("currency", None),
        ("thstrm_amount", "NaN"),
        ("thstrm_amount", "1e1000"),
        ("thstrm_amount", "1,00"),
        ("thstrm_amount", "9" * 49),
        ("thstrm_amount", 100),
        ("thstrm_amount", "-1"),
        ("thstrm_nm", ""),
        ("ord", ""),
    ],
)
def test_invalid_financial_row_fails(key, value):
    value_raw = financial()
    value_raw["list"][0][key] = value
    with pytest.raises(p.PilotError):
        p.parse_revenue(raw(value_raw), company(), filing(), "TEST_ONLY")


def test_duplicate_owner_and_fuzzy_name_fail():
    payload = financial()
    payload["list"].append(deepcopy(payload["list"][0]))
    with pytest.raises(p.PilotError, match="AMBIGUOUS"):
        p.parse_revenue(raw(payload), company(), filing(), "TEST_ONLY")
    payload["list"] = payload["list"][:1]
    payload["list"][0]["account_id"] = "custom_Revenue"
    with pytest.raises(p.PilotError, match="MISSING"):
        p.parse_revenue(raw(payload), company(), filing(), "TEST_ONLY")


@pytest.mark.parametrize("code", ["013", "020", "010", "011", "012", "800", "999", None])
def test_provider_failure_is_not_zero(code):
    with pytest.raises(p.PilotError, match="OPENDART_STATUS"):
        p.response_json(raw(dict(status=code, message="not persisted", list=[])))


@pytest.mark.parametrize(
    "mutation", ["future", "wrong_stock", "wrong_corp", "correction", "duplicate", "pagination"]
)
def test_filing_disposition_is_fail_closed(mutation):
    data = listing()
    if mutation == "future":
        data["list"][0]["rcept_dt"] = "20270101"
    elif mutation == "wrong_stock":
        data["list"][0]["stock_code"] = "000660"
    elif mutation == "wrong_corp":
        data["list"][0]["corp_code"] = "00999999"
    elif mutation == "correction":
        data["list"][0]["report_nm"] = "[\uae30\uc7ac\uc815\uc815]" + data["list"][0]["report_nm"]
    elif mutation == "duplicate":
        data["list"].append(deepcopy(data["list"][0]))
        data["total_count"] = 2
    else:
        data["total_page"] = 2
    with pytest.raises(p.PilotError):
        p.select_filing(raw(data), company(), date(2026, 10, 16))


def corp_zip(xml):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("CORPCODE.xml", xml)
    return stream.getvalue()


def test_identity_mapping_not_hardcoded_corp_code():
    xml = "<result><list><corp_code>00123456</corp_code><corp_name>\uc0bc\uc131\uc804\uc790</corp_name><stock_code>005930</stock_code></list></result>"
    mapped = p.resolve_company(corp_zip(xml))
    assert mapped["corp_code"] == "00123456"
    assert mapped["status"] == "PARSED_NOT_INDEPENDENTLY_QUALIFIED"
    for replacement in (
        xml.replace("005930", "000660"),
        xml.replace("\uc0bc\uc131\uc804\uc790", "other"),
        xml.replace("</result>", xml[8:-9] + "</result>"),
        "<!DOCTYPE x>" + xml,
    ):
        with pytest.raises(p.PilotError):
            p.resolve_company(corp_zip(replacement))


@pytest.mark.parametrize(
    "attack",
    [
        "synthetic",
        "rehashed_raw",
        "wrong_generation",
        "fake_signer",
        "shadow_grant",
        "postseal_insert",
        "revoked",
        "expired",
        "fake_document_span",
        "wrong_purpose",
        "earnings_comparison",
        "duplicate_owner",
    ],
)
def test_acquisition_only_boundary_never_issues_native_grant(attack):
    row = p.parse_revenue(raw(financial()), company(), filing(), "TEST_ONLY")
    row.update(attack=attack, source_status="VERIFIED", core_permission="ALLOWED")
    with pytest.raises(p.PilotError, match="NATIVE_CONSUMER_AUTHORITY_NOT_ISSUED"):
        p.deny_native_use(
            row, signer="self-issued", consumer="core_current_fact", signature=p.digest(raw(row))
        )


class Response:
    status = 200

    def __init__(self, body):
        self.body = io.BytesIO(body)
        self.headers = Message()

    def getheader(self, _key, default):
        if getattr(self, "endpoint", "").endswith(".json"):
            return "application/json"
        if self.body.getvalue().startswith(b"<"):
            return "application/xml"
        return "application/zip"

    def read1(self, size):
        return self.body.read(size)


def install_transport(monkeypatch, bodies, failure=None):
    calls = []

    class Connection:
        sock = None

        def set_debuglevel(self, level):
            assert level == 0

        def __init__(self, host, **kwargs):
            assert host == p.HOST and kwargs["context"].verify_mode == p.ssl.CERT_REQUIRED
            self.body = bodies.pop(0) if bodies else b""

        def request(self, method, path, headers):
            calls.append((method, path, dict(headers)))
            self.endpoint = path.split("?")[0]
            if failure:
                raise failure("secret-bearing transport text must never escape")

        def getresponse(self):
            response = Response(self.body)
            response.endpoint = self.endpoint
            if not response.headers.get_all("Content-Type"):
                response.headers["Content-Type"] = response.getheader("Content-Type", "")
            return response

        def close(self):
            pass

    monkeypatch.setattr(p.http.client, "HTTPSConnection", Connection)

    def inline_exchange(endpoint, params, key, timeout, *, frozen_request=None):
        results = []

        class Pipe:
            def send(self, value):
                results.append(value)

            def close(self):
                pass

        with monkeypatch.context() as local:
            local.setattr(p.os, "dup2", lambda *args: None)
            p._transport_worker(Pipe(), endpoint, params, key, timeout, frozen_request)
        return results[0]

    monkeypatch.setattr(p, "bounded_exchange", inline_exchange)
    return calls


def test_no_key_no_network_no_output_directory(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("OPENDART_API_KEY", raising=False)
    monkeypatch.setattr(
        p.os.sys, "argv", ["pilot", "--acquire", "--output", str(tmp_path / "absent")]
    )
    calls = install_transport(monkeypatch, [])
    assert p.main() == 2 and calls == [] and not (tmp_path / "absent").exists()
    assert json.loads(capsys.readouterr().out)["status"] == "R15_OPENDART_AUTH_KEY_UNAVAILABLE"


def test_transport_redaction_and_rate_limit_stop(tmp_path, monkeypatch):
    calls = install_transport(monkeypatch, [b"<result><status>020</status></result>"])
    collector = p.Collector("test" * 10, tmp_path / "capture", datetime.now(timezone.utc))
    with pytest.raises(p.PilotError, match="020"):
        collector.get("corpCode.xml", {})
    # A .xml error is not a ZIP and still stops without retry.
    assert len(calls) == 1


def test_json_provider_error_does_not_retry(tmp_path, monkeypatch):
    calls = install_transport(monkeypatch, [raw(dict(status="020"))])
    c = p.Collector("test" * 10, tmp_path / "capture", datetime.now(timezone.utc))
    c.corp_code = company()["corp_code"]
    c.financial_plan = ("2026", "11012")
    params = dict(corp_code=c.corp_code, bsns_year="2026", reprt_code="11012", fs_div="CFS")
    with pytest.raises(p.PilotError, match="020"):
        c.get("fnlttSinglAcntAll.json", params)
    with pytest.raises(p.PilotError, match="BUDGET_OR_STOP"):
        c.get("fnlttSinglAcntAll.json", params)
    assert len(calls) == 1
    receipt = (c.root / "01-request.json").read_text()
    assert "test" * 10 not in receipt and "crtfc_key" not in receipt


def test_transport_error_retry_bounded_and_sanitized(tmp_path, monkeypatch):
    calls = install_transport(monkeypatch, [], TimeoutError)
    c = p.Collector("test" * 10, tmp_path / "capture", datetime.now(timezone.utc))
    with pytest.raises(p.PilotError, match="TRANSIENT_TRANSPORT_FAILURE"):
        c.get("corpCode.xml", {})
    assert len(calls) == 3 and c.retries == 2 and c.halted
    for path in c.root.iterdir():
        assert "secret-bearing" not in path.read_text() and "test" * 10 not in path.read_text()


@pytest.mark.parametrize("attack", ["host", "key_param", "issuer", "receipt", "budget", "elapsed"])
def test_transport_scope_denies_before_connection(tmp_path, monkeypatch, attack):
    calls = install_transport(monkeypatch, [])
    c = p.Collector("test" * 10, tmp_path / "capture", datetime.now(timezone.utc))
    endpoint, params = "corpCode.xml", {}
    if attack == "host":
        endpoint = "https://other.example/api/corpCode.xml"
    elif attack == "key_param":
        params = {"crtfc_key": "caller"}
    elif attack == "issuer":
        endpoint, params = (
            "fnlttSinglAcntAll.json",
            dict(corp_code="00999999", bsns_year="2026", reprt_code="11012", fs_div="CFS"),
        )
    elif attack == "receipt":
        endpoint, params = "document.xml", dict(rcept_no="20260101000001")
    elif attack == "budget":
        c.count = 12
    else:
        c.started -= 301
    with pytest.raises(p.PilotError):
        c.get(endpoint, params)
    assert not calls


def test_secret_reflection_not_saved(tmp_path, monkeypatch):
    install_transport(monkeypatch, [("test" * 10).encode()])
    c = p.Collector("test" * 10, tmp_path / "capture", datetime.now(timezone.utc))
    with pytest.raises(p.PilotError, match="SECRET_REFLECTION_DENIED"):
        c.get("corpCode.xml", {})
    assert not list(c.root.glob("*.raw"))


def test_duplicate_json_fields_rejected():
    with pytest.raises(p.PilotError):
        p.response_json(b'{"status":"000","status":"013"}')


def test_full_synthetic_acquisition_preserves_unqualified_boundary(tmp_path, monkeypatch):
    xml = "<result><list><corp_code>00123456</corp_code><corp_name>\uc0bc\uc131\uc804\uc790</corp_name><stock_code>005930</stock_code></list></result>"
    calls = install_transport(
        monkeypatch, [corp_zip(xml), raw(listing()), raw(financial()), corp_zip("<document/>")]
    )
    out = tmp_path / "synthetic"
    result = p.acquire(out, "test" * 10, datetime(2026, 10, 16, tzinfo=timezone.utc))
    assert len(calls) == result["provider_gets"] == 4  # Stub transport calls, not provider calls.
    assert result["source_status"] == "CAPTURED_UNQUALIFIED" and result["core_grants"] == 0
    assert result["status"] == "R15_SOURCE_CAPTURED_PRIMARY_SPAN_PENDING"
    assert result["original_document"] == "CAPTURED_NOT_YET_CROSSCHECKED"
    for path in out.glob("*.json"):
        assert "test" * 10 not in path.read_text() and "crtfc_key" not in path.read_text()


def test_redirect_size_and_header_redaction(tmp_path, monkeypatch):
    install_transport(monkeypatch, [b"PKfake"])
    monkeypatch.setattr(Response, "status", 302)
    c = p.Collector("test" * 10, tmp_path / "redirect", datetime.now(timezone.utc))
    with pytest.raises(p.PilotError, match="HTTP_STATUS_REJECTED"):
        c.get("corpCode.xml", {})
    assert not list(c.root.glob("*.raw"))


@pytest.mark.parametrize(
    "kind", ["json_escape", "json_percent_composed", "zip_member", "html_entity", "utf16_entity"]
)
def test_encoded_secret_or_unsafe_xml_never_persisted(tmp_path, monkeypatch, kind):
    key = "test" * 10
    escaped = "".join("\\u%04x" % ord(char) for char in key)
    endpoint = "corpCode.xml"
    params = {}
    if kind in {"json_escape", "json_percent_composed"}:
        if kind == "json_percent_composed":
            percent = "".join("%%%02x" % ord(char) for char in key)
            escaped = "".join("\\u%04x" % ord(char) for char in percent)
        body = ('{"status":"000","message":"' + escaped + '"}').encode()
        endpoint = "fnlttSinglAcntAll.json"
        params = dict(corp_code="00123456", bsns_year="2026", reprt_code="11012", fs_div="CFS")
    elif kind == "zip_member":
        body = corp_zip("<result>" + key + "</result>")
    elif kind == "html_entity":
        body = ("<result>" + "".join("&#%d;" % ord(x) for x in key) + "</result>").encode()
    else:
        body = corp_zip(('<!DOCTYPE x [<!ENTITY x "boom">]><result>&x;</result>').encode("utf-16"))
    install_transport(monkeypatch, [body])
    c = p.Collector(key, tmp_path / "capture", datetime.now(timezone.utc))
    c.corp_code = "00123456"
    c.financial_plan = ("2026", "11012")
    with pytest.raises(p.PilotError):
        c.get(endpoint, params)
    assert not list(c.root.glob("*.raw"))


def test_selected_report_and_search_plan_pinned(tmp_path, monkeypatch):
    calls = install_transport(monkeypatch, [])
    c = p.Collector("test" * 10, tmp_path / "capture", datetime(2026, 10, 16, tzinfo=timezone.utc))
    c.corp_code = "00123456"
    c.financial_plan = ("2026", "11012")
    with pytest.raises(p.PilotError, match="REQUEST_REPORT_PLAN_MISMATCH"):
        c.get(
            "fnlttSinglAcntAll.json",
            dict(corp_code=c.corp_code, bsns_year="2025", reprt_code="11011", fs_div="CFS"),
        )
    with pytest.raises(p.PilotError, match="REQUEST_SEARCH_PLAN_MISMATCH"):
        c.get(
            "list.json",
            dict(
                corp_code=c.corp_code,
                bgn_de="20000101",
                end_de="20261016",
                pblntf_ty="A",
                last_reprt_at="N",
                page_no="1",
                page_count="100",
            ),
        )
    assert calls == []


def test_supervised_process_deadline_no_network(monkeypatch, record_property):
    def stuck_worker(pipe, *_args):
        p.time.sleep(5)

    monkeypatch.setattr(p, "_transport_worker", stuck_worker)
    start = p.time.monotonic()
    result = p.bounded_exchange("corpCode.xml", {}, "test" * 10, 0.05)
    assert p.time.monotonic() - start < 3
    assert result["deadline_expired"] and result["child_exit"] is not None
    assert result["lifecycle"] == "DEADLINE_TERMINATED"
    record_property("transport_lifecycle", json.dumps(result))


def test_partial_ipc_frame_cannot_bypass_deadline(monkeypatch, record_property):
    import struct

    def partial_worker(pipe, *_args):
        p.os.write(pipe.fileno(), struct.pack("!i", 1024) + b"x")
        p.time.sleep(5)

    monkeypatch.setattr(p, "_transport_worker", partial_worker)
    start = p.time.monotonic()
    result = p.bounded_exchange("corpCode.xml", {}, "test" * 10, 0.05)
    assert p.time.monotonic() - start < 3
    assert result["deadline_expired"] and result["reader_terminated"]
    assert result["child_exit"] is not None
    record_property("transport_lifecycle", json.dumps(result))


def test_large_complete_ipc_result_returns_without_network(monkeypatch, record_property):
    def complete_worker(pipe, *_args):
        pipe.send(dict(raw=b"x" * 1_000_000, error=None, transient=False))
        pipe.close()

    monkeypatch.setattr(p, "_transport_worker", complete_worker)
    result = p.bounded_exchange("corpCode.xml", {}, "test" * 10, 2)
    assert len(result.pop("raw")) == 1_000_000
    assert result["child_exit"] == 0 and result["reader_terminated"]
    record_property("transport_lifecycle", json.dumps(result))


@pytest.mark.parametrize("mime,expected", [
    ("application/zip", "RESPONSE_SIZE_LIMIT"),
    ("test" * 10, "RESPONSE_CONTENT_TYPE_DENIED"),
])
def test_size_and_header_redaction(tmp_path, monkeypatch, mime, expected):
    monkeypatch.setattr(Response, "status", 200)
    monkeypatch.setattr(Response, "getheader", lambda *args: mime)
    install_transport(monkeypatch, [b"PKtoo-large"])
    monkeypatch.setattr(p, "MAX_RAW", 4)
    c = p.Collector("test" * 10, tmp_path / "oversize", datetime.now(timezone.utc))
    with pytest.raises(p.PilotError, match=expected):
        c.get("corpCode.xml", {})
    assert "test" * 10 not in (c.root / "01-request.json").read_text()
    assert not list(c.root.glob("*.raw"))


@pytest.mark.parametrize(
    "location,expected",
    [
        ("/api/corpCode.xml", {"same_origin": True, "allowed_path": True}),
        (
            "https://OPENDART.FSS.OR.KR:443/api/corpCode.xml",
            {"same_origin": True, "explicit_port": 443},
        ),
        (
            "http://opendart.fss.or.kr/api/corpCode.xml",
            {"tls_downgrade": True, "same_origin": False},
        ),
        ("https://dart.fss.or.kr/", {"same_origin": False, "hostname": "dart.fss.or.kr"}),
        ("https://elsewhere.invalid/hidden", {"hostname": "UNRECOGNIZED_NOT_LOGGED"}),
        ("/", {"canonical_path": "/", "allowed_path": False}),
        (
            "/api/corpCode.xml?crtfc_key=opaque",
            {"credential_in_redirect": True, "known_key_parameter_present": True},
        ),
        ("/api/corpCode.xml?message=opaque", {"unexpected_parameters_present": True}),
        ("https://user:pass@opendart.fss.or.kr/api/corpCode.xml", {"credential_in_redirect": True}),
        (
            "https://opendart.fss.or.kr:8443/api/corpCode.xml",
            {"same_origin": False, "explicit_port": 8443},
        ),
    ],
)
def test_redirect_classification_never_authorizes_follow(location, expected):
    result = p.redirect_metadata([location], "corpCode.xml", "test" * 10)
    assert all(result[k] == v for k, v in expected.items())
    assert result["followed"] is False and result["credential_replayed"] is False
    assert result["policy"] in {"STOP_REQUIRES_INDEPENDENT_REVIEW", "REFUSE_REDIRECT"}
    assert "opaque" not in json.dumps(result) and "user:pass" not in json.dumps(result)


@pytest.mark.parametrize(
    "locations",
    [
        [],
        ["/", "/index.jsp"],
        [None],
        ["x" * 8193],
        ["https://["],
        ["https://opendart.fss.or.kr:bad/"],
        ["/\nsecret"],
        ["/\\secret"],
    ],
)
def test_unknown_location_stops_without_detail(locations):
    result = p.redirect_metadata(locations, "corpCode.xml", "test" * 10)
    assert result["classification"] == "UNKNOWN_LOCATION"
    assert not result["followed"]
    assert set(result) == {"present", "classification", "followed", "credential_replayed"}


@pytest.mark.parametrize(
    "place", ["query", "path", "host", "userinfo", "fragment", "encoded", "query_name"]
)
def test_redirect_secret_components_never_escape(place):
    key = "SENTINEL0123456789" * 2
    locations = {
        "query": "/api/corpCode.xml?unrecognized=" + key,
        "path": "/" + key,
        "host": "https://" + key + ".invalid/",
        "userinfo": "https://" + key + "@opendart.fss.or.kr/",
        "fragment": "/#" + key,
        "encoded": "/api/corpCode.xml?unrecognized=" + "".join("%%%02x" % ord(c) for c in key),
        "query_name": "/api/corpCode.xml?" + key + "=opaque",
    }
    result = p.redirect_metadata([locations[place]], "corpCode.xml", key)
    assert result["credential_in_redirect"]
    assert key not in json.dumps(result) and "SENTINEL" not in json.dumps(result)
    assert result["policy"] == "REFUSE_REDIRECT"


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_actual_transport_stops_3xx_without_body_or_retry(tmp_path, monkeypatch, status):
    key = "test" * 10
    calls = install_transport(monkeypatch, [b"body must never be read"])
    original_init = Response.__init__

    def with_header(self, body):
        original_init(self, body)
        self.headers["Location"] = "/api/corpCode.xml?crtfc_key=" + key

    monkeypatch.setattr(Response, "__init__", with_header)
    monkeypatch.setattr(Response, "status", status)
    monkeypatch.setattr(Response, "read1", lambda *_: pytest.fail("3xx body read"))
    collector = p.Collector(key, tmp_path / "capture", datetime.now(timezone.utc))
    with pytest.raises(p.PilotError, match="HTTP_STATUS_REJECTED"):
        collector.get("corpCode.xml", {})
    receipt = json.loads((collector.root / "01-request.json").read_text())
    assert len(calls) == 1 and collector.halted and collector.retries == 0
    assert receipt["redirect"]["credential_in_redirect"]
    assert not list(collector.root.glob("*.raw"))
    assert key not in json.dumps(receipt)


@pytest.mark.parametrize("location", ["#section", "", "?"])
def test_relative_redirect_inherits_credential_query_conservatively(location):
    result = p.redirect_metadata([location], "corpCode.xml", "test" * 10)
    assert result["query_present"]
    assert result["known_key_parameter_present"]
    assert result["credential_in_redirect"]
    assert result["policy"] == "REFUSE_REDIRECT"
    assert "test" * 10 not in json.dumps(result)

def json_company():
    return dict(status="000", **{**company(), "corp_code": p.COMPANY_SEED})


def json_bodies():
    search, statement = listing(), financial()
    search["list"][0]["corp_code"] = p.COMPANY_SEED
    statement["list"][0]["corp_code"] = p.COMPANY_SEED
    return [raw(json_company()), raw(search), raw(statement)]


@pytest.mark.parametrize("endpoint", ["company.json", "list.json", "fnlttSinglAcntAll.json"])
def test_r17_exact_provider_json_contract(endpoint):
    contract = p.request_contract(endpoint)
    assert contract["headers"] == {
        "Accept": "application/json", "User-Agent": "ThesisMonitor/1.0",
        "Accept-Encoding": "identity",
    }
    assert contract["provider_header_contract"] == p.sealed_opendart_contract.header_contract()
    assert contract["accepted_content_types"] == ["application/json"]
    assert contract["follow_redirects"] is False and contract["tls_verify"] is True
    assert contract["proxy_environment"] is False
    assert "crtfc_key" not in json.dumps(contract)


@pytest.mark.parametrize("endpoint", ["corpCode.xml", "document.xml"])
def test_r17_zip_accept_not_blind_json_alias(endpoint):
    contract = p.request_contract(endpoint)
    assert "application/zip" in contract["headers"]["Accept"]
    assert "application/json" not in contract["headers"]["Accept"]
    assert contract["headers"]["User-Agent"] == "ThesisMonitor/1.0"
    assert set(contract["accepted_content_types"]) == {
        "application/zip", "application/octet-stream", "application/xml", "text/xml"
    }


def test_r17_json_route_uses_company_before_filing_without_zip(tmp_path, monkeypatch):
    calls = install_transport(monkeypatch, json_bodies())
    result = p.acquire(tmp_path / "capture", "test" * 10,
                       datetime(2026, 10, 16, tzinfo=timezone.utc), route="json")
    assert [call[1].split("?")[0] for call in calls] == [
        "/api/company.json", "/api/list.json", "/api/fnlttSinglAcntAll.json"
    ]
    assert all(call[2] == p.request_contract("company.json")["headers"] for call in calls)
    assert result["provider_gets"] == 3  # Synthetic transport, zero provider calls.
    assert result["request_budget"] == 4 and result["retry_budget"] == 0
    assert result["source_status"] == "CAPTURED_UNQUALIFIED" and result["core_grants"] == 0
    assert result["original_document"] == "SOURCE_ORIGINAL_DOCUMENT_NOT_CROSSCHECKED"
    mapping = json.loads((tmp_path / "capture/company.json").read_text())
    assert mapping["candidate_origin"] == "HISTORICAL_HINT_ONLY"
    assert mapping["status"] == "PARSED_NOT_INDEPENDENTLY_QUALIFIED"
    for path in (tmp_path / "capture").glob("*"):
        assert b"test" * 10 not in path.read_bytes()
    receipts = [json.loads(path.read_text()) for path in (tmp_path / "capture").glob("*-request.json")]
    assert all(row["request_contract_sha256"] == p.contract_digest(row["request_contract"])
               for row in receipts)


@pytest.mark.parametrize("field,value", [
    ("corp_code", "00999999"), ("stock_code", "000001"), ("corp_name", "Different company"),
    ("status", "013"), ("corp_code", None),
])
def test_r17_company_mismatch_stops_before_next_request(tmp_path, monkeypatch, field, value):
    company_payload = json_company()
    company_payload[field] = value
    calls = install_transport(monkeypatch, [raw(company_payload)])
    result = p.acquire(tmp_path / "capture", "test" * 10,
                       datetime(2026, 10, 16, tzinfo=timezone.utc), route="json")
    assert len(calls) == 1 and result["core_grants"] == 0
    assert result["source_status"] == "NOT_CAPTURED"
    assert not (tmp_path / "capture/company.json").exists()
    assert not (tmp_path / "capture/revenue-occurrence.json").exists()


def test_r17_caller_seed_cannot_replace_official_response(tmp_path, monkeypatch):
    calls = install_transport(monkeypatch, [])
    collector = p.Collector("test" * 10, tmp_path / "capture",
                            datetime(2026, 10, 16, tzinfo=timezone.utc), route="json")
    collector.corp_code = p.COMPANY_SEED
    with pytest.raises(p.PilotError, match="OFFICIAL_COMPANY_RESPONSE_REQUIRED"):
        collector.confirm_company(raw(json_company()))
    with pytest.raises(p.PilotError, match="OFFICIAL_COMPANY_RESPONSE_REQUIRED"):
        collector.get("list.json", dict(corp_code=p.COMPANY_SEED, bgn_de="20260101",
            end_de="20261016", pblntf_ty="A", last_reprt_at="N", page_no="1", page_count="100"))
    assert calls == []


@pytest.mark.parametrize("endpoint,params", [
    ("corpCode.xml", {}), ("document.xml", {"rcept_no": "20260814000001"}),
    ("fnlttSinglAcnt.json", {"corp_code": p.COMPANY_SEED, "bsns_year": "2026", "reprt_code": "11012"}),
    ("company.json", {"corp_code": "00999999"}),
])
def test_r17_finite_json_route_rejects_other_routes_before_network(tmp_path, monkeypatch, endpoint, params):
    calls = install_transport(monkeypatch, [])
    collector = p.Collector("test" * 10, tmp_path / "capture",
                            datetime.now(timezone.utc), route="json")
    with pytest.raises(p.PilotError):
        collector.get(endpoint, params)
    assert calls == []


@pytest.mark.parametrize("status", [301, 302, 307, 308])
def test_r17_company_redirect_never_falls_back_to_zip(tmp_path, monkeypatch, status):
    calls = install_transport(monkeypatch, [raw(json_company())])
    monkeypatch.setattr(Response, "status", status)
    original = Response.__init__
    def redirected(self, body):
        original(self, body)
        self.headers["Location"] = "/error1.html"
    monkeypatch.setattr(Response, "__init__", redirected)
    monkeypatch.setattr(Response, "read1", lambda *_: pytest.fail("3xx body must not be read"))
    result = p.acquire(tmp_path / "capture", "test" * 10,
                       datetime.now(timezone.utc), route="json")
    receipt = json.loads((tmp_path / "capture/01-request.json").read_text())
    assert len(calls) == 1 and result["error"] == "HTTP_STATUS_REJECTED"
    assert receipt["redirect"]["canonical_path"] == "/error1.html"
    assert receipt["redirect"]["followed"] is False
    assert not list((tmp_path / "capture").glob("*.raw"))


def test_r17_json_route_has_no_transient_retry(tmp_path, monkeypatch):
    calls = install_transport(monkeypatch, [], TimeoutError)
    result = p.acquire(tmp_path / "capture", "test" * 10,
                       datetime.now(timezone.utc), route="json")
    assert len(calls) == 1 and result["retry_budget"] == 0
    assert result["error"] == "TRANSIENT_TRANSPORT_FAILURE"


@pytest.mark.parametrize("header,value", [("Accept", "text/html"), ("User-Agent", "Browser/1.0")])
def test_r17_header_drift_rejected_before_request(tmp_path, monkeypatch, header, value):
    calls = install_transport(monkeypatch, [])
    collector = p.Collector("test" * 10, tmp_path / "capture",
                            datetime.now(timezone.utc), route="json")
    inherited = p.sealed_opendart_contract.opendart_headers()
    monkeypatch.setattr(p.sealed_opendart_contract, "opendart_headers",
                        lambda: {**inherited, header: value})
    with pytest.raises(p.PilotError, match="PROVIDER_HEADER_CONTRACT_DRIFT"):
        collector.get("company.json", {"corp_code": p.COMPANY_SEED})
    assert calls == [] and collector.halted


def test_r17_worker_rejects_forged_descriptor_before_connect(monkeypatch):
    calls = install_transport(monkeypatch, [])
    descriptor = p.request_contract("company.json")
    descriptor["headers"]["Accept"] = "text/html"
    results = []
    class Pipe:
        def send(self, value): results.append(value)
        def close(self): pass
    p._transport_worker(Pipe(), "company.json", {"corp_code": p.COMPANY_SEED},
                        "test" * 10, 1, descriptor)
    assert results[0]["error"] == "REQUEST_DESCRIPTOR_DRIFT" and calls == []


@pytest.mark.parametrize("content_type", ["text/html", "application/zip", "application/xml"])
def test_r17_json_unexpected_content_type_denied_before_body(tmp_path, monkeypatch, content_type):
    calls = install_transport(monkeypatch, [raw(json_company())])
    monkeypatch.setattr(Response, "getheader", lambda *_: content_type)
    monkeypatch.setattr(Response, "read1", lambda *_: pytest.fail("wrong type must not be consumed"))
    result = p.acquire(tmp_path / "capture", "test" * 10,
                       datetime.now(timezone.utc), route="json")
    assert result["error"] == "RESPONSE_CONTENT_TYPE_DENIED" and len(calls) == 1
    assert not list((tmp_path / "capture").glob("*.raw"))


def test_r17_response_descriptor_mismatch_not_persisted(tmp_path, monkeypatch):
    monkeypatch.setattr(p, "bounded_exchange", lambda *_, **_kwargs: dict(
        raw=raw(json_company()), error=None, transient=False, request_contract_sha256="0" * 64))
    result = p.acquire(tmp_path / "capture", "test" * 10,
                       datetime.now(timezone.utc), route="json")
    assert result["error"] == "RESPONSE_REQUEST_CONTRACT_MISMATCH"
    assert not list((tmp_path / "capture").glob("*.raw"))


def test_r17_public_query_binding_rejects_other_candidate(tmp_path, monkeypatch):
    descriptor = p.request_contract("company.json")
    wrong_request = p.public_request_identity("company.json", {"corp_code": "00999999"}, descriptor)
    monkeypatch.setattr(p, "bounded_exchange", lambda *_, **_kwargs: dict(
        raw=raw(json_company()), error=None, transient=False,
        request_contract_sha256=p.contract_digest(descriptor),
        public_request_sha256=p.contract_digest(wrong_request)))
    result = p.acquire(tmp_path / "capture", "test" * 10,
                       datetime.now(timezone.utc), route="json")
    assert result["error"] == "RESPONSE_PUBLIC_REQUEST_MISMATCH"
    assert not list((tmp_path / "capture").glob("*.raw"))


def test_r17_four_request_cap_is_checked_before_transport(tmp_path, monkeypatch):
    calls = install_transport(monkeypatch, [raw(json_company())])
    collector = p.Collector("test" * 10, tmp_path / "capture",
                            datetime(2026, 10, 16, tzinfo=timezone.utc), route="json")
    collector.confirm_company(collector.get("company.json", {"corp_code": p.COMPANY_SEED}))
    collector.count = 4
    with pytest.raises(p.PilotError, match="REQUEST_BUDGET_OR_STOP"):
        collector.get("list.json", dict(corp_code=p.COMPANY_SEED, bgn_de="20260101",
            end_de="20261016", pblntf_ty="A", last_reprt_at="N", page_no="1", page_count="100"))
    assert len(calls) == 1


def test_r17_historical_headerless_stub_is_not_current_causal_proof(tmp_path, monkeypatch):
    def simulated_server(headers):
        return 200 if headers.get("Accept") == "application/json" and headers.get(
            "User-Agent") == "ThesisMonitor/1.0" else 302
    assert simulated_server({"Accept-Encoding": "identity"}) == 302
    calls = install_transport(monkeypatch, [raw(json_company())])
    collector = p.Collector("test" * 10, tmp_path / "capture",
                            datetime.now(timezone.utc), route="json")
    payload = collector.get("company.json", {"corp_code": p.COMPANY_SEED})
    assert simulated_server(calls[0][2]) == 200
    assert collector.confirm_company(payload)["corp_code"] == p.COMPANY_SEED
    assert len(calls) == 1


def test_r17_cli_selects_json_but_still_requires_explicit_acquire(tmp_path, monkeypatch, capsys):
    called = []
    monkeypatch.setenv("OPENDART_API_KEY", "test" * 10)
    monkeypatch.setattr(p, "acquire", lambda *args, **kwargs: called.append(kwargs) or {"synthetic": True})
    monkeypatch.setattr(p.os.sys, "argv", ["pilot", "--output", str(tmp_path / "none")])
    with pytest.raises(SystemExit):
        p.main()
    assert called == []
    monkeypatch.setattr(p.os.sys, "argv", ["pilot", "--acquire", "--output", str(tmp_path / "none")])
    assert p.main() == 2 and called == [{"route": "json"}]
    assert not (tmp_path / "none").exists()
    assert "test" * 10 not in capsys.readouterr().out

def test_r17_handoff_header_drift_denied_before_process_or_connect(tmp_path, monkeypatch):
    original_exchange = p.bounded_exchange
    collector = p.Collector("test" * 10, tmp_path / "capture",
                            datetime.now(timezone.utc), route="json")
    headers = p.sealed_opendart_contract.opendart_headers()
    def changed_after_freeze(endpoint, params, key, timeout, *, frozen_request):
        monkeypatch.setattr(p.sealed_opendart_contract, "opendart_headers",
                            lambda: {**headers, "User-Agent": "ChangedAfterFreeze"})
        return original_exchange(endpoint, params, key, timeout, frozen_request=frozen_request)
    monkeypatch.setattr(p, "bounded_exchange", changed_after_freeze)
    monkeypatch.setattr(p.multiprocessing, "get_context",
                        lambda *_: pytest.fail("drift must fail before child launch"))
    with pytest.raises(p.PilotError, match="REQUEST_DESCRIPTOR_DRIFT"):
        collector.get("company.json", {"corp_code": p.COMPANY_SEED})
    assert collector.halted
    assert not list(collector.root.glob("*.raw"))


def test_r17_frozen_query_drift_rejected_before_child_launch(monkeypatch):
    frozen = p.public_request_identity("company.json", {"corp_code": p.COMPANY_SEED},
                                       p.request_contract("company.json"))
    monkeypatch.setattr(p.multiprocessing, "get_context",
                        lambda *_: pytest.fail("wrong query must fail before child launch"))
    with pytest.raises(p.PilotError, match="REQUEST_DESCRIPTOR_DRIFT"):
        p.bounded_exchange("company.json", {"corp_code": "00999999"}, "test" * 10, 1,
                           frozen_request=frozen)


@pytest.mark.parametrize("values", [
    ["application/json", "text/html"],
    ["application/json; charset=UTF-8, text/html"],
    ["application/json; charset=UTF-8; charset=ASCII"],
    [""],
])
def test_r17_ambiguous_response_mime_rejected_before_body(tmp_path, monkeypatch, values):
    calls = install_transport(monkeypatch, [raw(json_company())])
    original = Response.__init__
    def with_headers(self, body):
        original(self, body)
        for value in values:
            self.headers["Content-Type"] = value
    monkeypatch.setattr(Response, "__init__", with_headers)
    monkeypatch.setattr(Response, "read1", lambda *_: pytest.fail("ambiguous MIME body read"))
    result = p.acquire(tmp_path / "capture", "test" * 10,
                       datetime.now(timezone.utc), route="json")
    assert result["error"] == "RESPONSE_CONTENT_TYPE_DENIED" and len(calls) == 1
    assert not list((tmp_path / "capture").glob("*.raw"))


@pytest.mark.parametrize("mime", ["application/json;charset=UTF-8", 'application/json; charset="UTF-8"'])
def test_r17_documented_json_charset_is_accepted(tmp_path, monkeypatch, mime):
    install_transport(monkeypatch, [raw(json_company())])
    monkeypatch.setattr(Response, "getheader", lambda *_: mime)
    collector = p.Collector("test" * 10, tmp_path / "capture",
                            datetime.now(timezone.utc), route="json")
    assert collector.confirm_company(collector.get("company.json", {"corp_code": p.COMPANY_SEED}))


def test_r17_non_utc_cutoff_uses_one_utc_generation(tmp_path, monkeypatch):
    from datetime import timedelta

    install_transport(monkeypatch, json_bodies())
    cutoff = datetime(2026, 10, 16, 1, 20, tzinfo=timezone(timedelta(hours=9)))
    result = p.acquire(tmp_path / "capture", "test" * 10, cutoff, route="json")
    assert result["source_status"] == "CAPTURED_UNQUALIFIED"
    occurrence = json.loads((tmp_path / "capture/revenue-occurrence.json").read_text())
    assert occurrence["generation"] == "opendart-pilot-20261015T162000Z"
    for path in (tmp_path / "capture").glob("*-request.json"):
        assert json.loads(path.read_text())["source_generation"] == occurrence["generation"]
