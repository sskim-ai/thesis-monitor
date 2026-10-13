"""Own one official CLI process; transport authorization is not model input."""
import json
from pathlib import Path
import sys

from app.services.official_codex_shadow_transport_service import OfficialShadowError
from app.services.official_codex_production_executor import invoke_official_bound
from app.services.production_model_transport import CONTRACT, ProductionWireRequest, binding_from_json
from app.services.unified_run_artifacts import durable_json


def main():
    frame = json.loads(sys.stdin.buffer.read())
    if set(frame) != {"contract", "directory", "binding", "request_id", "prompt_sha256", "schema_sha256"} or frame["contract"] != CONTRACT:
        raise ValueError("production_model_worker_contract")
    path = Path(frame["directory"])
    binding = binding_from_json(frame["binding"])
    request = ProductionWireRequest(binding, frame["request_id"], frame["prompt_sha256"], frame["schema_sha256"])
    try:
        receipt = invoke_official_bound(codex_bin=str(binding.executable), prompt=path / "approved-input/prompt.txt",
            schema=path / "approved-input/provider-wire-schema.json", output=path / "raw-output.json",
            log=path / "events.jsonl", cwd=path / "approved-input", timeout=600,
            state_namespace=request.request_id, request=request, receipt_contract=CONTRACT)
    except OfficialShadowError as exc:
        receipt = dict(status="FAIL", error_code=exc.code, process_started=exc.process_started)
    except Exception as exc:
        receipt = dict(status="FAIL", error_code="PRODUCTION_WIRE_INTERNAL_FAILURE", error_type=type(exc).__name__)
    else:
        receipt = dict(status="PASS", transport=receipt)
    durable_json(path / "transport-receipt.json", receipt, exclusive=True)


if __name__ == "__main__":
    main()
