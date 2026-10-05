"""Reviewed REV56B category decisions, independent of audit/model lineage."""
from scripts.newbuyer_fper_prerequisite_scope import CATEGORIES

CONTRACT = "newbuyer-security-basis-applicability-coverage-v1"
NATIVE = "app/services/provider_native_valuation_snapshot.py"
FRESH = "app/services/current_fresh_valuation.py"
KIS = "scripts/kis_current_fy1_owner.py"
BUSINESS = "app/services/canonical_business_quality_owner.py"


def requirements(metric, family, security=None):
    """Family dataflow first; no ticker, output label, or legacy ref input."""
    result = []
    for category in CATEGORIES:
        required, reason, path = True, 'Existing producer consumes or gates this semantic domain.', NATIVE
        if family == 'ATOMIC':
            if category in {'PRICE_TO_SECURITY_BINDING', 'VALUATION_CURRENCY_BASIS',
                            'SHARE_OR_DENOMINATOR_BASIS', 'BUSINESS_SOURCE_QUALITY'}:
                required = False
                reason = {
                    'PRICE_TO_SECURITY_BINDING': 'Current price is CONTEXT_ONLY; no price/native-ratio arithmetic.',
                    'VALUATION_CURRENCY_BASIS': 'No reporting-currency/price-currency conversion; provider identity currency checks stay in exact identity scope. Null currency is not currency clearance.',
                    'SHARE_OR_DENOMINATOR_BASIS': 'Atomic provider field is consumed without EPS/share reconstruction or share-unit adjustment.',
                    'BUSINESS_SOURCE_QUALITY': 'Reported-business quality is a separate BUSINESS_GLOBAL decision input, not an atomic valuation denominator.',
                }[category]
                path = FRESH if category == 'PRICE_TO_SECURITY_BINDING' else NATIVE
            if category == 'DEPOSITARY_OR_ADR_CONVERSION' and security:
                kind = str(security.get('security_type', '')).lower()
                if kind == 'common_stock' and security.get('issuer_type') != 'adr':
                    required = False
                    reason = ('Hash-bound security input selects the direct common-stock producer path; '
                              'no depositary conversion arithmetic or cross-security transfer is consumed. '
                              'This does not clear a failed exact-provider-identity gate.')
        elif family == 'DERIVED_KIS':
            path = KIS
            if category == 'BUSINESS_SOURCE_QUALITY':
                required, reason = False, 'Uses KIS research EPS, not reported business-quality fields.'
            if category == 'DEPOSITARY_OR_ADR_CONVERSION':
                required, reason = False, 'Domestic KIS product/standard-code equality and KRW/KRW-per-share quotient; no cross-security conversion exists in this path.'
        else:
            raise ValueError('unreviewed_metric_family')
        result.append(dict(category=category, metric=metric, required=required,
            requirement_owner_contract=CONTRACT, requirement_proof_kind='PRODUCER_SEMANTICS',
            requirement_reason=reason, producer_dataflow_proof_refs=[path],
            necessity_derived_from_legacy=False))
    return result


def base_cell(req, ticker, ref, generation, security, owner):
    from app.services.unified_snapshot_contract import digest
    return dict(**req, ticker=ticker, metric_ref=ref, required_for_metric_refs=[ref] if req['required'] else [],
        category_requirement_basis=req['requirement_reason'], coverage_disposition='UNRESOLVED',
        coverage_proof_kind='COMPOSED_TYPED_OWNER', owner_state='UNKNOWN', scope_level='METRIC_SCOPED',
        owner_contract=owner.get('contract'), owner_ref=owner.get('receipt_sha256', owner.get('snapshot_sha256')),
        owner_decision_version=None, owner_field_eligibility={}, owner_as_of=None, owner_effective_at=None,
        owner_temporal_scope=None, source_generation=generation, security_id=security,
        applies_to_metric_refs=[ref] if req['required'] else [], not_applicable_to_metric_refs=[],
        not_applicable_reason_codes=[], denial_reason_codes=[], qualification_reason_codes=[],
        input_refs=[], input_sha256=digest(owner), missing_fields=[])


def nonapplicable(cell):
    if cell['required'] or not cell['producer_dataflow_proof_refs']:
        raise ValueError('required_or_unproved_domain_cannot_be_not_applicable')
    cell.update(coverage_disposition='PROVEN_NOT_APPLICABLE', coverage_proof_kind='PRODUCER_SEMANTICS',
        owner_state=None, owner_contract=CONTRACT, owner_ref='producer-dataflow:'+cell['metric'],
        owner_decision_version='REV56B_AUDITED_DATAFLOW_NOT_CURRENT_STATE',
        owner_field_eligibility={'semantic_domain_consumed': False},
        owner_temporal_scope='STATIC_CODE_DATAFLOW: non-consumption is not a dated security or financial verdict',
        not_applicable_to_metric_refs=[cell['metric_ref']],
        not_applicable_reason_codes=['POSITIVE_PRODUCER_NONCONSUMPTION_PROOF'],
        input_refs=cell['producer_dataflow_proof_refs'])
    return cell


def finish(cell):
    if cell['coverage_disposition'] == 'PROVEN_NOT_APPLICABLE':
        if cell['required'] or cell['coverage_proof_kind'] != 'PRODUCER_SEMANTICS' or not cell['input_refs']:
            raise ValueError('invalid_not_applicable_proof')
        return cell
    if cell['coverage_proof_kind'] == 'PRODUCER_SEMANTICS':
        cell['missing_fields'].append('runtime_or_composed_current_decision_owner')
    needed = ['owner_contract', 'owner_ref', 'owner_decision_version', 'owner_field_eligibility',
              'owner_as_of', 'owner_temporal_scope', 'source_generation', 'security_id', 'input_refs']
    cell['missing_fields'] = sorted(set(cell['missing_fields'] + [k for k in needed if not cell.get(k)]))
    if cell['missing_fields'] or cell['owner_state'] == 'UNKNOWN':
        cell['coverage_disposition'], cell['owner_state'] = 'UNRESOLVED', 'UNKNOWN'
    else:
        cell['coverage_disposition'] = 'PROVEN_APPLICABLE'
    return cell


def native_cell(req, ticker, ref, source, snapshot, security):
    view = source['valuation_view']
    cell = base_cell(req, ticker, ref, view['run_id'], view['security_id'], snapshot)
    if not req['required']:
        return nonapplicable(cell)
    identity = snapshot['security_identity_receipt']
    exact = identity['status'] == 'QUALIFIED_EXACT_SECURITY'
    cell.update(owner_decision_version=snapshot['contract']+' + '+identity['contract'],
        owner_field_eligibility={'new_buyer_valuation_context_eligible': snapshot['new_buyer_valuation_context_eligible'],
                                 'identity_admitted': exact},
        owner_as_of=snapshot['retrieval_timestamp'], owner_effective_at=snapshot['metric_asof'],
        owner_temporal_scope='PROVIDER_LATEST_SNAPSHOT_AT_RETRIEVAL; underlying metric-as-of remains unknown when null',
        input_refs=[snapshot['snapshot_sha256'], snapshot['source_receipt_sha256'],
                    identity['receipt_sha256'], view['security_sha256']])
    category = req['category']
    if category in {'SECURITY_IDENTITY', 'PROVIDER_SECURITY_BINDING', 'VALUATION_SECURITY_BASIS'}:
        cell['owner_state'] = 'QUALIFIED' if exact else 'DENIED'
        cell['qualification_reason_codes'] = ['EXACT_PROVIDER_SECURITY_ADMISSION'] if exact else []
        cell['denial_reason_codes'] = identity['reasons'] if not exact else []
    elif category == 'SECURITY_CLASS_OR_LISTING':
        from app.services.provider_native_valuation_snapshot import MARKETS, _exchange
        if snapshot['provider'] == 'kiwoom':
            listing_pass = any(identity['market_exchange'] in aliases
                and security['exchange'] in {'KRX', aliases[0]} for aliases in MARKETS.values())
        else:
            listing_pass = (identity['market_exchange'] in {'NASDAQ', 'NYSE'}
                            and identity['market_exchange'] == _exchange(security['exchange']))
        cell['owner_state'] = 'QUALIFIED' if listing_pass else 'DENIED'
        cell['owner_field_eligibility']['listing_predicate'] = listing_pass
        cell['owner_field_eligibility']['requested_listing'] = security['exchange']
        cell['owner_field_eligibility']['returned_listing'] = identity['market_exchange']
        cell['qualification_reason_codes'] = ['BOUND_LISTING_PREDICATE_NOT_WHOLE_SHARE_CLASS_CLEARANCE'] if listing_pass else []
        cell['denial_reason_codes'] = [] if listing_pass else ['BOUND_PROVIDER_LISTING_PREDICATE_FAILED']
    elif category == 'DEPOSITARY_OR_ADR_CONVERSION':
        adr_denied = 'UNAVAILABLE_ADR_CONVERSION' in identity['reasons']
        if exact:
            cell['owner_state'] = 'QUALIFIED'
            cell['qualification_reason_codes'] = ['DIRECT_SECURITY_ADMISSION_GUARD_PASSED_NO_CONVERSION_GRANTED']
        elif adr_denied:
            cell['owner_state'], cell['denial_reason_codes'] = 'DENIED', ['UNAVAILABLE_ADR_CONVERSION']
        else:
            cell['missing_fields'] = ['depositary_specific_eligibility_decision']
    elif category == 'VALUATION_HORIZON_OR_PERIOD':
        # Qualified here means the declared label/snapshot temporal scope is
        # owned, not that a missing ratio or an exact metric date is available.
        cell['owner_state'] = 'QUALIFIED'
        cell['qualification_reason_codes'] = ['DECLARED_PROVIDER_METRIC_SEMANTICS_ONLY']
        cell['owner_field_eligibility']['semantic_scope'] = snapshot['metric_semantic']
        if req['metric'] == 'FORWARD_PE':
            cell['owner_field_eligibility']['horizon_authority'] = snapshot['horizon_authority']
            cell['owner_field_eligibility']['provider_horizon'] = snapshot['provider_horizon']
            cell['owner_field_eligibility']['canonical_horizon'] = snapshot['canonical_horizon']
    elif category == 'VALUATION_SOURCE_QUALITY':
        cell['owner_state'] = 'QUALIFIED' if snapshot['new_buyer_valuation_context_eligible'] else 'DENIED'
        cell['qualification_reason_codes'] = [snapshot['state']] if cell['owner_state'] == 'QUALIFIED' else []
        cell['denial_reason_codes'] = [snapshot['state']] if cell['owner_state'] == 'DENIED' else []
    else:
        raise AssertionError(category)
    return finish(cell)


def kis_cell(req, ticker, ref, source, row, view_hash):
    view, fper = source['valuation_view'], row['current_fper']
    cell = base_cell(req, ticker, ref, view['run_id'], view['security_id'], fper)
    if not req['required']:
        return nonapplicable(cell)
    eps, price, action = row['eps'], row['price'], row['action']
    if fper['state'] != 'QUALIFIED':
        cell['missing_fields'] = ['field_specific_current_decision', 'decision_version',
            'field_eligibility', 'field_effective_time', 'typed_denial_source_receipt_binding']
        cell['input_refs'] = [fper['receipt_sha256'], view_hash]
        cell['limitation'] = ('UNAVAILABLE_EPS preserves nonavailability but is returned before EPS security/date, '
            'current price and action scope are assessed. Acquisition time and wrapper generation do not '
            'supply those field decisions. Required derived domains remain unresolved, not DENIED or N/A.')
        return finish(cell)
    cell.update(owner_state='QUALIFIED', owner_decision_version=eps['contract']+' + '+action['contract'],
        owner_field_eligibility={'allowed_roles': fper['allowed_roles'], 'state': fper['state'],
            'eps_unit': eps['unit'], 'price_currency': price['currency'],
            'scope': 'EXACT_CURRENT_CLOSE_AND_DATED_HOUSE_RESEARCH_EPS_ONLY'},
        owner_as_of=eps['query_time'], owner_effective_at=fper['session_date'],
        owner_temporal_scope={'eps_estimate_date': eps['estdate'], 'fy1_period': eps['period'],
            'price_session': price['session_date'], 'price_retrieved_at': price['retrieved_at'],
            'action_window': action['guard_envelope'], 'not_current_estimate': True},
        input_refs=[fper['receipt_sha256'], eps['receipt_sha256'], price['receipt_sha256'],
                    action['receipt_sha256'], view_hash],
        qualification_reason_codes=['EXACT_REPLAYED_KIS_PRICE_EPS_ACTION_COMPOSITION'])
    return finish(cell)


def business_cell(ticker, source):
    view, quality = source['valuation_view'], source['quality_view']
    fact, receipt = quality['fact'], quality['receipt']
    req = dict(category='BUSINESS_SOURCE_QUALITY', metric='SELECTED_REPORTED_BUSINESS', required=True,
        requirement_owner_contract=CONTRACT, requirement_proof_kind='PRODUCER_SEMANTICS',
        requirement_reason='Independent selected reported-business gate; never a valuation metric denominator.',
        producer_dataflow_proof_refs=[BUSINESS], necessity_derived_from_legacy=False)
    cell = base_cell(req, ticker, receipt['canonical_ref'], view['run_id'], view['security_id'], receipt)
    fields = [field for out in receipt['owner_outputs'] for field in out['quality']['fields'].values()]
    cell.update(scope_level='BUSINESS_GLOBAL', owner_state='DENIED' if any(r['state'] == 'denied' for r in fields) else 'QUALIFIED',
        owner_decision_version=fact['fields']['decision_version'],
        owner_field_eligibility={'fields': fields, 'security_valuation_transfer': False},
        owner_as_of=fact['as_of_date'], owner_effective_at=fact['as_of_date'],
        owner_temporal_scope={'source_period': fact['as_of_date'],
            'filing_dates': sorted({o['metadata']['filing_date'] for o in receipt['owner_outputs']})},
        input_refs=[receipt['receipt_sha256'], receipt['projection_sha256'], receipt['fact_sha256']],
        qualification_reason_codes=[] if any(r['state'] == 'denied' for r in fields) else ['SELECTED_FIELDS_USABLE'],
        denial_reason_codes=fact['fields']['reason_codes'] if any(r['state'] == 'denied' for r in fields) else [])
    if any(r['state'] not in {'denied', 'verified_usable', 'caution_usable'} for r in fields):
        cell['owner_state'] = 'UNKNOWN'
    return finish(cell)
