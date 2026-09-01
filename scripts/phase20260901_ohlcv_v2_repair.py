from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from datetime import datetime
from pathlib import Path

from app.services.cross_market_decision_engine_service import (
    build_decision_evidence_packet,
)
from app.services.ohlcv_client import OhlcvClient
from app.services.packet_owned_technical_context_service import (
    PacketOwnedTechnicalContext,
)


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_json_object:{path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


async def collect(args: argparse.Namespace) -> None:
    packet_path = Path(args.packet).resolve()
    packet = _read_json(packet_path)
    stocks = [row for row in packet.get("stocks") or () if isinstance(row, dict)]
    if not stocks:
        raise ValueError("packet_stock_inventory_missing")
    as_of = datetime.fromisoformat(args.as_of or str(packet.get("generated_at") or ""))
    client = OhlcvClient()
    rows: list[dict[str, object]] = []
    evidence_packets = []
    replay_packet = json.loads(json.dumps(packet))
    replay_stocks = {
        str(row.get("ticker") or "").upper(): row
        for row in replay_packet.get("stocks") or ()
        if isinstance(row, dict)
    }
    for stock in stocks:
        ticker = str(stock.get("ticker") or "").upper()
        price_context = await client.fetch_price_context(ticker, as_of=as_of)
        technical_context = PacketOwnedTechnicalContext.model_validate(
            price_context.technical_context_payload()
        )
        replay_stocks[ticker]["technical_context"] = technical_context.model_dump(mode="json")
        evidence = build_decision_evidence_packet(
            packet=replay_packet,
            stock=replay_stocks[ticker],
            technical_context=technical_context,
        )
        evidence_packets.append(evidence)
        rows.append(
            {
                "ticker": ticker,
                "technical_context_id": technical_context.technical_context_id,
                "status": technical_context.status,
                "freshness_state": technical_context.freshness_state,
                "last_completed_bar": technical_context.last_completed_bar,
                "bar_counts": technical_context.bar_counts,
                "feature_counts": {
                    key: value.feature_count for key, value in technical_context.quality.items()
                },
                "quality": {
                    key: value.model_dump(mode="json")
                    for key, value in technical_context.quality.items()
                },
                "raw_bar_fingerprint": technical_context.raw_bar_fingerprint,
                "feature_fingerprint": technical_context.feature_fingerprint,
                "acquisition": technical_context.acquisition.model_dump(mode="json"),
                "failure_reason": technical_context.failure_reason,
                "evidence_sha256": evidence.evidence_sha256,
            }
        )
    output = Path(args.output).resolve()
    replay_path = output.with_name(output.stem + "-packet-copy.json")
    _write_json(replay_path, replay_packet)
    status_counts = {
        status: sum(str(row["status"]) == status for row in rows)
        for status in ("FULL", "PARTIAL_SAFE", "UNAVAILABLE", "INVALID")
    }
    _write_json(
        output,
        {
            "contract": "ohlcv-v2-repair-evidence-v1",
            "source_packet": str(packet_path),
            "source_packet_sha256": _sha256(packet_path),
            "source_packet_mutated": False,
            "replay_packet_copy": str(replay_path),
            "packet_id": packet.get("packet_id"),
            "market": packet.get("market"),
            "as_of": as_of.isoformat(),
            "subject_count": len(rows),
            "status_counts": status_counts,
            "decision_context_ready_count": len(evidence_packets),
            "rows": rows,
        },
    )
    print(
        json.dumps(
            {
                "output": str(output),
                "replay_packet_copy": str(replay_path),
                "subject_count": len(rows),
                "status_counts": status_counts,
                "decision_context_ready_count": len(evidence_packets),
            },
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--as-of")
    asyncio.run(collect(parser.parse_args()))


if __name__ == "__main__":
    main()
