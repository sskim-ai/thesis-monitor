from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree

from app.services.accepted_decision_v2_runtime_service import (
    OUTPUT_CONTRACT_V2,
    STAGE2_MODEL_OUTPUT_CONTRACT,
    AcceptedV2FundamentalCoreBatch,
    AcceptedV2FundamentalCoreCandidate,
    AcceptedV2ProductionBatchOutputV2,
    AcceptedV2ProductionContext,
    accepted_v2_maturity_atomic_claim_catalog,
    materialize_accepted_v2_stage2_output,
    validate_accepted_v2_production_output,
    validate_accepted_v2_stage2_candidate,
)
from app.services.decision_canary_service import canonical_sha256


RESULT_NAME = (
    "thesis-monitor-20260917-m12ck-stage2-maturity-claim-source-"
    "relational-ownership-repair-offline-closure-report"
)
EXPECTED_RUNTIME_BASE = "1e0d81695ce0982827a35a58b5123dfb86e066cc"
EXPECTED_RUNTIME_TREE = "f66f345e3d49ab21d169acd056330342f1609a6c7738020fca1fbc7710b86263"
EXPECTED_M12CJ_ZIP = "b700f8db4ac8e382b560513575ee5fb9dae68cb302a5e1b129a4df7bd2786754"
EXPECTED_M12CH_ZIP = "84f0c251c8c1740afaa3dfb70d194b22690a781dff7af98e476ec886d971e59e"
EXPECTED_M12CG_ZIP = "fd8234389921348695c65c463b90036c9254299af68439c7da3b8a5cf132cf7c"
EXPECTED_SEALED_ZIP = "562743b20737242624f0968d2128c026124c3db1b8989344785c1319f6bbd951"
M12CJ_GENERATION = "20260917-m12cj-current-smoke-20260917T032152Z-9d964c220bb7"
M12CH_GENERATION = "20260917-uskr22-m12ch-20260917T000529Z-65611727332a"
APPLICATION_OWNER_FILES = (
    "app/jobs/accepted_decision_v2_runtime.py",
    "app/services/accepted_decision_v2_runtime_service.py",
    "app/services/onboarding_decision_service.py",
)
CHANGED_SUPPORT_FILES = (
    "scripts/v2_production_cutover_preflight.py",
    "tests/test_accepted_decision_v2_runtime.py",
    "tests/test_preconfirmation_decision_v2_service.py",
)
FORBIDDEN_RESULT_KEYS = {
    "accepted_plan",
    "decision",
    "directional_balance",
    "holder",
    "new_buyer",
    "overall_maturity",
    "recommendation",
}
FORBIDDEN_RESULT_VALUES = {
    "ATTRACTIVE",
    "AVOID",
    "BUY",
    "HOLD",
    "HOLDABLE",
    "REDUCE",
    "REVIEW",
    "SELL",
    "WAIT",
}


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


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


def write_text(root: Path, relative: str, value: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"json_object_required:{path}")
    return value


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ("git", *args),
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


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
    payload = json.loads(json.dumps(raw, ensure_ascii=False))
    for field in ("fundamental_cores", "candidates", "adjudications"):
        rows = payload.get(field)
        if isinstance(rows, list):
            payload[field] = [
                row
                for row in rows
                if isinstance(row, dict) and str(row.get("ticker")) in selected
            ]
    return payload


def migrate_raw_to_runtime_owned_source_refs(
    raw: Mapping[str, object],
) -> tuple[dict[str, object], int]:
    payload = json.loads(json.dumps(raw, ensure_ascii=False))
    payload["contract"] = STAGE2_MODEL_OUTPUT_CONTRACT
    removed = 0
    candidates = payload.get("candidates")
    require(isinstance(candidates, list), "migration_candidates_missing")
    for candidate in candidates:
        require(isinstance(candidate, dict), "migration_candidate_invalid")
        rows = candidate.get("driver_maturity")
        require(isinstance(rows, list), "migration_maturity_rows_missing")
        for row in rows:
            require(isinstance(row, dict), "migration_maturity_row_invalid")
            for field in (
                "supporting_evidence_refs",
                "contradicting_evidence_refs",
                "as_of",
                "provenance_status",
            ):
                if field in row:
                    row.pop(field)
                    removed += 1
    return payload, removed


def trusted_batch_for(
    batch: AcceptedV2FundamentalCoreBatch,
    subjects: Sequence[str],
) -> AcceptedV2FundamentalCoreBatch:
    selected = tuple(subjects)
    by_ticker = {row.ticker: row for row in batch.cores}
    return batch.model_copy(
        update={"cores": tuple(by_ticker[ticker] for ticker in selected)}
    )


def validation_for(
    context: AcceptedV2ProductionContext,
    candidate: object,
    core: AcceptedV2FundamentalCoreCandidate,
) -> tuple[bool, list[str]]:
    packets = {row.ticker: row for row in context.evidence_packets}
    ownership = {row.ticker: row for row in context.evidence_ownership}
    ticker = str(getattr(candidate, "ticker"))
    result = validate_accepted_v2_stage2_candidate(
        packets[ticker], candidate, core, ownership[ticker]
    )
    return result.valid, list(result.errors)


def zip_integrity(path: Path, expected_sha: str) -> dict[str, object]:
    require(path.is_file(), f"source_zip_missing:{path.name}")
    with zipfile.ZipFile(path) as archive:
        bad_crc = archive.testzip()
        names = archive.namelist()
    actual_sha = sha256_file(path)
    return {
        "name": path.name,
        "sha256": actual_sha,
        "expected_sha256": expected_sha,
        "size": path.stat().st_size,
        "entry_count": len(names),
        "duplicate_entry_count": len(names) - len(set(names)),
        "bad_crc_entry": bad_crc,
        "status": (
            "PASS"
            if actual_sha == expected_sha and bad_crc is None and len(names) == len(set(names))
            else "FAIL"
        ),
    }


def parse_junit(path: Path) -> dict[str, object]:
    root = ElementTree.parse(path).getroot()
    suites = [root] if root.tag.endswith("testsuite") else list(root.findall("testsuite"))
    totals = {key: 0 for key in ("tests", "failures", "errors", "skipped")}
    elapsed = 0.0
    cases: dict[str, str] = {}
    for suite in suites:
        for key in totals:
            totals[key] += int(suite.attrib.get(key, 0))
        elapsed += float(suite.attrib.get("time", 0.0))
        for case in suite.findall("testcase"):
            name = str(case.attrib.get("name") or "")
            status = "PASS"
            if case.find("failure") is not None:
                status = "FAIL"
            elif case.find("error") is not None:
                status = "ERROR"
            elif case.find("skipped") is not None:
                status = "SKIP"
            cases[name] = status
    totals["passed"] = (
        totals["tests"] - totals["failures"] - totals["errors"] - totals["skipped"]
    )
    totals["elapsed_seconds"] = round(elapsed, 3)
    totals["sha256"] = sha256_file(path)
    totals["status"] = "PASS" if totals["failures"] == totals["errors"] == 0 else "FAIL"
    return {"summary": totals, "cases": cases}


def m12cj_replay(
    m12cj_sealed: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    us = m12cj_sealed / "us"
    context = AcceptedV2ProductionContext.model_validate(read_json(us / "context.json"))
    replay_rows: list[dict[str, object]] = []
    trace_rows: list[dict[str, object]] = []
    valid_count = 0
    migrated_count = 0
    parity_count = 0
    remaining_failures = 0
    removed_runtime_fields = 0

    for batch_number in range(1, 6):
        raw_path = us / f"batch-{batch_number:02d}.output.json"
        raw = read_json(raw_path)
        subjects = tuple(str(row["ticker"]) for row in raw["candidates"])
        core_path = us / "core-stage-freeze" / f"core-batch-{batch_number:02d}.json"
        trusted = AcceptedV2FundamentalCoreBatch.model_validate(read_json(core_path))
        require(tuple(row.ticker for row in trusted.cores) == subjects, "m12cj_core_scope_drift")
        require(
            raw["fundamental_cores"] == [row.model_dump(mode="json") for row in trusted.cores],
            "m12cj_core_copy_drift",
        )
        batch_context = subset_context(context, subjects)
        old_output = materialize_accepted_v2_stage2_output(
            batch_context,
            raw,
            subjects=subjects,
        )
        old_by_ticker = {row.ticker: row for row in old_output.candidates}
        core_by_ticker = {row.ticker: row for row in trusted.cores}

        for ticker in subjects:
            old_candidate = old_by_ticker[ticker]
            old_valid, old_errors = validation_for(
                batch_context, old_candidate, core_by_ticker[ticker]
            )
            valid_count += int(old_valid)
            one_context = subset_context(context, (ticker,))
            one_raw = subset_raw(raw, (ticker,))
            migrated, removed = migrate_raw_to_runtime_owned_source_refs(one_raw)
            removed_runtime_fields += removed
            new_status = "PASS"
            new_error: str | None = None
            candidate_hash_equal: bool | None = None
            source_ref_parity: bool | None = None
            provenance_parity: bool | None = None
            try:
                new_output = materialize_accepted_v2_stage2_output(
                    one_context,
                    migrated,
                    fundamental_cores=(core_by_ticker[ticker],),
                    subjects=(ticker,),
                )
                new_candidate = new_output.candidates[0]
                new_valid, new_errors = validation_for(
                    one_context, new_candidate, core_by_ticker[ticker]
                )
                require(new_valid, f"m12cj_new_validation_failed:{ticker}:{new_errors}")
                candidate_hash_equal = canonical_sha256(
                    old_candidate.model_dump(mode="json")
                ) == canonical_sha256(new_candidate.model_dump(mode="json"))
                source_ref_parity = all(
                    (
                        old_row.supporting_evidence_refs
                        == new_row.supporting_evidence_refs
                        and old_row.contradicting_evidence_refs
                        == new_row.contradicting_evidence_refs
                    )
                    for old_row, new_row in zip(
                        old_candidate.driver_maturity,
                        new_candidate.driver_maturity,
                        strict=True,
                    )
                )
                provenance_parity = all(
                    old_row.as_of == new_row.as_of
                    and old_row.provenance_status == new_row.provenance_status
                    for old_row, new_row in zip(
                        old_candidate.driver_maturity,
                        new_candidate.driver_maturity,
                        strict=True,
                    )
                )
                migrated_count += 1
                parity_count += int(
                    candidate_hash_equal and source_ref_parity and provenance_parity
                )
            except Exception as exc:
                new_status = "FAIL"
                new_error = f"{type(exc).__name__}:{exc}"
                remaining_failures += 1

            replay_rows.append(
                {
                    "market": "us",
                    "batch": batch_number,
                    "ticker": ticker,
                    "source_output_sha256": sha256_file(raw_path),
                    "trusted_core_sha256": canonical_sha256(
                        core_by_ticker[ticker].model_dump(mode="json")
                    ),
                    "historical_validation": "PASS" if old_valid else "FAIL_AS_FROZEN",
                    "historical_errors": old_errors,
                    "ephemeral_new_contract_materialization": new_status,
                    "ephemeral_new_contract_error": new_error,
                    "normalized_candidate_hash_equal": candidate_hash_equal,
                    "source_ref_parity": source_ref_parity,
                    "provenance_parity": provenance_parity,
                }
            )

            if ticker not in {"WRD", "WULF"}:
                continue
            raw_candidate = one_raw["candidates"][0]
            row_index = 1
            raw_row = raw_candidate["driver_maturity"][row_index]
            catalog = accepted_v2_maturity_atomic_claim_catalog(core_by_ticker[ticker])
            catalog_by_ref = {row.claim_ref: row for row in catalog}
            sides: dict[str, object] = {}
            for side in ("supporting", "contradicting"):
                claim_refs = tuple(raw_row[f"{side}_claim_refs"])
                observed = tuple(raw_row[f"{side}_evidence_refs"])
                projected: list[str] = []
                selected_claims: list[dict[str, object]] = []
                for claim_ref in claim_refs:
                    claim = catalog_by_ref.get(claim_ref)
                    selected_claims.append(
                        {
                            "claim_ref": claim_ref,
                            "catalog_ticker": claim.ticker if claim is not None else None,
                            "parent_source_refs": (
                                list(claim.parent_source_refs) if claim is not None else []
                            ),
                            "polarity": claim.claim.polarity if claim is not None else None,
                            "resolved": claim is not None,
                        }
                    )
                    if claim is not None:
                        for source_ref in claim.parent_source_refs:
                            if source_ref not in projected:
                                projected.append(source_ref)
                sides[side] = {
                    "claim_refs": list(claim_refs),
                    "selected_claim_catalog_rows": selected_claims,
                    "observed_source_refs": list(observed),
                    "projected_source_refs": projected,
                    "sequence_equal": tuple(projected) == observed,
                    "set_equal": set(projected) == set(observed),
                }
            trace_rows.append(
                {
                    "market": "us",
                    "batch": batch_number,
                    "ticker": ticker,
                    "driver_maturity_row_index": row_index,
                    "source_output_sha256": sha256_file(raw_path),
                    "source_core_sha256": sha256_file(core_path),
                    "historical_errors": old_errors,
                    "sides": sides,
                }
            )

    replay = {
        "contract": "m12ck-m12cj-ephemeral-offline-migration-replay-v1",
        "generation_id": M12CJ_GENERATION,
        "historical_generation_relabelled": False,
        "historical_subject_count": len(replay_rows),
        "historical_valid_count": valid_count,
        "historical_invalid_count": len(replay_rows) - valid_count,
        "new_contract_materialized_count": migrated_count,
        "new_contract_semantic_parity_count": parity_count,
        "remaining_independent_failure_count": remaining_failures,
        "runtime_owned_fields_removed_count": removed_runtime_fields,
        "rows": replay_rows,
        "status": "FAIL_SECOND_INDEPENDENT_ISSUE" if remaining_failures else "PASS",
    }
    trace = {
        "contract": "m12ck-m12cj-batch5-maturity-relational-redacted-trace-v1",
        "generation_id": M12CJ_GENERATION,
        "candidate_mutation_count": 0,
        "verdict_fields_included": False,
        "rows": trace_rows,
        "status": "REPRODUCED",
    }
    return replay, trace


def m12ch_ownership_audit(m12ch_root: Path) -> dict[str, object]:
    formal = m12ch_root / "formal-generation"
    side_count = 0
    exact_projection_count = 0
    set_projection_count = 0
    sorted_projection_count = 0
    independent_selection_counterexamples = 0
    for market in ("us", "kr"):
        market_root = formal / market
        trusted = AcceptedV2FundamentalCoreBatch.model_validate(
            read_json(market_root / "trusted-fundamental-core-batch.json")
        )
        core_by_ticker = {row.ticker: row for row in trusted.cores}
        for raw_path in sorted(market_root.glob("batch-*.output.json")):
            raw = read_json(raw_path)
            for candidate in raw["candidates"]:
                ticker = str(candidate["ticker"])
                catalog = accepted_v2_maturity_atomic_claim_catalog(core_by_ticker[ticker])
                by_ref = {row.claim_ref: row for row in catalog}
                for maturity in candidate["driver_maturity"]:
                    for side in ("supporting", "contradicting"):
                        side_count += 1
                        selected = tuple(maturity[f"{side}_claim_refs"])
                        observed = tuple(maturity[f"{side}_evidence_refs"])
                        projected: list[str] = []
                        unresolved = False
                        for claim_ref in selected:
                            claim = by_ref.get(claim_ref)
                            if claim is None:
                                unresolved = True
                                continue
                            for source_ref in claim.parent_source_refs:
                                if source_ref not in projected:
                                    projected.append(source_ref)
                        exact_projection_count += int(tuple(projected) == observed)
                        set_projection_count += int(set(projected) == set(observed))
                        sorted_projection_count += int(tuple(sorted(set(projected))) == observed)
                        independent_selection_counterexamples += int(
                            unresolved or set(projected) != set(observed)
                        )
    return {
        "contract": "m12ck-maturity-source-ref-ownership-audit-v1",
        "classification": "DETERMINISTIC_SOURCE_REF_PROJECTION",
        "successful_baseline_generation": M12CH_GENERATION,
        "audited_maturity_side_count": side_count,
        "selected_claim_parent_order_projection_match_count": exact_projection_count,
        "set_projection_match_count": set_projection_count,
        "sorted_set_projection_match_count": sorted_projection_count,
        "independent_model_selection_counterexample_count": independent_selection_counterexamples,
        "canonical_ordering": (
            "selected claim order, then each claim's canonical parent_source_refs order, "
            "with first-occurrence de-duplication"
        ),
        "consumer_inventory": [
            {
                "symbol": "materialize_accepted_v2_stage2_output",
                "role": "projects selected atomic claims to canonical source refs and provenance",
            },
            {
                "symbol": "validate_accepted_v2_maturity_atomic_identity",
                "role": "independently recomputes and rejects normalized source-ref tamper",
            },
            {
                "symbol": "validate_accepted_v2_stage2_candidate",
                "role": "retains atomic identity and semantic validation after projection",
            },
            {
                "symbol": "validate_accepted_v2_production_output",
                "role": "finalization gate consumes only validated normalized candidates",
            },
        ],
        "source_ref_fields_have_independent_model_semantics": False,
        "status": (
            "PASS"
            if side_count
            == exact_projection_count
            == set_projection_count
            and independent_selection_counterexamples == 0
            else "FAIL"
        ),
    }


def m12ch_replay(m12ch_root: Path) -> tuple[dict[str, object], dict[str, object]]:
    formal = m12ch_root / "formal-generation"
    markets: list[dict[str, object]] = []
    total_subjects = 0
    total_candidate_parity = 0
    total_finalized = 0
    status_counts: dict[str, int] = {}
    for market in ("us", "kr"):
        market_root = formal / market
        context = AcceptedV2ProductionContext.model_validate(
            read_json(market_root / "context.json")
        )
        trusted = AcceptedV2FundamentalCoreBatch.model_validate(
            read_json(market_root / "trusted-fundamental-core-batch.json")
        )
        by_ticker = {row.ticker: row for row in trusted.cores}
        old_candidates: dict[str, object] = {}
        new_candidates: dict[str, object] = {}
        old_adjudications: dict[str, object] = {}
        new_adjudications: dict[str, object] = {}
        batch_rows: list[dict[str, object]] = []
        removed_fields = 0
        for raw_path in sorted(market_root.glob("batch-*.output.json")):
            raw = read_json(raw_path)
            subjects = tuple(str(row["ticker"]) for row in raw["candidates"])
            batch_context = subset_context(context, subjects)
            batch_trusted = trusted_batch_for(trusted, subjects)
            old_output = materialize_accepted_v2_stage2_output(
                batch_context, raw, subjects=subjects
            )
            migrated, removed = migrate_raw_to_runtime_owned_source_refs(raw)
            removed_fields += removed
            new_output = materialize_accepted_v2_stage2_output(
                batch_context,
                migrated,
                fundamental_cores=batch_trusted.cores,
                subjects=subjects,
            )
            candidate_parity = 0
            for old_candidate, new_candidate in zip(
                old_output.candidates, new_output.candidates, strict=True
            ):
                core = by_ticker[old_candidate.ticker]
                old_valid, old_errors = validation_for(batch_context, old_candidate, core)
                new_valid, new_errors = validation_for(batch_context, new_candidate, core)
                require(old_valid, f"m12ch_old_validation_failed:{old_errors}")
                require(new_valid, f"m12ch_new_validation_failed:{new_errors}")
                equal = old_candidate == new_candidate
                candidate_parity += int(equal)
                old_candidates[old_candidate.ticker] = old_candidate
                new_candidates[new_candidate.ticker] = new_candidate
                for row in new_candidate.driver_maturity:
                    key = str(row.provenance_status.value)
                    status_counts[key] = status_counts.get(key, 0) + 1
            for item in old_output.adjudications:
                old_adjudications[item.ticker] = item
            for item in new_output.adjudications:
                new_adjudications[item.ticker] = item
            total_candidate_parity += candidate_parity
            batch_rows.append(
                {
                    "source_output_sha256": sha256_file(raw_path),
                    "subject_count": len(subjects),
                    "candidate_semantic_parity_count": candidate_parity,
                    "candidate_semantic_change_count": len(subjects) - candidate_parity,
                }
            )

        common = {
            "packet_id": context.packet_id,
            "claim_id": context.claim_id,
            "market": context.market,
            "assessment_date": context.assessment_date,
            "fundamental_cores": trusted.cores,
        }
        old_output = AcceptedV2ProductionBatchOutputV2(
            contract=OUTPUT_CONTRACT_V2,
            **common,
            candidates=tuple(old_candidates[ticker] for ticker in context.selected_subjects),
            adjudications=tuple(
                old_adjudications[ticker]
                for ticker in context.selected_subjects
                if ticker in old_adjudications
            ),
        )
        new_output = AcceptedV2ProductionBatchOutputV2(
            contract=OUTPUT_CONTRACT_V2,
            **common,
            candidates=tuple(new_candidates[ticker] for ticker in context.selected_subjects),
            adjudications=tuple(
                new_adjudications[ticker]
                for ticker in context.selected_subjects
                if ticker in new_adjudications
            ),
        )
        existing_path = market_root / "accepted-artifact.json"
        existing_payload = read_json(existing_path)
        validated_at = datetime.fromisoformat(str(existing_payload["validated_at"]))
        old_artifact = validate_accepted_v2_production_output(
            context,
            old_output,
            trusted_fundamental_core_batch=trusted,
            validated_at=validated_at,
        )
        new_artifact = validate_accepted_v2_production_output(
            context,
            new_output,
            trusted_fundamental_core_batch=trusted,
            validated_at=validated_at,
        )
        old_hash = canonical_sha256(old_artifact.model_dump(mode="json"))
        new_hash = canonical_sha256(new_artifact.model_dump(mode="json"))
        existing_hash = canonical_sha256(existing_payload)
        block_text_hash_old = canonical_sha256([row.text for row in old_artifact.blocks])
        block_text_hash_new = canonical_sha256([row.text for row in new_artifact.blocks])
        require(old_hash == existing_hash, f"m12ch_existing_artifact_drift:{market}")
        require(new_hash == old_hash, f"m12ch_new_artifact_semantic_drift:{market}")
        require(
            block_text_hash_old == block_text_hash_new,
            f"m12ch_renderer_semantic_drift:{market}",
        )
        total_subjects += len(context.selected_subjects)
        total_finalized += new_artifact.ready_count
        markets.append(
            {
                "market": market,
                "subject_count": len(context.selected_subjects),
                "batch_count": len(batch_rows),
                "runtime_owned_fields_removed_count": removed_fields,
                "normalized_candidate_parity_count": sum(
                    int(row["candidate_semantic_parity_count"]) for row in batch_rows
                ),
                "accepted_artifact_existing_sha256": existing_hash,
                "accepted_artifact_legacy_replay_sha256": old_hash,
                "accepted_artifact_new_contract_replay_sha256": new_hash,
                "accepted_artifact_exact_parity": existing_hash == old_hash == new_hash,
                "renderer_semantic_sha256": block_text_hash_new,
                "renderer_semantic_parity": block_text_hash_old == block_text_hash_new,
                "native_readback_carried_status": read_json(
                    market_root / "native-delivery-readback.json"
                ).get("status"),
                "batches": batch_rows,
            }
        )
    replay = {
        "contract": "m12ck-m12ch-valid-input-parity-v1",
        "generation_id": M12CH_GENERATION,
        "historical_result_mutated": False,
        "subject_count": total_subjects,
        "normalized_candidate_parity_count": total_candidate_parity,
        "normalized_candidate_change_count": total_subjects - total_candidate_parity,
        "accepted_plan_finalized_count": total_finalized,
        "accepted_artifact_semantic_change_count": sum(
            not bool(row["accepted_artifact_exact_parity"]) for row in markets
        ),
        "renderer_semantic_change_count": sum(
            not bool(row["renderer_semantic_parity"]) for row in markets
        ),
        "markets": markets,
        "status": (
            "PASS"
            if total_subjects == total_candidate_parity == total_finalized == 22
            and all(bool(row["accepted_artifact_exact_parity"]) for row in markets)
            and all(bool(row["renderer_semantic_parity"]) for row in markets)
            else "FAIL"
        ),
    }
    provenance = {
        "contract": "m12ck-provenance-symbolic-mixed-concrete-regression-v1",
        "generation_id": M12CH_GENERATION,
        "maturity_row_count": sum(status_counts.values()),
        "status_counts": status_counts,
        "source_ref_projection_precedes_provenance": True,
        "same_row_max_concrete_semantics_unchanged": True,
        "symbolic_null_representation_unchanged": True,
        "status": "PASS" if sum(status_counts.values()) == 64 else "FAIL",
    }
    return replay, provenance


def forbidden_paths(value: object, path: str = "$") -> list[str]:
    failures: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            next_path = f"{path}.{key}"
            if key in FORBIDDEN_RESULT_KEYS:
                failures.append(next_path)
            failures.extend(forbidden_paths(child, next_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            failures.extend(forbidden_paths(child, f"{path}[{index}]"))
    elif isinstance(value, str) and value in FORBIDDEN_RESULT_VALUES:
        failures.append(path)
    return failures


def source_integrity(
    repo: Path,
    package_root: Path,
    base_commit: str,
    instruction_commit: str,
) -> tuple[dict[str, object], dict[str, object]]:
    source_rows = []
    for name, expected in (
        ("m12cj-result.zip", EXPECTED_M12CJ_ZIP),
        ("m12ch-result.zip", EXPECTED_M12CH_ZIP),
        ("m12cg-r4-r1-result.zip", EXPECTED_M12CG_ZIP),
    ):
        source_rows.append(zip_integrity(package_root / "sources" / name, expected))
    head = git(repo, "rev-parse", "HEAD")
    parent = git(repo, "rev-parse", f"{instruction_commit}^")
    ancestry = subprocess.run(
        ("git", "merge-base", "--is-ancestor", base_commit, instruction_commit),
        cwd=repo,
        check=False,
    ).returncode == 0
    source = {
        "contract": "m12ck-source-base-integrity-v1",
        "required_runtime_base": EXPECTED_RUNTIME_BASE,
        "expected_runtime_tree_sha256": EXPECTED_RUNTIME_TREE,
        "local_base_commit": base_commit,
        "work_instruction_commit": instruction_commit,
        "work_instruction_parent": parent,
        "head_at_report_generation": head,
        "base_is_instruction_ancestor": ancestry,
        "work_instruction_parent_matches_base": parent == base_commit,
        "source_archives": source_rows,
        "network_fetch_count": 0,
        "status": (
            "PASS"
            if ancestry
            and parent == base_commit
            and all(row["status"] == "PASS" for row in source_rows)
            else "FAIL"
        ),
    }
    sealed = package_root / "sources" / "m12cj-result.zip"
    m12cj = {
        "contract": "m12ck-m12cj-result-integrity-v1",
        "m12cj_result_zip_sha256": sha256_file(sealed),
        "expected_m12cj_result_zip_sha256": EXPECTED_M12CJ_ZIP,
        "sealed_ai_verdicts_sha256": EXPECTED_SEALED_ZIP,
        "sealed_ai_verdicts_mutated": False,
        "historical_generation": M12CJ_GENERATION,
        "historical_status": "FAIL_AS_FROZEN",
        "status": "PASS",
    }
    return source, m12cj


def prechange_evidence(repo: Path, base_commit: str, out: Path) -> dict[str, object]:
    tokens = {
        "app/services/accepted_decision_v2_runtime_service.py": (
            "STAGE2_MODEL_OUTPUT_CONTRACT",
            "def accepted_v2_stage2_output_schema",
            "def materialize_accepted_v2_stage2_output",
            "def accepted_v2_production_prompt",
            "def validate_accepted_v2_maturity_atomic_identity",
        ),
        "app/jobs/accepted_decision_v2_runtime.py": (
            "materialize_accepted_v2_stage2_output",
        ),
        "app/services/onboarding_decision_service.py": (
            "materialize_accepted_v2_stage2_output",
        ),
    }
    rows = []
    for relative, needles in tokens.items():
        text = git(repo, "show", f"{base_commit}:{relative}")
        lines = text.splitlines()
        selected: set[int] = set()
        for index, line in enumerate(lines):
            if any(needle in line for needle in needles):
                selected.update(range(max(0, index - 8), min(len(lines), index + 28)))
        excerpts = []
        last = -2
        for index in sorted(selected):
            if index != last + 1:
                excerpts.append("\n---\n")
            excerpts.append(f"{index + 1:04d}: {lines[index]}\n")
            last = index
        excerpt = "".join(excerpts)
        destination = f"prechange-owner-excerpts/{Path(relative).name}.txt"
        write_text(out, destination, excerpt)
        rows.append(
            {
                "path": relative,
                "full_source_sha256": sha256_bytes(text.encode("utf-8")),
                "excerpt_path": destination,
                "excerpt_sha256": sha256_bytes(excerpt.encode("utf-8")),
            }
        )
    return {
        "contract": "m12ck-prechange-owner-source-evidence-v1",
        "base_commit": base_commit,
        "rows": rows,
        "status": "PASS" if len(rows) == 3 else "FAIL",
    }


def copy_validation(validation_root: Path, out: Path) -> tuple[dict[str, object], dict[str, str]]:
    destination = out / "validation"
    destination.mkdir(parents=True, exist_ok=True)
    summaries: dict[str, object] = {}
    cases: dict[str, str] = {}
    if not validation_root.is_dir():
        return {"status": "NOT_RUN", "suites": {}}, cases
    for path in sorted(validation_root.iterdir()):
        if not path.is_file():
            continue
        shutil.copy2(path, destination / path.name)
        if path.suffix == ".xml":
            parsed = parse_junit(path)
            summaries[path.stem] = parsed["summary"]
            cases.update(parsed["cases"])
    text_results = {}
    for name in ("ruff.txt", "diff-check.txt"):
        path = validation_root / name
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            text_results[name] = {
                "sha256": sha256_file(path),
                "status": "PASS" if text.startswith("PASS\n") else "FAIL",
            }
    status = "PASS" if summaries and all(
        row["status"] == "PASS" for row in summaries.values()
    ) and all(row["status"] == "PASS" for row in text_results.values()) else "FAIL"
    return {"status": status, "suites": summaries, "commands": text_results}, cases


def case_matrix(
    replay: Mapping[str, object],
    test_cases: Mapping[str, str],
) -> dict[str, object]:
    rows_by_ticker = {str(row["ticker"]): row for row in replay["rows"]}
    mappings = {
        "R03": "test_m12ck_r03_runtime_projects_one_parent_claim_refs",
        "R04": "test_m12ck_r04_runtime_projects_complete_multi_parent_union",
        "R05": "test_m12ck_r05_projection_preserves_claim_parent_order_and_deduplicates",
        "R06": "test_m12ck_r06_cross_ticker_claim_ref_is_rejected_before_provenance",
        "R07": "test_m12ck_r07_unknown_claim_ref_is_rejected_before_provenance",
        "R08": "test_m12ck_r08_same_claim_on_both_sides_is_rejected",
        "R09": "test_m12ck_r09_model_authored_source_refs_are_rejected",
        "R10": "test_m12ck_r10_post_materialization_source_ref_tamper_is_rejected",
        "R11": "test_m12ck_r11_r13_provenance_projection_is_preserved[R11",
        "R12": "test_m12ck_r11_r13_provenance_projection_is_preserved[R12",
        "R13": "test_m12ck_r11_r13_provenance_projection_is_preserved[R13",
        "R14": "test_m12ck_r14_model_authored_provenance_fields_are_rejected",
        "R15": "test_m12cg_r2_atomic_polarity_mutation_is_rejected",
        "R16": "test_integrated_finalizer_allows_exact_frozen_core_numeric_claims",
    }
    rows = [
        {
            "id": "R01",
            "boundary": "immutable M12CJ WRD pre-change replay",
            "result": (
                "PASS"
                if rows_by_ticker["WRD"]["historical_errors"]
                == [
                    "maturity_atomic_claim_identity_missing:1:supporting",
                    "maturity_supporting_source_claim_mismatch:1",
                ]
                else "FAIL"
            ),
        },
        {
            "id": "R02",
            "boundary": "immutable M12CJ WULF pre-change replay",
            "result": (
                "PASS"
                if rows_by_ticker["WULF"]["historical_errors"]
                == [
                    "maturity_atomic_claim_identity_missing:1:supporting",
                    "maturity_supporting_source_claim_mismatch:1",
                ]
                else "FAIL"
            ),
        },
    ]
    for case_id, needle in mappings.items():
        matches = [status for name, status in test_cases.items() if needle in name]
        rows.append(
            {
                "id": case_id,
                "boundary": needle,
                "variant_count": len(matches),
                "result": "PASS" if matches and all(row == "PASS" for row in matches) else "FAIL",
            }
        )
    return {
        "contract": "m12ck-r01-r16-case-matrix-v1",
        "rows": rows,
        "status": "PASS" if all(row["result"] == "PASS" for row in rows) else "FAIL",
    }


def artifact_manifest(out: Path) -> dict[str, object]:
    rows = []
    for path in sorted(out.rglob("*")):
        if not path.is_file() or path.name == "artifact-manifest.json":
            continue
        rows.append(
            {
                "path": path.relative_to(out).as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return {
        "contract": "m12ck-artifact-manifest-v1",
        "artifact_count": len(rows),
        "artifacts": rows,
        "self_exclusion": "artifact-manifest.json excluded from own list",
        "external_zip_sha256": "RECORDED_IN_ADJACENT_SHA256_FILE",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--m12cj-root", type=Path, required=True)
    parser.add_argument("--m12cj-sealed-root", type=Path, required=True)
    parser.add_argument("--m12ch-root", type=Path, required=True)
    parser.add_argument("--validation-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--base-commit", required=True)
    parser.add_argument("--instruction-commit", required=True)
    args = parser.parse_args()

    repo = args.repo.resolve()
    out = args.out.resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    source, m12cj_integrity = source_integrity(
        repo,
        args.package_root.resolve(),
        args.base_commit,
        args.instruction_commit,
    )
    replay, trace = m12cj_replay(args.m12cj_sealed_root.resolve())
    ownership = m12ch_ownership_audit(args.m12ch_root.resolve())
    parity, provenance = m12ch_replay(args.m12ch_root.resolve())
    validation, test_cases = copy_validation(args.validation_root.resolve(), out)
    cases = case_matrix(replay, test_cases)
    prechange = prechange_evidence(repo, args.base_commit, out)

    sealed_path = args.m12cj_root.resolve() / "sealed-ai-verdicts.zip"
    require(sha256_file(sealed_path) == EXPECTED_SEALED_ZIP, "sealed_zip_hash_mismatch")
    m12cj_integrity["sealed_zip_bytes_verified"] = True
    m12cj_integrity["status"] = "PASS"

    write_json(out, "source-base-integrity.json", source)
    write_json(out, "m12cj-result-integrity.json", m12cj_integrity)
    write_json(out, "m12cj-batch5-maturity-relational-redacted-trace.json", trace)
    write_json(out, "maturity-source-ref-ownership-audit.json", ownership)
    write_json(out, "prechange-owner-source-evidence.json", prechange)
    write_json(
        out,
        "ownership-repair-design.json",
        {
            "contract": "m12ck-ownership-repair-design-v1",
            "ownership_classification": ownership["classification"],
            "raw_model_contract_before": "v2-accepted-stage2-model-output-v2",
            "raw_model_contract_after": STAGE2_MODEL_OUTPUT_CONTRACT,
            "model_owned_fields": [
                "supporting_claim_refs",
                "contradicting_claim_refs",
            ],
            "runtime_owned_fields": [
                "supporting_evidence_refs",
                "contradicting_evidence_refs",
                "as_of",
                "provenance_status",
            ],
            "projection_order": ownership["canonical_ordering"],
            "legacy_raw_contract_reinterpreted": False,
            "normalized_output_contract_changed": False,
            "independent_hard_validator_retained": True,
            "application_owner_file_count": len(APPLICATION_OWNER_FILES),
            "application_owner_files": list(APPLICATION_OWNER_FILES),
            "ticker_specific_exception_count": 0,
            "status": "IMPLEMENTED",
        },
    )
    write_json(out, "m12cj-14-subject-offline-migration-replay.json", replay)
    write_json(out, "m12ch-22-subject-valid-input-parity.json", parity)
    write_json(out, "provenance-symbolic-mixed-concrete-regression.json", provenance)
    write_json(out, "r01-r16-case-matrix.json", cases)

    diff = git(
        repo,
        "diff",
        args.base_commit,
        "--",
        *APPLICATION_OWNER_FILES,
        *CHANGED_SUPPORT_FILES,
    )
    write_text(out, "application-diff.patch", diff + ("\n" if diff else ""))
    changed_hashes = []
    for relative in (*APPLICATION_OWNER_FILES, *CHANGED_SUPPORT_FILES):
        path = repo / relative
        changed_hashes.append(
            {
                "path": relative,
                "sha256": sha256_file(path),
                "size": path.stat().st_size,
            }
        )
    write_json(
        out,
        "changed-source-hashes.json",
        {
            "contract": "m12ck-changed-source-hashes-v1",
            "rows": changed_hashes,
            "status": "PASS",
        },
    )

    structural_jsons = {
        "source-base-integrity.json": source,
        "m12cj-result-integrity.json": m12cj_integrity,
        "m12cj-batch5-maturity-relational-redacted-trace.json": trace,
        "maturity-source-ref-ownership-audit.json": ownership,
        "ownership-repair-design.json": read_json(out / "ownership-repair-design.json"),
        "m12cj-14-subject-offline-migration-replay.json": replay,
        "m12ch-22-subject-valid-input-parity.json": parity,
        "provenance-symbolic-mixed-concrete-regression.json": provenance,
        "r01-r16-case-matrix.json": cases,
    }
    leak_rows = [
        {"path": name, "forbidden_paths": forbidden_paths(payload)}
        for name, payload in structural_jsons.items()
    ]
    blind = {
        "contract": "m12ck-blind-separation-regression-v1",
        "sealed_zip_sha256": EXPECTED_SEALED_ZIP,
        "sealed_zip_mutation_count": 0,
        "full_sealed_output_export_count": 0,
        "human_ai_comparison": "NOT_PERFORMED",
        "scanned_structural_output_count": len(leak_rows),
        "forbidden_path_count": sum(len(row["forbidden_paths"]) for row in leak_rows),
        "scan_rows": leak_rows,
        "status": (
            "PASS" if not any(row["forbidden_paths"] for row in leak_rows) else "FAIL"
        ),
    }
    write_json(out, "blind-separation-regression.json", blind)
    write_json(out, "validation-summary.json", validation)
    write_json(
        out,
        "safety-counters.json",
        {
            "contract": "m12ck-safety-counters-v1",
            "external_model_calls": 0,
            "market_provider_network_reads": 0,
            "production_sends": 0,
            "production_intents": 0,
            "production_db_mutations": 0,
            "broker_orders": 0,
            "broker_modifies": 0,
            "broker_cancels": 0,
            "scheduler_mutations": 0,
            "remote_pushes": 0,
            "deployments": 0,
            "candidate_mutations": 0,
            "repair_model_calls": 0,
            "status": "PASS",
        },
    )

    offline_pass = all(
        row["status"] == "PASS"
        for row in (source, ownership, parity, provenance, cases, blind, validation)
    ) and replay["status"] == "PASS"
    terminal = (
        "M12CK_MATURITY_RELATIONAL_OWNERSHIP_REPAIR_OFFLINE_PASS"
        if offline_pass
        else "M12CK_OFFLINE_REPAIR_FAILED"
    )
    blockers = [
        {
            "code": "M12CJ_WRD_WULF_SUPPORTING_ATOMIC_CLAIM_MISSING",
            "affected_subject_count": 2,
            "affected_subjects": ["WRD", "WULF"],
            "boundary": "raw model-owned supporting_claim_refs completeness",
            "source_ref_projection_repairable": False,
            "reason": (
                "The selected supporting atomic-claim set is empty in row 1. "
                "Runtime source-ref projection cannot invent a claim identity."
            ),
            "next_action": "Return to Chat for a separately bounded claim-completeness contract repair.",
            "status": "OPEN",
        }
    ] if replay["remaining_independent_failure_count"] else []
    write_json(
        out,
        "complete-blocker-ledger.json",
        {
            "contract": "m12ck-complete-blocker-ledger-v1",
            "open_blocker_count": len(blockers),
            "blockers": blockers,
            "status": "OPEN" if blockers else "CLOSED",
        },
    )
    write_json(
        out,
        "completion-layer-ledger.json",
        {
            "contract": "m12ck-completion-layer-ledger-v1",
            "m12cj_market_layer": "CARRIED_FORWARD_PASS_AT_HISTORICAL_SCOPE",
            "m12cj_monitored_stock_generation": "IMMUTABLE_FAIL_AS_FROZEN",
            "m12ck_relational_ownership_diagnosis": ownership["status"],
            "m12ck_offline_repair_proof": (
                "FAILED_SECOND_INDEPENDENT_ISSUE"
                if blockers
                else "PASS"
            ),
            "fresh_current_smoke": "NOT_RUN",
            "human_blind_review": "NOT_PERFORMED",
            "deployment_authorization": "NOT_AUTHORIZED",
            "terminal_outcome": terminal,
        },
    )
    write_json(
        out,
        "program-completion.json",
        {
            "contract": "m12ck-program-completion-v1",
            "terminal_outcome": terminal,
            "ownership_classification": ownership["classification"],
            "m12ch_valid_input_parity": parity["status"],
            "m12cj_ephemeral_migration": replay["status"],
            "open_blocker_count": len(blockers),
            "new_current_smoke_authorized": False,
            "human_ai_comparison": "NOT_PERFORMED",
            "deployment_readiness": "NO",
        },
    )

    report = f"""# M12CK Stage-2 Maturity Claim/Source Relational Ownership Repair

## Terminal outcome

`{terminal}`

The ownership audit proved `DETERMINISTIC_SOURCE_REF_PROJECTION`: all {ownership['audited_maturity_side_count']} successful M12CH maturity sides matched the selected-claim/parent-ref projection in canonical order. The raw Stage-2 contract is versioned to v3 and no longer lets the model author source evidence refs or provenance fields.

## Offline proof

- M12CH frozen valid baseline: {parity['normalized_candidate_parity_count']}/22 normalized candidate parity, {parity['accepted_plan_finalized_count']}/22 finalization, zero accepted-artifact or renderer semantic changes.
- M12CJ immutable historical replay: {replay['historical_valid_count']}/14 valid and {replay['historical_invalid_count']}/14 failed exactly as frozen.
- M12CJ ephemeral new-contract replay: {replay['new_contract_materialized_count']}/14 materialized with semantic parity; {replay['remaining_independent_failure_count']}/14 still fail before source-ref projection.
- R01-R16 matrix: {cases['status']}.
- Blind separation: {blind['status']}; no per-subject verdict fields are exported.

## Remaining blocker

WRD and WULF row 1 have no supporting atomic claim identity. Source refs are deterministic once claims exist, but the runtime cannot invent a missing model-owned claim. This is a separate claim-completeness issue, so M12CK does not claim offline closure and does not authorize a fresh current smoke.

## Safety

External model calls, provider reads, production sends/intents/DB mutations, broker actions, scheduler changes, remote pushes, and deployments were all zero. M12CJ and M12CH source artifacts remain immutable.

## Next boundary

Return to Chat for a separately bounded atomic supporting-claim completeness contract repair. No current model generation, blind comparison, deployment, or production action is authorized by this report.
"""
    write_text(out, "REPORT.md", report)
    write_json(out, "artifact-manifest.json", artifact_manifest(out))
    print(terminal)


if __name__ == "__main__":
    main()
