"""Dated research wording after original source/use verification, not roles."""
from calendar import monthrange
from datetime import date
from decimal import Decimal

CONTRACT = 'reported-financial-research-observation-v1'
NO_DRIVER_MEANING = ('NO_ELIGIBLE_ECONOMIC_EVIDENCE means no authorized directional '
    'business-thesis driver. It does not mean no published financial data, and is not a negative judgment.')


def historical_kis_reference(reviewed_owner, *, security, as_of):
    """Adapt a backend-reviewed historical Owner record, not a new FY1 grant.

    Custody/review capability must come from trusted backend code. A receipt JSON
    or its caller-generated hash is never a substitute for that capability.
    """
    from app.services.vnext_composite_research import instant
    from app.services.vnext_research_store import digest
    from scripts.kis_current_fy1_owner import current_fper, eps_receipt
    if not callable(reviewed_owner):raise ValueError('historical_owner_capability_required')
    original=reviewed_owner(security)
    row=original['row'];eps=row['eps'];price=row.get('price')
    if (row['security_code']!=security['ticker'] or security['country']!='KR' or
        not original.get('verified_archive_sha256') or not original.get('source_generation') or
        instant(original['as_of'])>=instant(as_of)):
        raise ValueError('historical_owner_security_or_time')
    if eps.get('state')!='KIS_FY1_EPS_ESTIMATE_SNAPSHOT':
        return dict(contract='historical-kis-reference-v1',status='TYPED_UNAVAILABLE',
            security=security['ticker'],reason=eps.get('state'),source_generation=original['source_generation'],facts=[])
    value=eps_receipt(eps)
    reproduced=current_fper(eps,price,row.get('action'))
    if reproduced!=row['current_fper'] or reproduced['state']!='QUALIFIED' or price['canonical_security_id']!=security['canonical_security_id']:
        raise ValueError('historical_owner_reproduction_or_identity')
    facts=[dict(metric='HISTORICAL_FY1_EPS',value=str(value),unit='KRW_PER_SHARE',period=eps['period'],as_of=eps['query_time'],source_sha=eps['estimate_sha256']),
           dict(metric='HISTORICAL_DERIVED_FPER',value=reproduced['display_value'],unit='multiple',period=eps['period'],as_of=price['session_date'],source_sha=price['raw_response_sha256'])]
    return dict(contract='historical-kis-reference-v1',status='HISTORICAL_QUALIFIED_NOT_CURRENT',security=security['ticker'],
        source_generation=original['source_generation'],archive_sha256=original['verified_archive_sha256'],
        original_owner_record_sha256=digest(row),facts=facts,current_source_eligible=False,strict_native=False,
        direction_allowed=False,allowed_use='HISTORICAL_RESEARCH_REFERENCE',provider_PER=False,
        limitation='Dated KIS house research, not consensus or current FY1 requalification; original share-unit guard remains bounded.')


def _quarter(cell):
    start,end=date.fromisoformat(cell['period_start']),date.fromisoformat(cell['period_end'])
    if (start.day!=1 or start.month not in (1,4,7,10) or end.year!=start.year or
        end.month!=start.month+2 or end.day!=monthrange(end.year,end.month)[1]):
        raise ValueError('exact_reported_quarter_required')
    return start.year*4+(start.month-1)//3


def reported_trends(projection):
    """Only verified exact research-reference cells; no ratios or causal claims."""
    from app.services.sec_research_source_authority import POLICY, POLICY_SHA256, USE
    if not projection:return None
    if (projection.get('contract')!=POLICY or projection.get('policy_sha256')!=POLICY_SHA256 or
        projection.get('use')!=USE or any(projection.get(k) is not False for k in
        ('strict_financial_L3','strict_native','investment_direction_grant','valuation_denominator_grant','independent_corroboration'))):
        raise ValueError('reported_observation_use_scope')
    facts=projection['facts'];comparisons=[];denials=[]
    for field in sorted({f['field'] for f in facts}):
        group=sorted((f for f in facts if f['field']==field),key=lambda f:f['period_end'])
        if field not in ('revenue','operating_income') or len(group)<2:continue
        current=group[-1]
        for prior in group[:-1]:
            try:
                distance=_quarter(current)-_quarter(prior)
                keys=('issuer','accession','raw_sha256','source_generation','lineage_group','basis','currency','scale')
                if (distance not in (1,4) or current['basis']!='CFS' or
                    any(current[k]!=prior[k] for k in keys) or
                    any(f.get('use')!=USE or not f.get('source_span') for f in (current,prior))):
                    raise ValueError('comparison_basis_or_lineage')
                a,b=Decimal(str(current['value'])),Decimal(str(prior['value']))
                if not a.is_finite() or not b.is_finite():raise ValueError('comparison_value')
                comparisons.append(dict(field=field,relation='PRIOR_QUARTER' if distance==1 else 'YEAR_OVER_YEAR',
                    reported_direction='HIGHER' if a>b else 'LOWER' if a<b else 'UNCHANGED',
                    current_period=[current['period_start'],current['period_end']],prior_period=[prior['period_start'],prior['period_end']],
                    occurrence_refs=[current['occurrence_id'],prior['occurrence_id']],source_sha256=current['raw_sha256'],
                    currency=current['currency'],scale=current['scale'],basis=current['basis'],lineage_group=current['lineage_group']))
            except (ValueError,KeyError):
                denials.append(dict(field=field,occurrence_refs=[current['occurrence_id'],prior['occurrence_id']],reason='COMPARISON_NOT_ADMITTED'))
    return dict(contract=CONTRACT,comparisons=comparisons,denials=denials,source_receipt_sha256=projection['receipt_sha256'],
        limitations=projection['limitations'],independent_corroboration=False,causality='UNKNOWN',recurrence='UNKNOWN',
        economic_direction_grant=False,strict_native=False,meaning=NO_DRIVER_MEANING,derived_growth_percentages=[])


def normalization_questions(packet):
    fields={e['field'] for e in packet['evidence'] if e['status'] in ('CURRENT_VALID','SOURCE_REFERENCE')}
    fields.update('financial.'+f['field'] for f in (packet.get('research_financial_reference') or {}).get('facts',[]))
    if not fields & {'financial.operating_income','financial.net_income'}:return []
    # Questions apply to all admitted earnings evidence, not growth thresholds.
    return [dict(id=key,question=question,status='NOT_DETERMINED_BY_ARITHMETIC') for key,question in (
        ('UNIT_BASIS_PERIOD','Confirm the original unit, consolidation basis and comparable reporting periods.'),
        ('RECURRING_COMPONENTS','What evidence distinguishes recurring earnings from one-off components? Absence of explanation proves neither.'),
        ('MARGIN_SUSTAINABILITY','What business evidence supports margin sustainability and appropriate peer comparability?'),
        ('FORWARD_EXPECTATIONS','Is an independently qualified forward earnings source available? Historical arithmetic does not supply FY1.'))]
