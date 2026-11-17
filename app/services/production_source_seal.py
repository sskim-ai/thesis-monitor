"""Request completeness is distinct from downstream value qualification."""
from collections import Counter
from datetime import datetime, timedelta
import json
from pathlib import Path
from zoneinfo import ZoneInfo

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
            path = root / "dispatch/raw" / request["role"] / "source.body"
            if sha256_bytes(path.read_bytes()) != value["raw_sha256"]:
                raise ValueError("production_market_raw_proof_invalid")
            raw = read(path)
            if isinstance(raw.get("result_list"), list):
                result[request["role"]] = dict(count=request["params"]["count"], rows=len(raw["result_list"]),
                    pages=1, proof_sha256=value["receipt_sha256"])
    return result


def slot_dispositions(root, frozen, outcome):
    root = Path(root)
    if frozen.get('scope') == 'SELECTED_ORIGINAL_RESEARCH_V1':
        from app.services.selected_source_plan import SelectedRequestPlan
        plan = SelectedRequestPlan.model_validate(frozen['plan'])
    else:
        plan = ProductionRequestPlan.model_validate(frozen["plan"])
    finals = {read(p)["logical_request_id"]: read(p) for p in (root / "dispatch/receipts").glob("*/final.json")}
    proofs = row_count_proofs(root, frozen, outcome)
    descriptors = {d.logical_request_id: d for d in plan.descriptors}
    if set(finals) - set(descriptors):
        raise ValueError("production_undeclared_source_receipt")
    night_tail = _verified_night_probe_tail(root, frozen, outcome, plan, finals)
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
            if key in night_tail:
                value = "NOT_ACTIVATED_VERIFIED_NIGHT_PROBE_TERMINAL"
        states[key] = value
        return value

    rows = [dict(subject=d.subject, logical_request_id=d.logical_request_id, descriptor_sha256=d.descriptor_sha256,
        role=d.consumer_role, mandatory=d.mandatory, disposition=classify(d.logical_request_id),
        row_count_proof=proofs.get(d.consumer_role), receipt_sha256=finals.get(d.logical_request_id, {}).get("receipt_sha256"))
        for d in plan.descriptors]
    for row in rows:
        if row['logical_request_id'] in night_tail:
            row['night_probe_terminal_proof'] = night_tail[row['logical_request_id']]
    unresolved = {"MISSING_REQUIRED_ATTEMPT", "SYSTEMIC_STOP", "ACTIVATION_UNRESOLVED"}
    return dict(contract="production-source-slot-dispositions-v1", generation_id=plan.generation_id,
        plan_sha256=plan.plan_sha256, status="FAIL" if any(r["disposition"] in unresolved for r in rows) else "PASS",
        rows=rows, counts=dict(Counter(r["disposition"] for r in rows)),
        acquired_body_does_not_claim_value_qualification=True)


def _verified_night_probe_tail(root, frozen, outcome, plan, finals):
    """Replay the bounded original probe; success closes only its unopened tail."""
    candidate = frozen.get('candidate', {})
    phase = outcome.get('phases', {}).get('night', {})
    if (frozen.get('scope') != 'SELECTED_ORIGINAL_RESEARCH_V1' or frozen.get('selected_market') != 'us'
            or 'systemic_stop' in outcome.get('phases', {}) or phase.get('status') != 'CAPTURED_NOT_QUALIFIED'
            or candidate.get('consumer_policy', {}).get('us_night') != 'ORIGINAL_CURRENT_PROBE_ONLY'):
        return {}
    from app.jobs.probe_krx_night_futures import KRX_FUTURES_DAILY_URL
    from app.services.production_source_context import POLICY
    from app.services.unified_sealed_context import replay_night

    def plain(path):
        return path.is_file() and not any(p.is_symlink() for p in (path, *path.parents))

    try:
        start = datetime.fromisoformat(frozen['frozen_at'])
        day = start.astimezone(ZoneInfo('Asia/Seoul')).date()
        dates = [(day-timedelta(days=i)).isoformat() for i in range(7)]
        keys = ['night:KOSPI200:'+d for d in dates]
        descriptors = {d.logical_request_id:d for d in plan.descriptors}
        if (start != plan.frozen_at or plan.market != 'us' or plan.generation_id != frozen['generation_id']
                or candidate['night_query_dates'] != dates or frozen['query_kst_date'] != day.isoformat()):
            return {}
        for key, date in zip(keys, dates, strict=True):
            d = descriptors[key]
            wire = json.loads(d.request_json)
            if (d.provider != 'krx_night_futures' or d.subject != 'KOSPI200' or d.market != 'kr'
                    or d.consumer_role != key or d.endpoint_operation != 'fut_bydd_trd' or d.response_binding
                    or wire['method'] != 'GET' or wire['url'] != KRX_FUTURES_DAILY_URL+'?basDd='+date.replace('-','')):
                return {}
        prefix = [key for key in keys if key in finals]
        if not 0 < len(prefix) < len(keys) or prefix != keys[:len(prefix)]:
            return {}
        tail = keys[len(prefix):]
        for key in tail:
            path = root/'dispatch/receipts'/key
            raw = root/'dispatch'/descriptors[key].raw_path
            if (key in outcome['logical_results'] or path.exists() or path.is_symlink()
                    or raw.exists() or raw.is_symlink()):
                return {}
        query, phase_path = root/'night/query.json', root/'phase-night.json'
        paths = sorted((root/'night/probe').glob('receipt-*.json'))
        if (len(paths) != len(prefix) or (root/'night/history').exists() or (root/'night/history').is_symlink()
                or not all(plain(p) for p in [query,phase_path,*paths])
                or read(query) != {'observed_at':frozen['frozen_at']} or read(phase_path) != phase):
            return {}
        previous = start
        acquisition = plan.generation_id+':night'
        receipts, bodies, hashes = [], {}, {}
        for key, path in zip(prefix, paths, strict=True):
            row, final = read(path), finals[key]
            if (outcome['logical_results'][key] != final or final['status'] != 'PASS'
                    or len(final['attempts']) != 1 or final['attempts'][0]['status'] != 200
                    or final['attempts'][0]['raw_sha256'] != final['raw_sha256']
                    or row['sealed_logical_id'] != key or row['sealed_final_receipt_sha256'] != final['receipt_sha256']
                    or row['artifact'] != descriptors[key].raw_path or row['artifact_sha256'] != final['raw_sha256']
                    or row['requested_at'] != final['attempts'][0]['started_at']
                    or row['received_at'] != final['attempts'][0]['finished_at']):
                return {}
            begin,end = (datetime.fromisoformat(row[k]) for k in ('requested_at','received_at'))
            if not previous <= begin <= end:
                return {}
            previous = end
            consume_bound_result(root=root/'dispatch',plan=plan,logical_id=key,receipt_sha256=final['receipt_sha256'])
            artifact = row['artifact']
            receipts.append(dict(row,acquisition_id=acquisition))
            bodies[artifact] = (root/'dispatch'/artifact).read_bytes()
            hashes[artifact] = final['raw_sha256']
        proof = replay_night(receipts=receipts,bodies=bodies,body_hashes=hashes,observed_at=start,
            run_id=plan.generation_id,acquisition_id=acquisition,expected_value_sha256=digest(phase['value']),
            policy=POLICY,run_started_at=start,acquisition_cutoff=datetime.fromisoformat(outcome['completed_at']))
        telemetry = proof['value']['telemetry']
        if (telemetry['status'] != 'ok' or telemetry['night_session_usable'] is not True
                or telemetry['queried_dates'] != dates[:len(prefix)] or not proof['value']['observations']
                or not any(r['product']=='KOSPI200' for r in telemetry['products'])):
            return {}
        return dict.fromkeys(tail, dict(value_sha256=proof['value_sha256'],
            prefix_receipt_sha256=[finals[k]['receipt_sha256'] for k in prefix]))
    except (ValueError, KeyError, TypeError, OSError):
        # Incomplete or inconsistent evidence does not close mandatory slots.
        return {}


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
