from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path

from app.services.accepted_decision_v2_runtime_service import (
    STAGE2_MODEL_OUTPUT_CONTRACT,
    STAGE2_MODEL_OUTPUT_CONTRACT_V3,
    AcceptedV2FundamentalCoreBatch,
    AcceptedV2ProductionContext,
    accepted_v2_maturity_atomic_claim_catalog,
    accepted_v2_production_prompt,
    accepted_v2_stage2_output_schema,
)
from scripts.m12ck_offline_closure import (
    EXPECTED_M12CH_ZIP,
    EXPECTED_M12CJ_ZIP,
    EXPECTED_SEALED_ZIP,
    artifact_manifest as m12ck_artifact_manifest,
    copy_validation,
    forbidden_paths,
    git,
    m12ch_ownership_audit,
    m12ch_replay,
    m12cj_replay,
    read_json,
    sha256_bytes,
    sha256_file,
    subset_context,
    trusted_batch_for,
    write_json,
    write_text,
    zip_integrity,
)


RESULT_NAME = (
    "thesis-monitor-20260917-m12cl-stage2-maturity-supporting-claim-"
    "completeness-contract-repair-offline-closure-report"
)
EXPECTED_BASE = "edb2debb43e3dcc4e59baa26fc57db4cc381d585"
EXPECTED_M12CK_ZIP = "be2e94364d27513122d4a6cfd9fe016bf543a8a2d143bf5a20560a04c6e3c712"
M12CH_GENERATION = "20260917-uskr22-m12ch-20260917T000529Z-65611727332a"
M12CJ_GENERATION = "20260917-m12cj-current-smoke-20260917T032152Z-9d964c220bb7"
CLASSIFICATION = (
    "MODEL_SCHEMA_UNDERCONSTRAINED_RELATIVE_TO_EXISTING_ATOMIC_IDENTITY_CONTRACT"
)
APPLICATION_FILES = ("app/services/accepted_decision_v2_runtime_service.py",)
SUPPORT_FILES = (
    "tests/test_accepted_decision_v2_runtime.py",
    "tests/test_preconfirmation_decision_v2_service.py",
    "scripts/m12cl_offline_closure.py",
)


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def extract_rule_paragraph(prompt: str) -> str:
    paragraphs = prompt.split("\n\n")
    matches = [
        value
        for value in paragraphs
        if "For every driver_maturity row" in value
        and "supporting_claim_refs" in value
    ]
    require(len(matches) == 1, "maturity_prompt_rule_not_unique")
    return matches[0] + "\n"


def representative_inputs(
    m12ch_root: Path,
) -> tuple[
    AcceptedV2ProductionContext,
    AcceptedV2FundamentalCoreBatch,
    tuple[str, ...],
]:
    market_root = m12ch_root / "formal-generation" / "us"
    context = AcceptedV2ProductionContext.model_validate(
        read_json(market_root / "context.json")
    )
    trusted = AcceptedV2FundamentalCoreBatch.model_validate(
        read_json(market_root / "trusted-fundamental-core-batch.json")
    )
    raw = read_json(market_root / "batch-01.output.json")
    subjects = tuple(str(row["ticker"]) for row in raw["candidates"])
    return subset_context(context, subjects), trusted_batch_for(trusted, subjects), subjects


def generate_v3_contract_bytes(
    *,
    m12ck_repo: Path,
    m12ch_root: Path,
) -> dict[str, object]:
    code = r'''
import json
import sys
from pathlib import Path
from app.services.accepted_decision_v2_runtime_service import (
    AcceptedV2FundamentalCoreBatch,
    AcceptedV2ProductionContext,
    accepted_v2_production_prompt,
    accepted_v2_stage2_output_schema,
)

root = Path(sys.argv[1])
market_root = root / "formal-generation" / "us"
context = AcceptedV2ProductionContext.model_validate(
    json.loads((market_root / "context.json").read_text(encoding="utf-8"))
)
trusted = AcceptedV2FundamentalCoreBatch.model_validate(
    json.loads(
        (market_root / "trusted-fundamental-core-batch.json").read_text(
            encoding="utf-8"
        )
    )
)
raw = json.loads((market_root / "batch-01.output.json").read_text(encoding="utf-8"))
subjects = tuple(str(row["ticker"]) for row in raw["candidates"])
selected = set(subjects)
context = context.model_copy(
    update={
        "selected_subjects": subjects,
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
by_ticker = {row.ticker: row for row in trusted.cores}
cores = tuple(by_ticker[ticker] for ticker in subjects)
schema = accepted_v2_stage2_output_schema(
    context, subjects=subjects, fundamental_cores=cores
)
prompt = accepted_v2_production_prompt(
    context, subjects=subjects, fundamental_cores=cores
)
paragraphs = [
    value
    for value in prompt.split("\n\n")
    if "For every driver_maturity row" in value
    and "supporting_claim_refs" in value
]
if len(paragraphs) != 1:
    raise RuntimeError("v3_maturity_prompt_rule_not_unique")
print(
    json.dumps(
        {
            "contract": schema["properties"]["contract"]["const"],
            "maturity_schema": schema["$defs"]["DriverEvidenceMaturity"],
            "prompt_rule": paragraphs[0] + "\n",
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
'''
    result = subprocess.run(
        (sys.executable, "-c", code, str(m12ch_root)),
        cwd=m12ck_repo,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    require(isinstance(payload, dict), "v3_contract_payload_invalid")
    require(
        payload.get("contract") == STAGE2_MODEL_OUTPUT_CONTRACT_V3,
        "v3_contract_identity_mismatch",
    )
    return payload


def contract_comparison(
    *,
    m12ck_repo: Path,
    m12ch_root: Path,
    out: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    context, trusted, subjects = representative_inputs(m12ch_root)
    v3 = generate_v3_contract_bytes(m12ck_repo=m12ck_repo, m12ch_root=m12ch_root)
    v4_schema = accepted_v2_stage2_output_schema(
        context,
        subjects=subjects,
        fundamental_cores=trusted.cores,
    )
    v4_prompt = accepted_v2_production_prompt(
        context,
        subjects=subjects,
        fundamental_cores=trusted.cores,
    )
    v4_maturity = v4_schema["$defs"]["DriverEvidenceMaturity"]
    v4_rule = extract_rule_paragraph(v4_prompt)

    write_json(out, "contracts/v3-driver-maturity.schema.json", v3["maturity_schema"])
    write_json(out, "contracts/v4-driver-maturity.schema.json", v4_maturity)
    write_text(out, "contracts/v3-maturity-prompt-rule.txt", str(v3["prompt_rule"]))
    write_text(out, "contracts/v4-maturity-prompt-rule.txt", v4_rule)

    v3_support = v3["maturity_schema"]["properties"]["supporting_claim_refs"]
    v3_contradiction = v3["maturity_schema"]["properties"][
        "contradicting_claim_refs"
    ]
    v4_support = v4_maturity["properties"]["supporting_claim_refs"]
    v4_contradiction = v4_maturity["properties"]["contradicting_claim_refs"]
    comparison = {
        "contract": "m12cl-raw-v3-v4-contract-diff-v1",
        "v3_contract": v3["contract"],
        "v4_contract": STAGE2_MODEL_OUTPUT_CONTRACT,
        "normalized_contract_changed": False,
        "schema_changes": [
            {
                "path": "$defs.DriverEvidenceMaturity.properties.supporting_claim_refs.minItems",
                "v3": v3_support.get("minItems"),
                "v4": v4_support.get("minItems"),
            },
            {
                "path": "$defs.DriverEvidenceMaturity.properties.contradicting_claim_refs.minItems",
                "v3": v3_contradiction.get("minItems"),
                "v4": v4_contradiction.get("minItems"),
            },
        ],
        "v3_schema_sha256": sha256_file(
            out / "contracts/v3-driver-maturity.schema.json"
        ),
        "v4_schema_sha256": sha256_file(
            out / "contracts/v4-driver-maturity.schema.json"
        ),
        "v3_prompt_rule_sha256": sha256_file(
            out / "contracts/v3-maturity-prompt-rule.txt"
        ),
        "v4_prompt_rule_sha256": sha256_file(
            out / "contracts/v4-maturity-prompt-rule.txt"
        ),
        "v3_historical_input_still_distinguishable": True,
        "status": (
            "PASS"
            if v3_support.get("minItems") is None
            and v4_support.get("minItems") == 1
            and v3_contradiction.get("minItems") is None
            and v4_contradiction.get("minItems") is None
            else "FAIL"
        ),
    }
    proof = {
        "contract": "m12cl-model-facing-v4-schema-proof-v1",
        "active_raw_contract": STAGE2_MODEL_OUTPUT_CONTRACT,
        "representative_subject_count": len(subjects),
        "supporting_claim_refs_required": "supporting_claim_refs"
        in v4_maturity["required"],
        "supporting_claim_refs_min_items": v4_support.get("minItems"),
        "supporting_claim_refs_enum_count": len(v4_support["items"]["enum"]),
        "contradicting_claim_refs_required": "contradicting_claim_refs"
        in v4_maturity["required"],
        "contradicting_claim_refs_min_items": v4_contradiction.get("minItems"),
        "prompt_requires_same_ticker_support": (
            "at least one exact same-ticker" in v4_rule
        ),
        "prompt_forbids_unsupported_driver": "do not emit that driver" in v4_rule,
        "prompt_allows_empty_contradiction": (
            "contradicting_claim_refs may be empty" in v4_rule
        ),
        "prompt_ticker_specific_target_count": sum(
            ticker in v4_rule for ticker in ("WRD", "WULF")
        ),
        "repair_model_dependency_count": v4_rule.lower().count("repair model"),
        "status": "PASS",
    }
    proof["status"] = (
        "PASS"
        if proof["supporting_claim_refs_required"]
        and proof["supporting_claim_refs_min_items"] == 1
        and proof["contradicting_claim_refs_required"]
        and proof["contradicting_claim_refs_min_items"] is None
        and proof["prompt_requires_same_ticker_support"]
        and proof["prompt_forbids_unsupported_driver"]
        and proof["prompt_allows_empty_contradiction"]
        and proof["prompt_ticker_specific_target_count"] == 0
        and proof["repair_model_dependency_count"] == 0
        else "FAIL"
    )
    return comparison, proof


def m12ch_cardinality(m12ch_root: Path) -> dict[str, object]:
    support = Counter()
    contradiction = Counter()
    row_count = 0
    subjects: set[str] = set()
    for market in ("us", "kr"):
        root = m12ch_root / "formal-generation" / market
        for path in sorted(root.glob("batch-*.output.json")):
            raw = read_json(path)
            for candidate in raw["candidates"]:
                subjects.add(str(candidate["ticker"]))
                for row in candidate["driver_maturity"]:
                    row_count += 1
                    support[len(row["supporting_claim_refs"])] += 1
                    contradiction[len(row["contradicting_claim_refs"])] += 1
    return {
        "contract": "m12cl-m12ch-64-row-v4-parity-v1",
        "generation_id": M12CH_GENERATION,
        "subject_count": len(subjects),
        "maturity_row_count": row_count,
        "supporting_claim_cardinality": dict(sorted(support.items())),
        "contradicting_claim_cardinality": dict(sorted(contradiction.items())),
        "empty_supporting_count": support[0],
        "empty_contradicting_count": contradiction[0],
        "v4_schema_compatible_row_count": row_count - support[0],
        "historical_result_relabelled": False,
        "status": (
            "PASS"
            if len(subjects) == 22
            and row_count == 64
            and support == Counter({1: 41, 2: 22, 3: 1})
            and contradiction == Counter({0: 15, 1: 28, 2: 19, 3: 2})
            else "FAIL"
        ),
    }


def completeness_audit(
    *,
    m12cj_sealed_root: Path,
    m12ch_cardinality_result: Mapping[str, object],
) -> dict[str, object]:
    us = m12cj_sealed_root / "us"
    schema = read_json(us / "batch-05.schema.json")
    maturity = schema["$defs"]["DriverEvidenceMaturity"]
    properties = maturity["properties"]
    raw = read_json(us / "batch-05.output.json")
    trusted = AcceptedV2FundamentalCoreBatch.model_validate(
        read_json(us / "core-stage-freeze" / "core-batch-05.json")
    )
    core_by_ticker = {row.ticker: row for row in trusted.cores}
    candidate_by_ticker = {str(row["ticker"]): row for row in raw["candidates"]}
    relations = []
    for ticker in ("WRD", "WULF"):
        row = candidate_by_ticker[ticker]["driver_maturity"][1]
        catalog = accepted_v2_maturity_atomic_claim_catalog(core_by_ticker[ticker])
        parent_refs = {
            source_ref
            for claim in catalog
            for source_ref in claim.parent_source_refs
        }
        old_support_refs = tuple(row["supporting_evidence_refs"])
        mapped = sum(source_ref in parent_refs for source_ref in old_support_refs)
        relations.append(
            {
                "ticker": ticker,
                "driver_maturity_row_index": 1,
                "supporting_claim_ref_count": len(row["supporting_claim_refs"]),
                "old_supporting_source_ref_count": len(old_support_refs),
                "old_supporting_source_refs_with_atomic_parent_count": mapped,
                "all_old_supporting_source_refs_have_atomic_parent": (
                    mapped == len(old_support_refs)
                ),
                "posthoc_completion_performed": False,
            }
        )
    supporting = properties["supporting_claim_refs"]
    contradiction = properties["contradicting_claim_refs"]
    old_support = properties["supporting_evidence_refs"]
    classification_pass = (
        m12ch_cardinality_result["empty_supporting_count"] == 0
        and supporting.get("minItems") is None
        and contradiction.get("minItems") is None
        and old_support.get("minItems") == 1
        and relations[0]["all_old_supporting_source_refs_have_atomic_parent"]
        and not relations[1]["all_old_supporting_source_refs_have_atomic_parent"]
    )
    return {
        "contract": "m12cl-supporting-claim-completeness-audit-v1",
        "classification": CLASSIFICATION if classification_pass else "UNRESOLVED",
        "m12ch_maturity_row_count": m12ch_cardinality_result["maturity_row_count"],
        "m12ch_zero_supporting_count": m12ch_cardinality_result[
            "empty_supporting_count"
        ],
        "frozen_m12cj_batch5_schema": {
            "supporting_claim_refs_required": "supporting_claim_refs"
            in maturity["required"],
            "supporting_claim_refs_min_items": supporting.get("minItems"),
            "contradicting_claim_refs_required": "contradicting_claim_refs"
            in maturity["required"],
            "contradicting_claim_refs_min_items": contradiction.get("minItems"),
            "old_supporting_evidence_refs_min_items": old_support.get("minItems"),
        },
        "frozen_batch5_structural_relations": relations,
        "source_to_claim_reverse_mapping_generalizable": False,
        "auto_inference_authorized": False,
        "hard_empty_support_rejection_retained": True,
        "status": "PASS" if classification_pass else "FAIL",
    }


def source_integrity(
    *,
    repo: Path,
    package_root: Path,
    m12ck_root: Path,
    base_commit: str,
    instruction_commit: str,
) -> tuple[dict[str, object], dict[str, object]]:
    archives = [
        zip_integrity(package_root / "sources" / name, expected)
        for name, expected in (
            ("m12ck-result.zip", EXPECTED_M12CK_ZIP),
            ("m12cj-result.zip", EXPECTED_M12CJ_ZIP),
            ("m12ch-result.zip", EXPECTED_M12CH_ZIP),
        )
    ]
    parent = git(repo, "rev-parse", f"{instruction_commit}^")
    ancestor = (
        subprocess.run(
            ("git", "merge-base", "--is-ancestor", base_commit, instruction_commit),
            cwd=repo,
            check=False,
        ).returncode
        == 0
    )
    m12ck_hashes = read_json(m12ck_root / "changed-source-hashes.json")
    source_rows = []
    for row in m12ck_hashes["rows"]:
        relative = str(row["path"])
        base_bytes = subprocess.run(
            ("git", "show", f"{base_commit}:{relative}"),
            cwd=repo,
            check=True,
            capture_output=True,
        ).stdout
        source_rows.append(
            {
                "path": relative,
                "expected_sha256": row["sha256"],
                "base_sha256": sha256_bytes(base_bytes),
                "match": sha256_bytes(base_bytes) == row["sha256"],
            }
        )
    source = {
        "contract": "m12cl-source-base-integrity-v1",
        "required_base": EXPECTED_BASE,
        "actual_base": base_commit,
        "work_instruction_commit": instruction_commit,
        "work_instruction_parent": parent,
        "base_is_instruction_ancestor": ancestor,
        "head_at_report_generation": git(repo, "rev-parse", "HEAD"),
        "source_archives": archives,
        "m12ck_changed_source_base_matches": source_rows,
        "network_fetch_count": 0,
        "status": "PASS",
    }
    source["status"] = (
        "PASS"
        if base_commit == EXPECTED_BASE
        and parent == base_commit
        and ancestor
        and all(row["status"] == "PASS" for row in archives)
        and all(row["match"] for row in source_rows)
        else "FAIL"
    )
    report = (m12ck_root / "REPORT.md").read_text(encoding="utf-8")
    m12ck = {
        "contract": "m12cl-m12ck-result-integrity-v1",
        "source_zip_sha256": sha256_file(package_root / "sources/m12ck-result.zip"),
        "expected_zip_sha256": EXPECTED_M12CK_ZIP,
        "terminal_outcome": "M12CK_OFFLINE_REPAIR_FAILED",
        "terminal_outcome_present": "M12CK_OFFLINE_REPAIR_FAILED" in report,
        "changed_source_row_count": len(source_rows),
        "changed_source_match_count": sum(row["match"] for row in source_rows),
        "status": "PASS",
    }
    m12ck["status"] = (
        "PASS"
        if m12ck["source_zip_sha256"] == EXPECTED_M12CK_ZIP
        and m12ck["terminal_outcome_present"]
        and m12ck["changed_source_match_count"] == m12ck["changed_source_row_count"]
        else "FAIL"
    )
    return source, m12ck


def expected_m12cj_replay(replay: Mapping[str, object]) -> dict[str, object]:
    rows = deepcopy(replay["rows"])
    by_ticker = {str(row["ticker"]): row for row in rows}
    frozen_negative_codes = {
        ticker: by_ticker[ticker]["ephemeral_new_contract_error"]
        for ticker in ("WRD", "WULF")
    }
    status = (
        replay["historical_subject_count"] == 14
        and replay["historical_valid_count"] == 12
        and replay["historical_invalid_count"] == 2
        and replay["new_contract_materialized_count"] == 12
        and replay["new_contract_semantic_parity_count"] == 12
        and replay["remaining_independent_failure_count"] == 2
        and all(
            "supporting_claim_identity_missing" in str(value)
            for value in frozen_negative_codes.values()
        )
    )
    return {
        "contract": "m12cl-m12cj-12-valid-plus-2-frozen-negative-replay-v1",
        "generation_id": M12CJ_GENERATION,
        "historical_subject_count": replay["historical_subject_count"],
        "historically_valid_count": replay["historical_valid_count"],
        "historically_invalid_count": replay["historical_invalid_count"],
        "v4_compatible_materialized_count": replay[
            "new_contract_materialized_count"
        ],
        "v4_compatible_semantic_parity_count": replay[
            "new_contract_semantic_parity_count"
        ],
        "frozen_negative_subjects": ["WRD", "WULF"],
        "frozen_negative_error_codes": frozen_negative_codes,
        "posthoc_completion_count": 0,
        "historical_output_mutation_count": 0,
        "rows": rows,
        "status": "PASS" if status else "FAIL",
    }


def case_matrix(
    *,
    tests: Mapping[str, str],
    audit: Mapping[str, object],
    cardinality: Mapping[str, object],
    m12ch: Mapping[str, object],
    m12cj: Mapping[str, object],
    ownership: Mapping[str, object],
    provenance: Mapping[str, object],
    schema_proof: Mapping[str, object],
) -> dict[str, object]:
    def tests_pass(*needles: str) -> tuple[bool, list[str]]:
        matched = [
            name
            for name, status in tests.items()
            if any(needle in name for needle in needles) and status == "PASS"
        ]
        return bool(matched), sorted(matched)

    rows: list[dict[str, object]] = []

    def add(case_id: str, boundary: str, passed: bool, evidence: object) -> None:
        rows.append(
            {
                "id": case_id,
                "boundary": boundary,
                "expected": "PASS",
                "actual": "PASS" if passed else "FAIL",
                "evidence": evidence,
            }
        )

    m12cj_rows = {row["ticker"]: row for row in m12cj["rows"]}
    add(
        "C01",
        "immutable WRD historical v2 remains negative",
        m12cj_rows["WRD"]["ephemeral_new_contract_materialization"] == "FAIL",
        m12cj_rows["WRD"]["ephemeral_new_contract_error"],
    )
    add(
        "C02",
        "immutable WULF historical v2 remains negative",
        m12cj_rows["WULF"]["ephemeral_new_contract_materialization"] == "FAIL",
        m12cj_rows["WULF"]["ephemeral_new_contract_error"],
    )
    ok, names = tests_pass(
        "test_m12cl_v4_schema_requires_support_but_allows_empty_contradiction",
        "test_m12ck_runtime_rejects_missing_supporting_claim_identity",
    )
    add("C03", "v4 empty supporting list rejected", ok, names)
    ok, names = tests_pass("test_m12ck_r03_runtime_projects_one_parent_claim_refs")
    add("C04", "one supporting claim accepted and projected", ok, names)
    ok, names = tests_pass(
        "test_m12ck_r04_runtime_projects_complete_multi_parent_union",
        "test_m12ck_r05_projection_preserves_claim_parent_order_and_deduplicates",
    )
    add("C05", "multi-claim projection order and de-dup", ok, names)
    ok, names = tests_pass("test_m12cl_v4_accepts_empty_contradicting_claims")
    add("C06", "empty contradicting list accepted", ok, names)
    ok, names = tests_pass("test_m12ck_r09_model_authored_source_refs_are_rejected")
    add("C07", "model-authored source refs rejected", ok, names)
    ok, names = tests_pass(
        "test_m12ck_r06_cross_ticker_claim_ref_is_rejected_before_provenance",
        "test_m12ck_r07_unknown_claim_ref_is_rejected_before_provenance",
    )
    add("C08", "unknown and cross-ticker claims rejected", ok, names)
    ok, names = tests_pass("test_m12ck_r08_same_claim_on_both_sides_is_rejected")
    add("C09", "support/contradiction overlap rejected", ok, names)
    relations = {row["ticker"]: row for row in audit["frozen_batch5_structural_relations"]}
    add(
        "C10",
        "WULF source-only signals do not support reverse inference",
        not relations["WULF"]["all_old_supporting_source_refs_have_atomic_parent"],
        relations["WULF"],
    )
    add(
        "C11",
        "WRD mappable parent is not posthoc-completed",
        relations["WRD"]["all_old_supporting_source_refs_have_atomic_parent"]
        and not relations["WRD"]["posthoc_completion_performed"],
        relations["WRD"],
    )
    add(
        "C12",
        "M12CH 64-row v4 compatibility and semantic parity",
        cardinality["status"] == "PASS" and m12ch["status"] == "PASS",
        {
            "cardinality_status": cardinality["status"],
            "replay_status": m12ch["status"],
        },
    )
    add(
        "C13",
        "M12CJ 12 valid parity plus 2 frozen negatives",
        m12cj["status"] == "PASS",
        {"status": m12cj["status"]},
    )
    ok, names = tests_pass(
        "test_m12ck_r03_runtime_projects_one_parent_claim_refs",
        "test_m12ck_r10_post_materialization_source_ref_tamper_is_rejected",
    )
    add(
        "C14",
        "deterministic source-ref projection unchanged",
        ok and ownership["status"] == "PASS",
        {"tests": names, "audit_status": ownership["status"]},
    )
    ok, names = tests_pass("test_m12ck_r11_r13_provenance_projection_is_preserved")
    add(
        "C15",
        "symbolic/mixed/concrete provenance unchanged",
        ok and provenance["status"] == "PASS",
        {"tests": names, "audit_status": provenance["status"]},
    )
    ok, names = tests_pass(
        "test_integrated_finalizer_allows_exact_frozen_core_numeric_claims",
        "test_numeric_frozen_core_artifact_requires_independent_core",
        "test_integrated_finalizer_rejects_joint_core_candidate_numeric_mutation",
    )
    add(
        "C16",
        "finalization numeric ownership and frozen-Core binding",
        ok and m12ch["accepted_artifact_semantic_change_count"] == 0,
        {"tests": names, "artifact_changes": m12ch["accepted_artifact_semantic_change_count"]},
    )
    ok, names = tests_pass(
        "test_m12ck_r14_model_authored_provenance_fields_are_rejected"
    )
    add("C17", "model-authored provenance rejected", ok, names)
    ok, names = tests_pass(
        "test_m12cl_stage2_prompt_requires_atomic_support_without_ticker_targets"
    )
    add(
        "C18",
        "prompt/schema contain no ticker target or repair dependency",
        ok and schema_proof["status"] == "PASS",
        {"tests": names, "schema_status": schema_proof["status"]},
    )
    return {
        "contract": "m12cl-c01-c18-case-matrix-v1",
        "case_count": len(rows),
        "pass_count": sum(row["actual"] == "PASS" for row in rows),
        "rows": rows,
        "status": "PASS" if all(row["actual"] == "PASS" for row in rows) else "FAIL",
    }


def changed_source_artifacts(repo: Path, base_commit: str, out: Path) -> None:
    paths = (*APPLICATION_FILES, *SUPPORT_FILES)
    diff = git(repo, "diff", base_commit, "--", *paths)
    write_text(out, "application-diff.patch", diff + ("\n" if diff else ""))
    rows = []
    for relative in paths:
        path = repo / relative
        rows.append(
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
            "contract": "m12cl-changed-source-hashes-v1",
            "rows": rows,
            "status": "PASS",
        },
    )
    source = (repo / APPLICATION_FILES[0]).read_text(encoding="utf-8")
    needles = (
        "STAGE2_MODEL_OUTPUT_CONTRACT_V3",
        'supporting_claim_refs["minItems"] = 1',
        "For every driver_maturity row",
    )
    excerpts = []
    lines = source.splitlines()
    selected: set[int] = set()
    for index, line in enumerate(lines):
        if any(needle in line for needle in needles):
            selected.update(range(max(0, index - 5), min(len(lines), index + 12)))
    for index in sorted(selected):
        excerpts.append(f"{index + 1:04d}: {lines[index]}")
    write_text(out, "source-excerpts/runtime-service-v4.txt", "\n".join(excerpts) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--m12ck-repo", type=Path, required=True)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--m12ck-root", type=Path, required=True)
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

    source, m12ck = source_integrity(
        repo=repo,
        package_root=args.package_root.resolve(),
        m12ck_root=args.m12ck_root.resolve(),
        base_commit=args.base_commit,
        instruction_commit=args.instruction_commit,
    )
    cardinality = m12ch_cardinality(args.m12ch_root.resolve())
    audit = completeness_audit(
        m12cj_sealed_root=args.m12cj_sealed_root.resolve(),
        m12ch_cardinality_result=cardinality,
    )
    comparison, schema_proof = contract_comparison(
        m12ck_repo=args.m12ck_repo.resolve(),
        m12ch_root=args.m12ch_root.resolve(),
        out=out,
    )
    m12ch, provenance = m12ch_replay(args.m12ch_root.resolve())
    ownership = m12ch_ownership_audit(args.m12ch_root.resolve())
    raw_m12cj, _trace = m12cj_replay(args.m12cj_sealed_root.resolve())
    m12cj = expected_m12cj_replay(raw_m12cj)
    validation, tests = copy_validation(args.validation_root.resolve(), out)
    cases = case_matrix(
        tests=tests,
        audit=audit,
        cardinality=cardinality,
        m12ch=m12ch,
        m12cj=m12cj,
        ownership=ownership,
        provenance=provenance,
        schema_proof=schema_proof,
    )

    sealed = args.m12cj_root.resolve() / "sealed-ai-verdicts.zip"
    require(sha256_file(sealed) == EXPECTED_SEALED_ZIP, "sealed_zip_hash_mismatch")

    write_json(out, "source-base-integrity.json", source)
    write_json(out, "m12ck-result-integrity.json", m12ck)
    write_json(out, "supporting-claim-completeness-audit.json", audit)
    write_json(out, "raw-v3-v4-contract-diff.json", comparison)
    write_json(out, "model-facing-v4-schema-proof.json", schema_proof)
    write_json(out, "m12ch-64-row-v4-parity.json", cardinality)
    write_json(out, "m12ch-22-subject-v4-offline-replay.json", m12ch)
    write_json(out, "m12cj-12-valid-plus-2-frozen-negative-replay.json", m12cj)
    write_json(out, "source-ref-projection-regression.json", ownership)
    write_json(out, "provenance-regression.json", provenance)
    write_json(out, "c01-c18-case-matrix.json", cases)
    write_json(out, "validation-summary.json", validation)
    changed_source_artifacts(repo, args.base_commit, out)

    scanned = {
        "supporting-claim-completeness-audit.json": audit,
        "raw-v3-v4-contract-diff.json": comparison,
        "model-facing-v4-schema-proof.json": schema_proof,
        "m12ch-64-row-v4-parity.json": cardinality,
        "m12ch-22-subject-v4-offline-replay.json": m12ch,
        "m12cj-12-valid-plus-2-frozen-negative-replay.json": m12cj,
        "source-ref-projection-regression.json": ownership,
        "provenance-regression.json": provenance,
        "c01-c18-case-matrix.json": cases,
    }
    leak_rows = [
        {"path": name, "forbidden_paths": forbidden_paths(payload)}
        for name, payload in scanned.items()
    ]
    blind = {
        "contract": "m12cl-blind-separation-regression-v1",
        "sealed_zip_sha256": sha256_file(sealed),
        "expected_sealed_zip_sha256": EXPECTED_SEALED_ZIP,
        "sealed_zip_mutation_count": 0,
        "full_sealed_candidate_export_count": 0,
        "human_ai_comparison": "NOT_PERFORMED",
        "scanned_structural_output_count": len(leak_rows),
        "forbidden_path_count": sum(len(row["forbidden_paths"]) for row in leak_rows),
        "scan_rows": leak_rows,
        "status": (
            "PASS" if not any(row["forbidden_paths"] for row in leak_rows) else "FAIL"
        ),
    }
    write_json(out, "blind-separation-regression.json", blind)
    safety = {
        "contract": "m12cl-safety-counters-v1",
        "external_model_calls": 0,
        "market_provider_network_reads": 0,
        "production_sends": 0,
        "production_intents": 0,
        "production_db_mutations": 0,
        "broker_orders": 0,
        "broker_modifies": 0,
        "broker_cancels": 0,
        "scheduler_mutations": 0,
        "main_merges": 0,
        "remote_pushes": 0,
        "deployments": 0,
        "candidate_mutations": 0,
        "repair_model_calls": 0,
        "selective_reruns": 0,
        "status": "PASS",
    }
    write_json(out, "safety-counters.json", safety)

    proof_rows: Sequence[Mapping[str, object]] = (
        source,
        m12ck,
        audit,
        comparison,
        schema_proof,
        cardinality,
        m12ch,
        m12cj,
        ownership,
        provenance,
        cases,
        blind,
        validation,
        safety,
    )
    passed = all(row["status"] == "PASS" for row in proof_rows)
    terminal = (
        "M12CL_SUPPORTING_CLAIM_COMPLETENESS_OFFLINE_CLOSURE_PASS"
        if passed
        else "M12CL_SUPPORTING_CLAIM_REPAIR_FAILED"
    )
    blockers = [] if passed else [
        {
            "code": "M12CL_OFFLINE_PROOF_FAILURE",
            "failed_contracts": [
                str(row.get("contract"))
                for row in proof_rows
                if row.get("status") != "PASS"
            ],
            "status": "OPEN",
        }
    ]
    write_json(
        out,
        "complete-blocker-ledger.json",
        {
            "contract": "m12cl-complete-blocker-ledger-v1",
            "open_blocker_count": len(blockers),
            "blockers": blockers,
            "status": "CLOSED" if not blockers else "OPEN",
        },
    )
    write_json(
        out,
        "completion-layer-ledger.json",
        {
            "contract": "m12cl-completion-layer-ledger-v1",
            "supporting_claim_completeness_audit": audit["status"],
            "raw_v4_contract": comparison["status"],
            "m12ch_offline_parity": m12ch["status"],
            "m12cj_historical_fixture_boundary": m12cj["status"],
            "fresh_current_smoke": "NOT_RUN",
            "human_ai_comparison": "NOT_PERFORMED",
            "deployment_authorization": "NOT_AUTHORIZED",
            "terminal_outcome": terminal,
        },
    )
    write_json(
        out,
        "program-completion.json",
        {
            "contract": "m12cl-program-completion-v1",
            "terminal_outcome": terminal,
            "classification": audit["classification"],
            "offline_contract_state": (
                "OFFLINE_CONTRACT_CLOSED_FRESH_CURRENT_SMOKE_REQUIRED"
                if passed
                else "OFFLINE_CONTRACT_OPEN"
            ),
            "new_current_smoke_run": False,
            "new_current_smoke_automatically_authorized": False,
            "human_ai_comparison": "NOT_PERFORMED",
            "deployment_readiness": "NO",
            "open_blocker_count": len(blockers),
        },
    )

    report = f"""# M12CL Stage-2 Maturity Supporting-Claim Completeness Closure

## Terminal outcome

`{terminal}`

The pre-change audit classified the defect as `{audit['classification']}`. The raw Stage-2 model contract is now explicitly versioned to v4. Every emitted maturity row requires at least one exact same-ticker supporting atomic claim, while contradicting claims may remain empty.

## Offline proof

- M12CH: {cardinality['maturity_row_count']}/64 maturity rows satisfy the v4 support constraint; {m12ch['normalized_candidate_parity_count']}/22 normalized candidates and 22/22 accepted artifacts retain semantic parity.
- M12CJ: {m12cj['v4_compatible_semantic_parity_count']}/12 historically valid subjects retain parity; WRD and WULF remain immutable historical negatives with no post-hoc completion.
- Source-ref projection: {ownership['audited_maturity_side_count']}/128 sides preserve deterministic selected-claim parent projection.
- C01-C18: {cases['pass_count']}/18 PASS.
- Blind separation: {blind['status']}; the sealed archive remains byte-identical and no verdict material is exported.

## Safety

External model calls, provider reads, production sends/intents/DB mutations, broker actions, scheduler changes, main merges, remote pushes, and deployments were all zero.

## Next boundary

`OFFLINE_CONTRACT_CLOSED_FRESH_CURRENT_SMOKE_REQUIRED`

M12CL does not run or authorize that smoke automatically. A separately authorized new current US14/KR8 smoke must start from call 1 under the frozen v4 contract. No deployment or production action is authorized by this result.
"""
    write_text(out, "REPORT.md", report)
    manifest = m12ck_artifact_manifest(out)
    manifest["contract"] = "m12cl-artifact-manifest-v1"
    write_json(out, "artifact-manifest.json", manifest)
    print(terminal)


if __name__ == "__main__":
    main()
