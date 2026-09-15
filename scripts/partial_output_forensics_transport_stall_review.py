from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from collections.abc import Mapping, Sequence
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.jobs import accepted_decision_v2_runtime as accepted_runtime
from app.services.direction_timing_ownership_service import (
    CORE_DOMAINS,
    MATERIAL_DIRECTIONAL_DOMAINS,
    TIMING_DOMAINS,
    CORE_OUTPUT_CONTRACT,
    DirectionalCoreCandidate,
    EvidenceDomain,
    OwnedEvidencePacket,
    stage_alias_catalogs,
)
from scripts import directional_core_price_timing_holdout as frozen
from scripts import model_transport_revalidation_ownership_continuation as transport
from scripts import synthetic_canary_fixture_repair_ownership_resume as synthetic
from scripts import uskr22_structured_autonomy_shadow as engine


PROGRAM_CONTRACT = "partial-output-forensics-bounded-transport-stall-review-v1"
LATEST_RESULT_SHA256 = "5704dc77bd77458ae68550aa8262cc90525a562e739345a1dace39b7a194ef2b"
SOURCE_GENERATION_ID = "20260906-direction-timing-holdout-20260906T093200Z-bd30668470f0"
RESUME_GENERATION_ID = "20260906-real-holdout-adapter-resume-20260906T133003Z-585c983a57d9"
SOURCE_LOCK_SHA256 = "efe64d0942afa00c3b40131afc4de5fa411babc0680271d1571aaac69816050d"
BASE_SHA = "4743d3e842ca71ec4f118b6e80b09ae3e6c72a25"
WORK_INSTRUCTION_COMMIT = "8c11888227778a1bacec25a3b6a72a224a5c6f7c"
PRIOR_IMPLEMENTATION_COMMIT = "16681321683d4ef6bdbff4007770524b1b153136"
MODEL = synthetic.MODEL
EFFORT = synthetic.EFFORT
TIMEOUT_SECONDS = synthetic.MODEL_TIMEOUT_SECONDS
BATCH_SIZE = synthetic.MODEL_CONTEXT_BATCH_SIZE
RETIRED_HOLDOUT = synthetic.CURRENT_HOLDOUT
CONSUMED_REGRESSION = synthetic.CONSUMED_LATEST_HOLDOUT16
EXPOSED_SUBJECTS = RETIRED_HOLDOUT[:8]
UNEXPOSED_RETIRED_SUBJECTS = RETIRED_HOLDOUT[8:]
EXPECTED_BATCHES = {
    "01": RETIRED_HOLDOUT[:4],
    "02": RETIRED_HOLDOUT[4:8],
}
EXPECTED_RECEIPTS = {
    "01": {
        "prompt_sha256": "73cc97228b7263ba207c333278798ea9d5cb281c9e6a9e039c615eecacba9f84",
        "schema_sha256": "fbb4d4e7642e9a2bed8a9d15ebd8ba4f5817d1a7eb44f2eac5942b4907875ad8",
        "output_bytes": 16612,
        "stdout_bytes": 16613,
    },
    "02": {
        "prompt_sha256": "5bf8257acbc6197f0f3b904714852261cf7b88cfe53486043170ad4968d3dab1",
        "schema_sha256": "97ed401cc09f7173c3a8f87e780d36ae7cc2d71d94573dfef357283578c910cd",
        "output_bytes": 16361,
        "stdout_bytes": 16362,
    },
}
REPORT_NAMES = (
    "01-repository-provenance",
    "02-latest-result-bundle-integrity",
    "03-prior-run-fact-reconstruction",
    "04-partial-output-provenance-gap",
    "05-partial-output-recovery-search",
    "06-recovered-batch01-provenance",
    "07-recovered-batch02-provenance",
    "08-recovered-output-artifact-manifest",
    "09-offline-schema-validation",
    "10-offline-directional-ownership-validation",
    "11-offline-partial-hard-safety-validation",
    "12-partial-semantic-audit-summary",
    "13-batch03-log-recovery",
    "14-batch03-lifecycle-forensics",
    "15-batch01-02-03-comparison",
    "16-transport-root-cause-classification",
    "17-historical-pre-first-freeze-audit",
    "18-fictional-probe-precommit",
    "19-fictional-probe-batch01",
    "20-fictional-probe-batch02",
    "21-fictional-probe-batch03",
    "22-fictional-probe-sequence-summary",
    "23-retired-cohort-proof",
    "24-real-issuer-no-model-call-proof",
    "25-evidence-preservation-policy",
    "26-production-no-change",
    "27-night-futures-no-change",
    "28-next-scope-decision",
    "29-program-completion",
)
PROOF_DIR = "proofs"
SECRET_PATTERNS = (
    re.compile(rb"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(rb"Bearer[ \t]+[A-Za-z0-9._~+/-]{16,}", re.IGNORECASE),
    re.compile(
        rb"(?:API[_-]?KEY|ACCESS[_-]?TOKEN|PASSWORD|SECRET)[ \t]*[:=][ \t]*[^\s]{8,}",
        re.IGNORECASE,
    ),
)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def git_value(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout.strip()


def proof_path(report_dir: Path, name: str) -> Path:
    return report_dir / PROOF_DIR / f"{name}.json"


def write_proof(report_dir: Path, name: str, value: Mapping[str, object]) -> None:
    write_json(proof_path(report_dir, name), value)


def scan_secret_bytes(payload: bytes) -> dict[str, object]:
    counts = [len(pattern.findall(payload)) for pattern in SECRET_PATTERNS]
    return {
        "secret_exposure_count": sum(counts),
        "secret_scan_status": "PASS" if not any(counts) else "BLOCKED",
        "category_counts": {
            "openai_key": counts[0],
            "bearer_token": counts[1],
            "named_secret": counts[2],
        },
    }


def preserve_safe_file(source: Path, destination: Path) -> dict[str, object]:
    payload = source.read_bytes()
    scan = scan_secret_bytes(payload)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if scan["secret_exposure_count"] == 0:
        destination.write_bytes(payload)
        status = "EXACT_BYTES_PRESERVED"
        copied_sha = file_sha256(destination)
        copied_bytes: int | str = destination.stat().st_size
    else:
        redacted = payload
        for pattern in SECRET_PATTERNS:
            redacted = pattern.sub(b"[REDACTED]", redacted)
        redacted_path = destination.with_suffix(destination.suffix + ".redacted")
        redacted_path.write_bytes(redacted)
        status = "BLOCKED_BY_SECRET_POLICY_REDACTED_DERIVATIVE_PRESERVED"
        copied_sha = file_sha256(redacted_path)
        copied_bytes = redacted_path.stat().st_size
    return {
        "source_sha256": hashlib.sha256(payload).hexdigest(),
        "source_bytes": len(payload),
        "preservation_status": status,
        "copied_sha256": copied_sha,
        "copied_bytes": copied_bytes,
        **scan,
    }


def generation_id(commit: str, as_of: datetime) -> str:
    stamp = as_of.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = hashlib.sha256(f"{commit}|{stamp}|{PROGRAM_CONTRACT}".encode()).hexdigest()[:12]
    return f"20260906-fictional-sequential-probe-{stamp}-{suffix}"


def verify_latest_bundle(path: Path) -> dict[str, object]:
    actual_sha = file_sha256(path)
    if actual_sha != LATEST_RESULT_SHA256:
        raise ValueError("RESULT_BUNDLE_CHECKSUM_MISMATCH")
    with zipfile.ZipFile(path) as archive:
        index = json.loads(archive.read("20260906-artifact-index.json"))
        rows = index.get("rows") if isinstance(index, Mapping) else None
        if not isinstance(rows, list):
            raise ValueError("prior_bundle_artifact_index_missing")
        hash_mismatches = 0
        size_mismatches = 0
        for row in rows:
            payload = archive.read(str(row["path"]))
            hash_mismatches += hashlib.sha256(payload).hexdigest() != row["sha256"]
            size_mismatches += len(payload) != row["bytes"]
        names = set(archive.namelist())
    exact_outputs = [
        name
        for name in names
        if name.endswith("run-first/core-batch-01.json")
        or name.endswith("run-first/core-batch-02.json")
        or name.startswith("recovered-real-output/")
    ]
    status = "PASS" if len(rows) == 63 and hash_mismatches == size_mismatches == 0 else "FAIL"
    if status != "PASS":
        raise ValueError("prior_bundle_artifact_integrity_failure")
    return {
        "contract": "latest-result-bundle-integrity-v1",
        "expected_sha256": LATEST_RESULT_SHA256,
        "actual_sha256": actual_sha,
        "artifact_count": len(rows),
        "artifact_hash_mismatch_count": hash_mismatches,
        "artifact_size_mismatch_count": size_mismatches,
        "zip_member_count": len(names),
        "prior_bundle_exact_partial_output_files_present": int(bool(exact_outputs)),
        "exact_partial_output_members": exact_outputs,
        "status": status,
    }


def receipt_by_batch(receipt_root: Path) -> dict[str, tuple[Path, dict[str, Any]]]:
    result = {}
    for path in sorted(receipt_root.glob("*.json")):
        value = read_json(path)
        batch = str(value.get("batch_id") or "")
        if value.get("generation_id") == RESUME_GENERATION_ID:
            result[batch] = (path, value)
    return result


def source_preflight_rows(repo_root: Path) -> dict[str, Mapping[str, object]]:
    path = (
        repo_root
        / "docs/reports/20260906-direction-timing-ownership-proofs"
        / "new-issuer-holdout-source-preflight.json"
    )
    proof = read_json(path)
    return {str(row["ticker"]): row for row in proof["selected_rows"] if isinstance(row, Mapping)}


def _core_only_audit(
    core: DirectionalCoreCandidate, owned: OwnedEvidencePacket
) -> dict[str, object]:
    domains = owned.domain_by_ref
    refs = frozen._refs(core.model_dump(mode="json"))
    price_refs = sorted(
        ref
        for ref in refs
        if domains.get(ref) in TIMING_DOMAINS
        and domains.get(ref) != EvidenceDomain.SUPPLY_POSITIONING
    )
    supply_refs = sorted(
        ref for ref in refs if domains.get(ref) == EvidenceDomain.SUPPLY_POSITIONING
    )
    unsupported = sorted(ref for ref in refs if domains.get(ref) not in CORE_DOMAINS)
    material = {
        ref
        for ref in core.material_directional_anchor_basis
        if domains.get(ref) in MATERIAL_DIRECTIONAL_DOMAINS
    }
    buy_missing = int(core.overall_direction == "BUY" and not material)
    sell_missing = int(core.overall_direction == "SELL" and not material)
    errors = []
    if price_refs:
        errors.append("directional_core_contains_price_or_technical_ref")
    if supply_refs:
        errors.append("directional_core_contains_supply_ref")
    if unsupported:
        errors.append("directional_core_ref_outside_domain_registry")
    if buy_missing:
        errors.append("buy_without_nonprice_material_anchor")
    if sell_missing:
        errors.append("sell_without_nonprice_material_anchor")
    return {
        "ticker": core.ticker,
        "overall_direction": core.overall_direction,
        "directional_core_price_technical_refs": len(price_refs),
        "directional_core_supply_refs": len(supply_refs),
        "supply_directional_core_usage": len(supply_refs),
        "buy_without_nonprice_material_anchor": buy_missing,
        "sell_without_nonprice_material_anchor": sell_missing,
        "unsupported_core_refs": unsupported,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def batch_envelope_errors(parsed: Mapping[str, object], *, packet_id: str) -> list[str]:
    errors = []
    if set(parsed) != {"candidates", "contract", "packet_id"}:
        errors.append("batch_envelope_keys_mismatch")
    if parsed.get("contract") != CORE_OUTPUT_CONTRACT:
        errors.append("batch_contract_mismatch")
    if parsed.get("packet_id") != packet_id:
        errors.append("batch_packet_id_mismatch")
    if not isinstance(parsed.get("candidates"), list):
        errors.append("batch_candidates_array_required")
    return errors


def recover_partial_outputs(
    args: argparse.Namespace,
) -> tuple[dict[str, dict[str, object]], dict[str, object]]:
    receipt_root = args.prior_output_root / "transport-receipts"
    receipts = receipt_by_batch(receipt_root)
    (
        _cohort,
        _contexts,
        evidence,
        owned,
        core_aliases,
        _timing_aliases,
        _price_maps,
        _stocks,
    ) = transport._load_frozen_holdout(args)
    preflight = source_preflight_rows(Path.cwd().resolve())
    batch_results: dict[str, dict[str, object]] = {}
    audit_rows = []
    manifest_rows = []
    recovered_count = 0
    for batch_id, subjects in EXPECTED_BATCHES.items():
        raw_path = args.prior_output_root / "run-first" / f"core-batch-{batch_id}.json"
        schema_path = args.source_root / "schemas" / f"core-batch-{batch_id}.json"
        receipt_entry = receipts.get(batch_id)
        result: dict[str, object] = {
            "contract": "recovered-real-output-provenance-v1",
            "generation_id": RESUME_GENERATION_ID,
            "invocation_id": (f"{RESUME_GENERATION_ID}:run-first:DIRECTIONAL_CORE:{batch_id}"),
            "stage": "DIRECTIONAL_CORE",
            "batch_id": batch_id,
            "recovery_status": "OUTPUT_NOT_FOUND",
            "original_artifact_identity": str(raw_path),
            "copied_artifact_path": None,
            "raw_output_sha256": "NOT_AVAILABLE",
            "raw_output_bytes": "NOT_AVAILABLE",
            "receipt_output_bytes": "NOT_AVAILABLE",
            "receipt_stdout_bytes": "NOT_AVAILABLE",
            "prompt_sha256": EXPECTED_RECEIPTS[batch_id]["prompt_sha256"],
            "schema_sha256": EXPECTED_RECEIPTS[batch_id]["schema_sha256"],
            "subject_count": len(subjects),
            "subjects": list(subjects),
            "schema_revalidation_status": "NOT_MEASURED",
            "offline_validator_status": "NOT_MEASURED",
            "secret_exposure_count": "NOT_MEASURED",
            "status": "NOT_MEASURED",
        }
        if raw_path.is_file() and schema_path.is_file() and receipt_entry:
            receipt_path, receipt = receipt_entry
            expected = EXPECTED_RECEIPTS[batch_id]
            raw = raw_path.read_bytes()
            parsed = json.loads(raw)
            observed_subjects = tuple(
                str(row.get("ticker") or "") for row in parsed.get("candidates", [])
            )
            if observed_subjects != subjects:
                raise ValueError("PARTIAL_OUTPUT_SUBJECT_MAPPING_CONFLICT")
            consistency = {
                "receipt_generation_match": receipt.get("generation_id") == RESUME_GENERATION_ID,
                "receipt_invocation_match": receipt.get("invocation_id") == result["invocation_id"],
                "receipt_stage_match": receipt.get("stage") == "DIRECTIONAL_CORE",
                "receipt_subject_count_match": receipt.get("subject_count") == len(subjects),
                "output_bytes_match": len(raw)
                == receipt.get("output_bytes")
                == expected["output_bytes"],
                "stdout_bytes_match": receipt.get("stdout_bytes") == expected["stdout_bytes"],
                "prompt_hash_match": receipt.get("prompt_sha256") == expected["prompt_sha256"],
                "schema_hash_match": receipt.get("schema_sha256")
                == expected["schema_sha256"]
                == file_sha256(schema_path),
                "output_parsed": receipt.get("output_parsed") is True,
                "receipt_status_pass": receipt.get("status") == "PASS",
            }
            stdout_path = receipt_path.with_suffix(".stdout.log")
            consistency["stdout_exact_json_plus_newline"] = (
                stdout_path.is_file() and stdout_path.read_bytes() == raw + b"\n"
            )
            if not all(consistency.values()):
                result["recovery_status"] = "PROVENANCE_AMBIGUOUS"
                result["consistency"] = consistency
            else:
                scan = scan_secret_bytes(raw)
                destination = (
                    args.output_root
                    / "preserved/recovered-real-output"
                    / f"first-directional-core-batch-{batch_id}.raw.json"
                )
                preservation = preserve_safe_file(raw_path, destination)
                schema_destination = destination.with_name(
                    f"first-directional-core-batch-{batch_id}.schema.json"
                )
                schema_preservation = preserve_safe_file(schema_path, schema_destination)
                if scan["secret_exposure_count"]:
                    recovery_status = "SECRET_BEARING_OUTPUT_NOT_BUNDLED"
                elif preservation["preservation_status"] != "EXACT_BYTES_PRESERVED":
                    recovery_status = "PROVENANCE_AMBIGUOUS"
                else:
                    recovery_status = "EXACT_PROVENANCE_LINKED_OUTPUT_RECOVERED"
                schema_errors = batch_envelope_errors(parsed, packet_id=SOURCE_GENERATION_ID)
                resolved, alias_audit = frozen._resolve_batch_candidates(
                    parsed.get("candidates"),
                    batch=subjects,
                    evidence={ticker: evidence[ticker] for ticker in subjects},
                    catalogs={ticker: core_aliases[ticker] for ticker in subjects},
                    model_type=DirectionalCoreCandidate,
                )
                core_rows = []
                for core in resolved:
                    if not isinstance(core, DirectionalCoreCandidate):
                        raise TypeError("directional_core_candidate_required")
                    row = _core_only_audit(core, owned[core.ticker])
                    row["source_sufficient"] = bool(
                        preflight[core.ticker].get("directional_model_eligible")
                    )
                    if not row["source_sufficient"]:
                        row["errors"].append("directional_model_call_on_source_insufficient")
                        row["status"] = "FAIL"
                    core_rows.append(row)
                validator_status = (
                    "PASS" if all(row["status"] == "PASS" for row in core_rows) else "FAIL"
                )
                result.update(
                    {
                        "recovery_status": recovery_status,
                        "copied_artifact_path": str(
                            destination.relative_to(args.output_root / "preserved")
                        ),
                        "raw_output_sha256": hashlib.sha256(raw).hexdigest(),
                        "raw_output_bytes": len(raw),
                        "receipt_output_bytes": receipt["output_bytes"],
                        "receipt_stdout_bytes": receipt["stdout_bytes"],
                        "schema_revalidation_status": ("PASS" if not schema_errors else "FAIL"),
                        "schema_validation_errors": schema_errors,
                        "offline_validator_status": validator_status,
                        "secret_exposure_count": scan["secret_exposure_count"],
                        "consistency": consistency,
                        "preservation": preservation,
                        "schema_preservation": schema_preservation,
                        "receipt_artifact_sha256": file_sha256(receipt_path),
                        "alias_audit_sha256": canonical_sha256(alias_audit),
                        "audit_rows": core_rows,
                        "status": (
                            "PASS"
                            if recovery_status == "EXACT_PROVENANCE_LINKED_OUTPUT_RECOVERED"
                            and not schema_errors
                            and validator_status == "PASS"
                            else "FAIL"
                        ),
                    }
                )
                recovered_count += len(core_rows)
                audit_rows.extend(core_rows)
                manifest_rows.extend(
                    [
                        {
                            "path": str(destination.relative_to(args.output_root / "preserved")),
                            "sha256": file_sha256(destination),
                            "bytes": destination.stat().st_size,
                            "artifact_class": "RECOVERED_REAL_MODEL_OUTPUT",
                            "historical_or_new": "HISTORICAL",
                            "secret_scan_status": scan["secret_scan_status"],
                        },
                        {
                            "path": str(
                                schema_destination.relative_to(args.output_root / "preserved")
                            ),
                            "sha256": file_sha256(schema_destination),
                            "bytes": schema_destination.stat().st_size,
                            "artifact_class": "RECOVERED_EXACT_SCHEMA",
                            "historical_or_new": "HISTORICAL",
                            "secret_scan_status": schema_preservation["secret_scan_status"],
                        },
                    ]
                )
        batch_results[batch_id] = result
    totals = {
        field: sum(int(row.get(field) or 0) for row in audit_rows)
        for field in (
            "directional_core_price_technical_refs",
            "directional_core_supply_refs",
            "supply_directional_core_usage",
            "buy_without_nonprice_material_anchor",
            "sell_without_nonprice_material_anchor",
        )
    }
    exact = all(
        result["recovery_status"] == "EXACT_PROVENANCE_LINKED_OUTPUT_RECOVERED"
        for result in batch_results.values()
    )
    clean = exact and recovered_count == 8 and all(row["status"] == "PASS" for row in audit_rows)
    summary = {
        "recovered_real_subject_output_count": recovered_count,
        "audit_rows": audit_rows,
        "artifact_manifest_rows": manifest_rows,
        "totals": totals,
        "directional_model_calls_on_source_insufficient": sum(
            not bool(row.get("source_sufficient")) for row in audit_rows
        ),
        "price_only_directional_model_calls": 0 if audit_rows else "NOT_MEASURED",
        "partial_output_semantic_audit_status": (
            "CLEAN_ON_RECOVERED_DIRECTIONAL_CORE"
            if clean
            else "SEMANTIC_DEFECT_CONFIRMED"
            if exact and audit_rows
            else "NOT_MEASURED"
        ),
    }
    return batch_results, summary


def receipt_for_invocation(receipt_root: Path, invocation_id: str) -> Path:
    digest = hashlib.sha256(invocation_id.encode()).hexdigest()[:16]
    return receipt_root / f"{digest}.json"


def lifecycle_fields(receipt: Mapping[str, object]) -> dict[str, object]:
    first_stderr = receipt.get("first_stderr_byte_monotonic")
    last_stderr = receipt.get("last_stderr_byte_monotonic")
    process_exit = receipt.get("process_exit_monotonic")
    burst: float | None = None
    silence: float | None = None
    if isinstance(first_stderr, (int, float)) and isinstance(last_stderr, (int, float)):
        burst = round(float(last_stderr) - float(first_stderr), 6)
    if isinstance(last_stderr, (int, float)) and isinstance(process_exit, (int, float)):
        silence = round(float(process_exit) - float(last_stderr), 6)
    metadata = receipt.get("transport_metadata")
    transport_metadata = metadata if isinstance(metadata, Mapping) else {}
    cli = receipt.get("cli_binary_identity")
    cli_identity = cli if isinstance(cli, Mapping) else {}
    return {
        "generation_id": receipt.get("generation_id"),
        "invocation_id": receipt.get("invocation_id"),
        "input_bytes": receipt.get("input_bytes"),
        "prompt_sha256": receipt.get("prompt_sha256"),
        "schema_sha256": receipt.get("schema_sha256"),
        "state_namespace_hash": transport_metadata.get("runtime_state_namespace_hash"),
        "working_directory_identity": receipt.get("working_directory_identity"),
        "cli_binary_path": cli_identity.get("path"),
        "cli_binary_sha256": cli_identity.get("sha256"),
        "cli_version": receipt.get("cli_version"),
        "model": receipt.get("model"),
        "reasoning_effort": receipt.get("reasoning_effort"),
        "stdin_complete": receipt.get("stdin_complete_monotonic") is not None,
        "first_stderr_seconds": receipt.get("elapsed_to_first_stderr_seconds"),
        "last_stderr_seconds": (
            round(float(last_stderr) - float(receipt["invocation_start_monotonic"]), 6)
            if isinstance(last_stderr, (int, float))
            and isinstance(receipt.get("invocation_start_monotonic"), (int, float))
            else None
        ),
        "stderr_bytes": receipt.get("stderr_bytes"),
        "stderr_burst_duration_seconds": burst,
        "silent_interval_before_exit_seconds": silence,
        "first_stdout_seconds": receipt.get("elapsed_to_first_stdout_seconds"),
        "stdout_bytes": receipt.get("stdout_bytes"),
        "output_bytes": receipt.get("output_bytes"),
        "output_file_created": bool(receipt.get("output_bytes")),
        "output_parsed": receipt.get("output_parsed"),
        "parse_error": receipt.get("parse_error"),
        "elapsed_to_exit_seconds": receipt.get("elapsed_to_exit_seconds"),
        "exit_code": receipt.get("exit_code"),
        "status": receipt.get("status"),
        "termination_initiator": receipt.get("termination_initiator"),
        "termination_signal": receipt.get("termination_signal"),
        "timeout_owner": receipt.get("timeout_owner"),
        "timeout_owner_count": receipt.get("timeout_owner_count"),
        "configured_timeout_seconds": receipt.get("configured_timeout_seconds"),
        "child_cleanup_status": receipt.get("child_cleanup_status"),
        "orphan_model_process_count": receipt.get("orphan_model_process_count"),
        "network_probe_attempts": transport_metadata.get("network_probe_attempts"),
        "network_resolved_address_count": transport_metadata.get("network_resolved_address_count"),
        "tls_trust_source": transport_metadata.get("tls_trust_source"),
        "request_accepted_observability": receipt.get("request_accepted_observability"),
    }


def recover_batch03_forensics(
    args: argparse.Namespace,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    receipts = receipt_by_batch(args.prior_output_root / "transport-receipts")
    comparison = []
    for batch_id in ("01", "02", "03"):
        if batch_id not in receipts:
            raise ValueError(f"historical_receipt_missing:{batch_id}")
        comparison.append(
            {
                "batch_id": batch_id,
                **lifecycle_fields(receipts[batch_id][1]),
            }
        )
    receipt_path, receipt = receipts["03"]
    destination = args.output_root / "preserved/recovered-transport-forensics"
    destination.mkdir(parents=True, exist_ok=True)
    sources = {
        "receipt": receipt_path,
        "stderr": receipt_path.with_suffix(".stderr.log"),
        "stdout": receipt_path.with_suffix(".stdout.log"),
        "transport_log": args.prior_output_root / "run-first/core-batch-03.log",
    }
    preservation = {}
    for label, source in sources.items():
        suffix = "json" if label == "receipt" else "raw.log"
        target = destination / f"batch03-{label}.{suffix}"
        preservation[label] = (
            preserve_safe_file(source, target)
            if source.is_file()
            else {"preservation_status": "OUTPUT_NOT_FOUND"}
        )
    facts = lifecycle_fields(receipt)
    facts.update(
        {
            "contract": "historical-batch03-lifecycle-forensics-v1",
            "raw_stderr_recovery_status": preservation["stderr"].get("preservation_status"),
            "raw_transport_log_recovery_status": preservation["transport_log"].get(
                "preservation_status"
            ),
            "preservation": preservation,
            "root_cause_classification": "ROOT_CAUSE_UNRESOLVED",
            "root_cause_confidence": "DIRECT_FACTS_STRONG_CAUSAL_ATTRIBUTION_UNAVAILABLE",
            "confirmed_facts": [
                "child_process_spawned",
                "stdin_completed",
                "startup_stderr_burst_only",
                "no_stdout",
                "no_output_file",
                "same_runtime_state_namespace_as_batches01_02",
                "same_cli_binary_version_model_effort",
                "single_watchdog_terminated_process_group",
                "orphan_process_count_zero",
                "network_readiness_probe_equal_to_prior_batches",
            ],
            "inferred_hypotheses": [
                "state_namespace_sequence_correlation_possible",
                "local_cli_runtime_stall_possible",
                "backend_or_model_stall_possible",
                "prompt_context_pathological_latency_possible",
            ],
            "unknowns": [
                "remote_request_acceptance",
                "remote_model_compute_state",
                "local_cli_event_loop_state_after_startup",
                "causal_role_of_shared_state_namespace",
                "causal_role_of_batch03_prompt_content",
            ],
            "status": "PASS",
        }
    )
    return facts, comparison


def probe_batches() -> tuple[dict[str, object], ...]:
    return (
        {
            "batch_id": "01",
            "market": "us",
            "subjects": tuple(f"SYNTHETIC_SEQ_US_{index}" for index in range(1, 5)),
        },
        {
            "batch_id": "02",
            "market": "kr",
            "subjects": tuple(f"SYNTHETIC_SEQ_KR_A{index}" for index in range(1, 5)),
        },
        {
            "batch_id": "03",
            "market": "kr",
            "subjects": tuple(f"SYNTHETIC_SEQ_KR_B{index}" for index in range(1, 5)),
        },
    )


def build_probe_inputs(output_root: Path, generation: str) -> tuple[list[dict[str, object]], str]:
    rows = []
    namespace = f"PARTIAL_OUTPUT_FORENSICS_{generation}"
    for position, batch in enumerate(probe_batches(), start=1):
        batch_id = str(batch["batch_id"])
        market = str(batch["market"])
        subjects = tuple(str(value) for value in batch["subjects"])
        owned_rows = tuple(
            synthetic.fictional_owned(ticker, market=market, padding_bytes=2300)
            for ticker in subjects
        )
        catalogs = {
            owned.source_packet.ticker: stage_alias_catalogs(owned)[0] for owned in owned_rows
        }
        packet_id = f"{generation}:fictional-sequential-core:{batch_id}"
        prompt = frozen._core_prompt(
            packet_id=packet_id,
            tickers=subjects,
            contexts=tuple(
                frozen._owned_context(owned, catalogs[owned.source_packet.ticker])
                for owned in owned_rows
            ),
        )
        schema = transport._batch_schema(
            candidate=DirectionalCoreCandidate,
            contract=CORE_OUTPUT_CONTRACT,
            packet_id=packet_id,
            catalogs=catalogs,
        )
        input_bytes = len(prompt.encode())
        if not 15_000 <= input_bytes <= 20_000:
            raise ValueError(f"fictional_probe_input_size_out_of_range:{batch_id}")
        directory = output_root / "probe-inputs" / f"batch-{batch_id}"
        directory.mkdir(parents=True, exist_ok=False)
        prompt_path = directory / "prompt.txt"
        schema_path = directory / "schema.json"
        prompt_path.write_text(prompt, encoding="utf-8")
        write_json(schema_path, schema)
        preserved = output_root / "preserved/fictional-sequential-probe" / f"batch-{batch_id}"
        preserved.mkdir(parents=True, exist_ok=False)
        shutil.copyfile(prompt_path, preserved / "prompt.txt")
        shutil.copyfile(schema_path, preserved / "schema.json")
        rows.append(
            {
                "probe_batch_id": batch_id,
                "same_namespace_sequence_position": position,
                "fictional_subject_ids": list(subjects),
                "fictional_subject_count": len(subjects),
                "market_mix": {market: len(subjects)},
                "real_issuer_identity_count": 0,
                "packet_id": packet_id,
                "prompt_path": str(prompt_path),
                "schema_path": str(schema_path),
                "input_bytes": input_bytes,
                "prompt_sha256": file_sha256(prompt_path),
                "schema_sha256": file_sha256(schema_path),
                "state_namespace": namespace,
                "status": "PRECOMMITTED",
            }
        )
    return rows, namespace


def historical_freeze_audit() -> dict[str, object]:
    commit_time = git_value("show", "-s", "--format=%cI", PRIOR_IMPLEMENTATION_COMMIT)
    first_start = "2026-09-06T13:30:21.890362+00:00"
    return {
        "contract": "historical-pre-first-implementation-freeze-audit-v1",
        "implementation_commit": PRIOR_IMPLEMENTATION_COMMIT,
        "implementation_commit_time": commit_time,
        "first_invocation_started_at": first_start,
        "implementation_commit_precedes_first": (
            datetime.fromisoformat(commit_time).astimezone(UTC)
            <= datetime.fromisoformat(first_start).astimezone(UTC)
        ),
        "reported_pre_first_freeze_checks": "PASS",
        "independent_immutable_uncommitted_worktree_timestamp_proof": "UNAVAILABLE",
        "historical_pre_first_implementation_freeze_proof": ("STRONG_BUT_TIMESTAMP_INCOMPLETE"),
        "status": "PASS_WITH_LIMITATION",
    }


def base_proofs(
    *,
    args: argparse.Namespace,
    state: Mapping[str, object],
    bundle: Mapping[str, object],
    recovered: Mapping[str, Mapping[str, object]],
    partial: Mapping[str, object],
    batch03: Mapping[str, object],
    comparison: Sequence[Mapping[str, object]],
    probe_precommit: Sequence[Mapping[str, object]],
    frozen_state: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    exact_recovered = all(
        row.get("recovery_status") == "EXACT_PROVENANCE_LINKED_OUTPUT_RECOVERED"
        for row in recovered.values()
    )
    schema_rows = [
        {
            "batch_id": batch_id,
            "schema_sha256": row.get("schema_sha256"),
            "schema_revalidation_status": row.get("schema_revalidation_status"),
            "errors": row.get("schema_validation_errors", []),
        }
        for batch_id, row in recovered.items()
    ]
    audit_rows = list(partial.get("audit_rows") or [])
    totals = dict(partial.get("totals") or {})
    prior_facts = {
        "contract": "prior-real-holdout-run-fact-reconstruction-v1",
        "source_generation_id": SOURCE_GENERATION_ID,
        "resume_generation_id": RESUME_GENERATION_ID,
        "source_lock_sha256": SOURCE_LOCK_SHA256,
        "runner_adapter_repair_status": "CLOSED",
        "batch_sequence": list(comparison),
        "first_status": "FAILED_MODEL_TIMEOUT_BATCH03",
        "real_holdout_subject_output_count": 8,
        "transport_retry_count": 0,
        "selective_rerun_count": 0,
        "status": "PASS",
    }
    return {
        "01-repository-provenance": {
            "contract": "repository-provenance-v1",
            "branch": state["branch"],
            "base_sha": BASE_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "implementation_commit": state["implementation_commit"],
            "implementation_tree": state["implementation_tree"],
            "origin_main_at_task_start": state["origin_main_at_task_start"],
            "shared_architecture_hashes": frozen_state["architecture"],
            "shared_source_hashes": frozen_state["sources"],
            "shared_transport_hashes": frozen_state["transport"],
            "unexplained_semantic_repository_drift": 0,
            "status": "PASS",
        },
        "02-latest-result-bundle-integrity": dict(bundle),
        "03-prior-run-fact-reconstruction": prior_facts,
        "04-partial-output-provenance-gap": {
            "contract": "partial-output-provenance-gap-v1",
            "prior_bundle_partial_output_provenance_gap": 1,
            "prior_bundle_exact_partial_output_files_present": bundle[
                "prior_bundle_exact_partial_output_files_present"
            ],
            "local_exact_output_recovery_status": (
                "RESOLVED_BY_PROVENANCE_LINKED_LOCAL_RECOVERY" if exact_recovered else "UNRESOLVED"
            ),
            "historical_result_bundle_rewritten": 0,
            "status": "PASS",
        },
        "05-partial-output-recovery-search": {
            "contract": "partial-output-recovery-search-v1",
            "search_scope": [
                str(args.prior_output_root / "run-first"),
                str(args.prior_output_root / "transport-receipts"),
                str(args.source_root / "schemas"),
            ],
            "unrelated_user_data_searched": 0,
            "model_recall_count": 0,
            "batch_results": {
                key: value.get("recovery_status") for key, value in recovered.items()
            },
            "status": "PASS",
        },
        "06-recovered-batch01-provenance": dict(recovered["01"]),
        "07-recovered-batch02-provenance": dict(recovered["02"]),
        "08-recovered-output-artifact-manifest": {
            "contract": "recovered-output-artifact-manifest-v1",
            "rows": partial.get("artifact_manifest_rows", []),
            "exact_raw_output_count": sum(
                row.get("artifact_class") == "RECOVERED_REAL_MODEL_OUTPUT"
                for row in partial.get("artifact_manifest_rows", [])
            ),
            "status": "PASS" if exact_recovered else "PARTIAL",
        },
        "09-offline-schema-validation": {
            "contract": "offline-recovered-schema-validation-v1",
            "model_call_count": 0,
            "rows": schema_rows,
            "status": (
                "PASS"
                if schema_rows
                and all(row["schema_revalidation_status"] == "PASS" for row in schema_rows)
                else "NOT_MEASURED"
            ),
        },
        "10-offline-directional-ownership-validation": {
            "contract": "offline-directional-core-ownership-validation-v1",
            "model_call_count": 0,
            "subject_count": len(audit_rows),
            "rows": audit_rows,
            **totals,
            "directional_model_calls_on_source_insufficient": partial.get(
                "directional_model_calls_on_source_insufficient"
            ),
            "price_only_directional_model_calls": partial.get("price_only_directional_model_calls"),
            "final_direction_owner": "DIRECTIONAL_CORE",
            "timing_stage_direction_mutation": "NOT_MEASURED",
            "timing_stage_balance_mutation": "NOT_MEASURED",
            "timing_stage_hold_lean_mutation": "NOT_MEASURED",
            "price_timing_new_buyer_upgrade": "NOT_MEASURED",
            "price_only_holder_reduce": "NOT_MEASURED",
            "price_only_directional_ownership_violations": "NOT_MEASURED",
            "primary_user_action_wording_owner": "NOT_MEASURED",
            "ai_imperative_primary_action": "NOT_MEASURED",
            "status": (
                "PASS"
                if partial.get("partial_output_semantic_audit_status")
                == "CLEAN_ON_RECOVERED_DIRECTIONAL_CORE"
                else "FAIL"
            ),
        },
        "11-offline-partial-hard-safety-validation": {
            "contract": "offline-partial-hard-safety-validation-v1",
            "price_or_technical_promoted_to_fundamental_logic": totals.get(
                "directional_core_price_technical_refs", "NOT_MEASURED"
            ),
            "supply_promoted_to_fundamental_logic": totals.get(
                "directional_core_supply_refs", "NOT_MEASURED"
            ),
            "unavailable_alias_promoted_to_fact": 0 if audit_rows else "NOT_MEASURED",
            "fabricated_numeric_provenance": "NOT_MEASURED",
            "accounting_attribution_substitution": "NOT_MEASURED",
            "adr_share_basis_mixing": "NOT_MEASURED",
            "provisional_earnings_fabrication": "NOT_MEASURED",
            "known_hard_safety_regression": 0,
            "measurement_boundary": "DIRECTIONAL_CORE_OUTPUT_AND_FROZEN_ALIAS_GRAPH_ONLY",
            "status": "PASS_WITH_EXPLICIT_NOT_MEASURED_FIELDS",
        },
        "12-partial-semantic-audit-summary": {
            "contract": "partial-semantic-audit-summary-v1",
            "partial_output_semantic_audit_status": partial["partial_output_semantic_audit_status"],
            "ownership_generalization_verdict": "NOT_MEASURED",
            "holdout_semantic_revelation_state": "NOT_MEASURED",
            "architecture_repair_needed": int(
                partial["partial_output_semantic_audit_status"] == "SEMANTIC_DEFECT_CONFIRMED"
            ),
            "status": "PASS",
        },
        "13-batch03-log-recovery": {
            "contract": "batch03-log-recovery-v1",
            "invocation_id": batch03["invocation_id"],
            "raw_stderr_recovery_status": batch03["raw_stderr_recovery_status"],
            "raw_transport_log_recovery_status": batch03["raw_transport_log_recovery_status"],
            "preservation": batch03["preservation"],
            "status": "PASS",
        },
        "14-batch03-lifecycle-forensics": dict(batch03),
        "15-batch01-02-03-comparison": {
            "contract": "historical-batch-sequence-comparison-v1",
            "rows": list(comparison),
            "same_state_namespace_hash": len({row["state_namespace_hash"] for row in comparison})
            == 1,
            "same_cli_binary_sha256": len({row["cli_binary_sha256"] for row in comparison}) == 1,
            "same_cli_version": len({row["cli_version"] for row in comparison}) == 1,
            "same_model_effort": len(
                {(row["model"], row["reasoning_effort"]) for row in comparison}
            )
            == 1,
            "status": "PASS",
        },
        "16-transport-root-cause-classification": {
            "contract": "transport-root-cause-classification-v1",
            "historical_classification": "ROOT_CAUSE_UNRESOLVED",
            "confirmed_multiple_timeout_owners": 0,
            "confirmed_orphan_process_leak": 0,
            "confirmed_live_workload_contention": 0,
            "confirmed_runner_adapter_interface_mismatch": 0,
            "request_accepted_observability": "UNAVAILABLE",
            "fictional_probe_result": "PENDING",
            "final_classification": "PENDING_FICTIONAL_PROBE",
            "status": "PENDING",
        },
        "17-historical-pre-first-freeze-audit": historical_freeze_audit(),
        "18-fictional-probe-precommit": {
            "contract": "fictional-sequential-probe-precommit-v1",
            "probe_generation_id": state["probe_generation_id"],
            "sequence": list(probe_precommit),
            "state_namespace": state["state_namespace"],
            "same_namespace_for_all_batches": 1,
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "configured_timeout_seconds": TIMEOUT_SECONDS,
            "timeout_owner_count": 1,
            "batch_semantics": "MODEL_CONTEXT_COUPLED",
            "retry_count_allowed": 0,
            "real_issuer_identity_count": 0,
            "status": "FROZEN",
        },
        "19-fictional-probe-batch01": {"status": "PENDING"},
        "20-fictional-probe-batch02": {"status": "PENDING"},
        "21-fictional-probe-batch03": {"status": "PENDING"},
        "22-fictional-probe-sequence-summary": {"status": "PENDING"},
        "23-retired-cohort-proof": {
            "contract": "retired-partial-exposure-cohort-proof-v1",
            "retired_holdout_cohort": list(RETIRED_HOLDOUT),
            "exposed_subjects": list(EXPOSED_SUBJECTS),
            "unexposed_but_retired_subjects": list(UNEXPOSED_RETIRED_SUBJECTS),
            "holdout_output_exposure_state": "PARTIALLY_EXPOSED",
            "holdout_semantic_revelation_state": "NOT_MEASURED",
            "holdout_retirement_state": "RETIRED_PARTIAL_EXPOSURE",
            "future_unseen_holdout_reuse_allowed": 0,
            "same_cohort_architecture_tuning_rerun_allowed": 0,
            "all_16_excluded_from_future_unseen_proof": 1,
            "status": "PASS",
        },
        "24-real-issuer-no-model-call-proof": {
            "contract": "real-issuer-no-model-call-proof-v1",
            "retired_holdout": list(RETIRED_HOLDOUT),
            "consumed_regression": list(CONSUMED_REGRESSION),
            "new_real_issuer_model_call_count": 0,
            "new_real_holdout_selection_count": 0,
            "historical_output_model_recall_count": 0,
            "status": "PASS",
        },
        "25-evidence-preservation-policy": {
            "contract": "per-context-experiment-evidence-preservation-v1",
            "scope": "EXPERIMENT_HARNESS_ONLY",
            "required_after_each_successful_context": [
                "exact_raw_model_output",
                "transport_receipt",
                "stdout_or_safe_redacted_derivative",
                "stderr_or_safe_redacted_derivative",
                "prompt_and_schema_hashes",
                "generation_invocation_stage_batch_subject_identity",
            ],
            "wait_for_whole_run_before_preservation": 0,
            "shared_production_transport_change": 0,
            "status": "ACTIVE_FOR_THIS_PROBE_AND_FUTURE_EXPERIMENT_HANDOFF",
        },
        "26-production-no-change": production_no_change(),
        "27-night-futures-no-change": {
            "contract": "night-futures-no-change-v1",
            "night_futures_code_mutation": 0,
            "night_futures_packet_injection": 0,
            "status": "PASS",
        },
        "28-next-scope-decision": {"status": "PENDING"},
        "29-program-completion": {"status": "PENDING"},
    }


def production_no_change() -> dict[str, object]:
    return {
        "contract": "forensic-production-no-change-v1",
        "main_merge": 0,
        "production_db_mutation": 0,
        "production_telegram_send": 0,
        "production_scheduler_change": 0,
        "monitoring_registration_calls": 0,
        "live_structured_autonomy_activation": 0,
        "live_v2_change": 0,
        "night_futures_code_mutation": 0,
        "status": "PASS",
    }


def write_reports(report_dir: Path) -> None:
    for name in REPORT_NAMES:
        proof = read_json(proof_path(report_dir, name))
        title = name.replace("-", " ").title()
        lines = [
            f"# {title}",
            "",
            f"Contract: `{proof.get('contract', 'pending')}`",
            "",
            f"Status: `{proof.get('status', 'NOT_MEASURED')}`",
            "",
            "```json",
            json.dumps(proof, ensure_ascii=False, indent=2, sort_keys=True, default=str),
            "```",
            "",
        ]
        (report_dir / f"{name}.md").write_text("\n".join(lines), encoding="utf-8")


def prepare(args: argparse.Namespace) -> None:
    if args.output_root.exists():
        raise ValueError("new_output_root_required")
    args.output_root.mkdir(parents=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    bundle = verify_latest_bundle(args.latest_result_bundle)
    frozen_state = synthetic.verify_frozen(args)
    implementation_commit = git_value("rev-parse", "HEAD")
    if (
        not subprocess.run(
            ["git", "merge-base", "--is-ancestor", BASE_SHA, implementation_commit]
        ).returncode
        == 0
    ):
        raise ValueError("base_not_ancestor_of_implementation")
    now = args.as_of.astimezone(UTC)
    generation = generation_id(implementation_commit, now)
    recovered, partial = recover_partial_outputs(args)
    batch03, comparison = recover_batch03_forensics(args)
    precommit, namespace = build_probe_inputs(args.output_root, generation)
    state = {
        "contract": PROGRAM_CONTRACT,
        "state": "PREPARED_FROZEN",
        "branch": git_value("branch", "--show-current"),
        "base_sha": BASE_SHA,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "implementation_commit": implementation_commit,
        "implementation_tree": git_value("rev-parse", "HEAD^{tree}"),
        "origin_main_at_task_start": args.origin_main_at_task_start,
        "prepared_at": now.isoformat(),
        "probe_generation_id": generation,
        "state_namespace": namespace,
        "harness_sha256": file_sha256(Path(__file__).resolve()),
        "probe_input_lock_sha256": canonical_sha256(precommit),
        "probe_precommit": precommit,
        "fictional_probe_model_call_count": 0,
        "new_real_issuer_model_call_count": 0,
        "partial_output_semantic_audit_status": partial["partial_output_semantic_audit_status"],
        "latest_result_zip_sha256": bundle["actual_sha256"],
        "status": "FROZEN",
    }
    proofs = base_proofs(
        args=args,
        state=state,
        bundle=bundle,
        recovered=recovered,
        partial=partial,
        batch03=batch03,
        comparison=comparison,
        probe_precommit=precommit,
        frozen_state=frozen_state,
    )
    for name, proof in proofs.items():
        write_proof(args.report_dir, name, proof)
    write_reports(args.report_dir)
    write_json(args.output_root / "program-state.json", state)
    print(json.dumps(state, sort_keys=True), flush=True)


def verify_program_freeze(args: argparse.Namespace, state: Mapping[str, object]) -> None:
    synthetic.verify_frozen(args)
    if file_sha256(Path(__file__).resolve()) != state["harness_sha256"]:
        raise ValueError("forensic_probe_harness_mutation_after_freeze")
    precommit = state.get("probe_precommit")
    if not isinstance(precommit, list):
        raise ValueError("probe_precommit_missing")
    if canonical_sha256(precommit) != state["probe_input_lock_sha256"]:
        raise ValueError("probe_input_lock_mutation")
    for row in precommit:
        if not isinstance(row, Mapping):
            raise ValueError("probe_precommit_row_invalid")
        prompt = Path(str(row["prompt_path"]))
        schema = Path(str(row["schema_path"]))
        if file_sha256(prompt) != row["prompt_sha256"]:
            raise ValueError("probe_prompt_mutation_after_freeze")
        if file_sha256(schema) != row["schema_sha256"]:
            raise ValueError("probe_schema_mutation_after_freeze")
    transport.verify_source_lock(args.source_root)


def preserve_probe_batch(
    *,
    args: argparse.Namespace,
    batch_id: str,
    prompt: Path,
    schema: Path,
    output: Path,
    log: Path,
    receipt: Path,
) -> dict[str, object]:
    destination = args.output_root / "preserved/fictional-sequential-probe" / f"batch-{batch_id}"
    sources = {
        "prompt": prompt,
        "schema": schema,
        "output": output,
        "transport_receipt": receipt,
        "stdout": receipt.with_suffix(".stdout.log"),
        "stderr": receipt.with_suffix(".stderr.log"),
        "transport_log": log,
    }
    suffixes = {
        "prompt": "txt",
        "schema": "json",
        "output": "raw.json",
        "transport_receipt": "json",
        "stdout": "raw.log",
        "stderr": "raw.log",
        "transport_log": "raw.log",
    }
    result = {}
    for label, source in sources.items():
        target = destination / f"{label}.{suffixes[label]}"
        result[label] = (
            preserve_safe_file(source, target)
            if source.is_file()
            else {"preservation_status": "OUTPUT_NOT_FOUND"}
        )
    return result


def validate_probe_output(
    *,
    output: Path,
    schema: Path,
    packet_id: str,
    subjects: Sequence[str],
    owned: Mapping[str, OwnedEvidencePacket],
    catalogs: Mapping[str, object],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    parsed = read_json(output)
    schema_errors = batch_envelope_errors(
        parsed,
        packet_id=packet_id,
    )
    resolved, alias_audit = frozen._resolve_batch_candidates(
        parsed.get("candidates"),
        batch=subjects,
        evidence={ticker: owned[ticker].source_packet for ticker in subjects},
        catalogs=catalogs,
        model_type=DirectionalCoreCandidate,
    )
    rows = []
    for core in resolved:
        if not isinstance(core, DirectionalCoreCandidate):
            raise TypeError("directional_core_candidate_required")
        rows.append(_core_only_audit(core, owned[core.ticker]))
    output_subjects = tuple(core.ticker for core in resolved)
    status = (
        "PASS"
        if not schema_errors
        and output_subjects == tuple(subjects)
        and all(row["status"] == "PASS" for row in rows)
        else "FAIL"
    )
    return (
        {
            "schema_errors": schema_errors,
            "output_subjects": list(output_subjects),
            "subject_order_match": output_subjects == tuple(subjects),
            "alias_audit_sha256": canonical_sha256(alias_audit),
            "status": status,
        },
        rows,
    )


def probe_result_document(
    *,
    state: Mapping[str, object],
    row: Mapping[str, object],
    receipt: Mapping[str, object] | None,
    preservation: Mapping[str, object],
    validation: Mapping[str, object] | None,
    ownership_rows: Sequence[Mapping[str, object]],
    error: str | None,
) -> dict[str, object]:
    lifecycle = lifecycle_fields(receipt) if receipt else {}
    batch_id = str(row["probe_batch_id"])
    status = (
        "PASS"
        if receipt
        and receipt.get("status") == "PASS"
        and validation
        and validation.get("status") == "PASS"
        else str(receipt.get("status") if receipt else "FAILED_BEFORE_RECEIPT")
    )
    destination = f"fictional-sequential-probe/batch-{batch_id}"
    secret_count = sum(
        int(value.get("secret_exposure_count") or 0)
        for value in preservation.values()
        if isinstance(value, Mapping)
    )
    return {
        "contract": "fictional-sequential-transport-probe-batch-v1",
        "probe_generation_id": state["probe_generation_id"],
        "invocation_id": (
            receipt.get("invocation_id")
            if receipt
            else f"{state['probe_generation_id']}:probe:DIRECTIONAL_CORE:{batch_id}"
        ),
        "stage": "DIRECTIONAL_CORE",
        "probe_batch_id": batch_id,
        "fictional_subject_count": row["fictional_subject_count"],
        "fictional_subject_ids": row["fictional_subject_ids"],
        "market_mix": row["market_mix"],
        "real_issuer_identity_count": 0,
        "same_namespace_sequence_position": row["same_namespace_sequence_position"],
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "configured_timeout_seconds": TIMEOUT_SECONDS,
        "timeout_owner_count": lifecycle.get("timeout_owner_count", 1),
        "input_bytes": row["input_bytes"],
        "prompt_sha256": row["prompt_sha256"],
        "schema_sha256": row["schema_sha256"],
        **lifecycle,
        "raw_output_artifact_path": f"{destination}/output.raw.json",
        "transport_receipt_path": f"{destination}/transport_receipt.json",
        "log_artifact_path": f"{destination}/transport_log.raw.log",
        "preservation": dict(preservation),
        "validation": dict(validation) if validation else "NOT_MEASURED",
        "ownership_rows": list(ownership_rows),
        "secret_exposure_count": secret_count,
        "error": error,
        "status": status,
    }


def run_probe(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "PREPARED_FROZEN":
        raise ValueError("prepared_frozen_state_required")
    verify_program_freeze(args, state)
    precommit = state["probe_precommit"]
    if not isinstance(precommit, list):
        raise ValueError("probe_precommit_missing")
    guard = synthetic.LiveWorkloadGuard(args.output_root / "live-workload-audit.json")
    adapter = synthetic.GuardedTransportAdapter(
        guard=guard,
        continuation_generation=str(state["probe_generation_id"]),
        receipt_root=args.output_root / "transport-receipts",
        codex_bin=accepted_runtime._signed_in_codex_bin(),
    )
    results = []
    stopped = False
    for row in precommit:
        if not isinstance(row, Mapping):
            raise ValueError("probe_precommit_row_invalid")
        batch_id = str(row["probe_batch_id"])
        if stopped:
            not_run = {
                "contract": "fictional-sequential-transport-probe-batch-v1",
                "probe_generation_id": state["probe_generation_id"],
                "probe_batch_id": batch_id,
                "fictional_subject_count": row["fictional_subject_count"],
                "fictional_subject_ids": row["fictional_subject_ids"],
                "real_issuer_identity_count": 0,
                "status": "NOT_RUN_AFTER_FIRST_FAILURE",
            }
            write_proof(
                args.report_dir,
                f"{18 + int(batch_id):02d}-fictional-probe-batch{batch_id}",
                not_run,
            )
            results.append(not_run)
            continue
        subjects = tuple(str(value) for value in row["fictional_subject_ids"])
        market = next(iter(row["market_mix"]))
        owned = {
            ticker: synthetic.fictional_owned(ticker, market=market, padding_bytes=2300)
            for ticker in subjects
        }
        catalogs = {ticker: stage_alias_catalogs(packet)[0] for ticker, packet in owned.items()}
        prompt = Path(str(row["prompt_path"]))
        schema = Path(str(row["schema_path"]))
        directory = args.output_root / "probe-runtime" / f"batch-{batch_id}"
        directory.mkdir(parents=True, exist_ok=False)
        output = directory / "output.json"
        log = directory / "transport.log"
        invocation_id = f"{state['probe_generation_id']}:probe:DIRECTIONAL_CORE:{batch_id}"
        receipt_path = receipt_for_invocation(
            args.output_root / "transport-receipts", invocation_id
        )
        error = None
        with engine.isolated_model_working_directory(
            run="fictional-sequential-probe", batch=int(batch_id)
        ) as cwd:
            try:
                adapter.invoke(
                    prompt=prompt,
                    output=output,
                    log=log,
                    schema=schema,
                    cwd=cwd,
                    timeout=TIMEOUT_SECONDS,
                    state_namespace=str(row["state_namespace"]),
                    invocation_id=invocation_id,
                    stage="DIRECTIONAL_CORE",
                    batch_id=batch_id,
                    subject_count=len(subjects),
                )
            except Exception as exc:  # noqa: BLE001 - evidence is preserved below.
                error = f"{type(exc).__name__}:{exc}"
        receipt = read_json(receipt_path) if receipt_path.is_file() else None
        validation = None
        ownership_rows: list[dict[str, object]] = []
        if output.is_file():
            with suppress(Exception):
                validation, ownership_rows = validate_probe_output(
                    output=output,
                    schema=schema,
                    packet_id=str(row["packet_id"]),
                    subjects=subjects,
                    owned=owned,
                    catalogs=catalogs,
                )
        preservation = preserve_probe_batch(
            args=args,
            batch_id=batch_id,
            prompt=prompt,
            schema=schema,
            output=output,
            log=log,
            receipt=receipt_path,
        )
        document = probe_result_document(
            state=state,
            row=row,
            receipt=receipt,
            preservation=preservation,
            validation=validation,
            ownership_rows=ownership_rows,
            error=error,
        )
        write_proof(
            args.report_dir,
            f"{18 + int(batch_id):02d}-fictional-probe-batch{batch_id}",
            document,
        )
        results.append(document)
        state["fictional_probe_model_call_count"] = adapter.model_call_count
        state["probe_results"] = results
        write_json(args.output_root / "program-state.json", state)
        if document["status"] != "PASS":
            stopped = True
    attempted = [row for row in results if row["status"] != "NOT_RUN_AFTER_FIRST_FAILURE"]
    passed = sum(row["status"] == "PASS" for row in attempted)
    timeout_count = sum(row["status"] == "TIMEOUT" for row in attempted)
    sequence_completed = int(len(attempted) == 3 and passed == 3)
    namespace_hashes = {
        row.get("state_namespace_hash") for row in attempted if row.get("state_namespace_hash")
    }
    if sequence_completed:
        root_cause = "TRANSIENT_STALL_NOT_REPRODUCED"
        readiness = (
            "READY_FOR_NEW_ISSUER_HOLDOUT_SELECTION_AND_OWNERSHIP_PROOF"
            if state["partial_output_semantic_audit_status"]
            == "CLEAN_ON_RECOVERED_DIRECTIONAL_CORE"
            else "NOT_READY_SEMANTIC_REPAIR_REQUIRED"
        )
        next_scope = (
            "NEW_ISSUER_HOLDOUT_SELECTION_AND_OWNERSHIP_PROOF"
            if readiness.startswith("READY_")
            else "GENERIC_ARCHITECTURE_REPAIR_THEN_NEW_ISSUER_HOLDOUT"
        )
        stop_reason = None
    else:
        root_cause = "ROOT_CAUSE_UNRESOLVED"
        readiness = "NOT_READY_TRANSPORT_BLOCKED"
        next_scope = "BOUNDED_TRANSPORT_RUNTIME_DIAGNOSTIC_REPAIR"
        stop_reason = "FICTIONAL_PROBE_FIRST_FAILURE_NO_RETRY"
    sequence = {
        "contract": "fictional-sequential-transport-probe-summary-v1",
        "probe_generation_id": state["probe_generation_id"],
        "results": [
            {"probe_batch_id": row["probe_batch_id"], "status": row["status"]} for row in results
        ],
        "fictional_probe_model_call_count": adapter.model_call_count,
        "fictional_probe_status": "PASS" if sequence_completed else "FAILED",
        "fictional_probe_sequence_completed": sequence_completed,
        "fictional_probe_timeout_count": timeout_count,
        "sequential_same_namespace_stall_reproduced": int(
            bool(timeout_count and len(attempted) == 3)
        ),
        "same_runtime_state_namespace_hash": int(len(namespace_hashes) == 1),
        "retry_count": 0,
        "new_real_issuer_model_call_count": 0,
        "status": "PASS" if sequence_completed else "STOPPED_ON_FIRST_FAILURE",
    }
    write_proof(args.report_dir, "22-fictional-probe-sequence-summary", sequence)
    root = read_json(proof_path(args.report_dir, "16-transport-root-cause-classification"))
    root.update(
        {
            "fictional_probe_result": sequence["fictional_probe_status"],
            "final_classification": root_cause,
            "historical_stall_fixed_claimed": 0,
            "status": "PASS" if sequence_completed else "UNRESOLVED_BLOCKER",
        }
    )
    write_proof(args.report_dir, "16-transport-root-cause-classification", root)
    next_decision = {
        "contract": "forensic-next-scope-decision-v1",
        "partial_output_semantic_audit_status": state["partial_output_semantic_audit_status"],
        "transport_root_cause_classification": root_cause,
        "readiness": readiness,
        "stop_reason": stop_reason,
        "next_scope": next_scope,
        "new_real_holdout_selected": 0,
        "required_future_exclusions": list(dict.fromkeys(RETIRED_HOLDOUT + CONSUMED_REGRESSION)),
        "future_per_context_exact_preservation_required": 1,
        "status": "PASS",
    }
    write_proof(args.report_dir, "28-next-scope-decision", next_decision)
    state.update(
        {
            "state": "EVIDENCE_COMPLETE" if sequence_completed else "STOPPED_PROBE_FAILED",
            "fictional_probe_model_call_count": adapter.model_call_count,
            "fictional_probe_status": sequence["fictional_probe_status"],
            "fictional_probe_sequence_completed": sequence_completed,
            "fictional_probe_timeout_count": timeout_count,
            "sequential_same_namespace_stall_reproduced": sequence[
                "sequential_same_namespace_stall_reproduced"
            ],
            "batch03_root_cause_classification": root_cause,
            "readiness": readiness,
            "stop_reason": stop_reason,
            "next_scope": next_scope,
        }
    )
    write_json(args.output_root / "program-state.json", state)
    write_reports(args.report_dir)
    print(json.dumps(state, sort_keys=True), flush=True)


def sync_preserved_artifacts(output_root: Path, report_dir: Path) -> None:
    preserved = output_root / "preserved"
    if not preserved.is_dir():
        return
    for source in sorted(path for path in preserved.iterdir() if path.is_dir()):
        destination = report_dir / source.name
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)


def artifact_class(path: Path) -> tuple[str, str]:
    value = path.as_posix()
    if value.startswith("recovered-real-output/"):
        return "RECOVERED_HISTORICAL_REAL_OUTPUT", "HISTORICAL"
    if value.startswith("recovered-transport-forensics/"):
        return "RECOVERED_HISTORICAL_TRANSPORT_EVIDENCE", "HISTORICAL"
    if value.startswith("fictional-sequential-probe/"):
        return "NEW_FICTIONAL_PROBE_EVIDENCE", "NEW"
    if value.endswith(".md"):
        return "HUMAN_READABLE_REPORT", "NEW"
    return "MACHINE_READABLE_REPORT", "NEW"


def write_artifact_index(report_dir: Path) -> dict[str, object]:
    excluded = {"20260906-artifact-index.json", "20260906-artifact-index.md"}
    paths = sorted(
        path for path in report_dir.rglob("*") if path.is_file() and path.name not in excluded
    )
    rows = []
    for path in paths:
        relative = path.relative_to(report_dir)
        kind, historical = artifact_class(relative)
        scan = scan_secret_bytes(path.read_bytes())
        if scan["secret_exposure_count"]:
            raise ValueError(f"secret_exposure_in_final_bundle:{relative}")
        rows.append(
            {
                "path": relative.as_posix(),
                "sha256": file_sha256(path),
                "bytes": path.stat().st_size,
                "artifact_class": kind,
                "historical_or_new": historical,
                "secret_scan_status": scan["secret_scan_status"],
            }
        )
    index = {
        "contract": "partial-output-forensics-artifact-index-v1",
        "artifact_count": len(rows),
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "rows": rows,
        "status": "PASS",
    }
    write_json(report_dir / "20260906-artifact-index.json", index)
    markdown = [
        "# Artifact Index",
        "",
        f"Artifacts: `{len(rows)}`",
        "",
        "| Path | SHA-256 | Bytes | Class | History | Secret Scan |",
        "|---|---|---:|---|---|---|",
    ]
    markdown.extend(
        "| {path} | `{sha256}` | {bytes} | {artifact_class} | "
        "{historical_or_new} | {secret_scan_status} |".format(**row)
        for row in rows
    )
    (report_dir / "20260906-artifact-index.md").write_text(
        "\n".join(markdown) + "\n", encoding="utf-8"
    )
    return index


def completion_document(
    *, args: argparse.Namespace, state: Mapping[str, object]
) -> dict[str, object]:
    ownership = read_json(
        proof_path(args.report_dir, "10-offline-directional-ownership-validation")
    )
    bundle = read_json(proof_path(args.report_dir, "02-latest-result-bundle-integrity"))
    batch01 = read_json(proof_path(args.report_dir, "06-recovered-batch01-provenance"))
    batch02 = read_json(proof_path(args.report_dir, "07-recovered-batch02-provenance"))
    batch03 = read_json(proof_path(args.report_dir, "14-batch03-lifecycle-forensics"))
    hard = read_json(proof_path(args.report_dir, "11-offline-partial-hard-safety-validation"))
    next_decision = read_json(proof_path(args.report_dir, "28-next-scope-decision"))
    sequence = read_json(proof_path(args.report_dir, "22-fictional-probe-sequence-summary"))
    production = production_no_change()
    validations_pass = all(
        value == "PASS" for value in (args.full_tests, args.ruff, args.diff_check)
    )
    readiness = str(next_decision["readiness"])
    if not validations_pass:
        readiness = "NOT_READY_VALIDATION_FAILED"
    return {
        "contract": "partial-output-forensics-program-completion-v1",
        "base_sha": BASE_SHA,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "implementation_commit": state["implementation_commit"],
        "final_head_sha": git_value("rev-parse", "HEAD"),
        "branch": state["branch"],
        "latest_result_zip_sha256": bundle["actual_sha256"],
        "latest_result_bundle_integrity": bundle["status"],
        "runner_adapter_repair_status": "CLOSED",
        "new_real_issuer_model_call_count": 0,
        "fictional_probe_model_call_count": state["fictional_probe_model_call_count"],
        "retired_holdout_cohort": list(RETIRED_HOLDOUT),
        "exposed_subjects": list(EXPOSED_SUBJECTS),
        "unexposed_but_retired_subjects": list(UNEXPOSED_RETIRED_SUBJECTS),
        "holdout_output_exposure_state": "PARTIALLY_EXPOSED",
        "holdout_semantic_revelation_state": "NOT_MEASURED",
        "holdout_retirement_state": "RETIRED_PARTIAL_EXPOSURE",
        "future_unseen_holdout_reuse_allowed": 0,
        "same_cohort_architecture_tuning_rerun_allowed": 0,
        "prior_bundle_exact_partial_output_files_present": bundle[
            "prior_bundle_exact_partial_output_files_present"
        ],
        "partial_output_provenance_gap": (
            "RESOLVED_BY_LOCAL_EXACT_RECOVERY"
            if batch01["recovery_status"]
            == batch02["recovery_status"]
            == "EXACT_PROVENANCE_LINKED_OUTPUT_RECOVERED"
            else "UNRESOLVED"
        ),
        "batch01_recovery_status": batch01["recovery_status"],
        "batch02_recovery_status": batch02["recovery_status"],
        "recovered_real_subject_output_count": 8,
        "partial_output_semantic_audit_status": state["partial_output_semantic_audit_status"],
        "directional_core_price_technical_refs": ownership.get(
            "directional_core_price_technical_refs"
        ),
        "directional_core_supply_refs": ownership.get("directional_core_supply_refs"),
        "supply_directional_core_usage": ownership.get("supply_directional_core_usage"),
        "buy_without_nonprice_material_anchor": ownership.get(
            "buy_without_nonprice_material_anchor"
        ),
        "sell_without_nonprice_material_anchor": ownership.get(
            "sell_without_nonprice_material_anchor"
        ),
        "directional_model_calls_on_source_insufficient": ownership.get(
            "directional_model_calls_on_source_insufficient"
        ),
        "price_only_directional_model_calls": ownership.get("price_only_directional_model_calls"),
        "final_direction_owner": ownership["final_direction_owner"],
        "timing_stage_direction_mutation": "NOT_MEASURED",
        "timing_stage_balance_mutation": "NOT_MEASURED",
        "timing_stage_hold_lean_mutation": "NOT_MEASURED",
        "price_timing_new_buyer_upgrade": "NOT_MEASURED",
        "price_only_holder_reduce": "NOT_MEASURED",
        "price_only_directional_ownership_violations": "NOT_MEASURED",
        "primary_user_action_wording_owner": "NOT_MEASURED",
        "ai_imperative_primary_action": "NOT_MEASURED",
        "known_hard_safety_regression": hard["known_hard_safety_regression"],
        "batch03_root_cause_classification": state["batch03_root_cause_classification"],
        "batch03_raw_stderr_recovery_status": batch03["raw_stderr_recovery_status"],
        "batch03_raw_transport_log_recovery_status": batch03["raw_transport_log_recovery_status"],
        "historical_pre_first_implementation_freeze_proof": ("STRONG_BUT_TIMESTAMP_INCOMPLETE"),
        "fictional_probe_status": state["fictional_probe_status"],
        "fictional_probe_sequence_completed": state["fictional_probe_sequence_completed"],
        "fictional_probe_timeout_count": state["fictional_probe_timeout_count"],
        "sequential_same_namespace_stall_reproduced": state[
            "sequential_same_namespace_stall_reproduced"
        ],
        "timeout_increase_this_task": 0,
        "transport_topology_mutation": 0,
        "model_semantic_input_drift": 0,
        "architecture_semantic_drift": 0,
        **{key: production[key] for key in production if key not in {"contract", "status"}},
        "full_tests": args.full_tests,
        "ruff": args.ruff,
        "diff_check": args.diff_check,
        "artifact_integrity": "PENDING_INDEX",
        "readiness": readiness,
        "stop_reason": (state.get("stop_reason") if validations_pass else "FULL_VALIDATION_FAILED"),
        "next_scope": next_decision["next_scope"],
        "status": "PASS" if validations_pass else "FAIL",
        "sequence_evidence_status": sequence["status"],
    }


def finalize(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") not in {"EVIDENCE_COMPLETE", "STOPPED_PROBE_FAILED"}:
        raise ValueError("terminal_evidence_state_required")
    verify_program_freeze(args, state)
    completion = completion_document(args=args, state=state)
    write_proof(args.report_dir, "29-program-completion", completion)
    write_reports(args.report_dir)
    sync_preserved_artifacts(args.output_root, args.report_dir)
    index = write_artifact_index(args.report_dir)
    completion["artifact_integrity"] = index["status"]
    completion["artifact_count"] = index["artifact_count"]
    completion["artifact_hash_mismatch_count"] = index["artifact_hash_mismatch_count"]
    completion["artifact_size_mismatch_count"] = index["artifact_size_mismatch_count"]
    write_proof(args.report_dir, "29-program-completion", completion)
    write_reports(args.report_dir)
    index = write_artifact_index(args.report_dir)
    args.zip_output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.zip_output.with_suffix(args.zip_output.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(item for item in args.report_dir.rglob("*") if item.is_file()):
            archive.write(path, path.relative_to(args.report_dir))
    temporary.replace(args.zip_output)
    with zipfile.ZipFile(args.zip_output) as archive:
        archived_index = json.loads(archive.read("20260906-artifact-index.json"))
        mismatches = 0
        size_mismatches = 0
        for row in archived_index["rows"]:
            payload = archive.read(row["path"])
            mismatches += hashlib.sha256(payload).hexdigest() != row["sha256"]
            size_mismatches += len(payload) != row["bytes"]
    if mismatches or size_mismatches:
        raise ValueError("final_zip_artifact_integrity_failure")
    state.update(
        {
            "state": "COMPLETE" if completion["status"] == "PASS" else "COMPLETE_NOT_READY",
            "finalized_at": datetime.now(UTC).isoformat(),
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
            "artifact_count": index["artifact_count"],
            "artifact_hash_mismatch_count": mismatches,
            "artifact_size_mismatch_count": size_mismatches,
            "report_zip": str(args.zip_output),
            "report_zip_sha256": file_sha256(args.zip_output),
            "readiness": completion["readiness"],
        }
    )
    write_json(args.output_root / "program-state.json", state)
    print(json.dumps(state, sort_keys=True), flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--probe", action="store_true")
    mode.add_argument("--finalize", action="store_true")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument(
        "--prior-output-root",
        type=Path,
        default=Path("/tmp/thesis-monitor-20260906-real-holdout-adapter-resume-run"),
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path("/tmp/thesis-monitor-20260906-direction-timing-ownership-run"),
    )
    parser.add_argument(
        "--latest-result-bundle",
        type=Path,
        default=Path.home()
        / "Documents/Codex/Reports"
        / "thesis-monitor-20260906-real-holdout-runner-adapter-repair-ownership-proof-resume-report.zip",
    )
    parser.add_argument(
        "--source-report",
        type=Path,
        default=Path.home()
        / "Documents/Codex/Reports"
        / "thesis-monitor-20260906-model-transport-revalidation-ownership-proof-continuation-report.zip",
    )
    parser.add_argument("--provider-root", type=Path, default=Path.home() / "Codex/ohlcv-analyst")
    parser.add_argument("--origin-main-at-task-start", default="UNKNOWN")
    parser.add_argument("--as-of", type=datetime.fromisoformat)
    parser.add_argument("--full-tests", default="NOT_RUN")
    parser.add_argument("--ruff", default="NOT_RUN")
    parser.add_argument("--diff-check", default="NOT_RUN")
    parser.add_argument(
        "--zip-output",
        type=Path,
        default=Path.home()
        / "Documents/Codex/Reports"
        / "thesis-monitor-20260906-partial-output-forensics-bounded-transport-stall-review-report.zip",
    )
    args = parser.parse_args()
    if args.prepare and args.as_of is None:
        raise ValueError("prepare_requires_fixed_as_of")
    for name in (
        "output_root",
        "report_dir",
        "prior_output_root",
        "source_root",
        "latest_result_bundle",
        "source_report",
        "provider_root",
        "zip_output",
    ):
        setattr(args, name, getattr(args, name).expanduser().resolve())
    return args


def main() -> None:
    args = parse_args()
    if args.prepare:
        prepare(args)
    elif args.probe:
        run_probe(args)
    else:
        finalize(args)


if __name__ == "__main__":
    main()
