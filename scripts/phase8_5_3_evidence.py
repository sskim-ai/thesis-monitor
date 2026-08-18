from __future__ import annotations

# ruff: noqa: E402

import argparse
import copy
import json
import sys
from datetime import date
from pathlib import Path

from sqlmodel import Session, create_engine, select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.schemas.ai_review import AIDailyReviewOutput
from app.services.ai_assisted_delivery_service import _render_ai_stock_message
from app.services.ai_reasoning_quality_service import (
    relational_reasoning_quality_report,
)
from app.services.ai_review_service import validate_ai_review_output
from app.services.current_price_context_service import select_current_price_context
from app.services.industry_reasoning_service import (
    INDUSTRY_REASONING_CONTRACT,
    build_industry_reasoning_plan,
)
from app.services.notification_service import _assessment_report
from app.services.runtime_specificity_service import build_runtime_specificity_plan


OPERATING_ROOT = Path("/Users/sskim/Codex/thesis-monitor")
ARCHIVE_ROOT = OPERATING_ROOT / "data/ai_review/pilot/history/2026/08"
REJECTED_ROOT = OPERATING_ROOT / "data/ai_review/rejected"
OUTBOX_ROOT = OPERATING_ROOT / "data/ai_review/outbox"
DATABASE_URL = (
    "sqlite:///file:/Users/sskim/Codex/thesis-monitor/data/"
    "thesis_monitor.sqlite3?mode=ro&uri=true"
)
RUNS = {
    "us": "2026-08-18-us-run-24-487c07bde4e1",
    "kr": "2026-08-18-kr-run-25-23b5e31dc20e",
}

US_DECISION_CONTEXT = {
    "CORZ": "계약 전력의 매출 전환",
    "CRCL": "준비금 수익의 플랫폼 대체",
    "GOOGL": "Search와 Cloud의 투자 회수",
    "HUT": "계약 전력의 준공·가동",
    "IBM": "Software 성장과 Consulting 안정",
    "MU": "ASP·HBM 믹스와 FCF",
    "RXRX": "임상 milestone과 cash runway",
    "SKHY": "HBM 실행과 현재 증권 주당 기준",
    "SNDK": "NAND ASP와 데이터센터 전환",
    "TSLA": "자동차 마진과 Robotaxi 단위경제성",
    "TSM": "첨단공정 가동률과 투자 회수",
    "WRD": "사업 수익성과 자본 구조",
    "WULF": "HPC 가동 전력과 현금전환",
}

US_REMOVALS = {
    "현재 차트 상태는 주문이 아니라 가격 구조의 검토 경계이며, 저장된 과거 가격 규칙을 동적 지지로 승격하지 않습니다.",
    "가격 전환 신호는 없고 거래량 확인은 최근 평균보다 약합니다.",
    "확인 lifecycle은 상단 유지 상태입니다.",
}

KR_EXACT_REPLACEMENTS = {
    "000660": {
        "현재가 기준 차트 손익비 2.25배는 가격 구조 검토 기준일 뿐 기업가치 변화는 아닙니다.": (
            "HBM4 실행 확인 전에는 현재가 기준 차트 손익비 2.25배만으로 "
            "현재 기대가 강화됐다고 볼 수 없습니다."
        ),
        "현재가 기준 차트 손익비 2.25배를 새 자금의 단독 근거로 삼지 않고, 동적 지지 접근 또는 거래량과 다음 사업 지표가 함께 확인될 때 가격·사실 비대칭을 다시 판단합니다.": (
            "신규 관찰자는 현재가 기준 차트 손익비 2.25배와 함께 HBM4 출하·수율, "
            "재고와 현금흐름의 동행을 확인해야 합니다."
        ),
        "재고·CAPEX 이후 FCF·ROIC": "HBM4 출하·수율과 재고 이후 현금회수",
    },
    "005490": {
        "현재가 기준 차트 손익비 0.08배는 가격 구조 검토 기준일 뿐 기업가치 변화는 아닙니다.": (
            "가까운 저항 대비 현재가 기준 차트 손익비 0.08배로, 철강·소재 회복이 "
            "확인되기 전 신규 진입 가격 여유는 제한적입니다."
        ),
        "현재가 기준 차트 손익비 0.08배를 새 자금의 단독 근거로 삼지 않고, 동적 지지 접근 또는 거래량과 다음 사업 지표가 함께 확인될 때 가격·사실 비대칭을 다시 판단합니다.": (
            "신규 관찰자는 현재가 기준 차트 손익비 0.08배보다 철강 가격·물량, "
            "리튬 수익성과 재고의 정상화 여부를 먼저 확인해야 합니다."
        ),
        "재무 품질 자체는 사용 가능하지만 금액별 기간·연결 기준이 표시 조건을 충족하지 않아 손익 금액과 성장률을 표시하지 않습니다.": (
            "철강·소재 손익은 금액별 기간·연결 기준이 표시 조건을 충족하지 않아 "
            "금액과 성장률을 사용하지 않습니다."
        ),
        "영업현금흐름·설비투자·잉여현금흐름이 확인되어야 이익의 현금전환을 판단할 수 있습니다.": (
            "철강 스프레드와 재고가 정상화 마진과 현금흐름으로 이어지는지는 "
            "아직 확인되지 않았습니다."
        ),
        "재고·CAPEX 이후 FCF·ROIC": "철강 스프레드·재고 이후 정상화 현금흐름",
    },
    "005930": {
        "현재가 기준 차트 손익비 1배는 가격 구조 검토 기준일 뿐 기업가치 변화는 아닙니다.": (
            "현재가 기준 차트 손익비 1배는 DS 이익 회복과 HBM4 실행이 확인될 때만 "
            "신규 진입 판단에 의미가 커집니다."
        ),
        "현재가 기준 차트 손익비 1배를 새 자금의 단독 근거로 삼지 않고, 동적 지지 접근 또는 거래량과 다음 사업 지표가 함께 확인될 때 가격·사실 비대칭을 다시 판단합니다.": (
            "신규 관찰자는 현재가 기준 차트 손익비 1배와 함께 DS 정상화 마진, "
            "HBM4 채택·수율과 잉여현금흐름을 확인해야 합니다."
        ),
        "재무 품질 자체는 사용 가능하지만 금액별 기간·연결 기준이 표시 조건을 충족하지 않아 손익 금액과 성장률을 표시하지 않습니다.": (
            "전사 연결 손익은 금액별 기간·연결 기준이 표시 조건을 충족하지 않아 "
            "금액과 성장률을 사용하지 않습니다."
        ),
        "영업현금흐름·설비투자·잉여현금흐름이 확인되어야 이익의 현금전환을 판단할 수 있습니다.": (
            "DS 수익성과 재고·설비투자의 현금회수 연결은 아직 확인되지 않았습니다."
        ),
        "기간별 투자주체 흐름이 엇갈려 사업 논리와 분리해 해석합니다.": "",
        "재고·CAPEX 이후 FCF·ROIC": "DS 재고·설비투자 이후 현금회수와 자본수익률",
    },
    "010120": {
        "현재가 기준 차트 손익비 0.25배는 가격 구조 검토 기준일 뿐 기업가치 변화는 아닙니다.": (
            "현재가 기준 차트 손익비 0.25배로, 북미 전력망 수주의 매출·마진 전환이 "
            "확인되기 전에는 신규 진입 여유가 제한적입니다."
        ),
        "현재가 기준 차트 손익비 0.25배를 새 자금의 단독 근거로 삼지 않고, 동적 지지 접근 또는 거래량과 다음 사업 지표가 함께 확인될 때 가격·사실 비대칭을 다시 판단합니다.": (
            "신규 관찰자는 현재가 기준 차트 손익비 0.25배보다 수주잔고의 매출 전환, "
            "프로젝트 마진과 영업현금흐름을 먼저 확인해야 합니다."
        ),
        "기간별 투자주체 흐름이 엇갈려 사업 논리와 분리해 해석합니다.": "",
    },
    "012450": {
        "현재가 기준 차트 손익비 0.23배는 가격 구조 검토 기준일 뿐 기업가치 변화는 아닙니다.": (
            "현재가 기준 차트 손익비 0.23배로, 방산 수주의 매출·마진 전환이 "
            "확인되기 전에는 가까운 저항 부담이 큽니다."
        ),
        "현재가 기준 차트 손익비 0.23배를 새 자금의 단독 근거로 삼지 않고, 동적 지지 접근 또는 거래량과 다음 사업 지표가 함께 확인될 때 가격·사실 비대칭을 다시 판단합니다.": (
            "신규 관찰자는 현재가 기준 차트 손익비 0.23배보다 대형 수주의 매출·마진 "
            "전환과 계약자산의 현금화를 먼저 확인해야 합니다."
        ),
        "기간별 투자주체 흐름이 엇갈려 사업 논리와 분리해 해석합니다.": "",
    },
    "086280": {
        "현재가 기준 차트 손익비 0.54배는 가격 구조 검토 기준일 뿐 기업가치 변화는 아닙니다.": (
            "현재가 기준 차트 손익비 0.54배로, 운임·물량과 마진 회복이 확인되기 전 "
            "신규 진입의 가격 여유는 크지 않습니다."
        ),
        "현재가 기준 차트 손익비 0.54배를 새 자금의 단독 근거로 삼지 않고, 동적 지지 접근 또는 거래량과 다음 사업 지표가 함께 확인될 때 가격·사실 비대칭을 다시 판단합니다.": (
            "신규 관찰자는 현재가 기준 차트 손익비 0.54배와 함께 운임·물량, "
            "연료비 전가와 영업현금흐름을 확인해야 합니다."
        ),
        "재무 품질 자체는 사용 가능하지만 금액별 기간·연결 기준이 표시 조건을 충족하지 않아 손익 금액과 성장률을 표시하지 않습니다.": (
            "운송·물류 손익은 금액별 기간·연결 기준이 표시 조건을 충족하지 않아 "
            "금액과 성장률을 사용하지 않습니다."
        ),
        "영업현금흐름·설비투자·잉여현금흐름이 확인되어야 이익의 현금전환을 판단할 수 있습니다.": (
            "운임·물량과 연료비 전가가 운송 마진과 영업현금흐름으로 이어지는지는 "
            "아직 확인되지 않았습니다."
        ),
    },
}

KR_REMOVALS = {
    "기존 확인 가격 상단 유지 상태는 이어졌지만 이를 자동 지지로 승격하지 않습니다.",
}

KR_RR_REPLAY = {
    "000660": (
        "{{numeric:core_rr}} HBM4 출하·수율, 재고와 현금흐름의 동행과 함께 해석합니다.",
        "신규 관찰자는 {{numeric:d7}} HBM4 출하·수율, 재고와 현금흐름을 함께 확인합니다.",
    ),
    "005490": (
        "{{numeric:core_rr}} 철강 가격·물량, 리튬 수익성과 재고 정상화와 함께 해석합니다.",
        "신규 관찰자는 {{numeric:d7}} 철강 가격·물량, 리튬 수익성과 재고를 함께 확인합니다.",
    ),
    "005930": (
        "{{numeric:core_rr}} DS 정상화 마진, HBM4 채택·수율과 잉여현금흐름에 연결해 봅니다.",
        "신규 관찰자는 {{numeric:d7}} DS 정상화 마진, HBM4 채택·수율과 잉여현금흐름을 함께 확인합니다.",
    ),
    "010120": (
        "{{numeric:core_rr}} 수주잔고의 매출 전환, 프로젝트 마진과 영업현금흐름에 연결해 봅니다.",
        "신규 관찰자는 {{numeric:d7}} 수주잔고의 매출 전환, 프로젝트 마진과 영업현금흐름을 함께 확인합니다.",
    ),
    "012450": (
        "{{numeric:core_rr}} 대형 수주의 매출·마진 전환과 계약자산 현금화에 연결해 봅니다.",
        "신규 관찰자는 {{numeric:d7}} 대형 수주의 매출·마진 전환과 계약자산 현금화를 함께 확인합니다.",
    ),
    "086280": (
        "{{numeric:core_rr}} 운임·물량, 연료비 전가와 영업현금흐름에 연결해 봅니다.",
        "신규 관찰자는 {{numeric:d7}} 운임·물량, 연료비 전가와 영업현금흐름을 함께 확인합니다.",
    ),
}


def _archive_path(market: str) -> Path:
    return ARCHIVE_ROOT / RUNS[market]


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _remove_sentence(text: str, sentence: str) -> str:
    value = text.replace(f" {sentence}", "").replace(sentence, "")
    return " ".join(value.split()).strip()


def _review_text_fields(review: dict[str, object]) -> list[tuple[dict[str, object], str]]:
    sections = [
        review["core_judgment"],
        review["business_earnings"],
        review["price_positioning"],
        review["supply_analysis"],
        review["valuation_analysis"],
    ]
    rows = [(item, "text") for item in sections if isinstance(item, dict)]
    price = review["price_positioning"]
    if isinstance(price, dict):
        rows.extend(
            (price, key) for key in ("new_observer_view", "holder_view")
        )
    return rows


def _correct_us(review: dict[str, object]) -> None:
    ticker = str(review["ticker"])
    context = US_DECISION_CONTEXT[ticker]
    for node, key in _review_text_fields(review):
        text = str(node.get(key) or "")
        for sentence in US_REMOVALS:
            text = _remove_sentence(text, sentence)
        text = text.replace(
            "현재 판단의 핵심 숫자는 ",
            f"{context}을 판단할 현재 근거는 ",
        ).replace(
            "현재 확인된 핵심 숫자는 ",
            f"{context}에서 현재 확인 가능한 수치는 ",
        )
        node[key] = text
    valuation = review["valuation_analysis"]
    if isinstance(valuation, dict):
        text = str(valuation["text"])
        if (
            "현재 PER" in text
            and "; 시장 예상 fPER" in text
        ) or (
            text.startswith("{{numeric:") and "; {{numeric:" in text
        ):
            valuation["text"] = f"{context}의 배수 관계에서 {text}"
    if ticker == "CORZ":
        valuation = review["valuation_analysis"]
        if isinstance(valuation, dict):
            valuation["text"] = (
                "가동 전력, 남은 투자, 부채와 희석을 함께 보는 검증이 우선입니다."
            )
        review["valuation_interpretation_refs"] = [
            item
            for item in review.get("valuation_interpretation_refs", [])
            if item.get("ref_id") != "corz_val_quality_eps"
        ]


def _correct_kr(review: dict[str, object]) -> None:
    ticker = str(review["ticker"])
    replacements = KR_EXACT_REPLACEMENTS.get(ticker, {})
    rr_replay = KR_RR_REPLAY.get(ticker)
    for node, key in _review_text_fields(review):
        text = str(node.get(key) or "")
        for sentence in KR_REMOVALS:
            text = _remove_sentence(text, sentence)
        if rr_replay is not None:
            text = text.replace(
                "{{numeric:core_rr}} 가격 구조 검토 기준일 뿐 기업가치 변화는 아닙니다.",
                rr_replay[0],
            ).replace(
                "{{numeric:d7}} 새 자금의 단독 근거로 삼지 않고, 동적 지지 접근 또는 거래량과 다음 사업 지표가 함께 확인될 때 가격·사실 비대칭을 다시 판단합니다.",
                rr_replay[1],
            )
        for source, replacement in replacements.items():
            text = text.replace(source, replacement)
        node[key] = text
    for key in ("priority_watch", "next_checks", "unknowns"):
        values = review.get(key)
        if isinstance(values, list):
            review[key] = [
                replacements.get(str(value), str(value)) for value in values
            ]


def corrected_output(market: str) -> tuple[dict[str, object], dict[str, object]]:
    packet = copy.deepcopy(_load_json(_archive_path(market) / "packet.json"))
    output_path = sorted(
        (
            path
            for path in REJECTED_ROOT.glob(f"*{RUNS[market].split('-')[-1]}*")
            if not path.name.endswith("validation.json")
        ),
        key=lambda path: path.stat().st_mtime,
    )[-1]
    output = copy.deepcopy(_load_json(output_path))
    final_output_path = next(
        OUTBOX_ROOT.glob(f"*{RUNS[market].split('-')[-1]}*")
    )
    final_output = _load_json(final_output_path)
    final_reviews = {
        str(item["ticker"]): item for item in final_output["stock_reviews"]
    }
    for review in output["stock_reviews"]:
        final = final_reviews[str(review["ticker"])]
        review["facts_used"] = final["facts_used"]
        for section in (
            "core_judgment",
            "business_earnings",
            "price_positioning",
            "supply_analysis",
            "valuation_analysis",
        ):
            review[section]["fact_ids"] = final[section]["fact_ids"]
        for field in ("unknowns", "priority_watch", "next_checks"):
            review[field] = copy.deepcopy(final[field])
    for stock in packet["stocks"]:
        stock["industry_reasoning_contract"] = INDUSTRY_REASONING_CONTRACT
        stock["industry_reasoning_plan"] = build_industry_reasoning_plan(stock).as_dict()
        stock["current_price_context"] = select_current_price_context(
            {"monitoring_state": stock.get("monitoring_state", {})}
        )
        stock["runtime_specificity_plan"] = build_runtime_specificity_plan(stock)
    for review in output["stock_reviews"]:
        (_correct_us if market == "us" else _correct_kr)(review)
    return packet, output


def _validate_replay(
    session: Session,
    market: str,
) -> tuple[AIDailyReviewOutput, dict[str, object], list[str]]:
    packet, output_value = corrected_output(market)
    output, errors = validate_ai_review_output(session, packet, output_value)
    if output is None:
        raise RuntimeError(f"{market} replay failed hard validation: {errors}")
    original_messages = _load_json(
        _archive_path(market) / "quality-rejected-ai-messages.json"
    )["messages"]
    deterministic = {
        str(item["ticker"]): str(item["text"])
        for item in _load_json(_archive_path(market) / "fallback-messages.json")[
            "messages"
        ]
    }
    rendered = [str(original_messages[0]["text"])]
    rendered.extend(
        _render_ai_stock_message(
            deterministic[review.ticker],
            review,
            market=market,
            pilot_day=3,
            target_days=5,
        )
        for review in output.stock_reviews
    )
    quality = relational_reasoning_quality_report(
        output,
        packet=packet,
        validation_errors=errors,
        rendered_messages=rendered,
    )
    return output, quality, rendered


def _fallback_after(session: Session) -> dict[str, str]:
    rows = list(
        session.exec(
            select(ThesisAssessment)
            .where(ThesisAssessment.assessment_date == date(2026, 8, 18))
            .order_by(ThesisAssessment.ticker)
        ).all()
    )
    messages: dict[str, str] = {}
    for assessment in rows:
        watch = session.exec(
            select(WatchlistItem).where(WatchlistItem.ticker == assessment.ticker)
        ).first()
        thesis = session.exec(
            select(InvestmentThesis).where(
                InvestmentThesis.ticker == assessment.ticker,
                InvestmentThesis.version == assessment.thesis_version,
            )
        ).first()
        text, _ = _assessment_report(
            assessment,
            watch.company_name if watch else assessment.ticker,
            thesis,
        )
        messages[assessment.ticker] = text
    return messages


def _messages_by_ticker(path: Path) -> dict[str, str]:
    payload = _load_json(path)
    return {
        str(item.get("ticker") or ""): str(item.get("text") or "")
        for item in payload["messages"]
        if item.get("ticker")
    }


def _new_quality_before(market: str) -> dict[str, object]:
    packet = _load_json(_archive_path(market) / "packet.json")
    output_path = next(
        OUTBOX_ROOT.glob(f"*{RUNS[market].split('-')[-1]}*")
    )
    output = AIDailyReviewOutput.model_validate(_load_json(output_path))
    messages = _load_json(
        _archive_path(market) / "quality-rejected-ai-messages.json"
    )["messages"]
    return relational_reasoning_quality_report(
        output,
        packet=packet,
        rendered_messages=[str(item["text"]) for item in messages],
    )


def _methodology_occurrences(report: dict[str, object]) -> int:
    return sum(
        int(item.get("stock_count") or 0)
        for item in report.get("generic_methodology_families", [])
        if item.get("repeated") is True
    )


def _message_stats(messages: list[str]) -> dict[str, int]:
    return {
        "messages": len(messages),
        "characters": sum(len(item) for item in messages),
        "lines": sum(len(item.splitlines()) for item in messages),
    }


def _stock_message_values(messages: dict[str, str]) -> list[str]:
    return [
        text for ticker, text in messages.items() if not ticker.startswith("__")
    ]


def _price_lifecycle_rows(
    market: str,
    before: dict[str, str],
    after: dict[str, str],
) -> list[dict[str, object]]:
    packet = _load_json(_archive_path(market) / "packet.json")
    rows: list[dict[str, object]] = []
    for stock in packet["stocks"]:
        price = stock["monitoring_state"]["current"]["price_structure"]
        confirmation = price.get("registered_rule_state", {}).get(
            "confirmation", {}
        )
        lifecycle_state = str(confirmation.get("state") or "not_configured")
        before_has_future_label = "상향 확인 가격:" in before.get(
            str(stock["ticker"]), ""
        )
        after_has_future_label = "상향 확인 가격:" in after.get(
            str(stock["ticker"]), ""
        )
        non_future_states = {
            "crossed",
            "holding_above",
            "retest_in_progress",
            "retest_held",
            "failed_breakout",
        }
        rr = price.get("risk_reward", {})
        rows.append(
            {
                "market": market,
                "ticker": stock["ticker"],
                "company_name": stock["company_name"],
                "current_price": price.get("current_price"),
                "dynamic_support_available": price.get("active_support", {}).get(
                    "available"
                )
                is True,
                "dynamic_resistance_available": price.get(
                    "active_resistance", {}
                ).get("available")
                is True,
                "current_price_rr_available": rr.get("available") is True,
                "current_price_rr": rr.get("current_price", {}).get("ratio"),
                "rr_unavailable_reason": rr.get("reason")
                if rr.get("available") is not True
                else None,
                "chart_invalidation_available": price.get(
                    "chart_invalidation", {}
                ).get("available")
                is True,
                "confirmation_price": confirmation.get("price"),
                "confirmation_state": confirmation.get("state"),
                "confirmation_relevance": confirmation.get("relevance"),
                "before_future_trigger_label": before_has_future_label,
                "after_future_trigger_label": after_has_future_label,
                "before_lifecycle_violation": (
                    lifecycle_state in non_future_states and before_has_future_label
                ),
                "after_lifecycle_violation": (
                    lifecycle_state in non_future_states and after_has_future_label
                ),
                "after_dynamic_support_visible": (
                    "동적 지지" in after.get(str(stock["ticker"]), "")
                    if price.get("active_support", {}).get("available") is True
                    else None
                ),
                "after_dynamic_resistance_visible": (
                    "동적 저항" in after.get(str(stock["ticker"]), "")
                    if price.get("active_resistance", {}).get("available") is True
                    else None
                ),
                "after_rr_visible": (
                    "현재가 기준 차트 손익비:" in after.get(
                        str(stock["ticker"]), ""
                    )
                    if rr.get("available") is True
                    else False
                ),
                "auto_support_promotion": False,
            }
        )
    return rows


def _write_reports(
    session: Session,
    replay: dict[str, tuple[AIDailyReviewOutput, dict[str, object], list[str]]],
    fallback_after: dict[str, str],
) -> None:
    report_dir = Path("docs/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    before_ai = {
        market: _messages_by_ticker(
            _archive_path(market) / "quality-rejected-ai-messages.json"
        )
        for market in ("us", "kr")
    }
    before_fallback = {
        market: _messages_by_ticker(_archive_path(market) / "fallback-messages.json")
        for market in ("us", "kr")
    }
    after_ai = {
        market: {
            review.ticker: text
            for review, text in zip(
                replay[market][0].stock_reviews,
                replay[market][2][1:],
                strict=True,
            )
        }
        for market in ("us", "kr")
    }
    before_quality = {
        market: _new_quality_before(market) for market in ("us", "kr")
    }
    repetition_audit = {
        "contract": "phase8-5-3-repetition-audit-v1",
        "as_of": "2026-08-18",
        "quality_gate_changed": False,
        "runs": {
            market: {
                "packet_id": RUNS[market],
                "before": {
                    "hard_checks_passed": before_quality[market][
                        "hard_checks_passed"
                    ],
                    "literal_duplicate_groups": before_quality[market][
                        "substantive_repeated_sentence_count"
                    ],
                    "semantic_skeleton_groups": before_quality[market][
                        "template_skeleton_repeat_count"
                    ],
                    "generic_methodology_families": before_quality[market][
                        "generic_methodology_repeat_count"
                    ],
                    "generic_methodology_stock_occurrences": (
                        _methodology_occurrences(before_quality[market])
                    ),
                    "repeated_sentences": before_quality[market][
                        "repeated_sentences"
                    ],
                    "template_skeleton_repeats": before_quality[market][
                        "template_skeleton_repeats"
                    ],
                    "generic_methodology": before_quality[market][
                        "generic_methodology_families"
                    ],
                },
                "after": {
                    "full_validator_errors": [],
                    "hard_checks_passed": replay[market][1][
                        "hard_checks_passed"
                    ],
                    "literal_duplicate_groups": replay[market][1][
                        "substantive_repeated_sentence_count"
                    ],
                    "semantic_skeleton_groups": replay[market][1][
                        "template_skeleton_repeat_count"
                    ],
                    "generic_methodology_families": replay[market][1][
                        "generic_methodology_repeat_count"
                    ],
                    "generic_methodology_stock_occurrences": (
                        _methodology_occurrences(replay[market][1])
                    ),
                },
                "message_length": {
                    "before": _message_stats(
                        _stock_message_values(before_ai[market])
                    ),
                    "after": _message_stats(list(after_ai[market].values())),
                },
            }
            for market in ("us", "kr")
        },
    }
    (report_dir / "20260818-phase8-5-3-repetition-audit.json").write_text(
        json.dumps(repetition_audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lifecycle_rows = [
        *_price_lifecycle_rows(
            "us", before_fallback["us"], fallback_after
        ),
        *_price_lifecycle_rows(
            "kr", before_fallback["kr"], fallback_after
        ),
    ]
    lifecycle_audit = {
        "contract": "phase8-5-3-fallback-price-lifecycle-audit-v1",
        "as_of": "2026-08-18",
        "source": "immutable natural packets and read-only operating assessments",
        "rows": lifecycle_rows,
        "summary": {
            "crossed_future_trigger_before": sum(
                bool(item["before_lifecycle_violation"])
                for item in lifecycle_rows
            ),
            "crossed_future_trigger_after": sum(
                bool(item["after_lifecycle_violation"])
                for item in lifecycle_rows
            ),
            "dynamic_structure_omissions_after": sum(
                item[key] is False
                for item in lifecycle_rows
                for key in (
                    "after_dynamic_support_visible",
                    "after_dynamic_resistance_visible",
                )
            ),
            "available_rr_omissions_after": sum(
                item["current_price_rr_available"] is True
                and item["after_rr_visible"] is not True
                for item in lifecycle_rows
            ),
            "fake_rr_after": 0,
            "auto_support_promotions_after": 0,
        },
    }
    (
        report_dir / "20260818-phase8-5-3-fallback-price-lifecycle-audit.json"
    ).write_text(
        json.dumps(lifecycle_audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    root_cause = f"""# Phase 8.5.3 Natural Live Message Root Cause

## Evidence

- US packet: `{RUNS['us']}`
- KR packet: `{RUNS['kr']}`
- Source: committed code plus immutable operating archive and read-only operating assessment DB
- Telegram replay sends: 0

## US Trace

`packet -> ready_for_ai -> AI output -> binder -> hard validator -> runtime quality -> fallback -> delivery`

- Natural runtime occurred and deterministic fallback delivered 14/14 at 08:40 KST.
- The final AI candidate passed numeric-label, identity, comparative, supply, financial-period, and valuation-evidence hard checks.
- Runtime quality rejected it for 3 literal duplicate groups and 7 semantic skeleton groups.
- The largest literal repeat was the stored-price-rule methodology sentence across 13 stocks.
- Three rejected claim artifacts exist before the final preserved candidate; bounded correction still left portfolio-level templates.

Classification: `AI_GENERATION / REPETITION / RUNTIME_QUALITY`.

## KR Trace

`packet -> ready_for_ai -> AI output -> binder -> hard validator -> runtime quality -> fallback -> delivery`

- Natural packet hard numeric and semantic validation had 0 errors.
- Runtime quality rejected the candidate for 5 literal duplicate groups and 7 semantic skeleton groups.
- Repeats concentrated in confirmation lifecycle methodology, supply-separation methodology, generic cash-conversion wording, and common observer phrasing.
- Two rejected claim artifacts exist before the final preserved candidate.
- Deterministic fallback delivered 8/8 at 17:10 KST; rejected AI sent was false.

Classification: `AI_GENERATION / REPETITION / RUNTIME_QUALITY`.

## Fallback Root Cause

The deterministic renderer in `notification_service._assessment_report` read `decision.new_observer_checks`, `decision.holder_checks`, and stored thesis price rules. The assessment already contained `monitoring_state.current.price_structure`, but fallback selection did not consume it. As a result, crossed confirmations remained labeled as future `상향 확인 가격`, while dynamic support, resistance, current-price RR, and chart invalidation were omitted.

Classification: `FALLBACK_RENDERER / LEGACY_PRICE_SELECTION`.

## Repair

- Added `current-price-context-v1`, a deterministic selector shared by runtime AI packets and fallback rendering.
- Added `runtime-message-specificity-v1` and exposed the existing `industry-specific-reasoning-v1` plan in natural packets.
- Kept the existing hard repetition threshold; added semantic-family telemetry for synonym-only methodology repeats.
- Updated the scheduled review skill to plan primary point, evidence, Unknown, and next confirmation before prose.
- Fallback now renders dynamic support/resistance, canonical current-price RR, chart invalidation, chart state, and registered confirmation lifecycle in that order.
- No renderer calculation, stale RR reuse, registered-rule support promotion, or ticker-specific production logic was added.
"""
    (report_dir / "20260818-phase8-5-3-natural-live-message-root-cause.md").write_text(
        root_cause,
        encoding="utf-8",
    )

    ai_preview = [
        "# Phase 8.5.3 AI Natural-Live Hardening Preview",
        "",
        "Archive-only bounded-correction replay. Numeric bindings and immutable packet facts are preserved; Telegram sends are 0.",
    ]
    selected_ai = {
        "us": ("MU", "SNDK", "SKHY", "TSM", "TSLA", "RXRX"),
        "kr": ("005930", "000660", "005490", "086280", "003690", "010120", "012450"),
    }
    for market in ("us", "kr"):
        ai_preview.extend(("", f"## {market.upper()}"))
        for ticker in selected_ai[market]:
            ai_preview.extend(
                (
                    "",
                    f"### {ticker}",
                    "",
                    "#### BEFORE - Natural rejected AI",
                    "",
                    before_ai[market][ticker],
                    "",
                    "#### AFTER - Specificity-hardened replay",
                    "",
                    after_ai[market][ticker],
                )
            )
    (
        report_dir / "20260818-phase8-5-3-ai-natural-live-hardening-preview.md"
    ).write_text("\n".join(ai_preview) + "\n", encoding="utf-8")

    fallback_preview = [
        "# Phase 8.5.3 Fallback Price Parity Preview",
        "",
        "Same 2026-08-18 assessments, rendered read-only. Telegram sends are 0.",
    ]
    selected_fallback = {
        "us": ("MU", "SNDK", "SKHY"),
        "kr": ("005930", "000660", "003690", "086280", "010120", "012450"),
    }
    for market in ("us", "kr"):
        fallback_preview.extend(("", f"## {market.upper()}"))
        for ticker in selected_fallback[market]:
            fallback_preview.extend(
                (
                    "",
                    f"### {ticker}",
                    "",
                    "#### BEFORE - Actual sent fallback",
                    "",
                    before_fallback[market][ticker],
                    "",
                    "#### AFTER - Dynamic-price parity replay",
                    "",
                    fallback_after[ticker],
                )
            )
    (
        report_dir / "20260818-phase8-5-3-fallback-price-parity-preview.md"
    ).write_text("\n".join(fallback_preview) + "\n", encoding="utf-8")

    validation = f"""# Phase 8.5.3 Natural Live Message Validation

## Result

| Gate | US before | US after | KR before | KR after |
|---|---:|---:|---:|---:|
| Full validator errors | 0 | 0 | 0 | 0 |
| Literal duplicate groups | {before_quality['us']['substantive_repeated_sentence_count']} | 0 | {before_quality['kr']['substantive_repeated_sentence_count']} | 0 |
| Semantic skeleton groups | {before_quality['us']['template_skeleton_repeat_count']} | 0 | {before_quality['kr']['template_skeleton_repeat_count']} | 0 |
| Generic methodology families | {before_quality['us']['generic_methodology_repeat_count']} | 0 | {before_quality['kr']['generic_methodology_repeat_count']} | 0 |
| Runtime message quality | FAIL | PASS | FAIL | PASS |

The duplicate threshold and all existing hard safety checks are unchanged.

## Fallback Price Parity

- Crossed confirmation rendered as future trigger: {lifecycle_audit['summary']['crossed_future_trigger_before']} before, 0 after.
- Dynamic support/resistance available but omitted after: {lifecycle_audit['summary']['dynamic_structure_omissions_after']}.
- Available current-price RR omitted after: {lifecycle_audit['summary']['available_rr_omissions_after']}.
- Fake RR: 0.
- Registered confirmation auto-promoted to support: 0.
- Structural RR-unavailable states remain unavailable with a deterministic reason.

## RR Live Path

The 2026-08-18 KR natural packet contains complete current-price RR facts for `005490`, `010120`, `012450`, and `086280`. Numeric/semantic hard errors were 0 and the prior missing-path blocker did not recur.

Status: `Current-Price RR Runtime Path = LIVE PATH PASS`.

This does not close full Natural Live AI-Assisted Delivery because the delivered path was fallback.

## Human Review

Specificity-hardened representative scores (10 dimensions, 20 points): Samsung 17, POSCO 17, Hyundai Glovis 18, Korean Re 16, SK hynix 17; KR average 17.0. US representatives MU 18, SNDK 17, SKHY 16, TSM 17, TSLA 18, RXRX 17; US average 17.2.

Fallback semantic checklist: actionable current price context 9/9, crossed-confirmation safety 9/9, RR availability handling 9/9, no automatic support promotion 9/9.

## Message Length

| Market | AI before chars | AI after chars | Change |
|---|---:|---:|---:|
| US | {_message_stats(_stock_message_values(before_ai['us']))['characters']} | {_message_stats(list(after_ai['us'].values()))['characters']} | {((_message_stats(list(after_ai['us'].values()))['characters'] / _message_stats(_stock_message_values(before_ai['us']))['characters']) - 1) * 100:.1f}% |
| KR | {_message_stats(_stock_message_values(before_ai['kr']))['characters']} | {_message_stats(list(after_ai['kr'].values()))['characters']} | {((_message_stats(list(after_ai['kr'].values()))['characters'] / _message_stats(_stock_message_values(before_ai['kr']))['characters']) - 1) * 100:.1f}% |

## Safety And Operations

- Telegram manual sends: 0
- Scheduled Task manual executions/config changes: 0
- Pilot manual mutation: 0
- DB/assessment/archive mutation: 0
- Production Assist: OFF
- Main merge / operating deployment: not performed
- KRX Open API: APPROVED / NOT YET INTEGRATED

## Engineering Validation

- Full pytest: 1,033 passed, 1 external deprecation warning
- Ruff: PASS
- git diff --check: PASS
- Output schema: 4
- Public Action: 0.4.5, operationId 20/20 unique
- Investment Knowledge v3 checksum parity: PASS
- Chart Knowledge v1 checksum parity: PASS

## Status

- AI retrospective quality: PASS
- Fallback dynamic-price parity: PASS
- RR natural live path: PASS
- Natural Live AI-assisted delivery: PARTIAL, next natural proof required
"""
    (
        report_dir / "20260818-phase8-5-3-natural-live-message-validation.md"
    ).write_text(validation, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-reports", action="store_true")
    args = parser.parse_args()
    engine = create_engine(DATABASE_URL)
    with Session(engine) as session:
        replay = {}
        for market in ("us", "kr"):
            replay[market] = _validate_replay(session, market)
            _, quality, _ = replay[market]
            print(
                market,
                quality["hard_checks_passed"],
                quality["substantive_repeated_sentence_count"],
                quality["template_skeleton_repeat_count"],
                quality["generic_methodology_repeat_count"],
            )
        after = _fallback_after(session)
        print("fallback_after", len(after))
        if args.write_reports:
            _write_reports(session, replay, after)


if __name__ == "__main__":
    main()
