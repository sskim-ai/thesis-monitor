"""R2B-R3 detached quality supplement and whole-cohort offline readiness."""
import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import sys
import zipfile

from app.services import canonical_business_quality_owner as quality
from app.services.unified_snapshot_contract import digest
from scripts import r2b_r2_preflight as previous
from scripts import r2b_r3_quality as binding
from scripts import r2b_r1_offline_closure as r1
from scripts import r2b_sealed_blind_preflight as io
from scripts.sealed_cohort_offline_proof import network_guard
from scripts.unified_stock_owner_proof import POLICY


def run(args):
    network = network_guard()
    args.output.mkdir(parents=True, exist_ok=False)
    audit = previous.SourceReadAudit([args.source_zip, args.blind_zip, args.receipt, args.applicability],
                                    [args.source_zip.parent, args.blind_zip.parent, args.receipt.parent])
    sys.addaudithook(audit)
    members = []
    manifest = io.read_verified_archive(args.source_zip, io.SOURCE_ZIP_SHA)
    quality.require(io.sha(args.blind_zip.read_bytes()) == r1.BLIND_SHA, "blind_zip_changed")
    quality.require(io.sha(args.receipt.read_bytes()) == r1.RECEIPT_SHA, "neutral_receipt_changed")
    inventory = json.loads(args.applicability.read_bytes())
    quality.require(inventory["implementation_changes_started"] is False and len(inventory["rows"]) == 22,
                    "preimplementation_applicability_required")
    rows, supplements, materials, prepared, gaps = [], {}, [], {}, []
    generation = "20260928-r2b-r3-" + datetime.now().strftime("%Y%m%dT%H%M%S")
    with zipfile.ZipFile(args.source_zip) as archive, zipfile.ZipFile(args.blind_zip) as blind:
        def read(name):
            members.append({"archive": "REV10", "path": name, "sha256": manifest[name]["sha256"]})
            return archive.read(name)
        combined = json.loads(read("whole-1/combined-full-source-packet.json"))
        for name, wanted in r1.SOURCE_HASHES.items():
            quality.require(digest(json.loads(read("whole-1/" + name))) == wanted, "source_identity_mismatch")
        cutoff = datetime.fromisoformat(combined["seed"]["started_at"])
        acquisition = json.loads(read("input/sealed-live/rev8-full-source-acquisition-plan.json"))
        versions = {t: read("input/sealed-live/class-c/business-versioned-" + t + ".json")
                    for ts in io.UNIVERSE.values() for t in ts}
        locals_ = {m: json.loads(read("input/sealed-live/class-c/local-" + m + ".json")) for m in io.UNIVERSE}
        owner_inputs = dict(versions=versions, version_hashes=acquisition["class_c_versions"],
                            local_seeds=list(locals_.values()), cutoff=cutoff, policy=POLICY)
        for item in inventory["rows"]:
            ticker, market = item["ticker"], item["market"]
            original = combined["packets"][market]["stocks"][ticker]
            stock = original
            authority = combined["authority_graph"]["stocks"][ticker]
            try:
                if item["classification"] == "EXPECTED_OWNER_OUTPUT_RECONSTRUCTIBLE":
                    supplement = quality.derive(stock=stock, **owner_inputs)
                    supplements[ticker] = supplement
                    name = "BLIND_SOURCE_REVIEW/stocks/" + ticker + ".json"
                    raw = blind.read(name)
                    members.append({"archive": "BLIND_SOURCE_ONLY", "path": name, "sha256": io.sha(raw)})
                    materials.append(binding.blind_materiality(supplement, json.loads(raw)))
                    stock, authority = binding.bind_supplement(stock, authority, supplement, owner_inputs=owner_inputs)
                projection = binding.require_quality_owner(stock, authority, decision_mode=item["decision_mode"])
                row, inputs = previous.preflight_subject(stock, authority, locals_[market], generation=generation,
                    cutoff=combined["seed"]["started_at"], defer_b=True,
                    source_view_owner=binding.quality_source_view)
                row["quality_owner_projection"] = projection
                row["original_source_sha256"] = digest(original)
                row["quality_authority"] = [r for r in authority["authority"]["authority_records"]
                                            if r["ref_id"].startswith("canonical:financial_quality:")]
                prepared[ticker] = inputs
            except (ValueError, KeyError, TypeError) as exc:
                gap = dict(ticker=ticker, evidence_class=item["accepted_business_evidence_class"],
                    source_period=item["source_periods"], missing_input_or_contract=str(exc),
                    expected_owner="canonical reported business quality", not_applicable_valid=False)
                gaps.append(gap)
                row = dict(ticker=ticker, market=market, Core="NOT_RETESTED", A="BLOCKED", B="DEPENDENCY_BLOCKED",
                    NewBuyer="BLOCKED", Holder="DEPENDENCY_BLOCKED", status="BLOCKED", blocker=str(exc),
                    model_visible_quality_effect=None)
            rows.append(row)
            print(ticker, row["A"], row.get("blocker"), flush=True)
        a_ready = sum(r.get("A") == "PASS" for r in rows)
        if a_ready == 22:
            for row in rows:
                data = prepared[row["ticker"]]
                if data["mode"] == "UNKNOWN_LIMIT":
                    continue
                try:
                    ctx, entries, valuation = previous.b_input(data["view"], **data["b_probe_inputs"])
                    probe = data["b_probe_inputs"]
                    row.update(B="PASS", Holder="PASS", status="PASS", b_context_sha256=digest(ctx),
                        b_schema=previous.schema_check(previous.c.decision_schema(data["mode"],
                            probe["capability"], valuation, entries, {})))
                except (ValueError, KeyError, TypeError) as exc:
                    row.update(B="BLOCKED", Holder="BLOCKED", status="BLOCKED", blocker=str(exc))
        else:
            for row in rows:
                row.update(B="WHOLE_A_DEPENDENCY_BLOCKED", Holder="WHOLE_A_DEPENDENCY_BLOCKED", status="BLOCKED")
    changed = [r for r in materials if r["status"] == "MATERIAL_SOURCE_VIEW_CHANGED"]
    ready = sum(r["status"] == "PASS" for r in rows)
    terminal = ("R2B_R3_TYPED_QUALITY_OWNER_GAP" if gaps else
                "R2B_R3_A_MATERIALIZER_PARITY_GAP" if ready != 22 else
                "R2B_R3_BLIND_REVIEW_MATERIAL_SOURCE_VIEW_CHANGED" if changed else "READY_FOR_REQUEST_FREEZE")
    summary = dict(terminal=terminal, generation_id=generation, status="PASS" if ready == 22 and not changed else "BLOCKED",
        input_ready=ready, stage_ready={s: sum(r.get(s) == "PASS" for r in rows) for s in ("Core", "A", "B")},
        classification_counts=dict(Counter(r["classification"] for r in inventory["rows"])),
        supplement_count=len(supplements), supplement_sha256=digest(supplements),
        material_source_view_changed_tickers=[r["ticker"] for r in changed],
        model_calls=dict(Market=0, Core=0, A=0, B=0), actual_messages=0, provider_calls=0,
        model_input_binding_issued=False, production_side_effects=0,
        independent_assessment_content_read=False, reveal_gate="CLOSED", source_hashes=r1.SOURCE_HASHES,
        blind_sha256=r1.BLIND_SHA, neutral_receipt_sha256=r1.RECEIPT_SHA,
        implementation=io.git("rev-parse", "HEAD"), worktree_clean=not bool(io.git("status", "--porcelain")),
        probes_not_model_outputs=True)
    for name, data in (("summary.json", summary), ("preflight.json", {**summary, "rows": rows}),
        ("quality-supplements.json", supplements), ("blind-materiality-audit.json", materials),
        ("unresolved-owner-gaps.json", gaps), ("prepared-inputs.json", prepared),
        ("source-read-audit.json", {**audit.receipt(), "archive_members": members, "network": network})):
        io.save(args.output, name, data)
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("output", "source-zip", "blind-zip", "receipt", "applicability"):
        parser.add_argument("--" + name, type=Path, required=True)
    run(parser.parse_args())
