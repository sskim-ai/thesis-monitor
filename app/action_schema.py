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
    return schema
