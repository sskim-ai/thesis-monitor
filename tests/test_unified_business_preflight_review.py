"""Offline counterexamples only; synthetic HTTP responses are not source evidence."""

import asyncio
from datetime import date
from pathlib import Path

import httpx
import pytest

from app.services.opendart_financial_recovery_service import OpenDartRecoveryClient
from app.services.sec_financial_snapshot_service import SecFinancialSnapshotService
from app.services.unified_stock_acquisition import UNIVERSE
from scripts.unified_business_preflight_review import RETAINED, review


@pytest.mark.parametrize("exhibits", [0, 3, 9])
def test_sec_five_filing_limit_does_not_bound_exhibit_requests(exhibits):
    requests = []

    def respond(request):
        requests.append(str(request.url))
        if request.url.path.startswith("/submissions/"):
            return httpx.Response(200, json={"filings": {"recent": {
                "form": ["6-K"], "accessionNumber": ["0000000001-26-000001"],
                "primaryDocument": ["primary.htm"], "filingDate": ["2026-09-01"]}}})
        if request.url.path.endswith("index.json"):
            return httpx.Response(200, json={"directory": {"item": [
                {"name": f"ex99-{i}.htm"} for i in range(exhibits)]}})
        return httpx.Response(200, text="<html>No financial statement in this synthetic fixture.</html>")

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            await SecFinancialSnapshotService()._scan_foreign_filings(client, "0000000001")
    asyncio.run(run())
    assert len(requests) == 3 + exhibits


@pytest.mark.parametrize("pages", [1, 3, 9])
def test_opendart_selected_filing_limit_does_not_bound_discovery_pages(tmp_path, pages):
    requests = []

    def respond(request):
        requests.append(int(request.url.params["page_no"]))
        return httpx.Response(200, json={"status": "000", "total_page": pages, "list": []})
    owner = OpenDartRecoveryClient("synthetic-no-credential", tmp_path,
                                  transport=httpx.MockTransport(respond))
    asyncio.run(owner.discover(ticker="TEST", corp_code="00000001",
                              begin=date(2026, 1, 1), end=date(2026, 9, 1), limit=1))
    assert requests == list(range(1, pages + 1))
    assert owner.provider_calls == pages


def inputs():
    inventory = [{"ticker": t, "market": m} for m, ts in UNIVERSE.items()
                 for t in ts if t not in RETAINED]
    identities = {r["ticker"]: {"ticker": r["ticker"], "canonical_security_id": "fixture:" + r["ticker"],
                    "cik": "0000000001" if r["market"] == "us" else None,
                    "corp_code": "00000001" if r["market"] == "kr" else None} for r in inventory}
    return dict(root=Path(__file__).resolve().parents[1], inventory=inventory, identities=identities,
                frozen_at="2026-09-27T00:00:00+00:00", instruction_sha="test", code_sha="test")


def test_plan_cannot_be_promoted_to_executable_or_assume_zero_pages():
    value = review(**inputs())
    assert value == review(**inputs())
    assert len(value["entries"]) == 40
    assert len({r["logical_acquisition_id"] for r in value["entries"]}) == 40
    assert not value["executable"]
    assert value["underlying_transport_total"] is None
    assert value["executable_logical_entries"] == value["actual_transport_total"] == 0
    assert all(r["retries"] == 0 and r["raw_artifact_sha256"] is None for r in value["entries"])
    assert set(r["subject"] for r in value["entries"]).isdisjoint(RETAINED)


def test_incomplete_inventory_is_not_a_plan():
    args = inputs()
    args["inventory"] = args["inventory"][:-1]
    with pytest.raises(ValueError, match="exact_twenty"):
        review(**args)


def test_unbound_security_is_rejected():
    args = inputs()
    args["identities"][args["inventory"][0]["ticker"]]["canonical_security_id"] = None
    with pytest.raises(ValueError, match="source_owned_security"):
        review(**args)
