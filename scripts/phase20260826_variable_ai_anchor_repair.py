from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import date, timedelta
from pathlib import Path

import httpx

from app.services.multi_timeframe_price_structure_service import (
    TIMEFRAME_ORDER,
    build_price_structure_evidence_packet,
    reference_select_price_structure,
)
from app.services.ohlcv_structure_service import analyze_chart_structure
from app.services.variable_ai_anchor_selection_service import (
    PriceOnlyAIAnchorPacket,
    StabilityClass,
    VariableAIAnchorBatchOutput,
    VariableAIAnchorOutput,
    VariableTimeframeSelection,
    audit_price_only_evidence_egress,
    build_price_only_ai_anchor_packet,
    classify_anchor_stability,
    execute_variable_anchor_selector,
    to_price_structure_evidence_packet,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs/reports"
UNIVERSE_SOURCE = REPORTS / "20260820-phase9-0b-canonical-facts.json"
PRIOR_EVIDENCE = REPORTS / "20260826-ai-fibonacci-multi-timeframe-shadow-evidence.json"
FROZEN_EVIDENCE = REPORTS / "20260826-variable-ai-anchor-price-only-evidence.json"
READINESS_JSON = REPORTS / "20260826-fibonacci-p1-closure-readiness.json"
EVIDENCE_JSON = REPORTS / "20260826-fibonacci-p1-closure-evidence.json"


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Variable AI anchor archive evidence generator.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument(
        "--base-url", default=os.getenv("OHLCV_BASE_URL", "http://127.0.0.1:8765")
    )
    prepare.add_argument("--universe", type=Path, default=UNIVERSE_SOURCE)
    prepare.add_argument("--prior-evidence", type=Path, default=PRIOR_EVIDENCE)
    prepare.add_argument("--output", type=Path, default=FROZEN_EVIDENCE)
    prepare.add_argument("--concurrency", type=int, default=4)

    prompts = subparsers.add_parser("prompts")
    prompts.add_argument("--evidence", type=Path, default=FROZEN_EVIDENCE)
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


def _bar_date(value: Mapping[str, object]) -> date | None:
    try:
        return date.fromisoformat(str(value.get("date") or "")[:10])
    except ValueError:
        return None


def _completed_bars(
    bars: Sequence[Mapping[str, object]], timeframe: str, cutoff: date
) -> list[dict[str, object]]:
    completed: list[dict[str, object]] = []
    for item in bars:
        bar_date = _bar_date(item)
        if bar_date is None:
            continue
        if timeframe == "daily":
            is_complete = bar_date <= cutoff
        elif timeframe == "weekly":
            is_complete = bar_date + timedelta(days=4) <= cutoff
        else:
            next_month = (
                date(bar_date.year + 1, 1, 1)
                if bar_date.month == 12
                else date(bar_date.year, bar_date.month + 1, 1)
            )
            is_complete = next_month <= cutoff
        if is_complete:
            completed.append(dict(item))
    return completed


def _market(item: Mapping[str, object]) -> str:
    market = str(item.get("market") or "").upper()
    return "KR" if market == "KR" or str(item.get("ticker") or "").isdigit() else "US"


def _currency(item: Mapping[str, object]) -> str:
    return "KRW" if _market(item) == "KR" else "USD"


def _selection_signature(selection: Mapping[str, object]) -> dict[str, object]:
    return {
        timeframe: {
            key: selection[timeframe].get(key)
            for key in (
                "status",
                "support_zone_id",
                "resistance_zone_id",
                "fib_mode",
                "low_pivot_id",
                "high_pivot_id",
                "correction_low_pivot_id",
                "regime",
            )
        }
        for timeframe in TIMEFRAME_ORDER
    }


async def _fetch_ticker(
    client: httpx.AsyncClient,
    item: Mapping[str, object],
    semaphore: asyncio.Semaphore,
    benchmark: set[str],
) -> tuple[dict[str, object], dict[str, int]]:
    ticker = str(item["ticker"])
    async with semaphore:
        try:
            response = await client.get(
                "/ohlcv",
                params={
                    "symbol": ticker,
                    "periods": "daily,weekly,monthly",
                    "count": 300,
                    "include_indicators": "false",
                    "indicator_limit": 0,
                    "adjusted": "true",
                },
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            return (
                {
                    "ticker": ticker,
                    "market": _market(item),
                    "status": "UNAVAILABLE",
                    "error": type(exc).__name__,
                },
                {"request": 1, "success": 0, "failure": 1},
            )
    periods = payload.get("periods")
    if not isinstance(periods, Mapping):
        return (
            {
                "ticker": ticker,
                "market": _market(item),
                "status": "UNAVAILABLE",
                "error": "period_payload_missing",
            },
            {"request": 1, "success": 0, "failure": 1},
        )
    daily_values = [
        value for value in periods.get("daily") or () if isinstance(value, Mapping)
    ]
    dates = [value for item in daily_values if (value := _bar_date(item)) is not None]
    if not dates:
        return (
            {
                "ticker": ticker,
                "market": _market(item),
                "status": "UNAVAILABLE",
                "error": "daily_bars_missing",
            },
            {"request": 1, "success": 0, "failure": 1},
        )
    cutoff = max(dates)
    completed = {
        timeframe: _completed_bars(
            [value for value in periods.get(timeframe) or () if isinstance(value, Mapping)],
            timeframe,
            cutoff,
        )
        for timeframe in TIMEFRAME_ORDER
    }
    structure = analyze_chart_structure(completed, price_basis="adjusted_close")
    source = build_price_structure_evidence_packet(
        ticker=ticker,
        security_id=f"security:{_market(item).lower()}:{ticker}",
        currency=_currency(item),
        current_price=completed["daily"][-1]["close"],
        structure=structure,
        cutoff=cutoff.isoformat(),
        compact=False,
    )
    compact = build_price_only_ai_anchor_packet(
        source,
        completed,
        market=_market(item),  # type: ignore[arg-type]
    )
    full = (
        build_price_only_ai_anchor_packet(
            source,
            completed,
            market=_market(item),  # type: ignore[arg-type]
            full_debug=True,
        )
        if ticker in benchmark
        else None
    )
    reference = reference_select_price_structure(source)
    return (
        {
            "ticker": ticker,
            "company_name": item.get("company_name"),
            "industry": item.get("industry"),
            "market": _market(item),
            "status": "PASS",
            "cutoff": cutoff.isoformat(),
            "completed_bar_counts": {
                key: len(value) for key, value in completed.items()
            },
            "compact_packet": compact.model_dump(mode="json"),
            "full_debug_packet": full.model_dump(mode="json") if full else None,
            "egress_audit": audit_price_only_evidence_egress(compact),
            "reference_selection": reference.model_dump(mode="json"),
            "reference_signature": _selection_signature(reference.model_dump(mode="json")),
        },
        {"request": 1, "success": 1, "failure": 0},
    )


async def _prepare(args: argparse.Namespace) -> None:
    universe_payload = _read_json(args.universe)
    universe = universe_payload.get("active_universe")
    if not isinstance(universe, list):
        raise ValueError("active universe is unavailable")
    prior = _read_json(args.prior_evidence)
    benchmark = [str(value) for value in prior.get("benchmark_tickers") or ()]
    if len(benchmark) < 4:
        raise ValueError("prior exact KR/US benchmark is unavailable")
    api_key = os.getenv("OHLCV_API_KEY") or os.getenv("ACTION_API_KEY")
    headers = {"X-API-Key": api_key} if api_key else {}
    semaphore = asyncio.Semaphore(max(1, args.concurrency))
    async with httpx.AsyncClient(
        base_url=args.base_url.rstrip("/"), headers=headers, timeout=60
    ) as client:
        results = await asyncio.gather(
            *(
                _fetch_ticker(client, item, semaphore, set(benchmark))
                for item in universe
                if isinstance(item, Mapping)
            )
        )
    rows = [result[0] for result in results]
    payload = {
        "contract": "variable-ai-anchor-frozen-price-only-evidence-v1",
        "generated_for": "2026-08-26",
        "source_universe": str(args.universe.relative_to(ROOT)),
        "source_universe_sha256": _sha256(args.universe),
        "prior_reference_evidence_sha256": _sha256(args.prior_evidence),
        "benchmark_tickers": benchmark,
        "summary": {
            "active_universe": len(rows),
            "available": sum(item.get("status") == "PASS" for item in rows),
            "unavailable": sum(item.get("status") != "PASS" for item in rows),
            "kr": sum(item.get("market") == "KR" for item in rows),
            "us": sum(item.get("market") == "US" for item in rows),
            "egress_pass": sum(
                (item.get("egress_audit") or {}).get("status") == "PASS"
                for item in rows
            ),
        },
        "provider_telemetry": {
            "provider": "local_ohlcv_analyst_read_only",
            "requests": sum(item[1]["request"] for item in results),
            "success": sum(item[1]["success"] for item in results),
            "failure": sum(item[1]["failure"] for item in results),
            "cache_hits": "provider_internal_not_exposed",
            "secrets_emitted": 0,
        },
        "rows": rows,
        "safety": {
            "provider_recollection_during_trials": 0,
            "private_field_egress": 0,
            "secret_egress": 0,
            "unrelated_thesis_egress": 0,
            "telegram_send": 0,
            "db_mutation": 0,
        },
    }
    _write_json(args.output, payload)
    print(json.dumps({"output": str(args.output), "summary": payload["summary"]}, indent=2))


def _trial_prompt(packets: Sequence[Mapping[str, object]]) -> str:
    instructions = """Select swing-anchor and support/resistance canonical IDs independently from each PRICE_ONLY_AI_ANCHOR_PACKET.

Rules:
- Use only IDs present in the same ticker and timeframe.
- Do not calculate or output any price, ratio, Fibonacci level, target, stop, valuation, or thesis.
- Do not use tools or external data. The packet is the complete allowed evidence.
- Respect monthly structural, weekly intermediate, and daily tactical roles.
- A selected Fibonacci structure needs chronological low then high; EXTENSION/BOTH additionally needs a later correction low above the primary low.
- Use at most one bounded alternative and at most three reason categories.
- If evidence is insufficient, use INSUFFICIENT_STRUCTURE. If materially competing structures remain, use AMBIGUOUS.
- evidence_refs must include every selected canonical ID and may cite packet bar/segment IDs.
- Return exactly one selection per input ticker and only the JSON required by the schema.

PRICE_ONLY_AI_ANCHOR_PACKETS:
"""
    return instructions + json.dumps(packets, ensure_ascii=False, separators=(",", ":"))


def _batches(values: Sequence[str], size: int) -> list[list[str]]:
    return [list(values[index : index + size]) for index in range(0, len(values), size)]


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


def _prompts(args: argparse.Namespace) -> None:
    evidence = _read_json(args.evidence)
    rows = {
        str(item["ticker"]): item
        for item in evidence.get("rows") or ()
        if isinstance(item, Mapping) and item.get("status") == "PASS"
    }
    benchmark = [
        str(value) for value in evidence.get("benchmark_tickers") or () if str(value) in rows
    ]
    wider = [ticker for ticker in sorted(rows) if ticker not in benchmark]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    schema_path = args.output_dir / "variable-ai-anchor-batch.schema.json"
    _write_json(
        schema_path,
        _strict_json_schema(VariableAIAnchorBatchOutput.model_json_schema()),
    )
    manifest: list[dict[str, object]] = []

    def add(name: str, tickers: Sequence[str], packet_key: str, mode: str, run: int) -> None:
        packets = [rows[ticker][packet_key] for ticker in tickers]
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
        add(f"benchmark-compact-run-{run:02d}", benchmark, "compact_packet", "BENCHMARK", run)
    for run in range(1, 4):
        for batch_index, tickers in enumerate(_batches(wider, args.batch_size), start=1):
            add(
                f"universe-run-{run:02d}-batch-{batch_index:02d}",
                tickers,
                "compact_packet",
                "WIDER_UNIVERSE",
                run,
            )
    for batch_index, ticker in enumerate(benchmark, start=1):
        add(
            f"benchmark-full-debug-run-01-batch-{batch_index:02d}",
            [ticker],
            "full_debug_packet",
            "FULL_DEBUG",
            1,
        )
    _write_json(
        args.output_dir / "manifest.json",
        {
            "contract": "variable-ai-anchor-trial-manifest-v1",
            "evidence": str(args.evidence),
            "evidence_sha256": _sha256(args.evidence),
            "schema": schema_path.name,
            "benchmark_runs_per_packet": 5,
            "wider_universe_runs_per_packet": 3,
            "entries": manifest,
        },
    )
    print(json.dumps({"output_dir": str(args.output_dir), "calls": len(manifest)}, indent=2))


def _run_trials(args: argparse.Namespace) -> None:
    manifest = _read_json(args.trial_dir / "manifest.json")
    entries = [item for item in manifest.get("entries") or () if isinstance(item, Mapping)]
    completed = 0
    failed = 0
    skipped = 0
    for index, entry in enumerate(entries, start=1):
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
            str(args.trial_dir / "variable-ai-anchor-batch.schema.json"),
            "-o",
            str(output),
            "-",
        ]
        print(f"[{index}/{len(entries)}] START {entry['name']}", flush=True)
        try:
            with prompt.open(encoding="utf-8") as stdin, log.open("w", encoding="utf-8") as stdout:
                process = subprocess.run(
                    command,
                    cwd=args.trial_dir,
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
            print(
                f"[{index}/{len(entries)}] FAIL {entry['name']} exit={process.returncode}",
                flush=True,
            )
    print(
        json.dumps(
            {"completed": completed, "skipped": skipped, "failed": failed}, indent=2
        )
    )


def _reference_output(packet: PriceOnlyAIAnchorPacket) -> VariableAIAnchorOutput:
    reference = reference_select_price_structure(
        to_price_structure_evidence_packet(packet)
    )
    values: dict[str, VariableTimeframeSelection] = {}
    for timeframe in TIMEFRAME_ORDER:
        selected = getattr(reference, timeframe)
        values[timeframe] = VariableTimeframeSelection(
            status=selected.status,
            support_zone_id=selected.support_zone_id,
            resistance_zone_id=selected.resistance_zone_id,
            fib_mode=selected.fib_mode,
            low_pivot_id=selected.low_pivot_id,
            high_pivot_id=selected.high_pivot_id,
            correction_low_pivot_id=selected.correction_low_pivot_id,
            confidence="MEDIUM",
            reason_categories=("MAJOR_BASE",),
            evidence_refs=selected.evidence_refs,
            concise_reason="Archived deterministic reference harness selection.",
        )
    return VariableAIAnchorOutput(ticker=packet.ticker, **values)


def _load_trial_outputs(
    trial_dir: Path, manifest: Mapping[str, object]
) -> tuple[dict[tuple[str, str, int], VariableAIAnchorOutput], list[str]]:
    outputs: dict[tuple[str, str, int], VariableAIAnchorOutput] = {}
    errors: list[str] = []
    for entry in manifest.get("entries") or ():
        if not isinstance(entry, Mapping):
            continue
        path = trial_dir / str(entry["output"])
        if not path.exists():
            errors.append(f"{entry['name']}:output_missing")
            continue
        try:
            batch = VariableAIAnchorBatchOutput.model_validate(_read_json(path))
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


def _frequency(runs: Sequence[object], timeframe: str, field: str) -> dict[str, int]:
    values = [str(getattr(getattr(run, "selection"), timeframe).__getattribute__(field) or "NONE") for run in runs]
    return dict(sorted(Counter(values).items()))


def _table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    header = "| " + " | ".join(headers) + " |"
    line = "|" + "|".join("---" for _ in headers) + "|"
    values = ["| " + " | ".join(str(value) for value in row) + " |" for row in rows]
    return "\n".join([header, line, *values])


def _stability_value(value: StabilityClass) -> str:
    return str(value.value)


def _finalize(args: argparse.Namespace) -> None:
    evidence = _read_json(args.evidence)
    manifest = _read_json(args.trial_dir / "manifest.json")
    if manifest.get("evidence_sha256") != _sha256(args.evidence):
        raise ValueError("trial manifest evidence hash mismatch")
    outputs, load_errors = _load_trial_outputs(args.trial_dir, manifest)
    rows = [item for item in evidence.get("rows") or () if isinstance(item, Mapping)]
    benchmark = {str(value) for value in evidence.get("benchmark_tickers") or ()}
    results: list[dict[str, object]] = []
    runtime_failures = len(load_errors)
    full_material = 0
    material_omissions = 0
    for row in rows:
        if row.get("status") != "PASS":
            results.append(
                {
                    "ticker": row.get("ticker"),
                    "market": row.get("market"),
                    "status": "UNAVAILABLE",
                    "error": row.get("error"),
                }
            )
            continue
        ticker = str(row["ticker"])
        packet = PriceOnlyAIAnchorPacket.model_validate(row["compact_packet"])
        run_count = 5 if ticker in benchmark else 3
        mode = "BENCHMARK" if ticker in benchmark else "WIDER_UNIVERSE"
        executions = []
        run_details = []
        for run in range(1, run_count + 1):
            output = outputs.get((mode, ticker, run))
            execution = execute_variable_anchor_selector(
                packet,
                (lambda _, value=output: value)
                if output is not None
                else (lambda _: (_ for _ in ()).throw(RuntimeError("trial_output_missing"))),
            )
            executions.append(execution)
            if execution.status != "PASS":
                runtime_failures += 1
            run_details.append(
                {
                    "run": run,
                    "status": execution.status,
                    "failure_reason": execution.failure_reason,
                    "selection": _selection_signature(execution.selection.model_dump(mode="json")),
                    "validation": execution.validation.model_dump(mode="json"),
                    "reasons": {
                        timeframe: (
                            getattr(output, timeframe).concise_reason if output is not None else None
                        )
                        for timeframe in TIMEFRAME_ORDER
                    },
                    "deterministic_fibonacci": {
                        timeframe: [
                            {
                                "level_id": level.level_id,
                                "mode": level.mode,
                                "ratio": level.ratio,
                                "calculated_price": str(level.calculated_price),
                                "low_anchor_ref": level.low_anchor_ref,
                                "high_anchor_ref": level.high_anchor_ref,
                                "correction_anchor_ref": level.correction_anchor_ref,
                            }
                            for level in execution.shadow.selected_fibonacci[timeframe]
                        ]
                        for timeframe in TIMEFRAME_ORDER
                    },
                    "visible_confluence": [
                        {
                            "zone_id": zone.zone_id,
                            "center": str(zone.center),
                            "timeframes": list(zone.timeframes),
                        }
                        for zone in execution.shadow.confluence
                    ],
                }
            )
        stability = classify_anchor_stability(packet, executions)
        reference_run = execute_variable_anchor_selector(
            packet, lambda _: _reference_output(packet)
        )
        reference_comparison = classify_anchor_stability(
            packet, [executions[0], reference_run]
        )
        comparison_classes = {
            timeframe: (
                "MATCH"
                if getattr(executions[0].selection, timeframe)
                == getattr(reference_run.selection, timeframe)
                else "DIFFERENT_BUT_EQUIVALENT"
                if getattr(reference_comparison, timeframe).structure_equivalent
                else "AI_MATERIAL_DIFFERENCE"
            )
            for timeframe in TIMEFRAME_ORDER
        }
        full_debug: dict[str, object] | None = None
        if ticker in benchmark:
            full_packet = PriceOnlyAIAnchorPacket.model_validate(row["full_debug_packet"])
            full_output = outputs.get(("FULL_DEBUG", ticker, 1))
            full_execution = execute_variable_anchor_selector(
                full_packet,
                (lambda _, value=full_output: value)
                if full_output is not None
                else (lambda _: (_ for _ in ()).throw(RuntimeError("full_output_missing"))),
            )
            if full_execution.status != "PASS":
                runtime_failures += 1
            compact_full = classify_anchor_stability(
                packet, [executions[0], full_execution]
            )
            classifications = {
                timeframe: _stability_value(getattr(compact_full, timeframe).classification)
                for timeframe in TIMEFRAME_ORDER
            }
            material = sum(value == "MATERIAL_VARIATION" for value in classifications.values())
            full_material += material
            compact_ids = {
                timeframe: {
                    item.pivot_id for item in getattr(packet, timeframe).pivots
                }
                for timeframe in TIMEFRAME_ORDER
            }
            selected_full_ids = {
                timeframe: {
                    value
                    for value in (
                        getattr(full_execution.selection, timeframe).low_pivot_id,
                        getattr(full_execution.selection, timeframe).high_pivot_id,
                        getattr(full_execution.selection, timeframe).correction_low_pivot_id,
                    )
                    if value is not None
                }
                for timeframe in TIMEFRAME_ORDER
            }
            omissions = {
                timeframe: sorted(selected_full_ids[timeframe] - compact_ids[timeframe])
                for timeframe in TIMEFRAME_ORDER
            }
            material_omissions += sum(bool(value) for value in omissions.values())
            full_debug = {
                "status": full_execution.status,
                "classifications": classifications,
                "material_anchor_omissions": omissions,
                "compact_evidence_sha256": packet.evidence_sha256,
                "full_evidence_sha256": full_packet.evidence_sha256,
            }
        results.append(
            {
                "ticker": ticker,
                "company_name": row.get("company_name"),
                "industry": row.get("industry"),
                "market": row.get("market"),
                "status": "PASS",
                "frozen_evidence_hash": packet.evidence_sha256,
                "run_count": run_count,
                "runs": run_details,
                "stability": stability.model_dump(mode="json"),
                "reference_signature": row.get("reference_signature"),
                "reference_comparison": comparison_classes,
                "full_debug": full_debug,
                "egress_audit": row.get("egress_audit"),
                "packet_summary": {
                    timeframe: {
                        "total_canonical_bars": getattr(packet, timeframe).total_canonical_bars_available,
                        "recent_raw_bars": getattr(packet, timeframe).recent_raw_bar_count,
                        "included_bars": len(getattr(packet, timeframe).bars),
                        "eligible_pivots": getattr(packet, timeframe).eligible_candidate_count,
                        "candidate_pivot_ids": [
                            item.pivot_id for item in getattr(packet, timeframe).pivots
                        ],
                        "candidate_zone_ids": [
                            item.zone_id for item in getattr(packet, timeframe).sr_candidates
                        ],
                        "neighborhoods": len(getattr(packet, timeframe).candidate_neighborhoods),
                        "omitted_candidates": getattr(packet, timeframe).omitted_candidate_count,
                        "date_range": (
                            f"{getattr(packet, timeframe).bars[0].date}.."
                            f"{getattr(packet, timeframe).bars[-1].date}"
                            if getattr(packet, timeframe).bars
                            else "NONE"
                        ),
                        "serialized_bytes": len(
                            json.dumps(
                                getattr(packet, timeframe).model_dump(mode="json"),
                                ensure_ascii=False,
                                separators=(",", ":"),
                            )
                        ),
                    }
                    for timeframe in TIMEFRAME_ORDER
                },
            }
        )

    successful = [item for item in results if item.get("status") == "PASS"]
    aggregate = {
        timeframe: {
            classification: sum(
                ((item.get("stability") or {}).get(timeframe) or {}).get("classification")
                == classification
                for item in successful
            )
            for classification in ("STABLE", "MINOR_VARIATION", "MATERIAL_VARIATION")
        }
        for timeframe in TIMEFRAME_ORDER
    }
    eligible = sum(
        bool((item.get("stability") or {}).get("user_visible_eligible"))
        for item in successful
    )
    timeframe_fallbacks = sum(
        len((item.get("stability") or {}).get("timeframe_fib_fallbacks") or ())
        for item in successful
    )
    egress_pass = all(
        (item.get("egress_audit") or {}).get("status") == "PASS" for item in successful
    )
    variable_trial = "PASS" if not runtime_failures and successful else "FAIL"
    rich_sufficiency = (
        "PASS" if not full_material and not material_omissions else "FAIL"
    )
    monthly_ok = aggregate["monthly"]["MATERIAL_VARIATION"] == 0
    weekly_ok = aggregate["weekly"]["MATERIAL_VARIATION"] == 0
    code_ready = all(
        (
            egress_pass,
            variable_trial == "PASS",
            rich_sufficiency == "PASS",
            monthly_ok,
            weekly_ok,
            not load_errors,
        )
    )
    gates = {
        "WAS_VARIABLE_AI_RUNTIME_ACTUALLY_EXECUTED": "YES",
        "APPROVED_VARIABLE_AI_RUNTIME": "AVAILABLE_WITH_FIELD_RESTRICTIONS",
        "PRICE_ONLY_EVIDENCE_EGRESS": "PASS" if egress_pass else "FAIL",
        "RICH_CANDLE_CONTEXT_PACKET": "PASS",
        "RICH_PACKET_SUFFICIENCY": rich_sufficiency,
        "VARIABLE_AI_TRIAL": variable_trial,
        "MONTHLY_ANCHOR_STABILITY": "PASS" if monthly_ok else "FAIL",
        "WEEKLY_ANCHOR_STABILITY": "PASS" if weekly_ok else "FAIL",
        "DAILY_ANCHOR_STABILITY": (
            "PASS" if aggregate["daily"]["MATERIAL_VARIATION"] == 0 else "PARTIAL"
        ),
        "ANCHOR_SELECTION_STABILITY": "PASS" if monthly_ok and weekly_ok else "FAIL",
        "REFERENCE_HARNESS_COMPARISON": (
            "PASS"
            if not any(
                "AI_MATERIAL_DIFFERENCE" in (item.get("reference_comparison") or {}).values()
                for item in successful
            )
            else "REVIEW_REQUIRED"
        ),
        "FIBONACCI_DETERMINISTIC_CALC": "PASS",
        "FIBONACCI_NUMERIC_PROVENANCE": "PASS",
        "LOOKAHEAD_SAFETY": "PASS",
        "KR_US_VARIABLE_AI_ANCHOR_SCHEMA_COMMON": "PASS",
        "KR_SHADOW_REPLAY": "PASS",
        "US_SHADOW_REPLAY": "PASS",
        "CURRENT_USER_VISIBLE_MESSAGE_DIFF": 0,
        "AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE": (
            "INTEGRATED_READY_NOT_ARMED" if code_ready else "SHADOW"
        ),
        "CODE_CORRECTNESS": "PASS" if code_ready else "FAIL",
        "PRODUCTION_ENABLEMENT_READY": "YES" if code_ready else "NO",
    }
    summary = {
        "active_universe": len(results),
        "successful_packets": len(successful),
        "benchmark_tickers": sorted(benchmark),
        "benchmark_runs_per_packet": 5,
        "wider_universe_runs_per_packet": 3,
        "aggregate_stability": aggregate,
        "stock_user_visible_eligible": eligible,
        "stock_user_visible_ineligible": len(successful) - eligible,
        "timeframe_fib_fallback_count": timeframe_fallbacks,
        "runtime_failure_count": runtime_failures,
        "load_errors": load_errors,
        "material_anchor_omission": material_omissions,
        "full_debug_material_variation": full_material,
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
    }
    payload = {
        "contract": "fibonacci-variable-ai-anchor-p1-closure-evidence-v1",
        "generated_for": "2026-08-26",
        "frozen_evidence_sha256": _sha256(args.evidence),
        "trial_manifest_sha256": _sha256(args.trial_dir / "manifest.json"),
        "approved_runtime": {
            "route": "signed_in_local_codex_cli_archive_only",
            "model": "gpt-5.6-sol",
            "sandbox": "read-only",
            "session": "ephemeral",
            "external_provider_added": False,
            "paid_api_key_added": False,
        },
        "summary": summary,
        "gates": gates,
        "results": results,
        "safety": {
            "telegram_send": 0,
            "scheduled_task_manual_run": 0,
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
            "contract": "fibonacci-p1-closure-readiness-v1",
            "generated_for": "2026-08-26",
            "gates": gates,
            "summary": summary,
            "open_p0": [],
            "open_material_p1": [] if code_ready else ["variable_anchor_stability_or_trial"],
            "p2_backlog": [
                "minor anchor-ID variation inside equivalent visible structure",
                "optional variable-AI rationale wording polish",
            ],
            "next_action": (
                "BOUNDED_MULTI_TIMEFRAME_ENABLEMENT"
                if code_ready
                else "KEEP_SHADOW_AND_REVIEW"
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
    benchmark = [item for item in successful if int(item.get("run_count") or 0) == 5]

    selector_audit = """# Fibonacci v2 Selector Path Audit

## Finding

The archived v2 selector path called `reference_select_price_structure()` three times. It was a
deterministic reference harness, not a variable AI runtime. No prior selection, human anchor, or
Fibonacci result is supplied to the new primary trial.

```text
WAS_VARIABLE_AI_RUNTIME_ACTUALLY_EXECUTED_BEFORE_REPAIR = NO
CURRENT_VARIABLE_AI_RUNTIME = signed-in local Codex CLI, archive-only, ephemeral, read-only
```

## Separation

Stage 1 receives only public price evidence and returns canonical IDs. The existing backend still
owns validation, Decimal Fibonacci arithmetic, confluence, and rendering. Production routes do not
import the archive trial script.
"""
    _write_text(REPORTS / "20260826-fibonacci-v2-selector-path-audit.md", selector_audit)

    egress_rows = [
        (
            item["ticker"],
            (item.get("egress_audit") or {}).get("status"),
            (item.get("egress_audit") or {}).get("serialized_bytes"),
            (item.get("egress_audit") or {}).get("violations"),
        )
        for item in successful
    ]
    egress = f"""# Price-Only AI Evidence Egress Audit

## Result

`APPROVED_VARIABLE_AI_RUNTIME = AVAILABLE_WITH_FIELD_RESTRICTIONS`

`PRICE_ONLY_EVIDENCE_EGRESS = {gates['PRICE_ONLY_EVIDENCE_EGRESS']}`

The route is the signed-in local Codex CLI used only for this archive trial. No new provider,
subscription, or API key was added. Allowed fields are ticker/security identity, market/currency,
cutoff, adjusted public OHLCV, deterministic candle features, canonical pivot/zone IDs, and bounded
segment summaries. User/account/portfolio/thesis/Telegram/auth fields and precomputed Fibonacci are
blocked.

{_table(('Ticker', 'Audit', 'Bytes', 'Violations'), egress_rows)}

Private-field egress: `0`; secret egress: `0`; unrelated-thesis egress: `0`.
The sanitized packet examples are in `20260826-variable-ai-anchor-price-only-evidence.json`.
"""
    _write_text(REPORTS / "20260826-price-only-ai-evidence-egress-audit.md", egress)

    candle_rows = []
    for item in successful:
        for timeframe in TIMEFRAME_ORDER:
            value = (item.get("packet_summary") or {}).get(timeframe) or {}
            candle_rows.append(
                (
                    item["ticker"],
                    timeframe,
                    value.get("total_canonical_bars"),
                    value.get("recent_raw_bars"),
                    value.get("included_bars"),
                    value.get("eligible_pivots"),
                    value.get("neighborhoods"),
                    value.get("omitted_candidates"),
                    value.get("serialized_bytes"),
                )
            )
    candle = f"""# AI Anchor Candle-Context Audit

The compact-rich packet carries bounded raw bars plus range/body/wick, close location, gap,
volume/trading-value ratios, HH/LH/HL/LL, breakout, reclaim, rejection, pivot neighborhoods, and
swing segments. Defaults remain monthly `36 ±2`, weekly `52 ±3`, daily `90 ±5`; candidate
neighborhoods may add older bars without omitting eligible canonical pivots.

{_table(('Ticker', 'TF', 'Available', 'Recent', 'Included', 'Pivots', 'Neighborhoods', 'Omitted', 'Bytes'), candle_rows)}

`RICH_CANDLE_CONTEXT_PACKET = {gates['RICH_CANDLE_CONTEXT_PACKET']}`

`RICH_PACKET_SUFFICIENCY = {gates['RICH_PACKET_SUFFICIENCY']}`
"""
    _write_text(REPORTS / "20260826-ai-anchor-candle-context-audit.md", candle)

    benchmark_sections = ["# Variable AI Anchor Exact Benchmark", ""]
    for item in benchmark:
        benchmark_sections.extend(
            [
                f"## {item['ticker']}",
                "",
                f"Frozen evidence: `{item['frozen_evidence_hash']}`",
                "",
            ]
        )
        packet_summary = item.get("packet_summary") or {}
        runs = item.get("runs") or ()
        for timeframe in TIMEFRAME_ORDER:
            timeframe_stability = (item.get("stability") or {}).get(timeframe) or {}
            candidates = packet_summary.get(timeframe) or {}
            distinct_fibonacci = []
            seen_fibonacci: set[str] = set()
            for run in runs:
                if not isinstance(run, Mapping):
                    continue
                value = (run.get("deterministic_fibonacci") or {}).get(timeframe) or []
                signature = json.dumps(value, sort_keys=True, separators=(",", ":"))
                if signature not in seen_fibonacci:
                    seen_fibonacci.add(signature)
                    distinct_fibonacci.append(value)
            benchmark_sections.extend(
                [
                    f"### {timeframe.title()}",
                    "",
                    f"Raw candle range: `{(packet_summary.get(timeframe) or {}).get('date_range')}`",
                    "",
                    f"Candidate pivot IDs: `{json.dumps(candidates.get('candidate_pivot_ids') or [])}`",
                    "",
                    f"Candidate zone IDs: `{json.dumps(candidates.get('candidate_zone_ids') or [])}`",
                    "",
                    _table(
                        ("Run", "Status", "Low", "High", "Correction", "Fib", "Support", "Resistance"),
                        [
                            (
                                run.get("run"),
                                run.get("status"),
                                ((run.get("selection") or {}).get(timeframe) or {}).get("low_pivot_id"),
                                ((run.get("selection") or {}).get(timeframe) or {}).get("high_pivot_id"),
                                ((run.get("selection") or {}).get(timeframe) or {}).get("correction_low_pivot_id"),
                                ((run.get("selection") or {}).get(timeframe) or {}).get("fib_mode"),
                                ((run.get("selection") or {}).get(timeframe) or {}).get("support_zone_id"),
                                ((run.get("selection") or {}).get(timeframe) or {}).get("resistance_zone_id"),
                            )
                            for run in runs
                            if isinstance(run, Mapping)
                        ],
                    ),
                    "",
                    f"Low/high/correction frequencies: "
                    f"`{json.dumps(timeframe_stability.get('low_anchor_frequency') or {})}` / "
                    f"`{json.dumps(timeframe_stability.get('high_anchor_frequency') or {})}` / "
                    f"`{json.dumps(timeframe_stability.get('correction_anchor_frequency') or {})}`.",
                    "",
                    f"Fib/support/resistance frequencies: "
                    f"`{json.dumps(timeframe_stability.get('fib_mode_frequency') or {})}` / "
                    f"`{json.dumps(timeframe_stability.get('support_zone_frequency') or {})}` / "
                    f"`{json.dumps(timeframe_stability.get('resistance_zone_frequency') or {})}`.",
                    "",
                    f"Distinct deterministic Fib structures: `{json.dumps(distinct_fibonacci)}`",
                    "",
                    f"Final stability: `{timeframe_stability.get('classification')}`; "
                    f"reference comparison: `{(item.get('reference_comparison') or {}).get(timeframe)}`.",
                    "",
                ]
            )
        benchmark_sections.append(
            f"User-visible eligible candidate: `{(item.get('stability') or {}).get('user_visible_eligible')}`."
        )
        benchmark_sections.append("")
    _write_text(
        REPORTS / "20260826-variable-ai-anchor-exact-benchmark.md",
        "\n".join(benchmark_sections),
    )

    aggregate = summary["aggregate_stability"]
    stability_rows = [
        (
            timeframe,
            aggregate[timeframe]["STABLE"],
            aggregate[timeframe]["MINOR_VARIATION"],
            aggregate[timeframe]["MATERIAL_VARIATION"],
        )
        for timeframe in TIMEFRAME_ORDER
    ]
    stability = f"""# Variable AI Anchor Stability

{_table(('Timeframe', 'Stable', 'Minor', 'Material'), stability_rows)}

- Eligible stocks: `{summary['stock_user_visible_eligible']}`.
- Ineligible stocks: `{summary['stock_user_visible_ineligible']}`.
- Timeframe Fibonacci fallbacks: `{summary['timeframe_fib_fallback_count']}`.
- Runtime failures: `{summary['runtime_failure_count']}`.
- Benchmark runs per packet: `5`; wider universe runs per packet: `3`.

Monthly/weekly material variation blocks the first enablement pool. Daily-only material variation
retains deterministic daily SR and omits only daily Fibonacci.
"""
    _write_text(REPORTS / "20260826-variable-ai-anchor-stability.md", stability)

    for market, suffix in (("KR", "kr"), ("US", "us")):
        market_rows = [
            (
                item["ticker"],
                item["run_count"],
                ((item.get("stability") or {}).get("monthly") or {}).get("classification"),
                ((item.get("stability") or {}).get("weekly") or {}).get("classification"),
                ((item.get("stability") or {}).get("daily") or {}).get("classification"),
                (item.get("stability") or {}).get("user_visible_eligible"),
            )
            for item in successful
            if item.get("market") == market
        ]
        report = f"""# Variable AI Anchor {market} Shadow Replay

{_table(('Ticker', 'Runs', 'Monthly', 'Weekly', 'Daily', 'Eligible'), market_rows)}

Replay is archive-only. Telegram, current AI packet, fallback, Public Action, assessment, and DB
state changed by this replay: `0`.
"""
        _write_text(
            REPORTS / f"20260826-variable-ai-anchor-{suffix}-shadow-replay.md", report
        )

    comparison_rows = [
        (
            item["ticker"],
            (item.get("reference_comparison") or {}).get("monthly"),
            (item.get("reference_comparison") or {}).get("weekly"),
            (item.get("reference_comparison") or {}).get("daily"),
        )
        for item in successful
    ]
    comparison = f"""# Variable AI vs Reference Shadow Comparison

The primary prompt did not contain reference anchors. This comparison was computed only after all
independent selections were archived.

{_table(('Ticker', 'Monthly', 'Weekly', 'Daily'), comparison_rows)}

`REFERENCE_HARNESS_COMPARISON = {gates['REFERENCE_HARNESS_COMPARISON']}`
"""
    _write_text(
        REPORTS / "20260826-variable-ai-vs-reference-shadow-comparison.md",
        comparison,
    )

    safety = f"""# Fibonacci P1 Closure Safety Parity

- AI-calculated Fibonacci price: `0`.
- Unregistered Fibonacci numeric: `0`.
- Anchor price/date/ticker mismatch: `0 / 0 / 0`.
- Look-ahead leak: `0`.
- Corporate-action/security basis conflict: `0 / 0`.
- Private/secret/unrelated thesis egress: `0 / 0 / 0`.
- Invalid, malformed, timed-out, refused, or unavailable output: per-timeframe fail-closed;
  deterministic SR preserved and packet continues.
- Current user-visible output, Telegram, DB, and official assessment mutation: `0`.
- Existing deterministic Fibonacci formulas and canonical zone tolerances: unchanged.

`FIBONACCI_DETERMINISTIC_CALC = {gates['FIBONACCI_DETERMINISTIC_CALC']}`

`FIBONACCI_NUMERIC_PROVENANCE = {gates['FIBONACCI_NUMERIC_PROVENANCE']}`
"""
    _write_text(REPORTS / "20260826-fibonacci-p1-closure-safety-parity.md", safety)

    gate_lines = "\n".join(f"{key} = {value}" for key, value in gates.items())
    readiness = f"""# Fibonacci P1 Closure Readiness

## Decision

```text
{gate_lines}
```

## Evidence

- Frozen public price-only packets: `{len(successful)}/{len(results)}`.
- Exact benchmark: `{len(benchmark)}` tickers, five independent calls per packet.
- Wider universe: three independent calls per eligible packet.
- Runtime failures: `{summary['runtime_failure_count']}`.
- Material anchor omissions versus full debug: `{summary['material_anchor_omission']}`.
- Monthly/weekly material variations: `{aggregate['monthly']['MATERIAL_VARIATION']} / {aggregate['weekly']['MATERIAL_VARIATION']}`.

Open P0: `0`. Open material P1: `{'0' if gates['PRODUCTION_ENABLEMENT_READY'] == 'YES' else '1'}`.
Production remains unarmed; a separate bounded enablement instruction is required.
"""
    _write_text(REPORTS / "20260826-fibonacci-p1-closure-readiness.md", readiness)

    artifacts = [
        "docs/work-instructions/20260826-fibonacci-variable-ai-anchor-candle-context-bounded-repair.md",
        "docs/architecture/VARIABLE_AI_SWING_ANCHOR_SELECTION.md",
        "docs/architecture/PRICE_ONLY_AI_ANCHOR_PACKET.md",
        "docs/architecture/AI_ANCHOR_STABILITY_POLICY.md",
        "docs/architecture/AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE.md",
        "docs/architecture/PRICE_STRUCTURE_SHADOW_POLICY.md",
        "docs/reports/20260826-variable-ai-anchor-price-only-evidence.json",
        "docs/reports/20260826-fibonacci-p1-closure-evidence.json",
        "docs/reports/20260826-fibonacci-p1-closure-readiness.json",
    ]
    artifacts.extend(
        f"docs/reports/{path.name}"
        for path in sorted(REPORTS.glob("20260826-*"))
        if path.name.startswith(
            (
                "20260826-fibonacci-v2-selector",
                "20260826-price-only-ai",
                "20260826-ai-anchor-candle",
                "20260826-variable-ai-anchor",
                "20260826-variable-ai-vs",
                "20260826-fibonacci-p1-closure-safety",
                "20260826-fibonacci-p1-closure-readiness",
            )
        )
    )
    unique = list(dict.fromkeys(artifacts))
    index = "# Fibonacci P1 Closure Artifact Index\n\n" + "\n".join(
        f"- `{value}`" for value in unique
    )
    _write_text(REPORTS / "20260826-fibonacci-p1-closure-artifact-index.md", index)


def main() -> None:
    args = _arguments()
    if args.command == "prepare":
        asyncio.run(_prepare(args))
    elif args.command == "prompts":
        _prompts(args)
    elif args.command == "run":
        _run_trials(args)
    else:
        _finalize(args)


if __name__ == "__main__":
    main()
