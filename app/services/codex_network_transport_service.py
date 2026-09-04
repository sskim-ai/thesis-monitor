from __future__ import annotations

import socket
import ssl
import stat
import time
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Callable


NETWORK_READINESS_CONTRACT = "codex-network-readiness-v1"
CODEX_NETWORK_HOST = "chatgpt.com"
CODEX_NETWORK_PORT = 443
NETWORK_PROBE_ATTEMPT_LIMIT = 3
NETWORK_PROBE_TIMEOUT_SECONDS = 5.0
NETWORK_PROBE_BACKOFF_SECONDS = (0.5, 1.5)
CODEX_CA_CERTIFICATE_ENV = "CODEX_CA_CERTIFICATE"
SSL_CERT_FILE_ENV = "SSL_CERT_FILE"
SYSTEM_CA_BUNDLE_CANDIDATES = (
    Path("/etc/ssl/cert.pem"),
    Path("/etc/ssl/certs/ca-certificates.crt"),
)


class CodexTransportFailureType(StrEnum):
    TLS_CERTIFICATE_UNKNOWN_ISSUER = "TLS_CERTIFICATE_UNKNOWN_ISSUER"
    TLS_CERTIFICATE_EXPIRED = "TLS_CERTIFICATE_EXPIRED"
    TLS_CERTIFICATE_HOSTNAME_MISMATCH = "TLS_CERTIFICATE_HOSTNAME_MISMATCH"
    TLS_CERTIFICATE_OTHER = "TLS_CERTIFICATE_OTHER"
    DNS_FAILURE = "DNS_FAILURE"
    CONNECT_TIMEOUT = "CONNECT_TIMEOUT"
    CONNECTION_REFUSED = "CONNECTION_REFUSED"
    OTHER_TRANSPORT_FAILURE = "OTHER_TRANSPORT_FAILURE"

    # Retained for persisted historical receipts and non-certificate transport states.
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


@dataclass(frozen=True)
class CodexTLSConfiguration:
    environment: dict[str, str]
    trust_source: str
    ca_bundle_path: str | None


@dataclass(frozen=True)
class CodexTransportDiagnostic:
    failure_type: CodexTransportFailureType
    raw_diagnostic_token: str | None = None


class CodexTransportError(ValueError):
    def __init__(
        self,
        failure_type: CodexTransportFailureType,
        *,
        attempts: int,
        raw_diagnostic_token: str | None = None,
    ) -> None:
        self.failure_type = failure_type
        self.attempts = attempts
        self.raw_diagnostic_token = raw_diagnostic_token
        super().__init__(f"{failure_type.value}:attempts={attempts}")


def _is_approved_system_ca_bundle(path: Path) -> bool:
    try:
        resolved = path.resolve(strict=True)
        metadata = resolved.stat()
    except OSError:
        return False
    return (
        stat.S_ISREG(metadata.st_mode)
        and metadata.st_uid == 0
        and not stat.S_IMODE(metadata.st_mode) & 0o022
        and resolved.stat().st_size > 0
    )


def codex_tls_environment(base: dict[str, str]) -> CodexTLSConfiguration:
    environment = dict(base)
    explicit_codex_ca = environment.get(CODEX_CA_CERTIFICATE_ENV)
    if explicit_codex_ca:
        return CodexTLSConfiguration(
            environment=environment,
            trust_source="EXPLICIT_CODEX_CA_CERTIFICATE",
            ca_bundle_path=explicit_codex_ca,
        )
    explicit_ssl_ca = environment.get(SSL_CERT_FILE_ENV)
    if explicit_ssl_ca:
        return CodexTLSConfiguration(
            environment=environment,
            trust_source="EXPLICIT_SSL_CERT_FILE",
            ca_bundle_path=explicit_ssl_ca,
        )
    for candidate in SYSTEM_CA_BUNDLE_CANDIDATES:
        if _is_approved_system_ca_bundle(candidate):
            environment[CODEX_CA_CERTIFICATE_ENV] = str(candidate)
            return CodexTLSConfiguration(
                environment=environment,
                trust_source="ROOT_OWNED_SYSTEM_CA_BUNDLE",
                ca_bundle_path=str(candidate),
            )
    return CodexTLSConfiguration(
        environment=environment,
        trust_source="CODEX_BUILT_IN_DEFAULT",
        ca_bundle_path=None,
    )


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
        return CodexTransportFailureType.DNS_FAILURE
    if isinstance(exc, ConnectionRefusedError):
        return CodexTransportFailureType.CONNECTION_REFUSED
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return CodexTransportFailureType.CONNECT_TIMEOUT
    if isinstance(exc, ssl.SSLCertVerificationError):
        return diagnose_codex_transport_failure(str(exc)).failure_type
    if isinstance(exc, ssl.SSLError):
        return CodexTransportFailureType.TLS_CERTIFICATE_OTHER
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
    return diagnose_codex_transport_failure(log_text, timed_out=timed_out).failure_type


def diagnose_codex_transport_failure(
    log_text: str,
    *,
    timed_out: bool = False,
) -> CodexTransportDiagnostic:
    if timed_out:
        return CodexTransportDiagnostic(CodexTransportFailureType.MODEL_TIMEOUT)

    normalized = log_text.casefold()
    compact = "".join(character for character in normalized if character.isalnum())
    marker_groups = (
        (
            CodexTransportFailureType.TLS_CERTIFICATE_UNKNOWN_ISSUER,
            ("unknownissuer", "unknown issuer", "unable to get local issuer certificate"),
            "UnknownIssuer",
        ),
        (
            CodexTransportFailureType.TLS_CERTIFICATE_EXPIRED,
            ("certificate has expired", "expired certificate", "certificateexpired"),
            "CertificateExpired",
        ),
        (
            CodexTransportFailureType.TLS_CERTIFICATE_HOSTNAME_MISMATCH,
            (
                "hostname mismatch",
                "certificate is not valid for",
                "not valid for name",
                "invalid certificate subject name",
            ),
            "HostnameMismatch",
        ),
        (
            CodexTransportFailureType.TLS_CERTIFICATE_OTHER,
            (
                "certificate verify failed",
                "invalid peer certificate",
                "tls handshake failed",
                "ssl handshake failed",
            ),
            "CertificateVerifyFailed",
        ),
        (
            CodexTransportFailureType.DNS_FAILURE,
            (
                "failed to lookup address information",
                "nodename nor servname provided",
                "name or service not known",
                "temporary failure in name resolution",
                "could not resolve host",
            ),
            "DNSFailure",
        ),
        (
            CodexTransportFailureType.MODEL_RATE_LIMIT,
            (
                "rate limit",
                "too many requests",
                "status code: 429",
                "http status 429",
            ),
            "RateLimit",
        ),
        (
            CodexTransportFailureType.CONNECTION_REFUSED,
            (
                "connection refused",
                "connectionrefused",
            ),
            "ConnectionRefused",
        ),
        (
            CodexTransportFailureType.CONNECT_TIMEOUT,
            (
                "connect timeout",
                "connection timed out",
                "timed out while connecting",
                "connecttimeout",
            ),
            "ConnectTimeout",
        ),
        (
            CodexTransportFailureType.LOCAL_NETWORK_CONNECTIVITY_FAILURE,
            (
                "network is unreachable",
                "no route to host",
                "error_is_connect=true",
            ),
            "LocalNetworkConnectivityFailure",
        ),
        (
            CodexTransportFailureType.MODEL_TIMEOUT,
            (
                "error_is_timeout=true",
                "request timed out",
                "operation timed out",
            ),
            "ModelTimeout",
        ),
        (
            CodexTransportFailureType.CODEX_APP_SERVER_TRANSPORT_FAILURE,
            (
                "failed to connect to websocket",
                "stream disconnected before completion",
                "falling back from websockets to https transport",
                "transport channel closed",
            ),
            "AppServerTransportFailure",
        ),
    )
    for failure_type, markers, raw_token in marker_groups:
        if any(marker in normalized or marker in compact for marker in markers):
            return CodexTransportDiagnostic(failure_type, raw_token)
    return CodexTransportDiagnostic(
        CodexTransportFailureType.OTHER_TRANSPORT_FAILURE,
        "OtherTransportFailure",
    )


def retryable_codex_transport_failure(
    failure_type: CodexTransportFailureType,
) -> bool:
    return failure_type in {
        CodexTransportFailureType.DNS_FAILURE,
        CodexTransportFailureType.CONNECT_TIMEOUT,
        CodexTransportFailureType.CONNECTION_REFUSED,
        CodexTransportFailureType.LOCAL_DNS_RESOLUTION_FAILURE,
        CodexTransportFailureType.LOCAL_NETWORK_CONNECTIVITY_FAILURE,
        CodexTransportFailureType.CODEX_APP_SERVER_TRANSPORT_FAILURE,
    }
