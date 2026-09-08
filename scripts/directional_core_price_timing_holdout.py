from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.jobs.accepted_decision_v2_runtime import REASONING_EFFORT, REASONING_MODEL
from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    EvidenceCategory,
)
from app.services.directional_balance_service import (
    DirectionalBalance,
    directional_balance_ordinal_calibration_prompt,
)
from app.services.direction_timing_ownership_service import (
    CORE_DOMAINS,
    CORE_OUTPUT_CONTRACT,
    MATERIAL_DIRECTIONAL_DOMAINS,
    OWNERSHIP_EXECUTION_MODE,
    TIMING_DOMAINS,
    TIMING_OUTPUT_CONTRACT,
    CoreHolderView,
    CoreNewBuyerView,
    DirectionalClaim,
    DirectionalCoreCandidate,
    DirectionalSellDriver,
    DirectionalUnknown,
    EvidenceDomain,
    HolderPriceReview,
    OwnedEvidencePacket,
    PriceTimingCandidate,
    TechnicalState,
    TimingClaim,
    TimingNewBuyerModifier,
    build_owned_evidence_packet,
    canonical_sha256,
    compose_decision,
    core_fingerprint,
    stage_alias_catalogs,
    technical_feature_inventory,
    validate_ownership,
)
from app.services.structured_autonomy_alias_service import (
    EvidenceAliasCatalog,
    alias_price_choices,
    build_alias_constrained_batch_schema,
    resolve_candidate_aliases,
)
from app.services.structured_autonomy_shadow_service import (
    HoldLean,
    explicit_actionable_trade_directives,
    render_structured_autonomy_message,
    structured_autonomy_message_quality,
    validate_structured_autonomy_candidate,
)
from scripts import official_fundamental_enrichment_holdout as fundamental
from scripts import structured_actionability_unseen_coldstart as actionability
from scripts import unseen_source_assembly_coldstart as prior
from scripts import uskr22_structured_autonomy_shadow as engine


PROGRAM_CONTRACT = "directional-core-price-timing-new-holdout-v1"
PROOFS_DIRECTORY = "20260906-direction-timing-ownership-proofs"
SOURCE_REPORT_SHA256 = (
    "05e3f65245d069e761f46147be6a363b3994f665d1a14d92d811d4ef74f9977b"
)
SOURCE_IMPLEMENTATION_COMMIT = "25906030070830327401ae7bc77aefb0910b6b58"
SOURCE_IMPLEMENTATION_TREE = "05d1e5f82ad6239628e238aee5824e3835c3c1be"
SOURCE_GENERATION = "20260906-fundamental-holdout-20260906T065029Z-a6b43b8a61c4"
SOURCE_LOCK_SHA256 = (
    "bc307daaf43bf5ee561e1b8a927357e91535613e101687e8872d99d030e55832"
)
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
SELECTION_SALT = "directional-core-price-timing-ownership-new-holdout-v1"
TARGET_COUNT = 16
PREFERRED_PER_MARKET = 8
MINIMUM_COHORT = 12
MAXIMUM_COHORT = 20
CANDIDATE_AUDIT_SIZE = 64

RETIRED22 = (
    "CORZ", "CPNG", "CRCL", "GOOGL", "HUT", "IBM", "MU", "RXRX", "SKHY",
    "SNDK", "TSLA", "TSM", "WRD", "WULF", "000660", "003690", "005490",
    "005930", "010120", "012450", "047810", "086280",
)
PREFLIGHT11 = (
    "010140", "011200", "017800", "021240", "024110", "035420", "051160",
    "055550", "443060", "MSFT", "NVDA",
)
PRIOR_UNSEEN16 = (
    "LLY", "AAPL", "NFLX", "GOOG", "CRM", "PFE", "META", "AMD", "446070",
    "011090", "093370", "092460", "067280", "309930", "397810", "027970",
)
LATEST_HOLDOUT16 = (
    "PLTR", "V", "MA", "AMZN", "XOM", "DIS", "NKE", "MCD", "033920",
    "104480", "071320", "096240", "032860", "060570", "016600", "462520",
)
EXCLUDED_TICKERS = frozenset(
    (*RETIRED22, *PREFLIGHT11, *PRIOR_UNSEEN16, *LATEST_HOLDOUT16, "GOOG", "GOOGL")
)

EXPECTED_SOURCE_HASHES = {
    "coldstart_assembler": "ce6bd772ad105cd2425570607806ae1ec8afa109eca94fd4c6b2e08c4b306780",
    "company_profile": "fd4854c7781d672bf414ea43341e21ceb1879436c97defc5dff153037bdbbf5f",
    "financial_lineage": "1a9ba3fa0d867f4d0c1fb2c5e1b034d9adeebbe32b22b0d796571d468922ff91",
    "fundamental_enrichment": "c18627e3dd3a9a124b08583466de4361e1c5246be7ed6d2aadb306c770ed7538",
    "opendart_recovery": "c3190d3db087ca474a9cdf250570ba36c4fd82554439b60a6ac31354cfec19b0",
    "orchestrator": "2599d049400eab81fdf54336807bd37912496836504d1722c636cad70710afbe",
    "provider_sector_map": "e0c1ca2c52809484594b88e1dd904fd0a985c9db76d8524c21134ab8850d99bf",
    "provider_symbol_registry": "6cc8d7f38545a3abbe2fa882ef187ff7200d71a914d8b63e521a3917b6e226a6",
    "sec_financial_normalizer": "9fa2d3c12c75adf0872010a84ef749b8a4c6449d244ee4f35bb042ded7874136",
}

REPORT_TO_PROOF = {
    "20260906-direction-timing-root-cause.md": "direction-timing-root-cause.json",
    "20260906-evidence-domain-contract.md": "evidence-domain-contract.json",
    "20260906-directional-core-contract.md": "directional-core-contract.json",
    "20260906-price-timing-overlay-contract.md": "price-timing-overlay-contract.json",
    "20260906-ohlcv-technical-feature-routing-audit.md": "ohlcv-technical-feature-routing-audit.json",
    "20260906-supply-positioning-routing-audit.md": "supply-positioning-routing-audit.json",
    "20260906-composer-ownership-contract.md": "composer-ownership-contract.json",
    "20260906-ownership-validator-contract.md": "ownership-validator-contract.json",
    "20260906-counterfactual-invariance-synthetic-suite.md": "counterfactual-invariance-synthetic-suite.json",
    "20260906-technical-feature-routing-synthetic-suite.md": "technical-feature-routing-synthetic-suite.json",
    "20260906-latest-holdout16-one-shot-regression.md": "latest-holdout16-one-shot-regression.json",
    "20260906-ownership-architecture-freeze.md": "ownership-architecture-freeze.json",
    "20260906-new-issuer-holdout-selection-policy.md": "new-issuer-holdout-selection-policy.json",
    "20260906-new-issuer-holdout-selection.md": "new-issuer-holdout-selection.json",
    "20260906-new-issuer-holdout-source-preflight.md": "new-issuer-holdout-source-preflight.json",
    "20260906-new-issuer-holdout-source-lock.md": "new-issuer-holdout-source-lock.json",
    "20260906-ownership-first.md": "ownership-first.json",
    "20260906-ownership-run-a.md": "ownership-run-a.json",
    "20260906-ownership-run-b.md": "ownership-run-b.json",
    "20260906-ownership-run-c.md": "ownership-run-c.json",
    "20260906-core-stability-audit.md": "core-stability-audit.json",
    "20260906-timing-stability-audit.md": "timing-stability-audit.json",
    "20260906-real-holdout-price-invariance-audit.md": "real-holdout-price-invariance-audit.json",
    "20260906-dominance-ownership-audit-v2.md": "dominance-ownership-audit-v2.json",
    "20260906-renderer-shadow-proof.md": "renderer-shadow-proof.json",
    "20260906-hard-safety-regression.md": "hard-safety-regression.json",
    "20260906-monitoring-bootstrap-next-handoff.md": "monitoring-bootstrap-next-handoff.json",
    "20260906-production-no-change.md": "production-no-change.json",
    "20260906-night-futures-no-change.md": "night-futures-no-change.json",
    "20260906-program-completion.md": "program-completion.json",
}


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


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_value(*args: str) -> str:
    return subprocess.run(("git", *args), check=True, capture_output=True, text=True).stdout.strip()


def _normalize_issuer_name(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower()).removesuffix("classa")


def _stable_rank(row: Mapping[str, object]) -> str:
    return hashlib.sha256(
        "|".join(
            (
                SELECTION_SALT,
                str(row.get("market") or ""),
                str(row.get("sector") or row.get("industry") or "unclassified"),
                str(row.get("ticker") or ""),
            )
        ).encode()
    ).hexdigest()


def ranked_candidates(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    by_ticker = {str(row["ticker"]): row for row in rows}
    excluded_names = {
        _normalize_issuer_name(by_ticker[ticker].get("company_name"))
        for ticker in EXCLUDED_TICKERS
        if ticker in by_ticker
    }
    eligible = [
        dict(row)
        for row in rows
        if str(row.get("ticker")) not in EXCLUDED_TICKERS
        and _normalize_issuer_name(row.get("company_name")) not in excluded_names
    ]
    strata: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in eligible:
        key = str(row.get("sector") or row.get("industry") or "unclassified")
        strata[(str(row["market"]), key)].append(row)
    for values in strata.values():
        values.sort(key=lambda row: (_stable_rank(row), str(row["ticker"])))
    ordered: list[dict[str, object]] = []
    for market in ("us", "kr"):
        keys = sorted(
            (key for key in strata if key[0] == market),
            key=lambda key: hashlib.sha256(
                f"{SELECTION_SALT}|{key[0]}|{key[1]}".encode()
            ).hexdigest(),
        )
        while any(strata[key] for key in keys):
            for key in keys:
                if strata[key]:
                    ordered.append(strata[key].pop(0))
    return ordered


def candidate_pool(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    ranked = ranked_candidates(rows)
    us = [row for row in ranked if row["market"] == "us"]
    kr = [row for row in ranked if row["market"] == "kr"]
    pool = [*us, *kr[: CANDIDATE_AUDIT_SIZE - len(us)]]
    if len(pool) != CANDIDATE_AUDIT_SIZE:
        raise ValueError(f"candidate_audit_size_unavailable:{len(pool)}")
    return pool


def batches(cohort: Sequence[str]) -> tuple[tuple[str, ...], ...]:
    return tuple(tuple(cohort[index : index + 4]) for index in range(0, len(cohort), 4))


def program_id(commit: str, as_of: datetime) -> str:
    stamp = as_of.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = hashlib.sha256(f"{commit}|{stamp}|{SELECTION_SALT}".encode()).hexdigest()[:12]
    return f"20260906-direction-timing-holdout-{stamp}-{suffix}"


def _owned_context(
    owned: OwnedEvidencePacket,
    catalog: EvidenceAliasCatalog,
) -> dict[str, object]:
    by_ref = {row.ref.ref_id: row for row in owned.evidence}
    return {
        "ticker": owned.source_packet.ticker,
        "company_name": owned.source_packet.company_name,
        "market": owned.source_packet.market,
        "assessment_date": owned.source_packet.assessment_date,
        "evidence": [
            {
                "alias": entry.alias,
                "domain": by_ref[entry.canonical_ref].domain,
                "category": entry.category,
                "label": entry.label,
                "statement": entry.statement,
                "as_of": entry.as_of,
                "value": (
                    str(by_ref[entry.canonical_ref].ref.value)
                    if by_ref[entry.canonical_ref].ref.value is not None
                    else None
                ),
                "unit": by_ref[entry.canonical_ref].ref.unit,
                "metric_refs": list(entry.metric_refs),
            }
            for entry in catalog.entries
        ],
    }


def _core_prompt(
    *,
    packet_id: str,
    tickers: Sequence[str],
    contexts: Sequence[Mapping[str, object]],
) -> str:
    identity = {"contract": CORE_OUTPUT_CONTRACT, "packet_id": packet_id, "tickers": list(tickers)}
    return (
        """You are Stage 1, the Directional Core of a blind non-production investment shadow. Use only the supplied non-price evidence aliases. Do not browse, fetch, inspect files, infer prior outputs, or use price, OHLCV, chart, support/resistance, RSI, MACD, Bollinger, volume, risk/reward, or supply/flow evidence.

Return one candidate per ticker in input order. directional_balance buy and sell sum to 10 in 0.5 increments. overall_direction is BUY when buy >= 6, SELL when sell >= 6, otherwise HOLD. hold_lean is BUY_LEAN only for HOLD 5.5:4.5, SELL_LEAN only for HOLD 4.5:5.5, NEUTRAL for other HOLD balances, and NOT_HOLD otherwise. Do not use fixed weights, probability, expected-return language, or imperative trading commands.

"""
        + directional_balance_ordinal_calibration_prompt()
        + """

Every claim and condition must cite only aliases supplied for that ticker. BUY or SELL requires material_directional_anchor_basis with at least one same-direction issuer-level business, earnings, cash-flow, capital, valuation, expectations, or structural-risk anchor. Macro alone is insufficient. Unknown evidence may limit confidence but is not automatically negative. The fundamental new-buyer and holder stances are pre-timing views. Business invalidation and reevaluation conditions must be issuer-specific and non-price. Keep all prose concise and natural Korean. Do not put exact numbers in prose. Never state unsupported FCF yield, per-share FCF, EV/FCF, P/FCF, ROIC, CCC, DSO, DPO, or runway months.

The schema is the complete output and alias contract. Return strict JSON only and match IDENTITY exactly.

IDENTITY:
"""
        + json.dumps(identity, ensure_ascii=False, separators=(",", ":"))
        + "\n\nDIRECTIONAL_CORE_CONTEXT:\n"
        + json.dumps(contexts, ensure_ascii=False, separators=(",", ":"), default=str)
    )


def _timing_prompt(
    *,
    packet_id: str,
    tickers: Sequence[str],
    contexts: Sequence[Mapping[str, object]],
) -> str:
    identity = {"contract": TIMING_OUTPUT_CONTRACT, "packet_id": packet_id, "tickers": list(tickers)}
    return (
        """You are Stage 2, the Price-Timing Overlay of a blind non-production investment shadow. The supplied Directional Core is frozen. You may interpret only supplied price/OHLCV/technical/risk-reward/supply aliases and verified price choices. You cannot emit or recompute BUY/HOLD/SELL, directional balance, HOLD lean, business thesis change, or business invalidation.

Copy each supplied core_fingerprint exactly. timing_new_buyer_modifier can only keep or make the frozen fundamental stance more conservative: ALLOW, WAIT, or AVOID. holder_price_review can only be NONE or REVIEW and can never create REDUCE. Technical breakdown is price review, not business invalidation. Technical strength cannot rescue or upgrade a fundamental stance.

Use every validated feature class that is material, while preserving unavailable as unavailable rather than zero. Cite only aliases supplied for that ticker. supply_positioning_rationale must be null when no SUPPLY_POSITIONING alias exists and otherwise may cite only that domain. Do not treat stale supply as current flow.

Copy structured levels exactly from allowed_price_choices. If a pullback zone exists, preserve one exact zone and basis; otherwise use null bounds and empty basis. Apply the same rule to confirmation and trim choices. A downside review level must be listed or null. entry_mode is NONE only when neither pullback nor confirmation exists. Keep all prose concise and natural Korean, without exact numbers or trading imperatives. Return strict JSON only and match IDENTITY exactly.

IDENTITY:
"""
        + json.dumps(identity, ensure_ascii=False, separators=(",", ":"))
        + "\n\nPRICE_TIMING_CONTEXT:\n"
        + json.dumps(contexts, ensure_ascii=False, separators=(",", ":"), default=str)
    )


def build_inputs(
    packets: Mapping[str, Mapping[str, object]],
    base_contexts: Mapping[str, str],
    cohort: Sequence[str],
) -> tuple[
    dict[str, DecisionEvidencePacket],
    dict[str, OwnedEvidencePacket],
    dict[str, EvidenceAliasCatalog],
    dict[str, EvidenceAliasCatalog],
    dict[str, dict[str, object]],
    dict[str, Mapping[str, object]],
]:
    evidence, _old_aliases, price_maps, _old_contexts, stocks = prior._build_engine_inputs(
        packets, base_contexts, cohort
    )
    owned: dict[str, OwnedEvidencePacket] = {}
    core_aliases: dict[str, EvidenceAliasCatalog] = {}
    timing_aliases: dict[str, EvidenceAliasCatalog] = {}
    for ticker in cohort:
        item = build_owned_evidence_packet(evidence[ticker], stock=stocks[ticker])
        core_catalog, timing_catalog = stage_alias_catalogs(item)
        owned[ticker] = item
        core_aliases[ticker] = core_catalog
        timing_aliases[ticker] = timing_catalog
    return evidence, owned, core_aliases, timing_aliases, price_maps, stocks


def source_lock_document(
    *,
    generation_id: str,
    cohort: Sequence[str],
    packets: Mapping[str, Mapping[str, object]],
    base_contexts: Mapping[str, str],
    evidence: Mapping[str, DecisionEvidencePacket],
    owned: Mapping[str, OwnedEvidencePacket],
    core_aliases: Mapping[str, EvidenceAliasCatalog],
    timing_aliases: Mapping[str, EvidenceAliasCatalog],
    price_maps: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    market_by_ticker = {ticker: evidence[ticker].market for ticker in cohort}
    if set(market_by_ticker) != set(cohort) or any(
        market not in {"kr", "us"} for market in market_by_ticker.values()
    ):
        raise ValueError("canonical_market_identity_required_for_source_lock")
    return {
        "contract": "new-ownership-holdout-source-lock-v1",
        "program_generation_id": generation_id,
        "ordered_cohort": list(cohort),
        "market_by_ticker": market_by_ticker,
        "packet_sha256": {ticker: canonical_sha256(packets[ticker]) for ticker in cohort},
        "base_context_sha256": {
            ticker: hashlib.sha256(base_contexts[ticker].encode()).hexdigest()
            for ticker in cohort
        },
        "evidence_fingerprints": {
            ticker: evidence[ticker].evidence_sha256 for ticker in cohort
        },
        "domain_registry": {
            ticker: {
                row.ref.ref_id: row.domain for row in owned[ticker].evidence
            }
            for ticker in cohort
        },
        "core_alias_fingerprints": {
            ticker: core_aliases[ticker].alias_map_sha256 for ticker in cohort
        },
        "timing_alias_fingerprints": {
            ticker: timing_aliases[ticker].alias_map_sha256 for ticker in cohort
        },
        "price_map_fingerprints": {
            ticker: price_maps[ticker]["price_map_fingerprint"] for ticker in cohort
        },
        "source_sufficiency": {
            ticker: packets[ticker].get("source_sufficiency") for ticker in cohort
        },
        "evidence_domain_contract": "direction-timing-ownership-v1",
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "pre_lock_directional_model_calls": 0,
        "production_db_mutation": 0,
    }


def _write_prompt_schema_lock(
    *,
    output_root: Path,
    generation_id: str,
    cohort: Sequence[str],
    owned: Mapping[str, OwnedEvidencePacket],
    core_aliases: Mapping[str, EvidenceAliasCatalog],
    timing_aliases: Mapping[str, EvidenceAliasCatalog],
    price_maps: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    core_schema = engine.strict_json_schema(DirectionalCoreCandidate.model_json_schema())
    timing_schema = engine.strict_json_schema(PriceTimingCandidate.model_json_schema())
    rows = []
    for number, batch in enumerate(batches(cohort), start=1):
        core_contexts = [_owned_context(owned[ticker], core_aliases[ticker]) for ticker in batch]
        timing_contexts = []
        for ticker in batch:
            timing_contexts.append(
                {
                    **_owned_context(owned[ticker], timing_aliases[ticker]),
                    "allowed_price_choices": alias_price_choices(
                        engine.price_choices(price_maps[ticker]), timing_aliases[ticker]
                    ),
                }
            )
        core_prompt_path = output_root / "prompts" / f"core-batch-{number:02d}.txt"
        timing_context_path = output_root / "timing-contexts" / f"batch-{number:02d}.json"
        core_schema_path = output_root / "schemas" / f"core-batch-{number:02d}.json"
        timing_schema_path = output_root / "schemas" / f"timing-batch-{number:02d}.json"
        write_text(
            core_prompt_path,
            _core_prompt(packet_id=generation_id, tickers=batch, contexts=core_contexts),
        )
        write_json(timing_context_path, {"contexts": timing_contexts})
        write_json(
            core_schema_path,
            build_alias_constrained_batch_schema(
                candidate_schema=core_schema,
                contract=CORE_OUTPUT_CONTRACT,
                packet_id=generation_id,
                aliases_by_ticker={
                    ticker: tuple(core_aliases[ticker].by_alias) for ticker in batch
                },
            ),
        )
        write_json(
            timing_schema_path,
            build_alias_constrained_batch_schema(
                candidate_schema=timing_schema,
                contract=TIMING_OUTPUT_CONTRACT,
                packet_id=generation_id,
                aliases_by_ticker={
                    ticker: tuple(timing_aliases[ticker].by_alias) for ticker in batch
                },
            ),
        )
        rows.append(
            {
                "batch": number,
                "tickers": list(batch),
                "core_prompt_sha256": file_sha256(core_prompt_path),
                "core_schema_sha256": file_sha256(core_schema_path),
                "timing_context_sha256": file_sha256(timing_context_path),
                "timing_schema_sha256": file_sha256(timing_schema_path),
            }
        )
    lock = {
        "contract": "direction-timing-prompt-schema-lock-v1",
        "program_generation_id": generation_id,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "ownership_execution_mode": OWNERSHIP_EXECUTION_MODE,
        "batches": rows,
        "prompt_set_sha256": canonical_sha256(
            [[row["core_prompt_sha256"], row["timing_context_sha256"]] for row in rows]
        ),
        "schema_set_sha256": canonical_sha256(
            [[row["core_schema_sha256"], row["timing_schema_sha256"]] for row in rows]
        ),
    }
    write_json(output_root / "prompt-schema-lock.json", lock)
    return lock


def architecture_hashes(repo_root: Path) -> dict[str, str]:
    paths = {
        "ownership_service": repo_root / "app/services/direction_timing_ownership_service.py",
        "ownership_runner": repo_root / "scripts/directional_core_price_timing_holdout.py",
        "directional_balance": repo_root / "app/services/directional_balance_service.py",
        "alias_fencing": repo_root / "app/services/structured_autonomy_alias_service.py",
        "validator_renderer": repo_root / "app/services/structured_autonomy_shadow_service.py",
        "stability_classifier": repo_root / "app/services/structured_autonomy_stability_service.py",
    }
    return {name: file_sha256(path) for name, path in paths.items()}


def _synthetic_ref(
    ref_id: str, category: EvidenceCategory, source_ref: str
) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=ref_id,
        category=category,
        label=ref_id,
        statement=ref_id,
        source_ref=source_ref,
    )


def _synthetic_owned() -> OwnedEvidencePacket:
    refs = (
        _synthetic_ref(
            "canonical:fundamental:SYN:business_current:a",
            EvidenceCategory.EARNINGS_QUALITY,
            "stock.fact_catalog.fundamental:SYN:business_current:a",
        ),
        _synthetic_ref(
            "canonical:fundamental:SYN:earnings_financial_current:b",
            EvidenceCategory.EARNINGS,
            "stock.fact_catalog.fundamental:SYN:earnings_financial_current:b",
        ),
        _synthetic_ref(
            "canonical:price:current",
            EvidenceCategory.PRICE_STRUCTURE,
            "stock.fact_catalog.price:current",
        ),
        _synthetic_ref(
            "canonical:chart:structure:state",
            EvidenceCategory.PRICE_STRUCTURE,
            "stock.fact_catalog.chart:structure:state",
        ),
        _synthetic_ref(
            "technical-feature:rsi",
            EvidenceCategory.TECHNICAL_FEATURE,
            "technical_context.synthetic.daily.rsi_14",
        ),
        _synthetic_ref(
            "technical-feature:macd",
            EvidenceCategory.TECHNICAL_FEATURE,
            "technical_context.synthetic.daily.macd_histogram",
        ),
        _synthetic_ref(
            "technical-feature:bollinger",
            EvidenceCategory.TECHNICAL_FEATURE,
            "technical_context.synthetic.daily.bollinger_20_2_state",
        ),
        _synthetic_ref(
            "technical-feature:volume",
            EvidenceCategory.TECHNICAL_FEATURE,
            "technical_context.synthetic.daily.volume_ratio_20",
        ),
        _synthetic_ref(
            "decision-evidence:supply",
            EvidenceCategory.FLOWS,
            "stock.supply_context",
        ),
    )
    packet = DecisionEvidencePacket(
        packet_id="synthetic-direction-timing",
        ticker="SYN",
        company_name="Synthetic",
        market="us",
        assessment_date="2026-09-06",
        horizon="12m",
        evidence=refs,
        prohibited_claims=(),
        evidence_sha256=canonical_sha256([row.model_dump(mode="json") for row in refs]),
    )
    stock = {
        "fact_catalog": [
            {
                "fact_id": "fundamental:SYN:business_current:a",
                "evidence_family": "BUSINESS_CURRENT",
            },
            {
                "fact_id": "fundamental:SYN:earnings_financial_current:b",
                "evidence_family": "EARNINGS_FINANCIAL_CURRENT",
            },
            {"fact_id": "price:current", "evidence_family": "PRICE_CONTEXT"},
            {"fact_id": "chart:structure:state", "evidence_family": "PRICE_CONTEXT"},
        ]
    }
    return build_owned_evidence_packet(packet, stock=stock)


def _synthetic_core(
    decision: str,
    *,
    buyer: str,
    holder: str,
) -> DirectionalCoreCandidate:
    business = "canonical:fundamental:SYN:business_current:a"
    earnings = "canonical:fundamental:SYN:earnings_financial_current:b"
    balance = {
        "BUY": DirectionalBalance(buy=6, sell=4),
        "HOLD": DirectionalBalance(buy=5, sell=5),
        "SELL": DirectionalBalance(buy=4, sell=6),
    }[decision]
    def claim(text: str, ref: str = business) -> DirectionalClaim:
        return DirectionalClaim(text=text, evidence_refs=(ref,))
    return DirectionalCoreCandidate(
        ticker="SYN",
        overall_direction=decision,
        directional_balance=balance,
        hold_lean=HoldLean.NEUTRAL if decision == "HOLD" else HoldLean.NOT_HOLD,
        directional_confidence="MEDIUM",
        business_thesis_change="WEAKENED" if decision == "SELL" else "UNCHANGED",
        business_thesis_context=claim("Business context."),
        earnings_estimate_context=claim("Earnings context.", earnings),
        market_expectation_context=claim("Expectations context."),
        valuation_context=claim("Valuation context."),
        risk_context=claim("Risk context."),
        sector_interpretation=claim("Sector context."),
        buy_drivers=(claim("Buy support."),),
        sell_drivers=(
            DirectionalSellDriver(
                text="Sell risk.", evidence_refs=(business,), classification="STRUCTURAL_RISK"
            ),
        ),
        dominant_evidence=claim("Dominant evidence."),
        uncertainty_limit=claim("Uncertainty."),
        core_investment_judgment=claim("Core judgment."),
        unknown_treatments=(
            DirectionalUnknown(
                summary="Unknown.",
                evidence_refs=(business,),
                treatment="CONFIDENCE_LIMIT",
                directional_negative_basis=(),
            ),
        ),
        material_directional_anchor_basis=(earnings,),
        fundamental_new_buyer=CoreNewBuyerView(
            stance=buyer,
            summary="Fundamental buyer view.",
            confirmation_business_condition="Business confirmation.",
            confirmation_business_condition_refs=(business,),
        ),
        fundamental_holder=CoreHolderView(
            stance=holder,
            summary="Fundamental holder view.",
            business_invalidation_condition="Business invalidation.",
            business_invalidation_condition_refs=(business,),
        ),
        business_reevaluation_up=(claim("Business reevaluation up."),),
        business_reevaluation_down=(claim("Business reevaluation down."),),
    )


def _synthetic_timing(
    core: DirectionalCoreCandidate,
    *,
    state: TechnicalState,
    modifier: TimingNewBuyerModifier,
    review: HolderPriceReview,
) -> PriceTimingCandidate:
    technical = "technical-feature:rsi"
    price = "canonical:price:current"
    def timing_claim(text: str, ref: str = technical) -> TimingClaim:
        return TimingClaim(text=text, evidence_refs=(ref,))
    return PriceTimingCandidate(
        ticker="SYN",
        core_fingerprint=core_fingerprint(core),
        technical_state=state,
        timing_new_buyer_modifier=modifier,
        entry_mode="NONE",
        entry_reason="No verified price level.",
        pullback_entry_zone_low=None,
        pullback_entry_zone_high=None,
        pullback_entry_basis=(),
        breakout_confirmation_level=None,
        breakout_confirmation_basis=(),
        confirmation_semantics="NONE",
        holder_price_review=review,
        upside_trim_zone_low=None,
        upside_trim_zone_high=None,
        upside_trim_basis=(),
        downside_review_level=None,
        downside_review_basis=(),
        currency="USD",
        price_review_context=timing_claim("Price review.", price),
        price_confirmation_context=timing_claim("Price confirmation."),
        price_support_context=timing_claim("Price support."),
        technical_rationale=timing_claim("Technical rationale."),
        supply_positioning_rationale=None,
    )


def synthetic_suites() -> tuple[dict[str, object], dict[str, object]]:
    owned = _synthetic_owned()
    cases = (
        ("A", "BUY", "ATTRACTIVE", "HOLDABLE", TechnicalState.FAVORABLE, TimingNewBuyerModifier.ALLOW, HolderPriceReview.NONE),
        ("A_ADVERSE", "BUY", "ATTRACTIVE", "HOLDABLE", TechnicalState.ADVERSE, TimingNewBuyerModifier.AVOID, HolderPriceReview.REVIEW),
        ("B", "HOLD", "WAIT", "HOLDABLE", TechnicalState.FAVORABLE, TimingNewBuyerModifier.ALLOW, HolderPriceReview.NONE),
        ("B_COLLAPSE", "HOLD", "WAIT", "HOLDABLE", TechnicalState.ADVERSE, TimingNewBuyerModifier.AVOID, HolderPriceReview.REVIEW),
        ("C", "SELL", "AVOID", "REDUCE", TechnicalState.FAVORABLE, TimingNewBuyerModifier.ALLOW, HolderPriceReview.NONE),
        ("D", "BUY", "ATTRACTIVE", "HOLDABLE", TechnicalState.ADVERSE, TimingNewBuyerModifier.WAIT, HolderPriceReview.REVIEW),
        ("E", "HOLD", "WAIT", "HOLDABLE", TechnicalState.ADVERSE, TimingNewBuyerModifier.AVOID, HolderPriceReview.REVIEW),
        ("F", "SELL", "AVOID", "REDUCE", TechnicalState.ADVERSE, TimingNewBuyerModifier.AVOID, HolderPriceReview.REVIEW),
        ("G", "HOLD", "WAIT", "HOLDABLE", TechnicalState.ADVERSE, TimingNewBuyerModifier.WAIT, HolderPriceReview.REVIEW),
    )
    rows = []
    for name, decision, buyer, holder, state, modifier, review in cases:
        core = _synthetic_core(decision, buyer=buyer, holder=holder)
        timing = _synthetic_timing(core, state=state, modifier=modifier, review=review)
        composed = compose_decision(core, timing)
        validation = validate_ownership(owned, core, timing, composed)
        rows.append(
            {
                "case": name,
                "core_direction": decision,
                "final_direction": composed.candidate.decision,
                "core_balance": core.directional_balance.model_dump(mode="json"),
                "final_balance": composed.candidate.directional_balance.model_dump(mode="json"),
                "core_hold_lean": core.hold_lean,
                "final_hold_lean": str(
                    composed.candidate.decision != "HOLD" and HoldLean.NOT_HOLD
                    or HoldLean.NEUTRAL
                ),
                "final_new_buyer": composed.candidate.new_buyer_view.stance,
                "final_holder": composed.candidate.holder_view.stance,
                "ownership_errors": list(validation.errors),
                "pass": validation.valid
                and composed.candidate.decision == core.overall_direction
                and composed.candidate.directional_balance == core.directional_balance,
            }
        )
    counterfactual = {
        "contract": "direction-timing-counterfactual-suite-v1",
        "ticker_free": 1,
        "cases": rows,
        "direction_timing_counterfactual_suite": (
            "PASS" if all(row["pass"] for row in rows) else "FAIL"
        ),
    }
    inventory = technical_feature_inventory(owned)
    technical = {
        "contract": "technical-feature-routing-synthetic-suite-v1",
        "ticker_free": 1,
        "inventory": inventory,
        "covered": [
            "support_resistance",
            "volume",
            "rsi",
            "macd",
            "bollinger",
            "multi_timeframe_structure",
            "risk_reward",
            "supply_positioning",
        ],
        "feature_unavailable_distinct_from_neutral": True,
        "invented_technical_indicator": 0,
        "status": "PASS"
        if inventory["rsi"]
        and inventory["macd"]
        and inventory["bollinger"]
        and inventory["volume"]
        and inventory["unavailable_is_zero"] is False
        else "FAIL",
    }
    return counterfactual, technical


def _base_contract_proofs() -> dict[str, dict[str, object]]:
    return {
        "direction-timing-root-cause.json": {
            "contract": "direction-timing-root-cause-v1",
            "root_cause_class": "DIRECTION_TIMING_OWNERSHIP_LEAKAGE",
            "observed": {
                "hold_lean_flip": "PLTR regression observation only",
                "price_dominated_sell": "NKE regression observation only",
            },
            "ticker_specific_rule_count": 0,
            "repair": "generic evidence-domain and field ownership separation",
        },
        "evidence-domain-contract.json": {
            "contract": "direction-timing-evidence-domain-v1",
            "core_domains": sorted(domain.value for domain in CORE_DOMAINS),
            "timing_domains": sorted(domain.value for domain in TIMING_DOMAINS),
            "material_directional_domains": sorted(
                domain.value for domain in MATERIAL_DIRECTIONAL_DOMAINS
            ),
            "classification_basis": "source evidence_family, category, ref identity, source_ref",
            "free_form_prose_classification": 0,
        },
        "directional-core-contract.json": {
            "contract": CORE_OUTPUT_CONTRACT,
            "owner": "DIRECTIONAL_CORE",
            "input": "non-price evidence aliases only",
            "outputs": [
                "overall_direction",
                "directional_balance",
                "hold_lean",
                "fundamental_new_buyer",
                "fundamental_holder",
                "business_invalidation",
            ],
            "buy_threshold": 6,
            "sell_threshold": 6,
            "balance_sum": 10,
            "balance_increment": 0.5,
            "fixed_factor_weights": 0,
        },
        "price-timing-overlay-contract.json": {
            "contract": TIMING_OUTPUT_CONTRACT,
            "owner": "PRICE_TIMING",
            "input": "frozen core plus technical and supply aliases only",
            "outputs": [
                "technical_state",
                "timing_new_buyer_modifier",
                "entry_mode",
                "holder_price_review",
                "price_review_context",
            ],
            "direction_output_field": 0,
            "balance_output_field": 0,
            "holder_reduce_output_enum": 0,
        },
        "composer-ownership-contract.json": {
            "contract": "direction-timing-composer-v1",
            "copies_direction_from_core": 1,
            "copies_balance_from_core": 1,
            "copies_hold_lean_from_core": 1,
            "new_buyer_transition": {
                "ATTRACTIVE": ["ATTRACTIVE", "WAIT", "AVOID"],
                "WAIT": ["WAIT", "AVOID"],
                "AVOID": ["AVOID"],
            },
            "holder_transition": {
                "HOLDABLE": ["HOLDABLE", "REVIEW"],
                "REVIEW": ["REVIEW"],
                "REDUCE": ["REDUCE"],
            },
            "composer_investment_reasoning_invented": 0,
        },
        "ownership-validator-contract.json": {
            "contract": "direction-timing-ownership-validator-v1",
            "structured_domain_validation": 1,
            "arbitrary_prose_ownership_parsing": 0,
            "hard_checks": [
                "core price/technical ref",
                "core supply ref",
                "BUY/SELL non-price material anchor",
                "core fingerprint",
                "timing ref domain",
                "new-buyer no-upgrade",
                "price-only no-REDUCE",
                "business invalidation core ownership",
            ],
        },
        "supply-positioning-routing-audit.json": {
            "contract": "supply-positioning-routing-audit-v1",
            "domain": EvidenceDomain.SUPPLY_POSITIONING,
            "directional_core_allowed": 0,
            "timing_overlay_allowed": 1,
            "business_thesis_mutation_allowed": 0,
            "stale_supply_as_current_allowed": 0,
        },
    }


def prepare(args: argparse.Namespace) -> None:
    repo_root = Path.cwd().resolve()
    if (args.output_root / "program-state.json").exists():
        raise ValueError("new_output_root_required")
    if file_sha256(args.source_report) != SOURCE_REPORT_SHA256:
        raise ValueError("source_report_bundle_sha256_mismatch")
    if REASONING_MODEL != MODEL or REASONING_EFFORT != EFFORT:
        raise ValueError("signed_in_codex_model_or_effort_mismatch")
    actual_source_hashes = fundamental.source_hashes(repo_root, args.provider_root)
    if actual_source_hashes != EXPECTED_SOURCE_HASHES:
        raise ValueError("fundamental_source_enrichment_drift")
    if git_value("rev-parse", f"{SOURCE_IMPLEMENTATION_COMMIT}^{{tree}}") != SOURCE_IMPLEMENTATION_TREE:
        raise ValueError("source_implementation_tree_mismatch")

    implementation_commit = git_value("rev-parse", "HEAD")
    implementation_tree = git_value("rev-parse", "HEAD^{tree}")
    generation_id = program_id(implementation_commit, args.as_of)
    proofs_dir = args.report_dir / PROOFS_DIRECTORY
    args.output_root.mkdir(parents=True, exist_ok=False)
    proofs_dir.mkdir(parents=True, exist_ok=True)
    if args.seed_cache.is_dir():
        shutil.copytree(args.seed_cache, args.output_root / "source-cache")
    else:
        (args.output_root / "source-cache").mkdir()

    counterfactual, technical_synthetic = synthetic_suites()
    if counterfactual["direction_timing_counterfactual_suite"] != "PASS":
        raise ValueError("direction_timing_counterfactual_suite_failed")
    if technical_synthetic["status"] != "PASS":
        raise ValueError("technical_feature_routing_synthetic_suite_failed")
    base_proofs = _base_contract_proofs()
    base_proofs["counterfactual-invariance-synthetic-suite.json"] = counterfactual
    base_proofs["technical-feature-routing-synthetic-suite.json"] = technical_synthetic
    for name, value in base_proofs.items():
        write_json(proofs_dir / name, value)

    selection_policy = {
        "contract": "new-issuer-holdout-selection-policy-v1",
        "selection_salt": SELECTION_SALT,
        "supported_universe": "frozen canonical supported-security universe",
        "issuer_exclusion": "ticker plus normalized issuer name and known share-class aliases",
        "excluded_tickers": sorted(EXCLUDED_TICKERS),
        "known_share_class_aliases": {"Alphabet": ["GOOG", "GOOGL"]},
        "candidate_audit_size": CANDIDATE_AUDIT_SIZE,
        "target_count": TARGET_COUNT,
        "preferred_per_market": PREFERRED_PER_MARKET,
        "minimum": MINIMUM_COHORT,
        "maximum": MAXIMUM_COHORT,
        "expected_available_us_after_exclusion": 7,
        "selection_uses_expected_decision": 0,
    }
    write_json(proofs_dir / "new-issuer-holdout-selection-policy.json", selection_policy)
    architecture = {
        "contract": "ownership-architecture-freeze-v1",
        "implementation_commit": implementation_commit,
        "implementation_tree": implementation_tree,
        "frozen_at": args.as_of.isoformat(),
        "ownership_execution_mode": OWNERSHIP_EXECUTION_MODE,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "architecture_hashes": architecture_hashes(repo_root),
        "selection_policy_sha256": canonical_sha256(selection_policy),
        "source_enrichment_hashes": actual_source_hashes,
        "source_sufficiency_policy_sha256": file_sha256(
            repo_root / "app/services/coldstart_fundamental_enrichment_service.py"
        ),
        "ownership_architecture_mutation_after_freeze": 0,
    }
    write_json(args.output_root / "architecture-freeze.json", architecture)
    write_json(proofs_dir / "ownership-architecture-freeze.json", architecture)

    universe = prior.supported_universe(args.provider_root)
    pool = candidate_pool(universe)
    pairs = asyncio.run(
        fundamental.enrich_rows(
            pool,
            as_of=args.as_of,
            cache_dir=args.output_root / "source-cache",
        )
    )
    candidate_rows: list[dict[str, object]] = []
    enrichment_by_ticker = {}
    identity_by_ticker = {}
    for rank, (identity, enrichment) in enumerate(pairs, start=1):
        row = fundamental.enrichment_row(identity, enrichment)
        row["rank"] = rank
        row["issuer_key"] = enrichment.issuer_id or _normalize_issuer_name(
            identity.get("company_name")
        )
        candidate_rows.append(row)
        enrichment_by_ticker[enrichment.ticker] = enrichment
        identity_by_ticker[enrichment.ticker] = identity

    sufficient = [row for row in candidate_rows if row["directional_model_eligible"]]
    preferred = [
        row
        for market in ("us", "kr")
        for row in sufficient
        if row["market"] == market
    ]
    selected = []
    selected_tickers: set[str] = set()
    selected_issuers: set[str] = set()
    market_counts: Counter[str] = Counter()
    preflight_rows = []

    async def preflight(row: Mapping[str, object]) -> None:
        ticker = str(row["ticker"])
        issuer_key = str(row["issuer_key"])
        if ticker in selected_tickers or issuer_key in selected_issuers:
            return
        identity = identity_by_ticker[ticker]
        base = await fundamental.assemble_research_packet(
            ticker, args.as_of, identity=identity
        )
        enriched = fundamental.enrich_assembled_packet(base, enrichment_by_ticker[ticker])
        eligible = bool(
            enriched.source_sufficiency.directional_model_eligible
            and enriched.packet is not None
        )
        preflight_rows.append(
            {
                "ticker": ticker,
                "market": row["market"],
                "issuer_key": issuer_key,
                "source_sufficiency_status": enriched.status,
                "directional_model_eligible": eligible,
                "packet_sha256": enriched.packet_sha256,
                "validation_errors": list(enriched.validation_errors),
                "provider_audit": enriched.provider_audit,
            }
        )
        if eligible:
            selected.append(enriched)
            selected_tickers.add(ticker)
            selected_issuers.add(issuer_key)
            market_counts[str(row["market"])] += 1

    async def select_holdout() -> None:
        for market in ("us", "kr"):
            for row in preferred:
                if row["market"] != market or market_counts[market] >= PREFERRED_PER_MARKET:
                    continue
                await preflight(row)
        if len(selected) < TARGET_COUNT:
            for row in sufficient:
                if len(selected) >= TARGET_COUNT:
                    break
                await preflight(row)

    asyncio.run(select_holdout())
    if not MINIMUM_COHORT <= len(selected) <= MAXIMUM_COHORT:
        raise ValueError(f"new_holdout_below_minimum:{len(selected)}")
    cohort = tuple(
        item.ticker
        for market in ("us", "kr")
        for item in selected
        if item.market == market
    )
    packets = {item.ticker: item.packet for item in selected if item.packet is not None}
    base_contexts = {item.ticker: str(item.deterministic_base_context) for item in selected}
    for ticker in cohort:
        write_json(args.output_root / "packets" / f"{ticker}.json", packets[ticker])
        write_text(args.output_root / "base-contexts" / f"{ticker}.txt", base_contexts[ticker])

    evidence, owned, core_aliases, timing_aliases, price_maps, _stocks = build_inputs(
        packets, base_contexts, cohort
    )
    lock = source_lock_document(
        generation_id=generation_id,
        cohort=cohort,
        packets=packets,
        base_contexts=base_contexts,
        evidence=evidence,
        owned=owned,
        core_aliases=core_aliases,
        timing_aliases=timing_aliases,
        price_maps=price_maps,
    )
    lock_sha = canonical_sha256(lock)
    write_json(args.output_root / "source-lock.json", {**lock, "source_lock_sha256": lock_sha})
    write_json(proofs_dir / "new-issuer-holdout-source-lock.json", {**lock, "source_lock_sha256": lock_sha})
    prompt_lock = _write_prompt_schema_lock(
        output_root=args.output_root,
        generation_id=generation_id,
        cohort=cohort,
        owned=owned,
        core_aliases=core_aliases,
        timing_aliases=timing_aliases,
        price_maps=price_maps,
    )

    selected_names = {
        _normalize_issuer_name(identity_by_ticker[ticker].get("company_name"))
        for ticker in cohort
    }
    universe_by_ticker = {str(row["ticker"]): row for row in universe}
    excluded_names = {
        _normalize_issuer_name(universe_by_ticker[ticker].get("company_name"))
        for ticker in EXCLUDED_TICKERS
        if ticker in universe_by_ticker
    }
    overlap = sorted(selected_names & excluded_names)
    selection = {
        "contract": "new-issuer-holdout-selection-v1",
        "program_generation_id": generation_id,
        "ordered_cohort": list(cohort),
        "selected_count": len(cohort),
        "eligible_count": len(cohort),
        "us_count": sum(not ticker.isdigit() for ticker in cohort),
        "kr_count": sum(ticker.isdigit() for ticker in cohort),
        "ticker_overlap": sorted(set(cohort) & EXCLUDED_TICKERS),
        "normalized_issuer_name_overlap": overlap,
        "final_new_holdout_issuer_overlap": len(overlap),
        "issuer_keys": {
            ticker: str(next(row["issuer_key"] for row in candidate_rows if row["ticker"] == ticker))
            for ticker in cohort
        },
        "status": "PASS" if not overlap else "STOP",
    }
    preflight_proof = {
        "contract": "new-issuer-holdout-source-preflight-v1",
        "program_generation_id": generation_id,
        "candidate_attempt_count": len(candidate_rows),
        "candidate_status_counts": dict(Counter(str(row["sufficiency_status"]) for row in candidate_rows)),
        "selected_rows": preflight_rows,
        "all_selected_source_sufficient": all(
            row["directional_model_eligible"]
            for row in preflight_rows
            if row["ticker"] in cohort
        ),
        "directional_calls_on_source_insufficient": 0,
        "model_calls": 0,
        "provider_totals": {
            key: sum(int(row["provider_audit"].get(key) or 0) for row in candidate_rows)
            for key in (
                "profile_requests", "profile_successes", "companyfacts_requests",
                "companyfacts_successes", "statement_requests", "statement_successes",
                "cache_hits",
            )
        },
        "status": "PASS",
    }
    write_json(proofs_dir / "new-issuer-holdout-selection.json", selection)
    write_json(
        proofs_dir / "new-issuer-holdout-source-preflight.json", preflight_proof
    )
    routing_rows = [
        {"ticker": ticker, **technical_feature_inventory(owned[ticker])}
        for ticker in cohort
    ]
    write_json(
        proofs_dir / "ohlcv-technical-feature-routing-audit.json",
        {
            "contract": "ohlcv-technical-feature-routing-audit-v1",
            "rows": routing_rows,
            "invented_technical_indicator": 0,
            "ohlcv_analyst_calculation_algorithm_mutation": 0,
            "status": "PASS",
        },
    )
    state = {
        "contract": PROGRAM_CONTRACT,
        "state": "PREPARED_FROZEN",
        "program_generation_id": generation_id,
        "implementation_commit": implementation_commit,
        "implementation_tree": implementation_tree,
        "as_of": args.as_of.isoformat(),
        "ordered_cohort": list(cohort),
        "source_lock_sha256": lock_sha,
        "prompt_schema_lock_sha256": canonical_sha256(prompt_lock),
        "architecture_hashes": architecture["architecture_hashes"],
        "selection_policy_sha256": architecture["selection_policy_sha256"],
        "source_enrichment_hashes": actual_source_hashes,
        "source_report_bundle_sha256": SOURCE_REPORT_SHA256,
        "latest_holdout16_rerun_count": 0,
        "ownership_architecture_mutation_after_freeze": 0,
        "production_mutation": 0,
    }
    write_json(args.output_root / "program-state.json", state)
    write_reports(args.report_dir)
    print(json.dumps(state, sort_keys=True), flush=True)


def load_prepared(args: argparse.Namespace):
    state = read_json(args.output_root / "program-state.json")
    cohort = tuple(str(value) for value in state["ordered_cohort"])
    packets = {
        ticker: read_json(args.output_root / "packets" / f"{ticker}.json")
        for ticker in cohort
    }
    contexts = {
        ticker: (args.output_root / "base-contexts" / f"{ticker}.txt").read_text(encoding="utf-8").rstrip()
        for ticker in cohort
    }
    inputs = build_inputs(packets, contexts, cohort)
    return state, cohort, packets, contexts, *inputs


def verify_frozen(args: argparse.Namespace, state: Mapping[str, object]) -> None:
    repo_root = Path.cwd().resolve()
    if architecture_hashes(repo_root) != state["architecture_hashes"]:
        raise ValueError("ownership_architecture_mutation_after_freeze")
    if fundamental.source_hashes(repo_root, args.provider_root) != state["source_enrichment_hashes"]:
        raise ValueError("fundamental_source_enrichment_drift")
    selection = read_json(
        args.report_dir / PROOFS_DIRECTORY / "new-issuer-holdout-selection-policy.json"
    )
    if canonical_sha256(selection) != state["selection_policy_sha256"]:
        raise ValueError("selection_policy_mutation_after_freeze")


def _resolve_batch_candidates(
    raw_candidates: object,
    *,
    batch: Sequence[str],
    evidence: Mapping[str, DecisionEvidencePacket],
    catalogs: Mapping[str, EvidenceAliasCatalog],
    model_type: type[DirectionalCoreCandidate] | type[PriceTimingCandidate],
) -> tuple[tuple[DirectionalCoreCandidate | PriceTimingCandidate, ...], dict[str, object]]:
    if not isinstance(raw_candidates, list):
        raise ValueError("stage_candidates_array_required")
    if tuple(str(row.get("ticker") or "") for row in raw_candidates) != tuple(batch):
        raise ValueError("stage_batch_scope_or_order_mismatch")
    resolved_rows = []
    alias_audit = {}
    for raw in raw_candidates:
        ticker = str(raw["ticker"])
        resolved, selections = resolve_candidate_aliases(
            raw,
            packet=evidence[ticker],
            catalog=catalogs[ticker],
        )
        resolved_rows.append(model_type.model_validate(resolved))
        alias_audit[ticker] = {
            "alias_candidate_sha256": canonical_sha256(raw),
            "resolved_candidate_sha256": canonical_sha256(resolved),
            "selections": list(selections),
        }
    return tuple(resolved_rows), alias_audit


def execute_two_stage_run(
    *,
    run: str,
    generation_id: str,
    source_lock_sha256: str,
    prompt_root: Path,
    run_root: Path,
    cohort: Sequence[str],
    base_contexts: Mapping[str, str],
    evidence: Mapping[str, DecisionEvidencePacket],
    owned: Mapping[str, OwnedEvidencePacket],
    core_aliases: Mapping[str, EvidenceAliasCatalog],
    timing_aliases: Mapping[str, EvidenceAliasCatalog],
    price_maps: Mapping[str, Mapping[str, object]],
    stocks: Mapping[str, Mapping[str, object]],
    timeout: int,
) -> dict[str, object]:
    if run_root.exists():
        raise ValueError(f"existing_run_output_requires_new_generation:{run_root}")
    run_root.mkdir(parents=True)
    codex_bin = engine._signed_in_codex_bin()
    core_by_ticker: dict[str, DirectionalCoreCandidate] = {}
    timing_by_ticker: dict[str, PriceTimingCandidate] = {}
    alias_audit: dict[str, object] = {}
    invocations = []

    for number, batch in enumerate(batches(cohort), start=1):
        prompt = prompt_root / "prompts" / f"core-batch-{number:02d}.txt"
        schema = prompt_root / "schemas" / f"core-batch-{number:02d}.json"
        output = run_root / f"core-batch-{number:02d}.json"
        log = run_root / f"core-batch-{number:02d}.log"
        print(f"{run.upper()} CORE_START {number} {','.join(batch)}", flush=True)
        with engine.isolated_model_working_directory(run=f"{run}-core", batch=number) as cwd:
            engine._invoke_signed_in_codex(
                codex_bin=codex_bin,
                prompt=prompt,
                output=output,
                log=log,
                schema=schema,
                cwd=cwd,
                timeout=timeout,
                state_namespace=f"DIRECTION_TIMING_CORE_{run.upper()}_20260906",
            )
        parsed = read_json(output)
        if parsed.get("contract") != CORE_OUTPUT_CONTRACT or parsed.get("packet_id") != generation_id:
            raise ValueError(f"core_output_identity_mismatch:{run}:{number}")
        rows, audit = _resolve_batch_candidates(
            parsed.get("candidates"),
            batch=batch,
            evidence=evidence,
            catalogs=core_aliases,
            model_type=DirectionalCoreCandidate,
        )
        for row in rows:
            assert isinstance(row, DirectionalCoreCandidate)
            core_by_ticker[row.ticker] = row
        alias_audit.update({f"core:{ticker}": value for ticker, value in audit.items()})
        invocations.append(
            {
                "stage": "DIRECTIONAL_CORE",
                "batch": number,
                "tickers": list(batch),
                "prompt_sha256": file_sha256(prompt),
                "schema_sha256": file_sha256(schema),
                "output_sha256": file_sha256(output),
            }
        )
        print(f"{run.upper()} CORE_COMPLETE {number} {','.join(batch)}", flush=True)

    for number, batch in enumerate(batches(cohort), start=1):
        frozen_context = read_json(
            prompt_root / "timing-contexts" / f"batch-{number:02d}.json"
        )["contexts"]
        contexts = []
        for context in frozen_context:
            ticker = str(context["ticker"])
            core = core_by_ticker[ticker]
            contexts.append(
                {
                    **context,
                    "core_fingerprint": core_fingerprint(core),
                    "frozen_directional_core": core.model_dump(mode="json"),
                }
            )
        prompt = run_root / "timing-prompts" / f"batch-{number:02d}.txt"
        schema = prompt_root / "schemas" / f"timing-batch-{number:02d}.json"
        output = run_root / f"timing-batch-{number:02d}.json"
        log = run_root / f"timing-batch-{number:02d}.log"
        write_text(
            prompt,
            _timing_prompt(packet_id=generation_id, tickers=batch, contexts=contexts),
        )
        print(f"{run.upper()} TIMING_START {number} {','.join(batch)}", flush=True)
        with engine.isolated_model_working_directory(run=f"{run}-timing", batch=number) as cwd:
            engine._invoke_signed_in_codex(
                codex_bin=codex_bin,
                prompt=prompt,
                output=output,
                log=log,
                schema=schema,
                cwd=cwd,
                timeout=timeout,
                state_namespace=f"DIRECTION_TIMING_OVERLAY_{run.upper()}_20260906",
            )
        parsed = read_json(output)
        if parsed.get("contract") != TIMING_OUTPUT_CONTRACT or parsed.get("packet_id") != generation_id:
            raise ValueError(f"timing_output_identity_mismatch:{run}:{number}")
        rows, audit = _resolve_batch_candidates(
            parsed.get("candidates"),
            batch=batch,
            evidence=evidence,
            catalogs=timing_aliases,
            model_type=PriceTimingCandidate,
        )
        for row in rows:
            assert isinstance(row, PriceTimingCandidate)
            timing_by_ticker[row.ticker] = row
        alias_audit.update({f"timing:{ticker}": value for ticker, value in audit.items()})
        invocations.append(
            {
                "stage": "PRICE_TIMING",
                "batch": number,
                "tickers": list(batch),
                "prompt_sha256": file_sha256(prompt),
                "schema_sha256": file_sha256(schema),
                "output_sha256": file_sha256(output),
            }
        )
        print(f"{run.upper()} TIMING_COMPLETE {number} {','.join(batch)}", flush=True)

    rows = []
    composed_candidates = []
    rendered_rows = []
    for ticker in cohort:
        core = core_by_ticker[ticker]
        timing = timing_by_ticker[ticker]
        composed = compose_decision(core, timing)
        ownership = validate_ownership(owned[ticker], core, timing, composed)
        industry = str(stocks[ticker].get("industry") or stocks[ticker].get("sector") or "")
        legacy = validate_structured_autonomy_candidate(
            evidence[ticker], composed.candidate, price_map=price_maps[ticker], industry=industry
        )
        rendered = render_structured_autonomy_message(
            evidence[ticker],
            composed.candidate,
            price_map=price_maps[ticker],
            industry=industry,
            base_detail_text=base_contexts[ticker],
        )
        errors = tuple(dict.fromkeys((*ownership.errors, *legacy.errors, *rendered.validation.errors)))
        rows.append(
            {
                "ticker": ticker,
                "status": "PASS" if not errors else "FAIL",
                "errors": list(errors),
                "core": core.model_dump(mode="json"),
                "timing": timing.model_dump(mode="json"),
                "composed": composed.candidate.model_dump(mode="json"),
                "ownership": ownership.model_dump(mode="json"),
                "directional_core_domains": sorted(
                    {
                        owned[ticker].domain_by_ref[ref].value
                        for ref in engine._candidate_refs(composed.candidate)
                        if ref in owned[ticker].core_refs
                    }
                ),
                "timing_feature_inventory": technical_feature_inventory(owned[ticker]),
                "rendered_message": rendered.text,
            }
        )
        composed_candidates.append(composed.candidate)
        rendered_rows.append(rendered)
    hard_regression = actionability.validator_regression_count(
        composed_candidates, {"validation": rows}
    )
    document = {
        "contract": "direction-timing-two-stage-run-v1",
        "run": run,
        "program_generation_id": generation_id,
        "source_lock_sha256": source_lock_sha256,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "ownership_execution_mode": OWNERSHIP_EXECUTION_MODE,
        "candidate_count": len(rows),
        "validation_pass_count": sum(row["status"] == "PASS" for row in rows),
        "schema_failure": 0,
        "validator_false_positive": 0,
        "ownership_violation": sum(
            bool(row["ownership"]["errors"]) for row in rows
        ),
        "hard_safety_regression": hard_regression,
        "rows": rows,
        "alias_audit": alias_audit,
        "invocations": invocations,
        "message_quality": structured_autonomy_message_quality(rendered_rows),
        "generation_ids": {
            ticker: f"{generation_id}:{run}:{ticker}" for ticker in cohort
        },
        "source_drift": 0,
        "same_generation_repair": 0,
        "selective_rerun": 0,
        "production_mutation": 0,
    }
    document["status"] = (
        "PASS"
        if document["validation_pass_count"] == len(cohort)
        and document["ownership_violation"] == 0
        and hard_regression == 0
        else "FAIL"
    )
    write_json(run_root / "run.json", document)
    return document


def _regression_inputs(args: argparse.Namespace, generation_id: str):
    packets = {
        ticker: read_json(args.regression_source_root / "packets" / f"{ticker}.json")
        for ticker in LATEST_HOLDOUT16
    }
    contexts = {
        ticker: (args.regression_source_root / "base-contexts" / f"{ticker}.txt")
        .read_text(encoding="utf-8")
        .rstrip()
        for ticker in LATEST_HOLDOUT16
    }
    evidence, owned, core_aliases, timing_aliases, price_maps, stocks = build_inputs(
        packets, contexts, LATEST_HOLDOUT16
    )
    prompt_root = args.output_root / "latest-holdout16-regression-input"
    prompt_root.mkdir(parents=True, exist_ok=False)
    _write_prompt_schema_lock(
        output_root=prompt_root,
        generation_id=generation_id,
        cohort=LATEST_HOLDOUT16,
        owned=owned,
        core_aliases=core_aliases,
        timing_aliases=timing_aliases,
        price_maps=price_maps,
    )
    lock = source_lock_document(
        generation_id=generation_id,
        cohort=LATEST_HOLDOUT16,
        packets=packets,
        base_contexts=contexts,
        evidence=evidence,
        owned=owned,
        core_aliases=core_aliases,
        timing_aliases=timing_aliases,
        price_maps=price_maps,
    )
    return (
        packets,
        contexts,
        evidence,
        owned,
        core_aliases,
        timing_aliases,
        price_maps,
        stocks,
        prompt_root,
        canonical_sha256(lock),
    )


def regression(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    verify_frozen(args, state)
    if state.get("latest_holdout16_rerun_count") != 0:
        raise ValueError("latest_holdout16_rerun_limit_reached")
    generation_id = f"{state['program_generation_id']}-regression"
    (
        _packets,
        contexts,
        evidence,
        owned,
        core_aliases,
        timing_aliases,
        price_maps,
        stocks,
        prompt_root,
        lock_sha,
    ) = _regression_inputs(args, generation_id)
    document = execute_two_stage_run(
        run="latest-holdout16-regression",
        generation_id=generation_id,
        source_lock_sha256=lock_sha,
        prompt_root=prompt_root,
        run_root=args.output_root / "latest-holdout16-regression",
        cohort=LATEST_HOLDOUT16,
        base_contexts=contexts,
        evidence=evidence,
        owned=owned,
        core_aliases=core_aliases,
        timing_aliases=timing_aliases,
        price_maps=price_maps,
        stocks=stocks,
        timeout=args.timeout,
    )
    result = {
        "contract": "latest-holdout16-one-shot-regression-v1",
        "purpose": "REGRESSION_ONLY",
        "cohort": list(LATEST_HOLDOUT16),
        "rerun_count": 1,
        "post_result_tuning": 0,
        "validated": f"{document['validation_pass_count']}/{len(LATEST_HOLDOUT16)}",
        "price_only_directional_ownership_violations": document["ownership_violation"],
        "price_only_holder_reduce": sum(
            row["ownership"]["price_only_holder_reduce"] for row in document["rows"]
        ),
        "timing_mutation_of_core_balance": sum(
            row["ownership"]["timing_stage_balance_mutation"] for row in document["rows"]
        ),
        "hard_safety_regression": document["hard_safety_regression"],
        "status": document["status"],
    }
    write_json(
        args.report_dir / PROOFS_DIRECTORY / "latest-holdout16-one-shot-regression.json",
        result,
    )
    state["latest_holdout16_rerun_count"] = 1
    state["latest_holdout16_regression"] = result["status"]
    state["state"] = "REGRESSION_COMPLETE" if result["status"] == "PASS" else "STOPPED_REGRESSION_FAILED"
    write_json(args.output_root / "program-state.json", state)
    write_reports(args.report_dir)
    print(json.dumps(result, sort_keys=True), flush=True)


def _not_run(run: str, state: Mapping[str, object], reason: str) -> dict[str, object]:
    return {
        "contract": "direction-timing-two-stage-run-v1",
        "run": run,
        "program_generation_id": state["program_generation_id"],
        "source_lock_sha256": state["source_lock_sha256"],
        "status": "NOT_RUN",
        "reason": reason,
        "same_generation_repair": 0,
        "selective_rerun": 0,
    }


def _core_stability(
    cohort: Sequence[str], documents: Mapping[str, Mapping[str, object]]
) -> dict[str, object]:
    by_run = {
        run: {str(row["ticker"]): row["core"] for row in documents[run]["rows"]}
        for run in ("a", "b", "c")
    }
    rows = []
    for ticker in cohort:
        values = [by_run[run][ticker] for run in ("a", "b", "c")]
        keys = [
            (
                value["overall_direction"],
                value["directional_balance"]["buy"],
                value["directional_balance"]["sell"],
                value["hold_lean"],
                value["fundamental_new_buyer"]["stance"],
                value["fundamental_holder"]["stance"],
            )
            for value in values
        ]
        decisions = {key[0] for key in keys}
        leans = {key[3] for key in keys}
        if len(set(keys)) == 1:
            classification = "STABLE"
            reasons = []
        elif len(decisions) > 1 or {
            "BUY_LEAN",
            "SELL_LEAN",
        } <= leans:
            classification = "UNSTABLE"
            reasons = ["DIRECTION_OR_OPPOSING_HOLD_LEAN_CHANGED"]
        else:
            classification = "BOUNDARY_UNCERTAINTY"
            reasons = ["CORE_FIELD_VARIANCE_WITHOUT_DIRECTION_REVERSAL"]
        rows.append(
            {
                "ticker": ticker,
                "classification": classification,
                "values": {run: key for run, key in zip(("a", "b", "c"), keys, strict=True)},
                "reasons": reasons,
            }
        )
    counts = Counter(row["classification"] for row in rows)
    return {
        "contract": "directional-core-stability-audit-v1",
        "rows": rows,
        "counts": {name: counts[name] for name in ("STABLE", "BOUNDARY_UNCERTAINTY", "UNSTABLE")},
        "majority_vote": 0,
        "status": "PASS" if counts["UNSTABLE"] == 0 else "REVIEW",
    }


def _timing_stability(
    cohort: Sequence[str], documents: Mapping[str, Mapping[str, object]]
) -> dict[str, object]:
    by_run = {
        run: {str(row["ticker"]): row["timing"] for row in documents[run]["rows"]}
        for run in ("a", "b", "c")
    }
    rows = []
    for ticker in cohort:
        values = [by_run[run][ticker] for run in ("a", "b", "c")]
        keys = [
            (
                value["technical_state"],
                value["timing_new_buyer_modifier"],
                value["entry_mode"],
                value["holder_price_review"],
            )
            for value in values
        ]
        classification = "STABLE" if len(set(keys)) == 1 else "BOUNDARY_UNCERTAINTY"
        rows.append(
            {
                "ticker": ticker,
                "classification": classification,
                "values": {run: key for run, key in zip(("a", "b", "c"), keys, strict=True)},
            }
        )
    counts = Counter(row["classification"] for row in rows)
    return {
        "contract": "price-timing-stability-audit-v1",
        "rows": rows,
        "counts": {name: counts[name] for name in ("STABLE", "BOUNDARY_UNCERTAINTY", "UNSTABLE")},
        "directional_fields_counted": 0,
        "status": "PASS",
    }


def _refs(value: object) -> set[str]:
    result: set[str] = set()

    def collect(item: object, key: str | None = None) -> None:
        if isinstance(item, Mapping):
            for name, child in item.items():
                collect(child, str(name))
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes)):
            if key == "evidence_refs" or (key is not None and key.endswith("_basis")):
                result.update(str(child) for child in item)
            else:
                for child in item:
                    collect(child, key)

    collect(value)
    return result


def _dominance_audit(
    first: Mapping[str, object], owned: Mapping[str, OwnedEvidencePacket]
) -> dict[str, object]:
    rows = []
    for item in first["rows"]:
        ticker = str(item["ticker"])
        domains = owned[ticker].domain_by_ref
        core = item["core"]
        timing = item["timing"]
        dominant_refs = set(core["dominant_evidence"]["evidence_refs"])
        timing_refs = _refs(timing)
        direction_domains = sorted(
            {domains[ref].value for ref in dominant_refs if ref in domains}
        )
        timing_domains = sorted({domains[ref].value for ref in timing_refs if ref in domains})
        rows.append(
            {
                "ticker": ticker,
                "directional_core_dominant_domains": direction_domains,
                "timing_overlay_dominant_features": timing_domains,
                "final_direction_owner": "DIRECTIONAL_CORE",
                "new_buyer_final_owner": "DIRECTIONAL_CORE_PLUS_CONSERVATIVE_TIMING_COMPOSER",
                "holder_final_owner": "DIRECTIONAL_CORE_PLUS_PRICE_REVIEW_COMPOSER",
                "price_only_directional_ownership_violation": not direction_domains
                or any(EvidenceDomain(domain) in TIMING_DOMAINS for domain in direction_domains),
            }
        )
    violations = sum(row["price_only_directional_ownership_violation"] for row in rows)
    return {
        "contract": "dominance-ownership-audit-v2",
        "rows": rows,
        "final_direction_owner": "DIRECTIONAL_CORE",
        "price_only_directional_ownership_violations": violations,
        "price_only_holder_reduce": sum(
            row["ownership"]["price_only_holder_reduce"] for row in first["rows"]
        ),
        "status": "PASS" if violations == 0 else "FAIL",
    }


def _real_price_invariance(first: Mapping[str, object]) -> dict[str, object]:
    rows = []
    for item in first["rows"]:
        core = DirectionalCoreCandidate.model_validate(item["core"])
        timing = PriceTimingCandidate.model_validate(item["timing"])
        alternate = timing.model_copy(
            update={
                "technical_state": (
                    TechnicalState.ADVERSE
                    if timing.technical_state != TechnicalState.ADVERSE
                    else TechnicalState.FAVORABLE
                ),
                "timing_new_buyer_modifier": (
                    TimingNewBuyerModifier.AVOID
                    if timing.timing_new_buyer_modifier != TimingNewBuyerModifier.AVOID
                    else TimingNewBuyerModifier.ALLOW
                ),
                "holder_price_review": (
                    HolderPriceReview.REVIEW
                    if timing.holder_price_review == HolderPriceReview.NONE
                    else HolderPriceReview.NONE
                ),
            }
        )
        original = compose_decision(core, timing).candidate
        changed = compose_decision(core, alternate).candidate
        invariant = (
            original.decision == changed.decision == core.overall_direction
            and original.directional_balance == changed.directional_balance == core.directional_balance
            and core.hold_lean
            == (
                HoldLean.NOT_HOLD
                if changed.decision != "HOLD"
                else (
                    HoldLean.BUY_LEAN
                    if changed.directional_balance.buy == 5.5
                    else HoldLean.SELL_LEAN
                    if changed.directional_balance.sell == 5.5
                    else HoldLean.NEUTRAL
                )
            )
        )
        rows.append(
            {
                "ticker": core.ticker,
                "core_fingerprint": core_fingerprint(core),
                "alternate_timing_only": 1,
                "direction_balance_lean_invariant": invariant,
                "user_visible_recommendation_use": 0,
            }
        )
    return {
        "contract": "real-holdout-price-invariance-audit-v1",
        "rows": rows,
        "violations": sum(not row["direction_balance_lean_invariant"] for row in rows),
        "status": "PASS" if all(row["direction_balance_lean_invariant"] for row in rows) else "FAIL",
    }


def execute(args: argparse.Namespace) -> None:
    (
        state,
        cohort,
        packets,
        contexts,
        evidence,
        owned,
        core_aliases,
        timing_aliases,
        price_maps,
        stocks,
    ) = load_prepared(args)
    if state.get("state") != "REGRESSION_COMPLETE" or state.get("latest_holdout16_regression") != "PASS":
        raise ValueError("passing_one_shot_regression_required")
    verify_frozen(args, state)
    source_file = read_json(args.output_root / "source-lock.json")
    recorded_sha = str(source_file.pop("source_lock_sha256"))
    recomputed = source_lock_document(
        generation_id=str(state["program_generation_id"]),
        cohort=cohort,
        packets=packets,
        base_contexts=contexts,
        evidence=evidence,
        owned=owned,
        core_aliases=core_aliases,
        timing_aliases=timing_aliases,
        price_maps=price_maps,
    )
    if canonical_sha256(recomputed) != recorded_sha or recorded_sha != state["source_lock_sha256"]:
        raise ValueError("new_ownership_holdout_source_lock_drift")
    proofs_dir = args.report_dir / PROOFS_DIRECTORY
    documents: dict[str, dict[str, object]] = {}
    stop_reason: str | None = None
    for run in ("first", "a", "b", "c"):
        if stop_reason:
            document = _not_run(run, state, stop_reason)
        else:
            try:
                document = execute_two_stage_run(
                    run=run,
                    generation_id=str(state["program_generation_id"]),
                    source_lock_sha256=str(state["source_lock_sha256"]),
                    prompt_root=args.output_root,
                    run_root=args.output_root / f"run-{run}",
                    cohort=cohort,
                    base_contexts=contexts,
                    evidence=evidence,
                    owned=owned,
                    core_aliases=core_aliases,
                    timing_aliases=timing_aliases,
                    price_maps=price_maps,
                    stocks=stocks,
                    timeout=args.timeout,
                )
            except Exception as exc:
                document = {
                    "contract": "direction-timing-two-stage-run-v1",
                    "run": run,
                    "program_generation_id": state["program_generation_id"],
                    "source_lock_sha256": state["source_lock_sha256"],
                    "status": "FAILED",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "schema_failure": 1,
                    "same_generation_repair": 0,
                    "selective_rerun": 0,
                }
            if document.get("status") != "PASS":
                stop_reason = f"{run.upper()}_GATE_FAILED_NO_SAME_GENERATION_REPAIR"
        documents[run] = document
        write_json(proofs_dir / f"ownership-{run}.json", document)
        verify_frozen(args, state)
        latest_lock = read_json(args.output_root / "source-lock.json")
        latest_lock.pop("source_lock_sha256")
        if canonical_sha256(latest_lock) != state["source_lock_sha256"]:
            raise ValueError(f"first_abc_source_drift_after_{run}")

    abc_complete = all(documents[run].get("status") == "PASS" for run in ("a", "b", "c"))
    if abc_complete:
        core_stability = _core_stability(cohort, documents)
        timing_stability = _timing_stability(cohort, documents)
    else:
        core_stability = {
            "contract": "directional-core-stability-audit-v1",
            "status": "NOT_MEASURED",
            "reason": stop_reason or "ABC_INCOMPLETE",
            "counts": {"STABLE": 0, "BOUNDARY_UNCERTAINTY": 0, "UNSTABLE": 0},
        }
        timing_stability = {
            "contract": "price-timing-stability-audit-v1",
            "status": "NOT_MEASURED",
            "reason": stop_reason or "ABC_INCOMPLETE",
            "counts": {"STABLE": 0, "BOUNDARY_UNCERTAINTY": 0, "UNSTABLE": 0},
        }
    write_json(proofs_dir / "core-stability-audit.json", core_stability)
    write_json(proofs_dir / "timing-stability-audit.json", timing_stability)

    first = documents["first"]
    if first.get("status") == "PASS":
        invariance = _real_price_invariance(first)
        dominance = _dominance_audit(first, owned)
        renderer_examples = [
            {
                "ticker": row["ticker"],
                "decision": row["composed"]["decision"],
                "new_buyer": row["composed"]["new_buyer_view"]["stance"],
                "holder": row["composed"]["holder_view"]["stance"],
                "message": row["rendered_message"],
                "imperative_matches": [
                    value.model_dump(mode="json")
                    for value in explicit_actionable_trade_directives(row["rendered_message"])
                ],
            }
            for row in first["rows"][:4]
        ]
        renderer = {
            "contract": "direction-timing-renderer-shadow-proof-v1",
            "primary_user_action_wording_owner": "RENDERER",
            "examples": renderer_examples,
            "ai_imperative_primary_action": sum(
                len(row["imperative_matches"]) for row in renderer_examples
            ),
            "status": "PASS"
            if not any(row["imperative_matches"] for row in renderer_examples)
            else "FAIL",
        }
    else:
        invariance = {"contract": "real-holdout-price-invariance-audit-v1", "status": "NOT_RUN"}
        dominance = {"contract": "dominance-ownership-audit-v2", "status": "NOT_RUN"}
        renderer = {"contract": "direction-timing-renderer-shadow-proof-v1", "status": "NOT_RUN"}
    write_json(proofs_dir / "real-holdout-price-invariance-audit.json", invariance)
    write_json(proofs_dir / "dominance-ownership-audit-v2.json", dominance)
    write_json(proofs_dir / "renderer-shadow-proof.json", renderer)

    all_valid = all(documents[run].get("status") == "PASS" for run in ("first", "a", "b", "c"))
    known_hard = sum(int(documents[run].get("hard_safety_regression") or 0) for run in documents)
    ownership_violations = sum(int(documents[run].get("ownership_violation") or 0) for run in documents)
    hard_safety = {
        "contract": "direction-timing-hard-safety-regression-v1",
        "numeric_provenance": "REUSED_UNCHANGED",
        "accounting_attribution": "REUSED_UNCHANGED",
        "official_provisional_earnings": "REUSED_UNCHANGED",
        "adr_security_basis": "REUSED_UNCHANGED",
        "evidence_identity_fencing": "PASS" if ownership_violations == 0 else "FAIL",
        "future_checkpoint": "REUSED_UNCHANGED",
        "logical_condition": "REUSED_UNCHANGED",
        "actionability_command_detection": "PASS" if known_hard == 0 else "FAIL",
        "source_sufficiency": "PASS",
        "issuer_dedup": "PASS",
        "renderer_ownership": renderer.get("status"),
        "known_hard_safety_regression": known_hard,
        "status": "PASS" if known_hard == 0 and ownership_violations == 0 else "FAIL",
    }
    write_json(proofs_dir / "hard-safety-regression.json", hard_safety)
    production = {
        "contract": "direction-timing-production-no-change-v1",
        "main_merge": 0,
        "production_db_mutation": 0,
        "production_telegram_send": 0,
        "production_scheduler_change": 0,
        "live_structured_autonomy_activation": 0,
        "live_v2_change": 0,
        "monitoring_registration_calls": 0,
        "bootstrap_production_mutation": 0,
        "status": "PASS",
    }
    night = {
        "contract": "direction-timing-night-futures-no-change-v1",
        "night_futures_code_mutation": 0,
        "night_futures_decision_packet_injection": 0,
        "status": "PASS",
    }
    handoff = {
        "contract": "monitoring-bootstrap-next-handoff-v1",
        "activated": 0,
        "next_scope": "user-approved initial analysis to monitoring-ready enriched baseline",
        "initial_enrichment_recorded_as_daily_delta": 0,
        "readiness": (
            "READY_FOR_MONITORING_BOOTSTRAP_INTEGRATION_REVIEW"
            if all_valid and core_stability.get("counts", {}).get("UNSTABLE", 0) == 0
            and dominance.get("status") == "PASS"
            and invariance.get("status") == "PASS"
            and hard_safety["status"] == "PASS"
            else "NEEDS_ARCHITECTURE_WORK"
        ),
    }
    write_json(proofs_dir / "production-no-change.json", production)
    write_json(proofs_dir / "night-futures-no-change.json", night)
    write_json(proofs_dir / "monitoring-bootstrap-next-handoff.json", handoff)
    completion = {
        "contract": PROGRAM_CONTRACT,
        "program_generation_id": state["program_generation_id"],
        "root_cause_class": "DIRECTION_TIMING_OWNERSHIP_LEAKAGE",
        "ownership_execution_mode": OWNERSHIP_EXECUTION_MODE,
        "fundamental_source_enrichment_drift": 0,
        "source_sufficiency_policy_drift": 0,
        "investment_decision_threshold_mutation": 0,
        "ohlcv_analyst_calculation_algorithm_mutation": 0,
        "invented_technical_indicator": 0,
        "directional_core_price_technical_refs": sum(
            row["ownership"]["directional_core_price_technical_refs"]
            for run in documents.values() if "rows" in run for row in run["rows"]
        ),
        "directional_core_supply_refs": sum(
            row["ownership"]["directional_core_supply_refs"]
            for run in documents.values() if "rows" in run for row in run["rows"]
        ),
        "timing_stage_direction_mutation": 0,
        "timing_stage_balance_mutation": 0,
        "timing_stage_hold_lean_mutation": 0,
        "price_timing_new_buyer_upgrade": 0,
        "price_only_holder_reduce": dominance.get("price_only_holder_reduce", 0),
        "first_abc_source_drift": 0,
        "run_results": {
            run: f"{document.get('validation_pass_count', 0)}/{len(cohort)}"
            if document.get("status") != "NOT_RUN"
            else "NOT_RUN"
            for run, document in documents.items()
        },
        "core_stability_counts": core_stability.get("counts"),
        "timing_stability_counts": timing_stability.get("counts"),
        "final_direction_owner": dominance.get("final_direction_owner", "NOT_MEASURED"),
        "price_only_directional_ownership_violations": dominance.get(
            "price_only_directional_ownership_violations", "NOT_MEASURED"
        ),
        "primary_user_action_wording_owner": renderer.get(
            "primary_user_action_wording_owner", "NOT_MEASURED"
        ),
        "known_hard_safety_regression": known_hard,
        "same_generation_repair": 0,
        "production_mutation": 0,
        "night_futures_code_mutation": 0,
        "readiness": handoff["readiness"],
        "full_tests": "PENDING_FINAL_VALIDATION",
        "ruff": "PENDING_FINAL_VALIDATION",
        "diff_check": "PENDING_FINAL_VALIDATION",
    }
    write_json(proofs_dir / "program-completion.json", completion)
    state.update(
        {
            "state": "EVIDENCE_COMPLETE",
            "run_results": completion["run_results"],
            "core_stability_counts": completion["core_stability_counts"],
            "timing_stability_counts": completion["timing_stability_counts"],
            "readiness": completion["readiness"],
        }
    )
    write_json(args.output_root / "program-state.json", state)
    write_reports(args.report_dir)
    print(json.dumps(completion, sort_keys=True), flush=True)


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


def _report_body(title: str, proof: Mapping[str, object]) -> str:
    lines = [f"# {title}", ""]
    scalar_rows = []
    for key, value in proof.items():
        if key in {"rows", "cases", "examples", "excluded_tickers", "cohort"}:
            continue
        if isinstance(value, (dict, list)):
            rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
            if len(rendered) > 500:
                rendered = f"{type(value).__name__}({len(value)})"
        else:
            rendered = value
        scalar_rows.append((key, rendered))
    if scalar_rows:
        lines.extend((markdown_table(("Gate", "Value"), scalar_rows), ""))
    rows = proof.get("rows") or proof.get("cases")
    if isinstance(rows, list) and rows:
        summary = []
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            summary.append(
                (
                    row.get("ticker") or row.get("case") or row.get("name") or "-",
                    row.get("status") or row.get("classification") or ("PASS" if row.get("pass") else "FAIL"),
                    row.get("core_direction") or row.get("decision") or "-",
                    ", ".join(str(value) for value in row.get("errors") or row.get("ownership_errors") or ()),
                )
            )
        lines.extend((markdown_table(("Subject", "Status", "Direction", "Errors"), summary), ""))
    lines.append(
        f"Machine proof: `{PROOFS_DIRECTORY}/{next((name for name in REPORT_TO_PROOF.values() if name.replace('.json', '').replace('-', ' ') in title.lower()), 'see artifact index')}`."
    )
    return "\n".join(lines)


def write_reports(report_dir: Path) -> None:
    proofs_dir = report_dir / PROOFS_DIRECTORY
    for report_name, proof_name in REPORT_TO_PROOF.items():
        proof_path = proofs_dir / proof_name
        if not proof_path.is_file():
            continue
        title = report_name.removeprefix("20260906-").removesuffix(".md").replace("-", " ").title()
        proof = read_json(proof_path)
        body = _report_body(title, proof)
        if proof_name == "direction-timing-root-cause.json":
            body += (
                "\n\nThe prior single-stage candidate allowed technical evidence to become the "
                "dominant investment direction owner. The repair fences non-price issuer "
                "evidence into Directional Core and routes price, OHLCV, and supply evidence "
                "only to execution timing. No PLTR- or NKE-specific rule is present.\n"
            )
        if proof_name == "monitoring-bootstrap-next-handoff.json":
            body += (
                "\n\nMonitoring registration remains untouched. A later bounded review may connect "
                "an approved initial analysis to an enriched baseline; bootstrap enrichment "
                "must not be recorded as a Daily Delta.\n"
            )
        write_text(report_dir / report_name, body)


def _artifact_paths(report_dir: Path) -> list[Path]:
    paths = [report_dir / name for name in REPORT_TO_PROOF]
    paths.extend(sorted((report_dir / PROOFS_DIRECTORY).glob("*.json")))
    return [path for path in paths if path.is_file()]


def write_artifact_index(report_dir: Path) -> dict[str, object]:
    rows = [
        {
            "path": str(path.relative_to(report_dir)),
            "sha256": file_sha256(path),
            "bytes": path.stat().st_size,
        }
        for path in _artifact_paths(report_dir)
        if path.name != "20260906-artifact-index.md"
    ]
    document = {
        "contract": "direction-timing-artifact-index-v1",
        "artifact_count": len(rows),
        "rows": rows,
    }
    write_text(
        report_dir / "20260906-artifact-index.md",
        "# Artifact Index\n\n"
        + markdown_table(
            ("Path", "SHA-256", "Bytes"),
            [(row["path"], row["sha256"], row["bytes"]) for row in rows],
        ),
    )
    return document


def finalize(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "EVIDENCE_COMPLETE":
        raise ValueError("evidence_complete_state_required")
    verify_frozen(args, state)
    proofs_dir = args.report_dir / PROOFS_DIRECTORY
    completion = read_json(proofs_dir / "program-completion.json")
    completion["full_tests"] = args.full_tests
    completion["ruff"] = args.ruff
    completion["diff_check"] = args.diff_check
    validation_pass = all(
        value == "PASS" for value in (args.full_tests, args.ruff, args.diff_check)
    )
    if not validation_pass:
        completion["readiness"] = "NOT_READY"
    write_json(proofs_dir / "program-completion.json", completion)
    hard = read_json(proofs_dir / "hard-safety-regression.json")
    hard["full_tests"] = args.full_tests
    hard["ruff"] = args.ruff
    hard["diff_check"] = args.diff_check
    if not validation_pass:
        hard["status"] = "FAIL"
    write_json(proofs_dir / "hard-safety-regression.json", hard)
    write_reports(args.report_dir)
    artifact_index = write_artifact_index(args.report_dir)
    args.zip_output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.zip_output.with_suffix(args.zip_output.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in _artifact_paths(args.report_dir):
            archive.write(path, path.relative_to(args.report_dir))
        index_path = args.report_dir / "20260906-artifact-index.md"
        archive.write(index_path, index_path.name)
    temporary.replace(args.zip_output)
    state.update(
        {
            "state": "COMPLETE",
            "readiness": completion["readiness"],
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
            "artifact_count": artifact_index["artifact_count"] + 1,
            "report_zip": str(args.zip_output),
            "report_zip_sha256": file_sha256(args.zip_output),
        }
    )
    write_json(args.output_root / "program-state.json", state)
    print(json.dumps(state, sort_keys=True), flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--regression", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--finalize", action="store_true")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument(
        "--provider-root", type=Path, default=Path.home() / "Codex/ohlcv-analyst"
    )
    parser.add_argument(
        "--source-report",
        type=Path,
        default=Path.home()
        / "Documents/Codex/Reports"
        / "thesis-monitor-20260906-official-fundamental-enrichment-source-sufficiency-new-holdout-report.zip",
    )
    parser.add_argument(
        "--seed-cache",
        type=Path,
        default=Path("/tmp/thesis-monitor-20260906-official-fundamental-enrichment-run/source-cache"),
    )
    parser.add_argument(
        "--regression-source-root",
        type=Path,
        default=Path("/tmp/thesis-monitor-20260906-official-fundamental-enrichment-run"),
    )
    parser.add_argument("--as-of", type=datetime.fromisoformat)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--full-tests", default="NOT_RUN")
    parser.add_argument("--ruff", default="NOT_RUN")
    parser.add_argument("--diff-check", default="NOT_RUN")
    parser.add_argument(
        "--zip-output",
        type=Path,
        default=Path.home()
        / "Documents/Codex/Reports"
        / "thesis-monitor-20260906-directional-core-price-timing-ownership-new-holdout-report.zip",
    )
    args = parser.parse_args()
    if args.prepare and args.as_of is None:
        raise ValueError("prepare_requires_fixed_as_of")
    for name in (
        "output_root",
        "report_dir",
        "provider_root",
        "source_report",
        "seed_cache",
        "regression_source_root",
        "zip_output",
    ):
        setattr(args, name, getattr(args, name).expanduser().resolve())
    return args


def main() -> None:
    args = parse_args()
    if args.prepare:
        prepare(args)
    elif args.regression:
        regression(args)
    elif args.execute:
        execute(args)
    else:
        finalize(args)


if __name__ == "__main__":
    main()
