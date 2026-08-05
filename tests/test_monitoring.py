from fastapi.testclient import TestClient

from app.main import app

AUTH_HEADERS = {"X-Action-API-Key": "test-action-key"}


def _payload(core_thesis: str = "AI infrastructure demand supports earnings growth") -> dict:
    return {
        "ticker": "SK하이닉스",
        "company_name": "SK하이닉스",
        "exchange": "KRX",
        "core_thesis": core_thesis,
        "time_horizon": "2-3 years",
        "strengthen_signals": ["HBM customer expansion"],
        "weaken_signals": ["HBM market share decline"],
        "invalidation_signals": ["major HBM customer loss"],
    }


def test_monitoring_item_registration_versions_and_deactivation() -> None:
    with TestClient(app) as client:
        response = client.post("/monitoring-items", json=_payload(), headers=AUTH_HEADERS)
        assert response.status_code == 200
        assert response.json()["ticker"] == "000660"
        assert response.json()["thesis"]["version"] == 1

        response = client.post("/monitoring-items", json=_payload(), headers=AUTH_HEADERS)
        assert response.status_code == 200
        assert response.json()["thesis"]["version"] == 1

        response = client.post(
            "/monitoring-items",
            json=_payload("HBM leadership expands margins"),
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        assert response.json()["thesis"]["version"] == 2

        response = client.get("/monitoring-items/000660", headers=AUTH_HEADERS)
        assert response.status_code == 200
        assert response.json()["thesis"]["core_thesis"] == "HBM leadership expands margins"

        response = client.post("/monitoring-items/000660/deactivate", headers=AUTH_HEADERS)
        assert response.status_code == 200
        assert response.json()["active"] is False


def test_monitoring_routes_require_api_key() -> None:
    with TestClient(app) as client:
        response = client.get("/monitoring-items")

    assert response.status_code == 401
