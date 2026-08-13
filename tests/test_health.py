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
    assert schema["info"]["version"] == "0.4.5"

    operation_ids = [
        operation["operationId"]
        for path_item in schema["paths"].values()
        for operation in path_item.values()
        if isinstance(operation, dict) and "operationId" in operation
    ]
    assert len(operation_ids) == 20
    assert len(operation_ids) == len(set(operation_ids))

    price_period = schema["components"]["schemas"]["AnalysisPricePeriod"][
        "properties"
    ]
    assert "window_return_pct" in price_period
    assert "period_return_pct" not in price_period
    earnings = schema["components"]["schemas"]["AnalysisEarningsSnapshot"][
        "properties"
    ]
    assert "financial_currency" in earnings
    supply = schema["components"]["schemas"]["InvestorSupplyContext"]["properties"]
    assert "foreign_net_buy_qty_20" in supply
    assert "primary_signal" in supply
    analysis_supply = schema["components"]["schemas"]["AnalysisPriceSnapshot"][
        "properties"
    ]["supply"]
    assert analysis_supply["$ref"] == "#/components/schemas/InvestorSupplyContext"


def test_custom_gpt_docs_reference_analysis_snapshot_action() -> None:
    operation_id = "getTickerAnalysisSnapshot"
    for relative_path in (
        "docs/custom_gpt_instructions_ko.md",
        "docs/custom_gpt_regression_prompts.md",
    ):
        assert operation_id in Path(relative_path).read_text(encoding="utf-8")


def test_custom_gpt_instructions_fit_product_limit_and_preserve_initial_analysis() -> None:
    text = Path("docs/custom_gpt_instructions_ko.md").read_text(encoding="utf-8")

    assert len(text) <= 8_000
    for concept in (
        "Mode A",
        "Initial Thesis Analysis",
        "getCompanyProfile",
        "getEarningsCheckpoints",
        "getThesisEvents",
        "getTickerAnalysisSnapshot",
        "monitorStock",
        "Kill Condition",
        "수급",
    ):
        assert concept in text
    for knowledge_reference in ("Knowledge", "Initial Analysis", "Valuation", "수급"):
        assert knowledge_reference in text


def test_custom_gpt_knowledge_and_runtime_policy_keep_separate_responsibilities() -> None:
    text = Path("docs/custom_gpt_knowledge_ko.md").read_text(encoding="utf-8")

    for concept in (
        "Fact / Interpretation / Unknown",
        "Earnings Quality",
        "시장 기대",
        "업종별 Valuation",
        "수급",
        "Kill Condition",
        "Macro",
        "잠정실적",
        "ADR",
    ):
        assert concept in text

    policy = Path(
        ".agents/skills/thesis-monitor-daily-review/references/daily-review-policy.md"
    ).read_text(encoding="utf-8")
    for concept in (
        "KRX morning gate",
        "price.supply.score",
        "07:50",
        "16:05",
    ):
        assert concept in policy


def test_generated_action_schema_files_match() -> None:
    rendered = {
        Path(relative_path).read_text(encoding="utf-8")
        for relative_path in (
            "openapi.action.json",
            "docs/custom_gpt_action_schema.yaml",
            "docs/custom_gpt_action_schema_v2.yaml",
        )
    }

    assert len(rendered) == 1


def test_custom_gpt_regressions_cover_initial_supply_and_mode_separation() -> None:
    text = Path("docs/custom_gpt_regression_prompts.md").read_text(encoding="utf-8")

    for scenario in (
        "005930",
        "005930 분석해줘",
        "005930 오늘 점검해줘",
        "005930 분석하고 앞으로 모니터링해줘",
        "GOOGL",
        "Korean Initial Analysis With Supply",
        "foreign_exit_retail_absorption",
    ):
        assert scenario in text
