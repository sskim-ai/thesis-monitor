from fastapi.testclient import TestClient

from app.main import app


def test_mock_provider_returns_events() -> None:
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
    with TestClient(app) as client:
        response = client.get(
            "/thesis-events?ticker=NVDA&lookback_days=30&requires_review_only=true"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["events"]
        assert all(event["thesis_relevance"]["requires_review"] for event in data["events"])


def test_provider_filter() -> None:
    with TestClient(app) as client:
        response = client.get("/thesis-events?ticker=NVDA&lookback_days=30&provider=mock")

        assert response.status_code == 200
        data = response.json()
        assert data["events"]
        assert all(event["provider"] == "mock" for event in data["events"])


def test_earnings_checkpoints_response_shape() -> None:
    with TestClient(app) as client:
        response = client.get("/earnings-checkpoints?ticker=NVDA")

        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "NVDA"
        assert "Revenue growth vs guidance" in data["checkpoints"]


def test_company_profile_from_mock_provider() -> None:
    with TestClient(app) as client:
        response = client.get("/company-profile?ticker=AMD")

        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AMD"
        assert data["company_name"] == "Advanced Micro Devices"
