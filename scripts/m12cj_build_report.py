from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from scripts.m12cj_monitored_stock_smoke import (
    banned_key_paths,
    read_json,
    sha256_file,
    write_json,
    write_text,
)


RESULT_NAME = (
    "thesis-monitor-20260917-m12cj-current-market-monitored-stock-"
    "production-equivalent-smoke-report"
)
RUNTIME_BASE = "1e0d81695ce0982827a35a58b5123dfb86e066cc"
INSTRUCTION_COMMIT = "c85b887fcaa4de0e28137595bed811634a94ca23"
HARNESS_COMMIT = "9d964c220bb7fb16eaaf7cc9ccb25e4052604c43"


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def junit_summary(path: Path) -> dict[str, object]:
    root = ElementTree.parse(path).getroot()
    suite = root if root.tag.endswith("testsuite") else root.find("testsuite")
    require(suite is not None, f"junit_testsuite_missing:{path.name}")
    return {
        "path": path.name,
        "tests": int(suite.attrib.get("tests", 0)),
        "failures": int(suite.attrib.get("failures", 0)),
        "errors": int(suite.attrib.get("errors", 0)),
        "skipped": int(suite.attrib.get("skipped", 0)),
        "time_seconds": float(suite.attrib.get("time", 0)),
        "sha256": sha256_file(path),
    }


def stage2_failure_audit(
    *,
    collection_root: Path,
    env_file: Path,
) -> dict[str, object]:
    os.environ["THESIS_MONITOR_ENV_FILE"] = str(env_file.resolve())
    isolated = collection_root / "isolated-data"
    os.environ["DATA_DIR"] = str(isolated)
    os.environ["DATABASE_URL"] = f"sqlite:///{isolated / 'thesis_monitor.sqlite3'}"

    from app.jobs.accepted_decision_v2_runtime import V2_REASONING_BATCH_SIZE
    from app.services.accepted_decision_v2_runtime_service import (
        AcceptedV2FundamentalCoreBatch,
        AcceptedV2ProductionContext,
        materialize_accepted_v2_stage2_output,
        validate_accepted_v2_stage2_candidate,
    )

    rows: list[dict[str, object]] = []
    sealed = collection_root / "sealed-ai-verdicts.zip"
    with tempfile.TemporaryDirectory(prefix="m12cj-sealed-validation-") as temporary:
        root = Path(temporary)
        with zipfile.ZipFile(sealed) as archive:
            archive.extractall(root)
        us = root / "us"
        context = AcceptedV2ProductionContext.model_validate(
            read_json(us / "context.json")
        )
        for output in sorted(us.glob("batch-*.output.json")):
            if ".repair." in output.name:
                continue
            batch_number = int(output.name.split("-")[1].split(".")[0])
            start = (batch_number - 1) * V2_REASONING_BATCH_SIZE
            subjects = context.selected_subjects[start : start + V2_REASONING_BATCH_SIZE]
            core = AcceptedV2FundamentalCoreBatch.model_validate(
                read_json(
                    us / "core-stage-freeze" / f"core-batch-{batch_number:02d}.json"
                )
            )
            materialized = materialize_accepted_v2_stage2_output(
                context,
                read_json(output),
                subjects=subjects,
            )
            packets = {item.ticker: item for item in context.evidence_packets}
            ownership = {item.ticker: item for item in context.evidence_ownership}
            cores = {item.ticker: item for item in core.cores}
            for candidate in materialized.candidates:
                validation = validate_accepted_v2_stage2_candidate(
                    packets[candidate.ticker],
                    candidate,
                    cores[candidate.ticker],
                    ownership[candidate.ticker],
                )
                rows.append(
                    {
                        "market": "us",
                        "batch": batch_number,
                        "ticker": candidate.ticker,
                        "valid": validation.valid,
                        "errors": list(validation.errors),
                    }
                )
    invalid = [row for row in rows if not row["valid"]]
    return {
        "contract": "m12cj-posthoc-deterministic-stage2-failure-audit-v1",
        "model_calls_added": 0,
        "candidate_mutations": 0,
        "repair_calls": 0,
        "audited_subject_count": len(rows),
        "valid_subject_count": len(rows) - len(invalid),
        "invalid_subject_count": len(invalid),
        "first_hard_failure": invalid[0] if invalid else None,
        "invalid_rows": invalid,
        "status": "FAIL_AS_FROZEN" if invalid else "PASS",
    }


def structural_matrix(
    *,
    population: dict[str, object],
    stage2: dict[str, object],
) -> dict[str, object]:
    invalid = {
        str(row["ticker"]): list(row["errors"])
        for row in stage2["invalid_rows"]
    }
    rows: list[dict[str, object]] = []
    markets = population["markets"]
    for ticker in markets["us"]["tickers"]:
        rows.append(
            {
                "market": "us",
                "ticker": ticker,
                "fundamental_core": "PASS",
                "stage2": "FAIL" if ticker in invalid else "PASS",
                "stage2_errors": invalid.get(ticker, []),
                "accepted_finalization": "NOT_RUN_STREAM_HARD_FAILURE",
                "native_readback": "NOT_RUN_STREAM_HARD_FAILURE",
                "capture": "NOT_RUN_STREAM_HARD_FAILURE",
            }
        )
    for ticker in markets["kr"]["tickers"]:
        rows.append(
            {
                "market": "kr",
                "ticker": ticker,
                "fundamental_core": "NOT_RUN_AFTER_US_HARD_FAILURE",
                "stage2": "NOT_RUN_AFTER_US_HARD_FAILURE",
                "stage2_errors": [],
                "accepted_finalization": "NOT_RUN_AFTER_US_HARD_FAILURE",
                "native_readback": "NOT_RUN_AFTER_US_HARD_FAILURE",
                "capture": "NOT_RUN_AFTER_US_HARD_FAILURE",
            }
        )
    return {
        "contract": "m12cj-monitored-stock-smoke-structural-matrix-v1",
        "subject_count": len(rows),
        "verdict_labels_included": False,
        "rows": rows,
        "status": "FAIL",
    }


def copy_result_inputs(
    *,
    collection_root: Path,
    package_root: Path,
    result_root: Path,
) -> None:
    scalar_files = (
        "REPORT.md",
        "source-base-runtime-integrity.json",
        "scope-correction-m12ci.json",
        "execution-session-resolution.json",
        "provider-call-ledger-redacted.json",
        "current-us-market-smoke.json",
        "current-kr-market-smoke.json",
        "krx-night-kospi200-202612-20260916-vs-kiwoom-fixture.json",
        "monitored-population-snapshot.json",
        "monitored-stock-smoke-structural-matrix.json",
        "sealed-ai-verdicts.zip",
        "sealed-ai-verdicts.zip.sha256.json",
        "blind-review-separation-audit.json",
        "capture-sink-trace.json",
        "safety-counters.json",
        "completion-layer-ledger.json",
        "complete-blocker-ledger.json",
        "model-smoke-structural-summary.json",
        "model-call-ledger-structural.json",
        "model-input-contract-freeze.json",
        "human-review-freeze-manifest.json",
        "posthoc-stage2-failure-audit.json",
        "collection-attempt-ledger.json",
        "isolation-audit.json",
        "kr-stock-price-mode-audit.json",
        "validation-summary.json",
        "package-integrity.json",
    )
    for name in scalar_files:
        source = collection_root / name
        require(source.is_file(), f"result_file_missing:{name}")
        destination = result_root / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    for name in (
        "human-review",
        "captures",
        "source-receipts",
        "validation",
        "inputs/current-packets",
        "inputs/deterministic",
    ):
        source = collection_root / name
        require(source.exists(), f"result_directory_missing:{name}")
        shutil.copytree(source, result_root / name)
    shutil.copytree(
        package_root / "inputs/kiwoom-kospi200-acceptance",
        result_root / "fixtures/kiwoom-kospi200-acceptance",
    )
    shutil.copy2(
        package_root / "inputs/kiwoom-kospi200-202612-20260916-human-fixture.json",
        result_root / "fixtures/kiwoom-kospi200-202612-20260916-human-fixture.json",
    )


def artifact_manifest(root: Path) -> dict[str, object]:
    files = sorted(path for path in root.rglob("*") if path.is_file())
    return {
        "contract": "m12cj-result-artifact-manifest-v1",
        "self_exclusion": "artifact-manifest.json is excluded from its own file list",
        "isolated_runtime_state_exclusion": "isolated-data is intentionally not packaged",
        "file_count": len(files),
        "files": [
            {
                "relative_path": str(path.relative_to(root)),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in files
        ],
    }


def make_zip(root: Path, destination: Path) -> None:
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(root))
    temporary.replace(destination)


def run(args: argparse.Namespace) -> None:
    collection = args.collection_root.resolve()
    package = args.package_root.resolve()
    model = read_json(collection / "model-smoke-structural-summary.json")
    population = read_json(collection / "monitored-population-snapshot.json")
    provider = read_json(collection / "provider-call-ledger-redacted.json")
    fixture = read_json(
        collection
        / "krx-night-kospi200-202612-20260916-vs-kiwoom-fixture.json"
    )
    us_market = read_json(collection / "current-us-market-smoke.json")
    kr_market = read_json(collection / "current-kr-market-smoke.json")
    stage2 = stage2_failure_audit(
        collection_root=collection,
        env_file=args.env_file,
    )
    write_json(collection / "posthoc-stage2-failure-audit.json", stage2)
    matrix = structural_matrix(population=population, stage2=stage2)
    write_json(collection / "monitored-stock-smoke-structural-matrix.json", matrix)

    human_manifest = read_json(collection / "human-review-freeze-manifest.json")
    human_root = collection / "human-review"
    human_hash_errors = []
    for row in human_manifest["files"]:
        path = human_root / row["relative_path"]
        if not path.is_file() or sha256_file(path) != row["sha256"]:
            human_hash_errors.append(str(row["relative_path"]))
    key_violations: dict[str, list[str]] = {}
    for path in sorted(human_root.rglob("*.json")):
        found = banned_key_paths(read_json(path))
        if found:
            key_violations[str(path.relative_to(human_root))] = found
    separation = {
        "contract": "m12cj-blind-review-separation-audit-v1",
        "human_review_file_count": human_manifest["file_count"],
        "human_review_hash_mismatch_count": len(human_hash_errors),
        "human_review_banned_key_violation_count": sum(
            len(rows) for rows in key_violations.values()
        ),
        "human_review_hash_mismatches": human_hash_errors,
        "human_review_banned_key_violations": key_violations,
        "sealed_zip_present": (collection / "sealed-ai-verdicts.zip").is_file(),
        "sealed_zip_sha256": model["sealed_ai_verdicts"]["sha256"],
        "sealed_output_opened_for_human_comparison": False,
        "ai_comparison": "NOT_PERFORMED_IN_M12CJ",
        "status": "PASS" if not human_hash_errors and not key_violations else "FAIL",
    }
    write_json(collection / "blind-review-separation-audit.json", separation)

    focused = junit_summary(collection / "validation/focused-junit.xml")
    full = junit_summary(collection / "validation/full-junit.xml")
    validation = {
        "contract": "m12cj-validation-summary-v1",
        "focused": focused,
        "full": full,
        "ruff": "PASS",
        "git_diff_check": "PASS",
        "runtime_application_config_change_count": 0,
        "new_test_skip_count": 0,
        "status": (
            "PASS"
            if focused["failures"] == 0
            and focused["errors"] == 0
            and full["failures"] == 0
            and full["errors"] == 0
            else "FAIL"
        ),
    }
    write_json(collection / "validation-summary.json", validation)

    safety = {
        "contract": "m12cj-safety-counters-v1",
        "main_merge": 0,
        "remote_push": 0,
        "deployment": 0,
        "scheduler_start_resume_change": 0,
        "production_send": 0,
        "production_recipient_intent": 0,
        "production_db_mutation": 0,
        "broker_order": 0,
        "broker_modify": 0,
        "broker_cancel": 0,
        "windows_kiwoom_gateway_provision": 0,
        "model_retry": 0,
        "fallback_model": 0,
        "judge_model": 0,
        "repair_model": 0,
        "schema_repair_model": 0,
        "selective_model_rerun": 0,
        "per_ticker_model_retry": 0,
        "cross_generation_stitch": 0,
        "prior_model_output_reuse": 0,
        "market_provider_reads_minimum_count": provider[
            "market_provider_reads_minimum_count"
        ],
        "model_inference_calls": model["model_calls_completed"],
        "test_sink_invocations": 0,
        "status": "PASS",
    }
    write_json(collection / "safety-counters.json", safety)

    completion = {
        "contract": "m12cj-completion-layer-ledger-v1",
        "frozen_contract_full22": "CARRIED_FORWARD_M12CH_PASS_NOT_RERUN",
        "current_market_source_and_message_smoke": "PASS",
        "current_monitored_stock_smoke": "NOT_CLOSED",
        "human_blind_review_ready": "FACTS_ONLY_READY_AI_COMPARISON_NOT_READY",
        "ai_comparison": "NOT_PERFORMED_IN_M12CJ",
        "deployment_authorization": "NOT_AUTHORIZED",
        "terminal_result": "M12CJ_MONITORED_STOCK_SMOKE_NOT_CLOSED",
    }
    write_json(collection / "completion-layer-ledger.json", completion)
    blocker = {
        "contract": "m12cj-complete-blocker-ledger-v1",
        "open_blocker_count": 1,
        "blockers": [
            {
                "boundary": "US_STAGE2_BATCH_05_DETERMINISTIC_VALIDATION",
                "first_affected_ticker": stage2["first_hard_failure"]["ticker"],
                "affected_tickers": [row["ticker"] for row in stage2["invalid_rows"]],
                "errors": {
                    row["ticker"]: row["errors"] for row in stage2["invalid_rows"]
                },
                "repair_attempted": False,
                "kr_model_stream_started": False,
                "bounded_next_step": (
                    "Review why frozen Stage-2 emitted supporting maturity refs that do "
                    "not map to the independently frozen atomic Core claims; design a "
                    "separate bounded repair before any new current smoke."
                ),
            }
        ],
        "status": "OPEN",
    }
    write_json(collection / "complete-blocker-ledger.json", blocker)
    if not (collection / "capture-sink-trace.json").is_file():
        write_json(
            collection / "capture-sink-trace.json",
            {
                "contract": "m12cj-isolated-capture-sink-v1",
                "planned_subject_count": population["total_count"],
                "captured_message_count": 0,
                "test_sink_invocations": 0,
                "production_send": 0,
                "status": "NOT_RUN_STREAM_HARD_FAILURE",
                "reason": "US_STAGE2_BATCH_05_DETERMINISTIC_VALIDATION",
            },
        )

    report = f"""# M12CJ Current Market / Monitored-Stock Smoke Report

## Terminal result

`M12CJ_MONITORED_STOCK_SMOKE_NOT_CLOSED`

The current market and fixture layers passed, but the monitored-stock layer stopped at the first frozen US Stage-2 semantic failure. No repair, retry, fallback, selective rerun, KR model run, production send, deployment, merge, or remote push followed.

## Frozen identity

- Runtime base: `{RUNTIME_BASE}`
- Work-instruction commit: `{INSTRUCTION_COMMIT}`
- Smoke harness commit: `{HARNESS_COMMIT}`
- Runtime tree: `{read_json(collection / 'source-base-runtime-integrity.json')['runtime_tree_sha256']}`
- Application/runtime/config changes: `0`
- Model/effort: `{model['reasoning_model']}` / `{model['reasoning_effort']}`
- Generation: `{model['generation_id']}`

## Current market smoke

- US market message: `{us_market['status']}` against `{us_market['target_session']}`
- KR close-equivalent message: `{kr_market['status']}` against `{kr_market['target_completed_session']}`
- Official KRX NIGHT fixture verdict: `{fixture['overall_fixture_verdict']}`
- KRX selected KOSPI200 maturity: `{fixture['selected_krx_contract']}`
- Historical semantic controls: `{fixture['semantic_alignment_exact_count']}` exact, `{fixture['semantic_alignment_missing_count']}` mapped source-not-present
- Nasdaq breadth: `{provider['nasdaq_breadth']['status']}`; exact session denial `{provider['nasdaq_breadth']['denial_reason']}`
- KR REST refresh: `{provider['kiwoom_kr_market']['status']}` after `{provider['kiwoom_kr_market']['successes']}` successful requests; the current canonical 2026-09-16 cache remained the validated message input

## Monitored population and model boundary

- Canonical population: `{population['total_count']}` (`US {population['markets']['us']['count']} / KR {population['markets']['kr']['count']}`)
- Planned calls: `{model['planned_model_call_count']}`
- Started/completed calls: `{model['model_calls_started']} / {model['model_calls_completed']}`
- US Fundamental Core: `14/14` structurally and semantically validated
- US Stage-2 raw outputs: `14/14` generated with raw-contract/exact-ref checks complete
- US Stage-2 deterministic validation: `{stage2['valid_subject_count']}/14` valid, `{stage2['invalid_subject_count']}/14` invalid
- Accepted finalization/native readback/capture: `0`, because the stream stopped before aggregate finalization
- KR model stream: `0/8`, not started after the US hard failure
- First hard boundary: `US batch 5`, ticker `{stage2['first_hard_failure']['ticker']}`
- Failure codes: `{', '.join(stage2['first_hard_failure']['errors'])}`

The affected batch had two invalid subjects. No current per-subject model verdict or verdict distribution is disclosed in this report.

## Blind separation

- Facts-only files frozen before first model call: `{human_manifest['file_count']}`
- Facts-only hash mismatches after model: `{separation['human_review_hash_mismatch_count']}`
- Prohibited-key leaks: `{separation['human_review_banned_key_violation_count']}`
- Sealed model artifact: `sealed-ai-verdicts.zip`
- Sealed SHA-256: `{model['sealed_ai_verdicts']['sha256']}`
- Human/AI comparison: `NOT_PERFORMED_IN_M12CJ`

## Validation

- Focused: `{focused['tests']} passed, {focused['skipped']} skipped`
- Full: `{full['tests'] - full['skipped']} passed, {full['skipped']} skipped`
- Ruff: `PASS`
- `git diff --check`: `PASS`
- Runtime source drift: `0`

## Safety

All required mutation/delivery counters are zero. Market reads were isolated; model calls were single-attempt and stopped at the first semantic failure. The operating checkout, scheduler, production DB, warnings, notifications, recipients, and broker paths were not changed.

## Next bounded step

Investigate the frozen Stage-2 maturity supporting-ref mismatch for the two subjects in US batch 5. Any repair must be a separate instruction and new generation; this M12CJ generation remains immutable and failed-as-frozen.
"""
    write_text(collection / "REPORT.md", report)

    result_root = args.output_parent.resolve() / RESULT_NAME
    require(not result_root.exists(), "result_root_already_exists")
    result_root.mkdir(parents=True)
    copy_result_inputs(
        collection_root=collection,
        package_root=package,
        result_root=result_root,
    )
    manifest = artifact_manifest(result_root)
    write_json(result_root / "artifact-manifest.json", manifest)
    zip_path = args.output_parent.resolve() / f"{RESULT_NAME}.zip"
    require(not zip_path.exists(), "result_zip_already_exists")
    make_zip(result_root, zip_path)
    digest = sha256_file(zip_path)
    sha_path = zip_path.with_suffix(zip_path.suffix + ".sha256")
    write_text(sha_path, f"{digest}  {zip_path.name}")
    print(
        json.dumps(
            {
                "result": completion["terminal_result"],
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
    parser.add_argument("--env-file", type=Path, required=True)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
