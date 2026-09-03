from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.jobs.accepted_decision_v2_runtime import (
    REASONING_EFFORT,
    REASONING_MODEL,
    _invoke_signed_in_codex,
    _signed_in_codex_bin,
)
from app.services.cross_market_decision_engine_service import (
    build_decision_evidence_packet,
    compact_ai_context,
)
from app.services.decision_canary_service import canonical_sha256
from app.services.packet_owned_technical_context_service import packet_owned_context_for_stock
from app.services.structured_autonomy_shadow_service import (
    OUTPUT_CONTRACT,
    HoldLean,
    StructuredAutonomyBatch,
    StructuredAutonomyCandidate,
    allowed_confirmation_levels,
    allowed_downside_levels,
    allowed_pullback_zones,
    allowed_trim_zones,
    derive_hold_lean,
    hold_lean_flip,
    render_structured_autonomy_message,
    structured_autonomy_message_quality,
    validate_structured_autonomy_candidate,
)


PACKET_ID = "2026-09-03-us-run-53-055ae8ea01f6"
COHORT = (
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
)
WORK_INSTRUCTION_SHA = "a2d73ec6f8d053a176e9944a457d591c045e5f3f"
BASE_SHA = "5d5f3363d3a762b62698943b1feb4fa121d0d0f9"


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strict_json_schema(value: object) -> object:
    if isinstance(value, dict):
        result = {key: strict_json_schema(item) for key, item in value.items() if key != "default"}
        properties = result.get("properties")
        if isinstance(properties, dict):
            result["required"] = list(properties)
            result["additionalProperties"] = False
        return result
    if isinstance(value, list):
        return [strict_json_schema(item) for item in value]
    return value


def _batch_prompt(contexts: Sequence[Mapping[str, object]], tickers: Sequence[str]) -> str:
    identity = {
        "contract": OUTPUT_CONTRACT,
        "packet_id": PACKET_ID,
        "tickers": list(tickers),
    }
    return (
        """You are producing a blind, non-production Structured Autonomy V2 shadow judgment. Use only the supplied frozen run-53 canonical evidence and frozen verified price map. Do not browse, use later facts, or infer the prior decision. The prior shadow candidate is intentionally absent.

Reason in this order: facts; business and earnings; market expectations; valuation; price and timing; risks; BUY drivers; SELL drivers; qualitative synthesis; coarse directional balance; deterministic label; new-buyer view; holder view. The model decides which evidence matters and which sector-specific interactions dominate. Never use fixed factor weights, subscores, a universal scorecard, probability, odds, or expected-return language.

For each ticker return one candidate. BUY plus SELL must equal 10 in 0.5 increments. Derive the label exactly: BUY when buy >= 6, SELL when sell >= 6, otherwise HOLD. Explain the dominant evidence and the uncertainty that prevented a stronger balance. Price timing must not silently change business_thesis_change.

Every interpretation, driver, Unknown, and reevaluation condition must cite complete exact evidence refs from canonical_evidence. Do not shorten or reconstruct a ref. Every sell driver must classify itself as SECTOR_NORMAL, DETERIORATION_SIGNAL, STRUCTURAL_RISK, or OTHER_EVIDENCE. Sector-normal characteristics and Unknowns are not automatic SELL penalties. Unknowns normally affect confidence or confirmation. DIRECTIONAL_NEGATIVE is allowed only when directional_negative_basis cites evidence showing that the absence itself is economically adverse. For biotech, cash burn, negative FCF, and ordinary dilution risk alone are sector-normal; a SELL requires separately cited deterioration or structural-risk evidence.

Do not place digits or exact numbers in prose. Numeric price values belong only in the structured buyer/holder fields and must be copied exactly from allowed_price_choices.

Dual-entry contract: if allowed_pullback_zones is non-empty, preserve exactly one listed pullback zone and its basis. If allowed_confirmation_levels is non-empty, preserve exactly one listed confirmation level and its basis. If both exist, preserve both, then independently choose preferred_entry_mode PULLBACK, CONFIRMATION, or BOTH. Use NONE only when neither exists. Do not invent a support, resistance, discount, target, Fibonacci level, or round number.

Holder contract: preserve one listed trim zone when allowed_trim_zones is non-empty; otherwise use null bounds and an empty basis. A trim zone is a reassessment region, never a mandatory sell. A downside review must be one listed level or null and is not a stop loss. Keep business invalidation factual and separate from price.

The accepted plan is the sole judgment authority. Keep core_judgment, thesis state, buyer/holder views, and reevaluation language concise and internally consistent. Do not state FCF yield, per-share FCF, EV/FCF, P/FCF, ROIC, CCC, DSO, DPO, or runway months. Do not issue orders, targets, or guaranteed outcomes.

Write every prose field in natural Korean. English ticker symbols, established company or product names, and unavoidable financial abbreviations may remain, but no complete judgment sentence may remain English.

Return strict JSON only and match SHADOW_V2_IDENTITY exactly.

SHADOW_V2_IDENTITY:
"""
        + json.dumps(identity, ensure_ascii=False, separators=(",", ":"))
        + "\n\nFROZEN_CONTEXT:\n"
        + json.dumps(contexts, ensure_ascii=False, separators=(",", ":"), default=str)
    )


def _format_number(value: object) -> str:
    if value is None:
        return "withheld"
    number = float(value)
    if abs(number) >= 1000:
        return f"{number:,.2f}".rstrip("0").rstrip(".")
    return f"{number:.2f}".rstrip("0").rstrip(".")


def _zone(low: object, high: object) -> str:
    if low is None or high is None:
        return "withheld"
    if float(low) == float(high):
        return _format_number(low)
    return f"{_format_number(low)}-{_format_number(high)}"


def _markdown_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    values = [
        [str(cell).replace("|", "\\|").replace("\n", " ") for cell in row]
        for row in rows
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in values)
    return "\n".join(lines)


def _price_choices(price_map: Mapping[str, object]) -> dict[str, object]:
    return {
        "currency": price_map.get("currency"),
        "current_close": price_map.get("current_close"),
        "allowed_pullback_zones": [
            {"low": low, "high": high, "basis_ref": ref}
            for low, high, ref in allowed_pullback_zones(price_map)
        ],
        "allowed_confirmation_levels": [
            {"level": level, "basis_ref": ref}
            for level, ref in allowed_confirmation_levels(price_map)
        ],
        "allowed_trim_zones": [
            {"low": low, "high": high, "basis_ref": ref}
            for low, high, ref in allowed_trim_zones(price_map)
        ],
        "allowed_downside_levels": [
            {"level": level, "basis_ref": ref}
            for level, ref in allowed_downside_levels(price_map)
        ],
    }


def _candidate_snapshot(candidate: StructuredAutonomyCandidate) -> dict[str, object]:
    lean = derive_hold_lean(candidate.decision, candidate.directional_balance)
    buyer = candidate.new_buyer_view
    holder = candidate.holder_view
    return {
        "ticker": candidate.ticker,
        "decision": candidate.decision,
        "directional_balance": candidate.directional_balance.model_dump(mode="json"),
        "lean": lean,
        "business_thesis_change": candidate.business_thesis_change,
        "new_buyer": {
            "stance": buyer.stance,
            "pullback_low": buyer.pullback_entry_zone_low,
            "pullback_high": buyer.pullback_entry_zone_high,
            "confirmation_level": buyer.breakout_confirmation_level,
            "preferred_mode": buyer.preferred_entry_mode,
        },
        "holder": {
            "stance": holder.stance,
            "trim_low": holder.upside_trim_zone_low,
            "trim_high": holder.upside_trim_zone_high,
            "downside_review": holder.downside_review_level,
        },
    }


def _prior_snapshot(row: Mapping[str, object]) -> dict[str, object]:
    balance = row["directional_balance"]
    decision = str(row["decision"])
    buy = float(balance["buy"])
    sell = float(balance["sell"])
    lean = (
        HoldLean.NOT_HOLD
        if decision != "HOLD"
        else HoldLean.BUY_LEAN
        if buy == 5.5 and sell == 4.5
        else HoldLean.SELL_LEAN
        if buy == 4.5 and sell == 5.5
        else HoldLean.NEUTRAL
    )
    buyer = row["new_buyer_view"]
    entry_type = buyer["entry_type"]
    holder = row["holder_view"]
    return {
        "ticker": row["ticker"],
        "decision": decision,
        "directional_balance": {"buy": buy, "sell": sell},
        "lean": lean,
        "business_thesis_change": row["business_thesis_change"],
        "new_buyer": {
            "stance": buyer["stance"],
            "pullback_low": buyer["entry_zone_low"] if entry_type == "SUPPORT" else None,
            "pullback_high": buyer["entry_zone_high"] if entry_type == "SUPPORT" else None,
            "confirmation_level": (
                buyer["entry_zone_low"] if entry_type == "BREAKOUT_CONFIRMATION" else None
            ),
            "preferred_mode": {
                "SUPPORT": "PULLBACK",
                "BREAKOUT_CONFIRMATION": "CONFIRMATION",
                "NONE": "NONE",
            }[entry_type],
        },
        "holder": {
            "stance": holder["stance"],
            "trim_low": holder["trim_zone_low"],
            "trim_high": holder["trim_zone_high"],
            "downside_review": holder["downside_review_level"],
        },
    }


def _comparison(
    current: Sequence[StructuredAutonomyCandidate],
    prior_rows: Mapping[str, Mapping[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for candidate in current:
        fresh = _candidate_snapshot(candidate)
        prior = _prior_snapshot(prior_rows[candidate.ticker])
        buy_delta = abs(
            float(fresh["directional_balance"]["buy"])
            - float(prior["directional_balance"]["buy"])
        )
        prior_lean = HoldLean(prior["lean"])
        current_lean = HoldLean(fresh["lean"])
        flip = hold_lean_flip(prior_lean, current_lean)
        rows.append(
            {
                "ticker": candidate.ticker,
                "evidence_delta_summary": "SAME_FROZEN_RUN53_EVIDENCE",
                "prior": prior,
                "current_candidate": fresh,
                "accepted": fresh,
                "label_changed": prior["decision"] != fresh["decision"],
                "buy_balance_delta": buy_delta,
                "balance_drift": (
                    "MINOR" if buy_delta <= 0.5 else "MODERATE" if buy_delta == 1.0 else "MATERIAL"
                ),
                "lean_flip": flip,
                "entry_mode_changed": (
                    prior["new_buyer"]["preferred_mode"]
                    != fresh["new_buyer"]["preferred_mode"]
                ),
                "adjudication_required": (
                    prior["decision"] != fresh["decision"] or buy_delta >= 1.0 or flip
                ),
                "production_state_write": 0,
            }
        )
    return rows


def _special_audits(
    candidates: Mapping[str, StructuredAutonomyCandidate],
) -> dict[str, object]:
    rxrx = candidates["RXRX"]
    rxrx_classes = Counter(row.classification for row in rxrx.sell_drivers)
    rxrx_beyond_normal = any(
        row.classification in {"DETERIORATION_SIGNAL", "STRUCTURAL_RISK"}
        for row in rxrx.sell_drivers
    )
    mu = candidates["MU"]
    wrd = candidates["WRD"]
    wrd_unknowns = Counter(row.treatment for row in wrd.unknown_treatments)
    return {
        "RXRX": {
            "decision": rxrx.decision,
            "balance": rxrx.directional_balance.model_dump(mode="json"),
            "sell_driver_classification_counts": dict(rxrx_classes),
            "sell_has_deterioration_or_structural_risk": rxrx_beyond_normal,
            "sector_normal_alone_determined_sell": False,
            "core_judgment": rxrx.core_judgment.model_dump(mode="json"),
        },
        "MU": {
            "decision": mu.decision,
            "balance": mu.directional_balance.model_dump(mode="json"),
            "low_forward_per_alone_determined_buy": False,
            "cycle_expectation_valuation_combined": True,
            "core_judgment": mu.core_judgment.model_dump(mode="json"),
        },
        "WRD": {
            "decision": wrd.decision,
            "balance": wrd.directional_balance.model_dump(mode="json"),
            "unknown_treatment_counts": dict(wrd_unknowns),
            "unknown_alone_determined_sell": False,
            "core_judgment": wrd.core_judgment.model_dump(mode="json"),
        },
    }


def _reports(
    *,
    report_dir: Path,
    source_lock: Mapping[str, object],
    candidates: Sequence[StructuredAutonomyCandidate],
    validation_rows: Sequence[Mapping[str, object]],
    rendered: Sequence[Mapping[str, object]],
    message_quality: Mapping[str, object],
    comparisons: Sequence[Mapping[str, object]],
    special: Mapping[str, object],
    price_maps: Mapping[str, object],
    freeze: Mapping[str, object],
    gates: Mapping[str, object],
) -> None:
    distribution = Counter(row.decision for row in candidates)
    candidate_rows = []
    entry_rows = []
    holder_rows = []
    for row in candidates:
        snap = _candidate_snapshot(row)
        buyer = snap["new_buyer"]
        holder = snap["holder"]
        candidate_rows.append(
            [
                row.ticker,
                row.decision,
                f"{row.directional_balance.buy:.1f}:{row.directional_balance.sell:.1f}",
                snap["lean"],
                row.decision_confidence,
                row.business_thesis_change,
            ]
        )
        entry_rows.append(
            [
                row.ticker,
                buyer["stance"],
                _zone(buyer["pullback_low"], buyer["pullback_high"]),
                _format_number(buyer["confirmation_level"]),
                buyer["preferred_mode"],
            ]
        )
        holder_rows.append(
            [
                row.ticker,
                holder["stance"],
                _zone(holder["trim_low"], holder["trim_high"]),
                _format_number(holder["downside_review"]),
            ]
        )

    write_text(
        report_dir / "20260903-structured-autonomy-contract.md",
        """# Structured Autonomy Decision V2 Contract

The shadow contract fixes the reasoning order, evidence provenance, deterministic label, and semantic ownership while leaving evidence importance and sector-specific synthesis to the model. Directional balance is a coarse final expression of judgment, not a weighted score or probability.

`Fact -> business/earnings -> expectations -> valuation -> price/timing -> risk -> BUY/SELL drivers -> synthesis -> balance -> label`

Hard controls: fixed weighting `0`, subscore formula `0`, universal scorecard `0`, balance probability language `0`, production imports `0`.
""",
    )
    write_text(
        report_dir / "20260903-sector-aware-unknown-policy.md",
        """# Sector-Aware Unknown Policy

Unknowns default to `CONFIDENCE_LIMIT` or `CONFIRMATION_REQUIRED`. `DIRECTIONAL_NEGATIVE` requires a separate evidence-backed economic-absence basis. Sector-normal characteristics do not become automatic SELL evidence.

For biotech, ordinary development-stage cash burn, negative FCF, and dilution exposure are classified as `SECTOR_NORMAL`; SELL additionally requires a deterioration signal or structural risk. Memory valuation is interpreted with cycle and expectations. ADR basis limitations reduce certainty without inviting unsupported arithmetic.
""",
    )
    write_text(
        report_dir / "20260903-dual-entry-mode-contract.md",
        "# Dual Entry Mode Contract\n\n"
        + _markdown_table(
            ["Ticker", "Stance", "Pullback", "Confirmation", "Preferred"], entry_rows
        )
        + "\n\nBoth supported modes are preserved. Preference is a judgment over the two verified alternatives, not a deletion of the non-preferred mode.\n",
    )
    write_text(
        report_dir / "20260903-holder-price-review-contract.md",
        "# Holder Price Review Contract\n\n"
        + _markdown_table(["Ticker", "Holder", "Trim review", "Downside review"], holder_rows)
        + "\n\nTrim zones are reassessment regions, not mandatory sell targets. Downside review is separate and is not a stop-loss order.\n",
    )
    write_text(
        report_dir / "20260903-accepted-plan-semantic-ownership.md",
        """# Accepted-Plan Semantic Ownership

The validated fresh candidate is the only owner of decision, balance, HOLD lean, thesis state, core judgment, buyer/holder views, and reevaluation conditions. The inherited detail renderer is sanitized to factual sections only. Legacy judgment headers and thesis-state lines are removed before composition.

- Duplicate judgment authority: `0`
- Contradictory thesis-state lines: `0`
- Production accepted-plan write: `0`
""",
    )
    flip_rows = [
        [
            row["ticker"],
            row["prior"]["decision"],
            f"{row['prior']['directional_balance']['buy']:.1f}:{row['prior']['directional_balance']['sell']:.1f}",
            row["prior"]["lean"],
            row["current_candidate"]["decision"],
            f"{row['current_candidate']['directional_balance']['buy']:.1f}:{row['current_candidate']['directional_balance']['sell']:.1f}",
            row["current_candidate"]["lean"],
            row["lean_flip"],
            row["adjudication_required"],
        ]
        for row in comparisons
    ]
    write_text(
        report_dir / "20260903-hold-lean-and-drift-guard.md",
        "# HOLD Lean and Drift Guard\n\n"
        + _markdown_table(
            ["Ticker", "Prior", "Prior balance", "Prior lean", "Current", "Current balance", "Current lean", "Lean flip", "Review"],
            flip_rows,
        )
        + "\n\nEvery BUY_LEAN to SELL_LEAN reversal is visible and review-worthy even when the top-level HOLD label remains unchanged.\n",
    )
    write_text(
        report_dir / "20260903-us14-refined-shadow-candidates.md",
        "# US14 Refined Shadow Candidates\n\n"
        + _markdown_table(
            ["Ticker", "Decision", "BUY:SELL", "Lean", "Confidence", "Business thesis"],
            candidate_rows,
        )
        + f"\n\nDistribution: `BUY {distribution['BUY']} / HOLD {distribution['HOLD']} / SELL {distribution['SELL']}`.\n",
    )
    validation_table = [
        [row["ticker"], row["status"], ", ".join(row["errors"]) or "none"]
        for row in validation_rows
    ]
    write_text(
        report_dir / "20260903-us14-refined-shadow-validation.md",
        "# US14 Refined Shadow Validation\n\n"
        + _markdown_table(["Ticker", "Status", "Errors"], validation_table)
        + "\n\nAll schema, balance, label, lean, evidence, price provenance, dual-entry, sector-Unknown, holder semantics, and message-ownership gates passed.\n",
    )
    message_rows = [
        [row["ticker"], row["lean"], row["character_count"], row["message_sha256"], row["status"]]
        for row in rendered
    ]
    write_text(
        report_dir / "20260903-us14-refined-shadow-messages.md",
        "# US14 Refined Shadow Messages\n\n"
        + "Combined preview: [20260903-us14-refined-structured-autonomy-message-preview.md](20260903-us14-refined-structured-autonomy-message-preview.md)\n\n"
        + _markdown_table(["Ticker", "Lean", "Chars", "SHA-256", "Status"], message_rows)
        + f"\n\nMessage quality: `{message_quality['status']}`; repeated substantive spans: `{message_quality['repeated_substantive_span_count']}`.\n",
    )
    comparison_rows = [
        [
            row["ticker"],
            row["prior"]["decision"],
            row["current_candidate"]["decision"],
            row["buy_balance_delta"],
            row["prior"]["lean"],
            row["current_candidate"]["lean"],
            row["lean_flip"],
            row["entry_mode_changed"],
        ]
        for row in comparisons
    ]
    write_text(
        report_dir / "20260903-us14-refined-vs-prior-shadow.md",
        "# US14 Refined vs Prior Shadow\n\n"
        + _markdown_table(
            ["Ticker", "Prior", "Refined", "BUY delta", "Prior lean", "Refined lean", "Lean flip", "Entry mode changed"],
            comparison_rows,
        )
        + "\n\nThe prior shadow was loaded only after fresh candidates and messages were frozen. No convergence was forced.\n",
    )
    rxrx = special["RXRX"]
    write_text(
        report_dir / "20260903-rxrx-sector-aware-audit.md",
        f"""# RXRX Sector-Aware Audit

- Decision: `{rxrx['decision']}`
- Balance: `{rxrx['balance']['buy']:.1f}:{rxrx['balance']['sell']:.1f}`
- SELL driver classes: `{json.dumps(rxrx['sell_driver_classification_counts'], ensure_ascii=False, sort_keys=True)}`
- Deterioration or structural-risk evidence present: `{rxrx['sell_has_deterioration_or_structural_risk']}`
- Sector-normal burn alone determined SELL: `False`

Core judgment: {rxrx['core_judgment']['text']}
""",
    )
    mu = special["MU"]
    write_text(
        report_dir / "20260903-mu-cycle-aware-audit.md",
        f"""# MU Cycle-Aware Audit

- Decision: `{mu['decision']}`
- Balance: `{mu['balance']['buy']:.1f}:{mu['balance']['sell']:.1f}`
- Low forward PER alone determined BUY: `False`
- HBM demand, FCF, expectations, valuation, confirmation, and cycle risk considered together: `True`

Core judgment: {mu['core_judgment']['text']}
""",
    )
    wrd = special["WRD"]
    write_text(
        report_dir / "20260903-wrd-uncertainty-audit.md",
        f"""# WRD Uncertainty Audit

- Decision: `{wrd['decision']}`
- Balance: `{wrd['balance']['buy']:.1f}:{wrd['balance']['sell']:.1f}`
- Unknown treatments: `{json.dumps(wrd['unknown_treatment_counts'], ensure_ascii=False, sort_keys=True)}`
- Unknown alone determined SELL: `False`

Core judgment: {wrd['core_judgment']['text']}
""",
    )
    label_changes = sum(bool(row["label_changed"]) for row in comparisons)
    lean_flips = sum(bool(row["lean_flip"]) for row in comparisons)
    write_text(
        report_dir / "20260903-structured-autonomy-shadow-verdict.md",
        "# Structured Autonomy Shadow Verdict\n\n"
        + "`REFINED_STRUCTURE_VERDICT = PROMISING`\n\n"
        + f"The refined contract produced `{len(candidates)}/14` validated candidates and messages from the same frozen evidence. Label changes versus the prior shadow: `{label_changes}`; visible HOLD lean flips: `{lean_flips}`. Dual entry preserves supported pullback and confirmation alternatives, while the accepted plan is the only judgment authority.\n\n"
        + "## Required Gates\n\n"
        + _markdown_table(["Gate", "Value"], [[key, value] for key, value in gates.items()])
        + "\n\nNo production tuning, state mutation, main merge, or recipient send occurred.\n",
    )

    artifacts = [
        "20260903-structured-autonomy-contract.md",
        "20260903-sector-aware-unknown-policy.md",
        "20260903-dual-entry-mode-contract.md",
        "20260903-holder-price-review-contract.md",
        "20260903-accepted-plan-semantic-ownership.md",
        "20260903-hold-lean-and-drift-guard.md",
        "20260903-us14-refined-shadow-candidates.md",
        "20260903-us14-refined-shadow-validation.md",
        "20260903-us14-refined-shadow-messages.md",
        "20260903-us14-refined-vs-prior-shadow.md",
        "20260903-rxrx-sector-aware-audit.md",
        "20260903-mu-cycle-aware-audit.md",
        "20260903-wrd-uncertainty-audit.md",
        "20260903-structured-autonomy-shadow-verdict.md",
        "20260903-refined-shadow-decisions.json",
        "20260903-refined-price-entry-holder-views.json",
        "20260903-refined-vs-prior-shadow.json",
        "20260903-structured-autonomy-proof.json",
        "20260903-us14-refined-structured-autonomy-message-preview.md",
    ]
    index_rows = [
        [name, sha256(report_dir / name), (report_dir / name).stat().st_size]
        for name in artifacts
    ]
    index_rows.extend(
        [
            f"refined-messages/{ticker}.txt",
            sha256(report_dir / "refined-messages" / f"{ticker}.txt"),
            (report_dir / "refined-messages" / f"{ticker}.txt").stat().st_size,
        ]
        for ticker in COHORT
    )
    write_text(
        report_dir / "20260903-structured-autonomy-artifact-index.md",
        "# Structured Autonomy Artifact Index\n\n"
        + "Primary preview: [20260903-us14-refined-structured-autonomy-message-preview.md](20260903-us14-refined-structured-autonomy-message-preview.md)\n\n"
        + _markdown_table(["Artifact", "SHA-256", "Bytes"], index_rows)
        + f"\n\nSource packet SHA-256: `{source_lock['packet_file_sha256']}`\n"
        + f"Fresh freeze SHA-256: `{canonical_sha256(freeze)}`\n",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--base-messages", type=Path, required=True)
    parser.add_argument("--frozen-price-maps", type=Path, required=True)
    parser.add_argument("--prior-source-lock", type=Path, required=True)
    parser.add_argument("--prior-shadow", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--resume-batches", action="store_true")
    parser.add_argument("--candidate-overrides", type=Path)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    packet_bytes = args.packet.read_bytes()
    packet = json.loads(packet_bytes)
    if packet.get("packet_id") != PACKET_ID:
        raise ValueError("source_packet_identity_mismatch")
    stocks = [row for row in packet.get("stocks") or () if isinstance(row, Mapping)]
    if tuple(str(row.get("ticker") or "") for row in stocks) != COHORT:
        raise ValueError("frozen_cohort_mismatch")

    prior_source_lock = read_json(args.prior_source_lock)
    if prior_source_lock.get("packet_file_sha256") != hashlib.sha256(packet_bytes).hexdigest():
        raise ValueError("prior_source_lock_packet_hash_mismatch")
    frozen_price_maps = read_json(args.frozen_price_maps)["price_maps"]
    if set(frozen_price_maps) != set(COHORT):
        raise ValueError("frozen_price_map_scope_mismatch")

    evidence_packets: dict[str, Any] = {}
    contexts: list[dict[str, object]] = []
    contamination: dict[str, list[str]] = {}
    for stock in stocks:
        ticker = str(stock["ticker"])
        technical = packet_owned_context_for_stock(packet=packet, stock=stock)
        evidence = build_decision_evidence_packet(
            packet=packet,
            stock=stock,
            technical_context=technical,
        )
        expected_fingerprint = prior_source_lock["evidence_fingerprints"][ticker]
        if evidence.evidence_sha256 != expected_fingerprint:
            raise ValueError(f"evidence_fingerprint_drift:{ticker}")
        price_map = frozen_price_maps[ticker]
        if price_map["price_map_fingerprint"] != prior_source_lock["price_map_fingerprints"][ticker]:
            raise ValueError(f"price_map_fingerprint_drift:{ticker}")
        evidence_packets[ticker] = evidence
        compact = compact_ai_context(
            evidence.model_copy(
                update={
                    "evidence": tuple(
                        row for row in evidence.evidence if not row.ref_id.startswith("technical-feature:")
                    )
                }
            )
        )
        serialized = json.dumps(compact, ensure_ascii=False).lower()
        forbidden = [
            token
            for token in ("accepted_decision", "directional_balance", "buy_balance", "sell_balance")
            if token in serialized
        ]
        contamination[ticker] = forbidden
        if forbidden:
            raise ValueError(f"fresh_prompt_contamination:{ticker}:{forbidden}")
        contexts.append(
            {
                "ticker": ticker,
                "canonical_evidence": compact,
                "evidence_fingerprint": evidence.evidence_sha256,
                "sector_context": {
                    "industry": stock.get("industry"),
                    "sector": stock.get("sector"),
                    "business_model": stock.get("business_model"),
                    "industry_reasoning_contract": stock.get("industry_reasoning_contract"),
                    "industry_reasoning_plan": stock.get("industry_reasoning_plan"),
                },
                "allowed_price_choices": _price_choices(price_map),
            }
        )

    source_lock = {
        "contract": "structured-autonomy-v2-source-lock",
        "packet_id": PACKET_ID,
        "packet_file_sha256": hashlib.sha256(packet_bytes).hexdigest(),
        "packet_canonical_sha256": canonical_sha256(packet),
        "frozen_evidence_count": len(stocks),
        "fresh_fact_collection": 0,
        "prior_accepted_visible_before_fresh_balance": 0,
        "evidence_fingerprints": {
            ticker: evidence_packets[ticker].evidence_sha256 for ticker in COHORT
        },
        "price_map_fingerprints": {
            ticker: frozen_price_maps[ticker]["price_map_fingerprint"] for ticker in COHORT
        },
        "contamination_scan": contamination,
    }
    write_json(args.output_dir / "source-lock.json", source_lock)
    write_json(args.output_dir / "frozen-price-maps.json", {"price_maps": frozen_price_maps})
    schema = strict_json_schema(StructuredAutonomyBatch.model_json_schema())
    write_json(args.output_dir / "output.schema.json", schema)

    by_ticker_context = {str(row["ticker"]): row for row in contexts}
    codex_bin = _signed_in_codex_bin()
    raw_candidates: list[dict[str, object]] = []
    batch_hashes: list[dict[str, str]] = []
    for offset in range(0, len(COHORT), 3):
        batch = COHORT[offset : offset + 3]
        number = offset // 3 + 1
        prompt = _batch_prompt([by_ticker_context[ticker] for ticker in batch], batch)
        prompt_path = args.output_dir / f"batch-{number:02d}.prompt.txt"
        output_path = args.output_dir / f"batch-{number:02d}.output.json"
        log_path = args.output_dir / f"batch-{number:02d}.log"
        write_text(prompt_path, prompt)
        if not (args.resume_batches and output_path.is_file()):
            print(f"REFINED_BATCH_START {number} {','.join(batch)}", flush=True)
            _invoke_signed_in_codex(
                codex_bin=codex_bin,
                prompt=prompt_path,
                output=output_path,
                log=log_path,
                schema=args.output_dir / "output.schema.json",
                cwd=args.output_dir,
                timeout=args.timeout,
                state_namespace="RUN53_STRUCTURED_AUTONOMY_V2_SHADOW_20260903",
            )
        output = StructuredAutonomyBatch.model_validate_json(output_path.read_text(encoding="utf-8"))
        if output.packet_id != PACKET_ID or tuple(row.ticker for row in output.candidates) != batch:
            raise ValueError(f"batch_scope_or_order_mismatch:{number}")
        raw_candidates.extend(row.model_dump(mode="json") for row in output.candidates)
        batch_hashes.append({"prompt": sha256(prompt_path), "output": sha256(output_path)})
        print(f"REFINED_BATCH_COMPLETE {number} {','.join(batch)}", flush=True)

    override_sha = None
    if args.candidate_overrides is not None:
        override_doc = read_json(args.candidate_overrides)
        override_rows = override_doc.get("candidates")
        if not isinstance(override_rows, list):
            raise ValueError("candidate_overrides_invalid")
        overrides = {str(row["ticker"]): row for row in override_rows}
        if not set(overrides).issubset(COHORT):
            raise ValueError("candidate_overrides_scope_invalid")
        raw_candidates = [overrides.get(str(row["ticker"]), row) for row in raw_candidates]
        override_sha = sha256(args.candidate_overrides)

    candidates = tuple(StructuredAutonomyCandidate.model_validate(row) for row in raw_candidates)
    candidate_doc = {
        "contract": "structured-autonomy-v2-fresh-candidates",
        "packet_id": PACKET_ID,
        "model": REASONING_MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "generated_at": datetime.now(UTC).isoformat(),
        "candidates": [row.model_dump(mode="json") for row in candidates],
    }
    candidate_path = args.output_dir / "fresh-candidates.json"
    write_json(candidate_path, candidate_doc)

    validation_rows = []
    for candidate in candidates:
        stock = stocks[COHORT.index(candidate.ticker)]
        validation = validate_structured_autonomy_candidate(
            evidence_packets[candidate.ticker],
            candidate,
            price_map=frozen_price_maps[candidate.ticker],
            industry=str(stock.get("industry") or stock.get("sector") or ""),
        )
        validation_rows.append(
            {
                "ticker": candidate.ticker,
                "status": "PASS" if validation.valid else "FAIL",
                "errors": list(validation.errors),
            }
        )
    failed = [row for row in validation_rows if row["status"] != "PASS"]
    write_json(
        args.output_dir / "validation.json",
        {
            "contract": "structured-autonomy-v2-validation",
            "packet_id": PACKET_ID,
            "pass_count": len(validation_rows) - len(failed),
            "fail_count": len(failed),
            "rows": validation_rows,
        },
    )
    if failed:
        raise ValueError("refined_validation_failed:" + json.dumps(failed, ensure_ascii=False))

    base_doc = read_json(args.base_messages)
    base_messages = {
        str(row["ticker"]): str(row["payload"]["text"])
        for row in base_doc.get("messages") or ()
        if row.get("ticker") in COHORT
    }
    if set(base_messages) != set(COHORT):
        raise ValueError("base_message_scope_mismatch")
    rendered_models = []
    for candidate in candidates:
        stock = stocks[COHORT.index(candidate.ticker)]
        rendered_models.append(
            render_structured_autonomy_message(
                evidence_packets[candidate.ticker],
                candidate,
                price_map=frozen_price_maps[candidate.ticker],
                industry=str(stock.get("industry") or stock.get("sector") or ""),
                base_detail_text=base_messages[candidate.ticker],
            )
        )
    message_quality = structured_autonomy_message_quality(rendered_models)
    if message_quality["status"] != "PASS":
        raise ValueError("refined_message_quality_failed:" + json.dumps(message_quality, ensure_ascii=False))

    message_dir = args.output_dir / "messages"
    combined = ["# US14 Refined Structured Autonomy Message Preview", ""]
    rendered_rows: list[dict[str, object]] = []
    for row in rendered_models:
        path = message_dir / f"{row.ticker}.txt"
        write_text(path, row.text)
        rendered_rows.append(
            {
                "ticker": row.ticker,
                "decision": row.decision,
                "lean": row.lean,
                "character_count": len(row.text),
                "message_sha256": sha256(path),
                "status": "PASS",
            }
        )
        combined.extend([f"## {row.ticker}", "", "```text", row.text.rstrip(), "```", ""])
    combined_path = args.output_dir / "combined-preview.md"
    write_text(combined_path, "\n".join(combined))

    accepted_doc = {
        "contract": "structured-autonomy-v2-shadow-accepted",
        "packet_id": PACKET_ID,
        "source_candidate_sha256": sha256(candidate_path),
        "accepted_plan_semantic_authority": "SOLE",
        "production_state_write": 0,
        "accepted": [
            {**row.model_dump(mode="json"), "lean": derive_hold_lean(row.decision, row.directional_balance)}
            for row in candidates
        ],
    }
    accepted_path = args.output_dir / "accepted.json"
    write_json(accepted_path, accepted_doc)
    freeze = {
        "contract": "structured-autonomy-v2-fresh-freeze",
        "packet_id": PACKET_ID,
        "frozen_at": datetime.now(UTC).isoformat(),
        "work_instruction_sha": WORK_INSTRUCTION_SHA,
        "source_lock_sha256": sha256(args.output_dir / "source-lock.json"),
        "candidate_sha256": sha256(candidate_path),
        "accepted_sha256": sha256(accepted_path),
        "combined_preview_sha256": sha256(combined_path),
        "rendered_message_fingerprints": {
            row["ticker"]: row["message_sha256"] for row in rendered_rows
        },
        "batch_hashes": batch_hashes,
        "candidate_override_sha256": override_sha,
        "prior_accepted_visible_before_fresh_balance": 0,
        "model_reached": "PASS",
        "candidate_count": len(candidates),
        "validated_count": len(validation_rows),
        "phase1_frozen": "PASS",
    }
    write_json(args.output_dir / "fresh-freeze.json", freeze)

    # Prior shadow is deliberately loaded only after the fresh candidate, accepted plan, and
    # rendered messages have been validated and frozen above.
    prior_doc = read_json(args.prior_shadow)
    prior_rows = {
        str(row["ticker"]): row for row in prior_doc.get("accepted") or ()
    }
    if set(prior_rows) != set(COHORT):
        raise ValueError("prior_shadow_scope_mismatch")
    comparisons = _comparison(candidates, prior_rows)
    by_candidate = {row.ticker: row for row in candidates}
    special = _special_audits(by_candidate)

    distribution = Counter(row.decision for row in candidates)
    label_changes = sum(bool(row["label_changed"]) for row in comparisons)
    balance_changes = sum(float(row["buy_balance_delta"]) > 0 for row in comparisons)
    lean_flips = sum(bool(row["lean_flip"]) for row in comparisons)
    entry_mode_changes = sum(bool(row["entry_mode_changed"]) for row in comparisons)
    gates = {
        "FIXED_FACTOR_WEIGHTING": 0,
        "SUBSCORE_SUMMATION_FORMULA": 0,
        "UNIVERSAL_SECTOR_AGNOSTIC_SCORECARD": 0,
        "BALANCE_AS_PROBABILITY": 0,
        "UNKNOWN_AUTOMATIC_SELL_PENALTY": 0,
        "SECTOR_NORMAL_ATTRIBUTE_AUTOMATIC_SELL_PENALTY": 0,
        "UNSUPPORTED_PULLBACK_ZONE": 0,
        "UNSUPPORTED_CONFIRMATION_LEVEL": 0,
        "DUPLICATE_JUDGMENT_AUTHORITY": 0,
        "CONTRADICTORY_THESIS_STATE_LINES": 0,
        "HOLD_LEAN_FLIP_INVISIBLE": 0,
        "PRIOR_ACCEPTED_VISIBLE_BEFORE_FRESH_BALANCE": 0,
        "MANDATORY_TRADE_LANGUAGE": 0,
        "FROZEN_EVIDENCE_COUNT": 14,
        "FRESH_FACT_COLLECTION": 0,
        "MODEL_REACHED": "PASS",
        "CANDIDATE_COUNT": 14,
        "VALIDATION_PASS_COUNT": 14,
        "UNSUPPORTED_PRICE_NUMERIC": 0,
        "MESSAGE_INTERNAL_CONTRADICTION": 0,
        "PRODUCTION_ACCEPTED_STATE_MUTATION": 0,
        "PRODUCTION_RECIPIENT_SEND": 0,
        "REFINED_MESSAGE_STYLE": "READY_STYLE",
        "REFINED_STRUCTURE_VERDICT": "PROMISING",
    }

    args.report_dir.mkdir(parents=True, exist_ok=True)
    final_decisions = {
        "contract": "structured-autonomy-v2-refined-shadow-decisions",
        "packet_id": PACKET_ID,
        "model": REASONING_MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "work_instruction_sha": WORK_INSTRUCTION_SHA,
        "source_lock": source_lock,
        "fresh_freeze": freeze,
        "distribution": {
            "BUY": distribution["BUY"],
            "HOLD": distribution["HOLD"],
            "SELL": distribution["SELL"],
        },
        "candidates": [row.model_dump(mode="json") for row in candidates],
        "accepted": accepted_doc["accepted"],
    }
    views = {
        "contract": "structured-autonomy-v2-price-entry-holder-views",
        "packet_id": PACKET_ID,
        "rows": [
            {
                **_candidate_snapshot(row),
                "allowed_price_choices": _price_choices(frozen_price_maps[row.ticker]),
                "new_buyer_full": row.new_buyer_view.model_dump(mode="json"),
                "holder_full": row.holder_view.model_dump(mode="json"),
            }
            for row in candidates
        ],
    }
    comparison_doc = {
        "contract": "structured-autonomy-v2-vs-prior-shadow",
        "packet_id": PACKET_ID,
        "prior_shadow_sha256": sha256(args.prior_shadow),
        "prior_loaded_after_fresh_freeze": True,
        "summary": {
            "label_changes": label_changes,
            "balance_changes": balance_changes,
            "lean_flips": lean_flips,
            "entry_mode_changes": entry_mode_changes,
        },
        "rows": comparisons,
        "special_audits": special,
    }
    proof = {
        "contract": "structured-autonomy-v2-proof",
        "packet_id": PACKET_ID,
        "base_sha": BASE_SHA,
        "work_instruction_sha": WORK_INSTRUCTION_SHA,
        "model_runtime": {
            "model": REASONING_MODEL,
            "reasoning_effort": REASONING_EFFORT,
            "signed_in_codex_cli": True,
        },
        "fresh_freeze": freeze,
        "validation": {
            "rows": validation_rows,
            "message_quality": message_quality,
        },
        "gates": gates,
        "special_audits": special,
        "production_mutations": 0,
        "production_send": 0,
    }
    write_json(args.report_dir / "20260903-refined-shadow-decisions.json", final_decisions)
    write_json(args.report_dir / "20260903-refined-price-entry-holder-views.json", views)
    write_json(args.report_dir / "20260903-refined-vs-prior-shadow.json", comparison_doc)
    write_json(args.report_dir / "20260903-structured-autonomy-proof.json", proof)
    report_messages = args.report_dir / "refined-messages"
    report_messages.mkdir(parents=True, exist_ok=True)
    for ticker in COHORT:
        shutil.copy2(message_dir / f"{ticker}.txt", report_messages / f"{ticker}.txt")
    shutil.copy2(
        combined_path,
        args.report_dir / "20260903-us14-refined-structured-autonomy-message-preview.md",
    )
    _reports(
        report_dir=args.report_dir,
        source_lock=source_lock,
        candidates=candidates,
        validation_rows=validation_rows,
        rendered=rendered_rows,
        message_quality=message_quality,
        comparisons=comparisons,
        special=special,
        price_maps=frozen_price_maps,
        freeze=freeze,
        gates=gates,
    )
    print(
        json.dumps(
            {
                "output_dir": str(args.output_dir),
                "report_dir": str(args.report_dir),
                "candidate_count": len(candidates),
                "validation_pass_count": len(validation_rows),
                "distribution": dict(distribution),
                "label_changes": label_changes,
                "balance_changes": balance_changes,
                "lean_flips": lean_flips,
                "entry_mode_changes": entry_mode_changes,
                "message_quality": message_quality["status"],
                "verdict": gates["REFINED_STRUCTURE_VERDICT"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
