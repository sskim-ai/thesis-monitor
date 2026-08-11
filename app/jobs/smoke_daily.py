import asyncio
import json
from collections import Counter
from datetime import date

from sqlmodel import Session

from app.database import engine, init_db
from app.services.daily_monitor_service import run_daily_monitor


async def _run() -> None:
    init_db()
    with Session(engine) as session:
        result = await run_daily_monitor(
            session,
            run_date=date.today(),
            force=True,
            queue_notifications=False,
            dispatch_notifications=False,
        )
    thesis_counts = Counter(item.business_thesis_change.value for item in result.assessments)
    valuation_counts = Counter(item.valuation_change.value for item in result.assessments)
    rows = [
        {
            "ticker": item.ticker,
            "business_thesis_change": item.business_thesis_change.value,
            "structural_risk_level": item.structural_risk_level.value,
            "confidence": item.confidence,
            "valuation_context": item.valuation_change.value,
            "valuation_relative_position": item.valuation_snapshot.valuation_relative_position.value,
            "valuation_relative_position_confidence": item.valuation_snapshot.valuation_relative_position_confidence,
            "valuation_relative_position_reason": item.valuation_snapshot.valuation_relative_position_reason,
            "price_state": item.price_context.decision.price_state,
            "market_session": item.market_session,
            "trailing_pe_source": item.valuation_snapshot.trailing_pe_source,
            "price_to_book_source": item.valuation_snapshot.price_to_book_source,
            "forward_pe_source": item.valuation_snapshot.forward_pe_source,
            "forward_price_to_book_source": item.valuation_snapshot.forward_price_to_book_source,
            "trailing_pe": item.valuation_snapshot.trailing_pe,
            "price_to_book": item.valuation_snapshot.price_to_book,
            "forward_pe": item.valuation_snapshot.forward_pe,
            "forward_price_to_book": item.valuation_snapshot.forward_price_to_book,
            "financial_period_end": item.valuation_snapshot.financial_period_end,
            "filing_date": item.valuation_snapshot.filing_date,
            "price_as_of": item.valuation_snapshot.price_as_of,
            "historical_pe_median": (
                item.valuation_snapshot.historical_pe_statistics.historical_median
                if item.valuation_snapshot.historical_pe_statistics else None
            ),
            "historical_pb_median": (
                item.valuation_snapshot.historical_pb_statistics.historical_median
                if item.valuation_snapshot.historical_pb_statistics else None
            ),
            "historical_pe_percentile": (
                item.valuation_snapshot.historical_pe_statistics.current_percentile
                if item.valuation_snapshot.historical_pe_statistics else None
            ),
            "historical_pb_percentile": (
                item.valuation_snapshot.historical_pb_statistics.current_percentile
                if item.valuation_snapshot.historical_pb_statistics else None
            ),
            "history_observation_count": max(
                item.valuation_snapshot.historical_pe_statistics.observation_count
                if item.valuation_snapshot.historical_pe_statistics else 0,
                item.valuation_snapshot.historical_pb_statistics.observation_count
                if item.valuation_snapshot.historical_pb_statistics else 0,
            ),
            "historical_comparability": item.valuation_snapshot.historical_comparability,
            "new_warnings_today": item.new_warnings,
            "open_confirmed_warnings": item.open_confirmed_warnings,
            "persistent_watch_risks": item.persistent_watch_risks,
            "new_buyer_price_view": item.new_buyer_price_view,
            "holder_price_view": item.holder_price_view,
            "valuation_quality": item.valuation_snapshot.quality,
        }
        for item in result.assessments
    ]
    print(
        json.dumps(
            {
                "status": result.status,
                "ticker_count": result.ticker_count,
                "success_count": result.success_count,
                "failure_count": result.failure_count,
                "thesis_distribution": thesis_counts,
                "valuation_distribution": valuation_counts,
                "tickers": rows,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(_run())
