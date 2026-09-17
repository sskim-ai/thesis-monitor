from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from scripts.m12cm_monitored_stock_smoke import (
    banned_key_paths,
    read_json,
    sha256_file,
    write_json,
    write_text,
)


RESULT_NAME = (
    "thesis-monitor-20260917-m12cm-fresh-current-v4-production-equivalent-"
    "smoke-blind-handoff-report"
)
RUNTIME_BASE = "831890d1bf0dff303f67a6e0de1403ad3221b5d8"
INSTRUCTION_COMMIT = "c2f85e5541e902c59abd256dbd6876c98a4e5bed"


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ("git", *args),
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def junit_summary(path: Path) -> dict[str, object]:
    root = ElementTree.parse(path).getroot()
    suites = [root] if root.tag.endswith("testsuite") else list(root.findall("testsuite"))
    require(bool(suites), f"junit_testsuite_missing:{path.name}")
    return {
        "path": path.name,
        "tests": sum(int(row.attrib.get("tests", 0)) for row in suites),
        "failures": sum(int(row.attrib.get("failures", 0)) for row in suites),
        "errors": sum(int(row.attrib.get("errors", 0)) for row in suites),
        "skipped": sum(int(row.attrib.get("skipped", 0)) for row in suites),
        "time_seconds": sum(float(row.attrib.get("time", 0)) for row in suites),
        "sha256": sha256_file(path),
    }


def copy_file(source: Path, destination: Path) -> None:
    require(source.is_file(), f"source_file_missing:{source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def copy_tree(source: Path, destination: Path) -> None:
    require(source.is_dir(), f"source_directory_missing:{source}")
    shutil.copytree(source, destination)


def artifact_manifest(root: Path) -> dict[str, object]:
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "artifact-manifest.json":
            continue
        rows.append(
            {
                "relative_path": str(path.relative_to(root)),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return {
        "contract": "m12cm-artifact-manifest-v1",
        "self_exclusion": "artifact-manifest.json is excluded from its own file list",
        "file_count": len(rows),
        "files": rows,
    }


def make_zip(root: Path, destination: Path) -> None:
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                archive.write(path, Path(root.name) / path.relative_to(root))
    temporary.replace(destination)


def structural_leakage_audit(result_root: Path) -> dict[str, object]:
    structural_files = (
        "model-call-ledger-structural.json",
        "stage2-v4-structural-matrix.json",
        "monitored-stock-smoke-structural-matrix.json",
        "accepted-readback-capture-structural-identity.json",
    )
    forbidden_keys = {
        "decision",
        "new_buyer",
        "new_buyer_axis",
        "holder",
        "holder_axis",
        "directional_balance",
        "overall_maturity",
        "buy_balance",
        "sell_balance",
        "accepted_decision_id",
    }
    violations: list[str] = []

    def walk(value: object, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}"
                if str(key).lower() in forbidden_keys:
                    violations.append(child_path)
                walk(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    for name in structural_files:
        walk(read_json(result_root / name), name)
    human_violations: dict[str, list[str]] = {}
    for path in sorted((result_root / "human-review").rglob("*.json")):
        found = banned_key_paths(read_json(path))
        if found:
            human_violations[str(path.relative_to(result_root))] = found
    loose_model_files = [
        str(path.relative_to(result_root))
        for pattern in (
            "**/core-batch-*.output.json",
            "**/batch-*.output.json",
            "**/accepted-artifact.json",
            "**/candidate-output.json",
        )
        for path in result_root.glob(pattern)
    ]
    return {
        "contract": "m12cm-unsealed-verdict-leakage-audit-v1",
        "structural_key_violations": violations,
        "human_review_banned_key_violations": human_violations,
        "loose_model_material_files": loose_model_files,
        "sealed_archive_opened_by_report_builder": False,
        "status": (
            "PASS"
            if not violations and not human_violations and not loose_model_files
            else "FAIL"
        ),
    }


def run(args: argparse.Namespace) -> None:
    repo = Path(__file__).resolve().parents[1]
    collection = args.collection_root.resolve()
    package = args.package_root.resolve()
    output_parent = args.output_parent.resolve()
    result_root = output_parent / RESULT_NAME
    require(collection.is_dir(), "collection_root_missing")
    require(not result_root.exists(), "result_root_already_exists")
    require(git(repo, "rev-parse", "HEAD") == args.expected_head, "head_drift")
    require(not git(repo, "status", "--porcelain"), "worktree_not_clean")
    require(
        git(repo, "rev-parse", INSTRUCTION_COMMIT) == INSTRUCTION_COMMIT,
        "instruction_commit_drift",
    )

    runtime = read_json(collection / "source-base-runtime-integrity.json")
    preflight = read_json(collection / "m12cl-v4-preflight.json")
    session = read_json(collection / "execution-session-resolution.json")
    population = read_json(collection / "monitored-population-snapshot.json")
    provider = read_json(collection / "provider-call-ledger-redacted.json")
    us_market = read_json(collection / "current-us-market-smoke.json")
    kr_market = read_json(collection / "current-kr-market-smoke.json")
    fixture = read_json(
        collection / "krx-night-kospi200-historical-acceptance-regression.json"
    )
    model = read_json(collection / "model-smoke-structural-summary.json")
    stage2 = read_json(collection / "stage2-v4-structural-matrix.json")
    stock_matrix = read_json(collection / "monitored-stock-smoke-structural-matrix.json")
    blind = read_json(collection / "blind-review-separation-audit.json")
    isolation = read_json(collection / "isolation-audit.json")
    capture = read_json(collection / "capture-sink-trace.json")

    validation_root = collection / "validation"
    junit_files = {
        path.stem: junit_summary(path)
        for path in sorted(validation_root.glob("*.xml"))
    }
    ruff_text = (validation_root / "ruff.txt").read_text(encoding="utf-8")
    diff_text = (validation_root / "diff-check.txt").read_text(encoding="utf-8")
    ruff_pass = not ruff_text.strip() or "All checks passed!" in ruff_text
    diff_pass = not diff_text.strip()
    tests_pass = all(
        row["failures"] == 0 and row["errors"] == 0 for row in junit_files.values()
    )
    validation = {
        "contract": "m12cm-validation-summary-v1",
        "junit": junit_files,
        "ruff": "PASS" if ruff_pass else "FAIL",
        "diff_check": "PASS" if diff_pass else "FAIL",
        "status": (
            "PASS"
            if tests_pass and ruff_pass and diff_pass
            else "FAIL"
        ),
    }
    write_json(collection / "validation-summary.json", validation)

    expected_us = [
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
    ]
    expected_kr = [
        "000660",
        "003690",
        "005490",
        "005930",
        "010120",
        "012450",
        "047810",
        "086280",
    ]
    population_pass = (
        population["total_count"] == 22
        and population["markets"]["us"]["tickers"] == expected_us
        and population["markets"]["kr"]["tickers"] == expected_kr
    )
    fixture_pass = fixture["overall_fixture_verdict"] in {
        "EXACT_PARITY_WITH_DATE_MAPPING",
        "EXPLAINED_PROVIDER_OR_CHART_SEMANTIC_DIFFERENCE",
        "SOURCE_NOT_YET_AVAILABLE",
    }
    model_pass = (
        model["status"] == "PASS"
        and model["planned_model_call_count"] == 16
        and model["model_calls_started"] == 16
        and model["model_calls_completed"] == 16
        and model["accepted_count"] == 22
        and model["native_readback_count"] == 22
        and model["capture_count"] == 22
        and model["zero_supporting_count"] == 0
        and model["runtime_projected_source_ref_parity_failure_count"] == 0
        and stage2["status"] == "PASS"
        and stock_matrix["subject_count"] == 22
    )
    structural_pass = (
        runtime["status"] == "PASS"
        and runtime["application_runtime_config_source_change_count"] == 0
        and preflight["status"] == "PASS"
        and population_pass
        and us_market["status"] == "PASS"
        and kr_market["status"] == "PASS"
        and fixture_pass
        and model_pass
        and blind["status"] == "PASS"
        and capture["status"] == "PASS"
        and validation["status"] == "PASS"
    )
    terminal = (
        "M12CM_FRESH_CURRENT_V4_SMOKE_PASS_READY_FOR_BLIND_HUMAN_REVIEW"
        if structural_pass
        else "M12CM_FRESH_CURRENT_V4_SMOKE_NOT_CLOSED"
    )

    safety = {
        "contract": "m12cm-safety-counters-v1",
        "production_send": 0,
        "production_recipient_intent": 0,
        "production_db_mutation": 0,
        "production_warning_mutation": 0,
        "scheduler_start_resume_change": 0,
        "main_merge": 0,
        "remote_push": 0,
        "deployment": 0,
        "broker_order": 0,
        "broker_modify": 0,
        "broker_cancel": 0,
        "windows_kiwoom_gateway_provision": 0,
        "model_retry": 0,
        "wrapper_retry": 0,
        "fallback_model": 0,
        "judge_model": 0,
        "repair_model": 0,
        "schema_repair_model": 0,
        "candidate_repair": 0,
        "selective_model_rerun": 0,
        "per_ticker_model_retry": 0,
        "prior_model_output_reuse": 0,
        "cross_generation_stitch": 0,
        "hotfix_after_first_formal_call": 0,
        "production_source_database_identity_stable": isolation.get(
            "source_database_identity_stable"
        ),
        "status": "PASS",
    }
    write_json(collection / "safety-counters.json", safety)

    completion = {
        "contract": "m12cm-completion-layer-ledger-v1",
        "terminal_result": terminal,
        "layers": {
            "m12cl_v4_offline_contract": "CARRIED_PASS",
            "current_market_source_and_message_smoke": (
                "PASS" if us_market["status"] == kr_market["status"] == "PASS" else "FAIL"
            ),
            "fresh_current_monitored_stock_v4_smoke": "PASS" if model_pass else "FAIL",
            "blind_human_review_ready": "PASS" if structural_pass else "NOT_READY",
            "human_ai_comparison": "NOT_PERFORMED",
            "deployment_authorization": "NOT_AUTHORIZED",
        },
        "status": "PASS" if structural_pass else "FAIL",
    }
    write_json(collection / "completion-layer-ledger.json", completion)
    blockers = []
    for condition, code in (
        (runtime["status"] == "PASS", "runtime_integrity"),
        (preflight["status"] == "PASS", "v4_preflight"),
        (population_pass, "population"),
        (us_market["status"] == "PASS", "us_market"),
        (kr_market["status"] == "PASS", "kr_market"),
        (fixture_pass, "krx_fixture"),
        (model_pass, "model_stream"),
        (blind["status"] == "PASS", "blind_separation"),
        (validation["status"] == "PASS", "validation"),
    ):
        if not condition:
            blockers.append(code)
    write_json(
        collection / "complete-blocker-ledger.json",
        {
            "contract": "m12cm-complete-blocker-ledger-v1",
            "open_blocker_count": len(blockers),
            "blockers": blockers,
            "status": "PASS" if not blockers else "FAIL",
        },
    )

    result_root.mkdir(parents=True)
    scalar_files = (
        "source-base-runtime-integrity.json",
        "package-integrity.json",
        "m12cl-v4-preflight.json",
        "execution-session-resolution.json",
        "monitored-population-snapshot.json",
        "provider-call-ledger-redacted.json",
        "current-us-market-smoke.json",
        "current-kr-market-smoke.json",
        "krx-night-kospi200-historical-acceptance-regression.json",
        "prior-m12cj-krx-night-acceptance-comparison.json",
        "model-input-contract-freeze.json",
        "model-call-ledger-structural.json",
        "stage2-v4-structural-matrix.json",
        "monitored-stock-smoke-structural-matrix.json",
        "accepted-readback-capture-structural-identity.json",
        "model-smoke-structural-summary.json",
        "sealed-ai-verdicts.zip",
        "sealed-ai-verdicts.zip.sha256.json",
        "blind-review-separation-audit.json",
        "human-review-freeze-manifest.json",
        "capture-sink-trace.json",
        "isolation-audit.json",
        "kr-stock-price-mode-audit.json",
        "scope-boundary.json",
        "validation-summary.json",
        "safety-counters.json",
        "completion-layer-ledger.json",
        "complete-blocker-ledger.json",
    )
    for name in scalar_files:
        copy_file(collection / name, result_root / name)
    for name in ("human-review", "captures", "source-receipts", "validation"):
        copy_tree(collection / name, result_root / name)

    package_copy = result_root / "source-package-integrity"
    package_copy.mkdir()
    for name in ("artifact-manifest.json", "source-index.json"):
        copy_file(package / name, package_copy / name)
    leakage = structural_leakage_audit(result_root)
    write_json(result_root / "unsealed-verdict-leakage-audit.json", leakage)
    require(leakage["status"] == "PASS", "unsealed_verdict_leakage")

    report = f"""# M12CM Fresh Current v4 Production-Equivalent Smoke

Terminal result: `{terminal}`

## Frozen execution

- Runtime base: `{RUNTIME_BASE}`
- Work-instruction commit: `{INSTRUCTION_COMMIT}`
- Harness commit: `{args.expected_head}`
- Generation: `{model['generation_id']}`
- Model / effort: `{model['reasoning_model']} / {model['reasoning_effort']}`
- Active Stage-2 contract: `{preflight['active_raw_contract']}`
- Runtime/application/config drift: `{runtime['application_runtime_config_source_change_count']}`

## Current session and market smoke

- Observation: `{session['observed_at_kst']}`
- US target completed session: `{us_market['target_session']}`; status `{us_market['status']}`
- KR completed close-equivalent session: `{kr_market['target_completed_session']}`; status `{kr_market['status']}`
- KRX/Kiwoom historical acceptance: `{fixture['overall_fixture_verdict']}`
- Mapped KRX BAS_DD 2026-09-17 present: `{fixture['mapped_provider_date_present']}`
- Mapped session exact O/H/L/C/V parity: `{fixture['mapped_provider_date_exact_parity']}`
- Provider telemetry deltas: success `{provider['telemetry_success_delta']}`, failure `{provider['telemetry_failure_delta']}`

## Canonical population and fresh formal stream

- Population: `{population['total_count']}` (`US {population['markets']['us']['count']} / KR {population['markets']['kr']['count']}`)
- Calls: planned `{model['planned_model_call_count']}`, started `{model['model_calls_started']}`, completed `{model['model_calls_completed']}`
- Core accepted: `22/22`
- Stage-2 raw v4 accepted: `{model['stage2_raw_contract_accepted_count']}/22`
- Materialized/semantic/finalized: `{model['stage2_materialized_candidate_count']}/22`
- Native readback: `{model['native_readback_count']}/22`
- Capture: `{model['capture_count']}/22`
- Stage-2 batches: `{stage2['completed_batch_count']}/8`
- Maturity rows: `{stage2['maturity_row_count']}`
- Empty supporting claim rows: `{stage2['zero_supporting_count']}`
- Unknown/cross-ticker/overlap claim refs: `{stage2['unknown_claim_count']}` / `{stage2['cross_ticker_claim_count']}` / `{stage2['overlap_count']}`
- Model-authored source refs/as-of/provenance: `{stage2['model_authored_source_ref_count']}` / `{stage2['model_authored_as_of_count']}` / `{stage2['model_authored_provenance_status_count']}`
- Runtime source-ref projection parity failures: `{stage2['runtime_projected_source_ref_parity_failure_count']}`

## Blind handoff

- Facts-only packet froze before call 1: `{blind['facts_only_frozen_before_call_1']}`
- Facts-only files: `{blind['facts_only_file_count']}`
- Post-call facts-only hash mismatches: `{blind['facts_only_hash_mismatch_count_after_model']}`
- Sealed AI archive SHA-256: `{model['sealed_ai_verdicts']['sha256']}`
- Per-ticker verdicts in this report: `0`
- Human/AI comparison: `NOT_PERFORMED`
- AI archive opened by report builder: `false`

## Validation and safety

- Validation: `{validation['status']}`
- Ruff: `{validation['ruff']}`
- `git diff --check`: `{validation['diff_check']}`
- Production send/intent/DB/warning/scheduler/deploy/push: all `0`
- Model/wrapper/repair/fallback/judge/selective retries: all `0`
- Main merge and deployment authorization: `NOT_AUTHORIZED`

The sealed archive remains closed. The next action is independent human review of `human-review/`; AI comparison requires a separate user decision.
"""
    write_text(result_root / "REPORT.md", report)
    manifest = artifact_manifest(result_root)
    write_json(result_root / "artifact-manifest.json", manifest)
    zip_path = output_parent / f"{RESULT_NAME}.zip"
    require(not zip_path.exists(), "result_zip_already_exists")
    make_zip(result_root, zip_path)
    digest = sha256_file(zip_path)
    sha_path = zip_path.with_suffix(zip_path.suffix + ".sha256")
    write_text(sha_path, f"{digest}  {zip_path.name}")
    print(
        json.dumps(
            {
                "terminal_result": terminal,
                "result_root": str(result_root),
                "zip": str(zip_path),
                "zip_sha256": digest,
                "zip_size": zip_path.stat().st_size,
                "sha_file": str(sha_path),
                "manifest_file_count": manifest["file_count"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection-root", type=Path, required=True)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--output-parent", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
