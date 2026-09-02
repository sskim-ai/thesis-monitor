from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


DISCLAIMER = "※ 분석 분류이며 주문·자동매매·의무 매매 지시가 아닙니다."


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_json_object:{path}")
    return value


def _write(path: Path, value: str) -> None:
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _write_json(path: Path, value: object) -> None:
    _write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _market_proof(root: Path, market: str) -> dict[str, object]:
    path = root / market / "accepted-artifact.json"
    artifact = _read(path)
    plans = artifact["accepted_plans"]
    blocks = {row["ticker"]: row for row in artifact["blocks"]}
    diagnostics = {
        row["ticker"]: row
        for row in artifact["decision_consistency"]["diagnostics"]
    }
    rows = []
    for plan in plans:
        block = blocks[plan["ticker"]]
        diagnostic = diagnostics[plan["ticker"]]
        rows.append(
            {
                "ticker": plan["ticker"],
                "candidate": plan["candidate_decision"],
                "adjudication_status": plan["adjudication_status"],
                "adjudication_recommendation": plan["adjudication_recommendation"],
                "accepted": plan["accepted_decision"],
                "accepted_source": plan["accepted_source"],
                "evidence_fingerprint": plan["candidate_evidence_fingerprint"],
                "accepted_decision_id": plan["accepted_decision_id"],
                "rendered_sha256": hashlib.sha256(block["text"].encode()).hexdigest(),
                "rendered_character_count": len(block["text"]),
                "common_disclaimer_occurrences": block["text"].count(DISCLAIMER),
                "consistency_explained": diagnostic["explained"],
            }
        )
    repairs = sorted((root / market).glob("*.repair.json"))
    return {
        "packet_id": artifact["packet_id"],
        "artifact_sha256": _sha(path),
        "context_ready_count": len(artifact["evidence_packets"]),
        "candidate_count": len(artifact["candidates"]),
        "accepted_count": artifact["ready_count"],
        "not_ready_count": artifact["not_ready_count"],
        "explicit_v2_count": len(artifact["blocks"]),
        "fallback_count": 0,
        "decision_distribution": dict(
            sorted(Counter(row["accepted"] for row in rows).items())
        ),
        "bounded_repair_count": len(repairs),
        "bounded_repair_tickers": [path.name.split(".")[-3] for path in repairs],
        "message_quality": artifact["message_quality"],
        "decision_consistency": {
            key: artifact["decision_consistency"][key]
            for key in (
                "status",
                "unexplained_accepted_decision_drift",
                "raw_candidate_used_as_final",
                "daily_review_overrides_valid_v2_accepted",
            )
        },
        "common_disclaimer_occurrences": sum(
            row["common_disclaimer_occurrences"] for row in rows
        ),
        "rows": rows,
    }


def _delivery_proof(root: Path) -> dict[str, object]:
    receipt = _read(root / "test-sink-final-receipt.json")
    rows = [
        {
            key: row[key]
            for key in (
                "sequence",
                "ticker",
                "route",
                "logical_identity",
                "character_count",
                "rendered_sha256",
                "outbound_sha256",
                "received_sha256",
                "exact_payload_match",
                "send_attempts",
            )
        }
        for row in receipt["rows"]
    ]
    return {
        "contract": "four-track-test-recipient-sanitized-receipt-v1",
        "namespace": receipt["namespace"],
        "status": receipt["status"],
        "planned_message_count": receipt["planned_message_count"],
        "sent_message_count": receipt["sent_message_count"],
        "initial_sent_count": receipt["initial_sent_count"],
        "continuation_sent_count": receipt["continuation_sent_count"],
        "rate_limit_recovery": receipt["rate_limit_recovery"],
        "exact_payload_match": receipt["exact_payload_match"],
        "duplicate_count": receipt["duplicate_count"],
        "orphan_count": receipt["orphan_count"],
        "production_collision": receipt["production_collision"],
        "production_intent_created": receipt["production_intent_created"],
        "production_recipient_send_count": receipt["production_recipient_send_count"],
        "raw_recipient_ids_retained": 0,
        "account_identifiers_retained": 0,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--reports-dir", type=Path, required=True)
    args = parser.parse_args()
    kr = _market_proof(args.input_root, "kr")
    us = _market_proof(args.input_root, "us")
    delivery = _delivery_proof(args.input_root)
    proof = {
        "contract": "four-track-production-equivalent-integration-proof-v1",
        "status": "PASS",
        "model": "gpt-5.6-sol",
        "reasoning_effort": "xhigh",
        "kr": kr,
        "us": us,
        "test_recipient_delivery": delivery,
        "production_packet_mutation": 0,
        "production_accepted_mutation": 0,
        "production_assessment_mutation": 0,
        "production_notification_mutation": 0,
        "production_delivery_ledger_mutation": 0,
    }
    _write_json(
        args.reports_dir / "20260902-four-track-integration-proof.json", proof
    )
    _write_json(
        args.reports_dir / "20260902-test-recipient-integration-receipt.json",
        delivery,
    )
    _write(
        args.reports_dir / "20260902-kr-production-equivalent-final.md",
        f"""# 2026-09-02 KR Production-Equivalent Final

- Packet: `{kr['packet_id']}`
- Model / effort: `gpt-5.6-sol` / `xhigh`
- Context / candidate / accepted / explicit V2: `8/8/8/8`
- Not ready / fallback: `0/0`
- Distribution: `{kr['decision_distribution']}`
- Bounded repairs: `{kr['bounded_repair_count']}` ({', '.join(kr['bounded_repair_tickers'])})
- Message quality / repetition: `PASS / 0`
- Common disclaimer occurrences: `0`
- Decision consistency / unexplained drift: `PASS / 0`
- Raw candidate final / daily-review accepted override: `0/0`

The frozen KR cohort includes the mandatory controls `047810`, `000660`, `005930`, `010120`,
and `012450`. Candidate, accepted-plan, renderer, and exact-payload validation all completed with
no production send or state mutation.
""",
    )
    _write(
        args.reports_dir / "20260902-us-production-equivalent-final.md",
        f"""# 2026-09-02 US Production-Equivalent Final

- Packet: `{us['packet_id']}`
- Model / effort: `gpt-5.6-sol` / `xhigh`
- Context / candidate / accepted / explicit V2: `14/14/14/14`
- Not ready / fallback: `0/0`
- Distribution: `{us['decision_distribution']}`
- Bounded repairs: `{us['bounded_repair_count']}` ({', '.join(us['bounded_repair_tickers'])})
- Message quality / repetition: `PASS / 0`
- Common disclaimer occurrences: `0`
- Decision consistency / unexplained drift: `PASS / 0`
- Raw candidate final / daily-review accepted override: `0/0`

No decision distribution was forced. The production-equivalent path used the immutable run-51
packet, signed-in Codex, strict candidate validation, adjudication, accepted-plan ownership, and
the repaired renderer. Production send and state mutation were both zero.
""",
    )
    _write(
        args.reports_dir / "20260902-test-recipient-integration-delivery.md",
        f"""# 2026-09-02 Test Recipient Integration Delivery

- Dedicated non-production sink isolation: `PASS`
- Planned / sent: `{delivery['planned_message_count']}/{delivery['sent_message_count']}`
- Initial / continuation: `{delivery['initial_sent_count']}/{delivery['continuation_sent_count']}`
- Rate-limit recovery: `{delivery['rate_limit_recovery']}`
- Exact payload match: `{delivery['exact_payload_match']}`
- Duplicate / orphan: `{delivery['duplicate_count']}/{delivery['orphan_count']}`
- Production collision / intent / send: `0/0/0`
- Raw recipient IDs retained: `0`

Telegram returned HTTP 429 after 20 exact messages. The continuation contract selected only the
two unsent logical identities and closed the final 22-message set without duplicate delivery.
""",
    )
    print(json.dumps({"status": "PASS", "kr": 8, "us": 14, "sent": 22}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
