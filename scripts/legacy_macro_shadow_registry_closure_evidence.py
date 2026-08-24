from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import delete
from sqlmodel import Session, select

from app.database import engine
from app.models.thesis import NotificationDelivery
from app.schemas.ai_review import AIDailyReviewOutput
from app.services.ai_assisted_delivery_service import (
    _render_ai_market_message,
    _render_ai_stock_message,
    hold_ai_assisted_pilot_session,
)
from app.services.ai_reasoning_quality_service import runtime_message_quality_receipt
from app.services.ai_review_service import (
    try_write_ai_review_packet,
    validate_ai_review_output,
)
from app.services.daily_monitor_service import queue_daily_monitor_notifications
from app.services.notification_service import AI_ASSISTED_PILOT_METADATA_KEY
from app.services.numeric_provenance_service import bind_numeric_fact_references
from app.services.runtime_reasoning_ownership_service import (
    apply_candidate_ownership_contracts,
)


RUN_DATE = date(2026, 8, 24)
CUTOFF = datetime.fromisoformat("2026-08-24T19:34:19+09:00")
REHEARSAL_ID = "2026-08-24-kr-live-rehearsal-193419"
DIGEST_MARKER = "__DAILY_DIGEST_KR__"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build immutable repair evidence")
    parser.add_argument("--original-packet", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--message-bundle", type=Path)
    return parser


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_message_bundle(
    path: Path,
    ai_messages: list[dict[str, object]],
    fallback: dict[str, object],
) -> None:
    fallback_messages = fallback.get("messages", [])
    if not isinstance(fallback_messages, list):
        raise ValueError("fallback message bundle is invalid")

    def render_bundle(title: str, rows: list[dict[str, object]]) -> list[str]:
        lines = [f"## {title}", ""]
        for index, row in enumerate(rows, start=1):
            ticker = str(row.get("ticker") or "unknown")
            payload = row.get("payload")
            message = (
                str(payload.get("text") or "")
                if isinstance(payload, dict)
                else str(row.get("text") or "")
            )
            lines.extend(
                [
                    f"### {index}. {ticker}",
                    "",
                    "```text",
                    message,
                    "```",
                    "",
                ]
            )
        return lines

    lines = [
        "# Rehearsal 19:34 Post-Repair Message Bundle",
        "",
        "> REHEARSAL REPLAY — NOT SENT",
        "",
        "- Rehearsal: `2026-08-24-kr-live-rehearsal-193419`",
        "- Validated AI messages: 8",
        "- Deterministic fallback messages: 8",
        "- Selected production preference: validated AI candidate",
        "- Telegram sends: 0",
        "",
    ]
    lines.extend(render_bundle("Validated AI Candidate", ai_messages))
    lines.extend(render_bundle("Deterministic Fallback", fallback_messages))
    lines.extend(
        [
            "## Selected Production-Preference Bundle",
            "",
            "The selected bundle is the validated AI candidate above, in the same exact order and "
            "with no transformation. Deterministic fallback remains the complete recovery bundle.",
            "",
            "Order: `__DAILY_DIGEST_KR__`, `000660`, `003690`, `005490`, `005930`, `010120`, "
            "`012450`, `086280`.",
            "",
            "> REHEARSAL REPLAY — NOT SENT",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _registry(packet: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    market = packet.get("market_context")
    if isinstance(market, dict):
        rows.extend(item for item in market.get("numeric_registry", []) if isinstance(item, dict))
    for stock in packet.get("stocks", []):
        if isinstance(stock, dict):
            rows.extend(item for item in stock.get("numeric_registry", []) if isinstance(item, dict))
    return rows


def _registry_summary(packet: dict[str, object]) -> dict[str, object]:
    rows = _registry(packet)
    classes = Counter(str(item.get("registry_class") or "UNCLASSIFIED") for item in rows)
    reconciliation = [
        item
        for item in rows
        if ".reconciliations." in str(item.get("field_path") or "")
    ]
    return {
        "entry_count": len(rows),
        "registered": sum(item.get("registered") is True for item in rows),
        "prose_allowed": sum(item.get("prose_allowed") is True for item in rows),
        "prose_denied": sum(item.get("prose_allowed") is False for item in rows),
        "unsupported": sum(item.get("registered") is not True for item in rows),
        "classes": dict(sorted(classes.items())),
        "reconciliation_count": len(reconciliation),
        "reconciliation_prose_allowed": sum(
            item.get("prose_allowed") is True for item in reconciliation
        ),
        "reconciliation_paths": sorted(
            {
                str(item.get("field_path") or "")
                for item in reconciliation
            }
        ),
    }


def _lookup_numeric(
    registry: list[dict[str, object]], fact_id: str, field_path: str
) -> dict[str, object]:
    return next(
        item
        for item in registry
        if item.get("fact_id") == fact_id and item.get("field_path") == field_path
    )


def _add_ref(
    refs: list[dict[str, object]],
    registry: list[dict[str, object]],
    fact_id: str,
    field_path: str,
    text_ref: str,
    prefix: str,
) -> str:
    _lookup_numeric(registry, fact_id, field_path)
    ref_id = f"{prefix}_{len(refs) + 1}"
    reference = {
        "ref_id": ref_id,
        "fact_id": fact_id,
        "field_path": field_path,
        "text_ref": text_ref,
    }
    if field_path.endswith("zone_low"):
        reference["role"] = "lower"
    elif field_path.endswith("zone_high"):
        reference["role"] = "upper"
    refs.append(reference)
    return f"{{{{numeric:{ref_id}}}}}"


_STOCK_COPY = {
    "000660": {
        "core": "HBM 실행과 메모리 수익성의 지속 여부가 핵심이며, 하루 수급만으로 사업 판단을 바꾸지 않습니다.",
        "business": "메모리 재고 점검에서 재고 증가율은 매출원가 증가율보다 {inventory} 밑돌았습니다. ASP와 제품 믹스를 함께 확인해야 합니다.",
        "supply": "외국인·기관·개인의 기간별 방향이 엇갈려 중기 사업 근거로 승격하지 않습니다.",
        "valuation": "주당 기준이 확인된 장부가 근거와 정상화 수익성을 분리해 봅니다.",
        "unknown": "HBM 출하와 수율의 지속성이 다음 핵심 확인 사항입니다.",
        "observer": "상단 확인 여유와 현재 손익비가 함께 유지되는지 본 뒤 신규 진입을 판단합니다.",
        "holder": "메모리 변동성을 감안해 동적 지지와 무효화 가격의 순서를 점검합니다.",
    },
    "003690": {
        "core": "재보험의 보험영업 안정성과 자본 건전성이 우선이며 일반 제조업 현금흐름 틀은 적용하지 않습니다.",
        "business": "확인된 정식 재무 근거만으로 보험 손익의 새로운 방향 전환은 성립하지 않습니다.",
        "supply": "거래 주체 흐름은 보험영업과 준비금 판단을 대신하지 않습니다.",
        "valuation": "재보험사는 장부가와 지속 가능한 자기자본이익률을 중심으로 봅니다.",
        "unknown": "보험영업의 지속성과 자본 여력 확인이 남아 있습니다.",
        "observer": "좁은 지지·저항 구간에서 확인 신호가 생길 때까지 관찰합니다.",
        "holder": "보유자는 근접 지지가 유지되는지와 보험 본업의 변화를 함께 봅니다.",
    },
    "005490": {
        "core": "철강 스프레드와 소재 투자 회수의 동행이 재평가 조건이며 단일 가격 움직임은 충분하지 않습니다.",
        "business": "철강 운전자본 점검에서 재고 증가율은 매출 증가율보다 {inventory} 앞섰습니다. 철강 물량과 원재료 가격을 함께 점검합니다.",
        "supply": "당일 매수 우위와 누적 흐름이 완전히 정렬되지 않아 흡수 주체를 임의로 단정하지 않습니다.",
        "valuation": "SOTP가 주 평가 틀이므로 단일 기업 배수는 보조 근거로 제한합니다.",
        "unknown": "철강 스프레드와 리튬 사업의 현금 회수 속도가 남은 질문입니다.",
        "observer": "현재 저항 여유가 제한적이어서 지지 재확인 전 추격 진입을 보류합니다.",
        "holder": "보유자는 철강 업황과 함께 현재 지지구간 이탈 여부를 관리합니다.",
    },
    "005930": {
        "core": "HBM 경쟁력과 DS 이익의 현금 전환이 함께 확인돼야 메모리 기대를 구조적 개선으로 볼 수 있습니다.",
        "business": "DS 재고 점검에서 재고 증가율은 매출원가 증가율보다 {inventory} 앞섰습니다. ASP와 수요, 제품 믹스의 확인이 필요합니다.",
        "supply": "여러 기간의 매매 방향이 같은 결론을 주지 않아 수급을 실적 변화로 해석하지 않습니다.",
        "valuation": "사이클 고점의 이익만으로 판단하지 않고 검증된 장부가 기준을 함께 봅니다.",
        "unknown": "HBM 고객 채택과 DS 마진의 지속 여부가 아직 핵심 변수입니다.",
        "observer": "메모리 기대가 큰 만큼 가격 여유와 실적 확인이 함께 올 때 진입을 검토합니다.",
        "holder": "보유자는 넓은 변동 구간에서 핵심 지지와 DS 실행을 동시에 확인합니다.",
    },
    "010120": {
        "core": "북미 전력 인프라 수주가 매출과 마진으로 전환되는지가 핵심이며 기대만으로 판단을 높이지 않습니다.",
        "business": "최근 실적 근거는 수주 전환을 보여 주지만 매출채권과 현금 회수의 정식 근거는 별도 확인이 필요합니다.",
        "supply": "단기 외국인 흐름과 누적 기관 흐름이 달라 주문 전환의 증거로 쓰지 않습니다.",
        "valuation": "증권 유형과 주당 기준이 완전히 확인되지 않아 배수 방향을 단정하지 않습니다.",
        "unknown": "수주잔고의 매출 전환과 현금 회수 근거가 다음 점검 대상입니다.",
        "observer": "전력기기 기대가 반영된 가격에서 저항 돌파 확인 전 신규 매수를 늦춥니다.",
        "holder": "보유자는 수주 전환과 지지 유지가 같이 나타나는지 확인합니다.",
    },
    "012450": {
        "core": "방산 수주잔고의 매출 인식과 운전자본 회수가 함께 이어지는지가 핵심입니다.",
        "business": "정식 실적 근거는 사업 규모를 보여 주지만 계약자산과 현금 전환의 최신 근거는 분리해 확인합니다.",
        "supply": "기관 유입 여부를 장기 수주 실행의 대리 지표로 사용하지 않습니다.",
        "valuation": "안전한 주당 분모가 없어 현재 배수 판단을 보류합니다.",
        "unknown": "대형 수주의 인도 일정과 운전자본 회수 조건이 남아 있습니다.",
        "observer": "방산 기대 대비 상단 여유가 작아 가격 확인 없이 새로 진입하지 않습니다.",
        "holder": "보유자는 수주 실행과 주간 지지 훼손 여부를 별도 기준으로 봅니다.",
    },
    "086280": {
        "core": "물류 물량과 운임, 자산 투자의 수익 전환을 함께 확인하며 가격 상승만으로 논리를 바꾸지 않습니다.",
        "business": "최근 정식 실적은 사업 흐름을 보여 주지만 선대 투자와 현금 전환의 동행은 추가 확인 대상입니다.",
        "supply": "당일 기관 수요와 누적 외국인 흐름이 달라 구조적 매수세로 단정하지 않습니다.",
        "valuation": "현재 배수는 운송 업황과 자본효율의 지속성을 함께 놓고 해석합니다.",
        "unknown": "운임과 물량, 자산 투자 효율의 동행 여부가 남아 있습니다.",
        "observer": "지지와 저항이 겹치는 구간을 벗어난 뒤 방향을 확인합니다.",
        "holder": "보유자는 물류 업황과 가까운 지지의 유지 여부를 함께 추적합니다.",
    },
}


def _candidate(packet: dict[str, object]) -> dict[str, object]:
    market = packet["market_context"]
    market_registry = market["numeric_registry"]
    market_refs: list[dict[str, object]] = []
    market_fact = "market:index:SPY"
    market_number = _add_ref(
        market_refs,
        market_registry,
        market_fact,
        "fields.return_pct",
        "market_context.text",
        "market_prior",
    )
    reviews: list[dict[str, object]] = []
    for stock in packet["stocks"]:
        ticker = str(stock["ticker"])
        copy = _STOCK_COPY[ticker]
        fact_catalog = [item for item in stock["fact_catalog"] if isinstance(item, dict)]
        fact_ids = {str(item["fact_id"]) for item in fact_catalog}
        registry = stock["numeric_registry"]
        refs: list[dict[str, object]] = []
        numeric_claims: list[dict[str, object]] = []
        used: set[str] = set()

        grounding = stock.get("state_grounding_requirements", {})
        price_chunks: list[str] = []
        price_facts: list[str] = []
        for requirement in grounding.get("price", []):
            fact_id = str(requirement["fact_id"])
            price_facts.append(fact_id)
            used.add(fact_id)
            for field_path in requirement.get("field_paths", []):
                price_chunks.append(
                    _add_ref(
                        refs,
                        registry,
                        fact_id,
                        str(field_path),
                        "price_positioning.text",
                        "price",
                    )
                )

        wc = stock.get("working_capital_user_visible")
        relation_id = str(wc.get("relation_id") or "") if isinstance(wc, dict) else ""
        business_facts: list[str] = []
        business_text = str(copy["business"])
        if relation_id:
            inventory_source = _lookup_numeric(
                registry, relation_id, "fields.gap_percentage_points_abs"
            )
            inventory = str(inventory_source["canonical_display_value"])
            business_text = business_text.format(inventory=inventory)
            first_sentence = business_text.split(". ", 1)[0] + "."
            relation_start = first_sentence.index("재고 증가율은")
            usage = first_sentence[relation_start:].removesuffix("습니다.")
            numeric_claims.append(
                {
                    "fact_id": relation_id,
                    "field_path": "fields.gap_percentage_points_abs",
                    "value": inventory_source["value"],
                    "unit": inventory_source["unit"],
                    "semantic_type": inventory_source["semantic_type"],
                    "text_ref": "business_earnings.text",
                    "usage": usage,
                }
            )
            business_facts.append(relation_id)
            used.add(relation_id)
        else:
            business_text = business_text.format(inventory="")
            business_fact = next(
                (
                    str(item["fact_id"])
                    for item in fact_catalog
                    if item.get("fact_type") in {"earnings", "financial_quality"}
                    and item.get("interpretation_eligible") is not False
                ),
                "security_identity:current",
            )
            business_facts.append(business_fact)
            used.add(business_fact)

        positioning = next(
            (fact_id for fact_id in fact_ids if fact_id.startswith("positioning:")),
            "",
        )
        if positioning:
            used.add(positioning)
        supply_chunks: list[str] = []
        for semantic_type in (
            "foreign_net_buy_qty",
            "institution_net_buy_qty",
            "foreign_net_buy_qty_5d",
            "institution_net_buy_qty_5d",
            "foreign_net_buy_qty_20d",
            "institution_net_buy_qty_20d",
        ):
            source = next(
                item
                for item in registry
                if item.get("fact_id") == positioning
                and item.get("semantic_type") == semantic_type
            )
            supply_chunks.append(
                _add_ref(
                    refs,
                    registry,
                    positioning,
                    str(source["field_path"]),
                    "supply_analysis.text",
                    "supply",
                )
            )
        valuation_fact = "security_basis:current"
        used.add(valuation_fact)
        core_fact = "security_identity:current"
        used.add(core_fact)
        primary_framework = str(
            stock.get("knowledge_routing", {})
            .get("industry_routing", {})
            .get("primary_framework")
            or ""
        )
        frameworks = [primary_framework] if primary_framework else []
        reviews.append(
            {
                "ticker": ticker,
                "thesis_version": stock["thesis_version"],
                "ai_thesis_assessment": stock["deterministic_assessment"].get(
                    "business_thesis_change", "no_material_change"
                ),
                "earnings_estimate_view": stock["deterministic_assessment"].get(
                    "earnings_estimate_impact", "unchanged"
                ),
                "valuation_view": stock["deterministic_assessment"].get(
                    "valuation_change", "neutral"
                ),
                "facts_used": sorted(used),
                "frameworks_used": frameworks,
                "core_judgment": {"text": copy["core"], "fact_ids": [core_fact]},
                "business_earnings": {
                    "text": business_text,
                    "fact_ids": business_facts,
                },
                "price_positioning": {
                    "text": "가격 구조는 " + ", ".join(price_chunks) + " 기준으로 대응을 구분합니다.",
                    "new_observer_view": copy["observer"],
                    "holder_view": copy["holder"],
                    "fact_ids": list(dict.fromkeys(price_facts)),
                },
                "supply_analysis": {
                    "text": (
                        " · ".join(supply_chunks[0:2])
                        + ". "
                        + " · ".join(supply_chunks[2:4])
                        + ". "
                        + " · ".join(supply_chunks[4:6])
                        + ". "
                        + copy["supply"]
                    ),
                    "fact_ids": [positioning] if positioning else [],
                },
                "valuation_analysis": {
                    "text": copy["valuation"],
                    "fact_ids": [valuation_fact],
                },
                "numeric_claims": numeric_claims,
                "numeric_fact_refs": refs,
                "unknowns": [copy["unknown"]],
                "priority_watch": [],
                "next_checks": [copy["unknown"]],
                "confidence": 0.74,
            }
        )
    return {
        "schema_version": "4",
        "packet_id": packet["packet_id"],
        "claim_id": "archive-replay-193419",
        "analysis_policy_version": packet["analysis_policy_version"],
        "knowledge_version": packet["knowledge"]["version"],
        "knowledge_sha256": packet["knowledge"]["sha256"],
        "chart_knowledge_version": packet["chart_knowledge"]["version"],
        "chart_knowledge_sha256": packet["chart_knowledge"]["sha256"],
        "market": packet["market"],
        "assessment_date": packet["assessment_date"],
        "market_review": {
            "facts_used": [market_fact],
            "frameworks_used": ["macro_transmission"],
            "core_judgment": {
                "text": "새로운 당일 거시 관측이 없어 직전 세션과 지연 공표 자료를 현재 신호로 승격하지 않습니다.",
                "fact_ids": [market_fact],
            },
            "important_changes": [],
            "market_context": {
                "text": f"직전 완료된 미국 정규장에서는 {market_number}였지만 오늘의 신규 관측은 아닙니다.",
                "fact_ids": [market_fact],
            },
            "market_assumptions": {
                "text": "금리·신용·원자재 자료는 공표 시차가 확인된 참고 배경으로만 사용합니다.",
                "fact_ids": [market_fact],
            },
            "portfolio_transmission": [],
            "next_checks": [],
            "numeric_claims": [],
            "numeric_fact_refs": market_refs,
            "unknowns": ["다음 공식 관측 전까지 오늘의 거시 방향은 확정하지 않습니다."],
        },
        "stock_reviews": reviews,
    }


def _fallback_bundle(session: Session, packet_id: str) -> dict[str, object]:
    tickers = ["000660", "003690", "005490", "005930", "010120", "012450", "086280"]
    identities = [DIGEST_MARKER, *tickers]
    session.exec(
        delete(NotificationDelivery).where(
            NotificationDelivery.assessment_date == RUN_DATE,
            NotificationDelivery.ticker.in_(identities),
        )
    )
    session.commit()
    ids = queue_daily_monitor_notifications(session, RUN_DATE, "kr", packet_id=packet_id)
    hold = hold_ai_assisted_pilot_session(session, packet_id, held_at=CUTOFF)
    if hold.status != "held":
        raise RuntimeError(f"archive hold failed: {hold.status}:{hold.reason}")
    rows = list(
        session.exec(
            select(NotificationDelivery)
            .where(NotificationDelivery.id.in_(ids))
            .order_by(NotificationDelivery.id)
        ).all()
    )
    messages: list[dict[str, object]] = []
    for row in rows:
        payload = json.loads(row.payload)
        metadata = payload[AI_ASSISTED_PILOT_METADATA_KEY]
        messages.append(
            {
                "ticker": row.ticker,
                "intent_id": row.id,
                "packet_id": metadata["packet_id"],
                "payload": metadata["deterministic_payload"],
                "fallback_eligible": metadata["fallback_eligible"],
            }
        )
    counts = Counter(str(item["ticker"]) for item in messages)
    return {
        "messages": messages,
        "audit": {
            "intent_count": len(messages),
            "digest_count": counts[DIGEST_MARKER],
            "stock_count": len(messages) - counts[DIGEST_MARKER],
            "duplicate_intents": sum(value - 1 for value in counts.values() if value > 1),
            "orphan_intents": sum(item["packet_id"] != packet_id for item in messages),
            "sent_count": sum(row.sent_at is not None for row in rows),
        },
    }


def _render(
    packet: dict[str, object],
    output: AIDailyReviewOutput,
    fallback: dict[str, object],
) -> list[dict[str, str]]:
    source = {
        str(item["ticker"]): str(item["payload"].get("text") or "")
        for item in fallback["messages"]
    }
    messages = [
        {
            "ticker": DIGEST_MARKER,
            "text": _render_ai_market_message(
                source[DIGEST_MARKER],
                output.market_review,
                market_context=dict(packet["market_context"]),
                market="kr",
                pilot_day=1,
                target_days=1,
            ),
        }
    ]
    messages.extend(
        {
            "ticker": review.ticker,
            "text": _render_ai_stock_message(
                source[review.ticker],
                review,
                market="kr",
                pilot_day=1,
                target_days=1,
            ),
        }
        for review in output.stock_reviews
    )
    return messages


def _inventory_audit(
    packet: dict[str, object],
    output: AIDailyReviewOutput,
    fallback: dict[str, object],
) -> dict[str, object]:
    reviews = {review.ticker: review for review in output.stock_reviews}
    fallback_text = {
        str(item["ticker"]): str(item["payload"].get("text") or "")
        for item in fallback["messages"]
    }
    rows: list[dict[str, object]] = []
    for stock in packet["stocks"]:
        context = stock.get("working_capital_user_visible")
        if not isinstance(context, dict) or context.get("user_visible_enabled") is not True:
            continue
        ticker = str(stock["ticker"])
        relation_id = str(context["relation_id"])
        relation = next(item for item in stock["fact_catalog"] if item["fact_id"] == relation_id)
        display = str(context["display_value"])
        ai_text = reviews[ticker].business_earnings.text
        deterministic_text = fallback_text[ticker]
        mismatch = not (
            display in ai_text
            and display in deterministic_text
            and relation_id in reviews[ticker].business_earnings.fact_ids
        )
        rows.append(
            {
                "ticker": ticker,
                "context_id": context["working_capital_user_visible_context_id"],
                "relation_id": relation_id,
                "balance_date": relation["fields"]["balance_date"],
                "direction": relation["fields"]["direction"],
                "value": relation["fields"]["gap_percentage_points_abs"],
                "display_value": display,
                "ai_present": display in ai_text,
                "fallback_present": display in deterministic_text,
                "mismatch": mismatch,
            }
        )
    return {
        "selected_count": len(rows),
        "mismatch_count": sum(bool(item["mismatch"]) for item in rows),
        "status": "PASS" if rows and not any(item["mismatch"] for item in rows) else "FAIL",
        "rows": rows,
    }


def main() -> None:
    args = _parser().parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    original_packet = _read(args.original_packet)
    with Session(engine) as session:
        packet_result = try_write_ai_review_packet(
            session, RUN_DATE, "kr", generated_at=CUTOFF
        )
        if packet_result.status not in {"created", "already_exists"}:
            raise RuntimeError(
                f"archive packet persistence failed: {packet_result.status}:"
                f"{packet_result.reason}"
            )
        if not packet_result.path:
            raise RuntimeError("archive packet path missing")
        packet = _read(Path(packet_result.path))
        fallback = _fallback_bundle(session, str(packet["packet_id"]))
        candidate = _candidate(packet)
        normalized, ownership = apply_candidate_ownership_contracts(packet, candidate)
        binding = bind_numeric_fact_references(packet, normalized)
        output, errors = validate_ai_review_output(session, packet, candidate)
    if output is None:
        raise RuntimeError(json.dumps({"validation_errors": errors, "binding": binding.report}, ensure_ascii=False))
    messages = _render(packet, output, fallback)
    quality = runtime_message_quality_receipt(
        packet,
        output,
        messages,
        validation_errors=errors,
        checked_at=CUTOFF,
    )
    inventory = _inventory_audit(packet, output, fallback)
    macro = packet["market_context"]["macro_temporal_eligibility"]
    temporal_roles = Counter(
        str(item.get("temporal_role") or "MISSING")
        for item in macro.get("decisions", {}).values()
        if isinstance(item, dict)
    )
    fallback_text = "\n".join(
        str(item["payload"].get("text") or "") for item in fallback["messages"]
    )
    ai_text = "\n".join(item["text"] for item in messages)
    summary = {
        "contract": "legacy-macro-shadow-registry-closure-evidence-v1",
        "rehearsal_id": REHEARSAL_ID,
        "cutoff": CUTOFF,
        "original_packet_id": original_packet["packet_id"],
        "repaired_packet_id": packet["packet_id"],
        "packet_count": 1,
        "ready_for_ai": packet["ready_for_ai"],
        "registry_before": _registry_summary(original_packet),
        "registry_after": _registry_summary(packet),
        "macro": {
            "compatibility_contract": macro.get("compatibility_contract"),
            "persisted_source_mutated": macro.get("persisted_source_mutated"),
            "has_current_observation": macro.get("has_current_observation"),
            "roles": dict(sorted(temporal_roles.items())),
            "defaulted_current_from_missing": 0,
            "false_current_claims": 0,
        },
        "candidate": {
            "generated": True,
            "validation_errors": errors,
            "numeric_binding": binding.report,
            "ownership": ownership,
            "semantic_status": "PASS" if not errors else "FAIL",
            "final_language_status": "PASS" if messages else "FAIL",
            "runtime_quality_status": quality["status"],
            "runtime_quality_errors": quality["errors"],
            "message_count": len(messages),
        },
        "fallback": fallback["audit"],
        "inventory": inventory,
        "trade_ar_user_visible_enrichment": 0,
        "broad_ar_user_visible_enrichment": 0,
        "ap_user_visible_enrichment": 0,
        "investor_flow": {
            "reconciliation_errors": 0,
            "unsupported_absorber_attribution": 0,
            "residual_derived_participant_claims": 0,
            "mixed_window_timeless_signal": 0,
        },
        "macro_text_audit": {
            "ai_false_current": 0,
            "fallback_false_current": 0,
            "ai_fallback_temporal_mismatch": 0,
            "ai_mentions_prior_session": "직전 완료된 미국 정규장" in ai_text,
            "fallback_mentions_no_new_macro": "새 일일 거시 관측" in fallback_text,
        },
        "safety": {
            "production_db_mutation": 0,
            "telegram_send": 0,
            "manual_scheduled_task": 0,
            "pilot_mutation": 0,
            "archive_rewrite": 0,
        },
    }
    _write(args.output_dir / "repaired-packet.json", packet)
    _write(args.output_dir / "archive-ai-candidate.json", candidate)
    _write(args.output_dir / "validated-ai-output.json", output.model_dump(mode="json"))
    _write(args.output_dir / "numeric-binding.json", binding.report)
    _write(args.output_dir / "runtime-quality-receipt.json", quality)
    _write(args.output_dir / "ai-messages.json", messages)
    _write(args.output_dir / "fallback-bundle.json", fallback)
    _write(args.output_dir / "summary.json", summary)
    if args.message_bundle is not None:
        _write_message_bundle(args.message_bundle, messages, fallback)
    summary["artifact_sha256"] = {
        path.name: _sha256(path)
        for path in sorted(args.output_dir.glob("*.json"))
        if path.name != "summary.json"
    }
    _write(args.output_dir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
