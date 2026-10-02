"""R3 pre-network review only. This is not a source acquisition adapter."""

from __future__ import annotations

import ast
from pathlib import Path

from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest


BASE = "4f61f308fe382fc149ee8435a31cbedf9b81fd06"
R2_SHA = "90abe3133c8a41ff0a89167edab28a5a3ef016f68af78a30196ed95a675cb686"
TERMINAL = "M12DS_R6_R5F_R2B0_R3_BUSINESS_OWNER_GAP_REMAINS"
RETAINED = {"005930", "047810"}


def source_reference(root: Path, path: str, symbol: str) -> dict:
    raw = (root / path).read_bytes()
    tree = ast.parse(raw)
    node = tree
    for part in symbol.split("."):
        node = next(n for n in node.body if getattr(n, "name", None) == part)
    return {"path": path, "symbol": symbol, "line": node.lineno,
            "end_line": node.end_lineno, "file_sha256": sha256_bytes(raw)}


def review(root: Path, *, inventory: list[dict], identities: dict, frozen_at: str,
           instruction_sha: str, code_sha: str) -> dict:
    tickers = [r["ticker"] for r in inventory]
    if len(tickers) != 20 or len(set(tickers)) != 20 or RETAINED.intersection(tickers):
        raise ValueError("exact_twenty_blocked_subjects_required")
    if sorted(r["market"] for r in inventory) != ["kr"] * 6 + ["us"] * 14:
        raise ValueError("exact_us14_kr6_required")
    refs = {
        "sec": source_reference(root, "app/services/sec_financial_snapshot_service.py",
                                "SecFinancialSnapshotService._scan_foreign_filings"),
        "sec_refresh": source_reference(root, "app/services/sec_financial_snapshot_service.py",
                                        "SecFinancialSnapshotService.refresh"),
        "dart": source_reference(root, "app/services/opendart_financial_recovery_service.py",
                                 "OpenDartRecoveryClient.discover"),
        "dart_events": source_reference(root, "app/providers/filings.py", "OpenDARTProvider.fetch_events"),
        "sec_events": source_reference(root, "app/providers/filings.py", "SecEdgarProvider.fetch_events"),
        "transport": source_reference(root, "app/services/unified_event_acquisition.py", "EventReceiptTransport"),
        "stock": source_reference(root, "app/services/unified_stock_owner.py", "assemble_stock"),
    }
    blockers = [
        {"id": "SEC_FINANCIAL_TRANSPORT_PLAN_UNBOUNDED", "scope": "US14 financial acquisition",
         "evidence": [refs["sec"], refs["sec_refresh"]],
         "reason": "refresh unconditionally scans foreign filings; index and linked exhibits have no enforced cap. The five-6-K limit is not a transport/page bound.",
         "next_repair": "Add an explicit bounded discovery/document plan with raw response receipts; cap exhaustion must deny completeness, not silently truncate."},
        {"id": "OPENDART_FINANCIAL_DISCOVERY_PLAN_UNBOUNDED", "scope": "KR6 financial acquisition",
         "evidence": [refs["dart"]],
         "reason": "discover(limit=1) limits selected filings only after all response total_page pages have been fetched; no discovery page cap exists.",
         "next_repair": "Expose and enforce discovery/page/request bounds and bind the actual discovery and statement bytes to the selected filing."},
        {"id": "STOCK_BUSINESS_INPUT_INTERFACE_GAP", "scope": "20 prospective business inputs",
         "evidence": [refs["stock"]],
         "reason": "R2 stock owner takes no event input, builds evidence=[], admits earnings refs only and uses price plan.frozen_at as the financial/assessment cutoff.",
         "next_repair": "Add owner-bound event inputs and an explicit business cutoff distinct from sealed price identity; preserve all existing event and financial gates."},
    ]
    rows = []
    for item in sorted(inventory, key=lambda r: (r["market"], r["ticker"])):
        ticker, market = item["ticker"], item["market"]
        identity = identities[ticker]
        if identity.get("ticker") != ticker or not identity.get("canonical_security_id"):
            raise ValueError("source_owned_security_identity_required")
        for evidence_class in ("REPORTED_FINANCIAL", "BUSINESS_EVENT"):
            financial = evidence_class == "REPORTED_FINANCIAL"
            provider = "sec_edgar" if market == "us" else "opendart"
            owner = ("SecFinancialSnapshotService.refresh" if market == "us" else
                     "OpenDartRecoveryClient.discover/recover_filing") if financial else (
                     "EventAcquisition.collect/SecEdgarProvider" if market == "us" else
                     "EventAcquisition.collect/OpenDARTProvider")
            identity_key = "cik" if market == "us" else "corp_code"
            reason = ("SEC_FINANCIAL_TRANSPORT_PLAN_UNBOUNDED" if market == "us" else
                      "OPENDART_FINANCIAL_DISCOVERY_PLAN_UNBOUNDED") if financial else "STOCK_BUSINESS_INPUT_INTERFACE_GAP"
            rows.append({"subject": ticker, "market": market, "evidence_class": evidence_class,
                "owner": owner, "provider": provider, "expected_identity": identity,
                "identity_available": bool(identity.get(identity_key)),
                "endpoint_family": (("company_tickers/companyfacts/submissions/Archives" if financial else
                    "submissions") if market == "us" else ("list/statements/conditional-xbrl" if financial else
                    "list/response-dependent-filing-enrichment")),
                "logical_acquisition_id": "r3:" + ticker + ":" + evidence_class.lower(),
                "use": "OPTIONAL_ALTERNATIVE_FOR_MANDATORY_OBSERVED_BUSINESS_UNION",
                "max_logical_acquisitions": 1, "max_attempts": 1, "retries": 0,
                "transport_bound": (1 if not financial and market == "us" and identity.get("cik") else None),
                "transport_bound_kind": ("EXISTING_BOUND_CIK_SINGLE_SUBMISSIONS_GET" if not financial and
                    market == "us" and identity.get("cik") else "NOT_ESTABLISHED_BY_EXISTING_OWNER_PLAN"),
                "status": "NOT_ATTEMPTED_PRE_NETWORK_OWNER_GUARD", "reason": reason,
                "actual_requests": 0, "actual_auth_calls": 0, "source_receipt": None,
                "raw_artifact_sha256": None})
    plan = {"review": "R2B0-R3", "frozen_at": frozen_at, "instruction_sha": instruction_sha,
        "code_sha": code_sha, "accepted_base": BASE, "accepted_r2_zip_sha256": R2_SHA,
        "status": "NOT_EXECUTABLE_OWNER_GUARD", "executable": False,
        "candidate_logical_entries": len(rows), "maximum_authorized_logical_acquisitions": 40,
        "executable_logical_entries": 0, "actual_logical_acquisitions": 0,
        "underlying_transport_total": None, "actual_transport_total": 0,
        "no_network_until_complete_bounded_owner_plan": True,
        "retained_without_recollection": sorted(RETAINED), "entries": rows,
        "blockers": blockers, "owner_references": refs,
        "alternate_review": {
            "SEC_event": "Single submissions read with bound CIK exists; it does not close the R2 event-input interface.",
            "Google_Naver": "Existing one-request news providers exist; no undeclared news substitution or event-only bypass of the whole-plan stop was made.",
            "OpenDART_event": "Response-driven enrichment and caller-supplied max_requests are not an owner-produced exact transport plan.",
            "financial_projection": "Pure companyfacts/statement projectors are not independently raw-receipt-bound acquisition owners."},
        "terminal": TERMINAL}
    return {**plan, "review_sha256": digest(plan)}
