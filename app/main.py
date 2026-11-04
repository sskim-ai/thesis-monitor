from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import sys
import os

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
from app.services.runtime_maintenance import (
    RequestDrain, MaintenanceMiddleware, maintenance_enabled, startup_attestation,
)

maintenance_control = RequestDrain()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if maintenance_enabled() and os.environ.get("SCHEMA_VERIFIED_NO_MIGRATION_STARTUP") != "1":
        raise RuntimeError("maintenance_requires_schema_only_startup")
    schema = init_db()
    if maintenance_enabled():
        from app.services.kiwoom_global_lane import configured_lane
        from app.services import kiwoom_global_lane, runtime_maintenance
        from app.providers import kiwoom_rest_client
        app.state.maintenance_attestation = startup_attestation(
            [sys.modules[__name__], sys.modules["app.database"], runtime_maintenance,
             kiwoom_global_lane, kiwoom_rest_client], maintenance_control,
            lane=configured_lane(), schema=schema)
    try:
        yield
    finally:
        if maintenance_enabled():
            maintenance_control.drain()


app = FastAPI(
    title="Thesis Monitor API",
    version="0.1.0",
    description="Collects and normalizes thesis-relevant company events.",
    lifespan=lifespan,
)
app.add_middleware(MaintenanceMiddleware, control=maintenance_control)

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
