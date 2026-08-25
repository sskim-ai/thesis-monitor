from __future__ import annotations

import argparse
import json
from pathlib import Path


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _rows(payload: dict[str, object]) -> dict[str, dict[str, object]]:
    messages = payload.get("messages")
    if not isinstance(messages, list):
        raise ValueError("messages are missing")
    return {
        str(row.get("ticker") or ""): row
        for row in messages
        if isinstance(row, dict)
    }


def _block(label: str, value: object) -> str:
    return f"### {label}\n\n```text\n{str(value or '').strip()}\n```\n"


def build_benchmark(
    *,
    kr_baseline: dict[str, object],
    kr_replay: dict[str, object],
    us_baseline: dict[str, object],
    us_replay: dict[str, object],
) -> str:
    cases = (
        ("KR MARKET DIGEST", "__DAILY_DIGEST_KR__", kr_baseline, kr_replay),
        ("SK HYNIX", "000660", kr_baseline, kr_replay),
        ("HANWHA AEROSPACE", "012450", kr_baseline, kr_replay),
        ("US MARKET DIGEST", "__DAILY_DIGEST__", us_baseline, us_replay),
        ("CORZ", "CORZ", us_baseline, us_replay),
        ("CRCL", "CRCL", us_baseline, us_replay),
    )
    output = [
        "# KR/US Enriched Message Quality v2 Exact Benchmark",
        "",
        "Evidence class: immutable packet plus separately labeled "
        "`SUPPLEMENTAL_STRUCTURED_EVIDENCE`. Delivery and archive mutation: `0`.",
        "",
    ]
    for label, ticker, baseline, replay in cases:
        before = _rows(baseline).get(ticker)
        after = _rows(replay).get(ticker)
        if before is None or after is None:
            raise ValueError(f"benchmark case is missing: {ticker}")
        output.extend(
            [
                f"## {label}",
                "",
                _block("SPARSE_PREVIOUS", before.get("candidate_text")),
                _block("ENRICHED_PRE_QUALITY", after.get("enriched_pre_quality")),
                _block(
                    "ENRICHED_POST_QUALITY_V2",
                    after.get("enriched_post_quality_v2"),
                ),
                _block(
                    "DETERMINISTIC_REFERENCE",
                    after.get("deterministic_reference"),
                ),
                _block("ADAPTIVE_SELECTED", after.get("adaptive_selected")),
                "- Quality v2: `"
                f"{(after.get('quality_v2') or {}).get('status', 'UNKNOWN')}`",
                f"- Renderer: `{after.get('selected_renderer') or 'NONE'}`",
                f"- Canary eligible: `{after.get('eligible')}`",
                "",
            ]
        )
    return "\n".join(output).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the exact Quality v2 benchmark.")
    parser.add_argument("--kr-baseline", type=Path, required=True)
    parser.add_argument("--kr-replay", type=Path, required=True)
    parser.add_argument("--us-baseline", type=Path, required=True)
    parser.add_argument("--us-replay", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    text = build_benchmark(
        kr_baseline=_json(args.kr_baseline),
        kr_replay=_json(args.kr_replay),
        us_baseline=_json(args.us_baseline),
        us_replay=_json(args.us_replay),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(json.dumps({"output": str(args.output), "bytes": len(text.encode())}))


if __name__ == "__main__":
    main()
