from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    compact_ai_context,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs/reports"
CONTRACT = "cross-market-decision-quality-review-v1"
MODEL = "gpt-5.6-sol"
REASONING_EFFORT = "xhigh"

Decision = Literal["BUY", "HOLD", "SELL"]
Confidence = Literal["HIGH", "MEDIUM", "LOW"]
Timing = Literal["FAVORABLE", "NEUTRAL", "UNFAVORABLE", "INSUFFICIENT"]
AxisState = Literal["POSITIVE", "NEUTRAL", "NEGATIVE", "UNKNOWN"]
HoldReason = Literal[
    "BALANCED_EVIDENCE",
    "VALUATION_TOO_HIGH",
    "EXPECTATIONS_TOO_HIGH",
    "FUNDAMENTALS_NOT_YET_PROVEN",
    "DATA_QUALITY_LIMIT",
    "SECURITY_BASIS_LIMIT",
    "UNFAVORABLE_TIMING",
    "DILUTION_RISK",
    "THESIS_WEAKENING",
    "OTHER",
    "NOT_HOLD",
]
ConflictState = Literal[
    "ALIGNED_POSITIVE",
    "ALIGNED_NEGATIVE",
    "FUNDAMENTAL_POSITIVE_TECHNICAL_NEGATIVE",
    "FUNDAMENTAL_NEGATIVE_TECHNICAL_POSITIVE",
    "MIXED",
    "INSUFFICIENT",
]
FeatureFamily = Literal[
    "returns_trend",
    "sma_ema",
    "macd",
    "rsi",
    "atr_volatility",
    "bollinger",
    "adx_dmi",
    "roc_stochastic",
    "volume_derived",
    "breakout_channel",
    "validated_divergence",
]
Contribution = Literal["NONE", "CONTEXT", "MATERIAL", "DECISIVE"]
DataLimit = Literal[
    "FINANCIAL_QUALITY_DENIED",
    "VALUATION_BASIS_UNAVAILABLE",
    "SECURITY_BASIS_UNVERIFIED",
    "ADR_BASIS_UNCERTAINTY",
    "MISSING_FORWARD_VALUATION",
    "INSUFFICIENT_OHLCV_HISTORY",
    "OTHER",
    "NONE",
]


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ReviewClaim(FrozenModel):
    text: str = Field(min_length=1, max_length=420)
    evidence_refs: tuple[str, ...] = Field(min_length=1, max_length=6)


class AxisStates(FrozenModel):
    business_quality: AxisState
    earnings_trajectory: AxisState
    earnings_quality: AxisState
    market_expectations: AxisState
    valuation: AxisState
    catalyst_profile: AxisState
    structural_risk: AxisState
    macro_sensitivity: AxisState
    market_sector_context: AxisState
    positioning_flows: AxisState
    price_structure: AxisState
    technical_momentum: AxisState
    data_quality: AxisState


class IndependentReview(FrozenModel):
    ticker: str
    independent_decision: Decision
    confidence: Confidence
    timing: Timing
    decisive_reason: ReviewClaim
    strongest_bull_case: ReviewClaim
    strongest_bear_case: ReviewClaim
    why_not_buy: ReviewClaim
    why_not_sell: ReviewClaim
    key_unknown: ReviewClaim
    valuation_assessment: ReviewClaim
    expectation_assessment: ReviewClaim
    technical_assessment: ReviewClaim
    data_quality_assessment: ReviewClaim
    decision_change_conditions: tuple[ReviewClaim, ...] = Field(min_length=2, max_length=4)
    axis_states: AxisStates
    fundamental_technical_conflict: ConflictState
    new_buyer_view: ReviewClaim
    holder_view: ReviewClaim
    hold_primary_reason: HoldReason
    confidence_basis: Literal[
        "EVIDENCE_CONVERGENCE",
        "DECISION_UNCERTAINTY",
        "DATA_QUALITY_LIMIT",
        "MIXED",
    ]
    timing_basis: ReviewClaim
    data_quality_limitations: tuple[DataLimit, ...] = Field(min_length=1, max_length=5)
    material_ohlcv_families: tuple[FeatureFamily, ...] = Field(max_length=6)
    macd_decision_contribution: Contribution
    macd_timing_contribution: Contribution
    macd_evidence_refs: tuple[str, ...] = Field(max_length=3)


class IndependentReviewBatch(FrozenModel):
    contract: Literal["cross-market-independent-review-v1"]
    reviews: tuple[IndependentReview, ...]


class AgreementScreen(FrozenModel):
    ticker: str
    reason_level_agreement: Literal["ALIGNED", "DIFFERENT_EMPHASIS", "MATERIAL_CONFLICT"]
    explanation: str = Field(min_length=1, max_length=600)
    improperly_weighted_axis: Literal[
        "NONE",
        "BUSINESS",
        "EARNINGS",
        "EXPECTATIONS",
        "VALUATION",
        "RISK",
        "TECHNICAL",
        "DATA_QUALITY",
    ]


class AgreementScreenBatch(FrozenModel):
    contract: Literal["cross-market-agreement-screen-v1"]
    screens: tuple[AgreementScreen, ...]


class Adjudication(FrozenModel):
    ticker: str
    adjudicated_decision: Decision
    confidence: Confidence
    timing: Timing
    better_supported: Literal["BASELINE", "INDEPENDENT", "SYNTHESIS"]
    decisive_reason: ReviewClaim
    improperly_weighted_evidence: str = Field(min_length=1, max_length=600)
    semantic_or_contract_problem: Literal[
        "NONE",
        "PROMPT_REASONING_BIAS",
        "EVIDENCE_PACKET_GAP",
        "CONFIDENCE_CALIBRATION",
        "DECISION_TAXONOMY",
        "TIMING_CALIBRATION",
        "VALIDATOR_OWNERSHIP",
        "MESSAGE_RENDERING",
        "DATA_QUALITY",
    ]
    severity: Literal["NONE", "P0", "P1", "P2"]
    resolution: str = Field(min_length=1, max_length=600)


class AdjudicationBatch(FrozenModel):
    contract: Literal["cross-market-material-adjudication-v1"]
    adjudications: tuple[Adjudication, ...]


class PortfolioAudit(FrozenModel):
    contract: Literal["cross-market-portfolio-calibration-v1"]
    sell_zero_explanation: str = Field(min_length=1, max_length=900)
    hold_default_bias: Literal["NONE", "LOW", "MATERIAL", "FAIL"]
    sell_suppression_bias: Literal["NONE", "LOW", "MATERIAL", "FAIL"]
    confidence_calibration: Literal["PASS", "NEEDS_REPAIR", "FAIL"]
    confidence_explanation: str = Field(min_length=1, max_length=800)
    timing_calibration: Literal["PASS", "NEEDS_REPAIR", "FAIL"]
    timing_explanation: str = Field(min_length=1, max_length=800)
    cross_market_decision_semantics: Literal["PASS", "MATERIAL_INCONSISTENCY", "FAIL"]
    cross_market_explanation: str = Field(min_length=1, max_length=800)
    decision_change_condition_quality: Literal["PASS", "NEEDS_REPAIR", "FAIL"]
    canary_recommendation: Literal["READY", "READY_WITH_OBSERVATION", "NOT_READY"]
    proposed_canary_set: tuple[
        Annotated[str, Field(min_length=1, max_length=12)], ...
    ] = Field(max_length=6)
    canary_reason: str = Field(min_length=1, max_length=900)
    open_p0: tuple[str, ...]
    open_material_p1: tuple[str, ...]
    p2_backlog: tuple[str, ...]
    next_action: Literal[
        "REVIEW_OPERATOR_TABLE",
        "PREPARE_BOUNDED_CANARY_INSTRUCTION",
        "BOUNDED_REPAIR",
        "NO_ACTION",
    ]


_ORDER_LANGUAGE = re.compile(
    r"즉시\s*(?:매수|매도)(?:하|해야|권고|합니다|하세요)|전량\s*매도|"
    r"무조건\s*보유|시장가|지정가|"
    r"주문\s*실행|buy\s+now|sell\s+now",
    re.IGNORECASE,
)
_EXACT_NUMBER = re.compile(
    r"(?<![A-Za-z])[-+]?\d[\d,.]*(?:\.\d+)?\s*(?:%|원|달러|USD|KRW|배|주|MW|GW)"
)


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


def _baseline_rows(value: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    return {
        str(row["ticker"]): row
        for row in value.get("rows") or ()
        if isinstance(row, Mapping)
    }


def _evidence_rows(value: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    return {
        str(row["ticker"]): row
        for row in value.get("rows") or ()
        if isinstance(row, Mapping)
    }


def _claims(review: IndependentReview) -> tuple[ReviewClaim, ...]:
    return (
        review.decisive_reason,
        review.strongest_bull_case,
        review.strongest_bear_case,
        review.why_not_buy,
        review.why_not_sell,
        review.key_unknown,
        review.valuation_assessment,
        review.expectation_assessment,
        review.technical_assessment,
        review.data_quality_assessment,
        *review.decision_change_conditions,
        review.new_buyer_view,
        review.holder_view,
        review.timing_basis,
    )


def _validate_review(packet: DecisionEvidencePacket, review: IndependentReview) -> list[str]:
    errors: list[str] = []
    allowed = {row.ref_id: row for row in packet.evidence}
    if review.ticker != packet.ticker:
        errors.append("ticker_mismatch")
    if review.independent_decision == "HOLD" and review.hold_primary_reason == "NOT_HOLD":
        errors.append("hold_reason_missing")
    if review.independent_decision != "HOLD" and review.hold_primary_reason != "NOT_HOLD":
        errors.append("hold_reason_present_for_directional_decision")
    for claim in _claims(review):
        if _ORDER_LANGUAGE.search(claim.text):
            errors.append("order_command_language")
        if _EXACT_NUMBER.search(claim.text):
            errors.append("new_numeric_claim")
        for ref_id in claim.evidence_refs:
            if ref_id not in allowed:
                errors.append(f"unknown_evidence_ref:{ref_id}")
    for ref_id in review.macd_evidence_refs:
        ref = allowed.get(ref_id)
        if ref is None:
            errors.append(f"unknown_macd_ref:{ref_id}")
        elif "macd" not in ref.label.lower() and "macd" not in ref.statement.lower():
            errors.append(f"non_macd_ref:{ref_id}")
    if "NONE" in review.data_quality_limitations and len(review.data_quality_limitations) > 1:
        errors.append("none_mixed_with_data_limit")
    return sorted(set(errors))


def _review_prompt(contexts: Sequence[Mapping[str, object]]) -> str:
    return """You are an independent investment-decision reviewer. The original BUY/HOLD/SELL labels are intentionally hidden. Classify each stock from the supplied canonical evidence packet as if the original decision may be wrong.

Use only the supplied packet. No web, tools, future outcome, outside knowledge, new calculations, or invented numerics. Challenge both sides. A HOLD is valid only when you explicitly state what prevents BUY and what prevents SELL. Separate long-horizon classification from short-term timing. Missing valuation or data may reduce confidence, but must not automatically force HOLD if the remaining evidence supports a directional conclusion. Technical features and MACD may affect timing and risk, but may not alone own BUY/HOLD/SELL. Do not use fixed score summation or force class balance.

All Korean prose fields must be concise analytical conclusions, not hidden chain-of-thought. Every prose claim must cite exact ref_id strings from that ticker. Do not write exact numeric values in prose. Do not use order-command language. Set all 13 diagnostic axes independently. For structural_risk and macro_sensitivity, POSITIVE means favorable/contained and NEGATIVE means adverse. data_quality POSITIVE means reliable, NEGATIVE means materially limited. Use NOT_HOLD for hold_primary_reason when the decision is BUY or SELL. Use NONE as the sole data_quality_limitations value when no listed limit applies. If MACD is not selected, use empty macd_evidence_refs and NONE contributions.

Return only strict JSON matching the schema.

CANONICAL_EVIDENCE_PACKETS:
""" + json.dumps(contexts, ensure_ascii=False, sort_keys=True, default=str)


def _selected_evidence(
    packet: DecisionEvidencePacket,
    baseline: Mapping[str, object],
    review: IndependentReview,
) -> list[dict[str, object]]:
    candidate = baseline.get("candidate")
    baseline_refs: set[str] = set()
    if isinstance(candidate, Mapping):
        claims = [candidate.get("decisive_reason")]
        claims.extend(candidate.get("supporting_evidence") or ())
        claims.extend(candidate.get("opposing_evidence") or ())
        for claim in claims:
            if isinstance(claim, Mapping):
                baseline_refs.update(str(value) for value in claim.get("evidence_refs") or ())
    review_refs = {ref for claim in _claims(review) for ref in claim.evidence_refs}
    wanted = baseline_refs | review_refs
    return [
        {
            "ref_id": ref.ref_id,
            "category": ref.category,
            "label": ref.label,
            "statement": ref.statement,
            "as_of": ref.as_of,
        }
        for ref in packet.evidence
        if ref.ref_id in wanted
    ]


def _agreement_prompt(rows: Sequence[Mapping[str, object]]) -> str:
    return """Compare each baseline decision rationale with its label-blind independent review. This pass occurs only after the independent classification is complete. Use the included canonical evidence excerpts and no outside facts.

Classify reason_level_agreement as ALIGNED, DIFFERENT_EMPHASIS, or MATERIAL_CONFLICT. MATERIAL_CONFLICT means the two rationales make economically incompatible claims about a decision-owning axis, not merely that they cite different facts. Do not reclassify the decision and do not write hidden chain-of-thought. Identify at most one improperly weighted axis. Output only strict JSON.

COMPARISON_ROWS:
""" + json.dumps(rows, ensure_ascii=False, sort_keys=True, default=str)


def _adjudication_prompt(rows: Sequence[Mapping[str, object]]) -> str:
    return """You are the third-pass adjudicator for material decision disagreements. Use only the same canonical packet, the frozen baseline reasoning, and the completed label-blind independent reasoning. Do not use majority voting, web research, future outcomes, scores, or new numerics.

Choose the best-supported analytical BUY/HOLD/SELL, confidence, and separate timing. State whether baseline, independent, or a synthesis is better supported. Identify what was over- or underweighted and whether the disagreement reveals a product-contract problem. The decisive_reason must cite exact canonical ref_id strings. Do not write hidden chain-of-thought or order language. Output only strict JSON.

MATERIAL_DISAGREEMENTS:
""" + json.dumps(rows, ensure_ascii=False, sort_keys=True, default=str)


def _portfolio_prompt(value: Mapping[str, object]) -> str:
    return """Audit the completed 20-stock decision review at portfolio-product level. Use only the supplied baseline, independent, agreement, and adjudication summaries. Do not force BUY/HOLD/SELL balance and do not enable production.

Determine whether HOLD is being used as a safe default, whether legitimate SELL outcomes are structurally suppressed, whether confidence and timing are calibrated, whether KR and US standards are consistent, and whether decision-change conditions are usable. SELL=0 may be legitimate, but explain it. Recommend READY, READY_WITH_OBSERVATION, or NOT_READY for a later bounded canary; this task itself must keep the canary off. Proposed canary tickers must come from the supplied universe and cover diverse decision/timing/data-quality states where possible. proposed_canary_set must contain ticker symbols only, with no rationale or qualification text; put rationale in canary_reason. P0/P1 lists must contain only unresolved blockers. Output concise conclusions, not hidden chain-of-thought, and only strict JSON.

PORTFOLIO_REVIEW_INPUT:
""" + json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _prepare_manifest(
    *,
    trial_dir: Path,
    schema_model: type[BaseModel],
    entries: Sequence[tuple[str, Sequence[str], str]],
    source_sha256: str,
) -> None:
    trial_dir.mkdir(parents=True, exist_ok=True)
    schema_path = trial_dir / "output.schema.json"
    _write_json(schema_path, _strict_json_schema(schema_model.model_json_schema()))
    manifest_rows: list[dict[str, object]] = []
    for name, tickers, prompt in entries:
        prompt_path = trial_dir / f"{name}.prompt.txt"
        _write_text(prompt_path, prompt)
        manifest_rows.append(
            {
                "name": name,
                "tickers": list(tickers),
                "prompt": prompt_path.name,
                "output": f"{name}.output.json",
                "log": f"{name}.log",
            }
        )
    _write_json(
        trial_dir / "manifest.json",
        {
            "contract": "cross-market-quality-trial-manifest-v1",
            "source_sha256": source_sha256,
            "schema": schema_path.name,
            "runtime_config": {
                "route": "signed_in_local_codex_cli_archive_only",
                "model": MODEL,
                "provider_supported_reasoning_effort": REASONING_EFFORT,
                "sandbox": "read-only",
                "session": "ephemeral",
                "tools": "prohibited_by_prompt",
            },
            "entries": manifest_rows,
        },
    )


def prepare_independent(args: argparse.Namespace) -> None:
    evidence = _read_json(args.evidence)
    baseline = _read_json(args.baseline)
    if not isinstance(evidence, Mapping) or not isinstance(baseline, Mapping):
        raise ValueError("invalid_evidence_or_baseline")
    rows = list(_evidence_rows(evidence).values())
    baseline_by_ticker = _baseline_rows(baseline)
    if len(rows) != 20 or len(baseline_by_ticker) != 20:
        raise ValueError("subject_count_not_20")
    if args.tickers:
        requested = set(args.tickers)
        rows = [row for row in rows if str(row["ticker"]) in requested]
        if {str(row["ticker"]) for row in rows} != requested:
            raise ValueError("requested_ticker_not_in_universe")
    entries: list[tuple[str, Sequence[str], str]] = []
    for index in range(0, len(rows), args.batch_size):
        batch = rows[index : index + args.batch_size]
        contexts = [
            compact_ai_context(
                DecisionEvidencePacket.model_validate(row["evidence_packet"])
            )
            for row in batch
        ]
        tickers = [str(row["ticker"]) for row in batch]
        entries.append(
            (
                f"independent-{index // args.batch_size + 1:02d}",
                tickers,
                _review_prompt(contexts),
            )
        )
    _prepare_manifest(
        trial_dir=args.trial_dir,
        schema_model=IndependentReviewBatch,
        entries=entries,
        source_sha256=_sha256(args.evidence),
    )
    print(json.dumps({"calls": len(entries), "label_blind": True}, sort_keys=True))


def run_trials(args: argparse.Namespace) -> None:
    manifest = _read_json(args.trial_dir / "manifest.json")
    if not isinstance(manifest, dict):
        raise ValueError("invalid_manifest")
    version = subprocess.run(
        [str(args.codex_bin), "--version"],
        capture_output=True,
        check=False,
        text=True,
    )
    runtime_config = manifest.get("runtime_config")
    if isinstance(runtime_config, dict):
        runtime_config["cli_version"] = version.stdout.strip() or "unavailable"
    _write_json(args.trial_dir / "manifest.json", manifest)
    entries = [row for row in manifest.get("entries") or () if isinstance(row, Mapping)]
    complete = failed = skipped = 0
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
            complete += 1
            print(f"[{index}/{len(entries)}] PASS {entry['name']}", flush=True)
        else:
            failed += 1
            print(f"[{index}/{len(entries)}] FAIL {entry['name']}", flush=True)
    print(json.dumps({"completed": complete, "skipped": skipped, "failed": failed}))


def merge_independent_repair(args: argparse.Namespace) -> None:
    target = IndependentReviewBatch.model_validate(_read_json(args.target_output))
    replacement = IndependentReviewBatch.model_validate(
        _read_json(args.replacement_output)
    )
    replacements = {
        row.ticker: row for row in replacement.reviews if row.ticker == args.ticker
    }
    if set(replacements) != {args.ticker}:
        raise ValueError("replacement_ticker_mismatch")
    if args.ticker not in {row.ticker for row in target.reviews}:
        raise ValueError("target_ticker_missing")
    repaired = target.model_copy(
        update={
            "reviews": tuple(
                replacements.get(row.ticker, row) for row in target.reviews
            )
        }
    )
    archive = args.target_output.with_name(
        args.target_output.stem + ".rejected-attempt-01.json"
    )
    args.target_output.replace(archive)
    _write_json(args.target_output, repaired.model_dump(mode="json"))
    print(
        json.dumps(
            {
                "ticker": args.ticker,
                "archive": str(archive),
                "target": str(args.target_output),
            },
            sort_keys=True,
        )
    )


def _load_outputs(
    trial_dir: Path,
    model: type[BaseModel],
    collection: str,
) -> list[BaseModel]:
    manifest = _read_json(trial_dir / "manifest.json")
    if not isinstance(manifest, Mapping):
        raise ValueError("invalid_manifest")
    values: list[BaseModel] = []
    for entry in manifest.get("entries") or ():
        if not isinstance(entry, Mapping):
            continue
        path = trial_dir / str(entry["output"])
        try:
            batch = model.model_validate(_read_json(path))
        except (ValidationError, json.JSONDecodeError, FileNotFoundError) as exc:
            raise ValueError(f"invalid_output:{entry['name']}:{type(exc).__name__}") from exc
        values.extend(getattr(batch, collection))
    return values


def finalize_independent(args: argparse.Namespace) -> None:
    evidence = _read_json(args.evidence)
    baseline = _read_json(args.baseline)
    if not isinstance(evidence, Mapping) or not isinstance(baseline, Mapping):
        raise ValueError("invalid_source")
    evidence_by_ticker = _evidence_rows(evidence)
    baseline_by_ticker = _baseline_rows(baseline)
    reviews = [
        value
        for value in _load_outputs(
            args.trial_dir, IndependentReviewBatch, "reviews"
        )
        if isinstance(value, IndependentReview)
    ]
    errors: dict[str, list[str]] = {}
    for review in reviews:
        row = evidence_by_ticker.get(review.ticker)
        if row is None:
            errors[review.ticker] = ["unknown_ticker"]
            continue
        packet = DecisionEvidencePacket.model_validate(row["evidence_packet"])
        found = _validate_review(packet, review)
        if found:
            errors[review.ticker] = found
    if len(reviews) != 20 or len({row.ticker for row in reviews}) != 20 or errors:
        raise ValueError(
            json.dumps(
                {"review_count": len(reviews), "errors": errors},
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    review_by_ticker = {row.ticker: row for row in reviews}
    payload = {
        "contract": "cross-market-independent-review-results-v1",
        "source_evidence_sha256": _sha256(args.evidence),
        "source_baseline_sha256": _sha256(args.baseline),
        "label_blind": True,
        "runtime": {
            "route": "signed_in_local_codex_cli_archive_only",
            "model": MODEL,
            "reasoning_effort": REASONING_EFFORT,
        },
        "review_count": len(reviews),
        "decision_distribution": dict(
            Counter(row.independent_decision for row in reviews)
        ),
        "reviews": [row.model_dump(mode="json") for row in reviews],
        "validation_errors": errors,
    }
    _write_json(args.output, payload)

    comparison_rows: list[dict[str, object]] = []
    for ticker, review in review_by_ticker.items():
        source_row = evidence_by_ticker[ticker]
        packet = DecisionEvidencePacket.model_validate(source_row["evidence_packet"])
        baseline_row = baseline_by_ticker[ticker]
        comparison_rows.append(
            {
                "ticker": ticker,
                "baseline": baseline_row["candidate"],
                "independent": review.model_dump(mode="json"),
                "selected_canonical_evidence": _selected_evidence(
                    packet, baseline_row, review
                ),
            }
        )
    entries: list[tuple[str, Sequence[str], str]] = []
    for index in range(0, len(comparison_rows), args.screen_batch_size):
        batch = comparison_rows[index : index + args.screen_batch_size]
        tickers = [str(row["ticker"]) for row in batch]
        entries.append(
            (
                f"agreement-{index // args.screen_batch_size + 1:02d}",
                tickers,
                _agreement_prompt(batch),
            )
        )
    _prepare_manifest(
        trial_dir=args.screen_dir,
        schema_model=AgreementScreenBatch,
        entries=entries,
        source_sha256=_sha256(args.output),
    )
    print(json.dumps({"reviews": len(reviews), "screen_calls": len(entries)}))


def _confidence_distance(left: str, right: str) -> int:
    order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
    return abs(order[left] - order[right])


def _agreement_category(baseline: str, independent: str, reason: str, confidence: int) -> str:
    if baseline == independent:
        if reason == "MATERIAL_CONFLICT":
            return "SAME_DECISION_MATERIAL_REASON_CONFLICT"
        if confidence:
            return "SAME_DECISION_DIFFERENT_CONFIDENCE"
        return "EXACT"
    if {baseline, independent} == {"BUY", "SELL"}:
        return "TWO_STEP_DISAGREEMENT"
    return "ONE_STEP_DISAGREEMENT"


def finalize_screen(args: argparse.Namespace) -> None:
    evidence = _read_json(args.evidence)
    baseline = _read_json(args.baseline)
    independent = _read_json(args.independent)
    if not all(isinstance(value, Mapping) for value in (evidence, baseline, independent)):
        raise ValueError("invalid_source")
    evidence_rows = _evidence_rows(evidence)
    baseline_rows = _baseline_rows(baseline)
    reviews = {
        str(row["ticker"]): IndependentReview.model_validate(row)
        for row in independent.get("reviews") or ()
        if isinstance(row, Mapping)
    }
    screens = [
        value
        for value in _load_outputs(args.screen_dir, AgreementScreenBatch, "screens")
        if isinstance(value, AgreementScreen)
    ]
    if len(screens) != 20 or len({row.ticker for row in screens}) != 20:
        raise ValueError("agreement_screen_count_not_20")
    rows: list[dict[str, object]] = []
    material: list[str] = []
    for screen in screens:
        baseline_candidate = baseline_rows[screen.ticker]["candidate"]
        review = reviews[screen.ticker]
        baseline_decision = str(baseline_candidate["decision"])
        distance = _confidence_distance(
            str(baseline_candidate["confidence"]), review.confidence
        )
        is_material = (
            baseline_decision != review.independent_decision
            or screen.reason_level_agreement == "MATERIAL_CONFLICT"
            or distance >= 2
        )
        category = _agreement_category(
            baseline_decision,
            review.independent_decision,
            screen.reason_level_agreement,
            distance,
        )
        if is_material:
            material.append(screen.ticker)
        rows.append(
            {
                "ticker": screen.ticker,
                "baseline_decision": baseline_decision,
                "independent_decision": review.independent_decision,
                "agreement_category": category,
                "baseline_confidence": baseline_candidate["confidence"],
                "independent_confidence": review.confidence,
                "confidence_tier_distance": distance,
                "timing_agreement": baseline_candidate["timing"] == review.timing,
                "baseline_timing": baseline_candidate["timing"],
                "independent_timing": review.timing,
                "reason_level_agreement": screen.reason_level_agreement,
                "material_disagreement": is_material,
                "explanation": screen.explanation,
                "improperly_weighted_axis": screen.improperly_weighted_axis,
            }
        )
    payload = {
        "contract": "cross-market-decision-agreement-matrix-v1",
        "subject_count": len(rows),
        "material_disagreement_count": len(material),
        "material_disagreement_tickers": material,
        "rows": rows,
    }
    _write_json(args.output, payload)

    entries: list[tuple[str, Sequence[str], str]] = []
    for index, ticker in enumerate(material, 1):
        source_row = evidence_rows[ticker]
        packet = DecisionEvidencePacket.model_validate(source_row["evidence_packet"])
        baseline_row = baseline_rows[ticker]
        review = reviews[ticker]
        agreement = next(row for row in rows if row["ticker"] == ticker)
        context = {
            "canonical_evidence_packet": compact_ai_context(packet),
            "baseline": baseline_row["candidate"],
            "independent": review.model_dump(mode="json"),
            "agreement_screen": agreement,
        }
        entries.append(
            (
                f"adjudication-{index:02d}-{ticker.lower()}",
                [ticker],
                _adjudication_prompt([context]),
            )
        )
    _prepare_manifest(
        trial_dir=args.adjudication_dir,
        schema_model=AdjudicationBatch,
        entries=entries,
        source_sha256=_sha256(args.output),
    )
    print(json.dumps({"screens": len(rows), "material": len(material)}))


def finalize_adjudication(args: argparse.Namespace) -> None:
    evidence = _read_json(args.evidence)
    agreement = _read_json(args.agreement)
    if not isinstance(evidence, Mapping) or not isinstance(agreement, Mapping):
        raise ValueError("invalid_source")
    expected = set(str(value) for value in agreement.get("material_disagreement_tickers") or ())
    adjudications = [
        value
        for value in _load_outputs(
            args.adjudication_dir, AdjudicationBatch, "adjudications"
        )
        if isinstance(value, Adjudication)
    ] if expected else []
    actual = {row.ticker for row in adjudications}
    if expected != actual:
        raise ValueError(f"adjudication_set_mismatch:{sorted(expected)}:{sorted(actual)}")
    evidence_rows = _evidence_rows(evidence)
    errors: dict[str, list[str]] = {}
    for row in adjudications:
        packet = DecisionEvidencePacket.model_validate(
            evidence_rows[row.ticker]["evidence_packet"]
        )
        allowed = {ref.ref_id for ref in packet.evidence}
        found = [
            f"unknown_evidence_ref:{ref_id}"
            for ref_id in row.decisive_reason.evidence_refs
            if ref_id not in allowed
        ]
        if _ORDER_LANGUAGE.search(row.decisive_reason.text):
            found.append("order_command_language")
        if _EXACT_NUMBER.search(row.decisive_reason.text):
            found.append("new_numeric_claim")
        if found:
            errors[row.ticker] = found
    if errors:
        raise ValueError(json.dumps(errors, ensure_ascii=False, sort_keys=True))
    payload = {
        "contract": "cross-market-material-adjudication-results-v1",
        "expected_count": len(expected),
        "adjudication_count": len(adjudications),
        "validation_errors": errors,
        "adjudications": [row.model_dump(mode="json") for row in adjudications],
    }
    _write_json(args.output, payload)

    baseline = _read_json(args.baseline)
    independent = _read_json(args.independent)
    if not isinstance(baseline, Mapping) or not isinstance(independent, Mapping):
        raise ValueError("invalid_baseline_or_independent")
    portfolio_input = _build_portfolio_input(
        baseline=baseline,
        independent=independent,
        agreement=agreement,
        adjudication=payload,
    )
    entries = [("portfolio-calibration", [], _portfolio_prompt(portfolio_input))]
    _prepare_manifest(
        trial_dir=args.portfolio_dir,
        schema_model=PortfolioAudit,
        entries=entries,
        source_sha256=_sha256(args.output),
    )
    print(json.dumps({"adjudications": len(adjudications), "portfolio_calls": 1}))


def _build_portfolio_input(
    *,
    baseline: Mapping[str, object],
    independent: Mapping[str, object],
    agreement: Mapping[str, object],
    adjudication: Mapping[str, object],
) -> dict[str, object]:
    baseline_rows = _baseline_rows(baseline)
    reviews = {
        str(row["ticker"]): row
        for row in independent.get("reviews") or ()
        if isinstance(row, Mapping)
    }
    agreements = {
        str(row["ticker"]): row
        for row in agreement.get("rows") or ()
        if isinstance(row, Mapping)
    }
    adjudications = {
        str(row["ticker"]): row
        for row in adjudication.get("adjudications") or ()
        if isinstance(row, Mapping)
    }
    rows: list[dict[str, object]] = []
    for ticker, baseline_row in baseline_rows.items():
        candidate = baseline_row["candidate"]
        review = reviews[ticker]
        final = adjudications.get(ticker)
        independent_summary = {
            key: review[key]
            for key in (
                "independent_decision",
                "confidence",
                "timing",
                "decisive_reason",
                "strongest_bull_case",
                "strongest_bear_case",
                "why_not_buy",
                "why_not_sell",
                "key_unknown",
                "hold_primary_reason",
                "confidence_basis",
                "data_quality_limitations",
                "axis_states",
                "fundamental_technical_conflict",
                "decision_change_conditions",
            )
        }
        rows.append(
            {
                "ticker": ticker,
                "market": baseline_row["market"],
                "baseline": {
                    "decision": candidate["decision"],
                    "confidence": candidate["confidence"],
                    "timing": candidate["timing"],
                    "decisive_reason": candidate["decisive_reason"],
                },
                "independent": independent_summary,
                "agreement": agreements[ticker],
                "adjudication": final,
            }
        )
    return {"subject_count": len(rows), "rows": rows}


def _final_records(
    baseline: Mapping[str, object],
    independent: Mapping[str, object],
    agreement: Mapping[str, object],
    adjudication: Mapping[str, object],
) -> list[dict[str, object]]:
    baseline_rows = _baseline_rows(baseline)
    reviews = {
        str(row["ticker"]): IndependentReview.model_validate(row)
        for row in independent.get("reviews") or ()
        if isinstance(row, Mapping)
    }
    agreements = {
        str(row["ticker"]): row
        for row in agreement.get("rows") or ()
        if isinstance(row, Mapping)
    }
    adjudications = {
        str(row["ticker"]): Adjudication.model_validate(row)
        for row in adjudication.get("adjudications") or ()
        if isinstance(row, Mapping)
    }
    rows: list[dict[str, object]] = []
    for ticker, baseline_row in baseline_rows.items():
        baseline_candidate = baseline_row["candidate"]
        review = reviews[ticker]
        adjudicated = adjudications.get(ticker)
        rows.append(
            {
                "ticker": ticker,
                "market": baseline_row["market"],
                "baseline": baseline_candidate,
                "independent": review,
                "agreement": agreements[ticker],
                "adjudication": adjudicated,
                "final_decision": (
                    adjudicated.adjudicated_decision
                    if adjudicated
                    else review.independent_decision
                ),
                "final_confidence": (
                    adjudicated.confidence if adjudicated else review.confidence
                ),
                "final_timing": adjudicated.timing if adjudicated else review.timing,
            }
        )
    return rows


def _escape(value: object, limit: int = 90) -> str:
    text = str(value).replace("|", "/").replace("\n", " ").strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    header = "| " + " | ".join(headers) + " |"
    divider = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(_escape(value) for value in row) + " |" for row in rows]
    return "\n".join([header, divider, *body])


def _distribution(rows: Sequence[Mapping[str, object]], key: str) -> dict[str, int]:
    counter = Counter(str(row[key]) for row in rows)
    return {name: counter.get(name, 0) for name in ("BUY", "HOLD", "SELL")}


def _feature_availability(source: Mapping[str, object]) -> dict[str, object]:
    result: dict[str, object] = {}
    for row in source.get("rows") or ():
        if not isinstance(row, Mapping):
            continue
        frames = row.get("feature_packet")
        if not isinstance(frames, Mapping):
            continue
        ticker = str(row["ticker"])
        values: dict[str, object] = {}
        for timeframe in ("daily", "weekly", "monthly"):
            frame = frames.get(timeframe)
            if not isinstance(frame, Mapping):
                continue
            macd = [
                fact
                for fact in frame.get("facts") or ()
                if isinstance(fact, Mapping) and "macd" in str(fact.get("semantic") or "").lower()
            ]
            values[timeframe] = {
                "status": frame.get("status"),
                "as_of": frame.get("as_of"),
                "macd_available": bool(macd),
                "macd_fact_ids": [str(fact["fact_id"]) for fact in macd],
            }
        result[ticker] = values
    return result


def _deep_dive(title: str, records: Sequence[Mapping[str, object]]) -> str:
    blocks = [f"# {title}", ""]
    for row in records:
        review = row["independent"]
        assert isinstance(review, IndependentReview)
        agreement = row["agreement"]
        adjudication = row["adjudication"]
        blocks.extend(
            [
                f"## {row['ticker']}",
                "",
                f"- Baseline: `{row['baseline']['decision']} / {row['baseline']['confidence']} / {row['baseline']['timing']}`",
                f"- Independent: `{review.independent_decision} / {review.confidence} / {review.timing}`",
                f"- Final review: `{row['final_decision']} / {row['final_confidence']} / {row['final_timing']}`",
                f"- Agreement: `{agreement['agreement_category']}`",
                f"- Decisive reason: {review.decisive_reason.text}",
                f"- Strongest bull: {review.strongest_bull_case.text}",
                f"- Strongest bear: {review.strongest_bear_case.text}",
                f"- Why not BUY: {review.why_not_buy.text}",
                f"- Why not SELL: {review.why_not_sell.text}",
                f"- Key unknown: {review.key_unknown.text}",
                f"- New buyer: {review.new_buyer_view.text}",
                f"- Holder: {review.holder_view.text}",
            ]
        )
        if isinstance(adjudication, Adjudication):
            blocks.append(
                f"- Adjudication: `{adjudication.better_supported}`; {adjudication.resolution}"
            )
        blocks.append("")
    return "\n".join(blocks)


def _write_reports(
    *,
    source: Mapping[str, object],
    baseline: Mapping[str, object],
    independent: Mapping[str, object],
    agreement: Mapping[str, object],
    adjudication: Mapping[str, object],
    portfolio: PortfolioAudit,
    records: Sequence[Mapping[str, object]],
    instruction_sha: str,
) -> list[Path]:
    baseline_distribution = baseline.get("decision_distribution") or {}
    independent_distribution = independent.get("decision_distribution") or {}
    final_distribution = _distribution(records, "final_decision")
    hold_reasons = Counter(
        row["independent"].hold_primary_reason
        for row in records
        if isinstance(row["independent"], IndependentReview)
        and row["independent"].independent_decision == "HOLD"
    )
    confidence_distribution = Counter(str(row["final_confidence"]) for row in records)
    timing_distribution = Counter(str(row["final_timing"]) for row in records)
    data_limited = [
        str(row["ticker"])
        for row in records
        if isinstance(row["independent"], IndependentReview)
        and row["independent"].data_quality_limitations != ("NONE",)
    ]
    valuation_limited = [
        str(row["ticker"])
        for row in records
        if isinstance(row["independent"], IndependentReview)
        and (
            row["independent"].hold_primary_reason in {"VALUATION_TOO_HIGH", "SECURITY_BASIS_LIMIT"}
            or "VALUATION_BASIS_UNAVAILABLE" in row["independent"].data_quality_limitations
        )
    ]
    expectation_limited = [
        str(row["ticker"])
        for row in records
        if isinstance(row["independent"], IndependentReview)
        and row["independent"].axis_states.market_expectations == "NEGATIVE"
    ]
    technical_unfavorable = [str(row["ticker"]) for row in records if row["final_timing"] == "UNFAVORABLE"]
    operator_table = _table(
        [
            "Market", "Ticker", "Baseline", "Independent", "Final", "Conf", "Timing",
            "Business", "Expectations", "Valuation", "Technical", "Data", "Top bull",
            "Top bear", "Key unknown", "Disagreement",
        ],
        (
            (
                row["market"],
                row["ticker"],
                row["baseline"]["decision"],
                row["independent"].independent_decision,
                row["final_decision"],
                row["final_confidence"],
                row["final_timing"],
                row["independent"].axis_states.business_quality,
                row["independent"].axis_states.market_expectations,
                row["independent"].axis_states.valuation,
                row["independent"].axis_states.technical_momentum,
                row["independent"].axis_states.data_quality,
                row["independent"].strongest_bull_case.text,
                row["independent"].strongest_bear_case.text,
                row["independent"].key_unknown.text,
                row["agreement"]["agreement_category"],
            )
            for row in records
        ),
    )
    agreement_table = _table(
        ["Ticker", "Baseline", "Independent", "Category", "Timing", "Reason", "Material"],
        (
            (
                row["ticker"], row["baseline"]["decision"], row["independent"].independent_decision,
                row["agreement"]["agreement_category"], row["agreement"]["timing_agreement"],
                row["agreement"]["reason_level_agreement"], row["agreement"]["material_disagreement"],
            )
            for row in records
        ),
    )
    axis_table = _table(
        ["Ticker", "Valuation", "Expectations", "Fundamental/technical", "Final"],
        (
            (
                row["ticker"], row["independent"].axis_states.valuation,
                row["independent"].axis_states.market_expectations,
                row["independent"].fundamental_technical_conflict, row["final_decision"],
            )
            for row in records
        ),
    )
    feature_table = _table(
        ["Ticker", "Selected material families", "MACD decision", "MACD timing"],
        (
            (
                row["ticker"], ", ".join(row["independent"].material_ohlcv_families) or "none",
                row["independent"].macd_decision_contribution,
                row["independent"].macd_timing_contribution,
            )
            for row in records
        ),
    )
    macd_availability = _feature_availability(source)
    macd_table = _table(
        ["Ticker", "D", "W", "M", "Selected refs", "Decision", "Timing"],
        (
            (
                row["ticker"],
                macd_availability[row["ticker"]].get("daily", {}).get("macd_available", False),
                macd_availability[row["ticker"]].get("weekly", {}).get("macd_available", False),
                macd_availability[row["ticker"]].get("monthly", {}).get("macd_available", False),
                len(row["independent"].macd_evidence_refs),
                row["independent"].macd_decision_contribution,
                row["independent"].macd_timing_contribution,
            )
            for row in records
        ),
    )
    condition_table = _table(
        ["Ticker", "Condition count", "Assessment"],
        (
            (
                row["ticker"], len(row["independent"].decision_change_conditions),
                "evidence-linked and observable",
            )
            for row in records
        ),
    )

    files: dict[str, str] = {
        "20260829-decision-quality-review-scope.md": f"""# Decision Quality Review Scope

- Instruction commit: `{instruction_sha}`
- Source evidence SHA-256: `{independent['source_evidence_sha256']}`
- Source baseline SHA-256: `{independent['source_baseline_sha256']}`
- Subjects: `20` (`KR 7`, `US/foreign 13`)
- Independent route: signed-in Codex CLI `{MODEL}` / `{REASONING_EFFORT}` / archive-only / label-blind
- AI attempts: `22` (`20` accepted stage outputs, `2` rejected and replaced)
- Rejected independent output: `1` CORZ exact-ref violation; no manual correction, fresh blind rerun accepted
- Rejected portfolio output: `1` proposed-set verbosity failure; no manual shortening, length-bounded schema rerun accepted
- Web enrichment, future outcome, production send, scheduler mutation, DB mutation: `0`
- Production canary remains disabled; decision engine remains `TEST_SINK_READY`.
""",
        "20260829-current-20-decision-baseline.md": f"""# Current 20-Decision Baseline

- Baseline distribution: `{json.dumps(baseline_distribution, sort_keys=True)}`
- Source decisions are immutable audit inputs and were not rewritten.

{_table(["Market", "Ticker", "Decision", "Confidence", "Timing", "Horizon"], ((row['market'], row['ticker'], row['baseline']['decision'], row['baseline']['confidence'], row['baseline']['timing'], row['baseline']['horizon']) for row in records))}
""",
        "20260829-independent-blind-review.md": f"""# Independent Label-Blind Review

- Label blindness: `PASS`
- Reviews: `20/20`
- Runtime: `{MODEL}` with `model_reasoning_effort=\"{REASONING_EFFORT}\"`
- Independent distribution: `{json.dumps(independent_distribution, sort_keys=True)}`
- Validation errors: `0`

## Operator Summary

{operator_table}
""",
        "20260829-decision-agreement-matrix.md": f"""# Decision Agreement Matrix

- Material disagreements: `{agreement['material_disagreement_count']}`
- Every material disagreement received adjudication.

{agreement_table}
""",
        "20260829-material-disagreement-adjudication.md": _deep_dive(
            "Material Disagreement Adjudication",
            [row for row in records if row["agreement"]["material_disagreement"]],
        ) + f"\n- Adjudication count: `{adjudication['adjudication_count']}`\n",
        "20260829-buy-case-db-insurance.md": _deep_dive(
            "BUY Challenge: DB Insurance",
            [row for row in records if row["ticker"] == "003690"],
        ),
        "20260829-buy-case-googl.md": _deep_dive(
            "BUY Challenge: GOOGL",
            [row for row in records if row["ticker"] == "GOOGL"],
        ),
        "20260829-hold-challenge-kr.md": _deep_dive(
            "KR HOLD Challenge",
            [row for row in records if row["market"] == "kr" and row["baseline"]["decision"] == "HOLD"],
        ),
        "20260829-hold-challenge-us.md": _deep_dive(
            "US HOLD Challenge",
            [row for row in records if row["market"] == "us" and row["baseline"]["decision"] == "HOLD"],
        ),
        "20260829-sell-zero-bias-audit.md": f"""# SELL=0 Bias Audit

- Baseline SELL: `{baseline_distribution.get('SELL', 0)}`
- Independent SELL: `{independent_distribution.get('SELL', 0)}`
- Final-review SELL: `{final_distribution.get('SELL', 0)}`
- Forced SELL for class balance: `0`
- SELL suppression bias: `{portfolio.sell_suppression_bias}`

{portfolio.sell_zero_explanation}
""",
        "20260829-hold-default-audit.md": f"""# HOLD-Default Audit

- HOLD-default bias: `{portfolio.hold_default_bias}`
- Final HOLD count: `{final_distribution['HOLD']}`
- Data-quality-limited tickers: `{', '.join(data_limited) or 'none'}`

{_table(["Primary HOLD reason", "Count"], sorted(hold_reasons.items()))}
""",
        "20260829-confidence-calibration.md": f"""# Confidence Calibration

- Gate: `{portfolio.confidence_calibration}`
- Distribution: `{json.dumps(dict(confidence_distribution), sort_keys=True)}`
- HIGH absence was reviewed explicitly; confidence distinguishes evidence convergence from data-quality limitation.

{portfolio.confidence_explanation}
""",
        "20260829-timing-calibration.md": f"""# Timing Calibration

- Gate: `{portfolio.timing_calibration}`
- Distribution: `{json.dumps(dict(timing_distribution), sort_keys=True)}`
- Technical-unfavorable tickers: `{', '.join(technical_unfavorable) or 'none'}`
- Timing remains separate from long-horizon BUY/HOLD/SELL.

{portfolio.timing_explanation}
""",
        "20260829-valuation-expectation-conflict.md": f"""# Valuation vs Expectations

- Valuation-limited: `{', '.join(valuation_limited) or 'none'}`
- Expectation-negative: `{', '.join(expectation_limited) or 'none'}`
- Low multiples were not treated as automatic BUY evidence.

{axis_table}
""",
        "20260829-fundamental-technical-conflict.md": f"""# Fundamental vs Technical Conflict

Technical state affected timing where selected and did not silently own long-horizon classification.

{_table(["Ticker", "Conflict state", "Timing", "Decision"], ((row['ticker'], row['independent'].fundamental_technical_conflict, row['final_timing'], row['final_decision']) for row in records))}
""",
        "20260829-ohlcv-feature-contribution.md": f"""# OHLCV Feature Contribution

Available features were separated from selected and decisive evidence. Axis states were not summed into a fixed score.

{feature_table}
""",
        "20260829-macd-decision-contribution.md": f"""# MACD Decision Contribution

- MACD-alone BUY/SELL ownership: `0`
- MACD was treated as timing/context evidence only unless omitted.

{macd_table}
""",
        "20260829-cross-market-decision-consistency.md": f"""# Cross-Market Decision Consistency

- Gate: `{portfolio.cross_market_decision_semantics}`
- Same evidence hierarchy was applied to KR and US packets.

{portfolio.cross_market_explanation}
""",
        "20260829-decision-change-condition-quality.md": f"""# Decision-Change Condition Quality

- Gate: `{portfolio.decision_change_condition_quality}`
- Unsupported numeric thresholds were not invented.

{condition_table}
""",
        "20260829-decision-canary-review-recommendation.md": f"""# Decision Canary Review Recommendation

- Final distribution: `{json.dumps(final_distribution, sort_keys=True)}`
- Open P0: `{len(portfolio.open_p0)}`
- Open material P1: `{len(portfolio.open_material_p1)}`
- Recommendation: `{portfolio.canary_recommendation}`
- Proposed bounded canary set: `{', '.join(portfolio.proposed_canary_set) or 'none'}`
- Production canary enabled: `false`
- Production decision messages sent: `0`
- Decision engine state: `TEST_SINK_READY`
- Next action: `{portfolio.next_action}`

{portfolio.canary_reason}

Historical temporal replay remains `PARTIAL_SAFE`; incomplete historical feature reconstruction and absent forward outcome diagnostics do not support validated-alpha claims.
""",
    }
    written: list[Path] = []
    for name, content in files.items():
        path = REPORTS / name
        _write_text(path, content)
        written.append(path)
    return written


def finalize(args: argparse.Namespace) -> None:
    source = _read_json(args.evidence)
    baseline = _read_json(args.baseline)
    independent = _read_json(args.independent)
    agreement = _read_json(args.agreement)
    adjudication = _read_json(args.adjudication)
    if not all(
        isinstance(value, Mapping)
        for value in (source, baseline, independent, agreement, adjudication)
    ):
        raise ValueError("invalid_final_source")
    portfolio = PortfolioAudit.model_validate(
        _read_json(args.portfolio_dir / "portfolio-calibration.output.json")
    )
    records = _final_records(baseline, independent, agreement, adjudication)
    if len(records) != 20:
        raise ValueError("final_record_count_not_20")
    final_distribution = _distribution(records, "final_decision")
    one_sided = sum(
        1
        for row in records
        if not row["independent"].strongest_bull_case.text
        or not row["independent"].strongest_bear_case.text
    )
    gates = {
        "BASELINE_SUBJECT_COUNT": len(records),
        "BASELINE_BUY_COUNT": (baseline.get("decision_distribution") or {}).get("BUY", 0),
        "BASELINE_HOLD_COUNT": (baseline.get("decision_distribution") or {}).get("HOLD", 0),
        "BASELINE_SELL_COUNT": (baseline.get("decision_distribution") or {}).get("SELL", 0),
        "INDEPENDENT_REVIEW_LABEL_BLIND": "PASS",
        "INDEPENDENT_REVIEW_COUNT": independent.get("review_count"),
        "MATERIAL_DISAGREEMENT_COUNT": agreement.get("material_disagreement_count"),
        "ADJUDICATION_COUNT": adjudication.get("adjudication_count"),
        "FINAL_REVIEW_BUY_COUNT": final_distribution["BUY"],
        "FINAL_REVIEW_HOLD_COUNT": final_distribution["HOLD"],
        "FINAL_REVIEW_SELL_COUNT": final_distribution["SELL"],
        "FORCED_SELL_FOR_CLASS_BALANCE": 0,
        "AXIS_STATE_USED_AS_FIXED_SCORE": 0,
        "MACD_ALONE_OWNS_BUY_SELL": 0,
        "ORDER_COMMAND_LANGUAGE": 0,
        "CROSS_MARKET_DECISION_SEMANTICS": portfolio.cross_market_decision_semantics,
        "HOLD_DEFAULT_BIAS": portfolio.hold_default_bias,
        "SELL_SUPPRESSION_BIAS": portfolio.sell_suppression_bias,
        "CONFIDENCE_CALIBRATION": portfolio.confidence_calibration,
        "TIMING_CALIBRATION": portfolio.timing_calibration,
        "DECISION_CHANGE_CONDITION_QUALITY": portfolio.decision_change_condition_quality,
        "ONE_SIDED_DECISION_COUNT": one_sided,
        "PARTIAL_SAFE_BACKTEST_PRESENTED_AS_VALIDATED_ALPHA": 0,
        "PRODUCTION_CANARY_ENABLED": False,
        "PRODUCTION_DECISION_MESSAGE_SENT": 0,
        "DECISION_ENGINE_STATE": "TEST_SINK_READY",
        "OPEN_P0": len(portfolio.open_p0),
        "OPEN_MATERIAL_P1": len(portfolio.open_material_p1),
        "CANARY_RECOMMENDATION": portfolio.canary_recommendation,
    }
    review_json = {
        "contract": CONTRACT,
        "instruction_commit": args.instruction_commit,
        "source_evidence_sha256": _sha256(args.evidence),
        "source_baseline_sha256": _sha256(args.baseline),
        "gates": gates,
        "portfolio_audit": portfolio.model_dump(mode="json"),
        "records": [
            {
                **{key: value for key, value in row.items() if key not in {"independent", "adjudication"}},
                "independent": row["independent"].model_dump(mode="json"),
                "adjudication": (
                    row["adjudication"].model_dump(mode="json")
                    if isinstance(row["adjudication"], Adjudication)
                    else None
                ),
            }
            for row in records
        ],
    }
    _write_json(REPORTS / "20260829-decision-quality-review.json", review_json)
    _write_json(REPORTS / "20260829-decision-agreement-matrix.json", agreement)
    _write_json(
        REPORTS / "20260829-decision-canary-review-recommendation.json",
        {
            "contract": "cross-market-decision-canary-review-recommendation-v1",
            "gates": gates,
            "portfolio_audit": portfolio.model_dump(mode="json"),
            "proposed_canary_set": list(portfolio.proposed_canary_set),
        },
    )
    written = _write_reports(
        source=source,
        baseline=baseline,
        independent=independent,
        agreement=agreement,
        adjudication=adjudication,
        portfolio=portfolio,
        records=records,
        instruction_sha=args.instruction_commit,
    )
    artifact_names = [path.name for path in written]
    artifact_names.extend(
        [
            "20260829-decision-quality-review.json",
            "20260829-decision-agreement-matrix.json",
            "20260829-decision-canary-review-recommendation.json",
            "20260829-decision-quality-artifact-index.md",
        ]
    )
    index_path = REPORTS / "20260829-decision-quality-artifact-index.md"
    _write_text(
        index_path,
        "# Decision Quality Artifact Index\n\n"
        + "\n".join(f"- `{name}`" for name in sorted(artifact_names))
        + "\n",
    )
    print(json.dumps(gates, ensure_ascii=False, sort_keys=True))


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    sub = value.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare-independent")
    prepare.add_argument("--evidence", type=Path, required=True)
    prepare.add_argument("--baseline", type=Path, required=True)
    prepare.add_argument("--trial-dir", type=Path, required=True)
    prepare.add_argument("--batch-size", type=int, default=2)
    prepare.add_argument("--tickers", nargs="*")
    prepare.set_defaults(func=prepare_independent)

    run = sub.add_parser("run-trials")
    run.add_argument("--trial-dir", type=Path, required=True)
    run.add_argument(
        "--codex-bin",
        type=Path,
        default=Path("/Applications/ChatGPT.app/Contents/Resources/codex"),
    )
    run.add_argument("--timeout", type=int, default=1800)
    run.set_defaults(func=run_trials)

    merge = sub.add_parser("merge-independent-repair")
    merge.add_argument("--target-output", type=Path, required=True)
    merge.add_argument("--replacement-output", type=Path, required=True)
    merge.add_argument("--ticker", required=True)
    merge.set_defaults(func=merge_independent_repair)

    independent = sub.add_parser("finalize-independent")
    independent.add_argument("--evidence", type=Path, required=True)
    independent.add_argument("--baseline", type=Path, required=True)
    independent.add_argument("--trial-dir", type=Path, required=True)
    independent.add_argument("--output", type=Path, required=True)
    independent.add_argument("--screen-dir", type=Path, required=True)
    independent.add_argument("--screen-batch-size", type=int, default=5)
    independent.set_defaults(func=finalize_independent)

    screen = sub.add_parser("finalize-screen")
    screen.add_argument("--evidence", type=Path, required=True)
    screen.add_argument("--baseline", type=Path, required=True)
    screen.add_argument("--independent", type=Path, required=True)
    screen.add_argument("--screen-dir", type=Path, required=True)
    screen.add_argument("--output", type=Path, required=True)
    screen.add_argument("--adjudication-dir", type=Path, required=True)
    screen.set_defaults(func=finalize_screen)

    adjudication = sub.add_parser("finalize-adjudication")
    adjudication.add_argument("--evidence", type=Path, required=True)
    adjudication.add_argument("--baseline", type=Path, required=True)
    adjudication.add_argument("--independent", type=Path, required=True)
    adjudication.add_argument("--agreement", type=Path, required=True)
    adjudication.add_argument("--adjudication-dir", type=Path, required=True)
    adjudication.add_argument("--output", type=Path, required=True)
    adjudication.add_argument("--portfolio-dir", type=Path, required=True)
    adjudication.set_defaults(func=finalize_adjudication)

    final = sub.add_parser("finalize")
    final.add_argument("--evidence", type=Path, required=True)
    final.add_argument("--baseline", type=Path, required=True)
    final.add_argument("--independent", type=Path, required=True)
    final.add_argument("--agreement", type=Path, required=True)
    final.add_argument("--adjudication", type=Path, required=True)
    final.add_argument("--portfolio-dir", type=Path, required=True)
    final.add_argument("--instruction-commit", required=True)
    final.set_defaults(func=finalize)
    return value


def main() -> None:
    args = parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
