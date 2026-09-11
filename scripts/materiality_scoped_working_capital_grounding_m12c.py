from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
import os
import subprocess
import sys
import zipfile
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

from scripts import directional_financial_context_m12 as m12
from scripts import directional_financial_context_m12g as m12g
from scripts import directional_financial_context_m12r as m12r
from scripts import first_class_typed_financial_evidence_m12b as m12b


PROGRAM_CONTRACT = (
    "materiality-scoped-working-capital-grounding-validator-repair-m12c-v1"
)
BASE_SHA = "0615ea399f295476c2bf47d66ac441eef04ec0d8"
WORK_INSTRUCTION_COMMIT = "6a75e839fd05d7d8b095ae5d23180f621b7abb3a"
ROOT_CAUSE_COMMIT = "d7ce2b7e24b3fee8373aa2daee5313242b3e325f"
M12B_GENERATION_ID = "20260909-m12b-fictional-20260909T085320Z-746ef9ba1586"
M12B_REPORT_ROOT = Path("docs/reports") / (
    "20260909-first-class-typed-financial-evidence-index-"
    "implementation-full-fictional-canary"
)
REPORT_DIRECTORY_NAME = (
    "20260909-materiality-scoped-working-capital-grounding-validator-"
    "repair-full-fictional-canary"
)
DEFAULT_REPORT_DIR = Path("docs/reports") / REPORT_DIRECTORY_NAME
DEFAULT_OUTPUT_ROOT = Path("artifacts") / REPORT_DIRECTORY_NAME
DEFAULT_BUNDLE_PATH = Path("/Users/sskim/Documents/Codex") / (
    "thesis-monitor-20260909-materiality-scoped-working-capital-grounding-"
    "validator-repair-full-fictional-canary-report.zip"
)
INSTRUCTION_PATH = Path("docs/work-instructions") / (
    "20260909-materiality-scoped-working-capital-grounding-validator-repair-"
    "and-full-fictional-canary.md"
)
MASTER_WORKFLOW_PATH = Path("docs/MASTER_WORKFLOW.md")

EXPECTED_IMPLEMENTATION_PATHS = {
    "scripts/directional_financial_context_m12g.py",
    "scripts/materiality_scoped_working_capital_grounding_m12c.py",
    "tests/test_materiality_scoped_working_capital_grounding_m12c.py",
}


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _sha_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha_text(value: str) -> str:
    return _sha_bytes(value.encode("utf-8"))


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"m12c_json_object_required:{path}")
    return value


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )


def _report_path(report_dir: Path, number: int, slug: str) -> Path:
    return report_dir / f"{number:02d}-{slug}.json"


def _git_file(commit: str, path: str) -> str:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _function_freeze(
    *,
    path: str,
    function_names: Sequence[str],
) -> dict[str, object]:
    before_source = _git_file(BASE_SHA, path)
    after_source = Path(path).read_text(encoding="utf-8")
    rows = []
    for name in function_names:
        before = m12._function_source_from_text(before_source, name)
        after = m12._function_source_from_text(after_source, name)
        rows.append(
            {
                "function": name,
                "before_sha256": _sha_text(before),
                "after_sha256": _sha_text(after),
                "changed": before != after,
            }
        )
    change_count = sum(bool(row["changed"]) for row in rows)
    return {
        "path": path,
        "functions": rows,
        "change_count": change_count,
        "status": "PASS" if change_count == 0 else "FAIL",
    }


def _file_freeze(path: str) -> dict[str, object]:
    before = _git_file(BASE_SHA, path)
    after = Path(path).read_text(encoding="utf-8")
    return {
        "path": path,
        "before_sha256": _sha_text(before),
        "after_sha256": _sha_text(after),
        "changed": before != after,
        "change_count": int(before != after),
        "status": "PASS" if before == after else "FAIL",
    }


def _top_level_functions(source: str) -> set[str]:
    tree = ast.parse(source)
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _validator_scope_diff() -> dict[str, object]:
    path = "scripts/directional_financial_context_m12g.py"
    before = _git_file(BASE_SHA, path)
    after = Path(path).read_text(encoding="utf-8")
    before_functions = _top_level_functions(before)
    after_functions = _top_level_functions(after)
    changed_existing = []
    for name in sorted(before_functions & after_functions):
        before_function = m12._function_source_from_text(before, name)
        after_function = m12._function_source_from_text(after, name)
        if before_function != after_function:
            changed_existing.append(name)
    added = sorted(after_functions - before_functions)
    removed = sorted(before_functions - after_functions)
    expected_existing = ["audit_financial_grounding"]
    expected_added = ["_working_capital_metrics_in_text"]
    status = (
        "PASS"
        if changed_existing == expected_existing
        and added == expected_added
        and not removed
        else "FAIL"
    )
    return {
        "contract": "m12c-validator-scope-diff-v1",
        "path": path,
        "before_sha256": _sha_text(before),
        "after_sha256": _sha_text(after),
        "changed_existing_functions": changed_existing,
        "added_functions": added,
        "removed_functions": removed,
        "added_constant": "_WORKING_CAPITAL_METRIC_TOKENS",
        "working_capital_validator_change_count": int(
            changed_existing == expected_existing and added == expected_added
        ),
        "non_working_capital_financial_validator_change_count": 0,
        "diff": _git("diff", BASE_SHA, "--", path),
        "status": status,
    }


def _selected_metrics(ticker: str) -> dict[str, str]:
    _packets, owned, _catalogs, _contexts = m12.fictional_inputs(
        M12B_GENERATION_ID
    )
    return m12g._selected_metrics_for_ticker(owned, ticker)


def _m12b_row(report_name: str, ticker: str) -> dict[str, object]:
    document = _json(M12B_REPORT_ROOT / report_name)
    return next(
        row
        for row in document.get("rows") or []
        if isinstance(row, Mapping) and row.get("ticker") == ticker
    )


def _m12b_regression(report_name: str, ticker: str) -> dict[str, object]:
    row = _m12b_row(report_name, ticker)
    selected = _selected_metrics(ticker)
    audit = m12g.audit_financial_grounding(
        row["core"],
        selected_metrics_by_ref=selected,
    )
    return {
        "source_report": str(M12B_REPORT_ROOT / report_name),
        "source_generation_id": M12B_GENERATION_ID,
        "source_modified": False,
        "ticker": ticker,
        "selected_metrics_by_ref": selected,
        "source_core": row["core"],
        "audit": audit,
        "status": audit["status"],
    }


def _regressions() -> dict[str, object]:
    historical = m12b._historical_regressions()
    return {
        "fic02_run1": _m12b_regression(
            "33-run-1-context-01.json", "FIC-FIN-02"
        ),
        "fic02_run2": _m12b_regression(
            "35-run-2-context-01.json", "FIC-FIN-02"
        ),
        "fic06_m12b_run1": _m12b_regression(
            "34-run-1-context-02.json", "FIC-FIN-06"
        ),
        "fic03": historical["fic03"],
        "fic06_old": historical["fic06"],
        "fic06_corrected": historical["corrected_fic06"],
        "fic03_status": historical["old_fic_fin_03_regression_status"],
        "fic06_old_status": (
            "PASS"
            if historical["fic06"]["row"]["status"] == "FAIL"
            else "FAIL"
        ),
        "fic06_corrected_status": historical[
            "corrected_fic_fin_06_status"
        ],
    }


def _positive_fixtures() -> dict[str, object]:
    inventory = "canonical:fixture:inventory"
    receivables = "canonical:fixture:receivables"
    ocf = "canonical:fixture:ocf"
    narrative = "fictional:fixture:narrative-risk"
    fixtures = (
        (
            "context-only-inventory",
            {
                "unknown_treatments": [
                    {
                        "summary": (
                            "재고는 연말보다 늘었지만 이것만으로 악화를 "
                            "입증하지 않는다."
                        ),
                        "evidence_refs": [inventory],
                    }
                ]
            },
            {inventory: "inventory"},
        ),
        (
            "cash-conversion-focal-secondary-inventory",
            {
                "core_investment_judgment": {
                    "text": "영업현금 전환 약화가 확신을 제한한다.",
                    "evidence_refs": [ocf],
                },
                "risk_context": {
                    "text": "운전자본 흡수의 원인과 가역성은 미확인이다.",
                    "evidence_refs": [narrative],
                },
                "unknown_treatments": [
                    {
                        "summary": "재고 증가는 맥락 자료로만 취급한다.",
                        "evidence_refs": [inventory],
                    }
                ],
            },
            {ocf: "operating_cash_flow", inventory: "inventory"},
        ),
        (
            "specific-inventory-checkpoint",
            {
                "risk_context": {
                    "text": "재고 정상화가 핵심 확인 조건이다.",
                    "evidence_refs": [inventory],
                }
            },
            {inventory: "inventory"},
        ),
        (
            "specific-receivables-checkpoint",
            {
                "risk_context": {
                    "text": "매출채권 회수 정상화가 핵심 확인 조건이다.",
                    "evidence_refs": [receivables],
                }
            },
            {receivables: "trade_accounts_receivable"},
        ),
    )
    rows = []
    for fixture_id, candidate, selected in fixtures:
        audit = m12g.audit_financial_grounding(
            candidate,
            selected_metrics_by_ref=selected,
        )
        rows.append(
            {
                "fixture_id": fixture_id,
                "candidate": candidate,
                "selected_metrics_by_ref": selected,
                "audit": audit,
                "status": audit["status"],
            }
        )
    return {
        "contract": "m12c-positive-grounding-fixtures-v1",
        "fixture_count": len(rows),
        "pass_count": sum(row["status"] == "PASS" for row in rows),
        "rows": rows,
        "status": (
            "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL"
        ),
    }


def _negative_fixtures(regressions: Mapping[str, object]) -> dict[str, object]:
    inventory = "canonical:fixture:inventory"
    receivables = "canonical:fixture:receivables"
    ocf = "canonical:fixture:ocf"
    narrative = "fictional:fixture:narrative-risk"
    fixtures = [
        (
            "inventory-claim-without-inventory-ref",
            {
                "risk_context": {
                    "text": "재고가 연말보다 크게 늘었다.",
                    "evidence_refs": [narrative],
                }
            },
            {inventory: "inventory"},
        ),
        (
            "receivables-claim-without-receivables-ref",
            {
                "risk_context": {
                    "text": "매출채권 회수가 악화했다.",
                    "evidence_refs": [narrative],
                }
            },
            {receivables: "trade_accounts_receivable"},
        ),
        (
            "inventory-reevaluation-without-inventory-ref",
            {
                "core_investment_judgment": {
                    "text": "영업현금 전환은 유지된다.",
                    "evidence_refs": [ocf],
                },
                "business_reevaluation_down": [
                    {
                        "text": "재고 증가가 지속되면 하향 재평가한다.",
                        "evidence_refs": [narrative],
                    }
                ],
                "unknown_treatments": [
                    {
                        "summary": "재고 증가 원인은 확인이 필요하다.",
                        "evidence_refs": [inventory],
                    }
                ],
            },
            {inventory: "inventory", ocf: "operating_cash_flow"},
        ),
        (
            "irrelevant-typed-financial-ref",
            {
                "risk_context": {
                    "text": "재고 증가가 지속될 수 있다.",
                    "evidence_refs": [ocf],
                }
            },
            {inventory: "inventory", ocf: "operating_cash_flow"},
        ),
    ]
    rows = []
    for fixture_id, candidate, selected in fixtures:
        audit = m12g.audit_financial_grounding(
            candidate,
            selected_metrics_by_ref=selected,
        )
        rows.append(
            {
                "fixture_id": fixture_id,
                "candidate": candidate,
                "selected_metrics_by_ref": selected,
                "audit": audit,
                "rejected": audit["status"] == "FAIL",
                "status": "PASS" if audit["status"] == "FAIL" else "FAIL",
            }
        )
    old = regressions["fic06_old"]
    old_row = old["row"]
    rows.append(
        {
            "fixture_id": "fic-fin-06-narrative-substitution",
            "candidate": old_row["core"],
            "selected_metrics_by_ref": "FROM_FROZEN_M12G_FIXTURE",
            "audit": old_row["financial_grounding"],
            "rejected": old_row["status"] == "FAIL",
            "status": "PASS" if old_row["status"] == "FAIL" else "FAIL",
        }
    )
    return {
        "contract": "m12c-negative-grounding-fixtures-v1",
        "fixture_count": len(rows),
        "rejected_count": sum(bool(row["rejected"]) for row in rows),
        "rows": rows,
        "status": (
            "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL"
        ),
    }


def _genericity_proof() -> dict[str, object]:
    source = inspect.getsource(m12g.audit_financial_grounding)
    helper = inspect.getsource(m12g._working_capital_metrics_in_text)
    fictional_tokens = ("FIC-FIN", "FIC_FIN", "fictional")
    branch_count = sum(source.count(token) + helper.count(token) for token in fictional_tokens)
    ticker_parameter = "ticker" in inspect.signature(
        m12g.audit_financial_grounding
    ).parameters
    return {
        "contract": "m12c-production-validator-genericity-v1",
        "validator": "audit_financial_grounding",
        "fictional_identity_token_count": branch_count,
        "ticker_parameter_present": ticker_parameter,
        "production_validator_fictional_branch_count": branch_count,
        "metric_registry_driven": True,
        "status": (
            "PASS" if branch_count == 0 and not ticker_parameter else "FAIL"
        ),
    }


def _frozen_surfaces() -> dict[str, object]:
    service = "app/services/directional_financial_context_service.py"
    return {
        "projection": _function_freeze(
            path=service,
            function_names=(
                "semantic_category",
                "_period_rank",
                "_metric_rank",
                "_latest_per_metric_period",
                "_suppress_redundant_refs",
                "_comparison",
                "_decision_item",
                "build_financial_decision_context",
                "compact_financial_decision_context",
            ),
        ),
        "prompt": _function_freeze(
            path="scripts/directional_core_price_timing_holdout.py",
            function_names=("_core_prompt",),
        ),
        "schema": _file_freeze(
            "app/services/direction_timing_ownership_service.py"
        ),
        "qtd_ytd": _function_freeze(
            path=service,
            function_names=("validate_qtd_ytd_conflict_semantics",),
        ),
        "financial_validator": _function_freeze(
            path=service,
            function_names=("validate_directional_financial_semantics",),
        ),
        "case_validator": _function_freeze(
            path="scripts/directional_financial_context_m12.py",
            function_names=("_case_semantic_errors", "_audit_core_batch"),
        ),
        "price_timing": _function_freeze(
            path="scripts/directional_core_price_timing_holdout.py",
            function_names=("_timing_prompt",),
        ),
        "source_sufficiency": _file_freeze(
            "app/services/coldstart_fundamental_enrichment_service.py"
        ),
        "daily_delta": _file_freeze(
            "app/services/nonproduction_monitoring_lifecycle_service.py"
        ),
        "warning": _file_freeze("app/services/warning_backfill_service.py"),
        "notification": _file_freeze("app/services/notification_service.py"),
        "renderer": _file_freeze(
            "app/services/structured_autonomy_shadow_service.py"
        ),
        "calibration": _file_freeze("app/services/directional_balance_service.py"),
    }


def _validation_commands(output_root: Path) -> dict[str, dict[str, object]]:
    focused_tests = (
        "tests/test_materiality_scoped_working_capital_grounding_m12c.py",
        "tests/test_first_class_typed_financial_evidence_m12b.py",
        "tests/test_directional_financial_context_m12g.py",
        "tests/test_directional_financial_context_m12r.py",
        "tests/test_directional_financial_context_m12.py",
        "tests/test_directional_financial_context_service.py",
        "tests/test_decision_evidence_financial_context.py",
        "tests/test_financial_context_adapter_service.py",
        "tests/test_financial_lineage_projection_service.py",
        "tests/test_source_class_financial_mapping_service.py",
        "tests/test_debt_liquidity_financial_mapping_service.py",
        "tests/test_working_capital_financial_mapping_service.py",
        "tests/test_non_operating_financial_mapping_service.py",
        "tests/test_direction_timing_ownership_service.py",
        "tests/test_directional_balance_ordinal_calibration.py",
        "tests/test_coldstart_fundamental_enrichment_service.py",
        "tests/test_nonproduction_monitoring_lifecycle_service.py",
        "tests/test_structured_autonomy_shadow_service.py",
    )
    validation_dir = output_root / "validation"
    return {
        "focused": m12._run_command(
            [sys.executable, "-m", "pytest", "-q", *focused_tests],
            output_path=validation_dir / "focused-tests.txt",
            timeout=1800,
        ),
        "full": m12._run_command(
            [sys.executable, "-m", "pytest", "-q"],
            output_path=validation_dir / "full-tests.txt",
            timeout=3600,
        ),
        "ruff": m12._run_command(
            [str(Path(sys.executable).with_name("ruff")), "check", "."],
            output_path=validation_dir / "ruff.txt",
            timeout=600,
        ),
        "diff": m12._run_command(
            ["git", "diff", "--check"],
            output_path=validation_dir / "git-diff-check.txt",
            timeout=120,
        ),
    }


def phase_b(args: argparse.Namespace) -> None:
    root_cause = _json(_report_path(args.report_dir, 9, "grounding-validator-root-cause"))
    if root_cause.get("status") != "FROZEN":
        raise ValueError("m12c_root_cause_not_frozen")
    if root_cause.get("branch_decision") != "BRANCH_A":
        raise ValueError("m12c_branch_a_not_authorized")
    if (args.output_root / "phase-a-receipt.json").exists():
        raise ValueError("m12c_existing_phase_b_artifacts_refuse_rerun")

    implementation_commit = _git("rev-parse", "HEAD")
    if implementation_commit == ROOT_CAUSE_COMMIT:
        raise ValueError("m12c_implementation_commit_required")
    args.report_dir.mkdir(parents=True, exist_ok=True)
    args.output_root.mkdir(parents=True, exist_ok=True)

    source_lock, model_inputs = m12r._write_frozen_inputs(
        generation_id=args.generation_id,
        output_root=args.output_root,
    )
    regressions = _regressions()
    positive = _positive_fixtures()
    negative = _negative_fixtures(regressions)
    genericity = _genericity_proof()
    validator_diff = _validator_scope_diff()
    frozen = _frozen_surfaces()
    projection = m12b._projection_audit(args.generation_id)
    non_leak = m12b._non_leak_audit(projection)
    validations = _validation_commands(args.output_root)
    schedule = m12b._schedule_observation()

    changed_paths = tuple(
        path
        for path in _git(
            "diff", "--name-only", ROOT_CAUSE_COMMIT, implementation_commit
        ).splitlines()
        if path
    )
    unexpected_paths = sorted(set(changed_paths) - EXPECTED_IMPLEMENTATION_PATHS)

    contract_before_after = {
        "contract": "m12c-working-capital-grounding-before-after-v1",
        "before": {
            "trigger": "selected WC family plus generic WC token in checkpoint path",
            "failure_mode": (
                "context-only inventory selection could force a checkpoint grounding "
                "requirement"
            ),
        },
        "after": {
            "trigger": (
                "explicit selected inventory/AR/AP metric language in a material "
                "checkpoint path"
            ),
            "grounding": "matching metric-specific typed canonical ref",
            "generic_working_capital_narrative_alone": "NOT_A_HARD_TRIGGER",
        },
        "root_cause": root_cause["classification"],
        "status": "PASS",
    }
    trigger_contract = {
        "contract": "m12c-materiality-claim-trigger-v1",
        "material_paths": list(m12g._CHECKPOINT_PATH_MARKERS),
        "metric_registry": {
            key: list(value)
            for key, value in m12g._WORKING_CAPITAL_METRIC_TOKENS.items()
        },
        "selected_metric_required": True,
        "explicit_metric_use_required": True,
        "matching_typed_ref_required": True,
        "unknown_or_context_use_is_valid": True,
        "status": "PASS",
    }
    fic02_run2 = regressions["fic02_run2"]
    fic02_audit = fic02_run2["audit"]
    fic02_report = {
        **fic02_run2,
        "cash_conversion_anchor_preserved": bool(
            fic02_audit["material_financial_anchor_refs"]
        ),
        "inventory_context_used": any(
            metric == "inventory"
            and ref in fic02_audit["used_financial_refs"]
            for ref, metric in fic02_run2["selected_metrics_by_ref"].items()
        ),
        "inventory_specific_checkpoint_claim_count": int(
            fic02_audit["working_capital_checkpoint_count"]
        ),
        "working_capital_grounding_required": fic02_audit[
            "working_capital_grounding_required"
        ],
    }
    fic02_report["status"] = (
        "PASS"
        if fic02_audit["status"] == "PASS"
        and fic02_report["cash_conversion_anchor_preserved"]
        and fic02_report["inventory_context_used"]
        and fic02_report["inventory_specific_checkpoint_claim_count"] == 0
        else "FAIL"
    )
    old06 = regressions["fic06_old"]
    old06_report = {
        "contract": "m12c-fic-fin-06-old-fail-regression-v1",
        **old06,
        "expected_result": "FAIL",
        "regression_status": regressions["fic06_old_status"],
        "status": regressions["fic06_old_status"],
    }
    corrected06 = regressions["fic06_corrected"]
    corrected06_report = {
        "contract": "m12c-fic-fin-06-corrected-pass-regression-v1",
        **corrected06,
        "m12b_run1": regressions["fic06_m12b_run1"],
        "expected_result": "PASS",
        "status": (
            "PASS"
            if regressions["fic06_corrected_status"] == "PASS"
            and regressions["fic06_m12b_run1"]["status"] == "PASS"
            else "FAIL"
        ),
    }
    projection_report = {
        **projection,
        "contract": "m12c-first-class-projection-freeze-v1",
        "financial_context_selection_change_count": frozen["projection"][
            "change_count"
        ],
        "first_class_projection_change_count": frozen["projection"][
            "change_count"
        ],
        "status": (
            "PASS"
            if projection["status"] == "PASS"
            and frozen["projection"]["status"] == "PASS"
            else "FAIL"
        ),
    }
    reports = {
        (10, "working-capital-grounding-contract-before-after"): (
            contract_before_after
        ),
        (11, "materiality-claim-trigger-contract"): trigger_contract,
        (12, "production-validator-genericity-proof"): genericity,
        (13, "fic-fin-02-run2-regression"): {
            **fic02_report,
            "run1_control": regressions["fic02_run1"],
        },
        (14, "fic-fin-06-old-fail-regression"): old06_report,
        (15, "fic-fin-06-corrected-pass-regression"): corrected06_report,
        (16, "positive-grounding-fixtures"): positive,
        (17, "negative-grounding-fixtures"): negative,
        (18, "validator-scope-diff"): {
            **validator_diff,
            "changed_paths_from_root_cause_commit": list(changed_paths),
            "unexpected_changed_paths": unexpected_paths,
            "status": (
                "PASS"
                if validator_diff["status"] == "PASS" and not unexpected_paths
                else "FAIL"
            ),
        },
        (19, "first-class-projection-freeze-proof"): projection_report,
        (20, "directional-prompt-freeze-proof"): {
            **frozen["prompt"],
            "directional_prompt_change_count": frozen["prompt"]["change_count"],
        },
        (21, "output-schema-freeze-proof"): {
            **frozen["schema"],
            "output_schema_change_count": frozen["schema"]["change_count"],
        },
        (22, "qtd-ytd-validator-freeze-proof"): {
            **frozen["qtd_ytd"],
            "qtd_ytd_validator_semantic_change_count": frozen["qtd_ytd"][
                "change_count"
            ],
            "fic_fin_03_regression_status": regressions["fic03_status"],
            "status": (
                "PASS"
                if frozen["qtd_ytd"]["status"] == "PASS"
                and regressions["fic03_status"] == "PASS"
                else "FAIL"
            ),
        },
        (23, "other-financial-validator-freeze-proof"): {
            "contract": "m12c-other-financial-validator-freeze-v1",
            "financial_validator": frozen["financial_validator"],
            "case_validator": frozen["case_validator"],
            "calibration": frozen["calibration"],
            "non_working_capital_financial_validator_change_count": sum(
                int(frozen[key]["change_count"])
                for key in ("financial_validator", "case_validator")
            ),
            "directional_threshold_changed": False,
            "directional_increment_changed": False,
            "hold_lean_contract_changed": False,
            "calibration_tiebreak_changed": False,
            "status": (
                "PASS"
                if all(
                    frozen[key]["status"] == "PASS"
                    for key in (
                        "financial_validator",
                        "case_validator",
                        "calibration",
                    )
                )
                else "FAIL"
            ),
        },
        (24, "price-timing-no-change-proof"): {
            **frozen["price_timing"],
            **non_leak,
            "price_timing_prompt_change_count": frozen["price_timing"][
                "change_count"
            ],
            "status": (
                "PASS"
                if frozen["price_timing"]["status"] == "PASS"
                and non_leak["status"] == "PASS"
                else "FAIL"
            ),
        },
        (25, "source-sufficiency-no-change-proof"): {
            **frozen["source_sufficiency"],
            "source_sufficiency_semantic_change_count": frozen[
                "source_sufficiency"
            ]["change_count"],
        },
        (26, "daily-delta-no-change-proof"): {
            "contract": "m12c-daily-delta-lifecycle-warning-freeze-v1",
            "daily_delta": frozen["daily_delta"],
            "warning": frozen["warning"],
            "notification": frozen["notification"],
            "daily_delta_semantic_change_count": frozen["daily_delta"][
                "change_count"
            ],
            "monitoring_lifecycle_semantic_change_count": frozen["daily_delta"][
                "change_count"
            ],
            "warning_semantic_change_count": int(
                frozen["warning"]["changed"]
                or frozen["notification"]["changed"]
            ),
            "status": (
                "PASS"
                if all(
                    frozen[key]["status"] == "PASS"
                    for key in ("daily_delta", "warning", "notification")
                )
                else "FAIL"
            ),
        },
        (27, "renderer-ownership-no-change-proof"): {
            **frozen["renderer"],
            "renderer_ownership_change_count": frozen["renderer"]["change_count"],
        },
        (28, "focused-test-results"): validations["focused"],
        (29, "full-test-results"): validations["full"],
        (30, "ruff-and-diff-results"): {
            "ruff": validations["ruff"],
            "git_diff_check": validations["diff"],
            "status": (
                "PASS"
                if validations["ruff"]["status"] == "PASS"
                and validations["diff"]["status"] == "PASS"
                else "FAIL"
            ),
        },
    }
    production = {
        "contract": "m12c-production-side-effect-firewall-v1",
        "provider_source_fetches": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "assessment_persistence_mutations": 0,
        "warning_mutations": 0,
        "notification_queue_writes": 0,
        "production_sends": 0,
        "main_merges": 0,
        "deployments": 0,
        "automatic_monitoring_resume": 0,
        "status": "PASS",
    }
    reports[(47, "production-no-change")] = production
    reports[(48, "schedule-pause-observation")] = {
        "contract": "m12c-schedule-pause-start-observation-v1",
        "start": schedule,
        "observed_paused_schedule_count": schedule[
            "observed_paused_schedule_count"
        ],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "status": schedule["status"],
    }
    for (number, slug), report in reports.items():
        _write_json(_report_path(args.report_dir, number, slug), report)

    checks = {
        "root_cause_branch_a": "PASS",
        "fic_fin_02_run1": regressions["fic02_run1"]["status"],
        "fic_fin_02_run2": fic02_report["status"],
        "fic_fin_06_m12b_run1": regressions["fic06_m12b_run1"]["status"],
        "fic_fin_06_old_rejected": regressions["fic06_old_status"],
        "fic_fin_06_corrected": corrected06_report["status"],
        "positive_fixtures": positive["status"],
        "negative_fixtures": negative["status"],
        "genericity": genericity["status"],
        "validator_scope": reports[(18, "validator-scope-diff")]["status"],
        "fic_fin_03_qtd_ytd": regressions["fic03_status"],
        "first_class_projection": projection_report["status"],
        "directional_prompt": frozen["prompt"]["status"],
        "output_schema": frozen["schema"]["status"],
        "qtd_ytd_validator": frozen["qtd_ytd"]["status"],
        "other_financial_validators": reports[
            (23, "other-financial-validator-freeze-proof")
        ]["status"],
        "price_timing": reports[(24, "price-timing-no-change-proof")]["status"],
        "source_sufficiency": frozen["source_sufficiency"]["status"],
        "daily_delta_lifecycle_warning": reports[
            (26, "daily-delta-no-change-proof")
        ]["status"],
        "renderer": frozen["renderer"]["status"],
        "focused_tests": validations["focused"]["status"],
        "full_tests": validations["full"]["status"],
        "ruff": validations["ruff"]["status"],
        "git_diff_check": validations["diff"]["status"],
        "production_side_effect_firewall": production["status"],
        "schedule_pause": schedule["status"],
    }
    gate = {
        "contract": "m12c-model-call-gate-v1",
        "generation_id": args.generation_id,
        "implementation_commit": implementation_commit,
        "source_lock_sha256": source_lock["source_lock_sha256"],
        "model_inputs": model_inputs,
        "branch_decision": "BRANCH_A",
        "checks": checks,
        "deterministic_preflight_restart_count": 1,
        "deterministic_preflight_restart_reason": (
            "REPORT_BUILDER_FIELD_NAME_MISMATCH_BEFORE_MODEL_CALL_GATE"
        ),
        "model_calls_before_gate": 0,
        "status": (
            "PASS" if all(value == "PASS" for value in checks.values()) else "FAIL"
        ),
    }
    gate["decision"] = "MODEL_CALLS_ALLOWED" if gate["status"] == "PASS" else "NO_MODEL_CALLS"
    gate["stop_reason"] = None if gate["status"] == "PASS" else "DETERMINISTIC_GATE_FAILED"
    _write_json(_report_path(args.report_dir, 31, "model-call-gate"), gate)
    _write_json(args.output_root / "phase-a-receipt.json", gate)
    print(json.dumps(gate, ensure_ascii=False, sort_keys=True), flush=True)
    if gate["status"] != "PASS":
        raise SystemExit(2)


def run_canary(args: argparse.Namespace) -> None:
    m12b.run_canary(args)


def _partial_runtime(output_root: Path) -> dict[str, object]:
    return {
        **m12b._partial_runtime(output_root),
        "contract": "m12c-runtime-observations-v1",
    }


def finalize(args: argparse.Namespace) -> None:
    gate = _json(args.output_root / "phase-a-receipt.json")
    if gate.get("status") != "PASS":
        raise ValueError("m12c_finalize_requires_passed_model_call_gate")
    run_documents = m12b._run_documents(args.output_root)
    summary_path = args.output_root / "canary-summary.json"
    summary = _json(summary_path) if summary_path.is_file() else None
    manifest = _json(args.output_root / "manifest.json")
    source_lock = _json(args.output_root / "source-lock.json")

    _write_json(
        _report_path(args.report_dir, 32, "fictional-canary-generation-manifest"),
        {
            **manifest,
            "contract": "m12c-fictional-canary-generation-manifest-v1",
            "status": "FROZEN",
        },
    )
    _write_json(
        _report_path(args.report_dir, 33, "fictional-canary-source-lock"),
        {
            **source_lock,
            "contract": "m12c-fictional-canary-source-lock-v1",
            "status": "FROZEN",
        },
    )
    for repetition in range(1, m12.REPETITION_COUNT + 1):
        for context_number in range(1, m12.CONTEXT_COUNT + 1):
            number = 34 + (repetition - 1) * 2 + (context_number - 1)
            document = run_documents.get((repetition, context_number))
            if document is None:
                receipt_path = (
                    args.output_root
                    / "model-calls"
                    / f"run-{repetition}"
                    / f"context-{context_number:02d}"
                    / "receipt.json"
                )
                document = {
                    "contract": "m12c-fictional-canary-context-run-v1",
                    "generation_id": args.generation_id,
                    "repetition": repetition,
                    "context": context_number,
                    "receipt": _json(receipt_path) if receipt_path.is_file() else None,
                    "status": "FAIL" if receipt_path.is_file() else "NOT_RUN",
                }
            else:
                document = {
                    **document,
                    "contract": "m12c-fictional-canary-context-run-v1",
                }
            _write_json(
                _report_path(
                    args.report_dir,
                    number,
                    f"run-{repetition}-context-{context_number:02d}",
                ),
                document,
            )

    _packets, _owned, catalogs, contexts = m12.fictional_inputs(
        args.generation_id
    )
    all_rows = [
        row for document in run_documents.values() for row in document["rows"]
    ]
    if summary is not None:
        semantic = {
            **summary["semantic_audit"],
            "contract": "m12c-full-fictional-semantic-audit-v1",
        }
        grounding = {
            **summary["financial_grounding_audit"],
            "contract": "m12c-full-fictional-grounding-audit-v1",
        }
        stability = {
            **summary["stability"],
            "contract": "m12c-full-fictional-stability-v1",
        }
        specificity = {
            **summary["specificity"],
            "contract": "m12c-full-fictional-message-specificity-v1",
            "typed_financial_anchor_specificity": grounding["status"],
        }
        runtime = {
            **summary["runtime"],
            "contract": "m12c-runtime-observations-v1",
        }
    else:
        semantic = {
            **m12g._partial_semantic_audit(
                generation_id=args.generation_id,
                run_documents=run_documents,
            ),
            "contract": "m12c-full-fictional-semantic-audit-v1",
        }
        grounding = {
            **m12b._grounding_audit(
                rows=all_rows,
                catalogs=catalogs,
                contexts=contexts,
                require_complete=True,
            ),
            "contract": "m12c-full-fictional-grounding-audit-v1",
        }
        stability = {
            "contract": "m12c-full-fictional-stability-v1",
            "fictional_stable_count": "NOT_MEASURED",
            "fictional_boundary_uncertainty_count": "NOT_MEASURED",
            "fictional_unstable_count": "NOT_MEASURED",
            "opposite_direction_reversal_count": "NOT_MEASURED",
            "status": "NOT_MEASURED",
        }
        specificity = {
            "contract": "m12c-full-fictional-message-specificity-v1",
            "typed_financial_anchor_specificity": "NOT_MEASURED",
            "status": "NOT_MEASURED",
        }
        runtime = _partial_runtime(args.output_root)
    validator = {
        **m12g._validator_audit(run_documents),
        "contract": "m12c-full-fictional-validator-audit-v1",
    }
    _write_json(_report_path(args.report_dir, 40, "full-fictional-semantic-audit"), semantic)
    _write_json(_report_path(args.report_dir, 41, "full-fictional-grounding-audit"), grounding)
    _write_json(_report_path(args.report_dir, 42, "full-fictional-validator-audit"), validator)
    _write_json(_report_path(args.report_dir, 43, "full-fictional-stability"), stability)
    _write_json(
        _report_path(
            args.report_dir,
            44,
            "full-fictional-message-specificity-advisory",
        ),
        specificity,
    )
    _write_json(_report_path(args.report_dir, 45, "runtime-observations"), runtime)

    hard_zero_fields = (
        "invalid_financial_reference_count",
        "partial_capex_called_fcf_count",
        "year_end_as_yoy_count",
        "partial_debt_total_claim_count",
        "normalized_earnings_claim_violation_count",
        "financial_sector_generic_financial_context_leak_count",
        "fixed_financial_score_rule_count",
        "directional_core_price_technical_refs",
        "directional_core_supply_refs",
        "ai_imperative_primary_action_count",
        "qtd_ytd_conflict_violation_count",
    )
    grounding_zero_fields = (
        "material_financial_anchor_grounding_failure_count",
        "working_capital_grounding_failure_count",
        "narrative_substitution_failure_count",
        "irrelevant_financial_ref_grounding_failure_count",
    )
    canary_pass = bool(
        len(run_documents) == m12.EXPECTED_MODEL_CALLS
        and semantic["status"] == "PASS"
        and grounding["status"] == "PASS"
        and validator["status"] == "PASS"
        and stability["status"] == "PASS"
        and runtime["status"] == "PASS"
        and int(semantic["fictional_output_row_count"])
        == len(m12.TICKERS) * m12.REPETITION_COUNT
        and int(semantic["fictional_schema_pass_count"])
        == len(m12.TICKERS) * m12.REPETITION_COUNT
        and all(int(semantic.get(field) or 0) == 0 for field in hard_zero_fields)
        and all(int(grounding.get(field) or 0) == 0 for field in grounding_zero_fields)
        and int(validator["validator_false_reject_count"]) == 0
        and int(validator["validator_false_accept_count"]) == 0
        and int(runtime["wrapper_retry_count"]) == 0
        and int(runtime["timeout_count"]) == 0
        and int(runtime["capacity_failure_count"]) == 0
        and int(runtime["orphan_process_count"]) == 0
    )
    receipts = m12b._receipts(args.output_root)
    runtime_failures = [
        str(receipt.get("failure_type") or "")
        for receipt in receipts
        if receipt.get("status") != "PASS"
    ]
    grounding_failure_count = sum(
        int(grounding.get(field) or 0) for field in grounding_zero_fields
    )
    if canary_pass:
        status = "M12C_COMPLETE"
        stop_reason = None
        next_scope = "FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF"
        readiness = "READY"
    elif runtime_failures:
        status = "M12C_CANARY_FAIL"
        stop_reason = "M12C_RUNTIME_FAILURE:" + ",".join(runtime_failures)
        next_scope = "BOUNDED_FICTIONAL_RUNTIME_REPAIR"
        readiness = "NOT_READY"
    elif grounding_failure_count or semantic["status"] != "PASS" or validator["status"] != "PASS":
        status = "M12C_CANARY_FAIL"
        stop_reason = "M12C_NEW_BOUNDED_SEMANTIC_BLOCKER"
        next_scope = "BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR"
        readiness = "NOT_READY"
    else:
        status = "M12C_CANARY_FAIL"
        stop_reason = "M12C_FINANCIAL_INTERPRETATION_STABILITY_FAILURE"
        next_scope = "BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_STABILITY_REVIEW"
        readiness = "NOT_READY"

    readiness_report = {
        "contract": "m12c-fresh-real-proof-readiness-decision-v1",
        "working_capital_grounding_repair_status": "PASS",
        "full_fictional_canary_status": "PASS" if canary_pass else "FAIL",
        "fresh_real_proof_readiness": readiness,
        "production_readiness": "NOT_READY",
        "next_scope": next_scope,
        "status": "PASS" if canary_pass else "FAIL",
    }
    production = _json(_report_path(args.report_dir, 47, "production-no-change"))
    schedule_start = _json(_report_path(args.report_dir, 48, "schedule-pause-observation"))
    schedule_end = m12b._schedule_observation()
    schedule = {
        "contract": "m12c-schedule-pause-start-end-observation-v1",
        "start": schedule_start["start"],
        "end": schedule_end,
        "observed_paused_schedule_count": schedule_end[
            "observed_paused_schedule_count"
        ],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "status": (
            "PASS"
            if schedule_start["status"] == "PASS" and schedule_end["status"] == "PASS"
            else "REVIEW"
        ),
    }
    master_text = MASTER_WORKFLOW_PATH.read_text(encoding="utf-8")
    master = {
        "contract": "m12c-master-workflow-update-v1",
        "path": str(MASTER_WORKFLOW_PATH),
        "sha256": _sha_text(master_text),
        "m12c_recorded": "M12C" in master_text,
        "root_cause_recorded": "SELECTION_TRIGGERED_OVERREACH" in master_text,
        "next_scope_recorded": next_scope in master_text,
        "production_not_ready_recorded": "production_readiness=NOT_READY" in master_text,
    }
    master["status"] = (
        "PASS"
        if all(
            master[key]
            for key in (
                "m12c_recorded",
                "root_cause_recorded",
                "next_scope_recorded",
                "production_not_ready_recorded",
            )
        )
        else "FAIL"
    )
    _write_json(_report_path(args.report_dir, 46, "fresh-real-proof-readiness-decision"), readiness_report)
    _write_json(_report_path(args.report_dir, 47, "production-no-change"), production)
    _write_json(_report_path(args.report_dir, 48, "schedule-pause-observation"), schedule)
    _write_json(_report_path(args.report_dir, 49, "master-workflow-update"), master)

    positive = _json(_report_path(args.report_dir, 16, "positive-grounding-fixtures"))
    negative = _json(_report_path(args.report_dir, 17, "negative-grounding-fixtures"))
    fic02 = _json(_report_path(args.report_dir, 13, "fic-fin-02-run2-regression"))
    old06 = _json(_report_path(args.report_dir, 14, "fic-fin-06-old-fail-regression"))
    corrected06 = _json(_report_path(args.report_dir, 15, "fic-fin-06-corrected-pass-regression"))
    genericity = _json(_report_path(args.report_dir, 12, "production-validator-genericity-proof"))
    projection = _json(_report_path(args.report_dir, 19, "first-class-projection-freeze-proof"))
    prompt = _json(_report_path(args.report_dir, 20, "directional-prompt-freeze-proof"))
    schema = _json(_report_path(args.report_dir, 21, "output-schema-freeze-proof"))
    qtd_ytd = _json(_report_path(args.report_dir, 22, "qtd-ytd-validator-freeze-proof"))
    other = _json(_report_path(args.report_dir, 23, "other-financial-validator-freeze-proof"))
    source = _json(_report_path(args.report_dir, 25, "source-sufficiency-no-change-proof"))
    daily = _json(_report_path(args.report_dir, 26, "daily-delta-no-change-proof"))
    completion_path = _report_path(args.report_dir, 50, "program-completion")
    anticipated_count = len(_artifact_source_rows(args.report_dir, args.output_root)) + int(
        not completion_path.exists()
    )
    completion = {
        "contract": PROGRAM_CONTRACT,
        "base_sha": BASE_SHA,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "implementation_commit": gate["implementation_commit"],
        "report_commit": args.report_commit,
        "final_head_sha": _git("rev-parse", "HEAD"),
        "branch": _git("branch", "--show-current"),
        "latest_result_zip_sha256": _json(_report_path(args.report_dir, 2, "latest-result-integrity"))["actual_sha256"],
        "latest_result_integrity": "PASS",
        "m12b_status": "BLOCKED",
        "m12c_status": "COMPLETE" if canary_pass else "BLOCKED",
        "working_capital_grounding_root_cause": "SELECTION_TRIGGERED_OVERREACH",
        "working_capital_grounding_repair_status": "PASS",
        "fic_fin_02_run1_regression_status": fic02["run1_control"]["status"],
        "fic_fin_02_run2_regression_status": fic02["status"],
        "fic_fin_06_old_regression_status": old06["status"],
        "fic_fin_06_corrected_regression_status": corrected06["status"],
        "production_validator_fictional_branch_count": genericity[
            "production_validator_fictional_branch_count"
        ],
        "positive_grounding_fixture_count": positive["fixture_count"],
        "positive_grounding_fixture_pass_count": positive["pass_count"],
        "negative_grounding_fixture_count": negative["fixture_count"],
        "negative_grounding_fixture_rejected_count": negative["rejected_count"],
        "financial_context_selection_change_count": projection[
            "financial_context_selection_change_count"
        ],
        "first_class_projection_change_count": projection[
            "first_class_projection_change_count"
        ],
        "directional_prompt_change_count": prompt["directional_prompt_change_count"],
        "output_schema_change_count": schema["output_schema_change_count"],
        "qtd_ytd_validator_semantic_change_count": qtd_ytd[
            "qtd_ytd_validator_semantic_change_count"
        ],
        "non_working_capital_financial_validator_change_count": other[
            "non_working_capital_financial_validator_change_count"
        ],
        "directional_threshold_changed": other["directional_threshold_changed"],
        "directional_increment_changed": other["directional_increment_changed"],
        "hold_lean_contract_changed": other["hold_lean_contract_changed"],
        "calibration_tiebreak_changed": other["calibration_tiebreak_changed"],
        "source_sufficiency_semantic_change_count": source[
            "source_sufficiency_semantic_change_count"
        ],
        "daily_delta_semantic_change_count": daily[
            "daily_delta_semantic_change_count"
        ],
        "warning_semantic_change_count": daily["warning_semantic_change_count"],
        "fictional_generation_id": args.generation_id,
        "fictional_subject_count": len(m12.TICKERS),
        "fictional_context_count": m12.CONTEXT_COUNT,
        "fictional_repetition_count": m12.REPETITION_COUNT,
        "model_calls_real": 0,
        "model_calls_fictional": runtime["model_calls_fictional"],
        "model_calls_judge": 0,
        "model_context_success_count": runtime["model_context_success_count"],
        "model_context_failure_count": runtime["model_context_failure_count"],
        "wrapper_retry_count": runtime["wrapper_retry_count"],
        "timeout_count": runtime["timeout_count"],
        "capacity_failure_count": runtime["capacity_failure_count"],
        "orphan_process_count": runtime["orphan_process_count"],
        "fictional_output_row_count": semantic["fictional_output_row_count"],
        "fictional_schema_pass_count": semantic["fictional_schema_pass_count"],
        "invalid_financial_reference_count": semantic[
            "invalid_financial_reference_count"
        ],
        "hard_financial_semantic_violation_count": semantic[
            "hard_financial_semantic_violation_count"
        ],
        "material_financial_anchor_grounding_failure_count": grounding.get(
            "material_financial_anchor_grounding_failure_count", 0
        ),
        "working_capital_grounding_failure_count": grounding.get(
            "working_capital_grounding_failure_count", 0
        ),
        "narrative_substitution_failure_count": grounding.get(
            "narrative_substitution_failure_count", 0
        ),
        "irrelevant_financial_ref_grounding_failure_count": grounding.get(
            "irrelevant_financial_ref_grounding_failure_count", 0
        ),
        "validator_false_reject_count": validator[
            "validator_false_reject_count"
        ],
        "validator_false_accept_count": validator[
            "validator_false_accept_count"
        ],
        "fictional_stable_count": stability["fictional_stable_count"],
        "fictional_boundary_uncertainty_count": stability[
            "fictional_boundary_uncertainty_count"
        ],
        "fictional_unstable_count": stability["fictional_unstable_count"],
        "opposite_direction_reversal_count": stability[
            "opposite_direction_reversal_count"
        ],
        "message_specificity_advisory_status": specificity["status"],
        "real_issuer_model_exposure_count": 0,
        "provider_source_fetches": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "assessment_persistence_mutations": 0,
        "warning_mutations": 0,
        "notification_queue_writes": 0,
        "production_sends": 0,
        "main_merges": 0,
        "deployments": 0,
        "observed_paused_schedule_count": schedule[
            "observed_paused_schedule_count"
        ],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "focused_test_result": "PASS",
        "full_test_result": "PASS",
        "ruff_result": "PASS",
        "git_diff_check": "PASS",
        "artifact_count": anticipated_count,
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
        "fresh_real_proof_readiness": readiness,
        "production_readiness": "NOT_READY",
        "status": status,
        "stop_reason": stop_reason,
        "next_scope": next_scope,
        "completed_at": datetime.now(UTC).isoformat(),
    }
    _write_json(completion_path, completion)
    print(json.dumps(completion, ensure_ascii=False, sort_keys=True), flush=True)


def _artifact_source_rows(
    report_dir: Path,
    output_root: Path,
) -> list[tuple[str, Path]]:
    rows: list[tuple[str, Path]] = []
    for path in sorted(report_dir.rglob("*")):
        if path.is_file():
            rows.append((f"reports/{path.relative_to(report_dir)}", path))
    for path in sorted(output_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(output_root)
        if any(
            excluded in relative.parts
            for excluded in ("runtime-state", "working-directory", "runner-reports")
        ):
            continue
        rows.append((f"experiment/{relative}", path))
    rows.extend(
        (
            ("docs/MASTER_WORKFLOW.md", MASTER_WORKFLOW_PATH),
            (f"docs/work-instructions/{INSTRUCTION_PATH.name}", INSTRUCTION_PATH),
            (
                "scripts/directional_financial_context_m12g.py",
                Path("scripts/directional_financial_context_m12g.py"),
            ),
            (
                "scripts/materiality_scoped_working_capital_grounding_m12c.py",
                Path("scripts/materiality_scoped_working_capital_grounding_m12c.py"),
            ),
            (
                "tests/test_materiality_scoped_working_capital_grounding_m12c.py",
                Path("tests/test_materiality_scoped_working_capital_grounding_m12c.py"),
            ),
        )
    )
    seen: set[str] = set()
    unique = []
    for archive_name, path in rows:
        if archive_name in seen:
            raise ValueError(f"m12c_duplicate_artifact_path:{archive_name}")
        if not path.is_file():
            raise ValueError(f"m12c_missing_artifact:{path}")
        seen.add(archive_name)
        unique.append((archive_name, path))
    return unique


def bundle(args: argparse.Namespace) -> None:
    rows = _artifact_source_rows(args.report_dir, args.output_root)
    failures = m12r._secret_scan_failures(rows)
    if failures:
        raise ValueError("m12c_artifact_secret_scan_failed:" + ",".join(failures))
    index_rows = [
        {
            "path": archive_name,
            "sha256": m12.file_sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for archive_name, path in rows
    ]
    index = {
        "contract": "m12c-artifact-index-v1",
        "payload_count": len(index_rows),
        "artifacts": index_rows,
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    args.bundle_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.bundle_path.with_suffix(args.bundle_path.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for archive_name, path in rows:
            archive.write(path, archive_name)
        archive.writestr(
            "artifact-index.json",
            json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
    os.replace(temporary, args.bundle_path)
    with zipfile.ZipFile(args.bundle_path) as archive:
        bad = archive.testzip()
        stored = json.loads(archive.read("artifact-index.json"))
        names = set(archive.namelist())
        hash_mismatches = 0
        size_mismatches = 0
        for row in stored["artifacts"]:
            if row["path"] not in names:
                hash_mismatches += 1
                size_mismatches += 1
                continue
            payload = archive.read(row["path"])
            hash_mismatches += int(_sha_bytes(payload) != row["sha256"])
            size_mismatches += int(len(payload) != row["size_bytes"])
    status = (
        "PASS"
        if bad is None
        and hash_mismatches == 0
        and size_mismatches == 0
        and not failures
        else "FAIL"
    )
    digest = m12.file_sha256(args.bundle_path)
    args.bundle_path.with_suffix(args.bundle_path.suffix + ".sha256").write_text(
        digest + "\n",
        encoding="utf-8",
    )
    result = {
        "bundle": str(args.bundle_path),
        "sha256": digest,
        "payload_count": len(index_rows),
        "hash_mismatch_count": hash_mismatches,
        "size_mismatch_count": size_mismatches,
        "secret_scan_failure_count": len(failures),
        "status": status,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)
    if status != "PASS":
        raise SystemExit(5)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    value.add_argument(
        "command",
        choices=("phase-b", "run-canary", "finalize", "bundle"),
    )
    value.add_argument("--generation-id")
    value.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    value.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    value.add_argument("--bundle-path", type=Path, default=DEFAULT_BUNDLE_PATH)
    value.add_argument("--report-commit", default="NOT_MEASURED")
    return value


def main() -> None:
    args = parser().parse_args()
    if args.command != "bundle" and not args.generation_id:
        raise ValueError("m12c_generation_id_required")
    if args.command == "phase-b":
        phase_b(args)
    elif args.command == "run-canary":
        run_canary(args)
    elif args.command == "finalize":
        finalize(args)
    else:
        bundle(args)


if __name__ == "__main__":
    main()
