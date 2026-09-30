"""Opt-in bounded KIS discovery. No runtime imports, model calls or token cache."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from io import StringIO
import json
import logging
from pathlib import Path
import re
import shutil
import time

from dotenv.parser import parse_stream
import httpx

from app.services.unified_run_artifacts import durable_bytes, durable_json

ORIGIN = "https://openapi.koreainvestment.com:9443"
AUTH_PATH = "/oauth2/tokenP"
DATA_PATH = "/uapi/domestic-stock/v1/quotations/estimate-perform"
TR_ID = "HHKST668300C0"
STAGE_A = ("000660", "005930")
STAGE_B = ("003690", "005490", "010120", "012450", "047810", "086280")
KR8 = STAGE_A + STAGE_B
GROUPS = ("output1", "output2", "output3", "output4")
PREFIX = "R2B_R9_REV32_KIS_"
SECRET_FIELD = re.compile(r"^(?:access_token|appkey|appsecret|authorization|secret|token)$", re.I)


def now():
    return datetime.now(timezone.utc).isoformat()


class ProbeStop(Exception):
    """Only fixed machine codes may cross the transport boundary."""


@dataclass(frozen=True, repr=False)
class Credentials:
    app_key: str = field(repr=False)
    app_secret: str = field(repr=False)

    def __repr__(self):
        return "Credentials([REDACTED])"


def load_credentials(path: Path) -> Credentials:
    aliases = {"KIS_APP_KEY", "KIS_APP_SECRET", "KIS_SECRET_APP_KEY"}
    values = {}
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            stripped = stripped[1:].strip()
        key = stripped.split("=", 1)[0].strip()
        if key not in aliases:
            continue
        bindings = list(parse_stream(StringIO(stripped)))
        if len(bindings) != 1 or bindings[0].error or not bindings[0].value:
            raise ProbeStop("CREDENTIAL_GAP")
        value = bindings[0].value
        if key in values and values[key] != value:
            raise ProbeStop("CREDENTIAL_GAP")
        values[key] = value
    secrets = {values[k] for k in ("KIS_APP_SECRET", "KIS_SECRET_APP_KEY") if k in values}
    if not values.get("KIS_APP_KEY") or len(secrets) != 1:
        raise ProbeStop("CREDENTIAL_GAP")
    return Credentials(values["KIS_APP_KEY"], secrets.pop())


def scan(raw: bytes, secrets: list[bytes], *, auth_fields=False):
    if any(value and value in raw for value in secrets):
        raise ProbeStop("SECRET_EXPOSURE_GAP")
    if re.search(rb"\bBearer\s+[A-Za-z0-9._~-]+|\b\d{7,}:[A-Za-z0-9_-]{20,}", raw):
        raise ProbeStop("SECRET_EXPOSURE_GAP")
    if auth_fields:
        try:
            value = json.loads(raw)
        except (ValueError, UnicodeError):
            return

        def check(item):
            if isinstance(item, dict):
                for key, child in item.items():
                    if SECRET_FIELD.fullmatch(key) and child:
                        raise ProbeStop("SECRET_EXPOSURE_GAP")
                    check(child)
            elif isinstance(item, list):
                for child in item:
                    check(child)

        check(value)


def schema_inventory(payload: dict) -> dict:
    """Describe exact observed fields, without guessing metric or row semantics."""
    out = {}
    for group in GROUPS:
        value = payload.get(group)
        rows = value if isinstance(value, list) else [value] if isinstance(value, dict) else []
        fields = {}
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            for key, val in row.items():
                item = fields.setdefault(key, {"types": [], "values_in_row_order": []})
                kind = type(val).__name__
                if kind not in item["types"]:
                    item["types"].append(kind)
                item["values_in_row_order"].append({"row_index": index, "raw": val})
        out[group] = {"present": group in payload, "container_type": type(value).__name__,
                      "row_count": len(rows), "row_types": [type(r).__name__ for r in rows],
                      "fields": fields, "semantic_assignment": "NOT_INFERRED"}
    return out


class Probe:
    def __init__(self, output: Path, credentials: Credentials, client, *, extra_secrets=()):
        self.output = output
        self.credentials = credentials
        self.client = client
        self.secrets = [credentials.app_key.encode(), credentials.app_secret.encode(), *extra_secrets]
        self.token = None
        self.auth_count = 0
        self.data_count = 0
        self.pages = {}
        self.results = {}

    def save(self, name, value):
        raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
        scan(raw, self.secrets)
        durable_bytes(self.output / name, raw, exclusive=True)

    def disk_guard(self):
        if shutil.disk_usage(self.output).free < 8 * 1024**3:
            raise ProbeStop("DISK_GAP")

    def authenticate(self):
        if self.auth_count:
            raise ProbeStop("AUTH_BUDGET_EXCEEDED")
        self.disk_guard()
        self.auth_count += 1
        self.save("auth-attempt.json", {"started_at": now(), "operation": "tokenP", "attempt": 1})
        try:
            response = self.client.post(ORIGIN + AUTH_PATH,
                json={"grant_type": "client_credentials", "appkey": self.credentials.app_key,
                      "appsecret": self.credentials.app_secret},
                headers={"content-type": "application/json", "accept": "application/json",
                         "user-agent": "ThesisMonitor/1.0"})
        except httpx.HTTPError:
            self.save("auth-receipt.json", {"status": "TRANSPORT_FAILURE", "ended_at": now(),
                                           "body_preserved": False})
            raise ProbeStop("TRANSPORT_FAILURE") from None
        try:
            body = response.json()
        except (ValueError, UnicodeError):
            body = {}
        token = body.get("access_token") if isinstance(body, dict) else None
        success = response.status_code == 200 and isinstance(token, str) and bool(token)
        if isinstance(token, str) and token:
            self.secrets.append(token.encode())
        receipt = {"http_status": response.status_code, "ended_at": now(), "success": success,
                   "body_preserved": False, "token_storage": "MEMORY_ONLY",
                   "headers_preserved": False}
        # Never serialize the auth response, including unexpected error descriptions.
        self.save("auth-receipt.json", receipt)
        if not success:
            raise ProbeStop("AUTH_FAILURE")
        self.token = token

    def fetch(self, code: str):
        if code not in KR8 or code in self.results or code in self.pages or not self.token:
            raise ProbeStop("REQUEST_SCOPE_GAP")
        self.pages[code] = 0
        result = []
        continuation = ""
        for page in range(2):
            self.disk_guard()
            if self.data_count >= 16:
                raise ProbeStop("DATA_BUDGET_EXCEEDED")
            stem = f"data/{code}-{page + 1}"
            self.data_count += 1
            self.pages[code] += 1
            self.save(stem + "-request.json", {"method": "GET", "path": DATA_PATH, "tr_id": TR_ID,
                "SHT_CD": code, "tr_cont": continuation, "started_at": now(),
                "ordinal": self.data_count, "page": page + 1, "request_secret_values_recorded": False})
            try:
                response = self.client.get(ORIGIN + DATA_PATH, params={"SHT_CD": code},
                    headers={"authorization": "Bearer " + self.token,
                             "appkey": self.credentials.app_key, "appsecret": self.credentials.app_secret,
                             "tr_id": TR_ID, "tr_cont": continuation, "custtype": "P",
                             "content-type": "application/json", "accept": "application/json",
                             "user-agent": "ThesisMonitor/1.0"})
            except httpx.HTTPError:
                self.save(stem + "-receipt.json", {"status": "TRANSPORT_FAILURE", "ended_at": now()})
                raise ProbeStop("TRANSPORT_FAILURE") from None
            raw = response.content
            # Fail before any body/header reaches disk or stdout.
            scan(raw, self.secrets, auth_fields=True)
            headers = {k: response.headers.get(k) for k in ("tr_cont", "tr_id", "content-type", "date")}
            scan(json.dumps(headers).encode(), self.secrets)
            durable_bytes(self.output / (stem + ".body"), raw, exclusive=True)
            try:
                payload = json.loads(raw)
            except (ValueError, UnicodeError):
                payload = {}
            if not isinstance(payload, dict):
                payload = {}
            receipt = {"SHT_CD": code, "page": page + 1, "ended_at": now(),
                       "http_status": response.status_code, "response_headers": headers,
                       "rt_cd": payload.get("rt_cd"), "msg_cd": payload.get("msg_cd"),
                       "msg1": payload.get("msg1"), "raw_sha256": sha256(raw).hexdigest(),
                       "bytes": len(raw), "secret_scan": "PASS"}
            self.save(stem + "-receipt.json", receipt)
            self.save(stem + "-schema.json", schema_inventory(payload))
            result.append({"receipt": receipt, "payload": payload})
            if response.status_code != 200:
                raise ProbeStop("TRANSPORT_FAILURE")
            if payload.get("rt_cd") != "0":
                self.results[code] = {"state": "KIS_RETURN_ERROR", "pages": result}
                return
            if headers["tr_cont"] not in ("M", "F"):
                self.results[code] = {"state": "COMPLETE", "pages": result}
                return
            continuation = "N"
            time.sleep(0.2)
        self.results[code] = {"state": "BOUNDED_CONTINUATION_INCOMPLETE", "pages": result}

    def counters(self):
        return {"authentication": self.auth_count, "estimate_perform": self.data_count,
                "pages_per_subject": self.pages,
                "continuations": sum(max(0, value - 1) for value in self.pages.values()),
                "transport_retry": 0, "semantic_retry": 0, "models": 0, "messages": 0,
                "telegram": 0, "alpha_vantage": 0, "broker_orders": 0,
                "production_mutations_by_controller": 0}


def run(output: Path, env_file: Path):
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    durable_json(output / "probe-freeze.json", {"created_at": now(), "stage_a": STAGE_A,
        "stage_b": STAGE_B, "auth_max": 1, "data_max": 16, "pages_per_subject_max": 2,
        "timeout_seconds": 45, "retries": 0, "redirects": False,
        "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "DIAGNOSTIC_ONLY", "source_mutation": False}, exclusive=True)
    credentials = load_credentials(env_file)
    # Logging of HTTP request objects is deliberately disabled, not redirected to artifacts.
    for name in ("httpx", "httpcore"):
        logging.getLogger(name).disabled = True
    with httpx.Client(timeout=45, follow_redirects=False) as client:
        probe = Probe(output, credentials, client)
        terminal = "OFFLINE_STAGE_A_REVIEW_PENDING"
        try:
            probe.save("credential-presence.json", {"app_key_present": True, "secret_present": True,
                "credential_source_id_sha256": sha256(str(env_file).encode()).hexdigest(),
                "user_accepted_existing_unrotated_credentials": True, "values_recorded": False,
                "env_file_modified": False})
            probe.authenticate()
            for code in STAGE_A:
                probe.fetch(code)
                time.sleep(0.2)
            probe.save("stage-a-results.json", probe.results)
            probe.save("stage-a-counters.json", probe.counters())
            print("STAGE_A_COMPLETE offline semantic review required; token remains memory-only", flush=True)
            # The source owner must be implemented/frozen offline before Stage B is authorized.
            # Retain the single auth token in this process only; no second auth operation.
            deadline = time.monotonic() + 3600
            gate = output / "stage-b-gate.json"
            while not gate.exists() and time.monotonic() < deadline:
                time.sleep(1)
            if not gate.exists():
                terminal = "OFFLINE_STAGE_A_REVIEW_TIMEOUT"
            else:
                decision = json.loads(gate.read_bytes())
                if decision.get("allow") is True:
                    # Explicit useful path + frozen tested owner required, not a coverage count.
                    owner = Path(decision["owner_path"])
                    if (decision.get("stage_a_exact_semantics") is not True
                            or decision.get("focused_tests") != "PASS"
                            or sha256(owner.read_bytes()).hexdigest() != decision.get("owner_sha256")):
                        raise ProbeStop("SEMANTICS_GAP")
                    for code in STAGE_B:
                        probe.fetch(code)
                        time.sleep(0.2)
                    terminal = "KR8_PROBE_COMPLETE_OFFLINE_QUALIFICATION_REQUIRED"
                else:
                    terminal = PREFIX + "ESTIMATE_SEMANTICS_GAP"
            probe.save("all-results.json", probe.results)
        except ProbeStop as exc:
            terminal = PREFIX + str(exc)
        finally:
            probe.save("request-counters.json", probe.counters())
            probe.save("probe-terminal.json", {"terminal": terminal, "ended_at": now()})
            probe.token = None
            print(terminal, json.dumps(probe.counters()), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    args = parser.parse_args()
    try:
        run(args.output, args.env_file)
    except ProbeStop as exc:
        print(PREFIX + str(exc), flush=True)
        raise SystemExit(2) from None
    except Exception:
        # A settings/transport traceback can carry credential input. Never emit it.
        print(PREFIX + "SANITIZED_CONTROLLER_FAILURE", flush=True)
        raise SystemExit(2) from None
