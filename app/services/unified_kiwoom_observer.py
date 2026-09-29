"""Opt-in market-data receipt ownership; never observes OAuth or account APIs."""

from __future__ import annotations

from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path

import httpx
from pydantic import Field, model_validator

from app.services.unified_run_artifacts import durable_json
from app.services.unified_snapshot_contract import ContractModel, digest
from app.services.unified_source_observer import capture_source_response
from app.services.unified_source_policy import UnifiedSourcePolicy


class KiwoomRead(ContractModel):
    key: str
    role: str
    api_id: str
    body: dict[str, str]
    mandatory: bool
    max_pages: int = Field(ge=1, le=100)
    max_requests_per_page: int = Field(ge=1, le=10)

    @model_validator(mode="after")
    def market_only(self):
        fields = {
            "ka20001": {"mrkt_tp", "inds_cd"}, "ka20003": {"inds_cd"},
            "ka20009": {"mrkt_tp", "inds_cd"},
            "ka10051": {"mrkt_tp", "amt_qty_tp", "base_dt", "stex_tp"},
            "ka10066": {"mrkt_tp", "amt_qty_tp", "trde_tp", "stex_tp"},
        }
        if self.api_id not in fields or set(self.body) != fields[self.api_id]:
            raise ValueError("kiwoom_market_read_not_authorized")
        if self.api_id != "ka10066" and self.max_pages != 1:
            raise ValueError("kiwoom_pagination_not_declared")
        expected_role = ("kr_market_investor_flows" if self.api_id in {"ka10051", "ka10066"}
                         else "kr_local_indices_sectors_breadth")
        if self.role != expected_role or self.mandatory != (self.api_id.startswith("ka2")):
            raise ValueError("kiwoom_role_classification_mismatch")
        return self

    @property
    def endpoint(self) -> str:
        return "/api/dostk/mrkcond" if self.api_id == "ka10066" else "/api/dostk/sect"


class KiwoomReceiptObserver:
    def __init__(self, *, root: Path, run_id: str, attempt_id: str, session_date: date,
                 reads: tuple[KiwoomRead, ...], policy: UnifiedSourcePolicy,
                 completed_session_only: bool = False):
        policy.require("kiwoom_rest")
        if not run_id or not attempt_id or not reads or root.exists():
            raise ValueError("new_source_attempt_root_and_identity_required")
        if any(p.is_symlink() for p in (root, *root.parents)):
            raise ValueError("source_artifact_symlink")
        if len({r.key for r in reads}) != len(reads) or len({
            digest([r.api_id, r.body]) for r in reads
        }) != len(reads):
            raise ValueError("duplicate_source_read_identity")
        self.root, self.run_id, self.attempt_id = root, run_id, attempt_id
        self.session_date, self.policy = session_date, policy
        self.completed_session_only = completed_session_only
        self._plan = json.dumps([r.model_dump(mode="json") for r in reads], sort_keys=True)
        self._ordinal = 0
        self._counts: dict[tuple[str, int], int] = {}
        self._pages: dict[str, list[dict]] = {}
        self._cursors: dict[str, str | None] = {}
        self._pending: dict[str, dict] = {}
        self._started = False
        self._finished = False
        durable_json(root / "plan.json", {"run_id": run_id, "attempt_id": attempt_id,
            "acquisition_class": "ATTEMPT_FRESH", "session": session_date.isoformat(),
            "provider": "kiwoom_rest", "reads": json.loads(self._plan),
            **({"completed_session_only": True} if completed_session_only else {})}, exclusive=True)

    @property
    def reads(self) -> tuple[KiwoomRead, ...]:
        return tuple(KiwoomRead.model_validate(r) for r in json.loads(self._plan))

    def begin(self, session_date: date, observed_at: datetime) -> None:
        if self._started or self._ordinal or session_date != self.session_date:
            raise ValueError("kiwoom_new_whole_attempt_required")
        if observed_at.utcoffset() is None:
            raise ValueError("source_timezone_required")
        self._started = True

    def preflight(self, endpoint: str, api_id: str, body: dict,
                  continuation: bool, next_key: str) -> KiwoomRead:
        if not self._started or self._finished:
            raise ValueError("kiwoom_collection_not_open")
        selected = [r for r in self.reads if (r.endpoint, r.api_id, r.body) ==
                    (endpoint, api_id, body)]
        if len(selected) != 1:
            raise ValueError("source_request_outside_frozen_plan")
        read = selected[0]
        cursor = self._cursors.get(read.key, "")
        if cursor is None or continuation != bool(cursor) or next_key != cursor:
            raise ValueError("kiwoom_page_chain_mismatch")
        page = len(self._pages.get(read.key, [])) + 1
        if page > read.max_pages or self._counts.get((read.key, page), 0) >= read.max_requests_per_page:
            raise ValueError("source_request_budget_exhausted")
        return read

    async def post(self, client: httpx.AsyncClient, *, endpoint: str, api_id: str,
                   body: dict, headers: dict, continuation: bool, next_key: str) -> httpx.Response:
        read = self.preflight(endpoint, api_id, body, continuation, next_key)
        page = len(self._pages.get(read.key, [])) + 1
        count = self._counts.get((read.key, page), 0) + 1
        self._counts[read.key, page] = count
        self._ordinal += 1
        identity = f"read-{self._ordinal:04d}"
        # Pagination cursors are bound by hash. Authorization is never serialized.
        request = {"method": "POST", "route": endpoint, "api_id": api_id, "body": body,
                   "page": page, "continuation": continuation,
                   "cursor_sha256": hashlib.sha256(next_key.encode()).hexdigest()}
        receipt = {"run_id": self.run_id, "attempt_id": self.attempt_id,
            "acquisition_class": "ATTEMPT_FRESH", "ordinal": self._ordinal,
            "role_ordinal": count, "role": read.role, "read_key": read.key,
            "market": "kr", "provider": "kiwoom_rest", "session": self.session_date.isoformat(),
            "request": request, "request_sha256": digest(request),
            "requested_at": datetime.now(timezone.utc).isoformat()}
        response = await capture_source_response(root=self.root, identity=identity, receipt=receipt,
            send=lambda: client.post(endpoint, json=body, headers=headers))
        self._pending[identity] = response.extensions["unified_source_receipt"][1]
        return response

    def accept_page(self, response: httpx.Response, *, continuation: bool, next_key: str) -> None:
        identity, receipt = response.extensions["unified_source_receipt"]
        if self._pending.pop(identity, None) != receipt or receipt["attempt_id"] != self.attempt_id:
            raise ValueError("kiwoom_foreign_or_consumed_response")
        if not 200 <= response.status_code < 300 or receipt["artifact_sha256"] != hashlib.sha256(
            response.content
        ).hexdigest():
            raise ValueError("kiwoom_response_binding_mismatch")
        payload = response.json()
        self.policy.check_lineage(payload)
        if int(payload.get("return_code", 0)) != 0 or (continuation and not next_key):
            raise ValueError("kiwoom_page_not_accepted")
        key = receipt["read_key"]
        pages = self._pages.setdefault(key, [])
        if receipt["request"]["page"] != len(pages) + 1:
            raise ValueError("kiwoom_page_order_mismatch")
        accepted = {"response_receipt_sha256": digest(receipt),
                    "raw_sha256": receipt["artifact_sha256"], "identity": identity,
                    "page": len(pages) + 1, "continuation": continuation,
                    "next_cursor_sha256": hashlib.sha256(next_key.encode()).hexdigest()}
        durable_json(self.root / f"{identity}.page.json", accepted, exclusive=True)
        pages.append(accepted)
        self._cursors[key] = next_key if continuation else None

    def finish(self, *, collection=None, denial: str | None = None) -> None:
        if self._finished:
            raise ValueError("kiwoom_collection_already_finished")
        self._finished = True
        incomplete = [r.key for r in self.reads if self._cursors.get(r.key, "") is not None]
        consumed_completion = {}
        if self.completed_session_only and collection is not None and denial is None:
            from app.services.kiwoom_consumed_page_contract import read_dependencies
            for read in self.reads:
                if read.api_id not in {"ka20001", "ka20009"}:
                    continue
                pages = self._pages.get(read.key, [])
                bodies = [json.loads((self.root / (p["identity"] + ".body")).read_bytes()) for p in pages]
                consumed_completion[read.key] = read_dependencies(read.api_id, bodies,
                    session=self.session_date, continuation=[p["continuation"] for p in pages])
        mandatory_incomplete = [r.key for r in self.reads if r.mandatory and r.key in incomplete
                                and r.key not in consumed_completion]
        values = None if collection is None else collection.cross_section.model_dump(mode="json")
        if values is not None:
            self.policy.check_lineage(values)
        local_ok = collection is not None and not mandatory_incomplete and denial is None
        flow_ok = local_ok and not incomplete and not collection.audit.blocked_concentration_markets
        role_values = {
            "kr_local_indices_sectors_breadth": (
                {k: values[k] for k in ("indices", "sectors", "breadth", "breadth_by_scope")}
                if local_ok else None),
            "kr_market_investor_flows": (
                {k: values[k] for k in ("market_flows", "concentration")} if flow_ok else None),
        }
        durable_json(self.root / "normalization.json", {
            "run_id": self.run_id, "attempt_id": self.attempt_id,
            "provider": "kiwoom_rest", "session": self.session_date.isoformat(),
            "page_sets": self._pages, "page_sets_sha256": digest(self._pages),
            "missing_reads": incomplete, "mandatory_complete": local_ok,
            **({"consumer_completion": consumed_completion} if self.completed_session_only else {}),
            "denial": denial, "roles": {role: {"value": value,
                "value_sha256": digest(value) if value is not None else None,
                "status": "AVAILABLE" if value is not None else "FAILED_CLOSED" if
                role == "kr_local_indices_sectors_breadth" else "OPTIONAL_UNAVAILABLE"}
                for role, value in role_values.items()},
            "owner_audit": collection.audit.model_dump(mode="json") if collection else None,
            "validator_contracts": ["kiwoom-kr-market-context-v1", "kr-market-flow-reconciliation-v1"],
            "qualification": "OWNER_INTERFACE_ONLY_NOT_SOURCE_ADAPTER",
        }, exclusive=True)
