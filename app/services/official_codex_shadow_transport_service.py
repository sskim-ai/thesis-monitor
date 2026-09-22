"""Opt-in official CLI transport; no credential provisioning or remote preflight.

Bindings are local review receipts, not authentication or isolation certificates.
This module is deliberately absent from production's default invocation path.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_VERSION = "codex-cli 0.155.1"
RELEASE_TAG = "rust-v0.155.1"
PACKAGE_SHA256 = "e6e08717da9e35b72332eff753527fe79a9ae876081033c5c6820a8e5f58b943"
CHECKSUM_MANIFEST_SHA256 = "e7c267fa8cda3fb783be8380ef9c2b660ceea740426bbae17ac1df8cd1012937"
CONFIG_SCHEMA_SHA256 = "786fee5181619dc73963f7544fa6afe8364236392d999df92d3dd6b3a8c8ac70"
QUALIFICATION_CONTRACT = "official-codex-install-qualification-v1"
CONTRACT = "official-codex-shadow-transport-v1"
CONFIG_CONTROLS = (
    'model_reasoning_effort="xhigh"',
    'model_provider="openai"',
    'web_search="disabled"',
    "features.shell_tool=false",
    "features.unified_exec=false",
    "agents.enabled=false",
    "features.multi_agent_v2=false",
    "memories.use_memories=false",
    "memories.generate_memories=false",
    "allow_login_shell=false",
    "project_doc_max_bytes=0",
)
COMMAND_PREFIX = (
    "exec",
    "--ephemeral",
    "--skip-git-repo-check",
    "--sandbox",
    "read-only",
    "--ignore-user-config",
    "--ignore-rules",
    "--json",
    "-m",
    "gpt-5.6-sol",
    *(argument for control in CONFIG_CONTROLS for argument in ("-c", control)),
)
OVERRIDE_VARIABLES = (
    "OPENAI_API_KEY",
    "CODEX_API_KEY",
    "CODEX_ACCESS_TOKEN",
    "OPENAI_BASE_URL",
    "OPENAI_FEDERATION_RULE_ID",
    "OPENAI_IDENTITY_TOKEN_FILE",
    "OPENAI_WORKLOAD_IDENTITY_CONTEXT",
    "CODEX_CLI_BIN",
)


class OfficialShadowError(ValueError):
    def __init__(self, code: str, *, process_started: bool = False) -> None:
        self.code = code
        self.process_started = process_started
        super().__init__(code)


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise OfficialShadowError(code)


def file_sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


@dataclass(frozen=True)
class OfficialCodexBinding:
    executable: Path
    executable_sha256: str
    version: str
    auth_method: str
    home: str
    codex_home: str | None
    user_config_sha256: str | None
    installation_verified: bool = False
    qualification_path: Path | None = None
    qualification_sha256: str | None = None


@dataclass(frozen=True)
class OfficialShadowRequest:
    binding: OfficialCodexBinding
    request_id: str
    prompt_sha256: str
    schema_sha256: str


def validate_binding(binding: OfficialCodexBinding, codex_bin: str) -> None:
    path = binding.executable
    _require(path.is_absolute() and str(path) == codex_bin, "OFFICIAL_EXECUTABLE_MISMATCH")
    _require(binding.installation_verified, "OFFICIAL_INSTALLATION_UNVERIFIED")
    _require(
        path.is_file()
        and path.resolve() == path
        and os.access(path, os.X_OK)
        and path.stat().st_uid == os.getuid()
        and not path.stat().st_mode & stat.S_IWOTH,
        "OFFICIAL_INSTALLATION_UNVERIFIED",
    )
    _require(file_sha256(path) == binding.executable_sha256, "OFFICIAL_EXECUTABLE_DRIFT")
    _require(binding.version == SUPPORTED_VERSION, "OFFICIAL_OPTIONS_REVIEW_REQUIRED")
    qualification = binding.qualification_path
    _require(
        qualification is not None
        and qualification.is_absolute()
        and qualification.is_file()
        and qualification.resolve() == qualification,
        "OFFICIAL_QUALIFICATION_MISSING",
    )
    _require(
        file_sha256(qualification) == binding.qualification_sha256,
        "OFFICIAL_QUALIFICATION_DRIFT",
    )
    try:
        receipt = json.loads(qualification.read_bytes())
    except (ValueError, UnicodeError) as exc:
        raise OfficialShadowError("OFFICIAL_QUALIFICATION_INVALID") from exc
    _require(isinstance(receipt, dict), "OFFICIAL_QUALIFICATION_INVALID")
    _require(
        receipt.get("contract") == QUALIFICATION_CONTRACT
        and receipt.get("release_tag") == RELEASE_TAG
        and receipt.get("package_sha256") == PACKAGE_SHA256
        and receipt.get("checksum_manifest_sha256") == CHECKSUM_MANIFEST_SHA256
        and receipt.get("provenance_status") == "PASS",
        "OFFICIAL_PROVENANCE_UNVERIFIED",
    )
    _require(
        receipt.get("executable") == str(path)
        and receipt.get("executable_sha256") == binding.executable_sha256
        and receipt.get("version") == binding.version
        and isinstance(receipt.get("standalone_root"), str)
        and path
        == Path(receipt["standalone_root"]) / "releases/0.155.1-aarch64-apple-darwin/bin/codex",
        "OFFICIAL_EXECUTABLE_MISMATCH",
    )
    _require(
        receipt.get("config_schema_sha256") == CONFIG_SCHEMA_SHA256
        and receipt.get("command_prefix") == list(COMMAND_PREFIX)
        and receipt.get("required_tail_flags") == ["--output-schema", "-o", "-"],
        "OFFICIAL_REQUIRED_CONTROL_UNVERIFIED",
    )
    _require(
        not any(os.environ.get(key) for key in OVERRIDE_VARIABLES),
        "AUTH_OR_PROVIDER_OVERRIDE_PRESENT",
    )
    _require(
        binding.auth_method == "CHATGPT_LOCAL_CONFIRMED"
        and receipt.get("auth_status") == "CHATGPT_AUTH_CONFIRMED",
        "CHATGPT_AUTH_UNVERIFIED",
    )
    _require(
        os.environ.get("HOME") == binding.home
        and os.environ.get("CODEX_HOME") == binding.codex_home,
        "CREDENTIAL_STORE_DRIFT",
    )
    # The verified argv ignores user config; managed requirements remain CLI-owned.
    _require(binding.user_config_sha256 is None, "USER_CONFIG_MUST_BE_IGNORED")


def classify_input_events(events: bytes) -> dict[str, object]:
    """Conservative telemetry classification, never proof of source-only inference."""
    count = 0
    started = completed = False
    unknown = False
    outside = False
    safe_items = {"agent_message", "reasoning"}
    tool_items = {
        "command_execution",
        "mcp_tool_call",
        "web_search",
        "file_change",
        "image_view",
        "collab_tool_call",
    }
    for line in events.splitlines():
        try:
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError
        except (ValueError, UnicodeError):
            unknown = True
            continue
        count += 1
        kind = event.get("type")
        started |= kind == "thread.started"
        completed |= kind == "turn.completed"
        if kind in {"item.started", "item.updated", "item.completed"}:
            item = event.get("item")
            item_type = item.get("type") if isinstance(item, dict) else None
            outside |= item_type in tool_items
            unknown |= item_type not in safe_items | tool_items
        elif kind not in {"thread.started", "turn.started", "turn.completed"}:
            unknown = True
    state = "DECLARED_INPUT_WITH_DOCUMENTED_RUNTIME_LIMITS"
    if unknown or not (started and completed):
        state = "INPUT_BOUNDARY_UNVERIFIED"
    if outside:
        state = "UNDECLARED_INPUT_OBSERVED"
    return {"state": state, "event_count": count, "source_only_inference_certified": False}


def invoke_official_shadow(
    *,
    codex_bin: str,
    prompt: Path,
    output: Path,
    log: Path,
    schema: Path,
    cwd: Path,
    timeout: int,
    state_namespace: str,
    request: OfficialShadowRequest,
) -> dict[str, object]:
    validate_binding(request.binding, codex_bin)
    _require(
        timeout == 1200 and state_namespace == request.request_id, "REQUEST_ID_OR_TIMEOUT_DRIFT"
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
        "contract": CONTRACT,
        "request_id": request.request_id,
        "transport_attempts": 1,
        "network_probe_attempts": 0,
        "retry_recovered": False,
        "provider_attempts": "UNOBSERVABLE_CLI_INTERNAL",
        "source_only_inference_certified": False,
        "qualification_sha256": request.binding.qualification_sha256,
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
