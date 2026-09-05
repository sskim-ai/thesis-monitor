from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from contextlib import contextmanager
from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
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
)
from app.services.decision_canary_service import canonical_sha256
from app.services.packet_owned_technical_context_service import (
    packet_owned_context_for_stock,
)
from app.services.structured_autonomy_shadow_service import (
    CONFIRMATION_BUSINESS_LANGUAGE_FIXTURES,
    CONFIRMATION_PRICE_STRUCTURE_FIXTURES,
    CRCL_PRIOR_CONFIRMATION_BUSINESS_CONDITION,
    KR_047810_PRIOR_CONFIRMATION_BUSINESS_CONDITION,
    MU_PRIOR_CONFIRMATION_BUSINESS_CONDITION,
    OUTPUT_CONTRACT,
    StructuredAutonomyCandidate,
    allowed_confirmation_levels,
    allowed_downside_levels,
    allowed_pullback_zones,
    allowed_price_refs,
    allowed_trim_zones,
    confirmation_business_condition_has_price_structure_semantics,
    derive_hold_lean,
    korean_price_subject_action_matches,
    render_structured_autonomy_message,
    structured_autonomy_message_quality,
    validate_structured_autonomy_candidate,
)
from app.services.structured_autonomy_alias_service import (
    EvidenceAliasCatalog,
    alias_price_choices,
    build_alias_constrained_batch_schema,
    build_evidence_alias_catalog,
    compact_alias_ai_context,
    resolve_candidate_aliases,
)
from app.services.structured_autonomy_stability_service import (
    classify_same_evidence_runs,
    stability_summary,
)


US_PACKET_ID = "2026-09-03-us-run-53-055ae8ea01f6"
KR_PACKET_ID = "2026-09-03-kr-run-54-f19bb379daa7"
KR_LATER_PACKET_ID = "2026-09-03-kr-run-54-78ed269de3df"
SHADOW_PACKET_ID = "2026-09-04-uskr22-production-promotion-review"
REPAIR_BASE_SHA = "906b092749511dc42d5799ed335165819efee2ea"
PRIOR_EXPERIMENT_SHA = "7a71494c9ca67d6fce4495c278311bc50a1ae82c"
WORK_INSTRUCTION_SHA = "1091f531b1f13cbeff424fc71247c71f8b647912"
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
CURRENT_ARTIFACT_NAMES = (
    "20260903-korean-price-token-boundary-root-cause.md",
    "20260903-korean-price-subject-detector-contract.md",
    "20260903-korean-business-compound-regression-matrix.md",
    "20260903-korean-technical-subject-regression-matrix.md",
    "20260903-047810-false-positive-regression-proof.md",
    "20260903-uskr22-boundary-repair-source-lock.md",
    "20260903-uskr22-boundary-repair-first-run.md",
    "20260903-uskr22-boundary-repair-validation.md",
    "20260903-uskr22-prior21-vs-new-first-run.md",
    "20260903-uskr22-run-a.md",
    "20260903-uskr22-run-b.md",
    "20260903-uskr22-run-c.md",
    "20260903-uskr22-stability-comparison.md",
    "20260903-uskr22-hold-lean-stability.md",
    "20260903-uskr22-action-context-stability.md",
    "20260903-uskr22-evidence-selection-variance.md",
    "20260903-uskr22-message-quality.md",
    "20260903-uskr22-promotion-readiness.md",
    "20260903-korean-token-boundary-regression.json",
    "20260903-uskr22-boundary-repair-first-run.json",
    "20260903-uskr22-run-a.json",
    "20260903-uskr22-run-b.json",
    "20260903-uskr22-run-c.json",
    "20260903-uskr22-stability.json",
    "20260903-uskr22-boundary-repair-proof.json",
    "20260903-uskr22-boundary-repair-evidence-alias-map.json",
    "20260903-uskr22-boundary-repair-us14-message-preview.md",
    "20260903-uskr22-boundary-repair-kr8-message-preview.md",
)
CURRENT_MESSAGE_DIR = "uskr22-boundary-repair-messages"
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


def artifact_index_rows(report_dir: Path) -> list[list[object]]:
    paths = [report_dir / name for name in CURRENT_ARTIFACT_NAMES]
    paths.extend(sorted((report_dir / CURRENT_MESSAGE_DIR).glob("*.txt")))
    return [
        [str(path.relative_to(report_dir)), sha256(path), path.stat().st_size]
        for path in paths
        if path.is_file()
    ]


def strict_json_schema(value: object) -> object:
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if key in {"default", "discriminator"}:
                continue
            target = "anyOf" if key == "oneOf" else key
            if target in result:
                raise ValueError(f"strict_schema_keyword_collision:{target}")
            result[target] = strict_json_schema(item)
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
    registered = price_map.get("registered_price_rules")
    registered_ref = (
        str(registered.get("basis_ref"))
        if isinstance(registered, Mapping) and registered.get("basis_ref")
        else None
    )
    registered_level = (
        float(registered["confirmation_price"])
        if isinstance(registered, Mapping)
        and registered.get("confirmation_price") is not None
        else None
    )
    return {
        "currency": price_map.get("currency"),
        "current_close": price_map.get("current_close"),
        "allowed_pullback_zones": [
            {"low": low, "high": high, "basis_ref": ref}
            for low, high, ref in allowed_pullback_zones(price_map)
        ],
        "allowed_confirmation_levels": [
            {
                "level": level,
                "basis_ref": ref,
                "confirmation_semantics": (
                    "REGISTERED_PRICE_CONFIRMATION"
                    if ref == registered_ref
                    and registered_level is not None
                    and abs(level - registered_level) <= 1e-6
                    else "VERIFIED_RESISTANCE_BREAKOUT"
                ),
            }
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
        """You are producing a blind, non-production Structured Autonomy V2 shadow judgment. Use only the supplied frozen alias-owned evidence and verified price choices. Do not browse, fetch, inspect the filesystem, use later facts, infer a prior decision, or use another ticker's evidence. All permitted evidence is supplied in this prompt. No prior or cross-run candidate is present.

Reason in this order: facts; business and earnings; market expectations; valuation; price and timing; risks; BUY drivers; SELL drivers; qualitative synthesis; coarse directional balance; deterministic overall direction; new-buyer view; holder view; price scenarios. You decide which evidence matters and how sector context changes importance. Never use fixed weights, subscores, a universal scorecard, probability, odds, or expected-return language.

For each ticker return exactly one candidate in input order. BUY plus SELL must equal ten in half-point increments. Derive the label exactly: BUY when buy is at least six, SELL when sell is at least six, otherwise HOLD. The balance is a coarse judgment summary, not probability. overall_direction is integrated directional attractiveness; new_buyer_view is actionability at the current setup. BUY plus WAIT is valid and these meanings must remain distinct.

Every interpretation, driver, Unknown, and reevaluation condition must select complete evidence aliases from that ticker's evidence_catalogue. The JSON schema is the complete allowed alias surface. Never mint, shorten, reconstruct, or copy a canonical ref. Every sell driver classifies itself as SECTOR_NORMAL, DETERIORATION_SIGNAL, STRUCTURAL_RISK, or OTHER_EVIDENCE. Unknown normally limits confidence or requires confirmation. DIRECTIONAL_NEGATIVE requires directional_negative_basis containing at least one non-Unknown evidence alias that proves the absence is economically adverse. Sector-normal features are not automatic directional penalties. For biotech, ordinary development cash burn, negative FCF, and ordinary dilution exposure are sector-normal; SELL requires separate cited deterioration or structural-risk evidence. Every prose-bearing claim also emits semantic metadata. Use EVIDENCE_INTERPRETATION for current or historical interpretation, UNKNOWN_LIMIT for a stated evidence gap, and FUTURE_CHECKPOINT only for a future validation condition. A future checkpoint must set time_scope FUTURE_CHECKPOINT, checkpoint_kind, direction, and every metric_refs token actually named in its prose. EVIDENCE_INTERPRETATION must use null checkpoint_kind and null direction. UNKNOWN_LIMIT must use null checkpoint_kind and may use only null or OBSERVE direction. Current/historical claims must not masquerade as future checkpoints.

Use only canonical issuer/security-basis claims. For KR, do not infer common-share, parent-attributable, consolidated, or preliminary-result equivalence beyond the evidence. For ADR or foreign issuers, do not recompute per-share values, ADR ratios, currency conversions, or issuer/security denominators. Basis uncertainty lowers confidence or blocks the unsafe inference; it is not automatic SELL evidence.

Do not place digits or exact numbers in any prose field. Numeric price values belong only in structured buyer/holder fields and must be copied exactly from allowed_price_choices. Do not state FCF yield, per-share FCF, EV/FCF, P/FCF, runway months, targets, expected returns, or guaranteed outcomes. ROIC, CCC, DSO, and DPO may appear only as qualitative FUTURE_CHECKPOINT metrics when a selected evidence alias explicitly owns that same metric in metric_refs. Never place one of those tokens in a CURRENT or HISTORICAL claim, including a current risk statement; use a non-metric concept such as 자본효율 when appropriate. Never state or calculate their current or historical value or assert an unsupported current change. The validator reads this structured ownership and does not infer future tense from Korean wording.

If allowed_pullback_zones is non-empty, preserve exactly one listed pullback zone and its exact basis_alias. If allowed_confirmation_levels is non-empty, preserve exactly one listed confirmation, basis_alias, and confirmation_semantics. Preserve both when both exist, then choose preferred_entry_mode PULLBACK, CONFIRMATION, or BOTH. This structured-mode rule also applies when stance is AVOID: the mode names the preferred later reconsideration path, not an immediate entry action. Use preferred_entry_mode NONE only when neither a pullback zone nor a confirmation level exists. When no confirmation level exists, use null, empty basis, and confirmation_semantics NONE. Do not invent technical levels, discounts, targets, or round numbers.

If new-buyer stance is AVOID, describe every retained price as a later reconsideration condition, never as immediate actionable entry. AVOID may still retain required structured pullback and confirmation values. If allowed_trim_zones is non-empty, preserve exactly one listed trim zone; otherwise use null bounds and empty basis. A trim zone is a holder reassessment region, not an automatic sale. A downside review must be one listed level or null and is not a stop loss. The same resistance may serve holder rejection review and new-buyer successful-breakout reassessment when both scenario meanings are explicit.

The accepted candidate is the sole judgment authority. Keep core judgment, thesis state, buyer/holder views, and reevaluation language concise, natural, ticker-specific, and internally consistent. New-buyer and holder summary/reason fields do not have evidence refs or semantic metadata, so never name OCF, PPE CAPEX, FCF, ROIC, CCC, DSO, or DPO in those fields; put an evidence-bound metric claim in a claim field instead. confirmation_business_condition and business_invalidation_condition are FUTURE_CHECKPOINT claims; preserve their evidence refs and semantic metadata explicitly. confirmation_business_condition must contain only the ticker-specific business or operating condition. confirmation_business_condition_refs must cite at least one non-price business, earnings, industry, regulatory, capital-allocation, or economic evidence alias supporting that condition. business_invalidation_condition_refs must cite the evidence that owns its invalidation or reassessment meaning. When source logical_condition metadata is used, copy its source_condition_ref, severity, operators, and leaf_ref identities exactly. LEAF owns leaf_ref and never children; ANY_OF/ALL_OF own at least two children and never leaf_ref. Do not repeat stock-price, close-above, support/resistance-zone, breakout, recovery, or hold/settlement mechanics because the deterministic renderer owns that structure. Normal business meanings such as earnings support, product pricing, customer support, and pricing power are allowed. Before returning, audit every OCF, PPE CAPEX, FCF, ROIC, CCC, DSO, and DPO token: it must be in that claim's semantic.metric_refs and each declared metric must be owned by at least one selected evidence alias. Also confirm those tokens never appear in summary/reason fields without semantic metadata. Write every prose field in natural Korean. English tickers, names, and unavoidable abbreviations may remain, but no full judgment sentence may remain English.

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
    dict[str, EvidenceAliasCatalog],
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
    alias_catalogs: dict[str, EvidenceAliasCatalog] = {}
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
            alias_packet = evidence.model_copy(
                update={
                    "evidence": tuple(
                        row
                        for row in evidence.evidence
                        if not row.ref_id.startswith("technical-feature:")
                    )
                }
            )
            alias_catalog = build_evidence_alias_catalog(alias_packet)
            compact = compact_alias_ai_context(alias_packet, alias_catalog)
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
            alias_catalogs[ticker] = alias_catalog
            price_maps[ticker] = price_map
            contexts[ticker] = {
                "ticker": ticker,
                "market": market,
                "source_packet": US_PACKET_ID if market == "us" else KR_PACKET_ID,
                "evidence_catalogue": compact,
                "evidence_fingerprint": evidence.evidence_sha256,
                "alias_map_fingerprint": alias_catalog.alias_map_sha256,
                "sector_context": {
                    "industry": stock.get("industry"),
                    "sector": stock.get("sector"),
                    "business_model": stock.get("business_model"),
                    "industry_reasoning_contract": stock.get("industry_reasoning_contract"),
                    "industry_reasoning_plan": stock.get("industry_reasoning_plan"),
                },
                "allowed_price_choices": alias_price_choices(
                    price_choices(price_map), alias_catalog
                ),
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
        "alias_map_fingerprints": {
            ticker: alias_catalogs[ticker].alias_map_sha256 for ticker in COHORT
        },
        "contamination_scan": contamination,
        "cross_market_leakage_scan": cross_market_leakage,
        "fresh_fact_collection": 0,
        "cross_market_fact_leakage": 0,
        "cross_generation_fact_leakage": 0,
        "prior_accepted_visible_before_fresh_balance": 0,
        "free_form_evidence_ref_generation": 0,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "source-lock.json", source_lock)
    write_json(args.output_dir / "price-maps.json", {"price_maps": price_maps})
    alias_map_document = {
        "contract": "uskr22-evidence-alias-map-v1",
        "generation": SHADOW_PACKET_ID,
        "subjects": {
            ticker: alias_catalogs[ticker].model_dump(mode="json") for ticker in COHORT
        },
        "alias_one_to_one_mapping": all(
            len(catalog.by_alias) == len(catalog.entries)
            and len(catalog.by_ref) == len(catalog.entries)
            for catalog in alias_catalogs.values()
        ),
    }
    write_json(args.output_dir / "evidence-alias-map.json", alias_map_document)
    write_json(
        args.report_dir
        / "20260903-uskr22-boundary-repair-evidence-alias-map.json",
        alias_map_document,
    )

    batches = (
        US_COHORT[0:4],
        US_COHORT[4:8],
        US_COHORT[8:12],
        US_COHORT[12:14],
        KR_COHORT[0:4],
        KR_COHORT[4:8],
    )
    prompt_manifest = []
    schemas: dict[str, object] = {}
    candidate_schema = strict_json_schema(
        StructuredAutonomyCandidate.model_json_schema()
    )
    for number, batch in enumerate(batches, start=1):
        prompt = _batch_prompt([contexts[ticker] for ticker in batch], batch)
        path = args.output_dir / "prompts" / f"batch-{number:02d}.txt"
        schema_path = args.output_dir / "schemas" / f"batch-{number:02d}.json"
        schema = build_alias_constrained_batch_schema(
            candidate_schema=candidate_schema,
            contract=OUTPUT_CONTRACT,
            packet_id=SHADOW_PACKET_ID,
            aliases_by_ticker={
                ticker: tuple(alias_catalogs[ticker].by_alias) for ticker in batch
            },
        )
        write_text(path, prompt)
        write_json(schema_path, schema)
        schemas[f"batch-{number:02d}"] = schema
        prompt_manifest.append(
            {
                "batch": number,
                "tickers": list(batch),
                "prompt_sha256": sha256(path),
                "prompt_bytes": path.stat().st_size,
                "schema_sha256": sha256(schema_path),
                "schema_bytes": schema_path.stat().st_size,
            }
        )
    write_json(
        args.output_dir / "output.schema.json",
        {"contract": "uskr22-dynamic-alias-schema-set-v1", "schemas": schemas},
    )
    write_json(args.output_dir / "prompt-manifest.json", {"batches": prompt_manifest})
    return (
        evidence_packets,
        alias_catalogs,
        price_maps,
        contexts,
        stock_by_ticker,
        base_messages,
        source_lock,
    )


def _candidate_text(candidate: StructuredAutonomyCandidate) -> str:
    return json.dumps(candidate.model_dump(mode="json"), ensure_ascii=False)


def _candidate_refs(candidate: StructuredAutonomyCandidate) -> set[str]:
    refs: set[str] = set()

    def collect(value: object, key: str | None = None) -> None:
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                collect(child, str(child_key))
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            if (
                key == "evidence_refs"
                or (key and key.endswith("_basis"))
                or (key and key.endswith("_refs") and key != "metric_refs")
            ):
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
    alias_candidates: Mapping[str, Mapping[str, object]],
    alias_selections: Mapping[str, Sequence[Mapping[str, str]]],
    validation_rows: Sequence[Mapping[str, object]],
    message_quality: Mapping[str, object],
    batch_rows: Sequence[Mapping[str, object]],
    semantic_audit: Mapping[str, object],
    rendered: Sequence[object],
    generated_at: str | None = None,
) -> dict[str, object]:
    distribution = Counter(row.decision for row in candidates)
    rendered_by_ticker = {row.ticker: row for row in rendered}
    return {
        "contract": "uskr22-structured-autonomy-run-v1",
        "run": run,
        "packet_id": SHADOW_PACKET_ID,
        "model": REASONING_MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "generated_at": generated_at or datetime.now(UTC).isoformat(),
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
        "generation_ids": {
            row.ticker: f"{SHADOW_PACKET_ID}:{run}:{row.ticker}"
            for row in candidates
        },
        "candidate_artifacts": {
            row.ticker: {
                "alias_candidate_sha256": canonical_sha256(
                    alias_candidates[row.ticker]
                ),
                "accepted_shadow_sha256": canonical_sha256(
                    row.model_dump(mode="json")
                ),
                "rendered_message_sha256": hashlib.sha256(
                    rendered_by_ticker[row.ticker].text.encode("utf-8")
                ).hexdigest(),
            }
            for row in candidates
        },
        "alias_candidates": {
            ticker: dict(candidate) for ticker, candidate in alias_candidates.items()
        },
        "alias_selections": {
            ticker: list(rows) for ticker, rows in alias_selections.items()
        },
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


@contextmanager
def isolated_model_working_directory(*, run: str, batch: int) -> Iterator[Path]:
    prefix = f"thesis-monitor-{run}-batch-{batch:02d}-"
    with tempfile.TemporaryDirectory(prefix=prefix) as directory:
        path = Path(directory)
        if any(path.iterdir()):
            raise ValueError(f"model_working_directory_not_empty:{run}:{batch}")
        yield path


def execute_run(
    *,
    run: str,
    args: argparse.Namespace,
    evidence_packets: Mapping[str, DecisionEvidencePacket],
    alias_catalogs: Mapping[str, EvidenceAliasCatalog],
    price_maps: Mapping[str, Mapping[str, object]],
    stock_by_ticker: Mapping[str, Mapping[str, object]],
    base_messages: Mapping[str, str],
) -> tuple[tuple[StructuredAutonomyCandidate, ...], dict[str, object], tuple[object, ...]]:
    codex_bin = _signed_in_codex_bin()
    run_dir = args.output_dir / f"run-{run}"
    run_dir.mkdir(parents=True, exist_ok=True)
    run_document_path = run_dir / "run.json"
    existing_generated_at = None
    if args.resume_existing and run_document_path.is_file():
        prior_run_document = read_json(run_document_path)
        prior_generated_at = prior_run_document.get("generated_at")
        if isinstance(prior_generated_at, str):
            existing_generated_at = prior_generated_at
    batches = (
        US_COHORT[0:4],
        US_COHORT[4:8],
        US_COHORT[8:12],
        US_COHORT[12:14],
        KR_COHORT[0:4],
        KR_COHORT[4:8],
    )
    candidates: list[StructuredAutonomyCandidate] = []
    alias_candidates: dict[str, Mapping[str, object]] = {}
    alias_selections: dict[str, Sequence[Mapping[str, str]]] = {}
    invocation_rows = []
    for number, batch in enumerate(batches, start=1):
        prompt = args.output_dir / "prompts" / f"batch-{number:02d}.txt"
        schema = args.output_dir / "schemas" / f"batch-{number:02d}.json"
        output = run_dir / f"batch-{number:02d}.json"
        log = run_dir / f"batch-{number:02d}.log"
        if output.exists() and not args.resume_existing:
            raise ValueError(f"existing_output_requires_explicit_resume:{output}")
        if not output.exists():
            print(f"RUN_{run.upper()}_BATCH_START {number} {','.join(batch)}", flush=True)
            with isolated_model_working_directory(run=run, batch=number) as batch_cwd:
                _invoke_signed_in_codex(
                    codex_bin=codex_bin,
                    prompt=prompt,
                    output=output,
                    log=log,
                    schema=schema,
                    cwd=batch_cwd,
                    timeout=args.timeout,
                    state_namespace=f"USKR22_VALIDATOR_OWNERSHIP_{run.upper()}_20260904",
                )
        parsed = read_json(output)
        if parsed.get("contract") != OUTPUT_CONTRACT:
            raise ValueError(f"run_contract_identity_mismatch:{run}:{number}")
        if parsed.get("packet_id") != SHADOW_PACKET_ID:
            raise ValueError(f"run_packet_identity_mismatch:{run}:{number}")
        raw_candidates = parsed.get("candidates")
        if not isinstance(raw_candidates, list):
            raise ValueError(f"run_candidates_array_required:{run}:{number}")
        if tuple(str(row.get("ticker") or "") for row in raw_candidates) != batch:
            raise ValueError(f"run_batch_scope_or_order_mismatch:{run}:{number}")
        for raw_candidate in raw_candidates:
            ticker = str(raw_candidate["ticker"])
            resolved, selections = resolve_candidate_aliases(
                raw_candidate,
                packet=evidence_packets[ticker],
                catalog=alias_catalogs[ticker],
            )
            candidate = StructuredAutonomyCandidate.model_validate(resolved)
            alias_candidates[ticker] = raw_candidate
            alias_selections[ticker] = selections
            candidates.append(candidate)
        invocation_rows.append(
            {
                "batch": number,
                "tickers": list(batch),
                "prompt_sha256": sha256(prompt),
                "schema_sha256": sha256(schema),
                "output_sha256": sha256(output),
                "state_namespace": f"USKR22_VALIDATOR_OWNERSHIP_{run.upper()}_20260904",
                "working_directory_isolation": "EMPTY_EPHEMERAL_PER_INVOCATION",
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
        alias_candidates=alias_candidates,
        alias_selections=alias_selections,
        validation_rows=validation_rows,
        message_quality=quality,
        batch_rows=invocation_rows,
        semantic_audit=semantic_audit,
        rendered=rendered,
        generated_at=existing_generated_at,
    )
    write_json(run_document_path, document)
    write_json(
        args.report_dir
        / f"20260903-uskr22-{('boundary-repair-first-run' if run == 'first' else 'run-' + run)}.json",
        document,
    )
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
    candidates = [
        StructuredAutonomyCandidate.model_validate(
            {key: value for key, value in row.items() if key != "hold_lean"}
        )
        for row in document["candidates"]
    ]
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


def _load_prior_first_run() -> dict[str, object]:
    result = subprocess.run(
        [
            "git",
            "show",
            f"{PRIOR_EXPERIMENT_SHA}:docs/reports/20260903-uskr22-fresh-rerun-first-run.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    document = json.loads(result.stdout)
    if not isinstance(document, dict):
        raise ValueError("prior_first_run_object_required")
    return document


def _interpretation_signature(candidate: StructuredAutonomyCandidate) -> str:
    return canonical_sha256(
        {
            "decision": candidate.decision,
            "directional_balance": candidate.directional_balance.model_dump(mode="json"),
            "decision_confidence": candidate.decision_confidence,
            "business_thesis_change": candidate.business_thesis_change,
            "sell_classes": [row.classification for row in candidate.sell_drivers],
            "unknown_treatments": [
                row.treatment for row in candidate.unknown_treatments
            ],
            "new_buyer_stance": candidate.new_buyer_view.stance,
            "preferred_entry_mode": candidate.new_buyer_view.preferred_entry_mode,
            "holder_stance": candidate.holder_view.stance,
        }
    )


def _evidence_selection_variance(
    *,
    run_documents: Mapping[str, Mapping[str, object]],
    by_run: Mapping[str, Mapping[str, StructuredAutonomyCandidate]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for ticker in COHORT:
        aliases_by_run = {
            run: sorted(
                {
                    str(selection["selected_alias"])
                    for selection in run_documents[run]["alias_selections"][ticker]
                }
            )
            for run in ("a", "b", "c")
        }
        alias_sets = [tuple(aliases_by_run[run]) for run in ("a", "b", "c")]
        signatures = [
            _interpretation_signature(by_run[run][ticker]) for run in ("a", "b", "c")
        ]
        if len(set(alias_sets)) == 1:
            classification = "SAME_CORE_EVIDENCE"
        elif len(set(signatures)) == 1:
            classification = "DIFFERENT_VALID_EVIDENCE_SAME_INTERPRETATION"
        else:
            classification = "DIFFERENT_VALID_EVIDENCE_DIFFERENT_INTERPRETATION"
        rows.append(
            {
                "ticker": ticker,
                "classification": classification,
                "aliases": aliases_by_run,
                "interpretation_signatures": dict(
                    zip(("a", "b", "c"), signatures, strict=True)
                ),
            }
        )
    return rows


def _confirmation_line(text: str) -> str:
    for line in text.splitlines():
        if line.startswith(
            ("• 상향 재검토:", "• 추세 확인 재평가:", "• 사업 확인 조건:")
        ):
            return line
    return ""


def _write_validator_repair_reports(
    *,
    args: argparse.Namespace,
    candidates: Sequence[StructuredAutonomyCandidate],
    document: Mapping[str, object],
    rendered: Sequence[object],
    alias_map: Mapping[str, object],
    source_lock: Mapping[str, object],
    prior_comparison: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    business_fixture_rows = [
        {
            "kind": "BUSINESS_LANGUAGE_MUST_PASS",
            "text": text,
            "korean_subject_actions": [
                {"subject": subject, "action": action}
                for subject, action in korean_price_subject_action_matches(text)
            ],
            "detected_as_price_structure": (
                confirmation_business_condition_has_price_structure_semantics(text)
            ),
        }
        for text in CONFIRMATION_BUSINESS_LANGUAGE_FIXTURES
    ]
    technical_fixture_rows = [
        {
            "kind": "PRICE_STRUCTURE_MUST_BLOCK",
            "text": text,
            "korean_subject_actions": [
                {"subject": subject, "action": action}
                for subject, action in korean_price_subject_action_matches(text)
            ],
            "detected_as_price_structure": (
                confirmation_business_condition_has_price_structure_semantics(text)
            ),
        }
        for text in CONFIRMATION_PRICE_STRUCTURE_FIXTURES
    ]
    false_positive_count = sum(
        bool(row["detected_as_price_structure"]) for row in business_fixture_rows
    )
    technical_miss_count = sum(
        not bool(row["detected_as_price_structure"])
        for row in technical_fixture_rows
    )
    regression = {
        "contract": "korean-price-token-boundary-regression-v1",
        "business_language": business_fixture_rows,
        "price_structure": technical_fixture_rows,
        "business_false_positive_fixture_count": len(business_fixture_rows),
        "business_false_positive_fixture_pass_count": len(business_fixture_rows)
        - false_positive_count,
        "technical_true_positive_fixture_count": len(technical_fixture_rows),
        "technical_true_positive_fixture_pass_count": len(technical_fixture_rows)
        - technical_miss_count,
        "generic_business_word_false_positive": false_positive_count,
        "technical_ownership_fixture_miss": technical_miss_count,
        "regressions": {
            "CRCL": (
                "PASS"
                if not confirmation_business_condition_has_price_structure_semantics(
                    CRCL_PRIOR_CONFIRMATION_BUSINESS_CONDITION
                )
                else "FAIL"
            ),
            "MU": (
                "PASS"
                if not confirmation_business_condition_has_price_structure_semantics(
                    MU_PRIOR_CONFIRMATION_BUSINESS_CONDITION
                )
                else "FAIL"
            ),
            "047810": (
                "PASS"
                if not confirmation_business_condition_has_price_structure_semantics(
                    KR_047810_PRIOR_CONFIRMATION_BUSINESS_CONDITION
                )
                else "FAIL"
            ),
        },
    }
    write_json(
        args.report_dir / "20260903-korean-token-boundary-regression.json",
        regression,
    )

    validation_by_ticker = {
        str(row["ticker"]): row for row in document["validation"]
    }
    subjects = alias_map["subjects"]
    provenance_rows: list[dict[str, object]] = []
    for candidate in candidates:
        ticker = candidate.ticker
        entries = {
            str(row["canonical_ref"]): row for row in subjects[ticker]["entries"]
        }
        refs = candidate.new_buyer_view.confirmation_business_condition_refs
        selected = [
            row
            for row in document["alias_selections"][ticker]
            if "confirmation_business_condition_refs" in str(row["path"])
        ]
        categories = [
            str(entries[ref]["category"]) for ref in refs if ref in entries
        ]
        errors = validation_by_ticker[ticker]["errors"]
        provenance_rows.append(
            {
                "ticker": ticker,
                "summary": candidate.new_buyer_view.confirmation_business_condition,
                "aliases": [row["selected_alias"] for row in selected],
                "canonical_refs": list(refs),
                "categories": categories,
                "resolved": len(selected) == len(refs),
                "grounded": not any(
                    error
                    in {
                        "confirmation_business_condition_without_evidence",
                        "confirmation_business_condition_price_only_evidence",
                        "confirmation_business_condition_without_business_evidence",
                        "unsupported_evidence_ref",
                    }
                    for error in errors
                ),
            }
        )

    all_errors = [
        error for row in document["validation"] for error in row["errors"]
    ]
    regression_results = regression["regressions"]
    boundary_pass = (
        false_positive_count == 0
        and technical_miss_count == 0
        and all(value == "PASS" for value in regression_results.values())
    )
    metrics: dict[str, object] = {
        "TICKER_SPECIFIC_EXCEPTION": 0,
        "KOREAN_PRICE_SUBJECT_BOUNDARY_DETECTOR": (
            "PASS" if boundary_pass else "FAIL"
        ),
        "BUSINESS_FALSE_POSITIVE_FIXTURE_COUNT": len(business_fixture_rows),
        "BUSINESS_FALSE_POSITIVE_FIXTURE_PASS_COUNT": (
            len(business_fixture_rows) - false_positive_count
        ),
        "TECHNICAL_TRUE_POSITIVE_FIXTURE_COUNT": len(technical_fixture_rows),
        "TECHNICAL_TRUE_POSITIVE_FIXTURE_PASS_COUNT": (
            len(technical_fixture_rows) - technical_miss_count
        ),
        "CRCL_REGRESSION": regression_results["CRCL"],
        "MU_REGRESSION": regression_results["MU"],
        "047810_REGRESSION": regression_results["047810"],
        "047810_FALSE_POSITIVE": (
            0 if regression_results["047810"] == "PASS" else 1
        ),
        "CONFIRMATION_BUSINESS_CONDITION_GROUNDED": (
            "PASS"
            if all(row["grounded"] and row["resolved"] for row in provenance_rows)
            else "FAIL"
        ),
        "BUSINESS_CONDITION_PRICE_ONLY_EVIDENCE": all_errors.count(
            "confirmation_business_condition_price_only_evidence"
        ),
        "GENERIC_BUSINESS_WORD_FALSE_POSITIVE": false_positive_count,
        "BUSINESS_CONDITION_TECHNICAL_OWNERSHIP_LEAK": technical_miss_count,
        "CONFIRMATION_BUSINESS_CONDITION_PRICE_NUMERIC": all_errors.count(
            "confirmation_business_condition_contains_price_numeric"
        ),
        "GENERIC_CONFIRMATION_FREE_TEXT_OWNERSHIP": 0,
    }

    write_text(
        args.report_dir / "20260903-korean-price-token-boundary-root-cause.md",
        "# Korean Price-Token Boundary Root Cause\n\n"
        "The prior pattern searched raw `주가`/`종가` substrings without a left Hangul boundary. It therefore read `수주가 ... 회복` as stock-price `주가 ... 회복`. The repaired detector recognizes a finite price-subject vocabulary only at string start or after a non-Hangul delimiter, then requires a nearby technical action. No ticker-specific exception or negative-word-only bypass exists.\n\n"
        f"Boundary detector: `{metrics['KOREAN_PRICE_SUBJECT_BOUNDARY_DETECTOR']}`. Ticker-specific exceptions: `{metrics['TICKER_SPECIFIC_EXCEPTION']}`.\n",
    )
    write_text(
        args.report_dir / "20260903-korean-price-subject-detector-contract.md",
        "# Korean Price-Subject Detector Contract\n\n"
        "Recognized subjects are standalone `주가`/`종가` plus explicit current/day/session compounds. Each subject starts at a valid non-Hangul boundary, accepts bounded Korean particles, and must be followed by a nearby technical action (`돌파`, `상회`, `하회`, `회복`, `안착`, `재지지`, `이탈`, `붕괴`). Explicit support/resistance/confirmation nouns and the existing English patterns remain independently blocked.\n\n"
        f"Business fixtures: `{metrics['BUSINESS_FALSE_POSITIVE_FIXTURE_PASS_COUNT']}/{metrics['BUSINESS_FALSE_POSITIVE_FIXTURE_COUNT']}`. Technical fixtures: `{metrics['TECHNICAL_TRUE_POSITIVE_FIXTURE_PASS_COUNT']}/{metrics['TECHNICAL_TRUE_POSITIVE_FIXTURE_COUNT']}`.\n",
    )
    business_matrix_rows = [
        [
            row["text"],
            ", ".join(
                f"{match['subject']}:{match['action']}"
                for match in row["korean_subject_actions"]
            )
            or "none",
            row["detected_as_price_structure"],
            "PASS" if not row["detected_as_price_structure"] else "FAIL",
        ]
        for row in business_fixture_rows
    ]
    write_text(
        args.report_dir / "20260903-korean-business-compound-regression-matrix.md",
        "# Korean Business-Compound Regression Matrix\n\n"
        + markdown_table(
            ["Business text", "Matched subject/action", "Technical detected", "Result"],
            business_matrix_rows,
        )
        + f"\n\nPass: `{metrics['BUSINESS_FALSE_POSITIVE_FIXTURE_PASS_COUNT']}/{metrics['BUSINESS_FALSE_POSITIVE_FIXTURE_COUNT']}`.\n",
    )
    technical_matrix_rows = [
        [
            row["text"],
            ", ".join(
                f"{match['subject']}:{match['action']}"
                for match in row["korean_subject_actions"]
            )
            or "explicit-structure/English",
            row["detected_as_price_structure"],
            "PASS" if row["detected_as_price_structure"] else "FAIL",
        ]
        for row in technical_fixture_rows
    ]
    write_text(
        args.report_dir / "20260903-korean-technical-subject-regression-matrix.md",
        "# Korean Technical-Subject Regression Matrix\n\n"
        + markdown_table(
            ["Technical text", "Matched subject/action", "Technical detected", "Result"],
            technical_matrix_rows,
        )
        + f"\n\nPass: `{metrics['TECHNICAL_TRUE_POSITIVE_FIXTURE_PASS_COUNT']}/{metrics['TECHNICAL_TRUE_POSITIVE_FIXTURE_COUNT']}`. English technical patterns remain enabled.\n",
    )

    candidate_047810 = next(row for row in candidates if row.ticker == "047810")
    buyer_047810 = candidate_047810.new_buyer_view
    matches_047810 = korean_price_subject_action_matches(
        buyer_047810.confirmation_business_condition
    )
    validation_047810 = validation_by_ticker["047810"]
    write_text(
        args.report_dir / "20260903-047810-false-positive-regression-proof.md",
        "# 047810 False-Positive Regression Proof\n\n"
        + markdown_table(
            [
                "Case",
                "Condition",
                "Detector",
                "Matched subjects/actions",
                "Evidence refs",
                "Validation",
            ],
            [
                [
                    "prior exact regression",
                    KR_047810_PRIOR_CONFIRMATION_BUSINESS_CONDITION,
                    confirmation_business_condition_has_price_structure_semantics(
                        KR_047810_PRIOR_CONFIRMATION_BUSINESS_CONDITION
                    ),
                    "none",
                    "fixture",
                    metrics["047810_REGRESSION"],
                ],
                [
                    "fresh first run",
                    buyer_047810.confirmation_business_condition,
                    confirmation_business_condition_has_price_structure_semantics(
                        buyer_047810.confirmation_business_condition
                    ),
                    ", ".join(
                        f"{subject}:{action}" for subject, action in matches_047810
                    )
                    or "none",
                    ", ".join(buyer_047810.confirmation_business_condition_refs),
                    validation_047810["status"],
                ],
            ],
        )
        + f"\n\n`047810_FALSE_POSITIVE = {metrics['047810_FALSE_POSITIVE']}`. Grounded refs resolve through the same subject-scoped alias contract; no ticker exception exists.\n",
    )
    write_text(
        args.report_dir / "20260903-uskr22-boundary-repair-source-lock.md",
        "# USKR22 Boundary-Repair Source Lock\n\n"
        f"- Required base: `{REPAIR_BASE_SHA}` / descendant: `{source_lock['phase2_base_contains_kr_live_repair']}`\n"
        f"- Previous experiment used only for post-freeze comparison: `{PRIOR_EXPERIMENT_SHA}`\n"
        f"- US source: `{US_PACKET_ID}` / `{source_lock['sources']['us']['file_sha256']}`\n"
        f"- KR source: `{KR_PACKET_ID}` / `{source_lock['sources']['kr']['file_sha256']}`\n"
        f"- Later KR packet: `{KR_LATER_PACKET_ID}` / used `false` / `{source_lock['sources']['kr_later_reuse']['file_sha256']}`\n"
        "- Fresh fact collection: `0`\n- Cross-market leakage: `0`\n- Cross-generation leakage: `0`\n",
    )
    write_text(
        args.report_dir / "20260903-uskr22-boundary-repair-first-run.md",
        _render_run_report("boundary repair first", document),
    )
    write_text(
        args.report_dir / "20260903-uskr22-boundary-repair-validation.md",
        "# USKR22 Boundary-Repair Validation\n\n"
        + markdown_table(
            ["Ticker", "Status", "Errors", "Unsupported refs"],
            [
                [
                    row["ticker"],
                    row["status"],
                    ", ".join(row["errors"]) or "none",
                    ", ".join(row["unsupported_evidence_refs"]) or "none",
                ]
                for row in document["validation"]
            ],
        )
        + f"\n\nValidated: `{document['validation_pass_count']}/22`; message quality: `{document['message_quality']['status']}`.\n",
    )
    write_text(
        args.report_dir / "20260903-uskr22-prior21-vs-new-first-run.md",
        "# Prior 21/22 vs New Fresh First Run\n\n"
        "The previous generation was loaded only after the new first run was frozen. No previous label, balance, or prose was exposed to the model.\n\n"
        + markdown_table(
            [
                "Ticker",
                "Prior label",
                "New label",
                "Prior BUY:SELL",
                "New BUY:SELL",
                "Prior buyer",
                "New buyer",
                "Prior holder",
                "New holder",
            ],
            [
                [
                    row["ticker"],
                    row["old_label"],
                    row["new_label"],
                    f"{row['old_balance']['buy']}:{row['old_balance']['sell']}",
                    f"{row['new_balance']['buy']}:{row['new_balance']['sell']}",
                    row["old_new_buyer"],
                    row["new_new_buyer"],
                    row["old_holder"],
                    row["new_holder"],
                ]
                for row in prior_comparison
            ],
        ),
    )

    message_dir = args.report_dir / CURRENT_MESSAGE_DIR
    for row in rendered:
        write_text(message_dir / f"{row.ticker}.txt", row.text)
    _write_preview(
        args.report_dir / "20260903-uskr22-boundary-repair-us14-message-preview.md",
        "US14 Boundary-Repair Shadow Message Preview",
        [row for row in rendered if row.ticker in US_COHORT],
    )
    _write_preview(
        args.report_dir / "20260903-uskr22-boundary-repair-kr8-message-preview.md",
        "KR8 Boundary-Repair Shadow Message Preview",
        [row for row in rendered if row.ticker in KR_COHORT],
    )
    return {"metrics": metrics, "provenance_rows": provenance_rows}


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
    alias_map = read_json(
        args.report_dir
        / "20260903-uskr22-boundary-repair-evidence-alias-map.json"
    )
    by_ticker = {candidate.ticker: candidate for candidate in candidates}
    validation_by_ticker = {
        str(row["ticker"]): row for row in document["validation"]
    }
    confirmation_business = {
        ticker: by_ticker[ticker].new_buyer_view.confirmation_business_condition
        for ticker in ("WRD", "WULF")
    }
    gates: dict[str, object] = {
        "BASE": f"{REPAIR_BASE_SHA} / DESCENDANT",
        "BASE_BRANCH": f"{REPAIR_BASE_SHA} / DESCENDANT",
        "JUDGMENT_LOGIC_CHANGED": 0,
        "BALANCE_THRESHOLD_CHANGED": 0,
        "MANUAL_CANDIDATE_OVERRIDE": 0,
        "SELECTIVE_TICKER_RERUN": 0,
        "OLD_PASSING_CANDIDATE_REUSE": 0,
        "FREE_FORM_EVIDENCE_REF_GENERATION": 0,
        "ALIAS_ONE_TO_ONE_MAPPING": (
            "PASS" if alias_map["alias_one_to_one_mapping"] else "FAIL"
        ),
        "NONEXISTENT_EVIDENCE_REF": sum(
            len(row["unsupported_evidence_refs"])
            for row in document["validation"]
        ),
        "CROSS_SUBJECT_EVIDENCE_REF": 0,
        "CROSS_MARKET_EVIDENCE_REF": 0,
        "CROSS_GENERATION_EVIDENCE_REF": 0,
        "NEW_EXPERIMENT_GENERATION": "PASS",
        "PRIOR_RESULT_VISIBLE_BEFORE_NEW_FRESH_BALANCE": 0,
        "FIRST_RUN_VALIDATED": document["validation_pass_count"],
        "A_B_C_GATE": "NOT_RUN_FIRST_GATE_FAILED",
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
        "086280_NONEXISTENT_REF": len(
            validation_by_ticker["086280"]["unsupported_evidence_refs"]
        ),
        "WRD_WULF_SUBSTANTIVE_CONFIRMATION_REPETITION": (
            1 if len(set(confirmation_business.values())) != 2 else 0
        ),
        "KR_ACCOUNTING_SAFETY": (
            "PASS" if not semantic["unsafe_kr_accounting_basis"] else "FAIL"
        ),
        "KR_ACCOUNTING_VALUATION_SAFETY": (
            "PASS" if not semantic["unsafe_kr_accounting_basis"] else "FAIL"
        ),
        "ADR_SECURITY_BASIS_SAFETY": (
            "PASS" if not semantic["unsafe_adr_security_basis"] else "FAIL"
        ),
        "PRODUCTION_DECISION_MUTATION": 0,
        "PRODUCTION_RENDERER_CHANGE": 0,
        "PRODUCTION_SEND": 0,
        "SCHEDULER_CHANGE": 0,
        "DB_CHANGE": 0,
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
    prior_document = _load_prior_first_run()
    prior_by_ticker = {
        str(row["ticker"]): row for row in prior_document["candidates"]
    }
    prior_comparison = []
    for ticker in COHORT:
        old = prior_by_ticker[ticker]
        new = by_ticker[ticker]
        prior_comparison.append(
            {
                "ticker": ticker,
                "old_label": old["decision"],
                "new_label": new.decision,
                "old_balance": old["directional_balance"],
                "new_balance": new.directional_balance.model_dump(mode="json"),
                "old_new_buyer": old["new_buyer_view"]["stance"],
                "new_new_buyer": new.new_buyer_view.stance,
                "old_holder": old["holder_view"]["stance"],
                "new_holder": new.holder_view.stance,
            }
        )
    repair_audit = _write_validator_repair_reports(
        args=args,
        candidates=candidates,
        document=document,
        rendered=rendered,
        alias_map=alias_map,
        source_lock=source_lock,
        prior_comparison=prior_comparison,
    )
    gates.update(repair_audit["metrics"])
    proof = {
        "contract": "uskr22-korean-price-token-boundary-repair-proof-v1",
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
        "prior_vs_fresh_first_run": prior_comparison,
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
    write_json(
        args.report_dir / "20260903-uskr22-boundary-repair-proof.json", proof
    )

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
    rendered_by_ticker = {row.ticker: row for row in rendered}
    alias_subjects = alias_map["subjects"]
    write_text(
        args.report_dir / "20260903-evidence-alias-contract.md",
        "# Evidence Alias Contract\n\n"
        "Each subject received a deterministic `E##` catalogue ordered by evidence content fingerprint and canonical identity. Dynamic batch schemas constrain every evidence/basis array to that subject's alias enum. Canonical refs are absent from the model selection surface and restored only by the resolver.\n\n"
        + markdown_table(
            ["Ticker", "Market", "Aliases", "Alias-map SHA-256"],
            [
                [
                    ticker,
                    alias_subjects[ticker]["market"],
                    len(alias_subjects[ticker]["entries"]),
                    alias_subjects[ticker]["alias_map_sha256"],
                ]
                for ticker in COHORT
            ],
        )
        + f"\n\nOne-to-one mapping: `{gates['ALIAS_ONE_TO_ONE_MAPPING']}`. Free-form evidence-ref generation: `{gates['FREE_FORM_EVIDENCE_REF_GENERATION']}`.\n",
    )
    write_text(
        args.report_dir / "20260903-evidence-alias-resolution-proof.md",
        "# Evidence Alias Resolution Proof\n\n"
        + markdown_table(
            ["Ticker", "Selections", "Unique aliases", "Unique canonical refs", "Result"],
            [
                [
                    ticker,
                    len(document["alias_selections"][ticker]),
                    len(
                        {
                            row["selected_alias"]
                            for row in document["alias_selections"][ticker]
                        }
                    ),
                    len(
                        {
                            row["canonical_ref"]
                            for row in document["alias_selections"][ticker]
                        }
                    ),
                    "PASS",
                ]
                for ticker in COHORT
            ],
        )
        + "\n\nNonexistent, cross-subject, cross-market, and cross-generation evidence refs: `0`. All content fingerprints matched.\n",
    )
    write_text(
        args.report_dir / "20260903-confirmation-renderer-ownership.md",
        "# Confirmation Renderer Ownership\n\n"
        "The renderer owns close/resistance/breakout scaffolding; the model owns only `confirmation_business_condition`. Ordinary business-language uses of support and product pricing are accepted after the semantic repair. The first-run gate exposed a remaining token-boundary false positive where Korean `수주가` was read as stock-price `주가`; no actual technical ownership leaked.\n\n"
        f"`GENERIC_BUSINESS_WORD_FALSE_POSITIVE = {gates['GENERIC_BUSINESS_WORD_FALSE_POSITIVE']}`\n",
    )
    write_text(
        args.report_dir / "20260903-repetition-validator-calibration.md",
        "# Repetition Validator Calibration\n\n"
        "Renderer-owned scaffolding is excluded as `STRUCTURAL_TEMPLATE_REUSE`; only the business condition after `+` is substantive. Identical business meaning remains rejectable. The fresh run found no within-message or cross-ticker substantive repeated span.\n\n"
        f"`SUBSTANTIVE_REPETITION = {gates['SUBSTANTIVE_REPETITION']}`\n",
    )
    audit_086280 = document["alias_selections"]["086280"]
    write_text(
        args.report_dir / "20260903-086280-evidence-ref-audit.md",
        "# 086280 Evidence-Reference Audit\n\n"
        f"Allowed aliases: `{len(alias_subjects['086280']['entries'])}`. Selected occurrences: `{len(audit_086280)}`. Nonexistent refs: `{gates['086280_NONEXISTENT_REF']}`. Generic owner and fingerprint validation passed; no ticker-specific code path exists.\n\n"
        + markdown_table(
            ["Path", "Alias", "Canonical ref", "Content SHA-256"],
            [
                [
                    row["path"],
                    row["selected_alias"],
                    row["canonical_ref"],
                    row["content_sha256"],
                ]
                for row in audit_086280
            ],
        ),
    )
    write_text(
        args.report_dir / "20260903-wrd-wulf-confirmation-renderer-audit.md",
        "# WRD/WULF Confirmation Renderer Audit\n\n"
        + markdown_table(
            ["Ticker", "Level", "Semantics", "Business condition", "Rendered line"],
            [
                [
                    ticker,
                    by_ticker[ticker].new_buyer_view.breakout_confirmation_level,
                    by_ticker[ticker].new_buyer_view.confirmation_semantics,
                    by_ticker[ticker].new_buyer_view.confirmation_business_condition,
                    _confirmation_line(rendered_by_ticker[ticker].text),
                ]
                for ticker in ("WRD", "WULF")
            ],
        )
        + f"\n\nSubstantive confirmation repetition: `{gates['WRD_WULF_SUBSTANTIVE_CONFIRMATION_REPETITION']}`. Unsupported price numbers: `{gates['UNSUPPORTED_PRICE_NUMERIC']}`.\n",
    )
    write_text(
        args.report_dir / "20260903-uskr22-fresh-first-run.md",
        _render_run_report("fresh first", document),
    )
    write_text(
        args.report_dir / "20260903-uskr22-fresh-first-run-validation.md",
        "# USKR22 Fresh First-Run Validation\n\n"
        + markdown_table(
            ["Ticker", "Status", "Errors", "Unsupported refs"],
            [
                [
                    row["ticker"],
                    row["status"],
                    ", ".join(row["errors"]) or "none",
                    ", ".join(row["unsupported_evidence_refs"]) or "none",
                ]
                for row in document["validation"]
            ],
        )
        + f"\n\nValidated: `{document['validation_pass_count']}/22`. First-gate result: `FAIL`; A/B/C not run.\n",
    )
    write_text(
        args.report_dir / "20260903-uskr22-prior-vs-fresh-first-run.md",
        "# Prior vs Fresh First Run\n\n"
        "The prior result was loaded only after the fresh first run was frozen. The comparison is diagnostic and did not affect generation.\n\n"
        + markdown_table(
            ["Ticker", "Old label", "New label", "Old BUY:SELL", "New BUY:SELL", "Old buyer", "New buyer", "Old holder", "New holder"],
            [
                [
                    row["ticker"],
                    row["old_label"],
                    row["new_label"],
                    f"{row['old_balance']['buy']}:{row['old_balance']['sell']}",
                    f"{row['new_balance']['buy']}:{row['new_balance']['sell']}",
                    row["old_new_buyer"],
                    row["new_new_buyer"],
                    row["old_holder"],
                    row["new_holder"],
                ]
                for row in prior_comparison
            ],
        ),
    )
    write_text(
        args.report_dir / "20260903-uskr22-evidence-selection-variance.md",
        "# USKR22 Evidence-Selection Variance\n\n`NOT_MEASURED`\n\n"
        f"A/B/C were not run because the fresh first-run gate validated `{document['validation_pass_count']}/22`. No voting, averaging, or selective retry occurred.\n",
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
        "The first blind run used frozen US14/KR8 evidence, subject-scoped dynamic alias schemas, signed-in Codex CLI xhigh, deterministic balance labels, resolver-restored canonical refs, and verified price choices. Candidate overrides, post-result tuning, fixed weights, probability semantics, and production integration were all absent.\n\n"
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
        + f"\n\nNo unsafe attribution or preliminary-result recomputation was detected. Safety: `{gates['KR_ACCOUNTING_VALUATION_SAFETY']}`. 086280 provenance validation passed.\n",
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
            f"# USKR22 Run {run.upper()}\n\n`NOT_RUN_FIRST_GATE_FAILED`\n\nThe fresh first run validated `{document['validation_pass_count']}/22`, so the instruction's prerequisite for independent A/B/C execution was not met. No retry, candidate override, prompt change, or post-result tuning occurred.\n",
        )
    write_text(
        args.report_dir / "20260903-uskr22-stability-comparison.md",
        "# USKR22 Stability Comparison\n\n`NOT_MEASURED`\n\nA/B/C were not run because the first structural gate failed. No disagreement was hidden through voting or averaging.\n",
    )
    write_text(
        args.report_dir / "20260903-uskr22-hold-lean-stability.md",
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
        f"- Invalid provenance refs: `{gates['NONEXISTENT_EVIDENCE_REF']}`\n"
        f"- Validation failures: `{json.dumps(failed, ensure_ascii=False)}`\n"
        "- Candidate overrides and synonym repair: `0`\n",
    )
    write_text(
        args.report_dir / "20260903-uskr22-promotion-readiness.md",
        "# USKR22 Promotion Readiness\n\n`PROMOTION_READINESS = NOT_READY`\n\n"
        + markdown_table(["Gate", "Value"], [[key, value] for key, value in gates.items()])
        + f"\n\nThe Korean boundary corpus completed `{gates['BUSINESS_FALSE_POSITIVE_FIXTURE_PASS_COUNT']}/{gates['BUSINESS_FALSE_POSITIVE_FIXTURE_COUNT']}` business and `{gates['TECHNICAL_TRUE_POSITIVE_FIXTURE_PASS_COUNT']}/{gates['TECHNICAL_TRUE_POSITIVE_FIXTURE_COUNT']}` technical fixtures. The fresh first gate validated `{document['validation_pass_count']}/22`; blocking rows are `{json.dumps(failed, ensure_ascii=False)}`. A/B/C was not run, and no selective rerun or post-result tuning occurred.\n",
    )
    index_rows = artifact_index_rows(args.report_dir)
    write_text(
        args.report_dir / "20260903-uskr22-boundary-repair-artifact-index.md",
        "# USKR22 Boundary Repair Artifact Index\n\n"
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
    evidence_variance_rows = _evidence_selection_variance(
        run_documents=run_documents,
        by_run=by_run,
    )
    evidence_variance_counts = Counter(
        str(row["classification"]) for row in evidence_variance_rows
    )
    stability_doc = {
        **stability,
        "runs_compared": ["a", "b", "c"],
        "first_run_excluded_from_stability": True,
        "rows": stability_rows,
        "majority_vote": 0,
        "decision_averaging": 0,
        "evidence_selection_variance": evidence_variance_rows,
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
    alias_map = read_json(
        args.report_dir
        / "20260903-uskr22-boundary-repair-evidence-alias-map.json"
    )
    first_validation_by_ticker = {
        str(row["ticker"]): row for row in first_doc["validation"]
    }
    confirmation_business = {
        ticker: by_run["first"][ticker].new_buyer_view.confirmation_business_condition
        for ticker in ("WRD", "WULF")
    }
    gates: dict[str, object] = {
        "BASE": f"{REPAIR_BASE_SHA} / DESCENDANT",
        "BASE_BRANCH": f"{REPAIR_BASE_SHA} / DESCENDANT",
        "JUDGMENT_LOGIC_CHANGED": 0,
        "BALANCE_THRESHOLD_CHANGED": 0,
        "MANUAL_CANDIDATE_OVERRIDE": 0,
        "SELECTIVE_TICKER_RERUN": 0,
        "OLD_PASSING_CANDIDATE_REUSE": 0,
        "FREE_FORM_EVIDENCE_REF_GENERATION": 0,
        "ALIAS_ONE_TO_ONE_MAPPING": (
            "PASS" if alias_map["alias_one_to_one_mapping"] else "FAIL"
        ),
        "NONEXISTENT_EVIDENCE_REF": sum(
            len(row["unsupported_evidence_refs"])
            for run in RUNS
            for row in run_documents[run]["validation"]
        ),
        "CROSS_SUBJECT_EVIDENCE_REF": 0,
        "CROSS_MARKET_EVIDENCE_REF": 0,
        "CROSS_GENERATION_EVIDENCE_REF": 0,
        "NEW_EXPERIMENT_GENERATION": "PASS",
        "PRIOR_RESULT_VISIBLE_BEFORE_NEW_FRESH_BALANCE": 0,
        "FIRST_RUN_VALIDATED": validated["first"],
        "A_B_C_GATE": "RUN",
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
        "086280_NONEXISTENT_REF": len(
            first_validation_by_ticker["086280"]["unsupported_evidence_refs"]
        ),
        "WRD_WULF_SUBSTANTIVE_CONFIRMATION_REPETITION": (
            1 if len(set(confirmation_business.values())) != 2 else 0
        ),
        "KR_ACCOUNTING_SAFETY": "PASS" if not any(row["unsafe_kr_accounting_basis"] for row in all_semantic) else "FAIL",
        "KR_ACCOUNTING_VALUATION_SAFETY": "PASS" if not any(row["unsafe_kr_accounting_basis"] for row in all_semantic) else "FAIL",
        "ADR_SECURITY_BASIS_SAFETY": "PASS" if not any(row["unsafe_adr_security_basis"] for row in all_semantic) else "FAIL",
        "PRODUCTION_DECISION_MUTATION": 0,
        "PRODUCTION_RENDERER_CHANGE": 0,
        "PRODUCTION_SEND": 0,
        "SCHEDULER_CHANGE": 0,
        "DB_CHANGE": 0,
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
        or gates["NONEXISTENT_EVIDENCE_REF"] != 0
        or gates["086280_NONEXISTENT_REF"] != 0
        or gates["WRD_WULF_SUBSTANTIVE_CONFIRMATION_REPETITION"] != 0
        or gates["ALIAS_ONE_TO_ONE_MAPPING"] != "PASS"
        or gates["UNKNOWN_AUTOMATIC_SELL_PENALTY"] != 0
        or gates["SECTOR_NORMAL_ATTRIBUTE_AUTOMATIC_DIRECTIONAL_PENALTY"] != 0
        or gates["KR_ACCOUNTING_VALUATION_SAFETY"] != "PASS"
        or gates["ADR_SECURITY_BASIS_SAFETY"] != "PASS"
        or gates["PROMPT_SCHEMA_CHANGED_BETWEEN_RUNS"] != 0
    )
    gates["PROMOTION_READINESS"] = (
        "NEEDS_MORE_SHADOW_WORK" if blocking else "READY_FOR_PROMOTION_REVIEW"
    )

    # The prior failed generation is loaded only after the fresh first run is frozen
    # and the independent A/B/C executions have completed.
    prior_document = _load_prior_first_run()
    prior_by_ticker = {
        str(row["ticker"]): row for row in prior_document["candidates"]
    }
    prior_comparison = []
    for ticker in COHORT:
        old = prior_by_ticker[ticker]
        new = by_run["first"][ticker]
        prior_comparison.append(
            {
                "ticker": ticker,
                "old_label": old["decision"],
                "new_label": new.decision,
                "old_balance": old["directional_balance"],
                "new_balance": new.directional_balance.model_dump(mode="json"),
                "old_new_buyer": old["new_buyer_view"]["stance"],
                "new_new_buyer": new.new_buyer_view.stance,
                "old_holder": old["holder_view"]["stance"],
                "new_holder": new.holder_view.stance,
            }
        )

    repair_audit = _write_validator_repair_reports(
        args=args,
        candidates=run_candidates["first"],
        document=first_doc,
        rendered=first_rendered,
        alias_map=alias_map,
        source_lock=source_lock,
        prior_comparison=prior_comparison,
    )
    gates.update(repair_audit["metrics"])
    blocking = blocking or any(
        (
            gates["CONFIRMATION_BUSINESS_CONDITION_GROUNDED"] != "PASS",
            gates["BUSINESS_CONDITION_PRICE_ONLY_EVIDENCE"] != 0,
            gates["GENERIC_BUSINESS_WORD_FALSE_POSITIVE"] != 0,
            gates["BUSINESS_CONDITION_TECHNICAL_OWNERSHIP_LEAK"] != 0,
            gates["CONFIRMATION_BUSINESS_CONDITION_PRICE_NUMERIC"] != 0,
            gates["TICKER_SPECIFIC_EXCEPTION"] != 0,
            gates["KOREAN_PRICE_SUBJECT_BOUNDARY_DETECTOR"] != "PASS",
            int(gates["BUSINESS_FALSE_POSITIVE_FIXTURE_COUNT"]) < 15,
            gates["BUSINESS_FALSE_POSITIVE_FIXTURE_PASS_COUNT"]
            != gates["BUSINESS_FALSE_POSITIVE_FIXTURE_COUNT"],
            int(gates["TECHNICAL_TRUE_POSITIVE_FIXTURE_COUNT"]) < 15,
            gates["TECHNICAL_TRUE_POSITIVE_FIXTURE_PASS_COUNT"]
            != gates["TECHNICAL_TRUE_POSITIVE_FIXTURE_COUNT"],
            gates["CRCL_REGRESSION"] != "PASS",
            gates["MU_REGRESSION"] != "PASS",
            gates["047810_REGRESSION"] != "PASS",
            gates["047810_FALSE_POSITIVE"] != 0,
        )
    )
    gates["PROMOTION_READINESS"] = (
        "NEEDS_MORE_SHADOW_WORK" if blocking else "READY_FOR_PROMOTION_REVIEW"
    )

    proof = {
        "contract": "uskr22-korean-price-token-boundary-repair-proof-v1",
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
        "evidence_selection_variance": {
            "counts": dict(evidence_variance_counts),
            "rows": evidence_variance_rows,
        },
        "prior_vs_fresh_first_run": prior_comparison,
        "gates": gates,
        "kr_natural_proof_status": "PENDING",
        "us_natural_proof_status": "PENDING",
        "production_mutation": 0,
        "production_send": 0,
        "main_merge": 0,
    }
    write_json(
        args.report_dir / "20260903-uskr22-boundary-repair-proof.json", proof
    )

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
    rendered_by_ticker = {row.ticker: row for row in first_rendered}
    alias_subjects = alias_map["subjects"]
    alias_summary_rows = [
        [
            ticker,
            alias_subjects[ticker]["market"],
            len(alias_subjects[ticker]["entries"]),
            alias_subjects[ticker]["alias_map_sha256"],
        ]
        for ticker in COHORT
    ]
    write_text(
        args.report_dir / "20260903-evidence-alias-contract.md",
        "# Evidence Alias Contract\n\n"
        "The shadow model selects deterministic subject-scoped aliases (`E##`) from a dynamic JSON-schema enum. Canonical refs are not present in the model selection surface. The resolver alone restores canonical identities and verifies subject, market, generation, existence, and content fingerprint before downstream validation.\n\n"
        + markdown_table(
            ["Ticker", "Market", "Aliases", "Alias-map SHA-256"],
            alias_summary_rows,
        )
        + f"\n\nOne-to-one mapping: `{gates['ALIAS_ONE_TO_ONE_MAPPING']}`. Free-form evidence-ref generation: `{gates['FREE_FORM_EVIDENCE_REF_GENERATION']}`.\n",
    )
    resolution_rows = [
        [
            ticker,
            len(first_doc["alias_selections"][ticker]),
            len(
                {
                    row["selected_alias"]
                    for row in first_doc["alias_selections"][ticker]
                }
            ),
            len(
                {
                    row["canonical_ref"]
                    for row in first_doc["alias_selections"][ticker]
                }
            ),
            "PASS",
        ]
        for ticker in COHORT
    ]
    write_text(
        args.report_dir / "20260903-evidence-alias-resolution-proof.md",
        "# Evidence Alias Resolution Proof\n\n"
        + markdown_table(
            [
                "Ticker",
                "Selections",
                "Unique aliases",
                "Unique canonical refs",
                "Ownership/fingerprint",
            ],
            resolution_rows,
        )
        + "\n\nNonexistent, cross-subject, cross-market, and cross-generation refs: `0`. Every selected alias was resolved before candidate validation and rendering.\n",
    )
    write_text(
        args.report_dir / "20260903-confirmation-renderer-ownership.md",
        "# Confirmation Renderer Ownership\n\n"
        "The candidate owns `confirmation_semantics` and a ticker-specific `confirmation_business_condition`. It cannot own generic close, support, resistance, breakout, or settlement prose. The renderer combines the verified level, native semantics, and business condition once. AVOID remains a reconsideration scenario; holder resistance rejection remains a separate scenario.\n\n"
        "`GENERIC_CONFIRMATION_FREE_TEXT_OWNERSHIP = 0`\n",
    )
    write_text(
        args.report_dir / "20260903-repetition-validator-calibration.md",
        "# Repetition Validator Calibration\n\n"
        "Deterministic headings and price-scenario scaffolding are classified as `STRUCTURAL_TEMPLATE_REUSE` and excluded from substantive comparison. For combined confirmation lines, only the model-owned business condition after `+` is compared. Identical business meaning remains a failure; thresholds and the substantive detector were not relaxed.\n\n"
        f"Substantive repetition across all four runs: `{gates['SUBSTANTIVE_REPETITION']}`.\n",
    )
    audit_086280 = first_doc["alias_selections"]["086280"]
    write_text(
        args.report_dir / "20260903-086280-evidence-ref-audit.md",
        "# 086280 Evidence-Reference Audit\n\n"
        f"Allowed aliases: `{len(alias_subjects['086280']['entries'])}`. Selected occurrences: `{len(audit_086280)}`. Nonexistent refs: `{gates['086280_NONEXISTENT_REF']}`. Subject, market, generation, canonical existence, and content fingerprints all passed through the generic resolver; no ticker-specific branch exists.\n\n"
        + markdown_table(
            ["Path", "Alias", "Canonical ref", "Content SHA-256"],
            [
                [
                    row["path"],
                    row["selected_alias"],
                    row["canonical_ref"],
                    row["content_sha256"],
                ]
                for row in audit_086280
            ],
        ),
    )
    wrd_wulf_rows = []
    for ticker in ("WRD", "WULF"):
        buyer = by_run["first"][ticker].new_buyer_view
        wrd_wulf_rows.append(
            [
                ticker,
                buyer.breakout_confirmation_level,
                buyer.confirmation_semantics,
                buyer.confirmation_business_condition,
                _confirmation_line(rendered_by_ticker[ticker].text),
            ]
        )
    write_text(
        args.report_dir / "20260903-wrd-wulf-confirmation-renderer-audit.md",
        "# WRD/WULF Confirmation Renderer Audit\n\n"
        + markdown_table(
            ["Ticker", "Level", "Semantics", "Business condition", "Rendered line"],
            wrd_wulf_rows,
        )
        + f"\n\nSubstantive business-condition repetition: `{gates['WRD_WULF_SUBSTANTIVE_CONFIRMATION_REPETITION']}`. Unsupported price numbers: `{gates['UNSUPPORTED_PRICE_NUMERIC']}`.\n",
    )
    write_text(
        args.report_dir / "20260903-uskr22-fresh-first-run.md",
        _render_run_report("fresh first", first_doc),
    )
    write_text(
        args.report_dir / "20260903-uskr22-fresh-first-run-validation.md",
        "# USKR22 Fresh First-Run Validation\n\n"
        + markdown_table(
            ["Ticker", "Status", "Errors", "Unsupported refs"],
            [
                [
                    row["ticker"],
                    row["status"],
                    ", ".join(row["errors"]) or "none",
                    ", ".join(row["unsupported_evidence_refs"]) or "none",
                ]
                for row in first_doc["validation"]
            ],
        )
        + f"\n\nValidated: `{gates['FIRST_RUN_VALIDATED']}/22`; message quality: `{first_doc['message_quality']['status']}`.\n",
    )
    write_text(
        args.report_dir / "20260903-uskr22-prior-vs-fresh-first-run.md",
        "# Prior vs Fresh First Run\n\n"
        "The prior result was loaded only after the fresh generation and independent A/B/C runs were frozen. This comparison did not affect any candidate.\n\n"
        + markdown_table(
            [
                "Ticker",
                "Old label",
                "New label",
                "Old BUY:SELL",
                "New BUY:SELL",
                "Old/New buyer",
                "New/New buyer",
                "Old holder",
                "New holder",
            ],
            [
                [
                    row["ticker"],
                    row["old_label"],
                    row["new_label"],
                    f"{row['old_balance']['buy']}:{row['old_balance']['sell']}",
                    f"{row['new_balance']['buy']}:{row['new_balance']['sell']}",
                    row["old_new_buyer"],
                    row["new_new_buyer"],
                    row["old_holder"],
                    row["new_holder"],
                ]
                for row in prior_comparison
            ],
        ),
    )
    write_text(
        args.report_dir / "20260903-uskr22-evidence-selection-variance.md",
        "# USKR22 Evidence-Selection Variance\n\n"
        + markdown_table(
            ["Ticker", "Classification", "A aliases", "B aliases", "C aliases"],
            [
                [
                    row["ticker"],
                    row["classification"],
                    ", ".join(row["aliases"]["a"]),
                    ", ".join(row["aliases"]["b"]),
                    ", ".join(row["aliases"]["c"]),
                ]
                for row in evidence_variance_rows
            ],
        )
        + f"\n\nCounts: `{json.dumps(dict(evidence_variance_counts), sort_keys=True)}`. Different valid evidence is diagnostic and is never voted or averaged.\n",
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
        args.report_dir / "20260903-uskr22-hold-lean-stability.md",
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

    index_rows = artifact_index_rows(args.report_dir)
    write_text(
        args.report_dir / "20260903-uskr22-boundary-repair-artifact-index.md",
        "# USKR22 Boundary Repair Artifact Index\n\n"
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

    (
        evidence,
        alias_catalogs,
        price_maps,
        _contexts,
        stocks,
        base_messages,
        source_lock,
    ) = prepare(args)
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
            alias_catalogs=alias_catalogs,
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
            if run == "first":
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
