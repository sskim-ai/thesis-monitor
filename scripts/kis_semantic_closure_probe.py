"""Bounded opt-in REV33 identity reads; sealed Stage-A estimates are never refreshed."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import logging
from pathlib import Path
import time

import httpx

from app.services.unified_run_artifacts import durable_bytes
from scripts.kis_estimate_capability_probe import (
    DATA_PATH, ORIGIN, TR_ID, Probe, ProbeStop, STAGE_A, STAGE_B,
    load_credentials, now, scan, schema_inventory,
)

ROUTES = {
    "search-info": ("/uapi/domestic-stock/v1/quotations/search-info", "CTPF1604R"),
    "search-stock-info": ("/uapi/domestic-stock/v1/quotations/search-stock-info", "CTPF1002R"),
}


def needs_secondary(payload, code):
    row = payload.get("output")
    if not isinstance(row, dict):
        return True
    identifiers = {row.get(k) for k in ("pdno", "shtn_pdno", "std_pdno")}
    direct_pair = code in identifiers and "A" + code in identifiers
    return not (direct_pair and row.get("prdt_type_cd") == "300"
                and row.get("mket_id_cd") and row.get("scty_grp_id_cd")
                and row.get("prdt_name"))


class ClosureProbe(Probe):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identity_results = {}
        self.identity_attempts = set()
        self.stage_b_admitted = False

    def identity(self, code, kind):
        key = (code, kind)
        if code not in STAGE_A or kind not in ROUTES or key in self.identity_attempts or not self.token:
            raise ProbeStop("IDENTITY_REQUEST_SCOPE_GAP")
        if kind == "search-stock-info":
            primary = self.identity_results.get(code, {}).get("search-info")
            if not primary or not needs_secondary(primary["payload"], code):
                raise ProbeStop("SECONDARY_NOT_REQUIRED")
        self.disk_guard()
        self.identity_attempts.add(key)
        path, tr_id = ROUTES[kind]
        stem = "identity/" + code + "-" + kind
        self.save(stem + "-request.json", {"method": "GET", "path": path, "tr_id": tr_id,
            "params": {"PDNO": code, "PRDT_TYPE_CD": "300"}, "started_at": now(),
            "ordinal": len(self.identity_attempts), "retry": 0, "redirects": False})
        try:
            response = self.client.get(ORIGIN + path,
                params={"PDNO": code, "PRDT_TYPE_CD": "300"},
                headers={"authorization": "Bearer " + self.token,
                    "appkey": self.credentials.app_key, "appsecret": self.credentials.app_secret,
                    "tr_id": tr_id, "custtype": "P", "content-type": "application/json",
                    "accept": "application/json", "user-agent": "ThesisMonitor/1.0"})
        except httpx.HTTPError:
            self.save(stem + "-receipt.json", {"status": "TRANSPORT_FAILURE", "ended_at": now()})
            raise ProbeStop("TRANSPORT_FAILURE") from None
        raw = response.content
        scan(raw, self.secrets, auth_fields=True)
        headers = {k: response.headers.get(k) for k in ("content-type", "tr_id", "tr_cont", "date")}
        scan(json.dumps(headers).encode(), self.secrets)
        try:
            payload = json.loads(raw)
        except (ValueError, UnicodeError):
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        durable_bytes(self.output / (stem + ".body"), raw, exclusive=True)
        receipt = {"http_status": response.status_code, "ended_at": now(),
            "raw_sha256": sha256(raw).hexdigest(), "bytes": len(raw), "headers": headers,
            "rt_cd": payload.get("rt_cd"), "msg_cd": payload.get("msg_cd"),
            "msg1": payload.get("msg1"), "secret_scan": "PASS"}
        self.save(stem + "-receipt.json", receipt)
        if response.status_code != 200 or payload.get("rt_cd") != "0":
            raise ProbeStop("IDENTITY_SOURCE_FAILURE")
        if headers["tr_cont"] in ("M", "F"):
            raise ProbeStop("IDENTITY_UNEXPECTED_CONTINUATION")
        self.identity_results.setdefault(code, {})[kind] = {"receipt": receipt, "payload": payload}

    def fetch(self, code):
        if code not in STAGE_B or not self.stage_b_admitted:
            raise ProbeStop("STAGE_B_NOT_ADMITTED")
        if code in self.pages or self.data_count >= 6 or not self.token:
            raise ProbeStop("STAGE_B_BUDGET_GAP")
        self.disk_guard()
        self.pages[code] = 1
        self.data_count += 1
        stem = "stage-b/" + code
        self.save(stem + "-request.json", {"path": DATA_PATH, "tr_id": TR_ID,
            "params": {"SHT_CD": code}, "started_at": now(), "page": 1, "retry": 0})
        try:
            response = self.client.get(ORIGIN + DATA_PATH, params={"SHT_CD": code},
                headers={"authorization": "Bearer " + self.token,
                    "appkey": self.credentials.app_key, "appsecret": self.credentials.app_secret,
                    "tr_id": TR_ID, "custtype": "P", "content-type": "application/json",
                    "accept": "application/json", "user-agent": "ThesisMonitor/1.0"})
        except httpx.HTTPError:
            raise ProbeStop("TRANSPORT_FAILURE") from None
        raw = response.content
        scan(raw, self.secrets, auth_fields=True)
        headers = {k: response.headers.get(k) for k in ("content-type", "tr_id", "tr_cont", "date")}
        scan(json.dumps(headers).encode(), self.secrets)
        try:
            payload = json.loads(raw)
        except (ValueError, UnicodeError):
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        durable_bytes(self.output / (stem + ".body"), raw, exclusive=True)
        receipt = {"http_status": response.status_code, "ended_at": now(),
            "raw_sha256": sha256(raw).hexdigest(), "bytes": len(raw), "headers": headers,
            "rt_cd": payload.get("rt_cd"), "msg_cd": payload.get("msg_cd"),
            "msg1": payload.get("msg1"), "secret_scan": "PASS"}
        self.save(stem + "-receipt.json", receipt)
        self.save(stem + "-schema.json", schema_inventory(payload))
        if response.status_code != 200:
            raise ProbeStop("TRANSPORT_FAILURE")
        # Portal policy does not permit paging, even if an unexpected header requests it.
        if headers["tr_cont"] in ("M", "F"):
            raise ProbeStop("ESTIMATE_CONTINUATION_POLICY_GAP")
        self.results[code] = {"payload": payload, "receipt": receipt,
            "state": "COMPLETE" if payload.get("rt_cd") == "0" else "PROVIDER_RETURN_ERROR"}

    def counters(self):
        return {**super().counters(), "identity": len(self.identity_attempts),
            "search_info": sum(k == "search-info" for _, k in self.identity_attempts),
            "search_stock_info": sum(k == "search-stock-info" for _, k in self.identity_attempts),
            "stage_a_estimate_refresh": 0, "opendart": 0}


def run(output, env_file):
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    for name in ("httpx", "httpcore"):
        logging.getLogger(name).disabled = True
    with httpx.Client(timeout=45, follow_redirects=False) as client:
        probe = ClosureProbe(output, load_credentials(env_file), client)
        terminal = "IDENTITY_REVIEW_PENDING"
        try:
            probe.save("execution-freeze.json", {"script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
                "created_at": now(), "initial_identity_calls_max": 2, "identity_calls_max": 4,
                "auth_max": 1, "stage_a_estimate_refresh_max": 0, "retry_max": 0,
                "routes": ROUTES, "codes": STAGE_A, "stage_b": "QUALIFIED_OWNER_GATE_REQUIRED",
                "secondary_rule": "Missing direct provider code pair OR market/security/name fields"})
            probe.authenticate()
            for code in STAGE_A:
                probe.identity(code, "search-info")
                time.sleep(0.2)
            for code in STAGE_A:
                if needs_secondary(probe.identity_results[code]["search-info"]["payload"], code):
                    probe.identity(code, "search-stock-info")
                    time.sleep(0.2)
            probe.save("identity-results.json", probe.identity_results)
            probe.save("identity-counters.json", probe.counters())
            print("IDENTITY_READS_COMPLETE token memory-only; offline semantics gate required", flush=True)
            terminal = "IDENTITY_READS_COMPLETE_OFFLINE_REVIEW_REQUIRED"
            gate = output / "stage-b-gate.json"
            deadline = time.monotonic() + 3600
            while not gate.exists() and time.monotonic() < deadline:
                time.sleep(1)
            if gate.exists():
                decision = json.loads(gate.read_bytes())
                if decision.get("allow") is True:
                    owner = Path(decision["owner_path"])
                    if (decision.get("qualified_stage_a_metrics", 0) < 1
                            or decision.get("focused_tests") != "PASS"
                            or sha256(owner.read_bytes()).hexdigest() != decision.get("owner_sha256")):
                        raise ProbeStop("STAGE_B_OWNER_GATE_GAP")
                    probe.stage_b_admitted = True
                    for code in STAGE_B:
                        probe.fetch(code)
                        time.sleep(0.2)
                    probe.save("stage-b-results.json", probe.results)
                    terminal = "STAGE_B_COMPLETE_OFFLINE_QUALIFICATION_REQUIRED"
                else:
                    terminal = "STAGE_A_SEMANTIC_REVIEW_CLOSED_NO_ADDITIONAL_ESTIMATE_CALLS"
            else:
                terminal = "OFFLINE_REVIEW_TIMEOUT_NO_STAGE_B"
        except ProbeStop as exc:
            terminal = "R2B_R9_REV33_KIS_" + str(exc)
        finally:
            probe.save("request-counters.json", probe.counters())
            probe.save("terminal.json", {"terminal": terminal, "ended_at": now()})
            probe.token = None
            print(terminal, json.dumps(probe.counters()), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--env-file", required=True, type=Path)
    args = parser.parse_args()
    try:
        run(args.output, args.env_file)
    except Exception:
        print("R2B_R9_REV33_SANITIZED_PROBE_FAILURE", flush=True)
        raise SystemExit(2) from None
