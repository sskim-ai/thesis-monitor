import json
from datetime import date

import pytest
import httpx
from sqlmodel import Session

from app.database import engine, init_db
from app.models.financial import FinancialSnapshot
from app.models.security import SecurityMaster
from app.models.thesis import InvestmentThesis
from app.providers.filings import (
    OpenDARTProvider,
    _extract_financial_facts,
    _report_code_from_title,
)
from app.schemas.thesis import PriceContext, PricePeriodSummary, PriceRulesInput
from app.services.financial_validation import normalize_standalone_quarter
from app.services.thesis_evaluation_service import evaluate_thesis
from app.services.valuation_snapshot_service import ValuationSnapshotService


def _price(close: float) -> PriceContext:
    return PriceContext(
        available=True,
        periods={
            "daily": PricePeriodSummary(
                requested_count=500,
                actual_count=500,
                latest_date="2055-08-10",
                latest_close=close,
            )
        },
    )


def _thesis(ticker: str, method: str = "forward P/E") -> InvestmentThesis:
    return InvestmentThesis(
        ticker=ticker,
        version=1,
        core_thesis="반복 가능한 이익과 현금흐름을 확인한다.",
        valuation_framework=json.dumps({"primary_method": method}),
        market_expectations=json.dumps({"level": "balanced"}),
    )


def _verified_kr_security(ticker: str) -> SecurityMaster:
    return SecurityMaster(
        canonical_company_id=f"company:{ticker}",
        canonical_security_id=f"security:{ticker}:krx",
        ticker=ticker,
        exchange="KRX",
        country="KR",
        company_name=f"Fixture {ticker}",
        security_type="common_stock",
        issuer_type="krx",
        identity_quality="verified",
        identity_provider="fixture_identity",
    )


def _quarter(
    ticker: str,
    year: int,
    period_type: str,
    reported_month: int,
    *,
    revenue: float = 100,
    income: float = 10,
    eps: float | None = 1,
    equity: float | None = None,
    shares: float | None = 10,
    dividends: float | None = None,
    warning: bool = False,
) -> FinancialSnapshot:
    return FinancialSnapshot(
        ticker=ticker,
        period=f"{year}-{period_type}",
        period_type=period_type,
        fiscal_year=year,
        period_scope="single-quarter",
        reported_date=date(year, reported_month, 1),
        financials_as_of=date(year, reported_month, 1),
        provider="fixture",
        revenue=revenue,
        net_income=income,
        owners_parent_net_income=income,
        common_net_income=income,
        diluted_eps=eps,
        common_equity=equity,
        owners_parent_equity=equity,
        common_shares_outstanding=shares,
        diluted_shares=shares,
        dividends=dividends,
        financial_statement_basis_warning=warning,
    )


def test_h1_and_fy_cumulative_values_are_normalized_to_standalone_quarters() -> None:
    q2 = normalize_standalone_quarter(250, 100, "half-year")
    q4 = normalize_standalone_quarter(600, 430, "annual")

    assert q2.valid is True
    assert q2.value == 150
    assert q4.valid is True
    assert q4.value == 170


def test_cumulative_value_without_prior_period_is_not_guessed() -> None:
    result = normalize_standalone_quarter(250, None, "half-year")

    assert result.valid is False
    assert result.value is None
    assert result.method == "missing_prior_cumulative"


def test_opendart_q3_and_cumulative_amount_are_explicit() -> None:
    report_code = _report_code_from_title("분기보고서 (2054.09)")
    facts = _extract_financial_facts(
        [
            {
                "account_nm": "매출액",
                "account_id": "ifrs-full_Revenue",
                "fs_div": "CFS",
                "sj_div": "IS",
                "sj_nm": "연결 손익계산서",
                "thstrm_nm": "제3분기",
                "frmtrm_nm": "전기",
                "thstrm_amount": "150",
                "thstrm_add_amount": "430",
            }
        ],
        report_code or "",
    )

    assert report_code == "11014"
    assert any("financial fact: 매출액 = 150 KRW" in fact for fact in facts)
    assert any("financial cumulative fact: 매출액 = 430 KRW" in fact for fact in facts)
    assert any("period_scope=ytd" in fact for fact in facts)


@pytest.mark.anyio
async def test_opendart_common_share_status_is_structured() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "status": "000",
                "list": [
                    {
                        "se": "보통주",
                        "istc_totqy": "1000",
                        "tesstk_co": "100",
                        "distb_stock_co": "900",
                    }
                ],
            },
        )

    provider = OpenDARTProvider()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        facts, warnings = await provider._fetch_share_status_facts(
            client,
            "test",
            "00126380",
            "반기보고서 (2054.06)",
            date(2054, 8, 1),
        )

    assert warnings == []
    assert any("보통주유통주식수 = 900 shares" in fact for fact in facts)


@pytest.mark.anyio
async def test_derived_trailing_per_and_pbr_use_ttm_and_common_equity() -> None:
    init_db()
    ticker = "DRVPER"
    with Session(engine) as session:
        rows = [
            _quarter(ticker, 2054, "Q1", 3),
            _quarter(ticker, 2054, "H1", 6),
            _quarter(ticker, 2054, "Q3", 9),
            _quarter(ticker, 2054, "FY", 12, equity=1_000),
        ]
        session.add(_verified_kr_security(ticker))
        session.add_all(rows)
        session.commit()
        snapshot = await ValuationSnapshotService().fetch(
            ticker,
            "KRX",
            _price(100),
            session=session,
            thesis=_thesis(ticker),
        )

    assert snapshot.trailing_pe == 25
    assert snapshot.trailing_pe_source == "derived_trailing"
    assert snapshot.trailing_pe_method == "TTM diluted EPS"
    assert snapshot.price_to_book == 1
    assert snapshot.price_to_book_source == "derived_trailing"


@pytest.mark.anyio
async def test_negative_ttm_eps_is_rendered_as_not_meaningful() -> None:
    init_db()
    ticker = "NEGTTM"
    with Session(engine) as session:
        session.add(_verified_kr_security(ticker))
        for row in (
            _quarter(ticker, 2054, "Q1", 3, income=-5, eps=-0.5),
            _quarter(ticker, 2054, "H1", 6, income=-5, eps=-0.5),
            _quarter(ticker, 2054, "Q3", 9, income=-5, eps=-0.5),
            _quarter(ticker, 2054, "FY", 12, income=-5, eps=-0.5),
        ):
            session.add(row)
        session.commit()
        snapshot = await ValuationSnapshotService().fetch(
            ticker, "KRX", _price(10), session=session, thesis=_thesis(ticker)
        )

    assert snapshot.trailing_pe is None
    assert snapshot.trailing_pe_status == "not_meaningful"


@pytest.mark.anyio
async def test_internal_fy1_model_requires_eight_clean_quarters_and_is_labeled() -> None:
    init_db()
    ticker = "MODELFY1"
    periods = (("Q1", 3), ("H1", 6), ("Q3", 9), ("FY", 12))
    with Session(engine) as session:
        session.add(_verified_kr_security(ticker))
        for year in (2053, 2054):
            for period_type, month in periods:
                session.add(
                    _quarter(
                        ticker,
                        year,
                        period_type,
                        month,
                        equity=1_000 if period_type == "FY" else None,
                        dividends=2 if period_type == "FY" else None,
                    )
                )
        session.commit()
        snapshot = await ValuationSnapshotService().fetch(
            ticker, "KRX", _price(100), session=session, thesis=_thesis(ticker)
        )

    assert snapshot.forward_pe_status == "value"
    assert snapshot.forward_pe_source == "modeled_forward"
    assert snapshot.forward_basis == "FY1"
    assert snapshot.forward_price_to_book_status == "value"
    assert snapshot.forward_price_to_book_source == "modeled_forward"
    assert snapshot.forward_valuation_confidence < snapshot.trailing_valuation_confidence


@pytest.mark.anyio
async def test_low_quality_history_does_not_create_forward_values() -> None:
    init_db()
    ticker = "LOWMODEL"
    with Session(engine) as session:
        session.add(_verified_kr_security(ticker))
        session.add(_quarter(ticker, 2054, "FY", 12, equity=1_000, warning=True))
        session.commit()
        snapshot = await ValuationSnapshotService().fetch(
            ticker, "KRX", _price(100), session=session, thesis=_thesis(ticker)
        )

    assert snapshot.forward_pe_status == "unavailable"
    assert snapshot.forward_price_to_book_status == "unavailable"


@pytest.mark.anyio
async def test_sotp_company_does_not_receive_generic_forward_model() -> None:
    init_db()
    ticker = "SOTPNO"
    periods = (("Q1", 3), ("H1", 6), ("Q3", 9), ("FY", 12))
    with Session(engine) as session:
        session.add(_verified_kr_security(ticker))
        for year in (2053, 2054):
            for period_type, month in periods:
                session.add(
                    _quarter(
                        ticker,
                        year,
                        period_type,
                        month,
                        equity=1_000 if period_type == "FY" else None,
                    )
                )
        session.commit()
        snapshot = await ValuationSnapshotService().fetch(
            ticker,
            "KRX",
            _price(100),
            session=session,
            thesis=_thesis(ticker, "sum-of-the-parts"),
        )

    assert snapshot.trailing_pe_source == "derived_trailing"
    assert snapshot.forward_pe_source == "unavailable"
    assert snapshot.forward_price_to_book_source == "unavailable"


def test_price_state_below_support_and_above_confirmation_are_current_state() -> None:
    thesis = _thesis("PRICEINT")
    thesis.price_rules = PriceRulesInput(
        currency="USD",
        confirmation_price=110,
        support_zone_low=95,
        support_zone_high=100,
        warning_price=90,
        invalidation_price=80,
    ).model_dump_json(exclude_none=True)

    below = evaluate_thesis(thesis, [], _price(92))
    above = evaluate_thesis(thesis, [], _price(115))

    assert below.valuation_snapshot.current_price == 92
    assert "지지구간 아래" in below.new_buyer_price_view
    assert above.valuation_snapshot.current_price == 115
    assert "상향 확인 가격을 넘어서고 있습니다" in above.new_buyer_price_view
    assert "돌파 여부" not in above.new_buyer_price_view
    assert "가격 조정" not in above.new_buyer_price_view
    assert "지지 회복" not in above.new_buyer_price_view


def test_no_new_event_can_still_have_high_confidence() -> None:
    result = evaluate_thesis(_thesis("CONFHIGH"), [], _price(100))

    assert result.status == "no_material_change"
    assert result.confidence >= 0.70


def test_warning_state_has_stable_lifecycle_metadata() -> None:
    from app.models.event import Event

    thesis = _thesis("WARNMETA")
    thesis.weaken_signals = json.dumps(["margin guidance down"])
    event = Event(
        ticker="WARNMETA",
        date=date.today(),
        source="Company filing",
        provider="company_ir",
        title="Margin guidance down",
        url="https://example.com/warning",
        event_type="margin_deterioration",
        confirmed_facts=json.dumps(["Margin guidance down was confirmed"]),
        relevance_score=90,
    )

    result = evaluate_thesis(thesis, [event], _price(100))
    state = result.warning_states[0]

    assert state["warning_id"]
    assert state["ticker"] == "WARNMETA"
    assert state["status"] == "open"
    assert state["source_event_ids"]
