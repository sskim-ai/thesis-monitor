"""Run-owned data reads, reused unchanged across price attempts; no activation."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import httpx
from pydantic import Field

from app.services.unified_run_artifacts import durable_json
from app.services.unified_snapshot_contract import ContractModel, digest
from app.services.unified_source_observer import _secret_field, capture_source_response
from app.services.unified_source_policy import UnifiedSourcePolicy


class RunRead(ContractModel):
    key: str
    route: str
    params: dict[str, str]
    max_requests: int = Field(ge=1, le=10)


class RunAcquisitionObserver:
    def __init__(self, *, root: Path, run_id: str, acquisition_id: str,
                 provider: str, role: str, reads: tuple[RunRead, ...],
                 policy: UnifiedSourcePolicy):
        policy.require(provider)
        if not run_id or not acquisition_id or not role or not reads or root.exists():
            raise ValueError("new_run_acquisition_required")
        if any(p.is_symlink() for p in (root, *root.parents)):
            raise ValueError("source_artifact_symlink")
        if len({r.key for r in reads}) != len(reads) or len({
            digest([r.route, r.params]) for r in reads}) != len(reads):
            raise ValueError("duplicate_run_read")
        for read in reads:
            if "?" in read.route or "@" in read.route or _secret_field(read.params):
                raise ValueError("run_read_secret_risk")
        self.root, self.run_id, self.acquisition_id = root, run_id, acquisition_id
        self.provider, self.role, self.policy = provider, role, policy
        self._plan = json.dumps([r.model_dump(mode="json") for r in reads], sort_keys=True)
        self._counts: dict[str, int] = {}
        self._receipts: list[dict] = []
        self._ordinal = 0
        self._open = False
        self._used = False
        durable_json(root / "plan.json", {**self.identity, "reads": json.loads(self._plan)},
                     exclusive=True)

    @property
    def identity(self) -> dict:
        return {"run_id": self.run_id, "acquisition_id": self.acquisition_id,
                "acquisition_class": "RUN_FRESH_ONCE", "provider": self.provider,
                "role": self.role}

    def begin(self, *, provider: str, role: str) -> None:
        if self._used or (provider, role) != (self.provider, self.role):
            raise ValueError("run_acquisition_identity_or_reuse_mismatch")
        self._used, self._open = True, True

    async def get(self, client: httpx.AsyncClient, route: str, *, params: dict | None = None,
                  credential_params: dict | None = None) -> httpx.Response:
        if not self._open:
            raise ValueError("run_acquisition_not_open")
        selected = [RunRead.model_validate(r) for r in json.loads(self._plan)
                    if r["route"] == route and r["params"] == (params or {})]
        if len(selected) != 1:
            raise ValueError("source_request_outside_frozen_plan")
        read = selected[0]
        if credential_params and not (self.provider == "finnhub_earnings"
                                     and set(credential_params) == {"token"}):
            raise ValueError("source_credentials_not_authorized")
        count = self._counts.get(read.key, 0) + 1
        if count > read.max_requests:
            raise ValueError("source_request_budget_exhausted")
        self._counts[read.key] = count
        self._ordinal += 1
        identity = f"read-{self._ordinal:04d}"
        request = {"method": "GET", "route": route, "params": params or {}}
        receipt = {**self.identity, "ordinal": self._ordinal, "read_key": read.key,
                   "request": request, "request_sha256": digest(request),
                   "requested_at": datetime.now(timezone.utc).isoformat()}
        try:
            response = await capture_source_response(root=self.root, identity=identity,
                receipt=receipt, send=lambda: client.get(route,
                    params={**(params or {}), **(credential_params or {})}, follow_redirects=False))
        finally:
            path = self.root / f"{identity}.response.json"
            self._receipts.append({"artifact": path.name,
                "receipt": json.loads(path.read_bytes()) if path.exists() else None})
        return response

    def finish(self, *, normalized: dict | None, contract: str, fingerprint: str,
               denial: str | None = None) -> dict:
        if not self._open:
            raise ValueError("run_acquisition_not_open")
        self._open = False
        if normalized is not None:
            self.policy.check_lineage(normalized)
        if not self._receipts and denial is None:
            raise ValueError("run_acquisition_without_source")
        value = {**self.identity, "reads": self._receipts,
            "reads_sha256": digest(self._receipts), "normalized": normalized,
            "normalized_sha256": digest(normalized) if normalized is not None else None,
            "validator_contract": contract, "validator_fingerprint": fingerprint,
            "denial": denial, "status": "OWNER_NORMALIZED" if denial is None else "UNAVAILABLE",
            "qualification": "OWNER_INTERFACE_ONLY_NOT_SOURCE_ADAPTER"}
        durable_json(self.root / "normalization.json", value, exclusive=True)
        return value
