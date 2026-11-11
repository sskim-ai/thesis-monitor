"""Production input denial composed ahead of the byte-frozen CLI executors.

This boundary grants no source or execution authority. The frozen executor still
validates the executable, binding, policy, input hashes and exclusive outputs.
"""
import hashlib
import json

from app.services.fixture_context_authority import reject_test_only_production
from app.services.official_codex_shadow_transport_service import OfficialShadowError, _require


CONTRACT = "official-transport-input-preflight-v1"
PREFLIGHT_REJECT_EXIT = 65


def _unique_schema_object(pairs):
    value = {}
    for key, item in pairs:
        _require(key not in value, "INPUT_ENCODING_OR_SCHEMA_INVALID")
        value[key] = item
    return value


def preflight_official_input(*, prompt, schema, cwd, request):
    """Reject fixture content before credential/worker/output side effects."""
    request.execution_policy.validate()
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
    prompt_bytes, schema_bytes = prompt.read_bytes(), schema.read_bytes()
    _require(hashlib.sha256(prompt_bytes).hexdigest() == request.prompt_sha256, "PROMPT_DRIFT")
    _require(hashlib.sha256(schema_bytes).hexdigest() == request.schema_sha256, "SCHEMA_DRIFT")
    try:
        prompt_text = prompt_bytes.decode("utf-8", errors="strict")
        schema_value = json.loads(schema_bytes, object_pairs_hook=_unique_schema_object)
        _require(isinstance(schema_value, dict), "SCHEMA_INVALID")
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise OfficialShadowError("INPUT_ENCODING_OR_SCHEMA_INVALID") from exc
    reject_test_only_production({"prompt": prompt_text, "response_schema": schema_value})
