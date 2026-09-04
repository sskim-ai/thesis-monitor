from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from app.jobs.accepted_decision_v2_runtime import (
    _invoke_signed_in_codex,
    _signed_in_codex_bin,
)
from app.services.codex_network_transport_service import codex_tls_environment
from app.services.codex_runtime_state_service import prepare_codex_runtime_state


EXPECTED_RESULT = "TLS_PREFLIGHT_OK"


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="thesis-monitor-tls-preflight-") as raw_root:
        root = Path(raw_root)
        prompt = root / "prompt.txt"
        schema = root / "schema.json"
        output = root / "output.json"
        log = root / "codex.log"
        prompt.write_text(
            'Return one JSON object exactly: {"result":"TLS_PREFLIGHT_OK"}. '
            "Do not call tools.\n",
            encoding="utf-8",
        )
        _write_json(
            schema,
            {
                "type": "object",
                "properties": {"result": {"type": "string", "const": EXPECTED_RESULT}},
                "required": ["result"],
                "additionalProperties": False,
            },
        )
        telemetry = _invoke_signed_in_codex(
            codex_bin=_signed_in_codex_bin(),
            prompt=prompt,
            output=output,
            log=log,
            schema=schema,
            cwd=root,
            timeout=args.timeout,
            state_namespace="us-natural-tls-preflight-20260904",
        )
        result = json.loads(output.read_text(encoding="utf-8"))
        log_text = log.read_text(encoding="utf-8", errors="replace")
        runtime_state = prepare_codex_runtime_state(
            root / "runtime-state",
            namespace="audit",
        )
        tls_configuration = codex_tls_environment(runtime_state.environment())
        proof = {
            "contract": "us-signed-in-cli-tls-preflight-v1",
            "cli_exit_code": 0,
            "model_result_count": int(result == {"result": EXPECTED_RESULT}),
            "tls_unknown_issuer_count": log_text.casefold().count("unknownissuer"),
            "tls_certificate_verify_error_count": log_text.casefold().count(
                "certificate verify"
            ),
            "trust_source": tls_configuration.trust_source,
            "ca_bundle_path": tls_configuration.ca_bundle_path,
            "ca_bundle_sha256": (
                hashlib.sha256(Path(tls_configuration.ca_bundle_path).read_bytes()).hexdigest()
                if tls_configuration.ca_bundle_path
                else None
            ),
            "transport": telemetry,
            "production_packet_used": 0,
            "telegram_send": 0,
            "scheduler_mutation": 0,
            "database_mutation": 0,
        }
        print(json.dumps(proof, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
