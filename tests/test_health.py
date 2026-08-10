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
    monitor_schema = schema["paths"]["/monitoring-items"]["post"]["requestBody"][
        "content"
    ]["application/json"]["schema"]
    assert monitor_schema["type"] == "object"
    assert monitor_schema["required"] == ["ticker", "company_name", "core_thesis"]
    assert monitor_schema["properties"]["exchange"]["type"] == "string"
    assert "anyOf" not in monitor_schema["properties"]["exchange"]
    assert monitor_schema["properties"]["thesis_drivers"]["type"] == "array"
    assert monitor_schema["properties"]["validation_metrics"]["type"] == "array"
    price_rules = monitor_schema["properties"]["price_rules"]
    assert price_rules["properties"]["confirmation_price"]["type"] == "number"
    assert price_rules["properties"]["invalidation_price"]["type"] == "number"
    exposure = monitor_schema["properties"]["macro_exposures"]["items"]
    assert exposure["properties"]["condition"]["type"] == "string"
