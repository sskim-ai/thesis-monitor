import asyncio
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.api import routes_company
from app.main import app
from app.models.thesis import InvestmentThesis, NotificationDelivery, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.schemas.company import CompanyProfile
from app.schemas.thesis import (
    DataCoverage,
    HistoricalValuationStatistics,
    PriceContext,
    PriceDecisionContext,
    PricePeriodSummary,
    ValuationRelativePosition,
    ValuationSnapshot,
)
from app.services.ticker_analysis_snapshot_service import (
    TickerAnalysisSnapshotService,
)


def _session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def _price_context() -> PriceContext:
    return PriceContext(
        available=True,
        periods={
            "daily": PricePeriodSummary(
                requested_count=500,
                actual_count=250,
                latest_date="2026-08-11",
                latest_close=120.0,
                period_return_pct=20.0,
                range_position_pct=75.0,
            ),
            "weekly": PricePeriodSummary(
                requested_count=300,
                actual_count=100,
                latest_date="2026-08-07",
                latest_close=120.0,
                period_return_pct=35.0,
                range_position_pct=80.0,
            ),
        },
        decision=PriceDecisionContext(
            current_price=120.0,
            currency="USD",
            price_as_of="2026-08-11",
            market_session="closed",
        ),
    )


def _valuation_snapshot() -> ValuationSnapshot:
    return ValuationSnapshot(
        current_price=120.0,
        currency="USD",
        price_as_of="2026-08-11",
        valuation_data_as_of="2026-08-11",
        latest_earnings_period="2026-06-30",
        earnings_context_source="preliminary_earnings",
        earnings_context_is_preliminary=True,
        earnings_context_usable=True,
        eps_per_usable=True,
        latest_revenue=1_000.0,
        latest_operating_income=250.0,
        latest_operating_margin=25.0,
        latest_revenue_qoq=5.0,
        latest_operating_income_qoq=8.0,
        latest_revenue_yoy=12.0,
        latest_operating_income_yoy=18.0,
        ttm_eps=10.0,
        ttm_contains_preliminary=True,
        bvps=40.0,
        forward_eps=12.0,
        forward_bvps=None,
        trailing_pe=12.0,
        trailing_pe_status="value",
        price_to_book=3.0,
        price_to_book_status="value",
        forward_pe=10.0,
        forward_pe_status="value",
        forward_price_to_book=2.5,
        forward_price_to_book_status="value",
        quality="fresh",
        valuation_relative_position=ValuationRelativePosition.somewhat_premium,
        valuation_relative_position_confidence="medium",
        historical_pe_statistics=HistoricalValuationStatistics(
            metric="PER",
            current_value=12.0,
            historical_median=10.0,
            current_percentile=70.0,
            observation_count=150,
            lookback_years=4.5,
        ),
        historical_pb_statistics=HistoricalValuationStatistics(
            metric="PBR",
            current_value=3.0,
            historical_median=2.0,
            current_percentile=85.0,
            observation_count=150,
            lookback_years=4.5,
        ),
    )


class _Collection:
    async def get_company_profile(
        self, session: Session, ticker: str
    ) -> CompanyProfile:
        del session
        return CompanyProfile(
            ticker=ticker,
            company_name="Test Company",
            exchange="NASDAQ" if not ticker.isdigit() else "KRX",
        )


class _PriceClient:
    def __init__(self, context: PriceContext | None = None, *, fail: bool = False):
        self.context = context or _price_context()
        self.fail = fail

    async def fetch_price_context(
        self, ticker: str, *, session: Session
    ) -> PriceContext:
        del ticker, session
        if self.fail:
            raise RuntimeError("provider unavailable")
        return self.context


class _ValuationService:
    def __init__(
        self, snapshot: ValuationSnapshot | None = None, *, fail: bool = False
    ) -> None:
        self.snapshot = snapshot or _valuation_snapshot()
        self.fail = fail
        self.received_thesis = object()

    async def fetch(
        self,
        ticker: str,
        exchange: str,
        price_context: PriceContext,
        *,
        session: Session,
        thesis: InvestmentThesis | None,
    ) -> ValuationSnapshot:
        del ticker, exchange, price_context, session
        self.received_thesis = thesis
        if self.fail:
            raise RuntimeError("valuation unavailable")
        return self.snapshot


class _CoverageService:
    def __init__(self, coverage: DataCoverage | None = None) -> None:
        self.coverage = coverage or DataCoverage(
            price="fresh",
            price_quality="fresh",
            earnings="fresh",
            valuation="fresh",
            financial_freshness="current",
            full_financial_quality="current",
            preliminary_financial_quality="current",
            full_financial_freshness="current",
        )

    def build(
        self, session: Session, ticker: str, snapshot: ValuationSnapshot
    ) -> DataCoverage:
        del session, ticker, snapshot
        return self.coverage


def _service(
    *,
    price: _PriceClient | None = None,
    valuation: _ValuationService | None = None,
    coverage: _CoverageService | None = None,
) -> tuple[TickerAnalysisSnapshotService, _ValuationService]:
    valuation = valuation or _ValuationService()
    return (
        TickerAnalysisSnapshotService(
            collection_service=_Collection(),
            price_client=price or _PriceClient(),
            valuation_service=valuation,
            coverage_service=coverage or _CoverageService(),
        ),
        valuation,
    )


def test_unmonitored_ticker_returns_compact_formula_inputs_without_side_effects() -> None:
    session = _session()
    service, valuation_service = _service()
    models = (WatchlistItem, InvestmentThesis, ThesisAssessment, NotificationDelivery)
    before = [len(session.exec(select(model)).all()) for model in models]

    result = asyncio.run(service.fetch(session, "googl"))

    after = [len(session.exec(select(model)).all()) for model in models]
    assert before == after == [0, 0, 0, 0]
    assert valuation_service.received_thesis is None
    assert result.ticker == "GOOGL"
    assert result.exchange == "NASDAQ"
    assert result.price.current_price == 120.0
    assert result.price.periods["daily"].actual_count == 250
    assert result.earnings.latest_period == "2026-06-30"
    assert result.earnings.is_preliminary is True
    assert result.valuation.trailing_pe == pytest.approx(
        result.valuation.current_price / result.valuation.ttm_eps
    )
    assert result.valuation.price_to_book == pytest.approx(
        result.valuation.current_price / result.valuation.bvps
    )
    assert result.valuation.forward_pe == pytest.approx(
        result.valuation.current_price / result.valuation.forward_eps
    )
    assert result.valuation.historical_pe is not None
    assert result.valuation.historical_pe.median == 10.0

    payload = result.model_dump()
    forbidden = {
        "provider",
        "ttm_source_filings",
        "denominator_as_of",
        "multiple_basis_conflicts",
        "warnings",
        "observation_count",
        "raw_observations",
    }
    rendered_payload = str(payload)
    assert all(field not in rendered_payload for field in forbidden)


def test_registered_ticker_state_is_not_changed() -> None:
    session = _session()
    item = WatchlistItem(
        ticker="IBM",
        company_name="IBM",
        exchange="NYSE",
        latest_status="no_material_change",
        latest_assessment_date=date(2026, 8, 11),
    )
    thesis = InvestmentThesis(ticker="IBM", version=3, core_thesis="Existing thesis")
    session.add(item)
    session.add(thesis)
    session.commit()
    service, _ = _service()

    result = asyncio.run(service.fetch(session, "IBM"))

    session.refresh(item)
    session.refresh(thesis)
    assert result.ticker == "IBM"
    assert item.latest_status == "no_material_change"
    assert item.latest_assessment_date == date(2026, 8, 11)
    assert thesis.version == 3
    assert len(session.exec(select(ThesisAssessment)).all()) == 0
    assert len(session.exec(select(NotificationDelivery)).all()) == 0


def test_provider_only_forward_multiple_does_not_invent_denominator() -> None:
    snapshot = _valuation_snapshot().model_copy(
        update={"forward_pe": 19.3, "forward_eps": None}
    )
    service, _ = _service(valuation=_ValuationService(snapshot))

    result = asyncio.run(service.fetch(_session(), "IBM"))

    assert result.valuation.forward_pe == 19.3
    assert result.valuation.forward_eps is None


def test_eps_less_preliminary_keeps_earnings_context_without_inventing_per() -> None:
    snapshot = _valuation_snapshot().model_copy(
        update={
            "ttm_eps": None,
            "trailing_pe": None,
            "trailing_pe_status": "unavailable",
            "eps_per_usable": False,
        }
    )
    service, _ = _service(valuation=_ValuationService(snapshot))

    result = asyncio.run(service.fetch(_session(), "005930"))

    assert result.earnings.revenue == 1_000.0
    assert result.earnings.operating_margin == 25.0
    assert result.valuation.ttm_eps is None
    assert result.valuation.trailing_pe is None
    assert any("EPS 기준이 없어" in caution for caution in result.cautions)


def test_partial_provider_failures_return_available_components() -> None:
    price_service, _ = _service(price=_PriceClient(fail=True))
    price_result = asyncio.run(price_service.fetch(_session(), "MU"))
    assert price_result.price.available is False
    assert price_result.valuation.trailing_pe == 12.0
    assert any("가격 데이터를" in caution for caution in price_result.cautions)

    valuation_service, _ = _service(valuation=_ValuationService(fail=True))
    valuation_result = asyncio.run(valuation_service.fetch(_session(), "RXRX"))
    assert valuation_result.price.available is True
    assert valuation_result.valuation.trailing_pe is None
    assert any("Valuation 계산" in caution for caution in valuation_result.cautions)


def test_forward_reference_caution_is_compact_and_provider_neutral() -> None:
    snapshot = _valuation_snapshot().model_copy(
        update={
            "forward_pe_reference_caution": True,
            "forward_pe_reference_caution_reason": "provider horizon unknown",
        }
    )
    service, _ = _service(valuation=_ValuationService(snapshot))

    result = asyncio.run(service.fetch(_session(), "MU"))

    caution = next(item for item in result.cautions if "fPER" in item)
    assert "참고 수준" in caution
    assert "provider" not in caution.lower()


def test_ticker_analysis_snapshot_endpoint_returns_compact_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, _ = _service()
    monkeypatch.setattr(routes_company, "analysis_snapshot_service", service)

    with TestClient(app) as client:
        response = client.get("/ticker-analysis-snapshot", params={"ticker": "GOOGL"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "GOOGL"
    assert payload["valuation"]["ttm_eps"] == 10.0
    assert "provider" not in payload["valuation"]
    assert "warnings" not in payload["valuation"]


def test_ticker_analysis_snapshot_query_requires_nonempty_ticker() -> None:
    with TestClient(app) as client:
        response = client.get("/ticker-analysis-snapshot", params={"ticker": ""})

    assert response.status_code == 422
