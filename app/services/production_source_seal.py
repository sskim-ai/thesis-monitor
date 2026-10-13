"""Request completeness is distinct from downstream value qualification."""
from collections import Counter
import json
from pathlib import Path

from app.services.production_source_plan import ProductionRequestPlan
from app.services.sealed_fresh_dispatch import _binding_parent, consume_bound_result
from app.services.sealed_response_binding import resolve_response_binding, SlotNotSelected
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest


def read(path):
    return json.loads(Path(path).read_bytes())


def row_count_proofs(root, frozen, outcome):
    owner = Path(frozen["native_owner_root"]) / "app/providers/kiwoom.py"
    if sha256_bytes(owner.read_bytes()) != frozen["native_owner"]["owner_files"]["app/providers/kiwoom.py"]:
        raise ValueError("production_native_owner_drift")
    result = {}
    replay = outcome.get("phases", {}).get("stock-native-replay", {}).get("value", {})
    if replay.get("status") == "PASS":
        replay_rows = {r["entry_id"]: r for r in replay["rows"]}
        for index, entry in enumerate(frozen["stock_plan"]["reads"], 1):
            path = root / f"native/stocks/role-{index:03d}.receipt.json"
            receipt = read(path)
            normalized = path.parent / receipt["normalized_artifact"]
            row = replay_rows[entry["entry_id"]]
            if (receipt["entry"] != entry or receipt["status"] != "CAPTURED" or row["status"] != "PASS"
                    or sha256_bytes(normalized.read_bytes()) != receipt["normalized_sha256"]
                    or receipt["normalized_sha256"] != row["normalized_sha256"]
                    or any(sha256_bytes((path.parent / p["artifact"]).read_bytes()) != p["source_sha256"]
                           for p in receipt["pages"])):
                raise ValueError("production_native_row_count_proof_invalid")
            result["stock:" + entry["entry_id"]] = dict(count=entry["count"], rows=len(read(normalized)),
                pages=len(receipt["pages"]), proof_sha256=sha256_bytes(path.read_bytes()))
    for request in frozen.get("us_market_reads", []):
        value = outcome["logical_results"].get(request["role"])
        if value and value["status"] == "PASS":
            path = root / "dispatch" / value["attempts"][-1]["artifact"]
            if sha256_bytes(path.read_bytes()) != value["raw_sha256"]:
                raise ValueError("production_market_raw_proof_invalid")
            raw = read(path)
            if isinstance(raw.get("result_list"), list):
                result[request["role"]] = dict(count=request["params"]["count"], rows=len(raw["result_list"]),
                    pages=1, proof_sha256=value["receipt_sha256"])
    return result


def slot_dispositions(root, frozen, outcome):
    root = Path(root)
    plan = ProductionRequestPlan.model_validate(frozen["plan"])
    finals = {read(p)["logical_request_id"]: read(p) for p in (root / "dispatch/receipts").glob("*/final.json")}
    proofs = row_count_proofs(root, frozen, outcome)
    descriptors = {d.logical_request_id: d for d in plan.descriptors}
    if set(finals) - set(descriptors):
        raise ValueError("production_undeclared_source_receipt")
    states = {}

    def classify(key):
        if key in states:
            return states[key]
        descriptor, final = descriptors[key], finals.get(key)
        proof = proofs.get(descriptor.consumer_role)
        count_stop = (descriptor.provider == "kiwoom" and descriptor.response_binding
            and descriptor.response_binding.kind == "KIWOOM_CONTINUATION" and proof
            and descriptor.page_ordinal > proof["pages"] and proof["rows"] >= proof["count"] > 0)
        if final is not None:
            if final["status"] == "PASS":
                consume_bound_result(root=root / "dispatch", plan=plan, logical_id=key,
                                     receipt_sha256=final["receipt_sha256"])
                value = "ACQUIRED_BOUND_BODY_PENDING_OWNER_QUALIFICATION"
            else:
                value = {"NOT_SELECTED": "NOT_ACTIVATED_EXACT_SELECTION_RULE",
                    "FAILED": "ACQUISITION_OR_NORMALIZATION_FAILED"}.get(final["status"], "SYSTEMIC_STOP")
        elif descriptor.response_binding:
            parents = {k: classify(k) for k in descriptor.response_binding.parents}
            if any(v in {"MISSING_REQUIRED_ATTEMPT", "SYSTEMIC_STOP", "ACTIVATION_UNRESOLVED"} for v in parents.values()):
                value = "ACTIVATION_UNRESOLVED"
            elif any(v in {"ACQUISITION_OR_NORMALIZATION_FAILED", "NOT_ACTIVATED_PARENT_FAILED"} for v in parents.values()):
                value = "NOT_ACTIVATED_PARENT_FAILED"
            elif any(v.startswith("NOT_ACTIVATED") for v in parents.values()):
                value = "NOT_ACTIVATED_PARENT_NOT_SELECTED"
            else:
                bound = {k: _binding_parent(root / "dispatch", plan, k, finals[k]["receipt_sha256"]) for k in parents}
                try:
                    resolve_response_binding(descriptor.request_json, descriptor.response_binding, bound)
                except SlotNotSelected:
                    value = "NOT_ACTIVATED_EXACT_SELECTION_RULE"
                else:
                    value = "MISSING_REQUIRED_ATTEMPT"
            if value in {"MISSING_REQUIRED_ATTEMPT", "ACTIVATION_UNRESOLVED"} and count_stop:
                value = "NOT_ACTIVATED_FROZEN_NATIVE_ROW_TARGET_SATISFIED"
        else:
            value = "MISSING_REQUIRED_ATTEMPT" if descriptor.mandatory else "NOT_ACTIVATED_OPTIONAL_SLOT"
        states[key] = value
        return value

    rows = [dict(subject=d.subject, logical_request_id=d.logical_request_id, descriptor_sha256=d.descriptor_sha256,
        role=d.consumer_role, mandatory=d.mandatory, disposition=classify(d.logical_request_id),
        row_count_proof=proofs.get(d.consumer_role), receipt_sha256=finals.get(d.logical_request_id, {}).get("receipt_sha256"))
        for d in plan.descriptors]
    unresolved = {"MISSING_REQUIRED_ATTEMPT", "SYSTEMIC_STOP", "ACTIVATION_UNRESOLVED"}
    return dict(contract="production-source-slot-dispositions-v1", generation_id=plan.generation_id,
        plan_sha256=plan.plan_sha256, status="FAIL" if any(r["disposition"] in unresolved for r in rows) else "PASS",
        rows=rows, counts=dict(Counter(r["disposition"] for r in rows)),
        acquired_body_does_not_claim_value_qualification=True)


def corpus_index(root):
    root = Path(root)
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("production_source_seal_symlink_denied")
        if path.is_file():
            raw = path.read_bytes()
            result[str(path.relative_to(root))] = dict(bytes=len(raw), sha256=sha256_bytes(raw))
    return result


def seal_collection(root, *, seal_path, frozen, outcome):
    slots = slot_dispositions(root, frozen, outcome)
    if slots["status"] != "PASS" or "systemic_stop" in outcome["phases"]:
        raise ValueError("production_source_request_coverage_gap")
    value = dict(contract="production-source-collection-seal-v1", generation_id=frozen["generation_id"],
        source_plan_sha256=digest(frozen), slot_dispositions=slots, files=corpus_index(root),
        model_calls_before_seal=0, value_qualification_claimed=False, recollection_after_seal_allowed=False)
    value["receipt_sha256"] = digest(value)
    durable_json(seal_path, value, exclusive=True)
    return value


def verify_collection_seal(root, seal, frozen):
    if (seal["receipt_sha256"] != digest({k: v for k, v in seal.items() if k != "receipt_sha256"})
            or seal["generation_id"] != frozen["generation_id"] or seal["source_plan_sha256"] != digest(frozen)
            or seal["files"] != corpus_index(root)):
        raise ValueError("production_source_seal_changed")
