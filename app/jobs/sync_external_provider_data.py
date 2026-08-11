import argparse
import asyncio
import json

from sqlmodel import Session, select

from app.database import engine, init_db
from app.models.watchlist import WatchlistItem
from app.providers.identity import OpenFigiProvider
from app.providers.policy import ProviderPolicyRegistry
from app.services.alpha_vantage_service import AlphaVantageService
from app.services.security_master_service import SecurityMasterService


async def run(*, use_openfigi: bool, use_alpha: bool) -> dict[str, object]:
    init_db()
    result: dict[str, object] = {
        "security_master": {},
        "openfigi": {},
        "alpha_vantage": {},
        "optional_providers": ProviderPolicyRegistry().optional_statuses(),
    }
    with Session(engine) as session:
        items = list(
            session.exec(
                select(WatchlistItem).where(WatchlistItem.active.is_(True))
            ).all()
        )
        securities = {}
        for item in items:
            security = SecurityMasterService().ensure(session, item.ticker)
            securities[item.ticker] = security
            result["security_master"][item.ticker] = security.identity_quality
        if use_openfigi:
            provider = OpenFigiProvider()
            for ticker in ("GOOGL", "TSM", "WRD", "005930"):
                security = securities.get(ticker)
                if security is None:
                    continue
                mapped, reason = await provider.enrich(session, security)
                result["openfigi"][ticker] = {
                    "mapped": mapped,
                    "reason": reason,
                }
        if use_alpha:
            provider = AlphaVantageService()
            for ticker in ("GOOGL", "IBM", "MU", "TSLA", "SNDK"):
                if ticker not in securities:
                    continue
                bundle = await provider.collect(
                    session,
                    ticker,
                    functions=(
                        "EARNINGS_ESTIMATES",
                        "SHARES_OUTSTANDING",
                        "DIVIDENDS",
                        "SPLITS",
                    ),
                )
                result["alpha_vantage"][ticker] = {
                    "statuses": bundle.statuses,
                    "warnings": bundle.warnings,
                }
        session.commit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--openfigi", action="store_true")
    parser.add_argument("--skip-alpha", action="store_true")
    args = parser.parse_args()
    asyncio.run(run(use_openfigi=args.openfigi, use_alpha=not args.skip_alpha))


if __name__ == "__main__":
    main()
