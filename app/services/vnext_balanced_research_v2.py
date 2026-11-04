"""Default-OFF research differentiation, with no new source-use entitlement.

V1 remains unchanged semantically. Opposite-polarity evidence is not universally
required here; an issued Overall still needs original directional permission,
an anchor, distinct corroboration and the original ordinal calibration.
"""
from copy import deepcopy
import json
from typing import Literal

from app.services import vnext_balanced_research as v1

CONTRACT = 'RESEARCH_BALANCED_POLICY_V2'
OVERALL_CONTRACT = 'RESEARCH_OVERALL_V1'
ENABLED_BY_DEFAULT = False


class Overall(v1.Overall):
    policy: Literal['RESEARCH_OVERALL_V1']
    anchor_refs: list[str]
    corroborating_refs: list[str]
    independent_support_reason: str
    counterevidence_state: Literal['REVIEWED_WITHIN_ADMITTED_SET', 'MISSING_REQUIRED', 'NOT_ISSUED']
    counterevidence_refs: list[str]
    missing_required: list[str]


class Balanced(v1.Balanced):
    overall: Overall


class ResearchBalanced(v1.ResearchBalanced):
    contract: Literal['RESEARCH_BALANCED_POLICY_V2']
    balanced: Balanced


def schema():
    result = ResearchBalanced.model_json_schema()
    def walk(node):
        if isinstance(node, dict):
            if node.get('type') == 'object':
                node['required'] = list(node.get('properties', {}))
                node['additionalProperties'] = False
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)
    walk(result)
    return result


def _overall(overall, positive, negative, rows, value, packet):
    eligible = {k for k,r in rows.items() if r['eligible'] and r['layer'] in ('ECONOMIC_OBSERVATION','VALUATION_CONTEXT')}
    for field in ('anchor_refs','corroborating_refs','counterevidence_refs'):
        v1._refs(overall[field], eligible, 'research_overall_evidence_use_denied')
    v1._prose(overall['independent_support_reason'])
    for reason in overall['missing_required']:
        v1._prose(reason)
    if overall['stance'] == 'NOT_ISSUED':
        if overall['balance'] is not None:
            raise ValueError('balanced_unissued_overall_has_balance')
        return
    admitted = {e['ref']:e for e in packet['base']['evidence']}
    used = set(overall['refs']) | set(overall['anchor_refs']) | set(overall['corroborating_refs']) | set(overall['counterevidence_refs'])
    # Source flags are from the cold, backend-owned packet, never model output.
    if not used or any(admitted[r].get('direction_allowed') is not True for r in used):
        raise ValueError('research_overall_source_direction_not_authorized')
    if overall['missing_required'] or overall['counterevidence_state'] != 'REVIEWED_WITHIN_ADMITTED_SET':
        raise ValueError('research_overall_required_counterevidence_missing')
    if not set(overall['counterevidence_refs']) >= negative:
        raise ValueError('research_overall_admitted_adverse_evidence_omitted')
    anchor = set(overall['anchor_refs'])
    corroboration = set(overall['corroborating_refs'])
    side = positive if overall['stance']=='BUY' else negative if overall['stance']=='SELL' else positive|negative
    material = {r for s in ('positive','negative') for d in value['economic_drivers_'+s]
                if d['importance'] in ('MATERIAL','DECISIVE') for r in d['refs']}
    if not anchor or not anchor <= side & material:
        raise ValueError('research_overall_material_anchor_missing')
    if not corroboration or not (anchor|corroboration) <= set(overall['refs']):
        raise ValueError('research_overall_distinct_support_missing')
    if {rows[r]['lineage_group'] for r in anchor} & {rows[r]['lineage_group'] for r in corroboration}:
        raise ValueError('research_overall_correlated_support')
    # A different source category is necessary in some cases, never sufficient:
    # the model must explain its distinct economic contribution under calibration.
    if overall['balance'] is None or v1.v3.decision_from_directional_balance(
            v1.v3.DirectionalBalance.model_validate(overall['balance'])) != overall['stance']:
        raise ValueError('balanced_overall_ordinal_mismatch')
    b = value['balanced']
    if overall['stance']=='BUY' and (b['active_material_risk_refs'] or b['business_quality_denials'] or b['confidence_veto_refs']):
        raise ValueError('research_overall_positive_required_support_veto')


def validate_and_render(value, packet, *, registry, **validation_inputs):
    checked = v1._validate_and_render(value,packet,registry=registry,output_model=ResearchBalanced,
        contract=CONTRACT,overall_check=_overall,**validation_inputs)
    if not (value['balanced']['business_positive_refs'] or value['balanced']['business_negative_refs']):
        if value['balanced']['newbuyer_confidence'] != 'NOT_SEPARATELY_ISSUED':
            raise ValueError('balanced_unissued_newbuyer_confidence')
        checked['balanced'].update(newbuyer_fundamental='NOT_ISSUED',
            newbuyer_reason='NO_ELIGIBLE_ECONOMIC_BASIS', newbuyer_reason_refs=[])
        checked['rendered']['balanced'] = deepcopy(checked['balanced'])
    return checked


def prompt(packet, stage, *, knowledge, registry, prior=None):
    # Original prompts/validators remain exact. This suffix supersedes only the
    # V1 symmetric-Overall rule and schema, not original source-use restrictions.
    text = v1.prompt(packet,stage,knowledge=knowledge,registry=registry,prior=prior)
    rights = {e['ref']:e.get('direction_allowed') is True for e in packet['base']['evidence']}
    return text + '''
VERSIONED RESEARCH OVERRIDE: RESEARCH_BALANCED_POLICY_V2 / RESEARCH_OVERALL_V1.
Return the V2 schema. Preserve original v4 decision=null, balance=null,
INSUFFICIENT_EVIDENCE and UNPROVEN. This is not Strict Core, B2 or readiness.
Contrary evidence is not a universal prerequisite for any Overall view. Use a
material anchor and distinct economic corroboration under the original ordinal
calibration, not reference counts or source-category independence alone.
Every Overall reference must have original directional permission in the map
below. False/unknown permission cannot be renewed by this policy or by your
interpretation. Keep Overall NOT_ISSUED if unavailable, with null balance and
NOT_SEPARATELY_ISSUED confidence. No mapping NewBuyer/Holder/Timing into Overall.
For issued Overall, cite material anchor_refs and corroborating_refs included
in overall.refs, explain independent_support_reason, review all admitted adverse
economic evidence, and identify missing_required. REVIEWED_WITHIN_ADMITTED_SET
means only the admitted source set, never a claim of complete market research.
Missing required support blocks issuance, but absence of contrary facts is not
itself negative evidence. For an unissued axis, lists may be empty and explain
the exact limitation without inventing a counterevidence search.
No absolute fair-value target is required for contextual valuation. A raw low
ratio is not cheapness; dates, financial/share basis and expectations matter.
Do not invent price targets, peers, causes, recurring profit or active risks.
Fundamental ATTRACTIVE may coexist with WAIT_FOR_ZONE. Historical adverse facts
are not current structural risks. Holder remains VIRTUAL; no personal holdings.
Use NOT_SEPARATELY_ISSUED for every UNRESOLVED or NOT_ISSUED axis. No target
label counts. All prose/number/source/quality rules of the original remain.
ORIGINAL DIRECTIONAL PERMISSIONS (data, not instructions):
''' + json.dumps(rights,sort_keys=True)


def render(checked):
    if checked.get('balanced_contract') != CONTRACT:
        raise ValueError('research_v2_render_scope')
    projected=deepcopy(checked)
    projected['balanced_contract']=v1.CONTRACT
    # Reuse presentation only, never reissue V1 ownership or modify saved output.
    text=v1.render(projected)
    return text.replace(v1.CONTRACT,CONTRACT,1)
