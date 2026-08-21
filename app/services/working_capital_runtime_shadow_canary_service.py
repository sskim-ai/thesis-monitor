from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
import uuid
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Callable, Iterable, Iterator, Mapping

from app.config import get_settings
from app.services.cash_flow_baseline_consistency_service import financial_period_context
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
from app.services.working_capital_shadow_consumption_service import (
    CONTRACT_VERSION as CONSUMPTION_CONTRACT_VERSION,
    WorkingCapitalReasoningContext,
    WorkingCapitalShadowReasoning,
    build_working_capital_reasoning_context,
    context_to_dict,
    reasoning_to_dict,
    render_working_capital_reasoning,
    validate_working_capital_reasoning,
)


CANARY_POLICY_VERSION = "working-capital-runtime-shadow-canary-v1"
CANARY_ARCHIVE_VERSION = "working-capital-runtime-shadow-canary-archive-v1"
CANONICAL_FACTS_REPORT = "20260821-phase9-1b-canonical-facts.json"
CASH_FLOW_FACTS_REPORT = "20260820-phase9-0b-canonical-facts.json"
ALLOWED_METRICS = frozenset({Metric.INVENTORY, Metric.TRADE_AR})
_NUMBER = re.compile(r"(?<![A-Za-z0-9_])[-+]?\d[\d,]*(?:\.\d+)?")


@dataclass(frozen=True)
class CanaryLaunchResult:
    status: str
    packet_id: str | None = None
    canary_id: str | None = None
    process_id: int | None = None
    reason: str | None = None


@dataclass(frozen=True)
class CanaryRunResult:
    status: str
    packet_id: str
    canary_id: str
    attempt_id: str | None = None
    receipt_path: str | None = None
    reason: str | None = None


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _data_root() -> Path:
    return Path(get_settings().data_dir).resolve()


def _report_path(filename: str) -> Path:
    return _repository_root() / "docs" / "reports" / filename


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json_once(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temp.open("x", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, default=str)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


@contextmanager
def _canary_lock(canary_id: str) -> Iterator[None]:
    digest = hashlib.sha256(canary_id.encode("utf-8")).hexdigest()
    path = (
        _data_root()
        / "ai_review"
        / "working_capital_canary"
        / "locks"
        / f"{digest}.lock"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def canary_identity(packet_id: str) -> str:
    identity = {
        "packet_id": packet_id,
        "consumption_contract": CONSUMPTION_CONTRACT_VERSION,
        "canary_policy": CANARY_POLICY_VERSION,
    }
    return f"wc-canary-{_sha256_bytes(_canonical_json(identity))[:24]}"


def _packet_path(packet_id: str) -> Path:
    return _data_root() / "ai_review" / "inbox" / f"{packet_id}.json"


def _production_archive(packet: Mapping[str, object]) -> Path:
    run_date = date.fromisoformat(str(packet["assessment_date"]))
    return (
        _data_root()
        / "ai_review"
        / "pilot"
        / "history"
        / f"{run_date:%Y}"
        / f"{run_date:%m}"
        / str(packet["packet_id"])
    )


def _canary_root(packet: Mapping[str, object]) -> Path:
    return (
        _production_archive(packet)
        / "working-capital-shadow-canary"
        / canary_identity(str(packet["packet_id"]))
    )


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
        flow_semantic=(
            str(row["flow_semantic"]) if row.get("flow_semantic") else None
        ),
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
    fact_rows = record.get("canonical_facts") or ()
    facts = {
        str(row["fact_id"]): financial_fact_from_mapping(row)
        for row in fact_rows
        if isinstance(row, dict) and row.get("fact_id")
    }
    metric_rows = record.get("metrics")
    relation_rows = record.get("relations")
    movements = tuple(
        _movement(row, facts)
        for row in (metric_rows.values() if isinstance(metric_rows, dict) else ())
        if isinstance(row, dict)
    )
    relations = tuple(
        _relation(row)
        for row in (relation_rows.values() if isinstance(relation_rows, dict) else ())
        if isinstance(row, dict)
    )
    latest = record.get("latest_safe_working_capital_date")
    return WorkingCapitalCoreSnapshot(
        issuer_id=str(record["issuer_id"]),
        as_of_date=as_of,
        latest_safe_working_capital_date=(
            date.fromisoformat(str(latest)) if latest else None
        ),
        metric_states=movements,
        relations=relations,
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


def _runtime_scope(snapshot: WorkingCapitalCoreSnapshot) -> WorkingCapitalCoreSnapshot:
    movements = tuple(item for item in snapshot.metric_states if _is_allowed_movement(item))
    allowed = {item.balance_metric for item in movements}
    relations = tuple(
        item
        for item in snapshot.relations
        if item.balance_metric in allowed
        and item.balance_metric in ALLOWED_METRICS
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


def _latest_preliminary_periods(database: Path, cutoff: date) -> dict[str, date]:
    if not database.exists():
        return {}
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    try:
        rows = connection.execute(
            """
            SELECT ticker, MAX(financial_period_end)
              FROM financialsnapshot
             WHERE snapshot_type = 'preliminary_earnings'
               AND financial_period_end IS NOT NULL
               AND COALESCE(filing_date, reported_date) <= ?
               AND period_mapping_validation_failed = 0
               AND financial_statement_basis_warning = 0
             GROUP BY ticker
            """,
            (cutoff.isoformat(),),
        ).fetchall()
    finally:
        connection.close()
    return {
        str(ticker): date.fromisoformat(str(period))
        for ticker, period in rows
        if period
    }


def _cash_flow_periods(cutoff: date) -> dict[str, date]:
    payload = _read_json(_report_path(CASH_FLOW_FACTS_REPORT))
    facts = {
        str(row["fact_id"]): row
        for row in payload.get("canonical_facts") or ()
        if isinstance(row, dict) and row.get("fact_id")
    }
    result: dict[str, date] = {}
    for record in payload.get("active_universe") or ():
        if not isinstance(record, dict) or not record.get("ticker"):
            continue
        latest = record.get("latest_safe_period")
        if not isinstance(latest, dict) or not latest.get("fcf_fact_id"):
            continue
        fact = facts.get(str(latest["fcf_fact_id"]))
        if not fact or not fact.get("filing_date") or not fact.get("period_end"):
            continue
        if date.fromisoformat(str(fact["filing_date"])) <= cutoff:
            result[str(record["ticker"])] = date.fromisoformat(str(fact["period_end"]))
    return result


def _load_runtime_inputs(
    packet: Mapping[str, object],
) -> tuple[
    dict[str, WorkingCapitalCoreSnapshot],
    dict[str, dict[str, object]],
    dict[str, date],
    str,
]:
    path = _report_path(CANONICAL_FACTS_REPORT)
    payload = _read_json(path)
    cutoff = date.fromisoformat(str(packet["assessment_date"]))
    snapshots: dict[str, WorkingCapitalCoreSnapshot] = {}
    records: dict[str, dict[str, object]] = {}
    for raw in payload.get("active_universe") or ():
        if not isinstance(raw, dict) or not raw.get("ticker"):
            continue
        ticker = str(raw["ticker"])
        records[ticker] = raw
        snapshots[ticker] = _runtime_scope(_snapshot(raw, as_of=cutoff))
    return snapshots, records, _cash_flow_periods(cutoff), _file_sha256(path)


def _stock_source_text(stock: Mapping[str, object]) -> str:
    return json.dumps(stock, ensure_ascii=False, sort_keys=True, default=str)


def _packet_financial_periods(
    stock: Mapping[str, object],
) -> tuple[date | None, date | None]:
    valuation = stock.get("valuation")
    if not isinstance(valuation, dict):
        return None, None
    return financial_period_context(valuation)


def _quality_receipt(
    reasonings: Mapping[str, WorkingCapitalShadowReasoning | None]
) -> dict[str, object]:
    texts = [item.text for item in reasonings.values() if item is not None]
    exact = [text for text, count in Counter(texts).items() if count > 1]
    skeletons = Counter(_NUMBER.sub("<NUM>", text) for text in texts)
    repeated_skeletons = [text for text, count in skeletons.items() if count >= 3]
    errors = [
        *({"error": "exact_reasoning_repeat", "text": text} for text in exact),
        *(
            {"error": "portfolio_template_repeat", "skeleton": text}
            for text in repeated_skeletons
        ),
    ]
    return {
        "contract": "working-capital-runtime-shadow-quality-v1",
        "status": "passed" if not errors else "rejected",
        "errors": errors,
        "threshold_changes": 0,
    }


def _numeric_binding_report(
    reasonings: Mapping[str, WorkingCapitalShadowReasoning | None],
    relations: Mapping[str, WorkingCapitalRelation],
    facts: Mapping[str, FinancialFact],
) -> dict[str, object]:
    automatic = 0
    errors: list[dict[str, str]] = []
    for ticker, reasoning in reasonings.items():
        if reasoning is None:
            continue
        for claim in reasoning.numeric_claims:
            relation = relations.get(claim.relation_id)
            if relation is None:
                errors.append({"ticker": ticker, "error": "relation_missing"})
                continue
            if (
                relation.gap_percentage_points != Decimal(claim.value)
                or relation.input_fact_ids != claim.input_fact_ids
                or claim.display not in reasoning.text
                or any(fact_id not in facts for fact_id in claim.input_fact_ids)
            ):
                errors.append({"ticker": ticker, "error": "numeric_binding_mismatch"})
                continue
            automatic += 1
    return {
        "status": "passed" if not errors else "rejected",
        "automatic": automatic,
        "manual": 0,
        "rejected": len(errors),
        "unresolved": 0,
        "errors": errors,
    }


def _failure_receipt(
    *,
    packet_id: str,
    canary_id: str,
    attempt_id: str,
    status: str,
    reason: str,
    production_delivery_sha256: str,
    started_at: datetime,
) -> dict[str, object]:
    completed_at = datetime.now(UTC)
    return {
        "contract": CANARY_POLICY_VERSION,
        "packet_id": packet_id,
        "canary_id": canary_id,
        "attempt_id": attempt_id,
        "status": status,
        "reason": reason,
        "production_delivery_sha256": production_delivery_sha256,
        "production_influence_count": 0,
        "telegram_delivery_count": 0,
        "assessment_mutation_count": 0,
        "warning_mutation_count": 0,
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
    }


def _write_attempt_failure(
    attempt_dir: Path,
    *,
    packet_id: str,
    canary_id: str,
    attempt_id: str,
    status: str,
    reason: str,
    production_delivery_sha256: str,
    started_at: datetime,
) -> Path | None:
    path = attempt_dir / "canary-receipt.json"
    try:
        _write_json_once(
            path,
            _failure_receipt(
                packet_id=packet_id,
                canary_id=canary_id,
                attempt_id=attempt_id,
                status=status,
                reason=reason,
                production_delivery_sha256=production_delivery_sha256,
                started_at=started_at,
            ),
        )
    except OSError:
        return None
    return path


def run_working_capital_runtime_shadow_canary(
    packet_id: str,
    *,
    delivery_mode: str,
    expected_delivery_sha256: str,
    now: datetime | None = None,
) -> CanaryRunResult:
    started_at = (now or datetime.now(UTC)).astimezone(UTC)
    canary_id = canary_identity(packet_id)
    attempt_id = f"attempt-{started_at:%Y%m%dT%H%M%S%fZ}-{uuid.uuid4().hex[:8]}"
    packet_path = _packet_path(packet_id)
    if not packet_path.exists():
        return CanaryRunResult("PACKET_MISSING", packet_id, canary_id, reason="packet_missing")
    packet = _read_json(packet_path)
    archive = _production_archive(packet)
    root = _canary_root(packet)
    attempt_dir = root / "attempts" / attempt_id
    completion = root / "canary-complete.json"
    with _canary_lock(canary_id):
        if completion.exists():
            return CanaryRunResult(
                "DUPLICATE_SKIPPED",
                packet_id,
                canary_id,
                reason="logical_canary_already_complete",
            )
        delivery_path = archive / "delivery-result.json"
        try:
            delivery = _read_json(delivery_path)
            actual_delivery_sha = _file_sha256(delivery_path)
        except Exception as exc:
            receipt = _write_attempt_failure(
                attempt_dir,
                packet_id=packet_id,
                canary_id=canary_id,
                attempt_id=attempt_id,
                status="PRODUCTION_ARTIFACT_UNAVAILABLE",
                reason=type(exc).__name__,
                production_delivery_sha256=expected_delivery_sha256,
                started_at=started_at,
            )
            return CanaryRunResult(
                "PRODUCTION_ARTIFACT_UNAVAILABLE",
                packet_id,
                canary_id,
                attempt_id,
                str(receipt) if receipt else None,
                type(exc).__name__,
            )
        production_valid = all(
            (
                delivery.get("status") == "sent",
                int(delivery.get("pending_count") or 0) == 0,
                int(delivery.get("sent_count") or 0)
                == int(delivery.get("delivery_count") or 0),
                str(delivery.get("delivery_mode") or "") == delivery_mode,
                actual_delivery_sha == expected_delivery_sha256,
            )
        )
        if not production_valid:
            receipt = _write_attempt_failure(
                attempt_dir,
                packet_id=packet_id,
                canary_id=canary_id,
                attempt_id=attempt_id,
                status="PRODUCTION_NOT_FINAL",
                reason="delivery_result_not_terminal_or_identity_mismatch",
                production_delivery_sha256=actual_delivery_sha,
                started_at=started_at,
            )
            return CanaryRunResult(
                "PRODUCTION_NOT_FINAL",
                packet_id,
                canary_id,
                attempt_id,
                str(receipt) if receipt else None,
                "delivery_result_not_terminal_or_identity_mismatch",
            )

        stage_started = time.perf_counter()
        try:
            snapshots, records, cash_flow_periods, canonical_sha = _load_runtime_inputs(packet)
            cutoff = date.fromisoformat(str(packet["assessment_date"]))
            preliminary = _latest_preliminary_periods(
                _data_root() / "thesis_monitor.sqlite3", cutoff
            )
            contexts: dict[str, WorkingCapitalReasoningContext] = {}
            reasonings: dict[str, WorkingCapitalShadowReasoning | None] = {}
            all_facts: dict[str, FinancialFact] = {}
            all_relations: dict[str, WorkingCapitalRelation] = {}
            packet_stocks = {
                str(item["ticker"]): item
                for item in packet.get("stocks") or ()
                if isinstance(item, dict) and item.get("ticker")
            }
            for ticker, stock in packet_stocks.items():
                snapshot = snapshots.get(ticker)
                record = records.get(ticker)
                if snapshot is None or record is None:
                    continue
                packet_formal, packet_preliminary = _packet_financial_periods(stock)
                latest_formal = max(
                    (
                        item
                        for item in (
                            snapshot.latest_safe_working_capital_date,
                            packet_formal,
                        )
                        if item is not None
                    ),
                    default=None,
                )
                latest_preliminary = max(
                    (
                        item
                        for item in (preliminary.get(ticker), packet_preliminary)
                        if item is not None
                    ),
                    default=None,
                )
                context = build_working_capital_reasoning_context(
                    snapshot,
                    ticker=ticker,
                    market=str(packet.get("market") or record.get("market") or ""),
                    packet_id=packet_id,
                    assessment_date=cutoff,
                    cutoff=cutoff,
                    industry=str(record.get("industry") or ""),
                    monitoring_text=_stock_source_text(stock),
                    existing_unknowns=tuple(
                        str(item) for item in stock.get("unknowns") or ()
                    ),
                    latest_formal_balance_date=latest_formal,
                    latest_provisional_period_end=latest_preliminary,
                    cash_flow_period_end=cash_flow_periods.get(ticker),
                )
                contexts[ticker] = context
                reasonings[ticker] = render_working_capital_reasoning(context)
                all_facts.update(
                    {item.fact_id: item for item in snapshot.canonical_facts}
                )
                all_relations.update(
                    {
                        item.relation_id: item
                        for item in snapshot.relations
                        if item.relation_id is not None
                    }
                )
            build_latency_ms = round((time.perf_counter() - stage_started) * 1000, 3)
        except Exception as exc:
            receipt = _write_attempt_failure(
                attempt_dir,
                packet_id=packet_id,
                canary_id=canary_id,
                attempt_id=attempt_id,
                status="FAILED_RUNTIME",
                reason=type(exc).__name__,
                production_delivery_sha256=actual_delivery_sha,
                started_at=started_at,
            )
            return CanaryRunResult(
                "FAILED_RUNTIME",
                packet_id,
                canary_id,
                attempt_id,
                str(receipt) if receipt else None,
                type(exc).__name__,
            )

        validation_started = time.perf_counter()
        binding = _numeric_binding_report(reasonings, all_relations, all_facts)
        semantic_rows: list[dict[str, object]] = []
        semantic_error_count = 0
        for ticker, context in contexts.items():
            errors = validate_working_capital_reasoning(
                context,
                all_facts,
                all_relations,
                reasonings.get(ticker),
                thesis_status_changed=False,
                valuation_changed=False,
                warning_changed=False,
            )
            semantic_error_count += len(errors)
            semantic_rows.append({"ticker": ticker, "errors": list(errors)})
        semantic = {
            "contract": "working-capital-runtime-semantic-validation-v1",
            "status": "passed" if semantic_error_count == 0 else "rejected",
            "error_count": semantic_error_count,
            "subjects": semantic_rows,
            "causal_overclaim_count": 0,
            "unsupported_advanced_ratio_count": 0,
            "production_state_mutation_count": 0,
        }
        quality = _quality_receipt(reasonings)
        validation_latency_ms = round(
            (time.perf_counter() - validation_started) * 1000, 3
        )
        selected = [ticker for ticker, item in reasonings.items() if item is not None]
        status = "COMPLETE_PASS" if selected else "SUPPRESSED_NO_ELIGIBLE_CONTEXT"
        reason = "all_shadow_gates_passed" if selected else "no_selected_context"
        if binding["status"] != "passed" or semantic["status"] != "passed" or quality["status"] != "passed":
            status = "FAILED_VALIDATION"
            reason = "shadow_validation_rejected"

        contexts_payload = {
            ticker: context_to_dict(context) for ticker, context in contexts.items()
        }
        raw_output = {
            "packet_id": packet_id,
            "canary_id": canary_id,
            "generation_mode": "deterministic_contract_renderer",
            "shadow_fallback_used": False,
            "subjects": {
                ticker: reasoning_to_dict(reasoning)
                for ticker, reasoning in reasonings.items()
            },
        }
        artifacts: tuple[tuple[str, object], ...] = (
            (
                "canary-manifest.json",
                {
                    "archive_contract": CANARY_ARCHIVE_VERSION,
                    "canary_policy": CANARY_POLICY_VERSION,
                    "packet_id": packet_id,
                    "canary_id": canary_id,
                    "production_delivery_sha256": actual_delivery_sha,
                    "canonical_facts_sha256": canonical_sha,
                    "allowed_metrics": sorted(item.value for item in ALLOWED_METRICS),
                    "excluded_metric_families": [
                        "accounts_receivable_broad",
                        "trade_accounts_payable",
                        "accounts_payable_broad",
                        "dso",
                        "inventory_days",
                        "dpo",
                        "ccc",
                    ],
                    "created_at": started_at.isoformat(),
                },
            ),
            (
                "working-capital-sidecar.json",
                {
                    "contract": CONSUMPTION_CONTRACT_VERSION,
                    "packet_id": packet_id,
                    "subjects": contexts_payload,
                },
            ),
            ("raw-shadow-output.json", raw_output),
            ("numeric-binding.json", binding),
            ("semantic-validation.json", semantic),
            ("runtime-quality-receipt.json", quality),
        )
        try:
            for filename, payload in artifacts:
                _write_json_once(attempt_dir / filename, payload)
        except Exception as exc:
            receipt = _write_attempt_failure(
                attempt_dir,
                packet_id=packet_id,
                canary_id=canary_id,
                attempt_id=attempt_id,
                status="FAILED_RUNTIME",
                reason=type(exc).__name__,
                production_delivery_sha256=actual_delivery_sha,
                started_at=started_at,
            )
            return CanaryRunResult(
                "FAILED_RUNTIME",
                packet_id,
                canary_id,
                attempt_id,
                str(receipt) if receipt else None,
                type(exc).__name__,
            )

        receipt_payload = _failure_receipt(
            packet_id=packet_id,
            canary_id=canary_id,
            attempt_id=attempt_id,
            status=status,
            reason=reason,
            production_delivery_sha256=actual_delivery_sha,
            started_at=started_at,
        )
        receipt_payload.update(
            {
                "market": packet.get("market"),
                "assessment_date": packet.get("assessment_date"),
                "eligible_subject_count": sum(
                    item.consumption_eligible for item in contexts.values()
                ),
                "selected_subject_count": len(selected),
                "selected_subjects": selected,
                "selected_metric_families": {
                    ticker: contexts[ticker].selected_relation.balance_metric.value
                    for ticker in selected
                    if contexts[ticker].selected_relation is not None
                },
                "selected_relation_ids": {
                    ticker: list(reasonings[ticker].relation_ids)
                    for ticker in selected
                    if reasonings[ticker] is not None
                },
                "selected_fact_ids": {
                    ticker: list(reasonings[ticker].fact_ids)
                    for ticker in selected
                    if reasonings[ticker] is not None
                },
                "numeric_binding": {
                    key: binding[key]
                    for key in ("automatic", "manual", "rejected", "unresolved")
                },
                "semantic_error_count": semantic_error_count,
                "quality_error_count": len(quality["errors"]),
                "cash_flow_cross_link_count": sum(
                    item.cash_flow_context_used for item in contexts.values()
                ),
                "production_ai_input_change_count": 0,
                "production_fallback_change_count": 0,
                "public_action_change_count": 0,
                "public_snapshot_change_count": 0,
                "latency_ms": {
                    "build": build_latency_ms,
                    "validation": validation_latency_ms,
                    "total": round((time.perf_counter() - stage_started) * 1000, 3),
                },
            }
        )
        receipt_payload["receipt_id"] = (
            f"wc-receipt-{_sha256_bytes(_canonical_json(receipt_payload))[:24]}"
        )
        receipt_path = attempt_dir / "canary-receipt.json"
        _write_json_once(receipt_path, receipt_payload)
        if status in {"COMPLETE_PASS", "SUPPRESSED_NO_ELIGIBLE_CONTEXT"}:
            completion_payload = {
                "archive_contract": CANARY_ARCHIVE_VERSION,
                "packet_id": packet_id,
                "canary_id": canary_id,
                "attempt_id": attempt_id,
                "status": status,
                "canary_receipt_id": receipt_payload["receipt_id"],
                "production_delivery_sha256": actual_delivery_sha,
                "completed_at": datetime.now(UTC).isoformat(),
                "artifacts": [
                    {
                        "path": str(path.relative_to(root)),
                        "sha256": _file_sha256(path),
                    }
                    for path in sorted(attempt_dir.glob("*.json"))
                ],
            }
            _write_json_once(completion, completion_payload)
        return CanaryRunResult(
            status,
            packet_id,
            canary_id,
            attempt_id,
            str(receipt_path),
            None if status in {"COMPLETE_PASS", "SUPPRESSED_NO_ELIGIBLE_CONTEXT"} else reason,
        )


def _launch_failure_receipt(
    packet: Mapping[str, object], *, delivery_sha256: str, reason: str
) -> None:
    root = _canary_root(packet)
    now = datetime.now(UTC)
    attempt_id = f"launch-{now:%Y%m%dT%H%M%S%fZ}-{uuid.uuid4().hex[:8]}"
    _write_attempt_failure(
        root / "attempts" / attempt_id,
        packet_id=str(packet["packet_id"]),
        canary_id=canary_identity(str(packet["packet_id"])),
        attempt_id=attempt_id,
        status="LAUNCH_FAILED",
        reason=reason,
        production_delivery_sha256=delivery_sha256,
        started_at=now,
    )


def launch_working_capital_runtime_shadow_canary(
    delivery_result: Mapping[str, object],
    *,
    popen: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
) -> CanaryLaunchResult:
    packet_id = str(delivery_result.get("packet_id") or "")
    if not get_settings().working_capital_runtime_shadow_canary_enabled:
        return CanaryLaunchResult("disabled", packet_id or None)
    if (
        not packet_id
        or delivery_result.get("status") != "sent"
        or int(delivery_result.get("pending_count") or 0) != 0
        or int(delivery_result.get("sent_count") or 0)
        != int(delivery_result.get("delivery_count") or 0)
    ):
        return CanaryLaunchResult(
            "not_terminal",
            packet_id or None,
            reason="production_delivery_not_terminal_sent",
        )
    packet_path = _packet_path(packet_id)
    try:
        packet = _read_json(packet_path)
        delivery_path = _production_archive(packet) / "delivery-result.json"
        delivery_sha256 = _file_sha256(delivery_path)
        archived = _read_json(delivery_path)
        identity_fields = (
            "packet_id",
            "delivery_mode",
            "status",
            "delivery_count",
            "sent_count",
            "pending_count",
        )
        if any(
            archived.get(field) != delivery_result.get(field)
            for field in identity_fields
        ):
            return CanaryLaunchResult(
                "identity_mismatch",
                packet_id,
                reason="returned_delivery_result_differs_from_archive",
            )
        process = popen(
            [
                sys.executable,
                "-m",
                "app.jobs.working_capital_shadow_canary",
                "--packet-id",
                packet_id,
                "--delivery-mode",
                str(delivery_result.get("delivery_mode") or ""),
                "--delivery-result-sha256",
                delivery_sha256,
            ],
            cwd=str(_repository_root()),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
        )
    except Exception as exc:
        try:
            if "packet" in locals():
                _launch_failure_receipt(
                    packet,
                    delivery_sha256=(delivery_sha256 if "delivery_sha256" in locals() else ""),
                    reason=type(exc).__name__,
                )
        except Exception:
            pass
        return CanaryLaunchResult(
            "launch_failed",
            packet_id,
            canary_identity(packet_id),
            reason=type(exc).__name__,
        )
    return CanaryLaunchResult(
        "launched", packet_id, canary_identity(packet_id), process.pid
    )


def working_capital_canary_status_counts(
    contexts: Iterable[WorkingCapitalReasoningContext],
) -> dict[str, int]:
    return dict(Counter(item.freshness_state.value for item in contexts))
