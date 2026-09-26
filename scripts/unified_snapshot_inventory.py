"""Read-only scheduler inventory. Never exports environment values or raw prompts."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import plistlib
import subprocess
import tomllib

from app.services.unified_run_artifacts import durable_json


def inventory(home: Path, operating: Path) -> dict:
    def fingerprint(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def command(args):
        result = subprocess.run(args, capture_output=True, text=True, check=False)
        return result.returncode, result.stdout

    automations = []
    for path in sorted((home / ".codex/automations").glob("*/automation.toml")):
        value = tomllib.loads(path.read_text())
        if "thesis-monitor" not in str(path) and "thesis-monitor" not in value.get("prompt", ""):
            continue
        identity = path.parent.name
        automations.append({"id": identity, "status": value.get("status"),
                            "schedule": value.get("rrule"), "sha256": fingerprint(path),
                            "classification": "DISABLE_AT_CUTOVER" if identity in {
                                "thesis-monitor-ai-review-us-primary", "thesis-monitor-ai-review-us-backup",
                                "thesis-monitor-ai-review-kr-primary", "thesis-monitor-ai-review-kr-backup"
                            } else "PRESERVE_UNRELATED"})
    agents = []
    disabled_code, disabled_output = command(["launchctl", "print-disabled", f"gui/{os.getuid()}"])
    for path in sorted((home / "Library/LaunchAgents").glob("*thesis-monitor*.plist")):
        value = plistlib.loads(path.read_bytes())
        label = value["Label"]
        code, output = command(["launchctl", "print", f"gui/{os.getuid()}/{label}"])
        argv = value.get("ProgramArguments", [])
        role = "PRESERVE_UNRELATED"
        if any("app.jobs.monitor_daily" in arg for arg in argv):
            role = "REPLACE_SINGLE_ENTRY"
        if any("app.jobs.ai_review" in arg and ("fallback" in arg or "retry-delivery" in arg)
               for arg in argv):
            role = "DISABLE_SECONDARY_DELIVERY_PATH"
        agents.append({"label": label, "file": path.name, "sha256": fingerprint(path),
                       "schedule": value.get("StartCalendarInterval"),
                       "loaded": code == 0, "launchctl_returncode": code,
                       "disabled": f'"{label}" => true' in disabled_output if disabled_code == 0 else None,
                       "running": "state = running" in output if code == 0 else None,
                       "entrypoint": next((a for a in argv if "app.jobs." in a), "service_or_other"),
                       "classification": role})
    code, head = command(["git", "-C", str(operating), "rev-parse", "HEAD"])
    status_code, status = command(["git", "-C", str(operating), "status", "--porcelain"])
    return {"observed_at": datetime.now(timezone.utc).isoformat(), "automations": automations,
            "launch_agents": agents, "operating_head": head.strip() if code == 0 else None,
            "operating_clean": not status.strip() if status_code == 0 else None,
            "mutations": 0, "secrets_exported": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--operating", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = inventory(args.home, args.operating)
    durable_json(args.output, value, exclusive=True)
    print(json.dumps(value, indent=2))
