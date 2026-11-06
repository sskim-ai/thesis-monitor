"""Read actual dispatched listing receipts before any current Parent issuance."""
import json
from app.services.sealed_fresh_dispatch import decode_request_plan, consume_bound_result
from app.services.vnext_research_store import digest, plain


def retained_listing_rows(root):
    root = plain(root)
    plan = decode_request_plan(json.loads(plain(root/'plan.json').read_bytes()))
    rows = []
    for descriptor in plan.descriptors:
        if descriptor.endpoint_operation != 'ka10099':
            continue
        final_path = plain(root/'receipts'/descriptor.logical_request_id/'final.json')
        if not final_path.exists():
            continue
        final = json.loads(final_path.read_bytes())
        if final['status'] != 'PASS':
            continue
        consume_bound_result(root=root, plan=plan, logical_id=descriptor.logical_request_id,
            receipt_sha256=final['receipt_sha256'])
        raw = plain(root/descriptor.raw_path).read_bytes()
        if digest(raw) != final['raw_sha256']:
            raise ValueError('retained_routing_raw_drift')
        rows.extend(json.loads(raw).get('list', []))
    return rows
