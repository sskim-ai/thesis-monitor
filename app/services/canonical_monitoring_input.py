"""Canonical current-source input transformations, independent of controllers."""
from copy import deepcopy
from decimal import Decimal

from app.services.direction_timing_ownership_service import verified_owned_packet_view
from app.services.provider_native_technical import INDICATORS
from scripts import r2b_r2_contract as c
from app.services import canonical_monitoring_owner as owner
from app.services.entry_candidate_basis import restrict_entry_candidates
from scripts.m12co_entry_range_contract import build_subject_candidate_coverage
from scripts.m12cr_r1_typed_quality_contract import project_business_evidence_quality, project_security_valuation_basis
from scripts.m12dj_source_authority_preflight import preflight_current_pass_a_subject
from scripts.m12ds_r2_ranges import eligible_range_inputs, valuation_policy
from scripts.m12cq_two_pass_contract import build_pass_b_subject_context, validate_pass_b_transformation


NATIVE_TECHNICAL_PROMPT = '''Use native_technical_context for trend, momentum, volume and the choice of an
available tactical watch zone. The supplied provider fields and formula meanings
are authoritative inputs; do not replace them with Wilder RSI, BB20/2, a different
EMA seed or a locally recalculated indicator. Use the supplied timeframe and bar
date. Null or unavailable fields are missing evidence, never zero. A short history
does not by itself invalidate the other available indicators. Interpret their
agreement and disagreement in context, without inventing universal thresholds.
Technical evidence informs entry context only; it cannot create business direction,
fundamental cheapness, fair value or a new price range.'''


def native_technical_context(view, context):
    """Copy the Source's native values that survived the existing B projection.

    This is a model-input projection, not another indicator or admission engine.
    Unavailable periods/fields retain their names and reasons with null values.
    """
    packet = view.get('evidence_packet') or {}
    native = packet.get('technical_context_quality', {}).get('provider_native')
    if native is None:
        return None
    emitted = {row['ref_id']: row for row in context['decision_evidence']}
    eligible = {row['ref_id'] for row in context['source_use_projection']['source_permissions']
                if 'ENTRY' in row['allowed_uses']}
    original = [row for row in packet['evidence']
                if row['ref_id'].startswith('native:') and row['category'] == 'technical_feature']
    result = {key: deepcopy(native.get(key)) for key in
              ('provider', 'provider_code', 'market', 'adjusted', 'cutoff',
               'indicator_schema', 'formula_semantics', 'source_hash')}
    result['periods'] = {}
    monitoring = native.get('allowed_use') == 'MONITORING_TECHNICAL'
    for timeframe in ('daily', 'weekly', 'monthly'):
        period = native['periods'].get(timeframe, {})
        frame_quality = packet['technical_context_quality'].get(
            {'daily': 'D', 'weekly': 'W', 'monthly': 'M'}[timeframe], {})
        as_of = period.get('completed_as_of')
        available = (monitoring and period.get('status') == 'AVAILABLE'
                     and frame_quality.get('usable_for_current_reasoning') is True)
        values, quality, refs = {}, {}, {}
        reasons = list(period.get('reasons') or []) + list(frame_quality.get('reasons') or [])
        if not monitoring:
            reasons.append('NATIVE_SCOPE_NOT_MONITORING')
        for field in INDICATORS:
            source_value = period.get('indicators', {}).get(field)
            source_quality = period.get('indicator_quality', {}).get(field, 'UNAVAILABLE_PROVIDER_NULL_OR_MISSING')
            matches = [row for row in original
                       if row['source_ref'].endswith('.native.' + timeframe + '.' + field)]
            row = matches[0] if len(matches) == 1 else None
            ref = row['ref_id'] if row else None
            usable = (available and source_quality == 'PROVIDER_NATIVE' and source_value is not None
                      and ref in emitted and ref in eligible)
            if usable:
                visible = emitted[ref]
                if (row['as_of'] != as_of or visible['as_of'] != as_of
                        or Decimal(str(row['value'])) != Decimal(str(source_value))
                        or visible['value'] != row['value']):
                    raise ValueError('native_model_source_value_mismatch')
                values[field] = deepcopy(source_value)
                quality[field] = source_quality
                refs[field] = ref
            else:
                values[field] = None
                quality[field] = (source_quality if source_quality != 'PROVIDER_NATIVE'
                                  else 'UNAVAILABLE_FOR_MONITORING')
        if not refs and period.get('status') == 'AVAILABLE':
            reasons.append('NO_ELIGIBLE_NATIVE_INDICATOR_EVIDENCE')
        result['periods'][timeframe] = dict(
            as_of=as_of, status='AVAILABLE' if refs else
            'INVALID' if period.get('status') == 'INVALID' else 'UNAVAILABLE',
            calculation_row_count=period.get('returned_count', 0),
            completed_row_count=period.get('completed_count', 0),
            source_hash=period.get('source_hash'), indicators=values,
            indicator_quality=quality, evidence_refs=refs,
            reasons=list(dict.fromkeys(reasons)))
    return result

def subject_inputs(view, authority, receipt, *, generation, atomic=()):
    owned = verified_owned_packet_view(view)
    source_generation = authority["authority"]["source_generation_id"]
    cat, metadata, chain = c.bound_chain(view, authority, atomic=list(atomic), generation=generation,
                                       source_generation=source_generation, view_receipt=receipt)
    ownership = {"ticker": view["ticker"], "core_ref_ids": sorted(owned.core_refs),
                 "timing_ref_ids": sorted(owned.timing_refs)}
    sub = build_subject_candidate_coverage(market=view["market"], packet=view["evidence_packet"], ownership=ownership)
    sub.update(decision_evidence=metadata,
        business_evidence_quality_state=project_business_evidence_quality(view["evidence_packet"]),
        security_valuation_basis_state=project_security_valuation_basis(view["evidence_packet"]),
        directional_disclosure_quality_refs=sorted(set(cat["material_disclosure_failure_refs"] + cat["positive_quality_refs"])))
    return cat, sub, chain

def a_input(view, cat, sub, chain, authority):
    return preflight_current_pass_a_subject(ticker=view["ticker"], source_generation_id=chain["source_generation_id"],
        execution_generation_id=chain["execution_generation_id"], catalog=cat, source_packet=sub,
        authority=chain["authority"], projection=chain["projection"], binding=chain["binding"], expectation=chain["expectation"],
        prohibited_pass_a_source_refs=authority["pass_a_visibility_exclusions"])

def b_input(view, cat, sub, chain, classification, capability):
    range_subject, entries, exclusions = eligible_range_inputs(sub, cat["entry_catalog"], chain)
    valuation = valuation_policy(range_subject, classification, sub["security_valuation_basis_state"])
    valuation["source_use_exclusions"] = exclusions
    common = dict(catalog=cat, source_use_view=chain["projection"], source_use_binding=chain["binding"],
        source_use_expectation=chain["expectation"], source_generation_id=chain["source_generation_id"],
        execution_generation_id=chain["execution_generation_id"], require_source_use=True)
    ctx = build_pass_b_subject_context(context=owner.m12db._source_context(view["ticker"], sub),
        ticker=view["ticker"], pass_a=classification, policy_option=valuation["option"], **common)
    common.pop("require_source_use")
    transform = validate_pass_b_transformation(context=ctx, raw_source_metadata=sub["decision_evidence"], **common)
    c._require(transform["status"] == "PASS", "pass_b_transformation_failed")
    ctx.update(r2_policy_capability=capability, r2_valuation=valuation, r2_eligible_range_catalog=entries)
    ctx, entries = restrict_entry_candidates(ctx, entries, ticker=view['ticker'],
        security_id=(view.get('valuation_view') or {}).get('security_id'),
        source_generation_id=chain['source_generation_id'])
    native = native_technical_context(view, ctx)
    if native is not None:
        ctx['native_technical_context'] = native
    return ctx, entries, valuation
