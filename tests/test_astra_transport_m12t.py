from pathlib import Path

import pytest

from scripts import astra_transport_m12t as audit


def receipt():
    return {
        "started_at": "2026-01-01T00:00:00+00:00",
        "finished_at": "2026-01-01T00:30:00+00:00",
        "wrapper_retry_count": 0,
        "timed_out": True,
        "output_size": 0,
        "network_readiness": {"ready": True},
        "status": "FAIL",
        "failure_type": "MODEL_TIMEOUT",
    }


LOG = "OpenAI Codex v0.test\nmodel: gpt-6-astra\nreasoning effort: xhigh\nsession id: fictional-session\nuser\ncontent\nWARN codex_core::responses_retry: stream disconnected - retrying sampling request (1/5)"


def test_internal_retry_is_not_wrapper_retry():
    result = audit.diagnostics(receipt(), LOG, b"prompt", b"{}")
    assert result["cli_internal_retry_event_count"] == 1
    assert result["wrapper_retry_count"] == 0
    assert result["elapsed_seconds"] == 1800
    assert result["observed_model"] == "gpt-6-astra"
    assert result["backend_sampling_request_count"] == "NOT_MEASURED"


def test_missing_header_is_not_inferred_from_requested_model():
    result = audit.diagnostics({**receipt(), "model": "gpt-6-astra"}, "", b"", b"")
    assert result["observed_model"] == "NOT_MEASURED"


@pytest.mark.parametrize("failed", [False, True])
def test_observation_preserves_single_attempt_and_failure(tmp_path, failed):
    kwargs = {
        key: tmp_path / name
        for key, name in (
            ("receipt_path", "receipt.json"),
            ("log", "transport.log"),
            ("prompt", "prompt.txt"),
            ("schema", "schema.json"),
        )
    }
    kwargs["log"].write_text(LOG)
    kwargs["prompt"].write_text("fictional")
    kwargs["schema"].write_text("{}")
    calls = []

    def original(**kw):
        calls.append(kw)
        r = receipt()
        audit.write(kw["receipt_path"], r)
        if failed:
            raise RuntimeError("MODEL_TIMEOUT")
        return r

    if failed:
        with pytest.raises(RuntimeError, match="MODEL_TIMEOUT"):
            audit.observed_call(original, **kwargs)
    else:
        assert audit.observed_call(original, **kwargs)["cli_internal_retry_event_count"] == 1
    saved = audit.read(kwargs["receipt_path"])
    assert saved["failure_type"] == "MODEL_TIMEOUT"
    assert saved["observed_effort"] == "xhigh"
    assert len(calls) == 1


def test_required_report_ids_and_runtime_contract():
    assert set(audit.SLUGS) == set(range(1, 63))
    assert len(set(audit.SLUGS.values())) == 62
    assert audit.m12.TIMEOUT_SECONDS == 1800
    assert audit.m12.SUBJECTS_PER_CONTEXT == 4
    assert audit.m12.REPETITION_COUNT == 3
    assert Path(audit.INSTRUCTION).is_file()
