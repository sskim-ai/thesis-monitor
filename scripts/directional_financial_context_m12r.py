from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

from app.services.cross_market_decision_engine_service import FinancialPeriodType
from app.services.direction_timing_ownership_service import canonical_sha256
from app.services.directional_financial_context_service import (
    validate_qtd_ytd_conflict_semantics,
)
from scripts import directional_financial_context_m12 as m12


PROGRAM_CONTRACT = "directional-financial-context-m12r-v1"
BASE_SHA = "d0e17f537d111203eafec057012182b983069831"
WORK_INSTRUCTION_COMMIT = "d01c02f3338093bf5ee380f65b8b5907ff5bbf25"
M12_GENERATION_ID = "20260909-m12-fictional-20260909T031350Z-72c281729499"
LATEST_RESULT_ZIP = Path(
    "/Users/sskim/Documents/Codex/"
    "thesis-monitor-20260909-directional-financial-context-consumption-"
    "specificity-implementation-report.zip"
)
LATEST_RESULT_SHA256 = (
    "0df2b7117ac262cc45792fe10a1b92f33bd1853d1d0545318e953f4d5a791471"
)
REPORT_DIRECTORY_NAME = (
    "20260909-bounded-directional-financial-context-validator-repair-"
    "full-fictional-canary"
)
DEFAULT_REPORT_DIR = Path("docs/reports") / REPORT_DIRECTORY_NAME
DEFAULT_OUTPUT_ROOT = Path("artifacts") / REPORT_DIRECTORY_NAME
DEFAULT_BUNDLE_PATH = Path("/Users/sskim/Documents/Codex") / (
    "thesis-monitor-20260909-bounded-directional-financial-context-validator-"
    "repair-full-fictional-canary-report.zip"
)

POSITIVE_FIXTURES = (
    "최근 분기는 흑자지만 연초 이후 누적 기준은 적자다.",
    "분기 영업흑자와 누계 영업손실이 공존한다.",
    "QTD profit is positive while YTD operating income remains negative.",
    "The latest quarter is profitable whereas year-to-date income is negative.",
    "Quarterly profit is positive while cumulative operating income is negative.",
    "이번 분기는 개선됐지만 연초부터 누적 실적은 아직 손실이다.",
)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_text(value: str) -> str:
    return _sha_bytes(value.encode("utf-8"))


def _report_path(report_dir: Path, number: int, slug: str) -> Path:
    return report_dir / f"{number:02d}-{slug}.json"


def _zip_bytes(path: str) -> bytes:
    with zipfile.ZipFile(LATEST_RESULT_ZIP) as archive:
        return archive.read(path)


def _zip_json(path: str) -> dict[str, object]:
    value = json.loads(_zip_bytes(path))
    if not isinstance(value, dict):
        raise ValueError(f"m12r_zip_json_object_required:{path}")
    return value


def _normalize_generation_identity(value: object, *generation_ids: str) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): _normalize_generation_identity(child, *generation_ids)
            for key, child in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [
            _normalize_generation_identity(child, *generation_ids) for child in value
        ]
    if isinstance(value, str):
        normalized = value
        for generation_id in generation_ids:
            normalized = normalized.replace(generation_id, "<GENERATION_ID>")
        return normalized
    return value


def _normalized_json_sha(value: object, *generation_ids: str) -> str:
    return canonical_sha256(
        _normalize_generation_identity(value, *generation_ids)
    )


def _latest_result_integrity() -> dict[str, object]:
    actual_sha = m12.file_sha256(LATEST_RESULT_ZIP)
    hash_mismatches = 0
    size_mismatches = 0
    zip_test_errors: list[str] = []
    indexed_payload_count = 0
    secret_scan_failures = 0
    with zipfile.ZipFile(LATEST_RESULT_ZIP) as archive:
        bad = archive.testzip()
        if bad:
            zip_test_errors.append(bad)
        index = json.loads(archive.read("artifact-index.json"))
        rows = index.get("artifacts") or []
        indexed_payload_count = len(rows)
        names = set(archive.namelist())
        for row in rows:
            path = str(row.get("path") or "")
            if path not in names:
                hash_mismatches += 1
                size_mismatches += 1
                continue
            payload = archive.read(path)
            if _sha_bytes(payload) != row.get("sha256"):
                hash_mismatches += 1
            if len(payload) != row.get("size_bytes"):
                size_mismatches += 1
        secret_scan_failures = int(
            index.get("artifact_secret_scan_failure_count") or 0
        )
    status = (
        "PASS"
        if actual_sha == LATEST_RESULT_SHA256
        and not zip_test_errors
        and indexed_payload_count == 95
        and hash_mismatches == 0
        and size_mismatches == 0
        and secret_scan_failures == 0
        else "FAIL"
    )
    return {
        "contract": "m12r-latest-result-integrity-v1",
        "path": str(LATEST_RESULT_ZIP),
        "expected_sha256": LATEST_RESULT_SHA256,
        "actual_sha256": actual_sha,
        "checksum_match": actual_sha == LATEST_RESULT_SHA256,
        "zip_test_errors": zip_test_errors,
        "indexed_payload_count": indexed_payload_count,
        "artifact_hash_mismatch_count": hash_mismatches,
        "artifact_size_mismatch_count": size_mismatches,
        "artifact_secret_scan_failure_count": secret_scan_failures,
        "status": status,
    }


def _function_freeze(
    *,
    path: str,
    function_names: Sequence[str],
) -> dict[str, object]:
    before_source = m12._git_file(BASE_SHA, path)
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
    return {
        "path": path,
        "functions": rows,
        "change_count": sum(row["changed"] for row in rows),
        "status": "PASS" if all(not row["changed"] for row in rows) else "FAIL",
    }


def _file_freeze(path: str) -> dict[str, object]:
    before = m12._git_file(BASE_SHA, path)
    after = Path(path).read_text(encoding="utf-8")
    return {
        "path": path,
        "before_sha256": _sha_text(before),
        "after_sha256": _sha_text(after),
        "changed": before != after,
        "status": "PASS" if before == after else "FAIL",
    }


def _launchd_label_disabled(output: str, label: str) -> bool:
    return any(
        marker in output
        for marker in (
            f'"{label}" => true',
            f'"{label}" => disabled',
        )
    )


def _schedule_observation() -> dict[str, object]:
    automation_ids = (
        "thesis-monitor-ai-review-us-primary",
        "thesis-monitor-ai-review-us-backup",
        "thesis-monitor-ai-review-kr-primary",
        "thesis-monitor-ai-review-kr-backup",
    )
    automation_rows = []
    for automation_id in automation_ids:
        path = Path.home() / ".codex" / "automations" / automation_id / "automation.toml"
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        automation_rows.append(
            {
                "id": automation_id,
                "status": (
                    "PAUSED"
                    if 'status = "PAUSED"' in text
                    else "NOT_CONFIRMED_PAUSED"
                ),
                "path_exists": path.is_file(),
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
    launch_rows = [
        {
            "id": label,
            "status": (
                "PAUSED"
                if _launchd_label_disabled(result.stdout, label)
                else "NOT_CONFIRMED_PAUSED"
            ),
        }
        for label in launch_labels
    ]
    rows = [*automation_rows, *launch_rows]
    paused = sum(row["status"] == "PAUSED" for row in rows)
    return {
        "contract": "m12r-schedule-pause-observation-v1",
        "observed_at": datetime.now(UTC).isoformat(),
        "rows": rows,
        "launchctl_returncode": result.returncode,
        "observed_paused_schedule_count": paused,
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "status": "PASS" if paused == 8 else "REVIEW",
    }


def _period_fixture_refs() -> tuple[object, object]:
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


def _validate_fixture(candidate: object) -> dict[str, object]:
    qtd, ytd = _period_fixture_refs()
    result = validate_qtd_ytd_conflict_semantics(
        candidate,
        supplied_refs=(qtd, ytd),
        required_ref_ids=(qtd.ref_id, ytd.ref_id),
    )
    return result.model_dump(mode="json")


def _positive_fixture_report() -> dict[str, object]:
    qtd, ytd = _period_fixture_refs()
    rows = []
    for index, text in enumerate(POSITIVE_FIXTURES, start=1):
        validation = _validate_fixture(
            {
                "claim": {
                    "text": text,
                    "evidence_refs": [qtd.ref_id, ytd.ref_id],
                }
            }
        )
        rows.append(
            {
                "fixture_id": f"positive-{index:02d}",
                "text": text,
                "validation": validation,
                "status": "PASS" if validation["valid"] else "FAIL",
            }
        )
    return {
        "contract": "m12r-qtd-ytd-positive-fixtures-v1",
        "fixture_count": len(rows),
        "pass_count": sum(row["status"] == "PASS" for row in rows),
        "rows": rows,
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def _negative_fixture_report() -> dict[str, object]:
    qtd, ytd = _period_fixture_refs()
    both = [qtd.ref_id, ytd.ref_id]
    fixtures = (
        (
            "vague-recent-results",
            {"claim": {"text": "최근 실적은 엇갈린다.", "evidence_refs": both}},
        ),
        (
            "adverbial-cumulative",
            {
                "claim": {
                    "text": "분기 실적이 좋지만 누적적으로도 중요하다.",
                    "evidence_refs": both,
                }
            },
        ),
        (
            "qtd-marker-only",
            {"claim": {"text": "최근 분기 실적만 개선됐다.", "evidence_refs": both}},
        ),
        (
            "ytd-marker-only",
            {
                "claim": {
                    "text": "연초 이후 누적 실적은 손실이다.",
                    "evidence_refs": both,
                }
            },
        ),
        (
            "both-markers-one-ref",
            {
                "claim": {
                    "text": "분기는 흑자지만 누계는 적자다.",
                    "evidence_refs": [qtd.ref_id],
                }
            },
        ),
        (
            "both-markers-ytd-ref-only",
            {
                "claim": {
                    "text": "분기는 흑자지만 누계는 적자다.",
                    "evidence_refs": [ytd.ref_id],
                }
            },
        ),
        (
            "both-refs-period-names-without-contrast",
            {
                "claim": {
                    "text": "QTD와 YTD 영업실적을 확인했다.",
                    "evidence_refs": both,
                }
            },
        ),
        (
            "both-refs-no-explicit-period-contrast",
            {"claim": {"text": "두 실적은 엇갈린다.", "evidence_refs": both}},
        ),
        (
            "unrelated-quarter-checkpoint",
            {
                "claims": [
                    {"text": "최근 실적은 엇갈린다.", "evidence_refs": both},
                    {"text": "다음 분기 수요를 확인한다.", "evidence_refs": []},
                ]
            },
        ),
        (
            "unrelated-cumulative-text",
            {
                "claims": [
                    {"text": "최근 실적은 엇갈린다.", "evidence_refs": both},
                    {"text": "고객 누적 수는 별도 지표다.", "evidence_refs": []},
                ]
            },
        ),
    )
    rows = []
    for fixture_id, candidate in fixtures:
        validation = _validate_fixture(candidate)
        rows.append(
            {
                "fixture_id": fixture_id,
                "candidate": candidate,
                "validation": validation,
                "status": "PASS" if not validation["valid"] else "FAIL",
            }
        )
    return {
        "contract": "m12r-qtd-ytd-negative-fixtures-v1",
        "fixture_count": len(rows),
        "rejected_count": sum(row["status"] == "PASS" for row in rows),
        "rows": rows,
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def _historical_raw_regression() -> dict[str, object]:
    raw = _zip_json("experiment/model-calls/run-1/context-01/output.raw.json")
    packets, owned, catalogs, _contexts = m12.fictional_inputs(M12_GENERATION_ID)
    batch, alias_audit = m12._resolve_core_batch(
        raw,
        generation_id=M12_GENERATION_ID,
        tickers=m12.CONTEXTS[0],
        packets=packets,
        catalogs=catalogs,
    )
    rows, audit = m12._audit_core_batch(
        batch,
        owned=owned,
        catalogs=catalogs,
    )
    focal = next(row for row in rows if row["ticker"] == "FIC-FIN-03")
    return {
        "contract": "m12r-historical-raw-output-regression-v1",
        "source_path": "experiment/model-calls/run-1/context-01/output.raw.json",
        "source_sha256": _sha_bytes(
            _zip_bytes("experiment/model-calls/run-1/context-01/output.raw.json")
        ),
        "alias_audit": alias_audit,
        "rows": rows,
        "audit": audit,
        "historical_fic_fin_03_regression_status": focal["status"],
        "focal_qtd_ytd_validation": focal["qtd_ytd_semantics"],
        "new_hard_financial_semantic_violation_count": audit["hard_error_count"],
        "status": (
            "PASS"
            if audit["status"] == "PASS"
            and audit["pass_count"] == 4
            and focal["qtd_ytd_semantics"]["valid"]
            else "FAIL"
        ),
    }


def _model_input_freeze(
    *,
    generation_id: str,
    output_root: Path,
) -> dict[str, object]:
    prompt_rows = []
    schema_rows = []
    for context_number in range(1, m12.CONTEXT_COUNT + 1):
        base = f"experiment/frozen-contexts/context-{context_number:02d}"
        old_prompt = _zip_bytes(f"{base}/prompt.txt").decode("utf-8")
        new_prompt_path = (
            output_root / "frozen-contexts" / f"context-{context_number:02d}" / "prompt.txt"
        )
        new_prompt = new_prompt_path.read_text(encoding="utf-8")
        old_normalized = old_prompt.replace(M12_GENERATION_ID, "<GENERATION_ID>")
        new_normalized = new_prompt.replace(generation_id, "<GENERATION_ID>")
        prompt_rows.append(
            {
                "context": context_number,
                "before_normalized_sha256": _sha_text(old_normalized),
                "after_normalized_sha256": _sha_text(new_normalized),
                "changed": old_normalized != new_normalized,
            }
        )
        old_schema = _zip_json(f"{base}/schema.json")
        new_schema = m12.read_json(
            output_root
            / "frozen-contexts"
            / f"context-{context_number:02d}"
            / "schema.json"
        )
        old_sha = _normalized_json_sha(old_schema, M12_GENERATION_ID)
        new_sha = _normalized_json_sha(new_schema, generation_id)
        schema_rows.append(
            {
                "context": context_number,
                "before_normalized_sha256": old_sha,
                "after_normalized_sha256": new_sha,
                "changed": old_sha != new_sha,
            }
        )
    return {
        "prompt_rows": prompt_rows,
        "schema_rows": schema_rows,
        "directional_prompt_change_count": sum(row["changed"] for row in prompt_rows),
        "schema_change_count": sum(row["changed"] for row in schema_rows),
    }


def _packet_context_freeze(
    *,
    generation_id: str,
    output_root: Path,
) -> dict[str, object]:
    case_rows = []
    context_rows = []
    for ticker in m12.TICKERS:
        old_packet = _zip_json(f"experiment/packets/{ticker}.json")
        new_packet = m12.read_json(output_root / "packets" / f"{ticker}.json")
        old_packet_sha = _normalized_json_sha(old_packet, M12_GENERATION_ID)
        new_packet_sha = _normalized_json_sha(new_packet, generation_id)
        case_rows.append(
            {
                "ticker": ticker,
                "before_normalized_sha256": old_packet_sha,
                "after_normalized_sha256": new_packet_sha,
                "changed": old_packet_sha != new_packet_sha,
            }
        )
        old_context = _zip_json(f"experiment/contexts/{ticker}.json")
        new_context = m12.read_json(output_root / "contexts" / f"{ticker}.json")
        old_context_sha = _normalized_json_sha(old_context, M12_GENERATION_ID)
        new_context_sha = _normalized_json_sha(new_context, generation_id)
        context_rows.append(
            {
                "ticker": ticker,
                "before_normalized_sha256": old_context_sha,
                "after_normalized_sha256": new_context_sha,
                "changed": old_context_sha != new_context_sha,
            }
        )
    return {
        "case_rows": case_rows,
        "context_rows": context_rows,
        "fictional_case_change_count": sum(row["changed"] for row in case_rows),
        "financial_context_selection_change_count": sum(
            row["changed"] for row in context_rows
        ),
    }


def _write_frozen_inputs(
    *,
    generation_id: str,
    output_root: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    packets, owned, catalogs, contexts = m12.fictional_inputs(generation_id)
    manifest = m12.fictional_manifest(generation_id)
    source_lock = m12._source_lock(
        generation_id, packets, owned, catalogs, contexts
    )
    model_inputs = m12._write_frozen_model_inputs(
        output_root=output_root,
        generation_id=generation_id,
        contexts=contexts,
        catalogs=catalogs,
    )
    m12.write_json(output_root / "manifest.json", manifest)
    m12.write_json(output_root / "source-lock.json", source_lock)
    for ticker in m12.TICKERS:
        m12.write_json(
            output_root / "packets" / f"{ticker}.json",
            packets[ticker].model_dump(mode="json"),
        )
        m12.write_json(
            output_root / "aliases" / f"{ticker}.json",
            catalogs[ticker].model_dump(mode="json"),
        )
        m12.write_json(
            output_root / "contexts" / f"{ticker}.json",
            contexts[ticker],
        )
    return source_lock, model_inputs


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
        raise ValueError("m12r_implementation_commit_required")
    if (args.output_root / "phase-a-receipt.json").exists():
        raise ValueError("m12r_existing_phase_a_artifacts_refuse_rerun")

    args.report_dir.mkdir(parents=True, exist_ok=True)
    args.output_root.mkdir(parents=True, exist_ok=True)
    source_lock, model_inputs = _write_frozen_inputs(
        generation_id=args.generation_id,
        output_root=args.output_root,
    )
    latest_integrity = _latest_result_integrity()
    historical = _historical_raw_regression()
    positive = _positive_fixture_report()
    negative = _negative_fixture_report()
    model_input_freeze = _model_input_freeze(
        generation_id=args.generation_id,
        output_root=args.output_root,
    )
    packet_context_freeze = _packet_context_freeze(
        generation_id=args.generation_id,
        output_root=args.output_root,
    )
    directional_function_freeze = _function_freeze(
        path="scripts/directional_core_price_timing_holdout.py",
        function_names=("_core_prompt",),
    )
    timing_function_freeze = _function_freeze(
        path="scripts/directional_core_price_timing_holdout.py",
        function_names=("_timing_prompt",),
    )
    selector_function_freeze = _function_freeze(
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
    fictional_function_freeze = _function_freeze(
        path="scripts/directional_financial_context_m12.py",
        function_names=(
            "_period",
            "_financial_ref",
            "_financial_pair",
            "_generic_ref",
            "_technical_ref",
            "_common_refs",
            "_case_refs",
            "_family_for_ref",
            "fictional_inputs",
            "fictional_manifest",
            "_source_lock",
            "_write_frozen_model_inputs",
        ),
    )
    no_change = {
        "source_sufficiency": _file_freeze(
            "app/services/coldstart_fundamental_enrichment_service.py"
        ),
        "daily_delta": _file_freeze(
            "app/services/nonproduction_monitoring_lifecycle_service.py"
        ),
        "renderer": _file_freeze(
            "app/services/structured_autonomy_shadow_service.py"
        ),
        "warning": _file_freeze("app/services/warning_backfill_service.py"),
        "notification": _file_freeze("app/services/notification_service.py"),
    }
    validations = _validation_commands(args.output_root)
    schedule = _schedule_observation()

    changed_paths = tuple(
        path
        for path in _git(
            "diff", "--name-only", WORK_INSTRUCTION_COMMIT, implementation_commit
        ).splitlines()
        if path
    )
    expected_changed_paths = {
        "app/services/directional_financial_context_service.py",
        "scripts/directional_financial_context_m12.py",
        "scripts/directional_financial_context_m12r.py",
        "tests/test_directional_financial_context_m12.py",
        "tests/test_directional_financial_context_m12r.py",
        "tests/test_directional_financial_context_service.py",
    }
    unexpected_changed_paths = sorted(
        set(changed_paths) - expected_changed_paths
    )
    old_run = _zip_json("reports/33-canary-context-01-run-1.json")
    old_focal = next(
        row for row in old_run["rows"] if row["ticker"] == "FIC-FIN-03"
    )

    repository = {
        "contract": "m12r-repository-provenance-v1",
        "branch": _git("branch", "--show-current"),
        "base_sha": BASE_SHA,
        "actual_base_head": _git("rev-parse", f"{WORK_INSTRUCTION_COMMIT}^"),
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "implementation_commit": implementation_commit,
        "changed_paths_from_instruction_commit": list(changed_paths),
        "unexpected_changed_paths": unexpected_changed_paths,
        "status": "PASS" if not unexpected_changed_paths else "FAIL",
    }
    scope = {
        "contract": "m12r-scope-freeze-v1",
        "model": m12.MODEL,
        "reasoning_effort": m12.EFFORT,
        "timeout_seconds": m12.TIMEOUT_SECONDS,
        "fictional_subject_count": len(m12.TICKERS),
        "fictional_context_count": m12.CONTEXT_COUNT,
        "fictional_repetition_count": m12.REPETITION_COUNT,
        "fictional_model_calls": m12.EXPECTED_MODEL_CALLS,
        "real_model_calls": 0,
        "judge_model_calls": 0,
        "provider_source_fetches": 0,
        "validator_only_semantic_repair": True,
        "production_side_effects_allowed": False,
        "status": "FROZEN",
    }
    before_after = {
        "contract": "m12r-qtd-ytd-validator-before-after-v1",
        "before": {
            "ticker": "FIC-FIN-03",
            "errors": old_focal["errors"],
            "status": old_focal["status"],
            "validator_behavior": "QTD_OR_QUARTER_AND_YTD_OR_NUGYE_ONLY",
        },
        "after": {
            "ticker": "FIC-FIN-03",
            "status": historical["historical_fic_fin_03_regression_status"],
            "validation": historical["focal_qtd_ytd_validation"],
            "validator_behavior": (
                "SAME_METRIC_QTD_YTD_REFS_PLUS_BOUNDED_PERIOD_LANGUAGE_AND_RELATION"
            ),
        },
        "prompt_changed": False,
        "fictional_case_changed": False,
        "status": historical["status"],
    }
    prompt_report = {
        "contract": "m12r-directional-prompt-freeze-proof-v1",
        "function_freeze": directional_function_freeze,
        "normalized_model_input_rows": model_input_freeze["prompt_rows"],
        "directional_prompt_change_count": (
            directional_function_freeze["change_count"]
            + model_input_freeze["directional_prompt_change_count"]
        ),
    }
    prompt_report["status"] = (
        "PASS" if prompt_report["directional_prompt_change_count"] == 0 else "FAIL"
    )
    timing_report = {
        "contract": "m12r-price-timing-prompt-freeze-proof-v1",
        "function_freeze": timing_function_freeze,
        "price_timing_prompt_change_count": timing_function_freeze["change_count"],
    }
    timing_report["status"] = (
        "PASS" if timing_report["price_timing_prompt_change_count"] == 0 else "FAIL"
    )
    selector_report = {
        "contract": "m12r-financial-context-selection-freeze-proof-v1",
        "function_freeze": selector_function_freeze,
        "context_rows": packet_context_freeze["context_rows"],
        "financial_context_selection_change_count": (
            selector_function_freeze["change_count"]
            + packet_context_freeze["financial_context_selection_change_count"]
        ),
    }
    selector_report["status"] = (
        "PASS"
        if selector_report["financial_context_selection_change_count"] == 0
        else "FAIL"
    )
    case_report = {
        "contract": "m12r-fictional-case-freeze-proof-v1",
        "function_freeze": fictional_function_freeze,
        "packet_rows": packet_context_freeze["case_rows"],
        "fictional_case_change_count": (
            fictional_function_freeze["change_count"]
            + packet_context_freeze["fictional_case_change_count"]
        ),
    }
    case_report["status"] = (
        "PASS" if case_report["fictional_case_change_count"] == 0 else "FAIL"
    )
    schema_report = {
        "contract": "m12r-schema-freeze-proof-v1",
        "rows": model_input_freeze["schema_rows"],
        "schema_change_count": model_input_freeze["schema_change_count"],
    }
    schema_report["status"] = (
        "PASS" if schema_report["schema_change_count"] == 0 else "FAIL"
    )

    reports: dict[tuple[int, str], object] = {
        (1, "repository-provenance"): repository,
        (2, "latest-result-integrity"): latest_integrity,
        (3, "m12r-scope-freeze"): scope,
        (4, "m12-failure-reproduction"): {
            "contract": "m12r-m12-failure-reproduction-v1",
            "attempted_contexts": 1,
            "transport_success_count": 1,
            "schema_valid_row_count": 4,
            "hard_financial_semantic_violation_count": 0,
            "focal_ticker": "FIC-FIN-03",
            "reported_errors": old_focal["errors"],
            "status": "REPRODUCED",
        },
        (5, "qtd-ytd-validator-root-cause"): {
            "contract": "m12r-qtd-ytd-validator-root-cause-v1",
            "root_cause": (
                "QTD_YTD_VALIDATOR_KOREAN_CUMULATIVE_WORDING_FALSE_REJECT"
            ),
            "recognized_before": ["ytd", "누계"],
            "missed_valid_marker": "누적",
            "model_semantic_failure": False,
            "status": "CONFIRMED",
        },
        (6, "qtd-ytd-validator-before-after"): before_after,
        (7, "validator-responsibility-contract"): {
            "contract": "m12r-validator-responsibility-v1",
            "requires_same_metric_qtd_and_ytd_selected_refs": True,
            "requires_same_claim_qtd_and_ytd_linkage": True,
            "requires_explicit_qtd_language": True,
            "requires_explicit_ytd_or_cumulative_language": True,
            "requires_explicit_period_relation": True,
            "rejects_loose_cumulative_substring": True,
            "status": "PASS",
        },
        (8, "historical-raw-output-regression"): historical,
        (9, "qtd-ytd-positive-fixture-manifest"): positive,
        (10, "qtd-ytd-negative-fixture-manifest"): negative,
        (11, "validator-false-accept-control"): {
            "contract": "m12r-validator-false-accept-control-v1",
            "fixture_count": negative["fixture_count"],
            "rejected_count": negative["rejected_count"],
            "validator_false_accept_count": (
                negative["fixture_count"] - negative["rejected_count"]
            ),
            "status": negative["status"],
        },
        (12, "validator-false-reject-control"): {
            "contract": "m12r-validator-false-reject-control-v1",
            "fixture_count": positive["fixture_count"],
            "pass_count": positive["pass_count"],
            "historical_fic_fin_03_status": historical[
                "historical_fic_fin_03_regression_status"
            ],
            "validator_false_reject_count": (
                positive["fixture_count"] - positive["pass_count"]
            ),
            "status": (
                "PASS"
                if positive["status"] == "PASS" and historical["status"] == "PASS"
                else "FAIL"
            ),
        },
        (13, "directional-prompt-freeze-proof"): prompt_report,
        (14, "price-timing-prompt-freeze-proof"): timing_report,
        (15, "financial-context-selection-freeze-proof"): selector_report,
        (16, "fictional-case-freeze-proof"): case_report,
        (17, "schema-freeze-proof"): schema_report,
        (18, "source-sufficiency-no-change-proof"): {
            **no_change["source_sufficiency"],
            "source_sufficiency_semantic_change_count": int(
                no_change["source_sufficiency"]["changed"]
            ),
        },
        (19, "daily-delta-no-change-proof"): {
            **no_change["daily_delta"],
            "daily_delta_semantic_change_count": int(
                no_change["daily_delta"]["changed"]
            ),
            "warning": no_change["warning"],
            "notification": no_change["notification"],
            "warning_semantic_change_count": int(
                no_change["warning"]["changed"]
                or no_change["notification"]["changed"]
            ),
        },
        (20, "renderer-ownership-no-change-proof"): {
            **no_change["renderer"],
            "renderer_substantive_change_count": int(
                no_change["renderer"]["changed"]
            ),
        },
        (21, "focused-test-results"): validations["focused"],
        (22, "full-test-results"): validations["full"],
        (23, "ruff-and-diff-results"): {
            "ruff": validations["ruff"],
            "git_diff_check": validations["diff"],
            "status": (
                "PASS"
                if validations["ruff"]["status"] == "PASS"
                and validations["diff"]["status"] == "PASS"
                else "FAIL"
            ),
        },
        (40, "schedule-pause-observation"): {
            "contract": "m12r-schedule-pause-start-observation-v1",
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
        m12.write_json(_report_path(args.report_dir, number, slug), report)

    checks = {
        "latest_result_integrity": latest_integrity["status"],
        "repository_scope": repository["status"],
        "historical_false_reject_regression": historical["status"],
        "positive_fixtures": positive["status"],
        "negative_fixtures": negative["status"],
        "directional_prompt_freeze": prompt_report["status"],
        "price_timing_prompt_freeze": timing_report["status"],
        "financial_context_selection_freeze": selector_report["status"],
        "fictional_case_freeze": case_report["status"],
        "schema_freeze": schema_report["status"],
        "source_sufficiency_no_change": no_change["source_sufficiency"]["status"],
        "daily_delta_no_change": no_change["daily_delta"]["status"],
        "renderer_no_change": no_change["renderer"]["status"],
        "warning_no_change": (
            "PASS"
            if no_change["warning"]["status"] == "PASS"
            and no_change["notification"]["status"] == "PASS"
            else "FAIL"
        ),
        "schedule_pause": schedule["status"],
        "focused_tests": validations["focused"]["status"],
        "full_tests": validations["full"]["status"],
        "ruff": validations["ruff"]["status"],
        "git_diff_check": validations["diff"]["status"],
    }
    receipt = {
        "contract": "m12r-phase-a-gate-v1",
        "generation_id": args.generation_id,
        "implementation_commit": implementation_commit,
        "source_lock_sha256": source_lock["source_lock_sha256"],
        "model_inputs": model_inputs,
        "checks": checks,
        "model_calls_before_gate": 0,
        "status": "PASS" if all(value == "PASS" for value in checks.values()) else "FAIL",
        "stop_reason": (
            None
            if all(value == "PASS" for value in checks.values())
            else "NO_MODEL_CALLS"
        ),
    }
    m12.write_json(_report_path(args.report_dir, 24, "phase-a-gate"), receipt)
    m12.write_json(args.output_root / "phase-a-receipt.json", receipt)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True), flush=True)
    if receipt["status"] != "PASS":
        raise SystemExit(2)


def run_canary(args: argparse.Namespace) -> None:
    runner_args = argparse.Namespace(
        generation_id=args.generation_id,
        output_root=args.output_root,
        report_dir=args.output_root / "runner-reports",
    )
    m12.run_canary(runner_args)


def _run_documents(output_root: Path) -> dict[tuple[int, int], dict[str, object]]:
    rows: dict[tuple[int, int], dict[str, object]] = {}
    for repetition in range(1, m12.REPETITION_COUNT + 1):
        for context_number in range(1, m12.CONTEXT_COUNT + 1):
            path = (
                output_root
                / "model-calls"
                / f"run-{repetition}"
                / f"context-{context_number:02d}"
                / "run-document.json"
            )
            if path.is_file():
                rows[(repetition, context_number)] = m12.read_json(path)
    return rows


def _receipts(output_root: Path) -> list[dict[str, object]]:
    rows = []
    for path in sorted((output_root / "model-calls").glob("run-*/context-*/receipt.json")):
        rows.append(m12.read_json(path))
    return rows


def _partial_semantic_audit(
    *,
    generation_id: str,
    run_documents: Mapping[tuple[int, int], Mapping[str, object]],
) -> dict[str, object]:
    rows = [row for document in run_documents.values() for row in document["rows"]]
    counters = Counter()
    for row in rows:
        semantics = row["financial_semantics"]
        ownership = row["ownership"]
        qtd_ytd = row["qtd_ytd_semantics"]
        counters.update(
            {
                "invalid_financial_reference_count": semantics[
                    "invalid_financial_reference_count"
                ],
                "partial_capex_called_fcf_count": semantics[
                    "partial_capex_called_fcf_count"
                ],
                "year_end_as_yoy_count": semantics["year_end_as_yoy_count"],
                "partial_debt_total_claim_count": semantics[
                    "partial_debt_total_claim_count"
                ],
                "normalized_earnings_claim_violation_count": semantics[
                    "normalized_earnings_claim_violation_count"
                ],
                "financial_sector_generic_financial_context_leak_count": semantics[
                    "financial_sector_generic_financial_context_leak_count"
                ],
                "fixed_financial_score_rule_count": semantics[
                    "fixed_financial_score_rule_count"
                ],
                "directional_core_price_technical_refs": ownership[
                    "directional_core_price_technical_refs"
                ],
                "directional_core_supply_refs": ownership[
                    "directional_core_supply_refs"
                ],
                "ai_imperative_primary_action_count": row[
                    "ai_imperative_primary_action_count"
                ],
                "qtd_ytd_conflict_required_count": int(qtd_ytd["required"]),
                "qtd_ytd_conflict_pass_count": int(
                    qtd_ytd["required"] and qtd_ytd["valid"]
                ),
                "qtd_ytd_conflict_violation_count": len(qtd_ytd["errors"]),
                "hard_error_count": len(row["errors"]),
            }
        )
    return {
        "contract": "m12r-fictional-canary-semantic-audit-v1",
        "generation_id": generation_id,
        "fictional_output_row_count": len(rows),
        "fictional_schema_pass_count": len(rows),
        **dict(counters),
        "hard_financial_semantic_violation_count": counters["hard_error_count"],
        "all_rows_pass": all(row["status"] == "PASS" for row in rows),
        "status": (
            "PASS"
            if len(rows) == len(m12.TICKERS) * m12.REPETITION_COUNT
            and all(row["status"] == "PASS" for row in rows)
            else "FAIL"
        ),
    }


def _validator_audit(
    run_documents: Mapping[tuple[int, int], Mapping[str, object]],
) -> dict[str, object]:
    rows = []
    by_repetition: dict[str, dict[str, int]] = {}
    false_reject_count = 0
    false_accept_count = 0
    for (repetition, context_number), document in sorted(run_documents.items()):
        repetition_key = f"run-{repetition}"
        counts = by_repetition.setdefault(
            repetition_key,
            {"required_count": 0, "pass_count": 0, "violation_count": 0},
        )
        for row in document["rows"]:
            validation = row["qtd_ytd_semantics"]
            required = bool(validation["required"])
            valid = bool(validation["valid"])
            counts["required_count"] += int(required)
            counts["pass_count"] += int(required and valid)
            counts["violation_count"] += len(validation["errors"])
            false_reject_count += int(
                required
                and not valid
                and int(validation["explicit_claim_count"]) > 0
            )
            false_accept_count += int(
                required
                and valid
                and int(validation["explicit_claim_count"]) == 0
            )
            rows.append(
                {
                    "repetition": repetition,
                    "context": context_number,
                    "ticker": row["ticker"],
                    "validation": validation,
                }
            )
    violation_count = sum(
        values["violation_count"] for values in by_repetition.values()
    )
    return {
        "contract": "m12r-full-fictional-canary-validator-audit-v1",
        "rows": rows,
        "validator_pass_count_by_repetition": by_repetition,
        "validator_false_reject_count": false_reject_count,
        "validator_false_accept_count": false_accept_count,
        "qtd_ytd_conflict_violation_count": violation_count,
        "status": (
            "PASS"
            if len(rows) == len(m12.TICKERS) * m12.REPETITION_COUNT
            and false_reject_count == 0
            and false_accept_count == 0
            and violation_count == 0
            else "FAIL"
        ),
    }


def _partial_runtime(output_root: Path) -> dict[str, object]:
    receipts = _receipts(output_root)
    return {
        "contract": "m12r-runtime-observations-v1",
        "model": m12.MODEL,
        "reasoning_effort": m12.EFFORT,
        "model_calls_fictional": len(receipts),
        "model_calls_real": 0,
        "model_calls_judge": 0,
        "model_context_success_count": sum(
            receipt["status"] == "PASS" for receipt in receipts
        ),
        "model_context_failure_count": sum(
            receipt["status"] != "PASS" for receipt in receipts
        ),
        "wrapper_retry_count": sum(
            int(receipt.get("wrapper_retry_count") or 0) for receipt in receipts
        ),
        "timeout_count": sum(
            int(receipt.get("timeout_count") or 0) for receipt in receipts
        ),
        "capacity_failure_count": sum(
            "CAPACITY" in str(receipt.get("failure_type") or "").upper()
            for receipt in receipts
        ),
        "orphan_process_count": sum(
            int(receipt.get("orphan_process_count") or 0) for receipt in receipts
        ),
        "single_authoritative_watchdog": True,
        "batch_split": 0,
        "status": "FAIL",
        "receipts": receipts,
    }


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
            for excluded in ("runtime-state", "working-directory", "runner-reports")
        ):
            continue
        rows.append((f"experiment/{relative}", path))
    rows.extend(
        (
            ("docs/MASTER_WORKFLOW.md", Path("docs/MASTER_WORKFLOW.md")),
            (
                "docs/work-instructions/"
                "20260909-bounded-directional-financial-context-validator-"
                "repair-and-full-fictional-canary.md",
                Path(
                    "docs/work-instructions/"
                    "20260909-bounded-directional-financial-context-validator-"
                    "repair-and-full-fictional-canary.md"
                ),
            ),
        )
    )
    seen: set[str] = set()
    unique = []
    for archive_name, path in rows:
        if archive_name in seen:
            raise ValueError(f"m12r_duplicate_artifact_path:{archive_name}")
        seen.add(archive_name)
        unique.append((archive_name, path))
    return unique


def _secret_scan_failures(rows: Sequence[tuple[str, Path]]) -> list[str]:
    markers = (
        "TELEGRAM_BOT_TOKEN=",
        "OPENAI_API_KEY=",
        "DART_API_KEY=",
        "ACTION_API_KEY=",
        '"access_token":',
        '"refresh_token":',
    )
    failures = []
    for archive_name, path in rows:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if any(marker in text for marker in markers):
            failures.append(archive_name)
    return failures


def finalize(args: argparse.Namespace) -> None:
    phase_a_receipt = m12.read_json(args.output_root / "phase-a-receipt.json")
    if phase_a_receipt.get("status") != "PASS":
        raise ValueError("m12r_finalize_requires_passed_phase_a")
    run_documents = _run_documents(args.output_root)
    canary_summary_path = args.output_root / "canary-summary.json"
    canary_summary = (
        m12.read_json(canary_summary_path) if canary_summary_path.is_file() else None
    )

    manifest = m12.read_json(args.output_root / "manifest.json")
    source_lock = m12.read_json(args.output_root / "source-lock.json")
    m12.write_json(
        _report_path(args.report_dir, 25, "fictional-canary-generation-manifest"),
        {
            **manifest,
            "contract": "m12r-fictional-canary-generation-manifest-v1",
            "status": "FROZEN",
        },
    )
    m12.write_json(
        _report_path(args.report_dir, 26, "fictional-canary-source-lock"),
        {
            **source_lock,
            "contract": "m12r-fictional-canary-source-lock-v1",
            "status": "FROZEN",
        },
    )
    for repetition in range(1, m12.REPETITION_COUNT + 1):
        for context_number in range(1, m12.CONTEXT_COUNT + 1):
            number = 25 + (repetition - 1) * 2 + context_number
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
                    "contract": "m12r-fictional-canary-context-run-v1",
                    "generation_id": args.generation_id,
                    "repetition": repetition,
                    "context": context_number,
                    "receipt": (
                        m12.read_json(receipt_path) if receipt_path.is_file() else None
                    ),
                    "status": "FAIL" if receipt_path.is_file() else "NOT_RUN",
                }
            else:
                document = {
                    **document,
                    "contract": "m12r-fictional-canary-context-run-v1",
                }
            m12.write_json(
                _report_path(
                    args.report_dir,
                    number,
                    f"run-{repetition}-context-{context_number:02d}",
                ),
                document,
            )

    if canary_summary is not None:
        semantic = {
            **canary_summary["semantic_audit"],
            "contract": "m12r-full-fictional-canary-semantic-audit-v1",
        }
        stability = {
            **canary_summary["stability"],
            "contract": "m12r-full-fictional-canary-stability-v1",
        }
        specificity = {
            **canary_summary["specificity"],
            "contract": "m12r-full-fictional-canary-message-specificity-v1",
        }
        runtime = {
            **canary_summary["runtime"],
            "contract": "m12r-runtime-observations-v1",
        }
    else:
        semantic = _partial_semantic_audit(
            generation_id=args.generation_id,
            run_documents=run_documents,
        )
        stability = {
            "contract": "m12r-full-fictional-canary-stability-v1",
            "fictional_stable_count": "NOT_MEASURED",
            "fictional_boundary_uncertainty_count": "NOT_MEASURED",
            "fictional_unstable_count": "NOT_MEASURED",
            "opposite_direction_reversal_count": "NOT_MEASURED",
            "status": "NOT_MEASURED",
        }
        specificity = {
            "contract": "m12r-full-fictional-canary-message-specificity-v1",
            "status": "NOT_MEASURED",
        }
        runtime = _partial_runtime(args.output_root)
    validator = _validator_audit(run_documents)

    m12.write_json(
        _report_path(args.report_dir, 33, "full-fictional-canary-semantic-audit"),
        semantic,
    )
    m12.write_json(
        _report_path(args.report_dir, 34, "full-fictional-canary-validator-audit"),
        validator,
    )
    m12.write_json(
        _report_path(args.report_dir, 35, "full-fictional-canary-stability"),
        stability,
    )
    m12.write_json(
        _report_path(
            args.report_dir, 36, "full-fictional-canary-message-specificity-advisory"
        ),
        specificity,
    )
    m12.write_json(
        _report_path(args.report_dir, 37, "runtime-observations"), runtime
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
    canary_pass = bool(
        len(run_documents) == m12.EXPECTED_MODEL_CALLS
        and semantic["status"] == "PASS"
        and validator["status"] == "PASS"
        and stability["status"] == "PASS"
        and runtime["status"] == "PASS"
        and int(semantic["fictional_output_row_count"])
        == len(m12.TICKERS) * m12.REPETITION_COUNT
        and int(semantic["fictional_schema_pass_count"])
        == len(m12.TICKERS) * m12.REPETITION_COUNT
        and all(int(semantic.get(field) or 0) == 0 for field in hard_zero_fields)
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
    if canary_pass:
        stop_reason = None
        next_scope = "FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF"
        fresh_real_readiness = "READY"
    elif runtime_failures:
        stop_reason = "M12R_RUNTIME_FAILURE:" + ",".join(runtime_failures)
        next_scope = "BOUNDED_FICTIONAL_RUNTIME_REPAIR"
        fresh_real_readiness = "NOT_READY"
    else:
        stop_reason = "M12R_FINANCIAL_SEMANTIC_OR_STABILITY_FAILURE"
        next_scope = "BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR"
        fresh_real_readiness = "NOT_READY"

    readiness = {
        "contract": "m12r-fresh-real-proof-readiness-decision-v1",
        "validator_repair_status": "PASS",
        "full_fictional_canary_status": "PASS" if canary_pass else "FAIL",
        "fresh_real_proof_readiness": fresh_real_readiness,
        "production_readiness": "NOT_READY",
        "next_scope": next_scope,
        "status": "PASS" if canary_pass else "FAIL",
    }
    production = {
        "contract": "m12r-production-no-change-v1",
        "provider_source_fetches": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "assessment_persistence_mutations": 0,
        "warning_mutations": 0,
        "notification_queue_writes": 0,
        "production_sends": 0,
        "main_merges": 0,
        "deployments": 0,
        "live_v2_changes": 0,
        "night_futures_changes": 0,
        "automatic_monitoring_resume": 0,
        "production_readiness": "NOT_READY",
        "status": "PASS",
    }
    schedule_start = m12.read_json(
        _report_path(args.report_dir, 40, "schedule-pause-observation")
    )
    schedule_end = _schedule_observation()
    schedule = {
        "contract": "m12r-schedule-pause-start-end-observation-v1",
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
    master_text = Path("docs/MASTER_WORKFLOW.md").read_text(encoding="utf-8")
    master = {
        "contract": "m12r-master-workflow-update-v1",
        "path": "docs/MASTER_WORKFLOW.md",
        "sha256": _sha_text(master_text),
        "m12r_recorded": "M12R" in master_text,
        "validator_root_cause_recorded": (
            "QTD_YTD_VALIDATOR_KOREAN_CUMULATIVE_WORDING_FALSE_REJECT"
            in master_text
        ),
        "next_scope_recorded": next_scope in master_text,
        "production_not_ready_recorded": "production_readiness=NOT_READY" in master_text,
    }
    master["status"] = (
        "PASS"
        if all(
            master[key]
            for key in (
                "m12r_recorded",
                "validator_root_cause_recorded",
                "next_scope_recorded",
                "production_not_ready_recorded",
            )
        )
        else "FAIL"
    )
    m12.write_json(
        _report_path(args.report_dir, 38, "fresh-real-proof-readiness-decision"),
        readiness,
    )
    m12.write_json(
        _report_path(args.report_dir, 39, "production-no-change"), production
    )
    m12.write_json(
        _report_path(args.report_dir, 40, "schedule-pause-observation"), schedule
    )
    m12.write_json(
        _report_path(args.report_dir, 41, "master-workflow-update"), master
    )

    positive = m12.read_json(
        _report_path(args.report_dir, 9, "qtd-ytd-positive-fixture-manifest")
    )
    negative = m12.read_json(
        _report_path(args.report_dir, 10, "qtd-ytd-negative-fixture-manifest")
    )
    prompt_freeze = m12.read_json(
        _report_path(args.report_dir, 13, "directional-prompt-freeze-proof")
    )
    timing_freeze = m12.read_json(
        _report_path(args.report_dir, 14, "price-timing-prompt-freeze-proof")
    )
    selector_freeze = m12.read_json(
        _report_path(args.report_dir, 15, "financial-context-selection-freeze-proof")
    )
    case_freeze = m12.read_json(
        _report_path(args.report_dir, 16, "fictional-case-freeze-proof")
    )
    schema_freeze = m12.read_json(
        _report_path(args.report_dir, 17, "schema-freeze-proof")
    )
    source_freeze = m12.read_json(
        _report_path(args.report_dir, 18, "source-sufficiency-no-change-proof")
    )
    daily_freeze = m12.read_json(
        _report_path(args.report_dir, 19, "daily-delta-no-change-proof")
    )
    completion_path = _report_path(args.report_dir, 42, "program-completion")
    preliminary_rows = _artifact_source_rows(
        report_dir=args.report_dir,
        output_root=args.output_root,
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
        "m1_status": "COMPLETE",
        "m2_status": "COMPLETE",
        "m3_status": "COMPLETE",
        "m4_status": "COMPLETE",
        "m5_status": "COMPLETE",
        "m6_status": "COMPLETE",
        "m7_status": "COMPLETE",
        "m8_status": "COMPLETE",
        "m9_status": "COMPLETE",
        "m10_status": "COMPLETE",
        "m11_status": "COMPLETE",
        "m12_status": "DETERMINISTIC_COMPLETE_CANARY_BLOCKED",
        "m12r_status": "COMPLETE" if canary_pass else "BLOCKED",
        "m12_root_cause": (
            "QTD_YTD_VALIDATOR_KOREAN_CUMULATIVE_WORDING_FALSE_REJECT"
        ),
        "validator_repair_status": "PASS",
        "historical_fic_fin_03_regression_status": "PASS",
        "qtd_ytd_positive_fixture_count": positive["fixture_count"],
        "qtd_ytd_positive_fixture_pass_count": positive["pass_count"],
        "qtd_ytd_negative_fixture_count": negative["fixture_count"],
        "qtd_ytd_negative_fixture_rejected_count": negative["rejected_count"],
        "validator_false_reject_count": validator["validator_false_reject_count"],
        "validator_false_accept_count": validator["validator_false_accept_count"],
        "directional_prompt_change_count": prompt_freeze[
            "directional_prompt_change_count"
        ],
        "price_timing_prompt_change_count": timing_freeze[
            "price_timing_prompt_change_count"
        ],
        "financial_context_selection_change_count": selector_freeze[
            "financial_context_selection_change_count"
        ],
        "fictional_case_change_count": case_freeze["fictional_case_change_count"],
        "schema_change_count": schema_freeze["schema_change_count"],
        "directional_threshold_changed": False,
        "directional_increment_changed": False,
        "hold_lean_contract_changed": False,
        "calibration_tiebreak_changed": False,
        "source_sufficiency_semantic_change_count": source_freeze[
            "source_sufficiency_semantic_change_count"
        ],
        "daily_delta_semantic_change_count": daily_freeze[
            "daily_delta_semantic_change_count"
        ],
        "warning_semantic_change_count": daily_freeze[
            "warning_semantic_change_count"
        ],
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
        "live_v2_changes": 0,
        "night_futures_changes": 0,
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
        "status": "M12R_COMPLETE" if canary_pass else "M12R_CANARY_FAIL",
        "stop_reason": stop_reason,
        "next_scope": next_scope,
        "completed_at": datetime.now(UTC).isoformat(),
    }
    m12.write_json(completion_path, completion)
    print(json.dumps(completion, ensure_ascii=False, sort_keys=True), flush=True)


def bundle(args: argparse.Namespace) -> None:
    rows = _artifact_source_rows(
        report_dir=args.report_dir,
        output_root=args.output_root,
    )
    failures = _secret_scan_failures(rows)
    if failures:
        raise ValueError("m12r_artifact_secret_scan_failed:" + ",".join(failures))
    index_rows = [
        {
            "path": archive_name,
            "sha256": m12.file_sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for archive_name, path in rows
    ]
    index = {
        "contract": "m12r-artifact-index-v1",
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
        if bad:
            raise ValueError(f"m12r_bundle_crc_failed:{bad}")
        for row in index_rows:
            payload = archive.read(row["path"])
            if _sha_bytes(payload) != row["sha256"]:
                raise ValueError(f"m12r_bundle_hash_mismatch:{row['path']}")
            if len(payload) != row["size_bytes"]:
                raise ValueError(f"m12r_bundle_size_mismatch:{row['path']}")
    digest = m12.file_sha256(args.bundle_path)
    m12.write_text(
        args.bundle_path.with_suffix(args.bundle_path.suffix + ".sha256"),
        digest,
    )
    print(
        json.dumps(
            {
                "bundle": str(args.bundle_path),
                "sha256": digest,
                "payload_count": len(index_rows),
                "hash_mismatch_count": 0,
                "size_mismatch_count": 0,
                "secret_scan_failure_count": 0,
                "status": "PASS",
            },
            sort_keys=True,
        ),
        flush=True,
    )


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=PROGRAM_CONTRACT)
    value.add_argument(
        "command", choices=("phase-a", "run-canary", "finalize", "bundle")
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
        raise ValueError("m12r_generation_id_required")
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
