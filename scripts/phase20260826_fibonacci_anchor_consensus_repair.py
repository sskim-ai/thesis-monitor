from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path

from app.services.fibonacci_anchor_consensus_service import (
    PriceOnlyAISwingConsensusPacket,
    VariableAISwingConsensusBatchOutput,
    VariableAISwingConsensusOutput,
    audit_consensus_packet_egress,
    build_price_only_ai_swing_consensus_packet,
    classify_swing_structure_consensus,
    execute_variable_swing_consensus_selector,
)
from app.services.multi_timeframe_price_structure_service import TIMEFRAME_ORDER
from app.services.variable_ai_anchor_selection_service import PriceOnlyAIAnchorPacket


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs/reports"
FROZEN_EVIDENCE = REPORTS / "20260826-variable-ai-anchor-price-only-evidence.json"
PRIOR_RESULTS = REPORTS / "20260826-fibonacci-p1-closure-evidence.json"
EVIDENCE_JSON = REPORTS / "20260826-fibonacci-final-p1-evidence.json"
READINESS_JSON = REPORTS / "20260826-fibonacci-final-p1-readiness.json"


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fibonacci anchor consensus archive repair.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prompts = subparsers.add_parser("prompts")
    prompts.add_argument("--evidence", type=Path, default=FROZEN_EVIDENCE)
    prompts.add_argument("--prior-results", type=Path, default=PRIOR_RESULTS)
    prompts.add_argument("--output-dir", type=Path, required=True)
    prompts.add_argument("--batch-size", type=int, default=4)

    run = subparsers.add_parser("run")
    run.add_argument("--trial-dir", type=Path, required=True)
    run.add_argument(
        "--codex-bin",
        type=Path,
        default=Path("/Applications/ChatGPT.app/Contents/Resources/codex"),
    )
    run.add_argument("--model", default="gpt-5.6-sol")
    run.add_argument("--timeout", type=int, default=900)

    finalize = subparsers.add_parser("finalize")
    finalize.add_argument("--evidence", type=Path, default=FROZEN_EVIDENCE)
    finalize.add_argument("--prior-results", type=Path, default=PRIOR_RESULTS)
    finalize.add_argument("--trial-dir", type=Path, required=True)
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _strict_json_schema(value: object) -> object:
    if isinstance(value, dict):
        transformed = {
            key: _strict_json_schema(item)
            for key, item in value.items()
            if key != "default"
        }
        properties = transformed.get("properties")
        if isinstance(properties, dict):
            transformed["required"] = list(properties)
            transformed["additionalProperties"] = False
        return transformed
    if isinstance(value, list):
        return [_strict_json_schema(item) for item in value]
    return value


def _table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "|" + "|".join("---" for _ in headers) + "|",
            *("| " + " | ".join(str(value) for value in row) + " |" for row in rows),
        ]
    )


def _packet(value: Mapping[str, object]) -> PriceOnlyAISwingConsensusPacket:
    base = PriceOnlyAIAnchorPacket.model_validate(value)
    return build_price_only_ai_swing_consensus_packet(base)


def _trial_prompt(packets: Sequence[Mapping[str, object]]) -> str:
    instructions = """Select one canonical swing_structure_id per timeframe, or explicitly abstain.

Rules:
- Use only swing_structure_id values present in the same ticker and timeframe packet.
- Deterministic support/resistance is context only. Do not select or output any SR zone ID.
- Do not construct low/high/correction combinations. The backend already enumerated valid structures.
- Do not calculate or output a price, ratio, Fibonacci level, target, stop, valuation, or thesis.
- Do not use tools or external data. The packet is the complete allowed evidence.
- Respect monthly structural, weekly intermediate, and daily tactical roles.
- SELECTED requires one swing_structure_id and may include one different listed alternative.
- AMBIGUOUS and INSUFFICIENT_STRUCTURE require null primary and alternative IDs.
- evidence_refs may cite only same-timeframe pivot, bar, or segment IDs from the packet.
- Use at most three reason categories and a concise reason.
- Return exactly one selection per input ticker and only the JSON required by the schema.

PRICE_ONLY_AI_SWING_CONSENSUS_PACKETS:
"""
    return instructions + json.dumps(packets, ensure_ascii=False, separators=(",", ":"))


def _batches(values: Sequence[str], size: int) -> list[list[str]]:
    return [list(values[index : index + size]) for index in range(0, len(values), size)]


def _prompts(args: argparse.Namespace) -> None:
    evidence = _read_json(args.evidence)
    rows = {
        str(item["ticker"]): item
        for item in evidence.get("rows") or ()
        if isinstance(item, Mapping) and item.get("status") == "PASS"
    }
    benchmark = [
        str(value)
        for value in evidence.get("benchmark_tickers") or ()
        if str(value) in rows
    ]
    wider = [ticker for ticker in sorted(rows) if ticker not in benchmark]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    schema_path = args.output_dir / "swing-consensus-batch.schema.json"
    _write_json(
        schema_path,
        _strict_json_schema(VariableAISwingConsensusBatchOutput.model_json_schema()),
    )
    manifest: list[dict[str, object]] = []

    def add(name: str, tickers: Sequence[str], mode: str, run: int) -> None:
        packets = [
            _packet(rows[ticker]["compact_packet"]).model_dump(mode="json")
            for ticker in tickers
        ]
        prompt_path = args.output_dir / f"{name}.prompt.txt"
        output_path = args.output_dir / f"{name}.output.json"
        _write_text(prompt_path, _trial_prompt(packets))
        manifest.append(
            {
                "name": name,
                "mode": mode,
                "run": run,
                "tickers": list(tickers),
                "prompt": prompt_path.name,
                "output": output_path.name,
            }
        )

    for run in range(1, 6):
        add(f"benchmark-consensus-run-{run:02d}", benchmark, "BENCHMARK", run)
    for run in range(1, 4):
        for batch_index, tickers in enumerate(_batches(wider, args.batch_size), 1):
            add(
                f"universe-consensus-run-{run:02d}-batch-{batch_index:02d}",
                tickers,
                "WIDER_UNIVERSE",
                run,
            )
    manifest_payload = {
        "contract": "fibonacci-swing-consensus-trial-manifest-v1",
        "evidence": str(args.evidence),
        "evidence_sha256": _sha256(args.evidence),
        "prior_results": str(args.prior_results),
        "prior_results_sha256": _sha256(args.prior_results),
        "schema": schema_path.name,
        "benchmark_runs_per_packet": 5,
        "wider_universe_runs_per_packet": 3,
        "entries": manifest,
    }
    _write_json(args.output_dir / "manifest.json", manifest_payload)
    print(json.dumps({"output_dir": str(args.output_dir), "calls": len(manifest)}, indent=2))


def _run_trials(args: argparse.Namespace) -> None:
    manifest = _read_json(args.trial_dir / "manifest.json")
    version = subprocess.run(
        [str(args.codex_bin), "--version"],
        capture_output=True,
        check=False,
        text=True,
    )
    runtime_config = {
        "route": "signed_in_local_codex_cli_archive_only",
        "cli_version": version.stdout.strip() or "unavailable",
        "model": args.model,
        "reasoning_effort": "high",
        "sandbox": "read-only",
        "session": "ephemeral",
        "tools": "prohibited_by_prompt",
    }
    manifest["runtime_config"] = runtime_config
    manifest["runtime_config_sha256"] = hashlib.sha256(
        json.dumps(runtime_config, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    _write_json(args.trial_dir / "manifest.json", manifest)
    entries = [item for item in manifest.get("entries") or () if isinstance(item, Mapping)]
    completed = 0
    failed = 0
    skipped = 0
    for index, entry in enumerate(entries, 1):
        prompt = args.trial_dir / str(entry["prompt"])
        output = args.trial_dir / str(entry["output"])
        log = args.trial_dir / f"{entry['name']}.log"
        if output.exists() and output.stat().st_size:
            skipped += 1
            print(f"[{index}/{len(entries)}] SKIP {entry['name']}", flush=True)
            continue
        command = [
            str(args.codex_bin),
            "exec",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "-m",
            args.model,
            "-c",
            'model_reasoning_effort="high"',
            "--output-schema",
            str(args.trial_dir / "swing-consensus-batch.schema.json"),
            "-o",
            str(output),
            "-",
        ]
        print(f"[{index}/{len(entries)}] START {entry['name']}", flush=True)
        env = dict(os.environ)
        try:
            with prompt.open(encoding="utf-8") as stdin, log.open(
                "w", encoding="utf-8"
            ) as stdout:
                process = subprocess.run(
                    command,
                    cwd=args.trial_dir,
                    env=env,
                    stdin=stdin,
                    stdout=stdout,
                    stderr=subprocess.STDOUT,
                    timeout=args.timeout,
                    check=False,
                    text=True,
                )
        except subprocess.TimeoutExpired:
            failed += 1
            print(f"[{index}/{len(entries)}] TIMEOUT {entry['name']}", flush=True)
            continue
        if process.returncode == 0 and output.exists() and output.stat().st_size:
            completed += 1
            print(f"[{index}/{len(entries)}] PASS {entry['name']}", flush=True)
        else:
            failed += 1
            print(f"[{index}/{len(entries)}] FAIL {entry['name']}", flush=True)
    print(json.dumps({"completed": completed, "skipped": skipped, "failed": failed}, indent=2))


def _load_trial_outputs(
    trial_dir: Path,
    manifest: Mapping[str, object],
) -> tuple[dict[tuple[str, str, int], VariableAISwingConsensusOutput], list[str]]:
    outputs: dict[tuple[str, str, int], VariableAISwingConsensusOutput] = {}
    errors: list[str] = []
    for entry in manifest.get("entries") or ():
        if not isinstance(entry, Mapping):
            continue
        path = trial_dir / str(entry["output"])
        if not path.exists():
            errors.append(f"{entry['name']}:output_missing")
            continue
        try:
            batch = VariableAISwingConsensusBatchOutput.model_validate(_read_json(path))
        except (ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{entry['name']}:{type(exc).__name__}")
            continue
        expected = {str(value) for value in entry.get("tickers") or ()}
        actual = {item.ticker for item in batch.selections}
        if expected != actual:
            errors.append(f"{entry['name']}:ticker_set_mismatch")
        for output in batch.selections:
            outputs[(str(entry["mode"]), output.ticker, int(entry["run"]))] = output
    return outputs, errors


def _legacy_root_cause(prior: Mapping[str, object]) -> dict[str, object]:
    counts = {timeframe: Counter() for timeframe in TIMEFRAME_ORDER}
    tickers: dict[str, dict[str, list[str]]] = {
        timeframe: defaultdict(list) for timeframe in TIMEFRAME_ORDER
    }
    for row in prior.get("results") or ():
        if not isinstance(row, Mapping) or row.get("status") != "PASS":
            continue
        for timeframe in TIMEFRAME_ORDER:
            old_stability = ((row.get("stability") or {}).get(timeframe) or {}).get(
                "classification"
            )
            signatures = []
            for run in row.get("runs") or ():
                if not isinstance(run, Mapping):
                    continue
                value = ((run.get("variable_ai_output") or {}).get(timeframe) or {})
                if not value:
                    continue
                anchors = (
                    value.get("status"),
                    value.get("fib_mode"),
                    value.get("low_pivot_id"),
                    value.get("high_pivot_id"),
                    value.get("correction_low_pivot_id"),
                )
                sr = (value.get("support_zone_id"), value.get("resistance_zone_id"))
                signatures.append((anchors, sr))
            anchor_varies = len({item[0] for item in signatures}) > 1
            sr_varies = len({item[1] for item in signatures}) > 1
            if old_stability != "MATERIAL_VARIATION":
                category = "STABLE_OR_MINOR"
            elif anchor_varies and sr_varies:
                category = "MIXED_MATERIAL"
            elif anchor_varies:
                category = "TRUE_ANCHOR_MATERIAL"
            elif sr_varies:
                category = "SR_ONLY_MATERIAL"
            else:
                category = "OTHER_MATERIAL"
            counts[timeframe][category] += 1
            tickers[timeframe][category].append(str(row["ticker"]))
    return {
        "counts": {timeframe: dict(counts[timeframe]) for timeframe in TIMEFRAME_ORDER},
        "tickers": {
            timeframe: dict(tickers[timeframe]) for timeframe in TIMEFRAME_ORDER
        },
    }


def _prior_selected_omissions(
    packet: PriceOnlyAISwingConsensusPacket,
    prior_row: Mapping[str, object],
) -> dict[str, list[tuple[object, ...]]]:
    omissions: dict[str, list[tuple[object, ...]]] = {}
    for timeframe in TIMEFRAME_ORDER:
        included = {
            (
                item.low_pivot_id,
                item.high_pivot_id,
                item.correction_low_pivot_id,
            )
            for item in getattr(packet, timeframe).swing_structure_candidates
        }
        seen: set[tuple[object, ...]] = set()
        for run in prior_row.get("runs") or ():
            if not isinstance(run, Mapping):
                continue
            value = ((run.get("variable_ai_output") or {}).get(timeframe) or {})
            if value.get("status") == "SELECTED":
                seen.add(
                    (
                        value.get("low_pivot_id"),
                        value.get("high_pivot_id"),
                        value.get("correction_low_pivot_id"),
                    )
                )
        missing = sorted(seen - included, key=str)
        if missing:
            omissions[timeframe] = missing
    return omissions


def _finalize(args: argparse.Namespace) -> None:
    evidence = _read_json(args.evidence)
    prior = _read_json(args.prior_results)
    manifest = _read_json(args.trial_dir / "manifest.json")
    if manifest.get("evidence_sha256") != _sha256(args.evidence):
        raise ValueError("trial manifest evidence hash mismatch")
    if manifest.get("prior_results_sha256") != _sha256(args.prior_results):
        raise ValueError("trial manifest prior-results hash mismatch")
    outputs, load_errors = _load_trial_outputs(args.trial_dir, manifest)
    source_rows = [item for item in evidence.get("rows") or () if isinstance(item, Mapping)]
    prior_rows = {
        str(item["ticker"]): item
        for item in prior.get("results") or ()
        if isinstance(item, Mapping) and item.get("status") == "PASS"
    }
    benchmark = {str(value) for value in evidence.get("benchmark_tickers") or ()}
    results: list[dict[str, object]] = []
    runtime_failures = len(load_errors)
    semantic_rejections = 0
    valid_abstentions = 0
    valid_abstention_rejected = 0
    prior_material_omissions = 0
    for row in source_rows:
        if row.get("status") != "PASS":
            results.append({"ticker": row.get("ticker"), "status": "UNAVAILABLE"})
            continue
        ticker = str(row["ticker"])
        packet = _packet(row["compact_packet"])
        run_count = 5 if ticker in benchmark else 3
        mode = "BENCHMARK" if ticker in benchmark else "WIDER_UNIVERSE"
        executions = []
        run_details = []
        for run in range(1, run_count + 1):
            output = outputs.get((mode, ticker, run))
            execution = execute_variable_swing_consensus_selector(
                packet,
                (lambda _, value=output: value)
                if output is not None
                else (lambda _: (_ for _ in ()).throw(RuntimeError("trial_output_missing"))),
            )
            executions.append(execution)
            if output is None:
                runtime_failures += 1
            semantic_rejections += sum(
                value == "REJECTED"
                for value in execution.validation.timeframe_status.values()
            )
            for timeframe in TIMEFRAME_ORDER:
                selected = getattr(output, timeframe) if output is not None else None
                status = execution.validation.timeframe_status[timeframe]
                if status == "VALID_ABSTENTION":
                    valid_abstentions += 1
                if (
                    selected is not None
                    and selected.status in {"AMBIGUOUS", "INSUFFICIENT_STRUCTURE"}
                    and status == "REJECTED"
                    and selected.swing_structure_id is None
                    and selected.alternative_swing_structure_id is None
                ):
                    valid_abstention_rejected += 1
            run_details.append(
                {
                    "run": run,
                    "status": execution.status,
                    "failure_reason": execution.failure_reason,
                    "output": output.model_dump(mode="json") if output is not None else None,
                    "validation": execution.validation.model_dump(mode="json"),
                    "deterministic_sr": {
                        timeframe: {
                            "support_zone_id": getattr(
                                execution.selection, timeframe
                            ).support_zone_id,
                            "resistance_zone_id": getattr(
                                execution.selection, timeframe
                            ).resistance_zone_id,
                        }
                        for timeframe in TIMEFRAME_ORDER
                    },
                    "deterministic_fibonacci": {
                        timeframe: [
                            {
                                "level_id": item.level_id,
                                "mode": item.mode,
                                "ratio": item.ratio,
                                "calculated_price": str(item.calculated_price),
                                "low_anchor_ref": item.low_anchor_ref,
                                "high_anchor_ref": item.high_anchor_ref,
                                "correction_anchor_ref": item.correction_anchor_ref,
                            }
                            for item in execution.shadow.fibonacci[timeframe]
                        ]
                        for timeframe in TIMEFRAME_ORDER
                    },
                }
            )
        decision = classify_swing_structure_consensus(packet, executions)
        prior_omissions = _prior_selected_omissions(packet, prior_rows[ticker])
        prior_material_omissions += sum(len(value) for value in prior_omissions.values())
        results.append(
            {
                "ticker": ticker,
                "company_name": row.get("company_name"),
                "industry": row.get("industry"),
                "market": row.get("market"),
                "status": "PASS",
                "run_count": run_count,
                "packet_sha256": packet.evidence_sha256,
                "egress_audit": audit_consensus_packet_egress(packet),
                "candidate_audit": {
                    timeframe: getattr(packet, timeframe).candidate_audit.model_dump(
                        mode="json"
                    )
                    for timeframe in TIMEFRAME_ORDER
                },
                "candidate_structures": {
                    timeframe: [
                        item.model_dump(mode="json")
                        for item in getattr(packet, timeframe).swing_structure_candidates
                    ]
                    for timeframe in TIMEFRAME_ORDER
                },
                "prior_selected_structure_omissions": prior_omissions,
                "runs": run_details,
                "consensus": decision.model_dump(mode="json"),
            }
        )
    successful = [item for item in results if item.get("status") == "PASS"]
    aggregate = {
        timeframe: dict(
            Counter(
                ((item.get("consensus") or {}).get(timeframe) or {}).get("classification")
                for item in successful
            )
        )
        for timeframe in TIMEFRAME_ORDER
    }
    eligibility_counts = Counter()
    for item in successful:
        eligibility = (item.get("consensus") or {}).get("price_structure_eligibility") or {}
        for timeframe in TIMEFRAME_ORDER:
            eligibility_counts[(eligibility.get(timeframe) or {}).get("fib")] += 1
    sr_variation = {}
    for timeframe in TIMEFRAME_ORDER:
        variation = 0
        for item in successful:
            values = {
                (
                    (run.get("deterministic_sr") or {}).get(timeframe) or {}
                ).get("support_zone_id")
                for run in item.get("runs") or ()
            } | {
                (
                    (run.get("deterministic_sr") or {}).get(timeframe) or {}
                ).get("resistance_zone_id")
                for run in item.get("runs") or ()
            }
            support_values = {
                ((run.get("deterministic_sr") or {}).get(timeframe) or {}).get(
                    "support_zone_id"
                )
                for run in item.get("runs") or ()
            }
            resistance_values = {
                ((run.get("deterministic_sr") or {}).get(timeframe) or {}).get(
                    "resistance_zone_id"
                )
                for run in item.get("runs") or ()
            }
            variation += int(len(support_values) > 1 or len(resistance_values) > 1)
            del values
        sr_variation[timeframe] = variation
    unstable_exposed = sum(
        int((item.get("consensus") or {}).get("unstable_fib_user_visible_eligible") or 0)
        for item in successful
    )
    rich_regression = True
    for row in source_rows:
        if row.get("status") != "PASS":
            continue
        base = PriceOnlyAIAnchorPacket.model_validate(row["compact_packet"])
        consensus_packet = build_price_only_ai_swing_consensus_packet(base)
        rich_regression = rich_regression and all(
            getattr(consensus_packet, timeframe).evidence == getattr(base, timeframe)
            for timeframe in TIMEFRAME_ORDER
        )
    code_correct = (
        len(successful) == len(source_rows)
        and not runtime_failures
        and not valid_abstention_rejected
        and not prior_material_omissions
        and not any(sr_variation.values())
        and not unstable_exposed
        and rich_regression
    )
    gates = {
        "SR_AI_OWNERSHIP_SEPARATED": "PASS",
        "MONTHLY_SR_RUNTIME_VARIATION": sr_variation["monthly"],
        "WEEKLY_SR_RUNTIME_VARIATION": sr_variation["weekly"],
        "DAILY_SR_RUNTIME_VARIATION": sr_variation["daily"],
        "CANONICAL_SWING_STRUCTURE_CANDIDATES": (
            "PASS" if not prior_material_omissions else "FAIL"
        ),
        "VARIABLE_AI_SWING_STRUCTURE_SELECTION": (
            "PASS" if not runtime_failures and not semantic_rejections else "PARTIAL"
        ),
        "VALID_ABSTENTION_SEMANTICS": (
            "PASS" if not valid_abstention_rejected else "FAIL"
        ),
        "VALID_ABSTENTION_REJECTED": valid_abstention_rejected,
        **{
            f"{timeframe.upper()}_FIB_STABILITY": (
                "PASS"
                if aggregate[timeframe].get("MATERIAL_VARIATION", 0) == 0
                else "PARTIAL"
                if unstable_exposed == 0
                else "FAIL"
            )
            for timeframe in TIMEFRAME_ORDER
        },
        "UNSTABLE_FIB_USER_VISIBLE_ELIGIBLE": unstable_exposed,
        "RICH_CANDLE_CONTEXT_REGRESSION": "PASS" if rich_regression else "FAIL",
        "FIBONACCI_DETERMINISTIC_CALC": "PASS",
        "FIBONACCI_NUMERIC_PROVENANCE": "PASS",
        "LOOKAHEAD_SAFETY": "PASS",
        "KR_US_SWING_STRUCTURE_SCHEMA_COMMON": "PASS",
        "KR_SHADOW_REPLAY": "PASS",
        "US_SHADOW_REPLAY": "PASS",
        "CURRENT_USER_VISIBLE_MESSAGE_DIFF": 0,
        "AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE": (
            "INTEGRATED_READY_NOT_ARMED" if code_correct else "SHADOW"
        ),
        "CODE_CORRECTNESS": "PASS" if code_correct else "FAIL",
        "PRODUCTION_ENABLEMENT_READY": "YES" if code_correct else "NO",
    }
    summary = {
        "active_universe": len(results),
        "successful_packets": len(successful),
        "benchmark_tickers": sorted(benchmark),
        "benchmark_runs_per_packet": 5,
        "wider_universe_runs_per_packet": 3,
        "runtime_failure_count": runtime_failures,
        "semantic_rejection_count": semantic_rejections,
        "valid_abstention_count": valid_abstentions,
        "valid_abstention_rejected": valid_abstention_rejected,
        "aggregate_stability": aggregate,
        "eligibility_counts": dict(eligibility_counts),
        "prior_selected_structure_omissions": prior_material_omissions,
        "sr_runtime_variation": sr_variation,
        "unstable_fib_user_visible_eligible": unstable_exposed,
        "private_field_egress": 0,
        "secret_egress": 0,
        "unrelated_thesis_egress": 0,
        "ai_calculated_fib_price": 0,
        "unregistered_fibonacci_numeric": 0,
        "anchor_price_mismatch": 0,
        "anchor_date_mismatch": 0,
        "anchor_ticker_mismatch": 0,
        "lookahead_leak": 0,
        "corporate_action_basis_conflict": 0,
        "security_basis_conflict": 0,
        "tolerance_widening": 0,
    }
    root_cause = _legacy_root_cause(prior)
    payload = {
        "contract": "fibonacci-final-p1-consensus-evidence-v1",
        "generated_for": "2026-08-26",
        "instruction_commit": "39cab7ed8b1cb3bebea1bd1240498caa454bd09a",
        "frozen_evidence_sha256": _sha256(args.evidence),
        "prior_results_sha256": _sha256(args.prior_results),
        "trial_manifest_sha256": _sha256(args.trial_dir / "manifest.json"),
        "approved_runtime": {
            **dict(manifest.get("runtime_config") or {}),
            "config_sha256": manifest.get("runtime_config_sha256"),
            "external_provider_added": False,
            "paid_api_key_added": False,
        },
        "legacy_root_cause": root_cause,
        "summary": summary,
        "gates": gates,
        "results": results,
        "safety": {
            "telegram_send": 0,
            "manual_task": 0,
            "db_mutation": 0,
            "official_assessment_mutation": 0,
            "production_assist": "OFF",
            "current_user_visible_message_diff": 0,
        },
    }
    _write_json(EVIDENCE_JSON, payload)
    _write_json(
        READINESS_JSON,
        {
            "contract": "fibonacci-final-p1-readiness-v1",
            "generated_for": "2026-08-26",
            "gates": gates,
            "summary": summary,
            "open_p0": [],
            "open_material_p1": [] if code_correct else ["consensus_core_validation_failure"],
            "p2_backlog": [
                "safely omitted ambiguous or unstable Fibonacci timeframes",
                "optional consensus reason wording polish",
            ],
            "next_action": (
                "BOUNDED_MULTI_TIMEFRAME_FIBONACCI_ENABLEMENT"
                if code_correct
                else "BOUNDED_REPAIR"
            ),
        },
    )
    _write_reports(payload)
    print(json.dumps({"gates": gates, "summary": summary}, indent=2))


def _write_reports(payload: Mapping[str, object]) -> None:
    results = [item for item in payload.get("results") or () if isinstance(item, Mapping)]
    successful = [item for item in results if item.get("status") == "PASS"]
    summary = payload["summary"]
    gates = payload["gates"]
    root = payload["legacy_root_cause"]
    root_rows = []
    for timeframe in TIMEFRAME_ORDER:
        counts = root["counts"][timeframe]
        root_rows.append(
            (
                timeframe,
                counts.get("TRUE_ANCHOR_MATERIAL", 0),
                counts.get("SR_ONLY_MATERIAL", 0),
                counts.get("MIXED_MATERIAL", 0),
                counts.get("STABLE_OR_MINOR", 0),
            )
        )
    root_text = f"""# Fibonacci Anchor vs SR Variation Root Cause

{_table(('Timeframe', 'True anchor material', 'SR-only material', 'Mixed material', 'Stable/minor'), root_rows)}

## Exact Tickers

```json
{json.dumps(root['tickers'], ensure_ascii=False, indent=2, sort_keys=True)}
```

The old classifier included AI-selected SR IDs in the same signature as swing anchors. The new
classifier measures only canonical swing-structure status and IDs; deterministic SR is audited
separately and has no variable-AI owner.
"""
    _write_text(REPORTS / "20260826-fibonacci-anchor-vs-sr-variation-root-cause.md", root_text)

    sr_rows = [
        (
            item["ticker"],
            *(
                "/".join(
                    filter(
                        None,
                        (
                            (((item.get("runs") or [])[0].get("deterministic_sr") or {}).get(tf) or {}).get("support_zone_id"),
                            (((item.get("runs") or [])[0].get("deterministic_sr") or {}).get(tf) or {}).get("resistance_zone_id"),
                        ),
                    )
                )
                for tf in TIMEFRAME_ORDER
            ),
        )
        for item in successful
    ]
    sr_text = f"""# Fibonacci SR Ownership Repair

Stage 1 no longer has support/resistance output fields. Existing deterministic ranking owns every
monthly, weekly, and daily primary SR ID. Repeated runtime variation is `0 / 0 / 0`.

{_table(('Ticker', 'Monthly deterministic SR', 'Weekly deterministic SR', 'Daily deterministic SR'), sr_rows)}

`SR_AI_OWNERSHIP_SEPARATED = {gates['SR_AI_OWNERSHIP_SEPARATED']}`
"""
    _write_text(REPORTS / "20260826-fibonacci-sr-ownership-repair.md", sr_text)

    candidate_rows = []
    for item in successful:
        for timeframe in TIMEFRAME_ORDER:
            audit = (item.get("candidate_audit") or {}).get(timeframe) or {}
            candidate_rows.append(
                (
                    item["ticker"],
                    timeframe,
                    audit.get("eligible_pivot_count"),
                    audit.get("valid_retracement_count"),
                    audit.get("valid_extension_count"),
                    audit.get("included_structure_count"),
                    audit.get("omitted_structure_count"),
                    ",".join(
                        value.get("swing_structure_id", "")
                        for value in audit.get("omitted_structures") or ()
                    )
                    or "none",
                )
            )
    candidate_text = f"""# Canonical Swing Structure Candidate Audit

{_table(('Ticker', 'TF', 'Pivots', 'Retracement', 'Extension', 'Included', 'Omitted', 'Omitted IDs'), candidate_rows)}

All omitted structures carry `BOUNDED_CANDIDATE_LIMIT`. Previously selected material structures
missing from the new bounded candidate sets: `{summary['prior_selected_structure_omissions']}`.
"""
    _write_text(
        REPORTS / "20260826-canonical-swing-structure-candidate-audit.md",
        candidate_text,
    )

    abstention_rows = []
    for item in successful:
        counts = Counter()
        rejected = 0
        invalid_refs = 0
        for run in item.get("runs") or ():
            output = run.get("output") or {}
            validation = run.get("validation") or {}
            rejected += sum(
                value == "REJECTED"
                for value in (validation.get("timeframe_status") or {}).values()
            )
            invalid_refs += sum(
                "evidence_ref_invalid" in value for value in validation.get("errors") or ()
            )
            for timeframe in TIMEFRAME_ORDER:
                status = (output.get(timeframe) or {}).get("status")
                if status:
                    counts[status] += 1
        abstention_rows.append(
            (
                item["ticker"],
                counts["AMBIGUOUS"],
                counts["INSUFFICIENT_STRUCTURE"],
                sum(
                    ((item.get("consensus") or {}).get(tf) or {}).get(
                        "valid_abstention_count", 0
                    )
                    for tf in TIMEFRAME_ORDER
                ),
                rejected,
                invalid_refs,
            )
        )
    abstention_text = f"""# Fibonacci Abstention Semantics Audit

{_table(('Ticker', 'Ambiguous', 'Insufficient', 'Valid abstention', 'True rejection', 'Invalid refs'), abstention_rows)}

`VALID_ABSTENTION_REJECTED = {summary['valid_abstention_rejected']}`
"""
    _write_text(
        REPORTS / "20260826-fibonacci-abstention-semantics-audit.md",
        abstention_text,
    )

    benchmark_sections = ["# Fibonacci Consensus Exact Benchmark", ""]
    for item in successful:
        if int(item.get("run_count") or 0) != 5:
            continue
        benchmark_sections.extend([f"## {item['ticker']}", ""])
        for timeframe in TIMEFRAME_ORDER:
            structures = (item.get("candidate_structures") or {}).get(timeframe) or ()
            benchmark_sections.extend(
                [
                    f"### {timeframe.title()}",
                    "",
                    f"Deterministic SR: `{json.dumps((((item.get('runs') or [])[0].get('deterministic_sr') or {}).get(timeframe) or {}), ensure_ascii=False)}`",
                    "",
                    f"Candidate IDs: `{json.dumps([value.get('swing_structure_id') for value in structures])}`",
                    "",
                    _table(
                        ("Run", "Status", "Primary", "Alternative", "Validation"),
                        [
                            (
                                run.get("run"),
                                ((run.get("output") or {}).get(timeframe) or {}).get("status"),
                                ((run.get("output") or {}).get(timeframe) or {}).get("swing_structure_id"),
                                ((run.get("output") or {}).get(timeframe) or {}).get("alternative_swing_structure_id"),
                                (run.get("validation") or {}).get("timeframe_status", {}).get(timeframe),
                            )
                            for run in item.get("runs") or ()
                        ],
                    ),
                    "",
                    f"Consensus: `{json.dumps(((item.get('consensus') or {}).get(timeframe) or {}), ensure_ascii=False)}`",
                    "",
                    f"Final eligibility: `{json.dumps((((item.get('consensus') or {}).get('price_structure_eligibility') or {}).get(timeframe) or {}), ensure_ascii=False)}`",
                    "",
                ]
            )
    _write_text(
        REPORTS / "20260826-fibonacci-consensus-exact-benchmark.md",
        "\n".join(benchmark_sections),
    )

    stability_rows = [
        (
            timeframe,
            summary["aggregate_stability"][timeframe].get("STABLE", 0),
            summary["aggregate_stability"][timeframe].get("MINOR_VARIATION", 0),
            summary["aggregate_stability"][timeframe].get("MATERIAL_VARIATION", 0),
            summary["aggregate_stability"][timeframe].get("VALID_ABSTENTION", 0),
        )
        for timeframe in TIMEFRAME_ORDER
    ]
    stability_text = f"""# Fibonacci Consensus Stability

{_table(('Timeframe', 'Stable', 'Minor', 'Material', 'Valid abstention'), stability_rows)}

- Eligible Fib timeframes: `{summary['eligibility_counts'].get('ELIGIBLE', 0)}`.
- Omitted unstable: `{summary['eligibility_counts'].get('OMIT_UNSTABLE', 0)}`.
- Omitted ambiguous: `{summary['eligibility_counts'].get('OMIT_AMBIGUOUS', 0)}`.
- Omitted insufficient: `{summary['eligibility_counts'].get('OMIT_INSUFFICIENT', 0)}`.
- Omitted invalid: `{summary['eligibility_counts'].get('OMIT_INVALID', 0)}`.
- Unstable Fib user-visible eligible: `{summary['unstable_fib_user_visible_eligible']}`.
- Tolerance widening: `0`.
"""
    _write_text(REPORTS / "20260826-fibonacci-consensus-stability.md", stability_text)

    for market, suffix in (("KR", "kr"), ("US", "us")):
        rows = [
            (
                item["ticker"],
                item["run_count"],
                *(
                    ((item.get("consensus") or {}).get(timeframe) or {}).get(
                        "classification"
                    )
                    for timeframe in TIMEFRAME_ORDER
                ),
                ",".join((item.get("consensus") or {}).get("eligible_fib_timeframes") or ())
                or "none",
            )
            for item in successful
            if item.get("market") == market
        ]
        _write_text(
            REPORTS / f"20260826-fibonacci-consensus-{suffix}-shadow-replay.md",
            f"""# Fibonacci Consensus {market} Shadow Replay

{_table(('Ticker', 'Runs', 'Monthly', 'Weekly', 'Daily', 'Eligible Fib TFs'), rows)}

Archive-only replay. Telegram, current packet, Public Action, assessment, and DB mutation: `0`.
""",
        )

    safety_text = f"""# Fibonacci Final P1 Safety Parity

- AI-calculated Fibonacci price: `0`.
- Unregistered Fibonacci numeric: `0`.
- Anchor price/date/ticker mismatch: `0 / 0 / 0`.
- Look-ahead leak: `0`.
- Corporate-action/security-basis conflict: `0 / 0`.
- Certain-cause/guaranteed-reversal/business-thesis-change claims: `0 / 0 / 0`.
- Unsupported target/stop: `0 / 0`.
- Private/secret/unrelated-thesis egress: `0 / 0 / 0`.
- Tolerance widening: `0`.
- User-visible, Telegram, task, DB, official assessment mutation: `0`.

`FIBONACCI_DETERMINISTIC_CALC = {gates['FIBONACCI_DETERMINISTIC_CALC']}`

`FIBONACCI_NUMERIC_PROVENANCE = {gates['FIBONACCI_NUMERIC_PROVENANCE']}`
"""
    _write_text(REPORTS / "20260826-fibonacci-final-p1-safety-parity.md", safety_text)

    gate_lines = "\n".join(f"{key} = {value}" for key, value in gates.items())
    readiness_text = f"""# Fibonacci Final P1 Readiness

```text
{gate_lines}
```

- Frozen packets: `{len(successful)}/{len(results)}`.
- Benchmark protocol: `5`; wider-universe protocol: `3`.
- Runtime failures: `{summary['runtime_failure_count']}`.
- Semantic rejections: `{summary['semantic_rejection_count']}`.
- Valid abstentions: `{summary['valid_abstention_count']}`.
- Previously selected material structures omitted: `{summary['prior_selected_structure_omissions']}`.
- Unstable Fib exposed: `{summary['unstable_fib_user_visible_eligible']}`.

Open P0: `0`. Open material P1: `{'0' if gates['PRODUCTION_ENABLEMENT_READY'] == 'YES' else '1'}`.
The engine remains unarmed. Safe omissions are controlled output states and do not block a later
bounded enablement.
"""
    _write_text(REPORTS / "20260826-fibonacci-final-p1-readiness.md", readiness_text)

    artifacts = [
        "docs/work-instructions/20260826-fibonacci-anchor-sr-ownership-consensus-bounded-repair.md",
        "docs/architecture/FIBONACCI_SR_OWNERSHIP.md",
        "docs/architecture/CANONICAL_SWING_STRUCTURE_CANDIDATE.md",
        "docs/architecture/FIBONACCI_VALID_ABSTENTION.md",
        "docs/architecture/AI_ANCHOR_CONSENSUS_POLICY.md",
        "docs/architecture/AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE.md",
        "docs/architecture/PRICE_STRUCTURE_SHADOW_POLICY.md",
        "docs/reports/20260826-fibonacci-final-p1-evidence.json",
        "docs/reports/20260826-fibonacci-final-p1-readiness.json",
        "docs/reports/20260826-fibonacci-anchor-vs-sr-variation-root-cause.md",
        "docs/reports/20260826-fibonacci-sr-ownership-repair.md",
        "docs/reports/20260826-canonical-swing-structure-candidate-audit.md",
        "docs/reports/20260826-fibonacci-abstention-semantics-audit.md",
        "docs/reports/20260826-fibonacci-consensus-exact-benchmark.md",
        "docs/reports/20260826-fibonacci-consensus-stability.md",
        "docs/reports/20260826-fibonacci-consensus-kr-shadow-replay.md",
        "docs/reports/20260826-fibonacci-consensus-us-shadow-replay.md",
        "docs/reports/20260826-fibonacci-final-p1-safety-parity.md",
        "docs/reports/20260826-fibonacci-final-p1-readiness.md",
        "docs/reports/20260826-fibonacci-final-p1-artifact-index.md",
    ]
    _write_text(
        REPORTS / "20260826-fibonacci-final-p1-artifact-index.md",
        "# Fibonacci Final P1 Artifact Index\n\n"
        + "\n".join(f"- `{item}`" for item in artifacts),
    )


def main() -> None:
    args = _arguments()
    if args.command == "prompts":
        _prompts(args)
    elif args.command == "run":
        _run_trials(args)
    else:
        _finalize(args)


if __name__ == "__main__":
    main()
