from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from app.services.direction_timing_ownership_service import canonical_sha256
from scripts.shadow_frozen_context_manifest import (
    CANONICAL_CONTEXT_KEY,
    CONTRACT_VERSION,
    canonicalize_shadow_manifest_state,
    normalize_shadow_manifest,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _state(
    tmp_path: Path,
    groups: list[list[str]] | None = None,
) -> tuple[dict[str, object], Path]:
    groups = groups or [[f"T{index:02d}" for index in range(1, 5)]]
    tickers = [ticker for group in groups for ticker in group]
    root = tmp_path / "artifacts" / "shadow"
    packet_paths = {}
    packet_hashes = {}
    packet_file_hashes = {}
    contexts = []
    for ticker in tickers:
        packet = {"ticker": ticker, "value": len(ticker)}
        path = root / "frozen-packets" / f"{ticker}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(packet, sort_keys=True) + "\n", encoding="utf-8")
        packet_paths[ticker] = str(path)
        packet_hashes[ticker] = canonical_sha256(packet)
        packet_file_hashes[ticker] = _sha(path)
    for number, group in enumerate(groups, start=1):
        directory = root / "frozen-contexts" / f"context-{number:02d}"
        inputs = {}
        for key in (
            "monolithic_prompt",
            "monolithic_schema",
            "stage1_prompt",
            "stage1_schema",
            "stage2_schema",
        ):
            path = directory / f"{key}.txt"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"{key}:{number}\n", encoding="utf-8")
            inputs[key] = {"path": str(path), "sha256": _sha(path)}
        contexts.append(
            {
                "context": number,
                "tickers": group,
                "packet_sha256": {
                    ticker: packet_hashes[ticker] for ticker in group
                },
                "business_delta_view_sha256": hashlib.sha256(
                    f"view:{number}".encode()
                ).hexdigest(),
                "inputs": inputs,
            }
        )
    return (
        {
            "status": "FROZEN",
            "generation_id": "test-generation",
            "context_count": len(contexts),
            "tickers": tickers,
            "packet_paths": packet_paths,
            "packet_hashes": packet_hashes,
            "packet_file_hashes": packet_file_hashes,
            "contexts": contexts,
        },
        root,
    )


def _normalize(state: dict[str, object], tmp_path: Path, root: Path):
    return normalize_shadow_manifest(
        state,
        repository_root=tmp_path,
        artifact_root=root,
        expected_tickers=state["tickers"],
    )


def test_shadow_manifest_01_writer_verifier_roundtrip(tmp_path: Path) -> None:
    state, root = _state(tmp_path)
    canonical = canonicalize_shadow_manifest_state(
        state,
        repository_root=tmp_path,
        artifact_root=root,
        expected_tickers=state["tickers"],
    )

    assert "contexts" not in canonical
    assert canonical["shadow_manifest_contract_version"] == CONTRACT_VERSION
    assert canonical["shadow_manifest_canonical_key"] == CANONICAL_CONTEXT_KEY
    normalized = normalize_shadow_manifest(
        canonical,
        repository_root=tmp_path,
        artifact_root=root,
        expected_tickers=state["tickers"],
        allow_legacy=False,
    )
    assert normalized["source_key"] == CANONICAL_CONTEXT_KEY
    assert normalized["ticker_count"] == 4


def test_shadow_manifest_02_six_context_twenty_two_ticker_coverage(
    tmp_path: Path,
) -> None:
    tickers = [f"T{index:02d}" for index in range(1, 23)]
    groups = [tickers[index : index + 4] for index in range(0, 22, 4)]
    state, root = _state(tmp_path, groups)

    normalized = _normalize(state, tmp_path, root)

    assert normalized["context_count"] == 6
    assert normalized["ticker_count"] == 22
    assert normalized["context_size_over_limit_count"] == 0


def test_shadow_manifest_03_duplicate_ticker_across_contexts_fails(
    tmp_path: Path,
) -> None:
    state, root = _state(tmp_path, [["T01", "T02"], ["T03", "T04"]])
    state["contexts"][1]["tickers"][0] = "T02"
    state["contexts"][1]["packet_sha256"] = {
        "T02": state["packet_hashes"]["T02"],
        "T04": state["packet_hashes"]["T04"],
    }

    with pytest.raises(ValueError, match="DUPLICATE_TICKER_ACROSS_CONTEXTS"):
        _normalize(state, tmp_path, root)


def test_shadow_manifest_04_missing_ticker_fails(tmp_path: Path) -> None:
    state, root = _state(tmp_path, [["T01", "T02"], ["T03", "T04"]])
    state["contexts"][1]["tickers"].pop()
    state["contexts"][1]["packet_sha256"].pop("T04")

    with pytest.raises(ValueError, match="TICKER_COVERAGE_MISMATCH"):
        _normalize(state, tmp_path, root)


def test_shadow_manifest_05_context_over_four_fails(tmp_path: Path) -> None:
    state, root = _state(tmp_path, [["T01", "T02", "T03", "T04", "T05"]])

    with pytest.raises(ValueError, match="CONTEXT_SIZE_INVALID"):
        _normalize(state, tmp_path, root)


def test_shadow_manifest_06_missing_input_file_fails(tmp_path: Path) -> None:
    state, root = _state(tmp_path)
    Path(state["contexts"][0]["inputs"]["stage1_prompt"]["path"]).unlink()

    with pytest.raises(ValueError, match="INPUT_FILE_MISSING"):
        _normalize(state, tmp_path, root)


def test_shadow_manifest_07_input_hash_mismatch_fails(tmp_path: Path) -> None:
    state, root = _state(tmp_path)
    state["contexts"][0]["inputs"]["stage1_schema"]["sha256"] = "0" * 64

    with pytest.raises(ValueError, match="INPUT_HASH_MISMATCH"):
        _normalize(state, tmp_path, root)


def test_shadow_manifest_08_packet_hash_mismatch_fails(tmp_path: Path) -> None:
    state, root = _state(tmp_path)
    state["contexts"][0]["packet_sha256"]["T01"] = "0" * 64

    with pytest.raises(ValueError, match="PACKET_HASH_MISMATCH"):
        _normalize(state, tmp_path, root)


def test_shadow_manifest_09_conflicting_dual_keys_fail(tmp_path: Path) -> None:
    state, root = _state(tmp_path)
    state[CANONICAL_CONTEXT_KEY] = copy.deepcopy(state["contexts"])
    state[CANONICAL_CONTEXT_KEY][0]["business_delta_view_sha256"] = "0" * 64

    with pytest.raises(ValueError, match="DUAL_KEY_CONFLICT"):
        _normalize(state, tmp_path, root)


def test_shadow_manifest_10_legacy_key_is_read_only_compatible(
    tmp_path: Path,
) -> None:
    state, root = _state(tmp_path)

    normalized = _normalize(state, tmp_path, root)

    assert normalized["source_key"] == "contexts"
    assert normalized["legacy_key_supported"] is True


def test_matching_dual_keys_are_unambiguous(tmp_path: Path) -> None:
    state, root = _state(tmp_path)
    state[CANONICAL_CONTEXT_KEY] = copy.deepcopy(state["contexts"])

    normalized = _normalize(state, tmp_path, root)

    assert normalized["source_key"] == CANONICAL_CONTEXT_KEY


def test_input_path_escape_fails(tmp_path: Path) -> None:
    state, root = _state(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    state["contexts"][0]["inputs"]["stage1_prompt"] = {
        "path": str(outside),
        "sha256": _sha(outside),
    }

    with pytest.raises(ValueError, match="PATH_ESCAPE"):
        _normalize(state, tmp_path, root)
