"""Durable local receipts and secret-minimized terminal debug export."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import zipfile

from app.services.unified_snapshot_contract import encoded


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def durable_bytes(path: Path, content: bytes, *, exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if exclusive:
            os.link(temporary, path)
            temporary.unlink()
        else:
            os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def durable_json(path: Path, value: object, *, exclusive: bool = False) -> None:
    durable_bytes(path, encoded(value) + b"\n", exclusive=exclusive)


SECRET_KEY = re.compile(r"token|password|secret|credential|api.?key|authorization|chat.?id", re.I)
SECRET_VALUE = re.compile(
    r"(?:Bearer\s+\S+|\b\d{7,}:[A-Za-z0-9_-]{20,}|\bsk-[A-Za-z0-9_-]{16,}|"
    r"(?i:api[_-]?key|token|password|authorization|chat_id)\s*[=:]\s*[^\s&,;]+)"
)


def sanitized(value: object, secrets: tuple[str, ...] = ()) -> object:
    if isinstance(value, dict):
        return {str(k): "[REDACTED]" if SECRET_KEY.search(str(k)) else sanitized(v, secrets)
                for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitized(v, secrets) for v in value]
    if isinstance(value, str):
        for secret in sorted((s for s in secrets if s), key=len, reverse=True):
            value = value.replace(secret, "[REDACTED]")
        return SECRET_VALUE.sub("[REDACTED]", value)
    return value


def copy_verified(source: Path, destination: Path) -> dict:
    """No implicit destination creation: a misspelled cloud path must fail visibly."""
    if not destination.is_dir():
        raise ValueError("configured_debug_destination_unavailable")
    data = source.read_bytes()
    target = destination / source.name
    try:
        durable_bytes(target, data, exclusive=True)
    except FileExistsError:
        if target.read_bytes() != data:
            raise ValueError("immutable_debug_destination_conflict") from None
    observed = target.read_bytes()
    if len(observed) != len(data) or sha256_bytes(observed) != sha256_bytes(data):
        raise ValueError("debug_destination_verification_failed")
    receipt = {"status": "LOCAL_COPY_HASH_VERIFIED", "file": source.name,
               "bytes": len(data), "sha256": sha256_bytes(data),
               "remote_sync": "NOT_VERIFIED"}
    durable_json(destination / (source.name + ".copy-receipt.json"), receipt)
    return receipt


def seal_failure_bundle(directory: Path, summary: dict, *, secrets: tuple[str, ...] = ()) -> Path:
    safe = sanitized(summary, secrets)
    report = ("# Monitoring Operational Failure\n\n"
              "No retry or investment decision is implied by this report.\n\n"
              f"Run: {safe['run_id']}\n\nStage: {safe['failed_stage']}\n\n"
              "Data policy: QUERY_TIME_SNAPSHOT; finality_claim=NOT_CLAIMED.\n"
              "Raw payloads, prompts, credentials and recipient identifiers are not exported.\n"
              "Local upload receipt and ZIP SHA-256 are detached to avoid self-hash cycles.\n")
    files = {"REPORT.md": report.encode(), "summary.json": encoded(safe) + b"\n"}
    for name in ("transitions", "attempts", "stage_receipts", "error_chain"):
        files[name + ".json"] = encoded(safe.get(name, [])) + b"\n"
    combined = b"\n".join(files.values())
    if any(s.encode() in combined for s in secrets if s) or SECRET_VALUE.search(combined.decode()):
        raise ValueError("debug_secret_scan_failed")
    files["secret-scan.json"] = encoded({"status": "PASS", "scope": "exported_sanitized_files",
                                         "raw_source_payloads_included": False})
    files["manifest.json"] = encoded({name: {"bytes": len(data), "sha256": sha256_bytes(data)}
                                      for name, data in sorted(files.items())})
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary_name = tempfile.mkstemp(dir=directory, prefix=".bundle-")
    os.close(fd)
    temporary = Path(temporary_name)
    path = directory / f"{summary['run_id']}-debug.zip"
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as bundle:
            for name, data in sorted(files.items()):
                bundle.writestr(name, data)
        durable_bytes(path, temporary.read_bytes(), exclusive=True)
        durable_bytes(path.with_suffix(".zip.sha256"),
                      f"{sha256_bytes(path.read_bytes())}  {path.name}\n".encode(), exclusive=True)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def load_json(path: Path) -> dict:
    return json.loads(path.read_bytes())
