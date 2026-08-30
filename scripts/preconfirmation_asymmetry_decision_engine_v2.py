from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import subprocess
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal

from pydantic import Field

from app.services.cross_market_decision_engine_service import (
    Decision,
    DecisionEvidencePacket,
    EvidenceClaim,
    FrozenModel,
    compact_ai_context,
)
from app.services.preconfirmation_decision_v2_service import (
    PreconfirmationDecisionBatch,
    PreconfirmationDecisionCandidate,
    candidate_claims,
    preconfirmation_message_quality,
    render_preconfirmation_shadow,
    validate_preconfirmation_candidate,
)
from scripts.kr_final_preenable_test_delivery import deliver_test_messages
from scripts.kr_market_preenable_evidence import audit_test_sink, load_env_values


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs/reports"
MODEL = "gpt-5.6-sol"
REASONING_EFFORT = "xhigh"
TEST_NAMESPACE = "PRECONFIRMATION_ASYMMETRY_V2_SHADOW_TEST_ONLY"


class V2Adjudication(FrozenModel):
    ticker: str
    v1_decision: Decision
    v2_decision: Decision
    accepted_decision: Decision
    recommendation: Literal["KEEP_V1", "KEEP_V2", "NEEDS_REPAIR"]
    v1_overrequired_confirmation: Literal["YES", "NO", "UNCERTAIN"]
    v2_underweighted_execution_risk: Literal["YES", "NO", "UNCERTAIN"]
    v1_ignored_confirmation_cost: Literal["YES", "NO", "UNCERTAIN"]
    v2_overstated_favorable_asymmetry: Literal["YES", "NO", "UNCERTAIN"]
    valuation_or_expectation_misuse: Literal["V1", "V2", "BOTH", "NEITHER", "UNCERTAIN"]
    data_quality_comparison_safe: bool
    decisive_basis: EvidenceClaim
    bounded_repair: str = Field(min_length=2, max_length=300)


class V2AdjudicationBatch(FrozenModel):
    contract: Literal["preconfirmation-v2-adjudication-output-v1"]
    adjudications: tuple[V2Adjudication, ...]


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
            key: _strict_json_schema(item) for key, item in value.items() if key != "default"
        }
        properties = transformed.get("properties")
        if isinstance(properties, dict):
            transformed["required"] = list(properties)
            transformed["additionalProperties"] = False
        return transformed
    if isinstance(value, list):
        return [_strict_json_schema(item) for item in value]
    return value


def _evidence_rows(value: Mapping[str, object]) -> list[Mapping[str, object]]:
    return [row for row in value.get("rows") or () if isinstance(row, Mapping)]


def _baseline_rows(value: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    return {
        str(row["ticker"]): row
        for row in value.get("rows") or ()
        if isinstance(row, Mapping) and row.get("ticker")
    }


def _prompt(contexts: Sequence[Mapping[str, object]]) -> str:
    return """You are the sole owner of a label-blind SHADOW-v2 analytical BUY/HOLD/SELL review. The v1 labels are intentionally absent. Use only the supplied canonical evidence. No web, tools, outside knowledge, future outcome, hidden calculation, fixed score, or class-balance target.

Core question: how much business uncertainty remains, how much the market already prices, and whether risk/reward is attractive before full confirmation. Full confirmation is not required for BUY. Confirmed evidence is not sufficient for BUY when pricing requires an optimistic or bull case.

Hard factual safety is different from investment uncertainty. Security/share/ADR basis conflict, currency conflict, unverified denominator, malformed data, future leakage, and provenance failure must fail closed. If factual_safety_state is BLOCKED, pricing_requirement and asymmetry must be UNKNOWN and pre_confirmation_buy must be false.

For each stock:
- classify 1-6 company-specific core drivers as EARLY/PARTIAL/CONFIRMED/MIXED/UNKNOWN; identify decisive drivers and what remains unproven;
- preserve the market-expectation enum exactly: depressed/low/balanced/elevated/very_high/speculative/unknown;
- classify pricing requirement and expose valuation, expectation, assumption, and unknown evidence;
- create evidence-bound BEAR/BASE/BULL interpretations without target prices or invented forecasts;
- assess asymmetry, confirmation cost, and preconfirmation error cost independently, without weights or deterministic mapping;
- let fundamentals own long-horizon asymmetry; technical/market facts may affect timing only unless economically linked;
- set pre_confirmation_buy=true only for BUY with a decisive EARLY/PARTIAL driver and include every required explanation field;
- set post_confirmation_hold=true only for HOLD with overall CONFIRMED maturity because the price also rerated;
- state why not BUY and why not SELL even for directional decisions, plus genuine opposing evidence and asymmetric observable change conditions;
- use VERY_HIGH reasoning_grade, but calibrate confidence independently;
- every claim and maturity ref must copy exact complete ref_id values from the same ticker;
- all prose fields must be concise natural Korean analytical conclusions;
- do not put exact numeric values, target/fair values, FCF yield/per-share, EV/FCF, ROIC, CCC, DSO, DPO, runway months, order language, or position sizing in prose;
- do not repeat an identical substantive sentence across companies;
- output only strict JSON matching the schema.

CANONICAL_EVIDENCE_PACKETS:
""" + json.dumps(contexts, ensure_ascii=False, separators=(",", ":"), default=str)


def _prepare(args: argparse.Namespace) -> None:
    evidence = _read_json(args.evidence)
    if not isinstance(evidence, Mapping):
        raise ValueError("invalid_evidence")
    rows = _evidence_rows(evidence)
    if len(rows) != 20 or len({str(row.get("ticker")) for row in rows}) != 20:
        raise ValueError("active_universe_not_20_unique_subjects")
    if args.tickers:
        requested = set(args.tickers)
        rows = [row for row in rows if str(row.get("ticker")) in requested]
        if {str(row.get("ticker")) for row in rows} != requested:
            raise ValueError("requested_ticker_not_in_universe")
    args.trial_dir.mkdir(parents=True, exist_ok=True)
    schema = args.trial_dir / "output.schema.json"
    _write_json(schema, _strict_json_schema(PreconfirmationDecisionBatch.model_json_schema()))
    entries: list[dict[str, object]] = []
    for index in range(0, len(rows), args.batch_size):
        batch = rows[index : index + args.batch_size]
        contexts = [
            compact_ai_context(DecisionEvidencePacket.model_validate(row["evidence_packet"]))
            for row in batch
        ]
        name = f"v2-shadow-{index // args.batch_size + 1:02d}"
        prompt_path = args.trial_dir / f"{name}.prompt.txt"
        _write_text(prompt_path, _prompt(contexts))
        entries.append(
            {
                "name": name,
                "tickers": [str(row["ticker"]) for row in batch],
                "prompt": prompt_path.name,
                "output": f"{name}.output.json",
                "log": f"{name}.log",
            }
        )
    _write_json(
        args.trial_dir / "manifest.json",
        {
            "contract": "preconfirmation-v2-shadow-manifest-v1",
            "label_blind": True,
            "source_evidence": str(args.evidence),
            "source_evidence_sha256": _sha256(args.evidence),
            "schema": schema.name,
            "runtime_config": {
                "route": "signed_in_local_codex_cli_archive_only",
                "model": MODEL,
                "provider_supported_reasoning_effort": REASONING_EFFORT,
                "sandbox": "read-only",
                "session": "ephemeral",
                "tools": "prohibited_by_prompt",
            },
            "entries": entries,
        },
    )
    print(json.dumps({"calls": len(entries), "label_blind": True}, sort_keys=True))


def _run(args: argparse.Namespace) -> None:
    manifest = _read_json(args.trial_dir / "manifest.json")
    if not isinstance(manifest, dict):
        raise ValueError("invalid_manifest")
    version = subprocess.run(
        [str(args.codex_bin), "--version"], capture_output=True, check=False, text=True
    )
    runtime = manifest.get("runtime_config")
    if isinstance(runtime, dict):
        runtime["cli_version"] = version.stdout.strip() or "unavailable"
    _write_json(args.trial_dir / "manifest.json", manifest)
    completed = failed = skipped = 0
    entries = [row for row in manifest.get("entries") or () if isinstance(row, Mapping)]
    for index, entry in enumerate(entries, 1):
        output = args.trial_dir / str(entry["output"])
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
            MODEL,
            "-c",
            'model_reasoning_effort="xhigh"',
            "--output-schema",
            str(args.trial_dir / str(manifest["schema"])),
            "-o",
            str(output),
            "-",
        ]
        prompt = args.trial_dir / str(entry["prompt"])
        log = args.trial_dir / str(entry["log"])
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
                    text=True,
                    timeout=args.timeout,
                    check=False,
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
    print(json.dumps({"completed": completed, "failed": failed, "skipped": skipped}))


def _finalize(args: argparse.Namespace) -> None:
    evidence = _read_json(args.evidence)
    baseline = _read_json(args.baseline)
    manifest = _read_json(args.trial_dir / "manifest.json")
    if not all(isinstance(value, Mapping) for value in (evidence, baseline, manifest)):
        raise ValueError("invalid_finalize_input")
    assert isinstance(evidence, Mapping)
    assert isinstance(baseline, Mapping)
    assert isinstance(manifest, Mapping)
    packets = {
        str(row["ticker"]): DecisionEvidencePacket.model_validate(row["evidence_packet"])
        for row in _evidence_rows(evidence)
    }
    baseline_by_ticker = _baseline_rows(baseline)
    candidates: dict[str, PreconfirmationDecisionCandidate] = {}
    parse_errors: list[str] = []
    for entry in manifest.get("entries") or ():
        if not isinstance(entry, Mapping):
            continue
        path = args.trial_dir / str(entry["output"])
        try:
            output = PreconfirmationDecisionBatch.model_validate(_read_json(path))
        except Exception as exc:
            parse_errors.append(f"{entry.get('name')}:{type(exc).__name__}:{exc}")
            continue
        for row in output.decisions:
            if row.ticker in candidates:
                parse_errors.append(f"duplicate_candidate:{row.ticker}")
            candidates[row.ticker] = row
    expected = set(packets)
    if set(candidates) != expected:
        parse_errors.append(
            "subject_set_mismatch:missing="
            + ",".join(sorted(expected - set(candidates)))
            + ":extra="
            + ",".join(sorted(set(candidates) - expected))
        )
    rows: list[dict[str, object]] = []
    rendered = []
    validation_errors: list[str] = []
    for ticker, packet in packets.items():
        candidate = candidates.get(ticker)
        if candidate is None:
            continue
        validation = validate_preconfirmation_candidate(packet, candidate)
        if not validation.valid:
            validation_errors.extend(f"{ticker}:{error}" for error in validation.errors)
            rendered_row = None
        else:
            rendered_row = render_preconfirmation_shadow(packet, candidate)
            rendered.append(rendered_row)
        baseline_row = baseline_by_ticker.get(ticker) or {}
        baseline_candidate = baseline_row.get("candidate")
        v1_decision = (
            str(baseline_candidate.get("decision"))
            if isinstance(baseline_candidate, Mapping)
            else "UNKNOWN"
        )
        rows.append(
            {
                "ticker": ticker,
                "company_name": packet.company_name,
                "market": packet.market,
                "evidence_sha256": packet.evidence_sha256,
                "v1_decision": v1_decision,
                "v2_decision": candidate.decision,
                "decision_agreement": v1_decision == candidate.decision,
                "material_disagreement": v1_decision != candidate.decision,
                "candidate": candidate.model_dump(mode="json"),
                "validation": validation.model_dump(mode="json"),
                "rendered": rendered_row.model_dump(mode="json") if rendered_row else None,
                "status": "PASS" if validation.valid else "FAIL",
            }
        )
    quality = preconfirmation_message_quality(tuple(rendered))
    counts = Counter(row["v2_decision"] for row in rows)
    status = (
        "PASS"
        if not parse_errors
        and not validation_errors
        and len(rows) == 20
        and quality["status"] == "PASS"
        else "FAIL"
    )
    result = {
        "contract": "preconfirmation-asymmetry-shadow-v2",
        "status": status,
        "subject_count": len(rows),
        "source_evidence_sha256": _sha256(args.evidence),
        "source_baseline_sha256": _sha256(args.baseline),
        "label_blind": bool(manifest.get("label_blind")),
        "ai_runtime": manifest.get("runtime_config"),
        "decision_distribution": {
            decision: counts.get(decision, 0) for decision in ("BUY", "HOLD", "SELL")
        },
        "preconfirmation_buy_count": sum(
            bool((row["candidate"] or {}).get("pre_confirmation_buy")) for row in rows
        ),
        "postconfirmation_hold_count": sum(
            bool((row["candidate"] or {}).get("post_confirmation_hold")) for row in rows
        ),
        "material_disagreement_count": sum(
            bool(row["material_disagreement"]) for row in rows
        ),
        "parse_errors": parse_errors,
        "validation_errors": validation_errors,
        "message_quality": quality,
        "production_packet_changed": False,
        "production_canary_state_mutated": False,
        "production_delivery_intent_created": 0,
        "rows": rows,
    }
    _write_json(args.output, result)
    print(
        json.dumps(
            {
                "status": status,
                "subjects": len(rows),
                "distribution": result["decision_distribution"],
                "material_disagreements": result["material_disagreement_count"],
            },
            sort_keys=True,
        )
    )


def _adjudication_prompt(rows: Sequence[Mapping[str, object]]) -> str:
    return """Adjudicate only the listed material v1/v2 decision disagreements after the label-blind v2 pass is complete. Use the frozen v1 candidate, validated v2 candidate, and same canonical evidence excerpts. No web, future outcomes, scores, target prices, new numerics, or majority voting.

For every row answer whether v1 over-required confirmation, v2 underweighted execution risk, v1 ignored confirmation cost, v2 overstated favorable asymmetry, either side misused valuation/expectations, and whether data quality permits comparison. KEEP_V1 or KEEP_V2 means that side is better supported by the shared packet. NEEDS_REPAIR means a material product-contract problem remains. accepted_decision must be a supplied v1 or v2 decision. decisive_basis must be concise Korean and cite exact refs. bounded_repair must be NONE when no repair remains. Output only strict JSON.

MATERIAL_DISAGREEMENTS:
""" + json.dumps(rows, ensure_ascii=False, separators=(",", ":"), default=str)


def _prepare_adjudication(args: argparse.Namespace) -> None:
    evidence = _read_json(args.evidence)
    baseline = _read_json(args.baseline)
    shadow = _read_json(args.shadow)
    if not all(isinstance(value, Mapping) for value in (evidence, baseline, shadow)):
        raise ValueError("invalid_adjudication_input")
    assert isinstance(evidence, Mapping)
    assert isinstance(baseline, Mapping)
    assert isinstance(shadow, Mapping)
    packet_rows = {str(row["ticker"]): row for row in _evidence_rows(evidence)}
    baseline_rows = _baseline_rows(baseline)
    disagreements = [
        row
        for row in shadow.get("rows") or ()
        if isinstance(row, Mapping) and row.get("material_disagreement") is True
    ]
    args.trial_dir.mkdir(parents=True, exist_ok=True)
    schema = args.trial_dir / "output.schema.json"
    _write_json(schema, _strict_json_schema(V2AdjudicationBatch.model_json_schema()))
    entries: list[dict[str, object]] = []
    for index in range(0, len(disagreements), args.batch_size):
        batch = disagreements[index : index + args.batch_size]
        contexts = []
        for row in batch:
            ticker = str(row["ticker"])
            packet = DecisionEvidencePacket.model_validate(packet_rows[ticker]["evidence_packet"])
            candidate = PreconfirmationDecisionCandidate.model_validate(row["candidate"])
            wanted = {
                ref_id for claim in candidate_claims(candidate) for ref_id in claim.evidence_refs
            }
            baseline_candidate = baseline_rows[ticker].get("candidate")
            if isinstance(baseline_candidate, Mapping):
                for key in ("decisive_reason", "why_not_buy", "why_not_sell"):
                    claim = baseline_candidate.get(key)
                    if isinstance(claim, Mapping):
                        wanted.update(str(ref) for ref in claim.get("evidence_refs") or ())
            contexts.append(
                {
                    "ticker": ticker,
                    "v1_candidate": baseline_candidate,
                    "v2_candidate": row["candidate"],
                    "evidence": [
                        {
                            "ref_id": ref.ref_id,
                            "category": ref.category,
                            "label": ref.label,
                            "statement": ref.statement,
                        }
                        for ref in packet.evidence
                        if ref.ref_id in wanted
                    ],
                }
            )
        name = f"v2-adjudication-{index // args.batch_size + 1:02d}"
        prompt = args.trial_dir / f"{name}.prompt.txt"
        _write_text(prompt, _adjudication_prompt(contexts))
        entries.append(
            {
                "name": name,
                "tickers": [str(row["ticker"]) for row in batch],
                "prompt": prompt.name,
                "output": f"{name}.output.json",
                "log": f"{name}.log",
            }
        )
    _write_json(
        args.trial_dir / "manifest.json",
        {
            "contract": "preconfirmation-v2-adjudication-manifest-v1",
            "source_sha256": _sha256(args.shadow),
            "schema": schema.name,
            "runtime_config": {
                "route": "signed_in_local_codex_cli_archive_only",
                "model": MODEL,
                "provider_supported_reasoning_effort": REASONING_EFFORT,
                "sandbox": "read-only",
                "session": "ephemeral",
                "tools": "prohibited_by_prompt",
            },
            "entries": entries,
        },
    )
    print(json.dumps({"material_disagreements": len(disagreements), "calls": len(entries)}))


def _finalize_adjudication(args: argparse.Namespace) -> None:
    evidence = _read_json(args.evidence)
    shadow = _read_json(args.shadow)
    manifest = _read_json(args.trial_dir / "manifest.json")
    if not all(isinstance(value, Mapping) for value in (evidence, shadow, manifest)):
        raise ValueError("invalid_adjudication_finalize_input")
    assert isinstance(evidence, Mapping)
    assert isinstance(shadow, Mapping)
    assert isinstance(manifest, Mapping)
    packets = {
        str(row["ticker"]): DecisionEvidencePacket.model_validate(row["evidence_packet"])
        for row in _evidence_rows(evidence)
    }
    expected = {
        str(row["ticker"])
        for row in shadow.get("rows") or ()
        if isinstance(row, Mapping) and row.get("material_disagreement") is True
    }
    shadow_rows = {
        str(row["ticker"]): row
        for row in shadow.get("rows") or ()
        if isinstance(row, Mapping) and row.get("ticker")
    }
    rows: list[dict[str, object]] = []
    errors: list[str] = []
    for entry in manifest.get("entries") or ():
        if not isinstance(entry, Mapping):
            continue
        try:
            batch = V2AdjudicationBatch.model_validate(
                _read_json(args.trial_dir / str(entry["output"]))
            )
        except Exception as exc:
            errors.append(f"{entry.get('name')}:{type(exc).__name__}:{exc}")
            continue
        for row in batch.adjudications:
            packet = packets.get(row.ticker)
            source = shadow_rows.get(row.ticker) or {}
            allowed_decisions = {str(source.get("v1_decision")), str(source.get("v2_decision"))}
            if packet is None:
                errors.append(f"unknown_ticker:{row.ticker}")
                continue
            allowed_refs = {ref.ref_id for ref in packet.evidence}
            for ref_id in row.decisive_basis.evidence_refs:
                if ref_id not in allowed_refs:
                    errors.append(f"{row.ticker}:unknown_ref:{ref_id}")
            if row.accepted_decision not in allowed_decisions:
                errors.append(f"{row.ticker}:accepted_decision_not_supplied")
            if row.recommendation == "NEEDS_REPAIR" and row.bounded_repair == "NONE":
                errors.append(f"{row.ticker}:repair_missing")
            rows.append(row.model_dump(mode="json"))
    tickers = [str(row["ticker"]) for row in rows]
    if set(tickers) != expected or len(tickers) != len(set(tickers)):
        errors.append("adjudication_subject_set_mismatch")
    result = {
        "contract": "preconfirmation-v2-material-disagreement-adjudication-v1",
        "status": "PASS" if not errors else "FAIL",
        "material_disagreement_count": len(expected),
        "adjudication_count": len(rows),
        "open_material_p1": [
            f"{row['ticker']}:{row['bounded_repair']}"
            for row in rows
            if row["recommendation"] == "NEEDS_REPAIR"
        ],
        "errors": errors,
        "rows": rows,
    }
    _write_json(args.output, result)
    print(json.dumps({"status": result["status"], "adjudications": len(rows)}))


def _historical_diagnostic(args: argparse.Namespace) -> None:
    temporal = _read_json(args.temporal)
    if not isinstance(temporal, Mapping):
        raise ValueError("invalid_temporal_replay")
    leak = int(temporal.get("historical_replay_lookahead_leak") or 0)
    outcome = str(temporal.get("outcome_diagnostics") or "NOT_AVAILABLE")
    available = outcome not in {"SUPPRESSED_SOURCE_NOT_ARCHIVED", "NOT_AVAILABLE"}
    result = {
        "contract": "confirmation-delay-historical-diagnostic-v2",
        "status": "PARTIAL_SAFE" if not leak else "FAIL",
        "source_contract": temporal.get("contract"),
        "subject_count": temporal.get("subject_count"),
        "checkpoint_count": temporal.get("checkpoint_count"),
        "historical_replay_lookahead_leak": leak,
        "future_outcome_entered_decision_packet": 0,
        "confirmation_delay_price_change": "NOT_AVAILABLE" if not available else outcome,
        "earnings_fcf_roic_estimate_change": "NOT_AVAILABLE",
        "expectation_valuation_rerating": "NOT_AVAILABLE",
        "reason": (
            "canonical_forward_outcomes_and_point_in_time_estimate_series_not_archived"
            if not available
            else "available_source_requires_separate_review"
        ),
        "presented_as_validated_alpha": 0,
        "decision": "DIAGNOSTIC_ONLY_NO_ALPHA_CLAIM",
    }
    _write_json(args.output, result)
    print(json.dumps({"status": result["status"], "lookahead": leak}))


def _received_quality(text: str) -> Mapping[str, object]:
    required = (
        "🧪 SHADOW V2 · 비대칭/증거성숙도 검증",
        "AI 종합 판단:",
        "증거 성숙도:",
        "가격 비대칭:",
        "🎯 판단",
        "🔄 판단 변경 조건",
    )
    errors = [f"missing:{token}" for token in required if token not in text]
    if len(text) > 3500:
        errors.append("message_too_long")
    if re.search(r"목표가|적정가|시장가\s*(?:매수|매도)", text):
        errors.append("forbidden_language")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


async def _send_test(args: argparse.Namespace) -> None:
    shadow = _read_json(args.shadow)
    if not isinstance(shadow, Mapping) or shadow.get("status") != "PASS":
        raise ValueError("shadow_not_pass")
    rows = [row for row in shadow.get("rows") or () if isinstance(row, Mapping)]
    if len(rows) != 20 or any(row.get("status") != "PASS" for row in rows):
        raise ValueError("all_20_shadow_rows_must_pass")
    messages = [
        {
            "ticker": str(row["ticker"]),
            "route": "SHADOW_V2_TEST_ONLY",
            "logical_identity": f"{args.namespace}:{row['ticker']}",
            "text": str((row.get("rendered") or {}).get("text") or ""),
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
        contract="preconfirmation-asymmetry-v2-test-sink-v1",
        namespace=args.namespace,
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
    prepare.add_argument("--evidence", type=Path, required=True)
    prepare.add_argument("--trial-dir", type=Path, required=True)
    prepare.add_argument("--batch-size", type=int, default=2)
    prepare.add_argument("--tickers", nargs="*")
    run = sub.add_parser("run")
    run.add_argument("--trial-dir", type=Path, required=True)
    run.add_argument(
        "--codex-bin",
        type=Path,
        default=Path("/Applications/ChatGPT.app/Contents/Resources/codex"),
    )
    run.add_argument("--timeout", type=int, default=1800)
    finalize = sub.add_parser("finalize")
    finalize.add_argument("--evidence", type=Path, required=True)
    finalize.add_argument("--baseline", type=Path, required=True)
    finalize.add_argument("--trial-dir", type=Path, required=True)
    finalize.add_argument("--output", type=Path, required=True)
    adjudicate = sub.add_parser("prepare-adjudication")
    adjudicate.add_argument("--evidence", type=Path, required=True)
    adjudicate.add_argument("--baseline", type=Path, required=True)
    adjudicate.add_argument("--shadow", type=Path, required=True)
    adjudicate.add_argument("--trial-dir", type=Path, required=True)
    adjudicate.add_argument("--batch-size", type=int, default=2)
    finalize_adjudication = sub.add_parser("finalize-adjudication")
    finalize_adjudication.add_argument("--evidence", type=Path, required=True)
    finalize_adjudication.add_argument("--shadow", type=Path, required=True)
    finalize_adjudication.add_argument("--trial-dir", type=Path, required=True)
    finalize_adjudication.add_argument("--output", type=Path, required=True)
    historical = sub.add_parser("historical-diagnostic")
    historical.add_argument("--temporal", type=Path, required=True)
    historical.add_argument("--output", type=Path, required=True)
    send = sub.add_parser("send-test")
    send.add_argument("--env-file", type=Path, required=True)
    send.add_argument("--shadow", type=Path, required=True)
    send.add_argument("--receipt", type=Path, required=True)
    send.add_argument("--namespace", default=TEST_NAMESPACE)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "prepare":
        _prepare(args)
    elif args.command == "run":
        _run(args)
    elif args.command == "finalize":
        _finalize(args)
    elif args.command == "prepare-adjudication":
        _prepare_adjudication(args)
    elif args.command == "finalize-adjudication":
        _finalize_adjudication(args)
    elif args.command == "historical-diagnostic":
        _historical_diagnostic(args)
    elif args.command == "send-test":
        asyncio.run(_send_test(args))


if __name__ == "__main__":
    main()
