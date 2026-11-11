"""Own one official CLI process; transport authorization is not model input."""
import json
from pathlib import Path
import sys

from app.services.official_codex_shadow_transport_service import OfficialShadowError
from app.services.official_codex_production_executor import invoke_official_bound
from app.services.official_transport_input_preflight import PREFLIGHT_REJECT_EXIT, preflight_official_input
from app.services.production_model_transport import request_from_frame
from app.services.unified_run_artifacts import durable_json


def main():
    frame = json.loads(sys.stdin.buffer.read())
    request = request_from_frame(frame)
    path = Path(frame["directory"])
    binding = request.binding
    try:
        preflight_official_input(prompt=path / "approved-input/prompt.txt",
            schema=path / "approved-input/provider-wire-schema.json", cwd=path / "approved-input", request=request)
    except (OfficialShadowError, ValueError):
        return PREFLIGHT_REJECT_EXIT
    try:
        receipt = invoke_official_bound(codex_bin=str(binding.executable), prompt=path / "approved-input/prompt.txt",
            schema=path / "approved-input/provider-wire-schema.json", output=path / "raw-output.json",
            log=path / "events.jsonl", cwd=path / "approved-input", timeout=request.execution_policy.timeout_seconds,
            state_namespace=request.request_id, request=request, receipt_contract=frame['contract'])
    except OfficialShadowError as exc:
        receipt = dict(status="FAIL", error_code=exc.code, process_started=exc.process_started)
    except Exception as exc:
        receipt = dict(status="FAIL", error_code="PRODUCTION_WIRE_INTERNAL_FAILURE", error_type=type(exc).__name__)
    else:
        receipt = dict(status="PASS", transport=receipt)
    durable_json(path / "transport-receipt.json", receipt, exclusive=True)


if __name__ == "__main__":
    raise SystemExit(main())
