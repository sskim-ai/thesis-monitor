import json
from datetime import date

import pytest
from sqlmodel import Session, select

from app.database import engine, init_db
from app.models.event import Event
from app.models.thesis import MonitorRun, NotificationDelivery
from app.schemas.thesis import MonitoringItemCreate, PriceContext, PricePeriodSummary
from app.services.daily_monitor_service import run_daily_monitor
from app.services.monitoring_service import register_monitoring_item


class FakeCollectionService:
    async def collect_events(self, session: Session, ticker: str, lookback_days: int) -> list[Event]:
        event = Event(
            ticker=ticker,
            company_name="Test Company",
            date=date(2030, 1, 2),
            source="Company filing",
            provider="sec_edgar",
            title="Test Company confirms a new customer production order",
            url="https://example.com/test-production-order",
            event_type="production_order",
            confirmed_facts=json.dumps(["New customer production order was confirmed"]),
            inferred_implications=json.dumps(["Demand thesis may strengthen"]),
            unknowns="[]",
            requires_review=True,
            relevance_score=70,
            relevance_reason="production order",
        )
        session.add(event)
        session.commit()
        return [event]


class FakePriceClient:
    async def fetch_price_context(self, ticker: str) -> PriceContext:
        return PriceContext(
            available=True,
            periods={
                "daily": PricePeriodSummary(
                    requested_count=500,
                    actual_count=420,
                    latest_date="2030-01-02",
                    latest_close=120,
                    period_return_pct=20,
                    range_position_pct=60,
                ),
                "weekly": PricePeriodSummary(requested_count=300, actual_count=240),
                "monthly": PricePeriodSummary(requested_count=100, actual_count=84),
            },
        )


@pytest.mark.anyio
async def test_daily_monitor_assesses_and_queues_dry_run_notification() -> None:
    init_db()
    with Session(engine) as session:
        register_monitoring_item(
            session,
            MonitoringItemCreate(
                ticker="TST1",
                company_name="Test Company",
                core_thesis="New production customers support growth",
                strengthen_signals=["new customer production order"],
                weaken_signals=["customer loss"],
                invalidation_signals=["largest customer terminates all orders"],
            ),
        )
        result = await run_daily_monitor(
            session,
            run_date=date(2030, 1, 2),
            collection_service=FakeCollectionService(),
            price_client=FakePriceClient(),
        )

        monitor_run = session.exec(select(MonitorRun).where(MonitorRun.run_date == date(2030, 1, 2))).one()
        assert result.status == "success", monitor_run.details
        assert result.assessments[0].status == "strengthened"
        assert result.assessments[0].price_context.periods["daily"].actual_count == 420
        assert result.assessments[0].thesis_snapshot.supporting_evidence
        assert "현재 평가" in result.assessments[0].thesis_snapshot.current_thesis
        delivery = session.exec(
            select(NotificationDelivery).where(NotificationDelivery.ticker == "TST1")
        ).one()
        assert delivery.status == "dry_run"

        delivery.status = "pending"
        session.commit()
        retry_result = await run_daily_monitor(
            session,
            run_date=date(2030, 1, 2),
            collection_service=FakeCollectionService(),
            price_client=FakePriceClient(),
        )
        session.refresh(delivery)
        assert retry_result.status == "already_completed"
        assert delivery.status == "dry_run"
