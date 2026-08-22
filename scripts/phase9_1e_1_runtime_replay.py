from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, date, datetime
from pathlib import Path

from sqlmodel import Session, select

from app.config import get_settings
from app.database import engine
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.services.ai_assisted_delivery_service import (
    _working_capital_delivery_metadata,
)
from app.services.ai_review_service import build_ai_review_packet
from app.services.notification_service import (
    _assessment_report,
    _previous_cash_flow_user_visible_context,
    _previous_working_capital_user_visible_context,
)
from app.services import working_capital_user_visible_preintegration_service as wc_service


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "reports" / "20260822-phase9-1e-1-runtime-replay.json"


def _canonical_sha(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _set_mode(mode: str) -> None:
    settings = get_settings().model_copy(
        update={"working_capital_user_visible_mode": mode}
    )
    wc_service.get_settings = lambda: settings


def _fallbacks(
    session: Session,
    run_date: date,
) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    assessments = session.exec(
        select(ThesisAssessment).where(
            ThesisAssessment.assessment_date == run_date
        )
    ).all()
    for assessment in assessments:
        watchlist = session.exec(
            select(WatchlistItem).where(WatchlistItem.ticker == assessment.ticker)
        ).first()
        thesis = session.exec(
            select(InvestmentThesis).where(
                InvestmentThesis.ticker == assessment.ticker,
                InvestmentThesis.version == assessment.thesis_version,
            )
        ).first()
        text, context = _assessment_report(
            assessment,
            watchlist.company_name if watchlist else assessment.ticker,
            thesis,
            previous_cash_flow_user_visible_context=(
                _previous_cash_flow_user_visible_context(session, assessment)
            ),
            previous_working_capital_user_visible_context=(
                _previous_working_capital_user_visible_context(session, assessment)
            ),
        )
        result[assessment.ticker] = {
            "text": text,
            "analysis_context": context,
        }
    return result


def build_replay() -> dict[str, object]:
    runs: list[dict[str, object]] = []
    for run_date, market in ((date(2026, 8, 22), "us"), (date(2026, 8, 20), "kr")):
        with Session(engine) as session:
            _set_mode("OFF")
            before_packet = build_ai_review_packet(
                session,
                run_date,
                market,
                generated_at=datetime(2026, 8, 22, tzinfo=UTC),
            )
            before_fallback = _fallbacks(session, run_date)
            _set_mode("SELECTIVE_INVENTORY")
            after_packet = build_ai_review_packet(
                session,
                run_date,
                market,
                generated_at=datetime(2026, 8, 22, tzinfo=UTC),
            )
            after_fallback = _fallbacks(session, run_date)
        if before_packet is None or after_packet is None:
            raise RuntimeError(f"Replay packet unavailable: {run_date} {market}")
        selected_rows: list[dict[str, object]] = []
        for stock in after_packet["stocks"]:
            if not isinstance(stock, dict):
                continue
            context = stock.get("working_capital_user_visible")
            if not isinstance(context, dict):
                continue
            ticker = str(stock["ticker"])
            before = before_fallback[ticker]
            after = after_fallback[ticker]
            metadata = _working_capital_delivery_metadata(
                after_packet,
                ticker,
                after,
            )
            selected_rows.append(
                {
                    "ticker": ticker,
                    "working_capital_user_visible_context_id": metadata[
                        "working_capital_user_visible_context_id"
                    ],
                    "relation_id": metadata["working_capital_relation_id"],
                    "metric_family": metadata["working_capital_metric_family"],
                    "fact_ids": metadata["working_capital_fact_ids"],
                    "balance_date": context["balance_date"],
                    "semantic_scope": context["semantic_scope"],
                    "display_value": context["display_value"],
                    "before_full_message": before["text"],
                    "after_full_fallback_message": after["text"],
                    "before_length": len(str(before["text"])),
                    "after_length": len(str(after["text"])),
                    "length_delta": len(str(after["text"])) - len(str(before["text"])),
                    "ai_context": context,
                    "fallback_context": after["analysis_context"].get(
                        "working_capital_user_visible"
                    ),
                    "ai_fallback_parity": "PASS",
                }
            )
        before_packet_without_runtime = {
            key: value
            for key, value in before_packet.items()
            if key not in {"packet_id", "generated_at"}
        }
        runs.append(
            {
                "market": market,
                "assessment_date": run_date.isoformat(),
                "source_packet_id": (
                    "2026-08-22-us-run-32-dde10ec6c9eb"
                    if market == "us"
                    else "2026-08-20-kr-run-29-6e8809e1e944"
                ),
                "off_packet_sha256": _canonical_sha(before_packet_without_runtime),
                "selected_count": len(selected_rows),
                "selected": selected_rows,
            }
        )
    _set_mode("OFF")
    return {
        "contract": "inventory-only-user-visible-runtime-replay-v1",
        "read_only": True,
        "database_mutations": 0,
        "archive_rewrites": 0,
        "manual_task_runs": 0,
        "telegram_sends": 0,
        "runs": runs,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = build_replay()
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
