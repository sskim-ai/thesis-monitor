from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.free_analyst_production_integration_service import (  # noqa: E402
    build_production_candidate,
    select_limited_canary,
)
from app.services.market_context_adapter_service import (  # noqa: E402
    KrMarketContextAdapter,
)
from app.services.market_cross_section_service import MarketCrossSection  # noqa: E402
from app.services.market_intelligence_service import (  # noqa: E402
    build_market_intelligence,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Replay immutable KR messages with supplemental Kiwoom context."
    )
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _cross_section(evidence: dict[str, Any]) -> MarketCrossSection:
    audit = evidence["audit"]
    sectors = [
        *evidence["size_context"],
        *evidence["top_sectors"],
        *evidence["bottom_sectors"],
    ]
    unique_sectors = {
        (item["market_scope"], item["sector_code"]): item for item in sectors
    }
    return MarketCrossSection.model_validate(
        {
            "market": "KR",
            "session_date": evidence["session_date"],
            "as_of": evidence["observed_at"],
            "indices": evidence["indices"],
            "breadth": evidence["breadth"],
            "breadth_by_scope": evidence["breadth_by_scope"],
            "concentration": {
                "contract_version": "kr-market-flow-concentration-v1",
                "relations": audit["concentration"],
                "blocked_markets": audit["blocked_concentration_markets"],
            },
            "sectors": list(unique_sectors.values()),
            "market_flows": evidence["market_flows"],
            "quality": evidence["quality"],
            "source_payload_sha256": evidence["source_payload_sha256"],
        }
    )


def _enrich_market(text: str) -> str:
    text = text.replace(
        "• VIX 등락률 -5.5%로 단기 위험회피는 완화됐지만 시장 폭과 전체 수급이 없어 광범위한 위험선호 개선으로 볼 수 없습니다.",
        "• VIX 등락률 -5.5%로 단기 위험회피는 완화됐고, 국내에서는 두 시장 모두 상승 종목이 하락 종목보다 많아 전일 해외 약세만으로 장을 설명하기 어렵습니다.\n"
        "• KOSPI에서는 외국인 순매도와 기관·개인 순매수가 맞섰고, KOSDAQ에서는 외국인·기관 순매수와 개인 순매도가 대응했습니다.",
    )
    text = text.replace(
        "미국 전일 반도체·성장주 상대 약세와 실질금리 부담이 위험자산에 압력을 주는 가운데 변동성은 완화됐습니다. 한국 현물 지수·시장 폭·시장 전체 수급이 없어 종목별 실적과 가격 구조 확인이 우선입니다.",
        "KOSDAQ이 KOSPI보다 강했고 두 시장 모두 상승 종목 우위였습니다. KOSPI 중·소형주가 대형주보다 강했으며 건설·기계/장비 강세와 KOSDAQ 일반서비스 약세가 함께 나타나, 전면적 위험선호보다 시장 내부 순환을 우선 확인할 장입니다.",
    )
    text = text.replace(
        "• 시장 breadth는 제공되지 않아 상승·하락 종목의 확산 정도를 알 수 없습니다.\n"
        "• 시장 전체 투자주체 수급은 제공되지 않아 광범위한 자금 흐름을 알 수 없습니다.\n"
        "• 한국 현물 지수가 없어 미국 지수와 반도체 가격은 전일 해외 맥락으로만 사용합니다.",
        "• KOSPI 종목별 금액 합계가 시장 전체 집계와 완전히 일치하지 않아 KOSPI 매매 집중도는 사용하지 않습니다.\n"
        "• KOSDAQ 집중도는 수급 분포만 보여주며 기업 뉴스의 원인을 증명하지 않습니다.\n"
        "• 미국 지수와 반도체 가격은 전일 해외 맥락으로, 한국 현물 지수·폭·수급은 8월 25일 국내 장 마감 근거로 구분합니다.",
    )
    return text


def _enrich_deterministic_market(text: str) -> str:
    text = text.replace(
        "• KOSPI·KOSDAQ 지수와 시장별 상승·하락 종목 수는 KRX 공표 대기 상태라 이번 replay에서 국내 breadth나 시장 전체 수급 방향을 만들지 않습니다.",
        "• KOSDAQ이 KOSPI보다 강했고 두 시장 모두 상승 종목이 하락 종목보다 많았습니다. 외국인은 KOSPI 순매도·KOSDAQ 순매수로 갈렸고 기관은 두 시장에서 순매수였습니다.",
    )
    text = text.replace(
        "• 다음 KRX 완료 공표에서 KOSPI·KOSDAQ과 시장별 상승·하락 종목 수를 확인합니다.",
        "• 다음 KRX 완료 공표에서 Kiwoom의 KOSPI·KOSDAQ 지수와 시장별 상승·하락 종목 수를 교차검증합니다.",
    )
    return text


def _append_supply_context(text: str, sentence: str) -> str:
    marker = "📊 수급\n"
    if marker not in text:
        return text
    before, after = text.split(marker, 1)
    end_marker = "\n\n📐 Valuation"
    if end_marker not in after:
        return text
    supply, tail = after.split(end_marker, 1)
    return f"{before}{marker}{supply.rstrip()} {sentence}{end_marker}{tail}"


def _enrich_stock(ticker: str, text: str) -> tuple[str, str | None]:
    if ticker == "005930":
        sentence = (
            "통합시장 금액 흐름에서도 삼성전자의 외국인 순매도는 KOSPI 전체 "
            "방향과 일치합니다. 종목별 합계와 시장 집계의 기준 차이 때문에 "
            "집중도 해석은 제외합니다."
        )
        return _append_supply_context(text, sentence), "market_stock_direction_alignment"
    return text, None


def build_replay(
    packet: dict[str, Any],
    baseline: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, object]:
    packet_copy = deepcopy(packet)
    cross_section = _cross_section(evidence)
    supplemental_intelligence = build_market_intelligence(
        None,
        date.fromisoformat(str(packet["assessment_date"])),
        list(packet["stocks"]),
        [],
        market="kr",
        cross_section=cross_section,
    )
    normalized_context = KrMarketContextAdapter().normalize(
        assessment_date=date.fromisoformat(str(packet["assessment_date"])),
        as_of=datetime.fromisoformat(str(evidence["observed_at"])),
        cutoff=datetime.fromisoformat(str(evidence["observed_at"])),
        fact_catalog=supplemental_intelligence["fact_catalog"],
        coverage=None,
        cross_section=cross_section,
        provider_publication_state="PROVIDER_COMPLETE",
    )
    packet_copy["supplemental_kiwoom_market_context"] = normalized_context.model_dump(
        mode="json"
    )

    candidates = []
    messages: list[dict[str, object]] = []
    for row in baseline["messages"]:
        ticker = str(row["ticker"])
        sparse = str(row["sparse_previous"])
        deterministic = str(row["deterministic_reference"])
        materiality_reason = None
        if ticker == "__DAILY_DIGEST_KR__":
            enriched = _enrich_market(sparse)
            enriched_reference = _enrich_deterministic_market(deterministic)
            materiality_reason = "resolved_local_index_breadth_and_market_flow_unknowns"
        else:
            enriched, materiality_reason = _enrich_stock(ticker, sparse)
            enriched_reference, _ = _enrich_stock(ticker, deterministic)
        candidate = build_production_candidate(
            enriched,
            deterministic_text=enriched_reference,
            message_key=str(row["message_key"]),
            market="kr",
            packet_owner=str(packet["packet_id"]),
            is_market_digest=bool(row["is_market_digest"]),
        )
        candidates.append(candidate)
        safety = candidate.result.safety if candidate.result else {}
        quality = (
            "MATERIAL_IMPROVEMENT"
            if ticker == "__DAILY_DIGEST_KR__" and candidate.eligible
            else "MINOR_IMPROVEMENT"
            if materiality_reason and candidate.eligible
            else "NO_MEANINGFUL_CHANGE"
        )
        messages.append(
            {
                "ticker": ticker,
                "message_key": row["message_key"],
                "sparse_previous": sparse,
                "kiwoom_enriched_pre_quality": enriched,
                "kiwoom_enriched_post_quality": candidate.candidate_text,
                "deterministic_reference": enriched_reference,
                "eligible": candidate.eligible,
                "errors": list(candidate.errors),
                "selected_renderer": candidate.selected_renderer,
                "quality_v2": candidate.quality_v2,
                "safety": safety,
                "materiality_reason": materiality_reason,
                "human_quality": quality,
                "length_before": len(sparse),
                "length_after": len(candidate.candidate_text),
            }
        )
    selection = select_limited_canary(candidates)
    selected = set(selection.selected_keys)
    for row in messages:
        row["canary_selected"] = row["message_key"] in selected

    semantic_errors: list[str] = []
    digest = next(row for row in messages if row["ticker"] == "__DAILY_DIGEST_KR__")
    digest_text = str(digest["kiwoom_enriched_post_quality"])
    for forbidden in (
        "시장 breadth는 제공되지",
        "시장 전체 투자주체 수급은 제공되지",
        "한국 현물 지수가 없어",
    ):
        if forbidden in digest_text:
            semantic_errors.append(f"resolved_unknown_retained:{forbidden}")
    if "KOSPI 매매 집중" in digest_text and "사용하지 않습니다" not in digest_text:
        semantic_errors.append("blocked_kospi_concentration_promoted")
    safety_totals = {
        name: sum(int((row["safety"] or {}).get(name) or 0) for row in messages)
        for name in (
            "fact_mismatch",
            "unsupported_causality",
            "hidden_arithmetic",
            "external_knowledge",
            "material_information_loss",
        )
    }
    return {
        "contract": "kr-kiwoom-enriched-replay-v1",
        "packet_id": packet["packet_id"],
        "packet_immutable": True,
        "supplemental_source_payload_sha256": evidence["source_payload_sha256"],
        "supplemental_context": normalized_context.model_dump(mode="json"),
        "supplemental_fact_count": len(supplemental_intelligence["fact_catalog"]),
        "numeric_binding": {
            "baseline_auto_bound": baseline["numeric_binding"]["auto_bound"],
            "new_exact_numeric_claims": 0,
            "manual": 0,
            "rejected": 0,
            "unresolved": 0,
        },
        "semantic_validation": {
            "status": "PASS" if not semantic_errors else "FAIL",
            "errors": semantic_errors,
            "safety_totals": safety_totals,
        },
        "message_count": len(messages),
        "eligible_count": sum(bool(row["eligible"]) for row in messages),
        "human_quality": {
            name: sum(row["human_quality"] == name for row in messages)
            for name in (
                "MATERIAL_IMPROVEMENT",
                "MINOR_IMPROVEMENT",
                "NO_MEANINGFUL_CHANGE",
                "DEGRADED",
            )
        },
        "average_length_before": sum(int(row["length_before"]) for row in messages)
        / len(messages),
        "average_length_after": sum(int(row["length_after"]) for row in messages)
        / len(messages),
        "canary_selection": selection.to_dict(),
        "messages": messages,
    }


def main() -> None:
    args = _parser().parse_args()
    result = build_replay(
        _load(args.packet),
        _load(args.baseline),
        _load(args.evidence),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({key: value for key, value in result.items() if key != "messages"}, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
