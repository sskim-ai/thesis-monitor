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
            "price_state": item.price_context.decision.price_state,
            "market_session": item.market_session,
            "trailing_pe_source": item.valuation_snapshot.trailing_pe_source,
            "price_to_book_source": item.valuation_snapshot.price_to_book_source,
            "forward_pe_source": item.valuation_snapshot.forward_pe_source,
            "forward_price_to_book_source": item.valuation_snapshot.forward_price_to_book_source,
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
