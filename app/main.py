from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes_action_schema import router as action_schema_router
from app.api.routes_admin import router as admin_router
from app.api.routes_company import router as company_router
from app.api.routes_earnings import router as earnings_router
from app.api.routes_events import router as events_router
from app.api.routes_health import router as health_router
from app.api.routes_macro import router as macro_router
from app.api.routes_monitoring import router as monitoring_router
from app.api.routes_provider import router as provider_router
from app.api.routes_watchlist import router as watchlist_router
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(
    title="Thesis Monitor API",
    version="0.1.0",
    description="Collects and normalizes thesis-relevant company events.",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(action_schema_router)
app.include_router(provider_router)
app.include_router(watchlist_router)
app.include_router(monitoring_router)
app.include_router(macro_router)
app.include_router(events_router)
app.include_router(company_router)
app.include_router(earnings_router)
app.include_router(admin_router)
