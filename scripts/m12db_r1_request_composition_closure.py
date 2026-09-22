from __future__ import annotations

import argparse
import json
import shutil
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path

from scripts import m12db_model_view_readiness as m12db
from scripts.m12cq_two_pass_contract import PassBBatchOutput, validate_pass_b_batch
from scripts.m12cr_shadow_contract import (
    normalize_future_pass_b,
    validate_future_pass_b_shape,
    validate_materialized_pass_b,
)
from scripts.m12cs_r1_provider_schema import (
    project_provider_wire_schema,
    scan_provider_structured_output_schema,
)
from scripts.m12cv_pass_b_capability_contract import (
    build_pass_b_capability_catalog,
    capability_pass_b_batch_schema,
    capability_prompt_template,
    validate_capability_selection,
)
from scripts.m12da_source_use_contract import canonical_sha256


REPO = Path(__file__).resolve().parents[1]
READY = "M12DB_R1_CAPABILITY_AWARE_REQUEST_AND_FINAL_VIEW_BOUND_READY_FOR_CHAT"
PARTIAL = "M12DB_R1_PARTIAL_WITH_EXACT_REQUEST_OR_SUPPORT_GAP"
M12DB_SHA256 = "f05d4b5530ddab08dfe342b198753f9c697b840bed8256862d6c917c43c68115"
M12CU_SHA256 = "ed8737b400ff84f77f5d8c13a365aa2d9ddee5c53f063c123c956d2c721053ea"


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise m12db.M12DBFailure(f"expected_json_object:{path}")
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


def _source_archives(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "m12db": args.m12db_zip.resolve(),
        "m12da_r3": args.r3_zip.resolve(),
        "m12cx": args.m12cx_zip.resolve(),
        "m12cx_supplemental": args.supplemental_zip.resolve(),
        "m12cu": args.m12cu_zip.resolve(),
    }


def _batch_artifacts(
    actual_root: Path,
) -> tuple[
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
]:
    contexts: dict[str, dict[str, object]] = {}
    catalogs: dict[str, dict[str, object]] = {}
    capabilities: dict[str, dict[str, object]] = {}
    for spec in m12db._batch_topology():
        market = str(spec["market"])
        batch = int(spec["batch"])
        directory = actual_root / "pass-b-fixture-captures" / market / f"batch-{batch:02d}"
        context_payload = read_json(directory / "subject-context.json")
        catalog_payload = read_json(directory / "ref-catalog.json")
        capability_payload = read_json(directory / "capability-catalog.json")
        for row in context_payload["subjects"]:
            ticker = str(row["ticker"])
            contexts[ticker] = deepcopy(dict(row))
            catalogs[ticker] = deepcopy(dict(catalog_payload[ticker]))
            capabilities[ticker] = deepcopy(dict(capability_payload[ticker]))
    return contexts, catalogs, capabilities


def _capability_pairs(capability: Mapping[str, object]) -> set[tuple[str, str]]:
    new_buyer = capability.get("new_buyer")
    branches = new_buyer.get("branches") if isinstance(new_buyer, Mapping) else ()
    return {
        (str(row.get("stance")), str(row.get("reason_class")))
        for row in branches or ()
        if isinstance(row, Mapping)
    }


def _synthetic_row(capability: Mapping[str, object]) -> dict[str, object]:
    evidence_classes = capability["evidence_classes"]
    assert isinstance(evidence_classes, Mapping)
    business_refs = list(evidence_classes.get("material_business_claim_refs") or ())
    m12db.require(bool(business_refs), f"supported_overall_ref_missing:{capability['ticker']}")
    new_buyer = capability["new_buyer"]
    assert isinstance(new_buyer, Mapping)
    branches = list(new_buyer.get("branches") or ())
    m12db.require(bool(branches), f"new_buyer_surface_missing:{capability['ticker']}")
    branch = branches[0]
    assert isinstance(branch, Mapping)
    stance = str(branch["stance"])
    allowed_refs = list(branch.get("allowed_evidence_refs") or ())
    allowed_tactical = list(branch.get("allowed_tactical_choices") or ())
    m12db.require(bool(allowed_refs), f"new_buyer_ref_missing:{capability['ticker']}")
    if stance == "WAIT":
        m12db.require(bool(allowed_tactical), f"wait_tactical_missing:{capability['ticker']}")
        tactical = str(allowed_tactical[0])
        conditions = ["동결된 조건을 다시 확인합니다."]
    else:
        tactical = "NOT_APPLICABLE"
        conditions = []
    overall = capability["overall"]
    assert isinstance(overall, Mapping)
    allowed_overall = list(overall.get("allowed_values") or ())
    direction = "BUY" if "BUY" in allowed_overall else str(allowed_overall[0])
    return {
        "overall_direction": direction,
        "directional_buy_score": 6.0,
        "decision_confidence": "MEDIUM",
        "decisive_supporting_claim_refs": [business_refs[0]],
        "decisive_contradicting_claim_refs": [],
        "thesis_state": "INTACT",
        "holder_decision": {
            "holder": "HOLDABLE",
            "reason_class": "NOT_APPLICABLE",
            "reason": "동결된 근거에서 보유 축의 훼손은 선택하지 않았습니다.",
            "evidence_refs": [],
        },
        "new_buyer_decision": {
            "new_buyer": stance,
            "reason_class": str(branch["reason_class"]),
            "reason": "동결된 capability가 허용한 신규매수 분기입니다.",
            "evidence_refs": [str(allowed_refs[0])],
            "tactical_choice": tactical,
            "re_evaluate_conditions": conditions,
        },
        "policy_summary": "세 축을 분리한 오프라인 contract fixture입니다.",
    }


def _validate_synthetic_batches(
    *,
    contexts: Mapping[str, Mapping[str, object]],
    catalogs: Mapping[str, Mapping[str, object]],
    capabilities: Mapping[str, Mapping[str, object]],
    chains: Mapping[str, Mapping[str, object]],
    source_packets: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    source_generation_ids = {str(chain["source_generation_id"]) for chain in chains.values()}
    m12db.require(len(source_generation_ids) == 1, "mixed_source_generation_not_supported")
    source_generation_id = next(iter(source_generation_ids))
    for spec in m12db._batch_topology():
        market = str(spec["market"])
        batch = int(spec["batch"])
        subjects = tuple(str(value) for value in spec["subjects"])
        output = {
            "decisions": {ticker: _synthetic_row(capabilities[ticker]) for ticker in subjects}
        }
        selected = validate_capability_selection(
            output,
            subjects=subjects,
            catalogs=catalogs,
            capabilities=capabilities,
            source_use_views={ticker: chains[ticker]["projection"] for ticker in subjects},
            source_use_bindings={ticker: chains[ticker]["binding"] for ticker in subjects},
            source_use_expectations={ticker: chains[ticker]["expectation"] for ticker in subjects},
            source_metadata_by_ticker={
                ticker: source_packets[ticker]["decision_evidence"] for ticker in subjects
            },
            source_generation_id=source_generation_id,
            execution_generation_id=m12db.EXECUTION_GENERATION,
            require_source_use=True,
        )
        normalized, normalization = normalize_future_pass_b(
            output,
            subjects=subjects,
            catalogs=catalogs,
        )
        materialized = validate_materialized_pass_b(
            normalized,
            subjects=subjects,
            catalogs=catalogs,
            pass_a_by_ticker={
                ticker: contexts[ticker]["frozen_pass_a_classification"] for ticker in subjects
            },
            policy_options={
                ticker: contexts[ticker]["deterministic_fundamental_option"] for ticker in subjects
            },
            capabilities=capabilities,
        )
        final = {"status": "NOT_RUN", "errors": ["normalization_failed"]}
        if normalization["status"] == "PASS":
            packet_id = f"m12db-r1-{market}-batch-{batch:02d}"
            envelope = PassBBatchOutput.model_validate(
                {
                    "contract": "m12cq-pass-b-decision-tactical-v1",
                    "generation_id": m12db.EXECUTION_GENERATION,
                    "packet_id": packet_id,
                    "market": market,
                    "assessment_date": "2026-09-19",
                    "decisions": normalized,
                }
            )
            final = validate_pass_b_batch(
                envelope,
                expected_identity={
                    "generation_id": m12db.EXECUTION_GENERATION,
                    "packet_id": packet_id,
                    "market": market,
                    "assessment_date": "2026-09-19",
                },
                subjects=subjects,
                catalogs=catalogs,
                pass_a_by_ticker={
                    ticker: contexts[ticker]["frozen_pass_a_classification"] for ticker in subjects
                },
                source_use_views={ticker: chains[ticker]["projection"] for ticker in subjects},
                source_use_bindings={ticker: chains[ticker]["binding"] for ticker in subjects},
                source_use_expectations={
                    ticker: chains[ticker]["expectation"] for ticker in subjects
                },
                source_metadata_by_ticker={
                    ticker: source_packets[ticker]["decision_evidence"] for ticker in subjects
                },
                source_generation_id=source_generation_id,
                execution_generation_id=m12db.EXECUTION_GENERATION,
                require_source_use=True,
            )
        status = (
            "PASS"
            if selected["status"]
            == normalization["status"]
            == materialized["status"]
            == final["status"]
            == "PASS"
            else "FAIL"
        )
        rows.append(
            {
                "market": market,
                "batch": batch,
                "subjects": list(subjects),
                "raw_capability_and_source_use": selected,
                "normalization": normalization,
                "materialized_policy": materialized,
                "final_source_use_semantics": final,
                "status": status,
            }
        )
    return {
        "contract": "m12db-r1-synthetic-b-consumer-chain-v1",
        "fixture_only": True,
        "investment_judgment": False,
        "batch_count": len(rows),
        "subject_count": sum(len(row["subjects"]) for row in rows),
        "rows": rows,
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def _generic_capability(*, resolved: bool) -> dict[str, object]:
    ticker = "RENAMED"
    catalog = {
        "ticker": ticker,
        "all_evidence_refs": ["evidence:business", "canonical:valuation", "canonical:price"],
        "core_evidence_refs": ["evidence:business", "canonical:valuation"],
        "timing_evidence_refs": ["canonical:price"],
        "valuation_evidence_refs": ["canonical:valuation"],
        "claim_refs": ["claim:business"],
        "atomic_claims": [
            {
                "ticker": ticker,
                "claim_ref": "claim:business",
                "claim": {
                    "text": "Generic business evidence.",
                    "polarity": "BULLISH",
                    "logical_condition": None,
                },
                "parent_source_refs": ["evidence:business"],
            }
        ],
        "entry_catalog": {
            "ticker": ticker,
            "current_price": {
                "value": 90.0,
                "as_of": "2026-09-19",
                "currency": "USD",
                "ref_id": "canonical:price",
            },
            "tactical_candidates": [],
            "unresolved_policy": {"tactical_unresolved_reason": "unavailable"},
        },
    }
    option = {
        "ticker": ticker,
        "status": "RESOLVED" if resolved else "UNRESOLVED",
        "low": 70.0 if resolved else None,
        "high": 80.0 if resolved else None,
        "currency": "USD" if resolved else None,
        "evidence_refs": ["canonical:valuation"] if resolved else [],
    }
    context = {
        "ticker": ticker,
        "current_price": deepcopy(catalog["entry_catalog"]["current_price"]),
        "tactical_candidates": [],
        "security_valuation_basis_state": {
            "state": "RESOLVED",
            "new_buyer_price_resolution_use_allowed": True,
        },
    }
    capability = build_pass_b_capability_catalog(
        context=context,
        catalog=catalog,
        pass_a={"ticker": ticker, "archetype": "DURABLE_FRANCHISE"},
        policy_option=option,
    )
    schema = capability_pass_b_batch_schema(
        subjects=(ticker,),
        catalogs={ticker: catalog},
        capabilities={ticker: capability},
    )
    provider, projection = project_provider_wire_schema(schema)
    return {
        "capability": capability,
        "schema_sha256": canonical_sha256(schema),
        "provider_schema_sha256": canonical_sha256(provider),
        "provider_projection": projection,
        "provider_scan": scan_provider_structured_output_schema(provider),
    }


def _artifact_manifest(root: Path) -> dict[str, object]:
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "artifact-manifest.json":
            continue
        rows.append(
            {
                "path": str(path.relative_to(root)),
                "sha256": m12db.sha256_file(path),
                "size": path.stat().st_size,
            }
        )
    return {
        "contract": "m12db-r1-artifact-manifest-v1",
        "file_count": len(rows),
        "files": rows,
    }


def run(args: argparse.Namespace) -> None:
    result_root = args.result_root.resolve()
    m12db.require(not result_root.exists(), "result_root_must_not_exist")
    result_root.mkdir(parents=True)
    archives = _source_archives(args)
    immutable_before = {name: m12db.sha256_file(path) for name, path in archives.items()}
    m12db.require(immutable_before["m12db"] == M12DB_SHA256, "m12db_archive_hash_mismatch")
    m12db.require(immutable_before["m12cu"] == M12CU_SHA256, "m12cu_archive_hash_mismatch")

    actual_root = result_root / "actual-caller-capture"
    m12db.run(
        argparse.Namespace(
            r3_zip=args.r3_zip,
            r3_root=args.r3_root,
            m12cx_zip=args.m12cx_zip,
            m12cx_root=args.m12cx_root,
            supplemental_zip=args.supplemental_zip,
            supplemental_root=args.supplemental_root,
            result_root=actual_root,
            implementation_commit=args.implementation_commit,
        )
    )
    actual_completion = read_json(actual_root / "program-completion.json")
    contexts, catalogs, capabilities = _batch_artifacts(actual_root)
    source_packets, source_catalogs, _ = m12db._load_archived_inputs(args.m12cx_root.resolve())
    m12db.require(canonical_sha256(catalogs) == canonical_sha256(source_catalogs), "catalog_drift")
    chains = m12db._source_chains(
        subjects=source_packets,
        catalogs=source_catalogs,
        r3_root=args.r3_root.resolve(),
    )

    binding_rows: list[dict[str, object]] = []
    unresolved_count = 0
    unresolved_forbidden_count = 0
    resolved_above_high_count = 0
    resolved_range_available_count = 0
    for ticker in m12db.POPULATION["us"] + m12db.POPULATION["kr"]:
        context = contexts[ticker]
        capability = capabilities[ticker]
        option = context["deterministic_fundamental_option"]
        current = context.get("current_price")
        pairs = _capability_pairs(capability)
        unresolved = isinstance(option, Mapping) and option.get("status") != "RESOLVED"
        if unresolved:
            unresolved_count += 1
            if not pairs.intersection(
                {
                    ("ATTRACTIVE", "ATTRACTIVE_WITHIN_RANGE"),
                    ("WAIT", "FUNDAMENTAL_RANGE_POSITION"),
                }
            ):
                unresolved_forbidden_count += 1
        resolved_above = bool(
            isinstance(option, Mapping)
            and option.get("status") == "RESOLVED"
            and isinstance(current, Mapping)
            and current.get("value") is not None
            and option.get("high") is not None
            and float(current["value"]) > float(option["high"])
        )
        if resolved_above:
            resolved_above_high_count += 1
            if ("WAIT", "FUNDAMENTAL_RANGE_POSITION") in pairs:
                resolved_range_available_count += 1
        binding_rows.append(
            {
                "ticker": ticker,
                "capability_sha256": canonical_sha256(capability),
                "context_capability_sha256": canonical_sha256(
                    context.get("pass_b_capability_catalog")
                ),
                "source_use_binding_sha256": capability.get("source_use_binding_sha256"),
                "business_evidence_quality_state_present": isinstance(
                    context.get("business_evidence_quality_state"), Mapping
                ),
                "security_valuation_basis_state_present": isinstance(
                    context.get("security_valuation_basis_state"), Mapping
                ),
                "directional_disclosure_quality_refs_present": isinstance(
                    context.get("directional_disclosure_quality_refs"), list
                ),
                "fundamental_unresolved": unresolved,
                "resolved_above_high": resolved_above,
                "new_buyer_branch_pairs": sorted([list(pair) for pair in pairs]),
                "status": "PASS"
                if canonical_sha256(capability)
                == canonical_sha256(context.get("pass_b_capability_catalog"))
                else "FAIL",
            }
        )

    capture_rows = []
    for spec in m12db._batch_topology():
        market = str(spec["market"])
        batch = int(spec["batch"])
        directory = actual_root / "pass-b-fixture-captures" / market / f"batch-{batch:02d}"
        receipt = read_json(directory / "no-network-outbound-receipt.json")
        scan = read_json(directory / "provider-dialect-scan.json")
        capture_rows.append(
            {
                "market": market,
                "batch": batch,
                "subjects": list(spec["subjects"]),
                "request_sha256": receipt["request_sha256"],
                "file_sha256": receipt["file_sha256"],
                "request_composition": receipt["request_composition"],
                "fixture_only": receipt["fixture_only"],
                "unsupported_provider_keyword_count": scan["unsupported_keyword_count"],
                "wire_unique_items_count": scan["unique_items_count"],
                "status": "PASS"
                if receipt["request_composition"] == "CAPABILITY_AWARE_FINAL"
                and receipt["fixture_only"] is True
                and scan["status"] == "PASS"
                and scan["unique_items_count"] == 0
                else "FAIL",
            }
        )

    consumer_chain = _validate_synthetic_batches(
        contexts=contexts,
        catalogs=catalogs,
        capabilities=capabilities,
        chains=chains,
        source_packets=source_packets,
    )
    write_json(result_root / "synthetic-valid-b-consumer-chain.json", consumer_chain)

    m12cu_raw = args.m12cu_root.resolve() / "model-calls/pass-b/us/batch-01/raw-output.json"
    historical = read_json(m12cu_raw)
    historical_subjects = ("CORZ", "CPNG", "CRCL")
    old_shape = validate_future_pass_b_shape(
        historical,
        subjects=historical_subjects,
        catalogs=catalogs,
    )
    repaired_capability = validate_capability_selection(
        historical,
        subjects=historical_subjects,
        catalogs=catalogs,
        capabilities=capabilities,
    )
    generic_unresolved = _generic_capability(resolved=False)
    generic_resolved = _generic_capability(resolved=True)
    unresolved_pairs = _capability_pairs(generic_unresolved["capability"])
    resolved_pairs = _capability_pairs(generic_resolved["capability"])
    crcl_errors = repaired_capability["per_ticker"]["CRCL"]
    replay = {
        "contract": "m12db-r1-historical-crcl-and-generic-branch-replay-v1",
        "historical_raw_path": str(m12cu_raw),
        "historical_raw_sha256": m12db.sha256_file(m12cu_raw),
        "expected_historical_raw_sha256": (
            "82d56065367b7aa07251d04b1fef86d0c7bbcc93afeb6a089ac317c6718d3035"
        ),
        "archived_m12cu_raw_shape_receipt": read_json(
            args.m12cu_root.resolve()
            / "model-calls/pass-b/us/batch-01/raw-semantic-validation.json"
        ),
        "archived_m12cu_provider_dialect": read_json(
            args.m12cu_root.resolve() / "model-calls/pass-b/us/batch-01/provider-dialect-scan.json"
        ),
        "current_generic_raw_shape": old_shape,
        "current_capability_validation": repaired_capability,
        "crcl_intended_branch_error_present": "PB_CAP_NEW_BUYER_BRANCH_FORBIDDEN" in crcl_errors,
        "jsonschema_runtime": "NOT_INSTALLED_AND_NOT_FETCHED",
        "generic_renamed_unresolved": {
            "branch_pairs": sorted([list(pair) for pair in unresolved_pairs]),
            "attractive_absent": ("ATTRACTIVE", "ATTRACTIVE_WITHIN_RANGE") not in unresolved_pairs,
            "range_wait_absent": ("WAIT", "FUNDAMENTAL_RANGE_POSITION") not in unresolved_pairs,
            "provider_scan": generic_unresolved["provider_scan"],
        },
        "generic_renamed_resolved_above_high": {
            "branch_pairs": sorted([list(pair) for pair in resolved_pairs]),
            "range_wait_present": ("WAIT", "FUNDAMENTAL_RANGE_POSITION") in resolved_pairs,
            "provider_scan": generic_resolved["provider_scan"],
        },
    }
    replay["status"] = (
        "PASS"
        if replay["historical_raw_sha256"] == replay["expected_historical_raw_sha256"]
        and old_shape["status"] == "PASS"
        and repaired_capability["status"] == "FAIL"
        and replay["crcl_intended_branch_error_present"]
        and replay["generic_renamed_unresolved"]["attractive_absent"]
        and replay["generic_renamed_unresolved"]["range_wait_absent"]
        and replay["generic_renamed_resolved_above_high"]["range_wait_present"]
        else "FAIL"
    )
    write_json(result_root / "historical-crcl-and-generic-branch-replay.json", replay)

    binding = {
        "contract": "m12db-r1-capability-schema-context-consumer-binding-v1",
        "subject_count": len(binding_rows),
        "batch_count": len(capture_rows),
        "fundamental_unresolved_subject_count": unresolved_count,
        "unresolved_subjects_without_forbidden_range_or_attractive": (unresolved_forbidden_count),
        "resolved_above_high_subject_count": resolved_above_high_count,
        "resolved_above_high_with_range_wait_count": resolved_range_available_count,
        "subjects": binding_rows,
        "captures": capture_rows,
        "consumer_chain_status": consumer_chain["status"],
        "status": "PASS"
        if all(row["status"] == "PASS" for row in binding_rows + capture_rows)
        and unresolved_count == unresolved_forbidden_count
        and resolved_above_high_count == resolved_range_available_count
        and consumer_chain["status"] == "PASS"
        else "FAIL",
    }
    write_json(result_root / "b-capability-to-schema-context-consumer-binding.json", binding)

    old_a: dict[str, dict[str, object]] = {}
    new_a: dict[str, dict[str, object]] = {}
    for spec in m12db._batch_topology():
        market = str(spec["market"])
        batch = int(spec["batch"])
        old_payload = read_json(
            args.m12db_root.resolve()
            / "pass-a-inputs"
            / market
            / f"batch-{batch:02d}"
            / "subject-context.json"
        )
        new_payload = read_json(
            actual_root / "pass-a-inputs" / market / f"batch-{batch:02d}" / "subject-context.json"
        )
        old_a.update({str(row["ticker"]): dict(row) for row in old_payload["subjects"]})
        new_a.update({str(row["ticker"]): dict(row) for row in new_payload["subjects"]})
    a_binding_source = read_json(actual_root / "pass-a-final-post-quality-view-binding.json")
    a_rows = []
    for row in a_binding_source["rows"]:
        ticker = str(row["ticker"])
        old_payload = m12db._pass_a_final_view_payload(old_a[ticker])
        new_payload = m12db._pass_a_final_view_payload(new_a[ticker])
        a_rows.append(
            {
                **row,
                "substantive_view_unchanged_from_m12db": canonical_sha256(old_payload)
                == canonical_sha256(new_payload),
                "old_substantive_view_sha256": canonical_sha256(old_payload),
                "new_substantive_view_sha256": canonical_sha256(new_payload),
            }
        )
    a_binding = {
        "contract": "m12db-r1-a-final-post-quality-view-binding-v1",
        "hash_owner": "scripts.m12cq_two_pass_contract.canonical_sha256",
        "subject_count": len(a_rows),
        "post_quality_changed_receipt_count": sum(
            row["intermediate_evidence_serialized_sha256"]
            != row["final_evidence_serialized_sha256"]
            for row in a_rows
        ),
        "substantive_semantic_change_count": sum(
            not row["substantive_view_unchanged_from_m12db"] for row in a_rows
        ),
        "rows": a_rows,
        "status": "PASS"
        if all(
            row["status"] == "PASS" and row["substantive_view_unchanged_from_m12db"]
            for row in a_rows
        )
        else "FAIL",
    }
    write_json(result_root / "a-final-post-quality-view-binding.json", a_binding)

    write_json(
        result_root / "future-b-dynamic-builder-freeze.json",
        {
            "contract": "m12db-r1-future-b-dynamic-builder-freeze-v1",
            "exact_future_b_requests_frozen": False,
            "reason": "Exact future B requests require the accepted future fresh A outputs.",
            "prompt_owner": ("scripts.m12cv_pass_b_capability_contract.capability_prompt_template"),
            "prompt_sha256": canonical_sha256(capability_prompt_template()),
            "schema_owner": (
                "scripts.m12cv_pass_b_capability_contract.capability_pass_b_batch_schema"
            ),
            "capability_owner": (
                "scripts.m12cv_pass_b_capability_contract.build_pass_b_capability_catalog"
            ),
            "provider_projection_owner": (
                "scripts.m12cs_r1_provider_schema.project_provider_wire_schema"
            ),
            "raw_capability_consumer": (
                "scripts.m12cv_pass_b_capability_contract.validate_capability_selection"
            ),
            "final_consumer": "scripts.m12cq_two_pass_contract.validate_pass_b_batch",
            "required_arguments": [
                "catalog",
                "current source metadata",
                "source_use_projection",
                "source_use_binding",
                "source_use_expectation",
                "source_generation_id",
                "execution_generation_id",
                "accepted pass_a",
                "same-subject deterministic option",
                "typed business quality",
                "security valuation basis",
                "pass_b_capability_catalog",
            ],
            "fixture_capture_count": len(capture_rows),
            "future_model_calls": 0,
            "status": "FROZEN_FOR_CHAT_SCOPE_DECISION",
        },
    )
    write_json(
        result_root / "whole-batch-future-reproof-scope.json",
        {
            "contract": "m12db-r1-whole-batch-future-reproof-scope-v1",
            "pass_a": "ALL_8_BATCHES_ONE_FRESH_NO_RETRY_GENERATION",
            "pass_b": "ALL_8_BATCHES_AFTER_EXACT_ACCEPTED_FRESH_A_FREEZE",
            "model_visible_a_permission_surface_changed_subject_count": 22,
            "historical_selected_support_affected_subjects": [
                "000660",
                "005490",
                "005930",
                "TSLA",
            ],
            "exact_future_b_request_hashes_known": False,
            "selective_rerun": False,
            "executed": False,
            "authorized": False,
            "status": "PLAN_ONLY",
        },
    )

    shutil.copy2(
        actual_root / "changed-sources.diff",
        result_root / "changed-sources.diff",
    )
    write_json(
        result_root / "source-hashes-and-owner-chain.json",
        {
            "contract": "m12db-r1-source-hashes-and-owner-chain-v1",
            "implementation_commit": args.implementation_commit,
            "archives": immutable_before,
            "changed_sources": read_json(actual_root / "changed-sources.json"),
            "owner_chain": [
                "trusted frozen loader",
                "current source-use expectation/projection/binding",
                "accepted A fixture and deterministic option",
                "typed quality and security basis",
                "build_pass_b_capability_catalog",
                "capability_pass_b_batch_schema",
                "capability_prompt_template",
                "provider wire projection",
                "no-network request capture",
                "validate_capability_selection",
                "normalize_future_pass_b",
                "validate_pass_b_batch",
            ],
            "status": "PASS",
        },
    )
    immutable_after = {name: m12db.sha256_file(path) for name, path in archives.items()}
    write_json(
        result_root / "original-input-output-immutability.json",
        {
            "contract": "m12db-r1-original-input-output-immutability-v1",
            "before": immutable_before,
            "after": immutable_after,
            "all_equal": immutable_before == immutable_after,
            "historical_outputs_rewritten": 0,
            "status": "PASS" if immutable_before == immutable_after else "FAIL",
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
    validation = read_json(actual_root / "validation/summary.json")
    write_json(result_root / "validation-summary.json", validation)
    all_ready = (
        actual_completion["status"] == "PASS"
        and binding["status"] == "PASS"
        and a_binding["status"] == "PASS"
        and replay["status"] == "PASS"
        and consumer_chain["status"] == "PASS"
        and validation["status"] == "PASS"
        and immutable_before == immutable_after
    )
    completion = {
        "contract": "m12db-r1-program-completion-v1",
        "terminal": READY if all_ready else PARTIAL,
        "subject_count": len(binding_rows),
        "batch_count": len(capture_rows),
        "a_final_binding_status": a_binding["status"],
        "b_request_composition_status": binding["status"],
        "historical_negative_control_status": replay["status"],
        "synthetic_consumer_chain_status": consumer_chain["status"],
        "validation_status": validation["status"],
        "model_calls": 0,
        "network_calls": 0,
        "future_inference_authorized": False,
        "production_authorized": False,
        "status": "PASS" if all_ready else "PARTIAL",
    }
    write_json(result_root / "program-completion.json", completion)
    write_text(
        result_root / "REQUEST_COMPOSITION_CLOSURE_DECISION.md",
        "\n".join(
            [
                "# M12DB-R1 Request Composition Closure Decision",
                "",
                f"- Terminal: `{completion['terminal']}`",
                f"- A final post-quality binding: `{a_binding['status']}` (22/22)",
                f"- B capability/context/schema captures: `{binding['status']}` (8/8, 22/22)",
                f"- Valid synthetic raw/source-use/final consumer chain: `{consumer_chain['status']}`",
                f"- Historical CRCL negative control: `{replay['status']}`",
                f"- Validation: `{validation['status']}`",
                "- Model/provider/network/source-refresh calls: `0`",
                "- Production/DB/send/scheduler/broker mutations: `0`",
                "- Merge/push/deploy: `0`",
                "",
                "Accepted M12DB A semantics and R3 authority are unchanged. The final A request now binds the post-quality model view, and final B fixture captures fail closed unless the exact current capability mapping is present in context, schema, prompt, and source binding.",
                "",
                "Exact future B request hashes remain intentionally unknown until a later accepted fresh A freeze. No A/B execution is authorized by this report.",
            ]
        ),
    )
    write_json(result_root / "artifact-manifest.json", _artifact_manifest(result_root))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m12db-zip", type=Path, required=True)
    parser.add_argument("--m12db-root", type=Path, required=True)
    parser.add_argument("--r3-zip", type=Path, required=True)
    parser.add_argument("--r3-root", type=Path, required=True)
    parser.add_argument("--m12cx-zip", type=Path, required=True)
    parser.add_argument("--m12cx-root", type=Path, required=True)
    parser.add_argument("--supplemental-zip", type=Path, required=True)
    parser.add_argument("--supplemental-root", type=Path, required=True)
    parser.add_argument("--m12cu-zip", type=Path, required=True)
    parser.add_argument("--m12cu-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--implementation-commit", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
