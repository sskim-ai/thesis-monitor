"""Producer-issued selection precedes completeness, quality, and source use.

V1 wire schemas remain unchanged, but public hashes alone cannot issue or restore
ownership. Original sealed-input replay and selection must occur in this trusted
process. V2 additionally requires the live current parent; neither registry is a
durable store or an authorization to change the original evidence policy.
"""
from typing import Literal
from copy import deepcopy
from weakref import WeakKeyDictionary

from pydantic import BaseModel, ConfigDict

from app.services.unified_snapshot_contract import digest

_CURRENT_SELECTIONS = WeakKeyDictionary()
_LEGACY_SELECTIONS = {}


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


class CurrentSelectedFinancialOwnerEnvelope(SelectedFinancialOwnerEnvelope):
    contract: Literal['selected-financial-owner-v2'] = 'selected-financial-owner-v2'
    current_parent: dict
    current_purpose_receipt_sha256: str | None


def _current(parent, intake, projection, plan=None):
    from app.services.current_financial_purpose_intake import resolve_parent, require_projection
    purpose = None
    if projection.get('current_purpose_intake') is not None or intake is not None:
        purpose = require_projection(intake, projection)
        if parent is None:
            raise ValueError('selected_financial_current_parent_required')
    receipt = resolve_parent(parent, plan=plan) if parent is not None else None
    if purpose is not None and purpose['parent'] != receipt:
        raise ValueError('selected_financial_current_parent_mismatch')
    return receipt, purpose


def _legacy_replay(*, plan, acquisition, projection, facts, bridge, origin, issuer_inputs):
    from app.services.bounded_financial_projection import replay_original_projection
    from app.services.current_financial_purpose_intake import require_legacy_scope

    plan, acquisition, projection, facts, bridge, origin, issuer_inputs = deepcopy(
        (plan, acquisition, projection, facts, bridge, origin, issuer_inputs))

    def replay():
        require_legacy_scope(plan=plan, projection=projection, facts=facts)
        direct = replay_original_projection(plan=plan, acquisition=acquisition, projection=projection)
        if bridge is None:
            if origin is not None or issuer_inputs is not None or direct != facts:
                raise ValueError('selected_financial_original_comparisons_mismatch')
            return
        if issuer_inputs is None:
            raise ValueError('selected_financial_original_issuer_inputs_required')
        if direct:
            raise ValueError('issuer_business_native_comparison_already_owned')
        from app.services.bounded_financial_stock_owner import _issuer_business_facts
        expected_bridge, expected_facts, expected_origin = _issuer_business_facts(plan, issuer_inputs)
        if (expected_bridge != bridge or expected_facts != facts or expected_origin != origin):
            raise ValueError('selected_financial_original_issuer_replay_mismatch')
        source = issuer_inputs['source_inputs']
        require_legacy_scope(plan=source['plan'], projection=expected_origin['projection'], facts=expected_facts)
        replay_original_projection(plan=source['plan'], acquisition=source['acquisition'],
                                   projection=expected_origin['projection'])

    replay()
    return replay


def select(*, plan, acquisition, projection, facts, bridge=None, origin=None, legacy_issuer_inputs=None,
           current_financial_parent=None, current_purpose_intake=None):
    parent, purpose = _current(current_financial_parent, current_purpose_intake, projection, plan)
    legacy_replay = None
    if parent is not None:
        from app.services.current_financial_purpose_intake import require_current_projection
        if bridge is not None or origin is not None:
            raise ValueError('current_selected_bridge_requires_separate_source_parent')
        require_current_projection(current_financial_parent, projection, facts, plan=plan, acquisition=acquisition)
    if (projection.get('purpose_reconciliation') is not None
            or projection.get('source_completeness', {}).get('current_generation_eligible') is False
            or (origin is not None and (origin.get('projection', {}).get('purpose_reconciliation') is not None
                or origin.get('projection', {}).get('source_completeness', {}).get('current_generation_eligible') is False))):
        raise ValueError('selected_financial_auxiliary_purpose_current_use_not_authorized')
    if bridge is None and plan.get('provider') not in {'sec_edgar', 'opendart'}:
        raise ValueError('selected_financial_direct_provider_unsupported')
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
    if parent is None:
        legacy_replay = _legacy_replay(plan=plan, acquisition=acquisition, projection=projection,
            facts=facts, bridge=bridge, origin=origin, issuer_inputs=legacy_issuer_inputs)
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
    cls = SelectedFinancialOwnerEnvelope
    if parent is not None:
        cls = CurrentSelectedFinancialOwnerEnvelope
        data.update(contract='selected-financial-owner-v2', current_parent=parent,
                    current_purpose_receipt_sha256=purpose['receipt_sha256'] if purpose else None)
    result = cls(**data, envelope_sha256=digest(data)).model_dump(mode='json')
    if parent is not None:
        _CURRENT_SELECTIONS.setdefault(current_financial_parent, {})[result['envelope_sha256']] = deepcopy(result)
    else:
        _LEGACY_SELECTIONS[result['envelope_sha256']] = (
            deepcopy(result), deepcopy(selected), deepcopy(facts), deepcopy(bridge), legacy_replay)
    return result


def validate(envelope, *, projection, facts, bridge, current_financial_parent=None, current_purpose_intake=None):
    parent, purpose = _current(current_financial_parent, current_purpose_intake, projection)
    if parent is None:
        from app.services.current_financial_purpose_intake import require_legacy_scope
        require_legacy_scope(projection=projection, facts=facts)
    if parent is not None:
        from app.services.current_financial_purpose_intake import require_current_projection
        require_current_projection(current_financial_parent, projection, facts)
    if (projection.get('purpose_reconciliation') is not None
            or projection.get('source_completeness', {}).get('current_generation_eligible') is False):
        raise ValueError('selected_financial_auxiliary_purpose_current_use_not_authorized')
    is_current = envelope.get('contract') == 'selected-financial-owner-v2'
    cls = CurrentSelectedFinancialOwnerEnvelope if is_current else SelectedFinancialOwnerEnvelope
    value = cls.model_validate(envelope).model_dump(mode='json')
    if (is_current != (parent is not None) or is_current and (
            value['current_parent'] != parent or value['current_purpose_receipt_sha256'] !=
            (purpose['receipt_sha256'] if purpose else None))):
        raise ValueError('selected_financial_current_owner_binding_mismatch')
    if is_current and _CURRENT_SELECTIONS.get(current_financial_parent, {}).get(value['envelope_sha256']) != value:
        raise ValueError('selected_financial_unissued_or_changed_current_envelope')
    if (value['envelope_sha256'] != digest({k: v for k, v in value.items() if k != 'envelope_sha256'})
            or value['selected_projection_sha256'] != digest(projection)
            or value['selected_fact_ids'] != sorted(f['fact_id'] for f in facts)
            or value['bridge_receipt'] != bridge):
        raise ValueError('selected_financial_owner_binding_mismatch')
    if not is_current:
        issued = _LEGACY_SELECTIONS.get(value['envelope_sha256'])
        if issued is None or issued[:4] != (value, projection, facts, bridge):
            raise ValueError('selected_financial_unissued_or_changed_legacy_envelope')
        issued[4]()
    return value
