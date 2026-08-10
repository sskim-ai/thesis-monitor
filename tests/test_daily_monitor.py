import json
from datetime import date

import pytest
from sqlmodel import Session, select

from app.database import engine, init_db
from app.models.event import Event
from app.models.thesis import MonitorRun, NotificationDelivery
from app.models.watchlist import WatchlistItem
from app.schemas.thesis import (
    MonitoringItemCreate,
    PriceContext,
    PricePeriodSummary,
    PriceRulesInput,
)
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


class EmptyCollectionService:
    async def collect_events(self, session: Session, ticker: str, lookback_days: int) -> list[Event]:
        return []


class RulePriceClient:
    def __init__(self, previous_close: float, latest_close: float) -> None:
        self.previous_close = previous_close
        self.latest_close = latest_close

    async def fetch_price_context(self, ticker: str) -> PriceContext:
        return PriceContext(
            available=True,
            periods={
                "daily": PricePeriodSummary(
                    requested_count=500,
                    actual_count=500,
                    latest_date="2030-01-03",
                    previous_close=self.previous_close,
                    latest_close=self.latest_close,
                    latest_high=max(self.previous_close, self.latest_close),
                    latest_low=min(self.previous_close, self.latest_close),
                    range_position_pct=60,
                )
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
                market_expectations={
                    "level": "elevated",
                    "summary": "A new customer ramp is partly reflected",
                },
                valuation_framework={"primary_method": "forward P/E"},
                multiple_expansion_signals=["new customer production order"],
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
        assessment = next(item for item in result.assessments if item.ticker == "TST1")
        assert assessment.status == "strengthened"
        assert assessment.price_context.periods["daily"].actual_count == 420
        assert assessment.thesis_snapshot.supporting_evidence
        assert assessment.valuation_context.impact == "expansion"
        assert assessment.thesis_snapshot.valuation_context.impact == "expansion"
        assert "현재 평가" in assessment.thesis_snapshot.current_thesis
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


@pytest.mark.anyio
async def test_daily_monitor_uses_structured_price_rules() -> None:
    init_db()
    with Session(engine) as session:
        register_monitoring_item(
            session,
            MonitoringItemCreate(
                ticker="PRC1",
                company_name="Price Rule Company",
                core_thesis="Price confirmation supports the operating thesis",
                price_rules=PriceRulesInput(
                    currency="USD",
                    confirmation_price=100,
                    support_zone_low=90,
                    support_zone_high=95,
                    warning_price=88,
                    invalidation_price=80,
                ),
            ),
        )
        result = await run_daily_monitor(
            session,
            run_date=date(2030, 1, 3),
            collection_service=EmptyCollectionService(),
            price_client=RulePriceClient(previous_close=99, latest_close=101),
        )

        assessment = next(item for item in result.assessments if item.ticker == "PRC1")
        assert assessment.status == "no_material_change"
        assert assessment.price_context.rule_evaluation.status == "confirmation_triggered"
        assert "상향 돌파" in assessment.price_view
        assert any(item["provider"] == "ohlcv-analyst" for item in assessment.evidence)


@pytest.mark.anyio
async def test_price_invalidation_deactivates_monitoring_item() -> None:
    init_db()
    with Session(engine) as session:
        register_monitoring_item(
            session,
            MonitoringItemCreate(
                ticker="PRC2",
                company_name="Invalidated Price Company",
                core_thesis="The thesis requires the structural price floor to hold",
                price_rules=PriceRulesInput(
                    currency="USD",
                    warning_price=95,
                    invalidation_price=90,
                ),
            ),
        )
        result = await run_daily_monitor(
            session,
            run_date=date(2030, 1, 4),
            collection_service=EmptyCollectionService(),
            price_client=RulePriceClient(previous_close=96, latest_close=89),
        )

        assessment = next(item for item in result.assessments if item.ticker == "PRC2")
        assert assessment.status == "invalidated"
        item = session.exec(select(WatchlistItem).where(WatchlistItem.ticker == "PRC2")).one()
        assert item.active is False
