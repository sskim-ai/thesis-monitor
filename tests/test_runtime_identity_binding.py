from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import runtime_identity_binding as identity


SOURCE_ID = "source-generation"
RUNTIME_ID = "runtime-generation"
SUBJECTS = ("SYNTHETIC_US_1", "SYNTHETIC_US_2")
CONTRACT = "directional-core-output-v1"


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _schema(packet_id: str = SOURCE_ID, contract: str = CONTRACT) -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "contract": {"const": contract, "type": "string"},
            "packet_id": {"const": packet_id, "type": "string"},
            "candidates": {
                "type": "array",
                "minItems": len(SUBJECTS),
                "maxItems": len(SUBJECTS),
                "items": {
                    "anyOf": [
                        {
                            "type": "object",
                            "properties": {
                                "ticker": {"const": ticker, "type": "string"}
                            },
                        }
                        for ticker in SUBJECTS
                    ]
                },
            },
        },
    }


def _prompt(packet_id: str = SOURCE_ID, contract: str = CONTRACT) -> str:
    document = {
        "contract": contract,
        "packet_id": packet_id,
        "tickers": list(SUBJECTS),
    }
    return (
        "Frozen investment instructions.\n\nIDENTITY:\n"
        + json.dumps(document, separators=(",", ":"))
        + "\n\nCONTEXT:\nunchanged evidence"
    )


def _binding(**changes: object) -> identity.RuntimeIdentityBinding:
    values = {
        "source_generation_id": SOURCE_ID,
        "runtime_generation_id": RUNTIME_ID,
        "source_lock_sha256": "source-lock",
        "run_id": "first",
        "stage": "DIRECTIONAL_CORE",
        "batch_id": "01",
        "invocation_id": f"{RUNTIME_ID}:first:DIRECTIONAL_CORE:01",
        "ordered_subjects": SUBJECTS,
        "output_contract": CONTRACT,
        "per_subject_packet_hashes": tuple((ticker, f"hash-{ticker}") for ticker in SUBJECTS),
    }
    values.update(changes)
    return identity.RuntimeIdentityBinding(**values)


def _prepared(tmp_path: Path) -> dict[str, Path]:
    paths = {
        "source_prompt": tmp_path / "source-prompt.txt",
        "source_schema": tmp_path / "source-schema.json",
        "runtime_prompt": tmp_path / "runtime-prompt.txt",
        "runtime_schema": tmp_path / "runtime-schema.json",
        "lock": tmp_path / "binding-lock.json",
        "source_lock": tmp_path / "source-lock.json",
        "preflight": tmp_path / "preflight.json",
    }
    paths["source_prompt"].write_text(_prompt(), encoding="utf-8")
    _write_json(paths["source_schema"], _schema())
    _write_json(
        paths["source_lock"],
        {
            "source_lock_sha256": "source-lock",
            "packet_sha256": {ticker: f"hash-{ticker}" for ticker in SUBJECTS},
        },
    )
    identity.bind_runtime_request(
        prompt_template=paths["source_prompt"],
        schema_template=paths["source_schema"],
        runtime_prompt=paths["runtime_prompt"],
        runtime_schema=paths["runtime_schema"],
        binding=_binding(),
        lock_path=paths["lock"],
    )
    return paths


def _preflight(paths: dict[str, Path], **changes: object) -> dict[str, object]:
    values = {
        "prompt_path": paths["runtime_prompt"],
        "schema_path": paths["runtime_schema"],
        "lock_path": paths["lock"],
        "source_lock_path": paths["source_lock"],
        "validator_expected_packet_id": RUNTIME_ID,
        "adapter_generation_id": RUNTIME_ID,
        "result_path": paths["preflight"],
    }
    values.update(changes)
    return identity.preflight_actual_request(**values)


def test_runtime_binding_updates_only_dedicated_identity_fields(tmp_path: Path) -> None:
    paths = _prepared(tmp_path)

    result = _preflight(paths)
    lock = identity.read_json(paths["lock"])

    assert result["status"] == "PASS"
    assert identity.prompt_identity(paths["runtime_prompt"].read_text())["packet_id"] == RUNTIME_ID
    assert identity.schema_packet_id(identity.read_json(paths["runtime_schema"])) == RUNTIME_ID
    assert identity.prompt_identity(paths["source_prompt"].read_text())["packet_id"] == SOURCE_ID
    assert identity.schema_packet_id(identity.read_json(paths["source_schema"])) == SOURCE_ID
    assert lock["decision_prompt_semantic_change"] == 0
    assert lock["investment_schema_semantic_change"] == 0
    assert lock["historical_source_artifact_mutation"] == 0


@pytest.mark.parametrize(
    "mutation,expected",
    (
        ("schema_old", "schema_packet_id_const"),
        ("prompt_old", "prompt_packet_id"),
        ("validator_old", "validator_expected_packet_id"),
        ("adapter_old", "adapter_generation_id"),
        ("schema_contract", "schema_contract"),
        ("subject_order", "prompt_subject_order"),
        ("schema_path_old", "schema_packet_id_const"),
    ),
)
def test_actual_request_identity_mismatches_fail_before_spawn(
    tmp_path: Path, mutation: str, expected: str
) -> None:
    paths = _prepared(tmp_path)
    changes: dict[str, object] = {}
    if mutation == "schema_old":
        _write_json(paths["runtime_schema"], _schema())
    elif mutation == "prompt_old":
        paths["runtime_prompt"].write_text(_prompt(), encoding="utf-8")
    elif mutation == "validator_old":
        changes["validator_expected_packet_id"] = SOURCE_ID
    elif mutation == "adapter_old":
        changes["adapter_generation_id"] = SOURCE_ID
    elif mutation == "schema_contract":
        schema = identity.read_json(paths["runtime_schema"])
        schema["properties"]["contract"]["const"] = "price-timing-overlay-output-v1"
        _write_json(paths["runtime_schema"], schema)
    elif mutation == "subject_order":
        prompt = identity.prompt_identity(paths["runtime_prompt"].read_text())
        prompt["tickers"] = list(reversed(SUBJECTS))
        paths["runtime_prompt"].write_text(_prompt(RUNTIME_ID).replace(
            json.dumps(list(SUBJECTS), separators=(",", ":")),
            json.dumps(list(reversed(SUBJECTS)), separators=(",", ":")),
        ), encoding="utf-8")
    elif mutation == "schema_path_old":
        changes["schema_path"] = paths["source_schema"]

    with pytest.raises(
        identity.PreSpawnRuntimeIdentityBindingMismatch,
        match="PRESPAWN_RUNTIME_IDENTITY_BINDING_MISMATCH",
    ):
        _preflight(paths, **changes)

    proof = identity.read_json(paths["preflight"])
    assert proof["status"] == "FAIL"
    assert proof["spawn_started"] == 0
    assert proof["transport_receipt_expected"] == 0
    assert any(expected in error for error in proof["errors"])


def test_nonidentity_prompt_or_schema_change_is_not_hidden_by_normalization(
    tmp_path: Path,
) -> None:
    paths = _prepared(tmp_path)
    original_prompt = paths["runtime_prompt"].read_text(encoding="utf-8")
    original_schema = identity.read_json(paths["runtime_schema"])
    changed_schema = json.loads(json.dumps(original_schema))
    changed_schema["properties"]["candidates"]["minItems"] = 1

    assert identity.normalized_prompt_semantic_hash(original_prompt) != (
        identity.normalized_prompt_semantic_hash(original_prompt + "\nchanged")
    )
    assert identity.normalized_schema_semantic_hash(original_schema) != (
        identity.normalized_schema_semantic_hash(changed_schema)
    )


def test_receipt_and_output_validation_reject_cross_run_or_unexpected_identity() -> None:
    binding = _binding()
    receipt = {
        "generation_id": RUNTIME_ID,
        "invocation_id": binding.invocation_id,
        "stage": binding.stage,
        "batch_id": binding.batch_id,
        "subject_count": len(SUBJECTS),
    }
    output = {
        "contract": CONTRACT,
        "packet_id": RUNTIME_ID,
        "candidates": [{"ticker": ticker} for ticker in SUBJECTS],
    }

    assert identity.validate_receipt_identity(receipt, binding)["status"] == "PASS"
    assert identity.validate_output_identity(output, binding)["status"] == "PASS"

    receipt["invocation_id"] = f"{RUNTIME_ID}:a:DIRECTIONAL_CORE:01"
    output["packet_id"] = SOURCE_ID
    assert identity.validate_receipt_identity(receipt, binding)["status"] == "FAIL"
    assert identity.validate_output_identity(output, binding)["status"] == "FAIL"


def test_missing_or_corrupt_binding_lock_fails_closed(tmp_path: Path) -> None:
    paths = _prepared(tmp_path)
    paths["lock"].write_text("{}\n", encoding="utf-8")

    with pytest.raises(identity.PreSpawnRuntimeIdentityBindingMismatch):
        _preflight(paths)


def test_binding_rejects_source_identity_overwrite_attempt(tmp_path: Path) -> None:
    paths = _prepared(tmp_path)
    paths["source_prompt"].write_text(_prompt("unrelated-id"), encoding="utf-8")

    with pytest.raises(
        identity.PreSpawnRuntimeIdentityBindingMismatch,
        match="prompt_template_packet_id",
    ):
        identity.bind_runtime_request(
            prompt_template=paths["source_prompt"],
            schema_template=paths["source_schema"],
            runtime_prompt=tmp_path / "second-prompt.txt",
            runtime_schema=tmp_path / "second-schema.json",
            binding=_binding(),
            lock_path=tmp_path / "second-lock.json",
        )
