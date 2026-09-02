from __future__ import annotations

import socket
import ssl

import pytest

from app.services import codex_network_transport_service as service
from app.services.codex_network_transport_service import (
    NETWORK_READINESS_CONTRACT,
    CodexTransportFailureType,
    classify_codex_transport_failure,
    probe_codex_network_readiness,
    retryable_codex_transport_failure,
)


def test_network_readiness_recovers_after_bounded_dns_retry(monkeypatch) -> None:
    calls = 0
    delays: list[float] = []

    def fake_probe_once(host: str, port: int, timeout: float) -> int:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise socket.gaierror("temporary resolver failure")
        assert host == "chatgpt.com"
        assert port == 443
        assert timeout == 2.0
        return 4

    monkeypatch.setattr(service, "_probe_once", fake_probe_once)

    result = probe_codex_network_readiness(
        attempts=3,
        timeout=2.0,
        backoff_seconds=(0.25, 0.5),
        sleeper=delays.append,
    )

    assert result.contract == NETWORK_READINESS_CONTRACT
    assert result.ready is True
    assert result.attempts == 2
    assert result.resolved_address_count == 4
    assert result.failure_history == (
        CodexTransportFailureType.LOCAL_DNS_RESOLUTION_FAILURE,
    )
    assert delays == [0.25]


@pytest.mark.parametrize(
    ("error", "expected"),
    (
        (
            socket.gaierror("resolver unavailable"),
            CodexTransportFailureType.LOCAL_DNS_RESOLUTION_FAILURE,
        ),
        (
            ConnectionError("network unavailable"),
            CodexTransportFailureType.LOCAL_NETWORK_CONNECTIVITY_FAILURE,
        ),
        (
            ssl.SSLError("certificate verify failed"),
            CodexTransportFailureType.TLS_HANDSHAKE_FAILURE,
        ),
    ),
)
def test_network_readiness_failures_are_exact_and_bounded(
    monkeypatch,
    error: OSError,
    expected: CodexTransportFailureType,
) -> None:
    calls = 0
    delays: list[float] = []

    def fake_probe_once(host: str, port: int, timeout: float) -> int:
        nonlocal calls
        calls += 1
        raise error

    monkeypatch.setattr(service, "_probe_once", fake_probe_once)

    result = probe_codex_network_readiness(
        attempts=3,
        backoff_seconds=(0.1, 0.2),
        sleeper=delays.append,
    )

    assert result.ready is False
    assert result.failure_type == expected
    assert result.failure_history == (expected, expected, expected)
    assert calls == 3
    assert delays == [0.1, 0.2]


def test_codex_log_failure_taxonomy_prioritizes_dns_root_cause() -> None:
    log = """
    failed to connect to websocket: IO error: failed to lookup address information
    stream disconnected before completion
    error_is_connect=true
    """

    assert (
        classify_codex_transport_failure(log)
        == CodexTransportFailureType.LOCAL_DNS_RESOLUTION_FAILURE
    )


@pytest.mark.parametrize(
    ("log", "timed_out", "expected"),
    (
        (
            "certificate verify failed during TLS handshake",
            False,
            CodexTransportFailureType.TLS_HANDSHAKE_FAILURE,
        ),
        (
            "HTTP status 429: too many requests",
            False,
            CodexTransportFailureType.MODEL_RATE_LIMIT,
        ),
        (
            "stream disconnected before completion",
            False,
            CodexTransportFailureType.CODEX_APP_SERVER_TRANSPORT_FAILURE,
        ),
        ("", True, CodexTransportFailureType.MODEL_TIMEOUT),
        ("unexpected provider response", False, CodexTransportFailureType.MODEL_PROVIDER_RESPONSE_FAILURE),
    ),
)
def test_codex_log_failure_taxonomy(
    log: str,
    timed_out: bool,
    expected: CodexTransportFailureType,
) -> None:
    assert classify_codex_transport_failure(log, timed_out=timed_out) == expected


def test_only_transient_transport_failures_are_retryable() -> None:
    assert retryable_codex_transport_failure(
        CodexTransportFailureType.LOCAL_DNS_RESOLUTION_FAILURE
    )
    assert retryable_codex_transport_failure(
        CodexTransportFailureType.CODEX_APP_SERVER_TRANSPORT_FAILURE
    )
    assert not retryable_codex_transport_failure(
        CodexTransportFailureType.MODEL_RATE_LIMIT
    )
    assert not retryable_codex_transport_failure(
        CodexTransportFailureType.MODEL_PROVIDER_RESPONSE_FAILURE
    )
