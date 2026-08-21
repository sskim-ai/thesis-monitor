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
import calendar
from collections import Counter, defaultdict
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Callable, Iterable, Iterator, Mapping, Sequence

from app.config import get_settings
from app.services.cash_flow_baseline_consistency_service import (
    CONTRACT_VERSION as BASELINE_CONSISTENCY_CONTRACT_VERSION,
    consistency_error,
    decision_to_dict,
    evidence_from_shadow_context,
    repair_baseline_cash_flow_text,
    rendered_message_cash_flow_sections,
)
from app.services.cash_flow_capital_efficiency_service import (
    CapexScope,
    EligibilityStatus,
    FactType,
    FinancialFact,
    Metric,
    PeriodIdentity,
    PeriodType,
)
from app.services.cash_flow_shadow_consumption_service import (
    CONTRACT_VERSION as CONSUMPTION_CONTRACT_VERSION,
    CashFlowReasoningContext,
    ShadowReasoning,
    build_cash_flow_reasoning_context,
    context_to_dict,
    reasoning_to_dict,
    render_shadow_reasoning,
    resolve_cash_flow_unknowns,
    validate_shadow_reasoning,
)


CANARY_POLICY_VERSION = "cash-flow-runtime-shadow-canary-v1"
CANARY_ARCHIVE_VERSION = "cash-flow-runtime-shadow-canary-archive-v1"
CANONICAL_FACTS_REPORT = "20260820-phase9-0b-canonical-facts.json"
ARCHITECTURE_REPORT = "20260820-phase9-0a-coverage.json"
_DATE = re.compile(r"20\d{2}-\d{2}-\d{2}")
_NUMBER = re.compile(r"(?<![A-Za-z0-9_])[-+]?\d[\d,]*(?:\.\d+)?")
_SPACE = re.compile(r"\s+")
_SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+")


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


ShadowGenerator = Callable[
    [
        Mapping[str, CashFlowReasoningContext],
        Mapping[str, FinancialFact],
        Mapping[str, str],
        Mapping[str, str],
    ],
    Mapping[str, ShadowReasoning | None],
]


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _data_root() -> Path:
    return Path(get_settings().data_dir).resolve()


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
    path = _data_root() / "ai_review" / "cash_flow_canary" / "locks" / f"{digest}.lock"
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
    return f"cf-canary-{_sha256_bytes(_canonical_json(identity))[:24]}"


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
    return _production_archive(packet) / "cash-flow-shadow-canary" / canary_identity(
        str(packet["packet_id"])
    )


def _report_path(filename: str) -> Path:
    return _repository_root() / "docs" / "reports" / filename


def _as_date(value: object) -> date | None:
    if not value:
        return None
    text = str(value)
    try:
        return date.fromisoformat(text)
    except ValueError:
        match = re.search(r"(20\d{2})\.(\d{2})", text)
        if match is None:
            return None
        year = int(match.group(1))
        month = int(match.group(2))
        return date(year, month, calendar.monthrange(year, month)[1])


def _fact(row: Mapping[str, object]) -> FinancialFact:
    capex_scope = row.get("capex_scope")
    return FinancialFact(
        fact_id=str(row["fact_id"]),
        issuer_id=str(row["issuer_id"]),
        metric=Metric(str(row["metric"])),
        value=Decimal(str(row["value"])),
        currency=str(row["currency"]),
        unit=str(row["unit"]),
        period=PeriodIdentity(
            start=date.fromisoformat(str(row["period_start"])),
            end=date.fromisoformat(str(row["period_end"])),
            period_type=PeriodType(str(row["period_type"])),
            fiscal_year=int(row["fiscal_year"]),
            fiscal_quarter=(
                int(row["fiscal_quarter"])
                if row.get("fiscal_quarter") is not None
                else None
            ),
        ),
        entity_scope=str(row["entity_scope"]),
        statement_basis=str(row["statement_basis"]),
        reported_or_derived=str(row["reported_or_derived"]),
        source_provider=str(row["source_provider"]),
        source_document_id=str(row["source_document_id"]),
        filing_date=date.fromisoformat(str(row["filing_date"])),
        source_occurrence_id=str(row["source_occurrence_id"]),
        raw_payload_sha256=str(row["raw_payload_sha256"]),
        semantic_mapping=str(row.get("semantic_mapping") or ""),
        fact_type=FactType(str(row["fact_type"])),
        source_document_type=(
            str(row["source_document_type"])
            if row.get("source_document_type") is not None
            else None
        ),
        source_semantic=(
            str(row["source_semantic"])
            if row.get("source_semantic") is not None
            else None
        ),
        source_reported_value=(
            Decimal(str(row["source_reported_value"]))
            if row.get("source_reported_value") is not None
            else None
        ),
        source_reported_unit=(
            str(row["source_reported_unit"])
            if row.get("source_reported_unit") is not None
            else None
        ),
        source_sign=(
            str(row["source_sign"]) if row.get("source_sign") is not None else None
        ),
        normalization_transform=(
            str(row["normalization_transform"])
            if row.get("normalization_transform") is not None
            else None
        ),
        capex_scope=CapexScope(str(capex_scope)) if capex_scope else None,
        derivation_formula=(
            str(row["derivation_formula"])
            if row.get("derivation_formula") is not None
            else None
        ),
        derivation_version=(
            str(row["derivation_version"])
            if row.get("derivation_version") is not None
            else None
        ),
        input_fact_ids=tuple(str(item) for item in row.get("input_fact_ids") or ()),
        quality=str(row.get("quality") or "REPORTED_VERIFIED"),
        eligibility=EligibilityStatus(str(row.get("eligibility") or "ELIGIBLE")),
        denial_reason=(
            str(row["denial_reason"])
            if row.get("denial_reason") is not None
            else None
        ),
        cautions=tuple(str(item) for item in row.get("cautions") or ()),
        as_of_date=_as_date(row.get("as_of_date")),
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


def _operating_earnings_period(stock: Mapping[str, object]) -> date | None:
    values: list[date] = []
    for item in stock.get("fact_catalog") or ():
        if not isinstance(item, dict):
            continue
        if not str(item.get("fact_type") or "").startswith("financial"):
            continue
        value = _as_date(item.get("as_of_date"))
        if value is not None:
            values.append(value)
    return max(values, default=None)


def _stock_source_text(stock: Mapping[str, object]) -> str:
    values: list[str] = [
        str(stock.get("industry") or ""),
        str(stock.get("sector") or ""),
        str(stock.get("business_model") or ""),
        str(stock.get("revenue_sources") or ""),
    ]
    for key in (
        "thesis",
        "industry_reasoning_plan",
        "runtime_specificity_plan",
        "previous_assessment",
    ):
        value = stock.get(key)
        if isinstance(value, dict):
            values.append(json.dumps(value, ensure_ascii=False, sort_keys=True))
    values.extend(str(item) for item in stock.get("unknowns") or ())
    return " ".join(value for value in values if value)


def _packet_sha(packet_path: Path) -> str:
    return _file_sha256(packet_path)


def _production_candidate_identity(archive: Path) -> str | None:
    candidate = archive / "ai-review.json"
    return _file_sha256(candidate) if candidate.exists() else None


def _production_message_texts(
    archive: Path,
    delivery_mode: str,
) -> dict[str, str]:
    candidates = (
        ("ai-assisted-messages.json",)
        if delivery_mode == "ai_assisted"
        else ("fallback-messages.json", "deterministic-messages.json")
    )
    for filename in candidates:
        path = archive / filename
        if not path.exists():
            continue
        value = _read_json(path)
        output: dict[str, str] = {}
        for item in value.get("messages") or ():
            if not isinstance(item, dict) or not item.get("ticker"):
                continue
            payload = item.get("payload")
            text = (
                payload.get("text")
                if isinstance(payload, dict)
                else item.get("text")
            )
            if isinstance(text, str):
                output[str(item["ticker"])] = text
        if output:
            return output
    return {}


def _baseline_consistency_audit(
    packet_stocks: Mapping[str, Mapping[str, object]],
    contexts: Mapping[str, CashFlowReasoningContext],
    facts: Mapping[str, FinancialFact],
    *,
    archive: Path,
    delivery_mode: str,
) -> dict[str, object]:
    production_texts = _production_message_texts(archive, delivery_mode)
    rows: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    for ticker, context in contexts.items():
        stock = packet_stocks.get(ticker, {})
        thesis = stock.get("thesis") if isinstance(stock, dict) else None
        sources: list[tuple[str, str, str]] = []
        if isinstance(thesis, dict) and isinstance(thesis.get("core_thesis"), str):
            sources.append(
                (
                    "packet.thesis.core_thesis",
                    "core_thesis",
                    str(thesis["core_thesis"]),
                )
            )
        production_text = production_texts.get(ticker)
        if production_text:
            sources.extend(
                (
                    f"production_delivery.{heading}",
                    section,
                    value,
                )
                for heading, section, value in rendered_message_cash_flow_sections(
                    production_text
                )
            )
        evidence = evidence_from_shadow_context(context, facts)
        for text_ref, section, value in sources:
            repair = repair_baseline_cash_flow_text(
                ticker,
                value,
                evidence,
                text_ref=text_ref,
                section=section,
                origin_type=(
                    "production_delivery" if section == "production_delivery" else "packet"
                ),
            )
            for decision in repair.decisions:
                row = decision_to_dict(decision)
                rows.append(row)
                error = consistency_error(decision)
                if error:
                    errors.append(
                        {
                            "ticker": ticker,
                            "text_ref": text_ref,
                            "error": error,
                            "claim_id": decision.claim.claim_id,
                        }
                    )
    return {
        "contract": BASELINE_CONSISTENCY_CONTRACT_VERSION,
        "status": "passed" if not errors else "rejected",
        "claim_count": len(rows),
        "error_count": len(errors),
        "claims": rows,
        "errors": errors,
    }


def _load_runtime_inputs(
    packet: Mapping[str, object],
) -> tuple[
    dict[str, dict[str, object]],
    dict[str, list[FinancialFact]],
    dict[str, FinancialFact],
    dict[str, date | None],
    dict[str, date],
    dict[str, str],
    dict[str, str],
    str,
    str,
]:
    cash_path = _report_path(CANONICAL_FACTS_REPORT)
    architecture_path = _report_path(ARCHITECTURE_REPORT)
    cash = _read_json(cash_path)
    architecture = _read_json(architecture_path)
    records = {
        str(item["ticker"]): item
        for item in cash.get("active_universe") or ()
        if isinstance(item, dict) and item.get("ticker")
    }
    formal = {
        str(item["ticker"]): _as_date(item.get("latest_formal_period"))
        for item in architecture.get("active_universe") or ()
        if isinstance(item, dict) and item.get("ticker")
    }
    facts_by_ticker: dict[str, list[FinancialFact]] = defaultdict(list)
    facts_by_id: dict[str, FinancialFact] = {}
    for raw in cash.get("canonical_facts") or ():
        if not isinstance(raw, dict) or not raw.get("ticker"):
            continue
        fact = _fact(raw)
        facts_by_ticker[str(raw["ticker"])].append(fact)
        facts_by_id[fact.fact_id] = fact
    source_database = Path(str(cash.get("source_database") or ""))
    if not source_database.exists():
        source_database = _data_root() / "thesis_monitor.sqlite3"
    cutoff = date.fromisoformat(str(packet["assessment_date"]))
    preliminary = _latest_preliminary_periods(source_database, cutoff)
    industries = {ticker: str(item.get("industry") or "") for ticker, item in records.items()}
    financial_types = {
        ticker: str(item.get("financial_type") or "non_financial")
        for ticker, item in records.items()
    }
    return (
        records,
        dict(facts_by_ticker),
        facts_by_id,
        formal,
        preliminary,
        industries,
        financial_types,
        _file_sha256(cash_path),
        _file_sha256(architecture_path),
    )


def _generate_shadow_output(
    contexts: Mapping[str, CashFlowReasoningContext],
    facts: Mapping[str, FinancialFact],
    industries: Mapping[str, str],
    source_texts: Mapping[str, str],
) -> Mapping[str, ShadowReasoning | None]:
    return {
        ticker: render_shadow_reasoning(
            context,
            facts,
            industry=industries.get(ticker, ""),
            source_text=source_texts.get(ticker, ""),
        )
        for ticker, context in contexts.items()
    }


def _numeric_binding_report(
    reasonings: Mapping[str, ShadowReasoning | None],
    facts: Mapping[str, FinancialFact],
) -> dict[str, object]:
    errors: list[dict[str, str]] = []
    claims: list[dict[str, object]] = []
    for ticker, reasoning in reasonings.items():
        if reasoning is None:
            continue
        for claim in reasoning.numeric_claims:
            fact = facts.get(claim.fact_id)
            row = {"ticker": ticker, **asdict(claim)}
            claims.append(row)
            if fact is None:
                errors.append({"ticker": ticker, "error": "numeric_fact_missing"})
            elif Decimal(claim.value) != fact.value:
                errors.append({"ticker": ticker, "error": "numeric_value_mismatch"})
            elif claim.semantic_type != fact.metric.value:
                errors.append({"ticker": ticker, "error": "numeric_semantic_mismatch"})
            elif claim.display not in reasoning.text:
                errors.append({"ticker": ticker, "error": "numeric_display_unresolved"})
    return {
        "status": "passed" if not errors else "rejected",
        "automatic": len(claims) - len(errors),
        "manual": 0,
        "rejected": len(errors),
        "unresolved": 0,
        "claims": claims,
        "errors": errors,
    }


def _normalized_sentences(text: str) -> list[str]:
    return [
        _SPACE.sub(" ", part.strip()).casefold()
        for part in _SENTENCE.split(text)
        if part.strip()
    ]


def _quality_receipt(
    packet_id: str,
    reasonings: Mapping[str, ShadowReasoning | None],
    *,
    checked_at: datetime,
) -> dict[str, object]:
    sentence_tickers: dict[str, set[str]] = defaultdict(set)
    skeleton_tickers: dict[str, set[str]] = defaultdict(set)
    triple_numeric_tickers: list[str] = []
    for ticker, reasoning in reasonings.items():
        if reasoning is None:
            continue
        if len(reasoning.numeric_claims) > 2:
            triple_numeric_tickers.append(ticker)
        for sentence in _normalized_sentences(reasoning.text):
            sentence_tickers[sentence].add(ticker)
            skeleton = _NUMBER.sub("<numeric>", _DATE.sub("<date>", sentence))
            skeleton_tickers[skeleton].add(ticker)
    repeated = [
        {"sentence": sentence, "tickers": sorted(tickers)}
        for sentence, tickers in sentence_tickers.items()
        if len(tickers) >= 2
    ]
    skeletons = [
        {"skeleton": skeleton, "tickers": sorted(tickers)}
        for skeleton, tickers in skeleton_tickers.items()
        if len(tickers) >= 3
    ]
    errors: list[str] = []
    if repeated:
        errors.append("substantive_cash_flow_sentence_repetition")
    if skeletons:
        errors.append("cash_flow_template_skeleton_repetition")
    if triple_numeric_tickers:
        errors.append("cash_flow_numeric_tuple_dump")
    payload: dict[str, object] = {
        "contract": "runtime-message-quality-receipt-v2",
        "scope": CANARY_POLICY_VERSION,
        "packet_id": packet_id,
        "status": "passed" if not errors else "rejected",
        "errors": errors,
        "checked_at": checked_at.astimezone(UTC).isoformat(),
        "thresholds_relaxed": False,
        "check_results": {
            "rendered_subject_count": sum(value is not None for value in reasonings.values()),
            "substantive_repeated_sentence_count": len(repeated),
            "template_skeleton_repeat_count": len(skeletons),
            "numeric_tuple_dump_count": len(triple_numeric_tickers),
            "repeated_sentences": repeated,
            "template_skeleton_repeats": skeletons,
            "numeric_tuple_dump_tickers": triple_numeric_tickers,
        },
    }
    payload["receipt_id"] = f"cf-quality-{_sha256_bytes(_canonical_json(payload))[:24]}"
    return payload


def _failure_receipt(
    *,
    packet_id: str,
    canary_id: str,
    attempt_id: str,
    status: str,
    reason: str,
    production_delivery_sha256: str,
    started_at: datetime,
    completed_at: datetime,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "archive_contract": CANARY_ARCHIVE_VERSION,
        "packet_id": packet_id,
        "canary_id": canary_id,
        "attempt_id": attempt_id,
        "status": status,
        "reason": reason,
        "production_delivery_sha256": production_delivery_sha256,
        "production_influence_count": 0,
        "telegram_delivery_count": 0,
        "assessment_persistence_count": 0,
        "warning_lifecycle_mutation_count": 0,
        "started_at": started_at.astimezone(UTC).isoformat(),
        "completed_at": completed_at.astimezone(UTC).isoformat(),
    }
    payload["receipt_id"] = f"cf-receipt-{_sha256_bytes(_canonical_json(payload))[:24]}"
    return payload


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
                completed_at=datetime.now(UTC),
            ),
        )
    except OSError:
        return None
    return path


def run_cash_flow_runtime_shadow_canary(
    packet_id: str,
    *,
    delivery_mode: str,
    expected_delivery_sha256: str,
    generator: ShadowGenerator | None = None,
    now: datetime | None = None,
) -> CanaryRunResult:
    started_at = (now or datetime.now(UTC)).astimezone(UTC)
    canary_id = canary_identity(packet_id)
    attempt_id = f"attempt-{started_at:%Y%m%dT%H%M%S%fZ}-{uuid.uuid4().hex[:8]}"
    packet_path = _packet_path(packet_id)
    if not packet_path.exists():
        return CanaryRunResult(
            status="PACKET_MISSING",
            packet_id=packet_id,
            canary_id=canary_id,
            reason="packet_missing",
        )
    packet = _read_json(packet_path)
    archive = _production_archive(packet)
    root = _canary_root(packet)
    attempt_dir = root / "attempts" / attempt_id
    completion = root / "canary-complete.json"
    with _canary_lock(canary_id):
        if completion.exists():
            return CanaryRunResult(
                status="DUPLICATE_SKIPPED",
                packet_id=packet_id,
                canary_id=canary_id,
                reason="logical_canary_already_complete",
            )
        delivery_path = archive / "delivery-result.json"
        try:
            delivery = _read_json(delivery_path)
            actual_delivery_sha = _file_sha256(delivery_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
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
                status="PRODUCTION_ARTIFACT_UNAVAILABLE",
                packet_id=packet_id,
                canary_id=canary_id,
                attempt_id=attempt_id,
                receipt_path=str(receipt) if receipt else None,
                reason=type(exc).__name__,
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
                status="PRODUCTION_NOT_FINAL",
                packet_id=packet_id,
                canary_id=canary_id,
                attempt_id=attempt_id,
                receipt_path=str(receipt) if receipt else None,
                reason="delivery_result_not_terminal_or_identity_mismatch",
            )

        stage_started = time.perf_counter()
        try:
            (
                records,
                facts_by_ticker,
                facts_by_id,
                formal,
                preliminary,
                industries,
                financial_types,
                canonical_facts_sha,
                architecture_sha,
            ) = _load_runtime_inputs(packet)
            load_latency_ms = round((time.perf_counter() - stage_started) * 1000, 3)
            packet_stocks = {
                str(item["ticker"]): item
                for item in packet.get("stocks") or ()
                if isinstance(item, dict) and item.get("ticker")
            }
            cutoff = date.fromisoformat(str(packet["assessment_date"]))
            contexts: dict[str, CashFlowReasoningContext] = {}
            source_texts: dict[str, str] = {}
            unknowns_by_ticker: dict[str, tuple[str, ...]] = {}
            for ticker, stock in packet_stocks.items():
                record = records.get(ticker)
                if record is None:
                    continue
                source_text = _stock_source_text(stock)
                source_texts[ticker] = source_text
                unknowns = tuple(str(item) for item in stock.get("unknowns") or ())
                unknowns_by_ticker[ticker] = unknowns
                metrics = record.get("metrics")
                fcf_metric = metrics.get("fcf") if isinstance(metrics, dict) else {}
                preferred_fcf = (
                    str(fcf_metric.get("fact_id"))
                    if isinstance(fcf_metric, dict) and fcf_metric.get("fact_id")
                    else None
                )
                contexts[ticker] = build_cash_flow_reasoning_context(
                    ticker=ticker,
                    industry=industries.get(ticker, ""),
                    financial_type=financial_types.get(ticker, "non_financial"),
                    core_status=str(record.get("cash_flow_core_status") or "BLOCKED"),
                    facts=facts_by_ticker.get(ticker, ()),
                    cutoff=cutoff,
                    latest_formal_period=formal.get(ticker),
                    latest_provisional_period=preliminary.get(ticker),
                    latest_operating_earnings_period=_operating_earnings_period(stock),
                    preferred_fcf_fact_id=preferred_fcf,
                    existing_unknowns=unknowns,
                    materiality_signals=(source_text,),
                )
            sidecar_latency_ms = round((time.perf_counter() - stage_started) * 1000, 3)
        except Exception as exc:
            receipt = _write_attempt_failure(
                attempt_dir,
                packet_id=packet_id,
                canary_id=canary_id,
                attempt_id=attempt_id,
                status="SIDECAR_BUILD_FAILED",
                reason=type(exc).__name__,
                production_delivery_sha256=actual_delivery_sha,
                started_at=started_at,
            )
            return CanaryRunResult(
                status="SIDECAR_BUILD_FAILED",
                packet_id=packet_id,
                canary_id=canary_id,
                attempt_id=attempt_id,
                receipt_path=str(receipt) if receipt else None,
                reason=type(exc).__name__,
            )

        generated_at = datetime.now(UTC)
        try:
            generation_started = time.perf_counter()
            reasonings = dict(
                (generator or _generate_shadow_output)(
                    contexts,
                    facts_by_id,
                    industries,
                    source_texts,
                )
            )
            ai_latency_ms = round((time.perf_counter() - generation_started) * 1000, 3)
        except Exception as exc:
            receipt = _write_attempt_failure(
                attempt_dir,
                packet_id=packet_id,
                canary_id=canary_id,
                attempt_id=attempt_id,
                status="AI_GENERATION_FAILED",
                reason=type(exc).__name__,
                production_delivery_sha256=actual_delivery_sha,
                started_at=started_at,
            )
            return CanaryRunResult(
                status="AI_GENERATION_FAILED",
                packet_id=packet_id,
                canary_id=canary_id,
                attempt_id=attempt_id,
                receipt_path=str(receipt) if receipt else None,
                reason=type(exc).__name__,
            )

        validator_started = time.perf_counter()
        binding = _numeric_binding_report(reasonings, facts_by_id)
        semantic_rows: list[dict[str, object]] = []
        unknown_rows: list[dict[str, object]] = []
        semantic_error_count = 0
        for ticker, context in contexts.items():
            reasoning = reasonings.get(ticker)
            resolved, unknown_audit = resolve_cash_flow_unknowns(
                unknowns_by_ticker.get(ticker, ()),
                context,
                industry=industries.get(ticker, ""),
                source_text=source_texts.get(ticker, ""),
            )
            errors = validate_shadow_reasoning(
                context,
                facts_by_id,
                reasoning,
                unknowns=resolved,
                valuation_changed=False,
                thesis_status_changed=False,
            )
            semantic_error_count += len(errors)
            semantic_rows.append({"ticker": ticker, "errors": list(errors)})
            unknown_rows.append(
                {
                    "ticker": ticker,
                    "before": list(unknowns_by_ticker.get(ticker, ())),
                    "after": list(resolved),
                    "audit": unknown_audit,
                }
            )
        baseline_consistency = _baseline_consistency_audit(
            packet_stocks,
            contexts,
            facts_by_id,
            archive=archive,
            delivery_mode=delivery_mode,
        )
        semantic_error_count += int(baseline_consistency["error_count"])
        semantic = {
            "status": "passed" if semantic_error_count == 0 else "rejected",
            "error_count": semantic_error_count,
            "subjects": semantic_rows,
            "baseline_cash_flow_consistency": {
                "contract": baseline_consistency["contract"],
                "status": baseline_consistency["status"],
                "claim_count": baseline_consistency["claim_count"],
                "error_count": baseline_consistency["error_count"],
            },
            "prohibited_metrics_created": 0,
            "valuation_context_mutations": 0,
            "thesis_status_mutations": 0,
        }
        quality = _quality_receipt(packet_id, reasonings, checked_at=datetime.now(UTC))
        validator_latency_ms = round((time.perf_counter() - validator_started) * 1000, 3)
        status = "COMPLETE_PASS"
        reason: str | None = None
        if binding["status"] != "passed":
            status = "NUMERIC_BINDING_FAILED"
            reason = "numeric_binding_rejected"
        elif semantic["status"] != "passed":
            status = "SEMANTIC_VALIDATION_FAILED"
            reason = "shadow_semantic_validation_rejected"
        elif quality["status"] != "passed":
            status = "RUNTIME_QUALITY_FAILED"
            reason = "shadow_runtime_quality_rejected"

        contexts_payload = {
            ticker: context_to_dict(context) for ticker, context in contexts.items()
        }
        raw_output = {
            "packet_id": packet_id,
            "canary_id": canary_id,
            "generated_at": generated_at.isoformat(),
            "subjects": {
                ticker: reasoning_to_dict(reasoning)
                for ticker, reasoning in reasonings.items()
            },
        }
        shadow_input = {
            "packet_id": packet_id,
            "packet_sha256": _packet_sha(packet_path),
            "assessment_date": packet["assessment_date"],
            "market": packet["market"],
            "packet_generated_at": packet.get("generated_at"),
            "source_monitor_run_id": packet.get("source_monitor_run_id"),
            "analysis_policy_version": packet.get("analysis_policy_version"),
            "output_schema_version": packet.get("output_schema_version"),
            "production_delivery_mode": delivery_mode,
            "production_delivery_sha256": actual_delivery_sha,
            "production_candidate_id": _production_candidate_identity(archive),
            "cash_flow_contract": CONSUMPTION_CONTRACT_VERSION,
            "canary_policy": CANARY_POLICY_VERSION,
            "contexts": contexts_payload,
        }
        sidecar = {
            "packet_id": packet_id,
            "contract": CONSUMPTION_CONTRACT_VERSION,
            "canonical_facts_sha256": canonical_facts_sha,
            "architecture_evidence_sha256": architecture_sha,
            "baseline_consistency_contract": BASELINE_CONSISTENCY_CONTRACT_VERSION,
            "subjects": contexts_payload,
        }
        bound_output = {
            **raw_output,
            "binding": binding,
            "unknown_resolution": unknown_rows,
        }
        manifest = {
            "archive_contract": CANARY_ARCHIVE_VERSION,
            "canary_id": canary_id,
            "packet_id": packet_id,
            "packet_sha256": _packet_sha(packet_path),
            "production_delivery_sha256": actual_delivery_sha,
            "production_delivery_mode": delivery_mode,
            "production_candidate_id": _production_candidate_identity(archive),
            "shadow_candidate_id": f"cf-shadow-{_sha256_bytes(_canonical_json(raw_output))[:24]}",
            "cash_flow_contract": CONSUMPTION_CONTRACT_VERSION,
            "canary_policy": CANARY_POLICY_VERSION,
            "natural_proof_state": "RUNTIME_OBSERVATION_REQUIRES_SCHEDULE_SOURCE_REVIEW",
            "created_at": started_at.isoformat(),
        }
        artifacts: Sequence[tuple[str, object]] = (
            ("canary-manifest.json", manifest),
            ("cash-flow-sidecar.json", sidecar),
            ("shadow-input.json", shadow_input),
            ("raw-shadow-output.json", raw_output),
            ("bound-shadow-output.json", bound_output),
            ("semantic-validation.json", semantic),
            ("baseline-consistency.json", baseline_consistency),
            ("runtime-quality-receipt.json", quality),
        )
        archive_started = time.perf_counter()
        try:
            for filename, payload in artifacts:
                _write_json_once(attempt_dir / filename, payload)
        except Exception as exc:
            receipt = _write_attempt_failure(
                attempt_dir,
                packet_id=packet_id,
                canary_id=canary_id,
                attempt_id=attempt_id,
                status="ARCHIVE_WRITE_FAILED",
                reason=type(exc).__name__,
                production_delivery_sha256=actual_delivery_sha,
                started_at=started_at,
            )
            return CanaryRunResult(
                status="ARCHIVE_WRITE_FAILED",
                packet_id=packet_id,
                canary_id=canary_id,
                attempt_id=attempt_id,
                receipt_path=str(receipt) if receipt else None,
                reason=type(exc).__name__,
            )
        archive_latency_ms = round((time.perf_counter() - archive_started) * 1000, 3)
        completed_at = datetime.now(UTC)
        receipt_payload = _failure_receipt(
            packet_id=packet_id,
            canary_id=canary_id,
            attempt_id=attempt_id,
            status=status,
            reason=reason or "all_shadow_gates_passed",
            production_delivery_sha256=actual_delivery_sha,
            started_at=started_at,
            completed_at=completed_at,
        )
        receipt_payload["shadow_candidate_id"] = manifest["shadow_candidate_id"]
        receipt_payload["quality_receipt_id"] = quality["receipt_id"]
        receipt_payload["numeric_binding"] = {
            key: binding[key]
            for key in ("automatic", "manual", "rejected", "unresolved")
        }
        receipt_payload["semantic_error_count"] = semantic_error_count
        receipt_payload["baseline_consistency_error_count"] = baseline_consistency[
            "error_count"
        ]
        receipt_payload["quality_error_count"] = len(quality["errors"])
        receipt_payload["latency_ms"] = {
            "input_load": load_latency_ms,
            "sidecar": sidecar_latency_ms,
            "ai_generation": ai_latency_ms,
            "validator": validator_latency_ms,
            "archive": archive_latency_ms,
            "total": round((time.perf_counter() - stage_started) * 1000, 3),
        }
        receipt_payload.pop("receipt_id", None)
        receipt_payload["receipt_id"] = (
            f"cf-receipt-{_sha256_bytes(_canonical_json(receipt_payload))[:24]}"
        )
        receipt_path = attempt_dir / "canary-receipt.json"
        _write_json_once(receipt_path, receipt_payload)
        if status == "COMPLETE_PASS":
            completion_payload = {
                "archive_contract": CANARY_ARCHIVE_VERSION,
                "packet_id": packet_id,
                "canary_id": canary_id,
                "attempt_id": attempt_id,
                "status": status,
                "canary_receipt_id": receipt_payload["receipt_id"],
                "production_delivery_sha256": actual_delivery_sha,
                "completed_at": completed_at.isoformat(),
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
            status=status,
            packet_id=packet_id,
            canary_id=canary_id,
            attempt_id=attempt_id,
            receipt_path=str(receipt_path),
            reason=reason,
        )


def _launch_failure_receipt(
    packet: Mapping[str, object],
    *,
    delivery_sha256: str,
    reason: str,
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


def launch_cash_flow_runtime_shadow_canary(
    delivery_result: Mapping[str, object],
    *,
    popen: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
) -> CanaryLaunchResult:
    packet_id = str(delivery_result.get("packet_id") or "")
    if not get_settings().cash_flow_runtime_shadow_canary_enabled:
        return CanaryLaunchResult(status="disabled", packet_id=packet_id or None)
    if (
        not packet_id
        or delivery_result.get("status") != "sent"
        or int(delivery_result.get("pending_count") or 0) != 0
        or int(delivery_result.get("sent_count") or 0)
        != int(delivery_result.get("delivery_count") or 0)
    ):
        return CanaryLaunchResult(
            status="not_terminal",
            packet_id=packet_id or None,
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
                status="identity_mismatch",
                packet_id=packet_id,
                reason="returned_delivery_result_differs_from_archive",
            )
        command = [
            sys.executable,
            "-m",
            "app.jobs.cash_flow_shadow_canary",
            "--packet-id",
            packet_id,
            "--delivery-mode",
            str(delivery_result.get("delivery_mode") or ""),
            "--delivery-result-sha256",
            delivery_sha256,
        ]
        process = popen(
            command,
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
            status="launch_failed",
            packet_id=packet_id,
            canary_id=canary_identity(packet_id),
            reason=type(exc).__name__,
        )
    return CanaryLaunchResult(
        status="launched",
        packet_id=packet_id,
        canary_id=canary_identity(packet_id),
        process_id=process.pid,
    )


def cash_flow_canary_status_counts(
    contexts: Iterable[CashFlowReasoningContext],
) -> dict[str, int]:
    return dict(Counter(context.freshness_state.value for context in contexts))
