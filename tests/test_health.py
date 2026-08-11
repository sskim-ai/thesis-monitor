from pathlib import Path

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
    assert "/monitoring-items/summaries" in schema["paths"]
    assert (
        schema["paths"]["/monitoring-items/summaries"]["get"]["operationId"]
        == "listMonitoredStockSummaries"
    )
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
    expectations = monitor_schema["properties"]["market_expectations"]
    assert expectations["properties"]["level"]["type"] == "string"
    valuation = monitor_schema["properties"]["valuation_framework"]
    assert valuation["properties"]["primary_method"]["type"] == "string"
    assert monitor_schema["properties"]["multiple_expansion_signals"]["type"] == "array"
    price_rules = monitor_schema["properties"]["price_rules"]
    assert price_rules["properties"]["confirmation_price"]["type"] == "number"
    assert price_rules["properties"]["invalidation_price"]["type"] == "number"
    exposure = monitor_schema["properties"]["macro_exposures"]["items"]
    assert exposure["properties"]["condition"]["type"] == "string"
    assessment_path = schema["paths"]["/monitoring-items/{ticker}/assessments"]
    assert assessment_path["post"]["operationId"] == "recordThesisAssessment"
    assessment_schema = assessment_path["post"]["requestBody"]["content"][
        "application/json"
    ]["schema"]
    assert assessment_schema["type"] == "object"
    assert assessment_schema["properties"]["valuation_context"]["type"] == "string"


def test_public_action_schema_includes_read_only_ticker_analysis_snapshot() -> None:
    with TestClient(app) as client:
        response = client.get("/action-openapi.json")

    assert response.status_code == 200
    schema = response.json()
    operation = schema["paths"]["/ticker-analysis-snapshot"]["get"]
    assert operation["operationId"] == "getTickerAnalysisSnapshot"
    assert schema["info"]["version"] == "0.4.0"

    operation_ids = [
        operation["operationId"]
        for path_item in schema["paths"].values()
        for operation in path_item.values()
        if isinstance(operation, dict) and "operationId" in operation
    ]
    assert len(operation_ids) == 20
    assert len(operation_ids) == len(set(operation_ids))


def test_custom_gpt_docs_reference_analysis_snapshot_action() -> None:
    operation_id = "getTickerAnalysisSnapshot"
    for relative_path in (
        "docs/custom_gpt_instructions_ko.md",
        "docs/custom_gpt_knowledge_ko.md",
        "docs/custom_gpt_regression_prompts.md",
    ):
        assert operation_id in Path(relative_path).read_text(encoding="utf-8")
