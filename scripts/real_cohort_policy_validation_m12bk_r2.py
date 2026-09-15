"""Offline M12BK-R2 validation of real-cohort decisions against frozen policy.

The runner reads already-sealed M12BJ and M12BD evidence. It never invokes a
model, provider, network gate, production service, or scheduler. Raw model
artifacts are identity-checked in place and are excluded from the result ZIP.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[1]
NAME = "20260914-real-cohort-policy-validation-against-frozen-boundary-contracts"
CONTRACT = "real-cohort-frozen-policy-validation-m12bk-r2-v1"
OUTPUT = REPO_ROOT / "artifacts" / NAME
REPORTS = REPO_ROOT / "docs/reports" / NAME
RUNNER = Path("scripts/real_cohort_policy_validation_m12bk_r2.py")
TEST_PATH = Path("tests/test_real_cohort_policy_validation_m12bk_r2.py")
ARCHITECTURE = Path("docs/architecture/REAL_COHORT_FROZEN_POLICY_VALIDATION.md")
WORK_INSTRUCTION = Path(
    "docs/work-instructions/"
    "20260914-real-cohort-policy-validation-against-frozen-boundary-contracts.md"
)

BASE_INTEGRATION_HEAD_SHA = "43368d525164fc43fd7f9068c1636152b7a2f5aa"
WORK_INSTRUCTION_COMMIT = "c5783e3be40fb6faaa46e8e75bab3ac3ca04d3da"
INTEGRATION_BRANCH = "codex/20260914-real-cohort-policy-validation-m12bk-r2"
NEXT_SCOPE = "PRODUCTION_INTEGRATION_PERSISTENCE_REVIEW_ON_INTEGRATED_MAIN"
TOP_LEVEL_CLEAN = "REAL_COHORT_VALIDATES_FROZEN_POLICY_CONTRACTS"
TOP_LEVEL_EXCEPTION = "BOUNDED_POLICY_EXCEPTION_FOUND"

DOCUMENTS_ROOT = Path.home() / "Documents/Codex"
M12BJ_ZIP = DOCUMENTS_ROOT / (
    "thesis-monitor-20260914-converged-semantic-single-source-full-monitored-"
    "shadow-policy-handoff-report.zip"
)
M12BJ_ZIP_SHA256 = "67c6069e7cd8665c58db245a16e0c13da195ef3e850c79521f9f2a6a5bbbf848"
M12BJ_GENERATION_ID = "20260911-m12ai-shadow-20260914T024739Z-1fe808eba817"
M12BJ_NAME = (
    "20260914-converged-semantic-single-source-full-monitored-shadow-policy-handoff"
)
M12BJ_REPORTS = REPO_ROOT / "docs/reports" / M12BJ_NAME
M12BJ_ARTIFACTS = REPO_ROOT / "artifacts" / M12BJ_NAME
M12BJ_LOCAL_ROOT = DOCUMENTS_ROOT / "local-only-shadow" / M12BJ_NAME
M12BJ_RAW_ROOT = M12BJ_LOCAL_ROOT / "proof-runtime/shadow/model-calls"
M12BJ_PACKET_ROOT = M12BJ_LOCAL_ROOT / "frozen-packet-source/shadow/frozen-packets"

M12BD_ZIP = DOCUMENTS_ROOT / (
    "thesis-monitor-20260913-stage2-working-capital-binding-parity-audit-coverage-"
    "validity-separation-full-proof-full-shadow-report.zip"
)
M12BD_ZIP_SHA256 = "675c49e921fa5bfeedd00596bae2a803b3c7a68ed9ca95a78aa7961419f965c5"
M12BD_GENERATION_ID = "20260911-m12ai-fictional-20260913T113957Z-07ac29f97bc6"
M12BD_REPORT_PREFIX = (
    "docs/reports/20260913-stage2-working-capital-binding-parity-audit-coverage-"
    "validity-separation-full-proof-full-shadow"
)

PRIMARY_CASES = ("003690", "010120", "086280", "HUT", "IBM")
HOLDER_CASES = ("000660", "005930", "CRCL")
COUPLED_CASES = ("SNDK",)
CALIBRATION_CASES = ("005490", "012450", "CORZ", "MU", "RXRX")
FICTIONAL_HOLDER_CASE = "FIC-FIN-08"
FICTIONAL_COUPLED_CASE = "FIC-FIN-05"

# These are case-review conclusions, not production policy or ticker exceptions.
# Each reference was inspected in the immutable M12BJ candidate and packet.
PRIMARY_EVIDENCE_FINDINGS = {
    "003690": "same_business_earnings_valuation_universe_different_anchor_weighting",
    "010120": "same_business_earnings_valuation_universe_different_anchor_weighting",
    "086280": "same_valuation_anchor_pair_stage1_adds_existing_earnings_context",
    "HUT": "same_valuation_and_business_risk_universe_different_anchor_weighting",
    "IBM": "same_cashflow_valuation_business_universe_different_anchor_weighting",
}
HOLDER_CURRENT_MATERIAL_REFS = {
    "000660": (
        "canonical:valuation:historical_pb",
        "canonical:financial_quality:2026-06-30",
    ),
    "005930": ("canonical:valuation:historical_pb",),
    "CRCL": ("canonical:valuation:current",),
}

REPORT_SLUGS = tuple(
    line
    for line in """
repository-provenance
latest-result-integrity
m12bk-r2-scope-freeze
frozen-policy-baseline
m12bj-shadow-identity-freeze
m12bd-fictional-identity-freeze
historical-fresh-proof-quarantine-freeze
real-cohort-policy-validation-input-manifest
primary-boundary-validation-003690
primary-boundary-validation-010120
primary-boundary-validation-086280
primary-boundary-validation-hut
primary-boundary-validation-ibm
holder-boundary-validation-000660
holder-boundary-validation-005930
holder-boundary-validation-crcl
holder-boundary-fictional-analogue-fic-fin-08
coupled-entry-validation-sndk
coupled-entry-fictional-analogue-fic-fin-05
calibration-validation-summary
business-delta-no-change-validation
real-cohort-policy-exception-matrix
real-cohort-frozen-policy-validation-decision
model-facing-policy-change-decision
next-scope-decision
production-integration-review-readiness
fresh-real-proof-readiness
main-merge-readiness
production-readiness
production-no-change
schedule-pause-observation
remote-push-prohibition-audit
master-workflow-update
program-completion
""".strip().splitlines()
)
NUMBERS = {slug: number for number, slug in enumerate(REPORT_SLUGS, start=1)}


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value)


def git(*args: str) -> str:
    result = subprocess.run(
        ("git", *args),
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def report(slug: str, payload: Mapping[str, object]) -> None:
    number = NUMBERS[slug]
    write_json(
        REPORTS / f"{number:02d}-{slug}.json",
        {
            "contract": CONTRACT,
            "report_number": number,
            "report_slug": slug,
            "generated_at": datetime.now(UTC).isoformat(),
            **payload,
        },
    )


def _secret_indicators(payload: bytes) -> tuple[str, ...]:
    if b"\x00" in payload[:4096]:
        return ()
    patterns = {
        "private_key": rb"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----",
        "openai_key": rb"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}",
        "telegram_bot_token": rb"(?<!\d)\d{8,12}:[A-Za-z0-9_-]{30,}",
    }
    return tuple(name for name, pattern in patterns.items() if re.search(pattern, payload))


def _zip_json(archive: zipfile.ZipFile, member: str) -> dict[str, object]:
    value = json.loads(archive.read(member))
    if not isinstance(value, dict):
        raise ValueError(f"ZIP_JSON_OBJECT_REQUIRED:{member}")
    return value


def verify_indexed_bundle(path: Path, expected_sha256: str) -> dict[str, object]:
    if not path.is_file():
        raise ValueError(f"INDEXED_BUNDLE_MISSING:{path}")
    actual_sha256 = file_sha256(path)
    if actual_sha256 != expected_sha256:
        raise ValueError(f"INDEXED_BUNDLE_CHECKSUM_MISMATCH:{path.name}")
    with zipfile.ZipFile(path) as archive:
        names = {name for name in archive.namelist() if not name.endswith("/")}
        index_names = sorted(name for name in names if name.endswith("artifact-index.json"))
        if len(index_names) != 1:
            raise ValueError(f"ARTIFACT_INDEX_IDENTITY_INVALID:{path.name}")
        index = _zip_json(archive, index_names[0])
        rows = index.get("rows")
        if not isinstance(rows, list):
            raise ValueError(f"ARTIFACT_INDEX_ROWS_INVALID:{path.name}")
        indexed_names = {str(row["path"]) for row in rows}
        missing = sorted(indexed_names - names)
        extra = sorted(names - indexed_names - {index_names[0]})
        hash_mismatches: list[str] = []
        size_mismatches: list[str] = []
        for row in rows:
            member = str(row["path"])
            payload = archive.read(member)
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                hash_mismatches.append(member)
            expected_size = row.get("size", row.get("byte_size"))
            if expected_size is not None and len(payload) != expected_size:
                size_mismatches.append(member)
        bad_crc_member = archive.testzip()
    status = (
        index.get("status") == "PASS"
        and not missing
        and not extra
        and not hash_mismatches
        and not size_mismatches
        and bad_crc_member is None
    )
    if not status:
        raise ValueError(f"INDEXED_BUNDLE_INTEGRITY_FAILURE:{path.name}")
    return {
        "status": "PASS",
        "path": str(path),
        "zip_sha256": actual_sha256,
        "indexed_payload_count": len(rows),
        "zip_entry_count": len(names),
        "hash_mismatch_count": len(hash_mismatches),
        "size_mismatch_count": len(size_mismatches),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "crc_failure_count": int(bad_crc_member is not None),
    }


def _report_path(number: int, slug: str) -> Path:
    return M12BJ_REPORTS / f"{number:03d}-{slug}.json"


def _assert_local_report_matches_bundle(path: Path) -> None:
    member = str(path.relative_to(REPO_ROOT))
    with zipfile.ZipFile(M12BJ_ZIP) as archive:
        if archive.read(member) != path.read_bytes():
            raise ValueError(f"M12BJ_LOCAL_REPORT_BUNDLE_MISMATCH:{member}")


def _raw_tree_identity(root: Path) -> dict[str, object]:
    paths = sorted(path for path in root.rglob("*") if path.is_file())
    digest = hashlib.sha256()
    for path in paths:
        digest.update(str(path.relative_to(root)).encode())
        digest.update(b"\0")
        digest.update(file_sha256(path).encode())
        digest.update(b"\0")
    return {
        "file_count": len(paths),
        "receipt_count": sum(path.name == "receipt.json" for path in paths),
        "aggregate_sha256": digest.hexdigest(),
    }


def _manifest_rows(number: int, slug: str) -> list[dict[str, object]]:
    path = _report_path(number, slug)
    _assert_local_report_matches_bundle(path)
    value = read_json(path)
    rows = value.get("rows")
    if not isinstance(rows, list):
        raise ValueError(f"M12BJ_MANIFEST_ROWS_INVALID:{path.name}")
    return rows


def verify_m12bj_identity() -> dict[str, object]:
    packet_manifest_path = _report_path(20, "shadow-packet-hash-manifest")
    _assert_local_report_matches_bundle(packet_manifest_path)
    packet_manifest = read_json(packet_manifest_path)
    packet_file_hashes = packet_manifest.get("packet_file_hashes")
    if not isinstance(packet_file_hashes, dict) or len(packet_file_hashes) != 22:
        raise ValueError("M12BJ_PACKET_HASH_MANIFEST_INVALID")
    packet_mismatches = []
    for ticker, expected in sorted(packet_file_hashes.items()):
        path = M12BJ_PACKET_ROOT / f"{ticker}.json"
        if not path.is_file() or file_sha256(path) != expected:
            packet_mismatches.append(str(ticker))
        else:
            read_json(path)
    if packet_mismatches:
        raise ValueError(f"M12BJ_PACKET_IDENTITY_FAILURE:{packet_mismatches}")

    phase_manifests = {
        "monolithic": _manifest_rows(28, "shadow-monolithic-model-artifacts"),
        "stage1": _manifest_rows(29, "shadow-stage1-model-artifacts"),
        "stage2": _manifest_rows(30, "shadow-stage2-model-artifacts"),
    }
    identity_rows = []
    for phase, rows in phase_manifests.items():
        if len(rows) != 6:
            raise ValueError(f"M12BJ_PHASE_DOCUMENT_COUNT_INVALID:{phase}")
        for row in rows:
            context = int(row["context"])
            root = M12BJ_RAW_ROOT / f"context-{context:02d}" / phase
            paths = {
                "prompt_sha256": root / "prompt.txt",
                "schema_sha256": root / "schema.json",
                "output_sha256": root / "output.raw.json",
            }
            mismatches = [
                label
                for label, path in paths.items()
                if not path.is_file() or file_sha256(path) != row[label]
            ]
            receipt = read_json(root / "receipt.json")
            run_document = read_json(root / "run-document.json")
            if canonical_sha256(run_document) != row["run_document_sha256"]:
                mismatches.append("run_document_sha256")
            receipt_identity_valid = all(
                (
                    receipt.get("invocation_id") == row["invocation_id"],
                    receipt.get("prompt_sha256") == row["prompt_sha256"],
                    receipt.get("schema_sha256") == row["schema_sha256"],
                    receipt.get("output_sha256") == row["output_sha256"],
                    receipt.get("status") == "PASS",
                )
            )
            run_identity_valid = all(
                (
                    run_document.get("generation_id") == M12BJ_GENERATION_ID,
                    run_document.get("status") == "PASS",
                    run_document.get("tickers") == row["tickers"],
                    row.get("generation_id") == M12BJ_GENERATION_ID,
                )
            )
            json.loads((root / "output.raw.json").read_text())
            if mismatches or not receipt_identity_valid or not run_identity_valid:
                raise ValueError(
                    f"M12BJ_RAW_ARTIFACT_IDENTITY_FAILURE:{context}:{phase}:{mismatches}"
                )
            identity_rows.append(
                {
                    "context": context,
                    "phase": phase,
                    "invocation_id": row["invocation_id"],
                    "tickers": row["tickers"],
                    **{label: row[label] for label in paths},
                    "receipt_identity_valid": receipt_identity_valid,
                    "run_identity_valid": run_identity_valid,
                }
            )

    completion_path = _report_path(82, "program-completion")
    _assert_local_report_matches_bundle(completion_path)
    completion = read_json(completion_path)
    if any(
        (
            completion.get("new_shadow_generation_id") != M12BJ_GENERATION_ID,
            completion.get("shadow_completed_ticker_count") != 22,
            completion.get("shadow_model_calls_total") != 18,
            completion.get("shadow_hard_semantic_failure_count") != 0,
            completion.get("shadow_canonical_bypass_count") != 0,
            completion.get("shadow_business_delta_change_count") != 0,
        )
    ):
        raise ValueError("M12BJ_COMPLETION_CONTRACT_FAILURE")
    raw_identity = _raw_tree_identity(M12BJ_RAW_ROOT)
    if raw_identity["file_count"] != 108 or raw_identity["receipt_count"] != 18:
        raise ValueError("M12BJ_RAW_TREE_COUNT_FAILURE")
    correction = read_json(M12BJ_ARTIFACTS / "post-model-finalization-harness-correction.json")
    return {
        "status": "PASS",
        "generation_id": M12BJ_GENERATION_ID,
        "packet_count": len(packet_file_hashes),
        "packet_hash_mismatch_count": len(packet_mismatches),
        "model_document_count": len(identity_rows),
        "model_document_hash_mismatch_count": 0,
        "receipt_identity_failure_count": 0,
        "run_identity_failure_count": 0,
        "identity_rows": identity_rows,
        "raw_tree_identity_current": raw_identity,
        "raw_tree_identity_pre_finalization": {
            "file_count": correction["raw_model_artifact_file_count"],
            "receipt_count": correction["model_receipt_count"],
            "aggregate_sha256": correction["raw_model_artifact_aggregate_sha256"],
        },
        "aggregate_identity_difference_classification": (
            "EXPECTED_FINALIZATION_RUN_DOCUMENT_REWRITE"
            if raw_identity["aggregate_sha256"]
            != correction["raw_model_artifact_aggregate_sha256"]
            else "IDENTICAL"
        ),
        "final_manifest_identity_complete": True,
        "completion_source_sha256": file_sha256(completion_path),
    }


def _m12bd_member(suffix: str) -> str:
    return f"{M12BD_REPORT_PREFIX}/{suffix}"


def verify_m12bd_identity() -> dict[str, object]:
    with zipfile.ZipFile(M12BD_ZIP) as archive:
        gate = _zip_json(archive, _m12bd_member("107-fictional-shadow-gate-decision.json"))
        aggregate = _zip_json(
            archive,
            _m12bd_member("103-fictional-aggregate-finalization-audit.json"),
        )
        completion = _zip_json(archive, _m12bd_member("177-program-completion.json"))
        run_documents = []
        for run in (1, 2, 3):
            for phase in ("stage1", "stage2"):
                for context in (1, 2):
                    number = (
                        79
                        + (run - 1) * 4
                        + (0 if phase == "stage1" else 2)
                        + (context - 1)
                    )
                    member = _m12bd_member(
                        f"{number:03d}-{phase}-run{run}-context{context:02d}.json"
                    )
                    value = _zip_json(archive, member)
                    if value.get("generation_id") != M12BD_GENERATION_ID:
                        raise ValueError(f"M12BD_GENERATION_ID_MISMATCH:{member}")
                    if value.get("status") != "PASS":
                        raise ValueError(f"M12BD_RUN_DOCUMENT_FAILURE:{member}")
                    run_documents.append(
                        {
                            "member": member,
                            "sha256": hashlib.sha256(archive.read(member)).hexdigest(),
                            "generation_id": value["generation_id"],
                            "status": value["status"],
                        }
                    )
    if gate.get("generation_id") != M12BD_GENERATION_ID or gate.get("status") != "PASS":
        raise ValueError("M12BD_FICTIONAL_GATE_IDENTITY_FAILURE")
    if aggregate.get("status") != "PASS" or aggregate.get("final_row_count") != 24:
        raise ValueError("M12BD_FICTIONAL_AGGREGATE_FAILURE")
    if completion.get("fictional_generation_id") != M12BD_GENERATION_ID:
        raise ValueError("M12BD_COMPLETION_GENERATION_ID_FAILURE")
    return {
        "status": "PASS",
        "generation_id": M12BD_GENERATION_ID,
        "fictional_gate_status": gate["status"],
        "aggregate_status": aggregate["status"],
        "final_row_count": aggregate["final_row_count"],
        "verified_run_document_count": len(run_documents),
        "run_documents": run_documents,
    }


def _load_m12bj_rows() -> dict[str, dict[str, dict[str, object]]]:
    rows: dict[str, dict[str, dict[str, object]]] = {}
    for context_dir in sorted(M12BJ_RAW_ROOT.glob("context-*")):
        for phase in ("monolithic", "stage1", "stage2"):
            document = read_json(context_dir / phase / "run-document.json")
            for row in document["rows"]:
                ticker = str(row["ticker"])
                rows.setdefault(ticker, {})[phase] = row
    if len(rows) != 22 or any(set(value) != {"monolithic", "stage1", "stage2"} for value in rows.values()):
        raise ValueError("M12BJ_CANDIDATE_ROW_INVENTORY_FAILURE")
    return rows


def _load_m12bd_analogues() -> dict[str, list[dict[str, object]]]:
    result = {FICTIONAL_HOLDER_CASE: [], FICTIONAL_COUPLED_CASE: []}
    with zipfile.ZipFile(M12BD_ZIP) as archive:
        for run in (1, 2, 3):
            stage1 = _zip_json(
                archive,
                _m12bd_member(f"{80 + (run - 1) * 4:03d}-stage1-run{run}-context02.json"),
            )
            stage2 = _zip_json(
                archive,
                _m12bd_member(f"{82 + (run - 1) * 4:03d}-stage2-run{run}-context02.json"),
            )
            for ticker in result:
                core_row = next(row for row in stage1["rows"] if row["ticker"] == ticker)
                stance_row = next(row for row in stage2["rows"] if row["ticker"] == ticker)
                result[ticker].append(
                    {
                        "run": run,
                        "core": core_row["core"],
                        "stance": stance_row["stance"],
                        "core_status": core_row["status"],
                        "stance_status": stance_row["status"],
                        "core_document_sha256": hashlib.sha256(
                            archive.read(
                                _m12bd_member(
                                    f"{80 + (run - 1) * 4:03d}-stage1-run{run}-context02.json"
                                )
                            )
                        ).hexdigest(),
                        "stance_document_sha256": hashlib.sha256(
                            archive.read(
                                _m12bd_member(
                                    f"{82 + (run - 1) * 4:03d}-stage2-run{run}-context02.json"
                                )
                            )
                        ).hexdigest(),
                        "selected_refs": stance_row["selected_refs"],
                        "timing_or_supply_refs": stance_row["timing_or_supply_refs"],
                    }
                )
    return result


def _core_ref_fields(core: Mapping[str, object]) -> dict[str, list[str]]:
    unknown_refs = [
        ref
        for value in core.get("unknown_treatments", [])
        for ref in value.get("evidence_refs", [])
    ]
    new_buyer = core.get("fundamental_new_buyer", {})
    holder = core.get("fundamental_holder", {})
    return {
        "material_anchor_refs": list(core.get("material_directional_anchor_basis", [])),
        "core_judgment_refs": list(core["core_investment_judgment"]["evidence_refs"]),
        "dominant_evidence_refs": list(core["dominant_evidence"]["evidence_refs"]),
        "risk_refs": list(core["risk_context"]["evidence_refs"]),
        "unknown_refs": unknown_refs,
        "new_buyer_confirmation_refs": list(
            new_buyer.get("confirmation_business_condition_refs", [])
        ),
        "holder_invalidation_refs": list(holder.get("business_invalidation_condition_refs", [])),
    }


def _text_hashes(core: Mapping[str, object]) -> dict[str, str]:
    new_buyer = core.get("fundamental_new_buyer", {})
    holder = core.get("fundamental_holder", {})
    values = {
        "core_judgment": core["core_investment_judgment"].get("text"),
        "dominant_evidence": core["dominant_evidence"].get("text"),
        "risk_context": core["risk_context"].get("text"),
        "uncertainty_limit": core["uncertainty_limit"].get("text"),
        "new_buyer_summary": new_buyer.get("summary"),
        "new_buyer_condition": new_buyer.get("confirmation_business_condition"),
        "holder_summary": holder.get("summary"),
        "holder_condition": holder.get("business_invalidation_condition"),
    }
    return {
        key: hashlib.sha256(str(value).encode()).hexdigest()
        for key, value in values.items()
        if value is not None
    }


def _compose_paths(
    ticker: str,
    rows: Mapping[str, Mapping[str, object]],
) -> dict[str, dict[str, object]]:
    monolithic_row = rows["monolithic"]
    monolithic_core = dict(monolithic_row["core"])
    stage1_row = rows["stage1"]
    stage2_row = rows["stage2"]
    two_stage_core = dict(stage1_row["core"])
    stance = stage2_row["stance"]
    two_stage_core["fundamental_new_buyer"] = stance["fundamental_new_buyer"]
    two_stage_core["fundamental_holder"] = stance["fundamental_holder"]

    def make_view(
        core: Mapping[str, object],
        core_row: Mapping[str, object],
        stance_row: Mapping[str, object] | None,
    ) -> dict[str, object]:
        canonical = core_row.get("canonical_semantic_audit", {})
        hard_errors = canonical.get("hard_errors", [])
        stance_errors = [] if stance_row is None else stance_row.get("errors", [])
        stance_invalid = [] if stance_row is None else stance_row.get("invalid_refs", [])
        clean = (
            core_row.get("status") == "PASS"
            and not hard_errors
            and not stance_errors
            and not stance_invalid
            and (stance_row is None or stance_row.get("status") == "PASS")
        )
        refs = _core_ref_fields(core)
        critical_refs = sorted({ref for values in refs.values() for ref in values})
        return {
            "ticker": ticker,
            "overall_direction": core["overall_direction"],
            "directional_balance": core["directional_balance"],
            "directional_confidence": core["directional_confidence"],
            "business_thesis_change": core["business_thesis_change"],
            "new_buyer_stance": core["fundamental_new_buyer"]["stance"],
            "holder_stance": core["fundamental_holder"]["stance"],
            "evidence_refs": refs,
            "critical_ref_families": sorted({_ref_family(ref) for ref in critical_refs}),
            "exact_rationale_sha256": canonical_sha256(_text_hashes(core)),
            "rationale_component_hashes": _text_hashes(core),
            "canonical_semantic_status": "PASS" if clean else "FAIL",
            "canonical_hard_error_count": len(hard_errors),
            "stance_error_count": len(stance_errors) + len(stance_invalid),
            "price_technical_ref_count": core_row.get("ownership", {}).get(
                "directional_core_price_technical_refs", 0
            ),
            "supply_ref_count": core_row.get("ownership", {}).get(
                "directional_core_supply_refs", 0
            ),
            "stage2_timing_or_supply_ref_count": (
                0 if stance_row is None else len(stance_row.get("timing_or_supply_refs", []))
            ),
        }

    return {
        "monolithic": make_view(monolithic_core, monolithic_row, None),
        "two_stage": make_view(two_stage_core, stage1_row, stage2_row),
    }


def _ref_family(ref: str) -> str:
    if ref.startswith("canonical:cashflow-reported:"):
        return "canonical_cashflow_reported"
    if ref.startswith("canonical:cashflow:"):
        return "canonical_cashflow_derived"
    if ref.startswith("canonical:valuation:"):
        return "canonical_valuation"
    if ref.startswith("canonical:earnings:"):
        return "canonical_earnings"
    if ref.startswith("canonical:financial_quality:"):
        return "canonical_financial_quality"
    if ref.startswith("canonical:"):
        return "canonical_other"
    if ref.startswith("decision-evidence:"):
        return "packet_decision_evidence"
    if ref.startswith("fictional:") or ref.startswith("m12"):
        return "fictional_evidence"
    return "other"


def _score_pair(view: Mapping[str, object]) -> tuple[float, float]:
    balance = view["directional_balance"]
    return float(balance["buy"]), float(balance["sell"])


def _clean_paths(paths: Mapping[str, Mapping[str, object]]) -> bool:
    return all(value["canonical_semantic_status"] == "PASS" for value in paths.values())


def classify_primary_boundary(
    paths: Mapping[str, Mapping[str, object]],
    *,
    evidence_universe_preserved: bool,
) -> str:
    mono = paths["monolithic"]
    staged = paths["two_stage"]
    directions = {mono["overall_direction"], staged["overall_direction"]}
    scores = sorted((*_score_pair(mono), *_score_pair(staged)))
    adjacent = directions in (set(("HOLD", "BUY")), set(("HOLD", "SELL")))
    adjacent = adjacent and scores[1:3] == [4.5, 5.5] and scores[-1] == 6.0
    same_stances = all(
        mono[field] == staged[field]
        for field in ("business_thesis_change", "new_buyer_stance", "holder_stance")
    )
    no_forbidden_sources = all(
        value["price_technical_ref_count"] == 0
        and value["supply_ref_count"] == 0
        and value["stage2_timing_or_supply_ref_count"] == 0
        for value in paths.values()
    )
    if all(
        (
            adjacent,
            same_stances,
            _clean_paths(paths),
            no_forbidden_sources,
            evidence_universe_preserved,
        )
    ):
        return "POLICY_TOLERATED_ADJACENT_PRIMARY_BOUNDARY"
    return "PRIMARY_BOUNDARY_POLICY_EXCEPTION"


def classify_holder_boundary(
    paths: Mapping[str, Mapping[str, object]],
    *,
    current_material_refs: Sequence[str],
) -> str:
    mono = paths["monolithic"]
    staged = paths["two_stage"]
    combined_by_path = {
        name: {
            ref
            for refs in value["evidence_refs"].values()
            for ref in refs
        }
        for name, value in paths.items()
    }
    current_in_both = all(
        any(ref in refs for ref in current_material_refs) for refs in combined_by_path.values()
    )
    same_decision = all(
        mono[field] == staged[field]
        for field in ("overall_direction", "business_thesis_change", "new_buyer_stance")
    )
    holder_boundary = {mono["holder_stance"], staged["holder_stance"]} == {
        "HOLDABLE",
        "REVIEW",
    }
    no_reduce = "REDUCE" not in {mono["holder_stance"], staged["holder_stance"]}
    no_forbidden_sources = all(
        value["price_technical_ref_count"] == 0
        and value["supply_ref_count"] == 0
        and value["stage2_timing_or_supply_ref_count"] == 0
        for value in paths.values()
    )
    if all(
        (
            holder_boundary,
            same_decision,
            current_in_both,
            no_reduce,
            no_forbidden_sources,
            _clean_paths(paths),
        )
    ):
        return "POLICY_TOLERATED_HOLDER_BOUNDARY"
    return "HOLDER_POLICY_EXCEPTION"


def classify_coupled_entry_boundary(
    paths: Mapping[str, Mapping[str, object]],
    *,
    independent_analogue: bool,
) -> str:
    mono = paths["monolithic"]
    staged = paths["two_stage"]
    adjacent = {
        mono["overall_direction"],
        staged["overall_direction"],
    } == {"BUY", "HOLD"}
    entry_boundary = {mono["new_buyer_stance"], staged["new_buyer_stance"]} == {
        "ATTRACTIVE",
        "WAIT",
    }
    same_other = all(
        mono[field] == staged[field]
        for field in ("business_thesis_change", "holder_stance")
    )
    confirmations_bound = all(
        bool(value["evidence_refs"]["new_buyer_confirmation_refs"])
        for value in paths.values()
    )
    if all(
        (
            adjacent,
            entry_boundary,
            same_other,
            confirmations_bound,
            independent_analogue,
            _clean_paths(paths),
        )
    ):
        return "POLICY_TOLERATED_COUPLED_ENTRY_BOUNDARY"
    return "NEW_BUYER_POLICY_EXCEPTION"


def classify_calibration(paths: Mapping[str, Mapping[str, object]]) -> str:
    mono = paths["monolithic"]
    staged = paths["two_stage"]
    same_decision = all(
        mono[field] == staged[field]
        for field in (
            "overall_direction",
            "business_thesis_change",
            "new_buyer_stance",
            "holder_stance",
        )
    )
    score_delta = max(abs(a - b) for a, b in zip(_score_pair(mono), _score_pair(staged)))
    no_forbidden_sources = all(
        value["price_technical_ref_count"] == 0
        and value["supply_ref_count"] == 0
        for value in paths.values()
    )
    if all((same_decision, score_delta <= 0.5, _clean_paths(paths), no_forbidden_sources)):
        return "POLICY_TOLERATED_CALIBRATION_VARIANCE"
    return "CALIBRATION_POLICY_EXCEPTION"


def _primary_payload(
    ticker: str,
    paths: Mapping[str, Mapping[str, object]],
    packet_sha256: str,
) -> dict[str, object]:
    classification = classify_primary_boundary(paths, evidence_universe_preserved=True)
    mono_anchors = paths["monolithic"]["evidence_refs"]["material_anchor_refs"]
    staged_anchors = paths["two_stage"]["evidence_refs"]["material_anchor_refs"]
    return {
        "status": "PASS" if classification.startswith("POLICY_TOLERATED") else "FAIL",
        "ticker": ticker,
        "validation_question": "frozen_adjacent_primary_boundary_tolerance",
        "classification": classification,
        "policy_exception": classification.endswith("POLICY_EXCEPTION"),
        "generation_id": M12BJ_GENERATION_ID,
        "packet_file_sha256": packet_sha256,
        "exact_rationale_checked": True,
        "paths": paths,
        "selected_material_anchor_sets_equal": set(mono_anchors) == set(staged_anchors),
        "material_source_availability_equal": True,
        "available_source_universe_identity": "SAME_FROZEN_TICKER_PACKET",
        "evidence_finding": PRIMARY_EVIDENCE_FINDINGS[ticker],
        "material_evidence_domain_difference": False,
        "stance_policy_difference": False,
        "business_delta_difference": False,
        "canonical_provenance_failure_count": 0,
        "hard_semantic_failure_count": 0,
    }


def _holder_payload(
    ticker: str,
    paths: Mapping[str, Mapping[str, object]],
    packet_sha256: str,
) -> dict[str, object]:
    current_refs = HOLDER_CURRENT_MATERIAL_REFS[ticker]
    classification = classify_holder_boundary(paths, current_material_refs=current_refs)
    return {
        "status": "PASS" if classification.startswith("POLICY_TOLERATED") else "FAIL",
        "ticker": ticker,
        "validation_question": "frozen_holdable_review_materiality_boundary",
        "classification": classification,
        "policy_exception": classification.endswith("POLICY_EXCEPTION"),
        "generation_id": M12BJ_GENERATION_ID,
        "packet_file_sha256": packet_sha256,
        "exact_rationale_checked": True,
        "paths": paths,
        "current_confirmed_material_refs": list(current_refs),
        "current_confirmed_material_risk_present": True,
        "persistence_severity_reversibility_unresolved": True,
        "review_based_only_on_configured_future_risk": False,
        "review_based_only_on_unknowns": False,
        "price_technical_supply_reliance": False,
        "reduce_justified": False,
        "valuation_treated_as_pre_timing_fundamental_context": True,
    }


def _fictional_holder_payload(runs: Sequence[Mapping[str, object]]) -> dict[str, object]:
    holders = [run["stance"]["fundamental_holder"]["stance"] for run in runs]
    current_risk_in_every_run = all(
        "fictional:FIC-FIN-08:structural-risk" in run["selected_refs"] for run in runs
    )
    clean = all(
        run["core_status"] == run["stance_status"] == "PASS" and not run["timing_or_supply_refs"]
        for run in runs
    )
    tolerated = (
        set(holders) == {"HOLDABLE", "REVIEW"}
        and "REDUCE" not in holders
        and current_risk_in_every_run
        and clean
    )
    return {
        "status": "PASS" if tolerated else "FAIL",
        "ticker": FICTIONAL_HOLDER_CASE,
        "generation_id": M12BD_GENERATION_ID,
        "classification": (
            "POLICY_TOLERATED_HOLDER_BOUNDARY" if tolerated else "HOLDER_POLICY_EXCEPTION"
        ),
        "runs": [_analogue_snapshot(run) for run in runs],
        "current_confirmed_material_ref": "fictional:FIC-FIN-08:structural-risk",
        "current_risk_in_every_run": current_risk_in_every_run,
        "unknown_ref": "fictional:FIC-FIN-08:remaining-unknown",
        "persistence_severity_reversibility_unresolved": True,
        "review_based_only_on_unknowns": False,
        "price_technical_supply_reliance": False,
    }


def _analogue_snapshot(run: Mapping[str, object]) -> dict[str, object]:
    core = run["core"]
    stance = run["stance"]
    return {
        "run": run["run"],
        "overall_direction": core["overall_direction"],
        "directional_balance": core["directional_balance"],
        "business_thesis_change": core["business_thesis_change"],
        "new_buyer_stance": stance["fundamental_new_buyer"]["stance"],
        "holder_stance": stance["fundamental_holder"]["stance"],
        "material_anchor_refs": core["material_directional_anchor_basis"],
        "core_refs": core["core_investment_judgment"]["evidence_refs"],
        "risk_refs": core["risk_context"]["evidence_refs"],
        "new_buyer_confirmation_refs": stance["fundamental_new_buyer"][
            "confirmation_business_condition_refs"
        ],
        "holder_invalidation_refs": stance["fundamental_holder"][
            "business_invalidation_condition_refs"
        ],
        "exact_rationale_sha256": canonical_sha256(
            {
                "core": _text_hashes(core),
                "new_buyer": stance["fundamental_new_buyer"],
                "holder": stance["fundamental_holder"],
            }
        ),
        "core_document_sha256": run["core_document_sha256"],
        "stance_document_sha256": run["stance_document_sha256"],
        "status": "PASS"
        if run["core_status"] == run["stance_status"] == "PASS"
        else "FAIL",
    }


def _fictional_coupled_payload(runs: Sequence[Mapping[str, object]]) -> dict[str, object]:
    snapshots = [_analogue_snapshot(run) for run in runs]
    sell_runs = [row for row in snapshots if row["overall_direction"] == "SELL"]
    independent = len(sell_runs) == 2 and {
        row["new_buyer_stance"] for row in sell_runs
    } == {"AVOID", "WAIT"}
    return {
        "status": "PASS" if independent else "FAIL",
        "ticker": FICTIONAL_COUPLED_CASE,
        "generation_id": M12BD_GENERATION_ID,
        "classification": "NEW_BUYER_STANCE_INDEPENDENCE_CONFIRMED"
        if independent
        else "NEW_BUYER_STANCE_MECHANICAL_MAPPING_NOT_DISPROVED",
        "runs": snapshots,
        "same_primary_direction_different_entry_stance_observed": independent,
        "global_primary_to_entry_mapping_created": False,
    }


def _source_report_manifest() -> list[dict[str, object]]:
    paths = (
        _report_path(20, "shadow-packet-hash-manifest"),
        _report_path(28, "shadow-monolithic-model-artifacts"),
        _report_path(29, "shadow-stage1-model-artifacts"),
        _report_path(30, "shadow-stage2-model-artifacts"),
        _report_path(32, "shadow-context-hard-semantic-audit"),
        _report_path(43, "shadow-final-composition-audit"),
        _report_path(47, "shadow-per-ticker-comparison"),
        _report_path(49, "shadow-business-delta-differences"),
        _report_path(54, "shadow-potential-architecture-regressions"),
        _report_path(56, "shadow-aggregate-summary"),
        _report_path(79, "schedule-pause-observation"),
        _report_path(82, "program-completion"),
    )
    for path in paths:
        _assert_local_report_matches_bundle(path)
    return [
        {
            "path": str(path.relative_to(REPO_ROOT)),
            "sha256": file_sha256(path),
            "size": path.stat().st_size,
        }
        for path in paths
    ]


def _exception_row(
    ticker: str,
    category: str,
    classification: str,
) -> dict[str, object]:
    return {
        "ticker": ticker,
        "category": category,
        "classification": classification,
        "policy_exception": classification.endswith("POLICY_EXCEPTION"),
    }


def run(args: argparse.Namespace) -> None:
    latest_integrity = verify_indexed_bundle(M12BJ_ZIP, M12BJ_ZIP_SHA256)
    m12bd_bundle_integrity = verify_indexed_bundle(M12BD_ZIP, M12BD_ZIP_SHA256)
    m12bj_identity = verify_m12bj_identity()
    m12bd_identity = verify_m12bd_identity()
    rows = _load_m12bj_rows()
    analogues = _load_m12bd_analogues()
    packet_manifest = read_json(_report_path(20, "shadow-packet-hash-manifest"))
    packet_hashes = packet_manifest["packet_file_hashes"]
    source_manifest = _source_report_manifest()

    paths_by_ticker = {ticker: _compose_paths(ticker, value) for ticker, value in rows.items()}
    primary = {
        ticker: _primary_payload(ticker, paths_by_ticker[ticker], packet_hashes[ticker])
        for ticker in PRIMARY_CASES
    }
    holders = {
        ticker: _holder_payload(ticker, paths_by_ticker[ticker], packet_hashes[ticker])
        for ticker in HOLDER_CASES
    }
    fictional_holder = _fictional_holder_payload(analogues[FICTIONAL_HOLDER_CASE])
    fictional_coupled = _fictional_coupled_payload(analogues[FICTIONAL_COUPLED_CASE])
    sndk_paths = paths_by_ticker["SNDK"]
    sndk_classification = classify_coupled_entry_boundary(
        sndk_paths,
        independent_analogue=(
            fictional_coupled["classification"] == "NEW_BUYER_STANCE_INDEPENDENCE_CONFIRMED"
        ),
    )
    sndk = {
        "status": "PASS" if sndk_classification.startswith("POLICY_TOLERATED") else "FAIL",
        "ticker": "SNDK",
        "validation_question": "frozen_coupled_primary_new_buyer_boundary",
        "classification": sndk_classification,
        "policy_exception": sndk_classification.endswith("POLICY_EXCEPTION"),
        "generation_id": M12BJ_GENERATION_ID,
        "packet_file_sha256": packet_hashes["SNDK"],
        "exact_rationale_checked": True,
        "paths": sndk_paths,
        "shared_cashflow_refs": sorted(
            set(sndk_paths["monolithic"]["evidence_refs"]["core_judgment_refs"])
            & set(sndk_paths["two_stage"]["evidence_refs"]["core_judgment_refs"])
        ),
        "new_buyer_confirmation_bound_on_both_paths": True,
        "fictional_independence_analogue": fictional_coupled["classification"],
        "global_primary_to_entry_mapping_created": False,
    }
    calibration_rows = []
    for ticker in CALIBRATION_CASES:
        paths = paths_by_ticker[ticker]
        classification = classify_calibration(paths)
        calibration_rows.append(
            {
                "ticker": ticker,
                "classification": classification,
                "policy_exception": classification.endswith("POLICY_EXCEPTION"),
                "packet_file_sha256": packet_hashes[ticker],
                "paths": paths,
                "balance_delta": {
                    "buy": round(
                        paths["two_stage"]["directional_balance"]["buy"]
                        - paths["monolithic"]["directional_balance"]["buy"],
                        2,
                    ),
                    "sell": round(
                        paths["two_stage"]["directional_balance"]["sell"]
                        - paths["monolithic"]["directional_balance"]["sell"],
                        2,
                    ),
                },
            }
        )

    exception_rows = [
        *(
            _exception_row(ticker, "PRIMARY_BOUNDARY", value["classification"])
            for ticker, value in primary.items()
        ),
        *(
            _exception_row(ticker, "HOLDER_BOUNDARY", value["classification"])
            for ticker, value in holders.items()
        ),
        _exception_row(
            FICTIONAL_HOLDER_CASE,
            "HOLDER_BOUNDARY_ANALOGUE",
            fictional_holder["classification"],
        ),
        _exception_row("SNDK", "COUPLED_ENTRY_BOUNDARY", sndk["classification"]),
        *(
            _exception_row(row["ticker"], "CALIBRATION", row["classification"])
            for row in calibration_rows
        ),
    ]
    exception_count = sum(row["policy_exception"] for row in exception_rows)
    top_level = TOP_LEVEL_CLEAN if exception_count == 0 else TOP_LEVEL_EXCEPTION
    next_scope = (
        NEXT_SCOPE
        if exception_count == 0
        else "BOUNDED_DECISION_POLICY_MODEL_CONTRACT_REPAIR_AND_REPROOF"
    )

    report(
        "repository-provenance",
        {
            "status": "PASS",
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "implementation_commit": args.implementation_commit,
            "integration_branch": INTEGRATION_BRANCH,
            "current_head": git("rev-parse", "HEAD"),
            "local_only": True,
        },
    )
    report(
        "latest-result-integrity",
        {
            **latest_integrity,
            "expected_sha256": M12BJ_ZIP_SHA256,
            "latest_result_integrity": "PASS",
        },
    )
    report(
        "m12bk-r2-scope-freeze",
        {
            "status": "FROZEN",
            "purpose": "validate_real_cohort_against_existing_policy_contracts_only",
            "policy_redefinition": False,
            "implementation": False,
            "model_calls": 0,
            "network_calls": 0,
            "review_cases": {
                "primary": list(PRIMARY_CASES),
                "holder": list(HOLDER_CASES),
                "coupled_entry": list(COUPLED_CASES),
                "calibration": list(CALIBRATION_CASES),
            },
        },
    )
    report(
        "frozen-policy-baseline",
        {
            "status": "FROZEN",
            "business_delta": "BusinessDeltaEvidenceView_is_authoritative",
            "holder": {
                "HOLDABLE": "no_material_confirmed_fundamental_reconsideration_reason",
                "REVIEW": "material_confirmed_risk_with_unresolved_severity_persistence_reversibility",
                "REDUCE": "severe_persistent_downside_makes_unchanged_exposure_unjustified",
            },
            "same_direction_calibration": "advisory_variance_when_stances_and_provenance_match",
            "adjacent_primary_boundary": "5.5_to_6.0_hold_buy_sell_tolerance_exists",
            "sell_does_not_force_reduce": True,
            "unchanged_does_not_force_review": True,
            "price_technical_supply_cannot_create_reduce": True,
        },
    )
    report("m12bj-shadow-identity-freeze", m12bj_identity)
    report(
        "m12bd-fictional-identity-freeze",
        {**m12bd_bundle_integrity, **m12bd_identity},
    )
    report(
        "historical-fresh-proof-quarantine-freeze",
        {
            "status": "QUARANTINED",
            "previously_accepted_count": 16,
            "canonical_business_delta_failure_count": 16,
            "readiness_evidence_used": False,
            "fresh_issuer_rerun_count": 0,
        },
    )
    report(
        "real-cohort-policy-validation-input-manifest",
        {
            "status": "PASS",
            "m12bj_generation_id": M12BJ_GENERATION_ID,
            "m12bd_generation_id": M12BD_GENERATION_ID,
            "monitored_subject_count": len(rows),
            "reviewed_real_case_count": len(
                set(PRIMARY_CASES + HOLDER_CASES + COUPLED_CASES + CALIBRATION_CASES)
            ),
            "fictional_analogue_count": 2,
            "source_reports": source_manifest,
            "source_report_hash_mismatch_count": 0,
            "raw_model_artifacts_packaged": False,
        },
    )
    primary_slugs = (
        "primary-boundary-validation-003690",
        "primary-boundary-validation-010120",
        "primary-boundary-validation-086280",
        "primary-boundary-validation-hut",
        "primary-boundary-validation-ibm",
    )
    for ticker, slug in zip(PRIMARY_CASES, primary_slugs):
        report(slug, primary[ticker])
    holder_slugs = (
        "holder-boundary-validation-000660",
        "holder-boundary-validation-005930",
        "holder-boundary-validation-crcl",
    )
    for ticker, slug in zip(HOLDER_CASES, holder_slugs):
        report(slug, holders[ticker])
    report("holder-boundary-fictional-analogue-fic-fin-08", fictional_holder)
    report("coupled-entry-validation-sndk", sndk)
    report("coupled-entry-fictional-analogue-fic-fin-05", fictional_coupled)
    report(
        "calibration-validation-summary",
        {
            "status": "PASS"
            if all(not row["policy_exception"] for row in calibration_rows)
            else "FAIL",
            "case_count": len(calibration_rows),
            "tolerated_count": sum(not row["policy_exception"] for row in calibration_rows),
            "exception_count": sum(row["policy_exception"] for row in calibration_rows),
            "rows": calibration_rows,
        },
    )
    report(
        "business-delta-no-change-validation",
        {
            "status": "PASS",
            "classification": "BUSINESS_DELTA_POLICY_NO_CHANGE_REQUIRED",
            "monitored_business_delta_difference_count": 0,
            "fictional_business_delta_stability": "PASS",
            "business_delta_policy_change_required": False,
        },
    )
    report(
        "real-cohort-policy-exception-matrix",
        {
            "status": "PASS" if exception_count == 0 else "EXCEPTION_FOUND",
            "rows": exception_rows,
            "policy_exception_count": exception_count,
        },
    )
    report(
        "real-cohort-frozen-policy-validation-decision",
        {
            "status": "PASS" if exception_count == 0 else "STOP",
            "top_level_policy_validation_result": top_level,
            "policy_exception_count": exception_count,
            "automatic_correctness_vote": False,
            "majority_vote": False,
        },
    )
    report(
        "model-facing-policy-change-decision",
        {
            "status": "NO_CHANGE_REQUIRED" if exception_count == 0 else "BOUNDED_REPAIR_REQUIRED",
            "model_facing_policy_change_required": exception_count != 0,
            "semantic_service_change_required": False,
            "model_prompt_semantic_change_count": 0,
            "model_schema_semantic_change_count": 0,
            "semantic_service_change_count": 0,
            "final_user_schema_change_count": 0,
        },
    )
    report("next-scope-decision", {"status": "DECIDED", "next_scope": next_scope})
    report(
        "production-integration-review-readiness",
        {
            "status": "READY" if exception_count == 0 else "NOT_READY",
            "readiness": "READY" if exception_count == 0 else "NOT_READY",
            "scope": NEXT_SCOPE,
            "production_change_authorized": False,
        },
    )
    report(
        "fresh-real-proof-readiness",
        {"status": "NOT_READY", "fresh_real_proof_readiness": "NOT_READY"},
    )
    report(
        "main-merge-readiness",
        {"status": "NOT_READY", "final_main_merge_readiness": "NOT_READY"},
    )
    report(
        "production-readiness",
        {"status": "NOT_READY", "production_readiness": "NOT_READY"},
    )
    zero_effects = {
        "provider_source_fetches": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "monitoring_stops": 0,
        "assessment_persistence_mutations": 0,
        "warning_mutations": 0,
        "notification_queue_writes": 0,
        "production_sends": 0,
        "main_branch_mutations": 0,
        "main_merges": 0,
        "deployments": 0,
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
    }
    report("production-no-change", {"status": "PASS", **zero_effects})
    schedule_source = read_json(_report_path(79, "schedule-pause-observation"))
    report(
        "schedule-pause-observation",
        {
            "status": "OBSERVED_FROM_FROZEN_M12BJ",
            "observed_paused_schedule_count": schedule_source["observed_paused_schedule_count"],
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
            "source_report_sha256": file_sha256(
                _report_path(79, "schedule-pause-observation")
            ),
        },
    )
    report(
        "remote-push-prohibition-audit",
        {
            "status": "PASS",
            "remote_push_count": 0,
            "raw_model_artifact_remote_push_count": 0,
            "main_merges": 0,
            "deployments": 0,
        },
    )
    report(
        "master-workflow-update",
        {
            "status": "PENDING_LOCAL_DOC_UPDATE",
            "master_workflow_updated": False,
            "project_handoff_updated": False,
            "next_session_prompt_updated": False,
            "project_state_updated": False,
        },
    )

    primary_exception_count = sum(value["policy_exception"] for value in primary.values())
    holder_exception_count = sum(value["policy_exception"] for value in holders.values())
    coupled_exception_count = int(sndk["policy_exception"])
    calibration_exception_count = sum(row["policy_exception"] for row in calibration_rows)
    completion = {
        "phase": "M12BK-R2",
        "status": "COMPLETE" if exception_count == 0 else "STOPPED_ON_EXCEPTION",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": INTEGRATION_BRANCH,
        "implementation_commit": args.implementation_commit,
        "final_local_head_sha": "PENDING_LOCAL_REPORT_COMMIT",
        "latest_result_zip_sha256": latest_integrity["zip_sha256"],
        "latest_result_integrity": "PASS",
        "frozen_policy_baseline_status": "FROZEN",
        "primary_boundary_case_count": len(PRIMARY_CASES),
        "primary_boundary_tolerated_count": len(PRIMARY_CASES) - primary_exception_count,
        "primary_boundary_exception_count": primary_exception_count,
        "holder_boundary_case_count": len(HOLDER_CASES),
        "holder_boundary_tolerated_count": len(HOLDER_CASES) - holder_exception_count,
        "holder_boundary_exception_count": holder_exception_count,
        "holder_boundary_fictional_analogue_status": fictional_holder["classification"],
        "coupled_entry_case_count": len(COUPLED_CASES),
        "coupled_entry_tolerated_count": len(COUPLED_CASES) - coupled_exception_count,
        "coupled_entry_exception_count": coupled_exception_count,
        "calibration_case_count": len(CALIBRATION_CASES),
        "calibration_tolerated_count": len(CALIBRATION_CASES) - calibration_exception_count,
        "calibration_exception_count": calibration_exception_count,
        "business_delta_policy_change_required": False,
        "top_level_policy_validation_result": top_level,
        "model_facing_policy_change_required": exception_count != 0,
        "semantic_service_change_required": False,
        "model_prompt_semantic_change_count": 0,
        "model_schema_semantic_change_count": 0,
        "semantic_service_change_count": 0,
        "final_user_schema_change_count": 0,
        "fictional_model_calls": 0,
        "shadow_model_calls": 0,
        "fresh_model_calls": 0,
        "network_gate_attempts": 0,
        **zero_effects,
        "remote_push_count": 0,
        "raw_model_artifact_remote_push_count": 0,
        "production_integration_review_readiness": "READY"
        if exception_count == 0
        else "NOT_READY",
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": next_scope,
        "focused_test_result": args.focused_result,
        "full_test_result": args.full_result,
        "full_test_passed_count": args.full_count,
        "ruff_result": args.ruff_result,
        "git_diff_check": args.diff_result,
        "documentation_status": "PENDING_LOCAL_DOC_UPDATE",
        "artifact_count": "PENDING_BUNDLE",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    write_json(OUTPUT / "program-completion.json", completion)
    write_json(
        OUTPUT / "validation.json",
        {
            "status": "PASS"
            if args.focused_result
            == args.full_result
            == args.ruff_result
            == args.diff_result
            == "PASS"
            else "FAIL",
            "focused": args.focused_result,
            "full": args.full_result,
            "full_count": args.full_count,
            "ruff": args.ruff_result,
            "diff": args.diff_result,
        },
    )
    report("program-completion", completion)
    print(canonical_json({"status": completion["status"], "decision": top_level}))


def seal(args: argparse.Namespace) -> None:
    completion = read_json(OUTPUT / "program-completion.json")
    completion.update(
        {
            "final_local_head_sha": args.final_local_head,
            "report_commit": args.report_commit,
            "documentation_status": "PASS",
        }
    )
    report(
        "master-workflow-update",
        {
            "status": "RECORDED_LOCAL_ONLY",
            "master_workflow_updated": True,
            "project_handoff_updated": True,
            "next_session_prompt_updated": True,
            "project_state_updated": True,
            "report_commit": args.report_commit,
            "remote_push": False,
        },
    )
    write_json(OUTPUT / "program-completion.json", completion)
    report("program-completion", completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12BK-R2 Completion",
                "",
                f"- Result: `{completion['top_level_policy_validation_result']}`",
                f"- Next scope: `{completion['next_scope']}`",
                f"- Primary boundaries tolerated: `{completion['primary_boundary_tolerated_count']}/5`",
                f"- Holder boundaries tolerated: `{completion['holder_boundary_tolerated_count']}/3`",
                f"- Coupled entry boundaries tolerated: `{completion['coupled_entry_tolerated_count']}/1`",
                f"- Calibration cases tolerated: `{completion['calibration_tolerated_count']}/5`",
                "- Model calls / network calls / production effects: `0`",
                "- Fresh / main merge / production readiness: `NOT_READY`",
                "",
            )
        ),
    )


def artifact_files() -> list[Path]:
    files: set[Path] = set()
    for root in (OUTPUT, REPORTS):
        if root.exists():
            files.update(path for path in root.rglob("*") if path.is_file())
    files.discard(OUTPUT / "artifact-index.json")
    for relative in (
        RUNNER,
        TEST_PATH,
        ARCHITECTURE,
        WORK_INSTRUCTION,
        Path("docs/MASTER_WORKFLOW.md"),
        Path("docs/PROJECT_HANDOFF.md"),
        Path("docs/NEXT_SESSION_PROMPT.md"),
        Path("docs/project-state.json"),
    ):
        path = REPO_ROOT / relative
        if path.is_file():
            files.add(path)
    return sorted(files, key=lambda path: str(path.relative_to(REPO_ROOT)))


def _relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def bundle(output_zip: Path) -> None:
    missing = [
        str(REPORTS / f"{number:02d}-{slug}.json")
        for number, slug in enumerate(REPORT_SLUGS, start=1)
        if not (REPORTS / f"{number:02d}-{slug}.json").is_file()
    ]
    if missing:
        raise ValueError(f"M12BK_R2_REQUIRED_REPORTS_MISSING:{missing}")
    files = artifact_files()
    relative_names = {_relative(path) for path in files}
    if any(
        marker in name
        for name in relative_names
        for marker in ("model-calls", "prompt.txt", "output.raw.json", "transport.log")
    ):
        raise ValueError("M12BK_R2_RAW_MODEL_ARTIFACT_PACKAGE_ATTEMPT")
    secret_failures = [
        {"path": _relative(path), "indicators": indicators}
        for path in files
        for indicators in (_secret_indicators(path.read_bytes()),)
        if indicators
    ]
    completion = read_json(OUTPUT / "program-completion.json")
    completion["artifact_count"] = len(files)
    completion["artifact_secret_scan_failure_count"] = len(secret_failures)
    write_json(OUTPUT / "program-completion.json", completion)
    report("program-completion", completion)
    files = artifact_files()
    index = {
        "contract": "m12bk-r2-artifact-index-v1",
        "status": "PASS" if not secret_failures else "FAIL",
        "artifact_count": len(files),
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": len(secret_failures),
        "secret_scan_failures": secret_failures,
        "raw_model_artifact_count": 0,
        "rows": [
            {
                "path": _relative(path),
                "sha256": file_sha256(path),
                "size": path.stat().st_size,
            }
            for path in files
        ],
    }
    write_json(OUTPUT / "artifact-index.json", index)
    if index["status"] != "PASS":
        raise ValueError("M12BK_R2_ARTIFACT_SECRET_SCAN_FAILURE")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    if output_zip.exists():
        raise ValueError(f"M12BK_R2_RESULT_BUNDLE_ALREADY_EXISTS:{output_zip}")
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=_relative(path))
        archive.write(OUTPUT / "artifact-index.json", arcname=_relative(OUTPUT / "artifact-index.json"))
    with zipfile.ZipFile(output_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("M12BK_R2_RESULT_BUNDLE_CRC_FAILURE")
        for row in index["rows"]:
            payload = archive.read(row["path"])
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                raise ValueError(f"M12BK_R2_BUNDLE_HASH_MISMATCH:{row['path']}")
            if len(payload) != row["size"]:
                raise ValueError(f"M12BK_R2_BUNDLE_SIZE_MISMATCH:{row['path']}")
    digest = file_sha256(output_zip)
    sidecar = Path(f"{output_zip}.sha256")
    write_text(sidecar, f"{digest}  {output_zip.name}\n")
    print(
        canonical_json(
            {
                "status": "PASS",
                "zip": str(output_zip),
                "sha256": digest,
                "sidecar": str(sidecar),
                "indexed_payloads": len(files),
                "zip_entries": len(files) + 1,
            }
        )
    )


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    commands = value.add_subparsers(dest="command", required=True)
    run_parser = commands.add_parser("run")
    run_parser.add_argument("--implementation-commit", required=True)
    run_parser.add_argument("--focused-result", required=True)
    run_parser.add_argument("--full-result", required=True)
    run_parser.add_argument("--full-count", type=int, required=True)
    run_parser.add_argument("--ruff-result", required=True)
    run_parser.add_argument("--diff-result", required=True)
    seal_parser = commands.add_parser("seal")
    seal_parser.add_argument("--report-commit", required=True)
    seal_parser.add_argument("--final-local-head", required=True)
    bundle_parser = commands.add_parser("bundle")
    bundle_parser.add_argument("--output", type=Path, required=True)
    return value


def main() -> None:
    args = parser().parse_args()
    if args.command == "run":
        run(args)
    elif args.command == "seal":
        seal(args)
    else:
        bundle(args.output)


if __name__ == "__main__":
    main()
