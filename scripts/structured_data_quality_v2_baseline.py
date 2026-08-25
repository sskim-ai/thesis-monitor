from __future__ import annotations

import argparse
import json
import re
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
from app.services.numeric_provenance_service import bind_numeric_fact_references
from app.services.runtime_reasoning_ownership_service import (
    apply_candidate_ownership_contracts,
)
from app.services.working_capital_user_visible_preintegration_service import (
    ensure_relation_semantics,
    normalize_directional_numeric_refs,
)


_GENERIC_SYNTHESIS = re.compile(
    r"현재 근거는 핵심 사업 조건(?:의 존재)?(?:을|를)? 보여도?\s*"
    r"투자 논리의 다음 확인까지 닫지는 못합니다"
)


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def _bound_output(
    packet: dict[str, object],
    output: dict[str, object],
) -> tuple[AIDailyReviewOutput, dict[str, object]]:
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


def _generic_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if _GENERIC_SYNTHESIS.search(line)]


def _duplicate_generic_claims(text: str) -> int:
    return 1 if len(_generic_lines(text)) >= 2 else 0


def build_baseline(
    *,
    packet: dict[str, object],
    output: dict[str, object],
    deterministic: dict[str, object],
) -> dict[str, object]:
    packet = ensure_relation_semantics(packet)
    market = str(packet.get("market") or "").lower()
    packet_id = str(packet.get("packet_id") or "")
    ai_output, numeric_binding = _bound_output(packet, output)
    market_context = packet.get("market_context")
    if not isinstance(market_context, dict):
        raise ValueError("packet market context is missing")
    deterministic_rows = deterministic.get("messages")
    if not isinstance(deterministic_rows, list):
        raise ValueError("deterministic messages are missing")
    reviews = {item.ticker: item for item in ai_output.stock_reviews}
    candidates = []
    messages: list[dict[str, object]] = []
    for row in deterministic_rows:
        if not isinstance(row, dict) or not isinstance(row.get("payload"), dict):
            continue
        ticker = str(row.get("ticker") or "")
        deterministic_text = str(row["payload"].get("text") or "")
        is_market = ticker.startswith("__DAILY_DIGEST")
        if is_market:
            source_text = _render_ai_market_message(
                deterministic_text,
                ai_output.market_review,
                market_context=market_context,
                market=market,
                pilot_day=1,
                target_days=1,
            )
            message_key = f"market:{packet_id}"
        else:
            review = reviews.get(ticker)
            if review is None:
                raise ValueError(f"AI stock review is missing: {ticker}")
            source_text = _render_ai_stock_message(
                deterministic_text,
                review,
                market=market,
                pilot_day=1,
                target_days=1,
            )
            message_key = f"stock:{ticker}"
        candidate = build_production_candidate(
            source_text,
            deterministic_text=deterministic_text,
            message_key=message_key,
            market=market,
            packet_owner=packet_id,
            is_market_digest=is_market,
        )
        candidates.append(candidate)
        messages.append(
            {
                "ticker": ticker,
                "message_key": message_key,
                "candidate_text": candidate.candidate_text,
                "eligible": candidate.eligible,
                "errors": list(candidate.errors),
                "selected_renderer": candidate.selected_renderer,
                "generic_synthesis_lines": _generic_lines(candidate.candidate_text),
                "duplicate_generic_claims": _duplicate_generic_claims(
                    candidate.candidate_text
                ),
                "safety": candidate.result.safety if candidate.result else None,
            }
        )
    selection = select_limited_canary(candidates)
    return {
        "contract": "structured-data-quality-v2-baseline-v1",
        "packet_id": packet_id,
        "market": market,
        "base_code_required": True,
        "message_count": len(messages),
        "eligible_count": sum(bool(row["eligible"]) for row in messages),
        "generic_synthesis_lines": sum(
            len(row["generic_synthesis_lines"]) for row in messages
        ),
        "generic_synthesis_messages": sum(
            bool(row["generic_synthesis_lines"]) for row in messages
        ),
        "duplicate_section_claims": sum(
            int(row["duplicate_generic_claims"]) for row in messages
        ),
        "numeric_binding": numeric_binding,
        "canary_selection": selection.to_dict(),
        "messages": messages,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reproduce the instruction-commit sparse Quality v2 baseline."
    )
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--ai-output", type=Path, required=True)
    parser.add_argument("--deterministic", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_baseline(
        packet=_json(args.packet),
        output=_json(args.ai_output),
        deterministic=_json(args.deterministic),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "packet_id": result["packet_id"],
                "message_count": result["message_count"],
                "eligible_count": result["eligible_count"],
                "generic_synthesis_lines": result["generic_synthesis_lines"],
                "duplicate_section_claims": result["duplicate_section_claims"],
                "selected": result["canary_selection"]["selected_keys"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
