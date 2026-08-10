from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_health() -> None:
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_public_action_schema() -> None:
    with TestClient(app) as client:
        response = client.get("/action-openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["servers"] == [
        {"url": "https://sskim-macmini.tailb44bb1.ts.net/thesis"}
    ]
    assert "/thesis-events" in schema["paths"]
    assert "/admin/daily-monitor" not in schema["paths"]
    assert "facility_investment" in schema["components"]["schemas"]["EventType"]["enum"]
    assert "/action-openapi.json" not in schema["paths"]
    operation = schema["paths"]["/thesis-events"]["get"]
    assert "description" not in operation
    provider = next(
        parameter
        for parameter in operation["parameters"]
        if parameter["name"] == "provider"
    )
    assert provider["schema"]["type"] == "string"
    assert "anyOf" not in provider["schema"]
