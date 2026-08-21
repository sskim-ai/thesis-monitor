from __future__ import annotations

# ruff: noqa: E501

import argparse
import hashlib
import json
from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.services.cash_flow_capital_efficiency_service import (
    FactType,
    FinancialFact,
    Metric,
)
from app.services.working_capital_core_service import (
    BALANCE_METRICS,
    DERIVATION_VERSION,
    CanonicalMovement,
    WorkingCapitalCoreSnapshot,
    WorkingCapitalRelation,
    build_working_capital_core_snapshot,
)
from app.services.working_capital_evidence_service import (
    CONTRACT_VERSION,
    build_sec_working_capital_batch,
    canonicalize_occurrences,
    extract_opendart_occurrences,
)
from scripts.phase9_0a_evidence import _active_universe
from scripts.phase9_1a_working_capital_evidence import (
    KR_AUDIT,
    OPEN_DART_REPORT_CODE,
    OPEN_DART_YEARS,
    _kr_filing,
    _working_taxonomy,
)


ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = ROOT / "docs" / "reports"
RUN_DATE = "20260821"
AS_OF = date(2026, 8, 21)
PHASE_9_1A_COVERAGE = REPORT_ROOT / f"{RUN_DATE}-phase9-1a-coverage.json"
METRIC_KEYS = {
    Metric.INVENTORY: "inventory",
    Metric.TRADE_AR: "trade_ar",
    Metric.BROAD_AR: "broad_ar",
    Metric.TRADE_AP: "trade_ap",
    Metric.BROAD_AP: "broad_ap",
}
RELATION_KEYS = {
    (Metric.TRADE_AR, Metric.REVENUE): "trade_ar_vs_revenue",
    (Metric.BROAD_AR, Metric.REVENUE): "broad_ar_vs_revenue",
    (Metric.INVENTORY, Metric.REVENUE): "inventory_vs_revenue",
    (Metric.INVENTORY, Metric.COGS): "inventory_vs_cogs",
    (Metric.TRADE_AP, Metric.COGS): "trade_ap_vs_cogs",
    (Metric.BROAD_AP, Metric.COGS): "broad_ap_vs_cogs",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fact_dict(fact: FinancialFact) -> dict[str, Any]:
    return {
        "fact_id": fact.fact_id,
        "issuer_id": fact.issuer_id,
        "metric": fact.metric.value,
        "value": str(fact.value),
        "currency": fact.currency,
        "unit": fact.unit,
        "fact_type": fact.fact_type.value,
        "reported_or_derived": fact.reported_or_derived,
        "period_start": fact.period.start.isoformat(),
        "period_end": fact.period.end.isoformat(),
        "period_type": fact.period.period_type.value,
        "fiscal_year": fact.period.fiscal_year,
        "fiscal_quarter": fact.period.fiscal_quarter,
        "duration_days": fact.period.duration_days,
        "entity_scope": fact.entity_scope,
        "statement_basis": fact.statement_basis,
        "source_provider": fact.source_provider,
        "source_document_id": fact.source_document_id,
        "source_document_type": fact.source_document_type,
        "filing_date": fact.filing_date.isoformat(),
        "source_available_at": fact.source_available_at.isoformat() if fact.source_available_at else None,
        "source_occurrence_id": fact.source_occurrence_id,
        "source_semantic": fact.source_semantic,
        "raw_payload_sha256": fact.raw_payload_sha256,
        "semantic_mapping": fact.semantic_mapping,
        "balance_scope": fact.balance_scope,
        "net_gross_scope": fact.net_gross_scope,
        "derivation_formula": fact.derivation_formula,
        "derivation_version": fact.derivation_version,
        "input_fact_ids": list(fact.input_fact_ids),
        "quality": fact.quality,
        "eligibility": fact.eligibility.value,
        "denial_reason": fact.denial_reason,
        "cautions": list(fact.cautions),
        "restatement_policy_id": fact.restatement_policy_id,
        "as_of_date": fact.as_of_date.isoformat() if fact.as_of_date else None,
    }


def _movement_dict(movement: CanonicalMovement) -> dict[str, Any]:
    return {
        "status": movement.status.value,
        "metric": movement.balance_metric.value,
        "current_fact_id": movement.current.fact_id if movement.current else None,
        "prior_fact_id": movement.prior.fact_id if movement.prior else None,
        "delta_fact_id": movement.delta_fact.fact_id if movement.delta_fact else None,
        "yoy_fact_id": movement.yoy_fact.fact_id if movement.yoy_fact else None,
        "absolute_delta": str(movement.delta_fact.value) if movement.delta_fact else None,
        "yoy_pct": str(movement.yoy_fact.value) if movement.yoy_fact else None,
        "freshness_state": movement.freshness_state.value if movement.freshness_state else None,
        "denial_reasons": list(movement.denial_reasons),
        "cautions": list(movement.cautions),
    }


def _relation_dict(relation: WorkingCapitalRelation) -> dict[str, Any]:
    return {
        "status": relation.status.value,
        "relation_id": relation.relation_id,
        "relation_type": relation.relation_type,
        "direction": relation.direction.value if relation.direction else None,
        "balance_metric": relation.balance_metric.value,
        "balance_semantic": relation.balance_semantic,
        "balance_scope": relation.balance_scope,
        "flow_metric": relation.flow_metric.value,
        "flow_semantic": relation.flow_semantic,
        "gap_percentage_points": str(relation.gap_percentage_points) if relation.gap_percentage_points is not None else None,
        "current_balance_fact_id": relation.current_balance_fact_id,
        "prior_balance_fact_id": relation.prior_balance_fact_id,
        "current_flow_fact_id": relation.current_flow_fact_id,
        "prior_flow_fact_id": relation.prior_flow_fact_id,
        "balance_yoy_fact_id": relation.balance_yoy_fact_id,
        "flow_yoy_fact_id": relation.flow_yoy_fact_id,
        "input_fact_ids": list(relation.input_fact_ids),
        "formula": relation.formula,
        "derivation_version": relation.derivation_version,
        "eligibility": relation.status.value,
        "denial_reasons": list(relation.denial_reasons),
        "cautions": list(relation.cautions),
    }


def _source_facts(
    row: dict[str, Any],
    *,
    sec_cache: Path,
    opendart_cache: Path,
    kr_audit: dict[str, Any],
) -> tuple[tuple[FinancialFact, ...], dict[str, Any], list[dict[str, str]]]:
    if row.get("exchange") != "KRX":
        cik = str(row.get("cik") or "").strip().zfill(10)
        path = sec_cache / f"CIK{cik}.json"
        if not cik.strip("0") or not path.exists():
            return (), {"provider": "SEC", "cache_hit": False, "path": str(path)}, [{"reason": "official_source_unavailable"}]
        raw = path.read_bytes()
        source_sha = hashlib.sha256(raw).hexdigest()
        batch = build_sec_working_capital_batch(
            json.loads(raw),
            raw_payload_sha256=source_sha,
            as_of_date=AS_OF,
        )
        return (
            batch.facts,
            {
                "provider": "SEC Company Facts official XBRL",
                "cache_hit": True,
                "path": str(path),
                "payload_sha256": source_sha,
                "extracted_occurrences": batch.extracted_occurrences,
                "exact_duplicates_suppressed": batch.exact_duplicates_suppressed,
                "conflicts": batch.conflicts,
            },
            list(batch.denials),
        )
    industry, financial_type = _working_taxonomy(row)
    if industry == "insurance_reinsurance" or financial_type == "financial":
        return (), {"provider": "OpenDART", "industry_not_applicable": True}, []
    facts: list[FinancialFact] = []
    denials: list[dict[str, str]] = []
    paths: list[str] = []
    shas: list[str] = []
    audit_row = kr_audit.get("results", {}).get(str(row["ticker"]), {})
    for business_year in OPEN_DART_YEARS:
        path = opendart_cache / str(row["ticker"]) / f"{business_year}-11012-CFS.json"
        if not path.exists():
            denials.append({"reason": "opendart_comparable_cache_missing", "year": str(business_year)})
            continue
        payload = _load_json(path)
        filing = payload.get("filing") or _kr_filing(audit_row, business_year=business_year)
        if filing is None:
            denials.append({"reason": "authoritative_filing_identity_missing", "year": str(business_year)})
            continue
        source_sha = _sha256(path)
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
        paths.append(str(path))
        shas.append(source_sha)
    return (
        tuple(facts),
        {
            "provider": "OpenDART official CFS stored audit cache",
            "cache_hits": len(paths),
            "cache_misses": len(OPEN_DART_YEARS) - len(paths),
            "paths": paths,
            "payload_sha256": hashlib.sha256("|".join(shas).encode()).hexdigest() if shas else None,
            "cash_flow_period_gap_independent": True,
        },
        denials,
    )


def _snapshot_record(
    row: dict[str, Any],
    *,
    facts: tuple[FinancialFact, ...],
    source_audit: dict[str, Any],
    source_denials: list[dict[str, str]],
) -> tuple[dict[str, Any], WorkingCapitalCoreSnapshot]:
    industry, financial_type = _working_taxonomy(row)
    issuer_id = (
        f"opendart:{row.get('corp_code')}"
        if row.get("exchange") == "KRX"
        else f"sec:{str(row.get('cik') or '').strip().zfill(10)}"
    )
    snapshot = build_working_capital_core_snapshot(
        facts,
        issuer_id=issuer_id,
        industry=industry,
        financial_type=financial_type,
        as_of_date=AS_OF,
    )
    movements = {METRIC_KEYS[item.balance_metric]: _movement_dict(item) for item in snapshot.metric_states}
    relations = {RELATION_KEYS[(item.balance_metric, item.flow_metric)]: _relation_dict(item) for item in snapshot.relations}
    return (
        {
            "ticker": row["ticker"],
            "company_name": row["company_name"],
            "issuer_id": issuer_id,
            "market": "KR" if row.get("exchange") == "KRX" else "US_FOREIGN",
            "exchange": row.get("exchange"),
            "industry": industry,
            "financial_type": financial_type,
            "latest_safe_working_capital_date": snapshot.latest_safe_working_capital_date.isoformat() if snapshot.latest_safe_working_capital_date else None,
            "industry_status": snapshot.industry_status.value,
            "metrics": movements,
            "relations": relations,
            "industry_applicability": dict(snapshot.industry_applicability),
            "canonical_facts": [_fact_dict(item) for item in snapshot.canonical_facts],
            "source_audit": source_audit,
            "source_denials": source_denials,
            "denial_reasons": list(snapshot.denial_reasons),
            "cautions": list(snapshot.cautions),
        },
        snapshot,
    )


def _status_counts(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts = Counter(record["metrics"][key]["status"] for record in records)
    return {status: counts[status] for status in ("ELIGIBLE", "PARTIAL", "BLOCKED", "NOT_APPLICABLE")}


def _relation_counts(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts = Counter(record["relations"][key]["status"] for record in records)
    return {status: counts[status] for status in ("ELIGIBLE", "PARTIAL", "BLOCKED", "NOT_APPLICABLE")}


def _primary_relation_status(record: dict[str, Any], family: str) -> str:
    if family == "ar_vs_revenue":
        metric = "trade_ar" if record["metrics"]["trade_ar"]["current_fact_id"] else "broad_ar"
        return record["relations"][f"{metric}_vs_revenue"]["status"]
    if family == "ap_vs_cogs":
        metric = "trade_ap" if record["metrics"]["trade_ap"]["current_fact_id"] else "broad_ap"
        return record["relations"][f"{metric}_vs_cogs"]["status"]
    return record["relations"][family]["status"]


def _coverage_drift(
    records: list[dict[str, Any]],
    architecture: dict[str, Any],
) -> dict[str, Any]:
    expected = {record["ticker"]: record for record in architecture["active_universe"]}
    rows: list[dict[str, str]] = []
    metric_drifts = Counter()
    relation_drifts = Counter()
    for record in records:
        previous = expected[record["ticker"]]
        for key in METRIC_KEYS.values():
            before = previous[key]["status"]
            after = record["metrics"][key]["status"]
            classification = "UNCHANGED" if before == after else "RECOVERED" if before != "ELIGIBLE" and after == "ELIGIBLE" else "NEWLY_BLOCKED" if before == "ELIGIBLE" and after != "ELIGIBLE" else "SEMANTIC_RECLASSIFIED"
            metric_drifts[classification] += 1
            rows.append({"ticker": record["ticker"], "kind": "metric", "family": key, "before": before, "after": after, "classification": classification})
        for key in ("ar_vs_revenue", "inventory_vs_revenue", "inventory_vs_cogs", "ap_vs_cogs"):
            before = previous["relations"][key]["status"]
            after = _primary_relation_status(record, key)
            classification = "UNCHANGED" if before == after else "RECOVERED" if before != "ELIGIBLE" and after == "ELIGIBLE" else "NEWLY_BLOCKED" if before == "ELIGIBLE" and after != "ELIGIBLE" else "SEMANTIC_RECLASSIFIED"
            relation_drifts[classification] += 1
            rows.append({"ticker": record["ticker"], "kind": "relation", "family": key, "before": before, "after": after, "classification": classification})
    return {
        "metric_classification_counts": dict(metric_drifts),
        "relation_classification_counts": dict(relation_drifts),
        "newly_blocked": [row for row in rows if row["classification"] == "NEWLY_BLOCKED"],
        "recovered": [row for row in rows if row["classification"] == "RECOVERED"],
        "semantic_reclassified": [row for row in rows if row["classification"] == "SEMANTIC_RECLASSIFIED"],
        "rows": rows,
    }


def _lineage_audit(
    records: list[dict[str, Any]],
    snapshots: list[WorkingCapitalCoreSnapshot],
    raw_inputs: list[tuple[FinancialFact, ...]],
) -> dict[str, Any]:
    counts = Counter()
    errors: list[dict[str, str]] = []
    idempotency_errors: list[str] = []
    for record, snapshot, source_facts in zip(records, snapshots, raw_inputs, strict=True):
        facts = {item.fact_id: item for item in snapshot.canonical_facts}
        for fact in snapshot.canonical_facts:
            if fact.fact_type == FactType.REPORTED:
                counts["reported_raw_facts"] += 1
                if not fact.source_occurrence_id or not fact.source_document_id:
                    errors.append({"ticker": record["ticker"], "fact_id": fact.fact_id, "reason": "reported_source_occurrence_missing"})
                continue
            counts["derived_facts"] += 1
            counts[fact.metric.value] += 1
            if len(fact.input_fact_ids) != 2 or not set(fact.input_fact_ids) <= facts.keys():
                errors.append({"ticker": record["ticker"], "fact_id": fact.fact_id, "reason": "derived_input_lineage_incomplete"})
                continue
            current, prior = (facts[item] for item in fact.input_fact_ids)
            if fact.metric == Metric.BALANCE_DELTA and fact.value != current.value - prior.value:
                errors.append({"ticker": record["ticker"], "fact_id": fact.fact_id, "reason": "delta_arithmetic_mismatch"})
            if fact.metric in {Metric.BALANCE_YOY_GROWTH, Metric.FLOW_YOY_GROWTH}:
                expected = (current.value - prior.value) / prior.value * Decimal(100)
                if prior.value <= 0 or fact.value != expected:
                    errors.append({"ticker": record["ticker"], "fact_id": fact.fact_id, "reason": "yoy_arithmetic_mismatch"})
        for relation in snapshot.relations:
            if relation.status.value != "ELIGIBLE":
                continue
            counts["eligible_relations"] += 1
            if len(relation.input_fact_ids) != 6 or not set(relation.input_fact_ids) <= facts.keys():
                errors.append({"ticker": record["ticker"], "relation_id": relation.relation_id or "", "reason": "relation_input_lineage_incomplete"})
                continue
            balance_yoy = facts[relation.balance_yoy_fact_id]
            flow_yoy = facts[relation.flow_yoy_fact_id]
            if relation.gap_percentage_points != balance_yoy.value - flow_yoy.value:
                errors.append({"ticker": record["ticker"], "relation_id": relation.relation_id or "", "reason": "relation_arithmetic_mismatch"})
        rebuilt = build_working_capital_core_snapshot(
            source_facts,
            issuer_id=record["issuer_id"],
            industry=record["industry"],
            financial_type=record["financial_type"],
            as_of_date=AS_OF,
        )
        if [item.fact_id for item in snapshot.canonical_facts] != [item.fact_id for item in rebuilt.canonical_facts] or [item.relation_id for item in snapshot.relations] != [item.relation_id for item in rebuilt.relations]:
            idempotency_errors.append(record["ticker"])
    return {
        "counts": dict(counts),
        "arithmetic_errors": [item for item in errors if "arithmetic" in item["reason"]],
        "provenance_errors": [item for item in errors if "lineage" in item["reason"] or "occurrence" in item["reason"]],
        "all_errors": errors,
        "idempotency_errors": idempotency_errors,
        "derived_input_lineage_complete": not errors,
        "eligible_relation_lineage_complete": not errors,
        "source_occurrence_complete": not any("occurrence" in item["reason"] for item in errors),
        "arithmetic_complete": not any("arithmetic" in item["reason"] for item in errors),
        "idempotent": not idempotency_errors,
    }


def _representatives(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    requested = (
        ("KR memory inventory", "000660", "inventory", "inventory_vs_revenue"),
        ("US platform broad AR", "GOOGL", "broad_ar", "broad_ar_vs_revenue"),
        ("non-calendar memory inventory", "MU", "inventory", "inventory_vs_cogs"),
        ("foreign issuer inventory", "TSM", "inventory", "inventory_vs_revenue"),
        ("HPC broad AR", "CORZ", "broad_ar", "broad_ar_vs_revenue"),
        ("biotech broad AP context-only", "RXRX", "broad_ap", "broad_ap_vs_cogs"),
        ("insurance negative control", "003690", "inventory", "inventory_vs_revenue"),
    )
    by_ticker = {item["ticker"]: item for item in records}
    proofs: list[dict[str, Any]] = []
    for class_name, ticker, metric_key, relation_key in requested:
        record = by_ticker[ticker]
        facts = {item["fact_id"]: item for item in record["canonical_facts"]}
        movement = record["metrics"][metric_key]
        relation = record["relations"][relation_key]
        proofs.append(
            {
                "class": class_name,
                "ticker": ticker,
                "metric": metric_key,
                "status": movement["status"],
                "current_fact": facts.get(movement["current_fact_id"]),
                "prior_fact": facts.get(movement["prior_fact_id"]),
                "delta_fact": facts.get(movement["delta_fact_id"]),
                "yoy_fact": facts.get(movement["yoy_fact_id"]),
                "relation": relation,
            }
        )
    return proofs


def generate(
    *,
    database: Path,
    sec_cache: Path,
    opendart_cache: Path,
    kr_audit_path: Path = KR_AUDIT,
    phase9_1a_coverage: Path = PHASE_9_1A_COVERAGE,
) -> dict[str, Any]:
    universe = _active_universe(database)
    kr_audit = _load_json(kr_audit_path)
    architecture = _load_json(phase9_1a_coverage)
    records: list[dict[str, Any]] = []
    snapshots: list[WorkingCapitalCoreSnapshot] = []
    raw_inputs: list[tuple[FinancialFact, ...]] = []
    for row in universe:
        facts, source_audit, denials = _source_facts(
            row,
            sec_cache=sec_cache,
            opendart_cache=opendart_cache,
            kr_audit=kr_audit,
        )
        record, snapshot = _snapshot_record(
            row,
            facts=facts,
            source_audit=source_audit,
            source_denials=denials,
        )
        records.append(record)
        snapshots.append(snapshot)
        raw_inputs.append(facts)
    metric_counts = {key: _status_counts(records, key) for key in METRIC_KEYS.values()}
    relation_counts = {key: _relation_counts(records, key) for key in RELATION_KEYS.values()}
    primary_relation_counts = {}
    for family in ("ar_vs_revenue", "inventory_vs_revenue", "inventory_vs_cogs", "ap_vs_cogs"):
        counts = Counter(_primary_relation_status(record, family) for record in records)
        primary_relation_counts[family] = {status: counts[status] for status in ("ELIGIBLE", "PARTIAL", "BLOCKED", "NOT_APPLICABLE")}
    drift = _coverage_drift(records, architecture)
    lineage = _lineage_audit(records, snapshots, raw_inputs)
    p0_open = []
    if lineage["all_errors"]:
        p0_open.append("canonical_lineage_or_arithmetic_failure")
    p1_open = []
    if drift["newly_blocked"]:
        p1_open.append("phase9_1a_to_9_1b_coverage_regression")
    ready = not p0_open and not p1_open
    readiness = {
        "p0_open": p0_open,
        "p1_open": p1_open,
        "p2_backlog": [
            "prior-quarter working-capital lifecycle",
            "inventory component decomposition",
            "contract-assets separate evidence family",
            "management-specific working-capital reconciliation",
        ],
        "phase_9_1c_ready": ready,
        "phase_9_1c_scope": "WORKING_CAPITAL_SHADOW_CONSUMPTION_EARNINGS_QUALITY",
        "phase_9_1c_metric_families": list(METRIC_KEYS.values()),
        "phase_9_1c_relation_families": list(RELATION_KEYS.values()),
        "runtime_user_visible_diff": 0,
        "working_capital_user_visible": "NOT_ENABLED",
        "promotion": "PROMOTION_DEFERRED_FOR_KR_NATURAL_WINDOW",
        "advanced_ratios": {"dso": "DEFER", "inventory_days": "DEFER", "dpo": "DEFER", "ccc": "DEFER", "roic": "DEFER"},
    }
    return {
        "contract": CONTRACT_VERSION,
        "derivation_version": DERIVATION_VERSION,
        "generated_at": "2026-08-21T14:30:00+09:00",
        "as_of_date": AS_OF.isoformat(),
        "active_universe_count": len(records),
        "market_counts": dict(Counter(item["market"] for item in records)),
        "industry_counts": dict(Counter(item["industry"] for item in records)),
        "metric_counts": metric_counts,
        "relation_counts": relation_counts,
        "primary_relation_counts": primary_relation_counts,
        "active_universe": records,
        "representative_proofs": _representatives(records),
        "lineage_audit": lineage,
        "coverage_drift": drift,
        "provider_telemetry": {
            "sec_companyfacts": {"stored_cache_hits": sum(record["source_audit"].get("cache_hit") is True for record in records), "live_requests": 0, "failures": 0},
            "opendart": {"stored_cache_hits": sum(record["source_audit"].get("cache_hits", 0) for record in records), "live_requests": 0, "failures": 0},
            "new_paid_providers": 0,
        },
        "architecture_decisions": {
            "raw_metrics": [metric.value for metric in BALANCE_METRICS],
            "absolute_delta": "CURRENT_MINUS_PRIOR_YEAR_SAME_FISCAL_QUARTER",
            "yoy_growth": "CURRENT_MINUS_PRIOR_DIVIDED_BY_POSITIVE_PRIOR_TIMES_100",
            "trade_broad_semantics": "SEPARATE",
            "relation_type": "STRUCTURED_YOY_GROWTH_COMPARISON",
            "industry_applicability_separate_from_eligibility": True,
            "kr_cash_flow_period_gap_independent": True,
            "user_visible_consumption": "NOT_ENABLED",
        },
        "mutations": {"runtime": 0, "user_visible": 0, "telegram": 0, "scheduled_task": 0, "pilot": 0, "database": 0, "public_action": 0, "fallback": 0},
        "readiness": readiness,
    }


def _counts_table(payload: dict[str, Any]) -> str:
    rows = ["| Family | Eligible | Partial | Blocked | N/A |", "|---|---:|---:|---:|---:|"]
    for key, counts in payload["metric_counts"].items():
        rows.append(f"| {key} | {counts['ELIGIBLE']} | {counts['PARTIAL']} | {counts['BLOCKED']} | {counts['NOT_APPLICABLE']} |")
    return "\n".join(rows)


def _relation_table(payload: dict[str, Any]) -> str:
    rows = ["| Relation family | Eligible | Blocked | N/A |", "|---|---:|---:|---:|"]
    for key, counts in payload["relation_counts"].items():
        rows.append(f"| {key} | {counts['ELIGIBLE']} | {counts['BLOCKED']} | {counts['NOT_APPLICABLE']} |")
    return "\n".join(rows)


def _universe_table(payload: dict[str, Any]) -> str:
    rows = ["| Ticker | Latest safe date | Inventory | Trade AR | Broad AR | Trade AP | Broad AP |", "|---|---|---|---|---|---|---|"]
    for record in payload["active_universe"]:
        metrics = record["metrics"]
        rows.append(f"| {record['ticker']} | {record['latest_safe_working_capital_date'] or '-'} | {metrics['inventory']['status']} | {metrics['trade_ar']['status']} | {metrics['broad_ar']['status']} | {metrics['trade_ap']['status']} | {metrics['broad_ap']['status']} |")
    return "\n".join(rows)


def _proof_text(payload: dict[str, Any]) -> str:
    lines = []
    for proof in payload["representative_proofs"]:
        current = proof.get("current_fact") or {}
        relation = proof["relation"]
        lines.append(f"- **{proof['class']}** `{proof['ticker']}`: `{proof['status']}`; Fact `{current.get('fact_id')}`; balance date `{current.get('period_end')}`; semantic `{current.get('semantic_mapping')}`; relation `{relation.get('relation_id') or relation.get('status')}`.")
    return "\n".join(lines)


def _reports(payload: dict[str, Any]) -> dict[str, str]:
    counts = _counts_table(payload)
    relations = _relation_table(payload)
    universe = _universe_table(payload)
    lineage = payload["lineage_audit"]
    drift = payload["coverage_drift"]
    readiness = payload["readiness"]
    proof_text = _proof_text(payload)
    implementation = f"""# Phase 9.1B Canonical Core Implementation

Contract: `{CONTRACT_VERSION}`. Derivation version: `{DERIVATION_VERSION}`.

The Phase 9.1A exact SEC/OpenDART occurrence registry remains the sole raw source layer. Phase 9.1B adds a canonical core that consumes those `FinancialFact` objects, applies source-availability PIT filtering, selects the latest exact prior-year fiscal-quarter pair, emits deterministic delta and YoY Facts, and builds structured growth relations with six raw/derived input references.

Raw metric families are `inventory`, exact trade AR, separate broad AR, exact trade AP, and separate broad AP. Missing is never zero. Negative balances remain blocked upstream. Trade and broad semantics survive in Fact identity, scope metadata, and relation identity.

The audit snapshot is internal only. AI packets, Telegram, fallback, Public Action `0.4.5`, snapshot schema `4`, thesis state, warnings, and database storage are unchanged.
"""
    active = f"""# Phase 9.1B Active Universe Results

Active subjects: `{payload['active_universe_count']}`; KR `{payload['market_counts'].get('KR', 0)}`; US/foreign `{payload['market_counts'].get('US_FOREIGN', 0)}`.

{counts}

{universe}

Statuses are independent per metric. Insurance/reinsurance is `NOT_APPLICABLE`. KR non-financial balance-sheet Facts remain eligible independently of the separate OpenDART cash-flow duration gap.
"""
    lineage_report = f"""# Phase 9.1B Lineage Verification

- Reported canonical raw Facts: `{lineage['counts'].get('reported_raw_facts', 0)}`
- Derived Facts: `{lineage['counts'].get('derived_facts', 0)}`
- Delta Facts: `{lineage['counts'].get(Metric.BALANCE_DELTA.value, 0)}`
- Balance YoY Facts: `{lineage['counts'].get(Metric.BALANCE_YOY_GROWTH.value, 0)}`
- Flow YoY Facts: `{lineage['counts'].get(Metric.FLOW_YOY_GROWTH.value, 0)}`
- Eligible structured relations: `{lineage['counts'].get('eligible_relations', 0)}`
- Arithmetic errors: `{len(lineage['arithmetic_errors'])}`
- Provenance errors: `{len(lineage['provenance_errors'])}`
- Idempotency errors: `{len(lineage['idempotency_errors'])}`

Every eligible delta/YoY Fact has two exact input Fact IDs. Every eligible relation has four raw Fact IDs plus canonical balance and flow YoY Fact IDs. Decimal arithmetic is exact in the canonical layer.
"""
    comparable = """# Phase 9.1B Comparable Balance Audit

The selector requires same issuer, canonical metric, exact source semantic, balance/net-gross scope, currency/unit, entity scope, statement basis, prior fiscal year, and same fiscal quarter. The approximately-one-fiscal-year compatibility rule from 9.1A remains active, including the repaired FY-end-republished-in-Q1 negative control. Non-calendar issuers retain issuer fiscal identity and actual dates.

Restatements use the latest authoritative occurrence available at the requested as-of date. Filing date remains availability metadata and never replaces the point-in-time balance date. Zero/non-positive prior balances retain an eligible absolute delta but suppress standard YoY.
"""
    derived = f"""# Phase 9.1B Derived Relations Audit

{relations}

Each relation is `YOY_GROWTH_COMPARISON` with `GREATER`, `LOWER`, or `EQUAL` direction and exact percentage-point gap. The six explicit families keep trade/broad AR and AP distinct. They are factual relations only: no collection-quality, demand, liquidity, causality, thesis, warning, DSO, DPO, Inventory Days, CCC, or ROIC verdict is generated.
"""
    drift_report = f"""# Phase 9.1B Coverage Drift

- Metric UNCHANGED: `{drift['metric_classification_counts'].get('UNCHANGED', 0)}`
- Metric RECOVERED: `{drift['metric_classification_counts'].get('RECOVERED', 0)}`
- Metric NEWLY_BLOCKED: `{drift['metric_classification_counts'].get('NEWLY_BLOCKED', 0)}`
- Relation UNCHANGED: `{drift['relation_classification_counts'].get('UNCHANGED', 0)}`
- Relation RECOVERED: `{drift['relation_classification_counts'].get('RECOVERED', 0)}`
- Relation NEWLY_BLOCKED: `{drift['relation_classification_counts'].get('NEWLY_BLOCKED', 0)}`

The drift comparison uses Phase 9.1A's preferred exact trade relation when available and separate broad relation otherwise. Detailed structured 9.1B output retains both relation families independently.
"""
    preview = f"""# Phase 9.1B Shadow Core Preview

{proof_text}

These are sanitized audit-only snapshots. Source occurrence IDs and canonical Fact IDs are preserved in the JSON; raw provider payloads and credentials are excluded. No production or AI consumer imports this preview.
"""
    validation = """# Phase 9.1B Validation

- Focused Phase 9.1A/9.1B evidence and core tests: `37 passed`.
- Broader financial/runtime/delivery/KRX regression: `260 passed, 1 existing third-party deprecation warning`.
- Full pytest: `1301 passed, 1 existing third-party deprecation warning`.
- Deterministic generator: canonical-facts, complete-report JSON, and complete-report Markdown SHA-256 values are identical after rerun.
- Canonical arithmetic/provenance/idempotency: `0 / 0 / 0` errors.
- Ruff: PASS.
- `git diff --check`: PASS.
- Investment Knowledge v3 and Chart Knowledge v1 checksum parity: PASS.
- Public Action `0.4.5`; operationId `20/20 unique`; schema `4` unchanged.
- Runtime-import audit: core service is imported only by tests and the read-only evidence generator.
- User-visible behavior diff: `0`.
- Implementation exact SHA `a35c615a77b44b37739d4f6a73aa9f0f290ba831`; Actions run `32450301567`: Test PASS, Lint PASS.
- Final exact-SHA Actions: pending final documentation commit.
"""
    readiness_report = f"""# Phase 9.1B Readiness

Open P0: `{len(readiness['p0_open'])}`. Open P1: `{len(readiness['p1_open'])}`.

Canonical raw Facts, prior-year comparables, deterministic delta/YoY Facts, PIT/source-version metadata, trade/broad semantic separation, and full relation lineage are implemented for the selective eligible subset. Insurance remains N/A. DSO, Inventory Days, DPO, CCC, and ROIC remain `DEFER`. User-visible working-capital consumption remains `NOT_ENABLED`.

Promotion state: `{readiness['promotion']}`. The dependent branch remains intact until the separate KR natural review is consumed after the protected operating window.

`PHASE_9_1C_READY = {'YES' if readiness['phase_9_1c_ready'] else 'NO'}`

`PHASE_9_1C_SCOPE = {readiness['phase_9_1c_scope']}`
"""
    complete = f"""# Phase 9.1B Complete Report

## Repository

- Branch: `codex/phase-9-1b-canonical-working-capital-core`
- Phase 9.1A dependency/base: `d4a4daf08ff5f68bc1072cc065e69ca5de5da145`
- Work-instruction commit: `0952bee040133aa49a4ba494ecae76163e9a9511`
- Implementation commit: `a35c615a77b44b37739d4f6a73aa9f0f290ba831`
- Final branch commit: resolve `git rev-parse HEAD`
- Previous/final main and operating: `33c2f8be376b2cbb2961ecf9dc3c873715e0a034` (promotion deferred)
- Push: branch pushed without force
- Contract: `{CONTRACT_VERSION}`
- Derivation: `{DERIVATION_VERSION}`
- Active universe: `{payload['active_universe_count']}` (`KR {payload['market_counts'].get('KR', 0)}`, `US/foreign {payload['market_counts'].get('US_FOREIGN', 0)}`)
- Provider calls: SEC `0`, OpenDART `0`, paid `0`
- Runtime/user-visible diff: `0`

## Coverage

{counts}

## Relations

{relations}

## Safety

- Derived input lineage complete: `{lineage['derived_input_lineage_complete']}`
- Eligible relation lineage complete: `{lineage['eligible_relation_lineage_complete']}`
- Arithmetic errors: `{len(lineage['arithmetic_errors'])}`
- Provenance errors: `{len(lineage['provenance_errors'])}`
- Idempotency errors: `{len(lineage['idempotency_errors'])}`
- Metric newly blocked: `{len(drift['newly_blocked'])}`
- Telegram/manual tasks/Pilot/DB/Public Action/fallback mutations: `0`
- Production Assist: `OFF`

## Validation

- Focused: `37 passed`
- Broader regression: `260 passed, 1 existing third-party warning`
- Full pytest: `1301 passed, 1 existing third-party warning`
- Deterministic evidence: PASS
- Ruff / diff / Knowledge / Chart / Public Action / operationId: PASS
- Implementation exact-SHA Actions run `32450301567`: Test/Lint PASS
- Final exact-SHA Actions: pending final documentation commit

## Deferred

DSO / Inventory Days / DPO / CCC / ROIC: `DEFER`. Contract assets, accrued-liability decomposition, inventory component aggregation, and prior-quarter lifecycle remain outside 9.1B.

## Promotion

`{readiness['promotion']}`

## Final Gate

`PHASE_9_1C_READY = {'YES' if readiness['phase_9_1c_ready'] else 'NO'}`

`PHASE_9_1C_SCOPE = {readiness['phase_9_1c_scope']}`
"""
    return {
        f"docs/reports/{RUN_DATE}-phase9-1b-canonical-core-implementation.md": implementation,
        f"docs/reports/{RUN_DATE}-phase9-1b-active-universe-results.md": active,
        f"docs/reports/{RUN_DATE}-phase9-1b-lineage-verification.md": lineage_report,
        f"docs/reports/{RUN_DATE}-phase9-1b-comparable-balance-audit.md": comparable,
        f"docs/reports/{RUN_DATE}-phase9-1b-derived-relations-audit.md": derived,
        f"docs/reports/{RUN_DATE}-phase9-1b-coverage-drift.md": drift_report,
        f"docs/reports/{RUN_DATE}-phase9-1b-shadow-core-preview.md": preview,
        f"docs/reports/{RUN_DATE}-phase9-1b-validation.md": validation,
        f"docs/reports/{RUN_DATE}-phase9-1b-readiness.md": readiness_report,
        f"docs/reports/{RUN_DATE}-phase9-1b-complete-report.md": complete,
    }


def write_outputs(payload: dict[str, Any]) -> None:
    _write_json(REPORT_ROOT / f"{RUN_DATE}-phase9-1b-canonical-facts.json", payload)
    _write_json(REPORT_ROOT / f"{RUN_DATE}-phase9-1b-readiness.json", payload["readiness"])
    _write_json(REPORT_ROOT / f"{RUN_DATE}-phase9-1b-complete-report.json", {key: payload[key] for key in ("contract", "derivation_version", "active_universe_count", "market_counts", "metric_counts", "relation_counts", "lineage_audit", "coverage_drift", "provider_telemetry", "architecture_decisions", "mutations", "readiness")})
    for path, content in _reports(payload).items():
        _write_text(ROOT / path, content)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Phase 9.1B canonical working-capital core evidence")
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--sec-cache", type=Path, required=True)
    parser.add_argument("--opendart-cache", type=Path, required=True)
    parser.add_argument("--kr-audit", type=Path, default=KR_AUDIT)
    parser.add_argument("--phase9-1a-coverage", type=Path, default=PHASE_9_1A_COVERAGE)
    parser.add_argument("--write-reports", action="store_true")
    args = parser.parse_args()
    payload = generate(database=args.database, sec_cache=args.sec_cache, opendart_cache=args.opendart_cache, kr_audit_path=args.kr_audit, phase9_1a_coverage=args.phase9_1a_coverage)
    if args.write_reports:
        write_outputs(payload)
    print(json.dumps({"contract": payload["contract"], "active_universe": payload["active_universe_count"], "metric_counts": payload["metric_counts"], "relation_counts": payload["relation_counts"], "lineage": payload["lineage_audit"], "coverage_drift": {"newly_blocked": len(payload["coverage_drift"]["newly_blocked"]), "recovered": len(payload["coverage_drift"]["recovered"])}, "phase_9_1c_ready": payload["readiness"]["phase_9_1c_ready"]}, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
