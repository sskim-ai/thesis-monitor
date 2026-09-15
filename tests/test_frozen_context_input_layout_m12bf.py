from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts import business_delta_evidence_capability_m12ai as capability
from scripts.shadow_frozen_context_manifest import (
    FROZEN_INPUT_FILENAMES,
    LEGACY_FLAT,
    NESTED_INPUTS_V1,
    resolve_frozen_context_input,
    verify_frozen_context_inputs,
)


FICTIONAL_INPUTS = (
    "stage1_prompt",
    "stage1_schema",
    "stage2_schema",
)
SHADOW_INPUTS = (
    "monolithic_prompt",
    "monolithic_schema",
    *FICTIONAL_INPUTS,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _files(directory: Path, names: tuple[str, ...]) -> dict[str, Path]:
    result = {}
    for name in names:
        path = directory / FROZEN_INPUT_FILENAMES[name]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{name}\n", encoding="utf-8")
        result[name] = path
    return result


def _nested(files: dict[str, Path]) -> dict[str, object]:
    return {
        "context": 1,
        "inputs": {
            name: {"path": str(path), "sha256": _sha(path)}
            for name, path in files.items()
        },
    }


def _flat(files: dict[str, Path]) -> dict[str, object]:
    row: dict[str, object] = {"context": 1}
    for name, path in files.items():
        row[name] = str(path)
        row[f"{name}_sha256"] = _sha(path)
    return row


def _verify(
    row: dict[str, object],
    names: tuple[str, ...],
    directory: Path,
) -> list[dict[str, object]]:
    return verify_frozen_context_inputs(
        row,
        required_inputs=names,
        repository_root=directory.parents[3],
        expected_context_directory=directory,
    )


def test_input_layout_p01_legacy_flat_passes(tmp_path: Path) -> None:
    directory = tmp_path / "fictional/frozen-contexts/context-01"
    rows = _verify(_flat(_files(directory, FICTIONAL_INPUTS)), FICTIONAL_INPUTS, directory)

    assert len(rows) == 3
    assert {row["detected_layout"] for row in rows} == {LEGACY_FLAT}


def test_input_layout_p02_nested_passes(tmp_path: Path) -> None:
    directory = tmp_path / "fictional/frozen-contexts/context-01"
    rows = _verify(
        _nested(_files(directory, FICTIONAL_INPUTS)),
        FICTIONAL_INPUTS,
        directory,
    )

    assert len(rows) == 3
    assert {row["detected_layout"] for row in rows} == {NESTED_INPUTS_V1}


def test_input_layout_p03_shadow_five_input_nested_passes(tmp_path: Path) -> None:
    directory = tmp_path / "shadow/frozen-contexts/context-01"
    rows = _verify(
        _nested(_files(directory, SHADOW_INPUTS)),
        SHADOW_INPUTS,
        directory,
    )

    assert len(rows) == 5
    assert {row["detected_layout"] for row in rows} == {NESTED_INPUTS_V1}


def test_input_layout_n01_dual_layout_fails(tmp_path: Path) -> None:
    directory = tmp_path / "shadow/frozen-contexts/context-01"
    files = _files(directory, SHADOW_INPUTS)
    row = _nested(files)
    row["stage1_prompt"] = str(files["stage1_prompt"])
    row["stage1_prompt_sha256"] = _sha(files["stage1_prompt"])

    with pytest.raises(ValueError, match="AMBIGUOUS_FROZEN_INPUT_LAYOUT"):
        resolve_frozen_context_input(row, "stage1_prompt")


def test_input_layout_n02_partial_dual_layout_fails(tmp_path: Path) -> None:
    directory = tmp_path / "shadow/frozen-contexts/context-01"
    files = _files(directory, SHADOW_INPUTS)
    row = _nested(files)
    row["stage1_prompt_sha256"] = _sha(files["stage1_prompt"])

    with pytest.raises(ValueError, match="PARTIAL_OR_AMBIGUOUS"):
        resolve_frozen_context_input(row, "stage1_prompt")


def test_input_layout_n03_nested_missing_hash_fails(tmp_path: Path) -> None:
    directory = tmp_path / "shadow/frozen-contexts/context-01"
    row = _nested(_files(directory, SHADOW_INPUTS))
    del row["inputs"]["stage1_prompt"]["sha256"]

    with pytest.raises(ValueError, match="NESTED_FROZEN_INPUT_INCOMPLETE"):
        resolve_frozen_context_input(row, "stage1_prompt")


def test_input_layout_n04_flat_missing_hash_fails(tmp_path: Path) -> None:
    directory = tmp_path / "fictional/frozen-contexts/context-01"
    row = _flat(_files(directory, FICTIONAL_INPUTS))
    del row["stage1_prompt_sha256"]

    with pytest.raises(ValueError, match="LEGACY_FLAT_FROZEN_INPUT_INCOMPLETE"):
        resolve_frozen_context_input(row, "stage1_prompt")


def test_input_layout_n05_hash_mismatch_fails(tmp_path: Path) -> None:
    directory = tmp_path / "shadow/frozen-contexts/context-01"
    row = _nested(_files(directory, SHADOW_INPUTS))
    row["inputs"]["stage1_prompt"]["sha256"] = "0" * 64

    with pytest.raises(ValueError, match="FROZEN_INPUT_CHANGED:stage1_prompt"):
        _verify(row, SHADOW_INPUTS, directory)


def test_input_layout_n06_required_input_missing_fails(tmp_path: Path) -> None:
    directory = tmp_path / "shadow/frozen-contexts/context-01"
    row = _nested(_files(directory, SHADOW_INPUTS))
    del row["inputs"]["monolithic_schema"]

    with pytest.raises(ValueError, match="FROZEN_INPUT_REQUIRED_MISSING"):
        _verify(row, SHADOW_INPUTS, directory)


def test_input_layout_n07_malformed_inputs_object_fails() -> None:
    with pytest.raises(ValueError, match="MALFORMED_FROZEN_INPUTS_OBJECT"):
        resolve_frozen_context_input({"inputs": []}, "stage1_prompt")


def test_nested_layout_marker_never_falls_back_to_flat(tmp_path: Path) -> None:
    directory = tmp_path / "fictional/frozen-contexts/context-01"
    files = _files(directory, FICTIONAL_INPUTS)
    row = _flat(files)
    row["inputs"] = {}

    with pytest.raises(ValueError, match="PARTIAL_OR_AMBIGUOUS"):
        resolve_frozen_context_input(row, "stage1_prompt")


@pytest.mark.parametrize(
    ("subject", "inputs", "layout"),
    (
        ("FICTIONAL", FICTIONAL_INPUTS, LEGACY_FLAT),
        ("SHADOW", SHADOW_INPUTS, NESTED_INPUTS_V1),
    ),
)
def test_shared_verifier_accepts_each_versioned_layout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    subject: str,
    inputs: tuple[str, ...],
    layout: str,
) -> None:
    output = tmp_path / "proof"
    directory = output / subject.casefold() / "frozen-contexts/context-01"
    files = _files(directory, inputs)
    row = _flat(files) if layout == LEGACY_FLAT else _nested(files)
    monkeypatch.setattr(capability, "OUTPUT", output)
    monkeypatch.setattr(capability, "_code_hashes", lambda: {"code": "frozen"})
    state = {
        "status": "FROZEN",
        "code_hashes": {"code": "frozen"},
        "frozen_contexts": [row],
    }

    capability._verify_frozen_state(state, subject=subject)


def test_shared_shadow_verifier_requires_monolithic_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "proof"
    directory = output / "shadow/frozen-contexts/context-01"
    row = _nested(_files(directory, FICTIONAL_INPUTS))
    monkeypatch.setattr(capability, "OUTPUT", output)
    monkeypatch.setattr(capability, "_code_hashes", lambda: {"code": "frozen"})
    state = {
        "status": "FROZEN",
        "code_hashes": {"code": "frozen"},
        "frozen_contexts": [row],
    }

    with pytest.raises(ValueError, match="FROZEN_INPUT_REQUIRED_MISSING"):
        capability._verify_frozen_state(state, subject="SHADOW")
