"""Bounded source-only historical inventory and KRX owner proof. Never live."""

import argparse
import asyncio
from datetime import date, datetime
import hashlib
import json
from pathlib import Path

from app.services.unified_aggregate_receipt import AggregateChild, AggregateReceipt, ArtifactBinding
from app.services.unified_krx_history_replay import (
    OWNER, PRODUCTS, HistoricalKrxChild, HistoricalKrxPlan,
    krx_replay_fingerprint, native_candidate_projection, replay_krx_history_aggregate,
)
from app.services.unified_run_artifacts import durable_json
from app.services.unified_snapshot_contract import digest
from scripts.unified_adapter_preflight import raw_ohlcv_artifacts


US = ("CORZ", "CPNG", "CRCL", "GOOGL", "HUT", "IBM", "MU", "RXRX", "SKHY", "SNDK", "TSLA", "TSM", "WRD", "WULF")
KR = ("000660", "003690", "005490", "005930", "010120", "012450", "047810", "086280")


def freeze_krx(archive: Path, root: Path, run_id: str) -> AggregateReceipt:
    """Freeze originals and dependency plan before the owner is executed."""
    if root.exists():
        raise FileExistsError("immutable_replay_root_exists")
    root.mkdir(parents=True)

    def copy(relative):
        source = archive / relative
        if any(p.is_symlink() for p in (source, *source.parents)) or not source.is_file():
            raise ValueError("original_source_missing_or_symlink")
        raw = source.read_bytes()
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with target.open("xb") as stream:
                stream.write(raw)
        elif target.read_bytes() != raw:
            raise ValueError("source_copy_conflict")
        return ArtifactBinding(path=relative, sha256=hashlib.sha256(raw).hexdigest())

    manifest_binding = copy("report/source-snapshot-manifest.json")
    manifest = json.loads((root / manifest_binding.path).read_bytes())
    probe_binding = copy("source/night-probe.json")
    probe = json.loads((root / probe_binding.path).read_bytes())
    candidate_binding = copy("source/night-provider.json")
    candidate = json.loads((root / candidate_binding.path).read_bytes())
    native_candidate = native_candidate_projection(candidate)
    durable_json(root / "native-candidate.json", native_candidate, exclusive=True)
    native_binding = ArtifactBinding(path="native-candidate.json",
        sha256=hashlib.sha256((root / "native-candidate.json").read_bytes()).hexdigest())
    required = set()
    for observation in candidate["observations"]:
        for frame in observation["raw_payload"]["night_timeframes"].values():
            if isinstance(frame, dict):
                required.update(frame["source_raw_sha256"])
    prefix = "private/isolated-data/market/krx-night-history"
    history, probes = [], []
    probe_dates = set(probe["queried_dates"])
    probe_shas = {r["query_date"]: r["raw_payload_sha256"] for r in probe["date_statuses"]}
    # Inventory is restricted to the explicitly declared original history root.
    for path in sorted((archive / prefix / "raw").rglob("*.receipt.json")):
        row = json.loads(path.read_bytes())
        query_date, sha = row["query_date"], row["raw_payload_sha256"]
        is_probe = query_date in probe_dates and sha == probe_shas[query_date]
        if not is_probe and sha not in required:
            continue
        purpose = "probe" if is_probe else "history"
        child = HistoricalKrxChild(child_id=f"{purpose}:{query_date}", purpose=purpose,
            query_date=date.fromisoformat(query_date), receipt=copy(str(path.relative_to(archive))),
            body=copy(f"{prefix}/{row['raw_relative_path']}"))
        (probes if is_probe else history).append(child)
    children = tuple(sorted(history, key=lambda c: c.query_date) + sorted(probes, key=lambda c: c.query_date, reverse=True))
    plan = HistoricalKrxPlan(run_id=run_id, source_archive_id=manifest_binding.sha256,
        source_manifest=manifest_binding, source_manifest_generation_id=manifest["generation_id"],
        source_probe=probe_binding, source_candidate=candidate_binding, owner_fingerprint=krx_replay_fingerprint(),
        observed_at=datetime.fromisoformat(probe["fetched_at"]), session_date=date.fromisoformat(probe["source_date"]),
        children=children)
    durable_json(root / "replay-plan.json", plan.model_dump(mode="json"), exclusive=True)
    fields = dict(owner=OWNER, run_id=run_id, acquisition_class="RUN_FRESH_ONCE",
        acquisition_id="historical-replay-not-live", role="night_and_publication_context",
        market="us", symbol="*", provider="krx_night_futures", basis="same_contract_night_dwm",
        session=plan.session_date.isoformat(), requested_at=plan.observed_at.isoformat(),
        received_at=plan.observed_at.isoformat(), artifact=native_binding.path,
        artifact_sha256=native_binding.sha256,
        plan={"path": "replay-plan.json", "sha256": hashlib.sha256((root / "replay-plan.json").read_bytes()).hexdigest()},
        expected_child_ids=[c.child_id for c in children],
        children=[AggregateChild(child_id=c.child_id, receipt=c.receipt).model_dump(mode="json") for c in children],
        normalized_sha256=digest(native_candidate), validator_contract=OWNER,
        coverage={"mode": plan.mode, "products": list(PRODUCTS), "live_qualified": False},
        contract="unified-transitive-source-receipt-v1", attempt_id=None)
    receipt = AggregateReceipt(**fields, aggregate_sha256=digest(fields))
    durable_json(root / "aggregate-receipt.json", receipt.model_dump(mode="json"), exclusive=True)
    return receipt


def run(archive: Path, output: Path):
    if output.exists():
        raise FileExistsError("immutable_proof_output_exists")
    output.mkdir(parents=True)
    candidates = raw_ohlcv_artifacts(archive)
    stock_rows = [{"ticker": ticker, "market": market, "blocker": "STOCK_MATERIALIZATION",
        "status": "BLOCKED", "required_raw_roles": ["adjusted_daily", "adjusted_weekly", "adjusted_monthly", "unadjusted_weekly_valuation"],
        "denial": "ORIGINAL_ROLE_BOUND_REQUEST_RESPONSE_RECEIPTS_NOT_FOUND",
        "stock_packet_generated": False, "observed_business_union": "NOT_QUALIFIED_NO_PACKET_ASSEMBLED",
        "optional_estimates_cf_wc": "UNAVAILABLE_NOT_ADDITIONAL_BLOCKERS"}
        for market, tickers in (("us", US), ("kr", KR)) for ticker in tickers]
    if candidates:
        raise ValueError("new_raw_candidates_require_explicit_role_review")
    durable_json(output / "stock-source-inventory.json", {"archive": str(archive),
        "standalone_original_ohlcv_candidates": candidates, "subjects": stock_rows,
        "missing_role_bindings": 4 * len(stock_rows), "assessment_substitutions": 0}, exclusive=True)
    receipt = freeze_krx(archive, output / "krx-inputs", "r2a-r5-offline-history")
    durable_json(output / "pre-replay-freeze.json", {"aggregate_sha256": receipt.aggregate_sha256,
        "plan_sha256": receipt.plan.sha256, "owner_fingerprint": krx_replay_fingerprint()}, exclusive=True)
    try:
        first = asyncio.run(replay_krx_history_aggregate(root=output / "krx-inputs", receipt=receipt,
            expected_plan_sha256=receipt.plan.sha256))
        second = asyncio.run(replay_krx_history_aggregate(root=output / "krx-inputs", receipt=receipt,
            expected_plan_sha256=receipt.plan.sha256))
        if first != second:
            raise ValueError("krx_replay_nondeterministic")
        krx = {**first, "deterministic_second_replay": True}
    except (ValueError, OSError) as exc:
        krx = {"status": "BLOCKED", "error": str(exc), "blocker": "KRX_ACQUISITION_HISTORY_REPLAY"}
    durable_json(output / "krx-replay-proof.json", krx, exclusive=True)
    result = {"terminal": "M12DS_R6_R5F_R2A_R5_TWO_BLOCKER_GAP_REMAINS",
        "blockers": ["STOCK_MATERIALIZATION"] + ([] if krx["status"] == "PASS" else ["KRX_ACQUISITION_HISTORY_REPLAY"]),
        "NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED": False, "complete_source_adapter_qualified": False,
        "complete_ai_adapter_qualified": False, "source_gate": "FAILED_CLOSED",
        "full_packet_assembly": "NOT_REACHED", "R2B": "NOT_GENERATED_NOT_EXECUTED", "R3": "BLOCKED",
        "provider_calls": 0, "model_calls": 0, "rendered_messages": 0, "production_mutations": 0}
    durable_json(output / "prequalification.json", result, exclusive=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.archive, args.output), indent=2))
