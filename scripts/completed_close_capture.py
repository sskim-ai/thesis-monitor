"""Offline-safe market-response capture; not a qualified production price owner.

The caller owns authorization, exact requests and network budgets. This module
never performs requests and never permits recollection after a local failure.
"""
from hashlib import sha256
from pathlib import Path
from typing import Callable, Iterable

from app.services.unified_run_artifacts import durable_bytes, durable_json


def _secret_bytes(values: Iterable[bytes | str]) -> tuple[bytes, ...]:
    result = []
    for value in values:
        if not isinstance(value, (bytes, str)):
            raise TypeError("capture_secret_value_type_invalid")
        if value:
            result.append(value.encode() if isinstance(value, str) else value)
    return tuple(result)


def capture_received_response(*, directory: Path, raw: bytes, http_status: int,
                              request_sha256: str, known_secrets: Iterable[bytes | str],
                              validator: Callable[[bytes], dict]) -> dict:
    """Persist immutable bytes before any parser/validator/secret-scanner runs.

    A local validation failure blocks export and downstream use, not retention.
    Exception messages are deliberately omitted because they may contain data.
    """
    if not isinstance(raw, bytes) or type(http_status) is not int:
        raise ValueError("capture_response_envelope_invalid")
    if len(request_sha256) != 64 or any(c not in "0123456789abcdef" for c in request_sha256):
        raise ValueError("capture_request_hash_invalid")
    directory.mkdir(parents=True, exist_ok=False, mode=0o700)
    durable_bytes(directory / "response.body", raw, exclusive=True)
    identity = dict(http_status=http_status, raw_sha256=sha256(raw).hexdigest(), raw_bytes=len(raw),
                    request_sha256=request_sha256, response_received=True, provider_retry_allowed=False)
    durable_json(directory / "capture.json", identity, exclusive=True)
    result = dict(**identity, status="REJECTED", export_allowed=False, downstream_allowed=False)
    try:
        if any(value in raw for value in _secret_bytes(known_secrets)):
            result["reason"] = "KNOWN_SECRET_IN_PRIVATE_RESPONSE"
        elif http_status != 200:
            result["reason"] = "HTTP_FAILURE_RESPONSE_PRESERVED"
        else:
            validation = validator(raw)
            if not isinstance(validation, dict) or validation.get("status") not in {"PASS", "FAIL"}:
                raise ValueError("capture_validator_result_invalid")
            result.update(status=validation["status"], export_allowed=True, validation=validation)
            # Qualification PASS is still not whole-source authorization.
            result["downstream_allowed"] = False
    except Exception as exc:
        result.update(reason="LOCAL_VALIDATION_FAILURE_RESPONSE_PRESERVED", error_class=type(exc).__name__)
    durable_json(directory / "validation.json", result, exclusive=True)
    return result


def controls_gate(receipts: dict[str, dict], required: tuple[str, ...]) -> dict:
    """Every required control needs an independently retained, verified response."""
    missing = sorted(set(required) - set(receipts))
    extra = sorted(set(receipts) - set(required))
    failed = sorted(t for t, row in receipts.items() if row.get("status") != "PASS"
                    or not row.get("response_received") or not row.get("raw_sha256")
                    or not row.get("export_allowed"))
    passed = not missing and not extra and not failed
    return dict(status="PASS" if passed else "FAIL", missing=missing, extra=extra, failed=failed,
                stage_b_allowed=passed, model_calls_allowed=False)
