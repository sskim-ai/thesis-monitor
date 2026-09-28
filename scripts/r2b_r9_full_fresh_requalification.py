"""Source-only offline controller. No implicit acquisition or model route.

The generation plan is a candidate until every declared mandatory role has an
implemented fresh replay owner. A missing owner cannot be approved by a flag.
"""

import argparse
from datetime import datetime
import json
from pathlib import Path

from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.fresh_source_run_contract import acquisition_plan, validate_local_seed
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_stock_acquisition import StockPlan, UNIVERSE

CONTRACT = 'r9-rev8-fresh-controller-v1'
ALL22 = frozenset(t for ts in UNIVERSE.values() for t in ts)


def _read(root, binding):
    relative = Path(binding['path'])
    if relative.is_absolute() or '..' in relative.parts or not relative.parts:
        raise ValueError('fresh_controller_relative_artifact_required')
    if any(root.joinpath(*relative.parts[:i]).is_symlink() for i in range(1, len(relative.parts)+1)):
        raise ValueError('fresh_controller_symlink_artifact_denied')
    raw = (root / relative).read_bytes()
    if sha256_bytes(raw) != binding['sha256']:
        raise ValueError('fresh_controller_artifact_hash_mismatch')
    return raw


def load_stock_inputs(root, descriptor, stock_plan, *, _bridge_source=False):
    """Explicit data-only inputs; no dynamic imports, callbacks or old result."""
    required = {'ticker', 'local', 'receipts', 'components', 'artifacts', 'financial_plan',
                'financial_acquisition', 'financial_receipts', 'financial_raw', 'allowed_providers'}
    if (set(descriptor) - {'issuer_bridge'} != required or descriptor['ticker'] not in ALL22
            or (_bridge_source and descriptor.get('issuer_bridge') is not None)):
        raise ValueError('fresh_stock_descriptor_shape_or_subject')
    def read(name):
        return json.loads(_read(root, descriptor[name]))
    local = read('local')
    validate_local_seed(local)
    receipts, components = read('receipts'), read('components')
    raw_directory = root / descriptor['financial_raw']
    relative = Path(descriptor['financial_raw'])
    if relative.is_absolute() or '..' in relative.parts or raw_directory.resolve() != raw_directory:
        raise ValueError('fresh_financial_raw_directory_invalid')
    technical = dict(plan=stock_plan, ticker=descriptor['ticker'], local_seed=local, financial=None,
        receipts=receipts, components=components,
        artifacts={name: _read(root, binding) for name, binding in descriptor['artifacts'].items()},
        policy=UnifiedSourcePolicy(frozenset(descriptor['allowed_providers'])))
    technical['expected_hashes'] = dict(plan=digest(stock_plan.model_dump(mode='json')),
        local=digest(local), financial=digest(None), receipts=digest(receipts), components=digest(components))
    financial_receipts = read('financial_receipts')
    for receipt in financial_receipts:
        if receipt.get('artifact'):
            _read(raw_directory, {'path': receipt['artifact'], 'sha256': receipt['raw_sha256']})
        logical = receipt['logical_id'].removeprefix(descriptor['ticker'] + ':')
        try:
            ordinal = int(logical.removeprefix('request-'))
        except ValueError as exc:
            raise ValueError('fresh_financial_request_identity_invalid') from exc
        if logical != f'request-{ordinal:03d}' or ordinal < 1:
            raise ValueError('fresh_financial_request_identity_invalid')
    result = dict(technical_inputs=technical, financial_inputs=dict(plan=read('financial_plan'),
        acquisition=read('financial_acquisition'), receipts=financial_receipts, directory=raw_directory,
        field_semantics=True))
    if descriptor.get('issuer_bridge') is not None:
        from app.services.unified_stock_owner import assemble_stock
        from app.services.bounded_financial_stock_owner import assemble
        bridge = descriptor['issuer_bridge']
        if set(bridge) != {'source_descriptor', 'official_identity', 'source_result_sha256'}:
            raise ValueError('fresh_bridge_descriptor_shape')
        source = load_stock_inputs(root, bridge['source_descriptor'], stock_plan, _bridge_source=True)
        if source['financial_inputs']['plan']['ticker'] == descriptor['ticker']:
            raise ValueError('fresh_bridge_cross_security_required')
        inputs = dict(baseline=assemble_stock(**{**source['technical_inputs'], 'fresh_financial_pending': True}),
            local_seed=source['technical_inputs']['local_seed'], **source['financial_inputs'])
        if digest(assemble(**inputs)) != bridge['source_result_sha256']:
            raise ValueError('fresh_bridge_source_result_hash_mismatch')
        official = json.loads(_read(root, bridge['official_identity']))
        result['financial_inputs']['issuer_business'] = dict(source_inputs=inputs,
            official_identity=official, official_identity_sha256=digest(official),
            source_result_sha256=bridge['source_result_sha256'])
    return result


def assemble_current_stocks(root, manifest):
    """Rebuild all22 in deterministic order, preserving each source failure."""
    if set(manifest['stocks']) != ALL22:
        raise ValueError('fresh_controller_exact_all22_required')
    plan = StockPlan.model_validate(manifest['stock_plan'])
    if plan.run_id != manifest['run_id']:
        raise ValueError('fresh_controller_generation_mismatch')
    output, errors = {}, {}
    for ticker in sorted(ALL22):
        descriptor = manifest['stocks'][ticker]
        if descriptor['ticker'] != ticker:
            raise ValueError('fresh_controller_subject_mapping_mismatch')
        try:
            inputs = load_stock_inputs(root, descriptor, plan)
            output[ticker] = assemble_fresh_stock(**inputs)
        except (ValueError, KeyError, TypeError) as exc:
            errors[ticker] = dict(error_class=type(exc).__name__, reason=str(exc))
    return dict(contract=CONTRACT, run_id=plan.run_id, stocks=output, errors=errors,
        accepted=sum(s['status'] == 'PASS' for s in output.values()), expected=22,
        stock_semantic_hashes={t: digest(s) for t, s in output.items()},
        complete_source_adapter_qualified=False, production_dispatch_enabled=False)


def replay_current_stocks(root, manifest):
    first = assemble_current_stocks(root, manifest)
    second = assemble_current_stocks(root, manifest)
    if first != second:
        raise ValueError('fresh_stock_replay_not_deterministic')
    return dict(first=first, second_sha256=digest(second), replay_equal=True,
                whole_source_replay_qualified=False)


def prepare_fresh_subject(inputs, *, execution_generation_id):
    """Use the existing Core/A/B preflight on a freshly replayed source owner."""
    from scripts.m12cn_policy_contract import build_subject_catalog
    from scripts.m12dk_current_source_authority import freeze_current_source_binding
    from scripts.m12dr_financial_source_authority import build_source_authority
    from scripts.r2b_r2_preflight import preflight_subject
    from app.services.direction_timing_ownership_service import OwnedEvidencePacket
    stock = assemble_fresh_stock(**inputs)
    if stock['status'] != 'PASS':
        raise ValueError('fresh_model_source_incomplete:' + ','.join(stock['mandatory_missing']))
    owned = OwnedEvidencePacket.model_validate(stock['ownership'])
    context = dict(evidence_packets=[stock['evidence_packet']], evidence_ownership=[dict(
        ticker=stock['ticker'], core_ref_ids=sorted(owned.core_refs), timing_ref_ids=sorted(owned.timing_refs))])
    catalog = build_subject_catalog(context=context, ticker=stock['ticker'], atomic_claims=[])
    metadata = [r for r in stock['evidence_packet']['evidence'] if r['ref_id'] in catalog['all_evidence_refs']]
    args = dict(ticker=stock['ticker'], source_generation_id=stock['fresh_run_id'],
        source_packet=stock['packet'], evidence_packet=stock['evidence_packet'], catalog=catalog,
        source_metadata=metadata, frozen_binding=freeze_current_source_binding(
            source_generation_id=stock['fresh_run_id'], source_packet=stock['packet'], evidence_packet=stock['evidence_packet']),
        quality_bundles={}, issuer_bindings={}, fresh_business_inputs=inputs)
    authority = build_source_authority(**args)
    readiness, prepared = preflight_subject(stock, authority, inputs['technical_inputs']['local_seed'],
        generation=execution_generation_id, cutoff=stock['packet']['generated_at'])
    return dict(stock=stock, authority=authority, readiness=readiness, prepared=prepared)


def candidate_plan(stock_plan, identities, *, kr_max_pages):
    plan = acquisition_plan(stock_plan, identities, kr_max_pages=kr_max_pages)
    # These gaps are explicitly about unimplemented end-to-end routes. An
    # existing source collector or a synthetic row test alone cannot close one.
    gaps = [
        'FRESH_WHOLE_SOURCE_ALL22_MARKET_CONTEXT_REPLAY_NOT_QUALIFIED',
        'ISSUER_BRIDGE_DESCRIPTOR_ALL22_ARCHETYPE_PROOF_NOT_CLOSED',
        'FRESH_QUALITY_REQUIRES_COMPARISON_NO_UNKNOWN_LIMIT_SOURCE_PATH',
        'QUALIFIED_VALUATION_SECTION_OWNER_PATH_NOT_CLOSED',
        'COMPLETE_DETAILED_SECTION_OWNERS_AND_END_TO_END_24_CAPTURE_NOT_CLOSED',
    ]
    return dict(contract=CONTRACT, source_candidate=plan, phase_a='R2B_R9_REV8_PREFLIGHT_CONTRACT_GAP',
        blockers=gaps, dispatch_allowed=False, final_provider_plan_qualified=False,
        candidate_maximum_transport_attempts=sum(b['maximum_HTTP_attempts'] for b in plan['budgets'].values()),
        external_calls=0, model_calls=0, production_side_effects=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['candidate', 'replay-stocks'])
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    from scripts.sealed_cohort_offline_proof import network_guard
    counters = network_guard()
    raw = args.input.read_bytes()
    if sha256_bytes(raw) != args.sha256:
        raise ValueError('fresh_controller_input_not_frozen')
    data = json.loads(raw)
    if args.mode == 'candidate':
        result = candidate_plan(data['stock_plan'], data['identities'], kr_max_pages=data['kr_max_pages'])
    else:
        result = replay_current_stocks(args.input.parent.resolve(), data)
    result['offline_network_audit'] = counters
    result['generated_at'] = datetime.now().astimezone().isoformat()
    durable_json(args.output, result, exclusive=True)
    print(json.dumps({'contract': CONTRACT, 'provider_calls': 0, 'model_calls': 0,
                      'dispatch_allowed': False}))


if __name__ == '__main__':
    main()
