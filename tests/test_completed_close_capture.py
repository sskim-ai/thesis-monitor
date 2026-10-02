from hashlib import sha256
import json

import pytest

from scripts.completed_close_capture import capture_received_response, controls_gate


def capture(tmp_path, **changes):
    kwargs = dict(directory=tmp_path / "capture", raw=b'{"return_code":0}', http_status=200,
                  request_sha256="a" * 64, known_secrets=[b"private-key", "private-token"],
                  validator=lambda raw: dict(status="PASS"))
    kwargs.update(changes)
    return capture_received_response(**kwargs)


def test_string_and_byte_secrets_preserve_market_response(tmp_path):
    result = capture(tmp_path)
    raw = (tmp_path / "capture/response.body").read_bytes()
    assert result["raw_sha256"] == sha256(raw).hexdigest()
    assert result["status"] == "PASS" and result["export_allowed"]
    assert not result["provider_retry_allowed"] and not result["downstream_allowed"]


@pytest.mark.parametrize("failure", [TypeError, ValueError, KeyError])
def test_local_parser_failure_keeps_raw_and_forbids_provider_retry(tmp_path, failure):
    def invalid(raw):
        assert (tmp_path / "capture/response.body").read_bytes() == raw
        assert (tmp_path / "capture/capture.json").is_file()
        raise failure("sensitive exception must not be recorded")
    result = capture(tmp_path, validator=invalid)
    assert result["status"] == "REJECTED"
    assert result["error_class"] == failure.__name__
    assert not result["export_allowed"] and not result["provider_retry_allowed"]
    assert "sensitive exception" not in json.dumps(result)


def test_invalid_secret_input_fails_after_retention(tmp_path):
    result = capture(tmp_path, known_secrets=[object()])
    assert (tmp_path / "capture/response.body").exists()
    assert result["error_class"] == "TypeError" and not result["export_allowed"]


def test_secret_response_stays_private_and_skips_validator(tmp_path):
    result = capture(tmp_path, raw=b'private-token', validator=lambda raw: pytest.fail("must not parse"))
    assert result["reason"] == "KNOWN_SECRET_IN_PRIVATE_RESPONSE"
    assert not result["export_allowed"] and not result["downstream_allowed"]


@pytest.mark.parametrize("status", [302, 400, 401, 403, 429, 500])
def test_http_failure_preserved_without_retry(tmp_path, status):
    result = capture(tmp_path, http_status=status)
    assert result["http_status"] == status and not result["provider_retry_allowed"]
    assert not result["export_allowed"]


def test_duplicate_capture_cannot_replace_original(tmp_path):
    before = capture(tmp_path)
    with pytest.raises(FileExistsError):
        capture(tmp_path, raw=b'changed')
    assert sha256((tmp_path / "capture/response.body").read_bytes()).hexdigest() == before["raw_sha256"]


@pytest.mark.parametrize("change", [{"status": "UNVERIFIABLE"}, {"raw_sha256": None},
                                   {"response_received": False}, {"export_allowed": False}])
def test_incomplete_control_never_opens_stage_b_or_models(change):
    record = dict(status="PASS", raw_sha256="b" * 64, response_received=True, export_allowed=True)
    assert controls_gate({"X": record}, ("X",))["stage_b_allowed"]
    result = controls_gate({"X": dict(record, **change)}, ("X",))
    assert not result["stage_b_allowed"] and not result["model_calls_allowed"]


def test_missing_and_extra_control_fail_closed():
    assert controls_gate({}, ("X",))["missing"] == ["X"]
    assert controls_gate({"Y": {}}, ("X",))["extra"] == ["Y"]
