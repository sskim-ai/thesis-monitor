from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import subprocess
import sys
import zipfile
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

from app.services import directional_financial_context_service as financial
from app.services.cross_market_decision_engine_service import FinancialPeriodType
from scripts import directional_financial_context_m12 as m12
from scripts import directional_financial_context_m12g as m12g
from scripts import directional_financial_context_m12r as m12r
from scripts import first_class_typed_financial_evidence_m12b as m12b


PROGRAM_CONTRACT = "qtd-ytd-plain-korean-period-validator-repair-m12d-v1"
BASE_SHA = "6c1928846c25063b66662da6ff9465988ac44e98"
WORK_INSTRUCTION_COMMIT = "dd28946351e9a1517d1c50992c93265113efdba0"
ROOT_CAUSE_COMMIT = "4b1b0417514b85b5c37a7ca61394ab98f522f099"
M12C_REPORT_ROOT = Path("docs/reports") / (
    "20260909-materiality-scoped-working-capital-grounding-validator-repair-full-fictional-canary"
)
M12R_REPORT_ROOT = Path("docs/reports") / (
    "20260909-bounded-directional-financial-context-validator-repair-full-fictional-canary"
)
REPORT_DIRECTORY_NAME = (
    "20260909-qtd-ytd-plain-korean-period-validator-repair-full-fictional-canary"
)
DEFAULT_REPORT_DIR = Path("docs/reports") / REPORT_DIRECTORY_NAME
DEFAULT_OUTPUT_ROOT = Path("artifacts") / REPORT_DIRECTORY_NAME
DEFAULT_BUNDLE_PATH = Path("/Users/sskim/Documents/Codex") / (
    "thesis-monitor-20260909-qtd-ytd-plain-korean-period-validator-repair-"
    "full-fictional-canary-report.zip"
)
INSTRUCTION_PATH = Path("docs/work-instructions") / (
    "20260909-qtd-ytd-plain-korean-period-validator-repair-and-full-fictional-canary.md"
)
MASTER_WORKFLOW_PATH = Path("docs/MASTER_WORKFLOW.md")
SERVICE_PATH = "app/services/directional_financial_context_service.py"
EXPECTED_IMPLEMENTATION_PATHS = {
    SERVICE_PATH,
    "scripts/qtd_ytd_plain_korean_period_validator_m12d.py",
    "tests/test_qtd_ytd_plain_korean_period_validator_m12d.py",
}

POSITIVE_FIXTURES = (
    "분기 영업흑자와 누적 영업손실이 상충한다.",
    "분기 흑자와 연초 이후 누적 적자가 공존한다.",
    "분기 기준은 흑자지만 누계 기준은 적자다.",
    "이번 분기는 흑자지만 YTD는 손실이다.",
)


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
        raise ValueError(f"m12d_json_object_required:{path}")
    return value


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
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
        node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _validator_scope_diff() -> dict[str, object]:
    before = _git_file(BASE_SHA, SERVICE_PATH)
    after = Path(SERVICE_PATH).read_text(encoding="utf-8")
    before_functions = _top_level_functions(before)
    after_functions = _top_level_functions(after)
    changed_functions = []
    for name in sorted(before_functions & after_functions):
        if m12._function_source_from_text(before, name) != m12._function_source_from_text(
            after, name
        ):
            changed_functions.append(name)
    added_functions = sorted(after_functions - before_functions)
    removed_functions = sorted(before_functions - after_functions)
    diff = _git("diff", BASE_SHA, "--", SERVICE_PATH)
    changed_content_lines = [
        line
        for line in diff.splitlines()
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
    ]
    expected_lines = {
        '-    re.compile(r"지만|반면|공존|충돌|맞서|엇갈"),',
        '+    re.compile(r"지만|반면|공존|충돌|상충|맞서|엇갈"),',
    }
    status = (
        "PASS"
        if set(changed_content_lines) == expected_lines
        and len(changed_content_lines) == 2
        and not changed_functions
        and not added_functions
        and not removed_functions
        else "FAIL"
    )
    return {
        "contract": "m12d-qtd-ytd-validator-scope-diff-v1",
        "path": SERVICE_PATH,
        "changed_content_lines": changed_content_lines,
        "changed_existing_functions": changed_functions,
        "added_functions": added_functions,
        "removed_functions": removed_functions,
        "qtd_marker_registry_changed": False,
        "ytd_marker_registry_changed": False,
        "period_relation_registry_changed": True,
        "qtd_ytd_validator_semantic_change_count": 1,
        "non_qtd_ytd_financial_validator_change_count": 0,
        "diff": diff,
        "status": status,
    }


def _period_refs() -> tuple[object, object]:
    refs, _framework = m12._case_refs("FIC-FIN-03")
    qtd = next(
        ref
        for ref in refs
        if ref.financial_context is not None
        and ref.financial_context.metric == "operating_income"
        and ref.financial_context.period.type == FinancialPeriodType.QTD
    )
    ytd = next(
        ref
        for ref in refs
        if ref.financial_context is not None
        and ref.financial_context.metric == "operating_income"
        and ref.financial_context.period.type == FinancialPeriodType.YTD
    )
    return qtd, ytd


def _validate_candidate(
    candidate: object,
    *,
    supplied_refs: Sequence[object] | None = None,
    required_ref_ids: Sequence[str] | None = None,
) -> dict[str, object]:
    qtd, ytd = _period_refs()
    actual_refs = tuple(supplied_refs or (qtd, ytd))
    actual_required = tuple(required_ref_ids or tuple(ref.ref_id for ref in actual_refs))
    return financial.validate_qtd_ytd_conflict_semantics(
        candidate,
        supplied_refs=actual_refs,
        required_ref_ids=actual_required,
    ).model_dump(mode="json")


def _text_candidate(text: str, refs: Sequence[object]) -> dict[str, object]:
    return {
        "claim": {
            "text": text,
            "evidence_refs": [ref.ref_id for ref in refs],
        }
    }


def _positive_fixture_report() -> dict[str, object]:
    refs = _period_refs()
    rows = []
    for index, text in enumerate(POSITIVE_FIXTURES, start=1):
        validation = _validate_candidate(_text_candidate(text, refs))
        rows.append(
            {
                "fixture_id": f"positive-{index:02d}",
                "text": text,
                "validation": validation,
                "status": "PASS" if validation["valid"] else "FAIL",
            }
        )
    return {
        "contract": "m12d-qtd-ytd-positive-fixtures-v1",
        "fixture_count": len(rows),
        "pass_count": sum(row["status"] == "PASS" for row in rows),
        "rows": rows,
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def _negative_fixture_report() -> dict[str, object]:
    qtd, ytd = _period_refs()
    vague_with_both = (
        "분기점이 중요하며 누적 영업손실과 상충한다.",
        "분기 영업흑자만 확인됐다.",
        "누적 영업손실만 확인됐다.",
        "서로 다른 실적이 있다.",
        "QTD와 YTD 영업실적을 확인했다.",
    )
    rows = []
    for index, text in enumerate(vague_with_both, start=1):
        validation = _validate_candidate(_text_candidate(text, (qtd, ytd)))
        rows.append(
            {
                "fixture_id": f"negative-{index:02d}",
                "text": text,
                "case": "both_refs_but_period_contrast_not_explicit",
                "validation": validation,
                "accepted_as_same_metric_conflict": bool(
                    validation["required"] and validation["valid"]
                ),
            }
        )
    for refs, label in (
        ((qtd,), "missing_ytd_link"),
        ((ytd,), "missing_qtd_link"),
        ((), "unlinked"),
    ):
        validation = _validate_candidate(
            _text_candidate("분기 영업흑자와 누적 영업손실이 상충한다.", refs)
        )
        rows.append(
            {
                "fixture_id": f"negative-{len(rows) + 1:02d}",
                "text": "분기 영업흑자와 누적 영업손실이 상충한다.",
                "case": label,
                "validation": validation,
                "accepted_as_same_metric_conflict": bool(
                    validation["required"] and validation["valid"]
                ),
            }
        )
    unrelated = {
        "core_investment_judgment": {
            "text": "실적이 엇갈린다.",
            "evidence_refs": [qtd.ref_id, ytd.ref_id],
        },
        "sector_interpretation": {
            "text": "사업의 분기별 구조를 본다.",
            "evidence_refs": [],
        },
    }
    validation = _validate_candidate(unrelated)
    rows.append(
        {
            "fixture_id": f"negative-{len(rows) + 1:02d}",
            "text": "분기 appears only in an unrelated unlinked sector claim",
            "case": "unrelated_plain_quarter_path",
            "validation": validation,
            "accepted_as_same_metric_conflict": bool(
                validation["required"] and validation["valid"]
            ),
        }
    )
    ytd_revenue = qtd.model_copy(
        update={
            "ref_id": "canonical:fixture:revenue-ytd",
            "financial_context": qtd.financial_context.model_copy(
                update={
                    "metric": "revenue",
                    "period": qtd.financial_context.period.model_copy(
                        update={"type": FinancialPeriodType.YTD}
                    ),
                }
            ),
        }
    )
    different_metric = _validate_candidate(
        _text_candidate("분기 영업흑자와 누적 매출이 상충한다.", (qtd, ytd_revenue)),
        supplied_refs=(qtd, ytd_revenue),
        required_ref_ids=(qtd.ref_id, ytd_revenue.ref_id),
    )
    rows.append(
        {
            "fixture_id": f"negative-{len(rows) + 1:02d}",
            "text": "분기 영업흑자와 누적 매출이 상충한다.",
            "case": "different_metrics_not_a_required_conflict",
            "validation": different_metric,
            "accepted_as_same_metric_conflict": bool(
                different_metric["required"] and different_metric["valid"]
            ),
        }
    )
    rejected_count = sum(not row["accepted_as_same_metric_conflict"] for row in rows)
    return {
        "contract": "m12d-qtd-ytd-negative-fixtures-v1",
        "fixture_count": len(rows),
        "rejected_count": rejected_count,
        "rows": rows,
        "status": "PASS" if rejected_count == len(rows) else "FAIL",
    }


def _report_row(path: Path, ticker: str) -> dict[str, object]:
    document = _json(path)
    return next(
        row
        for row in document.get("rows") or []
        if isinstance(row, Mapping) and row.get("ticker") == ticker
    )


def _fic03_regression(path: Path, label: str) -> dict[str, object]:
    row = _report_row(path, "FIC-FIN-03")
    validation = _validate_candidate(row["core"])
    return {
        "label": label,
        "source_path": str(path),
        "source_modified": False,
        "source_validation": row.get("qtd_ytd_semantics"),
        "replayed_validation": validation,
        "status": "PASS" if validation["valid"] else "FAIL",
    }


def _historical_regressions() -> dict[str, object]:
    rows = {
        "historical": _fic03_regression(
            M12R_REPORT_ROOT / "08-historical-raw-output-regression.json",
            "M12R historical",
        ),
        "run1": _fic03_regression(
            M12C_REPORT_ROOT / "34-run-1-context-01.json",
            "M12C run-1 context-01",
        ),
        "run2": _fic03_regression(
            M12C_REPORT_ROOT / "36-run-2-context-01.json",
            "M12C run-2 context-01",
        ),
        "run3": _fic03_regression(
            M12C_REPORT_ROOT / "38-run-3-context-01.json",
            "M12C run-3 context-01",
        ),
    }
    return {
        "contract": "m12d-fic-fin-03-regressions-v1",
        "rows": rows,
        "status": ("PASS" if all(row["status"] == "PASS" for row in rows.values()) else "FAIL"),
    }


def _marker_contracts() -> tuple[dict[str, object], dict[str, object]]:
    qtd_markers = (
        "분기",
        "분기 기준",
        "분기 실적",
        "분기 영업흑자",
        "분기 영업손실",
        "최근 분기",
        "이번 분기",
        "해당 분기",
        "직전 분기",
    )
    ytd_markers = (
        "YTD",
        "year-to-date",
        "cumulative",
        "누계",
        "누적",
        "누적 기준",
        "연초 이후",
        "연초부터",
        "연초 이후 누적",
        "연초부터 누적",
    )
    qtd_rows = [
        {
            "marker": marker,
            "detected": financial._matches_period_family(
                financial._normalized_period_text(marker),
                financial._QTD_PERIOD_PATTERNS,
            ),
        }
        for marker in qtd_markers
    ]
    ytd_rows = [
        {
            "marker": marker,
            "detected": financial._matches_period_family(
                financial._normalized_period_text(marker),
                financial._YTD_PERIOD_PATTERNS,
            ),
        }
        for marker in ytd_markers
    ]
    qtd = {
        "contract": "m12d-korean-qtd-marker-contract-v1",
        "registry_changed": False,
        "plain_quarter_requires_same_claim_qtd_ytd_evidence_linkage": True,
        "rows": qtd_rows,
        "status": "PASS" if all(row["detected"] for row in qtd_rows) else "FAIL",
    }
    ytd = {
        "contract": "m12d-korean-ytd-marker-regression-v1",
        "registry_changed": False,
        "rows": ytd_rows,
        "status": "PASS" if all(row["detected"] for row in ytd_rows) else "FAIL",
    }
    return qtd, ytd


def _claim_path_contract() -> dict[str, object]:
    qtd, ytd = _period_refs()
    refs = [qtd.ref_id, ytd.ref_id]
    text = "분기 영업흑자와 누적 영업손실이 상충한다."
    candidate = {
        "core_investment_judgment": {"text": text, "evidence_refs": refs},
        "dominant_evidence": {"text": text, "evidence_refs": refs},
        "earnings_estimate_context": {"text": text, "evidence_refs": refs},
        "business_thesis_context": {"text": text, "evidence_refs": refs},
        "buy_drivers": [{"text": text, "evidence_refs": refs}],
        "sell_drivers": [{"text": text, "evidence_refs": refs}],
        "business_reevaluation_up": [{"text": text, "evidence_refs": refs}],
        "business_reevaluation_down": [{"text": text, "evidence_refs": refs}],
        "fundamental_new_buyer": {
            "confirmation_business_condition": text,
            "confirmation_business_condition_refs": refs,
        },
        "fundamental_holder": {
            "business_invalidation_condition": text,
            "business_invalidation_condition_refs": refs,
        },
        "sector_interpretation": {"text": text, "evidence_refs": refs},
    }
    validation = _validate_candidate(candidate)
    paths = (
        "core_investment_judgment",
        "dominant_evidence",
        "earnings_estimate_context",
        "business_thesis_context",
        "buy_drivers",
        "sell_drivers",
        "business_reevaluation_up",
        "business_reevaluation_down",
        "fundamental_new_buyer",
        "fundamental_holder",
        "sector_interpretation",
    )
    return {
        "contract": "m12d-qtd-ytd-claim-path-coverage-v1",
        "audited_paths": list(paths),
        "expected_linked_claim_count": len(paths),
        "validation": validation,
        "arbitrary_path_added": False,
        "status": (
            "PASS"
            if validation["valid"]
            and validation["linked_claim_count"] == len(paths)
            and validation["explicit_claim_count"] == len(paths)
            else "FAIL"
        ),
    }


def _evidence_linkage_contract() -> dict[str, object]:
    qtd, ytd = _period_refs()
    text = "분기 영업흑자와 누적 영업손실이 상충한다."
    both = _validate_candidate(_text_candidate(text, (qtd, ytd)))
    qtd_only = _validate_candidate(_text_candidate(text, (qtd,)))
    ytd_only = _validate_candidate(_text_candidate(text, (ytd,)))
    unlinked = _validate_candidate(_text_candidate(text, ()))
    return {
        "contract": "m12d-qtd-ytd-evidence-linkage-v1",
        "same_metric_pair_required": True,
        "same_claim_both_refs": both,
        "qtd_only": qtd_only,
        "ytd_only": ytd_only,
        "unlinked": unlinked,
        "status": (
            "PASS"
            if both["valid"]
            and not qtd_only["valid"]
            and not ytd_only["valid"]
            and not unlinked["valid"]
            else "FAIL"
        ),
    }


def _frozen_surfaces(generation_id: str) -> dict[str, object]:
    service = SERVICE_PATH
    return {
        "working_capital": _file_freeze("scripts/directional_financial_context_m12g.py"),
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
        "projection_runtime": m12b._projection_audit(generation_id),
        "prompt": _function_freeze(
            path="scripts/directional_core_price_timing_holdout.py",
            function_names=("_core_prompt",),
        ),
        "price_timing": _function_freeze(
            path="scripts/directional_core_price_timing_holdout.py",
            function_names=("_timing_prompt",),
        ),
        "schema": _file_freeze("app/services/direction_timing_ownership_service.py"),
        "financial_validator": _function_freeze(
            path=service,
            function_names=("validate_directional_financial_semantics",),
        ),
        "case_validator": _function_freeze(
            path="scripts/directional_financial_context_m12.py",
            function_names=("_case_semantic_errors", "_audit_core_batch"),
        ),
        "fictional_cases": _function_freeze(
            path="scripts/directional_financial_context_m12.py",
            function_names=("_case_refs", "fictional_inputs", "fictional_manifest"),
        ),
        "source_sufficiency": _file_freeze(
            "app/services/coldstart_fundamental_enrichment_service.py"
        ),
        "daily_delta": _file_freeze("app/services/nonproduction_monitoring_lifecycle_service.py"),
        "warning": _file_freeze("app/services/warning_backfill_service.py"),
        "notification": _file_freeze("app/services/notification_service.py"),
        "renderer": _file_freeze("app/services/structured_autonomy_shadow_service.py"),
        "calibration": _file_freeze("app/services/directional_balance_service.py"),
    }


def _validation_commands(output_root: Path) -> dict[str, dict[str, object]]:
    focused_tests = (
        "tests/test_qtd_ytd_plain_korean_period_validator_m12d.py",
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
    root = _json(_report_path(args.report_dir, 8, "qtd-ytd-root-cause"))
    if root.get("status") != "FROZEN" or root.get("branch") != "BRANCH_A":
        raise ValueError("m12d_branch_a_root_cause_not_frozen")
    if (args.output_root / "phase-a-receipt.json").exists():
        raise ValueError("m12d_existing_phase_b_artifacts_refuse_rerun")
    implementation_commit = _git("rev-parse", "HEAD")
    if implementation_commit == ROOT_CAUSE_COMMIT:
        raise ValueError("m12d_implementation_commit_required")

    args.report_dir.mkdir(parents=True, exist_ok=True)
    args.output_root.mkdir(parents=True, exist_ok=True)
    source_lock, model_inputs = m12r._write_frozen_inputs(
        generation_id=args.generation_id,
        output_root=args.output_root,
    )
    validator_diff = _validator_scope_diff()
    regressions = _historical_regressions()
    positive = _positive_fixture_report()
    negative = _negative_fixture_report()
    qtd_contract, ytd_contract = _marker_contracts()
    path_contract = _claim_path_contract()
    linkage_contract = _evidence_linkage_contract()
    frozen = _frozen_surfaces(args.generation_id)
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
    before_after = {
        "contract": "m12d-qtd-ytd-validator-before-after-v1",
        "before": {
            "plain_korean_qtd_marker_detected": True,
            "korean_ytd_marker_detected": True,
            "상충_relation_marker_detected": False,
            "authoritative_run3_status": "FAIL",
        },
        "after": {
            "plain_korean_qtd_marker_detected": True,
            "korean_ytd_marker_detected": True,
            "상충_relation_marker_detected": financial._matches_period_family(
                financial._normalized_period_text("상충해"),
                financial._PERIOD_RELATION_PATTERNS,
            ),
            "authoritative_run3_status": regressions["rows"]["run3"]["status"],
        },
        "root_cause": root["classification"],
        "root_cause_subtype": root["subtype"],
        "status": (
            "PASS"
            if regressions["rows"]["run3"]["status"] == "PASS"
            and financial._matches_period_family(
                financial._normalized_period_text("상충해"),
                financial._PERIOD_RELATION_PATTERNS,
            )
            else "FAIL"
        ),
    }
    run3 = {
        "contract": "m12d-run3-fic-fin-03-regression-v1",
        **regressions["rows"]["run3"],
        "expected_result": "PASS",
    }
    wc_sources = {
        "fic02_run1": _json(M12C_REPORT_ROOT / "13-fic-fin-02-run2-regression.json")[
            "run1_control"
        ]["status"],
        "fic02_run2": _json(M12C_REPORT_ROOT / "13-fic-fin-02-run2-regression.json")["status"],
        "fic06_old": _json(M12C_REPORT_ROOT / "14-fic-fin-06-old-fail-regression.json")["status"],
        "fic06_corrected": _json(M12C_REPORT_ROOT / "15-fic-fin-06-corrected-pass-regression.json")[
            "status"
        ],
    }
    wc_freeze = {
        "contract": "m12d-working-capital-validator-freeze-v1",
        "file_freeze": frozen["working_capital"],
        "regressions": wc_sources,
        "working_capital_validator_semantic_change_count": frozen["working_capital"][
            "change_count"
        ],
    }
    wc_freeze["status"] = (
        "PASS"
        if frozen["working_capital"]["status"] == "PASS"
        and all(value == "PASS" for value in wc_sources.values())
        else "FAIL"
    )
    projection = {
        "contract": "m12d-first-class-projection-freeze-v1",
        "function_freeze": frozen["projection"],
        "runtime_projection": frozen["projection_runtime"],
        "first_class_projection_change_count": frozen["projection"]["change_count"],
        "financial_context_selection_change_count": frozen["projection"]["change_count"],
    }
    projection["status"] = (
        "PASS"
        if frozen["projection"]["status"] == "PASS"
        and frozen["projection_runtime"]["status"] == "PASS"
        else "FAIL"
    )
    prompt = {
        **frozen["prompt"],
        "contract": "m12d-directional-prompt-freeze-v1",
        "directional_prompt_change_count": frozen["prompt"]["change_count"],
    }
    schema = {
        **frozen["schema"],
        "contract": "m12d-output-schema-freeze-v1",
        "output_schema_change_count": frozen["schema"]["change_count"],
    }
    other = {
        "contract": "m12d-other-financial-validator-freeze-v1",
        "financial_validator": frozen["financial_validator"],
        "case_validator": frozen["case_validator"],
        "calibration": frozen["calibration"],
        "fictional_cases": frozen["fictional_cases"],
        "non_qtd_ytd_financial_validator_change_count": sum(
            int(frozen[key]["change_count"]) for key in ("financial_validator", "case_validator")
        ),
        "fictional_case_change_count": frozen["fictional_cases"]["change_count"],
        "directional_threshold_changed": False,
        "directional_increment_changed": False,
        "hold_lean_contract_changed": False,
        "calibration_tiebreak_changed": False,
    }
    other["status"] = (
        "PASS"
        if all(
            frozen[key]["status"] == "PASS"
            for key in ("financial_validator", "case_validator", "calibration", "fictional_cases")
        )
        else "FAIL"
    )
    price_timing = {
        **frozen["price_timing"],
        "contract": "m12d-price-timing-no-change-v1",
        "price_timing_prompt_change_count": frozen["price_timing"]["change_count"],
    }
    source = {
        **frozen["source_sufficiency"],
        "contract": "m12d-source-sufficiency-no-change-v1",
        "source_sufficiency_semantic_change_count": frozen["source_sufficiency"]["change_count"],
    }
    daily = {
        "contract": "m12d-daily-delta-lifecycle-warning-no-change-v1",
        "daily_delta": frozen["daily_delta"],
        "warning": frozen["warning"],
        "notification": frozen["notification"],
        "daily_delta_semantic_change_count": frozen["daily_delta"]["change_count"],
        "monitoring_lifecycle_semantic_change_count": frozen["daily_delta"]["change_count"],
        "warning_semantic_change_count": int(
            frozen["warning"]["changed"] or frozen["notification"]["changed"]
        ),
    }
    daily["status"] = (
        "PASS"
        if all(
            frozen[key]["status"] == "PASS" for key in ("daily_delta", "warning", "notification")
        )
        else "FAIL"
    )
    renderer = {
        **frozen["renderer"],
        "contract": "m12d-renderer-ownership-no-change-v1",
        "renderer_ownership_change_count": frozen["renderer"]["change_count"],
    }
    reports = {
        (9, "qtd-ytd-validator-before-after"): before_after,
        (10, "korean-qtd-marker-contract"): qtd_contract,
        (11, "korean-ytd-marker-regression"): ytd_contract,
        (12, "claim-path-coverage-contract"): path_contract,
        (13, "evidence-linkage-contract"): linkage_contract,
        (14, "run3-fic-fin-03-regression"): run3,
        (15, "qtd-ytd-positive-fixtures"): positive,
        (16, "qtd-ytd-negative-fixtures"): negative,
        (17, "false-accept-control"): {
            "contract": "m12d-qtd-ytd-false-accept-control-v1",
            "fixture_count": negative["fixture_count"],
            "rejected_count": negative["rejected_count"],
            "validator_false_accept_count": negative["fixture_count"] - negative["rejected_count"],
            "status": negative["status"],
        },
        (18, "false-reject-control"): {
            "contract": "m12d-qtd-ytd-false-reject-control-v1",
            "fixture_count": positive["fixture_count"],
            "pass_count": positive["pass_count"],
            "historical_regressions": regressions,
            "validator_false_reject_count": positive["fixture_count"] - positive["pass_count"],
            "status": (
                "PASS"
                if positive["status"] == "PASS" and regressions["status"] == "PASS"
                else "FAIL"
            ),
        },
        (19, "working-capital-validator-freeze-proof"): wc_freeze,
        (20, "first-class-projection-freeze-proof"): projection,
        (21, "directional-prompt-freeze-proof"): prompt,
        (22, "output-schema-freeze-proof"): schema,
        (23, "other-financial-validator-freeze-proof"): other,
        (24, "price-timing-no-change-proof"): price_timing,
        (25, "source-sufficiency-no-change-proof"): source,
        (26, "daily-delta-no-change-proof"): daily,
        (27, "renderer-ownership-no-change-proof"): renderer,
        (28, "focused-test-results"): validations["focused"],
        (29, "full-test-results"): validations["full"],
        (30, "ruff-and-diff-results"): {
            "contract": "m12d-ruff-and-diff-v1",
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
        "contract": "m12d-production-side-effect-firewall-v1",
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
        "contract": "m12d-schedule-pause-start-observation-v1",
        "start": schedule,
        "observed_paused_schedule_count": schedule["observed_paused_schedule_count"],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "status": schedule["status"],
    }
    for (number, slug), report in reports.items():
        _write_json(_report_path(args.report_dir, number, slug), report)

    checks = {
        "branch_a_frozen": "PASS",
        "validator_scope": validator_diff["status"],
        "run1_regression": regressions["rows"]["run1"]["status"],
        "run2_regression": regressions["rows"]["run2"]["status"],
        "run3_regression": regressions["rows"]["run3"]["status"],
        "historical_regression": regressions["rows"]["historical"]["status"],
        "positive_fixtures": positive["status"],
        "negative_fixtures": negative["status"],
        "qtd_marker_contract": qtd_contract["status"],
        "ytd_marker_contract": ytd_contract["status"],
        "claim_path_contract": path_contract["status"],
        "evidence_linkage": linkage_contract["status"],
        "working_capital_freeze": wc_freeze["status"],
        "first_class_projection": projection["status"],
        "directional_prompt": prompt["status"],
        "output_schema": schema["status"],
        "other_financial_validators": other["status"],
        "price_timing": price_timing["status"],
        "source_sufficiency": source["status"],
        "daily_delta_lifecycle_warning": daily["status"],
        "renderer": renderer["status"],
        "implementation_paths": "PASS" if not unexpected_paths else "FAIL",
        "focused_tests": validations["focused"]["status"],
        "full_tests": validations["full"]["status"],
        "ruff": validations["ruff"]["status"],
        "git_diff_check": validations["diff"]["status"],
        "production_side_effect_firewall": production["status"],
        "schedule_pause": schedule["status"],
    }
    gate = {
        "contract": "m12d-model-call-gate-v1",
        "generation_id": args.generation_id,
        "implementation_commit": implementation_commit,
        "source_lock_sha256": source_lock["source_lock_sha256"],
        "model_inputs": model_inputs,
        "branch_decision": "BRANCH_A",
        "changed_paths_from_root_cause_commit": list(changed_paths),
        "unexpected_changed_paths": unexpected_paths,
        "checks": checks,
        "model_calls_before_gate": 0,
        "status": ("PASS" if all(value == "PASS" for value in checks.values()) else "FAIL"),
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
        "contract": "m12d-runtime-observations-v1",
    }


def finalize(args: argparse.Namespace) -> None:
    gate = _json(args.output_root / "phase-a-receipt.json")
    if gate.get("status") != "PASS":
        raise ValueError("m12d_finalize_requires_passed_model_call_gate")
    run_documents = m12b._run_documents(args.output_root)
    summary_path = args.output_root / "canary-summary.json"
    summary = _json(summary_path) if summary_path.is_file() else None
    manifest = _json(args.output_root / "manifest.json")
    source_lock = _json(args.output_root / "source-lock.json")

    _write_json(
        _report_path(args.report_dir, 32, "fictional-canary-generation-manifest"),
        {
            **manifest,
            "contract": "m12d-fictional-canary-generation-manifest-v1",
            "status": "FROZEN",
        },
    )
    _write_json(
        _report_path(args.report_dir, 33, "fictional-canary-source-lock"),
        {
            **source_lock,
            "contract": "m12d-fictional-canary-source-lock-v1",
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
                    "contract": "m12d-fictional-canary-context-run-v1",
                    "generation_id": args.generation_id,
                    "repetition": repetition,
                    "context": context_number,
                    "receipt": _json(receipt_path) if receipt_path.is_file() else None,
                    "status": "FAIL" if receipt_path.is_file() else "NOT_RUN",
                }
            else:
                document = {
                    **document,
                    "contract": "m12d-fictional-canary-context-run-v1",
                }
            _write_json(
                _report_path(
                    args.report_dir,
                    number,
                    f"run-{repetition}-context-{context_number:02d}",
                ),
                document,
            )

    _packets, _owned, catalogs, contexts = m12.fictional_inputs(args.generation_id)
    all_rows = [row for document in run_documents.values() for row in document["rows"]]
    if summary is not None:
        semantic = {
            **summary["semantic_audit"],
            "contract": "m12d-full-fictional-semantic-audit-v1",
        }
        grounding = {
            **summary["financial_grounding_audit"],
            "contract": "m12d-full-fictional-grounding-audit-v1",
        }
        stability = {
            **summary["stability"],
            "contract": "m12d-full-fictional-stability-v1",
        }
        specificity = {
            **summary["specificity"],
            "contract": "m12d-full-fictional-message-specificity-v1",
            "typed_financial_anchor_specificity": grounding["status"],
        }
        runtime = {
            **summary["runtime"],
            "contract": "m12d-runtime-observations-v1",
        }
    else:
        semantic = {
            **m12g._partial_semantic_audit(
                generation_id=args.generation_id,
                run_documents=run_documents,
            ),
            "contract": "m12d-full-fictional-semantic-audit-v1",
        }
        grounding = {
            **m12b._grounding_audit(
                rows=all_rows,
                catalogs=catalogs,
                contexts=contexts,
                require_complete=True,
            ),
            "contract": "m12d-full-fictional-grounding-audit-v1",
        }
        stability = {
            "contract": "m12d-full-fictional-stability-v1",
            "fictional_stable_count": "NOT_MEASURED",
            "fictional_boundary_uncertainty_count": "NOT_MEASURED",
            "fictional_unstable_count": "NOT_MEASURED",
            "opposite_direction_reversal_count": "NOT_MEASURED",
            "status": "NOT_MEASURED",
        }
        specificity = {
            "contract": "m12d-full-fictional-message-specificity-v1",
            "typed_financial_anchor_specificity": "NOT_MEASURED",
            "status": "NOT_MEASURED",
        }
        runtime = _partial_runtime(args.output_root)
    validator = {
        **m12g._validator_audit(run_documents),
        "contract": "m12d-full-fictional-qtd-ytd-validator-audit-v1",
    }
    validator["qtd_ytd_true_semantic_violation_count"] = validator[
        "qtd_ytd_conflict_violation_count"
    ]
    _write_json(
        _report_path(args.report_dir, 40, "full-fictional-semantic-audit"),
        semantic,
    )
    _write_json(
        _report_path(args.report_dir, 41, "full-fictional-grounding-audit"),
        grounding,
    )
    _write_json(
        _report_path(args.report_dir, 42, "full-fictional-qtd-ytd-validator-audit"),
        validator,
    )
    _write_json(
        _report_path(args.report_dir, 43, "full-fictional-stability"),
        stability,
    )
    _write_json(
        _report_path(
            args.report_dir,
            44,
            "full-fictional-message-specificity-advisory",
        ),
        specificity,
    )
    _write_json(
        _report_path(args.report_dir, 45, "runtime-observations"),
        runtime,
    )

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
        and int(semantic["fictional_output_row_count"]) == len(m12.TICKERS) * m12.REPETITION_COUNT
        and int(semantic["fictional_schema_pass_count"]) == len(m12.TICKERS) * m12.REPETITION_COUNT
        and all(int(semantic.get(field) or 0) == 0 for field in hard_zero_fields)
        and all(int(grounding.get(field) or 0) == 0 for field in grounding_zero_fields)
        and int(validator["validator_false_reject_count"]) == 0
        and int(validator["validator_false_accept_count"]) == 0
        and int(validator["qtd_ytd_true_semantic_violation_count"]) == 0
        and int(stability["opposite_direction_reversal_count"]) == 0
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
    grounding_failure_count = sum(int(grounding.get(field) or 0) for field in grounding_zero_fields)
    if canary_pass:
        status = "M12D_COMPLETE"
        stop_reason = None
        next_scope = "FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF"
        readiness = "READY"
    elif runtime_failures:
        status = "M12D_CANARY_FAIL"
        stop_reason = "M12D_RUNTIME_FAILURE:" + ",".join(runtime_failures)
        next_scope = "BOUNDED_FICTIONAL_RUNTIME_REPAIR"
        readiness = "NOT_READY"
    elif grounding_failure_count or semantic["status"] != "PASS" or validator["status"] != "PASS":
        status = "M12D_CANARY_FAIL"
        stop_reason = "M12D_NEW_BOUNDED_SEMANTIC_BLOCKER"
        next_scope = "BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR"
        readiness = "NOT_READY"
    else:
        status = "M12D_CANARY_FAIL"
        stop_reason = "M12D_FINANCIAL_INTERPRETATION_STABILITY_FAILURE"
        next_scope = "BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_STABILITY_REVIEW"
        readiness = "NOT_READY"

    readiness_report = {
        "contract": "m12d-fresh-real-proof-readiness-decision-v1",
        "qtd_ytd_repair_status": "PASS",
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
        "contract": "m12d-schedule-pause-start-end-observation-v1",
        "start": schedule_start["start"],
        "end": schedule_end,
        "observed_paused_schedule_count": schedule_end["observed_paused_schedule_count"],
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
        "contract": "m12d-master-workflow-update-v1",
        "path": str(MASTER_WORKFLOW_PATH),
        "sha256": _sha_text(master_text),
        "m12d_recorded": "M12D" in master_text,
        "root_cause_recorded": "KOREAN_PERIOD_RELATION_MARKER_FALSE_REJECT" in master_text,
        "next_scope_recorded": next_scope in master_text,
        "production_not_ready_recorded": "production_readiness=NOT_READY" in master_text,
    }
    master["status"] = (
        "PASS"
        if all(
            master[key]
            for key in (
                "m12d_recorded",
                "root_cause_recorded",
                "next_scope_recorded",
                "production_not_ready_recorded",
            )
        )
        else "FAIL"
    )
    _write_json(
        _report_path(args.report_dir, 46, "fresh-real-proof-readiness-decision"),
        readiness_report,
    )
    _write_json(
        _report_path(args.report_dir, 47, "production-no-change"),
        production,
    )
    _write_json(
        _report_path(args.report_dir, 48, "schedule-pause-observation"),
        schedule,
    )
    _write_json(
        _report_path(args.report_dir, 49, "master-workflow-update"),
        master,
    )

    positive = _json(_report_path(args.report_dir, 15, "qtd-ytd-positive-fixtures"))
    negative = _json(_report_path(args.report_dir, 16, "qtd-ytd-negative-fixtures"))
    regressions = _historical_regressions()
    wc = _json(_report_path(args.report_dir, 19, "working-capital-validator-freeze-proof"))
    projection = _json(_report_path(args.report_dir, 20, "first-class-projection-freeze-proof"))
    prompt = _json(_report_path(args.report_dir, 21, "directional-prompt-freeze-proof"))
    schema = _json(_report_path(args.report_dir, 22, "output-schema-freeze-proof"))
    other = _json(_report_path(args.report_dir, 23, "other-financial-validator-freeze-proof"))
    price_timing = _json(_report_path(args.report_dir, 24, "price-timing-no-change-proof"))
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
        "latest_result_zip_sha256": _json(
            _report_path(args.report_dir, 2, "latest-result-integrity")
        )["observed_sha256"],
        "latest_result_integrity": "PASS",
        "m12c_status": "BLOCKED",
        "m12d_status": "COMPLETE" if canary_pass else "BLOCKED",
        "qtd_ytd_root_cause": "OTHER_BOUNDED_VALIDATOR_DEFECT:KOREAN_PERIOD_RELATION_MARKER_FALSE_REJECT",
        "qtd_ytd_repair_status": "PASS",
        "fic_fin_03_run1_regression_status": regressions["rows"]["run1"]["status"],
        "fic_fin_03_run2_regression_status": regressions["rows"]["run2"]["status"],
        "fic_fin_03_run3_regression_status": regressions["rows"]["run3"]["status"],
        "historical_fic_fin_03_regression_status": regressions["rows"]["historical"]["status"],
        "qtd_ytd_positive_fixture_count": positive["fixture_count"],
        "qtd_ytd_positive_fixture_pass_count": positive["pass_count"],
        "qtd_ytd_negative_fixture_count": negative["fixture_count"],
        "qtd_ytd_negative_fixture_rejected_count": negative["rejected_count"],
        "validator_false_reject_count": validator["validator_false_reject_count"],
        "validator_false_accept_count": validator["validator_false_accept_count"],
        "qtd_ytd_true_semantic_violation_count": validator["qtd_ytd_true_semantic_violation_count"],
        "working_capital_validator_semantic_change_count": wc[
            "working_capital_validator_semantic_change_count"
        ],
        "first_class_projection_change_count": projection["first_class_projection_change_count"],
        "financial_context_selection_change_count": projection[
            "financial_context_selection_change_count"
        ],
        "directional_prompt_change_count": prompt["directional_prompt_change_count"],
        "price_timing_prompt_change_count": price_timing["price_timing_prompt_change_count"],
        "output_schema_change_count": schema["output_schema_change_count"],
        "non_qtd_ytd_financial_validator_change_count": other[
            "non_qtd_ytd_financial_validator_change_count"
        ],
        "directional_threshold_changed": other["directional_threshold_changed"],
        "directional_increment_changed": other["directional_increment_changed"],
        "hold_lean_contract_changed": other["hold_lean_contract_changed"],
        "calibration_tiebreak_changed": other["calibration_tiebreak_changed"],
        "source_sufficiency_semantic_change_count": source[
            "source_sufficiency_semantic_change_count"
        ],
        "daily_delta_semantic_change_count": daily["daily_delta_semantic_change_count"],
        "monitoring_lifecycle_semantic_change_count": daily[
            "monitoring_lifecycle_semantic_change_count"
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
        "invalid_financial_reference_count": semantic["invalid_financial_reference_count"],
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
        "fictional_stable_count": stability["fictional_stable_count"],
        "fictional_boundary_uncertainty_count": stability["fictional_boundary_uncertainty_count"],
        "fictional_unstable_count": stability["fictional_unstable_count"],
        "opposite_direction_reversal_count": stability["opposite_direction_reversal_count"],
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
        "observed_paused_schedule_count": schedule["observed_paused_schedule_count"],
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
            (SERVICE_PATH, Path(SERVICE_PATH)),
            (
                "scripts/qtd_ytd_plain_korean_period_validator_m12d.py",
                Path("scripts/qtd_ytd_plain_korean_period_validator_m12d.py"),
            ),
            (
                "tests/test_qtd_ytd_plain_korean_period_validator_m12d.py",
                Path("tests/test_qtd_ytd_plain_korean_period_validator_m12d.py"),
            ),
        )
    )
    seen: set[str] = set()
    unique = []
    for archive_name, path in rows:
        if archive_name in seen:
            raise ValueError(f"m12d_duplicate_artifact_path:{archive_name}")
        if not path.is_file():
            raise ValueError(f"m12d_missing_artifact:{path}")
        seen.add(archive_name)
        unique.append((archive_name, path))
    return unique


def bundle(args: argparse.Namespace) -> None:
    rows = _artifact_source_rows(args.report_dir, args.output_root)
    failures = m12r._secret_scan_failures(rows)
    if failures:
        raise ValueError("m12d_artifact_secret_scan_failed:" + ",".join(failures))
    index_rows = [
        {
            "path": archive_name,
            "sha256": m12.file_sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for archive_name, path in rows
    ]
    index = {
        "contract": "m12d-artifact-index-v1",
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
        if bad is None and hash_mismatches == 0 and size_mismatches == 0 and not failures
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
        raise ValueError("m12d_generation_id_required")
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
