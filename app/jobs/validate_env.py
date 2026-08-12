import argparse
from pathlib import Path

from pydantic import ValidationError

from app.config import Settings


def validation_error_lines(error: ValidationError) -> list[str]:
    lines: list[str] = []
    for item in error.errors(include_input=False, include_url=False):
        key = ".".join(str(part) for part in item.get("loc", ())) or "configuration"
        error_type = str(item.get("type", "validation_error"))
        label = "Unknown environment key" if error_type == "extra_forbidden" else "Invalid setting"
        lines.append(f"{label}: {key.upper()} ({error_type})")
    return sorted(set(lines))


def validate_env_file(path: Path) -> list[str]:
    try:
        Settings(_env_file=path)
    except ValidationError as exc:
        return validation_error_lines(exc)
    return []


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate thesis-monitor environment keys without printing values."
    )
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    args = parser.parse_args()
    errors = validate_env_file(args.env_file)
    if errors:
        print("Environment validation failed:")
        for line in errors:
            print(f"- {line}")
        raise SystemExit(1)
    print(f"Environment configuration is valid: {args.env_file}")


if __name__ == "__main__":
    main()
