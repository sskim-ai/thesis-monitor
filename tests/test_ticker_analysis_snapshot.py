import asyncio
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.api import routes_company
from app.main import app
from app.models.financial import FinancialSnapshot
from app.models.security import SecurityMaster
from app.models.thesis import InvestmentThesis, NotificationDelivery, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.schemas.company import CompanyProfile
from app.schemas.thesis import (
    DataCoverage,
    HistoricalValuationStatistics,
    InvestorSupplyContext,
    PriceContext,
    PriceDecisionContext,
    PricePeriodSummary,
    ValuationRelativePosition,
    ValuationSnapshot,
)
from app.services.ticker_analysis_snapshot_service import (
    TickerAnalysisSnapshotService,
)
from app.services.valuation_snapshot_service import ValuationSnapshotService


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


def _investor_supply_context() -> InvestorSupplyContext:
    return InvestorSupplyContext(
        available=True,
        as_of_date="2026-08-11",
        foreign_net_buy_qty=-153_000,
        institution_net_buy_qty=205_000,
        individual_net_buy_qty=0,
        foreign_net_buy_qty_5=-6_981_054,
        institution_net_buy_qty_5=-34_386,
        individual_net_buy_qty_5=5_829_492,
        foreign_net_buy_qty_20=-8_108_432,
        institution_net_buy_qty_20=-11_716_549,
        individual_net_buy_qty_20=18_403_424,
        foreign_holding_qty=2_724_356_859,
        foreign_holding_ratio=46.6,
        score=34,
        quality="distribution",
        quality_detail="foreign_holding_up_net_sell",
        primary_signal="foreign_exit_retail_absorption",
        foreign_flow_direction_20="selling",
        institution_flow_direction_20="selling",
        individual_flow_direction_20="buying",
        confidence="high",
        validation_status="validated",
        data_scope="daily_latest",
        investor_20d_validation_status="validated",
        investor_20d_diff_ratio=0.0,
        signals=["foreign_exit_retail_absorption"],
    )


def _valuation_snapshot() -> ValuationSnapshot:
    return ValuationSnapshot(
        current_price=120.0,
        currency="USD",
        financial_currency="USD",
        price_as_of="2026-08-11",
        valuation_data_as_of="2026-08-11",
        latest_earnings_period="2026-06-30",
        earnings_context_source="preliminary_earnings",
        earnings_context_is_preliminary=True,
        earnings_context_usable=True,
        latest_eps_usable=True,
        ttm_eps_usable=True,
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
    async def get_company_profile(self, session: Session, ticker: str) -> CompanyProfile:
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

    async def fetch_price_context(self, ticker: str, *, session: Session) -> PriceContext:
        del ticker, session
        if self.fail:
            raise RuntimeError("provider unavailable")
        return self.context


class _ValuationService:
    def __init__(self, snapshot: ValuationSnapshot | None = None, *, fail: bool = False) -> None:
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

    def build(self, session: Session, ticker: str, snapshot: ValuationSnapshot) -> DataCoverage:
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
    assert result.price.supply.available is False
    assert result.price.periods["daily"].actual_count == 250
    assert result.price.periods["daily"].window_return_pct == 20.0
    assert result.earnings.latest_period == "2026-06-30"
    assert result.earnings.is_preliminary is True
    assert result.earnings.financial_currency == "USD"
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


def test_unmonitored_korean_ticker_exposes_supply_without_side_effects() -> None:
    session = _session()
    supply = _investor_supply_context()
    price_context = _price_context().model_copy(
        update={
            "decision": _price_context().decision.model_copy(
                update={"currency": "KRW", "price_as_of": "2026-08-12"}
            ),
            "supply": supply,
        }
    )
    service, _ = _service(price=_PriceClient(price_context))
    models = (WatchlistItem, InvestmentThesis, ThesisAssessment, NotificationDelivery)
    before = [len(session.exec(select(model)).all()) for model in models]

    result = asyncio.run(service.fetch(session, "005930"))

    after = [len(session.exec(select(model)).all()) for model in models]
    assert before == after == [0, 0, 0, 0]
    assert result.price.price_as_of == "2026-08-12"
    assert result.price.supply.available is True
    assert result.price.supply.as_of_date == "2026-08-11"
    assert result.price.supply.foreign_net_buy_qty == -153_000
    assert result.price.supply.foreign_net_buy_qty_5 == -6_981_054
    assert result.price.supply.foreign_net_buy_qty_20 == -8_108_432
    assert result.price.supply.score == 34
    assert result.price.supply.primary_signal == "foreign_exit_retail_absorption"
    assert result.price.supply.confidence == "high"
    assert result.price.supply.validation_status == "validated"
    assert result.price.supply.data_scope == "daily_latest"
    assert result.price.supply.investor_20d_validation_status == "validated"
    assert result.price.supply.investor_20d_diff_ratio == 0.0
    assert result.price.supply.signals == ["foreign_exit_retail_absorption"]


def test_unsafe_adr_denominators_stay_null_with_compact_caution() -> None:
    snapshot = _valuation_snapshot().model_copy(
        update={
            "ttm_eps": None,
            "bvps": None,
            "forward_eps": None,
            "forward_bvps": None,
            "trailing_pe": 18.0,
            "trailing_pe_source": "provider",
            "earnings_context_source": "full_statement",
            "earnings_context_is_preliminary": False,
            "ttm_eps_usable": False,
            "eps_per_usable": False,
            "price_to_book": None,
            "forward_pe": 15.0,
            "forward_pe_source": "consensus_forward",
            "trailing_pe_basis_status": "currency_mismatch",
            "price_to_book_basis_status": "currency_mismatch",
            "forward_pe_basis_status": "insufficient_metadata",
            "valuation_calculation_warning": True,
        }
    )
    coverage = _CoverageService(
        DataCoverage(
            price="fresh",
            price_quality="fresh",
            earnings="fresh",
            valuation="partial",
            financial_freshness="current",
            reason_codes=["per_share_basis_insufficient"],
        )
    )
    service, _ = _service(
        valuation=_ValuationService(snapshot),
        coverage=coverage,
    )

    result = asyncio.run(service.fetch(_session(), "TSM"))

    assert result.valuation.ttm_eps is None
    assert result.valuation.bvps is None
    assert result.valuation.forward_eps is None
    assert result.valuation.trailing_pe == 18.0
    assert result.valuation.forward_pe == 15.0
    assert any("가격 통화" in caution for caution in result.cautions)
    payload = str(result.model_dump())
    assert "currency_mismatch" not in payload
    assert "per_share_basis_insufficient" not in payload


def test_unmonitored_adr_uses_security_master_and_skips_unsafe_history() -> None:
    session = _session()
    session.add(
        SecurityMaster(
            canonical_company_id="company:test-adr",
            canonical_security_id="security:test-adr:adr",
            ticker="TESTADR",
            company_name="Test ADR",
            exchange="NASDAQ",
            issuer_type="adr",
            security_type="Depositary Receipt",
        )
    )
    for index, period_end in enumerate(
        (
            date(2025, 9, 30),
            date(2025, 12, 31),
            date(2026, 3, 31),
            date(2026, 6, 30),
        ),
        start=1,
    ):
        session.add(
            FinancialSnapshot(
                ticker="TESTADR",
                period=f"2025-Q{index}",
                snapshot_type="full_statement",
                period_type=("Q3", "FY", "Q1", "H1")[index - 1],
                fiscal_year=period_end.year,
                financial_period_end=period_end,
                filing_date=date(2026, min(period_end.month + 1, 12), 20),
                reported_date=date(2026, min(period_end.month + 1, 12), 20),
                revenue=100,
                common_net_income=10,
                owners_parent_net_income=10,
                diluted_eps=float(index),
                common_equity=1_000,
                common_shares_outstanding=100,
                currency="TWD",
                provider="sec_companyfacts",
                raw_financial_fields='[{"field":"diluted_eps","currency":"TWD",'
                '"security_basis":"unknown"}]',
            )
        )
    session.commit()

    class _HistoryMustNotRun:
        def update_cache(self, *args: object, **kwargs: object) -> list[object]:
            raise AssertionError("unsafe ADR history must not be updated")

        def apply(self, *args: object, **kwargs: object) -> None:
            raise AssertionError("unsafe ADR history must not be applied")

    service = ValuationSnapshotService()
    service.settings = service.settings.model_copy(
        update={
            "finnhub_api_key": None,
            "alpha_vantage_api_key": None,
            "sec_user_agent": None,
        }
    )
    service.history_service = _HistoryMustNotRun()  # type: ignore[assignment]

    result = asyncio.run(
        service.fetch(
            "TESTADR",
            "NASDAQ",
            _price_context(),
            session=session,
            thesis=None,
        )
    )

    assert result.resolved_issuer_type == "adr"
    assert result.is_depositary_security is True
    assert result.raw_ttm_eps == 10
    assert result.ttm_eps is None
    assert result.trailing_pe is None
    assert result.bvps is None
    assert result.historical_pe_statistics is None
    assert result.historical_per_share_basis_status == (
        "historical_per_share_basis_unverified"
    )


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
    snapshot = _valuation_snapshot().model_copy(update={"forward_pe": 19.3, "forward_eps": None})
    service, _ = _service(valuation=_ValuationService(snapshot))

    result = asyncio.run(service.fetch(_session(), "IBM"))

    assert result.valuation.forward_pe == 19.3
    assert result.valuation.forward_eps is None


@pytest.mark.parametrize(
    ("ticker", "price_currency", "financial_currency"),
    [
        ("005930", "KRW", "KRW"),
        ("GOOGL", "USD", "USD"),
        ("TSM", "USD", "TWD"),
        ("UNKNOWN", "USD", None),
    ],
)
def test_financial_currency_comes_from_earnings_snapshot_not_price(
    ticker: str,
    price_currency: str,
    financial_currency: str | None,
) -> None:
    price_context = _price_context().model_copy(
        update={
            "decision": _price_context().decision.model_copy(update={"currency": price_currency})
        }
    )
    snapshot = _valuation_snapshot().model_copy(update={"financial_currency": financial_currency})
    service, _ = _service(
        price=_PriceClient(price_context),
        valuation=_ValuationService(snapshot),
    )

    result = asyncio.run(service.fetch(_session(), ticker))

    assert result.price.currency == price_currency
    assert result.earnings.financial_currency == financial_currency


def test_eps_less_preliminary_keeps_earnings_context_without_inventing_per() -> None:
    snapshot = _valuation_snapshot().model_copy(
        update={
            "ttm_eps": None,
            "trailing_pe": None,
            "trailing_pe_status": "unavailable",
            "latest_eps_usable": False,
            "ttm_eps_usable": False,
            "eps_per_usable": False,
        }
    )
    service, _ = _service(valuation=_ValuationService(snapshot))

    result = asyncio.run(service.fetch(_session(), "005930"))

    assert result.earnings.revenue == 1_000.0
    assert result.earnings.operating_margin == 25.0
    assert result.valuation.ttm_eps is None
    assert result.valuation.trailing_pe is None
    assert any("TTM EPS 자체 계산은 보류" in caution for caution in result.cautions)


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
    assert payload["earnings"]["financial_currency"] == "USD"
    assert payload["price"]["periods"]["daily"]["window_return_pct"] == 20.0
    assert payload["price"]["supply"]["available"] is False
    assert "period_return_pct" not in payload["price"]["periods"]["daily"]
    assert payload["valuation"]["ttm_eps"] == 10.0
    assert "provider" not in payload["valuation"]
    assert "warnings" not in payload["valuation"]


def test_ticker_analysis_snapshot_query_requires_nonempty_ticker() -> None:
    with TestClient(app) as client:
        response = client.get("/ticker-analysis-snapshot", params={"ticker": ""})

    assert response.status_code == 422
