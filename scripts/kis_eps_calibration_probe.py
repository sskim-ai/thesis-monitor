"""Opt-in REV34 KIS calibration transport; never imported by runtime collectors."""

import argparse
from hashlib import sha256
import json
import logging
from pathlib import Path
import time

import httpx

from app.services.unified_run_artifacts import durable_bytes
from scripts import kis_estimate_capability_probe as base

RATIO_PATH = "/uapi/domestic-stock/v1/finance/financial-ratio"
RATIO_TR = "FHKST66430300"
CONTROLS = ("005930", "000660")


class CalibrationProbe(base.Probe):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calls = []
        self.last_finished = time.monotonic()
        self.stage_b_allowed = False

    def fetch(self, code, kind="ratio"):
        if (not self.token or kind not in {"ratio", "estimate"}
                or code not in base.KR8 or (code, kind) in self.calls
                or self.data_count >= 16):
            raise base.ProbeStop("REQUEST_SCOPE_GAP")
        if (code in CONTROLS and kind != "ratio") or (
                code in base.STAGE_B and not self.stage_b_allowed):
            raise base.ProbeStop("STAGE_GATE_GAP")
        if kind == "ratio" and code in base.STAGE_B:
            previous = self.results.get(code + ":estimate", {})
            rows = previous.get("payload", {}).get("output3")
            if previous.get("state") != "COMPLETE" or not isinstance(rows, list) or len(rows) != 3:
                raise base.ProbeStop("PARTIAL_LAYOUT_GATE_GAP")
        self.disk_guard()
        time.sleep(max(0, 1.1 - (time.monotonic() - self.last_finished)))
        path, tr = (RATIO_PATH, RATIO_TR) if kind == "ratio" else (base.DATA_PATH, base.TR_ID)
        params = ({"FID_DIV_CLS_CODE": "0", "fid_cond_mrkt_div_code": "J", "fid_input_iscd": code}
                  if kind == "ratio" else {"SHT_CD": code})
        stem = f"{kind}/{code}"
        self.data_count += 1
        self.calls.append((code, kind))
        request = {"method": "GET", "path": path, "tr_id": tr, "params": params,
                   "started_at": base.now(), "ordinal": self.data_count,
                   "redirects": False, "retries": 0, "security_code": code}
        self.save(stem + "-request.json", request)
        try:
            response = self.client.get(base.ORIGIN + path, params=params, headers={
                "authorization": "Bearer " + self.token,
                "appkey": self.credentials.app_key, "appsecret": self.credentials.app_secret,
                "tr_id": tr, "custtype": "P", "content-type": "application/json",
                "accept": "application/json", "user-agent": "ThesisMonitor/1.0"})
        except httpx.HTTPError:
            self.save(stem + "-receipt.json", {"state": "TRANSPORT_FAILURE", "ended_at": base.now()})
            raise base.ProbeStop("TRANSPORT_FAILURE") from None
        finally:
            self.last_finished = time.monotonic()
        raw = response.content
        base.scan(raw, self.secrets, auth_fields=True)
        headers = {key: response.headers.get(key) for key in ("tr_cont", "content-type", "date", "tr_id")}
        base.scan(json.dumps(headers).encode(), self.secrets)
        durable_bytes(self.output / (stem + ".body"), raw, exclusive=True)
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        receipt = {"security_code": code, "SHT_CD": code, "http_status": response.status_code, "ended_at": base.now(),
                   "raw_sha256": sha256(raw).hexdigest(), "response_headers": headers,
                   "request": request, "rt_cd": payload.get("rt_cd"), "msg_cd": payload.get("msg_cd"),
                   "secret_scan": "PASS", "bytes": len(raw)}
        self.save(stem + "-receipt.json", receipt)
        state = "COMPLETE"
        if response.status_code != 200 or payload.get("rt_cd") != "0":
            state = "KIS_RATE_LIMIT_GAP" if payload.get("msg_cd") == "EGW00201" else "KIS_RETURN_ERROR"
        elif headers.get("tr_cont") in {"M", "F"}:
            state = "UNAVAILABLE_CONTINUATION_CONTRACT"
        self.results[code + ":" + kind] = {"state": state, "receipt": receipt, "payload": payload}
        if state != "COMPLETE":
            raise base.ProbeStop(state)

    def counters(self):
        return {"authentication": self.auth_count, "data_total": self.data_count,
                "financial_ratio": sum(k == "ratio" for _, k in self.calls),
                "estimate_perform": sum(k == "estimate" for _, k in self.calls),
                "stage_a_estimate_perform": 0, "calls": self.calls, "continuations": 0,
                "minimum_spacing_seconds": 1.1, "retries": 0, "models": 0,
                "messages": 0, "telegram": 0, "orders": 0, "production_mutations": 0}


def run(output, env_file):
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name in ("httpx", "httpcore"):
        logging.getLogger(name).disabled = True
    with httpx.Client(timeout=45, follow_redirects=False) as client:
        probe = CalibrationProbe(output, base.load_credentials(env_file), client)
        probe.save("request-freeze.json", {"script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            "created_at": base.now(), "stage_a": CONTROLS, "stage_b": base.STAGE_B,
            "auth_max": 1, "data_max": 16, "continuation": "DISABLED_PORTAL_UNSUPPORTED",
            "stage_a_estimate_refresh": False, "timeout_seconds": 45, "retries": 0})
        terminal = "STAGE_A_REVIEW_PENDING"
        try:
            probe.authenticate()
            for code in CONTROLS:
                probe.fetch(code)
            probe.save("stage-a-results.json", probe.results)
            probe.save("stage-a-counters.json", probe.counters())
            print("STAGE_A_COMPLETE: 2 ratio requests; waiting for offline qualification gate", flush=True)
            gate = output / "stage-b-gate.json"
            deadline = time.monotonic() + 3600
            while not gate.exists() and time.monotonic() < deadline:
                time.sleep(1)
            if not gate.exists():
                terminal = "OFFLINE_REVIEW_TIMEOUT"
            else:
                decision = json.loads(gate.read_bytes())
                if decision.get("allow") is not True:
                    terminal = "STAGE_B_NOT_ADMITTED"
                else:
                    from scripts.kis_eps_wire_calibration import verify_stage_b_gate
                    verify_stage_b_gate(decision)
                    probe.stage_b_allowed = True
                    for code in base.STAGE_B:
                        probe.fetch(code, "estimate")
                        if len(probe.results[code + ":estimate"]["payload"].get("output3", [])) == 3:
                            probe.fetch(code, "ratio")
                    terminal = "STAGE_B_COMPLETE_OFFLINE_REVIEW_REQUIRED"
        except base.ProbeStop as exc:
            terminal = str(exc)
        except Exception as exc:
            terminal = "INTERNAL_GAP_" + type(exc).__name__
        finally:
            probe.save("results.json", probe.results)
            probe.save("counters.json", probe.counters())
            probe.save("terminal.json", {"state": terminal, "ended_at": base.now(),
                                        "token_storage": "MEMORY_ONLY"})
            probe.token = None
        print(terminal, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    args = parser.parse_args()
    run(args.output, args.env_file)
