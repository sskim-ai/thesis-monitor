"""Optional, same-generation KR stock flow. Share quantities, not a score."""
from datetime import date
import math

from app.services.kr_investor_flow_service import build_investor_flow_reconciliation
from app.services.market_session import is_exchange_session_date, preceding_exchange_session_date
from app.services.unified_snapshot_contract import digest

ROUTE = "/api/dostk/chart"
API = "ka10060"
BASIS = "KIWOOM_SHARE_QUANTITY_UNIT_1"
PARTICIPANTS = ("foreign", "institution", "individual")
WINDOWS = ((1, ""), (5, "_5"), (20, "_20"))


def read_for(daily):
    entry_id = f"stock_flow:kr:{daily.subject}"
    return dict(entry_id=entry_id, market="kr", subject=daily.subject,
        canonical_security_id=daily.canonical_security_id, role="session_net_buy",
        route=ROUTE, api_id=API, max_pages=1, count=20, unit="shares", basis=BASIS,
        latest_completed_session=daily.latest_completed_session,
        payload=dict(dt=daily.latest_completed_session.replace("-", ""), stk_cd=daily.subject,
                     amt_qty_tp="2", trde_tp="0", unit_tp="1"))


def require_planned_reads(stock, request_plan, supplied):
    """Check both sides of the existing plan-to-worker wire handoff."""
    from app.services.canonical_source_plan import kiwoom_request
    from app.services.sealed_fresh_dispatch import wire_identity

    slots = [d for d in request_plan.descriptors if d.source_family == "stock_flow"
             or d.consumer_role.startswith("stock_flow:")]
    if not supplied and not slots:
        return []
    reads = [read_for(row) for row in stock.reads if row.market == "kr" and row.role == "adjusted_daily"]
    if (stock.run_id != request_plan.generation_id or set(stock.universe) != {"kr"}
            or not reads or supplied != reads or len(slots) != len(reads)):
        raise ValueError("kr_stock_flow_plan_mismatch")
    by_key = {d.logical_request_id: d for d in slots}
    for read in reads:
        key = read["entry_id"]
        d = by_key.get(key)
        expected_wire = wire_identity(kiwoom_request(API, ROUTE, read["payload"]), ("PLAN_CREDENTIAL",))
        if (d is None or d.mandatory or d.market != "kr" or d.provider != "kiwoom"
                or d.subject != read["subject"] or d.target_period != read["latest_completed_session"]
                or d.endpoint_operation != API or d.source_family != "stock_flow"
                or d.role_id != key or d.consumer_role != key or d.request_json != expected_wire
                or d.max_pages != 1 or d.max_documents != 1 or d.response_binding is not None
                or d.max_transport_attempts != 1):
            raise ValueError("kr_stock_flow_wire_mismatch")
    return reads


def _integer(value):
    return (int(value) if type(value) in {int, float} and math.isfinite(value)
            and abs(value) < 2**53 and int(value) == value else None)


def project(*, source, plan, daily, completed_daily_rows):
    """Admit only raw-replayed, sealed stock rows on consecutive chart sessions."""
    expected = read_for(daily)
    receipt = source["receipt"]
    if (daily.market != "kr" or daily.role != "adjusted_daily"
            or source["read"] != expected or source["run_id"] != plan.run_id
            or source["scope"] != "KR_INDIVIDUAL_SECURITY"
            or source["receipt_sha256"] != digest(receipt)
            or receipt["entry"] != expected or receipt["run_id"] != plan.run_id
            or receipt["status"] != "CAPTURED"):
        raise ValueError("kr_flow_source_binding_mismatch")
    target = expected["latest_completed_session"]
    incomplete = {"PARTIAL", "PROVISIONAL", "OPEN", "LIVE", "UNCONFIRMED", "UNKNOWN", "INVALID"}
    dates = [r["date"] for r in completed_daily_rows
             if str(r.get("bar_state") or r.get("completion_state") or "").upper() not in incomplete]
    rows = source["rows"]
    observed = [date.fromisoformat(row["date"]).isoformat() for row in rows]
    if (not is_exchange_session_date("XKRX", date.fromisoformat(target))
            or not dates or dates != sorted(set(dates)) or dates[-1] != target
            or not observed or observed != sorted(set(observed)) or observed[-1] != target
            or any(day > target for day in observed)
            or source["receipt"]["normalized_sha256"] != digest(rows)):
        raise ValueError("kr_flow_wrong_or_unconfirmed_completed_session")

    # Never use the provider's min-period rolling values or count a missing
    # participant/session as zero. The existing reconciler owns all summation.
    mapping = {row["date"]: row for row in rows}
    latest = mapping[target]
    values, period_status = {}, {}
    for size, suffix in WINDOWS:
        sessions = dates[-size:]
        if (len(sessions) != size or any(day not in mapping for day in sessions)
                or any(preceding_exchange_session_date("XKRX", date.fromisoformat(right)) != date.fromisoformat(left)
                       for left, right in zip(sessions, sessions[1:]))):
            period_status[f"{size}d"] = "INCOMPLETE_SESSION_COVERAGE"
            continue
        clean = [{"date": day, **{key: _integer(v) for key, v in mapping[day].items()
                                if key.endswith("_net_buy_qty")}} for day in sessions]
        if size > 1 and any(row.get(f"{participant}_net_buy_qty") is None
                            for row in clean for participant in PARTICIPANTS):
            period_status[f"{size}d"] = "INCOMPLETE_PARTICIPANT_COVERAGE"
            continue
        reconciled = build_investor_flow_reconciliation(clean)
        status = "NOT_CHECKED" if size > 1 else "DAILY_PROVIDER_ROW"
        for participant in PARTICIPANTS:
            field = f"{participant}_net_buy_qty"
            value = reconciled.get(field + suffix)
            if value is None or any(row.get(field) is None for row in clean):
                continue
            check = _integer(latest.get("ka10061_" + field + suffix)) if size > 1 else None
            if check is not None and value != check:
                status = "CONFLICT"
            values[field + suffix] = value
        if status == "CONFLICT":
            for participant in PARTICIPANTS:
                values.pop(f"{participant}_net_buy_qty{suffix}", None)
        period_status[f"{size}d"] = status
    if not values:
        return None
    return dict(as_of_date=target, scope="KR_INDIVIDUAL_SECURITY", unit="shares", basis=BASIS,
        ticker=daily.subject, canonical_security_id=daily.canonical_security_id,
        source_generation=plan.run_id, provider="kiwoom", source_role=expected["entry_id"],
        period_comparison=period_status, **values)
