"""Isolated production OHLCV-owner worker; no application DB, AI, or service mutation.

The original Kiwoom provider owns pagination and normalization. A process-local
transport boundary permits only the frozen chart role and one credential exchange.
It captures original response bytes before the owner parses them.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

import httpx


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def save(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def write(path: Path, value):
    save(path, encoded(value) + b"\n")


def now():
    return datetime.now(timezone.utc).isoformat()


SECRET = re.compile(r"token|password|secret|credential|api.?key|authorization|chat.?id", re.I)


def contains_secret_field(value):
    if isinstance(value, dict):
        return any(SECRET.search(str(k)) or contains_secret_field(v) for k, v in value.items())
    return isinstance(value, list) and any(contains_secret_field(v) for v in value)


class WireBoundary:
    def __init__(self, *, root: Path, plan: dict, client, secrets: tuple[str, ...]):
        self.root, self.plan, self.client, self.secrets = root, plan, client, secrets
        self.active = None
        self.pages = []
        self.auth_calls = self.data_calls = 0
        self.page_number = 0
        self.last_continuation = None
        self._consumed_roles = set()
        self._continuations = set()

    def begin(self, entry):
        if entry not in self.plan["reads"] or entry["entry_id"] in self._consumed_roles:
            raise ValueError("unplanned_or_repeated_logical_role")
        self._consumed_roles.add(entry["entry_id"])
        self.active, self.pages, self.page_number, self.last_continuation = entry, [], 0, None
        self._continuations = set()

    def post(self, url, *, json, headers, timeout):
        if url == "https://api.kiwoom.com/oauth2/token":
            if self.auth_calls or self.active is None:
                raise ValueError("auth_budget_exhausted")
            self.auth_calls += 1
            record = {"external_ordinal": self.auth_calls + self.data_calls,
                      "request_kind": "AUTH", "requested_at": now(),
                      "request_body_and_response_not_exported": True}
            write(self.root / "auth-intent.json", record)
            try:
                response = self.client.post(url, json=json, headers=headers, timeout=timeout)
                record.update(http_status=response.status_code, status="HTTP_RESPONSE")
                try:
                    token = response.json().get("token")
                    if token:
                        self.secrets = (*self.secrets, token)
                except ValueError:
                    pass
                return response
            except httpx.HTTPError as exc:
                record.update(status="TRANSPORT_ERROR", error_class=type(exc).__name__)
                raise
            finally:
                record["received_at"] = now()
                write(self.root / "auth-response.json", record)
        entry = self.active
        if entry is None or url != "https://api.kiwoom.com" + entry["route"]:
            raise ValueError("undeclared_provider_or_endpoint_denied")
        expected = {"stk_cd": entry["subject"], "upd_stkpc_tp": str(int(entry["adjusted"]))}
        if entry["market"] == "us":
            expected.update(stex_tp=entry["exchange"], strt_dt="", exrt_appl_tp="0")
        else:
            expected["base_dt"] = entry["query_date"]
        if json != expected or headers.get("api-id") != entry["api_id"]:
            raise ValueError("request_not_in_frozen_role")
        continuation = {"cont_yn": headers.get("cont-yn"), "next_key": headers.get("next-key")}
        if self.page_number == 0:
            if continuation != {"cont_yn": "N", "next_key": ""}:
                raise ValueError("first_page_continuation_invalid")
        elif self.last_continuation != continuation or continuation["cont_yn"] != "Y" or not continuation["next_key"]:
            raise ValueError("retry_or_undeclared_pagination_denied")
        if continuation["next_key"] in self._continuations:
            raise ValueError("repeated_pagination_denied")
        if self.page_number >= entry["max_pages"]:
            raise ValueError("page_budget_exhausted")
        self.page_number += 1
        self._continuations.add(continuation["next_key"])
        self.data_calls += 1
        identity = f"transport-{self.data_calls:04d}"
        request = {"method": "POST", "route": entry["route"], "api_id": entry["api_id"],
                   "payload": json, "continuation": continuation}
        record = {"run_id": self.plan["run_id"], "acquisition_id": self.plan["acquisition_id"],
                  "entry_id": entry["entry_id"], "provider": "kiwoom",
                  "external_ordinal": self.auth_calls + self.data_calls,
                  "data_ordinal": self.data_calls, "page_ordinal": self.page_number,
                  "request": request, "request_sha256": sha(encoded(request)), "requested_at": now()}
        write(self.root / (identity + ".intent.json"), record)
        try:
            response = self.client.post(url, json=json, headers=headers, timeout=timeout)
            raw = response.content
            record.update(http_status=response.status_code, received_at=now())
            try:
                secret_fields = contains_secret_field(response.json())
            except ValueError:
                secret_fields = False
            if secret_fields or any(s.encode() in raw for s in self.secrets if s):
                record.update(status="BODY_WITHHELD_SECRET_RISK")
                raise ValueError("source_body_secret_risk")
            record.update(artifact=identity + ".body", source_sha256=sha(raw), status="HTTP_RESPONSE")
            # Only chart pagination headers are retained; auth and generic headers never leave memory.
            try:
                body = response.json()
                body = body if isinstance(body, dict) else {}
            except ValueError:
                body = {}
            self.last_continuation = {
                "cont_yn": str(response.headers.get("cont-yn") or body.get("cont-yn") or body.get("cont_yn") or "N"),
                "next_key": str(response.headers.get("next-key") or body.get("next-key") or body.get("next_key") or ""),
            }
            record["response_continuation"] = self.last_continuation
            save(self.root / record["artifact"], raw)
            return response
        except httpx.HTTPError as exc:
            record.update(status="TRANSPORT_ERROR", error_class=type(exc).__name__, received_at=now())
            raise
        finally:
            record.setdefault("received_at", now())
            self.pages.append(record.copy())
            write(self.root / (identity + ".response.json"), record)


def owner_configuration(owner_root, settings):
    names = subprocess.check_output(["git", "ls-files", "app"], cwd=owner_root, text=True).splitlines()
    values = settings.model_dump(mode="json")
    return {
        "owner_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=owner_root, text=True).strip(),
        "owner_clean": not subprocess.check_output(["git", "status", "--porcelain"], cwd=owner_root, text=True).strip(),
        "owner_files": {name: sha((owner_root / name).read_bytes()) for name in names},
        "settings_sha256": sha(encoded(values)),
        "request_environment_sha256": sha(encoded({key: os.environ.get(key) for key in
            ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "SSL_CERT_FILE", "SSL_CERT_DIR")})),
        "base_url": settings.kiwoom_base_url, "live_provider": settings.enable_live_provider,
        "environment": settings.kiwoom_env, "configured_retries": settings.kiwoom_max_retries,
        "configured_timeout_seconds": settings.kiwoom_timeout_seconds,
        "credentials_present": bool(settings.kiwoom_app_key and settings.kiwoom_secret_key),
        "execution_override": {"kiwoom_max_retries": 0},
        "operating_settings_modified": False,
    }


def acquire(plan, root, owner, settings):
    plan_hash = sha(encoded(plan))
    with httpx.Client(transport=httpx.HTTPTransport(retries=0), follow_redirects=False) as client:
        wire = WireBoundary(root=root, plan=plan, client=client,
                            secrets=(settings.kiwoom_app_key, settings.kiwoom_secret_key))
        # Module-local dependency injection in this isolated worker only. Original
        # auth, pagination, rate limiting, error handling, and normalization remain owners.
        owner.httpx = SimpleNamespace(post=wire.post, HTTPError=httpx.HTTPError)
        bounded_settings = settings.model_copy(update={"kiwoom_max_retries": 0})
        provider = owner.KiwoomProvider(owner.KiwoomClient(bounded_settings, owner.KiwoomAuth(bounded_settings)))
        for ordinal, entry in enumerate(plan["reads"], 1):
            wire.begin(entry)
            receipt = {"run_id": plan["run_id"], "acquisition_id": plan["acquisition_id"],
                       "plan_sha256": plan_hash, "entry": entry, "logical_ordinal": ordinal,
                       "started_at": now()}
            write(root / f"role-{ordinal:03d}.intent.json", receipt)
            try:
                bars = provider.get_bars(code=entry["subject"], period=entry["timeframe"],
                    count=entry["count"], adjusted=entry["adjusted"], exchange=entry["exchange"])
                data = encoded(bars)
                path = f"role-{ordinal:03d}.normalized.json"
                save(root / path, data)
                receipt.update(status="CAPTURED", normalized_artifact=path, normalized_sha256=sha(data))
            except Exception as exc:
                # Exact error identity and original data error bodies are retained;
                # arbitrary exception messages can contain auth values or URLs.
                receipt.update(status="FAILED", error_class=type(exc).__name__,
                    error_message_sha256=sha(str(exc).encode()),
                    error_code=str(exc) if isinstance(exc, ValueError) and re.fullmatch(r"[a-z_]+", str(exc)) else None)
            receipt.update(completed_at=now(), pages=wire.pages)
            write(root / f"role-{ordinal:03d}.receipt.json", receipt)
            print(json.dumps({"logical": ordinal, "subject": entry["subject"],
                "role": entry["role"], "status": receipt["status"], "pages": len(wire.pages)}), flush=True)
        write(root / "transport-counts.json", {"logical_roles_attempted": len(plan['reads']),
            "provider_data_requests": wire.data_calls, "auth_requests": wire.auth_calls,
            "external_transport_requests": wire.data_calls + wire.auth_calls,
            "automatic_retries": 0, "alpha_vantage_calls": 0, "massive_calls": 0,
            "fallback_calls": 0, "symbol_discovery_calls": 0, "investor_flow_calls": 0,
            "model_calls": 0, "rendered_messages": 0, "telegram_sends": 0,
            "production_db_writes": 0, "scheduler_mutations": 0})


def replay(plan, root, owner):
    results = []
    for ordinal, entry in enumerate(plan["reads"], 1):
        receipt = json.loads((root / f"role-{ordinal:03d}.receipt.json").read_bytes())
        if receipt["status"] != "CAPTURED":
            results.append({"entry_id": entry["entry_id"], "status": "NOT_REACHED_SOURCE_FAILED"})
            continue

        class ReplayClient:
            index = 0

            def post(self, route, api_id, payload, *, cont_yn="N", next_key=""):
                page = receipt["pages"][self.index]
                self.index += 1
                request = {"method": "POST", "route": route, "api_id": api_id, "payload": payload,
                           "continuation": {"cont_yn": cont_yn, "next_key": next_key}}
                if request != page["request"]:
                    raise ValueError("offline_owner_request_mismatch")
                path = Path(page["artifact"])
                if path.is_absolute() or ".." in path.parts or (root / path).is_symlink():
                    raise ValueError("offline_owner_path_invalid")
                raw = (root / path).read_bytes()
                if sha(raw) != page["source_sha256"]:
                    raise ValueError("offline_source_hash_mismatch")
                data = json.loads(raw)
                continuation = page["response_continuation"]
                data["_headers"] = {"cont-yn": continuation["cont_yn"], "next-key": continuation["next_key"]}
                return data

        class ReplayDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime.strptime(entry["query_date"], "%Y%m%d")

        owner.datetime = ReplayDateTime
        client = ReplayClient()
        try:
            bars = owner.KiwoomProvider(client).get_bars(code=entry["subject"], period=entry["timeframe"],
                count=entry["count"], adjusted=entry["adjusted"], exchange=entry["exchange"])
            if client.index != len(receipt["pages"]) or sha(encoded(bars)) != receipt["normalized_sha256"]:
                raise ValueError("offline_owner_normalization_mismatch")
            results.append({"entry_id": entry["entry_id"], "status": "PASS",
                            "normalized_sha256": sha(encoded(bars)), "network_calls": 0})
        except Exception as exc:
            results.append({"entry_id": entry["entry_id"], "status": "FAIL", "error_class": type(exc).__name__})
    write(root.parent / "raw-owner-replay.json", results)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("inspect", "acquire", "replay"))
    parser.add_argument("--owner-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--plan-sha256")
    args = parser.parse_args()
    sys.path.insert(0, str(args.owner_root))
    from app.config import Settings
    from app.providers import kiwoom as owner

    settings = Settings(_env_file=args.owner_root / ".env")
    config = owner_configuration(args.owner_root, settings)
    if args.mode == "inspect":
        write(args.output, config)
        return
    raw = args.plan.read_bytes()
    if sha(raw) != args.plan_sha256:
        raise ValueError("frozen_plan_file_hash_mismatch")
    plan = json.loads(raw)
    for key in ("owner_head", "owner_files", "settings_sha256", "request_environment_sha256"):
        if config[key] != plan[key]:
            raise ValueError("configured_owner_changed_after_freeze")
    if not config["owner_clean"] or not config["live_provider"] or config["environment"] != "real" or config["base_url"] != "https://api.kiwoom.com":
        raise ValueError("configured_production_owner_not_qualified")
    if args.mode == "acquire":
        if args.output.exists():
            raise ValueError("one_shot_output_already_exists")
        args.output.mkdir(parents=True, mode=0o700)
        save(args.output / "frozen-plan.json", raw)
        acquire(plan, args.output, owner, settings)
    else:
        replay(plan, args.output, owner)


if __name__ == "__main__":
    main()
