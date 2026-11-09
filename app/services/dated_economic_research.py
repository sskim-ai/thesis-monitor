"""Dated research consumption, not a legacy Stage, owner or direction issuer."""
from copy import deepcopy
from decimal import Decimal, InvalidOperation
import json
import re

from app.services.vnext_composite_research import numeric_catalog
from app.services.expectation_valuation_interaction_service import (
    ExpectationValuationLineage, classify_expectation_valuation_interaction,
)

CONTRACT = 'C22D_DATED_ECONOMIC_RESEARCH_VIEW'


def meaningful(value):
    if isinstance(value,str):
        text=value.strip()
        if text.lower() in {'','null','none','n/a','unknown','not_verified'}:return False
        try:return meaningful(json.loads(text))
        except (ValueError,TypeError):return True
    if isinstance(value,dict):return any(meaningful(v) for v in value.values())
    if isinstance(value,(list,tuple)):return any(meaningful(v) for v in value)
    return value is not None


def _finite(value):
    if value is None or isinstance(value,bool):return False
    try:return Decimal(str(value)).is_finite()
    except (InvalidOperation,ValueError,TypeError):return False


def _sha(value):
    return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None


def valuation_locator(fact):
    # A citation locator into existing material, never a legacy source_ref/grant.
    return json.dumps(dict(receipt=fact.get('source_receipt_sha256'),field=fact.get('provider_field') or fact.get('metric')),
        sort_keys=True,separators=(',',':'))


def consume_research(packet,*,input_sha256,extra_valuation=(),public_context=()):
    if packet.get('contract')!='C22C_EXISTING_SOURCE_DATED_INVESTMENT_INPUT' or not _sha(input_sha256):
        raise ValueError('dated_research_input_contract_or_hash')
    ticker=packet['ticker'];technical=deepcopy(packet['technical'])
    original=deepcopy(packet['economic']['evidence']);observations=[];excluded=[]
    for row in original:
        data=row.get('data',{});fields=data.get('fields',{})
        if fields.get('source_ticker') not in (None,ticker):raise ValueError('research_financial_identity_mismatch')
        admitted=(row.get('status') in {'SOURCE_REFERENCE','CURRENT_VALID'} and _sha(row.get('source_sha'))
            and bool(row.get('ref')) and bool(row.get('lineage_group')))
        compare=(admitted and data.get('interpretation_eligible') is True
            and fields.get('comparison_eligible') is not False and not fields.get('observation_only')
            and all(_finite(fields.get(key)) for key in ('current_value','prior_comparable_value','delta'))
            and all(fields.get(k) for k in ('currency','period_start','period_end','period_type',
                'prior_period_start','prior_period_end','statement_basis','source_receipt')))
        if not admitted:excluded.append(dict(original_ref=row.get('ref'),reason='SOURCE_STATUS_OR_PROVENANCE_NOT_ADMITTED'))
        role='QUANTITATIVE_COMPARISON' if compare else 'DATED_OBSERVATION_ONLY' if admitted else 'EXCLUDED'
        observations.append(dict(original_ref=row.get('ref'),source_ref=row.get('source_ref'),field=row['field'],
            source_sha=row.get('source_sha'),lineage_group=row.get('lineage_group'),source_scope=deepcopy(row.get('scope')),
            source_receipt=fields.get('source_receipt'),source_cutoff=fields.get('source_cutoff'),capsule_as_of=packet['economic']['as_of'],
            original_fields=deepcopy(fields),original_quality={k:deepcopy(v) for k,v in data.items() if k!='fields'},
            original_status=row.get('status'),allowed_use=row.get('allowed_use'),role=role,
            analytic_observation=({k:deepcopy(fields.get(k)) for k in ('current_value','prior_comparable_value','delta','growth_pct','direction',
                'currency','unit','period_start','period_end','period_type','prior_period_start','prior_period_end','statement_basis',
                'fiscal_comparability','anomaly_cautions','limitations','recurrence_verified')} if compare else None),
            verified_mechanism=fields.get('mechanism_verified') is True,
            structural_risk_verified=fields.get('structural_risk_verified') is True,
            strict_owner_issued=fields.get('strict_owner_issued') is True))
    comparisons=[o for o in observations if o['role']=='QUANTITATIVE_COMPARISON']
    placeholder=[];retained=[]
    for row in technical.get('evidence',[]):
        if not meaningful(row.get('statement')):
            placeholder.append(dict(original_ref=row.get('ref_id'),category=row.get('category'),reason='EMPTY_PLACEHOLDER_NOT_EVIDENCE'))
        else:retained.append(row)
    technical['evidence']=retained
    # Source values, native period quality, missing periods and dated SR remain intact.
    native=technical.get('technical_context_quality',{}).get('provider_native',{})
    if native.get('provider_code')!=ticker or native.get('current_price_qualified') is not False:
        raise ValueError('research_technical_identity_or_scope')
    available=[p for p in native.get('periods',{}).values() if p.get('status')=='AVAILABLE']
    sr=deepcopy(packet.get('dated_price_structure',{}))
    valuations=[];unavailable=[];seen=set()
    for source in [*packet.get('prior_approved_valuation_facts',[]),*extra_valuation]:
        fact=deepcopy(source);symbol=fact.get('ticker') or fact.get('requested_security_id')
        if symbol!=ticker:raise ValueError('research_valuation_identity_mismatch')
        value=fact.get('exact_value',fact.get('value'))
        usable=(fact.get('display_eligible') is True and _finite(value) and _sha(fact.get('raw_sha256'))
            and _sha(fact.get('source_receipt_sha256')) and fact.get('retrieval_timestamp'))
        if not usable:
            unavailable.append(dict(metric=fact.get('metric'),value=None,state=fact.get('state','UNAVAILABLE'),original_fact=fact));continue
        key=(fact.get('metric'),fact['raw_sha256'])
        if key in seen:continue
        seen.add(key)
        valuations.append(dict(metric=fact['metric'],value=value,source_locator=valuation_locator(fact),original_fact=fact,
            current_price_grant=False,standalone_direction_grant=False))
    contexts=[]
    for row in public_context:
        if (row.get('ticker')!=ticker or not meaningful(row.get('content')) or not row.get('source_ref')
                or not _sha(row.get('source_sha256')) or not row.get('as_of')):continue
        contexts.append(deepcopy(row))
    forecast=[v for v in valuations if v['metric']=='FY1_EPS']
    expectations=[r for r in contexts if r.get('category')=='expectations']
    expectation_refs=[r['source_ref'] for r in expectations]+[v['source_locator'] for v in forecast]
    valuation_refs=[v['source_locator'] for v in valuations]
    shared=[]
    for v in valuations:
        for eps in forecast:
            if v['metric'] in {'FPER','FORWARD_PE'} and v['original_fact']['raw_sha256']==eps['original_fact']['raw_sha256']:
                shared.append(eps['source_locator'])
    independent=[r['source_ref'] for r in expectations if r.get('independent_source_verified') is True]
    if expectation_refs and valuation_refs:
        interaction=classify_expectation_valuation_interaction(ticker=ticker,lineage=ExpectationValuationLineage(
            expectation_refs=tuple(dict.fromkeys(expectation_refs)),valuation_refs=tuple(dict.fromkeys(valuation_refs)),
            independent_expectation_basis_refs=tuple(dict.fromkeys(independent)),shared_underlying_refs=tuple(dict.fromkeys(shared)))).model_dump(mode='json')
    else:interaction=dict(classification='UNKNOWN',reason='NO_SOURCED_MARKET_EXPECTATION_NO_DOUBLE_COUNT',independent_anchor_count=0)
    comparison_refs=[o['original_ref'] for o in comparisons]
    context_refs=[o['original_ref'] for o in observations if o['role']=='DATED_OBSERVATION_ONLY']
    questions=[dict(question='Explain the reported change only within its original period and currency. Separate demand, mix, pricing, cost or one-off hypotheses from verified causes; absent cause remains UNKNOWN.',evidence_refs=comparison_refs),
        dict(question='Check recurrence, cash conversion and falsifying future observations. Do not infer EPS, margins, annualized values or direction from these comparisons.',evidence_refs=comparison_refs+context_refs)] if comparisons else []
    risk_questions=[dict(question='Assess possible balance-sheet/cash-flow/earnings-quality exposure from the dated observations. A potential exposure is not an occurred active risk; identify missing evidence.',evidence_refs=context_refs or comparison_refs)]
    expectation_status='CONDITIONAL' if expectations or forecast else 'UNVERIFIED'
    business_context=[c for c in contexts if c.get('category')=='business_context']
    risk_context=[c for c in contexts if c.get('category')=='risk']
    dated_ready=bool(comparisons and available and sr.get('SR') and _sha(packet.get('technical_source_sha256')))
    reasoning_ready=bool(dated_ready and questions and risk_questions and any(o['source_receipt'] for o in comparisons))
    return dict(contract=CONTRACT,ticker=ticker,market=native.get('market'),input_provenance=dict(source_input_sha256=input_sha256,
        economic_original_source_sha256=packet['economic']['original_source_sha256'],technical_source_sha256=packet['technical_source_sha256']),
        as_of=packet['economic']['as_of'],issuer_ids=sorted({str(o['original_fields']['issuer_id']) for o in observations if o['original_fields'].get('issuer_id')}),
        financial_observations=observations,financial_numeric_catalog=numeric_catalog({'evidence':[r for r in original if r.get('status') in {'SOURCE_REFERENCE','CURRENT_VALID'}]}),
        business_change_candidates=[dict(evidence_ref=o['original_ref'],field=o['field'],source_fields=o['analytic_observation'],
            role='OBSERVED_REPORTED_CHANGE_NOT_VERIFIED_CAUSE',mechanism_verified=o['verified_mechanism']) for o in comparisons],
        economic_driver_count=len(comparisons),verified_mechanism_count=sum(o['verified_mechanism'] for o in comparisons),
        business_mechanism=dict(status='CONDITIONAL',source_context=business_context,analytic_questions=questions),
        market_expectations=dict(status=expectation_status,source_evidence=expectations,analyst_forecast_references=forecast,
            interpretation='Analyst EPS/atomic forward ratio is not independently proven price-implied growth or company guidance'),
        structural_risk=dict(status='SOURCED_CONTEXT_REQUIRES_INTERPRETATION' if risk_context else 'CONDITIONAL',source_evidence=risk_context,
            questions=risk_questions,occurred_risk_assertion=None),expectation_valuation_interaction=interaction,
        valuation=valuations,valuation_unavailable=unavailable,technical=technical,dated_price_structure=sr,
        excluded_placeholders=placeholder,excluded_financial=excluded,
        DATED_RESEARCH_EVIDENCE_READY=dated_ready,ECONOMIC_REASONING_INPUT_READY=reasoning_ready,
        reasoning_readiness_scope='CONDITIONAL_BLIND_ANALYSIS_INPUT_NOT_VERIFIED_BUSINESS_MECHANISM_OR_STANCE',
        STRICT_NATIVE_STAGE_READY=False,legacy_MODEL_INPUT_VALID=packet.get('MODEL_INPUT_VALID'),
        no_current_price_grant=True,model_executed=False,NO_SEND=True,
        model_instruction='BLIND input only. Cite original references; distinguish fact, causal hypothesis, uncertainty and falsification. Preserve different periods/limits. No mechanically generated BUY/WAIT/AVOID. No independent corroboration from shared lineage. No legacy Stage/Owner approval is implied.')
