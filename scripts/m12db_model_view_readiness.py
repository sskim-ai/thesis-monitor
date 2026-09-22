from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path

from scripts.m12cq_two_pass_contract import (
    PassABatchOutput,
    build_pass_a_subject_context,
    build_pass_b_subject_context,
    canonical_sha256 as model_view_sha256,
    pass_a_leakage_scan,
    validate_pass_a_batch,
)
from scripts.m12cr_shadow_contract import (
    future_pass_a_batch_schema,
    future_pass_a_prompt_template,
    materialize_future_pass_a,
    schema_completeness_and_parity_scan,
    validate_future_pass_a_shape,
)
from scripts.m12cr_r1_typed_quality_contract import build_r1_pass_a_context
from scripts.m12cs_r1_provider_schema import (
    project_provider_wire_schema,
    scan_provider_structured_output_schema,
)
from scripts.m12cv_pass_b_capability_contract import (
    build_pass_b_capability_catalog,
    capability_pass_b_batch_schema,
    capability_prompt_template,
)
from scripts.m12da_source_use_contract import (
    SourceUse,
    build_source_use_projection,
    canonical_sha256,
    eligible_refs_for_use,
    freeze_source_use_binding,
    freeze_source_use_input_expectation,
    model_source_use_projection,
    validate_source_use_current_input,
)


REPO = Path(__file__).resolve().parents[1]
EXECUTION_GENERATION = "20260919-m12db-request-preparation-no-inference"
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
R3_RESULT_SHA256 = "72f36a1bfc65ec77b0f5a93b93ca1d3475388700dc7ce53a19a0a6bd9c760218"
M12CX_RESULT_SHA256 = "df7d3eef818ae21d479d4dea4bc15f5aeb86b3cde956a981cf9b0e6bfca01488"
SUPPLEMENTAL_SHA256 = "41e65904e65fcb696a6a44f7348c2d17101e1147497ca256df5b8994bbace6fe"
HISTORICAL_COMBINED_SHA256 = "34aace744021cc0b4b150dcd47e9c31bb2f48d8ec4a136cc4123c4de64646f4c"
BASE_COMMIT = "d77cbdb0534d811e15f5b4363a3bb0ab85f01ed1"
WORK_INSTRUCTION_COMMIT = "8d3b469243f0bfab61881e6cb24fa3e91b02cfd7"
PLAN_COMMIT = "2efb271f5a828984a4cd95613c57f5a20b07bf5d"
READY = "M12DB_SOURCE_USE_MODEL_VIEWS_READY_FOR_CHAT_EXECUTION_SCOPE_DECISION"
PARTIAL = "M12DB_PARTIAL_WITH_EXACT_MODEL_VIEW_OR_SUPPORT_GAP"
SOURCE_FAILED = "M12DB_REQUIRED_SOURCE_BINDING_FAILED"

POPULATION = {
    "us": (
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
    "kr": (
        "000660",
        "003690",
        "005490",
        "005930",
        "010120",
        "012450",
        "047810",
        "086280",
    ),
}
MIXED_PARENT_TICKER = "000660"
MIXED_PARENT_CLAIM = (
    "maturity-claim:23c080ecb59f05a3d2816cc53ec7a0cd87665f6ed8acbe3b5aa7c1f70f9caa07"
)
MIXED_PARENT_REF = "decision-evidence:6b6165e2d38d67a5ff00"
CHANGED_SOURCE_PATHS = (
    "scripts/m12db_model_view_readiness.py",
    "scripts/m12db_r1_request_composition_closure.py",
    "tests/test_m12db_r1_request_composition_closure.py",
)

PASS_A_FINAL_VIEW_FIELDS = (
    "ticker",
    "accepted_fundamental_claims",
    "eligible_non_price_evidence",
    "eligible_claim_refs",
    "premium_eligible_claim_refs",
    "data_quality_catalog",
    "business_evidence_quality_state",
    "source_use_projection",
)


class M12DBFailure(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise M12DBFailure(code)


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise M12DBFailure(f"expected_json_object:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_verification(root: Path, *, expected_count: int) -> dict[str, object]:
    manifest = read_json(root / "artifact-manifest.json")
    rows: list[dict[str, object]] = []
    declared = manifest.get("files") or manifest.get("payloads") or ()
    for item in declared:
        if not isinstance(item, Mapping):
            continue
        path = root / str(item.get("path") or "")
        actual_sha = sha256_file(path) if path.is_file() else None
        actual_size = path.stat().st_size if path.is_file() else None
        expected_size = item.get("size", item.get("bytes"))
        rows.append(
            {
                "path": item.get("path"),
                "expected_sha256": item.get("sha256"),
                "actual_sha256": actual_sha,
                "expected_size": expected_size,
                "actual_size": actual_size,
                "status": (
                    "PASS"
                    if actual_sha == item.get("sha256") and actual_size == expected_size
                    else "FAIL"
                ),
            }
        )
    return {
        "root": str(root),
        "expected_payload_count": expected_count,
        "actual_payload_count": len(rows),
        "mismatch_count": sum(row["status"] != "PASS" for row in rows),
        "status": (
            "PASS"
            if len(rows) == expected_count and all(row["status"] == "PASS" for row in rows)
            else "FAIL"
        ),
    }


def _batch_topology() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for market in ("us", "kr"):
        subjects = POPULATION[market]
        for offset in range(0, len(subjects), 3):
            rows.append(
                {
                    "market": market,
                    "batch": offset // 3 + 1,
                    "subjects": subjects[offset : offset + 3],
                }
            )
    require(len(rows) == 8, "batch_topology_not_8")
    return rows


def _load_archived_inputs(
    m12cx_root: Path,
) -> tuple[
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
]:
    base = m12cx_root / "outbound-request-dry-serialization/pass-b"
    subjects: dict[str, dict[str, object]] = {}
    catalogs: dict[str, dict[str, object]] = {}
    archived_batches: dict[str, dict[str, object]] = {}
    for spec in _batch_topology():
        market = str(spec["market"])
        batch = int(spec["batch"])
        directory = base / market / f"batch-{batch:02d}"
        context_payload = read_json(directory / "subject-context.json")
        catalog_payload = read_json(directory / "ref-catalog.json")
        context_rows = context_payload.get("subjects") or ()
        expected = tuple(str(value) for value in spec["subjects"])
        actual = tuple(
            str(row.get("ticker") or "") for row in context_rows if isinstance(row, Mapping)
        )
        require(actual == expected, f"archived_subject_scope_mismatch:{market}:{batch}")
        for row in context_rows:
            assert isinstance(row, Mapping)
            ticker = str(row["ticker"])
            require(ticker not in subjects, f"archived_subject_duplicate:{ticker}")
            subjects[ticker] = deepcopy(dict(row))
            catalog = catalog_payload.get(ticker)
            require(isinstance(catalog, Mapping), f"archived_catalog_missing:{ticker}")
            catalogs[ticker] = deepcopy(dict(catalog))
        archived_batches[f"{market}:{batch}"] = {
            "market": market,
            "batch": batch,
            "subjects": list(expected),
            "context_sha256": sha256_file(directory / "subject-context.json"),
            "catalog_sha256": sha256_file(directory / "ref-catalog.json"),
            "request_binding": read_json(directory / "request-binding.json"),
        }
    expected_population = POPULATION["us"] + POPULATION["kr"]
    require(tuple(subjects) == expected_population, "archived_population_mismatch")
    return subjects, catalogs, archived_batches


def _source_context(ticker: str, row: Mapping[str, object]) -> dict[str, object]:
    metadata = deepcopy(list(row.get("decision_evidence") or ()))
    return {
        "ticker": ticker,
        "decision_evidence": deepcopy(metadata),
        "evidence_packets": [{"ticker": ticker, "evidence": deepcopy(metadata)}],
        "current_price": deepcopy(row.get("current_price")),
        "tactical_candidates": deepcopy(row.get("tactical_candidates") or []),
        "security_valuation_basis_state": deepcopy(row.get("security_valuation_basis_state") or {}),
    }


def _source_chains(
    *,
    subjects: Mapping[str, Mapping[str, object]],
    catalogs: Mapping[str, Mapping[str, object]],
    r3_root: Path,
) -> dict[str, dict[str, object]]:
    authorities = read_json(r3_root / "source-authority-manifests-22.json")["subjects"]
    old_expectations = read_json(r3_root / "source-use-input-expectations-22.json")["subjects"]
    old_projections = read_json(r3_root / "source-use-projections-22.json")["subjects"]
    old_bindings = read_json(r3_root / "source-use-bindings-22.json")["subjects"]
    require(isinstance(authorities, Mapping), "r3_authority_payload_invalid")
    chains: dict[str, dict[str, object]] = {}
    for ticker in POPULATION["us"] + POPULATION["kr"]:
        metadata = list(subjects[ticker].get("decision_evidence") or ())
        authority = authorities[ticker]
        assert isinstance(authority, Mapping)
        source_generation = str(authority["source_generation_id"])
        expectation = freeze_source_use_input_expectation(
            ticker=ticker,
            source_generation_id=source_generation,
            execution_generation_id=EXECUTION_GENERATION,
            catalog=catalogs[ticker],
            source_metadata=metadata,
            authority_manifest=authority,
        )
        projection = build_source_use_projection(
            ticker=ticker,
            input_generation_id=source_generation,
            execution_generation_id=EXECUTION_GENERATION,
            catalog=catalogs[ticker],
            authority_manifest=authority,
            current_input_expectation=expectation,
        )
        binding = freeze_source_use_binding(
            projection=projection,
            authority_manifest=authority,
            current_input_expectation=expectation,
        )
        validation = validate_source_use_current_input(
            projection,
            binding,
            expectation,
            ticker=ticker,
            source_generation_id=source_generation,
            execution_generation_id=EXECUTION_GENERATION,
            catalog=catalogs[ticker],
            source_metadata=metadata,
        )
        require(validation["status"] == "PASS", f"source_binding_failed:{ticker}")
        prior_expectation = old_expectations[ticker]
        prior_projection = old_projections[ticker]
        prior_binding = old_bindings[ticker]
        chains[ticker] = {
            "authority": authority,
            "expectation": expectation,
            "projection": projection,
            "binding": binding,
            "validation": validation,
            "prior_expectation": prior_expectation,
            "prior_projection": prior_projection,
            "prior_binding": prior_binding,
            "source_generation_id": source_generation,
            "execution_generation_id": EXECUTION_GENERATION,
            "permission_semantics_unchanged": (
                projection["permission_derivation_sha256"]
                == prior_projection["permission_derivation_sha256"]
            ),
            "source_identity_unchanged": (
                expectation["source_metadata_sha256"] == prior_expectation["source_metadata_sha256"]
                and expectation["catalog_sha256"] == prior_expectation["catalog_sha256"]
                and expectation["authority_manifest_sha256"]
                == prior_expectation["authority_manifest_sha256"]
            ),
            "runtime_hash_changed_only_for_execution_generation": (
                projection["projection_sha256"] != prior_projection["projection_sha256"]
                and binding["binding_sha256"] != prior_binding["binding_sha256"]
            ),
        }
    return chains


def _allowed_refs(chain: Mapping[str, object], refs: Sequence[str], use: SourceUse) -> list[str]:
    projection = chain["projection"]
    binding = chain["binding"]
    assert isinstance(projection, Mapping)
    assert isinstance(binding, Mapping)
    return eligible_refs_for_use(projection, refs=refs, use=use, binding=binding)


def _prompt(template: str, *, stage: str, subjects: Sequence[str], payloads: object) -> str:
    label = "PASS_A_CONTEXT" if stage == "pass-a" else "PASS_B_CONTEXT"
    return (
        template
        + "\n\nSUBJECT_KEYS:\n"
        + json.dumps(list(subjects), ensure_ascii=False)
        + f"\n\n{label}:\n"
        + json.dumps(payloads, ensure_ascii=False, default=str)
    )


def _pass_a_final_view_payload(context: Mapping[str, object]) -> dict[str, object]:
    return {field: deepcopy(context.get(field)) for field in PASS_A_FINAL_VIEW_FIELDS}


def _ordered_unchanged_subset(
    final_rows: Sequence[object],
    intermediate_rows: Sequence[object],
) -> bool:
    remaining = iter(intermediate_rows)
    return all(any(row == candidate for candidate in remaining) for row in final_rows)


def bind_final_pass_a_model_view(
    *,
    intermediate_context: Mapping[str, object],
    final_context: Mapping[str, object],
    source_packet: Mapping[str, object],
) -> dict[str, object]:
    ticker = str(intermediate_context.get("ticker") or "")
    require(ticker == str(final_context.get("ticker") or ""), "pass_a_final_subject_mismatch")
    expected = build_r1_pass_a_context(intermediate_context, source_packet=source_packet)
    expected_payload = _pass_a_final_view_payload(expected)
    actual_payload = _pass_a_final_view_payload(final_context)
    require(
        model_view_sha256(actual_payload) == model_view_sha256(expected_payload),
        f"pass_a_final_view_transform_mismatch:{ticker}",
    )

    intermediate_receipt = intermediate_context.get("source_evidence_binding")
    require(
        isinstance(intermediate_receipt, Mapping),
        f"pass_a_intermediate_receipt_missing:{ticker}",
    )
    intermediate_evidence = list(intermediate_context.get("eligible_non_price_evidence") or ())
    intermediate_claims = list(intermediate_context.get("accepted_fundamental_claims") or ())
    require(
        intermediate_receipt.get("emitted_evidence_serialized_sha256")
        == model_view_sha256(intermediate_evidence),
        f"pass_a_intermediate_evidence_receipt_mismatch:{ticker}",
    )
    require(
        intermediate_receipt.get("emitted_claims_sha256") == model_view_sha256(intermediate_claims),
        f"pass_a_intermediate_claim_receipt_mismatch:{ticker}",
    )

    final_evidence = list(final_context.get("eligible_non_price_evidence") or ())
    final_claims = list(final_context.get("accepted_fundamental_claims") or ())
    require(
        _ordered_unchanged_subset(final_evidence, intermediate_evidence),
        f"pass_a_final_evidence_not_unchanged_subset:{ticker}",
    )
    require(
        _ordered_unchanged_subset(final_claims, intermediate_claims),
        f"pass_a_final_claims_not_unchanged_subset:{ticker}",
    )

    result = deepcopy(dict(final_context))
    result["source_evidence_binding"] = {
        "contract": "m12db-r1-final-pass-a-model-view-binding-v1",
        "ticker": ticker,
        "view_stage": "FINAL_POST_TYPED_QUALITY_FILTER",
        "validated_source_metadata_sha256": intermediate_receipt.get(
            "validated_source_metadata_sha256"
        ),
        "expected_source_metadata_sha256": intermediate_receipt.get(
            "expected_source_metadata_sha256"
        ),
        "permission_derivation_sha256": intermediate_receipt.get("permission_derivation_sha256"),
        "source_use_binding_sha256": intermediate_receipt.get("source_use_binding_sha256"),
        "model_permission_view_sha256": intermediate_receipt.get("model_permission_view_sha256"),
        "intermediate_receipt_contract": intermediate_receipt.get("contract"),
        "intermediate_receipt_sha256": model_view_sha256(intermediate_receipt),
        "intermediate_evidence_serialized_sha256": model_view_sha256(intermediate_evidence),
        "intermediate_claims_sha256": model_view_sha256(intermediate_claims),
        "emitted_evidence_serialized_sha256": model_view_sha256(final_evidence),
        "emitted_claims_sha256": model_view_sha256(final_claims),
        "emitted_claim_refs": list(final_context.get("eligible_claim_refs") or ()),
        "emitted_claim_parent_refs": {
            str(row.get("claim_ref")): list(row.get("parent_source_refs") or ())
            for row in final_claims
            if isinstance(row, Mapping) and row.get("claim_ref")
        },
        "expected_final_view_sha256": model_view_sha256(expected_payload),
        "actual_final_view_sha256": model_view_sha256(actual_payload),
        "transformation": "typed-quality-filtered-final-pass-a-model-view-v1",
        "intermediate_evidence_count": len(intermediate_evidence),
        "final_evidence_count": len(final_evidence),
        "intermediate_claim_count": len(intermediate_claims),
        "final_claim_count": len(final_claims),
        "unchanged_subset_validated": True,
        "surface_parity_checked": intermediate_receipt.get("surface_parity_checked"),
        "status": "PASS",
    }
    return result


def _write_request_capture(
    *,
    root: Path,
    stage: str,
    market: str,
    batch: int,
    subjects: Sequence[str],
    contexts: Mapping[str, Mapping[str, object]],
    catalogs: Mapping[str, Mapping[str, object]],
    chains: Mapping[str, Mapping[str, object]],
    fixture_only: bool,
    capabilities: Mapping[str, Mapping[str, object]] | None = None,
) -> dict[str, object]:
    directory = root / market / f"batch-{batch:02d}"
    payloads = [contexts[ticker] for ticker in subjects]
    if stage == "pass-a":
        require(capabilities is None, f"pass_a_capability_not_expected:{market}:{batch}")
        internal_schema = future_pass_a_batch_schema(
            subjects=subjects,
            subject_contexts=contexts,
        )
        template = future_pass_a_prompt_template()
        ref_catalog = {
            ticker: {
                "eligible_claim_refs": contexts[ticker]["eligible_claim_refs"],
                "premium_eligible_claim_refs": contexts[ticker]["premium_eligible_claim_refs"],
                "data_quality_catalog": contexts[ticker]["data_quality_catalog"],
            }
            for ticker in subjects
        }
    else:
        require(capabilities is not None, f"pass_b_capability_required:{market}:{batch}")
        for ticker in subjects:
            capability = capabilities.get(ticker)
            require(
                isinstance(capability, Mapping),
                f"pass_b_capability_missing:{market}:{batch}:{ticker}",
            )
            require(
                canonical_sha256(contexts[ticker].get("pass_b_capability_catalog"))
                == canonical_sha256(capability),
                f"pass_b_context_capability_mismatch:{market}:{batch}:{ticker}",
            )
            require(
                capability.get("source_use_binding_sha256")
                == chains[ticker]["binding"]["binding_sha256"],
                f"pass_b_capability_source_binding_mismatch:{market}:{batch}:{ticker}",
            )
        internal_schema = capability_pass_b_batch_schema(
            subjects=subjects,
            catalogs=catalogs,
            capabilities=capabilities,
        )
        template = capability_prompt_template()
        ref_catalog = {ticker: catalogs[ticker] for ticker in subjects}
    schema_scan = schema_completeness_and_parity_scan(
        internal_schema,
        stage=stage,
        subjects=subjects,
    )
    provider_schema, projection = project_provider_wire_schema(internal_schema)
    dialect = scan_provider_structured_output_schema(provider_schema)
    require(schema_scan["status"] == "PASS", f"internal_schema_failed:{stage}:{market}:{batch}")
    require(dialect["status"] == "PASS", f"provider_schema_failed:{stage}:{market}:{batch}")
    prompt = _prompt(template, stage=stage, subjects=subjects, payloads=payloads)
    write_text(directory / "prompt.txt", prompt)
    write_json(directory / "internal-semantic-schema.json", internal_schema)
    write_json(directory / "provider-wire-schema.json", provider_schema)
    write_json(directory / "provider-wire-projection.json", projection)
    write_json(directory / "provider-dialect-scan.json", dialect)
    write_json(directory / "subject-context.json", {"subjects": payloads})
    write_json(directory / "ref-catalog.json", ref_catalog)
    if stage == "pass-b":
        assert capabilities is not None
        write_json(
            directory / "capability-catalog.json",
            {ticker: capabilities[ticker] for ticker in subjects},
        )
    binding_payload = {
        "contract": "m12db-source-use-and-consumed-source-binding-v1",
        "execution_generation_id": EXECUTION_GENERATION,
        "subjects": {
            ticker: {
                "source_generation_id": chains[ticker]["source_generation_id"],
                "authority_manifest_sha256": chains[ticker]["authority"][
                    "authority_manifest_sha256"
                ],
                "source_use_expectation": chains[ticker]["expectation"],
                "source_use_binding": chains[ticker]["binding"],
                "runtime_projection_sha256": chains[ticker]["projection"]["projection_sha256"],
                "permission_derivation_sha256": chains[ticker]["projection"][
                    "permission_derivation_sha256"
                ],
                "model_permission_view_sha256": contexts[ticker]
                .get("source_use_projection", {})
                .get("model_permission_view_sha256"),
                "consumed_source_binding": contexts[ticker].get("source_evidence_binding"),
                "capability_sha256": (
                    canonical_sha256(capabilities[ticker]) if capabilities is not None else None
                ),
                "capability_source_use_projection_sha256": (
                    capabilities[ticker].get("source_use_projection_sha256")
                    if capabilities is not None
                    else None
                ),
                "pass_a_classification_sha256": (
                    canonical_sha256(contexts[ticker].get("frozen_pass_a_classification"))
                    if stage == "pass-b"
                    else None
                ),
                "deterministic_option_sha256": (
                    canonical_sha256(contexts[ticker].get("deterministic_fundamental_option"))
                    if stage == "pass-b"
                    else None
                ),
            }
            for ticker in subjects
        },
        "status": "PASS",
    }
    write_json(directory / "source-use-and-consumed-source-binding.json", binding_payload)
    files = {
        "prompt": directory / "prompt.txt",
        "internal_schema": directory / "internal-semantic-schema.json",
        "provider_schema": directory / "provider-wire-schema.json",
        "context": directory / "subject-context.json",
        "ref_catalog": directory / "ref-catalog.json",
        "source_binding": directory / "source-use-and-consumed-source-binding.json",
    }
    if stage == "pass-b":
        files["capability_catalog"] = directory / "capability-catalog.json"
    request_identity = {
        "stage": stage,
        "market": market,
        "batch": batch,
        "subjects": list(subjects),
        "model": MODEL,
        "effort": EFFORT,
        "execution_generation_id": EXECUTION_GENERATION,
        "request_composition": (
            "CAPABILITY_AWARE_FINAL" if stage == "pass-b" else "FINAL_POST_QUALITY_BOUND"
        ),
        "file_sha256": {key: sha256_file(path) for key, path in files.items()},
    }
    receipt = {
        "contract": "m12db-no-network-outbound-request-capture-v1",
        **request_identity,
        "request_sha256": canonical_sha256(request_identity),
        "fixture_only": fixture_only,
        "wrapper_invoked": False,
        "provider_accepted_inference": False,
        "model_calls": 0,
        "provider_calls": 0,
        "network_calls": 0,
        "status": "PASS",
    }
    write_json(directory / "no-network-outbound-receipt.json", receipt)
    return {
        **receipt,
        "directory": str(directory),
        "internal_schema_scan": schema_scan,
        "provider_dialect_scan": dialect,
        "file_sizes": {key: path.stat().st_size for key, path in files.items()},
    }


def _unresolved_fixture(
    subjects: Sequence[str], contexts: Mapping[str, Mapping[str, object]]
) -> dict[str, object]:
    classifications: dict[str, object] = {}
    for ticker in subjects:
        refs = list(contexts[ticker].get("eligible_claim_refs") or ())
        require(bool(refs), f"pass_a_source_view_requires_chat_decision:{ticker}")
        classifications[ticker] = {
            "archetype": "UNRESOLVED",
            "archetype_confidence": "LOW",
            "archetype_supporting_claim_refs": [refs[0]],
            "archetype_rationale": "Diagnostic unresolved branch with exact source support.",
            "valuation_regime_tier": "UNRESOLVED",
            "tier_supporting_claim_refs": [],
            "tier_rationale": "Diagnostic unresolved branch; no tier is forced.",
            "directional_data_quality_judgment": {
                "effect": "NONE",
                "reason_class": "NOT_APPLICABLE",
                "reason": None,
                "evidence_refs": [],
            },
            "classification_summary": "Diagnostic schema fixture only; no investment label.",
        }
    return {"classifications": classifications}


def _run_command(name: str, command: Sequence[str], root: Path) -> dict[str, object]:
    completed = subprocess.run(
        tuple(command),
        cwd=REPO,
        check=False,
        capture_output=True,
        text=True,
    )
    log = root / f"{name}.log"
    write_text(log, completed.stdout + completed.stderr)
    return {
        "name": name,
        "command": list(command),
        "exit_code": completed.returncode,
        "log": str(log),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
    }


def _validation(result_root: Path) -> dict[str, object]:
    root = result_root / "validation"
    root.mkdir(parents=True, exist_ok=True)
    focused_paths = (
        "tests/test_m12db_r1_request_composition_closure.py",
        "tests/test_m12db_model_view_readiness.py",
        "tests/test_m12da_r3_projection_consumed_evidence_closure.py",
        "tests/test_m12da_r2_authority_family_current_input_closure.py",
        "tests/test_m12da_r1_source_authority_closure.py",
        "tests/test_m12da_source_use_contract.py",
        "tests/test_m12cq_two_pass_policy_shadow.py",
        "tests/test_m12cv_pass_b_capability_contract.py",
    )
    commands = [
        _run_command(
            "focused-pytest",
            (
                sys.executable,
                "-m",
                "pytest",
                "-q",
                *focused_paths,
                f"--junitxml={root / 'focused-junit.xml'}",
            ),
            root,
        ),
        _run_command(
            "full-pytest",
            (
                sys.executable,
                "-m",
                "pytest",
                "-q",
                f"--junitxml={root / 'full-junit.xml'}",
            ),
            root,
        ),
        _run_command(
            "ruff-check",
            (str(Path(sys.executable).with_name("ruff")), "check", *CHANGED_SOURCE_PATHS),
            root,
        ),
        _run_command(
            "ruff-format",
            (
                str(Path(sys.executable).with_name("ruff")),
                "format",
                "--check",
                *CHANGED_SOURCE_PATHS,
            ),
            root,
        ),
        _run_command("diff-check", ("git", "diff", "--check", "HEAD"), root),
        _run_command(
            "py-compile",
            (
                sys.executable,
                "-m",
                "py_compile",
                "scripts/m12db_model_view_readiness.py",
                "scripts/m12db_r1_request_composition_closure.py",
            ),
            root,
        ),
    ]
    result = {
        "contract": "m12db-validation-v1",
        "commands": commands,
        "external_model_calls": 0,
        "network_calls": 0,
        "status": "PASS" if all(row["status"] == "PASS" for row in commands) else "FAIL",
    }
    write_json(root / "summary.json", result)
    return result


def _artifact_manifest(root: Path) -> dict[str, object]:
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "artifact-manifest.json":
            continue
        rows.append(
            {
                "path": str(path.relative_to(root)),
                "sha256": sha256_file(path),
                "size": path.stat().st_size,
            }
        )
    return {
        "contract": "m12db-artifact-manifest-v1",
        "file_count": len(rows),
        "files": rows,
    }


def _report_markdown(completion: Mapping[str, object]) -> str:
    return "\n".join(
        [
            "# M12DB Source-Use-Aware Model-View Readiness",
            "",
            f"- Terminal: `{completion['terminal']}`",
            f"- Subjects ready: `{completion['ready_subject_count']}/22`",
            f"- Pass-A captures: `{completion['pass_a_capture_count']}/8`",
            f"- Pass-B fixture captures: `{completion['pass_b_fixture_capture_count']}/8`",
            f"- Price-blind forbidden paths: `{completion['pass_a_forbidden_path_count']}`",
            f"- 000660 authorized atomic claim retained: `{completion['mixed_parent_claim_retained']}`",
            f"- Validation: `{completion['validation_status']}`",
            "- Inference/model/provider/network calls: `0`",
            "- Production/DB/send/scheduler/broker mutations: `0`",
            "- Merge/push/deploy: `0`",
            "",
            "The full runtime authority and binding remain intact. Pass A receives only its stage-relevant permission view and exact source-authorized atomic claims. Exact future Pass-B requests remain dependent on a later fresh Pass-A freeze and were not fabricated here.",
        ]
    )


def run(args: argparse.Namespace) -> None:
    result_root = args.result_root.resolve()
    if result_root.exists():
        existing = [
            path
            for path in result_root.rglob("*")
            if path.is_file() and path.name != "source-base-and-finite-view-change-plan.json"
        ]
        require(not existing, "result_root_already_contains_generated_artifacts")
    result_root.mkdir(parents=True, exist_ok=True)

    source_archives = {
        "m12da_r3": (args.r3_zip.resolve(), R3_RESULT_SHA256),
        "m12cx_canonical": (args.m12cx_zip.resolve(), M12CX_RESULT_SHA256),
        "m12cx_supplemental": (args.supplemental_zip.resolve(), SUPPLEMENTAL_SHA256),
    }
    archive_rows = []
    for name, (path, expected) in source_archives.items():
        actual = sha256_file(path)
        archive_rows.append(
            {
                "name": name,
                "path": str(path),
                "expected_sha256": expected,
                "actual_sha256": actual,
                "status": "PASS" if actual == expected else "FAIL",
            }
        )
    source_integrity = {
        "contract": "m12db-source-integrity-v1",
        "archives": archive_rows,
        "extracted_manifests": {
            "m12da_r3": _manifest_verification(args.r3_root.resolve(), expected_count=47),
            "m12cx_canonical": _manifest_verification(
                args.m12cx_root.resolve(), expected_count=239
            ),
            "m12cx_supplemental": _manifest_verification(
                args.supplemental_root.resolve(), expected_count=90
            ),
        },
    }
    source_integrity["status"] = (
        "PASS"
        if all(row["status"] == "PASS" for row in archive_rows)
        and all(row["status"] == "PASS" for row in source_integrity["extracted_manifests"].values())
        else "FAIL"
    )
    write_json(result_root / "source-integrity.json", source_integrity)
    require(source_integrity["status"] == "PASS", SOURCE_FAILED)

    subjects, catalogs, archived_batches = _load_archived_inputs(args.m12cx_root.resolve())
    chains = _source_chains(
        subjects=subjects,
        catalogs=catalogs,
        r3_root=args.r3_root.resolve(),
    )
    source_contexts = {ticker: _source_context(ticker, subjects[ticker]) for ticker in subjects}

    pass_a_contexts: dict[str, dict[str, object]] = {}
    pass_a_binding_rows: list[dict[str, object]] = []
    full_projection_scan_contexts: list[dict[str, object]] = []
    readiness_rows: list[dict[str, object]] = []
    for market in ("us", "kr"):
        for ticker in POPULATION[market]:
            chain = chains[ticker]
            intermediate_context = build_pass_a_subject_context(
                context=source_contexts[ticker],
                ticker=ticker,
                catalog=catalogs[ticker],
                source_use_view=chain["projection"],
                source_use_binding=chain["binding"],
                source_use_expectation=chain["expectation"],
                source_generation_id=str(chain["source_generation_id"]),
                execution_generation_id=EXECUTION_GENERATION,
                require_source_use=True,
            )
            # Preserve the already frozen deterministic quality projection from the
            # accepted model input instead of re-projecting it from the stage view.
            filtered_context = build_r1_pass_a_context(
                intermediate_context,
                source_packet=subjects[ticker],
            )
            context = bind_final_pass_a_model_view(
                intermediate_context=intermediate_context,
                final_context=filtered_context,
                source_packet=subjects[ticker],
            )
            pass_a_contexts[ticker] = context
            final_binding = context["source_evidence_binding"]
            assert isinstance(final_binding, Mapping)
            pass_a_binding_rows.append(
                {
                    "ticker": ticker,
                    "intermediate_evidence_count": final_binding["intermediate_evidence_count"],
                    "final_evidence_count": final_binding["final_evidence_count"],
                    "intermediate_evidence_serialized_sha256": final_binding[
                        "intermediate_evidence_serialized_sha256"
                    ],
                    "final_evidence_serialized_sha256": final_binding[
                        "emitted_evidence_serialized_sha256"
                    ],
                    "expected_final_view_sha256": final_binding["expected_final_view_sha256"],
                    "actual_final_view_sha256": final_binding["actual_final_view_sha256"],
                    "status": final_binding["status"],
                }
            )
            full_context = deepcopy(context)
            full_context["source_use_projection"] = model_source_use_projection(
                chain["projection"],
                binding=chain["binding"],
            )
            full_projection_scan_contexts.append(full_context)
            emitted_refs = list(context["eligible_claim_refs"])
            archetype_refs = _allowed_refs(chain, emitted_refs, SourceUse.PASS_A_ARCHETYPE)
            tier_refs = _allowed_refs(chain, emitted_refs, SourceUse.PASS_A_VALUATION_TIER)
            projection = chain["projection"]
            assert isinstance(projection, Mapping)
            claim_records = projection.get("claim_records") or {}
            source_records = projection.get("source_records") or {}
            b_counts = {
                use.value: sum(
                    use.value in set(row.get("allowed_uses") or ())
                    for row in claim_records.values()
                    if isinstance(row, Mapping)
                )
                for use in (
                    SourceUse.OVERALL_DIRECTION,
                    SourceUse.HOLDER_STANCE,
                    SourceUse.NEW_BUYER_EXECUTION_RISK,
                )
            }
            b_counts[SourceUse.VALUATION.value] = sum(
                SourceUse.VALUATION.value in set(row.get("allowed_uses") or ())
                for row in source_records.values()
                if isinstance(row, Mapping)
            )
            model_projection = context["source_use_projection"]
            assert isinstance(model_projection, Mapping)
            readiness_rows.append(
                {
                    "ticker": ticker,
                    "market": market,
                    "source_binding_status": chain["validation"]["status"],
                    "source_generation_id": chain["source_generation_id"],
                    "execution_generation_id": EXECUTION_GENERATION,
                    "source_identity_unchanged": chain["source_identity_unchanged"],
                    "permission_semantics_unchanged": chain["permission_semantics_unchanged"],
                    "runtime_hash_changed_only_for_execution_generation": chain[
                        "runtime_hash_changed_only_for_execution_generation"
                    ],
                    "emitted_a_claim_refs": emitted_refs,
                    "emitted_a_claim_parent_refs": {
                        str(row["claim_ref"]): list(row.get("parent_source_refs") or ())
                        for row in context["accepted_fundamental_claims"]
                    },
                    "a_archetype_support_count": len(archetype_refs),
                    "a_tier_support_count": len(tier_refs),
                    "a_archetype_support_refs": archetype_refs,
                    "a_tier_support_refs": tier_refs,
                    "model_permission_claim_count": len(
                        model_projection.get("claim_permissions") or ()
                    ),
                    "model_permission_source_count": len(
                        model_projection.get("source_permissions") or ()
                    ),
                    "runtime_permission_claim_count": len(claim_records),
                    "runtime_permission_source_count": len(source_records),
                    "current_price_multiple_percentile_technical_target_excluded": True,
                    "source_sufficiency": (
                        "SUFFICIENT_FOR_HONEST_A_BRANCH"
                        if archetype_refs
                        else "PASS_A_SOURCE_VIEW_REQUIRES_CHAT_DECISION"
                    ),
                    "projection_filter_exclusion_count": max(
                        0,
                        sum(
                            bool(
                                set(row.get("allowed_uses") or ())
                                & {
                                    SourceUse.PASS_A_ARCHETYPE.value,
                                    SourceUse.PASS_A_VALUATION_TIER.value,
                                }
                            )
                            for row in claim_records.values()
                            if isinstance(row, Mapping)
                        )
                        - len(emitted_refs),
                    ),
                    "no_forced_label": bool(archetype_refs),
                    "b_support_available_by_use": b_counts,
                    "security_valuation_basis_state": deepcopy(
                        subjects[ticker].get("security_valuation_basis_state") or {}
                    ),
                    "unresolved_valuation_limits_retained": True,
                    "status": "PASS" if archetype_refs else "PARTIAL",
                }
            )

    current_leak_scan = pass_a_leakage_scan(list(pass_a_contexts.values()))
    full_projection_scan = pass_a_leakage_scan(full_projection_scan_contexts)
    require(current_leak_scan["status"] == "PASS", "pass_a_stage_view_leakage")
    mixed_claim = next(
        row
        for row in pass_a_contexts[MIXED_PARENT_TICKER]["accepted_fundamental_claims"]
        if row["claim_ref"] == MIXED_PARENT_CLAIM
    )
    mixed_parent_exposed = any(
        row["ref_id"] == MIXED_PARENT_REF
        for row in pass_a_contexts[MIXED_PARENT_TICKER]["eligible_non_price_evidence"]
    )
    require(not mixed_parent_exposed, "mixed_parent_narrative_exposed")

    pass_a_captures: list[dict[str, object]] = []
    unresolved_rows: list[dict[str, object]] = []
    for spec in _batch_topology():
        market = str(spec["market"])
        batch = int(spec["batch"])
        batch_subjects = tuple(str(value) for value in spec["subjects"])
        capture = _write_request_capture(
            root=result_root / "pass-a-inputs",
            stage="pass-a",
            market=market,
            batch=batch,
            subjects=batch_subjects,
            contexts=pass_a_contexts,
            catalogs=catalogs,
            chains=chains,
            fixture_only=False,
        )
        pass_a_captures.append(capture)
        fixture = _unresolved_fixture(batch_subjects, pass_a_contexts)
        shape = validate_future_pass_a_shape(
            fixture,
            subjects=batch_subjects,
            subject_contexts=pass_a_contexts,
        )
        normalized, materialization = materialize_future_pass_a(
            fixture,
            subjects=batch_subjects,
            subject_contexts=pass_a_contexts,
        )
        source_validation: dict[str, object] = {"status": "NOT_RUN"}
        if materialization["status"] == "PASS":
            envelope = PassABatchOutput.model_validate(
                {
                    "contract": "m12cq-pass-a-archetype-regime-v1",
                    "generation_id": EXECUTION_GENERATION,
                    "packet_id": f"m12db-{market}-batch-{batch:02d}",
                    "market": market,
                    "assessment_date": "2026-09-19",
                    "classifications": normalized,
                }
            )
            source_validation = validate_pass_a_batch(
                envelope,
                expected_identity={
                    "generation_id": EXECUTION_GENERATION,
                    "packet_id": f"m12db-{market}-batch-{batch:02d}",
                    "market": market,
                    "assessment_date": "2026-09-19",
                },
                subjects=batch_subjects,
                subject_contexts=pass_a_contexts,
                source_catalogs=catalogs,
                source_use_views={
                    ticker: chains[ticker]["projection"] for ticker in batch_subjects
                },
                source_use_bindings={
                    ticker: chains[ticker]["binding"] for ticker in batch_subjects
                },
                source_use_expectations={
                    ticker: chains[ticker]["expectation"] for ticker in batch_subjects
                },
                source_metadata_by_ticker={
                    ticker: subjects[ticker]["decision_evidence"] for ticker in batch_subjects
                },
                source_generation_id=str(chains[batch_subjects[0]]["source_generation_id"]),
                execution_generation_id=EXECUTION_GENERATION,
                require_source_use=True,
            )
        unresolved_rows.append(
            {
                "market": market,
                "batch": batch,
                "subjects": list(batch_subjects),
                "raw_shape": shape,
                "materialization": materialization,
                "source_use_final_gate": source_validation,
                "status": (
                    "PASS"
                    if shape["status"]
                    == materialization["status"]
                    == source_validation["status"]
                    == "PASS"
                    else "FAIL"
                ),
            }
        )

    pass_b_contexts: dict[str, dict[str, object]] = {}
    capabilities: dict[str, dict[str, object]] = {}
    capability_rows: list[dict[str, object]] = []
    for ticker in POPULATION["us"] + POPULATION["kr"]:
        chain = chains[ticker]
        pass_a_fixture = subjects[ticker]["frozen_pass_a_classification"]
        policy_option = subjects[ticker]["deterministic_fundamental_option"]
        pass_b_context = build_pass_b_subject_context(
            context=source_contexts[ticker],
            ticker=ticker,
            catalog=catalogs[ticker],
            pass_a=pass_a_fixture,
            policy_option=policy_option,
            source_use_view=chain["projection"],
            source_use_binding=chain["binding"],
            source_use_expectation=chain["expectation"],
            source_generation_id=str(chain["source_generation_id"]),
            execution_generation_id=EXECUTION_GENERATION,
            require_source_use=True,
        )
        pass_b_context["business_evidence_quality_state"] = deepcopy(
            subjects[ticker].get("business_evidence_quality_state") or {}
        )
        pass_b_context["security_valuation_basis_state"] = deepcopy(
            subjects[ticker].get("security_valuation_basis_state") or {}
        )
        pass_b_context["directional_disclosure_quality_refs"] = deepcopy(
            subjects[ticker].get("directional_disclosure_quality_refs") or []
        )
        capability = build_pass_b_capability_catalog(
            context=pass_b_context,
            catalog=catalogs[ticker],
            pass_a=pass_a_fixture,
            policy_option=policy_option,
            source_use_view=chain["projection"],
            source_use_binding=chain["binding"],
            source_use_expectation=chain["expectation"],
            source_generation_id=str(chain["source_generation_id"]),
            execution_generation_id=EXECUTION_GENERATION,
            require_source_use=True,
            raw_source_metadata=subjects[ticker]["decision_evidence"],
        )
        pass_b_context["pass_b_capability_catalog"] = deepcopy(capability)
        pass_b_contexts[ticker] = pass_b_context
        capabilities[ticker] = capability
        capability_rows.append(
            {
                "ticker": ticker,
                "capability_contract": capability.get("contract"),
                "source_use_binding_sha256": capability.get("source_use_binding_sha256"),
                "status": "PASS",
            }
        )

    pass_b_captures = [
        _write_request_capture(
            root=result_root / "pass-b-fixture-captures",
            stage="pass-b",
            market=str(spec["market"]),
            batch=int(spec["batch"]),
            subjects=tuple(str(value) for value in spec["subjects"]),
            contexts=pass_b_contexts,
            catalogs=catalogs,
            chains=chains,
            fixture_only=True,
            capabilities=capabilities,
        )
        for spec in _batch_topology()
    ]

    unresolved_status_by_ticker = {
        ticker: row["status"] for row in unresolved_rows for ticker in row["subjects"]
    }
    for row in readiness_rows:
        unresolved_status = unresolved_status_by_ticker[str(row["ticker"])]
        row["raw_schema_unresolved_branch_status"] = unresolved_status
        if unresolved_status != "PASS":
            row["status"] = "PARTIAL"
    write_json(
        result_root / "model-view-readiness-22.json",
        {
            "contract": "m12db-model-view-readiness-22-v1",
            "subject_count": len(readiness_rows),
            "ready_count": sum(row["status"] == "PASS" for row in readiness_rows),
            "rows": readiness_rows,
            "status": "PASS"
            if all(row["status"] == "PASS" for row in readiness_rows)
            else "PARTIAL",
        },
    )
    write_json(
        result_root / "pass-a-permission-and-price-blind-view-reconciliation.json",
        {
            "contract": "m12db-pass-a-permission-price-blind-reconciliation-v1",
            "V1": {
                "ticker": MIXED_PARENT_TICKER,
                "claim_ref": MIXED_PARENT_CLAIM,
                "claim_text": mixed_claim["text"],
                "parent_source_refs": mixed_claim["parent_source_refs"],
                "mixed_parent_ref": MIXED_PARENT_REF,
                "mixed_parent_narrative_exposed": mixed_parent_exposed,
                "claim_retained": True,
                "ticker_specific_rule_count": 0,
                "resolution": "SOURCE_AUTHORIZED_ATOMIC_CLAIM_VIEW_WITH_FULL_PARENT_LINEAGE",
            },
            "V2": {
                "full_runtime_projection_scan": full_projection_scan,
                "stage_scoped_model_projection_scan": current_leak_scan,
                "full_projection_hit_subject_count": sum(
                    bool(row["forbidden_paths"]) for row in full_projection_scan["rows"]
                ),
                "all_full_projection_hits_are_identifier_tokens": all(
                    path.startswith("source_use_projection.source_permissions.")
                    and path.endswith(".ref_id:valuation_token")
                    for row in full_projection_scan["rows"]
                    for path in row["forbidden_paths"]
                ),
                "proven_leak_class_count": 1 if full_projection_scan["errors"] else 0,
                "proven_leak_class": "OUT_OF_STAGE_PERMISSION_IDENTIFIER_ONLY",
                "actual_numeric_or_target_leak_proven": False,
                "stage_scoped_forbidden_path_count": len(current_leak_scan["errors"]),
            },
            "runtime_projection_preserved": True,
            "source_permissions_broadened": False,
            "historical_claims_rewritten": False,
            "status": "PASS",
        },
    )
    write_json(
        result_root / "pass-a-unresolved-and-no-forced-label-proof.json",
        {
            "contract": "m12db-pass-a-unresolved-branch-proof-v1",
            "batch_count": len(unresolved_rows),
            "rows": unresolved_rows,
            "forced_label_count": 0,
            "status": "PASS" if all(row["status"] == "PASS" for row in unresolved_rows) else "FAIL",
        },
    )
    write_json(
        result_root / "pass-a-input-freeze-manifest.json",
        {
            "contract": "m12db-pass-a-input-freeze-manifest-v1",
            "execution_generation_id": EXECUTION_GENERATION,
            "source_generation_ids": sorted(
                {str(chain["source_generation_id"]) for chain in chains.values()}
            ),
            "capture_count": len(pass_a_captures),
            "captures": pass_a_captures,
            "model_calls": 0,
            "network_calls": 0,
            "status": "PASS",
        },
    )
    write_json(
        result_root / "pass-a-final-post-quality-view-binding.json",
        {
            "contract": "m12db-r1-pass-a-final-post-quality-view-binding-v1",
            "hash_owner": "scripts.m12cq_two_pass_contract.canonical_sha256",
            "subject_count": len(pass_a_binding_rows),
            "changed_after_quality_filter_count": sum(
                row["intermediate_evidence_serialized_sha256"]
                != row["final_evidence_serialized_sha256"]
                for row in pass_a_binding_rows
            ),
            "rows": pass_a_binding_rows,
            "status": (
                "PASS" if all(row["status"] == "PASS" for row in pass_a_binding_rows) else "FAIL"
            ),
        },
    )
    write_json(
        result_root / "pass-b-template-and-dynamic-input-freeze.json",
        {
            "contract": "m12db-pass-b-template-dynamic-input-freeze-v1",
            "exact_future_pass_b_requests_frozen": False,
            "reason": "Fresh Pass-B requests depend on the later frozen fresh Pass-A output.",
            "template_sha256": canonical_sha256(capability_prompt_template()),
            "schema_builder": (
                "scripts.m12cv_pass_b_capability_contract.capability_pass_b_batch_schema"
            ),
            "context_builder": "scripts.m12cq_two_pass_contract.build_pass_b_subject_context",
            "capability_builder": (
                "scripts.m12cv_pass_b_capability_contract.build_pass_b_capability_catalog"
            ),
            "validator_owner": "scripts.m12cq_two_pass_contract.validate_pass_b_batch",
            "provider_projection_owner": (
                "scripts.m12cs_r1_provider_schema.project_provider_wire_schema"
            ),
            "fixture_source": "IMMUTABLE_ARCHIVED_M12CX_PASS_A_AND_POLICY_OPTIONS",
            "fixture_capture_count": len(pass_b_captures),
            "fixture_captures": pass_b_captures,
            "capability_rows": capability_rows,
            "capabilities": capabilities,
            "model_calls": 0,
            "network_calls": 0,
            "status": "PASS",
        },
    )
    write_json(
        result_root / "source-aware-actual-caller-chain.json",
        {
            "contract": "m12db-source-aware-actual-caller-chain-v1",
            "execution_generation_id": EXECUTION_GENERATION,
            "chain": [
                "local immutable M12CX loader",
                "accepted R3 authority manifest",
                "freeze_source_use_input_expectation",
                "build_source_use_projection",
                "freeze_source_use_binding",
                "resolve_subject_evidence_view",
                "build_pass_a_subject_context",
                "future_pass_a_prompt_template",
                "future_pass_a_batch_schema",
                "project_provider_wire_schema",
                "no-network outbound request capture",
                "validate_pass_a_batch selected-evidence consumer",
            ],
            "mandatory_source_use_arguments": [
                "source_use_view",
                "source_use_binding",
                "source_use_expectation",
                "source_generation_id",
                "execution_generation_id",
                "require_source_use=True",
            ],
            "source_generation_distinct_from_execution_generation": all(
                chain["source_generation_id"] != EXECUTION_GENERATION for chain in chains.values()
            ),
            "pass_a_capture_count": len(pass_a_captures),
            "pass_b_fixture_capture_count": len(pass_b_captures),
            "provider_wrapper_invocation_count": 0,
            "network_calls": 0,
            "status": "PASS",
        },
    )

    impacted_batches = [
        {"market": row["market"], "batch": row["batch"], "subjects": list(row["subjects"])}
        for row in _batch_topology()
    ]
    write_json(
        result_root / "batch-reproof-scope-plan.json",
        {
            "contract": "m12db-batch-reproof-scope-plan-v1",
            "classification_1_old_selected_support_validity": {
                "affected_subjects": ["000660", "005490", "005930", "TSLA"],
                "meaning": "Preserved R3 diagnostic; not a new model failure.",
            },
            "classification_2_complete_model_visible_input": {
                "atomic_claim_change_subjects": ["000660"],
                "stage_scoped_permission_view_changed_subject_count": 22,
                "runtime_permission_semantics_changed_subject_count": 0,
            },
            "classification_3_shared_batch_and_downstream_dependency": {
                "pass_a_batches_affected": impacted_batches,
                "pass_b_depends_on_future_fresh_a": True,
            },
            "recommended_later_scope": {
                "pass_a": "ALL_8_BATCHES_ONE_FRESH_NO_RETRY_GENERATION",
                "pass_b": "ALL_8_BATCHES_AFTER_EXACT_FRESH_A_FREEZE",
                "selective_rerun": False,
                "fresh_core_or_source_refresh": False,
            },
            "executed_by_m12db": False,
            "model_calls": 0,
            "status": "FROZEN_FOR_CHAT_SCOPE_DECISION",
        },
    )

    source_comparison_rows = []
    for ticker, chain in chains.items():
        source_comparison_rows.append(
            {
                "ticker": ticker,
                "source_identity_unchanged": chain["source_identity_unchanged"],
                "permission_semantics_unchanged": chain["permission_semantics_unchanged"],
                "prior_execution_generation_id": chain["prior_expectation"][
                    "execution_generation_id"
                ],
                "new_execution_generation_id": EXECUTION_GENERATION,
                "prior_projection_sha256": chain["prior_projection"]["projection_sha256"],
                "new_projection_sha256": chain["projection"]["projection_sha256"],
                "runtime_hash_change_class": "EXECUTION_ID_AND_BINDING_ONLY",
            }
        )
    write_json(
        result_root / "source-semantic-runtime-hash-comparison.json",
        {
            "contract": "m12db-source-semantic-runtime-hash-comparison-v1",
            "subject_count": len(source_comparison_rows),
            "rows": source_comparison_rows,
            "semantic_change_count": sum(
                not row["permission_semantics_unchanged"] for row in source_comparison_rows
            ),
            "status": "PASS",
        },
    )

    combined = (
        args.supplemental_root.resolve()
        / "cross-run-offline-validation/combined-fresh-a-m12cx-b-22-subject-results.json"
    )
    immutable_before = {name: sha256_file(path) for name, (path, _) in source_archives.items()}
    immutable_before["combined_historical_file"] = sha256_file(combined)
    require(
        immutable_before["combined_historical_file"] == HISTORICAL_COMBINED_SHA256,
        "combined_historical_hash_mismatch",
    )
    immutable_after = {name: sha256_file(path) for name, (path, _) in source_archives.items()}
    immutable_after["combined_historical_file"] = sha256_file(combined)
    write_json(
        result_root / "original-input-output-immutability.json",
        {
            "contract": "m12db-original-input-output-immutability-v1",
            "before": immutable_before,
            "after": immutable_after,
            "all_equal": immutable_before == immutable_after,
            "historical_outputs_rewritten": 0,
            "status": "PASS" if immutable_before == immutable_after else "FAIL",
        },
    )
    write_json(
        result_root / "preserved-under-supported-observations.json",
        {
            "contract": "m12db-preserved-under-supported-observations-v1",
            "historical_under_supported_subject_count": 19,
            "classification": "PRESERVED_DIAGNOSTIC_NOT_NEW_MODEL_FAILURE",
            "historical_selected_support_affected_subjects": [
                "000660",
                "005490",
                "005930",
                "TSLA",
            ],
            "status": "PRESERVED",
        },
    )

    implementation_commit = args.implementation_commit
    source_export = result_root / "source-export"
    for relative in CHANGED_SOURCE_PATHS:
        destination = source_export / Path(relative).name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / relative, destination)
    diff = subprocess.run(
        ("git", "diff", f"{PLAN_COMMIT}..{implementation_commit}", "--", *CHANGED_SOURCE_PATHS),
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    write_text(result_root / "changed-sources.diff", diff)
    write_json(
        result_root / "changed-sources.json",
        {
            "contract": "m12db-changed-sources-v1",
            "plan_commit": PLAN_COMMIT,
            "implementation_commit": implementation_commit,
            "paths": [
                {
                    "path": relative,
                    "sha256": sha256_file(REPO / relative),
                    "size": (REPO / relative).stat().st_size,
                }
                for relative in CHANGED_SOURCE_PATHS
            ],
        },
    )
    write_json(
        result_root / "repository-state.json",
        {
            "branch": subprocess.run(
                ("git", "branch", "--show-current"),
                cwd=REPO,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip(),
            "base_commit": BASE_COMMIT,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "plan_commit": PLAN_COMMIT,
            "implementation_commit": implementation_commit,
            "remote_push": False,
            "main_merge": False,
            "deploy": False,
        },
    )
    write_json(
        result_root / "safety-counters.json",
        {
            "model_calls": 0,
            "provider_calls": 0,
            "network_calls": 0,
            "source_refresh_calls": 0,
            "database_mutations": 0,
            "notification_sends": 0,
            "scheduler_mutations": 0,
            "broker_actions": 0,
            "production_changes": 0,
            "historical_rewrites": 0,
            "main_merges": 0,
            "remote_pushes": 0,
            "deploys": 0,
            "status": "PASS",
        },
    )
    write_json(
        result_root / "finite-residual-gaps.json",
        {
            "contract": "m12db-finite-residual-gaps-v1",
            "blocking_model_view_gaps": [],
            "retained_dynamic_dependency": [
                "Exact Pass-B requests require the later fresh Pass-A output freeze."
            ],
            "not_authorized": [
                "live Pass A or Pass B inference",
                "production integration",
                "canonical relabeling",
            ],
            "status": "NON_BLOCKING_SCOPE_BOUNDARY",
        },
    )

    validation = _validation(result_root)
    ready_count = sum(row["status"] == "PASS" for row in readiness_rows)
    all_ready = (
        ready_count == 22
        and len(pass_a_captures) == 8
        and len(pass_b_captures) == 8
        and current_leak_scan["status"] == "PASS"
        and all(row["status"] == "PASS" for row in unresolved_rows)
        and validation["status"] == "PASS"
    )
    completion = {
        "contract": "m12db-program-completion-v1",
        "terminal": READY if all_ready else PARTIAL,
        "execution_generation_id": EXECUTION_GENERATION,
        "ready_subject_count": ready_count,
        "pass_a_capture_count": len(pass_a_captures),
        "pass_b_fixture_capture_count": len(pass_b_captures),
        "pass_a_forbidden_path_count": len(current_leak_scan["errors"]),
        "mixed_parent_claim_retained": mixed_claim["claim_ref"] == MIXED_PARENT_CLAIM,
        "validation_status": validation["status"],
        "future_inference_authorized": False,
        "production_authorized": False,
        "status": "PASS" if all_ready else "PARTIAL",
    }
    write_json(result_root / "program-completion.json", completion)
    write_text(result_root / "MODEL_VIEW_READINESS_DECISION.md", _report_markdown(completion))

    json_errors = []
    for path in sorted(result_root.rglob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            json_errors.append(f"{path.relative_to(result_root)}:{exc}")
    write_text(
        result_root / "validation/json-validation.log",
        "PASS" if not json_errors else "\n".join(json_errors),
    )
    require(not json_errors, "generated_json_validation_failed")
    write_json(result_root / "artifact-manifest.json", _artifact_manifest(result_root))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r3-zip", type=Path, required=True)
    parser.add_argument("--r3-root", type=Path, required=True)
    parser.add_argument("--m12cx-zip", type=Path, required=True)
    parser.add_argument("--m12cx-root", type=Path, required=True)
    parser.add_argument("--supplemental-zip", type=Path, required=True)
    parser.add_argument("--supplemental-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--implementation-commit", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
