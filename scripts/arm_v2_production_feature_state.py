from __future__ import annotations

import argparse
import os
from pathlib import Path


V2_PRODUCTION_FEATURE_STATE = {
    "VISIBLE_STOCK_DECISION_ENGINE": "v2_accepted",
    "V2_PRODUCTION_ENABLED": "true",
    "V2_FULL_MONITORED_STOCK_COVERAGE_TARGET": "true",
    "V1_DECISION_ROLLBACK_AVAILABLE": "true",
}


def arm_v2_production_feature_state(env_file: Path) -> tuple[str, ...]:
    original = env_file.read_text(encoding="utf-8")
    seen: set[str] = set()
    output: list[str] = []
    for line in original.splitlines():
        stripped = line.strip()
        key = stripped.split("=", 1)[0] if "=" in stripped else ""
        if stripped and not stripped.startswith("#") and key in V2_PRODUCTION_FEATURE_STATE:
            output.append(f"{key}={V2_PRODUCTION_FEATURE_STATE[key]}")
            seen.add(key)
        else:
            output.append(line)
    if output and output[-1]:
        output.append("")
    for key, value in V2_PRODUCTION_FEATURE_STATE.items():
        if key not in seen:
            output.append(f"{key}={value}")
    temporary = env_file.with_name(f".{env_file.name}.v2-production.tmp")
    temporary.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
    os.chmod(temporary, env_file.stat().st_mode)
    os.replace(temporary, env_file)
    return tuple(V2_PRODUCTION_FEATURE_STATE)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, required=True)
    updated = arm_v2_production_feature_state(parser.parse_args().env_file)
    print("updated_feature_keys=" + ",".join(updated))


if __name__ == "__main__":
    main()
