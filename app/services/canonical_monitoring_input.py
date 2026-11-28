"""Canonical current-source input transformations, independent of controllers."""
from copy import deepcopy
from decimal import Decimal

from app.services.direction_timing_ownership_service import verified_owned_packet_view
from app.services.provider_native_technical import INDICATORS
from scripts import r2b_r2_contract as c
from app.services import canonical_monitoring_owner as owner
from app.services.entry_candidate_basis import restrict_entry_candidates
from scripts.m12co_entry_range_contract import build_subject_candidate_coverage
from scripts.m12cr_r1_typed_quality_contract import project_business_evidence_quality, project_security_valuation_basis
from scripts.m12dj_source_authority_preflight import preflight_current_pass_a_subject
from scripts.m12ds_r2_ranges import eligible_range_inputs, valuation_policy
from scripts.m12cq_two_pass_contract import build_pass_b_subject_context, validate_pass_b_transformation


NATIVE_TECHNICAL_PROMPT = '''Use native_technical_context for trend, momentum, volume and the choice of an
available tactical watch zone. The supplied provider fields and formula meanings
are authoritative inputs; do not replace them with Wilder RSI, BB20/2, a different
EMA seed or a locally recalculated indicator. Use the supplied timeframe and bar
date. Null or unavailable fields are missing evidence, never zero. A short history
does not by itself invalidate the other available indicators. Interpret their
agreement and disagreement in context, without inventing universal thresholds.
Technical evidence informs entry context only; it cannot create business direction,
fundamental cheapness, fair value or a new price range.'''

C60_NATIVE_GUIDANCE = '''Read the available MA alignment and direction, price distance/convergence,
Bollinger position/width and Envelope, RSI and MACD line versus histogram, volume with price,
and return/drawdown by their actual bar units. Use meaningful evidence across families and
completed D/W/M horizons; do not count correlated indicators as independent votes. Compare
native values at the same supplied bar dates; lag5 means five bars, not five calendar days.
In recent_comparison, dates/close/volume are [current, previous, lag5]. The previous, lag5 and
close_relations arrays follow the shared comparison_fields order. Relation strings follow
relation_dates in chronological order: A=above, B=below,
E=equal, ?=missing. They are observed closes only, not intraday touches or proof of an older
historical crossing. Do not infer continuous movement between sparse observations. The existing
native field evidence ref identifies the source artifact and field, including its supplied
comparison; do not pretend a historical value occurred on the latest date. No indicator
recalculation. BB expansion/upper-band progress can support a trend; a lower-band breach and
recovery may be useful. Negative MACD or incomplete alignment alone is not an entry veto.
Distinguish constructive early recovery from deterioration and an unsupported bounce; weigh
price/RR/structure, not perfect indicator agreement. Missing long history is not bearishness.
Use only supplied eligible candidate prices and their own risk/reward; do not skip closer
resistance, transfer risk from another candidate, or turn a chart level into fair value.'''



def native_technical_context(view, context):
    """Copy the Source's native values that survived the existing B projection.

    This is a model-input projection, not another indicator or admission engine.
    Unavailable periods/fields retain their names and reasons with null values.
    """
    packet = view.get('evidence_packet') or {}
    native = packet.get('technical_context_quality', {}).get('provider_native')
    if native is None:
        return None
    emitted = {row['ref_id']: row for row in context['decision_evidence']}
    eligible = {row['ref_id'] for row in context['source_use_projection']['source_permissions']
                if 'ENTRY' in row['allowed_uses']}
    original = [row for row in packet['evidence']
                if row['ref_id'].startswith('native:') and row['category'] == 'technical_feature']
    result = {key: deepcopy(native.get(key)) for key in
              ('provider', 'provider_code', 'market', 'adjusted', 'cutoff',
               'indicator_schema', 'formula_semantics', 'source_hash')}
    result['periods'] = {}
    if native.get('comparison_version') == 1:
        result['comparison_version'] = 1
        result['comparison_fields'] = list(INDICATORS)
    monitoring = native.get('allowed_use') == 'MONITORING_TECHNICAL'
    for timeframe in ('daily', 'weekly', 'monthly'):
        period = native['periods'].get(timeframe, {})
        frame_quality = packet['technical_context_quality'].get(
            {'daily': 'D', 'weekly': 'W', 'monthly': 'M'}[timeframe], {})
        as_of = period.get('completed_as_of')
        available = (monitoring and period.get('status') == 'AVAILABLE'
                     and frame_quality.get('usable_for_current_reasoning') is True)
        values, quality, refs = {}, {}, {}
        reasons = list(period.get('reasons') or []) + list(frame_quality.get('reasons') or [])
        if not monitoring:
            reasons.append('NATIVE_SCOPE_NOT_MONITORING')
        for field in INDICATORS:
            source_value = period.get('indicators', {}).get(field)
            source_quality = period.get('indicator_quality', {}).get(field, 'UNAVAILABLE_PROVIDER_NULL_OR_MISSING')
            matches = [row for row in original
                       if row['source_ref'].endswith('.native.' + timeframe + '.' + field)]
            row = matches[0] if len(matches) == 1 else None
            ref = row['ref_id'] if row else None
            usable = (available and source_quality == 'PROVIDER_NATIVE' and source_value is not None
                      and ref in emitted and ref in eligible)
            if usable:
                visible = emitted[ref]
                if (row['as_of'] != as_of or visible['as_of'] != as_of
                        or Decimal(str(row['value'])) != Decimal(str(source_value))
                        or visible['value'] != row['value']):
                    raise ValueError('native_model_source_value_mismatch')
                values[field] = deepcopy(source_value)
                quality[field] = source_quality
                refs[field] = ref
            else:
                values[field] = None
                quality[field] = (source_quality if source_quality != 'PROVIDER_NATIVE'
                                  else 'UNAVAILABLE_FOR_MONITORING')
        if not refs and period.get('status') == 'AVAILABLE':
            reasons.append('NO_ELIGIBLE_NATIVE_INDICATOR_EVIDENCE')
        result['periods'][timeframe] = dict(
            as_of=as_of, status='AVAILABLE' if refs else
            'INVALID' if period.get('status') == 'INVALID' else 'UNAVAILABLE',
            calculation_row_count=period.get('returned_count', 0),
            completed_row_count=period.get('completed_count', 0),
            source_hash=period.get('source_hash'), indicators=values,
            indicator_quality=quality, evidence_refs=refs,
            reasons=list(dict.fromkeys(reasons)))
        comparison = period.get('recent_comparison')
        if refs and result.get('comparison_version') == 1 and comparison is not None:
            # Same source hash/field ref already survived ENTRY projection.
            # Never expose denied or unavailable fields from the artifact's history.
            compact = deepcopy(comparison)
            prior, relations = compact.pop('prior_indicators'), compact.pop('close_relations')
            # Shared column order avoids repeating every field name for D/W/M.
            compact['previous'] = [prior.get(f, [None, None])[0] if f in refs else None
                                   for f in INDICATORS]
            compact['lag5'] = [prior.get(f, [None, None])[1] if f in refs else None
                               for f in INDICATORS]
            compact['close_relations'] = [relations.get(f) if f in refs else None for f in INDICATORS]
            result['periods'][timeframe]['recent_comparison'] = compact
        path = period.get('recent_path')
        if refs and available and path is not None:
            from app.services.provider_native_technical import RECENT_PATH_FIELDS
            dates = path['dates']
            if (not 0 < len(dates) <= 20 or dates != sorted(set(dates))
                    or dates[-1] != as_of
                    or any(len(path[key]) != len(dates) for key in ('close','volume'))
                    or any(len(vals) != len(dates) for vals in path['indicators'].values())):
                raise ValueError('native_recent_path_alignment')
            result['periods'][timeframe]['recent_path'] = dict(
                dates=deepcopy(dates), close=deepcopy(path['close']), volume=deepcopy(path['volume']),
                indicators={f:deepcopy(path['indicators'][f]) for f in RECENT_PATH_FIELDS
                            if f in refs and f in path['indicators']})
    return result

def subject_inputs(view, authority, receipt, *, generation, atomic=()):
    owned = verified_owned_packet_view(view)
    source_generation = authority["authority"]["source_generation_id"]
    cat, metadata, chain = c.bound_chain(view, authority, atomic=list(atomic), generation=generation,
                                       source_generation=source_generation, view_receipt=receipt)
    ownership = {"ticker": view["ticker"], "core_ref_ids": sorted(owned.core_refs),
                 "timing_ref_ids": sorted(owned.timing_refs)}
    sub = build_subject_candidate_coverage(market=view["market"], packet=view["evidence_packet"], ownership=ownership)
    sub.update(decision_evidence=metadata,
        business_evidence_quality_state=project_business_evidence_quality(view["evidence_packet"]),
        security_valuation_basis_state=project_security_valuation_basis(view["evidence_packet"]),
        directional_disclosure_quality_refs=sorted(set(cat["material_disclosure_failure_refs"] + cat["positive_quality_refs"])))
    return cat, sub, chain

def a_input(view, cat, sub, chain, authority):
    gate = preflight_current_pass_a_subject(ticker=view["ticker"], source_generation_id=chain["source_generation_id"],
        execution_generation_id=chain["execution_generation_id"], catalog=cat, source_packet=sub,
        authority=chain["authority"], projection=chain["projection"], binding=chain["binding"], expectation=chain["expectation"],
        prohibited_pass_a_source_refs=authority["pass_a_visibility_exclusions"])

    final = gate['model_context']
    if final and (compatible := pass_a_filing_context(view, final)):
        from app.services.unified_snapshot_contract import digest
        final['filing_context_only'] = compatible
        gate['receipt']['final_model_view_sha256'] = digest(final)
    return gate


def pass_a_filing_context(view, final):
    rows = filing_observations(view)
    if not rows:
        return []
    from scripts.m12cq_two_pass_contract import pass_a_leakage_scan
    # The contextual material cannot be cited as an independent archetype or tier vote.
    eligible = {r['ref_id'] for r in final['eligible_non_price_evidence']}
    eligible &= {r['ref_id'] for r in final['source_use_projection']['source_permissions']
                 if 'PASS_A_ARCHETYPE' in r['allowed_uses'] and 'PASS_A_ARCHETYPE' not in r.get('prohibited_uses', ())}
    documents = {f['fields'].get('source_receipt') for f in view['packet']['stocks'][0]['fact_catalog']
                 if f['fact_type'] == 'earnings_comparison' and 'canonical:' + f['fact_id'] in eligible}
    return [r for r in rows if r['observation']['source_document_id'] in documents
            and pass_a_leakage_scan([r])['status'] == 'PASS']


def filing_observations(view):
    from app.services.unified_snapshot_contract import digest
    stocks = (view.get('packet') or {}).get('stocks', [])
    owner = view.get('selected_financial_owner') or {}
    direct = owner.get('owner_type')
    if (len(stocks) != 1 or not stocks[0].get('reported_filing_context')
            or direct not in ('direct_sec', 'direct_opendart') or owner.get('bridge_receipt')
            or owner.get('monitored_security') != view['ticker'] or stocks[0]['ticker'] != view['ticker']
            or owner.get('selected_projection_sha256') != digest(view.get('projection'))):
        return []
    security_id = (view.get('valuation_view') or {}).get('security_id')
    result = []
    for item in stocks[0]['reported_filing_context']:
        source = item['observation']
        operating = item['kind'] == 'REPORTED_OPERATING_CONTEXT_ONLY'
        if operating != (direct == 'direct_opendart') or (operating and source.get('source_provider') != 'opendart'):
            continue
        if item['kind'] == 'FILING_EXCERPT_CONTEXT_ONLY':
            issuer, security, ref = source['issuer_id'], source['security_id'], digest(source)
        elif operating or item['kind'] == 'REPORTED_SEGMENT_CONTEXT_ONLY':
            issuer, security = source['provider_issuer_id'], source['canonical_security_id']
            if not source.get('context_eligible') or source.get('quality_errors') or source.get('direction_eligible') is not False:
                continue
            ref = digest({k: v for k, v in source.items() if k != 'normalized_hash'})
        else:
            continue
        if (ref == item['ref_id'] and source['ticker'] == view['ticker']
                and issuer == owner['issuer_identity'] and security == security_id):
            if operating or item['kind'] == 'REPORTED_SEGMENT_CONTEXT_ONLY':
                registry = item.get('numeric_registry_entry') or {}
                if (registry.get('fact_id') != ref or registry.get('registered') is not True
                        or registry.get('semantic_type') != source['metric']
                        or registry.get('unit') != source['currency'] or registry.get('value') != source['value']):
                    continue
                keys = ('source_document_id','document','filing_date')
                keys += ('account_name','source_column','period_role','current_prior_role') if operating else ('dimensions',)
                keys += ('semantic','metric','value','currency','unit','period_start','period_end','statement_basis')
                result.append(dict(ref_id=ref, as_of=source['period_end'], kind=item['kind'],
                    observation={k: deepcopy(source[k]) for k in keys}))
            else:
                result.append(dict(ref_id=ref, as_of=source['filing_date'], kind=item['kind'],
                    observation={k: source[k] for k in ('source_document_id','document','document_type',
                        'report_end','classification','excerpt')}))
    return result


def economic_context(view, context, classification, *, original_rows=None):
    """Compact existing, eligible business observations, not additional votes.

    The frozen Source and existing source-use projection own the values. Do
    not promote an absolute/context-only observation to a directional claim,
    and do not copy valuation, chart, audit-only or denied values.
    """
    from app.services.cross_market_decision_engine_service import canonical_fact_statement
    from app.services.new_buyer_base_contract import number
    from app.services.unified_snapshot_contract import digest
    rows = view.get('packet', {}).get('stocks', [])
    if len(rows) != 1 or rows[0].get('ticker') != view['ticker']:
        return dict(observations=[], relationships=[])
    facts = {f['fact_id']: f for f in rows[0].get('fact_catalog', ())}
    permissions = {r['ref_id']: set(r.get('allowed_uses', ())) - set(r.get('prohibited_uses', ()))
                   for r in context['source_use_projection']['source_permissions']}
    filing_rows = filing_observations(view)
    observed = list(filing_rows)
    originals = None if original_rows is None else {r['ref_id']: r for r in original_rows}
    comparison_keys = ('metric','current_value','prior_comparable_value','growth_pct',
        'period_start','period_end','prior_period_start','prior_period_end','period_type',
        'currency','statement_basis','issuer_id','source_ticker','source_receipt',
        'anomaly_cautions','reported_quarter_basis','fiscal_comparability')
    for row in context['decision_evidence']:
        ref = row['ref_id']
        uses = permissions.get(ref, set())
        if not uses & {'CONTEXT','OVERALL_DIRECTION'}:
            continue
        source_time = row.get('source_time') or {}
        if originals is not None:
            # Pass B strips source_time from its compact rows; recover only the
            # proof for an unchanged, visible row, not other source-only fields.
            parent = originals.get(ref)
            if parent is None or any(row.get(k) != parent.get(k) for k in ('statement', 'as_of')):
                continue
            source_time = parent.get('source_time') or {}
        fact = facts.get(ref.removeprefix('canonical:')) if ref.startswith('canonical:') else None
        fields = (fact or {}).get('fields', {})
        item = dict(ref_id=ref, as_of=row.get('as_of'))
        if (fact and fact.get('fact_type') == 'earnings_comparison'
                and fact.get('interpretation_eligible') is True
                and row.get('statement') == canonical_fact_statement(fact)
                and source_time.get('canonical_fact_sha256') == digest(fact)
                and number(fields.get('current_value')) is not None
                and number(fields.get('prior_comparable_value')) is not None):
            values = {k: deepcopy(fields[k]) for k in comparison_keys if k in fields}
            # Keep the exact reported amounts; percentage growth is unsuitable
            # for a negative base or a transition through zero.
            if number(values['prior_comparable_value']) <= 0 or number(values['current_value']) < 0:
                values.pop('growth_pct', None)
            item.update(kind='REPORTED_COMPARISON', observation=values)
        elif row.get('financial_context') and row.get('financial_value') is not None:
            item.update(kind='REPORTED_FINANCIAL_CONTEXT_ONLY',
                        observation=dict(value=row['financial_value'], context=deepcopy(row['financial_context'])))
        elif fact and fact.get('fact_type') == 'earnings' and fact.get('prose_eligible') is True:
            if source_time.get('canonical_fact_sha256') != digest(fact):
                continue
            item.update(kind='REPORTED_ABSOLUTE_CONTEXT_ONLY', observation=deepcopy(fields))
        elif ref.startswith('canonical:event:') and 'CONTEXT' in uses:
            # The current RSS owner authenticates a headline, not the contract,
            # forecast or allegation mentioned in it.
            item.update(kind='REPORTED_EVENT_CONTEXT_ONLY', observation=row['statement'])
        else:
            continue
        observed.append(item)
    # The existing selected financial projection also owns absolute context
    # fields, even when they have no comparative directional fact. Use their
    # original normalized_hash references only as economic context. No issuer
    # bridge may transfer a security denominator, and no denied comparison is
    # resurrected through a second source-field projection.
    owner = view.get('selected_financial_owner') or {}
    projection = view.get('projection') or {}
    if (not owner.get('bridge_receipt') and projection
            and owner.get('selected_projection_sha256') == digest(projection)
            and owner.get('monitored_security') == view['ticker']):
        compared_metrics = {f.get('fields', {}).get('metric') for f in facts.values()
                            if f.get('fact_type') == 'earnings_comparison'}
        context_metrics = {'revenue','operating_income','net_income','owners_parent_net_income',
            'operating_cash_flow','operating_cashflow','assets','liabilities','equity',
            'stockholders_equity','noncontrolling_interest','cash_and_cash_equivalents',
            'debt_including_current','interest_bearing_debt_total','inventory',
            'ppe_capex_cash_outflow','ocf_less_ppe_capex','diluted_eps','diluted_shares',
            'weighted_average_diluted_shares','dividends','share_repurchases','roe','roic'}
        fields = [row for row in (*projection.get('fields', ()), *rows[0].get('reported_absolute_context_fields', ()))
                  if row.get('ticker') == view['ticker']
                  and row.get('canonical_security_id') == (view.get('valuation_view') or {}).get('security_id')
                  and row.get('context_eligible') is True and not row.get('quality_errors')
                  and row.get('source_use') == 'ABSOLUTE_CONTEXT_ELIGIBLE'
                  and row.get('metric') in context_metrics - compared_metrics
                  and number(row.get('value')) is not None and row.get('normalized_hash')]
        by_ref = {row['normalized_hash']: row for row in fields}
        # Preserve original current/prior pairing where supplied. A prior
        # number without an admitted pair is not labeled comparable growth.
        groups = {}
        for row in fields:
            if row.get('current_prior_role') == 'current':
                key = (row['metric'], row.get('period_role'), row.get('statement_basis'), row.get('currency'))
                groups.setdefault(key, []).append(row)
        selected = set()
        for group in groups.values():
            latest = max(row.get('period_end') or '' for row in group)
            candidates = [row for row in group if row.get('period_end') == latest]
            if len({(row.get('period_start'), row['value'], row.get('semantic')) for row in candidates}) != 1:
                continue
            chosen = max(candidates, key=lambda row: (row.get('filing_date') or '', row['normalized_hash']))
            selected.add(chosen['normalized_hash'])
        for pair in projection.get('comparison_candidates', ()):
            if pair.get('current_ref') in selected and pair.get('prior_ref') in by_ref:
                selected.add(pair['prior_ref'])
        for ref in sorted(selected):
            row = by_ref[ref]
            if ref != digest({k:v for k,v in row.items() if k != 'normalized_hash'}):
                continue
            keys = ('metric','value','period_start','period_end','period_role','period_kind',
                    'current_prior_role','currency','unit','statement_basis','filing_date',
                    'source_provider','source_document_id','semantic','formal_state')
            observed.append(dict(ref_id=ref, as_of=row.get('period_end'),
                kind='REPORTED_ABSOLUTE_CONTEXT_ONLY',
                observation={k:deepcopy(row[k]) for k in keys if k in row}))
    # A margin relationship uses two matched original periods, not a new
    # independent bullish/bearish vote. No denominator or period substitution.
    relations = []
    comparisons = [r for r in observed if r['kind'] == 'REPORTED_COMPARISON']
    revenue = [r for r in comparisons if r['observation']['metric'] == 'revenue']
    operating = [r for r in comparisons if r['observation']['metric'] == 'operating_income']
    if len(revenue) == len(operating) == 1:
        rev, op = revenue[0]['observation'], operating[0]['observation']
        keys = ('period_start','period_end','prior_period_start','prior_period_end',
                'period_type','currency','statement_basis','issuer_id','source_ticker','source_receipt')
        if all(rev.get(k) is not None and rev[k] == op.get(k) for k in keys):
            curr, prev = number(rev['current_value']), number(rev['prior_comparable_value'])
            if curr > 0 and prev > 0:
                a = number(op['current_value']) / curr * 100
                b = number(op['prior_comparable_value']) / prev * 100
                relations.append(dict(kind='OPERATING_MARGIN_COMPARISON',
                    source_refs=[revenue[0]['ref_id'], operating[0]['ref_id']],
                    current_pct=float(a), prior_pct=float(b), change_pp=float(a-b),
                    scope='DERIVED_CONTEXT_NOT_INDEPENDENT_DIRECTION'))
    leads = [dict(title=r['title'], published_at=r['published_at'], source_use='HEADLINE_FOLLOWUP_ONLY')
             for r in (view.get('event_view') or {}).get('binding', {}).get('selected', ())
             if r.get('review_scope') == 'HEADLINE_FOLLOWUP_ONLY'
             and r.get('reason') == 'business_relevance_failure' and r.get('published_at')]
    scope = {}
    if filing_rows:
        if filing_rows[0]['kind'] == 'REPORTED_OPERATING_CONTEXT_ONLY':
            scope['filing_scope'] = ('Consolidated reported accounts. Distinguish balances from period results. '
                'Contract balances do not measure backlog. PPE carrying amounts do not measure capex or capacity. '
                'R&D expense is incurred spending. Investment income can be part of the net investment result. '
                'These accounts alone do not establish growth drivers.')
        else:
            scope['filing_scope'] = ('Issuer statements are attributed context. Product and segment dimensions '
                'can overlap. Keep each period, unit and classification separate; do not sum dimensions, '
                'infer a security denominator, or convert plans to realized results.')
    return dict(observations=observed, relationships=relations,
                **({'unverified_headlines_to_check': leads[:2]} if leads else {}),
                **scope,
                classification={k: deepcopy(classification[k]) for k in ('archetype','valuation_regime_tier')
                                if k in classification})


def b_input(view, cat, sub, chain, classification, capability):
    range_subject, entries, exclusions = eligible_range_inputs(sub, cat["entry_catalog"], chain)
    valuation = valuation_policy(range_subject, classification, sub["security_valuation_basis_state"],
        historical_context_only=view.get('contract') == 'fresh-financial-stock-owner-v1')
    valuation["source_use_exclusions"] = exclusions
    common = dict(catalog=cat, source_use_view=chain["projection"], source_use_binding=chain["binding"],
        source_use_expectation=chain["expectation"], source_generation_id=chain["source_generation_id"],
        execution_generation_id=chain["execution_generation_id"], require_source_use=True)
    ctx = build_pass_b_subject_context(context=owner.m12db._source_context(view["ticker"], sub),
        ticker=view["ticker"], pass_a=classification, policy_option=valuation["option"], **common)
    common.pop("require_source_use")
    transform = validate_pass_b_transformation(context=ctx, raw_source_metadata=sub["decision_evidence"], **common)
    c._require(transform["status"] == "PASS", "pass_b_transformation_failed")
    ctx.update(r2_policy_capability=capability, r2_valuation=valuation, r2_eligible_range_catalog=entries)
    ctx, entries = restrict_entry_candidates(ctx, entries, ticker=view['ticker'],
        security_id=(view.get('valuation_view') or {}).get('security_id'),
        source_generation_id=chain['source_generation_id'])
    stocks = (view.get('packet') or {}).get('stocks', [])
    if len(stocks) == 1 and stocks[0].get('ticker') == view['ticker']:
        structure = stocks[0].get('chart_context', {}).get('structure', {})
        v3 = structure.get('price_structure_v3') or {}
        if (v3.get('ticker') == view['ticker'] and v3.get('eligible_for_b2_timing') is False
                and not structure.get('nearest_supports') and v3.get('zones')):
            ctx['reference_only_support_reason'] = 'NO_QUALIFIED_STRUCTURE_V3_REFERENCE_ONLY'
    native = native_technical_context(view, ctx)
    if native is not None:
        ctx['native_technical_context'] = native
        # The complete basis checks were already executed. The model does not
        # need duplicate audit digests for each candidate in three lists.
        # B2 recomputes the same basis from the unchanged source evidence.
        for rows in (entries['tactical_candidates'], ctx['tactical_candidates'],
                     ctx['r2_eligible_range_catalog']['tactical_candidates'],
                     ctx['entry_candidate_diagnostics']):
            for row in rows:
                row.pop('basis_proofs', None)
    if view.get('contract') == 'fresh-financial-stock-owner-v1':
        ctx['economic_context'] = economic_context(view, ctx, classification, original_rows=sub['decision_evidence'])
    return ctx, entries, valuation
