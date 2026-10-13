"""Whole sealed cohort readiness. Offline probes are never model candidates."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import zipfile

from scripts import r2b_r2_contract as c
from scripts import r2b_r1_offline_closure as r1
from scripts import r2b_sealed_blind_preflight as io
from app.services import canonical_monitoring_owner as owner  # noqa: F401
from scripts.sealed_cohort_offline_proof import network_guard


class SourceReadAudit:
    """Exact source-file allowlist; external assessment content stays sealed."""

    def __init__(self, allowed, protected_roots):
        self.allowed = {Path(p).resolve() for p in allowed}
        self.roots = tuple(Path(p).resolve() for p in protected_roots)
        self.reads = Counter()
        self.denials = []

    def __call__(self, event, args):
        if event != "open" or not isinstance(args[0], (str, bytes, Path)):
            return
        path = Path(args[0].decode() if isinstance(args[0], bytes) else args[0]).resolve()
        if "INDEPENDENT_BLIND_ASSESSMENT" in path.name.upper():
            self.denials.append("external_assessment_content_forbidden")
            raise PermissionError("external_assessment_content_forbidden")
        mode = args[1]
        reading = mode is None or "r" in mode or "+" in mode
        if reading and any(path.is_relative_to(root) for root in self.roots):
            if path not in self.allowed:
                self.denials.append("source_read_outside_allowlist")
                raise PermissionError("source_read_outside_allowlist")
            self.reads[str(path)] += 1

    def receipt(self):
        return dict(allowlist=sorted(map(str, self.allowed)), reads=dict(self.reads), denials=self.denials,
                    independent_assessment_content_read=False, scope="preflight_python_open_events")


def require_whole_ready(receipt):
    expected = {ticker for tickers in io.UNIVERSE.values() for ticker in tickers}
    rows = receipt.get("rows", [])
    c._require(receipt.get("status") == "PASS" and receipt.get("ready") == 22
               and len(rows) == 22 and {r["ticker"] for r in rows} == expected,
               "whole_cohort_model_input_gap")
    for row in rows:
        c._require(all(row.get(stage) == "PASS" for stage in ("Core", "A", "B", "NewBuyer", "Holder")),
                   "whole_cohort_stage_gap")
        if row["decision_mode"] == "EVIDENCE_BASED":
            c._require(row.get("a_materialization", {}).get("status") == "PASS", "materialization_proof_missing")
    return {"status": "READY_FOR_REQUEST_FREEZE", "actual_model_dispatch_authorized": False}


from app.services.canonical_subject_preflight import schema_check  # noqa: E402,F401


from app.services.canonical_subject_preflight import synthetic_shape_probe  # noqa: E402,F401


from app.services.canonical_subject_preflight import materialization_probe  # noqa: E402,F401


from app.services.canonical_monitoring_input import subject_inputs  # noqa: E402,F401


from app.services.canonical_monitoring_input import a_input  # noqa: E402,F401


from app.services.canonical_monitoring_input import b_input  # noqa: E402,F401


from app.services.canonical_subject_preflight import preflight_subject  # noqa: E402,F401


def run(args):
    network = network_guard()
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    audit = SourceReadAudit([args.source / name for name in r1.SOURCE_HASHES] + [
        args.source_zip, args.blind_zip, args.receipt],
        [args.source.parent, args.source_zip.parent, args.receipt.parent])
    sys.addaudithook(audit)
    manifest = io.read_verified_archive(args.source_zip, io.SOURCE_ZIP_SHA)
    source = {}
    for name, wanted in r1.SOURCE_HASHES.items():
        raw = (args.source / name).read_bytes()
        source[name] = json.loads(raw)
        c._require(io.digest(source[name]) == wanted and io.sha(raw) == manifest["whole-1/" + name]["sha256"],
                   "sealed_source_mismatch:" + name)
    for path, expected in ((args.blind_zip, r1.BLIND_SHA), (args.receipt, r1.RECEIPT_SHA)):
        c._require(io.sha(path.read_bytes()) == expected, "blind_or_receipt_identity")
    combined = source["combined-full-source-packet.json"]
    generation = "20260928-r2b-r2-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rows, prepared = [], {}
    with zipfile.ZipFile(args.source_zip) as archive:
        for market, tickers in io.UNIVERSE.items():
            local = json.loads(archive.read(f"input/sealed-live/class-c/local-{market}.json"))
            c._require(set(combined["packets"][market]["stocks"]) == set(tickers), "exact_universe")
            for ticker in tickers:
                try:
                    row, inputs = preflight_subject(combined["packets"][market]["stocks"][ticker],
                        combined["authority_graph"]["stocks"][ticker], local,
                        generation=generation, cutoff=combined["seed"]["started_at"])
                    prepared[ticker] = inputs
                except (ValueError, KeyError, TypeError) as exc:
                    row = {"ticker": ticker, "market": market, "status": "BLOCKED", "blocker": str(exc)}
                rows.append(row)
                print(json.dumps({k: row.get(k) for k in ("ticker", "status", "decision_mode", "blocker")}), flush=True)
    ready = sum(r["status"] == "PASS" for r in rows)
    summary = dict(generation_id=generation, status="PASS" if ready == 22 else "BLOCKED", ready=ready,
        active_count=len(rows), modes=dict(Counter(r.get("decision_mode") for r in rows)),
        model_calls=0, provider_calls=0, network=network, independent_assessment_read=False,
        blind_sha256=r1.BLIND_SHA, receipt_sha256=r1.RECEIPT_SHA, source_hashes=r1.SOURCE_HASHES,
        implementation=io.git("rev-parse", "HEAD"), worktree_clean=not bool(io.git("status", "--porcelain")),
        probes_not_model_outputs=True, all_request_binding_sealed=False, allow_model_dispatch=False)
    summary.update(terminal="READY_FOR_REQUEST_FREEZE" if ready == 22 else "R2B_R2_WHOLE_COHORT_MODEL_INPUT_GAP",
                   stage_ready={stage: sum(r.get(stage) == "PASS" for r in rows)
                                for stage in ("Core", "A", "B", "NewBuyer", "Holder")})
    io.save(out, "preflight.json", {**summary, "rows": rows})
    io.save(out, "prepared-inputs.json", prepared)
    io.save(out, "summary.json", summary)
    io.save(out, "source-read-audit.json", audit.receipt())
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("output", "source", "source-zip", "blind-zip", "receipt"):
        parser.add_argument("--" + name, type=Path, required=True)
    run(parser.parse_args())
