from fastapi.testclient import TestClient

from app.main import app


def test_provider_status_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/provider-status")

        assert response.status_code == 200
        data = response.json()
        names = {item["name"] for item in data}
        assert "mock" in names
        assert "naver_news" in names
        assert "opendart" in names
        assert all("configured" in item for item in data)
        assert all("required_settings" in item for item in data)


def test_provider_status_reports_setting_names_not_values() -> None:
    with TestClient(app) as client:
        response = client.get("/provider-status")

        assert response.status_code == 200
        data = response.json()
        naver = next(item for item in data if item["name"] == "naver_news")
        assert naver["required_settings"] == ["NAVER_CLIENT_ID", "NAVER_CLIENT_SECRET"]
        assert isinstance(naver["configured"], bool)
