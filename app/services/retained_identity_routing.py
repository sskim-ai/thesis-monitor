"""Read actual dispatched listing receipts before any current Parent issuance."""
import json
from app.services.sealed_fresh_dispatch import decode_request_plan, consume_bound_result, _binding_parent
from app.services.sealed_response_binding import resolve_response_binding, SlotNotSelected
from app.services.vnext_research_store import digest, plain


def retained_listing_rows(root):
    root = plain(root)
    plan = decode_request_plan(json.loads(plain(root/'plan.json').read_bytes()))
    rows = []
    descriptors = {d.logical_request_id:d for d in plan.descriptors}
    visiting = set()
    def unselected(descriptor):
        if descriptor.response_binding is None:
            return False
        key=descriptor.logical_request_id
        if key in visiting:
            raise ValueError('retained_routing_binding_cycle')
        visiting.add(key)
        try:
            parents={}
            for parent in descriptor.response_binding.parents:
                path=plain(root/'receipts'/parent/'final.json')
                if not path.exists():
                    if parent in descriptors and unselected(descriptors[parent]):
                        return True
                    raise ValueError('retained_routing_selected_receipt_missing')
                final=json.loads(path.read_bytes())
                parents[parent]=_binding_parent(root,plan,parent,final['receipt_sha256'])
            try:resolve_response_binding(descriptor.request_json,descriptor.response_binding,parents)
            except SlotNotSelected:return True
            return False
        finally:visiting.remove(key)
    for descriptor in plan.descriptors:
        if descriptor.endpoint_operation != 'ka10099':
            continue
        final_path = plain(root/'receipts'/descriptor.logical_request_id/'final.json')
        if not final_path.exists():
            if unselected(descriptor):continue
            raise ValueError('retained_routing_selected_receipt_missing')
        final = json.loads(final_path.read_bytes())
        if final['status'] != 'PASS':
            if final['status']=='NOT_SELECTED':
                _binding_parent(root,plan,descriptor.logical_request_id,final['receipt_sha256'])
                continue
            raise ValueError('retained_routing_selected_receipt_denied')
        consume_bound_result(root=root, plan=plan, logical_id=descriptor.logical_request_id,
            receipt_sha256=final['receipt_sha256'])
        raw = plain(root/descriptor.raw_path).read_bytes()
        if digest(raw) != final['raw_sha256']:
            raise ValueError('retained_routing_raw_drift')
        rows.extend(json.loads(raw).get('list', []))
    return rows
