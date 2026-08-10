from copy import deepcopy

from fastapi import FastAPI


ACTION_PATHS = {
    "/health",
    "/provider-status",
    "/company-profile",
    "/earnings-checkpoints",
    "/thesis-events",
    "/monitoring-items",
    "/monitoring-items/summaries",
    "/monitoring-items/{ticker}",
    "/monitoring-items/{ticker}/deactivate",
    "/monitoring-items/{ticker}/assessments",
    "/macro/briefings/latest",
    "/macro/briefings/{briefing_date}",
    "/macro/regime/latest",
    "/macro/theses",
    "/macro/events",
    "/macro/provider-status",
    "/macro/ticker/{ticker}/impacts",
}


def _simplify_thesis_event_action(schema: dict[str, object]) -> None:
    paths = schema.get("paths")
    if not isinstance(paths, dict):
        return
    path_item = paths.get("/thesis-events")
    if not isinstance(path_item, dict):
        return
    operation = path_item.get("get")
    if not isinstance(operation, dict):
        return

    operation["summary"] = "Get Thesis Events"
    operation.pop("description", None)
    for parameter in operation.get("parameters", []):
        if isinstance(parameter, dict) and parameter.get("name") == "provider":
            parameter["schema"] = {
                "type": "string",
                "minLength": 1,
                "title": "Provider",
            }


def _simplify_monitor_stock_action(schema: dict[str, object]) -> None:
    paths = schema.get("paths")
    if not isinstance(paths, dict):
        return
    path_item = paths.get("/monitoring-items")
    if not isinstance(path_item, dict):
        return
    operation = path_item.get("post")
    if not isinstance(operation, dict):
        return

    request_body = operation.get("requestBody")
    if not isinstance(request_body, dict):
        return
    content = request_body.get("content")
    if not isinstance(content, dict):
        return
    media_type = content.get("application/json")
    if not isinstance(media_type, dict):
        return

    signal_array = {"type": "array", "items": {"type": "string"}}
    media_type["schema"] = {
        "type": "object",
        "properties": {
            "ticker": {"type": "string", "minLength": 1},
            "company_name": {"type": "string", "minLength": 1},
            "exchange": {"type": "string"},
            "core_thesis": {"type": "string", "minLength": 1},
            "time_horizon": {"type": "string"},
            "thesis_drivers": signal_array,
            "validation_metrics": signal_array,
            "strengthen_signals": signal_array,
            "weaken_signals": signal_array,
            "invalidation_signals": signal_array,
            "price_rules": {
                "type": "object",
                "properties": {
                    "currency": {"type": "string"},
                    "basis": {"type": "string", "enum": ["close"]},
                    "confirmation_price": {"type": "number"},
                    "support_zone_low": {"type": "number"},
                    "support_zone_high": {"type": "number"},
                    "warning_price": {"type": "number"},
                    "invalidation_price": {"type": "number"},
                },
            },
            "market_expectations": {
                "type": "object",
                "properties": {
                    "as_of_date": {"type": "string", "format": "date"},
                    "level": {
                        "type": "string",
                        "enum": [
                            "depressed",
                            "low",
                            "balanced",
                            "elevated",
                            "very_high",
                            "speculative",
                            "unknown",
                        ],
                    },
                    "summary": {"type": "string"},
                    "priced_in": signal_array,
                    "upside_surprises": signal_array,
                    "downside_surprises": signal_array,
                    "evidence_basis": signal_array,
                },
            },
            "valuation_framework": {
                "type": "object",
                "properties": {
                    "primary_method": {"type": "string"},
                    "secondary_methods": signal_array,
                    "rationale": {"type": "string"},
                    "key_inputs": signal_array,
                    "peer_or_historical_basis": signal_array,
                    "valuation_caveats": signal_array,
                },
            },
            "multiple_expansion_signals": signal_array,
            "multiple_compression_signals": signal_array,
            "macro_exposures": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "factor": {"type": "string", "minLength": 1},
                        "direction": {
                            "type": "string",
                            "enum": ["positive", "negative", "mixed"],
                        },
                        "weight": {"type": "integer", "minimum": 1, "maximum": 5},
                        "channel": {"type": "string", "minLength": 1},
                        "horizon": {"type": "string"},
                        "condition": {"type": "string"},
                        "review_required": {"type": "boolean"},
                    },
                    "required": ["factor", "direction", "channel"],
                },
            },
        },
        "required": ["ticker", "company_name", "core_thesis"],
    }


def build_action_schema(app: FastAPI) -> dict[str, object]:
    schema = deepcopy(app.openapi())
    schema["info"] = {
        "title": "Thesis Monitor Public Action API",
        "version": "0.2.0",
        "description": (
            "Collect thesis evidence, register versioned investment theses, manage the monitored "
            "stock list, read daily thesis assessments, and retrieve macro briefings, regimes, "
            "events, and ticker-level macro impacts. Administrative jobs are excluded."
        ),
    }
    schema["servers"] = [{"url": "https://sskim-macmini.tailb44bb1.ts.net/thesis"}]
    paths = schema.get("paths", {})
    if isinstance(paths, dict):
        schema["paths"] = {
            path: value for path, value in paths.items() if path in ACTION_PATHS
        }
    _simplify_thesis_event_action(schema)
    _simplify_monitor_stock_action(schema)
    return schema
