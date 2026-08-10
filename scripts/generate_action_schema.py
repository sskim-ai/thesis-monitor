import json
from pathlib import Path

from app.action_schema import build_action_schema
from app.main import app


def main() -> None:
    schema = build_action_schema(app)
    rendered = json.dumps(schema, ensure_ascii=False, indent=2) + "\n"
    for output_path in (
        "openapi.action.json",
        "docs/custom_gpt_action_schema.yaml",
        "docs/custom_gpt_action_schema_v2.yaml",
    ):
        Path(output_path).write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
