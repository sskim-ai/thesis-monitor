from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from app.jobs import accepted_decision_v2_runtime as runtime
from app.services.accepted_decision_v2_runtime_service import (
    ARTIFACT_CONTRACT_V2,
    OUTPUT_CONTRACT_V2,
    REASONING_EFFORT,
    REASONING_MODEL,
    STAGE2_MATURITY_AS_OF_AGGREGATION,
    STAGE2_MATURITY_AS_OF_SEMANTICS,
    STAGE2_MATURITY_PROVENANCE_MATERIALIZATION_CONTRACT,
    STAGE2_MODEL_OUTPUT_CONTRACT,
    accepted_v2_fundamental_core_output_schema,
    accepted_v2_fundamental_core_prompt,
    accepted_v2_fundamental_core_ref_catalog_manifest,
    accepted_v2_stage2_output_schema,
    accepted_v2_stage2_ref_catalog_manifest,
)
from scripts import v2_production_cutover_preflight as preflight


REPO = Path(__file__).resolve().parents[1]
REQUIRED_BASE = "1e0d81695ce0982827a35a58b5123dfb86e066cc"
INSTRUCTION_COMMIT = "fa0b645c"
INSTRUCTION_PATH = "docs/work-instructions/20260917-m12ch-frozen-contract-new-full22-reproof.md"
INSTRUCTION_FILE_SHA256 = "7f261c6263f390e79234020778c4ec454b5ec635d023bed63c319ae86a797a8a"
EXPECTED_PACKETS = {
    "us": {
        "whole_file_sha256": ("2c01a21c887ca41512798199387120e8ded5afd2888f5b78a9c54ea59e975228"),
        "canonical_sha256": ("78f9c31b351e36e1811e77b286b480c9bd85eed1157234861fe7f6855dbc194a"),
        "packet_id": "2026-09-15-us-run-61-b8b5976b9991",
        "claim_id": "preflight-us-20260902",
        "assessment_date": "2026-09-15",
        "subjects": (
            "CORZ",
            "CPNG",
            "CRCL",
            "GOOGL",
            "HUT",
            "IBM",
            "MU",
            "RXRX",
            "SKHY",
            "SNDK",
            "TSLA",
            "TSM",
            "WRD",
            "WULF",
        ),
    },
    "kr": {
        "whole_file_sha256": ("819af90aa5ff159ee77ef2be69fc115ad169631acc9cfcc101081bef4318b597"),
        "canonical_sha256": ("b18bf36d4b03091079d5c607edf0f6f23076223ae333ef2f27eaec9437549663"),
        "packet_id": "2026-09-15-kr-run-62-edf2b6a8751b",
        "claim_id": "preflight-kr-20260902",
        "assessment_date": "2026-09-15",
        "subjects": (
            "000660",
            "003690",
            "005490",
            "005930",
            "010120",
            "012450",
            "047810",
            "086280",
        ),
    },
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return sha256_bytes(payload.encode("utf-8"))


def serialized_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str) + "\n"
    ).encode("utf-8")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_json_object:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(serialized_json(value))
    temporary.replace(path)


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def git_text(*args: str) -> str:
    return subprocess.run(
        ("git", *args),
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def git_bytes(*args: str) -> bytes:
    return subprocess.run(
        ("git", *args),
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout


def junit_summary(path: Path) -> dict[str, int | str]:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    totals = {
        key: sum(int(suite.attrib.get(key, "0")) for suite in suites)
        for key in ("tests", "failures", "errors", "skipped")
    }
    return {"path": str(path), **totals}


def deterministic_snapshot_audit(
    *,
    market: str,
    source: Path,
    destination: Path,
    expected: dict[str, Any],
) -> dict[str, object]:
    payload = read_json(source)
    messages = payload.get("messages")
    require(isinstance(messages, list), f"{market}:deterministic_messages_missing")
    tickers = tuple(str(row.get("ticker") or "") for row in messages if isinstance(row, dict))
    require(len(tickers) == len(messages), f"{market}:deterministic_row_invalid")
    require(tickers == expected["subjects"], f"{market}:deterministic_subject_drift")
    require(
        payload.get("packet_id") == expected["packet_id"],
        f"{market}:deterministic_packet_id_drift",
    )
    for row in messages:
        assert isinstance(row, dict)
        body = row.get("payload")
        require(isinstance(body, dict), f"{market}:deterministic_payload_missing")
        require(bool(str(body.get("text") or "")), f"{market}:deterministic_text_empty")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return {
        "market": market,
        "source_path": str(source),
        "bundled_path": str(destination),
        "whole_file_sha256": sha256_file(destination),
        "packet_id": payload["packet_id"],
        "subject_count": len(messages),
        "subjects": list(tickers),
        "status": "PASS",
    }


async def run(args: argparse.Namespace) -> None:
    output = args.output_root.resolve()
    require(not output.exists(), "premodel_output_already_exists")
    output.mkdir(parents=True)

    package_root = args.package_root.resolve()
    package_result = json.loads(
        subprocess.run(
            ("python3", str(package_root / "verify_package.py")),
            cwd=package_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    )
    require(package_result.get("status") == "PASS", "package_verification_failed")
    write_json(output / "01-package-integrity.json", package_result)

    head = git_text("rev-parse", "HEAD")
    require(head == args.expected_head, "harness_head_drift")
    require(not git_text("status", "--porcelain"), "worktree_not_clean")
    require(
        subprocess.run(
            ("git", "merge-base", "--is-ancestor", REQUIRED_BASE, head),
            cwd=REPO,
            check=False,
        ).returncode
        == 0,
        "required_base_not_ancestor",
    )
    instruction_full = git_text("rev-parse", INSTRUCTION_COMMIT)
    require(
        subprocess.run(
            ("git", "merge-base", "--is-ancestor", instruction_full, head),
            cwd=REPO,
            check=False,
        ).returncode
        == 0,
        "instruction_commit_not_ancestor",
    )
    require(
        sha256_file(REPO / INSTRUCTION_PATH) == INSTRUCTION_FILE_SHA256,
        "instruction_file_sha_drift",
    )

    runtime_paths = git_text(
        "ls-tree",
        "-r",
        "--name-only",
        REQUIRED_BASE,
        "--",
        "app",
        "pyproject.toml",
        "uv.lock",
        "scripts/v2_production_cutover_preflight.py",
    ).splitlines()
    runtime_rows: list[dict[str, object]] = []
    drift: list[str] = []
    for relative in runtime_paths:
        current = (REPO / relative).read_bytes()
        frozen = git_bytes("show", f"{REQUIRED_BASE}:{relative}")
        if current != frozen:
            drift.append(relative)
        runtime_rows.append(
            {"path": relative, "sha256": sha256_bytes(current), "size": len(current)}
        )
    require(not drift, "runtime_source_drift:" + ",".join(drift))
    runtime_tree_sha = canonical_sha256(runtime_rows)
    proof_paths = (
        REPO / "scripts/m12ch_premodel_audit.py",
        REPO / "scripts/m12ch_full22_reproof.py",
        REPO / "scripts/m12ch_build_report.py",
    )
    proof_rows = [
        {"path": path.relative_to(REPO).as_posix(), "sha256": sha256_file(path)}
        for path in proof_paths
    ]
    write_json(
        output / "02-repository-runtime-freeze.json",
        {
            "status": "PASS",
            "required_runtime_base": REQUIRED_BASE,
            "instruction_commit": instruction_full,
            "harness_freeze_commit": head,
            "runtime_source_drift_count": len(drift),
            "runtime_tree_file_count": len(runtime_rows),
            "runtime_tree_sha256": runtime_tree_sha,
            "runtime_files": runtime_rows,
            "proof_harness_files": proof_rows,
        },
    )

    require(REASONING_MODEL == "gpt-5.6-sol", "model_contract_drift")
    require(REASONING_EFFORT == "xhigh", "reasoning_effort_contract_drift")
    require(
        STAGE2_MODEL_OUTPUT_CONTRACT == "v2-accepted-stage2-model-output-v2",
        "raw_stage2_contract_drift",
    )
    require(
        STAGE2_MATURITY_PROVENANCE_MATERIALIZATION_CONTRACT
        == "stage2-maturity-as-of-deterministic-v2",
        "normalization_contract_drift",
    )
    require(
        OUTPUT_CONTRACT_V2 == "v2-accepted-production-output-v2",
        "accepted_output_contract_drift",
    )
    require(
        ARTIFACT_CONTRACT_V2 == "v2-accepted-production-artifact-v2",
        "artifact_contract_drift",
    )
    require(
        STAGE2_MATURITY_AS_OF_SEMANTICS == "LATEST_KNOWN_CONCRETE_SAME_ROW_PROVENANCE_DATE",
        "maturity_semantics_drift",
    )
    require(
        STAGE2_MATURITY_AS_OF_AGGREGATION == "MAX_CONCRETE_OWNED_DATES",
        "maturity_aggregation_drift",
    )
    codex_bin = runtime._signed_in_codex_bin()
    require(Path(codex_bin).is_file(), "signed_in_codex_cli_missing")
    require(os.access(codex_bin, os.X_OK), "signed_in_codex_cli_not_executable")

    old_manifest = read_json(args.m12ce_root / "premodel/fundamental-core-freeze-manifest.json")
    old_rows = {(str(row["market"]), int(row["batch"])): row for row in old_manifest["batches"]}
    model_rows: list[dict[str, object]] = []
    call_plan: list[dict[str, object]] = []
    ordinal = 0
    model_facing_mismatches: list[dict[str, object]] = []
    historical_unbound_schema_differences: list[dict[str, object]] = []
    for market in ("us", "kr"):
        expected = EXPECTED_PACKETS[market]
        packet_path = package_root / f"inputs/frozen-packets/{market}.json"
        require(
            sha256_file(packet_path) == expected["whole_file_sha256"],
            f"{market}:packet_whole_file_sha_drift",
        )
        packet = read_json(packet_path)
        require(
            packet.get("packet_id") == expected["packet_id"],
            f"{market}:packet_id_drift",
        )
        require(
            packet.get("assessment_date") == expected["assessment_date"],
            f"{market}:assessment_date_drift",
        )
        context = await preflight._context(packet_path, claim_id=expected["claim_id"])
        require(
            context.source_packet_sha256 == expected["canonical_sha256"],
            f"{market}:canonical_packet_sha_drift",
        )
        require(
            tuple(context.selected_subjects) == expected["subjects"],
            f"{market}:subject_order_drift",
        )
        for index in range(0, len(context.selected_subjects), runtime.V2_REASONING_BATCH_SIZE):
            subjects = tuple(
                context.selected_subjects[index : index + runtime.V2_REASONING_BATCH_SIZE]
            )
            batch = index // runtime.V2_REASONING_BATCH_SIZE + 1
            prompt = accepted_v2_fundamental_core_prompt(context, subjects=subjects)
            prompt_sha = sha256_bytes((prompt.rstrip() + "\n").encode("utf-8"))
            schema = accepted_v2_fundamental_core_output_schema(context, subjects=subjects)
            catalog = accepted_v2_fundamental_core_ref_catalog_manifest(context, subjects=subjects)
            unbound_schema = accepted_v2_stage2_output_schema(context, subjects=subjects)
            maturity = unbound_schema["$defs"]["DriverEvidenceMaturity"]
            require("as_of" not in maturity["properties"], "stage2_schema_exposes_as_of")
            require(
                "provenance_status" not in maturity["properties"],
                "stage2_schema_exposes_provenance_status",
            )
            require(
                maturity.get("additionalProperties") is False,
                "stage2_schema_not_strict",
            )
            identity = {
                key: schema["properties"][key]["const"]
                for key in (
                    "contract",
                    "packet_id",
                    "claim_id",
                    "market",
                    "assessment_date",
                )
            }
            row = {
                "market": market,
                "batch": batch,
                "subjects": list(subjects),
                "expected_subject_count": len(subjects),
                "fundamental_core_prompt_sha256": prompt_sha,
                "fundamental_core_schema_semantic_sha256": canonical_sha256(schema),
                "fundamental_core_schema_size_bytes": len(serialized_json(schema)),
                "fundamental_core_ref_catalog_hash": catalog["ref_catalog_hash"],
                "fundamental_core_ref_catalog_count": catalog["ref_catalog_count"],
                "ticker_domain_hash": canonical_sha256(subjects),
                "identity_contract_hash": canonical_sha256(
                    {
                        "contract": "fundamental-core-batch-identity-v1",
                        "identity": identity,
                        "expected_subject_count": len(subjects),
                        "expected_tickers": list(subjects),
                    }
                ),
                "stage2_unbound_schema_semantic_sha256": canonical_sha256(unbound_schema),
                "stage2_unbound_ref_catalog_hash": (
                    accepted_v2_stage2_ref_catalog_manifest(context, subjects=subjects)[
                        "ref_catalog_hash"
                    ]
                ),
                "stage2_exact_freeze": "DEFERRED_UNTIL_NEW_FROZEN_CORE_EXISTS",
            }
            expected_row = old_rows[(market, batch)]
            compared_fields = (
                "subjects",
                "expected_subject_count",
                "fundamental_core_prompt_sha256",
                "fundamental_core_schema_semantic_sha256",
                "fundamental_core_schema_size_bytes",
                "fundamental_core_ref_catalog_hash",
                "fundamental_core_ref_catalog_count",
                "ticker_domain_hash",
                "identity_contract_hash",
                "stage2_unbound_ref_catalog_hash",
            )
            for field in compared_fields:
                if row[field] != expected_row[field]:
                    model_facing_mismatches.append(
                        {
                            "market": market,
                            "batch": batch,
                            "field": field,
                            "expected": expected_row[field],
                            "observed": row[field],
                        }
                    )
            if (
                row["stage2_unbound_schema_semantic_sha256"]
                != expected_row["stage2_unbound_schema_semantic_sha256"]
            ):
                historical_unbound_schema_differences.append(
                    {
                        "market": market,
                        "batch": batch,
                        "historical_m12ce": expected_row["stage2_unbound_schema_semantic_sha256"],
                        "current_frozen_base": row["stage2_unbound_schema_semantic_sha256"],
                        "classification": ("NON_MODEL_VISIBLE_DEFERRED_CORE_BINDING_CONTROL"),
                    }
                )
            model_rows.append(row)
        for stage in ("FUNDAMENTAL_CORE", "PRICE_TIMING"):
            for index in range(0, len(context.selected_subjects), runtime.V2_REASONING_BATCH_SIZE):
                ordinal += 1
                call_plan.append(
                    {
                        "ordinal": ordinal,
                        "market": market,
                        "stage": stage,
                        "batch": index // runtime.V2_REASONING_BATCH_SIZE + 1,
                        "subjects": list(
                            context.selected_subjects[
                                index : index + runtime.V2_REASONING_BATCH_SIZE
                            ]
                        ),
                    }
                )
    require(ordinal == 16, "planned_call_count_drift")
    require(
        len(historical_unbound_schema_differences) == len(model_rows),
        "historical_unbound_schema_control_count_drift",
    )
    write_json(
        output / "fundamental-core-freeze-manifest.json",
        {
            "contract": "m12ch-model-facing-freeze-v1",
            "status": "PASS" if not model_facing_mismatches else "FAIL",
            "reasoning_model": REASONING_MODEL,
            "reasoning_effort": REASONING_EFFORT,
            "planned_model_call_count": 16,
            "batch_count": len(model_rows),
            "model_facing_hash_mismatch_count": len(model_facing_mismatches),
            "model_facing_hash_mismatches": model_facing_mismatches,
            "historical_unbound_schema_difference_count": len(
                historical_unbound_schema_differences
            ),
            "historical_unbound_schema_differences": (historical_unbound_schema_differences),
            "stage2_actual_payload_policy": (
                "FREEZE_BOUND_PROMPT_SCHEMA_AND_CATALOG_AFTER_NEW_CORE"
            ),
            "batches": model_rows,
            "call_plan": call_plan,
        },
    )
    require(not model_facing_mismatches, "model_facing_contract_drift")

    deterministic_rows = [
        deterministic_snapshot_audit(
            market=market,
            source=getattr(args, f"{market}_deterministic").resolve(),
            destination=output / f"deterministic/{market}-deterministic.json",
            expected=EXPECTED_PACKETS[market],
        )
        for market in ("us", "kr")
    ]
    deterministic_builder = None
    if args.deterministic_builder is not None:
        builder = args.deterministic_builder.resolve()
        require(builder.is_file(), "deterministic_builder_missing")
        destination = output / "deterministic/build_deterministic_payloads.py"
        shutil.copy2(builder, destination)
        deterministic_builder = {
            "source_path": str(builder),
            "bundled_path": str(destination),
            "sha256": sha256_file(destination),
        }
    write_json(
        output / "03-input-and-deterministic-dependency-freeze.json",
        {
            "status": "PASS",
            "assessment_date": "2026-09-15",
            "fresh_generation_not_current_market_collection": True,
            "packet_inputs": {
                market: {
                    **EXPECTED_PACKETS[market],
                    "subjects": list(EXPECTED_PACKETS[market]["subjects"]),
                }
                for market in ("us", "kr")
            },
            "deterministic_snapshots": deterministic_rows,
            "deterministic_builder": deterministic_builder,
        },
    )

    control = read_json(args.independent_control.resolve())
    require(control.get("status") == "PASS", "independent_control_failed")
    shutil.copy2(
        args.independent_control.resolve(),
        output / "04-independent-finalizer-reader-control.json",
    )
    junit = junit_summary(args.focused_junit.resolve())
    require(junit["tests"] > 0, "focused_tests_empty")
    require(
        junit["failures"] == 0 and junit["errors"] == 0,
        "focused_tests_failed",
    )
    write_json(output / "05-focused-regression.json", {"status": "PASS", **junit})

    write_json(
        output / "premodel-audit.json",
        {
            "contract": "m12ch-premodel-gate-v1",
            "status": "PASS",
            "package_integrity": "PASS",
            "repository_runtime_freeze": "PASS",
            "runtime_tree_sha256": runtime_tree_sha,
            "instruction_commit": instruction_full,
            "harness_freeze_commit": head,
            "source_packet_count": 2,
            "subject_count": 22,
            "planned_model_call_count": 16,
            "model_facing_hash_mismatch_count": 0,
            "historical_unbound_schema_difference_count": len(
                historical_unbound_schema_differences
            ),
            "stage2_actual_payload_freeze": ("AFTER_NEW_CORE_BEFORE_EACH_STAGE2_CALL"),
            "independent_finalizer_reader_control": "PASS",
            "focused_regression": "PASS",
            "signed_in_codex_cli_configured": True,
            "signed_in_codex_cli_path_sha256": sha256_bytes(codex_bin.encode()),
            "reasoning_model": REASONING_MODEL,
            "reasoning_effort": REASONING_EFFORT,
            "formal_generation_id": "DEFERRED_TO_FORMAL_START",
            "external_model_calls": 0,
            "production_mutations": 0,
            "production_sends": 0,
        },
    )
    print(json.dumps(read_json(output / "premodel-audit.json"), indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--m12ce-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--independent-control", type=Path, required=True)
    parser.add_argument("--focused-junit", type=Path, required=True)
    parser.add_argument("--us-deterministic", type=Path, required=True)
    parser.add_argument("--kr-deterministic", type=Path, required=True)
    parser.add_argument("--deterministic-builder", type=Path)
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
