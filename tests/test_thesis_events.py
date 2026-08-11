import os
from datetime import date

os.environ["ENABLE_LIVE_PROVIDERS"] = "false"
os.environ["INCLUDE_MOCK_PROVIDER"] = "true"

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.api import routes_events
from app.config import get_settings
from app.database import engine
from app.models.event import Event
from app.providers.base import RawEvent
from app.providers.mock import MockProvider
from app.utils.tickers import normalize_ticker

get_settings.cache_clear()
routes_events.collection_service.providers = [MockProvider()]
routes_events.collection_service.profile_fallback_provider = MockProvider()

from app.main import app  # noqa: E402


def _force_mock_events() -> None:
    routes_events.collection_service.providers = [MockProvider()]
    routes_events.collection_service.profile_fallback_provider = MockProvider()


def test_mock_provider_returns_events() -> None:
    _force_mock_events()
    with TestClient(app) as client:
        response = client.get("/thesis-events?ticker=NVDA&lookback_days=30")

        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "NVDA"
        assert data["events"]
        assert data["events"][0]["provider"]
        assert data["events"][0]["confirmed_facts"]
        assert "inferred_implications" in data["events"][0]
        assert "unknowns" in data["events"][0]
        assert "capex_impact_known" in data["events"][0]["financial_impact"]
        assert "inventory_risk" in data["events"][0]["financial_impact"]
        assert "receivables_risk" in data["events"][0]["financial_impact"]


def test_requires_review_only_filter() -> None:
    _force_mock_events()
    with TestClient(app) as client:
        response = client.get(
            "/thesis-events?ticker=NVDA&lookback_days=30&requires_review_only=true"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["events"]
        assert all(event["thesis_relevance"]["requires_review"] for event in data["events"])


def test_provider_filter() -> None:
    _force_mock_events()
    with TestClient(app) as client:
        response = client.get("/thesis-events?ticker=NVDA&lookback_days=30&provider=mock")

        assert response.status_code == 200
        data = response.json()
        assert data["events"]
        assert all(event["provider"] == "mock" for event in data["events"])


def test_quarantined_document_identity_is_not_returned_by_action_api() -> None:
    previous_providers = routes_events.collection_service.providers
    routes_events.collection_service.providers = []
    try:
        with TestClient(app) as client:
            with Session(engine) as session:
                session.add(
                    Event(
                        ticker="QEVT",
                        company_name="Quarantine Test",
                        date=date.today(),
                        source="OpenDART",
                        provider="opendart",
                        title="Valid filing",
                        url="https://dart.example/valid",
                        event_type="financial_report",
                        document_identity_status="validated",
                        requires_review=True,
                    )
                )
                session.add(
                    Event(
                        ticker="QEVT",
                        company_name="Quarantine Test",
                        date=date.today(),
                        source="OpenDART",
                        provider="opendart",
                        title="Quarantined filing",
                        url="https://dart.example/invalid",
                        event_type="financial_report",
                        document_identity_status="invalid_mismatch",
                        requires_review=True,
                    )
                )
                session.commit()

            response = client.get(
                "/thesis-events?ticker=QEVT&lookback_days=30&requires_review_only=true"
            )
    finally:
        routes_events.collection_service.providers = previous_providers

    assert response.status_code == 200
    assert [event["title"] for event in response.json()["events"]] == ["Valid filing"]


class KoreanTickerProvider(MockProvider):
    async def fetch_events(self, ticker: str, lookback_days: int) -> list[RawEvent]:
        if ticker != "000660":
            return []
        return [
            RawEvent(
                ticker=ticker,
                company_name="SK하이닉스",
                date=date.today(),
                source="Mock Filing",
                provider=self.name,
                title="SK hynix notes inventory normalization in memory business",
                url="https://example.com/skhynix-inventory-normalization",
                summary="Management described inventory normalization in the memory segment.",
                keywords=["inventory normalization", "memory"],
                confirmed_facts=["Management described inventory normalization"],
                inferred_implications=["Inventory normalization may reduce pricing pressure"],
                unknowns=["Customer-level HBM demand", "Quarterly margin impact"],
            )
        ]


def test_korean_company_name_maps_to_canonical_ticker() -> None:
    routes_events.collection_service.providers = [KoreanTickerProvider()]
    routes_events.collection_service.profile_fallback_provider = MockProvider()
    with TestClient(app) as client:
        response = client.get("/thesis-events?ticker=SK하이닉스&lookback_days=30&provider=mock")

        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "000660"
        assert data["company_name"] == "SK하이닉스"
        assert data["events"]
        assert data["events"][0]["provider"] == "mock"


def test_supported_korean_watchlist_names_map_to_canonical_tickers() -> None:
    expected = {
        "코리안리": "003690",
        "HMM": "011200",
        "현대글로비스": "086280",
        "NAVER": "035420",
        "HD현대": "267250",
        "빅솔론": "093190",
        "팬오션": "028670",
        "지엔씨에너지": "119850",
        "제주반도체": "080220",
    }
    for company_name, ticker in expected.items():
        assert normalize_ticker(company_name) == ticker


def test_earnings_checkpoints_response_shape() -> None:
    _force_mock_events()
    with TestClient(app) as client:
        response = client.get("/earnings-checkpoints?ticker=NVDA")

        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "NVDA"
        assert "Revenue growth vs guidance" in data["checkpoints"]


def test_company_profile_from_mock_provider() -> None:
    _force_mock_events()
    with TestClient(app) as client:
        response = client.get("/company-profile?ticker=AMD")

        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AMD"
        assert data["company_name"] == "Advanced Micro Devices"



def test_korean_samsung_ticker_alias() -> None:
    _force_mock_events()
    with TestClient(app) as client:
        response = client.get("/company-profile?ticker=삼성전자")

        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "005930"
        assert data["company_name"] == "삼성전자"
