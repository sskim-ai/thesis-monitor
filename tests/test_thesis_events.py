from fastapi.testclient import TestClient

from app.main import app


def test_mock_provider_returns_events() -> None:
    with TestClient(app) as client:
        response = client.get("/thesis-events?ticker=NVDA&lookback_days=30")

        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "NVDA"
        assert data["events"]
        assert data["events"][0]["confirmed_facts"]
        assert "inferred_implications" in data["events"][0]
        assert "unknowns" in data["events"][0]
