from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


IDENTITY_MARKER = "IDENTITY:\n"
IDENTITY_PLACEHOLDER = "__RUNTIME_PACKET_ID__"


class PreSpawnRuntimeIdentityBindingMismatch(RuntimeError):
    """Raised before transport when the concrete request is not identity-consistent."""


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha256(path: Path) -> str:
    return bytes_sha256(path.read_bytes())


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def prompt_identity(text: str) -> dict[str, Any]:
    if IDENTITY_MARKER not in text:
        raise ValueError("prompt_identity_marker_missing")
    identity_line = text.split(IDENTITY_MARKER, 1)[1].splitlines()[0]
    identity = json.loads(identity_line)
    if not isinstance(identity, dict):
        raise ValueError("prompt_identity_object_required")
    return identity


def _replace_prompt_identity(text: str, identity: Mapping[str, object]) -> str:
    before, after = text.split(IDENTITY_MARKER, 1)
    _old_line, separator, remainder = after.partition("\n")
    line = json.dumps(identity, ensure_ascii=False, separators=(",", ":"))
    return before + IDENTITY_MARKER + line + (separator + remainder if separator else "")


def normalized_prompt_semantic_hash(text: str) -> str:
    identity = prompt_identity(text)
    identity["packet_id"] = IDENTITY_PLACEHOLDER
    return bytes_sha256(_replace_prompt_identity(text, identity).encode("utf-8"))


def normalized_schema_semantic_hash(schema: Mapping[str, object]) -> str:
    normalized = json.loads(json.dumps(schema))
    properties = normalized.get("properties")
    if not isinstance(properties, dict):
        raise ValueError("schema_properties_missing")
    packet_id = properties.get("packet_id")
    if not isinstance(packet_id, dict) or "const" not in packet_id:
        raise ValueError("schema_packet_id_const_missing")
    packet_id["const"] = IDENTITY_PLACEHOLDER
    return canonical_sha256(normalized)


def schema_contract(schema: Mapping[str, object]) -> str | None:
    properties = schema.get("properties")
    contract = properties.get("contract") if isinstance(properties, Mapping) else None
    return str(contract.get("const")) if isinstance(contract, Mapping) else None


def schema_packet_id(schema: Mapping[str, object]) -> str | None:
    properties = schema.get("properties")
    packet = properties.get("packet_id") if isinstance(properties, Mapping) else None
    return str(packet.get("const")) if isinstance(packet, Mapping) else None


def schema_subjects(schema: Mapping[str, object]) -> tuple[str, ...]:
    properties = schema.get("properties")
    candidates = properties.get("candidates") if isinstance(properties, Mapping) else None
    items = candidates.get("items") if isinstance(candidates, Mapping) else None
    alternatives = items.get("anyOf") if isinstance(items, Mapping) else None
    if not isinstance(alternatives, list):
        raise ValueError("schema_candidate_subject_constraints_missing")
    result: list[str] = []
    for candidate in alternatives:
        candidate_properties = (
            candidate.get("properties") if isinstance(candidate, Mapping) else None
        )
        ticker = (
            candidate_properties.get("ticker")
            if isinstance(candidate_properties, Mapping)
            else None
        )
        if not isinstance(ticker, Mapping) or "const" not in ticker:
            raise ValueError("schema_candidate_ticker_const_missing")
        result.append(str(ticker["const"]))
    return tuple(result)


@dataclass(frozen=True)
class RuntimeIdentityBinding:
    source_generation_id: str
    runtime_generation_id: str
    source_lock_sha256: str
    run_id: str
    stage: str
    batch_id: str
    invocation_id: str
    ordered_subjects: tuple[str, ...]
    output_contract: str
    per_subject_packet_hashes: tuple[tuple[str, str], ...]

    def document(self) -> dict[str, object]:
        value = asdict(self)
        value["ordered_subjects"] = list(self.ordered_subjects)
        value["per_subject_packet_hashes"] = dict(self.per_subject_packet_hashes)
        return value

    @classmethod
    def from_document(cls, value: Mapping[str, object]) -> RuntimeIdentityBinding:
        packet_hashes = value.get("per_subject_packet_hashes")
        if not isinstance(packet_hashes, Mapping):
            raise ValueError("binding_packet_hashes_missing")
        return cls(
            source_generation_id=str(value["source_generation_id"]),
            runtime_generation_id=str(value["runtime_generation_id"]),
            source_lock_sha256=str(value["source_lock_sha256"]),
            run_id=str(value["run_id"]),
            stage=str(value["stage"]),
            batch_id=str(value["batch_id"]),
            invocation_id=str(value["invocation_id"]),
            ordered_subjects=tuple(str(item) for item in value["ordered_subjects"]),
            output_contract=str(value["output_contract"]),
            per_subject_packet_hashes=tuple(
                (str(key), str(item)) for key, item in packet_hashes.items()
            ),
        )


def load_binding(lock_path: Path) -> RuntimeIdentityBinding:
    lock = read_json(lock_path)
    binding = lock.get("binding")
    if not isinstance(binding, Mapping):
        raise ValueError("binding_object_missing")
    return RuntimeIdentityBinding.from_document(binding)


def bind_runtime_request(
    *,
    prompt_template: Path,
    schema_template: Path,
    runtime_prompt: Path,
    runtime_schema: Path,
    binding: RuntimeIdentityBinding,
    lock_path: Path,
) -> dict[str, object]:
    source_prompt_bytes = prompt_template.read_bytes()
    source_prompt_text = source_prompt_bytes.decode("utf-8")
    source_prompt_identity = prompt_identity(source_prompt_text)
    if source_prompt_identity.get("packet_id") not in {
        binding.source_generation_id,
        binding.runtime_generation_id,
    }:
        raise PreSpawnRuntimeIdentityBindingMismatch(
            "PRESPAWN_RUNTIME_IDENTITY_BINDING_MISMATCH:prompt_template_packet_id"
        )
    if source_prompt_identity.get("contract") != binding.output_contract:
        raise PreSpawnRuntimeIdentityBindingMismatch(
            "PRESPAWN_RUNTIME_IDENTITY_BINDING_MISMATCH:prompt_template_contract"
        )
    if tuple(str(value) for value in source_prompt_identity.get("tickers") or ()) != (
        binding.ordered_subjects
    ):
        raise PreSpawnRuntimeIdentityBindingMismatch(
            "PRESPAWN_RUNTIME_IDENTITY_BINDING_MISMATCH:prompt_template_subjects"
        )
    runtime_identity = dict(source_prompt_identity)
    runtime_identity["packet_id"] = binding.runtime_generation_id
    runtime_prompt_text = _replace_prompt_identity(source_prompt_text, runtime_identity)

    source_schema_bytes = schema_template.read_bytes()
    source_schema = json.loads(source_schema_bytes)
    if not isinstance(source_schema, dict):
        raise ValueError("schema_template_object_required")
    if schema_packet_id(source_schema) not in {
        binding.source_generation_id,
        binding.runtime_generation_id,
    }:
        raise PreSpawnRuntimeIdentityBindingMismatch(
            "PRESPAWN_RUNTIME_IDENTITY_BINDING_MISMATCH:schema_template_packet_id"
        )
    runtime_schema_value = json.loads(json.dumps(source_schema))
    runtime_schema_value["properties"]["packet_id"]["const"] = (
        binding.runtime_generation_id
    )

    source_prompt_semantic_hash = normalized_prompt_semantic_hash(source_prompt_text)
    runtime_prompt_semantic_hash = normalized_prompt_semantic_hash(runtime_prompt_text)
    source_schema_semantic_hash = normalized_schema_semantic_hash(source_schema)
    runtime_schema_semantic_hash = normalized_schema_semantic_hash(runtime_schema_value)
    if source_prompt_semantic_hash != runtime_prompt_semantic_hash:
        raise PreSpawnRuntimeIdentityBindingMismatch(
            "PRESPAWN_RUNTIME_IDENTITY_BINDING_MISMATCH:prompt_nonidentity_drift"
        )
    if source_schema_semantic_hash != runtime_schema_semantic_hash:
        raise PreSpawnRuntimeIdentityBindingMismatch(
            "PRESPAWN_RUNTIME_IDENTITY_BINDING_MISMATCH:schema_nonidentity_drift"
        )

    runtime_prompt.parent.mkdir(parents=True, exist_ok=True)
    runtime_prompt.write_text(runtime_prompt_text, encoding="utf-8")
    write_json(runtime_schema, runtime_schema_value)
    lock: dict[str, object] = {
        "contract": "runtime-identity-binding-lock-v1",
        "binding": binding.document(),
        "authorized_runtime_identity_binding_change": int(
            binding.source_generation_id != binding.runtime_generation_id
        ),
        "modified_fields": [
            "prompt.IDENTITY.packet_id",
            "schema./properties/packet_id/const",
        ],
        "source_prompt_sha256": bytes_sha256(source_prompt_bytes),
        "raw_runtime_prompt_sha256": file_sha256(runtime_prompt),
        "source_schema_sha256": bytes_sha256(source_schema_bytes),
        "raw_runtime_schema_sha256": file_sha256(runtime_schema),
        "identity_normalized_prompt_semantic_hash": runtime_prompt_semantic_hash,
        "identity_normalized_schema_semantic_hash": runtime_schema_semantic_hash,
        "source_prompt_identity_normalized_hash": source_prompt_semantic_hash,
        "source_schema_identity_normalized_hash": source_schema_semantic_hash,
        "decision_prompt_semantic_change": 0,
        "investment_schema_semantic_change": 0,
        "historical_source_artifact_mutation": 0,
    }
    lock["identity_binding_lock_hash"] = canonical_sha256(lock)
    write_json(lock_path, lock)
    return lock


def _source_lock_packet_hashes(path: Path) -> tuple[str, dict[str, str]]:
    source_lock = read_json(path)
    lock_hash = str(
        source_lock.get("source_lock_sha256")
        or source_lock.get("aggregate_source_lock_sha256")
        or ""
    )
    packets = source_lock.get("packet_sha256") or source_lock.get(
        "per_issuer_packet_hashes"
    )
    if not isinstance(packets, Mapping):
        raise ValueError("source_lock_packet_hashes_missing")
    return lock_hash, {str(key): str(value) for key, value in packets.items()}


def preflight_actual_request(
    *,
    prompt_path: Path,
    schema_path: Path,
    lock_path: Path,
    source_lock_path: Path,
    validator_expected_packet_id: str,
    adapter_generation_id: str,
    result_path: Path,
) -> dict[str, object]:
    errors: list[str] = []
    lock = read_json(lock_path)
    recorded_lock_hash = str(lock.get("identity_binding_lock_hash") or "")
    lock_without_hash = dict(lock)
    lock_without_hash.pop("identity_binding_lock_hash", None)
    if canonical_sha256(lock_without_hash) != recorded_lock_hash:
        errors.append("binding_lock_hash_mismatch")
    binding = lock.get("binding")
    if not isinstance(binding, Mapping):
        errors.append("binding_object_missing")
        binding = {}
    runtime_id = str(binding.get("runtime_generation_id") or "")
    expected_contract = str(binding.get("output_contract") or "")
    expected_subjects = tuple(str(value) for value in binding.get("ordered_subjects") or ())

    try:
        identity = prompt_identity(prompt_path.read_text(encoding="utf-8"))
    except Exception as exc:
        identity = {}
        errors.append(f"prompt_identity_invalid:{type(exc).__name__}")
    try:
        schema = read_json(schema_path)
        actual_schema_subjects = schema_subjects(schema)
    except Exception as exc:
        schema = {}
        actual_schema_subjects = ()
        errors.append(f"schema_invalid:{type(exc).__name__}")

    checks = {
        "prompt_packet_id": identity.get("packet_id") == runtime_id,
        "schema_packet_id_const": schema_packet_id(schema) == runtime_id,
        "validator_expected_packet_id": validator_expected_packet_id == runtime_id,
        "adapter_generation_id": adapter_generation_id == runtime_id,
        "prompt_contract": identity.get("contract") == expected_contract,
        "schema_contract": schema_contract(schema) == expected_contract,
        "prompt_subject_order": tuple(identity.get("tickers") or ()) == expected_subjects,
        "schema_subject_constraints": actual_schema_subjects == expected_subjects,
        "runtime_prompt_hash": file_sha256(prompt_path)
        == lock.get("raw_runtime_prompt_sha256"),
        "runtime_schema_hash": file_sha256(schema_path)
        == lock.get("raw_runtime_schema_sha256"),
    }
    errors.extend(name for name, passed in checks.items() if not passed)

    try:
        source_lock_hash, source_packet_hashes = _source_lock_packet_hashes(
            source_lock_path
        )
        expected_packet_hashes = {
            str(key): str(value)
            for key, value in (binding.get("per_subject_packet_hashes") or {}).items()
        }
        if source_lock_hash != binding.get("source_lock_sha256"):
            errors.append("source_lock_hash_mismatch")
        if {
            ticker: source_packet_hashes.get(ticker) for ticker in expected_subjects
        } != expected_packet_hashes:
            errors.append("per_subject_packet_hash_mismatch")
    except Exception as exc:
        errors.append(f"source_lock_invalid:{type(exc).__name__}")

    result = {
        "contract": "actual-adapter-request-identity-preflight-v1",
        "runtime_generation_id": runtime_id,
        "run_id": binding.get("run_id"),
        "stage": binding.get("stage"),
        "batch_id": binding.get("batch_id"),
        "invocation_id": binding.get("invocation_id"),
        "ordered_subjects": list(expected_subjects),
        "identity_binding_lock_hash": recorded_lock_hash,
        "checks": checks,
        "errors": errors,
        "spawn_started": 0,
        "transport_receipt_expected": 0,
        "real_model_invocations": 0,
        "status": "PASS" if not errors else "FAIL",
    }
    write_json(result_path, result)
    if errors:
        error = PreSpawnRuntimeIdentityBindingMismatch(
            "PRESPAWN_RUNTIME_IDENTITY_BINDING_MISMATCH:" + ",".join(errors)
        )
        setattr(
            error,
            "transport_lifecycle",
            {
                "failure_stage": "PRE_SPAWN_IDENTITY_GATE",
                "spawn_started": 0,
                "transport_receipt_expected": 0,
                "transport_receipt_created": 0,
                "root_exception_masked": 0,
            },
        )
        raise error
    return result


def validate_receipt_identity(
    receipt: Mapping[str, object], binding: RuntimeIdentityBinding
) -> dict[str, object]:
    expected = {
        "generation_id": binding.runtime_generation_id,
        "invocation_id": binding.invocation_id,
        "stage": binding.stage,
        "batch_id": binding.batch_id,
        "subject_count": len(binding.ordered_subjects),
    }
    mismatches = {
        key: {"expected": expected_value, "actual": receipt.get(key)}
        for key, expected_value in expected.items()
        if receipt.get(key) != expected_value
    }
    return {
        "contract": "transport-receipt-identity-validation-v1",
        "expected": expected,
        "mismatches": mismatches,
        "status": "PASS" if not mismatches else "FAIL",
    }


def validate_output_identity(
    output: Mapping[str, object], binding: RuntimeIdentityBinding
) -> dict[str, object]:
    checks = {
        "contract": output.get("contract") == binding.output_contract,
        "packet_id": output.get("packet_id") == binding.runtime_generation_id,
        "subject_order": tuple(
            str(row.get("ticker") or "")
            for row in output.get("candidates") or ()
            if isinstance(row, Mapping)
        )
        == binding.ordered_subjects,
    }
    return {
        "contract": "model-output-runtime-identity-validation-v1",
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def binding_from_state(
    *,
    state: Mapping[str, object],
    run: str,
    stage: str,
    batch_number: int,
    subjects: Sequence[str],
    output_contract: str,
) -> RuntimeIdentityBinding:
    runtime_id = str(state["program_generation_id"])
    source_id = str(state.get("source_generation_id") or runtime_id)
    packet_hashes = state.get("packet_hashes")
    if not isinstance(packet_hashes, Mapping):
        packet_hashes = {}
    batch_id = f"{batch_number:02d}"
    invocation_id = f"{runtime_id}:{run}:{stage}:{batch_id}"
    return RuntimeIdentityBinding(
        source_generation_id=source_id,
        runtime_generation_id=runtime_id,
        source_lock_sha256=str(state["source_lock_sha256"]),
        run_id=run,
        stage=stage,
        batch_id=batch_id,
        invocation_id=invocation_id,
        ordered_subjects=tuple(str(value) for value in subjects),
        output_contract=output_contract,
        per_subject_packet_hashes=tuple(
            (str(ticker), str(packet_hashes.get(str(ticker)) or ""))
            for ticker in subjects
        ),
    )
