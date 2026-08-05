import json
from pathlib import Path

from app.main import app


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
}


def main() -> None:
    schema = app.openapi()
    schema["info"] = {
        "title": "Thesis Monitor Public Action API",
        "version": "0.2.0",
        "description": (
            "Collect thesis evidence, register versioned investment theses, manage the monitored "
            "stock list, and read daily thesis assessments. Administrative jobs are excluded."
        ),
    }
    schema["servers"] = [{"url": "https://sskim-macmini.tailb44bb1.ts.net/thesis"}]
    schema["paths"] = {
        path: value for path, value in schema["paths"].items() if path in ACTION_PATHS
    }
    rendered = json.dumps(schema, ensure_ascii=False, indent=2) + "\n"
    for output_path in (
        "openapi.action.json",
        "docs/custom_gpt_action_schema.yaml",
        "docs/custom_gpt_action_schema_v2.yaml",
    ):
        Path(output_path).write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
