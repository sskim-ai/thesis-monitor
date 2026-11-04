"""Research-only signals and investor perspectives over unchanged v3 safeguards."""
import copy
import json
from typing import Literal
from app.services import vnext_research_v3 as v3
from app.services.vnext_research_store import digest

CONTRACT = 'vnext-economic-timing-research-v4'
MODEL, EFFORT = v3.MODEL, v3.EFFORT
EXTRA = ('decision_scope', 'economic_evidence_signal', 'valuation_judgment',
         'valuation_evidence_refs', 'market_or_price_timing', 'newbuyer_stance',
         'holder_stance', 'holdings_included', 'user_thesis_included',
         'counter_hypothesis_refs', 'counter_hypothesis_outcome')


class ResearchV4(v3.ResearchV3):
    contract: Literal['vnext-economic-timing-research-v4']
    decision_scope: Literal['PROVISIONAL_RESEARCH_NOT_CORE']
    economic_evidence_signal: Literal['LIMITED_POSITIVE', 'LIMITED_NEGATIVE', 'MIXED', 'NO_ELIGIBLE_ECONOMIC_EVIDENCE']
    valuation_judgment: Literal['UNPROVEN', 'CHEAP', 'EXPENSIVE']
    valuation_evidence_refs: list[str]
    market_or_price_timing: Literal['FAVORABLE', 'AVOID', 'WATCH', 'UNKNOWN']
    newbuyer_stance: Literal['CONDITIONAL_INTEREST', 'WAIT_FOR_TRIGGER', 'AVOID_ON_EVIDENCE', 'INSUFFICIENT']
    holder_stance: Literal['THESIS_HOLD_CONDITIONAL', 'RISK_REVIEW', 'TRIM_CONDITIONAL', 'INSUFFICIENT']
    holdings_included: bool
    user_thesis_included: bool
    counter_hypothesis_refs: list[str]
    counter_hypothesis_outcome: Literal['SUPPORTED', 'CONTRADICTED', 'UNRESOLVED']


def schema():
    value = ResearchV4.model_json_schema()
    def required(node):
        if isinstance(node, dict):
            if node.get('type') == 'object':
                node['required'] = list(node.get('properties', {}))
                node['additionalProperties'] = False
            for child in node.values():
                required(child)
        elif isinstance(node, list):
            for child in node:
                required(child)
    required(value)
    return value


def validate_and_render(value, packet, *, price_source_bytes=None):
    ResearchV4.model_validate(value)
    if (value['holdings_included'] or value['user_thesis_included'] or
            packet.get('holdings_included') is not False or packet.get('user_thesis_included') is not False):
        raise ValueError('private_investor_basis_not_admitted')
    # This consumer has no strict Core ownership capability. Preserve that boundary
    # even when a useful one-sided research observation is possible.
    if value['decision'] is not None or value['balance'] is not None or value['disposition'] != 'INSUFFICIENT_EVIDENCE':
        raise ValueError('strict_core_judgment_not_issued')
    sides = [bool(value['economic_drivers_'+s]) for s in ('positive', 'negative')]
    expected = {(True, False): 'LIMITED_POSITIVE', (False, True): 'LIMITED_NEGATIVE',
                (True, True): 'MIXED', (False, False): 'NO_ELIGIBLE_ECONOMIC_EVIDENCE'}[tuple(sides)]
    if value['economic_evidence_signal'] != expected:
        raise ValueError('research_signal_driver_mismatch')
    contracts = v3.evidence_contract(packet)
    for ref in value['valuation_evidence_refs']:
        if ref not in contracts or not contracts[ref]['eligible'] or contracts[ref]['layer'] != 'VALUATION_CONTEXT':
            raise ValueError('valuation_reference_not_eligible')
    # Atomic multiples and reported amounts do not issue a normalized-profit or
    # fair-value benchmark. No such authority is carried by this input contract.
    if value['valuation_judgment'] != 'UNPROVEN':
        raise ValueError('qualified_profit_and_value_benchmark_missing')
    for ref in value['counter_hypothesis_refs']:
        if ref not in contracts or not contracts[ref]['eligible']:
            raise ValueError('counter_hypothesis_ref_not_eligible')
    if value['counter_hypothesis_outcome'] != 'UNRESOLVED' and not value['counter_hypothesis_refs']:
        raise ValueError('counter_hypothesis_requires_evidence')
    timing = bool(value['timing_support'] or value['timing_risks'])
    if value['market_or_price_timing'] in ('FAVORABLE', 'AVOID') and not timing:
        raise ValueError('timing_signal_requires_price_evidence')
    if value['newbuyer_stance'] == 'CONDITIONAL_INTEREST' and not sides[0]:
        raise ValueError('conditional_interest_requires_economic_support')
    if value['newbuyer_stance'] == 'AVOID_ON_EVIDENCE' and not (sides[1] or value['timing_risks']):
        raise ValueError('avoid_requires_adverse_evidence')
    if value['holder_stance'] == 'THESIS_HOLD_CONDITIONAL' and not sides[0]:
        raise ValueError('conditional_thesis_requires_economic_support')
    if value['holder_stance'] == 'TRIM_CONDITIONAL' and not (sides[1] or value['timing_risks']):
        raise ValueError('trim_requires_adverse_evidence')
    old = {k: copy.deepcopy(v) for k, v in value.items() if k not in EXTRA}
    old['contract'] = v3.CONTRACT
    checked = v3.validate_and_render(old, packet, price_source_bytes=price_source_bytes)
    checked['rendered'].update({k: copy.deepcopy(value[k]) for k in EXTRA})
    checked['rendered']['contract'] = CONTRACT
    checked.update(contract=CONTRACT, draft_sha256=digest(value),
                   strict_directional_authority=False, personal_holder_advice=False)
    return checked


def prompt(packet, stage, *, knowledge, prior=None):
    # Reuse exact source, ordinal, numeric and original chart policies.
    base = v3.prompt(packet, stage, knowledge=knowledge, prior=prior)
    policy = '''VERSION FOUR OVERRIDE FOR THIS RESEARCH CONTRACT ONLY:
The complete strict economic judgment remains INSUFFICIENT_EVIDENCE with decision=null
and balance=null because this route has no Core acceptance capability. This is NOT an
instruction to erase an eligible one-sided economic observation. Set the separate
economic_evidence_signal from your source-supported positive/negative drivers:
positive only LIMITED_POSITIVE, negative only LIMITED_NEGATIVE, both MIXED, neither
NO_ELIGIBLE_ECONOMIC_EVIDENCE. These describe limited evidence, not BUY/SELL or
recurrence/causality authority. No desired ticker label, magnitude threshold or forced
counterevidence. Same-filing revenue and operating income remain one lineage.
decision_scope=PROVISIONAL_RESEARCH_NOT_CORE. holdings_included=false and
user_thesis_included=false: Holder is a hypothetical role, never personal advice.
Provide a useful concise provisional_business_signal with exactly the strongest
supported interpretation and its key limit. State what evidence would change it.
Use the explicit market_or_price_timing enum independently of corporate economics.
Markets may describe divergence or tech-led weakness from eligible price observations;
do not infer macro causes or company deterioration. UNKNOWN/MISSING is not negative.
NewBuyer CONDITIONAL_INTEREST requires supported economic upside plus a falsifiable
condition, not an order. WAIT_FOR_TRIGGER can express a dated price confirmation or
missing valuation requirement. AVOID_ON_EVIDENCE needs actual adverse evidence.
Holder THESIS_HOLD_CONDITIONAL is hypothetical and needs economic support;
RISK_REVIEW is allowed for timing/evidence limits without inventing a personal thesis.
TRIM_CONDITIONAL needs explicit actual risk and conditional language, not missing data.
Valuation_judgment=UNPROVEN in this packet contract: atomic provider multiples lack a
qualified normalized-profit/fair-value benchmark. Discuss eligible multiples in
valuation_expectations and valuation_evidence_refs, not cheap/expensive assertions.
Use counterevidence to state ONE serious counter-hypothesis and evidence that would
resolve it. Record counter_hypothesis_refs and outcome; missing causal evidence means
UNRESOLVED, not supported or false. Adjudication must test it against the same packet
and explain retained/revised reasoning in review_changes, not merely copy wording.
All prose/price numeric occurrences retain the original exact placeholder contract.
No literal numeric digits in prose; enum names/field refs are not prose.
The earlier v3 wording about two-sided balance applies only to the complete judgment,
not to this new evidence signal. Return v4 schema JSON only.'''
    return policy + '\n' + base
