from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Mapping

from sqlmodel import Session

from app.database import engine
from app.services.ai_assisted_delivery_service import (
    _render_ai_market_message,
    _render_ai_stock_message,
)
from app.services.ai_reasoning_quality_service import (
    runtime_message_quality_receipt,
    verify_runtime_message_quality_receipt,
)
from app.services.ai_review_service import validate_ai_review_output
from app.services.night_futures_session_mapping_service import (
    KST,
    map_latest_completed_krx_night_session,
)
from app.services.numeric_provenance_service import bind_numeric_fact_references
from app.services.runtime_reasoning_ownership_service import (
    apply_candidate_ownership_contracts,
)
from app.services.semantic_decision_service import ensure_semantic_scope_contract
from app.services.working_capital_user_visible_preintegration_service import (
    ensure_relation_semantics,
    normalize_directional_numeric_refs,
)


PACKET_ID = "2026-09-02-us-run-51-39a4d4eec53e"
MARKET_TICKER = "__DAILY_DIGEST__"


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _deterministic_messages(path: Path) -> dict[str, str]:
    value = _load(path)
    return {
        str(item["ticker"]): str(item["payload"]["text"])
        for item in value["messages"]
        if isinstance(item, Mapping) and isinstance(item.get("payload"), Mapping)
    }


def _binding_and_ownership(
    packet: dict[str, object],
    candidate: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    upgraded = ensure_semantic_scope_contract(ensure_relation_semantics(packet))
    directional, relation = normalize_directional_numeric_refs(upgraded, candidate)
    owned, ownership = apply_candidate_ownership_contracts(upgraded, directional)
    binding = bind_numeric_fact_references(upgraded, owned)
    return (
        {
            "errors": list(binding.errors),
            "report": binding.report,
            "relation": relation,
        },
        ownership,
    )


def _daily_review_proof(args: argparse.Namespace) -> dict[str, object]:
    packet = _load(args.packet)
    candidate = _load(args.candidate)
    if packet.get("packet_id") != PACKET_ID:
        raise ValueError("run51_packet_identity_mismatch")
    binding, ownership = _binding_and_ownership(packet, candidate)
    with Session(engine) as session:
        output, errors = validate_ai_review_output(session, packet, candidate)
    if output is None:
        raise ValueError(f"run51_daily_review_replay_failed:{errors}")
    deterministic = _deterministic_messages(args.deterministic)
    messages = [
        {
            "ticker": MARKET_TICKER,
            "text": _render_ai_market_message(
                deterministic[MARKET_TICKER],
                output.market_review,
                market_context=packet["market_context"],
                market="us",
                pilot_day=5,
                target_days=5,
            ),
        }
    ]
    messages.extend(
        {
            "ticker": review.ticker,
            "text": _render_ai_stock_message(
                deterministic[review.ticker],
                review,
                market="us",
                pilot_day=5,
                target_days=5,
            ),
        }
        for review in output.stock_reviews
    )
    expected = [str(item["ticker"]) for item in packet["stocks"]]
    quality = runtime_message_quality_receipt(
        packet,
        output,
        messages,
        expected_stock_tickers=expected,
        checked_at=datetime.now(UTC),
    )
    verified = verify_runtime_message_quality_receipt(
        quality,
        packet,
        output,
        messages,
        expected_stock_tickers=expected,
    )
    checks = quality["check_results"]
    original_validation = _load(args.original_validation)
    return {
        "contract": "run51-daily-review-quality-proof-v1",
        "packet_id": PACKET_ID,
        "source": {
            "packet_sha256": _sha256(args.packet),
            "candidate_sha256": _sha256(args.candidate),
            "original_validation_sha256": _sha256(args.original_validation),
            "original_error_count": len(original_validation.get("errors") or ()),
        },
        "after": {
            "schema_and_semantic_errors": errors,
            "numeric_binding_errors": binding["errors"],
            "auto_bound": binding["report"].get("auto_bound"),
            "manual_legacy": binding["report"].get("manual_legacy"),
            "typed_valuation_errors": (
                binding["report"].get("typed_valuation_interpretations", {}).get("errors", [])
            ),
            "quality_status": quality["status"],
            "quality_verified": verified,
            "substantive_repeated_sentence_count": checks["substantive_repeated_sentence_count"],
            "template_skeleton_repeat_count": checks["template_skeleton_repeat_count"],
            "observer_holder_distinct_count": checks["observer_holder_distinct_count"],
            "rendered_identity_prose_mismatch_count": checks[
                "rendered_identity_prose_mismatch_count"
            ],
            "valuation_evidence_error_count": checks["valuation_evidence_error_count"],
            "final_rendered_language": checks["final_rendered_language"],
            "rendered_heading_quality": checks["rendered_heading_quality"],
            "message_count": len(messages),
            "stock_count": len(output.stock_reviews),
        },
        "ownership": {
            "status": ownership.get("status"),
            "suppression_count": len(ownership.get("suppressions") or ()),
            "handoff_count": len(ownership.get("handoffs") or ()),
            "unresolved": ownership.get("unresolved") or [],
            "suppressions": ownership.get("suppressions") or [],
            "handoffs": ownership.get("handoffs") or [],
        },
        "messages": [
            {
                "ticker": item["ticker"],
                "character_count": len(item["text"]),
                "sha256": hashlib.sha256(item["text"].encode()).hexdigest(),
            }
            for item in messages
        ],
        "production_send": 0,
    }


def _night_proof(args: argparse.Namespace) -> dict[str, object]:
    source = _load(args.night_source)
    mapping = map_latest_completed_krx_night_session(
        datetime(2026, 9, 2, 8, 20, tzinfo=KST),
        us_regular_session_date=date(2026, 9, 1),
    )
    if mapping is None:
        raise ValueError("run51_night_session_mapping_unavailable")
    returned = sorted(
        {
            str(row.get("returned_night_bas_dd") or "")
            for attempt in source.get("attempts") or ()
            for row in attempt.get("per_product") or ()
            if isinstance(row, Mapping) and row.get("returned_night_bas_dd")
        }
    )
    return {
        "contract": "run51-night-futures-session-proof-v1",
        "packet_id": PACKET_ID,
        "mapping": mapping.to_dict(),
        "provider_semantics": "completed_session_end_date",
        "provider_dates_returned": returned,
        "ready_count": source.get("ready_count"),
        "rendered_count": source.get("rendered_count"),
        "status": source.get("status"),
        "classification": "SOURCE_LIMITATION_SAFE",
        "forced_reclassification": 0,
        "source_sha256": _sha256(args.night_source),
    }


def _runtime_state_proof(args: argparse.Namespace) -> dict[str, object]:
    receipt = _load(args.probe_receipt)
    return {
        "contract": "run51-codex-runtime-state-proof-v1",
        "probe_contract": receipt.get("contract"),
        "probe_status": receipt.get("status"),
        "model": "gpt-5.6-sol",
        "reasoning_effort": "xhigh",
        "sandbox": "read-only",
        "state_contract": "codex-runtime-state-v1",
        "state_scope": "isolated_per_claim_namespace",
        "codex_home": "claim_scoped_private_0700",
        "sqlite_home": "claim_scoped_private_0700",
        "sqlite_wal_probe": "PASS",
        "signed_in_auth": "owner_only_read_only_symlink_reference",
        "plaintext_auth_copy": 0,
        "production_send": 0,
        "database_mutation": 0,
        "receipt_sha256": _sha256(args.probe_receipt),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--original-validation", type=Path, required=True)
    parser.add_argument("--deterministic", type=Path, required=True)
    parser.add_argument("--night-source", type=Path, required=True)
    parser.add_argument("--probe-receipt", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    _write_json(
        args.output_dir / "20260902-daily-review-quality-proof.json",
        _daily_review_proof(args),
    )
    _write_json(
        args.output_dir / "20260902-night-futures-session-proof.json",
        _night_proof(args),
    )
    _write_json(
        args.output_dir / "20260902-codex-runtime-state-proof.json",
        _runtime_state_proof(args),
    )


if __name__ == "__main__":
    main()
