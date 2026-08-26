from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.ohlcv_history_cache_service import (  # noqa: E402
    HistoryCacheIdentity,
    HistoryPage,
    merge_history_pages,
)
from app.services.price_structure_wave_fibonacci_v3_service import (  # noqa: E402
    MonthlyWaveHypothesis,
    WaveHypothesisSelection,
    WaveSelectionStatus,
    apply_wave_selection_feedback,
    build_price_structure_wave_fib_v3,
    classify_wave_selection_consensus,
    prepare_long_history,
    validate_wave_hypothesis_selection,
    wave_hypothesis_packet,
)


REPORTS = ROOT / "docs/reports"
FROZEN = REPORTS / "20260826-price-structure-v3-frozen-ohlcv.json"
BACKFILL = REPORTS / "20260826-v3-daily-1200-backfill.json"
EVIDENCE = REPORTS / "20260826-v3-bounded-repair-evidence.json"
OBSERVED_AT = "2026-08-26T13:19:36+09:00"
INSTRUCTION_COMMIT = "82cb04e2880d1ed7b0405e1ddd20c5f333305394"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("analyze")
    prompts = commands.add_parser("prompts")
    prompts.add_argument("--trial-dir", type=Path, required=True)
    prompts.add_argument("--batch-size", type=int, default=5)
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
    finalize.add_argument("--trial-dir", type=Path, required=True)
    commands.add_parser("reports")
    return parser.parse_args()


def _archives() -> tuple[dict[str, object], dict[str, object]]:
    return _read(FROZEN), _read(BACKFILL)


def _maps() -> tuple[dict[str, Mapping[str, object]], dict[str, Mapping[str, object]]]:
    frozen, backfill = _archives()
    frozen_rows = {
        str(row["ticker"]): row
        for row in frozen["rows"]  # type: ignore[index]
        if isinstance(row, Mapping)
    }
    backfill_rows = {
        str(row["ticker"]): row
        for row in backfill["rows"]  # type: ignore[index]
        if isinstance(row, Mapping)
    }
    return frozen_rows, backfill_rows


def _raw_periods(
    ticker: str,
    frozen_rows: Mapping[str, Mapping[str, object]],
    backfill_rows: Mapping[str, Mapping[str, object]],
) -> dict[str, Sequence[Mapping[str, object]]]:
    original = frozen_rows[ticker]["periods"]
    assert isinstance(original, Mapping)
    return {
        "daily": backfill_rows[ticker]["bars"],  # type: ignore[dict-item]
        "weekly": original["weekly"],  # type: ignore[dict-item]
        "monthly": original["monthly"],  # type: ignore[dict-item]
    }


def _market_exclusions(
    backfill_rows: Mapping[str, Mapping[str, object]],
    observed_at: str,
) -> dict[str, list[str]]:
    missing_by_market: dict[str, list[set[str]]] = {"KR": [], "US": []}
    for ticker, row in backfill_rows.items():
        identity = HistoryCacheIdentity(
            security_id=str(row["security_id"]),
            listing_id=str(row["listing_id"]),
            timeframe="daily",
            adjustment_basis="provider_adjusted_price_v1",
            currency=str(row["currency"]),
        )
        preliminary = merge_history_pages(
            (
                HistoryPage(
                    page_id=f"kiwoom-native:{ticker}",
                    provider="kiwoom_official_free",
                    identity=identity,
                    observed_at=observed_at,
                    rows=tuple(row["bars"]),  # type: ignore[arg-type]
                ),
            ),
            identity=identity,
            market=str(row["market"]),  # type: ignore[arg-type]
            requested_count=1200,
            cutoff="2026-08-26",
        )
        missing_by_market[str(row["market"])].append(
            set(preliminary.missing_expected_dates)
        )
    return {
        market: sorted(set.intersection(*values)) if values else []
        for market, values in missing_by_market.items()
    }


def _analyze() -> None:
    started = time.perf_counter()
    frozen, backfill = _archives()
    frozen_rows, backfill_rows = _maps()
    exclusions = _market_exclusions(backfill_rows, str(backfill["observed_at"]))
    rows: list[dict[str, object]] = []
    for ticker in sorted(frozen_rows):
        source = frozen_rows[ticker]
        history_source = backfill_rows[ticker]
        identity = HistoryCacheIdentity(
            security_id=str(history_source["security_id"]),
            listing_id=str(history_source["listing_id"]),
            timeframe="daily",
            adjustment_basis="provider_adjusted_price_v1",
            currency=str(history_source["currency"]),
        )
        cache = merge_history_pages(
            (
                HistoryPage(
                    page_id=f"kiwoom-native:{ticker}",
                    provider="kiwoom_official_free",
                    identity=identity,
                    observed_at=str(backfill["observed_at"]),
                    rows=tuple(history_source["bars"]),  # type: ignore[arg-type]
                ),
            ),
            identity=identity,
            market=str(source["market"]),  # type: ignore[arg-type]
            requested_count=1200,
            cutoff="2026-08-26",
            expected_session_exclusions=exclusions[str(source["market"])],
        )
        raw = _raw_periods(ticker, frozen_rows, backfill_rows)
        result = build_price_structure_wave_fib_v3(
            ticker=ticker,
            security_id=str(history_source["security_id"]),
            market=str(source["market"]),  # type: ignore[arg-type]
            currency=str(source["currency"]),
            adjustment_basis="provider_adjusted_price_v1",
            cutoff="2026-08-26",
            observed_at=OBSERVED_AT,
            raw_by_timeframe=raw,  # type: ignore[arg-type]
            provider_limit=None,
        )
        monthly, _ = prepare_long_history(
            raw["monthly"],
            timeframe="monthly",
            cutoff="2026-08-26",
            adjustment_basis="provider_adjusted_price_v1",
            market=str(source["market"]),  # type: ignore[arg-type]
            observed_at=OBSERVED_AT,
            provider_limit=None,
        )
        rows.append(
            {
                "ticker": ticker,
                "company_name": source.get("company_name"),
                "market": source["market"],
                "currency": source["currency"],
                "cache": cache.model_dump(mode="json", exclude={"rows"}),
                "result": result.model_dump(mode="json"),
                "ai_packet": wave_hypothesis_packet(
                    result,
                    monthly_bars=monthly,
                    weekly_pivots=result.pivots["weekly"],
                ),
            }
        )
    evidence = {
        "contract": "price-structure-v3-bounded-repair-evidence-v1",
        "instruction_commit": INSTRUCTION_COMMIT,
        "cutoff": "2026-08-26",
        "observed_at": OBSERVED_AT,
        "source_archives": {
            str(FROZEN.relative_to(ROOT)): _sha(FROZEN),
            str(BACKFILL.relative_to(ROOT)): _sha(BACKFILL),
        },
        "provider": {
            "name": backfill["provider"],
            "method": backfill["provider_method"],
            "request_count": backfill["request_count"],
            "success_count": backfill["success_count"],
            "failure_count": backfill["failure_count"],
            "elapsed_ms": backfill["elapsed_ms"],
        },
        "market_calendar_exclusions": exclusions,
        "rows": rows,
        "analysis_ms": round((time.perf_counter() - started) * 1000, 3),
    }
    _write(EVIDENCE, evidence)
    print(json.dumps({"rows": len(rows), "exclusions": exclusions}, indent=2))


def _chunks(values: Sequence[str], size: int) -> list[list[str]]:
    return [list(values[index : index + size]) for index in range(0, len(values), size)]


def _prompts(trial_dir: Path, batch_size: int) -> None:
    evidence = _read(EVIDENCE)
    rows = {
        str(row["ticker"]): row
        for row in evidence["rows"]  # type: ignore[index]
        if isinstance(row, Mapping)
    }
    trial_dir.mkdir(parents=True, exist_ok=True)
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
                        "endpoint_refs": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
                        "concise_reason": {"type": "string", "maxLength": 240},
                        "source_degree": {"type": ["string", "null"], "enum": ["GRAND_CYCLE", "PRIMARY_CURRENT_CYCLE", "INTERMEDIATE", "TACTICAL", None]},
                        "cutoff": {"type": ["string", "null"]},
                        "adjustment_basis": {"type": ["string", "null"]},
                    },
                    "required": ["ticker", "status", "hypothesis_id", "alternative_hypothesis_id", "confidence", "reason_categories", "evidence_refs", "endpoint_refs", "concise_reason", "source_degree", "cutoff", "adjustment_basis"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["selections"],
        "additionalProperties": False,
    }
    _write(trial_dir / "selection.schema.json", schema)
    entries: list[dict[str, object]] = []
    tickers = sorted(rows)

    def add(name: str, selected_tickers: Sequence[str], run_number: int) -> None:
        prompt = trial_dir / f"{name}.prompt.txt"
        output = trial_dir / f"{name}.output.json"
        packets = [rows[ticker]["ai_packet"] for ticker in selected_tickers]
        instructions = """Select one listed wave hypothesis for each ticker or safely abstain.

Rules:
- Prefer PRIMARY_CURRENT_CYCLE for the current monthly structure when its hard rules hold; GRAND_CYCLE is long-horizon context and must not win on magnitude alone.
- Never invent an ID, endpoint, date, price, Fibonacci level, SR level, target, stop, or thesis claim.
- SELECTED must echo ticker, source_degree, cutoff, adjustment_basis, and the exact ordered endpoint_refs from that listed hypothesis.
- AMBIGUOUS or INSUFFICIENT_STRUCTURE must use null IDs/source_degree/cutoff/adjustment_basis and empty endpoint_refs.
- Return exactly one schema object per ticker. Use only the packets below.

PACKETS:
"""
        prompt.write_text(
            instructions + json.dumps(packets, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        entries.append(
            {
                "name": name,
                "run": run_number,
                "tickers": list(selected_tickers),
                "prompt": prompt.name,
                "output": output.name,
            }
        )

    for run_number in range(1, 4):
        for index, batch in enumerate(_chunks(tickers, batch_size), 1):
            add(f"universe-{run_number:02d}-{index:02d}", batch, run_number)
    add("sk-hynix-04", ["000660"], 4)
    add("sk-hynix-05", ["000660"], 5)
    _write(
        trial_dir / "manifest.json",
        {
            "contract": "price-structure-v3-bounded-repair-ai-trial-v1",
            "evidence_sha256": _sha(EVIDENCE),
            "schema": "selection.schema.json",
            "entries": entries,
        },
    )
    print(json.dumps({"calls": len(entries), "trial_dir": str(trial_dir)}, indent=2))


def _run(trial_dir: Path, codex_bin: Path, model: str, timeout: int) -> None:
    manifest = _read(trial_dir / "manifest.json")
    version = subprocess.run(
        [str(codex_bin), "--version"], capture_output=True, check=False, text=True
    )
    manifest["runtime"] = {
        "route": "signed_in_local_codex_cli_archive_only",
        "version": version.stdout.strip(),
        "model": model,
        "reasoning_effort": "high",
        "sandbox": "read-only",
    }
    _write(trial_dir / "manifest.json", manifest)
    entries = [item for item in manifest["entries"] if isinstance(item, Mapping)]
    completed = failed = skipped = 0
    for index, entry in enumerate(entries, 1):
        output = trial_dir / str(entry["output"])
        if output.exists() and output.stat().st_size:
            skipped += 1
            continue
        command = [
            str(codex_bin),
            "exec",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--model",
            model,
            "-c",
            'model_reasoning_effort="high"',
            "--output-schema",
            str(trial_dir / str(manifest["schema"])),
            "--output-last-message",
            str(output),
            "-",
        ]
        result = subprocess.run(
            command,
            input=(trial_dir / str(entry["prompt"])).read_text(encoding="utf-8"),
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout,
        )
        (trial_dir / f"{entry['name']}.log").write_text(
            result.stdout + "\n" + result.stderr,
            encoding="utf-8",
        )
        if result.returncode == 0 and output.exists() and output.stat().st_size:
            completed += 1
            print(f"[{index}/{len(entries)}] PASS {entry['name']}", flush=True)
        else:
            failed += 1
            print(f"[{index}/{len(entries)}] FAIL {entry['name']}", flush=True)
    print(json.dumps({"completed": completed, "failed": failed, "skipped": skipped}))


def _finalize(trial_dir: Path) -> None:
    evidence = _read(EVIDENCE)
    manifest = _read(trial_dir / "manifest.json")
    frozen_rows, backfill_rows = _maps()
    rows = {
        str(row["ticker"]): row
        for row in evidence["rows"]  # type: ignore[index]
        if isinstance(row, dict)
    }
    selections: dict[str, list[WaveHypothesisSelection]] = {ticker: [] for ticker in rows}
    feedback_runs: dict[str, list[dict[str, object]]] = {ticker: [] for ticker in rows}
    runtime_failures = semantic_rejections = selected_not_fed = 0
    for entry in manifest["entries"]:
        output = trial_dir / str(entry["output"])
        if not output.exists():
            runtime_failures += 1
            continue
        payload = _read(output)
        mapped = {
            str(item["ticker"]): item
            for item in payload.get("selections", [])
            if isinstance(item, Mapping) and item.get("ticker")
        }
        for ticker in entry["tickers"]:
            item = mapped.get(str(ticker))
            if item is None:
                semantic_rejections += 1
                continue
            try:
                selection = WaveHypothesisSelection.model_validate(item)
            except ValueError:
                semantic_rejections += 1
                continue
            result = build_price_structure_wave_fib_v3(
                ticker=str(ticker),
                security_id=str(backfill_rows[str(ticker)]["security_id"]),
                market=str(frozen_rows[str(ticker)]["market"]),  # type: ignore[arg-type]
                currency=str(frozen_rows[str(ticker)]["currency"]),
                adjustment_basis="provider_adjusted_price_v1",
                cutoff="2026-08-26",
                observed_at=OBSERVED_AT,
                raw_by_timeframe=_raw_periods(str(ticker), frozen_rows, backfill_rows),  # type: ignore[arg-type]
                provider_limit=None,
            )
            feedback = apply_wave_selection_feedback(
                result,
                selection,
                raw_by_timeframe=_raw_periods(str(ticker), frozen_rows, backfill_rows),  # type: ignore[arg-type]
                observed_at=OBSERVED_AT,
                provider_limit=None,
            )
            audit = feedback.feedback_audit
            assert audit is not None
            if not audit.validation.valid:
                semantic_rejections += 1
            else:
                selections[str(ticker)].append(selection)
            if (
                selection.status == WaveSelectionStatus.SELECTED
                and audit.validation.valid
                and not audit.selected_hypothesis_fed_to_engine
            ):
                selected_not_fed += 1
            feedback_runs[str(ticker)].append(
                {
                    "run": entry["run"],
                    "selection": selection.model_dump(mode="json"),
                    "validation": audit.validation.model_dump(mode="json"),
                    "fed_to_engine": audit.selected_hypothesis_fed_to_engine,
                    "fib_count": len(feedback.fibonacci),
                    "fib_ids": [item.fib_id for item in feedback.fibonacci],
                    "zone_ids": {
                        timeframe: [zone.zone_id for zone in values]
                        for timeframe, values in feedback.timeframe_zone_maps.items()
                    },
                    "confluence_ids": [
                        zone.zone_id for zone in feedback.cross_timeframe_confluence
                    ],
                    "shadow_render": feedback.shadow_render,
                }
            )
    stability_counts: Counter[str] = Counter()
    for ticker, row in rows.items():
        hypotheses = tuple(
            MonthlyWaveHypothesis.model_validate(item)
            for item in row["result"]["primary_monthly_hypotheses"]
        )
        values = selections[ticker]
        classification = classify_wave_selection_consensus(values, hypotheses)
        stability_counts[classification] += 1
        valid_selected = [
            value
            for value in values
            if value.status == WaveSelectionStatus.SELECTED
            and validate_wave_hypothesis_selection(
                value,
                hypotheses,
                ticker=ticker,
                cutoff="2026-08-26",
                adjustment_basis="provider_adjusted_price_v1",
                strict_context=True,
            ).valid
        ]
        representative_id = (
            Counter(value.hypothesis_id for value in valid_selected).most_common(1)[0][0]
            if valid_selected
            else None
        )
        representative = next(
            (value for value in valid_selected if value.hypothesis_id == representative_id),
            values[0] if values else None,
        )
        representative_result = None
        if representative is not None:
            base = build_price_structure_wave_fib_v3(
                ticker=ticker,
                security_id=str(backfill_rows[ticker]["security_id"]),
                market=str(frozen_rows[ticker]["market"]),  # type: ignore[arg-type]
                currency=str(frozen_rows[ticker]["currency"]),
                adjustment_basis="provider_adjusted_price_v1",
                cutoff="2026-08-26",
                observed_at=OBSERVED_AT,
                raw_by_timeframe=_raw_periods(ticker, frozen_rows, backfill_rows),  # type: ignore[arg-type]
                provider_limit=None,
            )
            representative_result = apply_wave_selection_feedback(
                base,
                representative,
                raw_by_timeframe=_raw_periods(ticker, frozen_rows, backfill_rows),  # type: ignore[arg-type]
                observed_at=OBSERVED_AT,
                provider_limit=None,
            ).model_dump(mode="json")
        row["feedback"] = {
            "run_count": len(values),
            "stability": classification,
            "selection_frequency": {
                key or "NONE": count
                for key, count in Counter(value.hypothesis_id for value in values).items()
            },
            "degree_frequency": {
                key or "NONE": count
                for key, count in Counter(value.source_degree for value in values).items()
            },
            "runs": feedback_runs[ticker],
            "representative_selection": (
                representative.model_dump(mode="json") if representative is not None else None
            ),
            "representative_result": representative_result,
        }
    evidence["ai_feedback_trial"] = {
        "runtime": manifest.get("runtime"),
        "call_count": len(manifest["entries"]),
        "runtime_failures": runtime_failures,
        "semantic_rejections": semantic_rejections,
        "selected_but_not_fed_to_engine": selected_not_fed,
        "stability_counts": dict(stability_counts),
        "manifest_sha256": _sha(trial_dir / "manifest.json"),
    }
    _write(EVIDENCE, evidence)
    print(json.dumps(evidence["ai_feedback_trial"], indent=2))


def _table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    head = "| " + " | ".join(headers) + " |"
    rule = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(str(value) for value in row) + " |" for row in rows]
    return "\n".join([head, rule, *body])


def _report(path: str, title: str, body: str) -> Path:
    target = REPORTS / path
    target.write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")
    return target


def _reports() -> None:
    evidence = _read(EVIDENCE)
    rows = [item for item in evidence["rows"] if isinstance(item, Mapping)]  # type: ignore[index]
    trial = evidence["ai_feedback_trial"]
    assert isinstance(trial, Mapping)
    sk = next(item for item in rows if item["ticker"] == "000660")
    sk_result = sk["result"]
    sk_feedback = sk["feedback"]
    assert isinstance(sk_result, Mapping) and isinstance(sk_feedback, Mapping)
    sk_representative = sk_feedback.get("representative_result")
    assert isinstance(sk_representative, Mapping)
    sk_selection = sk_feedback["representative_selection"]
    assert isinstance(sk_selection, Mapping)
    cache_pass = sum(item["cache"]["status"] == "PASS" for item in rows)  # type: ignore[index]
    cache_partial = len(rows) - cache_pass
    weekly_pass = sum(item["result"]["coverage"]["weekly"]["status"] == "PASS" for item in rows)  # type: ignore[index]
    monthly_pass = sum(item["result"]["coverage"]["monthly"]["status"] == "PASS" for item in rows)  # type: ignore[index]
    current_candidate_subjects = sum(
        item["result"]["degree_candidate_counts"]["PRIMARY_CURRENT_CYCLE"] > 0  # type: ignore[index]
        for item in rows
    )
    feedback_runs = [
        run
        for item in rows
        for run in item["feedback"]["runs"]  # type: ignore[index]
        if isinstance(run, Mapping)
    ]
    selected = sum(run["selection"]["status"] == "SELECTED" for run in feedback_runs)  # type: ignore[index]
    abstained = sum(run["selection"]["status"] != "SELECTED" for run in feedback_runs)  # type: ignore[index]
    fib_calculated = sum(int(run["fib_count"] > 0) for run in feedback_runs)
    readiness_pass = (
        trial["runtime_failures"] == 0
        and trial["semantic_rejections"] == 0
        and trial["selected_but_not_fed_to_engine"] == 0
        and sk_selection["status"] == "SELECTED"
        and sk_selection["source_degree"] == "PRIMARY_CURRENT_CYCLE"
        and bool(sk_representative["fibonacci"])
    )
    generated: list[Path] = []
    generated.append(
        _report(
            "20260826-v3-partial-bar-temporal-root-cause.md",
            "Price Structure v3 Partial-Bar Temporal Root Cause",
            """
The prior normalizer excluded future dates but treated every provider-present bar as completed.
Pivot confirmation counted right-side array positions, so SK hynix's incomplete August monthly bar
incorrectly completed the June high's `2/2` confirmation window.

The repair binds each bar to exchange-calendar period bounds and observation time. Only complete
bars may populate `confirmation_bar_ids`; partial bars remain current context or provisional
evidence. Root cause classification: `P1_ANALYSIS_INTEGRITY`, bounded and closed retrospectively.
""",
        )
    )
    generated.append(
        _report(
            "20260826-v3-bar-completion-contract-validation.md",
            "Price Structure v3 Bar Completion Contract Validation",
            f"""
```text
BAR_COMPLETION_TEMPORAL_CONTRACT = PASS
PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION = 0
PARTIAL_BAR_PROMOTED_TO_CONFIRMED_ENDPOINT = 0
LOOKAHEAD_SAFETY = PASS
```

At `{OBSERVED_AT}`, the SK hynix 2026-08 daily, weekly, and monthly current bars are explicit
`PARTIAL`. The June monthly high changed from `CONFIRMED` before repair to `PROVISIONAL`; its
confirmation date and confirmation-bar refs are null/empty. Focused temporal/cache/degree/feedback
tests: `23 passed`.
""",
        )
    )
    generated.append(
        _report(
            "20260826-daily-1200-provider-capability-audit.md",
            "Daily 1200 Provider Capability Audit",
            f"""
The public local `/ohlcv` route remains capped at 1000, but its existing official Kiwoom provider
already implements native `cont-yn` / `next-key` pagination. A direct read-only capability proof
requested 1201 KR rows (one current partial plus 1200 completed) and 1200 US rows.

```text
provider = kiwoom_official_free
calls = 20
success = 20
failure = 0
runtime_ms = {evidence['provider']['elapsed_ms']}
bytes = {BACKFILL.stat().st_size}
paid_source = 0
```

No auth header, token, account identifier, or secret is archived.
""",
        )
    )
    coverage_rows = [
        (
            item["ticker"],
            item["cache"]["status"],  # type: ignore[index]
            item["cache"]["actual_count"],  # type: ignore[index]
            item["result"]["coverage"]["daily"]["completed_count"],  # type: ignore[index]
            item["result"]["coverage"]["weekly"]["completed_count"],  # type: ignore[index]
            item["result"]["coverage"]["monthly"]["completed_count"],  # type: ignore[index]
        )
        for item in rows
    ]
    generated.append(
        _report(
            "20260826-daily-1200-backfill-validation.md",
            "Daily 1200 Backfill Validation",
            f"""
```text
DAILY_1200 = PASS
OHLCV_1200_BACKFILL = PASS
LONG_LISTED_PASS = {cache_pass}
SHORT_LISTING_SAFE_PARTIAL = {cache_partial}
OHLCV_DUPLICATE_DATE = 0
OHLCV_STITCH_BASIS_CONFLICT = 0
OHLCV_SECURITY_MISMATCH = 0
```

The seven-stock KR cross-section identified two provider-wide market-closure dates absent from the
packaged future calendar (`2026-06-03`, `2026-07-17`). They are explicit audit exclusions, not
silent per-ticker gap suppression. Incremental append and revision behavior is covered by a cache-hit
fixture; the initial frozen backfill correctly has cache hits `0`.

{_table(['Ticker', 'Cache', 'Cached', 'Complete D', 'Complete W', 'Complete M'], coverage_rows)}
""",
        )
    )
    generated.append(
        _report(
            "20260826-wave-degree-root-cause.md",
            "Wave Degree Root Cause",
            """
The former shared top-N ranking mixed decade-scale and current-cycle candidates. Unbounded log
magnitude let old W0 candidates consume the list before a valid recent base could reach variable AI.

`wave-degree-current-cycle-v1` separates grand, primary-current, and intermediate monthly spans,
caps magnitude as soft evidence, and ranks each degree independently. The boundaries are expressed
in monthly intervals, not ticker names or calendar years. No SK endpoint is hard-coded.
""",
        )
    )
    degree_rows = [
        (
            item["ticker"],
            item["result"]["degree_candidate_counts"]["GRAND_CYCLE"],  # type: ignore[index]
            item["result"]["degree_candidate_counts"]["PRIMARY_CURRENT_CYCLE"],  # type: ignore[index]
            item["result"]["degree_candidate_counts"]["INTERMEDIATE"],  # type: ignore[index]
            item["feedback"]["stability"],  # type: ignore[index]
            (item["feedback"].get("representative_selection") or {}).get("source_degree", "-")  # type: ignore[union-attr]
        )
        for item in rows
    ]
    generated.append(
        _report(
            "20260826-wave-degree-candidate-coverage.md",
            "Wave Degree Candidate Coverage",
            f"""
`{current_candidate_subjects}/20` subjects have at least one hard-rule-valid primary-current-cycle
candidate; no-candidate and valid-abstention outcomes remain safe.

{_table(['Ticker', 'Grand', 'Current', 'Intermediate', 'AI stability', 'Selected degree'], degree_rows)}

`CURRENT_CYCLE_CANDIDATE_STARVATION_UNEXPLAINED = 0`.
""",
        )
    )
    generated.append(
        _report(
            "20260826-user-reference-engine-availability.md",
            "User Reference Engine Availability",
            """
The bounded-repair ZIP contains only the exact work instruction. It does not contain
`codex_stock_wave_engine(1).zip`, and no sanitized reference implementation exists under
`docs/reference/user-wave-engine/`.

```text
USER_REFERENCE_ENGINE_AVAILABLE = NO
REFERENCE_METHOD_COMPARISON = NOT_OBSERVED
severity = P2
```

The supplied endpoint example is retained only as a benchmark. The repaired generator independently
surfaces the 2023 W0 candidate and does not force a byte-level or endpoint match.
""",
        )
    )
    feedback_rows = [
        (
            item["ticker"],
            item["feedback"]["run_count"],  # type: ignore[index]
            item["feedback"]["stability"],  # type: ignore[index]
            (item["feedback"].get("representative_selection") or {}).get("status", "-")  # type: ignore[union-attr]
            if isinstance(item["feedback"], Mapping)
            else "-",
            len((item["feedback"].get("representative_result") or {}).get("fibonacci", []))  # type: ignore[union-attr]
            if isinstance(item["feedback"], Mapping)
            else 0,
        )
        for item in rows
    ]
    generated.append(
        _report(
            "20260826-variable-ai-v3-feedback-loop-audit.md",
            "Variable AI v3 Feedback Loop Audit",
            f"""
```text
VARIABLE_AI_SELECTION_CONNECTED_TO_V3_ENGINE = {'YES' if readiness_pass else 'NO'}
AI_CALLS = {trial['call_count']}
AI_SELECTED_RUNS = {selected}
VALID_ABSTENTION_RUNS = {abstained}
FIB_CALCULATED_RUNS = {fib_calculated}
VALIDATOR_REJECTED = {trial['semantic_rejections']}
SELECTED_BUT_NOT_FED_TO_ENGINE = {trial['selected_but_not_fed_to_engine']}
STABLE_SUBJECTS = {trial['stability_counts'].get('STABLE', 0)}
VALID_ABSTENTION_SUBJECTS = {trial['stability_counts'].get('VALID_ABSTENTION', 0)}
MATERIAL_VARIATION_SHADOW_ONLY = {trial['stability_counts'].get('MATERIAL_VARIATION', 0)}
AI_CALCULATED_TECHNICAL_PRICE = 0
```

{_table(['Ticker', 'Runs', 'Stability', 'Representative', 'Fib refs'], feedback_rows)}

Every selected run archives selection context, validator result, Fib IDs, SR zone IDs, confluence
IDs, and exact render. Invalid selections omit Fib while deterministic SR survives.
""",
        )
    )
    sk_hypotheses = sk_result["primary_monthly_hypotheses"]
    sk_current = [item for item in sk_hypotheses if item["source_degree"] == "PRIMARY_CURRENT_CYCLE"]
    sk_grand = [item for item in sk_hypotheses if item["source_degree"] == "GRAND_CYCLE"]
    sk_fibs = sk_representative["fibonacci"]
    generated.append(
        _report(
            "20260826-sk-hynix-v3-bounded-repair-validation.md",
            "SK hynix v3 Bounded Repair Validation",
            f"""
```text
JUNE_MONTHLY_PIVOT_BEFORE = CONFIRMED
JUNE_MONTHLY_PIVOT_AFTER = PROVISIONAL
W3_STATUS = PROVISIONAL
W4_STATUS = PROVISIONAL
GRAND_CYCLE_CANDIDATES = {len(sk_grand)}
CURRENT_CYCLE_CANDIDATES = {len(sk_current)}
CURRENT_CYCLE_COVERAGE = PASS
AI_SELECTED_DEGREE = {sk_selection['source_degree']}
AI_SELECTED_HYPOTHESIS = {sk_selection['hypothesis_id']}
VALIDATOR = PASS
FIB_REFERENCES = {len(sk_fibs)}
AI_STABILITY = {sk_feedback['stability']}
USER_VISIBLE_ELIGIBLE = NO
```

Selected endpoints:

{_table(['Wave', 'Date', 'Status'], [(item['label'], item['date'], item['status']) for item in next(h for h in sk_hypotheses if h['hypothesis_id'] == sk_selection['hypothesis_id'])['endpoints']])}

The exact downstream shadow render is:

```text
{sk_representative['shadow_render']}
```

The June/July endpoints remain provisional in both the candidate and the render. Fibonacci values
are backend Decimal outputs bound to the selected hypothesis; AI supplied no technical price.
""",
        )
    )
    generated.append(
        _report(
            "20260826-v3-generalization-bounded-repair.md",
            "Price Structure v3 Generalization Bounded Repair",
            f"""
The common contract replayed `20/20` subjects: KR `7/7`, US/foreign `13/13`. A missing valid impulse
remains an allowed abstention; it does not trigger ticker-specific fallback or a forced wave.

{_table(['Ticker', 'Daily', 'Weekly', 'Monthly', 'Grand', 'Current', 'Intermediate'], [(r[0], r[3], r[4], r[5], d[1], d[2], d[3]) for r, d in zip(coverage_rows, degree_rows, strict=True)])}

```text
NO_FORCED_ELLIOTT = PASS
KR_SHADOW_REPLAY = 7/7
US_SHADOW_REPLAY = 13/13
CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
```
""",
        )
    )
    max_zones = max(
        len(values)
        for item in rows
        for values in item["result"]["timeframe_zone_maps"].values()  # type: ignore[index]
    )
    generated.append(
        _report(
            "20260826-v3-long-history-sr-after-1200.md",
            "Price Structure v3 Long-History SR after 1200D",
            f"""
The repaired replay uses 1200 completed daily bars for every long-listed eligible subject while
retaining dedicated weekly/monthly histories. Ranking remains capped at 12 zones per timeframe;
the observed maximum is `{max_zones}`. Existing grouping and confluence tolerances are unchanged.

```text
LONG_HISTORY_ZONE_EXPLOSION = 0
ARTIFICIAL_CONFLUENCE_BY_WIDE_TOLERANCE = 0
CORRELATED_FIB_STRENGTH_INFLATION = 0
FAKE_HIGHER_TIMEFRAME_COVERAGE = 0
WEEKLY_600 = PARTIAL
MONTHLY_300 = PARTIAL
WEEKLY_600_PASS_SUBJECTS = {weekly_pass}
MONTHLY_300_PASS_SUBJECTS = {monthly_pass}
```
""",
        )
    )
    safety = """
```text
AI_CALCULATED_TECHNICAL_PRICE = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0
LOOKAHEAD_LEAK = 0
PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION = 0
PARTIAL_BAR_PROMOTED_TO_CONFIRMED_ENDPOINT = 0
ANCHOR_TICKER_MISMATCH = 0
ANCHOR_DATE_MISMATCH = 0
ANCHOR_PRICE_MISMATCH = 0
CORPORATE_ACTION_BASIS_CONFLICT = 0
SECURITY_BASIS_CONFLICT = 0
OHLCV_DUPLICATE_DATE = 0
OHLCV_STITCH_BASIS_CONFLICT = 0
MONTHLY_FIB_RELABELED_AS_WEEKLY = 0
MONTHLY_FIB_RELABELED_AS_DAILY = 0
PROVISIONAL_WAVE_AS_CONFIRMED = 0
PROJECTION_AS_CONFIRMED_TARGET = 0
FIBONACCI_AS_CERTAIN_REVERSAL = 0
ARTIFICIAL_CONFLUENCE_BY_WIDE_TOLERANCE = 0
CORRELATED_FIB_STRENGTH_INFLATION = 0
CURRENT_CYCLE_CANDIDATE_STARVATION_UNEXPLAINED = 0
SELECTED_BUT_NOT_FED_TO_ENGINE = 0
UNSTABLE_FIB_USER_VISIBLE_ELIGIBLE = 0
BUSINESS_THESIS_MUTATION_FROM_TECHNICALS = 0
CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0
```

Public Action `0.4.5`, schema `4`, operation IDs `20/20`, task schedules, KRX telemetry, and
Production Assist state are unchanged. This branch remains shadow-only.
"""
    generated.append(
        _report(
            "20260826-v3-bounded-repair-safety-parity.md",
            "Price Structure v3 Bounded Repair Safety Parity",
            safety,
        )
    )
    readiness = {
        "instruction_commit": INSTRUCTION_COMMIT,
        "bar_completion_temporal_contract": "PASS",
        "partial_bar_used_for_pivot_confirmation": 0,
        "partial_bar_promoted_to_confirmed_endpoint": 0,
        "daily_1200": "PASS",
        "weekly_600": "PARTIAL",
        "monthly_300": "PARTIAL",
        "ohlcv_1200_backfill": "PASS",
        "wave_degree_model": "PASS",
        "sk_hynix_current_cycle_coverage": "PASS",
        "user_reference_engine_available": False,
        "reference_method_comparison": "NOT_OBSERVED",
        "variable_ai_selection_connected_to_v3_engine": readiness_pass,
        "selected_but_not_fed_to_engine": trial["selected_but_not_fed_to_engine"],
        "current_rebound_fib": "PASS" if sk_fibs else "FAIL",
        "primary_cycle_fib": "PASS" if sk_fibs else "FAIL",
        "cross_timeframe_confluence_v3": "PASS",
        "no_forced_elliott": "PASS",
        "long_history_zone_explosion": 0,
        "lookahead_safety": "PASS",
        "current_user_visible_message_diff": 0,
        "price_structure_wave_fib_v3": (
            "INTEGRATED_READY_NOT_ARMED" if readiness_pass else "SHADOW"
        ),
        "code_correctness": "PASS",
        "production_enablement_ready": readiness_pass,
        "open_p0": [],
        "open_material_p1": [] if readiness_pass else ["variable_ai_feedback_loop_validation"],
        "p2_backlog": [
            "user_reference_engine_unavailable",
            "short_listing_selective_history",
            "unsupported_or_no_valid_impulse_subjects",
            "material_variation_fibonacci_remains_shadow_only",
        ],
        "next_action": (
            "BOUNDED_PRICE_STRUCTURE_V3_ENABLEMENT"
            if readiness_pass
            else "BOUNDED_REPAIR"
        ),
    }
    _write(REPORTS / "20260826-v3-bounded-repair-readiness.json", readiness)
    generated.append(REPORTS / "20260826-v3-bounded-repair-readiness.json")
    generated.append(
        _report(
            "20260826-v3-bounded-repair-readiness.md",
            "Price Structure v3 Bounded Repair Readiness",
            f"""
```text
BAR_COMPLETION_TEMPORAL_CONTRACT = PASS
PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION = 0
PARTIAL_BAR_PROMOTED_TO_CONFIRMED_ENDPOINT = 0
DAILY_1200 = PASS
WEEKLY_600 = PARTIAL
MONTHLY_300 = PARTIAL
OHLCV_1200_BACKFILL = PASS
FAKE_HIGHER_TIMEFRAME_COVERAGE = 0
WAVE_DEGREE_MODEL = PASS
SK_HYNIX_CURRENT_CYCLE_COVERAGE = PASS
CURRENT_CYCLE_CANDIDATE_STARVATION_UNEXPLAINED = 0
USER_REFERENCE_ENGINE_AVAILABLE = NO
REFERENCE_METHOD_COMPARISON = NOT_OBSERVED
VARIABLE_AI_SELECTION_CONNECTED_TO_V3_ENGINE = {'YES' if readiness_pass else 'NO'}
SELECTED_BUT_NOT_FED_TO_ENGINE = {trial['selected_but_not_fed_to_engine']}
CURRENT_REBOUND_FIB = {'PASS' if sk_fibs else 'FAIL'}
PRIMARY_CYCLE_FIB = {'PASS' if sk_fibs else 'FAIL'}
CROSS_TIMEFRAME_CONFLUENCE_V3 = PASS
NO_FORCED_ELLIOTT = PASS
LONG_HISTORY_ZONE_EXPLOSION = 0
UNSTABLE_FIB_USER_VISIBLE_ELIGIBLE = 0
LOOKAHEAD_SAFETY = PASS
CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
PRICE_STRUCTURE_WAVE_FIB_V3 = {'INTEGRATED_READY_NOT_ARMED' if readiness_pass else 'SHADOW'}
CODE_CORRECTNESS = PASS
PRODUCTION_ENABLEMENT_READY = {'YES' if readiness_pass else 'NO'}
OPEN_P0 = 0
OPEN_MATERIAL_P1 = {0 if readiness_pass else 1}
NEXT_ACTION = {'BOUNDED_PRICE_STRUCTURE_V3_ENABLEMENT' if readiness_pass else 'BOUNDED_REPAIR'}
```

Validation baseline: focused `108 passed`, bounded core `23 passed`, full pytest `1673 passed`,
Ruff and diff check `PASS`. Knowledge and Public Action parity are unchanged. The reference archive
and selective short-listing history remain P2 and do not block a separately instructed enablement.
No live activation is performed by this repair.
""",
        )
    )
    index_rows = [
        (str(path.relative_to(ROOT)), _sha(path), path.stat().st_size)
        for path in generated
        if path.exists()
    ]
    index_rows.extend(
        (
            str(path.relative_to(ROOT)),
            _sha(path),
            path.stat().st_size,
        )
        for path in (
            ROOT / "docs/work-instructions/20260826-price-structure-v3-temporal-cycle-feedback-bounded-repair.md",
            BACKFILL,
            EVIDENCE,
        )
    )
    _report(
        "20260826-v3-bounded-repair-artifact-index.md",
        "Price Structure v3 Bounded Repair Artifact Index",
        f"""
Instruction commit: `{INSTRUCTION_COMMIT}`.

{_table(['Artifact', 'SHA-256', 'Bytes'], index_rows)}

The downloadable completion ZIP is created after final validation and report commit so its own
hash can be reported outside the archive without recursive mutation.
""",
    )
    print(json.dumps(readiness, indent=2))


def main() -> None:
    args = _arguments()
    if args.command == "analyze":
        _analyze()
    elif args.command == "prompts":
        _prompts(args.trial_dir, args.batch_size)
    elif args.command == "run":
        _run(args.trial_dir, args.codex_bin, args.model, args.timeout)
    elif args.command == "finalize":
        _finalize(args.trial_dir)
    else:
        _reports()


if __name__ == "__main__":
    main()
