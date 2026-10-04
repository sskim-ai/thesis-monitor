"""Offline B2 v2 ownership composition. No model, persistence or production caller."""
from copy import deepcopy

from scripts import newbuyer_b2_contract as v1
from scripts.kis_eps_wire_calibration import digest, sealed, verified
from scripts.newbuyer_fper_prerequisite_scope import CATEGORIES, blocker_census
from scripts.kis_no_estimate_owner import aware

POLICY = 'newbuyer-b2-v2-axis-role-policy-v1'
METRIC = 'NewBuyerValuationMetricResolutionV2'
EVALUABILITY = 'NewBuyerValuationEvaluabilityV2'
CONFIDENCE = 'newbuyer-current-confidence-admissibility-v1'
ROLES = ('METRIC_ELIGIBILITY_ONLY', 'BUSINESS_GATE_QUALITY',
         'NEWBUYER_CONFIDENCE_VETO', 'GLOBAL_VALUATION_VETO', 'CONTEXT_ONLY')


def coverage_gate(coverage, census, coverage_sha, census_sha):
    verified(coverage, 'REV56COfflineCoverageReproofV1')
    verified(census, 'OfflineCurrentOwnerBlockerCensusV1')
    if coverage['receipt_sha256'] != coverage_sha or census['receipt_sha256'] != census_sha:
        raise ValueError('v2_coverage_census_sha_mismatch')
    rows = coverage['rows']
    if (not rows or coverage['subjects'] != len(rows) or coverage['complete_subjects'] != len(rows)
            or coverage['unresolved_required_cells'] != 0
            or not all(coverage[k] for k in ('coverage_complete','owner_provenance_complete',
                'temporal_provenance_complete','decision_provenance_complete'))
            or census != blocker_census(rows, expected_subjects=[r['ticker'] for r in rows])):
        raise ValueError('v2_incomplete_coverage_or_census')
    return {r['ticker']: r for r in rows}


def subject_binding(subject, row):
    if (row['ticker'] != subject['ticker'] or row['canonical_security_id'] != subject['security_id']
            or row['source_generation'] != subject['source_generation_id']):
        raise ValueError('v2_exact_subject_binding')


def metric_resolution(subject, row, census):
    """Resolve all category cells, never subtract blockers from loose fact counts."""
    subject_binding(subject, row)
    relevant = row['relevant_valuation_metric_refs']
    if not relevant or len(relevant) != len(set(relevant)):
        raise ValueError('v2_relevant_metric_universe_missing')
    qualified = set(row['qualified_relevant_valuation_refs'])
    facts = v1.usable_facts(subject)
    if set(facts) != qualified or not qualified <= set(relevant):
        raise ValueError('v2_qualified_fact_coverage_binding')
    blocks = [b for b in census['rows'] if b['ticker'] == subject['ticker']]
    results = []
    for ref in relevant:
        cells = [c for c in row['categories'] if c['metric_ref'] == ref]
        if len(cells) != len(CATEGORIES) or {c['category'] for c in cells} != set(CATEGORIES):
            raise ValueError('v2_metric_category_universe')
        denials = []
        for cell in cells:
            disposition = cell['coverage_disposition']
            if disposition not in ('PROVEN_APPLICABLE', 'PROVEN_NOT_APPLICABLE') or cell['missing_fields']:
                raise ValueError('v2_incomplete_category')
            if disposition == 'PROVEN_NOT_APPLICABLE':
                if (cell['required'] or cell['owner_state'] is not None
                        or ref not in cell['not_applicable_to_metric_refs']
                        or not cell['not_applicable_reason_codes']):
                    raise ValueError('v2_unproven_nonconsumption')
                continue
            if (cell['owner_state'] not in ('QUALIFIED','DENIED')
                    or ref not in cell['applies_to_metric_refs']
                    or not all(cell.get(k) for k in ('owner_contract','owner_ref','owner_decision_version',
                        'owner_field_eligibility','owner_as_of','owner_temporal_scope','input_refs','input_sha256'))
                    or cell['coverage_proof_kind'] == 'PRODUCER_SEMANTICS'):
                raise ValueError('v2_current_category_ownership_gap')
            if cell['owner_state'] == 'DENIED':
                matches = [b for b in blocks if b['scope_level'] == 'METRIC_SCOPED'
                    and b['owner_ref'] == cell['owner_ref'] and b['owner_contract'] == cell['owner_contract']
                    and b['input_sha256'] == cell['input_sha256']
                    and cell['category'] in b['category'] and ref in b['affected_metric_refs']
                    and sorted(b['reason_codes']) == sorted(cell['denial_reason_codes'])]
                if len(matches) != 1:
                    raise ValueError('v2_exact_metric_denial_binding')
                denials.append(matches[0]['blocker_ref'])
        if ref in facts and denials:
            state = 'INVALID_CONTRADICTORY_OWNERSHIP'
        elif denials:
            state = 'UNUSABLE_TYPED_DENIAL'
        elif ref in facts:
            state = 'USABLE'
        else:
            raise ValueError('v2_no_fact_and_no_typed_denial')
        results.append(sealed(dict(contract=METRIC, ticker=subject['ticker'], metric_ref=ref,
            metric=cells[0]['metric'], state=state, category_cells_sha256=digest(cells),
            coverage_row_sha256=row['receipt_sha256'], qualified_fact_sha256=digest(facts[ref]) if ref in facts else None,
            exact_blocker_refs=sorted(set(denials)), relevant=True, supersession_contract=None)))
    for ref, fact in subject['facts'].items():
        if ref in facts:
            continue
        if fact['metric'] != 'PBR' or fact['asset_relevance_proven'] is not False:
            raise ValueError('v2_unknown_irrelevant_metric')
        results.append(sealed(dict(contract=METRIC, ticker=subject['ticker'], metric_ref=ref,
            metric='PBR', state='NOT_RELEVANT', category_cells_sha256=None,
            coverage_row_sha256=row['receipt_sha256'], qualified_fact_sha256=digest(fact),
            exact_blocker_refs=[], relevant=False, supersession_contract=None,
            reason='FROZEN_V1_PBR_REQUIRES_OWNED_ASSET_RELEVANCE')))
    return results


def evaluability(subject, row, census, coverage_sha):
    metrics = metric_resolution(subject, row, census)
    relevant = [r for r in metrics if r['relevant']]
    usable = sorted(r['metric_ref'] for r in relevant if r['state'] == 'USABLE')
    blocked = sorted(r['metric_ref'] for r in relevant if r['state'] == 'UNUSABLE_TYPED_DENIAL')
    invalid = any(r['state'] == 'INVALID_CONTRADICTORY_OWNERSHIP' for r in relevant)
    if invalid:
        state = 'INVALID_INCOMPLETE_CONTRACT'
    elif usable:
        state = 'EVALUABLE'
    elif relevant and len(blocked) == len(relevant) and all(r['exact_blocker_refs'] for r in relevant):
        state = 'ALL_RELEVANT_METRICS_UNUSABLE'
    else:
        state = 'INVALID_INCOMPLETE_CONTRACT'
    refs = sorted({b for r in relevant for b in r['exact_blocker_refs']})
    all_proof = sealed(dict(contract='AllRelevantValuationMetricsUnusableV2',
        ticker=subject['ticker'], relevant_metric_refs=sorted(row['relevant_valuation_metric_refs']),
        metric_resolution_refs=[r['receipt_sha256'] for r in relevant], exact_blocker_refs=refs,
        no_usable_metric_survives=True, metric_scopes_unchanged=True,
        coverage_receipt_sha256=coverage_sha, blocker_census_receipt_sha256=census['receipt_sha256']
    )) if state == 'ALL_RELEVANT_METRICS_UNUSABLE' else None
    value = sealed(dict(contract=EVALUABILITY, ticker=subject['ticker'],
        relevant_valuation_metric_refs=sorted(row['relevant_valuation_metric_refs']),
        metric_resolution_refs=[r['receipt_sha256'] for r in metrics],
        qualified_relevant_valuation_refs=sorted(row['qualified_relevant_valuation_refs']),
        metric_blocker_refs=refs, blocked_metric_refs=blocked, usable_valuation_metric_refs=usable,
        coverage_receipt_ref=coverage_sha, blocker_census_receipt_ref=census['receipt_sha256'],
        evaluability_state=state, all_metrics_unusable_proof=all_proof is not None,
        all_metrics_unusable_proof_ref=all_proof['receipt_sha256'] if all_proof else None))
    if set(usable) & set(blocked):
        raise ValueError('v2_cross_metric_denial')
    return value, metrics, all_proof


def confidence_owner(owner, subject):
    """Reserved explicit current-owner interface; no real owner is manufactured here."""
    if owner is None:
        return []
    verified(owner, CONFIDENCE)
    if (owner.get('ticker') != subject['ticker'] or owner.get('security_id') != subject['security_id']
            or owner.get('source_generation') != subject['source_generation_id']
            or owner.get('scope') != 'NEWBUYER_GLOBAL'
            or owner.get('category') != 'NEWBUYER_CONFIDENCE_ADMISSIBILITY'
            or owner.get('state') != 'DENIED' or owner.get('cross_cutting_admissibility') is not True
            or not owner.get('input_refs') or not owner.get('input_sha256')
            or not owner.get('reason_codes') or owner.get('proof_type') != 'CURRENT_TYPED_OWNER'):
        raise ValueError('v2_unauthorized_confidence_veto')
    aware(owner.get('as_of'))
    return ['current-confidence:'+owner['receipt_sha256']]


def business_roles(subject, census, confidence=None):
    cap = subject['capability']
    positive, negative, risk = (sorted(set(cap[k])) for k in ('positive','negative','holder_risk'))
    legacy = set(cap['confidence'] + cap['quality'])
    if legacy & set(positive + negative + risk):
        raise ValueError('v2_legacy_directional_role_overlap')
    claims = {c['claim_ref']: c for c in subject['frozen_business_claims']}
    if len(claims) != len(subject['frozen_business_claims']) or not set(positive+negative+risk) <= set(claims):
        raise ValueError('v2_business_claim_binding')
    roles, linked, invalidated = [], [], set()
    for b in census['rows']:
        if b['ticker'] != subject['ticker']:
            continue
        if b['canonical_security_id'] != subject['security_id'] or b['source_generation'] != subject['source_generation_id']:
            raise ValueError('v2_blocker_subject_binding')
        links = []
        if b['scope_level'] == 'METRIC_SCOPED':
            role, rule = 'METRIC_ELIGIBILITY_ONLY', 'S8_METRIC_SCOPE'
        elif b['scope_level'] == 'BUSINESS_GLOBAL' and b['category'] == ['BUSINESS_SOURCE_QUALITY']:
            # Direct exact ref intersection only. Parent-source or period similarity is not linkage.
            for ref in positive+negative:
                exact = sorted(set(claims[ref]['claim']['evidence_refs']) & set(b['affected_metric_refs']))
                if exact:
                    links.append(dict(blocker_ref=b['blocker_ref'], affected_source_refs=exact,
                        core_capability_ref=ref, core_claim_sha256=digest(claims[ref]),
                        contribution='POSITIVE' if ref in positive else 'NEGATIVE',
                        rule='DIRECT_EXACT_AFFECTED_EVIDENCE_NOT_PARENT_SOURCE'))
            role = 'BUSINESS_GATE_QUALITY' if links else 'CONTEXT_ONLY'
            rule = 'S8_EXACT_GATE_SUPPORT_LINK' if links else 'S8_NO_EXACT_GATE_SUPPORT_LINK'
        else:
            raise ValueError('v2_unreviewed_blocker_role')
        roles.append(dict(blocker_ref=b['blocker_ref'], category=deepcopy(b['category']),
            owner_contract=b['owner_contract'], owner_ref=b['owner_ref'],
            scope=b['scope_level'], role=role, rule=rule, exact_linkage=links,
            affected_metric_refs=deepcopy(b['affected_metric_refs']), reason_codes=deepcopy(b['reason_codes'])))
        linked.extend(links)
        invalidated.update(r['core_capability_ref'] for r in links)
    eligible_pos = sorted(set(positive)-invalidated)
    eligible_neg = sorted(set(negative)-invalidated)
    base = v1.business_gate(subject)
    admissible = bool(eligible_pos) and not eligible_neg and not risk
    gate = sealed(dict(contract='NewBuyerBusinessGateV2', base_business_gate_pass=base,
        base_business_positive_refs=positive, base_business_negative_refs=negative,
        business_quality_blocker_refs=[r['blocker_ref'] for r in roles if r['role']=='BUSINESS_GATE_QUALITY'],
        business_quality_linkage_refs=[digest(r) for r in linked],
        eligible_positive_core_refs_after_quality=eligible_pos,
        eligible_negative_core_refs_after_quality=eligible_neg,
        business_evidence_admissible=admissible, v2_business_gate_pass=base and admissible,
        quality_invalidates_required_support=base and not admissible and bool(invalidated),
        active_risk_refs=risk, frozen_overall=subject['frozen_overall']))
    confidence_refs = confidence_owner(confidence, subject)
    if confidence_refs:
        roles.append(dict(blocker_ref=confidence_refs[0],category=[confidence['category']],
            owner_contract=confidence['contract'], owner_ref=confidence['receipt_sha256'],
            scope=confidence['scope'],role='NEWBUYER_CONFIDENCE_VETO',rule='S17_EXPLICIT_CURRENT_OWNER',
            exact_linkage=[], affected_metric_refs=[],reason_codes=confidence['reason_codes']))
    policy = sealed(dict(contract=POLICY, rows=roles, confidence_veto_refs=confidence_refs,
        linkage_proof=linked, automatic_census_veto=False, global_valuation_veto_refs=[]))
    return policy, gate


def legacy_entitlement(subject, records, coverage_sha, census_sha):
    refs = set(subject['capability']['confidence'] + subject['capability']['quality'])
    claims = {r['claim_ref']: r for r in subject['frozen_business_claims']}
    rows = [r for r in records if r['ticker'] == subject['ticker']]
    if len(rows) != len(refs) or {r['claim_ref'] for r in rows} != refs:
        raise ValueError('v2_legacy_audit_universe')
    result = []
    for row in rows:
        ref = row['claim_ref']
        if digest(claims[ref]) != row['legacy_claim_sha256']:
            raise ValueError('v2_historical_claim_drift')
        result.append(dict(ticker=subject['ticker'],claim_ref=ref,historical_claim_preserved=True,
            original_effect=row['effect'], original_materiality=row['existing_materiality'],
            historical_claim_sha256=digest(claims[ref]),
            v2_newbuyer_veto_entitlement='CONTEXT_ONLY_NO_VETO_ENTITLEMENT',
            linked_current_blocker_refs=[],linkage_basis='NO_EXACT_CURRENT_TYPED_VETO_LINK',
            coverage_receipt_sha256=coverage_sha,blocker_census_receipt_sha256=census_sha,
            model_visible_in_b2_v2=False,renderer_or_audit_context_only=True,
            claim_semantics_reclassified=False,blind_label_used=False))
    return sealed(dict(contract='NewBuyerLegacyEntitlementV2',rows=result))


def choices(model_input, valuation_state):
    """Fundamental stance precedence; timing never participates in this function."""
    gate = model_input['business_gate']
    risk = model_input['active_risk_refs']
    if risk:
        return 'AVOID', 'ACTIVE_ADVERSE_UNCOMPENSATED', risk
    if not gate['v2_business_gate_pass']:
        if gate['quality_invalidates_required_support']:
            return 'WAIT', 'BUSINESS_EVIDENCE_UNCERTAINTY', gate['business_quality_blocker_refs']
        reason = 'BUSINESS_MIXED' if gate['base_business_positive_refs'] and gate['base_business_negative_refs'] else 'BUSINESS_GATE_NOT_MET'
        return 'WAIT', reason, sorted(set(gate['base_business_positive_refs']+gate['base_business_negative_refs']))
    if model_input['valuation_evaluability']['evaluability_state'] == 'ALL_RELEVANT_METRICS_UNUSABLE':
        return 'WAIT', 'VALUATION_UNRESOLVED', [model_input['all_metrics_unusable_proof_ref']] + model_input['valuation_evaluability']['metric_blocker_refs']
    if model_input['confidence_veto_refs']:
        return 'WAIT', 'CONFIDENCE_UNCERTAINTY', model_input['confidence_veto_refs']
    if valuation_state == 'SUPPORTIVE':
        return 'ATTRACTIVE', 'QUALIFIED_VALUATION_CONTEXT_SUPPORTIVE', gate['eligible_positive_core_refs_after_quality']
    if valuation_state in ('NEUTRAL','BURDENSOME'):
        return 'WAIT', 'VALUATION_'+valuation_state, None
    raise ValueError('v2_free_unresolved_forbidden')
