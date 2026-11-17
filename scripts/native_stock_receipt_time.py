"""Verify ordering within one captured Native stock clock domain."""
from datetime import datetime
from hashlib import sha256
import json
import re


CONTRACT = "native-stock-monotonic-v1"
_NS = 1_000_000_000


def clock_domain_sha(domain):
    return sha256(json.dumps(domain, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def wall_time(value):
    try:
        stamp = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError("stock_wall_clock_format_invalid") from None
    if stamp.utcoffset() is None:
        raise ValueError("stock_wall_clock_zone_required")
    return stamp


def verify_monotonic_receipt(receipt, *, expected_domain=None, check_diagnostic=True):
    """Return wall-time observations and the measured wall/monotonic discrepancy."""
    pages = receipt.get("pages", ())
    if "clock" not in receipt:
        if expected_domain is not None or any("clock" in page for page in pages):
            raise ValueError("stock_clock_contract_missing")
        return None
    clock = receipt["clock"]
    if not isinstance(clock, dict) or set(clock) != {"domain", "start_ns", "end_ns", "elapsed_ns", "diagnostic"}:
        raise ValueError("stock_clock_contract_invalid")
    domain = clock["domain"]
    if (not isinstance(domain, dict) or set(domain) != {"contract", "boot_sha256", "worker", "pid"}
            or domain["contract"] != CONTRACT
            or not isinstance(domain["boot_sha256"], str) or re.fullmatch(r"[0-9a-f]{64}", domain["boot_sha256"]) is None
            or not isinstance(domain["worker"], str) or re.fullmatch(r"[0-9a-f]{32}", domain["worker"]) is None
            or type(domain["pid"]) is not int or domain["pid"] <= 0
            or (expected_domain is not None and domain != expected_domain)):
        raise ValueError("stock_clock_domain_mismatch")
    pin = clock_domain_sha(domain)
    start, end = clock["start_ns"], clock["end_ns"]
    if any(type(n) is not int or n < 0 for n in (start, end, clock["elapsed_ns"])) or end - start != clock["elapsed_ns"]:
        raise ValueError("stock_monotonic_order_mismatch")
    points = [(wall_time(receipt["started_at"]), start)]
    previous_page = None
    for ordinal, page in enumerate(pages, 1):
        marker = page.get("clock")
        if (not isinstance(marker, dict) or set(marker) != {"domain_sha256", "request_ns", "receive_ns", "elapsed_ns"}
                or marker["domain_sha256"] != pin):
            raise ValueError("stock_clock_domain_mismatch")
        sent, received = marker["request_ns"], marker["receive_ns"]
        if (any(type(n) is not int or n < 0 for n in (sent, received, marker["elapsed_ns"]))
                or not points[-1][1] <= sent <= received <= end
                or received - sent != marker["elapsed_ns"]):
            raise ValueError("stock_monotonic_order_mismatch")
        continuation = {"cont_yn": "N", "next_key": ""} if previous_page is None else previous_page["response_continuation"]
        if (page["run_id"] != receipt["run_id"] or page["acquisition_id"] != receipt["acquisition_id"]
                or page["request"]["method"] != "POST" or page["request"]["continuation"] != continuation
                or page["page_ordinal"] != ordinal
                or (previous_page is not None and
                    (continuation["cont_yn"] != "Y" or not continuation["next_key"]
                     or page["external_ordinal"] != previous_page["external_ordinal"] + 1))):
            raise ValueError("stock_monotonic_page_lineage_mismatch")
        points.extend(((wall_time(page["requested_at"]), sent), (wall_time(page["received_at"]), received)))
        previous_page = page
    points.append((wall_time(receipt["completed_at"]), end))
    offsets = [(wall-points[0][0]).total_seconds() - (tick-start)/_NS for wall, tick in points]
    excess = max(offsets) - min(offsets)
    adjusted = excess >= 0.25 or any(b[0] < a[0] for a, b in zip(points, points[1:]))
    diagnostic = "WALL_CLOCK_ADJUSTED_MONOTONIC_ORDER_PASS" if adjusted else "MONOTONIC_ORDER_PASS"
    if check_diagnostic and clock["diagnostic"] != diagnostic:
        raise ValueError("stock_clock_diagnostic_mismatch")
    return [wall for wall, _ in points], excess, diagnostic
