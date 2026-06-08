from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api.routes_company import router as company_router
from app.api.routes_earnings import router as earnings_router
from app.api.routes_events import router as events_router
from app.api.routes_health import router as health_router
from app.api.routes_watchlist import router as watchlist_router
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(
    title="Thesis Monitor API",
    version="0.1.0",
    description=(
        "Collects and normalizes thesis-relevant company events for investment research. "
        "This API does not make buy or sell recommendations."
    ),
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(watchlist_router)
app.include_router(events_router)
app.include_router(company_router)
app.include_router(earnings_router)

