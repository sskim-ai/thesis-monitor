from __future__ import annotations

import socket
import ssl
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Callable


NETWORK_READINESS_CONTRACT = "codex-network-readiness-v1"
CODEX_NETWORK_HOST = "chatgpt.com"
CODEX_NETWORK_PORT = 443
NETWORK_PROBE_ATTEMPT_LIMIT = 3
NETWORK_PROBE_TIMEOUT_SECONDS = 5.0
NETWORK_PROBE_BACKOFF_SECONDS = (0.5, 1.5)


class CodexTransportFailureType(StrEnum):
    LOCAL_DNS_RESOLUTION_FAILURE = "LOCAL_DNS_RESOLUTION_FAILURE"
    LOCAL_NETWORK_CONNECTIVITY_FAILURE = "LOCAL_NETWORK_CONNECTIVITY_FAILURE"
    TLS_HANDSHAKE_FAILURE = "TLS_HANDSHAKE_FAILURE"
    CODEX_APP_SERVER_TRANSPORT_FAILURE = "CODEX_APP_SERVER_TRANSPORT_FAILURE"
    MODEL_PROVIDER_RESPONSE_FAILURE = "MODEL_PROVIDER_RESPONSE_FAILURE"
    MODEL_TIMEOUT = "MODEL_TIMEOUT"
    MODEL_RATE_LIMIT = "MODEL_RATE_LIMIT"


@dataclass(frozen=True)
class CodexNetworkReadiness:
    contract: str
    ready: bool
    host: str
    port: int
    attempts: int
    resolved_address_count: int
    failure_type: CodexTransportFailureType | None = None
    failure_history: tuple[CodexTransportFailureType, ...] = ()


class CodexTransportError(ValueError):
    def __init__(
        self,
        failure_type: CodexTransportFailureType,
        *,
        attempts: int,
    ) -> None:
        self.failure_type = failure_type
        self.attempts = attempts
        super().__init__(f"{failure_type.value}:attempts={attempts}")


def _probe_once(host: str, port: int, timeout: float) -> int:
    addresses = socket.getaddrinfo(
        host,
        port,
        type=socket.SOCK_STREAM,
    )
    if not addresses:
        raise socket.gaierror("resolver_returned_no_addresses")

    context = ssl.create_default_context()
    last_error: OSError | None = None
    for family, socktype, proto, _, sockaddr in addresses:
        raw_socket = socket.socket(family, socktype, proto)
        try:
            raw_socket.settimeout(timeout)
            raw_socket.connect(sockaddr)
            with context.wrap_socket(raw_socket, server_hostname=host):
                return len(addresses)
        except ssl.SSLError:
            raw_socket.close()
            raise
        except OSError as exc:
            last_error = exc
            raw_socket.close()
    if last_error is not None:
        raise last_error
    raise OSError("network_probe_connection_failed")


def _probe_failure_type(exc: BaseException) -> CodexTransportFailureType:
    if isinstance(exc, socket.gaierror):
        return CodexTransportFailureType.LOCAL_DNS_RESOLUTION_FAILURE
    if isinstance(exc, ssl.SSLError):
        return CodexTransportFailureType.TLS_HANDSHAKE_FAILURE
    return CodexTransportFailureType.LOCAL_NETWORK_CONNECTIVITY_FAILURE


def probe_codex_network_readiness(
    *,
    host: str = CODEX_NETWORK_HOST,
    port: int = CODEX_NETWORK_PORT,
    attempts: int = NETWORK_PROBE_ATTEMPT_LIMIT,
    timeout: float = NETWORK_PROBE_TIMEOUT_SECONDS,
    backoff_seconds: tuple[float, ...] = NETWORK_PROBE_BACKOFF_SECONDS,
    sleeper: Callable[[float], None] = time.sleep,
) -> CodexNetworkReadiness:
    if attempts < 1:
        raise ValueError("codex_network_probe_attempts_must_be_positive")

    failures: list[CodexTransportFailureType] = []
    for attempt in range(1, attempts + 1):
        try:
            resolved_address_count = _probe_once(host, port, timeout)
        except (OSError, ssl.SSLError) as exc:
            failures.append(_probe_failure_type(exc))
            if attempt < attempts:
                delay_index = min(attempt - 1, len(backoff_seconds) - 1)
                if backoff_seconds:
                    sleeper(backoff_seconds[delay_index])
            continue
        return CodexNetworkReadiness(
            contract=NETWORK_READINESS_CONTRACT,
            ready=True,
            host=host,
            port=port,
            attempts=attempt,
            resolved_address_count=resolved_address_count,
            failure_history=tuple(failures),
        )

    return CodexNetworkReadiness(
        contract=NETWORK_READINESS_CONTRACT,
        ready=False,
        host=host,
        port=port,
        attempts=attempts,
        resolved_address_count=0,
        failure_type=failures[-1],
        failure_history=tuple(failures),
    )


def classify_codex_transport_failure(
    log_text: str,
    *,
    timed_out: bool = False,
) -> CodexTransportFailureType:
    if timed_out:
        return CodexTransportFailureType.MODEL_TIMEOUT

    normalized = log_text.casefold()
    marker_groups = (
        (
            CodexTransportFailureType.LOCAL_DNS_RESOLUTION_FAILURE,
            (
                "failed to lookup address information",
                "nodename nor servname provided",
                "name or service not known",
                "temporary failure in name resolution",
                "could not resolve host",
            ),
        ),
        (
            CodexTransportFailureType.MODEL_RATE_LIMIT,
            (
                "rate limit",
                "too many requests",
                "status code: 429",
                "http status 429",
            ),
        ),
        (
            CodexTransportFailureType.TLS_HANDSHAKE_FAILURE,
            (
                "certificate verify failed",
                "tls handshake failed",
                "ssl handshake failed",
                "unknown issuer",
            ),
        ),
        (
            CodexTransportFailureType.LOCAL_NETWORK_CONNECTIVITY_FAILURE,
            (
                "network is unreachable",
                "no route to host",
                "connection refused",
                "error_is_connect=true",
            ),
        ),
        (
            CodexTransportFailureType.MODEL_TIMEOUT,
            (
                "error_is_timeout=true",
                "request timed out",
                "operation timed out",
            ),
        ),
        (
            CodexTransportFailureType.CODEX_APP_SERVER_TRANSPORT_FAILURE,
            (
                "failed to connect to websocket",
                "stream disconnected before completion",
                "falling back from websockets to https transport",
                "transport channel closed",
            ),
        ),
    )
    for failure_type, markers in marker_groups:
        if any(marker in normalized for marker in markers):
            return failure_type
    return CodexTransportFailureType.MODEL_PROVIDER_RESPONSE_FAILURE


def retryable_codex_transport_failure(
    failure_type: CodexTransportFailureType,
) -> bool:
    return failure_type in {
        CodexTransportFailureType.LOCAL_DNS_RESOLUTION_FAILURE,
        CodexTransportFailureType.LOCAL_NETWORK_CONNECTIVITY_FAILURE,
        CodexTransportFailureType.TLS_HANDSHAKE_FAILURE,
        CodexTransportFailureType.CODEX_APP_SERVER_TRANSPORT_FAILURE,
    }
