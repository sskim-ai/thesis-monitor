from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.schemas.ai_review import AIDailyReviewOutput
from app.services.ai_assisted_delivery_service import (
    _render_ai_market_message,
    _render_ai_stock_message,
)
from app.services.free_analyst_production_integration_service import (
    build_production_candidate,
    select_limited_canary,
)
from app.services.free_analyst_message_service import message_quality_v2_report
from app.services.numeric_provenance_service import bind_numeric_fact_references
from app.services.runtime_reasoning_ownership_service import (
    apply_candidate_ownership_contracts,
)
from app.services.working_capital_user_visible_preintegration_service import (
    ensure_relation_semantics,
    normalize_directional_numeric_refs,
)


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def _return_pct(previous: float, current: float) -> float:
    if previous <= 0 or current <= 0:
        raise ValueError("structured market prices must be positive")
    return (current / previous - 1.0) * 100.0


def _validated_output(
    packet: dict[str, object],
    output: dict[str, object],
) -> tuple[AIDailyReviewOutput, dict[str, object]]:
    """Run the production numeric normalization and binding sequence."""
    directional, relation_report = normalize_directional_numeric_refs(packet, output)
    normalized, ownership_report = apply_candidate_ownership_contracts(
        packet,
        directional,
    )
    binding = bind_numeric_fact_references(packet, normalized)
    if binding.errors:
        raise ValueError(f"numeric binding failed: {binding.errors}")
    report = dict(binding.report)
    report["candidate_ownership"] = ownership_report
    report["working_capital_relation_semantics"] = relation_report
    return AIDailyReviewOutput.model_validate(binding.output), report


def _us_summary(
    packet: dict[str, object],
    supplemental: dict[str, object],
) -> tuple[str, dict[str, object]]:
    bars = supplemental.get("us_etf_bars")
    if not isinstance(bars, dict):
        raise ValueError("US supplemental ETF bars are missing")
    returns: dict[str, float] = {}
    for symbol, rows in bars.items():
        if not isinstance(rows, list) or len(rows) != 2:
            raise ValueError(f"US supplemental bar pair is invalid: {symbol}")
        if any(not isinstance(row, dict) for row in rows):
            raise ValueError(f"US supplemental bar row is invalid: {symbol}")
        dates = [str(row.get("date") or "") for row in rows]
        if dates != ["2026-08-21", "2026-08-24"]:
            raise ValueError(f"US supplemental session mismatch: {symbol}")
        returns[str(symbol)] = _return_pct(
            float(rows[0]["close"]),
            float(rows[1]["close"]),
        )

    market_context = packet.get("market_context")
    facts = market_context.get("fact_catalog") if isinstance(market_context, dict) else None
    spy_fact = next(
        (
            fact
            for fact in facts or []
            if isinstance(fact, dict) and fact.get("fact_id") == "market:index:SPY"
        ),
        None,
    )
    fields = spy_fact.get("fields") if isinstance(spy_fact, dict) else None
    spy_return = fields.get("return_pct") if isinstance(fields, dict) else None
    if not isinstance(spy_return, (int, float)):
        raise ValueError("US packet SPY return is unavailable")
    rsp_gap = returns["RSP"] - float(spy_return)
    sectors = {symbol: value for symbol, value in returns.items() if symbol != "RSP"}
    strongest = sorted(sectors, key=lambda symbol: (-sectors[symbol], symbol))[:2]
    weakest = sorted(sectors, key=lambda symbol: (sectors[symbol], symbol))[:2]
    summary = (
        "동일가중 S&P500이 시가총액가중 SPY를 웃돌았고, "
        f"섹터는 {'·'.join(strongest)}가 상대적으로 강한 반면 "
        f"{'·'.join(weakest)}는 약해 지수 움직임의 폭과 집중을 구분합니다."
    )
    return summary, {
        "target_session": "2026-08-24",
        "rsp_return_pct": returns["RSP"],
        "spy_return_pct": float(spy_return),
        "equal_weight_minus_cap_weight_pct_point": rsp_gap,
        "sector_returns_pct": sectors,
        "strongest_sectors": strongest,
        "weakest_sectors": weakest,
        "breadth": "UNAVAILABLE",
        "participant_flow": "UNAVAILABLE_NOT_SUPPORTED",
    }


def _kr_summary(supplemental: dict[str, object]) -> tuple[str, dict[str, object]]:
    readiness = supplemental.get("kr_target_session_readiness")
    if not isinstance(readiness, dict):
        raise ValueError("KR target-session readiness is missing")
    if readiness.get("status") != "MARKET_COMPLETED_PROVIDER_PENDING":
        raise ValueError("KR target session must remain publication-pending in this replay")
    return (
        "KOSPI·KOSDAQ 지수와 시장별 상승·하락 종목 수는 KRX 공표 대기 상태라 "
        "이번 replay에서 국내 breadth나 시장 전체 수급 방향을 만들지 않습니다.",
        {
            "target_session": "2026-08-25",
            "indices": "PUBLICATION_PENDING",
            "breadth": "PUBLICATION_PENDING",
            "market_flows": "UNAVAILABLE",
            "next_check": (
                "다음 KRX 완료 공표에서 KOSPI·KOSDAQ과 시장별 상승·하락 "
                "종목 수를 확인합니다."
            ),
        },
    )


def _enrich_market_reference(text: str, summary: str) -> str:
    marker = "📈 중요한 변화\n"
    if marker in text:
        return text.replace(marker, f"{marker}• {summary}\n", 1)
    return f"{text.rstrip()}\n\n🧭 구조화 시장 맥락\n{summary}"


def _replace_first_next_check(text: str, replacement: str) -> str:
    marker = "📌 다음 확인\n"
    if marker not in text:
        return f"{text.rstrip()}\n\n{marker}• {replacement}"
    before, after = text.split(marker, 1)
    lines = after.splitlines()
    if lines and lines[0].startswith("• "):
        lines[0] = f"• {replacement}"
    else:
        lines.insert(0, f"• {replacement}")
    return f"{before}{marker}" + "\n".join(lines)


def build_replay(
    *,
    packet: dict[str, object],
    output: dict[str, object],
    deterministic: dict[str, object],
    supplemental: dict[str, object],
) -> dict[str, object]:
    packet = ensure_relation_semantics(packet)
    market = str(packet.get("market") or "").lower()
    if market not in {"kr", "us"}:
        raise ValueError("packet market must be KR or US")
    packet_id = str(packet.get("packet_id") or "")
    ai_output, numeric_binding = _validated_output(packet, output)
    deterministic_rows = deterministic.get("messages")
    if not isinstance(deterministic_rows, list):
        raise ValueError("deterministic messages are missing")
    market_context = packet.get("market_context")
    if not isinstance(market_context, dict):
        raise ValueError("packet market context is missing")
    reviews = {item.ticker: item for item in ai_output.stock_reviews}
    if market == "us":
        structured_summary, structured_context = _us_summary(packet, supplemental)
    else:
        structured_summary, structured_context = _kr_summary(supplemental)

    candidates = []
    rows: list[dict[str, object]] = []
    for row in deterministic_rows:
        if not isinstance(row, dict) or not isinstance(row.get("payload"), dict):
            continue
        ticker = str(row.get("ticker") or "")
        deterministic_text = str(row["payload"].get("text") or "")
        is_market = ticker.startswith("__DAILY_DIGEST")
        if is_market:
            sparse_text = _render_ai_market_message(
                deterministic_text,
                ai_output.market_review,
                market_context=market_context,
                market=market,
                pilot_day=1,
                target_days=1,
            )
            enriched_pre_quality = (
                f"{sparse_text.rstrip()}\n\n🧭 구조화 시장 맥락\n{structured_summary}"
            )
            enriched_reference = _enrich_market_reference(
                deterministic_text,
                structured_summary,
            )
            next_check = structured_context.get("next_check")
            if isinstance(next_check, str) and next_check:
                enriched_pre_quality = _replace_first_next_check(
                    enriched_pre_quality,
                    next_check,
                )
                enriched_reference = _replace_first_next_check(
                    enriched_reference,
                    next_check,
                )
            message_key = f"market:{packet_id}"
        else:
            review = reviews.get(ticker)
            if review is None:
                raise ValueError(f"AI stock review is missing: {ticker}")
            sparse_text = _render_ai_stock_message(
                deterministic_text,
                review,
                market=market,
                pilot_day=1,
                target_days=1,
            )
            enriched_pre_quality = sparse_text
            enriched_reference = deterministic_text
            message_key = f"stock:{ticker}"
        candidate = build_production_candidate(
            enriched_pre_quality,
            deterministic_text=enriched_reference,
            message_key=message_key,
            market=market,
            packet_owner=packet_id,
            is_market_digest=is_market,
        )
        candidates.append(candidate)
        sparse_quality = message_quality_v2_report(
            sparse_text,
            deterministic_reference=enriched_reference,
        )
        enriched_pre_quality_report = message_quality_v2_report(
            enriched_pre_quality,
            deterministic_reference=enriched_reference,
        )
        rows.append(
            {
                "ticker": ticker,
                "message_key": message_key,
                "is_market_digest": is_market,
                "sparse_previous": sparse_text,
                "enriched_pre_quality": enriched_pre_quality,
                "enriched_post_quality_v2": candidate.candidate_text,
                "deterministic_reference": enriched_reference,
                "adaptive_selected": candidate.candidate_text,
                "eligible": candidate.eligible,
                "errors": list(candidate.errors),
                "selected_renderer": candidate.selected_renderer,
                "sparse_quality_v2": sparse_quality,
                "enriched_pre_quality_v2": enriched_pre_quality_report,
                "quality_v2": candidate.quality_v2,
                "safety": candidate.result.safety if candidate.result else None,
            }
        )
    selection = select_limited_canary(candidates)
    return {
        "contract": "structured-data-quality-v2-replay-v1",
        "packet_id": packet_id,
        "market": market,
        "evidence_class": "SUPPLEMENTAL_STRUCTURED_EVIDENCE",
        "structured_summary": structured_summary,
        "structured_context": structured_context,
        "numeric_binding": numeric_binding,
        "message_count": len(rows),
        "eligible_count": sum(bool(row["eligible"]) for row in rows),
        "generic_synthesis_lines_before": sum(
            len((row.get("sparse_quality_v2") or {}).get("generic_synthesis_lines", []))
            for row in rows
        ),
        "generic_synthesis_lines_enriched_pre_quality": sum(
            len(
                (row.get("enriched_pre_quality_v2") or {}).get(
                    "generic_synthesis_lines",
                    [],
                )
            )
            for row in rows
        ),
        "generic_synthesis_lines_after": sum(
            len((row.get("quality_v2") or {}).get("generic_synthesis_lines", []))
            for row in rows
        ),
        "duplicate_section_claims_before": sum(
            int(
                (row.get("sparse_quality_v2") or {}).get(
                    "duplicate_substantive_section_claim_count",
                    0,
                )
            )
            for row in rows
        ),
        "duplicate_section_claims_enriched_pre_quality": sum(
            int(
                (row.get("enriched_pre_quality_v2") or {}).get(
                    "duplicate_substantive_section_claim_count",
                    0,
                )
            )
            for row in rows
        ),
        "duplicate_section_claims_after": sum(
            int(
                (row.get("quality_v2") or {}).get(
                    "duplicate_substantive_section_claim_count", 0
                )
            )
            for row in rows
        ),
        "canary_selection": selection.to_dict(),
        "messages": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build an archive-only structured-data Quality v2 replay."
    )
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--ai-output", type=Path, required=True)
    parser.add_argument("--deterministic", type=Path, required=True)
    parser.add_argument("--supplemental", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_replay(
        packet=_json(args.packet),
        output=_json(args.ai_output),
        deterministic=_json(args.deterministic),
        supplemental=_json(args.supplemental),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "packet_id": result["packet_id"],
        "message_count": result["message_count"],
        "eligible_count": result["eligible_count"],
        "selected": result["canary_selection"]["selected_keys"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
