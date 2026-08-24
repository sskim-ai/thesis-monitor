from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a no-send KR rehearsal message report")
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--ai-status", default="NOT_GENERATED")
    parser.add_argument("--ai-reason", default="shadow_numeric_semantic_gate_not_ready")
    args = parser.parse_args()

    bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
    messages = bundle.get("messages", [])
    if not isinstance(messages, list):
        raise ValueError("fallback messages must be a list")
    sections = [
        "# MANUAL LIVE REHEARSAL - NOT SENT",
        "",
        f"- Rehearsal: `{bundle.get('rehearsal_id')}`",
        f"- Packet: `{bundle.get('packet_id')}`",
        "- This is a 19:34 fresh rehearsal, not a 16:15 reconstruction.",
        f"- AI candidate: `{args.ai_status}` (`{args.ai_reason}`)",
        "- Production-preference bundle: `DETERMINISTIC_FALLBACK`",
        "- Telegram sends: `0`",
        "",
        "The selected production-preference version is exactly the fallback version printed below.",
    ]
    for index, item in enumerate(messages, start=1):
        if not isinstance(item, dict):
            raise ValueError("message row must be an object")
        payload = item.get("payload")
        if not isinstance(payload, dict) or not isinstance(payload.get("text"), str):
            raise ValueError("message payload text missing")
        ticker = str(item.get("ticker") or "")
        label = "KR market digest" if ticker == "__DAILY_DIGEST_KR__" else ticker
        sections.extend(
            [
                "",
                "---",
                "",
                f"## {index}. {label}",
                "",
                str(payload["text"]),
            ]
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(sections).rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
