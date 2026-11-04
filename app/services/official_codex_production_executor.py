"""Production executor preserving the byte-frozen historical shadow transport.

The historical module stays immutable. Body parity is independently tested;
production authorization remains outside the model-visible input.
"""
import hashlib
import json
import subprocess
from dataclasses import asdict

from app.services.official_codex_shadow_transport_service import (
    COMMAND_PREFIX, OfficialShadowError, _require, validate_binding,
    file_sha256, classify_input_events,
)


def invoke_official_bound(*, codex_bin, prompt, output, log, schema, cwd, timeout,
                          state_namespace, request, receipt_contract):
    """Execute only a separately authorized production request."""
    validate_binding(request.binding, codex_bin)
    request.execution_policy.validate()
    _require(
        type(timeout) is int
        and timeout == request.execution_policy.timeout_seconds
        and state_namespace == request.request_id,
        "REQUEST_ID_OR_TIMEOUT_DRIFT",
    )
    _require(cwd.is_absolute() and cwd.is_dir() and not cwd.is_symlink(), "INPUT_CWD_INVALID")
    _require(
        not any((parent / ".git").exists() for parent in (cwd, *cwd.parents)),
        "INPUT_CWD_INSIDE_REPOSITORY",
    )
    _require(
        prompt == cwd / "prompt.txt" and schema == cwd / "provider-wire-schema.json",
        "REQUEST_INPUT_LAYOUT_INVALID",
    )
    _require(
        set(cwd.iterdir()) == {prompt, schema}
        and all(path.is_file() and not path.is_symlink() for path in (prompt, schema)),
        "UNDECLARED_INPUT_PRESENT",
    )
    prompt_bytes = prompt.read_bytes()
    schema_bytes = schema.read_bytes()
    _require(hashlib.sha256(prompt_bytes).hexdigest() == request.prompt_sha256, "PROMPT_DRIFT")
    _require(hashlib.sha256(schema_bytes).hexdigest() == request.schema_sha256, "SCHEMA_DRIFT")
    try:
        prompt_bytes.decode("utf-8", errors="strict")
        _require(isinstance(json.loads(schema_bytes), dict), "SCHEMA_INVALID")
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise OfficialShadowError("INPUT_ENCODING_OR_SCHEMA_INVALID") from exc
    stderr = log.with_name(log.name + ".stderr")
    claim = output.with_name(output.name + ".invocation")
    paths = (output, log, stderr, claim)
    _require(
        len(set(paths)) == 4
        and all(
            path.is_absolute()
            and path.parent == cwd.parent
            and not path.exists()
            and not path.is_symlink()
            for path in paths
        ),
        "OUTPUT_NOT_EXCLUSIVE",
    )
    command = [
        codex_bin,
        *COMMAND_PREFIX,
        "--output-schema",
        str(schema),
        "-o",
        str(output),
        "-",
    ]
    # The exclusive claim survives failure: the same request directory cannot be retried.
    try:
        with claim.open("x", encoding="utf-8") as stream:
            stream.write(request.request_id)
    except FileExistsError as exc:
        raise OfficialShadowError("OUTPUT_NOT_EXCLUSIVE") from exc
    receipt: dict[str, object] = {
        "contract": receipt_contract,
        "request_id": request.request_id,
        "transport_attempts": 1,
        "network_probe_attempts": 0,
        "retry_recovered": False,
        "provider_attempts": "UNOBSERVABLE_CLI_INTERNAL",
        "source_only_inference_certified": False,
        "qualification_sha256": request.binding.qualification_sha256,
        "execution_policy": asdict(request.execution_policy),
        "invocation_identity_sha256": hashlib.sha256(
            json.dumps(
                {
                    "argv": command,
                    "request_id": request.request_id,
                    "prompt_sha256": request.prompt_sha256,
                    "schema_sha256": request.schema_sha256,
                    "executable_sha256": request.binding.executable_sha256,
                    "qualification_sha256": request.binding.qualification_sha256,
                    "timeout": timeout,
                    "execution_policy": asdict(request.execution_policy),
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest(),
    }
    try:
        with log.open("xb") as events, stderr.open("xb") as errors:
            process = subprocess.run(
                command,
                cwd=cwd,
                input=prompt_bytes,
                stdout=events,
                stderr=errors,
                timeout=timeout,
                check=False,
            )
    except subprocess.TimeoutExpired as exc:
        raise OfficialShadowError("TRANSPORT_TIMEOUT", process_started=True) from exc
    except OSError as exc:
        raise OfficialShadowError("PROCESS_START_FAILED") from exc
    if process.returncode != 0:
        raise OfficialShadowError("PROCESS_NONZERO", process_started=True)
    if file_sha256(prompt) != request.prompt_sha256 or file_sha256(schema) != request.schema_sha256:
        raise OfficialShadowError("INPUT_CHANGED_DURING_INVOCATION", process_started=True)
    if not output.is_file() or output.is_symlink() or not output.stat().st_size:
        raise OfficialShadowError("FINAL_OUTPUT_EMPTY", process_started=True)
    try:
        final = json.loads(output.read_bytes())
        if not isinstance(final, dict):
            raise ValueError
    except (ValueError, UnicodeError) as exc:
        raise OfficialShadowError("FINAL_OUTPUT_MALFORMED", process_started=True) from exc
    receipt["input_boundary"] = classify_input_events(log.read_bytes())
    if receipt["input_boundary"]["state"] != "DECLARED_INPUT_WITH_DOCUMENTED_RUNTIME_LIMITS":
        raise OfficialShadowError(receipt["input_boundary"]["state"], process_started=True)
    return receipt
