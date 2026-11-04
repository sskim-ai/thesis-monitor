"""Original wire-plan partitions and independent byte replay, never Market grants.

Descriptors and their continuation/exchange-discovery dependency closure stay
intact. The result is Source-only evidence, not the canonical Market authority
graph (which also needs publications, macro, Class-C and optional-night policy).
"""
from datetime import datetime, timezone
from pathlib import PurePosixPath

from app.services.sealed_fresh_dispatch import RequestPlan
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest

CONTRACT = 'market-component-chunk-v1'


def partition_market_plan(plan, *, maximum_http=20):
    plan = RequestPlan.model_validate(plan)
    if type(maximum_http) is not int or not 2 <= maximum_http <= 20:
        raise ValueError('market_chunk_physical_cap')
    descriptors = {d.logical_request_id:d for d in plan.descriptors}
    if len(descriptors) != len(plan.descriptors) or 'kiwoom:auth' not in descriptors:
        raise ValueError('market_chunk_exact_original_plan')
    if any(d.provider != 'kiwoom' or d.transient_retry_max != 0 for d in descriptors.values()):
        raise ValueError('market_chunk_original_provider_retry_zero_required')
    groups = {}
    for d in plan.descriptors:
        if d.logical_request_id == 'kiwoom:auth':
            continue
        if not d.logical_request_id.startswith(('kr_market:', 'us_market:')):
            raise ValueError('market_chunk_market_only_required')
        groups.setdefault(d.group_id, set()).add(d.logical_request_id)

    def closure(ids):
        result, visiting = set(), set()
        def visit(key):
            if key in visiting or key not in descriptors:
                raise ValueError('market_chunk_dependency_missing_or_cycle')
            if key in result:
                return
            visiting.add(key)
            d = descriptors[key]
            if d.response_binding:
                for parent in d.response_binding.parents:visit(parent)
            visiting.remove(key);result.add(key)
        for key in ids:visit(key)
        result.add('kiwoom:auth')
        return result

    def attempts(ids):
        return sum(descriptors[i].max_transport_attempts for i in ids)

    selections, current = [], set()
    for group in groups.values():
        required = closure(group)
        if attempts(required) > maximum_http:
            raise ValueError('market_chunk_indivisible_component_exceeds_cap')
        proposed = closure(current | required)
        if current and attempts(proposed) > maximum_http:
            selections.append(closure(current));current = required
        else:
            current = proposed
    if current:selections.append(closure(current))
    chunks = []
    for number, ids in enumerate(selections, 1):
        data = plan.model_dump(mode='json')
        data['descriptors'] = [d.model_dump(mode='json') for d in plan.descriptors if d.logical_request_id in ids]
        roles = {d.consumer_role for d in plan.descriptors if d.logical_request_id in ids}
        data['mandatory_roles'] = [r for r in plan.mandatory_roles if r in roles]
        # Unresolved roles are never silently removed to make a live plan eligible.
        child = RequestPlan.model_validate(data)
        chunks.append(dict(contract=CONTRACT,chunk_id=f'market-chunk-{number:03d}',
            original_plan_sha256=plan.plan_sha256,plan=child.model_dump(mode='json'),
            plan_sha256=child.plan_sha256,maximum_physical_http=attempts(ids),
            retry=0,source_only=True,MarketParent=False))
    if not chunks or set().union(*selections) != set(descriptors):
        raise ValueError('market_chunk_incomplete_coverage')
    return chunks


def cold_reassemble(plan, chunks, records, artifact_reader, *, maximum_http=20):
    """Separate process replay of exact chunk/receipt bytes, NOT live attestation.

    CAPTURED entries bind original request hashes, page ordinals and response
    bytes. Continuation slots can be absent only with explicit original-dispatcher
    not-selected receipts. Such metadata is not reissued as authenticated HTTP.
    """
    plan = RequestPlan.model_validate(plan)
    expected = partition_market_plan(plan,maximum_http=maximum_http)
    if chunks != expected or len(records) != len(chunks):
        raise ValueError('market_chunk_exact_partition_required')
    by_chunk = {r['chunk_id']:r for r in records}
    if len(by_chunk) != len(records) or set(by_chunk) != {c['chunk_id'] for c in chunks}:
        raise ValueError('market_chunk_missing_or_duplicate')
    combined, used_paths, ordinals = {}, set(), set()
    for chunk in chunks:
        record = by_chunk[chunk['chunk_id']]
        child = RequestPlan.model_validate(chunk['plan'])
        source = [d for d in child.descriptors if d.logical_request_id != 'kiwoom:auth']
        rows = record['entries']
        if (record.get('contract') != CONTRACT or record.get('plan_sha256') != child.plan_sha256
                or type(record.get('actual_http')) is not int
                or not 1 <= record['actual_http'] <= chunk['maximum_physical_http']
                or len(rows) != len(source)):
            raise ValueError('market_chunk_receipt_scope_or_budget')
        entries = {r['descriptor_id']:r for r in rows}
        if len(entries) != len(rows) or set(entries) != {d.logical_request_id for d in source}:
            raise ValueError('market_chunk_descriptor_coverage')
        captured = 0
        for d in source:
            r = entries[d.logical_request_id]
            if (r.get('descriptor_sha256') != digest(d.model_dump(mode='json'))
                    or r.get('generation_id') != plan.generation_id
                    or r.get('provider') != d.provider or r.get('session') != d.target_period
                    or r.get('page_ordinal') != d.page_ordinal
                    or r.get('request_sha256') != sha256_bytes(d.request_json.encode())):
                raise ValueError('market_chunk_exact_original_descriptor_required')
            if r.get('status') == 'NOT_SELECTED':
                if (not d.response_binding or d.response_binding.kind != 'KIWOOM_CONTINUATION'
                        or r.get('reason') != 'ORIGINAL_DISPATCHER_NOT_SELECTED'):
                    raise ValueError('market_chunk_invalid_omission')
                previous = entries[d.response_binding.parents[0]]
                if previous.get('status') != 'NOT_SELECTED' and previous.get('response_headers',{}).get('cont-yn') != 'N':
                    raise ValueError('market_chunk_continuation_omitted')
                normalized = dict(status='NOT_SELECTED',reason=r['reason'])
            else:
                requested = datetime.fromisoformat(r['requested_at'])
                received = datetime.fromisoformat(r['received_at'])
                if (r.get('status') != 'CAPTURED' or r.get('http_status') != 200
                        or requested.utcoffset() is None or received.utcoffset() is None
                        or not plan.frozen_at <= requested <= received <= datetime.now(timezone.utc)):
                    raise ValueError('market_chunk_capture_clock_or_response')
                ordinal = r['physical_ordinal']
                if type(ordinal) is not int or ordinal <= 0 or ordinal in ordinals:
                    raise ValueError('market_chunk_physical_ordinal')
                ordinals.add(ordinal)
                path = PurePosixPath(r['artifact'])
                if path.is_absolute() or '..' in path.parts or str(path) in used_paths:
                    raise ValueError('market_chunk_artifact_namespace')
                used_paths.add(str(path))
                raw = artifact_reader(str(path),r['raw_sha256'])
                if len(raw) != r['raw_bytes'] or sha256_bytes(raw) != r['raw_sha256']:
                    raise ValueError('market_chunk_raw_hash')
                if d.max_pages > 1:
                    headers = r.get('response_headers',{})
                    if headers.get('cont-yn') not in ('Y','N') or (headers['cont-yn']=='Y' and not headers.get('next-key')):
                        raise ValueError('market_chunk_continuation_metadata_missing')
                    if d.page_ordinal == d.max_pages and headers['cont-yn'] != 'N':
                        raise ValueError('market_chunk_continuation_incomplete')
                    if d.page_ordinal > 1:
                        previous = entries[d.response_binding.parents[0]]
                        if previous.get('status') != 'CAPTURED' or previous.get('response_headers',{}).get('cont-yn') != 'Y':
                            raise ValueError('market_chunk_unexpected_continuation')
                captured += 1
                normalized = dict(status='CAPTURED',raw_sha256=r['raw_sha256'],raw_bytes=len(raw))
            if d.logical_request_id in combined and combined[d.logical_request_id] != normalized:
                raise ValueError('market_chunk_shared_dependency_conflict')
            combined[d.logical_request_id] = normalized
        if record['actual_http'] != captured+1:
            raise ValueError('market_chunk_auth_and_physical_count')
    required = {d.logical_request_id for d in plan.descriptors if d.logical_request_id != 'kiwoom:auth'}
    if set(combined) != required:
        raise ValueError('market_chunk_reassembly_incomplete')
    return dict(contract=CONTRACT,original_plan_sha256=plan.plan_sha256,
        components=combined,component_hash=digest(combined),
        status='SOURCE_BYTES_REASSEMBLED_NOT_PARENT',capture_authentication='NOT_REISSUED',
        MarketParent='NOT_ISSUED',native=False,valuation=False,model_use=False,
        original_parent_gap='SOURCE_CHUNK_PARENT_BINDING_NOT_PROVEN: canonical authority graph, Class-C, publications and macro/overnight inputs required')
