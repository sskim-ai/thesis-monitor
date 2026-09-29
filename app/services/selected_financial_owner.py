"""Hash-bound selection precedes completeness, quality, and source use."""
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.services.unified_snapshot_contract import digest


class SelectedFinancialOwnerEnvelope(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    contract: Literal['selected-financial-owner-v1'] = 'selected-financial-owner-v1'
    monitored_security: str
    issuer_identity: str
    owner_type: Literal['direct_sec', 'direct_opendart', 'issuer_business_bridge']
    selected_acquisition_sha256: str
    selected_projection_sha256: str
    field_completeness: dict
    source_completeness: dict
    bridge_receipt: dict | None
    selected_fact_ids: list[str]
    unselected_owner_states: list[dict]
    selection_reason: str
    envelope_sha256: str


def select(*, plan, acquisition, projection, facts, bridge=None, origin=None):
    selected = projection if origin is None else origin['projection']
    selected_acquisition = digest(acquisition) if origin is None else origin['input_hashes']['acquisition']
    if bridge is not None:
        if (origin is None or origin['status'] != 'PASS' or bridge['status'] != 'PASS'
                or not bridge['legal_issuer_id'] or not bridge['ISSUER_BUSINESS_EVIDENCE_ELIGIBLE']
                or bridge['SECURITY_PER_SHARE_BRIDGE_ELIGIBLE'] or bridge['SECURITY_VALUATION_BRIDGE_ELIGIBLE']
                or bridge['security_valuation_transfer'] or bridge['scope'] != 'issuer_business_only'
                or bridge['receipt_sha256'] != digest({k: v for k, v in bridge.items() if k != 'receipt_sha256'})):
            raise ValueError('selected_financial_bridge_incomplete')
        for fact in facts:
            binding = fact.get('issuer_business_bridge') or {}
            if (binding.get('bridge_receipt_sha256') != bridge['receipt_sha256']
                    or binding.get('source_result_sha256') != digest(origin)
                    or binding.get('security_valuation_transfer') is not False
                    or binding.get('scope') != 'issuer_business_only'):
                raise ValueError('selected_financial_fact_bridge_mismatch')
    elif origin is not None:
        raise ValueError('selected_financial_origin_without_bridge')
    # Native non-FPI projectors already own field eligibility via quality and
    # acquisition receipts; absence of an FPI-only receipt is not an absence claim.
    fields = selected.get('financial_field_completeness') or dict(
        owner='native_reported_field_quality', projection_sha256=digest(selected),
        partial_field_consumption_allowed=not selected.get('acquisition_denial_reconciliation', {}).get('effective_denials', []))
    source = selected.get('source_completeness') or dict(
        owner='native_reported_acquisition', acquisition_sha256=selected_acquisition,
        projection_sha256=digest(selected))
    data = dict(contract='selected-financial-owner-v1', monitored_security=plan['ticker'],
        issuer_identity=bridge['legal_issuer_id'] if bridge else plan['issuer'],
        owner_type='issuer_business_bridge' if bridge else 'direct_sec' if plan['provider']=='sec_edgar' else 'direct_opendart',
        selected_acquisition_sha256=selected_acquisition, selected_projection_sha256=digest(selected),
        field_completeness=fields, source_completeness=source, bridge_receipt=bridge,
        selected_fact_ids=sorted(f['fact_id'] for f in facts),
        unselected_owner_states=[dict(owner='direct_sec', state='UNSELECTED',
            reason='NOT_APPLICABLE_FOR_SELECTED_BUSINESS_OWNER', projection_sha256=digest(projection))] if bridge else [],
        selection_reason='VERIFIED_LEGAL_ISSUER_BUSINESS_BRIDGE' if bridge else 'DIRECT_REPORTED_OWNER')
    return SelectedFinancialOwnerEnvelope(**data, envelope_sha256=digest(data)).model_dump(mode='json')


def validate(envelope, *, projection, facts, bridge):
    value = SelectedFinancialOwnerEnvelope.model_validate(envelope).model_dump(mode='json')
    if (value['envelope_sha256'] != digest({k: v for k, v in value.items() if k != 'envelope_sha256'})
            or value['selected_projection_sha256'] != digest(projection)
            or value['selected_fact_ids'] != sorted(f['fact_id'] for f in facts)
            or value['bridge_receipt'] != bridge):
        raise ValueError('selected_financial_owner_binding_mismatch')
    return value
