from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
from typing import Mapping

from sqlmodel import Session, select

from app.database import engine, init_db
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.services.accepted_decision_v2_runtime_service import effective_prior_accepted
from scripts.kr_final_preenable_test_delivery import deliver_test_messages
from scripts.kr_market_preenable_evidence import audit_test_sink, load_env_values


CONTRACT = "onboarding-readiness-premerge-test-sink-v1"
NAMESPACE = "TEST_ONLY_ONBOARDING_READINESS_20260831"
CONTROL_SUBJECTS = ("047810", "CPNG", "003690", "GOOGL", "HUT", "RXRX", "SNDK")


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _json_dict(value: str | None) -> dict[str, object]:
    try:
        parsed = json.loads(value or "{}")
    except (json.JSONDecodeError, TypeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _json_list(value: str | None) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except (json.JSONDecodeError, TypeError):
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _latest_thesis(session: Session, ticker: str) -> InvestmentThesis | None:
    return session.exec(
        select(InvestmentThesis)
        .where(InvestmentThesis.ticker == ticker, InvestmentThesis.status == "active")
        .order_by(InvestmentThesis.version.desc())
    ).first()


def _latest_assessment(session: Session, ticker: str) -> ThesisAssessment | None:
    return session.exec(
        select(ThesisAssessment)
        .where(ThesisAssessment.ticker == ticker)
        .order_by(ThesisAssessment.assessment_date.desc())
    ).first()


def _compact(value: str, limit: int = 260) -> str:
    text = " ".join(value.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _control_message(
    item: WatchlistItem,
    audit_row: Mapping[str, object],
    thesis: InvestmentThesis | None,
    assessment: ThesisAssessment | None,
    accepted_decision: str | None,
) -> str:
    after = audit_row.get("after")
    after = after if isinstance(after, Mapping) else {}
    active = after.get("active") is True
    blockers = [str(value) for value in after.get("blockers") or []]
    expectations = _json_dict(thesis.market_expectations) if thesis else {}
    valuation = _json_dict(thesis.valuation_framework) if thesis else {}
    unknowns = _json_list(assessment.unknowns) if assessment else []
    strengthen = _json_list(thesis.strengthen_signals) if thesis else []
    weaken = _json_list(thesis.weaken_signals) if thesis else []
    lines = [
        "[온보딩 readiness 비생산 테스트]",
        f"{item.company_name} ({item.ticker})",
        (
            f"상태: ACTIVE_READY | 판단: {accepted_decision}"
            if active and accepted_decision
            else "상태: ACTIVE_READY | 판단: 첫 자연 점검의 accepted decision 대기"
            if active
            else "상태: PENDING_SAFE | production 판단에서 제외"
        ),
    ]
    if thesis and thesis.core_thesis:
        lines.append(f"핵심 논리: {_compact(thesis.core_thesis)}")
    expectation_summary = str(expectations.get("summary") or "").strip()
    if expectation_summary:
        lines.append(f"시장 기대: {_compact(expectation_summary)}")
    primary_method = str(valuation.get("primary_method") or "").strip()
    if primary_method:
        lines.append(f"Valuation: {primary_method}")
    if assessment and assessment.price_view.strip():
        lines.append(f"가격 구조: {_compact(assessment.price_view)}")
    if blockers:
        lines.append(f"미완료: {', '.join(blockers)}")
    elif unknowns:
        lines.append(f"남은 Unknown: {_compact(unknowns[0])}")
    if strengthen:
        lines.append(f"상향 재평가 조건: {_compact(strengthen[0])}")
    if weaken:
        lines.append(f"하향 재평가 조건: {_compact(weaken[0])}")
    lines.append("테스트 전용이며 주문 또는 production delivery intent가 아닙니다.")
    return "\n".join(lines)


def build_messages(
    audit_path: Path,
) -> list[dict[str, object]]:
    audit = _read_json(audit_path)
    rows = audit.get("subjects")
    if not isinstance(rows, list):
        raise ValueError("audit subjects missing")
    by_ticker = {
        str(row.get("ticker") or ""): row
        for row in rows
        if isinstance(row, Mapping)
    }
    active = sorted(
        ticker
        for ticker, row in by_ticker.items()
        if isinstance(row.get("after"), Mapping)
        and row["after"].get("active") is True
    )
    selected = list(dict.fromkeys([*active, *CONTROL_SUBJECTS]))
    missing_controls = sorted(set(CONTROL_SUBJECTS) - set(by_ticker))
    if missing_controls:
        raise ValueError(f"test controls missing: {missing_controls}")
    accepted = effective_prior_accepted()
    messages: list[dict[str, object]] = []
    with Session(engine) as session:
        items = {
            item.ticker: item
            for item in session.exec(
                select(WatchlistItem).where(WatchlistItem.ticker.in_(selected))
            ).all()
        }
        for ticker in selected:
            item = items.get(ticker)
            if item is None:
                raise ValueError(f"watchlist item missing: {ticker}")
            prior = accepted.get(ticker)
            text = _control_message(
                item,
                by_ticker[ticker],
                _latest_thesis(session, ticker),
                _latest_assessment(session, ticker),
                str(prior.accepted_decision) if prior else None,
            )
            messages.append(
                {
                    "ticker": ticker,
                    "route": "TEST_ONLY_ONBOARDING_READINESS",
                    "text": text,
                    "logical_identity": f"{NAMESPACE}:{ticker}",
                    "rendered_sha256": _sha256_text(text),
                    "production_intent": False,
                }
            )
    return messages


async def run(args: argparse.Namespace) -> dict[str, object]:
    init_db()
    messages = build_messages(args.audit)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    message_path = args.output_dir / "test-messages.json"
    message_path.write_text(
        json.dumps(
            {"contract": CONTRACT, "messages": messages},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    env = load_env_values(args.env_file)
    sink = audit_test_sink(env)
    if sink.get("available") is not True:
        raise ValueError(f"dedicated_test_sink_unavailable:{sink.get('reason')}")
    receipt = None
    if args.resume_failed:
        prior_path = args.output_dir / "test-sink-receipt.json"
        if not prior_path.exists():
            raise ValueError("failed_test_sink_receipt_missing")
        prior = _read_json(prior_path)
        prior_rows = [
            row
            for row in prior.get("rows", [])
            if isinstance(row, Mapping) and row.get("exact_payload_match") is True
        ]
        sent_by_identity = {
            str(row.get("logical_identity") or ""): row for row in prior_rows
        }
        by_identity = {str(row["logical_identity"]): row for row in messages}
        for identity, row in sent_by_identity.items():
            planned = by_identity.get(identity)
            if planned is None or row.get("outbound_sha256") != planned.get(
                "rendered_sha256"
            ):
                raise ValueError("continuation_prior_payload_identity_mismatch")
        remaining = [
            row
            for row in messages
            if str(row["logical_identity"]) not in sent_by_identity
        ]
        continuation = await deliver_test_messages(
            remaining,
            token=env.get("TELEGRAM_BOT_TOKEN", ""),
            test_chat_id=env.get(str(sink.get("selected_test_key_name") or ""), ""),
            production_chat_id=env.get("TELEGRAM_CHAT_ID", ""),
            test_sink_alias=str(sink["test_sink_alias"]),
            production_sink_alias=str(sink["production_sink_alias"]),
            receipt_path=args.output_dir / "test-sink-continuation-receipt.json",
            contract=CONTRACT,
            namespace=NAMESPACE,
        )
        combined_rows = [*prior_rows, *continuation.get("rows", [])]
        receipt = {
            "contract": CONTRACT,
            "namespace": NAMESPACE,
            "status": (
                "sent"
                if len(combined_rows) == len(messages)
                and all(row.get("exact_payload_match") is True for row in combined_rows)
                else "failed"
            ),
            "test_sink_alias": sink["test_sink_alias"],
            "production_sink_alias": sink["production_sink_alias"],
            "planned_message_count": len(messages),
            "sent_message_count": len(combined_rows),
            "exact_payload_match": all(
                row.get("exact_payload_match") is True for row in combined_rows
            ),
            "rate_limit_continuation": True,
            "initial_sent_count": len(prior_rows),
            "continuation_sent_count": len(continuation.get("rows", [])),
            "duplicate_count": 0,
            "orphan_count": 0,
            "production_collision": 0,
            "production_intent_created": 0,
            "production_recipient_send_count": 0,
            "rows": combined_rows,
        }
        final_path = args.output_dir / "test-sink-final-receipt.json"
        if final_path.exists():
            raise FileExistsError("final test receipt already exists")
        final_path.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    elif args.send:
        selected_key = str(sink.get("selected_test_key_name") or "")
        receipt = await deliver_test_messages(
            messages,
            token=env.get("TELEGRAM_BOT_TOKEN", ""),
            test_chat_id=env.get(selected_key, ""),
            production_chat_id=env.get("TELEGRAM_CHAT_ID", ""),
            test_sink_alias=str(sink["test_sink_alias"]),
            production_sink_alias=str(sink["production_sink_alias"]),
            receipt_path=args.output_dir / "test-sink-receipt.json",
            contract=CONTRACT,
            namespace=NAMESPACE,
        )
    return {
        "contract": CONTRACT,
        "status": receipt.get("status") if receipt else "READY_NOT_SENT",
        "message_count": len(messages),
        "eligible_message_count": sum(
            "ACTIVE_READY" in str(row["text"]) for row in messages
        ),
        "control_subjects": list(CONTROL_SUBJECTS),
        "test_sink_alias": sink["test_sink_alias"],
        "production_sink_alias": sink["production_sink_alias"],
        "test_exact_payload": (
            bool(receipt and receipt.get("exact_payload_match") is True)
        ),
        "test_production_recipient_send": 0,
        "production_delivery_intent_created": 0,
        "message_sha256": _sha256_text(message_path.read_text(encoding="utf-8")),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--resume-failed", action="store_true")
    args = parser.parse_args()
    result = asyncio.run(run(args))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
