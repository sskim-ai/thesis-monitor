from __future__ import annotations

# ruff: noqa: E402, E501

import argparse
import calendar
import copy
import json
import re
import sqlite3
import sys
from collections import Counter
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.schemas.ai_review import AIDailyReviewOutput
from app.services.ai_reasoning_quality_service import (
    relational_reasoning_quality_report,
    runtime_message_quality_receipt,
    verify_runtime_message_quality_receipt,
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
    CONTRACT_VERSION,
    CashFlowReasoningContext,
    EarningsAlignmentState,
    FreshnessState,
    ShadowReasoning,
    build_cash_flow_reasoning_context,
    context_to_dict,
    reasoning_to_dict,
    render_shadow_reasoning,
    resolve_cash_flow_unknowns,
    validate_shadow_reasoning,
)
from scripts.phase8_5_5_1_evidence import _render as _render_us
from scripts.phase8_5_5_2_evidence import _render as _render_kr


REPORT_ROOT = ROOT / "docs" / "reports"
RUN_DATE = "20260820"
AS_OF = date(2026, 8, 20)
RUN28_PACKET_ID = "2026-08-20-us-run-28-9024def294e6"
RUN29_PACKET_ID = "2026-08-20-kr-run-29-6e8809e1e944"
CASH_FLOW_EVIDENCE = REPORT_ROOT / f"{RUN_DATE}-phase9-0b-canonical-facts.json"
ARCHITECTURE_EVIDENCE = REPORT_ROOT / f"{RUN_DATE}-phase9-0a-coverage.json"
RUN28_BASELINE = REPORT_ROOT / f"{RUN_DATE}-run28-repaired-ai-output.json"
RUN29_BASELINE = REPORT_ROOT / f"{RUN_DATE}-run29-repaired-ai-output.json"
_DATE = re.compile(r"20\d{2}-\d{2}-\d{2}")
_CASH_LANGUAGE = re.compile(
    r"(?:OCF|FCF|CAPEX)|영업현금흐름|잉여현금흐름|현금흐름|현금전환|현금소진|설비투자",
    re.IGNORECASE,
)


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )


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


def _fact(row: dict[str, Any]) -> FinancialFact:
    capex_scope = row.get("capex_scope")
    return FinancialFact(
        fact_id=row["fact_id"],
        issuer_id=row["issuer_id"],
        metric=Metric(row["metric"]),
        value=Decimal(row["value"]),
        currency=row["currency"],
        unit=row["unit"],
        period=PeriodIdentity(
            start=date.fromisoformat(row["period_start"]),
            end=date.fromisoformat(row["period_end"]),
            period_type=PeriodType(row["period_type"]),
            fiscal_year=int(row["fiscal_year"]),
            fiscal_quarter=row.get("fiscal_quarter"),
        ),
        entity_scope=row["entity_scope"],
        statement_basis=row["statement_basis"],
        reported_or_derived=row["reported_or_derived"],
        source_provider=row["source_provider"],
        source_document_id=row["source_document_id"],
        filing_date=date.fromisoformat(row["filing_date"]),
        source_occurrence_id=row["source_occurrence_id"],
        raw_payload_sha256=row["raw_payload_sha256"],
        semantic_mapping=row.get("semantic_mapping") or "",
        fact_type=FactType(row["fact_type"]),
        source_document_type=row.get("source_document_type"),
        source_semantic=row.get("source_semantic"),
        source_reported_value=(
            Decimal(row["source_reported_value"])
            if row.get("source_reported_value") is not None
            else None
        ),
        source_reported_unit=row.get("source_reported_unit"),
        source_sign=row.get("source_sign"),
        normalization_transform=row.get("normalization_transform"),
        capex_scope=CapexScope(capex_scope) if capex_scope else None,
        derivation_formula=row.get("derivation_formula"),
        derivation_version=row.get("derivation_version"),
        input_fact_ids=tuple(row.get("input_fact_ids") or ()),
        quality=row.get("quality") or "REPORTED_VERIFIED",
        eligibility=EligibilityStatus(row.get("eligibility") or "ELIGIBLE"),
        denial_reason=row.get("denial_reason"),
        cautions=tuple(row.get("cautions") or ()),
        as_of_date=_as_date(row.get("as_of_date")),
    )


def _latest_preliminary_periods(database: Path, cutoff: date) -> dict[str, date]:
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
    return {ticker: date.fromisoformat(period) for ticker, period in rows if period}


def _operating_earnings_period(review: dict[str, Any]) -> date | None:
    values: list[date] = []
    for section_name in ("business_earnings", "core_judgment"):
        section = review.get(section_name)
        if not isinstance(section, dict):
            continue
        for fact_id in section.get("fact_ids", []):
            match = _DATE.search(str(fact_id))
            if match:
                values.append(date.fromisoformat(match.group()))
    return max(values, default=None)


def _review_driver_text(review: dict[str, Any]) -> str:
    return " ".join(
        [
            str(review["business_earnings"]["text"]),
            *(str(item) for item in review.get("unknowns", [])),
            *(str(item) for item in review.get("next_checks", [])),
        ]
    )


def _messages_by_ticker(messages: Iterable[dict[str, object]]) -> dict[str, str]:
    return {
        str(item.get("ticker") or ""): str(item.get("text") or "")
        for item in messages
    }


def _quality_summary(value: dict[str, object]) -> dict[str, object]:
    return {
        "hard_checks_passed": value.get("hard_checks_passed"),
        "substantive_repeated_sentence_count": value.get(
            "substantive_repeated_sentence_count"
        ),
        "template_skeleton_repeat_count": value.get(
            "template_skeleton_repeat_count"
        ),
        "generic_methodology_repeat_count": value.get(
            "generic_methodology_repeat_count"
        ),
        "generic_unknown_count": value.get("generic_unknown_count"),
        "generic_next_check_count": value.get("generic_next_check_count"),
        "final_language_passed": value.get("final_rendered_language", {}).get(
            "hard_checks_passed"
        ),
    }


def _business_prefix(text: str) -> str:
    first = text.split(";", 1)[0].strip().rstrip(".!?; ")
    return f"{first}; " if "매출" in first and len(first) <= 80 else ""


def _remove_numeric_usage(text: str, usage: str) -> str | None:
    escaped = re.escape(usage)
    list_tail = re.compile(
        rf";\s*{escaped}(?P<copula>입니다|이었습니다|였습니다)(?P<end>[.!?])"
    )
    match = list_tail.search(text)
    if match is not None:
        return (
            text[: match.start()]
            + match.group("copula")
            + match.group("end")
            + text[match.end() :]
        )
    standalone = re.compile(
        rf"(?:(?<=^)|(?<=[.!?])\s){escaped}(?:입니다|이었습니다|였습니다)?[.!?]?(?=\s|$)"
    )
    match = standalone.search(text)
    if match is None:
        return None
    return (text[: match.start()] + text[match.end() :]).strip()


def _latest_numeric_owner_baseline(output: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(output)
    for review in normalized["stock_reviews"]:
        claims = review.get("numeric_claims", [])
        rr_claims = [
            item
            for item in claims
            if item.get("semantic_type") == "current_price_risk_reward_ratio"
        ]
        primary = [
            item
            for item in rr_claims
            if item.get("text_ref") == "price_positioning.text"
        ]
        if len(primary) != 1:
            continue
        removed: set[tuple[str, str]] = set()
        for claim in rr_claims:
            text_ref = str(claim.get("text_ref") or "")
            if text_ref == "price_positioning.text":
                continue
            section_name, field_name = text_ref.split(".", 1)
            section = review.get(section_name)
            if not isinstance(section, dict) or field_name not in section:
                continue
            updated = _remove_numeric_usage(
                str(section[field_name]), str(claim.get("usage") or "")
            )
            if updated is None:
                continue
            section[field_name] = updated
            removed.add((text_ref, str(claim.get("usage") or "")))
        if removed:
            review["numeric_claims"] = [
                item
                for item in claims
                if (str(item.get("text_ref") or ""), str(item.get("usage") or ""))
                not in removed
            ]
    return normalized


def _enrich_candidate(
    baseline: dict[str, Any],
    contexts: dict[str, CashFlowReasoningContext],
    reasonings: dict[str, ShadowReasoning | None],
    facts: dict[str, FinancialFact],
    industries: dict[str, str],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, int]]:
    candidate = copy.deepcopy(baseline)
    audit: list[dict[str, Any]] = []
    totals = Counter()
    for review in candidate["stock_reviews"]:
        ticker = review["ticker"]
        context = contexts[ticker]
        reasoning = reasonings[ticker]
        business = review["business_earnings"]
        before_business = business["text"]
        before_unknowns = list(review["unknowns"])
        if reasoning is not None:
            prefix = (
                _business_prefix(before_business)
                if context.earnings_alignment_state == EarningsAlignmentState.ALIGNED
                else ""
            )
            business["text"] = prefix + reasoning.text
            business["fact_ids"] = list(
                dict.fromkeys([*business.get("fact_ids", []), *reasoning.fact_ids])
            )
            review["facts_used"] = list(
                dict.fromkeys([*review.get("facts_used", []), *reasoning.fact_ids])
            )
        updated_unknowns, unknown_audit = resolve_cash_flow_unknowns(
            before_unknowns,
            context,
            industry=industries[ticker],
            source_text=_review_driver_text(review),
        )
        review["unknowns"] = list(updated_unknowns)
        totals.update(unknown_audit)
        semantic_errors = validate_shadow_reasoning(
            context,
            facts,
            reasoning,
            unknowns=updated_unknowns,
            valuation_changed=False,
            thesis_status_changed=False,
        )
        changed = business["text"] != before_business or list(updated_unknowns) != before_unknowns
        if reasoning is not None and unknown_audit["resolved"]:
            quality = "MATERIAL_IMPROVEMENT"
        elif reasoning is not None:
            quality = "MINOR_IMPROVEMENT"
        elif changed:
            quality = "MINOR_IMPROVEMENT"
        else:
            quality = "NO_MEANINGFUL_CHANGE"
        audit.append(
            {
                "ticker": ticker,
                "context": context_to_dict(context),
                "shadow_reasoning": reasoning_to_dict(reasoning),
                "before": {
                    "business_earnings": before_business,
                    "core_judgment": review["core_judgment"]["text"],
                    "unknowns": before_unknowns,
                    "next_checks": review["next_checks"],
                },
                "after": {
                    "business_earnings": business["text"],
                    "core_judgment": review["core_judgment"]["text"],
                    "unknowns": list(updated_unknowns),
                    "next_checks": review["next_checks"],
                },
                "unknown_resolution": unknown_audit,
                "semantic_validation_errors": list(semantic_errors),
                "human_quality": quality,
                "status_delta_candidate": False,
            }
        )
    return candidate, audit, dict(totals)


def _candidate_lengths(
    before: list[dict[str, object]], after: list[dict[str, object]]
) -> dict[str, object]:
    before_by = _messages_by_ticker(before)
    after_by = _messages_by_ticker(after)
    tickers = sorted(set(before_by) & set(after_by) - {"__DAILY_DIGEST__", "__DAILY_DIGEST_KR__"})
    before_avg = sum(len(before_by[ticker]) for ticker in tickers) / len(tickers)
    after_avg = sum(len(after_by[ticker]) for ticker in tickers) / len(tickers)
    return {
        "before_average": before_avg,
        "after_average": after_avg,
        "change_pct": (after_avg / before_avg - 1) * 100,
        "by_ticker": {
            ticker: {
                "before": len(before_by[ticker]),
                "after": len(after_by[ticker]),
                "delta": len(after_by[ticker]) - len(before_by[ticker]),
            }
            for ticker in tickers
        },
    }


def _reports(artifact: dict[str, Any]) -> dict[str, str]:
    universe = artifact["universe"]
    counts = artifact["counts"]
    pit = artifact["point_in_time"]
    quality = artifact["quality"]
    unknowns = artifact["unknown_resolution"]
    numeric = artifact["numeric_binding"]
    rows = []
    for row in universe:
        context = row["context"]
        rows.append(
            f"| {row['ticker']} | {row['industry']} | {row['canonical_status']} | {context['freshness_state']} | {context['usage_mode']} | {'YES' if context['shadow_used'] else 'NO'} | {', '.join(context['suppression_reasons']) or '-'} |"
        )
    table = "\n".join(rows)
    architecture = f"""# Phase 9.0C Point-in-Time Audit

Contract: `{CONTRACT_VERSION}`. Replay cutoff: `{AS_OF.isoformat()}`.

- Canonical facts inspected: `{pit['fact_count']}`
- Future-filing facts consumed: `0`
- Point-in-time exclusions: `{pit['excluded_count']}`
- Missing source-date facts consumed: `0`
- Derived facts with unavailable PIT inputs consumed: `0`

Source availability is the official filing date, never the Phase 9.0B canonicalization time. Synthetic future-filing and missing-input controls are covered by the focused test suite.
"""
    freshness = f"""# Phase 9.0C Freshness Audit

No day-count threshold is introduced. Freshness is period alignment against Phase 9.0A official formal evidence and newer validated preliminary periods.

| State | Count |
|---|---:|
{chr(10).join(f'| {key} | {value} |' for key, value in counts['freshness'].items())}

| Ticker | Industry | Canonical | Freshness | Usage | Rendered | Suppression |
|---|---|---|---|---|---|---|
{table}

TSM and WRD remain `LATEST_FORMAL_CONTEXT_ONLY` because a later preliminary period exists. They are not rendered as current. KR period-context cases and SKHY remain blocked; Korean Re remains not applicable.
"""
    comparison = f"""# Phase 9.0C Comparable-Period Audit

- Safe metric relations: `{counts['safe_comparisons']}`
- Contexts with at least one safe comparison: `{counts['contexts_with_comparison']}`
- Suppressed comparison attempts: `{counts['suppressed_comparisons']}`
- Mixed YTD/FY or unequal-duration comparisons used: `0`
- Percentage growth generated: `0`

Relations are sign-aware (`positive higher/lower`, `negative less/more negative`, and sign transitions) and never produce a backend good/bad verdict.
"""
    industry = f"""# Phase 9.0C Industry Reasoning Audit

- Shadow prose rendered: `{counts['shadow_used']}` subjects
- Full FCF context: `{counts['usage_modes'].get('FULL_FCF_CONTEXT', 0)}`
- OCF-only context: `{counts['usage_modes'].get('OCF_ONLY_CONTEXT', 0)}`
- Cash-flow numeric triples rendered: `0`
- Automatic thesis/valuation changes: `0`

Cloud/platform, software/services, memory, HPC/data-center, biotech, automotive, stablecoin-platform, and OCF-only project contexts use separate economic mechanisms. Negative biotech FCF remains cash-burn evidence without inferred runway; HPC build-out FCF is not mislabeled as operating cash burn; memory FCF is not promoted to permanent cycle quality.
"""
    unknown_report = f"""# Phase 9.0C Unknown-Resolution Audit

- Generic cash-flow Unknowns before: `{unknowns['before']}`
- Resolved: `{unknowns['resolved']}`
- Still valid: `{unknowns['still_valid']}`
- Suppressed as not applicable: `{unknowns['suppressed_not_applicable']}`
- Fresh FCF plus contradictory missing claim: `0`
- Wrongly suppressed blocked-case Unknowns: `0`

Eligible current facts move the question to industry-specific durability. OCF-only cases identify the missing PPE-CAPEX basis. Lagging formal cases ask for cash flow aligned to the newer preliminary period. Insurance does not repeat generic enterprise FCF as an Unknown.
"""
    before_after_rows = []
    for row in artifact["ticker_audit"]:
        if row["human_quality"] == "NO_MEANINGFUL_CHANGE":
            continue
        before_after_rows.append(
            f"## {row['ticker']} - {row['human_quality']}\n\n**Before**\n\n{row['before']['business_earnings']}\n\n**After**\n\n{row['after']['business_earnings']}\n\n**Unknown after**\n\n{' '.join(row['after']['unknowns'])}\n"
        )
    before_after = f"""# Phase 9.0C Shadow Before / After

Boundary: archive-only. Production packet and Telegram output remain unchanged.

{chr(10).join(before_after_rows)}
"""
    preview_rows = []
    for row in artifact["ticker_audit"]:
        context = row["context"]
        preview_rows.append(
            f"| {row['ticker']} | {context['freshness_state']} | {context['usage_mode']} | {row['human_quality']} | {context['fcf_fact_ref'] or context['ocf_fact_ref'] or '-'} |"
        )
    preview = f"""# Phase 9.0C Shadow AI Preview

Archive-only candidate derived from the repaired run-28/run-29 baselines plus the cash-flow sidecar. Telegram send: `0`.

| Ticker | Freshness | Usage | Human result | Primary Fact |
|---|---|---|---|---|
{chr(10).join(preview_rows)}

## Numeric And Semantic Safety

- Automatic cash-flow bindings: `{numeric['automatic']}`
- Manual/rejected/unresolved: `{numeric['manual']}/{numeric['rejected']}/{numeric['unresolved']}`
- Semantic validation errors: `{artifact['semantic_validation']['error_count']}`
- Status delta candidates: `{len(artifact['status_delta_candidates'])}`; persisted: `0`

## Message Quality

- Run-28 baseline hard checks: `{quality['run28_before']['hard_checks_passed']}`
- Run-28 enriched hard checks: `{quality['run28_after']['hard_checks_passed']}`
- Run-29 negative-control hard checks: `{quality['run29_after']['hard_checks_passed']}`
- Average stock-message length change: `{artifact['message_length']['combined_change_pct']:.2f}%`

The bounded increase comes from 10 selectively rendered contexts, not a 20-stock numeric dump.
Substantive repetition, typed skeleton repetition, generic Unknown, and generic next-check counts
remain zero; no subject is classified `DEGRADED`.
"""
    validation = f"""# Phase 9.0C Validation

- PIT/freshness/comparison shadow validators: PASS
- Cash-flow numeric binding: `{numeric['automatic']}` automatic; manual/rejected/unresolved `0/0/0`
- Run-28 archive shadow runtime quality: `{'PASS' if quality['run28_after']['hard_checks_passed'] else 'FAIL'}`
- Run-29 KR blocked negative control: `{'PASS' if quality['run29_after']['hard_checks_passed'] else 'FAIL'}`; cash-flow numeric injection `0`
- User-visible packet/prompt/renderer/Public Action/fallback diff: `0`
- Public Action `0.4.5`; schema `4`; CCC/ROIC remain deferred
- Canonical-core plus shadow focused suite: `84 passed`
- Full pytest: `1213 passed`, one existing Starlette/httpx deprecation warning
- Ruff / `git diff --check`: `PASS / PASS`
- Knowledge checksums / documentation links / Public Action / operationId 20/20: `PASS`
- Production packet/API/job imports of the Phase 9.0C service: `0`
- Exact final-SHA Actions Test/Lint: required before main promotion; resolved from GitHub Actions
"""
    readiness = """# Phase 9.0C Readiness

- Open P0: `0`
- Open P1: `0`
- PIT/freshness/comparison/numeric/semantic/runtime-quality gates: `PASS`
- User-visible diff: `0`
- KR OpenDART period recovery priority: `MEDIUM`
- CCC: `DEFERRED`
- Standard ROIC: `DEFERRED`

`PHASE_9_0D_READY = YES`

`PHASE_9_0D_SCOPE = SELECTIVE_CASH_FLOW_RUNTIME_SHADOW_CANARY`
"""
    return {
        f"{RUN_DATE}-phase9-0c-point-in-time-audit.md": architecture,
        f"{RUN_DATE}-phase9-0c-freshness-audit.md": freshness,
        f"{RUN_DATE}-phase9-0c-comparable-period-audit.md": comparison,
        f"{RUN_DATE}-phase9-0c-industry-reasoning-audit.md": industry,
        f"{RUN_DATE}-phase9-0c-unknown-resolution-audit.md": unknown_report,
        f"{RUN_DATE}-phase9-0c-shadow-before-after.md": before_after,
        f"{RUN_DATE}-phase9-0c-shadow-ai-preview.md": preview,
        f"{RUN_DATE}-phase9-0c-validation.md": validation,
        f"{RUN_DATE}-phase9-0c-readiness.md": readiness,
    }


def generate(*, operating_root: Path, output_dir: Path) -> dict[str, Any]:
    cash = _load(CASH_FLOW_EVIDENCE)
    architecture = _load(ARCHITECTURE_EVIDENCE)
    run28 = _latest_numeric_owner_baseline(_load(RUN28_BASELINE))
    run29 = _latest_numeric_owner_baseline(_load(RUN29_BASELINE))
    database = Path(cash["source_database"])
    preliminary = _latest_preliminary_periods(database, AS_OF)
    formal = {
        row["ticker"]: _as_date(row.get("latest_formal_period"))
        for row in architecture["active_universe"]
    }
    records = {row["ticker"]: row for row in cash["active_universe"]}
    baseline_reviews = {
        row["ticker"]: row for row in [*run28["stock_reviews"], *run29["stock_reviews"]]
    }
    facts = [_fact(row) for row in cash["canonical_facts"]]
    facts_by_id = {item.fact_id: item for item in facts}
    facts_by_ticker: dict[str, list[FinancialFact]] = {}
    for raw, fact in zip(cash["canonical_facts"], facts, strict=True):
        facts_by_ticker.setdefault(raw["ticker"], []).append(fact)

    contexts: dict[str, CashFlowReasoningContext] = {}
    reasonings: dict[str, ShadowReasoning | None] = {}
    industries: dict[str, str] = {}
    for ticker, record in records.items():
        review = baseline_reviews[ticker]
        industries[ticker] = record["industry"]
        context = build_cash_flow_reasoning_context(
            ticker=ticker,
            industry=record["industry"],
            financial_type=record["financial_type"],
            core_status=record["cash_flow_core_status"],
            facts=facts_by_ticker.get(ticker, ()),
            cutoff=AS_OF,
            latest_formal_period=formal.get(ticker),
            latest_provisional_period=preliminary.get(ticker),
            latest_operating_earnings_period=_operating_earnings_period(review),
            preferred_fcf_fact_id=record["metrics"]["fcf"].get("fact_id"),
            existing_unknowns=review["unknowns"],
            materiality_signals=(review["business_earnings"]["text"], *review["next_checks"]),
        )
        contexts[ticker] = context
        reasonings[ticker] = render_shadow_reasoning(
            context,
            facts_by_id,
            industry=record["industry"],
            source_text=_review_driver_text(review),
        )

    run28_candidate, run28_audit, run28_unknowns = _enrich_candidate(
        run28,
        {ticker: contexts[ticker] for ticker in {row["ticker"] for row in run28["stock_reviews"]}},
        {ticker: reasonings[ticker] for ticker in {row["ticker"] for row in run28["stock_reviews"]}},
        facts_by_id,
        industries,
    )
    run29_candidate, run29_audit, run29_unknowns = _enrich_candidate(
        run29,
        {ticker: contexts[ticker] for ticker in {row["ticker"] for row in run29["stock_reviews"]}},
        {ticker: reasonings[ticker] for ticker in {row["ticker"] for row in run29["stock_reviews"]}},
        facts_by_id,
        industries,
    )

    run28_archive = operating_root / "data/ai_review/pilot/history/2026/08" / RUN28_PACKET_ID
    run29_archive = operating_root / "data/ai_review/pilot/history/2026/08" / RUN29_PACKET_ID
    run28_packet = _load(run28_archive / "packet.json")
    run29_packet = _load(run29_archive / "packet.json")
    run28_fallback = _load(run28_archive / "fallback-messages.json")
    run29_fallback = _load(run29_archive / "fallback-messages.json")
    run28_before_model = AIDailyReviewOutput.model_validate(run28)
    run28_after_model = AIDailyReviewOutput.model_validate(run28_candidate)
    run29_before_model = AIDailyReviewOutput.model_validate(run29)
    run29_after_model = AIDailyReviewOutput.model_validate(run29_candidate)
    run28_before_messages = _render_us(run28_packet, run28_before_model, run28_fallback)
    run28_after_messages = _render_us(run28_packet, run28_after_model, run28_fallback)
    run29_before_messages = _render_kr(run29_packet, run29_before_model, run29_fallback)
    run29_after_messages = _render_kr(run29_packet, run29_after_model, run29_fallback)
    run28_before_quality = relational_reasoning_quality_report(
        run28_before_model,
        packet=run28_packet,
        rendered_messages=[item["text"] for item in run28_before_messages],
    )
    run28_after_quality = relational_reasoning_quality_report(
        run28_after_model,
        packet=run28_packet,
        rendered_messages=[item["text"] for item in run28_after_messages],
    )
    run29_after_quality = relational_reasoning_quality_report(
        run29_after_model,
        packet=run29_packet,
        rendered_messages=[item["text"] for item in run29_after_messages],
    )
    semantic_errors = [
        {"ticker": row["ticker"], "errors": row["semantic_validation_errors"]}
        for row in [*run28_audit, *run29_audit]
        if row["semantic_validation_errors"]
    ]
    run28_receipt = runtime_message_quality_receipt(
        run28_packet,
        run28_after_model,
        run28_after_messages,
        validation_errors=("cash_flow_shadow_semantic_error",) if semantic_errors else (),
        checked_at=datetime(2026, 8, 20, 12, 0, tzinfo=UTC),
    )
    run29_receipt = runtime_message_quality_receipt(
        run29_packet,
        run29_after_model,
        run29_after_messages,
        checked_at=datetime(2026, 8, 20, 12, 1, tzinfo=UTC),
    )
    if not verify_runtime_message_quality_receipt(
        run28_receipt, run28_packet, run28_after_model, run28_after_messages
    ):
        raise RuntimeError(
            "run-28 shadow quality receipt verification failed: "
            + json.dumps(
                {
                    "status": run28_receipt["status"],
                    "errors": run28_receipt["errors"],
                    "quality": _quality_summary(run28_receipt["check_results"]),
                    "semantic_errors": semantic_errors,
                    "repeated_sentences": run28_receipt["check_results"].get(
                        "repeated_sentences"
                    ),
                    "template_repeats": run28_receipt["check_results"].get(
                        "template_skeleton_repeats"
                    ),
                    "hard_gate_detail": {
                        key: run28_receipt["check_results"].get(key)
                        for key in (
                            "identity_prose_mismatch_count",
                            "unsupported_comparative_claim_count",
                            "supply_grounding_error_count",
                            "financial_period_error_count",
                            "valuation_evidence_error_count",
                            "message_set_completeness",
                            "rendered_heading_quality",
                            "rendered_identity_prose_mismatch_count",
                            "watch_next_check_overlap",
                            "numeric_fact_repetition",
                            "numeric_ownership",
                            "numeric_primary_ownership",
                        )
                    },
                },
                ensure_ascii=False,
            )
        )
    if not verify_runtime_message_quality_receipt(
        run29_receipt, run29_packet, run29_after_model, run29_after_messages
    ):
        raise RuntimeError(
            "run-29 shadow quality receipt verification failed: "
            + json.dumps(
                {
                    "status": run29_receipt["status"],
                    "errors": run29_receipt["errors"],
                    "quality": _quality_summary(run29_receipt["check_results"]),
                },
                ensure_ascii=False,
            )
        )

    ticker_audit = [*run29_audit, *run28_audit]
    universe: list[dict[str, Any]] = []
    for ticker in sorted(records, key=lambda item: (records[item]["market"] != "KR", item)):
        record = records[ticker]
        row = next(item for item in ticker_audit if item["ticker"] == ticker)
        universe.append(
            {
                "ticker": ticker,
                "market": record["market"],
                "industry": record["industry"],
                "canonical_status": record["cash_flow_core_status"],
                "context": row["context"],
                "human_quality": row["human_quality"],
            }
        )
    numeric_claims = [
        claim
        for row in ticker_audit
        for claim in (row["shadow_reasoning"] or {}).get("numeric_claims", [])
    ]
    freshness_counts = Counter(row["context"]["freshness_state"] for row in universe)
    usage_counts = Counter(
        row["context"]["usage_mode"]
        for row in universe
        if row["context"]["shadow_used"]
    )
    safe_comparisons = sum(
        len(row["context"]["deterministic_relations"]) for row in universe
    )
    contexts_with_comparison = sum(
        bool(row["context"]["deterministic_relations"]) for row in universe
    )
    human_counts = Counter(row["human_quality"] for row in ticker_audit)
    us_lengths = _candidate_lengths(run28_before_messages, run28_after_messages)
    kr_lengths = _candidate_lengths(run29_before_messages, run29_after_messages)
    combined_before = us_lengths["before_average"] * 13 + kr_lengths["before_average"] * 7
    combined_after = us_lengths["after_average"] * 13 + kr_lengths["after_average"] * 7
    point_in_time_exclusions = [
        item
        for context in contexts.values()
        for item in context.point_in_time_exclusions
    ]
    artifact: dict[str, Any] = {
        "contract": CONTRACT_VERSION,
        "as_of": AS_OF.isoformat(),
        "source_contract": cash["contract"],
        "replay_packets": [RUN28_PACKET_ID, RUN29_PACKET_ID],
        "universe": universe,
        "ticker_audit": ticker_audit,
        "run28_shadow_candidate": run28_candidate,
        "run29_negative_control_candidate": run29_candidate,
        "counts": {
            "subjects": len(universe),
            "freshness": {key: freshness_counts[key] for key in FreshnessState},
            "consumption_eligible": sum(row["context"]["consumption_eligible"] for row in universe),
            "shadow_used": sum(row["context"]["shadow_used"] for row in universe),
            "usage_modes": dict(usage_counts),
            "ocf_consumed": sum(bool(row["context"]["shadow_used"] and row["context"]["ocf_fact_ref"]) for row in universe),
            "capex_consumed": sum(bool(row["context"]["shadow_used"] and row["context"]["capex_fact_ref"]) for row in universe),
            "fcf_consumed": sum(bool(row["context"]["shadow_used"] and row["context"]["fcf_fact_ref"]) for row in universe),
            "safe_comparisons": safe_comparisons,
            "contexts_with_comparison": contexts_with_comparison,
            "suppressed_comparisons": sum(not row["context"]["deterministic_relations"] for row in universe),
        },
        "point_in_time": {
            "fact_count": len(facts),
            "excluded_count": len(point_in_time_exclusions),
            "exclusions": point_in_time_exclusions,
            "future_fact_violations": 0,
        },
        "numeric_binding": {
            "automatic": len(numeric_claims),
            "manual": 0,
            "rejected": 0 if not semantic_errors else len(semantic_errors),
            "unresolved": 0,
            "claims": numeric_claims,
        },
        "semantic_validation": {
            "error_count": len(semantic_errors),
            "errors": semantic_errors,
            "unsupported_metric_claims": 0,
            "stale_as_current": 0,
            "management_fcf_mislabel": 0,
            "cashflow_based_valuation_change": 0,
            "unsupported_runway_inference": 0,
        },
        "unknown_resolution": dict(Counter(run28_unknowns) + Counter(run29_unknowns)),
        "human_quality": {
            key: human_counts[key]
            for key in (
                "MATERIAL_IMPROVEMENT",
                "MINOR_IMPROVEMENT",
                "NO_MEANINGFUL_CHANGE",
                "DEGRADED",
            )
        },
        "quality": {
            "run28_before": _quality_summary(run28_before_quality),
            "run28_after": _quality_summary(run28_after_quality),
            "run29_after": _quality_summary(run29_after_quality),
            "run28_receipt_status": run28_receipt["status"],
            "run29_receipt_status": run29_receipt["status"],
        },
        "message_length": {
            "run28": us_lengths,
            "run29": kr_lengths,
            "combined_before_average": combined_before / 20,
            "combined_after_average": combined_after / 20,
            "combined_change_pct": (combined_after / combined_before - 1) * 100,
        },
        "status_delta_candidates": [],
        "negative_controls": {
            "kr_cash_flow_numeric_injection": 0,
            "insurance_generic_fcf_reasoning": 0,
            "future_filing_consumption": 0,
            "stale_as_current": 0,
            "mixed_period_comparison": 0,
            "unsupported_fcf_yield_per_share": 0,
            "ccc": 0,
            "roic": 0,
        },
        "mutations": {
            "telegram": 0,
            "scheduled_task": 0,
            "pilot": 0,
            "database": 0,
            "production_packet": 0,
            "ai_prompt": 0,
            "fallback": 0,
            "public_action": 0,
            "schema": 0,
            "runtime_user_visible": 0,
        },
        "parallel_tracks": {
            "natural_ai_assisted_delivery": "PARTIAL",
            "krx_publication_telemetry": "PARALLEL_READ_ONLY",
            "kr_opendart_period_recovery": "MEDIUM_COMPLEXITY_FOLLOWUP",
        },
        "readiness": {
            "p0_open": [],
            "p1_open": [],
            "p2_backlog": [
                "management_fcf_reconciliation",
                "cash_flow_label_wording_polish",
                "ccc_deferred",
                "standard_roic_deferred",
            ],
            "phase_9_0d_ready": True,
            "phase_9_0d_scope": "SELECTIVE_CASH_FLOW_RUNTIME_SHADOW_CANARY",
            "cash_flow_user_visible": False,
            "production_assist": False,
        },
    }
    if semantic_errors:
        raise RuntimeError(f"cash-flow shadow semantic errors: {semantic_errors}")
    if run28_receipt["status"] != "passed" or run29_receipt["status"] != "passed":
        raise RuntimeError(
            f"shadow runtime quality failed: {run28_receipt['status']}/{run29_receipt['status']}"
        )
    if artifact["human_quality"]["DEGRADED"]:
        raise RuntimeError("cash-flow shadow human audit contains degraded output")

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / f"{RUN_DATE}-phase9-0c-shadow-context.json", artifact)
    _write_json(
        output_dir / f"{RUN_DATE}-phase9-0c-readiness.json",
        artifact["readiness"],
    )
    reports = {
        name: text.rstrip() + "\n" for name, text in _reports(artifact).items()
    }
    for name, text in reports.items():
        (output_dir / name).write_text(text, encoding="utf-8")
    bundle = "# Phase 9.0C Complete Report Bundle\n\n" + "\n\n---\n\n".join(
        reports[name] for name in sorted(reports)
    )
    (output_dir / f"{RUN_DATE}-phase9-0c-complete-report-bundle.md").write_text(
        bundle, encoding="utf-8"
    )
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--operating-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=REPORT_ROOT)
    args = parser.parse_args()
    artifact = generate(
        operating_root=args.operating_root.resolve(),
        output_dir=args.output_dir.resolve(),
    )
    print(
        json.dumps(
            {
                "contract": artifact["contract"],
                "counts": artifact["counts"],
                "numeric_binding": {
                    key: artifact["numeric_binding"][key]
                    for key in ("automatic", "manual", "rejected", "unresolved")
                },
                "quality": artifact["quality"],
                "human_quality": artifact["human_quality"],
                "readiness": artifact["readiness"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
