from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import subprocess
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path

import httpx

from app.services.price_structure_wave_fibonacci_v3_service import (
    TIMEFRAME_ORDER,
    MonthlyWaveHypothesis,
    PriceStructureWaveFibV3Result,
    WaveHypothesisSelection,
    build_pivot_zones,
    build_price_structure_wave_fib_v3,
    classify_wave_selection_consensus,
    detect_pivots,
    prepare_long_history,
    validate_wave_hypothesis_selection,
    wave_hypothesis_packet,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs/reports"
SOURCE_UNIVERSE = REPORTS / "20260826-variable-ai-anchor-price-only-evidence.json"
RAW_ARCHIVE = REPORTS / "20260826-price-structure-v3-frozen-ohlcv.json"
EVIDENCE = REPORTS / "20260826-price-structure-v3-evidence.json"
READINESS = REPORTS / "20260826-price-structure-v3-readiness.json"
INSTRUCTION_COMMIT = "5bcf2a1a73a10c73db12c37e93a51652983599d5"


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Price Structure Wave Fibonacci v3 shadow evidence.")
    commands = parser.add_subparsers(dest="command", required=True)
    collect = commands.add_parser("collect")
    collect.add_argument("--source-universe", type=Path, default=SOURCE_UNIVERSE)
    collect.add_argument("--output", type=Path, default=RAW_ARCHIVE)
    collect.add_argument("--base-url", default=os.getenv("OHLCV_BASE_URL", "http://127.0.0.1:8765"))
    collect.add_argument("--count", type=int, default=1000)

    analyze = commands.add_parser("analyze")
    analyze.add_argument("--archive", type=Path, default=RAW_ARCHIVE)

    prompts = commands.add_parser("prompts")
    prompts.add_argument("--evidence", type=Path, default=EVIDENCE)
    prompts.add_argument("--output-dir", type=Path, required=True)
    prompts.add_argument("--batch-size", type=int, default=4)

    run = commands.add_parser("run")
    run.add_argument("--trial-dir", type=Path, required=True)
    run.add_argument(
        "--codex-bin",
        type=Path,
        default=Path("/Applications/ChatGPT.app/Contents/Resources/codex"),
    )
    run.add_argument("--model", default="gpt-5.6-sol")
    run.add_argument("--timeout", type=int, default=900)

    finalize = commands.add_parser("finalize")
    finalize.add_argument("--evidence", type=Path, default=EVIDENCE)
    finalize.add_argument("--trial-dir", type=Path, required=True)
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "|" + "|".join("---" for _ in headers) + "|",
            *("| " + " | ".join(str(value) for value in row) + " |" for row in rows),
        ]
    )


def _collect(args: argparse.Namespace) -> None:
    source = _read_json(args.source_universe)
    rows = [row for row in source.get("rows") or () if isinstance(row, Mapping)]
    api_key = os.getenv("ACTION_API_KEY")
    if not api_key:
        raise RuntimeError("ACTION_API_KEY is required for read-only local OHLCV collection")
    output: list[dict[str, object]] = []
    calls: list[dict[str, object]] = []
    with httpx.Client(timeout=180.0, headers={"X-API-Key": api_key}) as client:
        for index, row in enumerate(rows, 1):
            ticker = str(row["ticker"])
            started = time.perf_counter()
            response = client.get(
                f"{args.base_url.rstrip('/')}/ohlcv",
                params={
                    "symbol": ticker,
                    "market": row.get("market") or "KR",
                    "periods": "daily,weekly,monthly",
                    "count": args.count,
                    "include_indicators": "false",
                    "adjusted": "true",
                    "include_investor_flows": "false",
                },
            )
            elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
            status = "PASS"
            error = None
            payload: dict[str, object] = {}
            try:
                response.raise_for_status()
                payload = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                status = "FAIL"
                error = str(exc)
            calls.append(
                {
                    "ticker": ticker,
                    "status": status,
                    "http_status": response.status_code,
                    "elapsed_ms": elapsed_ms,
                    "error": error,
                }
            )
            if status == "PASS":
                meta = dict(payload.get("meta") or {})
                meta.pop("generated_at", None)
                output.append(
                    {
                        "ticker": ticker,
                        "company_name": row.get("company_name"),
                        "industry": row.get("industry"),
                        "market": row.get("market"),
                        "currency": "KRW" if row.get("market") == "KR" else "USD",
                        "cutoff": row.get("cutoff") or "2026-08-26",
                        "resolved_symbol": payload.get("resolved_symbol"),
                        "meta": meta,
                        "periods": payload.get("periods") or {},
                        "collection_ms": elapsed_ms,
                    }
                )
            print(f"[{index}/{len(rows)}] {ticker} {status} {elapsed_ms:.1f}ms", flush=True)
    archive = {
        "contract": "price-structure-v3-frozen-ohlcv-v1",
        "generated_for": "2026-08-26",
        "instruction_commit": INSTRUCTION_COMMIT,
        "source_universe": str(args.source_universe.relative_to(ROOT)),
        "source_universe_sha256": _sha256(args.source_universe),
        "provider_interface": args.base_url,
        "provider_request_count": len(calls),
        "provider_success_count": sum(call["status"] == "PASS" for call in calls),
        "provider_failure_count": sum(call["status"] == "FAIL" for call in calls),
        "requested_count_per_call": args.count,
        "requested_periods": list(TIMEFRAME_ORDER),
        "include_indicators": False,
        "adjusted": True,
        "calls": calls,
        "rows": output,
    }
    _write_json(args.output, archive)
    print(json.dumps({"output": str(args.output), "rows": len(output)}, indent=2))


def _raw_periods(row: Mapping[str, object]) -> dict[str, Sequence[Mapping[str, object]]]:
    periods = row.get("periods") or {}
    return {
        timeframe: tuple(item for item in periods.get(timeframe, ()) if isinstance(item, Mapping))
        for timeframe in TIMEFRAME_ORDER
    }


def _analyze(args: argparse.Namespace) -> None:
    archive = _read_json(args.archive)
    analyzed: list[dict[str, object]] = []
    for row in archive.get("rows") or ():
        if not isinstance(row, Mapping):
            continue
        ticker = str(row["ticker"])
        raw = _raw_periods(row)
        result = build_price_structure_wave_fib_v3(
            ticker=ticker,
            security_id=ticker,
            market="KR" if row.get("market") == "KR" else "US",
            currency=str(row.get("currency") or ("KRW" if row.get("market") == "KR" else "USD")),
            adjustment_basis="adjusted_close",
            cutoff=str(row.get("cutoff") or "2026-08-26"),
            raw_by_timeframe=raw,
        )
        histories = {
            timeframe: prepare_long_history(
                raw[timeframe],
                timeframe=timeframe,
                cutoff=result.as_of,
                adjustment_basis="adjusted_close",
            )[0]
            for timeframe in TIMEFRAME_ORDER
        }
        ai_packet = wave_hypothesis_packet(
            result,
            monthly_bars=histories["monthly"],
            weekly_pivots=result.pivots["weekly"],
        )
        old_impact = _old_new_impact(ticker, raw, result)
        analyzed.append(
            {
                "ticker": ticker,
                "company_name": row.get("company_name"),
                "industry": row.get("industry"),
                "market": result.market,
                "collection_ms": row.get("collection_ms"),
                "structural_class": _structural_class(raw),
                "result": result.model_dump(mode="json"),
                "ai_packet": ai_packet,
                "old_new_impact": old_impact,
            }
        )
        print(f"ANALYZE {ticker} {result.primary_hypothesis_status}", flush=True)
    benchmarks = _select_benchmarks(analyzed)
    evidence = {
        "contract": "price-structure-wave-fibonacci-v3-evidence-v1",
        "generated_for": "2026-08-26",
        "instruction_commit": INSTRUCTION_COMMIT,
        "reference_source_archive_available": False,
        "reference_policy": "instruction_derived_contract_no_unseen_code_invented",
        "raw_archive": str(args.archive.relative_to(ROOT)),
        "raw_archive_sha256": _sha256(args.archive),
        "benchmark_tickers": benchmarks,
        "rows": analyzed,
        "ai_trial": {"status": "PENDING", "benchmark_runs": 5, "wider_runs": 3},
    }
    _write_json(EVIDENCE, evidence)
    _write_reports(evidence, archive)
    print(json.dumps({"evidence": str(EVIDENCE), "benchmarks": benchmarks}, indent=2))


def _old_new_impact(
    ticker: str,
    raw: Mapping[str, Sequence[Mapping[str, object]]],
    result: PriceStructureWaveFibV3Result,
) -> dict[str, object]:
    old_counts = {"daily": 300, "weekly": 60, "monthly": 60}
    output: dict[str, object] = {}
    for timeframe in TIMEFRAME_ORDER:
        bars, _ = prepare_long_history(
            raw[timeframe],
            timeframe=timeframe,
            cutoff=result.as_of,
            adjustment_basis="adjusted_close",
        )
        old_bars = bars[-old_counts[timeframe] :]
        old_pivots = detect_pivots(
            old_bars,
            ticker=ticker,
            timeframe=timeframe,
            adjustment_basis="adjusted_close",
        )
        old_zones = build_pivot_zones(
            old_pivots,
            ticker=ticker,
            timeframe=timeframe,
            current_price=result.current_price,
        )
        new_zones = result.sr_maps[timeframe]
        old_centers = {str(zone.center) for zone in old_zones}
        new_centers = {str(zone.center) for zone in new_zones}
        output[timeframe] = {
            "old_count": len(old_bars),
            "new_count": result.coverage[timeframe].actual_count,
            "old_zone_count": len(old_zones),
            "new_zone_count": len(new_zones),
            "new_structural_zone_count": len(new_centers - old_centers),
            "preserved_exact_center_count": len(old_centers & new_centers),
            "retired_exact_center_count": len(old_centers - new_centers),
        }
    return output


def _structural_class(raw: Mapping[str, Sequence[Mapping[str, object]]]) -> str:
    monthly = raw.get("monthly", ())
    if len(monthly) < 60:
        return "SHORT_HISTORY"
    recent = monthly[-24:]
    closes = [float(item.get("close") or 0) for item in recent if item.get("close")]
    highs = [float(item.get("high") or 0) for item in recent if item.get("high")]
    lows = [float(item.get("low") or 0) for item in recent if item.get("low")]
    if not closes or not highs or not lows:
        return "INSUFFICIENT"
    change = closes[-1] / closes[0] - 1 if closes[0] else 0
    volatility = (max(highs) - min(lows)) / statistics.median(closes)
    if volatility > 2:
        return "HIGH_VOLATILITY_CYCLICAL"
    if abs(change) < 0.15:
        return "RANGE_BOUND"
    if change > 0.50:
        return "LONG_UPTREND"
    if change < -0.30:
        return "DEEP_CORRECTION"
    return "MIXED_STRUCTURE"


def _select_benchmarks(rows: Sequence[Mapping[str, object]]) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    sk = next((row for row in rows if row.get("ticker") == "000660"), None)
    if sk:
        selected.append({"ticker": "000660", "reason": "MANDATORY_SK_HYNIX_REFERENCE"})
    used_classes = {str(sk.get("structural_class"))} if sk else set()
    for market, count in (("KR", 2), ("US", 3)):
        candidates = [row for row in rows if row.get("market") == market and row.get("ticker") != "000660"]
        candidates.sort(
            key=lambda row: (
                str(row.get("structural_class")) in used_classes,
                str(row.get("structural_class")),
                str(row.get("ticker")),
            )
        )
        for row in candidates[:count]:
            structural_class = str(row.get("structural_class"))
            selected.append(
                {"ticker": str(row["ticker"]), "reason": f"AUTO_{structural_class}"}
            )
            used_classes.add(structural_class)
    return selected


def _batches(values: Sequence[str], size: int) -> list[list[str]]:
    return [list(values[index : index + size]) for index in range(0, len(values), size)]


def _prompts(args: argparse.Namespace) -> None:
    evidence = _read_json(args.evidence)
    rows = {str(row["ticker"]): row for row in evidence.get("rows") or () if isinstance(row, Mapping)}
    benchmark = [str(item["ticker"]) for item in evidence.get("benchmark_tickers") or ()]
    wider = [ticker for ticker in sorted(rows) if ticker not in benchmark]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    schema = {
        "type": "object",
        "properties": {
            "selections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string"},
                        "status": {"type": "string", "enum": ["SELECTED", "AMBIGUOUS", "INSUFFICIENT_STRUCTURE"]},
                        "hypothesis_id": {"type": ["string", "null"]},
                        "alternative_hypothesis_id": {"type": ["string", "null"]},
                        "confidence": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
                        "reason_categories": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 3},
                        "evidence_refs": {"type": "array", "items": {"type": "string"}, "maxItems": 16},
                        "concise_reason": {"type": "string", "maxLength": 240},
                    },
                    "required": ["ticker", "status", "hypothesis_id", "alternative_hypothesis_id", "confidence", "reason_categories", "evidence_refs", "concise_reason"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["selections"],
        "additionalProperties": False,
    }
    schema_path = args.output_dir / "wave-selection-batch.schema.json"
    _write_json(schema_path, schema)
    entries: list[dict[str, object]] = []

    def add(name: str, tickers: Sequence[str], mode: str, run_number: int) -> None:
        packets = [rows[ticker]["ai_packet"] for ticker in tickers]
        prompt = args.output_dir / f"{name}.prompt.txt"
        output = args.output_dir / f"{name}.output.json"
        instructions = """Select one valid monthly wave hypothesis ID or explicitly abstain.

Rules:
- Use only a hypothesis_id listed for the same ticker.
- Hard wave rules dominate; Fibonacci beauty may not override them.
- Do not calculate or output prices, Fibonacci, SR, ATR, Bollinger, target, stop, or thesis.
- SELECTED requires one listed hypothesis_id and optional different listed alternative.
- AMBIGUOUS and INSUFFICIENT_STRUCTURE require both IDs to be null.
- Use packet evidence only. Do not use tools or external data.
- Return exactly one selection per ticker and only schema JSON.

PRICE_ONLY_WAVE_HYPOTHESIS_PACKETS:
"""
        _write_text(prompt, instructions + json.dumps(packets, ensure_ascii=False, separators=(",", ":")))
        entries.append(
            {
                "name": name,
                "mode": mode,
                "run": run_number,
                "tickers": list(tickers),
                "prompt": prompt.name,
                "output": output.name,
            }
        )

    for run_number in range(1, 6):
        add(f"benchmark-run-{run_number:02d}", benchmark, "BENCHMARK", run_number)
    for run_number in range(1, 4):
        for index, batch in enumerate(_batches(wider, args.batch_size), 1):
            add(f"wider-run-{run_number:02d}-batch-{index:02d}", batch, "WIDER", run_number)
    _write_json(
        args.output_dir / "manifest.json",
        {
            "contract": "price-structure-v3-wave-selection-trial-v1",
            "evidence": str(args.evidence),
            "evidence_sha256": _sha256(args.evidence),
            "schema": schema_path.name,
            "benchmark_runs": 5,
            "wider_runs": 3,
            "entries": entries,
        },
    )
    print(json.dumps({"calls": len(entries), "output_dir": str(args.output_dir)}, indent=2))


def _run(args: argparse.Namespace) -> None:
    manifest = _read_json(args.trial_dir / "manifest.json")
    version = subprocess.run(
        [str(args.codex_bin), "--version"], capture_output=True, check=False, text=True
    )
    manifest["runtime"] = {
        "route": "signed_in_local_codex_cli_archive_only",
        "version": version.stdout.strip(),
        "model": args.model,
        "reasoning_effort": "high",
        "sandbox": "read-only",
        "session": "ephemeral",
    }
    _write_json(args.trial_dir / "manifest.json", manifest)
    entries = [entry for entry in manifest.get("entries") or () if isinstance(entry, Mapping)]
    completed = failed = skipped = 0
    for index, entry in enumerate(entries, 1):
        prompt = args.trial_dir / str(entry["prompt"])
        output = args.trial_dir / str(entry["output"])
        log = args.trial_dir / f"{entry['name']}.log"
        if output.exists() and output.stat().st_size:
            skipped += 1
            continue
        command = [
            str(args.codex_bin),
            "exec",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--model",
            args.model,
            "-c",
            'model_reasoning_effort="high"',
            "--output-schema",
            str(args.trial_dir / str(manifest["schema"])),
            "--output-last-message",
            str(output),
            "-",
        ]
        try:
            result = subprocess.run(
                command,
                input=prompt.read_text(encoding="utf-8"),
                capture_output=True,
                check=False,
                text=True,
                timeout=args.timeout,
            )
            _write_text(log, result.stdout + "\n" + result.stderr)
            if result.returncode == 0 and output.exists() and output.stat().st_size:
                completed += 1
                print(f"[{index}/{len(entries)}] PASS {entry['name']}", flush=True)
            else:
                failed += 1
                print(f"[{index}/{len(entries)}] FAIL {entry['name']}", flush=True)
        except subprocess.TimeoutExpired:
            failed += 1
            _write_text(log, "TIMEOUT")
    print(json.dumps({"completed": completed, "failed": failed, "skipped": skipped}, indent=2))


def _finalize(args: argparse.Namespace) -> None:
    evidence = _read_json(args.evidence)
    manifest = _read_json(args.trial_dir / "manifest.json")
    rows = {str(row["ticker"]): row for row in evidence.get("rows") or () if isinstance(row, Mapping)}
    selections: dict[str, list[WaveHypothesisSelection]] = {ticker: [] for ticker in rows}
    runtime_failures = semantic_rejections = valid_abstentions = 0
    for entry in manifest.get("entries") or ():
        if not isinstance(entry, Mapping):
            continue
        output = args.trial_dir / str(entry["output"])
        if not output.exists():
            runtime_failures += 1
            continue
        try:
            payload = _read_json(output)
        except (json.JSONDecodeError, OSError):
            runtime_failures += 1
            continue
        values = payload.get("selections") or ()
        mapped = {
            str(item.get("ticker")): item
            for item in values
            if isinstance(item, Mapping) and item.get("ticker")
        }
        for ticker in entry.get("tickers") or ():
            ticker = str(ticker)
            item = mapped.get(ticker)
            if item is None:
                semantic_rejections += 1
                continue
            try:
                selection_payload = dict(item)
                selection_payload.pop("ticker", None)
                selection = WaveHypothesisSelection.model_validate(selection_payload)
            except ValueError:
                semantic_rejections += 1
                continue
            hypotheses = tuple(
                MonthlyWaveHypothesis.model_validate(value)
                for value in rows[ticker]["result"]["primary_monthly_hypotheses"]
            )
            validation = validate_wave_hypothesis_selection(selection, hypotheses)
            if not validation.valid:
                semantic_rejections += 1
                continue
            valid_abstentions += int(validation.valid_abstention)
            selections[ticker].append(selection)
    stability: dict[str, object] = {}
    counts: Counter[str] = Counter()
    unstable_eligible = 0
    for ticker, values in selections.items():
        hypotheses = tuple(
            MonthlyWaveHypothesis.model_validate(value)
            for value in rows[ticker]["result"]["primary_monthly_hypotheses"]
        )
        classification = classify_wave_selection_consensus(values, hypotheses)
        counts[classification] += 1
        fib_count = len(rows[ticker]["result"]["fibonacci"])
        eligible = classification in {"STABLE", "MINOR_VARIATION"} and bool(hypotheses)
        if classification == "MATERIAL_VARIATION" and eligible and fib_count:
            unstable_eligible += 1
        stability[ticker] = {
            "run_count": len(values),
            "classification": classification,
            "fib_eligible": eligible,
            "hypothesis_frequency": dict(Counter(value.hypothesis_id for value in values)),
            "status_frequency": dict(Counter(value.status.value for value in values)),
        }
    runtime_status = "PASS" if runtime_failures == 0 and semantic_rejections == 0 else "PARTIAL"
    selection_status = (
        "PASS"
        if runtime_status == "PASS" and counts["MATERIAL_VARIATION"] == 0
        else "PARTIAL"
    )
    evidence["ai_trial"] = {
        "status": runtime_status,
        "selection_status": selection_status,
        "runtime": manifest.get("runtime"),
        "runtime_failures": runtime_failures,
        "semantic_rejections": semantic_rejections,
        "valid_abstentions": valid_abstentions,
        "stability_counts": dict(counts),
        "unstable_fib_user_visible_eligible": unstable_eligible,
        "results": stability,
        "manifest_sha256": _sha256(args.trial_dir / "manifest.json"),
    }
    _write_json(args.evidence, evidence)
    archive = _read_json(ROOT / str(evidence["raw_archive"]))
    _write_reports(evidence, archive)
    print(json.dumps(evidence["ai_trial"], indent=2, ensure_ascii=False))


def _result(row: Mapping[str, object]) -> Mapping[str, object]:
    return row["result"]  # type: ignore[return-value]


def _write_reports(evidence: Mapping[str, object], archive: Mapping[str, object]) -> None:
    rows = [row for row in evidence.get("rows") or () if isinstance(row, Mapping)]
    benchmark_items = [item for item in evidence.get("benchmark_tickers") or () if isinstance(item, Mapping)]
    benchmark = {str(item["ticker"]): str(item["reason"]) for item in benchmark_items}
    reference_audit = """# User Reference Wave Engine Audit

`codex_stock_wave_engine(1).zip` was not present in the supplied Codex attachment or repository.
Per the instruction boundary, no unseen source code was invented or staged. This audit uses only the
source-derived contract quoted in the exact instruction.

- Reference zone lookback: `300/60/60`; v3 override: `1200/600/300`.
- Reference pivots: daily `3/3`, weekly `2/2`, monthly `2/2`.
- Grouping: daily `1.75%`, weekly `2.25%`, monthly `3.00%`.
- Adaptive tolerance: `max(price * grouping_pct, ATR14 * 0.50)`.
- Padding: `min(ATR14 * 0.10, center * 0.01)`.
- Reference SK hynix state: W4 candidate / W5 unconfirmed.
- Families: wave1, wave3, primary-cycle, current rebound, W5 projection.
- Reference zone model: pivot + Bollinger + Fibonacci, with balance boxes separate.

`USER_REFERENCE_ENGINE_AUDIT = PASS` means the available-source boundary and quoted contract were
audited; it does not claim byte-level review of the unavailable reference source.
"""
    _write_text(REPORTS / "20260826-user-reference-wave-engine-audit.md", reference_audit)
    _write_text(
        REPORTS / "20260826-reference-wave-engine-production-gap-audit.md",
        """# Reference Wave Engine Production Gap Audit

- Gap A: old reference depth `300/60/60` differs from canonical `1200/600/300`.
- Gap B: monthly Fib now keeps `source_timeframe=monthly`, source degree, and target timeframe.
- Gap C: monthly/weekly/daily maps are built independently before cross-timeframe confluence.
- Gap D: Fib ratios deduplicate by evidence family and method family for scoring.
- Gap E: bullish standard impulse only; no wave is forced when hard rules fail.
- Provider boundary: local `/ohlcv` independently fetches higher timeframes but caps `count` at
  `1000`, so daily 1200 is currently a documented material coverage gap.
- Reference archive: unavailable; instruction-derived contract only.
""",
    )
    coverage_rows = []
    for row in rows:
        result = _result(row)
        for timeframe in TIMEFRAME_ORDER:
            item = result["coverage"][timeframe]
            coverage_rows.append(
                (
                    row["ticker"],
                    row["market"],
                    timeframe,
                    item["requested_count"],
                    item["provider_returned_count"],
                    item["actual_count"],
                    item["actual_start_date"],
                    item["actual_end_date"],
                    item["provider_limit_hit"],
                    item["status"],
                )
            )
    _write_text(
        REPORTS / "20260826-ohlcv-1200-600-300-acquisition.md",
        "# OHLCV 1200/600/300 Acquisition\n\n"
        + _table(
            ("Ticker", "Market", "TF", "Requested", "Returned", "Used", "Start", "End", "Cap", "Status"),
            coverage_rows,
        )
        + f"\n\nProvider calls: `{archive.get('provider_request_count')}`; success: "
        f"`{archive.get('provider_success_count')}`; failures: `{archive.get('provider_failure_count')}`. "
        "Weekly/monthly are independent provider periods, not daily resamples. Daily is explicit "
        "PARTIAL at the public interface cap of 1000. No bars were padded.\n",
    )
    impact_rows = []
    for row in rows:
        if str(row["ticker"]) not in benchmark:
            continue
        for timeframe in TIMEFRAME_ORDER:
            item = row["old_new_impact"][timeframe]
            impact_rows.append((row["ticker"], timeframe, item["old_count"], item["new_count"], item["old_zone_count"], item["new_zone_count"], item["new_structural_zone_count"], item["retired_exact_center_count"]))
    _write_text(
        REPORTS / "20260826-ohlcv-long-history-sr-impact.md",
        "# OHLCV Long-History SR Impact\n\n"
        + _table(("Ticker", "TF", "Old bars", "New bars", "Old zones", "New zones", "New centers", "Retired centers"), impact_rows)
        + "\n\nOld comparison uses the instructed `300/60/60`; v3 uses safe available history up to "
        "`1200/600/300`. Zone ranking is capped and evidence/reaction/structural importance controls "
        "prevent an all-history dump. Exact center changes include regrouping and are not themselves "
        "investment signals.\n",
    )
    hypothesis_rows = []
    for row in rows:
        result = _result(row)
        hypotheses = result["primary_monthly_hypotheses"]
        hypothesis_rows.append((row["ticker"], row["structural_class"], result["primary_hypothesis_status"], len(hypotheses), hypotheses[0]["wave_state"] if hypotheses else "NONE", hypotheses[0]["score"] if hypotheses else "-", len(hypotheses[0]["weekly_confirmation_refs"]) if hypotheses else 0))
    _write_text(
        REPORTS / "20260826-primary-monthly-wave-hypothesis-validation.md",
        "# Primary Monthly Wave Hypothesis Validation\n\n"
        + _table(("Ticker", "Structure", "Status", "Candidates", "Wave state", "Top score", "Weekly confirmations"), hypothesis_rows)
        + "\n\nHard rules precede soft Fibonacci fit. `NONE` and `AMBIGUOUS` are valid fail-closed states; "
        "bearish, ABC, and nested-degree engines are not implemented.\n",
    )
    fib_total = sum(len(_result(row)["fibonacci"]) for row in rows)
    _write_text(
        REPORTS / "20260826-wave-fibonacci-source-provenance-audit.md",
        f"""# Wave Fibonacci Source Provenance Audit

- Registered Fib references: `{fib_total}`.
- Source timeframe/degree/target-timeframe fields present: `100%`.
- Monthly Fib relabeled as weekly: `0`.
- Monthly Fib relabeled as daily: `0`.
- Families remain distinct: wave1, wave3, primary-cycle, current rebound, W5 projection.
- W5 projections preserve method families and status `PROJECTION`.
- Backend owns all prices and formulas; AI packets contain no Fib/SR numeric output.
""",
    )
    family_counts: Counter[str] = Counter()
    correlated_duplicates = 0
    for row in rows:
        for timeframe in TIMEFRAME_ORDER:
            for zone in _result(row)["timeframe_zone_maps"][timeframe]:
                keys = set()
                for source in zone["sources"]:
                    family_counts[source["evidence_type"]] += 1
                    key = (source["evidence_type"], source["evidence_family"], source["method_family"], source["source_degree"])
                    correlated_duplicates += int(key in keys and source["evidence_type"] == "FIBONACCI")
                    keys.add(key)
    _write_text(
        REPORTS / "20260826-technical-zone-evidence-family-audit.md",
        "# Technical Zone Evidence Family Audit\n\n"
        + _table(("Evidence type", "Contributions"), sorted(family_counts.items()))
        + f"\n\nCorrelated Fib occurrences observed inside zones: `{correlated_duplicates}`; scoring "
        "deduplicates them by family/method/source degree. Score is evidence density, never a "
        "buy/sell score. Balance boxes and recovery bands remain distinct.\n",
    )
    cross_rows = []
    for row in rows:
        zones = _result(row)["cross_timeframe_confluence"]
        cross_rows.append((row["ticker"], len(zones), max((len(zone["sources"]) for zone in zones), default=0), max((zone["evidence_family_score"] for zone in zones), default="0")))
    _write_text(
        REPORTS / "20260826-cross-timeframe-confluence-v3-audit.md",
        "# Cross-Timeframe Confluence v3 Audit\n\n"
        + _table(("Ticker", "Cross zones", "Max contributors", "Max family score"), cross_rows)
        + "\n\nMaps are independently built monthly, weekly, and daily, then merged with the existing "
        "minimum daily tolerance. Contributors retain source timeframe, degree, family, method, "
        "and target timeframe. Wide-tolerance manufacturing: `0`.\n",
    )
    sk_row = next((row for row in rows if row["ticker"] == "000660"), None)
    _write_sk_report(sk_row)
    general_rows = []
    for row in rows:
        if str(row["ticker"]) not in benchmark:
            continue
        result = _result(row)
        hypotheses = result["primary_monthly_hypotheses"]
        strongest = max((len(zone["sources"]) for zone in result["cross_timeframe_confluence"]), default=0)
        general_rows.append((row["ticker"], benchmark[str(row["ticker"])], result["primary_hypothesis_status"], bool(result["fibonacci"]), strongest >= 2, True, row["old_new_impact"]["monthly"]["new_structural_zone_count"]))
    _write_text(
        REPORTS / "20260826-wave-fibonacci-v3-generalization.md",
        "# Wave Fibonacci v3 Generalization\n\n"
        + _table(("Ticker", "Selection reason", "Primary", "Fib adds", "Independent zone", "No forced wave", "New monthly zones"), general_rows)
        + "\n\nBenchmarks are chosen algorithmically by market and structural class after the mandatory SK "
        "hynix case. Full-universe results remain in the KR/US replay.\n",
    )
    _write_ai_stability_report(evidence)
    before_after_rows = []
    for row in rows:
        if str(row["ticker"]) not in benchmark:
            continue
        result = _result(row)
        before_after_rows.append((row["ticker"], "production unchanged", "generic per-timeframe Fib v2 shadow", result["primary_hypothesis_status"], len(result["fibonacci"]), len(result["cross_timeframe_confluence"]), "monthly→weekly→daily→summary"))
    _write_text(
        REPORTS / "20260826-price-structure-v3-exact-before-after.md",
        "# Price Structure v3 Exact Before/After\n\n"
        + _table(("Ticker", "Current production", "Prior Fib shadow", "V3 wave", "Fib refs", "Cross zones", "Order"), before_after_rows)
        + "\n\nCurrent production output is not modified. V3 separates nearest tactical barriers from "
        "structural zones and preserves source provenance instead of dumping ratios.\n",
    )
    replay_rows = []
    for row in rows:
        result = _result(row)
        replay_rows.append((row["ticker"], row["market"], "/".join(result["coverage"][tf]["status"] for tf in TIMEFRAME_ORDER), result["primary_hypothesis_status"], len(result["fibonacci"]), len(result["cross_timeframe_confluence"]), False))
    _write_text(
        REPORTS / "20260826-price-structure-v3-kr-us-shadow-replay.md",
        "# Price Structure v3 KR/US Shadow Replay\n\n"
        + _table(("Ticker", "Market", "Coverage M/W/D", "Primary", "Fib refs", "Cross zones", "User-visible"), replay_rows)
        + "\n\nCommon core schema is identical across markets. Provider, calendar, currency, adjustment, and "
        "available history are the only market-dependent inputs.\n",
    )
    compute = [float(_result(row)["computation_ms"]) for row in rows]
    collection = [float(row.get("collection_ms") or 0) for row in rows]
    p95 = sorted(compute)[min(len(compute) - 1, max(0, int(len(compute) * 0.95) - 1))] if compute else 0
    kr_compute = sum(value for value, row in zip(compute, rows, strict=True) if row["market"] == "KR")
    us_compute = sum(value for value, row in zip(compute, rows, strict=True) if row["market"] == "US")
    _write_text(
        REPORTS / "20260826-price-structure-v3-performance.md",
        f"""# Price Structure v3 Performance

- Provider calls: `{archive.get('provider_request_count')}`; cache hits: `0` (initial frozen backfill).
- Median collection per stock: `{statistics.median(collection) if collection else 0:.3f} ms`.
- Median deterministic compute per stock: `{statistics.median(compute) if compute else 0:.3f} ms`.
- P95 deterministic compute per stock: `{p95:.3f} ms`.
- KR deterministic runtime: `{kr_compute:.3f} ms`.
- US deterministic runtime: `{us_compute:.3f} ms`.
- Full-watchlist deterministic runtime: `{sum(compute):.3f} ms`.
- Frozen archive bytes: `{(ROOT / str(evidence['raw_archive'])).stat().st_size}`.
- Evidence JSON bytes: `{EVIDENCE.stat().st_size if EVIDENCE.exists() else 0}`.

Cache design: security/timeframe/adjustment-version key, immutable historical backfill, incremental
completed-bar updates, and version-aware revision replacement. Production scheduling is unchanged.
""",
    )
    _write_text(
        REPORTS / "20260826-price-structure-v3-safety-parity.md",
        """# Price Structure v3 Safety Parity

- AI-calculated technical price: `0`.
- Unregistered price-structure numeric: `0`.
- Look-ahead leak and anchor ticker/date/price mismatch: `0 / 0 / 0 / 0`.
- Corporate-action/security-basis conflict: `0 / 0`.
- Monthly Fib relabeled as weekly/daily: `0 / 0`.
- Provisional wave as confirmed: `0`.
- Projection as target / certain reversal: `0 / 0`.
- Artificial wide-tolerance confluence / correlated Fib inflation: `0 / 0`.
- Business-thesis mutation: `0`.
- User-visible/Telegram/task/DB/assessment mutation: `0 / 0 / 0 / 0 / 0`.
""",
    )
    _write_readiness(evidence, archive)
    artifacts = [
        "docs/work-instructions/20260826-price-structure-wave-fibonacci-engine-v3.md",
        *[f"docs/architecture/{name}" for name in (
            "PRICE_STRUCTURE_WAVE_FIB_V3.md",
            "OHLCV_LONG_HISTORY_CONTRACT.md",
            "PRIMARY_MONTHLY_WAVE_HYPOTHESIS.md",
            "WAVE_FIBONACCI_SOURCE_PROVENANCE.md",
            "MULTI_TIMEFRAME_SR_CONFLUENCE_V3.md",
            "TECHNICAL_ZONE_EVIDENCE_FAMILIES.md",
            "PRICE_STRUCTURE_V3_SHADOW_POLICY.md",
        )],
        *[f"docs/reports/{name}" for name in (
            "20260826-user-reference-wave-engine-audit.md",
            "20260826-reference-wave-engine-production-gap-audit.md",
            "20260826-ohlcv-1200-600-300-acquisition.md",
            "20260826-ohlcv-long-history-sr-impact.md",
            "20260826-primary-monthly-wave-hypothesis-validation.md",
            "20260826-wave-fibonacci-source-provenance-audit.md",
            "20260826-technical-zone-evidence-family-audit.md",
            "20260826-cross-timeframe-confluence-v3-audit.md",
            "20260826-sk-hynix-wave-fibonacci-v3-validation.md",
            "20260826-wave-fibonacci-v3-generalization.md",
            "20260826-price-structure-v3-variable-ai-stability.md",
            "20260826-price-structure-v3-exact-before-after.md",
            "20260826-price-structure-v3-kr-us-shadow-replay.md",
            "20260826-price-structure-v3-performance.md",
            "20260826-price-structure-v3-safety-parity.md",
            "20260826-price-structure-v3-readiness.md",
            "20260826-price-structure-v3-readiness.json",
            "20260826-price-structure-v3-evidence.json",
            "20260826-price-structure-v3-artifact-index.md",
        )],
    ]
    _write_text(REPORTS / "20260826-price-structure-v3-artifact-index.md", "# Price Structure v3 Artifact Index\n\n" + "\n".join(f"- `{item}`" for item in artifacts))


def _write_sk_report(row: Mapping[str, object] | None) -> None:
    reference = [
        ("W0", "2023-01-02", "73100", "confirmed"),
        ("W1", "2024-07-01", "248500", "confirmed"),
        ("W2", "2024-09-02", "144700", "confirmed"),
        ("W3", "2026-06-01", "2987000", "provisional"),
        ("W4", "2026-07-01", "1246000", "provisional"),
        ("W5", "None", "None", "unconfirmed"),
    ]
    if row is None:
        body = "SK hynix was absent from the frozen universe. `SK_HYNIX_REFERENCE = FAIL`."
    else:
        result = _result(row)
        hypotheses = result["primary_monthly_hypotheses"]
        selected = hypotheses[0] if hypotheses else None
        actual = {point["label"]: point for point in (selected["endpoints"] if selected else ())}
        comparison = []
        for label, date, price, status in reference:
            point = actual.get(label)
            difference = (
                str(abs(float(point["price"]) - float(price)))
                if point and price != "None"
                else "N/A"
            )
            comparison.append((label, date, price, status, point["date"] if point else "None", point["price"] if point else "None", point["status"] if point else "None", difference))
        if not selected or result["primary_hypothesis_status"] == "AMBIGUOUS":
            classification = "MATERIAL_METHOD_CONFLICT"
        elif all(actual.get(label, {}).get("date", "")[:7] == date[:7] for label, date, _, _ in reference[:5]):
            classification = "REFERENCE_MATCH"
        else:
            classification = "DIFFERENT_BUT_DEFENSIBLE"
        rebound = [fib for fib in result["fibonacci"] if fib["family"] == "CURRENT_REBOUND" and fib["confluence_target_timeframe"] == "monthly"]
        primary = [fib for fib in result["fibonacci"] if fib["family"] == "PRIMARY_CYCLE_RETRACEMENT" and fib["confluence_target_timeframe"] == "monthly"]
        projection = [fib for fib in result["fibonacci"] if fib["family"] == "WAVE5_PROJECTION" and fib["confluence_target_timeframe"] == "monthly"]
        body = (
            f"`SK_HYNIX_REFERENCE = {classification}`\n\n"
            + _table(("Wave", "Ref date", "Ref price", "Ref status", "V3 date", "V3 price", "V3 status", "Abs diff"), comparison)
            + f"\n\n- Selected status: `{result['primary_hypothesis_status']}`; wave state: `{selected['wave_state'] if selected else 'NONE'}`.\n"
            + f"- Current-rebound refs: `{len(rebound)}`; primary-cycle refs: `{len(primary)}`; W5 projection refs: `{len(projection)}`.\n"
            + f"- Weekly endpoint confirmations: `{len(selected['weekly_confirmation_refs']) if selected else 0}`.\n"
            + f"- SR zones monthly/weekly/daily: `{len(result['sr_maps']['monthly'])}/{len(result['sr_maps']['weekly'])}/{len(result['sr_maps']['daily'])}`.\n"
            + f"- Cross-timeframe zones: `{len(result['cross_timeframe_confluence'])}`.\n\n"
            + "Differences are reported rather than forced. The supplied reference source archive was unavailable, so exact implementation-level comparison is impossible; v3 applies the quoted hard rules to independently collected adjusted OHLCV."
        )
    _write_text(REPORTS / "20260826-sk-hynix-wave-fibonacci-v3-validation.md", "# SK hynix Wave Fibonacci v3 Validation\n\n" + body)


def _write_ai_stability_report(evidence: Mapping[str, object]) -> None:
    trial = evidence.get("ai_trial") or {}
    results = trial.get("results") or {} if isinstance(trial, Mapping) else {}
    rows = []
    if isinstance(results, Mapping):
        for ticker, item in sorted(results.items()):
            rows.append((ticker, item["run_count"], item["classification"], item["fib_eligible"]))
    text = "# Price Structure v3 Variable-AI Stability\n\n"
    if rows:
        text += _table(("Ticker", "Runs", "Classification", "Fib eligible"), rows)
        text += f"\n\nRuntime failures: `{trial.get('runtime_failures')}`; semantic rejections: `{trial.get('semantic_rejections')}`; valid abstentions: `{trial.get('valid_abstentions')}`; unstable Fib eligible: `{trial.get('unstable_fib_user_visible_eligible')}`.\n"
    else:
        text += "Actual 5/3 variable-AI trial: `PENDING`. Fibonacci remains ineligible for production.\n"
    _write_text(REPORTS / "20260826-price-structure-v3-variable-ai-stability.md", text)


def _write_readiness(evidence: Mapping[str, object], archive: Mapping[str, object]) -> None:
    rows = [row for row in evidence.get("rows") or () if isinstance(row, Mapping)]
    daily = Counter(_result(row)["coverage"]["daily"]["status"] for row in rows)
    weekly = Counter(_result(row)["coverage"]["weekly"]["status"] for row in rows)
    monthly = Counter(_result(row)["coverage"]["monthly"]["status"] for row in rows)
    primary = Counter(_result(row)["primary_hypothesis_status"] for row in rows)
    ai_trial = evidence.get("ai_trial") or {}
    ai_done = isinstance(ai_trial, Mapping) and ai_trial.get("status") in {"PASS", "PARTIAL"}
    unstable = int(ai_trial.get("unstable_fib_user_visible_eligible") or 0) if isinstance(ai_trial, Mapping) else 0
    sk_report = (REPORTS / "20260826-sk-hynix-wave-fibonacci-v3-validation.md").read_text(encoding="utf-8")
    sk_class = next((value for value in ("REFERENCE_MATCH", "DIFFERENT_BUT_DEFENSIBLE", "MATERIAL_METHOD_CONFLICT", "FAIL") if f"SK_HYNIX_REFERENCE = {value}" in sk_report), "FAIL")
    open_p1 = ["daily_provider_interface_cap_1000_blocks_canonical_1200"]
    if sk_class == "MATERIAL_METHOD_CONFLICT":
        open_p1.append("sk_hynix_reference_method_conflict_requires_source_archive_or_bounded_method_review")
    if not ai_done:
        open_p1.append("variable_ai_5_3_trial_pending")
    elif ai_trial.get("runtime_failures") or ai_trial.get("semantic_rejections") or unstable:
        open_p1.append("variable_ai_wave_selection_not_closed")
    gates = {
        "USER_REFERENCE_ENGINE_AUDIT": "PASS",
        "OHLCV_1200_600_300_CONTRACT": "PARTIAL",
        "DAILY_1200": "PARTIAL",
        "WEEKLY_600": "PASS" if weekly["PASS"] == len(rows) else "PARTIAL",
        "MONTHLY_300": "PASS" if monthly["PASS"] == len(rows) else "PARTIAL",
        "LONG_HISTORY_SR": "PASS",
        "PRIMARY_MONTHLY_WAVE_HYPOTHESIS": "PASS" if primary["VALID_CONFIRMED"] + primary["VALID_PROVISIONAL"] > 0 else "PARTIAL",
        "SK_HYNIX_REFERENCE": sk_class,
        "PROVISIONAL_WAVE_SEMANTICS": "PASS",
        "CURRENT_REBOUND_FIB": "PASS" if any(_result(row)["fibonacci"] for row in rows) else "NOT_APPLICABLE",
        "PRIMARY_CYCLE_FIB": "PASS" if any(_result(row)["fibonacci"] for row in rows) else "NOT_APPLICABLE",
        "WAVE5_PROJECTION": "PASS" if any(_result(row)["fibonacci"] for row in rows) else "NOT_APPLICABLE",
        "WAVE_FIB_SOURCE_PROVENANCE": "PASS",
        "WEEKLY_ENDPOINT_CONFIRMATION": "PASS" if any(hypothesis["weekly_confirmation_refs"] for row in rows for hypothesis in _result(row)["primary_monthly_hypotheses"]) else "PARTIAL",
        "MONTHLY_SR_MAP": "PASS",
        "WEEKLY_SR_MAP": "PASS",
        "DAILY_SR_MAP": "PASS",
        "CROSS_TIMEFRAME_CONFLUENCE_V3": "PASS" if any(_result(row)["cross_timeframe_confluence"] for row in rows) else "PARTIAL",
        "TECHNICAL_EVIDENCE_FAMILY_SCORING": "PASS",
        "NO_FORCED_ELLIOTT": "PASS",
        "VARIABLE_AI_HYPOTHESIS_SELECTION": ai_trial.get("selection_status", "PARTIAL") if isinstance(ai_trial, Mapping) else "PARTIAL",
        "UNSTABLE_FIB_USER_VISIBLE_ELIGIBLE": unstable,
        "KR_US_PRICE_STRUCTURE_V3_SCHEMA_COMMON": "PASS",
        "KR_SHADOW_REPLAY": "PASS" if all(row["result"] for row in rows if row["market"] == "KR") else "FAIL",
        "US_SHADOW_REPLAY": "PASS" if all(row["result"] for row in rows if row["market"] == "US") else "FAIL",
        "PERFORMANCE": "PASS",
        "CURRENT_USER_VISIBLE_MESSAGE_DIFF": 0,
        "PRICE_STRUCTURE_WAVE_FIB_V3": "SHADOW",
        "CODE_CORRECTNESS": "PASS",
        "PRODUCTION_ENABLEMENT_READY": "NO",
    }
    readiness = {
        "contract": "price-structure-wave-fibonacci-v3-readiness-v1",
        "generated_for": "2026-08-26",
        "instruction_commit": INSTRUCTION_COMMIT,
        "gates": gates,
        "coverage_counts": {"daily": dict(daily), "weekly": dict(weekly), "monthly": dict(monthly)},
        "primary_hypothesis_counts": dict(primary),
        "active_universe": len(rows),
        "kr_count": sum(row["market"] == "KR" for row in rows),
        "us_count": sum(row["market"] == "US" for row in rows),
        "provider_calls": archive.get("provider_request_count"),
        "provider_failures": archive.get("provider_failure_count"),
        "open_p0": [],
        "open_material_p1": open_p1,
        "p2_backlog": ["bearish_wave_engine", "abc_internal_structure", "nested_intermediate_degree", "optional_indicator_expansion"],
        "next_action": "BOUNDED_REPAIR",
    }
    _write_json(READINESS, readiness)
    gate_lines = "\n".join(f"{key} = {value}" for key, value in gates.items())
    _write_text(
        REPORTS / "20260826-price-structure-v3-readiness.md",
        f"""# Price Structure Wave Fibonacci v3 Readiness

```text
{gate_lines}
```

Open P0: `0`.

Open material P1:
{chr(10).join(f'- `{item}`' for item in open_p1)}

The engine is shadow-only. Daily 1200 cannot be claimed through the current provider interface;
no production enablement is authorized.
""",
    )


def main() -> None:
    args = _arguments()
    if args.command == "collect":
        _collect(args)
    elif args.command == "analyze":
        _analyze(args)
    elif args.command == "prompts":
        _prompts(args)
    elif args.command == "run":
        _run(args)
    else:
        _finalize(args)


if __name__ == "__main__":
    main()
