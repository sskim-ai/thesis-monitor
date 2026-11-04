"""Opt-in dated reported amounts from original replay, not new use authority."""
from app.services.bounded_financial_projection import project
from app.services.vnext_research_store import digest
from scripts.m12dr_financial_source_authority import source_quality

CONTRACT = 'vnext-original-reported-amount-reference-v1'
CONTEXT_CONTRACT = 'vnext-original-cfbs-context-v1'


def _context_fact(field, projection):
    roles = {'operating_cashflow': 'OPERATING_CASHFLOW', 'operating_cash_flow': 'OPERATING_CASHFLOW',
        'assets': 'BALANCE_ASSETS', 'liabilities': 'BALANCE_LIABILITIES', 'equity': 'BALANCE_TOTAL_EQUITY',
        'stockholders_equity': 'BALANCE_STOCKHOLDERS_EQUITY',
        'debt_including_current': 'DEBT_INCLUDING_CURRENT', 'owners_parent_net_income': 'OWNERS_PARENT_NET_INCOME',
        'noncontrolling_interest': 'NONCONTROLLING_INTEREST', 'cash_and_cash_equivalents': 'CASH_AND_CASH_EQUIVALENTS'}
    f = field
    result = dict(contract=CONTEXT_CONTRACT, as_of_date=f['period_end'],
        quality_contract=CONTEXT_CONTRACT, quality_receipt_sha256=f['normalized_hash'],
        projection_sha256=digest(projection), interpretation_eligible=False, prose_eligible=True,
        fields=dict(metric=f['metric'], current_value=f['value'], period_start=f['period_start'],
            period_end=f['period_end'], period_type=f['period_role'], period_kind=f['period_kind'],
            fact_role=roles[f['metric']]+'_'+f['period_role'].upper(), semantic=f['semantic'],
            currency=f['currency'], unit=f['unit'], unit_scale=f['unit_scale'], statement_basis=f['statement_basis'],
            consolidation_explicitly_proven=f['consolidation_explicitly_proven'], accounting_standard=f['accounting_standard'],
            source_ticker=f['ticker'], canonical_security_id=f['canonical_security_id'],
            canonical_company_id=f['canonical_company_id'], issuer_id=f['provider_issuer_id'],
            source_receipt=f['source_document_id'], source_occurrences=[f['occurrence_id']],
            filing_date=f['filing_date'], fiscal_year=f['fiscal_year'], fiscal_period=f['fiscal_period'],
            original_raw_sha256=f['raw_artifact_sha256'], source_generation=projection['source_generation'],
            source_cutoff=projection['source_cutoff'], context_projection_sha256=digest(projection),
            observation_only=True, comparison_eligible=False, recurrence_verified=False,
            mechanism_verified=False, structural_risk_verified=False, direction_allowed=False,
            valuation_denominator_eligible=False, strict_owner_issued=False,
            limitations=['Exact dated amount only; no comparison, cash-conversion, recurrence, valuation or direction grant.',
                'Same filing is correlated evidence, never independent corroboration.',
                'Entity-wide SEC scope is not a separate consolidated-statement attestation.']))
    if f.get('documentary_reconciliation'):
        proof = f['documentary_reconciliation']
        result['fields'].update(documentary_reconciliation=proof,
            documentary_receipt_sha256=proof['receipt_sha256'],
            qualified_comparison=dict(value=proof['cells'][1]['value'],
                period=proof['periods'][1], source_cell=proof['cells'][1],
                use='SAME_FILING_H1_CFS_CFO_FACT_ONLY', economic_interpretation=False),
            counterevidence_rows=proof['counterevidence_rows'],
            review_cutoff=proof['review_cutoff'], retrospective_qualification=True)
        result['fields']['limitations'] = [
            'Newly documented retrospective H1 CFO amount and same-filing comparison only.',
            'No Q2, cash-conversion, FCF, recurrence, valuation or investment-direction grant.',
            'All CF reconciliation rows retained as correlated context, not independent support.',
            'Original capture cutoff is preserved; later HTML does not certify old as-of availability.']
    return result


def replay_reported_context(*, plan, acquisition, directory, receipts, expected_projection,
                            security, project_options=None, documentary_input=None, extended_sec_fields=False):
    """Narrow opt-in extension; original amount/comparison routes are unchanged."""
    from app.services.bounded_financial_projection import reported_context_fields
    if plan['security'] != security or plan['ticker'] != security['ticker']:
        raise ValueError('financial_reuse_security_mismatch')
    result = reported_context_fields(plan, acquisition, directory, receipts,
        expected_projection=expected_projection, project_options=project_options,
        documentary_input=documentary_input, extended_sec_fields=extended_sec_fields)
    facts, denied = [], list(result['denied'])
    for field in result['fields']:
        if field['context_eligible'] and not field['quality_errors']:
            facts.append(_context_fact(field, result))
        else:
            denied.append(dict(metric=field['metric'], reason='CONTEXT_FIELD_QUALITY_DENIED',
                               field=field, details=field['quality_errors']))
    return dict(contract=CONTEXT_CONTRACT, facts=facts, denied=denied,
        projection_sha256=digest(result), original_projection_sha256=digest(expected_projection),
        strict_native=False, new_provider_requests=0)


def verify_reported_context(fact, security):
    """A serialized capsule is not authority; re-enter live original replay."""
    from app.services.bounded_financial_projection import replay_original_context
    fields = fact.get('fields', {})
    projection = replay_original_context(fields.get('context_projection_sha256'))
    if any(projection['security'].get(k) != security.get(k) for k in
           ('ticker', 'canonical_security_id', 'canonical_company_id', 'country', 'cik', 'corp_code',
            'ordinary_share_identifier', 'adr_ratio')):
        raise ValueError('reported_context_security_mismatch')
    expected = [_context_fact(f, projection) for f in projection['fields']
                if f['context_eligible'] and not f['quality_errors']]
    if fact not in expected:
        raise ValueError('reported_context_fact_owner_mismatch')
    return True


def balance_composition_property(facts, security):
    """P1 accounting composition, not a judgment about solvency or cheapness.

    Exact total-equity taxonomy is required. Parent stockholders' equity is
    not substituted, and a zero residual is not independent corroboration.
    """
    from decimal import Decimal, InvalidOperation, localcontext
    metrics = ('assets', 'liabilities', 'equity')
    selected = {m: [f for f in facts if f.get('fields', {}).get('metric') == m] for m in metrics}
    result = dict(property='REPORTED_CONSOLIDATED_BALANCE_COMPOSITION', level='P1',
        contract=CONTEXT_CONTRACT, status='INSUFFICIENT', factual_arithmetic_supported=False,
        property_interpretation_qualified=False, business_driver_eligible=False,
        valuation_metric_eligible=False, overall_direction_eligible=False,
        current_qualified=False, independent_corroboration=False)
    if any(len(selected[m]) != 1 for m in metrics):
        return dict(result, reason='EXACT_TOTAL_BALANCE_COMPONENTS_REQUIRED',
                    metric_counts={m: len(selected[m]) for m in metrics})
    ordered = [selected[m][0] for m in metrics]
    for fact in ordered:
        verify_reported_context(fact, security)
    fields = [f['fields'] for f in ordered]
    shared = ('canonical_security_id', 'canonical_company_id', 'issuer_id', 'source_receipt',
        'original_raw_sha256', 'source_generation', 'period_start', 'period_end', 'period_kind',
        'period_type', 'statement_basis', 'currency', 'unit', 'unit_scale', 'accounting_standard')
    if any(not fields[0].get(k) or any(f.get(k) != fields[0][k] for f in fields[1:]) for k in shared):
        return dict(result, reason='BALANCE_SCOPE_PERIOD_UNIT_OR_ORIGIN_MISMATCH')
    taxonomy = {
        'IFRS': ('ifrs-full_Assets', 'ifrs-full_Liabilities', 'ifrs-full_Equity'),
        'US-GAAP': ('us-gaap:Assets', 'us-gaap:Liabilities',
                    'us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'),
    }
    if (tuple(f.get('semantic') for f in fields) != taxonomy.get(fields[0]['accounting_standard'])
            or any(f.get('consolidation_explicitly_proven') is not True for f in fields)
            or fields[0]['statement_basis'] != 'consolidated'):
        return dict(result, reason='TOTAL_EQUITY_AND_CONSOLIDATED_SCOPE_REQUIRED')
    if fields[0]['period_kind'] != 'instant' or fields[0]['period_start'] != fields[0]['period_end']:
        return dict(result, reason='SAME_INSTANT_REQUIRED')
    occurrences = [f['source_occurrences'] for f in fields]
    if any(len(o) != 1 for o in occurrences) or len({o[0] for o in occurrences}) != 3:
        return dict(result, reason='DISTINCT_EXACT_BALANCE_OCCURRENCES_REQUIRED')
    try:
        values = [Decimal(str(f['current_value'])) for f in fields]
        if any(not v.is_finite() for v in values) or values[0] <= 0:
            return dict(result, reason='FINITE_POSITIVE_ASSET_DENOMINATOR_REQUIRED')
        with localcontext() as context:
            context.prec = max(len(format(v, 'f')) for v in values) + 3
            residual = values[0] - values[1] - values[2]
        if residual:
            return dict(result, reason='REPORTED_BALANCE_IDENTITY_CONTRADICTED', residual=str(residual))
    except (InvalidOperation, TypeError, ValueError):
        return dict(result, reason='BALANCE_VALUE_NOT_EXACT_NUMERIC')
    # Exact rational expressions avoid inventing a tolerance or a risk threshold.
    text = lambda value: format(value, 'f').rstrip('0').rstrip('.') if '.' in format(value, 'f') else format(value, 'f')
    amounts = dict(zip(metrics, map(text, values)))
    result.update(status='QUALIFIED_FACTUAL_PROPERTY', factual_arithmetic_supported=True,
        reason='EXACT_REPORTED_IDENTITY_AND_SAME_SCOPE_COMPONENTS', as_of_date=fields[0]['period_end'],
        security_id=security['canonical_security_id'], source_receipt=fields[0]['source_receipt'],
        origin_group=fields[0]['issuer_id']+':'+fields[0]['source_receipt'],
        original_raw_sha256=fields[0]['original_raw_sha256'], currency=fields[0]['currency'],
        unit_scale=fields[0]['unit_scale'], statement_basis=fields[0]['statement_basis'],
        source_generation=fields[0]['source_generation'], source_occurrences=occurrences,
        source_fact_hashes=[digest(f) for f in ordered], source_quality_receipts=[f['quality_receipt_sha256'] for f in ordered],
        formula='assets = liabilities + total_equity', residual='0', amounts=amounts,
        component_fractions={m: dict(numerator=amounts[m], denominator=amounts['assets']) for m in ('liabilities','equity')},
        allowed_use='DATED_FACTUAL_ACCOUNTING_EXPLANATION_ONLY',
        limitations=['Same filing: correlated components, not independent evidence.',
                    'A balanced identity is not evidence of resilience, recurring profit, low risk or fair value.',
                    'No current freshness, share/ADS denominator, valuation or investment-direction grant.'])
    result['property_sha256'] = digest(result)
    return result


def replay_reported_amounts(*, plan, acquisition, directory, receipts, expected_projection,
                           security, project_options=None):
    if plan['security'] != security or plan['ticker'] != security['ticker']:
        raise ValueError('financial_reuse_security_mismatch')
    actual = project(plan, acquisition, directory, receipts, **(project_options or {}))
    if actual != expected_projection:
        raise ValueError('original_financial_projection_drift')
    facts, denied = [], []
    for bundle in actual['quality_bundles']:
        quality = source_quality(bundle)
        if quality != bundle['quality']:
            raise ValueError('original_quality_drift')
        for metric in ('revenue', 'operating_income', 'net_income'):
            q = quality['fields'].get('current.' + metric, {})
            fields = [f for f in actual['fields'] if f['metric'] == metric and f['current_prior_role'] == 'current']
            unique = {f['normalized_hash']: f for f in fields}
            if len(unique) != 1 or q.get('prose_eligible') is not True or q.get('hard_denial_reasons'):
                denied.append(dict(metric=metric, reason='ORIGINAL_REPORTED_FIELD_NOT_QUALIFIED',
                                   details=q.get('hard_denial_reasons', ['ORIGINAL_PROSE_OWNER_NOT_AVAILABLE'])))
                continue
            f = next(iter(unique.values()))
            lineage = q.get('lineage') or {}
            if (not f['context_eligible'] or f['quality_errors'] or
                    lineage.get('amount') != f['value'] or
                    lineage.get('source_row_identity') != f['occurrence_id'] or
                    lineage.get('amount_period_start') != f['period_start'] or
                    lineage.get('amount_period_end') != f['period_end'] or
                    lineage.get('currency') != f['currency'] or
                    lineage.get('statement_basis') != f['statement_basis']):
                raise ValueError('reported_field_lineage_disagreement')
            issuer = ('CIK:' if plan['market'] == 'us' else 'DART:') + plan['issuer']
            facts.append(dict(contract=CONTRACT, as_of_date=f['period_end'],
                quality_contract=quality['contract'], quality_receipt_sha256=quality['receipt_sha256'],
                fields=dict(metric=metric, current_value=f['value'], period_start=f['period_start'],
                    period_end=f['period_end'], period_type=f['period_role'], currency=f['currency'],
                    unit=f['unit'], unit_scale=f['unit_scale'], statement_basis=f['statement_basis'],
                    issuer_id=issuer, source_ticker=plan['ticker'], source_receipt=f['source_document_id'],
                    source_occurrences=[f['occurrence_id']], original_raw_sha256=f['raw_artifact_sha256'],
                    source_generation=plan['run_id'], source_cutoff=plan['cutoff'],
                    observation_only=True, comparison_eligible=False, recurrence_verified=False,
                    valuation_denominator_eligible=False, strict_owner_issued=False,
                    anomaly_cautions=quality['quality_reason_codes'],
                    limitations=quality['limitations'] + ['Dated single reported amount; no growth, recurring-profit, EPS or valuation denominator grant.']),
                projection_sha256=digest(actual)))
    return dict(contract=CONTRACT, facts=facts, denied=denied, strict_native=False,
                replay_only=True, new_provider_requests=0, projection_sha256=digest(actual))
