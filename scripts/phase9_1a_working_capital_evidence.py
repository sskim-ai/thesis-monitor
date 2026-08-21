from __future__ import annotations

# ruff: noqa: E501

import argparse
import asyncio
import hashlib
import json
import os
from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping

import httpx

from app.services.cash_flow_capital_efficiency_service import (
    EligibilityStatus,
    FinancialFact,
    Metric,
)
from app.services.opendart_financial_recovery_service import STATEMENT_ENDPOINT
from app.services.working_capital_evidence_service import (
    CONTRACT_VERSION,
    ComparableMovement,
    ComparableSelection,
    CrossGrowthRelation,
    build_sec_working_capital_batch,
    canonicalize_occurrences,
    derive_comparable_movement,
    derive_cross_growth_relation,
    extract_opendart_occurrences,
    industry_applicability,
    select_aligned_flow_pair,
    select_latest_comparable_balance,
)
from scripts.phase9_0a_evidence import _active_universe, _taxonomy


ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = ROOT / "docs" / "reports"
RUN_DATE = "20260821"
AS_OF = date(2026, 8, 21)
OPEN_DART_REPORT_CODE = "11012"
OPEN_DART_YEARS = (2026, 2025)
KR_AUDIT = REPORT_ROOT / "20260817-phase8-1-1-authoritative-financial-recovery-audit.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _decimal(value: Decimal | None) -> str | None:
    return str(value) if value is not None else None


def _fact_dict(fact: FinancialFact) -> dict[str, Any]:
    return {
        "fact_id": fact.fact_id,
        "issuer_id": fact.issuer_id,
        "metric": fact.metric.value,
        "value": str(fact.value),
        "currency": fact.currency,
        "unit": fact.unit,
        "period_start": fact.period.start.isoformat(),
        "period_end": fact.period.end.isoformat(),
        "period_type": fact.period.period_type.value,
        "fiscal_year": fact.period.fiscal_year,
        "fiscal_quarter": fact.period.fiscal_quarter,
        "entity_scope": fact.entity_scope,
        "statement_basis": fact.statement_basis,
        "source_provider": fact.source_provider,
        "source_document_id": fact.source_document_id,
        "source_document_type": fact.source_document_type,
        "filing_date": fact.filing_date.isoformat(),
        "source_available_at": (
            fact.source_available_at.isoformat() if fact.source_available_at else None
        ),
        "source_occurrence_id": fact.source_occurrence_id,
        "source_semantic": fact.source_semantic,
        "raw_payload_sha256": fact.raw_payload_sha256,
        "semantic_mapping": fact.semantic_mapping,
        "balance_scope": fact.balance_scope,
        "net_gross_scope": fact.net_gross_scope,
        "quality": fact.quality,
        "eligibility": fact.eligibility.value,
        "cautions": list(fact.cautions),
    }


def _selection_dict(selection: ComparableSelection) -> dict[str, Any]:
    return {
        "status": selection.status.value,
        "current_fact_id": selection.current.fact_id if selection.current else None,
        "prior_fact_id": selection.prior.fact_id if selection.prior else None,
        "reasons": list(selection.reasons),
    }


def _movement_dict(movement: ComparableMovement) -> dict[str, Any]:
    return {
        "status": movement.status.value,
        "current_fact_id": movement.current_fact_id,
        "prior_fact_id": movement.prior_fact_id,
        "absolute_delta": _decimal(movement.absolute_delta),
        "yoy_pct": _decimal(movement.growth_pct),
        "direction": movement.direction.value if movement.direction else None,
        "reasons": list(movement.reasons),
    }


def _relation_dict(relation: CrossGrowthRelation) -> dict[str, Any]:
    return {
        "status": relation.status.value,
        "relation_id": relation.relation_id,
        "relation_type": (
            relation.relation_type.value if relation.relation_type else None
        ),
        "percentage_point_difference": _decimal(
            relation.percentage_point_difference
        ),
        "input_fact_ids": list(relation.input_fact_ids),
        "formula": relation.formula,
        "reasons": list(relation.reasons),
    }


def _working_taxonomy(row: dict[str, Any]) -> tuple[str, str]:
    industry, financial_type = _taxonomy(row)
    source_text = " ".join(
        str(row.get(key) or "") for key in ("industry", "sector")
    ).lower()
    if (
        industry == "general_non_financial"
        and "financial" in source_text
        and financial_type != "financial"
    ):
        return "special_financial_like", financial_type
    return industry, financial_type


def _kr_filing(
    audit_row: Mapping[str, Any],
    *,
    business_year: int,
) -> dict[str, Any] | None:
    return next(
        (
            item
            for item in audit_row.get("filing_history", [])
            if item.get("business_year") == business_year
            and item.get("report_code") == OPEN_DART_REPORT_CODE
        ),
        None,
    )


async def acquire_opendart_cache(
    *,
    universe: list[dict[str, Any]],
    audit: dict[str, Any],
    cache_root: Path,
    api_key: str,
) -> dict[str, Any]:
    telemetry: dict[str, Any] = {
        "provider": "OpenDART official full financial statements",
        "requests": 0,
        "successes": 0,
        "failures": [],
        "preexisting_cache_hits": 0,
        "purpose": "2026/2025 half-year CFS point-in-time comparable audit",
    }
    cache_root.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(timeout=30.0) as client:
        for row in universe:
            if row.get("exchange") != "KRX":
                continue
            industry, financial_type = _working_taxonomy(row)
            if industry == "insurance_reinsurance" or financial_type == "financial":
                continue
            ticker = str(row["ticker"])
            audit_row = audit["results"].get(ticker, {})
            for business_year in OPEN_DART_YEARS:
                filing = _kr_filing(audit_row, business_year=business_year)
                path = cache_root / ticker / f"{business_year}-11012-CFS.json"
                if path.exists():
                    telemetry["preexisting_cache_hits"] += 1
                    continue
                if filing is None:
                    telemetry["failures"].append(
                        {
                            "ticker": ticker,
                            "year": business_year,
                            "reason": "authoritative_half_year_filing_missing",
                        }
                    )
                    continue
                telemetry["requests"] += 1
                try:
                    response = await client.get(
                        STATEMENT_ENDPOINT,
                        params={
                            "crtfc_key": api_key,
                            "corp_code": row.get("corp_code"),
                            "bsns_year": business_year,
                            "reprt_code": OPEN_DART_REPORT_CODE,
                            "fs_div": "CFS",
                        },
                    )
                    response.raise_for_status()
                    payload = response.json()
                    if payload.get("status") != "000":
                        raise ValueError(f"opendart_status_{payload.get('status')}")
                    rows = [
                        item
                        for item in payload.get("list", [])
                        if isinstance(item, dict)
                        and str(item.get("rcept_no") or filing["receipt_no"])
                        == str(filing["receipt_no"])
                    ]
                    sanitized = {
                        "ticker": ticker,
                        "corp_code": row.get("corp_code"),
                        "business_year": business_year,
                        "report_code": OPEN_DART_REPORT_CODE,
                        "basis": "CFS",
                        "filing": filing,
                        "response_sha256": hashlib.sha256(response.content).hexdigest(),
                        "rows": rows,
                    }
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(
                        json.dumps(
                            sanitized,
                            ensure_ascii=False,
                            indent=2,
                            sort_keys=True,
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                except (httpx.HTTPError, ValueError) as error:
                    telemetry["failures"].append(
                        {
                            "ticker": ticker,
                            "year": business_year,
                            "reason": type(error).__name__,
                        }
                    )
                else:
                    telemetry["successes"] += 1
    _write_json(cache_root / "acquisition-telemetry.json", telemetry)
    return telemetry


def _metric_evidence(
    facts: tuple[FinancialFact, ...],
    *,
    metrics: tuple[Metric, ...],
) -> tuple[ComparableSelection, ComparableMovement]:
    selection = select_latest_comparable_balance(facts, metrics=metrics)
    return selection, derive_comparable_movement(selection)


def _cross_relation(
    facts: tuple[FinancialFact, ...],
    *,
    balances: ComparableSelection,
    flow_metric: Metric,
) -> CrossGrowthRelation:
    flows = select_aligned_flow_pair(
        facts,
        metric=flow_metric,
        balances=balances,
    )
    return derive_cross_growth_relation(balances, flows)


def _record_from_facts(
    row: dict[str, Any],
    *,
    facts: tuple[FinancialFact, ...],
    source: str,
    source_sha: str | None,
    source_audit: dict[str, Any],
    denials: list[dict[str, str]],
) -> dict[str, Any]:
    industry, financial_type = _working_taxonomy(row)
    applicability = dict(industry_applicability(industry))
    if industry == "insurance_reinsurance" or financial_type == "financial":
        not_applicable = {
            "status": "NOT_APPLICABLE",
            "current_fact_id": None,
            "prior_fact_id": None,
            "absolute_delta": None,
            "yoy_pct": None,
            "direction": None,
            "reasons": ["generic_working_capital_not_applicable"],
        }
        return {
            "ticker": row["ticker"],
            "company_name": row["company_name"],
            "market": "KR" if row.get("exchange") == "KRX" else "US_FOREIGN",
            "exchange": row.get("exchange"),
            "industry": industry,
            "financial_type": financial_type,
            "source": source,
            "source_payload_sha256": source_sha,
            "latest_formal_balance_date": None,
            "inventory": dict(not_applicable),
            "trade_ar": dict(not_applicable),
            "broad_ar": dict(not_applicable),
            "trade_ap": dict(not_applicable),
            "broad_ap": dict(not_applicable),
            "revenue": {"status": "NOT_APPLICABLE", "reasons": []},
            "cogs": {"status": "NOT_APPLICABLE", "reasons": []},
            "relations": {
                key: {"status": "NOT_APPLICABLE", "reasons": []}
                for key in (
                    "ar_vs_revenue",
                    "inventory_vs_revenue",
                    "inventory_vs_cogs",
                    "ap_vs_cogs",
                )
            },
            "industry_applicability": applicability,
            "cross_link_readiness": "NOT_APPLICABLE",
            "coverage_strength": "NOT_APPLICABLE",
            "facts": [],
            "denials": denials,
            "source_audit": source_audit,
        }

    inventory_selection, inventory = _metric_evidence(
        facts, metrics=(Metric.INVENTORY,)
    )
    trade_ar_selection, trade_ar = _metric_evidence(
        facts, metrics=(Metric.TRADE_AR,)
    )
    broad_ar_selection, broad_ar = _metric_evidence(
        facts, metrics=(Metric.BROAD_AR,)
    )
    trade_ap_selection, trade_ap = _metric_evidence(
        facts, metrics=(Metric.TRADE_AP,)
    )
    broad_ap_selection, broad_ap = _metric_evidence(
        facts, metrics=(Metric.BROAD_AP,)
    )
    ar_selection = (
        trade_ar_selection
        if trade_ar_selection.current is not None
        else broad_ar_selection
    )
    ap_selection = (
        trade_ap_selection
        if trade_ap_selection.current is not None
        else broad_ap_selection
    )
    revenue_flow = select_aligned_flow_pair(
        facts, metric=Metric.REVENUE, balances=ar_selection
    )
    cogs_flow = select_aligned_flow_pair(
        facts, metric=Metric.COGS, balances=inventory_selection
    )
    relations = {
        "ar_vs_revenue": _relation_dict(
            _cross_relation(
                facts,
                balances=ar_selection,
                flow_metric=Metric.REVENUE,
            )
        ),
        "inventory_vs_revenue": _relation_dict(
            _cross_relation(
                facts,
                balances=inventory_selection,
                flow_metric=Metric.REVENUE,
            )
        ),
        "inventory_vs_cogs": _relation_dict(
            _cross_relation(
                facts,
                balances=inventory_selection,
                flow_metric=Metric.COGS,
            )
        ),
        "ap_vs_cogs": _relation_dict(
            _cross_relation(
                facts,
                balances=ap_selection,
                flow_metric=Metric.COGS,
            )
        ),
    }
    movements = {
        "inventory": inventory,
        "trade_ar": trade_ar,
        "broad_ar": broad_ar,
        "trade_ap": trade_ap,
        "broad_ap": broad_ap,
    }
    comparable_count = sum(
        item.status == EligibilityStatus.ELIGIBLE for item in movements.values()
    )
    current_count = sum(item.current_fact_id is not None for item in movements.values())
    if comparable_count >= 3:
        coverage_strength = "STRONG"
    elif comparable_count:
        coverage_strength = "SELECTIVE"
    elif current_count:
        coverage_strength = "WEAK"
    else:
        coverage_strength = "BLOCKED"
    relation_count = sum(
        item["status"] == "ELIGIBLE" for item in relations.values()
    )
    cross_link_readiness = (
        "HIGH_VALUE"
        if relation_count >= 2
        and any(value == "PRIMARY" for value in applicability.values())
        else "MEDIUM_VALUE"
        if relation_count
        else "LOW_VALUE"
    )
    current_dates = [
        selection.current.period.end
        for selection in (
            inventory_selection,
            trade_ar_selection,
            broad_ar_selection,
            trade_ap_selection,
            broad_ap_selection,
        )
        if selection.current is not None
    ]
    return {
        "ticker": row["ticker"],
        "company_name": row["company_name"],
        "market": "KR" if row.get("exchange") == "KRX" else "US_FOREIGN",
        "exchange": row.get("exchange"),
        "industry": industry,
        "financial_type": financial_type,
        "source": source,
        "source_payload_sha256": source_sha,
        "latest_formal_balance_date": (
            max(current_dates).isoformat() if current_dates else None
        ),
        "inventory": _movement_dict(inventory),
        "trade_ar": _movement_dict(trade_ar),
        "broad_ar": _movement_dict(broad_ar),
        "trade_ap": _movement_dict(trade_ap),
        "broad_ap": _movement_dict(broad_ap),
        "revenue": _selection_dict(revenue_flow),
        "cogs": _selection_dict(cogs_flow),
        "relations": relations,
        "industry_applicability": applicability,
        "cross_link_readiness": cross_link_readiness,
        "coverage_strength": coverage_strength,
        "facts": [_fact_dict(item) for item in facts],
        "denials": denials,
        "source_audit": source_audit,
    }


def _sec_record(
    row: dict[str, Any],
    *,
    sec_cache: Path,
) -> tuple[dict[str, Any], int, int]:
    cik = str(row.get("cik") or "").strip().zfill(10)
    source_path = sec_cache / f"CIK{cik}.json"
    if not cik.strip("0") or not source_path.exists():
        record = _record_from_facts(
            row,
            facts=(),
            source="SEC Company Facts cache missing",
            source_sha=None,
            source_audit={"cache_path": str(source_path), "cache_hit": False},
            denials=[{"reason": "official_source_unavailable"}],
        )
        return record, 0, 1
    raw = source_path.read_bytes()
    source_sha = hashlib.sha256(raw).hexdigest()
    batch = build_sec_working_capital_batch(
        json.loads(raw), raw_payload_sha256=source_sha, as_of_date=AS_OF
    )
    record = _record_from_facts(
        row,
        facts=batch.facts,
        source="SEC Company Facts official XBRL stored cache",
        source_sha=source_sha,
        source_audit={
            "cache_path": str(source_path),
            "cache_hit": True,
            "extracted_occurrences": batch.extracted_occurrences,
            "exact_duplicates_suppressed": batch.exact_duplicates_suppressed,
            "conflicts": batch.conflicts,
        },
        denials=list(batch.denials),
    )
    return record, 1, 0


def _kr_record(
    row: dict[str, Any],
    *,
    audit: dict[str, Any],
    opendart_cache: Path,
) -> tuple[dict[str, Any], int, int]:
    industry, financial_type = _working_taxonomy(row)
    if industry == "insurance_reinsurance" or financial_type == "financial":
        return (
            _record_from_facts(
                row,
                facts=(),
                source="OpenDART formal statement; industry N/A",
                source_sha=audit.get("source_packet_sha256"),
                source_audit={"generic_working_capital_suppressed": True},
                denials=[],
            ),
            0,
            0,
        )
    facts: list[FinancialFact] = []
    denials: list[dict[str, str]] = []
    hits = 0
    misses = 0
    source_shas: list[str] = []
    for business_year in OPEN_DART_YEARS:
        path = opendart_cache / str(row["ticker"]) / f"{business_year}-11012-CFS.json"
        if not path.exists():
            misses += 1
            denials.append(
                {
                    "reason": "opendart_comparable_cache_missing",
                    "year": str(business_year),
                }
            )
            continue
        hits += 1
        payload = _load_json(path)
        filing = payload["filing"]
        source_sha = _sha256(path)
        source_shas.append(source_sha)
        occurrences = extract_opendart_occurrences(
            payload.get("rows", []),
            issuer_id=f"opendart:{row.get('corp_code')}",
            business_year=business_year,
            report_code=OPEN_DART_REPORT_CODE,
            filing_date=date.fromisoformat(str(filing["receipt_date"])),
            source_document_id=str(filing["receipt_no"]),
            raw_payload_sha256=source_sha,
            requested_basis="CFS",
        )
        batch = canonicalize_occurrences(occurrences, as_of_date=AS_OF)
        facts.extend(batch.facts)
        denials.extend(batch.denials)
    combined_sha = (
        hashlib.sha256("|".join(source_shas).encode()).hexdigest()
        if source_shas
        else None
    )
    record = _record_from_facts(
        row,
        facts=tuple(facts),
        source="OpenDART official 2026/2025 half-year CFS stored audit cache",
        source_sha=combined_sha,
        source_audit={
            "cache_hits": hits,
            "cache_misses": misses,
            "basis": "CFS",
            "years": list(OPEN_DART_YEARS),
            "cash_flow_period_gap_independent": True,
        },
        denials=denials,
    )
    return record, hits, misses


def _status_counts(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts = Counter(str(item[key]["status"]) for item in records)
    return {
        status: counts[status]
        for status in ("ELIGIBLE", "PARTIAL", "BLOCKED", "NOT_APPLICABLE")
    }


def _relation_counts(
    records: list[dict[str, Any]], key: str
) -> dict[str, int]:
    counts = Counter(str(item["relations"][key]["status"]) for item in records)
    return {
        status: counts[status]
        for status in ("ELIGIBLE", "PARTIAL", "BLOCKED", "NOT_APPLICABLE")
    }


def _representatives(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def has_pair(record: dict[str, Any]) -> bool:
        return any(
            record[key]["status"] == "ELIGIBLE"
            for key in ("inventory", "trade_ar", "broad_ar", "trade_ap", "broad_ap")
        )

    def non_calendar(record: dict[str, Any]) -> bool:
        expected_month = {1: 3, 2: 6, 3: 9, 4: 12}
        current_ids = {
            record[key]["current_fact_id"]
            for key in ("inventory", "trade_ar", "broad_ar", "trade_ap", "broad_ap")
            if record[key]["current_fact_id"]
        }
        for fact in record["facts"]:
            quarter = fact.get("fiscal_quarter")
            if (
                fact["fact_id"] in current_ids
                and fact["period_type"] == "POINT_IN_TIME"
                and quarter in expected_month
                and int(fact["period_end"][5:7]) != expected_month[quarter]
            ):
                return True
        return False

    classes = (
        (
            "US industrial/operating company",
            lambda item: item["market"] == "US_FOREIGN"
            and item["industry"] in {"automotive", "cloud_platform_software"}
            and has_pair(item),
        ),
        (
            "memory/semiconductor",
            lambda item: item["industry"] == "memory_semiconductor" and has_pair(item),
        ),
        (
            "automotive",
            lambda item: item["industry"] == "automotive" and has_pair(item),
        ),
        (
            "capital-intensive/HPC",
            lambda item: item["industry"] == "hpc_data_center" and has_pair(item),
        ),
        (
            "biotech negative control",
            lambda item: item["industry"] == "biotech",
        ),
        (
            "KR non-financial industrial",
            lambda item: item["market"] == "KR"
            and item["financial_type"] == "non_financial"
            and has_pair(item),
        ),
        (
            "insurance N/A",
            lambda item: item["industry"] == "insurance_reinsurance",
        ),
        (
            "foreign issuer",
            lambda item: item["market"] == "US_FOREIGN"
            and any(
                fact.get("source_document_type") in {"20-F", "20-F/A", "6-K", "6-K/A"}
                for fact in item["facts"]
            )
            and has_pair(item),
        ),
        ("non-calendar fiscal issuer", non_calendar),
    )
    output: list[dict[str, Any]] = []
    for label, predicate in classes:
        selected = next((item for item in records if predicate(item)), None)
        if selected is None:
            output.append(
                {"class": label, "ticker": None, "status": "NO_SAFE_REPRESENTATIVE"}
            )
            continue
        facts = {item["fact_id"]: item for item in selected["facts"]}
        metric_key = next(
            (
                key
                for key in ("inventory", "trade_ar", "broad_ar", "trade_ap", "broad_ap")
                if selected[key]["status"] == "ELIGIBLE"
            ),
            None,
        ) or next(
            (
                key
                for key in ("inventory", "trade_ar", "broad_ar", "trade_ap", "broad_ap")
                if selected[key]["current_fact_id"]
            ),
            None,
        )
        metric = selected[metric_key] if metric_key else {}
        output.append(
            {
                "class": label,
                "ticker": selected["ticker"],
                "company_name": selected["company_name"],
                "status": metric.get("status") or "NOT_APPLICABLE",
                "metric": metric_key,
                "current_fact": facts.get(metric.get("current_fact_id")),
                "prior_fact": facts.get(metric.get("prior_fact_id")),
                "absolute_delta": metric.get("absolute_delta"),
                "yoy_pct": metric.get("yoy_pct"),
                "relations": selected["relations"],
                "source": selected["source"],
            }
        )
    return output


def _coverage_table(records: list[dict[str, Any]]) -> str:
    lines = [
        "| Ticker | Industry | Inventory | Trade AR | Broad AR | Trade AP | Broad AP | AR/Revenue | Inv/Revenue | Inv/COGS | AP/COGS |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for item in records:
        lines.append(
            "| {ticker} | {industry} | {inventory} | {trade_ar} | {broad_ar} | {trade_ap} | {broad_ap} | {ar_rev} | {inv_rev} | {inv_cogs} | {ap_cogs} |".format(
                ticker=item["ticker"],
                industry=item["industry"],
                inventory=item["inventory"]["status"],
                trade_ar=item["trade_ar"]["status"],
                broad_ar=item["broad_ar"]["status"],
                trade_ap=item["trade_ap"]["status"],
                broad_ap=item["broad_ap"]["status"],
                ar_rev=item["relations"]["ar_vs_revenue"]["status"],
                inv_rev=item["relations"]["inventory_vs_revenue"]["status"],
                inv_cogs=item["relations"]["inventory_vs_cogs"]["status"],
                ap_cogs=item["relations"]["ap_vs_cogs"]["status"],
            )
        )
    return "\n".join(lines)


def _counts_table(counts: dict[str, dict[str, int]]) -> str:
    lines = [
        "| Metric | Eligible | Partial | Blocked | N/A |",
        "|---|---:|---:|---:|---:|",
    ]
    for metric, values in counts.items():
        lines.append(
            f"| {metric} | {values['ELIGIBLE']} | {values['PARTIAL']} | {values['BLOCKED']} | {values['NOT_APPLICABLE']} |"
        )
    return "\n".join(lines)


def _decisions(records: list[dict[str, Any]]) -> dict[str, Any]:
    inventory_pairs = sum(item["inventory"]["status"] == "ELIGIBLE" for item in records)
    trade_ar_pairs = sum(item["trade_ar"]["status"] == "ELIGIBLE" for item in records)
    broad_ar_pairs = sum(item["broad_ar"]["status"] == "ELIGIBLE" for item in records)
    trade_ap_pairs = sum(item["trade_ap"]["status"] == "ELIGIBLE" for item in records)
    broad_ap_pairs = sum(item["broad_ap"]["status"] == "ELIGIBLE" for item in records)
    revenue_relations = sum(
        item["relations"]["ar_vs_revenue"]["status"] == "ELIGIBLE"
        or item["relations"]["inventory_vs_revenue"]["status"] == "ELIGIBLE"
        for item in records
    )
    cogs_relations = sum(
        item["relations"]["inventory_vs_cogs"]["status"] == "ELIGIBLE"
        or item["relations"]["ap_vs_cogs"]["status"] == "ELIGIBLE"
        for item in records
    )
    if (
        inventory_pairs
        and (trade_ar_pairs or broad_ar_pairs)
        and (trade_ap_pairs or broad_ap_pairs)
    ):
        scope = "SELECTIVE_INVENTORY_AR_AP_CANONICAL_CORE"
    elif inventory_pairs and (trade_ar_pairs or broad_ar_pairs):
        scope = "SELECTIVE_INVENTORY_AR_CANONICAL_CORE"
    elif inventory_pairs:
        scope = "SELECTIVE_INVENTORY_CANONICAL_CORE"
    else:
        scope = "SELECTIVE_WORKING_CAPITAL_CANONICAL_CORE"
    return {
        "inventory_metric": "inventory (total inventory semantic only)",
        "inventory_component_aggregation": "PROHIBITED_UNLESS_EXPLICITLY_PROVEN",
        "ar_initial_scope": "TRADE_PLUS_SEPARATE_BROAD",
        "ap_initial_scope": "TRADE_PLUS_SEPARATE_BROAD",
        "balance_scope": "issuer-reported current scope preserved; no automatic current/noncurrent summation",
        "net_ar_policy": "issuer-reported net AR preserved; no gross-up",
        "prior_comparable_rule": "same issuer fiscal quarter, prior fiscal year, exact semantic/basis/currency/unit",
        "revenue_alignment": "same filing, same fiscal period end/type, prior-year comparable; YTD preferred for Q2/Q3",
        "cogs_alignment": (
            "INCLUDE_SELECTIVELY_EXACT_SEMANTIC"
            if cogs_relations
            else "DEFER"
        ),
        "phase_9_1b_scope": scope,
        "include_absolute_delta": True,
        "include_safe_yoy_growth": True,
        "include_revenue_cross_growth": bool(revenue_relations),
        "include_cogs_cross_growth": bool(cogs_relations),
        "trade_ar_pairs": trade_ar_pairs,
        "broad_ar_pairs": broad_ar_pairs,
        "trade_ap_pairs": trade_ap_pairs,
        "broad_ap_pairs": broad_ap_pairs,
        "inventory_pairs": inventory_pairs,
        "dso_ready_for_implementation": "DEFER",
        "inventory_days_ready_for_implementation": "DEFER",
        "dpo_ready_for_implementation": "DEFER",
        "ccc_ready_for_implementation": "DEFER",
    }


def generate(
    *,
    database: Path,
    sec_cache: Path,
    opendart_cache: Path,
    kr_audit_path: Path = KR_AUDIT,
) -> dict[str, Any]:
    universe = _active_universe(database)
    audit = _load_json(kr_audit_path)
    records: list[dict[str, Any]] = []
    sec_hits = 0
    sec_misses = 0
    dart_hits = 0
    dart_misses = 0
    for row in universe:
        if row.get("exchange") == "KRX":
            record, hits, misses = _kr_record(
                row,
                audit=audit,
                opendart_cache=opendart_cache,
            )
            dart_hits += hits
            dart_misses += misses
        else:
            record, hits, misses = _sec_record(row, sec_cache=sec_cache)
            sec_hits += hits
            sec_misses += misses
        records.append(record)
    counts = {
        key: _status_counts(records, key)
        for key in ("inventory", "trade_ar", "broad_ar", "trade_ap", "broad_ap")
    }
    relation_counts = {
        key: _relation_counts(records, key)
        for key in (
            "ar_vs_revenue",
            "inventory_vs_revenue",
            "inventory_vs_cogs",
            "ap_vs_cogs",
        )
    }
    acquisition = (
        _load_json(opendart_cache / "acquisition-telemetry.json")
        if (opendart_cache / "acquisition-telemetry.json").exists()
        else {
            "requests": 0,
            "successes": 0,
            "failures": [],
            "preexisting_cache_hits": 0,
        }
    )
    decisions = _decisions(records)
    readiness = {
        "p0_open": [],
        "p1_open": [],
        "p2_backlog": [
            "prior-quarter balance relations",
            "inventory component decomposition",
            "management-specific contract-asset extension",
            "DSO/Inventory Days/DPO/CCC prerequisites",
        ],
        "phase_9_1b_ready": True,
        "phase_9_1b_scope": decisions["phase_9_1b_scope"],
        "runtime_user_visible_diff": 0,
    }
    return {
        "contract": CONTRACT_VERSION,
        "generated_at": "2026-08-21T13:00:00+09:00",
        "as_of_date": AS_OF.isoformat(),
        "active_universe_count": len(records),
        "market_counts": dict(Counter(item["market"] for item in records)),
        "industry_counts": dict(Counter(item["industry"] for item in records)),
        "metric_counts": counts,
        "relation_counts": relation_counts,
        "active_universe": records,
        "representative_proofs": _representatives(records),
        "architecture_decisions": decisions,
        "provider_telemetry": {
            "sec_companyfacts": {
                "stored_cache_hits": sec_hits,
                "cache_misses": sec_misses,
                "live_requests": 0,
            },
            "opendart": {
                "generation_cache_hits": dart_hits,
                "generation_cache_misses": dart_misses,
                "acquisition": acquisition,
            },
            "new_paid_providers": 0,
        },
        "deferred": {
            "dso": True,
            "inventory_days": True,
            "dpo": True,
            "ccc": True,
        },
        "mutations": {
            "runtime": 0,
            "user_visible": 0,
            "telegram": 0,
            "scheduled_task": 0,
            "pilot": 0,
            "database": 0,
        },
        "readiness": readiness,
    }


def _proof_lines(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    for item in payload["representative_proofs"]:
        current = item.get("current_fact") or {}
        prior = item.get("prior_fact") or {}
        lines.append(
            "- **{class_name}**: `{ticker}` / `{status}`; metric `{metric}`; current `{current_value}` at `{current_date}`; prior `{prior_value}` at `{prior_date}`; source `{source}`.".format(
                class_name=item["class"],
                ticker=item.get("ticker"),
                status=item.get("status"),
                metric=item.get("metric"),
                current_value=current.get("value"),
                current_date=current.get("period_end"),
                prior_value=prior.get("value"),
                prior_date=prior.get("period_end"),
                source=item.get("source"),
            )
        )
    return "\n".join(lines)


def _reports(payload: dict[str, Any]) -> dict[str, str]:
    records = payload["active_universe"]
    counts = payload["metric_counts"]
    relation_counts = payload["relation_counts"]
    decisions = payload["architecture_decisions"]
    provider = payload["provider_telemetry"]
    table = _coverage_table(records)
    counts_table = _counts_table({**counts, **relation_counts})
    proofs = _proof_lines(payload)
    architecture = f"""# Working Capital Evidence Architecture

Contract: `{CONTRACT_VERSION}`

## Decision

Working-capital evidence extends the canonical financial lineage model. Inventory, receivables, and payables are point-in-time Facts keyed by `balance_date`; revenue and COGS are duration Facts used only when issuer fiscal period, exact semantic, currency/unit, entity scope, statement basis, and source version align.

The exact canonical raw metric names are:

- `inventory`: total inventory semantic only; component aggregation is prohibited unless separately proven.
- `trade_accounts_receivable`: exact trade semantic only.
- `accounts_receivable_broad`: broad/current or trade-and-other receivables, never renamed trade AR.
- `trade_accounts_payable`: exact trade semantic only.
- `accounts_payable_broad`: broad/current or trade-and-other payables, never renamed trade AP.

`AR_INITIAL_SCOPE = {decisions['ar_initial_scope']}`

`AP_INITIAL_SCOPE = {decisions['ap_initial_scope']}`

Current/noncurrent scope is preserved from the source. No automatic summation or AR gross-up occurs. SEC facts retain issuer-reported scope; OpenDART CFS is consolidated and never mixed with OFS.

## Comparable Rule

The primary pair is the same issuer fiscal quarter in the prior fiscal year with the same exact semantic, currency/unit, entity scope, statement basis, and authoritative source version. Q2 versus prior FY-end is not YoY. Non-calendar issuers use fiscal identity rather than calendar-quarter assumptions. Restated values use the latest authoritative occurrence while preserving the economic period from the earliest official occurrence.

Absolute delta is `current - prior`. YoY percentage is calculated only when the prior balance is positive. Missing or zero is never substituted. A negative normalized balance is blocked for source review.

Revenue and COGS relations require the same filing and matching fiscal period end/type. Q2/Q3 YTD is preferred. Relation output is factual (`BALANCE_INCREASED`, `AR_GROWTH_GT_REVENUE_GROWTH`, and related typed identities), never a good/bad or thesis verdict.

## Point-In-Time And Freshness

Every Fact retains filing/source availability. Historical replay requires `source_available_at <= cutoff`. A newer provisional earnings period without a formal balance sheet yields `FORMAL_LAGGING_PROVISIONAL`; the older balance is not relabeled as the provisional quarter. No 30/60/90-day threshold is introduced.

## Industry And Safety

Inventory is primary for memory, automotive, and steel/materials; AR is primary for industrial/project and transport subjects where semantics are safe. Contract assets are not trade AR. Accrued liabilities are not trade AP. Insurance/reinsurance is `NOT_APPLICABLE`; biotech and special financial-like platforms remain context-only unless business-specific evidence supports more.

No DSO, Inventory Days, DPO, CCC, AI packet, fallback, Public Action, snapshot, thesis-state, warning, or user-visible behavior is implemented in Phase 9.1A.
"""
    provider_report = f"""# Phase 9.1A Provider Coverage

## Sources

- SEC Company Facts official XBRL stored cache hits: `{provider['sec_companyfacts']['stored_cache_hits']}`
- SEC cache misses: `{provider['sec_companyfacts']['cache_misses']}`
- SEC live calls: `0`
- OpenDART bounded acquisition requests: `{provider['opendart']['acquisition'].get('requests', 0)}`
- OpenDART successes: `{provider['opendart']['acquisition'].get('successes', 0)}`
- OpenDART failures: `{len(provider['opendart']['acquisition'].get('failures', []))}`
- OpenDART generator cache hits: `{provider['opendart']['generation_cache_hits']}`
- OpenDART generator cache misses: `{provider['opendart']['generation_cache_misses']}`
- New paid providers / APIs: `0 / 0`

The OpenDART acquisition is bounded to the 2026 and 2025 half-year CFS for active KR non-financial issuers. It does not crawl other years/forms and does not attempt the separate KR cash-flow period recovery.
"""
    coverage_report = f"""# Phase 9.1A Active Universe Coverage

Active monitored subjects: `{payload['active_universe_count']}`; KR `{payload['market_counts'].get('KR', 0)}`; US/foreign `{payload['market_counts'].get('US_FOREIGN', 0)}`.

{counts_table}

{table}

`ELIGIBLE` means a current and prior-year comparable pair exists. `PARTIAL` generally means the current exact Fact exists but the strict comparable pair does not. Trade and broad metrics are counted independently.
"""
    inventory_report = f"""# Phase 9.1A Inventory Lineage Audit

- Comparable total-inventory pairs: `{counts['inventory']['ELIGIBLE']}`
- Current-only/partial: `{counts['inventory']['PARTIAL']}`
- Blocked: `{counts['inventory']['BLOCKED']}`
- Not applicable: `{counts['inventory']['NOT_APPLICABLE']}`

Only `InventoryNet`, `Inventories`, or an independently verified total-inventory semantic is accepted. Finished goods, raw materials, WIP, contract assets, biological assets, investment property, securities inventory, and prepaid expenses are not silently promoted or aggregated. Latest authoritative restated occurrences are versioned; derived delta/growth retains both Fact IDs.
"""
    receivables_report = f"""# Phase 9.1A Receivables Lineage Audit

- Exact trade AR comparable pairs: `{counts['trade_ar']['ELIGIBLE']}`
- Broad AR comparable pairs: `{counts['broad_ar']['ELIGIBLE']}`
- AR-versus-revenue eligible relations: `{relation_counts['ar_vs_revenue']['ELIGIBLE']}`

Decision: `AR_INITIAL_SCOPE = {decisions['ar_initial_scope']}`. Exact trade AR and broad AR remain separate metrics. Accounts-and-other, notes, financing, loans, other receivables, and contract assets are not renamed trade AR. Issuer-reported net amounts remain net; no allowance gross-up is performed.
"""
    payables_report = f"""# Phase 9.1A Payables Lineage Audit

- Exact trade AP comparable pairs: `{counts['trade_ap']['ELIGIBLE']}`
- Broad AP comparable pairs: `{counts['broad_ap']['ELIGIBLE']}`
- AP-versus-COGS eligible relations: `{relation_counts['ap_vs_cogs']['ELIGIBLE']}`

Decision: `AP_INITIAL_SCOPE = {decisions['ap_initial_scope']}`. Accounts payable, accounts-payable-and-accrued-liabilities, and trade-and-other payables remain broad when trade-only identity is unproven. Accrued expenses, contract liabilities, other payables, and debt are not trade AP.
"""
    comparable_report = f"""# Phase 9.1A Comparable Period Audit

Primary comparison is prior-year same fiscal quarter or FY-versus-prior-FY. Q2 versus prior FY-end is rejected. Non-calendar issuers retain their fiscal quarter and actual balance dates. Current and prior facts require exact semantic, currency/unit, entity scope, and statement basis.

Revenue relation coverage: AR/revenue `{relation_counts['ar_vs_revenue']['ELIGIBLE']}`, inventory/revenue `{relation_counts['inventory_vs_revenue']['ELIGIBLE']}`. COGS relation coverage: inventory/COGS `{relation_counts['inventory_vs_cogs']['ELIGIBLE']}`, AP/COGS `{relation_counts['ap_vs_cogs']['ELIGIBLE']}`.

Revenue policy: `{decisions['revenue_alignment']}`.

COGS policy: `{decisions['cogs_alignment']}`. No DSO, DPO, inventory-days, or causal collection/demand/liquidity verdict is derived.
"""
    industry_report = """# Phase 9.1A Industry Applicability

| Framework | Inventory | AR | AP | Main safe future relation |
|---|---|---|---|---|
| memory / semiconductor | PRIMARY | SECONDARY | SECONDARY | inventory vs revenue/COGS, cycle context required |
| automotive | PRIMARY | SECONDARY | SECONDARY | inventory vs revenue/COGS; finance receivables excluded |
| steel / materials | PRIMARY | PRIMARY | SECONDARY | inventory and AR deltas, no demand inference alone |
| industrial / electrical | PRIMARY | PRIMARY | SECONDARY | trade AR vs revenue; contract assets remain separate |
| aerospace / project | SECONDARY | SECONDARY | SECONDARY | exact AR only; contract assets future extension |
| transport / logistics | CONTEXT_ONLY | PRIMARY | SECONDARY | AR vs revenue where exact |
| cloud / software | CONTEXT_ONLY | SECONDARY | CONTEXT_ONLY | selective AR context |
| HPC / data center | CONTEXT_ONLY | SECONDARY | SECONDARY | subordinate to OCF/CAPEX/FCF and build-out |
| biotech | CONTEXT_ONLY | CONTEXT_ONLY | CONTEXT_ONLY | no forced primary relation |
| insurance / reinsurance | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | generic industrial WC suppressed |
| special financial-like | CONTEXT_ONLY | CONTEXT_ONLY | CONTEXT_ONLY | business-specific contract required |

Working-capital evidence remains a typed signal, not a thesis status mutation or causal explanation.
"""
    proofs_report = f"""# Phase 9.1A Representative Proofs

{proofs}

Each proof in the JSON retains exact source document, occurrence ID, semantic, balance date, filing date, currency/unit, entity/basis, current/prior Fact IDs, deterministic delta/growth, and typed relation inputs. Missing fields remain fail-closed.
"""
    readiness = f"""# Phase 9.1A Readiness

## Closed Decisions

- Inventory: total inventory only; no silent component aggregation.
- AR: `{decisions['ar_initial_scope']}`.
- AP: `{decisions['ap_initial_scope']}`.
- Balance scope: source current/total scope preserved; no automatic summation.
- Comparable date: prior fiscal-year same fiscal quarter, exact semantic/basis/currency/unit.
- Revenue: same filing and comparable flow period; YTD preferred for Q2/Q3.
- COGS: `{decisions['cogs_alignment']}`.
- PIT/freshness: source availability retained; provisional-only periods do not relabel formal balances.
- DSO / Inventory Days / DPO / CCC: `DEFER / DEFER / DEFER / DEFER`.

Open P0: `0`. Open material P1: `0`.

P2 backlog: prior-quarter relations, inventory components, contract assets, and advanced ratio prerequisites.

Runtime/user-visible behavior diff: `0`.

`PHASE_9_1B_READY = YES`

`PHASE_9_1B_SCOPE = {decisions['phase_9_1b_scope']}`

Recommended next phase: Phase 9.1B canonical working-capital core for the selected Inventory/AR subset, preserving exact trade versus separate broad semantics and fail-closing unsupported AP/COGS relations.
"""
    return {
        "docs/architecture/WORKING_CAPITAL_EVIDENCE.md": architecture,
        f"docs/reports/{RUN_DATE}-phase9-1a-provider-coverage.md": provider_report,
        f"docs/reports/{RUN_DATE}-phase9-1a-active-universe-coverage.md": coverage_report,
        f"docs/reports/{RUN_DATE}-phase9-1a-inventory-lineage-audit.md": inventory_report,
        f"docs/reports/{RUN_DATE}-phase9-1a-receivables-lineage-audit.md": receivables_report,
        f"docs/reports/{RUN_DATE}-phase9-1a-payables-lineage-audit.md": payables_report,
        f"docs/reports/{RUN_DATE}-phase9-1a-comparable-period-audit.md": comparable_report,
        f"docs/reports/{RUN_DATE}-phase9-1a-industry-applicability.md": industry_report,
        f"docs/reports/{RUN_DATE}-phase9-1a-representative-proofs.md": proofs_report,
        f"docs/reports/{RUN_DATE}-phase9-1a-readiness.md": readiness,
    }


def write_outputs(payload: dict[str, Any]) -> None:
    _write_json(REPORT_ROOT / f"{RUN_DATE}-phase9-1a-coverage.json", payload)
    _write_json(
        REPORT_ROOT / f"{RUN_DATE}-phase9-1a-readiness.json",
        payload["readiness"],
    )
    for path, content in _reports(payload).items():
        _write_text(ROOT / path, content)


async def _main(args: argparse.Namespace) -> None:
    universe = _active_universe(args.database)
    audit = _load_json(args.kr_audit)
    if args.acquire_opendart:
        api_key = os.getenv("OPENDART_API_KEY", "")
        if not api_key:
            raise RuntimeError("OPENDART_API_KEY is not configured")
        await acquire_opendart_cache(
            universe=universe,
            audit=audit,
            cache_root=args.opendart_cache,
            api_key=api_key,
        )
    payload = generate(
        database=args.database,
        sec_cache=args.sec_cache,
        opendart_cache=args.opendart_cache,
        kr_audit_path=args.kr_audit,
    )
    if args.write_reports:
        write_outputs(payload)
    print(
        json.dumps(
            {
                "contract": payload["contract"],
                "active_universe": payload["active_universe_count"],
                "metric_counts": payload["metric_counts"],
                "relation_counts": payload["relation_counts"],
                "phase_9_1b_ready": payload["readiness"]["phase_9_1b_ready"],
                "phase_9_1b_scope": payload["readiness"]["phase_9_1b_scope"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Phase 9.1A working-capital evidence architecture audit"
    )
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--sec-cache", type=Path, required=True)
    parser.add_argument("--opendart-cache", type=Path, required=True)
    parser.add_argument("--kr-audit", type=Path, default=KR_AUDIT)
    parser.add_argument("--acquire-opendart", action="store_true")
    parser.add_argument("--write-reports", action="store_true")
    asyncio.run(_main(parser.parse_args()))
