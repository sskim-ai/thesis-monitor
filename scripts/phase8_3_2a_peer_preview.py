from __future__ import annotations

# ruff: noqa: E402

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.free_source_peer_service import render_free_peer_context


def _after_messages(source: str) -> list[tuple[str, str, str]]:
    market = "unknown"
    messages: list[tuple[str, str, str]] = []
    sections = re.split(r"(?=^## |^### )", source, flags=re.MULTILINE)
    for section in sections:
        market_match = re.match(r"^## (KR|US)\s*$", section.splitlines()[0] if section else "")
        if market_match:
            market = market_match.group(1).lower()
            continue
        ticker_match = re.match(r"^### ([A-Z0-9]+)\s*$", section.splitlines()[0] if section else "")
        if not ticker_match or "#### AFTER - Phase 8.5.3.1" not in section:
            continue
        after = section.split("#### AFTER - Phase 8.5.3.1", 1)[1].strip()
        messages.append((market, ticker_match.group(1), after))
    return messages


def _integrate(message: str, peer_text: str | None) -> str:
    if not peer_text:
        return message
    marker = "📐 Valuation\n"
    start = message.find(marker)
    if start < 0:
        raise ValueError("valuation section missing")
    paragraph_start = start + len(marker)
    paragraph_end = message.find("\n\n", paragraph_start)
    if paragraph_end < 0:
        paragraph_end = len(message)
    paragraph = message[paragraph_start:paragraph_end].rstrip()
    return (
        message[:paragraph_start]
        + paragraph
        + " "
        + peer_text
        + message[paragraph_end:]
    )


def build_preview(source: str, audit: dict[str, object]) -> str:
    states = audit.get("states")
    if not isinstance(states, dict):
        raise ValueError("free peer states missing")
    sections: list[str] = []
    lengths: list[dict[str, object]] = []
    for market, ticker, before in _after_messages(source):
        state = states.get(ticker)
        peer_text = (
            render_free_peer_context(state) if isinstance(state, dict) else None
        )
        after = _integrate(before, peer_text)
        change = len(after) - len(before)
        change_pct = round(change / len(before) * 100, 2) if before else 0.0
        lengths.append(
            {
                "ticker": ticker,
                "market": market,
                "peer_added": peer_text is not None,
                "before_chars": len(before),
                "after_chars": len(after),
                "change_chars": change,
                "change_pct": change_pct,
            }
        )
        sections.append(
            f"## {market.upper()} {ticker}\n\n"
            f"Status: {'PEER_CONTEXT_ADDED' if peer_text else 'UNCHANGED'}\n\n"
            f"### Before\n\n{before}\n\n"
            f"### After\n\n{after}"
        )
    enhanced = [item for item in lengths if item["peer_added"]]
    unchanged = [item for item in lengths if not item["peer_added"]]
    average_added_pct = (
        round(sum(float(item["change_pct"]) for item in enhanced) / len(enhanced), 2)
        if enhanced
        else 0.0
    )
    table = [
        "| Market | Ticker | State | Before chars | After chars | Change |",
        "|---|---:|---|---:|---:|---:|",
        *[
            f"| {item['market'].upper()} | {item['ticker']} | "
            f"{'ADDED' if item['peer_added'] else 'UNCHANGED'} | "
            f"{item['before_chars']} | {item['after_chars']} | {item['change_pct']}% |"
            for item in lengths
        ],
    ]
    header = f"""# Phase 8.3.2A Free-Source Full-Message Preview

Immutable context: 2026-08-18 assessment archive, with US completed-session valuation dated 2026-08-17. This is archive-only; Telegram sends: 0.

Peer context added: {len(enhanced)} / {len(lengths)} representative messages.

Unchanged baseline messages: {len(unchanged)} / {len(lengths)}; exact character change: 0 for every unavailable/suppressed subject.

Average length change where peer context was added: {average_added_pct}%.

The peer sentence is integrated into the existing Valuation section. No new section is created.

## Length Audit

{chr(10).join(table)}
"""
    return header.rstrip() + "\n\n" + "\n\n---\n\n".join(sections) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-preview", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    preview = build_preview(
        args.source_preview.read_text(encoding="utf-8"),
        audit,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(preview, encoding="utf-8")


if __name__ == "__main__":
    main()
