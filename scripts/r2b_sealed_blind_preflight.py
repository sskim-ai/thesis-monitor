"""Seal source-only review before checking the unchanged Core consumption gate.

No model, provider, database, scheduler, or delivery entry point is imported or
called. A failed whole-cohort preflight is terminal for this instruction.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

from app.services.direction_timing_ownership_service import OwnedEvidencePacket
from app.services.unified_run_artifacts import SECRET_KEY, durable_bytes, durable_json
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE
from app.services.unified_stock_owner import reject_downstream
from scripts import m12ds_r4_r4_policy as policy
from scripts.m12db_model_view_readiness import _batch_topology
from scripts.sealed_cohort_offline_proof import network_guard

REPO = Path(__file__).resolve().parents[1]
INSTRUCTIONS = REPO / "docs/work-instructions/20260927-r2b-sealed-source-blind-review"
SOURCE_ZIP_SHA = "5cd89052657b6d4d29d174415fa1ce3dd686ccf20a14ea342256feda28d9836a"
INSTRUCTION_ZIP_SHA = "cb572a12b0d51345cade3ec0b735cbb20c817ee047aac3a8f66a8fce18f1205c"
BASE = "b6cc049118131000122d717305d83c1b9e78ae6b"
STEM = "thesis-monitor-20260927-r2b"


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(root, name, value):
    durable_json(root / name, value, exclusive=True)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def read_verified_archive(path, expected_sha):
    if sha(path.read_bytes()) != expected_sha:
        raise ValueError("source_zip_sha_mismatch")
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("bundle-manifest.json"))
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != set(manifest) | {"bundle-manifest.json"}:
            raise ValueError("source_manifest_set_mismatch")
        for name, entry in manifest.items():
            parsed = Path(name)
            if parsed.is_absolute() or ".." in parsed.parts:
                raise ValueError("source_archive_path_invalid")
            raw = archive.read(name)
            if sha(raw) != entry["sha256"] or len(raw) != entry["bytes"]:
                raise ValueError("source_artifact_hash_mismatch:" + name)
        return manifest


def source_only_stock(stock, authority):
    if stock.get("contract") == "fresh-financial-stock-owner-v1":
        from scripts.fresh_source_only_export import source_only_fresh_stock
        return source_only_fresh_stock(stock, authority)
    packet = stock["packet"]
    reject_downstream(packet)
    result = {"source_packet": packet, "financial_bindings": stock["financial_bindings"],
        "financial_state": stock["financial_state"], "source_graph": stock["source_graph"],
        "numeric_registry_graph": stock["numeric_registry_graph"],
        "evidence_reference_graph": stock["evidence_reference_graph"],
        "data_use_authority": authority["authority"],
        "original_source_packet_sha256": digest(packet)}
    # Domain/role assignment and observation-effect policy are not reviewer input.
    for name in ("persisted_event_receipt", "event_binding", "versioned_business_receipt"):
        if name in stock:
            result[name] = stock[name]
    reject_downstream(result)
    return result


def stock_preflight(stock, authority):
    owned = OwnedEvidencePacket.model_validate(stock["ownership"])
    if owned.source_packet.model_dump(mode="json") != stock["evidence_packet"]:
        raise ValueError("owned_evidence_packet_mismatch")
    metadata = [r for r in stock["evidence_packet"]["evidence"] if r["ref_id"] in owned.core_refs]
    records = authority["authority"]["authority_records"]
    permitted = [r["ref_id"] for r in records if r["authority_state"] == "RESOLVED"
                 and "OVERALL_DIRECTION" in r["allowed_uses"]]
    fields = policy.frozen_fact_fields(stock["packet"], stock["ticker"], metadata)
    observations = policy.observations(metadata, authority["authority"], fields)
    return {"ticker": stock["ticker"], "market": stock["market"],
        "source_assembly_status": stock["status"],
        "source_packet_sha256": digest(stock["packet"]),
        "source_authority_sha256": digest(authority),
        "source_owned_core_refs": len(metadata), "directional_authority_refs": sorted(permitted),
        "observed_propositions": len(observations),
        "status": "PASS" if observations else "BLOCKED",
        "denial_reason": None if observations else "FRESH_CORE_DIRECTIONAL_ENTITLEMENT_INCOMPLETE",
        "financial_source_state": stock["financial_state"],
        "event_authority": [{k: r.get(k) for k in ("ref_id", "authority_state", "allowed_uses", "prohibited_uses")}
                            for r in records if r["ref_id"].startswith("canonical:event:")],
        "authority_widened": False}


def cohort_preflight(combined):
    if set(combined["packets"]) != {"us", "kr"}:
        raise ValueError("exact_two_markets_required")
    rows = []
    for market, tickers in UNIVERSE.items():
        stocks = combined["packets"][market]["stocks"]
        if set(stocks) != set(tickers):
            raise ValueError("exact_frozen_universe_required")
        for ticker in tickers:
            rows.append(stock_preflight(stocks[ticker], combined["authority_graph"]["stocks"][ticker]))
    ready = sum(row["status"] == "PASS" for row in rows)
    return {"status": "PASS" if ready == 22 else "BLOCKED", "ready_count": ready,
        "active_count": len(rows), "allow_model_dispatch": ready == 22,
        "owner": "scripts.m12ds_r4_r4_policy.observations",
        "gate_owner": "scripts.m12ds_r2_shadow_reproof.Reproof.prepare",
        "rows": rows, "old_ai_outputs_read": False, "new_model_calls": 0}


def known_secrets():
    values = []
    for env in (Path("/Users/sskim/Codex/thesis-monitor/.env"),
                Path("/Users/sskim/Codex/ohlcv-analyst/.env")):
        for line in env.read_text().splitlines():
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            key, value = line.split("=", 1)
            value = value.strip().strip("\"'")
            if SECRET_KEY.search(key) and len(value) >= 8:
                values.append(value.encode())
    return values


def seal(folder, target, secrets):
    paths = sorted(p for p in folder.rglob("*") if p.is_file())
    pattern = re.compile(rb"\b\d{7,}:[A-Za-z0-9_-]{20,}|\bsk-[A-Za-z0-9_-]{16,}")
    for path in paths:
        raw = path.read_bytes()
        if any(s in raw for s in secrets) or pattern.search(raw):
            raise ValueError("secret_scan_failed:" + str(path.relative_to(folder)))
    save(folder, "secret-scan.json", {"status": "PASS", "files": len(paths),
        "known_values_checked": True, "token_patterns_checked": True,
        "secrets_exported": False, "auth_bodies_exported": False})
    paths.append(folder / "secret-scan.json")
    manifest = {str(p.relative_to(folder)): {"sha256": sha(p.read_bytes()), "bytes": p.stat().st_size}
                for p in paths}
    save(folder, "bundle-manifest.json", manifest)
    with zipfile.ZipFile(target, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in paths + [folder / "bundle-manifest.json"]:
            archive.write(path, folder.name + "/" + str(path.relative_to(folder)))
    with zipfile.ZipFile(target) as archive:
        if set(archive.namelist()) != {folder.name + "/" + n for n in manifest} | {folder.name + "/bundle-manifest.json"}:
            raise ValueError("sealed_archive_manifest_mismatch")
        for name, item in manifest.items():
            data = archive.read(folder.name + "/" + name)
            if sha(data) != item["sha256"] or len(data) != item["bytes"]:
                raise ValueError("sealed_archive_hash_mismatch")
    checksum = sha(target.read_bytes())
    durable_bytes(target.with_suffix(".zip.sha256"), (checksum + "  " + target.name + "\n").encode(), exclusive=True)
    return {"filename": target.name, "sha256": checksum, "bytes": target.stat().st_size,
            "manifest_entries": len(manifest), "sealed_at": now()}


def run(bundle, attachment, output):
    counts = network_guard()
    if output.exists() or git("status", "--porcelain"):
        raise ValueError("new_output_and_clean_commit_required")
    if sha(attachment.read_bytes()) != INSTRUCTION_ZIP_SHA:
        raise ValueError("instruction_zip_sha_mismatch")
    bindings = json.loads((INSTRUCTIONS / "source-bindings.json").read_bytes())
    if bindings["implementation"] != BASE:
        raise ValueError("source_implementation_mismatch")
    manifest = read_verified_archive(bundle, SOURCE_ZIP_SHA)
    source = {}
    with zipfile.ZipFile(bundle) as archive:
        for kind, name in bindings["source_paths"].items():
            raw = archive.read(name)
            source[kind] = json.loads(raw)
            durable_bytes(output / "verified-source" / Path(name).name, raw, exclusive=True)
    expected = bindings["hashes"]
    for kind in ("seed", "combined", "authority", "us", "kr"):
        wanted = expected["packet_hashes"][kind] if kind in {"us", "kr"} else expected[
            {"seed": "seed_sha256", "combined": "combined_sha256", "authority": "authority_graph_sha256"}[kind]]
        if digest(source[kind]) != wanted:
            raise ValueError("instruction_semantic_hash_mismatch:" + kind)
    combined = source["combined"]
    if (combined["seed"] != source["seed"] or combined["authority_graph"] != source["authority"]
            or any(combined["packets"][m] != source[m] for m in ("us", "kr"))):
        raise ValueError("cross_artifact_binding_mismatch")
    generation = "20260927-r2b-blind-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    identity = {"generation_id": generation, "source_run_id": bindings["source_run_id"],
        "source_cutoff": bindings["source_cutoff"], "source_hashes": expected,
        "source_implementation": BASE, "controller_commit": git("rev-parse", "HEAD"),
        "instruction_zip_sha256": INSTRUCTION_ZIP_SHA, "source_zip_sha256": SOURCE_ZIP_SHA,
        "manifest_entries_verified": len(manifest), "provider_refresh": 0}
    save(output, "source-verification.json", identity)
    blind = output / "BLIND_SOURCE_REVIEW"
    save(blind, "source-identity.json", identity)
    for market, tickers in UNIVERSE.items():
        for ticker in tickers:
            stock = combined["packets"][market]["stocks"][ticker]
            item = source_only_stock(stock, combined["authority_graph"]["stocks"][ticker])
            save(blind, f"stocks/{ticker}.json", item)
        market_item = {"market_sources": source[market]["market_sources"],
                       "original_whole_packet_sha256": expected["packet_hashes"][market]}
        reject_downstream(market_item)
        save(blind, f"markets/{market}.json", market_item)
    for name, key in (("publication-context", "publication_context"), ("night-futures", "night"),
                      ("optional-denials", "optional_denials"), ("issuer-bridge", "issuer_bridge")):
        item = source["authority"][key]
        reject_downstream(item)
        save(blind, name + ".json", item)
    save(blind, "external-comparison-template.json", {"status": "UNFILLED", "generation_id": generation,
        "reviewer": None, "frozen_at": None, "blind_pack_sha256": None,
        "subjects": [{"ticker": t, "direction": None, "buy_sell": None, "hold_lean": None,
            "new_buyer": None, "holder": None, "entry_mode": None, "confidence": None,
            "fact_ids": [], "rationale": None} for ts in UNIVERSE.values() for t in ts]})
    readme = """# Independent Source Review

This bundle was frozen before model dispatch. It contains 22 stock source packets,
US/KR market source components, two night-futures products, publication context,
denials and source-use limits. It contains no AI decisions, previous candidates,
rendered messages, policy-expected answers or observation-effect model prompts.

Review at the recorded source cutoff, not as a current production recommendation.
Source dates, financial periods and market session dates are distinct. Null and
unavailable are not zero. Stored thesis/configured signals are user input, not
observed business evidence or verified forecasts. Numeric chart/trend relations
are deterministic source features, not investment direction labels.

SNDK's persisted RSS/Seeking Alpha headline requires review and is CONTEXT only.
Do not treat its amount as a verified contract or official financial result.
SKHY issuer evidence does not transfer to per-share/security valuation. Preserve
all CF/WC/estimate/flow denials and authority restrictions. Source validity does
not establish decision or production readiness.

Write your independent assessment without opening MONITORING_AI_RESULT. Freeze
it first; leave unrecorded fields null/empty. Add the delivered blind ZIP SHA to
your completed template. Comparison/reveal requires that external freeze and
subsequent permission. The empty template is not a completed review.
"""
    durable_bytes(blind / "README.md", readme.encode(), exclusive=True)
    secrets = known_secrets()
    blind_receipt = seal(blind, output / (STEM + "-BLIND_SOURCE_REVIEW.zip"), secrets)
    save(output, "blind-freeze.json", {**blind_receipt, "model_calls_before_seal": 0,
                                     "generation_id": generation})
    freeze = {**identity, "blind": blind_receipt, "frozen_at": now(),
        "batch_plan": _batch_topology(), "stage_order": ["market", "core", "pass-a", "pass-b"],
        "model": "gpt-5.6-sol", "effort": "xhigh", "timeout_seconds": 1200,
        "max_calls": {"market": 2, "core": 8, "pass-a": 8, "pass-b": 8},
        "transport_retries": 0, "semantic_retries": 0, "fallback": 0, "judge": 0,
        "source_use_gate_required_before_any_model": True,
        "code": {str(p.relative_to(REPO)): sha(p.read_bytes()) for base in ("app", "scripts")
                 for p in sorted((REPO / base).rglob("*")) if p.is_file() and p.suffix in {".py", ".json"}}}
    save(output, "execution-plan-freeze.json", freeze)
    gate = cohort_preflight(combined)
    if sha((output / blind_receipt["filename"]).read_bytes()) != blind_receipt["sha256"]:
        raise ValueError("blind_freeze_drift")
    save(output, "core-source-use-preflight.json", gate)
    save(output, "execution-state.json", {"generation_id": generation,
        "status": "PREFLIGHT_PASS_NOT_DISPATCHED" if gate["allow_model_dispatch"] else "BLOCKED_BEFORE_MODEL",
        "market_calls": 0, "core_calls": 0, "a_calls": 0, "b_calls": 0,
        "rendered_previews": 0, "expected_previews": 24, "network_guard": counts,
        "source_modified": False, "authority_widened": False, "reveal_gate": "CLOSED",
        "external_review": "AWAITING_INDEPENDENT_FREEZE", "stopped_at": now()})
    print(json.dumps({"blind_sealed": True, "source_verified": len(manifest),
        "preflight": gate["status"], "core_eligible": gate["ready_count"],
        "blocked": [r["ticker"] for r in gate["rows"] if r["status"] != "PASS"],
        "model_calls": 0, "network_calls": counts["network_attempts"]}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--attachment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.bundle, args.attachment, args.output)


if __name__ == "__main__":
    main()
