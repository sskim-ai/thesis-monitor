"""Opt-in source-bound arithmetic, not a new Financial Owner or valuation grant."""
import copy
import math
import json
from app.services.vnext_financial_reuse import replay_reported_amounts
from app.services.vnext_research_store import digest
from scripts.m12dr_financial_source_authority import comparative_facts, source_quality

CONTRACT = 'vnext-source-earnings-composition-v1'


def _comparison_data(evidence, snapshots, issuer_id, ticker):
    raw = snapshots[evidence['source_sha']]
    if digest(raw) != evidence['source_sha']:
        raise ValueError('comparison_snapshot_digest_mismatch')
    snapshot = json.loads(raw)
    facts = []
    for bundle in snapshot['projection']['quality_bundles']:
        quality = source_quality(bundle)
        if quality != bundle['quality']:
            raise ValueError('comparison_snapshot_quality_drift')
        facts.extend(comparative_facts(quality, ticker=ticker, issuer_id=issuer_id))
    selected = [f for f in facts if f['fields']['metric'] == evidence['field'].split('.')[-1]]
    if len(selected) != 1:
        raise ValueError('comparison_snapshot_not_unique')
    return {k: selected[0][k] for k in ('fields', 'as_of_date', 'quality_contract', 'quality_receipt_sha256')}


def compose(packet, *, original_context):
    """Re-run the existing owner before deriving a limited research attachment."""
    ctx = dict(original_context)
    snapshots = ctx.pop('comparison_source_bytes')
    plan, projection = ctx['plan'], ctx['expected_projection']
    if (packet.get('strict_native') is not False or packet.get('live_authority') is not False
            or packet.get('holdings_included') is not False or packet.get('user_thesis_included') is not False
            or packet['case'] != plan['ticker']
            or packet['public_security']['canonical_security_id'] != plan['security']['canonical_security_id']):
        raise ValueError('composition_public_identity_required')
    replay = replay_reported_amounts(**ctx)
    qualified = {r['fields']['metric']: r for r in replay['facts']}
    evidence = {e['field']: e for e in packet['evidence'] if e['field'].startswith('financial.')}
    comparisons = {}; fields = {}; bindings = []
    for metric in ('revenue', 'operating_income'):
        candidates = [c for c in projection['comparisons'] if c['metric'] == metric]
        fs = [f for f in projection['fields'] if f['metric'] == metric and f['current_prior_role'] == 'current']
        if len(candidates) != 1 or len(fs) != 1 or metric not in qualified:
            raise ValueError('original_comparison_not_qualified')
        c, f = candidates[0], fs[0]; e = evidence.get('financial.' + metric)
        if not e or e['status'] != 'SOURCE_REFERENCE':
            raise ValueError('comparison_packet_missing')
        p = e['data']['fields']; cur, prior = c['current'], c['comparison']
        if any(q.get('prose_eligible') is not True or q.get('hard_denial_reasons') for q in (cur, prior)):
            raise ValueError('original_comparison_denied')
        pairs = dict(current_value=cur['lineage']['amount'], prior_comparable_value=prior['lineage']['amount'],
            period_start=f['period_start'], period_end=f['period_end'], currency=f['currency'],
            statement_basis=f['statement_basis'], source_receipt=f['source_document_id'],
            prior_period_start=prior['lineage']['amount_period_start'], prior_period_end=prior['lineage']['amount_period_end'],
            growth_pct=c['growth_pct'], delta=c['delta'], direction=c['direction'],
            issuer_id=qualified[metric]['fields']['issuer_id'], source_ticker=plan['ticker'],
            period_type=cur['lineage']['amount_period_type'], recurrence_verified=False)
        if any(p.get(k) != v for k, v in pairs.items()) or p['source_occurrences'] != [cur['lineage']['source_row_identity'], prior['lineage']['source_row_identity']]:
            raise ValueError('comparison_packet_original_mismatch')
        # Historical comparisons and later amount replay have distinct receipts.
        if e['data'] != _comparison_data(e, snapshots, pairs['issuer_id'], plan['ticker']):
            raise ValueError('comparison_quality_identity_mismatch')
        comparisons[metric], fields[metric] = c, f
        bindings.append(dict(metric=metric, ref=e['ref'], raw_sha256=f['raw_artifact_sha256'],
            account=f['semantic'], occurrences=p['source_occurrences'], source_receipt=f['source_document_id']))
    net = qualified.get('net_income'); ne = evidence.get('financial.net_income')
    if net is None or ne is None or ne['data'] != {k: net[k] for k in ('fields', 'as_of_date', 'quality_contract', 'quality_receipt_sha256')}:
        raise ValueError('net_income_original_mismatch')
    r, o = fields['revenue'], fields['operating_income']; rc, oc = comparisons['revenue'], comparisons['operating_income']
    keys = ('canonical_security_id', 'canonical_company_id', 'source_document_id', 'raw_artifact_sha256',
            'period_start', 'period_end', 'period_role', 'currency', 'unit', 'unit_scale', 'statement_basis')
    compatible = all(r[k] == o[k] for k in keys)
    compatible &= all(rc['comparison']['lineage'][k] == oc['comparison']['lineage'][k]
                      for k in ('amount_period_start', 'amount_period_end', 'amount_period_type', 'currency', 'statement_basis'))
    # Insurance revenue is not total operating revenue; no industry/ticker shortcut.
    applicable = r['semantic'] == 'ifrs-full_Revenue' and o['semantic'] == 'dart_OperatingIncomeLoss'
    amounts = [rc[side]['lineage']['amount'] for side in ('current', 'comparison')]
    denominator = all(type(v) in (int, float) and math.isfinite(v) and v > 0 for v in amounts)
    reason = 'ELIGIBLE_SOURCE_BOUND_ARITHMETIC' if compatible and applicable and denominator else (
        'BASIS_OR_PERIOD_MISMATCH' if not compatible else 'REVENUE_DENOMINATOR_SCOPE_UNPROVEN' if not applicable else 'NONPOSITIVE_DENOMINATOR')
    ratios = []
    if reason == 'ELIGIBLE_SOURCE_BOUND_ARITHMETIC':
        for side in ('current', 'comparison'):
            rn, on = rc[side]['lineage'], oc[side]['lineage']
            if not math.isfinite(on['amount']): raise ValueError('nonfinite_operating_amount')
            ratios.append(dict(role=side, value=100 * on['amount'] / rn['amount'], unit='percent',
                numerator=on['amount'], denominator=rn['amount'], period=rn['amount_period_start']+'/'+rn['amount_period_end'],
                formula='100 * exact operating income / exact revenue', refs=[b['ref'] for b in bindings],
                occurrences=[on['source_row_identity'], rn['source_row_identity']], source_sha=r['raw_artifact_sha256']))
    return dict(contract=CONTRACT, base_packet_sha256=digest(packet), projection_sha256=replay['projection_sha256'],
        source_generation=plan['run_id'], source_cutoff=plan['cutoff'], source_receipt=r['source_document_id'],
        bindings=bindings, net_income_ref=ne['ref'], net_income_original_sha=digest(net),
        margin_status=reason, operating_margin=ratios, independent_lineages=1,
        corroboration={m: c['current']['corroboration'] for m, c in comparisons.items()},
        source_quality_unchanged=True, recurrence='NOT_ESTABLISHED', mechanism='NOT_ESTABLISHED',
        context_limits=['Arithmetic is not causal attribution, recurrence, cash conversion, economic role or valuation.',
                        'Source-column equality and within-statement reconciliation are not independent corroboration.',
                        'Net income remains a dated absolute total; no growth, EPS, attributable or FY1 grant.'],
        strict_native=False, investment_direction_grant=False, valuation_denominator_grant=False)


def catalog(attachment):
    rows = []
    for r in attachment['operating_margin']:
        n = dict(fact_id=r['refs'][1], field_path='/earnings_composition/operating_margin/'+r['role'],
            value=r['value'], unit='percent', basis='DERIVED_SAME_FILING_RESEARCH_ONLY', as_of=r['period'],
            source_sha=r['source_sha'], supporting_refs=r['refs'], occurrences=r['occurrences'], derived_role=r['role'])
        n['catalog_id'] = 'c'+digest(n)[:16]; rows.append(n)
    return rows


def enrich(packet, *, original_context):
    result = copy.deepcopy(packet)
    result['earnings_composition'] = compose(packet, original_context=original_context)
    result['numeric_catalog'] += catalog(result['earnings_composition'])
    return result


def verify(packet, *, original_context):
    base = copy.deepcopy(packet); att = base.pop('earnings_composition')
    extras = catalog(att)
    if extras and base['numeric_catalog'][-len(extras):] != extras: raise ValueError('derived_catalog_drift')
    if extras: base['numeric_catalog'] = base['numeric_catalog'][:-len(extras)]
    if compose(base, original_context=original_context) != att: raise ValueError('composition_original_replay_mismatch')
    return base, extras
