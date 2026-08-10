from copy import deepcopy

from fastapi import FastAPI


ACTION_PATHS = {
    "/health",
    "/provider-status",
    "/company-profile",
    "/earnings-checkpoints",
    "/thesis-events",
    "/monitoring-items",
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
    return schema
