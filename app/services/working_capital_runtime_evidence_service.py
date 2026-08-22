from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Mapping

from app.services.cash_flow_capital_efficiency_service import (
    EligibilityStatus,
    FinancialFact,
    Metric,
    financial_fact_from_mapping,
)
from app.services.working_capital_core_service import (
    CanonicalMovement,
    RelationDirection,
    WorkingCapitalCoreSnapshot,
    WorkingCapitalRelation,
)
from app.services.working_capital_evidence_service import (
    FreshnessState as CoreFreshnessState,
)


CANONICAL_FACTS_REPORT = "20260821-phase9-1b-canonical-facts.json"
ALLOWED_USER_VISIBLE_METRICS = frozenset({Metric.INVENTORY, Metric.TRADE_AR})


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def canonical_report_path() -> Path:
    return _repository_root() / "docs" / "reports" / CANONICAL_FACTS_REPORT


@lru_cache(maxsize=4)
def _read_report(path: str) -> dict[str, object]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Canonical working-capital report must be an object")
    return value


def _movement(
    row: Mapping[str, object], facts: Mapping[str, FinancialFact]
) -> CanonicalMovement:
    freshness = row.get("freshness_state")
    return CanonicalMovement(
        status=EligibilityStatus(str(row["status"])),
        balance_metric=Metric(str(row["metric"])),
        current=facts.get(str(row.get("current_fact_id") or "")),
        prior=facts.get(str(row.get("prior_fact_id") or "")),
        delta_fact=facts.get(str(row.get("delta_fact_id") or "")),
        yoy_fact=facts.get(str(row.get("yoy_fact_id") or "")),
        freshness_state=(
            CoreFreshnessState(str(freshness)) if freshness is not None else None
        ),
        denial_reasons=tuple(str(item) for item in row.get("denial_reasons") or ()),
        cautions=tuple(str(item) for item in row.get("cautions") or ()),
    )


def _relation(row: Mapping[str, object]) -> WorkingCapitalRelation:
    return WorkingCapitalRelation(
        status=EligibilityStatus(str(row["status"])),
        relation_id=(str(row["relation_id"]) if row.get("relation_id") else None),
        relation_type=str(row["relation_type"]),
        direction=(
            RelationDirection(str(row["direction"])) if row.get("direction") else None
        ),
        balance_metric=Metric(str(row["balance_metric"])),
        balance_semantic=(
            str(row["balance_semantic"]) if row.get("balance_semantic") else None
        ),
        balance_scope=(
            str(row["balance_scope"]) if row.get("balance_scope") else None
        ),
        flow_metric=Metric(str(row["flow_metric"])),
        flow_semantic=(str(row["flow_semantic"]) if row.get("flow_semantic") else None),
        gap_percentage_points=(
            Decimal(str(row["gap_percentage_points"]))
            if row.get("gap_percentage_points") is not None
            else None
        ),
        current_balance_fact_id=(
            str(row["current_balance_fact_id"])
            if row.get("current_balance_fact_id")
            else None
        ),
        prior_balance_fact_id=(
            str(row["prior_balance_fact_id"])
            if row.get("prior_balance_fact_id")
            else None
        ),
        current_flow_fact_id=(
            str(row["current_flow_fact_id"]) if row.get("current_flow_fact_id") else None
        ),
        prior_flow_fact_id=(
            str(row["prior_flow_fact_id"]) if row.get("prior_flow_fact_id") else None
        ),
        balance_yoy_fact_id=(
            str(row["balance_yoy_fact_id"]) if row.get("balance_yoy_fact_id") else None
        ),
        flow_yoy_fact_id=(
            str(row["flow_yoy_fact_id"]) if row.get("flow_yoy_fact_id") else None
        ),
        input_fact_ids=tuple(str(item) for item in row.get("input_fact_ids") or ()),
        formula=str(row["formula"]),
        derivation_version=str(row["derivation_version"]),
        denial_reasons=tuple(str(item) for item in row.get("denial_reasons") or ()),
        cautions=tuple(str(item) for item in row.get("cautions") or ()),
    )


def _snapshot(record: Mapping[str, object], *, as_of: date) -> WorkingCapitalCoreSnapshot:
    facts = {
        str(row["fact_id"]): financial_fact_from_mapping(row)
        for row in record.get("canonical_facts") or ()
        if isinstance(row, dict) and row.get("fact_id")
    }
    metric_rows = record.get("metrics")
    relation_rows = record.get("relations")
    latest = record.get("latest_safe_working_capital_date")
    return WorkingCapitalCoreSnapshot(
        issuer_id=str(record["issuer_id"]),
        as_of_date=as_of,
        latest_safe_working_capital_date=(date.fromisoformat(str(latest)) if latest else None),
        metric_states=tuple(
            _movement(row, facts)
            for row in (metric_rows.values() if isinstance(metric_rows, dict) else ())
            if isinstance(row, dict)
        ),
        relations=tuple(
            _relation(row)
            for row in (relation_rows.values() if isinstance(relation_rows, dict) else ())
            if isinstance(row, dict)
        ),
        canonical_facts=tuple(sorted(facts.values(), key=lambda item: item.fact_id)),
        industry_applicability=dict(record.get("industry_applicability") or {}),
        industry_status=EligibilityStatus(str(record["industry_status"])),
        denial_reasons=tuple(str(item) for item in record.get("denial_reasons") or ()),
        cautions=tuple(str(item) for item in record.get("cautions") or ()),
    )


def _is_allowed_movement(item: CanonicalMovement) -> bool:
    if (
        item.status != EligibilityStatus.ELIGIBLE
        or item.current is None
        or item.prior is None
    ):
        return False
    if item.balance_metric == Metric.TRADE_AR:
        return True
    if item.balance_metric != Metric.INVENTORY:
        return False
    return all(fact.balance_scope == "total" for fact in (item.current, item.prior))


def user_visible_scope(snapshot: WorkingCapitalCoreSnapshot) -> WorkingCapitalCoreSnapshot:
    movements = tuple(item for item in snapshot.metric_states if _is_allowed_movement(item))
    allowed = {item.balance_metric for item in movements}
    relations = tuple(
        item
        for item in snapshot.relations
        if item.balance_metric in allowed
        and item.balance_metric in ALLOWED_USER_VISIBLE_METRICS
        and (item.balance_metric != Metric.INVENTORY or item.balance_scope == "total")
    )
    return WorkingCapitalCoreSnapshot(
        issuer_id=snapshot.issuer_id,
        as_of_date=snapshot.as_of_date,
        latest_safe_working_capital_date=snapshot.latest_safe_working_capital_date,
        metric_states=movements,
        relations=relations,
        canonical_facts=snapshot.canonical_facts,
        industry_applicability=snapshot.industry_applicability,
        industry_status=snapshot.industry_status,
        denial_reasons=snapshot.denial_reasons,
        cautions=snapshot.cautions,
    )


def load_working_capital_snapshot(
    ticker: str,
    *,
    as_of: date,
    report_path: Path | None = None,
) -> tuple[WorkingCapitalCoreSnapshot, dict[str, object]] | None:
    path = (report_path or canonical_report_path()).resolve()
    if not path.exists():
        return None
    payload = _read_report(str(path))
    record = next(
        (
            item
            for item in payload.get("active_universe") or ()
            if isinstance(item, dict) and str(item.get("ticker")) == ticker
        ),
        None,
    )
    if not isinstance(record, dict):
        return None
    return user_visible_scope(_snapshot(record, as_of=as_of)), dict(record)
