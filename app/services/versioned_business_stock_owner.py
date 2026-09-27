"""Rebind sealed business versions to fresh security-level source components.

The version is an immutable source record, never an old packet or PASS label.
Comparisons are reconstructed by the existing financial owners. Original
periods and permissions are preserved; only current eligibility is rechecked.
"""
from copy import deepcopy
from datetime import datetime
import json

from app.services.bounded_financial_stock_owner import build_shadow_numeric_registry
from app.services.cross_market_decision_engine_service import build_decision_evidence_packet
from app.services.direction_timing_ownership_service import build_owned_evidence_packet, stage_alias_catalogs
from app.services.issuer_business_bridge import bind_comparison
from app.services.packet_owned_technical_context_service import PacketOwnedTechnicalContext
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_owner import assemble_stock, reject_downstream
from scripts.m12dr_financial_source_authority import comparative_facts, source_quality

CONTRACT = 'versioned-business-current-stock-binding-v1'
VERSION_KEYS = {'contract', 'ticker', 'frozen_at', 'original_cutoff', 'source_artifact_sha256',
    'parent_zip_sha256', 'quality_bundles', 'facts', 'financial_source_graph',
    'issuer_business_bridge', 'scope', 'old_class_a_values_consumed', 'prior_event_reused_as_class_b'}


def _time(value):
    at = datetime.fromisoformat(value)
    if at.utcoffset() is None:
        raise ValueError('business_source_time_naive')
    return at


def version_document(raw, expected_sha256, *, ticker, cutoff):
    if sha256_bytes(raw) != expected_sha256:
        raise ValueError('business_version_hash_mismatch')
    doc = json.loads(raw)
    reject_downstream(doc)
    if (set(doc) != VERSION_KEYS or doc['ticker'] != ticker
            or doc['contract'] != 'frozen-accepted-reported-comparison-input-v1'
            or doc['old_class_a_values_consumed'] is not False
            or doc['prior_event_reused_as_class_b'] is not False):
        raise ValueError('business_version_shape_or_subject_mismatch')
    if not _time(doc['original_cutoff']) <= _time(doc['frozen_at']) <= cutoff:
        raise ValueError('business_version_after_cutoff')
    return doc


def _identity(local_seeds, ticker):
    records = [r['record'] for seed in local_seeds for v in seed['roles'].values()
               for r in v['records'] if r['table'] == 'securitymaster' and r['record'].get('ticker') == ticker]
    unique = {digest(r): r for r in records}
    if len(unique) != 1:
        raise ValueError('business_current_security_identity_missing_or_ambiguous')
    return next(iter(unique.values()))


def replay_version(*, ticker, versions, version_hashes, local_seeds, cutoff, policy):
    path = 'class-c/business-versioned-' + ticker + '.json'
    doc = version_document(versions[ticker], version_hashes[path], ticker=ticker, cutoff=cutoff)
    security = _identity(local_seeds, ticker)
    bridge = doc['issuer_business_bridge']
    eligibility, candidates = [], []
    if bridge is not None:
        if (bridge.get('receipt_sha256') != digest({k: v for k, v in bridge.items() if k != 'receipt_sha256'})
                or bridge.get('scope') != 'issuer_business_only'
                or bridge.get('security_ticker') != ticker
                or bridge.get('monitored_security_id') != security['canonical_security_id']
                or bridge.get('target_company_id') != security['canonical_company_id']
                or bridge.get('provider_issuer_ids', {}).get('sec') != security.get('cik')
                or bridge.get('SECURITY_PER_SHARE_BRIDGE_ELIGIBLE') is not False
                or bridge.get('SECURITY_VALUATION_BRIDGE_ELIGIBLE') is not False
                or bridge.get('security_valuation_transfer') is not False
                or bridge.get('ISSUER_BUSINESS_EVIDENCE_ELIGIBLE') is not True
                or _time(bridge['cutoff']) > cutoff):
            raise ValueError('issuer_bridge_current_identity_or_scope_mismatch')
        underlying = bridge['underlying_ticker']
        if underlying == ticker:
            raise ValueError('recursive_issuer_bridge_denied')
        source_doc = version_document(versions[underlying],
            version_hashes['class-c/business-versioned-' + underlying + '.json'],
            ticker=underlying, cutoff=cutoff)
        if source_doc['issuer_business_bridge'] is not None:
            raise ValueError('recursive_issuer_bridge_denied')
        source = _identity(local_seeds, underlying)
        if (source.get('canonical_security_id') != bridge['source_security_id']
                or source.get('canonical_company_id') != bridge['source_company_id']
                or 'DART:' + str(source.get('corp_code')) != bridge['issuer_id']
                or doc['quality_bundles']):
            raise ValueError('issuer_bridge_underlying_identity_mismatch')
        base = replay_version(ticker=underlying, versions=versions, version_hashes=version_hashes,
                              local_seeds=local_seeds, cutoff=cutoff, policy=policy)
        for original in base['facts']:
            matches = [f for f in doc['facts'] if f.get('issuer_business_bridge', {}).get('original_fact_id') == original['fact_id']]
            if len(matches) != 1:
                continue
            accepted = matches[0]
            projected = deepcopy(original)
            projected['fact_id'] = original['fact_id'].replace(':' + underlying + ':', ':' + ticker + ':', 1)
            projected['issuer_projection'] = deepcopy(bridge)
            candidates.append(bind_comparison(projected, original, bridge,
                source_result_sha256=accepted['issuer_business_bridge']['source_result_sha256']))
        eligibility.append({'scope': 'issuer_business_only', 'bridge_sha256': digest(bridge),
            'underlying_version_sha256': base['version_sha256'], 'underlying_replay_sha256': digest(base),
            'original_identity_receipt': 'FROZEN_ACCEPTED_SOURCE_OWNED_BRIDGE',
            'current_security_identity_rechecked': True, 'price_technical_transfers': 0,
            'security_per_share_eligible': False, 'security_valuation_eligible': False})
    else:
        for bundle in doc['quality_bundles']:
            inputs = bundle['source_inputs']
            if inputs['ticker'] != ticker:
                raise ValueError('business_quality_subject_mismatch')
            provider = inputs['formal']['provider']
            if provider not in {'sec_companyfacts', 'sec_foreign_filing', 'opendart'}:
                raise ValueError('business_source_provider_denied')
            policy.require(provider)
            issuer = ('DART:' + str(security.get('corp_code')) if provider == 'opendart'
                      else 'CIK:' + str(security.get('cik')).zfill(10))
            if issuer.endswith('None'):
                raise ValueError('business_issuer_identity_missing')
            quality = source_quality(bundle)
            if quality != bundle['quality']:
                raise ValueError('business_original_quality_replay_mismatch')
            original = comparative_facts(quality, ticker=ticker, issuer_id=issuer)
            for row in original:
                if row['fields']['period_end'] > cutoff.date().isoformat():
                    raise ValueError('business_period_after_cutoff')
            updated = deepcopy(bundle)
            updated['source_inputs']['cutoff'] = cutoff.date().isoformat()
            updated['source_inputs_sha256'] = digest(updated['source_inputs'])
            current = source_quality(updated)
            if current['status'] != quality['status'] or current['comparative_observations'] != quality['comparative_observations']:
                raise ValueError('business_current_eligibility_changed')
            candidates.extend(original)
            eligibility.append({'provider': provider, 'issuer_id': issuer,
                'original_source_inputs_sha256': bundle['source_inputs_sha256'],
                'original_quality_sha256': digest(quality), 'current_quality_sha256': digest(current),
                'current_cutoff': cutoff.isoformat(), 'source_generation_id': bundle['source_generation_id']})
    original_by_hash = {digest(f): f for f in candidates}
    if any(digest(f) not in original_by_hash for f in doc['facts']):
        raise ValueError('business_fact_not_reproduced_from_original_source')
    if len({f['fact_id'] for f in doc['facts']}) != len(doc['facts']):
        raise ValueError('business_fact_identity_duplicate')
    return {'contract': CONTRACT, 'ticker': ticker, 'version_sha256': version_hashes[path],
        'facts': deepcopy(doc['facts']), 'eligibility': eligibility, 'bridge': deepcopy(bridge),
        'source_graph': deepcopy(doc['financial_source_graph']),
        'source_cutoff': doc['original_cutoff'], 'current_cutoff': cutoff.isoformat(),
        'original_source_artifact_sha256': doc['source_artifact_sha256'],
        'old_class_a_values_consumed': False, 'current_class_b_claimed': False}


def bind_current_stock(*, stock_inputs, versions, version_hashes, local_seeds):
    ticker, plan = stock_inputs['ticker'], stock_inputs['plan']
    business = replay_version(ticker=ticker, versions=versions, version_hashes=version_hashes,
        local_seeds=local_seeds, cutoff=plan.frozen_at, policy=stock_inputs['policy'])
    baseline = assemble_stock(**stock_inputs, financial_tuple_denial=bool(business['facts']))
    # Existing complete owners remain byte-for-byte unchanged.
    if baseline['status'] == 'PASS':
        return {'contract': CONTRACT, 'binding_kind': 'BASE_OWNER_ALREADY_COMPLETE',
                'result': baseline, 'business_version': business, 'baseline_invariant': True}
    if not business['facts']:
        return {'contract': CONTRACT, 'binding_kind': 'NO_ELIGIBLE_VERSIONED_BUSINESS',
                'result': baseline, 'business_version': business, 'baseline_invariant': True}
    result = deepcopy(baseline)
    stock = result['packet']['stocks'][0]
    # Invalid direct-financial envelopes are not retained beside qualified comparisons.
    rejected = {r['fact_id'] for r in result['observed_business_union'] if r['status'] != 'PASS'}
    stock['fact_catalog'] = [f for f in stock['fact_catalog'] if f['fact_id'] not in rejected]
    if rejected:
        stock['valuation'] = {}
    stock['fact_catalog'].extend(business['facts'])
    stock['numeric_registry'] = build_shadow_numeric_registry(stock['fact_catalog'])
    technical = PacketOwnedTechnicalContext.model_validate(stock['technical_context'])
    evidence = build_decision_evidence_packet(packet=result['packet'], stock=stock, technical_context=technical)
    owned = build_owned_evidence_packet(evidence, stock=stock)
    stage_alias_catalogs(owned)
    refs = {'canonical:' + f['fact_id'] for f in business['facts']}
    if refs - {r.ref_id for r in evidence.evidence}:
        raise ValueError('business_typed_reference_lost')
    missing = [m for m in baseline['mandatory_missing'] if m != 'observed_business_union:eligible_reported_financial_or_event']
    bad_numeric = [r for r in stock['numeric_registry'] if not r['registered']]
    if bad_numeric:
        missing.append('numeric_registry:unregistered_fields')
    for fid in rejected:
        result['source_graph'].pop(fid)
    for fact in business['facts']:
        result['source_graph'][fact['fact_id']] = {'ticker': ticker, 'fact_sha256': digest(fact),
            'source': 'versioned_reported_business', 'input_sha256': business['version_sha256'],
            'original_source_artifact_sha256': business['original_source_artifact_sha256'],
            'original_occurrence_graph': business['source_graph'][fact['fact_id']],
            'current_eligibility_sha256': digest(business['eligibility']),
            'source_scope': 'issuer_business_only_no_current_price_or_security_valuation'}
    result.update(status='PASS' if not missing else 'BLOCKED', mandatory_missing=missing,
        diagnostic_packet_sha256=digest(result['packet']), packet_sha256=digest(result['packet']) if not missing else None,
        evidence_packet=evidence.model_dump(mode='json'), ownership=owned.model_dump(mode='json'),
        observed_business_union=[r for r in result['observed_business_union'] if r['status'] == 'PASS'] + [
            {'status': 'PASS', 'source_kind': 'VERSIONED_COMPARATIVE_FINANCIAL', 'ref_id': ref,
             'version_sha256': business['version_sha256']} for ref in sorted(refs)],
        observed_business_cardinality=baseline['observed_business_cardinality'] + len(refs),
        numeric_registry_unregistered=bad_numeric)
    result['input_hashes']['versioned_business'] = business['version_sha256']
    result['numeric_registry_graph'] = [{'fact_id': r['fact_id'], 'field_path': r['field_path'],
        'registry_entry_sha256': digest(r), 'source_node_sha256': digest(result['source_graph'][r['fact_id']])}
        for r in stock['numeric_registry']]
    result['evidence_reference_graph'] = {r.ref_id: {'ticker': ticker, 'source_ref': r.source_ref,
        'evidence_sha256': digest(r.model_dump(mode='json')), 'input_hashes': deepcopy(result['input_hashes']),
        'technical_context_id': technical.technical_context_id} for r in evidence.evidence}
    return {'contract': CONTRACT, 'binding_kind': 'ISSUER_BRIDGE' if business['bridge'] else 'COMPARATIVE_VERSION',
            'result': result, 'business_version': business, 'baseline_invariant': False,
            'fresh_price_technical_unchanged': all(stock[k] == baseline['packet']['stocks'][0][k]
                for k in ('price_and_positioning', 'technical_context', 'chart_context', 'current_price_context'))}
