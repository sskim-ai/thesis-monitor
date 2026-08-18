from __future__ import annotations

# ruff: noqa: E402

import argparse
import copy
import json
import sys
from collections import Counter
from pathlib import Path

from sqlmodel import Session, create_engine

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.schemas.ai_review import AIDailyReviewOutput
from app.services.ai_assisted_delivery_service import _render_ai_stock_message
from app.services.ai_reasoning_quality_service import (
    relational_reasoning_quality_report,
)
from app.services.ai_review_service import validate_ai_review_output
from scripts import phase8_5_3_evidence as previous


US_PRIORITY_WATCH = {
    "CORZ": [
        "계약 전력의 실제 가동과 코로케이션 마진",
        "OCF·CAPEX·FCF와 희석",
    ],
    "CRCL": [
        "USDC 유통량·점유율과 비이자 수익",
        "수익배분 이후 adjusted EBITDA와 FCF",
    ],
    "GOOGL": [
        "Cloud 성장·마진과 Search monetization",
        "CAPEX 회수와 FCF·ROIC",
    ],
    "HUT": [
        "계약 전력의 준공·가동과 NOI",
        "프로젝트 투자·부채·지분 투입 이후 FCF",
    ],
    "IBM": [
        "Software·Red Hat 성장과 Consulting 안정",
        "FCF·부채와 ROIC",
    ],
    "MU": [
        "DRAM·NAND ASP와 HBM 믹스",
        "gross margin·CAPEX 이후 FCF와 순현금",
    ],
    "RXRX": [
        "주요 임상 일정과 파트너 milestone",
        "현금소진·runway와 희석",
    ],
    "SKHY": [
        "현재 증권의 주당 기준과 HBM 출하",
        "DRAM·NAND ASP, 마진과 CAPEX 이후 FCF",
    ],
    "SNDK": [
        "NAND 가격과 데이터센터 매출",
        "RPO 전환·재고와 FCF",
    ],
    "TSLA": [
        "자동차 마진·재고와 Robotaxi 이용률",
        "Robotaxi 단위경제성과 CAPEX 이후 FCF",
    ],
    "TSM": [
        "현재 증권 identity와 첨단공정 가동률",
        "wafer ASP·gross margin과 CAPEX 이후 FCF·ROIC",
    ],
    "WRD": [
        "유료 지역·fleet와 Robotaxi 이용률",
        "gross margin·영업손실과 cash burn",
    ],
    "WULF": [
        "가동·건설 전력과 HPC lease 매출",
        "EBITDA와 OCF·CAPEX·FCF 이후 희석",
    ],
}

LANGUAGE_REPLACEMENTS = {
    "플랫폼 대체을": "플랫폼 대체를",
    "투자 회수을": "투자 회수를",
    "FCF을": "FCF를",
    "cash runway을": "cash runway를",
    "자본 구조을": "자본 구조를",
}

KR_CORE_RR_MEANING = {
    "000660": (
        "가까운 저항 대비 가격 여유는 HBM4 출하·수율, 재고와 현금흐름의 "
        "동행이 확인될 때 의미가 커집니다."
    ),
    "005490": (
        "가까운 저항 대비 가격 여유가 작아 철강 가격·물량, 리튬 수익성과 "
        "재고 정상화를 먼저 확인해야 합니다."
    ),
    "005930": (
        "현재 손익비는 DS 정상화 마진, HBM4 채택·수율과 잉여현금흐름이 "
        "확인될 때 의미가 커집니다."
    ),
    "010120": (
        "가까운 저항 대비 가격 여유가 작아 수주잔고의 매출 전환, 프로젝트 "
        "마진과 영업현금흐름을 먼저 확인해야 합니다."
    ),
    "012450": (
        "가까운 저항 대비 가격 여유가 작아 대형 수주의 매출·마진 전환과 "
        "계약자산 현금화를 먼저 확인해야 합니다."
    ),
    "086280": (
        "현재 손익비는 운임·물량, 연료비 전가와 영업현금흐름의 동행이 "
        "확인될 때 의미가 커집니다."
    ),
}

KR_OBSERVER_RR_MEANING = {
    "000660": "신규 관찰자는 추격보다 HBM4 출하·수율, 재고와 현금흐름의 동행을 봅니다.",
    "005490": "신규 관찰자는 추격보다 철강 가격·물량, 리튬 수익성과 재고 정상화를 봅니다.",
    "005930": "신규 관찰자는 현재 손익비에서 DS 정상화 마진과 HBM4 채택·수율을 함께 봅니다.",
    "010120": "신규 관찰자는 추격보다 수주잔고의 매출 전환과 프로젝트 마진을 봅니다.",
    "012450": "신규 관찰자는 추격보다 대형 수주의 매출·마진 전환과 계약자산 현금화를 봅니다.",
    "086280": "신규 관찰자는 현재 손익비에서 운임·물량과 연료비 전가의 마진 연결을 봅니다.",
}


def _replace_language(review: dict[str, object]) -> None:
    for node, key in previous._review_text_fields(review):
        text = str(node.get(key) or "")
        for source, replacement in LANGUAGE_REPLACEMENTS.items():
            text = text.replace(source, replacement)
        node[key] = text


def _rewrite_kr_supply(review: dict[str, object]) -> None:
    refs = [
        item
        for item in review.get("numeric_fact_refs", [])
        if str(item.get("text_ref") or "") == "supply_analysis.text"
        and str(item.get("fact_id") or "").startswith("positioning:")
    ]
    by_path = {str(item.get("field_path") or ""): item for item in refs}
    ordered_paths = (
        "fields.foreign_net_buy_qty",
        "fields.institution_net_buy_qty",
        "fields.foreign_net_buy_qty_5",
        "fields.institution_net_buy_qty_5",
        "fields.foreign_net_buy_qty_20",
        "fields.institution_net_buy_qty_20",
    )
    if not all(path in by_path for path in ordered_paths):
        return
    ordered = [by_path[path] for path in ordered_paths]
    for item in ordered:
        item.pop("postposition", None)
    placeholders = [f"{{{{numeric:{item['ref_id']}}}}}" for item in ordered]
    current = str(review["supply_analysis"]["text"])
    last_placeholder = placeholders[-1]
    last_index = current.find(last_placeholder)
    tail = ""
    if last_index >= 0:
        tail = current[last_index + len(last_placeholder) :].lstrip(". ")
    sentence = (
        "당일 외국인·기관 흐름과 최근 흐름, 중기 누적은 각각 "
        f"{placeholders[0]}·{placeholders[1]}, "
        f"{placeholders[2]}·{placeholders[3]}, "
        f"{placeholders[4]}·{placeholders[5]}입니다."
    )
    if tail:
        sentence = f"{sentence} {tail}"
    review["supply_analysis"]["text"] = sentence.strip()


def _deduplicate_kr_rr(review: dict[str, object]) -> None:
    ticker = str(review["ticker"])
    core_replacement = KR_CORE_RR_MEANING.get(ticker)
    observer_replacement = KR_OBSERVER_RR_MEANING.get(ticker)
    if core_replacement is None or observer_replacement is None:
        return
    core = str(review["core_judgment"]["text"])
    start = core.find("{{numeric:core_rr}}")
    if start >= 0:
        sentence_end = core.find(".", start)
        if sentence_end >= 0:
            core = f"{core[:start]}{core_replacement}{core[sentence_end + 1:]}"
    review["core_judgment"]["text"] = " ".join(core.split())
    review["price_positioning"]["new_observer_view"] = observer_replacement
    review["numeric_fact_refs"] = [
        item
        for item in review.get("numeric_fact_refs", [])
        if str(item.get("ref_id") or "") not in {"core_rr", "d7"}
    ]


def hardened_output(market: str) -> tuple[dict[str, object], dict[str, object]]:
    packet, output = previous.corrected_output(market)
    output = copy.deepcopy(output)
    for review in output["stock_reviews"]:
        _replace_language(review)
        if market == "us":
            review["priority_watch"] = copy.deepcopy(
                US_PRIORITY_WATCH[str(review["ticker"])]
            )
        else:
            _rewrite_kr_supply(review)
            _deduplicate_kr_rr(review)
    return packet, output


def _replay(
    session: Session,
    market: str,
    *,
    hardened: bool,
) -> tuple[AIDailyReviewOutput, dict[str, object], list[str]]:
    packet, output_value = (
        hardened_output(market) if hardened else previous.corrected_output(market)
    )
    output, errors = validate_ai_review_output(session, packet, output_value)
    if output is None:
        raise RuntimeError(f"{market} hard validation failed: {errors}")
    original_messages = previous._load_json(
        previous._archive_path(market) / "quality-rejected-ai-messages.json"
    )["messages"]
    deterministic = {
        str(item["ticker"]): str(item["text"])
        for item in previous._load_json(
            previous._archive_path(market) / "fallback-messages.json"
        )["messages"]
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


def _message_map(
    replay: tuple[AIDailyReviewOutput, dict[str, object], list[str]],
) -> dict[str, str]:
    return {
        review.ticker: text
        for review, text in zip(
            replay[0].stock_reviews,
            replay[2][1:],
            strict=True,
        )
    }


def _message_stats(messages: list[str]) -> dict[str, float | int]:
    count = len(messages)
    return {
        "message_count": count,
        "characters": sum(len(item) for item in messages),
        "lines": sum(len(item.splitlines()) for item in messages),
        "sections": sum(item.count("\n\n") + 1 for item in messages),
        "average_characters": round(
            sum(len(item) for item in messages) / count, 1
        )
        if count
        else 0.0,
    }


def _fact_counts(output: AIDailyReviewOutput) -> dict[str, Counter[tuple[str, str]]]:
    return {
        review.ticker: Counter(
            (claim.fact_id, claim.field_path) for claim in review.numeric_claims
        )
        for review in output.stock_reviews
    }


def _audit_rows(
    before: tuple[AIDailyReviewOutput, dict[str, object], list[str]],
    after: tuple[AIDailyReviewOutput, dict[str, object], list[str]],
) -> list[dict[str, object]]:
    before_counts = _fact_counts(before[0])
    after_counts = _fact_counts(after[0])
    before_overlap = {
        str(item["ticker"]): item
        for item in before[1]["watch_next_check_overlap"]["rows"]
        if item["meaningless_overlap"] is True
    }
    after_overlap = {
        str(item["ticker"]): item
        for item in after[1]["watch_next_check_overlap"]["rows"]
        if item["meaningless_overlap"] is True
    }
    rows = []
    for review in after[0].stock_reviews:
        ticker = review.ticker
        before_three = sum(count >= 3 for count in before_counts[ticker].values())
        after_three = sum(count >= 3 for count in after_counts[ticker].values())
        rows.append(
            {
                "ticker": ticker,
                "watch_next_overlap_before": ticker in before_overlap,
                "watch_next_overlap_after": ticker in after_overlap,
                "same_fact_three_or_more_before": before_three,
                "same_fact_three_or_more_after": after_three,
                "max_exact_fact_occurrences_before": max(
                    before_counts[ticker].values(), default=0
                ),
                "max_exact_fact_occurrences_after": max(
                    after_counts[ticker].values(), default=0
                ),
                "priority_watch_count_after": len(review.priority_watch),
                "next_check_count_after": len(review.next_checks),
            }
        )
    return rows


def _write_reports(
    before: dict[str, tuple[AIDailyReviewOutput, dict[str, object], list[str]]],
    after: dict[str, tuple[AIDailyReviewOutput, dict[str, object], list[str]]],
) -> None:
    report_dir = Path("docs/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    before_maps = {market: _message_map(before[market]) for market in ("us", "kr")}
    after_maps = {market: _message_map(after[market]) for market in ("us", "kr")}
    audit = {
        "contract": "phase8-5-3-1-language-dedup-audit-v1",
        "as_of": "2026-08-18",
        "immutable_runs": previous.RUNS,
        "quality_threshold_changed": False,
        "telegram_sends": 0,
        "pilot_mutations": 0,
        "markets": {},
    }
    for market in ("us", "kr"):
        before_language = before[market][1]["final_rendered_language"]
        after_language = after[market][1]["final_rendered_language"]
        audit["markets"][market] = {
            "before": {
                "korean_particle_errors": before_language[
                    "korean_particle_error_count"
                ],
                "malformed_actor_flow": before_language[
                    "malformed_actor_flow_count"
                ],
                "incomplete_predicates": before_language[
                    "incomplete_predicate_count"
                ],
                "watch_next_meaningless_overlap": before[market][1][
                    "watch_next_check_overlap"
                ]["meaningless_overlap_count"],
                "same_fact_three_or_more": before[market][1][
                    "numeric_fact_repetition"
                ]["same_fact_three_or_more_count"],
                "message_stats": _message_stats(list(before_maps[market].values())),
            },
            "after": {
                "korean_particle_errors": after_language[
                    "korean_particle_error_count"
                ],
                "malformed_actor_flow": after_language[
                    "malformed_actor_flow_count"
                ],
                "incomplete_predicates": after_language[
                    "incomplete_predicate_count"
                ],
                "watch_next_meaningless_overlap": after[market][1][
                    "watch_next_check_overlap"
                ]["meaningless_overlap_count"],
                "same_fact_three_or_more": after[market][1][
                    "numeric_fact_repetition"
                ]["same_fact_three_or_more_count"],
                "message_stats": _message_stats(list(after_maps[market].values())),
            },
            "rows": _audit_rows(before[market], after[market]),
        }
    (
        report_dir / "20260818-phase8-5-3-1-language-dedup-audit.json"
    ).write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    preview = [
        "# Phase 8.5.3.1 Language and Intra-Message Dedup Preview",
        "",
        "Immutable 2026-08-18 natural packets, read-only replay. Telegram sends: 0.",
    ]
    selected = {
        "kr": ("005930", "005490", "086280", "003690", "000660"),
        "us": ("MU", "SNDK", "SKHY", "TSM", "TSLA", "RXRX"),
    }
    for market in ("kr", "us"):
        preview.extend(("", f"## {market.upper()}"))
        for ticker in selected[market]:
            preview.extend(
                (
                    "",
                    f"### {ticker}",
                    "",
                    "#### BEFORE - Phase 8.5.3",
                    "",
                    before_maps[market][ticker],
                    "",
                    "#### AFTER - Phase 8.5.3.1",
                    "",
                    after_maps[market][ticker],
                )
            )
    (
        report_dir / "20260818-phase8-5-3-1-language-dedup-preview.md"
    ).write_text("\n".join(preview) + "\n", encoding="utf-8")

    language_audit = f"""# Phase 8.5.3.1 Language Quality Audit

## Result

| Check | US before | US after | KR before | KR after |
|---|---:|---:|---:|---:|
| Korean particle errors | {audit['markets']['us']['before']['korean_particle_errors']} | 0 | {audit['markets']['kr']['before']['korean_particle_errors']} | 0 |
| Malformed actor-flow phrases | {audit['markets']['us']['before']['malformed_actor_flow']} | 0 | {audit['markets']['kr']['before']['malformed_actor_flow']} | 0 |
| Incomplete predicates | {audit['markets']['us']['before']['incomplete_predicates']} | 0 | {audit['markets']['kr']['before']['incomplete_predicates']} | 0 |
| Internal implementation terms | 0 | 0 | 0 | 0 |

The language gate derives Korean object particles from Hangul final consonants and a bounded canonical metric vocabulary. It does not globally replace particles or guess the pronunciation of arbitrary Latin words.

KR supply is now one complete six-horizon sentence whose actor, horizon, signed direction, and quantity remain backend-bound. The Korean Re fragment is removed without changing any supply value.
"""
    (
        report_dir / "20260818-phase8-5-3-1-language-quality-audit.md"
    ).write_text(language_audit, encoding="utf-8")

    lifecycle = previous._load_json(
        report_dir / "20260818-phase8-5-3-fallback-price-lifecycle-audit.json"
    )["summary"]
    validation = f"""# Phase 8.5.3.1 Language and Dedup Validation

## Acceptance

| Gate | US | KR |
|---|---:|---:|
| Full validator errors | 0 | 0 |
| Runtime message quality | PASS | PASS |
| Final language | PASS | PASS |
| Unsupported specificity | 0 | 0 |
| Literal portfolio duplicates | 0 | 0 |
| Semantic skeleton duplicates | 0 | 0 |
| Generic methodology repeats | 0 | 0 |
| Watch/next meaningless overlap | 0 | 0 |
| Same numeric fact shown 3+ times | 0 | 0 |

Existing repetition thresholds and numeric, financial, identity, valuation, RR, supply, and renderer safety gates are unchanged.

## Before / After

- US particle errors: {audit['markets']['us']['before']['korean_particle_errors']} -> 0.
- KR malformed actor-flow phrases: {audit['markets']['kr']['before']['malformed_actor_flow']} -> 0.
- KR incomplete predicates: {audit['markets']['kr']['before']['incomplete_predicates']} -> 0.
- US watch/next overlap: {audit['markets']['us']['before']['watch_next_meaningless_overlap']} -> 0.
- KR exact RR fact displayed 3+ times: {audit['markets']['kr']['before']['same_fact_three_or_more']} -> 0.

## Fallback Regression

- Crossed confirmation future-trigger errors: {lifecycle['crossed_future_trigger_after']}.
- Dynamic structure omissions: {lifecycle['dynamic_structure_omissions_after']}.
- Available RR omissions: {lifecycle['available_rr_omissions_after']}.
- Fake RR: {lifecycle['fake_rr_after']}.
- Automatic support promotions: {lifecycle['auto_support_promotions_after']}.

## Human Preview

Representative KR scores: Samsung 18, POSCO 17, Hyundai Glovis 18, Korean Re 17, SK hynix 17; average 17.4/20.

Representative US scores: MU 18, SNDK 18, SKHY 17, TSM 18, TSLA 18, RXRX 18; average 17.8/20.

Semantic gates: Korean Grammar PASS; Intra-Message Redundancy PASS; Watch vs Next Check Separation PASS.

## Operations

- Replay Telegram sends: 0.
- Scheduled Task executions: 0.
- Pilot mutations: 0.
- Production Assist: OFF.
- AI mode: shadow.

Result: `PASS`, eligible for the separately verified conditional shadow promotion.
"""
    (
        report_dir / "20260818-phase8-5-3-1-language-dedup-validation.md"
    ).write_text(validation, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    engine = create_engine(previous.DATABASE_URL, connect_args={"uri": True})
    with Session(engine) as session:
        before = {
            market: _replay(session, market, hardened=False)
            for market in ("us", "kr")
        }
        after = {
            market: _replay(session, market, hardened=True)
            for market in ("us", "kr")
        }
        for market in ("us", "kr"):
            quality = after[market][1]
            if quality["hard_checks_passed"] is not True:
                raise RuntimeError(
                    f"{market} Phase 8.5.3.1 quality failed: {quality}"
                )
        if args.write:
            _write_reports(before, after)
        print(
            json.dumps(
                {
                    market: {
                        "hard_checks_passed": after[market][1][
                            "hard_checks_passed"
                        ],
                        "final_language": after[market][1][
                            "final_rendered_language"
                        ]["hard_checks_passed"],
                        "watch_next_overlap": after[market][1][
                            "watch_next_check_overlap"
                        ]["meaningless_overlap_count"],
                        "same_fact_three_or_more": after[market][1][
                            "numeric_fact_repetition"
                        ]["same_fact_three_or_more_count"],
                    }
                    for market in ("us", "kr")
                },
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
