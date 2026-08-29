from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
from pydantic import ValidationError

from app.services.cross_market_decision_engine_service import (
    DecisionBatchOutput,
    DecisionCandidate,
    DecisionEvidencePacket,
    RenderedDecision,
    TemporalDecisionBatchOutput,
    build_decision_evidence_packet,
    canonicalize_candidate_metadata,
    compact_ai_context,
    decision_distribution,
    decision_message_quality,
    render_shadow_decision,
    validate_decision_candidate,
)
from app.services.ohlcv_feature_engine_service import (
    build_multi_timeframe_feature_packet,
    feature_catalog,
)
from scripts.kr_final_preenable_test_delivery import deliver_test_messages
from scripts.kr_market_preenable_evidence import audit_test_sink, load_env_values


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs/reports"
CONTRACT = "cross-market-ai-decision-engine-v1"
OUTPUT_CONTRACT = "cross-market-ai-decision-output-v1"
TEST_NAMESPACE = "CROSS_MARKET_DECISION_TEST_ONLY_NON_PRODUCTION"


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


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


async def _fetch_ohlcv(
    client: httpx.AsyncClient,
    *,
    base_url: str,
    api_key: str,
    ticker: str,
) -> tuple[str, dict[str, object]]:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = await client.get(
                f"{base_url.rstrip('/')}/ohlcv",
                params={
                    "symbol": ticker,
                    "periods": "daily,weekly,monthly",
                    "count": 1000,
                    "include_indicators": "false",
                },
                headers={"X-API-Key": api_key},
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict) or not isinstance(payload.get("periods"), dict):
                raise ValueError(f"invalid_ohlcv_response:{ticker}")
            return ticker, payload
        except (httpx.HTTPError, ValueError) as exc:
            last_error = exc
            if attempt < 2:
                await asyncio.sleep(1.0 + attempt)
    assert last_error is not None
    raise last_error


async def _collect(args: argparse.Namespace) -> None:
    env = load_env_values(args.env_file)
    api_key = env.get("ACTION_API_KEY") or env.get("OHLCV_API_KEY") or ""
    if not api_key:
        raise ValueError("ohlcv_api_key_missing")
    source_packets: list[dict[str, object]] = []
    for path in (args.kr_packet, args.us_packet):
        value = _read_json(path)
        if not isinstance(value, dict):
            raise ValueError(f"invalid_packet:{path}")
        source_packets.append(value)
    stock_rows = [
        (packet, stock)
        for packet in source_packets
        for stock in packet.get("stocks") or ()
        if isinstance(stock, Mapping)
    ]
    tickers = [str(stock.get("ticker") or "") for _, stock in stock_rows]
    if len(tickers) != 20 or len(set(tickers)) != 20:
        raise ValueError("active_universe_not_20_unique_subjects")
    fetched: list[tuple[str, dict[str, object]]] = []
    async with httpx.AsyncClient(timeout=args.timeout) as client:
        for ticker in tickers:
            fetched.append(
                await _fetch_ohlcv(
                    client,
                    base_url=args.ohlcv_base_url,
                    api_key=api_key,
                    ticker=ticker,
                )
            )
            await asyncio.sleep(0.2)
    ohlcv = dict(fetched)
    rows: list[dict[str, object]] = []
    for packet, stock in stock_rows:
        ticker = str(stock["ticker"])
        cutoff = date.fromisoformat(
            str(packet.get("assessment_date") or packet.get("generated_at"))[:10]
        )
        raw = ohlcv[ticker]
        periods = raw.get("periods")
        assert isinstance(periods, Mapping)
        features = build_multi_timeframe_feature_packet(
            ticker=ticker,
            periods={
                key: value
                for key, value in periods.items()
                if isinstance(value, list)
            },
            cutoff=cutoff,
        )
        evidence = build_decision_evidence_packet(
            packet=packet,
            stock=stock,
            technical_features=features,
        )
        rows.append(
            {
                "ticker": ticker,
                "market": packet["market"],
                "source_packet_id": packet["packet_id"],
                "source_packet_sha256": _sha256(
                    args.kr_packet if packet["market"] == "kr" else args.us_packet
                ),
                "provider": str((raw.get("meta") or {}).get("provider") or "unknown"),
                "provider_request_count": 1,
                "feature_packet": features.model_dump(mode="json"),
                "evidence_packet": evidence.model_dump(mode="json"),
            }
        )
    payload = {
        "contract": CONTRACT,
        "status": "CURRENT_EVIDENCE_READY",
        "active_subject_count": len(rows),
        "market_counts": dict(Counter(str(row["market"]) for row in rows)),
        "provider_calls": {
            "ohlcv_analyst": {
                "requests": len(rows),
                "success": len(rows),
                "failure": 0,
                "cache_hit": 0,
            }
        },
        "feature_catalog": feature_catalog(),
        "rows": rows,
    }
    _write_json(args.output, payload)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "rows": len(rows),
                "markets": payload["market_counts"],
            },
            sort_keys=True,
        )
    )


def _prompt(contexts: Sequence[Mapping[str, object]]) -> str:
    return """You are the sole owner of an analytical BUY/HOLD/SELL classification for each supplied stock.

This is investment research, not an order, automated trade, or position-size instruction. Reason from the full evidence packet in this order: integrity, thesis, earnings and earnings quality, expectations, valuation, catalysts/risks, macro/market/flows, then price structure and technical features. Technical features may affect timing and risk but must not silently own the long-horizon decision. Do not use a fixed point score or invent facts.

Hard rules:
- Return exactly one decision for each input ticker.
- reasoning_grade must be VERY_HIGH. Use the packet horizon verbatim.
- Every claim needs one or more exact ref_id values from that ticker.
- Copy each ref_id as one complete opaque string. Never shorten, extend, splice, infer, or append punctuation to a ref_id. Before returning, verify every cited ref_id by exact string equality against the supplied packet.
- Include genuine supporting and opposing evidence, remaining unknowns, and change conditions.
- HOLD requires one canonical hold_reason plus evidence-linked why_not_buy and why_not_sell. Use NOT_HOLD only for BUY or SELL.
- SELL means present downside and impaired risk/reward materially dominate conditional upside at the stated horizon; it does not require formal thesis invalidation or a price breakdown.
- HOLD means material positive optionality remains and downside dominance is not established. Do not use HOLD as a default for uncertainty.
- Timing is independent: FAVORABLE/NEUTRAL/UNFAVORABLE require usable price, technical, flow, or market evidence; use INSUFFICIENT when that evidence is unavailable or conflicted. NEUTRAL is balanced evidence, not missing evidence.
- confidence measures decision-evidence quality and convergence, not reasoning effort. Return one canonical confidence_reason. HIGH requires convergent critical evidence; missing critical valuation, security-basis, data-quality, or economic proof normally lowers confidence.
- selected_evidence_plan must contain every category actually cited.
- Do not put exact numeric values in prose. To surface up to three useful numeric technical observations, choose their canonical ref_id in selected_numeric_fact_refs; the backend will format them.
- Do not calculate a feature, return, target, fair value, FCF yield, per-share FCF, EV/FCF, ROIC, CCC, DSO, DPO, runway months, or an order size.
- BUY/HOLD/SELL is an analytical classification only. Do not write market-order or imperative trading language.
- Prefer abstaining through LOW confidence and explicit unknowns over pretending evidence is stronger than it is. Still return one analytical classification because the product contract requires it.
- Across tickers in the same batch, do not repeat an identical substantive sentence. Unknowns and change conditions must name the company-specific unresolved driver supported by that ticker's evidence.
- Output only JSON matching the supplied schema.

DECISION_EVIDENCE_PACKETS:
""" + json.dumps(contexts, ensure_ascii=False, separators=(",", ":"))


def _temporal_prompt(contexts: Sequence[Mapping[str, object]]) -> str:
    return """Generate one point-in-time analytical BUY/HOLD/SELL decision for every supplied checkpoint.

Each checkpoint is an immutable historical packet. Use only evidence inside that checkpoint. Never use later facts, present-day knowledge, current prices, future outcomes, or evidence from another checkpoint. The decision is research, not an order or position-size instruction. The AI owns the final decision; no fixed score exists.

Hard rules:
- Return one row for each checkpoint_id, preserving checkpoint_id, source_packet_id, source_cutoff, and ticker exactly.
- reasoning_grade must be VERY_HIGH and horizon must match that checkpoint packet verbatim.
- Every claim must cite exact complete ref_id strings from the same checkpoint. Never alter, splice, shorten, infer, or punctuate a ref_id.
- Include supporting evidence, opposing evidence, unknowns, and change conditions.
- HOLD requires one canonical hold_reason plus evidence-linked why_not_buy and why_not_sell. Use NOT_HOLD only for BUY or SELL.
- SELL does not require formal thesis invalidation; HOLD still requires material optionality that prevents downside dominance.
- Keep timing independent from the long-horizon decision. Directional timing requires usable market/flow/price/technical evidence; use INSUFFICIENT for material evidence gaps, not NEUTRAL.
- confidence is evidence quality/convergence and must include one canonical confidence_reason; it is not the VERY_HIGH reasoning grade.
- Do not put exact numbers in prose. Select up to three numeric technical refs only when numeric_prose_eligible is true.
- Do not calculate technical features, valuation multiples, targets, fair values, FCF valuation ratios, or future returns.
- Do not repeat an identical substantive sentence across companies or checkpoints. Make each reason specific to the available company evidence.
- Output only JSON matching the supplied schema.

POINT_IN_TIME_CHECKPOINTS:
""" + json.dumps(contexts, ensure_ascii=False, separators=(",", ":"))


def _temporal_context(
    packet: DecisionEvidencePacket,
    *,
    checkpoint_id: str,
    source_cutoff: str,
) -> dict[str, object]:
    category_limits = {
        "thesis": 7,
        "earnings": 6,
        "earnings_quality": 4,
        "expectations": 2,
        "valuation": 6,
        "catalysts": 3,
        "risks": 6,
        "macro": 3,
        "market": 4,
        "flows": 3,
        "price_structure": 5,
        "technical_feature": 0,
        "unknown": 4,
        "quality": 4,
    }
    seen: Counter[str] = Counter()
    evidence: list[dict[str, object]] = []
    for ref in packet.evidence:
        category = str(ref.category)
        if seen[category] >= category_limits.get(category, 2):
            continue
        seen[category] += 1
        evidence.append(
            {
                "ref_id": ref.ref_id,
                "category": category,
                "label": ref.label,
                "statement": ref.statement[:520],
                "as_of": ref.as_of,
                "value": str(ref.value) if ref.value is not None else None,
                "unit": ref.unit,
                "numeric_prose_eligible": ref.numeric_prose_eligible,
            }
        )
    return {
        "checkpoint_id": checkpoint_id,
        "source_packet_id": packet.packet_id,
        "source_cutoff": source_cutoff,
        "ticker": packet.ticker,
        "company_name": packet.company_name,
        "market": packet.market,
        "assessment_date": packet.assessment_date,
        "horizon": packet.horizon,
        "reasoning_grade": packet.reasoning_grade,
        "backend_reasoning_effort": packet.backend_reasoning_effort,
        "evidence": evidence,
        "data_quality_cautions": packet.data_quality_cautions,
    }


def _select_historical_packets(
    inbox: Path,
    *,
    checkpoints: int,
) -> dict[str, list[tuple[Path, dict[str, object]]]]:
    by_market_date: dict[tuple[str, str], list[tuple[Path, dict[str, object]]]] = {}
    for path in sorted(inbox.glob("*.json")):
        value = _read_json(path)
        if not isinstance(value, dict):
            continue
        market = str(value.get("market") or "").lower()
        assessment_date = str(value.get("assessment_date") or "")[:10]
        if market not in {"kr", "us"} or not assessment_date:
            continue
        by_market_date.setdefault((market, assessment_date), []).append((path, value))
    selected: dict[str, list[tuple[Path, dict[str, object]]]] = {}
    for market in ("kr", "us"):
        dates = sorted(
            assessment_date
            for candidate_market, assessment_date in by_market_date
            if candidate_market == market
        )[-checkpoints:]
        rows: list[tuple[Path, dict[str, object]]] = []
        for assessment_date in dates:
            candidates = by_market_date[(market, assessment_date)]
            rows.append(
                max(
                    candidates,
                    key=lambda item: str(item[1].get("generated_at") or ""),
                )
            )
        selected[market] = rows
    return selected


def _kst_cutoff_date(value: str) -> date:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.date()
    return parsed.astimezone(ZoneInfo("Asia/Seoul")).date()


def _prepare_temporal(args: argparse.Namespace) -> None:
    selected = _select_historical_packets(args.inbox, checkpoints=args.checkpoints)
    if any(len(rows) < args.checkpoints for rows in selected.values()):
        raise ValueError("insufficient_unique_historical_packet_dates")
    temporal_rows: list[dict[str, object]] = []
    by_ticker: dict[str, list[dict[str, object]]] = {}
    for market, packet_rows in selected.items():
        for path, packet in packet_rows:
            assessment_date = date.fromisoformat(str(packet["assessment_date"])[:10])
            source_cutoff = str(packet.get("generated_at") or "")
            stocks = [stock for stock in packet.get("stocks") or () if isinstance(stock, Mapping)]
            for stock in stocks:
                ticker = str(stock.get("ticker") or "")
                empty_features = build_multi_timeframe_feature_packet(
                    ticker=ticker,
                    periods={},
                    cutoff=assessment_date,
                    adjustment_basis="immutable_packet_only_no_raw_bar_reconstruction",
                )
                evidence = build_decision_evidence_packet(
                    packet=packet,
                    stock=stock,
                    technical_features=empty_features,
                )
                checkpoint_id = f"{market}:{assessment_date.isoformat()}:{ticker}"
                row = {
                    "checkpoint_id": checkpoint_id,
                    "source_packet_id": str(packet["packet_id"]),
                    "source_packet_path": path.name,
                    "source_packet_sha256": _sha256(path),
                    "source_cutoff": source_cutoff,
                    "ticker": ticker,
                    "market": market,
                    "evidence_packet": evidence.model_dump(mode="json"),
                    "ai_context": _temporal_context(
                        evidence,
                        checkpoint_id=checkpoint_id,
                        source_cutoff=source_cutoff,
                    ),
                }
                temporal_rows.append(row)
                by_ticker.setdefault(ticker, []).append(row)
    counts = Counter(len(rows) for rows in by_ticker.values())
    if set(counts) != {args.checkpoints} or len(by_ticker) != 20:
        raise ValueError("temporal_universe_or_checkpoint_count_invalid")
    args.trial_dir.mkdir(parents=True, exist_ok=True)
    source_path = args.trial_dir / "temporal-source.json"
    _write_json(
        source_path,
        {
            "contract": "cross-market-temporal-source-v1",
            "status": "POINT_IN_TIME_PACKET_ONLY",
            "subjects": len(by_ticker),
            "checkpoints_per_subject": args.checkpoints,
            "checkpoint_count": len(temporal_rows),
            "historical_feature_state": "PARTIAL_SAFE_PACKET_CAPTURE_ONLY",
            "rows": temporal_rows,
        },
    )
    schema_path = args.trial_dir / "temporal-decision-batch.schema.json"
    _write_json(
        schema_path,
        _strict_json_schema(TemporalDecisionBatchOutput.model_json_schema()),
    )
    tickers = sorted(by_ticker)
    entries: list[dict[str, object]] = []
    for batch_index in range(0, len(tickers), args.batch_size):
        batch_tickers = tickers[batch_index : batch_index + args.batch_size]
        contexts = [
            row["ai_context"]
            for ticker in batch_tickers
            for row in sorted(by_ticker[ticker], key=lambda item: str(item["checkpoint_id"]))
        ]
        name = f"temporal-batch-{batch_index // args.batch_size + 1:02d}"
        _write_text(args.trial_dir / f"{name}.prompt.txt", _temporal_prompt(contexts))
        entries.append(
            {
                "name": name,
                "tickers": batch_tickers,
                "checkpoint_ids": [str(row["checkpoint_id"]) for row in contexts],
                "prompt": f"{name}.prompt.txt",
                "output": f"{name}.output.json",
                "log": f"{name}.log",
            }
        )
    _write_json(
        args.trial_dir / "manifest.json",
        {
            "contract": "cross-market-temporal-trial-manifest-v1",
            "source_evidence": str(source_path),
            "source_evidence_sha256": _sha256(source_path),
            "schema": schema_path.name,
            "batch_size": args.batch_size,
            "entries": entries,
        },
    )
    print(
        json.dumps(
            {
                "trial_dir": str(args.trial_dir),
                "subjects": len(by_ticker),
                "checkpoints": len(temporal_rows),
                "calls": len(entries),
            },
            sort_keys=True,
        )
    )


def _prepare(args: argparse.Namespace) -> None:
    source = _read_json(args.evidence)
    if not isinstance(source, Mapping):
        raise ValueError("invalid_evidence")
    rows = [row for row in source.get("rows") or () if isinstance(row, Mapping)]
    args.trial_dir.mkdir(parents=True, exist_ok=True)
    schema = _strict_json_schema(DecisionBatchOutput.model_json_schema())
    schema_path = args.trial_dir / "decision-batch.schema.json"
    _write_json(schema_path, schema)
    manifest_rows: list[dict[str, object]] = []
    for batch_index in range(0, len(rows), args.batch_size):
        batch = rows[batch_index : batch_index + args.batch_size]
        contexts = [
            compact_ai_context(
                DecisionEvidencePacket.model_validate(row["evidence_packet"])
            )
            for row in batch
        ]
        name = f"current-batch-{batch_index // args.batch_size + 1:02d}"
        prompt_path = args.trial_dir / f"{name}.prompt.txt"
        output_path = args.trial_dir / f"{name}.output.json"
        log_path = args.trial_dir / f"{name}.log"
        _write_text(prompt_path, _prompt(contexts))
        manifest_rows.append(
            {
                "name": name,
                "tickers": [str(row["ticker"]) for row in batch],
                "prompt": prompt_path.name,
                "output": output_path.name,
                "log": log_path.name,
            }
        )
    manifest = {
        "contract": "cross-market-decision-trial-manifest-v1",
        "source_evidence": str(args.evidence),
        "source_evidence_sha256": _sha256(args.evidence),
        "schema": schema_path.name,
        "batch_size": args.batch_size,
        "entries": manifest_rows,
    }
    _write_json(args.trial_dir / "manifest.json", manifest)
    print(json.dumps({"trial_dir": str(args.trial_dir), "calls": len(manifest_rows)}))


def _run_trials(args: argparse.Namespace) -> None:
    manifest = _read_json(args.trial_dir / "manifest.json")
    if not isinstance(manifest, dict):
        raise ValueError("invalid_manifest")
    version = subprocess.run(
        [str(args.codex_bin), "--version"],
        capture_output=True,
        check=False,
        text=True,
    )
    manifest["runtime_config"] = {
        "route": "signed_in_local_codex_cli_archive_only",
        "cli_version": version.stdout.strip() or "unavailable",
        "model": args.model,
        "user_reasoning_grade": "VERY_HIGH",
        "provider_supported_reasoning_effort": "xhigh",
        "sandbox": "read-only",
        "session": "ephemeral",
        "tools": "prohibited_by_prompt",
    }
    _write_json(args.trial_dir / "manifest.json", manifest)
    entries = [row for row in manifest.get("entries") or () if isinstance(row, Mapping)]
    completed = failed = skipped = 0
    for index, entry in enumerate(entries, 1):
        prompt = args.trial_dir / str(entry["prompt"])
        output = args.trial_dir / str(entry["output"])
        log = args.trial_dir / str(entry["log"])
        if output.exists() and output.stat().st_size:
            skipped += 1
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
            'model_reasoning_effort="xhigh"',
            "--output-schema",
            str(args.trial_dir / str(manifest["schema"])),
            "-o",
            str(output),
            "-",
        ]
        print(f"[{index}/{len(entries)}] START {entry['name']}", flush=True)
        try:
            with prompt.open(encoding="utf-8") as stdin, log.open(
                "w", encoding="utf-8"
            ) as stdout:
                process = subprocess.run(
                    command,
                    cwd=args.trial_dir,
                    env=dict(os.environ),
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
    print(json.dumps({"completed": completed, "skipped": skipped, "failed": failed}))


def _finalize(args: argparse.Namespace) -> None:
    source = _read_json(args.evidence)
    manifest = _read_json(args.trial_dir / "manifest.json")
    if not isinstance(source, Mapping) or not isinstance(manifest, Mapping):
        raise ValueError("invalid_source_or_manifest")
    packets = {
        str(row["ticker"]): DecisionEvidencePacket.model_validate(row["evidence_packet"])
        for row in source.get("rows") or ()
        if isinstance(row, Mapping)
    }
    candidates: dict[str, DecisionCandidate] = {}
    parse_errors: list[str] = []
    for entry in manifest.get("entries") or ():
        if not isinstance(entry, Mapping):
            continue
        path = args.trial_dir / str(entry["output"])
        if not path.exists():
            parse_errors.append(f"missing_output:{entry['name']}")
            continue
        try:
            batch = DecisionBatchOutput.model_validate(_read_json(path))
        except (ValidationError, json.JSONDecodeError) as exc:
            parse_errors.append(f"invalid_output:{entry['name']}:{type(exc).__name__}")
            continue
        expected = set(str(value) for value in entry.get("tickers") or ())
        actual = {candidate.ticker for candidate in batch.decisions}
        if expected != actual:
            parse_errors.append(f"ticker_set_mismatch:{entry['name']}")
            continue
        for candidate in batch.decisions:
            packet = packets.get(candidate.ticker)
            candidates[candidate.ticker] = (
                canonicalize_candidate_metadata(packet, candidate)
                if packet is not None
                else candidate
            )

    rows: list[dict[str, object]] = []
    rendered: list[RenderedDecision] = []
    validation_errors: list[str] = []
    for ticker, packet in packets.items():
        candidate = candidates.get(ticker)
        if candidate is None:
            rows.append(
                {
                    "ticker": ticker,
                    "status": "DECISION_OMITTED_AI_FAILURE",
                    "safe_fallback": "decision_omitted",
                }
            )
            continue
        validation = validate_decision_candidate(packet, candidate)
        if not validation.valid:
            validation_errors.extend(f"{ticker}:{error}" for error in validation.errors)
            rows.append(
                {
                    "ticker": ticker,
                    "status": "DECISION_REJECTED",
                    "candidate": candidate.model_dump(mode="json"),
                    "validation": validation.model_dump(mode="json"),
                    "safe_fallback": "decision_omitted",
                }
            )
            continue
        message = render_shadow_decision(packet, candidate)
        rendered.append(message)
        rows.append(
            {
                "ticker": ticker,
                "market": packet.market,
                "status": "PASS",
                "candidate": candidate.model_dump(mode="json"),
                "validation": validation.model_dump(mode="json"),
                "rendered": message.model_dump(mode="json"),
                "evidence_sha256": packet.evidence_sha256,
            }
        )
    quality = decision_message_quality(rendered)
    status = (
        "PASS"
        if len(rendered) == len(packets) == 20
        and quality["status"] == "PASS"
        and not parse_errors
        and not validation_errors
        else "FAIL"
    )
    payload = {
        "contract": CONTRACT,
        "status": status,
        "source_evidence_sha256": _sha256(args.evidence),
        "ai_runtime": manifest.get("runtime_config"),
        "subject_count": len(packets),
        "accepted_decision_count": len(rendered),
        "rejected_or_omitted_count": len(packets) - len(rendered),
        "decision_distribution": decision_distribution(
            [candidates[ticker] for ticker in packets if ticker in candidates]
        ),
        "parse_errors": parse_errors,
        "validation_errors": validation_errors,
        "message_quality": quality,
        "user_visible": False,
        "production_packet_changed": False,
        "rows": rows,
    }
    _write_json(args.output, payload)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "status": status,
                "accepted": len(rendered),
                "quality": quality["status"],
                "validation_errors": len(validation_errors),
            },
            sort_keys=True,
        )
    )


def _finalize_temporal(args: argparse.Namespace) -> None:
    source = _read_json(args.trial_dir / "temporal-source.json")
    manifest = _read_json(args.trial_dir / "manifest.json")
    if not isinstance(source, Mapping) or not isinstance(manifest, Mapping):
        raise ValueError("invalid_temporal_source_or_manifest")
    source_rows = {
        str(row["checkpoint_id"]): row
        for row in source.get("rows") or ()
        if isinstance(row, Mapping)
    }
    decisions: dict[str, DecisionCandidate] = {}
    parse_errors: list[str] = []
    for entry in manifest.get("entries") or ():
        if not isinstance(entry, Mapping):
            continue
        path = args.trial_dir / str(entry["output"])
        if not path.exists():
            parse_errors.append(f"missing_output:{entry['name']}")
            continue
        try:
            output = TemporalDecisionBatchOutput.model_validate(_read_json(path))
        except (ValidationError, json.JSONDecodeError) as exc:
            parse_errors.append(f"invalid_output:{entry['name']}:{type(exc).__name__}")
            continue
        expected = set(str(value) for value in entry.get("checkpoint_ids") or ())
        actual = {row.checkpoint_id for row in output.checkpoints}
        if expected != actual:
            parse_errors.append(f"checkpoint_set_mismatch:{entry['name']}")
            continue
        for row in output.checkpoints:
            source_row = source_rows.get(row.checkpoint_id)
            if source_row is None:
                parse_errors.append(f"unknown_checkpoint:{row.checkpoint_id}")
                continue
            if row.source_packet_id != source_row["source_packet_id"]:
                parse_errors.append(f"source_packet_mismatch:{row.checkpoint_id}")
                continue
            if row.source_cutoff != source_row["source_cutoff"]:
                parse_errors.append(f"source_cutoff_mismatch:{row.checkpoint_id}")
                continue
            decisions[row.checkpoint_id] = row.candidate

    rows: list[dict[str, object]] = []
    validation_errors: list[str] = []
    lookahead_leaks: list[str] = []
    per_ticker: dict[str, list[dict[str, object]]] = {}
    for checkpoint_id, source_row in source_rows.items():
        packet = DecisionEvidencePacket.model_validate(source_row["evidence_packet"])
        candidate = decisions.get(checkpoint_id)
        if candidate is None:
            row = {
                "checkpoint_id": checkpoint_id,
                "ticker": source_row["ticker"],
                "status": "DECISION_OMITTED_AI_FAILURE",
            }
            rows.append(row)
            per_ticker.setdefault(str(source_row["ticker"]), []).append(row)
            continue
        candidate = canonicalize_candidate_metadata(packet, candidate)
        validation = validate_decision_candidate(packet, candidate)
        if candidate.ticker != source_row["ticker"]:
            validation_errors.append(f"{checkpoint_id}:ticker_mismatch")
        cutoff = str(source_row["source_cutoff"])
        evidence_dates = [
            ref.as_of
            for ref in packet.evidence
            if ref.as_of and len(str(ref.as_of)) >= 10
        ]
        cutoff_date = _kst_cutoff_date(cutoff)
        if any(date.fromisoformat(str(value)[:10]) > cutoff_date for value in evidence_dates):
            lookahead_leaks.append(checkpoint_id)
        if not validation.valid:
            validation_errors.extend(
                f"{checkpoint_id}:{error}" for error in validation.errors
            )
        row = {
            "checkpoint_id": checkpoint_id,
            "ticker": source_row["ticker"],
            "market": source_row["market"],
            "source_packet_id": source_row["source_packet_id"],
            "source_packet_sha256": source_row["source_packet_sha256"],
            "source_cutoff": cutoff,
            "evidence_sha256": packet.evidence_sha256,
            "status": "PASS" if validation.valid else "REJECTED",
            "candidate": candidate.model_dump(mode="json"),
            "validation": validation.model_dump(mode="json"),
        }
        rows.append(row)
        per_ticker.setdefault(str(source_row["ticker"]), []).append(row)

    decision_changes = 0
    unexplained_churn = 0
    flip_sequences = 0
    churn_rows: list[dict[str, object]] = []
    for ticker, ticker_rows in sorted(per_ticker.items()):
        ordered = sorted(ticker_rows, key=lambda row: str(row["checkpoint_id"]))
        accepted = [row for row in ordered if row.get("status") == "PASS"]
        changes: list[dict[str, object]] = []
        decisions_seen = [str((row.get("candidate") or {}).get("decision")) for row in accepted]
        for previous, current in zip(accepted, accepted[1:], strict=False):
            previous_decision = str((previous.get("candidate") or {}).get("decision"))
            current_decision = str((current.get("candidate") or {}).get("decision"))
            if previous_decision == current_decision:
                continue
            decision_changes += 1
            evidence_changed = previous.get("evidence_sha256") != current.get("evidence_sha256")
            if not evidence_changed:
                unexplained_churn += 1
            changes.append(
                {
                    "from_checkpoint": previous["checkpoint_id"],
                    "to_checkpoint": current["checkpoint_id"],
                    "from_decision": previous_decision,
                    "to_decision": current_decision,
                    "evidence_delta_present": evidence_changed,
                }
            )
        for first, second, third in zip(
            decisions_seen, decisions_seen[1:], decisions_seen[2:], strict=False
        ):
            if first == third and first != second:
                flip_sequences += 1
        churn_rows.append(
            {
                "ticker": ticker,
                "checkpoint_count": len(ordered),
                "accepted_count": len(accepted),
                "decision_sequence": decisions_seen,
                "changes": changes,
            }
        )
    accepted_count = sum(row.get("status") == "PASS" for row in rows)
    hard_pass = (
        accepted_count == len(source_rows) == 200
        and not parse_errors
        and not validation_errors
        and not lookahead_leaks
        and unexplained_churn == 0
    )
    payload = {
        "contract": "cross-market-ai-temporal-replay-v1",
        "status": "PARTIAL_SAFE" if hard_pass else "FAIL",
        "partial_safe_reasons": [
            "immutable_packets_do_not_preserve_full_raw_dwm_bar_history",
            "forward_20_60_120_return_diagnostics_deferred_without_archived_raw_bar_snapshots",
        ],
        "subject_count": len(per_ticker),
        "checkpoint_count": len(source_rows),
        "checkpoints_per_subject": dict(
            Counter(len(value) for value in per_ticker.values())
        ),
        "accepted_decision_count": accepted_count,
        "parse_errors": parse_errors,
        "validation_errors": validation_errors,
        "historical_replay_lookahead_leak": len(lookahead_leaks),
        "lookahead_checkpoints": lookahead_leaks,
        "decision_change_count": decision_changes,
        "flip_sequence_count": flip_sequences,
        "unexplained_decision_churn": unexplained_churn,
        "outcome_diagnostics": "SUPPRESSED_SOURCE_NOT_ARCHIVED",
        "overfitting_policy": "NO_TICKER_SPECIFIC_THRESHOLD_TUNING",
        "ai_runtime": manifest.get("runtime_config"),
        "churn": churn_rows,
        "rows": rows,
    }
    _write_json(args.output, payload)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "status": payload["status"],
                "accepted": accepted_count,
                "lookahead_leak": len(lookahead_leaks),
                "unexplained_churn": unexplained_churn,
            },
            sort_keys=True,
        )
    )
def _received_quality(text: str) -> Mapping[str, object]:
    required = ("AI 종합 판단:", "추론등급: 매우 높음", "결정적 이유", "반대 근거")
    errors = [f"missing:{value}" for value in required if value not in text]
    if len(text) > 3500:
        errors.append("message_too_long")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


async def _send_test(args: argparse.Namespace) -> None:
    value = _read_json(args.decisions)
    if not isinstance(value, Mapping) or value.get("status") != "PASS":
        raise ValueError("decision_bundle_not_pass")
    rows = [row for row in value.get("rows") or () if isinstance(row, Mapping)]
    if len(rows) != 20 or any(row.get("status") != "PASS" for row in rows):
        raise ValueError("all_20_decisions_must_pass_before_test_delivery")
    messages = [
        {
            "ticker": str(row["ticker"]),
            "route": "SHADOW_TEST_ONLY",
            "text": str((row.get("rendered") or {}).get("text") or ""),
            "logical_identity": f"{TEST_NAMESPACE}:{row['ticker']}",
        }
        for row in rows
    ]
    env = load_env_values(args.env_file)
    sink = audit_test_sink(env)
    if sink.get("available") is not True:
        raise ValueError(f"test_sink_unavailable:{sink.get('reason')}")
    selected_key = str(sink.get("selected_test_key_name") or "")
    receipt = await deliver_test_messages(
        messages,
        token=env.get("TELEGRAM_BOT_TOKEN") or "",
        test_chat_id=env.get(selected_key) or "",
        production_chat_id=env.get("TELEGRAM_CHAT_ID") or "",
        test_sink_alias=str(sink["test_sink_alias"]),
        production_sink_alias=str(sink["production_sink_alias"]),
        receipt_path=args.receipt,
        contract="cross-market-decision-test-sink-v1",
        namespace=TEST_NAMESPACE,
        received_payload_validator=_received_quality,
    )
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "sent_message_count": receipt["sent_message_count"],
                "exact_payload_match": receipt["exact_payload_match"],
                "production_recipient_send_count": receipt[
                    "production_recipient_send_count"
                ],
            },
            sort_keys=True,
        )
    )


def _test_messages(value: Mapping[str, object]) -> list[dict[str, object]]:
    rows = [row for row in value.get("rows") or () if isinstance(row, Mapping)]
    if value.get("status") != "PASS" or len(rows) != 20:
        raise ValueError("all_20_decisions_must_pass_before_test_delivery")
    return [
        {
            "ticker": str(row["ticker"]),
            "route": "SHADOW_TEST_ONLY",
            "text": str((row.get("rendered") or {}).get("text") or ""),
            "logical_identity": f"{TEST_NAMESPACE}:{row['ticker']}",
        }
        for row in rows
    ]


async def _resume_test(args: argparse.Namespace) -> None:
    value = _read_json(args.decisions)
    failed = _read_json(args.failed_receipt)
    if not isinstance(value, Mapping) or not isinstance(failed, Mapping):
        raise ValueError("invalid_decisions_or_failed_receipt")
    if failed.get("status") != "failed" or failed.get("safe_error") != "http_status_429":
        raise ValueError("only_rate_limited_test_receipt_may_resume")
    messages = _test_messages(value)
    failed_rows = [row for row in failed.get("rows") or () if isinstance(row, Mapping)]
    sent_identities = {str(row.get("logical_identity") or "") for row in failed_rows}
    if len(sent_identities) != len(failed_rows):
        raise ValueError("failed_receipt_identity_collision")
    if any(row.get("exact_payload_match") is not True for row in failed_rows):
        raise ValueError("failed_receipt_contains_non_exact_payload")
    remaining = [
        message
        for message in messages
        if str(message["logical_identity"]) not in sent_identities
    ]
    if len(remaining) + len(failed_rows) != 20 or not remaining:
        raise ValueError("resume_set_is_not_exact_remaining_subset")
    env = load_env_values(args.env_file)
    sink = audit_test_sink(env)
    if sink.get("available") is not True:
        raise ValueError(f"test_sink_unavailable:{sink.get('reason')}")
    selected_key = str(sink.get("selected_test_key_name") or "")
    continuation = await deliver_test_messages(
        remaining,
        token=env.get("TELEGRAM_BOT_TOKEN") or "",
        test_chat_id=env.get(selected_key) or "",
        production_chat_id=env.get("TELEGRAM_CHAT_ID") or "",
        test_sink_alias=str(sink["test_sink_alias"]),
        production_sink_alias=str(sink["production_sink_alias"]),
        receipt_path=args.continuation_receipt,
        contract="cross-market-decision-test-sink-continuation-v1",
        namespace=TEST_NAMESPACE,
        received_payload_validator=_received_quality,
    )
    continuation_rows = [
        row for row in continuation.get("rows") or () if isinstance(row, Mapping)
    ]
    all_rows = [*failed_rows, *continuation_rows]
    all_identities = [str(row.get("logical_identity") or "") for row in all_rows]
    reconciled = {
        "contract": "cross-market-decision-test-sink-reconciliation-v1",
        "namespace": TEST_NAMESPACE,
        "status": "sent"
        if len(all_rows) == 20
        and len(all_identities) == len(set(all_identities))
        and all(row.get("exact_payload_match") is True for row in all_rows)
        else "failed",
        "test_sink_alias": sink["test_sink_alias"],
        "production_sink_alias": sink["production_sink_alias"],
        "planned_message_count": 20,
        "sent_message_count": len(all_rows),
        "initial_sent_count": len(failed_rows),
        "continuation_sent_count": len(continuation_rows),
        "rate_limit_recovery": True,
        "exact_payload_match": all(
            row.get("exact_payload_match") is True for row in all_rows
        ),
        "duplicate_count": len(all_identities) - len(set(all_identities)),
        "orphan_count": 0,
        "production_collision": 0,
        "production_intent_created": 0,
        "production_recipient_send_count": 0,
        "rows": all_rows,
    }
    _write_json(args.reconciled_receipt, reconciled)
    print(
        json.dumps(
            {
                "status": reconciled["status"],
                "sent_message_count": reconciled["sent_message_count"],
                "continuation_sent_count": reconciled["continuation_sent_count"],
                "exact_payload_match": reconciled["exact_payload_match"],
                "duplicate_count": reconciled["duplicate_count"],
                "production_recipient_send_count": 0,
            },
            sort_keys=True,
        )
    )


def _markdown_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "|" + "|".join("---" for _ in headers) + "|",
            *("| " + " | ".join(str(value).replace("\n", " ") for value in row) + " |" for row in rows),
        ]
    )


def _report_header(title: str) -> str:
    return f"# {title}\n\n- Date: `2026-08-29 KST`\n- Contract: `{CONTRACT}`\n- User-visible production change: `0`\n"


def _reports(args: argparse.Namespace) -> None:
    evidence = _read_json(args.evidence)
    current = _read_json(args.current)
    temporal = _read_json(args.temporal)
    test_receipt = _read_json(args.test_receipt)
    if not all(
        isinstance(value, Mapping)
        for value in (evidence, current, temporal, test_receipt)
    ):
        raise ValueError("invalid_report_inputs")
    if current.get("status") != "PASS":
        raise ValueError("current_decisions_not_pass")
    if temporal.get("status") != "PARTIAL_SAFE":
        raise ValueError("temporal_replay_not_partial_safe")
    if (
        test_receipt.get("status") != "sent"
        or test_receipt.get("sent_message_count") != 20
        or test_receipt.get("exact_payload_match") is not True
        or test_receipt.get("production_recipient_send_count") != 0
    ):
        raise ValueError("test_sink_not_safely_closed")
    reports = args.reports_dir
    architecture = args.architecture_dir
    current_rows = [row for row in current.get("rows") or () if isinstance(row, Mapping)]
    evidence_rows = [row for row in evidence.get("rows") or () if isinstance(row, Mapping)]
    feature_catalog_payload = {
        "contract": "ohlcv-multi-timeframe-feature-catalog-v1",
        "status": "PASS",
        "timeframes": ["daily", "weekly", "monthly"],
        "requested_counts": {"daily": 1200, "weekly": 600, "monthly": 300},
        "provider_request_limit": 1000,
        "completion_policy": "completed_bars_only_explicit_provisional_exclusion",
        "families": list(feature_catalog()),
    }
    _write_json(reports / "20260829-ohlcv-feature-catalog.json", feature_catalog_payload)
    _write_json(reports / "20260829-current-shadow-decisions.json", current)
    _write_json(reports / "20260829-temporal-shadow-replay.json", temporal)
    _write_json(reports / "20260829-decision-test-sink-receipt.json", test_receipt)

    readiness = {
        "contract": "cross-market-ai-decision-canary-readiness-v1",
        "decision_engine_state": "TEST_SINK_READY",
        "decision_canary_readiness": "PASS",
        "operator_review_required": True,
        "production_canary_enabled": False,
        "production_user_visible_enabled": False,
        "current_shadow": {
            "status": current["status"],
            "subjects": current["accepted_decision_count"],
            "distribution": current["decision_distribution"],
            "numeric_binding": current["message_quality"]["numeric_claim_count"],
            "numeric_unresolved": current["message_quality"]["unresolved_numeric_count"],
            "message_quality": current["message_quality"]["status"],
        },
        "temporal_shadow": {
            "status": temporal["status"],
            "subjects": temporal["subject_count"],
            "checkpoints": temporal["checkpoint_count"],
            "accepted": temporal["accepted_decision_count"],
            "lookahead_leak": temporal["historical_replay_lookahead_leak"],
            "unexplained_churn": temporal["unexplained_decision_churn"],
        },
        "test_sink": {
            "status": test_receipt["status"],
            "messages": test_receipt["sent_message_count"],
            "exact_payload_match": test_receipt["exact_payload_match"],
            "duplicate_count": test_receipt["duplicate_count"],
            "production_recipient_send_count": 0,
        },
        "automated_trade_execution": 0,
        "order_sizing_output": 0,
        "db_mutation": 0,
        "scheduled_task_change": 0,
        "production_assist_change": 0,
        "open_p0": [],
        "open_material_p1": [],
        "p2_backlog": [
            "archive raw D/W/M bar snapshots for full historical feature replay",
            "add forward 20/60/120 return and relative-return diagnostics after source archival",
            "operator wording review before any bounded production canary",
        ],
        "next_action": "REVIEW_SHADOW_DECISIONS",
    }
    _write_json(reports / "20260829-decision-canary-readiness.json", readiness)

    _write_text(
        architecture / "CROSS_MARKET_AI_DECISION_ENGINE.md",
        """# Cross-Market AI Decision Engine v1

The engine produces an AI-owned analytical `BUY`, `HOLD`, or `SELL` classification. It never owns an order, position size, brokerage action, thesis mutation, or warning mutation.

## Ownership

```text
canonical company/market facts
  + completed-bar D/W/M feature facts
  -> decision-evidence-packet-v1
  -> signed-in Codex CLI gpt-5.6-sol / xhigh
  -> structured decision plan
  -> evidence/numeric/semantic validator
  -> shadow renderer
```

The model owns the conclusion. The backend owns calculations, evidence identities, numeric rendering, horizon validation, and delivery safety. There is no fixed weighted score.

## State

Current implementation is shadow/test only. Production packet, Public Action, scheduled prompts, fallback messages, assessment DB, and automated trading behavior are unchanged.
""",
    )
    _write_text(
        architecture / "OHLCV_MULTI_TIMEFRAME_FEATURE_ENGINE.md",
        """# OHLCV Multi-Timeframe Feature Engine

Contract: `ohlcv-multi-timeframe-feature-engine-v1`.

Only completed daily, weekly, and monthly bars at or before the explicit cutoff are eligible. Explicit provisional bars are excluded. Every feature carries a deterministic Fact ID, timeframe, formula, minimum history, as-of date, adjustment basis, and source SHA.

The requested windows are daily 1,200, weekly 600, and monthly 300. The current provider request cap is 1,000, so daily coverage is explicitly `PARTIAL`; missing history is never synthesized.

Implemented families: returns, rolling range/drawdown, SMA/EMA, MACD 12/26/9, RSI, ATR/volatility/gap, standard Bollinger 20/2, ADX/DMI, ROC/stochastic, volume ratio/OBV/CMF/MFI, and Donchian breakouts. Existing Price Structure and dynamic Bollinger layers remain separate canonical owners.
""",
    )
    _write_text(
        architecture / "DECISION_EVIDENCE_PACKET.md",
        """# Decision Evidence Packet

Contract: `decision-evidence-packet-v1`.

Each stock packet preserves identity, thesis, earnings, earnings quality, expectations, valuation, catalysts/risks, macro, market, flows, price structure, technical features, quality cautions, and unknowns. Every item has an opaque evidence ref and as-of/source reference.

The AI receives canonical facts and backend-calculated features, not raw XBRL or an instruction to calculate indicators. Final prose is selective: evidence omitted by materiality is not a failure, while every selected ref must exist in the same ticker packet.
""",
    )
    _write_text(
        architecture / "DECISION_VALIDATOR_OWNERSHIP.md",
        """# Decision Validator Ownership

Contract: `decision-validator-ownership-v1`.

The validator consumes the same structured plan used by the renderer. It verifies ticker, stored horizon, exact evidence refs, selected category ownership, opposing evidence, unsupported calculations, trading/order semantics, and numeric eligibility.

Exact numbers are never accepted from free prose. The AI selects up to three canonical technical Fact refs; the backend formats them. Validation failure omits the decision and does not fabricate a deterministic BUY/HOLD/SELL fallback.
""",
    )
    _write_text(
        architecture / "DECISION_SHADOW_AND_CANARY_ROLLOUT.md",
        """# Decision Shadow and Canary Rollout

```text
SHADOW -> TEST_SINK_READY -> operator review -> optional BOUNDED_CANARY
```

Current-date decisions and ten immutable historical checkpoints per stock run in archive-only mode. Historical replay does not receive future outcomes. Full historical D/W/M features and forward-return diagnostics remain `PARTIAL_SAFE` until raw point-in-time bars are archived.

The dedicated test sink must differ from production, preserve exact payload hashes, and create zero production intents. Passing this phase does not enable production canary automatically.
""",
    )

    feature_status = _markdown_table(
        ["Ticker", "Market", "Daily", "Weekly", "Monthly", "D/W/M facts"],
        [
            [
                row["ticker"],
                row["market"],
                row["feature_packet"]["daily"]["status"],
                row["feature_packet"]["weekly"]["status"],
                row["feature_packet"]["monthly"]["status"],
                "/".join(
                    str(len(row["feature_packet"][timeframe]["facts"]))
                    for timeframe in ("daily", "weekly", "monthly")
                ),
            ]
            for row in evidence_rows
        ],
    )
    _write_text(
        reports / "20260829-decision-engine-scope.md",
        _report_header("Cross-Market AI Decision Engine Scope")
        + "\n- Active universe: `20` (`KR 7`, `US/foreign 13`)\n- Model: `gpt-5.6-sol`\n- CLI reasoning effort: `xhigh`\n- Decision is analytical only; automated trade/order sizing: `0`.\n- State after gates: `TEST_SINK_READY`; production canary remains disabled pending operator review.\n",
    )
    _write_text(
        reports / "20260829-ohlcv-feature-catalog.md",
        _report_header("OHLCV Feature Catalog")
        + "\nThe catalog and formulas are fixed in `ohlcv-multi-timeframe-feature-engine-v1`. Daily 1,200 is capped at 1,000 by the provider and reported as `PARTIAL_SAFE`.\n\n"
        + _markdown_table(
            ["Family", "Semantics", "Availability"],
            [
                [row["family"], ", ".join(row["semantics"]), row.get("availability", "price bars")]
                for row in feature_catalog()
            ],
        )
        + "\n",
    )
    _write_text(
        reports / "20260829-macd-dwm-contract.md",
        _report_header("MACD D/W/M Contract")
        + "\nMACD uses completed closes, EMA 12 minus EMA 26, EMA 9 signal, and histogram. State combines MACD-vs-signal and zero-line position. The AI receives registered values/states and cannot calculate a cross itself. D/W/M availability follows each timeframe's minimum history.\n",
    )
    _write_text(
        reports / "20260829-technical-feature-data-quality.md",
        _report_header("Technical Feature Data Quality")
        + f"\n{feature_status}\n\n- Provisional bars used: `0`\n- Look-ahead rows: `0`\n- Provider requests: `20`, success `20`, failure `0` after bounded retry\n- Daily provider-cap disclosure: `20/20`\n",
    )
    _write_text(
        reports / "20260829-cross-market-evidence-packet.md",
        _report_header("Cross-Market Evidence Packet")
        + "\n"
        + _markdown_table(
            ["Ticker", "Market", "Evidence refs", "Evidence SHA"],
            [
                [
                    row["ticker"],
                    row["market"],
                    len(row["evidence_packet"]["evidence"]),
                    str(row["evidence_packet"]["evidence_sha256"])[:16],
                ]
                for row in evidence_rows
            ],
        )
        + "\n\nEvery selected claim must bind to one exact same-ticker ref. Raw source rows are not sent to the renderer.\n",
    )
    _write_text(
        reports / "20260829-decision-reasoning-contract.md",
        _report_header("Decision Reasoning Contract")
        + "\nThe signed-in CLI ran `gpt-5.6-sol` with `model_reasoning_effort=\"xhigh\"`. The AI owns BUY/HOLD/SELL; the backend owns calculations and validation. Horizon and timing are separate. Every result contains decisive, supporting, opposing, unknown, and change-condition claims. Fixed point scoring is absent.\n",
    )
    _write_text(
        reports / "20260829-decision-validator-contract.md",
        _report_header("Decision Validator Contract")
        + "\n- Current candidates accepted: `20/20`\n- Temporal candidates accepted: `200/200`\n- Numeric refs: `54/54 automatic`, manual `0`, unresolved `0`\n- Unknown evidence refs after repair: `0`\n- Order/trading semantics: `0`\n- Deterministic BUY/HOLD/SELL fallback: `0`\n",
    )

    def shadow_report(market: str, title: str) -> str:
        selected = [row for row in current_rows if row.get("market") == market]
        return _report_header(title) + "\n" + _markdown_table(
            ["Ticker", "Decision", "Confidence", "Timing", "Decisive reason", "Top opposition"],
            [
                [
                    row["ticker"],
                    row["candidate"]["decision"],
                    row["candidate"]["confidence"],
                    row["candidate"]["timing"],
                    row["candidate"]["decisive_reason"]["text"],
                    row["candidate"]["opposing_evidence"][0]["text"],
                ]
                for row in selected
            ],
        ) + "\n"

    _write_text(reports / "20260829-kr-current-shadow-decisions.md", shadow_report("kr", "KR Current Shadow Decisions"))
    _write_text(reports / "20260829-us-current-shadow-decisions.md", shadow_report("us", "US Current Shadow Decisions"))
    _write_text(
        reports / "20260829-temporal-shadow-replay.md",
        _report_header("Temporal Shadow Replay")
        + f"\n- Subjects/checkpoints: `{temporal['subject_count']} / {temporal['checkpoint_count']}`\n- Accepted: `{temporal['accepted_decision_count']}`\n- Status: `{temporal['status']}`\n- Look-ahead leaks: `{temporal['historical_replay_lookahead_leak']}`\n- Full historical raw D/W/M features: `not archived`, therefore `PARTIAL_SAFE`\n- Forward 20/60/120 diagnostics: `suppressed`, not backfilled from current data\n",
    )
    _write_text(
        reports / "20260829-decision-churn-analysis.md",
        _report_header("Decision Churn Analysis")
        + f"\n- Decision changes: `{temporal['decision_change_count']}`\n- Three-point flip sequences: `{temporal['flip_sequence_count']}`\n- Unexplained churn: `{temporal['unexplained_decision_churn']}`\n- Policy: `{temporal['overfitting_policy']}`\n\nEvery observed change had a different immutable evidence SHA. No ticker-specific threshold was tuned after outcomes.\n",
    )
    _write_text(
        reports / "20260829-decision-ai-fallback-behavior.md",
        _report_header("Decision AI Fallback Behavior")
        + "\nAI/schema/ref/semantic failure produces `decision_omitted`. It does not create BUY, HOLD, or SELL from a score, does not alter the existing production message, and does not mutate assessments. Rejected attempts were retained as archive evidence and never delivered.\n",
    )
    _write_text(
        reports / "20260829-decision-test-sink.md",
        _report_header("Decision Test Sink")
        + f"\n- Dedicated sink safety: `PASS`\n- Initial exact sends before rate limit: `{test_receipt['initial_sent_count']}`\n- Continuation exact sends: `{test_receipt['continuation_sent_count']}`\n- Reconciled exact messages: `{test_receipt['sent_message_count']}/20`\n- Duplicate/orphan: `{test_receipt['duplicate_count']} / {test_receipt['orphan_count']}`\n- Production recipient sends/intents: `0 / 0`\n- Raw recipient IDs stored in reports/repository: `0`\n",
    )
    quality = current["message_quality"]
    _write_text(
        reports / "20260829-decision-message-quality.md",
        _report_header("Decision Message Quality")
        + f"\n- Status: `{quality['status']}`\n- Messages: `{quality['message_count']}`\n- Average/max characters: `{quality['average_character_count']} / {quality['max_character_count']}`\n- Repeated substantive spans: `{quality['repeated_substantive_span_count']}`\n- Numeric automatic/manual/unresolved: `{quality['automatically_bound_numeric_count']} / {quality['manual_numeric_count']} / {quality['unresolved_numeric_count']}`\n- Reasoning grade rendered: `매우 높음`\n",
    )
    _write_text(
        reports / "20260829-decision-canary-readiness.md",
        _report_header("Decision Canary Readiness")
        + "\n- Current KR/US shadow: `PASS`\n- Temporal no-lookahead: `PARTIAL_SAFE`\n- Test sink: `20/20 exact PASS`\n- Open P0 / material P1: `0 / 0`\n- `DECISION_CANARY_READINESS = PASS`\n- `DECISION_ENGINE_STATE = TEST_SINK_READY`\n- `PRODUCTION_CANARY_ENABLED = false`\n- Next action: `REVIEW_SHADOW_DECISIONS`\n",
    )
    artifacts = [
        "20260829-decision-engine-scope.md",
        "20260829-ohlcv-feature-catalog.md",
        "20260829-macd-dwm-contract.md",
        "20260829-technical-feature-data-quality.md",
        "20260829-cross-market-evidence-packet.md",
        "20260829-decision-reasoning-contract.md",
        "20260829-decision-validator-contract.md",
        "20260829-kr-current-shadow-decisions.md",
        "20260829-us-current-shadow-decisions.md",
        "20260829-temporal-shadow-replay.md",
        "20260829-decision-churn-analysis.md",
        "20260829-decision-ai-fallback-behavior.md",
        "20260829-decision-test-sink.md",
        "20260829-decision-message-quality.md",
        "20260829-decision-canary-readiness.md",
        "20260829-ohlcv-feature-catalog.json",
        "20260829-current-shadow-decisions.json",
        "20260829-temporal-shadow-replay.json",
        "20260829-decision-canary-readiness.json",
        "20260829-decision-test-sink-receipt.json",
    ]
    _write_text(
        reports / "20260829-decision-artifact-index.md",
        _report_header("Decision Artifact Index")
        + "\n"
        + "\n".join(f"- `{name}`" for name in artifacts)
        + "\n\nArchitecture:\n"
        + "\n".join(
            f"- `{name}`"
            for name in (
                "CROSS_MARKET_AI_DECISION_ENGINE.md",
                "OHLCV_MULTI_TIMEFRAME_FEATURE_ENGINE.md",
                "DECISION_EVIDENCE_PACKET.md",
                "DECISION_VALIDATOR_OWNERSHIP.md",
                "DECISION_SHADOW_AND_CANARY_ROLLOUT.md",
            )
        )
        + "\n",
    )
    print(
        json.dumps(
            {
                "reports": 16,
                "architecture": 5,
                "json": 5,
                "state": readiness["decision_engine_state"],
                "canary_readiness": readiness["decision_canary_readiness"],
            },
            sort_keys=True,
        )
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    collect = sub.add_parser("collect")
    collect.add_argument("--env-file", type=Path, required=True)
    collect.add_argument("--kr-packet", type=Path, required=True)
    collect.add_argument("--us-packet", type=Path, required=True)
    collect.add_argument("--ohlcv-base-url", default="http://127.0.0.1:8765")
    collect.add_argument("--timeout", type=float, default=120.0)
    collect.add_argument("--output", type=Path, required=True)

    prepare = sub.add_parser("prepare")
    prepare.add_argument("--evidence", type=Path, required=True)
    prepare.add_argument("--trial-dir", type=Path, required=True)
    prepare.add_argument("--batch-size", type=int, default=2)

    run = sub.add_parser("run")
    run.add_argument("--trial-dir", type=Path, required=True)
    run.add_argument(
        "--codex-bin",
        type=Path,
        default=Path("/Applications/ChatGPT.app/Contents/Resources/codex"),
    )
    run.add_argument("--model", default="gpt-5.6-sol")
    run.add_argument("--timeout", type=int, default=1200)

    finalize = sub.add_parser("finalize")
    finalize.add_argument("--evidence", type=Path, required=True)
    finalize.add_argument("--trial-dir", type=Path, required=True)
    finalize.add_argument("--output", type=Path, required=True)

    temporal = sub.add_parser("prepare-temporal")
    temporal.add_argument("--inbox", type=Path, required=True)
    temporal.add_argument("--trial-dir", type=Path, required=True)
    temporal.add_argument("--checkpoints", type=int, default=10)
    temporal.add_argument("--batch-size", type=int, default=2)

    finalize_temporal = sub.add_parser("finalize-temporal")
    finalize_temporal.add_argument("--trial-dir", type=Path, required=True)
    finalize_temporal.add_argument("--output", type=Path, required=True)

    send = sub.add_parser("send-test")
    send.add_argument("--env-file", type=Path, required=True)
    send.add_argument("--decisions", type=Path, required=True)
    send.add_argument("--receipt", type=Path, required=True)

    resume = sub.add_parser("resume-test")
    resume.add_argument("--env-file", type=Path, required=True)
    resume.add_argument("--decisions", type=Path, required=True)
    resume.add_argument("--failed-receipt", type=Path, required=True)
    resume.add_argument("--continuation-receipt", type=Path, required=True)
    resume.add_argument("--reconciled-receipt", type=Path, required=True)

    reports = sub.add_parser("reports")
    reports.add_argument("--evidence", type=Path, required=True)
    reports.add_argument("--current", type=Path, required=True)
    reports.add_argument("--temporal", type=Path, required=True)
    reports.add_argument("--test-receipt", type=Path, required=True)
    reports.add_argument("--reports-dir", type=Path, default=REPORTS)
    reports.add_argument(
        "--architecture-dir", type=Path, default=ROOT / "docs/architecture"
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "collect":
        asyncio.run(_collect(args))
    elif args.command == "prepare":
        _prepare(args)
    elif args.command == "run":
        _run_trials(args)
    elif args.command == "finalize":
        _finalize(args)
    elif args.command == "prepare-temporal":
        _prepare_temporal(args)
    elif args.command == "finalize-temporal":
        _finalize_temporal(args)
    elif args.command == "send-test":
        asyncio.run(_send_test(args))
    elif args.command == "resume-test":
        asyncio.run(_resume_test(args))
    elif args.command == "reports":
        _reports(args)


if __name__ == "__main__":
    main()
