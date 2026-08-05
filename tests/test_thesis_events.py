import os
from datetime import date

os.environ["ENABLE_LIVE_PROVIDERS"] = "false"
os.environ["INCLUDE_MOCK_PROVIDER"] = "true"

from fastapi.testclient import TestClient

from app.api import routes_events
from app.config import get_settings
from app.providers.base import RawEvent
from app.providers.mock import MockProvider

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
