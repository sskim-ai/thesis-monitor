"""Original-engine Source projection; synthetic bars and transport only."""

from copy import deepcopy
from datetime import date, timedelta
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pandas as pd
import pytest

from app.services.unified_stock_acquisition import decode_native_indicators
from scripts import unified_stock_source_worker as worker


ORIGINAL_SOURCE_SHA256 = "ed793cdeb4b89d6787f95e5ee2ba191ec0f7ffd0d1c680b90451dc10aa838835"
ORIGINAL_SOURCE_URL = (
    "https://github.com/sskim-ai/ohlcv-analyst/blob/"
    "f19c54b8299031caf473737e044f0a2b77db5671/app/indicators/technical.py"
)


def load_original_engine(tmp_path):
    """Load the pinned Analyst source; no fetching or formula copies in tests.

    Source: ORIGINAL_SOURCE_URL, Git blob 7054107179b78a49165fc019eb14019808ce27c3.
    The source is immutable test data, never imported by production code.
    """
    fixture = Path(__file__).parent / "fixtures/ohlcv-native-f19c54b.technical.py.txt"
    if not fixture.is_file():
        pytest.fail("Pinned original OHLCV test data missing: " + str(fixture))
    raw = fixture.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == ORIGINAL_SOURCE_SHA256, "original_indicator_source_sha256_mismatch"
    path = tmp_path / "original_ohlcv_technical.py"
    path.write_bytes(raw)
    spec = importlib.util.spec_from_file_location("c58_original_ohlcv_technical", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def original_engine(tmp_path):
    return load_original_engine(tmp_path)


def bars(count=720):
    return [dict(date=(date(2023, 1, 1) + timedelta(days=i)).isoformat(),
                 open=100 + i % 11, high=115 + i % 11, low=90 + i % 11,
                 close=101 + i % 7 + i / 100, volume=1000 + i % 13)
            for i in range(count)]


@pytest.mark.parametrize("market,timeframe", [("kr", "daily"), ("us", "weekly"),
                                               ("kr", "monthly")])
def test_full_history_uses_exact_original_values_then_bounds_output(original_engine, market, timeframe):
    source = bars()
    original = deepcopy(source)
    entry = dict(entry_id=f"{market}:SYNTHETIC:adjusted_{timeframe}")
    expected = original_engine.add_indicators(pd.DataFrame(source))
    result = worker.native_indicator_projection(source, entry, worker.sha(worker.encoded(source)),
                                                engine=original_engine)
    assert result["status"] == "AVAILABLE" and result["reason"] is None
    assert result["calculation_row_count"] == len(source) and len(result["rows"]) == 30
    assert result["rows"] == [{"date": str(row["date"]),
                               "indicators": original_engine.indicator_dict(row)}
                              for _, row in expected.tail(30).iterrows()]
    assert len(result["rows"][-1]["indicators"]) == 38
    assert result["rows"][-1]["indicators"]["MA288"] is not None
    assert result["engine"]["calculator"]["source_sha256"] == hashlib.sha256(
        Path(original_engine.__file__).read_bytes()).hexdigest()
    assert source == original


def test_original_calculator_runs_once_and_short_history_is_preserved(original_engine):
    source = bars(18)
    original_calculate = original_engine.add_indicators
    calls = []

    def calculate(frame):
        calls.append(len(frame))
        return original_calculate(frame)

    engine = SimpleNamespace(add_indicators=calculate, indicator_dict=original_engine.indicator_dict)
    result = worker.native_indicator_projection(source, {"entry_id": "us:SHORT:adjusted_monthly"},
                                                worker.sha(worker.encoded(source)), engine=engine)
    assert calls == [18]
    assert result["status"] == "AVAILABLE" and len(result["rows"]) == 18
    assert result["rows"][-1]["indicators"]["MA288"] is None
    assert result["rows"][-1]["indicators"]["MACD_OSC_320_640_9"] is not None


def test_supplied_values_and_nulls_never_trigger_a_calculator(original_engine):
    source = bars(3)
    values = dict.fromkeys(original_engine.INDICATOR_COLUMNS)
    values.update(RSI14=47.123456789012, MACD=-0.000000123456789)
    for row in source:
        row["indicators"] = deepcopy(values)

    def forbidden(*args, **kwargs):
        raise AssertionError("provider values recalculated")

    engine = SimpleNamespace(add_indicators=forbidden, indicator_dict=forbidden)
    result = worker.native_indicator_projection(source, {"entry_id": "kr:SUPPLIED:adjusted_daily"},
                                                worker.sha(worker.encoded(source)), engine=engine)
    assert result["status"] == "AVAILABLE"
    assert result["rows"][-1]["indicators"] == values
    assert result["engine"] == {"mode": "PROVIDER_SUPPLIED"}
    for row in source:
        row["indicators"] = None
    absent = worker.native_indicator_projection(source, {"entry_id": "kr:SUPPLIED:adjusted_daily"},
                                                worker.sha(worker.encoded(source)), engine=engine)
    assert absent["status"] == "UNAVAILABLE"
    assert absent["reason"] == "PROVIDER_INDICATORS_UNAVAILABLE"


@pytest.mark.parametrize("market,failure", [("kr", False), ("us", True)])
def test_real_worker_preserves_raw_capture_and_http_counts(tmp_path, monkeypatch, original_engine,
                                                         market, failure):
    from app.services import kiwoom_global_lane

    monkeypatch.setattr(kiwoom_global_lane, "boot_identity", lambda: "SYNTHETIC_C58_BOOT")
    source = bars(18)
    code = "005930" if market == "kr" else "MU"
    route = "/api/dostk/chart" if market == "kr" else "/api/us/chart"
    api = "ka10081" if market == "kr" else "usa06012"
    entry = dict(entry_id=f"{market}:{code}:adjusted_daily", subject=code, market=market,
                 role="adjusted_daily", timeframe="daily", adjusted=True,
                 exchange="KRX" if market == "kr" else "ND", query_date="20261125",
                 count=len(source), max_pages=1, route=route, api_id=api)
    plan = dict(run_id="SYNTHETIC", acquisition_id="SYNTHETIC:source", reads=[entry])
    calls = []

    class Client:
        def __enter__(self):
            return self

        def __exit__(self, *unused):
            return False

        def post(self, url, *, json, headers, timeout):
            calls.append(url)
            return httpx.Response(200, json={"return_code": 0, "rows": source},
                                  headers={"cont-yn": "N", "next-key": ""},
                                  request=httpx.Request("POST", url))

    class Provider:
        def __init__(self, client):
            self.client = client

        def get_bars(self, **kwargs):
            body = dict(stk_cd=code, upd_stkpc_tp="1")
            if market == "kr":
                body["base_dt"] = entry["query_date"]
            else:
                body.update(stex_tp="ND", strt_dt="", exrt_appl_tp="0")
            response = owner.httpx.post("https://api.kiwoom.com" + route, json=body,
                headers={"api-id": api, "cont-yn": "N", "next-key": ""}, timeout=10)
            return response.json()["rows"]

    owner = SimpleNamespace(KiwoomProvider=Provider, KiwoomClient=lambda *a: None,
                            KiwoomAuth=lambda *a: None)
    settings = SimpleNamespace(kiwoom_app_key="SYNTHETIC", kiwoom_secret_key="SYNTHETIC",
                               model_copy=lambda **kwargs: settings)
    engine = original_engine
    if failure:
        def broken(frame):
            raise RuntimeError("do not leak arbitrary exception text")
        engine = SimpleNamespace(add_indicators=broken, indicator_dict=original_engine.indicator_dict)
    monkeypatch.setattr(worker, "importlib", SimpleNamespace(import_module=lambda name: engine))
    monkeypatch.setattr(worker, "httpx", SimpleNamespace(Client=lambda **kw: Client(),
                        HTTPTransport=lambda **kw: None, HTTPError=httpx.HTTPError))
    root = tmp_path / "capture"
    worker.acquire(plan, root, owner, settings)
    receipt = json.loads((root / "role-001.receipt.json").read_bytes())
    assert receipt["status"] == "CAPTURED"
    raw = (root / receipt["normalized_artifact"]).read_bytes()
    assert raw == worker.encoded(source)
    assert receipt["normalized_sha256"] == worker.sha(raw)
    result = decode_native_indicators(SimpleNamespace(**entry), receipt,
                                      lambda path, expected: (root / path).read_bytes(), required=True)
    assert result["status"] == ("UNAVAILABLE" if failure else "AVAILABLE")
    if failure:
        assert result["reason"] == "ORIGINAL_INDICATOR_ENGINE_ERROR_RuntimeError"
        assert "do not leak" not in json.dumps(result)
    counts = json.loads((root / "transport-counts.json").read_bytes())
    assert len(calls) == counts["provider_data_requests"] == counts["external_transport_requests"] == 1
    assert counts["model_calls"] == counts["fallback_calls"] == counts["automatic_retries"] == 0


def test_decode_keeps_missing_legacy_separate_from_new_capture_gap():
    read = SimpleNamespace(entry_id="kr:005930:adjusted_daily", adjusted=True)
    assert decode_native_indicators(read, {}, lambda *a: b"") is None
    with pytest.raises(ValueError, match="native_indicator_artifact_required"):
        decode_native_indicators(read, {}, lambda *a: b"", required=True)


@pytest.mark.parametrize("change", ["bytes", "source", "entry"])
def test_decode_rejects_sidecar_from_a_different_capture(original_engine, change):
    source = bars(3)
    entry = dict(entry_id="kr:005930:adjusted_daily", adjusted=True)
    normalized_sha = worker.sha(worker.encoded(source))
    payload = worker.native_indicator_projection(source, entry, normalized_sha, engine=original_engine)
    if change == "source":
        payload["source_normalized_sha256"] = "0" * 64
    if change == "entry":
        payload["entry_id"] = "us:MU:adjusted_daily"
    raw = worker.encoded(payload)
    receipt = dict(entry=entry, normalized_sha256=normalized_sha,
                   native_indicators=dict(artifact="native.json", sha256=worker.sha(raw)))
    if change == "bytes":
        raw += b" "
    with pytest.raises(ValueError, match="native_indicator_(artifact_hash|source_binding)_mismatch"):
        decode_native_indicators(SimpleNamespace(**entry), receipt, lambda *a: raw, required=True)
