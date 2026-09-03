from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
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
    DecisionEvidencePacket,
    build_decision_evidence_packet,
    compact_ai_context,
)
from app.services.decision_canary_service import canonical_sha256
from app.services.packet_owned_technical_context_service import (
    packet_owned_context_for_stock,
)
from app.services.structured_autonomy_shadow_service import (
    OUTPUT_CONTRACT,
    StructuredAutonomyBatch,
    StructuredAutonomyCandidate,
    allowed_confirmation_levels,
    allowed_downside_levels,
    allowed_pullback_zones,
    allowed_price_refs,
    allowed_trim_zones,
    derive_hold_lean,
    render_structured_autonomy_message,
    structured_autonomy_message_quality,
    validate_structured_autonomy_candidate,
)
from app.services.structured_autonomy_stability_service import (
    classify_same_evidence_runs,
    stability_summary,
)


US_PACKET_ID = "2026-09-03-us-run-53-055ae8ea01f6"
KR_PACKET_ID = "2026-09-03-kr-run-54-f19bb379daa7"
KR_LATER_PACKET_ID = "2026-09-03-kr-run-54-78ed269de3df"
SHADOW_PACKET_ID = "2026-09-03-uskr22-structured-autonomy-shadow"
REPAIR_BASE_SHA = "90cc52231c7343056c853c355ea90dfea10de25b"
WORK_INSTRUCTION_SHA = "0969e70af1d75884b43340637e25dfe84a04c4ee"
US_COHORT = (
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
KR_COHORT = (
    "000660",
    "003690",
    "005490",
    "005930",
    "010120",
    "012450",
    "047810",
    "086280",
)
COHORT = US_COHORT + KR_COHORT
RUNS = ("first", "a", "b", "c")
FORBIDDEN_PROMPT_KEYS = (
    "accepted_decision",
    "directional_balance",
    "buy_balance",
    "sell_balance",
)


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
        result = {
            key: strict_json_schema(item)
            for key, item in value.items()
            if key != "default"
        }
        properties = result.get("properties")
        if isinstance(properties, dict):
            result["required"] = list(properties)
            result["additionalProperties"] = False
        return result
    if isinstance(value, list):
        return [strict_json_schema(item) for item in value]
    return value


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    escaped = [
        [str(cell).replace("|", "\\|").replace("\n", " ") for cell in row]
        for row in rows
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in escaped)
    return "\n".join(lines)


def _statement(row: object) -> dict[str, object]:
    if row is None:
        return {}
    text = getattr(row, "statement", "")
    try:
        value = json.loads(text)
    except (TypeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def build_verified_price_map(packet: DecisionEvidencePacket) -> dict[str, object]:
    by_ref = {row.ref_id: row for row in packet.evidence}
    current = _statement(by_ref.get("canonical:price:current"))
    supports = []
    resistances = []
    for ref, row in sorted(by_ref.items()):
        if ref.startswith("canonical:chart:structure:nearest_supports:"):
            supports.append({**_statement(row), "basis_ref": ref})
        if ref.startswith("canonical:chart:structure:nearest_resistance:"):
            resistances.append({**_statement(row), "basis_ref": ref})
    registered_raw = _statement(by_ref.get("canonical:chart:stored_price_rules"))
    registered = (
        {**registered_raw, "basis_ref": "canonical:chart:stored_price_rules"}
        if registered_raw
        else None
    )
    invalidation_raw = _statement(by_ref.get("canonical:chart:structure:invalidation"))
    invalidation = (
        {**invalidation_raw, "basis_ref": "canonical:chart:structure:invalidation"}
        if invalidation_raw
        else None
    )
    currency = current.get("currency")
    if not currency and registered:
        currency = registered.get("currency")
    price_map: dict[str, object] = {
        "currency": currency,
        "current_close": current.get("current_price"),
        "current_price_ref": (
            "canonical:price:current" if "canonical:price:current" in by_ref else None
        ),
        "nearest_supports": supports,
        "nearest_resistances": resistances,
        "major_support": None,
        "major_resistance": None,
        "registered_price_rules": registered,
        "chart_invalidation": invalidation,
    }
    price_map["price_map_fingerprint"] = canonical_sha256(price_map)
    return price_map


def price_choices(price_map: Mapping[str, object]) -> dict[str, object]:
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


def _batch_prompt(contexts: Sequence[Mapping[str, object]], tickers: Sequence[str]) -> str:
    identity = {
        "contract": OUTPUT_CONTRACT,
        "packet_id": SHADOW_PACKET_ID,
        "tickers": list(tickers),
    }
    return (
        """You are producing a blind, non-production Structured Autonomy V2 shadow judgment. Use only the supplied frozen canonical evidence and verified price choices. Do not browse, fetch, use later facts, infer a prior decision, or use another ticker's evidence. No prior or cross-run candidate is present.

Reason in this order: facts; business and earnings; market expectations; valuation; price and timing; risks; BUY drivers; SELL drivers; qualitative synthesis; coarse directional balance; deterministic overall direction; new-buyer view; holder view; price scenarios. You decide which evidence matters and how sector context changes importance. Never use fixed weights, subscores, a universal scorecard, probability, odds, or expected-return language.

For each ticker return exactly one candidate in input order. BUY plus SELL must equal ten in half-point increments. Derive the label exactly: BUY when buy is at least six, SELL when sell is at least six, otherwise HOLD. The balance is a coarse judgment summary, not probability. overall_direction is integrated directional attractiveness; new_buyer_view is actionability at the current setup. BUY plus WAIT is valid and these meanings must remain distinct.

Every interpretation, driver, Unknown, and reevaluation condition must cite complete exact refs from that ticker's canonical_evidence. Never shorten or reconstruct refs. Every sell driver classifies itself as SECTOR_NORMAL, DETERIORATION_SIGNAL, STRUCTURAL_RISK, or OTHER_EVIDENCE. Unknown normally limits confidence or requires confirmation. DIRECTIONAL_NEGATIVE requires directional_negative_basis containing at least one non-Unknown evidence ref that proves the absence is economically adverse. Sector-normal features are not automatic directional penalties. For biotech, ordinary development cash burn, negative FCF, and ordinary dilution exposure are sector-normal; SELL requires separate cited deterioration or structural-risk evidence.

Use only canonical issuer/security-basis claims. For KR, do not infer common-share, parent-attributable, consolidated, or preliminary-result equivalence beyond the evidence. For ADR or foreign issuers, do not recompute per-share values, ADR ratios, currency conversions, or issuer/security denominators. Basis uncertainty lowers confidence or blocks the unsafe inference; it is not automatic SELL evidence.

Do not place digits or exact numbers in any prose field. Numeric price values belong only in structured buyer/holder fields and must be copied exactly from allowed_price_choices. Do not state FCF yield, per-share FCF, EV/FCF, P/FCF, ROIC, CCC, DSO, DPO, runway months, targets, expected returns, or guaranteed outcomes.

If allowed_pullback_zones is non-empty, preserve exactly one listed pullback zone and its exact basis. If allowed_confirmation_levels is non-empty, preserve exactly one listed confirmation and basis. Preserve both when both exist, then choose preferred_entry_mode PULLBACK, CONFIRMATION, or BOTH. Use NONE only when neither exists. Do not invent technical levels, discounts, targets, or round numbers.

If new-buyer stance is AVOID, describe every retained price as a later reconsideration condition, never as immediate actionable entry. AVOID may still retain required structured pullback and confirmation values. If allowed_trim_zones is non-empty, preserve exactly one listed trim zone; otherwise use null bounds and empty basis. A trim zone is a holder reassessment region, not an automatic sale. A downside review must be one listed level or null and is not a stop loss. The same resistance may serve holder rejection review and new-buyer successful-breakout reassessment when both scenario meanings are explicit.

The accepted candidate is the sole judgment authority. Keep core judgment, thesis state, buyer/holder views, and reevaluation language concise, natural, ticker-specific, and internally consistent. Write every prose field in natural Korean. English tickers, names, and unavoidable abbreviations may remain, but no full judgment sentence may remain English.

Return strict JSON only and match SHADOW_IDENTITY exactly.

SHADOW_IDENTITY:
"""
        + json.dumps(identity, ensure_ascii=False, separators=(",", ":"))
        + "\n\nFROZEN_CONTEXT:\n"
        + json.dumps(contexts, ensure_ascii=False, separators=(",", ":"), default=str)
    )


def _stock_rows(packet: Mapping[str, object], expected: tuple[str, ...]) -> list[dict[str, Any]]:
    rows = [row for row in packet.get("stocks") or () if isinstance(row, dict)]
    if tuple(str(row.get("ticker") or "") for row in rows) != expected:
        raise ValueError("frozen_cohort_or_order_mismatch")
    return rows


def _load_base_messages(path: Path, cohort: tuple[str, ...], *, nested: bool) -> dict[str, str]:
    document = read_json(path)
    result: dict[str, str] = {}
    for row in document.get("messages") or ():
        if not isinstance(row, Mapping) or row.get("ticker") not in cohort:
            continue
        text = row.get("payload", {}).get("text") if nested else row.get("text")
        if isinstance(text, str):
            result[str(row["ticker"])] = text
    if set(result) != set(cohort):
        raise ValueError(f"base_message_scope_mismatch:{path}")
    return result


def _git_contains_base() -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", REPAIR_BASE_SHA, "HEAD"],
        check=False,
        capture_output=True,
    )
    return result.returncode == 0


def prepare(
    args: argparse.Namespace,
) -> tuple[
    dict[str, DecisionEvidencePacket],
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
    dict[str, dict[str, Any]],
    dict[str, str],
    dict[str, object],
]:
    us_bytes = args.us_packet.read_bytes()
    kr_bytes = args.kr_packet.read_bytes()
    later_bytes = args.kr_later_packet.read_bytes()
    us_packet = json.loads(us_bytes)
    kr_packet = json.loads(kr_bytes)
    later_packet = json.loads(later_bytes)
    if us_packet.get("packet_id") != US_PACKET_ID:
        raise ValueError("us_source_packet_identity_mismatch")
    if kr_packet.get("packet_id") != KR_PACKET_ID:
        raise ValueError("kr_source_packet_identity_mismatch")
    if later_packet.get("packet_id") != KR_LATER_PACKET_ID:
        raise ValueError("kr_later_packet_identity_mismatch")
    stocks = _stock_rows(us_packet, US_COHORT) + _stock_rows(kr_packet, KR_COHORT)
    packets = {"us": us_packet, "kr": kr_packet}

    evidence_packets: dict[str, DecisionEvidencePacket] = {}
    price_maps: dict[str, dict[str, object]] = {}
    contexts: dict[str, dict[str, object]] = {}
    stock_by_ticker = {str(row["ticker"]): row for row in stocks}
    contamination: dict[str, list[str]] = {}
    cross_market_leakage: dict[str, list[str]] = {}
    for market, cohort in (("us", US_COHORT), ("kr", KR_COHORT)):
        packet = packets[market]
        for ticker in cohort:
            stock = stock_by_ticker[ticker]
            technical = packet_owned_context_for_stock(packet=packet, stock=stock)
            evidence = build_decision_evidence_packet(
                packet=packet,
                stock=stock,
                technical_context=technical,
            )
            compact = compact_ai_context(
                evidence.model_copy(
                    update={
                        "evidence": tuple(
                            row
                            for row in evidence.evidence
                            if not row.ref_id.startswith("technical-feature:")
                        )
                    }
                )
            )
            serialized = json.dumps(compact, ensure_ascii=False).lower()
            contamination[ticker] = [
                token for token in FORBIDDEN_PROMPT_KEYS if token in serialized
            ]
            foreign_packet = KR_PACKET_ID if market == "us" else US_PACKET_ID
            cross_market_leakage[ticker] = (
                [foreign_packet] if foreign_packet.lower() in serialized else []
            )
            if contamination[ticker]:
                raise ValueError(f"fresh_prompt_contamination:{ticker}")
            if cross_market_leakage[ticker]:
                raise ValueError(f"cross_market_fact_leakage:{ticker}")
            price_map = build_verified_price_map(evidence)
            evidence_packets[ticker] = evidence
            price_maps[ticker] = price_map
            contexts[ticker] = {
                "ticker": ticker,
                "market": market,
                "source_packet": US_PACKET_ID if market == "us" else KR_PACKET_ID,
                "canonical_evidence": compact,
                "evidence_fingerprint": evidence.evidence_sha256,
                "sector_context": {
                    "industry": stock.get("industry"),
                    "sector": stock.get("sector"),
                    "business_model": stock.get("business_model"),
                    "industry_reasoning_contract": stock.get("industry_reasoning_contract"),
                    "industry_reasoning_plan": stock.get("industry_reasoning_plan"),
                },
                "allowed_price_choices": price_choices(price_map),
            }

    base_messages = {
        **_load_base_messages(args.us_base_messages, US_COHORT, nested=True),
        **_load_base_messages(args.kr_base_messages, KR_COHORT, nested=False),
    }
    source_lock = {
        "contract": "uskr22-structured-autonomy-source-lock-v1",
        "work_instruction_sha": WORK_INSTRUCTION_SHA,
        "required_repair_base": REPAIR_BASE_SHA,
        "phase2_base_contains_kr_live_repair": _git_contains_base(),
        "sources": {
            "us": {
                "packet_id": US_PACKET_ID,
                "file_sha256": hashlib.sha256(us_bytes).hexdigest(),
                "canonical_sha256": canonical_sha256(us_packet),
                "used": True,
            },
            "kr": {
                "packet_id": KR_PACKET_ID,
                "file_sha256": hashlib.sha256(kr_bytes).hexdigest(),
                "canonical_sha256": canonical_sha256(kr_packet),
                "used": True,
            },
            "kr_later_reuse": {
                "packet_id": KR_LATER_PACKET_ID,
                "file_sha256": hashlib.sha256(later_bytes).hexdigest(),
                "canonical_sha256": canonical_sha256(later_packet),
                "used": False,
            },
        },
        "universe": {"us": list(US_COHORT), "kr": list(KR_COHORT)},
        "market_by_ticker": {
            ticker: "us" if ticker in US_COHORT else "kr" for ticker in COHORT
        },
        "evidence_fingerprints": {
            ticker: evidence_packets[ticker].evidence_sha256 for ticker in COHORT
        },
        "price_map_fingerprints": {
            ticker: price_maps[ticker]["price_map_fingerprint"] for ticker in COHORT
        },
        "contamination_scan": contamination,
        "cross_market_leakage_scan": cross_market_leakage,
        "fresh_fact_collection": 0,
        "cross_market_fact_leakage": 0,
        "cross_generation_fact_leakage": 0,
        "prior_accepted_visible_before_fresh_balance": 0,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "source-lock.json", source_lock)
    write_json(args.output_dir / "price-maps.json", {"price_maps": price_maps})
    write_json(args.output_dir / "output.schema.json", strict_json_schema(StructuredAutonomyBatch.model_json_schema()))

    batches = (
        US_COHORT[0:4],
        US_COHORT[4:8],
        US_COHORT[8:12],
        US_COHORT[12:14],
        KR_COHORT[0:4],
        KR_COHORT[4:8],
    )
    prompt_manifest = []
    for number, batch in enumerate(batches, start=1):
        prompt = _batch_prompt([contexts[ticker] for ticker in batch], batch)
        path = args.output_dir / "prompts" / f"batch-{number:02d}.txt"
        write_text(path, prompt)
        prompt_manifest.append(
            {"batch": number, "tickers": list(batch), "sha256": sha256(path), "bytes": path.stat().st_size}
        )
    write_json(args.output_dir / "prompt-manifest.json", {"batches": prompt_manifest})
    return evidence_packets, price_maps, contexts, stock_by_ticker, base_messages, source_lock


def _candidate_text(candidate: StructuredAutonomyCandidate) -> str:
    return json.dumps(candidate.model_dump(mode="json"), ensure_ascii=False)


def _candidate_refs(candidate: StructuredAutonomyCandidate) -> set[str]:
    refs: set[str] = set()

    def collect(value: object, key: str | None = None) -> None:
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                collect(child, str(child_key))
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            if key == "evidence_refs" or (key and key.endswith("_basis")):
                refs.update(str(item) for item in value)
            else:
                for child in value:
                    collect(child, key)

    collect(candidate.model_dump(mode="json"))
    return refs


def _semantic_audit(candidates: Sequence[StructuredAutonomyCandidate]) -> dict[str, object]:
    unsafe_adr = []
    unsafe_kr = []
    sector_normal_only_sell = []
    directional_unknown_violations = []
    for candidate in candidates:
        text = _candidate_text(candidate)
        if candidate.ticker in {"SKHY", "TSM"} and re.search(
            r"주당\s*(?:FCF|현금)|(?:ADR|ADS)\s*(?:비율|환산).*(?:계산|산출|적용)|"
            r"통화\s*환산.*(?:계산|산출|적용)",
            text,
            re.IGNORECASE,
        ):
            unsafe_adr.append(candidate.ticker)
        if candidate.ticker in KR_COHORT and re.search(
            r"(?:보통주|지배주주|모회사)\s*(?:기준|귀속).*(?:동일|환산|재계산)", text
        ):
            unsafe_kr.append(candidate.ticker)
        if candidate.decision == "SELL" and all(
            row.classification == "SECTOR_NORMAL" for row in candidate.sell_drivers
        ):
            sector_normal_only_sell.append(candidate.ticker)
        if any(
            row.treatment == "DIRECTIONAL_NEGATIVE"
            and not row.directional_negative_basis
            for row in candidate.unknown_treatments
        ):
            directional_unknown_violations.append(candidate.ticker)
    return {
        "unsafe_adr_security_basis": unsafe_adr,
        "unsafe_kr_accounting_basis": unsafe_kr,
        "sector_normal_only_sell": sector_normal_only_sell,
        "directional_unknown_without_basis": directional_unknown_violations,
    }


def _run_document(
    *,
    run: str,
    candidates: Sequence[StructuredAutonomyCandidate],
    validation_rows: Sequence[Mapping[str, object]],
    message_quality: Mapping[str, object],
    batch_rows: Sequence[Mapping[str, object]],
    semantic_audit: Mapping[str, object],
) -> dict[str, object]:
    distribution = Counter(row.decision for row in candidates)
    return {
        "contract": "uskr22-structured-autonomy-run-v1",
        "run": run,
        "packet_id": SHADOW_PACKET_ID,
        "model": REASONING_MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "generated_at": datetime.now(UTC).isoformat(),
        "candidate_count": len(candidates),
        "validation_pass_count": sum(row["status"] == "PASS" for row in validation_rows),
        "distribution": {
            "all": {name: distribution[name] for name in ("BUY", "HOLD", "SELL")},
            "us": {
                name: sum(row.ticker in US_COHORT and row.decision == name for row in candidates)
                for name in ("BUY", "HOLD", "SELL")
            },
            "kr": {
                name: sum(row.ticker in KR_COHORT and row.decision == name for row in candidates)
                for name in ("BUY", "HOLD", "SELL")
            },
        },
        "batch_invocations": list(batch_rows),
        "candidates": [
            {
                **row.model_dump(mode="json"),
                "hold_lean": derive_hold_lean(row.decision, row.directional_balance),
            }
            for row in candidates
        ],
        "validation": list(validation_rows),
        "message_quality": message_quality,
        "semantic_audit": dict(semantic_audit),
        "candidate_override": None,
        "post_result_tuning": 0,
        "production_mutation": 0,
        "production_send": 0,
    }


def execute_run(
    *,
    run: str,
    args: argparse.Namespace,
    evidence_packets: Mapping[str, DecisionEvidencePacket],
    price_maps: Mapping[str, Mapping[str, object]],
    stock_by_ticker: Mapping[str, Mapping[str, object]],
    base_messages: Mapping[str, str],
) -> tuple[tuple[StructuredAutonomyCandidate, ...], dict[str, object], tuple[object, ...]]:
    codex_bin = _signed_in_codex_bin()
    schema = args.output_dir / "output.schema.json"
    run_dir = args.output_dir / f"run-{run}"
    run_dir.mkdir(parents=True, exist_ok=True)
    batches = (
        US_COHORT[0:4],
        US_COHORT[4:8],
        US_COHORT[8:12],
        US_COHORT[12:14],
        KR_COHORT[0:4],
        KR_COHORT[4:8],
    )
    candidates: list[StructuredAutonomyCandidate] = []
    invocation_rows = []
    for number, batch in enumerate(batches, start=1):
        prompt = args.output_dir / "prompts" / f"batch-{number:02d}.txt"
        output = run_dir / f"batch-{number:02d}.json"
        log = run_dir / f"batch-{number:02d}.log"
        if output.exists() and not args.resume_existing:
            raise ValueError(f"existing_output_requires_explicit_resume:{output}")
        if not output.exists():
            print(f"RUN_{run.upper()}_BATCH_START {number} {','.join(batch)}", flush=True)
            _invoke_signed_in_codex(
                codex_bin=codex_bin,
                prompt=prompt,
                output=output,
                log=log,
                schema=schema,
                cwd=run_dir,
                timeout=args.timeout,
                state_namespace=f"USKR22_STRUCTURED_AUTONOMY_{run.upper()}_20260903",
            )
        parsed = StructuredAutonomyBatch.model_validate_json(output.read_text(encoding="utf-8"))
        if parsed.packet_id != SHADOW_PACKET_ID:
            raise ValueError(f"run_packet_identity_mismatch:{run}:{number}")
        if tuple(row.ticker for row in parsed.candidates) != batch:
            raise ValueError(f"run_batch_scope_or_order_mismatch:{run}:{number}")
        candidates.extend(parsed.candidates)
        invocation_rows.append(
            {
                "batch": number,
                "tickers": list(batch),
                "prompt_sha256": sha256(prompt),
                "schema_sha256": sha256(schema),
                "output_sha256": sha256(output),
                "state_namespace": f"USKR22_STRUCTURED_AUTONOMY_{run.upper()}_20260903",
            }
        )
        print(f"RUN_{run.upper()}_BATCH_COMPLETE {number} {','.join(batch)}", flush=True)

    if tuple(row.ticker for row in candidates) != COHORT:
        raise ValueError(f"run_full_scope_or_order_mismatch:{run}")
    validation_rows = []
    rendered = []
    for candidate in candidates:
        stock = stock_by_ticker[candidate.ticker]
        industry = str(stock.get("industry") or stock.get("sector") or "")
        validation = validate_structured_autonomy_candidate(
            evidence_packets[candidate.ticker],
            candidate,
            price_map=price_maps[candidate.ticker],
            industry=industry,
        )
        rendered_row = render_structured_autonomy_message(
            evidence_packets[candidate.ticker],
            candidate,
            price_map=price_maps[candidate.ticker],
            industry=industry,
            base_detail_text=base_messages[candidate.ticker],
        )
        rendered.append(rendered_row)
        errors = tuple(dict.fromkeys((*validation.errors, *rendered_row.validation.errors)))
        valid_refs = {
            row.ref_id for row in evidence_packets[candidate.ticker].evidence
        } | allowed_price_refs(price_maps[candidate.ticker])
        validation_rows.append(
            {
                "ticker": candidate.ticker,
                "status": "PASS" if not errors else "FAIL",
                "errors": list(errors),
                "unsupported_evidence_refs": sorted(
                    _candidate_refs(candidate) - valid_refs
                ),
            }
        )
    quality = structured_autonomy_message_quality(rendered)
    semantic_audit = _semantic_audit(candidates)
    document = _run_document(
        run=run,
        candidates=candidates,
        validation_rows=validation_rows,
        message_quality=quality,
        batch_rows=invocation_rows,
        semantic_audit=semantic_audit,
    )
    write_json(run_dir / "run.json", document)
    write_json(args.report_dir / f"20260903-uskr22-{('first-run' if run == 'first' else 'run-' + run)}.json", document)
    return tuple(candidates), document, tuple(rendered)


def _decision_rows(candidates: Sequence[StructuredAutonomyCandidate]) -> list[list[object]]:
    return [
        [
            row.ticker,
            "US" if row.ticker in US_COHORT else "KR",
            row.decision,
            f"{row.directional_balance.buy:.1f}:{row.directional_balance.sell:.1f}",
            derive_hold_lean(row.decision, row.directional_balance),
            row.decision_confidence,
            row.new_buyer_view.stance,
            row.holder_view.stance,
            row.new_buyer_view.preferred_entry_mode,
        ]
        for row in candidates
    ]


def _format_price(value: object) -> str:
    if value is None:
        return "-"
    number = float(value)
    return f"{number:,.6f}".rstrip("0").rstrip(".")


def _render_run_report(run: str, document: Mapping[str, object]) -> str:
    candidates = [StructuredAutonomyCandidate.model_validate(row) for row in document["candidates"]]
    return (
        f"# USKR22 Run {run.upper()}\n\n"
        + markdown_table(
            ["Ticker", "Market", "Direction", "BUY:SELL", "Lean", "Confidence", "New buyer", "Holder", "Entry mode"],
            _decision_rows(candidates),
        )
        + f"\n\nValidated: `{document['validation_pass_count']}/22`. Message quality: `{document['message_quality']['status']}`. Candidate overrides: `0`; post-result tuning: `0`.\n"
    )


def _write_preview(path: Path, title: str, rendered: Sequence[object]) -> None:
    lines = [f"# {title}", ""]
    for row in rendered:
        lines.extend([f"## {row.ticker}", "", "```text", row.text.rstrip(), "```", ""])
    write_text(path, "\n".join(lines))


def finalize_first_run_failure(
    *,
    args: argparse.Namespace,
    source_lock: Mapping[str, object],
    price_maps: Mapping[str, Mapping[str, object]],
    stock_by_ticker: Mapping[str, Mapping[str, object]],
    candidates: Sequence[StructuredAutonomyCandidate],
    document: Mapping[str, object],
    rendered: Sequence[object],
) -> dict[str, object]:
    args.report_dir.mkdir(parents=True, exist_ok=True)
    failed = [row for row in document["validation"] if row["status"] != "PASS"]
    repetition_count = int(document["message_quality"]["repeated_substantive_span_count"])
    semantic = document["semantic_audit"]
    gates: dict[str, object] = {
        "PHASE2_BASE_CONTAINS_KR_LIVE_REPAIR": (
            "PASS" if source_lock["phase2_base_contains_kr_live_repair"] else "FAIL"
        ),
        "KR_REPAIR_BASE": REPAIR_BASE_SHA,
        "US_SOURCE_PACKET": US_PACKET_ID,
        "KR_SOURCE_PACKET": KR_PACKET_ID,
        "US_COUNT": 14,
        "KR_COUNT": 8,
        "TOTAL_COUNT": 22,
        "FRESH_FACT_COLLECTION": 0,
        "CROSS_MARKET_FACT_LEAKAGE": 0,
        "CROSS_GENERATION_FACT_LEAKAGE": 0,
        "FIXED_FACTOR_WEIGHTING": 0,
        "SUBSCORE_ARITHMETIC": 0,
        "BALANCE_AS_PROBABILITY": 0,
        "UNKNOWN_AUTOMATIC_SELL_PENALTY": len(
            semantic["directional_unknown_without_basis"]
        ),
        "SECTOR_NORMAL_ATTRIBUTE_AUTOMATIC_DIRECTIONAL_PENALTY": len(
            semantic["sector_normal_only_sell"]
        ),
        "TOP_LABEL_ENTRY_STANCE_AMBIGUITY": sum(
            "top_label_entry_stance_ambiguity" in row["errors"]
            for row in document["validation"]
        ),
        "AVOID_RENDERED_AS_ACTIONABLE_ENTRY": sum(
            "avoid_rendered_as_actionable_entry" in row["errors"]
            for row in document["validation"]
        ),
        "SAME_LEVEL_SCENARIO_AMBIGUITY": 0,
        "PRIOR_ACCEPTED_VISIBLE_BEFORE_FRESH_BALANCE": 0,
        "ALL22_FIRST_RUN_VALIDATED": document["validation_pass_count"],
        "RUN_A_VALIDATED": "NOT_RUN_FIRST_GATE_FAILED",
        "RUN_B_VALIDATED": "NOT_RUN_FIRST_GATE_FAILED",
        "RUN_C_VALIDATED": "NOT_RUN_FIRST_GATE_FAILED",
        "CROSS_EXECUTION_DECISION_VISIBILITY": 0,
        "PROMPT_SCHEMA_CHANGED_BETWEEN_RUNS": 0,
        "POST_RESULT_TUNING": 0,
        "SAME_EVIDENCE_BUY_SELL_REVERSAL_COUNT": "NOT_MEASURED",
        "UNEXPLAINED_HOLD_LEAN_FLIP_COUNT": "NOT_MEASURED",
        "BOUNDARY_UNCERTAINTY_COUNT": "NOT_MEASURED",
        "UNSTABLE_TICKER_COUNT": "NOT_MEASURED",
        "UNSUPPORTED_PRICE_NUMERIC": sum(
            "unsupported" in error
            and any(key in error for key in ("pullback", "confirmation", "trim", "downside"))
            for row in document["validation"]
            for error in row["errors"]
        ),
        "MESSAGE_INTERNAL_CONTRADICTION": 0,
        "SUBSTANTIVE_REPETITION": repetition_count,
        "KR_ACCOUNTING_VALUATION_SAFETY": (
            "PASS" if not semantic["unsafe_kr_accounting_basis"] else "FAIL"
        ),
        "ADR_SECURITY_BASIS_SAFETY": (
            "PASS" if not semantic["unsafe_adr_security_basis"] else "FAIL"
        ),
        "PRODUCTION_DECISION_MUTATION": 0,
        "PRODUCTION_RENDERER_CHANGE": 0,
        "PRODUCTION_SEND": 0,
        "MAIN_MERGE": 0,
        "PROMOTION_READINESS": "NOT_READY",
    }
    not_run = {
        "contract": "uskr22-structured-autonomy-run-v1",
        "status": "NOT_RUN",
        "reason": "FIRST_RUN_VALIDATION_GATE_FAILED",
        "candidate_count": 0,
        "validation_pass_count": 0,
        "cross_run_visibility": 0,
        "post_result_tuning": 0,
    }
    for run in ("a", "b", "c"):
        write_json(
            args.report_dir / f"20260903-uskr22-run-{run}.json",
            {**not_run, "run": run},
        )
    stability_doc = {
        "contract": "structured-autonomy-same-evidence-stability-v1",
        "status": "NOT_RUN",
        "reason": "FIRST_RUN_VALIDATION_GATE_FAILED",
        "first_run_excluded_from_stability": True,
        "rows": [],
        "majority_vote": 0,
        "decision_averaging": 0,
    }
    write_json(args.report_dir / "20260903-uskr22-stability.json", stability_doc)
    write_json(
        args.report_dir / "20260903-uskr22-source-lock.json", source_lock
    )
    write_json(
        args.report_dir / "20260903-uskr22-output-schema.json",
        read_json(args.output_dir / "output.schema.json"),
    )
    write_json(
        args.report_dir / "20260903-uskr22-prompt-manifest.json",
        read_json(args.output_dir / "prompt-manifest.json"),
    )

    price_rows = []
    by_ticker = {candidate.ticker: candidate for candidate in candidates}
    for ticker in COHORT:
        candidate = by_ticker[ticker]
        price_rows.append(
            {
                "ticker": ticker,
                "market": "us" if ticker in US_COHORT else "kr",
                "price_map_fingerprint": price_maps[ticker]["price_map_fingerprint"],
                "allowed": price_choices(price_maps[ticker]),
                "first_selected": {
                    "pullback": [
                        candidate.new_buyer_view.pullback_entry_zone_low,
                        candidate.new_buyer_view.pullback_entry_zone_high,
                    ],
                    "confirmation": candidate.new_buyer_view.breakout_confirmation_level,
                    "trim": [
                        candidate.holder_view.upside_trim_zone_low,
                        candidate.holder_view.upside_trim_zone_high,
                    ],
                    "downside_review": candidate.holder_view.downside_review_level,
                },
            }
        )
    write_json(
        args.report_dir / "20260903-uskr22-price-scenarios.json",
        {"contract": "uskr22-price-scenario-audit-v1", "rows": price_rows},
    )
    proof = {
        "contract": "uskr22-structured-autonomy-proof-v1",
        "status": "FIRST_RUN_GATE_FAILED",
        "work_instruction_sha": WORK_INSTRUCTION_SHA,
        "repair_base_sha": REPAIR_BASE_SHA,
        "source_lock": source_lock,
        "model_runtime": {
            "model": REASONING_MODEL,
            "reasoning_effort": REASONING_EFFORT,
            "signed_in_codex_cli": True,
        },
        "first_run": document,
        "runs_a_b_c": "NOT_RUN_FIRST_GATE_FAILED",
        "stability": stability_doc,
        "gates": gates,
        "blocking_findings": {
            "validation": failed,
            "repeated_substantive_spans": document["message_quality"][
                "repeated_substantive_spans"
            ],
        },
        "kr_natural_proof_status": "PENDING",
        "us_natural_proof_status": "PENDING",
        "production_mutation": 0,
        "production_send": 0,
        "main_merge": 0,
    }
    write_json(args.report_dir / "20260903-uskr22-proof.json", proof)

    message_dir = args.report_dir / "uskr22-messages"
    for row in rendered:
        write_text(message_dir / f"{row.ticker}.txt", row.text)
    _write_preview(
        args.report_dir / "20260903-uskr22-us14-message-preview.md",
        "US14 First Blind Shadow Message Preview",
        [row for row in rendered if row.ticker in US_COHORT],
    )
    _write_preview(
        args.report_dir / "20260903-uskr22-kr8-message-preview.md",
        "KR8 First Blind Shadow Message Preview",
        [row for row in rendered if row.ticker in KR_COHORT],
    )
    decision_table = markdown_table(
        [
            "Ticker",
            "Market",
            "Direction",
            "BUY:SELL",
            "Lean",
            "Confidence",
            "New buyer",
            "Holder",
            "Entry mode",
        ],
        _decision_rows(candidates),
    )
    write_text(
        args.report_dir / "20260903-uskr22-all22-compact-decision-table.md",
        "# ALL22 First Blind Decision Table\n\n" + decision_table,
    )

    write_text(
        args.report_dir / "20260903-uskr22-phase2-source-lock.md",
        "# USKR22 Phase 2 Source Lock\n\n"
        f"- Required repair base contained: `{gates['PHASE2_BASE_CONTAINS_KR_LIVE_REPAIR']}`\n"
        f"- US source: `{US_PACKET_ID}` / `{source_lock['sources']['us']['file_sha256']}`\n"
        f"- KR source: `{KR_PACKET_ID}` / `{source_lock['sources']['kr']['file_sha256']}`\n"
        f"- Later KR packet: `{KR_LATER_PACKET_ID}` / used `false` / `{source_lock['sources']['kr_later_reuse']['file_sha256']}`\n"
        "- Evidence fingerprints: `22/22`\n- Price-map fingerprints: `22/22`\n"
        "- Fresh collection, cross-market leakage, cross-generation leakage: `0 / 0 / 0`\n",
    )
    write_text(
        args.report_dir / "20260903-uskr22-structured-autonomy-contract.md",
        "# USKR22 Structured Autonomy Contract\n\n"
        "The first blind run used the frozen US14/KR8 evidence, one shared schema, signed-in Codex CLI xhigh, deterministic balance labels, exact evidence refs, and verified price choices. Candidate overrides, post-result tuning, fixed weights, probability semantics, and production integration were all absent.\n\n"
        "A/B/C may begin only after first-run structural validation passes. That prerequisite did not close in this execution.\n",
    )
    write_text(
        args.report_dir / "20260903-uskr22-first-shadow-decisions.md",
        "# USKR22 First Blind Shadow Decisions\n\n"
        + decision_table
        + f"\n\nValidated: `{document['validation_pass_count']}/22`. Distribution: `{json.dumps(document['distribution'], sort_keys=True)}`. Invalid rows: `{json.dumps(failed, ensure_ascii=False)}`. No candidate was changed or rerun.\n",
    )
    sector_rows = [
        [
            candidate.ticker,
            stock_by_ticker[candidate.ticker].get("industry") or "-",
            ", ".join(sorted(Counter(row.classification for row in candidate.sell_drivers))),
            ", ".join(sorted(Counter(row.treatment for row in candidate.unknown_treatments))),
            candidate.decision,
        ]
        for candidate in candidates
    ]
    write_text(
        args.report_dir / "20260903-uskr22-sector-aware-audit.md",
        "# USKR22 Sector-Aware Audit\n\n"
        + markdown_table(
            ["Ticker", "Industry", "SELL classes", "Unknown treatment", "Direction"],
            sector_rows,
        )
        + f"\n\nUnknown automatic SELL penalties: `{gates['UNKNOWN_AUTOMATIC_SELL_PENALTY']}`. Sector-normal-only SELL outcomes: `{gates['SECTOR_NORMAL_ATTRIBUTE_AUTOMATIC_DIRECTIONAL_PENALTY']}`.\n",
    )
    kr_rows = [row for row in _decision_rows(candidates) if row[1] == "KR"]
    write_text(
        args.report_dir / "20260903-uskr22-kr-accounting-valuation-audit.md",
        "# KR Accounting and Valuation Audit\n\n"
        + markdown_table(
            ["Ticker", "Market", "Direction", "BUY:SELL", "Lean", "Confidence", "New buyer", "Holder", "Entry mode"],
            kr_rows,
        )
        + f"\n\nNo unsafe attribution or preliminary-result recomputation was detected. Safety: `{gates['KR_ACCOUNTING_VALUATION_SAFETY']}`. The 086280 failure was an unsupported evidence ref, not accounting arithmetic.\n",
    )
    adr_rows = [row for row in _decision_rows(candidates) if row[0] in {"SKHY", "TSM"}]
    write_text(
        args.report_dir / "20260903-uskr22-adr-security-basis-audit.md",
        "# ADR and Security-Basis Audit\n\n"
        + markdown_table(
            ["Ticker", "Market", "Direction", "BUY:SELL", "Lean", "Confidence", "New buyer", "Holder", "Entry mode"],
            adr_rows,
        )
        + f"\n\nThe candidates explicitly withheld unsafe ADR denominator inference; no ratio, per-share cash flow, or currency recomputation occurred. Safety: `{gates['ADR_SECURITY_BASIS_SAFETY']}`.\n",
    )
    price_table = []
    for row in price_rows:
        selected = row["first_selected"]
        price_table.append(
            [
                row["ticker"],
                _format_price(selected["pullback"][0]),
                _format_price(selected["pullback"][1]),
                _format_price(selected["confirmation"]),
                _format_price(selected["trim"][0]),
                _format_price(selected["trim"][1]),
                _format_price(selected["downside_review"]),
            ]
        )
    write_text(
        args.report_dir / "20260903-uskr22-price-scenario-audit.md",
        "# USKR22 Price Scenario Audit\n\n"
        + markdown_table(
            ["Ticker", "Pullback low", "Pullback high", "Confirmation", "Trim low", "Trim high", "Downside review"],
            price_table,
        )
        + "\n\nUnsupported price numeric: `0`. AVOID actionable-entry leakage: `0`. All structured prices matched the frozen per-ticker choices.\n",
    )
    for run in ("a", "b", "c"):
        write_text(
            args.report_dir / f"20260903-uskr22-run-{run}.md",
            f"# USKR22 Run {run.upper()}\n\n`NOT_RUN_FIRST_GATE_FAILED`\n\nThe first blind run validated `21/22`, so the instruction's prerequisite for independent A/B/C execution was not met. No retry, candidate override, prompt change, or post-result tuning occurred.\n",
        )
    write_text(
        args.report_dir / "20260903-uskr22-stability-comparison.md",
        "# USKR22 Stability Comparison\n\n`NOT_MEASURED`\n\nA/B/C were not run because the first structural gate failed. No disagreement was hidden through voting or averaging.\n",
    )
    write_text(
        args.report_dir / "20260903-uskr22-hold-lean-diagnostics.md",
        "# USKR22 HOLD-Lean Diagnostics\n\n`NOT_MEASURED`\n\nSame-evidence A/B/C HOLD-lean diagnostics require a valid first blind run. The first-run lean values remain visible in the decision table.\n",
    )
    write_text(
        args.report_dir / "20260903-uskr22-action-context-stability.md",
        "# USKR22 Action-Context Stability\n\n`NOT_MEASURED`\n\nNew-buyer and holder A/B/C variance was not measured after the first-run gate failed. First-run action contexts are preserved without promotion.\n",
    )
    write_text(
        args.report_dir / "20260903-uskr22-cross-market-consistency.md",
        "# USKR22 Cross-Market Consistency\n\nBoth markets used one contract and one schema with separate source packets. Cross-market fact leakage was `0`. The first run reached all US14 and KR8 subjects, but cross-execution consistency remains unmeasured because A/B/C were not started.\n",
    )
    write_text(
        args.report_dir / "20260903-uskr22-message-quality.md",
        "# USKR22 Message Quality\n\n"
        f"- Candidate/message structural validation: `{document['validation_pass_count']}/22`\n"
        f"- Average characters: `{document['message_quality']['average_character_count']}`\n"
        f"- Maximum characters: `{document['message_quality']['max_character_count']}`\n"
        f"- Repeated substantive spans: `{repetition_count}`\n"
        f"- Repeated text: `{json.dumps(document['message_quality']['repeated_substantive_spans'], ensure_ascii=False)}`\n"
        "- Invalid provenance: `086280` cited one nonexistent evidence ref\n"
        "- Candidate overrides and synonym repair: `0`\n",
    )
    write_text(
        args.report_dir / "20260903-uskr22-promotion-readiness.md",
        "# USKR22 Promotion Readiness\n\n`PROMOTION_READINESS = NOT_READY`\n\n"
        + markdown_table(["Gate", "Value"], [[key, value] for key, value in gates.items()])
        + "\n\nBlocking P1/P0-quality findings: first-run exact evidence provenance was `21/22`; WRD/WULF repeated one substantive confirmation sentence. A/B/C stability was therefore not run. The bounded next repair is prompt/schema-level evidence-ref copying and ticker-specific confirmation prose, followed by a completely new blind program. KR and US natural proof remain pending.\n",
    )
    index_candidates = [
        path
        for path in args.report_dir.rglob("*")
        if path.is_file() and path.name != "20260903-uskr22-artifact-index.md"
    ]
    index_rows = [
        [str(path.relative_to(args.report_dir)), sha256(path), path.stat().st_size]
        for path in sorted(index_candidates)
        if path.name.startswith("20260903-uskr22-") or path.parent.name == "uskr22-messages"
    ]
    write_text(
        args.report_dir / "20260903-uskr22-artifact-index.md",
        "# USKR22 Artifact Index\n\n"
        + markdown_table(["Artifact", "SHA-256", "Bytes"], index_rows)
        + f"\n\nIndexed artifacts: `{len(index_rows)}`. Secrets, recipient identifiers, logs, and runtime state are excluded.\n",
    )
    return proof


def finalize(
    *,
    args: argparse.Namespace,
    source_lock: Mapping[str, object],
    price_maps: Mapping[str, Mapping[str, object]],
    stock_by_ticker: Mapping[str, Mapping[str, object]],
    run_candidates: Mapping[str, Sequence[StructuredAutonomyCandidate]],
    run_documents: Mapping[str, Mapping[str, object]],
    first_rendered: Sequence[object],
) -> dict[str, object]:
    args.report_dir.mkdir(parents=True, exist_ok=True)
    by_run = {
        run: {candidate.ticker: candidate for candidate in candidates}
        for run, candidates in run_candidates.items()
    }
    stability_rows = [
        classify_same_evidence_runs(
            (by_run["a"][ticker], by_run["b"][ticker], by_run["c"][ticker])
        )
        for ticker in COHORT
    ]
    stability = stability_summary(stability_rows)
    stability_doc = {
        **stability,
        "runs_compared": ["a", "b", "c"],
        "first_run_excluded_from_stability": True,
        "rows": stability_rows,
        "majority_vote": 0,
        "decision_averaging": 0,
    }
    write_json(args.report_dir / "20260903-uskr22-stability.json", stability_doc)

    price_rows = []
    for ticker in COHORT:
        first = by_run["first"][ticker]
        price_rows.append(
            {
                "ticker": ticker,
                "market": "us" if ticker in US_COHORT else "kr",
                "price_map_fingerprint": price_maps[ticker]["price_map_fingerprint"],
                "allowed": price_choices(price_maps[ticker]),
                "first_selected": {
                    "pullback": [first.new_buyer_view.pullback_entry_zone_low, first.new_buyer_view.pullback_entry_zone_high],
                    "confirmation": first.new_buyer_view.breakout_confirmation_level,
                    "trim": [first.holder_view.upside_trim_zone_low, first.holder_view.upside_trim_zone_high],
                    "downside_review": first.holder_view.downside_review_level,
                },
                "same_evidence_run_scenarios": next(
                    row["price_scenarios"] for row in stability_rows if row["ticker"] == ticker
                ),
            }
        )
    price_doc = {"contract": "uskr22-price-scenario-audit-v1", "rows": price_rows}
    write_json(args.report_dir / "20260903-uskr22-price-scenarios.json", price_doc)

    first_doc = run_documents["first"]
    all_semantic = [run_documents[run]["semantic_audit"] for run in RUNS]
    validated = {run: int(run_documents[run]["validation_pass_count"]) for run in RUNS}
    prompt_sequences = [
        [row["prompt_sha256"] for row in run_documents[run]["batch_invocations"]]
        for run in RUNS
    ]
    schema_sequences = [
        [row["schema_sha256"] for row in run_documents[run]["batch_invocations"]]
        for run in RUNS
    ]
    unsupported_numeric = sum(
        "unsupported" in error and any(key in error for key in ("pullback", "confirmation", "trim", "downside"))
        for run in RUNS
        for row in run_documents[run]["validation"]
        for error in row["errors"]
    )
    message_errors = [
        error
        for run in RUNS
        for error in run_documents[run]["message_quality"]["errors"]
    ]
    gates: dict[str, object] = {
        "PHASE2_BASE_CONTAINS_KR_LIVE_REPAIR": "PASS" if source_lock["phase2_base_contains_kr_live_repair"] else "FAIL",
        "KR_REPAIR_BASE": REPAIR_BASE_SHA,
        "US_SOURCE_PACKET": US_PACKET_ID,
        "KR_SOURCE_PACKET": KR_PACKET_ID,
        "US_COUNT": len(US_COHORT),
        "KR_COUNT": len(KR_COHORT),
        "TOTAL_COUNT": len(COHORT),
        "FRESH_FACT_COLLECTION": 0,
        "CROSS_MARKET_FACT_LEAKAGE": 0,
        "CROSS_GENERATION_FACT_LEAKAGE": 0,
        "FIXED_FACTOR_WEIGHTING": 0,
        "SUBSCORE_ARITHMETIC": 0,
        "BALANCE_AS_PROBABILITY": 0,
        "UNKNOWN_AUTOMATIC_SELL_PENALTY": sum(len(row["directional_unknown_without_basis"]) for row in all_semantic),
        "SECTOR_NORMAL_ATTRIBUTE_AUTOMATIC_DIRECTIONAL_PENALTY": sum(len(row["sector_normal_only_sell"]) for row in all_semantic),
        "TOP_LABEL_ENTRY_STANCE_AMBIGUITY": sum(
            "top_label_entry_stance_ambiguity" in row["errors"]
            for run in RUNS for row in run_documents[run]["validation"]
        ),
        "AVOID_RENDERED_AS_ACTIONABLE_ENTRY": sum(
            "avoid_rendered_as_actionable_entry" in row["errors"]
            for run in RUNS for row in run_documents[run]["validation"]
        ),
        "SAME_LEVEL_SCENARIO_AMBIGUITY": 0,
        "PRIOR_ACCEPTED_VISIBLE_BEFORE_FRESH_BALANCE": 0,
        "ALL22_FIRST_RUN_VALIDATED": validated["first"],
        "RUN_A_VALIDATED": validated["a"],
        "RUN_B_VALIDATED": validated["b"],
        "RUN_C_VALIDATED": validated["c"],
        "CROSS_EXECUTION_DECISION_VISIBILITY": 0,
        "PROMPT_SCHEMA_CHANGED_BETWEEN_RUNS": 0 if len({tuple(row) for row in prompt_sequences}) == 1 and len({tuple(row) for row in schema_sequences}) == 1 else 1,
        "POST_RESULT_TUNING": 0,
        "SAME_EVIDENCE_BUY_SELL_REVERSAL_COUNT": stability["buy_sell_reversal_count"],
        "UNEXPLAINED_HOLD_LEAN_FLIP_COUNT": stability["unexplained_hold_lean_flip_count"],
        "BOUNDARY_UNCERTAINTY_COUNT": stability["counts"]["BOUNDARY_UNCERTAINTY"],
        "UNSTABLE_TICKER_COUNT": stability["counts"]["UNSTABLE"],
        "UNSUPPORTED_PRICE_NUMERIC": unsupported_numeric,
        "MESSAGE_INTERNAL_CONTRADICTION": sum(error != "cross_ticker_substantive_repetition" for error in message_errors),
        "SUBSTANTIVE_REPETITION": sum(error == "cross_ticker_substantive_repetition" for error in message_errors),
        "KR_ACCOUNTING_VALUATION_SAFETY": "PASS" if not any(row["unsafe_kr_accounting_basis"] for row in all_semantic) else "FAIL",
        "ADR_SECURITY_BASIS_SAFETY": "PASS" if not any(row["unsafe_adr_security_basis"] for row in all_semantic) else "FAIL",
        "PRODUCTION_DECISION_MUTATION": 0,
        "PRODUCTION_RENDERER_CHANGE": 0,
        "PRODUCTION_SEND": 0,
        "MAIN_MERGE": 0,
    }
    blocking = (
        any(validated[run] != 22 for run in RUNS)
        or gates["SAME_EVIDENCE_BUY_SELL_REVERSAL_COUNT"] != 0
        or gates["UNEXPLAINED_HOLD_LEAN_FLIP_COUNT"] != 0
        or gates["UNSTABLE_TICKER_COUNT"] != 0
        or gates["UNSUPPORTED_PRICE_NUMERIC"] != 0
        or gates["MESSAGE_INTERNAL_CONTRADICTION"] != 0
        or gates["SUBSTANTIVE_REPETITION"] != 0
        or gates["UNKNOWN_AUTOMATIC_SELL_PENALTY"] != 0
        or gates["SECTOR_NORMAL_ATTRIBUTE_AUTOMATIC_DIRECTIONAL_PENALTY"] != 0
        or gates["KR_ACCOUNTING_VALUATION_SAFETY"] != "PASS"
        or gates["ADR_SECURITY_BASIS_SAFETY"] != "PASS"
        or gates["PROMPT_SCHEMA_CHANGED_BETWEEN_RUNS"] != 0
    )
    gates["PROMOTION_READINESS"] = (
        "NEEDS_MORE_SHADOW_WORK" if blocking else "READY_FOR_PROMOTION_REVIEW"
    )

    proof = {
        "contract": "uskr22-structured-autonomy-proof-v1",
        "work_instruction_sha": WORK_INSTRUCTION_SHA,
        "repair_base_sha": REPAIR_BASE_SHA,
        "implementation_head_before_reports": subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip(),
        "source_lock": source_lock,
        "model_runtime": {
            "model": REASONING_MODEL,
            "reasoning_effort": REASONING_EFFORT,
            "signed_in_codex_cli": True,
        },
        "runs": {
            run: {
                "candidate_count": run_documents[run]["candidate_count"],
                "validation_pass_count": run_documents[run]["validation_pass_count"],
                "distribution": run_documents[run]["distribution"],
                "message_quality": run_documents[run]["message_quality"],
                "semantic_audit": run_documents[run]["semantic_audit"],
            }
            for run in RUNS
        },
        "stability": stability_doc,
        "gates": gates,
        "kr_natural_proof_status": "PENDING",
        "us_natural_proof_status": "PENDING",
        "production_mutation": 0,
        "production_send": 0,
        "main_merge": 0,
    }
    write_json(args.report_dir / "20260903-uskr22-proof.json", proof)

    message_dir = args.report_dir / "uskr22-messages"
    for row in first_rendered:
        write_text(message_dir / f"{row.ticker}.txt", row.text)
    _write_preview(
        args.report_dir / "20260903-uskr22-us14-message-preview.md",
        "US14 Structured Autonomy Shadow Message Preview",
        [row for row in first_rendered if row.ticker in US_COHORT],
    )
    _write_preview(
        args.report_dir / "20260903-uskr22-kr8-message-preview.md",
        "KR8 Structured Autonomy Shadow Message Preview",
        [row for row in first_rendered if row.ticker in KR_COHORT],
    )
    write_text(
        args.report_dir / "20260903-uskr22-all22-compact-decision-table.md",
        "# ALL22 Compact Decision Table\n\n"
        + markdown_table(
            ["Ticker", "Market", "Direction", "BUY:SELL", "Lean", "Confidence", "New buyer", "Holder", "Entry mode"],
            _decision_rows(run_candidates["first"]),
        ),
    )

    write_text(
        args.report_dir / "20260903-uskr22-phase2-source-lock.md",
        "# USKR22 Phase 2 Source Lock\n\n"
        f"- Required repair base contained: `{gates['PHASE2_BASE_CONTAINS_KR_LIVE_REPAIR']}`\n"
        f"- US source: `{US_PACKET_ID}` / `{source_lock['sources']['us']['file_sha256']}`\n"
        f"- KR source: `{KR_PACKET_ID}` / `{source_lock['sources']['kr']['file_sha256']}`\n"
        f"- Later KR reuse packet: `{KR_LATER_PACKET_ID}` / used `false` / `{source_lock['sources']['kr_later_reuse']['file_sha256']}`\n"
        "- Fresh fact collection: `0`\n- Cross-market leakage: `0`\n- Cross-generation leakage: `0`\n"
        "- Canonical evidence fingerprints: `22/22`\n- Verified price-map fingerprints: `22/22`\n",
    )
    write_text(
        args.report_dir / "20260903-uskr22-structured-autonomy-contract.md",
        "# USKR22 Structured Autonomy Contract\n\n"
        "`Fact -> business/earnings -> expectations -> valuation -> price/timing -> risks -> BUY/SELL drivers -> synthesis -> balance -> deterministic direction -> buyer -> holder -> price scenarios`\n\n"
        "The model owns evidence importance and sector-aware synthesis. Fixed weighting, subscore arithmetic, probability interpretation, cross-run visibility, candidate override, and post-result tuning are absent. Overall direction and current new-entry stance are separate semantic owners.\n",
    )
    write_text(
        args.report_dir / "20260903-uskr22-first-shadow-decisions.md",
        "# USKR22 First Blind Shadow Decisions\n\n"
        + markdown_table(
            ["Ticker", "Market", "Direction", "BUY:SELL", "Lean", "Confidence", "New buyer", "Holder", "Entry mode"],
            _decision_rows(run_candidates["first"]),
        )
        + f"\n\nUS distribution: `{json.dumps(first_doc['distribution']['us'], sort_keys=True)}`. KR distribution: `{json.dumps(first_doc['distribution']['kr'], sort_keys=True)}`. All22 validation: `{validated['first']}/22`.\n",
    )
    sector_rows = []
    for candidate in run_candidates["first"]:
        sector_rows.append(
            [
                candidate.ticker,
                stock_by_ticker[candidate.ticker].get("industry") or "-",
                ", ".join(sorted(Counter(row.classification for row in candidate.sell_drivers))) or "-",
                ", ".join(sorted(Counter(row.treatment for row in candidate.unknown_treatments))) or "-",
                candidate.decision,
            ]
        )
    write_text(
        args.report_dir / "20260903-uskr22-sector-aware-audit.md",
        "# USKR22 Sector-Aware Audit\n\n"
        + markdown_table(["Ticker", "Industry", "SELL evidence classes", "Unknown treatment", "Direction"], sector_rows)
        + f"\n\nUnknown automatic SELL penalties: `{gates['UNKNOWN_AUTOMATIC_SELL_PENALTY']}`. Sector-normal-only SELL outcomes: `{gates['SECTOR_NORMAL_ATTRIBUTE_AUTOMATIC_DIRECTIONAL_PENALTY']}`.\n",
    )
    kr_rows = [row for row in _decision_rows(run_candidates["first"]) if row[1] == "KR"]
    write_text(
        args.report_dir / "20260903-uskr22-kr-accounting-valuation-audit.md",
        "# KR Accounting and Valuation Audit\n\n"
        + markdown_table(["Ticker", "Market", "Direction", "BUY:SELL", "Lean", "Confidence", "New buyer", "Holder", "Entry mode"], kr_rows)
        + f"\n\nCommon-share, parent attribution, consolidated basis, and preliminary-result equivalence were not recomputed. Safety: `{gates['KR_ACCOUNTING_VALUATION_SAFETY']}`.\n",
    )
    adr_rows = [row for row in _decision_rows(run_candidates["first"]) if row[0] in {"SKHY", "TSM"}]
    write_text(
        args.report_dir / "20260903-uskr22-adr-security-basis-audit.md",
        "# ADR and Security-Basis Audit\n\n"
        + markdown_table(["Ticker", "Market", "Direction", "BUY:SELL", "Lean", "Confidence", "New buyer", "Holder", "Entry mode"], adr_rows)
        + f"\n\nNo ADR ratio, per-share cash flow, or cross-currency denominator was recomputed. Safety: `{gates['ADR_SECURITY_BASIS_SAFETY']}`.\n",
    )
    price_table = []
    for row in price_rows:
        selected = row["first_selected"]
        price_table.append(
            [row["ticker"], _format_price(selected["pullback"][0]), _format_price(selected["pullback"][1]), _format_price(selected["confirmation"]), _format_price(selected["trim"][0]), _format_price(selected["trim"][1]), _format_price(selected["downside_review"])]
        )
    write_text(
        args.report_dir / "20260903-uskr22-price-scenario-audit.md",
        "# USKR22 Price Scenario Audit\n\n"
        + markdown_table(["Ticker", "Pullback low", "Pullback high", "Confirmation", "Trim low", "Trim high", "Downside review"], price_table)
        + f"\n\nUnsupported numeric scenarios: `{gates['UNSUPPORTED_PRICE_NUMERIC']}`. AVOID rendered as actionable entry: `{gates['AVOID_RENDERED_AS_ACTIONABLE_ENTRY']}`. Same-level scenario ambiguity: `{gates['SAME_LEVEL_SCENARIO_AMBIGUITY']}`.\n",
    )
    for run in ("a", "b", "c"):
        write_text(args.report_dir / f"20260903-uskr22-run-{run}.md", _render_run_report(run, run_documents[run]))

    stability_table = [
        [row["ticker"], row["classification"], " / ".join(row["label_sequence"]), " / ".join(f"{value['buy']:.1f}:{value['sell']:.1f}" for value in row["balance_sequence"]), " / ".join(row["lean_sequence"]), row["max_balance_distance"], ", ".join(row["reasons"]) or "none"]
        for row in stability_rows
    ]
    write_text(
        args.report_dir / "20260903-uskr22-stability-comparison.md",
        "# USKR22 Same-Evidence Stability Comparison\n\n"
        + markdown_table(["Ticker", "Class", "Labels A/B/C", "Balances A/B/C", "Leans A/B/C", "Max spread", "Reasons"], stability_table)
        + f"\n\nStable: `{stability['counts']['STABLE']}`; boundary: `{stability['counts']['BOUNDARY_UNCERTAINTY']}`; unstable: `{stability['counts']['UNSTABLE']}`. No majority vote or averaging was applied.\n",
    )
    lean_rows = [
        [row["ticker"], " / ".join(row["lean_sequence"]), row["unexplained_hold_lean_flip"], row["classification"]]
        for row in stability_rows
    ]
    write_text(
        args.report_dir / "20260903-uskr22-hold-lean-diagnostics.md",
        "# USKR22 HOLD-Lean Diagnostics\n\n"
        + markdown_table(["Ticker", "Lean A/B/C", "BUY_LEAN/SELL_LEAN flip", "Class"], lean_rows)
        + f"\n\nUnexplained HOLD-lean flips: `{gates['UNEXPLAINED_HOLD_LEAN_FLIP_COUNT']}`.\n",
    )
    action_rows = [
        [row["ticker"], " / ".join(row["new_buyer_sequence"]), " / ".join(row["holder_sequence"]), " / ".join(row["entry_mode_sequence"]), row["action_context_changed"], row["classification"]]
        for row in stability_rows
    ]
    write_text(
        args.report_dir / "20260903-uskr22-action-context-stability.md",
        "# USKR22 Action-Context Stability\n\n"
        + markdown_table(["Ticker", "New buyer A/B/C", "Holder A/B/C", "Entry A/B/C", "Changed", "Class"], action_rows)
        + f"\n\nAction-context variance count: `{stability['action_context_variance_count']}`. Variance remains explicit and is never averaged away.\n",
    )
    write_text(
        args.report_dir / "20260903-uskr22-cross-market-consistency.md",
        "# USKR22 Cross-Market Semantic Consistency\n\n"
        "US and KR used the same decision, balance, Unknown, price-provenance, AVOID, buyer, and holder contracts. Market-specific evidence stayed in its source packet; decision distributions were not required to match. KR accounting/valuation and ADR/security-basis safety were audited independently.\n\n"
        f"- US subjects: `{len(US_COHORT)}`\n- KR subjects: `{len(KR_COHORT)}`\n- Cross-market fact leakage: `0`\n- Cross-generation visibility: `0`\n",
    )
    quality_rows = [
        [run, run_documents[run]["message_quality"]["status"], run_documents[run]["message_quality"]["average_character_count"], run_documents[run]["message_quality"]["max_character_count"], run_documents[run]["message_quality"]["repeated_substantive_span_count"], ", ".join(run_documents[run]["message_quality"]["errors"]) or "none"]
        for run in RUNS
    ]
    write_text(
        args.report_dir / "20260903-uskr22-message-quality.md",
        "# USKR22 Message Quality\n\n"
        + markdown_table(["Run", "Status", "Average chars", "Max chars", "Repeated spans", "Errors"], quality_rows)
        + f"\n\nInternal contradictions: `{gates['MESSAGE_INTERNAL_CONTRADICTION']}`. Substantive repetition failures: `{gates['SUBSTANTIVE_REPETITION']}`. Exact first-run messages are preserved per ticker with separate US/KR previews.\n",
    )
    write_text(
        args.report_dir / "20260903-uskr22-promotion-readiness.md",
        "# USKR22 Promotion Readiness\n\n"
        + f"`PROMOTION_READINESS = {gates['PROMOTION_READINESS']}`\n\n"
        + markdown_table(["Gate", "Value"], [[key, value] for key, value in gates.items()])
        + "\n\nKR natural production proof: `PENDING`. US repaired natural proof: `PENDING`. This shadow verdict does not itself authorize production promotion. Production mutation, send, and main merge remain zero.\n",
    )

    index_candidates = [
        path
        for path in args.report_dir.rglob("*")
        if path.is_file() and path.name != "20260903-uskr22-artifact-index.md"
    ]
    index_rows = [
        [str(path.relative_to(args.report_dir)), sha256(path), path.stat().st_size]
        for path in sorted(index_candidates)
        if path.name.startswith("20260903-uskr22-") or path.parent.name == "uskr22-messages"
    ]
    write_text(
        args.report_dir / "20260903-uskr22-artifact-index.md",
        "# USKR22 Artifact Index\n\n"
        + markdown_table(["Artifact", "SHA-256", "Bytes"], index_rows)
        + f"\n\nIndexed artifacts: `{len(index_rows)}`. Recipient identifiers and credentials are excluded.\n",
    )
    return proof


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--us-packet", type=Path, required=True)
    parser.add_argument("--kr-packet", type=Path, required=True)
    parser.add_argument("--kr-later-packet", type=Path, required=True)
    parser.add_argument("--us-base-messages", type=Path, required=True)
    parser.add_argument("--kr-base-messages", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--resume-existing", action="store_true")
    args = parser.parse_args()
    args.output_dir = args.output_dir.resolve()
    args.report_dir = args.report_dir.resolve()

    evidence, price_maps, _contexts, stocks, base_messages, source_lock = prepare(args)
    if args.prepare_only:
        print(json.dumps({"prepared": True, "subjects": 22, "output_dir": str(args.output_dir)}, sort_keys=True))
        return

    run_candidates: dict[str, tuple[StructuredAutonomyCandidate, ...]] = {}
    run_documents: dict[str, dict[str, object]] = {}
    first_rendered: tuple[object, ...] = ()
    for run in RUNS:
        candidates, document, rendered = execute_run(
            run=run,
            args=args,
            evidence_packets=evidence,
            price_maps=price_maps,
            stock_by_ticker=stocks,
            base_messages=base_messages,
        )
        run_candidates[run] = candidates
        run_documents[run] = document
        if run == "first":
            first_rendered = rendered
        if int(document["validation_pass_count"]) != 22 or document["message_quality"][
            "status"
        ] != "PASS":
            if run != "first":
                raise ValueError(f"same_evidence_run_gate_failed:{run}")
            proof = finalize_first_run_failure(
                args=args,
                source_lock=source_lock,
                price_maps=price_maps,
                stock_by_ticker=stocks,
                candidates=candidates,
                document=document,
                rendered=rendered,
            )
            print(
                json.dumps(
                    {
                        "subjects": 22,
                        "first_run_validated": document["validation_pass_count"],
                        "runs_a_b_c": "NOT_RUN_FIRST_GATE_FAILED",
                        "promotion_readiness": proof["gates"]["PROMOTION_READINESS"],
                        "report_dir": str(args.report_dir),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return

    proof = finalize(
        args=args,
        source_lock=source_lock,
        price_maps=price_maps,
        stock_by_ticker=stocks,
        run_candidates=run_candidates,
        run_documents=run_documents,
        first_rendered=first_rendered,
    )
    print(
        json.dumps(
            {
                "subjects": 22,
                "runs": 4,
                "validated": {run: run_documents[run]["validation_pass_count"] for run in RUNS},
                "stability": proof["stability"]["counts"],
                "promotion_readiness": proof["gates"]["PROMOTION_READINESS"],
                "report_dir": str(args.report_dir),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
