"""Canonical frozen-context manifest validation for monitored shadow proofs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re


CONTRACT_VERSION = "shadow-frozen-context-manifest-v1"
FROZEN_INPUT_RESOLVER_CONTRACT_VERSION = "frozen-context-input-layout-v1"
CANONICAL_CONTEXT_KEY = "frozen_contexts"
LEGACY_CONTEXT_KEY = "contexts"
MAX_CONTEXT_TICKERS = 4
REQUIRED_INPUTS = (
    "monolithic_prompt",
    "monolithic_schema",
    "stage1_prompt",
    "stage1_schema",
    "stage2_schema",
)
LEGACY_FLAT = "LEGACY_FLAT"
NESTED_INPUTS_V1 = "NESTED_INPUTS_V1"
FROZEN_INPUT_FILENAMES = {
    "monolithic_prompt": "monolithic-prompt.txt",
    "monolithic_schema": "monolithic-schema.json",
    "stage1_prompt": "stage1-prompt.txt",
    "stage1_schema": "stage1-schema.json",
    "stage2_schema": "stage2-schema.json",
}
_SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass(frozen=True)
class FrozenContextInputIdentity:
    path: str
    sha256: str
    layout: str

    def as_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "layout": self.layout,
        }


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _resolved_path(path: object, *, repository_root: Path) -> Path:
    candidate = Path(str(path))
    if not candidate.is_absolute():
        candidate = repository_root / candidate
    return candidate.resolve()


def _require_beneath(path: Path, *, root: Path, label: str) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"SHADOW_MANIFEST_PATH_ESCAPE:{label}:{path}") from exc


def _validated_identity(
    *,
    path: object,
    digest: object,
    layout: str,
    input_name: str,
) -> FrozenContextInputIdentity:
    if not isinstance(path, str) or not path.strip():
        raise ValueError(f"FROZEN_INPUT_PATH_INVALID:{input_name}")
    if not isinstance(digest, str) or not _SHA256_PATTERN.fullmatch(digest):
        raise ValueError(f"FROZEN_INPUT_SHA256_INVALID:{input_name}")
    return FrozenContextInputIdentity(
        path=path,
        sha256=digest.lower(),
        layout=layout,
    )


def resolve_frozen_context_input(
    row: Mapping[str, object],
    input_name: str,
) -> FrozenContextInputIdentity:
    """Resolve one frozen input from exactly one recognized serialized layout."""

    if input_name not in FROZEN_INPUT_FILENAMES:
        raise ValueError(f"UNKNOWN_FROZEN_INPUT_NAME:{input_name}")

    has_inputs_field = "inputs" in row
    nested = row.get("inputs")
    if has_inputs_field and not isinstance(nested, Mapping):
        raise ValueError("MALFORMED_FROZEN_INPUTS_OBJECT")

    nested_present = isinstance(nested, Mapping) and input_name in nested
    flat_path_present = input_name in row
    flat_hash_key = f"{input_name}_sha256"
    flat_hash_present = flat_hash_key in row

    if has_inputs_field and nested_present and flat_path_present and flat_hash_present:
        raise ValueError(f"AMBIGUOUS_FROZEN_INPUT_LAYOUT:{input_name}")
    if has_inputs_field and (flat_path_present or flat_hash_present):
        raise ValueError(
            f"PARTIAL_OR_AMBIGUOUS_FROZEN_INPUT_LAYOUT:{input_name}"
        )
    if has_inputs_field:
        if not nested_present:
            raise ValueError(f"FROZEN_INPUT_REQUIRED_MISSING:{input_name}")
        entry = nested[input_name]
        if not isinstance(entry, Mapping):
            raise ValueError(f"NESTED_FROZEN_INPUT_INVALID:{input_name}")
        if "path" not in entry or "sha256" not in entry:
            raise ValueError(f"NESTED_FROZEN_INPUT_INCOMPLETE:{input_name}")
        return _validated_identity(
            path=entry["path"],
            digest=entry["sha256"],
            layout=NESTED_INPUTS_V1,
            input_name=input_name,
        )

    if flat_path_present != flat_hash_present:
        raise ValueError(f"LEGACY_FLAT_FROZEN_INPUT_INCOMPLETE:{input_name}")

    if flat_path_present:
        return _validated_identity(
            path=row[input_name],
            digest=row[flat_hash_key],
            layout=LEGACY_FLAT,
            input_name=input_name,
        )

    raise ValueError(f"FROZEN_INPUT_REQUIRED_MISSING:{input_name}")


def verify_frozen_context_inputs(
    row: Mapping[str, object],
    *,
    required_inputs: Sequence[str],
    repository_root: Path,
    expected_context_directory: Path | None = None,
) -> list[dict[str, object]]:
    """Verify required frozen files and return auditable input identities."""

    resolved = [
        (input_name, resolve_frozen_context_input(row, input_name))
        for input_name in required_inputs
    ]
    layouts = {identity.layout for _, identity in resolved}
    if len(layouts) != 1:
        raise ValueError("PARTIAL_OR_AMBIGUOUS_FROZEN_INPUT_LAYOUT")

    repository_root = repository_root.resolve()
    expected_directory = (
        _resolved_path(expected_context_directory, repository_root=repository_root)
        if expected_context_directory is not None
        else None
    )
    audit_rows: list[dict[str, object]] = []
    for input_name, identity in resolved:
        path = _resolved_path(identity.path, repository_root=repository_root)
        if expected_directory is not None and path.parent != expected_directory:
            raise ValueError(f"FROZEN_INPUT_CONTEXT_PATH_MISMATCH:{input_name}")
        if path.name != FROZEN_INPUT_FILENAMES[input_name]:
            raise ValueError(f"FROZEN_INPUT_FILENAME_MISMATCH:{input_name}")
        if not path.is_file():
            raise ValueError(f"FROZEN_INPUT_MISSING:{input_name}")
        actual_sha256 = _file_sha256(path)
        if actual_sha256 != identity.sha256:
            raise ValueError(f"FROZEN_INPUT_CHANGED:{input_name}")
        audit_rows.append(
            {
                "input_name": input_name,
                "detected_layout": identity.layout,
                "declared_path": identity.path,
                "declared_sha256": identity.sha256,
                "actual_sha256": actual_sha256,
                "path_exists": True,
                "hash_match": True,
                "status": "PASS",
            }
        )
    return audit_rows


def _input_rows(row: Mapping[str, object]) -> dict[str, dict[str, str]]:
    resolved = {
        key: resolve_frozen_context_input(row, key) for key in REQUIRED_INPUTS
    }
    if len({identity.layout for identity in resolved.values()}) != 1:
        raise ValueError("PARTIAL_OR_AMBIGUOUS_FROZEN_INPUT_LAYOUT")
    return {
        key: {"path": identity.path, "sha256": identity.sha256}
        for key, identity in resolved.items()
    }


def _normalize_context_rows(rows: object) -> list[dict[str, object]]:
    if not isinstance(rows, list):
        raise ValueError("SHADOW_FROZEN_CONTEXTS_MISSING")
    normalized = []
    for raw in rows:
        if not isinstance(raw, Mapping):
            raise ValueError("SHADOW_FROZEN_CONTEXT_ROW_INVALID")
        context_id = raw.get("context_id", raw.get("context"))
        if not isinstance(context_id, int) or isinstance(context_id, bool):
            raise ValueError("SHADOW_MANIFEST_CONTEXT_ID_INVALID")
        tickers = raw.get("tickers")
        if not isinstance(tickers, list) or not all(
            isinstance(ticker, str) and ticker for ticker in tickers
        ):
            raise ValueError(f"SHADOW_MANIFEST_TICKERS_INVALID:{context_id}")
        packet_sha256 = raw.get("packet_sha256")
        if not isinstance(packet_sha256, Mapping):
            raise ValueError(f"SHADOW_MANIFEST_PACKET_HASHES_MISSING:{context_id}")
        view_digest = raw.get("business_delta_view_sha256")
        if not isinstance(view_digest, str) or not view_digest:
            raise ValueError(f"SHADOW_MANIFEST_DELTA_VIEW_HASH_MISSING:{context_id}")
        normalized.append(
            {
                "context_id": context_id,
                "tickers": list(tickers),
                "packet_sha256": {
                    str(ticker): str(digest)
                    for ticker, digest in packet_sha256.items()
                },
                "business_delta_view_sha256": view_digest,
                "inputs": _input_rows(raw),
            }
        )
    return normalized


def _context_source(
    state: Mapping[str, object],
    *,
    allow_legacy: bool,
) -> tuple[str, list[dict[str, object]]]:
    has_canonical = CANONICAL_CONTEXT_KEY in state
    has_legacy = LEGACY_CONTEXT_KEY in state
    if has_canonical and has_legacy:
        canonical = _normalize_context_rows(state[CANONICAL_CONTEXT_KEY])
        legacy = _normalize_context_rows(state[LEGACY_CONTEXT_KEY])
        if canonical != legacy:
            raise ValueError("SHADOW_MANIFEST_DUAL_KEY_CONFLICT")
        return CANONICAL_CONTEXT_KEY, canonical
    if has_canonical:
        return CANONICAL_CONTEXT_KEY, _normalize_context_rows(
            state[CANONICAL_CONTEXT_KEY]
        )
    if has_legacy and allow_legacy:
        return LEGACY_CONTEXT_KEY, _normalize_context_rows(state[LEGACY_CONTEXT_KEY])
    if has_legacy:
        raise ValueError("SHADOW_MANIFEST_LEGACY_KEY_NOT_ALLOWED")
    raise ValueError("SHADOW_FROZEN_CONTEXTS_MISSING")


def normalize_shadow_manifest(
    state: Mapping[str, object],
    *,
    repository_root: Path,
    artifact_root: Path,
    expected_tickers: Sequence[str] | None = None,
    allow_legacy: bool = True,
    verify_files: bool = True,
) -> dict[str, object]:
    """Validate and normalize one shadow manifest without mutating its source."""

    if state.get("status") != "FROZEN":
        raise ValueError("SHADOW_STATE_NOT_FROZEN")
    generation_id = state.get("generation_id")
    if not isinstance(generation_id, str) or not generation_id:
        raise ValueError("SHADOW_MANIFEST_GENERATION_ID_MISSING")

    source_key, contexts = _context_source(state, allow_legacy=allow_legacy)
    context_count = state.get("context_count")
    if not isinstance(context_count, int) or context_count != len(contexts):
        raise ValueError("SHADOW_MANIFEST_CONTEXT_COUNT_MISMATCH")

    context_ids = [int(row["context_id"]) for row in contexts]
    if len(context_ids) != len(set(context_ids)):
        raise ValueError("SHADOW_MANIFEST_DUPLICATE_CONTEXT_ID")
    if sorted(context_ids) != list(range(1, len(context_ids) + 1)):
        raise ValueError("SHADOW_MANIFEST_CONTEXT_ID_SEQUENCE_INVALID")

    flattened: list[str] = []
    for row in contexts:
        tickers = list(row["tickers"])
        if not 1 <= len(tickers) <= MAX_CONTEXT_TICKERS:
            raise ValueError(
                f"SHADOW_MANIFEST_CONTEXT_SIZE_INVALID:{row['context_id']}:{len(tickers)}"
            )
        if len(tickers) != len(set(tickers)):
            raise ValueError(
                f"SHADOW_MANIFEST_DUPLICATE_TICKER_IN_CONTEXT:{row['context_id']}"
            )
        flattened.extend(tickers)
    if len(flattened) != len(set(flattened)):
        raise ValueError("SHADOW_MANIFEST_DUPLICATE_TICKER_ACROSS_CONTEXTS")

    state_tickers = state.get("tickers")
    if not isinstance(state_tickers, list) or not all(
        isinstance(ticker, str) and ticker for ticker in state_tickers
    ):
        raise ValueError("SHADOW_MANIFEST_STATE_TICKERS_INVALID")
    target = list(expected_tickers) if expected_tickers is not None else state_tickers
    if flattened != target or state_tickers != target:
        raise ValueError("SHADOW_MANIFEST_TICKER_COVERAGE_MISMATCH")

    packet_paths = state.get("packet_paths")
    packet_hashes = state.get("packet_hashes")
    packet_file_hashes = state.get("packet_file_hashes")
    if not all(
        isinstance(value, Mapping)
        for value in (packet_paths, packet_hashes, packet_file_hashes)
    ):
        raise ValueError("SHADOW_MANIFEST_PACKET_REGISTRY_MISSING")

    repository_root = repository_root.resolve()
    artifact_root = _resolved_path(artifact_root, repository_root=repository_root)
    input_file_count = 0
    for row in contexts:
        tickers = list(row["tickers"])
        row_hashes = row["packet_sha256"]
        if set(row_hashes) != set(tickers):
            raise ValueError(
                f"SHADOW_MANIFEST_CONTEXT_PACKET_COVERAGE_MISMATCH:{row['context_id']}"
            )
        for ticker in tickers:
            if str(row_hashes[ticker]) != str(packet_hashes.get(ticker)):
                raise ValueError(f"SHADOW_MANIFEST_PACKET_HASH_MISMATCH:{ticker}")
        for key, value in row["inputs"].items():
            path = _resolved_path(value["path"], repository_root=repository_root)
            _require_beneath(path, root=artifact_root, label=f"{row['context_id']}:{key}")
            if verify_files:
                if not path.is_file():
                    raise ValueError(
                        f"SHADOW_MANIFEST_INPUT_FILE_MISSING:{row['context_id']}:{key}"
                    )
                if _file_sha256(path) != value["sha256"]:
                    raise ValueError(
                        f"SHADOW_MANIFEST_INPUT_HASH_MISMATCH:{row['context_id']}:{key}"
                    )
            input_file_count += 1

    for ticker in target:
        if ticker not in packet_paths or ticker not in packet_hashes:
            raise ValueError(f"SHADOW_MANIFEST_PACKET_REGISTRY_INCOMPLETE:{ticker}")
        path = _resolved_path(packet_paths[ticker], repository_root=repository_root)
        _require_beneath(path, root=artifact_root, label=f"packet:{ticker}")
        if verify_files:
            if not path.is_file():
                raise ValueError(f"SHADOW_MANIFEST_PACKET_FILE_MISSING:{ticker}")
            if _file_sha256(path) != str(packet_file_hashes.get(ticker)):
                raise ValueError(f"SHADOW_MANIFEST_PACKET_FILE_HASH_MISMATCH:{ticker}")
            payload = json.loads(path.read_text(encoding="utf-8"))
            if _canonical_sha256(payload) != str(packet_hashes[ticker]):
                raise ValueError(f"SHADOW_MANIFEST_PACKET_HASH_MISMATCH:{ticker}")

    return {
        "contract_version": CONTRACT_VERSION,
        "generation_id": generation_id,
        "status": "FROZEN",
        "source_key": source_key,
        "canonical_key": CANONICAL_CONTEXT_KEY,
        "legacy_key_supported": allow_legacy,
        "context_count": len(contexts),
        "ticker_count": len(flattened),
        "tickers": flattened,
        "context_size_over_limit_count": sum(
            len(row["tickers"]) > MAX_CONTEXT_TICKERS for row in contexts
        ),
        "input_file_count": input_file_count,
        "contexts": contexts,
    }


def canonicalize_shadow_manifest_state(
    state: Mapping[str, object],
    *,
    repository_root: Path,
    artifact_root: Path,
    expected_tickers: Sequence[str] | None = None,
) -> dict[str, object]:
    """Return a validated state with exactly one writable context-list key."""

    normalized = normalize_shadow_manifest(
        state,
        repository_root=repository_root,
        artifact_root=artifact_root,
        expected_tickers=expected_tickers,
        allow_legacy=True,
        verify_files=True,
    )
    result = dict(state)
    result.pop(LEGACY_CONTEXT_KEY, None)
    result["shadow_manifest_contract_version"] = CONTRACT_VERSION
    result["shadow_manifest_canonical_key"] = CANONICAL_CONTEXT_KEY
    result["shadow_manifest_legacy_key_supported"] = True
    result[CANONICAL_CONTEXT_KEY] = [
        {
            "context": row["context_id"],
            "tickers": row["tickers"],
            "packet_sha256": row["packet_sha256"],
            "business_delta_view_sha256": row["business_delta_view_sha256"],
            "inputs": row["inputs"],
        }
        for row in normalized["contexts"]
    ]
    return result
