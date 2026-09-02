from __future__ import annotations

import argparse
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.jobs.accepted_decision_v2_runtime import (
    _invoke_signed_in_codex,
    _signed_in_codex_bin,
)


CONTRACT = "codex-scheduler-context-app-server-probe-v1"


def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def run_probe(output_dir: Path, *, timeout: int = 180) -> dict[str, object]:
    probe_id = f"scheduler-probe-{uuid.uuid4()}"
    root = output_dir.resolve() / probe_id
    prompt = root / "prompt.txt"
    schema = root / "schema.json"
    output = root / "output.json"
    log = root / "codex.log"
    _write(
        prompt,
        (
            "Return exactly one JSON object with status APP_SERVER_READY. "
            "Do not access files, tools, networks, messaging, or external services.\n"
        ),
    )
    _write(
        schema,
        json.dumps(
            {
                "type": "object",
                "properties": {"status": {"type": "string", "const": "APP_SERVER_READY"}},
                "required": ["status"],
                "additionalProperties": False,
            },
            sort_keys=True,
        ),
    )
    transport = _invoke_signed_in_codex(
        codex_bin=_signed_in_codex_bin(),
        prompt=prompt,
        output=output,
        log=log,
        schema=schema,
        cwd=root,
        timeout=timeout,
        state_namespace=probe_id,
    )
    result = json.loads(output.read_text(encoding="utf-8"))
    if result != {"status": "APP_SERVER_READY"}:
        raise ValueError("codex_scheduler_context_probe_output_invalid")
    receipt = {
        "contract": CONTRACT,
        "status": "PASS",
        "probe_id": probe_id,
        "production_send": 0,
        "telegram_imported": 0,
        "database_mutation": 0,
        "network_readiness_contract": transport["contract"],
        "network_probe_attempts": transport["network_probe_attempts"],
        "codex_transport_attempts": transport["transport_attempts"],
        "transport_retry_recovered": transport["retry_recovered"],
        "completed_at": datetime.now(UTC).isoformat(),
    }
    _write(root / "receipt.json", json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/codex_runtime_state/probes"),
    )
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    print(
        json.dumps(
            run_probe(args.output_dir, timeout=args.timeout),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
