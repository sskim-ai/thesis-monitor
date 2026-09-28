"""Pure sealed-source projection into the existing Market consumer contract.

This is an audit/shadow adapter. It does not acquire sources or invoke the live
Market packet builder, and it is not imported by production.
"""
from copy import deepcopy
from datetime import date, datetime
import json
from zoneinfo import ZoneInfo

from app.services.ai_review_service import _market_packet_session, validate_market_packet_session_parity
from app.services.fact_consumer_scope_service import (
    MARKET_CONTEXT_CONSUMER_SCOPES, NIGHT_FUTURES_CONSUMER_SCOPES, with_fact_consumer_scopes,
)
from app.services.market_context_adapter_service import market_context_adapter, NormalizedMarketContext
from app.services.market_cross_section_service import MarketCrossSection
from app.services.market_intelligence_service import _SERIES, _observation_fact, _coverage, build_market_intelligence
from app.services.night_futures import summarize_night_futures, night_futures_context_row, night_futures_timeframe_facts
from app.services.numeric_semantic_registry import build_numeric_registry
from app.services.unified_snapshot_contract import digest
from scripts import m12ds_r4_r4_market as consumer

CONTRACT = 'sealed-market-consumer-projection-v1'
PUBLICATIONS = ('energy', 'korea_macro', 'kr_overnight_cross_assets', 'rates_credit_liquidity_risk',
                'central_bank_published_events')
ROLE = {'us': 'us_market_prices', 'kr': 'kr_local_indices_sectors_breadth'}


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def contract_inventory():
    """Recovered from R4/R3/R2 consumers, native adapter, registry and renderer."""
    specs = [
        ('market', 'string', True, 'sealed packet', 'US/KR identity', 'all'),
        ('assessment_date', 'ISO_DATE', True, '_market_packet_session', 'proof date, not source date', 'all'),
        ('generated_at', 'aware datetime', True, 'market acquisition cutoff', 'sealed proof time, not wall clock', 'session parity'),
        ('market_context.session', 'object', True, '_market_packet_session', 'completed regular session and assessment state', 'numeric catalog/render'),
        ('market_context.adapter_context', 'NormalizedMarketContext', True, 'MarketContextAdapter.normalize', 'local market source aliases', 'R2/R3 schema'),
        ('market_context.fact_catalog', 'list[Fact]', True, 'market_intelligence_service/night_futures', 'typed facts; empty eligibility allowed, absent owners not allowed', 'R2/R3/typed numeric'),
        ('market_context.numeric_registry', 'list[NumericField]', True, 'build_numeric_registry', 'exact fact ID, field path, value, unit, semantic', 'numeric catalog/render'),
        ('market_context.coverage', 'object', True, '_coverage/cross-section owner', 'row eligibility plus explicit block availability', 'R3'),
        ('market_context.night_futures', 'list[NightFuturesItem]', False, 'summarize_night_futures', 'official KRX normalized same-contract D/W/M', 'R4/R1/numeric render'),
        ('market_context.optional_denials', 'object', False, 'sealed optional_denials', 'unavailable is not zero', 'audit/adapter data_gaps'),
        ('market_context.publication_denials', 'list', False, 'sealed class-C owner', 'unmapped/denied publication occurrences, not current substitutes', 'audit'),
    ]
    inventory = dict(contract=CONTRACT, rows=[dict(path=p, type=t, mandatory=m, owner=o,
        semantic=s, consumed_by=c, source_time_requirement='source session <= assessment; query and publication dates distinct',
        numeric_registry_requirement='all numeric fact fields; adapter aliases trace to same canonical fields',
        source_ref_requirement='sealed packet/authority graph occurrence binding',
        coverage_requirement='explicit unavailable/denied; row eligibility remains current consumer owned',
        denial_representation='coverage.unavailable + reasons; never zero',
        renderer_dependency=c, unified_equivalent=True) for p,t,m,o,s,c in specs],
        prior_success_owner='scripts.m12ds_r4_r1_project_source.MARKET_FIELDS',
        policy_owner='scripts.m12ds_r4_r4_market', historical_values_reused=False,
        schema_semantics='DATA_INSUFFICIENT remains valid; direction requires eligible facts')
    schema=NormalizedMarketContext.model_json_schema()
    def walk(node,path):
        if '$ref' in node:
            node=schema['$defs'][node['$ref'].split('/')[-1]]
        if node.get('type')=='array':
            walk(node['items'],path+'[]')
        for name,child in node.get('properties',{}).items():
            template=deepcopy(inventory['rows'][4])
            template.update(path=path+'.'+name,type=child,mandatory=name in node.get('required',[]),
                owner='NormalizedMarketContext native JSON schema',semantic='Native adapter typed field; optional absence remains explicit')
            inventory['rows'].append(template)
            walk(child,path+'.'+name)
    walk(schema,'market_context.adapter_context')
    inventory['native_schema']=schema
    return inventory


def _authority(packet, seed, graph, expected):
    require(digest(graph) == expected, 'market_authority_graph_hash_mismatch')
    market = packet['market']
    require(market in ROLE and packet['authority_graph_sha256'] == expected, 'market_identity_mismatch')
    require(packet['run_seed_sha256'] == graph['run_seed_sha256'] == digest(seed), 'market_seed_mismatch')
    require(packet['market_sources'] == graph['markets'][market], 'market_authority_subset_mismatch')
    source = packet['market_sources']
    require(digest(source) == seed['attempt_hashes'][market] and source['attempt_id'] == seed['attempts'][market],
            'market_attempt_mismatch')
    require(source['run_id'] == seed['parent_run_id'], 'market_run_mismatch')
    component = source['component']
    require(component['source']['role'] == ROLE[market], 'market_source_role_mismatch')
    require(component['value_sha256'] == digest(component['value']), 'market_value_hash_mismatch')
    require(packet['publication_context'] == graph['publication_context'] and
            packet['optional_denials'] == graph['optional_denials'] and
            digest(packet['optional_denials']) == seed['optional_denial_set_sha256'], 'market_context_authority_mismatch')
    require(packet['class_c_versions'] == graph['class_c'] and digest(graph['class_c']) == seed['class_c_version_set_sha256'],
            'market_publication_versions_mismatch')
    start, cutoff = datetime.fromisoformat(seed['started_at']), datetime.fromisoformat(source['cutoff'])
    require(start.utcoffset() is not None and cutoff.utcoffset() is not None and start <= cutoff,
            'market_cutoff_invalid')
    require(start <= datetime.fromisoformat(component['original_source_time']) <= cutoff, 'market_query_time_invalid')
    if market == 'us':
        night = packet['night_and_publication_context']
        require(night == graph['night'] and night['value_sha256'] == digest(night['value']) == seed['run_acquisitions']['night'],
                'night_authority_mismatch')
    return component, cutoff


def _publication_facts(packet, assessed):
    facts, denials, refs = {}, [], {}
    context = packet['publication_context']
    if context.get('contract') == 'fresh-publication-replay-v1':
        require(context['run_id'] == packet['market_sources']['run_id'], 'fresh_publication_run_mismatch')
        require(context['value_sha256'] == digest(context['providers']), 'fresh_publication_value_mismatch')
        for provider, doc in sorted(context['providers'].items()):
            require(doc['value_sha256'] == digest(doc['value']), 'fresh_publication_provider_value_mismatch')
            for i, observation in enumerate(doc['value']['observations']):
                path = f'publication_context/providers/{provider}/value/observations/{i}'
                temporal = observation['raw_payload']['publication_context']
                require(temporal['response_sha256'] in doc['source_hashes'].values(), 'fresh_publication_raw_unbound')
                if observation['series_code'] not in _SERIES or not temporal['display_eligible']:
                    denials.append(dict(path=path, reason='not_consumed_or_publication_currentness_unproven',
                                        source_sha256=digest(observation)))
                    continue
                item = {**observation, 'provider': provider,
                    'previous_observation_date': observation['raw_payload'].get('previous_observation_date'),
                    'temporal': {**temporal, 'temporal_role': 'REFERENCE_LAGGING',
                        'today_signal_eligible': False, 'important_change_eligible': False,
                        'structured_state': 'SOURCE_UNAVAILABLE',
                        'reason': 'fresh_publication_level_and_source_period_delta_only_no_briefing_comparison'}}
                fact = _observation_fact(observation['series_code'], item, assessed)
                fact['as_of_date'] = temporal['observation_date']
                fact['source'] = provider
                fact.setdefault('fields', {})['publication_context'] = temporal
                ref = fact['fact_id']
                require(ref not in facts or facts[ref] == fact, 'ambiguous_publication_occurrence:' + ref)
                facts[ref] = fact
                refs.setdefault(ref, []).append(path)
        return list(facts.values()), denials, refs
    for role in PUBLICATIONS:
        name = 'class-c/' + role + '.json'
        doc = packet['publication_context'][name]
        require(doc['source_sha256'] == packet['class_c_versions'][name], 'publication_version_mismatch')
        projection = doc['projection']
        require(projection['contract'] == 'unified-class-c-owner-projection-v1', 'publication_owner_missing')
        for i, value in enumerate(projection['values']):
            observation = value.get('observation')
            path = f'publication_context/{name}/projection/values/{i}'
            if not projection['eligible'] or not observation or observation['series_code'] not in _SERIES:
                denials.append(dict(path=path, reason='not_consumed_by_current_Market_fact_contract',
                                    source_sha256=digest(value)))
                continue
            require('temporal' in value, 'publication_temporal_owner_missing')
            item = {**observation, 'temporal': value['temporal']}
            fact = _observation_fact(observation['series_code'], item, assessed)
            fact['as_of_date'] = datetime.fromisoformat(observation['observed_at']).date().isoformat()
            fact['source'] = observation['provider']
            ref = fact['fact_id']
            require(ref not in facts or facts[ref] == fact, 'ambiguous_publication_occurrence:' + ref)
            facts[ref] = fact
            refs.setdefault(ref, []).append(path)
    return list(facts.values()), denials, refs


def numeric_alias_audit(context, source):
    """Native adapter refs are aliases, not new independent numeric authorities."""
    catalog = source['fact_catalog']
    registry = {(r['fact_id'], r['field_path']): r for r in source['numeric_registry']}
    rows, errors = [], []
    mapping = {
        'indices': {'close': 'close', 'return_pct': 'return_pct'},
        'sectors': {'return_pct': 'return_pct', 'listed_count': 'listed_count'},
        'size_context': {'return_pct': 'return_pct'},
        'breadth': {'advancers': 'advance_count', 'decliners': 'decline_count',
                    'unchanged': 'unchanged_count', 'eligible_count': 'eligible_count'},
    }
    for ref, payload in context['facts'].items():
        kind = payload.get('kind')
        if kind not in mapping or 'fields' in payload:
            continue
        if kind == 'indices':
            matches = [f for f in catalog if f['fact_type'] == 'market_cross_section_index'
                       and f['fields']['symbol'] == payload['symbol']]
        elif kind == 'breadth':
            matches = [f for f in catalog if f['fact_id'] == 'market:breadth:kr:counts']
        else:
            matches = [f for f in catalog if f['fact_type'] == 'market_cross_section_sector'
                       and f['fields'].get('source_ref') == ref]
        if len(matches) != 1:
            errors.append('alias_canonical_owner_missing:' + ref)
            continue
        fact = matches[0]
        extra_numbers = [k for k,v in payload.items() if isinstance(v, (int,float)) and not isinstance(v,bool)
                         and k not in mapping[kind] and not (kind == 'breadth' and k == 'breadth_ratio')]
        errors.extend('unowned_alias_numeric_field:' + ref + ':' + k for k in extra_numbers)
        for key, target in mapping[kind].items():
            if payload.get(key) is None:
                continue
            path = 'fields.' + target
            row = registry.get((fact['fact_id'], path), {})
            ok = row.get('registered') is True and row.get('value') == payload[key]
            rows.append(dict(alias_ref=ref, alias_path=key, canonical_ref=fact['fact_id'],
                canonical_path=path, value=payload[key], unit=row.get('unit'),
                semantic_type=row.get('semantic_type'), registered=ok))
            if not ok:
                errors.append('alias_numeric_binding_failed:' + ref + ':' + key)
        if kind == 'breadth' and payload.get('breadth_ratio') is not None:
            denominator = payload['advancers'] + payload['decliners']
            ok = denominator > 0 and payload['breadth_ratio'] == payload['advancers'] / denominator
            rows.append(dict(alias_ref=ref, alias_path='breadth_ratio', value=payload['breadth_ratio'],
                canonical_ref=fact['fact_id'], input_paths=['fields.advance_count', 'fields.decline_count'],
                formula='advance_count / (advance_count + decline_count)', unit='ratio', registered=ok))
            if not ok:
                errors.append('breadth_alias_derived_binding_failed')
    return dict(status='FAIL' if errors else 'PASS', rows=rows, errors=errors,
                owner='native MarketContextAdapter aliases + canonical numeric registry')


def registered_projection(facts):
    """Keep the canonical registry's permissions; retain denied input in receipt."""
    projected = deepcopy(facts)
    by_id = {f['fact_id']:f for f in projected}
    denied = []
    for row in build_numeric_registry(projected):
        if row.get('registered') is True:
            continue
        # Night references and D/W/M scalars have their own existing typed
        # catalog/eligibility/arithmetic binder, checked after context creation.
        if by_id[row['fact_id']]['fact_type'] in {'night_futures','night_futures_timeframe'}:
            continue
        path = row['field_path']
        # Only optional observation scalars may be withheld here. Mandatory
        # identity and nested derivation owners must be closed, not stripped.
        require((by_id[row['fact_id']]['fact_type'],path)==
                ('market_breakeven_inflation','fields.previous_level_pct'), 'unregistered_required_market_field')
        field = path.split('.')[1]
        denied.append(dict(fact_id=row['fact_id'],field_path=path,value=by_id[row['fact_id']]['fields'].pop(field),
            reason='existing_numeric_registry_unregistered',source_preserved=True,model_visible=False))
    return projected, denied


def project_sealed_market_context(packet, seed, graph, *, expected_authority_sha256):
    """Return a separate consumer packet and receipt; source objects stay intact."""
    original = digest(packet)
    component, cutoff = _authority(packet, seed, graph, expected_authority_sha256)
    market = packet['market']
    assessed = cutoff.astimezone(ZoneInfo('Asia/Seoul')).date()
    session = _market_packet_session(market, assessed, cutoff)
    require(session['latest_completed_regular_session_date'] == component['session'], 'market_completed_session_mismatch')
    facts, publication_denials, refs = _publication_facts(packet, assessed)
    published = {f['fields']['series_code']:dict(quality_status=f['fields'].get('quality')) for f in facts}
    cross = None
    if market == 'kr':
        value = component['value']
        require(value.get('indices') and value.get('sectors') and value.get('breadth'), 'kr_mandatory_market_source_missing')
        cross = MarketCrossSection.model_validate(dict(**value, market='KR', session_date=component['session'],
            as_of=component['original_source_time'], source_payload_sha256=component['source']['artifact_sha256'],
            quality=dict(provider=component['provider'], provider_role=component['source']['role'],
                coverage='partial', freshness='fresh', universe_version=component['eligibility']['contract'],
                eligible_count=value['breadth']['eligible_count'])))
        native = build_market_intelligence(None, date.fromisoformat(component['session']), [], [], market=market, cross_section=cross)
        facts += native['fact_catalog']
        coverage = native['coverage']
        for f in native['fact_catalog']:
            kind = f['fact_type']
            if kind=='market_cross_section_index':
                indices=[i for i,r in enumerate(value['indices']) if r['symbol']==f['fields']['symbol']]
                require(len(indices)==1,'kr_index_occurrence_ambiguous')
                refs[f['fact_id']]=['market_sources/component/value/indices/'+str(indices[0])]
            elif kind=='market_cross_section_sector':
                indices=[i for i,r in enumerate(value['sectors']) if r.get('source_ref')==f['fields'].get('source_ref')]
                require(len(indices)==1,'kr_sector_occurrence_ambiguous')
                refs[f['fact_id']]=['market_sources/component/value/sectors/'+str(indices[0])]
            else:
                refs[f['fact_id']]=['market_sources/component/value/breadth']
    else:
        observations = component['value']['observations']
        require(observations, 'us_mandatory_market_source_missing')
        coverage = _coverage({o['series_code']: o for o in observations}, market)[0]
        for i, row in enumerate(observations):
            if row['series_code'] not in _SERIES:
                publication_denials.append(dict(path=f'market_sources/component/value/observations/{i}',
                    reason='not_in_current_market_series_contract', source_sha256=digest(row)))
                continue
            require(datetime.fromisoformat(row['observed_at']).date().isoformat() == component['session'],
                    'market_observation_session_mismatch')
            item = {**row, 'provider': component['provider']}
            fact = _observation_fact(row['series_code'], item, assessed)
            fact['as_of_date'] = component['session']
            fact['source'] = component['provider']
            if row.get('change_pct') is None:
                fact['fields'].update(today_signal_eligible=False, structured_state='CURRENT_LEVEL_ONLY')
            facts.append(fact)
            refs[fact['fact_id']] = [f'market_sources/component/value/observations/{i}']
        for category in ('indices', 'sectors', 'style_size'):
            block = coverage[category]
            returned = set(block['available_series'])
            eligible = {o['series_code'] for o in observations if o['series_code'] in returned
                        and o.get('change_pct') is not None}
            block.update(level_observation_series=sorted(returned), available_series=sorted(eligible),
                status='available' if eligible == returned and eligible else 'partial' if eligible else 'unavailable',
                missing_directional_series=sorted(returned-eligible),
                reason='completed_session_return_required_by_existing_Market_consumer')
        coverage['local_market_indices'] = deepcopy(coverage['indices'])
    publication_coverage = _coverage(published,market)[0]
    for key in ('commodities','credit','fx','liquidity','rates','risk_signals'):
        coverage[key] = publication_coverage[key]
        coverage[key]['availability_basis'] = 'sealed_published_observation; per-row temporal eligibility remains separate'
    require(len({f['fact_id'] for f in facts}) == len(facts), 'duplicate_source_market_fact')
    night_rows, night_cautions = [], []
    if market == 'us':
        observations = packet['night_and_publication_context']['value']['observations']
        normalized = [{**o, **o['raw_payload']} for o in observations]
        night = summarize_night_futures({'observations': normalized})
        require(len(night.items) == len(observations), 'normalized_night_owner_rejected')
        for item in night.items:
            row = json.loads(json.dumps(night_futures_context_row(item), default=str))
            night_rows.append(row)
            facts.append(dict(fact_id=row['fact_id'], fact_type='night_futures', as_of_date=row['session_date'], fields=row))
            facts.extend(night_futures_timeframe_facts(item))
            for ref in [row['fact_id'], *[f['fact_id'] for f in night_futures_timeframe_facts(item)]]:
                refs[ref] = ['night_and_publication_context/value/observations/' + str(len(night_rows)-1)]
        night_cautions = night.cautions
    facts = [with_fact_consumer_scopes(f, NIGHT_FUTURES_CONSUMER_SCOPES
        if f['fact_type'].startswith('night_futures') else MARKET_CONTEXT_CONSUMER_SCOPES) for f in facts]
    facts, numeric_denials = registered_projection(facts)
    registry = build_numeric_registry(facts)
    adapter = market_context_adapter(market).normalize(assessment_date=assessed, as_of=cutoff, cutoff=cutoff,
        fact_catalog=facts, coverage=coverage, cross_section=cross,
        provider_publication_state='PROVIDER_COMPLETE').model_dump(mode='json')
    source = dict(session=session, adapter_context=adapter, fact_catalog=facts, numeric_registry=registry,
        coverage=coverage, night_futures=night_rows, night_futures_cautions=night_cautions,
        optional_denials=deepcopy(packet['optional_denials']), publication_denials=publication_denials)
    projected = dict(market=market, assessment_date=assessed.isoformat(), generated_at=cutoff.isoformat(),
        proof_mode=seed['proof_mode'], market_context=source)
    parity = validate_market_packet_session_parity(projected)
    require(parity['status'] == 'PASS', 'market_projected_session_invalid')
    context = consumer.market_context(projected)
    boundary = consumer.numeric_boundary(context, source)
    aliases = numeric_alias_audit(context, source)
    require(context['parity_status'] == boundary['status'] == 'PASS', 'market_consumer_parity_failed')
    require(aliases['status'] == 'PASS', 'market_numeric_alias_failed')
    require(digest(packet) == original, 'market_source_mutated')
    return dict(packet=projected, context=context, schema=consumer.market_schema(context),
        receipt=dict(contract=CONTRACT, source_packet_sha256=original, context_sha256=digest(context),
            fact_catalog_sha256=digest(facts), numeric_registry_sha256=digest(registry),
            coverage_sha256=digest(coverage), source_refs=refs, session=parity,
            source_authority_sha256=expected_authority_sha256, numeric_boundary=boundary,
            numeric_alias_binding=aliases, provider_refresh=0, source_mutation=False, policy_mutation=False,
            numeric_field_denials=numeric_denials,
            proof_mode=seed['proof_mode'], optional_denials=deepcopy(packet['optional_denials'])))
