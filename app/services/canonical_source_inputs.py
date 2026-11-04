"""Canonical owner inputs; caller supplies a separately validated lineage binding."""
from pathlib import Path
from app.services.canonical_source_replay import read, stock_inputs, market_inputs, publication_inputs
from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.fresh_publication_replay import replay_fresh_publications
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_sealed_context import replay_night
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_composition import _resolve
from app.services.unified_stock_acquisition import StockPlan


def fresh_authority_inputs(stock, inputs):
    """Exact source replay arguments shared by single-subject and whole-cohort owners."""
    from scripts.m12cn_policy_contract import build_subject_catalog
    from scripts.m12dk_current_source_authority import freeze_current_source_binding
    from app.services.direction_timing_ownership_service import verified_owned_packet_view
    owned = verified_owned_packet_view(stock)
    context = dict(evidence_packets=[stock['evidence_packet']], evidence_ownership=[dict(
        ticker=stock['ticker'], core_ref_ids=sorted(owned.core_refs), timing_ref_ids=sorted(owned.timing_refs))])
    catalog = build_subject_catalog(context=context, ticker=stock['ticker'], atomic_claims=[])
    metadata = [r for r in stock['evidence_packet']['evidence'] if r['ref_id'] in catalog['all_evidence_refs']]
    return dict(ticker=stock['ticker'], source_generation_id=stock['fresh_run_id'],
        source_packet=stock['packet'], evidence_packet=stock['evidence_packet'], catalog=catalog,
        source_metadata=metadata, frozen_binding=freeze_current_source_binding(
            source_generation_id=stock['fresh_run_id'], source_packet=stock['packet'], evidence_packet=stock['evidence_packet']),
        quality_bundles={}, issuer_bindings={}, fresh_business_inputs=inputs)

def build_source_replay_inputs(root, frozen, outcome, policy, *, binding_factory, completed_close_sources=None,
                              stock_reader=stock_inputs, market_reader=market_inputs,
                              publication_reader=publication_inputs, cycle_owners=None, prospective_owners=None,
                              class_c_bridge=None):
    if class_c_bridge is not None:
        if cycle_owners is not None or prospective_owners is not None:
            raise ValueError('class_c_bridge_mixed_owner_route_denied')
        from app.services.current_class_c_source_bridge import require_dispatch
        require_dispatch(class_c_bridge, root=root, frozen=frozen, policy=policy)
    if completed_close_sources is None:
        from app.services.kiwoom_completed_close_owner import load_supplement_lineage
        completed_close_sources = load_supplement_lineage(root, parent_generation_id=frozen['generation_id'])
    if frozen.get('scope') == 'US14_ONLY':
        from scripts.us14_source_scope import require_us14_plan
        require_us14_plan(frozen)
    if frozen.get('scope') == 'KR8_ONLY':
        from scripts.kr8_source_scope import require_kr8_plan
        require_kr8_plan(frozen)
    inputs, errors = stock_reader(root, frozen, policy, outcome,
        **({'cycle_owners': cycle_owners} if cycle_owners is not None else {}),
        **({'prospective_owners': prospective_owners} if prospective_owners is not None else {}),
        **({'class_c_bridge': class_c_bridge} if class_c_bridge is not None else {}))
    if not inputs:
        raise ValueError('SOURCE_PARTIAL:empty_stock_bindings')
    plan = next(iter(inputs.values()))['technical_inputs']['plan']
    if 'stock_plan' in frozen and StockPlan.model_validate(frozen['stock_plan']) != plan:
        raise ValueError('SOURCE_PARTIAL:stock_plan_mismatch')
    if any(i['technical_inputs']['plan'] != plan for i in inputs.values()):
        raise ValueError('SOURCE_PARTIAL:mixed_stock_plans')
    universe = plan.universe
    if errors or set(inputs) != {t for ts in universe.values() for t in ts}:
        raise ValueError('SOURCE_PARTIAL:stock_bindings:' + ','.join(sorted(errors)))
    close_binding = {}
    if completed_close_sources is not None:
        from app.services.kiwoom_completed_close_owner import bind_technical_input
        if set(universe) != {'us'} or set(completed_close_sources) != set(universe['us']):
            raise ValueError('completed_close_whole_us14_scope_required')
        for ticker, item in inputs.items():
            supplement = completed_close_sources[ticker]
            item['technical_inputs'] = bind_technical_input(item['technical_inputs'],
                **supplement, security=item['financial_inputs']['plan']['security'])
        close_binding = dict(completed_close_supplement=digest({t: s['source'] for t,s in completed_close_sources.items()}))
    markets = market_reader(root, frozen, outcome, policy)
    context = publication_reader(root, frozen, outcome, policy)
    pub, night = replay_fresh_publications(**context['publications']), replay_night(**context['night'])
    from app.services.latest_published_fx import display_receipt
    fx = display_receipt(pub, frozen['context_sessions']['kr_fx'] if frozen.get('scope')=='US14_ONLY' else frozen["sessions"]["kr"])
    rows = {t: assemble_fresh_stock(**i) for t, i in inputs.items()}
    event_errors = [t for t, row in rows.items()
                    if str(row.get("event_view", {}).get("binding", {}).get("denial") or "").startswith("event_owner_error:")]
    if event_errors:
        raise ValueError("SOURCE_PARTIAL:event_owner_error:" + ",".join(sorted(event_errors)))
    native = {m: dict(run_id=frozen['generation_id'], attempt_id=n['attempt_id'],
        attempt_started_at=n['start'].isoformat(), cutoff=n['cutoff'].isoformat(), component=_resolve(**n))
        for m, item in markets.items() for n in [item['native_aggregate']]}
    if class_c_bridge is not None:
        from app.services.current_class_c_source_bridge import memory_version_set
        versions = memory_version_set(class_c_bridge, frozen=frozen, policy=policy)
    else:
        versions = {f'class-c/local-{m}.json': sha256_bytes((root/f'class-c/local-{m}.json').read_bytes()) for m in universe}
    repo = Path(__file__).resolve().parents[2]
    inventory = read(repo/'docs/operations/UNIFIED_ACQUISITION_CLASSES.json')
    from app.services.whole_source_code_owner_registry import WholeSourceCodeOwnerRegistry
    registry = WholeSourceCodeOwnerRegistry.freeze(repo,
        profile='fresh_us14' if frozen.get('scope')=='US14_ONLY' else 'fresh' if 'us' in universe else 'fresh_kr8')
    denials = dict(kr_market_investor_flows=dict(status='OPTIONAL_UNAVAILABLE', value=None,
        denial='NOT_SELECTED_FOR_MARKET_COMPOSITION', run_id=frozen['generation_id']))
    bridge = rows['SKHY']['issuer_business_bridge'] if 'us' in universe else {'status': 'NOT_APPLICABLE_KR8_ONLY'}
    bindings = {t: digest(dict(technical_plan=plan.model_dump(mode='json'),financial_plan=i['financial_inputs']['plan'])) for t,i in inputs.items()}
    from app.services.canonical_source_composition import auxiliary_issuer_binding
    auxiliary = {'auxiliary_issuer_set_sha256':digest(auxiliary_issuer_binding(
        {t:dict(fresh_financial_binding=i) for t,i in inputs.items()}))} if frozen.get('scope') == 'US14_ONLY' else {}
    seed = binding_factory(
        parent_run_id=plan.run_id, started_at=plan.frozen_at, source_policy_sha256=digest(sorted(policy.allowed_providers)),
        inventory_sha256=digest(inventory), **registry.seed_bindings, universe_sha256=digest(universe),
        attempts={m:n['attempt_id'] for m,n in native.items()}, attempt_hashes={m:digest(n) for m,n in native.items()},
        run_acquisitions=dict(stock=digest(plan.model_dump(mode='json')),publications=digest(pub),night=night['value_sha256'], **close_binding),
        class_c_version_set_sha256=digest(versions), stock_cohort_hashes={m:digest({t:rows[t] for t in ts}) for m,ts in universe.items()},
        night_publication_receipt_sha256=digest(dict(probe=night['original_receipts'],history=night.get('history_receipts',[]))),
        optional_denial_set_sha256=digest(denials), skhy_issuer_bridge_sha256=digest(bridge),
        fresh_stock_owner_set_sha256=digest(bindings), **auxiliary)
    args = dict(seed=seed, market_inputs=markets, stock_inputs={t:dict(fresh_financial_binding=i) for t,i in inputs.items()},
        authority_inputs={t:fresh_authority_inputs(rows[t],i) for t,i in inputs.items()}, version_set=versions,
        optional_denials=denials, issuer_bridge=bridge, composition_metadata=dict(inventory=inventory,
            allowed_providers=sorted(policy.allowed_providers),code_fingerprints=registry.fingerprints,
            code_owner_registry=registry.model_dump(mode="json"),
            fx_display_receipt=fx), fresh_context_inputs=context)
    return args
