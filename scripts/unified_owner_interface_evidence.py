"""Offline owner replay. Historical artifacts never receive current-run receipts."""

import argparse
import asyncio
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
import zipfile

from app.jobs.probe_krx_night_futures import (
    KST, _attach_fetch_telemetry, expected_latest_completed_krx_session,
    parse_krx_futures_payloads,
)
from app.providers.kiwoom_rest_client import KiwoomCallStats, KiwoomRestResponse, payload_sha256
from app.providers.nasdaq_trader_breadth_provider import parse_nasdaq_daily_market_file
from app.services.kiwoom_kr_market_context_service import KiwoomKrMarketContextService
from app.services.unified_run_artifacts import durable_bytes, durable_json


PRIOR_SHA = "8e00d434d551b8e88809d7db72841864fa24b1a144aac33a8abf2c9f2922bce9"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def verify_prior(path: Path) -> dict:
    if sha(path.read_bytes()) != PRIOR_SHA:
        raise ValueError("prior_r2a_identity_mismatch")
    with zipfile.ZipFile(path) as bundle:
        manifest = json.loads(bundle.read("bundle-manifest.json"))
        if set(bundle.namelist()) != {*manifest, "bundle-manifest.json"}:
            raise ValueError("prior_manifest_members_mismatch")
        for name, item in manifest.items():
            raw = bundle.read(name)
            if len(raw) != item["bytes"] or sha(raw) != item["sha256"]:
                raise ValueError("prior_manifest_hash_mismatch")
    return {"sha256": PRIOR_SHA, "manifest_entries_verified": len(manifest),
        "final": "99c78db1e8a326ee2b52be4a70b7d3a82b57f99d", "status": "VERIFIED"}


def replay_night(archive: Path, output: Path) -> dict:
    path = archive / "source/night-probe.json"
    original = json.loads(path.read_bytes())
    payloads, hashes, bindings = {}, {}, []
    for record in original["date_statuses"]:
        day = date.fromisoformat(record["query_date"])
        raw = (archive / "source/krx-raw" / f"{day}.json").read_bytes()
        if sha(raw) != record["raw_payload_sha256"]:
            raise ValueError("krx_original_byte_hash_mismatch")
        payloads[day], hashes[day] = json.loads(raw), sha(raw)
        artifact = f"genuine-sources/krx-{day}.json"
        durable_bytes(output / artifact, raw, exclusive=True)
        bindings.append({"artifact": artifact, "sha256": sha(raw), "original_owner_hash": record["raw_payload_sha256"]})
    original_time = datetime.fromisoformat(original["fetched_at"])
    replay = parse_krx_futures_payloads(payloads, fetched_at=original_time,
        queried_dates=[date.fromisoformat(v) for v in original["queried_dates"]],
        payload_sha256_by_date=hashes)
    replay = _attach_fetch_telemetry(replay, payloads=payloads,
        expected_session=expected_latest_completed_krx_session(original_time.astimezone(KST).date()),
        observation_time=original_time)
    actual = [v.model_dump(mode="json") for v in replay.observations]
    return {"owner": "parse_krx_futures_payloads", "source_sha256": sha(path.read_bytes()),
        "bindings": bindings, "original_fetched_at": original["fetched_at"],
        "original": original["observations"], "replayed": actual,
        "exact_normalization_parity": actual == original["observations"],
        "classification": "HISTORICAL_OWNER_REPLAY_NOT_CURRENT_RUN_CLASS_B"}


async def replay_kiwoom(path: Path, output: Path) -> dict:
    raw = path.read_bytes()
    original = json.loads(raw)
    responses = original["responses"]
    for response in responses:
        if payload_sha256(response["payload"]) != response["payload_sha256"]:
            raise ValueError("kiwoom_saved_payload_hash_mismatch")
    if payload_sha256([r["payload_sha256"] for r in responses]) != original["source_payload_sha256"]:
        raise ValueError("kiwoom_saved_page_set_hash_mismatch")

    class SavedOwnerClient:
        source_observer = None
        stats = KiwoomCallStats(**original["audit"]["provider_calls"])

        def __init__(self):
            self.index = 0

        async def request(self, *, endpoint, api_id, body, continuation=False, next_key=""):
            record = responses[self.index]
            self.index += 1
            if record["api_id"] != api_id or record["request"] != body:
                raise ValueError("kiwoom_saved_read_order_mismatch")
            if continuation != (record["page"] > 1):
                raise ValueError("kiwoom_saved_page_order_mismatch")
            # Historical archives omit cursor headers; this is parser replay only,
            # not a reconstruction of original wire/pagination receipts.
            return KiwoomRestResponse(api_id, record["payload"], record["continuation"],
                "historical-replay-cursor" if record["continuation"] else "", record["payload_sha256"])

    client = SavedOwnerClient()
    result = await KiwoomKrMarketContextService(client, max_pages=100).collect(
        session_date=date.fromisoformat(original["session_date"]),
        observed_at=datetime.fromisoformat(original["observed_at"]))
    durable_bytes(output / "genuine-sources/kiwoom-saved-owner-archive.json", raw, exclusive=True)
    return {"owner": "KiwoomKrMarketContextService.collect", "artifact_sha256": sha(raw),
        "original_observed_at": original["observed_at"], "source_payload_sha256": original["source_payload_sha256"],
        "saved_response_count": len(responses), "replayed_response_count": client.index,
        "all_saved_responses_consumed": client.index == len(responses),
        "exact_normalized_audit_parity": result.audit.model_dump(mode="json") == original["audit"],
        "original_audit": original["audit"], "replayed_audit": result.audit.model_dump(mode="json"),
        "wire_receipt_qualified": False, "original_cursor_headers_available": False,
        "classification": "HISTORICAL_PAYLOAD_AND_NORMALIZED_AUDIT_REPLAY_NOT_CURRENT_CLASS_A"}


def replay_breadth(archive: Path, output: Path) -> dict:
    root = archive / "private/isolated-data/market-context"
    path = root / "structured/us/2026-09-22.json"
    envelope = json.loads(path.read_bytes())["envelope"]
    source_sha = envelope["source_payload_sha256"]
    raw = (root / "nasdaq-trader/raw/2026" / f"{source_sha}.csv").read_bytes()
    if sha(raw) != source_sha:
        raise ValueError("nasdaq_original_byte_hash_mismatch")
    result = parse_nasdaq_daily_market_file(raw, target_session=date.fromisoformat(envelope["session_date"]),
        retrieved_at=datetime.fromisoformat(envelope["retrieved_at"]), source_url=envelope["source_refs"][0])
    durable_bytes(output / "genuine-sources/nasdaq-saved.csv", raw, exclusive=True)
    return {"owner": "parse_nasdaq_daily_market_file", "artifact_sha256": source_sha,
        "original_retrieved_at": envelope["retrieved_at"],
        "original_publication_state": envelope["publication_state"],
        "exact_publication_state_parity": result.publication_state == envelope["publication_state"],
        "original_cross_section": envelope["cross_section"], "result": result.model_dump(mode="json"),
        "unavailable_stays_unavailable": envelope["cross_section"] is None and result.observation is None,
        "classification": "HISTORICAL_PUBLICATION_DENIAL_REPLAY_NOT_CURRENT_RUN_CLASS_B"}


def generate(prior_zip: Path, archive: Path, saved_kiwoom: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError("owner_evidence_immutable")
    durable_json(output / "prior-r2a-identity.json", verify_prior(prior_zip), exclusive=True)
    with patch("socket.socket.connect", side_effect=AssertionError("network forbidden")) as connect:
        night = replay_night(archive, output)
        kiwoom = asyncio.run(replay_kiwoom(saved_kiwoom, output))
        breadth = replay_breadth(archive, output)
        for name, result in (("krx-night", night), ("kiwoom", kiwoom), ("nasdaq", breadth)):
            durable_json(output / f"genuine-{name}-replay.json", result, exclusive=True)
        durable_json(output / "network-free-proof.json", {"socket_connect_attempts": connect.call_count,
            "external_provider_calls": 0, "model_calls": 0, "render_calls": 0, "send_calls": 0,
            "current_source_cohort": False}, exclusive=True)
    if not all((night["exact_normalization_parity"], kiwoom["exact_normalized_audit_parity"],
                kiwoom["all_saved_responses_consumed"], breadth["exact_publication_state_parity"],
                breadth["unavailable_stays_unavailable"])):
        raise ValueError("historical_owner_parity_failed_see_receipts")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("prior-zip", "archive", "saved-kiwoom", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    generate(**vars(args))
    print("Historical owner replay complete; current-run acquisition not claimed.")
