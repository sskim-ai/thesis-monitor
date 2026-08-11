import argparse
import asyncio
import json

from sqlmodel import Session

from app.database import engine, init_db
from app.services.financial_backfill_service import backfill_financial_snapshots


async def _run(tickers: list[str], years: int) -> None:
    init_db()
    results: list[dict[str, object]] = []
    with Session(engine) as session:
        for ticker in tickers:
            result = await backfill_financial_snapshots(session, ticker, years=years)
            results.append(
                {
                    "ticker": result.ticker,
                    "report_count": result.report_count,
                    "backfilled_count": result.backfilled_count,
                    "skipped_count": result.skipped_count,
                    "warning_count": len(result.warnings),
                }
            )
    print(json.dumps(results, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill normalized OpenDART financial snapshots.")
    parser.add_argument("tickers", nargs="+", help="KRX ticker codes")
    parser.add_argument("--years", type=int, default=5)
    args = parser.parse_args()
    asyncio.run(_run(args.tickers, args.years))


if __name__ == "__main__":
    main()
