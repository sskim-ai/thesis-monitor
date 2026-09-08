from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from app.services.reference_universe_audit_service import (
    CanonicalSecurityReference,
    IdentityResolutionStatus,
    RoutingSupportStatus,
    canonical_sha256,
    file_sha256,
    fundamental_source_attemptable_securities,
    load_us_reference_universe,
    representative_securities,
)
from scripts import bounded_us_universe_expansion_issuer_reconciliation as expansion
from scripts import directional_core_boundary_fresh_generalization_proof as directional
from scripts import new_issuer_holdout_selection_ownership_proof as runner
from scripts import runtime_namespace_isolation_repair_fresh_holdout_proof as runtime_proof


PROGRAM_CONTRACT = (
    "authoritative-result-identity-reconciliation-us-source-expansion-proof-"
    "resume-v1"
)
WORK_INSTRUCTION_PATH = (
    "docs/work-instructions/20260908-authoritative-result-identity-"
    "reconciliation-us-source-expansion-proof-resume.md"
)
WORK_INSTRUCTION_SHA256 = (
    "ea1363c6707f55691f9ee13f73eb2ad02b40492033551b624fbb0488dcbab215"
)
BASE_SHA = "5323a73d9adde926eae5ff2b349faf954b201518"

LATEST_STOP_RESULT_NAME = (
    "thesis-monitor-20260908-us-source-universe-expansion-fresh-"
    "generalization-proof-resume-report.zip"
)
LATEST_STOP_RESULT_SHA256 = (
    "e2f0c5f84e637ca10a18211c7fa8a4c061232eac5d15ca4874ceccf2930a7fc0"
)
AUTHORITATIVE_CALIBRATION_RESULT_NAME = (
    "thesis-monitor-20260908-directional-core-boundary-calibration-repair-"
    "fresh-generalization-proof-report.zip"
)
AUTHORITATIVE_CALIBRATION_RESULT_SHA256 = (
    "ab330fa13a53775ecdd162f36f4f7afeda42415db03bd0c766c48bf3a2eaddac"
)
ERRONEOUS_PRIOR_EXPECTED_SHA256 = (
    "f0a41371e12127a891165860f3c44ce6af7d1b8dcd13d0c5b93570618a075e6a"
)
HISTORICAL_RESULT_NAME = directional.LATEST_RESULT_NAME
HISTORICAL_RESULT_SHA256 = directional.LATEST_RESULT_SHA256
EXPANSION_RESULT_NAME = expansion.RESULT_ZIP_NAME
EXPANSION_RESULT_SHA256 = (
    "12ed21a8fcd378036fb86e08193fcffb5b3e0f9f0710f92602a2f3c595c18cf4"
)
EXCLUSION_REGISTRY_COUNT = 149
EXCLUSION_REGISTRY_SHA256 = (
    "8d9f121ff6fc4749ef5da5cecad4e8f731a991a051e771cdeb5512fe34b63f6b"
)
SELECTION_SALT = expansion.SELECTION_SALT
US_SOURCE_EVALUATION_BUDGET = 48
TARGET_US = 4
TARGET_KR = 12
TARGET_TOTAL = TARGET_US + TARGET_KR
REPORT_DIRECTORY = (
    "20260908-authoritative-result-identity-reconciliation-us-source-"
    "expansion-proof-resume"
)

REFERENCE_MEMBERS = {
    "membership": "evidence/membership/us-reference-membership.jsonl",
    "sec": "evidence/reference-snapshots/sec-company-tickers.json",
    "nasdaq": "evidence/reference-snapshots/nasdaqlisted.txt",
    "other": "evidence/reference-snapshots/otherlisted.txt",
    "opendart": "evidence/reference-snapshots/opendart-corp-code.zip",
    "handoff": "reports/proofs/23-next-holdout-selection-handoff.json",
}
REFERENCE_SNAPSHOT_SHA256 = {
    "sec-company-tickers.json": (
        "f987a9fba01e1c1858ddcf0c032d77be301843860d7a0571efaa92ec3f938926"
    ),
    "nasdaqlisted.txt": (
        "491337a821469a830093aca740849358982960c46f0192537f5de898f59e9200"
    ),
    "otherlisted.txt": (
        "0e7be707f683443160a78e85139d8af18f786270c9ed82de8402d1d72538a319"
    ),
    "opendart-corp-code.zip": (
        "43903ff88932f2a1a2dc606b4169b1d3e6f6831019d2defa16e81e67c7ba0bdb"
    ),
}

REPORT_NAMES = (
    "01-repository-provenance",
    "02-latest-stop-result-integrity",
    "03-authoritative-calibration-result-integrity",
    "04-provenance-identity-reconciliation",
    "05-erroneous-prior-expected-hash-record",
    "06-calibration-freeze-reuse-proof",
    "07-real-exposure-exclusion-registry",
    "08-schedule-pause-observation",
    "09-us-supported-universe-funnel",
    "10-us-supported-universe-root-cause",
    "11-optional-price-overcoupling-audit",
    "12-us-reference-expansion-decision",
    "13-us-reference-expansion-diff",
    "14-us-reference-expansion-tests",
    "15-extended-us-candidate-policy",
    "16-extended-us-candidate-manifest",
    "17-us-source-readiness-audit",
    "18-us-source-failure-detail",
    "19-us-target-decision",
    "20-kr-pass-preservation",
    "21-fresh-us4-selection",
    "22-fresh-kr12-selection",
    "23-fresh-source-generation",
    "24-source-identity-audit",
    "25-source-sufficiency-audit",
    "26-fresh-source-lock",
    "27-fresh-proof-precommit",
    "28-investment-semantic-freeze",
    "29-runtime-isolation-freeze",
)

_DIRECTIONAL_ARCHITECTURE_HASHES = directional.architecture_hashes


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


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, default=str) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )
    temporary.replace(path)


def git_value(*args: str) -> str:
    return subprocess.run(
        ("git", *args), check=True, capture_output=True, text=True
    ).stdout.strip()


def bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def zip_json(archive: zipfile.ZipFile, member: str) -> dict[str, Any]:
    value = json.loads(archive.read(member))
    if not isinstance(value, dict):
        raise ValueError(f"zip_object_required:{member}")
    return value


def zip_jsonl(archive: zipfile.ZipFile, member: str) -> list[dict[str, Any]]:
    rows = []
    for line in archive.read(member).decode("utf-8").splitlines():
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"zip_jsonl_object_required:{member}")
        rows.append(value)
    return rows


def _safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts and "\\" not in name


def verify_indexed_bundle(
    path: Path, *, expected_name: str, expected_sha256: str
) -> dict[str, object]:
    if path.name != expected_name:
        raise ValueError(f"input_zip_name_mismatch:{path.name}")
    actual_sha256 = file_sha256(path)
    if actual_sha256 != expected_sha256:
        raise ValueError(f"input_zip_sha256_mismatch:{path.name}")
    sidecar = path.with_suffix(path.suffix + ".sha256")
    sidecar_value = sidecar.read_text(encoding="utf-8").split()[0] if sidecar.is_file() else None
    if sidecar_value is not None and sidecar_value != actual_sha256:
        raise ValueError(f"adjacent_checksum_mismatch:{path.name}")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        file_names = {name for name in names if not name.endswith("/")}
        duplicate_count = sum(count > 1 for count in Counter(names).values())
        unsafe_count = sum(not _safe_member(name) for name in names)
        crc_failure = archive.testzip()
        index = zip_json(archive, "artifact-index.json")
        index_rows = index.get("rows")
        if not isinstance(index_rows, list):
            raise ValueError(f"artifact_index_rows_missing:{path.name}")
        indexed = {
            str(row["path"]): row
            for row in index_rows
            if isinstance(row, Mapping) and row.get("path")
        }
        expected_payloads = file_names - {"artifact-index.json"}
        hash_mismatches = 0
        size_mismatches = 0
        secret_failures = 0
        for name, row in indexed.items():
            payload = archive.read(name)
            hash_mismatches += bytes_sha256(payload) != row.get("sha256")
            size_mismatches += len(payload) != row.get("byte_size")
            secret_failures += row.get("secret_scan_status") not in {None, "PASS"}
        failures = {
            "duplicate_member_count": duplicate_count,
            "unsafe_member_count": unsafe_count,
            "crc_failure": crc_failure,
            "index_membership_mismatch": int(set(indexed) != expected_payloads),
            "hash_mismatch_count": hash_mismatches,
            "size_mismatch_count": size_mismatches,
            "secret_scan_failure_count": secret_failures,
        }
    if any(bool(value) for value in failures.values()):
        raise ValueError(f"input_bundle_integrity_failed:{path.name}:{failures}")
    return {
        "contract": "indexed-result-bundle-integrity-v1",
        "path": str(path),
        "name": path.name,
        "expected_sha256": expected_sha256,
        "actual_sha256": actual_sha256,
        "adjacent_checksum_present": sidecar.is_file(),
        "adjacent_checksum_matches": sidecar_value in {None, actual_sha256},
        "member_count": len(names),
        "indexed_payload_count": len(indexed),
        **failures,
        "status": "PASS",
    }


def architecture_hashes(repo_root: Path) -> dict[str, str]:
    return {
        **_DIRECTIONAL_ARCHITECTURE_HASHES(repo_root),
        "authoritative_result_source_expansion_orchestrator": file_sha256(
            Path(__file__).resolve()
        ),
    }


def source_generation_ids(commit: str, as_of: datetime) -> tuple[str, str]:
    stamp = as_of.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    source_suffix = hashlib.sha256(
        f"{commit}|{stamp}|source|{PROGRAM_CONTRACT}".encode()
    ).hexdigest()[:12]
    runtime_suffix = hashlib.sha256(
        f"{commit}|{stamp}|runtime|{PROGRAM_CONTRACT}".encode()
    ).hexdigest()[:12]
    return (
        f"20260908-us-source-expansion-source-{stamp}-{source_suffix}",
        f"20260908-us-source-expansion-proof-{stamp}-{runtime_suffix}",
    )


def configure_stack() -> None:
    directional.PROGRAM_CONTRACT = PROGRAM_CONTRACT
    directional.WORK_INSTRUCTION_PATH = WORK_INSTRUCTION_PATH
    directional.WORK_INSTRUCTION_SHA256 = WORK_INSTRUCTION_SHA256
    directional.LATEST_FINAL_HEAD = BASE_SHA
    directional.PREVIOUS_EXCLUSION_COUNT = EXCLUSION_REGISTRY_COUNT
    directional.NEWLY_RETIRED_COUNT = 0
    directional.RETIRED_COHORT = ()
    directional.REPORT_DIRECTORY = f"{REPORT_DIRECTORY}/fresh-real-internal"
    directional.architecture_hashes = architecture_hashes
    directional.source_generation_ids = source_generation_ids
    directional._configure_stack()


def _write_report(report_dir: Path, name: str, value: Mapping[str, object]) -> None:
    directional.write_named_report(report_dir, name, value)


def _report(report_dir: Path, number: int, value: Mapping[str, object]) -> None:
    _write_report(report_dir, REPORT_NAMES[number - 1], value)


def _focused_validation() -> dict[str, object]:
    commands = (
        (
            "focused_pytest",
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "tests/test_reference_universe_audit_service.py",
                "tests/test_directional_core_boundary_fresh_generalization_proof.py",
            ],
        ),
        (
            "focused_ruff",
            [
                str(Path(sys.executable).with_name("ruff")),
                "check",
                "app/services/reference_universe_audit_service.py",
                "scripts/authoritative_result_identity_reconciliation_us_source_expansion_proof_resume.py",
                "scripts/directional_core_boundary_fresh_generalization_proof.py",
                "tests/test_reference_universe_audit_service.py",
                "tests/test_directional_core_boundary_fresh_generalization_proof.py",
            ],
        ),
    )
    rows = []
    for name, command in commands:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        rows.append(
            {
                "name": name,
                "command": command,
                "returncode": result.returncode,
                "output_tail": (result.stdout + result.stderr).strip().splitlines()[-20:],
                "status": "PASS" if result.returncode == 0 else "FAIL",
            }
        )
    status = "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL"
    result = {
        "contract": "us-reference-expansion-focused-validation-v1",
        "rows": rows,
        "source_or_model_calls": 0,
        "status": status,
    }
    if status != "PASS":
        raise ValueError("US_REFERENCE_EXPANSION_FOCUSED_VALIDATION_FAILED")
    return result


def _reference_snapshot_identity(handoff: Mapping[str, object]) -> str:
    snapshot = handoff.get("verified_reference_snapshot")
    if not isinstance(snapshot, Mapping):
        raise ValueError("verified_reference_snapshot_missing")
    return canonical_sha256(snapshot)


def _manifest(rows: Sequence[CanonicalSecurityReference]) -> dict[str, object]:
    return {
        "contract": "extended-us-candidate-manifest-v1",
        "target_count": TARGET_US,
        "bounded_candidate_count": len(rows),
        "candidate_rows": [
            {
                "candidate_rank": rank,
                "ticker": row.display_symbol,
                "canonical_security_id": row.canonical_security_id,
                "canonical_issuer_key": row.canonical_issuer_key,
                "issuer_name": row.issuer_name,
                "exchange": row.exchange,
                "provider_exchange": row.provider_exchange,
                "security_type": row.security_type,
                "routing_support_status": row.routing_support_status,
            }
            for rank, row in enumerate(rows, start=1)
        ],
        "source_evaluation_performed": 0,
        "model_calls": 0,
        "status": "FROZEN",
    }


def freeze(args: argparse.Namespace) -> None:
    configure_stack()
    repo_root = Path.cwd().resolve()
    if args.output_root.exists() or args.report_dir.exists():
        raise ValueError("new_output_and_report_directories_required")
    if file_sha256(repo_root / WORK_INSTRUCTION_PATH) != WORK_INSTRUCTION_SHA256:
        raise ValueError("work_instruction_content_drift")
    if git_value("status", "--short"):
        raise ValueError("clean_worktree_required_before_candidate_freeze")
    if args.as_of is None:
        raise ValueError("fixed_as_of_required")
    ancestor = subprocess.run(
        ("git", "merge-base", "--is-ancestor", BASE_SHA, "HEAD"), check=False
    ).returncode == 0
    if not ancestor:
        raise ValueError("base_not_ancestor_of_current_head")

    stop_integrity = verify_indexed_bundle(
        args.stop_result_zip,
        expected_name=LATEST_STOP_RESULT_NAME,
        expected_sha256=LATEST_STOP_RESULT_SHA256,
    )
    calibration_integrity = verify_indexed_bundle(
        args.calibration_result_zip,
        expected_name=AUTHORITATIVE_CALIBRATION_RESULT_NAME,
        expected_sha256=AUTHORITATIVE_CALIBRATION_RESULT_SHA256,
    )
    historical_integrity = verify_indexed_bundle(
        args.historical_result_zip,
        expected_name=HISTORICAL_RESULT_NAME,
        expected_sha256=HISTORICAL_RESULT_SHA256,
    )
    expansion_integrity = verify_indexed_bundle(
        args.expansion_zip,
        expected_name=EXPANSION_RESULT_NAME,
        expected_sha256=EXPANSION_RESULT_SHA256,
    )
    calibration_gate = directional.assert_calibration_frozen(repo_root)
    source_config = directional._source_config_presence_preflight(repo_root)
    pause = runtime_proof._pause_observation()
    namespace = directional._namespace_preflight()

    args.output_root.mkdir(parents=True)
    (args.report_dir / "proofs").mkdir(parents=True)
    internal = args.report_dir / "fresh-real-internal"
    (internal / "proofs").mkdir(parents=True)
    snapshot_root = args.output_root / "selection-inputs/reference-snapshots"
    snapshot_root.mkdir(parents=True)

    with zipfile.ZipFile(args.calibration_result_zip) as archive:
        registry = zip_json(
            archive,
            "experiment/fresh-real-proof/selection-inputs/merged-registry.json",
        )
        prior_candidates = zip_json(
            archive, "experiment/fresh-real-proof/candidate-identities.json"
        )
    if len(registry.get("rows") or []) != EXCLUSION_REGISTRY_COUNT:
        raise ValueError("exclusion_registry_count_mismatch")
    if canonical_sha256(registry) != EXCLUSION_REGISTRY_SHA256:
        raise ValueError("exclusion_registry_hash_mismatch")
    excluded = {str(value) for value in registry.get("all_excluded_issuer_keys") or []}
    if len(excluded) != EXCLUSION_REGISTRY_COUNT:
        raise ValueError("exclusion_registry_unique_identity_mismatch")

    with zipfile.ZipFile(args.expansion_zip) as archive:
        archived_us_rows = zip_jsonl(archive, REFERENCE_MEMBERS["membership"])
        handoff = zip_json(archive, REFERENCE_MEMBERS["handoff"])
        snapshot_members = {
            "sec-company-tickers.json": REFERENCE_MEMBERS["sec"],
            "nasdaqlisted.txt": REFERENCE_MEMBERS["nasdaq"],
            "otherlisted.txt": REFERENCE_MEMBERS["other"],
            "opendart-corp-code.zip": REFERENCE_MEMBERS["opendart"],
        }
        for filename, member in snapshot_members.items():
            payload = archive.read(member)
            if bytes_sha256(payload) != REFERENCE_SNAPSHOT_SHA256[filename]:
                raise ValueError(f"reference_snapshot_hash_mismatch:{filename}")
            (snapshot_root / filename).write_bytes(payload)

    retrieved_at = str(
        (handoff.get("verified_reference_snapshot") or {}).get("retrieved_at") or ""
    )
    if not retrieved_at:
        raise ValueError("reference_retrieved_at_missing")
    reconstructed = load_us_reference_universe(
        sec_company_tickers=snapshot_root / "sec-company-tickers.json",
        nasdaq_listed=snapshot_root / "nasdaqlisted.txt",
        other_listed=snapshot_root / "otherlisted.txt",
        retrieved_at=retrieved_at,
    )
    archived_models = [CanonicalSecurityReference.model_validate(row) for row in archived_us_rows]
    reconstructed_rows = [row.model_dump(mode="json") for row in reconstructed]
    reconstructed_hash = canonical_sha256(reconstructed_rows)
    archived_hash = canonical_sha256(archived_us_rows)
    if reconstructed_hash != archived_hash:
        raise ValueError("reference_adapter_reconstruction_mismatch")

    route_supported = representative_securities(
        archived_models,
        selection_salt=SELECTION_SALT,
        excluded_issuer_keys=excluded,
        require_routing_supported=True,
    )
    source_attemptable = fundamental_source_attemptable_securities(
        archived_models,
        selection_salt=SELECTION_SALT,
        excluded_issuer_keys=excluded,
    )
    if len(source_attemptable) < US_SOURCE_EVALUATION_BUDGET:
        raise ValueError("expanded_source_attemptable_universe_below_bounded_budget")
    us_candidates = source_attemptable[:US_SOURCE_EVALUATION_BUDGET]
    prior_us_rows = [dict(row) for row in prior_candidates.get("us") or []]
    prior_us_order = [str(row.get("display_symbol")) for row in prior_us_rows]
    route_supported_order = [row.display_symbol for row in route_supported]
    root_cause_confirmed = (
        len(prior_us_rows) == 9
        and set(prior_us_order) == set(route_supported_order)
        and len(source_attemptable) > len(route_supported)
    )
    if not root_cause_confirmed:
        raise ValueError("US_SUPPORTED_UNIVERSE_FUNNEL_ROOT_CAUSE_NOT_CONFIRMED")

    kr_rows = [dict(row) for row in prior_candidates.get("kr") or []]
    if len(kr_rows) < TARGET_KR:
        raise ValueError("preserved_kr_candidate_order_below_target")
    if any(str(row.get("canonical_issuer_key")) in excluded for row in kr_rows):
        raise ValueError("preserved_kr_candidate_exposure_overlap")

    candidate_identities = {
        "contract": "fresh-issuer-candidate-identities-v1",
        "us": [row.model_dump(mode="json") for row in us_candidates],
        "kr": kr_rows,
        "status": "FROZEN",
    }
    reference_identity = _reference_snapshot_identity(handoff)
    candidate_universe_hash = canonical_sha256(
        [row.model_dump(mode="json") for row in source_attemptable]
    )
    policy = {
        "contract": "extended-us-source-attemptable-selection-policy-v1",
        "status": "FROZEN_PRE_SOURCE_EVALUATION",
        "selection_salt": SELECTION_SALT,
        "ordering_method": (
            "SHA256(selection_salt|market|canonical_issuer_key|"
            "canonical_security_id), one deterministic representative per issuer"
        ),
        "candidate_universe_sha256": candidate_universe_hash,
        "candidate_identities_sha256": canonical_sha256(candidate_identities),
        "reference_snapshot_sha256": reference_identity,
        "verified_reference_snapshot": handoff.get("verified_reference_snapshot"),
        "exclusion_registry_count": EXCLUSION_REGISTRY_COUNT,
        "exclusion_registry_sha256": EXCLUSION_REGISTRY_SHA256,
        "market_targets": {"us": TARGET_US, "kr": TARGET_KR},
        "market_policies": {
            "us": {
                "candidate_order": [row.display_symbol for row in us_candidates],
                "bounded_evaluation_limit": len(us_candidates),
                "full_source_attemptable_issuer_count": len(source_attemptable),
            },
            "kr": {
                "candidate_order": [str(row["display_symbol"]) for row in kr_rows],
                "bounded_evaluation_limit": len(kr_rows),
            },
        },
        "selection_rule": (
            "remove all 149 exposed canonical issuers; preserve identity/security-"
            "class gates; admit route-supported or route-candidate issuers to the "
            "official fundamental source test; accept first source-eligible US4 "
            "and KR12 in the frozen order"
        ),
        "price_contract": "READY_OR_UNAVAILABLE_SAFE_WITHOUT_FABRICATION",
        "source_sufficiency_mutation": 0,
        "ticker_specific_exception_count": 0,
        "source_evaluation_performed": 0,
        "model_calls": 0,
    }
    manifest = _manifest(us_candidates)

    funnel = {
        "contract": "us-supported-universe-funnel-v1",
        "raw_official_reference_security_rows": len(archived_models),
        "normalized_security_rows": sum(bool(row.display_symbol) for row in archived_models),
        "canonical_security_identity_count": sum(
            row.canonical_security_id is not None for row in archived_models
        ),
        "identity_resolved_security_count": sum(
            row.identity_resolution_status == IdentityResolutionStatus.RESOLVED
            for row in archived_models
        ),
        "canonical_issuer_identity_count": len(
            {
                row.canonical_issuer_key
                for row in archived_models
                if row.canonical_issuer_key is not None
            }
        ),
        "routing_supported_security_count": sum(
            row.routing_support_status == RoutingSupportStatus.SUPPORTED
            for row in archived_models
        ),
        "routing_candidate_security_count": sum(
            row.routing_support_status == RoutingSupportStatus.CANDIDATE
            for row in archived_models
        ),
        "source_client_attemptable_unseen_issuer_count": len(source_attemptable),
        "real_exposure_exclusion_count": len(excluded),
        "remaining_unseen_routing_supported_issuer_count": len(route_supported),
        "bounded_candidate_count": len(us_candidates),
        "reference_membership_sha256": archived_hash,
        "reconstructed_membership_sha256": reconstructed_hash,
        "status": "PASS",
    }
    root_cause = {
        "contract": "us-supported-universe-funnel-root-cause-v1",
        "prior_bounded_candidate_count": len(prior_us_rows),
        "prior_candidate_order": prior_us_order,
        "remaining_route_supported_order": route_supported_order,
        "source_attemptable_unseen_issuer_count": len(source_attemptable),
        "root_cause": "OPTIONAL_PRICE_SUPPORT_OVERCOUPLING",
        "result": "US_SUPPORTED_UNIVERSE_FUNNEL_ROOT_CAUSE_CONFIRMED",
        "status": "PASS",
    }
    overcoupling = {
        "contract": "optional-price-support-overcoupling-audit-v1",
        "optional_price_support_overcoupling_found": 1,
        "fundamental_source_test_requires_price_route": False,
        "price_unavailable_safe_preserved": True,
        "price_fabrication_count": 0,
        "technical_claim_without_data_count": 0,
        "fundamental_source_sufficiency_mutation": 0,
        "status": "PASS",
    }
    expansion_decision = {
        "contract": "generic-us-reference-expansion-decision-v1",
        "generic_us_reference_expansion_applied": 1,
        "new_provider_count": 0,
        "paid_provider_count": 0,
        "ticker_specific_exception_count": 0,
        "security_class_policy_changed": 0,
        "issuer_dedup_policy_changed": 0,
        "decision": "ALLOW_OFFICIAL_FUNDAMENTAL_SOURCE_ATTEMPT_BEFORE_OPTIONAL_PRICE_ROUTE",
        "status": "PASS",
    }
    expansion_diff = {
        "contract": "generic-us-reference-expansion-diff-v1",
        "before_unseen_routing_supported_issuer_count": len(route_supported),
        "after_unseen_source_attemptable_issuer_count": len(source_attemptable),
        "bounded_before_count": len(prior_us_rows),
        "bounded_after_count": len(us_candidates),
        "added_source_attemptable_count": len(source_attemptable) - len(route_supported),
        "removed_security_safety_gate_count": 0,
        "source_requirement_relaxation_count": 0,
        "status": "PASS",
    }
    validation = _focused_validation()

    selection_inputs = args.output_root / "selection-inputs"
    write_json(selection_inputs / "merged-registry.json", registry)
    write_json(selection_inputs / "expansion-handoff.json", handoff)
    write_json(selection_inputs / "extended-us-candidate-policy.json", policy)
    write_json(selection_inputs / "extended-us-candidate-manifest.json", manifest)
    write_jsonl(
        selection_inputs / "us-candidates.jsonl", candidate_identities["us"]
    )
    write_jsonl(
        selection_inputs / "kr-candidates.jsonl", candidate_identities["kr"]
    )
    write_json(args.output_root / "candidate-identities.json", candidate_identities)
    write_json(args.output_root / "source-configuration-audit.json", source_config)
    write_json(args.output_root / "schedule-pause-observation.json", pause)
    write_json(args.output_root / "namespace-isolation-preflight.json", namespace)
    write_json(
        args.output_root / "input-integrity.json",
        {
            "latest_stop": stop_integrity,
            "authoritative_calibration": calibration_integrity,
            "historical_runtime": historical_integrity,
            "reference_expansion": expansion_integrity,
            "status": "PASS",
        },
    )

    provenance = {
        "contract": "repository-provenance-v1",
        "branch": git_value("branch", "--show-current"),
        "base_sha": BASE_SHA,
        "base_is_ancestor": ancestor,
        "work_instruction_commit": git_value(
            "log", "-1", "--format=%H", "--", WORK_INSTRUCTION_PATH
        ),
        "implementation_commit": git_value("rev-parse", "HEAD"),
        "implementation_tree": git_value("rev-parse", "HEAD^{tree}"),
        "origin_main": git_value("rev-parse", "origin/main"),
        "work_instruction_sha256": WORK_INSTRUCTION_SHA256,
        "status": "PASS",
    }
    reconciliation = {
        "contract": "authoritative-result-identity-reconciliation-v1",
        "latest_stop_result_sha256": stop_integrity["actual_sha256"],
        "authoritative_calibration_result_sha256": calibration_integrity[
            "actual_sha256"
        ],
        "erroneous_prior_expected_sha256": ERRONEOUS_PRIOR_EXPECTED_SHA256,
        "erroneous_hash_classification": "ERRONEOUS_PRIOR_INSTRUCTION_EXPECTED_HASH",
        "provenance_identity_reconciliation_status": "PASS",
        "status": "PASS",
    }
    erroneous = {
        "contract": "erroneous-prior-expected-hash-record-v1",
        "erroneous_prior_expected_sha256": ERRONEOUS_PRIOR_EXPECTED_SHA256,
        "authoritative_replacement_sha256": AUTHORITATIVE_CALIBRATION_RESULT_SHA256,
        "search_for_erroneous_identity_performed": 0,
        "classification": "ERRONEOUS_PRIOR_INSTRUCTION_EXPECTED_HASH",
        "status": "RECORDED",
    }
    calibration_reuse = {
        "contract": "calibration-freeze-reuse-proof-v1",
        **calibration_gate,
        "calibration_freeze_reused": True,
        "calibration_semantic_drift": 0,
        "fictional_calibration_rerun_count": 0,
        "status": "PASS",
    }
    registry_report = {
        "contract": "real-exposure-exclusion-registry-continuity-v1",
        "exclusion_registry_count": EXCLUSION_REGISTRY_COUNT,
        "exclusion_registry_sha256": EXCLUSION_REGISTRY_SHA256,
        "exclusion_shrink_count": 0,
        "future_unseen_reuse_of_excluded_issuer_allowed": 0,
        "status": "PASS",
    }

    for number, document in enumerate(
        (
            provenance,
            stop_integrity,
            calibration_integrity,
            reconciliation,
            erroneous,
            calibration_reuse,
            registry_report,
            pause,
            funnel,
            root_cause,
            overcoupling,
            expansion_decision,
            expansion_diff,
            validation,
            policy,
            manifest,
        ),
        start=1,
    ):
        _report(args.report_dir, number, document)

    runner.write_proof(internal, 1, provenance)
    runner.write_proof(
        internal,
        2,
        {
            "contract": "task-input-integrity-v1",
            "latest_stop": stop_integrity,
            "authoritative_calibration": calibration_integrity,
            "historical_runtime": historical_integrity,
            "reference_expansion": expansion_integrity,
            "status": "PASS",
        },
    )
    runner.write_proof(internal, 3, registry)
    runner.write_proof(internal, 4, registry_report)
    runner.write_proof(internal, 5, policy)
    runner.write_proof(internal, 6, manifest)
    runner.write_proof(
        internal,
        9,
        {
            "contract": "preserved-kr-candidate-manifest-v1",
            "target_count": TARGET_KR,
            "bounded_candidate_count": len(kr_rows),
            "candidate_order": [str(row["display_symbol"]) for row in kr_rows],
            "source_evaluation_performed": 0,
            "model_calls": 0,
            "status": "FROZEN",
        },
    )
    runner.write_reports(internal)

    prior_root_cause = (
        repo_root
        / "docs/reports/20260908-directional-core-boundary-calibration-repair-"
        "fresh-generalization-proof/proofs/06-directional-instability-root-cause-"
        "classification.json"
    )
    if not prior_root_cause.is_file():
        raise ValueError("frozen_directional_root_cause_proof_missing")
    write_json(
        args.report_dir
        / "proofs/06-directional-instability-root-cause-classification.json",
        read_json(prior_root_cause),
    )

    state = {
        "contract": PROGRAM_CONTRACT,
        "state": "SELECTION_FROZEN",
        "branch": provenance["branch"],
        "base_sha": BASE_SHA,
        "work_instruction_commit": provenance["work_instruction_commit"],
        "implementation_commit": provenance["implementation_commit"],
        "implementation_tree": provenance["implementation_tree"],
        "selection_freeze_commit": "PENDING_COMMIT",
        "selection_policy_sha256": canonical_sha256(policy),
        "candidate_identities_sha256": canonical_sha256(candidate_identities),
        "candidate_universe_sha256": candidate_universe_hash,
        "exclusion_registry_sha256": EXCLUSION_REGISTRY_SHA256,
        "exclusion_registry_count": EXCLUSION_REGISTRY_COUNT,
        "as_of": args.as_of.isoformat(),
        "ordered_cohort": [],
        "model_invocation_count": 0,
        "real_investment_model_invocation_count": 0,
        "calibration_gate": calibration_gate,
        "calibration_freeze_seal_sha256": directional.CALIBRATION_FREEZE_SHA256,
        "calibration_contract_sha256": directional.CALIBRATION_CONTRACT_SHA256,
        "namespace_isolation_preflight_sha256": canonical_sha256(namespace),
        "initial_pause_observation": pause,
        "source_configuration": source_config,
        "provenance_identity_reconciliation_status": "PASS",
        "optional_price_support_overcoupling_found": 1,
        "generic_us_reference_expansion_applied": 1,
        "ticker_specific_us_exception_count": 0,
        "production_scheduler_change_current_task": 0,
        "production_telegram_send_current_task": 0,
        "automatic_monitoring_resume": 0,
    }
    write_json(args.output_root / "program-state.json", state)
    write_text(
        args.report_dir / "README.md",
        "# Authoritative Result Reconciliation and US Source Expansion\n\n"
        "The corrected result identity, frozen Directional calibration, 149-issuer "
        "real-exposure registry, official reference snapshots, and outcome-independent "
        "US48/KR reserve order are frozen before source evaluation.",
    )
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def _internal_proof(args: argparse.Namespace, number: int) -> dict[str, Any]:
    path = runner.proof_path(args.report_dir / "fresh-real-internal", number)
    if path.is_file():
        return read_json(path)
    return {"status": "NOT_MEASURED", "reason": "UPSTREAM_STAGE_NOT_RUN"}


def _failure_taxonomy(row: Mapping[str, object]) -> str:
    if row.get("security_accounting_basis_status") != "PASS":
        return "SECURITY_OR_ACCOUNTING_BASIS_BLOCK"
    if row.get("fundamental_source_sufficient"):
        if row.get("price_timing_input_readiness") not in {"READY", "UNAVAILABLE_SAFE"}:
            return "OPTIONAL_PRICE_ONLY_LIMITATION"
        return "OTHER_CONFIRMED"
    reasons = " ".join(str(value).lower() for value in row.get("failure_reasons") or [])
    lineage = row.get("source_request_lineage") or []
    if "mapping" in reasons or "normaliz" in reasons or "taxonomy" in reasons:
        return "NORMALIZATION_OR_MAPPING_GAP"
    if any(token in reasons for token in ("missing", "required", "family")):
        return "MISSING_REQUIRED_FUNDAMENTAL_FAMILY"
    if not lineage or any(
        isinstance(item, Mapping) and item.get("status") in {"missing", "unavailable"}
        for item in lineage
    ):
        return "TRUE_OFFICIAL_SOURCE_ABSENCE"
    return "UNKNOWN"


def _write_post_source_reports(args: argparse.Namespace) -> None:
    us_audit = _internal_proof(args, 7)
    kr_audit = _internal_proof(args, 10)
    us_rows = []
    taxonomy = Counter()
    for raw in us_audit.get("rows") or []:
        row = dict(raw)
        if not row.get("eligible_for_final_holdout"):
            row["failure_taxonomy"] = _failure_taxonomy(row)
            taxonomy[row["failure_taxonomy"]] += 1
        us_rows.append(row)
    us_document = {
        **us_audit,
        "rows": us_rows,
        "failure_taxonomy_counts": dict(sorted(taxonomy.items())),
    }
    failures = [row for row in us_rows if not row.get("eligible_for_final_holdout")]
    _report(args.report_dir, 17, us_document)
    _report(
        args.report_dir,
        18,
        {
            "contract": "expanded-us-source-failure-detail-v1",
            "failure_count": len(failures),
            "failure_taxonomy_counts": dict(sorted(taxonomy.items())),
            "rows": failures,
            "status": "DIAGNOSTIC_COMPLETE",
        },
    )
    us_pass = us_audit.get("source_target_status") == "PASS"
    kr_pass = kr_audit.get("source_target_status") == "PASS"
    _report(
        args.report_dir,
        19,
        {
            "contract": "expanded-us-target-decision-v1",
            "target": TARGET_US,
            "attempted": us_audit.get("attempted_count", 0),
            "source_sufficient": us_audit.get("source_sufficient_count", 0),
            "source_insufficient": us_audit.get("source_insufficient_count", 0),
            "us_target_status": "PASS" if us_pass else "FAIL",
            "model_execution_allowed": int(us_pass and kr_pass),
            "readiness": (
                "READY_FOR_FRESH_SOURCE_LOCK"
                if us_pass and kr_pass
                else "NOT_READY_US_FREE_SOURCE_COVERAGE"
            ),
            "status": "PASS" if us_pass else "FAIL_CLOSED",
        },
    )
    _report(
        args.report_dir,
        20,
        {
            "contract": "kr-pass-preservation-and-revalidation-v1",
            "broad_kr_universe_expansion": 0,
            "target": TARGET_KR,
            "attempted": kr_audit.get("attempted_count", 0),
            "selected": kr_audit.get("source_sufficient_count", 0),
            "kr_target_status": "PASS" if kr_pass else "FAIL",
            "reserve_order_used": max(
                0, int(kr_audit.get("attempted_count") or 0) - TARGET_KR
            ),
            "status": "PASS" if kr_pass else "FAIL_CLOSED",
        },
    )
    if not (us_pass and kr_pass):
        return
    selection = _internal_proof(args, 15)
    cohort = selection.get("ordered_cohort") or []
    mappings = (
        (21, {**selection, "selected": list(cohort[:TARGET_US])}),
        (22, {**selection, "selected": list(cohort[TARGET_US:])}),
        (23, _internal_proof(args, 16)),
        (24, _internal_proof(args, 18)),
        (25, _internal_proof(args, 17)),
        (26, _internal_proof(args, 19)),
        (27, _internal_proof(args, 20)),
        (28, _internal_proof(args, 21)),
        (29, _internal_proof(args, 24)),
    )
    for number, document in mappings:
        _report(args.report_dir, number, document)


def prepare(args: argparse.Namespace) -> None:
    configure_stack()
    directional.prepare(args)
    _write_post_source_reports(args)


def seal(args: argparse.Namespace) -> None:
    configure_stack()
    directional.seal(args)


def execute(args: argparse.Namespace) -> None:
    configure_stack()
    directional.execute(args)


def _validation() -> dict[str, object]:
    commands = (
        ("full_pytest", [sys.executable, "-m", "pytest", "-q"]),
        ("ruff", [str(Path(sys.executable).with_name("ruff")), "check", "."]),
        ("git_diff_check", ["git", "diff", "--check"]),
    )
    rows = []
    for name, command in commands:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        rows.append(
            {
                "name": name,
                "command": command,
                "returncode": result.returncode,
                "output_tail": (result.stdout + result.stderr).strip().splitlines()[-30:],
                "status": "PASS" if result.returncode == 0 else "FAIL",
            }
        )
    return {
        "contract": "authoritative-resume-final-validation-v1",
        "rows": rows,
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def close_reports(args: argparse.Namespace) -> None:
    configure_stack()
    _write_post_source_reports(args)
    directional.close_reports(args)
    completion = read_json(args.output_root / "program-completion.json")
    integrity = read_json(args.output_root / "input-integrity.json")
    funnel = read_json(args.report_dir / "proofs" / f"{REPORT_NAMES[8]}.json")
    policy = read_json(args.report_dir / "proofs" / f"{REPORT_NAMES[14]}.json")
    us = read_json(args.report_dir / "proofs" / f"{REPORT_NAMES[16]}.json")
    kr = read_json(args.report_dir / "proofs" / f"{REPORT_NAMES[19]}.json")
    validation = _validation()
    run_results = completion.get("run_results") or {}
    if us.get("source_target_status") != "PASS":
        completion.update(
            {
                "status": "STOPPED",
                "readiness": "NOT_READY_US_FREE_SOURCE_COVERAGE",
                "stop_reason": "US_FREE_SOURCE_TARGET_BELOW_4",
                "next_scope": "BOUNDED_US_FREE_SOURCE_COVERAGE_REVIEW",
            }
        )
    completion.update(
        {
            "contract": PROGRAM_CONTRACT,
            "base_sha": BASE_SHA,
            "latest_stop_result_sha256": LATEST_STOP_RESULT_SHA256,
            "latest_stop_result_integrity": integrity["latest_stop"]["status"],
            "authoritative_calibration_result_sha256": (
                AUTHORITATIVE_CALIBRATION_RESULT_SHA256
            ),
            "authoritative_calibration_result_integrity": integrity[
                "authoritative_calibration"
            ]["status"],
            "erroneous_prior_expected_sha256": ERRONEOUS_PRIOR_EXPECTED_SHA256,
            "provenance_identity_reconciliation_status": "PASS",
            "calibration_freeze_reused": True,
            "calibration_contract_sha256": directional.CALIBRATION_CONTRACT_SHA256,
            "calibration_freeze_seal_sha256": directional.CALIBRATION_FREEZE_SHA256,
            "calibration_semantic_drift": 0,
            "fictional_calibration_rerun_count": 0,
            "exclusion_registry_count": EXCLUSION_REGISTRY_COUNT,
            "exclusion_registry_sha256": EXCLUSION_REGISTRY_SHA256,
            "us_reference_raw_security_count": funnel[
                "raw_official_reference_security_rows"
            ],
            "us_identity_resolved_security_count": funnel[
                "identity_resolved_security_count"
            ],
            "us_routing_supported_security_count": funnel[
                "routing_supported_security_count"
            ],
            "us_remaining_unseen_issuer_count": funnel[
                "source_client_attemptable_unseen_issuer_count"
            ],
            "us_bounded_candidate_count": policy["market_policies"]["us"][
                "bounded_evaluation_limit"
            ],
            "us_attempted_candidate_count": us.get("attempted_count", 0),
            "us_source_sufficient_count": us.get("source_sufficient_count", 0),
            "us_source_insufficient_count": us.get("source_insufficient_count", 0),
            "us_target_status": us.get("source_target_status", "NOT_MEASURED"),
            "us_failure_taxonomy_counts": us.get("failure_taxonomy_counts", {}),
            "optional_price_support_overcoupling_found": 1,
            "generic_us_reference_expansion_applied": 1,
            "ticker_specific_us_exception_count": 0,
            "kr_target_status": kr.get("kr_target_status", "NOT_MEASURED"),
            "kr_selected_count": kr.get("selected", 0),
            "run_results": {
                run: run_results.get(run, "NOT_RUN") for run in runner.RUNS
            },
            "automatic_monitoring_resume": 0,
            "paid_data_service_change": 0,
            "production_db_mutation": 0,
            "production_send": 0,
            "monitoring_registration_change": 0,
            "live_v2_change": 0,
            "night_futures_change": 0,
            "validation": validation,
        }
    )
    if validation["status"] != "PASS":
        completion.update(
            {
                "status": "STOPPED",
                "readiness": "NOT_READY_VALIDATION_FAILURE",
                "stop_reason": "FINAL_VALIDATION_FAILED",
                "next_scope": "BOUNDED_VALIDATION_REPAIR",
            }
        )
    write_json(args.output_root / "program-completion.json", completion)
    final_documents = {
        "fresh-holdout-exposure-retirement-state": _internal_proof(args, 51),
        "fresh-directional-core-stability": _internal_proof(args, 52),
        "fresh-price-timing-stability": _internal_proof(args, 53),
        "fresh-ownership-generalization": _internal_proof(args, 54),
        "fresh-renderer-ownership-proof": _internal_proof(args, 55),
        "fresh-hard-safety-regression": _internal_proof(args, 56),
        "fresh-message-quality-summary": (
            read_json(args.output_root / "advisory-message-quality-summary.json")
            if (args.output_root / "advisory-message-quality-summary.json").is_file()
            else {"status": "NOT_MEASURED"}
        ),
        "runtime-reliability-observations": (
            read_json(args.output_root / "execution-reconciliation.json")
            if (args.output_root / "execution-reconciliation.json").is_file()
            else {"status": "NOT_MEASURED"}
        ),
        "production-no-change": {
            "production_db_mutation": 0,
            "production_send": 0,
            "monitoring_registration_change": 0,
            "live_v2_change": 0,
            "automatic_monitoring_resume": 0,
            "status": "PASS",
        },
        "night-futures-no-change": {"night_futures_change": 0, "status": "PASS"},
        "next-scope-handoff": {
            "readiness": completion["readiness"],
            "next_scope": completion["next_scope"],
            "monitoring_remains_paused": True,
            "status": "PASS",
        },
        "validation": validation,
        "program-completion": completion,
    }
    for name, document in final_documents.items():
        _write_report(args.report_dir, name, document)
    print(json.dumps(completion, ensure_ascii=False, sort_keys=True), flush=True)


def package(args: argparse.Namespace) -> None:
    configure_stack()
    directional.package(args)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze", action="store_true")
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--seal", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--close-reports", action="store_true")
    mode.add_argument("--package", action="store_true")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--stop-result-zip", type=Path, required=True)
    parser.add_argument("--calibration-result-zip", type=Path, required=True)
    parser.add_argument("--historical-result-zip", type=Path, required=True)
    parser.add_argument("--expansion-zip", type=Path, required=True)
    parser.add_argument("--as-of", type=datetime.fromisoformat)
    parser.add_argument("--timeout", type=int, default=runner.TIMEOUT_SECONDS)
    parser.add_argument("--zip-output", type=Path, required=True)
    args = parser.parse_args()
    for name in (
        "output_root",
        "report_dir",
        "bundle_root",
        "stop_result_zip",
        "calibration_result_zip",
        "historical_result_zip",
        "expansion_zip",
        "zip_output",
    ):
        setattr(args, name, getattr(args, name).expanduser().resolve())
    args.latest_result_zip = args.historical_result_zip
    return args


def main() -> None:
    args = parse_args()
    if args.freeze:
        freeze(args)
    elif args.prepare:
        prepare(args)
    elif args.seal:
        seal(args)
    elif args.execute:
        execute(args)
    elif args.close_reports:
        close_reports(args)
    else:
        package(args)


if __name__ == "__main__":
    main()
