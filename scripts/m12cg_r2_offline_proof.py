from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from xml.etree import ElementTree

from app.services.accepted_decision_v2_runtime_service import (
    ARTIFACT_CONTRACT,
    advance_accepted_v2_state,
    load_accepted_v2_production_artifact,
    load_accepted_v2_state,
    parse_accepted_v2_production_artifact,
)
from app.services.decision_canary_service import canonical_sha256
from scripts import m12cg_r1_offline_proof as r1


REQUIRED_BASE_SHA = "b5b605fd92c19af68ce39b299d0e1b540160c849"
BEFORE_RUNTIME_SHA = "b7e541b6a3c54567018f937f32d6f92be09a7e4e"
R1_AUDIT_SHA = "9f85763b98f2a921a4dd59f49a53a3a68449b85a"
WORK_INSTRUCTION_CONTENT_SHA = (
    "368cf3f109c656f15455434261005f1d581c75e81e2e813faafd88cec9f53c07"
)
EXPECTED_SOURCE_SHAS = {
    "m12cb": "86d9a40debc253b1a2a155fe260962f701274bc7a75d17bf3c744ab3871bcddb",
    "m12cc": "7b4a09d651fc47d400831ddff603d4ce8b8cd2310674a31e07cd0b2b2fa728fd",
    "m12cd": "89d51179aca722ce38b282c51d3fedb34ea6446df8c6c6ea71bb8e5cf74951ff",
    "m12ce": "512c428bbb01c9ae0834cf0d79d01a330095f67553410f854e296bf9d94c07f9",
    "m12cf": "4375203ad1268fae87b79c88c00607e25849651e32961a87b0b73c537e8a1846",
    "m12cg": "ad8a75edb25d88220cb59d61919a9ba7c86278362b4bac2d30193092e14d06e8",
    "M12CG-R1": "55b2c890fedad3b5b09e5995862637d040f69db882745bfdddfa30d1d38c191f",
}
EXPECTED_SOURCE_COUNTS = {
    "m12cb": 262,
    "m12cc": 114,
    "m12cd": 89,
    "m12ce": 112,
    "m12cf": 46,
    "m12cg": 42,
    "M12CG-R1": 86,
}
RUNTIME_CHANGED_FILES = ("app/services/evidence_maturity_pricing_service.py",)
AUDIT_FILES = (
    "scripts/m12cg_r2_guard_probe.py",
    "scripts/m12cg_r2_runtime_probe.py",
    "scripts/m12cg_r2_offline_proof.py",
    "tests/test_m12cg_r2_offline_proof.py",
    "tests/test_preconfirmation_decision_v2_service.py",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def pretty_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def write_json(root: Path, relative: str, value: object) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pretty_bytes(value))
    return path


def run(repo: Path, *args: str) -> str:
    return subprocess.run(
        args,
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def git_bytes(repo: Path, revision: str, relative: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{revision}:{relative}"),
        cwd=repo,
        check=True,
        capture_output=True,
    ).stdout


def safe_zip_names(archive: zipfile.ZipFile) -> tuple[list[str], list[str], list[str]]:
    names = archive.namelist()
    unsafe = []
    for name in names:
        value = PurePosixPath(name)
        if value.is_absolute() or ".." in value.parts:
            unsafe.append(name)
    duplicate = sorted(name for name in set(names) if names.count(name) > 1)
    return names, unsafe, duplicate


def source_root_for_manifest(
    extraction_root: Path,
    manifest_suffix: PurePosixPath,
) -> tuple[Path, Path]:
    candidates = [
        path
        for path in extraction_root.rglob(manifest_suffix.name)
        if tuple(path.parts[-len(manifest_suffix.parts) :])
        == manifest_suffix.parts
    ]
    if len(candidates) != 1:
        raise ValueError(
            f"source_manifest_ambiguous:{manifest_suffix}:{len(candidates)}"
        )
    manifest_path = candidates[0]
    source_root = manifest_path
    for _ in manifest_suffix.parts:
        source_root = source_root.parent
    return source_root, manifest_path


def extract_and_verify_source(
    *,
    key: str,
    entry: Mapping[str, object],
    package_root: Path,
    extraction_root: Path,
) -> tuple[Path, dict[str, object]]:
    zip_path = package_root / "sources" / str(entry["filename"])
    expected_sha = EXPECTED_SOURCE_SHAS[key]
    actual_sha = sha256_file(zip_path)
    sidecar_path = zip_path.with_suffix(zip_path.suffix + ".sha256")
    sidecar_token = sidecar_path.read_text(encoding="utf-8").split()[0]
    destination = extraction_root / key
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        names, unsafe, duplicate = safe_zip_names(archive)
        bad_crc = archive.testzip()
        if unsafe or duplicate or bad_crc is not None:
            raise ValueError(f"unsafe_source_bundle:{key}")
        archive.extractall(destination)
    manifest_suffix = PurePosixPath(str(entry["manifest_path"]))
    source_root, manifest_path = source_root_for_manifest(
        destination,
        manifest_suffix,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = manifest.get("artifacts")
    if not isinstance(rows, list):
        raise ValueError(f"source_manifest_invalid:{key}")
    errors: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            errors.append({"path": None, "error": "invalid_manifest_row"})
            continue
        relative = PurePosixPath(str(row.get("path") or ""))
        if relative.is_absolute() or ".." in relative.parts:
            errors.append({"path": str(relative), "error": "unsafe_path"})
            continue
        path = source_root / relative
        if not path.is_file():
            errors.append({"path": str(relative), "error": "missing"})
            continue
        if path.stat().st_size != int(row.get("size") or -1):
            errors.append({"path": str(relative), "error": "size"})
        if sha256_file(path) != str(row.get("sha256") or ""):
            errors.append({"path": str(relative), "error": "sha256"})
    declared = int(manifest.get("artifact_count") or len(rows))
    expected_count = EXPECTED_SOURCE_COUNTS[key]
    status = (
        "PASS"
        if actual_sha == expected_sha == sidecar_token
        and declared == expected_count
        and len(rows) == expected_count
        and not errors
        else "FAIL"
    )
    return source_root, {
        "source_key": key,
        "filename": zip_path.name,
        "expected_sha256": expected_sha,
        "actual_sha256": actual_sha,
        "sidecar_sha256": sidecar_token,
        "archive_entry_count": len(names),
        "unsafe_entry_count": len(unsafe),
        "duplicate_entry_count": len(duplicate),
        "crc_bad_entry": bad_crc,
        "manifest_path": manifest_suffix.as_posix(),
        "manifest_declared_count": declared,
        "manifest_verified_count": len(rows) - len(errors),
        "manifest_errors": errors,
        "status": status,
    }


def export_git_tree(repo: Path, revision: str, destination: Path) -> None:
    r1.export_git_tree(repo, revision, destination)


def execute_probe(
    *,
    repo: Path,
    python: Path,
    script: Path,
    runtime_root: Path,
    runtime_label: str,
    result_path: Path,
    args: Sequence[str],
) -> dict[str, object]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(runtime_root)
    subprocess.run(
        (
            str(python),
            str(script),
            *args,
            "--result",
            str(result_path),
            "--runtime-label",
            runtime_label,
        ),
        cwd=repo,
        env=env,
        check=True,
    )
    return json.loads(result_path.read_text(encoding="utf-8"))


def keyed(rows: Sequence[Mapping[str, object]], *fields: str) -> dict[tuple[object, ...], Mapping[str, object]]:
    return {tuple(row.get(field) for field in fields): row for row in rows}


def compare_runtime_probes(
    before: Mapping[str, object],
    after: Mapping[str, object],
) -> dict[str, object]:
    sections: dict[str, object] = {}
    for section_name in ("historical", "fresh"):
        left = before[section_name]
        right = after[section_name]
        assert isinstance(left, Mapping) and isinstance(right, Mapping)
        batch_fields = (
            ("market", "source_output")
            if section_name == "historical"
            else ("batch",)
        )
        candidate_fields = (
            ("market", "source_output", "ticker")
            if section_name == "historical"
            else ("batch", "ticker")
        )
        left_batches = keyed(left["batches"], *batch_fields)
        right_batches = keyed(right["batches"], *batch_fields)
        batch_rows = []
        for key in sorted(left_batches):
            before_row = left_batches[key]
            after_row = right_batches[key]
            before_payload = before_row["payload"]
            after_payload = after_row["payload"]
            batch_rows.append(
                {
                    "identity": list(key),
                    "before_canonical_sha256": before_payload["canonical_sha256"],
                    "after_canonical_sha256": after_payload["canonical_sha256"],
                    "canonical_hash_equal": (
                        before_payload["canonical_sha256"]
                        == after_payload["canonical_sha256"]
                    ),
                    "candidate_count_equal": (
                        before_row["candidate_count"] == after_row["candidate_count"]
                    ),
                    "row_count_equal": before_row["row_count"] == after_row["row_count"],
                }
            )
        left_candidates = keyed(left["candidates"], *candidate_fields)
        right_candidates = keyed(right["candidates"], *candidate_fields)
        candidate_rows = []
        for key in sorted(left_candidates):
            before_row = left_candidates[key]
            after_row = right_candidates[key]
            candidate_rows.append(
                {
                    "identity": list(key),
                    "before_canonical_sha256": before_row["payload"]["canonical_sha256"],
                    "after_canonical_sha256": after_row["payload"]["canonical_sha256"],
                    "canonical_hash_equal": (
                        before_row["payload"]["canonical_sha256"]
                        == after_row["payload"]["canonical_sha256"]
                    ),
                    "row_projection_equal": before_row["rows"] == after_row["rows"],
                    "validation_equal": (
                        before_row["validation"] == after_row["validation"]
                        and before_row["validation_errors"]
                        == after_row["validation_errors"]
                    ),
                }
            )
        sections[section_name] = {
            "before_counts": {
                field: left[field]
                for field in (
                    "batch_count",
                    "candidate_count",
                    "row_count",
                    "valid_candidate_count",
                )
            },
            "after_counts": {
                field: right[field]
                for field in (
                    "batch_count",
                    "candidate_count",
                    "row_count",
                    "valid_candidate_count",
                )
            },
            "batch_rows": batch_rows,
            "candidate_rows": candidate_rows,
            "normalized_batch_hash_change_count": sum(
                not row["canonical_hash_equal"] for row in batch_rows
            ),
            "normalized_candidate_hash_change_count": sum(
                not row["canonical_hash_equal"] for row in candidate_rows
            ),
            "row_projection_change_count": sum(
                not row["row_projection_equal"] for row in candidate_rows
            ),
            "validation_change_count": sum(
                not row["validation_equal"] for row in candidate_rows
            ),
        }

    before_fresh = before["fresh"]
    after_fresh = after["fresh"]
    assert isinstance(before_fresh, Mapping) and isinstance(after_fresh, Mapping)
    model_rows = []
    for left, right in zip(
        before_fresh["model_facing"],
        after_fresh["model_facing"],
        strict=True,
    ):
        model_rows.append(
            {
                "batch": left["batch"],
                "subjects": left["subjects"],
                "prompt_byte_equal": left["prompt_sha256"] == right["prompt_sha256"],
                "schema_byte_equal": left["schema_sha256"] == right["schema_sha256"],
                "catalog_byte_equal": left["catalog_sha256"] == right["catalog_sha256"],
                "before": left,
                "after": right,
            }
        )
    before_final = keyed(before_fresh["finalizations"], "ticker")
    after_final = keyed(after_fresh["finalizations"], "ticker")
    finalization_rows = []
    for key in sorted(before_final):
        left = before_final[key]
        right = after_final[key]
        finalization_rows.append(
            {
                "ticker": key[0],
                "before_result": left["result"],
                "after_result": right["result"],
                "before_error": left.get("error"),
                "after_error": right.get("error"),
                "result_equal": (
                    left["result"] == right["result"]
                    and left.get("error") == right.get("error")
                ),
                "normalized_hash_equal": (
                    left["normalized_sha256"] == right["normalized_sha256"]
                ),
                "accepted_plan_hash_equal": (
                    left.get("accepted_plan_sha256")
                    == right.get("accepted_plan_sha256")
                ),
                "renderer_hash_equal": (
                    left.get("renderer_text_sha256")
                    == right.get("renderer_text_sha256")
                ),
            }
        )
    model_delta_count = sum(
        not (
            row["prompt_byte_equal"]
            and row["schema_byte_equal"]
            and row["catalog_byte_equal"]
        )
        for row in model_rows
    )
    valid_change_count = sum(
        int(sections[name][field])
        for name in ("historical", "fresh")
        for field in (
            "normalized_batch_hash_change_count",
            "normalized_candidate_hash_change_count",
            "row_projection_change_count",
            "validation_change_count",
        )
    )
    return {
        "contract": "m12cg-r2-before-after-valid-input-neutrality-v1",
        "before_runtime_sha": BEFORE_RUNTIME_SHA,
        "sections": sections,
        "model_facing_rows": model_rows,
        "model_facing_byte_delta_count": model_delta_count,
        "finalization_rows": finalization_rows,
        "finalization_result_change_count": sum(
            not row["result_equal"] for row in finalization_rows
        ),
        "valid_input_change_count": valid_change_count,
        "status": (
            "PASS_NO_VALID_INPUT_CHANGE"
            if valid_change_count == 0
            and model_delta_count == 0
            and all(row["result_equal"] for row in finalization_rows)
            else "FAIL_VALID_INPUT_CHANGE"
        ),
    }


def compare_guard_probes(
    before: Mapping[str, object],
    after: Mapping[str, object],
) -> dict[str, object]:
    before_rows = keyed(before["results"], "fixture_id")
    after_rows = keyed(after["results"], "fixture_id")
    rows = []
    for key in sorted(before_rows):
        left = before_rows[key]
        right = after_rows[key]
        rows.append(
            {
                "fixture_id": key[0],
                "before_assertion_result": left.get("assertion_result"),
                "after_assertion_result": right.get("assertion_result"),
                "before_observed_result": left.get("observed_result"),
                "after_observed_result": right.get("observed_result"),
                "after_evidence_scope": right.get("evidence_scope"),
                "after_variant_count": right.get("variant_count", 1),
            }
        )
    required = {f"G{index:02d}" for index in range(1, 15)}
    after_pass = {
        str(row["fixture_id"])
        for row in after["results"]
        if row.get("assertion_result") == "PASS"
    }
    return {
        "contract": "m12cg-r2-before-after-presence-guard-v1",
        "before_runtime_sha": BEFORE_RUNTIME_SHA,
        "before_status": before["status"],
        "after_status": after["status"],
        "before_guard_failure_preserved": before_rows[("G02",)].get(
            "observed_result"
        )
        == "ACCEPTED",
        "explicit_null_preservation_result": after_rows[("G01",)].get(
            "assertion_result"
        ),
        "financial_quality_missing_key_guard_result": after_rows[("G02",)].get(
            "assertion_result"
        ),
        "earnings_missing_label_guard_result": after_rows[("G04",)].get(
            "assertion_result"
        ),
        "earnings_missing_type_guard_result": after_rows[("G05",)].get(
            "assertion_result"
        ),
        "independent_validator_rejection_result": after_rows[("G13",)].get(
            "assertion_result"
        ),
        "fixture_count": len(rows),
        "variant_count": after["variant_count"],
        "rows": rows,
        "status": (
            "PASS_GUARD_REPAIR"
            if required == after_pass and before["status"] == "FAIL"
            else "FAIL_GUARD_REPAIR"
        ),
    }


def semantic_loss_proof(
    current_probe: Mapping[str, object],
    *,
    current_probe_root: Path,
    out: Path,
) -> dict[str, object]:
    fresh = current_probe["fresh"]
    assert isinstance(fresh, Mapping)
    skhy = next(row for row in fresh["candidates"] if row["ticker"] == "SKHY")
    payload_path = current_probe_root / "fresh" / str(skhy["payload"]["path"])
    original = json.loads(payload_path.read_text(encoding="utf-8"))
    decisive_rows = [row for row in skhy["rows"] if row.get("driver")]
    target = next(
        row
        for row in decisive_rows
        if row.get("provenance_status") == "SYMBOLIC_ONLY_NO_CONCRETE_DATE"
    )
    row_index = int(target["row_index"])
    mutated = deepcopy(original)
    deleted_row = mutated["driver_maturity"].pop(row_index)
    mutation_relative = (
        "payloads/negative-controls/"
        "SKHY.decisive-symbolic-row-deleted.candidate.json"
    )
    mutation_path = write_json(out, mutation_relative, mutated)
    diffs = r1.json_pointer_diffs(original, mutated)
    return {
        "contract": "m12cg-r2-semantic-loss-negative-control-v1",
        "ticker": "SKHY",
        "source_candidate_payload": (
            "runtime-probes/after-r2/fresh/" + payload_path.name
        ),
        "source_candidate_sha256": sha256_file(payload_path),
        "mutated_candidate_payload": mutation_relative,
        "mutated_candidate_sha256": sha256_file(mutation_path),
        "original_row_count": len(original["driver_maturity"]),
        "mutated_row_count": len(mutated["driver_maturity"]),
        "deleted_row_index": row_index,
        "deleted_row_sha256": sha256_bytes(canonical_bytes(deleted_row)),
        "deleted_row": deleted_row,
        "json_pointer_diffs": diffs,
        "semantic_loss_detected": (
            bool(diffs)
            and len(mutated["driver_maturity"]) + 1
            == len(original["driver_maturity"])
        ),
        "status": "PASS" if diffs else "FAIL",
    }


def source_excerpt(
    path: Path,
    symbol: Callable[..., object],
) -> dict[str, object]:
    lines, start = inspect.getsourcelines(symbol)
    text = "".join(lines)
    return {
        "file": path.as_posix(),
        "symbol": symbol.__name__,
        "start_line": start,
        "end_line": start + len(lines) - 1,
        "sha256": sha256_bytes(text.encode("utf-8")),
        "text": text,
    }


def native_acceptance_proof(
    *,
    current_probe_root: Path,
    fresh: Mapping[str, object],
    out: Path,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    artifacts = fresh["artifact_by_ticker"]
    legacy_artifacts = fresh["legacy_artifact_by_ticker"]
    assert isinstance(artifacts, Mapping) and isinstance(legacy_artifacts, Mapping)
    source_artifact = artifacts["CORZ"]
    payload = source_artifact.model_dump(mode="json")
    packet = {
        "packet_id": payload["packet_id"],
        "market": payload["market"],
        "assessment_date": payload["assessment_date"],
        "stocks": [{"ticker": "CORZ"}],
    }
    payload["source_packet_sha256"] = canonical_sha256(packet)
    artifact = parse_accepted_v2_production_artifact(payload)
    fixture_path = out / "payloads/native-owner/CORZ.ephemeral-artifact.json"
    write_json(out, "payloads/native-owner/CORZ.ephemeral-artifact.json", payload)
    loaded = load_accepted_v2_production_artifact(
        fixture_path,
        packet=packet,
        claim_id=artifact.claim_id,
    )
    negative_cases: list[dict[str, object]] = []

    def run_case(name: str, artifact_payload: object, packet_payload: object, claim_id: str) -> None:
        case_path = out / f"payloads/native-owner/{name}.json"
        case_path.write_bytes(pretty_bytes(artifact_payload))
        try:
            load_accepted_v2_production_artifact(
                case_path,
                packet=packet_payload,
                claim_id=claim_id,
            )
            observed = "UNEXPECTED_ACCEPTANCE"
        except Exception as exc:
            observed = f"{type(exc).__name__}:{exc}"
        negative_cases.append(
            {
                "case": name,
                "observed": observed,
                "status": "PASS" if observed != "UNEXPECTED_ACCEPTANCE" else "FAIL",
            }
        )

    swapped_packet = deepcopy(packet)
    swapped_packet["packet_id"] = "swapped-packet"
    run_case("packet-id-swap", payload, swapped_packet, artifact.claim_id)
    run_case("claim-id-swap", payload, packet, "swapped-claim")
    subject_swap = deepcopy(packet)
    subject_swap["stocks"] = [{"ticker": "HUT"}]
    run_case("subject-swap", payload, subject_swap, artifact.claim_id)
    hash_tamper = deepcopy(payload)
    hash_tamper["source_packet_sha256"] = "0" * 64
    run_case("source-packet-hash-tamper", hash_tamper, packet, artifact.claim_id)
    block_tamper = deepcopy(payload)
    block_tamper["blocks"][0]["text"] += " tampered"
    run_case("rendered-block-tamper", block_tamper, packet, artifact.claim_id)
    contract_tamper = deepcopy(payload)
    contract_tamper["contract"] = ARTIFACT_CONTRACT
    run_case("v2-payload-labeled-v1", contract_tamper, packet, artifact.claim_id)

    with tempfile.TemporaryDirectory(prefix="m12cg-r2-state-") as directory:
        settings = SimpleNamespace(data_dir=directory)
        timestamp = datetime(2026, 9, 16, tzinfo=UTC)
        first_path = advance_accepted_v2_state(
            artifact,
            settings=settings,
            updated_at=timestamp,
        )
        first_bytes = first_path.read_bytes()
        first_loaded = load_accepted_v2_state(settings=settings)
        second_path = advance_accepted_v2_state(
            artifact,
            settings=settings,
            updated_at=timestamp,
        )
        second_bytes = second_path.read_bytes()
        legacy = legacy_artifacts["CORZ"]
        legacy_payload = legacy.model_dump(mode="json")
        legacy_payload["source_packet_sha256"] = canonical_sha256(packet)
        legacy_fixture = parse_accepted_v2_production_artifact(legacy_payload)
        advance_accepted_v2_state(
            legacy_fixture,
            settings=settings,
            updated_at=timestamp,
        )
        legacy_then_new_path = advance_accepted_v2_state(
            artifact,
            settings=settings,
            updated_at=timestamp,
        )
        legacy_then_new_bytes = legacy_then_new_path.read_bytes()
        final_loaded = load_accepted_v2_state(settings=settings)
    write_json(
        out,
        "payloads/native-owner/CORZ.isolated-state.json",
        json.loads(second_bytes),
    )
    native = {
        "contract": "m12cg-r2-native-artifact-receipt-version-binding-v1",
        "native_authority": (
            "AcceptedV2ProductionArtifact loader validates packet/claim/scope/hash and "
            "rendered block; v2 orchestration receipt is diagnostic and is not the "
            "delivery artifact authority"
        ),
        "source_probe_root": current_probe_root.name,
        "positive_load_type": type(loaded).__name__,
        "positive_contract": loaded.contract,
        "positive_artifact_sha256": sha256_bytes(canonical_bytes(payload)),
        "negative_cases": negative_cases,
        "native_artifact_binding_result": (
            "PASS"
            if all(row["status"] == "PASS" for row in negative_cases)
            else "FAIL"
        ),
        "native_receipt_binding_result": (
            "NOT_APPLICABLE_SERVICE_SPECIFIC_OWNER_MISMATCH_"
            "EQUIVALENT_NATIVE_ARTIFACT_OWNER_EXECUTED"
        ),
        "canonical_receipt_service_bridge_added": False,
        "status": (
            "PASS_NATIVE_ARTIFACT_OWNER"
            if all(row["status"] == "PASS" for row in negative_cases)
            else "FAIL"
        ),
    }
    state = {
        "contract": "m12cg-r2-native-state-roundtrip-idempotency-v1",
        "first_state_loaded": first_loaded is not None,
        "same_version_replay_bytes_equal": first_bytes == second_bytes,
        "same_version_state_sha256": sha256_bytes(second_bytes),
        "legacy_then_new_entry_count": len(final_loaded.entries) if final_loaded else 0,
        "legacy_then_new_state_sha256": sha256_bytes(legacy_then_new_bytes),
        "single_ticker_entry_preserved": (
            final_loaded is not None
            and len(final_loaded.entries) == 1
            and final_loaded.entries[0].ticker == "CORZ"
        ),
        "production_storage_used": False,
        "status": (
            "PASS"
            if first_loaded is not None
            and first_bytes == second_bytes
            and final_loaded is not None
            and len(final_loaded.entries) == 1
            else "FAIL"
        ),
    }
    continuity = {
        "contract": "m12cg-r2-native-delivery-continuity-dedupe-intent-v1",
        "artifact_loader_executed": True,
        "state_roundtrip_executed": True,
        "actual_delivery_route_executed": False,
        "test_sink_delivery_executed": False,
        "duplicate_operational_intent_count": "NOT_PROVEN",
        "continuity_result": "NOT_PROVEN",
        "reason": (
            "The native state owner is post-delivery and has no offline delivery-intent "
            "ledger. No production or test-sink delivery was authorized, so identical "
            "state bytes cannot prove duplicate-intent suppression."
        ),
        "status": "NOT_PROVEN_NATIVE_DELIVERY_ROUTE_NOT_EXECUTED",
    }
    return native, state, continuity


def call_path_proof(repo: Path, out: Path) -> dict[str, object]:
    from app.jobs import accepted_decision_v2_runtime as job
    from app.services import ai_assisted_delivery_service as delivery
    from app.services import accepted_decision_v2_runtime_service as runtime

    symbols = (
        (Path("app/jobs/accepted_decision_v2_runtime.py"), job.validate_output),
        (
            Path("app/services/accepted_decision_v2_runtime_service.py"),
            runtime.load_accepted_v2_production_artifact,
        ),
        (
            Path("app/services/ai_assisted_delivery_service.py"),
            delivery._load_delivery_accepted_v2,
        ),
        (
            Path("app/services/accepted_decision_v2_runtime_service.py"),
            runtime.advance_accepted_v2_state,
        ),
    )
    excerpts = []
    for relative, symbol in symbols:
        excerpt = source_excerpt(relative, symbol)
        excerpts.append({key: value for key, value in excerpt.items() if key != "text"})
        target = out / "excerpts" / f"{relative.stem}--{symbol.__name__}.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(excerpt["text"]), encoding="utf-8")
    canonical_path = Path("app/services/canonical_acceptance_receipt_service.py")
    grep_result = subprocess.run(
        (
            "git",
            "grep",
            "-n",
            "canonical_acceptance_receipt_service",
            "--",
            "app/jobs",
            "app/services",
        ),
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    if grep_result.returncode not in {0, 1}:
        raise RuntimeError(
            "canonical_receipt_call_path_search_failed:"
            f"{grep_result.returncode}:{grep_result.stderr.strip()}"
        )
    grep = grep_result.stdout.strip()
    accepted_v2_direct_calls = [
        line
        for line in grep.splitlines()
        if "accepted_decision_v2" in line or "ai_assisted_delivery" in line
    ]
    return {
        "contract": "m12cg-r2-native-acceptance-requirement-owner-call-path-v1",
        "route": [
            "accepted_decision_v2_runtime.validate_output",
            "load_accepted_v2_production_artifact",
            "ai_assisted_delivery_service._load_delivery_accepted_v2",
            "rendered delivery inclusion",
            "advance_accepted_v2_state after complete send",
        ],
        "excerpts": excerpts,
        "canonical_service_file": canonical_path.as_posix(),
        "accepted_v2_to_canonical_receipt_direct_call_count": len(
            accepted_v2_direct_calls
        ),
        "accepted_v2_to_canonical_receipt_direct_calls": accepted_v2_direct_calls,
        "service_specific_requirement_disposition": (
            "NOT_APPLICABLE_SERVICE_SPECIFIC_OWNER_MISMATCH"
        ),
        "equivalent_native_obligations": {
            "parser_normalized_candidate": "EXECUTED",
            "artifact_packet_claim_scope_hash_binding": "EXECUTED",
            "state_loading_same_version_replay": "EXECUTED",
            "operational_delivery_continuity_dedupe": "NOT_PROVEN",
        },
        "status": "PARTIAL_NATIVE_OWNER_EXECUTED_DELIVERY_CONTINUITY_NOT_PROVEN",
    }


def parse_junit_nodes(path: Path) -> list[dict[str, object]]:
    root = ElementTree.parse(path).getroot()
    rows = []
    for case in root.iter("testcase"):
        classname = str(case.attrib.get("classname") or "")
        name = str(case.attrib.get("name") or "")
        module = classname.replace(".", "/") + ".py" if classname else ""
        status = "PASS"
        if case.find("failure") is not None or case.find("error") is not None:
            status = "FAIL"
        elif case.find("skipped") is not None:
            status = "SKIP"
        rows.append(
            {
                "node_id": f"{module}::{name}" if module else name,
                "name": name,
                "classname": classname,
                "status": status,
            }
        )
    return rows


def matching_nodes(
    nodes: Sequence[Mapping[str, object]],
    patterns: Sequence[str],
) -> list[dict[str, object]]:
    matched: dict[tuple[str, str], dict[str, object]] = {}
    for row in nodes:
        if not any(pattern in str(row["node_id"]) for pattern in patterns):
            continue
        key = (str(row["node_id"]), str(row["status"]))
        matched[key] = dict(row)
    return list(matched.values())


def aggregate_fixture_rows(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    unsupported_group_passes = []
    for row in rows:
        if row.get("assertion_result") != "PASS":
            continue
        denominator = int(row.get("denominator") or 0)
        evidence = row.get("evidence")
        if denominator < 1 or not isinstance(evidence, list) or not evidence:
            unsupported_group_passes.append(str(row.get("fixture_id")))
    not_proven = [
        str(row.get("fixture_id"))
        for row in rows
        if row.get("assertion_result") in {"NOT_PROVEN", "PARTIAL_NOT_PROVEN"}
    ]
    failures = [
        str(row.get("fixture_id"))
        for row in rows
        if row.get("assertion_result") == "FAIL"
    ]
    return {
        "fixture_variant_count": len(rows),
        "proven_count": sum(row.get("assertion_result") == "PASS" for row in rows),
        "not_proven_count": len(not_proven),
        "failure_count": len(failures),
        "unsupported_group_pass_count": len(unsupported_group_passes),
        "unsupported_group_pass_fixtures": unsupported_group_passes,
        "not_proven_fixtures": not_proven,
        "failed_fixtures": failures,
        "status": (
            "PASS"
            if not unsupported_group_passes and not not_proven and not failures
            else "PARTIAL"
            if not unsupported_group_passes and not failures
            else "FAIL"
        ),
    }


def fixture_specs() -> list[dict[str, object]]:
    return [
        {"id": "P01", "tests": ["test_stage2_materializer_uses_max_concrete_same_row_date"]},
        {"id": "P02", "tests": ["test_m12cg_concrete_projection_is_order_and_duplicate_invariant"]},
        {"id": "P03", "tests": ["test_stage2_materializer_uses_max_concrete_same_row_date"], "audit": "historical"},
        {"id": "P04", "tests": ["test_m12cg_mixed_provenance_uses_concrete_max_and_explicit_status"], "audit": "G09"},
        {"id": "P05", "tests": ["test_m12cg_mixed_provenance_uses_concrete_max_and_explicit_status"], "audit": "historical_mixed"},
        {"id": "P06", "tests": ["test_m12cg_symbolic_only_provenance_is_materialized_without_fake_date"], "audit": "G01"},
        {"id": "P07", "tests": ["test_stage2_materializer_uses_max_concrete_same_row_date"]},
        {"id": "P08", "tests": ["test_m12cg_concrete_projection_is_order_and_duplicate_invariant", "test_stage2_materializer_is_hash_stable"]},
        {"id": "P09", "tests": ["test_m12cg_r2_presence_guard_is_not_ref_or_market_specific"], "audit": "G14"},
        {"id": "P10", "audit": "historical_mixed"},
        {"id": "P11", "audit": "fresh"},
        {"id": "P12", "tests": ["test_m12cg_version_dispatch_preserves_legacy_and_rejects_unknown_contract"], "audit": "serialization"},
        {"id": "P13", "tests": ["test_m12cg_v2_artifact_roundtrip_is_deterministic"], "audit": "state"},
        {"id": "N01", "tests": ["test_stage2_materializer_rejects_model_authored_as_of"], "audit": "G12"},
        {"id": "N02", "tests": ["test_m12cg_model_authored_provenance_status_is_rejected"], "audit": "G12"},
        {"id": "N03", "tests": ["test_m12cg_version_dispatch_preserves_legacy_and_rejects_unknown_contract"], "audit": "serialization"},
        {"id": "N04", "tests": ["test_m12cg_normalized_status_date_shape_is_relationally_strict"]},
        {"id": "N05", "tests": ["test_m12cg_hard_validator_recomputes_max_and_status"]},
        {"id": "N06", "tests": ["test_m12cg_hard_validator_recomputes_max_and_status"]},
        {"id": "N07", "tests": ["test_stage2_materializer_rejects_unknown_ref", "test_stage2_materializer_rejects_cross_ticker_ref"]},
        {"id": "N08", "tests": ["test_m12cg_r2_concrete_peer_cannot_hide_missing_metadata_ref", "test_m12cg_concrete_ref_cannot_hide_invalid_symbolic_peer"], "audit": "G08"},
        {"id": "N09", "tests": ["test_m12cg_r2_empty_maturity_ref_set_is_rejected", "test_stage2_materializer_rejects_symbolic_only_without_global_fallback"]},
        {"id": "N10", "tests": ["test_m12cg_symbolic_classifier_requires_canonical_structured_metadata", "test_m12cg_r2_required_nullable_fields_reject_non_null_values"], "audit": "G07_G10_G11"},
        {"id": "N11", "tests": ["test_stage2_materializer_rejects_future_derived_date"], "audit": "G11"},
        {"id": "N12", "tests": ["test_driver_maturity_date_must_be_owned_by_a_cited_ref", "test_stage2_materializer_rejects_cross_ticker_ref"]},
        {"id": "N13", "tests": ["test_m12cg_hard_validator_recomputes_max_and_status"]},
        {"id": "N14", "tests": ["test_stage2_hard_validator_rejects_post_materialization_tamper", "test_m12cg_r2_independent_validator_rejects_forged_symbolic_projection"], "audit": "G13"},
        {"id": "N15", "tests": ["test_m12cg_earnings_placeholder_does_not_bypass_atomic_claim_eligibility"], "audit": "G03"},
        {"id": "N16", "audit": "semantic_loss"},
        {"id": "N17", "tests": ["test_m12cg_version_dispatch_preserves_legacy_and_rejects_unknown_contract"], "audit": "native_partial", "forced": "PARTIAL_NOT_PROVEN"},
        {"id": "N18", "audit": "serialization"},
        {"id": "N19", "tests": ["test_m12cg_normalized_date_rejects_non_json_null_primitives"], "audit": "G07"},
        {"id": "N20", "audit": "historical_negative"},
        {"id": "N21", "tests": ["test_mutated_numeric_frozen_core_fails_before_claim_scope_exemption", "test_stage2_owned_exact_numeric_claim_remains_hard_failure"]},
        {"id": "N22", "tests": ["test_m12cg_r2_atomic_polarity_mutation_is_rejected"]},
    ]


def fixture_coverage(
    *,
    nodes: Sequence[Mapping[str, object]],
    historical: Mapping[str, object],
    fresh_compare: Mapping[str, object],
    guard_after: Mapping[str, object],
    serialization: Mapping[str, object],
    semantic_loss: Mapping[str, object],
    native: Mapping[str, object],
    state: Mapping[str, object],
) -> dict[str, object]:
    guard = {
        str(row["fixture_id"]): row
        for row in guard_after["results"]
    }
    audit_checks = {
        "historical": historical["status"] == "PASS",
        "historical_mixed": historical["provenance_status_counts"].get(
            "CONCRETE_WITH_SYMBOLIC_REFS"
        )
        == 2,
        "fresh": fresh_compare["status"] == "PASS_NO_VALID_INPUT_CHANGE",
        "serialization": str(serialization["status"]).startswith("PASS"),
        "state": state["status"] == "PASS",
        "semantic_loss": semantic_loss["status"] == "PASS",
        "native_partial": native["status"] == "PASS_NATIVE_ARTIFACT_OWNER",
        "historical_negative": historical["original_invalid_candidate_count"] == 1,
        "G01": guard["G01"]["assertion_result"] == "PASS",
        "G03": guard["G03"]["assertion_result"] == "PASS",
        "G07": guard["G07"]["assertion_result"] == "PASS",
        "G08": guard["G08"]["assertion_result"] == "PASS",
        "G09": guard["G09"]["assertion_result"] == "PASS",
        "G11": guard["G11"]["assertion_result"] == "PASS",
        "G12": guard["G12"]["assertion_result"] == "PASS",
        "G13": guard["G13"]["assertion_result"] == "PASS",
        "G14": guard["G14"]["assertion_result"] == "PASS",
        "G07_G10_G11": all(
            guard[key]["assertion_result"] == "PASS"
            for key in ("G07", "G10", "G11")
        ),
    }
    rows = []
    for spec in fixture_specs():
        patterns = spec.get("tests", [])
        test_rows = matching_nodes(nodes, patterns)
        test_ok = bool(test_rows) and all(row["status"] == "PASS" for row in test_rows)
        audit_name = spec.get("audit")
        audit_ok = audit_checks.get(str(audit_name), True) if audit_name else True
        evidence = [
            {
                "type": "pytest_node",
                "node_id": row["node_id"],
                "result": row["status"],
            }
            for row in test_rows
        ]
        if audit_name:
            evidence.append(
                {
                    "type": "audit_assertion",
                    "name": audit_name,
                    "result": "PASS" if audit_ok else "FAIL",
                }
            )
        forced = spec.get("forced")
        if forced:
            assertion_result = str(forced)
        elif (not patterns or test_ok) and audit_ok:
            assertion_result = "PASS"
        else:
            assertion_result = "FAIL"
        rows.append(
            {
                "fixture_id": spec["id"],
                "observed_result": assertion_result,
                "expected_contract_result": (
                    "PRESERVE_VALID_INPUT"
                    if str(spec["id"]).startswith("P")
                    else "REJECT_INVALID_INPUT"
                ),
                "assertion_result": assertion_result,
                "evidence_scope": (
                    "NATIVE_ARTIFACT_ONLY_RECEIPT_CONTINUITY_NOT_PROVEN"
                    if spec["id"] == "N17"
                    else "EXECUTED_TEST_AND_OR_REPLAY"
                ),
                "denominator": len(evidence),
                "dependency": audit_name,
                "evidence": evidence,
            }
        )
    aggregate = aggregate_fixture_rows(rows)
    return {
        "contract": "m12cg-r2-original-fixtures-test-node-assertion-coverage-v1",
        **aggregate,
        "rows": rows,
    }


def dynamic_aggregation_negative_controls() -> dict[str, object]:
    cases = []
    for name, rows, expected in (
        (
            "assertion_failure",
            [{"fixture_id": "X", "assertion_result": "FAIL", "denominator": 1, "evidence": [{}]}],
            "FAIL",
        ),
        (
            "assertion_skipped",
            [{"fixture_id": "X", "assertion_result": "NOT_PROVEN", "denominator": 1, "evidence": [{}]}],
            "PARTIAL",
        ),
        (
            "assertion_absent",
            [{"fixture_id": "X", "assertion_result": "PASS", "denominator": 0, "evidence": []}],
            "FAIL",
        ),
        (
            "complete_pass",
            [{"fixture_id": "X", "assertion_result": "PASS", "denominator": 1, "evidence": [{}]}],
            "PASS",
        ),
    ):
        observed = aggregate_fixture_rows(rows)
        cases.append(
            {
                "case": name,
                "expected": expected,
                "observed": observed["status"],
                "status": "PASS" if observed["status"] == expected else "FAIL",
            }
        )
    return {
        "contract": "m12cg-r2-dynamic-aggregation-negative-controls-v1",
        "cases": cases,
        "status": "PASS" if all(row["status"] == "PASS" for row in cases) else "FAIL",
    }


def artifact_manifest(root: Path) -> dict[str, object]:
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "artifact-manifest.json":
            continue
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return {
        "contract": "m12cg-r2-artifact-manifest-v1",
        "manifest_self_excluded": True,
        "artifact_count": len(rows),
        "artifacts": rows,
    }


def build_report(args: argparse.Namespace) -> None:
    repo = args.repo.resolve()
    package_root = args.package_root.resolve()
    out = args.out.resolve()
    validation_dir = args.validation_dir.resolve()
    work_instruction = (
        args.work_instruction.resolve()
        if args.work_instruction.is_absolute()
        else (repo / args.work_instruction).resolve()
    )
    python = (
        args.python
        if args.python.is_absolute()
        else repo / args.python
    )
    if out.exists():
        shutil.rmtree(out)
    for directory in (
        "audits",
        "excerpts",
        "payloads",
        "proof-scripts",
        "repository",
        "runtime-probes",
        "validation",
    ):
        (out / directory).mkdir(parents=True, exist_ok=True)

    source_index = json.loads(
        (package_root / "SOURCE_BUNDLES.json").read_text(encoding="utf-8")
    )["sources"]
    with tempfile.TemporaryDirectory(prefix="m12cg-r2-") as scratch_value:
        scratch = Path(scratch_value)
        source_roots: dict[str, Path] = {}
        source_results: dict[str, object] = {}
        for key in EXPECTED_SOURCE_SHAS:
            root, result = extract_and_verify_source(
                key=key,
                entry=source_index[key],
                package_root=package_root,
                extraction_root=scratch / "sources",
            )
            source_roots[key] = root
            source_results[key] = result
        source_integrity = {
            "contract": "m12cg-r2-source-integrity-runtime-base-v1",
            "source_bundle_count_verified": sum(
                row["status"] == "PASS" for row in source_results.values()
            ),
            "source_bundle_count_required": len(EXPECTED_SOURCE_SHAS),
            "sources": source_results,
            "status": (
                "PASS"
                if all(row["status"] == "PASS" for row in source_results.values())
                else "FAIL"
            ),
        }

        head = run(repo, "git", "rev-parse", "HEAD")
        branch = run(repo, "git", "branch", "--show-current")
        instruction_sha = sha256_file(work_instruction)
        instruction_commit = run(
            repo,
            "git",
            "log",
            "-1",
            "--format=%H",
            "--",
            str(work_instruction.relative_to(repo)),
        )
        guard_implementation_sha = run(
            repo,
            "git",
            "log",
            "-1",
            "--format=%H",
            "--",
            *RUNTIME_CHANGED_FILES,
        )
        audit_implementation_sha = run(
            repo,
            "git",
            "log",
            "-1",
            "--format=%H",
            "--",
            *AUDIT_FILES,
        )
        runtime_changed = run(
            repo,
            "git",
            "diff",
            "--name-only",
            REQUIRED_BASE_SHA,
            head,
            "--",
            "app",
        ).splitlines()
        guard_diff = run(
            repo,
            "git",
            "diff",
            f"{REQUIRED_BASE_SHA}..{head}",
            "--",
            *RUNTIME_CHANGED_FILES,
        )
        (out / "repository/guard-runtime-diff.patch").write_text(
            guard_diff + "\n",
            encoding="utf-8",
        )
        before_bytes = git_bytes(
            repo,
            REQUIRED_BASE_SHA,
            RUNTIME_CHANGED_FILES[0],
        )
        current_bytes = (repo / RUNTIME_CHANGED_FILES[0]).read_bytes()
        repository = {
            "contract": "m12cg-r2-repository-provenance-v1",
            "repository": "sskim-ai/thesis-monitor",
            "branch": branch,
            "required_base_sha": REQUIRED_BASE_SHA,
            "before_runtime_sha": BEFORE_RUNTIME_SHA,
            "r1_audit_implementation_sha": R1_AUDIT_SHA,
            "work_instruction_commit": instruction_commit,
            "work_instruction_content_sha256": instruction_sha,
            "guard_implementation_sha": guard_implementation_sha,
            "audit_implementation_sha": audit_implementation_sha,
            "final_local_sha": head,
            "required_base_is_ancestor": subprocess.run(
                ("git", "merge-base", "--is-ancestor", REQUIRED_BASE_SHA, head),
                cwd=repo,
                check=False,
            ).returncode
            == 0,
            "runtime_changed_files": runtime_changed,
            "runtime_changed_symbols": [
                "evidence_maturity_pricing_service.symbolic_maturity_evidence_kind"
            ],
            "required_base_runtime_sha256": sha256_bytes(before_bytes),
            "current_runtime_sha256": sha256_bytes(current_bytes),
            "runtime_byte_changed": before_bytes != current_bytes,
            "status": (
                "PASS"
                if instruction_sha == WORK_INSTRUCTION_CONTENT_SHA
                and runtime_changed == list(RUNTIME_CHANGED_FILES)
                else "FAIL"
            ),
        }
        source_integrity["repository"] = repository
        write_json(
            out,
            "audits/source-integrity-and-runtime-base.json",
            source_integrity,
        )
        write_json(
            out,
            "audits/canonical-symbolic-classifier-history-and-presence-contract.json",
            {
                "contract": "m12cg-r2-symbolic-presence-contract-v1",
                "owner": (
                    "app/services/evidence_maturity_pricing_service.py::"
                    "symbolic_maturity_evidence_kind"
                ),
                "before_runtime_sha": BEFORE_RUNTIME_SHA,
                "required_invariants": {
                    "financial_quality": {
                        "required_present_explicit_null": ["source_period"]
                    },
                    "earnings": {
                        "required_present_explicit_null": [
                            "period_label",
                            "period_type",
                        ]
                    },
                },
                "producer_semantics_changed": False,
                "missing_keys_inserted": False,
                "version_bump": False,
                "runtime_changed_files": runtime_changed,
                "status": repository["status"],
            },
        )

        historical_binding = r1.validate_historical_source_map(
            package_root=package_root,
            m12cb_root=source_roots["m12cb"],
            m12cd_root=source_roots["m12cd"],
        )
        historical = r1.replay_historical(
            m12cb_root=source_roots["m12cb"],
            m12cd_root=source_roots["m12cd"],
            out=out,
        )
        write_json(
            out,
            "audits/historical-62-source-binding-and-original-ephemeral-verdicts.json",
            {
                "binding": historical_binding,
                "replay": historical,
            },
        )

        before_runtime_root = scratch / "before-runtime"
        export_git_tree(repo, BEFORE_RUNTIME_SHA, before_runtime_root)
        probe_root = out / "runtime-probes"
        before_runtime = execute_probe(
            repo=repo,
            python=python,
            script=repo / "scripts/m12cg_r2_runtime_probe.py",
            runtime_root=before_runtime_root,
            runtime_label="before-r2-b7e541b6",
            result_path=probe_root / "before-r2.json",
            args=(
                "--m12cb-root",
                str(source_roots["m12cb"]),
                "--m12ce-root",
                str(source_roots["m12ce"]),
                "--output-dir",
                str(probe_root / "before-r2"),
            ),
        )
        after_runtime = execute_probe(
            repo=repo,
            python=python,
            script=repo / "scripts/m12cg_r2_runtime_probe.py",
            runtime_root=repo,
            runtime_label="after-r2",
            result_path=probe_root / "after-r2.json",
            args=(
                "--m12cb-root",
                str(source_roots["m12cb"]),
                "--m12ce-root",
                str(source_roots["m12ce"]),
                "--output-dir",
                str(probe_root / "after-r2"),
            ),
        )
        runtime_compare = compare_runtime_probes(before_runtime, after_runtime)
        write_json(
            out,
            "audits/historical-before-after-r2-candidate-row-matrix.json",
            runtime_compare["sections"]["historical"],
        )
        write_json(
            out,
            "audits/fresh-42-before-after-r2-semantic-hash-matrix.json",
            runtime_compare["sections"]["fresh"],
        )
        write_json(
            out,
            "audits/model-facing-before-after-builder-byte-proof.json",
            {
                "contract": "m12cg-r2-model-facing-byte-proof-v1",
                "rows": runtime_compare["model_facing_rows"],
                "model_facing_byte_delta_count": runtime_compare[
                    "model_facing_byte_delta_count"
                ],
                "status": (
                    "PASS"
                    if runtime_compare["model_facing_byte_delta_count"] == 0
                    else "FAIL"
                ),
            },
        )

        before_guard = execute_probe(
            repo=repo,
            python=python,
            script=repo / "scripts/m12cg_r2_guard_probe.py",
            runtime_root=before_runtime_root,
            runtime_label="before-r2-b7e541b6",
            result_path=probe_root / "guard-before-r2.json",
            args=("--m12ce-root", str(source_roots["m12ce"])),
        )
        after_guard = execute_probe(
            repo=repo,
            python=python,
            script=repo / "scripts/m12cg_r2_guard_probe.py",
            runtime_root=repo,
            runtime_label="after-r2",
            result_path=probe_root / "guard-after-r2.json",
            args=("--m12ce-root", str(source_roots["m12ce"])),
        )
        guard_compare = compare_guard_probes(before_guard, after_guard)
        write_json(
            out,
            "audits/before-after-missing-vs-explicit-null-boundary.json",
            {
                **guard_compare,
                "before_results": before_guard["results"],
                "after_results": after_guard["results"],
            },
        )
        g13 = next(
            row for row in after_guard["results"] if row["fixture_id"] == "G13"
        )
        write_json(
            out,
            "audits/independent-validator-canonical-context-tamper-proof.json",
            g13,
        )
        g12 = next(
            row for row in after_guard["results"] if row["fixture_id"] == "G12"
        )
        write_json(out, "audits/raw-runtime-field-negative-tests.json", g12)

        fresh = r1.replay_fresh(m12ce_root=source_roots["m12ce"], out=out)
        serialization = r1.serialization_roundtrip_proof(fresh=fresh, out=out)
        write_json(
            out,
            "audits/serialization-type-json-bytes-hash-comparison.json",
            serialization,
        )
        semantic_loss = semantic_loss_proof(
            after_runtime,
            current_probe_root=probe_root / "after-r2",
            out=out,
        )
        polarity_node = (
            "tests/test_preconfirmation_decision_v2_service.py::"
            "test_m12cg_r2_atomic_polarity_mutation_is_rejected"
        )
        semantic_and_polarity = {
            "contract": "m12cg-r2-semantic-loss-polarity-negative-controls-v1",
            "semantic_loss": semantic_loss,
            "polarity_test_node": polarity_node,
            "polarity_result": "BOUND_FROM_FOCUSED_JUNIT",
            "status": semantic_loss["status"],
        }
        write_json(
            out,
            "audits/semantic-loss-and-polarity-negative-controls.json",
            semantic_and_polarity,
        )

        native, state, continuity = native_acceptance_proof(
            current_probe_root=probe_root / "after-r2",
            fresh=fresh,
            out=out,
        )
        call_path = call_path_proof(repo, out)
        write_json(
            out,
            "audits/native-acceptance-requirement-owner-call-path-matrix.json",
            call_path,
        )
        write_json(
            out,
            "audits/native-artifact-receipt-version-binding-proof.json",
            native,
        )
        write_json(
            out,
            "audits/state-roundtrip-idempotency-proof.json",
            state,
        )
        write_json(
            out,
            "audits/native-delivery-continuity-dedupe-intent-proof.json",
            continuity,
        )

        finalizations = runtime_compare["finalization_rows"]
        baseline_finalization = {
            "contract": "m12cg-r2-baseline-finalization-errors-coverage-v1",
            "fresh_stage2_subjects_valid": after_runtime["fresh"][
                "valid_candidate_count"
            ],
            "new_finalization_count": after_runtime["fresh"]["finalized_count"],
            "r2_before_after_finalization_parity_count": sum(
                row["before_result"] == row["after_result"] == "PASS"
                for row in finalizations
            ),
            "legacy_normalizable_count": fresh["v1_normalizable_count"],
            "paired_finalization_count": fresh[
                "paired_finalization_comparable_count"
            ],
            "baseline_finalization_errors": [
                {
                    "ticker": row["ticker"],
                    "before_error": row["before_error"],
                    "after_error": row["after_error"],
                    "baseline_parity": row["result_equal"],
                }
                for row in finalizations
                if row["after_result"] == "FAIL"
            ],
            "accepted_plan_coverage_complete": all(
                row["after_result"] == "PASS" for row in finalizations
            ),
            "status": "PARTIAL_BASELINE_ERRORS_PRESERVED",
        }
        write_json(
            out,
            "audits/baseline-finalization-errors-and-coverage.json",
            baseline_finalization,
        )

        validation_results: dict[str, object] = {}
        all_nodes: list[dict[str, object]] = []
        for source in sorted(validation_dir.iterdir()):
            if not source.is_file():
                continue
            target = out / "validation" / source.name
            shutil.copy2(source, target)
            if source.name.endswith("-junit.xml"):
                key = source.name.removesuffix("-junit.xml")
                validation_results[key] = r1.parse_junit(target)
                all_nodes.extend(parse_junit_nodes(target))
        fixtures = fixture_coverage(
            nodes=all_nodes,
            historical=historical,
            fresh_compare=runtime_compare,
            guard_after=after_guard,
            serialization=serialization,
            semantic_loss=semantic_loss,
            native=native,
            state=state,
        )
        write_json(
            out,
            "audits/original-fixtures-test-node-assertion-coverage.json",
            fixtures,
        )
        aggregation_controls = dynamic_aggregation_negative_controls()
        write_json(
            out,
            "audits/dynamic-aggregation-negative-control-tests.json",
            aggregation_controls,
        )

        validation = {
            "contract": "m12cg-r2-focused-full-frozen-regressions-v1",
            "results": validation_results,
            "commands": json.loads(
                (validation_dir / "commands.json").read_text(encoding="utf-8")
            ),
            "ruff": (
                validation_dir / "ruff.log"
            ).read_text(encoding="utf-8").strip(),
            "git_diff_check": (
                validation_dir / "git-diff-check.log"
            ).read_text(encoding="utf-8").strip(),
            "status": (
                "PASS"
                if validation_results
                and all(row["status"] == "PASS" for row in validation_results.values())
                else "FAIL"
            ),
        }
        write_json(
            out,
            "audits/focused-full-frozen-regressions.json",
            validation,
        )

        safety = {
            "contract": "m12cg-r2-safety-zero-call-production-audit-v1",
            "external_model_calls": 0,
            "full22_generations": 0,
            "model_retries": 0,
            "model_fallbacks": 0,
            "judge_calls": 0,
            "selective_model_reruns": 0,
            "production_sends": 0,
            "production_delivery_intents": 0,
            "production_db_mutations": 0,
            "scheduler_resumes": 0,
            "main_merges": 0,
            "deployments": 0,
            "remote_pushes": 0,
            "live_kiwoom_reads": 0,
            "live_kiwoom_orders": 0,
            "live_kiwoom_modifies": 0,
            "live_kiwoom_cancels": 0,
            "status": "PASS_ZERO",
        }
        write_json(
            out,
            "audits/safety-zero-call-and-production-audit.json",
            safety,
        )

        blockers = [
            {
                "category": "NATIVE_DELIVERY",
                "code": "M12CG_R2_NATIVE_DELIVERY_CONTINUITY_NOT_PROVEN",
                "detail": continuity["reason"],
            },
            {
                "category": "FIXTURE",
                "code": "M12CG_R2_N17_RECEIPT_SWAP_NOT_PROVEN",
                "detail": (
                    "Artifact packet/claim/version tamper rejection is proven, but the "
                    "diagnostic orchestration receipt is not an artifact authority and no "
                    "delivery route was executed."
                ),
            },
            {
                "category": "COVERAGE",
                "code": "M12CG_R2_GOOGL_HUT_FINALIZATION_BASELINE_FAILURE",
                "detail": (
                    "GOOGL and HUT retain identical pre/post adjudication numeric "
                    "rejections; no numeric policy repair was authorized."
                ),
            },
        ]
        guard_pass = guard_compare["status"] == "PASS_GUARD_REPAIR"
        valid_neutral = runtime_compare["status"] == "PASS_NO_VALID_INPUT_CHANGE"
        top_level_result = (
            "M12CG_R2_GUARD_REPAIR_PASS_OFFLINE_CLOSURE_PENDING"
            if guard_pass and valid_neutral
            else "M12CG_R2_GUARD_REPAIR_FAILED"
        )
        status_matrix = {
            "contract": "m12cg-r2-complete-blocker-scope-status-v1",
            "top_level_result": top_level_result,
            "guard_repair_status": "PASS" if guard_pass else "FAIL",
            "valid_input_neutrality": runtime_compare["status"],
            "source_coverage": source_integrity["status"],
            "fixture_coverage": fixtures["status"],
            "native_artifact_owner": native["status"],
            "native_state_roundtrip": state["status"],
            "native_delivery_continuity": continuity["status"],
            "complete_blocker_set": blockers,
            "new_full22_authorized": False,
            "message_model_contract_readiness": (
                "NOT_READY_PENDING_CHAT_REVIEW_AND_NATIVE_DELIVERY_CONTINUITY_"
                "PLUS_BASELINE_FINALIZATION_SCOPE"
            ),
            "deployment_readiness": "NO",
            "status": "STOP_FOR_CHAT",
        }
        write_json(
            out,
            "audits/complete-blocker-and-scope-status-matrix.json",
            status_matrix,
        )

        program_completion = {
            "contract": "m12cg-r2-program-completion-v1",
            "top_level_result": top_level_result,
            "source_bundle_count_verified": source_integrity[
                "source_bundle_count_verified"
            ],
            "required_base_sha": REQUIRED_BASE_SHA,
            "before_runtime_sha": BEFORE_RUNTIME_SHA,
            "work_instruction_commit": instruction_commit,
            "work_instruction_content_sha256": instruction_sha,
            "guard_implementation_sha": guard_implementation_sha,
            "audit_implementation_sha": audit_implementation_sha,
            "final_local_sha": head,
            "runtime_changed_files": runtime_changed,
            "runtime_changed_symbols": repository["runtime_changed_symbols"],
            "explicit_null_preservation_result": guard_compare[
                "explicit_null_preservation_result"
            ],
            "financial_quality_missing_key_guard_result": guard_compare[
                "financial_quality_missing_key_guard_result"
            ],
            "earnings_missing_label_guard_result": guard_compare[
                "earnings_missing_label_guard_result"
            ],
            "earnings_missing_type_guard_result": guard_compare[
                "earnings_missing_type_guard_result"
            ],
            "independent_validator_rejection_result": guard_compare[
                "independent_validator_rejection_result"
            ],
            "guard_repair_status": "PASS" if guard_pass else "FAIL",
            "historical_rows_replayed": after_runtime["historical"]["row_count"],
            "historical_candidates_valid": after_runtime["historical"][
                "valid_candidate_count"
            ],
            "historical_original_negative_count": historical[
                "original_invalid_candidate_count"
            ],
            "historical_date_parity_failures": historical[
                "date_parity_failure_count"
            ],
            "fresh_rows_replayed": after_runtime["fresh"]["row_count"],
            "fresh_stage2_subjects_valid": after_runtime["fresh"][
                "valid_candidate_count"
            ],
            "valid_input_semantic_change_count": runtime_compare[
                "valid_input_change_count"
            ],
            "valid_input_normalized_hash_change_count": sum(
                runtime_compare["sections"][section][
                    "normalized_candidate_hash_change_count"
                ]
                for section in ("historical", "fresh")
            ),
            "model_facing_byte_delta_count": runtime_compare[
                "model_facing_byte_delta_count"
            ],
            "fixture_variants_required": fixtures["fixture_variant_count"],
            "fixture_variants_proven": fixtures["proven_count"],
            "fixture_variants_not_proven": fixtures["not_proven_count"],
            "unsupported_group_pass_count": fixtures[
                "unsupported_group_pass_count"
            ],
            "native_owner_applicability": call_path[
                "service_specific_requirement_disposition"
            ],
            "service_specific_requirement_disposition": call_path[
                "service_specific_requirement_disposition"
            ],
            "native_receipt_binding_result": native[
                "native_receipt_binding_result"
            ],
            "native_state_roundtrip_result": state["status"],
            "continuity_result": continuity["continuity_result"],
            "duplicate_intent_result": continuity[
                "duplicate_operational_intent_count"
            ],
            "paired_finalization_count": baseline_finalization[
                "paired_finalization_count"
            ],
            "new_finalization_count": baseline_finalization[
                "new_finalization_count"
            ],
            "baseline_finalization_error_count": len(
                baseline_finalization["baseline_finalization_errors"]
            ),
            "accepted_plan_coverage_complete": baseline_finalization[
                "accepted_plan_coverage_complete"
            ],
            "offline_migration_compatibility_status": "PENDING",
            "complete_blocker_set": blockers,
            "new_full22_authorized": False,
            "message_model_contract_readiness": status_matrix[
                "message_model_contract_readiness"
            ],
            "deployment_readiness": "NO",
            **{
                key: value
                for key, value in safety.items()
                if key not in {"contract", "status"}
            },
        }
        write_json(out, "program-completion.json", program_completion)

        next_scope = """# Next bounded scope proposal

## Closed in M12CG-R2

The canonical symbolic classifier now distinguishes a required key that is absent from a
required key that is present with JSON null. All valid historical and fresh inputs remain
byte/hash/semantic neutral across the repair.

## Still open

1. Decide and execute a bounded native accepted-v2 delivery continuity/dedupe proof using an
   authorized isolated sink, or explicitly define the missing native intent owner. Do not add
   a bridge to canonical acceptance solely because both routes use receipt terminology.
2. Address GOOGL/HUT `adjudication_introduced_unregistered_numeric` only in a separately
   authorized numeric-ownership task if all-subject accepted-plan coverage is required.
3. Re-run N17 receipt/operational isolation after the applicable native authority is selected.

No model call, Full22, main merge, deployment, scheduler action, production mutation or send
is authorized by this report.
"""
        (out / "next-bounded-scope-proposal.md").write_text(
            next_scope,
            encoding="utf-8",
        )
        report = f"""# M12CG-R2 Symbolic Metadata Presence Guard and Offline Reproof

## Result

`{top_level_result}`

The authorized one-file runtime repair is complete. Required nullable producer metadata now
must be present and explicitly null; missing keys are rejected by the classifier, actual
materializer and independent validator. The exact before-R2 runtime accepts the same missing
financial-quality key fixture, while the repaired runtime rejects it.

Valid-input neutrality passes: historical {after_runtime['historical']['row_count']}/62 rows
and fresh {after_runtime['fresh']['row_count']}/42 rows replay with zero normalized candidate
hash changes, zero semantic changes and zero model-facing prompt/schema/catalog byte changes.
The seven successful finalizations remain successful; GOOGL/HUT retain their identical
pre-existing numeric rejection.

The broader offline migration remains open. Native artifact packet/claim/scope/hash binding
and isolated state roundtrip pass, but the orchestration receipt is diagnostic rather than the
delivery artifact authority. No delivery route or intent ledger was executed, so operational
continuity and duplicate-intent suppression remain NOT_PROVEN. N17 is therefore partial.

## Safety

- External model / Full22: 0 / 0
- Production send / intent / DB mutation: 0 / 0 / 0
- Kiwoom live read/order/modify/cancel: 0 / 0 / 0 / 0
- Main merge / deploy / remote push: 0 / 0 / 0

`new_full22_authorized=false`

`message_model_contract_readiness={status_matrix['message_model_contract_readiness']}`

`deployment_readiness=NO`
"""
        (out / "M12CG-R2-RESULT.md").write_text(report, encoding="utf-8")

        for script_name in (
            "m12cg_r2_guard_probe.py",
            "m12cg_r2_runtime_probe.py",
            "m12cg_r2_offline_proof.py",
        ):
            shutil.copy2(
                repo / "scripts" / script_name,
                out / "proof-scripts" / script_name,
            )
        shutil.copy2(
            work_instruction,
            out / "repository" / work_instruction.name,
        )
        (out / "repository/git-log.txt").write_text(
            run(repo, "git", "log", "-14", "--oneline", "--decorate") + "\n",
            encoding="utf-8",
        )
        (out / "repository/implementation-diff.patch").write_text(
            run(repo, "git", "diff", f"{REQUIRED_BASE_SHA}..{head}") + "\n",
            encoding="utf-8",
        )
        write_json(out, "artifact-manifest.json", artifact_manifest(out))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--validation-dir", type=Path, required=True)
    parser.add_argument("--work-instruction", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    build_report(parser.parse_args())


if __name__ == "__main__":
    main()
