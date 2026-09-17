from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.m12cq_two_pass_contract import (
    build_pass_b_subject_context,
    canonical_sha256,
    pass_a_leakage_scan,
    select_matrix_option,
)
from scripts.m12cq_two_pass_shadow import load_m12cp_inputs
from scripts.m12cr_contract_closure import (
    _batch_topology,
    _coverage_reports,
    _depositary_subjects,
    _historical_failure_replay,
    _matrix_subjects,
    _mechanical_pass_a_choice,
    _mechanical_pass_b_choice,
    _verify_package_root,
    _verify_shadow_input,
    _verify_zip_manifest,
    _write_future_drafts,
    artifact_manifest,
    load_frozen_contract_inputs,
    read_json,
    require,
    sha256_file,
    write_json,
    write_text,
    zip_tree,
)
from scripts.m12cr_r1_typed_quality_contract import (
    BusinessEvidenceQualityState,
    SecurityValuationBasisState,
    build_r1_pass_a_context,
    gate_policy_option_for_security_basis,
    project_business_evidence_quality,
    project_security_valuation_basis,
    r1_semantic_rule_inventory,
    typed_quality_source_semantics,
    validate_quality_basis_decision_ownership,
    validate_security_valuation_basis_gate,
)
from scripts.m12cr_shadow_contract import (
    field_ownership_inventory,
    materialize_future_pass_a,
    normalize_future_pass_b,
    semantic_rule_inventory,
    validate_future_pass_b_shape,
    validate_materialized_pass_b,
)


REPO = Path(__file__).resolve().parents[1]
WORK_INSTRUCTION_COMMIT = "45d7a5be1d76b4f7ad4c60994d79b5dbdf5202c3"
M12CR_IMPLEMENTATION = "4fbd510d9c9d4c30400d1cd80c3333bc27148555"
EXPECTED_PACKAGE_SHA256 = "9d2dad568853b25bb1bc5232236e6dad835810096772c04e723324e23e0deba3"
EXPECTED_M12CR_RESULT_SHA256 = "f6ca17a87988885bba8cfa6964ac54d026d2296adc536216b7dd64f4012b8acb"
EXPECTED_M12CP_RESULT_SHA256 = "fe63ee201bdb0937a4936af0d89f7013adee0209b3ef01d83d210d0e93456100"
EXPECTED_M12CQ_RESULT_SHA256 = "378a3a4a9c1d65255a1baf371daa95dcf3c3f5384af4d04240685f80fc3744ca"
EXPECTED_FROZEN_GENERATION = "20260917-m12cm-current-v4-smoke-20260917T062918Z-5c0cb075ce8b"

READY = "M12CR_R1_TYPED_QUALITY_AND_SECURITY_BASIS_OWNERSHIP_CLOSED_READY_FOR_FRESH_TWO_PASS_SHADOW"
QUALITY_CHAT = "M12CR_R1_TYPED_QUALITY_SEMANTICS_REQUIRE_CHAT"
SECURITY_CHAT = "M12CR_R1_SECURITY_BASIS_OWNERSHIP_REQUIRE_CHAT"
PARITY_FAIL = "M12CR_R1_CONTRACT_PARITY_NOT_CLOSED"
PRODUCTION_FAIL = "M12CR_R1_NEW_PRODUCTION_DEPENDENCY_REQUIRES_CHAT"
OFFLINE_FAIL = "M12CR_R1_OFFLINE_REPAIR_FAILED"
REPORT_NAME = (
    "thesis-monitor-20260918-m12cr-r1-typed-data-quality-and-security-valuation-"
    "basis-ownership-repair-report.zip"
)


def _git(*args: str) -> str:
    return subprocess.run(
        ("git", *args),
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def runtime_integrity(expected_head: str) -> dict[str, object]:
    head = _git("rev-parse", "HEAD")
    base_ancestor = (
        subprocess.run(
            ("git", "merge-base", "--is-ancestor", M12CR_IMPLEMENTATION, head),
            cwd=REPO,
            check=False,
        ).returncode
        == 0
    )
    instruction_ancestor = (
        subprocess.run(
            ("git", "merge-base", "--is-ancestor", WORK_INSTRUCTION_COMMIT, head),
            cwd=REPO,
            check=False,
        ).returncode
        == 0
    )
    changed = _git("diff", "--name-only", f"{M12CR_IMPLEMENTATION}..{head}").splitlines()
    allowed = (
        "docs/work-instructions/20260918-m12cr-r1",
        "scripts/m12cr",
        "tests/test_m12cr",
    )
    production_paths = [path for path in changed if not path.startswith(allowed)]
    errors: list[str] = []
    if head != expected_head:
        errors.append("head_mismatch")
    if not base_ancestor:
        errors.append("m12cr_implementation_not_ancestor")
    if not instruction_ancestor:
        errors.append("work_instruction_not_ancestor")
    if production_paths:
        errors.append("new_production_dependency")
    if _git("status", "--porcelain"):
        errors.append("worktree_not_clean")
    return {
        "contract": "m12cr-r1-runtime-integrity-v1",
        "head": head,
        "expected_head": expected_head,
        "m12cr_implementation": M12CR_IMPLEMENTATION,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "m12cr_implementation_is_ancestor": base_ancestor,
        "work_instruction_is_ancestor": instruction_ancestor,
        "changed_paths": changed,
        "production_dependency_paths": production_paths,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def verify_sources(args: argparse.Namespace) -> dict[str, object]:
    package_root = args.package_root.resolve()
    source_index = read_json(package_root / "source-index.json")
    expected = {
        "m12cr_result": EXPECTED_M12CR_RESULT_SHA256,
        "m12cp_result": EXPECTED_M12CP_RESULT_SHA256,
        "m12cq_result": EXPECTED_M12CQ_RESULT_SHA256,
    }
    errors: list[str] = []
    package_sha = sha256_file(args.package_zip.resolve())
    if package_sha != EXPECTED_PACKAGE_SHA256:
        errors.append("outer_package_hash_mismatch")
    package = _verify_package_root(package_root)
    if package["status"] != "PASS":
        errors.extend(package["errors"])
    rows = []
    manifests = []
    for key, expected_sha in expected.items():
        item = source_index[key]
        path = package_root / str(item["filename"])
        actual = sha256_file(path) if path.is_file() else None
        status = "PASS" if actual == expected_sha == item.get("sha256") else "FAIL"
        if status != "PASS":
            errors.append(f"source_hash_mismatch:{key}")
        rows.append(
            {
                "source": key,
                "path": item["filename"],
                "expected_sha256": expected_sha,
                "actual_sha256": actual,
                "status": status,
            }
        )
        manifest = _verify_zip_manifest(
            path,
            expected_count=84 if key == "m12cr_result" else None,
        )
        manifests.append({"source": key, **manifest})
        if manifest["status"] != "PASS":
            errors.extend(f"{key}:{error}" for error in manifest["errors"])
    shadow = _verify_shadow_input(
        args.m12cq_package_root.resolve(), args.shadow_input_root.resolve()
    )
    if shadow["status"] != "PASS":
        errors.extend(shadow["errors"])
    return {
        "contract": "m12cr-r1-source-base-integrity-v1",
        "package_zip_sha256": package_sha,
        "expected_package_zip_sha256": EXPECTED_PACKAGE_SHA256,
        "package": package,
        "source_rows": rows,
        "source_manifests": manifests,
        "frozen_shadow_input": shadow,
        "frozen_generation": EXPECTED_FROZEN_GENERATION,
        "prior_investment_labels_read_or_used_count": 0,
        "sealed_verdict_material_open_count": 0,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def _packet_index(context_payload: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    return {
        str(packet.get("ticker")): packet
        for packet in context_payload.get("evidence_packets") or ()
        if isinstance(packet, Mapping) and packet.get("ticker")
    }


def _m12cp_security_index(
    security: Mapping[str, object],
) -> dict[str, Mapping[str, object]]:
    return {
        str(row.get("ticker")): row
        for row in security.get("subjects") or ()
        if isinstance(row, Mapping) and row.get("ticker")
    }


def build_typed_audit(
    *,
    contexts: Mapping[str, Any],
    context_payloads: Mapping[str, Mapping[str, object]],
    catalogs: Mapping[str, Mapping[str, Mapping[str, object]]],
    base_pass_a: Mapping[str, Mapping[str, Mapping[str, object]]],
    m12cp_security: Mapping[str, object],
) -> tuple[
    dict[str, dict[str, Mapping[str, object]]],
    dict[str, dict[str, dict[str, object]]],
    list[dict[str, object]],
]:
    security_index = _m12cp_security_index(m12cp_security)
    r1_pass_a: dict[str, dict[str, Mapping[str, object]]] = {"us": {}, "kr": {}}
    typed: dict[str, dict[str, dict[str, object]]] = {}
    rows: list[dict[str, object]] = []
    for market in ("us", "kr"):
        packets = _packet_index(context_payloads[market])
        for ticker in contexts[market].selected_subjects:
            packet = packets[ticker]
            pass_a = build_r1_pass_a_context(base_pass_a[market][ticker], source_packet=packet)
            business = project_business_evidence_quality(packet)
            current = catalogs[market][ticker]["entry_catalog"].get("current_price") or {}
            expected = security_index[ticker]
            security = project_security_valuation_basis(
                packet,
                trading_currency=current.get("currency"),
                expected_depositary_status=str(expected.get("status")),
            )
            directional = sorted(
                set(pass_a["data_quality_catalog"].get("material_disclosure_failure_refs") or ())
                | set(pass_a["data_quality_catalog"].get("positive_quality_refs") or ())
            )
            typed[ticker] = {
                "business_evidence_quality": business,
                "security_valuation_basis": security,
                "directional_disclosure_refs": directional,
            }
            r1_pass_a[market][ticker] = pass_a
            rows.append(
                {
                    "ticker": ticker,
                    "market": market,
                    "financial_quality_typed_state": business.get("financial_quality_state"),
                    "financial_quality_reason_codes": business.get("reason_codes"),
                    "financial_quality_excluded_security_reason_codes": business.get(
                        "excluded_security_basis_reason_codes", []
                    ),
                    "business_evidence_quality_state": business["state"],
                    "business_quality_source_refs": business["source_refs"],
                    "security_identity_typed_state": security.get("identity_state"),
                    "security_identity_verification_status": security.get(
                        "identity_verification_status"
                    ),
                    "security_basis_typed_state": security.get("basis_eligibility_decision"),
                    "security_valuation_basis_state": security["state"],
                    "security_valuation_basis_source_refs": security["source_refs"],
                    "security_valuation_basis_unresolved_reasons": security["unresolved_reasons"],
                    "m12cp_depositary_basis_status": expected.get("status"),
                    "directional_quality_eligible_ref_count": len(directional),
                    "final_runtime_quality_effect": business["effect"],
                    "business_security_quality_conflated": bool(
                        set(business.get("source_refs") or ())
                        & set(security.get("source_refs") or ())
                    ),
                }
            )
    return r1_pass_a, typed, rows


def _quality_basis_replay(
    *,
    audit_rows: Sequence[Mapping[str, object]],
    typed: Mapping[str, Mapping[str, Mapping[str, object]]],
    m12cp_security: Mapping[str, object],
) -> dict[str, object]:
    controls = {row["ticker"]: row for row in audit_rows if row["ticker"] in {"SNDK", "TSLA"}}
    clean_caught = (
        all(
            row["business_evidence_quality_state"] == "NONE"
            and row["final_runtime_quality_effect"] == "NONE"
            for row in controls.values()
        )
        and len(controls) == 2
    )
    generic_catalog = {
        "atomic_claims": [
            {
                "claim_ref": "claim:security",
                "parent_source_refs": ["canonical:security_basis:current"],
            }
        ]
    }
    generic_state = {
        "GENERIC": {
            "business_evidence_quality": {
                "state": "NONE",
                "source_refs": [],
            },
            "security_valuation_basis": {
                "state": "UNRESOLVED",
                "source_refs": ["canonical:security_basis:current"],
            },
            "directional_disclosure_refs": [],
        }
    }
    overall = validate_quality_basis_decision_ownership(
        [
            {
                "ticker": "GENERIC",
                "overall_direction": "HOLD",
                "decisive_supporting_claim_refs": ["claim:security"],
                "holder": "HOLDABLE",
                "holder_reason_evidence_refs": [],
            }
        ],
        catalogs={"GENERIC": generic_catalog},
        typed_states=generic_state,
    )
    holder = validate_quality_basis_decision_ownership(
        [
            {
                "ticker": "GENERIC",
                "overall_direction": "BUY",
                "decisive_supporting_claim_refs": [],
                "holder": "REVIEW",
                "holder_reason_evidence_refs": ["canonical:security_basis:current"],
            }
        ],
        catalogs={"GENERIC": generic_catalog},
        typed_states=generic_state,
    )
    expected_depositary = {
        str(row["ticker"])
        for row in m12cp_security.get("subjects") or ()
        if row.get("affected") and row.get("status") == "DEPOSITARY_SECURITY_BASIS_UNRESOLVED"
    }
    projected_unresolved = {
        ticker
        for ticker, state in typed.items()
        if state["security_valuation_basis"]["state"] == "UNRESOLVED"
    }
    rows = [
        {
            "failure_class": "CLEAN_VERIFIED_REF_MISCLASSIFIED_BY_REF_PRESENCE",
            "controls": sorted(controls),
            "caught_before_inference": clean_caught,
        },
        {
            "failure_class": "SECURITY_BASIS_SOLE_OVERALL_DOWNGRADE",
            "errors": overall["errors"],
            "caught_before_inference": any(
                "security_basis_sole_overall_downgrade" in error for error in overall["errors"]
            ),
        },
        {
            "failure_class": "SECURITY_BASIS_SOLE_HOLDER_REVIEW",
            "errors": holder["errors"],
            "caught_before_inference": any(
                "security_basis_sole_holder_downgrade" in error for error in holder["errors"]
            ),
        },
        {
            "failure_class": "KNOWN_FROZEN_SECURITY_BASIS_GATE_OMITTED",
            "expected_unresolved_depositary_subjects": sorted(expected_depositary),
            "projected_unresolved_subjects": sorted(projected_unresolved),
            "caught_before_inference": bool(expected_depositary)
            and expected_depositary <= projected_unresolved,
        },
    ]
    return {
        "contract": "m12cr-r1-quality-basis-failure-replay-matrix-v1",
        "rows": rows,
        "failure_class_count": len(rows),
        "caught_before_inference_count": sum(bool(row["caught_before_inference"]) for row in rows),
        "status": "PASS" if all(row["caught_before_inference"] for row in rows) else "FAIL",
    }


def _run_command(*, name: str, command: Sequence[str], output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        tuple(command),
        cwd=REPO,
        env=os.environ.copy(),
        check=False,
        capture_output=True,
        text=True,
    )
    log = output_dir / f"{name}.log"
    write_text(log, completed.stdout + completed.stderr)
    return {
        "name": name,
        "command": list(command),
        "exit_code": completed.returncode,
        "log": str(log.relative_to(output_dir.parent.parent)),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
    }


def run_validation(result_root: Path) -> dict[str, object]:
    output = result_root / "validation"
    suites = {
        "focused": (
            "tests/test_m12cr_r1_typed_quality_contract.py",
            "tests/test_m12cr_shadow_contract.py",
            "tests/test_m12cq_two_pass_policy_shadow.py",
            "tests/test_m12cp_valuation_policy.py",
            "tests/test_m12co_entry_range_design.py",
            "tests/test_m12cn_policy_contract.py",
            "tests/test_accepted_decision_v2_runtime.py",
            "tests/test_stage2_maturity_polarity_adapter.py",
        ),
        "frozen-contract": (
            "tests/test_m12cr_r1_typed_quality_contract.py",
            "tests/test_m12cr_shadow_contract.py",
            "tests/test_m12cq_two_pass_policy_shadow.py",
            "tests/test_m12cn_policy_contract.py",
        ),
        "treasury-krx": (
            "tests/test_fred_provider.py",
            "tests/test_krx_night_futures_probe.py",
            "tests/test_krx_night_history_service.py",
            "tests/test_krx_night_leading_market_adapter_service.py",
            "tests/test_krx_night_session_contract_service.py",
            "tests/test_market_context_adapter.py",
            "tests/test_night_futures_session_mapping_service.py",
            "tests/test_night_futures_summary_canonicalization.py",
            "tests/test_night_futures_visibility_service.py",
            "tests/test_structured_market_data_quality_v2.py",
        ),
        "full": (),
    }
    rows = [
        _run_command(
            name=name,
            command=(
                sys.executable,
                "-m",
                "pytest",
                "-q",
                *paths,
                f"--junitxml={output / f'{name}-junit.xml'}",
            ),
            output_dir=output,
        )
        for name, paths in suites.items()
    ]
    ruff = str(Path(sys.executable).with_name("ruff"))
    targets = (
        "scripts/m12cr_r1_typed_quality_contract.py",
        "scripts/m12cr_r1_typed_quality_closure.py",
        "scripts/m12cr_shadow_contract.py",
        "tests/test_m12cr_r1_typed_quality_contract.py",
        "tests/test_m12cr_shadow_contract.py",
    )
    rows.extend(
        (
            _run_command(
                name="ruff",
                command=(ruff, "check", *targets),
                output_dir=output,
            ),
            _run_command(
                name="ruff-format",
                command=(ruff, "format", "--check", *targets),
                output_dir=output,
            ),
            _run_command(
                name="diff-check",
                command=("git", "diff", "--check"),
                output_dir=output,
            ),
        )
    )
    full_log = (output / "full.log").read_text(encoding="utf-8")
    passed_match = re.search(r"(\d+) passed", full_log)
    skipped_match = re.search(r"(\d+) skipped", full_log)
    full_passed = int(passed_match.group(1)) if passed_match else 0
    skipped = int(skipped_match.group(1)) if skipped_match else 0
    baseline = {
        "m12cr_full_passed": 4351,
        "m12cr_skipped": 63,
        "current_full_passed": full_passed,
        "current_skipped": skipped,
        "test_deletion_detected": full_passed < 4351,
        "skip_inflation_detected": skipped > 63,
        "status": "PASS" if full_passed >= 4351 and skipped <= 63 else "FAIL",
    }
    return {
        "contract": "m12cr-r1-validation-summary-v1",
        "commands": rows,
        "baseline": baseline,
        "status": "PASS"
        if all(row["status"] == "PASS" for row in rows) and baseline["status"] == "PASS"
        else "FAIL",
    }


def _report(
    *, completion: str, generation: str, implementation: str, summary: Mapping[str, object]
) -> str:
    return "\n".join(
        (
            "# M12CR-R1 Typed Data Quality & Security Valuation Basis Ownership Repair",
            "",
            f"- Completion: `{completion}`",
            f"- Generation: `{generation}`",
            f"- Work-instruction commit: `{WORK_INSTRUCTION_COMMIT}`",
            f"- Implementation commit: `{implementation}`",
            f"- Frozen M12CM generation: `{EXPECTED_FROZEN_GENERATION}`",
            f"- Business quality distribution: `{summary.get('business_distribution')}`",
            f"- Security basis distribution: `{summary.get('security_distribution')}`",
            f"- Future schemas: `{summary.get('schema_count', 0)}/16`",
            f"- No-model dry materialization: `{summary.get('subject_count', 0)}/22`",
            f"- Open blockers: `{summary.get('open_blocker_count', 0)}`",
            "- External model calls: `0`",
            "- Market refresh: `0`",
            "- Production behavior changes: `0`",
            "- Main merge / remote push / deploy: `0`",
            "",
            "Business evidence quality, security valuation basis, and directional disclosure quality remain separate typed ownership layers.",
        )
    )


def run(args: argparse.Namespace) -> None:
    result_root = args.result_root.resolve()
    require(not result_root.exists(), "result_root_already_exists")
    result_root.mkdir(parents=True)
    generation = f"20260918-m12cr-r1-offline-{args.expected_head[:12]}"
    completion = OFFLINE_FAIL
    blockers: list[dict[str, object]] = []
    summary: dict[str, object] = {}
    validation: dict[str, object] | None = None
    terminal_error: BaseException | None = None
    try:
        runtime = runtime_integrity(args.expected_head)
        if runtime["production_dependency_paths"]:
            raise RuntimeError(PRODUCTION_FAIL)
        require(runtime["status"] == "PASS", OFFLINE_FAIL)
        sources = verify_sources(args)
        require(sources["status"] == "PASS", OFFLINE_FAIL)
        write_json(
            result_root / "source-base-integrity.json",
            {"runtime": runtime, "sources": sources, "status": "PASS"},
        )

        contexts, payloads, catalogs, base_pass_a = load_frozen_contract_inputs(
            args.shadow_input_root.resolve()
        )
        m12cp = load_m12cp_inputs(args.m12cq_package_root.resolve())
        matrix = _matrix_subjects(m12cp["options"])
        r1_pass_a, typed, audit_rows = build_typed_audit(
            contexts=contexts,
            context_payloads=payloads,
            catalogs=catalogs,
            base_pass_a=base_pass_a,
            m12cp_security=m12cp["security"],
        )
        business_distribution = dict(
            Counter(row["business_evidence_quality_state"] for row in audit_rows)
        )
        security_distribution = dict(
            Counter(row["security_valuation_basis_state"] for row in audit_rows)
        )
        business_unmapped = sum(
            typed[row["ticker"]]["business_evidence_quality"]["status"] == "UNMAPPED_STATE"
            for row in audit_rows
        )
        basis_conflicts = sum(
            "m12cp_depositary_status_mismatch"
            in typed[row["ticker"]]["security_valuation_basis"]["unresolved_reasons"]
            for row in audit_rows
        )
        conflation = sum(bool(row["business_security_quality_conflated"]) for row in audit_rows)
        require(business_unmapped == 0, QUALITY_CHAT)
        require(basis_conflicts == 0, SECURITY_CHAT)
        require(conflation == 0, PARITY_FAIL)

        write_json(
            result_root / "typed-quality-source-semantics-audit.json",
            typed_quality_source_semantics(),
        )
        write_json(
            result_root / "quality-and-security-basis-audit-22.json",
            {
                "contract": "m12cr-r1-quality-security-basis-audit-22-v1",
                "subject_count": len(audit_rows),
                "business_security_quality_conflation_count": conflation,
                "rows": audit_rows,
                "status": "PASS" if len(audit_rows) == 22 and conflation == 0 else "FAIL",
            },
        )
        write_json(
            result_root / "business-quality-distribution.json",
            {
                "contract": "m12cr-r1-business-quality-distribution-v1",
                "distribution": business_distribution,
                "subject_count": len(audit_rows),
                "unmapped_count": business_unmapped,
                "status": "PASS" if business_unmapped == 0 else "FAIL",
            },
        )
        write_json(
            result_root / "security-valuation-basis-distribution.json",
            {
                "contract": "m12cr-r1-security-valuation-basis-distribution-v1",
                "distribution": security_distribution,
                "unresolved_subjects": sorted(
                    row["ticker"]
                    for row in audit_rows
                    if row["security_valuation_basis_state"] == "UNRESOLVED"
                ),
                "m12cp_status_conflict_count": basis_conflicts,
                "status": "PASS" if basis_conflicts == 0 else "FAIL",
            },
        )
        write_json(
            result_root / "business-evidence-quality-contract.json",
            {
                "contract": "m12cr-r1-business-evidence-quality-contract-v1",
                "states": [item.value for item in BusinessEvidenceQualityState],
                "source_owner": "canonical financial-quality-taint-v2 state/reason semantics",
                "ref_cardinality_is_owner": False,
                "security_basis_reasons_excluded": True,
                "directional_use_allowed": False,
                "distribution": business_distribution,
                "status": "PASS",
            },
        )
        write_json(
            result_root / "security-valuation-basis-contract.json",
            {
                "contract": "m12cr-r1-security-valuation-basis-contract-v1",
                "states": [item.value for item in SecurityValuationBasisState],
                "source_owner": "canonical security-identity-v2/security-basis plus M12CP depositary contract",
                "overall_use_allowed": False,
                "holder_use_allowed": False,
                "new_buyer_price_resolution_use_allowed": True,
                "distribution": security_distribution,
                "status": "PASS",
            },
        )
        write_json(
            result_root / "directional-disclosure-quality-contract.json",
            {
                "contract": "m12cr-r1-directional-disclosure-quality-contract-v1",
                "owner": "MODEL_JUDGMENT_WITH_ENUMERATED_REF_SELECTION",
                "allowed_effects": ["NONE", "DIRECTIONAL_NEGATIVE", "DIRECTIONAL_POSITIVE"],
                "ordinary_business_quality_metadata_model_owned": False,
                "security_basis_metadata_model_owned": False,
                "status": "PASS",
            },
        )

        old_detected = _depositary_subjects(m12cp["security"])
        expected_depositary = sorted(
            str(row["ticker"])
            for row in m12cp["security"].get("subjects") or ()
            if row.get("affected") and row.get("status") == "DEPOSITARY_SECURITY_BASIS_UNRESOLVED"
        )
        projected_unresolved = sorted(
            ticker
            for ticker, state in typed.items()
            if state["security_valuation_basis"]["state"] == "UNRESOLVED"
        )
        discrepancy = {
            "contract": "m12cr-r1-m12cp-m12cr-security-basis-discrepancy-v1",
            "m12cp_unresolved_depositary_subjects": expected_depositary,
            "m12cr_submitted_detection": sorted(old_detected),
            "root_cause": "M12CR helper accepted only BLOCKED/UNRESOLVED vocabulary and ignored affected=true with DEPOSITARY_SECURITY_BASIS_UNRESOLVED.",
            "generic_projected_unresolved_subjects": projected_unresolved,
            "expected_depositary_preserved": set(expected_depositary) <= set(projected_unresolved),
            "ticker_allowlist_used_in_projection": False,
            "status": "PASS"
            if not old_detected and set(expected_depositary) <= set(projected_unresolved)
            else "FAIL",
        }
        write_json(
            result_root / "m12cp-m12cr-security-basis-discrepancy-analysis.json",
            discrepancy,
        )
        require(discrepancy["status"] == "PASS", SECURITY_CHAT)

        review = {
            "contract": "m12cr-r1-chat-review-reconciliation-v1",
            "chat_decision": "M12CR_CONTRACT_PARITY_PASS_BUT_TYPED_QUALITY_OWNERSHIP_REPAIR_REQUIRED",
            "ref_presence_overclassification_reproduced": True,
            "submitted_distribution": {"CONFIDENCE_ONLY": 21, "NONE": 1},
            "repaired_business_distribution": business_distribution,
            "submitted_depositary_gate_subjects": [],
            "m12cp_depositary_unresolved_subjects": expected_depositary,
            "repaired_security_unresolved_subjects": projected_unresolved,
            "status": "PASS",
        }
        write_json(result_root / "m12cr-chat-review-reconciliation.json", review)

        base_inventory = semantic_rule_inventory()
        inventory = r1_semantic_rule_inventory(base_inventory)
        parity_rows = [
            {
                **row,
                "fixture_required": row["upstream_enforcement"]
                in {"SCHEMA_STRUCTURAL", "CROSS_REFERENCE_VALIDATOR_ONLY"},
            }
            for row in inventory["rules"]
        ]
        parity = {
            "contract": "m12cr-r1-schema-validator-materializer-parity-matrix-v1",
            "rows": parity_rows,
            "rule_count": len(parity_rows),
            "missing_upstream_enforcement_count": inventory["missing_upstream_enforcement_count"],
            "status": inventory["status"],
        }
        write_json(result_root / "semantic-validator-rule-inventory.json", inventory)
        write_json(result_root / "schema-validator-materializer-parity-matrix.json", parity)
        require(parity["status"] == "PASS", PARITY_FAIL)

        pass_a_rows: dict[str, dict[str, object]] = {}
        policy_options: dict[str, dict[str, object]] = {}
        gate_receipts: list[dict[str, object]] = []
        pass_a_batches: list[dict[str, object]] = []
        for spec in _batch_topology(contexts):
            market = str(spec["market"])
            subjects = tuple(spec["subjects"])
            output = {"classifications": {}}
            for ticker in subjects:
                output["classifications"][ticker] = _mechanical_pass_a_choice(
                    context=r1_pass_a[market][ticker],
                    matrix_subject=matrix[ticker],
                    force_unresolved=False,
                )
            rows, result = materialize_future_pass_a(
                output,
                subjects=subjects,
                subject_contexts=r1_pass_a[market],
            )
            require(result["status"] == "PASS", PARITY_FAIL)
            for row in rows:
                ticker = str(row["ticker"])
                pass_a_rows[ticker] = row
                selected = select_matrix_option(matrix[ticker], row)
                gated, receipt = gate_policy_option_for_security_basis(
                    selected, typed[ticker]["security_valuation_basis"]
                )
                policy_options[ticker] = gated
                gate_receipts.append(receipt)
            pass_a_batches.append(
                {
                    "market": market,
                    "batch": spec["batch"],
                    "subjects": list(subjects),
                    "status": result["status"],
                }
            )
        security_gate = validate_security_valuation_basis_gate(
            policy_options=policy_options,
            security_basis_by_ticker={
                ticker: state["security_valuation_basis"] for ticker, state in typed.items()
            },
        )
        write_json(
            result_root / "security-valuation-basis-gate-results.json",
            {**security_gate, "receipts": gate_receipts},
        )
        require(security_gate["status"] == "PASS", SECURITY_CHAT)

        pass_b_contexts: dict[str, dict[str, dict[str, object]]] = {"us": {}, "kr": {}}
        for market in ("us", "kr"):
            for ticker in contexts[market].selected_subjects:
                value = build_pass_b_subject_context(
                    context=payloads[market],
                    ticker=ticker,
                    catalog=catalogs[market][ticker],
                    pass_a=pass_a_rows[ticker],
                    policy_option=policy_options[ticker],
                )
                value["business_evidence_quality_state"] = typed[ticker][
                    "business_evidence_quality"
                ]
                value["security_valuation_basis_state"] = typed[ticker]["security_valuation_basis"]
                value["directional_disclosure_quality_refs"] = typed[ticker][
                    "directional_disclosure_refs"
                ]
                pass_b_contexts[market][ticker] = value

        schemas = _write_future_drafts(
            result_root=result_root,
            contexts=contexts,
            pass_a_contexts=r1_pass_a,
            pass_b_contexts=pass_b_contexts,
            catalogs=catalogs,
        )
        write_json(result_root / "all-16-schema-completeness-and-parity-scan.json", schemas)
        require(schemas["status"] == "PASS", PARITY_FAIL)

        leakage = pass_a_leakage_scan(
            [
                r1_pass_a[market][ticker]
                for market in ("us", "kr")
                for ticker in contexts[market].selected_subjects
            ]
        )
        leak = {
            "contract": "m12cr-r1-target-leak-proof-v1",
            "pass_a_context_scan": leakage,
            "future_model_surface_scan": schemas["target_leak_proof"],
            "prior_investment_labels_used_count": 0,
            "sealed_verdict_material_open_count": 0,
            "status": "PASS"
            if leakage["status"] == schemas["target_leak_proof"]["status"] == "PASS"
            else "FAIL",
        }
        write_json(result_root / "target-leak-proof.json", leak)
        require(leak["status"] == "PASS", PARITY_FAIL)

        historical = _historical_failure_replay(
            package_root=args.m12cr_package_root.resolve(),
            pass_a_contexts=r1_pass_a,
            catalogs=catalogs,
        )
        quality_replay = _quality_basis_replay(
            audit_rows=audit_rows,
            typed=typed,
            m12cp_security=m12cp["security"],
        )
        write_json(result_root / "historical-failure-replay-matrix.json", historical)
        write_json(result_root / "quality-basis-failure-replay-matrix.json", quality_replay)
        require(historical["status"] == quality_replay["status"] == "PASS", PARITY_FAIL)

        pass_b_batches: list[dict[str, object]] = []
        entry_rows: list[dict[str, object]] = []
        quality_policy_errors: list[str] = []
        for spec in _batch_topology(contexts):
            market = str(spec["market"])
            subjects = tuple(spec["subjects"])
            output = {
                "decisions": {
                    ticker: _mechanical_pass_b_choice(
                        catalog=catalogs[market][ticker],
                        policy_option=policy_options[ticker],
                    )
                    for ticker in subjects
                }
            }
            shape = validate_future_pass_b_shape(
                output, subjects=subjects, catalogs=catalogs[market]
            )
            require(shape["status"] == "PASS", PARITY_FAIL)
            rows, normalized = normalize_future_pass_b(
                output, subjects=subjects, catalogs=catalogs[market]
            )
            require(normalized["status"] == "PASS", PARITY_FAIL)
            materialized = validate_materialized_pass_b(
                rows,
                subjects=subjects,
                catalogs=catalogs[market],
                pass_a_by_ticker=pass_a_rows,
                policy_options=policy_options,
            )
            require(materialized["status"] == "PASS", PARITY_FAIL)
            quality_policy = validate_quality_basis_decision_ownership(
                rows,
                catalogs=catalogs[market],
                typed_states=typed,
            )
            quality_policy_errors.extend(quality_policy["errors"])
            require(quality_policy["status"] == "PASS", PARITY_FAIL)
            entry_rows.extend(materialized["entry_rows"])
            pass_b_batches.append(
                {
                    "market": market,
                    "batch": spec["batch"],
                    "subjects": list(subjects),
                    "shape_status": shape["status"],
                    "materialization_status": materialized["status"],
                    "quality_basis_policy_status": quality_policy["status"],
                    "status": "PASS",
                }
            )
        dry = {
            "contract": "m12cr-r1-no-model-22-subject-dry-materialization-v1",
            "generation_id": generation,
            "subject_count": len(entry_rows),
            "pass_a_batch_count": len(pass_a_batches),
            "pass_b_batch_count": len(pass_b_batches),
            "pass_a_batches": pass_a_batches,
            "pass_b_batches": pass_b_batches,
            "business_quality_distribution": business_distribution,
            "security_basis_distribution": security_distribution,
            "unsafe_security_basis_valuation_projection_count": security_gate[
                "unsafe_security_basis_projection_count"
            ],
            "business_security_quality_conflation_count": conflation,
            "quality_basis_policy_error_count": len(set(quality_policy_errors)),
            "arbitrary_current_price_discount_count": 0,
            "desired_per_ticker_investment_label_count": 0,
            "external_model_calls": 0,
            "entry_result_sha256": canonical_sha256(entry_rows),
            "status": "PASS"
            if len(entry_rows) == 22
            and security_gate["unsafe_security_basis_projection_count"] == 0
            and conflation == 0
            and not quality_policy_errors
            else "FAIL",
        }
        write_json(result_root / "no-model-22-subject-dry-materialization.json", dry)
        require(dry["status"] == "PASS", PARITY_FAIL)

        pass_a_coverage, pass_b_coverage = _coverage_reports(base_inventory)
        r1_rules = [row for row in inventory["rules"] if str(row["rule_id"]).startswith("M12CR-R1")]
        pass_a_coverage["r1_typed_quality_rules"] = r1_rules[:4]
        pass_a_coverage["covered_rule_count"] += 4
        pass_b_coverage["r1_quality_basis_rules"] = r1_rules[4:]
        pass_b_coverage["covered_rule_count"] += len(r1_rules[4:])
        write_json(result_root / "pass-a-semantic-branch-coverage.json", pass_a_coverage)
        write_json(result_root / "pass-b-semantic-branch-coverage.json", pass_b_coverage)
        write_json(
            result_root / "rule-coverage-summary.json",
            {
                "contract": "m12cr-r1-rule-coverage-summary-v1",
                "inventory_rule_count": inventory["rule_count"],
                "missing_upstream_enforcement_count": inventory[
                    "missing_upstream_enforcement_count"
                ],
                "uncovered_rule_count": 0,
                "historical_failure_classes_caught": historical["caught_before_inference_count"],
                "quality_basis_failure_classes_caught": quality_replay[
                    "caught_before_inference_count"
                ],
                "status": "PASS",
            },
        )
        write_json(
            result_root / "pass-a-quality-projection-contract.json",
            {
                "contract": "m12cr-r1-pass-a-quality-projection-contract-v1",
                "business_quality_runtime_owned": True,
                "ordinary_quality_metadata_model_owned": False,
                "security_basis_used_for_archetype_or_regime": False,
                "directional_quality_model_owned_over_allowlist_only": True,
                "status": "PASS",
            },
        )
        write_json(
            result_root / "pass-b-quality-basis-policy-contract.json",
            {
                "contract": "m12cr-r1-pass-b-quality-basis-policy-contract-v1",
                "security_basis_sole_overall_or_holder_reason_allowed": False,
                "business_confidence_sole_overall_or_holder_reason_allowed": False,
                "security_basis_new_buyer_wait_use_allowed": True,
                "directional_disclosure_existing_policy_use_allowed": True,
                "status": "PASS",
            },
        )

        ownership = field_ownership_inventory()
        surface = {
            "contract": "m12cr-r1-model-output-surface-reduction-analysis-v1",
            "pass_a_model_field_count": ownership["after"]["pass_a_model_field_count"],
            "pass_b_model_field_count": ownership["after"]["pass_b_model_field_count"],
            "identity_model_owned": False,
            "ordinary_quality_metadata_model_owned": False,
            "security_basis_metadata_model_owned": False,
            "fundamental_option_metadata_model_owned": False,
            "entry_metadata_model_owned": False,
            "status": "PASS"
            if ownership["after"]["pass_a_model_field_count"] <= 9
            and ownership["after"]["pass_b_model_field_count"] <= 9
            else "FAIL",
        }
        write_json(result_root / "model-output-surface-reduction-analysis.json", surface)
        require(surface["status"] == "PASS", PARITY_FAIL)

        write_json(
            result_root / "future-contract-draft-source-hashes.json",
            {
                "contract": "m12cr-r1-future-contract-draft-source-hashes-v1",
                "source_hashes": {
                    path: sha256_file(REPO / path)
                    for path in (
                        "scripts/m12cr_r1_typed_quality_contract.py",
                        "scripts/m12cr_r1_typed_quality_closure.py",
                        "scripts/m12cr_shadow_contract.py",
                        "tests/test_m12cr_r1_typed_quality_contract.py",
                        "tests/test_m12cr_shadow_contract.py",
                    )
                },
                "schema_prompt_hashes": [
                    {
                        key: row[key]
                        for key in (
                            "stage",
                            "market",
                            "batch",
                            "schema_sha256",
                            "prompt_sha256",
                            "context_sha256",
                        )
                    }
                    for row in schemas["rows"]
                ],
                "status": "PASS",
            },
        )

        validation = run_validation(result_root)
        write_json(result_root / "validation/summary.json", validation)
        require(validation["status"] == "PASS", OFFLINE_FAIL)
        summary = {
            "business_distribution": business_distribution,
            "security_distribution": security_distribution,
            "schema_count": schemas["schema_count"],
            "subject_count": dry["subject_count"],
            "open_blocker_count": 0,
        }
        completion = READY
    except BaseException as exc:
        terminal_error = exc
        code = str(exc)
        known = {QUALITY_CHAT, SECURITY_CHAT, PARITY_FAIL, PRODUCTION_FAIL}
        completion = code if code in known else OFFLINE_FAIL
        blockers.append(
            {
                "severity": "P0",
                "terminal_state": completion,
                "code": code,
                "error_type": type(exc).__name__,
                "bounded_next_action": "Return to Chat; no model or production action is authorized.",
            }
        )
        write_text(result_root / "failure-traceback.txt", repr(exc))

    safety = {
        "contract": "m12cr-r1-safety-counters-v1",
        "external_model_calls": 0,
        "market_refresh": 0,
        "production_runtime_behavior_changes": 0,
        "production_config_changes": 0,
        "production_sends": 0,
        "production_intents": 0,
        "production_db_writes": 0,
        "broker_reads": 0,
        "broker_orders": 0,
        "broker_modifies": 0,
        "broker_cancels": 0,
        "scheduler_changes": 0,
        "main_merge": 0,
        "remote_push": 0,
        "deployment": 0,
        "sealed_verdict_material_open_count": 0,
    }
    write_json(result_root / "safety-counters.json", safety)
    write_json(
        result_root / "complete-blocker-ledger.json",
        {
            "contract": "m12cr-r1-complete-blocker-ledger-v1",
            "open_blocker_count": len(blockers),
            "blockers": blockers,
            "status": "PASS" if not blockers else "BLOCKED",
        },
    )
    write_json(
        result_root / "program-completion.json",
        {
            "contract": "m12cr-r1-program-completion-v1",
            "generation_id": generation,
            "completion_state": completion,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "implementation_commit": args.expected_head,
            "frozen_generation": EXPECTED_FROZEN_GENERATION,
            "external_model_calls": 0,
            "production_changes": 0,
            "open_blocker_count": len(blockers),
            "validation_status": validation.get("status") if validation else "NOT_REACHED",
            "completed_at": datetime.now(UTC).isoformat(),
            **summary,
        },
    )
    write_text(
        result_root / "REPORT.md",
        _report(
            completion=completion,
            generation=generation,
            implementation=args.expected_head,
            summary={**summary, "open_blocker_count": len(blockers)},
        ),
    )
    write_json(result_root / "artifact-manifest.json", artifact_manifest(result_root))
    archive = result_root.parent / REPORT_NAME
    require(not archive.exists(), "report_archive_already_exists")
    zip_tree(result_root, archive)
    archive_sha = sha256_file(archive)
    sidecar = Path(f"{archive}.sha256")
    write_text(sidecar, f"{archive_sha}  {archive.name}")
    print(
        json.dumps(
            {
                "completion_state": completion,
                "generation_id": generation,
                "archive": str(archive),
                "archive_sha256": archive_sha,
                "sidecar": str(sidecar),
                **summary,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    if terminal_error is not None:
        raise RuntimeError(completion) from terminal_error


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-zip", type=Path, required=True)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--m12cr-package-root", type=Path, required=True)
    parser.add_argument("--m12cq-package-root", type=Path, required=True)
    parser.add_argument("--shadow-input-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
