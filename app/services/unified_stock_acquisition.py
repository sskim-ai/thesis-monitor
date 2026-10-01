"""Source-only stock acquisition plan and offline coverage gate. Never registered live."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import Field, model_validator

from app.services.market_session import market_session_for_ticker
from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import ContractModel, digest
from app.services.unified_source_policy import UnifiedSourcePolicy


UNIVERSE = {
    "us": ("CORZ", "CPNG", "CRCL", "GOOGL", "HUT", "IBM", "MU", "RXRX", "SKHY",
           "SNDK", "TSLA", "TSM", "WRD", "WULF"),
    "kr": ("000660", "003690", "005490", "005930", "010120", "012450", "047810", "086280"),
}
ROLES = {"adjusted_daily": ("daily", True), "adjusted_weekly": ("weekly", True),
         "adjusted_monthly": ("monthly", True), "unadjusted_weekly_valuation": ("weekly", False)}
API_IDS = {"us": {"daily": "usa06012", "weekly": "usa06013", "monthly": "usa06014"},
           "kr": {"daily": "ka10081", "weekly": "ka10082", "monthly": "ka10083"}}
PROVIDER = UnifiedSourcePolicy(frozenset({"kiwoom"}))


class StockRead(ContractModel):
    entry_id: str
    market: Literal["us", "kr"]
    subject: str
    canonical_security_id: str = Field(min_length=1)
    provider: Literal["kiwoom"] = "kiwoom"
    owner: Literal["ohlcv_analyst.KiwoomProvider.get_bars"] = "ohlcv_analyst.KiwoomProvider.get_bars"
    exchange: str
    route: str
    api_id: str
    role: str
    timeframe: Literal["daily", "weekly", "monthly"]
    adjusted: bool
    count: int = Field(ge=1, le=1000)
    max_pages: int = Field(ge=1, le=12)
    query_date: str
    latest_completed_session: str
    market_state: str
    query_semantics: Literal["LATEST_AVAILABLE_SOURCE_ROWS_NO_DATE_RELABEL"] = (
        "LATEST_AVAILABLE_SOURCE_ROWS_NO_DATE_RELABEL")

    @model_validator(mode="after")
    def identity(self):
        if self.subject not in UNIVERSE[self.market]:
            raise ValueError("stock_subject_not_authorized")
        if self.entry_id != f"{self.market}:{self.subject}:{self.role}":
            raise ValueError("stock_role_identity_mismatch")
        if ROLES.get(self.role) != (self.timeframe, self.adjusted):
            raise ValueError("stock_role_basis_mismatch")
        route = "/api/us/chart" if self.market == "us" else "/api/dostk/chart"
        if self.route != route or self.api_id != API_IDS[self.market][self.timeframe]:
            raise ValueError("stock_role_endpoint_mismatch")
        allowed = {"ND", "NY", "NA"} if self.market == "us" else {"KRX", "KOSPI", "KOSDAQ"}
        if self.exchange not in allowed:
            raise ValueError("stock_exchange_not_declared")
        pages = min(12, self.count // 100 + 2) if self.market == "us" else min(10, self.count // 200 + 2)
        if self.max_pages != pages:
            raise ValueError("stock_pagination_budget_mismatch")
        return self


class StockPlan(ContractModel):
    contract: Literal["one-shot-stock-source-acquisition-v1", "one-shot-kr8-source-acquisition-v1"] = "one-shot-stock-source-acquisition-v1"
    run_id: str = Field(min_length=1)
    acquisition_id: str = Field(min_length=1)
    frozen_at: datetime
    instruction_sha: str = Field(pattern=r"^[a-f0-9]{40}$")
    implementation_sha: str = Field(pattern=r"^[a-f0-9]{40}$")
    universe_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    owner_files: dict[str, str]
    owner_head: str
    settings_sha256: str
    request_environment_sha256: str
    reads: tuple[StockRead, ...]
    automatic_retries: Literal[0] = 0
    maximum_auth_requests: Literal[1] = 1

    @property
    def universe(self):
        return {"kr": UNIVERSE["kr"]} if self.contract == "one-shot-kr8-source-acquisition-v1" else UNIVERSE

    @model_validator(mode="after")
    def complete(self):
        expected = {f"{market}:{ticker}:{role}" for market, tickers in self.universe.items()
                    for ticker in tickers for role in ROLES}
        if len(self.reads) != len(expected) or {r.entry_id for r in self.reads} != expected:
            raise ValueError("exact_88_stock_plan_required")
        if self.frozen_at.tzinfo is None or not self.owner_files:
            raise ValueError("stock_plan_owner_time_required")
        return self


def make_reads(universe: dict, identities: dict, *, at: datetime, counts: dict,
               kr_only: bool = False) -> tuple[StockRead, ...]:
    selected = {"kr": UNIVERSE["kr"]} if kr_only else UNIVERSE
    if kr_only and set(universe) != {"kr"}:
        raise ValueError("kr8_exact_market_scope_required")
    for market, expected in selected.items():
        if tuple(sorted(universe[market]["eligible_subjects"])) != expected:
            raise ValueError(f"canonical_universe_mismatch:{market}")
    reads = []
    for market, tickers in selected.items():
        for subject in tickers:
            identity = identities[subject]
            exchange = identity["exchange"]
            if market == "us":
                exchange = {"NASDAQ": "ND", "NYSE": "NY", "AMEX": "NA"}.get(exchange)
            state = market_session_for_ticker(subject, at)
            for role, (period, adjusted) in ROLES.items():
                count = counts[market][role]
                reads.append(StockRead(entry_id=f"{market}:{subject}:{role}", market=market,
                    subject=subject, canonical_security_id=identity["canonical_security_id"],
                    exchange=exchange, route="/api/us/chart" if market == "us" else "/api/dostk/chart",
                    api_id=API_IDS[market][period], role=role, timeframe=period, adjusted=adjusted,
                    count=count, max_pages=min(12, count // 100 + 2) if market == "us" else min(10, count // 200 + 2),
                    query_date=at.astimezone(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d"),
                    latest_completed_session=state.latest_completed_regular_session_date.isoformat(),
                    market_state=state.session))
    return tuple(reads)


def bound_artifact(root: Path, path: str, sha: str) -> bytes:
    relative = Path(path)
    target = root / relative
    if relative.is_absolute() or ".." in relative.parts or any(
        p.is_symlink() for p in (target, *target.parents)
    ):
        raise ValueError("stock_artifact_path_invalid")
    data = target.read_bytes()
    if sha256_bytes(data) != sha:
        raise ValueError("stock_artifact_hash_mismatch")
    return data


def load_owned_role(plan: StockPlan, read: StockRead, receipt: dict, root: Path) -> list[dict]:
    """Verify receipt/source ownership without conflating it with consumer eligibility.

    Raw-page replay remains an additional proof. Returned rows are never repaired.
    """
    return decode_owned_role(plan, read, receipt,
        lambda path, sha: bound_artifact(root, path, sha))


def decode_owned_role(plan: StockPlan, read: StockRead, receipt: dict, artifact_reader) -> list[dict]:
    """Same receipt checks, with caller-owned byte inputs for pure assembly."""
    import json

    if receipt["run_id"] != plan.run_id or receipt["acquisition_id"] != plan.acquisition_id:
        raise ValueError("stock_prior_run_receipt")
    if receipt["plan_sha256"] != digest(plan.model_dump(mode="json")):
        raise ValueError("stock_plan_receipt_mismatch")
    if receipt["entry"] != read.model_dump(mode="json"):
        raise ValueError("stock_role_receipt_mismatch")
    start, end = (datetime.fromisoformat(receipt[k]) for k in ("started_at", "completed_at"))
    if not start.tzinfo or not end.tzinfo or not plan.frozen_at <= start <= end:
        raise ValueError("stock_receipt_time_mismatch")
    if receipt["status"] != "CAPTURED" or not receipt["pages"]:
        raise ValueError(receipt.get("error_class") or "stock_source_role_unavailable")
    if len(receipt["pages"]) > read.max_pages:
        raise ValueError("stock_page_budget_exceeded")
    for ordinal, page in enumerate(receipt["pages"], 1):
        PROVIDER.require(page["provider"])
        if page["entry_id"] != read.entry_id or page["page_ordinal"] != ordinal:
            raise ValueError("stock_page_ownership_mismatch")
        request = page["request"]
        if request["route"] != read.route or request["api_id"] != read.api_id:
            raise ValueError("stock_page_endpoint_mismatch")
        payload = request["payload"]
        if payload.get("stk_cd") != read.subject or payload.get("upd_stkpc_tp") != str(int(read.adjusted)):
            raise ValueError("stock_page_symbol_basis_mismatch")
        if read.market == "us" and payload.get("stex_tp") != read.exchange:
            raise ValueError("stock_page_exchange_mismatch")
        if page["request_sha256"] != digest(request):
            raise ValueError("stock_request_hash_mismatch")
        if not start <= datetime.fromisoformat(page["requested_at"]) <= datetime.fromisoformat(page["received_at"]) <= end:
            raise ValueError("stock_page_time_mismatch")
        raw = artifact_reader(page["artifact"], page["source_sha256"])
        data = json.loads(raw)
        PROVIDER.check_lineage(data)
        if page["http_status"] != 200 or str(data.get("return_code", "0")) not in {"0", ""}:
            raise ValueError("stock_source_error_response")
    bars = json.loads(artifact_reader(receipt["normalized_artifact"], receipt["normalized_sha256"]))
    if not isinstance(bars, list) or any(not isinstance(bar, dict) for bar in bars):
        raise ValueError("stock_normalized_shape_invalid")
    return bars


def validate_role(plan: StockPlan, read: StockRead, receipt: dict, root: Path) -> dict:
    """Historical whole-payload gate, retained for exact R2B0 reproducibility."""
    bars = load_owned_role(plan, read, receipt, root)
    inspection = inspect_normalized_ohlcv_rows(bars, timeframe=read.timeframe,
        cutoff=datetime.fromisoformat(read.latest_completed_session).date())
    if not bars or not inspection.valid:
        raise ValueError("stock_ohlcv_integrity_failed")
    dates = [str(bar["date"]) for bar in bars]
    if max(dates) > read.latest_completed_session:
        raise ValueError("stock_returned_future_session")
    return {"entry_id": read.entry_id, "status": "PASS", "rows": len(bars),
            "first_row_date": min(dates), "last_row_date": max(dates),
            "completed_session": read.latest_completed_session,
            "current_session_aligned": max(dates) == read.latest_completed_session,
            "session_policy": read.query_semantics, "date_relabel_count": 0,
            "validator_contract": inspection.contract,
            "validator_fingerprint": inspection.payload_fingerprint,
            "normalized_sha256": receipt["normalized_sha256"], "source_pages": len(receipt["pages"])}


def coverage(plan: StockPlan, rows: list[dict]) -> dict:
    expected = {r.entry_id for r in plan.reads}
    if len(rows) != 88 or {r["entry_id"] for r in rows} != expected:
        raise ValueError("exact_88_result_coverage_required")
    passed = sum(r["status"] == "PASS" for r in rows)
    return {"attempted": 88, "usable": passed, "failed": 88 - passed,
            "complete": passed == 88, "stock_materialization_allowed": passed == 88,
            "rows": rows}
