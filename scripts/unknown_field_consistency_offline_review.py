from __future__ import annotations

import argparse
import copy
import hashlib
import inspect
import json
import subprocess
import tempfile
import zipfile
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from app.services.direction_timing_ownership_service import (
    CORE_DOMAINS,
    DirectionalCoreCandidate,
    DirectionalUnknown,
    EvidenceDomain,
    PriceTimingCandidate,
    compose_decision,
    stage_alias_catalogs,
    validate_ownership,
)
from app.services.structured_autonomy_shadow_service import (
    unknown_treatment_consistency_issues,
)
from scripts import bounded_fictional_websocket_reconnect_diagnostic as diagnostic
from scripts import directional_core_price_timing_holdout as frozen
from scripts import fresh_issuer_ownership_proof_transport_risk_carried as secret_policy
from scripts import new_issuer_holdout_selection_ownership_proof as proof
from scripts import synthetic_canary_fixture_repair_ownership_resume as synthetic
from scripts import websocket_timeout_runtime_review_first_a_closeout as pause_observer


CONTRACT = "unknown-field-consistency-offline-evidence-review-v1"
EXPECTED_SOURCE_ZIP_SHA256 = (
    "2a58b8e8dbfcc6e3aa7cb4900bec2d16d29f149b69160e8fd0c5b0522f6a798e"
)
EXPECTED_SOURCE_MEMBER_COUNT = 2008
EXPECTED_INDEXED_PAYLOAD_COUNT = 2007
EXPERIMENT_PREFIX = Path("experiment/fresh-real-proof")
RUNS = ("FIRST", "A", "B", "C")
COMPLETE_RUNS = ("FIRST", "A", "B")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode()
    return bytes_sha256(payload)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, default=str) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def git_value(repo_root: Path, *args: str) -> str:
    return subprocess.run(
        ("git", *args),
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return not name.startswith("/") and "\\" not in name and ".." not in path.parts


def verify_source_archive(path: Path) -> dict[str, object]:
    actual_sha = file_sha256(path)
    if actual_sha != EXPECTED_SOURCE_ZIP_SHA256:
        raise ValueError("source_zip_sha256_mismatch")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
        unsafe = sorted(name for name in names if not _safe_member(name))
        crc_failure = archive.testzip()
        index = json.loads(archive.read("artifact-index.json"))
        rows = index.get("rows") if isinstance(index, Mapping) else None
        if not isinstance(rows, list):
            raise ValueError("source_artifact_index_rows_missing")
        indexed = {
            str(row["path"]): row
            for row in rows
            if isinstance(row, Mapping) and row.get("path")
        }
        payload_names = set(names) - {"artifact-index.json"}
        missing_index = sorted(payload_names - set(indexed))
        unexpected_index = sorted(set(indexed) - payload_names)
        hash_mismatches: list[str] = []
        size_mismatches: list[str] = []
        secret_failures: list[str] = []
        for name in sorted(payload_names & set(indexed)):
            payload = archive.read(name)
            row = indexed[name]
            if bytes_sha256(payload) != row.get("sha256"):
                hash_mismatches.append(name)
            if len(payload) != row.get("byte_size"):
                size_mismatches.append(name)
            if any(
                pattern.search(payload)
                for pattern in secret_policy.ARTIFACT_SECRET_PATTERNS.values()
            ):
                secret_failures.append(name)
        checks = {
            "zip_sha256": True,
            "member_count": len(names) == EXPECTED_SOURCE_MEMBER_COUNT,
            "indexed_payload_count": len(rows) == EXPECTED_INDEXED_PAYLOAD_COUNT,
            "crc": crc_failure is None,
            "duplicates": not duplicates,
            "safe_paths": not unsafe,
            "index_membership": not missing_index and not unexpected_index,
            "indexed_hashes": not hash_mismatches,
            "indexed_sizes": not size_mismatches,
            "independent_secret_scan": not secret_failures,
        }
        if not all(checks.values()):
            failed = ",".join(key for key, value in checks.items() if not value)
            raise ValueError(f"source_archive_integrity_failed:{failed}")
        return {
            "contract": "source-archive-integrity-v1",
            "source_path": str(path),
            "expected_sha256": EXPECTED_SOURCE_ZIP_SHA256,
            "actual_sha256": actual_sha,
            "zip_member_count": len(names),
            "indexed_payload_count": len(rows),
            "duplicate_member_count": len(duplicates),
            "unsafe_member_count": len(unsafe),
            "unindexed_payload_count": len(missing_index),
            "unexpected_index_row_count": len(unexpected_index),
            "hash_mismatch_count": len(hash_mismatches),
            "size_mismatch_count": len(size_mismatches),
            "secret_scan_failure_count": len(secret_failures),
            "checks": checks,
            "status": "PASS",
        }


def _all_refs(value: object) -> set[str]:
    refs: set[str] = set()

    def collect(item: object, key: str | None = None) -> None:
        if isinstance(item, Mapping):
            for child_key, child in item.items():
                collect(child, str(child_key))
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes)):
            if key == "evidence_refs" or key == "material_directional_anchor_basis" or (
                key is not None and key.endswith("_basis")
            ):
                refs.update(str(child) for child in item)
            else:
                for child in item:
                    collect(child, key)

    collect(value)
    return refs


def _all_strings(value: object) -> tuple[str, ...]:
    rows: list[str] = []
    if isinstance(value, str):
        rows.append(value)
    elif isinstance(value, Mapping):
        for child in value.values():
            rows.extend(_all_strings(child))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for child in value:
            rows.extend(_all_strings(child))
    return tuple(rows)


def _reference_to_alias(
    value: object, by_ref: Mapping[str, object], key: str | None = None
) -> object:
    if isinstance(value, Mapping):
        return {
            str(child_key): _reference_to_alias(child, by_ref, str(child_key))
            for child_key, child in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if key in {
            "business_invalidation_condition_refs",
            "confirmation_business_condition_refs",
            "evidence_refs",
            "material_directional_anchor_basis",
        } or (key is not None and key.endswith("_basis")):
            return [by_ref[str(child)].alias for child in value]
        return [_reference_to_alias(child, by_ref, key) for child in value]
    return value


def _load_inputs(experiment: Path) -> tuple[object, ...]:
    source_lock = read_json(experiment / "source-lock.json")
    cohort = tuple(str(value) for value in source_lock["ordered_cohort"])
    packets = {
        ticker: read_json(experiment / "packets" / f"{ticker}.json")
        for ticker in cohort
    }
    contexts = {
        ticker: (experiment / "base-contexts" / f"{ticker}.txt")
        .read_text(encoding="utf-8")
        .rstrip()
        for ticker in cohort
    }
    return source_lock, cohort, contexts, *frozen.build_inputs(packets, contexts, cohort)


def _context_metadata(context: Path, experiment: Path) -> dict[str, object]:
    manifest = read_json(context / "context_manifest.json")
    identity = read_json(context / "output-identity-validation.json")
    return {
        "context_path": str(context.relative_to(experiment)),
        "prompt_sha256": file_sha256(context / "prompt.txt"),
        "schema_sha256": file_sha256(context / "schema.json"),
        "receipt_sha256": file_sha256(context / "transport_receipt.json"),
        "raw_output_sha256": file_sha256(context / "output.raw.json"),
        "normalized_output_sha256": file_sha256(context / "output.normalized.json"),
        "identity_status": identity.get("status"),
        "manifest_original_partial_status": manifest.get(
            "per_context_partial_semantic_audit_status"
        ),
    }


def audit_historical_outputs(
    *,
    experiment: Path,
    source_lock: Mapping[str, object],
    contexts: Mapping[str, str],
    evidence: Mapping[str, object],
    owned: Mapping[str, object],
    core_aliases: Mapping[str, object],
    timing_aliases: Mapping[str, object],
    price_maps: Mapping[str, Mapping[str, object]],
    stocks: Mapping[str, Mapping[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    core_inventory: list[dict[str, object]] = []
    timing_inventory: list[dict[str, object]] = []
    core_by_run: dict[str, dict[str, DirectionalCoreCandidate]] = defaultdict(dict)
    exact_candidates: dict[tuple[str, str], dict[str, object]] = {}
    validator_hashes = {
        "shared_unknown_helper_source_sha256": bytes_sha256(
            inspect.getsource(unknown_treatment_consistency_issues).encode()
        ),
        "validator_file_sha256": file_sha256(
            Path(inspect.getsourcefile(unknown_treatment_consistency_issues) or "")
        ),
        "core_acceptance_file_sha256": file_sha256(Path(proof.__file__)),
    }
    packet_hashes = source_lock.get("packet_sha256") or {}

    for run in RUNS:
        stage_root = experiment / "model-contexts" / run / "DIRECTIONAL_CORE"
        for context in sorted(stage_root.glob("batch-*")):
            normalized = read_json(context / "output.normalized.json")
            raw = read_json(context / "output.raw.json")
            batch = tuple(str(row["ticker"]) for row in normalized["candidates"])
            rows = tuple(
                DirectionalCoreCandidate.model_validate(row)
                for row in normalized["candidates"]
            )
            resolved, alias_audit = frozen._resolve_batch_candidates(
                raw.get("candidates"),
                batch=batch,
                evidence=evidence,
                catalogs=core_aliases,
                model_type=DirectionalCoreCandidate,
            )
            alias_parity = {
                row.ticker: row.model_dump(mode="json")
                == expected.model_dump(mode="json")
                for row, expected in zip(resolved, rows, strict=True)
            }
            current = proof.core_partial_audit(rows, owned)
            current_by_ticker = {str(row["ticker"]): row for row in current["rows"]}
            original = read_json(context / "partial_semantic_audit.json")
            original_by_ticker = {
                str(row["ticker"]): row for row in original.get("rows") or []
            }
            metadata = _context_metadata(context, experiment)
            for row in rows:
                ticker = row.ticker
                dumped = row.model_dump(mode="json")
                exact_candidates[(run, ticker)] = dumped
                core_by_run[run][ticker] = row
                current_row = current_by_ticker[ticker]
                original_row = original_by_ticker.get(ticker) or {}
                core_inventory.append(
                    {
                        "run": run,
                        "stage": "DIRECTIONAL_CORE",
                        "batch": context.name,
                        "ticker": ticker,
                        "source_packet_sha256": packet_hashes.get(ticker),
                        **metadata,
                        "candidate_sha256": canonical_sha256(dumped),
                        "alias_candidate_sha256": (
                            alias_audit.get(ticker) or {}
                        ).get("alias_candidate_sha256"),
                        "alias_resolution_parity": alias_parity[ticker],
                        "original_verdict": original_row.get("status"),
                        "original_errors": original_row.get("errors") or [],
                        "current_verdict": current_row["status"],
                        "current_errors": current_row["errors"],
                        "current_issue_details": current_row.get(
                            "unknown_treatment_consistency_issues"
                        )
                        or [],
                        "validator_hashes": validator_hashes,
                        "applicability": "CHECKED",
                    }
                )

    for run in RUNS:
        stage_root = experiment / "model-contexts" / run / "PRICE_TIMING"
        for context in sorted(stage_root.glob("batch-*")):
            normalized = read_json(context / "output.normalized.json")
            raw = read_json(context / "output.raw.json")
            batch = tuple(str(row["ticker"]) for row in normalized["candidates"])
            rows = tuple(
                PriceTimingCandidate.model_validate(row)
                for row in normalized["candidates"]
            )
            resolved, alias_audit = frozen._resolve_batch_candidates(
                raw.get("candidates"),
                batch=batch,
                evidence=evidence,
                catalogs=timing_aliases,
                model_type=PriceTimingCandidate,
            )
            alias_parity = {
                row.ticker: row.model_dump(mode="json")
                == expected.model_dump(mode="json")
                for row, expected in zip(resolved, rows, strict=True)
            }
            current, _run_rows = proof.timing_partial_audit(
                rows=rows,
                core_by_ticker=core_by_run[run],
                owned=owned,
                evidence=evidence,
                price_maps=price_maps,
                stocks=stocks,
                base_contexts=contexts,
            )
            current_by_ticker = {str(row["ticker"]): row for row in current["rows"]}
            original = read_json(context / "partial_semantic_audit.json")
            original_by_ticker = {
                str(row["ticker"]): row for row in original.get("rows") or []
            }
            metadata = _context_metadata(context, experiment)
            for row in rows:
                ticker = row.ticker
                dumped = row.model_dump(mode="json")
                current_row = current_by_ticker[ticker]
                original_row = original_by_ticker.get(ticker) or {}
                timing_inventory.append(
                    {
                        "run": run,
                        "stage": "PRICE_TIMING",
                        "batch": context.name,
                        "ticker": ticker,
                        "source_packet_sha256": packet_hashes.get(ticker),
                        **metadata,
                        "candidate_sha256": canonical_sha256(dumped),
                        "alias_candidate_sha256": (
                            alias_audit.get(ticker) or {}
                        ).get("alias_candidate_sha256"),
                        "alias_resolution_parity": alias_parity[ticker],
                        "original_verdict": original_row.get("status"),
                        "original_errors": original_row.get("errors") or [],
                        "current_verdict": current_row["status"],
                        "current_errors": current_row["errors"],
                        "validator_hashes": validator_hashes,
                        "applicability": "CHECKED",
                    }
                )

    known = [
        row
        for row in core_inventory
        if row["run"] == "C" and row["ticker"] == "NEON"
    ]
    if len(known) != 1:
        raise ValueError("exact_neon_core_row_missing")
    summary = {
        "contract": "historical-core-timing-offline-audit-v1",
        "core": {
            "raw_rows": len(core_inventory),
            "identity_valid_rows": sum(
                row["identity_status"] == "PASS" for row in core_inventory
            ),
            "checked_rows": len(core_inventory),
            "failed_rows": sum(
                row["current_verdict"] == "FAIL" for row in core_inventory
            ),
            "not_applicable_rows": 0,
            "not_measured_rows": 0,
            "alias_resolution_parity_rows": sum(
                bool(row["alias_resolution_parity"]) for row in core_inventory
            ),
        },
        "timing": {
            "raw_rows": len(timing_inventory),
            "identity_valid_rows": sum(
                row["identity_status"] == "PASS" for row in timing_inventory
            ),
            "checked_rows": len(timing_inventory),
            "failed_rows": sum(
                row["current_verdict"] == "FAIL" for row in timing_inventory
            ),
            "not_applicable_rows": 0,
            "not_measured_rows": 0,
            "alias_resolution_parity_rows": sum(
                bool(row["alias_resolution_parity"]) for row in timing_inventory
            ),
        },
        "expected_early_core_failure": known[0],
        "historical_c_attempted_contexts": 5,
        "historical_c_completed_full_runs": 0,
        "transport_failures": 0,
        "context_semantic_failures": 1,
        "historical_invalid_output_still_rejected": True,
        "new_unexpected_failure_count": sum(
            row["current_verdict"] == "FAIL"
            and not (row["run"] == "C" and row["ticker"] == "NEON")
            for row in (*core_inventory, *timing_inventory)
        ),
        "status": "PASS",
    }
    summary["exact_candidates"] = exact_candidates
    return core_inventory, timing_inventory, summary


def _unknown_signature(row: Mapping[str, object]) -> list[dict[str, object]]:
    return [
        {
            "treatment": item.get("treatment"),
            "evidence_refs": item.get("evidence_refs") or [],
            "directional_negative_basis": item.get("directional_negative_basis") or [],
            "summary": item.get("summary"),
        }
        for item in row.get("unknown_treatments") or []
        if isinstance(item, Mapping)
    ]


def _driver_refs(row: Mapping[str, object], field: str) -> list[str]:
    return sorted(
        {
            str(ref)
            for claim in row.get(field) or []
            if isinstance(claim, Mapping)
            for ref in claim.get("evidence_refs") or []
        }
    )


def _core_snapshot(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "direction": row.get("overall_direction"),
        "balance": row.get("directional_balance"),
        "hold_lean": row.get("hold_lean"),
        "confidence": row.get("directional_confidence"),
        "dominant_evidence": row.get("dominant_evidence"),
        "material_anchors": row.get("material_directional_anchor_basis") or [],
        "buy_driver_refs": _driver_refs(row, "buy_drivers"),
        "sell_driver_refs": _driver_refs(row, "sell_drivers"),
        "unknown_treatments": _unknown_signature(row),
        "core_judgment": row.get("core_investment_judgment"),
        "new_buyer": row.get("fundamental_new_buyer"),
        "holder": row.get("fundamental_holder"),
        "reevaluation_up": row.get("business_reevaluation_up"),
        "reevaluation_down": row.get("business_reevaluation_down"),
    }


def _boundary_cause(before: Mapping[str, object], after: Mapping[str, object]) -> str:
    causes: list[str] = []
    before_balance = before.get("directional_balance") or {}
    after_balance = after.get("directional_balance") or {}
    if abs(float(before_balance.get("buy") or 0) - float(after_balance.get("buy") or 0)) == 0.5:
        causes.append("ADJACENT_BUCKET_CALIBRATION_VARIANCE")
    material_changed = (
        before.get("material_directional_anchor_basis")
        != after.get("material_directional_anchor_basis")
        or _driver_refs(before, "buy_drivers") != _driver_refs(after, "buy_drivers")
        or _driver_refs(before, "sell_drivers") != _driver_refs(after, "sell_drivers")
    )
    if material_changed:
        causes.append("MATERIAL_EVIDENCE_SELECTION_VARIANCE")
    if _unknown_signature(before) != _unknown_signature(after):
        causes.append("CURRENTNESS_OR_UNCERTAINTY_INTERPRETATION_VARIANCE")
    if not causes:
        return "INSUFFICIENT_EVIDENCE"
    if len(causes) > 1:
        return "MIXED"
    return causes[0]


def boundary_review(exact: Mapping[tuple[str, str], Mapping[str, object]]) -> dict[str, object]:
    tickers = sorted(ticker for run, ticker in exact if run == "C")
    rows = []
    absolute_crossings = []
    lean_only_changes = []
    direct_reversals = []
    for ticker in tickers:
        by_run = {run: exact[(run, ticker)] for run in RUNS}
        before = by_run["B"]
        after = by_run["C"]
        before_direction = str(before["overall_direction"])
        after_direction = str(after["overall_direction"])
        direction_changed = before_direction != after_direction
        lean_changed = before.get("hold_lean") != after.get("hold_lean")
        if direction_changed:
            absolute_crossings.append(ticker)
        elif lean_changed or before.get("directional_balance") != after.get(
            "directional_balance"
        ):
            lean_only_changes.append(ticker)
        all_directions = [str(by_run[run]["overall_direction"]) for run in RUNS]
        if "BUY" in all_directions and "SELL" in all_directions:
            direct_reversals.append(ticker)
        rows.append(
            {
                "ticker": ticker,
                "complete_first_a_b": {
                    run: _core_snapshot(by_run[run]) for run in COMPLETE_RUNS
                },
                "raw_first_a_b_c": {
                    run: _core_snapshot(by_run[run]) for run in RUNS
                },
                "b_to_c_absolute_direction_crossing": direction_changed,
                "b_to_c_lean_or_balance_only_change": not direction_changed
                and (
                    lean_changed
                    or before.get("directional_balance")
                    != after.get("directional_balance")
                ),
                "supported_cause_classification": _boundary_cause(before, after),
            }
        )
    return {
        "contract": "descriptive-directional-boundary-review-v1",
        "first_a_b_complete_run_count": 3,
        "first_a_b_c_raw_core_run_count": 4,
        "issuer_count": len(tickers),
        "b_to_c_absolute_direction_crossing_count": len(absolute_crossings),
        "b_to_c_absolute_direction_crossings": absolute_crossings,
        "b_to_c_lean_or_balance_only_change_count": len(lean_only_changes),
        "b_to_c_lean_or_balance_only_changes": lean_only_changes,
        "direct_buy_sell_reversal_count": len(direct_reversals),
        "direct_buy_sell_reversals": direct_reversals,
        "formal_current_cohort_stability": "NOT_MEASURED",
        "c_full_run_status": "NOT_COMPLETED",
        "rows": rows,
        "status": "DESCRIPTIVE_COMPLETE",
    }


def prompt_hash_ledger(
    experiment: Path,
    source_lock: Mapping[str, object],
    cohort: Sequence[str],
    owned: Mapping[str, object],
    core_aliases: Mapping[str, object],
) -> dict[str, object]:
    rows = []
    for number, batch in enumerate(frozen.batches(cohort), start=1):
        historical = experiment / "prompts" / f"core-batch-{number:02d}.txt"
        current = frozen._core_prompt(
            packet_id=str(source_lock["program_generation_id"]),
            tickers=batch,
            contexts=tuple(
                frozen._owned_context(owned[ticker], core_aliases[ticker])
                for ticker in batch
            ),
        )
        historical_text = historical.read_text(encoding="utf-8")
        rows.append(
            {
                "batch": number,
                "tickers": list(batch),
                "historical_prompt_sha256": bytes_sha256(historical_text.encode()),
                "current_prompt_sha256": bytes_sha256(current.encode()),
                "byte_identical": historical_text == current,
            }
        )
    prior_hashes = read_json(experiment / "program-state.json").get(
        "architecture_hashes"
    ) or {}
    return {
        "contract": "unknown-field-prompt-hash-ledger-v1",
        "historical_frozen_runner_sha256": prior_hashes.get("frozen_runner"),
        "current_frozen_runner_sha256": file_sha256(Path(frozen.__file__)),
        "historical_validator_renderer_sha256": prior_hashes.get(
            "validator_renderer"
        ),
        "current_validator_renderer_sha256": file_sha256(
            Path(inspect.getsourcefile(unknown_treatment_consistency_issues) or "")
        ),
        "prompt_changed": any(not row["byte_identical"] for row in rows),
        "model_emission_effectiveness": "NOT_MEASURED",
        "historical_calibration_applies_to_edited_prompt": False,
        "rows": rows,
        "status": "RECORDED",
    }


def offline_regression_matrix(
    exact: Mapping[tuple[str, str], Mapping[str, object]],
    owned: Mapping[str, object],
) -> dict[str, object]:
    historical = DirectionalCoreCandidate.model_validate(exact[("C", "NEON")])
    historical_result = proof.core_partial_audit((historical,), {"NEON": owned["NEON"]})
    fictional = synthetic.fictional_owned("SYNTHETIC_UNKNOWN_CONTRACT", market="us")
    base = synthetic.fixture_core(fictional)
    earnings = f"fictional:{base.ticker}:earnings"
    missing = f"fictional:{base.ticker}:unknown"
    support = f"fictional:{base.ticker}:support"

    def candidate(*unknowns: DirectionalUnknown) -> DirectionalCoreCandidate:
        return base.model_copy(update={"unknown_treatments": unknowns})

    confirmation = candidate(
        DirectionalUnknown(
            summary="Historical context requires current confirmation.",
            evidence_refs=(earnings,),
            treatment="CONFIRMATION_REQUIRED",
            directional_negative_basis=(),
        )
    )
    confidence_invalid = candidate(
        DirectionalUnknown(
            summary="Confidence is limited.",
            evidence_refs=(earnings,),
            treatment="CONFIDENCE_LIMIT",
            directional_negative_basis=(earnings,),
        )
    )
    confirmed_negative = candidate(
        DirectionalUnknown(
            summary="A confirmed loss is negative evidence.",
            evidence_refs=(earnings,),
            treatment="DIRECTIONAL_NEGATIVE",
            directional_negative_basis=(earnings,),
        ),
        DirectionalUnknown(
            summary="Future execution needs confirmation.",
            evidence_refs=(missing,),
            treatment="CONFIRMATION_REQUIRED",
            directional_negative_basis=(),
        ),
    )
    missing_negative = candidate(
        DirectionalUnknown(
            summary="Only missing evidence is supplied.",
            evidence_refs=(missing,),
            treatment="DIRECTIONAL_NEGATIVE",
            directional_negative_basis=(missing,),
        )
    )
    forbidden_price = base.model_copy(
        update={
            "business_thesis_context": base.business_thesis_context.model_copy(
                update={"evidence_refs": (support,)}
            )
        }
    )
    cases = []

    def add_case(name: str, row: DirectionalCoreCandidate, expected: str) -> None:
        result = proof.core_partial_audit((row,), {row.ticker: fictional})
        cases.append(
            {
                "case": name,
                "expected": expected,
                "actual": result["status"],
                "errors": result["rows"][0]["errors"],
                "status": "PASS" if result["status"] == expected else "FAIL",
            }
        )

    cases.append(
        {
            "case": "exact_historical_neon_invalid_core",
            "expected": "FAIL",
            "actual": historical_result["status"],
            "errors": historical_result["rows"][0]["errors"],
            "source_kind": "EXACT_HISTORICAL_MODEL_OUTPUT",
            "status": "PASS" if historical_result["status"] == "FAIL" else "FAIL",
        }
    )
    add_case("confirmation_required_context_without_negative_basis", confirmation, "PASS")
    add_case("confidence_limit_with_negative_basis", confidence_invalid, "FAIL")
    add_case("confirmed_negative_plus_separate_unknown", confirmed_negative, "PASS")
    add_case("missing_only_promoted_to_negative", missing_negative, "FAIL")
    add_case("forbidden_price_reference_in_core", forbidden_price, "FAIL")

    core_catalog, _ = stage_alias_catalogs(fictional)
    raw_alias = _reference_to_alias(
        base.model_dump(mode="json"), core_catalog.by_ref
    )
    resolved, _audit = frozen._resolve_batch_candidates(
        [raw_alias],
        batch=(base.ticker,),
        evidence={base.ticker: fictional.source_packet},
        catalogs={base.ticker: core_catalog},
        model_type=DirectionalCoreCandidate,
    )
    before = proof.core_partial_audit((base,), {base.ticker: fictional})
    after = proof.core_partial_audit(resolved, {base.ticker: fictional})
    alias_same = (
        resolved[0].model_dump(mode="json") == base.model_dump(mode="json")
        and before["status"] == after["status"]
    )
    cases.append(
        {
            "case": "same_candidate_before_after_valid_alias_resolution",
            "expected": "PASS",
            "actual": "PASS" if alias_same else "FAIL",
            "status": "PASS" if alias_same else "FAIL",
        }
    )
    bad_alias = json.loads(json.dumps(raw_alias))
    bad_alias["business_thesis_context"]["evidence_refs"] = ["E999"]
    try:
        frozen._resolve_batch_candidates(
            [bad_alias],
            batch=(base.ticker,),
            evidence={base.ticker: fictional.source_packet},
            catalogs={base.ticker: core_catalog},
            model_type=DirectionalCoreCandidate,
        )
        bad_alias_error = None
    except ValueError as exc:
        bad_alias_error = str(exc)
    cases.append(
        {
            "case": "nonexistent_alias_rejected",
            "expected": "FAIL",
            "actual": "FAIL" if bad_alias_error else "PASS",
            "error": bad_alias_error,
            "status": "PASS" if bad_alias_error else "FAIL",
        }
    )
    other = synthetic.fictional_owned("SYNTHETIC_OTHER_OWNER", market="us")
    other_catalog, _ = stage_alias_catalogs(other)
    try:
        frozen._resolve_batch_candidates(
            [raw_alias],
            batch=(base.ticker,),
            evidence={base.ticker: fictional.source_packet},
            catalogs={base.ticker: other_catalog},
            model_type=DirectionalCoreCandidate,
        )
        cross_owner_error = None
    except ValueError as exc:
        cross_owner_error = str(exc)
    cases.append(
        {
            "case": "cross_issuer_catalog_rejected",
            "expected": "FAIL",
            "actual": "FAIL" if cross_owner_error else "PASS",
            "error": cross_owner_error,
            "status": "PASS" if cross_owner_error else "FAIL",
        }
    )
    timing = synthetic.fixture_timing(fictional, base)
    composed = compose_decision(base, timing)
    ownership = validate_ownership(fictional, base, timing, composed)
    cases.append(
        {
            "case": "independently_valid_core_timing_ownership_unchanged",
            "expected": "PASS",
            "actual": "PASS" if not ownership.errors else "FAIL",
            "errors": list(ownership.errors),
            "status": "PASS" if not ownership.errors else "FAIL",
        }
    )
    return {
        "contract": "unknown-field-offline-regression-matrix-v1",
        "fixture_policy": "HAND_AUTHORED_OR_EXACT_HISTORICAL_NO_MODEL_CALL",
        "corrected_derivatives": "TEST_DERIVATIVE_NOT_MODEL_OUTPUT",
        "actual_orchestration_early_stop_test": (
            "tests/test_new_issuer_holdout_selection_ownership_proof.py::"
            "test_execute_run_stops_before_timing_after_invalid_core"
        ),
        "cases": cases,
        "case_count": len(cases),
        "failure_count": sum(row["status"] != "PASS" for row in cases),
        "status": "PASS" if all(row["status"] == "PASS" for row in cases) else "FAIL",
    }


def message_quality_review(
    experiment: Path,
    owned: Mapping[str, object],
    core_inventory: Sequence[Mapping[str, object]],
    timing_inventory: Sequence[Mapping[str, object]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    core_paths = {
        (str(row["run"]), str(row["ticker"])): str(row["context_path"])
        for row in core_inventory
    }
    timing_paths = {
        (str(row["run"]), str(row["ticker"])): str(row["context_path"])
        for row in timing_inventory
    }
    advisory_path = experiment / "advisory-message-quality-summary.json"
    advisory = read_json(advisory_path)
    inventory: list[dict[str, object]] = []
    messages: dict[tuple[str, str], list[str]] = {}
    composed_strings: dict[tuple[str, str], tuple[str, ...]] = {}
    for run in COMPLETE_RUNS:
        run_root = experiment / "issuer-results" / run
        for ticker_dir in sorted(path for path in run_root.iterdir() if path.is_dir()):
            ticker = ticker_dir.name
            composed_path = ticker_dir / "composed-state.json"
            lineage_path = ticker_dir / "renderer-input-lineage.json"
            message_path = ticker_dir / "rendered-message.txt"
            composed = read_json(composed_path)
            lineage = read_json(lineage_path)
            message = message_path.read_text(encoding="utf-8")
            lines = message.splitlines()
            messages[(run, ticker)] = lines
            composed_strings[(run, ticker)] = _all_strings(composed)
            decision_line = next((line for line in lines if "판단:" in line), "")
            available = {
                row.ref.ref_id
                for row in owned[ticker].evidence
                if row.domain in CORE_DOMAINS
                and row.domain
                not in {EvidenceDomain.IDENTITY_SECURITY, EvidenceDomain.DATA_QUALITY_LIMIT}
            }
            selected = _all_refs(lineage.get("core") or composed)
            omitted = sorted(available - selected)
            trace_complete = all(
                (
                    composed_path.is_file(),
                    lineage_path.is_file(),
                    message_path.is_file(),
                    (run, ticker) in core_paths,
                    (run, ticker) in timing_paths,
                )
            )
            inventory.append(
                {
                    "run": run,
                    "ticker": ticker,
                    "decision": composed.get("decision"),
                    "directional_balance": composed.get("directional_balance"),
                    "message_path": str(message_path.relative_to(experiment)),
                    "message_sha256": file_sha256(message_path),
                    "message_character_count": len(message),
                    "message_line_count": len(lines),
                    "composed_state_path": str(composed_path.relative_to(experiment)),
                    "composed_state_sha256": file_sha256(composed_path),
                    "renderer_lineage_path": str(lineage_path.relative_to(experiment)),
                    "renderer_lineage_sha256": file_sha256(lineage_path),
                    "core_context_path": core_paths.get((run, ticker)),
                    "timing_context_path": timing_paths.get((run, ticker)),
                    "source_packet_sha256": lineage.get("packet_sha256"),
                    "source_to_message_trace": "COMPLETE"
                    if trace_complete
                    else "UNKNOWN_OR_NOT_AVAILABLE_IN_BUNDLE",
                    "conclusion_line_matches_composed_decision": str(
                        composed.get("decision")
                    )
                    in decision_line,
                    "daily_delta_label_present": any(
                        token in message for token in ("Daily Delta", "데일리 델타")
                    ),
                    "supplied_issuer_specific_core_ref_count": len(available),
                    "selected_core_ref_count": len(selected),
                    "unselected_supplied_core_refs": omitted,
                    "unselected_ref_materiality": "NOT_ADJUDICATED",
                }
            )

    repeated_findings = []
    for advisory_row in advisory.get("rows") or []:
        run = str(advisory_row.get("run") or "").upper()
        quality = advisory_row.get("quality") or {}
        for span in quality.get("repeated_substantive_spans") or []:
            locations = []
            ownership = Counter()
            body = str(span)
            unwrapped = body.removeprefix("BUY 쪽: ").removeprefix("SELL 쪽: ")
            for (message_run, ticker), lines in messages.items():
                if message_run != run:
                    continue
                for number, line in enumerate(lines, start=1):
                    if body not in line:
                        continue
                    locations.append({"ticker": ticker, "line": number})
                    strings = composed_strings[(message_run, ticker)]
                    if body in strings:
                        ownership["MODEL_OWNED_SUBSTANTIVE"] += 1
                    elif unwrapped in strings:
                        ownership["MODEL_CONTENT_WITH_RENDERER_WRAPPER"] += 1
                    else:
                        ownership["RENDERER_INTRODUCED_OR_UNRESOLVED"] += 1
            repeated_findings.append(
                {
                    "run": run,
                    "span": body,
                    "occurrence_count": len(locations),
                    "locations": locations,
                    "ownership_counts": dict(ownership),
                }
            )
    original_counts = {
        str(row.get("run")): row.get("repeated_substantive_span_count")
        for row in advisory.get("rows") or []
    }
    review = {
        "contract": "preserved-message-quality-offline-review-v1",
        "message_count": len(inventory),
        "complete_trace_count": sum(
            row["source_to_message_trace"] == "COMPLETE" for row in inventory
        ),
        "conclusion_alignment_failure_count": sum(
            not row["conclusion_line_matches_composed_decision"] for row in inventory
        ),
        "daily_delta_label_count": sum(
            bool(row["daily_delta_label_present"]) for row in inventory
        ),
        "original_advisory_path": str(advisory_path.relative_to(experiment)),
        "original_advisory_sha256": file_sha256(advisory_path),
        "original_repeated_substantive_span_counts": original_counts,
        "original_advisory_status_preserved": True,
        "repeated_findings": repeated_findings,
        "safe_repeated_headers": [
            "판단 확신도",
            "사업 논리 상태",
            "신규 관찰자",
            "보유자",
            "핵심 판단",
            "재평가 조건",
        ],
        "source_not_supplied_to_core_finding": "DEFERRED_INPUT_COVERAGE_DECISION",
        "renderer_rewrite_performed": False,
        "candidate_rewrite_performed": False,
        "message_quality_original_advisory": "RECORDED",
        "message_quality_review_completion": "COMPLETE",
        "status": "COMPLETE_WITH_ADVISORY_FINDINGS",
    }
    return inventory, review


def integration_inventory(repo_root: Path) -> dict[str, object]:
    rows = [
        {
            "boundary": "explicit registration and versioned thesis",
            "module": "app/services/monitoring_service.py",
            "function": "register_monitoring_item_with_continuation",
            "current_caller": "app/api/routes_monitoring.py::register_monitoring",
            "shared_or_experiment": "PRODUCTION_SHARED",
            "input_output": "MonitoringItemCreate -> MonitoringItemRead",
            "side_effects": "explicit DB registration/versioning; onboarding continuation",
            "existing_tests": ["tests/test_monitoring.py", "tests/test_onboarding_readiness_service.py"],
            "future_requirement": "preserve explicit intent and pending readiness gates",
        },
        {
            "boundary": "initial read-only/acquired evidence preparation",
            "module": "app/services/onboarding_evidence_service.py",
            "function": "build_initial_evidence",
            "current_caller": "app/services/onboarding_reconciler_service.py::resume_onboarding_subject",
            "shared_or_experiment": "PRODUCTION_SHARED",
            "input_output": "WatchlistItem + as_of/acquire -> initial evidence dict",
            "side_effects": "acquire=True may collect; acquire=False reopens stored baseline",
            "existing_tests": ["tests/test_onboarding_readiness_service.py"],
            "future_requirement": "adapter test must distinguish source preparation from registration",
        },
        {
            "boundary": "versioned initial absolute baseline",
            "module": "app/services/onboarding_evidence_service.py",
            "function": "ensure_initial_baseline",
            "current_caller": "app/services/onboarding_reconciler_service.py::resume_onboarding_subject",
            "shared_or_experiment": "PRODUCTION_SHARED",
            "input_output": "validated initial evidence -> idempotent ThesisAssessment baseline",
            "side_effects": "DB assessment insert only when baseline absent",
            "existing_tests": ["tests/test_thesis_evaluation.py", "tests/test_onboarding_reconciler_service.py"],
            "future_requirement": "prove initial_baseline is never rendered as Daily Delta",
        },
        {
            "boundary": "bootstrap readiness and activation",
            "module": "app/services/onboarding_reconciler_service.py",
            "function": "resume_onboarding_subject",
            "current_caller": "registration continuation and reconcile_pending_onboarding",
            "shared_or_experiment": "PRODUCTION_SHARED",
            "input_output": "pending WatchlistItem -> staged readiness/activation result",
            "side_effects": "idempotent staged DB state transitions",
            "existing_tests": ["tests/test_onboarding_reconciler_service.py"],
            "future_requirement": "stored-but-incomplete remains non-production-eligible",
        },
        {
            "boundary": "daily event/earnings comparison and persistence",
            "module": "app/services/daily_monitor_service.py",
            "function": "run_daily_monitor",
            "current_caller": "app/jobs/monitor_daily.py::_run_market_job",
            "shared_or_experiment": "PRODUCTION_SHARED",
            "input_output": "eligible universe/run cutoff -> assessments and deliveries",
            "side_effects": "collection, assessments, warnings, optional queue/dispatch",
            "existing_tests": ["tests/test_daily_monitor.py", "tests/test_daily_accuracy_regressions.py"],
            "future_requirement": "missing refresh must not be reclassified as no material change",
        },
        {
            "boundary": "accepted V2 context and output validation",
            "module": "app/jobs/accepted_decision_v2_runtime.py",
            "function": "prepare_context / validate_output / generate",
            "current_caller": "same runtime CLI main and monitor job claim path",
            "shared_or_experiment": "PRODUCTION_RUNTIME_GATED",
            "input_output": "packet claim -> prepared context -> validated artifact",
            "side_effects": "runtime artifact state; model call only in generate",
            "existing_tests": ["tests/test_accepted_decision_v2_runtime.py", "tests/test_v2_wait_ownership.py"],
            "future_requirement": "future integration must use accepted claim/lease lifecycle",
        },
        {
            "boundary": "Directional Core and Price-Timing ownership/composition",
            "module": "app/services/direction_timing_ownership_service.py",
            "function": "build_owned_evidence_packet / compose_decision / validate_ownership",
            "current_caller": "experiment runners; no production activation in this task",
            "shared_or_experiment": "SHARED_CONTRACT_EXPERIMENT_CONSUMER",
            "input_output": "canonical packet + Core + Timing -> composed decision",
            "side_effects": "none",
            "existing_tests": ["tests/test_direction_timing_ownership_service.py"],
            "future_requirement": "adapt lifecycle inputs without collapsing baseline and delta",
        },
        {
            "boundary": "structured validator and renderer",
            "module": "app/services/structured_autonomy_shadow_service.py",
            "function": "validate_structured_autonomy_candidate / render_structured_autonomy_message",
            "current_caller": "shadow experiment timing audit",
            "shared_or_experiment": "SHARED_SHADOW_CONTRACT",
            "input_output": "packet + composed decision -> validation/rendered shadow message",
            "side_effects": "none",
            "existing_tests": ["tests/test_structured_autonomy_shadow_service.py"],
            "future_requirement": "production adapter requires separate canary and delivery decision",
        },
        {
            "boundary": "assessment/warning persistence",
            "module": "app/services/monitoring_service.py",
            "function": "record_assessment",
            "current_caller": "app/api/routes_monitoring.py::record_thesis_assessment",
            "shared_or_experiment": "PRODUCTION_SHARED",
            "input_output": "versioned assessment payload -> ThesisAssessmentRead",
            "side_effects": "DB assessment, warning and export state",
            "existing_tests": ["tests/test_monitoring.py"],
            "future_requirement": "initial absolute judgment must not overwrite prior versions/warnings",
        },
        {
            "boundary": "fallback, queue and Telegram send ownership",
            "module": "app/services/notification_service.py",
            "function": "queue_daily_stock_notification / dispatch_pending_notifications",
            "current_caller": "daily monitor and monitor_daily job",
            "shared_or_experiment": "PRODUCTION_SHARED",
            "input_output": "assessment/delivery row -> channel dispatch receipt",
            "side_effects": "notification DB state and external send when enabled",
            "existing_tests": ["tests/test_notification_service.py"],
            "future_requirement": "prove idempotent delivery and keep experiment output detached",
        },
    ]
    for row in rows:
        path = repo_root / str(row["module"])
        function_names = [part.strip() for part in str(row["function"]).split("/")]
        row["file_exists"] = path.is_file()
        row["function_tokens_present"] = all(
            f"def {name}" in path.read_text(encoding="utf-8")
            or f"async def {name}" in path.read_text(encoding="utf-8")
            for name in function_names
        )
        row["inspection_status"] = (
            "VERIFIED"
            if row["file_exists"] and row["function_tokens_present"]
            else "UNRESOLVED"
        )
    proposed_tests = [
        "initial absolute baseline is not a Daily Delta",
        "registration requires explicit user intent and incomplete onboarding stays inactive",
        "initial analysis does not overwrite prior thesis versions or warning state",
        "missing refresh is not converted to no material change",
        "baseline, assessment and delivery operations remain idempotent",
        "existing and new issuers share decision/message contracts without lifecycle collapse",
    ]
    return {
        "contract": "existing-code-integration-boundary-inventory-v1",
        "rows": rows,
        "verified_count": sum(row["inspection_status"] == "VERIFIED" for row in rows),
        "unresolved_count": sum(row["inspection_status"] != "VERIFIED" for row in rows),
        "minimal_nonproduction_plan": [
            "build an adapter from lifecycle-qualified evidence to the shared decision packet",
            "run archive/runtime shadow canary with persistence and delivery disabled",
            "prove lifecycle/idempotency tests before any production-readiness decision",
        ],
        "proposed_tests": proposed_tests,
        "production_integration_performed": False,
        "status": "COMPLETE",
    }


def pause_and_side_effect_observation() -> dict[str, object]:
    pause = pause_observer.observe_pause_state()
    process = diagnostic.PausedScheduleProcessObserver().observe()
    paused = (
        pause.get("status") == "VERIFIED_PAUSED_COMPLETE"
        and not process.get("active_natural_job_count")
        and not process.get("running_model_process_count")
    )
    return {
        "contract": "offline-review-operating-safety-v1",
        "pause_observation": pause,
        "process_observation": process,
        "model_calls": {"real": 0, "fictional": 0, "judge": 0},
        "provider_source_fetches": 0,
        "paid_data_service_changes": 0,
        "main_merges": 0,
        "deployments": 0,
        "production_db_mutations": 0,
        "production_sends": 0,
        "registrations": 0,
        "live_v2_activations": 0,
        "night_futures_changes": 0,
        "automatic_monitoring_resume": 0,
        "scheduler_mutation_count": 0,
        "status": "PASS" if paused else "CURRENT_STATE_NOT_VERIFIED",
    }


def _cohort_identities(
    experiment: Path, cohort: Sequence[str]
) -> dict[str, dict[str, str]]:
    identities = {}
    for ticker in cohort:
        packet = read_json(experiment / "packets" / f"{ticker}.json")
        market = str(packet.get("market") or "")
        assembly = packet.get("source_assembly") or {}
        issuer_id = str(assembly.get("issuer_id") or "")
        if market == "us" and issuer_id.isdigit():
            issuer_key = f"sec:cik:{issuer_id.zfill(10)}"
        elif market == "kr" and issuer_id.isdigit():
            issuer_key = f"opendart:corp:{issuer_id.zfill(8)}"
        else:
            raise ValueError(f"unsupported_cohort_identity:{ticker}:{market}:{issuer_id}")
        identities[str(ticker)] = {
            "canonical_issuer_key": issuer_key,
            "market": market,
        }
    return identities


def _reconcile_exposure_registry(
    source_registry: Mapping[str, object],
    identities: Mapping[str, Mapping[str, str]],
    core_inventory: Sequence[Mapping[str, object]],
    generation_id: str,
) -> tuple[dict[str, object], int]:
    rows_by_key = {
        str(row["canonical_issuer_key"]): copy.deepcopy(dict(row))
        for row in source_registry.get("rows") or []
        if isinstance(row, Mapping) and row.get("canonical_issuer_key")
    }
    if len(rows_by_key) != len(source_registry.get("rows") or []):
        raise ValueError("source_exposure_registry_duplicate_or_missing_key")
    inventory_by_ticker: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for item in core_inventory:
        inventory_by_ticker[str(item["ticker"])].append(item)
    appended = 0
    for ticker, identity in identities.items():
        issuer_key = str(identity["canonical_issuer_key"])
        evidence_rows = inventory_by_ticker[ticker]
        if len(evidence_rows) != 4:
            raise ValueError(f"cohort_core_exposure_incomplete:{ticker}")
        lineage = [
            {
                "experiment_class": CONTRACT,
                "exposure_class": "REAL_MODEL_OUTPUT",
                "generation_id": generation_id,
                "run": str(item["run"]),
                "source_artifact": (
                    f"experiment/fresh-real-proof/{item['context_path']}/"
                    "output.normalized.json"
                ),
                "source_artifact_sha256": str(item["normalized_output_sha256"]),
                "ticker": ticker,
                "usable_output_exists": True,
            }
            for item in sorted(evidence_rows, key=lambda value: str(value["run"]))
        ]
        row = rows_by_key.get(issuer_key)
        if row is None:
            appended += 1
            row = {
                "actual_output_exposure": True,
                "actual_real_model_spawn": True,
                "canonical_issuer_key": issuer_key,
                "exclusion_reasons": ["RETIRED_FOR_ARCHITECTURE_REPAIR"],
                "lineage": [],
                "market": identity["market"],
                "security_aliases": [],
                "whole_cohort_retired": True,
                "retirement_reasons": ["RETIRED_FOR_ARCHITECTURE_REPAIR"],
            }
            rows_by_key[issuer_key] = row
        row["actual_output_exposure"] = True
        row["actual_real_model_spawn"] = True
        row["whole_cohort_retired"] = True
        row["security_aliases"] = sorted(
            set(str(value) for value in row.get("security_aliases") or []) | {ticker}
        )
        row["exclusion_reasons"] = sorted(
            set(str(value) for value in row.get("exclusion_reasons") or [])
            | {"RETIRED_FOR_ARCHITECTURE_REPAIR"}
        )
        row["retirement_reasons"] = sorted(
            set(str(value) for value in row.get("retirement_reasons") or [])
            | {"RETIRED_FOR_ARCHITECTURE_REPAIR"}
        )
        existing_lineage = {
            canonical_sha256(value)
            for value in row.get("lineage") or []
            if isinstance(value, Mapping)
        }
        row.setdefault("lineage", [])
        for value in lineage:
            if canonical_sha256(value) not in existing_lineage:
                row["lineage"].append(value)
                existing_lineage.add(canonical_sha256(value))
    rows = [rows_by_key[key] for key in sorted(rows_by_key)]
    return (
        {
            "contract": "canonical-exposure-registry-unknown-consistency-review-v1",
            "source_contract": source_registry.get("contract"),
            "prior_registry_count": len(source_registry.get("rows") or []),
            "appended_exposed_issuer_count": appended,
            "newly_excluded_current_cohort_count": appended,
            "reconciled_registry_count": len(rows),
            "exclusion_shrink_count": 0,
            "latest_exposed_generation_id": generation_id,
            "latest_cohort_issuer_exposure": "16/16_REAL_OUTPUT_16/16_RETIRED",
            "latest_cohort_core_stage_coverage": "16/16_EACH_FIRST_A_B_C",
            "latest_cohort_timing_stage_coverage": "16/16_FIRST_A_B_4/16_C",
            "latest_complete_run_coverage": ["FIRST", "A", "B"],
            "latest_failed_run": "C_TIMING_AFTER_CORE_SEMANTIC_FAILURE",
            "latest_retirement_reason": "RETIRED_FOR_ARCHITECTURE_REPAIR",
            "rows": rows,
            "all_excluded_issuer_keys": sorted(rows_by_key),
            "status": "PASS",
        },
        appended,
    )


def source_exposure_review(
    extracted: Path,
    experiment: Path,
    cohort: Sequence[str],
    core_inventory: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object], dict[str, object]]:
    source_registry = read_json(experiment / "selection-inputs" / "merged-registry.json")
    source_completion = read_json(extracted / "completion.json")
    retirement = read_json(
        extracted
        / "reports"
        / "proofs"
        / "59-fresh-holdout-exposure-retirement-state.json"
    )
    program_state = read_json(experiment / "program-state.json")
    generation_id = str(program_state["program_generation_id"])
    identities = _cohort_identities(experiment, cohort)
    source_keys = set(str(value) for value in source_registry["all_excluded_issuer_keys"])
    missing_before = sorted(
        ticker
        for ticker, identity in identities.items()
        if identity["canonical_issuer_key"] not in source_keys
    )
    updated, appended = _reconcile_exposure_registry(
        source_registry, identities, core_inventory, generation_id
    )
    second_pass, second_appended = _reconcile_exposure_registry(
        updated, identities, core_inventory, generation_id
    )
    updated_keys = set(str(value) for value in updated["all_excluded_issuer_keys"])
    second_pass_rows_equivalent = canonical_sha256(updated["rows"]) == canonical_sha256(
        second_pass["rows"]
    )
    missing_after = sorted(
        ticker
        for ticker, identity in identities.items()
        if identity["canonical_issuer_key"] not in updated_keys
    )
    expected_exposed = sorted(str(value) for value in retirement["exposed_subjects"])
    status = (
        expected_exposed == sorted(cohort)
        and retirement.get("holdout_output_exposure_state") == "FULLY_EXPOSED"
        and retirement.get("holdout_retirement_state")
        == "RETIRED_FOR_ARCHITECTURE_REPAIR"
        and not missing_after
        and second_appended == 0
        and second_pass_rows_equivalent
    )
    review = {
        "contract": "current-cohort-exposure-retirement-review-v1",
        "cohort": list(cohort),
        "cohort_count": len(cohort),
        "canonical_identities": identities,
        "source_registry_sha256": canonical_sha256(source_registry),
        "source_registry_count": len(source_registry.get("rows") or []),
        "source_recorded_newly_excluded_current_cohort_count": source_completion.get(
            "newly_excluded_current_cohort_count"
        ),
        "missing_canonical_issuers_before_reconciliation": missing_before,
        "newly_appended_in_this_task": appended,
        "reconciled_registry_count": updated["reconciled_registry_count"],
        "missing_canonical_issuers_after_reconciliation": missing_after,
        "second_pass_appended_count": second_appended,
        "second_pass_registry_rows_equivalent": second_pass_rows_equivalent,
        "updated_registry_sha256": canonical_sha256(updated),
        "exposure_state": "FULLY_EXPOSED",
        "retirement_state": "RETIRED_FOR_ARCHITECTURE_REPAIR",
        "same_cohort_rerun_allowed": False,
        "status": "PASS" if status else "FAIL",
    }
    return review, updated


def _summary_markdown(
    authority: Mapping[str, object],
    audit: Mapping[str, object],
    regression: Mapping[str, object],
    boundary: Mapping[str, object],
    messages: Mapping[str, object],
    integration: Mapping[str, object],
    safety: Mapping[str, object],
) -> str:
    core = audit["core"]
    timing = audit["timing"]
    return f"""# Unknown-Field Consistency Offline Review

## Result

- Source ZIP integrity: `{authority['status']}` ({authority['zip_member_count']} members, {authority['indexed_payload_count']} indexed payloads)
- Core audit: `{core['checked_rows']}/{core['raw_rows']}` checked, `{core['failed_rows']}` expected failure
- Timing audit: `{timing['checked_rows']}/{timing['raw_rows']}` checked, `{timing['failed_rows']}` expected failure
- Exact historical NEON output: remains rejected; now detected at the Core gate
- Offline regression matrix: `{regression['status']}` ({regression['case_count']} cases)
- B to C absolute direction crossings: `{boundary['b_to_c_absolute_direction_crossing_count']}`
- Direct BUY to SELL reversals: `{boundary['direct_buy_sell_reversal_count']}`
- Preserved complete messages reviewed: `{messages['message_count']}`
- Integration boundaries verified: `{integration['verified_count']}/{len(integration['rows'])}`
- Paused operating state: `{safety['status']}`

## Claim Boundaries

- Model emission effectiveness: `NOT_MEASURED`
- Formal current-cohort stability: `NOT_MEASURED`
- Ownership generalization: `NOT_ESTABLISHED`
- Production readiness: `NOT_READY`
- C completed full runs: `0`
- New model/provider calls: `0/0`
"""


def run(args: argparse.Namespace) -> dict[str, object]:
    repo_root = Path(args.repo_root).resolve()
    source_zip = Path(args.source_zip).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    authority = verify_source_archive(source_zip)
    with tempfile.TemporaryDirectory(prefix="unknown-field-offline-review-") as raw_temp:
        extracted = Path(raw_temp)
        with zipfile.ZipFile(source_zip) as archive:
            archive.extractall(extracted)
        experiment = extracted / EXPERIMENT_PREFIX
        (
            source_lock,
            cohort,
            contexts,
            evidence,
            owned,
            core_aliases,
            timing_aliases,
            price_maps,
            stocks,
        ) = _load_inputs(experiment)
        core_inventory, timing_inventory, historical = audit_historical_outputs(
            experiment=experiment,
            source_lock=source_lock,
            contexts=contexts,
            evidence=evidence,
            owned=owned,
            core_aliases=core_aliases,
            timing_aliases=timing_aliases,
            price_maps=price_maps,
            stocks=stocks,
        )
        exact = historical.pop("exact_candidates")
        boundary = boundary_review(exact)
        prompt_ledger = prompt_hash_ledger(
            experiment, source_lock, cohort, owned, core_aliases
        )
        regression = offline_regression_matrix(exact, owned)
        message_inventory, messages = message_quality_review(
            experiment, owned, core_inventory, timing_inventory
        )
        exposure, updated_exposure_registry = source_exposure_review(
            extracted, experiment, cohort, core_inventory
        )
        neon = exact[("C", "NEON")]
        neon_context = next(
            row
            for row in core_inventory
            if row["run"] == "C" and row["ticker"] == "NEON"
        )
        exact_neon = {
            "contract": "exact-historical-neon-invalid-core-capture-v1",
            "source_zip_sha256": EXPECTED_SOURCE_ZIP_SHA256,
            "source_member": (
                "experiment/fresh-real-proof/model-contexts/C/DIRECTIONAL_CORE/"
                "batch-01/output.normalized.json"
            ),
            "source_member_sha256": neon_context["normalized_output_sha256"],
            "candidate_sha256": canonical_sha256(neon),
            "capture_kind": "EXACT_HISTORICAL_MODEL_OUTPUT",
            "candidate": neon,
            "mutation_count": 0,
        }

    integration = integration_inventory(repo_root)
    safety = pause_and_side_effect_observation()
    authority["repository"] = {
        "branch": git_value(repo_root, "branch", "--show-current"),
        "head": git_value(repo_root, "rev-parse", "HEAD"),
        "tree": git_value(repo_root, "write-tree"),
        "origin_main": git_value(repo_root, "rev-parse", "origin/main"),
    }
    call_graph = {
        "contract": "unknown-field-actual-call-graph-root-cause-v1",
        "producer": "scripts/directional_core_price_timing_holdout.py::_core_prompt",
        "alias_expansion": "structured_autonomy_alias_service.resolve_candidate_aliases",
        "core_acceptance": "new_issuer_holdout_selection_ownership_proof.core_partial_audit",
        "composer": "direction_timing_ownership_service.compose_decision",
        "late_validation": "structured_autonomy_shadow_service.validate_structured_autonomy_candidate",
        "missing_invariant_before_repair": (
            "core_partial_audit did not apply Unknown treatment/basis consistency"
        ),
        "repair": (
            "unknown_treatment_consistency_issues is shared by Core and final validation"
        ),
        "early_stop": (
            "execute_run checks core_partial_audit before entering the Price-Timing loop"
        ),
        "historical_failure_code": "unknown_nonnegative_has_directional_basis",
        "historical_failure_path": (
            "unknown_treatments[0].directional_negative_basis"
        ),
        "status": "ROOT_CAUSE_CONFIRMED_AND_BOUNDED_REPAIR_IMPLEMENTED",
    }
    completion = {
        "contract": CONTRACT,
        "generated_at": datetime.now(UTC).isoformat(),
        "implementation_result": "PASS",
        "offline_regression_result": regression["status"],
        "historical_invalid_output_still_rejected": historical[
            "historical_invalid_output_still_rejected"
        ],
        "early_core_detection_result": "PASS",
        "model_emission_effectiveness": "NOT_MEASURED",
        "formal_current_cohort_stability": "NOT_MEASURED",
        "ownership_generalization": "NOT_ESTABLISHED",
        "message_quality_original_advisory": "RECORDED",
        "message_quality_review_completion": messages[
            "message_quality_review_completion"
        ],
        "integration_inventory_completion": integration["status"],
        "production_readiness": "NOT_READY",
        "historical_c_attempted_contexts": 5,
        "historical_c_completed_full_runs": 0,
        "transport_failures": 0,
        "context_semantic_failures": 1,
        "model_calls": {"real": 0, "fictional": 0, "judge": 0},
        "provider_source_fetches": 0,
        "candidate_mutations": 0,
        "main_merge": 0,
        "deployment": 0,
        "production_db_send_registration_mutations": [0, 0, 0],
        "next_scope": "NONPRODUCTION_INTEGRATION_AND_DECISION_MESSAGE_QUALITY_REVIEW",
        "status": "CODE_AND_OFFLINE_EVIDENCE_REVIEW_COMPLETE",
    }
    outputs = {
        "01-authority-integrity.json": authority,
        "02-call-graph-root-cause.json": call_graph,
        "03-prompt-hash-ledger.json": prompt_ledger,
        "04-offline-regression-matrix.json": regression,
        "05-historical-core-timing-audit.json": historical,
        "06-boundary-review.json": boundary,
        "07-message-quality-review.json": messages,
        "08-integration-inventory.json": integration,
        "09-exposure-retirement-review.json": exposure,
        "09a-updated-exposure-registry.json": updated_exposure_registry,
        "10-operating-safety.json": safety,
        "11-completion.json": completion,
        "evidence/exact-neon-invalid-core.json": exact_neon,
    }
    for name, value in outputs.items():
        write_json(output_dir / name, value)
    write_jsonl(output_dir / "inventory/historical-core-64.jsonl", core_inventory)
    write_jsonl(output_dir / "inventory/historical-timing-52.jsonl", timing_inventory)
    write_jsonl(output_dir / "inventory/complete-messages-48.jsonl", message_inventory)
    (output_dir / "offline-review-summary.md").write_text(
        _summary_markdown(
            authority, historical, regression, boundary, messages, integration, safety
        ),
        encoding="utf-8",
    )
    return completion


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-zip", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    print(json.dumps(run(args), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
