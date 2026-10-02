"""Declared issuer-only source, without a stock packet or market-price baseline."""
from datetime import datetime
from typing import Literal

from pydantic import Field

from app.services.unified_snapshot_contract import ContractModel, digest


class AuxiliaryIssuerDependency(ContractModel):
    contract: Literal['auxiliary-issuer-only-v1'] = 'auxiliary-issuer-only-v1'
    role: Literal['AUXILIARY_ISSUER_ONLY'] = 'AUXILIARY_ISSUER_ONLY'
    primary_subject: Literal['SKHY'] = 'SKHY'
    auxiliary_issuer_security: Literal['000660'] = '000660'
    purpose: Literal['SHARED_ISSUER_BUSINESS_FINANCIAL_EVIDENCE'] = 'SHARED_ISSUER_BUSINESS_FINANCIAL_EVIDENCE'
    run_id: str
    cutoff: datetime
    source_plan_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    official_identity_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    user_message_eligible: Literal[False] = False
    model_subject_eligible: Literal[False] = False
    valuation_eligible: Literal[False] = False
    technical_eligible: Literal[False] = False


def assemble_issuer(*, plan, acquisition, directory, receipts, dependency,
                    target_plan, field_semantics=True):
    from app.services.bounded_financial_projection import project
    from app.services.bounded_financial_stock_owner import reported_comparisons

    dep = AuxiliaryIssuerDependency.model_validate(dependency)
    cutoff = dep.cutoff
    if (cutoff.utcoffset() is None or plan['ticker'] != dep.auxiliary_issuer_security
            or target_plan['ticker'] != dep.primary_subject or plan['market'] != 'kr'
            or target_plan['market'] != 'us' or plan['provider'] != 'opendart'
            or plan['run_id'] != dep.run_id or target_plan['run_id'] != dep.run_id
            or datetime.fromisoformat(plan['cutoff']) != cutoff
            or datetime.fromisoformat(target_plan['cutoff']) != cutoff
            or digest(plan) != dep.source_plan_sha256
            or digest(plan['security']) != plan['identity_sha256']):
        raise ValueError('auxiliary_issuer_generation_identity_mismatch')
    if not receipts:
        raise ValueError('auxiliary_issuer_source_receipts_required')
    for row in receipts:
        start, end = (datetime.fromisoformat(row[k]) for k in ('started_at','finished_at'))
        if start.utcoffset() is None or end.utcoffset() is None or not cutoff <= start <= end:
            raise ValueError('auxiliary_issuer_prior_generation_receipt')
    projection = project(plan, acquisition, directory, receipts, field_semantics=field_semantics)
    facts, denied = reported_comparisons(plan, projection)
    denials = projection.get('acquisition_denial_reconciliation', {}).get('effective_denials', acquisition.get('denials', []))
    complete = bool(facts) and not denied and not denials
    return dict(contract='auxiliary-issuer-financial-owner-v1', role=dep.role,
        status='PASS' if complete else 'BLOCKED', dependency=dep.model_dump(mode='json'),
        ticker=dep.auxiliary_issuer_security, primary_subject=dep.primary_subject,
        projection=projection, comparative_facts=facts, comparison_denials=denied,
        acquisition_denials=denials,
        input_hashes=dict(plan=digest(plan),acquisition=digest(acquisition),receipts=digest(receipts)),
        user_message_eligible=False,model_subject_eligible=False,valuation_eligible=False,technical_eligible=False)
