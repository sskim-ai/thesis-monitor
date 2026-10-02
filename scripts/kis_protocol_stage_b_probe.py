"""Explicit opt-in KR6-only transport, gated by actual frozen Stage-A receipts."""

import argparse
from hashlib import sha256
import json
import logging
from pathlib import Path
import time

import httpx

from app.services.unified_run_artifacts import durable_bytes
from scripts import kis_estimate_capability_probe as base
from scripts.kis_output3_protocol_owner import verify_gate

IDENTITY_PATH = "/uapi/domestic-stock/v1/quotations/search-info"
IDENTITY_TR = "CTPF1604R"


class StageBProbe(base.Probe):
    def __init__(self, *args, gate, **kwargs):
        verify_gate(gate)
        super().__init__(*args, **kwargs)
        self.gate = gate
        self.calls = []
        self.last_finished = time.monotonic()

    def fetch(self, code, kind):
        verify_gate(self.gate)
        if (not self.token or code not in base.STAGE_B or kind not in {"estimate", "identity"}
                or (code, kind) in self.calls or self.data_count >= 12):
            raise base.ProbeStop("REQUEST_SCOPE_GAP")
        self.disk_guard()
        time.sleep(max(0, 1.1 - (time.monotonic() - self.last_finished)))
        path, tr = (base.DATA_PATH, base.TR_ID) if kind == "estimate" else (IDENTITY_PATH, IDENTITY_TR)
        params = {"SHT_CD": code} if kind == "estimate" else {"PDNO": code, "PRDT_TYPE_CD": "300"}
        stem = f"{kind}/{code}"
        self.calls.append((code, kind))
        self.data_count += 1
        request = {"method": "GET", "path": path, "tr_id": tr, "params": params,
            "security_code": code, "ordinal": self.data_count, "started_at": base.now(),
            "redirects": False, "retries": 0, "gate_sha256": self.gate["receipt_sha256"]}
        self.save(stem + "-request.json", request)
        try:
            response = self.client.get(base.ORIGIN + path, params=params, headers={
                "authorization": "Bearer " + self.token, "appkey": self.credentials.app_key,
                "appsecret": self.credentials.app_secret, "tr_id": tr, "custtype": "P",
                "content-type": "application/json", "accept": "application/json", "user-agent": "ThesisMonitor/1.0"})
        except httpx.HTTPError:
            self.save(stem + "-receipt.json", {"state": "TRANSPORT_FAILURE", "ended_at": base.now()})
            raise base.ProbeStop("TRANSPORT_FAILURE") from None
        finally:
            self.last_finished = time.monotonic()
        raw = response.content
        base.scan(raw, self.secrets, auth_fields=True)
        headers = {k: response.headers.get(k) for k in ("tr_cont", "content-type", "date", "tr_id")}
        base.scan(json.dumps(headers).encode(), self.secrets)
        durable_bytes(self.output / (stem + ".body"), raw, exclusive=True)
        try:
            payload = json.loads(raw)
        except (ValueError, UnicodeError):
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        state = "COMPLETE"
        if payload.get("msg_cd") == "EGW00201":
            state = "KIS_RATE_LIMIT_GAP"
        elif response.status_code != 200:
            state = "TRANSPORT_FAILURE"
        elif payload.get("rt_cd") != "0":
            state = "UNAVAILABLE_PROVIDER_RESPONSE"
        elif headers.get("tr_cont") in {"M", "F"}:
            state = "UNAVAILABLE_CONTINUATION_CONTRACT"
        receipt = {"state": state, "security_code": code, "kind": kind, "request": request,
            "http_status": response.status_code, "ended_at": base.now(), "raw_sha256": sha256(raw).hexdigest(),
            "response_headers": headers, "rt_cd": payload.get("rt_cd"), "msg_cd": payload.get("msg_cd"),
            "bytes": len(raw), "secret_scan": "PASS"}
        self.save(stem + "-receipt.json", receipt)
        self.results[code + ":" + kind] = receipt
        if state in {"KIS_RATE_LIMIT_GAP", "TRANSPORT_FAILURE", "UNAVAILABLE_CONTINUATION_CONTRACT"}:
            raise base.ProbeStop(state)

    def counters(self):
        return {"authentication": self.auth_count, "data_total": self.data_count,
            "estimate_perform": sum(k == "estimate" for _, k in self.calls),
            "search_info": sum(k == "identity" for _, k in self.calls), "calls": self.calls,
            "stage_a_estimate_refresh": 0, "corporate_actions": 0, "minimum_spacing_seconds": 1.1,
            "continuations": 0, "retries": 0, "models": 0, "messages": 0, "telegram": 0,
            "orders": 0, "production_mutations": 0}


def run(output, env_file, gate_file):
    gate = json.loads(gate_file.read_bytes())
    verify_gate(gate)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name in ("httpx", "httpcore"):
        logging.getLogger(name).disabled = True
    with httpx.Client(timeout=45, follow_redirects=False) as client:
        probe = StageBProbe(output, base.load_credentials(env_file), client, gate=gate)
        probe.save("request-freeze.json", {"script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            "gate_sha256": gate["receipt_sha256"], "subjects": base.STAGE_B, "auth_max": 1,
            "estimate_max": 6, "identity_max": 6, "data_max": 12, "retries": 0,
            "created_at": base.now(), "timeout_seconds": 45, "corporate_action_routes": "NONE_CONFIGURED"})
        terminal = "STAGE_B_COMPLETE_OFFLINE_REVIEW_REQUIRED"
        try:
            probe.authenticate()
            for code in base.STAGE_B:
                probe.fetch(code, "estimate")
                probe.fetch(code, "identity")
        except base.ProbeStop as exc:
            terminal = str(exc)
        except Exception as exc:
            terminal = "INTERNAL_GAP_" + type(exc).__name__
        finally:
            probe.save("results.json", probe.results)
            probe.save("counters.json", probe.counters())
            probe.save("terminal.json", {"state": terminal, "ended_at": base.now(), "token_storage": "MEMORY_ONLY"})
            probe.token = None
        print(terminal, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--gate-file", type=Path, required=True)
    args = parser.parse_args()
    run(args.output, args.env_file, args.gate_file)
