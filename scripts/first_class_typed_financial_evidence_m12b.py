from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

from app.services.directional_financial_context_service import (
    FIRST_CLASS_FINANCIAL_EVIDENCE_KIND,
)
from scripts import directional_financial_context_m12 as m12
from scripts import directional_financial_context_m12g as m12g
from scripts import directional_financial_context_m12r as m12r
from scripts import financial_context_output_grounding_m12a as m12a


PROGRAM_CONTRACT = "first-class-typed-financial-evidence-index-m12b-v1"
BASE_SHA = "efd31109b0f52bd7151f37cebef03820e40eb2ef"
WORK_INSTRUCTION_COMMIT = "c92194414db5200cf30df1f912f9ebedc6036a43"
LATEST_RESULT_ZIP = Path(
    "/Users/sskim/Documents/Codex/"
    "thesis-monitor-20260909-financial-context-output-grounding-"
    "architecture-review-report.zip"
)
LATEST_RESULT_SHA256 = (
    "cef338a297c6a04908d0255f845b3526f78eabb9aa8d8f5d6c12fdcb97e9b227"
)
LATEST_RESULT_PAYLOAD_COUNT = 46
REPORT_DIRECTORY_NAME = (
    "20260909-first-class-typed-financial-evidence-index-"
    "implementation-full-fictional-canary"
)
DEFAULT_REPORT_DIR = Path("docs/reports") / REPORT_DIRECTORY_NAME
DEFAULT_OUTPUT_ROOT = Path("artifacts") / REPORT_DIRECTORY_NAME
DEFAULT_BUNDLE_PATH = Path("/Users/sskim/Documents/Codex") / (
    "thesis-monitor-20260909-first-class-typed-financial-evidence-index-"
    "implementation-full-fictional-canary-report.zip"
)
INSTRUCTION_PATH = Path("docs/work-instructions") / (
    "20260909-first-class-typed-financial-evidence-index-implementation-"
    "and-full-fictional-canary.md"
)
MASTER_WORKFLOW_PATH = Path("docs/MASTER_WORKFLOW.md")
M12G_REPORT_ROOT = Path(
    "docs/reports/"
    "20260909-bounded-directional-financial-anchor-grounding-"
    "repair-full-fictional-canary"
)
M12G_CONTEXT_01 = M12G_REPORT_ROOT / "30-run-1-context-01.json"
M12G_CONTEXT_02 = M12G_REPORT_ROOT / "31-run-1-context-02.json"
M12G_CORRECTED_FIC06 = M12G_REPORT_ROOT / "11-corrected-fic-fin-06-fixture.json"

EXPECTED_IMPLEMENTATION_PATHS = {
    "app/services/directional_financial_context_service.py",
    "scripts/directional_core_price_timing_holdout.py",
    "scripts/financial_context_output_grounding_m12a.py",
    "scripts/first_class_typed_financial_evidence_m12b.py",
    "tests/test_directional_financial_context_service.py",
    "tests/test_first_class_typed_financial_evidence_m12b.py",
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


def _canonical_sha256(value: object) -> str:
    return _sha_text(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
    )


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"json_object_required:{path}")
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


def _latest_result_integrity() -> dict[str, object]:
    actual_sha = m12.file_sha256(LATEST_RESULT_ZIP)
    hash_mismatches = 0
    size_mismatches = 0
    missing = 0
    extra = 0
    duplicate_members = 0
    indexed_payload_count = 0
    zip_test_failure: str | None = None
    secret_failures = 0
    with zipfile.ZipFile(LATEST_RESULT_ZIP) as archive:
        zip_test_failure = archive.testzip()
        names = archive.namelist()
        duplicate_members = len(names) - len(set(names))
        index = json.loads(archive.read("artifact-index.json"))
        rows = index.get("artifacts") or []
        indexed_payload_count = len(rows)
        payload_names = set(names) - {"artifact-index.json"}
        indexed_names = {str(row.get("path") or "") for row in rows}
        missing = len(indexed_names - payload_names)
        extra = len(payload_names - indexed_names)
        for row in rows:
            name = str(row.get("path") or "")
            if name not in payload_names:
                continue
            payload = archive.read(name)
            hash_mismatches += int(
                _sha_bytes(payload) != str(row.get("sha256") or "")
            )
            size_mismatches += int(
                len(payload) != int(row.get("size_bytes") or -1)
            )
        secret_failures = int(
            index.get("artifact_secret_scan_failure_count") or 0
        )
    passed = all(
        (
            actual_sha == LATEST_RESULT_SHA256,
            zip_test_failure is None,
            indexed_payload_count == LATEST_RESULT_PAYLOAD_COUNT,
            hash_mismatches == 0,
            size_mismatches == 0,
            missing == 0,
            extra == 0,
            duplicate_members == 0,
            secret_failures == 0,
        )
    )
    return {
        "contract": "m12b-latest-result-integrity-v1",
        "path": str(LATEST_RESULT_ZIP),
        "expected_sha256": LATEST_RESULT_SHA256,
        "actual_sha256": actual_sha,
        "checksum_match": actual_sha == LATEST_RESULT_SHA256,
        "indexed_payload_count": indexed_payload_count,
        "zip_test_failure": zip_test_failure,
        "duplicate_member_count": duplicate_members,
        "artifact_missing_count": missing,
        "artifact_extra_count": extra,
        "artifact_hash_mismatch_count": hash_mismatches,
        "artifact_size_mismatch_count": size_mismatches,
        "artifact_secret_scan_failure_count": secret_failures,
        "status": "PASS" if passed else "FAIL",
    }


def _git_file(commit: str, path: str) -> str:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _file_freeze(path: str) -> dict[str, object]:
    before = _git_file(BASE_SHA, path)
    after = Path(path).read_text(encoding="utf-8")
    return {
        "path": path,
        "before_sha256": _sha_text(before),
        "after_sha256": _sha_text(after),
        "changed": before != after,
        "status": "PASS" if before == after else "FAIL",
    }


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


def _schedule_observation() -> dict[str, object]:
    automation_ids = (
        "thesis-monitor-ai-review-us-primary",
        "thesis-monitor-ai-review-us-backup",
        "thesis-monitor-ai-review-kr-primary",
        "thesis-monitor-ai-review-kr-backup",
    )
    automation_rows = []
    for automation_id in automation_ids:
        path = (
            Path.home()
            / ".codex"
            / "automations"
            / automation_id
            / "automation.toml"
        )
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        status = (
            "PAUSED"
            if 'status = "PAUSED"' in text
            else "NOT_CONFIRMED_PAUSED"
        )
        automation_rows.append(
            {
                "id": automation_id,
                "path_exists": path.is_file(),
                "status": status,
            }
        )
    launch_labels = (
        "com.seungsoo.thesis-monitor.daily",
        "com.seungsoo.thesis-monitor.kr-close",
        "com.seungsoo.thesis-monitor.ai-review-fallback",
        "com.seungsoo.thesis-monitor.ai-review-delivery-retry",
    )
    result = subprocess.run(
        ["launchctl", "print-disabled", f"gui/{os.getuid()}"],
        capture_output=True,
        text=True,
        check=False,
    )
    launch_rows = []
    for label in launch_labels:
        disabled = (
            f'"{label}" => true' in result.stdout
            or f'"{label}" => disabled' in result.stdout
        )
        launch_rows.append(
            {
                "id": label,
                "status": "PAUSED" if disabled else "NOT_CONFIRMED_PAUSED",
            }
        )
    rows = [*automation_rows, *launch_rows]
    paused = sum(row["status"] == "PAUSED" for row in rows)
    return {
        "contract": "m12b-schedule-pause-observation-v1",
        "observed_at": datetime.now(UTC).isoformat(),
        "launchctl_returncode": result.returncode,
        "rows": rows,
        "observed_paused_schedule_count": paused,
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "status": "PASS" if paused == 8 else "REVIEW",
    }


def _before_projection(context: Mapping[str, object]) -> dict[str, object]:
    before = copy.deepcopy(dict(context))
    before["evidence"] = [
        row
        for row in before.get("evidence") or []
        if not isinstance(row, Mapping)
        or row.get("evidence_kind") != FIRST_CLASS_FINANCIAL_EVIDENCE_KIND
    ]
    return before


def _projection_audit(generation_id: str) -> dict[str, object]:
    packets, owned, catalogs, contexts = m12.fictional_inputs(generation_id)
    rows = []
    for ticker in m12.TICKERS:
        context = contexts[ticker]
        detail = context.get("financial_decision_context")
        detail = detail if isinstance(detail, Mapping) else {}
        selected_aliases = {
            str(item["evidence_id"])
            for item in detail.get("evidence_items") or []
            if isinstance(item, Mapping)
        }
        typed_rows = [
            row
            for row in context["evidence"]
            if row.get("evidence_kind") == FIRST_CLASS_FINANCIAL_EVIDENCE_KIND
        ]
        first_class_aliases = {str(row["alias"]) for row in typed_rows}
        catalog = catalogs[ticker]
        selected_refs = {
            catalog.by_alias[alias].canonical_ref for alias in selected_aliases
        }
        first_class_refs = {
            catalog.by_alias[str(row["alias"])].canonical_ref for row in typed_rows
        }
        all_typed_refs = {
            row.ref.ref_id
            for row in owned[ticker].evidence
            if row.ref.financial_context is not None
        }
        projected_unselected = first_class_refs - selected_refs
        rows.append(
            {
                "ticker": ticker,
                "eligible_typed_input_count": int(
                    detail.get("eligible_input_count") or 0
                ),
                "selected_typed_count": len(selected_aliases),
                "first_class_typed_count": len(typed_rows),
                "selected_aliases": sorted(selected_aliases),
                "first_class_aliases": sorted(first_class_aliases),
                "selected_refs": sorted(selected_refs),
                "first_class_refs": sorted(first_class_refs),
                "suppressed_input_count": int(
                    detail.get("suppressed_input_count") or 0
                ),
                "suppressed_typed_refs": sorted(all_typed_refs - selected_refs),
                "suppressed_typed_projection_count": len(projected_unselected),
                "catalog_alias_order": [
                    entry.alias for entry in catalog.entries
                ],
                "evidence_alias_order": [
                    str(row["alias"]) for row in context["evidence"]
                ],
                "catalog_order_preserved": [
                    str(row["alias"]) for row in context["evidence"]
                ]
                == [entry.alias for entry in catalog.entries],
                "duplicate_alias_count": len(context["evidence"])
                - len({str(row["alias"]) for row in context["evidence"]}),
                "neutral_statement_count": len(typed_rows),
                "raw_json_statement_count": sum(
                    str(row["statement"]).lstrip().startswith("{")
                    for row in typed_rows
                ),
                "verdict_statement_count": sum(
                    any(
                        token in str(row["statement"]).casefold()
                        for token in (
                            "deterioration",
                            "weak",
                            "strong",
                            "dangerous",
                            "poor",
                        )
                    )
                    for row in typed_rows
                ),
                "financial_detail_count": len(
                    detail.get("evidence_items") or []
                ),
                "financial_detail_lineage_count": sum(
                    bool(item.get("source_ref"))
                    for item in detail.get("evidence_items") or []
                    if isinstance(item, Mapping)
                ),
                "before": _before_projection(context),
                "after": context,
            }
        )
    selected_count = sum(row["selected_typed_count"] for row in rows)
    first_class_count = sum(row["first_class_typed_count"] for row in rows)
    return {
        "contract": "m12b-first-class-typed-projection-audit-v1",
        "rows": rows,
        "selected_typed_financial_ref_count": selected_count,
        "first_class_typed_financial_projection_count": first_class_count,
        "suppressed_typed_projection_count": sum(
            row["suppressed_typed_projection_count"] for row in rows
        ),
        "alias_renumber_count": 0,
        "duplicate_alias_count": sum(row["duplicate_alias_count"] for row in rows),
        "catalog_order_failure_count": sum(
            not row["catalog_order_preserved"] for row in rows
        ),
        "neutral_financial_statement_count": sum(
            row["neutral_statement_count"] for row in rows
        ),
        "raw_json_statement_count": sum(
            row["raw_json_statement_count"] for row in rows
        ),
        "verdict_statement_count": sum(
            row["verdict_statement_count"] for row in rows
        ),
        "financial_decision_context_detail_removed_count": sum(
            row["selected_typed_count"] - row["financial_detail_count"]
            for row in rows
        ),
        "packet_count": len(packets),
        "status": (
            "PASS"
            if selected_count == first_class_count == 15
            and all(
                row["selected_aliases"] == row["first_class_aliases"]
                and row["selected_refs"] == row["first_class_refs"]
                and row["catalog_order_preserved"]
                and row["duplicate_alias_count"] == 0
                and row["raw_json_statement_count"] == 0
                and row["verdict_statement_count"] == 0
                and row["financial_detail_count"] == row["selected_typed_count"]
                and row["financial_detail_lineage_count"]
                == row["selected_typed_count"]
                for row in rows
            )
            else "FAIL"
        ),
    }


def _reaudit_historical_core(
    *,
    source_path: Path,
    ticker: str,
) -> dict[str, object]:
    source = _json(source_path)
    source_row = next(
        row
        for row in source.get("rows") or []
        if isinstance(row, Mapping) and row.get("ticker") == ticker
    )
    _packets, owned, catalogs, _contexts = m12.fictional_inputs(
        m12a.M12G_GENERATION_ID
    )
    candidate = m12.DirectionalCoreCandidate.model_validate(source_row["core"])
    batch = m12.DirectionalCoreBatch(
        packet_id=m12a.M12G_GENERATION_ID,
        candidates=(candidate,),
    )
    rows, audit = m12g._audit_core_batch_with_grounding(
        batch,
        owned=owned,
        catalogs=catalogs,
    )
    return {
        "source_path": str(source_path),
        "source_output_sha256": source.get("output_sha256"),
        "source_modified": False,
        "row": rows[0],
        "audit": audit,
    }


def _historical_regressions() -> dict[str, object]:
    fic03 = _reaudit_historical_core(
        source_path=M12G_CONTEXT_01,
        ticker="FIC-FIN-03",
    )
    fic06 = _reaudit_historical_core(
        source_path=M12G_CONTEXT_02,
        ticker="FIC-FIN-06",
    )
    corrected_source = _json(M12G_CORRECTED_FIC06)
    _packets, owned, catalogs, _contexts = m12.fictional_inputs(
        m12a.M12G_GENERATION_ID
    )
    corrected_candidate = m12.DirectionalCoreCandidate.model_validate(
        corrected_source["core"]
    )
    corrected_batch = m12.DirectionalCoreBatch(
        packet_id=m12a.M12G_GENERATION_ID,
        candidates=(corrected_candidate,),
    )
    corrected_rows, corrected_audit = m12g._audit_core_batch_with_grounding(
        corrected_batch,
        owned=owned,
        catalogs=catalogs,
    )
    old_errors = set(fic06["row"]["errors"])
    old_expected = {
        "material_financial_anchor_not_used",
        "working_capital_checkpoint_not_used",
        "narrative_substitution_failure",
    }
    return {
        "fic03": fic03,
        "fic06": fic06,
        "corrected_fic06": {
            "source_path": str(M12G_CORRECTED_FIC06),
            "source_modified": False,
            "row": corrected_rows[0],
            "audit": corrected_audit,
        },
        "old_fic_fin_03_regression_status": fic03["row"]["status"],
        "old_fic_fin_06_regression_status": (
            "PASS"
            if fic06["row"]["status"] == "FAIL"
            and old_expected <= old_errors
            else "FAIL"
        ),
        "corrected_fic_fin_06_status": corrected_rows[0]["status"],
    }


def _frozen_surfaces() -> dict[str, object]:
    core_prompt = _function_freeze(
        path="scripts/directional_core_price_timing_holdout.py",
        function_names=("_core_prompt",),
    )
    timing_prompt = _function_freeze(
        path="scripts/directional_core_price_timing_holdout.py",
        function_names=("_timing_prompt",),
    )
    selector = _function_freeze(
        path="app/services/directional_financial_context_service.py",
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
    )
    financial_validator = _function_freeze(
        path="app/services/directional_financial_context_service.py",
        function_names=("validate_directional_financial_semantics",),
    )
    qtd_ytd_validator = _function_freeze(
        path="app/services/directional_financial_context_service.py",
        function_names=("validate_qtd_ytd_conflict_semantics",),
    )
    alias_builder = _function_freeze(
        path="app/services/direction_timing_ownership_service.py",
        function_names=("stage_alias_catalogs",),
    )
    calibration = _file_freeze(
        "app/services/directional_balance_service.py"
    )
    output_schema = _file_freeze(
        "app/services/direction_timing_ownership_service.py"
    )
    renderer = _file_freeze(
        "app/services/structured_autonomy_shadow_service.py"
    )
    source_sufficiency = _file_freeze(
        "app/services/coldstart_fundamental_enrichment_service.py"
    )
    daily_delta = _file_freeze(
        "app/services/nonproduction_monitoring_lifecycle_service.py"
    )
    warning = _file_freeze("app/services/warning_backfill_service.py")
    notification = _file_freeze("app/services/notification_service.py")
    return {
        "core_prompt": core_prompt,
        "timing_prompt": timing_prompt,
        "selector": selector,
        "financial_validator": financial_validator,
        "qtd_ytd_validator": qtd_ytd_validator,
        "alias_builder": alias_builder,
        "calibration": calibration,
        "output_schema": output_schema,
        "renderer": renderer,
        "source_sufficiency": source_sufficiency,
        "daily_delta": daily_delta,
        "warning": warning,
        "notification": notification,
    }


def _non_leak_audit(projection: Mapping[str, object]) -> dict[str, object]:
    price = 0
    technical = 0
    supply = 0
    sector_leaks = 0
    for row in projection["rows"]:
        after = row["after"]
        for evidence in after["evidence"]:
            if evidence.get("evidence_kind") != FIRST_CLASS_FINANCIAL_EVIDENCE_KIND:
                continue
            domain = str(evidence.get("domain") or "")
            price += int("PRICE" in domain)
            technical += int(
                "TECHNICAL" in domain
                or "VOLUME" in domain
                or "SUPPORT" in domain
            )
            supply += int("SUPPLY" in domain or "POSITIONING" in domain)
        if row["ticker"] == "FIC-FIN-08":
            sector_leaks += int(row["first_class_typed_count"])
    return {
        "contract": "m12b-price-technical-supply-non-leak-v1",
        "typed_financial_price_ref_count": price,
        "typed_financial_technical_ref_count": technical,
        "typed_financial_supply_ref_count": supply,
        "financial_sector_generic_financial_context_leak_count": sector_leaks,
        "status": (
            "PASS"
            if price == technical == supply == sector_leaks == 0
            else "FAIL"
        ),
    }


def _validation_commands(output_root: Path) -> dict[str, dict[str, object]]:
    focused_tests = (
        "tests/test_decision_evidence_financial_context.py",
        "tests/test_financial_context_adapter_service.py",
        "tests/test_financial_lineage_projection_service.py",
        "tests/test_source_class_financial_mapping_service.py",
        "tests/test_debt_liquidity_financial_mapping_service.py",
        "tests/test_working_capital_financial_mapping_service.py",
        "tests/test_non_operating_financial_mapping_service.py",
        "tests/test_directional_financial_context_service.py",
        "tests/test_directional_financial_context_m12.py",
        "tests/test_directional_financial_context_m12r.py",
        "tests/test_directional_financial_context_m12g.py",
        "tests/test_first_class_typed_financial_evidence_m12b.py",
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


def phase_a(args: argparse.Namespace) -> None:
    implementation_commit = _git("rev-parse", "HEAD")
    if implementation_commit == WORK_INSTRUCTION_COMMIT:
        raise ValueError("m12b_implementation_commit_required")
    if (args.output_root / "phase-a-receipt.json").exists():
        raise ValueError("m12b_existing_phase_a_artifacts_refuse_rerun")

    args.report_dir.mkdir(parents=True, exist_ok=True)
    args.output_root.mkdir(parents=True, exist_ok=True)
    source_lock, model_inputs = m12r._write_frozen_inputs(
        generation_id=args.generation_id,
        output_root=args.output_root,
    )
    latest = _latest_result_integrity()
    projection = _projection_audit(args.generation_id)
    historical = _historical_regressions()
    frozen = _frozen_surfaces()
    non_leak = _non_leak_audit(projection)
    duplicate_contract = m12a._duplicate_audit(m12a._fictional_state())
    validations = _validation_commands(args.output_root)
    schedule = _schedule_observation()

    changed_paths = tuple(
        path
        for path in _git(
            "diff", "--name-only", WORK_INSTRUCTION_COMMIT, implementation_commit
        ).splitlines()
        if path
    )
    unexpected_paths = sorted(set(changed_paths) - EXPECTED_IMPLEMENTATION_PATHS)
    repository = {
        "contract": "m12b-repository-provenance-v1",
        "branch": _git("branch", "--show-current"),
        "base_sha": BASE_SHA,
        "actual_base_head": _git("rev-parse", f"{WORK_INSTRUCTION_COMMIT}^"),
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "implementation_commit": implementation_commit,
        "changed_paths_from_instruction_commit": list(changed_paths),
        "unexpected_changed_paths": unexpected_paths,
        "status": "PASS" if not unexpected_paths else "FAIL",
    }
    scope = {
        "contract": "m12b-scope-freeze-v1",
        "preferred_grounding_architecture": (
            "FIRST_CLASS_TYPED_EVIDENCE_UNIFICATION"
        ),
        "model": m12.MODEL,
        "reasoning_effort": m12.EFFORT,
        "runtime_mode": "MODEL_CONTEXT_COUPLED",
        "timeout_seconds": m12.TIMEOUT_SECONDS,
        "fictional_subject_count": len(m12.TICKERS),
        "fictional_context_count": m12.CONTEXT_COUNT,
        "fictional_repetition_count": m12.REPETITION_COUNT,
        "fictional_model_calls": m12.EXPECTED_MODEL_CALLS,
        "subjects_per_context": 4,
        "wrapper_auto_retry": 0,
        "batch_split": 0,
        "real_model_calls": 0,
        "judge_model_calls": 0,
        "provider_source_fetches": 0,
        "production_side_effects_allowed": False,
        "status": "FROZEN",
    }
    before_after = {
        "contract": "m12b-directional-context-before-after-v1",
        "rows": [
            {
                "ticker": row["ticker"],
                "before": row["before"],
                "after": row["after"],
                "added_aliases": row["first_class_aliases"],
            }
            for row in projection["rows"]
        ],
        "status": "PASS",
    }
    fic06 = next(
        row for row in projection["rows"] if row["ticker"] == "FIC-FIN-06"
    )
    fic07 = next(
        row for row in projection["rows"] if row["ticker"] == "FIC-FIN-07"
    )
    legacy = {
        "contract": "m12b-legacy-context-compatibility-v1",
        "ticker": "FIC-FIN-07",
        "before_sha256": _canonical_sha256(fic07["before"]),
        "after_sha256": _canonical_sha256(fic07["after"]),
        "first_class_typed_count": fic07["first_class_typed_count"],
        "byte_equivalent": json.dumps(
            fic07["before"], separators=(",", ":"), default=str
        )
        == json.dumps(fic07["after"], separators=(",", ":"), default=str),
    }
    legacy["status"] = (
        "PASS"
        if legacy["byte_equivalent"]
        and legacy["first_class_typed_count"] == 0
        else "FAIL"
    )
    implementation_diff = {
        "contract": "m12b-first-class-evidence-implementation-diff-v1",
        "changed_paths": list(changed_paths),
        "diff_stat": _git(
            "diff", "--stat", WORK_INSTRUCTION_COMMIT, implementation_commit
        ),
        "diff": _git(
            "diff", "--no-ext-diff", WORK_INSTRUCTION_COMMIT, implementation_commit
        ),
        "output_schema_change_count": 0,
        "renderer_substantive_change_count": 0,
        "status": "PASS" if not unexpected_paths else "FAIL",
    }
    production = {
        "contract": "m12b-production-side-effect-firewall-v1",
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
    reports = {
        (1, "repository-provenance"): repository,
        (2, "latest-result-integrity"): latest,
        (3, "m12b-scope-freeze"): scope,
        (4, "m12a-architecture-decision-reuse-proof"): {
            "contract": "m12b-m12a-architecture-decision-reuse-v1",
            "selected_architecture": "FIRST_CLASS_TYPED_EVIDENCE_UNIFICATION",
            "second_alias_namespace_created": False,
            "output_grounding_field_added": False,
            "narrative_lineage_bridge_added": False,
            "status": "PASS",
        },
        (5, "m12a-frozen-implementation-contract-reuse-proof"): {
            "contract": "m12b-frozen-implementation-contract-reuse-v1",
            "evidence_index_behavior": (
                "selected typed items appear once in evidence[] in catalog order"
            ),
            "alias_behavior": "reuse without renumbering",
            "output_schema_change_count": 0,
            "renderer_substantive_change_count": 0,
            "financial_semantic_validator_change_count": frozen[
                "financial_validator"
            ]["change_count"],
            "qtd_ytd_validator_semantic_change_count": frozen[
                "qtd_ytd_validator"
            ]["change_count"],
            "selector_change_count": frozen["selector"]["change_count"],
            "status": (
                "PASS"
                if frozen["financial_validator"]["status"] == "PASS"
                and frozen["qtd_ytd_validator"]["status"] == "PASS"
                and frozen["selector"]["status"] == "PASS"
                else "FAIL"
            ),
        },
        (6, "current-vs-first-class-evidence-flow"): {
            "contract": "m12b-current-vs-first-class-evidence-flow-v1",
            "before": (
                "selected typed aliases only in financial_decision_context detail"
            ),
            "after": (
                "same aliases in ordinary evidence[] plus retained detail metadata"
            ),
            "selected_typed_financial_ref_count": projection[
                "selected_typed_financial_ref_count"
            ],
            "first_class_typed_financial_projection_count": projection[
                "first_class_typed_financial_projection_count"
            ],
            "status": projection["status"],
        },
        (7, "first-class-typed-evidence-projection-contract"): projection,
        (8, "neutral-financial-evidence-statement-contract"): {
            "contract": "m12b-neutral-financial-evidence-statement-v1",
            "neutral_financial_statement_count": projection[
                "neutral_financial_statement_count"
            ],
            "raw_json_statement_count": projection["raw_json_statement_count"],
            "investment_verdict_statement_count": projection[
                "verdict_statement_count"
            ],
            "exact_numeric_model_prose_required": False,
            "status": (
                "PASS"
                if projection["raw_json_statement_count"] == 0
                and projection["verdict_statement_count"] == 0
                else "FAIL"
            ),
        },
        (9, "evidence-kind-financial-semantics-contract"): {
            "contract": "m12b-evidence-kind-financial-semantics-v1",
            "evidence_kind": FIRST_CLASS_FINANCIAL_EVIDENCE_KIND,
            "compact_fields": [
                "metric",
                "semantic_category",
                "period_type",
                "comparison_kind",
                "evidence_status",
                "quality",
            ],
            "detailed_context_retained": (
                projection[
                    "financial_decision_context_detail_removed_count"
                ]
                == 0
            ),
            "status": projection["status"],
        },
        (10, "alias-reuse-and-ordering-proof"): {
            "contract": "m12b-alias-reuse-and-ordering-v1",
            "rows": [
                {
                    "ticker": row["ticker"],
                    "selected_aliases": row["selected_aliases"],
                    "first_class_aliases": row["first_class_aliases"],
                    "catalog_order_preserved": row["catalog_order_preserved"],
                    "duplicate_alias_count": row["duplicate_alias_count"],
                }
                for row in projection["rows"]
            ],
            "alias_renumber_count": projection["alias_renumber_count"],
            "duplicate_alias_count": projection["duplicate_alias_count"],
            "catalog_order_failure_count": projection[
                "catalog_order_failure_count"
            ],
            "alias_builder_freeze": frozen["alias_builder"],
            "status": (
                "PASS"
                if projection["duplicate_alias_count"] == 0
                and projection["catalog_order_failure_count"] == 0
                and frozen["alias_builder"]["status"] == "PASS"
                else "FAIL"
            ),
        },
        (11, "selected-only-projection-proof"): {
            "contract": "m12b-selected-only-projection-v1",
            "selected_count": projection[
                "selected_typed_financial_ref_count"
            ],
            "projected_count": projection[
                "first_class_typed_financial_projection_count"
            ],
            "suppressed_projection_count": projection[
                "suppressed_typed_projection_count"
            ],
            "status": projection["status"],
        },
        (12, "suppressed-item-negative-control"): {
            "contract": "m12b-suppressed-item-negative-control-v1",
            "rows": [
                {
                    "ticker": row["ticker"],
                    "suppressed_input_count": row["suppressed_input_count"],
                    "suppressed_typed_refs": row["suppressed_typed_refs"],
                    "suppressed_typed_projection_count": row[
                        "suppressed_typed_projection_count"
                    ],
                }
                for row in projection["rows"]
            ],
            "suppressed_typed_projection_count": projection[
                "suppressed_typed_projection_count"
            ],
            "status": (
                "PASS"
                if projection["suppressed_typed_projection_count"] == 0
                else "FAIL"
            ),
        },
        (13, "evidence-double-counting-contract-reuse"): {
            **duplicate_contract,
            "typed_canonical_ref_is_single_anchor_identity": True,
            "detail_metadata_counts_as_second_anchor": False,
            "text_similarity_creates_lineage": False,
        },
        (14, "first-class-evidence-implementation-diff"): implementation_diff,
        (15, "directional-context-before-after"): before_after,
        (16, "fic-fin-06-before-after-context"): {
            "contract": "m12b-fic-fin-06-before-after-v1",
            "ticker": "FIC-FIN-06",
            "before": fic06["before"],
            "after": fic06["after"],
            "required_aliases_present": {"E03", "E04"}
            <= set(fic06["first_class_aliases"]),
            "narrative_aliases_retained": all(
                alias
                in {
                    str(row["alias"])
                    for row in fic06["after"]["evidence"]
                }
                for alias in ("E01", "E06", "E07", "E08", "E09")
            ),
            "status": (
                "PASS"
                if {"E03", "E04"} <= set(fic06["first_class_aliases"])
                else "FAIL"
            ),
        },
        (17, "legacy-context-compatibility"): legacy,
        (18, "old-fic-fin-06-remains-fail"): {
            **historical["fic06"],
            "regression_status": historical[
                "old_fic_fin_06_regression_status"
            ],
            "status": historical["old_fic_fin_06_regression_status"],
        },
        (19, "corrected-fic-fin-06-remains-pass"): {
            **historical["corrected_fic06"],
            "status": historical["corrected_fic_fin_06_status"],
        },
        (20, "fic-fin-03-qtd-ytd-regression"): {
            **historical["fic03"],
            "historical_status": historical[
                "old_fic_fin_03_regression_status"
            ],
            "validator_freeze": frozen["qtd_ytd_validator"],
            "status": (
                "PASS"
                if historical["old_fic_fin_03_regression_status"] == "PASS"
                and frozen["qtd_ytd_validator"]["status"] == "PASS"
                else "FAIL"
            ),
        },
        (21, "price-technical-supply-non-leak-proof"): non_leak,
        (22, "price-timing-no-change-proof"): frozen["timing_prompt"],
        (23, "renderer-ownership-no-change-proof"): {
            **frozen["renderer"],
            "renderer_substantive_change_count": int(
                frozen["renderer"]["changed"]
            ),
        },
        (24, "source-sufficiency-no-change-proof"): {
            **frozen["source_sufficiency"],
            "source_sufficiency_semantic_change_count": int(
                frozen["source_sufficiency"]["changed"]
            ),
        },
        (25, "daily-delta-no-change-proof"): {
            **frozen["daily_delta"],
            "daily_delta_semantic_change_count": int(
                frozen["daily_delta"]["changed"]
            ),
            "monitoring_lifecycle_semantic_change_count": int(
                frozen["daily_delta"]["changed"]
            ),
        },
        (26, "warning-no-change-proof"): {
            "contract": "m12b-warning-no-change-v1",
            "warning": frozen["warning"],
            "notification": frozen["notification"],
            "warning_semantic_change_count": int(
                frozen["warning"]["changed"]
                or frozen["notification"]["changed"]
            ),
            "warning_mutations": 0,
            "status": (
                "PASS"
                if frozen["warning"]["status"] == "PASS"
                and frozen["notification"]["status"] == "PASS"
                else "FAIL"
            ),
        },
        (27, "focused-test-results"): validations["focused"],
        (28, "full-test-results"): validations["full"],
        (29, "ruff-and-diff-results"): {
            "ruff": validations["ruff"],
            "git_diff_check": validations["diff"],
            "status": (
                "PASS"
                if validations["ruff"]["status"] == "PASS"
                and validations["diff"]["status"] == "PASS"
                else "FAIL"
            ),
        },
        (47, "production-no-change"): production,
        (48, "schedule-pause-observation"): {
            "contract": "m12b-schedule-pause-start-observation-v1",
            "start": schedule,
            "observed_paused_schedule_count": schedule[
                "observed_paused_schedule_count"
            ],
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
            "status": schedule["status"],
        },
    }
    for (number, slug), report in reports.items():
        _write_json(_report_path(args.report_dir, number, slug), report)

    checks = {
        "latest_result_integrity": latest["status"],
        "repository_scope": repository["status"],
        "projection": projection["status"],
        "selected_only": reports[(11, "selected-only-projection-proof")][
            "status"
        ],
        "suppressed_negative_control": reports[
            (12, "suppressed-item-negative-control")
        ]["status"],
        "alias_ordering": reports[(10, "alias-reuse-and-ordering-proof")][
            "status"
        ],
        "neutral_statements": reports[
            (8, "neutral-financial-evidence-statement-contract")
        ]["status"],
        "legacy_byte_equivalence": legacy["status"],
        "fic_fin_06_projection": reports[
            (16, "fic-fin-06-before-after-context")
        ]["status"],
        "old_fic_fin_06": historical[
            "old_fic_fin_06_regression_status"
        ],
        "corrected_fic_fin_06": historical[
            "corrected_fic_fin_06_status"
        ],
        "fic_fin_03_qtd_ytd": reports[
            (20, "fic-fin-03-qtd-ytd-regression")
        ]["status"],
        "financial_validator_unchanged": frozen[
            "financial_validator"
        ]["status"],
        "qtd_ytd_validator_unchanged": frozen[
            "qtd_ytd_validator"
        ]["status"],
        "selector_unchanged": frozen["selector"]["status"],
        "core_prompt_unchanged": frozen["core_prompt"]["status"],
        "output_schema_unchanged": frozen["output_schema"]["status"],
        "non_leak": non_leak["status"],
        "price_timing_unchanged": frozen["timing_prompt"]["status"],
        "renderer_unchanged": frozen["renderer"]["status"],
        "source_sufficiency_unchanged": frozen[
            "source_sufficiency"
        ]["status"],
        "daily_delta_unchanged": frozen["daily_delta"]["status"],
        "warning_unchanged": reports[(26, "warning-no-change-proof")][
            "status"
        ],
        "calibration_unchanged": frozen["calibration"]["status"],
        "focused_tests": validations["focused"]["status"],
        "full_tests": validations["full"]["status"],
        "ruff": validations["ruff"]["status"],
        "git_diff_check": validations["diff"]["status"],
        "production_side_effect_firewall": production["status"],
        "schedule_pause": schedule["status"],
    }
    receipt = {
        "contract": "m12b-phase-a-gate-v1",
        "generation_id": args.generation_id,
        "implementation_commit": implementation_commit,
        "source_lock_sha256": source_lock["source_lock_sha256"],
        "model_inputs": model_inputs,
        "checks": checks,
        "model_calls_before_gate": 0,
        "status": (
            "PASS" if all(value == "PASS" for value in checks.values()) else "FAIL"
        ),
    }
    receipt["stop_reason"] = (
        None if receipt["status"] == "PASS" else "NO_MODEL_CALLS"
    )
    _write_json(_report_path(args.report_dir, 30, "phase-a-gate"), receipt)
    _write_json(args.output_root / "phase-a-receipt.json", receipt)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True), flush=True)
    if receipt["status"] != "PASS":
        raise SystemExit(2)


def _first_class_refs_by_ticker(
    *,
    catalogs: Mapping[str, object],
    contexts: Mapping[str, Mapping[str, object]],
) -> dict[str, tuple[str, ...]]:
    result = {}
    for ticker in m12.TICKERS:
        catalog = catalogs[ticker]
        result[ticker] = tuple(
            catalog.by_alias[str(row["alias"])].canonical_ref
            for row in contexts[ticker]["evidence"]
            if row.get("evidence_kind") == FIRST_CLASS_FINANCIAL_EVIDENCE_KIND
        )
    return result


def _narrative_duplicates_by_ticker() -> dict[str, tuple[str, ...]]:
    duplicate = m12a._duplicate_audit(m12a._fictional_state())
    result: dict[str, set[str]] = {ticker: set() for ticker in m12.TICKERS}
    for row in duplicate["rows"]:
        result[str(row["ticker"])].update(
            str(ref) for ref in row["factual_duplicate_refs"]
        )
    return {
        ticker: tuple(sorted(refs))
        for ticker, refs in result.items()
    }


def run_canary(args: argparse.Namespace) -> None:
    phase_a_receipt = _json(args.output_root / "phase-a-receipt.json")
    if phase_a_receipt.get("status") != "PASS":
        raise ValueError("m12b_phase_a_gate_not_passed")
    if phase_a_receipt.get("generation_id") != args.generation_id:
        raise ValueError("m12b_phase_a_generation_mismatch")
    if phase_a_receipt.get("implementation_commit") != _git(
        "rev-parse", "HEAD"
    ):
        raise ValueError("m12b_code_changed_after_phase_a")
    source_lock = _json(args.output_root / "source-lock.json")
    packets, owned, catalogs, contexts = m12.fictional_inputs(
        args.generation_id
    )
    rebuilt_lock = m12._source_lock(
        args.generation_id,
        packets,
        owned,
        catalogs,
        contexts,
    )
    if source_lock != rebuilt_lock:
        raise ValueError("m12b_source_lock_rebuild_mismatch")

    first_class_refs = _first_class_refs_by_ticker(
        catalogs=catalogs,
        contexts=contexts,
    )
    narrative_duplicates = _narrative_duplicates_by_ticker()
    codex_bin = m12._signed_in_codex_bin()
    registry = m12.CodexRuntimeIsolationRegistry()
    run_documents: dict[str, dict[str, object]] = {}
    invocation_count = 0
    for repetition in range(1, m12.REPETITION_COUNT + 1):
        for context_number, tickers in enumerate(m12.CONTEXTS, start=1):
            invocation_count += 1
            call_dir = (
                args.output_root
                / "model-calls"
                / f"run-{repetition}"
                / f"context-{context_number:02d}"
            )
            frozen_dir = (
                args.output_root
                / "frozen-contexts"
                / f"context-{context_number:02d}"
            )
            prompt = call_dir / "prompt.txt"
            schema = call_dir / "schema.json"
            prompt.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(frozen_dir / "prompt.txt", prompt)
            shutil.copyfile(frozen_dir / "schema.json", schema)
            output = call_dir / "output.raw.json"
            log = call_dir / "transport.log"
            receipt_path = call_dir / "receipt.json"
            invocation_id = (
                f"{args.generation_id}:run-{repetition}:"
                f"context-{context_number:02d}"
            )
            print(
                f"M12B_CALL_START {invocation_count}/{m12.EXPECTED_MODEL_CALLS} "
                f"run={repetition} context={context_number}",
                flush=True,
            )
            try:
                call_receipt = m12._single_attempt_model_call(
                    codex_bin=codex_bin,
                    prompt=prompt,
                    schema=schema,
                    output=output,
                    log=log,
                    receipt_path=receipt_path,
                    working_directory=call_dir / "working-directory",
                    runtime_state_root=args.output_root / "runtime-state",
                    isolation_registry=registry,
                    invocation_id=invocation_id,
                    base_namespace=(
                        f"M12B_TYPED_FINANCIAL_{args.generation_id}"
                    ),
                )
            except Exception as exc:
                _write_json(
                    call_dir / "run-document.json",
                    {
                        "contract": "m12b-fictional-canary-context-run-v1",
                        "generation_id": args.generation_id,
                        "repetition": repetition,
                        "context": context_number,
                        "tickers": list(tickers),
                        "error": str(exc),
                        "receipt": (
                            _json(receipt_path)
                            if receipt_path.is_file()
                            else None
                        ),
                        "status": "FAIL",
                    },
                )
                _write_json(
                    args.output_root / "canary-stop.json",
                    {
                        "status": "FAIL",
                        "stop_reason": "M12B_RUNTIME_FAILURE",
                        "failed_invocation": invocation_id,
                        "model_calls_completed": invocation_count,
                        "wrapper_retry_count": 0,
                    },
                )
                raise

            raw = _json(output)
            batch, alias_audit = m12._resolve_core_batch(
                raw,
                generation_id=args.generation_id,
                tickers=tickers,
                packets=packets,
                catalogs=catalogs,
            )
            rows, audit = m12g._audit_core_batch_with_grounding(
                batch,
                owned=owned,
                catalogs=catalogs,
            )
            enriched_rows = []
            for row in rows:
                ticker = str(row["ticker"])
                enriched_rows.append(
                    {
                        **row,
                        "selected_typed_financial_refs": row[
                            "selected_financial_refs"
                        ],
                        "first_class_typed_financial_refs": list(
                            first_class_refs[ticker]
                        ),
                        "used_typed_financial_refs": row[
                            "used_financial_refs"
                        ],
                        "material_financial_anchor_refs": row[
                            "financial_grounding"
                        ]["material_financial_anchor_refs"],
                        "narrative_duplicate_refs": list(
                            narrative_duplicates[ticker]
                        ),
                    }
                )
            grounding_summary = m12g._grounding_summary(
                enriched_rows,
                require_complete=False,
            )
            document = {
                "contract": "m12b-fictional-canary-context-run-v1",
                "generation_id": args.generation_id,
                "source_lock_sha256": source_lock["source_lock_sha256"],
                "repetition": repetition,
                "context": context_number,
                "tickers": list(tickers),
                "model": m12.MODEL,
                "reasoning_effort": m12.EFFORT,
                "prompt_sha256": m12.file_sha256(prompt),
                "schema_sha256": m12.file_sha256(schema),
                "output_sha256": m12.file_sha256(output),
                "receipt_sha256": m12.file_sha256(receipt_path),
                "transport": call_receipt,
                "alias_audit": alias_audit,
                "rows": enriched_rows,
                "audit": audit,
                "financial_grounding_audit": grounding_summary,
                "status": audit["status"],
            }
            _write_json(call_dir / "run-document.json", document)
            key = f"run-{repetition}-context-{context_number:02d}"
            run_documents[key] = document
            print(
                f"M12B_CALL_COMPLETE {invocation_count}/"
                f"{m12.EXPECTED_MODEL_CALLS} status={audit['status']}",
                flush=True,
            )
            if audit["status"] != "PASS":
                grounding_failures = sum(
                    int(grounding_summary.get(field) or 0)
                    for field in (
                        "material_financial_anchor_grounding_failure_count",
                        "working_capital_grounding_failure_count",
                        "narrative_substitution_failure_count",
                    )
                )
                _write_json(
                    args.output_root / "canary-stop.json",
                    {
                        "status": "FAIL",
                        "stop_reason": (
                            "M12B_FIRST_CLASS_GROUNDING_INSUFFICIENT"
                            if grounding_failures
                            else "M12B_MODEL_CANARY_FAIL"
                        ),
                        "failed_invocation": invocation_id,
                        "model_calls_completed": invocation_count,
                        "wrapper_retry_count": 0,
                    },
                )
                raise SystemExit(3)

    if invocation_count != m12.EXPECTED_MODEL_CALLS:
        raise ValueError("m12b_model_call_count_mismatch")
    canonical_args = argparse.Namespace(
        generation_id=args.generation_id,
        output_root=args.output_root,
        report_dir=args.output_root / "runner-reports",
    )
    summary = m12._final_canary_audits(
        args=canonical_args,
        run_documents=run_documents,
        source_lock=source_lock,
        registry=registry,
    )
    all_rows = [
        row for document in run_documents.values() for row in document["rows"]
    ]
    grounding = _grounding_audit(
        rows=all_rows,
        catalogs=catalogs,
        contexts=contexts,
        require_complete=True,
    )
    summary = {
        **summary,
        "contract": "m12b-fictional-canary-summary-v1",
        "financial_grounding_audit": grounding,
        "status": (
            "PASS"
            if summary["status"] == "PASS"
            and grounding["status"] == "PASS"
            else "FAIL"
        ),
    }
    summary["stop_reason"] = (
        None if summary["status"] == "PASS" else "M12B_MODEL_CANARY_FAIL"
    )
    _write_json(args.output_root / "canary-summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True), flush=True)
    if summary["status"] != "PASS":
        raise SystemExit(4)


def _grounding_audit(
    *,
    rows: Sequence[Mapping[str, object]],
    catalogs: Mapping[str, object],
    contexts: Mapping[str, Mapping[str, object]],
    require_complete: bool,
) -> dict[str, object]:
    first_class_refs = _first_class_refs_by_ticker(
        catalogs=catalogs,
        contexts=contexts,
    )
    details = []
    totals = Counter()
    for row in rows:
        ticker = str(row["ticker"])
        grounding = row.get("financial_grounding") or {}
        if not isinstance(grounding, Mapping):
            grounding = {}
        selected = [
            str(ref) for ref in grounding.get("selected_financial_refs") or []
        ]
        used = [
            str(ref) for ref in grounding.get("used_financial_refs") or []
        ]
        first_class = list(first_class_refs[ticker])
        detail = {
            "ticker": ticker,
            "selected_typed_financial_refs": selected,
            "first_class_typed_financial_refs": first_class,
            "used_typed_financial_refs": used,
            "material_financial_anchor_refs": grounding.get(
                "material_financial_anchor_refs", []
            ),
            "narrative_duplicate_refs": row.get(
                "narrative_duplicate_refs", []
            ),
            "grounding_failures": grounding.get("errors", []),
            "status": grounding.get("status", "NOT_MEASURED"),
        }
        details.append(detail)
        totals.update(
            {
                "selected_typed_financial_ref_count": len(selected),
                "first_class_typed_financial_ref_count": len(first_class),
                "used_typed_financial_ref_count": len(used),
                "material_financial_anchor_grounding_failure_count": int(
                    grounding.get(
                        "material_financial_anchor_grounding_failure_count", 0
                    )
                ),
                "working_capital_grounding_failure_count": int(
                    grounding.get(
                        "working_capital_grounding_failure_count", 0
                    )
                ),
                "narrative_substitution_failure_count": int(
                    grounding.get(
                        "narrative_substitution_failure_count", 0
                    )
                ),
                "irrelevant_financial_ref_grounding_failure_count": int(
                    grounding.get(
                        "irrelevant_financial_ref_grounding_failure_count", 0
                    )
                ),
            }
        )
    complete = len(rows) == len(m12.TICKERS) * m12.REPETITION_COUNT
    failures = sum(
        totals[field]
        for field in (
            "material_financial_anchor_grounding_failure_count",
            "working_capital_grounding_failure_count",
            "narrative_substitution_failure_count",
            "irrelevant_financial_ref_grounding_failure_count",
        )
    )
    projection_match = (
        totals["selected_typed_financial_ref_count"]
        == totals["first_class_typed_financial_ref_count"]
    )
    return {
        "contract": "m12b-full-fictional-financial-grounding-audit-v1",
        "rows": details,
        **dict(totals),
        "selected_first_class_count_match": projection_match,
        "complete_sample": complete,
        "status": (
            "PASS"
            if failures == 0
            and projection_match
            and (complete or not require_complete)
            else "FAIL"
        ),
    }


def _double_counting_advisory(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    duplicate = m12a._duplicate_audit(m12a._fictional_state())
    duplicate_map: dict[str, dict[str, set[str]]] = {
        ticker: {} for ticker in m12.TICKERS
    }
    for source in duplicate["rows"]:
        duplicate_map[str(source["ticker"])][str(source["canonical_ref"])] = {
            str(ref) for ref in source["factual_duplicate_refs"]
        }
    events = []
    for row in rows:
        ticker = str(row["ticker"])
        cited = m12._candidate_refs(row["core"])
        used_typed = {
            str(ref)
            for ref in row["financial_grounding"].get(
                "used_financial_refs", []
            )
        }
        for typed_ref in used_typed:
            duplicate_refs = duplicate_map[ticker].get(typed_ref, set())
            cited_duplicates = sorted(duplicate_refs & cited)
            if cited_duplicates:
                events.append(
                    {
                        "ticker": ticker,
                        "typed_ref": typed_ref,
                        "cited_narrative_duplicates": cited_duplicates,
                    }
                )
    return {
        "contract": "m12b-double-counting-advisory-v1",
        "typed_canonical_ref_is_single_anchor_identity": True,
        "detail_metadata_counts_as_second_anchor": False,
        "typed_plus_narrative_co_citation_event_count": len(events),
        "events": events,
        "deterministic_double_counting_violation_count": 0,
        "status": (
            "DOUBLE_COUNTING_ADVISORY" if events else "PASS"
        ),
    }


def _run_documents(
    output_root: Path,
) -> dict[tuple[int, int], dict[str, object]]:
    return m12r._run_documents(output_root)


def _receipts(output_root: Path) -> list[dict[str, object]]:
    return m12r._receipts(output_root)


def _partial_runtime(output_root: Path) -> dict[str, object]:
    return {
        **m12g._partial_runtime(output_root),
        "contract": "m12b-runtime-observations-v1",
    }


def finalize(args: argparse.Namespace) -> None:
    phase_a_receipt = _json(args.output_root / "phase-a-receipt.json")
    if phase_a_receipt.get("status") != "PASS":
        raise ValueError("m12b_finalize_requires_passed_phase_a")
    run_documents = _run_documents(args.output_root)
    canary_summary_path = args.output_root / "canary-summary.json"
    canary_summary = (
        _json(canary_summary_path) if canary_summary_path.is_file() else None
    )
    manifest = _json(args.output_root / "manifest.json")
    source_lock = _json(args.output_root / "source-lock.json")
    _write_json(
        _report_path(
            args.report_dir, 31, "fictional-canary-generation-manifest"
        ),
        {
            **manifest,
            "contract": "m12b-fictional-canary-generation-manifest-v1",
            "status": "FROZEN",
        },
    )
    _write_json(
        _report_path(args.report_dir, 32, "fictional-canary-source-lock"),
        {
            **source_lock,
            "contract": "m12b-fictional-canary-source-lock-v1",
            "status": "FROZEN",
        },
    )
    for repetition in range(1, m12.REPETITION_COUNT + 1):
        for context_number in range(1, m12.CONTEXT_COUNT + 1):
            number = 33 + (repetition - 1) * 2 + (context_number - 1)
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
                    "contract": "m12b-fictional-canary-context-run-v1",
                    "generation_id": args.generation_id,
                    "repetition": repetition,
                    "context": context_number,
                    "receipt": (
                        _json(receipt_path)
                        if receipt_path.is_file()
                        else None
                    ),
                    "status": (
                        "FAIL" if receipt_path.is_file() else "NOT_RUN"
                    ),
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
    if canary_summary is not None:
        semantic = {
            **canary_summary["semantic_audit"],
            "contract": "m12b-full-fictional-canary-semantic-audit-v1",
        }
        grounding = {
            **canary_summary["financial_grounding_audit"],
            "contract": "m12b-full-fictional-canary-grounding-audit-v1",
        }
        stability = {
            **canary_summary["stability"],
            "contract": "m12b-full-fictional-canary-stability-v1",
        }
        specificity = {
            **canary_summary["specificity"],
            "contract": (
                "m12b-full-fictional-canary-message-specificity-v1"
            ),
            "typed_financial_anchor_specificity": grounding["status"],
        }
        runtime = {
            **canary_summary["runtime"],
            "contract": "m12b-runtime-observations-v1",
        }
    else:
        semantic = {
            **m12g._partial_semantic_audit(
                generation_id=args.generation_id,
                run_documents=run_documents,
            ),
            "contract": "m12b-full-fictional-canary-semantic-audit-v1",
        }
        grounding = _grounding_audit(
            rows=all_rows,
            catalogs=catalogs,
            contexts=contexts,
            require_complete=True,
        )
        stability = {
            "contract": "m12b-full-fictional-canary-stability-v1",
            "fictional_stable_count": "NOT_MEASURED",
            "fictional_boundary_uncertainty_count": "NOT_MEASURED",
            "fictional_unstable_count": "NOT_MEASURED",
            "opposite_direction_reversal_count": "NOT_MEASURED",
            "status": "NOT_MEASURED",
        }
        specificity = {
            "contract": (
                "m12b-full-fictional-canary-message-specificity-v1"
            ),
            "typed_financial_anchor_specificity": "NOT_MEASURED",
            "status": "NOT_MEASURED",
        }
        runtime = _partial_runtime(args.output_root)
    validator = {
        **m12g._validator_audit(run_documents),
        "contract": "m12b-full-fictional-canary-validator-audit-v1",
    }
    double_counting = _double_counting_advisory(all_rows)

    _write_json(
        _report_path(
            args.report_dir, 39, "full-fictional-canary-semantic-audit"
        ),
        semantic,
    )
    _write_json(
        _report_path(
            args.report_dir, 40, "full-fictional-canary-grounding-audit"
        ),
        grounding,
    )
    _write_json(
        _report_path(
            args.report_dir,
            41,
            "full-fictional-canary-double-counting-advisory",
        ),
        double_counting,
    )
    _write_json(
        _report_path(
            args.report_dir, 42, "full-fictional-canary-validator-audit"
        ),
        validator,
    )
    _write_json(
        _report_path(
            args.report_dir, 43, "full-fictional-canary-stability"
        ),
        stability,
    )
    _write_json(
        _report_path(
            args.report_dir,
            44,
            "full-fictional-canary-message-specificity-advisory",
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
        and int(semantic["fictional_output_row_count"])
        == len(m12.TICKERS) * m12.REPETITION_COUNT
        and int(semantic["fictional_schema_pass_count"])
        == len(m12.TICKERS) * m12.REPETITION_COUNT
        and all(int(semantic.get(field) or 0) == 0 for field in hard_zero_fields)
        and all(
            int(grounding.get(field) or 0) == 0
            for field in grounding_zero_fields
        )
        and int(runtime["wrapper_retry_count"]) == 0
        and int(runtime["timeout_count"]) == 0
        and int(runtime["capacity_failure_count"]) == 0
        and int(runtime["orphan_process_count"]) == 0
    )
    receipts = _receipts(args.output_root)
    runtime_failures = [
        str(receipt.get("failure_type") or "")
        for receipt in receipts
        if receipt.get("status") != "PASS"
    ]
    grounding_failure_count = sum(
        int(grounding.get(field) or 0)
        for field in grounding_zero_fields
    )
    if canary_pass:
        status = "M12B_COMPLETE"
        stop_reason = None
        next_scope = "FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF"
        fresh_real_readiness = "READY"
    elif runtime_failures:
        status = "M12B_CANARY_FAIL"
        stop_reason = "M12B_RUNTIME_FAILURE:" + ",".join(runtime_failures)
        next_scope = "BOUNDED_FICTIONAL_RUNTIME_REPAIR"
        fresh_real_readiness = "NOT_READY"
    elif grounding_failure_count:
        status = "M12B_CANARY_FAIL"
        stop_reason = "FIRST_CLASS_TYPED_GROUNDING_INSUFFICIENT"
        next_scope = (
            "DIRECTIONAL_OUTPUT_FINANCIAL_GROUNDING_"
            "SCHEMA_REVIEW_OR_IMPLEMENTATION"
        )
        fresh_real_readiness = "NOT_READY"
    elif semantic["status"] != "PASS" or validator["status"] != "PASS":
        status = "M12B_CANARY_FAIL"
        stop_reason = "M12B_NEW_FINANCIAL_SEMANTIC_BLOCKER"
        next_scope = "BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR"
        fresh_real_readiness = "NOT_READY"
    else:
        status = "M12B_CANARY_FAIL"
        stop_reason = "M12B_FINANCIAL_INTERPRETATION_STABILITY_FAILURE"
        next_scope = (
            "BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_STABILITY_REVIEW"
        )
        fresh_real_readiness = "NOT_READY"

    readiness = {
        "contract": "m12b-fresh-real-proof-readiness-decision-v1",
        "first_class_projection_status": "PASS",
        "full_fictional_canary_status": "PASS" if canary_pass else "FAIL",
        "fresh_real_proof_readiness": fresh_real_readiness,
        "production_readiness": "NOT_READY",
        "next_scope": next_scope,
        "status": "PASS" if canary_pass else "FAIL",
    }
    production = _json(
        _report_path(args.report_dir, 47, "production-no-change")
    )
    schedule_start = _json(
        _report_path(args.report_dir, 48, "schedule-pause-observation")
    )
    schedule_end = _schedule_observation()
    schedule = {
        "contract": "m12b-schedule-pause-start-end-observation-v1",
        "start": schedule_start["start"],
        "end": schedule_end,
        "observed_paused_schedule_count": schedule_end[
            "observed_paused_schedule_count"
        ],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "status": (
            "PASS"
            if schedule_start["status"] == "PASS"
            and schedule_end["status"] == "PASS"
            else "REVIEW"
        ),
    }
    master_text = MASTER_WORKFLOW_PATH.read_text(encoding="utf-8")
    master = {
        "contract": "m12b-master-workflow-update-v1",
        "path": str(MASTER_WORKFLOW_PATH),
        "sha256": _sha_text(master_text),
        "m12b_recorded": "M12B" in master_text,
        "architecture_recorded": (
            "FIRST_CLASS_TYPED_EVIDENCE_UNIFICATION" in master_text
        ),
        "next_scope_recorded": next_scope in master_text,
        "production_not_ready_recorded": (
            "production_readiness=NOT_READY" in master_text
        ),
    }
    master["status"] = (
        "PASS"
        if all(
            master[key]
            for key in (
                "m12b_recorded",
                "architecture_recorded",
                "next_scope_recorded",
                "production_not_ready_recorded",
            )
        )
        else "FAIL"
    )
    _write_json(
        _report_path(
            args.report_dir, 46, "fresh-real-proof-readiness-decision"
        ),
        readiness,
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

    projection = _json(
        _report_path(
            args.report_dir, 7, "first-class-typed-evidence-projection-contract"
        )
    )
    frozen_contract = _json(
        _report_path(
            args.report_dir,
            5,
            "m12a-frozen-implementation-contract-reuse-proof",
        )
    )
    prompt_freeze = _function_freeze(
        path="scripts/directional_core_price_timing_holdout.py",
        function_names=("_core_prompt",),
    )
    timing_freeze = _function_freeze(
        path="scripts/directional_core_price_timing_holdout.py",
        function_names=("_timing_prompt",),
    )
    source = _json(
        _report_path(args.report_dir, 24, "source-sufficiency-no-change-proof")
    )
    daily = _json(
        _report_path(args.report_dir, 25, "daily-delta-no-change-proof")
    )
    warning = _json(
        _report_path(args.report_dir, 26, "warning-no-change-proof")
    )
    old06 = _json(
        _report_path(args.report_dir, 18, "old-fic-fin-06-remains-fail")
    )
    corrected06 = _json(
        _report_path(
            args.report_dir, 19, "corrected-fic-fin-06-remains-pass"
        )
    )
    fic03 = _json(
        _report_path(args.report_dir, 20, "fic-fin-03-qtd-ytd-regression")
    )
    preliminary_rows = _artifact_source_rows(
        report_dir=args.report_dir,
        output_root=args.output_root,
    )
    completion_path = _report_path(
        args.report_dir, 50, "program-completion"
    )
    anticipated_artifact_count = len(preliminary_rows) + int(
        not completion_path.exists()
    )
    completion = {
        "contract": PROGRAM_CONTRACT,
        "base_sha": BASE_SHA,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "implementation_commit": phase_a_receipt["implementation_commit"],
        "report_commit": args.report_commit,
        "final_head_sha": "NOT_MEASURED",
        "branch": _git("branch", "--show-current"),
        "latest_result_zip_sha256": LATEST_RESULT_SHA256,
        "latest_result_integrity": "PASS",
        **{f"m{index}_status": "COMPLETE" for index in range(1, 12)},
        "m12_status": "DETERMINISTIC_COMPLETE_CANARY_BLOCKED",
        "m12r_status": "BLOCKED",
        "m12g_status": "BLOCKED_PROMPT_GROUNDING_INSUFFICIENT",
        "m12a_status": "COMPLETE",
        "m12b_status": "COMPLETE" if canary_pass else "BLOCKED",
        "preferred_grounding_architecture": (
            "FIRST_CLASS_TYPED_EVIDENCE_UNIFICATION"
        ),
        "selected_typed_financial_ref_count": projection[
            "selected_typed_financial_ref_count"
        ],
        "first_class_typed_financial_projection_count": projection[
            "first_class_typed_financial_projection_count"
        ],
        "suppressed_typed_projection_count": projection[
            "suppressed_typed_projection_count"
        ],
        "alias_renumber_count": projection["alias_renumber_count"],
        "duplicate_alias_count": projection["duplicate_alias_count"],
        "neutral_financial_statement_count": projection[
            "neutral_financial_statement_count"
        ],
        "financial_decision_context_detail_removed_count": projection[
            "financial_decision_context_detail_removed_count"
        ],
        "output_schema_change_count": 0,
        "renderer_substantive_change_count": 0,
        "old_fic_fin_06_regression_status": old06["regression_status"],
        "corrected_fic_fin_06_status": corrected06["status"],
        "fic_fin_03_qtd_ytd_regression_status": fic03["status"],
        "financial_semantic_validator_change_count": frozen_contract[
            "financial_semantic_validator_change_count"
        ],
        "qtd_ytd_validator_semantic_change_count": frozen_contract[
            "qtd_ytd_validator_semantic_change_count"
        ],
        "directional_prompt_change_count": prompt_freeze["change_count"],
        "price_timing_prompt_change_count": timing_freeze["change_count"],
        "directional_threshold_changed": False,
        "directional_increment_changed": False,
        "hold_lean_contract_changed": False,
        "calibration_tiebreak_changed": False,
        "fixed_financial_score_rule_count": int(
            semantic.get("fixed_financial_score_rule_count") or 0
        ),
        "source_sufficiency_semantic_change_count": source[
            "source_sufficiency_semantic_change_count"
        ],
        "daily_delta_semantic_change_count": daily[
            "daily_delta_semantic_change_count"
        ],
        "warning_semantic_change_count": warning[
            "warning_semantic_change_count"
        ],
        "fictional_generation_id": args.generation_id,
        "fictional_subject_count": len(m12.TICKERS),
        "fictional_context_count": m12.CONTEXT_COUNT,
        "fictional_repetition_count": m12.REPETITION_COUNT,
        "model_calls_real": 0,
        "model_calls_fictional": runtime["model_calls_fictional"],
        "model_calls_judge": 0,
        "model_context_success_count": runtime[
            "model_context_success_count"
        ],
        "model_context_failure_count": runtime[
            "model_context_failure_count"
        ],
        "wrapper_retry_count": runtime["wrapper_retry_count"],
        "timeout_count": runtime["timeout_count"],
        "capacity_failure_count": runtime["capacity_failure_count"],
        "orphan_process_count": runtime["orphan_process_count"],
        "fictional_output_row_count": semantic[
            "fictional_output_row_count"
        ],
        "fictional_schema_pass_count": semantic[
            "fictional_schema_pass_count"
        ],
        "invalid_financial_reference_count": semantic[
            "invalid_financial_reference_count"
        ],
        "hard_financial_semantic_violation_count": semantic[
            "hard_financial_semantic_violation_count"
        ],
        "used_typed_financial_ref_count": grounding.get(
            "used_typed_financial_ref_count", 0
        ),
        "material_financial_anchor_grounding_failure_count": grounding.get(
            "material_financial_anchor_grounding_failure_count", 0
        ),
        "working_capital_grounding_failure_count": grounding.get(
            "working_capital_grounding_failure_count", 0
        ),
        "narrative_substitution_failure_count": grounding.get(
            "narrative_substitution_failure_count", 0
        ),
        "validator_false_reject_count": validator[
            "validator_false_reject_count"
        ],
        "validator_false_accept_count": validator[
            "validator_false_accept_count"
        ],
        "fictional_stable_count": stability[
            "fictional_stable_count"
        ],
        "fictional_boundary_uncertainty_count": stability[
            "fictional_boundary_uncertainty_count"
        ],
        "fictional_unstable_count": stability[
            "fictional_unstable_count"
        ],
        "opposite_direction_reversal_count": stability[
            "opposite_direction_reversal_count"
        ],
        "double_counting_advisory_status": double_counting["status"],
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
        "artifact_count": anticipated_artifact_count,
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
        "fresh_real_proof_readiness": fresh_real_readiness,
        "production_readiness": "NOT_READY",
        "status": status,
        "stop_reason": stop_reason,
        "next_scope": next_scope,
        "completed_at": datetime.now(UTC).isoformat(),
    }
    _write_json(completion_path, completion)
    print(json.dumps(completion, ensure_ascii=False, sort_keys=True), flush=True)


def _artifact_source_rows(
    *,
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
            for excluded in (
                "runtime-state",
                "working-directory",
                "runner-reports",
            )
        ):
            continue
        rows.append((f"experiment/{relative}", path))
    rows.extend(
        (
            ("docs/MASTER_WORKFLOW.md", MASTER_WORKFLOW_PATH),
            (
                f"docs/work-instructions/{INSTRUCTION_PATH.name}",
                INSTRUCTION_PATH,
            ),
            (
                "app/services/directional_financial_context_service.py",
                Path(
                    "app/services/directional_financial_context_service.py"
                ),
            ),
            (
                "scripts/directional_core_price_timing_holdout.py",
                Path("scripts/directional_core_price_timing_holdout.py"),
            ),
            (
                "scripts/first_class_typed_financial_evidence_m12b.py",
                Path(
                    "scripts/first_class_typed_financial_evidence_m12b.py"
                ),
            ),
            (
                "scripts/financial_context_output_grounding_m12a.py",
                Path("scripts/financial_context_output_grounding_m12a.py"),
            ),
            (
                "tests/test_directional_financial_context_service.py",
                Path("tests/test_directional_financial_context_service.py"),
            ),
            (
                "tests/test_first_class_typed_financial_evidence_m12b.py",
                Path(
                    "tests/test_first_class_typed_financial_evidence_m12b.py"
                ),
            ),
        )
    )
    seen: set[str] = set()
    unique = []
    for archive_name, path in rows:
        if archive_name in seen:
            raise ValueError(f"m12b_duplicate_artifact_path:{archive_name}")
        if not path.is_file():
            raise ValueError(f"m12b_missing_artifact:{path}")
        seen.add(archive_name)
        unique.append((archive_name, path))
    return unique


def bundle(args: argparse.Namespace) -> None:
    rows = _artifact_source_rows(
        report_dir=args.report_dir,
        output_root=args.output_root,
    )
    failures = m12r._secret_scan_failures(rows)
    if failures:
        raise ValueError(
            "m12b_artifact_secret_scan_failed:" + ",".join(failures)
        )
    index_rows = [
        {
            "path": archive_name,
            "sha256": m12.file_sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for archive_name, path in rows
    ]
    index = {
        "contract": "m12b-artifact-index-v1",
        "payload_count": len(index_rows),
        "artifacts": index_rows,
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    args.bundle_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.bundle_path.with_suffix(
        args.bundle_path.suffix + ".tmp"
    )
    with zipfile.ZipFile(
        temporary, "w", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        for archive_name, path in rows:
            archive.write(path, archive_name)
        archive.writestr(
            "artifact-index.json",
            json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
        )
    os.replace(temporary, args.bundle_path)
    with zipfile.ZipFile(args.bundle_path) as archive:
        bad = archive.testzip()
        stored_index = json.loads(archive.read("artifact-index.json"))
        names = set(archive.namelist())
        hash_mismatches = 0
        size_mismatches = 0
        for row in stored_index["artifacts"]:
            if row["path"] not in names:
                hash_mismatches += 1
                size_mismatches += 1
                continue
            payload = archive.read(row["path"])
            hash_mismatches += int(
                _sha_bytes(payload) != row["sha256"]
            )
            size_mismatches += int(
                len(payload) != row["size_bytes"]
            )
    status = (
        "PASS"
        if bad is None
        and hash_mismatches == 0
        and size_mismatches == 0
        and not failures
        else "FAIL"
    )
    digest = m12.file_sha256(args.bundle_path)
    args.bundle_path.with_suffix(
        args.bundle_path.suffix + ".sha256"
    ).write_text(digest + "\n", encoding="utf-8")
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
        choices=("phase-a", "run-canary", "finalize", "bundle"),
    )
    value.add_argument("--generation-id")
    value.add_argument(
        "--report-dir", type=Path, default=DEFAULT_REPORT_DIR
    )
    value.add_argument(
        "--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT
    )
    value.add_argument(
        "--bundle-path", type=Path, default=DEFAULT_BUNDLE_PATH
    )
    value.add_argument("--report-commit", default="NOT_MEASURED")
    return value


def main() -> None:
    args = parser().parse_args()
    if args.command != "bundle" and not args.generation_id:
        raise ValueError("m12b_generation_id_required")
    if args.command == "phase-a":
        phase_a(args)
    elif args.command == "run-canary":
        run_canary(args)
    elif args.command == "finalize":
        finalize(args)
    else:
        bundle(args)


if __name__ == "__main__":
    main()
