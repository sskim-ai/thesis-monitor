"""Opt-in offline research views. No Owner issuance, inference or production wiring."""
from copy import deepcopy
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.services.dated_research_model import encoded, digest, reference_catalog, build_prompt, _Citation
from app.services.kr_financial_lineage_service import opendart_field_lineage

CONTRACT = 'DATED_RESEARCH_REVIEW_V2_OFFLINE'
UNKNOWN = 'UNKNOWN'
Mode = Literal['POINT_IN_TIME', 'RETROSPECTIVE_DATED_RESEARCH']


def number(value):
    if value is None or isinstance(value, bool):
        raise ValueError('finite_number_required')
    try:
        n = Decimal(str(value).replace(',', ''))
        if not n.is_finite():
            raise ValueError('finite_number_required')
        return n
    except InvalidOperation as exc:
        raise ValueError('finite_number_required') from exc


def instant(value):
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.tzinfo is None:
        raise ValueError('timezone_required')
    return d


def temporal_record(fact, *, cutoff, prepared_at, mode, available_at_proven=None):
    if mode not in ('POINT_IN_TIME', 'RETROSPECTIVE_DATED_RESEARCH'):
        raise ValueError('research_mode_unknown')
    cut, prepared = instant(cutoff), instant(prepared_at)
    retrieved = instant(fact['retrieval_timestamp'])
    available = instant(available_at_proven) if available_at_proven else None
    if prepared < retrieved or (available and available > retrieved):
        raise ValueError('temporal_metadata_conflict')
    pit = retrieved <= cut and available is not None and available <= cut
    eligible = pit if mode == 'POINT_IN_TIME' else True
    provenance = {}
    if isinstance(fact.get('basis'), str) and fact['basis'].startswith('{'):
        provenance = json.loads(fact['basis'])
    return dict(research_mode=mode, historical_information_cutoff=cutoff,
        research_prepared_at=prepared_at, retrieved_at=fact['retrieval_timestamp'],
        metric_period_end=fact.get('metric_asof') or fact.get('underlying_denominator_period'),
        issuer_estimate_vintage=fact.get('estimate_vintage') or fact.get('issuer_estimate_vintage'),
        reference_price_as_of=fact.get('reference_price_as_of') or fact.get('price_as_of') or provenance.get('price', {}).get('session'),
        reference_price_basis=fact.get('price_basis') or provenance.get('price', {}).get('basis'), available_at_proven=available_at_proven,
        direction_anchor_temporally_eligible=eligible, original_owner_grants_unchanged=True,
        caveat=('POST_CUTOFF_OR_AVAILABILITY_UNPROVEN_NOT_A_PIT_ANCHOR' if not pit else 'PIT_AVAILABLE')
            if mode == 'POINT_IN_TIME' else 'LATER_INFORMATION_EXPLICIT_RETROSPECTIVE_NOT_BACKDATED')


def source_bound_temporal(view, ref, *, mode, prepared_at):
    """Derive eligibility from the hash-bound source view, never caller eligibility flags."""
    rows = [r for r in view['valuation'] if r['source_locator'] == ref]
    if len(rows) != 1:
        raise ValueError('valuation_locator_not_unique')
    row = rows[0]; fact = row['original_fact']
    if number(row['value']) != number(fact.get('exact_value',fact['value'])) or row['metric'] != fact['metric']:
        raise ValueError('valuation_value_or_metric_drift')
    for key in ('ticker', 'requested_security_id', 'returned_security_id'):
        if fact.get(key) is not None and fact[key] != view['ticker']:
            raise ValueError('valuation_security_drift')
    security_ids = {r['original_fields'].get('canonical_security_id') for r in view['financial_observations']}
    security_ids.discard(None)
    if fact.get('canonical_security_id') and security_ids and fact['canonical_security_id'] not in security_ids:
        raise ValueError('valuation_canonical_security_drift')
    locator = json.loads(ref)
    if (locator.get('receipt') != fact.get('source_receipt_sha256') or
            locator.get('field') != (fact.get('provider_field') or fact['metric'])):
        raise ValueError('valuation_locator_receipt_drift')
    available = None
    receipt = view.get('capture_receipts', {}).get(fact.get('source_receipt_sha256'))
    if receipt is not None:
        if (digest(encoded(receipt)) != fact.get('source_receipt_sha256') or
                receipt.get('raw_sha256') != fact.get('raw_sha256') or not fact.get('raw_sha256') or
                (receipt.get('ticker') is not None and receipt['ticker'] != view['ticker'])):
            raise ValueError('capture_receipt_binding_mismatch')
        captured = next((receipt.get(k) for k in ('retrieved_at','finished_at','collected_at','captured_at') if receipt.get(k)),None)
        if captured:
            if instant(captured) != instant(fact['retrieval_timestamp']):
                raise ValueError('capture_receipt_time_conflict')
            available = captured
    record = temporal_record(fact, cutoff=view['as_of'], prepared_at=prepared_at, mode=mode, available_at_proven=available)
    nested = json.loads(fact['basis']) if isinstance(fact.get('basis'),str) and fact['basis'].startswith('{') else {}
    if (fact.get('reference_price_as_of') and nested.get('price',{}).get('session') and
            fact['reference_price_as_of'] != nested['price']['session']):
        raise ValueError('valuation_price_session_conflict')
    for key in ('issuer_estimate_vintage', 'reference_price_as_of'):
        if record[key] and date.fromisoformat(str(record[key])[:10]) > instant(record['retrieved_at']).date():
            raise ValueError('valuation_future_vintage_or_price_session')
    record.update(source_fact_sha256=digest(encoded(fact)), source_locator=ref,
        source_receipt_sha256=fact.get('source_receipt_sha256'), raw_sha256=fact.get('raw_sha256'),
        original_use_limits={k:deepcopy(fact.get(k)) for k in ('overall_direction_use','analysis_scope','caution','caveats')})
    return record


def replay_occurrence(raw, receipt, request, lineage):
    """Re-read a recorded provider row, not a reauthorization of its Financial Owner."""
    if digest(raw) != receipt.get('raw_sha256') or receipt.get('HTTP_status') != 200:
        raise ValueError('raw_bytes_or_status_mismatch')
    if request.get('plan_sha256') != receipt.get('plan_sha256'):
        raise ValueError('request_receipt_binding_mismatch')
    payload = json.loads(raw)
    if 'concept' in lineage:
        if (payload.get('cik') != lineage['issuer_cik'] or
                digest(encoded(payload)) != lineage['source_payload_sha256']):
            raise ValueError('issuer_or_payload_mismatch')
        rows = payload['facts'][lineage['taxonomy']][lineage['concept']]['units'][lineage['currency']]
        rows = [r for r in rows if r.get('accn') == lineage['receipt']
                and r.get('start') == lineage['amount_period_start']
                and r.get('end') == lineage['amount_period_end']
                and number(r['val']) == number(lineage['amount'])]
        if len(rows) != 1:
            raise ValueError('exact_sec_occurrence_not_unique')
        return dict(provider='sec', original_raw_sha256=digest(raw), matches=1,
            period_and_unit_scale_verified=True, unit_scale=1, currency=lineage['currency'],
            statement_basis=lineage['statement_basis'], consolidation_explicitly_proven=False,
            limitation='SEC_ENTITY_WIDE_IS_NOT_CONSOLIDATION_ATTESTATION')
    params = request['params']
    if (str(params.get('bsns_year')) != str(lineage['bsns_year']) or
            str(params.get('reprt_code')) != lineage['reprt_code'] or
            params.get('fs_div') != lineage['fs_div']):
        raise ValueError('dart_request_scope_mismatch')
    rows = []
    for row in payload.get('list', []):
        if (row.get('corp_code') != params.get('corp_code') or
                row.get('rcept_no') != lineage['rcept_no']):
            continue
        actual = opendart_field_lineage(row, logical_field=lineage['logical_field'],
            report_code=lineage['reprt_code'], source_column=lineage['source_column'],
            selected=lineage['selected_for_canonical'], requested_fs_div=params['fs_div'])
        keys = ('source_row_identity', 'currency', 'statement_basis', 'amount_period_start',
                'amount_period_end', 'amount_period_type')
        if all(actual.get(k) == lineage.get(k) for k in keys) and number(actual['amount']) == number(lineage['amount']):
            rows.append(actual)
    if len(rows) != 1:
        raise ValueError('exact_dart_occurrence_not_unique')
    return dict(provider='opendart', original_raw_sha256=digest(raw), matches=1,
        period_and_unit_scale_verified=UNKNOWN, unit_scale=UNKNOWN, currency=lineage['currency'],
        statement_basis=lineage['statement_basis'], consolidation_explicitly_proven=params['fs_div'] == 'CFS',
        limitation='EXACT_API_AMOUNT_AND_EXISTING_PERIOD_PARSER_MATCH; RAW_HAS_NO_EXPLICIT_SCALE_ATTESTATION')


def replay_context(raw, receipt, request, fields):
    if digest(raw) != fields['original_raw_sha256'] or digest(raw) != receipt.get('raw_sha256'):
        raise ValueError('context_original_raw_mismatch')
    payload = json.loads(raw)
    if 'facts' in payload:
        taxonomy, concept = fields['semantic'].split(':', 1)
        if int(fields['issuer_id']) != payload['cik']:
            raise ValueError('context_issuer_mismatch')
        rows = payload['facts'][taxonomy][concept]['units'][fields['currency']]
        occurrences = []
        for i, row in enumerate(rows):
            locator = f'facts.{taxonomy}.{concept}.units.{fields["currency"]}[{i}]'
            start = row.get('start', row['end'])
            if (locator in fields['source_occurrences'] and row.get('accn') == fields['source_receipt']
                    and start == fields['period_start'] and row['end'] == fields['period_end']
                    and number(row['val']) == number(fields['current_value'])):
                occurrences.append(row)
        if len(occurrences) != 1 or receipt.get('HTTP_status') != 200 or request['plan_sha256'] != receipt['plan_sha256']:
            raise ValueError('context_exact_occurrence_missing')
        return dict(provider='sec', original_raw_sha256=digest(raw), matches=1, unit_scale=1,
            period_and_unit_scale_verified=fields.get('unit_scale') == 1,
            consolidation_explicitly_proven=False, limitation='ENTITY_WIDE_NOT_CONSOLIDATION_ATTESTATION')
    matches = []
    for row in payload.get('list', []):
        for column in ('thstrm_amount', 'thstrm_add_amount', 'frmtrm_q_amount', 'frmtrm_add_amount'):
            line = opendart_field_lineage(row, logical_field=fields['metric'], report_code=str(request['params']['reprt_code']),
                source_column=column, selected=True, requested_fs_div=request['params']['fs_div'])
            if (line['source_row_identity'] in fields['source_occurrences'] and line.get('amount') is not None
                    and line['currency'] == fields['currency'] and line['statement_basis'] == fields['statement_basis']
                    and line['amount_period_start'] == fields['period_start'] and line['amount_period_end'] == fields['period_end']
                    and number(line['amount']) == number(fields['current_value'])):
                matches.append(line)
    if len(matches) != 1:
        raise ValueError('context_exact_dart_occurrence_missing')
    return replay_occurrence(raw, receipt, request, matches[0])


def comparison_semantics(fields):
    """Keep unlike period lengths explicit; never annualize to manufacture comparability."""
    try:
        cs, ce, ps, pe = [date.fromisoformat(fields[k]) for k in
            ('period_start', 'period_end', 'prior_period_start', 'prior_period_end')]
        if not (cs < ce and ps < pe < cs):
            return False
        if (ce-cs).days == (pe-ps).days:
            return True
        policy = fields.get('fiscal_comparability') or {}
        if (fields.get('period_type') in ('annual', 'full_year') and
                policy.get('contract') == 'ISSUER_DECLARED_52_53_WEEK_ANNUAL_COMPARABLE' and
                policy.get('value_adjustment') is None and
                {(ce-cs).days + 1, (pe-ps).days + 1} == {364, 371}):
            return True
        return UNKNOWN
    except (KeyError, ValueError, TypeError):
        return UNKNOWN


def comparison_period_detail(fields):
    compatible = comparison_semantics(fields)
    result = dict(compatible=compatible, kind='UNVERIFIED', value_adjustment=None)
    if compatible is True:
        lengths = [(date.fromisoformat(fields[end])-date.fromisoformat(fields[start])).days+1
            for start,end in (('period_start','period_end'),('prior_period_start','prior_period_end'))]
        result.update(kind='EQUAL_DURATION' if lengths[0] == lengths[1] else
            'ISSUER_DECLARED_53_52_WEEK_COMPARABLE_WITH_CAVEAT', current_days=lengths[0], prior_days=lengths[1])
    return result


def operating_margin(revenue, operating_income):
    keys = ('issuer_id', 'statement_basis', 'period_start', 'period_end', 'period_type', 'currency', 'unit', 'unit_scale')
    for row in (revenue, operating_income):
        if (row.get('raw_verified') is not True or row.get('scale_verified') is not True or row.get('unit_scale') != 1):
            return dict(state='DERIVATION_BLOCKED_UNVERIFIED_SCALE', value=None)
        if row.get('consolidation_explicitly_proven') is not True:
            return dict(state='DERIVATION_BLOCKED_CONSOLIDATION_UNPROVEN', value=None)
    if (any(not revenue.get(k) or revenue[k] != operating_income.get(k) for k in keys) or
            revenue.get('metric') != 'revenue' or operating_income.get('metric') != 'operating_income' or
            not revenue.get('ref') or not operating_income.get('ref') or revenue['ref'] == operating_income['ref']):
        return dict(state='DERIVATION_BLOCKED_SCOPE_MISMATCH', value=None)
    r, o = number(revenue['value']), number(operating_income['value'])
    if r <= 0:
        return dict(state='DERIVATION_BLOCKED_NONPOSITIVE_REVENUE', value=None)
    proof = dict(formula='operating_income / revenue * 100', operands=[deepcopy(revenue), deepcopy(operating_income)],
        source_refs=[revenue['ref'], operating_income['ref']], unit='percent', value=str(o/r*100),
        state='DERIVED_FROM_VERIFIED_RAW', direction_grant=False)
    return {**proof, 'formula_receipt_sha256': digest(encoded(proof))}


class _Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Axis(_Strict):
    state: str
    confidence: Literal['LOW', 'MEDIUM', 'HIGH']
    statement: str
    refs: list[str]
    pro: list[str]
    con: list[str]
    unknown: list[str]
    as_of: str
    temporal_limitations: list[str]
    claim_role: Literal['DATED_OBSERVATION','ECONOMIC_HYPOTHESIS','VERIFIED_CAUSAL_FACT','ENTRY_TIMING_CONTEXT','UNKNOWN'] = 'UNKNOWN'


class ResearchSplit(_Strict):
    contract: Literal['DATED_RESEARCH_REVIEW_V2_OFFLINE']
    ticker: str
    input_digest: str
    research_mode: Mode
    newbuyer_fundamental_attractiveness: Axis
    newbuyer_entry_timing: Axis
    structural_risk: Literal['OBSERVED_RISK', 'POTENTIAL_EXPOSURE', 'UNKNOWN']
    thesis_comparison: Literal['NOT_COMPARED_TO_REGISTERED_THESIS']
    NO_SEND: Literal[True]
    Strict_NATIVE_STAGE_READY: Literal[False]
    citations: list[_Citation] = []


def validate_split(output, *, view, binding, temporal):
    result = ResearchSplit.model_validate(output).model_dump()
    if result['ticker'] != view['ticker'] or result['input_digest'] != binding['research_view_sha256']:
        raise ValueError('exact_output_binding_mismatch')
    if binding.get('byte_binding_verified') is not True or digest(encoded(view)) != binding['research_view_sha256']:
        raise ValueError('view_bytes_binding_required')
    if view.get('research_mode') and view['research_mode'] != result['research_mode']:
        raise ValueError('original_research_mode_conflict')
    catalog = reference_catalog(view)
    for name, labels in (
        ('newbuyer_fundamental_attractiveness', ('ATTRACTIVE', 'NEUTRAL', 'UNATTRACTIVE', 'UNKNOWN')),
        ('newbuyer_entry_timing', ('FAVORABLE', 'WAIT_FOR_CONFIRMATION', 'UNFAVORABLE', 'UNKNOWN'))):
        axis = result[name]
        if axis['state'] not in labels or not axis['statement'] or axis['as_of'] != view['as_of']:
            raise ValueError('axis_state_statement_or_time_invalid')
        if axis['state'] != UNKNOWN and not axis['refs']:
            raise ValueError('issued_axis_requires_citations')
        refs = axis['refs'] + axis['pro'] + axis['con']
        if any(ref not in catalog['refs'] or ref not in axis['refs'] for ref in refs):
            raise ValueError('unknown_or_unbound_reference')
        for ref in refs:
            if catalog['refs'][ref]['kind'] == 'valuation_locator_not_owner':
                time = temporal.get(ref)
                if not time or not time.get('research_prepared_at'):
                    raise ValueError('source_bound_prepared_time_required')
                expected = source_bound_temporal(view, ref, mode=result['research_mode'], prepared_at=time['research_prepared_at'])
                if (any(k in time and time[k] != expected[k] for k in expected) or
                        not expected['direction_anchor_temporally_eligible']):
                    raise ValueError('valuation_not_temporally_eligible')
                if expected['caveat'] not in axis['temporal_limitations']:
                    raise ValueError('temporal_caveat_required')
        kinds = {catalog['refs'][r]['kind'] for r in refs}
        economic = {'financial', 'public_business_profile_not_verified_cause', 'valuation_locator_not_owner'}
        if name == 'newbuyer_fundamental_attractiveness' and axis['state'] != UNKNOWN and not kinds & economic:
            raise ValueError('fundamental_requires_economic_context_not_only_technical')
        if axis['claim_role'] == 'VERIFIED_CAUSAL_FACT' and (
                not view.get('verified_mechanism_count') or not kinds & {'financial','public_business_profile_not_verified_cause'}):
            raise ValueError('unverified_cause_promoted_to_fact')
        if name == 'newbuyer_entry_timing' and axis['state'] == 'FAVORABLE' and not kinds & {
                'dated_technical','original_dated_SR_fact','original_dated_SR_source_sha256'}:
            raise ValueError('favorable_timing_requires_price_context')
    if result['structural_risk'] == 'OBSERVED_RISK' and not view['structural_risk']['occurred_risk_assertion']:
        raise ValueError('unverified_risk_promoted_to_occurred')
    for citation in result['citations']:
        if citation['axis'] not in ('newbuyer_fundamental_attractiveness','newbuyer_entry_timing') or citation['ref'] not in result[citation['axis']]['refs']:
            raise ValueError('split_numeric_axis_ref_mismatch')
    render_numeric_citations(result,catalog,view)
    return result


def render_numeric_citations(output, catalog, view, *, quality_sidecar=None, capture_receipts=None):
    """Exact structured citations only; this projector never generates an opinion."""
    rows = []
    financial = {r['original_ref']: r for r in view['financial_observations']}
    valuations = {r['source_locator']: r['original_fact'] for r in view['valuation']}
    for citation in output['citations']:
        fact = {k: v for k, v in citation.items() if k != 'axis'}
        if isinstance(fact.get('value'), bool) or fact not in catalog['numeric_facts']:
            raise ValueError('exact_numeric_citation_mismatch')
        ref = citation['ref']; original = financial.get(ref, {}).get('original_fields', {})
        valuation = valuations.get(ref, {})
        qa = (quality_sidecar or {}).get(ref, {})
        start_key, end_key = ('prior_period_start','prior_period_end') if fact['path'] == 'fields.prior_comparable_value' else ('period_start','period_end')
        start,end = original.get(start_key),original.get(end_key)
        period_state = 'NOT_FINANCIAL_PERIOD'
        if original:
            period_state = 'MATCHED' if start and end and fact['period'] == f'{start}/{end}' else 'UNKNOWN_OR_CONFLICT'
            if period_state != 'MATCHED': start,end = None,None
        retrieved = None; providers = set()
        for proof in qa.get('raw_replay', []):
            providers.add(proof['provider'])
            receipt = (capture_receipts or {}).get(proof['capture_receipt_sha256'])
            if receipt and digest(encoded(receipt)) == proof['capture_receipt_sha256'] and receipt.get('raw_sha256') == proof['original_raw_sha256']:
                value = receipt.get('finished_at')
                if value: instant(value); retrieved = max((retrieved or value,value),key=instant)
        provenance = dict(value=fact['value'], unit=fact['unit'], period=fact['period'], basis=fact['basis'],
            original_scale=original.get('unit_scale', UNKNOWN),
            raw_independently_verified_scale=qa.get('period_and_unit_scale_verified',UNKNOWN),
            period_start=start, period_end=end, period_metadata_state=period_state,
            period_type=original.get('period_type'), provider=valuation.get('provider') or (next(iter(providers)) if len(providers)==1 else UNKNOWN),
            ref=ref, path=fact['path'], retrieved_at=valuation.get('retrieval_timestamp') or retrieved,
            source_cutoff=financial.get(ref, {}).get('source_cutoff'), as_of=view['as_of'],
            technical_as_of=fact['period'] if catalog['refs'][ref]['kind'].startswith(('dated_technical','original_dated_SR')) else None,
            FY1_caveat='ESTIMATE_NOT_REPORTED_PROFIT; VINTAGE_DISTINCT_FROM_RETRIEVAL' if
                ('FY1' in str(valuation) or 'FORWARD' in str(valuation).upper()) else None)
        rows.append(provenance)
    return rows


def split_preview(view, binding, *, mode, prepared_at):
    """Source-only input/schema preview. Never convert legacy model labels into new answers."""
    if not binding.get('byte_binding_verified') or digest(encoded(view)) != binding['research_view_sha256']:
        raise ValueError('preview_source_digest_mismatch')
    catalog = reference_catalog(view)
    time = {row['source_locator']:source_bound_temporal(view,row['source_locator'],mode=mode,prepared_at=prepared_at)
        for row in view['valuation']}
    return dict(contract=CONTRACT, ticker=view['ticker'],as_of=view['as_of'],research_mode=mode,
        source_binding=deepcopy(binding),temporal=time, source_view=deepcopy(view), reference_catalog=catalog,
        split_schema=ResearchSplit.model_json_schema(),
        evidence_roles={ref:row['kind'] for ref,row in catalog['refs'].items()},
        new_judgment=None, model_executed=False, status='PASSED_SOURCE_INPUT__ITEM_PARTIAL_QUALITY__JUDGMENT_NOT_RUN',
        NO_SEND=True,Strict_NATIVE_STAGE_READY=False)


def compact_evidence(view):
    """Remove only catalog copies of fields already exactly present in the bound view."""
    full = reference_catalog(view)
    refs = {ref: {k: v for k, v in entry.items() if k == 'kind'} for ref, entry in full['refs'].items()}
    compact = dict(contract=CONTRACT, evidence=deepcopy(view), reference_catalog=dict(refs=refs,
        numeric_facts=deepcopy(full['numeric_facts'])))
    return compact, full


def compact_prompt_proposal(view, binding, *, stage, prior=None):
    old, schema, catalog = build_prompt(view, binding, stage=stage, prior=prior)
    marker = b'\nBOUND_RESEARCH_INPUT:\n'
    instruction, body = old.split(marker, 1)
    payload = json.loads(body)
    compact, _ = compact_evidence(view)
    payload['reference_catalog'] = compact['reference_catalog']
    new = instruction + marker + encoded(payload)
    return new, dict(old_prompt_sha256=digest(old), proposed_prompt_sha256=digest(new),
        old_bytes=len(old), proposed_bytes=len(new), bytes_removed=len(old)-len(new),
        schema_sha256=digest(encoded(schema)), full_catalog_sha256=digest(encoded(catalog)),
        actual_model_execution=False, token_and_quality_savings='UNPROVEN')
