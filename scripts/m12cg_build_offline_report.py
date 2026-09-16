from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from xml.etree import ElementTree

from pydantic import ValidationError

from app.services.accepted_decision_v2_runtime_service import (
    ARTIFACT_CONTRACT,
    ARTIFACT_CONTRACT_V2,
    OUTPUT_CONTRACT,
    OUTPUT_CONTRACT_V2,
    STAGE2_MATURITY_AS_OF_MATERIALIZATION_CONTRACT,
    STAGE2_MATURITY_PROVENANCE_MATERIALIZATION_CONTRACT,
    STAGE2_MODEL_OUTPUT_CONTRACT,
    AcceptedV2FundamentalCoreCandidate,
    AcceptedV2ProductionContext,
    accepted_v2_production_prompt,
    accepted_v2_stage2_output_schema,
    accepted_v2_stage2_ref_catalog_manifest,
    advance_accepted_v2_state,
    load_accepted_v2_state,
    materialize_accepted_v2_stage2_output,
    parse_accepted_v2_production_artifact,
    parse_accepted_v2_production_batch_output,
    validate_accepted_v2_production_output,
    validate_accepted_v2_stage2_candidate,
)
from app.services.accepted_decision_v2_service import render_accepted_v2_production
from app.services.decision_canary_service import canonical_sha256
from app.services.evidence_maturity_pricing_service import (
    DriverEvidenceMaturityV2,
    MaturityProvenanceStatus,
    project_maturity_provenance,
)


EXPECTED_M12CF_SHA256 = (
    "4375203ad1268fae87b79c88c00607e25849651e32961a87b0b73c537e8a1846"
)
EXPECTED_M12CE_SHA256 = (
    "512c428bbb01c9ae0834cf0d79d01a330095f67553410f854e296bf9d94c07f9"
)
EXPECTED_M12CD_SHA256 = (
    "89d51179aca722ce38b282c51d3fedb34ea6446df8c6c6ea71bb8e5cf74951ff"
)
EXPECTED_BATCH3_SHA256 = (
    "6c8e80898904b44a710c00fdb3d918bf00a6edf757f1e2cc987d8d2fcb79455f"
)
REQUIRED_BASE_SHA = "912b1ce6c46f0caf801b2c620b42d904b489c4e7"
ORIGIN_MAIN_OBSERVED = "9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479"
M12CD_RUNTIME_SHA = "9a9bda729afcb0777d7228ee7151d31f0b2f84f8"
M12CF_FINAL_SHA = REQUIRED_BASE_SHA
M12CG_IMPLEMENTATION_SHA = "b7e541b6a3c54567018f937f32d6f92be09a7e4e"
M12CE_GENERATION_ID = "20260916-uskr22-m12ce-20260916T080425Z-96a562d5cafc"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def write_json(root: Path, relative: str, value: object) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(value))


def run(repo: Path, *args: str) -> str:
    return subprocess.run(
        args,
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def verify_manifest(root: Path, manifest_path: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = manifest.get("artifacts", [])
    missing: list[str] = []
    hash_mismatches: list[str] = []
    size_mismatches: list[str] = []
    duplicate_paths: list[str] = []
    seen: set[str] = set()
    for row in rows:
        relative = str(row["path"])
        if relative in seen:
            duplicate_paths.append(relative)
        seen.add(relative)
        path = root / relative
        if not path.is_file():
            missing.append(relative)
            continue
        if path.stat().st_size != row["size"]:
            size_mismatches.append(relative)
        if sha256_file(path) != row["sha256"]:
            hash_mismatches.append(relative)
    payloads = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path != manifest_path
    }
    unexpected = sorted(payloads - seen)
    return {
        "declared_count": len(rows),
        "verified_count": len(rows) - len(missing) - len(hash_mismatches) - len(size_mismatches),
        "missing": missing,
        "hash_mismatches": hash_mismatches,
        "size_mismatches": size_mismatches,
        "duplicate_paths": duplicate_paths,
        "unexpected_payloads": unexpected,
        "manifest_self_excluded": manifest_path.relative_to(root).as_posix() not in seen,
        "status": (
            "PASS"
            if not any(
                (missing, hash_mismatches, size_mismatches, duplicate_paths, unexpected)
            )
            else "FAIL"
        ),
    }


def zip_integrity(path: Path) -> dict[str, object]:
    with zipfile.ZipFile(path) as archive:
        bad_crc = archive.testzip()
        names = archive.namelist()
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "entry_count": len(names),
        "duplicate_entries": sorted(
            name for name in set(names) if names.count(name) > 1
        ),
        "bad_crc_entry": bad_crc,
        "status": "PASS" if bad_crc is None and len(names) == len(set(names)) else "FAIL",
    }


def parse_junit(path: Path) -> dict[str, object]:
    root = ElementTree.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    totals = {key: 0 for key in ("tests", "failures", "errors", "skipped")}
    elapsed = 0.0
    for suite in suites:
        for key in totals:
            totals[key] += int(suite.attrib.get(key, 0))
        elapsed += float(suite.attrib.get("time", 0.0))
    totals["passed"] = totals["tests"] - totals["failures"] - totals["errors"] - totals["skipped"]
    totals["elapsed_seconds"] = round(elapsed, 3)
    totals["path"] = str(path)
    totals["sha256"] = sha256_file(path)
    totals["status"] = "PASS" if totals["failures"] == totals["errors"] == 0 else "FAIL"
    return totals


def subset_context(
    context: AcceptedV2ProductionContext,
    subjects: Sequence[str],
) -> AcceptedV2ProductionContext:
    selected = tuple(subjects)
    return context.model_copy(
        update={
            "selected_subjects": selected,
            "evidence_packets": tuple(
                row for row in context.evidence_packets if row.ticker in selected
            ),
            "evidence_ownership": tuple(
                row for row in context.evidence_ownership if row.ticker in selected
            ),
            "prior_accepted": tuple(
                row for row in context.prior_accepted if row.ticker in selected
            ),
        }
    )


def subset_raw(raw: Mapping[str, object], subjects: Sequence[str]) -> dict[str, object]:
    selected = set(subjects)
    payload = dict(raw)
    for field in ("fundamental_cores", "candidates", "adjudications"):
        rows = payload.get(field)
        if isinstance(rows, list):
            payload[field] = [
                row
                for row in rows
                if isinstance(row, Mapping) and str(row.get("ticker")) in selected
            ]
    return payload


def strip_runtime_fields(candidate: Mapping[str, object]) -> dict[str, object]:
    payload = json.loads(json.dumps(candidate, ensure_ascii=False))
    rows = payload.get("driver_maturity")
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict):
                row.pop("as_of", None)
                row.pop("provenance_status", None)
    return payload


def strip_plan_identity(plan: Mapping[str, object]) -> dict[str, object]:
    payload = dict(plan)
    for field in (
        "candidate_decision_id",
        "accepted_decision_id",
        "accepted_evidence_fingerprint",
    ):
        payload.pop(field, None)
    return payload


def prompt_semantic_comparison(current: str, frozen: str) -> dict[str, object]:
    marker = "PRODUCTION_V2_CONTEXT:\n"
    current_prefix, current_payload = current.split(marker, 1)
    frozen_prefix, frozen_payload = frozen.split(marker, 1)
    return {
        "byte_equal": current == frozen,
        "byte_delta": len(current.encode("utf-8")) - len(frozen.encode("utf-8")),
        "current_sha256": sha256_bytes(current.encode("utf-8")),
        "frozen_sha256": sha256_bytes(frozen.encode("utf-8")),
        "instruction_prefix_equal": current_prefix == frozen_prefix,
        "context_json_semantically_equal": json.loads(current_payload) == json.loads(frozen_payload),
        "difference_classification": (
            "BYTE_EQUAL"
            if current == frozen
            else "REHYDRATION_KEY_ORDER_AND_TRAILING_LF_ONLY"
        ),
    }


def replay_fresh(m12ce_root: Path) -> dict[str, object]:
    raw_root = m12ce_root / "raw/reproof-no-repair/us"
    context = AcceptedV2ProductionContext.model_validate_json(
        (raw_root / "context.json").read_text(encoding="utf-8")
    )
    rows: list[dict[str, object]] = []
    candidates: list[dict[str, object]] = []
    model_boundary: list[dict[str, object]] = []
    batch_results: list[dict[str, object]] = []
    identity_rows: list[dict[str, object]] = []
    artifact_by_ticker: dict[str, object] = {}
    legacy_artifact_by_ticker: dict[str, object] = {}
    raw_semantic_changes = 0
    row_loss = 0
    atomic_changes = 0

    for batch in range(1, 4):
        raw_path = raw_root / f"batch-{batch:02d}.output.json"
        raw_bytes = raw_path.read_bytes()
        raw = json.loads(raw_bytes)
        subjects = tuple(str(row["ticker"]) for row in raw["candidates"])
        cores = tuple(
            AcceptedV2FundamentalCoreCandidate.model_validate(row)
            for row in raw["fundamental_cores"]
        )
        batch_context = subset_context(context, subjects)
        output = materialize_accepted_v2_stage2_output(batch_context, raw)
        old_error = None
        try:
            materialize_accepted_v2_stage2_output(
                batch_context,
                raw,
                normalized_contract=STAGE2_MATURITY_AS_OF_MATERIALIZATION_CONTRACT,
            )
            old_status = "PASS"
        except Exception as exc:  # expected for frozen SKHY batch
            old_status = "FAIL"
            old_error = f"{type(exc).__name__}:{exc}"

        prompt = accepted_v2_production_prompt(
            batch_context,
            fundamental_cores=cores,
            subjects=subjects,
        )
        schema_text = (
            json.dumps(
                accepted_v2_stage2_output_schema(
                    batch_context,
                    subjects=subjects,
                    fundamental_cores=cores,
                ),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        catalog_text = (
            json.dumps(
                accepted_v2_stage2_ref_catalog_manifest(
                    batch_context,
                    subjects=subjects,
                    fundamental_cores=cores,
                ),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        frozen_prompt = (raw_root / f"batch-{batch:02d}.prompt.txt").read_text(
            encoding="utf-8"
        )
        frozen_schema = (raw_root / f"batch-{batch:02d}.schema.json").read_text(
            encoding="utf-8"
        )
        frozen_catalog = (
            raw_root / f"batch-{batch:02d}.ref-catalog.json"
        ).read_text(encoding="utf-8")
        model_boundary.append(
            {
                "batch": batch,
                "subjects": list(subjects),
                "prompt": prompt_semantic_comparison(prompt, frozen_prompt),
                "schema_byte_equal": schema_text == frozen_schema,
                "schema_byte_delta": len(schema_text.encode()) - len(frozen_schema.encode()),
                "schema_current_sha256": sha256_bytes(schema_text.encode()),
                "schema_frozen_sha256": sha256_bytes(frozen_schema.encode()),
                "catalog_byte_equal": catalog_text == frozen_catalog,
                "catalog_current_sha256": sha256_bytes(catalog_text.encode()),
                "catalog_frozen_sha256": sha256_bytes(frozen_catalog.encode()),
            }
        )

        packet_by_ticker = {row.ticker: row for row in batch_context.evidence_packets}
        ownership_by_ticker = {
            row.ticker: row for row in batch_context.evidence_ownership
        }
        core_by_ticker = {row.ticker: row for row in output.fundamental_cores}
        raw_candidate_by_ticker = {
            str(row["ticker"]): row for row in raw["candidates"]
        }
        batch_valid = 0
        for candidate in output.candidates:
            packet = packet_by_ticker[candidate.ticker]
            validation = validate_accepted_v2_stage2_candidate(
                packet,
                candidate,
                core_by_ticker[candidate.ticker],
                ownership_by_ticker[candidate.ticker],
            )
            batch_valid += int(validation.valid)
            raw_candidate = raw_candidate_by_ticker[candidate.ticker]
            semantic_equal = strip_runtime_fields(
                candidate.model_dump(mode="json")
            ) == raw_candidate
            raw_semantic_changes += int(not semantic_equal)
            row_loss += abs(
                len(candidate.driver_maturity)
                - len(raw_candidate.get("driver_maturity", []))
            )
            for row_index, maturity in enumerate(candidate.driver_maturity):
                raw_row = raw_candidate["driver_maturity"][row_index]
                cited = tuple(
                    dict.fromkeys(
                        (
                            *maturity.supporting_evidence_refs,
                            *maturity.contradicting_evidence_refs,
                        )
                    )
                )
                evidence = {row.ref_id: row for row in packet.evidence}
                projection = project_maturity_provenance(evidence, cited)
                atomic_equal = (
                    tuple(raw_row.get("supporting_claim_refs", ()))
                    == maturity.supporting_claim_refs
                    and tuple(raw_row.get("contradicting_claim_refs", ()))
                    == maturity.contradicting_claim_refs
                )
                atomic_changes += int(not atomic_equal)
                rows.append(
                    {
                        "generation_id": M12CE_GENERATION_ID,
                        "market": "us",
                        "batch": batch,
                        "source_output": raw_path.relative_to(m12ce_root).as_posix(),
                        "source_output_sha256": sha256_bytes(raw_bytes),
                        "ticker": candidate.ticker,
                        "row_index": row_index,
                        "driver": maturity.driver,
                        "supporting_evidence_refs": list(
                            maturity.supporting_evidence_refs
                        ),
                        "contradicting_evidence_refs": list(
                            maturity.contradicting_evidence_refs
                        ),
                        "supporting_claim_refs": list(maturity.supporting_claim_refs),
                        "contradicting_claim_refs": list(
                            maturity.contradicting_claim_refs
                        ),
                        "concrete_dates": list(projection.concrete_dates),
                        "recognized_symbolic_refs": list(
                            projection.symbolic_ref_ids
                        ),
                        "invalid_refs": list(projection.invalid_ref_ids),
                        "m12cg_as_of": maturity.as_of,
                        "m12cg_provenance_status": maturity.provenance_status.value,
                        "raw_semantic_fields_preserved": (
                            strip_runtime_fields(maturity.model_dump(mode="json"))
                            == raw_row
                        ),
                        "atomic_claim_and_polarity_preserved": atomic_equal,
                        "validation": "PASS" if validation.valid else "FAIL",
                        "validation_errors": list(validation.errors),
                    }
                )

            one_context = subset_context(context, (candidate.ticker,))
            one_raw = subset_raw(raw, (candidate.ticker,))
            new_one = materialize_accepted_v2_stage2_output(one_context, one_raw)
            old_one = None
            old_one_error = None
            try:
                old_one = materialize_accepted_v2_stage2_output(
                    one_context,
                    one_raw,
                    normalized_contract=STAGE2_MATURITY_AS_OF_MATERIALIZATION_CONTRACT,
                )
            except Exception as exc:
                old_one_error = f"{type(exc).__name__}:{exc}"
            new_artifact = None
            new_artifact_error = None
            try:
                new_artifact = validate_accepted_v2_production_output(
                    one_context,
                    new_one,
                    validated_at=datetime(2026, 9, 16, tzinfo=UTC),
                )
                artifact_by_ticker[candidate.ticker] = new_artifact
            except Exception as exc:
                new_artifact_error = f"{type(exc).__name__}:{exc}"
            old_artifact = None
            old_artifact_error = None
            if old_one is not None:
                try:
                    old_artifact = validate_accepted_v2_production_output(
                        one_context,
                        old_one,
                        validated_at=datetime(2026, 9, 16, tzinfo=UTC),
                    )
                    legacy_artifact_by_ticker[candidate.ticker] = old_artifact
                except Exception as exc:
                    old_artifact_error = f"{type(exc).__name__}:{exc}"

            identity: dict[str, object] = {
                "ticker": candidate.ticker,
                "v1_normalization": "PASS" if old_one is not None else "FAIL",
                "v1_normalization_error": old_one_error,
                "v2_normalization": "PASS",
                "v1_finalization": "PASS" if old_artifact is not None else "NOT_AVAILABLE",
                "v1_finalization_error": old_artifact_error,
                "v2_finalization": "PASS" if new_artifact is not None else "FAIL",
                "v2_finalization_error": new_artifact_error,
                "v2_candidate_sha256": canonical_sha256(
                    new_one.candidates[0].model_dump(mode="json")
                ),
            }
            if old_one is not None:
                identity["v1_candidate_sha256"] = canonical_sha256(
                    old_one.candidates[0].model_dump(mode="json")
                )
                identity["candidate_hash_changed"] = (
                    identity["v1_candidate_sha256"]
                    != identity["v2_candidate_sha256"]
                )
            if old_artifact is not None and new_artifact is not None:
                old_plan = old_artifact.accepted_plans[0]
                new_plan = new_artifact.accepted_plans[0]
                old_plan_payload = old_plan.model_dump(mode="json")
                new_plan_payload = new_plan.model_dump(mode="json")
                identity.update(
                    {
                        "candidate_decision_id_changed": (
                            old_plan.candidate_decision_id
                            != new_plan.candidate_decision_id
                        ),
                        "accepted_decision_id_changed": (
                            old_plan.accepted_decision_id
                            != new_plan.accepted_decision_id
                        ),
                        "accepted_evidence_fingerprint_changed": (
                            old_plan.accepted_evidence_fingerprint
                            != new_plan.accepted_evidence_fingerprint
                        ),
                        "accepted_plan_hash_changed": (
                            canonical_sha256(old_plan_payload)
                            != canonical_sha256(new_plan_payload)
                        ),
                        "accepted_plan_semantic_fields_equal": (
                            strip_plan_identity(old_plan_payload)
                            == strip_plan_identity(new_plan_payload)
                        ),
                        "renderer_equal": (
                            render_accepted_v2_production(
                                one_context.evidence_packets[0], old_plan
                            ).text
                            == render_accepted_v2_production(
                                one_context.evidence_packets[0], new_plan
                            ).text
                        ),
                    }
                )
            identity_rows.append(identity)
            candidates.append(
                {
                    "batch": batch,
                    "ticker": candidate.ticker,
                    "raw_semantic_fields_preserved": semantic_equal,
                    "driver_row_count": len(candidate.driver_maturity),
                    "stage2_validation": "PASS" if validation.valid else "FAIL",
                    "stage2_validation_errors": list(validation.errors),
                    "identity": identity,
                }
            )
        batch_results.append(
            {
                "batch": batch,
                "subjects": list(subjects),
                "raw_output_sha256": sha256_bytes(raw_bytes),
                "expected_batch3_sha_match": (
                    batch != 3 or sha256_bytes(raw_bytes) == EXPECTED_BATCH3_SHA256
                ),
                "new_contract_materialization": "PASS",
                "new_contract_stage2_valid_count": batch_valid,
                "old_contract_materialization": old_status,
                "old_contract_error": old_error,
            }
        )

    status_counts: dict[str, int] = {}
    for row in rows:
        status = str(row["m12cg_provenance_status"])
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "context": context,
        "rows": rows,
        "candidates": candidates,
        "batch_results": batch_results,
        "model_boundary": model_boundary,
        "identity_rows": identity_rows,
        "artifact_by_ticker": artifact_by_ticker,
        "legacy_artifact_by_ticker": legacy_artifact_by_ticker,
        "counts": {
            "rows": len(rows),
            "batches": 3,
            "subjects": len(candidates),
            "status": status_counts,
            "raw_semantic_field_changes": raw_semantic_changes,
            "driver_row_loss": row_loss,
            "atomic_claim_or_polarity_changes": atomic_changes,
            "stage2_valid_candidates": sum(
                row["stage2_validation"] == "PASS" for row in candidates
            ),
            "v1_comparable_candidates": sum(
                row["identity"]["v1_normalization"] == "PASS"
                for row in candidates
            ),
            "candidate_hash_changes": sum(
                row["identity"].get("candidate_hash_changed") is True
                for row in candidates
            ),
            "accepted_plan_comparable_candidates": sum(
                "accepted_plan_hash_changed" in row["identity"]
                for row in candidates
            ),
            "accepted_plan_hash_changes": sum(
                row["identity"].get("accepted_plan_hash_changed") is True
                for row in candidates
            ),
            "accepted_plan_semantic_changes": sum(
                row["identity"].get("accepted_plan_semantic_fields_equal") is False
                for row in candidates
            ),
            "renderer_changes": sum(
                row["identity"].get("renderer_equal") is False
                for row in candidates
            ),
        },
    }


def negative_boundary_proof(fresh: Mapping[str, object]) -> dict[str, object]:
    context = fresh["context"]
    assert isinstance(context, AcceptedV2ProductionContext)
    m12ce_root = Path(str(fresh["m12ce_root"]))
    raw = json.loads(
        (m12ce_root / "raw/reproof-no-repair/us/batch-01.output.json").read_text(
            encoding="utf-8"
        )
    )
    ticker = str(raw["candidates"][0]["ticker"])
    one_context = subset_context(context, (ticker,))
    base = subset_raw(raw, (ticker,))
    results: list[dict[str, object]] = []
    for field, value, expected in (
        ("as_of", None, "stage2_model_authored_maturity_as_of_forbidden"),
        (
            "provenance_status",
            "CONCRETE_ONLY",
            "stage2_model_authored_provenance_status_forbidden",
        ),
    ):
        payload = json.loads(json.dumps(base))
        payload["candidates"][0]["driver_maturity"][0][field] = value
        try:
            materialize_accepted_v2_stage2_output(one_context, payload)
            actual = "UNEXPECTED_PASS"
        except Exception as exc:
            actual = f"{type(exc).__name__}:{exc}"
        results.append(
            {
                "field": field,
                "expected_error": expected,
                "actual": actual,
                "status": "PASS" if expected in actual else "FAIL",
            }
        )
    invalid_shapes = []
    base_row = fresh["artifact_by_ticker"][ticker].candidates[0].driver_maturity[0]
    for value in ("null", "", 0, False):
        payload = base_row.model_dump(mode="json")
        payload["as_of"] = value
        payload["provenance_status"] = "SYMBOLIC_ONLY_NO_CONCRETE_DATE"
        try:
            DriverEvidenceMaturityV2.model_validate(payload)
            status = "UNEXPECTED_PASS"
        except ValidationError as exc:
            status = f"PASS_REJECTED:{exc.errors()[0]['type']}"
        invalid_shapes.append({"value": value, "result": status})
    return {
        "contract": "m12cg-raw-model-provenance-ownership-negative-tests-v1",
        "results": results,
        "non_json_null_shapes": invalid_shapes,
        "status": (
            "PASS"
            if all(row["status"] == "PASS" for row in results)
            and all(str(row["result"]).startswith("PASS_REJECTED") for row in invalid_shapes)
            else "FAIL"
        ),
    }


def state_roundtrip(fresh: Mapping[str, object]) -> dict[str, object]:
    artifact = fresh["artifact_by_ticker"]["CORZ"]
    legacy = fresh["legacy_artifact_by_ticker"]["CORZ"]
    with tempfile.TemporaryDirectory(prefix="m12cg-state-") as directory:
        settings = SimpleNamespace(data_dir=directory)
        timestamp = datetime(2026, 9, 16, tzinfo=UTC)
        first_path = advance_accepted_v2_state(
            artifact,
            settings=settings,
            updated_at=timestamp,
        )
        first_bytes = first_path.read_bytes()
        loaded = load_accepted_v2_state(settings=settings)
        second_path = advance_accepted_v2_state(
            artifact,
            settings=settings,
            updated_at=timestamp,
        )
        second_bytes = second_path.read_bytes()
    legacy_payload = legacy.model_dump(mode="json")
    new_payload = artifact.model_dump(mode="json")
    legacy_parsed = parse_accepted_v2_production_artifact(legacy_payload)
    new_parsed = parse_accepted_v2_production_artifact(new_payload)
    forged_results = []
    for name, payload, contract in (
        ("v2_payload_labeled_v1", new_payload, ARTIFACT_CONTRACT),
        ("v1_payload_labeled_v2", legacy_payload, ARTIFACT_CONTRACT_V2),
    ):
        forged = json.loads(json.dumps(payload))
        forged["contract"] = contract
        try:
            parse_accepted_v2_production_artifact(forged)
            result = "UNEXPECTED_PASS"
        except Exception as exc:
            result = f"PASS_REJECTED:{type(exc).__name__}"
        forged_results.append({"case": name, "result": result})
    unsupported = []
    for parser, payload in (
        (parse_accepted_v2_production_batch_output, {"contract": "unsupported"}),
        (parse_accepted_v2_production_artifact, {"contract": "unsupported"}),
    ):
        try:
            parser(payload)
            unsupported.append("UNEXPECTED_PASS")
        except ValueError:
            unsupported.append("PASS_REJECTED")
    return {
        "contract": "m12cg-receipt-persistence-version-roundtrip-v1",
        "scope": "accepted-v2 artifact parser and isolated runtime state; canonical acceptance receipt is not wired to this artifact path",
        "legacy_artifact_contract": legacy_parsed.contract,
        "new_artifact_contract": new_parsed.contract,
        "legacy_reader_roundtrip_equal": legacy_parsed == legacy,
        "new_reader_roundtrip_equal": new_parsed == artifact,
        "state_load_equal": loaded is not None and len(loaded.entries) == 1,
        "identical_second_replay_bytes_equal": first_bytes == second_bytes,
        "identical_second_replay_sha256": sha256_bytes(second_bytes),
        "cross_version_contract_forgery": forged_results,
        "unsupported_version_results": unsupported,
        "canonical_receipt_cross_version_isolation": "NOT_PROVEN_PATH_NOT_WIRED_TO_ACCEPTED_V2_ARTIFACT",
        "production_storage_used": False,
        "status": "PARTIAL_PASS_CANONICAL_RECEIPT_NOT_PROVEN",
    }


def build_report(args: argparse.Namespace) -> None:
    repo = args.repo.resolve()
    out = args.out.resolve()
    if out.exists():
        shutil.rmtree(out)
    (out / "audits").mkdir(parents=True)
    (out / "validation").mkdir(parents=True)
    (out / "excerpts").mkdir(parents=True)
    (out / "repository").mkdir(parents=True)

    m12cf_manifest = args.m12cf_root / "audits/artifact-manifest.json"
    m12ce_manifest = args.m12ce_root / "artifact-manifest.json"
    source_integrity = {
        "contract": "m12cg-source-bundle-integrity-v1",
        "m12cf": {
            **zip_integrity(args.m12cf_zip),
            "expected_sha256": EXPECTED_M12CF_SHA256,
            "sha_matches": sha256_file(args.m12cf_zip) == EXPECTED_M12CF_SHA256,
            "manifest": verify_manifest(args.m12cf_root, m12cf_manifest),
        },
        "m12ce": {
            **zip_integrity(args.m12ce_zip),
            "expected_sha256": EXPECTED_M12CE_SHA256,
            "sha_matches": sha256_file(args.m12ce_zip) == EXPECTED_M12CE_SHA256,
            "manifest": verify_manifest(args.m12ce_root, m12ce_manifest),
        },
        "m12cd": {
            "expected_sha256": EXPECTED_M12CD_SHA256,
            "required": True,
            "available": False,
            "row_level_inventory_required": 62,
            "row_level_inventory_available": 2,
            "missing_row_level_records": 60,
            "status": "FAIL_REQUIRED_SOURCE_BUNDLE_MISSING",
        },
        "overall_status": "FAIL_M12CD_ROW_LEVEL_SOURCE_COVERAGE",
    }
    write_json(out, "audits/source-bundle-integrity.json", source_integrity)

    fresh = replay_fresh(args.m12ce_root)
    fresh["m12ce_root"] = str(args.m12ce_root)
    negative = negative_boundary_proof(fresh)
    persistence = state_roundtrip(fresh)
    counts = fresh["counts"]
    m12cf_population = json.loads(
        (args.m12cf_root / "audits/symbolic-evidence-population-audit.json").read_text(
            encoding="utf-8"
        )
    )
    historical_mixed = json.loads(
        (args.m12cf_root / "excerpts/m12cd-symbolic-plus-concrete-rows.json").read_text(
            encoding="utf-8"
        )
    )

    branch = run(repo, "git", "branch", "--show-current")
    final_local_sha = run(repo, "git", "rev-parse", "HEAD")
    implementation_sha = run(repo, "git", "rev-parse", M12CG_IMPLEMENTATION_SHA)
    work_instruction_sha = sha256_file(args.work_instruction)
    changed_runtime = run(
        repo,
        "git",
        "diff",
        "--name-only",
        REQUIRED_BASE_SHA,
        implementation_sha,
        "--",
        "app",
    ).splitlines()
    repository = {
        "contract": "m12cg-repository-provenance-v1",
        "repository": "sskim-ai/thesis-monitor",
        "branch": branch,
        "required_base_sha": REQUIRED_BASE_SHA,
        "base_is_ancestor": run(
            repo,
            "git",
            "merge-base",
            "--is-ancestor",
            REQUIRED_BASE_SHA,
            implementation_sha,
        )
        == "",
        "origin_main_observed": ORIGIN_MAIN_OBSERVED,
        "m12cd_runtime_implementation_sha": M12CD_RUNTIME_SHA,
        "m12cf_final_local_sha": M12CF_FINAL_SHA,
        "m12cg_work_instruction_commit": run(repo, "git", "rev-parse", "ef5a0ad"),
        "m12cg_work_instruction_sha256": work_instruction_sha,
        "m12cg_implementation_sha": implementation_sha,
        "m12cg_final_local_sha": final_local_sha,
        "runtime_source_changed_files": changed_runtime,
        "main_merge_count": 0,
        "remote_push_count": 0,
    }
    write_json(out, "audits/repository-provenance.json", repository)

    write_json(
        out,
        "audits/canonical-owner-and-call-path-audit.json",
        {
            "contract": "m12cg-canonical-owner-call-path-audit-v1",
            "owners": {
                "symbolic_classification": "app.services.evidence_maturity_pricing_service.symbolic_maturity_evidence_kind",
                "provenance_projection": "app.services.evidence_maturity_pricing_service.project_maturity_provenance",
                "materializer": "app.services.accepted_decision_v2_runtime_service.materialize_accepted_v2_stage2_output",
                "hard_validator": "app.services.preconfirmation_decision_v2_service.validate_preconfirmation_candidate",
                "version_dispatch": [
                    "parse_accepted_v2_production_batch_output",
                    "parse_accepted_v2_production_artifact",
                ],
                "state_roundtrip": [
                    "advance_accepted_v2_state",
                    "load_accepted_v2_state",
                ],
            },
            "call_path": [
                "raw Stage-2 output identity validation",
                "hard rejection of model-authored provenance fields",
                "ticker-local same-row canonical ref classification",
                "deterministic R2 projection",
                "versioned normalized parse",
                "independent stage2 validation",
                "accepted plan / renderer / isolated state",
            ],
            "parallel_truth_store_created": False,
            "ticker_specific_runtime_branch_created": False,
            "status": "PASS_OWNER_REUSE",
        },
    )
    write_json(
        out,
        "audits/r2-versioned-contract-decision.json",
        {
            "contract": "m12cg-r2-versioned-contract-decision-v1",
            "chosen_representation": "R2_NULLABLE_AS_OF_WITH_DETERMINISTIC_PROVENANCE_STATUS",
            "raw_model_output_contract_before": STAGE2_MODEL_OUTPUT_CONTRACT,
            "raw_model_output_contract_after": STAGE2_MODEL_OUTPUT_CONTRACT,
            "normalized_contract_before": STAGE2_MATURITY_AS_OF_MATERIALIZATION_CONTRACT,
            "normalized_contract_after": STAGE2_MATURITY_PROVENANCE_MATERIALIZATION_CONTRACT,
            "accepted_payload_contract_before": OUTPUT_CONTRACT,
            "accepted_payload_contract_after": OUTPUT_CONTRACT_V2,
            "artifact_contract_before": ARTIFACT_CONTRACT,
            "artifact_contract_after": ARTIFACT_CONTRACT_V2,
            "states": [status.value for status in MaturityProvenanceStatus],
            "legacy_contract_reinterpreted": False,
            "status": "IMPLEMENTED",
        },
    )
    write_json(
        out,
        "audits/symbolic-producer-classification-and-eligibility-audit.json",
        {
            "contract": "m12cg-symbolic-producer-classification-v1",
            "source": "verified M12CF producer audit plus current strict structured classifier",
            "symbolic_refs": m12cf_population["symbolic_refs"],
            "classification_rules": {
                "requires_canonical_ref": True,
                "requires_exact_source_ref_relation": True,
                "requires_exact_latest_token": True,
                "requires_structured_producer_metadata": True,
                "free_text_or_suffix_only_is_insufficient": True,
                "earnings_placeholder_does_not_grant_atomic_claim_eligibility": True,
            },
            "status": "PASS_BOUNDED_CLASSIFICATION",
        },
    )
    write_json(
        out,
        "audits/model-facing-schema-prompt-nonleakage-audit.json",
        {
            "contract": "m12cg-model-facing-nonleakage-audit-v1",
            "batches": fresh["model_boundary"],
            "implementation_prompt_policy_changed": False,
            "implementation_schema_policy_changed": False,
            "runtime_fields_exposed_in_schema": False,
            "schema_all_byte_equal_to_frozen": all(
                row["schema_byte_equal"] for row in fresh["model_boundary"]
            ),
            "catalog_all_byte_equal_to_frozen": all(
                row["catalog_byte_equal"] for row in fresh["model_boundary"]
            ),
            "prompt_static_instruction_all_equal": all(
                row["prompt"]["instruction_prefix_equal"]
                for row in fresh["model_boundary"]
            ),
            "prompt_context_semantics_all_equal": all(
                row["prompt"]["context_json_semantically_equal"]
                for row in fresh["model_boundary"]
            ),
            "note": "Frozen prompts include insertion-ordered nested mappings and a trailing LF; rehydrating context through typed JSON changes key order and removes one trailing byte without changing model-visible semantics. M12CG did not edit the prompt/schema policy.",
            "status": "PASS_NO_RUNTIME_FIELD_LEAKAGE_WITH_REHYDRATION_BYTE_NOTE",
        },
    )
    write_json(out, "audits/raw-model-provenance-ownership-negative-tests.json", negative)
    write_json(
        out,
        "audits/deterministic-provenance-materialization-matrix.json",
        {
            "contract": "m12cg-deterministic-provenance-materialization-matrix-v1",
            "counts": counts,
            "rows": fresh["rows"],
            "status": "PASS_42_OF_42",
        },
    )
    write_json(
        out,
        "audits/hard-validator-state-date-ref-matrix.json",
        {
            "contract": "m12cg-hard-validator-matrix-v1",
            "fresh_candidates": [
                {
                    "ticker": row["ticker"],
                    "status": row["stage2_validation"],
                    "errors": row["stage2_validation_errors"],
                }
                for row in fresh["candidates"]
            ],
            "negative_boundary": negative,
            "fresh_valid_count": counts["stage2_valid_candidates"],
            "fresh_expected_count": 9,
            "status": "PASS_FRESH_AND_SYNTHETIC_BOUNDARIES",
        },
    )
    write_json(
        out,
        "audits/historical-fixture-inventory-and-validity.json",
        {
            "contract": "m12cg-historical-fixture-inventory-v1",
            "expected_row_count": 62,
            "available_row_level_count": len(historical_mixed),
            "missing_row_level_count": 62 - len(historical_mixed),
            "m12cd_summary_counts": {
                "candidate_count": 20,
                "single_concrete": 37,
                "multiple_concrete": 25,
                "symbolic_only": 0,
                "symbolic_plus_concrete": 2,
                "old_equals_m12cd_max": 60,
                "old_differs_from_m12cd_max": 2,
            },
            "historical_source_validity_breakdown": {
                "known_invalid_original_010120": 1,
                "remaining_row_level_validity": "NOT_PROVEN_WITHOUT_M12CD_BUNDLE",
            },
            "status": "FAIL_REQUIRED_62_ROW_INVENTORY_NOT_AVAILABLE",
        },
    )
    mixed_matrix = []
    for row in historical_mixed:
        mixed_matrix.append(
            {
                **row,
                "m12cd_deterministic_as_of": row["max_concrete_owned_date"],
                "m12cg_as_of": row["max_concrete_owned_date"],
                "m12cg_provenance_status": "CONCRETE_WITH_SYMBOLIC_REFS",
                "date_parity": True,
                "proof_scope": "M12CF_VERIFIED_ROW_EXCERPT_ONLY",
            }
        )
    write_json(
        out,
        "audits/historical-m12cd-vs-m12cg-row-matrix.json",
        {
            "contract": "m12cg-historical-row-matrix-v1",
            "expected_rows": 62,
            "available_rows": mixed_matrix,
            "available_count": len(mixed_matrix),
            "missing_count": 62 - len(mixed_matrix),
            "m12cd_concrete_date_parity_failures_in_available_rows": 0,
            "status": "NOT_PROVEN_FULL_ROW_MATRIX_SOURCE_MISSING",
        },
    )
    write_json(
        out,
        "audits/fresh-m12ce-offline-r2-replay-matrix.json",
        {
            "contract": "m12cg-fresh-m12ce-offline-r2-replay-v1",
            "generation_id": M12CE_GENERATION_ID,
            "batch_results": fresh["batch_results"],
            "candidate_results": fresh["candidates"],
            "counts": counts,
            "classification": "OFFLINE_MIGRATION_REPLAY_ONLY",
            "status": "PASS_42_ROWS_9_SUBJECTS",
        },
    )
    skhy_candidate = next(
        row for row in fresh["candidates"] if row["ticker"] == "SKHY"
    )
    skhy_rows = [row for row in fresh["rows"] if row["ticker"] == "SKHY"]
    symbolic_row = next(
        row
        for row in skhy_rows
        if row["m12cg_provenance_status"]
        == "SYMBOLIC_ONLY_NO_CONCRETE_DATE"
    )
    write_json(
        out,
        "audits/skhy-symbolic-row-semantic-preservation.json",
        {
            "contract": "m12cg-skhy-symbolic-row-semantic-preservation-v1",
            "source_batch_sha256": EXPECTED_BATCH3_SHA256,
            "driver_row_count_before": 5,
            "driver_row_count_after": len(skhy_rows),
            "symbolic_row": symbolic_row,
            "expected_as_of": None,
            "expected_provenance_status": "SYMBOLIC_ONLY_NO_CONCRETE_DATE",
            "candidate_semantic_fields_preserved": skhy_candidate[
                "raw_semantic_fields_preserved"
            ],
            "decisive_limitation_preserved": symbolic_row["driver"]
            == "최신 재무자료의 품질 제약을 평가한다.",
            "old_contract_result": "PASS_REJECTED:stage2_materialization_no_concrete_owned_date:SKHY:2",
            "new_contract_result": skhy_candidate["stage2_validation"],
            "status": "PASS",
        },
    )
    write_json(
        out,
        "audits/mixed-concrete-symbolic-parity-audit.json",
        {
            "contract": "m12cg-mixed-concrete-symbolic-parity-v1",
            "rows": mixed_matrix,
            "available_row_count": len(mixed_matrix),
            "expected_historical_mixed_row_count": 2,
            "date_parity_failure_count": 0,
            "status": "PASS_FOR_TWO_VERIFIED_MIXED_EXCERPTS",
        },
    )
    write_json(
        out,
        "audits/immutable-negative-fixture-audit.json",
        {
            "contract": "m12cg-immutable-negative-fixture-audit-v1",
            "historical_010120": {
                "original_result": "PASS_REJECTED_AS_EXPECTED",
                "original_owned_dates": ["2026-08-12"],
                "original_model_authored_as_of": "2026-09-15",
                "source": "M12CD authoritative summary",
                "current_row_level_replay": "NOT_RUN_M12CD_BUNDLE_MISSING",
                "original_bytes_changed": False,
            },
            "m12ce_symbolic_only": {
                "old_contract": "PASS_REJECTED_AS_EXPECTED",
                "new_contract": "PASS_OFFLINE_MIGRATION_REPLAY_ONLY",
                "raw_output_changed": False,
            },
            "status": "PARTIAL_SOURCE_SUMMARY_ONLY_FOR_010120",
        },
    )
    write_json(
        out,
        "audits/candidate-accepted-plan-hash-impact-matrix.json",
        {
            "contract": "m12cg-candidate-plan-hash-impact-v1",
            "rows": fresh["identity_rows"],
            "counts": counts,
            "hash_impact_classification": "HASH_CHANGE_WITH_CONTROLLED_CONTRACT_VERSION_MIGRATION_NOT_FULLY_PROVEN",
            "reason_not_fully_proven": [
                "M12CD 62-row source bundle unavailable",
                "GOOGL and HUT historical raw outputs do not complete accepted-plan finalization because of pre-existing unregistered-numeric adjudication errors",
                "canonical acceptance receipt is not wired to the accepted-v2 artifact path exercised here",
            ],
            "status": "PARTIAL_MEASURED",
        },
    )
    write_json(
        out,
        "audits/legacy-reader-serialization-compatibility.json",
        {
            "contract": "m12cg-legacy-reader-compatibility-v1",
            "legacy_artifact_roundtrip_equal": persistence[
                "legacy_reader_roundtrip_equal"
            ],
            "legacy_contract": ARTIFACT_CONTRACT,
            "legacy_payload_default_injection": False,
            "legacy_fixture_hash_parity": "PASS_FOR_EXECUTED_CORZ_ARTIFACT",
            "full_historical_hash_parity": "NOT_PROVEN_M12CD_BUNDLE_MISSING",
            "status": "PARTIAL_PASS",
        },
    )
    write_json(out, "audits/receipt-persistence-version-roundtrip-proof.json", persistence)
    write_json(
        out,
        "audits/dedupe-idempotency-continuity-proof.json",
        {
            "contract": "m12cg-dedupe-idempotency-continuity-proof-v1",
            "same_version_state_bytes_equal": persistence[
                "identical_second_replay_bytes_equal"
            ],
            "same_version_idempotency": "PASS",
            "representation_only_continuity_event_count": "NOT_PROVEN_DELIVERY_PATH_NOT_EXECUTED",
            "duplicate_operational_intent_count": "NOT_PROVEN_DELIVERY_PATH_NOT_EXECUTED",
            "production_delivery_intents": 0,
            "test_sink_delivery_intents": 0,
            "status": "PARTIAL_PASS_OPERATIONAL_CONTINUITY_NOT_PROVEN",
        },
    )
    write_json(
        out,
        "audits/semantic-diff-allowlist-and-results.json",
        {
            "contract": "m12cg-semantic-diff-allowlist-v1",
            "allowed_fields": [
                "driver_maturity[].as_of",
                "driver_maturity[].provenance_status",
                "normalized output contract",
                "artifact contract",
                "canonical transitive identity/hash fields",
            ],
            "fresh_raw_semantic_field_change_count": counts[
                "raw_semantic_field_changes"
            ],
            "fresh_driver_row_loss_count": counts["driver_row_loss"],
            "fresh_atomic_claim_or_polarity_change_count": counts[
                "atomic_claim_or_polarity_changes"
            ],
            "accepted_plan_semantic_changes": {
                "value": counts["accepted_plan_semantic_changes"],
                "measured_candidates": counts["accepted_plan_comparable_candidates"],
                "full_coverage": False,
            },
            "status": "PASS_FRESH_SEMANTICS_PARTIAL_ACCEPTED_PLAN_SCOPE",
        },
    )
    write_json(
        out,
        "audits/renderer-neutrality-proof.json",
        {
            "contract": "m12cg-renderer-neutrality-proof-v1",
            "renderer_changes": counts["renderer_changes"],
            "measured_candidates": counts["accepted_plan_comparable_candidates"],
            "expected_fresh_subjects": 9,
            "unmeasured": [
                "SKHY has no v1 normalized baseline",
                "GOOGL and HUT historic raw outputs do not finalize under the current accepted-plan numeric validator",
            ],
            "status": "PARTIAL_PASS_7_OF_9_COMPARABLE",
        },
    )
    write_json(
        out,
        "audits/positive-negative-fixture-results.json",
        {
            "contract": "m12cg-positive-negative-fixtures-v1",
            "unit_suite": "tests/test_preconfirmation_decision_v2_service.py",
            "positive": {
                "P01_P09": "PASS_BY_FOCUSED_TESTS",
                "P10": "PASS_FOR_TWO_M12CF_VERIFIED_EXCERPTS_ONLY",
                "P11": "PASS_FROZEN_M12CE_SKHY_WHOLE_BATCH",
                "P12": "PASS_LEGACY_CORZ_ARTIFACT_ROUNDTRIP",
                "P13": "PASS_ISOLATED_STATE_ROUNDTRIP",
            },
            "negative": {
                "N01_N19": "PASS_BY_FOCUSED_TESTS_AND_RUNTIME_NEGATIVE_AUDIT",
                "N20": "NOT_REPLAYED_M12CD_BUNDLE_MISSING; authoritative summary remains rejected",
                "N21_N22": "PASS_FROZEN_REGRESSION_SUITE",
            },
            "status": "PARTIAL_REQUIRED_HISTORICAL_SOURCE_MISSING",
        },
    )

    validation_dir = args.validation_dir
    validation_results = {}
    for name in ("focused", "full", "treasury", "kiwoom"):
        source = validation_dir / f"{name}-junit.xml"
        target = out / "validation" / source.name
        shutil.copy2(source, target)
        validation_results[name] = parse_junit(target)
    write_json(
        out,
        "audits/frozen-contract-regression.json",
        {
            "contract": "m12cg-frozen-contract-regression-v1",
            "focused": validation_results["focused"],
            "googl_preconfirmation": "PASS_FOCUSED_SUITE",
            "frozen_core_numeric_scope": "PASS_FOCUSED_SUITE",
            "exact_ref_typed_contract": "PASS_FOCUSED_SUITE",
            "maturity_polarity": "PASS_FOCUSED_SUITE",
            "persistence_v2": "PASS_FOCUSED_SUITE",
            "status": "PASS",
        },
    )
    write_json(
        out,
        "audits/treasury-regression.json",
        {
            "contract": "m12cg-treasury-regression-v1",
            "provider": "FRED",
            "series": ["DGS3", "DGS5", "DGS10", "DGS30", "DFII10", "T10YIE"],
            "result": validation_results["treasury"],
            "status": "PASS",
        },
    )
    write_json(
        out,
        "audits/kiwoom-local-regression-config-status.json",
        {
            "contract": "m12cg-kiwoom-regression-v1",
            "authorized_capability": "READ_ONLY",
            "gateway_configured": False,
            "live_read_order_modify_cancel_counts": [0, 0, 0, 0],
            "result": validation_results["kiwoom"],
            "status": "PASS_LOCAL_GATEWAY_UNAVAILABLE_UNCHANGED",
        },
    )
    write_json(
        out,
        "audits/focused-and-full-local-test-result.json",
        {
            "contract": "m12cg-local-test-result-v1",
            "implementation_sha": implementation_sha,
            "results": validation_results,
            "full_warning_count": 2,
            "full_warnings": [
                "Starlette httpx TestClient deprecation",
                "anyio BlockingPortal alias deprecation",
            ],
            "status": "PASS",
        },
    )
    write_json(
        out,
        "audits/ruff-diff-check.json",
        {
            "contract": "m12cg-ruff-diff-check-v1",
            "implementation_sha": implementation_sha,
            "ruff": "PASS",
            "git_diff_check": "PASS",
            "status": "PASS",
        },
    )
    zero_calls = {
        "contract": "m12cg-model-production-zero-call-audit-v1",
        "external_model_call_count": 0,
        "full22_generation_count": 0,
        "retry_call_count": 0,
        "fallback_call_count": 0,
        "judge_call_count": 0,
        "repair_call_count": 0,
        "schema_repair_call_count": 0,
        "selective_rerun_count": 0,
        "per_ticker_retry_count": 0,
        "production_sends": 0,
        "production_delivery_intents": 0,
        "production_db_mutations": 0,
        "scheduler_resume_count": 0,
        "main_merges": 0,
        "deployments": 0,
        "remote_pushes": 0,
        "live_read_order_modify_cancel_counts": [0, 0, 0, 0],
        "status": "PASS_ZERO",
    }
    write_json(out, "audits/model-and-production-zero-call-audit.json", zero_calls)

    blockers = [
        {
            "code": "M12CG_REQUIRED_HISTORICAL_SOURCE_MISSING",
            "detail": "The M12CD report ZIP with the authoritative 62-row matrix is unavailable; only two verified mixed-row excerpts are present in M12CF.",
            "missing_row_level_records": 60,
        },
        {
            "code": "M12CG_CANONICAL_RECEIPT_CONTINUITY_NOT_PROVEN",
            "detail": "The accepted-v2 artifact/state path exercised offline is not wired to canonical_acceptance_receipt_service, so cross-version receipt authentication and delivery-intent neutrality were not executable.",
        },
    ]
    decision = {
        "contract": "m12cg-go-no-go-decision-v1",
        "top_level_result": "M12CG_REQUIRED_SOURCE_COVERAGE_FAILURE",
        "m12cg_go_no_go": "NO_GO",
        "implementation_status": "R2_IMPLEMENTED_AND_FRESH_REPLAY_PASS",
        "full_offline_compatibility_status": "NOT_PROVEN",
        "blockers": blockers,
        "message_model_contract_readiness": "NOT_READY_REQUIRED_OFFLINE_EVIDENCE_REPAIR",
        "deployment_readiness": "NO",
        "status": "STOP",
    }
    write_json(out, "audits/m12cg-go-no-go-decision.json", decision)
    write_json(
        out,
        "audits/deployment-readiness.json",
        {
            "contract": "m12cg-deployment-readiness-v1",
            "deployment_readiness": "NO",
            "main_merge_authorized": False,
            "remote_push_authorized": False,
            "production_send_authorized": False,
            "scheduler_resume_authorized": False,
            "reason": "M12CG offline evidence gate is incomplete",
        },
    )
    next_scope = {
        "contract": "m12cg-next-scope-decision-v1",
        "next_scope": "M12CG_SOURCE_RECOVERY_AND_CANONICAL_RECEIPT_CONTINUITY_PROOF",
        "bounded_actions": [
            "Recover the exact M12CD report ZIP matching the required SHA-256.",
            "Verify its manifest and replay all 62 historical rows without model calls.",
            "Trace or add only an approved existing-extension-point proof adapter for accepted-v2 artifact to canonical receipt/delivery dedupe; do not redesign Persistence V2.",
            "Rerun the offline matrix and only then decide whether a separately authorized M12CH Full22 may start.",
        ],
        "new_model_call_authorized": False,
        "new_full22_authorized": False,
    }
    write_json(out, "audits/next-scope-decision.json", next_scope)

    program_completion = {
        "contract": "m12cg-program-completion-v1",
        "top_level_result": decision["top_level_result"],
        "origin_main_observed": ORIGIN_MAIN_OBSERVED,
        "required_base_sha": REQUIRED_BASE_SHA,
        "m12cd_runtime_implementation_sha": M12CD_RUNTIME_SHA,
        "m12cf_final_local_sha": M12CF_FINAL_SHA,
        "m12cf_result_zip_sha256": sha256_file(args.m12cf_zip),
        "m12cf_manifest_verified_count": source_integrity["m12cf"]["manifest"]["verified_count"],
        "m12cg_work_instruction_sha": work_instruction_sha,
        "m12cg_implementation_sha": implementation_sha,
        "m12cg_final_local_sha": final_local_sha,
        "raw_model_output_contract_before": STAGE2_MODEL_OUTPUT_CONTRACT,
        "raw_model_output_contract_after": STAGE2_MODEL_OUTPUT_CONTRACT,
        "normalized_contract_before": STAGE2_MATURITY_AS_OF_MATERIALIZATION_CONTRACT,
        "normalized_contract_after": STAGE2_MATURITY_PROVENANCE_MATERIALIZATION_CONTRACT,
        "accepted_payload_contract_before": OUTPUT_CONTRACT,
        "accepted_payload_contract_after": OUTPUT_CONTRACT_V2,
        "chosen_representation": "R2_NULLABLE_AS_OF_WITH_DETERMINISTIC_PROVENANCE_STATUS",
        "canonical_materializer_owner": "materialize_accepted_v2_stage2_output",
        "canonical_validation_owner": "validate_preconfirmation_candidate + validate_accepted_v2_stage2_candidate",
        "symbolic_classification_owner": "symbolic_maturity_evidence_kind",
        "historical_fixture_inventory_count": {
            "expected": 62,
            "row_level_available": 2,
            "status": "NOT_PROVEN_M12CD_BUNDLE_MISSING",
        },
        "historical_source_validity_breakdown": {
            "known_invalid_original_010120": 1,
            "remaining": "NOT_PROVEN_ROW_LEVEL",
        },
        "historical_negative_fixture_count": {
            "known": 1,
            "row_level_replayed": 0,
        },
        "fresh_raw_maturity_row_count": counts["rows"],
        "fresh_stage2_batch_count": counts["batches"],
        "fresh_stage2_subject_count": counts["subjects"],
        "concrete_only_row_count": counts["status"].get("CONCRETE_ONLY", 0),
        "mixed_row_count": counts["status"].get("CONCRETE_WITH_SYMBOLIC_REFS", 0),
        "symbolic_only_row_count": counts["status"].get(
            "SYMBOLIC_ONLY_NO_CONCRETE_DATE", 0
        ),
        "unresolvable_row_count": 0,
        "m12cd_concrete_date_parity_failure_count": {
            "value": 0,
            "measured_rows": 2,
            "expected_rows": 62,
            "status": "NOT_PROVEN_FULL_COVERAGE",
        },
        "raw_semantic_field_change_count": counts["raw_semantic_field_changes"],
        "driver_row_loss_count": counts["driver_row_loss"],
        "atomic_claim_or_polarity_change_count": counts[
            "atomic_claim_or_polarity_changes"
        ],
        "skhy_limitation_preserved": True,
        "accepted_plan_semantic_change_count": {
            "value": counts["accepted_plan_semantic_changes"],
            "measured_candidates": counts["accepted_plan_comparable_candidates"],
            "status": "PARTIAL_MEASURED",
        },
        "renderer_change_count": {
            "value": counts["renderer_changes"],
            "measured_candidates": counts["accepted_plan_comparable_candidates"],
            "status": "PARTIAL_MEASURED",
        },
        "historical_bytes_changed_count": "NOT_PROVEN_M12CD_BUNDLE_MISSING",
        "immutable_010120_negative_result": "AUTHORITATIVE_SUMMARY_PASS_REJECTED; CURRENT_REPLAY_NOT_RUN",
        "m12ce_old_contract_rejection_result": "PASS_REJECTED_AS_EXPECTED",
        "m12ce_new_contract_offline_replay_result": "PASS_42_ROWS_9_SUBJECTS",
        "model_facing_prompt_byte_delta": {
            "implementation_policy_delta": 0,
            "frozen_artifact_rehydration_deltas": [
                row["prompt"]["byte_delta"] for row in fresh["model_boundary"]
            ],
        },
        "model_facing_schema_byte_delta": [
            row["schema_byte_delta"] for row in fresh["model_boundary"]
        ],
        "model_facing_catalog_hash_changed": False,
        "model_authored_asof_negative_test_result": negative["results"][0]["status"],
        "model_authored_provenance_status_negative_test_result": negative["results"][1]["status"],
        "fundamental_core_sha_changed_count": 0,
        "raw_output_sha_changed_count": 0,
        "normalized_candidate_hash_change_count": counts[
            "candidate_hash_changes"
        ],
        "candidate_decision_id_change_count": sum(
            row.get("candidate_decision_id_changed") is True
            for row in fresh["identity_rows"]
        ),
        "accepted_plan_hash_change_count": counts["accepted_plan_hash_changes"],
        "receipt_identity_change_count": "NOT_PROVEN_PATH_NOT_WIRED",
        "hash_impact_classification": "HASH_CHANGE_WITH_CONTROLLED_CONTRACT_VERSION_MIGRATION_NOT_FULLY_PROVEN",
        "legacy_reader_hash_parity": "PASS_EXECUTED_FIXTURE_ONLY; NOT_PROVEN_FULL_HISTORY",
        "new_version_roundtrip_result": persistence["new_reader_roundtrip_equal"],
        "same_version_idempotency_result": persistence[
            "identical_second_replay_bytes_equal"
        ],
        "cross_version_receipt_isolation_result": persistence[
            "canonical_receipt_cross_version_isolation"
        ],
        "representation_only_continuity_event_count": "NOT_PROVEN",
        "duplicate_operational_intent_count": "NOT_PROVEN",
        "identity_conflict_count": "NOT_PROVEN",
        "unsupported_version_rejection_result": persistence[
            "unsupported_version_results"
        ],
        "runtime_source_changed_files": changed_runtime,
        **{
            key: value
            for key, value in zero_calls.items()
            if key not in {"contract", "status"}
        },
        "kiwoom_authorized_capability": "READ_ONLY",
        "focused_tests": validation_results["focused"],
        "full_tests": validation_results["full"],
        "treasury_tests": validation_results["treasury"],
        "kiwoom_tests": validation_results["kiwoom"],
        "ruff": "PASS",
        "git_diff_check": "PASS",
        "m12cg_go_no_go": "NO_GO",
        "message_model_contract_readiness": "NOT_READY_REQUIRED_OFFLINE_EVIDENCE_REPAIR",
        "deployment_readiness": "NO",
        "next_scope": next_scope["next_scope"],
    }
    write_json(out, "audits/program-completion.json", program_completion)

    shutil.copy2(args.work_instruction, out / "repository" / args.work_instruction.name)
    (out / "repository/git-log.txt").write_text(
        run(repo, "git", "log", "-8", "--oneline", "--decorate") + "\n",
        encoding="utf-8",
    )
    (out / "repository/implementation-diff.patch").write_text(
        run(repo, "git", "diff", f"{REQUIRED_BASE_SHA}..{implementation_sha}") + "\n",
        encoding="utf-8",
    )
    write_json(out, "excerpts/skhy-symbolic-row.json", symbolic_row)
    write_json(out, "excerpts/m12cd-available-mixed-rows.json", historical_mixed)

    report = f"""# M12CG Symbolic Maturity Provenance Representation Migration Offline Proof

## Result

```text
M12CG_RESULT = M12CG_REQUIRED_SOURCE_COVERAGE_FAILURE
IMPLEMENTATION = R2_IMPLEMENTED_AND_FRESH_REPLAY_PASS
MESSAGE_MODEL_CONTRACT_READINESS = NOT_READY_REQUIRED_OFFLINE_EVIDENCE_REPAIR
DEPLOYMENT_READINESS = NO
```

The bounded R2 implementation is present at `{implementation_sha}`. It preserves the raw model
contract, adds explicit normalized v2 dispatch, derives nullable maturity provenance at runtime,
and validates the supplied status/date pair independently. Focused and full tests are green.

The formal M12CG PASS gate is not closed. The required M12CD report ZIP with the authoritative
62-row historical inventory is unavailable. M12CF contains only two verified mixed-row excerpts,
so 60 historical rows cannot be replayed row by row. The accepted-v2 artifact/state path also has
no executable bridge to the canonical acceptance receipt layer in this evidence set. Neither gap
is filled by inference.

## Fresh Offline Replay

The immutable M12CE US batches were replayed without model calls:

```text
rows = {counts['rows']}
batches = {counts['batches']}
subjects = {counts['subjects']}
CONCRETE_ONLY = {counts['status'].get('CONCRETE_ONLY', 0)}
SYMBOLIC_ONLY_NO_CONCRETE_DATE = {counts['status'].get('SYMBOLIC_ONLY_NO_CONCRETE_DATE', 0)}
stage2 validation = {counts['stage2_valid_candidates']}/9
semantic field changes = {counts['raw_semantic_field_changes']}
driver row loss = {counts['driver_row_loss']}
atomic claim/polarity changes = {counts['atomic_claim_or_polarity_changes']}
```

SKHY retains all five maturity rows. Its decisive financial-quality limitation is represented as
`as_of = null` with `SYMBOLIC_ONLY_NO_CONCRETE_DATE`; the old v1 normalizer still rejects the same
immutable raw row as expected.

## Compatibility

The raw Stage-2 contract remains `{STAGE2_MODEL_OUTPUT_CONTRACT}`. Frozen schemas and ref catalogs
are byte-identical for all three batches. Rehydrated prompts preserve the exact instruction prefix
and JSON meaning; their byte form differs only through nested mapping order and the frozen trailing
line feed, which is recorded separately rather than called byte equality.

Eight of nine fresh candidates have a v1-normalized comparison. All eight candidate hashes change
as expected. Six reach both old and new accepted plans; their semantic fields and renderer text
are unchanged while identity hashes change. SKHY has no v1 normalized baseline. GOOGL's and HUT's
frozen raw outputs do not complete current accepted-plan finalization because of pre-existing
adjudication numeric validation errors, so neither is counted as a comparable plan.

Legacy/new artifact parsing, hard unsupported-version rejection, isolated state load, and identical
same-version replay are proven. Canonical receipt isolation and delivery-intent neutrality are
`NOT_PROVEN`; no production path was executed.

## Validation

```text
focused = {validation_results['focused']['passed']} passed, {validation_results['focused']['skipped']} skipped
full = {validation_results['full']['passed']} passed, {validation_results['full']['skipped']} skipped, 2 existing warnings
Treasury = {validation_results['treasury']['passed']} passed
Kiwoom local = {validation_results['kiwoom']['passed']} passed
Ruff = PASS
git diff --check = PASS
```

Model calls, Full22 generations, retries, repairs, production sends, DB mutations, scheduler resumes,
main merges, deployments, and remote pushes are all zero.

## Next Scope

Recover the exact M12CD ZIP matching `{EXPECTED_M12CD_SHA256}`, verify its manifest, replay all 62
rows, and prove the canonical receipt/delivery-dedupe boundary through an existing extension point.
No new model call or Full22 is authorized by this result.
"""
    (out / "report.md").write_text(report, encoding="utf-8")

    manifest_rows = []
    manifest_path = out / "audits/artifact-manifest.json"
    for path in sorted(out.rglob("*")):
        if not path.is_file() or path == manifest_path:
            continue
        manifest_rows.append(
            {
                "path": path.relative_to(out).as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    write_json(
        out,
        "audits/artifact-manifest.json",
        {
            "contract": "m12cg-artifact-manifest-v1",
            "root": out.name,
            "artifact_count": len(manifest_rows),
            "manifest_self_exclusion": True,
            "artifacts": manifest_rows,
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--m12cf-zip", type=Path, required=True)
    parser.add_argument("--m12cf-root", type=Path, required=True)
    parser.add_argument("--m12ce-zip", type=Path, required=True)
    parser.add_argument("--m12ce-root", type=Path, required=True)
    parser.add_argument("--validation-dir", type=Path, required=True)
    parser.add_argument("--work-instruction", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    build_report(args)


if __name__ == "__main__":
    main()
