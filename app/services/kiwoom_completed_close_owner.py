"""Offline US daily-price owner; never converts query-time chart quotes to closes."""
from copy import deepcopy
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
import json
from typing import Literal
from pathlib import Path

from app.services.completed_session_current_price import CompletedSessionCurrentPriceProjection
from app.services.ohlcv_provider_integrity_service import (
    BAR_FIELDS, canonical_fingerprint, inspect_normalized_ohlcv_rows,
)
from app.services.price_structure_wave_fibonacci_v3_service import (
    _calendar_for_range, _latest_completed_session,
)
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest


CONTRACT = "kiwoom-us-completed-session-price-v2"
CHART_DENIAL = "LATEST_USA06012_CUR_PRC_NOT_COMPLETED_SESSION_CLOSE_AUTHORITY"
TECHNICAL_DENIAL = "EXACT_US_SECURITY_ADJUSTMENT_COMPATIBILITY_UNPROVEN"
OFFICIAL_SPEC_SHA256 = "42a7b3912c9d9588c83bdc2db7779c8d2e038703a2b5562e54ef46ae905cba79"


class KiwoomCompletedClose(CompletedSessionCurrentPriceProjection):
    contract: Literal["kiwoom-us-completed-session-price-v2"] = CONTRACT
    source_role: Literal["usa20590_completed_daily"] = "usa20590_completed_daily"
    adjustment_basis: Literal["regular_close"] = "regular_close"
    price_role: Literal["COMPLETED_REGULAR_SESSION_CLOSE"] = "COMPLETED_REGULAR_SESSION_CLOSE"
    basis: Literal["PROVIDER_HISTORICAL_DAILY_CLOSE"] = "PROVIDER_HISTORICAL_DAILY_CLOSE"
    supplement_generation_id: str
    supplement_requested_at: str
    supplement_source_sha256: str
    documentation_sha256: str
    technical_compatibility: dict


def _wire_price(value):
    # Official usa20590 wire signs encode direction, not negative USD prices.
    # Only provider string fields have that convention; numeric negatives fail.
    if not isinstance(value, str) or not value.strip():
        raise ValueError("invalid_usa20590_price_wire_type")
    try:
        number = abs(Decimal(value.strip()))
    except InvalidOperation as exc:
        raise ValueError("invalid_usa20590_price") from exc
    if not number.is_finite() or number <= 0 or not float(number) < float("inf"):
        raise ValueError("nonpositive_or_nonfinite_usa20590_price")
    return float(number)


def project(*, source, plan, read, security, artifact_reader):
    """Replay explicit request/capture/raw bindings, not a supplied PASS verdict."""
    def load(key):
        item = source[key]
        raw = artifact_reader(item["path"], item["sha256"])
        if sha256_bytes(raw) != item["sha256"]:
            raise ValueError("completed_close_artifact_hash_mismatch")
        return raw

    request_raw, capture_raw, raw = (load(k) for k in ("request", "capture", "response"))
    request, capture = json.loads(request_raw), json.loads(capture_raw)
    if sha256_bytes(load("documentation")) != OFFICIAL_SPEC_SHA256:
        raise ValueError("completed_close_official_field_contract_mismatch")
    exchange = {"NASDAQ": "ND", "NYSE": "NY", "AMEX": "NA"}.get(security.get("exchange"), security.get("exchange"))
    target = date.fromisoformat(read.latest_completed_session)
    if (read not in plan.reads or read.market != "us" or read.role != "adjusted_daily"
            or security.get("ticker") != read.subject
            or security.get("canonical_security_id") != read.canonical_security_id
            or exchange != read.exchange
            or request.get("ticker") != read.subject
            or request.get("canonical_security_id") != read.canonical_security_id
            or request.get("currency") != "USD"
            or request.get("api_id") != "usa20590" or request.get("method") != "POST"
            or request.get("path") != "/api/us/mrkcond"
            or request.get("body") != dict(stex_tp=read.exchange, stk_cd=read.subject, base_dt=target.strftime("%Y%m%d"))):
        raise ValueError("completed_close_exact_security_route_or_date_mismatch")
    if (capture.get("http_status") != 200 or capture.get("response_received") is not True
            or capture.get("raw_sha256") != sha256_bytes(raw)
            or capture.get("raw_bytes") != len(raw)
            or capture.get("request_sha256") != sha256_bytes(request_raw)):
        raise ValueError("completed_close_capture_binding_mismatch")
    at = datetime.fromisoformat(request.get("started_at") or request.get("requested_at"))
    if at.utcoffset() is None or at < plan.frozen_at or not request.get("generation_id"):
        raise ValueError("completed_close_supplement_time_identity_mismatch")
    name, calendar = _calendar_for_range("US", start=target-timedelta(days=14), end=at.date()+timedelta(days=7))
    if any(_latest_completed_session(calendar, when) != target for when in (plan.frozen_at, at)):
        raise ValueError("completed_close_calendar_target_mismatch")
    calendar_receipt = dict(calendar=name, exchange=read.exchange, frozen_at=plan.frozen_at.isoformat(),
        supplement_requested_at=at.isoformat(), latest_completed_session=str(target))
    calendar_receipt["sha256"] = digest(calendar_receipt)
    body = json.loads(raw)
    if str(body.get("return_code")) != "0" or not isinstance(body.get("result_list"), list):
        raise ValueError("completed_close_api_failure")
    rows = [r for r in body["result_list"] if r.get("dt") == target.strftime("%Y%m%d")]
    if len(rows) != 1:
        raise ValueError("completed_close_exact_target_missing_or_duplicate")
    selected = rows[0]
    row = dict(date=str(target), **{key: _wire_price(selected[field]) for key, field in
        (("open", "open_pric"), ("high", "high_pric"), ("low", "low_pric"), ("close", "cur_prc"))})
    # Volume is not a prerequisite for close-only use and is not injected into charts.
    integrity = inspect_normalized_ohlcv_rows([row], timeframe="daily", cutoff=target)
    if not integrity.valid:
        raise ValueError("completed_close_own_ohlc_integrity_failed")
    compatibility = dict(status="UNPROVEN", technical_target_injection_allowed=False,
        reason=TECHNICAL_DENIAL, canonical_security_id=read.canonical_security_id,
        target_session=str(target), raw_price_display_allowed=True,
        owner="NO_QUALIFIED_US_ACTION_GUARD_IN_DECLARED_CORPUS")
    value = dict(contract=CONTRACT, generation_id=plan.run_id, acquisition_id=plan.acquisition_id,
        ticker=read.subject, canonical_security_id=read.canonical_security_id, market="us",
        exchange=read.exchange, currency="USD", source_role="usa20590_completed_daily",
        adjustment_basis="regular_close", target_session=str(target), calendar_receipt=calendar_receipt,
        source_plan_sha256=digest(plan.model_dump(mode="json")), source_receipt_sha256=sha256_bytes(capture_raw),
        raw_sha256=[sha256_bytes(raw)], normalized_sha256=digest(row), availability="AVAILABLE",
        denial_reasons=[], selected_row=row, selected_row_fingerprint=canonical_fingerprint({k: row.get(k) for k in BAR_FIELDS}),
        current_price=row["close"], price_as_of=str(target), target_integrity=integrity.model_dump(mode="json"),
        source_integrity=integrity.model_dump(mode="json"), out_of_scope_rows=[],
        price_role="COMPLETED_REGULAR_SESSION_CLOSE", basis="PROVIDER_HISTORICAL_DAILY_CLOSE",
        supplement_generation_id=request["generation_id"], supplement_requested_at=at.isoformat(),
        supplement_source_sha256=digest(source), documentation_sha256=OFFICIAL_SPEC_SHA256,
        technical_compatibility=compatibility)
    return KiwoomCompletedClose(**value, projection_sha256=digest(value))


def historical_only_roles(roles, *, cutoff):
    """No unqualified raw/adjusted splice. Latest native rows remain audit-only."""
    result = deepcopy(roles)
    for role, rows in result.items():
        # Even an in-range latest quote has no completed-close authority.
        latest = max((str(r.get("date") or "")[:10] for r in rows), default="")
        result[role] = [r for r in rows if str(r.get("date") or "")[:10] < min(latest, str(cutoff))]
    return result


def materialize(*, projection, roles, ticker, market, cutoff, observed_at):
    from app.services.unified_stock_anomaly_scope import materialize_source_components
    from app.services.current_effective_technical import project as effective
    from app.services.packet_owned_technical_context_service import build_packet_owned_technical_context
    if projection.ticker != ticker or market != "us" or projection.target_session != str(cutoff):
        raise ValueError("completed_close_component_identity_mismatch")
    view = historical_only_roles(roles, cutoff=cutoff)
    components = materialize_source_components(ticker=ticker, market=market, cutoff=cutoff,
        observed_at=observed_at, roles=view)
    for consumers in components["role_consumer_matrix"].values():
        for consumer in consumers:
            consumer.update(eligible=False, latest_row_valid=False, reason=TECHNICAL_DENIAL)
    periods = {}
    for tf in ("daily", "weekly", "monthly"):
        states = {r["date"]: r["bar_state"] for r in components["analysis_view_finality"][tf]["rows"]}
        periods[tf] = [{**r, "bar_state": states[str(r["date"])[:10]]} if str(r["date"])[:10] in states else r
            for r in view["adjusted_" + tf]]
        components["features"][tf].update(facts=[], current_role_gate=False, suppression_reason=TECHNICAL_DENIAL)
    context = build_packet_owned_technical_context(ticker=ticker, market=market, session="closed",
        as_of=observed_at, periods=periods, cutoff=cutoff, expected_daily_completed=str(cutoff),
        source="sealed_r2b0_kiwoom", source_version="one-shot-stock-source-acquisition-v1")
    components.update(source_rows_sha256=digest(roles), current_price=projection.current_price,
        current_price_eligible=True, mandatory_current_price_failure=False,
        completed_close_projection_sha256=projection.projection_sha256,
        latest_chart_close_disqualification=CHART_DENIAL,
        technical_compatibility=projection.technical_compatibility,
        technical_context_id=effective(context, components["features"]).technical_context_id)
    components["component_projection_sha256"] = None
    components["component_projection_sha256"] = digest(components)
    return components


def bind_technical_input(technical, *, source, artifacts, security):
    """Attach declared supplement bytes without changing any inherited receipt."""
    from app.services.unified_stock_acquisition import decode_owned_role
    tech = dict(technical)
    overlap = set(artifacts) & set(tech["artifacts"])
    if overlap:
        raise ValueError("completed_close_artifact_namespace_collision")
    tech["artifacts"] = {**tech["artifacts"], **artifacts}
    def read_artifact(path, sha):
        raw = tech["artifacts"][path]
        if sha256_bytes(raw) != sha:
            raise ValueError("completed_close_artifact_hash_mismatch")
        return raw
    plan = tech["plan"]
    reads = [r for r in plan.reads if r.subject == tech["ticker"]]
    daily = next(r for r in reads if r.role == "adjusted_daily")
    projection = project(source=source, plan=plan, read=daily, security=security, artifact_reader=read_artifact)
    roles = {r.role: decode_owned_role(plan, r, tech["receipts"][r.role], read_artifact) for r in reads}
    tech["components"] = materialize(projection=projection, roles=roles, ticker=daily.subject,
        market=daily.market, cutoff=date.fromisoformat(daily.latest_completed_session), observed_at=plan.frozen_at.isoformat())
    tech["completed_close_source"] = deepcopy(source)
    tech["expected_hashes"] = dict(tech["expected_hashes"], components=digest(tech["components"]),
        completed_close_source=digest(source))
    return tech


def load_supplement_lineage(root, *, parent_generation_id):
    """Explicit local layout adapter; path and bytes stay inside the sealed root."""
    root = Path(root).resolve()
    path = root / "completed-close-lineage.json"
    if not path.exists():
        return None
    lineage = json.loads(path.read_bytes())
    sources = lineage["sources"]
    if (lineage.get("contract") != CONTRACT or lineage.get("parent_generation_id") != parent_generation_id
            or digest(sources) != lineage.get("sources_sha256")):
        raise ValueError("completed_close_lineage_identity_mismatch")
    result = {}
    for ticker, source in sources.items():
        artifacts = {}
        for item in source.values():
            name = Path(item["path"])
            target = root / name
            if name.is_absolute() or ".." in name.parts or target.is_symlink() or not target.resolve().is_relative_to(root):
                raise ValueError("completed_close_lineage_path_escape")
            raw = target.read_bytes()
            if sha256_bytes(raw) != item["sha256"]:
                raise ValueError("completed_close_lineage_artifact_drift")
            artifacts[item["path"]] = raw
        result[ticker] = dict(source=source, artifacts=artifacts)
    return result
