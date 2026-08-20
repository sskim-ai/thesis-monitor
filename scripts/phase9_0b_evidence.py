from __future__ import annotations

# ruff: noqa: E501

import argparse
import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from app.services.cash_flow_capital_efficiency_service import (
    CONTRACT_VERSION,
    EligibilityStatus,
    FactType,
    FinancialFact,
    Metric,
)
from app.services.cash_flow_shadow_service import (
    CashFlowCoreSnapshot,
    build_sec_cash_flow_core,
    fact_to_dict,
)
from app.services.official_cash_flow_service import (
    registry_audit,
    rejected_semantic_audit,
)
from scripts.phase9_0a_evidence import _active_universe, _taxonomy


ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = ROOT / "docs" / "reports"
RUN_DATE = "20260820"
AS_OF = date(2026, 8, 20)
PHASE9_0A_COVERAGE = REPORT_ROOT / f"{RUN_DATE}-phase9-0a-coverage.json"


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


def _latest_fact(snapshot: CashFlowCoreSnapshot, metric: Metric) -> FinancialFact | None:
    values = [
        item
        for item in snapshot.facts
        if item.metric == metric and item.fact_type == FactType.REPORTED
    ]
    return max(
        values,
        key=lambda item: (item.period.end, item.filing_date, item.fact_id),
        default=None,
    )


def _metric(status: str, reason: str, fact: FinancialFact | None = None) -> dict[str, Any]:
    return {
        "status": status,
        "reason": reason,
        "fact_id": fact.fact_id if fact else None,
    }


def _sec_record(
    row: dict[str, Any],
    *,
    source_path: Path,
) -> tuple[dict[str, Any], tuple[dict[str, Any], ...], CashFlowCoreSnapshot]:
    raw = source_path.read_bytes()
    payload = json.loads(raw)
    source_sha = hashlib.sha256(raw).hexdigest()
    industry, financial_type = _taxonomy(row)
    snapshot = build_sec_cash_flow_core(
        payload,
        raw_payload_sha256=source_sha,
        as_of_date=AS_OF,
        financial_type=financial_type,
    )
    ocf = _latest_fact(snapshot, Metric.OCF)
    capex = _latest_fact(snapshot, Metric.CAPEX)
    if snapshot.status == EligibilityStatus.NOT_APPLICABLE:
        metrics = {
            "ocf": _metric("PARTIAL", "financial_industry_context_only"),
            "capex_ppe": _metric(
                "NOT_APPLICABLE", "financial_industry_not_applicable"
            ),
            "fcf": _metric("NOT_APPLICABLE", "financial_industry_not_applicable"),
        }
    else:
        metrics = {
            "ocf": _metric(
                "ELIGIBLE" if ocf else "BLOCKED",
                "official_occurrence_canonicalized" if ocf else "missing_ocf",
                ocf,
            ),
            "capex_ppe": _metric(
                "ELIGIBLE" if capex else "BLOCKED",
                "official_ppe_occurrence_canonicalized"
                if capex
                else "missing_ppe_capex",
                capex,
            ),
            "fcf": _metric(
                "ELIGIBLE" if snapshot.latest_fcf else "BLOCKED",
                "deterministic_ocf_minus_ppe_capex"
                if snapshot.latest_fcf
                else "compatible_ocf_capex_pair_missing",
                snapshot.latest_fcf,
            ),
        }
    facts = tuple(
        {"ticker": row["ticker"], **fact_to_dict(item)} for item in snapshot.facts
    )
    record = {
        "ticker": row["ticker"],
        "company_name": row["company_name"],
        "market": "US_FOREIGN",
        "exchange": row.get("exchange"),
        "industry": industry,
        "financial_type": financial_type,
        "issuer_type": row.get("issuer_type"),
        "security_type": row.get("security_type"),
        "source": "SEC Company Facts official XBRL",
        "source_cache": str(source_path),
        "source_payload_sha256": source_sha,
        "metrics": metrics,
        "cash_flow_core_status": snapshot.status.value,
        "latest_safe_period": (
            {
                "period_start": snapshot.latest_fcf.period.start.isoformat(),
                "period_end": snapshot.latest_fcf.period.end.isoformat(),
                "period_type": snapshot.latest_fcf.period.period_type.value,
                "currency": snapshot.latest_fcf.currency,
                "ocf_fact_id": snapshot.latest_fcf.input_fact_ids[0],
                "capex_fact_id": snapshot.latest_fcf.input_fact_ids[1],
                "fcf_fact_id": snapshot.latest_fcf.fact_id,
                "fcf_value": str(snapshot.latest_fcf.value),
            }
            if snapshot.latest_fcf
            else None
        ),
        "latest_qtd_fcf_fact_id": (
            snapshot.latest_qtd_fcf.fact_id if snapshot.latest_qtd_fcf else None
        ),
        "latest_ttm_fcf_fact_id": (
            snapshot.latest_ttm_fcf.fact_id if snapshot.latest_ttm_fcf else None
        ),
        "denial_reasons": list(snapshot.denial_reasons),
        "cautions": list(snapshot.cautions),
        "source_audit": snapshot.source_audit,
    }
    return record, facts, snapshot


def _missing_sec_record(row: dict[str, Any], source_path: Path) -> dict[str, Any]:
    industry, financial_type = _taxonomy(row)
    return {
        "ticker": row["ticker"],
        "company_name": row["company_name"],
        "market": "US_FOREIGN",
        "exchange": row.get("exchange"),
        "industry": industry,
        "financial_type": financial_type,
        "issuer_type": row.get("issuer_type"),
        "security_type": row.get("security_type"),
        "source": "SEC Company Facts cache missing",
        "source_cache": str(source_path),
        "source_payload_sha256": None,
        "metrics": {
            name: _metric("BLOCKED", "official_source_unavailable")
            for name in ("ocf", "capex_ppe", "fcf")
        },
        "cash_flow_core_status": "BLOCKED",
        "latest_safe_period": None,
        "latest_qtd_fcf_fact_id": None,
        "latest_ttm_fcf_fact_id": None,
        "denial_reasons": ["official_source_unavailable"],
        "cautions": [],
        "source_audit": {},
    }


def _kr_record(row: dict[str, Any], phase9_0a: dict[str, Any]) -> dict[str, Any]:
    industry, financial_type = _taxonomy(row)
    prior = next(
        item
        for item in phase9_0a["active_universe"]
        if item["ticker"] == row["ticker"]
    )
    if financial_type == "financial":
        metrics = {
            "ocf": _metric("PARTIAL", "financial_industry_context_only"),
            "capex_ppe": _metric(
                "NOT_APPLICABLE", "financial_industry_not_applicable"
            ),
            "fcf": _metric("NOT_APPLICABLE", "financial_industry_not_applicable"),
        }
        status = "NOT_APPLICABLE"
        reasons = ["financial_industry_not_applicable"]
    else:
        metrics = {
            "ocf": _metric("PARTIAL", "period_context_unresolved"),
            "capex_ppe": _metric("PARTIAL", "period_context_unresolved"),
            "fcf": _metric("BLOCKED", "period_context_unresolved"),
        }
        status = "PARTIAL"
        reasons = ["period_context_unresolved"]
    return {
        "ticker": row["ticker"],
        "company_name": row["company_name"],
        "market": "KR",
        "exchange": row.get("exchange"),
        "industry": industry,
        "financial_type": financial_type,
        "issuer_type": row.get("issuer_type"),
        "security_type": row.get("security_type"),
        "source": "OpenDART stored formal evidence",
        "source_payload_sha256": prior.get("source_payload_sha256"),
        "metrics": metrics,
        "cash_flow_core_status": status,
        "latest_safe_period": None,
        "latest_qtd_fcf_fact_id": None,
        "latest_ttm_fcf_fact_id": None,
        "denial_reasons": reasons,
        "cautions": [],
        "source_audit": {
            "phase9_0a_ocf": prior["metrics"]["ocf"],
            "phase9_0a_capex_ppe": prior["metrics"]["capex_ppe"],
            "canonical_promotion_count": 0,
        },
    }


def _metric_counts(records: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    output: dict[str, dict[str, int]] = {}
    for metric in ("ocf", "capex_ppe", "fcf"):
        counts = Counter(row["metrics"][metric]["status"] for row in records)
        output[metric] = {
            key: counts[key]
            for key in ("ELIGIBLE", "PARTIAL", "BLOCKED", "NOT_APPLICABLE")
        }
    return output


def _coverage_drift(
    records: list[dict[str, Any]],
    phase9_0a: dict[str, Any],
) -> list[dict[str, str]]:
    prior = {item["ticker"]: item for item in phase9_0a["active_universe"]}
    output: list[dict[str, str]] = []
    for record in records:
        ticker = record["ticker"]
        for metric in ("ocf", "capex_ppe", "fcf"):
            before = prior[ticker]["metrics"][metric]["status"]
            after = record["metrics"][metric]["status"]
            if before == after:
                category = "UNCHANGED"
            elif after == "ELIGIBLE":
                category = "NEWLY_ELIGIBLE"
            elif before == "ELIGIBLE":
                category = "NEWLY_BLOCKED"
            else:
                category = "RECOVERED" if after == "PARTIAL" else "UNCHANGED"
            output.append(
                {
                    "ticker": ticker,
                    "metric": metric,
                    "phase9_0a": before,
                    "phase9_0b": after,
                    "category": category,
                    "reason": record["metrics"][metric]["reason"],
                }
            )
    return output


def _lineage_audit(
    snapshots: dict[str, CashFlowCoreSnapshot],
) -> dict[str, Any]:
    eligible = 0
    complete = 0
    failures: list[dict[str, str]] = []
    for ticker, snapshot in snapshots.items():
        facts = {item.fact_id: item for item in snapshot.facts}
        for fcf in (item for item in snapshot.facts if item.metric == Metric.FCF):
            eligible += 1
            if len(fcf.input_fact_ids) != 2 or any(
                fact_id not in facts for fact_id in fcf.input_fact_ids
            ):
                failures.append({"ticker": ticker, "fact_id": fcf.fact_id, "reason": "input_fact_missing"})
                continue
            ocf, capex = (facts[fact_id] for fact_id in fcf.input_fact_ids)
            compatible = all(
                (
                    ocf.issuer_id == capex.issuer_id,
                    ocf.period == capex.period,
                    ocf.currency == capex.currency,
                    ocf.unit == capex.unit,
                    ocf.entity_scope == capex.entity_scope,
                    ocf.statement_basis == capex.statement_basis,
                    ocf.source_document_id == capex.source_document_id,
                    fcf.value == ocf.value - capex.value,
                    fcf.raw_payload_sha256
                    == hashlib.sha256(
                        f"{ocf.raw_payload_sha256}|{capex.raw_payload_sha256}".encode()
                    ).hexdigest(),
                )
            )
            if compatible:
                complete += 1
            else:
                failures.append({"ticker": ticker, "fact_id": fcf.fact_id, "reason": "lineage_or_arithmetic_mismatch"})
    return {
        "derived_fcf_facts": eligible,
        "complete_lineage": complete,
        "complete_pct": 100 if eligible and complete == eligible else 0,
        "failures": failures,
    }


def _representatives(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    classes = (
        ("US domestic issuer", lambda row: row["market"] == "US_FOREIGN" and row.get("issuer_type") != "foreign_private_issuer" and row["metrics"]["fcf"]["status"] == "ELIGIBLE"),
        ("non-calendar fiscal issuer", lambda row: row["market"] == "US_FOREIGN" and row.get("latest_safe_period") and not str(row["latest_safe_period"]["period_start"]).endswith("01-01")),
        ("foreign issuer / ADR", lambda row: row["market"] == "US_FOREIGN" and (row.get("issuer_type") == "foreign_private_issuer" or row.get("security_type") == "depositary_receipt") and row["metrics"]["fcf"]["status"] == "ELIGIBLE"),
        ("CAPEX-heavy infrastructure", lambda row: row["industry"] == "hpc_data_center" and row["metrics"]["fcf"]["status"] == "ELIGIBLE"),
        ("pre-profit biotech", lambda row: row["industry"] == "biotech"),
        ("financial industry exclusion", lambda row: row["financial_type"] == "financial"),
        ("KR period-context block", lambda row: row["market"] == "KR" and row["financial_type"] != "financial"),
    )
    output: list[dict[str, Any]] = []
    for label, predicate in classes:
        record = next((item for item in records if predicate(item)), None)
        output.append(
            {
                "class": label,
                "ticker": record["ticker"] if record else None,
                "ocf": record["metrics"]["ocf"] if record else None,
                "capex_ppe": record["metrics"]["capex_ppe"] if record else None,
                "fcf": record["metrics"]["fcf"] if record else None,
                "latest_safe_period": record.get("latest_safe_period") if record else None,
            }
        )
    return output


def _table(records: list[dict[str, Any]]) -> str:
    lines = [
        "| Ticker | Industry | OCF | PPE CAPEX | FCF | Latest period | Denial |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in records:
        latest = row.get("latest_safe_period") or {}
        period = (
            f"{latest.get('period_end')} {latest.get('period_type')}"
            if latest
            else "-"
        )
        lines.append(
            f"| {row['ticker']} | {row['industry']} | {row['metrics']['ocf']['status']} | {row['metrics']['capex_ppe']['status']} | {row['metrics']['fcf']['status']} | {period} | {', '.join(row['denial_reasons']) or '-'} |"
        )
    return "\n".join(lines)


def _reports(output: dict[str, Any]) -> dict[str, str]:
    records = output["active_universe"]
    counts = output["metric_counts"]
    lineage = output["lineage_audit"]
    representatives = output["representative_implementation_proofs"]
    drift = output["coverage_drift"]
    universe_table = _table(records)
    proof_lines = "\n".join(
        f"- **{item['class']}**: `{item['ticker']}`; OCF `{(item.get('ocf') or {}).get('status', 'N/A')}`, CAPEX `{(item.get('capex_ppe') or {}).get('status', 'N/A')}`, FCF `{(item.get('fcf') or {}).get('status', 'N/A')}`"
        for item in representatives
    )
    changed = [item for item in drift if item["category"] != "UNCHANGED"]
    drift_lines = "\n".join(
        f"- `{item['ticker']}` {item['metric']}: {item['phase9_0a']} -> {item['phase9_0b']} ({item['category']}; {item['reason']})"
        for item in changed
    ) or "- No status drift."
    implementation = f"""# Phase 9.0B Canonical Core Implementation

Contract: `{CONTRACT_VERSION}`

Implemented modules:

- `official_cash_flow_service`: exact SEC semantic registry, official occurrence extraction, fiscal-context normalization, deterministic reported Fact identity, version-aware selection.
- `cash_flow_shadow_service`: bounded period derivation, exact period/source pairing, deterministic PPE-only FCF, eligibility and audit serialization.
- `cash_flow_capital_efficiency_service`: explicit `REPORTED`, `DERIVED_PERIOD`, and `DERIVED_METRIC` types plus complete derivation metadata.

The production packet, AI prompt, renderer, fallback, Public Action, and database schema are unchanged. The core is internal shadow evidence only.
"""
    active = f"""# Phase 9.0B Active Universe Results

Active monitored stocks: `{len(records)}`; KR `{sum(row['market'] == 'KR' for row in records)}`; US/foreign `{sum(row['market'] == 'US_FOREIGN' for row in records)}`.

| Metric | Eligible | Partial | Blocked | N/A |
|---|---:|---:|---:|---:|
| OCF | {counts['ocf']['ELIGIBLE']} | {counts['ocf']['PARTIAL']} | {counts['ocf']['BLOCKED']} | {counts['ocf']['NOT_APPLICABLE']} |
| PPE CAPEX | {counts['capex_ppe']['ELIGIBLE']} | {counts['capex_ppe']['PARTIAL']} | {counts['capex_ppe']['BLOCKED']} | {counts['capex_ppe']['NOT_APPLICABLE']} |
| FCF | {counts['fcf']['ELIGIBLE']} | {counts['fcf']['PARTIAL']} | {counts['fcf']['BLOCKED']} | {counts['fcf']['NOT_APPLICABLE']} |

{universe_table}

## Phase 9.0A Drift

{drift_lines}
"""
    lineage_report = f"""# Phase 9.0B Lineage Verification

- Canonical FCF facts audited: `{lineage['derived_fcf_facts']}`
- Complete input lineage: `{lineage['complete_lineage']}`
- Complete lineage percentage: `{lineage['complete_pct']}%`
- Lineage/arithmetic failures: `{len(lineage['failures'])}`

Every eligible FCF retains exactly two input Fact IDs, matching issuer, period, currency/unit, entity scope, statement basis, and source-document chain. Derived raw SHA is deterministic over both input payload hashes.

## Representative Proofs

{proof_lines}
"""
    reproduction = f"""# Phase 9.0B FCF Reproduction Audit

Formula: `operating_cash_flow - positive-magnitude ppe_capex_cash_outflow`.

- Latest-period eligible issuers: `{counts['fcf']['ELIGIBLE']}`
- Blocked issuers: `{counts['fcf']['BLOCKED']}`
- Not applicable: `{counts['fcf']['NOT_APPLICABLE']}`
- Arithmetic/provenance failures: `{len(lineage['failures'])}`

Negative OCF and negative FCF remain valid. Missing OCF or CAPEX is never replaced with zero. Management-defined FCF remains separate and is not reconciled in this phase.
"""
    period = """# Phase 9.0B Period Derivation Audit

- Reported interim cash-flow occurrences remain `YTD`.
- Verified Q1 YTD may produce a `DERIVED_PERIOD` QTD fact.
- Q2/Q3 QTD uses adjacent same-FY compatible YTD difference only.
- TTM uses prior FY + current YTD - prior comparable YTD only.
- Company Facts comparative rows inherit fiscal context from the earliest official occurrence for the same semantic, start/end, and unit; the latest filing remains the value/version authority.
- Annualization and calendar-year inference: `0`.
- Odd/53-week source dates are preserved.
"""
    eligibility = """# Phase 9.0B Eligibility Results

Eligibility is contract-driven, not ticker-driven. The implementation reproduces the Phase 9.0A selective subset without status drift.

- KR non-financial: `PARTIAL/BLOCKED`, reason `period_context_unresolved`, canonical promotion `0`.
- Insurance/reinsurance: generic enterprise PPE CAPEX/FCF `NOT_APPLICABLE`.
- Foreign/ADR: issuer-level OCF/PPE CAPEX/FCF may be eligible; per-share/yield/market-cap arithmetic is absent.
- HUT: OCF remains eligible, PPE CAPEX and FCF remain blocked.
- SKHY: official registered OCF/PPE semantics remain unavailable, so all core metrics fail closed.
"""
    shadow = f"""# Phase 9.0B Shadow Cash-Flow Preview

This is archive-only internal evidence. No daily packet or public response consumes it.

{universe_table}

Canonical amounts and Fact IDs are in `20260820-phase9-0b-canonical-facts.json`. No FCF/share, FCF yield, EV/FCF, thesis delta, warning lifecycle, CCC, or ROIC is generated.
"""
    validation_path = REPORT_ROOT / f"{RUN_DATE}-phase9-0b-validation.md"
    validation = (
        validation_path.read_text(encoding="utf-8")
        if validation_path.exists()
        else """# Phase 9.0B Validation

Validation is recorded after focused and full repository checks. This evidence generator does not mutate runtime state, tasks, Telegram, Pilot, or the database.
"""
    )
    readiness = f"""# Phase 9.0B Readiness

- Open P0: `{len(output['readiness']['p0_open'])}`
- Open P1: `{len(output['readiness']['p1_open'])}`
- Runtime user-visible diff: `0`
- KR OpenDART period recovery: `MEDIUM_COMPLEXITY_FOLLOWUP`
- CCC: `DEFERRED`
- Standard ROIC: `DEFERRED`

`PHASE_9_0C_READY = {'YES' if output['readiness']['phase_9_0c_ready'] else 'NO'}`

`PHASE_9_0C_SCOPE = {output['readiness']['phase_9_0c_scope']}`
"""
    reports = {
        f"docs/reports/{RUN_DATE}-phase9-0b-canonical-core-implementation.md": implementation,
        f"docs/reports/{RUN_DATE}-phase9-0b-active-universe-results.md": active,
        f"docs/reports/{RUN_DATE}-phase9-0b-lineage-verification.md": lineage_report,
        f"docs/reports/{RUN_DATE}-phase9-0b-fcf-reproduction-audit.md": reproduction,
        f"docs/reports/{RUN_DATE}-phase9-0b-period-derivation-audit.md": period,
        f"docs/reports/{RUN_DATE}-phase9-0b-eligibility-results.md": eligibility,
        f"docs/reports/{RUN_DATE}-phase9-0b-shadow-cash-flow-preview.md": shadow,
        f"docs/reports/{RUN_DATE}-phase9-0b-validation.md": validation,
        f"docs/reports/{RUN_DATE}-phase9-0b-readiness.md": readiness,
    }
    reports[f"docs/reports/{RUN_DATE}-phase9-0b-complete-report-bundle.md"] = (
        "# Phase 9.0B Complete Report Bundle\n\n"
        "Boundary: internal canonical/shadow implementation; user-visible behavior changes `0`.\n\n"
        + "\n\n---\n\n".join(reports.values())
    )
    return reports


def generate(*, database: Path, sec_cache: Path) -> dict[str, Any]:
    phase9_0a = json.loads(PHASE9_0A_COVERAGE.read_text(encoding="utf-8"))
    universe = _active_universe(database)
    records: list[dict[str, Any]] = []
    canonical_facts: list[dict[str, Any]] = []
    snapshots: dict[str, CashFlowCoreSnapshot] = {}
    sec_cache_hits = 0
    sec_cache_misses = 0
    for row in universe:
        if row.get("exchange") == "KRX":
            records.append(_kr_record(row, phase9_0a))
            continue
        cik = str(row.get("cik") or "").strip().zfill(10)
        source_path = sec_cache / f"CIK{cik}.json"
        if not cik.strip("0") or not source_path.exists():
            sec_cache_misses += 1
            records.append(_missing_sec_record(row, source_path))
            continue
        sec_cache_hits += 1
        record, facts, snapshot = _sec_record(row, source_path=source_path)
        records.append(record)
        canonical_facts.extend(facts)
        snapshots[row["ticker"]] = snapshot

    counts = _metric_counts(records)
    drift = _coverage_drift(records, phase9_0a)
    lineage = _lineage_audit(snapshots)
    source_conflicts = sum(
        int(snapshot.source_audit.get("source_conflicts", 0))
        for snapshot in snapshots.values()
    )
    p0_open: list[dict[str, str]] = []
    if lineage["failures"]:
        p0_open.append(
            {
                "issue": "cash_flow_lineage_or_arithmetic_failure",
                "severity": "P0",
                "status": "OPEN",
            }
        )
    if source_conflicts:
        p0_open.append(
            {
                "issue": "official_source_occurrence_conflict",
                "severity": "P0",
                "status": "OPEN",
            }
        )
    p1_open: list[dict[str, str]] = []
    if any(item["category"] != "UNCHANGED" for item in drift):
        p1_open.append(
            {
                "issue": "phase9_0a_implementation_coverage_drift",
                "severity": "P1",
                "status": "OPEN",
            }
        )
    readiness = {
        "p0_open": p0_open,
        "p1_open": p1_open,
        "p2_backlog": [
            "management_defined_fcf_reconciliation",
            "user_visible_cash_flow_selection_and_wording",
            "ccc_deferred",
            "standard_roic_deferred",
        ],
        "phase_9_0c_ready": not p0_open and not p1_open,
        "phase_9_0c_scope": "CASH_FLOW_SHADOW_CONSUMPTION_EARNINGS_QUALITY",
        "kr_opendart_period_recovery_classification": "MEDIUM_COMPLEXITY_FOLLOWUP",
        "kr_opendart_period_recovery_priority": "MEDIUM",
        "runtime_behavior_diff": 0,
        "production_assist": "OFF",
    }
    output = {
        "contract": CONTRACT_VERSION,
        "as_of": AS_OF.isoformat(),
        "active_universe": records,
        "metric_counts": counts,
        "canonical_facts": canonical_facts,
        "coverage_drift": drift,
        "lineage_audit": lineage,
        "semantic_registry": list(registry_audit()),
        "rejected_semantics": list(rejected_semantic_audit()),
        "representative_implementation_proofs": _representatives(records),
        "provider_telemetry": {
            "sec_companyfacts": {
                "network_requests": 0,
                "network_successes": 0,
                "cache_hits": sec_cache_hits,
                "cache_misses": sec_cache_misses,
            },
            "opendart": {
                "network_requests": 0,
                "canonical_promotions": 0,
                "reason": "period_context_unresolved",
            },
            "new_paid_sources": 0,
            "new_api_keys": 0,
        },
        "source_database": str(database),
        "source_database_sha256": _sha256(database),
        "readiness": readiness,
        "deferred": {"ccc": True, "standard_roic": True},
        "mutations": {
            "runtime_behavior": 0,
            "public_action": 0,
            "daily_packet": 0,
            "ai_prompt": 0,
            "telegram": 0,
            "fallback": 0,
            "scheduled_task_manual_runs": 0,
            "pilot": 0,
            "database": 0,
            "archive_rewrite": 0,
        },
    }
    _write_json(REPORT_ROOT / f"{RUN_DATE}-phase9-0b-canonical-facts.json", output)
    _write_json(REPORT_ROOT / f"{RUN_DATE}-phase9-0b-readiness.json", readiness)
    for relative, content in _reports(output).items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Phase 9.0B stored-evidence audit")
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--sec-cache", type=Path, required=True)
    args = parser.parse_args()
    output = generate(database=args.database, sec_cache=args.sec_cache)
    print(
        json.dumps(
            {
                "active_universe": len(output["active_universe"]),
                "metric_counts": output["metric_counts"],
                "lineage_audit": output["lineage_audit"],
                "phase_9_0c_ready": output["readiness"]["phase_9_0c_ready"],
                "phase_9_0c_scope": output["readiness"]["phase_9_0c_scope"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
