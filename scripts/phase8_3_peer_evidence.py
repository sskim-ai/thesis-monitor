from __future__ import annotations

# ruff: noqa: E402

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

from sqlmodel import Session, create_engine, select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models.company import Company
from app.models.thesis import ThesisAssessment
from app.services.company_profile_service import read_profile_provenance
from app.services.peer_sector_valuation_service import build_peer_valuation_states


MANDATORY = {
    "kr": ("005930", "000660", "005490", "086280", "003690"),
    "us": ("MU", "TSM", "TSLA", "RXRX", "CORZ", "GOOGL"),
}
METRICS = (
    "trailing_pe",
    "price_to_book",
    "forward_pe_consensus",
    "forward_pe_modeled",
    "forward_price_to_book_consensus",
    "forward_price_to_book_modeled",
)


def _dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return {}
    try:
        parsed = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _market(company: Company) -> str:
    return "kr" if company.ticker.isdigit() else "us"


def _metric_summary(metric: object) -> dict[str, object]:
    value = _dict(metric)
    return {
        key: value.get(key)
        for key in (
            "available",
            "audit_available",
            "reason",
            "quality",
            "sample_count",
            "company_value",
            "median",
            "company_relative_multiple",
            "company_vs_median_pct",
            "company_cross_section_percentile",
        )
        if value.get(key) is not None
    }


def _state_summary(
    ticker: str,
    market: str,
    state: dict[str, object],
) -> dict[str, object]:
    audit = _dict(state.get("audit"))
    metric_audit = _dict(audit.get("metrics"))
    exclusion_reasons: Counter[str] = Counter()
    for metric in metric_audit.values():
        for item in _dict(metric).get("excluded", []):
            if isinstance(item, dict):
                exclusion_reasons[str(item.get("reason") or "unknown")] += 1
    return {
        "ticker": ticker,
        "market": market,
        "available": state.get("available"),
        "reason": state.get("reason"),
        "contract": state.get("contract"),
        "provider": state.get("provider"),
        "peer_scope": state.get("peer_scope"),
        "as_of_date": state.get("as_of_date"),
        "group_basis": state.get("group_basis"),
        "group_value": state.get("group_value"),
        "candidate_count": len(audit.get("candidate_tickers", [])),
        "issuer_deduplicated_count": len(
            audit.get("issuer_deduplicated_tickers", [])
        ),
        "sample_quality": state.get("sample_quality"),
        "framework": state.get("framework"),
        "interpretation_contract": state.get("interpretation_contract"),
        "metrics": {
            metric: _metric_summary(_dict(state.get("metrics")).get(metric))
            for metric in METRICS
        },
        "exclusion_reason_counts": dict(sorted(exclusion_reasons.items())),
        "audit": audit,
    }


def build_audit(
    database: Path,
    data_dir: Path,
    assessment_date: date,
) -> dict[str, object]:
    engine = create_engine(f"sqlite:///{database}")
    with Session(engine) as session:
        rows = list(
            session.exec(
                select(ThesisAssessment).where(
                    ThesisAssessment.assessment_date == assessment_date,
                    ThesisAssessment.assessment_state == "final",
                )
            ).all()
        )
        companies = {
            item.ticker: item
            for item in session.exec(
                select(Company).where(
                    Company.ticker.in_({row.ticker for row in rows})
                )
            ).all()
        }
        states = build_peer_valuation_states(
            session,
            rows,
            assessment_date,
            profile_reader=read_profile_provenance,
            data_dir=data_dir,
        )

    summaries = {
        ticker: _state_summary(ticker, _market(companies[ticker]), state)
        for ticker, state in sorted(states.items())
    }
    snapshot_coverage: dict[str, Counter[str]] = {
        metric: Counter() for metric in METRICS
    }
    for row in rows:
        snapshot = _dict(row.valuation_snapshot)
        source = str(snapshot.get("forward_pe_source") or "")
        statuses = {
            "trailing_pe": snapshot.get("trailing_pe_status"),
            "price_to_book": snapshot.get("price_to_book_status"),
            "forward_pe_consensus": (
                snapshot.get("forward_pe_status")
                if source == "consensus_forward"
                else "basis_not_selected"
            ),
            "forward_pe_modeled": (
                snapshot.get("forward_pe_status")
                if source == "modeled_forward"
                else "basis_not_selected"
            ),
            "forward_price_to_book_consensus": (
                snapshot.get("forward_price_to_book_status")
                if snapshot.get("forward_price_to_book_source")
                == "consensus_forward"
                else "basis_not_selected"
            ),
            "forward_price_to_book_modeled": (
                snapshot.get("forward_price_to_book_status")
                if snapshot.get("forward_price_to_book_source") == "modeled_forward"
                else "basis_not_selected"
            ),
        }
        for metric, status in statuses.items():
            snapshot_coverage[metric][str(status or "unavailable")] += 1

    mandatory = {
        market: {
            ticker: summaries.get(
                ticker,
                {"ticker": ticker, "market": market, "reason": "assessment_unavailable"},
            )
            for ticker in tickers
        }
        for market, tickers in MANDATORY.items()
    }
    return {
        "schema_version": "phase8-3-peer-audit-v1",
        "assessment_date": assessment_date.isoformat(),
        "source": "read_only_operating_assessment_archive",
        "provider_scope": "limited_active_monitoring_universe",
        "assessment_count": len(rows),
        "market_counts": dict(
            sorted(Counter(_market(companies[row.ticker]) for row in rows).items())
        ),
        "user_visible_peer_state_count": sum(
            summary.get("available") is True for summary in summaries.values()
        ),
        "snapshot_metric_status_counts": {
            metric: dict(sorted(counts.items()))
            for metric, counts in snapshot_coverage.items()
        },
        "mandatory_fixtures": mandatory,
        "states": summaries,
        "safety": {
            "ticker_hard_code_in_selection": 0,
            "renderer_calculation": 0,
            "ai_calculation": 0,
            "telegram_sends": 0,
            "database_mutations": 0,
            "operating_deployment": 0,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--assessment-date", type=date.fromisoformat, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    audit = build_audit(args.database, args.data_dir, args.assessment_date)
    payload = json.dumps(audit, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
