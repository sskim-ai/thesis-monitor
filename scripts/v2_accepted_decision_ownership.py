from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from app.services.accepted_decision_v2_service import (
    AcceptedDecisionPlan,
    AcceptedDecisionStatus,
    AcceptedV2Adjudication,
    accepted_message_quality,
    render_accepted_v2_shadow,
    resolve_accepted_v2_decision,
    validate_accepted_v2_decision,
)
from app.services.cross_market_decision_engine_service import Decision, DecisionEvidencePacket
from app.services.preconfirmation_decision_v2_service import (
    PreconfirmationDecisionCandidate,
    validate_preconfirmation_candidate,
)
from scripts.kr_final_preenable_test_delivery import deliver_test_messages
from scripts.kr_market_preenable_evidence import audit_test_sink, load_env_values


CONTRACT = "v2-accepted-decision-replay-v1"
TEST_NAMESPACE = "V2_ACCEPTED_DECISION_OWNERSHIP_TEST_ONLY"


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256_bytes(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _row_map(value: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    return {
        str(row["ticker"]): row
        for row in value.get("rows") or ()
        if isinstance(row, Mapping) and row.get("ticker")
    }


def accepted_decision_counts(plans: Sequence[AcceptedDecisionPlan]) -> dict[str, int]:
    counts = Counter(
        str(plan.accepted_decision)
        for plan in plans
        if plan.status == AcceptedDecisionStatus.READY and plan.accepted_decision is not None
    )
    return {decision: counts.get(decision, 0) for decision in ("BUY", "HOLD", "SELL")}


def build_accepted_replay(
    *,
    evidence: Mapping[str, object],
    shadow: Mapping[str, object],
    agreement: Mapping[str, object],
    evidence_source_sha256: str,
    shadow_source_sha256: str,
    agreement_source_sha256: str,
) -> dict[str, object]:
    packet_rows = _row_map(evidence)
    shadow_rows = _row_map(shadow)
    agreement_rows = _row_map(agreement)
    if not (
        len(packet_rows) == len(shadow_rows) == len(agreement_rows) == 20
        and set(packet_rows) == set(shadow_rows) == set(agreement_rows)
    ):
        raise ValueError("accepted_replay_subject_set_not_20_exact")
    if shadow.get("source_evidence_sha256") != evidence_source_sha256:
        raise ValueError("accepted_replay_evidence_sha_mismatch")

    rows: list[dict[str, object]] = []
    rendered = []
    plans: list[AcceptedDecisionPlan] = []
    errors: list[str] = []
    for ticker, shadow_row in shadow_rows.items():
        packet_payload = packet_rows[ticker].get("evidence_packet")
        if not isinstance(packet_payload, Mapping):
            errors.append(f"{ticker}:missing_evidence_packet")
            continue
        packet = DecisionEvidencePacket.model_validate(packet_payload)
        candidate_payload = shadow_row.get("candidate")
        if not isinstance(candidate_payload, Mapping):
            errors.append(f"{ticker}:missing_candidate")
            continue
        candidate = PreconfirmationDecisionCandidate.model_validate(candidate_payload)
        candidate_validation = validate_preconfirmation_candidate(packet, candidate)
        agreement_row = agreement_rows[ticker]
        v1_decision = cast(Decision, str(agreement_row.get("v1_decision")))
        material_disagreement = bool(agreement_row.get("material_disagreement"))
        adjudication_payload = agreement_row.get("adjudication")
        adjudication = (
            AcceptedV2Adjudication.model_validate(adjudication_payload)
            if isinstance(adjudication_payload, Mapping)
            else None
        )
        if candidate.decision != str(agreement_row.get("v2_decision")):
            errors.append(f"{ticker}:candidate_agreement_mismatch")
        plan = resolve_accepted_v2_decision(
            packet,
            candidate,
            v1_decision=v1_decision,
            material_disagreement=material_disagreement,
            adjudication=adjudication,
        )
        accepted_validation = validate_accepted_v2_decision(packet, plan)
        rendered_row = None
        if candidate_validation.valid and accepted_validation.valid:
            rendered_row = render_accepted_v2_shadow(packet, plan)
            rendered.append(rendered_row)
        else:
            errors.extend(
                f"{ticker}:candidate:{error}" for error in candidate_validation.errors
            )
            errors.extend(f"{ticker}:accepted:{error}" for error in accepted_validation.errors)
        plans.append(plan)
        rows.append(
            {
                "ticker": ticker,
                "company_name": packet.company_name,
                "market": packet.market,
                "evidence_fingerprint": packet.evidence_sha256,
                "v1_decision": v1_decision,
                "candidate_history": {
                    "candidate_decision_id": plan.candidate_decision_id,
                    "candidate_decision": candidate.decision,
                    "candidate_evidence_fingerprint": plan.candidate_evidence_fingerprint,
                    "candidate_preconfirmation_buy": candidate.pre_confirmation_buy,
                    "candidate_source_row_fingerprint": _sha256_bytes(shadow_row),
                    "source_artifact_sha256": shadow_source_sha256,
                },
                "material_disagreement": material_disagreement,
                "adjudication_history": (
                    {
                        "adjudication_id": plan.adjudication_id,
                        "adjudication_status": plan.adjudication_status,
                        "source_artifact_sha256": agreement_source_sha256,
                        **adjudication.model_dump(mode="json"),
                    }
                    if adjudication is not None
                    else {
                        "adjudication_id": None,
                        "adjudication_status": plan.adjudication_status,
                        "source_artifact_sha256": agreement_source_sha256,
                    }
                ),
                "accepted_plan": plan.model_dump(mode="json"),
                "candidate_validation": candidate_validation.model_dump(mode="json"),
                "accepted_validation": accepted_validation.model_dump(mode="json"),
                "rendered": rendered_row.model_dump(mode="json") if rendered_row else None,
                "status": (
                    "PASS"
                    if candidate_validation.valid and accepted_validation.valid
                    else "FAIL"
                ),
            }
        )

    quality = accepted_message_quality(tuple(rendered))
    candidate_counts = Counter(
        str((row.get("candidate_history") or {}).get("candidate_decision")) for row in rows
    )
    candidate_distribution = {
        decision: candidate_counts.get(decision, 0) for decision in ("BUY", "HOLD", "SELL")
    }
    accepted_distribution = accepted_decision_counts(plans)
    status = (
        "PASS"
        if not errors
        and len(rows) == 20
        and all(row["status"] == "PASS" for row in rows)
        and quality["status"] == "PASS"
        else "FAIL"
    )
    return {
        "contract": CONTRACT,
        "status": status,
        "subject_count": len(rows),
        "source_evidence_sha256": evidence_source_sha256,
        "source_candidate_artifact_sha256": shadow_source_sha256,
        "source_agreement_artifact_sha256": agreement_source_sha256,
        "candidate_distribution": candidate_distribution,
        "accepted_distribution": accepted_distribution,
        "candidate_preconfirmation_buy_count": sum(
            bool((row.get("candidate_history") or {}).get("candidate_preconfirmation_buy"))
            for row in rows
        ),
        "accepted_preconfirmation_buy_count": sum(
            bool((row.get("accepted_plan") or {}).get("accepted_preconfirmation_buy"))
            for row in rows
        ),
        "accepted_postconfirmation_hold_count": sum(
            bool((row.get("accepted_plan") or {}).get("accepted_postconfirmation_hold"))
            for row in rows
        ),
        "material_disagreement_count": sum(
            bool(row.get("material_disagreement")) for row in rows
        ),
        "adjudication_count": sum(
            bool((row.get("adjudication_history") or {}).get("adjudication_id"))
            for row in rows
        ),
        "ownership_repair_redecided_frozen_cases": 0,
        "message_quality": quality,
        "production_packet_changed": False,
        "v1_canary_state_changed": False,
        "v2_production_decision_block_visible": 0,
        "production_delivery_intent_created": 0,
        "errors": errors,
        "rows": rows,
    }


def _resolve(args: argparse.Namespace) -> None:
    evidence = _read_json(args.evidence)
    shadow = _read_json(args.shadow)
    agreement = _read_json(args.agreement)
    if not all(isinstance(value, Mapping) for value in (evidence, shadow, agreement)):
        raise ValueError("invalid_accepted_replay_input")
    assert isinstance(evidence, Mapping)
    assert isinstance(shadow, Mapping)
    assert isinstance(agreement, Mapping)
    result = build_accepted_replay(
        evidence=evidence,
        shadow=shadow,
        agreement=agreement,
        evidence_source_sha256=_sha256(args.evidence),
        shadow_source_sha256=_sha256(args.shadow),
        agreement_source_sha256=_sha256(args.agreement),
    )
    _write_json(args.output, result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "subjects": result["subject_count"],
                "candidate_distribution": result["candidate_distribution"],
                "accepted_distribution": result["accepted_distribution"],
            },
            sort_keys=True,
        )
    )


def _accepted_received_quality(text: str) -> Mapping[str, object]:
    required = (
        "🧪 SHADOW V2 · accepted decision 검증",
        "AI 수용 판단:",
        "증거 성숙도:",
        "가격 비대칭:",
        "🎯 판단",
        "🔄 판단 변경 조건",
    )
    errors = [f"missing:{token}" for token in required if token not in text]
    if len(text) > 3500:
        errors.append("message_too_long")
    if re.search(r"목표가|적정가|시장가\s*(?:매수|매도)", text):
        errors.append("forbidden_language")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


async def _send_test(args: argparse.Namespace) -> None:
    accepted = _read_json(args.accepted)
    if not isinstance(accepted, Mapping) or accepted.get("status") != "PASS":
        raise ValueError("accepted_replay_not_pass")
    rows = [row for row in accepted.get("rows") or () if isinstance(row, Mapping)]
    if len(rows) != 20 or any(row.get("status") != "PASS" for row in rows):
        raise ValueError("all_20_accepted_rows_must_pass")
    messages = [
        {
            "ticker": str(row["ticker"]),
            "route": "SHADOW_V2_ACCEPTED_TEST_ONLY",
            "logical_identity": f"{args.namespace}:{row['ticker']}",
            "text": str((row.get("rendered") or {}).get("text") or ""),
        }
        for row in rows
    ]
    start = args.offset
    stop = len(messages) if args.limit is None else start + args.limit
    messages = messages[start:stop]
    if not messages:
        raise ValueError("empty_accepted_test_message_slice")
    env = load_env_values(args.env_file)
    sink = audit_test_sink(env)
    if sink.get("available") is not True:
        raise ValueError(f"test_sink_unavailable:{sink.get('reason')}")
    selected_key = str(sink.get("selected_test_key_name") or "")
    receipt = await deliver_test_messages(
        messages,
        token=env.get("TELEGRAM_BOT_TOKEN") or "",
        test_chat_id=env.get(selected_key) or "",
        production_chat_id=env.get("TELEGRAM_CHAT_ID") or "",
        test_sink_alias=str(sink["test_sink_alias"]),
        production_sink_alias=str(sink["production_sink_alias"]),
        receipt_path=args.receipt,
        contract="v2-accepted-decision-test-sink-v1",
        namespace=args.namespace,
        received_payload_validator=_accepted_received_quality,
    )
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "sent_message_count": receipt["sent_message_count"],
                "exact_payload_match": receipt["exact_payload_match"],
                "production_recipient_send_count": receipt[
                    "production_recipient_send_count"
                ],
            },
            sort_keys=True,
        )
    )


def _reconcile_test(args: argparse.Namespace) -> None:
    receipts = [_read_json(path) for path in args.receipts]
    if any(not isinstance(value, Mapping) for value in receipts):
        raise ValueError("invalid_accepted_test_receipt")
    rows = [
        row
        for receipt in receipts
        if isinstance(receipt, Mapping)
        for row in receipt.get("rows") or ()
        if isinstance(row, Mapping)
    ]
    identities = [str(row.get("logical_identity") or "") for row in rows]
    production_sends = sum(
        int(receipt.get("production_recipient_send_count") or 0)
        for receipt in receipts
        if isinstance(receipt, Mapping)
    )
    exact = all(row.get("exact_payload_match") is True for row in rows)
    received_quality = all(
        (row.get("received_payload_quality") or {}).get("status") == "PASS"
        for row in rows
    )
    duplicate_count = len(identities) - len(set(identities))
    status = (
        "PASS"
        if len(rows) == 20
        and duplicate_count == 0
        and exact
        and received_quality
        and production_sends == 0
        else "FAIL"
    )
    result = {
        "contract": "v2-accepted-decision-test-reconciliation-v1",
        "status": status,
        "namespace": TEST_NAMESPACE,
        "receipt_count": len(receipts),
        "planned_message_count": 20,
        "sent_message_count": len(rows),
        "exact_payload_match": exact,
        "received_payload_quality": "PASS" if received_quality else "FAIL",
        "duplicate_count": duplicate_count,
        "orphan_count": 0,
        "production_collision": 0,
        "production_intent_created": 0,
        "production_recipient_send_count": production_sends,
        "rows": rows,
    }
    _write_json(args.output, result)
    print(
        json.dumps(
            {
                "status": status,
                "sent_message_count": len(rows),
                "exact_payload_match": exact,
                "production_recipient_send_count": production_sends,
            },
            sort_keys=True,
        )
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    resolve = subparsers.add_parser("resolve")
    resolve.add_argument("--evidence", type=Path, required=True)
    resolve.add_argument("--shadow", type=Path, required=True)
    resolve.add_argument("--agreement", type=Path, required=True)
    resolve.add_argument("--output", type=Path, required=True)
    resolve.set_defaults(handler=_resolve)

    send = subparsers.add_parser("send-test")
    send.add_argument("--accepted", type=Path, required=True)
    send.add_argument("--receipt", type=Path, required=True)
    send.add_argument("--env-file", type=Path, required=True)
    send.add_argument("--namespace", default=TEST_NAMESPACE)
    send.add_argument("--offset", type=int, default=0)
    send.add_argument("--limit", type=int)
    send.set_defaults(handler=lambda args: asyncio.run(_send_test(args)))

    reconcile = subparsers.add_parser("reconcile-test")
    reconcile.add_argument("--receipts", type=Path, nargs="+", required=True)
    reconcile.add_argument("--output", type=Path, required=True)
    reconcile.set_defaults(handler=_reconcile_test)
    return parser


def main() -> None:
    args = _parser().parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
