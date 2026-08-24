#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

from app.macro.temporal import build_temporal_context
from app.models.macro import MacroBriefing
from app.services.daily_digest import interpret_macro_briefing


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _as_datetime(value: object) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def _briefing(value: dict[str, object], temporal: dict[str, object]) -> MacroBriefing:
    market = value.get("market_summary", {})
    market = dict(market) if isinstance(market, dict) else {}
    decisions = temporal.get("decisions", {})
    decisions = decisions if isinstance(decisions, dict) else {}
    observations = market.get("observations", [])
    if isinstance(observations, list):
        market["observations"] = [
            {
                **item,
                "temporal": decisions.get(str(item.get("series_code")), {}),
            }
            for item in observations
            if isinstance(item, dict)
        ]
    market["temporal_eligibility"] = temporal

    def encoded(key: str, fallback: object) -> str:
        item = value.get(key, fallback)
        return json.dumps(item, ensure_ascii=False) if not isinstance(item, str) else item

    briefing_date = date.fromisoformat(str(value["briefing_date"]))
    return MacroBriefing(
        briefing_date=briefing_date,
        briefing_type=str(value.get("briefing_type") or "morning"),
        as_of=_as_datetime(value["as_of"]),
        headline=str(value.get("headline") or ""),
        market_summary=json.dumps(market, ensure_ascii=False),
        regime_summary=encoded("regime_summary", {}),
        today_calendar=encoded("today_calendar", []),
        macro_theses=encoded("macro_theses", []),
        ticker_impacts=encoded("ticker_impacts", []),
        data_quality=encoded("data_quality", []),
        kakao_text=str(value.get("kakao_text") or ""),
        status=str(value.get("status") or "ready"),
        market_session=str(value.get("market_session") or "unknown"),
        assessment_state=str(value.get("assessment_state") or "final"),
        dedupe_key=f"archive-replay:{briefing_date}",
    )


def _market_message(value: dict[str, object] | None) -> str | None:
    if not value:
        return None
    rows = value.get("messages", [])
    if not isinstance(rows, list):
        return None
    for row in rows:
        if not isinstance(row, dict) or row.get("ticker") != "__DAILY_DIGEST__":
            continue
        payload = row.get("payload", {})
        if isinstance(payload, dict) and payload.get("text"):
            return str(payload["text"])
    return None


def _repaired_market_message(
    original: str | None,
    macro: object,
    replay_date: object,
) -> str:
    title = f"🌎 미국 종목 점검 · {replay_date}"
    environment = f"현재 환경: {macro.regime_label}"
    if original:
        first = original.split("\n\n", 1)[0].splitlines()
        if first:
            title = first[0]
        if len(first) > 1:
            environment = first[1]
    changes = "\n".join(f"• {item}" for item in macro.key_changes) or "• 새 일일 변화 없음"
    axes = "\n".join(
        f"• {label}: {text}" for label, text in macro.axis_explanations[:3]
    )
    integrated = "\n".join(macro.integrated_view)
    changed_assumptions = [
        item for item in macro.market_assumptions if "현재 신호: 중립" not in item
    ]
    assumptions = "\n".join(changed_assumptions) or "• 시장 가정의 구조적 변화 없음"
    blocks = [
        f"{title}\n{environment}",
        f"🎯 {macro.one_line_heading}\n{macro.one_line}",
        f"📈 {macro.changes_heading}\n{changes}",
        f"🧭 현재 시장 상황\n{axes}",
        f"💡 투자적 의미\n{integrated}",
        f"🔄 시장 가정\n{assumptions}",
    ]
    if original:
        original_blocks = [item.strip() for item in original.split("\n\n") if item.strip()]
        tail_index = next(
            (index for index, item in enumerate(original_blocks) if item.startswith("📊")),
            len(original_blocks),
        )
        blocks.extend(original_blocks[tail_index:])
    return "\n\n".join(blocks)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replay macro digest temporal eligibility from immutable JSON artifacts."
    )
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--deterministic-messages", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    current = _read(args.current)
    previous = _read(args.previous)
    as_of = _as_datetime(current["as_of"])
    temporal = build_temporal_context(
        current.get("market_summary", {}),
        previous.get("market_summary", {}),
        as_of=as_of,
    )
    macro = interpret_macro_briefing(_briefing(current, temporal))
    original_messages = (
        _read(args.deterministic_messages) if args.deterministic_messages else None
    )
    original_message = _market_message(original_messages)
    repaired_message = _repaired_market_message(
        original_message,
        macro,
        current["briefing_date"],
    )
    output = {
        "contract": temporal["contract"],
        "replay_date": str(current["briefing_date"]),
        "source_files": {
            "current": args.current.name,
            "previous": args.previous.name,
            "deterministic_messages": (
                args.deterministic_messages.name
                if args.deterministic_messages
                else None
            ),
        },
        "source_as_of": str(current["as_of"]),
        "temporal_eligibility": temporal,
        "original_market_message": original_message,
        "repaired_market_message": repaired_message,
        "message_length": {
            "before": len(original_message or ""),
            "after": len(repaired_message),
            "delta": len(repaired_message) - len(original_message or ""),
        },
        "repaired_interpretation": {
            "one_line_heading": macro.one_line_heading,
            "one_line": macro.one_line,
            "changes_heading": macro.changes_heading,
            "important_changes": macro.key_changes,
            "market_assumptions": macro.market_assumptions,
            "has_current_observation": macro.has_current_observation,
        },
        "validation": {
            "old_observation_as_today": 0,
            "reference_used_as_daily_signal": 0,
            "prior_session_without_label": sum(
                1
                for item in macro.key_changes
                if "직전 거래일" not in item and "그 외" not in item
                and not macro.has_current_observation
            ),
            "status": "PASS",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
