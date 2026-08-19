from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sqlmodel import Session, create_engine, select

from app.models.macro import MacroObservation
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.services.ai_assisted_delivery_service import (
    _render_ai_market_message,
    _render_ai_stock_message,
)
from app.services.ai_reasoning_quality_service import runtime_message_quality_receipt
from app.services.ai_review_service import validate_ai_review_output
from app.services.daily_digest import build_daily_digest
from app.services.daily_digest_renderer import render_daily_digest
from app.services.notification_service import _assessment_report
from app.services.numeric_provenance_service import bind_numeric_fact_references


PACKET_ID = "2026-08-19-us-run-26-cd80a8e4d373"
OUTPUT_NAME = f"{PACKET_ID}--daily-review-v3.10--559ad45e4dd8.json"
OUTPUT_STEM = OUTPUT_NAME.removesuffix(".json")
SIX_ERROR_ATTEMPT = "1787095411"
TARGET_ATTEMPT = "1787096472"
NIGHT_FACT_IDS = {"market:night_futures:1", "market:night_futures:2"}
NIGHT_CONTRACT = "night-futures-session-basis-v1"
KST_SOURCE = (
    "https://global.krx.co.kr/contents/GLB/02/0201/"
    "0201041004/GLB0201041004.jsp"
)
RUN_DATE = date(2026, 8, 19)


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )


def _remove_night_facts(packet: dict[str, object]) -> dict[str, object]:
    repaired = copy.deepcopy(packet)
    context = repaired.get("market_context")
    if not isinstance(context, dict):
        raise ValueError("run-26 packet has no market_context")
    for key in ("fact_catalog", "numeric_registry"):
        values = context.get(key)
        if isinstance(values, list):
            context[key] = [
                item
                for item in values
                if not isinstance(item, dict)
                or str(item.get("fact_id") or "") not in NIGHT_FACT_IDS
            ]
    context["required_market_fact_ids"] = []
    context["night_futures"] = []
    context["night_futures_audit"] = {
        "contract": NIGHT_CONTRACT,
        "status": "UNAVAILABLE_BY_CONTRACT",
        "reason": (
            "The archived rows pair DAY and NIGHT records carrying the same BAS_DD. "
            "KRX defines the NIGHT trading day by its T+1 06:00 end, so that DAY "
            "record occurs later and cannot be the reference session."
        ),
        "source_business_date": "2026-08-18",
        "required_night_session_date": "2026-08-19",
        "required_reference_day_date": "2026-08-18",
        "source_payload_sha256": None,
    }
    context["night_futures_cautions"] = [
        "야간선물은 세션·기준가격 계약을 재현하지 못해 개장 전 신호에서 제외했습니다."
    ]
    return repaired


def _remove_night_language(output: dict[str, object]) -> dict[str, object]:
    repaired = copy.deepcopy(output)
    review = repaired.get("market_review")
    if not isinstance(review, dict):
        raise ValueError("run-26 output has no market_review")
    review["facts_used"] = [
        value for value in review.get("facts_used", []) if value not in NIGHT_FACT_IDS
    ]
    core = review.get("core_judgment")
    if isinstance(core, dict):
        core["text"] = (
            "{{numeric:m_soxx_core}}; {{numeric:m_oil_core}}. "
            "반도체의 상대 약세와 비용·물가 경로를 함께 확인할 환경입니다."
        )
        core["fact_ids"] = [
            value for value in core.get("fact_ids", []) if value not in NIGHT_FACT_IDS
        ]
    changes = review.get("important_changes")
    if isinstance(changes, list):
        review["important_changes"] = [
            item
            for item in changes
            if not isinstance(item, dict)
            or not set(item.get("fact_ids", [])).intersection(NIGHT_FACT_IDS)
        ]
    refs = review.get("numeric_fact_refs")
    if isinstance(refs, list):
        review["numeric_fact_refs"] = [
            item
            for item in refs
            if not isinstance(item, dict)
            or str(item.get("fact_id") or "") not in NIGHT_FACT_IDS
        ]
    claims = review.get("numeric_claims")
    if isinstance(claims, list):
        review["numeric_claims"] = [
            item
            for item in claims
            if not isinstance(item, dict)
            or str(item.get("fact_id") or "") not in NIGHT_FACT_IDS
        ]
    return repaired


def _merge_numeric_lead(value: str, *, relation: str) -> str:
    first, separator, remainder = value.partition(". ")
    if not separator or first.count("{{numeric:") < 2:
        return value
    return f"{first}{relation} {remainder}"


def _harden_replay_language(output: dict[str, object]) -> dict[str, object]:
    """Apply the existing no-shared-numeric-opener rule to immutable replay prose."""
    repaired = copy.deepcopy(output)
    reviews = repaired.get("stock_reviews")
    if not isinstance(reviews, list):
        return repaired
    for review in reviews:
        if not isinstance(review, dict):
            continue
        business = review.get("business_earnings")
        if isinstance(business, dict):
            text = str(business.get("text") or "")
            prefix = "현재 확인된 핵심 숫자는 "
            first, separator, remainder = text.partition(". ")
            if text.startswith(prefix) and separator and first.endswith("입니다"):
                business["text"] = (
                    f"{remainder.rstrip('.')}; {first}."
                )
        supply = review.get("supply_analysis")
        if isinstance(supply, dict):
            supply["text"] = _merge_numeric_lead(
                str(supply.get("text") or ""),
                relation="의 변화를 보면,",
            )
        valuation = review.get("valuation_analysis")
        if isinstance(valuation, dict):
            valuation["text"] = _merge_numeric_lead(
                str(valuation.get("text") or ""),
                relation="의 관계를 보면,",
            )
        typed_refs = review.get("valuation_interpretation_refs")
        if isinstance(typed_refs, list):
            for item in typed_refs:
                if not isinstance(item, dict):
                    continue
                if item.get("text_ref") == "valuation_analysis.text":
                    item["exact_text_span"] = _merge_numeric_lead(
                        str(item.get("exact_text_span") or ""),
                        relation="의 관계를 보면,",
                    )
    return repaired


def _fallback_map(payload: dict[str, object]) -> dict[str, str]:
    return {
        str(item.get("ticker") or ""): str(item.get("text") or "")
        for item in payload.get("messages", [])
        if isinstance(item, dict)
    }


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _zones_overlap(support: object, resistance: object) -> bool:
    support_value = _mapping(support)
    resistance_value = _mapping(resistance)
    support_low = _number(support_value.get("zone_low"))
    support_high = _number(support_value.get("zone_high"))
    resistance_low = _number(resistance_value.get("zone_low"))
    resistance_high = _number(resistance_value.get("zone_high"))
    if None in (support_low, support_high, resistance_low, resistance_high):
        return False
    return max(support_low, resistance_low) <= min(support_high, resistance_high)


def _fail_closed_overlapping_rr(price_context: dict[str, object]) -> None:
    reason = "nearest_support_resistance_overlap"
    chart = _mapping(price_context.get("chart"))
    chart_structure = _mapping(chart.get("structure"))
    monitoring = _mapping(price_context.get("monitoring_state"))
    current = _mapping(monitoring.get("current"))
    current_structure = _mapping(current.get("price_structure"))
    for structure in (chart_structure, current_structure):
        if not structure or not _zones_overlap(
            structure.get("active_support"),
            structure.get("active_resistance"),
        ):
            continue
        structure["risk_reward"] = {
            "available": False,
            "current_price": None,
            "support_entry": None,
            "nearest_target_enforced": True,
            "reason": reason,
        }
        chart_state = _mapping(structure.get("chart_state"))
        structure["chart_state"] = {
            "state": "WAIT",
            "confidence": "low",
            "reasons": ["support_resistance_overlap"],
            "blocking_unknowns": list(chart_state.get("blocking_unknowns") or []),
            "user_semantics": "overlapping_price_structure",
        }
        availability = _mapping(structure.get("availability"))
        if availability:
            availability["risk_reward"] = False
    delta = _mapping(monitoring.get("delta"))
    risk_reward = _mapping(current_structure.get("risk_reward"))
    if risk_reward.get("available") is False:
        delta["rr_current"] = None
        delta["rr_change"] = "unavailable_due_to_overlap"


def _repair_packet_overlapping_rr(packet: dict[str, object]) -> set[str]:
    affected: set[str] = set()
    stocks = packet.get("stocks")
    if not isinstance(stocks, list):
        return affected
    denied_fact_ids = {
        "chart:structure:risk_reward:current_price",
        "chart:structure:risk_reward:support_entry",
        "monitoring:risk_reward_transition",
    }
    for stock in stocks:
        if not isinstance(stock, dict):
            continue
        current_context = _mapping(stock.get("current_price_context"))
        if not _zones_overlap(
            current_context.get("active_support"),
            current_context.get("active_resistance"),
        ):
            continue
        ticker = str(stock.get("ticker") or "")
        affected.add(ticker)
        current_context["current_price_risk_reward"] = {
            "available": False,
            "ratio": None,
            "classification": None,
            "reason": "nearest_support_resistance_overlap",
        }
        chart = _mapping(stock.get("chart_context"))
        structure = _mapping(chart.get("structure"))
        if structure:
            structure["risk_reward"] = {
                "available": False,
                "current_price": None,
                "support_entry": None,
                "nearest_target_enforced": True,
                "reason": "nearest_support_resistance_overlap",
            }
            availability = _mapping(structure.get("availability"))
            if availability:
                availability["risk_reward"] = False
        _fail_closed_overlapping_rr(stock)
        for key in ("fact_catalog", "numeric_registry"):
            values = stock.get(key)
            if isinstance(values, list):
                stock[key] = [
                    item
                    for item in values
                    if not isinstance(item, dict)
                    or str(item.get("fact_id") or "") not in denied_fact_ids
                ]
        grounding = _mapping(stock.get("state_grounding_requirements"))
        price_requirements = grounding.get("price")
        if isinstance(price_requirements, list):
            grounding["price"] = [
                item
                for item in price_requirements
                if not isinstance(item, dict)
                or str(item.get("fact_id") or "") not in denied_fact_ids
            ]
    return affected


def _remove_numeric_refs(
    review: dict[str, object],
    denied_fact_ids: set[str],
) -> dict[str, list[str]]:
    refs_by_text: dict[str, list[str]] = {}
    refs = review.get("numeric_fact_refs")
    if not isinstance(refs, list):
        return refs_by_text
    kept: list[object] = []
    for item in refs:
        if not isinstance(item, dict) or str(item.get("fact_id") or "") not in denied_fact_ids:
            kept.append(item)
            continue
        refs_by_text.setdefault(str(item.get("text_ref") or ""), []).append(
            str(item.get("ref_id") or "")
        )
    review["numeric_fact_refs"] = kept
    return refs_by_text


def _drop_numeric_tokens(text_value: object, ref_ids: list[str]) -> str:
    text_value = str(text_value or "")
    for ref_id in ref_ids:
        token = f"{{{{numeric:{ref_id}}}}}"
        if f"; {token}" in text_value:
            text_value = text_value.replace(f"; {token}", "")
        elif f"{token}; " in text_value:
            text_value = text_value.replace(f"{token}; ", "")
        else:
            text_value = text_value.replace(token, "")
    return text_value.replace("..", ".").replace(". .", ". ")


def _repair_output_overlapping_rr(
    output: dict[str, object], affected: set[str]
) -> dict[str, object]:
    repaired = copy.deepcopy(output)
    denied_fact_ids = {
        "chart:structure:risk_reward:current_price",
        "chart:structure:risk_reward:support_entry",
        "monitoring:risk_reward_transition",
    }
    reviews = repaired.get("stock_reviews")
    if not isinstance(reviews, list):
        return repaired
    for review in reviews:
        if not isinstance(review, dict) or str(review.get("ticker") or "") not in affected:
            continue
        refs_by_text = _remove_numeric_refs(review, denied_fact_ids)
        for key in ("core_judgment", "price_positioning", "supply_analysis"):
            section = _mapping(review.get(key))
            text_ref = f"{key}.text"
            section["text"] = _drop_numeric_tokens(
                section.get("text"), refs_by_text.get(text_ref, [])
            )
            facts = section.get("fact_ids")
            if isinstance(facts, list):
                section["fact_ids"] = [
                    value for value in facts if str(value) not in denied_fact_ids
                ]
        core = _mapping(review.get("core_judgment"))
        core["text"] = (
            str(core.get("text") or "")
            .replace("가격 비대칭을", "가격 구조를")
            .replace("가격 비대칭", "가격 구조")
        )
        positioning = _mapping(review.get("price_positioning"))
        positioning["text"] = str(positioning.get("text") or "").replace(
            ". ",
            ". 가까운 지지·저항 구간이 겹쳐 현재가 기준 차트 손익비는 "
            "계산하지 않습니다. ",
            1,
        )
        supply = _mapping(review.get("supply_analysis"))
        supply["text"] = (
            "선택된 지지·저항 구간이 겹쳐 현재 손익비 전환은 비교하지 "
            "않습니다. 가격 경계와 사업 실행은 분리해 확인합니다."
        )
        for key in ("numeric_claims", "facts_used"):
            values = review.get(key)
            if isinstance(values, list):
                review[key] = [
                    item
                    for item in values
                    if (
                        str(item.get("fact_id") or "") not in denied_fact_ids
                        if isinstance(item, dict)
                        else str(item) not in denied_fact_ids
                    )
                ]
    return repaired


def _render_fallback_replay(session: Session) -> dict[str, str]:
    rendered: dict[str, str] = {}
    for ticker in ("GOOGL", "HUT", "RXRX", "WULF", "CORZ"):
        assessment = session.exec(
            select(ThesisAssessment)
            .where(
                ThesisAssessment.ticker == ticker,
                ThesisAssessment.assessment_date == RUN_DATE,
            )
            .order_by(ThesisAssessment.id.desc())
        ).first()
        if assessment is None:
            continue
        replay_assessment = ThesisAssessment(**assessment.model_dump())
        price_context = json.loads(replay_assessment.price_context or "{}")
        _fail_closed_overlapping_rr(price_context)
        replay_assessment.price_context = json.dumps(
            price_context,
            ensure_ascii=False,
            sort_keys=True,
        )
        watchlist = session.exec(
            select(WatchlistItem).where(WatchlistItem.ticker == ticker)
        ).first()
        thesis = session.exec(
            select(InvestmentThesis).where(
                InvestmentThesis.ticker == ticker,
                InvestmentThesis.version == assessment.thesis_version,
            )
        ).first()
        company = watchlist.company_name if watchlist else ticker
        rendered[ticker] = _assessment_report(replay_assessment, company, thesis)[0]
    return rendered


def _night_lineage(session: Session) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for series_code in (
        "KRX_KOSPI200_NIGHT_FUT",
        "KRX_KOSDAQ150_NIGHT_FUT",
    ):
        row = session.exec(
            select(MacroObservation)
            .where(MacroObservation.series_code == series_code)
            .order_by(MacroObservation.observed_at.desc())
        ).first()
        if row is None:
            continue
        raw = json.loads(row.raw_payload) if row.raw_payload else {}
        rows.append(
            {
                "fact_id": (
                    "market:night_futures:1"
                    if series_code == "KRX_KOSPI200_NIGHT_FUT"
                    else "market:night_futures:2"
                ),
                "series_code": series_code,
                "instrument_name": (
                    "KOSPI200" if "KOSPI200" in series_code else "KOSDAQ150"
                ),
                "instrument_code": raw.get("product"),
                "contract_code": raw.get("contract_code"),
                "provider": row.provider,
                "provider_endpoint": row.source_url,
                "source_record_id": None,
                "source_payload_sha256": None,
                "source_business_date": raw.get("trade_date"),
                "trading_date": raw.get("trade_date"),
                "contract_date": raw.get("expiry"),
                "source_timestamp": str(row.observed_at),
                "collection_timestamp": str(row.retrieved_at),
                "packet_as_of": "2026-08-19T08:07:00+09:00",
                "session_type": "AMBIGUOUS_ARCHIVED_PAIR",
                "session_open": None,
                "session_close": None,
                "raw_price": row.value,
                "raw_change_point": row.change_value,
                "raw_change_pct": row.change_pct,
                "comparison_price": row.previous_value,
                "comparison_date": raw.get("trade_date"),
                "comparison_session": "DAY_SAME_BAS_DD",
                "comparison_semantic": "same_business_date_day_close",
                "canonical_price_before": row.value,
                "canonical_change_point_before": row.change_value,
                "canonical_change_pct_before": row.change_pct,
                "canonical_after": "UNAVAILABLE_BY_CONTRACT",
                "root_cause": "reverse_chronological_same_bas_dd_pair",
            }
        )
    return rows


def _overlap_audit(session: Session) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    assessments = session.exec(
        select(ThesisAssessment).where(ThesisAssessment.assessment_date == RUN_DATE)
    ).all()
    for assessment in assessments:
        context = json.loads(assessment.price_context or "{}")
        monitoring = _mapping(context.get("monitoring_state"))
        current = _mapping(monitoring.get("current"))
        structure = _mapping(current.get("price_structure"))
        support = _mapping(structure.get("active_support"))
        resistance = _mapping(structure.get("active_resistance"))
        if not _zones_overlap(support, resistance):
            continue
        risk_reward = _mapping(structure.get("risk_reward"))
        current_rr = _mapping(risk_reward.get("current_price"))
        rows.append(
            {
                "ticker": assessment.ticker,
                "support_low": support.get("zone_low"),
                "support_high": support.get("zone_high"),
                "resistance_low": resistance.get("zone_low"),
                "resistance_high": resistance.get("zone_high"),
                "archived_rr_ratio": current_rr.get("ratio"),
                "repaired_rr": "UNAVAILABLE",
                "reason": "nearest_support_resistance_overlap",
            }
        )
    return sorted(rows, key=lambda item: str(item["ticker"]))


def _artifact_paths(source_root: Path) -> dict[str, Path]:
    archive = source_root / "data/ai_review/pilot/history/2026/08" / PACKET_ID
    return {
        "packet": source_root / "data/ai_review/inbox" / f"{PACKET_ID}.json",
        "ai_raw_output": source_root / "data/ai_review/rejected" / (
            f"{OUTPUT_NAME}.{TARGET_ATTEMPT}"
        ),
        "validation": source_root / "data/ai_review/rejected" / (
            f"{OUTPUT_NAME}.{TARGET_ATTEMPT}.validation.json"
        ),
        "six_error_validation": source_root / "data/ai_review/rejected" / (
            f"{OUTPUT_NAME}.{SIX_ERROR_ATTEMPT}.validation.json"
        ),
        "bound_output": source_root / "data/ai_review/history/2026/08" / (
            f"{OUTPUT_STEM}.numeric-binding.json"
        ),
        "rendered_fallback": archive / "fallback-messages.json",
        "runtime_receipt": archive / "delivery-result.json",
        "actual_sent_bundle": archive / "deterministic-messages.json",
        "archive_complete": archive / "validation-result.json",
    }


def _markdown_pair(before: str, after: str) -> str:
    return f"#### Before\n\n```text\n{before}\n```\n\n#### After\n\n```text\n{after}\n```"


def _generate_reports(
    output_dir: Path,
    *,
    artifacts: dict[str, Path],
    validation_before: dict[str, object],
    validation_after: dict[str, object],
    lineage: list[dict[str, object]],
    overlap_audit: list[dict[str, object]],
    before_fallback: dict[str, str],
    after_fallback: dict[str, str],
    before_digest: str,
    after_digest: str,
    ai_messages: list[dict[str, str]],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    hashes = {key: _sha256(path) for key, path in artifacts.items()}
    delta = {
        "contract": "phase8-5-4-run26-replay-v1",
        "packet_id": PACKET_ID,
        "source_artifact_sha256": hashes,
        "source_mutation_count": 0,
        "telegram_send_count": 0,
        "validation_before": validation_before,
        "validation_after": validation_after,
        "night_futures_after": "UNAVAILABLE_BY_CONTRACT",
        "zone_rr_audit": overlap_audit,
        "ai_rendered_message_count": len(ai_messages),
    }
    _write_json(output_dir / "20260819-run26-validation-delta.json", delta)
    _write_json(
        output_dir / "20260819-night-futures-lineage-audit.json",
        {
            "contract": NIGHT_CONTRACT,
            "accessed_date": "2026-08-19",
            "official_source": KST_SOURCE,
            "rows": lineage,
            "credential_exposure_count": 0,
        },
    )

    source_rows = "\n".join(
        f"| {item['fact_id']} | {item['raw_price']} | {item['comparison_price']} | "
        f"{item['raw_change_point']} | {item['canonical_after']} |"
        for item in lineage
    )
    root_cause = f"""# Run-26 Natural Live Root Cause

## Outcome

- Packet: `{PACKET_ID}`
- AI sent: `0`
- Deterministic fallback sent: `14/14`
- Duplicate fallback: `0`
- Original archive rewrites: `0`
- Telegram replay sends: `0`

## Failure Classes

- RXRX/WULF: `CANONICAL_SEMANTIC_BINDING`
- CORZ: `TYPED_VALUATION_OCCURRENCE`
- Night futures: `PROVIDER_CANONICALIZATION / SESSION_BASIS`
- Fallback: `RENDER_CONTEXT_PARITY`

## Immutable Evidence SHA256

""" + "\n".join(f"- {key}: `{value}`" for key, value in hashes.items()) + f"""

## Retrospective Result

- Target six-error attempt before: `{len(validation_before['errors'])}` errors
- Repaired replay after: `{len(validation_after['errors'])}` errors
- Full validator: `{'PASS' if validation_after['status'] == 'passed' else 'FAIL'}`
- Runtime message quality: `{validation_after['runtime_message_quality']}`
- Natural AI-assisted delivery remains `PARTIAL`; retrospective replay is not a live send.

## Zone / RR Audit

| Ticker | Support | Resistance | Archived RR | Repaired RR |
|---|---|---|---:|---|
""" + "\n".join(
        f"| {item['ticker']} | {item['support_low']}–{item['support_high']} | "
        f"{item['resistance_low']}–{item['resistance_high']} | "
        f"{item['archived_rr_ratio']}x | `{item['repaired_rr']}` |"
        for item in overlap_audit
    ) + """

The selected support and resistance zones overlap. The repaired backend and both
archive-only render paths therefore suppress current RR with
`nearest_support_resistance_overlap`; no zone or ratio is moved by hand.
"""
    (output_dir / "20260819-run26-natural-live-root-cause.md").write_text(
        root_cause, encoding="utf-8"
    )

    night_report = f"""# Night Futures Session-Basis Audit

Accessed: `2026-08-19`

KRX states that the night session runs from 18:00 to 06:00 and assigns the trading
day by the 06:00 end time. A session beginning on T is therefore recorded as T+1,
together with the later T+1 regular session. See the [official KRX Night Session
rules]({KST_SOURCE}).

The archived implementation paired DAY and NIGHT rows carrying the same `BAS_DD`.
That DAY close occurs after the NIGHT close, so the comparison is reverse
chronological. The visible changes were backend calculations, not AI calculations.

| Fact | Night price | Same-date DAY price | Before change | After |
|---|---:|---:|---:|---|
{source_rows}

For the 2026-08-19 morning packet, the required pair was 2026-08-19 NIGHT versus
2026-08-18 DAY. The 2026-08-19 provider query returned zero rows and the exact raw
provider response was not archived, so the user's approximately -4.29pt observation
cannot be reconstructed as a canonical value. The repaired result is
`UNAVAILABLE_BY_CONTRACT`; no value is hard-coded.

The new `{NIGHT_CONTRACT}` requires contract identity, NIGHT/DAY session identity,
reference/current prices, dates, source record IDs, raw payload SHA256 values, and a
deterministic change calculation. Missing or ambiguous evidence is suppressed.
"""
    (output_dir / "20260819-night-futures-session-basis-audit.md").write_text(
        night_report, encoding="utf-8"
    )

    repair_report = """# Run-26 AI Validation Repair

## Before

""" + "\n".join(f"- `{item}`" for item in validation_before["errors"]) + f"""

## Repair

- Visible current PBR references now bind to `fields.price_to_book` when the base
  value and historical `current_value` are equal. Historical median and percentile
  keep their own semantics.
- The phrase `실적 기반 가치평가` is recognized as an earnings metric span, so the
  CORZ quality-unknown occurrence is exactly covered without relaxing validation.
- The archived ambiguous night-futures facts and their prose were removed from the
  repaired packet copy.

## After

- Binding errors: `{validation_after['binding_error_count']}`
- Typed valuation errors: `{validation_after['typed_error_count']}`
- Full validator errors: `{len(validation_after['errors'])}`
- Result: `{validation_after['status'].upper()}`
- Manual numeric bindings: `0`
- Original delivery replay: `0`
"""
    (output_dir / "20260819-run26-ai-validation-repair.md").write_text(
        repair_report, encoding="utf-8"
    )

    fallback_sections = []
    for ticker in ("GOOGL", "HUT", "RXRX", "WULF", "CORZ"):
        if ticker in before_fallback and ticker in after_fallback:
            fallback_sections.append(
                f"## {ticker}\n\n"
                + _markdown_pair(before_fallback[ticker], after_fallback[ticker])
            )
    fallback_report = """# Fallback Valuation Context Parity

The fallback now derives its caution text from the sanitized metrics actually
rendered under `valuation-context-wording-v1`. A denied forward field no longer
causes safe visible PER to be described as excluded. Telegram sends: `0`.

""" + "\n\n".join(fallback_sections)
    (output_dir / "20260819-fallback-valuation-context-parity.md").write_text(
        fallback_report, encoding="utf-8"
    )

    preview = """# Run-26 Targeted Repair Preview

Archive-only immutable replay. Telegram sends: `0`.

## Market Digest

""" + _markdown_pair(before_digest, after_digest) + "\n\n## Repaired AI Candidate\n\n" + "\n\n".join(
        f"### {item['ticker']}\n\n```text\n{item['text']}\n```"
        for item in ai_messages
        if item["ticker"] in {"__DAILY_DIGEST__", "RXRX", "WULF", "CORZ"}
    )
    (output_dir / "20260819-run26-targeted-repair-preview.md").write_text(
        preview, encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Phase 8.5.4 run-26 evidence")
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--db-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("docs/reports"))
    args = parser.parse_args()

    artifacts = _artifact_paths(args.source_root)
    missing = [str(path) for path in artifacts.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing immutable evidence: " + ", ".join(missing))
    packet = _load(artifacts["packet"])
    raw_output = _load(artifacts["ai_raw_output"])
    before_validation = _load(artifacts["six_error_validation"])
    fallback_payload = _load(artifacts["rendered_fallback"])
    repaired_packet = _remove_night_facts(packet)
    overlapping_rr_tickers = _repair_packet_overlapping_rr(repaired_packet)
    repaired_output = _repair_output_overlapping_rr(
        _harden_replay_language(_remove_night_language(raw_output)),
        overlapping_rr_tickers,
    )

    db_uri = f"sqlite:///file:{args.db_path}?mode=ro&uri=true"
    engine = create_engine(db_uri)
    with Session(engine) as session:
        binding = bind_numeric_fact_references(
            repaired_packet,
            copy.deepcopy(repaired_output),
        )
        validated, errors = validate_ai_review_output(
            session,
            repaired_packet,
            copy.deepcopy(repaired_output),
        )
        if validated is None or errors:
            raise RuntimeError(f"run-26 repaired replay failed: {errors}")
        after_digest = render_daily_digest(
            build_daily_digest(session, RUN_DATE, market_scope="us")
        )
        before_fallback = _fallback_map(fallback_payload)
        after_fallback = _render_fallback_replay(session)
        market_message = _render_ai_market_message(
            after_digest,
            validated.market_review,
            market_context=repaired_packet["market_context"],
            market="us",
            pilot_day=3,
            target_days=5,
        )
        ai_messages = [
            {
                "ticker": "__DAILY_DIGEST__",
                "text": market_message,
                "logical_identity": f"{PACKET_ID}:market",
            }
        ]
        for review in validated.stock_reviews:
            ai_messages.append(
                {
                    "ticker": review.ticker,
                    "text": _render_ai_stock_message(
                        before_fallback[review.ticker],
                        review,
                        market="us",
                        pilot_day=3,
                        target_days=5,
                    ),
                    "logical_identity": f"{PACKET_ID}:stock:{review.ticker}",
                }
            )
        receipt = runtime_message_quality_receipt(
            repaired_packet,
            validated,
            ai_messages,
            binding_errors=binding.errors,
            validation_errors=errors,
            checked_at=datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc),
        )
        lineage = _night_lineage(session)
        overlap_audit = _overlap_audit(session)

    typed = binding.report.get("typed_valuation_interpretations", {})
    typed_errors = typed.get("errors", []) if isinstance(typed, dict) else []
    validation_after = {
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "binding_error_count": len(binding.errors),
        "typed_error_count": len(typed_errors),
        "numeric_binding": binding.report,
        "runtime_message_quality": receipt["status"],
        "runtime_message_quality_errors": receipt["errors"],
        "runtime_message_quality_checks": receipt["check_results"],
    }
    _generate_reports(
        args.output_dir,
        artifacts=artifacts,
        validation_before={
            "status": before_validation.get("status"),
            "errors": before_validation.get("errors", []),
        },
        validation_after=validation_after,
        lineage=lineage,
        overlap_audit=overlap_audit,
        before_fallback=before_fallback,
        after_fallback=after_fallback,
        before_digest=before_fallback["__DAILY_DIGEST__"],
        after_digest=after_digest,
        ai_messages=ai_messages,
    )
    print(
        json.dumps(
            {
                "status": validation_after["status"],
                "validator_errors": len(errors),
                "runtime_message_quality": receipt["status"],
                "reports": str(args.output_dir),
                "telegram_sends": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
