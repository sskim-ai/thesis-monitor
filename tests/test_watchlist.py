from fastapi.testclient import TestClient

from app.main import app


def test_watchlist_registration_and_listing() -> None:
    with TestClient(app) as client:
        payload = {
            "ticker": "NVDA",
            "company_name": "NVIDIA",
            "exchange": "NASDAQ",
            "notes": "AI infrastructure thesis",
        }
        headers = {"X-Action-API-Key": "test-action-key"}
        response = client.post("/watchlist", json=payload, headers=headers)
        assert response.status_code == 200
        assert response.json()["ticker"] == "NVDA"

        response = client.get("/watchlist", headers=headers)
        assert response.status_code == 200
        items = response.json()
        assert any(item["ticker"] == "NVDA" for item in items)
