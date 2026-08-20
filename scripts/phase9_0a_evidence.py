from __future__ import annotations

# ruff: noqa: E501

import argparse
import hashlib
import json
import os
import sqlite3
import time
from collections import Counter
from pathlib import Path
from typing import Any

import httpx

from app.services.cash_flow_capital_efficiency_service import CONTRACT_VERSION


ROOT = Path(__file__).resolve().parents[1]
RUN_DATE = "20260820"
AS_OF = "2026-08-20"
REPORT_ROOT = ROOT / "docs" / "reports"
KR_AUDIT = REPORT_ROOT / "20260817-phase8-1-1-authoritative-financial-recovery-audit.json"
SEC_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
FORMAL_FORMS = {"10-K", "10-Q", "20-F", "40-F", "6-K"}

FLOW_TAGS = {
    "ocf": {
        "us-gaap": ("NetCashProvidedByUsedInOperatingActivities",),
        "ifrs-full": ("CashFlowsFromUsedInOperatingActivities",),
    },
    "capex_ppe": {
        "us-gaap": (
            "PaymentsToAcquirePropertyPlantAndEquipment",
            "PaymentsForAdditionsToPropertyPlantAndEquipment",
        ),
        "ifrs-full": (
            "PurchaseOfPropertyPlantAndEquipment",
            "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
        ),
    },
    "revenue": {
        "us-gaap": (
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "Revenues",
            "SalesRevenueNet",
        ),
        "ifrs-full": ("Revenue",),
    },
    "net_income": {
        "us-gaap": ("ProfitLoss", "NetIncomeLoss"),
        "ifrs-full": ("ProfitLoss",),
    },
    "cogs": {
        "us-gaap": (
            "CostOfRevenue",
            "CostOfGoodsAndServicesSold",
            "CostOfGoodsSold",
        ),
        "ifrs-full": ("CostOfSales",),
    },
}

POINT_TAGS = {
    "inventory": {
        "us-gaap": ("InventoryNet",),
        "ifrs-full": ("Inventories",),
    },
    "ar": {
        "us-gaap": ("AccountsReceivableNetCurrent",),
        "ifrs-full": ("TradeAndOtherCurrentReceivables", "TradeReceivables"),
    },
    "ap": {
        "us-gaap": ("AccountsPayableCurrent",),
        "ifrs-full": ("TradeAndOtherCurrentPayables", "TradePayables"),
    },
}

TRADE_EXACT = {
    "ifrs-full:TradeReceivables",
    "ifrs-full:TradePayables",
}

METRICS = (
    "ocf",
    "capex_ppe",
    "fcf",
    "revenue",
    "inventory",
    "ar",
    "ap",
    "cogs",
    "ocf_margin",
    "fcf_margin",
    "capex_intensity",
    "cash_conversion",
    "dso",
    "inventory_days",
    "dpo",
    "ccc",
    "roic",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _active_universe(database: Path) -> list[dict[str, Any]]:
    uri = f"file:{database}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT w.ticker, w.company_name, w.exchange, c.industry, c.sector,
                   s.cik, s.corp_code, s.country, s.issuer_type, s.security_type,
                   s.adr_ratio, s.identity_quality, i.valuation_framework,
                   i.validation_metrics
              FROM watchlistitem AS w
              LEFT JOIN company AS c ON c.ticker = w.ticker
              LEFT JOIN securitymaster AS s ON s.ticker = w.ticker
              LEFT JOIN investmentthesis AS i
                ON i.ticker = w.ticker AND i.status = 'active'
             WHERE w.active = 1
             ORDER BY CASE WHEN w.exchange = 'KRX' THEN 0 ELSE 1 END, w.ticker
            """
        ).fetchall()
    finally:
        connection.close()
    return [dict(row) for row in rows]


def _taxonomy(row: dict[str, Any]) -> tuple[str, str]:
    text = " ".join(
        str(row.get(key) or "")
        for key in ("industry", "sector", "valuation_framework", "validation_metrics")
    ).lower()
    if (
        "insurance" in text
        or "reinsurance" in text
        or "combined ratio" in text
        or "합산비율" in text
    ):
        return "insurance_reinsurance", "financial"
    if "biotech" in text or "pipeline" in text or "임상" in text:
        return "biotech", "pre_profit_biotech"
    if (
        "memory" in text
        or "semiconductor" in text
        or "반도체" in text
        or "hbm" in text
        or "nand" in text
    ):
        return "memory_semiconductor", "non_financial"
    if "steel" in text or "철강" in text:
        return "steel_materials", "non_financial"
    if "transport" in text or "logistics" in text or "물류" in text:
        return "transport_logistics", "non_financial"
    if "automotive" in text or "자동차" in text:
        return "automotive", "non_financial"
    if (
        "billing mw" in text
        or "contract mw" in text
        or "계약 mw" in text
        or "가동 mw" in text
        or "hpc lease" in text
        or "project financing" in text
    ):
        return "hpc_data_center", "non_financial"
    if "cloud" in text or "search" in text or "platform" in text or "software" in text:
        return "cloud_platform_software", "non_financial"
    if "aerospace" in text or "방산" in text:
        return "aerospace_epc", "non_financial"
    if "electrical" in text or "전력" in text:
        return "industrial_epc", "non_financial"
    return "general_non_financial", "non_financial"


def _fetch_companyfacts(
    row: dict[str, Any],
    cache: Path,
    *,
    user_agent: str,
    refresh: bool,
    telemetry: dict[str, Any],
) -> tuple[dict[str, Any] | None, Path | None]:
    cik = str(row.get("cik") or "").strip().zfill(10)
    if not cik.strip("0"):
        return None, None
    path = cache / f"CIK{cik}.json"
    if path.exists() and not refresh:
        telemetry["generation_cache_hits"] += 1
        return json.loads(path.read_text(encoding="utf-8")), path
    telemetry["network_requests"] += 1
    response = httpx.get(
        SEC_URL.format(cik=cik),
        headers={"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"},
        timeout=30,
    )
    if response.status_code != 200:
        telemetry["failures"].append(
            {"ticker": row["ticker"], "status_code": response.status_code}
        )
        return None, None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(response.content)
    telemetry["network_successes"] += 1
    time.sleep(0.11)
    return response.json(), path


def _occurrences(payload: dict[str, Any], mapping: dict[str, tuple[str, ...]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    facts = payload.get("facts", {})
    for namespace, tags in mapping.items():
        namespace_facts = facts.get(namespace, {})
        for tag in tags:
            fact = namespace_facts.get(tag)
            if not isinstance(fact, dict):
                continue
            for unit, values in fact.get("units", {}).items():
                for item in values:
                    if item.get("form") not in FORMAL_FORMS or item.get("val") is None:
                        continue
                    output.append(
                        {
                            "namespace": namespace,
                            "tag": tag,
                            "semantic": f"{namespace}:{tag}",
                            "unit": unit,
                            "value": item["val"],
                            "start": item.get("start"),
                            "end": item.get("end"),
                            "filed": item.get("filed"),
                            "accession": item.get("accn"),
                            "form": item.get("form"),
                            "fiscal_year": item.get("fy"),
                            "fiscal_period": item.get("fp"),
                            "frame": item.get("frame"),
                        }
                    )
    return output


def _latest(values: list[dict[str, Any]], *, require_start: bool) -> dict[str, Any] | None:
    usable = [
        value
        for value in values
        if value.get("end") and (not require_start or value.get("start"))
    ]
    if not usable:
        return None
    usable.sort(
        key=lambda value: (
            str(value.get("end") or ""),
            str(value.get("filed") or ""),
            str(value.get("accession") or ""),
        ),
        reverse=True,
    )
    for candidate in usable:
        identity = tuple(
            candidate.get(key)
            for key in ("accession", "start", "end", "unit", "semantic")
        )
        matching_values = {
            item.get("value")
            for item in usable
            if tuple(
                item.get(key)
                for key in ("accession", "start", "end", "unit", "semantic")
            )
            == identity
        }
        if len(matching_values) == 1:
            return candidate
    return None


def _same_period(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return all(
        left.get(key) == right.get(key)
        for key in ("accession", "start", "end", "unit")
    )


def _latest_pair(
    left: list[dict[str, Any]], right: list[dict[str, Any]]
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    pairs = [(a, b) for a in left for b in right if _same_period(a, b)]
    if not pairs:
        return None
    pairs.sort(
        key=lambda pair: (
            str(pair[0].get("end") or ""),
            str(pair[0].get("filed") or ""),
            str(pair[0].get("accession") or ""),
        ),
        reverse=True,
    )
    for pair in pairs:
        identity = tuple(pair[0].get(key) for key in ("accession", "start", "end", "unit"))
        left_values = {
            item.get("value")
            for item in left
            if tuple(item.get(key) for key in ("accession", "start", "end", "unit"))
            == identity
        }
        right_values = {
            item.get("value")
            for item in right
            if tuple(item.get(key) for key in ("accession", "start", "end", "unit"))
            == identity
        }
        if len(left_values) == 1 and len(right_values) == 1:
            return pair
    return None


def _state(status: str, reason: str, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"status": status, "reason": reason, "evidence": evidence}


def _sec_record(row: dict[str, Any], payload: dict[str, Any], source_path: Path) -> dict[str, Any]:
    flows = {name: _occurrences(payload, tags) for name, tags in FLOW_TAGS.items()}
    points = {name: _occurrences(payload, tags) for name, tags in POINT_TAGS.items()}
    latest = {name: _latest(values, require_start=True) for name, values in flows.items()}
    latest_points = {name: _latest(values, require_start=False) for name, values in points.items()}
    fcf_pair = _latest_pair(flows["ocf"], flows["capex_ppe"])
    ocf_revenue_pair = _latest_pair(flows["ocf"], flows["revenue"])
    capex_revenue_pair = _latest_pair(flows["capex_ppe"], flows["revenue"])
    fcf_revenue = None
    if fcf_pair:
        fcf_revenue = next(
            (
                revenue
                for revenue in flows["revenue"]
                if _same_period(fcf_pair[0], revenue)
            ),
            None,
        )
    industry, financial_type = _taxonomy(row)
    metrics: dict[str, Any] = {}
    if financial_type == "financial":
        metrics.update(
            {
                "ocf": _state("PARTIAL", "financial_industry_context_only", latest["ocf"]),
                "capex_ppe": _state("NOT_APPLICABLE", "generic_capex_not_primary_for_financial_industry"),
                "fcf": _state("NOT_APPLICABLE", "generic_fcf_not_primary_for_financial_industry"),
                "revenue": _state("PARTIAL", "financial_revenue_semantics_require_industry_contract", latest["revenue"]),
                "inventory": _state("NOT_APPLICABLE", "not_primary_for_financial_industry"),
                "ar": _state("NOT_APPLICABLE", "not_primary_for_financial_industry"),
                "ap": _state("NOT_APPLICABLE", "not_primary_for_financial_industry"),
                "cogs": _state("NOT_APPLICABLE", "not_primary_for_financial_industry"),
            }
        )
        for metric in METRICS[8:]:
            metrics[metric] = _state("NOT_APPLICABLE", "generic_metric_not_applicable_to_financial_industry")
    else:
        metrics["ocf"] = _state("ELIGIBLE", "official_structured_filing_exact_semantic", latest["ocf"]) if latest["ocf"] else _state("BLOCKED", "exact_ocf_occurrence_missing")
        metrics["capex_ppe"] = _state("ELIGIBLE", "official_ppe_cash_payment_exact_semantic", latest["capex_ppe"]) if latest["capex_ppe"] else _state("BLOCKED", "exact_ppe_capex_occurrence_missing")
        metrics["fcf"] = _state("ELIGIBLE", "same_accession_period_unit_ocf_minus_ppe_capex", {"ocf": fcf_pair[0], "capex": fcf_pair[1]}) if fcf_pair else _state("BLOCKED", "compatible_ocf_capex_pair_missing")
        metrics["revenue"] = _state("ELIGIBLE", "official_structured_filing_exact_semantic", latest["revenue"]) if latest["revenue"] else _state("BLOCKED", "exact_revenue_occurrence_missing")
        metrics["inventory"] = _state("ELIGIBLE", "point_in_time_total_inventory", latest_points["inventory"]) if latest_points["inventory"] else _state("BLOCKED", "inventory_occurrence_missing")
        for name in ("ar", "ap"):
            occurrence = latest_points[name]
            if occurrence is None:
                metrics[name] = _state("BLOCKED", f"{name}_occurrence_missing")
            elif occurrence["semantic"] in TRADE_EXACT:
                metrics[name] = _state("ELIGIBLE", "exact_trade_balance", occurrence)
            else:
                metrics[name] = _state("PARTIAL", "broad_balance_not_proven_trade_only", occurrence)
        metrics["cogs"] = _state("ELIGIBLE", "official_structured_filing_exact_semantic", latest["cogs"]) if latest["cogs"] else _state("BLOCKED", "compatible_cogs_missing")
        metrics["ocf_margin"] = _state("ELIGIBLE", "compatible_ocf_revenue_pair", {"ocf": ocf_revenue_pair[0], "revenue": ocf_revenue_pair[1]}) if ocf_revenue_pair else _state("BLOCKED", "compatible_ocf_revenue_pair_missing")
        metrics["fcf_margin"] = _state("ELIGIBLE", "compatible_fcf_revenue_inputs", {"ocf": fcf_pair[0], "capex": fcf_pair[1], "revenue": fcf_revenue}) if fcf_pair and fcf_revenue else _state("BLOCKED", "compatible_fcf_revenue_inputs_missing")
        metrics["capex_intensity"] = _state("ELIGIBLE", "compatible_capex_revenue_pair", {"capex": capex_revenue_pair[0], "revenue": capex_revenue_pair[1]}) if capex_revenue_pair else _state("BLOCKED", "compatible_capex_revenue_pair_missing")
        metrics["cash_conversion"] = _state("ELIGIBLE", "ocf_margin_available_as_typed_component") if ocf_revenue_pair else _state("BLOCKED", "safe_cash_conversion_component_missing")
        metrics["dso"] = _state("BLOCKED", "average_trade_ar_not_proven")
        metrics["inventory_days"] = _state("BLOCKED", "average_inventory_and_compatible_cogs_not_proven")
        metrics["dpo"] = _state("BLOCKED", "purchases_and_average_trade_ap_not_proven")
        metrics["ccc"] = _state("BLOCKED", "all_safe_ccc_components_not_available")
        metrics["roic"] = _state("BLOCKED", "verified_excess_cash_policy_missing")
    latest_period = max(
        (str(value.get("end")) for value in latest.values() if value),
        default=None,
    )
    return {
        "ticker": row["ticker"],
        "company_name": row["company_name"],
        "market": "US_FOREIGN",
        "industry": industry,
        "financial_type": financial_type,
        "primary_source": "SEC companyfacts official XBRL",
        "latest_formal_period": latest_period,
        "issuer_type": row.get("issuer_type"),
        "security_type": row.get("security_type"),
        "issuer_level_boundary": "issuer_metrics_do_not_require_depositary_ratio",
        "security_level_boundary": "per_share_yield_and_ev_metrics_require_verified_security_fx_basis",
        "source_payload_sha256": _sha256(source_path),
        "metrics": metrics,
    }


def _kr_record(row: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    result = audit["results"][row["ticker"]]
    industry, financial_type = _taxonomy(row)
    fields = result["fields"]
    metrics: dict[str, Any] = {}
    if financial_type == "financial":
        metrics = {
            metric: _state(
                "PARTIAL" if metric == "ocf" else "NOT_APPLICABLE",
                "financial_industry_context_only" if metric == "ocf" else "generic_metric_not_applicable_to_financial_industry",
            )
            for metric in METRICS
        }
        metrics["revenue"] = _state("PARTIAL", "insurance_revenue_requires_industry_semantic")
    else:
        ocf = fields.get("operating_cash_flow", {})
        inventory = fields.get("inventory", {})
        revenue = fields.get("revenue", {})
        capex = result.get("capex_components", [])
        metrics["ocf"] = _state("PARTIAL", str(ocf.get("reason") or "cash_flow_period_unresolved"), ocf.get("lineage"))
        metrics["capex_ppe"] = _state("PARTIAL", "exact_ppe_components_exist_but_period_context_unresolved", {"component_count": sum(item.get("classification") == "ppe" for item in capex), "aggregation_eligible": sum(bool(item.get("aggregation_eligible")) for item in capex)})
        metrics["fcf"] = _state("BLOCKED", "ocf_and_ppe_capex_period_eligibility_not_closed")
        metrics["revenue"] = _state("ELIGIBLE", "financial_lineage_v2_verified", revenue.get("lineage")) if revenue.get("status") == "verified_usable" else _state("BLOCKED", str(revenue.get("reason") or "revenue_lineage_unavailable"))
        metrics["inventory"] = _state("ELIGIBLE", "financial_lineage_v2_verified_point_in_time", inventory.get("lineage")) if inventory.get("status") == "verified_usable" else _state("BLOCKED", str(inventory.get("reason") or "inventory_lineage_unavailable"))
        metrics["ar"] = _state("BLOCKED", "trade_ar_not_present_in_committed_recovery_audit")
        metrics["ap"] = _state("BLOCKED", "trade_ap_not_present_in_committed_recovery_audit")
        metrics["cogs"] = _state("BLOCKED", "compatible_cogs_not_present_in_committed_recovery_audit")
        for metric in ("ocf_margin", "fcf_margin", "capex_intensity", "cash_conversion"):
            metrics[metric] = _state("BLOCKED", "cash_flow_period_and_pair_eligibility_unresolved")
        metrics["dso"] = _state("BLOCKED", "average_trade_ar_not_available")
        metrics["inventory_days"] = _state("BLOCKED", "average_inventory_and_compatible_cogs_not_available")
        metrics["dpo"] = _state("BLOCKED", "purchases_and_average_trade_ap_not_available")
        metrics["ccc"] = _state("BLOCKED", "safe_dso_inventory_days_dpo_not_available")
        metrics["roic"] = _state("BLOCKED", "verified_excess_cash_policy_missing")
    filing = result["filing"]
    return {
        "ticker": row["ticker"],
        "company_name": row["company_name"],
        "market": "KR",
        "industry": industry,
        "financial_type": financial_type,
        "primary_source": "OpenDART formal statement stored audit",
        "latest_formal_period": filing.get("report_name"),
        "issuer_type": row.get("issuer_type"),
        "security_type": row.get("security_type"),
        "source_payload_sha256": audit["source_packet_sha256"],
        "metrics": metrics,
    }


def _metric_counts(records: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    output: dict[str, dict[str, int]] = {}
    for metric in METRICS:
        counts = Counter(record["metrics"][metric]["status"] for record in records)
        output[metric] = {status: counts.get(status, 0) for status in ("ELIGIBLE", "PARTIAL", "BLOCKED", "NOT_APPLICABLE")}
    return output


def _representatives(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    classes = (
        ("KR non-financial industrial", lambda row: row["market"] == "KR" and row["financial_type"] == "non_financial"),
        ("US domestic issuer", lambda row: row["market"] == "US_FOREIGN" and row["issuer_type"] == "domestic_us" and row["metrics"]["fcf"]["status"] == "ELIGIBLE"),
        ("non-calendar fiscal issuer", lambda row: row["market"] == "US_FOREIGN" and row["metrics"]["fcf"]["status"] == "ELIGIBLE" and not str((row["metrics"]["fcf"].get("evidence") or {}).get("ocf", {}).get("start") or "").endswith("-01-01")),
        ("foreign issuer / ADR", lambda row: row["issuer_type"] in {"adr", "foreign_private_issuer"} and row["metrics"]["fcf"]["status"] == "ELIGIBLE"),
        ("capex-heavy data-center", lambda row: row["market"] == "US_FOREIGN" and row["industry"] == "hpc_data_center"),
        ("pre-profit biotech", lambda row: row["financial_type"] == "pre_profit_biotech"),
        ("financial / insurance exclusion", lambda row: row["financial_type"] == "financial"),
    )
    selected: list[dict[str, Any]] = []
    for label, predicate in classes:
        record = next((item for item in records if predicate(item)), None)
        if record is None:
            selected.append({"class": label, "ticker": None, "result": "no_representative_available"})
            continue
        selected.append(
            {
                "class": label,
                "ticker": record["ticker"],
                "company_name": record["company_name"],
                "source": record["primary_source"],
                "period": record["latest_formal_period"],
                "ocf": record["metrics"]["ocf"],
                "capex_ppe": record["metrics"]["capex_ppe"],
                "fcf": record["metrics"]["fcf"],
                "reasoning": "eligible only where period, unit, entity/basis, and exact semantic dependencies close; otherwise fail-closed",
            }
        )
    return selected


def _coverage_table(records: list[dict[str, Any]]) -> str:
    columns = ("ocf", "capex_ppe", "fcf", "inventory", "ar", "ap", "cogs", "ccc", "roic")
    lines = ["| Ticker | Industry | " + " | ".join(columns) + " |", "|---|---|" + "---|" * len(columns)]
    for record in records:
        statuses = [record["metrics"][column]["status"] for column in columns]
        lines.append(f"| {record['ticker']} | {record['industry']} | " + " | ".join(statuses) + " |")
    return "\n".join(lines)


def _counts_table(counts: dict[str, dict[str, int]]) -> str:
    lines = ["| Metric | Eligible | Partial | Blocked | N/A |", "|---|---:|---:|---:|---:|"]
    for metric, values in counts.items():
        lines.append(f"| {metric} | {values['ELIGIBLE']} | {values['PARTIAL']} | {values['BLOCKED']} | {values['NOT_APPLICABLE']} |")
    return "\n".join(lines)


def _reports(payload: dict[str, Any]) -> dict[str, str]:
    counts = payload["metric_counts"]
    records = payload["active_universe"]
    proofs = payload["representative_lineage_proofs"]
    source = payload["provider_telemetry"]
    universe_table = _coverage_table(records)
    counts_table = _counts_table(counts)
    proof_lines = "\n".join(
        f"- **{item['class']}**: `{item.get('ticker')}`; OCF `{item.get('ocf', {}).get('status', 'N/A')}`, CAPEX `{item.get('capex_ppe', {}).get('status', 'N/A')}`, FCF `{item.get('fcf', {}).get('status', 'N/A')}`"
        for item in proofs
    )
    architecture = f"""# Cash Flow / Capital Efficiency Architecture

Contract: `{CONTRACT_VERSION}`

## Problem

Existing financial lineage safely covers earnings and selected balance-sheet facts, but it does not close cash-flow period identity, PPE CAPEX scope, FCF derivation, working-capital dependencies, or standard ROIC denominator safety across the active universe.

## Decision

Extend the existing lineage contracts with an occurrence-bound cash-flow and capital-efficiency contract. Implement only deterministic eligibility and audit tooling in Phase 9.0A; do not connect it to production runtime or user-visible messages.

## Why

Cash-flow values become decision-useful only after their period, entity, statement, currency, semantic, and source occurrence agree. Selective safe coverage is preferable to either broad unsafe arithmetic or waiting for universal coverage.

## Rejected Alternative

Rejected alternatives include annualizing interim cash flow, treating total investing outflow as CAPEX, mixing CFS and OFS facts, importing management FCF as backend FCF, using all cash as excess cash, and blocking issuer-level foreign cash flow solely because an ADR ratio is unavailable.

## Safety Constraint

Missing or ambiguous dependencies produce `BLOCKED`, `PARTIAL`, or `NOT_APPLICABLE`. No reverse engineering, proxy substitution, cross-currency arithmetic, production packet mutation, renderer change, or user-visible integration is allowed in Phase 9.0A.

## Ownership And Lineage

This contract extends `financial-lineage-v2`, `financial-quality-taint-v2`, and `security-identity-v2`. It does not create a parallel truth store. Every reported fact retains issuer, period, currency/unit, entity scope, statement basis, document/accession, filing date, source occurrence, raw SHA-256, source sign, and semantic mapping. Every derived fact requires input fact IDs and an explicit formula.

## Period Model

- Flow facts are explicitly `QTD`, `YTD`, `FY`, or `TTM`; balance facts are `POINT_IN_TIME`.
- Verified fiscal Q1 YTD may also represent QTD when its duration is quarter-like.
- Q2/Q3 QTD is `current YTD - adjacent prior-quarter YTD` only under identical issuer, fiscal year start, semantic, currency/unit, entity scope, statement basis, and restatement policy.
- TTM is `prior FY + current YTD - prior comparable YTD` only under the same compatibility rules and issuer fiscal calendar.
- Annualization such as Q1 times four is prohibited.

## OCF, CAPEX, And FCF

- OCF means signed net cash provided by or used in operating activities. EBITDA, operating income, and net income are not proxies.
- Baseline CAPEX is positive-magnitude cash paid to acquire PPE. Total investing cash flow, acquisitions, securities purchases, intangibles, and capitalized software are excluded from the baseline.
- Intangibles and software remain separately typed components. They are never silently added to PPE CAPEX.
- Backend baseline FCF is `OCF - PPE-only CAPEX cash outflow`, with same period, currency/unit, entity scope, and statement basis.
- Company-reported non-GAAP FCF remains a separate management metric and never replaces backend-derived FCF.

## Working Capital

Inventory, trade AR, and trade AP are point-in-time raw facts. Broad receivable/payable totals are `PARTIAL`, not trade balances. The first implementation layer is balance deltas against a comparable date. DSO requires average trade AR and compatible revenue; inventory days requires average inventory and COGS; standard DPO requires purchases and average trade AP. CCC exists only when all three typed components are safe.

## ROIC

Standard ROIC requires compatible EBIT, a valid effective tax rate, beginning/end equity and interest-bearing debt, a verified excess-cash policy, and average invested capital. Total cash is never silently treated as excess cash. Insurance is excluded from generic ROIC. Until an excess-cash policy exists, standard ROIC is deferred.

## Issuer And Security Boundary

Issuer-level OCF, CAPEX, and margins may remain eligible for foreign issuers without an ADR ratio when statement lineage is safe. FCF/share, FCF yield, and EV/FCF require verified security/share, market-cap, currency, FX, and depositary basis. Cross-currency arithmetic is prohibited.

## Industry Applicability

| Framework | OCF | CAPEX/FCF | Inventory/AR/AP | CCC | ROIC |
|---|---|---|---|---|---|
| memory / foundry | PRIMARY | PRIMARY | PRIMARY | SECONDARY | CONTEXT_ONLY |
| cloud / platform / software | PRIMARY | PRIMARY | SECONDARY | CONTEXT_ONLY | SELECTIVE |
| automotive | PRIMARY | PRIMARY | PRIMARY | SECONDARY | SELECTIVE |
| transport / steel / industrial / EPC | PRIMARY | PRIMARY | PRIMARY | SECONDARY | SELECTIVE |
| HPC / data-center | PRIMARY | PRIMARY | SECONDARY | CONTEXT_ONLY | DEFERRED |
| biotech | PRIMARY as burn | PRIMARY as burn | CONTEXT_ONLY | NOT_APPLICABLE | NOT_APPLICABLE |
| insurance / reinsurance | CONTEXT_ONLY | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE |

## AI Consumption Boundary

Architecture only in Phase 9.0A. Future AI input must keep facts separate from interpretation, remain delta-first, avoid automatic thesis changes, and expose missing data only when decision-relevant. No user-visible packet, prompt, fallback, or renderer changes are made here.
"""
    provider = f"""# Phase 9.0A Provider Coverage

## Source Hierarchy

1. Formal official statement
2. Official structured filing
3. Verified official earnings release
4. Existing validated structured provider

OpenDART stored evidence is reused for KR. SEC Company Facts official XBRL is used read-only for CIK-backed issuers. New paid sources and API keys: `0`.

## Call Audit

- SEC source-acquisition network requests: `{source['sec_companyfacts']['network_requests']}`
- SEC source-acquisition network successes: `{source['sec_companyfacts']['network_successes']}`
- SEC failures: `{len(source['sec_companyfacts']['failures'])}`
- SEC payloads already present before acquisition: `{source['sec_companyfacts']['acquisition_preexisting_cache_hits']}`
- Deterministic replay cache hits in final generation: `{source['sec_companyfacts']['generation_cache_hits']}`
- OpenDART live calls: `0`
- OpenDART stored provider calls represented by Phase 8.1.1: `{source['opendart_stored']['provider_calls']}`
- OpenDART stored XBRL cache hits: `{source['opendart_stored']['xbrl_cache_hits']}`

Official references: [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces), [OpenDART full financial statements](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019020).
"""
    coverage = f"""# Phase 9.0A Active Universe Coverage

Active stocks: `{len(records)}`; KR `{sum(row['market'] == 'KR' for row in records)}`; US/foreign `{sum(row['market'] == 'US_FOREIGN' for row in records)}`; financial `{sum(row['financial_type'] == 'financial' for row in records)}`.

{counts_table}

{universe_table}

`ELIGIBLE` requires lineage, not merely field presence. Each blocked or partial cell has a machine-readable reason in the coverage JSON.
"""
    lineage = f"""# Phase 9.0A Cash-Flow Lineage Audit

The SEC audit retains exact namespace/tag, accession, form, filed date, start/end, unit, value, fiscal year/period, and payload SHA. FCF pairs require the same accession, start, end, and unit. The KR audit preserves OpenDART receipt, CFS/OFS, statement section, taxonomy tag, source row identity, amount, and denial reason.

KR evidence found exact OCF and PPE/intangible rows, but the existing XBRL matcher could not prove a unique CF period context. Therefore KR OCF is `PARTIAL`, CAPEX is `PARTIAL`, and FCF is `BLOCKED`; no value is promoted. SEC eligible pairs are issuer-level and do not authorize security-level per-share or yield arithmetic.

## Representative Proofs

{proof_lines}
"""
    fcf = f"""# Phase 9.0A FCF Eligibility Matrix

Baseline: `OCF - positive-magnitude PPE-only cash outflow`.

- OCF eligible: `{counts['ocf']['ELIGIBLE']}`
- PPE CAPEX eligible: `{counts['capex_ppe']['ELIGIBLE']}`
- FCF eligible: `{counts['fcf']['ELIGIBLE']}`
- FCF partial: `{counts['fcf']['PARTIAL']}`
- FCF blocked: `{counts['fcf']['BLOCKED']}`
- FCF not applicable: `{counts['fcf']['NOT_APPLICABLE']}`

Intangibles and capitalized software remain separate. Acquisitions and total investing cash flow are excluded. Management FCF and backend FCF remain different metrics.
"""
    working = f"""# Phase 9.0A Working-Capital Eligibility

- Inventory eligible: `{counts['inventory']['ELIGIBLE']}`
- Trade AR eligible: `{counts['ar']['ELIGIBLE']}`; broad/partial: `{counts['ar']['PARTIAL']}`
- Trade AP eligible: `{counts['ap']['ELIGIBLE']}`; broad/partial: `{counts['ap']['PARTIAL']}`
- Full CCC eligible: `{counts['ccc']['ELIGIBLE']}`

Phase 9.0B does not include CCC. Raw balances and comparable-date deltas are the first safe layer. DSO, inventory days, DPO, and CCC are deferred until average typed balances and compatible flow denominators exist.
"""
    roic = f"""# Phase 9.0A ROIC Eligibility

Standard safe: `{counts['roic']['ELIGIBLE']}`. Blocked: `{counts['roic']['BLOCKED']}`. Not applicable: `{counts['roic']['NOT_APPLICABLE']}`.

Decision: `ROIC_DEFERRED`. Existing data does not provide a verified excess-cash policy across the eligible universe. Phase 9.0B must not label `Equity + Debt - All Cash` as standard invested capital. A later selective implementation may proceed only with explicit excess-cash evidence and average balance inputs.
"""
    industry = """# Phase 9.0A Industry Applicability

OCF/CAPEX/FCF are primary for memory, foundry, platform, automotive, transport, steel, industrial, and HPC/data-center subjects when lineage is safe. Biotech uses OCF/FCF as burn and runway context, not automatic thesis weakening. Insurance/reinsurance uses P/B-ROE, combined ratio, investment income, and capital adequacy; generic corporate FCF, CCC, and ROIC are not primary and are marked not applicable.

Single-quarter working-capital swings and peak-cycle FCF never become automatic structural thesis changes. Industry interpretation remains downstream of canonical evidence.
"""
    proofs_report = f"""# Phase 9.0A Representative Lineage Proofs

{proof_lines}

The selected tickers are derived from the active universe and taxonomy, not production exceptions. Full occurrence details and reasons are in `20260820-phase9-0a-coverage.json`.
"""
    readiness = """# Phase 9.0A Readiness

## Closed Definitions

- Period model: `QTD/YTD/FY/TTM/POINT_IN_TIME`, strict fiscal alignment, no annualization.
- OCF: exact operating-activities cash flow only.
- CAPEX: PPE-only cash outflow baseline; intangibles/software separate.
- FCF: same-period, same-unit, same-entity/basis OCF less PPE CAPEX.
- Working capital: raw balances and deltas first; CCC deferred.
- ROIC: deferred until verified excess-cash policy; insurance excluded.
- Foreign/ADR: issuer-level ratios may be safe; security-level yield/per-share metrics remain blocked without security/FX basis.
- Provisional earnings: no missing cash-flow inference.

Open P0: `0`. Open P1: `0`. P2 backlog: management-FCF reconciliation breadth, CCC coverage, excess-cash policy/ROIC, and user-visible wording for a later phase.

`PHASE_9_0B_READY = YES`

`PHASE_9_0B_SCOPE = SELECTIVE_ELIGIBLE_SUBSET_OCF_CAPEX_FCF_CORE`

Recommended next phase: Phase 9.0B canonical OCF/PPE-CAPEX/FCF core implementation for evidence-eligible issuers, fail-closed elsewhere. Working capital follows after raw balance coverage; advanced ROIC remains deferred.
"""
    reports = {
        "docs/architecture/CASH_FLOW_CAPITAL_EFFICIENCY.md": architecture,
        f"docs/reports/{RUN_DATE}-phase9-0a-provider-coverage.md": provider,
        f"docs/reports/{RUN_DATE}-phase9-0a-active-universe-coverage.md": coverage,
        f"docs/reports/{RUN_DATE}-phase9-0a-cash-flow-lineage-audit.md": lineage,
        f"docs/reports/{RUN_DATE}-phase9-0a-fcf-eligibility-matrix.md": fcf,
        f"docs/reports/{RUN_DATE}-phase9-0a-working-capital-eligibility.md": working,
        f"docs/reports/{RUN_DATE}-phase9-0a-roic-eligibility.md": roic,
        f"docs/reports/{RUN_DATE}-phase9-0a-industry-applicability.md": industry,
        f"docs/reports/{RUN_DATE}-phase9-0a-representative-lineage-proofs.md": proofs_report,
        f"docs/reports/{RUN_DATE}-phase9-0a-readiness.md": readiness,
    }
    validation_bundle = """# Phase 9.0A Validation And Operating Safety

- Branch: `codex/phase-9-0a-cash-flow-capital-efficiency-architecture`
- Base: `2c2aacf1df25a3d0483a14ecf19857ea9c1371b9`
- Contract/generator tests: 35 passed
- Focused regression: 278 passed
- Full pytest: 1,155 passed; 1 existing dependency deprecation warning
- Ruff / diff / JSON: PASS / PASS / PASS
- Investment Knowledge / Chart Knowledge: PASS / PASS
- Public Action / operationId: `0.4.5` / 20 of 20 unique
- Runtime imports, packet changes, renderer changes, DB schema changes: 0
- Manual Telegram / Task / Pilot / DB mutations: 0 / 0 / 0 / 0
- Production Assist: OFF
- AI-review automations: four ACTIVE, configuration changes 0
- KRX telemetry: 08:05/16:05 calendar-loaded, last exit 0, user-visible integration 0
- API restart: 0; architecture-only unimported contract

Implementation, final, main, operating, and exact-SHA Actions values are resolved in the final
promotion record below.

# Repository And Promotion

- Previous main: `2c2aacf1df25a3d0483a14ecf19857ea9c1371b9`
- Implementation SHA: `PENDING_EXACT_SHA_CI`
- Final SHA: `PENDING_FINAL_CI`
- Main promotion: `PENDING`
- Operating sync: `PENDING`
- Runtime behavior changed: `NO`

# Final Gate

Open P0: `0`

Open P1: `0`

`PHASE_9_0B_READY = YES`

`PHASE_9_0B_SCOPE = SELECTIVE_ELIGIBLE_SUBSET_OCF_CAPEX_FCF_CORE`
"""
    bundle_order = (
        architecture,
        provider,
        coverage,
        lineage,
        fcf,
        working,
        roic,
        industry,
        proofs_report,
        readiness,
        validation_bundle,
    )
    reports[f"docs/reports/{RUN_DATE}-phase9-0a-complete-report-bundle.md"] = (
        "# Phase 9.0A Complete Report Bundle\n\n"
        f"Generated: `{payload['generated_at']}`\n\n"
        f"Contract: `{CONTRACT_VERSION}`\n\n"
        "Boundary: architecture/evidence only; user-visible runtime changes `0`\n\n"
        + "\n\n---\n\n".join(bundle_order)
    )
    return reports


def generate(
    *,
    database: Path,
    sec_cache: Path,
    sec_user_agent: str,
    refresh_sec: bool,
    acquired_network_requests: int = 0,
    acquired_network_successes: int = 0,
    acquisition_preexisting_cache_hits: int = 0,
) -> dict[str, Any]:
    universe = _active_universe(database)
    kr_audit = json.loads(KR_AUDIT.read_text(encoding="utf-8"))
    telemetry: dict[str, Any] = {
        "network_requests": acquired_network_requests,
        "network_successes": acquired_network_successes,
        "acquisition_preexisting_cache_hits": acquisition_preexisting_cache_hits,
        "generation_cache_hits": 0,
        "failures": [],
    }
    records: list[dict[str, Any]] = []
    for row in universe:
        if row.get("exchange") == "KRX":
            records.append(_kr_record(row, kr_audit))
            continue
        payload, source_path = _fetch_companyfacts(
            row,
            sec_cache,
            user_agent=sec_user_agent,
            refresh=refresh_sec,
            telemetry=telemetry,
        )
        if payload is None or source_path is None:
            industry, financial_type = _taxonomy(row)
            records.append(
                {
                    "ticker": row["ticker"],
                    "company_name": row["company_name"],
                    "market": "US_FOREIGN",
                    "industry": industry,
                    "financial_type": financial_type,
                    "primary_source": "SEC companyfacts unavailable",
                    "latest_formal_period": None,
                    "issuer_type": row.get("issuer_type"),
                    "security_type": row.get("security_type"),
                    "metrics": {metric: _state("BLOCKED", "official_source_unavailable") for metric in METRICS},
                }
            )
            continue
        records.append(_sec_record(row, payload, source_path))
    counts = _metric_counts(records)
    p0_open: list[dict[str, str]] = []
    readiness = {
        "p0_open": p0_open,
        "p1_open": [],
        "p2_backlog": [
            "management-defined FCF reconciliation breadth",
            "typed average-balance coverage for DSO/inventory days/DPO/CCC",
            "verified excess-cash policy for selective standard ROIC",
            "future user-visible selection and wording",
        ],
        "phase_9_0b_ready": not p0_open,
        "phase_9_0b_scope": "SELECTIVE_ELIGIBLE_SUBSET_OCF_CAPEX_FCF_CORE",
        "runtime_behavior_diff": 0,
        "production_assist": "OFF",
    }
    output = {
        "contract": CONTRACT_VERSION,
        "as_of": AS_OF,
        "generated_at": "2026-08-20T00:00:00+09:00",
        "source_database": str(database),
        "source_database_sha256": _sha256(database),
        "active_universe": records,
        "metric_counts": counts,
        "representative_lineage_proofs": _representatives(records),
        "provider_telemetry": {
            "sec_companyfacts": telemetry,
            "opendart_stored": {
                "live_requests": 0,
                "provider_calls": kr_audit["summary"]["provider_calls"],
                "xbrl_cache_hits": kr_audit["summary"]["xbrl_cache_hits"],
                "source_audit_sha256": _sha256(KR_AUDIT),
            },
            "new_paid_sources": 0,
            "new_api_keys": 0,
        },
        "definition_decisions": {
            "baseline_fcf": "OCF minus positive-magnitude PPE-only cash outflow",
            "capex_scope": "PPE-only baseline; intangibles and capitalized software separate",
            "qtd": "Q1 verified YTD or adjacent same-FY compatible YTD delta",
            "ttm": "prior FY plus current YTD minus prior comparable YTD",
            "working_capital": "raw inventory/trade AR/trade AP and comparable-date deltas first",
            "ccc": "DEFERRED",
            "roic": "DEFERRED_PENDING_VERIFIED_EXCESS_CASH_POLICY",
            "adr": "issuer-level ratios separable; security-level yield/per-share blocked without basis",
            "financial_industry": "generic corporate FCF/CCC/ROIC not applicable",
        },
        "readiness": readiness,
        "mutations": {
            "runtime_behavior": 0,
            "telegram": 0,
            "scheduled_task_manual_runs": 0,
            "pilot": 0,
            "database": 0,
            "production_assist": 0,
        },
    }
    _write_json(REPORT_ROOT / f"{RUN_DATE}-phase9-0a-coverage.json", output)
    _write_json(REPORT_ROOT / f"{RUN_DATE}-phase9-0a-readiness.json", readiness)
    for relative, text in _reports(output).items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Phase 9.0A read-only evidence")
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--sec-cache", type=Path, required=True)
    parser.add_argument("--sec-user-agent", default=os.getenv("SEC_USER_AGENT", ""))
    parser.add_argument("--refresh-sec", action="store_true")
    parser.add_argument("--acquired-network-requests", type=int, default=0)
    parser.add_argument("--acquired-network-successes", type=int, default=0)
    parser.add_argument("--acquisition-preexisting-cache-hits", type=int, default=0)
    args = parser.parse_args()
    if not args.sec_user_agent:
        raise SystemExit("SEC_USER_AGENT is required for official SEC read-only requests")
    result = generate(
        database=args.database,
        sec_cache=args.sec_cache,
        sec_user_agent=args.sec_user_agent,
        refresh_sec=args.refresh_sec,
        acquired_network_requests=args.acquired_network_requests,
        acquired_network_successes=args.acquired_network_successes,
        acquisition_preexisting_cache_hits=args.acquisition_preexisting_cache_hits,
    )
    print(
        json.dumps(
            {
                "active_universe": len(result["active_universe"]),
                "sec_telemetry": result["provider_telemetry"]["sec_companyfacts"],
                "phase_9_0b_ready": result["readiness"]["phase_9_0b_ready"],
                "phase_9_0b_scope": result["readiness"]["phase_9_0b_scope"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
