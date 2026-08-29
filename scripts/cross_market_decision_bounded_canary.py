from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
from collections import Counter
from collections.abc import Mapping
from datetime import UTC, date, datetime
from pathlib import Path

import httpx

from app.config import Settings
from app.services.cross_market_decision_engine_service import (
    DecisionCandidate,
    DecisionEvidencePacket,
    build_decision_evidence_packet,
    compact_ai_context,
)
from app.services.decision_canary_service import (
    CANARY_REASONING_EFFORT,
    CANARY_REASONING_MODEL,
    DecisionCanaryBatchOutput,
    DecisionCanaryContext,
    DecisionCanaryState,
    DecisionCanaryStateEntry,
    DecisionPolarityPlanBatch,
    apply_decision_polarity_plan,
    build_decision_canary_context,
    decision_canary_prompt,
    insert_decision_canary_block,
    polarity_claim_errors,
    render_decision_canary_block,
    strict_json_schema,
    validate_decision_canary_output,
    write_decision_canary_state,
)
from app.services.ohlcv_feature_engine_service import build_multi_timeframe_feature_packet
from scripts.kr_final_preenable_test_delivery import deliver_test_messages
from scripts.kr_market_preenable_evidence import audit_test_sink, load_env_values


SUBJECTS = {"kr": ("003690", "000660"), "us": ("GOOGL", "RXRX")}
CONTRACT = "cross-market-decision-bounded-canary-v1"
TEST_NAMESPACE = "CROSS_MARKET_DECISION_BOUNDED_CANARY_TEST_ONLY"


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


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


async def _fetch_ohlcv(
    client: httpx.AsyncClient,
    *,
    ticker: str,
    base_url: str,
    api_key: str,
) -> tuple[str, dict[str, object], int]:
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
            value = response.json()
            if not isinstance(value, dict) or not isinstance(value.get("periods"), dict):
                raise ValueError(f"invalid_ohlcv_response:{ticker}")
            return ticker, value, attempt + 1
        except (httpx.HTTPError, ValueError) as exc:
            last_error = exc
            if attempt < 2:
                await asyncio.sleep(1.0 + attempt)
    assert last_error is not None
    raise last_error


def _canary_settings(env_file: Path) -> Settings:
    return Settings(_env_file=env_file).model_copy(
        update={
            "decision_engine_canary_enabled": True,
            "decision_engine_state": "canary",
            "decision_engine_canary_kr_subjects": ",".join(SUBJECTS["kr"]),
            "decision_engine_canary_us_subjects": ",".join(SUBJECTS["us"]),
        }
    )


async def _prepare(args: argparse.Namespace) -> None:
    settings = _canary_settings(args.env_file)
    api_key = settings.action_api_key or settings.ohlcv_api_key or ""
    if not api_key:
        raise ValueError("ohlcv_api_key_missing")
    packet_paths = {"kr": args.kr_packet, "us": args.us_packet}
    packets: dict[str, dict[str, object]] = {}
    for market, path in packet_paths.items():
        value = _read_json(path)
        if not isinstance(value, dict) or value.get("market") != market:
            raise ValueError(f"invalid_{market}_packet")
        packets[market] = value
    timeout = httpx.Timeout(settings.ohlcv_timeout_seconds, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        fetched_rows = await asyncio.gather(
            *(
                _fetch_ohlcv(
                    client,
                    ticker=ticker,
                    base_url=settings.ohlcv_base_url,
                    api_key=api_key,
                )
                for ticker in (*SUBJECTS["kr"], *SUBJECTS["us"])
            )
        )
    fetched = {ticker: payload for ticker, payload, _attempts in fetched_rows}
    provider_request_count = sum(attempts for _ticker, _payload, attempts in fetched_rows)
    evidence_rows: list[dict[str, object]] = []
    contexts: dict[str, DecisionCanaryContext] = {}
    for market, packet in packets.items():
        stocks = {
            str(row.get("ticker") or "").upper(): row
            for row in packet.get("stocks") or ()
            if isinstance(row, Mapping)
        }
        if any(ticker not in stocks for ticker in SUBJECTS[market]):
            raise ValueError(f"configured_subject_missing:{market}")
        cutoff = date.fromisoformat(str(packet.get("assessment_date") or "")[:10])
        evidence_packets: list[DecisionEvidencePacket] = []
        for ticker in SUBJECTS[market]:
            periods = fetched[ticker].get("periods")
            assert isinstance(periods, Mapping)
            features = build_multi_timeframe_feature_packet(
                ticker=ticker,
                periods={
                    str(key): value for key, value in periods.items() if isinstance(value, list)
                },
                cutoff=cutoff,
            )
            evidence = build_decision_evidence_packet(
                packet=packet,
                stock=stocks[ticker],
                technical_features=features,
            )
            evidence_packets.append(evidence)
            evidence_rows.append(
                {
                    "ticker": ticker,
                    "market": market,
                    "source_packet": str(packet_paths[market]),
                    "source_packet_sha256": _sha256(packet_paths[market]),
                    "source_packet_id": packet.get("packet_id"),
                    "assessment_date": packet.get("assessment_date"),
                    "provider": "local_ohlcv_api",
                    "evidence_packet": evidence.model_dump(mode="json"),
                    "feature_packet": features.model_dump(mode="json"),
                }
            )
        context = build_decision_canary_context(
            packet=packet,
            claim_id=f"preenable-{market}-{packet['packet_id']}",
            evidence_packets=evidence_packets,
            settings=settings,
        )
        contexts[market] = context
        _write_json(args.trial_dir / f"{market}-context.json", context.model_dump(mode="json"))
        _write_text(args.trial_dir / f"{market}-prompt.txt", decision_canary_prompt(context))
    _write_json(
        args.trial_dir / "output-schema.json",
        strict_json_schema(DecisionCanaryBatchOutput.model_json_schema()),
    )
    collected_at = datetime.now(UTC).isoformat()
    _write_json(
        args.evidence_output,
        {
            "contract": CONTRACT,
            "status": "PASS",
            "collected_at": collected_at,
            "subjects": SUBJECTS,
            "provider_calls": {
                "local_ohlcv_api": {
                    "request_count": provider_request_count,
                    "success_count": 4,
                    "failure_count": provider_request_count - 4,
                },
                "SEC": {"request_count": 0},
                "OpenDART": {"request_count": 0},
                "paid_provider": {"request_count": 0},
            },
            "rows": evidence_rows,
        },
    )
    _write_json(
        args.trial_dir / "manifest.json",
        {
            "contract": CONTRACT,
            "evidence_path": str(args.evidence_output),
            "evidence_sha256": _sha256(args.evidence_output),
            "markets": {
                market: {
                    "context": f"{market}-context.json",
                    "prompt": f"{market}-prompt.txt",
                    "output": f"{market}-output.json",
                    "artifact": f"{market}-artifact.json",
                    "log": f"{market}-codex.log",
                }
                for market in ("kr", "us")
            },
        },
    )
    print(
        json.dumps(
            {"status": "PASS", "provider_calls": provider_request_count},
            sort_keys=True,
        )
    )


def _run(args: argparse.Namespace) -> None:
    manifest = _read_json(args.trial_dir / "manifest.json")
    if not isinstance(manifest, Mapping):
        raise ValueError("invalid_manifest")
    markets = manifest.get("markets")
    if not isinstance(markets, Mapping):
        raise ValueError("invalid_market_manifest")
    rows: list[dict[str, object]] = []
    for market in ("kr", "us"):
        entry = markets.get(market)
        if not isinstance(entry, Mapping):
            raise ValueError(f"manifest_market_missing:{market}")
        prompt_path = args.trial_dir / str(entry["prompt"])
        output_path = args.trial_dir / str(entry["output"])
        log_path = args.trial_dir / str(entry["log"])
        artifact_path = args.trial_dir / str(entry["artifact"])
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
            CANARY_REASONING_MODEL,
            "-c",
            f'model_reasoning_effort="{CANARY_REASONING_EFFORT}"',
            "--output-schema",
            str(args.trial_dir / "output-schema.json"),
            "-o",
            str(output_path),
            "-",
        ]
        context = DecisionCanaryContext.model_validate(
            _read_json(args.trial_dir / str(entry["context"]))
        )
        if artifact_path.exists():
            artifact = validate_decision_canary_output(
                context,
                DecisionCanaryBatchOutput.model_validate(_read_json(output_path)),
            )
        else:
            base_prompt = prompt_path.read_text(encoding="utf-8")
            last_error: ValueError | None = None
            artifact = None
            attempts = (1, 2)
            if output_path.exists() and output_path.stat().st_size:
                existing = DecisionCanaryBatchOutput.model_validate(_read_json(output_path))
                try:
                    artifact = validate_decision_canary_output(context, existing)
                except ValueError as exc:
                    last_error = exc
                    attempts = (2,)
            for attempt in attempts if artifact is None else ():
                active_prompt = prompt_path
                active_log = log_path
                if attempt == 2:
                    assert last_error is not None
                    rejected_path = output_path.with_name(
                        output_path.stem + ".rejected-attempt-01.json"
                    )
                    rejected_output = output_path.read_text(encoding="utf-8")
                    output_path.replace(rejected_path)
                    active_prompt = prompt_path.with_name(prompt_path.stem + ".correction.txt")
                    active_log = log_path.with_name(log_path.stem + ".correction.log")
                    _write_text(
                        active_prompt,
                        base_prompt
                        + "\n\nCORRECTION ATTEMPT (one allowed):\n"
                        + "The prior output was rejected by the backend with: "
                        + str(last_error)
                        + "\nReturn a complete replacement. Preserve the analytical standard, "
                        + "but cite only exact complete ref_id values present in the evidence packets. "
                        + "Do not copy or repair a ref_id by approximation.\n\n"
                        + "REJECTED OUTPUT FOR CORRECTION:\n"
                        + rejected_output,
                    )
                with (
                    active_prompt.open(encoding="utf-8") as stdin,
                    active_log.open("w", encoding="utf-8") as stdout,
                ):
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
                if process.returncode != 0:
                    raise RuntimeError(f"codex_generation_failed:{market}:attempt_{attempt}")
                output = DecisionCanaryBatchOutput.model_validate(_read_json(output_path))
                try:
                    artifact = validate_decision_canary_output(context, output)
                    break
                except ValueError as exc:
                    last_error = exc
            if artifact is None:
                raise ValueError(f"decision_validation_failed_after_correction:{market}")
            _write_json(artifact_path, artifact.model_dump(mode="json"))
        for evidence, candidate, block in zip(
            artifact.evidence_packets,
            artifact.decisions,
            artifact.blocks,
            strict=True,
        ):
            rows.append(
                {
                    "ticker": candidate.ticker,
                    "market": market,
                    "packet_id": artifact.packet_id,
                    "assessment_date": artifact.assessment_date,
                    "decision": candidate.decision,
                    "confidence": candidate.confidence,
                    "confidence_reason": candidate.confidence_reason,
                    "horizon": candidate.horizon,
                    "timing": candidate.timing,
                    "hold_reason": candidate.hold_reason,
                    "candidate": candidate.model_dump(mode="json"),
                    "evidence_packet": evidence.model_dump(mode="json"),
                    "block": block.model_dump(mode="json"),
                    "status": "PASS",
                }
            )
    distribution = Counter(str(row["decision"]) for row in rows)
    _write_json(
        args.output,
        {
            "contract": CONTRACT,
            "status": "PASS",
            "reasoning_model": CANARY_REASONING_MODEL,
            "reasoning_effort": CANARY_REASONING_EFFORT,
            "reasoning_grade": "VERY_HIGH",
            "subject_count": len(rows),
            "decision_distribution": {
                key: distribution.get(key, 0) for key in ("BUY", "HOLD", "SELL")
            },
            "rows": rows,
        },
    )
    print(json.dumps({"status": "PASS", "distribution": dict(distribution)}, sort_keys=True))


def _apply_continuity(args: argparse.Namespace) -> None:
    settings = _canary_settings(args.env_file)
    evidence_value = _read_json(args.evidence)
    decisions_value = _read_json(args.continuity_decisions)
    if not isinstance(evidence_value, Mapping) or not isinstance(decisions_value, Mapping):
        raise ValueError("continuity_inputs_invalid")
    evidence = {
        str(row.get("ticker") or ""): DecisionEvidencePacket.model_validate(row["evidence_packet"])
        for row in evidence_value.get("rows") or ()
        if isinstance(row, Mapping) and isinstance(row.get("evidence_packet"), Mapping)
    }
    target_subjects = {*SUBJECTS["kr"], *SUBJECTS["us"]}
    continuity = {
        str(row.get("ticker") or ""): DecisionCandidate.model_validate(row["candidate"])
        for row in decisions_value.get("rows") or ()
        if isinstance(row, Mapping)
        and isinstance(row.get("candidate"), Mapping)
        and str(row.get("ticker") or "") in target_subjects
    }
    if set(continuity) != target_subjects:
        raise ValueError("continuity_subjects_incomplete")
    packet_paths = {"kr": args.kr_packet, "us": args.us_packet}
    manifest = _read_json(args.trial_dir / "manifest.json")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("markets"), Mapping):
        raise ValueError("invalid_manifest")
    for market, packet_path in packet_paths.items():
        packet = _read_json(packet_path)
        if not isinstance(packet, Mapping):
            raise ValueError(f"invalid_packet:{market}")
        context = build_decision_canary_context(
            packet=packet,
            claim_id=f"preenable-{market}-{packet['packet_id']}",
            evidence_packets=tuple(evidence[ticker] for ticker in SUBJECTS[market]),
            continuity_candidates={ticker: continuity[ticker] for ticker in SUBJECTS[market]},
            continuity_source="20260829-repaired-20-stock-decisions",
            settings=settings,
        )
        _write_json(
            args.trial_dir / f"{market}-context.json",
            context.model_dump(mode="json"),
        )
        _write_text(
            args.trial_dir / f"{market}-prompt.txt",
            decision_canary_prompt(context),
        )
        entry = manifest["markets"][market]
        assert isinstance(entry, Mapping)
        for key in ("output", "artifact"):
            path = args.trial_dir / str(entry[key])
            if path.exists():
                archive = path.with_name(path.stem + ".pre-continuity-churn.json")
                path.replace(archive)
    manifest["continuity_source"] = str(args.continuity_decisions)
    manifest["continuity_source_sha256"] = _sha256(args.continuity_decisions)
    manifest["unexplained_pre_continuity_churn"] = ["000660", "RXRX"]
    _write_json(args.trial_dir / "manifest.json", manifest)
    print(json.dumps({"status": "PASS", "continuity_subjects": 4}, sort_keys=True))


def _enrich_polarity(args: argparse.Namespace) -> None:
    decisions_value = _read_json(args.decisions)
    evidence_value = _read_json(args.evidence)
    if not isinstance(decisions_value, Mapping) or not isinstance(evidence_value, Mapping):
        raise ValueError("polarity_inputs_invalid")
    requested = tuple(item.strip().upper() for item in args.tickers.split(",") if item.strip())
    if not requested or len(requested) != len(set(requested)):
        raise ValueError("polarity_tickers_invalid")
    candidates = {
        str(row.get("ticker") or "").upper(): row["candidate"]
        for row in decisions_value.get("rows") or ()
        if isinstance(row, Mapping) and isinstance(row.get("candidate"), Mapping)
    }
    packets = {
        str(row.get("ticker") or "").upper(): DecisionEvidencePacket.model_validate(
            row["evidence_packet"]
        )
        for row in evidence_value.get("rows") or ()
        if isinstance(row, Mapping) and isinstance(row.get("evidence_packet"), Mapping)
    }
    missing = set(requested) - (set(candidates) & set(packets))
    if missing:
        raise ValueError("polarity_input_subject_missing:" + ",".join(sorted(missing)))
    args.trial_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = args.trial_dir / "polarity-prompt.txt"
    schema_path = args.trial_dir / "polarity-schema.json"
    output_path = args.trial_dir / "polarity-output.json"
    log_path = args.trial_dir / "polarity-codex.log"
    prompt = (
        """Select explicit directional evidence ownership for the supplied existing decisions.

This is a bounded semantic repair. Preserve every existing BUY/HOLD/SELL decision and all other candidate fields. Return only polarity plans. Use only exact canonical evidence ref_id values supplied for each ticker.

Hard contracts:
- buy_case_evidence: exactly one strongest genuinely BULLISH economic claim, polarity=BULLISH.
- sell_case_evidence: exactly one strongest genuinely BEARISH economic/risk claim, polarity=BEARISH.
- neutral_context_evidence: optional NEUTRAL source, identity, basis, or data-quality context.
- supporting_evidence/opposing_evidence are decision-relative and do not determine directional ownership.
- DATA_QUALITY claims must be NEUTRAL. Missing or verified data is not automatically bearish.
- TIMING_ONLY may describe price/market/flow/technical timing but cannot be the only owner of either directional side.
- Never place the same evidence ref on both directional sides.
- Every selected ref must have source lineage and as_of in the canonical packet.
- Do not invent facts, numbers, sentiment, valuation, targets, orders, or future evidence.
- For SELL, still select credible bullish optionality for the BUY side. For BUY, still select material bearish risk for the SELL side.
- Output strict JSON matching the supplied schema.

INPUTS:\n"""
        + json.dumps(
            [
                {
                    "ticker": ticker,
                    "decision": str(candidates[ticker].get("decision") or ""),
                    "evidence_sha256": packets[ticker].evidence_sha256,
                    "existing_candidate": candidates[ticker],
                    "canonical_evidence": compact_ai_context(packets[ticker]),
                }
                for ticker in requested
            ],
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )
    _write_text(prompt_path, prompt)
    _write_json(
        schema_path,
        strict_json_schema(DecisionPolarityPlanBatch.model_json_schema()),
    )
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
        CANARY_REASONING_MODEL,
        "-c",
        f'model_reasoning_effort="{CANARY_REASONING_EFFORT}"',
        "--output-schema",
        str(schema_path),
        "-o",
        str(output_path),
        "-",
    ]
    with prompt_path.open(encoding="utf-8") as stdin, log_path.open(
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
    if process.returncode != 0:
        raise RuntimeError("codex_polarity_generation_failed")
    batch = DecisionPolarityPlanBatch.model_validate(_read_json(output_path))
    plans = {plan.ticker: plan for plan in batch.plans}
    if set(plans) != set(requested):
        raise ValueError("polarity_output_subject_mismatch")
    rows: list[dict[str, object]] = []
    for ticker in requested:
        raw_candidate = candidates[ticker]
        try:
            current_candidate = DecisionCandidate.model_validate(raw_candidate)
        except ValueError:
            current_candidate = None
        if current_candidate is not None:
            enriched = apply_decision_polarity_plan(
                packets[ticker], current_candidate, plans[ticker]
            )
            candidate_payload = enriched.model_dump(mode="json")
            block_payload = render_decision_canary_block(
                packets[ticker], enriched
            ).model_dump(mode="json")
        else:
            plan = plans[ticker]
            if (
                plan.ticker != ticker
                or plan.decision != str(raw_candidate.get("decision") or "")
                or plan.evidence_sha256 != packets[ticker].evidence_sha256
            ):
                raise ValueError("legacy_polarity_plan_identity_mismatch")
            errors = polarity_claim_errors(
                packets[ticker],
                buy_case_evidence=plan.buy_case_evidence,
                sell_case_evidence=plan.sell_case_evidence,
                neutral_context_evidence=plan.neutral_context_evidence,
            )
            if errors:
                raise ValueError("legacy_polarity_plan_invalid:" + ",".join(errors))
            changes = raw_candidate.get("change_conditions") or ()
            if not isinstance(changes, list) or len(changes) < 2:
                raise ValueError("legacy_change_conditions_missing")
            confidence = {"HIGH": "높음", "MEDIUM": "중간", "LOW": "낮음"}
            timing = {
                "FAVORABLE": "우호적",
                "NEUTRAL": "중립",
                "UNFAVORABLE": "불리",
                "INSUFFICIENT": "판단 근거 부족",
            }
            lines = [
                f"🧠 AI 종합 판단: {plan.decision}",
                "추론등급: 매우 높음 | 판단 확신도: "
                + confidence[str(raw_candidate.get("confidence") or "LOW")],
                f"판단 기준: {raw_candidate.get('horizon')} | 단기 타이밍: "
                + timing[str(raw_candidate.get("timing") or "INSUFFICIENT")],
                "",
                f"🎯 판단: {raw_candidate['decisive_reason']['text']}",
                "✅ BUY 쪽 근거:",
                *(f"• {claim.text}" for claim in plan.buy_case_evidence),
                "⚠️ SELL 쪽 근거:",
                *(f"• {claim.text}" for claim in plan.sell_case_evidence),
                f"🔼 상향 조건: {changes[0]['text']}",
                f"🔽 하향 조건: {changes[1]['text']}",
                "※ 역사적 test-only 분석 분류이며 현재 판단·주문 지시가 아닙니다.",
            ]
            block_text = "\n".join(lines)
            if len(block_text) > 2200:
                raise ValueError("legacy_polarity_block_too_long")
            candidate_payload = {
                **raw_candidate,
                "buy_case_evidence": [
                    row.model_dump(mode="json") for row in plan.buy_case_evidence
                ],
                "sell_case_evidence": [
                    row.model_dump(mode="json") for row in plan.sell_case_evidence
                ],
                "neutral_context_evidence": [
                    row.model_dump(mode="json") for row in plan.neutral_context_evidence
                ],
            }
            block_payload = {
                "ticker": ticker,
                "decision": plan.decision,
                "text": block_text,
            }
        rows.append(
            {
                "ticker": ticker,
                "decision": str(raw_candidate.get("decision") or ""),
                "evidence_sha256": packets[ticker].evidence_sha256,
                "candidate": candidate_payload,
                "evidence_packet": packets[ticker].model_dump(mode="json"),
                "block": block_payload,
                "validation": {
                    "valid": True,
                    "polarity_contract": "decision-evidence-polarity-v1",
                },
            }
        )
    _write_json(
        args.output,
        {
            "contract": "decision-evidence-polarity-enrichment-v1",
            "status": "PASS",
            "reasoning_model": CANARY_REASONING_MODEL,
            "reasoning_effort": CANARY_REASONING_EFFORT,
            "rows": rows,
        },
    )
    print(json.dumps({"status": "PASS", "subjects": len(rows)}, sort_keys=True))


def _deterministic_texts(path: Path) -> dict[str, str]:
    value = _read_json(path)
    if not isinstance(value, Mapping):
        raise ValueError(f"invalid_messages:{path}")
    return {
        str(row.get("ticker") or ""): str(payload.get("text") or "")
        for row in value.get("messages") or ()
        if isinstance(row, Mapping) and isinstance((payload := row.get("payload")), Mapping)
    }


def _current_message_quality(
    text: str, *, base: str, block: str, decision: str
) -> dict[str, object]:
    required = (
        f"AI 종합 판단: {decision}",
        "추론등급: 매우 높음",
        "판단 확신도:",
        "단기 타이밍:",
        "🎯 판단:",
        "✅ BUY 쪽 근거:",
        "⚠️ SELL 쪽 근거:",
        "🔼 상향 조건:",
        "🔽 하향 조건:",
    )
    errors = [f"missing:{token}" for token in required if token not in text]
    if decision == "HOLD":
        errors.extend(
            f"missing:{token}"
            for token in ("BUY가 아닌 이유:", "SELL이 아닌 이유:")
            if token not in text
        )
    if text.replace(f"\n\n{block}", "", 1) != base:
        errors.append("existing_message_not_intact")
    if len(text) > 3500:
        errors.append("message_too_long")
    decision_part = text.replace(base, "")
    forbidden = ("시장가 매수", "전량 매도", "지금 사세요", "지금 파세요", "비중")
    if any(token in decision_part for token in forbidden):
        errors.append("order_or_sizing_language")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def _build_test(args: argparse.Namespace) -> None:
    current = _read_json(args.current)
    historical = _read_json(args.historical_buy)
    evidence = _read_json(args.historical_evidence)
    if not isinstance(current, Mapping) or current.get("status") != "PASS":
        raise ValueError("current_decisions_not_pass")
    if not isinstance(historical, Mapping) or not isinstance(evidence, Mapping):
        raise ValueError("historical_fixture_invalid")
    base = {
        **_deterministic_texts(args.kr_messages),
        **_deterministic_texts(args.us_messages),
    }
    messages: list[dict[str, object]] = []
    quality_rows: list[dict[str, object]] = []
    for row in current.get("rows") or ():
        if not isinstance(row, Mapping):
            continue
        ticker = str(row["ticker"])
        block = row.get("block")
        if not isinstance(block, Mapping) or ticker not in base:
            raise ValueError(f"current_message_input_missing:{ticker}")
        block_text = str(block["text"])
        text = insert_decision_canary_block(base[ticker], block_text)
        quality = _current_message_quality(
            text,
            base=base[ticker],
            block=block_text,
            decision=str(row["decision"]),
        )
        if quality["status"] != "PASS":
            raise ValueError(f"current_message_quality_failed:{ticker}")
        messages.append(
            {
                "ticker": ticker,
                "route": "CURRENT_PRODUCTION_EQUIVALENT_TEST_ONLY",
                "logical_identity": f"{TEST_NAMESPACE}:current:{ticker}",
                "text": text,
            }
        )
        quality_rows.append(
            {
                "ticker": ticker,
                "kind": "current",
                "status": "PASS",
                "character_count": len(text),
                "payload_sha256": _sha256_text(text),
                "price_structure_numeric_diff": 0,
            }
        )
    historical_as_of = {
        str(row.get("ticker") or ""): str(
            (row.get("evidence_packet") or {}).get("assessment_date") or ""
        )
        for row in evidence.get("rows") or ()
        if isinstance(row, Mapping) and isinstance(row.get("evidence_packet"), Mapping)
    }
    fixture_count = 0
    for row in historical.get("rows") or ():
        if not isinstance(row, Mapping) or str(row.get("ticker") or "") not in {
            "003690",
            "GOOGL",
        }:
            continue
        candidate = row.get("candidate")
        block = row.get("block")
        validation = row.get("validation")
        if not all(isinstance(value, Mapping) for value in (candidate, block, validation)):
            continue
        if candidate.get("decision") != "BUY" or validation.get("valid") is not True:
            continue
        ticker = str(row["ticker"])
        as_of = historical_as_of.get(ticker)
        if not as_of:
            raise ValueError(f"buy_fixture_as_of_missing:{ticker}")
        text = (
            "🧪 TEST FIXTURE · BUY 경로 검증\n"
            f"역사적 as_of: {as_of}\n"
            "현재 판단이나 production 상태가 아닙니다.\n\n"
            f"{block['text']}"
        )
        if len(text) > 3500 or "AI 종합 판단: BUY" not in text:
            raise ValueError(f"buy_fixture_quality_failed:{ticker}")
        messages.append(
            {
                "ticker": ticker,
                "route": "HISTORICAL_CANONICAL_BUY_FIXTURE_TEST_ONLY",
                "logical_identity": f"{TEST_NAMESPACE}:historical-buy:{ticker}:{as_of}",
                "text": text,
            }
        )
        quality_rows.append(
            {
                "ticker": ticker,
                "kind": "historical_buy_fixture",
                "status": "PASS",
                "as_of": as_of,
                "character_count": len(text),
                "payload_sha256": _sha256_text(text),
                "production_send": 0,
                "production_state_mutation": 0,
                "numeric_claim_count": validation.get("numeric_claim_count"),
                "automatic_numeric_count": validation.get("automatically_bound_numeric_count"),
            }
        )
        fixture_count += 1
    if len(messages) != 4 + fixture_count or fixture_count < 1:
        raise ValueError("test_message_count_invalid")
    identities = [str(row["logical_identity"]) for row in messages]
    if len(identities) != len(set(identities)):
        raise ValueError("duplicate_test_identity")
    _write_json(
        args.output,
        {
            "contract": CONTRACT,
            "status": "PASS",
            "namespace": TEST_NAMESPACE,
            "current_message_count": 4,
            "buy_fixture_count": fixture_count,
            "production_recipient_send_count": 0,
            "messages": messages,
            "quality": quality_rows,
        },
    )
    print(json.dumps({"status": "PASS", "messages": len(messages)}, sort_keys=True))


def _received_quality(text: str) -> Mapping[str, object]:
    if text.startswith("🧪 TEST FIXTURE · BUY 경로 검증"):
        required = (
            "역사적 as_of:",
            "AI 종합 판단: BUY",
            "현재 판단이나 production 상태가 아닙니다.",
        )
    else:
        required = ("AI 종합 판단:", "추론등급: 매우 높음", "🎯 판단:")
    errors = [f"missing:{token}" for token in required if token not in text]
    if len(text) > 3500:
        errors.append("message_too_long")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def _state_from_current(path: Path) -> DecisionCanaryState:
    value = _read_json(path)
    if not isinstance(value, Mapping) or value.get("status") != "PASS":
        raise ValueError("current_decisions_not_pass")
    timestamp = datetime.now(UTC).isoformat()
    entries: list[DecisionCanaryStateEntry] = []
    for row in value.get("rows") or ():
        if not isinstance(row, Mapping):
            continue
        evidence = DecisionEvidencePacket.model_validate(row["evidence_packet"])
        candidate = DecisionCandidate.model_validate(row["candidate"])
        entries.append(
            DecisionCanaryStateEntry(
                ticker=candidate.ticker,
                market=evidence.market,
                evidence_sha256=evidence.evidence_sha256,
                candidate=candidate,
                source_packet_id=evidence.packet_id,
                assessment_date=evidence.assessment_date,
                updated_at=timestamp,
            )
        )
    if {row.ticker for row in entries} != {*SUBJECTS["kr"], *SUBJECTS["us"]}:
        raise ValueError("state_subjects_incomplete")
    return DecisionCanaryState(
        state="canary",
        entries=tuple(sorted(entries, key=lambda row: row.ticker)),
    )


def _build_state(args: argparse.Namespace) -> None:
    state = _state_from_current(args.current)
    _write_json(args.output, state.model_dump(mode="json"))
    print(json.dumps({"status": "PASS", "entries": len(state.entries)}, sort_keys=True))


def _install_state(args: argparse.Namespace) -> None:
    settings = _canary_settings(args.env_file)
    state = _state_from_current(args.current)
    path = write_decision_canary_state(state, settings=settings)
    persisted = DecisionCanaryState.model_validate_json(path.read_text(encoding="utf-8"))
    if persisted != state:
        raise ValueError("installed_state_mismatch")
    print(json.dumps({"status": "PASS", "entries": len(state.entries)}, sort_keys=True))


async def _send_test(args: argparse.Namespace) -> None:
    value = _read_json(args.messages)
    if not isinstance(value, Mapping) or value.get("status") != "PASS":
        raise ValueError("preenable_messages_not_pass")
    messages = [row for row in value.get("messages") or () if isinstance(row, Mapping)]
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
        contract="cross-market-decision-bounded-canary-test-sink-v1",
        namespace=TEST_NAMESPACE,
        received_payload_validator=_received_quality,
    )
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "sent_message_count": receipt["sent_message_count"],
                "exact_payload_match": receipt["exact_payload_match"],
                "production_recipient_send_count": receipt["production_recipient_send_count"],
            },
            sort_keys=True,
        )
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--env-file", type=Path, required=True)
    prepare.add_argument("--kr-packet", type=Path, required=True)
    prepare.add_argument("--us-packet", type=Path, required=True)
    prepare.add_argument("--trial-dir", type=Path, required=True)
    prepare.add_argument("--evidence-output", type=Path, required=True)

    run = sub.add_parser("run")
    run.add_argument("--trial-dir", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument(
        "--codex-bin",
        type=Path,
        default=Path("/Applications/ChatGPT.app/Contents/Resources/codex"),
    )
    run.add_argument("--timeout", type=int, default=900)

    continuity = sub.add_parser("apply-continuity")
    continuity.add_argument("--env-file", type=Path, required=True)
    continuity.add_argument("--kr-packet", type=Path, required=True)
    continuity.add_argument("--us-packet", type=Path, required=True)
    continuity.add_argument("--evidence", type=Path, required=True)
    continuity.add_argument("--continuity-decisions", type=Path, required=True)
    continuity.add_argument("--trial-dir", type=Path, required=True)

    polarity = sub.add_parser("enrich-polarity")
    polarity.add_argument("--decisions", type=Path, required=True)
    polarity.add_argument("--evidence", type=Path, required=True)
    polarity.add_argument("--tickers", required=True)
    polarity.add_argument("--trial-dir", type=Path, required=True)
    polarity.add_argument("--output", type=Path, required=True)
    polarity.add_argument(
        "--codex-bin",
        type=Path,
        default=Path("/Applications/ChatGPT.app/Contents/Resources/codex"),
    )
    polarity.add_argument("--timeout", type=int, default=900)

    build_test = sub.add_parser("build-test")
    build_test.add_argument("--current", type=Path, required=True)
    build_test.add_argument("--kr-messages", type=Path, required=True)
    build_test.add_argument("--us-messages", type=Path, required=True)
    build_test.add_argument("--historical-buy", type=Path, required=True)
    build_test.add_argument("--historical-evidence", type=Path, required=True)
    build_test.add_argument("--output", type=Path, required=True)

    send_test = sub.add_parser("send-test")
    send_test.add_argument("--env-file", type=Path, required=True)
    send_test.add_argument("--messages", type=Path, required=True)
    send_test.add_argument("--receipt", type=Path, required=True)

    build_state = sub.add_parser("build-state")
    build_state.add_argument("--current", type=Path, required=True)
    build_state.add_argument("--output", type=Path, required=True)

    install_state = sub.add_parser("install-state")
    install_state.add_argument("--env-file", type=Path, required=True)
    install_state.add_argument("--current", type=Path, required=True)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "prepare":
        asyncio.run(_prepare(args))
    elif args.command == "run":
        _run(args)
    elif args.command == "apply-continuity":
        _apply_continuity(args)
    elif args.command == "enrich-polarity":
        _enrich_polarity(args)
    elif args.command == "build-test":
        _build_test(args)
    elif args.command == "send-test":
        asyncio.run(_send_test(args))
    elif args.command == "build-state":
        _build_state(args)
    else:
        _install_state(args)


if __name__ == "__main__":
    main()
