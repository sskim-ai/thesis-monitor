"""Explicit frozen controller -> native inspector binding; never a live CLI route."""

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

POLICY = "m12dc-packet-only-offline-integration-v1"
APPROVAL_CONTRACT = "m12dc-offline-inspector-approval-v1"
MODEL = "gpt-5.6-sol"
MAX_INPUT = 1_048_576
MAX_RECEIPT = 2_097_152


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def load_json(data: bytes | str) -> object:
    def pairs(items: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in items:
            require(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result

    def invalid_constant(_: str) -> None:
        raise ValueError("NONFINITE_JSON")

    return json.loads(data, object_pairs_hook=pairs, parse_constant=invalid_constant)


def bound_file(record: dict) -> bytes:
    p = Path(record["path"])
    require(p.is_absolute() and p.is_file() and not p.is_symlink(), "BOUND_FILE_PATH")
    data = p.read_bytes()
    require(digest(data) == record["sha256"], "BOUND_FILE_DRIFT")
    return data


def split_source(prompt: str, context: dict, schema: dict, stage: str) -> tuple[str, str]:
    """The archived source builder owns this separator; evidence never becomes developer text."""
    marker = "\n\nSUBJECT_KEYS:\n"
    require(prompt.count(marker) == 1, "SOURCE_PROMPT_LAYOUT")
    task, rest = prompt.split(marker)
    label = f"\n\nPASS_{stage}_CONTEXT:\n"
    require(rest.count(label) == 1, "SOURCE_CONTEXT_LAYOUT")
    keys, payload = rest.split(label)
    subjects = context["subjects"]
    require(load_json(payload) == subjects, "SOURCE_CONTEXT_NOT_EQUIVALENT")
    expected = [subject["ticker"] for subject in subjects]
    require(load_json(keys) == expected, "SOURCE_SUBJECT_KEYS_DRIFT")
    require(stage in ("A", "B"), "SOURCE_STAGE_UNSUPPORTED")
    wrapper = "classifications" if stage == "A" else "decisions"
    require(set(schema["properties"]) == {wrapper}, "SOURCE_SCHEMA_WRAPPER_DRIFT")
    require(
        set(schema["properties"][wrapper]["properties"]) == set(expected),
        "SOURCE_SCHEMA_SUBJECT_DRIFT",
    )
    return task, marker + rest


def verify_receipt(receipt: dict, frozen: dict, input_bytes: bytes, base: str) -> dict:
    for field, expected in {
        "policy": POLICY,
        "invocation_id": frozen["invocation_id"],
        "approved_input_sha256": digest(input_bytes),
        "executable_sha256": frozen["executable_sha256"],
        "model": MODEL,
        "effort": "xhigh",
        "source_manifest_sha256": frozen["source_manifest_sha256"],
        "source_prompt_sha256": frozen["source_prompt_sha256"],
        "static_context_sha256": digest(base.encode()),
        "task_sha256": digest(frozen["task_instructions"].encode()),
        "evidence_sha256": digest(frozen["evidence"].encode()),
        "schema_sha256": digest(canonical(frozen["output_schema"])),
        "auth_access": "NOT_ATTEMPTED",
        "managed_live_policy": "UNRESOLVED_LIVE_BLOCKED",
        "registered_dispatch_handlers": [],
        "host_context_discovery": "NOT_STARTED",
        "gate": "OFFLINE_INSPECT_AND_STOP",
        "transport_stop_code": "PACKET_ONLY_OFFLINE_NO_TRANSPORT",
    }.items():
        require(receipt.get(field) == expected, f"RECEIPT_MISMATCH:{field}")
    require(receipt.get("model_transport_attempted") is False, "TRANSPORT_STATE_MISMATCH")
    require(receipt.get("execution_authorized") is False, "EXECUTION_STATE_MISMATCH")
    managed = receipt.get("managed_composition", {})
    require(
        managed.get("state") == "ABSENT_IN_EXPLICIT_SYNTHETIC_INPUT_NOT_LIVE_ABSENCE"
        and managed.get("layers") == []
        and managed.get("scope") == "SYNTHETIC_CONFIG_ONLY_LIVE_UNRESOLVED"
        and managed.get("live_policy") == "UNRESOLVED_LIVE_BLOCKED",
        "MANAGED_SCOPE_MISMATCH",
    )
    body_bytes = receipt["final_request_body"].encode()
    require(len(body_bytes) <= MAX_INPUT, "RETURNED_BODY_OVERSIZE")
    require(digest(body_bytes) == receipt.get("final_request_sha256"), "RETURNED_BODY_HASH")
    body = load_json(body_bytes)
    require(
        set(body)
        == {
            "client_metadata",
            "include",
            "input",
            "model",
            "parallel_tool_calls",
            "prompt_cache_key",
            "reasoning",
            "store",
            "stream",
            "text",
            "tool_choice",
        },
        "BODY_FIELDS_DRIFT",
    )
    invocation = frozen["invocation_id"]
    require(
        body["client_metadata"]
        == {
            "session_id": invocation,
            "thread_id": invocation,
            "x-codex-installation-id": POLICY,
            "x-codex-window-id": invocation,
        }
        and body["prompt_cache_key"] == invocation,
        "BODY_INVOCATION_DRIFT",
    )
    require(
        body["store"] is False and body["parallel_tool_calls"] is False, "BODY_EXECUTION_OPTIONS"
    )
    require(body["model"] == MODEL and body["reasoning"]["effort"] == "xhigh", "BODY_MODEL")
    require(body.get("tools") in (None, []), "BODY_TOOLS")
    require(body["text"]["format"]["schema"] == frozen["output_schema"], "BODY_SCHEMA")
    require(body["text"]["format"]["strict"] is True, "BODY_SCHEMA_NOT_STRICT")
    messages = []
    embedded = []
    for item in body["input"]:
        if item["type"] == "additional_tools":
            require(item["role"] == "developer" and item["tools"] == [], "EMBEDDED_TOOLS")
            embedded.append(item)
            continue
        require(item["type"] == "message", "BODY_CONTEXT_HANDLE")
        require(len(item["content"]) == 1, "BODY_ATTACHMENT")
        content = item["content"][0]
        require(content["type"] == "input_text", "BODY_ATTACHMENT")
        messages.append((item["role"], content["text"]))
    # This pinned model uses Responses Lite. No generic role rewriting is allowed.
    # ResponsesApiRequest omits an empty instructions string during serialization.
    require("instructions" not in body and len(embedded) == 1, "BODY_BOOTSTRAP_SHAPE")
    require(
        messages
        == [
            ("developer", base),
            ("developer", frozen["task_instructions"]),
            ("user", frozen["evidence"]),
        ],
        "BODY_ROLE_OR_CONTENT_DRIFT",
    )
    return {"request_bytes": len(body_bytes), "request_sha256": digest(body_bytes)}


def load_approval(approval_path: Path, approved_sha256: str) -> tuple[dict, list[tuple]]:
    raw = approval_path.read_bytes()
    require(digest(raw) == approved_sha256, "APPROVAL_DRIFT")
    approval = load_json(raw)
    require(approval["contract"] == APPROVAL_CONTRACT, "APPROVAL_CONTRACT")
    require(approval["operation"] == "inspect" and approval["policy"] == POLICY, "OPERATION_DENIED")
    require(approval["model"] == MODEL and approval["effort"] == "xhigh", "MODEL_OR_EFFORT")
    source_raw = bound_file(approval["source_manifest"])
    source = load_json(source_raw)
    base = bound_file(approval["base_instructions"]).decode()
    bound_file(approval["executable"])
    bound_file(source["catalog"])
    for owner in source["task_owner_sources"].values():
        bound_file(owner)
    require(len(approval["requests"]) == len(source["fixtures"]) == 16, "FIXTURE_COHORT")
    expected_ids = [
        f"{stage}/{market}/batch-{batch:02d}"
        for stage in ("A", "B")
        for market, count in (("kr", 3), ("us", 5))
        for batch in range(1, count + 1)
    ]
    require(
        [row["id"] for row in approval["requests"]]
        == [row["id"] for row in source["fixtures"]]
        == expected_ids,
        "FIXTURE_ORDER",
    )
    require(
        len({row["invocation_id"] for row in approval["requests"]}) == 16, "INVOCATION_ID_REUSED"
    )
    prepared = []
    for row, fixture in zip(approval["requests"], source["fixtures"], strict=True):
        original = bound_file(fixture["prompt"]).decode()
        context = load_json(bound_file(fixture["context"]))
        schema = load_json(bound_file(fixture["schema"]))
        task, evidence = split_source(original, context, schema, fixture["stage"])
        require(
            digest(task.encode()) == source["task_owners"][fixture["stage"]], "TASK_OWNER_DRIFT"
        )
        raw_input = bound_file(row["input"])
        require(len(raw_input) <= MAX_INPUT, "INPUT_OVERSIZE")
        frozen = load_json(raw_input)
        expected = {
            "policy": POLICY,
            "operation": "inspect",
            "invocation_id": row["invocation_id"],
            "model": MODEL,
            "effort": "xhigh",
            "executable_sha256": approval["executable"]["sha256"],
            "source_manifest_sha256": digest(source_raw),
            "source_prompt_sha256": digest(original.encode()),
            "base_instructions_sha256": digest(base.encode()),
            "task_instructions": task,
            "evidence": evidence,
            "output_schema": schema,
            "managed_fixture": {"scope": "SYNTHETIC_CONFIG_ONLY_LIVE_UNRESOLVED", "layers": []},
        }
        require(frozen == expected, "INPUT_SOURCE_OR_POLICY_DRIFT")
        prepared.append((row, frozen, raw_input, base))
    return approval, prepared


def inspect_approval(approval_path: Path, approved_sha256: str, output: Path) -> dict:
    """No retries, fallback CLI, provider selection, or authentication entrypoint."""
    approval, prepared = load_approval(approval_path, approved_sha256)
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for row, frozen, raw_input, base in prepared:
        binary = approval["executable"]
        bound_file(binary)
        directory = output / row["id"]
        directory.mkdir(parents=True)
        try:
            with tempfile.TemporaryDirectory(prefix="packet-only-offline-") as empty_home:
                completed = subprocess.run(
                    [binary["path"], "--approved-input-sha256", digest(raw_input)],
                    input=raw_input,
                    capture_output=True,
                    cwd=empty_home,
                    env={
                        "HOME": empty_home,
                        "TMPDIR": empty_home,
                        "PATH": "/usr/bin:/bin",
                        "LANG": "C.UTF-8",
                    },
                    timeout=30,
                    check=False,
                )
        except (subprocess.TimeoutExpired, OSError) as error:
            (directory / "stdout.json").write_bytes(getattr(error, "stdout", None) or b"")
            (directory / "stderr.txt").write_bytes(getattr(error, "stderr", None) or b"")
            (directory / "process.json").write_bytes(
                canonical(
                    {
                        "status": "FAILED_NO_RETRY",
                        "error_type": type(error).__name__,
                        "invocation_id": row["invocation_id"],
                        "input_sha256": digest(raw_input),
                    }
                )
            )
            raise
        # Keep success and failure bytes, even when receipt validation rejects.
        (directory / "stdout.json").write_bytes(completed.stdout)
        (directory / "stderr.txt").write_bytes(completed.stderr)
        (directory / "process.json").write_bytes(
            canonical(
                {
                    "returncode": completed.returncode,
                    "invocation_id": row["invocation_id"],
                    "input_sha256": digest(raw_input),
                    "executable_sha256": binary["sha256"],
                }
            )
        )
        require(completed.returncode == 0, "NATIVE_INSPECTOR_REJECTED")
        require(0 < len(completed.stdout) <= MAX_RECEIPT, "RECEIPT_MISSING_OR_OVERSIZE")
        bound_file(binary)
        receipt = load_json(completed.stdout)
        checked = verify_receipt(receipt, frozen, raw_input, base)
        results.append(
            {
                "id": row["id"],
                "invocation_id": row["invocation_id"],
                "input_sha256": digest(raw_input),
                **checked,
                "status": "PASS",
            }
        )
    result = {
        "status": "OFFLINE_CONTROLLER_NATIVE_INSPECTION_PASS",
        "approved_manifest_sha256": approved_sha256,
        "fixtures": results,
        "fixture_count": len(results),
        "model_calls": 0,
        "auth_access": "NOT_ATTEMPTED",
        "transport": "PACKET_ONLY_OFFLINE_NO_TRANSPORT",
        "live_managed_policy": "UNRESOLVED_LIVE_BLOCKED",
        "fresh_ab_ready": False,
    }
    (output / "result.json").write_bytes(canonical(result) + b"\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--approved-approval-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = inspect_approval(args.approval, args.approved_approval_sha256, args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
