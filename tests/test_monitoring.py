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
        "thesis_drivers": ["HBM leadership", "AI server demand"],
        "validation_metrics": ["HBM revenue growth", "Free cash flow"],
        "market_expectations": {
            "as_of_date": "2030-01-01",
            "level": "very_high",
            "summary": "Strong HBM growth is already expected",
            "priced_in": ["HBM leadership"],
            "upside_surprises": ["FCF exceeds consensus"],
            "downside_surprises": ["HBM margin misses consensus"],
            "evidence_basis": ["stored operating thesis"],
        },
        "valuation_framework": {
            "primary_method": "cycle-adjusted forward P/E",
            "secondary_methods": ["EV/EBITDA"],
            "rationale": "Memory earnings require cycle normalization",
            "key_inputs": ["normalized EPS", "HBM mix"],
            "peer_or_historical_basis": ["memory-cycle history"],
            "valuation_caveats": ["peak earnings can understate P/E"],
        },
        "multiple_expansion_signals": ["FCF exceeds consensus"],
        "multiple_compression_signals": ["real yields rise"],
        "strengthen_signals": ["HBM customer expansion"],
        "weaken_signals": ["HBM market share decline"],
        "invalidation_signals": ["major HBM customer loss"],
        "price_rules": {
            "currency": "KRW",
            "confirmation_price": 1550000,
            "warning_price": 1400000,
            "invalidation_price": 1320000,
        },
    }


def test_monitoring_item_registration_versions_and_deactivation() -> None:
    with TestClient(app) as client:
        response = client.post("/monitoring-items", json=_payload(), headers=AUTH_HEADERS)
        assert response.status_code == 200
        assert response.json()["ticker"] == "000660"
        assert response.json()["active"] is False
        assert response.json()["onboarding_state"] == "PENDING_ONBOARDING"
        assert response.json()["production_eligible"] is False
        assert response.json()["thesis"]["version"] == 1
        assert response.json()["thesis"]["thesis_drivers"] == [
            "HBM leadership",
            "AI server demand",
        ]
        assert response.json()["thesis"]["validation_metrics"] == [
            "HBM revenue growth",
            "Free cash flow",
        ]
        assert response.json()["thesis"]["market_expectations"]["level"] == "very_high"
        assert (
            response.json()["thesis"]["valuation_framework"]["primary_method"]
            == "cycle-adjusted forward P/E"
        )
        assert response.json()["thesis"]["multiple_expansion_signals"] == [
            "FCF exceeds consensus"
        ]
        assert response.json()["thesis"]["price_rules"]["invalidation_price"] == 1320000

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


def test_monitoring_summaries_are_compact_and_action_friendly() -> None:
    with TestClient(app) as client:
        client.post("/monitoring-items", json=_payload(), headers=AUTH_HEADERS)
        response = client.get(
            "/monitoring-items/summaries?active_only=false", headers=AUTH_HEADERS
        )

    assert response.status_code == 200
    summary = response.json()[0]
    assert summary["ticker"] == "000660"
    assert summary["core_thesis"] == "AI infrastructure demand supports earnings growth"
    assert summary["thesis_drivers"] == ["HBM leadership", "AI server demand"]
    assert summary["validation_metrics"] == ["HBM revenue growth", "Free cash flow"]
    assert summary["market_expectation_level"] == "very_high"
    assert summary["valuation_primary_method"] == "cycle-adjusted forward P/E"
    assert summary["multiple_compression_signals"] == ["real yields rise"]
    assert summary["price_rules_summary"] == [
        "confirmation close >= 1550000 KRW",
        "warning close < 1400000 KRW",
        "invalidation close < 1320000 KRW",
    ]
    assert "thesis" not in summary


def test_assessment_write_preserves_history_and_updates_latest_fields() -> None:
    payload = _payload()
    payload["ticker"] = "ASMT"
    payload["company_name"] = "Assessment Test"
    first = {
        "assessment_date": "2030-01-01",
        "business_thesis_change": "no_material_change",
        "valuation_context": "neutral",
        "earnings_estimate_impact": "unknown",
        "confirmed_facts": ["Official filing was reviewed"],
        "inferred_implications": ["No material model change"],
        "unknowns": ["Consensus estimate is unavailable"],
    }
    second = {
        "assessment_date": "2030-01-02",
        "business_thesis_change": "strengthened",
        "valuation_context": "mixed",
        "earnings_estimate_impact": "up",
        "market_expectation_assessment": {
            "level": "very_high",
            "assessment": "mixed",
            "summary": "Strong growth is already expected",
            "evidence_basis": ["earnings beat", "real yield pressure"],
        },
        "confirmed_facts": ["Official guidance increased"],
        "inferred_implications": ["Earnings estimates may rise"],
        "unknowns": ["Duration of multiple pressure"],
    }
    with TestClient(app) as client:
        registered = client.post("/monitoring-items", json=payload, headers=AUTH_HEADERS)
        assert registered.status_code == 200
        version = registered.json()["thesis"]["version"]
        assert client.post(
            "/monitoring-items/ASMT/assessments", json=first, headers=AUTH_HEADERS
        ).status_code == 200
        saved = client.post(
            "/monitoring-items/ASMT/assessments", json=second, headers=AUTH_HEADERS
        )
        item = client.get("/monitoring-items/ASMT", headers=AUTH_HEADERS)
        history = client.get(
            "/monitoring-items/ASMT/assessments?limit=30", headers=AUTH_HEADERS
        )

    assert saved.status_code == 200
    assert saved.json()["business_thesis_change"] == "strengthened"
    assert saved.json()["valuation_change"] == "mixed"
    assert saved.json()["valuation_context"]["impact"] == "mixed"
    assert saved.json()["confirmed_facts"] == ["Official guidance increased"]
    assert item.json()["latest_status"] == "strengthened"
    assert item.json()["latest_assessment_date"] == "2030-01-02"
    assert item.json()["latest_valuation_context"] == "mixed"
    assert item.json()["latest_earnings_estimate_impact"] == "up"
    assert item.json()["thesis"]["version"] == version
    assert item.json()["thesis"]["market_expectations"] == payload["market_expectations"]
    assert item.json()["thesis"]["valuation_framework"] == payload["valuation_framework"]
    assert item.json()["thesis"]["multiple_expansion_signals"] == [
        "FCF exceeds consensus"
    ]
    assert item.json()["thesis"]["multiple_compression_signals"] == [
        "real yields rise"
    ]
    assert [entry["assessment_date"] for entry in history.json()] == [
        "2030-01-02",
        "2030-01-01",
    ]
