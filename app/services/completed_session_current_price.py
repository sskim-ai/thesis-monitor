"""Exact completed daily close ownership, independent of technical-series quality."""
from copy import deepcopy
from datetime import date, timedelta
from typing import Literal

from pydantic import Field, model_validator

from app.services.ohlcv_provider_integrity_service import (
    BAR_FIELDS, canonical_fingerprint, inspect_normalized_ohlcv_rows,
)
from app.services.price_structure_wave_fibonacci_v3_service import (
    _calendar_for_range, _latest_completed_session,
)
from app.services.unified_snapshot_contract import ContractModel, digest
from app.services.unified_stock_acquisition import StockPlan, StockRead, decode_owned_role


class CompletedSessionCurrentPriceProjection(ContractModel):
    contract: Literal["completed-session-current-price-v1"] = "completed-session-current-price-v1"
    generation_id: str
    acquisition_id: str
    ticker: str
    canonical_security_id: str
    market: Literal["us", "kr"]
    exchange: str
    currency: Literal["USD", "KRW"]
    source_role: Literal["adjusted_daily"] = "adjusted_daily"
    adjustment_basis: Literal["adjusted_close"] = "adjusted_close"
    target_session: str
    calendar_receipt: dict
    source_plan_sha256: str
    source_receipt_sha256: str
    raw_sha256: list[str]
    normalized_sha256: str
    availability: Literal["AVAILABLE", "UNAVAILABLE"]
    denial_reasons: list[str]
    selected_row: dict | None
    selected_row_fingerprint: str | None
    current_price: float | None = Field(allow_inf_nan=False, gt=0)
    price_as_of: str | None
    target_integrity: dict
    source_integrity: dict
    out_of_scope_rows: list[dict]
    projection_sha256: str

    @model_validator(mode="after")
    def consistent(self):
        value = self.model_dump(mode="json")
        value.pop("projection_sha256")
        if digest(value) != self.projection_sha256:
            raise ValueError("completed_price_projection_hash_mismatch")
        if self.availability == "AVAILABLE":
            row = self.selected_row
            if (not row or self.denial_reasons or not self.target_integrity["valid"]
                    or self.target_integrity["bar_count"] != 1 or self.current_price != float(row["close"])
                    or self.price_as_of != self.target_session or str(row["date"])[:10] != self.target_session
                    or self.selected_row_fingerprint != canonical_fingerprint({k: row.get(k) for k in BAR_FIELDS})):
                raise ValueError("completed_price_available_row_inconsistent")
        elif not self.denial_reasons or any(v is not None for v in
                (self.current_price, self.price_as_of, self.selected_row, self.selected_row_fingerprint)):
            raise ValueError("completed_price_unavailable_value_leakage")
        return self


def project_completed_price(*, plan: StockPlan, read: StockRead, receipt: dict,
                            artifact_reader, security: dict, currency: str,
                            adjustment_basis: str = "adjusted_close") -> CompletedSessionCurrentPriceProjection:
    """Source bindings and frozen calendar are verified before inspecting rows."""
    if read not in plan.reads or read.role != "adjusted_daily" or not read.adjusted or read.timeframe != "daily":
        raise ValueError("completed_price_source_role_mismatch")
    exchange = {"NASDAQ": "ND", "NYSE": "NY", "AMEX": "NA"}.get(security.get("exchange"), security.get("exchange"))
    if (security.get("ticker") != read.subject or security.get("canonical_security_id") != read.canonical_security_id
            or exchange != read.exchange or currency != {"us": "USD", "kr": "KRW"}[read.market]
            or adjustment_basis != "adjusted_close"):
        raise ValueError("completed_price_security_currency_basis_mismatch")
    target = date.fromisoformat(read.latest_completed_session)
    name, calendar = _calendar_for_range(read.market.upper(), start=target - timedelta(days=14),
                                        end=max(target, plan.frozen_at.date()) + timedelta(days=7))
    if _latest_completed_session(calendar, plan.frozen_at) != target:
        raise ValueError("completed_price_frozen_calendar_target_mismatch")
    calendar_receipt = dict(calendar=name, exchange=read.exchange, frozen_at=plan.frozen_at.isoformat(),
                            latest_completed_session=target.isoformat())
    calendar_receipt["sha256"] = digest(calendar_receipt)
    rows = decode_owned_role(plan, read, receipt, artifact_reader)
    inspection = inspect_normalized_ohlcv_rows(rows, timeframe="daily", cutoff=target)
    selected, excluded, errors = [], [], []
    for row in rows:
        fingerprint = canonical_fingerprint({k: row.get(k) for k in BAR_FIELDS})
        issues = [i.model_dump(mode="json") for i in inspection.issues if i.row_fingerprint == fingerprint]
        try:
            day = date.fromisoformat(str(row.get("date") or "")[:10])
        except ValueError:
            errors.append("UNKNOWN_ROW_SESSION_SCOPE")
            scope = "UNRESOLVED_SESSION_SCOPE"
        else:
            if day == target:
                selected.append(row)
                continue
            scope = "OUT_OF_SCOPE_LATER_SESSION" if day > target else "OUT_OF_SCOPE_HISTORICAL_SESSION"
        excluded.append(dict(scope=scope, row=deepcopy(row), row_fingerprint=fingerprint,
                             row_sha256=digest(row), anomalies=issues))
    target_integrity = inspect_normalized_ohlcv_rows(selected, timeframe="daily", cutoff=target)
    if len(selected) != 1:
        errors.append("TARGET_ROW_MISSING" if not selected else "TARGET_ROW_DUPLICATE_OR_CONFLICT")
    if not target_integrity.valid:
        errors.append("TARGET_ROW_INTEGRITY_FAILED")
    # An ordering violation at the target cannot be dismissed as a later-row defect.
    if any(i.bar_date == str(target) and i.violation.value == "BAR_TIMESTAMP_ORDERING" for i in inspection.issues):
        errors.append("TARGET_ROW_ORDERING_UNRESOLVED")
    row = deepcopy(selected[0]) if not errors else None
    body = dict(contract="completed-session-current-price-v1", generation_id=plan.run_id,
        acquisition_id=plan.acquisition_id, ticker=read.subject, canonical_security_id=read.canonical_security_id,
        market=read.market, exchange=read.exchange, currency=currency, source_role=read.role,
        adjustment_basis=adjustment_basis, target_session=str(target), calendar_receipt=calendar_receipt,
        source_plan_sha256=digest(plan.model_dump(mode="json")), source_receipt_sha256=digest(receipt),
        raw_sha256=[p["source_sha256"] for p in receipt["pages"]], normalized_sha256=receipt["normalized_sha256"],
        availability="UNAVAILABLE" if errors else "AVAILABLE", denial_reasons=sorted(set(errors)),
        selected_row=row, selected_row_fingerprint=canonical_fingerprint({k: row.get(k) for k in BAR_FIELDS}) if row else None,
        current_price=float(row["close"]) if row else None, price_as_of=str(target) if row else None,
        target_integrity=target_integrity.model_dump(mode="json"), source_integrity=inspection.model_dump(mode="json"),
        out_of_scope_rows=excluded)
    return CompletedSessionCurrentPriceProjection(**body, projection_sha256=digest(body))


def validate_completed_price(projection: dict, **inputs) -> CompletedSessionCurrentPriceProjection:
    actual = CompletedSessionCurrentPriceProjection.model_validate(projection)
    expected = project_completed_price(**inputs)
    if actual != expected:
        raise ValueError("completed_price_projection_source_binding_mismatch")
    return actual
